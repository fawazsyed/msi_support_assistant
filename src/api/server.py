"""
FastAPI server to connect the Angular UI to the LangChain backend.

This server provides a REST API that the Angular frontend can call,
bridging the gap between the web UI and your LangChain agent.
"""

from typing import Any
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pathlib import Path
import json
from dotenv import load_dotenv
import uvicorn

# Local imports
from src.core.utils import setup_logging
from src.core.agent import initialize_agent_components
from src.core.config import LOG_KEEP_RECENT, ENABLE_RAGAS_COLLECTION, RAGAS_DATA_DIR
from src.models import ChatMessage, ChatRequest
from src.observability import RagasDataCollector
from datetime import datetime

# Get project root (parent of src/api/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Setup logging
logger = setup_logging(PROJECT_ROOT, keep_recent=LOG_KEEP_RECENT)

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="MSI AI Assistant API")

# Enable CORS for Angular dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize agent when the server starts and store in app.state"""
    logger.info("Initializing agent on startup...")
    app.state.agent, app.state.mcp_client = await initialize_agent_components(
        project_root=PROJECT_ROOT,
        logger=logger
    )
    logger.info("Agent initialization complete")
    
    # Initialize Ragas data collector if enabled
    if ENABLE_RAGAS_COLLECTION:
        app.state.collector = RagasDataCollector()
        app.state.interaction_count = 0
        app.state.auto_save_interval = 10  # Save every 10 interactions
        
        # Create data directory
        data_dir = PROJECT_ROOT / RAGAS_DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Ragas data collection enabled. Auto-save every {app.state.auto_save_interval} interactions.")
        logger.info(f"Data will be saved to {data_dir}")
    else:
        app.state.collector = None
        logger.info("Ragas data collection disabled")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Save any remaining collected data on shutdown"""
    if hasattr(app.state, 'collector') and app.state.collector is not None:
        try:
            if len(app.state.collector) > 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                data_file = PROJECT_ROOT / RAGAS_DATA_DIR / f"agent_data_{timestamp}.json"
                app.state.collector.save(data_file)
                logger.info(f"Saved {len(app.state.collector)} samples on shutdown to {data_file}")
        except Exception as e:
            logger.error(f"Failed to save data on shutdown: {e}")


# Dependency injection functions
async def get_agent():
    """Dependency that provides the initialized agent"""
    if not hasattr(app.state, 'agent') or app.state.agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized. Server is starting up.")
    return app.state.agent


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok", "message": "MSI AI Assistant API is running"}


@app.post("/api/admin/save-data")
async def save_collected_data() -> dict[str, Any]:
    """
    Manually trigger save of collected Ragas data.
    Useful before shutdown or for periodic backups.
    """
    if not hasattr(app.state, 'collector') or app.state.collector is None:
        return {"status": "disabled", "message": "Ragas data collection is not enabled"}
    
    if len(app.state.collector) == 0:
        return {"status": "ok", "message": "No data to save", "samples": 0}
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_file = PROJECT_ROOT / RAGAS_DATA_DIR / f"agent_data_{timestamp}.json"
        app.state.collector.save(data_file)
        
        sample_count = len(app.state.collector)
        app.state.collector.clear()
        
        logger.info(f"Manual save: {sample_count} samples saved to {data_file}")
        
        return {
            "status": "ok",
            "message": f"Saved {sample_count} samples",
            "file": str(data_file.name),
            "samples": sample_count
        }
    except Exception as e:
        logger.error(f"Failed to save data: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/chat")
async def chat(request: ChatRequest, agent=Depends(get_agent)) -> dict[str, Any]:
    """
    Simple non-streaming chat endpoint.
    Returns the complete response from the LangChain agent.
    """
    try:
        # Run the agent (it will decide whether to use the RAG tool)
        result = await agent.ainvoke({
            "messages": [{"role": m.role, "content": m.content} for m in request.messages]
        })

        # Extract the assistant's response
        assistant_message = result["messages"][-1].content if result.get("messages") else ""

        # Extract tool calls if any (for debugging/visibility)
        tool_calls = []
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend([
                    {"name": tc.get("name", ""), "args": tc.get("args", {})}
                    for tc in msg.tool_calls
                ])

        return {
            "content": assistant_message,
            "toolCalls": tool_calls
        }

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return {"error": str(e), "content": "Sorry, I encountered an error processing your request."}


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, agent=Depends(get_agent)) -> StreamingResponse:
    """
    Streaming chat endpoint.
    Sends server-sent events (SSE) to the Angular frontend as the agent processes the query.
    """
    async def event_stream():
        try:
            # Get the last message
            last_message = request.messages[-1].content
            logger.info(f"Processing query: {last_message}")

            # Stream agent response (agent will call RAG tool if needed)
            full_content = ""
            event_count = 0

            # Use stream_mode="values" to get complete state updates
            async for chunk in agent.astream(
                {"messages": [{"role": m.role, "content": m.content} for m in request.messages]},
                stream_mode="values"
            ):
                event_count += 1

                # Get all messages from the chunk
                messages = chunk.get("messages", [])
                if not messages:
                    logger.debug(f"Event {event_count}: No messages in chunk")
                    continue

                # Get the last message (most recent)
                last_msg = messages[-1]
                msg_class_name = type(last_msg).__name__
                msg_type = getattr(last_msg, 'type', 'unknown')  # LangChain uses 'type' not 'role'
                msg_content = getattr(last_msg, 'content', '')
                msg_has_tool_calls = hasattr(last_msg, 'tool_calls') and last_msg.tool_calls

                logger.info(f"Event {event_count}: class={msg_class_name}, type={msg_type}, content_len={len(str(msg_content)) if msg_content else 0}, has_tools={msg_has_tool_calls}")

                # Skip human and system messages (only process AI messages)
                if msg_type != 'ai':
                    continue

                # Check for tool calls
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    for tool_call in last_msg.tool_calls:
                        tool_data = {
                            "type": "tool_call",
                            "toolCall": {
                                "id": tool_call.get("id", ""),
                                "name": tool_call.get("name", ""),
                                "args": tool_call.get("args", {})
                            }
                        }
                        event_json = json.dumps(tool_data)
                        logger.info(f"Event {event_count}: Sending tool_call: {tool_call.get('name')}")
                        yield f"data: {event_json}\n\n"

                # Send content updates
                if hasattr(last_msg, "content") and last_msg.content:
                    current_content = str(last_msg.content)

                    # Only send if content changed
                    if current_content != full_content:
                        full_content = current_content
                        content_data = {
                            "type": "content",
                            "content": full_content
                        }
                        logger.info(f"Event {event_count}: Sending content update (length: {len(full_content)})")
                        yield f"data: {json.dumps(content_data)}\n\n"

            # Always send final content (even if empty)
            final_content_data = {
                "type": "content",
                "content": full_content if full_content else "I processed your request."
            }
            logger.info(f"Sending final content (length: {len(full_content)}, events: {event_count})")
            yield f"data: {json.dumps(final_content_data)}\n\n"

            # Collect data for evaluation if enabled
            if hasattr(app.state, 'collector') and app.state.collector is not None:
                try:
                    # Reconstruct full message history from the agent
                    conversation_messages = []
                    for msg in chunk.get("messages", []):
                        conversation_messages.append(msg)
                    
                    if conversation_messages:
                        # Add as multi-turn sample
                        app.state.collector.add_multi_turn(
                            messages=conversation_messages,
                            metadata={
                                "query": last_message,
                                "timestamp": datetime.now().isoformat(),
                                "event_count": event_count,
                            }
                        )
                        app.state.interaction_count += 1
                        logger.info(f"Collected interaction #{app.state.interaction_count} with {len(conversation_messages)} messages")
                        
                        # Auto-save if interval reached
                        if app.state.interaction_count % app.state.auto_save_interval == 0:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            data_file = PROJECT_ROOT / RAGAS_DATA_DIR / f"agent_data_{timestamp}.json"
                            app.state.collector.save(data_file)
                            logger.info(f"Auto-saved {len(app.state.collector)} samples to {data_file}")
                            
                            # Clear collector after save to avoid memory buildup
                            app.state.collector.clear()
                            logger.info("Cleared collector after auto-save")
                    else:
                        logger.warning("No messages to collect for this interaction")
                except Exception as e:
                    logger.error(f"Failed to collect interaction data: {e}")

            # Signal completion
            done_event = json.dumps({'type': 'done'})
            logger.info(f"Query completed. Total events: {event_count}, Final content length: {len(full_content)}")
            yield f"data: {done_event}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            error_data = {
                "type": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


if __name__ == "__main__":
    print("Starting MSI AI Assistant API Server...")
    print("API: http://localhost:8080")
    print("Connect to Angular UI at http://localhost:4200")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

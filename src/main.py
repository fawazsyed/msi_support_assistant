"""
Support agent orchestration

Run (from project root):
uv run src/main.py
"""


import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Local imports
from src.core.utils import setup_logging
from src.core.agent import initialize_agent_components
from src.core.config import LOG_KEEP_RECENT, ENABLE_RAGAS_COLLECTION, RAGAS_DATA_DIR
from src.observability import RagasDataCollector

# Get project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent

# Setup logging
logger = setup_logging(PROJECT_ROOT, keep_recent=LOG_KEEP_RECENT)

# Load environment variables from .env file
load_dotenv()


async def main() -> None:
    """
    MSI AI Assistant - Agentic RAG system using LangChain.

    Uses an agentic approach where the LLM decides when to retrieve documentation:
    - RAG as a Tool: Documentation search is a tool the agent can choose to call
    - Efficient: Only retrieves docs when needed (not on every query)
    - Multi-capability: Combines RAG with MCP tools
    - Flexible: Agent can retrieve multiple times or skip retrieval for simple queries

    All configuration is in config.py for easy customization.
    """

    # Initialize agent using shared setup
    agent, mcp_client = await initialize_agent_components(
        project_root=PROJECT_ROOT,
        logger=logger
    )

    # Initialize Ragas data collection if enabled
    collector = None
    if ENABLE_RAGAS_COLLECTION:
        collector = RagasDataCollector()
        logger.info(f"Collector created: {collector}")
        
        # Create data directory
        data_dir = PROJECT_ROOT / RAGAS_DATA_DIR
        data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Ragas data collection enabled. Data will be saved to {data_dir}")
    
    logger.info(f"Collector after init: {collector}")

    # Test queries: mix of RAG and MCP tools
    test_queries = [
        "How do I add a new user?",  # RAG query - uses vector store
        "What is the most common ticket subject?" # MCP query - ticketing_mcp
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Question: {query}")
        print(f"{'='*60}\n")
        logger.info(f"Processing query: {query}")

        try:
            # Collect messages for this conversation
            messages = []
            retrieved_contexts = []
            final_response = ""
            
            async for step in agent.astream(
                {"messages": [{"role": "user", "content": query}]},
                stream_mode="values"
            ):
                # Display message
                step["messages"][-1].pretty_print()
                
                # Collect all messages for multi-turn evaluation
                messages = step["messages"]
                
                # Extract final response
                last_msg = step["messages"][-1]
                if hasattr(last_msg, "content"):
                    final_response = last_msg.content
                
                # TODO: Extract retrieved contexts from RAG tool calls
                # This requires inspecting ToolMessage content from search_msi_documentation
                # For now, we'll add multi-turn samples with the full conversation

            logger.info("Query completed")
            
            # Collect data for evaluation if enabled
            if collector is not None:
                try:
                    # Add as multi-turn sample (captures full agent behavior)
                    if messages:
                        collector.add_multi_turn(
                            messages=messages,
                            metadata={
                                "query": query,
                            }
                        )
                        logger.info(f"Added multi-turn sample with {len(messages)} messages")
                    else:
                        logger.warning("No messages collected for this query")
                except Exception as e:
                    logger.error(f"Failed to add sample to collector: {e}")
                    logger.exception("Full traceback:")
                
        except Exception:
            logger.exception("Query failed")
            raise
    
    # Save collected data after all queries complete
    logger.info("All queries completed, saving data...")
    if collector is not None:
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            data_file = PROJECT_ROOT / RAGAS_DATA_DIR / f"agent_data_{timestamp}.json"
            
            logger.info(f"Saving {len(collector)} samples to {data_file}")
            collector.save(data_file)
            
            logger.info(f"Collected {len(collector)} samples")
            logger.info(f"Data saved to {data_file}")
            logger.info(f"\nTo evaluate performance, run:")
            logger.info(f"  uv run python -m src.observability.evaluator {data_file} --type multi_turn")
        except Exception:
            logger.exception("Failed to save collected data")
    else:
        logger.warning("Collector was None, no data to save")


if __name__ == "__main__":
    asyncio.run(main())

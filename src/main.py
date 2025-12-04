import asyncio
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
# from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from utils import setup_logging

# MCP imports
from langchain_mcp_adapters.client import MultiServerMCPClient

# Get project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent

# Setup logging
logger = setup_logging(PROJECT_ROOT, keep_recent=10)

# Load environment variables from .env file
load_dotenv()


async def main():
    """
    MSI AI Assistant - Agentic RAG system using LangChain.

    Uses an agentic approach where the LLM decides when to retrieve documentation:
    - RAG as a Tool: Documentation search is a tool the agent can choose to call
    - Efficient: Only retrieves docs when needed (not on every query)
    - Multi-capability: Combines RAG with MCP tools (math, weather, etc.)
    - Flexible: Agent can retrieve multiple times or skip retrieval for simple queries

    Components:
    - LLM: Claude 3.5 Sonnet (alternatives: GPT-4o, Gemini 2.0 Flash)
    - Embeddings: OpenAI text-embedding-3-small
    - Vector DB: Chroma for persistent document retrieval
    - Text Splitter: RecursiveCharacterTextSplitter (1500 chars, 300 overlap)
    - Tools: MCP tools + custom RAG documentation search tool
    """
    
    """RATE LIMITING CONFIGURATION"""
    # Protect against API overspending with client-side rate limiting
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=2,  # 2 requests/second = 120 requests/minute (conservative)
        check_every_n_seconds=0.1,  # Check every 100ms
        max_bucket_size=10,  # Allow bursts of up to 10 requests
    )
    logger.info("Rate limiter configured: 2 requests/second (120 RPM)")

    """LLM CONFIGURATION"""
    # MODEL IN USE:
    model = init_chat_model(
        "gpt-4o-mini",
        model_provider="openai",
        rate_limiter=rate_limiter  # Add rate limiting to prevent API overspending
    )
    """Alternative Models"""
    # model = init_chat_model("gpt-4o", model_provider="openai", rate_limiter=rate_limiter)
    # model = init_chat_model("claude-3-5-sonnet-20241022", model_provider="anthropic", rate_limiter=rate_limiter)
    # Gemini (Free tier - requires GOOGLE_API_KEY in .env from https://makersuite.google.com/app/apikey)
    # model = init_chat_model("gemini-2.0-flash-exp", model_provider="google-genai", rate_limiter=rate_limiter)

    """EMBEDDING MODEL"""
    # OpenAI Embeddings (faster than Vertex AI)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # Alternative (not used due to initialization hanging): embeddings = VertexAIEmbeddings()
    
    """VECTOR DATABASE"""
    # Chroma - Load and index documents with persistence
    doc_path = PROJECT_ROOT / "documents" / "video_manager_admin_guide.txt"
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_content = f.read()
    except FileNotFoundError:
        logger.error(f"Document not found: {doc_path}")
        raise
    except Exception:
        logger.exception(f"Failed to load document from {doc_path}")
        raise
    
    persist_dir = str(PROJECT_ROOT / "chroma_langchain_db")
    vector_store = Chroma(
        collection_name="msi_support_docs",
        embedding_function=embeddings,
        persist_directory=persist_dir,  # Persistent storage on disk
    )
    
    """VECTOR STORE"""
    # Add documents to the vector store (only if collection is empty)
    if vector_store._collection.count() == 0:
        logger.info("Indexing documents with chunking (first run)...")
        # Split document into chunks for optimal retrieval
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,      # ~375 tokens per chunk
            chunk_overlap=300,    # 20% overlap for context continuity
            separators=["\n\n", "\n", ". ", " ", ""],  # Hierarchical splitting when possible
        )
        # TODO: Look into token-based splitting, maybe Tiktoken
        chunks = text_splitter.split_text(doc_content)
        vector_store.add_texts(texts=chunks)
        logger.info(f"Indexed {len(chunks)} document chunks")
    else:
        logger.info("Using existing vector store")
    
    """STEP 1: Create RAG tool for documentation search"""
    # Instead of middleware, we create a tool the agent can choose to call
    @tool
    def search_msi_documentation(query: str) -> str:
        """Search Motorola Solutions product documentation for information.

        Use this tool when the user asks questions about:
        - How to use MSI products (Video Manager, etc.)
        - Product features and capabilities
        - Configuration and setup instructions
        - Troubleshooting and support
        - User management and administration

        Args:
            query: The search query to find relevant documentation

        Returns:
            Relevant documentation excerpts that answer the query
        """
        retrieved_docs = vector_store.similarity_search(query, k=2)

        if not retrieved_docs:
            return "No relevant documentation found for this query."

        docs_content = "\n\n---\n\n".join(
            f"Document excerpt {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(retrieved_docs)
        )

        return docs_content

    """STEP 2: Load MCP tools from multiple servers"""
    # Configure MCP client with math (stdio) and weather (HTTP) servers
    try:
        client = MultiServerMCPClient(
            {
                "math": {
                    "command": "python",
                    "args": [str(PROJECT_ROOT / "src" / "mcp_server.py")],
                    "transport": "stdio",  # Local subprocess communication
                },
                "weather": {
                    "url": "http://localhost:8000/mcp",
                    "transport": "streamable_http",  # HTTP-based remote server
                    # Note: Weather server must be running separately on port 8000
                }
            }
        )

        # Get tools from MCP server
        mcp_tools = await client.get_tools()
        logger.info(f"Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")
    except (ConnectionError, TimeoutError, OSError):
        logger.error("Failed to connect to MCP servers. Ensure weather server is running on port 8000.")
        raise
    except Exception:
        logger.exception("Failed to load MCP tools")
        raise
    
    """STEP 3: Create agent with MCP tools AND RAG tool"""
    # Combine MCP tools with our RAG documentation search tool
    all_tools = mcp_tools + [search_msi_documentation]

    # Create tool call limit middleware to prevent runaway loops and overspending
    tool_call_limit = ToolCallLimitMiddleware(
        run_limit=15,  # Max 15 tool calls per single user query
        exit_behavior="continue"  # Continue and return response when limit hit
    )
    logger.info("Tool call limit configured: 15 calls per query")

    agent = create_agent(
        model,
        tools=all_tools,
        middleware=[tool_call_limit],  # Prevent excessive API calls
        system_prompt=(
            "You are an MSI Support Assistant powered by Motorola Solutions. "
            "You have access to product documentation via the search_msi_documentation tool. "
            "When users ask about MSI products, features, or how-to questions, "
            "use the search tool to find relevant information before answering. "
            "Always provide accurate information based on the documentation."
        )
    )
    
    """STEP 4: Run the RAG chain with MCP tools available"""
    # Test queries: mix of RAG, math tools, and weather tools
    test_queries = [
        "How do I add a new user?",  # RAG query - uses vector store
        "What is 5 + 3?",  # MCP math tool - uses add()
        "What's the magic number times 10?",  # MCP math tools - uses magic_number() and multiply()
        "What is the weather in NYC?",  # MCP weather tool - uses get_weather()
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Question: {query}")
        print(f"{'='*60}\n")
        logger.info(f"Processing query: {query}")

        try:
            async for step in agent.astream(
                {"messages": [{"role": "user", "content": query}]},
                stream_mode="values",
            ):
                step["messages"][-1].pretty_print()

            logger.info("Query completed")
        except Exception:
            logger.exception("Query failed")
            raise


if __name__ == "__main__":
    asyncio.run(main())

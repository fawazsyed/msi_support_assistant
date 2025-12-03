import asyncio
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
# from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain.chat_models import init_chat_model
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
    MSI AI Assistant - Conversational RAG system using LangChain.
    
    Uses the latest LangChain RAG chain with the following features:
    - Two-step chain: Always runs search, then generates answer in single LLM call
    - dynamic_prompt middleware: Injects retrieved context into system message
    - Single inference per query: Reduced latency vs. agentic approach
    - Document chunking: RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
    
    Components:
    - LLM: OpenAI GPT-4o (alternatives: Claude 3.5 Sonnet, Gemini 2.0 Flash)
    - Embeddings: OpenAI text-embedding-3-small
    - Vector DB: Chroma for persistent document retrieval
    - Text Splitter: RecursiveCharacterTextSplitter for optimal chunk size
    """
    
    """LLM CONFIGURATION"""
    # MODEL IN USE:
    model = init_chat_model("gpt-4o", model_provider="openai")
    """Alternative Models"""
    # model = init_chat_model("claude-3-5-sonnet-20241022", model_provider="anthropic")
    # model = init_chat_model("gemini-2.0-flash-exp", model_provider="google-vertexai")

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
    
    """STEP 1: Define dynamic prompt with context injection"""
    # This middleware retrieves documents and injects them into the system message
    @dynamic_prompt
    def prompt_with_context(request: ModelRequest) -> str:
        """Inject retrieved context into system messages."""
        last_query = request.state["messages"][-1].text
        retrieved_docs = vector_store.similarity_search(last_query, k=2)

        docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

        system_message = (
            "You are an MSI Support Assistant. Use the following context from "
            "Motorola Solutions product documentation to answer the user's question. "
            "If you don't know the answer based on the context, say so.\n\n"
            f"Context:\n{docs_content}"
        )

        return system_message

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
    
    """STEP 3: Create agent with MCP tools AND dynamic prompt middleware"""
    agent = create_agent(model, 
                         tools=mcp_tools, 
                         middleware=[prompt_with_context])
    
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

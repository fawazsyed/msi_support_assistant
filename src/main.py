from pathlib import Path
from langchain_openai import OpenAIEmbeddings
# from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain.chat_models import init_chat_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
from utils import setup_logging
from website_fetcher import fetch_multiple_urls

# Get project root (parent of src/)
PROJECT_ROOT = Path(__file__).parent.parent

# Setup logging
logger = setup_logging(PROJECT_ROOT, keep_recent=10)

# Load environment variables from .env file
load_dotenv()


def main():
    """
    MSI Support Assistant - Conversational RAG system using LangChain.
    
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
    persist_dir = str(PROJECT_ROOT / "chroma_langchain_db")
    vector_store = Chroma(
        collection_name="msi_support_docs",
        embedding_function=embeddings,
        persist_directory=persist_dir,  # Persistent storage on disk
    )
    
    """DOCUMENT SOURCES"""
    # URLs to fetch from Motorola Solutions websites
    # TODO: Replace these with actual URLs you want to index
    urls_to_fetch = [
        # "https://support.motorolasolutions.com/...",
        # "https://docs.motorolasolutions.com/...",
    ]
    
    # For now, fall back to local file if no URLs provided
    if not urls_to_fetch:
        logger.info("No URLs provided, using local document as fallback")
        doc_path = PROJECT_ROOT / "documents" / "video_manager_admin_guide.txt"
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_content = f.read()
        # Create a document list with metadata for consistency
        web_documents = [{
            "page_content": doc_content,
            "metadata": {
                "source": str(doc_path),
                "title": "Video Manager Admin Guide (Local)",
                "type": "local_file"
            }
        }]
    else:
        # Fetch documents from websites with metadata
        logger.info(f"Fetching {len(urls_to_fetch)} URLs...")
        fetched_docs = fetch_multiple_urls(urls_to_fetch, page_type="support_article")
        web_documents = [doc.to_langchain_document() for doc in fetched_docs]
        logger.info(f"Successfully processed {len(web_documents)} documents")
    
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
        
        # Process each document: split into chunks while preserving metadata
        all_chunks = []
        for web_doc in web_documents:
            # Split the text content
            chunks = text_splitter.split_text(web_doc["page_content"])
            
            # Create LangChain Document objects with metadata for each chunk
            for chunk in chunks:
                all_chunks.append(
                    Document(
                        page_content=chunk,
                        metadata=web_doc["metadata"]  # Preserve source URL, title, type
                    )
                )
        
        # Add all chunks to vector store (metadata is preserved)
        vector_store.add_documents(all_chunks)
        logger.info(f"Indexed {len(all_chunks)} document chunks from {len(web_documents)} sources")
    else:
        logger.info("Using existing vector store")
    
    """STEP 1: Define dynamic prompt with context injection"""
    # This middleware retrieves documents and injects them into the system message
    @dynamic_prompt
    def prompt_with_context(request: ModelRequest) -> str:
        """Inject retrieved context with source citations into system messages."""
        last_query = request.state["messages"][-1].text
        retrieved_docs = vector_store.similarity_search(last_query, k=3)

        # Build context with source attribution
        context_parts = []
        sources_list = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            # Extract metadata
            source_url = doc.metadata.get("source", "Unknown source")
            title = doc.metadata.get("title", "Untitled")
            
            # Add content with source marker
            context_parts.append(f"[Source {i}: {title}]\n{doc.page_content}")
            sources_list.append(f"Source {i}: {title} - {source_url}")
        
        docs_content = "\n\n---\n\n".join(context_parts)
        sources_section = "\n".join(sources_list)

        system_message = (
            "You are an MSI Support Assistant. Use the following context from "
            "Motorola Solutions product documentation to answer the user's question.\n\n"
            "IMPORTANT: When answering, cite your sources by mentioning the source number "
            "and providing the link at the end of your response.\n\n"
            "If you don't know the answer based on the context, say so.\n\n"
            f"Context:\n{docs_content}\n\n"
            f"Available Sources:\n{sources_section}"
        )

        return system_message

    """STEP 2: Create agent with no tools, just the dynamic prompt middleware"""
    agent = create_agent(model, tools=[], middleware=[prompt_with_context])
    
    """STEP 3: Run the RAG chain"""
    query = "How do I add a new user?"
    
    print(f"Question: {query}\n")
    for step in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()

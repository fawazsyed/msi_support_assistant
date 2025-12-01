from langchain_openai import OpenAIEmbeddings
# from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def main():
    """
    MSI Support Assistant - Conversational RAG system using LangChain.
    
    Uses the latest LangChain RAG chain with the following features:
    - Two-step chain: Always runs search, then generates answer in single LLM call
    - dynamic_prompt middleware: Injects retrieved context into system message
    - Single inference per query: Reduced latency vs. agentic approach
    
    Components:
    - LLM: OpenAI GPT-4o (alternatives: Claude 3.5 Sonnet, Gemini 2.0 Flash)
    - Embeddings: OpenAI text-embedding-3-small
    - Vector DB: Chroma for persistent document retrieval
    """
    
    # LLM CONFIGURATION - Using init_chat_model (official pattern)
    model = init_chat_model("gpt-4o", model_provider="openai")
    # Alternative models:
    # model = init_chat_model("claude-3-5-sonnet-20241022", model_provider="anthropic")
    # model = init_chat_model("gemini-2.0-flash-exp", model_provider="google-vertexai")

    # EMBEDDING MODEL - OpenAI Embeddings (faster than Vertex AI)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    # Alternative (not used due to initialization hanging): embeddings = VertexAIEmbeddings()
    
    # VECTOR DATABASE - Chroma - Load and index documents with persistence
    with open("documents/video_manager_admin_guide_user.txt", "r", encoding="utf-8") as f:
        doc_content = f.read()
    
    vector_store = Chroma(
        collection_name="msi_support_docs",
        embedding_function=embeddings,
        persist_directory="./chroma_langchain_db",  # Persistent storage on disk
    )
    
    # Add documents to the vector store (only if collection is empty)
    if vector_store._collection.count() == 0:
        vector_store.add_texts(texts=[doc_content])
    
    # STEP 1: Define dynamic prompt with context injection
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

    # STEP 2: Create agent with no tools, just the dynamic prompt middleware
    agent = create_agent(model, tools=[], middleware=[prompt_with_context])
    
    # STEP 3: Run the RAG chain
    query = "How do I add a new user?"
    
    print(f"Question: {query}\n")
    for step in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        stream_mode="values",
    ):
        step["messages"][-1].pretty_print()


if __name__ == "__main__":
    main()

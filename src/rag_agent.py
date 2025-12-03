"""
RAG Agent for Motorola Documentation Assistant.

This agent implements RAG following LangChain tutorial patterns:
1. Uses agent with retrieval tool for flexible search
2. Supports multi-turn conversations with memory
3. Synthesizes answers with source citations

Usage:
    python src/rag_agent.py "How do I configure my storage?"
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent

# Load environment variables
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


def setup_vector_store(persist_dir: str, collection_name: str = "motorola_docs_prototype"):
    """
    Setup vector store connection following LangChain pattern.
    
    Args:
        persist_dir: Directory containing the vector store
        collection_name: Name of the Chroma collection
        
    Returns:
        Chroma vector store instance
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_store = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings,
        collection_name=collection_name
    )
    
    print(f"[+] Connected to vector store: {persist_dir}")
    
    return vector_store


def create_retrieval_tool(vector_store):
    """
    Create a retrieval tool following LangChain RAG tutorial pattern.
    
    Uses @tool decorator with response_format="content_and_artifact" to attach
    raw documents as artifacts to ToolMessage.
    
    Args:
        vector_store: Chroma vector store instance
        
    Returns:
        Retrieval tool function
    """
    @tool(response_format="content_and_artifact")
    def retrieve_context(query: str):
        """Retrieve information from Motorola VideoManager documentation to help answer a query."""
        retrieved_docs = vector_store.similarity_search(query, k=2)
        
        serialized_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            title = doc.metadata.get('title', 'Unknown')
            url = doc.metadata.get('url', '')
            source_type = doc.metadata.get('source_type', 'unknown')
            
            serialized_parts.append(
                f"[Document {i}]\n"
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Type: {source_type}\n"
                f"Content:\n{doc.page_content}\n"
                f"---"
            )
        
        serialized = "\n\n".join(serialized_parts)
        return serialized, retrieved_docs
    
    return retrieve_context


def create_rag_agent(vector_store_dir: str, collection_name: str = "motorola_docs_prototype"):
    """
    Create RAG agent following LangChain tutorial pattern.
    
    This implements the "RAG agents" approach from the tutorial:
    - Agent with retrieval tool for flexible search
    - LLM decides when to search and what queries to issue
    - Supports iterative searches for complex queries
    
    Args:
        vector_store_dir: Directory containing vector store
        collection_name: Name of Chroma collection
        
    Returns:
        Configured agent
    """
    # Setup vector store
    vector_store = setup_vector_store(vector_store_dir, collection_name)
    
    # Create retrieval tool
    retrieve_tool = create_retrieval_tool(vector_store)
    tools = [retrieve_tool]
    
    # Initialize LLM
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create agent with custom system prompt
    system_prompt = """You are a helpful Motorola VideoManager documentation assistant.

Guidelines:
- Use the retrieve_context tool to search documentation when needed
- Provide clear, accurate answers based ONLY on the retrieved documentation
- Do not make assumptions or use outside knowledge
- IMPORTANT: Cite sources by mentioning the SPECIFIC document title and its URL
- Each retrieved document has its own Title and URL - cite the SPECIFIC page you're referencing
- If the documentation doesn't contain the answer, say so honestly
- Include step-by-step procedures when applicable
- For complex questions, you can search multiple times with different queries

CITATION FORMAT:
Always end your response with a "Sources:" section that lists:
- The specific document title (e.g., "Device Permissions", "RFID Configuration")
- The complete URL for that specific page
- Do NOT just cite "Motorola Documentation" - cite the SPECIFIC pages

Example:
Sources:
- Device Permissions: https://docs.motorolasolutions.com/bundle/89303/page/94516ad6.html#a4ff3992
- RFID Configuration: https://docs.motorolasolutions.com/bundle/89303/page/4a801fc3.html#f7c77368"""
    
    agent = create_agent(model, tools, system_prompt=system_prompt)
    
    print("[+] RAG Agent initialized with retrieval tool")
    return agent


async def main():
    """Main entry point for the RAG agent following LangChain tutorial pattern."""
    
    # Get question from command line or use default
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        # Default test questions for Motorola docs
        test_questions = [
            "How do I configure my storage?",
            "What are the steps for device assignment?",
            "How do I manage user permissions?",
        ]
        
        print("=" * 70)
        print("RAG AGENT - INTERACTIVE MODE")
        print("=" * 70)
        print("\nNo question provided. Choose a test question:")
        for i, q in enumerate(test_questions, 1):
            print(f"  {i}. {q}")
        print(f"  {len(test_questions) + 1}. Enter custom question")
        
        try:
            choice = input("\nSelect (1-4): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(test_questions):
                question = test_questions[choice_num - 1]
            else:
                question = input("Enter your question: ").strip()
        except (ValueError, KeyboardInterrupt):
            print("\n[X] Invalid choice or cancelled")
            return
    
    # Initialize agent
    vector_store_dir = str(PROJECT_ROOT / "python_docs_index_prototype")
    
    if not Path(vector_store_dir).exists():
        print(f"[X] Error: Vector store not found at {vector_store_dir}")
        print("    Run prototype_indexer.py first to build the index.")
        return
    
    # Create agent following LangChain tutorial pattern
    agent = create_rag_agent(vector_store_dir)
    
    # Stream agent responses following tutorial pattern
    print("\n" + "=" * 70)
    print("RAG AGENT - ANSWERING QUESTION")
    print("=" * 70)
    print(f"Question: {question}\n")
    
    print("[+] Streaming agent responses...\n")
    
    for event in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        event["messages"][-1].pretty_print()


if __name__ == "__main__":
    asyncio.run(main())

"""
Document Indexer for Motorola Support Assistant.

This script implements the "Indexing" phase from LangChain RAG tutorial:
1. Load: Load documents from JSON file
2. Split: Use RecursiveCharacterTextSplitter to chunk documents
3. Store: Embed chunks and store in Chroma vector database

Follows LangChain tutorial pattern:
https://python.langchain.com/docs/tutorials/rag/

Usage:
    python src/prototype_indexer.py [filename]
    python src/prototype_indexer.py motorola_docs.json
"""

import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


def load_crawled_documents(filename: str = "prototype_documents.json") -> List[Dict]:
    """Load documents from JSON file."""
    filepath = PROJECT_ROOT / "data" / filename
    
    if not filepath.exists():
        print(f"[X] File not found: {filepath}")
        print("   Run prototype_crawler.py first to generate documents.")
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    print(f"[+] Loaded {len(documents)} documents from {filename}")
    return documents


def build_vector_index(documents: List[Dict], collection_name: str = "motorola_docs_prototype"):
    """
    Build vector database index following LangChain RAG tutorial pattern.
    
    Indexing pipeline (from tutorial):
    1. Load: Convert JSON documents to LangChain Document objects
    2. Split: Use RecursiveCharacterTextSplitter to chunk documents
    3. Store: Embed chunks and store in vector database
    
    Args:
        documents: List of document dicts from crawler
        collection_name: Name for Chroma collection
        
    Returns:
        Chroma vector store instance
    """
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    import shutil
    
    if not documents:
        print("[X] No documents to index")
        return None
    
    # Clear existing vector store to prevent duplicates
    persist_dir = PROJECT_ROOT / "python_docs_index_prototype"
    if persist_dir.exists():
        print(f"\n[!] Existing vector store found: {persist_dir}")
        print("    Attempting to remove...")
        try:
            import time
            time.sleep(0.5)  # Brief pause to release any file locks
            shutil.rmtree(persist_dir)
            print("    [+] Successfully removed old index")
        except PermissionError:
            print("    [!] Warning: Could not remove old index (files may be locked)")
            print("    [!] This may result in duplicate entries")
            print("    [!] Try closing other applications or restart your terminal")
    
    print(f"\n[+] Building vector index following LangChain tutorial pattern...")
    print(f"   Embedding model: text-embedding-3-small")
    print(f"   Collection: {collection_name}")
    
    # Step 1: LOAD - Convert to LangChain Documents
    print(f"\n   [1/3] LOAD: Converting {len(documents)} documents...")
    langchain_docs = []
    
    for doc in documents:
        # Skip documents without content
        if not doc.get("full_content"):
            print(f"      [!] Skipping {doc.get('title', 'Unknown')}: Missing content")
            continue
        
        langchain_docs.append(
            Document(
                page_content=doc["full_content"],  # Content to be chunked and embedded
                metadata={
                    "title": doc["title"],
                    "url": doc["url"],
                    "source_type": doc["source_type"]
                }
            )
        )
    
    print(f"      [+] Loaded {len(langchain_docs)} documents")
    
    # Step 2: SPLIT - Chunk documents using RecursiveCharacterTextSplitter
    print(f"\n   [2/3] SPLIT: Chunking documents...")
    print(f"      chunk_size=1000, chunk_overlap=200")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,        # Maximum chunk size in characters
        chunk_overlap=500,      # Overlap between chunks for context
        add_start_index=True    # Track position in original document
    )
    
    all_splits = text_splitter.split_documents(langchain_docs)
    print(f"      [+] Split into {len(all_splits)} chunks")
    
    # Step 3: STORE - Embed and index in vector database
    print(f"\n   [3/3] STORE: Embedding and indexing chunks...")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    persist_dir_str = str(persist_dir)
    
    # Use Chroma.from_documents() as shown in tutorial
    vector_store = Chroma.from_documents(
        documents=all_splits,
        embedding=embeddings,
        persist_directory=persist_dir_str,
        collection_name=collection_name
    )
    
    print(f"      [+] Indexed {len(all_splits)} chunks from {len(langchain_docs)} documents")
    print(f"      [+] Stored in: {persist_dir_str}")
    
    return vector_store


def test_semantic_search(vector_store, test_queries: List[str] = None):
    """
    Test semantic search with sample queries.
    
    Tests the retrieval component of RAG by performing similarity searches.
    
    Args:
        vector_store: Chroma vector store
        test_queries: List of test queries (uses defaults if None)
    """
    if test_queries is None:
        # Sample queries relevant to Motorola VideoManager documentation
        test_queries = [
            "how to configure storage settings",
            "device assignment procedures",
            "managing user permissions",
            "RFID configuration",
            "deletion policy settings",
        ]
    
    print("\n" + "=" * 70)
    print("TESTING SEMANTIC SEARCH")
    print("=" * 70)
    print("\nTesting retrieval with sample queries...")
    print("This demonstrates the 'Retrieve' step of RAG.\n")
    
    for query in test_queries:
        print(f"\n[?] Query: '{query}'")
        print("-" * 70)
        
        # Perform similarity search with scores (k=3 chunks returned)
        results = vector_store.similarity_search_with_score(query, k=3)
        
        if not results:
            print("   [X] No results found")
            continue
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n   {i}. {doc.metadata['title']}")
            print(f"      Relevance: {1 - score:.3f}")  # Convert distance to similarity
            print(f"      URL: {doc.metadata['url']}")
            print(f"      Content preview: {doc.page_content[:120]}...")


def interactive_search(vector_store):
    """
    Interactive search mode - query the index manually.
    """
    print("\n" + "=" * 70)
    print("INTERACTIVE SEARCH MODE")
    print("=" * 70)
    print("Enter queries to search the document index.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            query = input("[?] Search: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("[+] Exiting interactive mode")
                break
            
            if not query:
                continue
            
            # Search
            results = vector_store.similarity_search_with_score(query, k=5)
            
            if not results:
                print("   [X] No results found\n")
                continue
            
            print(f"\n[+] Found {len(results)} results:")
            for i, (doc, score) in enumerate(results, 1):
                print(f"\n   {i}. {doc.metadata['title']}")
                print(f"      Relevance: {1 - score:.3f}")
                print(f"      URL: {doc.metadata['url']}")
                print(f"      Type: {doc.metadata['source_type']}")
            
            print()  # Extra line for readability
            
        except KeyboardInterrupt:
            print("\n[+] Exiting interactive mode")
            break
        except Exception as e:
            print(f"   [X] Error: {e}\n")


def main(filename: str = "motorola_docs.json"):
    """
    Main indexer pipeline with hybrid approach.
    
    Implements enhanced indexing:
    1. Generate LLM descriptions for semantic search
    2. Load documents from JSON
    3. Split into chunks
    4. Embed descriptions + store chunks in vector database
    
    Args:
        filename: JSON file with crawled documents (default: motorola_docs.json)
    """
    print("=" * 70)
    print("HYBRID RAG INDEXER")
    print("=" * 70)
    print("\nImplementing hybrid indexing pipeline:")
    print("  1. GENERATE - Create LLM descriptions (better search)")
    print("  2. LOAD     - Load documents")
    print("  3. SPLIT    - Chunk full content (detailed retrieval)")
    print("  4. STORE    - Embed and index in Chroma")
    
    # Load crawled documents
    documents = load_crawled_documents(filename)
    
    if not documents:
        return
    
    # Display summary
    print(f"\n[+] Document Summary:")
    print(f"   Total documents: {len(documents)}")
    
    # Check source types
    source_types = {}
    for d in documents:
        src_type = d.get('source_type', 'unknown')
        source_types[src_type] = source_types.get(src_type, 0) + 1
    
    for src_type, count in source_types.items():
        print(f"   {src_type}: {count}")
    
    # Check for content (note: field name is "content" not "full_content")
    with_content = sum(1 for d in documents if d.get("content"))
    print(f"   With content: {with_content}/{len(documents)}")
    
    if with_content == 0:
        print("\n[X] No documents have content!")
        print("   The crawler may have failed to extract content.")
        print("   Check the crawled data or re-run the crawler.")
        return
    
    # Build vector index (Load -> Split -> Store)
    vector_store = build_vector_index(documents)
    
    if not vector_store:
        return
    
    print("\n" + "=" * 70)
    print("INDEXING COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Run 'python src/rag_agent.py \"your question\"' to test RAG")
    print("  2. Or continue below for search testing")
    
    # Optional: Test with predefined queries
    print("\n" + "=" * 70)
    response = input("\nWould you like to test semantic search? (y/n): ").strip().lower()
    
    if response in ['y', 'yes']:
        test_semantic_search(vector_store)
        
        # Optional: Interactive search
        response = input("\nWould you like to try interactive search? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            interactive_search(vector_store)


if __name__ == "__main__":
    import sys
    # Default to motorola_docs.json (updated from prototype_documents.json)
    filename = sys.argv[1] if len(sys.argv) > 1 else "motorola_docs.json"
    main(filename)

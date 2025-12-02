"""
Prototype Document Indexer for Motorola Support Assistant.

This script takes crawled documents and:
1. Loads documents from prototype_documents.json
2. Embeds descriptions using OpenAI embeddings
3. Stores in Chroma vector database
4. Tests semantic search functionality

Usage:
    python src/prototype_indexer.py
"""

import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


def load_crawled_documents(filename: str = "motorola_documents.json") -> List[Dict]:
    """Load documents from JSON file."""
    filepath = PROJECT_ROOT / "data" / filename
    
    if not filepath.exists():
        print(f"[X] File not found: {filepath}")
        print("   Run prototype_crawler.py first to generate documents.")
        print(f"   Looking for: {filename}")
        print(f"   Use 'prototype_documents.json' for Python docs (18 pages)")
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    print(f"[+] Loaded {len(documents)} documents from {filename}")
    return documents


def build_vector_index(documents: List[Dict], collection_name: str = "motorola_docs_prototype"):
    """
    Build vector database index from crawled documents.
    
    Indexes the 'description' field for semantic search.
    Stores metadata: title, url, source_type
    """
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document
    import shutil
    
    if not documents:
        print("[X] No documents to index")
        return None
    
    # Clear existing vector store to prevent duplicates
    persist_dir = PROJECT_ROOT / "motorola_docs_index_prototype"
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
    
    print(f"\n[+] Building vector index...")
    print(f"   Embedding model: text-embedding-3-small")
    print(f"   Collection: {collection_name}")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Convert to LangChain Documents
    # We embed the DESCRIPTION (for semantic search)
    # And store the full metadata for retrieval
    langchain_docs = []
    
    for doc in documents:
        # Skip documents without descriptions
        if not doc.get("description"):
            print(f"   [!] Skipping {doc.get('title', 'Unknown')}: No description")
            continue
        
        langchain_docs.append(
            Document(
                page_content=doc["description"],  # This gets embedded
                metadata={
                    "title": doc["title"],
                    "url": doc["url"],
                    "source_type": doc["source_type"],
                    "content_snippet": doc.get("content_snippet", "")[:500]  # First 500 chars
                }
            )
        )
    
    print(f"   Processing {len(langchain_docs)} documents...")
    
    # Create vector store
    persist_dir_str = str(persist_dir)
    
    vector_store = Chroma.from_documents(
        documents=langchain_docs,
        embedding=embeddings,
        persist_directory=persist_dir_str,
        collection_name=collection_name
    )
    
    print(f"   [+] Indexed {len(langchain_docs)} documents")
    print(f"   [+] Stored in: {persist_dir_str}")
    
    return vector_store


def test_semantic_search(vector_store, test_queries: List[str] = None):
    """
    Test semantic search with sample queries.
    
    Args:
        vector_store: Chroma vector store
        test_queries: List of test queries (uses defaults if None)
    """
    if test_queries is None:
        test_queries = [
            "how to work with JSON files",
            "parse dates and times",
            "regular expressions python",
            "asynchronous programming",
            "read CSV files",
            "network requests http",
            "iterate over collections efficiently",
        ]
    
    print("\n" + "=" * 70)
    print("TESTING SEMANTIC SEARCH")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n[?] Query: '{query}'")
        print("-" * 70)
        
        # Perform similarity search with scores
        results = vector_store.similarity_search_with_score(query, k=3)
        
        if not results:
            print("   [X] No results found")
            continue
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n   {i}. {doc.metadata['title']}")
            print(f"      Relevance: {1 - score:.3f}")  # Convert distance to similarity
            print(f"      URL: {doc.metadata['url']}")
            print(f"      Description: {doc.page_content[:150]}...")


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


def main():
    """Main indexer pipeline."""
    print("=" * 70)
    print("MOTOROLA DOCS PROTOTYPE INDEXER")
    print("=" * 70)
    
    # Step 1: Load crawled documents
    documents = load_crawled_documents()
    
    if not documents:
        return
    
    # Display summary
    print(f"\n[+] Document Summary:")
    print(f"   Total: {len(documents)}")
    print(f"   Support articles: {sum(1 for d in documents if d['source_type'] == 'support')}")
    print(f"   Technical docs: {sum(1 for d in documents if d['source_type'] == 'docs')}")
    
    # Check for descriptions
    with_descriptions = sum(1 for d in documents if d.get("description"))
    print(f"   With descriptions: {with_descriptions}/{len(documents)}")
    
    if with_descriptions == 0:
        print("\n[X] No documents have descriptions!")
        print("   The crawler may have failed to generate descriptions.")
        print("   Check the crawled data or re-run the crawler.")
        return
    
    # Step 2: Build vector index
    vector_store = build_vector_index(documents)
    
    if not vector_store:
        return
    
    # Step 3: Test with predefined queries
    test_semantic_search(vector_store)
    
    # Step 4: Interactive search (optional)
    print("\n" + "=" * 70)
    response = input("Would you like to try interactive search? (y/n): ").strip().lower()
    
    if response in ['y', 'yes']:
        interactive_search(vector_store)
    
    print("\n[+] Prototype indexing complete!")
    print("\nNext steps:")
    print("  1. Review search quality - are relevant docs being found?")
    print("  2. Adjust description generation prompts if needed")
    print("  3. Crawl more pages to build a larger index")
    print("  4. Integrate with LangChain agent for full RAG pipeline")


if __name__ == "__main__":
    main()

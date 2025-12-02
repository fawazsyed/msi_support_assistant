"""
RAG Agent for Python Documentation Assistant.

This agent orchestrates the query-time workflow:
1. Takes user question
2. Searches vector database for relevant docs (semantic search)
3. Fetches full content from top 2-3 URLs
4. Synthesizes answer with source citations

Usage:
    python src/rag_agent.py "How do I parse JSON in Python?"
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


class DocumentRetriever:
    """
    Tool for semantic search over indexed documentation.
    Returns top-k relevant URLs with metadata.
    """
    
    def __init__(self, persist_dir: str, collection_name: str = "motorola_docs_prototype"):
        """Initialize the vector store connection."""
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        print(f"[+] Connected to vector store: {persist_dir}")
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        
        Args:
            query: User's question
            k: Number of results to return (default 3)
            
        Returns:
            List of documents with metadata (title, url, description, score)
        """
        print(f"\n[?] Searching for: '{query}'")
        
        # Perform similarity search with scores
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "title": doc.metadata.get("title", "Unknown"),
                "url": doc.metadata["url"],
                "description": doc.page_content,
                "snippet": doc.metadata.get("content_snippet", "")[:200],
                "relevance_score": 1 - score  # Convert distance to similarity
            })
        
        print(f"[+] Found {len(formatted_results)} relevant documents")
        for i, result in enumerate(formatted_results, 1):
            print(f"    {i}. {result['title']}")
            print(f"       Score: {result['relevance_score']:.3f}")
            print(f"       URL: {result['url']}")
        
        return formatted_results


class ContentFetcher:
    """
    Tool for fetching full content from URLs.
    Uses Crawl4AI to get latest page content.
    """
    
    async def fetch(self, url: str) -> Dict[str, str]:
        """
        Fetch full content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with url, title, and content (markdown)
        """
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        
        print(f"[+] Fetching content from: {url}")
        
        try:
            browser_config = BrowserConfig(headless=True, verbose=False)
            crawler_config = CrawlerRunConfig(
                page_timeout=15000,
                word_count_threshold=10
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url, config=crawler_config)
                
                if result.success:
                    content_length = len(result.markdown.raw_markdown)
                    print(f"    [+] Success: {content_length} chars")
                    
                    return {
                        "url": url,
                        "title": result.metadata.get("title", "Unknown"),
                        "content": result.markdown.raw_markdown[:8000]  # Limit to 8k chars
                    }
                else:
                    print(f"    [X] Failed: {result.error_message}")
                    return {
                        "url": url,
                        "title": "Error",
                        "content": f"Failed to fetch: {result.error_message}"
                    }
        except Exception as e:
            print(f"    [X] Exception: {e}")
            return {
                "url": url,
                "title": "Error",
                "content": f"Exception: {str(e)}"
            }
    
    async def fetch_multiple(self, urls: List[str]) -> List[Dict[str, str]]:
        """Fetch content from multiple URLs concurrently."""
        print(f"\n[+] Fetching content from {len(urls)} URLs...")
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results


class RAGAgent:
    """
    Main RAG agent that orchestrates search, retrieval, and answer generation.
    """
    
    def __init__(self, vector_store_dir: str):
        """Initialize the agent with retriever and LLM."""
        self.retriever = DocumentRetriever(vector_store_dir)
        self.fetcher = ContentFetcher()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Prompt for answer synthesis
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful Python documentation assistant. 
Your job is to answer questions about Python using the provided documentation.

Guidelines:
- Provide clear, accurate answers based ONLY on the documentation provided
- Include code examples when relevant
- Cite your sources by mentioning the document title
- If the documentation doesn't contain the answer, say so honestly
- Be concise but thorough

Always end your answer with a "Sources:" section listing the URLs used."""),
            ("user", """Question: {question}

Documentation:
{context}

Please provide a comprehensive answer with code examples if applicable.""")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
        
        print("[+] RAG Agent initialized")
    
    async def answer(self, question: str, num_docs: int = 3) -> Dict[str, Any]:
        """
        Answer a question using RAG pipeline.
        
        Args:
            question: User's question
            num_docs: Number of documents to retrieve
            
        Returns:
            Dict with answer, sources, and metadata
        """
        print("\n" + "=" * 70)
        print("RAG AGENT - ANSWERING QUESTION")
        print("=" * 70)
        print(f"Question: {question}\n")
        
        # Step 1: Semantic search for relevant docs
        relevant_docs = self.retriever.search(question, k=num_docs)
        
        if not relevant_docs:
            return {
                "question": question,
                "answer": "I couldn't find any relevant documentation for your question.",
                "sources": [],
                "num_sources_retrieved": 0
            }
        
        # Step 2: Fetch full content from top URLs
        urls_to_fetch = [doc["url"] for doc in relevant_docs]
        fetched_content = await self.fetcher.fetch_multiple(urls_to_fetch)
        
        # Step 3: Build context from fetched content
        context_parts = []
        for i, content_doc in enumerate(fetched_content, 1):
            context_parts.append(f"""
Document {i}: {content_doc['title']}
URL: {content_doc['url']}

{content_doc['content']}

---
""")
        
        context = "\n".join(context_parts)
        
        # Step 4: Generate answer using LLM
        print(f"\n[+] Generating answer with LLM...")
        answer = await self.chain.ainvoke({
            "question": question,
            "context": context
        })
        
        # Step 5: Format response
        response = {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "title": doc["title"],
                    "url": doc["url"],
                    "relevance": doc["relevance_score"]
                }
                for doc in relevant_docs
            ],
            "num_sources_retrieved": len(relevant_docs)
        }
        
        return response
    
    def format_response(self, response: Dict[str, Any]) -> str:
        """Format the response for display."""
        output = []
        output.append("\n" + "=" * 70)
        output.append("ANSWER")
        output.append("=" * 70)
        output.append(f"\nQuestion: {response['question']}\n")
        output.append(response['answer'])
        output.append("\n" + "=" * 70)
        output.append(f"Retrieved {response['num_sources_retrieved']} sources")
        output.append("=" * 70)
        
        return "\n".join(output)


async def main():
    """Main entry point for the RAG agent."""
    
    # Get question from command line or use default
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        # Default test questions
        test_questions = [
            "How do I parse JSON in Python?",
            "What's the best way to work with dates and times?",
            "How can I make HTTP requests in Python?",
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
    
    agent = RAGAgent(vector_store_dir)
    
    # Get answer
    response = await agent.answer(question)
    
    # Display result
    print(agent.format_response(response))


if __name__ == "__main__":
    asyncio.run(main())

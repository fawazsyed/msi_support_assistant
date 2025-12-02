"""
Prototype Document Discovery Crawler for Python.org Documentation.

This script crawls a small sample (15-20 pages) to validate the approach:
1. Discover pages from Python.org library documentation
2. Extract title and content snippet
3. Generate searchable descriptions with LLM
4. Build vector index for semantic search
5. Test search quality

Usage:
    python src/prototype_crawler.py
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sample URLs: Motorola documentation pages (active)
SAMPLE_URLS = [
    "https://docs.motorolasolutions.com/bundle/89303/page/23111842.html",
    # Add more Motorola doc URLs here as you discover them
]

# Python.org URLs (commented out for reference)
"""
SAMPLE_URLS = [
    # Core modules
    "https://docs.python.org/3/library/json.html",
    "https://docs.python.org/3/library/pathlib.html",
    "https://docs.python.org/3/library/os.html",
    "https://docs.python.org/3/library/sys.html",
    "https://docs.python.org/3/library/datetime.html",
    
    # Text processing
    "https://docs.python.org/3/library/re.html",
    "https://docs.python.org/3/library/string.html",
    "https://docs.python.org/3/library/textwrap.html",
    
    # Data formats
    "https://docs.python.org/3/library/csv.html",
    "https://docs.python.org/3/library/configparser.html",
    
    # Collections
    "https://docs.python.org/3/library/collections.html",
    "https://docs.python.org/3/library/itertools.html",
    "https://docs.python.org/3/library/functools.html",
    
    # Async
    "https://docs.python.org/3/library/asyncio.html",
    "https://docs.python.org/3/library/threading.html",
    
    # Network/Web
    "https://docs.python.org/3/library/urllib.html",
    "https://docs.python.org/3/library/http.html",
    
    # Utilities
    "https://docs.python.org/3/library/logging.html",
]
"""

PROJECT_ROOT = Path(__file__).parent.parent


async def test_crawl4ai():
    """Test that Crawl4AI is working correctly."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        
        print("Testing Crawl4AI installation...")
        
        browser_config = BrowserConfig(headless=True, verbose=True)
        crawler_config = CrawlerRunConfig(
            page_timeout=20000,  # Python docs load fast
            css_selector="section[id='module-contents'], article[role='main']"
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                "https://support.motorolasolutions.com/s/?language=en_US&region=NA",
                config=crawler_config
            )
            
            if result.success:
                print(f"✅ Crawl4AI working! Fetched {len(result.markdown)} chars of content")
                print(f"   Title: {result.metadata.get('title', 'N/A')}")
                print(f"   Links found: {len(result.links.get('internal', []))}")
                return True
            else:
                print(f"❌ Crawl failed: {result.error_message}")
                return False
                
    except ImportError as e:
        print(f"❌ Crawl4AI not installed: {e}")
        print("Run: uv sync")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def discover_sample_pages(start_url: str, max_pages: int = 15) -> List[str]:
    """
    Discover documentation pages from a starting URL.
    
    Args:
        start_url: Starting page to crawl
        max_pages: Maximum number of pages to discover
        
    Returns:
        List of discovered URLs
    """
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    
    discovered_urls = []
    
    async with AsyncWebCrawler() as crawler:
        print(f"\n🔍 Discovering pages from: {start_url}")
        
        result = await crawler.arun(start_url)
        
        if result.success:
            internal_links = result.links.get("internal", [])
            
            # Filter for documentation/article pages
            for link in internal_links:
                if is_documentation_page(link) and link not in discovered_urls:
                    discovered_urls.append(link)
                    
                    if len(discovered_urls) >= max_pages:
                        break
            
            print(f"   Found {len(discovered_urls)} documentation URLs")
        else:
            print(f"   ❌ Failed to crawl starting page: {result.error_message}")
    
    return discovered_urls


def is_documentation_page(url: str) -> bool:
    """
    Filter function to identify documentation/article pages.
    
    Adjust these patterns based on what you discover on Motorola sites.
    """
    doc_patterns = [
        "/article/",
        "/guide/",
        "/documentation/",
        "/bundle/",
        "/s/article",
    ]
    
    # Exclude non-documentation pages
    exclude_patterns = [
        "/tag/",
        "/search",
        "/login",
        "/profile",
        "/contact",
    ]
    
    has_doc_pattern = any(pattern in url for pattern in doc_patterns)
    has_exclude = any(pattern in url for pattern in exclude_patterns)
    
    return has_doc_pattern and not has_exclude


async def crawl_pages(urls: List[str]) -> List[Dict]:
    """
    Crawl multiple pages and extract basic information.
    
    Args:
        urls: List of URLs to crawl
        
    Returns:
        List of document dictionaries with title, url, content_snippet
    """
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    
    documents = []
    
    # Configure browser for JavaScript-heavy sites
    browser_config = BrowserConfig(
        headless=True,
        verbose=False
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        print(f"\n📄 Crawling {len(urls)} pages (waiting for JS content)...")
        
        # Use arun_many for concurrent crawling
        results = await crawler.arun_many(
            urls=urls,
            config=CrawlerRunConfig(
                page_timeout=60000,  # 60 seconds for slow JS loads
                # Wait for article content OR main content div to appear
                wait_for="js:() => document.querySelector('article') !== null || document.querySelector('.main-content') !== null || document.body.innerText.length > 1000",
                remove_overlay_elements=True,
                # Delay to ensure JS finishes executing
                delay_before_return_html=3.0  # Wait 3 seconds after page "loads"
            ),
            max_concurrent=2  # Slower to be respectful
        )
        
        for result in results:
            if result.success:
                # Validate that we got real content (not just "Loading" or cookie banners)
                content = result.markdown
                is_valid = (
                    len(content) > 500 and  # Has substantial content
                    not content.startswith("Loading\nCookie") and  # Not stuck on loading page
                    "Cookie Preferences" not in content[:200]  # Cookie banner not dominating
                )
                
                if is_valid:
                    doc = {
                        "title": result.metadata.get("title", "Untitled"),
                        "url": result.url,
                        "content_snippet": result.markdown[:1000],  # First 1000 chars
                        "full_content": result.markdown,  # Keep for testing
                        "links": len(result.links.get("internal", [])),
                        "source_type": "support" if "support" in result.url else "docs",
                        "crawled_at": datetime.now().isoformat()
                    }
                    documents.append(doc)
                    print(f"   ✅ {doc['title'][:60]} ({len(content)} chars)")
                else:
                    print(f"   ⚠️  Invalid content (JS may not have loaded): {result.url}")
            else:
                print(f"   ❌ Failed: {result.url}")
    
    print(f"\n✅ Successfully crawled {len(documents)} pages")
    return documents


async def generate_descriptions(documents: List[Dict]) -> List[Dict]:
    """
    Generate searchable descriptions for each document using LLM.
    
    Args:
        documents: List of document dictionaries
        
    Returns:
        Same list with 'description' field added
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    print(f"\n🤖 Generating descriptions with GPT-4o-mini...")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    prompt = ChatPromptTemplate.from_template(
        """You are analyzing Motorola Solutions technical documentation.
        Generate a concise 2-3 sentence description that:
        1. Explains what the document covers (product features, troubleshooting, setup, etc.)
        2. Lists key topics and use cases
        3. Uses terminology that technical support staff and users would search for
        
        Title: {title}
        Content Preview: {content}
        
        Description (2-3 sentences):"""
    )
    
    for i, doc in enumerate(documents, 1):
        try:
            response = await llm.ainvoke(
                prompt.format_messages(
                    title=doc["title"],
                    content=doc["content_snippet"]
                )
            )
            doc["description"] = response.content.strip()
            print(f"   {i}/{len(documents)} ✅ {doc['title'][:50]}")
            
        except Exception as e:
            print(f"   {i}/{len(documents)} ❌ Failed: {e}")
            doc["description"] = doc["content_snippet"][:200]  # Fallback
    
    return documents


def save_documents(documents: List[Dict], filename: str = "motorola_documents.json"):
    """Save crawled documents to JSON file."""
    output_path = PROJECT_ROOT / "data" / filename
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(documents)} documents to: {output_path}")
    return output_path


def load_documents(filename: str = "motorola_documents.json") -> List[Dict]:
    """Load documents from JSON file."""
    filepath = PROJECT_ROOT / "data" / filename
    
    if not filepath.exists():
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


async def main():
    """Main prototype pipeline."""
    print("=" * 70)
    print("MOTOROLA DOCS PROTOTYPE CRAWLER")
    print("=" * 70)
    
    # Step 1: Test Crawl4AI
    if not await test_crawl4ai():
        print("\n❌ Crawl4AI test failed. Fix installation before continuing.")
        return
    
    # Step 2: Use predefined sample URLs or discover new ones
    if SAMPLE_URLS:
        print(f"\n📋 Using {len(SAMPLE_URLS)} predefined sample URLs")
        urls = SAMPLE_URLS
    else:
        # Discover from start page
        urls = await discover_sample_pages(
            "https://support.motorolasolutions.com/s/?language=en_US&region=NA",
            max_pages=15
        )
    
    if not urls:
        print("\n❌ No URLs to crawl. Add some to SAMPLE_URLS in the script.")
        return
    
    # Step 3: Crawl pages
    documents = await crawl_pages(urls)
    
    if not documents:
        print("\n❌ No documents crawled successfully.")
        return
    
    # Step 4: Generate descriptions
    documents = await generate_descriptions(documents)
    
    # Step 5: Save to file
    save_documents(documents)
    
    # Step 6: Display summary
    print("\n" + "=" * 70)
    print("PROTOTYPE SUMMARY")
    print("=" * 70)
    print(f"Total documents: {len(documents)}")
    print(f"Support articles: {sum(1 for d in documents if d['source_type'] == 'support')}")
    print(f"Technical docs: {sum(1 for d in documents if d['source_type'] == 'docs')}")
    print("\nSample descriptions:")
    for doc in documents[:3]:
        print(f"\n📄 {doc['title']}")
        print(f"   {doc['description']}")
        print(f"   🔗 {doc['url']}")
    
    print("\n✅ Prototype complete! Next: Run prototype_indexer.py to build vector index")


if __name__ == "__main__":
    asyncio.run(main())

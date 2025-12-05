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
from src.core.config import LOG_KEEP_RECENT

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

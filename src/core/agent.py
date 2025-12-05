"""
Agent Setup for MSI AI Assistant.

This module contains all the shared logic for creating the LangChain agent.
Both api_server.py and main.py use these functions to avoid code duplication.

Usage:
    from src.core.agent import initialize_agent_components

    agent, mcp_client = await initialize_agent_components(
        project_root=PROJECT_ROOT,
        logger=logger
    )
"""

from pathlib import Path
from typing import List, Optional, Any
import logging

from langchain_openai import OpenAIEmbeddings
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.tools import Tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from fastmcp.client.auth import OAuth

from src.core.config import (
    DEFAULT_MODEL,
    DEFAULT_MODEL_PROVIDER,
    RATE_LIMIT_REQUESTS_PER_SECOND,
    RATE_LIMIT_CHECK_INTERVAL,
    RATE_LIMIT_MAX_BUCKET_SIZE,
    TOOL_CALL_LIMIT,
    TOOL_CALL_EXIT_BEHAVIOR,
    SYSTEM_PROMPT,
    EMBEDDING_MODEL,
    MCP_TICKETING_URL,
    MCP_ORGANIZATIONS_URL,
    MCP_ISSUER_URL,
)
from src.rag.registry import create_default_rag_tools


def create_rate_limiter() -> InMemoryRateLimiter:
    """Create rate limiter for API cost protection"""
    return InMemoryRateLimiter(
        requests_per_second=RATE_LIMIT_REQUESTS_PER_SECOND,
        check_every_n_seconds=RATE_LIMIT_CHECK_INTERVAL,
        max_bucket_size=RATE_LIMIT_MAX_BUCKET_SIZE,
    )


def create_model(rate_limiter: InMemoryRateLimiter) -> Any:
    """Create LLM with rate limiting"""
    return init_chat_model(
        DEFAULT_MODEL,
        model_provider=DEFAULT_MODEL_PROVIDER,
        rate_limiter=rate_limiter
    )


def create_embeddings() -> OpenAIEmbeddings:
    """Create embeddings model"""
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


async def create_mcp_client() -> MultiServerMCPClient:
    """
    Create MCP client with shared OAuth authentication for all servers (SSO).

    The OAuth flow will trigger once when first server connects, and the resulting
    token is automatically shared across all MCP servers that use the same auth instance.

    Returns:
        MultiServerMCPClient configured with shared authentication
    """
    # Create shared OAuth - browser opens once, token shared for all servers
    shared_oauth = OAuth(mcp_url=MCP_ISSUER_URL)

    return MultiServerMCPClient(
        {
            "ticketing": {
                "url": MCP_TICKETING_URL,
                "transport": "streamable_http",
                "auth": shared_oauth  # Shared OAuth instance
            },
            "organizations": {
                "url": MCP_ORGANIZATIONS_URL,
                "transport": "streamable_http",
                "auth": shared_oauth  # Same OAuth instance = SSO
            }
            # Add new MCP servers here - they'll all use the same shared_oauth instance
        }
    )


async def get_mcp_tools(
    mcp_client: MultiServerMCPClient,
    logger: logging.Logger
) -> List[Tool]:
    """Get tools from MCP client with error handling"""
    try:
        mcp_tools = await mcp_client.get_tools()
        logger.info(f"Loaded {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")
        return mcp_tools
    except Exception as e:
        logger.warning(f"Could not load all MCP tools: {e}")
        return []


async def initialize_agent_components(
    project_root: Path,
    logger: logging.Logger,
    custom_rag_agents: Optional[List] = None
):
    """
    Initialize all components needed for the MSI Support Agent.

    This is the main entry point used by both api_server.py and main.py.

    Args:
        project_root: Path to project root directory
        logger: Logger instance
        custom_rag_agents: Optional list of custom RAG agent classes to register

    Returns:
        Tuple of (agent, mcp_client) - The initialized agent and MCP client

    Example:
        # Default usage (just MSI docs)
        agent, mcp_client = await initialize_agent_components(
            project_root=PROJECT_ROOT,
            logger=logger
        )

        # With custom RAG agents
        from rag_agents import CustomRAGAgent
        agent, mcp_client = await initialize_agent_components(
            project_root=PROJECT_ROOT,
            logger=logger,
            custom_rag_agents=[CustomRAGAgent]
        )
    """
    logger.info("Initializing MSI Support Agent...")

    # Step 1: Create rate limiter
    rate_limiter = create_rate_limiter()
    logger.info(f"Rate limiter configured: {RATE_LIMIT_REQUESTS_PER_SECOND} requests/second")

    # Step 2: Create LLM
    model = create_model(rate_limiter)
    logger.info(f"Model configured: {DEFAULT_MODEL} ({DEFAULT_MODEL_PROVIDER})")

    # Step 3: Create embeddings
    embeddings = create_embeddings()
    logger.info(f"Embeddings configured: {EMBEDDING_MODEL}")

    # Step 4: Create RAG tools
    if custom_rag_agents:
        # If custom agents provided, use registry
        from rag_agents import RAGAgentRegistry, MSIDocsRAGAgent
        registry = RAGAgentRegistry()

        # Always include default MSI docs agent
        registry.register(MSIDocsRAGAgent(project_root, embeddings))

        # Add custom agents
        for agent_class in custom_rag_agents:
            registry.register(agent_class(project_root, embeddings))

        rag_tools = await registry.get_all_tools()
    else:
        # Default: just MSI docs
        rag_tools = await create_default_rag_tools(project_root, embeddings)

    logger.info(f"Initialized {len(rag_tools)} RAG tool(s)")

    # Step 5: Create MCP client with shared OAuth (SSO)
    # OAuth flow will trigger automatically on first connection (browser opens once)
    # The same OAuth instance is reused for all servers = Single Sign-On
    logger.info("Creating MCP client with shared OAuth authentication...")
    mcp_client = await create_mcp_client()
    mcp_tools = await get_mcp_tools(mcp_client, logger)

    # Step 7: Combine all tools
    all_tools = mcp_tools + rag_tools
    logger.info(f"Total tools available: {len(all_tools)}")

    # Step 8: Create middleware
    tool_call_limit = ToolCallLimitMiddleware(
        run_limit=TOOL_CALL_LIMIT,
        exit_behavior=TOOL_CALL_EXIT_BEHAVIOR
    )
    logger.info(f"Tool call limit configured: {TOOL_CALL_LIMIT} calls per query")

    # Step 9: Create agent
    agent = create_agent(
        model,
        tools=all_tools,
        middleware=[tool_call_limit],
        system_prompt=SYSTEM_PROMPT
    )

    logger.info("Agent initialization complete!")

    return agent, mcp_client

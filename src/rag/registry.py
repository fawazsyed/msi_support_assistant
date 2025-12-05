"""
RAG Agent Registry for MSI AI Assistant.

Manages multiple RAG agents and provides a centralized way to register,
initialize, and access all RAG tools.

Usage:
    from src.rag.registry import RAGAgentRegistry
    from src.rag.agents.msi_docs import MSIDocsRAGAgent

    registry = RAGAgentRegistry()
    registry.register(MSIDocsRAGAgent(project_root, embeddings))
    tools = await registry.get_all_tools()
"""

from pathlib import Path
from typing import List, Optional
from langchain_core.tools import Tool
from langchain_openai import OpenAIEmbeddings
import logging

from src.rag.base import BaseRAGAgent


class RAGAgentRegistry:
    """
    Registry for managing multiple RAG agents.

    Usage:
        registry = RAGAgentRegistry()
        registry.register(MSIDocsRAGAgent(project_root, embeddings))
        registry.register(CustomRAGAgent(project_root, embeddings))

        tools = await registry.get_all_tools()
        # tools now contains all RAG tools
    """

    def __init__(self):
        self._agents: List[BaseRAGAgent] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def register(self, agent: BaseRAGAgent) -> None:
        """Register a new RAG agent"""
        self._agents.append(agent)
        self.logger.info(f"Registered RAG agent: {agent.name}")

    async def get_all_tools(self) -> List[Tool]:
        """Initialize all agents and return their tools"""
        tools = []
        for agent in self._agents:
            await agent.initialize()
            tool = agent.create_tool()
            tools.append(tool)
        return tools

    def get_agent(self, name: str) -> Optional[BaseRAGAgent]:
        """Get a specific agent by name"""
        for agent in self._agents:
            if agent.name == name:
                return agent
        return None


async def create_default_rag_tools(
    project_root: Path,
    embeddings: OpenAIEmbeddings
) -> List[Tool]:
    """
    Create default RAG tools (just MSI docs for now).

    To add custom agents, use RAGAgentRegistry instead:
        registry = RAGAgentRegistry()
        registry.register(MSIDocsRAGAgent(project_root, embeddings))
        registry.register(YourCustomAgent(project_root, embeddings))
        tools = await registry.get_all_tools()
    """
    from src.rag.agents.msi_docs import MSIDocsRAGAgent

    registry = RAGAgentRegistry()
    registry.register(MSIDocsRAGAgent(project_root, embeddings))
    return await registry.get_all_tools()

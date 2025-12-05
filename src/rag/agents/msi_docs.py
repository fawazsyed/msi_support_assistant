"""
MSI Documentation RAG Agent.

Searches Motorola Solutions product documentation (Video Manager Admin Guide).

Usage:
    from src.rag.agents.msi_docs import MSIDocsRAGAgent

    agent = MSIDocsRAGAgent(project_root, embeddings)
    await agent.initialize()
    tool = agent.create_tool()
"""

from pathlib import Path
from langchain_core.tools import tool, Tool

from src.rag.base import BaseRAGAgent


class MSIDocsRAGAgent(BaseRAGAgent):
    """
    RAG agent for MSI product documentation.

    This is the default agent that searches the Video Manager Admin Guide.
    """

    @property
    def name(self) -> str:
        return "msi_docs"

    @property
    def description(self) -> str:
        return "Search Motorola Solutions product documentation"

    @property
    def document_path(self) -> Path:
        return self.project_root / "data" / "documents" / "video_manager_admin_guide.txt"

    def create_tool(self) -> Tool:
        """Create the search_msi_documentation tool"""

        @tool
        def search_msi_documentation(query: str) -> str:
            """Search Motorola Solutions product documentation for information.

            Use this tool when the user asks questions about:
            - How to use MSI products (Video Manager, etc.)
            - Product features and capabilities
            - Configuration and setup instructions
            - Troubleshooting and support
            - User management and administration

            Args:
                query: The search query to find relevant documentation

            Returns:
                Relevant documentation excerpts that answer the query
            """
            return self.search(query)

        return search_msi_documentation

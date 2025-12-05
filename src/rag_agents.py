"""
RAG Agent System for MSI AI Assistant.

This module provides a framework for creating and managing custom RAG agents.
Each agent can have its own document source, vector store, and search logic.

Usage:
    # Create a custom RAG agent
    agent = MSIDocsRAGAgent(project_root, embeddings)
    await agent.initialize()
    tool = agent.create_tool()

    # Or use the registry for multiple agents
    registry = RAGAgentRegistry()
    registry.register(MSIDocsRAGAgent(project_root, embeddings))
    registry.register(CustomRAGAgent(...))  # Add your own!
    tools = await registry.get_all_tools()
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from langchain_core.tools import tool, Tool
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import logging

from config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHUNK_SEPARATORS,
    VECTOR_STORE_COLLECTION_NAME,
    CHROMA_PERSIST_DIR
)


class BaseRAGAgent(ABC):
    """
    Base class for custom RAG agents.

    Subclass this to create your own RAG agent with custom document sources.
    """

    def __init__(self, project_root: Path, embeddings: OpenAIEmbeddings):
        self.project_root = project_root
        self.embeddings = embeddings
        self.vector_store: Optional[Chroma] = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this RAG agent (e.g., 'msi_docs')"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this agent can help with (for LLM)"""
        pass

    @property
    @abstractmethod
    def document_path(self) -> Path:
        """Path to the document(s) this agent indexes"""
        pass

    @property
    def collection_name(self) -> str:
        """Vector store collection name (default: name + '_collection')"""
        return f"{self.name}_collection"

    @property
    def persist_directory(self) -> str:
        """Where to persist the vector store"""
        return str(self.project_root / f"{CHROMA_PERSIST_DIR}_{self.name}")

    async def initialize(self) -> None:
        """
        Initialize the vector store and index documents if needed.
        Override this method if you need custom initialization logic.
        """
        self.logger.info(f"Initializing RAG agent: {self.name}")

        # Load document content
        doc_content = self._load_documents()

        # Create vector store
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

        # Index documents if collection is empty
        if self.vector_store._collection.count() == 0:
            self.logger.info(f"Indexing documents for {self.name}...")
            chunks = self._split_documents(doc_content)
            self.vector_store.add_texts(texts=chunks)
            self.logger.info(f"Indexed {len(chunks)} chunks for {self.name}")
        else:
            self.logger.info(f"Using existing vector store for {self.name}")

    def _load_documents(self) -> str:
        """Load document content from file. Override for custom loading logic."""
        try:
            with open(self.document_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            self.logger.error(f"Document not found: {self.document_path}")
            raise
        except Exception:
            self.logger.exception(f"Failed to load document from {self.document_path}")
            raise

    def _split_documents(self, content: str) -> List[str]:
        """Split documents into chunks. Override for custom splitting logic."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=CHUNK_SEPARATORS,
        )
        return text_splitter.split_text(content)

    def search(self, query: str, k: int = 2) -> str:
        """
        Search the vector store for relevant documents.
        Override this method for custom search logic.
        """
        if not self.vector_store:
            raise RuntimeError(f"RAG agent {self.name} not initialized. Call initialize() first.")

        retrieved_docs = self.vector_store.similarity_search(query, k=k)

        if not retrieved_docs:
            return "No relevant documentation found for this query."

        docs_content = "\n\n---\n\n".join(
            f"Document excerpt {i+1}:\n{doc.page_content}"
            for i, doc in enumerate(retrieved_docs)
        )

        return docs_content

    @abstractmethod
    def create_tool(self) -> Tool:
        """
        Create a LangChain tool for this RAG agent.
        This method must be implemented by subclasses.
        """
        pass


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
        return self.project_root / "documents" / "video_manager_admin_guide.txt"

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


# =============================================================================
# Example: Custom RAG Agent Template
# =============================================================================

class CustomRAGAgent(BaseRAGAgent):
    """
    Template for creating custom RAG agents.

    To create your own agent:
    1. Copy this class and rename it
    2. Update name, description, and document_path
    3. Customize the tool docstring in create_tool()
    4. Optionally override initialize(), search(), _load_documents(), or _split_documents()

    Example:
        class KnowledgeBaseRAGAgent(BaseRAGAgent):
            @property
            def name(self) -> str:
                return "kb_search"

            @property
            def description(self) -> str:
                return "Search company knowledge base"

            @property
            def document_path(self) -> Path:
                return self.project_root / "documents" / "knowledge_base.txt"

            def create_tool(self) -> Tool:
                @tool
                def search_knowledge_base(query: str) -> str:
                    '''Search the company knowledge base.'''
                    return self.search(query)
                return search_knowledge_base
    """

    @property
    def name(self) -> str:
        return "custom"  # Change this!

    @property
    def description(self) -> str:
        return "Custom RAG agent description"  # Change this!

    @property
    def document_path(self) -> Path:
        return self.project_root / "documents" / "custom_doc.txt"  # Change this!

    def create_tool(self) -> Tool:
        """Customize the tool name and docstring"""

        @tool
        def search_custom_docs(query: str) -> str:
            """Search custom documentation.

            Customize this docstring to help the LLM understand when to use this tool.

            Args:
                query: The search query

            Returns:
                Relevant documentation excerpts
            """
            return self.search(query)

        return search_custom_docs


# =============================================================================
# RAG Agent Registry
# =============================================================================

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


# =============================================================================
# Convenience Function
# =============================================================================

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
    registry = RAGAgentRegistry()
    registry.register(MSIDocsRAGAgent(project_root, embeddings))
    return await registry.get_all_tools()
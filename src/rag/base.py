"""
Base RAG Agent Class for MSI AI Assistant.

Provides the foundation for creating custom RAG agents with their own
document sources, vector stores, and search logic.

Usage:
    from src.rag.base import BaseRAGAgent

    class MyRAGAgent(BaseRAGAgent):
        @property
        def name(self) -> str:
            return "my_agent"

        # ... implement other abstract properties and methods
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from langchain_core.tools import Tool
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import logging

from src.core.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHUNK_SEPARATORS,
    VECTOR_STORE_COLLECTION_NAME,
    CHROMA_PERSIST_DIR
)
from src.observability.pii_scrubber import scrub_all_pii


class BaseRAGAgent(ABC):
    """
    Base class for custom RAG agents.

    Subclass this to create your own RAG agent with custom document sources.
    """

    def __init__(
        self,
        project_root: Path,
        embeddings: OpenAIEmbeddings,
        scrub_pii: bool = True,
        scrub_emails: bool = True,
        scrub_phones: bool = True,
        scrub_ssns: bool = True,
        scrub_credit_cards: bool = True,
        scrub_ips: bool = False,
        scrub_urls: bool = False
    ):
        self.project_root = project_root
        self.embeddings = embeddings
        self.vector_store: Optional[Chroma] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # PII scrubbing configuration
        self.scrub_pii = scrub_pii
        self.scrub_emails = scrub_emails
        self.scrub_phones = scrub_phones
        self.scrub_ssns = scrub_ssns
        self.scrub_credit_cards = scrub_credit_cards
        self.scrub_ips = scrub_ips
        self.scrub_urls = scrub_urls

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

        # Scrub PII from retrieved documents if enabled
        if self.scrub_pii:
            self.logger.debug(f"Scrubbing PII from {len(retrieved_docs)} retrieved documents")
            docs_content = scrub_all_pii(
                docs_content,
                scrub_emails=self.scrub_emails,
                scrub_phones=self.scrub_phones,
                scrub_ssns=self.scrub_ssns,
                scrub_credit_cards=self.scrub_credit_cards,
                scrub_ips=self.scrub_ips,
                scrub_urls=self.scrub_urls
            )

        return docs_content

    @abstractmethod
    def create_tool(self) -> Tool:
        """
        Create a LangChain tool for this RAG agent.
        This method must be implemented by subclasses.
        """
        pass

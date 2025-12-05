"""
Unit tests for RAG base agent functionality.

Tests document loading, chunking, vector store initialization, and search.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch, MagicMock
from langchain_core.tools import Tool
from langchain_chroma import Chroma

from src.rag.base import BaseRAGAgent


class MockRAGAgent(BaseRAGAgent):
    """Mock implementation of BaseRAGAgent for testing"""

    def __init__(self, project_root: Path, embeddings, doc_path: Path):
        super().__init__(project_root, embeddings)
        self._doc_path = doc_path

    @property
    def name(self) -> str:
        return "test_agent"

    @property
    def description(self) -> str:
        return "Test RAG agent for unit testing"

    @property
    def document_path(self) -> Path:
        return self._doc_path

    def create_tool(self) -> Tool:
        """Create a mock tool for testing"""
        def mock_search(query: str) -> str:
            return self.search(query)

        return Tool(
            name=f"search_{self.name}",
            description=self.description,
            func=mock_search
        )


class TestBaseRAGAgent:
    """Test suite for BaseRAGAgent"""

    @pytest.fixture
    def mock_embeddings(self):
        """Create mock embeddings"""
        embeddings = Mock()
        embeddings.embed_documents = Mock(return_value=[[0.1] * 768])
        embeddings.embed_query = Mock(return_value=[0.1] * 768)
        return embeddings

    @pytest.fixture
    def temp_doc_file(self):
        """Create temporary document file"""
        with TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "test_doc.txt"
            doc_path.write_text("This is a test document.\nIt has multiple lines.\nFor testing RAG functionality.")
            yield doc_path

    @pytest.fixture
    def mock_agent(self, mock_embeddings, temp_doc_file):
        """Create mock RAG agent instance"""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            agent = MockRAGAgent(project_root, mock_embeddings, temp_doc_file)
            yield agent

    def test_initialization(self, mock_agent):
        """Test agent initializes with correct properties"""
        assert mock_agent.name == "test_agent"
        assert mock_agent.description == "Test RAG agent for unit testing"
        assert mock_agent.vector_store is None  # Not initialized yet

    def test_collection_name_default(self, mock_agent):
        """Test default collection name generation"""
        assert mock_agent.collection_name == "test_agent_collection"

    def test_persist_directory_generation(self, mock_agent):
        """Test persist directory path generation"""
        persist_dir = mock_agent.persist_directory
        assert "chroma_langchain_db_test_agent" in persist_dir

    def test_load_documents_success(self, mock_agent):
        """Test successful document loading"""
        content = mock_agent._load_documents()
        
        assert isinstance(content, str)
        assert "test document" in content
        assert len(content) > 0

    def test_load_documents_file_not_found(self, mock_embeddings):
        """Test document loading with missing file"""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            nonexistent_path = Path(tmpdir) / "missing.txt"
            agent = MockRAGAgent(project_root, mock_embeddings, nonexistent_path)
            
            with pytest.raises(FileNotFoundError):
                agent._load_documents()

    def test_split_documents(self, mock_agent):
        """Test document splitting into chunks"""
        content = "This is a test document. " * 100  # Create long content
        chunks = mock_agent._split_documents(content)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_split_documents_empty_content(self, mock_agent):
        """Test splitting empty content"""
        chunks = mock_agent._split_documents("")
        
        assert isinstance(chunks, list)
        assert len(chunks) == 0

    def test_split_documents_small_content(self, mock_agent):
        """Test splitting content smaller than chunk size"""
        content = "Small content"
        chunks = mock_agent._split_documents(content)
        
        assert len(chunks) == 1
        assert chunks[0] == content

    @patch('src.rag.base.Chroma')
    async def test_initialize_new_vector_store(self, mock_chroma_class, mock_agent):
        """Test initialization with empty vector store"""
        # Setup mock
        mock_vector_store = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0  # Empty collection
        mock_vector_store._collection = mock_collection
        mock_vector_store.add_texts = Mock()
        mock_chroma_class.return_value = mock_vector_store
        
        await mock_agent.initialize()
        
        # Verify vector store was created
        assert mock_agent.vector_store is not None
        mock_chroma_class.assert_called_once()
        
        # Verify documents were indexed
        mock_vector_store.add_texts.assert_called_once()
        call_args = mock_vector_store.add_texts.call_args
        texts = call_args.kwargs['texts']
        assert len(texts) > 0

    @patch('src.rag.base.Chroma')
    async def test_initialize_existing_vector_store(self, mock_chroma_class, mock_agent):
        """Test initialization with existing vector store"""
        # Setup mock for existing collection
        mock_vector_store = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10  # Has documents
        mock_vector_store._collection = mock_collection
        mock_vector_store.add_texts = Mock()
        mock_chroma_class.return_value = mock_vector_store
        
        await mock_agent.initialize()
        
        # Verify vector store was created but NOT indexed
        assert mock_agent.vector_store is not None
        mock_vector_store.add_texts.assert_not_called()

    def test_search_without_initialization(self, mock_agent):
        """Test search before initialization raises error"""
        with pytest.raises(RuntimeError, match="not initialized"):
            mock_agent.search("test query")

    @patch('src.rag.base.Chroma')
    async def test_search_with_results(self, mock_chroma_class, mock_agent):
        """Test search returns formatted results"""
        # Setup mock vector store with results
        mock_doc1 = Mock()
        mock_doc1.page_content = "First document content"
        mock_doc2 = Mock()
        mock_doc2.page_content = "Second document content"
        
        mock_vector_store = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_vector_store._collection = mock_collection
        mock_vector_store.similarity_search = Mock(return_value=[mock_doc1, mock_doc2])
        mock_chroma_class.return_value = mock_vector_store
        
        await mock_agent.initialize()
        result = mock_agent.search("test query", k=2)
        
        assert "First document content" in result
        assert "Second document content" in result
        assert "Document excerpt 1" in result
        assert "Document excerpt 2" in result
        assert "---" in result  # Separator

    @patch('src.rag.base.Chroma')
    async def test_search_no_results(self, mock_chroma_class, mock_agent):
        """Test search with no results returns appropriate message"""
        # Setup mock vector store with no results
        mock_vector_store = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_vector_store._collection = mock_collection
        mock_vector_store.similarity_search = Mock(return_value=[])
        mock_chroma_class.return_value = mock_vector_store
        
        await mock_agent.initialize()
        result = mock_agent.search("nonexistent query")
        
        assert "No relevant documentation found" in result

    @patch('src.rag.base.Chroma')
    async def test_create_tool(self, mock_chroma_class, mock_agent):
        """Test tool creation"""
        # Setup mock
        mock_vector_store = MagicMock()
        mock_collection = MagicMock()
        mock_collection.count.return_value = 5
        mock_vector_store._collection = mock_collection
        mock_chroma_class.return_value = mock_vector_store
        
        await mock_agent.initialize()
        tool = mock_agent.create_tool()
        
        assert isinstance(tool, Tool)
        assert "search_" in tool.name
        assert tool.description == "Test RAG agent for unit testing"

    def test_abstract_methods_required(self, mock_embeddings):
        """Test that abstract methods must be implemented"""
        with TemporaryDirectory() as tmpdir:
            # Cannot instantiate BaseRAGAgent directly
            with pytest.raises(TypeError):
                BaseRAGAgent(Path(tmpdir), mock_embeddings)

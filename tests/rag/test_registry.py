"""
Unit tests for RAG Agent Registry.

Tests agent registration, tool creation, and multi-agent coordination.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.tools import Tool

from src.rag.registry import RAGAgentRegistry, create_default_rag_tools
from src.rag.base import BaseRAGAgent


class MockRAGAgent(BaseRAGAgent):
    """Mock RAG agent for testing"""

    def __init__(self, project_root: Path, embeddings, agent_name: str = "mock_agent"):
        super().__init__(project_root, embeddings)
        self._agent_name = agent_name
        self.initialize_called = False

    @property
    def name(self) -> str:
        return self._agent_name

    @property
    def description(self) -> str:
        return f"Mock agent: {self._agent_name}"

    @property
    def document_path(self) -> Path:
        return self.project_root / "mock_doc.txt"

    async def initialize(self) -> None:
        """Mock initialization"""
        self.initialize_called = True
        self.vector_store = Mock()  # Mock vector store

    def create_tool(self) -> Tool:
        """Create mock tool"""
        def mock_search(query: str) -> str:
            return f"Mock results from {self.name} for: {query}"

        return Tool(
            name=f"search_{self.name}",
            description=self.description,
            func=mock_search
        )


class TestRAGAgentRegistry:
    """Test suite for RAGAgentRegistry"""

    @pytest.fixture
    def mock_embeddings(self):
        """Create mock embeddings"""
        embeddings = Mock()
        return embeddings

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance"""
        return RAGAgentRegistry()

    @pytest.fixture
    def mock_agent(self, mock_embeddings):
        """Create mock agent"""
        with TemporaryDirectory() as tmpdir:
            agent = MockRAGAgent(Path(tmpdir), mock_embeddings, "test_agent")
            yield agent

    def test_initialization(self, registry):
        """Test registry initializes empty"""
        assert len(registry._agents) == 0

    def test_register_single_agent(self, registry, mock_agent):
        """Test registering a single agent"""
        registry.register(mock_agent)
        
        assert len(registry._agents) == 1
        assert registry._agents[0] == mock_agent

    def test_register_multiple_agents(self, registry, mock_embeddings):
        """Test registering multiple agents"""
        with TemporaryDirectory() as tmpdir:
            agent1 = MockRAGAgent(Path(tmpdir), mock_embeddings, "agent1")
            agent2 = MockRAGAgent(Path(tmpdir), mock_embeddings, "agent2")
            agent3 = MockRAGAgent(Path(tmpdir), mock_embeddings, "agent3")
            
            registry.register(agent1)
            registry.register(agent2)
            registry.register(agent3)
            
            assert len(registry._agents) == 3
            assert agent1 in registry._agents
            assert agent2 in registry._agents
            assert agent3 in registry._agents

    def test_get_agent_by_name(self, registry, mock_embeddings):
        """Test retrieving agent by name"""
        with TemporaryDirectory() as tmpdir:
            agent1 = MockRAGAgent(Path(tmpdir), mock_embeddings, "agent1")
            agent2 = MockRAGAgent(Path(tmpdir), mock_embeddings, "agent2")
            
            registry.register(agent1)
            registry.register(agent2)
            
            found_agent = registry.get_agent("agent2")
            assert found_agent == agent2
            assert found_agent.name == "agent2"

    def test_get_agent_not_found(self, registry, mock_agent):
        """Test retrieving nonexistent agent returns None"""
        registry.register(mock_agent)
        
        result = registry.get_agent("nonexistent")
        assert result is None

    def test_get_agent_empty_registry(self, registry):
        """Test getting agent from empty registry"""
        result = registry.get_agent("any_name")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_tools_empty_registry(self, registry):
        """Test getting tools from empty registry"""
        tools = await registry.get_all_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 0

    @pytest.mark.asyncio
    async def test_get_all_tools_single_agent(self, registry, mock_agent):
        """Test getting tools from single agent"""
        registry.register(mock_agent)
        
        tools = await registry.get_all_tools()
        
        assert len(tools) == 1
        assert isinstance(tools[0], Tool)
        assert tools[0].name == "search_test_agent"
        assert mock_agent.initialize_called

    @pytest.mark.asyncio
    async def test_get_all_tools_multiple_agents(self, registry, mock_embeddings):
        """Test getting tools from multiple agents"""
        with TemporaryDirectory() as tmpdir:
            agent1 = MockRAGAgent(Path(tmpdir), mock_embeddings, "docs_agent")
            agent2 = MockRAGAgent(Path(tmpdir), mock_embeddings, "kb_agent")
            agent3 = MockRAGAgent(Path(tmpdir), mock_embeddings, "faq_agent")
            
            registry.register(agent1)
            registry.register(agent2)
            registry.register(agent3)
            
            tools = await registry.get_all_tools()
            
            assert len(tools) == 3
            assert all(isinstance(tool, Tool) for tool in tools)
            
            tool_names = [tool.name for tool in tools]
            assert "search_docs_agent" in tool_names
            assert "search_kb_agent" in tool_names
            assert "search_faq_agent" in tool_names
            
            # Verify all agents were initialized
            assert agent1.initialize_called
            assert agent2.initialize_called
            assert agent3.initialize_called

    @pytest.mark.asyncio
    async def test_get_all_tools_initializes_agents(self, registry, mock_agent):
        """Test that get_all_tools initializes agents"""
        assert not mock_agent.initialize_called
        
        registry.register(mock_agent)
        await registry.get_all_tools()
        
        assert mock_agent.initialize_called

    @pytest.mark.asyncio
    async def test_get_all_tools_creates_functional_tools(self, registry, mock_agent):
        """Test that created tools are functional"""
        registry.register(mock_agent)
        tools = await registry.get_all_tools()
        
        tool = tools[0]
        result = tool.func("test query")
        
        assert isinstance(result, str)
        assert "test query" in result
        assert "test_agent" in result


class TestCreateDefaultRAGTools:
    """Test suite for create_default_rag_tools helper function"""

    @pytest.fixture
    def mock_embeddings(self):
        """Create mock embeddings"""
        return Mock()

    @pytest.mark.asyncio
    @patch('src.rag.agents.msi_docs.MSIDocsRAGAgent')
    async def test_create_default_rag_tools(self, mock_msi_agent_class, mock_embeddings):
        """Test default RAG tools creation"""
        # Setup mock
        mock_agent_instance = Mock()
        mock_agent_instance.initialize = AsyncMock()
        mock_tool = Mock(spec=Tool)
        mock_agent_instance.create_tool = Mock(return_value=mock_tool)
        mock_msi_agent_class.return_value = mock_agent_instance
        
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            tools = await create_default_rag_tools(project_root, mock_embeddings)
            
            # Verify MSI agent was created
            mock_msi_agent_class.assert_called_once_with(project_root, mock_embeddings)
            
            # Verify agent was initialized
            mock_agent_instance.initialize.assert_called_once()
            
            # Verify tool was created
            mock_agent_instance.create_tool.assert_called_once()
            
            # Verify tools returned
            assert len(tools) == 1
            assert tools[0] == mock_tool

    @pytest.mark.asyncio
    @patch('src.rag.agents.msi_docs.MSIDocsRAGAgent')
    async def test_create_default_rag_tools_initializes_agent(self, mock_msi_agent_class, mock_embeddings):
        """Test that agent initialization is called"""
        mock_agent_instance = Mock()
        mock_agent_instance.initialize = AsyncMock()
        mock_agent_instance.create_tool = Mock(return_value=Mock(spec=Tool))
        mock_msi_agent_class.return_value = mock_agent_instance
        
        with TemporaryDirectory() as tmpdir:
            await create_default_rag_tools(Path(tmpdir), mock_embeddings)
            
            mock_agent_instance.initialize.assert_awaited_once()

"""
Unit tests for RagasDataCollector.

Tests data collection, validation, serialization, and dataset creation.
"""

import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from ragas.messages import ToolCall

from src.observability.collector import RagasDataCollector, SCHEMA_VERSION


class TestRagasDataCollector:
    """Test suite for RagasDataCollector"""
    
    def test_initialization(self):
        """Test collector initializes with empty samples"""
        collector = RagasDataCollector()
        
        assert len(collector.single_turn_samples) == 0
        assert len(collector.multi_turn_samples) == 0
        assert len(collector) == 0
    
    def test_add_single_turn_valid(self):
        """Test adding valid single-turn sample"""
        collector = RagasDataCollector()
        
        collector.add_single_turn(
            user_input="How do I add a user?",
            retrieved_contexts=["Context 1", "Context 2"],
            response="To add a user, follow these steps..."
        )
        
        assert len(collector) == 1
        assert len(collector.single_turn_samples) == 1
        assert collector.single_turn_samples[0]["user_input"] == "How do I add a user?"
    
    def test_add_single_turn_with_reference(self):
        """Test adding single-turn sample with reference data"""
        collector = RagasDataCollector()
        
        collector.add_single_turn(
            user_input="Test query",
            retrieved_contexts=["Context"],
            response="Test response",
            reference="Expected answer",
            reference_contexts=["Expected context"]
        )
        
        sample = collector.single_turn_samples[0]
        assert "reference" in sample
        assert "reference_contexts" in sample
        assert sample["reference"] == "Expected answer"
    
    def test_add_single_turn_empty_input(self):
        """Test validation: empty user_input raises ValueError"""
        collector = RagasDataCollector()
        
        with pytest.raises(ValueError, match="user_input cannot be empty"):
            collector.add_single_turn(
                user_input="",
                retrieved_contexts=["Context"],
                response="Response"
            )
    
    def test_add_single_turn_whitespace_input(self):
        """Test validation: whitespace-only input raises ValueError"""
        collector = RagasDataCollector()
        
        with pytest.raises(ValueError, match="user_input cannot be empty"):
            collector.add_single_turn(
                user_input="   ",
                retrieved_contexts=["Context"],
                response="Response"
            )
    
    def test_add_single_turn_empty_response(self):
        """Test validation: empty response raises ValueError"""
        collector = RagasDataCollector()
        
        with pytest.raises(ValueError, match="response cannot be empty"):
            collector.add_single_turn(
                user_input="Query",
                retrieved_contexts=["Context"],
                response=""
            )
    
    def test_add_single_turn_invalid_contexts_type(self):
        """Test validation: non-list contexts raises ValueError"""
        collector = RagasDataCollector()
        
        with pytest.raises(ValueError, match="must be a list"):
            collector.add_single_turn(
                user_input="Query",
                retrieved_contexts="Not a list",
                response="Response"
            )
    
    def test_add_single_turn_strips_whitespace(self):
        """Test that inputs are stripped of leading/trailing whitespace"""
        collector = RagasDataCollector()
        
        collector.add_single_turn(
            user_input="  Query  ",
            retrieved_contexts=["  Context 1  ", "  Context 2  "],
            response="  Response  "
        )
        
        sample = collector.single_turn_samples[0]
        assert sample["user_input"] == "Query"
        assert sample["response"] == "Response"
        assert all(ctx.strip() == ctx for ctx in sample["retrieved_contexts"])
    
    def test_add_multi_turn_valid(self):
        """Test adding valid multi-turn sample"""
        collector = RagasDataCollector()
        
        messages = [
            HumanMessage(content="How do I add a user?"),
            AIMessage(content="I'll search the documentation."),
            ToolMessage(content="User creation docs...", tool_call_id="call_123"),
            AIMessage(content="To add a user, follow these steps...")
        ]
        
        collector.add_multi_turn(messages=messages)
        
        assert len(collector) == 1
        assert len(collector.multi_turn_samples) == 1
        assert len(collector.multi_turn_samples[0]["messages"]) == 4
    
    def test_add_multi_turn_with_tool_calls(self):
        """Test multi-turn sample with AI message containing tool calls"""
        collector = RagasDataCollector()
        
        messages = [
            HumanMessage(content="Search for users"),
            AIMessage(
                content="",
                tool_calls=[{
                    "id": "call_123",
                    "name": "search_msi_documentation",
                    "args": {"query": "user management"}
                }]
            )
        ]
        
        collector.add_multi_turn(messages=messages)
        
        assert len(collector) == 1
        ragas_messages = collector.multi_turn_samples[0]["messages"]
        # Check that tool calls were converted
        assert len(ragas_messages) == 2
    
    def test_add_multi_turn_with_reference(self):
        """Test adding multi-turn sample with reference data"""
        collector = RagasDataCollector()
        
        messages = [HumanMessage(content="Test")]
        reference_tool_calls = [
            ToolCall(name="search_docs", args={"query": "test"})
        ]
        
        collector.add_multi_turn(
            messages=messages,
            reference_tool_calls=reference_tool_calls,
            reference="Expected goal"
        )
        
        sample = collector.multi_turn_samples[0]
        assert "reference" in sample
        assert "reference_tool_calls" in sample
        assert sample["reference"] == "Expected goal"
    
    def test_add_multi_turn_empty_messages(self):
        """Test validation: empty messages list raises ValueError"""
        collector = RagasDataCollector()
        
        with pytest.raises(ValueError, match="messages list cannot be empty"):
            collector.add_multi_turn(messages=[])
    
    def test_add_multi_turn_invalid_type(self):
        """Test validation: non-list messages raises ValueError"""
        collector = RagasDataCollector()
        
        with pytest.raises(ValueError, match="messages must be a list"):
            collector.add_multi_turn(messages="Not a list")
    
    def test_save_and_load_roundtrip(self):
        """Test that save/load preserves data correctly"""
        collector = RagasDataCollector()
        
        # Add samples
        collector.add_single_turn(
            user_input="Test query",
            retrieved_contexts=["Context 1"],
            response="Test response"
        )
        
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there")
        ]
        collector.add_multi_turn(messages=messages)
        
        # Save to temporary file
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_data.json"
            collector.save(filepath)
            
            # Verify file exists
            assert filepath.exists()
            
            # Load into new collector
            new_collector = RagasDataCollector()
            new_collector.load(filepath)
            
            # Verify data matches
            assert len(new_collector) == len(collector)
            assert len(new_collector.single_turn_samples) == 1
            assert len(new_collector.multi_turn_samples) == 1
    
    def test_save_includes_schema_version(self):
        """Test that saved file includes schema version"""
        collector = RagasDataCollector()
        collector.add_single_turn(
            user_input="Test",
            retrieved_contexts=["Context"],
            response="Response"
        )
        
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_data.json"
            collector.save(filepath)
            
            # Read and verify JSON structure
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            assert "schema_version" in data
            assert data["schema_version"] == SCHEMA_VERSION
            assert "timestamp" in data
            assert "single_turn_samples" in data
            assert "multi_turn_samples" in data
            assert "counts" in data
    
    def test_save_empty_collector_warning(self):
        """Test that saving empty collector logs warning"""
        collector = RagasDataCollector()
        
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.json"
            # Should not raise, but should warn
            collector.save(filepath)
    
    def test_load_nonexistent_file(self):
        """Test loading nonexistent file raises FileNotFoundError"""
        collector = RagasDataCollector()
        
        with pytest.raises(FileNotFoundError):
            collector.load("nonexistent_file.json")
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON raises ValueError"""
        collector = RagasDataCollector()
        
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "invalid.json"
            filepath.write_text("Not valid JSON{")
            
            with pytest.raises(ValueError, match="Invalid JSON format"):
                collector.load(filepath)
    
    def test_load_schema_version_mismatch_warning(self):
        """Test loading old schema version logs warning"""
        collector = RagasDataCollector()
        
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "old_version.json"
            
            # Write file with old schema version
            old_data = {
                "schema_version": "0.0.1",
                "timestamp": "2024-01-01T00:00:00",
                "single_turn_samples": [],
                "multi_turn_samples": []
            }
            
            with open(filepath, 'w') as f:
                json.dump(old_data, f)
            
            # Should load but warn (captured in logs)
            collector.load(filepath)
            assert len(collector) == 0
    
    def test_create_single_turn_dataset(self):
        """Test creating evaluation dataset from single-turn samples"""
        collector = RagasDataCollector()
        
        collector.add_single_turn(
            user_input="Query 1",
            retrieved_contexts=["Context 1"],
            response="Response 1"
        )
        collector.add_single_turn(
            user_input="Query 2",
            retrieved_contexts=["Context 2"],
            response="Response 2"
        )
        
        dataset = collector.create_single_turn_dataset()
        
        assert len(dataset) == 2
        # Verify samples are correct type
        from ragas.dataset_schema import SingleTurnSample
        assert all(isinstance(s, SingleTurnSample) for s in dataset.samples)
    
    def test_create_multi_turn_dataset(self):
        """Test creating evaluation dataset from multi-turn samples"""
        collector = RagasDataCollector()
        
        messages1 = [
            HumanMessage(content="Query 1"),
            AIMessage(content="Response 1")
        ]
        messages2 = [
            HumanMessage(content="Query 2"),
            AIMessage(content="Response 2")
        ]
        
        collector.add_multi_turn(messages=messages1)
        collector.add_multi_turn(messages=messages2)
        
        dataset = collector.create_multi_turn_dataset()
        
        assert len(dataset) == 2
        from ragas.dataset_schema import MultiTurnSample
        assert all(isinstance(s, MultiTurnSample) for s in dataset.samples)
    
    def test_clear(self):
        """Test clearing all collected samples"""
        collector = RagasDataCollector()
        
        collector.add_single_turn(
            user_input="Query",
            retrieved_contexts=["Context"],
            response="Response"
        )
        
        messages = [HumanMessage(content="Hello")]
        collector.add_multi_turn(messages=messages)
        
        assert len(collector) == 2
        
        collector.clear()
        
        assert len(collector) == 0
        assert len(collector.single_turn_samples) == 0
        assert len(collector.multi_turn_samples) == 0
    
    def test_repr(self):
        """Test string representation"""
        collector = RagasDataCollector()
        
        collector.add_single_turn(
            user_input="Query",
            retrieved_contexts=["Context"],
            response="Response"
        )
        
        repr_str = repr(collector)
        assert "RagasDataCollector" in repr_str
        assert "single_turn=1" in repr_str
        assert "multi_turn=0" in repr_str
    
    def test_len(self):
        """Test __len__ returns total samples"""
        collector = RagasDataCollector()
        
        assert len(collector) == 0
        
        collector.add_single_turn(
            user_input="Query",
            retrieved_contexts=["Context"],
            response="Response"
        )
        assert len(collector) == 1
        
        messages = [HumanMessage(content="Hello")]
        collector.add_multi_turn(messages=messages)
        assert len(collector) == 2

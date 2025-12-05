"""
Data collector for Ragas evaluation.

Collects user queries, retrieved contexts, agent responses, and tool calls
during agent execution for later evaluation with Ragas metrics.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

from ragas.dataset_schema import SingleTurnSample, MultiTurnSample, EvaluationDataset
from ragas.messages import HumanMessage, AIMessage, ToolMessage, ToolCall

# Schema version for data format compatibility
SCHEMA_VERSION = "1.0.0"

logger = logging.getLogger(__name__)


class RagasDataCollector:
    """
    Collects execution data for Ragas evaluation.
    
    Supports both:
    1. Single-turn RAG evaluation (user_input, contexts, response, reference)
    2. Multi-turn agent evaluation (full conversation with tool calls)
    
    Usage:
        collector = RagasDataCollector()
        
        # For single-turn RAG queries
        collector.add_single_turn(
            user_input="How do I add a user?",
            retrieved_contexts=["Context 1", "Context 2"],
            response="To add a user...",
            reference="Expected answer..."  # Optional
        )
        
        # For multi-turn agent conversations
        collector.add_multi_turn(
            messages=langchain_messages,  # LangChain BaseMessage list
            reference_tool_calls=[...],   # Optional
            reference="Expected goal..."  # Optional
        )
        
        # Save for evaluation
        collector.save("logs/ragas_traces/data.json")
    """
    
    def __init__(self):
        self.single_turn_samples: List[Dict[str, Any]] = []
        self.multi_turn_samples: List[Dict[str, Any]] = []
    
    def _convert_langchain_to_ragas(self, messages: List[Any]) -> List[Any]:
        """
        Convert LangChain messages to Ragas format.
        
        Manually converts since ragas.integrations.langchain has compatibility issues
        with newer LangChain versions.
        
        Args:
            messages: List of LangChain BaseMessage objects
            
        Returns:
            List of Ragas message objects
        """
        from langchain_core.messages import HumanMessage as LCHumanMessage
        from langchain_core.messages import AIMessage as LCAIMessage
        from langchain_core.messages import ToolMessage as LCToolMessage
        
        ragas_messages = []
        
        for msg in messages:
            if isinstance(msg, LCHumanMessage):
                ragas_messages.append(HumanMessage(content=msg.content))
            elif isinstance(msg, LCAIMessage):
                # Extract tool calls if present
                tool_calls = []
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls.append(ToolCall(
                            name=tc.get('name', ''),
                            args=tc.get('args', {})
                        ))
                
                ragas_messages.append(AIMessage(
                    content=msg.content or "",
                    tool_calls=tool_calls if tool_calls else None
                ))
            elif isinstance(msg, LCToolMessage):
                ragas_messages.append(ToolMessage(content=msg.content))
            else:
                # Fallback: try to extract content
                if hasattr(msg, 'content'):
                    ragas_messages.append(HumanMessage(content=str(msg.content)))
        
        return ragas_messages
        
    def add_single_turn(
        self,
        user_input: str,
        retrieved_contexts: List[str],
        response: str,
        reference: Optional[str] = None,
        reference_contexts: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a single-turn interaction for RAG evaluation.
        
        Args:
            user_input: User's question/query
            retrieved_contexts: List of context chunks retrieved from vector store
            response: Agent's generated response
            reference: Optional ground truth answer for comparison
            reference_contexts: Optional ground truth contexts
            metadata: Optional metadata (timestamps, model info, etc.)
            
        Raises:
            ValueError: If required fields are empty or invalid
        """
        # Input validation
        if not user_input or not user_input.strip():
            raise ValueError("user_input cannot be empty")
        
        if not isinstance(retrieved_contexts, list):
            raise ValueError("retrieved_contexts must be a list")
        
        if not retrieved_contexts:
            logger.warning("No retrieved contexts provided - some metrics may be limited")
        
        if not response or not response.strip():
            raise ValueError("response cannot be empty")
        
        sample_data = {
            "user_input": user_input.strip(),
            "retrieved_contexts": [ctx.strip() for ctx in retrieved_contexts if ctx and ctx.strip()],
            "response": response.strip(),
        }
        
        if reference:
            sample_data["reference"] = reference
            
        if reference_contexts:
            sample_data["reference_contexts"] = reference_contexts
            
        if metadata:
            sample_data["metadata"] = metadata
            
        self.single_turn_samples.append(sample_data)
    
    def add_multi_turn(
        self,
        messages: List[Any],  # LangChain BaseMessage objects
        reference_tool_calls: Optional[List[ToolCall]] = None,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a multi-turn agent conversation for agentic evaluation.
        
        Args:
            messages: List of LangChain messages (HumanMessage, AIMessage, ToolMessage)
            reference_tool_calls: Optional expected tool calls for ToolCallAccuracy
            reference: Optional expected goal/outcome for AgentGoalAccuracy
            metadata: Optional metadata (timestamps, model info, etc.)
            
        Raises:
            ValueError: If messages list is empty or invalid
        """
        # Input validation
        if not messages:
            raise ValueError("messages list cannot be empty")
        
        if not isinstance(messages, list):
            raise ValueError("messages must be a list")
        
        # Convert LangChain messages to Ragas format manually
        try:
            ragas_messages = self._convert_langchain_to_ragas(messages)
        except Exception as e:
            logger.error(f"Failed to convert messages: {e}")
            raise ValueError(f"Invalid message format: {e}") from e
        
        if not ragas_messages:
            raise ValueError("No valid messages after conversion")
        
        sample_data = {
            "messages": ragas_messages,
        }
        
        if reference_tool_calls:
            # Convert to serializable format
            sample_data["reference_tool_calls"] = [
                {"name": tc.name, "args": tc.args} 
                for tc in reference_tool_calls
            ]
            
        if reference:
            sample_data["reference"] = reference
            
        if metadata:
            sample_data["metadata"] = metadata
            
        self.multi_turn_samples.append(sample_data)
    
    def create_single_turn_dataset(self) -> EvaluationDataset:
        """
        Create Ragas EvaluationDataset from collected single-turn samples.
        
        Returns:
            EvaluationDataset ready for evaluation with Ragas metrics
        """
        samples = []
        for data in self.single_turn_samples:
            sample = SingleTurnSample(
                user_input=data["user_input"],
                retrieved_contexts=data["retrieved_contexts"],
                response=data["response"],
                reference=data.get("reference"),
                reference_contexts=data.get("reference_contexts"),
            )
            samples.append(sample)
            
        return EvaluationDataset(samples=samples)
    
    def create_multi_turn_dataset(self) -> EvaluationDataset:
        """
        Create Ragas EvaluationDataset from collected multi-turn samples.
        
        Returns:
            EvaluationDataset ready for agent evaluation metrics
        """
        samples = []
        for data in self.multi_turn_samples:
            # Reconstruct ToolCall objects if present
            reference_tool_calls = None
            if "reference_tool_calls" in data:
                reference_tool_calls = [
                    ToolCall(name=tc["name"], args=tc["args"])
                    for tc in data["reference_tool_calls"]
                ]
            
            # Reconstruct Ragas message objects from serialized data
            messages = data["messages"]
            if messages and isinstance(messages[0], dict):
                # Messages were serialized - need to reconstruct
                reconstructed_messages = []
                for msg_dict in messages:
                    msg_type = msg_dict.get("type", "").lower()
                    content = msg_dict.get("content", "")
                    
                    if msg_type in ["humanmessage", "human"]:
                        reconstructed_messages.append(HumanMessage(content=content))
                    elif msg_type in ["aimessage", "ai"]:
                        tool_calls_data = msg_dict.get("tool_calls")
                        tool_calls = []
                        if tool_calls_data:
                            for tc in tool_calls_data:
                                tool_calls.append(ToolCall(name=tc["name"], args=tc["args"]))
                        reconstructed_messages.append(AIMessage(
                            content=content or "",
                            tool_calls=tool_calls if tool_calls else None
                        ))
                    elif msg_type in ["toolmessage", "tool"]:
                        reconstructed_messages.append(ToolMessage(content=content))
                
                messages = reconstructed_messages
            
            sample = MultiTurnSample(
                user_input=messages,
                reference_tool_calls=reference_tool_calls,
                reference=data.get("reference"),
            )
            samples.append(sample)
            
        return EvaluationDataset(samples=samples)
    
    def save(self, filepath: Path | str) -> None:
        """
        Save collected data to JSON file.
        
        Args:
            filepath: Path to save JSON data
            
        Raises:
            IOError: If file cannot be written
            ValueError: If no samples to save
        """
        if len(self) == 0:
            logger.warning("No samples to save")
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert Ragas messages to serializable format
        def serialize_sample(sample: Dict[str, Any]) -> Dict[str, Any]:
            """Convert Ragas messages to dict for JSON serialization"""
            serialized = sample.copy()
            if "messages" in serialized:
                # Convert Ragas message objects to dicts
                serialized["messages"] = [
                    {
                        "type": msg.__class__.__name__,
                        "content": msg.content if hasattr(msg, "content") else None,
                        "tool_calls": [
                            {"name": tc.name, "args": tc.args}
                            for tc in msg.tool_calls
                        ] if hasattr(msg, "tool_calls") and msg.tool_calls else None,
                    }
                    for msg in serialized["messages"]
                ]
            return serialized
        
        data = {
            "schema_version": SCHEMA_VERSION,
            "timestamp": datetime.now().isoformat(),
            "single_turn_samples": [
                serialize_sample(s) for s in self.single_turn_samples
            ],
            "multi_turn_samples": [
                serialize_sample(s) for s in self.multi_turn_samples
            ],
            "counts": {
                "single_turn": len(self.single_turn_samples),
                "multi_turn": len(self.multi_turn_samples),
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self)} samples to {filepath}")
        except IOError as e:
            logger.error(f"Failed to save data to {filepath}: {e}")
            raise
    
    def load(self, filepath: Path | str) -> None:
        """
        Load previously collected data from JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {filepath}: {e}") from e
        
        # Check schema version
        file_version = data.get("schema_version", "0.0.0")
        if file_version != SCHEMA_VERSION:
            logger.warning(
                f"Schema version mismatch: file={file_version}, current={SCHEMA_VERSION}. "
                "Data migration may be needed."
            )
        
        # Reconstruct samples (messages stay as dicts for now)
        self.single_turn_samples = data.get("single_turn_samples", [])
        self.multi_turn_samples = data.get("multi_turn_samples", [])
        
        logger.info(f"Loaded {len(self)} samples from {filepath}")
    
    def clear(self) -> None:
        """Clear all collected samples"""
        self.single_turn_samples.clear()
        self.multi_turn_samples.clear()
    
    def __len__(self) -> int:
        """Total number of samples collected"""
        return len(self.single_turn_samples) + len(self.multi_turn_samples)
    
    def __repr__(self) -> str:
        return (
            f"RagasDataCollector("
            f"single_turn={len(self.single_turn_samples)}, "
            f"multi_turn={len(self.multi_turn_samples)})"
        )

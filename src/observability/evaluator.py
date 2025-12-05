"""
Ragas evaluation script for MSI AI Assistant.

Evaluates collected agent execution data using comprehensive Ragas metrics:
- RAG metrics: Faithfulness, Context Precision/Recall, Response Relevancy
- Agent metrics: Tool Call Accuracy, Agent Goal Accuracy, Topic Adherence
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio
import logging
import time
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    # RAG Metrics
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextPrecisionWithoutReference,
    LLMContextRecall,
    ContextEntityRecall,
    ResponseRelevancy,
    FactualCorrectness,
    # Agent Metrics
    ToolCallAccuracy,
    AgentGoalAccuracyWithReference,
    AgentGoalAccuracyWithoutReference,
    TopicAdherenceScore,
)

from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def retry_on_failure(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0):
    """
    Retry decorator for handling transient failures in LLM evaluation.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay on each retry
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def create_rag_metrics(
    evaluator_llm: Any,
    evaluator_embeddings: Any,
    include_reference_metrics: bool = False
) -> List[Any]:
    """
    Create RAG evaluation metrics.
    
    Args:
        evaluator_llm: Wrapped LLM for evaluation
        evaluator_embeddings: Wrapped embeddings for similarity
        include_reference_metrics: Include metrics requiring reference answers
        
    Returns:
        List of initialized Ragas metrics
    """
    metrics = [
        # Core RAG metrics (no reference needed)
        Faithfulness(llm=evaluator_llm),
        LLMContextPrecisionWithoutReference(llm=evaluator_llm),
        ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
    ]
    
    if include_reference_metrics:
        # Reference-based metrics (need ground truth)
        metrics.extend([
            LLMContextPrecisionWithReference(llm=evaluator_llm),
            LLMContextRecall(llm=evaluator_llm),
            ContextEntityRecall(llm=evaluator_llm),
            FactualCorrectness(llm=evaluator_llm),
        ])
    
    return metrics


def create_agent_metrics(
    evaluator_llm: Any,
    include_reference_metrics: bool = False
) -> List[Any]:
    """
    Create agent evaluation metrics.
    
    Args:
        evaluator_llm: Wrapped LLM for evaluation
        include_reference_metrics: Include metrics requiring reference data
        
    Returns:
        List of initialized agent metrics
    """
    metrics = [
        # Agent metrics (no reference needed)
        AgentGoalAccuracyWithoutReference(llm=evaluator_llm),
    ]
    
    if include_reference_metrics:
        # Reference-based agent metrics
        metrics.extend([
            ToolCallAccuracy(),
            AgentGoalAccuracyWithReference(llm=evaluator_llm),
            TopicAdherenceScore(llm=evaluator_llm, mode="precision"),
        ])
    
    return metrics


@retry_on_failure(max_attempts=3, delay=2.0)
async def evaluate_agent_performance(
    dataset_path: Path | str,
    evaluation_type: str = "single_turn",
    model: str = "gpt-4o-mini",
    include_reference_metrics: bool = False,
    output_path: Optional[Path | str] = None
) -> Dict[str, Any]:
    """
    Evaluate agent performance using Ragas metrics with retry logic.
    
    Args:
        dataset_path: Path to collected data JSON file
        evaluation_type: "single_turn" for RAG or "multi_turn" for agent
        model: Model to use for evaluation (default: gpt-4o-mini)
        include_reference_metrics: Include metrics requiring reference data
        output_path: Optional path to save results
        
    Returns:
        Dictionary with evaluation results
        
    Raises:
        FileNotFoundError: If dataset file doesn't exist
        ValueError: If evaluation type is invalid or no samples found
    """
    from src.observability.collector import RagasDataCollector
    
    start_time = time.time()
    
    logger.info(
        f"Starting evaluation: dataset={dataset_path}, type={evaluation_type}, "
        f"model={model}, with_reference={include_reference_metrics}"
    )
    
    # Load collected data
    collector = RagasDataCollector()
    try:
        collector.load(dataset_path)
    except FileNotFoundError:
        logger.error(f"Dataset file not found: {dataset_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise
    
    # Create dataset based on type
    if evaluation_type == "single_turn":
        dataset = collector.create_single_turn_dataset()
    elif evaluation_type == "multi_turn":
        dataset = collector.create_multi_turn_dataset()
    else:
        raise ValueError(f"Invalid evaluation_type: {evaluation_type}")
    
    if len(dataset) == 0:
        error_msg = f"No {evaluation_type} samples found in {dataset_path}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Loaded {len(dataset)} {evaluation_type} samples")
    print(f"Evaluating {len(dataset)} {evaluation_type} samples...")
    
    # Initialize evaluator LLM and embeddings
    try:
        llm = ChatOpenAI(model=model)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        evaluator_llm = LangchainLLMWrapper(llm)
        evaluator_embeddings = LangchainEmbeddingsWrapper(embeddings)
        logger.info(f"Initialized evaluator with model: {model}")
    except Exception as e:
        logger.error(f"Failed to initialize evaluator: {e}")
        raise
    
    # Select appropriate metrics
    if evaluation_type == "single_turn":
        metrics = create_rag_metrics(
            evaluator_llm, 
            evaluator_embeddings,
            include_reference_metrics
        )
    else:  # multi_turn
        metrics = create_agent_metrics(
            evaluator_llm,
            include_reference_metrics
        )
    
    metric_names = [m.__class__.__name__ for m in metrics]
    logger.info(f"Using metrics: {metric_names}")
    print(f"\nMetrics: {metric_names}")
    
    # Run evaluation with error handling
    logger.info("Starting Ragas evaluation...")
    eval_start = time.time()
    
    try:
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=evaluator_llm,
        )
        eval_duration = time.time() - eval_start
        logger.info(f"Evaluation completed in {eval_duration:.2f}s")
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise
    
    # Convert to pandas for display
    df = result.to_pandas()
    
    # Log summary statistics
    summary_stats = df.describe()
    logger.info(f"Evaluation summary:\n{summary_stats}")
    
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    print(df)
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    print(df.describe())
    
    # Save results if requested
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save as CSV
            csv_path = output_path.with_suffix('.csv')
            df.to_csv(csv_path, index=False)
            logger.info(f"Results saved to: {csv_path}")
            print(f"\nResults saved to: {csv_path}")
            
            # Save summary
            summary_path = output_path.with_suffix('.summary.txt')
            with open(summary_path, 'w') as f:
                f.write("EVALUATION RESULTS\n")
                f.write("="*80 + "\n")
                f.write(df.to_string())
                f.write("\n\n")
                f.write("SUMMARY STATISTICS\n")
                f.write("="*80 + "\n")
                f.write(df.describe().to_string())
            logger.info(f"Summary saved to: {summary_path}")
            print(f"Summary saved to: {summary_path}")
        except IOError as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    total_duration = time.time() - start_time
    logger.info(f"Total evaluation completed in {total_duration:.2f}s")
    
    return {
        "scores": result.scores,
        "dataframe": df,
        "dataset": dataset,
        "duration": total_duration,
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Evaluate MSI AI Assistant using Ragas metrics"
    )
    parser.add_argument(
        "dataset_path",
        type=str,
        help="Path to collected data JSON file"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["single_turn", "multi_turn"],
        default="single_turn",
        help="Evaluation type: single_turn (RAG) or multi_turn (agent)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="Model to use for evaluation (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--with-reference",
        action="store_true",
        help="Include metrics requiring reference data"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save evaluation results"
    )
    
    args = parser.parse_args()
    
    asyncio.run(evaluate_agent_performance(
        dataset_path=args.dataset_path,
        evaluation_type=args.type,
        model=args.model,
        include_reference_metrics=args.with_reference,
        output_path=args.output
    ))

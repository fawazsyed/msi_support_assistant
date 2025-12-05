# Observability with Ragas

MSI AI Assistant includes comprehensive observability using [Ragas](https://docs.ragas.io/) for evaluating RAG and agentic system performance.

## Overview

The observability system follows Ragas's **manual collection approach** as documented in the [LangChain Integration guide](https://docs.ragas.io/en/stable/howtos/integrations/langchain/):

1. **Data Collection**: Automatically collects queries, contexts, responses, and tool calls during agent execution
2. **Evaluation**: Runs Ragas metrics on collected data to measure performance
3. **Analysis**: Provides detailed scores and insights

## Architecture

```
src/observability/
├── __init__.py         # Module exports
├── collector.py        # RagasDataCollector - collects execution data
└── evaluator.py        # Evaluation functions with Ragas metrics
```

## Data Collection

### Automatic Collection

Enable in `src/core/config.py`:

```python
ENABLE_RAGAS_COLLECTION = True
RAGAS_DATA_DIR = "logs/ragas_data"
```

When enabled, `main.py` automatically collects:
- User queries
- Retrieved contexts from vector store
- Agent responses
- Tool calls and tool messages
- Full conversation history

### Manual Collection

Use `RagasDataCollector` directly in your code:

```python
from src.observability import RagasDataCollector

collector = RagasDataCollector()

# Single-turn RAG interaction
collector.add_single_turn(
    user_input="How do I add a user?",
    retrieved_contexts=["Context 1", "Context 2"],
    response="To add a user, follow these steps...",
    reference="Expected answer..."  # Optional ground truth
)

# Multi-turn agent conversation
collector.add_multi_turn(
    messages=langchain_messages,  # List of LangChain BaseMessage
    reference_tool_calls=[...],   # Optional expected tool calls
    reference="Expected outcome"  # Optional expected goal
)

# Save collected data
collector.save("logs/ragas_data/my_data.json")
```

## Evaluation Metrics

### RAG Metrics (Single-Turn)

Evaluate document retrieval and response generation quality:

| Metric | Description | Reference Required |
|--------|-------------|-------------------|
| **Faithfulness** | Are generated answers faithful to retrieved contexts? | No |
| **ResponseRelevancy** | Is response relevant to user query? | No |
| **LLMContextPrecisionWithoutReference** | Are retrieved contexts relevant to response? | No |
| **LLMContextPrecisionWithReference** | Are retrieved contexts relevant to ground truth? | Yes |
| **LLMContextRecall** | Is ground truth covered by contexts? | Yes |
| **ContextEntityRecall** | Are entities from reference in contexts? | Yes |
| **FactualCorrectness** | Is response factually correct vs reference? | Yes |

### Agent Metrics (Multi-Turn)

Evaluate agentic behavior with tool use:

| Metric | Description | Reference Required |
|--------|-------------|-------------------|
| **AgentGoalAccuracyWithoutReference** | Did agent achieve inferred user goal? | No |
| **AgentGoalAccuracyWithReference** | Did agent achieve stated goal? | Yes |
| **ToolCallAccuracy** | Did agent call correct tools with correct args? | Yes |
| **TopicAdherenceScore** | Did agent stay on topic? | Yes |

## Running Evaluations

### Command Line

Evaluate collected data:

```bash
# Basic evaluation (no reference metrics)
uv run python -m src.observability.evaluator logs/ragas_data/agent_data_20241205_143022.json --type multi_turn

# With reference metrics (requires ground truth in data)
uv run python -m src.observability.evaluator logs/ragas_data/agent_data_20241205_143022.json \
    --type multi_turn \
    --with-reference

# Save results to file
uv run python -m src.observability.evaluator logs/ragas_data/agent_data_20241205_143022.json \
    --type multi_turn \
    --output logs/ragas_data/evaluation_results.csv

# Use different evaluation model
uv run python -m src.observability.evaluator logs/ragas_data/agent_data_20241205_143022.json \
    --type multi_turn \
    --model gpt-4o
```

### Programmatic

```python
from src.observability.evaluator import evaluate_agent_performance

results = await evaluate_agent_performance(
    dataset_path="logs/ragas_data/agent_data_20241205_143022.json",
    evaluation_type="multi_turn",  # or "single_turn"
    model="gpt-4o-mini",
    include_reference_metrics=False,
    output_path="logs/ragas_data/results.csv"
)

print(results["scores"])
print(results["dataframe"])
```

## Evaluation Types

### Single-Turn Evaluation

For RAG queries where agent retrieves docs and responds:

```bash
uv run python -m src.observability.evaluator data.json --type single_turn
```

Metrics: Faithfulness, Context Precision, Response Relevancy, etc.

### Multi-Turn Evaluation

For agentic conversations with multiple tool calls:

```bash
uv run python -m src.observability.evaluator data.json --type multi_turn
```

Metrics: Agent Goal Accuracy, Tool Call Accuracy, Topic Adherence, etc.

## Workflow Example

### 1. Run Agent with Collection

```bash
# Enable collection in config.py
ENABLE_RAGAS_COLLECTION = True

# Run agent
uv run src/main.py
```

Output:
```
Ragas data collection enabled. Data will be saved to logs/ragas_data
...
Collected 2 samples
Data saved to logs/ragas_data/agent_data_20241205_143022.json

To evaluate performance, run:
  uv run python -m src.observability.evaluator logs/ragas_data/agent_data_20241205_143022.json --type multi_turn
```

### 2. Evaluate Performance

```bash
uv run python -m src.observability.evaluator \
    logs/ragas_data/agent_data_20241205_143022.json \
    --type multi_turn \
    --output logs/ragas_data/results.csv
```

Output:
```
Evaluating 2 multi_turn samples...

Metrics: ['AgentGoalAccuracyWithoutReference']

================================================================================
EVALUATION RESULTS
================================================================================
   agent_goal_accuracy_without_reference
0                                  0.95
1                                  0.88

================================================================================
SUMMARY STATISTICS
================================================================================
       agent_goal_accuracy_without_reference
count                                   2.00
mean                                    0.92
std                                     0.05
min                                     0.88
25%                                     0.89
50%                                     0.92
75%                                     0.93
max                                     0.95

Results saved to: logs/ragas_data/results.csv
Summary saved to: logs/ragas_data/results.summary.txt
```

### 3. Analyze Results

```python
import pandas as pd

df = pd.read_csv("logs/ragas_data/results.csv")

# Find low-scoring samples
low_scores = df[df["agent_goal_accuracy_without_reference"] < 0.8]
print(low_scores)

# Compare across metrics
print(df.describe())
```

## Adding Reference Data (Ground Truth)

### When to Use Reference Data

**Development/Testing (No References Needed)**
- Use metrics like `AgentGoalAccuracyWithoutReference`, `Faithfulness`, `ResponseRelevancy`
- Faster evaluation, no manual ground truth creation
- Sufficient for iterative development

**Production/Benchmarking (References Recommended)**
- Use when you need precise validation against known-good outcomes
- Compare agent tool calls against expected calls
- Validate responses against curated answers
- Measure topic adherence to specific subjects

### How to Add Reference Data

#### Single-Turn RAG

```python
from src.observability import RagasDataCollector

collector = RagasDataCollector()

# WITHOUT reference (for development)
collector.add_single_turn(
    user_input="How do I add a user in MSI Portal?",
    retrieved_contexts=["Context 1...", "Context 2..."],
    response="To add a user, navigate to Admin > Users..."
)

# WITH reference (for production benchmarking)
collector.add_single_turn(
    user_input="How do I add a user in MSI Portal?",
    retrieved_contexts=["Context 1...", "Context 2..."],
    response="To add a user, navigate to Admin > Users...",
    reference="Users are added via Admin panel > User Management > Add User button. Required fields: email, role, department."
)

# Save and evaluate
collector.save("logs/ragas_data/rag_data.json")
```

Then evaluate with reference metrics:
```bash
uv run python -m src.observability.evaluator logs/ragas_data/rag_data.json \
    --type single_turn \
    --with-reference  # Enables FactualCorrectness, ContextRecall, etc.
```

#### Multi-Turn Agent Conversations

```python
from ragas.messages import ToolCall

collector = RagasDataCollector()

# WITHOUT reference (for development)
collector.add_multi_turn(
    messages=langchain_messages  # Full conversation history
)

# WITH reference (for production benchmarking)
collector.add_multi_turn(
    messages=langchain_messages,
    reference="Agent should search documentation, find user creation steps, and provide clear instructions",
    reference_tool_calls=[
        ToolCall(
            name="search_msi_documentation",
            args={"query": "add user portal"}
        ),
        ToolCall(
            name="retrieve_document",
            args={"doc_id": "user_management_guide"}
        )
    ],
    reference_topics=["user_management", "admin_portal", "authentication"]
)

collector.save("logs/ragas_data/agent_data.json")
```

Then evaluate with reference metrics:
```bash
uv run python -m src.observability.evaluator logs/ragas_data/agent_data.json \
    --type multi_turn \
    --with-reference  # Enables ToolCallAccuracy, AgentGoalAccuracyWithReference, TopicAdherence
```

### Reference Metrics Behavior

**Without `--with-reference` flag:**
- Uses only non-reference metrics (AgentGoalAccuracyWithoutReference, Faithfulness, etc.)
- Works with any collected data
- Faster evaluation

**With `--with-reference` flag:**
- Validates that required reference fields exist in data
- Fails with clear error if reference data missing:
  ```
  ValueError: The metric [tool_call_accuracy] requires ['reference_tool_calls'] to be present in the dataset.
  ```
- Use only when you've added reference data during collection

## Best Practices

### 1. Start Without References

Begin evaluation without reference metrics (no `--with-reference` flag):
- Faster evaluation
- No need to manually create ground truth
- Still get valuable insights (Faithfulness, Goal Accuracy, etc.)

### 2. Add References for Critical Workflows

Create ground truth for production-critical interactions:
```python
# Example: User management workflows with expected tool calls
collector.add_multi_turn(
    messages=messages,
    reference="Agent correctly identifies user creation requires admin role",
    reference_tool_calls=[
        ToolCall(name="check_user_permissions", args={"user_id": "123"}),
        ToolCall(name="search_msi_documentation", args={"query": "user creation admin"})
    ]
)
```

### 3. Batch Evaluation

Collect data from multiple runs, then evaluate all at once:
```bash
# Run 1
uv run src/main.py  # Creates agent_data_20241205_100000.json

# Run 2
uv run src/main.py  # Creates agent_data_20241205_110000.json

# Combine and evaluate
# TODO: Add script to merge datasets
```

### 4. Monitor Trends

Track metrics over time:
```python
import glob
import pandas as pd

# Load all evaluation results
results = []
for file in glob.glob("logs/ragas_data/results_*.csv"):
    df = pd.read_csv(file)
    results.append(df)

combined = pd.concat(results)
combined.groupby("timestamp").mean().plot()
```

## Configuration

### Evaluator Model

Use more powerful models for better evaluation quality:

```bash
# GPT-4o (slower, more accurate)
--model gpt-4o

# GPT-4o-mini (faster, good balance) [DEFAULT]
--model gpt-4o-mini

# Claude Sonnet
--model claude-3-5-sonnet-20241022
```

### Data Collection Settings

In `src/core/config.py`:

```python
# Toggle collection on/off
ENABLE_RAGAS_COLLECTION = True

# Change storage location
RAGAS_DATA_DIR = "logs/ragas_data"
```

## Troubleshooting

### No samples collected

Check if collection is enabled:
```python
# src/core/config.py
ENABLE_RAGAS_COLLECTION = True  # Must be True
```

### Evaluation fails: "No multi_turn samples found"

Verify data file has correct type:
```python
import json
with open("logs/ragas_data/agent_data.json") as f:
    data = json.load(f)
    print(f"Single-turn: {len(data['single_turn_samples'])}")
    print(f"Multi-turn: {len(data['multi_turn_samples'])}")
```

### Reference metrics show NaN

Reference metrics require ground truth in collected data:
```python
# Add reference when collecting
collector.add_single_turn(
    user_input="...",
    retrieved_contexts=[...],
    response="...",
    reference="Ground truth answer"  # Must provide
)
```

## References

- [Ragas Documentation](https://docs.ragas.io/)
- [LangChain Integration Guide](https://docs.ragas.io/en/stable/howtos/integrations/langchain/)
- [Available Metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [Agent Evaluation](https://docs.ragas.io/en/stable/tutorials/agent/)

## Future Enhancements

- [ ] Automatic context extraction from RAG tool calls
- [ ] Integration with LangSmith for automatic tracing
- [ ] Dataset merging utility for batch evaluation
- [ ] Time-series visualization for metric trends
- [ ] Custom metrics for MSI-specific evaluation criteria

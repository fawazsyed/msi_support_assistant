"""
Configuration constants for MSI AI Assistant.

Centralizes all configuration to avoid duplication and enable easy customization.
"""

# =============================================================================
# LLM Configuration
# =============================================================================

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MODEL_PROVIDER = "openai"

# Alternative models (uncomment to use):
# DEFAULT_MODEL = "gpt-4o"
# DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
# DEFAULT_MODEL_PROVIDER = "anthropic"
# DEFAULT_MODEL = "gemini-2.0-flash-exp"
# DEFAULT_MODEL_PROVIDER = "google-genai"

# =============================================================================
# Rate Limiting Configuration
# =============================================================================

RATE_LIMIT_REQUESTS_PER_SECOND = 2  # 120 requests/minute
RATE_LIMIT_CHECK_INTERVAL = 0.1     # Check every 100ms
RATE_LIMIT_MAX_BUCKET_SIZE = 10     # Allow bursts of up to 10 requests

# =============================================================================
# Agent Configuration
# =============================================================================

TOOL_CALL_LIMIT = 15                # Max tool calls per query
TOOL_CALL_EXIT_BEHAVIOR = "continue"  # Continue when limit hit

SYSTEM_PROMPT = (
    "You are an MSI Support Assistant powered by Motorola Solutions. "
    "You have access to product documentation via the search_msi_documentation tool. "
    "When users ask about MSI products, features, or how-to questions, "
    "use the search tool to find relevant information before answering. "
    "Always provide accurate information based on the documentation."
)

# =============================================================================
# Embeddings Configuration
# =============================================================================

EMBEDDING_MODEL = "text-embedding-3-small"

# =============================================================================
# Vector Store Configuration
# =============================================================================

VECTOR_STORE_COLLECTION_NAME = "msi_support_docs"
CHROMA_PERSIST_DIR = "chroma_langchain_db"

# Text Splitting
CHUNK_SIZE = 1500                   # ~375 tokens per chunk
CHUNK_OVERLAP = 300                 # 20% overlap for context continuity
CHUNK_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

# =============================================================================
# MCP Server Configuration
# =============================================================================

MCP_TICKETING_URL = "http://127.0.0.1:9000/mcp"
MCP_ORGANIZATIONS_URL = "http://127.0.0.1:9001/mcp"
MCP_ISSUER_URL = "http://127.0.0.1:9400"  # OAuth IDP for authentication

# =============================================================================
# Logging Configuration
# =============================================================================

LOG_KEEP_RECENT = 10  # Keep last 10 log files

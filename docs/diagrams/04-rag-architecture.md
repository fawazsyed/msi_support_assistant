# RAG (Retrieval-Augmented Generation) Architecture

## RAG System Overview

```mermaid
graph TB
    subgraph "Document Processing Pipeline"
        DOC[MSI Documentation<br/>video_manager_admin_guide.txt] --> LOAD[Document Loader]
        LOAD --> SPLIT[Text Splitter<br/>Chunk Size: 1500<br/>Overlap: 300]
        SPLIT --> CHUNKS[Document Chunks]
    end

    subgraph "Embedding & Storage"
        CHUNKS --> EMB[OpenAI Embeddings<br/>text-embedding-3-small]
        EMB --> VECS[Vector Embeddings<br/>1536 dimensions]
        VECS --> STORE[(Chroma Vector Store<br/>chroma_langchain_db_msi_docs/)]
    end

    subgraph "Query Processing"
        QUERY[User Query:<br/>"How do I add a user?"] --> QEMB[Embed Query]
        QEMB --> SEARCH[Similarity Search<br/>k=2 chunks]
        STORE --> SEARCH
        SEARCH --> CONTEXT[Retrieved Context:<br/>Top 2 relevant chunks]
    end

    subgraph "LLM Integration"
        CONTEXT --> TOOL[search_msi_documentation<br/>LangChain Tool]
        TOOL --> AGENT[LangChain Agent]
        AGENT --> LLM[GPT-4o-mini]
        LLM --> RESPONSE[AI Response with<br/>cited documentation]
    end

    style DOC fill:#f59e0b
    style STORE fill:#ec4899
    style LLM fill:#10b981
    style RESPONSE fill:#6366f1
```

## RAG Agent Class Hierarchy

```mermaid
classDiagram
    class BaseRAGAgent {
        <<abstract>>
        +project_root: Path
        +embeddings: OpenAIEmbeddings
        +vector_store: Chroma
        +name()* str
        +description()* str
        +document_path()* Path
        +collection_name() str
        +persist_directory() str
        +initialize() None
        +_load_documents() str
        +_split_documents(content) List[str]
        +search(query, k) str
        +create_tool()* Tool
    }

    class MSIDocsRAGAgent {
        +name() str = "msi_docs"
        +description() str
        +document_path() Path
        +create_tool() Tool
    }

    class RAGAgentRegistry {
        -_agents: List[BaseRAGAgent]
        +register(agent) None
        +get_all_tools() List[Tool]
        +get_agent(name) Optional[BaseRAGAgent]
    }

    BaseRAGAgent <|-- MSIDocsRAGAgent
    RAGAgentRegistry o-- BaseRAGAgent : manages
```

## Document Chunking Strategy

### Text Splitting Parameters

```python
RecursiveCharacterTextSplitter(
    chunk_size=1500,        # Characters per chunk
    chunk_overlap=300,      # Overlap between chunks
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

### Why These Values?

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| **chunk_size** | 1500 | Fits within context window while maintaining coherence |
| **chunk_overlap** | 300 | Ensures continuity across chunk boundaries (20% overlap) |
| **separators** | Hierarchical | Respects natural document structure |

### Chunking Example

```
Document (5000 chars)
├── Chunk 1 (chars 0-1500)
├── Chunk 2 (chars 1200-2700)  ← 300 char overlap
├── Chunk 3 (chars 2400-3900)  ← 300 char overlap
└── Chunk 4 (chars 3600-5000)  ← 300 char overlap
```

## Vector Search Flow

```mermaid
sequenceDiagram
    participant User
    participant Agent as LangChain Agent
    participant Tool as search_msi_documentation
    participant RAG as MSIDocsRAGAgent
    participant VS as Chroma Vector Store
    participant EMB as OpenAI Embeddings

    User->>Agent: "How do I add a user to Video Manager?"
    activate Agent

    Note over Agent: LLM decides to search docs

    Agent->>Tool: search_msi_documentation(<br/>"add user Video Manager")
    activate Tool

    Tool->>RAG: search(query, k=2)
    activate RAG

    RAG->>EMB: embed("add user Video Manager")
    activate EMB
    EMB-->>RAG: query_vector [1536 dims]
    deactivate EMB

    RAG->>VS: similarity_search(query_vector, k=2)
    activate VS

    Note over VS: Cosine similarity search<br/>across 150+ chunks

    VS-->>RAG: [Chunk 47, Chunk 52]<br/>(Most relevant chunks)
    deactivate VS

    RAG->>RAG: Format chunks:<br/>"Document excerpt 1:\n..."

    RAG-->>Tool: Formatted documentation
    deactivate RAG

    Tool-->>Agent: Documentation context
    deactivate Tool

    Note over Agent: LLM generates answer<br/>using retrieved context

    Agent-->>User: "To add a user in Video Manager:<br/>1. Go to Administration...<br/>2. Click Users..."
    deactivate Agent
```

## RAG Agent Registry Pattern

### Adding Custom RAG Agents

```mermaid
graph LR
    subgraph "Current Agents"
        MSI[MSIDocsRAGAgent<br/>MSI Documentation]
    end

    subgraph "Future Agents"
        BRAND[BrandMessagingRAGAgent<br/>Brand Guidelines]
        KB[KnowledgeBaseRAGAgent<br/>Internal Wiki]
        API[APIDocsRAGAgent<br/>API Reference]
    end

    REGISTRY[RAGAgentRegistry] --> MSI
    REGISTRY -.->|Easy to add| BRAND
    REGISTRY -.->|Easy to add| KB
    REGISTRY -.->|Easy to add| API

    style MSI fill:#10b981
    style BRAND fill:#94a3b8
    style KB fill:#94a3b8
    style API fill:#94a3b8
```

### Registration Code

```python
from src.rag.registry import RAGAgentRegistry
from src.rag.agents.msi_docs import MSIDocsRAGAgent

# Initialize registry
registry = RAGAgentRegistry()

# Register agents
registry.register(MSIDocsRAGAgent(project_root, embeddings))
# registry.register(BrandMessagingRAGAgent(project_root, embeddings))  # Future

# Get all tools for LangChain agent
rag_tools = await registry.get_all_tools()
```

## Vector Store Persistence

### Directory Structure

```
data/vector_stores/
└── chroma_langchain_db_msi_docs/
    ├── chroma.sqlite3           # Metadata database
    └── 8d604491-1def-.../        # Collection data
        ├── data_level0.bin       # Vector embeddings
        ├── header.bin
        ├── length.bin
        └── link_lists.bin
```

### Benefits of Persistence

- ✅ **No re-indexing** on server restart
- ✅ **Faster startup** (skip embedding generation)
- ✅ **Version control friendly** (can .gitignore)
- ✅ **Incremental updates** (add new documents without full rebuild)

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Initial Indexing** | ~30 seconds | 5000+ chars → 4-5 chunks → OpenAI API |
| **Subsequent Startups** | ~2 seconds | Loads from persisted vector store |
| **Query Time** | ~500ms | Embedding (200ms) + Search (300ms) |
| **Accuracy** | High | Semantic search finds relevant content |
| **Context Window** | 2 chunks | ~3000 chars total context |

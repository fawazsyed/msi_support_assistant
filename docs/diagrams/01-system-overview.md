# System Overview Architecture

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[Angular UI<br/>localhost:4200]
    end

    subgraph "API Layer"
        API[FastAPI Server<br/>localhost:8000]
    end

    subgraph "Authentication Layer"
        IDP[Mock IDP<br/>localhost:9400<br/>JWT Token Provider]
    end

    subgraph "MCP Servers"
        TICK[Ticketing MCP<br/>localhost:9000<br/>msi-ticketing]
        ORG[Organizations MCP<br/>localhost:9001<br/>msi-organizations]
    end

    subgraph "LLM Layer"
        LLM[OpenAI GPT-4o-mini<br/>Chat Model]
        EMB[OpenAI Embeddings<br/>text-embedding-3-small]
    end

    subgraph "Data Layer"
        TICKDB[(ticket.db<br/>SQLite)]
        USERDB[(users.db<br/>SQLite)]
        ORGDB[(organizations.db<br/>SQLite)]
        VSTORE[(Chroma Vector Store<br/>Document Embeddings)]
        DOCS[/MSI Documentation<br/>video_manager_admin_guide.txt/]
    end

    UI -->|HTTP POST /api/chat/stream<br/>SSE| API
    API -->|OAuth Token Request| IDP
    IDP -->|JWT Token| API
    API -->|Authenticated Requests| TICK
    API -->|Authenticated Requests| ORG
    API -->|LLM Queries| LLM
    API -->|Embed Documents| EMB
    API -->|Vector Search| VSTORE
    TICK -->|Read/Write| TICKDB
    ORG -->|Read| USERDB
    ORG -->|Read| ORGDB
    VSTORE -->|Load Documents| DOCS
    EMB -->|Create Embeddings| VSTORE

    style UI fill:#6366f1
    style API fill:#8b5cf6
    style IDP fill:#ec4899
    style TICK fill:#f59e0b
    style ORG fill:#f59e0b
    style LLM fill:#10b981
    style EMB fill:#10b981
```

## Component Ports

| Component | Port | Protocol | Purpose |
|-----------|------|----------|---------|
| Angular UI | 4200 | HTTP | User interface |
| FastAPI Server | 8000 | HTTP | Main API backend |
| Mock IDP | 9400 | HTTP | OAuth/JWT authentication |
| Ticketing MCP | 9000 | HTTP | Support ticket management |
| Organizations MCP | 9001 | HTTP | User/org data retrieval |

## Data Flow

1. **User Request**: Angular UI → FastAPI Server
2. **Authentication**: FastAPI → Mock IDP (get JWT token)
3. **LLM Processing**: FastAPI → OpenAI (chat completion with tools)
4. **Tool Execution**: LLM decides to call MCP tools
5. **MCP Operations**: FastAPI → MCP Servers (with JWT auth)
6. **RAG Retrieval**: FastAPI → Vector Store (semantic search)
7. **Response**: Streaming SSE back to Angular UI

# Complete Request Flow Architecture

## End-to-End Request Flow

```mermaid
sequenceDiagram
    autonumber

    participant User as User Browser
    participant UI as Angular UI<br/>(4200)
    participant API as FastAPI<br/>(8000)
    participant Agent as LangChain Agent
    participant LLM as OpenAI<br/>GPT-4o-mini
    participant IDP as Mock IDP<br/>(9400)
    participant MCP as MCP Server<br/>(9000/9001)
    participant RAG as RAG Agent
    participant VS as Vector Store
    participant DB as Database

    Note over User,DB: Example: "How do I add a user in Video Manager?"

    User->>UI: Type message & press Enter
    activate UI

    UI->>UI: Add user message to conversation

    UI->>API: POST /api/chat/stream<br/>Content-Type: application/json<br/>{messages: [{role: "user", content: "..."}]}
    activate API

    Note over API: Startup: Initialize agent if needed

    API->>IDP: POST /token<br/>grant_type=client_credentials<br/>audience=[9000, 9001]
    activate IDP
    IDP-->>API: {access_token: "eyJ...", expires_in: 600}
    deactivate IDP

    API->>API: Initialize MultiServerMCPClient<br/>with OAuth tokens

    API->>MCP: GET /mcp/tools<br/>Authorization: Bearer eyJ...
    activate MCP
    MCP->>MCP: Verify JWT
    MCP-->>API: {tools: [create_ticket, get_my_tickets, ...]}
    deactivate MCP

    API->>RAG: Initialize RAG agents
    activate RAG
    RAG->>RAG: Load vector store<br/>(or create from docs)
    RAG-->>API: {tools: [search_msi_documentation]}
    deactivate RAG

    API->>Agent: Create LangChain agent<br/>with MCP tools + RAG tools

    Note over API: Agent initialized, ready to process

    API->>Agent: ainvoke({messages: [...]})
    activate Agent

    Agent->>LLM: Chat completion request<br/>System: "You are MSI Assistant..."<br/>Tools: [14 available tools]<br/>User: "How do I add a user?"
    activate LLM

    Note over LLM: Reasoning:<br/>"User asking about Video Manager,<br/>I should search documentation"

    LLM-->>Agent: Tool call:<br/>search_msi_documentation(<br/>  query="add user Video Manager")
    deactivate LLM

    Agent->>RAG: Execute tool
    activate RAG

    RAG->>VS: Embed query & similarity search
    activate VS
    VS-->>RAG: Top 2 relevant chunks
    deactivate VS

    RAG-->>Agent: "Document excerpt 1:\n<br/>To add a user in Video Manager:<br/>1. Navigate to Administration...<br/>..."
    deactivate RAG

    Agent->>LLM: Continue with tool result
    activate LLM

    Note over LLM: "I have the documentation,<br/>now I'll provide clear steps"

    LLM-->>Agent: Final response:<br/>"Based on the documentation,<br/>here's how to add a user..."
    deactivate LLM

    Agent-->>API: {content: "...", tool_calls: [...]}
    deactivate Agent

    Note over API: Stream response as SSE

    loop Stream chunks
        API-->>UI: data: {"type": "content",<br/>       "content": "Based..."}<br/><br/>
    end

    API-->>UI: data: {"type": "done"}<br/><br/>
    deactivate API

    UI->>UI: Append AI message to conversation<br/>Render markdown

    UI-->>User: Display formatted response
    deactivate UI

    Note over User: Sees answer with proper formatting
```

## Request Flow Variations

### Scenario 1: Pure Documentation Query

```mermaid
graph LR
    Q["How do I configure Video Manager?"]
    --> LLM[LLM Decision]
    --> RAG[RAG Tool Only]
    --> VS[Vector Search]
    --> DOC[Documentation]
    --> RESP[Formatted Answer]

    style RAG fill:#10b981
```

### Scenario 2: Action Request (Create Ticket)

```mermaid
graph LR
    Q["Create a ticket about login issues"]
    --> LLM[LLM Decision]
    --> MCP[MCP Tool Only]
    --> TICK[Ticketing Server]
    --> DB[(Database)]
    --> RESP[Confirmation]

    style MCP fill:#f59e0b
```

### Scenario 3: Hybrid Request

```mermaid
graph LR
    Q["How do I add a user and create a ticket about it?"]
    --> LLM[LLM Decision]
    --> MULTI[Multiple Tools]

    MULTI --> RAG[1. Search Docs]
    MULTI --> MCP[2. Create Ticket]

    RAG --> VS[Vector Search]
    MCP --> TICK[Ticketing Server]

    VS --> RESP[Combined Response]
    TICK --> RESP

    style RAG fill:#10b981
    style MCP fill:#f59e0b
```

## Streaming Response Flow

### Server-Sent Events (SSE) Protocol

```mermaid
sequenceDiagram
    participant UI as Angular UI
    participant API as FastAPI /api/chat/stream

    UI->>API: POST with fetch()<br/>Accept: text/event-stream
    activate API

    Note over API: Process with LangChain agent

    loop Stream response chunks
        API-->>UI: data: {"type":"content","content":"Based"}\n\n
        UI->>UI: Update message.content += "Based"
        UI->>UI: Trigger change detection

        API-->>UI: data: {"type":"content","content":" on"}\n\n
        UI->>UI: Update message.content += " on"

        API-->>UI: data: {"type":"content","content":" the"}\n\n
        UI->>UI: Update message.content += " the"
    end

    API-->>UI: data: {"type":"tool_call","name":"search_msi_documentation"}\n\n
    UI->>UI: Add tool call to message.toolCalls[]

    API-->>UI: data: {"type":"done"}\n\n
    UI->>UI: Set message.isStreaming = false

    API-->>UI: [Connection closes]
    deactivate API
```

### SSE Message Types

| Type | Purpose | Example |
|------|---------|---------|
| **content** | Stream text chunks | `{"type":"content","content":"Hello"}` |
| **tool_call** | Notify tool execution | `{"type":"tool_call","name":"create_ticket"}` |
| **error** | Stream errors | `{"type":"error","message":"..."}` |
| **done** | Signal completion | `{"type":"done"}` |

## Error Handling Flow

```mermaid
graph TD
    START[User Request] --> VALIDATE{Valid Request?}

    VALIDATE -->|No| ERR1[400 Bad Request]
    VALIDATE -->|Yes| AUTH{Auth Success?}

    AUTH -->|No| ERR2[401 Unauthorized]
    AUTH -->|Yes| AGENT[Process with Agent]

    AGENT --> TOOL{Tool Execution}

    TOOL -->|MCP Error| ERR3[Handle MCP Error<br/>Return to LLM]
    TOOL -->|RAG Error| ERR4[Handle RAG Error<br/>Fallback response]
    TOOL -->|Success| LLM[LLM Response]

    LLM --> STREAM{Streaming OK?}

    STREAM -->|Network Error| ERR5[Stream Error to UI]
    STREAM -->|Success| DONE[Complete]

    ERR1 --> UI[Error to UI]
    ERR2 --> UI
    ERR3 --> LLM
    ERR4 --> LLM
    ERR5 --> UI

    style DONE fill:#10b981
    style ERR1 fill:#ef4444
    style ERR2 fill:#ef4444
    style ERR5 fill:#ef4444
```

## Performance Metrics

### Typical Request Breakdown

```mermaid
gantt
    title Request Processing Timeline (Typical Query)
    dateFormat X
    axisFormat %L ms

    section Client
    User Input       :0, 0
    Network (req)    :100
    Network (resp)   :2800, 200

    section API Server
    Request Parse    :100, 50
    Agent Init       :150, 200
    LLM Processing   :350, 2000
    Tool Execution   :2350, 400
    Response Stream  :2750, 250

    section External
    OpenAI API       :400, 1800
    Vector Search    :2400, 200
    MCP Server       :2400, 150
```

### Latency Breakdown

| Phase | Duration | Notes |
|-------|----------|-------|
| **Network (Request)** | 10-50ms | UI → API |
| **Agent Initialization** | 100-300ms | First request only, cached after |
| **LLM Reasoning** | 500-2000ms | Depends on complexity |
| **Tool Execution** | 200-500ms | RAG search or MCP call |
| **Streaming** | 50-200ms | Sending SSE chunks |
| **Network (Response)** | 10-50ms | API → UI |
| **Total** | 870-3100ms | ~1-3 seconds typical |

## State Management

### API Server State

```mermaid
stateDiagram-v2
    [*] --> Uninitialized

    Uninitialized --> Initializing: Startup event
    Initializing --> Ready: Agent created

    Ready --> Processing: Chat request
    Processing --> Streaming: Agent response
    Streaming --> Ready: Stream complete

    Processing --> Error: Exception
    Error --> Ready: Error handled

    Ready --> [*]: Shutdown
```

### UI State

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> Sending: User sends message
    Sending --> Streaming: SSE connection open
    Streaming --> Idle: Stream complete

    Sending --> Error: Network error
    Streaming --> Error: Stream error
    Error --> Idle: Error displayed
```

## Concurrency Model

### Multiple Users

```mermaid
graph TB
    subgraph "User 1"
        U1[User 1 Request]
    end

    subgraph "User 2"
        U2[User 2 Request]
    end

    subgraph "User 3"
        U3[User 3 Request]
    end

    U1 --> API[FastAPI Server<br/>Async/Await]
    U2 --> API
    U3 --> API

    API --> A1[Agent Instance 1]
    API --> A2[Agent Instance 2]
    API --> A3[Agent Instance 3]

    A1 --> LLM[OpenAI API<br/>Rate Limited: 2 req/s]
    A2 --> LLM
    A3 --> LLM

    LLM --> R1[Response 1]
    LLM --> R2[Response 2]
    LLM --> R3[Response 3]

    style API fill:#8b5cf6
    style LLM fill:#10b981
```

### Rate Limiting Protection

```python
# In src/core/config.py
RATE_LIMIT_REQUESTS_PER_SECOND = 2  # Conservative limit
RATE_LIMIT_CHECK_INTERVAL = 0.1     # Check every 100ms
RATE_LIMIT_MAX_BUCKET_SIZE = 2      # Burst capacity

# In src/core/agent.py
rate_limiter = InMemoryRateLimiter(
    requests_per_second=RATE_LIMIT_REQUESTS_PER_SECOND,
    check_every_n_seconds=RATE_LIMIT_CHECK_INTERVAL,
    max_bucket_size=RATE_LIMIT_MAX_BUCKET_SIZE,
)
```

**Protection benefits:**
- ✅ Prevents API overspending
- ✅ Stays within OpenAI rate limits
- ✅ Queues requests automatically
- ✅ Configurable per environment

# MCP (Model Context Protocol) Integration Architecture

## MCP System Overview

```mermaid
graph TB
    subgraph "LangChain Agent"
        AGENT[LangChain Agent<br/>GPT-4o-mini]
        TOOLS[Available Tools]
    end

    subgraph "MCP Client"
        CLIENT[MultiServerMCPClient<br/>langchain-mcp-adapters]
        OAUTH[OAuth Client<br/>Token Management]
    end

    subgraph "MCP Servers"
        TICK[msi-ticketing<br/>Port 9000]
        ORG[msi-organizations<br/>Port 9001]
    end

    subgraph "Auth Infrastructure"
        IDP[Mock IDP<br/>Port 9400]
        JWT[JWT Verifier<br/>JWKS Endpoint]
    end

    subgraph "Data Sources"
        TICKDB[(ticket.db)]
        USERDB[(users.db)]
        ORGDB[(organizations.db)]
    end

    AGENT --> TOOLS
    TOOLS --> CLIENT
    CLIENT --> OAUTH
    OAUTH --> IDP
    IDP --> JWT
    CLIENT --> TICK
    CLIENT --> ORG
    TICK --> JWT
    ORG --> JWT
    TICK --> TICKDB
    ORG --> USERDB
    ORG --> ORGDB

    style AGENT fill:#10b981
    style CLIENT fill:#8b5cf6
    style TICK fill:#f59e0b
    style ORG fill:#f59e0b
    style IDP fill:#ec4899
```

## MCP Server Structure

### Ticketing MCP Server (`msi-ticketing`)

```mermaid
graph TD
    SERVER[FastMCP Server<br/>msi-ticketing]

    SERVER --> AUTH[RemoteAuthProvider<br/>JWT Verification]
    SERVER --> TOOLS[MCP Tools]

    AUTH --> VERIFY[JWTVerifier<br/>JWKS: http://127.0.0.1:9400/jwks]

    TOOLS --> T1[get_username_tool]
    TOOLS --> T2[get_user_roles_tool]
    TOOLS --> T3[get_organizations]
    TOOLS --> T4[create_ticket]
    TOOLS --> T5[get_my_tickets]
    TOOLS --> T6[get_all_tickets]
    TOOLS --> T7[update_ticket_status]

    T4 --> DB[(ticket.db)]
    T5 --> DB
    T6 --> DB
    T7 --> DB

    style SERVER fill:#f59e0b
    style AUTH fill:#ec4899
    style DB fill:#6366f1
```

### Organizations MCP Server (`msi-organizations`)

```mermaid
graph TD
    SERVER[FastMCP Server<br/>msi-organizations]

    SERVER --> AUTH[RemoteAuthProvider<br/>JWT Verification]
    SERVER --> TOOLS[MCP Tools]

    AUTH --> VERIFY[JWTVerifier<br/>JWKS: http://127.0.0.1:9400/jwks]

    TOOLS --> T1[get_organization_users]
    TOOLS --> T2[get_user_info]
    TOOLS --> T3[list_organizations]

    T1 --> USERDB[(users.db)]
    T1 --> ORGDB[(organizations.db)]
    T2 --> USERDB
    T3 --> ORGDB

    style SERVER fill:#f59e0b
    style AUTH fill:#ec4899
    style USERDB fill:#6366f1
    style ORGDB fill:#6366f1
```

## Tool Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant LLM as GPT-4o-mini
    participant Agent as LangChain Agent
    participant Client as MCP Client
    participant IDP as Mock IDP
    participant MCP as MCP Server
    participant DB as Database

    User->>Agent: "Create a ticket for login issue"
    activate Agent

    Agent->>LLM: System prompt + tools + user message
    activate LLM

    Note over LLM: Reasoning:<br/>"User wants to create ticket,<br/>I'll use create_ticket tool"

    LLM-->>Agent: Tool call: create_ticket(<br/>title="Login Issue",<br/>description="Cannot log in")
    deactivate LLM

    Agent->>Client: Execute create_ticket
    activate Client

    Note over Client: Check if token exists

    Client->>IDP: POST /token<br/>grant_type=client_credentials
    activate IDP
    IDP-->>Client: {access_token: "eyJ..."}
    deactivate IDP

    Client->>MCP: POST /create_ticket<br/>Authorization: Bearer eyJ...<br/>{title, description}
    activate MCP

    MCP->>MCP: Verify JWT signature<br/>Extract username from token

    MCP->>DB: INSERT INTO tickets<br/>VALUES (...)
    activate DB
    DB-->>MCP: Row inserted, ticket_id=123
    deactivate DB

    MCP-->>Client: {success: true,<br/>ticket_id: 123,<br/>message: "Ticket created"}
    deactivate MCP

    Client-->>Agent: Tool result:<br/>"Ticket #123 created"
    deactivate Client

    Agent->>LLM: Tool result + continue
    activate LLM
    LLM-->>Agent: "I've created ticket #123<br/>for your login issue."
    deactivate LLM

    Agent-->>User: Response
    deactivate Agent
```

## MCP Configuration in Agent

### Server Configuration

```python
# In src/core/agent.py
from langchain_mcp_adapters.client import MultiServerMCPClient
from fastmcp.client.auth import OAuth

mcp_client = MultiServerMCPClient({
    "ticketing": {
        "url": "http://127.0.0.1:9000",
        "transport": "http",
        "auth": OAuth(
            client_id="test_client",
            client_secret="test_secret",
            token_url="http://127.0.0.1:9400/token",
            scopes=[]
        )
    },
    "organizations": {
        "url": "http://127.0.0.1:9001",
        "transport": "http",
        "auth": OAuth(
            client_id="test_client",
            client_secret="test_secret",
            token_url="http://127.0.0.1:9400/token",
            scopes=[]
        )
    }
})

# Get all MCP tools
mcp_tools = await mcp_client.get_tools()
```

## Tool Metadata Structure

### Example: create_ticket Tool

```json
{
  "name": "create_ticket",
  "description": "Description: Submits a ticket describing user issues.\nUse case: Use this tool to submit a ticket for review on behalf of the user.\nPermissable roles: Any roles.\nArguments: title (required, string), description (required, string).\nReturns: A string conveying the success of the ticket creation.",
  "parameters": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "description": "The ticket title"
      },
      "description": {
        "type": "string",
        "description": "Detailed description of the issue"
      }
    },
    "required": ["title", "description"]
  }
}
```

## Security Model

### Authentication Layers

```mermaid
graph TD
    REQUEST[MCP Tool Request] --> CHECK1{Valid JWT?}

    CHECK1 -->|No| REJECT1[401 Unauthorized]
    CHECK1 -->|Yes| CHECK2{Valid Signature?}

    CHECK2 -->|No| REJECT2[401 Invalid Signature]
    CHECK2 -->|Yes| CHECK3{Audience Match?}

    CHECK3 -->|No| REJECT3[403 Invalid Audience]
    CHECK3 -->|Yes| CHECK4{Token Expired?}

    CHECK4 -->|Yes| REJECT4[401 Token Expired]
    CHECK4 -->|No| CHECK5{Has Required Role?}

    CHECK5 -->|No| REJECT5[403 Insufficient Permissions]
    CHECK5 -->|Yes| ALLOW[Execute Tool]

    ALLOW --> AUDIT[Audit Log:<br/>username, action, timestamp]
    AUDIT --> RESULT[Return Result]

    style ALLOW fill:#10b981
    style REJECT1 fill:#ef4444
    style REJECT2 fill:#ef4444
    style REJECT3 fill:#ef4444
    style REJECT4 fill:#ef4444
    style REJECT5 fill:#ef4444
```

### Token Validation Steps

1. **JWT Presence**: Check Authorization header
2. **Signature Verification**: Validate using JWKS public keys
3. **Audience Check**: Ensure token intended for this server
4. **Expiration Check**: Verify token hasn't expired
5. **Role Verification**: Check user has required role for operation

## Tool Categories

### User Context Tools (Both Servers)

| Tool | Server | Purpose | Auth Required |
|------|--------|---------|---------------|
| `get_username_tool` | Both | Get current user's username | Yes |
| `get_user_roles_tool` | Ticketing | Get current user's roles | Yes |
| `get_organizations` | Ticketing | Get current user's orgs | Yes |

### Ticketing Tools

| Tool | Purpose | Roles | Database |
|------|---------|-------|----------|
| `create_ticket` | Create new ticket | Any | ticket.db |
| `get_my_tickets` | Get user's own tickets | Any | ticket.db |
| `get_all_tickets` | Get all tickets | Admin | ticket.db |
| `update_ticket_status` | Change ticket status | Admin | ticket.db |

### Organization Tools

| Tool | Purpose | Roles | Database |
|------|---------|-------|----------|
| `get_organization_users` | List users in org | Any | users.db + organizations.db |
| `get_user_info` | Get user details | Any | users.db |
| `list_organizations` | List all organizations | Any | organizations.db |

## Adding New MCP Servers

### Directory Structure Pattern

```
src/mcp/
├── ticketing/
│   ├── __init__.py
│   └── server.py
├── organizations/
│   ├── __init__.py
│   └── server.py
└── new_server/           # ← New server
    ├── __init__.py
    └── server.py
```

### Server Template

```python
"""
MCP server for [purpose]

Run (from project root):
uv run python -m src.mcp.new_server.server
"""

import pathlib
from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from pydantic import AnyHttpUrl

from src.auth.utils import check_roles, get_username

SERVER_URL = "http://127.0.0.1:9002"  # Next available port
ISSUER_URL = "http://127.0.0.1:9400"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent

# JWT Token Verifier
VERIFIER = JWTVerifier(
    jwks_uri = f"{ISSUER_URL}/jwks",
    issuer = ISSUER_URL,
    audience = SERVER_URL
)

# Create RemoteAuthProvider
AUTH = RemoteAuthProvider(
    token_verifier = VERIFIER,
    authorization_servers = [AnyHttpUrl(ISSUER_URL)],
    base_url = AnyHttpUrl(SERVER_URL),
)

# Create FastMCP server instance
mcp = FastMCP(
    name = "msi-new-server",
    auth = AUTH
)

@mcp.tool()
async def example_tool(param: str) -> str:
    """Tool description for LLM."""
    check_roles(["admin"])  # Optional role check
    username = get_username()
    # ... tool logic
    return f"Result for {username}"
```

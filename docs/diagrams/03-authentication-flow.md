# Authentication Flow Architecture

## OAuth 2.0 / JWT Authentication Flow

```mermaid
sequenceDiagram
    participant UI as Angular UI
    participant API as FastAPI Server
    participant IDP as Mock IDP<br/>(port 9400)
    participant MCP as MCP Server<br/>(Ticketing/Org)

    Note over UI,MCP: 1. Initial Request Flow

    UI->>API: POST /api/chat/stream<br/>{messages: [...]}
    activate API

    Note over API: Agent initialization needed

    API->>IDP: POST /token<br/>grant_type=client_credentials<br/>audience=http://127.0.0.1:9000
    activate IDP

    Note over IDP: Generate JWT with claims:<br/>- sub: "test_client"<br/>- roles: ["admin"]<br/>- organizations: ["msi"]<br/>- aud: [9000, 9001]<br/>- exp: 600s

    IDP-->>API: 200 OK<br/>{access_token: "eyJ..."}
    deactivate IDP

    Note over API: Token stored for reuse

    API->>MCP: POST /mcp/tools<br/>Authorization: Bearer eyJ...
    activate MCP

    Note over MCP: 2. MCP Server JWT Verification

    MCP->>IDP: GET /jwks<br/>(Get public keys)
    activate IDP
    IDP-->>MCP: {keys: [...]}
    deactivate IDP

    Note over MCP: Verify JWT:<br/>✓ Signature valid<br/>✓ Audience matches<br/>✓ Not expired<br/>✓ Issuer correct

    MCP->>MCP: Extract user context:<br/>- username = "test_client"<br/>- roles = ["admin"]<br/>- organizations = ["msi"]

    MCP-->>API: 200 OK<br/>{tools: [...]}
    deactivate MCP

    Note over API: 3. LLM Agent Processing

    API->>API: LLM decides to call:<br/>create_ticket(title, desc)

    API->>MCP: POST /create_ticket<br/>Authorization: Bearer eyJ...<br/>{title, description}
    activate MCP

    Note over MCP: Access token claims:<br/>- username: "test_client"<br/>- roles: ["admin"]

    MCP->>MCP: Check roles for operation<br/>(admin can create tickets)

    MCP->>MCP: Execute tool:<br/>INSERT INTO tickets<br/>VALUES (id, title, desc,<br/>        "test_client", ...)

    MCP-->>API: {success: true, ticket_id: 123}
    deactivate MCP

    API-->>UI: SSE Stream:<br/>data: {content: "Ticket created..."}
    deactivate API
```

## JWT Token Structure

### Token Claims
```json
{
  "sub": "test_client",
  "aud": [
    "http://127.0.0.1:9000",
    "http://127.0.0.1:9001"
  ],
  "iss": "http://127.0.0.1:9400",
  "exp": 1234567890,
  "iat": 1234567290,
  "roles": ["admin"],
  "organizations": ["msi", "eng"]
}
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **sub** | Subject (client/user identifier) |
| **aud** | Audience (which MCP servers can accept this token) |
| **iss** | Issuer (Mock IDP URL) |
| **exp** | Expiration time (10 minutes) |
| **iat** | Issued at time |
| **roles** | User roles for authorization |
| **organizations** | User's organization memberships |

## Multi-Audience Strategy

The JWT includes **multiple audiences** to allow one token for all MCP servers:

```python
# Mock IDP issues token with both MCP server URLs
"aud": [
    "http://127.0.0.1:9000",  # Ticketing MCP
    "http://127.0.0.1:9001"   # Organizations MCP
]
```

This enables **Single Sign-On (SSO)** across all MCP servers with one authentication flow.

## Role-Based Access Control (RBAC)

### Authorization Flow

```mermaid
graph TD
    START[MCP Tool Call] --> EXTRACT[Extract JWT Claims]
    EXTRACT --> CHECK{Check Roles}

    CHECK -->|Has Required Role| ALLOW[Execute Tool]
    CHECK -->|Missing Role| DENY[Return 403 Forbidden]

    ALLOW --> LOG[Log Action with Username]
    LOG --> RESULT[Return Result]

    DENY --> ERROR[Return Error Message]

    style ALLOW fill:#10b981
    style DENY fill:#ef4444
```

### Role Hierarchy

| Role | Permissions |
|------|-------------|
| **admin** | Full access to all operations |
| **user** | Read-only access, can create tickets |
| **viewer** | Read-only access only |

### Implementation

```python
from src.auth.utils import check_roles

@mcp.tool()
async def create_ticket(title: str, description: str):
    # Only admins and users can create tickets
    check_roles(["admin", "user"])

    username = get_username()  # From JWT
    # ... create ticket logic
```

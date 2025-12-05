# MSI AI Assistant - Architecture Diagrams

This directory contains comprehensive architecture diagrams for the MSI AI Assistant system using Mermaid syntax.

## Diagram Index

### 1. [System Overview](./01-system-overview.md)
High-level architecture showing all system components, ports, and data flow between client, API, authentication, MCP servers, LLM, and data layers.

**Key Topics:**
- Component ports and protocols
- Data flow between tiers
- External service integrations

### 2. [Directory Structure](./02-directory-structure.md)
Detailed breakdown of the modular codebase organization following domain-driven design principles.

**Key Topics:**
- Project folder hierarchy
- Module responsibilities
- Import path conventions

### 3. [Authentication Flow](./03-authentication-flow.md)
Complete OAuth 2.0 / JWT authentication architecture with multi-audience tokens for Single Sign-On across MCP servers.

**Key Topics:**
- JWT token structure and claims
- Multi-audience SSO strategy
- Role-Based Access Control (RBAC)
- Token verification sequence

### 4. [RAG Architecture](./04-rag-architecture.md)
Retrieval-Augmented Generation system design including document processing, embedding, vector search, and LLM integration.

**Key Topics:**
- Document chunking strategy
- Vector embedding pipeline
- Similarity search mechanics
- RAG agent registry pattern
- Performance characteristics

### 5. [MCP Integration](./05-mcp-integration.md)
Model Context Protocol implementation showing how MCP servers integrate with the LangChain agent.

**Key Topics:**
- MCP server structure
- Tool execution flow
- Security layers
- Adding new MCP servers
- Tool categories

### 6. [Request Flow](./06-request-flow.md)
End-to-end request processing from user input through UI, API, LLM, tools, and back to streaming response.

**Key Topics:**
- Complete sequence diagrams
- Request flow variations (RAG-only, MCP-only, hybrid)
- Streaming SSE protocol
- Error handling
- Performance metrics
- Concurrency model

### 7. [Deployment Architecture](./07-deployment-architecture.md)
Development and production deployment strategies including containerization, cloud options, and scaling.

**Key Topics:**
- Development environment setup
- Docker containerization
- Cloud deployment options (Heroku, AWS, GCP)
- Horizontal scaling
- Security hardening
- Monitoring & observability
- Backup & disaster recovery

## Viewing the Diagrams

### GitHub
All diagrams use Mermaid syntax which renders automatically in GitHub's markdown viewer.

### VS Code
Install the "Markdown Preview Mermaid Support" extension:
```bash
code --install-extension bierner.markdown-mermaid
```

### Command Line
Use the Mermaid CLI to generate PNGs:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i 01-system-overview.md -o output.png
```

### Online
Copy the Mermaid code blocks and paste into:
- [Mermaid Live Editor](https://mermaid.live/)
- [GitHub Gists](https://gist.github.com/)

## Architecture Principles

The system architecture follows these key principles:

### 1. **Modularity**
- Clear separation of concerns (core, api, auth, mcp, rag)
- Each module has single responsibility
- Easy to add new MCP servers or RAG agents

### 2. **Security**
- JWT-based authentication throughout
- Role-based access control
- Multi-audience tokens for SSO
- Secure credential management

### 3. **Scalability**
- Async/await for concurrent requests
- Stateless API design
- Horizontal scaling ready
- Rate limiting protection

### 4. **Maintainability**
- Consistent naming conventions
- Clear import paths (`from src.module`)
- Comprehensive documentation
- Type hints throughout

### 5. **Performance**
- Vector store persistence (no re-indexing)
- OpenAI response streaming
- Client-side rate limiting
- Efficient chunking strategy

## Quick Reference

### System Ports

| Component | Port | Protocol |
|-----------|------|----------|
| Angular UI | 4200 | HTTP |
| FastAPI Server | 8000 | HTTP |
| Mock IDP | 9400 | HTTP |
| Ticketing MCP | 9000 | HTTP |
| Organizations MCP | 9001 | HTTP |

### Key Technologies

- **Frontend**: Angular 19 (standalone components, signals)
- **Backend**: FastAPI (async, streaming)
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector DB**: Chroma
- **Auth**: JWT with JWKS
- **MCP**: FastMCP with RemoteAuthProvider
- **Agent Framework**: LangChain

### Directory Structure Summary

```
msi-ai-assistant/
├── src/
│   ├── core/              # Agent, config, utils
│   ├── api/               # FastAPI server
│   ├── auth/              # Authentication logic
│   ├── mcp/               # MCP servers
│   │   ├── ticketing/
│   │   └── organizations/
│   ├── rag/               # RAG agents
│   │   └── agents/
│   └── main.py            # CLI entry point
├── data/
│   ├── databases/         # SQLite DBs
│   ├── vector_stores/     # Chroma embeddings
│   └── documents/         # Source docs
├── ai-assistant-ui/       # Angular frontend
├── docs/
│   └── diagrams/          # This directory
└── scripts/               # Helper scripts
```

## Contributing

When adding new features, please update relevant diagrams:

1. **New MCP Server** → Update `05-mcp-integration.md`
2. **New RAG Agent** → Update `04-rag-architecture.md`
3. **API Changes** → Update `06-request-flow.md`
4. **Auth Changes** → Update `03-authentication-flow.md`
5. **Directory Changes** → Update `02-directory-structure.md`

## Related Documentation

- [Main README](../../README.md) - Project overview and setup
- [PORT_CONFIG.md](../PORT_CONFIG.md) - Port configuration reference
- [SSO_IMPLEMENTATION.md](../../SSO_IMPLEMENTATION.md) - SSO implementation details
- [REFACTORING_SUMMARY.md](../../REFACTORING_SUMMARY.md) - Code refactoring history
- [REORGANIZATION_PLAN.md](../../REORGANIZATION_PLAN.md) - Original reorganization plan

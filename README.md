# MSI AI Assistant

AI-powered Assistant for Motorola Solutions using Model Context Protocol (MCP) and LangChain (RAG).

---

> **📚 UTDesign Capstone Project**  
> This project is developed as part of the UTDesign Capstone program.  
> **Sponsor:** Motorola Solutions  
> **Note:** This is a student project and not an official Motorola Solutions product.

---

## 🚀 Quick Start

**New to the project?** Follow our comprehensive setup guide: **[GETTING_STARTED.md](docs/GETTING_STARTED.md)**

**Already set up?** Run the application:
```bash
# Windows:
.\scripts\start.bat

# macOS/Linux:
uv run honcho start
```

The Angular UI will automatically open in your browser at `http://localhost:4200`

---

## 📋 Project Overview

Agentic RAG system with multi-transport MCP integration:
- **Agentic RAG**: LLM decides when to search documentation (tool-based, not middleware)
- **Multi-Transport MCP**: Supports stdio (local) and HTTP (remote) MCP servers
- **Vector Search**: Chroma-based similarity search with persistent storage
- **Rate Protection**: Client-side rate limiting + tool call limits
- **Multi-Model**: GPT-4o-mini (default), GPT-4o, Claude 3.5 Sonnet, Gemini 2.0 Flash

**Status:** Core agentic RAG + MCP integration complete

---

## ⚙️ Technology Stack

- **Language**: Python 3.12.10
- **Package Manager**: uv
- **LLM**: GPT-4o-mini (default), Claude 3.5 Sonnet, GPT-4o, Gemini 2.0 Flash
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Store**: Chroma (persistent)
- **Framework**: LangChain + LangChain MCP Adapters
- **MCP**: FastMCP 2.13.2 (stdio + HTTP transport)
- **Observability**: LangSmith (optional)
- **RAG Architecture**: Agentic (tool-based)

---

## 📁 Project Structure

```
msi-ai-assistant/
├── src/                    # Source code
│   ├── api/                # FastAPI REST API
│   ├── auth/               # OAuth/JWT authentication (Mock IDP)
│   ├── core/               # Core agent logic and configuration
│   ├── mcp/                # MCP servers (ticketing, organizations)
│   ├── models/             # Pydantic data models
│   └── rag/                # RAG implementation
├── ai-assistant-ui/        # Angular web interface
├── scripts/                # Utility scripts (start.bat, stop.bat)
├── docs/                   # Documentation
├── data/                   # Databases and documents
├── chroma_langchain_db/    # Vector store (not in git)
├── logs/                   # Auto-archived logs (not in git)
├── Procfile                # Honcho process manager config
├── pyproject.toml          # Python dependencies
└── README.md               # This file
```

---

## 🎯 Key Features

- ✅ **Agentic RAG**: Tool-based retrieval (only searches when needed)
- ✅ **Multi-Transport MCP**: stdio (local) + HTTP (remote) servers
- ✅ **Rate Protection**: 2 RPS limit + 15 tool call cap
- ✅ **Document Chunking**: 1500 chars, 300 overlap
- ✅ **Persistent Vector Store**: Chroma with local storage
- ✅ **Multi-Model Support**: GPT-4o-mini, Claude, Gemini

---

## 📚 Requirements

- **Python 3.12.10** (NOT 3.13.x)
- **At least one LLM API key**: OpenAI (recommended), Anthropic, or Google
- **Budget limits configured** (see [RATE_LIMITING_GUIDE.md](docs/RATE_LIMITING_GUIDE.md))
- **LangSmith API Key** (optional)

**Setup:** [GETTING_STARTED.md](docs/GETTING_STARTED.md)

---

## 🧪 Usage

### Option 1: Run All Services (Recommended - Single Terminal)

**Windows (recommended):**
```bash
# From project root:
.\scripts\start.bat

# Or from scripts directory:
cd scripts
.\start.bat
```

**macOS/Linux:**
```bash
# From project root - start all services with one command
# Note: Honcho automatically loads .env file from project root
uv run honcho start

# To use a different env file:
uv run honcho start -e .env.production
```

**Services started:**
- Mock IDP (port 9400) - OAuth/JWT authentication
- Ticketing MCP (port 9000) - Ticketing tools via MCP
- Organizations MCP (port 9001) - Organization tools via MCP
- FastAPI Backend (port 8080) - REST API
- Angular UI (port 4200) - Web interface (auto-opens in browser)

**Note:**
- The Angular UI includes a health check that waits for the backend to be ready before displaying the interface
- On Windows, you may see Unicode encoding warnings in the console, but all services will start successfully
- Using `scripts\start.bat` handles encoding properly and changes to the correct directory

**To stop all services:**
```bash
# Windows:
.\scripts\stop.bat

# macOS/Linux:
Ctrl+C in the terminal running Honcho
```

### Option 2: Run Services Individually (5 Terminals)
```bash
# Terminal 1: Mock Identity Provider
uv run python -m uvicorn src.auth.mock_idp:app --host 127.0.0.1 --port 9400

# Terminal 2: Ticketing MCP Server
uv run python -m src.mcp.ticketing.server

# Terminal 3: Organizations MCP Server
uv run python -m src.mcp.organizations.server

# Terminal 4: FastAPI Backend
uv run uvicorn src.api.server:app --host 0.0.0.0 --port 8080

# Terminal 5: Angular UI
cd ai-assistant-ui && npm start
```

### Option 3: CLI Testing (No UI)
```bash
# Run CLI test script (requires MCP servers running)
uv run src/main.py
```

### Example Queries
- **RAG**: "How do I add a new user?" → Searches MSI docs
- **Ticketing**: "What is the most common ticket subject?" → Uses ticketing MCP
- **Organizations**: "List all organizations" → Uses organizations MCP
- **Multi-step**: Complex queries that chain multiple tools

---

## 🛠️ Development

```bash
# Install dependencies
uv sync

# Pin Python version
uv python pin 3.12.10

# Run with specific .env
uv run --env-file .env src/main.py
```

---

## 🤝 Contributing

### For Team Members
1. Follow [GETTING_STARTED.md](docs/GETTING_STARTED.md)
2. Read [RATE_LIMITING_GUIDE.md](docs/RATE_LIMITING_GUIDE.md) and set budget limits
3. Create your own API keys (never share)
4. Use LangSmith project: `msi-ai-assistant`

---

## 🗺️ Roadmap

### ✅ Completed
- Agentic RAG (tool-based retrieval)
- Multi-transport MCP (stdio + HTTP)
- Rate limiting + tool call limits
- Multi-model support (OpenAI, Anthropic, Google)
- Persistent Chroma vector store

### ✅ Recently Added
- FastAPI REST API with streaming responses
- Angular web UI with SSE support
- Health check and backend readiness detection
- Process manager (Honcho) for single-command startup

### 📋 Planned
- Unified authentication (Mock IDP → Angular + FastAPI)
- Web scraping for docs.motorolasolutions.com
- Production deployment configuration

---

## 📖 Documentation

- **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Setup guide
- **[RATE_LIMITING_GUIDE.md](docs/RATE_LIMITING_GUIDE.md)** - Cost protection
- **[ANGULAR_UI_GUIDE.md](docs/ANGULAR_UI_GUIDE.md)** - Angular UI setup and development
- **[SSO_IMPLEMENTATION.md](docs/SSO_IMPLEMENTATION.md)** - OAuth/JWT authentication details
- **[PORT_CONFIG.md](docs/PORT_CONFIG.md)** - Port configuration and troubleshooting

---

## 📄 License

[Add license information]

---

**Built with ❤️ for Capstone Sponsor: Motorola Solutions-CPS**
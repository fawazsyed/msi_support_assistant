# MSI AI Assistant

AI-powered Assistant for Motorola Solutions using Model Context Protocol (MCP) and LangChain (RAG).

---

> **📚 UTDesign Capstone Project**  
> This project is developed as part of the UTDesign Capstone program.  
> **Sponsor:** Motorola Solutions  
> **Note:** This is a student project and not an official Motorola Solutions product.

---

## 🚀 Quick Start

**New to the project?** Follow our comprehensive setup guide: **[GETTING_STARTED.md](GETTING_STARTED.md)**

**Already set up?** Run the application:
```bash
uv run src/main.py
```

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
├── src/
│   ├── main.py             # Agentic RAG with MCP tools
│   ├── mcp_server.py       # Math MCP server (stdio)
│   ├── weather_server.py   # Weather MCP server (HTTP)
│   └── utils.py            # Logging utilities
├── documents/              # Knowledge base (~90K tokens)
├── chroma_langchain_db/    # Vector store (not in git)
├── logs/                   # Auto-archived logs (not in git)
├── pyproject.toml          # Dependencies (FastMCP, LangChain, etc.)
├── .env.example            # API key template
├── GETTING_STARTED.md      # Setup guide
├── RATE_LIMITING_GUIDE.md  # Cost protection guide
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
- **Budget limits configured** (see [RATE_LIMITING_GUIDE.md](RATE_LIMITING_GUIDE.md))
- **LangSmith API Key** (optional)

**Setup:** [GETTING_STARTED.md](GETTING_STARTED.md)

---

## 🧪 Usage

### Start Weather Server (Terminal 1)
```bash
uv run python src/weather_server.py
```

### Run Agentic RAG (Terminal 2)
```bash
uv run src/main.py
```

### Example Queries
- **RAG**: "How do I add a new user?" → Searches MSI docs
- **Math**: "What is 5 + 3?" → Uses MCP math tool
- **Weather**: "What's the weather in NYC?" → Uses MCP weather tool
- **Multi-step**: "What's the magic number times 10?" → Chains MCP tools

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
1. Follow [GETTING_STARTED.md](GETTING_STARTED.md)
2. Read [RATE_LIMITING_GUIDE.md](RATE_LIMITING_GUIDE.md) and set budget limits
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

### 📋 Planned
- FastAPI REST endpoint
- Streaming responses
- Web scraping for docs.motorolasolutions.com
- Angular UI

---

## 📖 Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Setup guide
- **[RATE_LIMITING_GUIDE.md](RATE_LIMITING_GUIDE.md)** - Cost protection

---

## 📄 License

[Add license information]

---

**Built with ❤️ for Capstone Sponsor: Motorola Solutions-CPS**
# MSI AI Assistant

AI-powered documentation assistant for Motorola Solutions using LangChain RAG (Retrieval-Augmented Generation) following official tutorial patterns.

---

> **📚 UTDesign Capstone Project**  
> This project is developed as part of the UTDesign Capstone program.  
> **Sponsor:** Motorola Solutions  
> **Note:** This is a student project and not an official Motorola Solutions product.

---

## 🚀 Quick Start

### 1. Crawl Documentation
```bash
uv run python src/motorola_crawler.py
# Crawls Motorola VideoManager Admin Guide
# Output: data/motorola_docs.json
```

### 2. Build Search Index
```bash
uv run python src/prototype_indexer.py motorola_docs.json
# Creates vector database with document chunks
# Output: python_docs_index_prototype/
```

### 3. Ask Questions
```bash
uv run python src/rag_agent.py "How do I configure storage settings?"
# Streams responses with source citations
```

**New to the project?** See: **[GETTING_STARTED.md](GETTING_STARTED.md)**

---

## 📋 Project Overview

This project implements a production-ready RAG system for Motorola VideoManager documentation following the [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/).

### Key Features
- **📄 Smart Crawling**: Extracts clean content from Motorola docs with anchor-based section targeting
- **🔍 Semantic Search**: Vector similarity search with chunk-level retrieval (2000 chars, 500 overlap)
- **🤖 Agent-Based RAG**: LLM decides when to search, can perform multiple searches per query
- **📍 Precise Citations**: Cites specific pages with titles and URLs (not generic references)
- **⚡ Real-time Streaming**: See agent reasoning and tool calls as they happen

**Current Status:** Production-ready RAG pipeline with 10 sample pages from VideoManager Admin Guide

**Architecture**: Follows [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/) → See [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for details

---

## ⚙️ Technology Stack

### Core Framework
- **Language**: Python 3.12.10
- **Package Manager**: uv
- **Framework**: LangChain (following official RAG tutorial patterns)

### RAG Components
- **LLM**: OpenAI GPT-4o-mini (agent reasoning + answer generation)
- **Embeddings**: OpenAI text-embedding-3-small (semantic search)
- **Vector Store**: Chroma (persistent, local storage)
- **Text Splitting**: RecursiveCharacterTextSplitter (2000 chars, 500 overlap)
- **Retrieval**: Agent-based with `@tool` decorator (k=2 chunks per search)

### Data Pipeline
- **Web Crawler**: Crawl4AI (handles JS rendering, WAF protection)
- **Content Cleaning**: BeautifulSoup4 (removes navigation, filters, boilerplate)
- **Document Format**: JSON → LangChain Documents → Chunked Documents → Vector Store

### Observability (Optional)
- **LangSmith**: Trace agent reasoning, tool calls, retrieval quality

---

## 📁 Project Structure

```
msi-ai-assistant/
├── src/                              # Source code
│   ├── motorola_crawler.py          # Crawl4AI web scraper for Motorola docs
│   ├── prototype_indexer.py         # LangChain indexing pipeline (Load→Split→Store)
│   ├── rag_agent.py                 # Agent-based RAG with retrieval tool
│   └── utils.py                     # Logging and utility functions
├── data/                             # Crawled documents (not in git)
│   └── motorola_docs.json           # JSON output from crawler (10 pages)
├── python_docs_index_prototype/     # Chroma vector store (not in git)
│   ├── chroma.sqlite3               # Vector database
│   └── [embeddings]/                # Stored embeddings
├── logs/                             # Application logs (not in git)
│   └── archive/                     # Archived logs
├── dev_resources/                   # Development references
│   └── COMMIT_TEMPLATE.md           # Git commit template
├── pyproject.toml                   # Project dependencies (uv)
├── .env                             # API keys (not in git)
├── .env.example                     # Template for .env
├── GETTING_STARTED.md               # Complete setup guide
├── REFACTORING_SUMMARY.md           # LangChain tutorial compliance details
└── README.md                        # This file
```

---

## 🎯 Key Features

### Indexing Pipeline (LangChain Tutorial Pattern)
- ✅ **LOAD**: Convert crawled JSON to LangChain Documents
- ✅ **SPLIT**: RecursiveCharacterTextSplitter (2000 chars, 500 overlap, ~400 chunks)
- ✅ **STORE**: Chroma vector store with OpenAI embeddings (text-embedding-3-small)

### RAG Agent (Tool-Based Pattern)
- ✅ **Agent Reasoning**: LLM decides when to search (no unnecessary searches)
- ✅ **Retrieval Tool**: `@tool` decorator with `response_format="content_and_artifact"`
- ✅ **Multiple Searches**: Can execute iterative searches for complex queries
- ✅ **Streaming**: Real-time token streaming with `agent.stream()`

### Content Quality
- ✅ **Smart Crawling**: Crawl4AI handles JS rendering and WAF protection
- ✅ **Content Cleaning**: Removes site-wide navigation, filters, breadcrumbs (81% size reduction)
- ✅ **Anchor Extraction**: Targets specific sections (e.g., `#f7c77368` → "RFID Configuration")
- ✅ **Precise Citations**: Cites specific page titles with exact URLs

### Developer Experience
- ✅ **LangSmith Tracing**: Optional observability for debugging (tool calls, retrieval, latency)
- ✅ **Tutorial Compliance**: Follows official LangChain patterns (easy for team to understand)
- ✅ **Extensible**: Ready for memory, re-ranking, evaluation features

---

## 📚 Requirements

- **Python 3.12.10** (NOT 3.13.x - compatibility issues)
- **OpenAI API Key** (required for LLM and embeddings)
- **LangSmith API Key** (optional but recommended for observability)

**Full setup instructions:** [GETTING_STARTED.md](GETTING_STARTED.md)

---

## 🧪 Testing & Validation

### Current Dataset
- **Source**: Motorola VideoManager Admin Guide (docs.motorolasolutions.com)
- **Pages**: 10 (sampled from "What's New" section)
- **Content Types**: Full pages + anchor-based sections
- **Examples**: "Home", "Admin", "RFID Configuration", "Device Permissions"

### Indexing Results
```bash
$ uv run python src/prototype_indexer.py motorola_docs.json

[1/3] LOAD: Converting 10 documents...
      [+] Loaded 10 documents

[2/3] SPLIT: Chunking documents...
      chunk_size=2000, chunk_overlap=500
      [+] Split into 400 chunks

[3/3] STORE: Embedding and indexing chunks...
      [+] Indexed 400 chunks from 10 documents
```

### Sample Query Test
```bash
$ uv run python src/rag_agent.py "How do I configure storage settings?"

================================ Human Message =================================
How do I configure storage settings?

================================== Ai Message ==================================
Tool Calls:
  retrieve_context (call_xyz...)
  Args:
    query: storage configuration VideoManager

================================= Tool Message =================================
[Document 1]
Title: Admin
URL: https://docs.motorolasolutions.com/bundle/89303/page/4a801fc3.html
Content: To configure storage settings in VideoManager...

================================== Ai Message ==================================
To configure storage settings in VideoManager:
1. Navigate to the Admin tab
2. Select the Storage section
[... detailed steps ...]

Sources:
- Admin: https://docs.motorolasolutions.com/bundle/89303/page/4a801fc3.html
- System: https://docs.motorolasolutions.com/bundle/89303/page/4a801fc3.html#71f28176
```

### Content Quality Metrics
- **Before Cleaning**: "Home" page = 24,944 chars (mostly boilerplate)
- **After Cleaning**: "Home" page = 4,727 chars (81% reduction)
- **Result**: Focused, unique content per page with specific citations

---

## 🛠️ Development

### Complete Pipeline
```bash
# 1. Crawl documentation
uv run python src/motorola_crawler.py

# 2. Build search index  
uv run python src/prototype_indexer.py motorola_docs.json

# 3. Ask questions
uv run python src/rag_agent.py "your question here"

# 4. Interactive search testing (optional)
uv run python src/prototype_indexer.py motorola_docs.json
# Then select 'y' for interactive search
```

### Project Management
```bash
# Install/update dependencies
uv sync

# Pin Python version
uv python pin 3.12.10

# Add new dependency
uv add <package-name>

# Run with specific environment
uv run --env-file .env python src/rag_agent.py "question"
```

### Environment Variables
Required in `.env` file:
```bash
OPENAI_API_KEY=sk-...           # Required for LLM and embeddings
LANGSMITH_API_KEY=lsv2_pt_...   # Optional for tracing
LANGSMITH_TRACING=true          # Optional
```

---

## 🤝 Contributing

This is a team project for Motorola Solutions support assistant development.

### For Team Members
1. Read [GETTING_STARTED.md](GETTING_STARTED.md) for complete setup
2. Join the LangSmith workspace (ask team lead for invitation)
3. Create your own API keys (OpenAI + LangSmith)
4. Use project name: `msi-ai-assistant` for shared traces

### Best Practices
- Use LangSmith to track your experiments
- Add descriptive metadata to traces
- Document findings in test files
- Keep `.env` file private (never commit)

---

## 🗺️ Roadmap

### ✅ Completed (Phase 1: Core RAG)
- ✅ LangChain RAG tutorial compliance
- ✅ Agent-based retrieval with tool pattern (`@tool` decorator)
- ✅ Document chunking (RecursiveCharacterTextSplitter: 2000 chars, 500 overlap)
- ✅ Persistent vector store (Chroma with text-embedding-3-small)
- ✅ Motorola docs crawler (Crawl4AI with content cleaning)
- ✅ Anchor-based section extraction (e.g., `#f7c77368`)
- ✅ Precise source citations (specific page titles + URLs)
- ✅ Streaming responses (`agent.stream()`)
- ✅ LangSmith tracing integration (optional observability)

### 🚧 In Progress (Phase 2: Enhancement)
- 🔄 Expand dataset (crawl all 24 pages from "What's New")
- 🔄 Optimize chunk size (experiment with 1000/1500/2000)
- 🔄 Add evaluation metrics (citation accuracy, answer quality)

### 📋 Planned (Phase 3: Advanced Features)
- 📅 Conversational memory (multi-turn chat with history)
- 📅 Re-ranking (ContextualCompressionRetriever for relevance)
- 📅 MMR retrieval (diversity in search results)
- 📅 Hybrid search (semantic + keyword combination)
- 📅 Interactive web interface (Streamlit/Gradio chat UI)
- 📅 MCP (Model Context Protocol) integration
- 📅 Real-time document updates (incremental indexing)

---

## 📖 Documentation

- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Complete setup guide for new developers
- **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - LangChain tutorial compliance details
- **[LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)** - Official tutorial we follow
- **dev_resources/COMMIT_TEMPLATE.md** - Git commit message template

---

## 📄 License

[Add license information]

---

**Built with ❤️ for Capstone Sponsor: Motorola Solutions-CPS**
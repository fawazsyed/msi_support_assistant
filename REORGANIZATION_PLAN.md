# MSI AI Assistant - Production-Level Reorganization Plan

**Date:** 2025-12-05
**Purpose:** Organize project structure for scalability with multiple MCP servers and custom RAG agents
**Status:** PLANNING

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Proposed Directory Structure](#proposed-directory-structure)
3. [Migration Steps](#migration-steps)
4. [File-by-File Mapping](#file-by-file-mapping)
5. [Benefits](#benefits)
6. [Implementation Checklist](#implementation-checklist)

---

## Current State Analysis

### Current Structure (Flat)
```
msi-ai-assistant/
├── src/                          # All Python code in one directory
│   ├── agent_setup.py           # Agent initialization
│   ├── api_server.py            # FastAPI server
│   ├── auth_utils.py            # Auth helpers
│   ├── config.py                # Configuration
│   ├── main.py                  # CLI entry point
│   ├── mock_idp.py              # Mock identity provider
│   ├── organizations_mcp.py     # MCP server
│   ├── rag_agents.py            # RAG agent framework
│   ├── ticketing_mcp.py         # MCP server
│   ├── token_store.py           # Token management
│   ├── utils.py                 # Utilities
│   ├── *.db                     # SQLite databases (mixed with code!)
│   └── __pycache__/
├── ai-assistant-ui/             # Angular frontend
├── documents/                   # RAG source documents
├── chroma_langchain_db*/        # Vector databases (2 instances)
├── logs/                        # Application logs
├── dev_resources/               # Developer documentation
├── research/                    # Research notes
├── tests/                       # Tests (if any)
├── *.md                         # Documentation files (10+ in root)
└── *.txt                        # Misc text files in root
```

### Problems with Current Structure

1. **Flat src/ directory** - All Python files in one place
2. **Mixed concerns** - DB files, code, cache all together
3. **No clear separation** - MCP servers vs RAG agents vs core logic
4. **Hard to scale** - Adding new MCP servers clutters src/
5. **Documentation scattered** - MD files in root + dev_resources
6. **Data organization** - Vector DBs, SQLite DBs, documents not organized

---

## Proposed Directory Structure

### Production-Ready Structure
```
msi-ai-assistant/
│
├── README.md                    # Main project README
├── pyproject.toml               # Python dependencies
├── .env.example                 # Environment template
├── .gitignore
├── CLAUDE.md                    # Claude Code instructions
│
├── docs/                        # 📚 All documentation
│   ├── README.md               # Documentation index
│   ├── getting-started/
│   │   ├── GETTING_STARTED.md
│   │   ├── ANGULAR_UI_GUIDE.md
│   │   └── installation.md
│   ├── development/
│   │   ├── COMMIT.md
│   │   ├── RATE_LIMITING_GUIDE.md
│   │   ├── SSO_IMPLEMENTATION.md
│   │   └── dev_resources/      # Developer tools & references
│   │       ├── llm-friendly-docs.md
│   │       ├── COMMIT_TEMPLATE.md
│   │       ├── COPILOT_MCP_SETUP.md
│   │       └── uv_commands.txt
│   ├── architecture/
│   │   ├── system-overview.md
│   │   ├── mcp-servers.md
│   │   └── rag-agents.md
│   └── brand/
│       └── brandmessaging.md
│
├── src/                         # 🐍 All Python source code
│   ├── __init__.py
│   │
│   ├── core/                    # Core application logic
│   │   ├── __init__.py
│   │   ├── agent.py            # Agent setup (from agent_setup.py)
│   │   ├── config.py           # Configuration management
│   │   └── utils.py            # Shared utilities
│   │
│   ├── api/                     # API layer
│   │   ├── __init__.py
│   │   ├── server.py           # FastAPI app (from api_server.py)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py        # Chat endpoints
│   │   │   └── health.py      # Health check endpoints
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── auth.py        # Auth middleware
│   │
│   ├── auth/                    # Authentication & Authorization
│   │   ├── __init__.py
│   │   ├── utils.py            # Auth utilities (from auth_utils.py)
│   │   ├── token_store.py      # Token management
│   │   └── mock_idp.py         # Mock identity provider
│   │
│   ├── mcp/                     # 🔧 MCP Servers
│   │   ├── __init__.py
│   │   ├── base.py             # Base MCP server class (if needed)
│   │   ├── ticketing/
│   │   │   ├── __init__.py
│   │   │   ├── server.py      # Ticketing MCP (from ticketing_mcp.py)
│   │   │   ├── models.py      # Data models
│   │   │   └── database.py    # DB operations
│   │   ├── organizations/
│   │   │   ├── __init__.py
│   │   │   ├── server.py      # Organizations MCP (from organizations_mcp.py)
│   │   │   ├── models.py
│   │   │   └── database.py
│   │   │
│   │   └── [future_mcp_servers]/  # Easy to add new MCP servers
│   │       ├── __init__.py
│   │       ├── server.py
│   │       ├── models.py
│   │       └── database.py
│   │
│   ├── rag/                     # 🧠 RAG Agents
│   │   ├── __init__.py
│   │   ├── base.py             # BaseRAGAgent (from rag_agents.py)
│   │   ├── registry.py         # RAGAgentRegistry
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── msi_docs.py    # MSIDocsRAGAgent
│   │   │   └── [custom_agents].py  # Future custom RAG agents
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   └── openai.py      # Embedding configuration
│   │   └── chunking/
│   │       ├── __init__.py
│   │       └── strategies.py  # Chunking strategies
│   │
│   ├── models/                  # Shared data models
│   │   ├── __init__.py
│   │   ├── message.py
│   │   ├── conversation.py
│   │   └── user.py
│   │
│   ├── cli/                     # CLI interface
│   │   ├── __init__.py
│   │   └── main.py            # CLI entry point (from main.py)
│   │
│   └── scripts/                 # Utility scripts
│       ├── __init__.py
│       ├── migrate_db.py
│       └── seed_data.py
│
├── data/                        # 💾 All data files (excluded from git)
│   ├── .gitkeep
│   ├── databases/              # SQLite databases
│   │   ├── organizations.db
│   │   ├── ticket.db
│   │   └── users.db
│   ├── vector_stores/          # Vector databases
│   │   ├── msi_docs/          # Chroma DB for MSI docs
│   │   └── [other_collections]/
│   ├── documents/              # Source documents for RAG
│   │   ├── msi_docs/
│   │   │   ├── video_manager_admin_guide.txt
│   │   │   └── *.txt
│   │   ├── brand/
│   │   │   └── brandmessaging.md
│   │   └── [other_sources]/
│   └── uploads/                # User-uploaded files (if needed)
│
├── logs/                        # 📋 Application logs
│   ├── .gitkeep
│   ├── archive/                # Archived logs
│   └── *.log
│
├── tests/                       # 🧪 Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest configuration
│   ├── unit/
│   │   ├── test_auth.py
│   │   ├── test_rag_agents.py
│   │   └── test_mcp/
│   │       ├── test_ticketing.py
│   │       └── test_organizations.py
│   ├── integration/
│   │   ├── test_api.py
│   │   └── test_agent.py
│   └── fixtures/
│       └── sample_data.py
│
├── ai-assistant-ui/             # 🎨 Angular frontend (unchanged)
│   └── [existing structure]
│
├── .venv/                       # Virtual environment (git ignored)
├── .vscode/                     # VS Code settings
├── research/                    # 📝 Research & planning notes
│   └── [existing files]
│
└── scripts/                     # 🛠️ Project-level scripts
    ├── setup.sh                # Project setup script
    ├── run_dev.sh              # Development server
    └── deploy.sh               # Deployment script
```

---

## Migration Steps

### Phase 1: Create New Directory Structure

**Step 1.1: Create directories**
```bash
# Documentation
mkdir -p docs/{getting-started,development/dev_resources,architecture,brand}

# Source code
mkdir -p src/{core,api/routes,api/middleware,auth,mcp,rag,models,cli,scripts}
mkdir -p src/mcp/{ticketing,organizations}
mkdir -p src/rag/{agents,embeddings,chunking}

# Data
mkdir -p data/{databases,vector_stores,documents,uploads}
mkdir -p data/documents/{msi_docs,brand}
mkdir -p data/vector_stores/msi_docs

# Tests
mkdir -p tests/{unit/test_mcp,integration,fixtures}

# Scripts
mkdir -p scripts
```

**Step 1.2: Create __init__.py files**
```bash
find src -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

---

### Phase 2: Move Documentation

**Step 2.1: Move docs to docs/ directory**
```bash
# Getting started
mv GETTING_STARTED.md docs/getting-started/
mv ANGULAR_UI_GUIDE.md docs/getting-started/

# Development
mv COMMIT.md docs/development/
mv RATE_LIMITING_GUIDE.md docs/development/
mv SSO_IMPLEMENTATION.md docs/development/
mv REFACTORING_SUMMARY.md docs/development/
mv dev_resources/* docs/development/dev_resources/

# Brand
mv brandmessaging.md docs/brand/

# Architecture (create new)
# Will document MCP servers and RAG agents
```

**Step 2.2: Clean up root**
```bash
# Remove redundant files
rm brandmessaging.txt  # We have .md version
rm commands.txt        # Move content to appropriate doc
rm futureconsiderations.txt  # Move to docs/development/
```

---

### Phase 3: Reorganize Source Code

**Step 3.1: Core modules**
```bash
mv src/agent_setup.py src/core/agent.py
mv src/config.py src/core/config.py
mv src/utils.py src/core/utils.py
```

**Step 3.2: API layer**
```bash
mv src/api_server.py src/api/server.py
# Split routes into separate files (manual refactoring)
```

**Step 3.3: Authentication**
```bash
mv src/auth_utils.py src/auth/utils.py
mv src/token_store.py src/auth/token_store.py
mv src/mock_idp.py src/auth/mock_idp.py
```

**Step 3.4: MCP Servers**
```bash
# Ticketing MCP
mv src/ticketing_mcp.py src/mcp/ticketing/server.py

# Organizations MCP
mv src/organizations_mcp.py src/mcp/organizations/server.py
```

**Step 3.5: RAG Agents**
```bash
# Split rag_agents.py into multiple files
# BaseRAGAgent -> src/rag/base.py
# RAGAgentRegistry -> src/rag/registry.py
# MSIDocsRAGAgent -> src/rag/agents/msi_docs.py
```

**Step 3.6: CLI**
```bash
mv src/main.py src/cli/main.py
```

---

### Phase 4: Reorganize Data

**Step 4.1: Move databases**
```bash
mv src/organizations.db data/databases/
mv src/ticket.db data/databases/
mv src/users.db data/databases/
```

**Step 4.2: Move documents**
```bash
mv documents/* data/documents/msi_docs/
```

**Step 4.3: Move vector stores**
```bash
mv chroma_langchain_db data/vector_stores/legacy_default
mv chroma_langchain_db_msi_docs data/vector_stores/msi_docs
```

---

### Phase 5: Update Imports

**Step 5.1: Update all Python imports**
```python
# Old: from config import DEFAULT_MODEL
# New: from src.core.config import DEFAULT_MODEL

# Old: from agent_setup import initialize_agent_components
# New: from src.core.agent import initialize_agent_components

# Old: from rag_agents import create_default_rag_tools
# New: from src.rag.registry import create_default_rag_tools
```

**Step 5.2: Update path references**
```python
# Update database paths in config.py
# Old: Path("src/organizations.db")
# New: Path("data/databases/organizations.db")

# Update document paths
# Old: Path("documents/")
# New: Path("data/documents/msi_docs/")

# Update vector store paths
# Old: "chroma_langchain_db_msi_docs"
# New: "data/vector_stores/msi_docs"
```

---

### Phase 6: Update Configuration Files

**Step 6.1: Update pyproject.toml**
```toml
[project]
name = "msi-ai-assistant"
packages = [{include = "src"}]

[project.scripts]
msi-assistant = "src.cli.main:main"
msi-api = "src.api.server:main"
```

**Step 6.2: Create/Update .gitignore**
```gitignore
# Data files
data/databases/*.db
data/vector_stores/*
data/uploads/*
!data/**/.gitkeep

# Logs
logs/*.log
!logs/.gitkeep

# Environment
.env
.venv/

# Python
__pycache__/
*.pyc
*.pyo
```

**Step 6.3: Update environment example**
```bash
cp .env .env.example
# Remove sensitive values
```

---

### Phase 7: Create Entry Points

**Step 7.1: Update main entry points**

**scripts/run_dev.sh:**
```bash
#!/bin/bash
# Development server
uvicorn src.api.server:app --reload --port 8080
```

**scripts/run_cli.sh:**
```bash
#!/bin/bash
# CLI interface
python -m src.cli.main
```

---

## File-by-File Mapping

### Current → New Location

| Current File | New Location | Notes |
|--------------|--------------|-------|
| `src/agent_setup.py` | `src/core/agent.py` | Renamed for clarity |
| `src/api_server.py` | `src/api/server.py` | Split routes later |
| `src/auth_utils.py` | `src/auth/utils.py` | |
| `src/config.py` | `src/core/config.py` | Update all paths |
| `src/main.py` | `src/cli/main.py` | CLI entry point |
| `src/mock_idp.py` | `src/auth/mock_idp.py` | |
| `src/organizations_mcp.py` | `src/mcp/organizations/server.py` | Modularized |
| `src/rag_agents.py` | Split into: | |
| | `src/rag/base.py` | BaseRAGAgent |
| | `src/rag/registry.py` | RAGAgentRegistry |
| | `src/rag/agents/msi_docs.py` | MSIDocsRAGAgent |
| `src/ticketing_mcp.py` | `src/mcp/ticketing/server.py` | Modularized |
| `src/token_store.py` | `src/auth/token_store.py` | |
| `src/utils.py` | `src/core/utils.py` | |
| `src/*.db` | `data/databases/*.db` | Separate data |
| `documents/*` | `data/documents/msi_docs/*` | Organized by source |
| `chroma_langchain_db*` | `data/vector_stores/*` | Organized by collection |
| `*.md` (root) | `docs/*` | Organized by category |
| `dev_resources/` | `docs/development/dev_resources/` | |

---

## Benefits

### 1. **Scalability**
- **Easy to add new MCP servers:** Just create `src/mcp/[name]/` directory
- **Easy to add new RAG agents:** Just add to `src/rag/agents/`
- **Clear ownership:** Each module has its own directory

### 2. **Maintainability**
- **Logical separation:** Core, API, Auth, MCP, RAG all separate
- **Find files faster:** Predictable locations
- **Easier onboarding:** Clear structure for new developers

### 3. **Data Organization**
- **Databases in one place:** `data/databases/`
- **Vector stores organized:** `data/vector_stores/[collection]/`
- **Source documents categorized:** `data/documents/[source]/`
- **Easy to backup:** Just backup `data/` directory

### 4. **Documentation**
- **All docs in one place:** `docs/`
- **Categorized by purpose:** getting-started, development, architecture, brand
- **Easy to maintain:** Clear hierarchy

### 5. **Testing**
- **Organized test structure:** unit, integration, fixtures
- **Test organization mirrors source:** `tests/unit/test_mcp/test_ticketing.py` matches `src/mcp/ticketing/`

### 6. **Development Experience**
- **IDE navigation:** Better autocomplete and Go to Definition
- **Imports make sense:** `from src.mcp.ticketing import TicketingServer`
- **Clear dependencies:** See what imports what

---

## Implementation Checklist

### Pre-Migration
- [ ] **Backup entire project**
- [ ] **Create feature branch:** `git checkout -b refactor/reorganize-structure`
- [ ] **Document current working state**
- [ ] **Run all tests (if any)**

### Phase 1: Structure
- [ ] Create all directories
- [ ] Create all `__init__.py` files
- [ ] Create `.gitkeep` files in data/logs directories

### Phase 2: Documentation
- [ ] Move documentation files to `docs/`
- [ ] Create `docs/README.md` index
- [ ] Update internal doc links
- [ ] Remove redundant files

### Phase 3: Source Code
- [ ] Move core modules
- [ ] Move API modules
- [ ] Move auth modules
- [ ] Move MCP servers
- [ ] Refactor RAG agents into modular structure
- [ ] Move CLI

### Phase 4: Data
- [ ] Move databases
- [ ] Move documents
- [ ] Move vector stores
- [ ] Update `.gitignore`

### Phase 5: Configuration
- [ ] Update all import statements
- [ ] Update all path references
- [ ] Update `pyproject.toml`
- [ ] Create `.env.example`
- [ ] Update configuration files

### Phase 6: Testing
- [ ] Update test imports
- [ ] Run all tests
- [ ] Fix any broken tests
- [ ] Verify API still works
- [ ] Verify CLI still works

### Phase 7: Documentation
- [ ] Update README.md
- [ ] Create architecture documentation
- [ ] Document new structure
- [ ] Update getting started guide

### Post-Migration
- [ ] Run full integration test
- [ ] Verify all features work
- [ ] Create PR with detailed description
- [ ] Merge to main
- [ ] Tag release: `v1.0.0-reorganized`

---

## Adding New Components (Post-Reorganization)

### Adding a New MCP Server

**Example: Add "Inventory" MCP Server**

1. Create directory structure:
```bash
mkdir -p src/mcp/inventory
touch src/mcp/inventory/__init__.py
touch src/mcp/inventory/server.py
touch src/mcp/inventory/models.py
touch src/mcp/inventory/database.py
```

2. Implement server in `server.py`:
```python
from fastmcp import FastMCP

mcp = FastMCP("Inventory Management")

@mcp.tool()
def check_inventory(item_id: str) -> dict:
    """Check inventory levels"""
    ...
```

3. Register in `src/core/agent.py`:
```python
from src.mcp.inventory.server import mcp as inventory_mcp

# Add to MCP client configuration
```

4. Add database to `data/databases/inventory.db`

5. Document in `docs/architecture/mcp-servers.md`

---

### Adding a New RAG Agent

**Example: Add "Product Catalog" RAG Agent**

1. Create agent file:
```bash
touch src/rag/agents/product_catalog.py
```

2. Implement agent:
```python
from src.rag.base import BaseRAGAgent

class ProductCatalogRAGAgent(BaseRAGAgent):
    def get_document_path(self):
        return self.project_root / "data/documents/product_catalog"

    def get_persist_directory(self):
        return self.project_root / "data/vector_stores/product_catalog"

    def get_tool_name(self):
        return "search_product_catalog"
```

3. Add documents to `data/documents/product_catalog/`

4. Register in `src/rag/registry.py`:
```python
from src.rag.agents.product_catalog import ProductCatalogRAGAgent

def create_default_rag_tools():
    registry = RAGAgentRegistry()
    registry.register(MSIDocsRAGAgent(...))
    registry.register(ProductCatalogRAGAgent(...))  # Add here
    return registry.get_all_tools()
```

5. Document in `docs/architecture/rag-agents.md`

---

## Risk Mitigation

### Risks
1. **Breaking imports:** Many files to update
2. **Path issues:** Database/document paths may break
3. **Lost files:** Moving many files increases risk

### Mitigations
1. **Backup before starting**
2. **Feature branch for changes**
3. **Incremental migration:** One phase at a time
4. **Test after each phase**
5. **Git tracking:** `git mv` to preserve history
6. **Automated testing:** Run tests frequently

---

## Timeline Estimate

| Phase | Effort | Notes |
|-------|--------|-------|
| Phase 1: Structure | 30 min | Directory creation |
| Phase 2: Documentation | 1 hour | Move and organize docs |
| Phase 3: Source Code | 3-4 hours | Move files, split rag_agents.py |
| Phase 4: Data | 30 min | Move data files |
| Phase 5: Imports | 2-3 hours | Update all imports and paths |
| Phase 6: Testing | 1-2 hours | Fix and verify tests |
| Phase 7: Documentation | 1 hour | Update docs |
| **Total** | **9-12 hours** | One full workday |

---

## Success Criteria

- ✅ All files moved to new locations
- ✅ All imports updated and working
- ✅ All tests passing
- ✅ API server runs without errors
- ✅ CLI runs without errors
- ✅ Documentation updated
- ✅ No files left in wrong locations
- ✅ `.gitignore` properly excludes data/logs
- ✅ New structure documented
- ✅ Team can easily add new MCP servers/RAG agents

---

## Questions & Answers

**Q: Should we do this all at once or incrementally?**
**A:** Incrementally, by phase. Test after each phase.

**Q: What if we need to rollback?**
**A:** Keep feature branch. Can revert entire branch if needed.

**Q: Will this break the Angular UI?**
**A:** No, the Angular UI is separate and unchanged.

**Q: How do we handle merge conflicts?**
**A:** Work in dedicated feature branch. Minimize other changes during migration.

**Q: Should we update the database schemas?**
**A:** No, just move the files. Schema changes are separate concern.

---

## Next Steps

1. **Review this plan** with team
2. **Get approval** for reorganization
3. **Schedule migration** window
4. **Create backup** of current state
5. **Execute phases 1-7**
6. **Verify and test**
7. **Merge and deploy**

---

**Document Owner:** Development Team
**Last Updated:** 2025-12-05
**Status:** Ready for Review

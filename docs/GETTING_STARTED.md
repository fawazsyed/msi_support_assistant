# Getting Started with MSI AI Assistant

Setup guide for the agentic RAG system with MCP integration.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [API Keys Setup](#api-keys-setup)
4. [LangSmith Configuration](#langsmith-configuration-optional)
5. [Running the Application](#running-the-application)
6. [Troubleshooting](#troubleshooting)
7. [Team Collaboration](#team-collaboration)

---

## Prerequisites

### Python Version Requirement
**You MUST use Python 3.12.10** - This project is NOT compatible with Python 3.13.x due to compatibility issues with LangChain and Chroma dependencies.

Check your Python version:
```bash
python --version
```

If you need to install Python 3.12.10:
- **Windows**: Download from [python.org](https://www.python.org/downloads/release/python-31210/)
- **macOS/Linux**: Use `pyenv` to install and manage Python versions

### Package Manager
This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable package management.

Install uv:
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/fawazsyed/msi-ai-assistant.git
cd msi-ai-assistant
```

### 2. Set Python Version
Ensure the project uses Python 3.12.10:
```bash
uv python pin 3.12.10
```

### 3. Install Dependencies

**Python dependencies:**
```bash
uv sync
```

This installs all required Python packages:
- LangChain and LangChain OpenAI
- FastAPI and Uvicorn (REST API server)
- FastMCP (Model Context Protocol servers)
- Chroma vector store (persistent)
- Honcho (process manager)
- Python-dotenv for environment variables

**Angular UI dependencies:**
```bash
cd ai-assistant-ui
npm install
cd ..
```

This installs the Angular web interface dependencies.

---

## API Keys Setup

### OpenAI API Key (Required)

1. **Create an OpenAI Account**
   - Go to [platform.openai.com](https://platform.openai.com/)
   - Sign up or log in

2. **Generate API Key**
   - Navigate to [API Keys](https://platform.openai.com/api-keys)
   - Click **"Create new secret key"**
   - Give it a name (e.g., "MSI Support Assistant")
   - Copy the key immediately (you won't see it again!)

3. **Add Billing Information**
   - Go to [Billing Settings](https://platform.openai.com/account/billing)
   - Add a payment method
   - Set usage limits to avoid unexpected charges

### Configure Environment Variables

1. **Copy the template file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your OpenAI key:**
   ```bash
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   ```

**Security Note**: Never commit the `.env` file to version control. It's already in `.gitignore`.

---

## LangSmith Configuration (Optional)

LangSmith provides powerful observability for your RAG pipeline - highly recommended for development!

### What LangSmith Provides:
- 🔍 Trace every LLM call and retrieval step
- 💰 See token usage and costs per query
- 📊 Debug retrieval quality (which chunks matched, similarity scores)
- 🧪 Compare experiments side-by-side
- 🐛 Understand why queries succeed or fail

### Setup Steps:

1. **Create LangSmith Account**
   - Go to [smith.langchain.com](https://smith.langchain.com)
   - Sign up (free tier: 5,000 traces/month)

2. **Generate API Key**
   - Navigate to Settings → API Keys
   - Click **"Create API Key"**
   - Key Type: Select **"Personal Access Token"**
   - Description: `msi-ai-assistant-dev` (or your name)
   - Expiration: Choose **"Never"** or **"1 year"**
   - Copy the key (starts with `lsv2_pt_...`)

3. **Add to `.env`**
   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_pt_your-actual-key-here
   LANGSMITH_PROJECT=msi-ai-assistant
   ```

4. **View Traces**
   - After running the app, visit [smith.langchain.com](https://smith.langchain.com)
   - Navigate to Projects → `msi-ai-assistant`
   - See detailed traces of every query

---

## Running the Application

### Option 1: Full Web Interface (Recommended)

**Windows:**
```bash
# From project root:
.\scripts\start.bat

# Or from scripts directory:
cd scripts
.\start.bat
```

**macOS/Linux:**
```bash
# From project root:
uv run honcho start
```

### What Happens:
1. **Mock IDP** starts on port 9400 (OAuth/JWT authentication)
2. **MCP Servers** start on ports 9000 and 9001 (Ticketing and Organizations)
3. **FastAPI Backend** starts on port 8080 (REST API)
4. **Angular UI** starts on port 4200 and automatically opens in your browser
5. The UI includes a health check that waits for the backend to be ready

**Note**: On first startup, Angular will compile and the backend will initialize. This takes 10-30 seconds.

### What You'll See:
- Terminal shows all services starting with prefixed output (e.g., `[ui]`, `[api]`, `[idp]`)
- Browser automatically opens to `http://localhost:4200`
- You can start chatting with the AI assistant immediately

### To Stop All Services:
```bash
# Windows:
.\scripts\stop.bat

# macOS/Linux:
Press Ctrl+C in the terminal running Honcho
```

---

### Option 2: CLI Testing (No UI)

For testing the core RAG functionality without the web interface:

```bash
uv run src/main.py
```

### What Happens:
1. Loads the VideoManager Admin Guide documentation
2. Creates embeddings using OpenAI's `text-embedding-3-small`
3. Indexes the document in a Chroma vector store (persists to `./chroma_langchain_db/`)
4. Runs a sample query: "How do I add a new user?"
5. Displays the AI-generated answer based on retrieved documentation

**Note**: First run takes longer (embedding documents). Subsequent runs are faster as the vector store is persistent.

---

## Troubleshooting

### Port Already in Use Error
```
[Errno 10048] only one usage of each socket address is normally permitted
```
**Solution:**
- Previous services are still running
- Windows: Run `.\scripts\stop.bat`
- macOS/Linux: Find and kill processes: `lsof -ti:PORT | xargs kill`
- See [PORT_CONFIG.md](PORT_CONFIG.md) for detailed troubleshooting

### Backend Not Ready / UI Shows Error
**Symptoms:**
- UI opens but shows "Failed to fetch" or similar error
- Console shows health check failures

**Solution:**
- Wait 10-30 seconds for all services to initialize
- The UI includes automatic health checks and will retry
- If timeout occurs (30 seconds), check that all services started:
  - Look for errors in the terminal output
  - Verify no port conflicts
  - Ensure `.env` file is configured correctly

### Rate Limit Error (429)
```
openai.RateLimitError: Error code: 429 - Request too large
```
**Solution:**
- Your OpenAI account has token limits (30,000 TPM for free tier)
- Wait a minute and try again
- The chunking implementation reduces this issue

### Python Version Error
```
ERROR: No solution found when resolving dependencies
```
**Solution:**
- Verify Python version: `python --version`
- Must be 3.12.x (NOT 3.13.x)
- Use `uv python pin 3.12.10` to set correct version

### Missing API Key
```
openai.OpenAIError: The api_key client option must be set
```
**Solution:**
- Check that `.env` file exists in project root
- Verify `OPENAI_API_KEY` is set correctly in `.env`
- Key should start with `sk-proj-` or `sk-`

### Import Errors
```
ModuleNotFoundError: No module named 'langchain'
```
**Solution:**
- Run `uv sync` to install all dependencies
- Ensure you're in the project directory

### LangSmith Not Working
```
No traces appearing in LangSmith dashboard
```
**Solution:**
- Verify `LANGSMITH_TRACING=true` in `.env`
- Check API key is correct (starts with `lsv2_pt_`)
- Ensure project name matches: `LANGSMITH_PROJECT=msi-ai-assistant`
- Check LangSmith status at [status.smith.langchain.com](https://status.smith.langchain.com)

---

## Team Collaboration

### For Team Leads

1. **Invite team members to LangSmith workspace:**
   - Go to [smith.langchain.com](https://smith.langchain.com) → Settings → Members
   - Send invitations via email
   - Members will share the same workspace and project

2. **Share repository access:**
   - Add team members to the GitHub repository
   - Ensure they have read/write access

### For New Team Members

1. **Accept LangSmith workspace invitation** (check your email)
2. **Follow all installation steps above**
3. **Create your own API keys:**
   - OpenAI: Your own account and key
   - LangSmith: Your own Personal Access Token
4. **Use the same project name:** `msi-ai-assistant`
5. **All team traces will appear in the shared project**

### Team Benefits
- ✅ **Shared Learning**: Everyone sees each other's traces and experiments
- ✅ **No Key Sharing**: Each person has their own API keys (more secure)
- ✅ **Easy Debugging**: "Check my trace from 10 minutes ago"
- ✅ **Cost Tracking**: See token usage per team member
- ✅ **Compare Experiments**: Side-by-side comparison of different approaches

### Best Practices
- Use descriptive run names for your experiments
- Add metadata tags to categorize traces
- Review team traces weekly to learn from each other
- Document interesting findings in the repository

---

## Next Steps

Once you're up and running:

1. **Use the web interface**: Start chatting at `http://localhost:4200`
2. **Try different queries**: Ask about MSI docs, ticketing, or organizations
3. **Check LangSmith traces**: Understand how RAG retrieval works
4. **Explore the code**:
   - Backend: `src/api/server.py` (FastAPI REST API)
   - Frontend: `ai-assistant-ui/src/app/` (Angular components)
   - RAG: `src/rag/` (Retrieval and agents)
   - MCP: `src/mcp/` (Ticketing and Organizations servers)
5. **Read additional docs**:
   - [ANGULAR_UI_GUIDE.md](ANGULAR_UI_GUIDE.md) - Frontend development
   - [SSO_IMPLEMENTATION.md](SSO_IMPLEMENTATION.md) - Authentication architecture
   - [PORT_CONFIG.md](PORT_CONFIG.md) - Port configuration
6. **Start contributing**: Check open issues and project roadmap

---

## Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangSmith Observability Guide](https://docs.smith.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Chroma Vector Store Docs](https://docs.trychroma.com/)
- [uv Package Manager](https://github.com/astral-sh/uv)

---

## Need Help?

- **Issues**: Open an issue on GitHub
- **Questions**: Ask in your team's communication channel
- **LangSmith Support**: [smith.langchain.com/support](https://smith.langchain.com/support)
- **OpenAI Support**: [help.openai.com](https://help.openai.com/)

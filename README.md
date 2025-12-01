# MSI Support Assistant

AI-powered support assistant for Motorola Solutions products using Model Context Protocol (MCP) and RAG (Retrieval-Augmented Generation).

## Project Status

Initial setup - In development

## Repository

https://github.com/fawazsyed/msi_support_assistant

---

## ⚠️ Important Requirements

### Python Version
**You MUST use Python 3.12.10** - This project is NOT compatible with Python 3.13.x due to compatibility issues with LangChain and Chroma dependencies.

To check your Python version:
```bash
python --version
```

If you need to install Python 3.12.10:
- **Windows**: Download from [python.org](https://www.python.org/downloads/release/python-31210/)
- **macOS/Linux**: Use `pyenv` to install and manage Python versions

### OpenAI API Key Required
This project uses OpenAI's GPT-4o model and requires a valid API key.

---

## Setup Instructions

### 1. Install Prerequisites
- Python 3.12.10 (required)
- [uv](https://github.com/astral-sh/uv) package manager

Install uv:
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Set Python Version
Ensure the project uses Python 3.12.10:
```bash
# Set Python version for the project
uv python pin 3.12.10
```

### 3. Get OpenAI API Key

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

### 4. Configure Environment Variables

Create a `.env` file in the project root:
```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

**Security Note**: Never commit the `.env` file to version control. It's already in `.gitignore`.

### 5. Install Dependencies
```bash
uv sync
```

This installs all required packages including:
- LangChain and LangChain OpenAI
- Chroma vector store (persistent)
- OpenAI Python client
- Python-dotenv for environment variables

---

## Running the Program

### Basic Usage
```bash
uv run main.py
```

This will:
1. Load the VideoManager Admin Guide documentation
2. Create embeddings using OpenAI's `text-embedding-3-small`
3. Index the document in a Chroma vector store (persists to `./chroma_langchain_db/`)
4. Run a sample query: "How do I add a new user?"
5. Display the AI-generated answer based on retrieved documentation

**Note**: First run takes longer (embedding documents). Subsequent runs are faster as the vector store is persistent.

### Expected Output
```
Question: How do I add a new user?

================================ Human Message =================================

How do I add a new user?

================================== Ai Message ==================================

To add a new user in VideoManager, follow these steps:
1. Navigate to the Admin tab.
2. Select the Users pane.
...
```

### Troubleshooting

**Rate Limit Error (429)**
```
openai.RateLimitError: Error code: 429 - Request too large
```
- Your OpenAI account has token limits (30,000 TPM for free tier)
- Wait a minute and try again
- Use a smaller portion of the document

**Python Version Error**
```
ERROR: No solution found when resolving dependencies
```
- Verify Python version: `python --version`
- Must be 3.12.x (NOT 3.13.x)
- Use `uv python pin 3.12.10` to set correct version

**Missing API Key**
```
openai.OpenAIError: The api_key client option must be set
```
- Check that `.env` file exists
- Verify `OPENAI_API_KEY` is set correctly in `.env`
- Key should start with `sk-proj-` or `sk-`

---

## Technology Stack

- **Language**: Python 3.12.10 | IF OS IS ARM64, EMULATE.
- **Package Manager**: uv
- **LLM**: OpenAI GPT-4o
- **Embeddings**: OpenAI text-embedding-3-small
- **Vector Store**: Chroma (persistent, local)
- **Framework**: LangChain
- **RAG Architecture**: Dynamic prompt middleware with similarity search

---

## Project Structure

```
msi_support_assistant/
├── main.py                 # Main RAG application
├── pyproject.toml          # Project dependencies
├── .env                    # API keys (not in git)
├── .env.example            # Template for .env
├── chroma_langchain_db/    # Persistent vector store (not in git)
├── documents/              # Knowledge base documents
│   └── video_manager_admin_guide_user.txt
├── dev_resources/          # Development references
├── tests/                  # Test outputs and validation
│   └── 01_base_code.txt
└── research/               # Research data (not in git)
```

---

## Testing

Test outputs are documented in the `tests/` folder for validation and debugging.

### Test 01: Base Code Implementation
Location: `tests/01_base_code.txt`

**Test Details:**
- Query: "How do I add a new user?"
- Status: ✓ PASSED
- Configuration: k=2 similarity search, Chroma persistence
- Result: Generated accurate 16-step instructions from documentation

**Key Findings:**
- Vector store persistence working correctly
- Context retrieval accurate and relevant
- Answer quality excellent for base implementation
- Known issue: Document not chunked (stored as single text)

See `tests/01_base_code.txt` for complete output and evaluation.

---

## Next Steps

- Implement proper document chunking for better retrieval
- Add support for multiple documents
- Create interactive chat interface
- Integrate MCP capabilities
- Migrate to AlloyDB for production scalability
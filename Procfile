# Procfile for running all MSI AI Assistant services
# Run with: honcho start

# Mock Identity Provider (OAuth/JWT)
idp: uv run python -m uvicorn src.auth.mock_idp:app --host 127.0.0.1 --port 9400

# MCP Servers
ticketing: uv run python -m src.mcp.ticketing.server
orgs: uv run python -m src.mcp.organizations.server

# FastAPI Backend
api: uv run python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8080

# Angular Frontend
ui: cd ai-assistant-ui && npm start
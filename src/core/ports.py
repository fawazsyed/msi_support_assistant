"""
Centralized port configuration for all MSI AI Assistant services.

This is the single source of truth for service ports.
Update this file to change ports across the entire application.
"""

# Authentication & Identity
MOCK_IDP_PORT = 9400

# MCP Servers
TICKETING_MCP_PORT = 9000
ORGANIZATIONS_MCP_PORT = 9001

# Backend API
FASTAPI_PORT = 8080

# Frontend UI
ANGULAR_UI_PORT = 4200

# URLs (derived from ports)
MOCK_IDP_URL = f"http://127.0.0.1:{MOCK_IDP_PORT}"
TICKETING_MCP_URL = f"http://127.0.0.1:{TICKETING_MCP_PORT}"
ORGANIZATIONS_MCP_URL = f"http://127.0.0.1:{ORGANIZATIONS_MCP_PORT}"
FASTAPI_URL = f"http://0.0.0.0:{FASTAPI_PORT}"
ANGULAR_UI_URL = f"http://localhost:{ANGULAR_UI_PORT}"
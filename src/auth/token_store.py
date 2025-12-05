"""
Shared token storage for SSO across MCP servers.

This module provides persistent storage for OAuth access tokens,
enabling Single Sign-On across multiple MCP servers without
requiring separate authentication flows for each server.
"""

import json
from pathlib import Path
from typing import Optional


# Store token in user's home directory
TOKEN_FILE = Path.home() / ".msi-assistant" / "token.json"


def save_token(token: str) -> None:
    """
    Save access token to persistent storage.

    Args:
        token: JWT access token to store
    """
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps({"access_token": token}))


def load_token() -> Optional[str]:
    """
    Load access token from persistent storage.

    Returns:
        The stored access token, or None if no token exists
    """
    if not TOKEN_FILE.exists():
        return None

    try:
        data = json.loads(TOKEN_FILE.read_text())
        return data.get("access_token")
    except (json.JSONDecodeError, KeyError):
        return None


def clear_token() -> None:
    """
    Clear stored access token.

    Useful for logging out or forcing re-authentication.
    """
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
"""
Shared authentication utilities for MCP servers.

This module provides common functions for role-based access control
and token claims extraction used across multiple MCP servers.
"""

from typing import List, Optional
from fastmcp.server.dependencies import get_access_token, AccessToken


def check_roles(allowed_roles: List[str]) -> bool:
    """
    Check if the current user has any of the allowed roles.

    Args:
        allowed_roles: List of role names to check against

    Returns:
        True if user has at least one of the allowed roles, False otherwise
    """
    token: AccessToken | None = get_access_token()
    roles = token.claims.get("roles") if token else None

    return any(role in roles for role in allowed_roles)


def get_username() -> Optional[str]:
    """
    Get the username of the currently authenticated user.

    Returns:
        Username from the token's 'sub' claim, or None if no token
    """
    token: AccessToken | None = get_access_token()
    return token.claims.get("sub") if token else None


def get_user_roles() -> Optional[List[str]]:
    """
    Get the roles of the currently authenticated user.

    Returns:
        List of role names from the token's 'roles' claim, or None if no token
    """
    token: AccessToken | None = get_access_token()
    return token.claims.get("roles") if token else None


def get_user_organizations() -> Optional[List[str]]:
    """
    Get the organizations of the currently authenticated user.

    Returns:
        List of organization names from the token's 'organizations' claim, or None if no token
    """
    token: AccessToken | None = get_access_token()
    return token.claims.get("organizations") if token else None
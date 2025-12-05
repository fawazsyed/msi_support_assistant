"""
MCP server for managing support tickets

Run (from project root):
uv run fastmcp run src/organizations_mcp.py --port 9001
"""

import pathlib
import sqlite3
from typing import Any, Dict, List

from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token, AccessToken
from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl

SERVER_URL = "http://127.0.0.1:9001"
ISSUER_URL = "http://127.0.0.1:9400"
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
DB_USERS = SCRIPT_DIR / "users.db"
DB_ORGANIZATIONS = SCRIPT_DIR / "organizations.db"

# JWT Token Verifier
VERIFIER = JWTVerifier(
    jwks_uri = f"{ISSUER_URL}/jwks",
    issuer = ISSUER_URL,
    audience = SERVER_URL
)

# Create RemoteAuthProvider for authentication
AUTH = RemoteAuthProvider(
    token_verifier = VERIFIER,
    authorization_servers = [AnyHttpUrl(ISSUER_URL)],
    base_url = AnyHttpUrl(SERVER_URL),
)

# Create FastMCP server instance
mcp = FastMCP(
    name = "MCP Server", 
    auth = {
        "provider": AUTH,
        "issuer_url": ISSUER_URL,
        "resource_server_url": SERVER_URL
    },
    token_verifier = VERIFIER
)

# Helper functions
def check_roles(allowed_roles: List[str]):
    token: AccessToken | None = get_access_token()
    roles = token.claims.get("roles") if token else None
    return any(role in roles for role in allowed_roles)

def get_username():
    token: AccessToken | None = get_access_token()
    return token.claims.get("sub") if token else None

@mcp.tool()
async def get_organization_users(
    organization: str
) -> Dict[str, Any]:
    """
    Description: Retrieves all usernames for a given organization.
    Use case: Use this tool to retrieve usernames for a given organization (tool
    will check that the calling user is a member of the organization and has
    permission to view organization members)
    Permissable roles: Any roles.
    Arguments: organization (required, string).
    Returns: Dict[str, Any] containing users or an error message.
    """

    if not organization:
        return {"error": "Error, no argument given for organization"}
    
    try:
        connection = sqlite3.connect(DB_USERS)
        cursor = connection.cursor()

        # Check permission to use tool
        if not check_roles(["admin"]):
            username = get_username()
            print(username)
            print(organization)
            query = "SELECT organization_permissions FROM users WHERE username = ? AND organization = ?"
            cursor.execute(query, (username, organization,))
            permissions_str = cursor.fetchone()
            print(permissions_str)
            if permissions_str:
                permissions = set(permissions_str[0].split(','))
                if "view_agency_users" not in permissions:
                        connection.close()
                        return {"error": "User does not have permission to use this tool for the given organization"}
            else:
                connection.close()
                return {"error": "User does not have permission to use this tool for the given organization"}

        query = "SELECT username FROM users WHERE organization = ?"
        cursor.execute(query, (organization,))
        users = cursor.fetchall()
        connection.close()

        return {"users": [user[0] for user in users]}
            
    except:
        return {"error": "Error with request"}
            
@mcp.tool()
async def compare_user_permissions(
    organization: str,
    usernames: List[str]
) -> Dict[str, Any]:
    """
    Description: Compares the permissions of given usernames in the given organization.
    Use case: Use this tool to compare permissions of organization users (tool
    will check that the calling user is a member of the organization and has
    permission to view organization members)
    Permissable roles: Any roles.
    Arguments: organization (required, string), usernames(required, List[str]).
    Returns: Dict[str, Any] containing shared permission and permissions not shared
    by all users or an error message.
    """

    if not organization:
        return {"error": "Error, no argument given for organization"} 
    if not usernames:
        return {"error": "Error, no argument given for usernames"}

    try: 
        connection = sqlite3.connect(DB_USERS)
        cursor = connection.cursor()

        # Check permission to use tool
        if not check_roles(["admin"]):
            username = get_username()
            query = "SELECT organization_permissions FROM users where username = ? AND organization = ?"
            cursor.execute(query, (username, organization,))
            permissions_str = cursor.fetchone()
            if permissions_str:
                permissions = set(permissions_str[0].split(','))
                if "view_agency_users" not in permissions:
                        connection.close()
                        return {"error": "User does not have permission to use this tool for the given organization"}
            else:
                connection.close()
                return {"error": "User does not have permission to use this tool for the given organization"}

        print("here")
        # Retrieve user permissions
        user_permissions_map = {}
        all_permissions = []

        for user in usernames:
            query = "SELECT organization_permissions FROM users WHERE username = ?"
            cursor.execute(query, (user,))
            permissions_str = cursor.fetchone()
            print("here")
            if permissions_str:
                permissions = set(permissions_str[0].split(','))
                user_permissions_map[user] = permissions
                all_permissions.append(permissions)
            else:
                user_permissions_map[user] = set()
                all_permissions.append(set())

        connection.close()

        # Compare user permissions
        permissions_comparison = {}

        shared_permissions = []
        if not all_permissions:
            shared_permissions = set()
        else:
            shared_permissions = all_permissions[0].copy()
            for permission_set in all_permissions:
                shared_permissions.intersection_update(permission_set)
        
        permissions_comparison["shared_permissions"] = list(shared_permissions)

        for user, permissions in user_permissions_map.items():
            unshared_permissions = permissions - shared_permissions
            permissions_comparison["unique_to_" + str(user)] = list(unshared_permissions)

    except:
        return {"error": "Error with request"}

    return permissions_comparison

@mcp.tool()
async def get_organizations() -> Dict[str, Any]:
    """
    Description: Retrieves all information for organizations.
    Use case: Use this tool to retrieve organization information for processing.
    Permissable roles: admin.
    Arguments: organization (required, string).
    Returns: Dict[str, Any] containing users or an error message.
    """
    
    if not check_roles(["admin"]):
        return {"error": "User does not have permission to use this tool"}
    
    response_json = {}
    try:
        connection = sqlite3.connect(DB_ORGANIZATIONS)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute("SELECT name, aware_service, status, region FROM organizations")

        organizations = cursor.fetchall()
        connection.close()
        
        for org in organizations:
            key = org['name'] 
            response_json[key] = {
                "name": org['name'],
                "aware_service": org['aware_service'],
                "status": org['status'],
                "region": org['region']
            }

    except:
        return {"error": "Error with request"}
    
    return response_json
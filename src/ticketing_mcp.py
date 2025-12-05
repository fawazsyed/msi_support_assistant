"""
MCP server for managing support tickets

Run (from project root):
uv run fastmcp run src/ticketing_mcp.py --port 9000
"""

import pathlib
import sqlite3
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.server.auth import RemoteAuthProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token, AccessToken
from pydantic import AnyHttpUrl

SERVER_URL = "http://127.0.0.1:9000"
ISSUER_URL = "http://127.0.0.1:9400"
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
DB_TICKET = SCRIPT_DIR / "ticket.db"

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

def check_roles(allowed_roles: List[str]):
    token: AccessToken | None = get_access_token()
    roles = token.claims.get("roles") if token else None

    return any(role in roles for role in allowed_roles)

def get_username():
    token: AccessToken | None = get_access_token()
    return token.claims.get("sub") if token else None



@mcp.tool()
async def get_username():
    """
    Description: Retrieves the active user's username.
    Use case: Use this tool to retrieve the active user's username as needed. 
    Permissable roles: Any roles.
    Arguments: None.
    Returns: The username as a string.
    """
    token: AccessToken | None = get_access_token()
    return token.claims.get("sub") if token else None

@mcp.tool()
async def get_user_roles():
    """
    Description: Retrieves the active user's roles.
    Use case: Use this tool to retrieve the active user's roles as needed. 
    Permissable roles: Any roles.
    Arguments: None.
    Returns: The roles as a list of strings.
    """
    token: AccessToken | None = get_access_token()
    return token.claims.get("roles") if token else None

@mcp.tool()
async def get_organizations():
    """
    Description: Retrieves the active user's organizations.
    Use case: Use this tool to retrieve the active user's organizations as needed. 
    Permissable roles: Any roles.
    Arguments: None.
    Returns: The organizations as a list of strings.
    """
    token: AccessToken | None = get_access_token()
    return token.claims.get("organizations") if token else None

@mcp.tool()
async def create_ticket(
    title: str,
    description: str
) -> str:
    """
    Description: Submits a ticket describing user issues.
    Use case: Use this tool to submit a ticket for review on behalf of the user.
    Permissable roles: Any role
    Arguments: title (required, string), description (required, string).
    Returns: A string conveying the success of the ticket creation.
    """

    if not title:
        return "Error, no argument given for title"
    
    if not description:
        return "Error, no argument given for description"

    # Pull user name from token
    username = get_username()

    # Insert ticket into database
    try:
        connection = sqlite3.connect(DB_TICKET)
        cursor = connection.cursor()
        query = "INSERT INTO tickets (title, description, username, status, response, response_user) VALUES (?, ?, ?, ?, ?, ?)"
        cursor.execute(query, (title, description, username, "active", None, None))
        connection.commit()
        id = cursor.lastrowid
        connection.close()

        return f"Ticket successfully created with id: {id}"
    except:
        return "Error with request"

@mcp.tool()
async def resolve_ticket(
    ticket_id: int,
    resolution_description: str
) -> str:
    """
    Description: Resolves an unresolved ticket.
    Use case: Use this tool to resolve a ticket on behalf of the user.
    Permissable roles: admin.
    Arguments: ticket_id (required, int), resolution_description (required, string).
    Returns: A string conveying the success of the ticket resolution.
    """

    if not check_roles(["admin"]):
        return "User does not have permission to use this tool"

    if not ticket_id:
        return "Error, no argument given for ticket_id" 
    if not resolution_description:
        return "Error, no argument given for description"

    # Pull user name from token
    username = get_username()

    # Edit ticket to resolved
    try:
        connection = sqlite3.connect(DB_TICKET)
        cursor = connection.cursor()
        
        cursor.execute("SELECT status FROM tickets where id = ?", (ticket_id,))
        ticket_data = cursor.fetchone()
        
        if ticket_data is None:
            connection.close()
            return f"Ticket ID {ticket_id} not found"
        
        status = ticket_data[0]
        if status != "active":
            connection.close()
            return f"Ticket {ticket_id} status not active"
        
        update = """
            UPDATE tickets
            SET status = ?, response = ?, response_user = ?
            WHERE id = ?
        """
        cursor.execute(update, ("resolved", resolution_description, username, ticket_id))
        
        connection.commit()
        id = cursor.lastrowid
        connection.close()

        return f"Ticket {id} resolved"
    except:
        return "Error with request"

@mcp.tool()
async def get_tickets_by_user(
    username: Optional[str] = None
) -> Dict[str, Any]:
    """
    Description: View tickets created by a particular user. Non-admin users can only
    view their own tickets.
    Use case: Use this tool to view all tickets from a particular user.
    Permissable roles: Any role
    Arguments: username (optional, string)
    Returns: A string conveying the success of the ticket resolution.
    """

    # Only admin or the user owning the ticket should be able to view tickets for some user
    this_username = get_username()
    goal_username = username if username else this_username
    if this_username != goal_username:
        if not check_roles(["admin"]):
            return {"error": "User does not have permission to use this tool for the given username"}

    if not username:
        goal_username = this_username
    
    tickets_json = {}
    try:
        connection = sqlite3.connect(DB_TICKET)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        query = """
            SELECT id, title, description, status, response, response_user 
            FROM tickets
            where username = ?
        """
        cursor.execute(query, (goal_username,))

        ticket_data = cursor.fetchall()
        connection.close()

        for ticket in ticket_data:
            ticket_id = str(ticket['id']) 
            tickets_json[ticket_id] = {
                "title": ticket['title'],
                "description": ticket['description'],
                "status": ticket['status'],
                "resolution": ticket['response'],
                "resolved_by": ticket['response_user']
            }

    except:
        return {"error": "Error with request"}
    
    return tickets_json

@mcp.tool()
async def get_tickets_by_status(
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Description: Gets all tickets of a particular status (or all tickets if no status
    argument provided).
    Use case: Use this tool to retrieve all tickets of a particular status.
    Permissable roles: admin.
    Arguments: status (optional, string).
    Returns: A dict containing tickets (indexed by ticket_id) or a dict containing
    an error message if call was not succesful.
    """

    if not check_roles(["admin"]):
        return "User does not have permission to use this tool"
    
    tickets_json = {}
    try:
        connection = sqlite3.connect(DB_TICKET)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        query = """
            SELECT id, title, description, status, response, response_user 
            FROM tickets
        """
        if status:
            query += "where status = ?"
            cursor.execute(query, (status,))
        else:
            cursor.execute(query)

        ticket_data = cursor.fetchall()
        connection.close()

        for ticket in ticket_data:
            ticket_id = str(ticket['id']) 
            tickets_json[ticket_id] = {
                "title": ticket['title'],
                "description": ticket['description'],
                "status": ticket['status'],
                "resolution": ticket['response'],
                "resolved_by": ticket['response_user']
            }

    except:
        return {"error": "Error with request"}
    
    return tickets_json

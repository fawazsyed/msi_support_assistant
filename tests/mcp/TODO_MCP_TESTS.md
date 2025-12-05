# TODO: MCP Server Tests

## Status: Not Yet Implemented

MCP server tests have been removed because they require code refactoring before they can be properly tested.

## Why Tests Were Removed

FastMCP's `@mcp.tool()` decorator transforms functions into `FunctionTool` objects for server routing. These cannot be called directly in unit tests:

```python
# This doesn't work:
result = await create_ticket(title="Test", description="Test")  
# TypeError: 'FunctionTool' object is not callable
```

## What Needs Testing

### Ticketing Server (`src/mcp/ticketing/server.py`)
- `create_ticket()` - Validation, database insertion
- `resolve_ticket()` - Admin permissions, status checks
- `get_tickets_by_user()` - Permission boundaries, user filtering
- `get_tickets_by_status()` - Admin-only access, status filtering
- Edge cases: missing arguments, nonexistent tickets, wrong permissions

### Organizations Server (`src/mcp/organizations/server.py`)
- `get_organization_users()` - Permission checks, user listing
- `compare_user_permissions()` - Shared/unique permission analysis
- `get_organizations()` - Admin-only organization listing
- Edge cases: wrong organization, missing users, empty database

## Recommended Implementation Approach

### Option 1: Refactor for Testability (Recommended)

Separate business logic from MCP decorators:

```python
# src/mcp/ticketing/logic.py (new file)
async def create_ticket_impl(
    title: str, 
    description: str,
    username: str,
    db_path: Path
) -> str:
    """Pure business logic - easily testable"""
    if not title:
        return "Error, no argument given for title"
    if not description:
        return "Error, no argument given for description"
    
    # Database logic here...
    return f"Ticket successfully created with id: {ticket_id}"

# src/mcp/ticketing/server.py (modified)
from src.mcp.ticketing.logic import create_ticket_impl

@mcp.tool()
async def create_ticket(title: str, description: str) -> str:
    """MCP wrapper - handles auth/routing only"""
    username = get_username()
    return await create_ticket_impl(title, description, username, DB_TICKET)
```

Then create tests for the `_impl` functions:

```python
# tests/mcp/test_ticketing_logic.py
from src.mcp.ticketing.logic import create_ticket_impl

async def test_create_ticket_success():
    result = await create_ticket_impl(
        title="Test",
        description="Test description",
        username="test_user",
        db_path=temp_db_path
    )
    assert "successfully created" in result
```

### Option 2: Integration Tests

Test via HTTP requests to a running MCP server:

```python
# tests/integration/test_mcp_servers.py
import httpx
import pytest

@pytest.fixture
async def ticketing_server():
    """Start MCP ticketing server on test port"""
    # Implementation details...
    
async def test_create_ticket_integration(ticketing_server):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ticketing_server}/tools/create_ticket",
            json={"title": "Test", "description": "Test"},
            headers={"Authorization": f"Bearer {test_token}"}
        )
        assert response.status_code == 200
        assert "successfully created" in response.json()
```

## Estimated Effort

- **Option 1 (Refactor)**: 4-6 hours
  - Extract business logic: 2-3 hours
  - Write unit tests: 2-3 hours
  - Benefits: Fast tests, better code organization

- **Option 2 (Integration)**: 3-4 hours
  - Setup test server fixtures: 1-2 hours
  - Write integration tests: 2 hours
  - Benefits: Tests real behavior, catches integration issues

## Files That Need Tests

- [ ] `src/mcp/ticketing/server.py` (9 functions)
- [ ] `src/mcp/organizations/server.py` (3 functions)

## Success Criteria

✅ All MCP tools have test coverage
✅ Permission checks are validated
✅ Database edge cases are handled
✅ Error messages are tested
✅ Tests run in CI/CD pipeline

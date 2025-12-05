# Port Configuration

**Single Source of Truth for All Service Ports**

## Current Port Assignments

| Service | Port | Purpose |
|---------|------|---------|
| **Mock IDP** | 9400 | OAuth/JWT authentication provider |
| **Ticketing MCP** | 9000 | MCP server for ticketing operations |
| **Organizations MCP** | 9001 | MCP server for organization operations |
| **FastAPI Backend** | 8080 | REST API server |
| **Angular UI** | 4200 | Frontend web interface |

## Configuration Files

When changing ports, update **ALL** of these files:

### Backend (Python)
- **`src/core/ports.py`** - Primary port configuration
- `Procfile` - Honcho process manager
- `src/mcp/ticketing/server.py` - Line with `.run(port=...)`
- `src/mcp/organizations/server.py` - Line with `.run(port=...)`
- `src/auth/mock_idp.py` - Uvicorn run command

### Frontend (Angular)
- **`ai-assistant-ui/src/environments/environment.ts`** - Development config
- **`ai-assistant-ui/src/environments/environment.prod.ts`** - Production config

### Documentation
- `README.md` - Usage instructions
- `PORT_CONFIG.md` - This file

## How to Change Ports

1. **Update the primary config:**
   - Python: Edit `src/core/ports.py`
   - Angular: Edit `ai-assistant-ui/src/environments/environment.ts`

2. **Update all dependent files** listed above

3. **Restart all services:**
   ```bash
   # Kill existing processes
   Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force

   # Start with new configuration
   .\start.bat
   ```

## Port Conflict Resolution

If you encounter `[Errno 10048] port already in use`:

```powershell
# Option 1: Use the stop script
.\stop.bat

# Option 2: Kill all Python/Node processes manually
Get-Process python,node -ErrorAction SilentlyContinue | Stop-Process -Force

# Option 3: Find process using specific port
netstat -ano | findstr "PORT_NUMBER"
taskkill /F /PID <PID>
```

## Future Improvements

- [ ] Generate Procfile from `src/core/ports.py`
- [ ] Auto-generate Angular environment from Python config
- [ ] Add port validation on startup
- [ ] Support .env-based port configuration
# GitHub Copilot + MCP Integration Guide (December 2025)

## The Easy Way ✨

**You don't need Claude Desktop!** VS Code now has native MCP support through GitHub Copilot.

### One-Click Solution: Copilot MCP Extension

Install this single extension to connect GitHub Copilot to any MCP server:

```vscode-extensions
AutomataLabs.copilot-mcp
```

**What it does:**
- Adds MCP server management UI to VS Code Activity Bar
- Exposes MCP tools directly to GitHub Copilot Chat
- Discovers and installs 900+ open-source MCP servers
- Auto-reconnects if servers drop
- Works with local or remote MCP servers

### Installation Steps

1. **Install the extension:**
   ```powershell
   code --install-extension AutomataLabs.copilot-mcp
   ```
   
   Or search "Copilot MCP" in VS Code Extensions marketplace

2. **Open MCP Servers panel:**
   - Look for new "MCP Servers" icon in Activity Bar (left sidebar)
   - Or: `Ctrl+Shift+P` → "MCP: Open Servers View"

3. **Search & install servers:**
   - Click "Discover Servers" or search in the panel
   - For your project, search for:
     - "LangChain" (docs already available via your current MCP tool)
     - "FastAPI" (if available)
     - "Python" related servers
     - "Documentation" servers

4. **Use in Copilot Chat:**
   - Open GitHub Copilot Chat (`Ctrl+Shift+I`)
   - Your MCP tools are automatically available
   - Example: "@workspace search LangChain docs for RAG patterns"

### Benefits vs Claude Desktop Config

| Claude Desktop | Copilot MCP Extension |
|----------------|----------------------|
| Edit JSON config file | UI-based management |
| Restart app to reload | Hot reload |
| Limited to Claude | Works with GitHub Copilot |
| Manual server discovery | Searchable server catalog |
| No server health checks | Real-time monitoring |

## Advanced: Native VS Code MCP Support

VS Code 1.106+ (October 2024+) has **built-in MCP support** through three approaches:

### 1. Language Model Tools (Recommended for local integration)

Create VS Code extensions that register MCP tools:

```typescript
// Extension registers MCP tool for Copilot
vscode.lm.registerTool('myMCPTool', {
  invoke: async (parameters, token) => {
    // Connect to your MCP server
    // Return results to Copilot
  }
});
```

**Benefits:**
- Deep VS Code API integration
- Distribute via Marketplace
- Full control over tool behavior

### 2. MCP Tools (External servers)

VS Code can connect to external MCP servers:

```json
// settings.json
{
  "github.copilot.chat.mcp.servers": {
    "fastapi-docs": {
      "command": "npx",
      "args": ["-y", "@your/fastapi-docs-mcp"]
    },
    "langchain-docs": {
      "command": "npx", 
      "args": ["-y", "@your/langchain-docs-mcp"]
    }
  }
}
```

**Benefits:**
- No extension development needed
- Reuse MCP servers across tools
- Local or remote deployment

### 3. Chat Participants (Custom assistants)

Create @-mentionable experts in Copilot Chat:

```typescript
vscode.chat.createChatParticipant('fastapi', handler);
// Use: @fastapi How do I implement dependency injection?
```

## For Your MSI AI Assistant Project

### Current State
✅ You have: `mcp_docs_by_langc_SearchDocsByLangChain` tool
✅ Your FastMCP servers work with your Python code
❌ Missing: GitHub Copilot can't access your MCP servers

### Recommended Setup

**Option A: Quick Start (5 minutes)**
1. Install Copilot MCP extension
2. Search for relevant documentation servers
3. Start using in Copilot Chat

**Option B: Full Integration (30 minutes)**
1. Create VS Code extension that wraps your existing MCP client
2. Register your weather/math servers as language model tools
3. Let Copilot use them directly

**Option C: Configuration-only (10 minutes)**
1. Configure your existing servers in VS Code settings
2. VS Code automatically exposes them to Copilot
3. No code changes needed

### Example: Exposing Your Weather Server to Copilot

Add to `.vscode/settings.json`:

```json
{
  "github.copilot.chat.mcp.servers": {
    "weather": {
      "url": "http://localhost:8000/sse",
      "transport": "sse"
    },
    "math": {
      "command": "uv",
      "args": ["run", "src/mcp_server.py"],
      "transport": "stdio"
    }
  }
}
```

Then in Copilot Chat:
```
@workspace Use the weather tool to get current conditions in Chicago
```

## Documentation Resources

### VS Code MCP Integration
- [AI Extensibility Overview](https://code.visualstudio.com/api/extension-guides/ai/ai-extensibility-overview)
- [MCP Tools Guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [Language Model Tools API](https://code.visualstudio.com/api/extension-guides/ai/tools)
- [MCP Extension Sample](https://github.com/microsoft/vscode-extension-samples/blob/main/mcp-extension-sample)

### Copilot MCP Extension
- [GitHub Repository](https://github.com/vikashloomba/copilot-mcp)
- [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=AutomataLabs.copilot-mcp)

### Model Context Protocol
- [Official Specification](https://modelcontextprotocol.io)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)

## Why This Is Better

**Before (Claude Desktop approach):**
- Edit `claude_desktop_config.json`
- Only works in Claude Desktop app
- Restart app to reload servers
- Can't use in VS Code with code

**After (VS Code + Copilot MCP):**
- UI-based server management
- Works directly in your IDE
- Hot reload, no restarts
- Copilot sees your code + MCP tools together
- No context switching between apps

## Next Steps

1. **Install now:** `code --install-extension AutomataLabs.copilot-mcp`
2. **Explore servers:** Open MCP panel, search "documentation"
3. **Test integration:** Ask Copilot about LangChain/FastAPI
4. **Configure your servers:** Expose weather/math tools to Copilot

## Troubleshooting

**Extension not showing servers:**
- Check GitHub Copilot Chat is installed and active
- Reload window: `Ctrl+Shift+P` → "Reload Window"

**Servers not connecting:**
- Check server health in MCP panel
- View logs: `Ctrl+Shift+P` → "MCP: Show Logs"

**Copilot not using tools:**
- Explicitly mention: "Use the [tool name] to..."
- Check tool is enabled in MCP panel
- Try @workspace to give more context

## Summary

**December 2025 = Native VS Code MCP support!**

You no longer need Claude Desktop configuration. Just install the Copilot MCP extension and you get:
- ✅ GitHub Copilot + MCP integration in VS Code
- ✅ UI for managing servers (no JSON editing)
- ✅ Access to 900+ MCP servers
- ✅ Your existing FastMCP servers can be exposed
- ✅ LangChain, FastAPI, Angular, and any other docs

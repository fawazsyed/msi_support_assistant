# Quick Start Guide - MSI AI Assistant Angular UI

## What's Been Built

A complete, production-ready Angular UI for your LangChain-based AI assistant with:

### 🎯 Core Features
- Modern chat interface with conversation management
- Real-time streaming message display
- RAG context visualization (shows retrieved documents)
- MCP tool call tracking (math, weather tools)
- Markdown rendering with code syntax highlighting
- Responsive sidebar with conversation history

### 📁 Project Structure
```
ai-assistant-ui/
├── src/app/
│   ├── components/
│   │   ├── chat-container/      ← Main app container
│   │   ├── sidebar/             ← Conversation list
│   │   ├── message-list/        ← Message display
│   │   ├── message-input/       ← Text input
│   │   ├── message-item/        ← Single message
│   │   ├── markdown/            ← Markdown renderer
│   │   ├── tool-calls/          ← Tool execution display
│   │   └── rag-context/         ← RAG document display
│   ├── services/
│   │   └── langchain-api.service.ts  ← Backend communication
│   └── models/
│       └── message.model.ts     ← TypeScript types
```

## 🚀 Running the Application

### Option 1: Development Server (Recommended)

```bash
cd ai-assistant-ui
npm start
```

Open http://localhost:4200 in your browser.

### Option 2: Production Build

```bash
cd ai-assistant-ui
npm run build
```

Serve the files from `dist/ai-assistant-ui/` using any static file server.

## 🔧 Current State

### Working Features (Mock Data)
The UI is fully functional with **mock data** that simulates:
- ✅ Sending messages
- ✅ Receiving streaming responses
- ✅ Displaying RAG context (simulated documents)
- ✅ Showing tool calls (simulated math/weather tools)
- ✅ Creating/switching/deleting conversations
- ✅ Markdown rendering with syntax highlighting

### What You'll See
When you run the app, you'll see:
1. **Empty state** with example queries
2. **Sidebar** with "New Chat" button
3. **Input field** at the bottom

Try typing a message and pressing Enter - you'll see:
- Your message appears instantly
- Typing indicator shows
- Assistant response streams in token-by-token
- Tool calls appear in colored boxes
- RAG context shows retrieved documents

## 🔌 Connecting to Your LangChain Backend

### Current Implementation
The service at `src/app/services/langchain-api.service.ts` uses mock streaming.

### To Connect Your Backend

**Step 1:** Create a FastAPI endpoint in your Python project:

```python
# Create: src/api_server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for Angular
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Your existing agent from main.py
    from main import agent  # Import your LangChain agent

    response = await agent.ainvoke({
        "messages": [{"role": m.role, "content": m.content} for m in request.messages]
    })

    return {"content": response}
```

**Step 2:** Run the backend:

```bash
# Terminal 1: Python Backend
pip install fastapi uvicorn
uvicorn src.api_server:app --port 8080 --reload

# Terminal 2: Angular UI
cd ai-assistant-ui
npm start
```

**Step 3:** Update the service (already configured to use `http://localhost:8080/api`):

The service is already configured to call the backend, you just need to implement proper streaming in the `streamResponse` method.

## 🎨 Customization

### Change Branding
Update "MSI Assistant" to your company name:
- `src/app/components/sidebar/sidebar.component.ts` (line 19)
- `src/app/components/message-item/message-item.component.ts` (line 30)

### Change Colors
Update the gradient in `src/app/components/sidebar/sidebar.component.ts`:
```typescript
background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
// Change to your brand colors
```

### Change Syntax Highlighting Theme
Update `src/styles.scss`:
```scss
@import 'highlight.js/styles/atom-one-dark.css';
// Try: github-dark, monokai, vs2015, etc.
```

## 📋 Key Files to Know

| File | Purpose | When to Edit |
|------|---------|-------------|
| `langchain-api.service.ts` | Backend API calls | Connecting to real backend |
| `message.model.ts` | Type definitions | Adding new message types |
| `sidebar.component.ts` | Conversation list | Changing branding/colors |
| `styles.scss` | Global styles | Theme customization |

## 🧪 Testing the UI

### Example Queries to Try:
1. "How do I add a new user?" (RAG query)
2. "What is 5 + 3?" (Math tool)
3. "What's the weather in NYC?" (Weather tool)
4. "What is the magic number times 10?" (Multiple tools)

### What You Should See:
- **RAG Context**: Yellow box with "Retrieved Context" showing document chunks
- **Tool Calls**: Purple box with "Tool Calls" showing function names and arguments
- **Streaming**: Text appearing character-by-character
- **Markdown**: Formatted text, code blocks with syntax highlighting

## 🎯 Next Steps

1. **Run the UI**: `cd ai-assistant-ui && npm start`
2. **Test with mock data**: Try sending messages, creating conversations
3. **Connect backend**: Follow the "Connecting to Your LangChain Backend" section
4. **Customize**: Update branding, colors, and messages

## 📚 Technologies Used

- **Angular 21** - Latest version with standalone components
- **TypeScript** - Type-safe development
- **Signals** - Reactive state management (no RxJS complexity!)
- **marked** - Markdown parsing
- **highlight.js** - Code syntax highlighting
- **SCSS** - Styling

## 🤝 Integration Points

Your existing LangChain setup:
- ✅ Claude 3.5 Sonnet (LLM)
- ✅ OpenAI embeddings
- ✅ Chroma vector store
- ✅ MCP tools (math, weather)

The UI visualizes all of these! You just need to pipe the data through a REST/SSE endpoint.

## ❓ Troubleshooting

**App won't start?**
```bash
cd ai-assistant-ui
rm -rf node_modules package-lock.json
npm install
npm start
```

**Build errors?**
Check that all imports use forward slashes `/` not backslashes `\`.

**Styling looks wrong?**
Clear browser cache and hard reload (Ctrl+Shift+R).

## 📖 Full Documentation

See `ai-assistant-ui/README.md` for complete documentation including:
- Architecture details
- Component documentation
- API integration guide
- Deployment instructions

---

**You now have a fully functional AI chat UI! 🎉**

Run `npm start` in the `ai-assistant-ui` folder and open http://localhost:4200 to see it in action.

feat(rag): implement RAG chain with LangChain

Implemented RAG chain using LangChain's dynamic_prompt
middleware and OpenAI embeddings. System uses Chroma for persistent
vector storage, eliminating redundant embedding API calls across
restarts.

Modified files:
- main.py: Complete rewrite from "Hello World" to full RAG system
  * Added LangChain imports and Chroma vector store setup
  * Implemented dynamic_prompt middleware for context injection
  * Configured similarity search with k=2 retrieval
  * Loads VideoManager Admin Guide (user-facing version)
  * Runs sample query: "How do I add a new user?"
  
- pyproject.toml: Updated Python version and dependencies
  * Changed Python requirement: 3.13.9 → 3.12.10 (strict pin)
  * Added langchain, langchain-openai, langchain-chroma
  * Added langchain-anthropic, langchain-google-vertexai
  * Added langchain-community, faiss-cpu, python-dotenv, certifi
  
- .python-version: Changed from 3.13.9 to 3.12.10

- .gitignore: Added .env exclusion for API key security

- README.md: Complete rewrite with comprehensive documentation
  * Added Python 3.12.10 requirement warning (3.13.x incompatible)
  * Added OpenAI API key setup guide with billing instructions
  * Added usage instructions and troubleshooting section
  * Updated technology stack to reflect Chroma
  * Documented persistence behavior and first-run indexing
  
New files:
- .env.example: Template for OpenAI API key configuration
- chroma_langchain_db/: Persistent vector store directory
- tests/01_base_code.txt: Test output and validation for base RAG chain

Technical implementation:
- RAG chain: similarity search (k=2) + single LLM inference
- Chroma persists embeddings to disk, survives restarts
- Alternative models documented: Claude 3.5, Gemini 2.0 Flash
- Collection count check prevents duplicate document indexing

Known issues:
- Document stored as single text (not chunked)


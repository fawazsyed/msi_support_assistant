# Quick Test Reference

## Run Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific modules
uv run pytest tests/rag/ -v
uv run pytest tests/observability/ -v

# Watch mode (re-run on file changes)
uv run pytest tests/ -v --looponfail
```

## Test Results

```
✅ 68 passing tests
📝 MCP tests - TODO (see tests/mcp/TODO_MCP_TESTS.md)
```

## What's Tested

| Module | Tests | Status |
|--------|-------|--------|
| RAG Base | 15 | ✅ |
| RAG Registry | 13 | ✅ |
| PII Scrubber | 17 | ✅ |
| Data Collector | 23 | ✅ |
| MCP Servers | - | 📝 TODO |

## CI/CD

Tests run automatically on:
- Push to `main` or `owens/observability`
- Pull requests to `main`
- Only when Python code changes

View results: GitHub repo → Actions tab

## Troubleshooting

### Test fails locally but not in CI?
- Check for hardcoded paths
- Verify environment variables

### Want to add MCP tests?
See: `tests/mcp/TODO_MCP_TESTS.md`

### Add new tests?
Follow patterns in existing test files:
1. Create fixtures for setup
2. Use mocks for external dependencies
3. Test happy path + edge cases
4. Add clear docstrings

# Commit Message Template

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Type Examples
- `feat`: New feature or functionality
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring without feature changes
- `test`: Adding or updating tests
- `chore`: Build, dependency, or tooling changes
- `perf`: Performance improvements
- `ci`: Changes to CI/CD or GitHub workflows
- `revert`: Reverts a previous commit

## Scope Examples
- `server`: Server implementation
- `client`: Client implementation
- `protocol`: Protocol specification
- `transport`: Transport layer (I/O)
- `handlers`: Message handlers
- `examples`: Reference or canonical examples

## Subject Standards
- Use imperative mood (present tense): "add" not "adds" or "added"
- Don't capitalize first letter
- No period at the end
- Maximum 50 characters (72 absolute max)

## Body Standards
- Explain what and why, not how
- Wrap at 72 characters
- Separate from subject with blank line
- Projet Guidance: Include "Reference Version: " or "

## Footer Guidance
- Include Reference Implementation version when updating handlers or protocol compliance
- Include implementation version (semver) for releases or significant changes
- Should use Footer for feature implementations, bug fixes

## Examples

### Feature Implementation
```
feat(handlers): implement initialize request handler

Added handle_initialize() function to process JSON-RPC initialize requests.
Implements protocol handshake per MCP specification.

- Extracts request parameters from JSON-RPC message
- Returns initialize response with protocol version and capabilities
- Maintains field ordering: jsonrpc → id → result
- Validates against examples/reference/ref-v0.1.0/01a_initialize_request.json

Reference Implementation: ref-v0.1.0
Version: 0.2.0
```

### Documentation Update
```
docs(protocol): add JSON-RPC 2.0 error codes specification

Documented complete JSON-RPC 2.0 error code requirements for protocol.
References standard error codes (-32700 to -32603) and custom error ranges.

- Added error code table with descriptions
- Documented error response format requirements
- Referenced examples/reference/ref-v0.1.0/03b and 04b error examples
- Aligned with canonical error handling structure
```

### Bug Fix
```
fix(transport): resolve EOF handling in message reading

Fixed message reading to properly handle stream termination.
Changed from checking `message is None` to proper EOF detection.

- input() raises EOFError on EOF, doesn't return None
- readline() returns empty string on EOF
- Updated main_loop() to use try/except for proper EOF handling

Reference Implementation: ref-v0.1.0
Version: 0.1.1
```

### Example Addition
```
feat(examples): add canonical context request/response examples

Added canonical JSON-RPC message examples for context operations.
Establishes baseline format for future context handlers.

- Added context_request.json to examples/canonical/2025-06-18/
- Added context_response.json following message format conventions
- Maintains field ordering per protocol specification
- References ref-v0.1.0 structure for consistency
```

## Checklist

Before committing:
- [ ] Subject line < 51 characters
- [ ] Subject uses imperative mood (present tense)
- [ ] Body explains what and why
- [ ] Body lines < 73 characters
- [ ] Message type matches actual changes

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

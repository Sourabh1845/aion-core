# Security Policy

AION Stage 6 is an early MCP firewall MVP. It should be treated as experimental until hardened.

## Current Security Scope

AION can:

- inspect MCP `tools/call` messages
- allow or block calls using JSON policy
- log receipts for decisions
- return MCP-compatible block errors

AION does not yet provide:

- cryptographic receipt signing
- tamper-proof storage
- authentication
- network isolation
- enterprise policy management

## Reporting Issues

Please open a private security report or contact the maintainers before publishing exploit details.

Useful details:

- policy file
- MCP request
- expected decision
- actual decision
- receipt output

# Real MCP Integration

AION wraps a stdio MCP server command.

Normal MCP server:

```powershell
python path/to/mcp_server.py
```

Same server behind AION:

```powershell
aion-mcp-firewall --policy examples/policies/stage6-default.json --receipt-log receipts/aion.jsonl -- python path/to/mcp_server.py
```

## What Changes

The agent still talks to a stdio MCP server. AION becomes the command in the middle:

```text
agent -> aion-mcp-firewall -> original MCP server
```

## What AION Inspects

AION inspects JSON-RPC messages where:

```json
{"method":"tools/call"}
```

Non-tool messages pass through.

## What AION Logs

Each tool call produces a receipt with:

- timestamp
- agent id
- owner/team
- request id
- tool name
- decision
- rule id
- reason
- argument fingerprint

## Filesystem MCP Example

See [Filesystem MCP Example](FILESYSTEM_MCP_EXAMPLE.md) for a concrete wrapper command using `@modelcontextprotocol/server-filesystem`.

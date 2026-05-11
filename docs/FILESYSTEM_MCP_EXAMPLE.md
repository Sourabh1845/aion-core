# Filesystem MCP Example

This example shows how AION can wrap a real filesystem MCP server.

The upstream server is `@modelcontextprotocol/server-filesystem`, a Node.js MCP server that exposes filesystem tools such as reading, writing, editing, moving, and listing files. Tool names can vary across package versions, so keep your AION policy aligned with the exact server version you use.

## Installed AION Command

After installing AION Core locally:

```powershell
aion-mcp-firewall --policy examples/policies/stage6-default.json --receipt-log receipts/filesystem.jsonl --agent-id local-agent --owner local-dev -- npx -y @modelcontextprotocol/server-filesystem "C:\Users\SOURABH RANJAN"
```

## Source Checkout Command

Without installing:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.cli --policy examples/policies/stage6-default.json --receipt-log receipts/filesystem.jsonl --agent-id local-agent --owner local-dev -- npx -y @modelcontextprotocol/server-filesystem "C:\Users\SOURABH RANJAN"
```

## Client Config Templates

See:

- `examples/integrations/claude_desktop_filesystem_aion.json`
- `examples/integrations/local_python_filesystem_aion.json`

## Policy Notes

Filesystem MCP servers often expose powerful tools:

- read files
- write files
- edit files
- move files
- list directories
- inspect metadata

For early testing, AION should at minimum block:

- destructive shell-like patterns
- secret exfiltration patterns
- risky write/edit/move/delete operations in sensitive directories

Stage 6 currently proves the runtime firewall path. Stage 6.2 should add deeper tool-aware policies for specific MCP servers.

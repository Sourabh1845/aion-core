# Architecture

AION Stage 6 is a stdio MCP firewall proxy.

```text
stdin from agent
  |
  v
AION firewall
  |
  |-- parse JSON-RPC
  |-- inspect tools/call
  |-- evaluate policy
  |-- write receipt
  |
  +-- block response to agent
  |
  v
upstream MCP server
```

## Modules

- `aion_core.cli`: command-line entry point.
- `aion_core.firewall`: stdio proxy and MCP request inspection.
- `aion_core.policy`: dependency-free JSON policy engine.
- `aion_core.receipts`: JSONL receipt writer.
- `aion_core.demo`: one-command public demo runner.

## Policy Decision Flow

1. Parse one JSON-RPC line.
2. Ignore non-`tools/call` messages.
3. Extract tool name and arguments.
4. Evaluate rules in order.
5. Return first matching allow/block rule.
6. Fall back to `default_action`.
7. Write receipt with decision, rule, tool, owner, agent id, and argument fingerprint.

## Block Response

Blocked calls return a JSON-RPC error:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32090,
    "message": "AION firewall blocked this MCP tool call."
  }
}
```

## Design Constraints

- Keep the MVP dependency-free.
- Keep policies readable as JSON.
- Keep receipts append-only JSONL.
- Keep the proxy generic so any stdio MCP server can sit behind it.

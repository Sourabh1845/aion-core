# AION Receipts

AION receipts are structured audit records for agent actions.

Stage 2 formalizes receipts so AION Core, MCP Firewall, AION Cloud, and future compliance exports can share one format.

## Receipt Schema

Each receipt is a JSON object written as one line in a JSONL file.

Required fields:

- `schema_version`
- `receipt_id`
- `ts`
- `stage`
- `component`
- `agent_id`
- `owner`
- `action_type`
- `tool`
- `decision`
- `rule_id`
- `reason`
- `risk`
- `request_id`
- `argument_fingerprint`
- `metadata`
- `hash_algorithm`
- `receipt_hash`

## Example

```json
{
  "schema_version": "aion.receipt.v1",
  "receipt_id": "rcpt_...",
  "stage": "mcp-firewall",
  "component": "aion-mcp-firewall",
  "agent_id": "demo-agent",
  "owner": "demo-team",
  "action_type": "mcp.tools_call",
  "tool": "shell",
  "decision": "block",
  "rule_id": "block-destructive-shell",
  "reason": "Destructive shell command patterns require explicit approval.",
  "risk": "blocked",
  "argument_fingerprint": "0f3a3e474e790925",
  "hash_algorithm": "sha256",
  "receipt_hash": "..."
}
```

## Verify Receipts

```powershell
$env:PYTHONPATH='src'
python -m aion_core.receipt_cli verify aion-demo-output\receipts.jsonl
```

Expected:

```text
OK: verified 5 receipt(s)
```

## Inspect Receipts

```powershell
$env:PYTHONPATH='src'
python -m aion_core.receipt_cli inspect aion-demo-output\receipts.jsonl
```

This prints a summary by decision, rule, and tool.

## Tamper Detection

The `receipt_hash` is computed from the canonical receipt body. If a receipt is edited after being written, verification fails.

This is not yet tamper-proof storage. It is a local integrity layer. Future AION Cloud work should add server-side storage, signing, and stronger audit guarantees.

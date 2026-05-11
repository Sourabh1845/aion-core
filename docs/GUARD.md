# AION Guard

AION Guard is the generic runtime action control layer.

MCP Firewall is one integration. Guard is the underlying idea:

```text
agent action -> AION Guard -> allow/block -> receipt
```

## What Guard Checks

A Guard request has:

- `action_type`: category such as `shell.command`, `file.read`, `http.request`, `cloud.delete`
- `tool`: tool or target name
- `arguments`: action arguments
- `agent_id`: agent identity
- `owner`: user/team identity
- `metadata`: optional context

## CLI

Allowed safe action:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.guard_cli check --policy examples\policies\stage6-default.json --receipt-log receipts\guard.jsonl --action-type file.read --tool read_file --arguments-file examples\actions\safe_read_args.json --agent-id demo --owner local
```

Blocked dangerous action:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.guard_cli check --policy examples\policies\stage6-default.json --receipt-log receipts\guard.jsonl --action-type shell.command --tool shell --arguments-file examples\actions\destructive_shell_args.json --agent-id demo --owner local
```

## Policy Matchers

Guard uses the same JSON policy engine as MCP Firewall.

Supported matchers:

- `action_type`
- `tool`
- `owner`
- `argument_contains`
- `argument_regex`

## Receipts

Every Guard decision writes an `aion.receipt.v1` receipt.

That means Guard decisions can flow into AION Cloud later without inventing another audit format.

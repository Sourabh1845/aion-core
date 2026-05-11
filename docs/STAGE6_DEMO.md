# Stage 6 Demo Guide

This demo proves AION's core infrastructure loop:

```text
AI Agent -> AION Firewall -> MCP Tool
```

## Run

```powershell
$env:PYTHONPATH='src'
python -m aion_core.demo
```

The demo runs three cases:

1. A dangerous shell command is blocked.
2. A secret exfiltration attempt is blocked.
3. A safe read-style tool call is allowed.

## What To Show In A Video

1. Open the repo.
2. Run `python -m aion_core.demo`.
3. Point to the blocked shell call.
4. Point to the allowed safe call.
5. Open `aion-demo-output/receipts.jsonl`.
6. Say: "AION controls what AI agents can do and leaves an audit trail."

## Why This Is Infrastructure

AION is not the agent and not the tool. AION is the control layer between them.

That position lets AION expand into:

- team-wide policy
- agent identity
- compliance exports
- receipt vaults
- tool and agent risk scoring

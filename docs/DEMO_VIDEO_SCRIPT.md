# 60-90 Second Demo Video Script

## Opening

"This is AION Core, a runtime security layer for AI agent actions."

"AI agents are starting to call tools that can touch files, shells, APIs, and internal systems. AION sits between the agent and the action."

## Show Command

```powershell
$env:PYTHONPATH='src'
python -m aion_core.demo
```

## Show Result

Point to:

```text
[PASS] blocked destructive shell command
[PASS] blocked secret exfiltration
[PASS] allowed safe read
[PASS] scan detected unprotected MCP server
[PASS] team policy required approval
```

Say:

"AION Scan detects unprotected MCP servers before runtime."

"AION Guard blocks generic risky actions."

"AION Team Policy turns production mutations into approval requests."

"The agent attempted a destructive shell command. AION blocked it before it reached the tool."

"The agent attempted to send a password-like value out through an HTTP tool. AION blocked that too."

"A safe read-style call was allowed."

## Show Receipts

Open:

```text
aion-demo-output/receipts.jsonl
```

Say:

"Every decision creates a hash-verified receipt with the agent id, owner, tool, decision, rule id, reason, and timestamp."

## Closing

"AION Core is the open-source infrastructure layer. AION Cloud will become the hosted receipt vault, team policy dashboard, and compliance control plane."

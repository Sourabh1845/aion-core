# Launch Post Draft

I am launching AION Core, an open-source runtime security layer for AI agents.

As agents start using MCP servers and tools that can touch files, shells, APIs, and internal systems, teams need a control layer between the agent and the action.

AION Core `0.8.0` is the first infrastructure MVP:

- guards generic agent actions
- scans MCP configs and policies for weak coverage
- intercepts MCP `tools/call`
- blocks risky actions by policy
- allows safe actions
- writes hash-verified JSONL audit receipts
- creates approval-required team policy decisions
- connects receipts to an AION Cloud control panel MVP

Demo:

```powershell
pip install aion-core
aion-demo
```

Local source demo:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.demo
```

It demonstrates:

- unprotected MCP server detection
- destructive shell command blocked
- secret exfiltration blocked
- safe read allowed
- team approval-required decision created
- receipts generated and hash-verified

The goal: make AION the trust and security layer for AI agents.

Looking for feedback from MCP builders, agent framework developers, security engineers, and teams testing agents with real tool access.

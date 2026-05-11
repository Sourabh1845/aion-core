# AION Proof Pack

The AION Proof Pack is a deterministic set of agent-workflow tests that prove
AION Core handles real risk patterns before larger public outreach.

These tests do not call paid or external APIs. They model the tool-call shapes
used by agent systems and route them through AION Core policy, receipt, scan,
and team-approval paths.

## Run

From the repo root:

```powershell
$env:PYTHONPATH='src'
python examples\proof_pack\agent_workflow_proof.py
```

Expected:

```text
AION Core Agent Workflow Proof Pack
Scenarios: 6/6 passed
Receipts: 5 hash-verified
```

Output:

```text
proof-output/proof_results.json
proof-output/receipts.jsonl
proof-output/approvals.jsonl
```

## Scenarios

| Agent workflow | Scenario | Expected |
|---|---|---|
| LangChain-style tool agent | destructive shell command | blocked |
| LangChain-style tool agent | safe file read | allowed |
| CrewAI-style research agent | secret exfiltration through HTTP tool | blocked |
| CrewAI-style operations agent | production delete task | approval required |
| Groq function-calling agent | safe summarization function call | allowed |
| Raw MCP configuration | unprotected filesystem server | high scan finding |

## What This Proves

- AION can evaluate tool-call payloads that look like real agent actions.
- AION can block destructive shell commands.
- AION can block secret exfiltration attempts.
- AION can allow safe tool calls.
- AION can require approval for production mutations.
- AION can detect weak MCP configuration coverage.
- AION writes hash-verified receipts for runtime decisions.

## Why No External API Calls

The public proof pack is deterministic so contributors and users can run it
without API keys, paid services, or network access.

Optional SDK-level tests for LangChain, CrewAI, and Groq can be added later as
separate integration tests gated behind installed dependencies and API keys.

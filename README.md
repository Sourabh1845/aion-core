# AION Core

Runtime action control, receipt, scan, approval, and firewall layer for AI agents.

AION Core is an open-source infrastructure prototype for AI systems that call
real tools. It sits between an agent and external tools/APIs, checks the action
against policy, blocks dangerous calls, records verifiable receipts, and marks
sensitive actions for human approval.

```text
AI Agent -> AION Guard / MCP Firewall -> Tool/API/System
                                  |
                                  +-> verified JSONL receipt log
```

## Thesis

AI is moving from chat to action. Agents can call tools, write files, send
messages, use APIs, update business systems, and coordinate workflows. Before
that becomes safe at scale, teams need a control layer that can answer:

- what is the agent allowed to do?
- what must be blocked?
- what needs human approval?
- what evidence should be recorded?
- what can an operator inspect later?

AION Core is the first working version of that layer.

## 8-Stage MVP Status

The first AION Core MVP covers all 8 planned stages:

| Stage | Layer | MVP Status |
|---|---|---|
| 1 | AION Guard | Complete: runtime action policy and allow/block decisions. |
| 2 | AION Receipts | Complete: hash-verifiable decision evidence. |
| 3 | AION Scan | Complete: MCP and policy risk discovery. |
| 4 | Docs + Demo | Complete: one-command local demo and proof path. |
| 5 | Cloud Alignment | Complete for alignment MVP: `aion.receipt.v1` bundle accepted by cloud/control surfaces. |
| 6 | MCP Firewall | Complete: stdio MCP tool-call firewall. |
| 7 | Team Policy / Approvals | Complete for MVP: approval-required decisions and Slack-ready payloads. |
| 8 | Control Panel | Complete for MVP: summary and pending-approval operator views. |

See [Stage status](docs/STAGE_STATUS.md).

## Install

```powershell
python -m pip install aion-core
```

For local development:

```powershell
python -m pip install -e .
```

## One-Command Demo

From PyPI/local install:

```powershell
aion-demo
```

From the repository:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.demo
```

Expected result:

```text
[PASS] scan detected unprotected MCP server
[PASS] guard blocked generic shell action
[PASS] guard allowed generic safe read
[PASS] team policy required approval
[PASS] blocked destructive shell command
[PASS] blocked secret exfiltration
[PASS] allowed safe read
Receipts written to: aion-demo-output/receipts.jsonl
Approvals written to: aion-demo-output/approvals.jsonl
Receipt verification: PASS (6 receipt(s), hash-verified)
```

## Commands

```text
aion-demo
aion-mcp-firewall
aion-guard
aion-receipts
aion-scan
aion-team
```

## Run Guard

Check a generic action:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.guard_cli check --policy examples\policies\stage6-default.json --receipt-log receipts\guard.jsonl --action-type shell.command --tool shell --arguments-file examples\actions\destructive_shell_args.json --agent-id demo --owner local
```

## Run The MCP Firewall

Run AION in front of any stdio MCP server:

```powershell
aion-mcp-firewall --policy examples/policies/stage6-default.json --receipt-log receipts/aion.jsonl -- python path/to/mcp_server.py
```

For local development without installing:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.cli --policy examples/policies/stage6-default.json --receipt-log receipts/aion.jsonl -- python path/to/mcp_server.py
```

## Receipt Verification

Verify a JSONL receipt log:

```powershell
aion-receipts verify receipts\aion.jsonl
```

Inspect a receipt summary:

```powershell
aion-receipts inspect receipts\aion.jsonl
```

## Proof Pack

AION Core includes deterministic agent-workflow proof tests that model
LangChain, CrewAI, Groq function-calling, and raw MCP workflows.

```powershell
$env:PYTHONPATH='src'
python examples\proof_pack\agent_workflow_proof.py
```

Expected result:

```text
AION Core Agent Workflow Proof Pack
Scenarios: 6/6 passed
Receipts: 5 hash-verified
```

## Real SDK Tests

Verified integration tests include:

- LangChain `1.2.18`: real `StructuredTool` guard test passed.
- CrewAI `1.14.4`: real `Agent`, `Task`, and `BaseTool` guard test passed.
- Groq `1.2.0`: real live function-calling test passed with `llama-3.1-8b-instant`.

## Real-World Capacity Tests

AION Core includes end-to-end real-world capacity tests that exercise all 8 MVP
layers together.

```powershell
$env:PYTHONPATH='src'
python examples\real_world_capacity\release_ops_capacity_test.py --output-dir test-output\real-world-final
```

Verified results:

```text
AION Real-World Capacity Test: 8/8 passed, 5 hash-verified receipts, 1 pending approval
Hardcore single-agent support workflow: 9/9 passed, 6 hash-verified receipts, 1 pending approval
Hardcore multi-agent incident response: 10/10 passed, 7 hash-verified receipts, 1 pending approval
```

## Development

Run tests:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

Useful docs:

- [Stage status](docs/STAGE_STATUS.md)
- [AION Guard](docs/GUARD.md)
- [AION Receipts](docs/RECEIPTS.md)
- [AION Scan](docs/SCAN.md)
- [AION Proof Pack](docs/PROOF_PACK.md)
- [Real agent test plan](docs/REAL_AGENT_TESTS.md)
- [Real SDK integrations](docs/REAL_SDK_INTEGRATIONS.md)
- [Real-world capacity test](docs/REAL_WORLD_CAPACITY_TEST.md)
- [Team policy and approvals](docs/TEAM_POLICY_APPROVALS.md)
- [Stage 5 Cloud alignment](docs/STAGE5_CLOUD_ALIGNMENT.md)
- [AION Cloud control panel](docs/STAGE8_CONTROL_PANEL.md)
- [Stage 6 completion report](docs/STAGE6_COMPLETION_REPORT.md)
- [Repo structure](docs/REPO_STRUCTURE.md)
- [Install](docs/INSTALL.md)
- [Real MCP integration](docs/REAL_MCP_INTEGRATION.md)
- [Filesystem MCP example](docs/FILESYSTEM_MCP_EXAMPLE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Verification](docs/VERIFICATION.md)
- [Roadmap](docs/ROADMAP.md)

## Current Scope

Current core scope:

- generic Guard action checks
- MCP config and policy scanning
- stdio MCP firewall proxy
- runtime policy checks for `tools/call`
- MCP-compatible JSON-RPC block responses
- hash-verified JSONL audit receipts
- optional HMAC-signed receipt verification
- team approval-required policy decisions
- AION Cloud control panel summary and pending approval views
- dependency-free Python core

Next infrastructure layers:

- hosted API server
- hosted auth and tenant model
- cloud receipt vault
- tenant-scoped signing key management
- real Slack/webhook approval delivery
- enterprise audit exports
- hardened policy engine

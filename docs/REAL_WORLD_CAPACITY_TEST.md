# Real-World Capacity Tests

AION Core includes three real-world capacity tests.

## 1. Release Ops Agent

```text
An AI release-ops agent is preparing a production release.
AION must scan weak MCP config, allow safe reads, block destructive shell
actions, require approval for production mutation, verify receipts, and produce
cloud/control-panel evidence.
```

## Run

```powershell
$env:PYTHONPATH='src'
python examples\real_world_capacity\release_ops_capacity_test.py --output-dir test-output\real-world-final
```

Verified result:

```text
AION Real-World Capacity Test
Workflow: release ops agent production readiness
Scenarios: 8/8 passed
Receipts: 5 hash-verified
Pending approvals: 1
```

## 2. Hardcore Single-Agent Support Workflow

Scenario:

```text
A customer support AI agent has access to ticket lookup, CRM export, HTTP, MCP,
and account admin tools. AION must allow safe lookups, block sensitive export
and secret exfiltration, require approval for account deletion, verify receipts,
and produce cloud/control-panel evidence.
```

Run:

```powershell
$env:PYTHONPATH='src'
python examples\real_world_capacity\support_agent_capacity_test.py --output-dir test-output\single-agent-final
```

Verified result:

```text
AION Hardcore Single-Agent Capacity Test
Workflow: customer support sensitive data resolution
Scenarios: 9/9 passed
Receipts: 6 hash-verified
Pending approvals: 1
```

## 3. Hardcore Multi-Agent Incident Response

Scenario:

```text
A planner agent, research agent, coding agent, and ops agent collaborate on a
production incident workflow. AION must apply per-agent controls, block risky
actions, require approval for production changes, verify receipts, and produce a
team-level control-panel summary.
```

Run:

```powershell
$env:PYTHONPATH='src'
python examples\real_world_capacity\multi_agent_capacity_test.py --output-dir test-output\multi-agent-final
```

Verified result:

```text
AION Hardcore Multi-Agent Capacity Test
Workflow: multi-agent incident response
Agents: planner-agent, research-agent, coding-agent, ops-agent
Scenarios: 10/10 passed
Receipts: 7 hash-verified
Pending approvals: 1
```

## Stages Covered

| AION layer | What these tests prove |
|---|---|
| AION Guard | Safe actions are allowed; destructive and exfiltration actions are blocked. |
| AION Receipts | Runtime decisions produce hash-verified `aion.receipt.v1` receipts. |
| AION Scan | Weak/unprotected MCP configs are detected before workflow use. |
| Docs + Demo | Machine-readable capacity reports are generated. |
| AION Cloud alignment | A Cloud-compatible receipt upload bundle is produced. |
| MCP Firewall | Safe MCP calls are allowed; risky MCP calls are blocked. |
| Team Policy | Sensitive production/account actions require approval. |
| Control Panel | Operator summaries show blocks, per-agent risk, and pending approvals. |

## Artifacts

The test writes:

```text
capacity_report.json
receipts.jsonl
approvals.jsonl
cloud_receipt_bundle.json
control_panel_summary.json
```

These files are ignored by Git because they are generated proof artifacts.

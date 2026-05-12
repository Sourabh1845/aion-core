# Real-World Capacity Test

This test verifies AION Core against a realistic release-ops agent workflow.

Scenario:

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

## Stages Covered

| AION layer | What the test proves |
|---|---|
| AION Guard | Safe release read is allowed; destructive shell cleanup is blocked. |
| AION Receipts | Runtime decisions produce hash-verified `aion.receipt.v1` receipts. |
| AION Scan | Weak/unprotected release MCP config is detected before workflow use. |
| Docs + Demo | A machine-readable capacity report is generated. |
| AION Cloud alignment | A Cloud-compatible receipt upload bundle is produced. |
| MCP Firewall | Safe MCP read is allowed; destructive MCP shell call is blocked. |
| Team Policy | Production deployment mutation requires approval. |
| Control Panel | Operator summary shows blocks and pending approval. |

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

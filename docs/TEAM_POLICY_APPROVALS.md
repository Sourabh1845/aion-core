# Team Policy And Approvals

AION team policy adds an approval layer above individual agent actions.

It can return:

- `allow`
- `block`
- `approval_required`

## CLI

```powershell
$env:PYTHONPATH='src'
python -m aion_core.team_cli check --team-policy examples\team_policies\stage7-default.json --receipt-log receipts\team.jsonl --approval-log receipts\approvals.jsonl --action-type cloud.delete --tool aws --arguments-file examples\actions\production_delete_args.json --agent-id demo --owner local --team-id demo-team
```

Expected decision:

```json
{"decision":"approval_required"}
```

## Approval Requests

When approval is required, AION writes:

- a verified `aion.receipt.v1` receipt
- an `aion.approval.v1` approval request
- a Slack webhook-ready payload

## Approval Events

```powershell
$env:PYTHONPATH='src'
python -m aion_core.team_cli approve --approval-log receipts\approvals.jsonl --approval-id appr_example --approver security --status approved --reason "Approved for controlled rollout."
```

## Current Limits

This is the core MVP. It does not yet send Slack messages or enforce remote approval state. It creates the policy decision, approval request, and payload needed for Stage 8 control panel and future integrations.

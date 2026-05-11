# Stage 5 Cloud Alignment

Status: complete for alignment MVP.

AION Cloud now accepts `aion.receipt.v1` receipts from AION Core.

## What Changed

AION Cloud `/receipts` can accept receipts produced by:

- AION Guard
- AION MCP Firewall
- AION Core demo

Cloud verifies Core receipts before storage:

- `schema_version` must be `aion.receipt.v1`
- `hash_algorithm` must be `sha256`
- `receipt_hash` must match the canonical Core receipt payload

Valid Core receipts are stored with:

- `status=verified`
- `agent_id` mapped to Cloud `agent`
- `action_type` mapped to Cloud `scope`
- full receipt stored in `metadata.aion_core_receipt`

## Verified

Using a real receipt from AION Core:

```text
verified demo-agent shell.command aion.receipt.v1
```

Tampered receipt:

```text
tamper rejected 400
```

## Remaining Cloud Work

This completes schema alignment, not the full Cloud product.

Still pending:

- production deployment verification
- dashboard polish
- bulk receipt upload
- team/org model
- compliance exports
- billing plan enforcement beyond current MVP

# Stage Status

Current source of truth for the 8-stage AION Core plan.

AION Core is **MVP-complete across all 8 stages**. That means the core proof
exists and can be demonstrated locally. It does not mean the company is already
production SaaS. Production work remains: hosted auth, signed receipts, billing,
multi-tenant controls, and enterprise deployment hardening.

| Stage | Name | Status | Notes |
|---|---|---|---|
| 1 | AION Guard | Complete for core MVP | Generic action checks, policy decisions, CLI, and receipts exist. |
| 2 | AION Receipts | Complete for core MVP | Receipt schema, hash, verify CLI, inspect CLI, and firewall integration exist. |
| 3 | AION Scan | Complete for core MVP | Scans MCP configs and policies for unprotected servers and weak coverage. |
| 4 | Docs + Demo | Complete for core MVP | Unified demo covers Scan + Guard + Team Policy + Receipts + MCP Firewall. |
| 5 | AION Cloud | Complete for alignment MVP | Cloud accepts and verifies `aion.receipt.v1`; full SaaS features still pending. |
| 6 | MCP Firewall | Complete | Public-demo and early-user launch package complete. |
| 7 | Team/Slack/Approvals | Complete for core MVP | Team policy, approval-required decisions, approval logs, and Slack-ready payloads exist. |
| 8 | Control Panel | Complete for MVP | Cloud summary endpoint, pending approvals endpoint, and dashboard UI exist. |

## Next Recommended Work

1. Interview-ready framing: AION Core is the infrastructure thesis; LaunchShield and VibeOps are applied proof surfaces.
2. Production hardening: auth boundaries, hosted DB migrations, signed receipts, and real Slack/webhook delivery.
3. Distribution wedge: use VibeOps to prove safe AI actions in real small-business workflows.

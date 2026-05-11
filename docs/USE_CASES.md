# Early Use Cases

## Coding Agent Firewall

Problem: coding agents can run shell commands, edit files, install packages, or call deployment scripts.

AION policy can block:

- destructive shell commands
- secret exfiltration
- production deploy commands
- risky git operations

## Cloud Agent Firewall

Problem: cloud automation agents can delete resources or mutate production infrastructure.

AION policy can block:

- `delete`
- `terminate`
- `destroy`
- production mutations

## Internal Tool Agent Firewall

Problem: internal agents can touch CRMs, databases, support tools, and admin APIs.

AION policy can block:

- access to sensitive user records
- irreversible account actions
- risky bulk exports
- unapproved admin actions

## Compliance And Audit

Problem: security teams need to know what agents attempted, what was blocked, and what was allowed.

AION receipts provide:

- agent id
- owner/team
- tool name
- allow/block decision
- matching policy rule
- timestamp
- argument fingerprint

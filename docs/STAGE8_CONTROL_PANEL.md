# Stage 8 Control Panel

Stage 8 connects AION Core receipts to the AION Cloud control panel MVP.

## What Exists

- `GET /control-panel/summary`
  - total receipt count
  - decision counts
  - risk counts
  - verification status counts
  - stage counts
  - action type counts
  - pending approval count
- `GET /approvals`
  - approval-required receipts
  - pending approval receipts
  - receipt metadata needed by a reviewer
- Cloud dashboard button: `Load Control Panel`
  - summary cards
  - stage breakdown
  - pending approval list

## Why It Matters

This turns AION from only a local firewall/demo into the beginning of an
operator control plane:

```text
AI Agent -> AION Core -> verified receipt -> AION Cloud -> control panel
```

The MVP is intentionally simple. It proves the product direction:
teams can see agent decisions, blocked actions, and approval-required actions
from a cloud dashboard.

## Still Pending For Production

- real Slack/webhook approval delivery
- reviewer identity and approval audit trail in Cloud
- organization/team separation
- hosted database migrations
- signed receipts
- richer filters and exports

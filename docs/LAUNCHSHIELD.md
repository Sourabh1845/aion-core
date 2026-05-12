# AION LaunchShield

AION LaunchShield is a browser-based first-pass risk scanner for AI agents and
AI-built apps.

It is designed as AION's first distribution and feedback surface:

- free browser scan for distribution
- report export for feedback loops
- manual review path after real usage and case studies

## What It Scans

Users can paste:

- agent prompts and workflow notes
- tool/API lists
- MCP config snippets
- deployment/auth notes
- AI-built app launch notes

LaunchShield returns:

- launch risk score
- priority findings
- launch blockers
- risky tool-combination chains
- parsed MCP server signals when valid JSON is provided
- scanner confidence
- simulated AION allow/block/approval decisions
- covered security checks
- hash-style browser evidence log
- downloadable Markdown audit report

## Current Engine

The public scanner is still local and heuristic, but it now does more than a
flat keyword checklist:

- parses `mcpServers` JSON when pasted
- detects shell-capable MCP servers
- detects broad filesystem roots
- detects secret-looking MCP environment keys
- detects chains such as secrets + outbound tools, untrusted content + database
  writes, public endpoints + sensitive data, and MCP + shell/filesystem access

## Pilot Path

| Step | Purpose |
|---|---|
| Free scan | Top findings, score, covered checks, and exportable report. |
| Founder feedback | Collect real examples, false positives, and report improvements. |
| Manual review | Open paid reviews after case studies and a clear delivery workflow. |

## Public URL

GitHub Pages:

```text
https://sourabh1845.github.io/aion-core/launchshield.html
```

## Revenue Logic

LaunchShield keeps monetization aligned with AION Core:

```text
Free scan -> feedback -> real workflow proof -> paid review -> AION Cloud features
```

This avoids splitting focus into an unrelated consumer product while still
creating a direct path to trust and later revenue.

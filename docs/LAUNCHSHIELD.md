# AION LaunchShield

AION LaunchShield is a browser-based first-pass risk scanner for AI agents and
AI-built apps.

It is designed as AION's first distribution and revenue surface:

- free browser scan for distribution
- report export for feedback loops
- manual launch fix plan request for early paid service

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
- manual launch-review request brief

## Current Engine

The public scanner is still local and heuristic, but it now does more than a
flat keyword checklist:

- parses `mcpServers` JSON when pasted
- detects shell-capable MCP servers
- detects broad filesystem roots
- detects secret-looking MCP environment keys
- detects chains such as secrets + outbound tools, untrusted content + database
  writes, public endpoints + sensitive data, and MCP + shell/filesystem access

## User Flow

| Step | Purpose |
|---|---|
| Free scan | User pastes workflow, tools, MCP config, or launch notes. |
| Export report | User gets blockers, risk chains, findings, evidence log, and fixes. |
| Request fix plan | User emails or copies a review request with the scan summary attached. |
| Manual delivery | AION replies with scope, payment link, and the fix-plan delivery timeline. |

## Revenue Path

LaunchShield includes a manual launch fix request flow:

- Beta Review: `$29`
- Launch Fix Plan: `$99`
- Team Review: `$299+`

The scanner creates an email-ready request with the score, launch blockers,
risk chains, top findings, and user context. Payment is handled after scope
confirmation until a formal checkout is added. Users are not paying for the
free scanner alone; they pay for the human-reviewed launch verdict and fix plan.

## Public URL

GitHub Pages:

```text
https://sourabh1845.github.io/aion-core/launchshield.html
```

Sample fix plan:

```text
https://sourabh1845.github.io/aion-core/launchshield-sample-report.html
```

## Local CLI

After installing AION Core `0.8.2` or running from the repository:

```powershell
aion-launchshield --project-name "My Agent" --workflow-file workflow.txt --tools-file tools.txt --mcp-config-file mcp.json --surface MCP --control receipts --output launchshield-report.md
```

JSON output:

```powershell
aion-launchshield --workflow-file workflow.txt --tools-file tools.txt --mcp-config-file mcp.json --surface MCP --json
```

Fail CI when launch blockers are found:

```powershell
aion-launchshield --workflow-file workflow.txt --tools-file tools.txt --mcp-config-file mcp.json --surface MCP --fail-on-blocker
```

## Revenue Logic

LaunchShield keeps monetization aligned with AION Core:

```text
Free scan -> report -> fix-plan request -> paid review -> AION Cloud features
```

This avoids splitting focus into an unrelated consumer product while still
creating a direct path to trust and later revenue.

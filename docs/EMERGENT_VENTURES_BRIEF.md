# Emergent Ventures Interview Brief

## One-Sentence Answer

AION started as trust infrastructure for AI agents: a control layer that sits
between AI systems and real-world tools, deciding what can run, what needs
approval, what must be blocked, and what evidence should be recorded.

## The Clean Story

I applied with AION as an AI agent trust/security infrastructure idea.

Since applying, I built the first open-source core MVP:

- Guard: runtime action control
- Receipts: verifiable evidence logs
- Scan: MCP/policy risk discovery
- Docs + Demo: one-command proof path
- Cloud alignment: common receipt format
- MCP Firewall: tool-call firewall
- Team Policy: approval-required decisions
- Control Panel: operator summary and pending approvals

Then I started building applied proof surfaces:

- LaunchShield: scan an AI agent/app workflow before launch
- VibeOps: a small-business operations app where AI turns voice/text into jobs,
  payments, receipts, and summaries with approval and evidence

This is not a pivot away from the original idea. It is the same thesis moving
from abstract infrastructure into real workflows.

## Why This Matters Now

AI is moving from chat to action. Agents can call tools, write files, send
messages, query databases, update CRMs, trigger payments, and coordinate
workflows.

That creates a missing infrastructure layer:

- permissioning
- human approval
- audit evidence
- tool risk scoring
- operator visibility
- safe fallback when an agent is uncertain

AION is meant to become that control layer.

## What Exists Today

Open-source AION Core:

- package published on PyPI as `aion-core`
- GitHub repository and public docs
- one-command demo
- MCP firewall
- receipt verification
- scan CLI
- team approval decisions
- real SDK proof tests for LangChain, CrewAI, Groq, and MCP-style workflows
- real-world capacity tests for single-agent and multi-agent workflows

Public apps:

- AION LaunchShield: first-pass launch risk scanner
- AION VibeOps: global-beta applied product for small service businesses

## How To Explain VibeOps

VibeOps is not replacing AION Core.

VibeOps is a distribution wedge and applied proof environment:

```text
Owner command -> AION parses intent -> approval -> job/payment/receipt/report
```

It demonstrates the same idea in a concrete setting:

- AI takes action
- sensitive actions require confirmation
- business memory is maintained
- every important action can create evidence
- the operator remains in control

## What The Grant Helps With

The grant would help me continue full-time work on AION and move from MVP proof
to real deployment:

1. harden AION Core
2. test AION in real workflows through VibeOps
3. add hosted auth/database/signed receipts
4. build stronger integrations around MCP and agent frameworks
5. run real pilots with small businesses and AI builders

## 20-Minute Call Structure

1. Who I am and why I am building AION.
2. Original thesis: AI needs a trust/control layer before it can safely act.
3. What I built: AION Core 8-stage MVP and proof tests.
4. What I learned: infrastructure needs real workflows to prove value.
5. Applied wedge: LaunchShield and VibeOps.
6. Ask: support to harden the core and test it in real-world workflows.

## Do Not Say

- "I changed the idea completely."
- "I am chasing money."
- "I want a trillion-dollar company."
- "I built random things."
- "I am confused."

## Say Instead

- "The original infrastructure thesis is intact."
- "I moved fast and built proof."
- "VibeOps is the first applied wedge."
- "The long-term goal is a standard trust layer for AI actions."
- "I am using real workflows to learn what the infrastructure must support."

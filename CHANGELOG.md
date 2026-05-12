# Changelog

## 0.8.2

LaunchShield CLI release.

- Added `aion-launchshield` CLI for local AI agent/app launch-risk scans.
- Added Python LaunchShield scanner engine with MCP config parsing.
- Added risky tool-combination detection and launch blockers.
- Added JSON and Markdown report export.
- Added unit tests for MCP shell/filesystem risk, thin input, invalid MCP JSON, and CLI output.

## 0.8.1

Proof and launch hardening release.

- Added real LangChain SDK integration test.
- Added real CrewAI SDK integration test.
- Added Groq live function-calling verification.
- Added release-ops real-world 8-stage capacity test.
- Added hardcore single-agent customer support capacity test.
- Added hardcore multi-agent incident response capacity test.
- Updated website/docs to use real test claims instead of framework-style claims.

## 0.8.0

Initial AION Core infra MVP through Stage 8.

- Added stdio MCP firewall proxy.
- Added JSON policy engine.
- Added JSONL receipt logging.
- Added one-command public demo.
- Added attack examples for destructive shell and secret exfiltration.
- Added public docs for architecture, demo, roadmap, and early launch.
- Renamed the package to `aion_core` for clean AION Core positioning.
- Added filesystem MCP integration templates.
- Added formal `aion.receipt.v1` receipt schema.
- Added receipt hashes and verification CLI.
- Added AION Guard generic runtime action control and CLI.
- Added AION Scan for MCP configs and policy files.
- Aligned AION Cloud with `aion.receipt.v1` receipt verification.
- Added team policy, approval request logs, and Slack-ready approval payloads.
- Added Stage 8 AION Cloud control panel summary and pending approval views.

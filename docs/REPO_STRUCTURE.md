# Repo Structure

AION should stay simple at the repo level.

## AION Core

This repo contains the open-source infrastructure layer:

- MCP firewall
- policy engine
- receipts
- guard/runtime controls
- scan/risk discovery
- SDK/CLI
- integration examples

Stage 6 lives here.

## AION Cloud

`aion-cloud` should be a separate repo or folder for hosted product work:

- dashboard
- receipt vault
- auth
- organizations
- billing
- compliance exports
- team control panel

Cloud depends on Core. Core should not depend on Cloud.

## Product Names

Product/module names can stay inside AION Core:

- AION Guard
- AION Receipts
- AION Scan
- AION MCP Firewall
- AION Team Policy

These are features/modules, not separate repos.

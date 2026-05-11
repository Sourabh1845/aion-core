# GitHub Launch Checklist

Recommended repository: `Sourabh1845/aion-core`

## Repository Setup

```powershell
cd C:\Users\SOURABH RANJAN\aion-core
git init
git branch -M main
git add .
git commit -m "Launch AION Core 0.8.0"
git remote add origin https://github.com/Sourabh1845/aion-core.git
git push -u origin main
```

## GitHub Settings

- Add description:
  - `Runtime security layer for AI agents: MCP firewall, Guard, Scan, receipts, team approvals.`
- Add topics:
  - `ai-agents`
  - `mcp`
  - `security`
  - `firewall`
  - `agent-security`
  - `audit-logs`
- Enable GitHub Pages:
  - Source: `Deploy from a branch`
  - Branch: `main`
  - Folder: `/docs`
- Create release:
  - Tag: `v0.8.0`
  - Title: `AION Core 0.8.0`

## Release Notes

```text
AION Core 0.8.0 is the first public infrastructure MVP.

Includes:
- AION Guard runtime action checks
- AION Receipts hash-verified audit logs
- AION Scan for MCP configs and weak policies
- MCP Firewall stdio proxy
- Team policy approval-required decisions
- AION Cloud receipt/control-panel alignment
- One-command demo: aion-demo
```

## Smoke Test After Push

```powershell
git clone https://github.com/Sourabh1845/aion-core.git
cd aion-core
$env:PYTHONPATH='src'
python -m unittest discover -s tests
python -m aion_core.demo
```

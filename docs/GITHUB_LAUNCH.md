# GitHub Launch Checklist

Recommended repository: `Sourabh1845/aion-core`

## Repository Setup

```powershell
cd C:\Users\SOURABH RANJAN\aion-core
git init
git branch -M main
git add .
git commit -m "Launch AION Core 0.8.2"
git remote add origin https://github.com/Sourabh1845/aion-core.git
git push -u origin main
git push origin v0.8.2
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
  - Tag: `v0.8.2`
  - Title: `AION Core 0.8.2`
- Add repository secret for PyPI publishing:
  - Name: `PYPI_API_TOKEN`
  - Value: your PyPI project/account API token

## Release Notes

```text
AION Core 0.8.2 is a proof-hardened public infrastructure MVP for AI agent action control.

Includes:
- AION Guard runtime action checks
- AION Receipts hash-verified audit logs
- AION Scan for MCP configs and weak policies
- MCP Firewall stdio proxy
- Team policy approval-required decisions
- AION Cloud receipt/control-panel alignment
- One-command demo: aion-demo
- Real LangChain, CrewAI, and Groq live tests
- Single-agent and multi-agent real-world capacity tests
```

## Smoke Test After Push

```powershell
git clone https://github.com/Sourabh1845/aion-core.git
cd aion-core
$env:PYTHONPATH='src'
python -m unittest discover -s tests
python -m aion_core.demo
```

## CI

The repo includes:

- `.github/workflows/ci.yml`
  - tests Python 3.10, 3.11, 3.12
  - runs `aion-demo`
- `.github/workflows/python-publish.yml`
  - builds package when a GitHub release is published
  - uploads to PyPI using `PYPI_API_TOKEN`

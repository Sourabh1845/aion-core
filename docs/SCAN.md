# AION Scan

AION Scan discovers risky agent tool exposure before runtime.

It currently scans:

- MCP client config JSON files
- AION policy JSON files

## What It Detects

MCP config findings:

- unprotected MCP servers not wrapped by `aion-mcp-firewall`
- powerful servers that appear to expose filesystem, shell, browser, cloud, or database capabilities
- invalid MCP config shape

Policy findings:

- empty allow-by-default policy
- missing destructive shell coverage
- missing secret exfiltration coverage
- invalid policy rules

## CLI

Scan integration examples:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.scan_cli examples\integrations
```

JSON output:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.scan_cli examples\integrations --json
```

Fail on high-severity findings:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.scan_cli examples\integrations --fail-on-high
```

## Current Limits

This is a core MVP scanner. It does not yet execute MCP servers or inspect live tool schemas. Stage 3.2 should add deeper MCP tool-list inspection and richer policy coverage analysis.

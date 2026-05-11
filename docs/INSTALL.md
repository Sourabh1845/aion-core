# Install

## Local Development

From the repo root:

```powershell
python -m pip install -e .
```

Then run:

```powershell
aion-demo
```

`aion-stage6-demo` is still kept as a backward-compatible alias.

If editable install is not needed, use the source checkout command below.

## Without Installing

```powershell
$env:PYTHONPATH='src'
python -m aion_core.demo
```

## Firewall Command

```powershell
aion-mcp-firewall --policy examples/policies/stage6-default.json --receipt-log receipts/aion.jsonl -- python path/to/mcp_server.py
```

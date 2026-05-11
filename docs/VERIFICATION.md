# Verification

Last verified in this workspace:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

Result:

```text
Ran 19 tests
OK
```

Demo:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.demo --output-dir test-output\aion-core-demo
```

Result:

```text
[PASS] scan detected unprotected MCP server
[PASS] guard blocked generic shell action
[PASS] guard allowed generic safe read
[PASS] team policy required approval
[PASS] blocked destructive shell command
[PASS] blocked secret exfiltration
[PASS] allowed safe read
Receipt verification: PASS (6 receipt(s), hash-verified)
```

Cloud alignment:

```text
verified demo-agent shell.command aion.receipt.v1
tamper rejected 400
cloud import ok
```

Stage 8 control panel:

```text
Cloud backend syntax/import verified.
Cloud endpoints added: /control-panel/summary and /approvals.
Cloud dashboard UI includes Load Control Panel, summary cards, and pending approval list.
```

Receipt verification:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.receipt_cli verify test-output\aion-core-demo\receipts.jsonl
```

Result:

```text
OK: verified 6 receipt(s)
```

Scan:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.scan_cli examples\integrations
```

Expected high finding:

```text
HIGH unprotected-mcp-server
```

Packaging:

```powershell
python -m pip install -e .
```

Editable install successfully built and installed `aion-core` in the existing user venv.

Note: the Codex sandbox could not execute that venv's Python launcher because access to its base Python path was denied from the sandbox. Source-run commands using `PYTHONPATH=src` are fully verified.

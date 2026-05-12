# Verification

Last verified in this workspace:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

Result:

```text
Base environment:
Ran 22 tests
OK (skipped=2)

Real SDK venv:
Ran 22 tests
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

Proof Pack:

```powershell
$env:PYTHONPATH='src'
python examples\proof_pack\agent_workflow_proof.py --output-dir test-output\proof-pack-final
```

Result:

```text
AION Core Agent Workflow Proof Pack
Scenarios: 6/6 passed
Receipts: 5 hash-verified
```

Real SDK integrations:

```powershell
$env:PYTHONPATH='src;examples\real_integrations'
test-output\real-sdk-venv\Scripts\python.exe examples\real_integrations\run_real_sdk_tests.py --output-dir test-output\real-sdk-final
```

Result:

```text
AION + LangChain real SDK test
Scenarios: 2/2 passed
Receipts: 2 hash-verified

AION + CrewAI real SDK test
Scenarios: 2/2 passed
Receipts: 2 hash-verified

AION + Groq live SDK test
SKIPPED: GROQ_API_KEY is not set

Real SDK summary: 2 passed, 1 skipped, 0 failed
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

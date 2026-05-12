# Verification

Last verified in this workspace:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

Result:

```text
Base environment:
Ran 29 tests
OK (skipped=2)

Real SDK venv:
Ran 25 tests
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

Groq live verification:

```powershell
$env:GROQ_API_KEY='90-day Groq key'
$env:PYTHONPATH='src;examples\real_integrations'
test-output\real-sdk-venv\Scripts\python.exe examples\real_integrations\groq_live_test.py --require-api-key --output-dir test-output\real-sdk-final\groq
```

Result:

```text
AION + Groq live SDK test
Scenarios: 2/2 passed
Receipts: 2 hash-verified
```

Real-world capacity:

```powershell
$env:PYTHONPATH='src'
python examples\real_world_capacity\release_ops_capacity_test.py --output-dir test-output\real-world-final
```

Result:

```text
AION Real-World Capacity Test
Workflow: release ops agent production readiness
Scenarios: 8/8 passed
Receipts: 5 hash-verified
Pending approvals: 1

AION Hardcore Single-Agent Capacity Test
Workflow: customer support sensitive data resolution
Scenarios: 9/9 passed
Receipts: 6 hash-verified
Pending approvals: 1

AION Hardcore Multi-Agent Capacity Test
Workflow: multi-agent incident response
Agents: planner-agent, research-agent, coding-agent, ops-agent
Scenarios: 10/10 passed
Receipts: 7 hash-verified
Pending approvals: 1
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

LaunchShield CLI:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.launchshield --project-name 'CLI Markdown Smoke' --workflow 'Agent reads customer data from uploaded PDFs and external email content, then can trigger refunds and send email summaries.' --tools 'MCP filesystem server, shell, payment refund API, email sender, API_KEY in env.' --mcp-config-file test-output\launchshield-cli-smoke\mcp.json --surface MCP --surface OpenAI --control receipts --output test-output\launchshield-cli-smoke\report.md
```

Result:

```text
AION LaunchShield Report generated.
Score: 0/100
Status: critical
Scanner confidence: High
Risk chains: 4
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
python -m build
python -m twine check dist\*
```

Result:

```text
Successfully built aion_core-0.8.2.tar.gz and aion_core-0.8.2-py3-none-any.whl
Checking dist\aion_core-0.8.2-py3-none-any.whl: PASSED
Checking dist\aion_core-0.8.2.tar.gz: PASSED
```

Installed wheel smoke:

```text
Successfully installed aion-core-0.8.2
0.8.2
aion-launchshield generated a Markdown report with critical launch blockers.
```

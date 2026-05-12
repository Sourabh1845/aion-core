# AION Core

Runtime action control, receipt, and firewall layer for AI agents.

AION Core contains the open-source infrastructure pieces behind AION: Guard, Receipts, Scan, Team Policy, and the MCP Firewall.

```text
AI Agent -> AION Guard / MCP Firewall -> Tool/API/System
                                  |
                                  +-> verified JSONL receipt log
```

## One-Command Demo

From the repo root:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.demo
```

After local install or PyPI install:

```powershell
python -m pip install aion-core
aion-demo
```

For editable development installs:

```powershell
python -m pip install -e .
```

Expected result:

```text
[PASS] scan detected unprotected MCP server
[PASS] guard blocked generic shell action
[PASS] guard allowed generic safe read
[PASS] team policy required approval
[PASS] blocked destructive shell command
[PASS] blocked secret exfiltration
[PASS] allowed safe read
Receipts written to: aion-demo-output/receipts.jsonl
Approvals written to: aion-demo-output/approvals.jsonl
Receipt verification: PASS (6 receipt(s), hash-verified)
```

This proves the infrastructure wedge:

- generic Guard actions can be allowed or blocked
- dangerous shell action is blocked before reaching the tool
- secret exfiltration attempt is blocked before reaching the tool
- safe file-read action is allowed
- approval-required team actions create approval records
- every decision gets a receipt

## Proof Pack

AION Core includes deterministic agent-workflow proof tests that model
LangChain, CrewAI, Groq function-calling, and raw MCP workflows.

```powershell
$env:PYTHONPATH='src'
python examples\proof_pack\agent_workflow_proof.py
```

Expected result:

```text
AION Core Agent Workflow Proof Pack
Scenarios: 6/6 passed
Receipts: 5 hash-verified
```

Real SDK integration tests are also included:

- LangChain `1.2.18`: real `StructuredTool` guard test passed.
- CrewAI `1.14.4`: real `Agent`, `Task`, and `BaseTool` guard test passed.
- Groq `1.2.0`: real live function-calling test passed with `llama-3.1-8b-instant`.

## Real-World Capacity Tests

AION Core includes end-to-end real-world capacity tests that exercise all 8 MVP
layers together.

```powershell
$env:PYTHONPATH='src'
python examples\real_world_capacity\release_ops_capacity_test.py --output-dir test-output\real-world-final
```

Expected result:

```text
AION Real-World Capacity Test
Scenarios: 8/8 passed
Receipts: 5 hash-verified
Pending approvals: 1
```

Additional verified workflows:

- Hardcore single-agent customer support workflow: `9/9 passed`, `6` hash-verified receipts, `1` pending approval.
- Hardcore multi-agent incident response workflow: `10/10 passed`, `7` hash-verified receipts, `1` pending approval.

## Run Guard

Check a generic action:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.guard_cli check --policy examples\policies\stage6-default.json --receipt-log receipts\guard.jsonl --action-type shell.command --tool shell --arguments-file examples\actions\destructive_shell_args.json --agent-id demo --owner local
```

## Run The Firewall

Run AION in front of any stdio MCP server:

```powershell
aion-mcp-firewall --policy examples/policies/stage6-default.json --receipt-log receipts/aion.jsonl -- python path/to/mcp_server.py
```

For local development without installing:

```powershell
$env:PYTHONPATH='src'
python -m aion_core.cli --policy examples/policies/stage6-default.json --receipt-log receipts/aion.jsonl -- python path/to/mcp_server.py
```

## Manual Attack Demo

Blocked dangerous command:

```powershell
$env:PYTHONPATH='src'
Get-Content examples/attacks/destructive_shell.json | python -m aion_core.cli --policy examples/policies/stage6-default.json --receipt-log receipts/demo.jsonl -- python examples/demo_mcp_server.py
```

Allowed safe call:

```powershell
$env:PYTHONPATH='src'
Get-Content examples/attacks/safe_read.json | python -m aion_core.cli --policy examples/policies/stage6-default.json --receipt-log receipts/demo.jsonl -- python examples/demo_mcp_server.py
```

## Policy Shape

Policies are JSON so the MVP has zero runtime dependencies.

```json
{
  "default_action": "allow",
  "rules": [
    {
      "id": "block-shell-delete",
      "match": {
        "tool": ["shell", "run_command"],
        "argument_contains": ["rm -rf", "Remove-Item", "del /s"]
      },
      "action": "block",
      "reason": "Destructive shell command patterns require explicit approval."
    }
  ]
}
```

Supported rule matchers:

- `tool`: exact tool names or `*` wildcards.
- `argument_contains`: risky strings searched inside serialized arguments.
- `argument_regex`: risky regular expressions searched inside serialized arguments.
- `owner`: optional agent owner/team identity.

Supported actions:

- `allow`
- `block`

## Receipt Example

Every MCP `tools/call` decision is logged as JSONL:

```json
{"decision":"block","tool":"shell","rule_id":"block-shell-delete","reason":"Destructive shell command patterns require explicit approval."}
```

## Development

Run tests:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests
```

Useful docs:

- [Stage status](docs/STAGE_STATUS.md)
- [AION Guard](docs/GUARD.md)
- [AION Receipts](docs/RECEIPTS.md)
- [AION Scan](docs/SCAN.md)
- [AION Proof Pack](docs/PROOF_PACK.md)
- [Real agent test plan](docs/REAL_AGENT_TESTS.md)
- [Real SDK integrations](docs/REAL_SDK_INTEGRATIONS.md)
- [Real-world capacity test](docs/REAL_WORLD_CAPACITY_TEST.md)
- [Team policy and approvals](docs/TEAM_POLICY_APPROVALS.md)
- [Stage 5 Cloud alignment](docs/STAGE5_CLOUD_ALIGNMENT.md)
- [AION Cloud control panel](docs/STAGE8_CONTROL_PANEL.md)
- [Stage 6 completion report](docs/STAGE6_COMPLETION_REPORT.md)
- [Repo structure](docs/REPO_STRUCTURE.md)
- [Stage 6 demo guide](docs/STAGE6_DEMO.md)
- [Install](docs/INSTALL.md)
- [Real MCP integration](docs/REAL_MCP_INTEGRATION.md)
- [Filesystem MCP example](docs/FILESYSTEM_MCP_EXAMPLE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Launch checklist](docs/LAUNCH_CHECKLIST.md)
- [Launch outreach kit](docs/LAUNCH_OUTREACH_KIT.md)
- [GitHub launch](docs/GITHUB_LAUNCH.md)
- [PyPI release](docs/PYPI_RELEASE.md)
- [Website copy](docs/WEBSITE_COPY.md)
- [Verification](docs/VERIFICATION.md)
- [Demo video script](docs/DEMO_VIDEO_SCRIPT.md)
- [Launch post draft](docs/LAUNCH_POST.md)
- [Roadmap](docs/ROADMAP.md)

## Current Scope

Current core scope:

- generic Guard action checks
- MCP config and policy scanning
- stdio MCP firewall proxy
- runtime policy checks for `tools/call`
- MCP-compatible JSON-RPC block responses
- hash-verified JSONL audit receipts
- team approval-required policy decisions
- AION Cloud control panel summary and pending approval views
- dependency-free Python core

Next infrastructure layers:

- signed receipts
- agent identity
- cloud receipt vault
- tool risk registry
- real Slack/webhook approval delivery
- compliance exports

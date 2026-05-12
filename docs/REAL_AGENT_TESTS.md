# Real Agent Test Plan

AION Core now includes deterministic agent-workflow proof tests plus real SDK
integration tests against installed agent packages.

## Current Public Tests

Run:

```powershell
$env:PYTHONPATH='src'
python examples\proof_pack\agent_workflow_proof.py
```

Covered today:

- LangChain tool calls
- CrewAI research and operations tasks
- Groq function calls
- raw MCP config scanning
- team approval-required decisions
- hash-verified receipts

## Real SDK Tests

See [Real SDK Integrations](REAL_SDK_INTEGRATIONS.md).

Verified locally:

- LangChain `1.2.18`: passed
- CrewAI `1.14.4`: passed
- Groq `1.2.0`: live tool-calling test passed with `llama-3.1-8b-instant`

### LangChain

Goal:

- wrap AION Guard around a LangChain tool invocation
- block destructive shell tool calls
- allow safe read-only tools

Command:

```powershell
python examples\real_integrations\langchain_real_test.py
```

### CrewAI

Goal:

- evaluate CrewAI task/tool arguments before execution
- require approval for production mutations
- store receipts

Command:

```powershell
python examples\real_integrations\crewai_real_test.py
```

### Groq

Goal:

- validate a model-suggested function call before execution
- block exfiltration-shaped tool arguments
- allow safe function calls

Command:

```powershell
$env:GROQ_API_KEY='...'
python examples\real_integrations\groq_live_test.py --require-api-key
```

## Public Claim Language

Use this wording now:

```text
AION Core has been tested with LangChain, CrewAI, Groq live function calls, and
raw MCP workflows.
```

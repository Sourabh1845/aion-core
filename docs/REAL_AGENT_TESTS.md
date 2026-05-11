# Real Agent Test Plan

AION Core now includes deterministic agent-workflow proof tests. The next layer
is optional SDK-level testing against real agent packages and hosted model APIs.

## Current Public Tests

Run:

```powershell
$env:PYTHONPATH='src'
python examples\proof_pack\agent_workflow_proof.py
```

Covered today:

- LangChain-style tool calls
- CrewAI-style research and operations tasks
- Groq-style function calls
- raw MCP config scanning
- team approval-required decisions
- hash-verified receipts

## Optional Real SDK Tests

These should be added as separate tests because they require extra dependencies
or API keys.

### LangChain

Goal:

- wrap AION Guard around a LangChain tool invocation
- block destructive shell-style tool calls
- allow safe read-only tools

Suggested command:

```powershell
pip install langchain
python examples\proof_pack\optional_langchain_test.py
```

### CrewAI

Goal:

- evaluate CrewAI task/tool arguments before execution
- require approval for production mutations
- store receipts

Suggested command:

```powershell
pip install crewai
python examples\proof_pack\optional_crewai_test.py
```

### Groq

Goal:

- validate a model-suggested function call before execution
- block exfiltration-shaped tool arguments
- allow safe function calls

Suggested command:

```powershell
pip install groq
$env:GROQ_API_KEY='...'
python examples\proof_pack\optional_groq_test.py
```

## Public Claim Language

Use this wording until SDK-level tests are added:

```text
AION Core includes deterministic proof tests that model LangChain-style,
CrewAI-style, Groq-style, and raw MCP agent workflows.
```

Use this wording only after real SDK tests are implemented:

```text
AION Core has been tested with LangChain, CrewAI, Groq function calls, and raw
MCP workflows.
```

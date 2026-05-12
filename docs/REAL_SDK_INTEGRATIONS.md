# Real SDK Integrations

AION Core has real SDK integration tests for LangChain, CrewAI, and Groq.

Current verified status:

| SDK | Package version tested | Status | Notes |
|---|---:|---|---|
| LangChain | `1.2.18` | Passed | Uses real `langchain_core.tools.StructuredTool`. |
| CrewAI | `1.14.4` | Passed | Uses real `crewai.Agent`, `crewai.Task`, and `crewai.tools.BaseTool`. |
| Groq | `1.2.0` | Passed | Uses real `groq.Groq.chat.completions.create` live tool calling with `llama-3.1-8b-instant`. |

## Setup

From the repo root:

```powershell
python -m venv test-output\real-sdk-venv
test-output\real-sdk-venv\Scripts\python.exe -m pip install --upgrade pip
test-output\real-sdk-venv\Scripts\python.exe -m pip install -e . langchain crewai groq
```

## Run All Real SDK Tests

```powershell
$env:PYTHONPATH='src;examples\real_integrations'
test-output\real-sdk-venv\Scripts\python.exe examples\real_integrations\run_real_sdk_tests.py --output-dir test-output\real-sdk-final
```

Verified local result without `GROQ_API_KEY` in the runner environment:

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

## LangChain

Command:

```powershell
$env:PYTHONPATH='src;examples\real_integrations'
test-output\real-sdk-venv\Scripts\python.exe examples\real_integrations\langchain_real_test.py --output-dir test-output\real-sdk-final\langchain
```

What it verifies:

- Real `StructuredTool` destructive shell call is blocked before the underlying function executes.
- Real `StructuredTool` safe read call is allowed and executed.
- Receipts are hash-verified.

## CrewAI

Command:

```powershell
$env:PYTHONPATH='src;examples\real_integrations'
test-output\real-sdk-venv\Scripts\python.exe examples\real_integrations\crewai_real_test.py --output-dir test-output\real-sdk-final\crewai
```

What it verifies:

- Real `BaseTool` destructive shell call is blocked before tool execution.
- Real `BaseTool` safe research lookup is allowed and executed.
- Real `Agent` and `Task` objects are created using the current CrewAI API.
- Receipts are hash-verified.

## Groq Live Tool Calling

Command:

```powershell
$env:GROQ_API_KEY='your-groq-api-key'
$env:PYTHONPATH='src;examples\real_integrations'
test-output\real-sdk-venv\Scripts\python.exe examples\real_integrations\groq_live_test.py --require-api-key --output-dir test-output\real-sdk-final\groq
```

What it verifies when a key is present:

- Real `groq.Groq.chat.completions.create` returns tool calls.
- A destructive shell tool call is blocked before local execution.
- A safe function call is allowed.
- Receipts are hash-verified.

Verified live result after setting `GROQ_API_KEY`:

```text
AION + Groq live SDK test
Scenarios: 2/2 passed
Receipts: 2 hash-verified
```

The API key used for local verification was generated with a 90-day expiration.

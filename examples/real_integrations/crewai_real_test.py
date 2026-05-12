"""Real CrewAI integration test for AION Core.

This uses CrewAI's actual BaseTool API and verifies AION can guard CrewAI tool
execution without relying on a hosted LLM call.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import PrivateAttr

from aion_core.receipts import JsonlReceiptSink

from common import AionBlockedToolCall, check_with_aion, prepare_output_dir, receipt_summary, write_policy, write_result


class AionCrewShellTool(BaseTool):
    name: str = "shell"
    description: str = "Run shell commands after AION policy approval."
    _policy: Any = PrivateAttr()
    _receipt_sink: Any = PrivateAttr()
    _execution_count: dict[str, int] = PrivateAttr()

    def __init__(self, *, policy: Any, receipt_sink: JsonlReceiptSink, execution_count: dict[str, int]):
        super().__init__()
        self._policy = policy
        self._receipt_sink = receipt_sink
        self._execution_count = execution_count

    def _run(self, command: str) -> str:
        check_with_aion(
            policy=self._policy,
            receipt_sink=self._receipt_sink,
            action_type="shell.command",
            tool="shell",
            arguments={"command": command},
            agent_id="crewai-agent",
            owner="proof-team",
            request_id="crewai-shell-1",
            metadata={"sdk": "crewai", "package_api": "BaseTool"},
        )
        self._execution_count["shell"] += 1
        return f"executed shell: {command}"


class AionCrewResearchTool(BaseTool):
    name: str = "research_lookup"
    description: str = "Run safe research lookups after AION policy approval."
    _policy: Any = PrivateAttr()
    _receipt_sink: Any = PrivateAttr()
    _execution_count: dict[str, int] = PrivateAttr()

    def __init__(self, *, policy: Any, receipt_sink: JsonlReceiptSink, execution_count: dict[str, int]):
        super().__init__()
        self._policy = policy
        self._receipt_sink = receipt_sink
        self._execution_count = execution_count

    def _run(self, query: str) -> str:
        check_with_aion(
            policy=self._policy,
            receipt_sink=self._receipt_sink,
            action_type="research.lookup",
            tool="research_lookup",
            arguments={"query": query},
            agent_id="crewai-agent",
            owner="proof-team",
            request_id="crewai-research-1",
            metadata={"sdk": "crewai", "package_api": "BaseTool"},
        )
        self._execution_count["research_lookup"] += 1
        return f"lookup ok: {query}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run real CrewAI + AION integration test.")
    parser.add_argument("--output-dir", default="real-test-output/crewai")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    prepare_output_dir(output_dir)
    policy = write_policy(output_dir / "policy.json")
    receipt_sink = JsonlReceiptSink(output_dir / "receipts.jsonl")
    execution_count = {"shell": 0, "research_lookup": 0}

    shell_tool = AionCrewShellTool(policy=policy, receipt_sink=receipt_sink, execution_count=execution_count)
    research_tool = AionCrewResearchTool(policy=policy, receipt_sink=receipt_sink, execution_count=execution_count)
    agent = Agent(
        role="Security-tested operations agent",
        goal="Use tools only after AION approval",
        backstory="A test agent used to verify CrewAI tool protection.",
        tools=[shell_tool, research_tool],
    )
    task = Task(
        description="Verify AION protects CrewAI tools.",
        expected_output="AION protected CrewAI tool execution.",
        agent=agent,
        tools=[shell_tool, research_tool],
    )

    results: list[dict[str, Any]] = []
    failures = 0

    try:
        shell_tool.run(command="rm -rf ./workspace")
        blocked = False
        block_payload = {}
    except AionBlockedToolCall as exc:
        blocked = True
        block_payload = exc.payload
    shell_passed = blocked and execution_count["shell"] == 0
    failures += 0 if shell_passed else 1
    results.append(
        {
            "sdk": "crewai",
            "scenario": "BaseTool destructive shell call blocked before execution",
            "passed": shell_passed,
            "underlying_executions": execution_count["shell"],
            "aion": block_payload,
        }
    )

    safe_result = research_tool.run(query="AION agent security")
    safe_passed = "lookup ok" in safe_result and execution_count["research_lookup"] == 1
    failures += 0 if safe_passed else 1
    results.append(
        {
            "sdk": "crewai",
            "scenario": "BaseTool safe research lookup allowed and executed",
            "passed": safe_passed,
            "underlying_executions": execution_count["research_lookup"],
            "result": safe_result,
        }
    )

    proof = {
        "schema_version": "aion.real_sdk_test.v1",
        "sdk": "crewai",
        "package_api": "crewai.Agent, crewai.Task, crewai.tools.BaseTool",
        "agent_role": agent.role,
        "task_description": task.description,
        "passed": sum(1 for item in results if item["passed"]),
        "failed": failures,
        "receipt_summary": receipt_summary(output_dir / "receipts.jsonl"),
        "results": results,
    }
    write_result(output_dir / "crewai_result.json", proof)

    print("AION + CrewAI real SDK test")
    print(f"Scenarios: {proof['passed']}/{len(results)} passed")
    print(f"Receipts: {proof['receipt_summary']['total']} hash-verified")
    print(f"Results: {output_dir / 'crewai_result.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

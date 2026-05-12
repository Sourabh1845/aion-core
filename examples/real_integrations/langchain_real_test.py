"""Real LangChain integration test for AION Core.

This uses LangChain's actual StructuredTool API and verifies AION blocks risky
tool calls before the underlying tool function executes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from langchain_core.tools import StructuredTool

from aion_core.receipts import JsonlReceiptSink

from common import AionBlockedToolCall, check_with_aion, prepare_output_dir, receipt_summary, write_policy, write_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run real LangChain + AION integration test.")
    parser.add_argument("--output-dir", default="real-test-output/langchain")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    prepare_output_dir(output_dir)
    policy = write_policy(output_dir / "policy.json")
    receipt_sink = JsonlReceiptSink(output_dir / "receipts.jsonl")
    execution_count = {"shell": 0, "read_file": 0}

    def guarded_shell(command: str) -> str:
        check_with_aion(
            policy=policy,
            receipt_sink=receipt_sink,
            action_type="shell.command",
            tool="shell",
            arguments={"command": command},
            agent_id="langchain-agent",
            owner="proof-team",
            request_id="langchain-shell-1",
            metadata={"sdk": "langchain", "package_api": "StructuredTool"},
        )
        execution_count["shell"] += 1
        return f"executed shell: {command}"

    def guarded_read_file(path: str) -> str:
        check_with_aion(
            policy=policy,
            receipt_sink=receipt_sink,
            action_type="file.read",
            tool="read_file",
            arguments={"path": path},
            agent_id="langchain-agent",
            owner="proof-team",
            request_id="langchain-read-1",
            metadata={"sdk": "langchain", "package_api": "StructuredTool"},
        )
        execution_count["read_file"] += 1
        return f"read ok: {path}"

    shell_tool = StructuredTool.from_function(
        func=guarded_shell,
        name="shell",
        description="Run a shell command after AION policy approval.",
    )
    read_tool = StructuredTool.from_function(
        func=guarded_read_file,
        name="read_file",
        description="Read a local file after AION policy approval.",
    )

    results: list[dict[str, Any]] = []
    failures = 0

    try:
        shell_tool.invoke({"command": "rm -rf ./workspace"})
        blocked = False
        block_payload = {}
    except AionBlockedToolCall as exc:
        blocked = True
        block_payload = exc.payload
    shell_passed = blocked and execution_count["shell"] == 0
    failures += 0 if shell_passed else 1
    results.append(
        {
            "sdk": "langchain",
            "scenario": "StructuredTool destructive shell call blocked before execution",
            "passed": shell_passed,
            "underlying_executions": execution_count["shell"],
            "aion": block_payload,
        }
    )

    safe_result = read_tool.invoke({"path": "README.md"})
    safe_passed = safe_result == "read ok: README.md" and execution_count["read_file"] == 1
    failures += 0 if safe_passed else 1
    results.append(
        {
            "sdk": "langchain",
            "scenario": "StructuredTool safe file read allowed and executed",
            "passed": safe_passed,
            "underlying_executions": execution_count["read_file"],
            "result": safe_result,
        }
    )

    proof = {
        "schema_version": "aion.real_sdk_test.v1",
        "sdk": "langchain",
        "package_api": "langchain_core.tools.StructuredTool",
        "passed": sum(1 for item in results if item["passed"]),
        "failed": failures,
        "receipt_summary": receipt_summary(output_dir / "receipts.jsonl"),
        "results": results,
    }
    write_result(output_dir / "langchain_result.json", proof)

    print("AION + LangChain real SDK test")
    print(f"Scenarios: {proof['passed']}/{len(results)} passed")
    print(f"Receipts: {proof['receipt_summary']['total']} hash-verified")
    print(f"Results: {output_dir / 'langchain_result.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

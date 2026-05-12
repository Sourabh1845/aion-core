"""Live Groq function-calling integration test for AION Core.

This test calls the real Groq API when GROQ_API_KEY is set. It validates a
model-emitted tool call through AION before local tool execution.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from groq import Groq

from aion_core.receipts import JsonlReceiptSink

from common import AionBlockedToolCall, check_with_aion, prepare_output_dir, receipt_summary, write_policy, write_result


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Run a shell command after policy approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_ticket",
            "description": "Summarize a safe internal support ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Support ticket id."}
                },
                "required": ["ticket_id"],
            },
        },
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run live Groq + AION integration test.")
    parser.add_argument("--output-dir", default="real-test-output/groq")
    parser.add_argument("--model", default="llama-3.1-8b-instant")
    parser.add_argument(
        "--require-api-key",
        action="store_true",
        help="Fail if GROQ_API_KEY is not set instead of writing a skipped result.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    prepare_output_dir(output_dir)

    if not os.environ.get("GROQ_API_KEY"):
        result = {
            "schema_version": "aion.real_sdk_test.v1",
            "sdk": "groq",
            "status": "skipped",
            "reason": "GROQ_API_KEY is not set. Live Groq test was not executed.",
            "model": args.model,
        }
        write_result(output_dir / "groq_result.json", result)
        print("AION + Groq live SDK test")
        print("SKIPPED: GROQ_API_KEY is not set")
        return 2 if args.require_api_key else 0

    policy = write_policy(output_dir / "policy.json")
    receipt_sink = JsonlReceiptSink(output_dir / "receipts.jsonl")
    client = Groq()
    results: list[dict[str, Any]] = []
    failures = 0

    destructive_call = create_tool_call(
        client=client,
        model=args.model,
        tool_name="run_shell_command",
        prompt="Call run_shell_command with command exactly: rm -rf ./workspace",
    )
    shell_args = json.loads(destructive_call.function.arguments or "{}")
    try:
        check_with_aion(
            policy=policy,
            receipt_sink=receipt_sink,
            action_type="shell.command",
            tool="shell",
            arguments=shell_args,
            agent_id="groq-agent",
            owner="proof-team",
            request_id="groq-shell-1",
            metadata={"sdk": "groq", "model": args.model, "tool_call_id": destructive_call.id},
        )
        blocked = False
        block_payload = {}
    except AionBlockedToolCall as exc:
        blocked = True
        block_payload = exc.payload
    shell_passed = blocked and "rm -rf" in shell_args.get("command", "")
    failures += 0 if shell_passed else 1
    results.append(
        {
            "sdk": "groq",
            "scenario": "live Groq tool call for destructive shell command blocked before execution",
            "model": args.model,
            "tool_name": destructive_call.function.name,
            "arguments": shell_args,
            "passed": shell_passed,
            "aion": block_payload,
        }
    )

    safe_call = create_tool_call(
        client=client,
        model=args.model,
        tool_name="summarize_ticket",
        prompt="Call summarize_ticket with ticket_id exactly: T-100",
    )
    safe_args = json.loads(safe_call.function.arguments or "{}")
    allow_payload = check_with_aion(
        policy=policy,
        receipt_sink=receipt_sink,
        action_type="llm.function_call",
        tool="summarize_ticket",
        arguments=safe_args,
        agent_id="groq-agent",
        owner="proof-team",
        request_id="groq-ticket-1",
        metadata={"sdk": "groq", "model": args.model, "tool_call_id": safe_call.id},
    )
    safe_passed = safe_call.function.name == "summarize_ticket" and allow_payload["decision"] == "allow"
    failures += 0 if safe_passed else 1
    results.append(
        {
            "sdk": "groq",
            "scenario": "live Groq safe function call allowed",
            "model": args.model,
            "tool_name": safe_call.function.name,
            "arguments": safe_args,
            "passed": safe_passed,
            "aion": allow_payload,
        }
    )

    proof = {
        "schema_version": "aion.real_sdk_test.v1",
        "sdk": "groq",
        "status": "executed",
        "package_api": "groq.Groq.chat.completions.create",
        "model": args.model,
        "passed": sum(1 for item in results if item["passed"]),
        "failed": failures,
        "receipt_summary": receipt_summary(output_dir / "receipts.jsonl"),
        "results": results,
    }
    write_result(output_dir / "groq_result.json", proof)

    print("AION + Groq live SDK test")
    print(f"Scenarios: {proof['passed']}/{len(results)} passed")
    print(f"Receipts: {proof['receipt_summary']['total']} hash-verified")
    print(f"Results: {output_dir / 'groq_result.json'}")
    return 1 if failures else 0


def create_tool_call(*, client: Groq, model: str, tool_name: str, prompt: str) -> Any:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are testing tool calling. Use the requested tool exactly once.",
            },
            {"role": "user", "content": prompt},
        ],
        tools=TOOLS,
        tool_choice={"type": "function", "function": {"name": tool_name}},
        temperature=0,
    )
    message = completion.choices[0].message
    tool_calls = message.tool_calls or []
    if not tool_calls:
        raise RuntimeError(f"Groq model did not return a tool call for {tool_name}")
    return tool_calls[0]


if __name__ == "__main__":
    raise SystemExit(main())

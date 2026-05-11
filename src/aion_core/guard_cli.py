"""CLI for generic AION Guard action checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

from .guard import GuardRequest, evaluate_guard_request
from .policy import Policy
from .receipts import JsonlReceiptSink


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aion-guard",
        description="Check generic AI-agent actions against AION policy.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Evaluate one action and write a receipt.")
    check.add_argument("--policy", required=True, help="Path to a JSON AION policy file.")
    check.add_argument(
        "--receipt-log",
        default="receipts/aion-guard.jsonl",
        help="Path to the JSONL receipt log.",
    )
    check.add_argument("--action-type", required=True, help="Action type, e.g. shell.command.")
    check.add_argument("--tool", required=True, help="Tool or target name.")
    check.add_argument(
        "--arguments-json",
        default="{}",
        help="JSON object containing action arguments.",
    )
    check.add_argument(
        "--arguments-file",
        default=None,
        help="Path to a JSON file containing action arguments. Overrides --arguments-json.",
    )
    check.add_argument("--agent-id", default="unknown-agent")
    check.add_argument("--owner", default="local")
    check.add_argument("--request-id", default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.arguments_file:
            arguments = json.loads(Path(args.arguments_file).read_text(encoding="utf-8"))
        else:
            arguments = json.loads(args.arguments_json)
    except json.JSONDecodeError as exc:
        print(f"aion-guard: invalid --arguments-json: {exc}", file=sys.stderr)
        return 2
    if not isinstance(arguments, dict):
        print("aion-guard: --arguments-json must decode to a JSON object", file=sys.stderr)
        return 2

    policy = Policy.from_file(Path(args.policy))
    receipt_sink = JsonlReceiptSink(Path(args.receipt_log))
    result = evaluate_guard_request(
        request=GuardRequest(
            action_type=args.action_type,
            tool=args.tool,
            arguments=arguments,
            agent_id=args.agent_id,
            owner=args.owner,
            request_id=args.request_id or f"guard_{uuid4().hex}",
            metadata={"cli": "aion-guard"},
        ),
        policy=policy,
        receipt_sink=receipt_sink,
    )
    print(
        json.dumps(
            {
                "decision": result.decision.action,
                "rule_id": result.decision.rule_id,
                "reason": result.decision.reason,
                "receipt_id": result.receipt["receipt_id"],
                "receipt_hash": result.receipt["receipt_hash"],
            },
            sort_keys=True,
        )
    )
    return 1 if result.decision.action == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())

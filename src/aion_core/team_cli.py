"""CLI for AION team policy and approvals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

from .receipts import JsonlEventSink, JsonlReceiptSink
from .team_policy import (
    TeamActionRequest,
    TeamPolicy,
    create_approval_event,
    evaluate_team_action,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aion-team", description="Evaluate team policies and approvals.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Evaluate one team-scoped action.")
    check.add_argument("--team-policy", required=True, help="Path to a team policy JSON file.")
    check.add_argument("--receipt-log", default="receipts/aion-team.jsonl")
    check.add_argument("--approval-log", default="receipts/aion-approvals.jsonl")
    check.add_argument("--action-type", required=True)
    check.add_argument("--tool", required=True)
    check.add_argument("--arguments-file", default=None)
    check.add_argument("--arguments-json", default="{}")
    check.add_argument("--agent-id", default="unknown-agent")
    check.add_argument("--owner", default="local")
    check.add_argument("--team-id", default="")
    check.add_argument("--request-id", default=None)

    approve = subparsers.add_parser("approve", help="Append an approval decision event.")
    approve.add_argument("--approval-log", default="receipts/aion-approvals.jsonl")
    approve.add_argument("--approval-id", required=True)
    approve.add_argument("--approver", required=True)
    approve.add_argument("--status", choices=["approved", "rejected"], required=True)
    approve.add_argument("--reason", default="")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "approve":
        event = create_approval_event(
            approval_id=args.approval_id,
            approver=args.approver,
            status=args.status,
            reason=args.reason,
        )
        JsonlEventSink(Path(args.approval_log)).write(event)
        print(json.dumps(event, sort_keys=True))
        return 0

    try:
        arguments = _load_arguments(args.arguments_file, args.arguments_json)
    except ValueError as exc:
        print(f"aion-team: {exc}", file=sys.stderr)
        return 2

    policy = TeamPolicy.from_file(Path(args.team_policy))
    team_id = args.team_id or policy.team_id
    result = evaluate_team_action(
        request=TeamActionRequest(
            action_type=args.action_type,
            tool=args.tool,
            arguments=arguments,
            agent_id=args.agent_id,
            owner=args.owner,
            team_id=team_id,
            request_id=args.request_id or f"team_{uuid4().hex}",
            metadata={"cli": "aion-team"},
        ),
        policy=policy,
        receipt_sink=JsonlReceiptSink(Path(args.receipt_log)),
        approval_sink=JsonlEventSink(Path(args.approval_log)),
    )
    output = {
        "decision": result.decision.decision,
        "rule_id": result.decision.rule_id,
        "reason": result.decision.reason,
        "receipt_id": result.receipt["receipt_id"],
        "approval_id": result.approval_request["approval_id"] if result.approval_request else None,
        "slack_payload": result.slack_payload,
    }
    print(json.dumps(output, sort_keys=True))
    return 1 if result.decision.decision in {"block", "approval_required"} else 0


def _load_arguments(arguments_file: str | None, arguments_json: str) -> dict:
    if arguments_file:
        value = json.loads(Path(arguments_file).read_text(encoding="utf-8"))
    else:
        value = json.loads(arguments_json)
    if not isinstance(value, dict):
        raise ValueError("arguments must be a JSON object")
    return value


if __name__ == "__main__":
    raise SystemExit(main())

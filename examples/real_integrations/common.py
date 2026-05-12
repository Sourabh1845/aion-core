"""Shared helpers for real SDK integration tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from aion_core.guard import GuardRequest, evaluate_guard_request
from aion_core.policy import Policy
from aion_core.receipts import JsonlReceiptSink, summarize_receipts, verify_jsonl


POLICY_DATA = {
    "default_action": "allow",
    "rules": [
        {
            "id": "block-destructive-shell",
            "action": "block",
            "reason": "Destructive shell command patterns require explicit approval.",
            "match": {
                "tool": ["shell", "terminal", "run_command", "python_repl"],
                "argument_contains": [
                    "rm -rf",
                    "remove-item",
                    "del /s",
                    "format ",
                    "git reset --hard",
                    "drop database",
                    "truncate table",
                ],
            },
        },
        {
            "id": "block-secret-exfiltration",
            "action": "block",
            "reason": "Potential secret exfiltration attempt.",
            "match": {
                "tool": "*",
                "argument_regex": [
                    "api[_-]?key",
                    "secret[_-]?key",
                    "bearer\\s+[a-z0-9._-]+",
                    "password\\s*[:=]",
                ],
            },
        },
    ],
}


class AionBlockedToolCall(RuntimeError):
    """Raised when AION blocks a tool call before SDK tool execution."""

    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        super().__init__(json.dumps(payload, sort_keys=True))


def prepare_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_policy(path: Path) -> Policy:
    path.write_text(json.dumps(POLICY_DATA, indent=2), encoding="utf-8")
    return Policy.from_file(path)


def check_with_aion(
    *,
    policy: Policy,
    receipt_sink: JsonlReceiptSink,
    action_type: str,
    tool: str,
    arguments: dict[str, Any],
    agent_id: str,
    owner: str,
    request_id: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = evaluate_guard_request(
        request=GuardRequest(
            action_type=action_type,
            tool=tool,
            arguments=arguments,
            agent_id=agent_id,
            owner=owner,
            request_id=request_id,
            metadata=metadata or {},
        ),
        policy=policy,
        receipt_sink=receipt_sink,
    )
    payload = {
        "decision": result.decision.action,
        "rule_id": result.decision.rule_id,
        "reason": result.decision.reason,
        "receipt_id": result.receipt["receipt_id"],
    }
    if result.decision.action == "block":
        raise AionBlockedToolCall(payload)
    return payload


def write_result(path: Path, result: dict[str, Any]) -> None:
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")


def receipt_summary(path: Path) -> dict[str, Any]:
    return summarize_receipts(verify_jsonl(path))

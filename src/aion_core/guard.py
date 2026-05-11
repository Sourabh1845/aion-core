"""Generic runtime action control for AION Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .policy import Decision, Policy
from .receipts import ReceiptSink, normalize_receipt


@dataclass(frozen=True)
class GuardRequest:
    action_type: str
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    agent_id: str = "unknown-agent"
    owner: str = "local"
    request_id: str | int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GuardResult:
    decision: Decision
    receipt: dict[str, Any]


def evaluate_guard_request(
    *,
    request: GuardRequest,
    policy: Policy,
    receipt_sink: ReceiptSink | None = None,
) -> GuardResult:
    decision = policy.evaluate_action(
        action_type=request.action_type,
        tool_name=request.tool,
        arguments=request.arguments,
        agent_id=request.agent_id,
        owner=request.owner,
    )
    receipt = normalize_receipt(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "stage": "guard",
            "component": "aion-guard",
            "agent_id": request.agent_id,
            "owner": request.owner,
            "request_id": request.request_id,
            "action_type": request.action_type,
            "tool": request.tool,
            "decision": decision.action,
            "rule_id": decision.rule_id,
            "reason": decision.reason,
            "risk": "blocked" if decision.action == "block" else "accepted",
            "argument_fingerprint": policy.fingerprint(request.arguments),
            "metadata": request.metadata,
        }
    )
    if receipt_sink is not None:
        receipt_sink.write(receipt)
    return GuardResult(decision=decision, receipt=receipt)

"""Team policy and approval workflow for AION Core."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .receipts import JsonlReceiptSink, normalize_receipt


TEAM_DECISIONS = {"allow", "block", "approval_required"}


@dataclass(frozen=True)
class TeamActionRequest:
    action_type: str
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)
    agent_id: str = "unknown-agent"
    owner: str = "local"
    team_id: str = "default-team"
    request_id: str | int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TeamPolicyRule:
    id: str
    decision: str
    reason: str
    match: dict[str, Any]
    approvers: list[str] = field(default_factory=list)
    approval_ttl_minutes: int = 30

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamPolicyRule":
        rule_id = str(data.get("id") or "unnamed-team-rule")
        decision = str(data.get("decision") or data.get("action") or "block").lower()
        if decision not in TEAM_DECISIONS:
            raise ValueError(f"unsupported team policy decision for rule {rule_id}: {decision}")
        match = data.get("match") or {}
        if not isinstance(match, dict):
            raise ValueError(f"rule {rule_id} match must be an object")
        approvers = [str(item) for item in data.get("approvers", [])]
        return cls(
            id=rule_id,
            decision=decision,
            reason=str(data.get("reason") or f"Matched team policy rule {rule_id}."),
            match=match,
            approvers=approvers,
            approval_ttl_minutes=int(data.get("approval_ttl_minutes") or 30),
        )

    def matches(self, request: TeamActionRequest) -> bool:
        if not _matches_patterns(request.action_type, _as_list(self.match.get("action_type", "*"))):
            return False
        if not _matches_patterns(request.tool, _as_list(self.match.get("tool", "*"))):
            return False
        owner_patterns = self.match.get("owner")
        if owner_patterns is not None and not _matches_patterns(request.owner, _as_list(owner_patterns)):
            return False
        team_patterns = self.match.get("team_id")
        if team_patterns is not None and not _matches_patterns(request.team_id, _as_list(team_patterns)):
            return False

        serialized_args = _stable_json(request.arguments).lower()
        contains = self.match.get("argument_contains")
        if contains is not None:
            needles = [str(item).lower() for item in _as_list(contains)]
            if not any(needle in serialized_args for needle in needles):
                return False

        regexes = self.match.get("argument_regex")
        if regexes is not None:
            if not any(re.search(str(pattern), serialized_args, re.IGNORECASE) for pattern in _as_list(regexes)):
                return False
        return True


@dataclass(frozen=True)
class TeamPolicyDecision:
    decision: str
    reason: str
    rule_id: str
    approvers: list[str] = field(default_factory=list)
    approval_ttl_minutes: int = 30


class TeamPolicy:
    def __init__(
        self,
        *,
        team_id: str = "default-team",
        default_decision: str = "allow",
        rules: list[TeamPolicyRule] | None = None,
    ):
        default_decision = default_decision.lower()
        if default_decision not in TEAM_DECISIONS:
            raise ValueError("default_decision must be allow, block, or approval_required")
        self.team_id = team_id
        self.default_decision = default_decision
        self.rules = rules or []

    @classmethod
    def from_file(cls, path: Path) -> "TeamPolicy":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("team policy file must contain a JSON object")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamPolicy":
        rules = data.get("rules") or []
        if not isinstance(rules, list):
            raise ValueError("team policy rules must be a list")
        return cls(
            team_id=str(data.get("team_id") or "default-team"),
            default_decision=str(data.get("default_decision") or "allow"),
            rules=[TeamPolicyRule.from_dict(rule) for rule in rules],
        )

    def evaluate(self, request: TeamActionRequest) -> TeamPolicyDecision:
        for rule in self.rules:
            if not rule.matches(request):
                continue
            return TeamPolicyDecision(
                decision=rule.decision,
                reason=rule.reason,
                rule_id=rule.id,
                approvers=rule.approvers,
                approval_ttl_minutes=rule.approval_ttl_minutes,
            )
        return TeamPolicyDecision(
            decision=self.default_decision,
            reason=f"Allowed by team policy {self.team_id}.",
            rule_id="team-default",
        )


@dataclass(frozen=True)
class TeamPolicyResult:
    decision: TeamPolicyDecision
    receipt: dict[str, Any]
    approval_request: dict[str, Any] | None = None
    slack_payload: dict[str, Any] | None = None


def evaluate_team_action(
    *,
    request: TeamActionRequest,
    policy: TeamPolicy,
    receipt_sink: JsonlReceiptSink | None = None,
    approval_sink: JsonlReceiptSink | None = None,
) -> TeamPolicyResult:
    decision = policy.evaluate(request)
    receipt = normalize_receipt(
        {
            "stage": "team-policy",
            "component": "aion-team-policy",
            "agent_id": request.agent_id,
            "owner": request.owner,
            "request_id": request.request_id,
            "action_type": request.action_type,
            "tool": request.tool,
            "decision": decision.decision,
            "rule_id": decision.rule_id,
            "reason": decision.reason,
            "risk": _risk_for_decision(decision.decision),
            "argument_fingerprint": _fingerprint(request.arguments),
            "metadata": {
                **request.metadata,
                "team_id": request.team_id,
                "approvers": decision.approvers,
            },
        }
    )
    if receipt_sink is not None:
        receipt_sink.write(receipt)

    approval_request = None
    slack_payload = None
    if decision.decision == "approval_required":
        approval_request = create_approval_request(
            request=request,
            decision=decision,
            receipt=receipt,
        )
        slack_payload = create_slack_payload(approval_request)
        if approval_sink is not None:
            approval_sink.write(approval_request)

    return TeamPolicyResult(
        decision=decision,
        receipt=receipt,
        approval_request=approval_request,
        slack_payload=slack_payload,
    )


def create_approval_request(
    *,
    request: TeamActionRequest,
    decision: TeamPolicyDecision,
    receipt: dict[str, Any],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=decision.approval_ttl_minutes)
    approval = {
        "schema_version": "aion.approval.v1",
        "approval_id": f"appr_{uuid4().hex}",
        "status": "pending",
        "team_id": request.team_id,
        "agent_id": request.agent_id,
        "owner": request.owner,
        "action_type": request.action_type,
        "tool": request.tool,
        "request_id": request.request_id,
        "rule_id": decision.rule_id,
        "reason": decision.reason,
        "approvers": decision.approvers,
        "receipt_id": receipt["receipt_id"],
        "receipt_hash": receipt["receipt_hash"],
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "metadata": request.metadata,
    }
    approval["approval_hash"] = _fingerprint(approval)
    return approval


def create_approval_event(*, approval_id: str, approver: str, status: str, reason: str = "") -> dict[str, Any]:
    if status not in {"approved", "rejected"}:
        raise ValueError("approval event status must be approved or rejected")
    event = {
        "schema_version": "aion.approval_event.v1",
        "approval_id": approval_id,
        "status": status,
        "approver": approver,
        "reason": reason,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    event["event_hash"] = _fingerprint(event)
    return event


def create_slack_payload(approval_request: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": (
            "AION approval required: "
            f"{approval_request['action_type']} via {approval_request['tool']} "
            f"for team {approval_request['team_id']}"
        ),
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*AION approval required*\n"
                        f"*Action:* `{approval_request['action_type']}`\n"
                        f"*Tool:* `{approval_request['tool']}`\n"
                        f"*Rule:* `{approval_request['rule_id']}`\n"
                        f"*Reason:* {approval_request['reason']}"
                    ),
                },
            }
        ],
    }


def _risk_for_decision(decision: str) -> str:
    if decision == "block":
        return "blocked"
    if decision == "approval_required":
        return "pending_approval"
    return "accepted"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def _matches_patterns(value: str, patterns: list[Any]) -> bool:
    return any(fnmatch.fnmatchcase(value, str(pattern)) for pattern in patterns)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()

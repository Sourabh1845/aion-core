"""Policy engine for AION Stage 6."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    rule_id: str

    @classmethod
    def allow(cls, reason: str = "Allowed by policy.", rule_id: str = "default-allow") -> "Decision":
        return cls(action="allow", reason=reason, rule_id=rule_id)

    @classmethod
    def block(cls, reason: str, rule_id: str) -> "Decision":
        return cls(action="block", reason=reason, rule_id=rule_id)


@dataclass(frozen=True)
class PolicyRule:
    id: str
    action: str
    reason: str
    match: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolicyRule":
        rule_id = str(data.get("id") or "unnamed-rule")
        action = str(data.get("action") or "block").lower()
        if action not in {"allow", "block"}:
            raise ValueError(f"unsupported action for rule {rule_id}: {action}")
        reason = str(data.get("reason") or f"Matched policy rule {rule_id}.")
        match = data.get("match") or {}
        if not isinstance(match, dict):
            raise ValueError(f"rule {rule_id} match must be an object")
        return cls(id=rule_id, action=action, reason=reason, match=match)

    def matches(self, *, tool_name: str, arguments: Any, owner: str, action_type: str = "") -> bool:
        action_type_patterns = self.match.get("action_type")
        if action_type_patterns is not None and not _matches_patterns(
            action_type, _as_list(action_type_patterns)
        ):
            return False

        if not _matches_patterns(tool_name, _as_list(self.match.get("tool", "*"))):
            return False

        owner_patterns = self.match.get("owner")
        if owner_patterns is not None and not _matches_patterns(owner, _as_list(owner_patterns)):
            return False

        serialized_args = _stable_json(arguments).lower()

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


class Policy:
    def __init__(self, *, default_action: str = "allow", rules: list[PolicyRule] | None = None):
        default_action = default_action.lower()
        if default_action not in {"allow", "block"}:
            raise ValueError("default_action must be allow or block")
        self.default_action = default_action
        self.rules = rules or []

    @classmethod
    def from_file(cls, path: Path) -> "Policy":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("policy file must contain a JSON object")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        rules_data = data.get("rules") or []
        if not isinstance(rules_data, list):
            raise ValueError("policy rules must be a list")
        return cls(
            default_action=str(data.get("default_action") or "allow"),
            rules=[PolicyRule.from_dict(rule) for rule in rules_data],
        )

    def evaluate_tool_call(
        self,
        *,
        tool_name: str,
        arguments: Any,
        agent_id: str,
        owner: str,
    ) -> Decision:
        return self.evaluate_action(
            action_type="mcp.tools_call",
            tool_name=tool_name,
            arguments=arguments,
            agent_id=agent_id,
            owner=owner,
        )

    def evaluate_action(
        self,
        *,
        action_type: str,
        tool_name: str,
        arguments: Any,
        agent_id: str,
        owner: str,
    ) -> Decision:
        del agent_id
        for rule in self.rules:
            if not rule.matches(
                tool_name=tool_name,
                arguments=arguments,
                owner=owner,
                action_type=action_type,
            ):
                continue
            if rule.action == "allow":
                return Decision.allow(reason=rule.reason, rule_id=rule.id)
            return Decision.block(reason=rule.reason, rule_id=rule.id)

        if self.default_action == "allow":
            return Decision.allow()
        return Decision.block(
            reason="Blocked by default-deny policy.",
            rule_id="default-block",
        )

    def fingerprint(self, value: Any) -> str:
        return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def _matches_patterns(value: str, patterns: list[Any]) -> bool:
    return any(fnmatch.fnmatchcase(value, str(pattern)) for pattern in patterns)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))

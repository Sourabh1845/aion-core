"""Receipt schema, hashing, verification, and sinks for AION decisions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Iterable, Protocol
from uuid import uuid4


RECEIPT_SCHEMA_VERSION = "aion.receipt.v1"
HASH_ALGORITHM = "sha256"


class ReceiptSink(Protocol):
    def write(self, receipt: dict[str, Any]) -> None: ...


class ReceiptVerificationError(ValueError):
    pass


class JsonlReceiptSink:
    def __init__(self, path: Path):
        self.path = path

    def write(self, receipt: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        normalized = normalize_receipt(receipt)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalized, sort_keys=True, ensure_ascii=True) + "\n")


class JsonlEventSink:
    def __init__(self, path: Path):
        self.path = path

    def write(self, event: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, ensure_ascii=True) + "\n")


def normalize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(receipt)
    normalized.setdefault("schema_version", RECEIPT_SCHEMA_VERSION)
    normalized.setdefault("receipt_id", f"rcpt_{uuid4().hex}")
    normalized.setdefault("ts", datetime.now(timezone.utc).isoformat())
    normalized.setdefault("stage", "unknown")
    normalized.setdefault("component", normalized.get("stage", "unknown"))
    normalized.setdefault("agent_id", "unknown-agent")
    normalized.setdefault("owner", "local")
    normalized.setdefault("action_type", normalized.get("stage", "unknown"))
    normalized.setdefault("tool", "")
    normalized.setdefault("decision", "unknown")
    normalized.setdefault("rule_id", "")
    normalized.setdefault("reason", "")
    normalized.setdefault("risk", "unknown")
    normalized.setdefault("request_id", None)
    normalized.setdefault("argument_fingerprint", "")
    normalized.setdefault("metadata", {})
    normalized["hash_algorithm"] = HASH_ALGORITHM
    normalized["receipt_hash"] = receipt_hash(normalized)
    return normalized


def receipt_hash(receipt: dict[str, Any]) -> str:
    payload = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def verify_receipt(receipt: dict[str, Any]) -> None:
    required = [
        "schema_version",
        "receipt_id",
        "ts",
        "stage",
        "component",
        "agent_id",
        "owner",
        "action_type",
        "tool",
        "decision",
        "rule_id",
        "reason",
        "risk",
        "argument_fingerprint",
        "hash_algorithm",
        "receipt_hash",
    ]
    missing = [field for field in required if field not in receipt]
    if missing:
        raise ReceiptVerificationError(f"missing required receipt fields: {', '.join(missing)}")
    if receipt["schema_version"] != RECEIPT_SCHEMA_VERSION:
        raise ReceiptVerificationError(f"unsupported schema_version: {receipt['schema_version']}")
    if receipt["hash_algorithm"] != HASH_ALGORITHM:
        raise ReceiptVerificationError(f"unsupported hash_algorithm: {receipt['hash_algorithm']}")
    expected_hash = receipt_hash(receipt)
    if receipt["receipt_hash"] != expected_hash:
        raise ReceiptVerificationError(
            f"receipt_hash mismatch for {receipt['receipt_id']}: expected {expected_hash}"
        )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ReceiptVerificationError(f"line {line_number}: invalid JSON: {exc}") from exc
            if not isinstance(value, dict):
                raise ReceiptVerificationError(f"line {line_number}: receipt must be a JSON object")
            receipts.append(value)
    return receipts


def verify_jsonl(path: Path) -> list[dict[str, Any]]:
    receipts = load_jsonl(path)
    for receipt in receipts:
        verify_receipt(receipt)
    return receipts


def summarize_receipts(receipts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    total = 0
    decisions: dict[str, int] = {}
    tools: dict[str, int] = {}
    rules: dict[str, int] = {}
    for receipt in receipts:
        total += 1
        _count(decisions, str(receipt.get("decision", "unknown")))
        _count(tools, str(receipt.get("tool", "unknown")))
        _count(rules, str(receipt.get("rule_id", "unknown")))
    return {
        "total": total,
        "decisions": decisions,
        "tools": tools,
        "rules": rules,
    }


def _count(bucket: dict[str, int], key: str) -> None:
    bucket[key] = bucket.get(key, 0) + 1

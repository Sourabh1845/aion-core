import json
import shutil
import unittest
import uuid
from pathlib import Path

from aion_core.receipts import (
    JsonlReceiptSink,
    ReceiptVerificationError,
    load_jsonl,
    summarize_receipts,
    verify_jsonl,
)

WORKSPACE_TMP = Path(__file__).resolve().parents[1] / "test-output" / "receipts-unit"


class ReceiptTests(unittest.TestCase):
    def test_sink_writes_verifiable_receipt(self):
        with temporary_workspace_dir() as temp_dir:
            path = Path(temp_dir) / "receipts.jsonl"
            sink = JsonlReceiptSink(path)

            sink.write(
                {
                    "stage": "mcp-firewall",
                    "component": "aion-mcp-firewall",
                    "agent_id": "agent-1",
                    "owner": "team-1",
                    "action_type": "mcp.tools_call",
                    "tool": "shell",
                    "decision": "block",
                    "rule_id": "no-delete",
                    "reason": "No destructive command.",
                    "risk": "blocked",
                    "argument_fingerprint": "abc123",
                }
            )

            receipts = verify_jsonl(path)
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0]["schema_version"], "aion.receipt.v1")
            self.assertTrue(receipts[0]["receipt_id"].startswith("rcpt_"))
            self.assertEqual(len(receipts[0]["receipt_hash"]), 64)

    def test_verify_rejects_tampered_receipt(self):
        with temporary_workspace_dir() as temp_dir:
            path = Path(temp_dir) / "receipts.jsonl"
            sink = JsonlReceiptSink(path)
            sink.write({"tool": "read_file", "decision": "allow"})

            receipt = load_jsonl(path)[0]
            receipt["decision"] = "block"
            path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

            with self.assertRaises(ReceiptVerificationError):
                verify_jsonl(path)

    def test_summarize_receipts(self):
        receipts = [
            {"decision": "allow", "tool": "read_file", "rule_id": "default-allow"},
            {"decision": "block", "tool": "shell", "rule_id": "no-delete"},
            {"decision": "block", "tool": "shell", "rule_id": "no-delete"},
        ]

        summary = summarize_receipts(receipts)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["decisions"]["block"], 2)
        self.assertEqual(summary["tools"]["shell"], 2)
        self.assertEqual(summary["rules"]["no-delete"], 2)


def temporary_workspace_dir():
    WORKSPACE_TMP.mkdir(parents=True, exist_ok=True)
    path = WORKSPACE_TMP / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return WorkspaceDir(path)


class WorkspaceDir:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self) -> str:
        return str(self.path)

    def __exit__(self, exc_type, exc, traceback) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


def tearDownModule():
    shutil.rmtree(WORKSPACE_TMP, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

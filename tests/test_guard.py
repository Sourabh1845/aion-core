import json
import shutil
import unittest
import uuid
from pathlib import Path

from aion_core.guard import GuardRequest, evaluate_guard_request
from aion_core.policy import Policy
from aion_core.receipts import JsonlReceiptSink, verify_jsonl

WORKSPACE_TMP = Path(__file__).resolve().parents[1] / "test-output" / "guard-unit"


class GuardTests(unittest.TestCase):
    def test_blocks_generic_shell_action_and_writes_receipt(self):
        with temporary_workspace_dir() as temp_dir:
            receipt_path = Path(temp_dir) / "guard.jsonl"
            policy = Policy.from_dict(
                {
                    "rules": [
                        {
                            "id": "no-delete",
                            "action": "block",
                            "match": {
                                "action_type": "shell.*",
                                "tool": "shell",
                                "argument_contains": "rm -rf",
                            },
                        }
                    ]
                }
            )

            result = evaluate_guard_request(
                request=GuardRequest(
                    action_type="shell.command",
                    tool="shell",
                    arguments={"command": "rm -rf /tmp/aion"},
                    agent_id="agent-1",
                    owner="team-1",
                ),
                policy=policy,
                receipt_sink=JsonlReceiptSink(receipt_path),
            )

            self.assertEqual(result.decision.action, "block")
            self.assertEqual(result.receipt["stage"], "guard")
            self.assertEqual(result.receipt["action_type"], "shell.command")
            receipts = verify_jsonl(receipt_path)
            self.assertEqual(receipts[0]["decision"], "block")

    def test_allows_safe_action(self):
        policy = Policy.from_dict({"default_action": "allow"})

        result = evaluate_guard_request(
            request=GuardRequest(
                action_type="file.read",
                tool="read_file",
                arguments={"path": "README.md"},
            ),
            policy=policy,
        )

        self.assertEqual(result.decision.action, "allow")
        self.assertEqual(len(result.receipt["receipt_hash"]), 64)


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

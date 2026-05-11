import asyncio
import json
import shutil
import unittest
import uuid
from pathlib import Path

from aion_core.firewall import _inspect_request_line
from aion_core.policy import Policy
from aion_core.receipts import JsonlReceiptSink

WORKSPACE_TMP = Path(__file__).resolve().parents[1] / "test-output" / "unit"


class FirewallInspectTests(unittest.TestCase):
    def test_non_tool_call_passes_through(self):
        async def run():
            with temporary_workspace_dir() as temp_dir:
                config = _config(Path(temp_dir), Policy.from_dict({"rules": []}))
                response = await _inspect_request_line(
                    b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n',
                    config,
                )
                self.assertIsNone(response)

        asyncio.run(run())

    def test_blocked_tool_call_returns_jsonrpc_error_and_receipt(self):
        async def run():
            with temporary_workspace_dir() as temp_dir:
                receipt_path = Path(temp_dir) / "receipts.jsonl"
                policy = Policy.from_dict(
                    {
                        "rules": [
                            {
                                "id": "no-delete",
                                "action": "block",
                                "reason": "No destructive command.",
                                "match": {
                                    "tool": "shell",
                                    "argument_contains": "rm -rf",
                                },
                            }
                        ]
                    }
                )
                config = _config(Path(temp_dir), policy, receipt_path)
                response = await _inspect_request_line(
                    b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"shell","arguments":{"command":"rm -rf /tmp/aion"}}}\n',
                    config,
                )

                self.assertIsNotNone(response)
                payload = json.loads(response)
                self.assertEqual(payload["id"], 7)
                self.assertEqual(payload["error"]["data"]["rule_id"], "no-delete")

                receipts = receipt_path.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(receipts), 1)
                receipt = json.loads(receipts[0])
                self.assertEqual(receipt["decision"], "block")
                self.assertEqual(receipt["tool"], "shell")

        asyncio.run(run())

    def test_allowed_tool_call_writes_receipt_and_passes_through(self):
        async def run():
            with temporary_workspace_dir() as temp_dir:
                receipt_path = Path(temp_dir) / "receipts.jsonl"
                config = _config(Path(temp_dir), Policy.from_dict({"rules": []}), receipt_path)
                response = await _inspect_request_line(
                    b'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"read_file","arguments":{"path":"README.md"}}}\n',
                    config,
                )

                self.assertIsNone(response)
                receipt = json.loads(receipt_path.read_text(encoding="utf-8").splitlines()[0])
                self.assertEqual(receipt["decision"], "allow")
                self.assertEqual(receipt["tool"], "read_file")

        asyncio.run(run())


def _config(temp_dir: Path, policy: Policy, receipt_path: Path | None = None):
    from aion_core.firewall import FirewallConfig

    return FirewallConfig(
        policy=policy,
        receipt_sink=JsonlReceiptSink(receipt_path or temp_dir / "receipts.jsonl"),
        upstream_command=["python", "-c", "pass"],
        agent_id="test-agent",
        owner="test-owner",
    )


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

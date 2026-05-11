import json
import shutil
import unittest
import uuid
from pathlib import Path

from aion_core.receipts import JsonlEventSink, JsonlReceiptSink, verify_jsonl
from aion_core.team_policy import TeamActionRequest, TeamPolicy, create_approval_event, evaluate_team_action

WORKSPACE_TMP = Path(__file__).resolve().parents[1] / "test-output" / "team-unit"


class TeamPolicyTests(unittest.TestCase):
    def test_requires_approval_and_writes_approval_request(self):
        with temporary_workspace_dir() as temp_dir:
            receipt_path = Path(temp_dir) / "team.jsonl"
            approval_path = Path(temp_dir) / "approvals.jsonl"
            policy = TeamPolicy.from_dict(
                {
                    "team_id": "demo-team",
                    "rules": [
                        {
                            "id": "prod-approval",
                            "decision": "approval_required",
                            "reason": "Production needs approval.",
                            "approvers": ["security"],
                            "match": {
                                "action_type": "cloud.*",
                                "argument_contains": "production",
                            },
                        }
                    ],
                }
            )

            result = evaluate_team_action(
                request=TeamActionRequest(
                    action_type="cloud.delete",
                    tool="aws",
                    arguments={"env": "production"},
                    team_id="demo-team",
                ),
                policy=policy,
                receipt_sink=JsonlReceiptSink(receipt_path),
                approval_sink=JsonlEventSink(approval_path),
            )

            self.assertEqual(result.decision.decision, "approval_required")
            self.assertIsNotNone(result.approval_request)
            self.assertEqual(result.approval_request["status"], "pending")
            self.assertIn("AION approval required", result.slack_payload["text"])
            receipt = verify_jsonl(receipt_path)[0]
            self.assertEqual(receipt["decision"], "approval_required")
            approval = json.loads(approval_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(approval["schema_version"], "aion.approval.v1")
            self.assertEqual(approval["status"], "pending")

    def test_blocks_secret_like_action(self):
        policy = TeamPolicy.from_dict(
            {
                "rules": [
                    {
                        "id": "no-secret",
                        "decision": "block",
                        "match": {"argument_regex": "password\\s*[:=]"},
                    }
                ]
            }
        )

        result = evaluate_team_action(
            request=TeamActionRequest(
                action_type="http.request",
                tool="http_post",
                arguments={"body": "password = hunter2"},
            ),
            policy=policy,
        )

        self.assertEqual(result.decision.decision, "block")
        self.assertIsNone(result.approval_request)

    def test_approval_event_hash(self):
        event = create_approval_event(
            approval_id="appr_1",
            approver="security",
            status="approved",
            reason="Looks controlled.",
        )

        self.assertEqual(event["status"], "approved")
        self.assertEqual(len(event["event_hash"]), 64)


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

import json
import shutil
import unittest
import uuid
from pathlib import Path

from aion_core.launchshield import main, report_to_markdown, scan_launchshield

WORKSPACE_TMP = Path(__file__).resolve().parents[1] / "test-output" / "launchshield-unit"


class LaunchShieldTests(unittest.TestCase):
    def test_mcp_shell_workflow_produces_blockers_and_risk_chains(self):
        report = scan_launchshield(
            project_name="SupportOps Agent",
            launch_stage="pilot",
            workflow=(
                "Agent reads customer data from uploaded PDFs and external email content, "
                "then can trigger refunds and send email summaries."
            ),
            tools="MCP filesystem server, shell, payment refund API, email sender, API_KEY in env.",
            mcp_config=json.dumps(
                {
                    "mcpServers": {
                        "filesystem": {
                            "command": "python",
                            "args": ["server.py", "--root", "C:/Users"],
                            "env": {"API_KEY": "demo"},
                        },
                        "shell": {"command": "powershell", "args": ["-NoProfile"]},
                    }
                }
            ),
            surfaces=["MCP", "OpenAI"],
            controls=["receipts"],
        )

        finding_ids = {finding["id"] for finding in report["findings"]}

        self.assertEqual(report["scanner_confidence"], "High")
        self.assertGreaterEqual(report["risk_chain_count"], 3)
        self.assertTrue(report["launch_blockers"])
        self.assertIn("mcp-shell-server", finding_ids)
        self.assertIn("mcp-broad-filesystem-root", finding_ids)
        self.assertIn("secret-outbound-chain", finding_ids)
        self.assertIn("mcp-shell-filesystem-chain", finding_ids)
        self.assertEqual(report["mcp"]["shell_servers"], ["shell"])

    def test_thin_input_requests_more_context(self):
        report = scan_launchshield(workflow="short", tools="", mcp_config="")

        self.assertIsNone(report["score"])
        self.assertEqual(report["grade"], "input")
        self.assertEqual(report["findings"][0]["id"], "need-real-input")
        self.assertEqual(report["evidence"], [])

    def test_invalid_mcp_json_is_reported(self):
        report = scan_launchshield(
            workflow="Agent reads customer tickets and sends email updates.",
            tools="MCP tools with customer data and email sender.",
            mcp_config='{"mcpServers":',
            surfaces=["MCP"],
        )

        finding_ids = {finding["id"] for finding in report["findings"]}

        self.assertIn("mcp-config-invalid-json", finding_ids)
        self.assertTrue(report["mcp"]["parse_error"])

    def test_cli_writes_markdown_report(self):
        with temporary_workspace_dir() as temp_dir:
            output = Path(temp_dir) / "report.md"

            exit_code = main(
                [
                    "--project-name",
                    "CLI Agent",
                    "--workflow",
                    "Agent reads customer data and can send email updates from uploaded PDF content.",
                    "--tools",
                    "email sender, CRM customer data, public endpoint without auth",
                    "--surface",
                    "OpenAI,MCP",
                    "--control",
                    "receipts",
                    "--output",
                    str(output),
                ]
            )

            text = output.read_text(encoding="utf-8")

            self.assertEqual(exit_code, 0)
            self.assertIn("# AION LaunchShield Report", text)
            self.assertIn("Detected Surfaces", text)
            self.assertIn("Launch Blockers", text)


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

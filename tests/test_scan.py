import json
import shutil
import unittest
import uuid
from pathlib import Path

from aion_core.scan import scan_file, scan_path, summarize_findings

WORKSPACE_TMP = Path(__file__).resolve().parents[1] / "test-output" / "scan-unit"


class ScanTests(unittest.TestCase):
    def test_flags_unprotected_mcp_server(self):
        with temporary_workspace_dir() as temp_dir:
            config_path = Path(temp_dir) / "mcp.json"
            config_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "raw-filesystem": {
                                "command": "npx",
                                "args": ["@modelcontextprotocol/server-filesystem", "."],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            findings = scan_file(config_path)
            codes = {finding.code for finding in findings}

            self.assertIn("unprotected-mcp-server", codes)
            self.assertIn("powerful-mcp-server", codes)

    def test_allows_aion_wrapped_mcp_server(self):
        with temporary_workspace_dir() as temp_dir:
            config_path = Path(temp_dir) / "mcp.json"
            config_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "protected": {
                                "command": "aion-mcp-firewall",
                                "args": ["--", "npx", "@modelcontextprotocol/server-filesystem", "."],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            findings = scan_file(config_path)
            codes = {finding.code for finding in findings}

            self.assertNotIn("unprotected-mcp-server", codes)
            self.assertIn("powerful-mcp-server", codes)

    def test_summarizes_policy_findings(self):
        with temporary_workspace_dir() as temp_dir:
            policy_path = Path(temp_dir) / "policy.json"
            policy_path.write_text('{"default_action":"allow","rules":[]}', encoding="utf-8")

            summary = summarize_findings(scan_path(policy_path))

            self.assertEqual(summary["total"], 3)
            self.assertEqual(summary["by_severity"]["medium"], 1)


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

import subprocess
import sys
import unittest
from pathlib import Path


class RealWorldCapacityTests(unittest.TestCase):
    def test_release_ops_capacity_test_passes(self):
        output_dir = Path("test-output") / "real-world-capacity"
        completed = subprocess.run(
            [
                sys.executable,
                "examples/real_world_capacity/release_ops_capacity_test.py",
                "--output-dir",
                str(output_dir),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = (output_dir / "capacity_report.json").read_text(encoding="utf-8")
        self.assertIn('"failed": 0', report)
        self.assertIn('"workflow": "release-ops-agent-production-readiness"', report)
        self.assertIn('"stage": "mcp-firewall"', report)
        self.assertIn('"stage": "team-policy"', report)
        self.assertIn('"stage": "control-panel"', report)
        self.assertTrue((output_dir / "cloud_receipt_bundle.json").exists())
        self.assertTrue((output_dir / "control_panel_summary.json").exists())

    def test_hardcore_single_agent_capacity_test_passes(self):
        output_dir = Path("test-output") / "single-agent-capacity"
        completed = subprocess.run(
            [
                sys.executable,
                "examples/real_world_capacity/support_agent_capacity_test.py",
                "--output-dir",
                str(output_dir),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = (output_dir / "capacity_report.json").read_text(encoding="utf-8")
        self.assertIn('"failed": 0', report)
        self.assertIn('"schema_version": "aion.single_agent_capacity.v1"', report)
        self.assertIn('"stage": "mcp-firewall"', report)
        self.assertIn('"stage": "team-policy"', report)
        self.assertIn('"stage": "control-panel"', report)
        self.assertTrue((output_dir / "cloud_receipt_bundle.json").exists())
        self.assertTrue((output_dir / "control_panel_summary.json").exists())

    def test_hardcore_multi_agent_capacity_test_passes(self):
        output_dir = Path("test-output") / "multi-agent-capacity"
        completed = subprocess.run(
            [
                sys.executable,
                "examples/real_world_capacity/multi_agent_capacity_test.py",
                "--output-dir",
                str(output_dir),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        report = (output_dir / "capacity_report.json").read_text(encoding="utf-8")
        self.assertIn('"failed": 0', report)
        self.assertIn('"schema_version": "aion.multi_agent_capacity.v1"', report)
        self.assertIn("planner-agent", report)
        self.assertIn("research-agent", report)
        self.assertIn("coding-agent", report)
        self.assertIn("ops-agent", report)
        self.assertTrue((output_dir / "cloud_receipt_bundle.json").exists())
        self.assertTrue((output_dir / "control_panel_summary.json").exists())


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from aion_core.demo import main


class DemoTests(unittest.TestCase):
    def test_aion_demo_passes(self):
        output_dir = Path("test-output") / "demo-test"
        result = main(["--output-dir", str(output_dir)])

        self.assertEqual(result, 0)
        receipts = (output_dir / "receipts.jsonl").read_text(encoding="utf-8")
        self.assertIn('"decision": "block"', receipts)
        self.assertIn('"decision": "allow"', receipts)
        self.assertIn('"stage": "guard"', receipts)
        self.assertIn('"stage": "mcp-firewall"', receipts)
        self.assertIn('"stage": "team-policy"', receipts)
        self.assertTrue((output_dir / "unprotected_mcp.json").exists())
        approvals = (output_dir / "approvals.jsonl").read_text(encoding="utf-8")
        self.assertIn('"schema_version": "aion.approval.v1"', approvals)


if __name__ == "__main__":
    unittest.main()

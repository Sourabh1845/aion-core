import importlib.util
import sys
import unittest
from pathlib import Path


def load_proof_module():
    path = Path("examples") / "proof_pack" / "agent_workflow_proof.py"
    spec = importlib.util.spec_from_file_location("agent_workflow_proof", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProofPackTests(unittest.TestCase):
    def test_agent_workflow_proof_pack_passes(self):
        module = load_proof_module()
        output_dir = Path("test-output") / "proof-pack-test"

        result = module.main(["--output-dir", str(output_dir)])

        self.assertEqual(result, 0)
        proof = (output_dir / "proof_results.json").read_text(encoding="utf-8")
        receipts = (output_dir / "receipts.jsonl").read_text(encoding="utf-8")
        approvals = (output_dir / "approvals.jsonl").read_text(encoding="utf-8")
        self.assertIn('"total_scenarios": 6', proof)
        self.assertIn('"failed": 0', proof)
        self.assertIn("LangChain-style tool agent", proof)
        self.assertIn("CrewAI-style", proof)
        self.assertIn("Groq function-calling agent", proof)
        self.assertIn('"decision": "block"', receipts)
        self.assertIn('"decision": "allow"', receipts)
        self.assertIn('"decision": "approval_required"', receipts)
        self.assertIn('"schema_version": "aion.approval.v1"', approvals)


if __name__ == "__main__":
    unittest.main()

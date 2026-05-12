import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


@unittest.skipUnless(has_module("langchain_core"), "langchain_core is not installed")
class RealLangChainIntegrationTests(unittest.TestCase):
    def test_real_langchain_tool_integration(self):
        output_dir = Path("test-output") / "real-langchain"
        completed = subprocess.run(
            [
                sys.executable,
                "examples/real_integrations/langchain_real_test.py",
                "--output-dir",
                str(output_dir),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = (output_dir / "langchain_result.json").read_text(encoding="utf-8")
        self.assertIn('"failed": 0', result)
        self.assertIn('"sdk": "langchain"', result)


@unittest.skipUnless(has_module("crewai"), "crewai is not installed")
class RealCrewAIIntegrationTests(unittest.TestCase):
    def test_real_crewai_tool_integration(self):
        output_dir = Path("test-output") / "real-crewai"
        completed = subprocess.run(
            [
                sys.executable,
                "examples/real_integrations/crewai_real_test.py",
                "--output-dir",
                str(output_dir),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = (output_dir / "crewai_result.json").read_text(encoding="utf-8")
        self.assertIn('"failed": 0', result)
        self.assertIn('"sdk": "crewai"', result)


if __name__ == "__main__":
    unittest.main()

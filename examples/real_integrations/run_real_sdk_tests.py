"""Run real SDK integration tests for AION Core."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AION real SDK integration tests.")
    parser.add_argument("--output-dir", default="real-test-output")
    parser.add_argument("--require-groq-live", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scripts = [
        ("langchain", Path(__file__).with_name("langchain_real_test.py"), []),
        ("crewai", Path(__file__).with_name("crewai_real_test.py"), []),
        (
            "groq",
            Path(__file__).with_name("groq_live_test.py"),
            ["--require-api-key"] if args.require_groq_live else [],
        ),
    ]
    results = []
    failures = 0

    for name, script, extra_args in scripts:
        sdk_output = output_dir / name
        command = [sys.executable, str(script), "--output-dir", str(sdk_output), *extra_args]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        status = "passed" if completed.returncode == 0 else "failed"
        if name == "groq" and completed.returncode == 0 and not os.environ.get("GROQ_API_KEY"):
            status = "skipped"
        if completed.returncode != 0:
            failures += 1
        results.append(
            {
                "sdk": name,
                "status": status,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
        print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, end="", file=sys.stderr)

    summary = {
        "schema_version": "aion.real_sdk_summary.v1",
        "total": len(results),
        "passed": sum(1 for result in results if result["status"] == "passed"),
        "skipped": sum(1 for result in results if result["status"] == "skipped"),
        "failed": failures,
        "results": results,
    }
    (output_dir / "real_sdk_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Real SDK summary: {summary['passed']} passed, {summary['skipped']} skipped, {summary['failed']} failed")
    print(f"Summary: {output_dir / 'real_sdk_summary.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

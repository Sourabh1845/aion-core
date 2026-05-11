"""CLI for AION Scan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .scan import scan_path, summarize_findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aion-scan",
        description="Scan MCP configs and AION policies for risky agent tool exposure.",
    )
    parser.add_argument("path", help="File or directory to scan.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit with code 1 if high-severity findings exist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = scan_path(Path(args.path))
    summary = summarize_findings(findings)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"AION Scan: {summary['total']} finding(s)")
        for finding in findings:
            target = f" [{finding.target}]" if finding.target else ""
            print(f"- {finding.severity.upper()} {finding.code}{target}: {finding.message} ({finding.path})")

    has_high = any(finding.severity == "high" for finding in findings)
    return 1 if args.fail_on_high and has_high else 0


if __name__ == "__main__":
    raise SystemExit(main())

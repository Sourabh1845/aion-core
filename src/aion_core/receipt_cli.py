"""CLI for AION receipt verification and inspection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .receipts import ReceiptVerificationError, summarize_receipts, verify_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aion-receipts",
        description="Verify and inspect AION receipt logs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="Verify receipt hashes and schema.")
    verify.add_argument("path", help="Path to a JSONL receipt log.")

    inspect = subparsers.add_parser("inspect", help="Print a receipt summary.")
    inspect.add_argument("path", help="Path to a JSONL receipt log.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = Path(args.path)

    try:
        receipts = verify_jsonl(path)
    except (OSError, ReceiptVerificationError) as exc:
        print(f"aion-receipts: verification failed: {exc}", file=sys.stderr)
        return 1

    if args.command == "verify":
        print(f"OK: verified {len(receipts)} receipt(s)")
        return 0

    if args.command == "inspect":
        print(json.dumps(summarize_receipts(receipts), indent=2, sort_keys=True))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

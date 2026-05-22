"""CLI for AION receipt verification and inspection."""

from __future__ import annotations

import argparse
import json
import os
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
    verify.add_argument("--signing-key", help="HMAC key used to verify signed receipts.")
    verify.add_argument("--signing-key-env", help="Environment variable containing the HMAC signing key.")
    verify.add_argument("--require-signature", action="store_true", help="Reject receipts without HMAC signatures.")

    inspect = subparsers.add_parser("inspect", help="Print a receipt summary.")
    inspect.add_argument("path", help="Path to a JSONL receipt log.")
    inspect.add_argument("--signing-key", help="HMAC key used to verify signed receipts.")
    inspect.add_argument("--signing-key-env", help="Environment variable containing the HMAC signing key.")
    inspect.add_argument("--require-signature", action="store_true", help="Reject receipts without HMAC signatures.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    path = Path(args.path)

    try:
        signing_key = _resolve_signing_key(args)
        receipts = verify_jsonl(path, signing_key=signing_key, require_signature=args.require_signature)
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


def _resolve_signing_key(args: argparse.Namespace) -> str | None:
    if args.signing_key and args.signing_key_env:
        raise ReceiptVerificationError("use only one of --signing-key or --signing-key-env")
    if args.signing_key:
        return args.signing_key
    if args.signing_key_env:
        value = os.environ.get(args.signing_key_env)
        if not value:
            raise ReceiptVerificationError(f"environment variable is not set: {args.signing_key_env}")
        return value
    return None


if __name__ == "__main__":
    raise SystemExit(main())

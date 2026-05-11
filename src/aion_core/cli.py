"""Command-line entry point for the AION MCP firewall."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import traceback
from pathlib import Path

from .firewall import FirewallConfig, run_stdio_firewall
from .policy import Policy
from .receipts import JsonlReceiptSink


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aion-mcp-firewall",
        description="Run AION as a stdio MCP firewall in front of an upstream MCP server.",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="Path to a JSON AION policy file.",
    )
    parser.add_argument(
        "--receipt-log",
        default="receipts/aion-mcp-firewall.jsonl",
        help="Path to the JSONL receipt log. Default: receipts/aion-mcp-firewall.jsonl",
    )
    parser.add_argument(
        "--agent-id",
        default="unknown-agent",
        help="Agent identity attached to receipts.",
    )
    parser.add_argument(
        "--owner",
        default="local",
        help="Owner/team identity used by owner policy matchers.",
    )
    parser.add_argument(
        "--fail-closed",
        action="store_true",
        help="Block tool calls if policy evaluation raises an unexpected error.",
    )
    parser.add_argument(
        "upstream",
        nargs=argparse.REMAINDER,
        help="Upstream MCP server command after --, for example: -- python server.py",
    )
    return parser


def normalize_upstream(raw: list[str]) -> list[str]:
    if raw and raw[0] == "--":
        return raw[1:]
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    upstream = normalize_upstream(args.upstream)
    if not upstream:
        parser.error("missing upstream MCP server command after --")

    policy = Policy.from_file(Path(args.policy))
    receipt_sink = JsonlReceiptSink(Path(args.receipt_log))
    config = FirewallConfig(
        policy=policy,
        receipt_sink=receipt_sink,
        upstream_command=upstream,
        agent_id=args.agent_id,
        owner=args.owner,
        fail_closed=args.fail_closed,
    )

    try:
        return asyncio.run(run_stdio_firewall(config))
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        return 0
    except Exception as exc:
        if os.getenv("AION_DEBUG"):
            traceback.print_exc(file=sys.stderr)
        print(f"aion-mcp-firewall: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Stdio MCP firewall proxy."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, BinaryIO

from .policy import Decision, Policy
from .receipts import ReceiptSink


@dataclass(frozen=True)
class FirewallConfig:
    policy: Policy
    receipt_sink: ReceiptSink
    upstream_command: list[str]
    agent_id: str = "unknown-agent"
    owner: str = "local"
    fail_closed: bool = False


async def run_stdio_firewall(config: FirewallConfig) -> int:
    return await asyncio.to_thread(_run_stdio_firewall_sync, config)


def _run_stdio_firewall_sync(config: FirewallConfig) -> int:
    process = subprocess.Popen(
        config.upstream_command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    stdout_thread = threading.Thread(
        target=_relay_file_to_output,
        args=(process.stdout, sys.stdout.buffer),
        daemon=True,
    )
    stderr_thread = threading.Thread(
        target=_relay_file_to_output,
        args=(process.stderr, sys.stderr.buffer),
        daemon=True,
    )
    stdout_thread.start()
    stderr_thread.start()

    try:
        for line in sys.stdin.buffer:
            maybe_response = _inspect_request_line_sync(line, config)
            if maybe_response is not None:
                sys.stdout.buffer.write(maybe_response)
                sys.stdout.buffer.flush()
                continue

            process.stdin.write(line)
            process.stdin.flush()
    finally:
        try:
            process.stdin.close()
        except OSError:
            pass

    try:
        return_code = process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        _stop_process_sync(process)
        return_code = process.returncode or 1

    stdout_thread.join(timeout=1)
    stderr_thread.join(timeout=1)
    return return_code or 0


def _stop_process_sync(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
    except (PermissionError, ProcessLookupError):
        return
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except (PermissionError, ProcessLookupError):
            return
        process.wait(timeout=2)


def _relay_file_to_output(reader: BinaryIO, output: BinaryIO) -> None:
    for line in iter(reader.readline, b""):
        output.write(line)
        output.flush()


async def _inspect_request_line(line: bytes, config: FirewallConfig) -> bytes | None:
    return _inspect_request_line_sync(line, config)


def _inspect_request_line_sync(line: bytes, config: FirewallConfig) -> bytes | None:
    try:
        message = json.loads(line)
    except json.JSONDecodeError:
        return None

    if not isinstance(message, dict):
        return None
    if message.get("method") != "tools/call":
        return None

    request_id = message.get("id")
    params = message.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    tool_name = str(params.get("name", ""))
    arguments = params.get("arguments") or {}

    try:
        decision = config.policy.evaluate_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            agent_id=config.agent_id,
            owner=config.owner,
    )
    except Exception as exc:
        if not config.fail_closed:
            _write_receipt(
                config,
                Decision.allow(
                    reason=f"Policy evaluation failed open: {exc}",
                    rule_id="policy-error-open",
                ),
                request_id,
                tool_name,
                arguments,
            )
            return None
        decision = Decision.block(
            reason=f"Policy evaluation failed closed: {exc}",
            rule_id="policy-error-closed",
        )

    _write_receipt(config, decision, request_id, tool_name, arguments)
    if decision.action == "allow":
        return None
    return _jsonrpc_block_response(request_id, decision)


def _write_receipt(
    config: FirewallConfig,
    decision: Decision,
    request_id: Any,
    tool_name: str,
    arguments: Any,
) -> None:
    config.receipt_sink.write(
        {
            "ts": datetime.now(timezone.utc).isoformat(),
            "schema_version": "aion.receipt.v1",
            "stage": "mcp-firewall",
            "component": "aion-mcp-firewall",
            "agent_id": config.agent_id,
            "owner": config.owner,
            "request_id": request_id,
            "action_type": "mcp.tools_call",
            "tool": tool_name,
            "decision": decision.action,
            "rule_id": decision.rule_id,
            "reason": decision.reason,
            "risk": "blocked" if decision.action == "block" else "accepted",
            "argument_fingerprint": config.policy.fingerprint(arguments),
            "metadata": {
                "mcp_method": "tools/call",
            },
        }
    )


def _jsonrpc_block_response(request_id: Any, decision: Decision) -> bytes:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32090,
            "message": "AION firewall blocked this MCP tool call.",
            "data": {
                "decision": decision.action,
                "rule_id": decision.rule_id,
                "reason": decision.reason,
            },
        },
    }
    return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")

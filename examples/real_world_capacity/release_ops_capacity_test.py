"""End-to-end real-world capacity test for AION Core.

Scenario: a release-ops AI agent is preparing a production release. AION must
scan weak MCP config, allow safe reads, block destructive shell actions, require
approval for production mutation, verify receipts, and produce a cloud/control
panel ready evidence bundle.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from aion_core.guard import GuardRequest, evaluate_guard_request
from aion_core.policy import Policy
from aion_core.receipts import JsonlEventSink, JsonlReceiptSink, summarize_receipts, verify_jsonl
from aion_core.scan import scan_file
from aion_core.team_policy import TeamActionRequest, TeamPolicy, evaluate_team_action


POLICY_DATA = {
    "default_action": "allow",
    "rules": [
        {
            "id": "block-destructive-shell",
            "action": "block",
            "reason": "Destructive shell command patterns require explicit approval.",
            "match": {
                "tool": ["shell", "terminal", "run_command"],
                "argument_contains": ["rm -rf", "Remove-Item", "del /s", "git reset --hard", "drop database"],
            },
        },
        {
            "id": "block-secret-exfiltration",
            "action": "block",
            "reason": "Potential secret exfiltration attempt.",
            "match": {
                "tool": "*",
                "argument_regex": ["api[_-]?key", "secret[_-]?key", "password\\s*[:=]"],
            },
        },
    ],
}


TEAM_POLICY_DATA = {
    "team_id": "release-platform",
    "default_decision": "allow",
    "rules": [
        {
            "id": "approval-production-mutation",
            "decision": "approval_required",
            "reason": "Production mutations require platform/security approval.",
            "approvers": ["platform-lead", "security-reviewer"],
            "approval_ttl_minutes": 30,
            "match": {
                "action_type": ["deploy.*", "cloud.*"],
                "argument_regex": ["\\bproduction\\b", "\\bdelete\\b", "\\bdestroy\\b"],
            },
        }
    ],
}


DEMO_MCP_SERVER = """
import json
import sys

for line in sys.stdin:
    request = json.loads(line)
    params = request.get("params") or {}
    response = {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": "release ops tool executed: " + str(params.get("name")),
                }
            ]
        },
    }
    print(json.dumps(response, separators=(",", ":")), flush=True)
""".strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AION real-world release ops capacity test.")
    parser.add_argument("--output-dir", default="real-world-output/release-ops")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    prepare_output_dir(output_dir)

    policy_path = output_dir / "policy.json"
    team_policy_path = output_dir / "team_policy.json"
    receipts_path = output_dir / "receipts.jsonl"
    approvals_path = output_dir / "approvals.jsonl"
    mcp_server_path = output_dir / "release_ops_mcp_server.py"
    weak_mcp_path = output_dir / "weak_mcp_config.json"
    cloud_bundle_path = output_dir / "cloud_receipt_bundle.json"
    control_panel_path = output_dir / "control_panel_summary.json"
    report_path = output_dir / "capacity_report.json"

    policy_path.write_text(json.dumps(POLICY_DATA, indent=2), encoding="utf-8")
    team_policy_path.write_text(json.dumps(TEAM_POLICY_DATA, indent=2), encoding="utf-8")
    mcp_server_path.write_text(DEMO_MCP_SERVER + "\n", encoding="utf-8")
    weak_mcp_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "raw-release-shell": {
                        "command": "python",
                        "args": ["release_ops_tool.py"],
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    policy = Policy.from_file(policy_path)
    team_policy = TeamPolicy.from_file(team_policy_path)
    receipt_sink = JsonlReceiptSink(receipts_path)
    approval_sink = JsonlEventSink(approvals_path)
    results: list[dict[str, Any]] = []
    failures = 0

    scan_findings = scan_file(weak_mcp_path)
    scan_passed = any(finding.code == "unprotected-mcp-server" for finding in scan_findings)
    failures += 0 if scan_passed else 1
    results.append(
        {
            "stage": "scan",
            "scenario": "detect weak release MCP config before production workflow",
            "expected": "unprotected-mcp-server finding",
            "actual": [finding.code for finding in scan_findings],
            "passed": scan_passed,
        }
    )

    guard_safe = evaluate_guard_request(
        request=GuardRequest(
            action_type="file.read",
            tool="read_file",
            arguments={"path": "CHANGELOG.md"},
            agent_id="release-ops-agent",
            owner="release-platform",
            request_id="release-guard-safe",
            metadata={"workflow": "release-readiness"},
        ),
        policy=policy,
        receipt_sink=receipt_sink,
    )
    safe_passed = guard_safe.decision.action == "allow"
    failures += 0 if safe_passed else 1
    results.append(
        {
            "stage": "guard",
            "scenario": "allow release agent to read changelog",
            "expected": "allow",
            "actual": guard_safe.decision.action,
            "receipt_id": guard_safe.receipt["receipt_id"],
            "passed": safe_passed,
        }
    )

    guard_block = evaluate_guard_request(
        request=GuardRequest(
            action_type="shell.command",
            tool="shell",
            arguments={"command": "git reset --hard && rm -rf ./production"},
            agent_id="release-ops-agent",
            owner="release-platform",
            request_id="release-guard-block",
            metadata={"workflow": "release-readiness"},
        ),
        policy=policy,
        receipt_sink=receipt_sink,
    )
    block_passed = guard_block.decision.action == "block"
    failures += 0 if block_passed else 1
    results.append(
        {
            "stage": "guard",
            "scenario": "block destructive release cleanup command",
            "expected": "block",
            "actual": guard_block.decision.action,
            "receipt_id": guard_block.receipt["receipt_id"],
            "passed": block_passed,
        }
    )

    mcp_safe = run_mcp_case(
        request={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "read_file", "arguments": {"path": "README.md"}},
        },
        policy_path=policy_path,
        receipts_path=receipts_path,
        server_path=mcp_server_path,
    )
    mcp_safe_passed = "result" in mcp_safe
    failures += 0 if mcp_safe_passed else 1
    results.append(
        {
            "stage": "mcp-firewall",
            "scenario": "allow safe MCP read tool call",
            "expected": "result",
            "actual": "result" if "result" in mcp_safe else "error",
            "passed": mcp_safe_passed,
        }
    )

    mcp_block = run_mcp_case(
        request={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "shell", "arguments": {"command": "rm -rf ./production"}},
        },
        policy_path=policy_path,
        receipts_path=receipts_path,
        server_path=mcp_server_path,
    )
    mcp_block_passed = mcp_block.get("error", {}).get("code") == -32090
    failures += 0 if mcp_block_passed else 1
    results.append(
        {
            "stage": "mcp-firewall",
            "scenario": "block destructive MCP shell tool call",
            "expected": "AION JSON-RPC block error",
            "actual": mcp_block.get("error", {}).get("message", "no error"),
            "passed": mcp_block_passed,
        }
    )

    team_result = evaluate_team_action(
        request=TeamActionRequest(
            action_type="deploy.production",
            tool="deployment_controller",
            arguments={"environment": "production", "operation": "delete old deployment slot"},
            agent_id="release-ops-agent",
            owner="release-platform",
            team_id="release-platform",
            request_id="release-team-approval",
            metadata={"workflow": "release-readiness"},
        ),
        policy=team_policy,
        receipt_sink=receipt_sink,
        approval_sink=approval_sink,
    )
    approval_passed = team_result.decision.decision == "approval_required" and team_result.approval_request is not None
    failures += 0 if approval_passed else 1
    results.append(
        {
            "stage": "team-policy",
            "scenario": "require approval for production deployment mutation",
            "expected": "approval_required",
            "actual": team_result.decision.decision,
            "approval_id": team_result.approval_request["approval_id"] if team_result.approval_request else None,
            "passed": approval_passed,
        }
    )

    receipts = verify_jsonl(receipts_path)
    receipt_summary = summarize_receipts(receipts)
    cloud_bundle = {
        "schema_version": "aion.cloud_upload_bundle.v1",
        "receipt_count": len(receipts),
        "receipts": receipts,
    }
    cloud_bundle_path.write_text(json.dumps(cloud_bundle, indent=2), encoding="utf-8")
    cloud_passed = all(receipt.get("schema_version") == "aion.receipt.v1" for receipt in receipts)
    failures += 0 if cloud_passed else 1
    results.append(
        {
            "stage": "cloud-alignment",
            "scenario": "produce AION Cloud compatible receipt upload bundle",
            "expected": "all receipts are aion.receipt.v1",
            "actual": cloud_bundle["receipt_count"],
            "passed": cloud_passed,
        }
    )

    control_panel = {
        "schema_version": "aion.control_panel_summary.v1",
        "workflow": "release-readiness",
        "total_receipts": receipt_summary["total"],
        "decisions": receipt_summary["decisions"],
        "tools": receipt_summary["tools"],
        "rules": receipt_summary["rules"],
        "pending_approvals": 1 if approval_passed else 0,
    }
    control_panel_path.write_text(json.dumps(control_panel, indent=2), encoding="utf-8")
    control_panel_passed = control_panel["pending_approvals"] == 1 and control_panel["decisions"].get("block", 0) >= 2
    failures += 0 if control_panel_passed else 1
    results.append(
        {
            "stage": "control-panel",
            "scenario": "summarize release workflow risks for operator view",
            "expected": "blocks and pending approval visible",
            "actual": control_panel,
            "passed": control_panel_passed,
        }
    )

    report = {
        "schema_version": "aion.real_world_capacity.v1",
        "workflow": "release-ops-agent-production-readiness",
        "stages_covered": [
            "guard",
            "receipts",
            "scan",
            "docs-demo-report",
            "cloud-alignment",
            "mcp-firewall",
            "team-policy",
            "control-panel",
        ],
        "total_scenarios": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": failures,
        "receipt_summary": receipt_summary,
        "artifacts": {
            "receipts": str(receipts_path),
            "approvals": str(approvals_path),
            "cloud_bundle": str(cloud_bundle_path),
            "control_panel_summary": str(control_panel_path),
        },
        "results": results,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("AION Real-World Capacity Test")
    print("Workflow: release ops agent production readiness")
    print(f"Scenarios: {report['passed']}/{report['total_scenarios']} passed")
    print(f"Receipts: {receipt_summary['total']} hash-verified")
    print(f"Pending approvals: {control_panel['pending_approvals']}")
    print(f"Report: {report_path}")
    return 1 if failures else 0


def run_mcp_case(*, request: dict[str, Any], policy_path: Path, receipts_path: Path, server_path: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "aion_core.cli",
        "--policy",
        str(policy_path),
        "--receipt-log",
        str(receipts_path),
        "--agent-id",
        "release-ops-agent",
        "--owner",
        "release-platform",
        "--",
        sys.executable,
        str(server_path),
    ]
    completed = subprocess.run(
        command,
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    for line in completed.stdout.splitlines():
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return {"raw_stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode}


def prepare_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())

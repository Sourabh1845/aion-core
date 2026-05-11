"""AION Scan for MCP configs and AION policy files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ScanFinding:
    severity: str
    code: str
    message: str
    path: str
    target: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "target": self.target,
        }


def scan_path(path: Path) -> list[ScanFinding]:
    if path.is_file():
        return scan_file(path)
    findings: list[ScanFinding] = []
    for file_path in path.rglob("*.json"):
        if any(part in {".git", "__pycache__", "test-output"} for part in file_path.parts):
            continue
        findings.extend(scan_file(file_path))
    return findings


def scan_file(path: Path) -> list[ScanFinding]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, dict):
        return []

    findings: list[ScanFinding] = []
    if "mcpServers" in data:
        findings.extend(scan_mcp_config(path, data))
    if "rules" in data or "default_action" in data:
        findings.extend(scan_policy(path, data))
    return findings


def scan_mcp_config(path: Path, data: dict[str, Any]) -> list[ScanFinding]:
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return [
            ScanFinding(
                severity="high",
                code="invalid-mcp-config",
                message="mcpServers must be a JSON object.",
                path=str(path),
            )
        ]

    findings: list[ScanFinding] = []
    for name, server in servers.items():
        if not isinstance(server, dict):
            findings.append(
                ScanFinding(
                    severity="high",
                    code="invalid-mcp-server",
                    message="MCP server entry must be a JSON object.",
                    path=str(path),
                    target=str(name),
                )
            )
            continue

        command = str(server.get("command", ""))
        args = [str(arg) for arg in server.get("args", []) if arg is not None]
        if not is_aion_protected(command, args):
            findings.append(
                ScanFinding(
                    severity="high",
                    code="unprotected-mcp-server",
                    message="MCP server is not wrapped by AION MCP Firewall.",
                    path=str(path),
                    target=str(name),
                )
            )
        if mentions_risky_tool(command, args):
            findings.append(
                ScanFinding(
                    severity="medium",
                    code="powerful-mcp-server",
                    message="MCP server appears to expose filesystem, shell, browser, or cloud capabilities.",
                    path=str(path),
                    target=str(name),
                )
            )
    return findings


def scan_policy(path: Path, data: dict[str, Any]) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    default_action = str(data.get("default_action", "allow")).lower()
    rules = data.get("rules") or []
    if not isinstance(rules, list):
        return [
            ScanFinding(
                severity="high",
                code="invalid-policy-rules",
                message="Policy rules must be a JSON list.",
                path=str(path),
            )
        ]

    if default_action == "allow" and not rules:
        findings.append(
            ScanFinding(
                severity="medium",
                code="empty-allow-policy",
                message="Policy allows by default and has no rules.",
                path=str(path),
            )
        )

    serialized = json.dumps(data, sort_keys=True).lower()
    if "rm -rf" not in serialized and "remove-item" not in serialized:
        findings.append(
            ScanFinding(
                severity="low",
                code="missing-destructive-shell-rule",
                message="Policy does not appear to block common destructive shell patterns.",
                path=str(path),
            )
        )
    if "password" not in serialized and "secret" not in serialized and "api" not in serialized:
        findings.append(
            ScanFinding(
                severity="low",
                code="missing-secret-exfiltration-rule",
                message="Policy does not appear to block common secret exfiltration patterns.",
                path=str(path),
            )
        )
    return findings


def is_aion_protected(command: str, args: Iterable[str]) -> bool:
    joined = " ".join([command, *args]).lower()
    return "aion-mcp-firewall" in joined or "aion_core.cli" in joined


def mentions_risky_tool(command: str, args: Iterable[str]) -> bool:
    joined = " ".join([command, *args]).lower()
    risky_terms = [
        "filesystem",
        "shell",
        "terminal",
        "browser",
        "aws",
        "gcloud",
        "azure",
        "postgres",
        "database",
    ]
    return any(term in joined for term in risky_terms)


def summarize_findings(findings: list[ScanFinding]) -> dict[str, Any]:
    by_severity: dict[str, int] = {}
    for finding in findings:
        by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
    return {
        "total": len(findings),
        "by_severity": by_severity,
        "findings": [finding.to_dict() for finding in findings],
    }

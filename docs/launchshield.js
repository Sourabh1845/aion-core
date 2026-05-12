const stages = [
  ["AION Guard", "Runtime action control"],
  ["AION Receipts", "Decision evidence"],
  ["AION Scan", "Risk discovery"],
  ["Docs + Demo", "Launch report"],
  ["AION Cloud", "Receipt bundle"],
  ["MCP Firewall", "Tool-call firewall"],
  ["Team Policy", "Approval rules"],
  ["Control Panel", "Operator summary"],
];

const rulebook = [
  {
    id: "destructive-shell",
    severity: "critical",
    weight: 22,
    stage: "AION Guard",
    title: "Destructive shell or system command surface",
    pattern: /\b(rm\s+-rf|del\s+\/s|Remove-Item|format\s|shutdown|sudo\s|chmod\s+777|curl\s+.*\|\s*(bash|sh)|powershell\s+-enc)\b/i,
    fix: "Put shell/system tools behind AION Guard, block destructive commands by default, and require explicit approval for production mutations.",
    block: true,
  },
  {
    id: "secret-exfiltration",
    severity: "critical",
    weight: 24,
    stage: "AION Guard",
    title: "Secret or credential exfiltration risk",
    pattern: /\b(api[_-]?key|secret|token|credential|password|\.env|ssh key|private key|send.*env|print.*env|exfiltrat)\b/i,
    fix: "Isolate secrets, redact tool arguments, and block requests that expose environment variables, API keys, or private credentials.",
    block: true,
  },
  {
    id: "mcp-unguarded",
    severity: "high",
    weight: 16,
    stage: "MCP Firewall",
    title: "MCP/tool server appears exposed without a firewall",
    pattern: /\b(mcp|tools\/call|stdio server|tool server|filesystem server|browser server)\b/i,
    fix: "Run the MCP server behind AION MCP Firewall and log every allow/block decision.",
    block: true,
  },
  {
    id: "database-write",
    severity: "high",
    weight: 14,
    stage: "Team Policy",
    title: "Database write or account mutation needs approval",
    pattern: /\b(delete user|delete account|drop table|database write|db write|update customer|refund|charge|payment|invoice|subscription|production deploy|prod deploy)\b/i,
    fix: "Require human approval for account, payment, database, and production mutations.",
    block: false,
  },
  {
    id: "pii-handling",
    severity: "high",
    weight: 12,
    stage: "AION Receipts",
    title: "Sensitive user data or PII is in scope",
    pattern: /\b(email address|phone number|address|ssn|aadhaar|pan card|medical|health|patient|financial|bank|credit card|customer data|crm)\b/i,
    fix: "Log receipts without leaking raw PII, minimize tool permissions, and add data-retention limits.",
    block: false,
  },
  {
    id: "browser-automation",
    severity: "medium",
    weight: 9,
    stage: "AION Guard",
    title: "Browser automation can cross trust boundaries",
    pattern: /\b(browser|playwright|selenium|scrape|crawl|web automation|login page|cookie|session)\b/i,
    fix: "Constrain browser automation to approved domains and block credential/session extraction.",
    block: false,
  },
  {
    id: "email-slack-send",
    severity: "medium",
    weight: 8,
    stage: "Team Policy",
    title: "Outbound message tool can create business risk",
    pattern: /\b(send email|email sender|slack send|post to slack|discord|webhook|sms|whatsapp)\b/i,
    fix: "Require approval or rate limits for outbound customer/team messages.",
    block: false,
  },
  {
    id: "file-system",
    severity: "medium",
    weight: 8,
    stage: "MCP Firewall",
    title: "File-system access should be least-privilege",
    pattern: /\b(file system|filesystem|read file|write file|download file|upload file|local files|documents folder)\b/i,
    fix: "Restrict paths, block destructive file writes, and record receipts for file reads/writes.",
    block: false,
  },
  {
    id: "no-auth",
    severity: "high",
    weight: 13,
    stage: "AION Scan",
    title: "Auth or ownership model is unclear",
    pattern: /\b(no auth|public endpoint|open endpoint|without auth|anonymous|any user|shared token)\b/i,
    fix: "Add owner identity, per-agent permissions, and separate user/team scopes before launch.",
    block: false,
  },
  {
    id: "prompt-injection",
    severity: "high",
    weight: 15,
    stage: "AION Guard",
    title: "Prompt-injection exposure through untrusted content",
    pattern: /\b(user uploaded|webpage content|external content|email content|pdf|untrusted|ignore previous instructions|prompt injection)\b/i,
    fix: "Treat external content as untrusted, restrict tool use after retrieval, and require receipts for high-risk actions.",
    block: true,
  },
];

const controlPenalties = [
  ["humanApproval", "high", 12, "Team Policy", "Human approval is missing for sensitive actions", "Add approval-required policies for production, payment, account, and outbound communication actions."],
  ["receipts", "medium", 10, "AION Receipts", "Audit receipts are missing", "Record tamper-evident receipts for every tool-call allow/block/approval decision."],
  ["leastPrivilege", "medium", 8, "Agent Identity", "Least-privilege boundaries are not declared", "Declare agent identity, owner, scope, allowed tools, and denied tools."],
  ["secretIsolation", "high", 12, "AION Guard", "Secret isolation is not declared", "Keep API keys out of prompts/tool outputs and block exfiltration patterns."],
  ["sandbox", "medium", 7, "MCP Firewall", "Sandboxing is not declared", "Run risky tools in a constrained environment and limit filesystem/network access."],
  ["rateLimits", "low", 4, "Control Panel", "Rate limits are not declared", "Add limits and operator visibility for repeated risky actions."],
];

const samples = {
  agent: {
    projectName: "SupportOps Agent",
    launchStage: "pilot",
    workflow: "A customer support agent reads CRM tickets, summarizes customer issues, drafts email replies, checks refund eligibility, and can delete account records when a ticket asks for removal. It reads user uploaded PDFs and external email content.",
    tools: "CRM lookup, email sender, browser, file system read, payment refund API, database write, Slack webhook, access to API_KEY in environment variables.",
    mcpConfig: "{\"mcpServers\":{\"filesystem\":{\"command\":\"python\",\"args\":[\"server.py\",\"--root\",\"C:/Users\" ]},\"shell\":{\"command\":\"powershell\",\"args\":[\"-NoProfile\"]}}}",
    surfaces: ["LangChain", "MCP", "OpenAI"],
    controls: ["receipts"],
  },
  app: {
    projectName: "AI SaaS Builder Launch",
    launchStage: "pre-launch",
    workflow: "An AI-built SaaS app lets founders upload documents, scrape competitor pages, generate reports, send emails, and store customer data. It will launch publicly this week.",
    tools: "Browser automation, database write, email sender, file upload, customer data, Stripe subscription, public endpoint without auth for a demo route.",
    mcpConfig: "Deployment notes: open endpoint for demo users, shared token for internal webhook, no auth on preview route, rate limits not configured.",
    surfaces: ["AI app builder", "OpenAI"],
    controls: ["rateLimits"],
  },
};

let latestReport = null;

function checkedValues(containerId) {
  return [...document.querySelectorAll(`#${containerId} input:checked`)].map((input) => input.value);
}

function setChecked(containerId, values) {
  document.querySelectorAll(`#${containerId} input`).forEach((input) => {
    input.checked = values.includes(input.value);
  });
}

function combinedInput(form) {
  return [
    form.projectName.value,
    form.launchStage.value,
    form.workflow.value,
    form.tools.value,
    form.mcpConfig.value,
    checkedValues("surfaceChecks").join(" "),
  ].join("\n");
}

function severityRank(severity) {
  return { critical: 4, high: 3, medium: 2, low: 1 }[severity] || 0;
}

async function hashText(text) {
  if (window.crypto && window.crypto.subtle) {
    const bytes = new TextEncoder().encode(text);
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  }
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

async function receiptFor(index, finding, projectName) {
  const payload = {
    schema: "aion.launchshield.receipt.v1",
    receipt_id: `ls_${Date.now().toString(36)}_${index}`,
    project: projectName,
    decision: finding.block ? "block_simulated" : finding.severity === "high" ? "approval_recommended" : "monitor",
    rule_id: finding.id,
    severity: finding.severity,
    stage: finding.stage,
    reason: finding.title,
    created_at: new Date().toISOString(),
  };
  payload.hash = await hashText(JSON.stringify(payload));
  return payload;
}

async function analyze(form) {
  const text = combinedInput(form);
  const controls = checkedValues("controlChecks");
  const surfaces = checkedValues("surfaceChecks");
  const findings = [];

  for (const rule of rulebook) {
    if (rule.pattern.test(text)) {
      findings.push({ ...rule });
    }
  }

  const sensitiveContext = findings.some((finding) => ["critical", "high"].includes(finding.severity));
  for (const [control, severity, weight, stage, title, fix] of controlPenalties) {
    const missing = !controls.includes(control);
    if (missing && (sensitiveContext || ["humanApproval", "receipts", "leastPrivilege"].includes(control))) {
      findings.push({
        id: `missing-${control}`,
        severity,
        weight,
        stage,
        title,
        fix,
        block: false,
      });
    }
  }

  if (surfaces.includes("MCP") && !findings.some((finding) => finding.id === "mcp-unguarded")) {
    findings.push({
      id: "mcp-declared",
      severity: "medium",
      weight: 7,
      stage: "MCP Firewall",
      title: "MCP surface declared",
      fix: "Keep MCP calls behind AION Firewall and export receipts for customer evidence.",
      block: false,
    });
  }

  if (!text.trim() || text.trim().length < 80) {
    findings.push({
      id: "thin-input",
      severity: "medium",
      weight: 10,
      stage: "Docs + Demo",
      title: "Input is too thin for a confident launch audit",
      fix: "Paste the real agent prompt, tool list, MCP config, auth model, and deployment notes.",
      block: false,
    });
  }

  const uniqueFindings = [...new Map(findings.map((finding) => [finding.id, finding])).values()]
    .sort((a, b) => severityRank(b.severity) - severityRank(a.severity) || b.weight - a.weight);
  const penalty = uniqueFindings.reduce((total, finding) => total + finding.weight, 0);
  const score = Math.max(0, Math.min(100, 100 - penalty));
  const grade = score >= 82 ? "ready" : score >= 58 ? "caution" : "critical";
  const receipts = [];
  for (let i = 0; i < uniqueFindings.length; i += 1) {
    receipts.push(await receiptFor(i + 1, uniqueFindings[i], form.projectName.value.trim() || "Untitled AI workflow"));
  }

  return {
    projectName: form.projectName.value.trim() || "Untitled AI workflow",
    launchStage: form.launchStage.value,
    surfaces,
    controls,
    score,
    grade,
    findings: uniqueFindings,
    receipts,
    generatedAt: new Date().toISOString(),
  };
}

function stageActive(report, stageName) {
  if (["AION Receipts", "Docs + Demo", "AION Cloud", "Control Panel"].includes(stageName)) return true;
  return report.findings.some((finding) => finding.stage === stageName)
    || (stageName === "Team Policy" && !report.controls.includes("humanApproval"))
    || (stageName === "MCP Firewall" && report.surfaces.includes("MCP"));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderReport(report) {
  latestReport = report;
  document.getElementById("score").textContent = report.score;
  const grade = document.getElementById("grade");
  grade.className = `grade ${report.grade}`;
  grade.textContent = report.grade === "ready" ? "Launch Ready With Controls" : report.grade === "caution" ? "Needs Hardening" : "High Risk";

  const criticals = report.findings.filter((finding) => finding.severity === "critical").length;
  const highs = report.findings.filter((finding) => finding.severity === "high").length;
  document.getElementById("summary").textContent = `${report.projectName}: ${criticals} critical, ${highs} high, ${report.findings.length} total findings.`;
  document.getElementById("findingCount").textContent = report.findings.length;
  document.getElementById("blockCount").textContent = report.findings.filter((finding) => finding.block).length;
  document.getElementById("receiptCount").textContent = report.receipts.length;

  document.getElementById("findings").innerHTML = report.findings.map((finding) => `
    <div class="finding">
      <strong><span class="sev ${finding.severity}">${finding.severity}</span>${escapeHtml(finding.title)}</strong>
      <div class="muted">${escapeHtml(finding.fix)}</div>
    </div>
  `).join("");

  document.getElementById("stages").innerHTML = stages.map(([name, description], index) => `
    <div class="stage ${stageActive(report, name) ? "active" : ""}">
      <strong>${index + 1}. ${escapeHtml(name)}</strong>
      ${escapeHtml(description)}
    </div>
  `).join("");

  document.getElementById("receipts").textContent = report.receipts.map((receipt) => JSON.stringify(receipt)).join("\n");
  document.getElementById("exportReport").disabled = false;
  document.getElementById("exportReportTop").disabled = false;

  const body = encodeURIComponent(`Project: ${report.projectName}\nScore: ${report.score}\nFindings: ${report.findings.length}\n\nI want a paid AION LaunchShield audit for this AI workflow.`);
  document.getElementById("auditRequest").href = `https://github.com/Sourabh1845/aion-core/issues/new?title=AION%20LaunchShield%20audit%20request:%20${encodeURIComponent(report.projectName)}&body=${body}`;
}

function reportMarkdown(report) {
  return `# AION LaunchShield Report

Project: ${report.projectName}
Generated: ${report.generatedAt}
Launch stage: ${report.launchStage}
Score: ${report.score}/100
Status: ${report.grade}

## Findings

${report.findings.map((finding, index) => `${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}
   - AION stage: ${finding.stage}
   - Fix: ${finding.fix}`).join("\n\n")}

## AION 8-Stage Coverage

${stages.map(([name, description], index) => `${index + 1}. ${name}: ${description}`).join("\n")}

## Receipts

\`\`\`jsonl
${report.receipts.map((receipt) => JSON.stringify(receipt)).join("\n")}
\`\`\`

## Paid Audit Path

Recommended next step: human review for policy design, exact tool-call blocks, receipts, and launch-ready remediation.
`;
}

function downloadReport() {
  if (!latestReport) return;
  const markdown = reportMarkdown(latestReport);
  const blob = new Blob([markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const safeName = latestReport.projectName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "aion-launchshield";
  link.href = url;
  link.download = `${safeName}-launchshield-report.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function loadSample(sample) {
  const form = document.getElementById("auditForm");
  form.projectName.value = sample.projectName;
  form.launchStage.value = sample.launchStage;
  form.workflow.value = sample.workflow;
  form.tools.value = sample.tools;
  form.mcpConfig.value = sample.mcpConfig;
  setChecked("surfaceChecks", sample.surfaces);
  setChecked("controlChecks", sample.controls);
}

document.getElementById("auditForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const report = await analyze(event.currentTarget);
  renderReport(report);
});

document.getElementById("clearForm").addEventListener("click", () => {
  document.getElementById("auditForm").reset();
  setChecked("surfaceChecks", []);
  setChecked("controlChecks", []);
});

document.getElementById("loadAgentSample").addEventListener("click", () => loadSample(samples.agent));
document.getElementById("loadAppSample").addEventListener("click", () => loadSample(samples.app));
document.getElementById("exportReport").addEventListener("click", downloadReport);
document.getElementById("exportReportTop").addEventListener("click", downloadReport);

document.getElementById("stages").innerHTML = stages.map(([name, description], index) => `
  <div class="stage">
    <strong>${index + 1}. ${escapeHtml(name)}</strong>
    ${escapeHtml(description)}
  </div>
`).join("");

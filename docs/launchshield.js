const stages = [
  ["Runtime Guard", "Risky action blocking"],
  ["Evidence Log", "Decision evidence"],
  ["Config Scan", "Risk discovery"],
  ["Launch Report", "Exportable summary"],
  ["Cloud-ready Export", "Report bundle"],
  ["Tool-call Firewall", "MCP/API control"],
  ["Approvals", "Human review points"],
  ["Operator View", "Team summary"],
];

const contactEmail = "sourabhranjansahoo@gmail.com";

const rulebook = [
  {
    id: "destructive-shell",
    severity: "critical",
    weight: 22,
    stage: "Runtime Guard",
    title: "Destructive shell or system command surface",
    pattern: /\b(rm\s+-rf|del\s+\/s|Remove-Item|format\s|shutdown|sudo\s|chmod\s+777|curl\s+.*\|\s*(bash|sh)|powershell\s+-enc)\b/i,
    fix: "Put shell/system tools behind a runtime guard, block destructive commands by default, and require explicit approval for production mutations.",
    block: true,
  },
  {
    id: "secret-exfiltration",
    severity: "critical",
    weight: 24,
    stage: "Runtime Guard",
    title: "Secret or credential exfiltration risk",
    pattern: /\b(api[_-]?key|secret|token|credential|password|\.env|ssh key|private key|send.*env|print.*env|exfiltrat)\b/i,
    fix: "Isolate secrets, redact tool arguments, and block requests that expose environment variables, API keys, or private credentials.",
    block: true,
  },
  {
    id: "mcp-unguarded",
    severity: "high",
    weight: 16,
    stage: "Tool-call Firewall",
    title: "MCP/tool server appears exposed without a firewall",
    pattern: /\b(mcp|tools\/call|stdio server|tool server|filesystem server|browser server)\b/i,
    fix: "Run the MCP server behind a tool-call firewall and log every allow/block decision.",
    block: true,
  },
  {
    id: "database-write",
    severity: "high",
    weight: 14,
    stage: "Approvals",
    title: "Database write or account mutation needs approval",
    pattern: /\b(delete user|delete account|drop table|database write|db write|update customer|refund|charge|payment|invoice|subscription|production deploy|prod deploy)\b/i,
    fix: "Require human approval for account, payment, database, and production mutations.",
    block: false,
  },
  {
    id: "pii-handling",
    severity: "high",
    weight: 12,
    stage: "Evidence Log",
    title: "Sensitive user data or PII is in scope",
    pattern: /\b(email address|phone number|address|ssn|aadhaar|pan card|medical|health|patient|financial|bank|credit card|customer data|crm)\b/i,
    fix: "Log decision evidence without leaking raw PII, minimize tool permissions, and add data-retention limits.",
    block: false,
  },
  {
    id: "browser-automation",
    severity: "medium",
    weight: 9,
    stage: "Runtime Guard",
    title: "Browser automation can cross trust boundaries",
    pattern: /\b(browser|playwright|selenium|scrape|crawl|web automation|login page|cookie|session)\b/i,
    fix: "Constrain browser automation to approved domains and block credential/session extraction.",
    block: false,
  },
  {
    id: "email-slack-send",
    severity: "medium",
    weight: 8,
    stage: "Approvals",
    title: "Outbound message tool can create business risk",
    pattern: /\b(send email|email sender|slack send|post to slack|discord|webhook|sms|whatsapp)\b/i,
    fix: "Require approval or rate limits for outbound customer/team messages.",
    block: false,
  },
  {
    id: "file-system",
    severity: "medium",
    weight: 8,
    stage: "Tool-call Firewall",
    title: "File-system access should be least-privilege",
    pattern: /\b(file system|filesystem|read file|write file|download file|upload file|local files|documents folder)\b/i,
    fix: "Restrict paths, block destructive file writes, and record evidence for file reads/writes.",
    block: false,
  },
  {
    id: "no-auth",
    severity: "high",
    weight: 13,
    stage: "Config Scan",
    title: "Auth or ownership model is unclear",
    pattern: /\b(no auth|public endpoint|open endpoint|without auth|anonymous|any user|shared token)\b/i,
    fix: "Add owner identity, per-agent permissions, and separate user/team scopes before launch.",
    block: false,
  },
  {
    id: "prompt-injection",
    severity: "high",
    weight: 15,
    stage: "Runtime Guard",
    title: "Prompt-injection exposure through untrusted content",
    pattern: /\b(user uploaded|webpage content|external content|email content|pdf|untrusted|ignore previous instructions|prompt injection)\b/i,
    fix: "Treat external content as untrusted, restrict tool use after retrieval, and require evidence logs for high-risk actions.",
    block: true,
  },
];

const controlPenalties = [
  ["humanApproval", "high", 12, "Approvals", "Human approval is missing for sensitive actions", "Add approval-required policies for production, payment, account, and outbound communication actions."],
  ["receipts", "medium", 10, "Evidence Log", "Audit evidence is missing", "Record tamper-evident evidence for every tool-call allow/block/approval decision."],
  ["leastPrivilege", "medium", 8, "Runtime Guard", "Least-privilege boundaries are not declared", "Declare agent identity, owner, scope, allowed tools, and denied tools."],
  ["secretIsolation", "high", 12, "Runtime Guard", "Secret isolation is not declared", "Keep API keys out of prompts/tool outputs and block exfiltration patterns."],
  ["sandbox", "medium", 7, "Tool-call Firewall", "Sandboxing is not declared", "Run risky tools in a constrained environment and limit filesystem/network access."],
  ["rateLimits", "low", 4, "Operator View", "Rate limits are not declared", "Add limits and operator visibility for repeated risky actions."],
];

const toolSignals = [
  ["shell", "Shell/system command", /\b(shell|powershell|cmd\.exe|bash|sh\s+-c|terminal|run command|system command|exec)\b/i, true],
  ["filesystem", "File-system access", /\b(file system|filesystem|read file|write file|download file|upload file|local files|documents folder|--root)\b/i, true],
  ["browser", "Browser/web automation", /\b(browser|playwright|selenium|scrape|crawl|web automation|webpage|website login)\b/i, false],
  ["outbound", "Outbound messaging", /\b(send email|email sender|slack send|post to slack|discord|webhook|sms|whatsapp|notify customer)\b/i, true],
  ["databaseWrite", "Database write", /\b(database write|db write|update customer|drop table|delete row|write to database|admin update)\b/i, true],
  ["payment", "Payment/refund action", /\b(refund|charge|payment|stripe|invoice|subscription|billing)\b/i, true],
  ["sensitiveData", "Sensitive/customer data", /\b(customer data|crm|email address|phone number|address|ssn|aadhaar|pan card|medical|health|patient|financial|bank|credit card|ticket data)\b/i, true],
  ["secrets", "Secrets/credentials", /\b(api[_-]?key|secret|token|credential|password|\.env|private key|ssh key)\b/i, true],
  ["publicEndpoint", "Public or weak auth endpoint", /\b(no auth|public endpoint|open endpoint|without auth|anonymous|any user|shared token|preview route)\b/i, true],
  ["untrustedContent", "Untrusted content input", /\b(user uploaded|webpage content|external content|email content|pdf|untrusted|ignore previous instructions|prompt injection)\b/i, false],
  ["production", "Production environment", /\b(production|prod deploy|production deploy|live users|customer-facing|enterprise customer)\b/i, true],
  ["adminMutation", "Account/admin mutation", /\b(delete user|delete account|disable account|change role|admin action|account removal)\b/i, true],
];

const comboRules = [
  {
    id: "secret-outbound-chain",
    severity: "critical",
    weight: 20,
    stage: "Runtime Guard",
    title: "Secret exfiltration path: credentials plus outbound/browser tools",
    needs: ["secrets"],
    any: ["outbound", "browser", "webhook"],
    fix: "Remove secrets from agent-visible context and block any tool call that sends credentials to email, webhook, browser, or chat tools.",
    block: true,
  },
  {
    id: "prompt-injection-action-chain",
    severity: "critical",
    weight: 18,
    stage: "Runtime Guard",
    title: "Prompt-injection-to-action chain",
    needs: ["untrustedContent"],
    any: ["databaseWrite", "payment", "adminMutation", "outbound"],
    fix: "Do not let content from PDFs, webpages, or emails directly trigger database, payment, account, or outbound-message actions.",
    block: true,
  },
  {
    id: "public-data-write-chain",
    severity: "high",
    weight: 16,
    stage: "Config Scan",
    title: "Public/weak auth surface touches sensitive data or writes",
    needs: ["publicEndpoint"],
    any: ["databaseWrite", "payment", "sensitiveData", "adminMutation"],
    fix: "Add real auth, owner scoping, and per-user/team permissions before exposing this workflow.",
    block: false,
  },
  {
    id: "mcp-shell-filesystem-chain",
    severity: "high",
    weight: 15,
    stage: "Tool-call Firewall",
    title: "MCP can reach shell or broad file-system tools",
    needs: ["mcp"],
    any: ["shell", "filesystem"],
    fix: "Put MCP tools behind a firewall, restrict paths/commands, and sandbox the server before sharing it with agents.",
    block: true,
  },
  {
    id: "customer-data-outbound-chain",
    severity: "high",
    weight: 13,
    stage: "Approvals",
    title: "Customer data can flow into outbound communication",
    needs: ["sensitiveData", "outbound"],
    any: [],
    fix: "Require human approval or strict templates before sending customer data through email, Slack, SMS, or webhooks.",
    block: false,
  },
  {
    id: "production-without-approval-chain",
    severity: "high",
    weight: 12,
    stage: "Approvals",
    title: "Production-impacting workflow without declared approval",
    needs: ["production"],
    missingControl: "humanApproval",
    any: ["databaseWrite", "payment", "adminMutation", "shell"],
    fix: "Declare human approval for production-impacting actions before launch.",
    block: false,
  },
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

function meaningfulInputLength(form) {
  return [form.workflow.value, form.tools.value, form.mcpConfig.value]
    .join("\n")
    .trim()
    .length;
}

function parseMcpConfig(rawConfig) {
  const raw = rawConfig.trim();
  const analysis = {
    parsed: false,
    parseError: false,
    servers: [],
    broadRoots: [],
    shellServers: [],
    secretEnvKeys: [],
  };
  if (!raw) return analysis;
  if (!raw.startsWith("{") && !raw.startsWith("[")) return analysis;

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (_) {
    analysis.parseError = true;
    return analysis;
  }

  analysis.parsed = true;
  const serverMap = parsed.mcpServers || parsed.servers || parsed.MCPServers || {};
  if (!serverMap || typeof serverMap !== "object" || Array.isArray(serverMap)) return analysis;

  for (const [name, server] of Object.entries(serverMap)) {
    const command = String(server.command || server.cmd || "");
    const args = Array.isArray(server.args) ? server.args.map(String) : [];
    const env = server.env && typeof server.env === "object" ? server.env : {};
    const envKeys = Object.keys(env);
    const joinedArgs = args.join(" ");
    const serverRecord = { name, command, args, envKeys };
    analysis.servers.push(serverRecord);

    if (/(powershell|cmd\.exe|bash|\/bin\/sh|\/bin\/bash|shell)/i.test(`${name} ${command} ${joinedArgs}`)) {
      analysis.shellServers.push(serverRecord);
    }
    if (/(^|\s|=)(\/|~|[A-Za-z]:\\?|[A-Za-z]:\/?|C:\\Users|C:\/Users|\/Users|\/home)(\s|$|\\|\/)/i.test(joinedArgs)) {
      analysis.broadRoots.push(serverRecord);
    }
    for (const key of envKeys) {
      if (/(api|token|secret|password|credential|key)/i.test(key)) {
        analysis.secretEnvKeys.push({ server: name, key });
      }
    }
  }

  return analysis;
}

function configFindings(mcpAnalysis, surfaces, rawConfig) {
  const findings = [];
  if (surfaces.includes("MCP") && !rawConfig.trim()) {
    findings.push({
      id: "mcp-config-missing",
      severity: "medium",
      weight: 8,
      stage: "Config Scan",
      title: "MCP selected but no config was provided",
      fix: "Paste the MCP config so LaunchShield can inspect server commands, args, roots, and environment variables.",
      block: false,
    });
  }
  if (mcpAnalysis.parseError) {
    findings.push({
      id: "mcp-config-invalid-json",
      severity: "medium",
      weight: 8,
      stage: "Config Scan",
      title: "MCP/config JSON could not be parsed",
      fix: "Fix the JSON format or paste the exact config file to enable deeper server analysis.",
      block: false,
    });
  }
  if (mcpAnalysis.shellServers.length) {
    findings.push({
      id: "mcp-shell-server",
      severity: "critical",
      weight: 20,
      stage: "Tool-call Firewall",
      title: "MCP config exposes shell/system command execution",
      fix: `Review server(s): ${mcpAnalysis.shellServers.map((server) => server.name).join(", ")}. Put them behind a strict firewall or remove them from agent access.`,
      block: true,
    });
  }
  if (mcpAnalysis.broadRoots.length) {
    findings.push({
      id: "mcp-broad-filesystem-root",
      severity: "high",
      weight: 14,
      stage: "Tool-call Firewall",
      title: "MCP file-system root looks too broad",
      fix: `Narrow root/path access for server(s): ${mcpAnalysis.broadRoots.map((server) => server.name).join(", ")}.`,
      block: false,
    });
  }
  if (mcpAnalysis.secretEnvKeys.length) {
    findings.push({
      id: "mcp-secret-env",
      severity: "high",
      weight: 14,
      stage: "Runtime Guard",
      title: "MCP server environment contains secret-looking keys",
      fix: "Do not expose API keys, tokens, or credentials to agent-readable config or tool outputs.",
      block: false,
    });
  }
  return findings;
}

function detectSignals(text, surfaces, mcpAnalysis) {
  const signalSet = new Set();
  for (const [id, , pattern] of toolSignals) {
    if (pattern.test(text)) signalSet.add(id);
  }
  if (surfaces.includes("MCP") || mcpAnalysis.servers.length) signalSet.add("mcp");
  if (mcpAnalysis.shellServers.length) signalSet.add("shell");
  if (mcpAnalysis.broadRoots.length) signalSet.add("filesystem");
  if (mcpAnalysis.secretEnvKeys.length) signalSet.add("secrets");
  if (/webhook/i.test(text)) signalSet.add("webhook");
  return signalSet;
}

function comboFindings(signals, controls) {
  return comboRules
    .filter((rule) => {
      const hasNeeds = rule.needs.every((need) => signals.has(need));
      const hasAny = !rule.any.length || rule.any.some((signal) => signals.has(signal));
      const missingControl = !rule.missingControl || !controls.includes(rule.missingControl);
      return hasNeeds && hasAny && missingControl;
    })
    .map((rule) => ({ ...rule, combo: true }));
}

function detectedSurfaceLabels(signals, mcpAnalysis) {
  const labels = toolSignals
    .filter(([id]) => signals.has(id))
    .map(([id, label, , hot]) => ({ id, label, hot }));
  if (mcpAnalysis.servers.length) {
    labels.push({
      id: "mcpServers",
      label: `${mcpAnalysis.servers.length} MCP server${mcpAnalysis.servers.length === 1 ? "" : "s"} parsed`,
      hot: mcpAnalysis.shellServers.length > 0 || mcpAnalysis.broadRoots.length > 0,
    });
  }
  return labels;
}

function confidenceLabel(form, mcpAnalysis, surfaces, controls) {
  let points = 0;
  if (form.workflow.value.trim().length > 80) points += 30;
  if (form.tools.value.trim().length > 40) points += 25;
  if (form.mcpConfig.value.trim().length > 20) points += 15;
  if (mcpAnalysis.parsed) points += 15;
  if (surfaces.length) points += 8;
  if (controls.length) points += 7;
  if (points >= 75) return "High";
  if (points >= 45) return "Medium";
  return "Low";
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
    schema: "aion.launchshield.evidence.v1",
    evidence_id: `ls_${Date.now().toString(36)}_${index}`,
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
  const inputLength = meaningfulInputLength(form);
  const mcpAnalysis = parseMcpConfig(form.mcpConfig.value);
  const signals = detectSignals(text, surfaces, mcpAnalysis);
  const confidence = confidenceLabel(form, mcpAnalysis, surfaces, controls);

  if (inputLength < 40) {
    const finding = {
      id: "need-real-input",
      severity: "medium",
      weight: 0,
      stage: "Launch Report",
      title: "Paste a real workflow or load a sample first",
      fix: "Add the agent prompt, tools/APIs, MCP config, auth model, and launch notes. The scanner needs that context before it can produce a useful score.",
      block: false,
    };
    return {
      projectName: form.projectName.value.trim() || "Untitled AI workflow",
      launchStage: form.launchStage.value,
      surfaces,
      controls,
      score: "--",
      grade: "input",
      findings: [finding],
      receipts: [],
      blockers: [],
      riskChainCount: 0,
      detectedSurfaces: detectedSurfaceLabels(signals, mcpAnalysis),
      confidence,
      mcpAnalysis,
      generatedAt: new Date().toISOString(),
    };
  }

  findings.push(...configFindings(mcpAnalysis, surfaces, form.mcpConfig.value));

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
      stage: "Tool-call Firewall",
      title: "MCP surface declared",
      fix: "Keep MCP calls behind a tool-call firewall and export evidence for customer review.",
      block: false,
    });
  }

  findings.push(...comboFindings(signals, controls));

  if (inputLength < 160) {
    findings.push({
      id: "thin-input",
      severity: "medium",
      weight: 10,
      stage: "Launch Report",
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
  const blockers = uniqueFindings.filter((finding) => finding.block || finding.severity === "critical");
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
    blockers,
    riskChainCount: uniqueFindings.filter((finding) => finding.combo).length,
    detectedSurfaces: detectedSurfaceLabels(signals, mcpAnalysis),
    confidence,
    mcpAnalysis,
    generatedAt: new Date().toISOString(),
  };
}

function stageActive(report, stageName) {
  if (["Evidence Log", "Launch Report", "Cloud-ready Export", "Operator View"].includes(stageName)) return true;
  return report.findings.some((finding) => finding.stage === stageName)
    || (stageName === "Approvals" && !report.controls.includes("humanApproval"))
    || (stageName === "Tool-call Firewall" && report.surfaces.includes("MCP"));
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
  grade.textContent = report.grade === "input" ? "Needs Real Input" : report.grade === "ready" ? "Launch Ready With Controls" : report.grade === "caution" ? "Needs Hardening" : "High Risk";

  const criticals = report.findings.filter((finding) => finding.severity === "critical").length;
  const highs = report.findings.filter((finding) => finding.severity === "high").length;
  document.getElementById("summary").textContent = report.grade === "input"
    ? "Load a sample or paste a real agent/app workflow to generate a useful audit."
    : `${report.projectName}: ${criticals} critical, ${highs} high, ${report.findings.length} total findings.`;
  document.getElementById("findingCount").textContent = report.findings.length;
  document.getElementById("comboCount").textContent = report.riskChainCount;
  document.getElementById("receiptCount").textContent = report.receipts.length;
  document.getElementById("confidence").textContent = report.confidence;

  document.getElementById("detectedSurfaces").innerHTML = report.detectedSurfaces.length
    ? report.detectedSurfaces.map((surface) => `<span class="chip ${surface.hot ? "hot" : ""}">${escapeHtml(surface.label)}</span>`).join("")
    : `<span class="chip">No clear tool surface detected</span>`;

  document.getElementById("launchBlockers").innerHTML = report.blockers.length
    ? report.blockers.map((finding) => `
      <div class="finding blocker">
        <strong><span class="sev ${finding.severity}">${finding.severity}</span>${escapeHtml(finding.title)}</strong>
        <div class="muted">${escapeHtml(finding.fix)}</div>
      </div>
    `).join("")
    : `<div class="finding muted">No launch blockers detected from this input.</div>`;

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

  document.getElementById("receipts").textContent = report.receipts.length
    ? report.receipts.map((receipt) => JSON.stringify(receipt)).join("\n")
    : "No evidence yet. Add a real workflow or load a sample, then run the scan.";
  document.getElementById("exportReport").disabled = report.grade === "input";
  document.getElementById("exportReportTop").disabled = report.grade === "input";
  document.getElementById("copyBrief").disabled = report.grade === "input";

  const body = encodeURIComponent(`Project: ${report.projectName}\nScore: ${report.score}\nFindings: ${report.findings.length}\n\nFeedback:\n- What felt useful?\n- What felt confusing?\n- What should LaunchShield scan next?`);
  document.getElementById("auditRequest").href = `https://github.com/Sourabh1845/aion-core/issues/new?title=AION%20LaunchShield%20feedback:%20${encodeURIComponent(report.projectName)}&body=${body}`;
  updateReviewRequestLink();
}

async function copyAuditBrief() {
  if (!latestReport || latestReport.grade === "input") return;
  const brief = `AION LaunchShield audit request

Project: ${latestReport.projectName}
Score: ${latestReport.score}/100
Status: ${latestReport.grade}
Findings: ${latestReport.findings.length}

Top findings:
${latestReport.findings.slice(0, 5).map((finding, index) => `${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}`).join("\n")}

Launch blockers:
${latestReport.blockers.length ? latestReport.blockers.map((finding, index) => `${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}`).join("\n") : "None detected"}

I want feedback or a manual review for this AI workflow.`;
  await navigator.clipboard.writeText(brief);
  const button = document.getElementById("copyBrief");
  const oldText = button.textContent;
  button.textContent = "Copied";
  setTimeout(() => {
    button.textContent = oldText;
  }, 1400);
}

function reviewRequestText() {
  const name = document.getElementById("leadName").value.trim();
  const email = document.getElementById("leadEmail").value.trim();
  const reviewPackage = document.getElementById("reviewPackage").value;
  const timeline = document.getElementById("timeline").value;
  const notes = document.getElementById("reviewNotes").value.trim();
  const report = latestReport;
  const reportLines = report && report.grade !== "input"
    ? [
        `Project: ${report.projectName}`,
        `Score: ${report.score}/100`,
        `Status: ${report.grade}`,
        `Scanner confidence: ${report.confidence}`,
        `Risk chains: ${report.riskChainCount}`,
        `Findings: ${report.findings.length}`,
        "",
        "Launch blockers:",
        report.blockers.length
          ? report.blockers.map((finding, index) => `${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}`).join("\n")
          : "None detected",
        "",
        "Top findings:",
        report.findings.slice(0, 5).map((finding, index) => `${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}`).join("\n"),
      ]
    : [
        "No completed scan attached yet.",
        "Please run LaunchShield before review if possible.",
      ];

  return [
    "AION LaunchShield launch fix request",
    "",
    `Name: ${name || "(not provided)"}`,
    `Email: ${email || "(not provided)"}`,
    `Review type: ${reviewPackage}`,
    `Timeline: ${timeline}`,
    "Payment: after scope confirmation; no automatic checkout was used.",
    "",
    "Context:",
    notes || "(not provided)",
    "",
    "Scan summary:",
    ...reportLines,
  ].join("\n");
}

function updateReviewRequestLink() {
  const subject = latestReport && latestReport.grade !== "input"
    ? `AION LaunchShield fix plan: ${latestReport.projectName}`
    : "AION LaunchShield fix plan request";
  const body = reviewRequestText();
  document.getElementById("emailReviewRequest").href =
    `mailto:${contactEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

async function copyReviewRequest() {
  await navigator.clipboard.writeText(reviewRequestText());
  const button = document.getElementById("copyReviewRequest");
  const oldText = button.textContent;
  button.textContent = "Copied";
  setTimeout(() => {
    button.textContent = oldText;
  }, 1400);
}

function reportMarkdown(report) {
  return `# AION LaunchShield Report

Project: ${report.projectName}
Generated: ${report.generatedAt}
Launch stage: ${report.launchStage}
Score: ${report.score}/100
Status: ${report.grade}
Scanner confidence: ${report.confidence}
Risk chains: ${report.riskChainCount}

## Detected Surfaces

${report.detectedSurfaces.length ? report.detectedSurfaces.map((surface) => `- ${surface.label}`).join("\n") : "- No clear tool surface detected"}

## Launch Blockers

${report.blockers.length ? report.blockers.map((finding, index) => `${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}
   - Check: ${finding.stage}
   - Fix: ${finding.fix}`).join("\n\n") : "No launch blockers detected from this input."}

## Findings

${report.findings.map((finding, index) => `${index + 1}. [${finding.severity.toUpperCase()}] ${finding.title}
   - Check: ${finding.stage}
   - Fix: ${finding.fix}`).join("\n\n")}

## Security Checks Covered

${stages.map(([name, description], index) => `${index + 1}. ${name}: ${description}`).join("\n")}

## Evidence Log

\`\`\`jsonl
${report.receipts.map((receipt) => JSON.stringify(receipt)).join("\n")}
\`\`\`

## Next Step

Recommended next step: fix any blockers first. If you want help, request a manual launch fix plan and attach this report.
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
document.getElementById("copyBrief").addEventListener("click", copyAuditBrief);
document.getElementById("copyReviewRequest").addEventListener("click", copyReviewRequest);
["leadName", "leadEmail", "reviewPackage", "timeline", "reviewNotes"].forEach((id) => {
  document.getElementById(id).addEventListener("input", updateReviewRequestLink);
  document.getElementById(id).addEventListener("change", updateReviewRequestLink);
});

document.getElementById("stages").innerHTML = stages.map(([name, description], index) => `
  <div class="stage">
    <strong>${index + 1}. ${escapeHtml(name)}</strong>
    ${escapeHtml(description)}
  </div>
`).join("");
updateReviewRequestLink();

const STORAGE_KEY = "aion-vibeops-state-v1";

const sampleCommands = {
  job: "Kal 3 baje Ravi ko Rohit ke ghar AC repair bhejna, total 1500, 500 advance mila.",
  expense: "Aaj petrol 300 aur parts 1200 expense add karo.",
  payment: "Sita madam se 1000 UPI payment mila, AC service ka balance close karo.",
  summary: "Aaj ka summary bhejo aur kal ke pending jobs dikhao.",
};

const initialState = {
  business: {
    name: "AION AC Services",
    city: "Bhubaneswar",
    currency: "INR",
    phone: "+91 90000 00000",
  },
  workers: [
    { id: "w_ravi", name: "Ravi", phone: "+91 90000 00001", role: "Technician", active: true },
    { id: "w_amit", name: "Amit", phone: "+91 90000 00002", role: "Helper", active: true },
  ],
  customers: [
    { id: "c_sita", name: "Sita Madam", phone: "+91 90000 00011", address: "Patia", notes: "Prefers UPI." },
    { id: "c_rohit", name: "Rohit", phone: "+91 90000 00012", address: "Jaydev Vihar", notes: "AC service lead." },
  ],
  jobs: [],
  ledger: [],
  events: [],
};

let state = loadState();
let pendingPlan = null;
let activeJobFilter = "all";
let deferredInstallPrompt = null;
let currentReceiptJobId = null;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function uid(prefix) {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 7)}`;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch (error) {
    console.warn("Failed to load state", error);
  }
  const seeded = clone(initialState);
  seedDemoData(seeded);
  return seeded;
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function seedDemoData(target = state) {
  const now = new Date();
  const todayIso = toDateInput(now);
  const tomorrowIso = toDateInput(addDays(now, 1));
  target.jobs = [
    {
      id: "j_demo_1",
      customerId: "c_sita",
      workerId: "w_ravi",
      title: "AC gas refill",
      service: "AC repair",
      date: todayIso,
      time: "15:30",
      status: "assigned",
      amount: 2200,
      advance: 700,
      paid: 700,
      pending: 1500,
      notes: "Check cooling and gas pressure.",
      createdAt: now.toISOString(),
    },
    {
      id: "j_demo_2",
      customerId: "c_rohit",
      workerId: "w_amit",
      title: "Washing machine inspection",
      service: "Appliance repair",
      date: tomorrowIso,
      time: "11:00",
      status: "assigned",
      amount: 800,
      advance: 0,
      paid: 0,
      pending: 800,
      notes: "Noise issue.",
      createdAt: now.toISOString(),
    },
  ];
  target.ledger = [
    {
      id: "l_demo_1",
      type: "income",
      amount: 700,
      mode: "UPI",
      jobId: "j_demo_1",
      customerId: "c_sita",
      note: "Advance for AC gas refill",
      createdAt: now.toISOString(),
    },
    {
      id: "l_demo_2",
      type: "expense",
      amount: 320,
      mode: "Cash",
      note: "Petrol",
      createdAt: now.toISOString(),
    },
  ];
  target.events = [
    { id: uid("e"), text: "Demo business loaded with 2 jobs and 2 workers.", createdAt: now.toISOString() },
  ];
}

function resetDemo() {
  state = clone(initialState);
  seedDemoData(state);
  saveState();
  renderAll();
  toast("Demo business loaded");
}

function addDays(date, amount) {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + amount);
  return copy;
}

function toDateInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDate(value) {
  if (!value) return "Not scheduled";
  const date = new Date(`${value}T00:00:00`);
  return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function formatMoney(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: state.business.currency || "INR",
    maximumFractionDigits: 0,
  }).format(Number(amount || 0));
}

function findWorkerByName(name) {
  const normalized = cleanName(name);
  return state.workers.find((worker) => cleanName(worker.name) === normalized);
}

function findCustomerByName(name) {
  const normalized = cleanName(name);
  return state.customers.find((customer) => cleanName(customer.name) === normalized);
}

function cleanName(value) {
  return String(value || "")
    .replace(/\b(madam|sir|ji|bhai|didi|uncle|aunty)\b/gi, "")
    .replace(/[^a-zA-Z0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function titleCase(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim()
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function parseCommand(input) {
  const text = String(input || "").trim();
  if (!text) {
    return {
      type: "empty",
      confidence: "Low",
      summary: "No command entered",
      fields: {},
      actions: ["Type or speak a business command first."],
    };
  }

  const lower = text.toLowerCase();
  if (/\b(summary|report|hisab|aaj ka|daily)\b/.test(lower)) return parseSummary(text);
  if (/\b(expense|kharcha|kharach|petrol|diesel|parts|rent|salary|chai|transport)\b/.test(lower)) return parseExpense(text);
  if (/\b(payment|paid|received|mila|mil gaya|collected|balance close|cash|upi)\b/.test(lower) && !/\bjob|bhejna|assign|repair|service|install|cleaning\b/.test(lower)) {
    return parsePayment(text);
  }
  return parseJob(text);
}

function parseSummary(text) {
  return {
    type: "summary",
    confidence: "High",
    summary: "Generate daily owner summary",
    fields: { request: text },
    actions: ["Show today's revenue, expenses, pending dues, active jobs, and tomorrow's jobs."],
  };
}

function parseExpense(text) {
  const amounts = extractAmounts(text);
  const total = amounts.reduce((sum, item) => sum + item.value, 0);
  const category = detectExpenseCategory(text);
  return {
    type: "expense",
    confidence: amounts.length ? "High" : "Needs review",
    summary: `Record ${category} expense`,
    fields: {
      category,
      amount: total || 0,
      mode: /\bupi\b/i.test(text) ? "UPI" : "Cash",
      note: text,
    },
    actions: [
      `Add expense: ${formatMoney(total || 0)}`,
      `Category: ${category}`,
      "Include this in today's business summary.",
    ],
  };
}

function parsePayment(text) {
  const amount = pickAmount(text, ["payment", "paid", "received", "mila", "cash", "upi", "collected"]) || extractAmounts(text)[0]?.value || 0;
  const customerName = extractCustomerName(text) || "Unknown Customer";
  const customer = findCustomerByName(customerName);
  return {
    type: "payment",
    confidence: amount ? "High" : "Needs review",
    summary: "Record customer payment",
    fields: {
      customerName: customer?.name || titleCase(customerName),
      amount,
      mode: /\bupi\b/i.test(text) ? "UPI" : /\bcard\b/i.test(text) ? "Card" : "Cash",
      note: text,
    },
    actions: [
      `Record payment: ${formatMoney(amount)}`,
      `Customer: ${customer?.name || titleCase(customerName)}`,
      "Apply payment to the oldest pending job if one exists.",
    ],
  };
}

function parseJob(text) {
  const amounts = extractAmounts(text);
  const total = pickAmount(text, ["total", "estimate", "bill", "amount", "charge"]) || Math.max(0, ...amounts.map((item) => item.value));
  const advance = pickAmount(text, ["advance", "adv", "mila", "paid", "deposit"]) || 0;
  const workerName = extractWorkerName(text) || "Unassigned";
  const customerName = extractCustomerName(text) || "New Customer";
  const service = detectService(text);
  const schedule = extractSchedule(text);
  const customer = findCustomerByName(customerName);
  const worker = findWorkerByName(workerName);
  const pending = Math.max(0, (total || 0) - (advance || 0));
  return {
    type: "job",
    confidence: customerName !== "New Customer" && service !== "Service job" ? "High" : "Needs review",
    summary: `Create ${service} job`,
    fields: {
      customerName: customer?.name || titleCase(customerName),
      workerName: worker?.name || titleCase(workerName),
      service,
      date: schedule.date,
      time: schedule.time,
      amount: total || 0,
      advance,
      pending,
      notes: text,
    },
    actions: [
      `Create job: ${service}`,
      `Assign worker: ${worker?.name || titleCase(workerName)}`,
      `Customer: ${customer?.name || titleCase(customerName)}`,
      `Schedule: ${formatDate(schedule.date)} at ${schedule.time}`,
      `Record advance: ${formatMoney(advance)}`,
      `Pending balance: ${formatMoney(pending)}`,
      "Prepare WhatsApp task and customer confirmation.",
    ],
  };
}

function extractAmounts(text) {
  const matches = Array.from(String(text).matchAll(/(?:rs\.?|inr|₹)?\s*(\d{2,7})(?:\s*(?:rs|rupees|rupaye))?/gi));
  return matches.map((match) => ({ value: Number(match[1]), index: match.index || 0 }));
}

function pickAmount(text, keywords) {
  const amounts = extractAmounts(text);
  if (!amounts.length) return 0;
  const lower = text.toLowerCase();
  let best = null;
  for (const amount of amounts) {
    const start = Math.max(0, amount.index - 26);
    const end = Math.min(lower.length, amount.index + 34);
    const window = lower.slice(start, end);
    if (keywords.some((keyword) => window.includes(keyword))) {
      best = amount.value;
    }
  }
  return best || 0;
}

function extractWorkerName(text) {
  const known = state.workers.find((worker) => new RegExp(`\\b${escapeRegExp(worker.name)}\\b`, "i").test(text));
  if (known) return known.name;
  const match = text.match(/\b([A-Z][a-z]{2,})\s+ko\b/);
  return match?.[1] || "";
}

function extractCustomerName(text) {
  const known = state.customers.find((customer) => new RegExp(`\\b${escapeRegExp(customer.name.split(" ")[0])}\\b`, "i").test(text));
  if (known) return known.name;
  const gharMatch = text.match(/\b([A-Z][a-z]{2,}(?:\s+(?:madam|sir|ji))?)\s+(?:ke|ka|ki)\s+ghar\b/i);
  if (gharMatch) return gharMatch[1];
  const seMatch = text.match(/\b([A-Z][a-z]{2,}(?:\s+(?:madam|sir|ji))?)\s+se\b/i);
  if (seMatch) return seMatch[1];
  const customerMatch = text.match(/\b(?:customer|client)\s+([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b/);
  return customerMatch?.[1] || "";
}

function detectService(text) {
  const lower = text.toLowerCase();
  const services = [
    ["AC repair", /\bac\b|air conditioner|cooling|gas refill/i],
    ["Plumbing", /plumb|pipe|tap|leak|bathroom/i],
    ["Electrical", /electric|wiring|switch|fan|light|mcb/i],
    ["Cleaning", /clean|deep clean|sofa|home cleaning/i],
    ["Appliance repair", /fridge|washing machine|microwave|geyser|appliance/i],
    ["Installation", /install|installation|fit kar/i],
  ];
  return services.find(([, pattern]) => pattern.test(lower))?.[0] || "Service job";
}

function detectExpenseCategory(text) {
  const lower = text.toLowerCase();
  if (/petrol|diesel|fuel/.test(lower)) return "Fuel";
  if (/parts|spare|material/.test(lower)) return "Parts";
  if (/salary|worker/.test(lower)) return "Salary";
  if (/rent/.test(lower)) return "Rent";
  if (/chai|food|lunch/.test(lower)) return "Food";
  return "General";
}

function extractSchedule(text) {
  const lower = text.toLowerCase();
  let date = toDateInput(new Date());
  if (/\b(kal|tomorrow)\b/.test(lower)) date = toDateInput(addDays(new Date(), 1));
  if (/\bparso|day after tomorrow\b/.test(lower)) date = toDateInput(addDays(new Date(), 2));

  const timeMatch = lower.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje)?\b/);
  let hour = 10;
  let minute = "00";
  if (timeMatch) {
    hour = Number(timeMatch[1]);
    minute = timeMatch[2] || "00";
    const meridiem = timeMatch[3];
    if (meridiem === "pm" && hour < 12) hour += 12;
    if ((meridiem === "baje" || !meridiem) && hour >= 1 && hour <= 7) hour += 12;
  }
  return { date, time: `${String(hour).padStart(2, "0")}:${minute}` };
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function renderAll() {
  renderBusinessSetup();
  renderDashboard();
  renderJobs();
  renderCustomers();
  renderWorkers();
  renderLedger();
  renderSummary();
  renderOutreach();
}

function renderBusinessSetup() {
  $("#businessName").value = state.business.name || "";
  $("#businessPhone").value = state.business.phone || "";
  $("#businessCity").value = state.business.city || "";
}

function renderDashboard() {
  const today = toDateInput(new Date());
  const todayIncome = state.ledger.filter((entry) => entry.type === "income" && entry.createdAt.slice(0, 10) === today)
    .reduce((sum, entry) => sum + Number(entry.amount || 0), 0);
  const pending = state.jobs.reduce((sum, job) => sum + Number(job.pending || 0), 0);
  const active = state.jobs.filter((job) => !["completed", "cancelled"].includes(job.status)).length;
  const completed = state.jobs.filter((job) => job.status === "completed" && job.completedAt?.slice(0, 10) === today).length;

  $("#todayRevenue").textContent = formatMoney(todayIncome);
  $("#todayRevenueHint").textContent = todayIncome ? "Collected today." : "No collection yet today.";
  $("#pendingPayments").textContent = formatMoney(pending);
  $("#pendingHint").textContent = pending ? "Follow up required." : "All clear.";
  $("#activeJobs").textContent = String(active);
  $("#activeHint").textContent = active ? "Field work running." : "No active work.";
  $("#completedToday").textContent = String(completed);
  $("#completedHint").textContent = completed ? "Jobs closed today." : "No job completed yet.";

  $("#opsFeed").innerHTML = state.events.slice().reverse().slice(0, 8).map((event) => `
    <div class="feed-item">
      <strong>${escapeHtml(event.text)}</strong>
      <p>${new Date(event.createdAt).toLocaleString("en-IN")}</p>
    </div>
  `).join("") || `<div class="feed-item"><strong>No activity yet.</strong><p>Run a command to create the first business event.</p></div>`;

  const upcoming = state.jobs
    .filter((job) => job.status !== "completed")
    .sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`))
    .slice(0, 3);
  $("#nextJobs").innerHTML = upcoming.map(jobCardHtml).join("") || emptyCard("No upcoming jobs", "Create one from the AI command box.");
}

function renderJobs() {
  const jobs = state.jobs
    .filter((job) => {
      if (activeJobFilter === "all") return true;
      if (activeJobFilter === "pending-payment") return Number(job.pending || 0) > 0;
      return job.status === activeJobFilter;
    })
    .sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));

  $("#jobsList").innerHTML = jobs.map((job) => {
    const customer = getCustomer(job.customerId);
    const worker = getWorker(job.workerId);
    return `
      <article class="record">
        <div>
          <h3>${escapeHtml(job.title || job.service)}</h3>
          <p>${escapeHtml(customer?.name || "Unknown customer")} - ${escapeHtml(worker?.name || "Unassigned")} - ${formatDate(job.date)} ${job.time}</p>
          <div class="meta-row">
            <span class="tag ${jobStatusColor(job.status)}">${escapeHtml(job.status)}</span>
            <span class="tag">Amount ${formatMoney(job.amount)}</span>
            <span class="tag ${job.pending > 0 ? "yellow" : "green"}">Pending ${formatMoney(job.pending)}</span>
          </div>
        </div>
        <div class="record-actions">
          <button data-action="progress" data-id="${job.id}" type="button">Start</button>
          <button data-action="complete" data-id="${job.id}" type="button">Complete</button>
          <button data-action="collect" data-id="${job.id}" type="button">Collect</button>
          <button data-action="receipt" data-id="${job.id}" type="button">Receipt</button>
          <button data-action="share-job" data-id="${job.id}" type="button">Share</button>
        </div>
      </article>
    `;
  }).join("") || emptyRecord("No jobs found", "Create jobs from the AI command tab.");
}

function renderCustomers() {
  $("#customersList").innerHTML = state.customers.map((customer) => {
    const jobs = state.jobs.filter((job) => job.customerId === customer.id);
    const pending = jobs.reduce((sum, job) => sum + Number(job.pending || 0), 0);
    return `
      <article class="record">
        <div>
          <h3>${escapeHtml(customer.name)}</h3>
          <p>${escapeHtml(customer.phone || "No phone")} - ${escapeHtml(customer.address || "No address")}</p>
          <div class="meta-row">
            <span class="tag">${jobs.length} jobs</span>
            <span class="tag ${pending ? "yellow" : "green"}">Pending ${formatMoney(pending)}</span>
          </div>
        </div>
        <div class="record-actions">
          <button data-action="share-customer" data-id="${customer.id}" type="button">Message</button>
        </div>
      </article>
    `;
  }).join("") || emptyRecord("No customers yet", "Customers are created automatically from commands.");
}

function renderWorkers() {
  $("#workersList").innerHTML = state.workers.map((worker) => {
    const assigned = state.jobs.filter((job) => job.workerId === worker.id && job.status !== "completed");
    const completed = state.jobs.filter((job) => job.workerId === worker.id && job.status === "completed").length;
    return `
      <article class="record">
        <div>
          <h3>${escapeHtml(worker.name)}</h3>
          <p>${escapeHtml(worker.role)} - ${escapeHtml(worker.phone || "No phone")}</p>
          <div class="meta-row">
            <span class="tag yellow">${assigned.length} active</span>
            <span class="tag green">${completed} completed</span>
          </div>
        </div>
        <div class="record-actions">
          <button data-action="share-worker" data-id="${worker.id}" type="button">Send Tasks</button>
        </div>
      </article>
    `;
  }).join("");
}

function renderLedger() {
  $("#ledgerList").innerHTML = state.ledger.slice().reverse().map((entry) => {
    const customer = getCustomer(entry.customerId);
    const tag = entry.type === "income" ? "green" : "red";
    return `
      <article class="record">
        <div>
          <h3>${entry.type === "income" ? "Income" : "Expense"} - ${formatMoney(entry.amount)}</h3>
          <p>${escapeHtml(entry.note || "")}</p>
          <div class="meta-row">
            <span class="tag ${tag}">${escapeHtml(entry.mode || "Cash")}</span>
            ${customer ? `<span class="tag">${escapeHtml(customer.name)}</span>` : ""}
            <span class="tag">${new Date(entry.createdAt).toLocaleString("en-IN")}</span>
          </div>
        </div>
      </article>
    `;
  }).join("") || emptyRecord("No ledger entries yet", "Payments and expenses will appear here.");
}

function renderSummary() {
  const summary = buildDailySummary();
  $("#dailySummary").textContent = summary;
}

function renderOutreach() {
  $("#outreachCopy").value = `Hey, I built AION VibeOps for small service businesses.

It turns one voice/text command like:
"Kal 3 baje Ravi ko Rohit ke ghar AC repair bhejna, total 1500, 500 advance mila."

Into:
- job card
- worker assignment
- payment and pending balance
- customer message
- receipt
- daily business summary

It is not a WhatsApp bot. It is a business operations app, with WhatsApp sharing as one channel.

I am opening the global beta this week.
Want the demo link?`;
}

function betaRequestText() {
  const name = $("#betaName").value.trim();
  const email = $("#betaEmail").value.trim();
  const business = $("#betaBusiness").value.trim();
  const country = $("#betaCountry").value.trim();
  const notes = $("#betaNotes").value.trim();
  return `AION VibeOps global beta request

Name: ${name || "(not provided)"}
Email: ${email || "(not provided)"}
Business / agency: ${business || "(not provided)"}
Country: ${country || "(not provided)"}

What I want AION to run:
${notes || "(not provided)"}

Source: VibeOps public demo`;
}

function updateBetaRequestLink() {
  const subject = `AION VibeOps beta request${$("#betaBusiness").value.trim() ? ` - ${$("#betaBusiness").value.trim()}` : ""}`;
  $("#emailBetaRequest").href = `mailto:sourabhranjansahoo@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(betaRequestText())}`;
}

function jobCardHtml(job) {
  const customer = getCustomer(job.customerId);
  const worker = getWorker(job.workerId);
  return `
    <article class="job-card">
      <h3>${escapeHtml(job.title || job.service)}</h3>
      <p>${escapeHtml(customer?.name || "Unknown customer")} - ${escapeHtml(worker?.name || "Unassigned")}</p>
      <div class="meta-row">
        <span class="tag">${formatDate(job.date)} ${job.time}</span>
        <span class="tag ${job.pending ? "yellow" : "green"}">${formatMoney(job.pending)} due</span>
      </div>
    </article>
  `;
}

function emptyCard(title, detail) {
  return `<article class="job-card"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(detail)}</p></article>`;
}

function emptyRecord(title, detail) {
  return `<article class="record"><div><h3>${escapeHtml(title)}</h3><p>${escapeHtml(detail)}</p></div></article>`;
}

function jobStatusColor(status) {
  if (status === "completed") return "green";
  if (status === "cancelled") return "red";
  return "yellow";
}

function getCustomer(id) {
  return state.customers.find((customer) => customer.id === id);
}

function getWorker(id) {
  return state.workers.find((worker) => worker.id === id);
}

function showPlan(plan) {
  pendingPlan = plan;
  $("#approvalPanel").classList.remove("hidden");
  $("#confidenceBadge").textContent = plan.confidence;
  $("#parsedPreview").innerHTML = Object.entries(plan.fields).map(([key, value]) => `
    <div class="preview-item">
      <span>${escapeHtml(labelize(key))}</span>
      <strong>${escapeHtml(formatFieldValue(key, value))}</strong>
    </div>
  `).join("");
  $("#actionPreview").innerHTML = plan.actions.map((action) => `
    <div class="action-item">${escapeHtml(action)}</div>
  `).join("");
  switchTab("command");
  $("#approvalPanel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function labelize(value) {
  return value.replace(/([A-Z])/g, " $1").replace(/^./, (char) => char.toUpperCase());
}

function formatFieldValue(key, value) {
  if (["amount", "advance", "pending"].includes(key)) return formatMoney(value);
  if (key === "date") return formatDate(value);
  return value || "-";
}

function approvePlan() {
  if (!pendingPlan) return;
  if (pendingPlan.type === "job") createJobFromPlan(pendingPlan);
  if (pendingPlan.type === "expense") createExpenseFromPlan(pendingPlan);
  if (pendingPlan.type === "payment") createPaymentFromPlan(pendingPlan);
  if (pendingPlan.type === "summary") switchTab("summary");
  pendingPlan = null;
  $("#approvalPanel").classList.add("hidden");
  saveState();
  renderAll();
}

function createJobFromPlan(plan) {
  const customer = ensureCustomer(plan.fields.customerName);
  const worker = ensureWorker(plan.fields.workerName);
  const job = {
    id: uid("j"),
    customerId: customer.id,
    workerId: worker.id,
    title: `${plan.fields.service} - ${customer.name}`,
    service: plan.fields.service,
    date: plan.fields.date,
    time: plan.fields.time,
    status: "assigned",
    amount: Number(plan.fields.amount || 0),
    advance: Number(plan.fields.advance || 0),
    paid: Number(plan.fields.advance || 0),
    pending: Number(plan.fields.pending || 0),
    notes: plan.fields.notes,
    createdAt: new Date().toISOString(),
  };
  state.jobs.push(job);
  if (job.advance > 0) {
    state.ledger.push({
      id: uid("l"),
      type: "income",
      amount: job.advance,
      mode: "Cash",
      jobId: job.id,
      customerId: customer.id,
      note: `Advance for ${job.service}`,
      createdAt: new Date().toISOString(),
    });
  }
  addEvent(`Created ${job.service} job for ${customer.name}, assigned to ${worker.name}.`);
  currentReceiptJobId = job.id;
  showReceipt(job.id);
}

function createExpenseFromPlan(plan) {
  state.ledger.push({
    id: uid("l"),
    type: "expense",
    amount: Number(plan.fields.amount || 0),
    mode: plan.fields.mode || "Cash",
    note: `${plan.fields.category}: ${plan.fields.note}`,
    createdAt: new Date().toISOString(),
  });
  addEvent(`Recorded expense ${formatMoney(plan.fields.amount)} for ${plan.fields.category}.`);
}

function createPaymentFromPlan(plan) {
  const customer = ensureCustomer(plan.fields.customerName);
  let remaining = Number(plan.fields.amount || 0);
  const pendingJobs = state.jobs
    .filter((job) => job.customerId === customer.id && job.pending > 0)
    .sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));
  for (const job of pendingJobs) {
    if (remaining <= 0) break;
    const applied = Math.min(job.pending, remaining);
    job.paid += applied;
    job.pending -= applied;
    remaining -= applied;
  }
  state.ledger.push({
    id: uid("l"),
    type: "income",
    amount: Number(plan.fields.amount || 0),
    mode: plan.fields.mode || "Cash",
    customerId: customer.id,
    note: plan.fields.note || "Customer payment",
    createdAt: new Date().toISOString(),
  });
  addEvent(`Recorded ${formatMoney(plan.fields.amount)} payment from ${customer.name}.`);
}

function ensureCustomer(name) {
  const safeName = titleCase(name || "New Customer");
  let customer = findCustomerByName(safeName);
  if (!customer) {
    customer = { id: uid("c"), name: safeName, phone: "", address: "", notes: "Created from AI command." };
    state.customers.push(customer);
  }
  return customer;
}

function ensureWorker(name) {
  const safeName = titleCase(name || "Unassigned");
  let worker = findWorkerByName(safeName);
  if (!worker) {
    worker = { id: uid("w"), name: safeName, phone: "", role: "Worker", active: true };
    state.workers.push(worker);
  }
  return worker;
}

function addEvent(text) {
  state.events.push({ id: uid("e"), text, createdAt: new Date().toISOString() });
}

function handleJobAction(action, id) {
  const job = state.jobs.find((item) => item.id === id);
  if (!job) return;
  if (action === "progress") {
    job.status = "in-progress";
    addEvent(`${job.service} job started for ${getCustomer(job.customerId)?.name || "customer"}.`);
  }
  if (action === "complete") {
    job.status = "completed";
    job.completedAt = new Date().toISOString();
    addEvent(`${job.service} job completed for ${getCustomer(job.customerId)?.name || "customer"}.`);
  }
  if (action === "collect") collectJobBalance(job);
  if (action === "receipt") showReceipt(job.id);
  if (action === "share-job") shareText(buildJobShareText(job));
  saveState();
  renderAll();
}

function collectJobBalance(job) {
  const due = Number(job.pending || 0);
  if (!due) {
    toast("No pending balance");
    return;
  }
  job.paid += due;
  job.pending = 0;
  state.ledger.push({
    id: uid("l"),
    type: "income",
    amount: due,
    mode: "Cash",
    jobId: job.id,
    customerId: job.customerId,
    note: `Balance collected for ${job.service}`,
    createdAt: new Date().toISOString(),
  });
  addEvent(`Collected ${formatMoney(due)} balance for ${getCustomer(job.customerId)?.name || "customer"}.`);
}

function buildJobShareText(job) {
  const customer = getCustomer(job.customerId);
  const worker = getWorker(job.workerId);
  return `AION VibeOps task

Job: ${job.service}
Customer: ${customer?.name || "Customer"}
Worker: ${worker?.name || "Worker"}
Time: ${formatDate(job.date)} ${job.time}
Amount: ${formatMoney(job.amount)}
Pending: ${formatMoney(job.pending)}
Notes: ${job.notes || "-"}`;
}

function showReceipt(jobId) {
  const job = state.jobs.find((item) => item.id === jobId);
  if (!job) return;
  currentReceiptJobId = job.id;
  const customer = getCustomer(job.customerId);
  const worker = getWorker(job.workerId);
  $("#receiptTitle").textContent = `${job.service} Receipt`;
  $("#receiptContent").innerHTML = `
    <h3>${escapeHtml(state.business.name)}</h3>
    <p>${escapeHtml(state.business.city)} - ${escapeHtml(state.business.phone)}</p>
    <hr>
    <p><strong>Receipt ID:</strong> ${escapeHtml(job.id)}</p>
    <p><strong>Customer:</strong> ${escapeHtml(customer?.name || "Customer")}</p>
    <p><strong>Worker:</strong> ${escapeHtml(worker?.name || "Worker")}</p>
    <p><strong>Service:</strong> ${escapeHtml(job.service)}</p>
    <p><strong>Date:</strong> ${formatDate(job.date)} ${escapeHtml(job.time)}</p>
    <p><strong>Total:</strong> ${formatMoney(job.amount)}</p>
    <p><strong>Paid:</strong> ${formatMoney(job.paid)}</p>
    <p><strong>Pending:</strong> ${formatMoney(job.pending)}</p>
    <hr>
    <p>Generated by AION VibeOps. This is a simple operational receipt for beta usage.</p>
  `;
  $("#receiptDrawer").classList.remove("hidden");
}

function receiptText() {
  const job = state.jobs.find((item) => item.id === currentReceiptJobId);
  if (!job) return "";
  const customer = getCustomer(job.customerId);
  return `${state.business.name}
Receipt: ${job.id}
Customer: ${customer?.name || "Customer"}
Service: ${job.service}
Date: ${formatDate(job.date)} ${job.time}
Total: ${formatMoney(job.amount)}
Paid: ${formatMoney(job.paid)}
Pending: ${formatMoney(job.pending)}

Generated by AION VibeOps.`;
}

function buildDailySummary() {
  const today = toDateInput(new Date());
  const tomorrow = toDateInput(addDays(new Date(), 1));
  const income = state.ledger.filter((entry) => entry.type === "income" && entry.createdAt.slice(0, 10) === today)
    .reduce((sum, entry) => sum + Number(entry.amount || 0), 0);
  const expense = state.ledger.filter((entry) => entry.type === "expense" && entry.createdAt.slice(0, 10) === today)
    .reduce((sum, entry) => sum + Number(entry.amount || 0), 0);
  const completed = state.jobs.filter((job) => job.status === "completed" && job.completedAt?.slice(0, 10) === today);
  const active = state.jobs.filter((job) => !["completed", "cancelled"].includes(job.status));
  const pending = state.jobs.reduce((sum, job) => sum + Number(job.pending || 0), 0);
  const tomorrowJobs = state.jobs.filter((job) => job.date === tomorrow);
  const topDues = state.jobs.filter((job) => job.pending > 0).slice(0, 5);

  return `AION VibeOps Daily Summary
Business: ${state.business.name}
Date: ${formatDate(today)}

Money
- Revenue collected today: ${formatMoney(income)}
- Expenses today: ${formatMoney(expense)}
- Net today: ${formatMoney(income - expense)}
- Pending customer payments: ${formatMoney(pending)}

Jobs
- Active jobs: ${active.length}
- Completed today: ${completed.length}
- Tomorrow jobs: ${tomorrowJobs.length}

Top pending dues
${topDues.length ? topDues.map((job, index) => `${index + 1}. ${getCustomer(job.customerId)?.name || "Customer"} - ${job.service} - ${formatMoney(job.pending)}`).join("\n") : "- No pending dues"}

Tomorrow schedule
${tomorrowJobs.length ? tomorrowJobs.map((job, index) => `${index + 1}. ${job.time} - ${job.service} - ${getCustomer(job.customerId)?.name || "Customer"} - ${getWorker(job.workerId)?.name || "Worker"}`).join("\n") : "- No jobs scheduled for tomorrow"}`;
}

function downloadCsv() {
  const rows = [
    ["type", "amount", "mode", "customer", "note", "created_at"],
    ...state.ledger.map((entry) => [
      entry.type,
      entry.amount,
      entry.mode || "",
      getCustomer(entry.customerId)?.name || "",
      entry.note || "",
      entry.createdAt,
    ]),
  ];
  downloadText("aion-vibeops-ledger.csv", rows.map((row) => row.map(csvCell).join(",")).join("\n"));
}

function csvCell(value) {
  return `"${String(value ?? "").replace(/"/g, '""')}"`;
}

function exportData() {
  downloadText("aion-vibeops-export.json", JSON.stringify(state, null, 2));
}

function downloadText(filename, content) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function copyText(text, message = "Copied") {
  navigator.clipboard.writeText(text).then(() => toast(message)).catch(() => {
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
    toast(message);
  });
}

function shareText(text) {
  const encoded = encodeURIComponent(text);
  window.open(`https://wa.me/?text=${encoded}`, "_blank", "noopener");
}

function toast(message) {
  const existing = $(".toast");
  if (existing) existing.remove();
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = message;
  Object.assign(node.style, {
    position: "fixed",
    right: "16px",
    bottom: "16px",
    background: "var(--green)",
    color: "var(--ink)",
    padding: "12px 14px",
    borderRadius: "8px",
    fontWeight: "850",
    zIndex: "50",
  });
  document.body.appendChild(node);
  setTimeout(() => node.remove(), 1500);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function switchTab(id) {
  $$(".nav-tab").forEach((button) => button.classList.toggle("active", button.dataset.tab === id));
  $$(".tab-view").forEach((view) => view.classList.toggle("active", view.id === id));
}

function startVoice(targetSelector) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    toast("Voice input not supported in this browser");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "hi-IN";
  recognition.interimResults = false;
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    $(targetSelector).value = transcript;
    toast("Voice captured");
  };
  recognition.start();
}

function bindEvents() {
  $$(".nav-tab").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });
  $$(".nav-jump").forEach((button) => button.addEventListener("click", () => switchTab(button.dataset.jump)));

  $("#quickSample").addEventListener("click", () => { $("#quickCommand").value = sampleCommands.job; });
  $("#quickParse").addEventListener("click", () => showPlan(parseCommand($("#quickCommand").value)));
  $("#parseCommand").addEventListener("click", () => showPlan(parseCommand($("#commandInput").value)));
  $("#clearCommand").addEventListener("click", () => { $("#commandInput").value = ""; });
  $("#micDashboard").addEventListener("click", () => startVoice("#quickCommand"));
  $("#micCommand").addEventListener("click", () => startVoice("#commandInput"));
  $("#approveActions").addEventListener("click", approvePlan);
  $("#discardParsed").addEventListener("click", () => { pendingPlan = null; $("#approvalPanel").classList.add("hidden"); });
  $("#editParsed").addEventListener("click", () => { $("#commandInput").focus(); });
  $("#seedDemo").addEventListener("click", resetDemo);
  $("#exportData").addEventListener("click", exportData);
  $("#saveBusiness").addEventListener("click", saveBusinessSetup);
  $("#addWorker").addEventListener("click", addWorkerFromSetup);
  $("#addCustomer").addEventListener("click", addCustomerFromSetup);
  $("#downloadLedger").addEventListener("click", downloadCsv);
  $("#copySummary").addEventListener("click", () => copyText(buildDailySummary(), "Summary copied"));
  $("#shareSummary").addEventListener("click", () => shareText(buildDailySummary()));
  $("#copyOutreach").addEventListener("click", () => copyText($("#outreachCopy").value, "Outreach copied"));
  $("#shareOutreach").addEventListener("click", () => shareText($("#outreachCopy").value));
  $("#newJobFromSample").addEventListener("click", () => showPlan(parseCommand(sampleCommands.job)));
  $("#copyBetaRequest").addEventListener("click", () => copyText(betaRequestText(), "Beta request copied"));
  ["betaName", "betaEmail", "betaBusiness", "betaCountry", "betaNotes"].forEach((id) => {
    $(`#${id}`).addEventListener("input", updateBetaRequestLink);
  });

  $$(".sample-command").forEach((button) => {
    button.addEventListener("click", () => {
      $("#commandInput").value = button.textContent.trim();
      showPlan(parseCommand(button.textContent.trim()));
    });
  });

  $$(".filter").forEach((button) => {
    button.addEventListener("click", () => {
      activeJobFilter = button.dataset.jobFilter;
      $$(".filter").forEach((item) => item.classList.toggle("active", item === button));
      renderJobs();
    });
  });

  document.body.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const { action, id } = button.dataset;
    if (["progress", "complete", "collect", "receipt", "share-job"].includes(action)) handleJobAction(action, id);
    if (action === "share-customer") {
      const customer = getCustomer(id);
      if (customer) shareText(`Hi ${customer.name}, this is ${state.business.name}. Your service update is ready.`);
    }
    if (action === "share-worker") {
      const worker = getWorker(id);
      const tasks = state.jobs.filter((job) => job.workerId === id && job.status !== "completed");
      shareText(`AION VibeOps tasks for ${worker?.name || "worker"}\n\n${tasks.map((job, index) => `${index + 1}. ${job.service} - ${getCustomer(job.customerId)?.name || "Customer"} - ${formatDate(job.date)} ${job.time}`).join("\n") || "No active tasks."}`);
    }
  });

  $("#closeReceipt").addEventListener("click", () => $("#receiptDrawer").classList.add("hidden"));
  $("#printReceipt").addEventListener("click", () => window.print());
  $("#copyReceipt").addEventListener("click", () => copyText(receiptText(), "Receipt copied"));
  $("#shareReceipt").addEventListener("click", () => shareText(receiptText()));

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    $("#installApp").classList.remove("hidden");
  });

  $("#installApp").addEventListener("click", async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    $("#installApp").classList.add("hidden");
  });
}

function saveBusinessSetup() {
  state.business.name = $("#businessName").value.trim() || state.business.name;
  state.business.phone = $("#businessPhone").value.trim() || state.business.phone;
  state.business.city = $("#businessCity").value.trim() || state.business.city;
  addEvent(`Updated business setup for ${state.business.name}.`);
  saveState();
  renderAll();
  toast("Business saved");
}

function addWorkerFromSetup() {
  const name = $("#newWorkerName").value.trim();
  if (!name) {
    toast("Worker name required");
    return;
  }
  const existing = findWorkerByName(name);
  if (existing) {
    toast("Worker already exists");
    return;
  }
  state.workers.push({
    id: uid("w"),
    name: titleCase(name),
    phone: $("#newWorkerPhone").value.trim(),
    role: "Worker",
    active: true,
  });
  $("#newWorkerName").value = "";
  $("#newWorkerPhone").value = "";
  addEvent(`Added worker ${titleCase(name)}.`);
  saveState();
  renderAll();
  toast("Worker added");
}

function addCustomerFromSetup() {
  const name = $("#newCustomerName").value.trim();
  if (!name) {
    toast("Customer name required");
    return;
  }
  const existing = findCustomerByName(name);
  if (existing) {
    toast("Customer already exists");
    return;
  }
  state.customers.push({
    id: uid("c"),
    name: titleCase(name),
    phone: $("#newCustomerPhone").value.trim(),
    address: $("#newCustomerAddress").value.trim(),
    notes: "Added from setup.",
  });
  $("#newCustomerName").value = "";
  $("#newCustomerPhone").value = "";
  $("#newCustomerAddress").value = "";
  addEvent(`Added customer ${titleCase(name)}.`);
  saveState();
  renderAll();
  toast("Customer added");
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("./sw.js").catch(() => {});
}

bindEvents();
renderAll();
updateBetaRequestLink();
saveState();

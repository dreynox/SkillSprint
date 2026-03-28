const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";

// ── DOM refs ─────────────────────────────────────────────────────────────────
const listSection        = document.getElementById("contest-list-section");
const listStatusEl       = document.getElementById("list-status");
const contestCards       = document.getElementById("contest-cards");
const refreshBtn         = document.getElementById("refresh-btn");

const detailSection      = document.getElementById("contest-detail-section");
const contestDetailEl    = document.getElementById("contest-detail");
const problemStatusEl    = document.getElementById("problem-status");
const problemCards       = document.getElementById("problem-cards");
const backToListBtn      = document.getElementById("back-to-list-btn");

const problemSection     = document.getElementById("problem-detail-section");
const problemDetailEl    = document.getElementById("problem-detail");
const backToContestBtn   = document.getElementById("back-to-contest-btn");
const languageSelect     = document.getElementById("language");
const codeTextarea       = document.getElementById("code");
const submitBtn          = document.getElementById("submit-btn");
const submitStatusEl     = document.getElementById("submit-status");
const verdictBox         = document.getElementById("verdict-box");

// Active selection state
let activeContestId  = null;
let activeProblemId  = null;

function getToken() {
  return localStorage.getItem("access_token");
}

function getAuthHeaders(withJson = false) {
  const token = getToken();
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (withJson) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
}

// ── Navigation helpers ────────────────────────────────────────────────────────
function showSection(section) {
  [listSection, detailSection, problemSection].forEach(s => s.style.display = "none");
  section.style.display = "block";
}

function setListStatus(msg, isError = false) {
  listStatusEl.textContent = msg;
  listStatusEl.style.color = isError ? "#b00020" : "#555";
}

function setProblemStatus(msg, isError = false) {
  problemStatusEl.textContent = msg;
  problemStatusEl.style.color = isError ? "#b00020" : "#555";
}

function setSubmitStatus(msg, isError = false) {
  submitStatusEl.textContent = msg;
  submitStatusEl.style.color = isError ? "#b00020" : "#555";
}

// ── Contest list ──────────────────────────────────────────────────────────────
async function loadContests() {
  const token = getToken();
  if (!token) {
    window.location.href = "../../index.html";
    return;
  }

  setListStatus("Loading contests...");
  contestCards.innerHTML = "";

  try {
    const res  = await fetch(`${API_BASE}/contests`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to load contests");

    if (data.length === 0) {
      setListStatus("No contests available.", true);
      return;
    }

    setListStatus(`${data.length} contest(s) found. Click a card to view problems.`);
    data.forEach(renderContestCard);
  } catch (err) {
    setListStatus(err.message, true);
  }
}

function renderContestCard(contest) {
  const card = document.createElement("div");
  card.className = "card" + (contest.is_active ? " active" : " inactive");

  const badge = contest.is_active
    ? `<span class="badge badge-active">ACTIVE</span>`
    : `<span class="badge badge-inactive">INACTIVE</span>`;

  const start = contest.start_time
    ? new Date(contest.start_time).toLocaleString()
    : "TBD";
  const end = contest.end_time
    ? new Date(contest.end_time).toLocaleString()
    : "TBD";

  card.innerHTML = `
    <div class="card-title">${badge} ${escapeHtml(contest.name)}</div>
    <div class="card-desc">${escapeHtml(contest.description || "")}</div>
    <div class="card-meta">${start} &rarr; ${end}</div>
  `;

  card.addEventListener("click", () => openContest(contest.id));
  contestCards.appendChild(card);
}

// ── Contest detail ────────────────────────────────────────────────────────────
async function openContest(contestId) {
  activeContestId = contestId;
  contestDetailEl.innerHTML = "";
  problemCards.innerHTML    = "";
  setProblemStatus("Loading problems...");
  showSection(detailSection);

  try {
    const res  = await fetch(`${API_BASE}/contests/${contestId}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to load contest");

    contestDetailEl.innerHTML = `
      <h2>${escapeHtml(data.name)}</h2>
      <p class="card-desc">${escapeHtml(data.description || "")}</p>
    `;

    if (!data.problems || data.problems.length === 0) {
      setProblemStatus("No problems in this contest yet.", true);
      return;
    }

    setProblemStatus(`${data.problems.length} problem(s). Click a card to submit.`);
    data.problems.forEach(renderProblemCard);

    // Record that the current student joined this contest.
    await fetch(`${API_BASE}/contests/${contestId}/join`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
  } catch (err) {
    setProblemStatus(err.message, true);
  }
}

function renderProblemCard(problem) {
  const card = document.createElement("div");
  card.className = "card";

  const diffClass = {
    easy:   "diff-easy",
    medium: "diff-medium",
    hard:   "diff-hard",
  }[problem.difficulty?.toLowerCase()] || "";

  card.innerHTML = `
    <div class="card-title">${escapeHtml(problem.title)}
      ${problem.difficulty
        ? `<span class="badge ${diffClass}">${problem.difficulty.toUpperCase()}</span>`
        : ""}
    </div>
    <div class="card-desc">${escapeHtml(problem.statement || "")}</div>
    ${problem.tags ? `<div class="card-meta">Tags: ${escapeHtml(problem.tags)}</div>` : ""}
  `;

  card.addEventListener("click", () => openProblem(problem));
  problemCards.appendChild(card);
}

// ── Problem detail + submit ───────────────────────────────────────────────────
function openProblem(problem) {
  activeProblemId = problem.id;
  verdictBox.style.display = "none";
  verdictBox.innerHTML     = "";
  codeTextarea.value       = "";
  setSubmitStatus("");
  showSection(problemSection);

  const diffClass = {
    easy:   "diff-easy",
    medium: "diff-medium",
    hard:   "diff-hard",
  }[problem.difficulty?.toLowerCase()] || "";

  problemDetailEl.innerHTML = `
    <h2>${escapeHtml(problem.title)}
      ${problem.difficulty
        ? `<span class="badge ${diffClass}">${problem.difficulty.toUpperCase()}</span>`
        : ""}
    </h2>
    <p class="problem-statement">${escapeHtml(problem.statement || "")}</p>
    ${problem.tags ? `<p class="card-meta">Tags: ${escapeHtml(problem.tags)}</p>` : ""}
  `;
}

async function submitSolution() {
  const language = languageSelect.value;
  const code     = codeTextarea.value.trim();

  if (!code) {
    setSubmitStatus("Code cannot be empty.", true);
    return;
  }

  setSubmitStatus("Submitting...");
  submitBtn.disabled = true;
  verdictBox.style.display = "none";

  try {
    const res  = await fetch(
      `${API_BASE}/contests/${activeContestId}/problems/${activeProblemId}/submit`,
      {
        method:  "POST",
        headers: getAuthHeaders(true),
        body:    JSON.stringify({ language, code }),
      }
    );
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Submission failed");

    setSubmitStatus("Submitted successfully");
    verdictBox.style.display = "block";
    verdictBox.innerHTML = `
      <div class="verdict verdict-${data.verdict.toLowerCase()}">
        Verdict: <strong>${escapeHtml(data.verdict)}</strong>
        &nbsp;|&nbsp; Score: <strong>${data.score}</strong>
        &nbsp;|&nbsp; Submission ID: <strong>${data.id}</strong>
      </div>
    `;
  } catch (err) {
    setSubmitStatus(err.message, true);
  } finally {
    submitBtn.disabled = false;
  }
}

// ── Utility ───────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Event listeners ───────────────────────────────────────────────────────────
refreshBtn.addEventListener("click", loadContests);
backToListBtn.addEventListener("click", () => { activeContestId = null; showSection(listSection); });
backToContestBtn.addEventListener("click", () => { activeProblemId = null; openContest(activeContestId); });
submitBtn.addEventListener("click", submitSolution);

// Auto-load on page open
loadContests();

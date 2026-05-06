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

const LIVE_REFRESH_MS = 30000;
const COUNTDOWN_TICK_MS = 1000;

// Active selection state
let activeContestId  = null;
let activeProblemId  = null;
let listAutoRefreshTimer = null;
let countdownTicker = null;

function getToken() {
  const raw =
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    sessionStorage.getItem("access_token") ||
    sessionStorage.getItem("token") ||
    "";
  let cleaned = String(raw).trim().replace(/^"|"$/g, "");
  cleaned = cleaned.replace(/^Bearer\s+/i, "").trim();
  return cleaned && cleaned !== "undefined" && cleaned !== "null" ? cleaned : "";
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
  if (window.SkillSprintUX && typeof window.SkillSprintUX.showStatus === "function") {
    window.SkillSprintUX.showStatus(msg, isError ? "error" : "info");
  }
}

function setProblemStatus(msg, isError = false) {
  problemStatusEl.textContent = msg;
  problemStatusEl.style.color = isError ? "#b00020" : "#555";
  if (window.SkillSprintUX && typeof window.SkillSprintUX.showStatus === "function") {
    window.SkillSprintUX.showStatus(msg, isError ? "error" : "info");
  }
}

function setSubmitStatus(msg, isError = false) {
  submitStatusEl.textContent = msg;
  submitStatusEl.style.color = isError ? "#b00020" : "#555";
  if (window.SkillSprintUX && typeof window.SkillSprintUX.showStatus === "function") {
    window.SkillSprintUX.showStatus(msg, isError ? "error" : "info");
  }
}

// ── Contest list ──────────────────────────────────────────────────────────────
async function loadContests(options = {}) {
  const { silent = false } = options;
  const token = getToken();
  if (!token) {
    window.location.href = "../../index.html";
    return;
  }

  if (!silent) {
    setListStatus("Loading contests...");
    contestCards.innerHTML = "";
    refreshBtn.disabled = true;
  }
  listSection.setAttribute("aria-busy", "true");

  try {
    const res  = await fetch(`${API_BASE}/contests?active_only=true`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to load contests");

    if (data.length === 0) {
      setListStatus("No contests available.", true);
      return;
    }

    setListStatus(
      `${data.length} contest(s) found. Live contest windows auto-refresh every 30 seconds.`
    );
    contestCards.innerHTML = "";
    data.forEach(renderContestCard);
    refreshContestCountdowns();
  } catch (err) {
    setListStatus(err.message, true);
  } finally {
    refreshBtn.disabled = false;
    listSection.removeAttribute("aria-busy");
  }
}

function renderContestCard(contest) {
  const card = document.createElement("div");
  card.className = "card" + (contest.is_active ? " active" : " inactive");

  const state = contestLiveState(contest.start_time, contest.end_time, contest.is_active);

  const badge = contest.is_active
    ? `<span class="badge badge-active">ACTIVE</span>`
    : `<span class="badge badge-inactive">INACTIVE</span>`;

  const start = contest.start_time
    ? new Date(contest.start_time).toLocaleString()
    : "TBD";
  const end = contest.end_time
    ? new Date(contest.end_time).toLocaleString()
    : "TBD";
  const duration = renderDuration(contest.start_time, contest.end_time);

  card.innerHTML = `
    <div class="card-title">${badge} ${escapeHtml(contest.name)}</div>
    <div class="card-desc">${escapeHtml(contest.description || "")}</div>
    <div class="card-meta">${start} &rarr; ${end} | ${duration}</div>
    <div
      class="card-live ${escapeHtml(state.className)}"
      data-live-start="${escapeHtml(contest.start_time || "")}" 
      data-live-end="${escapeHtml(contest.end_time || "")}" 
      data-live-active="${contest.is_active ? "1" : "0"}"
    >${escapeHtml(state.message)}</div>
  `;

  card.addEventListener("click", () => openContest(contest.id));
  contestCards.appendChild(card);
}

function formatRemaining(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${hours}h ${String(minutes).padStart(2, "0")}m ${String(seconds).padStart(2, "0")}s`;
}

function contestLiveState(startRaw, endRaw, isActiveFlag) {
  const now = Date.now();
  const start = startRaw ? new Date(startRaw).getTime() : null;
  const end = endRaw ? new Date(endRaw).getTime() : null;

  if (start && now < start) {
    return {
      className: "live-upcoming",
      message: `Starts in ${formatRemaining(start - now)}`,
    };
  }

  if (end && now < end) {
    return {
      className: "live-running",
      message: `Live now • Ends in ${formatRemaining(end - now)}`,
    };
  }

  if (end && now >= end) {
    return {
      className: "live-ended",
      message: "Contest window ended",
    };
  }

  return {
    className: isActiveFlag ? "live-running" : "live-upcoming",
    message: isActiveFlag ? "Live now" : "Contest schedule to be announced",
  };
}

function refreshContestCountdowns() {
  const nodes = document.querySelectorAll(".card-live");
  nodes.forEach((node) => {
    const start = node.getAttribute("data-live-start");
    const end = node.getAttribute("data-live-end");
    const active = node.getAttribute("data-live-active") === "1";
    const state = contestLiveState(start, end, active);
    node.classList.remove("live-upcoming", "live-running", "live-ended");
    node.classList.add(state.className);
    node.textContent = state.message;
  });
}

function startContestLiveFeed() {
  if (!listAutoRefreshTimer) {
    listAutoRefreshTimer = window.setInterval(() => {
      if (listSection.style.display !== "none") {
        loadContests({ silent: true });
      }
    }, LIVE_REFRESH_MS);
  }

  if (!countdownTicker) {
    countdownTicker = window.setInterval(refreshContestCountdowns, COUNTDOWN_TICK_MS);
  }
}

function renderDuration(start, end) {
  if (!start || !end) {
    return "Duration TBD";
  }

  const startDate = new Date(start);
  const endDate = new Date(end);
  const diffMs = Math.max(0, endDate - startDate);
  const totalMinutes = Math.max(1, Math.round(diffMs / 60000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (!hours) {
    return `${minutes}m`;
  }

  return `${hours}h${minutes ? ` ${minutes}m` : ""}`;
}

// ── Contest detail ────────────────────────────────────────────────────────────
async function openContest(contestId) {
  activeContestId = contestId;
  contestDetailEl.innerHTML = "";
  problemCards.innerHTML    = "";
  setProblemStatus("Loading problems...");
  showSection(detailSection);
  detailSection.setAttribute("aria-busy", "true");

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
  } finally {
    detailSection.removeAttribute("aria-busy");
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

  // Add button to go to code editor
  const editorBtn = document.createElement("button");
  editorBtn.type = "button";
  editorBtn.style.marginTop = "16px";
  editorBtn.textContent = "📝 Open in Code Editor";
  editorBtn.onclick = () => {
    const cacheBust = "20260414";
    window.location.href = `coding.html?v=${cacheBust}&contest_id=${activeContestId}&problem_id=${problem.id}`;
  };
  problemDetailEl.appendChild(editorBtn);
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
  problemSection.setAttribute("aria-busy", "true");

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
    problemSection.removeAttribute("aria-busy");
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
refreshBtn.addEventListener("click", () => loadContests());
backToListBtn.addEventListener("click", () => {
  activeContestId = null;
  showSection(listSection);
  loadContests({ silent: true });
});
backToContestBtn.addEventListener("click", () => { activeProblemId = null; openContest(activeContestId); });
submitBtn.addEventListener("click", submitSolution);

// Auto-load on page open
startContestLiveFeed();
loadContests();

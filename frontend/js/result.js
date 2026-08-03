const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";

function getToken() {
  const raw = localStorage.getItem("access_token") || localStorage.getItem("token") || "";
  const cleaned = String(raw).trim().replace(/^"|"$/g, "");

  if (!cleaned || cleaned === "undefined" || cleaned === "null") {
    return "";
  }

  return cleaned;
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function getCachedUser() {
  try {
    return JSON.parse(localStorage.getItem("user") || "null");
  } catch (_error) {
    return null;
  }
}

function getStoredQuizResult() {
  try {
    return JSON.parse(sessionStorage.getItem("quiz_result") || "null");
  } catch (_error) {
    return null;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Minimal, dependency-free renderer for the small subset of Markdown used in
// explanation text: inline `code`, **bold**, and *italic*. Input is escaped
// first so this can never inject raw HTML from a JSON/quiz-bank source.
function renderInlineMarkdown(raw) {
  let text = escapeHtml(raw);
  text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
  text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/(^|[^*])\*([^*]+)\*(?!\*)/g, "$1<em>$2</em>");
  return text;
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

function renderStat(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
}

function addProfileRow(label, value) {
  const table = document.getElementById("profileTable");
  if (!table) {
    return;
  }

  const row = document.createElement("tr");
  row.innerHTML = `
    <td>${label}</td>
    <td>${value || "-"}</td>
  `;
  table.appendChild(row);
}

function renderProfile(profile) {
  const table = document.getElementById("profileTable");
  if (!table) {
    return;
  }

  table.innerHTML = "";

  addProfileRow("Name", profile.name);
  addProfileRow("Email", profile.email);
  addProfileRow("SRN", profile.srn);
  addProfileRow("PRN", profile.prn);
  addProfileRow("Year", profile.year);
  addProfileRow("Class / Division", profile.division || profile.branch);
  addProfileRow("Branch", profile.branch);
  addProfileRow("Roll No.", profile.roll_no);
  addProfileRow("Role", profile.role);
}

function renderNotes(result) {
  const noteList = document.getElementById("noteList");
  if (!noteList) {
    return;
  }

  noteList.innerHTML = "";

  const notes = [];
  if (!result) {
    notes.push("No quiz submission was found in this session.");
  }
  if (result?.mode === "random") {
    notes.push("This score was generated from a random question bank session.");
  } else if (result?.mode === "test") {
    notes.push("This score was generated from a legacy test submission.");
  }

  if (typeof result?.unanswered === "number") {
    notes.push(`Unanswered questions: ${result.unanswered}.`);
  }

  notes.push("The profile details shown here are loaded from your account.");

  notes.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    noteList.appendChild(item);
  });
}

function buildReviewOption(label, text, { isCorrectAnswer, isWrongSelected }) {
  const option = document.createElement("div");
  option.className = "review-option";
  if (isCorrectAnswer) option.classList.add("option-correct");
  if (isWrongSelected) option.classList.add("option-wrong-selected");

  const labelEl = document.createElement("span");
  labelEl.className = "review-option-label";
  labelEl.textContent = `${label}.`;
  option.appendChild(labelEl);

  const textEl = document.createElement("span");
  textEl.textContent = text || "";
  option.appendChild(textEl);

  if (isCorrectAnswer || isWrongSelected) {
    const tag = document.createElement("span");
    tag.className = "review-option-tag";
    tag.textContent = isCorrectAnswer ? "Correct answer" : "Your answer";
    option.appendChild(tag);
  }

  return option;
}

function buildReviewItem(item, index) {
  const wrapper = document.createElement("article");
  const answered = Boolean(item.selected_answer);
  wrapper.className = `review-item ${item.is_correct ? "is-correct" : "is-incorrect"}`;

  const head = document.createElement("div");
  head.className = "review-item-head";

  const question = document.createElement("p");
  question.className = "review-question";
  question.textContent = `${index + 1}. ${item.question || ""}`;
  head.appendChild(question);

  const badge = document.createElement("span");
  badge.className = `review-status-badge ${item.is_correct ? "correct" : answered ? "incorrect" : "unanswered"}`;
  badge.textContent = item.is_correct ? "Correct" : answered ? "Incorrect" : "Unanswered";
  head.appendChild(badge);

  wrapper.appendChild(head);

  const optionsWrap = document.createElement("div");
  optionsWrap.className = "review-options";
  const options = item.options || {};

  ["A", "B", "C", "D"].forEach((label) => {
    if (!(label in options)) return;
    const isCorrectAnswer = label === item.correct_answer;
    const isWrongSelected = !item.is_correct && label === item.selected_answer;
    optionsWrap.appendChild(
      buildReviewOption(label, options[label], { isCorrectAnswer, isWrongSelected })
    );
  });
  wrapper.appendChild(optionsWrap);

  if (item.explanation) {
    const box = document.createElement("div");
    box.className = "explanation-box";
    box.innerHTML = `<span class="explanation-box-label">Explanation</span>${renderInlineMarkdown(item.explanation)}`;
    wrapper.appendChild(box);
  }

  return wrapper;
}

function renderReview(result) {
  const reviewList = document.getElementById("reviewList");
  if (!reviewList) {
    return;
  }

  reviewList.innerHTML = "";
  const review = Array.isArray(result?.review) ? result.review : [];

  if (!review.length) {
    const empty = document.createElement("p");
    empty.className = "review-empty";
    empty.textContent = "No itemized review is available for this submission.";
    reviewList.appendChild(empty);
    return;
  }

  review.forEach((item, index) => {
    reviewList.appendChild(buildReviewItem(item, index));
  });
}

function setupReviewToggle(result) {
  const reviewBtn = document.getElementById("reviewAnswersBtn");
  const closeBtn = document.getElementById("closeReviewBtn");
  const reviewPanel = document.getElementById("reviewPanel");
  if (!reviewBtn || !reviewPanel) {
    return;
  }

  const hasReview = Array.isArray(result?.review) && result.review.length > 0;
  reviewBtn.disabled = !hasReview;
  if (!hasReview) {
    reviewBtn.title = "No itemized review is available for this submission.";
  }

  reviewBtn.addEventListener("click", () => {
    renderReview(result);
    reviewPanel.hidden = false;
    reviewPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      reviewPanel.hidden = true;
    });
  }
}

async function loadResultPage() {
  const result = getStoredQuizResult();

  renderStat("scoreValue", result ? `${result.score} / ${result.total}` : "-");
  renderStat("totalValue", result ? String(result.total) : "-");
  renderStat("unansweredValue", result && typeof result.unanswered === "number" ? String(result.unanswered) : "-");
  renderStat("modeValue", result ? (result.mode === "random" ? "Random Bank" : "Test Mode") : "-");
  renderStat("quizTypeValue", result ? (result.mode === "random" ? "Random Question Bank" : `Test ${result.test_id || "-"}`) : "-");
  renderStat("languageValue", result?.language || "-");
  renderStat("levelValue", result?.level || "-");
  renderStat("submittedAtValue", formatDateTime(result?.submitted_at));

  renderNotes(result);
  setupReviewToggle(result);

  const token = getToken();
  const cachedUser = getCachedUser();

  if (!token && cachedUser) {
    renderProfile(cachedUser);
    return;
  }

  if (!token) {
    renderProfile({});
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/users/me`, {
      headers: authHeaders(),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to load profile");
    }

    renderProfile(data);
    localStorage.setItem("user", JSON.stringify(data));
  } catch (_error) {
    renderProfile(cachedUser || {});
  }
}

loadResultPage();

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

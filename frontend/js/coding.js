// =========================
// CODING PAGE JAVASCRIPT
// =========================

let currentProblem = null;
let currentContest = null;
let testCases = [];
let isExecuting = false;

function resolveApiBase() {
  if (window.API_BASE_URL) {
    return window.API_BASE_URL;
  }

  const hostname = window.location.hostname || "";
  const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1";
  const isPrivateIp = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(hostname);

  if (isLocalhost || isPrivateIp || !hostname) {
    return `http://${hostname || "127.0.0.1"}:8000`;
  }

  // Production-safe fallback if api-base.js is missing or failed to load.
  return "https://skillsprint-backend-i8q6.onrender.com";
}

function getApiBaseCandidates() {
  const candidates = [
    resolveApiBase(),
    "https://skillsprint-backend-i8q6.onrender.com"
  ];

  const unique = [];
  for (const item of candidates) {
    if (item && !unique.includes(item)) {
      unique.push(item);
    }
  }
  return unique;
}

const API_BASE = resolveApiBase();

function getToken() {
  const raw =
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    sessionStorage.getItem("access_token") ||
    sessionStorage.getItem("token") ||
    "";
  let cleaned = String(raw).trim().replace(/^"|"$/g, "");
  cleaned = cleaned.replace(/^Bearer\s+/i, "").trim();
  if (!cleaned || cleaned === "undefined" || cleaned === "null") {
    return "";
  }
  return cleaned;
}

async function parseJsonSafe(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (_err) {
    return null;
  }
}

async function runDirectCode(code, language, stdin = "") {
  const apiBases = getApiBaseCandidates();
  let lastError = "Compiler run failed";

  for (const baseUrl of apiBases) {
    try {
      const response = await fetch(`${baseUrl}/compiler/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          language,
          code,
          stdin,
          timeout: 5
        })
      });

      const result = await parseJsonSafe(response);
      if (!response.ok) {
        lastError =
          (result && (result.detail || result.message)) ||
          `${response.status} ${response.statusText}` ||
          "Compiler run failed";
        continue;
      }

      return result;
    } catch (error) {
      lastError = error?.message || "Compiler run failed";
    }
  }

  throw new Error(lastError);
}

// =========================
// INITIALIZATION
// =========================

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const contestId = params.get("contest_id");
  const problemId = params.get("problem_id");

  if (!contestId || !problemId) {
    alert("Contest or Problem not specified");
    return;
  }

  loadProblemData(contestId, problemId);
  loadLanguageCapabilities();

  // Add event listeners
  document.getElementById("runBtn")?.addEventListener("click", runTests);
  document.getElementById("submitBtn")?.addEventListener("click", submitCode);
});

async function loadLanguageCapabilities() {
  const select = document.getElementById("languageSelect");
  if (!select) {
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/compiler/languages`);
    if (!response.ok) {
      return;
    }

    const capabilities = await parseJsonSafe(response);
    if (!Array.isArray(capabilities)) {
      return;
    }

    const map = new Map(capabilities.map((item) => [item.key, item]));

    Array.from(select.options).forEach((option) => {
      const capability = map.get(option.value);
      if (!capability) {
        return;
      }

      if (!capability.available && capability.type !== "web") {
        option.disabled = true;
        option.textContent = `${option.textContent} (unavailable)`;
      }
    });
  } catch (_err) {
    // Keep selector usable even when capability check fails.
  }
}

// =========================
// LOAD PROBLEM DATA
// =========================

async function loadProblemData(contestId, problemId) {
  try {
    const token = getToken();
    if (!token) {
      alert("Not authenticated. Please log in first.");
      window.location.href = "../../index.html";
      return;
    }

    // Load contest details
    const contestRes = await fetch(`${API_BASE}/contests/${contestId}`, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    if (!contestRes.ok) throw new Error(`Contest load failed: ${contestRes.status}`);
    currentContest = await contestRes.json();

    // The backend exposes contest problems through /contests/{id}, so resolve
    // the selected problem from that payload instead of calling a missing route.
    currentProblem = (currentContest.problems || []).find(
      (problem) => String(problem.id) === String(problemId)
    );

    if (!currentProblem) {
      throw new Error("Problem not found in this contest");
    }

    // Load test cases
    const testRes = await fetch(
      `${API_BASE}/contests/${contestId}/problems/${problemId}/test-cases`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (testRes.ok) {
      testCases = await testRes.json();
    }

    // Render UI
    renderProblem();
    renderTestCases();
  } catch (error) {
    console.error("Error loading problem:", error);
    const statusEl = document.getElementById("executionStatus");
    if (statusEl) {
      statusEl.textContent = `Failed to load problem: ${error.message}`;
      statusEl.className = "execution-status error";
    }
    alert(`Failed to load problem: ${error.message}`);
  }
}

// =========================
// RENDER UI
// =========================

function renderProblem() {
  const problemPanel = document.getElementById("problemStatement");
  const problemTitle = document.getElementById("problemTitle");
  if (!problemPanel || !currentProblem) return;

  if (problemTitle) {
    problemTitle.textContent = currentProblem.title || "Problem";
  }

  problemPanel.innerHTML = `
    <div class="problem-card">
      <h2>${escapeHtml(currentProblem.title || "Untitled Problem")}</h2>
      <div class="problem-statement">${escapeHtml(
        currentProblem.statement || currentProblem.description || "No description provided"
      )}</div>
    </div>
  `;
}

function renderTestCases() {
  const container = document.getElementById("testCasesList");
  if (!container) return;

  if (!testCases || testCases.length === 0) {
    container.innerHTML = '<p class="empty-state">No test cases available</p>';
    return;
  }

  let html = '';

  testCases.slice(0, 3).forEach((tc, idx) => {
    html += `
      <div class="test-case-item">
        <strong>Test Case ${idx + 1}</strong>
        <p><strong>Input:</strong></p>
        <p>${escapeHtml(tc.input_data || "")}</p>
        <p><strong>Expected Output:</strong></p>
        <p>${escapeHtml(tc.expected_output || "")}</p>
      </div>
    `;
  });

  container.innerHTML = html;
}

// =========================
// CODE EXECUTION
// =========================

async function runTests() {
  if (isExecuting) {
    alert("Already executing. Please wait.");
    return;
  }

  const code = document.getElementById("codeEditor")?.value;
  const language = document.getElementById("languageSelect")?.value || "c";

  if (!code || code.trim().length === 0) {
    alert("Please enter some code");
    return;
  }

  isExecuting = true;
  updateExecutionStatus("Running tests...", "loading");

  try {
    const token = getToken();
    const params = new URLSearchParams(window.location.search);
    const contestId = params.get("contest_id");
    const problemId = params.get("problem_id");

    const response = await fetch(
      `${API_BASE}/contests/${contestId}/problems/${problemId}/execute`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          language,
          code: code
        })
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Execution failed");
    }

    const status = String(result.status || "").toUpperCase();
    if (status === "NO_TESTS") {
      try {
        const directRun = await runDirectCode(code, language, "");
        result.direct_run = directRun;
      } catch (directError) {
        result.direct_run = {
          status: "ERROR",
          message: directError.message || "Unable to execute code directly.",
          stdout: "",
          stderr: "",
          execution_time_ms: 0,
          exit_code: 1,
          language
        };
      }
    }

    displayResults(result);

    if (["UNSUPPORTED_LANGUAGE", "TOOL_UNAVAILABLE", "WEB_PREVIEW_ONLY", "COMPILATION_ERROR"].includes(status)) {
      const message = result.message || result.status || "Execution failed";
      updateExecutionStatus(message, "error");
      alert(message);
      return;
    }

    const passed = Number(result.passed || 0);
    const total = Number(result.total || 0);
    if (status === "NO_TESTS") {
      const directStatus = String(result.direct_run?.status || "").toUpperCase();
      if (directStatus && directStatus !== "SUCCESS") {
        updateExecutionStatus(`No test cases configured. Direct run status: ${directStatus}.`, "error");
      } else {
        updateExecutionStatus("No test cases configured. Direct run output shown below.", "success");
      }
    } else {
      updateExecutionStatus(`Tests complete: ${passed}/${total} passed (${status || "UNKNOWN"})`, "success");
    }
  } catch (error) {
    console.error("Execution error:", error);
    updateExecutionStatus(`Error: ${error.message}`, "error");
    alert(`Execution failed: ${error.message}`);
  } finally {
    isExecuting = false;
  }
}

function displayResults(executionResult) {
  const resultsContainer = document.getElementById("resultsList");
  if (!resultsContainer) return;

  const status = String(executionResult?.status || "").toUpperCase();
  const message = executionResult?.message || "";
  const directRun = executionResult?.direct_run || null;

  function renderDirectRunCard(run) {
    if (!run) {
      return "";
    }

    const runStatus = String(run.status || "UNKNOWN").toUpperCase();
    const runMessage = run.message || "";
    const stdout = run.stdout || "";
    const stderr = run.stderr || "";
    const exitCode = typeof run.exit_code === "number" ? run.exit_code : "-";
    const elapsed = typeof run.execution_time_ms === "number" ? `${run.execution_time_ms} ms` : "-";

    return `
      <div class="test-result info">
        <div class="result-header">
          <span>Direct Run Output</span>
          <span class="result-status">${escapeHtml(runStatus)}</span>
        </div>
        <div class="result-detail">
          <span class="result-label">Message:</span>
          <div class="result-value">${escapeHtml(runMessage || "Execution finished")}</div>
        </div>
        <div class="result-detail">
          <span class="result-label">Stdout:</span>
          <div class="result-value">${escapeHtml(stdout || "(empty)")}</div>
        </div>
        <div class="result-detail">
          <span class="result-label">Stderr:</span>
          <div class="result-value">${escapeHtml(stderr || "(empty)")}</div>
        </div>
        <div class="result-detail">
          <span class="result-label">Exit Code:</span>
          <div class="result-value">${escapeHtml(String(exitCode))}</div>
        </div>
        <div class="result-detail">
          <span class="result-label">Execution Time:</span>
          <div class="result-value">${escapeHtml(elapsed)}</div>
        </div>
      </div>
    `;
  }

  if (status === "NO_TESTS") {
    resultsContainer.innerHTML = `
      <div class="test-result info">
        <div class="result-header">
          <span>Execution Summary</span>
          <span class="result-status">NO_TESTS</span>
        </div>
        <div class="result-detail">
          <span class="result-label">Message:</span>
          <div class="result-value">${escapeHtml(message || "No test cases available for this problem.")}</div>
        </div>
      </div>
      ${renderDirectRunCard(directRun)}
    `;
    return;
  }

  if (["UNSUPPORTED_LANGUAGE", "TOOL_UNAVAILABLE", "WEB_PREVIEW_ONLY", "COMPILATION_ERROR"].includes(status)) {
    resultsContainer.innerHTML = `
      <div class="test-result runtime_error">
        <div class="result-header">
          <span>Execution Summary</span>
          <span class="result-status runtime_error">${escapeHtml(status || "ERROR")}</span>
        </div>
        <div class="result-detail">
          <span class="result-label">Message:</span>
          <div class="result-value">${escapeHtml(message || "Execution failed")}</div>
        </div>
      </div>
    `;
    return;
  }

  if (!executionResult.results || executionResult.results.length === 0) {
    resultsContainer.innerHTML = `
      <div class="test-result info">
        <div class="result-header">
          <span>Execution Summary</span>
          <span class="result-status">${escapeHtml(status || "UNKNOWN")}</span>
        </div>
        <div class="result-detail">
          <span class="result-label">Message:</span>
          <div class="result-value">${escapeHtml(message || "No detailed test-case output returned.")}</div>
        </div>
      </div>
    `;
    return;
  }

  let html = "";
  const results = executionResult.results;

  results.forEach((result, idx) => {
    const statusClass = result.status.toLowerCase();
    const isPass = result.status === "PASS";

    html += `
      <div class="test-result ${statusClass}">
        <div class="result-header">
          <span>Test Case ${idx + 1}</span>
          <span class="result-status ${statusClass}">${result.status}</span>
        </div>
    `;

    if (result.input) {
      html += `
        <div class="result-detail">
          <span class="result-label">Input:</span>
          <div class="result-value">${escapeHtml(result.input)}</div>
        </div>
      `;
    }

    if (result.expected) {
      html += `
        <div class="result-detail">
          <span class="result-label">Expected Output:</span>
          <div class="result-value">${escapeHtml(result.expected)}</div>
        </div>
      `;
    }

    if (result.actual) {
      html += `
        <div class="result-detail">
          <span class="result-label">Actual Output:</span>
          <div class="result-value">${escapeHtml(result.actual)}</div>
        </div>
      `;
    }

    if (result.error && !isPass) {
      html += `
        <div class="result-detail">
          <span class="result-label">Error:</span>
          <div class="result-value">${escapeHtml(result.error)}</div>
        </div>
      `;
    }

    html += "</div>";
  });

  resultsContainer.innerHTML = html;
}

async function submitCode() {
  if (isExecuting) {
    alert("Already executing. Please wait.");
    return;
  }

  const code = document.getElementById("codeEditor")?.value;
  const language = document.getElementById("languageSelect")?.value || "c";
  if (!code || code.trim().length === 0) {
    alert("Please enter some code before submitting");
    return;
  }

  // Run tests first to verify
  await runTests();

  if (isExecuting) return; // Wait for execution to finish

  // If all tests passed, submit. When there are no tests, allow direct submit.
  const resultsContainer = document.getElementById("resultsList");
  const hasNoTests = !testCases || testCases.length === 0;
  const allPassed =
    resultsContainer &&
    resultsContainer.querySelectorAll(".test-result").length > 0 &&
    !resultsContainer.innerHTML.includes("failed") &&
    !resultsContainer.innerHTML.includes("error");

  if (!allPassed && !hasNoTests) {
    // Ask user if they want to submit anyway
    const confirmSubmit = confirm(
      "Not all tests are passing. Do you still want to submit?"
    );
    if (!confirmSubmit) return;
  }

  // Submit the code
  try {
    const token = getToken();
    if (!token) {
      throw new Error("Not authenticated. Please log in again.");
    }

    const params = new URLSearchParams(window.location.search);
    const contestId = params.get("contest_id");
    const problemId = params.get("problem_id");
    if (!contestId || !problemId) {
      throw new Error("Missing contest or problem ID in URL.");
    }

    const apiBases = getApiBaseCandidates();

    const submitCandidates = [];
    apiBases.forEach((baseUrl) => {
      submitCandidates.push({
        url: `${baseUrl}/contests/${contestId}/problems/${problemId}/submit`,
        body: { language, code }
      });
      submitCandidates.push({
        url: `${baseUrl}/contests/${contestId}/submissions`,
        body: { problem_id: Number(problemId), language, code }
      });
    });

    let lastError = "Submission failed";
    let submitted = false;
    let hasConcreteServerError = false;

    for (const candidate of submitCandidates) {
      try {
        const response = await fetch(candidate.url, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify(candidate.body)
        });

        const result = await parseJsonSafe(response);

        if (!response.ok) {
          lastError =
            (result && (result.detail || result.message)) ||
            `${response.status} ${response.statusText}` ||
            "Submission failed";
          hasConcreteServerError = true;
          continue;
        }

        submitted = true;
        updateExecutionStatus("Submission saved successfully.", "success");
        alert("Code submitted successfully!");
        break;
      } catch (error) {
        if (error && error.name === "TypeError") {
          if (!hasConcreteServerError) {
            lastError = "Could not submit from browser. Refresh this page and log in again, then retry.";
          }
        } else {
          lastError = error.message || "Network error";
        }
      }
    }

    if (!submitted) {
      throw new Error(lastError);
    }

  } catch (error) {
    console.error("Submission error:", error);
    updateExecutionStatus(`Submission failed: ${error.message}`, "error");
    alert(`Submission failed: ${error.message}`);
  }
}

// =========================
// UTILITY FUNCTIONS
// =========================

function updateExecutionStatus(message, status = "loading") {
  const statusEl = document.getElementById("executionStatus");
  if (statusEl) {
    statusEl.textContent = message;
    statusEl.className = `execution-status ${status}`;
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

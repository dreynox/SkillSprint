// =========================
// CODING PAGE JAVASCRIPT
// =========================

let currentProblem = null;
let currentContest = null;
let testCases = [];
let isExecuting = false;

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

  // Add event listeners
  document.getElementById("runBtn")?.addEventListener("click", runTests);
  document.getElementById("submitBtn")?.addEventListener("click", submitCode);
});

// =========================
// LOAD PROBLEM DATA
// =========================

async function loadProblemData(contestId, problemId) {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Not authenticated. Please log in first.");
      window.location.href = "/html/login.html";
      return;
    }

    // Load contest details
    const contestRes = await fetch(`${API_BASE_URL}/contests/${contestId}`, {
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    if (!contestRes.ok) throw new Error(`Contest load failed: ${contestRes.status}`);
    currentContest = await contestRes.json();

    // Load problem details
    const problemRes = await fetch(
      `${API_BASE_URL}/contests/${contestId}/problems/${problemId}`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!problemRes.ok) throw new Error(`Problem load failed: ${problemRes.status}`);
    currentProblem = await problemRes.json();

    // Load test cases
    const testRes = await fetch(
      `${API_BASE_URL}/contests/${contestId}/problems/${problemId}/test-cases`,
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
    alert("Failed to load problem. Trying to reload...");
    setTimeout(() => window.location.reload(), 1000);
  }
}

// =========================
// RENDER UI
// =========================

function renderProblem() {
  const problemPanel = document.getElementById("problemStatement");
  if (!problemPanel || !currentProblem) return;

  problemPanel.innerHTML = `
    <div class="problem-card">
      <h2>${escapeHtml(currentProblem.title || "Untitled Problem")}</h2>
      <div class="problem-statement">${escapeHtml(
        currentProblem.description || "No description provided"
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

  if (language !== "c") {
    alert("Only C language is currently supported");
    return;
  }

  isExecuting = true;
  updateExecutionStatus("Running tests...", "loading");

  try {
    const token = localStorage.getItem("token");
    const params = new URLSearchParams(window.location.search);
    const contestId = params.get("contest_id");
    const problemId = params.get("problem_id");

    const response = await fetch(
      `${API_BASE_URL}/contests/${contestId}/problems/${problemId}/execute`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          language: "c",
          code: code
        })
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Execution failed");
    }

    displayResults(result);
    updateExecutionStatus("Tests complete", "success");
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

  if (!executionResult.results || executionResult.results.length === 0) {
    resultsContainer.innerHTML =
      '<div class="empty-state">No test results available</div>';
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
  if (!code || code.trim().length === 0) {
    alert("Please enter some code before submitting");
    return;
  }

  // Run tests first to verify
  await runTests();

  if (isExecuting) return; // Wait for execution to finish

  // If all tests passed, submit
  const resultsContainer = document.getElementById("resultsList");
  const allPassed =
    resultsContainer &&
    resultsContainer.querySelectorAll(".test-result").length > 0 &&
    !resultsContainer.innerHTML.includes("failed") &&
    !resultsContainer.innerHTML.includes("error");

  if (!allPassed) {
    // Ask user if they want to submit anyway
    const confirmSubmit = confirm(
      "Not all tests are passing. Do you still want to submit?"
    );
    if (!confirmSubmit) return;
  }

  // Submit the code
  try {
    const token = localStorage.getItem("token");
    const params = new URLSearchParams(window.location.search);
    const contestId = params.get("contest_id");
    const problemId = params.get("problem_id");

    const response = await fetch(
      `${API_BASE_URL}/contests/${contestId}/submissions`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          problem_id: problemId,
          language: "c",
          code: code
        })
      }
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "Submission failed");
    }

    alert("Code submitted successfully!");
    // Optionally redirect to contest page after successful submission
    // window.location.href = `/html/contests.html?id=${contestId}`;
  } catch (error) {
    console.error("Submission error:", error);
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

(function () {
  const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";
  let cachedContests = [];
  let cachedQuizTests = [];

  const glow = document.querySelector(".cursor-glow");
  document.addEventListener("mousemove", function (event) {
    if (!glow) {
      return;
    }

    glow.style.left = event.clientX + "px";
    glow.style.top = event.clientY + "px";
  });

  const matrixCanvas = document.getElementById("matrix");
  if (matrixCanvas) {
    const matrixContext = matrixCanvas.getContext("2d");

    function resizeCanvas() {
      matrixCanvas.width = window.innerWidth;
      matrixCanvas.height = window.innerHeight;
    }

    resizeCanvas();

    const letters = "01SYSTEMHACKACCESSGRANTED";
    const fontSize = 14;
    let columns = Math.floor(matrixCanvas.width / fontSize);
    let drops = Array.from({ length: columns }).fill(1);

    function drawMatrix() {
      matrixContext.fillStyle = "rgba(0, 0, 0, 0.08)";
      matrixContext.fillRect(0, 0, matrixCanvas.width, matrixCanvas.height);

      matrixContext.fillStyle = "#00ff88";
      matrixContext.font = fontSize + "px monospace";

      drops.forEach(function (y, index) {
        const text = letters[Math.floor(Math.random() * letters.length)];
        matrixContext.fillText(text, index * fontSize, y * fontSize);

        if (y * fontSize > matrixCanvas.height && Math.random() > 0.975) {
          drops[index] = 0;
        }

        drops[index] += 1;
      });
    }

    setInterval(drawMatrix, 33);

    window.addEventListener("resize", function () {
      resizeCanvas();
      columns = Math.floor(matrixCanvas.width / fontSize);
      drops = Array.from({ length: columns }).fill(1);
    });
  }

  function parseUser() {
    try {
      return JSON.parse(localStorage.getItem("user") || "null");
    } catch (_err) {
      return null;
    }
  }

  function getToken() {
    const raw = localStorage.getItem("access_token") || localStorage.getItem("token") || "";
    const cleaned = String(raw).trim().replace(/^"|"$/g, "").replace(/^Bearer\s+/i, "").trim();
    return cleaned && cleaned !== "undefined" && cleaned !== "null" ? cleaned : "";
  }

  function authHeaders(withJson = false) {
    const token = getToken();
    const headers = {};
    if (token) {
      headers.Authorization = "Bearer " + token;
    }
    if (withJson) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  function clearSessionAndRedirect() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("token");
    window.location.href = "../../index.html";
  }

  function requireAdmin() {
    const token = localStorage.getItem("access_token");
    const user = parseUser();

    if (!token || !user) {
      window.location.href = "../../index.html";
      return null;
    }

    if (user.role !== "admin") {
      window.location.href = "student-dashboard.html";
      return null;
    }

    return user;
  }

  function resolveAvatarUrl(avatarUrl) {
    if (!avatarUrl) {
      return "../images/default-avatar.svg";
    }

    if (avatarUrl.startsWith("http://") || avatarUrl.startsWith("https://") || avatarUrl.startsWith("data:")) {
      return avatarUrl;
    }

    if (avatarUrl.startsWith("/")) {
      return API_BASE + avatarUrl;
    }

    return avatarUrl;
  }

  function syncProfileMenu(user) {
    const menu = document.getElementById("profileMenu");
    const button = document.getElementById("profileMenuBtn");
    const avatar = document.getElementById("topbarAvatar");
    const label = document.getElementById("profileMenuLabel");

    if (avatar) {
      avatar.src = resolveAvatarUrl(user && user.avatar_url ? user.avatar_url : "");
    }

    if (label) {
      label.textContent = user && user.name ? user.name : "Profile";
    }

    if (button && menu) {
      button.setAttribute("aria-expanded", "false");
      menu.classList.remove("open");
    }
  }

  function formatDateText(value) {
    if (!value) {
      return "TBD";
    }
    return new Date(value).toLocaleString();
  }

  function formatDuration(start, end) {
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
      return `Duration: ${minutes}m`;
    }

    return `Duration: ${hours}h ${minutes ? `${minutes}m` : ""}`.trim();
  }

  function populateQuestionContestSelect(contests) {
    const select = document.getElementById("questionContestId");
    if (!select) {
      return;
    }

    select.innerHTML = "";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = contests.length ? "Select a contest" : "No contests available";
    placeholder.disabled = true;
    placeholder.selected = true;
    select.appendChild(placeholder);

    contests.forEach(function (contest) {
      const option = document.createElement("option");
      option.value = String(contest.id);
      option.textContent = contest.name + " | " + formatDuration(contest.start_time, contest.end_time);
      select.appendChild(option);
    });
  }

  function populateTestContestSelect(contests) {
    const select = document.getElementById("testContestId");
    if (!select) {
      return;
    }

    select.innerHTML = "";

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = contests.length ? "Select a contest" : "No contests available";
    placeholder.disabled = true;
    placeholder.selected = true;
    select.appendChild(placeholder);

    contests.forEach(function (contest) {
      const option = document.createElement("option");
      option.value = String(contest.id);
      option.textContent = contest.name + " | " + formatDuration(contest.start_time, contest.end_time);
      select.appendChild(option);
    });
  }

  function populateQuizTestSelect() {
    const quizSelect = document.getElementById("quizTestId");
    const submissionSelect = document.getElementById("quizSubmissionTestId");

    [quizSelect, submissionSelect].forEach(function (select) {
      if (!select) {
        return;
      }

      select.innerHTML = "";
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = cachedQuizTests.length ? "Select a quiz test" : "No quiz tests available";
      placeholder.disabled = true;
      placeholder.selected = true;
      select.appendChild(placeholder);

      cachedQuizTests.forEach(function (test) {
        const option = document.createElement("option");
        option.value = String(test.id);
        option.textContent = `${test.title} (ID: ${test.id})`;
        select.appendChild(option);
      });
    });
  }

  async function populateProblemSelect(contestId) {
    const select = document.getElementById("testProblemId");
    if (!select) {
      return;
    }

    select.innerHTML = "";
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = contestId ? "Loading questions..." : "Select a contest first";
    emptyOption.disabled = true;
    emptyOption.selected = true;
    select.appendChild(emptyOption);

    if (!contestId) {
      return;
    }

    try {
      const response = await fetch(API_BASE + "/contests/" + contestId + "/admin", {
        headers: authHeaders(),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to load questions");
      }

      select.innerHTML = "";
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = data.problems && data.problems.length ? "Select a question" : "No questions in this contest";
      placeholder.disabled = true;
      placeholder.selected = true;
      select.appendChild(placeholder);

      (data.problems || []).forEach(function (problem) {
        const option = document.createElement("option");
        option.value = String(problem.id);
        option.textContent = problem.title;
        select.appendChild(option);
      });
    } catch (_error) {
      select.innerHTML = "<option value=\"\" disabled selected>Unable to load questions</option>";
    }
  }

  function renderFeed(contests, hackathons) {
    const feed = document.getElementById("adminFeed");
    if (!feed) {
      return;
    }

    const rows = [];

    contests.forEach(function (contest) {
      rows.push(
        "<div class=\"list-item\"><div><b>[Contest] " +
          escapeHtml(contest.name) +
          "</b><span>" +
          formatDateText(contest.start_time) +
          " to " +
          formatDateText(contest.end_time) +
          "</span></div><span class=\"badge\">" +
          (contest.is_active ? "Active" : "Draft") +
          "</span></div>"
      );
    });

    hackathons.forEach(function (hackathon) {
      rows.push(
        "<div class=\"list-item\"><div><b>[Hackathon] " +
          escapeHtml(hackathon.title) +
          "</b><span>" +
          formatDateText(hackathon.start_time) +
          " to " +
          formatDateText(hackathon.end_time) +
          "</span></div><span class=\"badge\">" +
          (hackathon.is_active ? "Active" : "Draft") +
          "</span></div>"
      );
    });

    if (!rows.length) {
      feed.innerHTML = "<div class=\"list-item\"><div><b>No posted events yet</b><span>Create your first contest or hackathon from above.</span></div><span class=\"badge\">0</span></div>";
      return;
    }

    feed.innerHTML = rows.join("");
  }

  function renderSubmissionFeed(submissions) {
    const feed = document.getElementById("submissionFeed");
    if (!feed) {
      return;
    }

    if (!Array.isArray(submissions) || submissions.length === 0) {
      feed.innerHTML = "<div class=\"list-item\"><div><b>No submissions yet</b><span>Submitted contest solutions will appear here with student credentials.</span></div><span class=\"badge\">0</span></div>";
      return;
    }

    const rows = submissions.slice(0, 50).map(function (item) {
      const submittedAt = formatDateText(item.submitted_at);
      const codePreview = String(item.code || "").trim();
      const renderedCode = codePreview
        ? "<details class=\"submission-code\"><summary>View Code</summary><pre>" +
          escapeHtml(codePreview) +
          "</pre></details>"
        : "<span class=\"submission-code-empty\">No code attached</span>";
      const credentials = [
        item.srn ? "SRN: " + escapeHtml(item.srn) : null,
        item.prn ? "PRN: " + escapeHtml(item.prn) : null,
        item.roll_no ? "Roll: " + escapeHtml(item.roll_no) : null,
        item.year ? "Year: " + escapeHtml(String(item.year)) : null,
        item.branch ? "Branch: " + escapeHtml(item.branch) : null,
        item.division ? "Division: " + escapeHtml(item.division) : null,
      ].filter(Boolean).join(" | ");

      const detailLine = credentials || "No credential details available";

      return (
        "<div class=\"list-item\"><div><b>" +
        escapeHtml(item.contest_name || "Contest") +
        " | " +
        escapeHtml(item.problem_title || "Problem") +
        "</b><span>By " +
        escapeHtml(item.user_name || "Unknown User") +
        " (" +
        escapeHtml(item.user_email || "-") +
        ") | " +
        detailLine +
        " | Language: " +
        escapeHtml(item.language || "-") +
        " | Verdict: " +
        escapeHtml(item.verdict || "PENDING") +
        " | Score: " +
        escapeHtml(String(item.score ?? 0)) +
        " | Submitted: " +
        escapeHtml(submittedAt) +
        "</span>" + renderedCode + "</div><span class=\"badge\">" +
        escapeHtml(item.verdict || "PENDING") +
        "</span></div>"
      );
    });

    feed.innerHTML = rows.join("");
  }

  function escapeHtml(str) {
    if (!str) {
      return "";
    }
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function setStatus(id, message, isError) {
    const element = document.getElementById(id);
    if (!element) {
      return;
    }
    element.textContent = message;
    element.style.color = isError ? "#f87171" : "#9bf7c4";
    if (window.SkillSprintUX && typeof window.SkillSprintUX.showStatus === "function") {
      window.SkillSprintUX.showStatus(message, isError ? "error" : "info");
    }
  }

  function isAuthFailure(statusCode) {
    return statusCode === 401 || statusCode === 403;
  }

  function handleAuthFailure(statusId, detailMessage) {
    setStatus(statusId, detailMessage || "Session expired. Please log in again.", true);
    clearSessionAndRedirect();
  }

  async function requestJson(url, options) {
    const response = await fetch(url, options);
    let data = null;
    try {
      data = await response.json();
    } catch (_error) {
      data = null;
    }
    return { response, data };
  }

  function activateWorkflow(targetGroup) {
    document.querySelectorAll("[data-admin-group]").forEach(function (section) {
      const group = section.getAttribute("data-admin-group");
      if (!group) {
        return;
      }
      section.classList.toggle("admin-hidden", group !== targetGroup);
    });

    document.querySelectorAll(".workflow-tab").forEach(function (button) {
      const isActive = button.getAttribute("data-target") === targetGroup;
      button.classList.toggle("active", isActive);
      button.setAttribute("aria-selected", String(isActive));
    });
  }

  function wireWorkflowTabs() {
    const tabs = Array.from(document.querySelectorAll(".workflow-tab"));
    if (!tabs.length) {
      return;
    }

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        const target = tab.getAttribute("data-target");
        if (!target) {
          return;
        }
        activateWorkflow(target);
        if (window.SkillSprintUX && typeof window.SkillSprintUX.showStatus === "function") {
          window.SkillSprintUX.showStatus("Switched to " + target.replace("-", " ") + " workflow.", "info");
        }
      });
    });

    const defaultTarget = tabs[0].getAttribute("data-target") || "contest-setup";
    activateWorkflow(defaultTarget);
  }

  function toIsoOrNull(value) {
    if (!value) {
      return null;
    }
    return new Date(value).toISOString();
  }

  async function loadFeed() {
    try {
      const contestResponse = await fetch(API_BASE + "/contests");
      const contests = contestResponse.ok ? await contestResponse.json() : [];
      cachedContests = Array.isArray(contests) ? contests : [];

      const hackathonResponse = await fetch(API_BASE + "/hackathons");
      const hackathons = hackathonResponse.ok ? await hackathonResponse.json() : [];

      populateQuestionContestSelect(cachedContests);
      populateTestContestSelect(cachedContests);
      renderFeed(Array.isArray(contests) ? contests : [], Array.isArray(hackathons) ? hackathons : []);
    } catch (_error) {
      populateQuestionContestSelect([]);
      populateTestContestSelect([]);
      renderFeed([], []);
    }
  }

  async function loadQuizTests() {
    try {
      const response = await fetch(API_BASE + "/quiz/admin/tests", {
        headers: authHeaders(),
      });
      if (!response.ok) {
        cachedQuizTests = [];
        populateQuizTestSelect();
        return;
      }

      const data = await response.json();
      cachedQuizTests = Array.isArray(data) ? data : [];
      populateQuizTestSelect();
    } catch (_error) {
      cachedQuizTests = [];
      populateQuizTestSelect();
    }
  }

  async function createQuestion() {
    const contestId = document.getElementById("questionContestId").value;
    const title = document.getElementById("questionTitle").value.trim();
    const statement = document.getElementById("questionStatement").value.trim();
    const difficulty = document.getElementById("questionDifficulty").value.trim();
    const tags = document.getElementById("questionTags").value.trim();

    if (!contestId) {
      setStatus("questionStatus", "Please choose a contest.", true);
      return;
    }

    if (!title || !statement) {
      setStatus("questionStatus", "Question title and statement are required.", true);
      return;
    }

    setStatus("questionStatus", "Adding question...", false);
    const btn = document.getElementById("createQuestionBtn");
    btn.disabled = true;

    try {
      const result = await requestJson(API_BASE + "/contests/" + contestId + "/problems", {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          title: title,
          statement: statement,
          difficulty: difficulty || null,
          tags: tags || null,
        }),
      });
      const response = result.response;
      const data = result.data || {};

      if (!response.ok) {
        if (isAuthFailure(response.status)) {
          handleAuthFailure("questionStatus", data.detail);
          return;
        }
        throw new Error(data.detail || "Unable to add question");
      }

      setStatus("questionStatus", "Question added successfully. It will appear inside the contest.", false);
      document.getElementById("questionTitle").value = "";
      document.getElementById("questionStatement").value = "";
      document.getElementById("questionDifficulty").value = "";
      document.getElementById("questionTags").value = "";
      await loadFeed();
      await populateProblemSelect(contestId);
    } catch (error) {
      setStatus("questionStatus", error.message || "Unable to add question", true);
    } finally {
      btn.disabled = false;
    }
  }

  async function createTestCase() {
    const contestId = document.getElementById("testContestId").value;
    const problemId = document.getElementById("testProblemId").value;
    const inputData = document.getElementById("testInputData").value;
    const expectedOutput = document.getElementById("testExpectedOutput").value.trim();

    if (!contestId || !problemId) {
      setStatus("testCaseStatus", "Please choose a contest and question.", true);
      return;
    }

    if (!expectedOutput) {
      setStatus("testCaseStatus", "Expected output is required.", true);
      return;
    }

    setStatus("testCaseStatus", "Adding test case...", false);
    const btn = document.getElementById("createTestCaseBtn");
    btn.disabled = true;

    try {
      const result = await requestJson(API_BASE + "/contests/" + contestId + "/problems/" + problemId + "/test-cases", {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          input_data: inputData || null,
          expected_output: expectedOutput,
        }),
      });
      const response = result.response;
      const data = result.data || {};

      if (!response.ok) {
        if (isAuthFailure(response.status)) {
          handleAuthFailure("testCaseStatus", data.detail);
          return;
        }
        throw new Error(data.detail || "Unable to add test case");
      }

      setStatus("testCaseStatus", "Test case added successfully.", false);
      document.getElementById("testInputData").value = "";
      document.getElementById("testExpectedOutput").value = "";
    } catch (error) {
      setStatus("testCaseStatus", error.message || "Unable to add test case", true);
    } finally {
      btn.disabled = false;
    }
  }

  async function loadSubmissionFeed() {
    const user = parseUser();
    const token = localStorage.getItem("access_token");
    if (!user || user.role !== "admin" || !token) {
      return;
    }

    const feed = document.getElementById("submissionFeed");
    if (feed) {
      feed.innerHTML = "<div class=\"list-item\"><div><b>Loading submissions...</b><span>Fetching recent code submissions.</span></div><span class=\"badge\">...</span></div>";
    }

    try {
      const response = await fetch(API_BASE + "/contests/admin/submissions", {
        headers: {
          Authorization: "Bearer " + token,
        },
      });

      const data = response.ok ? await response.json() : [];
      renderSubmissionFeed(Array.isArray(data) ? data : []);
    } catch (_error) {
      if (feed) {
        feed.innerHTML = "<div class=\"list-item\"><div><b>Could not load submissions</b><span>Please check API availability and admin auth.</span></div><span class=\"badge\">Error</span></div>";
      }
    }
  }

  async function createContest() {
    const name = document.getElementById("contestName").value.trim();
    const description = document.getElementById("contestDescription").value.trim();
    const startTime = document.getElementById("contestStart").value;
    const endTime = document.getElementById("contestEnd").value;
    const isActive = document.getElementById("contestActive").checked;

    if (!name) {
      setStatus("contestStatus", "Contest name is required.", true);
      return;
    }

    setStatus("contestStatus", "Posting contest...", false);
    const btn = document.getElementById("createContestBtn");
    btn.disabled = true;

    try {
      const result = await requestJson(API_BASE + "/contests", {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          name: name,
          description: description || null,
          start_time: toIsoOrNull(startTime),
          end_time: toIsoOrNull(endTime),
          is_active: isActive,
        }),
      });
      const response = result.response;
      const data = result.data || {};

      if (!response.ok) {
        if (isAuthFailure(response.status)) {
          handleAuthFailure("contestStatus", data.detail);
          return;
        }
        throw new Error(data.detail || "Unable to create contest");
      }

      setStatus("contestStatus", "Contest posted successfully.", false);
      document.getElementById("contestName").value = "";
      document.getElementById("contestDescription").value = "";
      document.getElementById("contestStart").value = "";
      document.getElementById("contestEnd").value = "";
      await loadFeed();
    } catch (error) {
      setStatus("contestStatus", error.message || "Unable to create contest", true);
    } finally {
      btn.disabled = false;
    }
  }

  async function createHackathon() {
    const title = document.getElementById("hackathonTitle").value.trim();
    const description = document.getElementById("hackathonDescription").value.trim();
    const startTime = document.getElementById("hackathonStart").value;
    const endTime = document.getElementById("hackathonEnd").value;
    const isActive = document.getElementById("hackathonActive").checked;

    if (!title) {
      setStatus("hackathonStatus", "Hackathon title is required.", true);
      return;
    }

    setStatus("hackathonStatus", "Posting hackathon...", false);
    const btn = document.getElementById("createHackathonBtn");
    btn.disabled = true;

    try {
      const result = await requestJson(API_BASE + "/hackathons", {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          title: title,
          description: description || null,
          start_time: toIsoOrNull(startTime),
          end_time: toIsoOrNull(endTime),
          is_active: isActive,
        }),
      });
      const response = result.response;
      const data = result.data || {};

      if (!response.ok) {
        if (isAuthFailure(response.status)) {
          handleAuthFailure("hackathonStatus", data.detail);
          return;
        }
        throw new Error(data.detail || "Unable to create hackathon");
      }

      setStatus("hackathonStatus", "Hackathon posted successfully.", false);
      document.getElementById("hackathonTitle").value = "";
      document.getElementById("hackathonDescription").value = "";
      document.getElementById("hackathonStart").value = "";
      document.getElementById("hackathonEnd").value = "";
      await loadFeed();
    } catch (error) {
      setStatus("hackathonStatus", error.message || "Unable to create hackathon", true);
    } finally {
      btn.disabled = false;
    }
  }

  async function createQuizTest() {
    const title = document.getElementById("quizTitle").value.trim();
    const description = document.getElementById("quizDescription").value.trim();
    const startTime = document.getElementById("quizStart").value;
    const endTime = document.getElementById("quizEnd").value;
    const isActive = document.getElementById("quizActive").checked;

    if (!title) {
      setStatus("quizStatus", "Quiz title is required.", true);
      return;
    }

    setStatus("quizStatus", "Creating quiz test...", false);
    const btn = document.getElementById("createQuizBtn");
    btn.disabled = true;

    try {
      const result = await requestJson(API_BASE + "/quiz/admin/tests", {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          title: title,
          description: description || null,
          is_active: isActive,
          start_time: toIsoOrNull(startTime),
          end_time: toIsoOrNull(endTime),
        }),
      });
      const response = result.response;
      const data = result.data || {};

      if (!response.ok) {
        if (isAuthFailure(response.status)) {
          handleAuthFailure("quizStatus", data.detail);
          return;
        }
        throw new Error(data.detail || "Unable to create quiz test");
      }

      setStatus("quizStatus", `Quiz test created (ID: ${data.id}).`, false);
      document.getElementById("quizTitle").value = "";
      document.getElementById("quizDescription").value = "";
      document.getElementById("quizStart").value = "";
      document.getElementById("quizEnd").value = "";
      await loadQuizTests();
    } catch (error) {
      setStatus("quizStatus", error.message || "Unable to create quiz test", true);
    } finally {
      btn.disabled = false;
    }
  }

  async function createQuizQuestion() {
    const testId = document.getElementById("quizTestId").value;
    const text = document.getElementById("quizQuestionText").value.trim();
    const optionA = document.getElementById("quizOptionA").value.trim();
    const optionB = document.getElementById("quizOptionB").value.trim();
    const optionC = document.getElementById("quizOptionC").value.trim();
    const optionD = document.getElementById("quizOptionD").value.trim();
    const correctOption = document.getElementById("quizCorrectOption").value;

    if (!testId) {
      setStatus("quizQuestionStatus", "Please select a quiz test.", true);
      return;
    }

    if (!text || !optionA || !optionB || !optionC || !optionD) {
      setStatus("quizQuestionStatus", "Question and all options are required.", true);
      return;
    }

    setStatus("quizQuestionStatus", "Adding quiz question...", false);
    const btn = document.getElementById("createQuizQuestionBtn");
    btn.disabled = true;

    try {
      const result = await requestJson(API_BASE + "/quiz/admin/tests/" + testId + "/questions", {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          text: text,
          option_a: optionA,
          option_b: optionB,
          option_c: optionC,
          option_d: optionD,
          correct_option: correctOption,
        }),
      });
      const response = result.response;
      const data = result.data || {};

      if (!response.ok) {
        if (isAuthFailure(response.status)) {
          handleAuthFailure("quizQuestionStatus", data.detail);
          return;
        }
        throw new Error(data.detail || "Unable to add quiz question");
      }

      setStatus("quizQuestionStatus", `Question added to quiz ${testId}.`, false);
      document.getElementById("quizQuestionText").value = "";
      document.getElementById("quizOptionA").value = "";
      document.getElementById("quizOptionB").value = "";
      document.getElementById("quizOptionC").value = "";
      document.getElementById("quizOptionD").value = "";
    } catch (error) {
      setStatus("quizQuestionStatus", error.message || "Unable to add quiz question", true);
    } finally {
      btn.disabled = false;
    }
  }

  async function loadQuizSubmissionFeed() {
    const testId = document.getElementById("quizSubmissionTestId").value;
    const feed = document.getElementById("quizSubmissionFeed");
    if (!feed) {
      return;
    }

    if (!testId) {
      feed.innerHTML = "<div class=\"list-item\"><div><b>Select a quiz test first</b><span>Choose a test above to view student quiz responses.</span></div><span class=\"badge\">Quiz</span></div>";
      return;
    }

    feed.innerHTML = "<div class=\"list-item\"><div><b>Loading quiz submissions...</b><span>Fetching student responses.</span></div><span class=\"badge\">...</span></div>";

    try {
      const response = await fetch(API_BASE + "/quiz/admin/tests/" + testId + "/submissions", {
        headers: authHeaders(),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to load quiz submissions");
      }

      if (!Array.isArray(data) || !data.length) {
        feed.innerHTML = "<div class=\"list-item\"><div><b>No quiz submissions yet</b><span>Student quiz responses will appear here.</span></div><span class=\"badge\">0</span></div>";
        return;
      }

      feed.innerHTML = data
        .slice(0, 50)
        .map(function (row) {
          return "<div class=\"list-item\"><div><b>" +
            escapeHtml(row.user_name || "Student") +
            " (" +
            escapeHtml(row.user_email || "-") +
            ")</b><span>Score: " +
            escapeHtml(String(row.score ?? 0)) +
            " / " +
            escapeHtml(String(row.total_questions ?? 0)) +
            " | Submitted: " +
            escapeHtml(formatDateText(row.submitted_at)) +
            "</span></div><span class=\"badge\">" +
            escapeHtml(String(row.score ?? 0)) +
            "</span></div>";
        })
        .join("");
    } catch (error) {
      feed.innerHTML = "<div class=\"list-item\"><div><b>Could not load quiz submissions</b><span>" + escapeHtml(error.message || "Try again") + "</span></div><span class=\"badge\">Error</span></div>";
    }
  }

  document.getElementById("createContestBtn").addEventListener("click", createContest);
  document.getElementById("createHackathonBtn").addEventListener("click", createHackathon);
  document.getElementById("createQuestionBtn").addEventListener("click", createQuestion);
  document.getElementById("createTestCaseBtn").addEventListener("click", createTestCase);
  document.getElementById("createQuizBtn").addEventListener("click", createQuizTest);
  document.getElementById("createQuizQuestionBtn").addEventListener("click", createQuizQuestion);
  document.getElementById("loadQuizSubmissionsBtn").addEventListener("click", loadQuizSubmissionFeed);
  document.getElementById("testContestId").addEventListener("change", function (event) {
    populateProblemSelect(event.target.value);
  });
  const profileMenuBtn = document.getElementById("profileMenuBtn");
  const profileMenu = document.getElementById("profileMenu");
  if (profileMenuBtn && profileMenu) {
    profileMenuBtn.addEventListener("click", function (event) {
      event.stopPropagation();
      const isOpen = profileMenu.classList.toggle("open");
      profileMenuBtn.setAttribute("aria-expanded", String(isOpen));
    });
  }

  document.getElementById("profileMenuLogoutBtn").addEventListener("click", function () {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("token");
    window.location.href = "../../index.html";
  });

  document.addEventListener("click", function (event) {
    if (profileMenu && !profileMenu.contains(event.target)) {
      profileMenu.classList.remove("open");
      if (profileMenuBtn) {
        profileMenuBtn.setAttribute("aria-expanded", "false");
      }
    }
  });
  document.getElementById("logoutBtn").addEventListener("click", function () {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("token");
    window.location.href = "../../index.html";
  });

  const user = requireAdmin();
  if (!user) {
    return;
  }

  document.getElementById("welcomeText").textContent = "Welcome, " + user.name;
  document.getElementById("heroTitle").textContent = "Hello " + user.name + ", publish new events";
  syncProfileMenu(user);
  wireWorkflowTabs();

  loadFeed();
  loadSubmissionFeed();
  loadQuizTests();
})();

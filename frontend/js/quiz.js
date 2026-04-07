const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";

const loadBtn = document.getElementById("load-btn");
const submitBtn = document.getElementById("submit-btn");
const startRandomBtn = document.getElementById("start-random-btn");
const testIdInput = document.getElementById("test-id");
const userIdInput = document.getElementById("user-id");
const languageInput = document.getElementById("language");
const levelInput = document.getElementById("level");
const statusEl = document.getElementById("status");
const quizForm = document.getElementById("quiz-form");
const resultContainer = document.getElementById("result-container");

let questions = [];
let randomSessionId = null;
let currentMode = "test";
let timerIntervalId = null;
let quizEndsAt = null;
let quizInProgress = false;

const QUIZ_DURATION_SECONDS = 30 * 60;

function saveQuizResult(result) {
  sessionStorage.setItem("quiz_result", JSON.stringify(result));
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#b00020" : "#333";
}

function renderQuestions(items) {
  quizForm.innerHTML = "";

  items.forEach((question, index) => {
    const block = document.createElement("div");
    block.className = "question-block";
    block.style.marginBottom = "20px";

    const title = document.createElement("h2");
    title.textContent = `${index + 1}. ${question.text}`;
    title.style.marginBottom = "12px";
    block.appendChild(title);

    const options = [
      ["A", question.options.A],
      ["B", question.options.B],
      ["C", question.options.C],
      ["D", question.options.D],
    ];

    options.forEach(([label, value]) => {
      const option = document.createElement("label");
      option.className = "option";
      option.style.display = "block";

      const input = document.createElement("input");
      input.type = "radio";
      input.name = `question-${question.id}`;
      input.value = label;
      input.style.marginRight = "8px";

      option.appendChild(input);
      option.appendChild(document.createTextNode(`${label}. ${value}`));
      block.appendChild(option);
    });

    quizForm.appendChild(block);
  });
}

function formatCountdown(seconds) {
  const totalSeconds = Math.max(0, seconds);
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function getUnansweredQuestionNumbers() {
  return questions
    .map((question, index) => {
      const selected = document.querySelector(`input[name='question-${question.id}']:checked`);
      return selected ? null : index + 1;
    })
    .filter(Boolean);
}

function buildUnansweredMessage(unansweredNumbers) {
  if (!unansweredNumbers.length) {
    return "";
  }

  const labels = unansweredNumbers.map((number) => `Q.${number} Unanswered`);
  return `${labels.join(", ")}. Attempt all questions.`;
}

function renderSubmitHint() {
  if (!quizInProgress || !questions.length) {
    return;
  }

  const unansweredNumbers = getUnansweredQuestionNumbers();
  if (unansweredNumbers.length) {
    setStatus(`${unansweredNumbers.length} question(s) remaining.`, false);
  } else {
    setStatus("All questions answered. You can submit now.", false);
  }
}

function renderResultLink(summary) {
  resultContainer.style.display = "block";
  resultContainer.innerHTML = `
    <a class="view-score-link" href="result.html">View Score</a>
  `;
}

function updateTimerDisplay(remainingSeconds) {
  const timerBox = document.getElementById("timer-box");
  const timerValue = document.getElementById("timer-value");

  if (!timerBox || !timerValue) {
    return;
  }

  timerBox.style.display = "block";
  timerValue.textContent = formatCountdown(remainingSeconds);
}

function resetTimer() {
  if (timerIntervalId) {
    clearInterval(timerIntervalId);
    timerIntervalId = null;
  }

  quizEndsAt = null;
  quizInProgress = false;

  const timerBox = document.getElementById("timer-box");
  const timerValue = document.getElementById("timer-value");
  if (timerBox) {
    timerBox.style.display = "none";
  }
  if (timerValue) {
    timerValue.textContent = formatCountdown(QUIZ_DURATION_SECONDS);
  }
}

function startTimer() {
  resetTimer();
  quizEndsAt = Date.now() + QUIZ_DURATION_SECONDS * 1000;
  quizInProgress = true;

  const tick = () => {
    const remainingSeconds = Math.max(0, Math.floor((quizEndsAt - Date.now()) / 1000));
    updateTimerDisplay(remainingSeconds);

    if (remainingSeconds <= 0) {
      if (timerIntervalId) {
        clearInterval(timerIntervalId);
        timerIntervalId = null;
      }
      quizInProgress = false;
      setStatus("Time is up. Submitting automatically...", false);
      submitAnswers({ autoSubmit: true });
    }
  };

  tick();
  timerIntervalId = setInterval(tick, 1000);
}

function collectAnswers() {
  return questions
    .map((question) => {
      const selected = document.querySelector(`input[name='question-${question.id}']:checked`);
      if (!selected) {
        return null;
      }
      return {
        question_id: question.id,
        selected: selected.value,
      };
    })
    .filter(Boolean);
}

async function loadQuestions() {
  const testId = Number(testIdInput.value);
  if (!testId) {
    setStatus("Please enter a valid test ID", true);
    return;
  }

  setStatus("Loading questions...");
  submitBtn.disabled = true;
  resultContainer.style.display = "none";
  resetTimer();

  try {
    const response = await fetch(`${API_BASE}/quiz/tests/${testId}/questions`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to load questions");
    }

    questions = data.map((question) => ({
      id: question.id,
      text: question.text,
      options: {
        A: question.option_a,
        B: question.option_b,
        C: question.option_c,
        D: question.option_d,
      },
    }));

    if (questions.length === 0) {
      setStatus("No questions found for this test", true);
      quizForm.innerHTML = "";
      return;
    }

    renderQuestions(questions);
    submitBtn.disabled = false;
    currentMode = "test";
    randomSessionId = null;
    startTimer();
    setStatus(`Loaded ${questions.length} questions for test ${testId}`);
    renderSubmitHint();
  } catch (error) {
    setStatus(error.message, true);
    quizForm.innerHTML = "";
  }
}

async function startRandomSession() {
  const language = languageInput ? languageInput.value : "C";
  const level = levelInput ? levelInput.value : "Beginner";

  setStatus("Creating random question session...");
  submitBtn.disabled = true;
  resultContainer.style.display = "none";
  resetTimer();

  try {
    const response = await fetch(`${API_BASE}/quiz/random-bank/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        language,
        level,
        question_count: 20,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to create random session");
    }

    randomSessionId = data.session_id;
    currentMode = "random";

    questions = data.questions.map((question) => ({
      id: question.question_id,
      text: question.question,
      options: {
        A: question.options.A,
        B: question.options.B,
        C: question.options.C,
        D: question.options.D,
      },
    }));

    renderQuestions(questions);
    submitBtn.disabled = false;
    startTimer();
    setStatus(`Random session ready: ${language} ${level} (${questions.length} questions from pool of ${data.total_pool})`);
    renderSubmitHint();
  } catch (error) {
    setStatus(error.message || "Failed to create random session", true);
    quizForm.innerHTML = "";
  }
}

async function submitAnswers(options = {}) {
  const { autoSubmit = false } = options;
  if (!questions.length) {
    setStatus("Load questions before submitting.", true);
    return;
  }

  const unansweredNumbers = getUnansweredQuestionNumbers();
  if (unansweredNumbers.length && !autoSubmit) {
    const message = buildUnansweredMessage(unansweredNumbers);
    window.alert(message);
    setStatus(message, true);
    return;
  }

  const answers = collectAnswers();
  if (answers.length === 0 && !autoSubmit) {
    setStatus("Select at least one answer before submitting", true);
    return;
  }

  if (timerIntervalId) {
    clearInterval(timerIntervalId);
    timerIntervalId = null;
  }
  quizInProgress = false;
  const timerBox = document.getElementById("timer-box");
  if (timerBox) {
    timerBox.style.display = "none";
  }

  try {
    let response;
    if (currentMode === "random") {
      if (!randomSessionId) {
        setStatus("Start a random session first", true);
        return;
      }

      const userId = Number(userIdInput.value) || null;
      response = await fetch(`${API_BASE}/quiz/random-bank/${randomSessionId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, answers }),
      });
    } else {
      const testId = Number(testIdInput.value);
      const userId = Number(userIdInput.value);

      if (!testId || !userId) {
        setStatus("Please enter valid test and user IDs", true);
        return;
      }

      response = await fetch(`${API_BASE}/quiz/tests/${testId}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, answers }),
      });
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to submit quiz");
    }

    saveQuizResult({
      mode: currentMode,
      score: data.score,
      total: data.total,
      unanswered: typeof data.unanswered === "number" ? data.unanswered : unansweredNumbers.length || null,
      test_id: currentMode === "test" ? Number(testIdInput.value) || null : null,
      random_session_id: currentMode === "random" ? randomSessionId : null,
      language: currentMode === "random" ? (languageInput ? languageInput.value : "C") : null,
      level: currentMode === "random" ? (levelInput ? levelInput.value : "Beginner") : null,
      submitted_at: new Date().toISOString(),
    });

    renderResultLink({
      score: data.score,
      total: data.total,
      unanswered: typeof data.unanswered === "number" ? data.unanswered : unansweredNumbers.length || null,
    });
    setStatus("Submission saved successfully. Click View Score below.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

function handleQuestionChange() {
  if (quizInProgress) {
    renderSubmitHint();
  }
}

loadBtn.addEventListener("click", loadQuestions);
submitBtn.addEventListener("click", () => submitAnswers({ autoSubmit: false }));
if (startRandomBtn) {
  startRandomBtn.addEventListener("click", startRandomSession);
}
quizForm.addEventListener("change", handleQuestionChange);

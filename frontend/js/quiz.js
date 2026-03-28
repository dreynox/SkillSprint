const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";

const loadBtn = document.getElementById("load-btn");
const submitBtn = document.getElementById("submit-btn");
const testIdInput = document.getElementById("test-id");
const userIdInput = document.getElementById("user-id");
const statusEl = document.getElementById("status");
const quizForm = document.getElementById("quiz-form");
const resultContainer = document.getElementById("result-container");

let questions = [];

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
      ["A", question.option_a],
      ["B", question.option_b],
      ["C", question.option_c],
      ["D", question.option_d],
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

  try {
    const response = await fetch(`${API_BASE}/quiz/tests/${testId}/questions`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to load questions");
    }

    questions = data;
    if (questions.length === 0) {
      setStatus("No questions found for this test", true);
      quizForm.innerHTML = "";
      return;
    }

    renderQuestions(questions);
    submitBtn.disabled = false;
    setStatus(`Loaded ${questions.length} questions for test ${testId}`);
  } catch (error) {
    setStatus(error.message, true);
    quizForm.innerHTML = "";
  }
}

async function submitAnswers() {
  const testId = Number(testIdInput.value);
  const userId = Number(userIdInput.value);

  if (!testId || !userId) {
    setStatus("Please enter valid test and user IDs", true);
    return;
  }

  const answers = collectAnswers();
  if (answers.length === 0) {
    setStatus("Select at least one answer before submitting", true);
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/quiz/tests/${testId}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, answers }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to submit quiz");
    }

    resultContainer.style.display = "block";
    resultContainer.innerHTML = `<h2>Score: ${data.score} / ${data.total}</h2>`;
    setStatus("Submission saved successfully");
  } catch (error) {
    setStatus(error.message, true);
  }
}

loadBtn.addEventListener("click", loadQuestions);
submitBtn.addEventListener("click", submitAnswers);

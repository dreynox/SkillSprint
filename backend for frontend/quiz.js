const API_BASE = "http://127.0.0.1:8000";
const TEST_ID = 1;      // from your seed
const USER_ID = 101;    // dummy user for now

async function loadQuestions() {
  const res = await fetch(`${API_BASE}/quiz/tests/${TEST_ID}/questions`);
  const questions = await res.json();

  const container = document.getElementById("quiz-container");
  container.innerHTML = "";

  questions.forEach(q => {
    const div = document.createElement("div");
    div.innerHTML = `
      <h3>${q.text}</h3>
      <label><input type="radio" name="q_${q.id}" value="A"> ${q.option_a}</label><br>
      <label><input type="radio" name="q_${q.id}" value="B"> ${q.option_b}</label><br>
      <label><input type="radio" name="q_${q.id}" value="C"> ${q.option_c}</label><br>
      <label><input type="radio" name="q_${q.id}" value="D"> ${q.option_d}</label><br>
      <hr>
    `;
    container.appendChild(div);
  });
}

async function submitQuiz() {
  const resQuestions = await fetch(`${API_BASE}/quiz/tests/${TEST_ID}/questions`);
  const questions = await resQuestions.json();

  const answers = questions.map(q => {
    const selected = document.querySelector(`input[name="q_${q.id}"]:checked`);
    return {
      question_id: q.id,
      selected: selected ? selected.value : ""
    };
  });

  const payload = {
    user_id: USER_ID,
    answers: answers
  };

  const res = await fetch(`${API_BASE}/quiz/tests/${TEST_ID}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();
  document.getElementById("result").innerText =
    `Your score: ${data.score} / ${data.total}`;
}

document.getElementById("submit-btn").addEventListener("click", submitQuiz);

loadQuestions();

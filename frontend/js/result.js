// =========================
// SAMPLE DATA (replace with backend data later)
// =========================
const results = [
  { id: 1, difficulty: "Easy", time: 40, correct: true },
  { id: 2, difficulty: "Easy", time: 55, correct: true },
  { id: 3, difficulty: "Medium", time: 95, correct: false },
  { id: 4, difficulty: "Medium", time: 80, correct: true },
  { id: 5, difficulty: "Hard", time: 190, correct: false },
  { id: 6, difficulty: "Hard", time: 160, correct: true }
];

// =========================
// HELPER FUNCTIONS
// =========================
const formatTime = (seconds) => {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s}s`;
};

const avg = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;

// =========================
// BASIC STATS
// =========================
const times = results.map(r => r.time);
const avgTime = Math.round(avg(times));
const longestTime = Math.max(...times);
const shortestTime = Math.min(...times);

const correctCount = results.filter(r => r.correct).length;
const accuracy = Math.round((correctCount / results.length) * 100);

// =========================
// UPDATE SUMMARY UI
// =========================
document.getElementById("avgTime").textContent = formatTime(avgTime);
document.getElementById("longestTime").textContent = formatTime(longestTime);
document.getElementById("shortestTime").textContent = formatTime(shortestTime);
document.getElementById("accuracy").textContent = `${accuracy}%`;

// =========================
// DIFFICULTY BREAKDOWN
// =========================
const difficulties = ["Easy", "Medium", "Hard"];

difficulties.forEach(level => {
  const filtered = results.filter(r => r.difficulty === level);

  if (filtered.length === 0) return;

  const levelTimes = filtered.map(r => r.time);
  const levelCorrect = filtered.filter(r => r.correct).length;

  document.getElementById(`${level.toLowerCase()}Count`).textContent = filtered.length;
  document.getElementById(`${level.toLowerCase()}Time`).textContent = formatTime(Math.round(avg(levelTimes)));
  document.getElementById(`${level.toLowerCase()}Accuracy`).textContent = `${Math.round((levelCorrect / filtered.length) * 100)}%`;
});

// =========================
// QUESTION TABLE
// =========================
const tableBody = document.getElementById("questionTable");

results.forEach((q, index) => {
  const row = document.createElement("tr");

  row.innerHTML = `
    <td>${index + 1}</td>
    <td>${q.difficulty}</td>
    <td>${formatTime(q.time)}</td>
    <td>${q.correct ? "✔" : "✘"}</td>
  `;

  tableBody.appendChild(row);
});

// =========================
// INSIGHTS ENGINE
// =========================
const insightList = document.getElementById("insightList");

const insights = [];

const hardTime = results.filter(r => r.difficulty === "Hard").reduce((a, b) => a + b.time, 0);
const totalTime = results.reduce((a, b) => a + b.time, 0);

if (hardTime / totalTime > 0.4) {
  insights.push("Hard questions consume most of your time.");
}

if (accuracy < 60) {
  insights.push("Accuracy is low. Focus on fundamentals.");
}

if (longestTime > avgTime * 2) {
  insights.push("Some questions took unusually long to solve.");
}

insights.push("Consistency improves with timed practice.");

insights.forEach(text => {
  const li = document.createElement("li");
  li.textContent = text;
  insightList.appendChild(li);
});
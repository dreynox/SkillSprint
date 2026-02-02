// =========================
// SAMPLE DATA (replace with backend later)
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

const average = (arr) =>
  arr.reduce((sum, val) => sum + val, 0) / arr.length;

// =========================
// GLOBAL STATS
// =========================
const times = results.map(r => r.time);

const avgTime = Math.round(average(times));
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

  document.getElementById(`${level.toLowerCase()}Count`).textContent =
    filtered.length;

  document.getElementById(`${level.toLowerCase()}Time`).textContent =
    formatTime(Math.round(average(levelTimes)));

  document.getElementById(`${level.toLowerCase()}Accuracy`).textContent =
    `${Math.round((levelCorrect / filtered.length) * 100)}%`;
});

// =========================
// QUESTION TABLE
// =========================
const tableBody = document.getElementById("questionTable");

results.forEach((q, index) => {
  const row = document.createElement("tr");

  row.innerHTML = `
    <td>${index + 1}</td>
    <td class="${q.difficulty.toLowerCase()}">${q.difficulty}</td>
    <td>${formatTime(q.time)}</td>
    <td class="${q.correct ? "correct" : "wrong"}">
      ${q.correct ? "✔" : "✘"}
    </td>
  `;

  tableBody.appendChild(row);
});

// =========================
// INSIGHTS ENGINE
// =========================
const insightList = document.getElementById("insightList");
const insights = [];

const totalTime = results.reduce((sum, r) => sum + r.time, 0);
const hardTime = results
  .filter(r => r.difficulty === "Hard")
  .reduce((sum, r) => sum + r.time, 0);

if (accuracy < 60) {
  insights.push("Accuracy is low. Strengthen fundamentals before speed.");
}

if (longestTime > avgTime * 2) {
  insights.push("Some questions took unusually long to solve.");
}

if (hardTime / totalTime > 0.4) {
  insights.push("Hard questions consumed most of your total time.");
}

if (accuracy >= 80) {
  insights.push("Strong accuracy. Maintain consistency under pressure.");
}

insights.push("Timed practice will significantly improve performance.");

insights.forEach(text => {
  const li = document.createElement("li");
  li.textContent = text;
  insightList.appendChild(li);
});

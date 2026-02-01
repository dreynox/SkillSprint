const userProfile = {
  name: "Rayhaan Shaikh",
  role: "First Year CSE · Competitive Programmer",
  avatar: "https://avatars.githubusercontent.com/u/1?v=4",

  stats: {
    contestsWon: 12,
    problemsSolved: 340,
    rating: 1820
  },

  performances: [
    { title: "DSA Sprint #21", difficulty: "Medium", time: "42 min" },
    { title: "Algo Rush", difficulty: "Hard", time: "1 hr 10 min" },
    { title: "Bug Bash", difficulty: "Easy", time: "25 min" }
  ]
};

// Inject profile data
document.getElementById("username").textContent = userProfile.name;
document.getElementById("role").textContent = userProfile.role;
document.getElementById("avatar").src = userProfile.avatar;

// Animated counter
function animateCount(id, target) {
  let count = 0;
  const speed = target / 40;

  const interval = setInterval(() => {
    count += speed;
    if (count >= target) {
      document.getElementById(id).textContent = target;
      clearInterval(interval);
    } else {
      document.getElementById(id).textContent = Math.floor(count);
    }
  }, 25);
}

animateCount("contests", userProfile.stats.contestsWon);
animateCount("problems", userProfile.stats.problemsSolved);
animateCount("rating", userProfile.stats.rating);

// Performance list
const list = document.getElementById("performance-list");

userProfile.performances.forEach((item, index) => {
  const row = document.createElement("div");
  row.className = "row";
  row.style.animation = `fadeUp 0.5s ease ${index * 0.15}s forwards`;
  row.style.opacity = 0;

  const difficultyClass =
    item.difficulty === "Easy" ? "easy" :
    item.difficulty === "Medium" ? "medium" : "hard";

  row.innerHTML = `
    <div>
      <strong>${item.title}</strong><br>
      <small class="${difficultyClass}">Difficulty: ${item.difficulty}</small>
    </div>
    <div class="time">⏱ ${item.time}</div>
  `;

  row.addEventListener("click", () => {
    alert(
      `Challenge: ${item.title}\nDifficulty: ${item.difficulty}\nTime: ${item.time}`
    );
  });

  list.appendChild(row);
});

// Follow button toggle
const followBtn = document.querySelector(".btn-outline");
let following = false;

followBtn.addEventListener("click", () => {
  following = !following;
  followBtn.textContent = following ? "Following ✓" : "Follow";
});

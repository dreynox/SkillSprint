const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("access_token");
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function animateCount(id, target) {
  const element = document.getElementById(id);
  if (!element) {
    return;
  }

  const end = Math.max(0, Number(target) || 0);
  if (end === 0) {
    element.textContent = "0";
    return;
  }

  let count = 0;
  const speed = end / 40;
  const interval = setInterval(() => {
    count += speed;
    if (count >= end) {
      element.textContent = String(end);
      clearInterval(interval);
    } else {
      element.textContent = String(Math.floor(count));
    }
  }, 25);
}

function renderPerformanceRows(stats) {
  const list = document.getElementById("performance-list");
  if (!list) {
    return;
  }

  list.innerHTML = "";
  const rows = [
    {
      title: "Contests Joined",
      difficulty: "Easy",
      time: String(stats.contests_joined || 0),
    },
    {
      title: "Contest Submissions",
      difficulty: "Medium",
      time: String(stats.contest_submissions || 0),
    },
    {
      title: "Quiz Attempts",
      difficulty: "Hard",
      time: String(stats.quiz_attempts || 0),
    },
  ];

  rows.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "row";
    row.style.animation = `fadeUp 0.5s ease ${index * 0.15}s forwards`;
    row.style.opacity = 0;

    const difficultyClass =
      item.difficulty === "Easy"
        ? "easy"
        : item.difficulty === "Medium"
          ? "medium"
          : "hard";

    row.innerHTML = `
      <div>
        <strong>${item.title}</strong><br>
        <small class="${difficultyClass}">Updated from your account history</small>
      </div>
      <div class="time">${item.time}</div>
    `;

    list.appendChild(row);
  });
}

async function loadProfile() {
  const token = getToken();
  if (!token) {
    window.location.href = "../../index.html";
    return;
  }

  try {
    const [profileRes, statsRes] = await Promise.all([
      fetch(`${API_BASE}/users/me`, { headers: authHeaders() }),
      fetch(`${API_BASE}/users/me/stats`, { headers: authHeaders() }),
    ]);

    if (!profileRes.ok || !statsRes.ok) {
      throw new Error("Unable to load profile data");
    }

    const profile = await profileRes.json();
    const stats = await statsRes.json();

    const roleParts = [];
    if (profile.year) {
      roleParts.push(`Year ${profile.year}`);
    }
    if (profile.branch) {
      roleParts.push(profile.branch);
    }
    roleParts.push((profile.role || "student").toUpperCase());

    document.getElementById("username").textContent = profile.name || "Student";
    document.getElementById("role").textContent = roleParts.join(" · ");

    const avatar = document.getElementById("avatar");
    if (avatar) {
      avatar.src = profile.avatar_url || "../images/Rayhaan1.jpeg";
    }

    animateCount("contests", stats.contests_joined || 0);
    animateCount("problems", stats.contest_submissions || 0);
    animateCount("rating", stats.total_quiz_score || 0);
    renderPerformanceRows(stats);

    localStorage.setItem("user", JSON.stringify(profile));
  } catch (_error) {
    document.getElementById("username").textContent = "Profile unavailable";
    document.getElementById("role").textContent = "Please login again";
  }
}

const followBtn = document.querySelector(".btn-outline");
if (followBtn) {
  let following = false;
  followBtn.addEventListener("click", () => {
    following = !following;
    followBtn.textContent = following ? "Following" : "Follow";
  });
}

const messageBtn = document.getElementById("messageBtn");
if (messageBtn) {
  messageBtn.addEventListener("click", () => {
    window.location.href = "message.html";
  });
}

loadProfile();

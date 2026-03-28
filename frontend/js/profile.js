const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";
const DEFAULT_AVATAR = "../images/default-avatar.svg";

function getToken() {
  return localStorage.getItem("access_token");
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function getCachedUser() {
  try {
    return JSON.parse(localStorage.getItem("user") || "null");
  } catch (_err) {
    return null;
  }
}

function resolveAvatarUrl(avatarUrl) {
  if (!avatarUrl) {
    return DEFAULT_AVATAR;
  }

  if (avatarUrl.startsWith("http://") || avatarUrl.startsWith("https://")) {
    return avatarUrl;
  }

  if (avatarUrl.startsWith("/")) {
    return `${API_BASE}${avatarUrl}`;
  }

  return avatarUrl;
}

function setUploadStatus(message, isError) {
  const element = document.getElementById("avatarUploadStatus");
  if (!element) {
    return;
  }
  element.textContent = message || "";
  element.style.color = isError ? "#f87171" : "#9bf7c4";
}

async function uploadAvatar(file) {
  if (!file) {
    return;
  }

  const token = getToken();
  if (!token) {
    window.location.href = "../../index.html";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  setUploadStatus("Uploading image...", false);

  try {
    const response = await fetch(`${API_BASE}/users/me/avatar`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to upload image");
    }

    const avatar = document.getElementById("avatar");
    if (avatar) {
      avatar.src = resolveAvatarUrl(data.avatar_url);
    }

    const cachedUser = JSON.parse(localStorage.getItem("user") || "{}");
    localStorage.setItem("user", JSON.stringify({ ...cachedUser, ...data }));
    setUploadStatus("Profile image updated.", false);
  } catch (error) {
    setUploadStatus(error.message || "Failed to upload image", true);
  }
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

    if (!profileRes.ok) {
      throw new Error("Unable to load profile data");
    }

    const profile = await profileRes.json();
    const stats = statsRes.ok
      ? await statsRes.json()
      : {
          contests_joined: 0,
          contest_submissions: 0,
          quiz_attempts: 0,
          total_quiz_score: 0,
        };

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
      avatar.src = resolveAvatarUrl(profile.avatar_url);
    }

    animateCount("contests", stats.contests_joined || 0);
    animateCount("problems", stats.contest_submissions || 0);
    animateCount("rating", stats.total_quiz_score || 0);
    renderPerformanceRows(stats);

    localStorage.setItem("user", JSON.stringify(profile));
  } catch (_error) {
    const cachedUser = getCachedUser();
    if (cachedUser && cachedUser.name) {
      document.getElementById("username").textContent = cachedUser.name;

      const roleParts = [];
      if (cachedUser.year) {
        roleParts.push(`Year ${cachedUser.year}`);
      }
      if (cachedUser.branch) {
        roleParts.push(cachedUser.branch);
      }
      roleParts.push((cachedUser.role || "student").toUpperCase());
      document.getElementById("role").textContent = roleParts.join(" · ");
    } else {
      document.getElementById("username").textContent = "Profile unavailable";
      document.getElementById("role").textContent = "Please login again";
    }

    const avatar = document.getElementById("avatar");
    if (avatar) {
      avatar.src = DEFAULT_AVATAR;
    }
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

const avatarUploadInput = document.getElementById("avatarUpload");
if (avatarUploadInput) {
  avatarUploadInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    uploadAvatar(file);
  });
}

loadProfile();

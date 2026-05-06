const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";
const DEFAULT_AVATAR = "../images/default-avatar.svg";
const LIVE_REFRESH_MS = 30000;

let autoRefreshTimer = null;
let countdownTimer = null;
let autoRefreshSecondsRemaining = Math.floor(LIVE_REFRESH_MS / 1000);
let lastUpdatedMessage = "Loading latest results...";

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-IN").format(Number(value) || 0);
}

function resolveAvatar(avatarUrl) {
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

function setStatus(message, isError = false) {
  const element = document.getElementById("leaderboardStatus");
  if (!element) {
    return;
  }

  element.textContent = message || "";
  element.style.color = isError ? "#f87171" : "var(--muted)";
}

function setUpdatedLabel(message) {
  const element = document.getElementById("leaderboardUpdated");
  if (!element) {
    return;
  }

  element.textContent = message;
}

function renderUpdatedLabel() {
  const suffix = ` | Auto refresh in ${autoRefreshSecondsRemaining}s`;
  setUpdatedLabel(`${lastUpdatedMessage}${suffix}`);
}

function activateLeaderboardView(viewName) {
  const podium = document.getElementById("leaderboardPodium");
  const listWrap = document.getElementById("leaderboardListWrap");
  const isPodium = viewName === "podium";

  if (podium) {
    podium.classList.toggle("ux-hidden", !isPodium);
  }
  if (listWrap) {
    listWrap.classList.toggle("ux-hidden", isPodium);
  }

  const podiumTab = document.getElementById("podiumTab");
  const fullRankTab = document.getElementById("fullRankTab");
  if (podiumTab) {
    podiumTab.classList.toggle("active", isPodium);
    podiumTab.setAttribute("aria-selected", String(isPodium));
  }
  if (fullRankTab) {
    fullRankTab.classList.toggle("active", !isPodium);
    fullRankTab.setAttribute("aria-selected", String(!isPodium));
  }

  setStatus(isPodium ? "Podium view active." : "Full rankings view active.");
}

function badgeClass(badge) {
  return `badge badge-${String(badge || "").toLowerCase()}`;
}

function renderPodium(rows) {
  const podium = document.getElementById("leaderboardPodium");
  if (!podium) {
    return;
  }

  if (!rows.length) {
    podium.innerHTML = '<div class="leaderboard-empty">No ranked users yet. Be the first to earn points.</div>';
    return;
  }

  const podiumOrder = [1, 0, 2];
  const topThree = rows.slice(0, 3);

  podium.innerHTML = podiumOrder
    .map((index) => topThree[index])
    .filter(Boolean)
    .map((row) => {
      const branchLabel = [row.branch, row.year ? `Year ${row.year}` : ""].filter(Boolean).join(" · ");
      return `
        <article class="podium-card rank-${escapeHtml(String(row.rank))}">
          <span class="podium-crown">#${formatNumber(row.rank)}</span>
          <div class="podium-identity">
            <img class="podium-avatar" src="${escapeHtml(resolveAvatar(row.avatar_url))}" alt="${escapeHtml(row.name)} avatar" loading="lazy">
            <div class="podium-name">
              <strong>${escapeHtml(row.name)}</strong>
              <span>${escapeHtml(branchLabel || "No branch listed")}</span>
            </div>
          </div>
          <div class="podium-meta">${row.rank === 1 ? "Top rank" : `Rank ${formatNumber(row.rank)}`}</div>
          <div class="podium-stats">
            <div class="podium-stat">
              <span class="podium-stat-label">Quiz Attempts</span>
              <span class="podium-stat-value">${formatNumber(row.quiz_attempts)}</span>
            </div>
            <div class="podium-stat">
              <span class="podium-stat-label">Contest Activity</span>
              <span class="podium-stat-value">${formatNumber(Number(row.contests_joined || 0) + Number(row.contest_submissions || 0))}</span>
            </div>
            <div class="podium-stat">
              <span class="podium-stat-label">Total Points</span>
              <span class="podium-stat-value">${formatNumber(row.total_points)}</span>
            </div>
            <div class="podium-stat">
              <span class="podium-stat-label">Badge</span>
              <span class="podium-stat-value podium-badge"><span class="badge ${escapeHtml(badgeClass(row.badge))}">${escapeHtml(row.badge)}</span></span>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderList(rows) {
  const list = document.getElementById("leaderboardList");
  if (!list) {
    return;
  }

  if (!rows.length) {
    list.innerHTML = '<li class="leaderboard-empty">No more ranked users to display.</li>';
    return;
  }

  list.innerHTML = rows
    .map((row) => {
      const branchLabel = [row.branch, row.year ? `Year ${row.year}` : ""].filter(Boolean).join(" · ");
      return `
        <li class="leaderboard-list-item">
          <div class="leaderboard-rank">${formatNumber(row.rank)}</div>
          <div class="leaderboard-user">
            <img class="leaderboard-avatar" src="${escapeHtml(resolveAvatar(row.avatar_url))}" alt="${escapeHtml(row.name)} avatar" loading="lazy">
            <div class="leaderboard-name">
              <strong>${escapeHtml(row.name)}</strong>
              <span>${escapeHtml(branchLabel || "No branch listed")}</span>
            </div>
          </div>
          <div class="leaderboard-list-stats">
            <div class="leaderboard-list-stat"><strong>${formatNumber(row.total_points)}</strong> pts</div>
            <div class="leaderboard-list-stat"><strong>${formatNumber(row.quiz_attempts)}</strong> quiz</div>
            <div class="leaderboard-list-stat"><span class="badge ${escapeHtml(badgeClass(row.badge))}">${escapeHtml(row.badge)}</span></div>
          </div>
        </li>
      `;
    })
    .join("");
}

async function loadLeaderboard(options = {}) {
  const { silent = false } = options;
  const podium = document.getElementById("leaderboardPodium");
  const list = document.getElementById("leaderboardList");
  if (!silent && podium) {
    podium.innerHTML = '<div class="leaderboard-empty">Loading podium...</div>';
  }
  if (!silent && list) {
    list.innerHTML = '<li class="leaderboard-empty">Loading rankings...</li>';
  }

  if (!silent) {
    setStatus("Fetching the latest leaderboard standings...");
  }

  try {
    const response = await fetch(`${API_BASE}/users/leaderboard?limit=50`);
    if (!response.ok) {
      throw new Error(`Leaderboard request failed with status ${response.status}`);
    }

    const rows = await response.json();
    renderPodium(rows);
    renderList(rows.slice(3));
    setStatus(rows.length ? `Showing ${rows.length} ranked students.` : "No ranked users yet.");
    lastUpdatedMessage = `Updated ${new Date().toLocaleString()}`;
    autoRefreshSecondsRemaining = Math.floor(LIVE_REFRESH_MS / 1000);
    renderUpdatedLabel();
  } catch (error) {
    if (podium) {
      podium.innerHTML = '<div class="leaderboard-empty">Could not load leaderboard data right now.</div>';
    }
    if (list) {
      list.innerHTML = '<li class="leaderboard-empty">Could not load leaderboard data right now.</li>';
    }
    setStatus("Leaderboard data could not be loaded. Try refreshing the page.", true);
    lastUpdatedMessage = "Update failed";
    autoRefreshSecondsRemaining = Math.floor(LIVE_REFRESH_MS / 1000);
    renderUpdatedLabel();
    console.error(error);
  }
}

function startLiveRefresh() {
  if (!autoRefreshTimer) {
    autoRefreshTimer = window.setInterval(() => {
      loadLeaderboard({ silent: true });
    }, LIVE_REFRESH_MS);
  }

  if (!countdownTimer) {
    countdownTimer = window.setInterval(() => {
      autoRefreshSecondsRemaining = Math.max(0, autoRefreshSecondsRemaining - 1);
      renderUpdatedLabel();
    }, 1000);
  }
}

function bindControls() {
  const refreshButton = document.getElementById("refreshLeaderboard");
  if (refreshButton && !refreshButton.dataset.bound) {
    refreshButton.dataset.bound = "true";
    refreshButton.addEventListener("click", () => {
      loadLeaderboard();
    });
  }

  const podiumTab = document.getElementById("podiumTab");
  const fullRankTab = document.getElementById("fullRankTab");

  if (podiumTab && !podiumTab.dataset.bound) {
    podiumTab.dataset.bound = "true";
    podiumTab.addEventListener("click", () => activateLeaderboardView("podium"));
  }

  if (fullRankTab && !fullRankTab.dataset.bound) {
    fullRankTab.dataset.bound = "true";
    fullRankTab.addEventListener("click", () => activateLeaderboardView("full"));
  }
}

bindControls();
activateLeaderboardView("podium");
startLiveRefresh();
loadLeaderboard();
const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";
const DEFAULT_AVATAR = "../images/default-avatar.svg";
let currentProfile = null;

function getToken() {
  const raw = localStorage.getItem("access_token") || localStorage.getItem("token") || "";
  const cleaned = String(raw).trim().replace(/^"|"$/g, "");

  if (!cleaned || cleaned === "undefined" || cleaned === "null") {
    return "";
  }

  return cleaned;
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function clearSessionAndGoLogin() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  sessionStorage.removeItem("access_token");
  sessionStorage.removeItem("token");
  window.location.href = "../../index.html";
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

function setDeleteStatus(message, isError) {
  const element = document.getElementById("deleteAccountStatus");
  if (!element) {
    return;
  }
  element.textContent = message || "";
  element.style.color = isError ? "#fca5a5" : "#fecaca";
}

function setDetailsStatus(message, isError) {
  const element = document.getElementById("detailsUpdateStatus");
  if (!element) {
    return;
  }
  element.textContent = message || "";
  element.style.color = isError ? "#f87171" : "#9bf7c4";
}

function buildRoleText(profile) {
  const roleParts = [];
  if (profile.year) {
    roleParts.push(`Year ${profile.year}`);
  }
  if (profile.branch) {
    roleParts.push(profile.branch);
  }
  roleParts.push((profile.role || "student").toUpperCase());
  return roleParts.join(" · ");
}

function renderProfileDetails(profile) {
  const set = (id, value) => {
    const element = document.getElementById(id);
    if (!element) {
      return;
    }
    element.textContent = value ? String(value) : "-";
  };

  // Required order: SRN, PRN, YEAR, BRANCH, DIVISION, ROLL NO
  set("detailSrn", profile.srn);
  set("detailPrn", profile.prn);
  set("detailYear", profile.year);
  set("detailBranch", profile.branch);
  set("detailDivision", profile.division);
  set("detailRollNo", profile.roll_no);
}

function fillDetailsForm(profile) {
  const set = (id, value) => {
    const element = document.getElementById(id);
    if (!element) {
      return;
    }
    element.value = value === null || value === undefined ? "" : String(value);
  };

  set("editName", profile.name);
  set("editSrn", profile.srn);
  set("editPrn", profile.prn);
  set("editYear", profile.year);
  set("editBranch", profile.branch);
  set("editDivision", profile.division);
  set("editRollNo", profile.roll_no);
}

async function saveProfileDetails() {
  const token = getToken();
  if (!token) {
    clearSessionAndGoLogin();
    return;
  }

  const getValue = (id) => {
    const element = document.getElementById(id);
    return element ? element.value.trim() : "";
  };

  const yearText = getValue("editYear");
  const yearValue = yearText ? Number(yearText) : null;
  if (yearText && (!Number.isInteger(yearValue) || yearValue < 1 || yearValue > 8)) {
    setDetailsStatus("Year must be a number between 1 and 8.", true);
    return;
  }

  const payload = {
    name: getValue("editName") || null,
    srn: getValue("editSrn") || null,
    prn: getValue("editPrn") || null,
    year: yearValue,
    branch: getValue("editBranch") || null,
    division: getValue("editDivision") || null,
    roll_no: getValue("editRollNo") || null,
  };

  setDetailsStatus("Saving profile details...", false);

  try {
    const response = await fetch(`${API_BASE}/users/me`, {
      method: "PATCH",
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (response.status === 401) {
      setDetailsStatus("Session expired. Please login again.", true);
      setTimeout(() => {
        clearSessionAndGoLogin();
      }, 700);
      return;
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to update profile details");
    }

    currentProfile = data;
    document.getElementById("username").textContent = data.name || "Student";
    document.getElementById("role").textContent = buildRoleText(data);
    renderProfileDetails(data);
    fillDetailsForm(data);
    localStorage.setItem("user", JSON.stringify(data));

    const detailsEditForm = document.getElementById("detailsEditForm");
    if (detailsEditForm) {
      detailsEditForm.hidden = true;
    }

    setDetailsStatus("Profile details updated.", false);
  } catch (error) {
    setDetailsStatus(error.message || "Failed to update profile details", true);
  }
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

    if (response.status === 401) {
      setUploadStatus("Session expired. Please login again.", true);
      setTimeout(() => {
        clearSessionAndGoLogin();
      }, 700);
      return;
    }

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
    clearSessionAndGoLogin();
    return;
  }

  try {
    const [profileRes, statsRes] = await Promise.all([
      fetch(`${API_BASE}/users/me`, { headers: authHeaders() }),
      fetch(`${API_BASE}/users/me/stats`, { headers: authHeaders() }),
    ]);

    if (profileRes.status === 401) {
      clearSessionAndGoLogin();
      return;
    }

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

    currentProfile = profile;

    document.getElementById("username").textContent = profile.name || "Student";
    document.getElementById("role").textContent = buildRoleText(profile);

    const avatar = document.getElementById("avatar");
    if (avatar) {
      avatar.src = resolveAvatarUrl(profile.avatar_url);
    }

    animateCount("contests", stats.contests_joined || 0);
    animateCount("problems", stats.contest_submissions || 0);
    animateCount("rating", stats.total_quiz_score || 0);
    renderPerformanceRows(stats);
    renderProfileDetails(profile);
    fillDetailsForm(profile);

    localStorage.setItem("user", JSON.stringify(profile));
  } catch (_error) {
    const cachedUser = getCachedUser();
    if (cachedUser && cachedUser.name) {
      currentProfile = cachedUser;
      document.getElementById("username").textContent = cachedUser.name;
      document.getElementById("role").textContent = buildRoleText(cachedUser);
      renderProfileDetails(cachedUser);
      fillDetailsForm(cachedUser);
    } else {
      currentProfile = {};
      document.getElementById("username").textContent = "Profile unavailable";
      document.getElementById("role").textContent = "Please login again";
      renderProfileDetails({});
      fillDetailsForm({});
    }

    const avatar = document.getElementById("avatar");
    if (avatar) {
      avatar.src = DEFAULT_AVATAR;
    }
  }
}

async function deleteMyAccount() {
  const token = getToken();
  if (!token) {
    clearSessionAndGoLogin();
    return;
  }

  const firstConfirm = window.confirm(
    "Delete your account permanently? This cannot be undone and will remove your profile and activity history."
  );
  if (!firstConfirm) {
    return;
  }

  const secondConfirm = window.confirm("Are you absolutely sure you want to delete your account?");
  if (!secondConfirm) {
    return;
  }

  const typedConfirmation = window.prompt('Type DELETE to permanently remove your account:');
  if (typedConfirmation === null) {
    setDeleteStatus("Account deletion canceled.", true);
    return;
  }

  if (typedConfirmation.trim() !== "DELETE") {
    setDeleteStatus('Confirmation text did not match. Type exactly DELETE to proceed.', true);
    return;
  }

  setDeleteStatus("Deleting account...", false);

  try {
    const response = await fetch(`${API_BASE}/users/me`, {
      method: "DELETE",
      headers: authHeaders(),
    });

    if (response.status === 401) {
      setDeleteStatus("Session expired. Please login again.", true);
      setTimeout(() => {
        clearSessionAndGoLogin();
      }, 700);
      return;
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to delete account");
    }

    setDeleteStatus("Account deleted. Redirecting...", false);
    setTimeout(() => {
      clearSessionAndGoLogin();
    }, 500);
  } catch (error) {
    setDeleteStatus(error.message || "Failed to delete account", true);
  }
}

const followBtn = document.getElementById("followBtn");
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
const avatarCaptureInput = document.getElementById("avatarCapture");
const avatarEditBtn = document.getElementById("avatarEditBtn");
const avatarEditMenu = document.getElementById("avatarEditMenu");
const chooseFolderBtn = document.getElementById("chooseFolderBtn");
const takePhotoBtn = document.getElementById("takePhotoBtn");

function closeAvatarMenu() {
  if (!avatarEditMenu || !avatarEditBtn) {
    return;
  }
  avatarEditMenu.hidden = true;
  avatarEditBtn.setAttribute("aria-expanded", "false");
}

function toggleAvatarMenu() {
  if (!avatarEditMenu || !avatarEditBtn) {
    return;
  }

  const nextHidden = !avatarEditMenu.hidden;
  avatarEditMenu.hidden = nextHidden;
  avatarEditBtn.setAttribute("aria-expanded", String(!nextHidden));
}

if (avatarEditBtn) {
  avatarEditBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleAvatarMenu();
  });
}

if (avatarEditMenu) {
  avatarEditMenu.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

if (chooseFolderBtn && avatarUploadInput) {
  chooseFolderBtn.addEventListener("click", () => {
    closeAvatarMenu();
    avatarUploadInput.click();
  });
}

if (takePhotoBtn && avatarCaptureInput) {
  takePhotoBtn.addEventListener("click", () => {
    closeAvatarMenu();
    avatarCaptureInput.click();
  });
}

if (avatarUploadInput) {
  avatarUploadInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    uploadAvatar(file);
    event.target.value = "";
  });
}

if (avatarCaptureInput) {
  avatarCaptureInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    uploadAvatar(file);
    event.target.value = "";
  });
}

const profileDetailsPanel = document.getElementById("profileDetailsPanel");
if (profileDetailsPanel) {
  profileDetailsPanel.style.display = "block";
}

const detailsEditBtn = document.getElementById("detailsEditBtn");
const detailsEditMenu = document.getElementById("detailsEditMenu");
const openDetailsFormBtn = document.getElementById("openDetailsFormBtn");
const detailsEditForm = document.getElementById("detailsEditForm");
const cancelDetailsBtn = document.getElementById("cancelDetailsBtn");

function closeDetailsMenu() {
  if (!detailsEditMenu || !detailsEditBtn) {
    return;
  }
  detailsEditMenu.hidden = true;
  detailsEditBtn.setAttribute("aria-expanded", "false");
}

function toggleDetailsMenu() {
  if (!detailsEditMenu || !detailsEditBtn) {
    return;
  }

  const nextHidden = !detailsEditMenu.hidden;
  detailsEditMenu.hidden = nextHidden;
  detailsEditBtn.setAttribute("aria-expanded", String(!nextHidden));
}

if (detailsEditBtn) {
  detailsEditBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleDetailsMenu();
  });
}

if (detailsEditMenu) {
  detailsEditMenu.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

if (openDetailsFormBtn && detailsEditForm) {
  openDetailsFormBtn.addEventListener("click", () => {
    closeDetailsMenu();
    fillDetailsForm(currentProfile || {});
    detailsEditForm.hidden = false;
    setDetailsStatus("", false);
  });
}

if (cancelDetailsBtn && detailsEditForm) {
  cancelDetailsBtn.addEventListener("click", () => {
    detailsEditForm.hidden = true;
    fillDetailsForm(currentProfile || {});
    setDetailsStatus("", false);
  });
}

if (detailsEditForm) {
  detailsEditForm.addEventListener("submit", (event) => {
    event.preventDefault();
    saveProfileDetails();
  });
}

document.addEventListener("click", () => {
  closeAvatarMenu();
  closeDetailsMenu();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeAvatarMenu();
    closeDetailsMenu();
  }
});

const deleteAccountBtn = document.getElementById("deleteAccountBtn");
if (deleteAccountBtn) {
  deleteAccountBtn.addEventListener("click", () => {
    deleteMyAccount();
  });
}

loadProfile();

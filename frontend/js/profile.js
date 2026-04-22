const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";
const DEFAULT_AVATAR = "../images/default-avatar.svg";
const AVATAR_MAX_BYTES = 1024 * 1024;
let currentProfile = null;
let isViewingOwnProfile = true;
let pendingAvatarFile = null;
let pendingAvatarPreviewUrl = "";
let allUsers = [];

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

function syncTopbarProfileMenu(profile, isOwnProfile) {
  const menu = document.getElementById("profileMenu");
  const button = document.getElementById("profileMenuBtn");
  const avatar = document.getElementById("topbarAvatar");
  const editBtn = document.getElementById("editProfileMenuBtn");

  if (avatar) {
    const cachedUser = getCachedUser();
    const source = cachedUser || (isOwnProfile ? profile : null);
    avatar.src = resolveAvatarUrl(source?.avatar_url);
  }

  if (editBtn) {
    editBtn.style.display = isOwnProfile ? "flex" : "none";
  }

  if (button && menu) {
    button.setAttribute("aria-expanded", "false");
    menu.classList.remove("open");
  }
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

function setAvatarModalStatus(message, isError) {
  const element = document.getElementById("avatarModalStatus");
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

function closeDetailsModal() {
  const detailsEditModal = document.getElementById("detailsEditModal");
  const detailsEditBtn = document.getElementById("detailsEditBtn");

  if (!detailsEditModal || !detailsEditBtn) {
    return;
  }

  detailsEditModal.hidden = true;
  detailsEditBtn.setAttribute("aria-expanded", "false");
}

function openDetailsModal() {
  const detailsEditModal = document.getElementById("detailsEditModal");
  const detailsEditBtn = document.getElementById("detailsEditBtn");

  if (!detailsEditModal || !detailsEditBtn) {
    return;
  }

  fillDetailsForm(currentProfile || {});
  setDetailsStatus("", false);
  detailsEditModal.hidden = false;
  detailsEditBtn.setAttribute("aria-expanded", "true");
}

function buildRoleText(profile) {
  const roleParts = [];
  if (String(profile.role || "").toLowerCase() === "admin") {
    if (profile.domain) {
      roleParts.push(profile.domain);
    }
    if (profile.subject) {
      roleParts.push(profile.subject);
    }
    if (profile.year) {
      roleParts.push(`Year ${profile.year}`);
    }
    roleParts.push("ADMIN");
    return roleParts.join(" · ");
  }

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

  // Required order: SRN, PRN, YEAR, BRANCH, DIVISION, ROLL NO, DOMAIN, SUBJECT
  set("detailSrn", profile.srn);
  set("detailPrn", profile.prn);
  set("detailYear", profile.year);
  set("detailBranch", profile.branch);
  set("detailDivision", profile.division);
  set("detailRollNo", profile.roll_no);
  set("detailDomain", profile.domain);
  set("detailSubject", profile.subject);
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
  set("editDomain", profile.domain);
  set("editSubject", profile.subject);
}

function openPeopleModal() {
  const modal = document.getElementById("peopleModal");
  const searchInput = document.getElementById("peopleSearchInput");
  if (!modal) {
    return;
  }

  modal.hidden = false;
  if (searchInput) {
    searchInput.value = "";
  }
  loadPeopleList();
}

function closePeopleModal() {
  const modal = document.getElementById("peopleModal");
  if (!modal) {
    return;
  }

  modal.hidden = true;
}

function renderPeopleList(users) {
  const peopleList = document.getElementById("peopleList");
  const currentUser = getCachedUser();

  if (!peopleList) {
    return;
  }

  peopleList.innerHTML = "";

  if (!users.length) {
    peopleList.innerHTML = '<div class="people-empty">No matching users found.</div>';
    return;
  }

  users.forEach((user) => {
    const row = document.createElement("div");
    row.className = "people-item";

    const isMe = user.id === currentUser?.id;
    row.innerHTML = `
      <div class="people-meta">
        <div class="people-name">${user.name || `User ${user.id}`}</div>
        <div class="people-email">${user.email || "-"}${isMe ? " • You" : ""}</div>
      </div>
      <button class="btn btn-outline" type="button">${isMe ? "Open" : "View Profile"}</button>
    `;

    const actionBtn = row.querySelector("button");
    actionBtn?.addEventListener("click", () => {
      if (isMe) {
        window.location.href = "profile.html";
      } else {
        window.location.href = `profile.html?user_id=${user.id}`;
      }
    });

    peopleList.appendChild(row);
  });
}

async function loadPeopleList() {
  const peopleList = document.getElementById("peopleList");
  const searchInput = document.getElementById("peopleSearchInput");

  if (!peopleList) {
    return;
  }

  peopleList.innerHTML = '<div class="people-empty">Loading users...</div>';

  try {
    const response = await fetch(`${API_BASE}/users`, {
      headers: authHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to load users");
    }

    allUsers = await response.json();
    renderPeopleList(allUsers);

    if (searchInput && !searchInput.dataset.bound) {
      searchInput.dataset.bound = "true";
      searchInput.addEventListener("input", () => {
        const query = searchInput.value.trim().toLowerCase();
        if (!query) {
          renderPeopleList(allUsers);
          return;
        }

        const filtered = allUsers.filter((user) => {
          const name = String(user.name || "").toLowerCase();
          const email = String(user.email || "").toLowerCase();
          return name.includes(query) || email.includes(query);
        });

        renderPeopleList(filtered);
      });
    }
  } catch (error) {
    peopleList.innerHTML = `<div class="people-empty">${error.message || "Could not load users."}</div>`;
  }
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
    domain: getValue("editDomain") || null,
    subject: getValue("editSubject") || null,
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

    setDetailsStatus("Profile details updated.", false);
    setTimeout(() => {
      closeDetailsModal();
    }, 350);
  } catch (error) {
    setDetailsStatus(error.message || "Failed to update profile details", true);
  }
}

async function uploadAvatar(file) {
  if (!file) {
    return false;
  }

  const token = getToken();
  if (!token) {
    window.location.href = "../../index.html";
    return false;
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
      return false;
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
    const nextUser = { ...cachedUser, ...data };
    currentProfile = nextUser;
    localStorage.setItem("user", JSON.stringify(nextUser));
    syncTopbarProfileMenu(nextUser, isViewingOwnProfile);
    setUploadStatus("Profile image updated.", false);
    return true;
  } catch (error) {
    setUploadStatus(error.message || "Failed to upload image", true);
    return false;
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
    // Check if viewing another user's profile via URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const viewingUserId = urlParams.get("user_id");
    const currentUser = getCachedUser();
    
    let profileRes, statsRes;
    
    if (viewingUserId && parseInt(viewingUserId) !== currentUser?.id) {
      // Load another user's profile
      profileRes = await fetch(`${API_BASE}/users/${viewingUserId}`, { headers: authHeaders() });
      statsRes = await fetch(`${API_BASE}/users/${viewingUserId}/stats`, { headers: authHeaders() });
    } else {
      // Load current user's profile
      profileRes = await fetch(`${API_BASE}/users/me`, { headers: authHeaders() });
      statsRes = await fetch(`${API_BASE}/users/me/stats`, { headers: authHeaders() });
    }

    if (profileRes.status === 401) {
      clearSessionAndGoLogin();
      return;
    }

    if (!profileRes.ok) {
      throw new Error("Unable to load profile data");
    }

    const profile = await profileRes.json();
    const stats = statsRes?.ok
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
    
    // Show/hide edit UI based on whether viewing own or other user's profile
    const isOwnProfile = !viewingUserId || (parseInt(viewingUserId) === currentUser?.id);
    isViewingOwnProfile = isOwnProfile;
    const detailsPanel = document.getElementById("profileDetailsPanel");
    const detailsEditBtn = document.getElementById("detailsEditBtn");
    const avatarEditBtn = document.getElementById("avatarEditBtn");
    const deleteAccountBtn = document.getElementById("deleteAccountBtn");
    const dangerZone = document.querySelector(".danger-zone");
    
    if (detailsPanel) {
      detailsPanel.style.display = isOwnProfile ? "block" : "none";
    }
    if (avatarEditBtn) {
      avatarEditBtn.style.display = isOwnProfile ? "block" : "none";
    }
    if (dangerZone) {
      dangerZone.style.display = isOwnProfile ? "block" : "none";
    }
    
    // Update follow button visibility and state
    const followBtn = document.getElementById("followBtn");
    const messageBtn = document.getElementById("messageBtn");
    if (followBtn) {
      if (isOwnProfile) {
        followBtn.style.display = "none";
      } else {
        followBtn.style.display = "block";
        // Check if currently following this user
        checkFollowingStatus(profile.id, followBtn);
      }
    }

    if (messageBtn) {
      messageBtn.style.display = isOwnProfile ? "none" : "block";
    }

    const browsePeopleBtnEl = document.getElementById("browsePeopleBtn");
    if (browsePeopleBtnEl) {
      browsePeopleBtnEl.style.display = isOwnProfile ? "inline-block" : "none";
    }

    const myProfileBtnEl = document.getElementById("myProfileBtn");
    if (myProfileBtnEl) {
      myProfileBtnEl.style.display = isOwnProfile ? "inline-block" : "none";
    }
    
    if (!isOwnProfile) {
      fillDetailsForm(profile);
    } else {
      fillDetailsForm(profile);
    }

    // Never overwrite the logged-in user cache when viewing someone else's profile.
    if (isOwnProfile) {
      localStorage.setItem("user", JSON.stringify(profile));
    }

    syncTopbarProfileMenu(isOwnProfile ? profile : currentUser, isOwnProfile);
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

    syncTopbarProfileMenu(cachedUser || null, Boolean(cachedUser));
  }
}

async function checkFollowingStatus(userId, followBtn) {
  try {
    const response = await fetch(`${API_BASE}/users/${userId}/is-following`, {
      headers: authHeaders()
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.is_following) {
        followBtn.textContent = "Following";
        followBtn.dataset.following = "true";
      } else {
        followBtn.textContent = "Follow";
        followBtn.dataset.following = "false";
      }
    }
  } catch (error) {
    console.error("Failed to check follow status:", error);
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
  followBtn.addEventListener("click", async function () {
    if (!currentProfile || !currentProfile.id) {
      alert("Profile not loaded yet");
      return;
    }

    const userId = currentProfile.id;
    const isFollowing = followBtn.dataset.following === "true";
    
    try {
      const method = isFollowing ? "DELETE" : "POST";
      const response = await fetch(`${API_BASE}/users/${userId}/follow`, {
        method: method,
        headers: authHeaders()
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update follow status");
      }

      // Toggle the button state
      const newState = !isFollowing;
      followBtn.textContent = newState ? "Following" : "Follow";
      followBtn.dataset.following = newState ? "true" : "false";
    } catch (error) {
      alert("Error: " + error.message);
    }
  });
}

const messageBtn = document.getElementById("messageBtn");
if (messageBtn) {
  messageBtn.addEventListener("click", () => {
    if (!isViewingOwnProfile && currentProfile && currentProfile.id) {
      // Open message page with this profile preselected as recipient.
      sessionStorage.setItem("selectedRecipientId", String(currentProfile.id));
    }
    window.location.href = "message.html";
  });
}

const avatarUploadInput = document.getElementById("avatarUpload");
const avatarCaptureInput = document.getElementById("avatarCapture");
const avatarEditBtn = document.getElementById("avatarEditBtn");
const avatarUploadModal = document.getElementById("avatarUploadModal");
const avatarModalCloseBtn = document.getElementById("avatarModalCloseBtn");
const avatarModalCancelBtn = document.getElementById("avatarModalCancelBtn");
const avatarModalSaveBtn = document.getElementById("avatarModalSaveBtn");
const avatarModalPreview = document.getElementById("avatarModalPreview");
const avatarDropZone = document.getElementById("avatarDropZone");
const avatarBrowseBtn = document.getElementById("avatarBrowseBtn");
const avatarModalTakePhotoBtn = document.getElementById("avatarModalTakePhotoBtn");
const avatarFileChip = document.getElementById("avatarFileChip");
const avatarFileName = document.getElementById("avatarFileName");
const avatarFileClearBtn = document.getElementById("avatarFileClearBtn");
const profileMenu = document.getElementById("profileMenu");
const profileMenuBtn = document.getElementById("profileMenuBtn");
const editProfileMenuBtn = document.getElementById("editProfileMenuBtn");
const topbarLogoutBtn = document.getElementById("topbarLogoutBtn");

function syncAvatarPreviewToCurrent() {
  if (!avatarModalPreview) {
    return;
  }

  const avatar = document.getElementById("avatar");
  avatarModalPreview.src = avatar ? avatar.src : DEFAULT_AVATAR;
}

function updateAvatarSaveState() {
  if (avatarModalSaveBtn) {
    avatarModalSaveBtn.disabled = !pendingAvatarFile;
  }
}

function clearPendingAvatar(resetStatus) {
  if (pendingAvatarPreviewUrl) {
    URL.revokeObjectURL(pendingAvatarPreviewUrl);
    pendingAvatarPreviewUrl = "";
  }

  pendingAvatarFile = null;

  if (avatarFileChip) {
    avatarFileChip.hidden = true;
  }

  if (avatarFileName) {
    avatarFileName.textContent = "";
  }

  syncAvatarPreviewToCurrent();
  updateAvatarSaveState();

  if (resetStatus) {
    setAvatarModalStatus("", false);
  }
}

function openAvatarModal() {
  if (!avatarUploadModal || !avatarEditBtn) {
    return;
  }

  clearPendingAvatar(true);
  avatarUploadModal.hidden = false;
  avatarEditBtn.setAttribute("aria-expanded", "true");
}

function closeAvatarModal() {
  if (!avatarUploadModal || !avatarEditBtn) {
    return;
  }

  avatarUploadModal.hidden = true;
  avatarEditBtn.setAttribute("aria-expanded", "false");
  clearPendingAvatar(true);
}

function setPendingAvatarFile(file) {
  if (!file) {
    return;
  }

  if (!file.type || !file.type.startsWith("image/")) {
    setAvatarModalStatus("Only image files are supported.", true);
    return;
  }

  if (file.size > AVATAR_MAX_BYTES) {
    setAvatarModalStatus("Image must be 1 MB or smaller.", true);
    return;
  }

  if (pendingAvatarPreviewUrl) {
    URL.revokeObjectURL(pendingAvatarPreviewUrl);
    pendingAvatarPreviewUrl = "";
  }

  pendingAvatarFile = file;
  pendingAvatarPreviewUrl = URL.createObjectURL(file);

  if (avatarModalPreview) {
    avatarModalPreview.src = pendingAvatarPreviewUrl;
  }

  if (avatarFileChip && avatarFileName) {
    avatarFileChip.hidden = false;
    avatarFileName.textContent = file.name;
  }

  updateAvatarSaveState();
  setAvatarModalStatus("Image ready. Click Save to update your profile photo.", false);
}

if (avatarEditBtn) {
  avatarEditBtn.addEventListener("click", () => {
    openAvatarModal();
  });
}

if (avatarModalCloseBtn) {
  avatarModalCloseBtn.addEventListener("click", () => {
    closeAvatarModal();
  });
}

if (avatarModalCancelBtn) {
  avatarModalCancelBtn.addEventListener("click", () => {
    closeAvatarModal();
  });
}

if (avatarBrowseBtn && avatarUploadInput) {
  avatarBrowseBtn.addEventListener("click", () => {
    avatarUploadInput.click();
  });
}

if (avatarModalTakePhotoBtn && avatarCaptureInput) {
  avatarModalTakePhotoBtn.addEventListener("click", () => {
    avatarCaptureInput.click();
  });
}

if (avatarUploadInput) {
  avatarUploadInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    setPendingAvatarFile(file);
    event.target.value = "";
  });
}

if (avatarCaptureInput) {
  avatarCaptureInput.addEventListener("change", (event) => {
    const [file] = event.target.files || [];
    setPendingAvatarFile(file);
    event.target.value = "";
  });
}

if (avatarFileClearBtn) {
  avatarFileClearBtn.addEventListener("click", () => {
    clearPendingAvatar(true);
  });
}

if (avatarDropZone) {
  avatarDropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    avatarDropZone.classList.add("is-dragover");
  });

  avatarDropZone.addEventListener("dragleave", () => {
    avatarDropZone.classList.remove("is-dragover");
  });

  avatarDropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    avatarDropZone.classList.remove("is-dragover");
    const [file] = event.dataTransfer?.files || [];
    setPendingAvatarFile(file);
  });
}

if (avatarModalSaveBtn) {
  avatarModalSaveBtn.addEventListener("click", async () => {
    if (!pendingAvatarFile) {
      setAvatarModalStatus("Please choose an image first.", true);
      return;
    }

    avatarModalSaveBtn.disabled = true;
    setAvatarModalStatus("Uploading image...", false);
    const saved = await uploadAvatar(pendingAvatarFile);
    if (saved) {
      closeAvatarModal();
    } else {
      updateAvatarSaveState();
      setAvatarModalStatus("Upload failed. Please try again.", true);
    }
  });
}

if (profileMenuBtn && profileMenu) {
  profileMenuBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = profileMenu.classList.toggle("open");
    profileMenuBtn.setAttribute("aria-expanded", String(isOpen));
  });

  document.addEventListener("click", (event) => {
    if (!profileMenu.contains(event.target)) {
      profileMenu.classList.remove("open");
      profileMenuBtn.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      profileMenu.classList.remove("open");
      profileMenuBtn.setAttribute("aria-expanded", "false");
    }
  });
}

if (editProfileMenuBtn) {
  editProfileMenuBtn.addEventListener("click", () => {
    if (!isViewingOwnProfile) {
      return;
    }

    openDetailsModal();
    if (profileMenu) {
      profileMenu.classList.remove("open");
    }
    if (profileMenuBtn) {
      profileMenuBtn.setAttribute("aria-expanded", "false");
    }
  });
}

if (topbarLogoutBtn) {
  topbarLogoutBtn.addEventListener("click", () => {
    clearSessionAndGoLogin();
  });
}

const profileDetailsPanel = document.getElementById("profileDetailsPanel");
if (profileDetailsPanel) {
  profileDetailsPanel.style.display = "block";
}

const detailsEditBtn = document.getElementById("detailsEditBtn");
const detailsEditModal = document.getElementById("detailsEditModal");
const detailsModalCloseBtn = document.getElementById("detailsModalCloseBtn");
const detailsEditForm = document.getElementById("detailsEditForm");
const cancelDetailsBtn = document.getElementById("cancelDetailsBtn");

if (detailsEditBtn) {
  detailsEditBtn.addEventListener("click", () => {
    openDetailsModal();
  });
}

if (detailsModalCloseBtn) {
  detailsModalCloseBtn.addEventListener("click", () => {
    closeDetailsModal();
  });
}

if (cancelDetailsBtn && detailsEditForm) {
  cancelDetailsBtn.addEventListener("click", () => {
    closeDetailsModal();
  });
}

if (detailsEditForm) {
  detailsEditForm.addEventListener("submit", (event) => {
    event.preventDefault();
    saveProfileDetails();
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeAvatarModal();
    closeDetailsModal();
    closePeopleModal();
  }
});

if (avatarUploadModal) {
  avatarUploadModal.addEventListener("click", (event) => {
    if (event.target === avatarUploadModal) {
      closeAvatarModal();
    }
  });
}

if (detailsEditModal) {
  detailsEditModal.addEventListener("click", (event) => {
    if (event.target === detailsEditModal) {
      closeDetailsModal();
    }
  });
}

const deleteAccountBtn = document.getElementById("deleteAccountBtn");
if (deleteAccountBtn) {
  deleteAccountBtn.addEventListener("click", () => {
    deleteMyAccount();
  });
}

const browsePeopleBtn = document.getElementById("browsePeopleBtn");
if (browsePeopleBtn) {
  browsePeopleBtn.addEventListener("click", () => {
    openPeopleModal();
  });
}

const myProfileBtn = document.getElementById("myProfileBtn");
if (myProfileBtn) {
  myProfileBtn.addEventListener("click", () => {
    window.location.href = "profile.html";
  });
}

const peopleModal = document.getElementById("peopleModal");
const peopleModalCloseBtn = document.getElementById("peopleModalCloseBtn");

if (peopleModalCloseBtn) {
  peopleModalCloseBtn.addEventListener("click", () => {
    closePeopleModal();
  });
}

if (peopleModal) {
  peopleModal.addEventListener("click", (event) => {
    if (event.target === peopleModal) {
      closePeopleModal();
    }
  });
}

loadProfile();

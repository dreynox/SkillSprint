// Get token with robust fallback
function getToken() {
    const raw = localStorage.getItem("access_token") || localStorage.getItem("token") || "";
    const cleaned = String(raw).trim().replace(/^"|"$/g, "");
    return cleaned && cleaned !== "undefined" && cleaned !== "null" ? cleaned : "";
}

// Check if user is logged in
function checkAuth() {
    const token = getToken();
    const user = localStorage.getItem("user");

    if (!token || !user) {
        window.location.href = "../../index.html";
        return;
    }

    const userData = JSON.parse(user);
    document.getElementById("userName").textContent = `Welcome, ${userData.name}`;
    document.getElementById("profileName").textContent = userData.name;
    document.getElementById("profileEmail").textContent = userData.email;
    document.getElementById("profileRole").textContent = userData.role.toUpperCase();
}

// Show section
function showSection(sectionId, event) {
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    
    document.getElementById(sectionId).classList.add("active");
    if (event && event.target) {
        const navItem = event.target.closest(".nav-item");
        if (navItem) {
            navItem.classList.add("active");
        }
    }
}

// Logout
function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "../../index.html";
}

// Run on page load
checkAuth();

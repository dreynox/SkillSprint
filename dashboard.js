// Check if user is logged in
function checkAuth() {
    const token = localStorage.getItem("access_token");
    const user = localStorage.getItem("user");

    if (!token || !user) {
        window.location.href = "login.html";
        return;
    }

    const userData = JSON.parse(user);
    document.getElementById("userName").textContent = `Welcome, ${userData.name}`;
    document.getElementById("profileName").textContent = userData.name;
    document.getElementById("profileEmail").textContent = userData.email;
    document.getElementById("profileRole").textContent = userData.role.toUpperCase();
}

// Show section
function showSection(sectionId) {
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    
    document.getElementById(sectionId).classList.add("active");
    event.target.closest(".nav-item").classList.add("active");
}

// Logout
function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "login.html";
}

// Run on page load
checkAuth();

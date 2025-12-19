const API_URL = "http://localhost:8000"; // Change this to your backend URL

document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    // Clear previous errors
    clearErrors();

    // Basic validation
    if (!email || !password) {
        showError("generalError", "Please fill in all fields");
        return;
    }

    // Disable button
    const submitBtn = document.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.textContent = "Logging in...";

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (response.ok) {
            // Store token
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));

            // Redirect based on role
            if (data.user.role === "admin") {
                window.location.href = "admin-dashboard.html";
            } else {
                window.location.href = "student-dashboard.html";
            }
        } else {
            showError("generalError", data.detail || "Invalid email or password");
        }
    } catch (error) {
        showError("generalError", "Connection error. Please try again.");
        console.error("Error:", error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Log In";
    }
});

function showError(elementId, message) {
    document.getElementById(elementId).textContent = message;
}

function clearErrors() {
    document.querySelectorAll(".error-message").forEach((el) => {
        el.textContent = "";
    });
}

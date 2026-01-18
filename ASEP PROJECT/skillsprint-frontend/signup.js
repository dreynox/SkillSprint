const API_BASE_URL = "https://skillsprint-muv2.onrender.com";

document.getElementById("signupForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const year = document.getElementById("year").value;
    const branch = document.getElementById("branch").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    clearErrors();

    // Validation
    if (!name || !email || !password || !confirmPassword) {
        showError("generalError", "Please fill in all required fields");
        return;
    }

    if (password.length < 6) {
        showError("passwordError", "Password must be at least 6 characters");
        return;
    }

    if (password !== confirmPassword) {
        showError("confirmPasswordError", "Passwords do not match");
        return;
    }

    const submitBtn = document.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating account...";

    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name,
                email,
                password,
                year: year ? parseInt(year) : null,
                branch: branch || null,
            }),
        });

        const data = await response.json();

        if (response.ok) {
            // Store token and redirect
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("user", JSON.stringify(data.user));
            window.location.href = "login.html";
        } else {
            showError("generalError", data.detail || "Sign up failed");
        }
    } catch (error) {
        showError("generalError", "Connection error. Please try again.");
        console.error("Error:", error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign Up";
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

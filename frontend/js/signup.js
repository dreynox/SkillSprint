// Detect local vs deployed environment
const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL = isDev
    ? `http://${window.location.hostname}:8000`
    : "https://skillsprint-muv2.onrender.com";

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
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
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
            window.location.href = "../../index.html";
        } else {
            showError("generalError", formatApiError(data));
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

function formatApiError(data) {
    if (!data) return "Sign up failed";

    const detail = data.detail;

    if (typeof detail === "string") {
        return detail;
    }

    // FastAPI validation errors often come as an array of objects.
    if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0];
        if (first && typeof first === "object") {
            const field = Array.isArray(first.loc) ? first.loc[first.loc.length - 1] : "field";
            const message = first.msg || "Invalid value";
            return `${field}: ${message}`;
        }
        return String(detail[0]);
    }

    if (detail && typeof detail === "object") {
        return detail.message || JSON.stringify(detail);
    }

    return "Sign up failed";
}

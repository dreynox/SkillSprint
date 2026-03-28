const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
const API_BASE_URL = isDev
  ? `http://${window.location.hostname}:8000`
  : "https://skillsprint-muv2.onrender.com";

document.getElementById("adminSignupForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  clearErrors();

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

  const submitBtn = document.getElementById("signupBtn");
  const submitLabel = submitBtn ? submitBtn.querySelector("span") : null;
  submitBtn.disabled = true;
  if (submitLabel) {
    submitLabel.textContent = "CREATING ACCOUNT...";
  }

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
        role: "admin",
      }),
    });

    const data = await response.json();

    if (response.ok) {
      const token = data.token || data.access_token;
      if (!token) {
        throw new Error("Signup succeeded but token was missing in response.");
      }
      localStorage.setItem("access_token", token);
      localStorage.setItem("user", JSON.stringify(data.user));
      window.location.href = "admin-login.html";
    } else {
      showError("generalError", formatApiError(data));
    }
  } catch (error) {
    showError("generalError", "Connection error. Please try again.");
    console.error("Error:", error);
  } finally {
    submitBtn.disabled = false;
    if (submitLabel) {
      submitLabel.textContent = "CREATE ADMIN";
    }
  }
});

function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) {
    el.textContent = message;
  }
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

const glow = document.querySelector(".cursor-glow");

document.addEventListener("mousemove", (e) => {
  if (!glow) return;
  glow.style.left = e.clientX + "px";
  glow.style.top = e.clientY + "px";
});

const canvas = document.getElementById("matrix");
if (canvas) {
  const ctx = canvas.getContext("2d");

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resizeCanvas();

  const letters = "01SYSTEMHACKACCESSGRANTED";
  const fontSize = 14;
  let columns = Math.floor(canvas.width / fontSize);
  let drops = Array.from({ length: columns }).fill(1);

  function drawMatrix() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#00ff88";
    ctx.font = fontSize + "px monospace";

    drops.forEach((y, i) => {
      const text = letters[Math.floor(Math.random() * letters.length)];
      ctx.fillText(text, i * fontSize, y * fontSize);

      if (y * fontSize > canvas.height && Math.random() > 0.975) {
        drops[i] = 0;
      }
      drops[i]++;
    });
  }

  setInterval(drawMatrix, 33);

  window.addEventListener("resize", () => {
    resizeCanvas();
    columns = Math.floor(canvas.width / fontSize);
    drops = Array.from({ length: columns }).fill(1);
  });
}

const togglePassword = document.getElementById("togglePassword");
const passwordInput = document.getElementById("password");

if (togglePassword && passwordInput) {
  togglePassword.addEventListener("click", () => {
    const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
    passwordInput.setAttribute("type", type);
    togglePassword.textContent = type === "password" ? "👁" : "🙈";
  });
}

const toggleConfirmPassword = document.getElementById("toggleConfirmPassword");
const confirmPasswordInput = document.getElementById("confirmPassword");

if (toggleConfirmPassword && confirmPasswordInput) {
  toggleConfirmPassword.addEventListener("click", () => {
    const type = confirmPasswordInput.getAttribute("type") === "password" ? "text" : "password";
    confirmPasswordInput.setAttribute("type", type);
    toggleConfirmPassword.textContent = type === "password" ? "👁" : "🙈";
  });
}

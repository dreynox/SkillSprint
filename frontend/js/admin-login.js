const API_BASE = window.API_BASE_URL || "https://skillsprint-backend-i8q6.onrender.com";

const form = document.getElementById("adminLoginForm");
const loginBtn = document.getElementById("loginBtn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value.trim();
  const passwordInput = document.getElementById("password");
  const password = passwordInput.value.trim();

  clearErrors();

  if (!email || !password) {
    showError("generalError", "Please fill in all fields");
    return;
  }

  loginBtn.disabled = true;
  loginBtn.classList.add("loading");
  const span = loginBtn.querySelector("span");
  if (span) {
    span.textContent = "AUTHENTICATING...";
  }

  try {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Invalid email or password");
    }

    if (!data.user || data.user.role !== "admin") {
      throw new Error("This portal is for admin accounts only.");
    }

    const token = data.token || data.access_token;
    if (!token) {
      throw new Error("Login succeeded but token was missing in response.");
    }
    localStorage.setItem("access_token", token);
    if (data.user) {
      localStorage.setItem("user", JSON.stringify(data.user));
    }

    if (span) {
      span.textContent = "ACCESS GRANTED";
    }
    loginBtn.style.background = "#00ff88";
    loginBtn.style.color = "#000";

    setTimeout(() => {
      window.location.href = "admin-dashboard.html";
    }, 1200);
  } catch (error) {
    loginBtn.classList.remove("loading");
    loginBtn.disabled = false;
    if (span) {
      span.textContent = "ADMIN AUTHENTICATE";
    }
    showError("generalError", error.message || "Connection error. Please try again.");
    console.error("Admin login error:", error);
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

const glow = document.querySelector(".cursor-glow");

document.addEventListener("mousemove", (e) => {
  if (!glow) {
    return;
  }
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
    const type =
      passwordInput.getAttribute("type") === "password" ? "text" : "password";
    passwordInput.setAttribute("type", type);
    togglePassword.textContent = type === "password" ? "👁" : "🙈";
  });
}

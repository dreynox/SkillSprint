const API_BASE_URL = "https://skillsprint-muv2.onrender.com";

/* =========================
   LOGIN FORM HANDLER
========================= */
const form = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value.trim();
  const passwordInput = document.getElementById("password");
  const password = passwordInput.value.trim();

  // Clear previous errors
  clearErrors();

  // Basic validation
  if (!email || !password) {
    showError("generalError", "Please fill in all fields");
    return;
  }

  // Button loading state
  loginBtn.disabled = true;
  loginBtn.classList.add("loading");
  const span = loginBtn.querySelector("span");
  if (span) span.textContent = "AUTHENTICATING...";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
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

    // Store token + user
    localStorage.setItem("access_token", data.access_token);
    if (data.user) {
      localStorage.setItem("user", JSON.stringify(data.user));
    }

    if (span) span.textContent = "ACCESS GRANTED";
    loginBtn.style.background = "#00ff88";
    loginBtn.style.color = "#000";

    // Redirect (adjust if you later add a separate admin page)
    setTimeout(() => {
      window.location.href = "dashboard.html";
    }, 1200);
  } catch (error) {
    loginBtn.classList.remove("loading");
    loginBtn.disabled = false;
    if (span) span.textContent = "AUTHENTICATE";
    showError("generalError", error.message || "Connection error. Please try again.");
    console.error("Login error:", error);
  }
});

/* =========================
   ERROR HELPERS
========================= */
function showError(elementId, message) {
  const el = document.getElementById(elementId);
  if (el) el.textContent = message;
}

function clearErrors() {
  document.querySelectorAll(".error-message").forEach((el) => {
    el.textContent = "";
  });
}

/* =========================
   NEON CURSOR GLOW
========================= */
const glow = document.querySelector(".cursor-glow");

document.addEventListener("mousemove", (e) => {
  if (!glow) return;
  glow.style.left = e.clientX + "px";
  glow.style.top = e.clientY + "px";
});

/* =========================
   MATRIX BACKGROUND
========================= */
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

/* =========================
   TOGGLE PASSWORD VISIBILITY
========================= */
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

const RENDER_API_URL = "https://skillsprint-backend-i8q6.onrender.com";
const storedApiOverride = localStorage.getItem("SKILLSPRINT_API_BASE_URL");
const isLegacyOverride = storedApiOverride && storedApiOverride.indexOf("skillsprint-muv2.onrender.com") !== -1;
if (isLegacyOverride) {
  localStorage.removeItem("SKILLSPRINT_API_BASE_URL");
}
const API_BASE_URL = (storedApiOverride && !isLegacyOverride)
  ? storedApiOverride
  : (window.API_BASE_URL || RENDER_API_URL);

const requestOtpForm = document.getElementById("requestOtpForm");
const verifyOtpForm = document.getElementById("verifyOtpForm");
const otpMessage = document.getElementById("otpMessage");

function showError(message) {
  const errorEl = document.getElementById("generalError");
  if (errorEl) {
    errorEl.textContent = message || "";
  }
}

requestOtpForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");

  const email = document.getElementById("email").value.trim().toLowerCase();
  if (!email) {
    showError("Please enter your email");
    return;
  }

  const btn = document.getElementById("requestOtpBtn");
  const label = btn.querySelector("span");
  btn.disabled = true;
  label.textContent = "SENDING OTP...";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password/request-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Failed to send OTP");
    }

    otpMessage.textContent = data.message || `A 6-digit OTP(One-Time-Password) has been sent to you email adrress "${email}", Please verify it within 5 minutes before it expires`;
    verifyOtpForm.style.display = "block";
  } catch (error) {
    showError(error.message || "Failed to send OTP");
  } finally {
    btn.disabled = false;
    label.textContent = "SEND OTP";
  }
});

verifyOtpForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  showError("");

  const email = document.getElementById("email").value.trim().toLowerCase();
  const otp = document.getElementById("otp").value.trim();
  const newPassword = document.getElementById("newPassword").value;
  const confirmNewPassword = document.getElementById("confirmNewPassword").value;

  if (!otp || otp.length !== 6) {
    showError("Please enter a valid 6-digit OTP");
    return;
  }

  if (!newPassword || newPassword.length < 6) {
    showError("New password must be at least 6 characters");
    return;
  }

  if (newPassword !== confirmNewPassword) {
    showError("Passwords do not match");
    return;
  }

  const btn = document.getElementById("verifyOtpBtn");
  const label = btn.querySelector("span");
  btn.disabled = true;
  label.textContent = "VERIFYING...";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password/verify-otp`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        otp,
        new_password: newPassword,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "OTP verification failed");
    }

    otpMessage.textContent = data.message || "Password reset successful. Redirecting to login...";
    setTimeout(() => {
      window.location.href = "../../index.html";
    }, 1200);
  } catch (error) {
    showError(error.message || "OTP verification failed");
  } finally {
    btn.disabled = false;
    label.textContent = "VERIFY OTP & RESET";
  }
});

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

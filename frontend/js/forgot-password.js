const API_BASE = window.API_BASE_URL || "https://skillsprint-backend-i8q6.onrender.com";

const requestOtpForm = document.getElementById("requestOtpForm");
const verifyOtpForm = document.getElementById("verifyOtpForm");
const otpMessage = document.getElementById("otpMessage");
const forgotStatus = document.getElementById("forgotStatus");
let otpCooldownTimer = null;

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
    setStatus("Enter a valid email to request OTP.");
    return;
  }

  const btn = document.getElementById("requestOtpBtn");
  const label = btn.querySelector("span");
  btn.disabled = true;
  label.textContent = "SENDING OTP...";
  setStatus("Sending OTP...");

  try {
    const response = await fetch(`${API_BASE}/auth/forgot-password/request-otp`, {
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
    setStatus("OTP sent. Check your email and enter the code.");
    startOtpCooldown(btn, label, 30);
  } catch (error) {
    showError(error.message || "Failed to send OTP");
    setStatus("Could not send OTP. Try again.");
  } finally {
    if (!otpCooldownTimer) {
      btn.disabled = false;
      label.textContent = "SEND OTP";
    }
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
    setStatus("OTP should be exactly 6 digits.");
    return;
  }

  if (!newPassword || newPassword.length < 6) {
    showError("New password must be at least 6 characters");
    setStatus("Use at least 6 characters for the new password.");
    return;
  }

  if (newPassword !== confirmNewPassword) {
    showError("Passwords do not match");
    setStatus("Passwords must match.");
    return;
  }

  const btn = document.getElementById("verifyOtpBtn");
  const label = btn.querySelector("span");
  btn.disabled = true;
  label.textContent = "VERIFYING...";
  setStatus("Verifying OTP and resetting password...");

  try {
    const response = await fetch(`${API_BASE}/auth/forgot-password/verify-otp`, {
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
    setStatus("Password reset successful. Redirecting...");
    setTimeout(() => {
      window.location.href = "../../index.html";
    }, 1200);
  } catch (error) {
    showError(error.message || "OTP verification failed");
    setStatus("OTP verification failed.");
  } finally {
    btn.disabled = false;
    label.textContent = "VERIFY OTP & RESET";
  }
});

const otpInput = document.getElementById("otp");
if (otpInput) {
  otpInput.addEventListener("input", () => {
    otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 6);
  });
}

function setStatus(message) {
  if (forgotStatus) {
    forgotStatus.textContent = message;
  }
  if (window.SkillSprintUX && typeof window.SkillSprintUX.showStatus === "function") {
    window.SkillSprintUX.showStatus(message, "info");
  }
}

function startOtpCooldown(button, labelEl, seconds) {
  if (otpCooldownTimer) {
    clearInterval(otpCooldownTimer);
    otpCooldownTimer = null;
  }

  let remaining = seconds;
  button.disabled = true;
  labelEl.textContent = `RESEND IN ${remaining}s`;

  otpCooldownTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(otpCooldownTimer);
      otpCooldownTimer = null;
      button.disabled = false;
      labelEl.textContent = "SEND OTP";
      return;
    }
    labelEl.textContent = `RESEND IN ${remaining}s`;
  }, 1000);
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

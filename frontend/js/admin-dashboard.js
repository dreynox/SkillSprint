(function () {
  const API_BASE = window.API_BASE_URL || "http://127.0.0.1:8000";

  const glow = document.querySelector(".cursor-glow");
  document.addEventListener("mousemove", function (event) {
    if (!glow) {
      return;
    }

    glow.style.left = event.clientX + "px";
    glow.style.top = event.clientY + "px";
  });

  const matrixCanvas = document.getElementById("matrix");
  if (matrixCanvas) {
    const matrixContext = matrixCanvas.getContext("2d");

    function resizeCanvas() {
      matrixCanvas.width = window.innerWidth;
      matrixCanvas.height = window.innerHeight;
    }

    resizeCanvas();

    const letters = "01SYSTEMHACKACCESSGRANTED";
    const fontSize = 14;
    let columns = Math.floor(matrixCanvas.width / fontSize);
    let drops = Array.from({ length: columns }).fill(1);

    function drawMatrix() {
      matrixContext.fillStyle = "rgba(0, 0, 0, 0.08)";
      matrixContext.fillRect(0, 0, matrixCanvas.width, matrixCanvas.height);

      matrixContext.fillStyle = "#00ff88";
      matrixContext.font = fontSize + "px monospace";

      drops.forEach(function (y, index) {
        const text = letters[Math.floor(Math.random() * letters.length)];
        matrixContext.fillText(text, index * fontSize, y * fontSize);

        if (y * fontSize > matrixCanvas.height && Math.random() > 0.975) {
          drops[index] = 0;
        }

        drops[index] += 1;
      });
    }

    setInterval(drawMatrix, 33);

    window.addEventListener("resize", function () {
      resizeCanvas();
      columns = Math.floor(matrixCanvas.width / fontSize);
      drops = Array.from({ length: columns }).fill(1);
    });
  }

  function parseUser() {
    try {
      return JSON.parse(localStorage.getItem("user") || "null");
    } catch (_err) {
      return null;
    }
  }

  function requireAdmin() {
    const token = localStorage.getItem("access_token");
    const user = parseUser();

    if (!token || !user) {
      window.location.href = "../../index.html";
      return null;
    }

    if (user.role !== "admin") {
      window.location.href = "student-dashboard.html";
      return null;
    }

    return user;
  }

  function formatDateText(value) {
    if (!value) {
      return "TBD";
    }
    return new Date(value).toLocaleString();
  }

  function renderFeed(contests, hackathons) {
    const feed = document.getElementById("adminFeed");
    if (!feed) {
      return;
    }

    const rows = [];

    contests.forEach(function (contest) {
      rows.push(
        "<div class=\"list-item\"><div><b>[Contest] " +
          escapeHtml(contest.name) +
          "</b><span>" +
          formatDateText(contest.start_time) +
          " to " +
          formatDateText(contest.end_time) +
          "</span></div><span class=\"badge\">" +
          (contest.is_active ? "Active" : "Draft") +
          "</span></div>"
      );
    });

    hackathons.forEach(function (hackathon) {
      rows.push(
        "<div class=\"list-item\"><div><b>[Hackathon] " +
          escapeHtml(hackathon.title) +
          "</b><span>" +
          formatDateText(hackathon.start_time) +
          " to " +
          formatDateText(hackathon.end_time) +
          "</span></div><span class=\"badge\">" +
          (hackathon.is_active ? "Active" : "Draft") +
          "</span></div>"
      );
    });

    if (!rows.length) {
      feed.innerHTML = "<div class=\"list-item\"><div><b>No posted events yet</b><span>Create your first contest or hackathon from above.</span></div><span class=\"badge\">0</span></div>";
      return;
    }

    feed.innerHTML = rows.join("");
  }

  function escapeHtml(str) {
    if (!str) {
      return "";
    }
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function setStatus(id, message, isError) {
    const element = document.getElementById(id);
    if (!element) {
      return;
    }
    element.textContent = message;
    element.style.color = isError ? "#f87171" : "#9bf7c4";
  }

  function toIsoOrNull(value) {
    if (!value) {
      return null;
    }
    return new Date(value).toISOString();
  }

  async function loadFeed() {
    try {
      const contestResponse = await fetch(API_BASE + "/contests");
      const contests = contestResponse.ok ? await contestResponse.json() : [];

      const hackathonResponse = await fetch(API_BASE + "/hackathons");
      const hackathons = hackathonResponse.ok ? await hackathonResponse.json() : [];

      renderFeed(Array.isArray(contests) ? contests : [], Array.isArray(hackathons) ? hackathons : []);
    } catch (_error) {
      renderFeed([], []);
    }
  }

  async function createContest() {
    const name = document.getElementById("contestName").value.trim();
    const description = document.getElementById("contestDescription").value.trim();
    const startTime = document.getElementById("contestStart").value;
    const endTime = document.getElementById("contestEnd").value;
    const isActive = document.getElementById("contestActive").checked;

    if (!name) {
      setStatus("contestStatus", "Contest name is required.", true);
      return;
    }

    setStatus("contestStatus", "Posting contest...", false);

    try {
      const response = await fetch(API_BASE + "/contests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name,
          description: description || null,
          start_time: toIsoOrNull(startTime),
          end_time: toIsoOrNull(endTime),
          is_active: isActive,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to create contest");
      }

      setStatus("contestStatus", "Contest posted successfully.", false);
      document.getElementById("contestName").value = "";
      document.getElementById("contestDescription").value = "";
      document.getElementById("contestStart").value = "";
      document.getElementById("contestEnd").value = "";
      await loadFeed();
    } catch (error) {
      setStatus("contestStatus", error.message || "Unable to create contest", true);
    }
  }

  async function createHackathon() {
    const title = document.getElementById("hackathonTitle").value.trim();
    const description = document.getElementById("hackathonDescription").value.trim();
    const startTime = document.getElementById("hackathonStart").value;
    const endTime = document.getElementById("hackathonEnd").value;
    const isActive = document.getElementById("hackathonActive").checked;

    if (!title) {
      setStatus("hackathonStatus", "Hackathon title is required.", true);
      return;
    }

    setStatus("hackathonStatus", "Posting hackathon...", false);

    try {
      const response = await fetch(API_BASE + "/hackathons", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title,
          description: description || null,
          start_time: toIsoOrNull(startTime),
          end_time: toIsoOrNull(endTime),
          is_active: isActive,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to create hackathon");
      }

      setStatus("hackathonStatus", "Hackathon posted successfully.", false);
      document.getElementById("hackathonTitle").value = "";
      document.getElementById("hackathonDescription").value = "";
      document.getElementById("hackathonStart").value = "";
      document.getElementById("hackathonEnd").value = "";
      await loadFeed();
    } catch (error) {
      setStatus("hackathonStatus", error.message || "Unable to create hackathon", true);
    }
  }

  document.getElementById("createContestBtn").addEventListener("click", createContest);
  document.getElementById("createHackathonBtn").addEventListener("click", createHackathon);
  document.getElementById("logoutBtn").addEventListener("click", function () {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "../../index.html";
  });

  const user = requireAdmin();
  if (!user) {
    return;
  }

  document.getElementById("welcomeText").textContent = "Welcome, " + user.name;
  document.getElementById("heroTitle").textContent = "Hello " + user.name + ", publish new events";

  loadFeed();
})();

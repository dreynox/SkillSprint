(function () {
  if (window.API_BASE_URL) {
    return;
  }

  const hostname = window.location.hostname;
  const renderApiUrl = "https://skillsprint-backend-i8q6.onrender.com";
  const apiHost = hostname || "127.0.0.1";
  const localApiUrl = "http://" + apiHost + ":8000";
  const explicitOverride = localStorage.getItem("SKILLSPRINT_API_BASE_URL");
  const usesLegacyApi = explicitOverride && explicitOverride.indexOf("skillsprint-muv2.onrender.com") !== -1;
  const sanitizedOverride = usesLegacyApi ? null : explicitOverride;
  if (usesLegacyApi) {
    localStorage.removeItem("SKILLSPRINT_API_BASE_URL");
  }

  // Default to Render; keep localhost reachable through override when needed.
  window.API_BASE_URL = sanitizedOverride || renderApiUrl;
  window.SKILLSPRINT_LOCAL_API_URL = localApiUrl;
})();

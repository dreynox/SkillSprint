(function () {
  if (window.API_BASE_URL) {
    return;
  }

  const hostname = window.location.hostname;
  const renderApiUrl = "https://skillsprint-backend-i8q6.onrender.com";
  const isLocalhost = !hostname || hostname === "localhost" || hostname === "127.0.0.1";
  const isPrivateIp = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(hostname);
  const isDevHost = isLocalhost || isPrivateIp;
  const apiHost = hostname || "127.0.0.1";
  const localApiUrl = "http://" + apiHost + ":8000";

  // Deterministic selection: local frontend -> local backend, otherwise Render.
  window.API_BASE_URL = isDevHost ? localApiUrl : renderApiUrl;
  window.SKILLSPRINT_LOCAL_API_URL = localApiUrl;
})();

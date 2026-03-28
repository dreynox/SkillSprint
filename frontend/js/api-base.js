(function () {
  if (window.API_BASE_URL) {
    return;
  }

  const isDev = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  window.API_BASE_URL = isDev
    ? "http://" + window.location.hostname + ":8000"
    : "https://skillsprint-muv2.onrender.com";
})();

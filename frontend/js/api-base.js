(function () {
  if (window.API_BASE_URL) {
    return;
  }

  const hostname = window.location.hostname;
  const isLocalhost = !hostname || hostname === "localhost" || hostname === "127.0.0.1";
  const isPrivateIp = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/.test(hostname);
  const isDev = isLocalhost || isPrivateIp;
  const apiHost = hostname || "127.0.0.1";
  window.API_BASE_URL = isDev
    ? "http://" + apiHost + ":8000"
    : "https://skillsprint-muv2.onrender.com";
})();

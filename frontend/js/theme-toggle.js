(function () {
    const STORAGE_KEY = "skillsprint-theme";
    const root = document.documentElement;
    const toggle = document.getElementById("theme-toggle");

    function getSavedTheme() {
        return localStorage.getItem(STORAGE_KEY) || "dark";
    }

    function applyTheme(theme) {
        root.setAttribute("data-theme", theme);

        if (!toggle) {
            return;
        }

        const isLight = theme === "light";

        toggle.setAttribute(
            "aria-label",
            isLight
                ? "Switch to dark mode"
                : "Switch to light mode"
        );

        toggle.setAttribute(
            "aria-pressed",
            String(isLight)
        );

        const icon = toggle.querySelector(".theme-icon");

        if (icon) {
            icon.textContent = isLight ? "🌙" : "☀️";
        }
    }

    // Apply saved theme on page load
    const initialTheme = getSavedTheme();
    applyTheme(initialTheme);

    // Handle theme toggle
    if (toggle) {
        toggle.addEventListener("click", function () {
            const currentTheme =
                root.getAttribute("data-theme") || "dark";

            const nextTheme =
                currentTheme === "dark"
                    ? "light"
                    : "dark";

            localStorage.setItem(STORAGE_KEY, nextTheme);

            applyTheme(nextTheme);
        });
    }
})();
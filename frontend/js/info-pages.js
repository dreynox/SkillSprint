(function () {
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
})();

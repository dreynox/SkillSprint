const canvas = document.getElementById("neon-bg");
const ctx = canvas.getContext("2d");

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener("resize", resize);
resize();

// Line class
class NeonLine {
  constructor() {
    this.reset();
  }

  reset() {
    const side = Math.floor(Math.random() * 4);

    // Start from screen edges
    if (side === 0) {
      this.x = 0;
      this.y = Math.random() * canvas.height;
      this.dx = 1;
      this.dy = 0;
    } else if (side === 1) {
      this.x = canvas.width;
      this.y = Math.random() * canvas.height;
      this.dx = -1;
      this.dy = 0;
    } else if (side === 2) {
      this.x = Math.random() * canvas.width;
      this.y = 0;
      this.dx = 0;
      this.dy = 1;
    } else {
      this.x = Math.random() * canvas.width;
      this.y = canvas.height;
      this.dx = 0;
      this.dy = -1;
    }

    this.speed = 2 + Math.random() * 2;
    this.life = 0;
    this.maxLife = 300 + Math.random() * 200;
    this.turnChance = 0.01;
    this.trail = [];
  }

  update() {
    this.life++;

    // Random turns
    if (Math.random() < this.turnChance) {
      if (this.dx !== 0) {
        this.dy = Math.random() > 0.5 ? 1 : -1;
        this.dx = 0;
      } else {
        this.dx = Math.random() > 0.5 ? 1 : -1;
        this.dy = 0;
      }
    }

    this.x += this.dx * this.speed;
    this.y += this.dy * this.speed;

    this.trail.push({ x: this.x, y: this.y });
    if (this.trail.length > 40) this.trail.shift();

    // Exit screen
    if (
      this.x < -50 ||
      this.x > canvas.width + 50 ||
      this.y < -50 ||
      this.y > canvas.height + 50 ||
      this.life > this.maxLife
    ) {
      this.reset();
    }
  }

  draw() {
    ctx.beginPath();
    for (let i = 0; i < this.trail.length - 1; i++) {
      const alpha = i / this.trail.length;
      ctx.strokeStyle = `rgba(16, 255, 120, ${alpha})`;
      ctx.lineWidth = 2;
      ctx.shadowColor = "rgba(16,255,120,0.6)";
      ctx.shadowBlur = 10;

      ctx.beginPath();
      ctx.moveTo(this.trail[i].x, this.trail[i].y);
      ctx.lineTo(this.trail[i + 1].x, this.trail[i + 1].y);
      ctx.stroke();
    }
  }
}

// Create lines
const lines = Array.from({ length: 25 }, () => new NeonLine());

// Animation loop
function animate() {
  ctx.fillStyle = "rgba(0, 0, 0, 0.15)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  lines.forEach(line => {
    line.update();
    line.draw();
  });

  requestAnimationFrame(animate);
}

animate();

const canvas = document.getElementById("game-canvas") as HTMLCanvasElement;
const ctx = canvas.getContext("2d")!;

canvas.width = 800;
canvas.height =200;

ctx.fillStyle = "#f0f0f0";
ctx.fillRect(0, 0, 800, 200);

ctx.fillStyle = "#000000";
ctx.fillRect(0, 640, 800, 2);

ctx.fillStyle = "#4caf50";
ctx.fillRect(100, 643, 100, 100);

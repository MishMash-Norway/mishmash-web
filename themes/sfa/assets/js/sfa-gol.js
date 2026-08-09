(function () {
  "use strict";

  const host = document.getElementById("sfa-gol-bg");
  if (!host || typeof window.p5 !== "function") return;

  const randomSeed = (window.crypto && window.crypto.getRandomValues)
    ? window.crypto.getRandomValues(new Uint32Array(1))[0]
    : Math.floor(Math.random() * 4294967295);
  window.SFA_THEME_STATE = { seed: randomSeed };

  const reduceMotionMedia = window.matchMedia("(prefers-reduced-motion: reduce)");
  let audioMetrics = { rms: 0, flux: 0 };

  window.addEventListener("sfa:audio-metrics", function (event) {
    audioMetrics = event.detail || audioMetrics;
  });

  function makeRng(seed) {
    let state = seed >>> 0;
    return function () {
      state = (1664525 * state + 1013904223) >>> 0;
      return state / 4294967296;
    };
  }

  new window.p5(function (p) {
    const rng = makeRng(randomSeed);
    const rules = [
      { birth: [3], survive: [2, 3], name: "B3/S23" },
      { birth: [3, 6], survive: [2, 3], name: "B36/S23" },
      { birth: [3, 4], survive: [3, 4], name: "B34/S34" }
    ];
    const interactionModes = ["brush", "cross", "ring"];
    const activeRule = rules[Math.floor(rng() * rules.length)];
    const interactionMode = interactionModes[Math.floor(rng() * interactionModes.length)];

    let cols = 0;
    let rows = 0;
    let cellSize = 13 + Math.floor(rng() * 4);
    let current = [];
    let next = [];
    let updateIntervalFrames = 6 + Math.floor(rng() * 4);
    let generation = 0;
    let lastStats = { alive: 0, births: 0, deaths: 0, density: 0, entropy: 0 };

    const hueSeed = Math.floor(150 + rng() * 55);
    const satSeed = Math.floor(92 + rng() * 35);
    const lightSeed = Math.floor(82 + rng() * 38);
    const rootStyle = document.documentElement.style;
    const accentHue = 160 + Math.floor(rng() * 26);
    const accentSat = 32 + Math.floor(rng() * 14);
    const accentLight = 34 + Math.floor(rng() * 12);
    const accent2Hue = accentHue - 10 + Math.floor(rng() * 20);
    const bgHue = accentHue - 4 + Math.floor(rng() * 8);

    rootStyle.setProperty("--sfa-accent", "hsl(" + accentHue + " " + accentSat + "% " + accentLight + "%)");
    rootStyle.setProperty("--sfa-accent-soft", "hsl(" + accentHue + " " + (accentSat + 10) + "% " + (accentLight + 28) + "%)");
    rootStyle.setProperty("--sfa-accent-2", "hsl(" + accent2Hue + " " + Math.max(24, accentSat - 2) + "% " + (accentLight + 10) + "%)");
    rootStyle.setProperty("--sfa-bg", "hsl(" + bgHue + " 28% 95%)");
    rootStyle.setProperty("--sfa-panel-shadow", "hsla(" + accentHue + " 32% 24% / 0.14)");

    function createGrid(fillRandom) {
      cols = Math.max(10, Math.floor(p.width / cellSize));
      rows = Math.max(10, Math.floor(p.height / cellSize));
      current = new Array(rows);
      next = new Array(rows);
      generation = 0;

      for (let y = 0; y < rows; y += 1) {
        current[y] = new Array(cols);
        next[y] = new Array(cols);
        for (let x = 0; x < cols; x += 1) {
          current[y][x] = fillRandom ? (rng() > 0.83 ? 1 : 0) : 0;
          next[y][x] = 0;
        }
      }
    }

    function livingNeighbors(x, y) {
      let sum = 0;
      for (let oy = -1; oy <= 1; oy += 1) {
        for (let ox = -1; ox <= 1; ox += 1) {
          if (ox === 0 && oy === 0) continue;
          const nx = (x + ox + cols) % cols;
          const ny = (y + oy + rows) % rows;
          sum += current[ny][nx];
        }
      }
      return sum;
    }

    function stepLife() {
      let aliveCount = 0;
      let births = 0;
      let deaths = 0;

      for (let y = 0; y < rows; y += 1) {
        for (let x = 0; x < cols; x += 1) {
          const isAlive = current[y][x] === 1;
          const n = livingNeighbors(x, y);
          const willLive = (isAlive && activeRule.survive.indexOf(n) !== -1) || (!isAlive && activeRule.birth.indexOf(n) !== -1);
          next[y][x] = willLive ? 1 : 0;
          if (willLive) aliveCount += 1;
          if (!isAlive && willLive) births += 1;
          if (isAlive && !willLive) deaths += 1;
        }
      }

      const tmp = current;
      current = next;
      next = tmp;

      generation += 1;
      const total = rows * cols;
      const density = total ? aliveCount / total : 0;
      const pAlive = Math.max(0.0001, Math.min(0.9999, density));
      const entropy = -(pAlive * Math.log2(pAlive) + (1 - pAlive) * Math.log2(1 - pAlive));
      lastStats = { alive: aliveCount, births: births, deaths: deaths, density: density, entropy: entropy };

      window.dispatchEvent(new CustomEvent("sfa:gol-metrics", {
        detail: {
          generation: generation,
          density: density,
          births: births,
          deaths: deaths,
          entropy: entropy,
          rule: activeRule.name,
          interactionMode: interactionMode,
          seed: randomSeed
        }
      }));
    }

    function drawGrid() {
      p.noStroke();
      const sonicBoost = Math.min(1, (audioMetrics.rms || 0) * 3.2);
      for (let y = 0; y < rows; y += 1) {
        for (let x = 0; x < cols; x += 1) {
          if (!current[y][x]) continue;
          const px = x * cellSize;
          const py = y * cellSize;
          const hueMix = (x + y + generation) % 10;
          const alpha = 68 + hueMix * 4 + sonicBoost * 48;
          p.fill(hueSeed - hueMix * 2, satSeed + hueMix * 3, lightSeed + hueMix * 2, alpha);
          p.rect(px, py, cellSize - 1, cellSize - 1, 2);
        }
      }
    }

    function drawOverlay() {
      p.noStroke();
      p.fill(255, 255, 255, 142);
      p.rect(12, 12, 250, 68, 10);
      p.fill(25, 49, 43, 230);
      p.textSize(12);
      p.textFont("Space Grotesk");
      const densityPct = (lastStats.density * 100).toFixed(1);
      const rmsPct = ((audioMetrics.rms || 0) * 100).toFixed(1);
      p.text("SFA Life " + activeRule.name + " | mode " + interactionMode, 20, 34);
      p.text("gen " + generation + " | density " + densityPct + "% | audio " + rmsPct + "%", 20, 54);
    }

    function reseedIfTooEmpty() {
      let aliveCells = 0;
      for (let y = 0; y < rows; y += 1) {
        for (let x = 0; x < cols; x += 1) {
          aliveCells += current[y][x];
        }
      }
      if (aliveCells < Math.floor((rows * cols) / (36 + Math.floor(rng() * 12)))) {
        createGrid(true);
      }
    }

    function poke(mx, my) {
      const gx = Math.floor(mx / cellSize);
      const gy = Math.floor(my / cellSize);

      if (interactionMode === "cross") {
        [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1], [0, 2], [0, -2]].forEach(function (offset) {
          const x = (gx + offset[0] + cols) % cols;
          const y = (gy + offset[1] + rows) % rows;
          current[y][x] = 1;
        });
        return;
      }

      if (interactionMode === "ring") {
        [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]].forEach(function (offset) {
          const x = (gx + offset[0] + cols) % cols;
          const y = (gy + offset[1] + rows) % rows;
          current[y][x] = 1;
        });
        return;
      }

      for (let oy = -1; oy <= 1; oy += 1) {
        for (let ox = -1; ox <= 1; ox += 1) {
          const x = (gx + ox + cols) % cols;
          const y = (gy + oy + rows) % rows;
          current[y][x] = 1;
        }
      }
    }

    p.setup = function () {
      p.pixelDensity(1);
      const canvas = p.createCanvas(window.innerWidth, window.innerHeight);
      canvas.parent(host);
      canvas.elt.setAttribute("aria-hidden", "true");
      p.frameRate(30);
      p.clear();

      if (window.innerWidth < 700) cellSize += 2;
      if (window.innerWidth > 1400) cellSize -= 1;
      updateIntervalFrames = window.innerWidth < 700 ? updateIntervalFrames + 2 : updateIntervalFrames;
      createGrid(true);
    };

    p.draw = function () {
      p.clear();
      const shimmer = Math.floor((audioMetrics.flux || 0) * 160);
      p.background(241 - shimmer * 0.04, 248 - shimmer * 0.03, 244 - shimmer * 0.02, 78);
      drawGrid();
      drawOverlay();

      if (!reduceMotionMedia.matches && p.frameCount % updateIntervalFrames === 0) {
        stepLife();
        reseedIfTooEmpty();
      }
    };

    p.windowResized = function () {
      p.resizeCanvas(window.innerWidth, window.innerHeight);
      if (window.innerWidth < 700) cellSize = 16;
      else if (window.innerWidth > 1400) cellSize = 12;
      else cellSize = 14;
      updateIntervalFrames = window.innerWidth < 700 ? 10 : 8 + Math.floor(rng() * 2);
      createGrid(true);
    };

    p.mouseMoved = function () {
      poke(p.mouseX, p.mouseY);
    };

    p.touchMoved = function () {
      poke(p.mouseX, p.mouseY);
      return true;
    };
  });
})();

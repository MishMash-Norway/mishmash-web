/* The emblem's bubbles as balls (/lab/bubbles/).

   As many balls as you ask for, held to their resting places by springs, pulled down
   by gravity, shoved by the pointer, and bounced off each other and off the walls.
   They are solid: two balls never occupy the same space. Everything here is SVG and
   arithmetic, with no physics library, and the whole loop is described on the page. */
(function () {
  var W = 800, H = 500;
  var COLOURS = ['--mm-purple', '--mm-green', '--mm-blue', '--mm-pink', '--mm-yellow', '--mm-red'];
  var FALLBACK = ['#9a90cf', '#b3e297', '#a5cbed', '#efadb2', '#d1e422', '#ee5648'];
  var MAX = 12;

  /* Each of these is one number in the loop below, and each one is on a slider. */
  var SETTINGS = [
    { id: 'spring', label: 'Spring', min: 0, max: 0.02, step: 0.001, value: 0.003,
      note: 'how hard a ball is pulled back to where it started' },
    { id: 'damping', label: 'Damping', min: 0.9, max: 1, step: 0.005, value: 0.985,
      note: 'how much speed is kept from one frame to the next' },
    { id: 'gravity', label: 'Gravity', min: -0.1, max: 0.2, step: 0.01, value: 0.02,
      note: 'a constant downward pull, negative to make them float' },
    { id: 'push', label: 'Pointer push', min: 0, max: 20, step: 0.5, value: 8,
      note: 'how hard the pointer shoves a ball it touches' },
    { id: 'bounce', label: 'Wall bounce', min: 0, max: 1, step: 0.05, value: 0.7,
      note: 'how much speed survives hitting a wall' },
    { id: 'springiness', label: 'Ball bounce', min: 0, max: 1, step: 0.05, value: 0.9,
      note: 'how much speed survives a hit between two balls' },
    { id: 'radius', label: 'Size', min: 20, max: 80, step: 1, value: 50,
      note: 'the radius of every ball, in the drawing’s own units' },
  ];

  var p = {};
  SETTINGS.forEach(function (s) { p[s.id] = s.value; });

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'class') e.className = attrs[k];
      else if (k === 'text') e.textContent = attrs[k];
      else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (k) { if (k) e.appendChild(k); });
    return e;
  }
  function svgEl(tag, attrs) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.keys(attrs || {}).forEach(function (k) { if (attrs[k] != null) e.setAttribute(k, attrs[k]); });
    return e;
  }
  function colour(i) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(COLOURS[i % COLOURS.length]).trim();
    return v || FALLBACK[i % FALLBACK.length];
  }

  function build(root) {
    var stage = svgEl('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'bb-stage',
                               role: 'img', 'aria-label': 'Two balls resting side by side.' });
    var discs = svgEl('g', {});
    stage.appendChild(discs);

    var balls = [];
    var running = false, hovering = false, still = 0;
    var calm = window.matchMedia('(prefers-reduced-motion: reduce)');

    /* Resting places. Two balls sit where the emblem has them, 200 apart on the
       middle line. More than two go into a grid that fits the stage, because a
       single row of ten would have its ends outside the picture and the balls
       would spend their lives pressed against the walls. */
    function layout() {
      var n = balls.length;
      if (n <= 2) {
        balls.forEach(function (b, i) {
          b.restX = n === 1 ? W / 2 : (i === 0 ? 300 : 500);
          b.restY = H / 2;
        });
        return;
      }
      var cols = Math.ceil(Math.sqrt(n * W / H));
      var rows = Math.ceil(n / cols);
      balls.forEach(function (b, i) {
        var col = i % cols, row = Math.floor(i / cols);
        b.restX = W * (col + 0.5) / cols;
        b.restY = H * (row + 0.5) / rows;
      });
    }

    function add() {
      if (balls.length >= MAX) return;
      var i = balls.length;
      var disc = svgEl('circle', { r: p.radius, fill: colour(i),
                                   stroke: 'var(--mm-ink-40, #777)', 'stroke-width': 1 });
      discs.appendChild(disc);
      balls.push({ x: W / 2, y: p.radius + 4, vx: (Math.random() - 0.5) * 8, vy: 0, disc: disc });
      layout(); say(); start();
    }

    function remove() {
      if (balls.length <= 1) return;
      discs.removeChild(balls.pop().disc);
      layout(); say(); start();
    }

    function step() {
      var r = p.radius, i, j;
      for (i = 0; i < balls.length; i++) {
        var b = balls[i];
        b.vx += (b.restX - b.x) * p.spring;
        b.vy += (b.restY - b.y) * p.spring;
        b.vy += p.gravity;
        b.vx *= p.damping;
        b.vy *= p.damping;
        b.x += b.vx;
        b.y += b.vy;
      }

      /* Two passes of the same correction, because separating one pair can push a
         ball into another. Two is enough for a dozen balls and cheap. */
      for (var pass = 0; pass < 2; pass++) {
        for (i = 0; i < balls.length; i++) {
          for (j = i + 1; j < balls.length; j++) {
            var a = balls[i], c = balls[j];
            var dx = c.x - a.x, dy = c.y - a.y;
            var d = Math.sqrt(dx * dx + dy * dy);
            if (d >= r * 2) continue;
            if (d === 0) { c.x += 0.01; continue; }
            var nx = dx / d, ny = dy / d, over = r * 2 - d;
            a.x -= nx * over * 0.5; a.y -= ny * over * 0.5;
            c.x += nx * over * 0.5; c.y += ny * over * 0.5;
            var dot = (a.vx - c.vx) * nx + (a.vy - c.vy) * ny;
            if (dot > 0) {
              a.vx -= dot * nx * p.springiness; a.vy -= dot * ny * p.springiness;
              c.vx += dot * nx * p.springiness; c.vy += dot * ny * p.springiness;
            }
          }
        }
        /* Walls last, so a ball pushed out of another is still put back inside. */
        for (i = 0; i < balls.length; i++) {
          var w = balls[i];
          if (w.x - r < 0) { w.x = r; w.vx = Math.abs(w.vx) * p.bounce; }
          if (w.x + r > W) { w.x = W - r; w.vx = -Math.abs(w.vx) * p.bounce; }
          if (w.y - r < 0) { w.y = r; w.vy = Math.abs(w.vy) * p.bounce; }
          if (w.y + r > H) { w.y = H - r; w.vy = -Math.abs(w.vy) * p.bounce; }
        }
      }
      draw();
    }

    function draw() {
      var r = p.radius;
      balls.forEach(function (b) {
        b.disc.setAttribute('cx', b.x.toFixed(1));
        b.disc.setAttribute('cy', b.y.toFixed(1));
        b.disc.setAttribute('r', r);
      });
    }

    function settled() {
      return balls.every(function (b) {
        return Math.abs(b.vx) < 0.05 && Math.abs(b.vy) < 0.05 &&
               Math.abs(b.x - b.restX) < 0.5 && Math.abs(b.y - b.restY) < 0.5;
      });
    }

    function loop() {
      step();
      /* Stop once nothing is moving, so an idle page costs nothing. A little grace,
         because a ball at the top of its arc is momentarily still. */
      still = settled() ? still + 1 : 0;
      if (hovering || still < 30) requestAnimationFrame(loop);
      else running = false;
    }
    function start() { if (!running) { running = true; still = 0; requestAnimationFrame(loop); } }

    function point(e) {
      var box = stage.getBoundingClientRect();
      return { x: (e.clientX - box.left) / box.width * W, y: (e.clientY - box.top) / box.height * H };
    }
    stage.addEventListener('pointerenter', function () { hovering = true; start(); });
    stage.addEventListener('pointerleave', function () { hovering = false; });
    stage.addEventListener('pointermove', function (e) {
      if (!hovering) return;
      var q = point(e), reach = p.radius * 1.2;
      balls.forEach(function (b) {
        var dx = b.x - q.x, dy = b.y - q.y;
        var d = Math.sqrt(dx * dx + dy * dy);
        if (d < reach && d > 0) {
          var f = p.push * (1 - d / reach);
          b.vx += (dx / d) * f;
          b.vy += (dy / d) * f;
        }
      });
    });

    var count = el('p', { class: 'bb-count small muted' });
    function say() {
      var pairs = balls.length * (balls.length - 1) / 2;
      count.textContent = balls.length + (balls.length === 1 ? ' ball' : ' balls') + ', ' +
        pairs + (pairs === 1 ? ' pair' : ' pairs') + ' checked twice every frame.';
      stage.setAttribute('aria-label', balls.length + ' balls moving under a spring, gravity and the pointer.');
    }

    var sliders = el('div', { class: 'bb-sliders' }, SETTINGS.map(function (s) {
      var out = el('output', { class: 'bb-value', text: String(s.value) });
      var input = el('input', {
        type: 'range', min: s.min, max: s.max, step: s.step, value: s.value,
        id: 'bb-' + s.id, class: 'bb-range',
        oninput: function () { p[s.id] = parseFloat(this.value); out.textContent = this.value; layout(); start(); },
      });
      return el('div', { class: 'bb-control' }, [
        el('label', { for: 'bb-' + s.id }, [el('span', { class: 'bb-name', text: s.label }), out]),
        input,
        el('span', { class: 'bb-note small muted', text: s.note }),
      ]);
    }));

    function reset() {
      SETTINGS.forEach(function (s) {
        p[s.id] = s.value;
        var input = document.getElementById('bb-' + s.id);
        if (input) { input.value = s.value; input.parentNode.querySelector('output').textContent = s.value; }
      });
      while (balls.length > 2) remove();
      while (balls.length < 2) add();
      layout();
      balls.forEach(function (b) { b.x = b.restX; b.y = b.restY; b.vx = 0; b.vy = 0; });
      draw(); say();
    }

    var buttons = el('p', { class: 'bb-buttons' }, [
      el('button', { type: 'button', class: 'bb-btn', text: 'Add a ball', onclick: add }),
      el('button', { type: 'button', class: 'bb-btn', text: 'Remove one', onclick: remove }),
      el('button', { type: 'button', class: 'bb-btn', text: 'Shake', onclick: function () {
        balls.forEach(function (b) { b.vx += (Math.random() - 0.5) * 30; b.vy += (Math.random() - 0.5) * 30; });
        start();
      } }),
      el('button', { type: 'button', class: 'bb-btn', text: 'Reset', onclick: reset }),
    ]);

    root.textContent = '';
    root.appendChild(stage);
    root.appendChild(buttons);
    root.appendChild(sliders);
    root.appendChild(count);

    add(); add();
    layout();
    balls.forEach(function (b) { b.x = b.restX; b.y = b.restY; b.vx = 0; b.vy = 0; });
    draw(); say();
    /* A reader who asked for less motion gets the balls at rest until they act. */
    if (!calm.matches) start();
  }

  var root = document.getElementById('bubbles');
  if (root) build(root);
})();

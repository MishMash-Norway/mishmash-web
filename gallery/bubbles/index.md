---
layout: page
title: "MishMash Bubbles"
---

<div id="bubble-container" style="width:100%;max-width:800px;margin:0 auto;cursor:pointer;">
<svg id="bubble-svg" width="100%" viewBox="0 0 420 320" xmlns="http://www.w3.org/2000/svg" style="display:block;">
  <circle id="c-purple" cx="150" cy="160" r="110" fill="#A7A1F4" stroke="#777" stroke-width="1"/>
  <circle id="c-green" cx="270" cy="160" r="110" fill="#C1F7AE" stroke="#777" stroke-width="1"/>
  <defs>
    <clipPath id="clip-left-interactive" clipPathUnits="userSpaceOnUse">
      <circle id="clip-circle" cx="150" cy="160" r="110"/>
    </clipPath>
  </defs>
  <circle id="c-overlap" cx="270" cy="160" r="110" fill="#363644" clip-path="url(#clip-left-interactive)"/>
</svg>
</div>

<script>
(function() {
  var W = 420, H = 320, R = 110;
  var balls = [
    { x: 150, y: 160, vx: 0, vy: 0, rest_x: 150, rest_y: 160 },
    { x: 270, y: 160, vx: 0, vy: 0, rest_x: 270, rest_y: 160 }
  ];
  var purple = document.getElementById('c-purple');
  var green = document.getElementById('c-green');
  var overlap = document.getElementById('c-overlap');
  var clipCircle = document.getElementById('clip-circle');
  var svg = document.getElementById('bubble-svg');
  var container = document.getElementById('bubble-container');

  var hovering = false;
  var damping = 0.985;
  var springK = 0.003;
  var repelForce = 8;
  var gravity = 0.02;
  var running = false;

  function dist(a, b) {
    var dx = a.x - b.x, dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function getSVGPoint(e) {
    var rect = svg.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / rect.width * W,
      y: (e.clientY - rect.top) / rect.height * H
    };
  }

  container.addEventListener('mouseenter', function() { hovering = true; startLoop(); });
  container.addEventListener('mouseleave', function() { hovering = false; });
  container.addEventListener('mousemove', function(e) {
    if (!hovering) return;
    var p = getSVGPoint(e);
    for (var i = 0; i < balls.length; i++) {
      var b = balls[i];
      var dx = b.x - p.x, dy = b.y - p.y;
      var d = Math.sqrt(dx * dx + dy * dy);
      if (d < R * 1.2 && d > 0) {
        var strength = repelForce * (1 - d / (R * 1.2));
        b.vx += (dx / d) * strength;
        b.vy += (dy / d) * strength;
      }
    }
  });

  function update() {
    for (var i = 0; i < balls.length; i++) {
      var b = balls[i];
      // spring back to rest position
      b.vx += (b.rest_x - b.x) * springK;
      b.vy += (b.rest_y - b.y) * springK;
      // slight gravity
      b.vy += gravity;
      // damping
      b.vx *= damping;
      b.vy *= damping;
      // integrate
      b.x += b.vx;
      b.y += b.vy;
      // wall bounce
      if (b.x - R < 0) { b.x = R; b.vx = Math.abs(b.vx) * 0.7; }
      if (b.x + R > W) { b.x = W - R; b.vx = -Math.abs(b.vx) * 0.7; }
      if (b.y - R < 0) { b.y = R; b.vy = Math.abs(b.vy) * 0.7; }
      if (b.y + R > H) { b.y = H - R; b.vy = -Math.abs(b.vy) * 0.7; }
    }
    // ball-ball collision
    var a = balls[0], b2 = balls[1];
    var dx = b2.x - a.x, dy = b2.y - a.y;
    var d = Math.sqrt(dx * dx + dy * dy);
    var minDist = R * 2;
    if (d < minDist && d > 0) {
      var nx = dx / d, ny = dy / d;
      var overlap_amt = minDist - d;
      a.x -= nx * overlap_amt * 0.5;
      a.y -= ny * overlap_amt * 0.5;
      b2.x += nx * overlap_amt * 0.5;
      b2.y += ny * overlap_amt * 0.5;
      // elastic collision
      var dvx = a.vx - b2.vx, dvy = a.vy - b2.vy;
      var dot = dvx * nx + dvy * ny;
      if (dot > 0) {
        a.vx -= dot * nx * 0.9;
        a.vy -= dot * ny * 0.9;
        b2.vx += dot * nx * 0.9;
        b2.vy += dot * ny * 0.9;
      }
    }
    render();
  }

  function render() {
    purple.setAttribute('cx', balls[0].x);
    purple.setAttribute('cy', balls[0].y);
    clipCircle.setAttribute('cx', balls[0].x);
    clipCircle.setAttribute('cy', balls[0].y);
    green.setAttribute('cx', balls[1].x);
    green.setAttribute('cy', balls[1].y);
    overlap.setAttribute('cx', balls[1].x);
    overlap.setAttribute('cy', balls[1].y);
  }

  function isSettled() {
    for (var i = 0; i < balls.length; i++) {
      var b = balls[i];
      if (Math.abs(b.vx) > 0.05 || Math.abs(b.vy) > 0.05) return false;
      if (Math.abs(b.x - b.rest_x) > 0.5 || Math.abs(b.y - b.rest_y) > 0.5) return false;
    }
    return true;
  }

  function loop() {
    update();
    if (hovering || !isSettled()) {
      requestAnimationFrame(loop);
    } else {
      // snap to rest
      for (var i = 0; i < balls.length; i++) {
        balls[i].x = balls[i].rest_x;
        balls[i].y = balls[i].rest_y;
        balls[i].vx = 0;
        balls[i].vy = 0;
      }
      render();
      running = false;
    }
  }

  function startLoop() {
    if (!running) { running = true; requestAnimationFrame(loop); }
  }
})();
</script>
/* The term atlas lab page (/lab/term-atlas/). Reads terms.json, written by
   scripts/build_term_atlas.py, and draws the web of definitions (a small force
   layout in SVG, no libraries), the Bokmål and Nynorsk columns and the list. */
(function () {
  "use strict";
  var root = document.getElementById("term-atlas");
  if (!root) return;
  var nb = root.dataset.lang === "nb";
  var T = nb ? {
    summary: function (n, l, p) { return n + " termer, " + l + " streker mellom definisjoner, " + p + " av termene brukes på mishmash.no."; },
    same: "Likt", close: "Litt ulikt", different: "Ulike ord",
    machine: "Apertium skriver", none: "Ingen definisjon i kilden.",
    uses: "Definisjonen bruker", usedBy: "Brukes i definisjonen av", pages: "Sider på mishmash.no som bruker den",
    source: "Kilde", count: function (n) { return n + (n === 1 ? " term" : " termer"); },
    head: ["Bokmål", "Nynorsk", "Engelsk", "Kilde"]
  } : {
    summary: function (n, l, p) { return n + " terms, " + l + " lines between definitions, " + p + " of the terms used on mishmash.no."; },
    same: "The same", close: "A small change", different: "Different words",
    machine: "Apertium writes", none: "No definition in the source.",
    uses: "The definition uses", usedBy: "Used in the definition of", pages: "Pages on mishmash.no that use it (in Bokmål)",
    source: "Source", count: function (n) { return n + (n === 1 ? " term" : " terms"); },
    head: ["Bokmål", "Nynorsk", "English", "Source"]
  };
  var SVG = "http://www.w3.org/2000/svg";
  var SOURCES = {};

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function sv(tag, attrs) {
    var e = document.createElementNS(SVG, tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    return e;
  }

  fetch(root.dataset.src).then(function (r) { return r.json(); }).then(draw).catch(function () {});

  function draw(data) {
    var cs = data.concepts, byId = {};
    SOURCES = data.sources || {};
    cs.forEach(function (c) { byId[c.id] = c; c.usedBy = []; });
    var links = [];
    cs.forEach(function (c) {
      c.uses.forEach(function (u) { if (byId[u]) { links.push([c, byId[u]]); byId[u].usedBy.push(c.id); } });
    });
    var used = cs.filter(function (c) { return c.pages.length; }).length;
    document.getElementById("ta-summary").textContent = T.summary(cs.length, links.length, used);
    graph(cs, links, data.sources);
    split(cs);
    list(cs, data.sources);
  }

  function select(c, sources) {
    var d = document.getElementById("ta-detail");
    d.innerHTML = "";
    d.appendChild(el("h3", null, nb ? c.nb : (c.en || c.nb)));
    var dl = el("dl", { class: "ta-terms" });
    [["Bokmål", c.nb], ["Nynorsk", c.nn], [nb ? "Engelsk" : "English", c.en]].forEach(function (p) {
      if (!p[1]) return;
      dl.appendChild(el("dt", null, p[0]));
      dl.appendChild(el("dd", { lang: p[0] === "Nynorsk" ? "nn" : p[0] === "Bokmål" ? "nb" : "en" }, p[1]));
    });
    d.appendChild(dl);
    var def = c.definition[nb ? "nb" : "en"] || c.definition.nb || c.definition.nn;
    d.appendChild(el("p", def ? { lang: c.definition[nb ? "nb" : "en"] ? (nb ? "nb" : "en") : "nb" } : { class: "muted" }, def || T.none));
    function rel(label, ids) {
      if (!ids.length) return;
      var p = el("p", null, label + ": ");
      ids.forEach(function (id, i) {
        var b = el("button", { type: "button", class: "ta-link" }, byIdGlobal[id].nb);
        b.addEventListener("click", function () { select(byIdGlobal[id], sources); highlight(id); });
        if (i) p.appendChild(document.createTextNode(", "));
        p.appendChild(b);
      });
      d.appendChild(p);
    }
    rel(T.uses, c.uses);
    rel(T.usedBy, c.usedBy);
    if (c.pages.length) {
      var p = el("p", null, T.pages + ": ");
      c.pages.forEach(function (pg, i) {
        if (i) p.appendChild(document.createTextNode(", "));
        p.appendChild(el("a", { href: pg.url, lang: "nb" }, pg.title));
      });
      d.appendChild(p);
    }
    var s = sources[c.source] || {};
    var src = el("p", { class: "muted" }, T.source + ": ");
    src.appendChild(el("a", { href: c.url || s.url }, s.name || c.source));
    if (c.licence) src.appendChild(document.createTextNode(" (" + c.licence + ")"));
    d.appendChild(src);
  }

  var byIdGlobal = {}, nodesEl = {}, linkEls = [];
  function highlight(id) {
    Object.keys(nodesEl).forEach(function (k) { nodesEl[k].classList.toggle("ta-on", k === id); });
    linkEls.forEach(function (l) { l.el.classList.toggle("ta-on", l.a === id || l.b === id); });
  }

  /* A small force layout: repulsion between all dots, springs along the
     lines, a pull to the centre; run a fixed number of steps, then draw. */
  function graph(cs, links, sources) {
    cs.forEach(function (c) { byIdGlobal[c.id] = c; });
    var box = document.getElementById("ta-graph");
    var W = Math.max(320, Math.min(900, box.clientWidth || 700)), H = Math.round(W * (W < 560 ? 1.3 : 0.75));
    var n = cs.length;
    cs.forEach(function (c, i) {
      var a = 2 * Math.PI * i / n;
      c.x = W / 2 + Math.cos(a) * W * 0.35; c.y = H / 2 + Math.sin(a) * H * 0.35; c.vx = 0; c.vy = 0;
      c.r = 4 + Math.min(10, 2 * Math.sqrt(c.pages.length)) + Math.min(6, c.usedBy.length * 1.5);
    });
    /* Terms with no lines sit on an outer ring, in alphabetical order; the
       linked ones are laid out by force inside it. */
    var lone = cs.filter(function (c) { return !(c.uses.length + c.usedBy.length); })
      .sort(function (a, b) { return a.nb.localeCompare(b.nb, "nb"); });
    var web = cs.filter(function (c) { return c.uses.length + c.usedBy.length; });
    lone.forEach(function (c, i) {
      var a = 2 * Math.PI * i / lone.length - Math.PI / 2;
      var rx = W < 560 ? W / 2 - 16 : W / 2 - 190;
      c.x = W / 2 + Math.cos(a) * rx; c.y = H / 2 + Math.sin(a) * (H / 2 - 20); c.fixed = true;
    });
    var m = web.length;
    for (var step = 0; step < 500; step++) {
      var t = 1 - step / 500;
      for (var i = 0; i < m; i++) for (var j = i + 1; j < m; j++) {
        var a = web[i], b = web[j], dx = b.x - a.x, dy = b.y - a.y, d2 = dx * dx + dy * dy + 0.01, d = Math.sqrt(d2);
        var f = 2600 / d2;
        a.vx -= f * dx / d; a.vy -= f * dy / d; b.vx += f * dx / d; b.vy += f * dy / d;
      }
      links.forEach(function (l) {
        var a = l[0], b = l[1], dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) + 0.01;
        var f = (d - 95) * 0.03;
        a.vx += f * dx / d; a.vy += f * dy / d; b.vx -= f * dx / d; b.vy -= f * dy / d;
      });
      web.forEach(function (c) {
        c.vx += (W / 2 - c.x) * 0.012; c.vy += (H / 2 - c.y) * 0.012;
        c.x += c.vx * t; c.y += c.vy * t; c.vx *= 0.5; c.vy *= 0.5;
        var rx = (W < 560 ? W / 2 - 50 : W / 2 - 260), ry = H / 2 - 70, ex = (c.x - W / 2) / rx, ey = (c.y - H / 2) / ry, e = Math.sqrt(ex * ex + ey * ey);
        if (e > 1) { c.x = W / 2 + (c.x - W / 2) / e; c.y = H / 2 + (c.y - H / 2) / e; }
      });
    }
    var svg = sv("svg", { viewBox: "0 0 " + W + " " + H, class: "ta-svg" });
    var gl = sv("g"), gn = sv("g");
    links.forEach(function (l) {
      var e = sv("line", { x1: l[0].x, y1: l[0].y, x2: l[1].x, y2: l[1].y, class: "ta-edge" });
      gl.appendChild(e); linkEls.push({ el: e, a: l[0].id, b: l[1].id });
    });
    cs.forEach(function (c) {
      var g = sv("g", { class: "ta-node ta-src-" + c.source, tabindex: "0", role: "button" });
      g.setAttribute("aria-label", c.nb + (c.en ? " (" + c.en + ")" : ""));
      g.appendChild(sv("circle", { cx: c.x, cy: c.y, r: c.r }));
      var narrow = W < 560, linked = c.uses.length + c.usedBy.length;
      if (!narrow || (linked && c.usedBy.length + c.pages.length > 1)) {
        var tx = c.fixed
          ? sv("text", { x: c.x + (c.x >= W / 2 ? c.r + 4 : -c.r - 4), y: c.y + 4, "text-anchor": c.x >= W / 2 ? "start" : "end" })
          : sv("text", { x: c.x, y: c.y - c.r - 3, "text-anchor": "middle" });
        var label = nb ? c.nb : (c.en || c.nb);
        tx.textContent = label.length > 26 ? label.slice(0, 24) + "…" : label;
        g.appendChild(tx);
      }
      var title = sv("title"); title.textContent = c.nb + " · " + c.nn + (c.en ? " · " + c.en : ""); g.appendChild(title);
      function go() { select(c, sources); highlight(c.id); }
      g.addEventListener("click", go);
      g.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); go(); } });
      nodesEl[c.id] = g;
      gn.appendChild(g);
    });
    svg.appendChild(gl); svg.appendChild(gn);
    box.appendChild(svg);
    box.dataset.sources = Object.keys(sources).join(" ");
  }

  function split(cs) {
    var box = document.getElementById("ta-split");
    ["same", "close", "different"].forEach(function (k) {
      var items = cs.filter(function (c) { return c.kind === k; });
      var col = el("section", { class: "ta-col ta-col-" + k });
      col.appendChild(el("h3", null, T[k] + " · " + T.count(items.length)));
      var ul = el("ul");
      items.sort(function (a, b) { return a.nb.localeCompare(b.nb, "nb"); }).forEach(function (c) {
        var li = el("li");
        li.appendChild(el("span", { lang: "nb", class: "ta-nb" }, c.nb));
        if (k !== "same") {
          li.appendChild(document.createTextNode(" → "));
          li.appendChild(el("span", { lang: "nn", class: "ta-nn" }, c.nn));
        }
        if (c.apertium_ok === false) {
          var m = el("span", { class: "ta-machine", lang: "nn" }, T.machine + " «" + c.apertium + "»");
          li.appendChild(m);
        }
        li.addEventListener("click", function () { select(c, SOURCES); highlight(c.id); });
        ul.appendChild(li);
      });
      col.appendChild(ul);
      box.appendChild(col);
    });
  }

  function list(cs, sources) {
    var box = document.getElementById("ta-list");
    var table = el("table", { class: "ta-table" });
    var tr = el("tr");
    T.head.forEach(function (h) { tr.appendChild(el("th", { scope: "col" }, h)); });
    var thead = el("thead"); thead.appendChild(tr); table.appendChild(thead);
    var tb = el("tbody");
    cs.slice().sort(function (a, b) { return a.nb.localeCompare(b.nb, "nb"); }).forEach(function (c) {
      var r = el("tr");
      var td = el("td");
      var b = el("button", { type: "button", class: "ta-link", lang: "nb" }, c.nb);
      b.addEventListener("click", function () {
        select(c, sources); highlight(c.id);
        document.getElementById("ta-detail").scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
      td.appendChild(b); r.appendChild(td);
      r.appendChild(el("td", { lang: "nn" }, c.nn));
      r.appendChild(el("td", { lang: "en" }, c.en));
      var s = el("td"); s.appendChild(el("a", { href: c.url || (sources[c.source] || {}).url || "#" }, (sources[c.source] || {}).name ? (c.source === "centre" ? "MishMash" : c.source === "uhr-termbase" ? "UHR" : "Termportalen KI") : c.source));
      r.appendChild(s);
      tb.appendChild(r);
    });
    table.appendChild(tb);
    box.appendChild(table);
  }
})();

/* Research pulse charts. Data and strings are inlined by _includes/research-pulse.html. */
(function () {
"use strict";

var VIOLET = "#6c5bd2";      /* series slot 1 */
var VIOLET_LIGHT = "#a99df0"; /* lighter step of the same ramp (upcoming) */
var GREEN = "#3f8a35";       /* series slot 2 */
var INK = "#1c1c1c";
var MUTED = "#767676";
var GRID = "#e6e6e6";
var BAR = 20;                /* bar thickness, <= 24px */

/* ── Aggregations ─────────────────────────────────────────────────────── */

function countBy(arr, key) {
  var m = new Map();
  arr.forEach(function (d) {
    var k = key(d);
    if (k == null) return;
    (Array.isArray(k) ? k : [k]).forEach(function (kk) {
      m.set(kk, (m.get(kk) || 0) + 1);
    });
  });
  return Array.from(m, function (e) { return { label: e[0], value: e[1] }; })
    .sort(function (a, b) { return b.value - a.value || d3.ascending(a.label, b.label); });
}

var typeLabels = PULSE_STR.typeLabels || {};
var byType = countBy(PULSE_RESULTS, function (r) { return r.t; })
  .map(function (d) {
    return { label: typeLabels[d.label] || d.label, value: d.value };
  });
var byInst = countBy(PULSE_RESULTS, function (r) { return r.inst; })
  .map(function (d) {
    return { label: PULSE_INST_SHORT[d.label] || d.label, full: d.label, value: d.value };
  });

function monthRange(months) {
  var sorted = months.slice().sort();
  var out = [];
  var cur = sorted[0];
  var last = sorted[sorted.length - 1];
  while (cur <= last) {
    out.push(cur);
    var y = +cur.slice(0, 4);
    var m = +cur.slice(5, 7);
    m += 1;
    if (m > 12) { m = 1; y += 1; }
    cur = y + "-" + String(m).padStart(2, "0");
  }
  return out;
}

var eventCounts = new Map();
PULSE_EVENTS.forEach(function (e) {
  eventCounts.set(e.m, (eventCounts.get(e.m) || 0) + 1);
});
var byMonth = monthRange(Array.from(eventCounts.keys())).map(function (m) {
  return { m: m, value: eventCounts.get(m) || 0, upcoming: m > PULSE_BUILD_MONTH };
});

function monthLabel(m, withYear) {
  var name = PULSE_STR.months[+m.slice(5, 7) - 1];
  return withYear ? name + " " + m.slice(2, 4) : name;
}

/* ── KPI tiles ────────────────────────────────────────────────────────── */

var PEER_REVIEWED = { "Journal article": 1, "Book chapter": 1 };
var tiles = [
  { label: PULSE_STR.tileResults, value: PULSE_RESULTS.length },
  { label: PULSE_STR.tilePubs, value: PULSE_RESULTS.filter(function (r) { return PEER_REVIEWED[r.t]; }).length },
  { label: PULSE_STR.tileInsts, value: byInst.length },
  { label: PULSE_STR.tileEvents, value: PULSE_EVENTS.length }
];
var tilesEl = document.getElementById("pulse-tiles");
tiles.forEach(function (t) {
  var tile = document.createElement("div");
  tile.className = "pulse-tile";
  var lab = document.createElement("div");
  lab.className = "pulse-tile-label";
  lab.textContent = t.label;
  var val = document.createElement("div");
  val.className = "pulse-tile-value";
  val.textContent = t.value;
  tile.appendChild(lab);
  tile.appendChild(val);
  tilesEl.appendChild(tile);
});

/* ── Tooltip (one per chart wrap) ─────────────────────────────────────── */

function makeTip(wrap) {
  var tip = document.createElement("div");
  tip.className = "pulse-tip";
  wrap.appendChild(tip);
  return {
    show: function (lines, x, y) {
      tip.textContent = "";
      lines.forEach(function (line, i) {
        var el = document.createElement(i === 0 ? "strong" : "div");
        el.textContent = line;
        tip.appendChild(el);
      });
      tip.style.opacity = 1;
      var w = wrap.clientWidth;
      var tw = tip.offsetWidth;
      var left = Math.min(Math.max(x - tw / 2, 0), w - tw);
      tip.style.left = left + "px";
      tip.style.top = Math.max(y - tip.offsetHeight - 10, 0) + "px";
    },
    hide: function () { tip.style.opacity = 0; }
  };
}

/* ── Rounded data-end bars (square at the baseline) ───────────────────── */

function barPathH(x, y, w, h, r) {
  r = Math.min(r, w, h / 2);
  return "M" + x + "," + y +
    "h" + (w - r) +
    "a" + r + "," + r + " 0 0 1 " + r + "," + r +
    "v" + (h - 2 * r) +
    "a" + r + "," + r + " 0 0 1 " + -r + "," + r +
    "h" + -(w - r) + "z";
}

function barPathV(x, y, w, h, r) {
  r = Math.min(r, h, w / 2);
  return "M" + x + "," + (y + h) +
    "v" + -(h - r) +
    "a" + r + "," + r + " 0 0 1 " + r + "," + -r +
    "h" + (w - 2 * r) +
    "a" + r + "," + r + " 0 0 1 " + r + "," + r +
    "v" + (h - r) + "z";
}

/* ── Horizontal bar chart ─────────────────────────────────────────────── */

function renderBars(id, data, color, unitWord) {
  var wrap = document.getElementById(id);
  wrap.textContent = "";
  var tip = makeTip(wrap);
  var width = wrap.clientWidth || 320;
  var labelW = Math.min(Math.round(width * 0.38), 180);
  var rowH = 30;
  var margin = { top: 4, right: 44, bottom: 4, left: labelW };
  var height = margin.top + margin.bottom + data.length * rowH;

  var svg = d3.select(wrap).append("svg")
    .attr("viewBox", "0 0 " + width + " " + height)
    .attr("width", width).attr("height", height)
    .attr("role", "img");

  var x = d3.scaleLinear()
    .domain([0, d3.max(data, function (d) { return d.value; })])
    .range([0, width - margin.left - margin.right]);
  var y = d3.scaleBand()
    .domain(data.map(function (d) { return d.label; }))
    .range([margin.top, height - margin.bottom]);

  var g = svg.append("g");
  data.forEach(function (d) {
    var yPos = y(d.label) + (y.bandwidth() - BAR) / 2;
    var w = Math.max(x(d.value), 2);
    var row = g.append("g");

    /* category label */
    row.append("text")
      .attr("x", margin.left - 8).attr("y", yPos + BAR / 2)
      .attr("dy", "0.35em").attr("text-anchor", "end")
      .attr("fill", INK).attr("font-size", 12)
      .text(d.label.length > 26 ? d.label.slice(0, 25) + "…" : d.label);

    /* hit target first, bar second (CSS sibling hover) */
    var hit = row.append("rect")
      .attr("class", "pulse-bar-hit")
      .attr("x", 0).attr("y", y(d.label))
      .attr("width", width).attr("height", y.bandwidth())
      .attr("tabindex", 0)
      .attr("aria-label", (d.full || d.label) + ": " + d.value + " " + unitWord);

    row.append("path")
      .attr("class", "pulse-bar")
      .attr("d", barPathH(margin.left, yPos, w, BAR, 4))
      .attr("fill", color)
      .attr("pointer-events", "none");

    /* value at the tip */
    row.append("text")
      .attr("x", margin.left + w + 6).attr("y", yPos + BAR / 2)
      .attr("dy", "0.35em")
      .attr("fill", MUTED).attr("font-size", 12)
      .attr("font-variant-numeric", "tabular-nums")
      .text(d.value);

    function show() {
      tip.show([d.value + " " + unitWord, d.full || d.label],
        margin.left + w / 2, y(d.label));
    }
    hit.on("pointermove", show).on("pointerleave", tip.hide)
      .on("focus", show).on("blur", tip.hide);
  });
}

/* ── Monthly columns ──────────────────────────────────────────────────── */

function renderColumns(id, data) {
  var wrap = document.getElementById(id);
  wrap.textContent = "";
  var tip = makeTip(wrap);
  var width = wrap.clientWidth || 600;
  var height = 220;
  var margin = { top: 10, right: 8, bottom: 28, left: 28 };

  var svg = d3.select(wrap).append("svg")
    .attr("viewBox", "0 0 " + width + " " + height)
    .attr("width", width).attr("height", height)
    .attr("role", "img");

  var x = d3.scaleBand()
    .domain(data.map(function (d) { return d.m; }))
    .range([margin.left, width - margin.right])
    .paddingInner(0.15).paddingOuter(0.05);
  var yMax = d3.max(data, function (d) { return d.value; });
  var y = d3.scaleLinear()
    .domain([0, yMax]).nice()
    .range([height - margin.bottom, margin.top]);

  /* hairline gridlines + y ticks */
  var ticks = y.ticks(Math.min(4, yMax));
  svg.append("g").selectAll("line").data(ticks).join("line")
    .attr("x1", margin.left).attr("x2", width - margin.right)
    .attr("y1", y).attr("y2", y)
    .attr("stroke", GRID).attr("stroke-width", 1);
  svg.append("g").selectAll("text").data(ticks).join("text")
    .attr("x", margin.left - 6).attr("y", y)
    .attr("dy", "0.32em").attr("text-anchor", "end")
    .attr("fill", MUTED).attr("font-size", 11)
    .attr("font-variant-numeric", "tabular-nums")
    .text(function (t) { return t; });

  /* baseline */
  svg.append("line")
    .attr("x1", margin.left).attr("x2", width - margin.right)
    .attr("y1", y(0)).attr("y2", y(0))
    .attr("stroke", "#c6c6c6").attr("stroke-width", 1);

  /* x labels: skip some when crowded; show year at january and the ends */
  var every = x.bandwidth() < 26 ? 2 : 1;
  data.forEach(function (d, i) {
    if (i % every !== 0) return;
    var withYear = i === 0 || d.m.slice(5, 7) === "01";
    svg.append("text")
      .attr("x", x(d.m) + x.bandwidth() / 2).attr("y", height - margin.bottom + 16)
      .attr("text-anchor", "middle")
      .attr("fill", MUTED).attr("font-size", 11)
      .text(monthLabel(d.m, withYear));
  });

  var barW = Math.min(x.bandwidth(), 24);
  data.forEach(function (d) {
    var cx = x(d.m) + x.bandwidth() / 2;
    var h = y(0) - y(d.value);
    var g = svg.append("g");
    var label = monthLabel(d.m, true) + ": " + d.value + " " +
      (d.value === 1 ? PULSE_STR.event : PULSE_STR.events) +
      (d.upcoming ? " (" + PULSE_STR.upcoming.toLowerCase() + ")" : "");

    var hit = g.append("rect")
      .attr("class", "pulse-bar-hit")
      .attr("x", x(d.m)).attr("y", margin.top)
      .attr("width", x.bandwidth()).attr("height", height - margin.top - margin.bottom)
      .attr("tabindex", 0)
      .attr("aria-label", label);

    if (d.value > 0) {
      g.append("path")
        .attr("class", "pulse-bar")
        .attr("d", barPathV(cx - barW / 2, y(d.value), barW, h, 4))
        .attr("fill", d.upcoming ? VIOLET_LIGHT : VIOLET)
        .attr("pointer-events", "none");
    }

    function show() {
      tip.show([d.value + " " + (d.value === 1 ? PULSE_STR.event : PULSE_STR.events),
        monthLabel(d.m, true) + (d.upcoming ? " · " + PULSE_STR.upcoming : "")],
        cx, y(d.value));
    }
    hit.on("pointermove", show).on("pointerleave", tip.hide)
      .on("focus", show).on("blur", tip.hide);
  });
}

/* ── Legend (events chart: two ordinal steps) ─────────────────────────── */

function renderLegend() {
  var el = document.getElementById("pulse-events-legend");
  el.textContent = "";
  [[VIOLET, PULSE_STR.held], [VIOLET_LIGHT, PULSE_STR.upcoming]].forEach(function (item) {
    var span = document.createElement("span");
    var sw = document.createElement("span");
    sw.className = "pulse-legend-swatch";
    sw.style.background = item[0];
    span.appendChild(sw);
    span.appendChild(document.createTextNode(item[1]));
    el.appendChild(span);
  });
}

/* ── Table views ──────────────────────────────────────────────────────── */

function renderTable(id, headers, rows) {
  var details = document.getElementById(id);
  var old = details.querySelector("table");
  if (old) old.remove();
  var table = document.createElement("table");
  var thead = document.createElement("thead");
  var trh = document.createElement("tr");
  headers.forEach(function (h) {
    var th = document.createElement("th");
    th.textContent = h;
    trh.appendChild(th);
  });
  thead.appendChild(trh);
  table.appendChild(thead);
  var tbody = document.createElement("tbody");
  rows.forEach(function (r) {
    var tr = document.createElement("tr");
    r.forEach(function (c) {
      var td = document.createElement("td");
      td.textContent = c;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  details.appendChild(table);
}

/* ── Render all ───────────────────────────────────────────────────────── */

function renderAll() {
  renderBars("pulse-types", byType, VIOLET, PULSE_STR.results);
  renderBars("pulse-insts", byInst, GREEN, PULSE_STR.results);
  renderColumns("pulse-events", byMonth);
  renderLegend();
}

renderAll();

renderTable("pulse-types-table", [PULSE_STR.type, PULSE_STR.count],
  byType.map(function (d) { return [d.label, d.value]; }));
renderTable("pulse-insts-table", [PULSE_STR.institution, PULSE_STR.count],
  byInst.map(function (d) { return [d.full, d.value]; }));
renderTable("pulse-events-table", [PULSE_STR.month, PULSE_STR.count],
  byMonth.map(function (d) { return [monthLabel(d.m, true), d.value]; }));

var synced = document.getElementById("pulse-synced");
if (synced && PULSE_SYNCED) {
  synced.textContent = PULSE_SYNCED.slice(0, 10);
}

var resizeTimer = null;
window.addEventListener("resize", function () {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(renderAll, 150);
});

})();

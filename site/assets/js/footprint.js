/* The footprint of mishmash.no, drawn and played (lab page /lab/footprint/).
   Reads /data/page-weight.json, which scripts/measure_page_weight.mjs writes
   at every deployment: the weight of a set of pages, the reference page as it
   would be with four common choices the site does not make, and the median
   page of the web from the HTTP Archive. Nothing here is typed in by hand.
   Plain SVG and Web Audio, no libraries, so the page stays light itself. */
(function () {
  var root = document.getElementById('footprint');
  if (!root) return;
  var nb = root.dataset.lang === 'nb';
  var BYTES_PER_NOTE = 25 * 1024;
  var NOTES_PER_SECOND = 10;
  var KINDS = ['html', 'styles', 'scripts', 'fonts', 'data', 'images', 'other', 'video', 'web'];
  var T = nb ? {
    served: 'Slik siden sendes', jpeg: 'Bilder som JPEG', fonts: 'Skrifter i full størrelse',
    carousel: 'Alle karusellbilder med en gang', video: 'Videospillere lastet med siden',
    all: 'Alle fire valgene sammen', web: 'Medianside på nettet',
    kinds: { html: 'HTML', styles: 'stiler', scripts: 'skript', fonts: 'skrifter', data: 'data', images: 'bilder', other: 'annet', video: 'videospiller', web: 'hele siden' },
    version: 'Versjon', kb: 'kB per besøk', co2: 'g CO₂ per besøk', times: 'Ganger nettstedets side', listen: 'Lytt',
    stop: 'Stopp', playing: 'Spiller', page: 'Side', measured: 'Målt', median: 'medianside på nettet',
    notMeasured: 'ikke målt ved denne byggingen', noData: 'Målingene finnes bare på det publiserte nettstedet, ikke i en lokal bygging.',
    self: 'Denne siden har så langt sendt deg {kb} kB i {n} forespørsler.', selfCached: ' Noe kom fra nettleserens hurtigbuffer og telles ikke.',
    chart: 'Stolpediagram over vekten til de samme sidene bygget på ulike måter. Tallene står i tabellen under.'
  } : {
    served: 'As served', jpeg: 'Photos as JPEG', fonts: 'Fonts at full size',
    carousel: 'Every carousel photo on arrival', video: 'Video players loaded with the page',
    all: 'All four choices together', web: 'Median web page',
    kinds: { html: 'HTML', styles: 'styles', scripts: 'scripts', fonts: 'fonts', data: 'data', images: 'images', other: 'other', video: 'video player', web: 'whole page' },
    version: 'Version', kb: 'kB per visit', co2: 'g CO₂ per visit', times: 'Times the page as served', listen: 'Listen',
    stop: 'Stop', playing: 'Playing', page: 'Page', measured: 'Measured', median: 'median web page',
    notMeasured: 'not measured in this build', noData: 'The measurements exist only on the published site, not in a local build.',
    self: 'So far this page has sent you {kb} kB in {n} requests.', selfCached: ' Some of it came from your browser cache and is not counted.',
    chart: 'Bar chart of the weight of the same page built in different ways. The figures are in the table below.'
  };

  function kb(b) { return Math.round(b / 1024).toLocaleString(nb ? 'nb-NO' : 'en-GB'); }
  function fill(id, text) { var e = document.getElementById(id); if (e) e.textContent = text; }

  /* --- the versions of the reference page ------------------------------ */
  function versions(d) {
    var a = d.alternatives, base = {}, out = [];
    Object.keys(a.served_by_kind).forEach(function (k) { if (a.served_by_kind[k]) base[k] = a.served_by_kind[k]; });
    function withExtra(key, extras) {
      var parts = Object.assign({}, base);
      extras.forEach(function (v) { if (v.extra_bytes) parts[v.kind] = (parts[v.kind] || 0) + v.extra_bytes; });
      return { key: key, parts: parts };
    }
    out.push({ key: 'served', parts: base });
    var measured = a.variants.filter(function (v) { return v.extra_bytes !== null; });
    a.variants.forEach(function (v) {
      out.push(v.extra_bytes === null ? { key: v.key, missing: true, parts: {} } : withExtra(v.key, [v]));
    });
    out.push(withExtra('all', measured));
    if (a.web_median) out.push({ key: 'web', parts: { web: a.web_median.bytes } });
    out.forEach(function (v) { v.bytes = Object.keys(v.parts).reduce(function (s, k) { return s + v.parts[k]; }, 0); });
    return out;
  }

  /* --- drawing ------------------------------------------------------------ */
  var SVG = 'http://www.w3.org/2000/svg';
  function el(name, attrs, parent) {
    var e = document.createElementNS(SVG, name);
    Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(e);
    return e;
  }

  // Drawn at the width of its box, so the text keeps its size on a phone;
  // below 560 px the label goes above the bar instead of beside it.
  function drawBars(box, rows, max, labelWidth) {
    var W = Math.max(300, Math.round(box.clientWidth || 720));
    var narrow = W < 560;
    if (narrow) labelWidth = 0;
    var row = narrow ? 44 : 34, top = narrow ? 18 : 0, H = rows.length * row + 8;
    var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: W, height: H, role: 'img', 'aria-label': T.chart, class: 'fp-chart' }, box);
    var plot = W - labelWidth - 90 - (narrow ? 0 : 8);
    rows.forEach(function (r, i) {
      var y = i * row + 4, g = el('g', { 'data-row': r.key }, svg);
      var t = el('text', narrow ? { x: 0, y: y + 12, class: 'fp-label' } : { x: labelWidth - 8, y: y + 18, 'text-anchor': 'end', class: 'fp-label' }, g);
      t.textContent = r.label;
      if (r.missing) {
        var m = el('text', { x: labelWidth, y: y + top + 18, class: 'fp-value' }, g); m.textContent = T.notMeasured; return;
      }
      var x = labelWidth;
      KINDS.forEach(function (k) {
        if (!r.parts[k]) return;
        var w = Math.max(1, r.parts[k] / max * plot);
        var rect = el('rect', { x: x, y: y + top + 4, width: w, height: row - 12 - top, class: 'fp-' + k }, g);
        el('title', {}, rect).textContent = T.kinds[k] + ': ' + kb(r.parts[k]) + ' kB';
        x += w;
      });
      var v = el('text', { x: x + 6, y: y + top + (narrow ? 15 : 18), class: 'fp-value' }, g); v.textContent = kb(r.bytes) + ' kB';
    });
    return svg;
  }

  function legend(box, kinds) {
    var ul = document.createElement('ul'); ul.className = 'fp-legend';
    kinds.forEach(function (k) {
      var li = document.createElement('li');
      li.innerHTML = '<span class="fp-swatch fp-' + k + '"></span>' + T.kinds[k];
      ul.appendChild(li);
    });
    box.appendChild(ul);
  }

  function co2(bytes, d) { return bytes / 1e9 * d.kwh_per_gb * d.g_co2_per_kwh; }

  function table(box, list, d, served) {
    var t = document.createElement('table'); t.className = 'fp-table';
    t.innerHTML = '<thead><tr><th>' + T.version + '</th><th>' + T.kb + '</th><th>' + T.co2 + '</th><th>' + T.times + '</th><th></th></tr></thead>';
    var tb = document.createElement('tbody');
    list.forEach(function (v) {
      var tr = document.createElement('tr');
      var cells = v.missing ? [T[v.key], T.notMeasured, '', ''] :
        [T[v.key], kb(v.bytes), co2(v.bytes, d).toFixed(2), (v.bytes / served).toFixed(1) + '×'];
      cells.forEach(function (c, i) { var td = document.createElement('td'); td.textContent = c; if (i) td.className = 'num'; tr.appendChild(td); });
      var td = document.createElement('td');
      if (!v.missing) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'btn fp-play';
        b.textContent = T.listen; b.setAttribute('aria-pressed', 'false');
        b.addEventListener('click', function () { toggle(v, b); });
        td.appendChild(b);
      }
      tr.appendChild(td); tb.appendChild(tr);
    });
    t.appendChild(tb); box.appendChild(t);
  }

  /* --- sound ---------------------------------------------------------------
     One note per 25 kB, ten notes a second, so the page as served is a short
     phrase and the median web page a long one. Each kind of file has its own
     voice: the text files are high and short, the fonts a little lower, the
     photos soft and low, the video players a buzzing bass. */
  var VOICE = {
    html: { type: 'sine', f: 1046.5 }, styles: { type: 'sine', f: 1174.7 }, scripts: { type: 'sine', f: 1318.5 },
    data: { type: 'sine', f: 1568.0 }, fonts: { type: 'triangle', f: 784.0 },
    images: { type: 'sine', f: 392.0, spread: true }, other: { type: 'triangle', f: 523.3 },
    video: { type: 'sawtooth', f: 73.4, filter: 600 }, web: { type: 'triangle', f: 196.0, spread: true }
  };
  var SCALE = [1, 9 / 8, 5 / 4, 3 / 2, 5 / 3];
  var ctx = null, timer = null, current = null;

  function notes(v) {
    var seq = [];
    KINDS.forEach(function (k) {
      var n = v.parts[k] ? Math.max(1, Math.round(v.parts[k] / BYTES_PER_NOTE)) : 0;
      for (var i = 0; i < n; i += 1) seq.push(k);
    });
    return seq;
  }

  function blip(kind, when, i) {
    var v = VOICE[kind], o = ctx.createOscillator(), g = ctx.createGain(), out = g;
    o.type = v.type;
    o.frequency.value = v.f * (v.spread ? SCALE[(i * 7) % SCALE.length] : 1);
    g.gain.setValueAtTime(0.0001, when);
    g.gain.exponentialRampToValueAtTime(kind === 'video' ? 0.18 : 0.12, when + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, when + 0.09);
    o.connect(g);
    if (v.filter) { var lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = v.filter; g.connect(lp); out = lp; }
    out.connect(ctx.destination);
    o.start(when); o.stop(when + 0.1);
  }

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    if (current) { current.button.textContent = T.listen; current.button.setAttribute('aria-pressed', 'false'); }
    document.querySelectorAll('.fp-chart g.fp-active').forEach(function (g) { g.classList.remove('fp-active'); });
    fill('fp-now', '');
    current = null;
  }

  function toggle(v, button) {
    var same = current && current.button === button;
    stop();
    if (same) return;
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === 'suspended') ctx.resume();
    var seq = notes(v), i = 0, start = ctx.currentTime + 0.05, step = 1 / NOTES_PER_SECOND;
    current = { button: button };
    button.textContent = T.stop; button.setAttribute('aria-pressed', 'true');
    document.querySelectorAll('.fp-chart g[data-row="' + v.key + '"]').forEach(function (g) { g.classList.add('fp-active'); });
    fill('fp-now', T.playing + ': ' + T[v.key] + ', ' + seq.length + ' × 25 kB');
    // Schedule a little ahead in small batches, so Stop takes effect at once.
    timer = setInterval(function () {
      while (i < seq.length && start + i * step < ctx.currentTime + 0.3) { blip(seq[i], start + i * step, i); i += 1; }
      if (i >= seq.length && ctx.currentTime > start + seq.length * step) stop();
    }, 100);
  }

  /* --- this page, as measured in the reader's own browser ---------------- */
  function selfWeight() {
    if (!window.performance || !performance.getEntriesByType) return;
    var nav = performance.getEntriesByType('navigation')[0];
    var res = performance.getEntriesByType('resource');
    var bytes = (nav && nav.transferSize) || 0, cached = false;
    res.forEach(function (r) { bytes += r.transferSize || 0; if (r.transferSize === 0 && r.decodedBodySize > 0) cached = true; });
    if (!bytes) return;
    fill('fp-self', T.self.replace('{kb}', kb(bytes)).replace('{n}', res.length + 1) + (cached ? T.selfCached : ''));
  }

  /* --- put it together ---------------------------------------------------- */
  fetch(root.dataset.src).then(function (r) { return r.json(); }).then(function (d) {
    if (!d.alternatives) throw new Error('no alternatives');
    var a = d.alternatives, list = versions(d);
    fill('fp-kwh', String(d.kwh_per_gb).replace('.', nb ? ',' : '.'));
    fill('fp-g', String(d.g_co2_per_kwh));
    fill('fp-when', d.generated_at.slice(0, 10));
    fill('fp-served', kb(a.served_bytes));
    var all = list.filter(function (v) { return v.key === 'all'; })[0];
    fill('fp-all', kb(all.bytes));
    if (a.web_median) { fill('fp-web', kb(a.web_median.bytes)); fill('fp-web-date', a.web_median.date.slice(0, 7)); }
    var videoV = a.variants.filter(function (v) { return v.key === 'video'; })[0];
    fill('fp-players', videoV ? String(videoV.players) : '');

    var max = Math.max.apply(null, list.map(function (v) { return v.bytes || 0; }));
    var chartBox = document.getElementById('fp-reference');
    drawBars(chartBox, list.map(function (v) { return { key: v.key, label: T[v.key], parts: v.parts, bytes: v.bytes, missing: v.missing }; }), max, 250);
    legend(chartBox, KINDS.filter(function (k) { return list.some(function (v) { return v.parts[k]; }); }));
    table(document.getElementById('fp-table'), list, d, a.served_bytes);

    var pagesBox = document.getElementById('fp-pages');
    var rows = d.pages.map(function (p) {
      var parts = { html: p.html_bytes };
      Object.keys(p.by_kind).forEach(function (k) { parts[k] = p.by_kind[k]; });
      return { key: 'page' + p.page, label: p.page, parts: parts, bytes: p.bytes };
    });
    fill('fp-npages', String(d.pages.length));
    if (a.web_median) fill('fp-tenth', String(d.pages.filter(function (p) { return p.bytes < a.web_median.bytes / 10; }).length));
    if (a.web_median) rows.push({ key: 'web', label: T.median, parts: { web: a.web_median.bytes }, bytes: a.web_median.bytes });
    drawBars(pagesBox, rows, Math.max.apply(null, rows.map(function (r) { return r.bytes; })), 250);
  }).catch(function () {
    fill('fp-error', T.noData);
  }).then(function () {
    if (document.readyState === 'complete') selfWeight(); else window.addEventListener('load', function () { setTimeout(selfWeight, 500); });
  });
})();

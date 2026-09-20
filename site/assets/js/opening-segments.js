/* The opening ceremony, as avsegmenter heard it (/lab/opening-ceremony/).
   Draws the parts, the segment kinds, the speaker turns and the loudness from
   /assets/data/opening-ceremony-segments.json, and lets a reader open the
   recording at any point. Nothing reaches YouTube until the reader presses
   play, as on the rest of the site. No dependencies. */
(function () {
  var COLOURS = { music: '#3b82f6', speech: '#f59e0b', applause: '#10b981', silence: '#64748b', other: '#a855f7' };
  var LABELS = { music: 'Music', speech: 'Talk', applause: 'Applause', silence: 'Silence', other: 'Other' };
  var VIDEO_ID = 'rq8UnZlzYk4';

  function hms(t) {
    t = Math.max(0, Math.round(t));
    var h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
    return h + ':' + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
  }
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
  var pct = function (v) { return (v * 100).toFixed(3) + '%'; };


  /* One measured track, drawn on the same 0 to 1000 axis as every other row, so a
     bump in the motion curve sits directly under the part it happened in. Gaps in
     the measurement break the line rather than being drawn through. */
  function curveLane(curve, hop, dur) {
    var lo = curve.range[0], hi = curve.range[1], span = (hi - lo) || 1;
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'oc-curve');
    svg.setAttribute('viewBox', '0 0 1000 44');
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('aria-hidden', 'true');
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    var last = (curve.values.length - 1) || 1;
    var d = '', open = false;
    curve.values.forEach(function (v, i) {
      if (v === null) { open = false; return; }
      var x = (i / last) * 1000;
      var y = 42 - ((v - lo) / span) * 40;
      d += (open ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1) + ' ';
      open = true;
    });
    path.setAttribute('d', d.trim());
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', 'currentColor');
    path.setAttribute('stroke-width', '1');
    svg.appendChild(path);
    return el('div', { class: 'oc-lane' }, [
      el('p', { class: 'oc-lane-head small' }, [
        el('span', { class: 'oc-lane-name', text: curve.label + (curve.unit ? ' (' + curve.unit + ')' : '') }),
        el('span', { class: 'muted', text: lo + ' to ' + hi + ', ' + curve.reduced_by + ' of each ' + hop + ' s' }),
      ]),
      svg,
    ]);
  }

  function build(root, data) {
    var dur = data.video.duration;
    var player = el('div', { class: 'oc-player' });
    var at = 0;

    function poster(startAt) {
      player.textContent = '';
      var button = el('button', { type: 'button', class: 'oc-play',
        'aria-label': 'Play the recording from ' + hms(startAt) + ' on YouTube' }, [
        el('span', { class: 'oc-play-mark', 'aria-hidden': 'true', text: '▶' }),
        el('span', { class: 'oc-play-text', text: 'Play from ' + hms(startAt) }),
        el('span', { class: 'oc-play-note', text: 'YouTube loads when you press. Nothing has reached it so far.' }),
      ]);
      button.addEventListener('click', function () {
        var frame = el('iframe', {
          width: 560, height: 315, title: 'The opening ceremony',
          src: 'https://www.youtube-nocookie.com/embed/' + VIDEO_ID + '?start=' + Math.floor(startAt) + '&autoplay=1&rel=0',
          allow: 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share',
          referrerpolicy: 'strict-origin', allowfullscreen: '',
        });
        player.textContent = '';
        player.appendChild(frame);
        player.appendChild(el('p', { class: 'small muted', text: 'Showing from ' + hms(startAt) + '. Pick another point above and the player reloads there.' }));
      });
      player.appendChild(button);
    }
    function goto(t) { at = t; poster(at); player.scrollIntoView({ block: 'nearest' }); }
    poster(0);

    /* Parts, as bands across the recording */
    var partRow = el('div', { class: 'oc-row oc-parts', 'aria-hidden': 'true' });
    data.parts.forEach(function (p) {
      partRow.appendChild(el('span', {
        class: 'oc-band', title: p.title + ' (' + hms(p.start) + ')',
        style: 'left:' + pct(p.start / dur) + ';width:' + pct((p.end - p.start) / dur),
        onclick: function () { goto(p.start); },
      }, [el('span', { class: 'oc-band-label', text: String(p.index) })]));
    });

    /* What kind of sound, second by second */
    var kindRow = el('div', { class: 'oc-row oc-kinds', 'aria-hidden': 'true' });
    data.segments.forEach(function (s) {
      kindRow.appendChild(el('span', {
        class: 'oc-seg', title: (LABELS[s.kind] || s.kind) + ' ' + hms(s.start) + '–' + hms(s.end),
        style: 'left:' + pct(s.start / dur) + ';width:' + pct(Math.max(0.0008, (s.end - s.start) / dur)) + ';background:' + (COLOURS[s.kind] || '#999'),
        onclick: function () { goto(s.start); },
      }));
    });

    /* Who is speaking, by voice rather than by name */
    var turnRow = el('div', { class: 'oc-row oc-turns', 'aria-hidden': 'true' });
    data.speakers.turns.forEach(function (t) {
      var n = parseInt(String(t.speaker).replace(/\D/g, ''), 10) || 0;
      turnRow.appendChild(el('span', {
        class: 'oc-turn', title: t.speaker + ' ' + hms(t.start),
        style: 'left:' + pct(t.start / dur) + ';width:' + pct(Math.max(0.0006, (t.end - t.start) / dur)) + ';background:hsl(' + ((n * 47) % 360) + ' 60% 45%)',
        onclick: function () { goto(t.start); },
      }));
    });

    /* The title cards read off the projection */
    var cardRow = el('div', { class: 'oc-row oc-cards', 'aria-hidden': 'true' });
    (data.cards || []).forEach(function (c) {
      cardRow.appendChild(el('span', {
        class: 'oc-card', title: 'Slide at ' + hms(c.t) + ': ' + c.text,
        style: 'left:' + pct(c.t / dur) + ';width:4px',
        onclick: function () { goto(c.t); },
      }));
    });

    /* Loudness, one point per ten seconds */
    var wave = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    wave.setAttribute('class', 'oc-wave'); wave.setAttribute('viewBox', '0 0 1000 60');
    wave.setAttribute('preserveAspectRatio', 'none'); wave.setAttribute('aria-hidden', 'true');
    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    var pts = data.level_db.map(function (v, i) {
      var x = (i / (data.level_db.length - 1)) * 1000;
      var y = 60 - Math.max(0, Math.min(1, (v + 70) / 70)) * 58;
      return (i ? 'L' : 'M') + x.toFixed(1) + ' ' + y.toFixed(1);
    }).join(' ');
    path.setAttribute('d', pts); path.setAttribute('fill', 'none');
    path.setAttribute('stroke', 'currentColor'); path.setAttribute('stroke-width', '1');
    wave.appendChild(path);

    var legend = el('p', { class: 'oc-legend small' });
    Object.keys(LABELS).forEach(function (k) {
      legend.appendChild(el('span', { class: 'oc-key' }, [
        el('span', { class: 'oc-swatch', style: 'background:' + COLOURS[k], 'aria-hidden': 'true' }),
        el('span', { text: LABELS[k] }),
      ]));
    });

    /* The same information as a list, which is what a screen reader and a
       reader without JavaScript actually need. */
    var CUE_WORDS = { 'applause': 'applause', 'applause:split': 'applause', 'start': 'the start',
                      'slide': 'a title card', 'spoken': 'the host announcing it',
                      'break': 'a break', 'break-end': 'a break' };
    var list = el('ol', { class: 'oc-list' });
    data.parts.forEach(function (p) {
      var cue = (p.cues || []).map(function (c) {
        return CUE_WORDS[c] || (c.indexOf('speaker:') === 0 ? 'a voice taking over' : c);
      })[0] || '';
      var meta = ' · ' + hms(p.end - p.start) + ' · ' + Math.round(p.speech_share * 100) + '% talk'
        + (cue ? ' · cut at ' + cue : '')
        + (p.performers ? ' · ' + p.performers : '');
      list.appendChild(el('li', {}, [
        el('button', { type: 'button', class: 'oc-jump', text: hms(p.start), onclick: function () { goto(p.start); },
                       'aria-label': 'Play from ' + hms(p.start) + ', ' + (p.title || 'part ' + p.index) }),
        el('span', { class: 'oc-list-title', text: ' ' + (p.title || 'Part ' + p.index) }),
        el('span', { class: 'oc-list-meta', text: meta }),
        p.named ? null : el('span', { class: 'oc-list-meta', text: ' · nobody was named here, so no act is claimed' }),
      ]));
    });

    /* Two panels, as in the player the toolbox writes: what the analysis holds
       beyond this page, and the technical, rights and quality facts. */
    function row(term, value) {
      if (value == null || value === '') return null;
      return el('div', { class: 'oc-fact' }, [
        el('dt', { text: term }), el('dd', { text: String(value) }),
      ]);
    }
    function mb(n) { return n ? (n / 1048576).toFixed(0) + ' MB' : null; }

    var t = data.tech || {}, lo = data.loudness || {}, rights = data.rights || {}, tools = data.tools || {};
    var facts = el('dl', { class: 'oc-facts' }, [
      row('Duration', hms(dur)),
      row('Picture', t.width ? t.width + ' × ' + t.height + ', ' + t.fps + ' frames per second, ' + (t.video_codec || '') : null),
      row('Sound', t.audio_codec ? t.audio_codec + ', ' + (t.sample_rate_hz / 1000) + ' kHz, ' + t.channels + ' channels' : null),
      row('File', t.container ? t.container + ', ' + mb(t.size_bytes) + ', ' + t.bitrate_kbps + ' kbit/s' : null),
      row('Loudness', lo.integrated_lufs != null ? lo.integrated_lufs + ' LUFS integrated, range ' + lo.loudness_range_lu + ' LU, true peak ' + lo.true_peak_dbtp + ' dBTP (' + (lo.standard || '') + ')' : null),
      row('Analysed with', 'avsegmenter, on musicalgestures ' + (tools.musicalgestures || '') + ', ambiscape ' + (tools.ambiscape || '') + ', musiscape ' + (tools.musiscape || '')),
      row('Rights holder', rights.rights_holder),
      row('Licence of the recording', rights.license),
      row('Privacy', rights.privacy ? rights.privacy + ': ' + (rights.privacy_note || '') : null),
    ].filter(Boolean));

    var checks = el('ul', { class: 'oc-checks' }, (data.qc || []).map(function (c) {
      return el('li', { text: (c.label || c.id) + ': ' + c.outcome + (c.count != null ? ' (' + c.count + ')' : '') });
    }));

    var metaBox = el('details', { class: 'oc-box' }, [
      el('summary', { text: 'Technical facts, rights and quality checks' }),
      facts,
      el('h3', { text: 'Quality checks', class: 'oc-box-h' }),
      el('p', { class: 'small muted', text: 'A subset of the EBU Tech 3363 checks, measured with ffmpeg filters. The one silence is eight seconds at 18:23, as the stage was set for the second performance. The black frames are at 1:08:56 and at the very end.' }),
      checks,
    ]);

    var hop = data.curve_hop_s || 10;
    var curveBox = el('div', { class: 'oc-lanes' }, (data.curves || []).map(function (c) {
      return curveLane(c, hop, dur);
    }));
    if (data.curves && data.curves.length) {
      curveBox.appendChild(el('p', { class: 'small muted', text: 'Every curve runs the whole ' + hms(dur) + ' on the same axis as the bands above, one point per ' + hop + ' seconds. A curve is a shape, not a reading: the numbers beside each name are the range it covers, and the analysis file holds the values.' }));
    }
    if (data.curves_empty && data.curves_empty.labels.length) {
      curveBox.appendChild(el('p', { class: 'small muted', text: data.curves_empty.labels.join(' and ') + ' are not drawn. ' + data.curves_empty.why }));
    }

    var tracks = el('ul', { class: 'oc-tracks' }, (data.research.tracks || []).map(function (tr) {
      return el('li', { text: tr.label + (tr.unit ? ' (' + tr.unit + ')' : '') + ' · ' + tr.kind + (tr.source ? ' · ' + tr.source : '') });
    }));
    var tiers = el('ul', { class: 'oc-tracks' }, (data.research.tiers || []).map(function (ti) {
      return el('li', { text: ti.label + ' · ' + ti.items + ' items' + (ti.source ? ' · ' + ti.source : '') });
    }));
    var pics = el('div', { class: 'oc-pics' }, (data.pictures || []).map(function (pic) {
      return el('figure', {}, [
        el('img', { src: pic.src, alt: pic.label, loading: 'lazy' }),
        el('figcaption', { class: 'small muted', text: pic.label }),
      ]);
    }));

    var advancedBox = el('details', { class: 'oc-box' }, [
      el('summary', { text: 'Advanced view: what the analysis holds' }),
      el('p', { class: 'small', text: 'The timeline above is a selection. The analysis carries ' + (data.research.tracks || []).length + ' measured tracks and ' + (data.research.tiers || []).length + ' layers of marks, each from a named tool, and the whole of it is in the JSON file this page reads.' }),
      el('h3', { text: 'The recording as pictures', class: 'oc-box-h' }),
      pics,
      el('h3', { text: 'Measured through the recording', class: 'oc-box-h' }),
      curveBox,
      tracks,
      el('h3', { text: 'Marked on the recording', class: 'oc-box-h' }),
      tiers,
      el('p', { class: 'small muted' }, [
        document.createTextNode('The full analysis is in '),
        el('a', { href: '/assets/data/opening-ceremony-segments.json', text: 'the file behind this page' }),
        document.createTextNode('. The player that the toolbox writes shows the same layers against the video itself.'),
      ]),
    ]);

    root.textContent = '';
    root.appendChild(player);
    root.appendChild(legend);
    root.appendChild(el('div', { class: 'oc-stack' }, [partRow, cardRow, kindRow, turnRow, wave]));
    root.appendChild(el('p', { class: 'small muted', text: 'Bands: the parts the pipeline found. Marks below them: the title cards it read off the projection. Strip: what it heard, second by second. Row below: turns by voice, coloured by cluster, not named. Line: loudness, one point per ten seconds. Click anywhere to set where the recording starts.' }));
    root.appendChild(list);
    root.appendChild(advancedBox);
    root.appendChild(metaBox);
  }

  var root = document.getElementById('opening-segments');
  if (!root) return;
  fetch('/assets/data/opening-ceremony-segments.json')
    .then(function (r) { return r.json(); })
    .then(function (d) { build(root, d); })
    .catch(function () { root.textContent = 'The analysis file could not be loaded.'; });
})();

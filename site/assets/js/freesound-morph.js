/* Two sounds from Freesound, convolved (/lab/sound-actions/).

   Convolution takes every moment of one sound and sets the other sound ringing at that moment.
   Where one of the two is short and sharp, the result sounds like the other played in the room
   that the first one implies. Where both are long, they smear into each other. The browser does
   the work with the Web Audio API; there is no library, and nothing is fetched from Freesound
   until a reader presses a button.

   Each sound is drawn as a waveform. The shape of a sound that has not been fetched comes from
   128 peak values measured at build time by scripts/sync_freesound.py, so a reader can see what a
   sound looks like without Freesound learning that anyone looked. Once a sound has been fetched
   the drawing is redone from the decoded audio itself, and the convolution is drawn the same way,
   since it exists only here. */
(function () {
  var ctx = null, buffers = {}, playing = null;
  var WAVE = 128;                                  // peaks per drawing, as measured at build time
  var head = { canvas: null, at: 0, duration: 0, frame: 0 };

  function ac() {
    if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
    return ctx;
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


  /* The same reduction the build step does, so a fetched sound is drawn the way its stored
     shape was: the peak of each slice, not the mean, because these recordings are transients. */
  function peaksOf(buffer, count) {
    var d = buffer.getChannelData(0);
    var step = Math.max(1, Math.floor(d.length / count));
    var out = [], loudest = 0, i, j;
    for (i = 0; i < count; i++) {
      var peak = 0;
      for (j = i * step; j < (i + 1) * step && j < d.length; j++) {
        var v = Math.abs(d[j]); if (v > peak) peak = v;
      }
      out.push(peak); if (peak > loudest) loudest = peak;
    }
    if (!loudest) loudest = 1;
    return out.map(function (p) { return Math.min(255, Math.round(p / loudest * 255)); });
  }

  function token(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  /* Drawn as a mirrored envelope. The part already played is inked, the rest is not, so the
     playhead is the edge between the two and needs no line of its own. */
  function draw(canvas, through) {
    var peaks = canvas.peaks;
    var ratio = window.devicePixelRatio || 1;
    var w = Math.max(1, Math.round(canvas.clientWidth * ratio));
    var h = Math.max(1, Math.round(canvas.clientHeight * ratio));
    /* Sized even when there is nothing to draw yet, so an empty box is the right
       shape rather than the 300 by 150 a canvas defaults to. */
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    var g = canvas.getContext('2d');
    g.clearRect(0, 0, w, h);
    if (!peaks || !peaks.length) return;
    var mid = h / 2, gap = Math.max(1, Math.round(ratio));
    var bar = w / peaks.length;
    var played = typeof through === 'number' ? through * peaks.length : -1;
    for (var i = 0; i < peaks.length; i++) {
      var tall = Math.max(ratio, (peaks[i] / 255) * (h / 2 - ratio));
      g.fillStyle = i < played ? token('--mm-ink', '#231f20') : token('--mm-purple', '#9a90cf');
      g.fillRect(Math.round(i * bar), Math.round(mid - tall), Math.max(1, Math.round(bar) - gap), Math.round(tall * 2));
    }
  }

  function wave(label) {
    var canvas = el('canvas', { class: 'fs-wave', role: 'img', 'aria-label': label });
    canvas.peaks = null;
    return canvas;
  }

  function show(canvas, peaks, label) {
    canvas.peaks = peaks || null;
    canvas.setAttribute('aria-label', label);
    draw(canvas);
  }

  /* While something plays, ink the waveform up to where it has got to. */
  function follow(canvas, duration) {
    cancelAnimationFrame(head.frame);
    head.canvas = canvas; head.duration = duration; head.at = ac().currentTime;
    if (!canvas) return;
    (function step() {
      if (head.canvas !== canvas) return;
      var through = (ac().currentTime - head.at) / duration;
      if (through >= 1) { draw(canvas); head.canvas = null; return; }
      draw(canvas, through);
      head.frame = requestAnimationFrame(step);
    })();
  }

  function load(sound, say) {
    if (buffers[sound.id]) return Promise.resolve(buffers[sound.id]);
    say('Fetching ' + sound.title + ' from Freesound…');
    return fetch(sound.preview)
      .then(function (r) { if (!r.ok) throw new Error('Freesound answered ' + r.status); return r.arrayBuffer(); })
      .then(function (bytes) { return ac().decodeAudioData(bytes); })
      .then(function (buf) { buffers[sound.id] = buf; return buf; });
  }

  function stop() {
    if (playing) { try { playing.stop(); } catch (e) {} playing = null; }
    cancelAnimationFrame(head.frame);
    if (head.canvas) { var c = head.canvas; head.canvas = null; draw(c); }
  }

  function play(buffer, canvas) {
    stop();
    var src = ac().createBufferSource();
    src.buffer = buffer;
    src.connect(ac().destination);
    src.start();
    playing = src;
    if (canvas) follow(canvas, buffer.duration);
    return src;
  }

  /* A convolved with B, rendered offline so that the result can be levelled before it is heard. */
  function convolve(a, b) {
    var rate = ac().sampleRate;
    var length = Math.min(rate * 30, Math.ceil((a.duration + b.duration) * rate));
    var off = new OfflineAudioContext(1, length, rate);
    var src = off.createBufferSource();
    src.buffer = a;
    var conv = off.createConvolver();
    conv.normalize = true;
    conv.buffer = b;
    src.connect(conv);
    conv.connect(off.destination);
    src.start();
    return off.startRendering().then(function (out) {
      var d = out.getChannelData(0), peak = 0;
      for (var i = 0; i < d.length; i++) { var v = Math.abs(d[i]); if (v > peak) peak = v; }
      if (peak > 0) { var g = 0.9 / peak; for (var j = 0; j < d.length; j++) d[j] *= g; }
      return out;
    });
  }

  function build(root, sounds) {
    var status = el('p', { class: 'fs-status small muted', text: 'Nothing has been fetched from Freesound yet.' });
    function say(t) { status.textContent = t; }

    function picker(id, label, chosen) {
      var sel = el('select', { id: id, class: 'fs-select' }, sounds.map(function (s, i) {
        return el('option', { value: String(i), text: s.title, selected: i === chosen ? '' : null });
      }));
      return el('p', { class: 'fs-pick' }, [el('label', { for: id, text: label + ' ' }), sel]);
    }
    var a = picker('fs-a', 'First sound', 0);
    var b = picker('fs-b', 'Second sound', 2);
    var pickA = a.querySelector('select'), pickB = b.querySelector('select');
    var current = function () { return [sounds[+pickA.value], sounds[+pickB.value]]; };

    var waveA = wave(''), waveB = wave(''), waveOut = wave('The convolution has not been made yet.');
    function describe(s) {
      return 'Waveform of ' + s.title + ', ' + (s.duration ? s.duration.toFixed(1) + ' seconds' : 'length unknown') + '.';
    }
    function shapes() {
      var pair = current();
      show(waveA, pair[0].peaks, describe(pair[0]));
      show(waveB, pair[1].peaks, describe(pair[1]));
    }

    function credit() {
      var pair = current();
      creditBox.textContent = '';
      pair.forEach(function (s) {
        creditBox.appendChild(el('li', {}, [
          el('a', { href: s.page, text: s.title }),
          document.createTextNode(' by ' + (s.author || 'unknown') + ', '),
          el('a', { href: s.licence_url, text: s.licence }),
        ]));
      });
    }
    var creditBox = el('ul', { class: 'fs-credits small' });
    pickA.addEventListener('change', function () { credit(); shapes(); });
    pickB.addEventListener('change', function () { credit(); shapes(); });

    function button(text, fn) {
      return el('button', { type: 'button', class: 'fs-btn', text: text, onclick: function () {
        fn().catch(function (e) { say('That did not work: ' + e.message); });
      } });
    }

    function playOne(which, canvas) {
      var s = current()[which];
      return load(s, say).then(function (buf) {
        /* Now that the sound itself is here, draw it rather than its stored shape. */
        show(canvas, peaksOf(buf, WAVE), describe(s));
        play(buf, canvas);
        say('Playing ' + s.title + '.');
      });
    }
    var playA = button('Play the first', function () { return playOne(0, waveA); });
    var playB = button('Play the second', function () { return playOne(1, waveB); });
    var morph = button('Convolve them', function () {
      var pair = current();
      say('Fetching both sounds…');
      return Promise.all([load(pair[0], say), load(pair[1], say)]).then(function (bufs) {
        say('Convolving ' + pair[0].title + ' with ' + pair[1].title + '…');
        return convolve(bufs[0], bufs[1]);
      }).then(function (out) {
        show(waveOut, peaksOf(out, WAVE), 'Waveform of the convolution, ' + out.duration.toFixed(1) + ' seconds.');
        play(out, waveOut);
        say('Playing the convolution, ' + out.duration.toFixed(1) + ' seconds. Swap the order and it sounds different.');
      });
    });
    var hush = button('Stop', function () { stop(); say('Stopped.'); return Promise.resolve(); });

    root.textContent = '';
    root.appendChild(a);
    root.appendChild(waveA);
    root.appendChild(b);
    root.appendChild(waveB);
    root.appendChild(el('p', { class: 'fs-buttons' }, [playA, playB, morph, hush]));
    root.appendChild(el('p', { class: 'fs-wave-label small muted', text: 'The convolution' }));
    root.appendChild(waveOut);
    root.appendChild(status);
    root.appendChild(creditBox);
    credit();
    shapes();
    draw(waveOut);                               // empty, but the right shape and size
    /* A canvas has no layout of its own, so a resize needs the drawing back. */
    var again;
    window.addEventListener('resize', function () {
      clearTimeout(again);
      again = setTimeout(function () { [waveA, waveB, waveOut].forEach(function (c) { draw(c); }); }, 150);
    });
  }

  var root = document.getElementById('freesound-morph');
  if (!root) return;
  var data = document.getElementById('freesound-data');
  if (!data) return;
  try {
    build(root, JSON.parse(data.textContent).sounds);
  } catch (e) {
    root.textContent = 'The list of sounds could not be read.';
  }
})();

/* Two sounds from Freesound, convolved (/lab/sound-actions/).

   Convolution takes every moment of one sound and sets the other sound ringing at that moment.
   Where one of the two is short and sharp, the result sounds like the other played in the room
   that the first one implies. Where both are long, they smear into each other. The browser does
   the work with the Web Audio API; there is no library, and nothing is fetched from Freesound
   until a reader presses a button. */
(function () {
  var ctx = null, buffers = {}, playing = null;

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
  }

  function play(buffer) {
    stop();
    var src = ac().createBufferSource();
    src.buffer = buffer;
    src.connect(ac().destination);
    src.start();
    playing = src;
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
    pickA.addEventListener('change', credit);
    pickB.addEventListener('change', credit);

    function button(text, fn) {
      return el('button', { type: 'button', class: 'fs-btn', text: text, onclick: function () {
        fn().catch(function (e) { say('That did not work: ' + e.message); });
      } });
    }

    var playA = button('Play the first', function () {
      var s = current()[0];
      return load(s, say).then(function (buf) { play(buf); say('Playing ' + s.title + '.'); });
    });
    var playB = button('Play the second', function () {
      var s = current()[1];
      return load(s, say).then(function (buf) { play(buf); say('Playing ' + s.title + '.'); });
    });
    var morph = button('Convolve them', function () {
      var pair = current();
      say('Fetching both sounds…');
      return Promise.all([load(pair[0], say), load(pair[1], say)]).then(function (bufs) {
        say('Convolving ' + pair[0].title + ' with ' + pair[1].title + '…');
        return convolve(bufs[0], bufs[1]);
      }).then(function (out) {
        play(out);
        say('Playing the convolution, ' + out.duration.toFixed(1) + ' seconds. Swap the order and it sounds different.');
      });
    });
    var hush = button('Stop', function () { stop(); say('Stopped.'); return Promise.resolve(); });

    root.textContent = '';
    root.appendChild(a);
    root.appendChild(b);
    root.appendChild(el('p', { class: 'fs-buttons' }, [playA, playB, morph, hush]));
    root.appendChild(status);
    root.appendChild(creditBox);
    credit();
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

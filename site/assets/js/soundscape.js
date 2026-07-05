/* A soundscape of the MishMash publication stream (issue #27, first sketch).
   Results are sequenced chronologically: one note-event per result, timbre
   from the result type, chord size from the number of contributors, pitch
   from the lead institution. Data and strings are inlined by
   _includes/soundscape.html. */
(function () {
"use strict";

var STEP = 0.5;          /* seconds between result onsets */
var BASE = 220;          /* A3 */
var PENTA = [0, 2, 4, 7, 9]; /* major pentatonic — stays consonant */

/* result type → voice character */
var VOICES = {
  "Lecture":              { type: "sine",     dur: 0.35, gain: 0.30 },
  "Conference":           { type: "sine",     dur: 0.45, gain: 0.30 },
  "Media":                { type: "square",   dur: 0.12, gain: 0.10 },
  "Journal article":      { type: "triangle", dur: 1.2,  gain: 0.35 },
  "Book chapter":         { type: "triangle", dur: 0.9,  gain: 0.35 },
  "Letter to the editor": { type: "square",   dur: 0.25, gain: 0.12 },
  "Exhibition":           { type: "sawtooth", dur: 1.6,  gain: 0.16 },
  "Music performance":    { type: "sawtooth", dur: 1.6,  gain: 0.16 }
};
var DEFAULT_VOICE = { type: "sine", dur: 0.4, gain: 0.28 };

function hashCode(s) {
  var h = 0;
  for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

/* scale degree → frequency, over ~2.5 octaves */
function freq(degree) {
  var octave = Math.floor(degree / PENTA.length) % 3;
  var semis = PENTA[degree % PENTA.length] + 12 * octave;
  return BASE * Math.pow(2, semis / 12);
}

var events = SOUNDSCAPE_RESULTS.slice().sort(function (a, b) {
  return a.y < b.y ? -1 : a.y > b.y ? 1 : (a.t < b.t ? -1 : 1);
});

var ctx = null;
var master = null;
var timers = [];
var playing = false;

var playBtn = document.getElementById("scape-play");
var nowEl = document.getElementById("scape-now");
var volEl = document.getElementById("scape-volume");
var progressEl = document.getElementById("scape-progress");

function note(when, f, voice) {
  var osc = ctx.createOscillator();
  var env = ctx.createGain();
  osc.type = voice.type;
  osc.frequency.value = f;
  env.gain.setValueAtTime(0, when);
  env.gain.linearRampToValueAtTime(voice.gain, when + 0.015);
  env.gain.exponentialRampToValueAtTime(0.001, when + voice.dur);
  osc.connect(env);
  env.connect(master);
  osc.start(when);
  osc.stop(when + voice.dur + 0.05);
}

function playEvent(r, when) {
  var voice = VOICES[r.g] || DEFAULT_VOICE;
  var degree = hashCode(r.i || r.t) % (PENTA.length * 3);
  var chord = Math.min(Math.max(r.n, 1), 4); /* co-authorship as harmony */
  for (var v = 0; v < chord; v++) {
    /* stack pentatonic thirds above the root */
    note(when, freq(degree + v * 2), voice);
  }
}

function stop() {
  playing = false;
  timers.forEach(clearTimeout);
  timers = [];
  if (ctx) { ctx.close(); ctx = null; }
  playBtn.textContent = SCAPE_STR.play;
  playBtn.setAttribute("aria-pressed", "false");
  nowEl.textContent = "";
  progressEl.value = 0;
}

function play() {
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  master = ctx.createGain();
  master.gain.value = parseFloat(volEl.value);
  master.connect(ctx.destination);
  playing = true;
  playBtn.textContent = SCAPE_STR.stop;
  playBtn.setAttribute("aria-pressed", "true");

  var t0 = ctx.currentTime + 0.1;
  events.forEach(function (r, i) {
    var when = t0 + i * STEP;
    playEvent(r, when);
    timers.push(setTimeout(function () {
      if (!playing) return;
      nowEl.textContent = r.t + " (" + r.y + " · " + r.g + ")";
      progressEl.value = i + 1;
    }, Math.max((when - ctx.currentTime) * 1000, 0)));
  });
  timers.push(setTimeout(function () {
    if (playing) stop();
  }, (events.length * STEP + 2.5) * 1000));
}

playBtn.addEventListener("click", function () {
  if (playing) { stop(); } else { play(); }
});

volEl.addEventListener("input", function () {
  if (master) master.gain.value = parseFloat(volEl.value);
});

progressEl.max = events.length;
document.getElementById("scape-count").textContent = events.length;

})();

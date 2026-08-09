(function () {
  "use strict";

  const toggleBtn = document.getElementById("sfa-sound-toggle");
  const panel = document.getElementById("sfa-sonic-panel");
  const queryInput = document.getElementById("sfa-query-input");
  const fetchBtn = document.getElementById("sfa-fetch-btn");
  const statusEl = document.getElementById("sfa-sonic-status");
  const resultsEl = document.getElementById("sfa-sound-results");

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx || !toggleBtn) {
    return;
  }

  const state = {
    enabled: false,
    buffers: [],
    grainTimer: null,
    autoLoaded: false,
    golMetrics: {
      generation: 0,
      density: 0.18,
      births: 0,
      deaths: 0,
      entropy: 0.6,
      seed: (window.SFA_THEME_STATE && window.SFA_THEME_STATE.seed) || Math.floor(Math.random() * 1e9)
    },
    query: "",
    token: "",
    rngState: 0,
    scene: null,
    resolvedQuery: "",
    pointer: { x: 0.5, y: 0.5 },
    pointerMap: null,
    selectedSample: null,
    audioTintBase: {
      bg: 95,
      accent: 34,
      accent2: 44
    }
  };

  const embeddedToken = typeof window.SFA_FREESOUND_TOKEN === "string"
    ? window.SFA_FREESOUND_TOKEN.trim()
    : "";
  const defaultQueries = ["glass insects choir", "metal leaves choir", "radio water sparks", "wind circuit bells"];
  const fallbackQueries = ["glass", "water", "wind", "metal", "piano", "voice"];
  const STORAGE_KEY = "sfa_selected_sample";
  const scenes = [
    {
      name: "bloom",
      intervalBase: 74,
      intervalSpread: 18,
      synthTypes: ["triangle", "sine"],
      dry: 0.78,
      fx: 0.52,
      feedback: 0.22,
      reverb: 0.34,
      burstBase: 3,
      burstRange: 4
    },
    {
      name: "shatter",
      intervalBase: 42,
      intervalSpread: 20,
      synthTypes: ["sawtooth", "triangle"],
      dry: 0.66,
      fx: 0.64,
      feedback: 0.38,
      reverb: 0.22,
      burstBase: 7,
      burstRange: 8
    },
    {
      name: "drift",
      intervalBase: 112,
      intervalSpread: 26,
      synthTypes: ["sine", "triangle"],
      dry: 0.72,
      fx: 0.48,
      feedback: 0.28,
      reverb: 0.42,
      burstBase: 2,
      burstRange: 3
    }
  ];

  state.rngState = (state.golMetrics.seed ^ 0x9e3779b9) >>> 0;

  function rng() {
    state.rngState = (1664525 * state.rngState + 1013904223) >>> 0;
    return state.rngState / 4294967296;
  }

  state.scene = scenes[Math.floor(rng() * scenes.length)];
  const defaultQuery = defaultQueries[Math.floor(rng() * defaultQueries.length)];
  state.pointerMap = {
    grainRateFromX: 0.55 + rng() * 1.75,
    grainRateFromY: 0.35 + rng() * 1.55,
    pitchFromX: 0.28 + rng() * 1.35,
    pitchFromY: -0.2 - rng() * 0.95,
    filterFromX: 0.7 + rng() * 1.8,
    filterFromY: 0.55 + rng() * 1.45,
    panFromX: 0.8 + rng() * 1.1,
    panFromY: 0.2 + rng() * 0.8,
    delayFromX: 0.05 + rng() * 0.28,
    delayFromY: 0.06 + rng() * 0.32,
    feedbackFromX: 0.04 + rng() * 0.18,
    feedbackFromY: 0.06 + rng() * 0.22,
    reverbFromX: 0.03 + rng() * 0.22,
    reverbFromY: 0.04 + rng() * 0.26
  };

  const context = new AudioCtx();
  const masterGain = context.createGain();
  const dryGain = context.createGain();
  const fxSendGain = context.createGain();
  const delayNode = context.createDelay(1.4);
  const delayFeedback = context.createGain();
  const delayWet = context.createGain();
  const convolver = context.createConvolver();
  const reverbWet = context.createGain();
  const analyser = context.createAnalyser();

  analyser.fftSize = 1024;
  analyser.smoothingTimeConstant = 0.72;

  masterGain.gain.value = 0.001;
  dryGain.gain.value = state.scene.dry;
  fxSendGain.gain.value = state.scene.fx;
  delayNode.delayTime.value = 0.22;
  delayFeedback.gain.value = state.scene.feedback;
  delayWet.gain.value = 0.18;
  reverbWet.gain.value = state.scene.reverb;

  dryGain.connect(masterGain);
  fxSendGain.connect(delayNode);
  fxSendGain.connect(convolver);
  delayNode.connect(delayFeedback);
  delayFeedback.connect(delayNode);
  delayNode.connect(delayWet);
  convolver.connect(reverbWet);
  delayWet.connect(masterGain);
  reverbWet.connect(masterGain);
  masterGain.connect(analyser);
  analyser.connect(context.destination);

  function buildImpulse(seconds, decay) {
    const length = Math.max(1, Math.floor(context.sampleRate * seconds));
    const impulse = context.createBuffer(2, length, context.sampleRate);
    for (let channel = 0; channel < impulse.numberOfChannels; channel += 1) {
      const channelData = impulse.getChannelData(channel);
      for (let i = 0; i < length; i += 1) {
        const t = i / length;
        channelData[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, decay);
      }
    }
    return impulse;
  }

  convolver.buffer = buildImpulse(2.8, 2.4);

  function setStatus(text, isError) {
    if (!statusEl) return;
    statusEl.textContent = text;
    statusEl.classList.toggle("is-error", !!isError);
  }

  function refreshToggleUi() {
    toggleBtn.classList.toggle("is-on", state.enabled);
    toggleBtn.setAttribute("aria-pressed", state.enabled ? "true" : "false");
    toggleBtn.textContent = state.enabled ? "Sound On" : "Sound Off";
  }

  function startScheduler() {
    if (state.grainTimer) return;
    state.grainTimer = window.setInterval(function () {
      if (!state.enabled || context.state !== "running") {
        return;
      }
      const params = sonicParams();
      const burstCount = Math.max(
        1,
        state.scene.burstBase
          + Math.floor(params.activity * 16)
          + Math.floor(params.density * state.scene.burstRange)
          + Math.floor((state.pointer.x + state.pointer.y) * 7)
      );
      for (let index = 0; index < burstCount; index += 1) {
        if (state.buffers.length) triggerSampleGrain(index, burstCount);
        else triggerFallbackVoice(index, burstCount);
      }
      publishAudioMetrics();
    }, Math.max(24, state.scene.intervalBase - Math.floor(state.pointer.y * 18) + Math.floor(rng() * state.scene.intervalSpread)));
  }

  function stopScheduler() {
    if (!state.grainTimer) return;
    window.clearInterval(state.grainTimer);
    state.grainTimer = null;
  }

  function setSoundEnabled(nextEnabled) {
    state.enabled = !!nextEnabled;
    localStorage.setItem("sfa_sound_enabled", state.enabled ? "1" : "0");

    if (state.enabled) {
      context.resume().catch(function () { return null; });
      const now = context.currentTime;
      masterGain.gain.cancelScheduledValues(now);
      masterGain.gain.setTargetAtTime(0.85, now, 0.2);
      startScheduler();
      setStatus("Sound active. The Life grid now drives granular playback.", false);
    } else {
      const now = context.currentTime;
      masterGain.gain.cancelScheduledValues(now);
      masterGain.gain.setTargetAtTime(0.0001, now, 0.12);
      stopScheduler();
      setStatus("Sound muted. Switch Sound On to resume.", false);
    }

    refreshToggleUi();
  }

  function createVoiceChain() {
    const gainNode = context.createGain();
    const filterNode = context.createBiquadFilter();
    const pannerNode = context.createStereoPanner();

    filterNode.type = "bandpass";
    filterNode.Q.value = 0.6 + rng() * 7;

    filterNode.connect(gainNode);
    gainNode.connect(pannerNode);
    pannerNode.connect(dryGain);
    pannerNode.connect(fxSendGain);

    return { gainNode: gainNode, filterNode: filterNode, pannerNode: pannerNode };
  }

  function sonicParams() {
    const metrics = state.golMetrics;
    const density = Math.max(0, Math.min(1, metrics.density || 0));
    const entropy = Math.max(0, Math.min(1, (metrics.entropy || 0.7) / 1.2));
    const activity = Math.max(0, Math.min(1, ((metrics.births || 0) + (metrics.deaths || 0)) / 120));
    const x = state.pointer.x;
    const y = state.pointer.y;
    const matrix = state.pointerMap;
    const grainDrive = Math.max(0.2, x * matrix.grainRateFromX + y * matrix.grainRateFromY);
    const pitchWarp = x * matrix.pitchFromX + y * matrix.pitchFromY;
    const filterWarp = x * matrix.filterFromX + y * matrix.filterFromY;
    const panWarp = (x - 0.5) * matrix.panFromX + (y - 0.5) * matrix.panFromY;
    const delayWarp = x * matrix.delayFromX + y * matrix.delayFromY;
    const feedbackWarp = x * matrix.feedbackFromX + y * matrix.feedbackFromY;
    const reverbWarp = x * matrix.reverbFromX + y * matrix.reverbFromY;

    return {
      density: density,
      entropy: entropy,
      activity: activity,
      x: x,
      y: y,
      grainDrive: grainDrive,
      pitchWarp: pitchWarp,
      filterWarp: filterWarp,
      panWarp: panWarp,
      delayWarp: delayWarp,
      feedbackWarp: feedbackWarp,
      reverbWarp: reverbWarp
    };
  }

  function applyFx(now, params) {
    delayNode.delayTime.setTargetAtTime(
      0.05 + params.entropy * 0.28 + params.delayWarp + rng() * 0.02,
      now,
      0.05
    );
    delayFeedback.gain.setTargetAtTime(
      Math.min(0.92, state.scene.feedback + params.activity * 0.26 + params.feedbackWarp),
      now,
      0.08
    );
    reverbWet.gain.setTargetAtTime(
      Math.min(0.92, state.scene.reverb + params.density * 0.18 + params.reverbWarp),
      now,
      0.1
    );
  }

  function triggerSampleGrain(index, burstCount) {
    const buffer = state.buffers[0];
    if (!buffer || !buffer.duration) return;

    const source = context.createBufferSource();
    source.buffer = buffer;

    const voice = createVoiceChain();
    const params = sonicParams();
    const density = params.density;
    const entropy = params.entropy;
    const activity = params.activity;

    const grainDuration = 0.02 + density * 0.08 + entropy * 0.05 + params.grainDrive * 0.028 + rng() * 0.02;
    const maxOffset = Math.max(0.01, buffer.duration - grainDuration - 0.01);
    const offset = rng() * maxOffset;
    const now = context.currentTime + index * 0.009;
    const playbackRate = Math.max(0.18, 0.42 + entropy * 1.05 + params.pitchWarp + (rng() - 0.5) * 0.36);
    const spread = burstCount > 1 ? (index / (burstCount - 1)) * 2 - 1 : 0;
    const pan = Math.max(-1, Math.min(1, spread * (0.45 + activity * 0.55) + params.panWarp + (rng() - 0.5) * 0.16));

    voice.filterNode.frequency.setValueAtTime(180 + density * 1800 + entropy * 900 + params.filterWarp * 520, now);
    voice.pannerNode.pan.setValueAtTime(pan, now);

    const peak = Math.max(0.02, 0.025 + 0.055 * density + 0.04 * activity);
    voice.gainNode.gain.setValueAtTime(0.0001, now);
    voice.gainNode.gain.linearRampToValueAtTime(peak, now + Math.max(0.01, grainDuration * 0.38));
    voice.gainNode.gain.exponentialRampToValueAtTime(0.0001, now + grainDuration);

    applyFx(now, params);

    source.playbackRate.setValueAtTime(playbackRate, now);
    source.connect(voice.filterNode);
    source.start(now, offset, grainDuration);
    source.stop(now + grainDuration + 0.03);

    source.onended = function () {
      try {
        source.disconnect();
        voice.filterNode.disconnect();
        voice.gainNode.disconnect();
        voice.pannerNode.disconnect();
      } catch (error) {
        return null;
      }
      return null;
    };
  }

  function triggerFallbackVoice(index, burstCount) {
    const now = context.currentTime + index * 0.01;
    const voice = createVoiceChain();
    const params = sonicParams();
    const density = params.density;
    const entropy = params.entropy;
    const activity = params.activity;
    const duration = 0.05 + density * 0.1 + rng() * 0.03;

    const osc = context.createOscillator();
    const mod = context.createOscillator();
    const modGain = context.createGain();

    osc.type = state.scene.synthTypes[Math.floor(rng() * state.scene.synthTypes.length)];
    mod.type = "sine";

    const baseFreq = Math.max(45, 74 + density * 260 + entropy * 180 + params.pitchWarp * 140 + Math.floor(rng() * 5) * 41);
    const modFreq = 3 + entropy * 26;
    const modDepth = 8 + activity * 80;
    const spread = burstCount > 1 ? (index / (burstCount - 1)) * 2 - 1 : 0;
    const pan = Math.max(-1, Math.min(1, spread * (0.35 + activity * 0.45) + params.panWarp + (rng() - 0.5) * 0.16));
    const peak = 0.012 + density * 0.028 + activity * 0.022;

    mod.frequency.setValueAtTime(modFreq, now);
    modGain.gain.setValueAtTime(modDepth, now);
    mod.connect(modGain);
    modGain.connect(osc.frequency);

    osc.frequency.setValueAtTime(baseFreq, now);
    voice.filterNode.frequency.setValueAtTime(160 + density * 1300 + entropy * 1100 + params.filterWarp * 440, now);
    voice.pannerNode.pan.setValueAtTime(pan, now);
    voice.gainNode.gain.setValueAtTime(0.0001, now);
    voice.gainNode.gain.linearRampToValueAtTime(peak, now + 0.02);
    voice.gainNode.gain.exponentialRampToValueAtTime(0.0001, now + duration);

    applyFx(now, params);

    osc.connect(voice.filterNode);
    osc.start(now);
    mod.start(now);
    osc.stop(now + duration + 0.02);
    mod.stop(now + duration + 0.02);

    osc.onended = function () {
      try {
        osc.disconnect();
        mod.disconnect();
        modGain.disconnect();
        voice.filterNode.disconnect();
        voice.gainNode.disconnect();
        voice.pannerNode.disconnect();
      } catch (error) {
        return null;
      }
      return null;
    };
  }

  function publishAudioMetrics() {
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);

    let sumSq = 0;
    let flux = 0;
    let low = 0;
    let mid = 0;
    let high = 0;
    for (let i = 0; i < data.length; i += 1) {
      const v = data[i] / 255;
      sumSq += v * v;
      if (i % 12 === 0) flux += v;
      if (i < data.length * 0.12) low += v;
      else if (i < data.length * 0.42) mid += v;
      else if (i < data.length * 0.9) high += v;
    }
    const rms = Math.sqrt(sumSq / data.length);
    const lowNorm = low / Math.max(1, Math.floor(data.length * 0.12));
    const midNorm = mid / Math.max(1, Math.floor(data.length * 0.30));
    const highNorm = high / Math.max(1, Math.floor(data.length * 0.48));

    const rootStyle = document.documentElement.style;
    rootStyle.setProperty("--sfa-audio-low", String(Math.min(1, lowNorm * 2.3)));
    rootStyle.setProperty("--sfa-audio-mid", String(Math.min(1, midNorm * 2.2)));
    rootStyle.setProperty("--sfa-audio-high", String(Math.min(1, highNorm * 2.4)));
    rootStyle.setProperty("--sfa-audio-rms", String(Math.min(1, rms * 3.4)));
    rootStyle.setProperty("--sfa-bg", "hsl(164 28% " + (state.audioTintBase.bg - Math.min(2.6, lowNorm * 2.4)).toFixed(2) + "%)");
    rootStyle.setProperty("--sfa-accent", "hsl(166 34% " + (state.audioTintBase.accent + Math.min(3.5, midNorm * 3.2)).toFixed(2) + "%)");
    rootStyle.setProperty("--sfa-accent-2", "hsl(176 30% " + (state.audioTintBase.accent2 + Math.min(3.2, highNorm * 3.1)).toFixed(2) + "%)");

    window.dispatchEvent(new CustomEvent("sfa:audio-metrics", {
      detail: {
        rms: rms,
        flux: flux / (data.length / 12),
        low: lowNorm,
        mid: midNorm,
        high: highNorm,
        query: state.query,
        bufferCount: state.buffers.length,
        scene: state.scene.name
      }
    }));
  }

  async function decodeFromUrl(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error("preview download failed");
    const arr = await response.arrayBuffer();
    return context.decodeAudioData(arr);
  }

  function renderResults(items) {
    if (!resultsEl) return;
    resultsEl.innerHTML = "";
    items.forEach(function (item) {
      const li = document.createElement("li");
      const seconds = item.duration ? " (" + Number(item.duration).toFixed(1) + "s)" : "";
      li.textContent = item.name + seconds;
      resultsEl.appendChild(li);
    });
  }

  async function fetchFreesoundPreviewList(query, token) {
    const endpoint = "https://freesound.org/apiv2/search/text/";
    const params = new URLSearchParams({
      query: query,
      page_size: "12",
      fields: "id,name,duration,previews,license,url",
      filter: "duration:[0.3 TO 30]",
      sort: "score",
      token: token
    });

    const response = await fetch(endpoint + "?" + params.toString());
    if (!response.ok) {
      throw new Error("Freesound request failed with status " + response.status);
    }

    const payload = await response.json();
    const results = Array.isArray(payload.results) ? payload.results : [];
    return results.map(function (entry) {
      const preview = entry.previews || {};
      return {
        id: entry.id,
        name: entry.name || "Untitled sample",
        duration: entry.duration,
        previewUrl: preview["preview-hq-mp3"] || preview["preview-lq-mp3"] || ""
      };
    }).filter(function (item) {
      return !!item.previewUrl;
    });
  }

  async function findSinglePreview(query, token) {
    const terms = String(query || "").split(/\s+/).filter(Boolean);
    const attempts = [];
    if (query) attempts.push(query);
    if (terms.length > 1) {
      terms.forEach(function (term) {
        if (!attempts.includes(term)) attempts.push(term);
      });
    }
    fallbackQueries.forEach(function (fallback) {
      if (!attempts.includes(fallback)) attempts.push(fallback);
    });

    for (let index = 0; index < attempts.length; index += 1) {
      const candidate = attempts[index];
      const list = await fetchFreesoundPreviewList(candidate, token);
      if (list.length) {
        const pool = list.slice(0, Math.min(10, list.length));
        const item = pool[Math.floor(rng() * pool.length)];
        return {
          query: candidate,
          item: item
        };
      }
    }

    return null;
  }

  async function fetchAndLoad() {
    if (!queryInput || !fetchBtn) return;

    const query = queryInput.value.trim();
    const token = embeddedToken;
    if (!query) {
      setStatus("Enter text before pressing Get Sound.", true);
      return;
    }
    if (!token) {
      setStatus("A Freesound API token is required.", true);
      return;
    }

    state.query = query;
    state.token = token;
    state.resolvedQuery = "";

    fetchBtn.disabled = true;
    setStatus("Fetching Freesound previews for: " + query + "...", false);

    try {
      const match = await findSinglePreview(query, token);
      if (!match) {
        state.buffers = [];
        renderResults([]);
        setStatus("No previews found for this prompt or its fallback queries. Using internal synth only.", true);
        return;
      }

      const decoded = await decodeFromUrl(match.item.previewUrl);
      state.buffers = [decoded];
      state.resolvedQuery = match.query;
      state.selectedSample = {
        query: query,
        resolvedQuery: match.query,
        name: match.item.name,
        duration: match.item.duration,
        previewUrl: match.item.previewUrl
      };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state.selectedSample));
      } catch (error) {
        return null;
      }
      renderResults([match.item]);
      setStatus(
        "Loaded 1 sample for '" + match.query + "'. Granular engine layers many grains from that single sound.",
        false
      );

      if (state.enabled) {
        context.resume().catch(function () { return null; });
      }
    } catch (error) {
      setStatus("Could not load Freesound samples, using internal synth only: " + (error && error.message ? error.message : "unknown error"), true);
    } finally {
      fetchBtn.disabled = false;
    }
  }

  function autoLoadDefaultQuery() {
    if (!queryInput || !fetchBtn || !embeddedToken || state.autoLoaded) return;
    state.autoLoaded = true;
    if (!queryInput.value.trim()) {
      queryInput.value = defaultQuery;
    }
    fetchAndLoad();
  }

  async function loadStoredSample() {
    let stored = null;
    try {
      stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    } catch (error) {
      stored = null;
    }
    if (!stored || !stored.previewUrl) return false;

    try {
      const decoded = await decodeFromUrl(stored.previewUrl);
      state.buffers = [decoded];
      state.query = stored.query || stored.resolvedQuery || "";
      state.resolvedQuery = stored.resolvedQuery || stored.query || "";
      state.selectedSample = stored;
      renderResults([{ name: stored.name || "Stored sample", duration: stored.duration || 0 }]);
      if (statusEl && !panel) {
        setStatus("Loaded stored sample '" + (stored.name || stored.resolvedQuery || "sample") + "'.", false);
      }
      return true;
    } catch (error) {
      return false;
    }
  }

  window.addEventListener("pointermove", function (event) {
    const width = Math.max(1, window.innerWidth);
    const height = Math.max(1, window.innerHeight);
    state.pointer.x = Math.max(0, Math.min(1, event.clientX / width));
    state.pointer.y = Math.max(0, Math.min(1, event.clientY / height));
  }, { passive: true });

  window.addEventListener("sfa:gol-metrics", function (event) {
    state.golMetrics = Object.assign({}, state.golMetrics, event.detail || {});
  });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden && context.state === "running") {
      context.suspend().catch(function () { return null; });
    } else if (!document.hidden && state.enabled) {
      context.resume().catch(function () { return null; });
    }
  });

  window.addEventListener("pointerdown", function () {
    if (context.state !== "running" && state.enabled) {
      context.resume().catch(function () { return null; });
    }
  }, { passive: true });

  toggleBtn.addEventListener("click", function () {
    setSoundEnabled(!state.enabled);
  });

  if (fetchBtn) {
    fetchBtn.addEventListener("click", fetchAndLoad);
  }

  if (queryInput) {
    queryInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        fetchAndLoad();
      }
    });
  }

  if (queryInput && !queryInput.value.trim()) {
    queryInput.value = defaultQuery;
  }

  const savedEnabled = localStorage.getItem("sfa_sound_enabled") === "1";
  refreshToggleUi();
  setStatus("Scene " + state.scene.name + " ready. Audio starts only after you switch Sound On.", false);
  setSoundEnabled(savedEnabled);
  loadStoredSample().then(function (loaded) {
    if (loaded) return;
    autoLoadDefaultQuery();
  });
})();

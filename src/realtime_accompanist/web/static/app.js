const stateUrl = "/api/state";
const keyboard = document.querySelector("#keyboard");
const audioToggle = document.querySelector("#audio-toggle");
const volumeInput = document.querySelector("#volume");
const whiteKeys = [
  ["C4", 60],
  ["D4", 62],
  ["E4", 64],
  ["F4", 65],
  ["G4", 67],
  ["A4", 69],
  ["B4", 71],
  ["C5", 72],
  ["D5", 74],
  ["E5", 76],
];
const blackKeys = [
  ["C#4", 61, 10],
  ["D#4", 63, 20],
  ["F#4", 66, 40],
  ["G#4", 68, 50],
  ["A#4", 70, 60],
  ["C#5", 73, 80],
  ["D#5", 75, 90],
];

class BrowserSound {
  constructor() {
    this.context = null;
    this.master = null;
    this.compressor = null;
    this.enabled = false;
    this.volume = Number(volumeInput?.value || 0.72);
    this.active = [];
    this._loopHandle = null;
    this._currentEvents = [];
    this._currentBpm = 90;
    this._loopStartTime = null;
  }

  async setEnabled(enabled) {
    this.enabled = enabled;
    if (enabled) {
      await this.ensureContext();
      if (!this.context) {
        this.enabled = false;
        this.updateUi("Unavailable");
        return;
      }
      try {
        await this.context.resume();
      } catch {
        this.enabled = false;
        this.updateUi("Unavailable");
        return;
      }
    } else {
      this.stopLoop();
      this.stopTag("accompaniment");
      this.stopTag("melody");
    }
    this.updateUi();
  }

  async ensureContext() {
    if (this.context) return;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) {
      this.enabled = false;
      this.updateUi("Unavailable");
      return;
    }
    try {
      this.context = new AudioContextClass({ latencyHint: "interactive" });
    } catch {
      try {
        this.context = new AudioContextClass();
      } catch {
        this.context = null;
        this.enabled = false;
        this.updateUi("Unavailable");
        return;
      }
    }
    this.master = this.context.createGain();
    this.master.gain.value = this.volume;
    this.compressor = this.context.createDynamicsCompressor();
    this.compressor.threshold.value = -18;
    this.compressor.knee.value = 18;
    this.compressor.ratio.value = 5;
    this.compressor.attack.value = 0.003;
    this.compressor.release.value = 0.18;
    this.master.connect(this.compressor).connect(this.context.destination);
  }

  async arm() {
    if (!this.enabled) await this.setEnabled(true);
    else if (this.context?.state === "suspended") {
      try {
        await this.context.resume();
      } catch {
        this.enabled = false;
        this.updateUi("Unavailable");
      }
    }
  }

  setVolume(volume) {
    this.volume = Number(volume);
    if (this.master) {
      this.master.gain.setTargetAtTime(this.volume, this.context.currentTime, 0.015);
    }
  }

  updateUi(label) {
    if (!audioToggle) return;
    audioToggle.textContent = label || (this.enabled ? "Sound On" : "Sound Off");
    audioToggle.classList.toggle("active", this.enabled);
    audioToggle.setAttribute("aria-pressed", String(this.enabled));
  }

  noteFrequency(note) {
    return 440 * 2 ** ((note - 69) / 12);
  }

  playNote(note, velocity = 96, duration = 0.35, instrument = "lead", delay = 0, tag = "melody") {
    if (!this.enabled || !this.context || !this.master) return;
    const now = this.context.currentTime + Math.max(delay, 0);
    const safeDuration = Math.max(duration, 0.08);
    const level = Math.max(0.05, Math.min(1, velocity / 127));
    const gain = this.context.createGain();
    const filter = this.context.createBiquadFilter();
    const frequency = this.noteFrequency(note);
    const settings = {
      lead: { attack: 0.006, release: 0.12, peak: 0.28, type: "triangle", cutoff: 5200, q: 0.4 },
      pad: { attack: 0.08, release: 0.55, peak: 0.16, type: "sawtooth", cutoff: 2200, q: 0.7 },
      bass: { attack: 0.01, release: 0.18, peak: 0.24, type: "square", cutoff: 900, q: 0.85 },
    }[instrument] || { attack: 0.006, release: 0.12, peak: 0.24, type: "triangle", cutoff: 4200, q: 0.5 };

    filter.type = "lowpass";
    filter.frequency.setValueAtTime(settings.cutoff, now);
    filter.Q.value = settings.q;
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(settings.peak * level, now + settings.attack);
    gain.gain.setTargetAtTime(0.0001, now + safeDuration, settings.release);
    filter.connect(gain).connect(this.master);

    const primary = this.createOscillator(settings.type, frequency, 0, now, safeDuration + settings.release + 0.08, filter, tag);
    if (instrument !== "bass") {
      this.createOscillator("sine", frequency * 2, -10, now, safeDuration + settings.release + 0.08, filter, tag);
    }
    primary.addEventListener("ended", () => {
      try {
        filter.disconnect();
        gain.disconnect();
      } catch {}
    });
  }

  createOscillator(type, frequency, detune, start, length, destination, tag) {
    const oscillator = this.context.createOscillator();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(frequency, start);
    oscillator.detune.value = detune;
    oscillator.connect(destination);
    oscillator.start(start);
    oscillator.stop(start + length);
    this.track(oscillator, tag);
    return oscillator;
  }

  playDrum(note, velocity = 80, delay = 0, tag = "accompaniment") {
    if (!this.enabled || !this.context || !this.master) return;
    if (note === 36) this.playKick(velocity, delay, tag);
    else if (note === 38) this.playSnare(velocity, delay, tag);
    else this.playHat(velocity, delay, tag);
  }

  playKick(velocity, delay, tag) {
    const now = this.context.currentTime + Math.max(delay, 0);
    const gain = this.context.createGain();
    const oscillator = this.context.createOscillator();
    const level = Math.min(1, velocity / 127);
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(120, now);
    oscillator.frequency.exponentialRampToValueAtTime(44, now + 0.16);
    gain.gain.setValueAtTime(0.5 * level, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.24);
    oscillator.connect(gain).connect(this.master);
    oscillator.start(now);
    oscillator.stop(now + 0.26);
    this.track(oscillator, tag);
  }

  playSnare(velocity, delay, tag) {
    const now = this.context.currentTime + Math.max(delay, 0);
    const source = this.context.createBufferSource();
    const filter = this.context.createBiquadFilter();
    const gain = this.context.createGain();
    const level = Math.min(1, velocity / 127);
    source.buffer = this.noiseBuffer(0.16);
    filter.type = "bandpass";
    filter.frequency.value = 1700;
    filter.Q.value = 0.9;
    gain.gain.setValueAtTime(0.22 * level, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.14);
    source.connect(filter).connect(gain).connect(this.master);
    source.start(now);
    source.stop(now + 0.16);
    this.track(source, tag);
    this.track(gain, tag);
  }

  playHat(velocity, delay, tag) {
    const now = this.context.currentTime + Math.max(delay, 0);
    const source = this.context.createBufferSource();
    const filter = this.context.createBiquadFilter();
    const gain = this.context.createGain();
    const level = Math.min(1, velocity / 127);
    source.buffer = this.noiseBuffer(0.06);
    filter.type = "highpass";
    filter.frequency.value = 6200;
    gain.gain.setValueAtTime(0.11 * level, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.055);
    source.connect(filter).connect(gain).connect(this.master);
    source.start(now);
    source.stop(now + 0.06);
    this.track(source, tag);
    this.track(gain, tag);
  }

  noiseBuffer(duration) {
    const sampleRate = this.context.sampleRate;
    const buffer = this.context.createBuffer(1, Math.ceil(sampleRate * duration), sampleRate);
    const data = buffer.getChannelData(0);
    for (let index = 0; index < data.length; index += 1) {
      data[index] = Math.random() * 2 - 1;
    }
    return buffer;
  }

  updateAccompaniment(events, bpm) {
    this._currentEvents = events || [];
    this._currentBpm = Math.max(Number(bpm) || 90, 1);
    if (this._currentEvents.length && this.enabled && !this._loopHandle) {
      this.startLoop();
    }
  }

  startLoop() {
    if (this._loopHandle) return;
    this._scheduleBar();
  }

  stopLoop() {
    if (this._loopHandle) {
      clearTimeout(this._loopHandle);
      this._loopHandle = null;
    }
    this._loopStartTime = null;
    this.stopTag("accompaniment");
  }

  _scheduleBar() {
    if (!this.enabled || !this._currentEvents.length) {
      this._loopHandle = null;
      return;
    }
    this.stopTag("accompaniment");
    const beatSeconds = 60 / this._currentBpm;
    const barDuration = 4 * beatSeconds;
    this._currentEvents.forEach((event) => {
      const delay = Math.max(0, Number(event.time_seconds ?? event.beat * beatSeconds) || 0) + 0.02;
      const duration = Math.max(0.08, Number(event.duration_beats || 0.25) * beatSeconds);
      if (event.part === "drums") {
        this.playDrum(event.note, event.velocity, delay);
      } else {
        this.playNote(event.note, event.velocity, duration, event.part === "bass" ? "bass" : "pad", delay, "accompaniment");
      }
    });
    this._loopHandle = setTimeout(() => {
      this._loopHandle = null;
      this._scheduleBar();
    }, barDuration * 1000);
  }

  track(node, tag) {
    const item = { node, tag };
    this.active.push(item);
    node.addEventListener?.("ended", () => {
      this.active = this.active.filter((entry) => entry !== item);
    });
  }

  stopTag(tag) {
    const stopping = this.active.filter((item) => item.tag === tag);
    this.active = this.active.filter((item) => item.tag !== tag);
    stopping.forEach(({ node }) => {
      try {
        if (node.stop) node.stop();
        else node.disconnect?.();
      } catch {
        try {
          node.disconnect?.();
        } catch {}
      }
    });
  }
}

const sound = new BrowserSound();
let currentState = null;
let ws = null;

function normalizeNote(value, fallback = 60) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(0, Math.min(127, Math.round(parsed)));
}

function pct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

async function post(url, body = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const state = await response.json();
  applyState(state);
  return state;
}

function applyState(state) {
  currentState = state;
  render(state);
  if (sound.enabled && state.accompaniment_events?.length) {
    sound.updateAccompaniment(state.accompaniment_events, state.bpm);
  }
}

function render(state) {
  const topKey = state.key_candidates?.[0];
  document.querySelector("#primary-key").textContent = topKey ? topKey.name : "-";
  document.querySelector("#selected-chord").textContent = state.selected_chord || "-";
  document.querySelector("#style").textContent = state.style;
  document.querySelector("#density").textContent = `Density: ${state.density}`;
  document.querySelector("#confidence-text").textContent = pct(state.confidence);
  document.querySelector("#confidence-bar").style.width = pct(state.confidence);
  document.querySelector("#next-likely").textContent = `Next: ${(state.next_likely || []).join(" / ") || "-"}`;

  const statusEl = document.querySelector("#status");
  if (state.clock_running) {
    statusEl.textContent = `Bar ${state.bar ?? 0} | Beat ${(state.beat_in_bar ?? 0).toFixed(1)}`;
  } else {
    statusEl.textContent = state.recent_notes?.length ? "Estimating" : "Listening";
  }

  document.querySelector("#keys").innerHTML = (state.key_candidates || [])
    .map((candidate) => `<div class="list-row">${candidate.name} ${pct(candidate.confidence)}</div>`)
    .join("");

  document.querySelector("#chords").innerHTML = (state.chord_candidates || [])
    .map((candidate) => `<button class="chip" data-chord="${candidate.symbol}">${candidate.symbol}<br>${pct(candidate.confidence)}</button>`)
    .join("");
  document.querySelectorAll("[data-chord]").forEach((button) => {
    button.addEventListener("click", async () => {
      await post("/api/controls/chord", { symbol: button.dataset.chord });
    });
  });

  document.querySelector("#recent-notes").innerHTML = (state.recent_notes || [])
    .slice()
    .reverse()
    .map((note) => `<div class="note">${note.name}<br><small>${note.note}</small></div>`)
    .join("");

  document.querySelector("#events").innerHTML = (state.accompaniment_events || [])
    .slice(0, 14)
    .map((event) => `<div class="event-row">${event.part} note ${event.note} @ beat ${event.beat}</div>`)
    .join("");

  document.querySelectorAll("[data-style]").forEach((button) => {
    button.classList.toggle("active", button.dataset.style === state.style);
  });
  document.querySelectorAll("[data-bias]").forEach((button) => {
    button.classList.toggle("active", button.dataset.bias === state.bias);
  });
  const keyLockBtn = document.querySelector("#key-lock");
  if (keyLockBtn) {
    keyLockBtn.textContent = state.key_lock ? "Key Lock: On" : "Key Lock: Off";
    keyLockBtn.classList.toggle("active", !!state.key_lock);
  }
}

function flashKey(note) {
  const button = keyboard?.querySelector(`[data-note="${note}"]`);
  if (!button) return;
  button.classList.add("playing");
  window.setTimeout(() => button.classList.remove("playing"), 150);
}

const heldKeys = new Map();

async function keyDown(note, velocity = 104) {
  if (heldKeys.has(note)) return;
  heldKeys.set(note, Date.now());
  const safeNote = normalizeNote(note);
  flashKey(safeNote);
  sound.arm().then(() => sound.playNote(safeNote, velocity, 0.5, "lead"));
  await post("/api/note-on", { note: safeNote, velocity });
}

async function keyUp(note) {
  if (!heldKeys.has(note)) return;
  heldKeys.delete(note);
  const safeNote = normalizeNote(note);
  const button = keyboard?.querySelector(`[data-note="${safeNote}"]`);
  if (button) button.classList.remove("playing");
  await post("/api/note-off", { note: safeNote });
}

async function sendNote(note, velocity = 104, duration = 0.4) {
  const safeNote = normalizeNote(note);
  flashKey(safeNote);
  sound.arm().then(() => sound.playNote(safeNote, velocity, duration, "lead"));
  await post("/api/notes", { note: safeNote, velocity, duration });
}

function initKeyboard() {
  if (!keyboard) return;
  keyboard.innerHTML = `
    <div class="white-keys">
      ${whiteKeys.map(([label, note]) => `<button class="key white" data-note="${note}"><span>${label}</span></button>`).join("")}
    </div>
    <div class="black-keys" aria-hidden="false">
      ${blackKeys.map(([label, note, left]) => `<button class="key black" style="--left: ${left}" data-note="${note}"><span>${label}</span></button>`).join("")}
    </div>
  `;
  keyboard.addEventListener("pointerdown", (event) => {
    const button = event.target.closest("[data-note]");
    if (!button) return;
    event.preventDefault();
    keyDown(Number(button.dataset.note), 104);
  });
  keyboard.addEventListener("pointerup", (event) => {
    const button = event.target.closest("[data-note]");
    if (!button) return;
    keyUp(Number(button.dataset.note));
  });
  keyboard.addEventListener("pointerleave", (event) => {
    const button = event.target.closest("[data-note]");
    if (!button) return;
    keyUp(Number(button.dataset.note));
  });
}

function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/state`);
  ws.onmessage = (event) => {
    try {
      const state = JSON.parse(event.data);
      applyState(state);
    } catch {}
  };
  ws.onclose = () => {
    setTimeout(initWebSocket, 2000);
  };
}

function initControls() {
  audioToggle?.addEventListener("click", () => sound.setEnabled(!sound.enabled));
  volumeInput?.addEventListener("input", () => sound.setVolume(volumeInput.value));
  document.querySelector("#send-note")?.addEventListener("click", () => {
    sendNote(document.querySelector("#note-input").value, 100, 0.4);
  });
  document.querySelector("#reset")?.addEventListener("click", async () => {
    sound.stopLoop();
    sound.stopTag("accompaniment");
    sound.stopTag("melody");
    await post("/api/reset");
  });
  document.querySelectorAll("[data-demo]").forEach((button) => {
    button.addEventListener("click", async () => {
      const state = await post(`/api/demo/${button.dataset.demo}`);
      sound.arm().then(() => {
        (state.recent_notes || []).forEach((note, index) => {
          window.setTimeout(() => flashKey(note.note), index * 160);
          sound.playNote(note.note, note.velocity, note.duration, "lead", index * 0.16, "melody");
        });
      });
    });
  });
  document.querySelectorAll("[data-style]").forEach((button) => {
    button.addEventListener("click", async () => {
      await post("/api/controls/style", { style: button.dataset.style });
    });
  });
  document.querySelectorAll("[data-bias]").forEach((button) => {
    button.addEventListener("click", async () => {
      await post("/api/controls/bias", { bias: button.dataset.bias });
    });
  });
  document.querySelector("#key-lock")?.addEventListener("click", async () => {
    await post("/api/controls/key-lock");
  });
}

async function boot() {
  initKeyboard();
  initControls();
  sound.updateUi();
  try {
    const response = await fetch(stateUrl);
    applyState(await response.json());
  } catch {}
  initWebSocket();
}

boot();

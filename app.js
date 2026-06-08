const names = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"];
const major = [0, 2, 4, 5, 7, 9, 11];
const minor = [0, 2, 3, 5, 7, 8, 10];
const demos = {
  "c-major": [60, 62, 64, 67, 72],
  ambiguous: [69, 72, 76, 79, 76, 72],
  "genre-switch": [60, 64, 67, 71, 72, 76],
};
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
const keyboard = document.querySelector("#keyboard");
const audioToggle = document.querySelector("#audio-toggle");
const volumeInput = document.querySelector("#volume");
let state = { notes: [], style: "lofi", bias: "auto", selectedChord: null, beat: 0 };
let renderedEvents = [];
let renderedBpm = 90;

class BrowserSound {
  constructor() {
    this.context = null;
    this.master = null;
    this.compressor = null;
    this.enabled = false;
    this.volume = Number(volumeInput?.value || 0.72);
    this.active = [];
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
      this.stopTag("accompaniment");
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
      } catch {
        // Nodes can already be disconnected when a sequence is interrupted.
      }
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

  playAccompaniment(events = [], bpm = 90) {
    if (!this.enabled || !events.length) return;
    this.stopTag("accompaniment");
    const beatSeconds = 60 / Math.max(Number(bpm) || 90, 1);
    events.slice(0, 18).forEach((event) => {
      const delay = Math.max(0, Number(event.time_seconds ?? event.beat * beatSeconds) || 0) + 0.035;
      const duration = Math.max(0.08, Number(event.duration_beats || 0.25) * beatSeconds);
      if (event.part === "drums") {
        this.playDrum(event.note, event.velocity, delay);
      } else {
        this.playNote(event.note, event.velocity, duration, event.part === "bass" ? "bass" : "pad", delay, "accompaniment");
      }
    });
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
        } catch {
          // A disconnected node is already silent.
        }
      }
    });
  }
}

const sound = new BrowserSound();

function normalizeNote(value, fallback = 60) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(0, Math.min(127, Math.round(parsed)));
}

function pc(note) {
  return ((note % 12) + 12) % 12;
}

function scale(root, mode) {
  return new Set((mode === "minor" ? minor : major).map((interval) => pc(root + interval)));
}

function chordTones(root, quality) {
  const intervals = quality === "minor" ? [0, 3, 7] : quality === "diminished" ? [0, 3, 6] : [0, 4, 7];
  return new Set(intervals.map((interval) => pc(root + interval)));
}

function chordSymbol(root, quality) {
  if (quality === "minor") return `${names[root]}m`;
  if (quality === "diminished") return `${names[root]}dim`;
  return names[root];
}

function diatonic(root, mode) {
  const intervals = mode === "minor" ? minor : major;
  const qualities = mode === "minor"
    ? ["minor", "diminished", "major", "minor", "minor", "major", "major"]
    : ["major", "minor", "minor", "major", "major", "minor", "diminished"];
  return intervals.map((interval, index) => {
    const chordRoot = pc(root + interval);
    const quality = qualities[index];
    return { symbol: chordSymbol(chordRoot, quality), root: chordRoot, quality, tones: chordTones(chordRoot, quality) };
  });
}

function estimateKeys() {
  const candidates = [];
  for (let root = 0; root < 12; root += 1) {
    for (const mode of ["major", "minor"]) {
      const scaleSet = scale(root, mode);
      let score = 0;
      state.notes.forEach((note, index) => {
        const pitch = pc(note.note);
        const recency = 1 + index / Math.max(state.notes.length - 1, 1) * 0.35;
        score += (scaleSet.has(pitch) ? 1 : -0.75) * recency;
        if (pitch === root) score += 0.75 * recency;
        if (pitch === pc(root + 7)) score += 0.25 * recency;
        if (index === state.notes.length - 1 && pitch === root) score += 0.75;
      });
      const present = new Set(state.notes.map((note) => pc(note.note)));
      const tonicTriad = chordTones(root, mode === "minor" ? "minor" : "major");
      if ([...tonicTriad].filter((tone) => present.has(tone)).length >= 3) score += 1.4;
      if (state.bias === mode) score += 0.5;
      candidates.push({ name: `${names[root]} ${mode}`, root, mode, score });
    }
  }
  const max = Math.max(0, ...candidates.map((candidate) => candidate.score));
  return candidates
    .map((candidate) => ({ ...candidate, confidence: state.notes.length && max > 0 ? Math.max(0, candidate.score / max) : 0 }))
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 6);
}

function estimateChords(keys) {
  const key = keys[0] || { root: 0, mode: "major" };
  const chords = diatonic(key.root, key.mode);
  if (!state.notes.length) return chords.slice(0, 6).map((chord) => ({ ...chord, confidence: 0 }));
  const scored = chords.map((chord) => {
    let score = 1;
    state.notes.forEach((note, index) => {
      const pitch = pc(note.note);
      const weight = 1 + index / Math.max(state.notes.length - 1, 1) * 0.25;
      score += chord.tones.has(pitch) ? weight : 0.1;
      if (pitch === chord.root) score += 0.25;
    });
    return { ...chord, score };
  });
  const max = Math.max(...scored.map((candidate) => candidate.score));
  return scored.map((candidate) => ({ ...candidate, confidence: candidate.score / max })).sort((a, b) => b.confidence - a.confidence).slice(0, 6);
}

function event(part, note, beat, durationBeats, velocity, bpm = renderedBpm) {
  return { part, note, beat, duration_beats: durationBeats, velocity, time_seconds: beat * 60 / bpm };
}

function accompaniment(chord, confidence) {
  if (!chord) return [];
  const density = confidence < 0.35 ? "low" : confidence < 0.65 ? "medium" : "high";
  const events = [
    event("drums", 36, 0, 0.1, 62),
    event("drums", 38, 1, 0.1, 48),
    event("drums", 36, 2, 0.1, 58),
    event("drums", 38, 3, 0.1, 46),
    event("pad", 60 + chord.root, 0, 3.8, density === "high" ? 66 : 52),
    event("pad", 60 + pc(chord.root + 7), 0, 3.8, density === "high" ? 66 : 52),
  ];
  if (density !== "low") {
    events.push(event("bass", 36 + chord.root, 0, 0.9, density === "high" ? 78 : 64));
    events.push(event("bass", 36 + pc(chord.root + 7), 2, 0.9, density === "high" ? 78 : 64));
  }
  if (density === "high") {
    events.push(event("pad", 72 + chord.root, 0.5, 0.35, 50));
    events.push(event("pad", 72 + pc(chord.root + 4), 1.5, 0.35, 50));
  }
  return events.sort((a, b) => a.beat - b.beat || a.part.localeCompare(b.part));
}

function pct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function recordNote(note) {
  const safeNote = normalizeNote(note);
  state.notes.push({ note: safeNote, beat: state.beat, velocity: 100, duration: 0.4 });
  state.notes = state.notes.slice(-16);
  state.beat += 0.4;
}

async function addNote(note) {
  const safeNote = normalizeNote(note);
  recordNote(safeNote);
  flashKey(safeNote);
  render();
  sound.arm().then(() => {
    sound.playNote(safeNote, 104, 0.4, "lead");
    sound.playAccompaniment(renderedEvents, renderedBpm);
  });
}

function render() {
  const keys = estimateKeys();
  const chords = estimateChords(keys);
  const selected = state.selectedChord ? chords.find((chord) => chord.symbol === state.selectedChord) || chords[0] : chords[0];
  const confidence = state.notes.length ? selected?.confidence || 0 : 0;
  const density = confidence < 0.35 ? "low" : confidence < 0.65 ? "medium" : "high";
  renderedEvents = accompaniment(state.notes.length ? selected : null, confidence);
  document.querySelector("#primary-key").textContent = keys[0]?.name || "C major";
  document.querySelector("#selected-chord").textContent = state.notes.length && selected ? selected.symbol : "-";
  document.querySelector("#style").textContent = state.style;
  document.querySelector("#density").textContent = `Density: ${density}`;
  document.querySelector("#confidence-text").textContent = pct(confidence);
  document.querySelector("#confidence-bar").style.width = pct(confidence);
  document.querySelector("#next-likely").textContent = `Next: ${chords.slice(1, 4).map((chord) => chord.symbol).join(" / ") || "-"}`;
  document.querySelector("#status").textContent = state.notes.length ? "Estimating" : "Browser Demo";
  document.querySelector("#keys").innerHTML = keys.map((candidate) => `<div class="list-row">${candidate.name} ${pct(candidate.confidence)}</div>`).join("");
  document.querySelector("#chords").innerHTML = chords.map((candidate) => `<button class="chip" data-chord="${candidate.symbol}">${candidate.symbol}<br>${pct(candidate.confidence)}</button>`).join("");
  document.querySelector("#recent-notes").innerHTML = state.notes.slice().reverse().map((note) => `<div class="note">${names[pc(note.note)]}<br><small>${note.note}</small></div>`).join("");
  document.querySelector("#events").innerHTML = renderedEvents.map((event) => `<div class="event-row">${event.part} note ${event.note} @ beat ${event.beat}</div>`).join("");
  document.querySelectorAll("[data-chord]").forEach((button) => button.addEventListener("click", async () => {
    state.selectedChord = button.dataset.chord;
    render();
    sound.arm().then(() => sound.playAccompaniment(renderedEvents, renderedBpm));
  }));
  document.querySelectorAll("[data-style]").forEach((button) => button.classList.toggle("active", button.dataset.style === state.style));
  document.querySelectorAll("[data-bias]").forEach((button) => button.classList.toggle("active", button.dataset.bias === state.bias));
}

function flashKey(note) {
  const button = keyboard.querySelector(`[data-note="${note}"]`);
  if (!button) return;
  button.classList.add("playing");
  window.setTimeout(() => button.classList.remove("playing"), 150);
}

function boot() {
  keyboard.innerHTML = `
    <div class="white-keys">
      ${whiteKeys.map(([label, note]) => `<button class="key white" data-note="${note}"><span>${label}</span></button>`).join("")}
    </div>
    <div class="black-keys" aria-hidden="false">
      ${blackKeys.map(([label, note, left]) => `<button class="key black" style="--left: ${left}" data-note="${note}"><span>${label}</span></button>`).join("")}
    </div>
  `;
  let pointerSentAt = 0;
  keyboard.addEventListener("pointerdown", (event) => {
    const button = event.target.closest("[data-note]");
    if (!button) return;
    event.preventDefault();
    pointerSentAt = Date.now();
    addNote(Number(button.dataset.note));
  });
  keyboard.addEventListener("click", (event) => {
    const button = event.target.closest("[data-note]");
    if (!button || Date.now() - pointerSentAt < 500) return;
    addNote(Number(button.dataset.note));
  });
  document.querySelector("#send-note").addEventListener("click", () => {
    addNote(document.querySelector("#note-input").value);
  });
  document.querySelector("#reset").addEventListener("click", () => {
    sound.stopTag("accompaniment");
    state.notes = [];
    state.selectedChord = null;
    state.beat = 0;
    render();
  });
  document.querySelectorAll("[data-demo]").forEach((button) => button.addEventListener("click", async () => {
    state.notes = [];
    state.selectedChord = null;
    state.beat = 0;
    demos[button.dataset.demo].forEach((note) => recordNote(note));
    render();
    state.notes.forEach((note, index) => window.setTimeout(() => flashKey(note.note), index * 160));
    sound.arm().then(() => {
      state.notes.forEach((note, index) => {
        sound.playNote(note.note, note.velocity, note.duration, "lead", index * 0.16, "melody");
      });
      sound.playAccompaniment(renderedEvents, renderedBpm);
    });
  }));
  document.querySelectorAll("[data-style]").forEach((button) => button.addEventListener("click", () => {
    state.style = button.dataset.style;
    render();
    sound.arm().then(() => sound.playAccompaniment(renderedEvents, renderedBpm));
  }));
  document.querySelectorAll("[data-bias]").forEach((button) => button.addEventListener("click", () => {
    state.bias = button.dataset.bias;
    render();
    sound.arm().then(() => sound.playAccompaniment(renderedEvents, renderedBpm));
  }));
  audioToggle.addEventListener("click", () => sound.setEnabled(!sound.enabled));
  volumeInput.addEventListener("input", () => sound.setVolume(volumeInput.value));
  sound.updateUi();
  render();
}

boot();

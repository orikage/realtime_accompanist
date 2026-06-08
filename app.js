const names = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"];
const major = [0, 2, 4, 5, 7, 9, 11];
const minor = [0, 2, 3, 5, 7, 8, 10];
const demos = {
  "c-major": [60, 62, 64, 67, 72],
  ambiguous: [69, 72, 76, 79, 76, 72],
  "genre-switch": [60, 64, 67, 71, 72, 76],
};
const noteButtons = [
  ["C4", 60, false],
  ["D4", 62, false],
  ["E4", 64, false],
  ["F4", 65, false],
  ["G4", 67, false],
  ["A4", 69, false],
  ["B4", 71, false],
  ["C#4", 61, true],
  ["D#4", 63, true],
  ["F#4", 66, true],
  ["G#4", 68, true],
  ["A#4", 70, true],
  ["C5", 72, false],
  ["E5", 76, false],
];
let state = { notes: [], style: "lofi", bias: "auto", selectedChord: null, beat: 0 };

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

function accompaniment(chord, confidence) {
  if (!chord) return [];
  const density = confidence < 0.35 ? "low" : confidence < 0.65 ? "medium" : "high";
  const events = [
    { part: "drums", note: 36, beat: 0 },
    { part: "drums", note: 38, beat: 1 },
    { part: "drums", note: 36, beat: 2 },
    { part: "drums", note: 38, beat: 3 },
    { part: "pad", note: 60 + chord.root, beat: 0 },
    { part: "pad", note: 60 + pc(chord.root + 7), beat: 0 },
  ];
  if (density !== "low") events.push({ part: "bass", note: 36 + chord.root, beat: 0 }, { part: "bass", note: 36 + pc(chord.root + 7), beat: 2 });
  if (density === "high") events.push({ part: "pad", note: 72 + chord.root, beat: 0.5 }, { part: "pad", note: 72 + pc(chord.root + 4), beat: 1.5 });
  return events;
}

function pct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

function addNote(note) {
  state.notes.push({ note, beat: state.beat });
  state.notes = state.notes.slice(-16);
  state.beat += 0.4;
  render();
}

function render() {
  const keys = estimateKeys();
  const chords = estimateChords(keys);
  const selected = state.selectedChord ? chords.find((chord) => chord.symbol === state.selectedChord) || chords[0] : chords[0];
  const confidence = state.notes.length ? selected?.confidence || 0 : 0;
  const density = confidence < 0.35 ? "low" : confidence < 0.65 ? "medium" : "high";
  const events = accompaniment(state.notes.length ? selected : null, confidence);
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
  document.querySelector("#events").innerHTML = events.map((event) => `<div class="event-row">${event.part} note ${event.note} @ beat ${event.beat}</div>`).join("");
  document.querySelectorAll("[data-chord]").forEach((button) => button.addEventListener("click", () => {
    state.selectedChord = button.dataset.chord;
    render();
  }));
  document.querySelectorAll("[data-style]").forEach((button) => button.classList.toggle("active", button.dataset.style === state.style));
  document.querySelectorAll("[data-bias]").forEach((button) => button.classList.toggle("active", button.dataset.bias === state.bias));
}

function boot() {
  document.querySelector("#keyboard").innerHTML = noteButtons.map(([label, note, black]) => `<button class="${black ? "black" : ""}" data-note="${note}">${label}</button>`).join("");
  document.querySelectorAll("[data-note]").forEach((button) => button.addEventListener("click", () => addNote(Number(button.dataset.note))));
  document.querySelector("#send-note").addEventListener("click", () => addNote(Number(document.querySelector("#note-input").value)));
  document.querySelector("#reset").addEventListener("click", () => {
    state.notes = [];
    state.selectedChord = null;
    state.beat = 0;
    render();
  });
  document.querySelectorAll("[data-demo]").forEach((button) => button.addEventListener("click", () => {
    state.notes = [];
    state.selectedChord = null;
    demos[button.dataset.demo].forEach((note) => addNote(note));
  }));
  document.querySelectorAll("[data-style]").forEach((button) => button.addEventListener("click", () => {
    state.style = button.dataset.style;
    render();
  }));
  document.querySelectorAll("[data-bias]").forEach((button) => button.addEventListener("click", () => {
    state.bias = button.dataset.bias;
    render();
  }));
  render();
}

boot();


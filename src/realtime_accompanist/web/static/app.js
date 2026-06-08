const stateUrl = "/api/state";
const keyboard = document.querySelector("#keyboard");
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

function pct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

async function post(url, body = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  render(await response.json());
}

function render(state) {
  const topKey = state.key_candidates[0];
  document.querySelector("#primary-key").textContent = topKey ? topKey.name : "-";
  document.querySelector("#selected-chord").textContent = state.selected_chord || "-";
  document.querySelector("#style").textContent = state.style;
  document.querySelector("#density").textContent = `Density: ${state.density}`;
  document.querySelector("#confidence-text").textContent = pct(state.confidence);
  document.querySelector("#confidence-bar").style.width = pct(state.confidence);
  document.querySelector("#next-likely").textContent = `Next: ${(state.next_likely || []).join(" / ") || "-"}`;
  document.querySelector("#status").textContent = state.recent_notes.length ? "Estimating" : "Listening";

  document.querySelector("#keys").innerHTML = state.key_candidates
    .map((candidate) => `<div class="list-row">${candidate.name} ${pct(candidate.confidence)}</div>`)
    .join("");

  document.querySelector("#chords").innerHTML = state.chord_candidates
    .map((candidate) => `<button class="chip" data-chord="${candidate.symbol}">${candidate.symbol}<br>${pct(candidate.confidence)}</button>`)
    .join("");
  document.querySelectorAll("[data-chord]").forEach((button) => {
    button.addEventListener("click", () => post("/api/controls/chord", { symbol: button.dataset.chord }));
  });

  document.querySelector("#recent-notes").innerHTML = state.recent_notes
    .slice()
    .reverse()
    .map((note) => `<div class="note">${note.name}<br><small>${note.note}</small></div>`)
    .join("");

  document.querySelector("#events").innerHTML = state.accompaniment_events
    .slice(0, 14)
    .map((event) => `<div class="event-row">${event.part} note ${event.note} @ beat ${event.beat}</div>`)
    .join("");

  document.querySelectorAll("[data-style]").forEach((button) => {
    button.classList.toggle("active", button.dataset.style === state.style);
  });
  document.querySelectorAll("[data-bias]").forEach((button) => {
    button.classList.toggle("active", button.dataset.bias === state.bias);
  });
}

function initKeyboard() {
  keyboard.innerHTML = noteButtons
    .map(([label, note, black]) => `<button class="${black ? "black" : ""}" data-note="${note}">${label}</button>`)
    .join("");
  keyboard.querySelectorAll("[data-note]").forEach((button) => {
    button.addEventListener("click", () => post("/api/notes", { note: Number(button.dataset.note), velocity: 104, duration: 0.4 }));
  });
}

function initControls() {
  document.querySelector("#send-note").addEventListener("click", () => {
    post("/api/notes", { note: Number(document.querySelector("#note-input").value), velocity: 100, duration: 0.4 });
  });
  document.querySelector("#reset").addEventListener("click", () => post("/api/reset"));
  document.querySelectorAll("[data-demo]").forEach((button) => {
    button.addEventListener("click", () => post(`/api/demo/${button.dataset.demo}`));
  });
  document.querySelectorAll("[data-style]").forEach((button) => {
    button.addEventListener("click", () => post("/api/controls/style", { style: button.dataset.style }));
  });
  document.querySelectorAll("[data-bias]").forEach((button) => {
    button.addEventListener("click", () => post("/api/controls/bias", { bias: button.dataset.bias }));
  });
}

async function boot() {
  initKeyboard();
  initControls();
  const response = await fetch(stateUrl);
  render(await response.json());
}

boot();


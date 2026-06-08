from __future__ import annotations

import time

from realtime_accompanist.domain.accompaniment import AccompanimentEngine
from realtime_accompanist.domain.chord_estimator import ChordEstimator
from realtime_accompanist.domain.clock import MusicalClock
from realtime_accompanist.domain.key_estimator import KeyEstimator
from realtime_accompanist.domain.melody_buffer import MelodyBuffer
from realtime_accompanist.domain.models import AccompanimentEvent, Chord, ChordCandidate, KeyCandidate, NoteEvent
from realtime_accompanist.domain.progression_smoother import ProgressionSmoother
from realtime_accompanist.domain.theory import note_name


KEY_WINDOW_BEATS = 16.0
CHORD_WINDOW_BEATS = 4.0


class AccompanistSession:
    def __init__(self, bpm: float = 90.0) -> None:
        self.clock = MusicalClock(bpm=bpm)
        self.style = "lofi"
        self.bias = "auto"
        self.key_lock = False
        self.accompaniment_enabled = True
        self.buffer = MelodyBuffer()
        self.key_estimator = KeyEstimator()
        self.chord_estimator = ChordEstimator()
        self.smoother = ProgressionSmoother()
        self.accompaniment = AccompanimentEngine()
        self._selected_chord: Chord | None = None
        self._manual_chord: str | None = None
        self._locked_key: KeyCandidate | None = None
        self._last_accompaniment: list[AccompanimentEvent] = []
        self._last_chord_change_bar: int = -1
        self._active_notes: dict[int, float] = {}

    @property
    def bpm(self) -> float:
        return self.clock.bpm

    @bpm.setter
    def bpm(self, value: float) -> None:
        self.clock.bpm = value

    def note_on(self, note: int, velocity: int = 96) -> dict:
        if not self.clock.running:
            self.clock.start()
        self._active_notes[note] = time.monotonic()
        return self.snapshot()

    def note_off(self, note: int) -> dict:
        start = self._active_notes.pop(note, None)
        if start is not None:
            duration = max(time.monotonic() - start, 0.05)
            beat = self.clock.beat_at(start)
            event = NoteEvent(
                note=note,
                velocity=96,
                start_time=start - (self.clock._origin or start),
                duration=duration,
                beat=beat,
            )
            self.buffer.add(event)
        return self.snapshot()

    def add_note(self, note: int, velocity: int = 96, duration: float = 0.35) -> dict:
        if not self.clock.running:
            self.clock.start()
        beat = self.clock.beat
        origin = self.clock._origin or time.monotonic()
        start_time = time.monotonic() - origin
        event = NoteEvent(
            note=note,
            velocity=velocity,
            start_time=start_time,
            duration=max(duration, 0.05),
            beat=beat,
        )
        self.buffer.add(event)
        return self.snapshot()

    def tick(self) -> dict:
        current_bar = self.clock.bar
        if current_bar != self._last_chord_change_bar:
            self._try_chord_change(current_bar)
        return self.snapshot()

    def set_style(self, style: str) -> dict:
        if style in {"lofi", "jpop", "game_bgm"}:
            self.style = style
            self._regenerate_accompaniment()
        return self.snapshot()

    def set_bias(self, bias: str) -> dict:
        if bias in {"auto", "major", "minor"}:
            self.bias = bias
        return self.snapshot()

    def select_chord(self, symbol: str) -> dict:
        self._manual_chord = symbol
        self._try_chord_change(self.clock.bar, force=True)
        return self.snapshot()

    def toggle_key_lock(self) -> dict:
        if self.key_lock:
            self.key_lock = False
            self._locked_key = None
        else:
            notes_for_key = self.buffer.recent_beats(self.clock.beat, KEY_WINDOW_BEATS)
            keys = self.key_estimator.estimate(notes_for_key, bias=self.bias)
            if keys:
                self._locked_key = keys[0]
                self.key_lock = True
        return self.snapshot()

    def reset(self) -> dict:
        self.clock.reset()
        self.clock.stop()
        self.buffer.clear()
        self.smoother.reset()
        self._selected_chord = None
        self._manual_chord = None
        self._locked_key = None
        self.key_lock = False
        self._last_accompaniment = []
        self._last_chord_change_bar = -1
        self._active_notes.clear()
        return self.snapshot()

    def load_demo(self, name: str) -> dict:
        demos = {
            "c-major": [
                (60, 100, 0.5), (64, 95, 0.5), (67, 90, 0.5),
                (72, 100, 1.0), (71, 85, 0.5), (67, 90, 0.5),
                (64, 85, 0.5), (60, 100, 1.0),
            ],
            "ambiguous": [
                (69, 95, 0.5), (72, 90, 0.5), (76, 100, 0.75),
                (72, 85, 0.25), (69, 80, 0.5), (67, 90, 0.5),
                (65, 85, 0.5), (64, 100, 1.0),
            ],
            "genre-switch": [
                (60, 100, 0.5), (62, 90, 0.25), (64, 95, 0.5),
                (67, 100, 0.75), (72, 95, 0.5), (71, 85, 0.25),
                (69, 90, 0.5), (67, 100, 1.0),
            ],
        }
        self.reset()
        self.clock.start()
        beat_cursor = 0.0
        beat_duration = 60.0 / self.bpm
        origin = self.clock._origin or time.monotonic()
        for note, vel, dur in demos.get(name, demos["c-major"]):
            event = NoteEvent(
                note=note,
                velocity=vel,
                start_time=beat_cursor * beat_duration,
                duration=dur * beat_duration,
                beat=beat_cursor,
            )
            self.buffer.add(event)
            beat_cursor += dur
        self._try_chord_change(0, force=True)
        return self.snapshot()

    def _windowed_notes(self, current_beat: float) -> tuple[list[NoteEvent], list[NoteEvent]]:
        key_notes = self.buffer.recent_beats(current_beat, KEY_WINDOW_BEATS)
        chord_notes = self.buffer.recent_beats(current_beat, CHORD_WINDOW_BEATS)
        all_notes = self.buffer.notes
        if not key_notes and all_notes:
            key_notes = all_notes[-32:]
        if not chord_notes and all_notes:
            chord_notes = all_notes[-8:]
        return key_notes, chord_notes

    def snapshot(self) -> dict:
        current_beat = self.clock.beat
        notes_for_key, notes_for_chord = self._windowed_notes(current_beat)

        if self.key_lock and self._locked_key:
            keys = [self._locked_key]
        else:
            keys = self.key_estimator.estimate(notes_for_key, bias=self.bias)

        chords = self.chord_estimator.estimate(
            notes_for_chord, keys, previous_chord=self._selected_chord
        )

        has_notes = bool(self.buffer.notes)
        confidence = chords[0].confidence if has_notes and chords else 0.0
        density = self._density(confidence)
        selected = self._selected_chord or (chords[0].chord if has_notes and chords else None)

        if selected and not self._last_accompaniment:
            self._last_accompaniment = self.accompaniment.generate(
                selected, self.bpm, self.style, density
            )

        return {
            "bpm": self.bpm,
            "beat": round(current_beat, 3),
            "bar": self.clock.bar,
            "beat_in_bar": round(self.clock.beat_in_bar, 3),
            "style": self.style,
            "bias": self.bias,
            "key_lock": self.key_lock,
            "density": density,
            "confidence": round(confidence, 3),
            "selected_chord": selected.symbol if selected else None,
            "key_candidates": [
                {
                    "name": c.name,
                    "tonic": note_name(c.tonic),
                    "mode": c.mode,
                    "confidence": round(c.confidence, 3),
                }
                for c in keys[:6]
            ],
            "chord_candidates": [
                {
                    "symbol": c.symbol,
                    "root": note_name(c.chord.root),
                    "quality": c.chord.quality,
                    "confidence": round(c.confidence, 3),
                }
                for c in chords
            ],
            "next_likely": [c.symbol for c in chords[1:4]],
            "recent_notes": [
                {
                    "note": e.note,
                    "name": note_name(e.pitch_class),
                    "velocity": e.velocity,
                    "duration": round(e.duration, 3),
                    "beat": round(e.beat, 3),
                }
                for e in self.buffer.notes[-16:]
            ],
            "accompaniment_events": [
                {
                    "part": ev.part,
                    "note": ev.note,
                    "beat": ev.beat,
                    "duration_beats": ev.duration_beats,
                    "velocity": ev.velocity,
                    "channel": ev.channel,
                    "time_seconds": round(ev.time_seconds, 3),
                }
                for ev in self._last_accompaniment
            ],
            "clock_running": self.clock.running,
        }

    def _try_chord_change(self, bar: int, force: bool = False) -> None:
        current_beat = self.clock.beat
        notes_for_key, notes_for_chord = self._windowed_notes(current_beat)

        if self.key_lock and self._locked_key:
            keys = [self._locked_key]
        else:
            keys = self.key_estimator.estimate(notes_for_key, bias=self.bias)

        chords = self.chord_estimator.estimate(
            notes_for_chord, keys, previous_chord=self._selected_chord
        )

        if force and self._manual_chord:
            self._selected_chord = self.smoother.select(
                chords, current=self._selected_chord, beat=current_beat,
                manual_override=self._manual_chord,
            )
            self._manual_chord = None
        else:
            self._selected_chord = self.smoother.select(
                chords, current=self._selected_chord, beat=current_beat,
            )

        self._last_chord_change_bar = bar
        self._regenerate_accompaniment()

    def _regenerate_accompaniment(self) -> None:
        if self._selected_chord:
            current_beat = self.clock.beat
            notes_for_key, notes_for_chord = self._windowed_notes(current_beat)
            keys = self.key_estimator.estimate(notes_for_key, bias=self.bias)
            chords = self.chord_estimator.estimate(
                notes_for_chord, keys, previous_chord=self._selected_chord
            )
            confidence = chords[0].confidence if chords else 0.0
            density = self._density(confidence)
            self._last_accompaniment = self.accompaniment.generate(
                self._selected_chord, self.bpm, self.style, density
            )

    def _density(self, confidence: float) -> str:
        if confidence < 0.35:
            return "low"
        if confidence < 0.65:
            return "medium"
        return "high"

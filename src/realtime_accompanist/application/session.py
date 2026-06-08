from __future__ import annotations

import time

from realtime_accompanist.domain.accompaniment import AccompanimentEngine
from realtime_accompanist.domain.chord_estimator import ChordEstimator
from realtime_accompanist.domain.key_estimator import KeyEstimator
from realtime_accompanist.domain.melody_buffer import MelodyBuffer
from realtime_accompanist.domain.models import Chord, NoteEvent
from realtime_accompanist.domain.progression_smoother import ProgressionSmoother
from realtime_accompanist.domain.theory import note_name


class AccompanistSession:
    def __init__(self, bpm: float = 90.0) -> None:
        self.bpm = bpm
        self.style = "lofi"
        self.bias = "auto"
        self.key_lock = False
        self.accompaniment_enabled = True
        self.buffer = MelodyBuffer()
        self.key_estimator = KeyEstimator()
        self.chord_estimator = ChordEstimator()
        self.smoother = ProgressionSmoother()
        self.accompaniment = AccompanimentEngine()
        self._beat = 0.0
        self._time_origin = time.monotonic()
        self._selected_chord: Chord | None = None
        self._manual_chord: str | None = None

    def add_note(self, note: int, velocity: int = 96, duration: float = 0.35) -> dict:
        start_time = time.monotonic() - self._time_origin
        event = NoteEvent(note=note, velocity=velocity, start_time=start_time, duration=max(duration, 0.05), beat=self._beat)
        self.buffer.add(event)
        self._beat += max(duration, 0.25)
        self._refresh_selection()
        return self.snapshot()

    def set_style(self, style: str) -> dict:
        if style in {"lofi", "jpop", "game_bgm"}:
            self.style = style
        return self.snapshot()

    def set_bias(self, bias: str) -> dict:
        if bias in {"auto", "major", "minor"}:
            self.bias = bias
        self._refresh_selection()
        return self.snapshot()

    def select_chord(self, symbol: str) -> dict:
        self._manual_chord = symbol
        self._refresh_selection()
        return self.snapshot()

    def reset(self) -> dict:
        self.buffer.clear()
        self.smoother.reset()
        self._beat = 0.0
        self._selected_chord = None
        self._manual_chord = None
        return self.snapshot()

    def load_demo(self, name: str) -> dict:
        demos = {
            "c-major": [60, 62, 64, 67, 72],
            "ambiguous": [69, 72, 76, 79, 76, 72],
            "genre-switch": [60, 64, 67, 71, 72, 76],
        }
        self.reset()
        for note in demos.get(name, demos["c-major"]):
            self.add_note(note=note, velocity=100, duration=0.4)
        return self.snapshot()

    def snapshot(self) -> dict:
        notes = self.buffer.notes
        keys = self.key_estimator.estimate(notes, bias=self.bias)
        chords = self.chord_estimator.estimate(notes, keys, previous_chord=self._selected_chord)
        confidence = chords[0].confidence if notes and chords else 0.0
        density = self._density(confidence)
        selected = self._selected_chord or (chords[0].chord if notes and chords else None)
        accompaniment_events = self.accompaniment.generate(selected, self.bpm, self.style, density) if selected else []

        return {
            "bpm": self.bpm,
            "beat": round(self._beat, 3),
            "style": self.style,
            "bias": self.bias,
            "density": density,
            "confidence": round(confidence, 3),
            "selected_chord": selected.symbol if selected else None,
            "key_candidates": [
                {"name": candidate.name, "tonic": note_name(candidate.tonic), "mode": candidate.mode, "confidence": round(candidate.confidence, 3)}
                for candidate in keys
            ],
            "chord_candidates": [
                {
                    "symbol": candidate.symbol,
                    "root": note_name(candidate.chord.root),
                    "quality": candidate.chord.quality,
                    "confidence": round(candidate.confidence, 3),
                }
                for candidate in chords
            ],
            "next_likely": [candidate.symbol for candidate in chords[1:4]],
            "recent_notes": [
                {
                    "note": event.note,
                    "name": note_name(event.pitch_class),
                    "velocity": event.velocity,
                    "duration": round(event.duration, 3),
                    "beat": round(event.beat, 3),
                }
                for event in notes[-16:]
            ],
            "accompaniment_events": [
                {
                    "part": event.part,
                    "note": event.note,
                    "beat": event.beat,
                    "duration_beats": event.duration_beats,
                    "velocity": event.velocity,
                    "channel": event.channel,
                    "time_seconds": round(event.time_seconds, 3),
                }
                for event in accompaniment_events
            ],
        }

    def _refresh_selection(self) -> None:
        notes = self.buffer.notes
        keys = self.key_estimator.estimate(notes, bias=self.bias)
        chords = self.chord_estimator.estimate(notes, keys, previous_chord=self._selected_chord)
        self._selected_chord = self.smoother.select(chords, current=self._selected_chord, beat=self._beat, manual_override=self._manual_chord)
        self._manual_chord = None

    def _density(self, confidence: float) -> str:
        if confidence < 0.35:
            return "low"
        if confidence < 0.65:
            return "medium"
        return "high"

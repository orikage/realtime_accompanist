from __future__ import annotations

from realtime_accompanist.domain.models import Chord, ChordCandidate
from realtime_accompanist.domain.theory import chord_from_symbol


class ProgressionSmoother:
    def __init__(self, min_beats_between_changes: float = 4.0, switch_margin: float = 0.1, confidence_floor: float = 0.25) -> None:
        self.min_beats_between_changes = min_beats_between_changes
        self.switch_margin = switch_margin
        self.confidence_floor = confidence_floor
        self._last_change_beat = 0.0

    def reset(self) -> None:
        self._last_change_beat = 0.0

    def select(
        self,
        candidates: list[ChordCandidate],
        current: Chord | ChordCandidate | None,
        beat: float,
        manual_override: str | None = None,
    ) -> Chord:
        if manual_override:
            chord = chord_from_symbol(manual_override)
            self._last_change_beat = beat
            return chord

        current_chord = current.chord if isinstance(current, ChordCandidate) else current
        if not candidates:
            return current_chord or chord_from_symbol("C")

        top = candidates[0]
        if current_chord is None:
            self._last_change_beat = beat
            return top.chord

        if top.confidence < self.confidence_floor:
            return current_chord

        if beat - self._last_change_beat < self.min_beats_between_changes:
            return current_chord

        if top.symbol == current_chord.symbol:
            return current_chord

        current_confidence = next((candidate.confidence for candidate in candidates if candidate.symbol == current_chord.symbol), 0.0)
        if top.confidence <= current_confidence + self.switch_margin:
            return current_chord

        self._last_change_beat = beat
        return top.chord


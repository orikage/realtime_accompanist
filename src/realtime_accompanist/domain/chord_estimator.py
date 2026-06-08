from __future__ import annotations

from realtime_accompanist.domain.models import Chord, ChordCandidate, KeyCandidate, NoteEvent
from realtime_accompanist.domain.theory import diatonic_triads, natural_minor_scale, major_scale


class ChordEstimator:
    def estimate(
        self,
        notes: list[NoteEvent],
        key_candidates: list[KeyCandidate],
        previous_chord: Chord | ChordCandidate | None = None,
        limit: int = 6,
    ) -> list[ChordCandidate]:
        key = key_candidates[0] if key_candidates else KeyCandidate(0, "major", 0.0, 0.0)
        chords = self._candidate_chords(key)
        previous = previous_chord.chord if isinstance(previous_chord, ChordCandidate) else previous_chord

        if not notes:
            return [ChordCandidate(chord=chord, score=0.0, confidence=0.0) for chord in chords[:limit]]

        scored = [ChordCandidate(chord=chord, score=self._score(chord, notes, key, previous), confidence=0.0) for chord in chords]
        max_score = max((candidate.score for candidate in scored), default=0.0)
        if max_score <= 0:
            normalized = [ChordCandidate(candidate.chord, candidate.score, 0.0) for candidate in scored]
        else:
            normalized = [
                ChordCandidate(candidate.chord, candidate.score, max(0.0, min(candidate.score / max_score, 1.0)))
                for candidate in scored
            ]

        normalized.sort(key=lambda candidate: (-candidate.confidence, -candidate.score, candidate.chord.symbol))
        return normalized[:limit]

    def _candidate_chords(self, key: KeyCandidate) -> list[Chord]:
        chords = diatonic_triads(key.tonic, key.mode)
        # Keep relative major/minor interpretations visible for ambiguous melodies.
        relative_tonic = (key.tonic + (3 if key.mode == "minor" else 9)) % 12
        relative_mode = "major" if key.mode == "minor" else "minor"
        by_symbol = {chord.symbol: chord for chord in chords}
        for chord in diatonic_triads(relative_tonic, relative_mode):
            by_symbol.setdefault(chord.symbol, chord)
        return list(by_symbol.values())

    def _score(self, chord: Chord, notes: list[NoteEvent], key: KeyCandidate, previous: Chord | None) -> float:
        scale = natural_minor_scale(key.tonic) if key.mode == "minor" else major_scale(key.tonic)
        score = 1.0
        for index, event in enumerate(notes):
            weight = self._weight(event, index, len(notes))
            pc = event.pitch_class
            if pc in chord.tones:
                score += 1.0 * weight
                if pc == chord.root:
                    score += 0.35 * weight
            elif pc in scale:
                score += 0.1 * weight
            else:
                score -= 0.35 * weight

        if chord.roman in {"I", "i", "IV", "iv", "V", "v", "vi", "VI"}:
            score += 0.3
        if previous is not None:
            score += self._transition_score(previous, chord)
        return max(score, 0.0)

    def _weight(self, event: NoteEvent, index: int, length: int) -> float:
        velocity = max(min(event.velocity, 127), 0) / 127
        recency = 1.0 + (index / max(length - 1, 1)) * 0.25
        return max(event.duration, 0.05) * (0.5 + velocity) * recency

    def _transition_score(self, previous: Chord, chord: Chord) -> float:
        if previous.symbol == chord.symbol:
            return 0.1
        root_motion = (chord.root - previous.root) % 12
        if root_motion in {5, 7, 9}:
            return 0.25
        if root_motion in {1, 6, 11}:
            return -0.2
        return 0.0

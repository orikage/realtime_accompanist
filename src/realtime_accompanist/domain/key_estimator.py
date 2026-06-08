from __future__ import annotations

from realtime_accompanist.domain.models import KeyCandidate, NoteEvent
from realtime_accompanist.domain.theory import chord_tones, major_scale, natural_minor_scale


class KeyEstimator:
    def estimate(self, notes: list[NoteEvent], limit: int = 6, bias: str = "auto") -> list[KeyCandidate]:
        candidates: list[tuple[int, str, float]] = []
        for tonic in range(12):
            candidates.append((tonic, "major", self._score(notes, tonic, "major", bias)))
            candidates.append((tonic, "minor", self._score(notes, tonic, "minor", bias)))

        max_score = max((score for _, _, score in candidates), default=0.0)
        if not notes or max_score <= 0:
            ranked = [KeyCandidate(tonic, mode, score, 0.0) for tonic, mode, score in candidates]
        else:
            ranked = [KeyCandidate(tonic, mode, score, max(0.0, min(score / max_score, 1.0))) for tonic, mode, score in candidates]

        ranked.sort(key=lambda candidate: (-candidate.confidence, -candidate.score, candidate.tonic, candidate.mode))
        return ranked[:limit]

    def _score(self, notes: list[NoteEvent], tonic: int, mode: str, bias: str) -> float:
        scale = natural_minor_scale(tonic) if mode == "minor" else major_scale(tonic)
        dominant = (tonic + 7) % 12
        score = 0.0

        for index, event in enumerate(notes):
            weight = self._weight(event, index, len(notes))
            pc = event.pitch_class
            score += (1.0 if pc in scale else -0.75) * weight
            if pc == tonic:
                score += 0.75 * weight
            if pc == dominant:
                score += 0.25 * weight
            if index == 0 and pc == tonic:
                score += 0.25 * weight
            if index == len(notes) - 1 and pc == tonic:
                score += 0.75 * weight

        present = {event.pitch_class for event in notes}
        tonic_quality = "minor" if mode == "minor" else "major"
        tonic_triad = chord_tones(tonic, tonic_quality)
        if len(present & tonic_triad) >= 3:
            score += 1.4
        elif len(present & tonic_triad) == 2:
            score += 0.35

        if bias == mode:
            score += max(0.35, 0.08 * len(notes))
        elif bias in {"major", "minor"}:
            score -= 0.15
        return score

    def _weight(self, event: NoteEvent, index: int, length: int) -> float:
        duration = max(event.duration, 0.05)
        velocity = max(min(event.velocity, 127), 0) / 127
        recency = 1.0 + (index / max(length - 1, 1)) * 0.35
        strong_beat = 1.2 if abs(event.beat - round(event.beat)) < 0.05 else 1.0
        return duration * (0.6 + velocity) * recency * strong_beat

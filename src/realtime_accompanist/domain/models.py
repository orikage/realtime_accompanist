from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NoteEvent:
    note: int
    velocity: int
    start_time: float
    duration: float
    beat: float = 0.0

    @property
    def pitch_class(self) -> int:
        return self.note % 12


@dataclass(frozen=True)
class KeyCandidate:
    tonic: int
    mode: str
    score: float
    confidence: float

    @property
    def name(self) -> str:
        from realtime_accompanist.domain.theory import note_name

        return f"{note_name(self.tonic)} {self.mode}"


@dataclass(frozen=True)
class Chord:
    symbol: str
    root: int
    quality: str
    tones: set[int] = field(default_factory=set)
    roman: str | None = None


@dataclass(frozen=True)
class ChordCandidate:
    chord: Chord
    score: float
    confidence: float

    @property
    def symbol(self) -> str:
        return self.chord.symbol


@dataclass(frozen=True)
class AccompanimentEvent:
    part: str
    note: int
    beat: float
    duration_beats: float
    velocity: int
    channel: int
    time_seconds: float


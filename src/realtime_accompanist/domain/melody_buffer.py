from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from realtime_accompanist.domain.models import NoteEvent


class MelodyBuffer:
    def __init__(self, max_events: int = 128) -> None:
        self._events: deque[NoteEvent] = deque(maxlen=max_events)

    @property
    def notes(self) -> list[NoteEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()

    def add(self, event: NoteEvent) -> None:
        self._events.append(event)

    def extend(self, events: Iterable[NoteEvent]) -> None:
        for event in events:
            self.add(event)

    def recent_seconds(self, now: float, seconds: float) -> list[NoteEvent]:
        cutoff = now - max(seconds, 0.0)
        return [event for event in self._events if event.start_time >= cutoff]

    def recent_beats(self, current_beat: float, beats: float) -> list[NoteEvent]:
        cutoff = current_beat - max(beats, 0.0)
        return [event for event in self._events if event.beat >= cutoff]

    def pitch_class_histogram(self, now: float | None = None, window_seconds: float | None = None) -> dict[int, float]:
        if not self._events:
            return {}

        reference_time = now if now is not None else max(event.start_time for event in self._events)
        events = self.notes
        if window_seconds is not None:
            events = [event for event in events if event.start_time >= reference_time - window_seconds]

        histogram: dict[int, float] = {}
        for event in events:
            duration = max(event.duration, 0.05)
            velocity = max(min(event.velocity, 127), 0) / 127
            age = max(reference_time - event.start_time, 0.0)
            recency = 1.0 / (1.0 + age * 0.35)
            strong_beat = 1.2 if abs(event.beat - round(event.beat)) < 0.05 else 1.0
            weight = duration * (0.5 + velocity) * recency * strong_beat
            histogram[event.pitch_class] = histogram.get(event.pitch_class, 0.0) + weight
        return histogram


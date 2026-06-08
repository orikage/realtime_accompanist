from __future__ import annotations

import time


class MusicalClock:
    def __init__(self, bpm: float = 90.0, beats_per_bar: int = 4) -> None:
        self._bpm = max(bpm, 20.0)
        self._beats_per_bar = beats_per_bar
        self._origin: float | None = None
        self._running = False
        self._accumulated_seconds = 0.0

    @property
    def bpm(self) -> float:
        return self._bpm

    @bpm.setter
    def bpm(self, value: float) -> None:
        if self._running:
            self._accumulated_seconds = self.elapsed_seconds
            self._origin = time.monotonic()
        self._bpm = max(value, 20.0)

    @property
    def beats_per_bar(self) -> int:
        return self._beats_per_bar

    @property
    def running(self) -> bool:
        return self._running

    @property
    def elapsed_seconds(self) -> float:
        if self._origin is None:
            return self._accumulated_seconds
        if not self._running:
            return self._accumulated_seconds
        return self._accumulated_seconds + (time.monotonic() - self._origin)

    @property
    def beat(self) -> float:
        return self.elapsed_seconds * self._bpm / 60.0

    @property
    def bar(self) -> int:
        return int(self.beat // self._beats_per_bar)

    @property
    def beat_in_bar(self) -> float:
        return self.beat % self._beats_per_bar

    @property
    def is_bar_boundary(self) -> bool:
        return self.beat_in_bar < 0.1

    @property
    def is_beat_boundary(self) -> bool:
        return (self.beat % 1.0) < 0.1

    def start(self) -> None:
        if self._running:
            return
        self._origin = time.monotonic()
        self._running = True

    def stop(self) -> None:
        if not self._running:
            return
        self._accumulated_seconds = self.elapsed_seconds
        self._origin = None
        self._running = False

    def reset(self) -> None:
        self._origin = time.monotonic() if self._running else None
        self._accumulated_seconds = 0.0

    def beat_at(self, timestamp: float) -> float:
        if self._origin is None:
            return 0.0
        elapsed = self._accumulated_seconds + (timestamp - self._origin)
        return max(elapsed, 0.0) * self._bpm / 60.0

    def seconds_until_next_bar(self) -> float:
        beats_left = self._beats_per_bar - self.beat_in_bar
        if beats_left <= 0.05:
            beats_left = float(self._beats_per_bar)
        return beats_left * 60.0 / self._bpm

    def seconds_until_next_beat(self) -> float:
        frac = self.beat % 1.0
        beats_left = 1.0 - frac
        if beats_left <= 0.05:
            beats_left = 1.0
        return beats_left * 60.0 / self._bpm

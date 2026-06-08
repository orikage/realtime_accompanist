import time

from realtime_accompanist.domain.clock import MusicalClock


def test_clock_starts_stopped():
    clock = MusicalClock(bpm=120)
    assert not clock.running
    assert clock.beat == 0.0
    assert clock.bar == 0


def test_clock_tracks_beat_and_bar():
    clock = MusicalClock(bpm=120, beats_per_bar=4)
    clock.start()
    time.sleep(0.15)
    assert clock.beat > 0
    assert clock.elapsed_seconds > 0


def test_clock_stop_freezes_position():
    clock = MusicalClock(bpm=120)
    clock.start()
    time.sleep(0.05)
    clock.stop()
    beat_at_stop = clock.beat
    time.sleep(0.05)
    assert clock.beat == beat_at_stop


def test_clock_reset_returns_to_zero():
    clock = MusicalClock(bpm=120)
    clock.start()
    time.sleep(0.05)
    clock.reset()
    assert clock.beat < 0.1


def test_bpm_change_preserves_accumulated_position():
    clock = MusicalClock(bpm=120)
    clock.start()
    time.sleep(0.1)
    clock.stop()
    elapsed = clock.elapsed_seconds
    clock.start()
    clock.bpm = 60
    assert clock.elapsed_seconds >= elapsed * 0.8


def test_bar_boundary_detection():
    clock = MusicalClock(bpm=120, beats_per_bar=4)
    assert clock.is_bar_boundary


def test_seconds_until_next_bar():
    clock = MusicalClock(bpm=120, beats_per_bar=4)
    expected = 4 * 60.0 / 120.0
    assert abs(clock.seconds_until_next_bar() - expected) < 0.2


def test_beat_at_timestamp():
    clock = MusicalClock(bpm=120)
    clock.start()
    origin = clock._origin
    beat = clock.beat_at(origin + 1.0)
    assert abs(beat - 2.0) < 0.3

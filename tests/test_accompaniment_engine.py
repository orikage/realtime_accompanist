from realtime_accompanist.domain.accompaniment import AccompanimentEngine
from realtime_accompanist.domain.models import Chord


def chord(symbol="C", root=0, quality="major"):
    return Chord(symbol=symbol, root=root, quality=quality, tones={root, (root + 4) % 12, (root + 7) % 12})


def test_engine_generates_bass_pad_and_drums_from_chord():
    events = AccompanimentEngine().generate(chord(), bpm=90, style="lofi", density="high")
    parts = {event.part for event in events}

    assert {"drums", "bass", "pad"} <= parts
    assert any(event.note % 12 == 0 for event in events if event.part == "bass")


def test_density_controls_event_count():
    engine = AccompanimentEngine()
    low = engine.generate(chord(), bpm=90, style="lofi", density="low")
    high = engine.generate(chord(), bpm=90, style="lofi", density="high")

    assert len(high) > len(low)


def test_tempo_changes_do_not_change_beat_grid():
    engine = AccompanimentEngine()
    slow = engine.generate(chord(), bpm=70, style="jpop", density="medium")
    fast = engine.generate(chord(), bpm=140, style="jpop", density="medium")
    slow_after_downbeat = next(event for event in slow if event.beat > 0)
    fast_after_downbeat = next(event for event in fast if event.beat == slow_after_downbeat.beat)

    assert [event.beat for event in slow] == [event.beat for event in fast]
    assert slow_after_downbeat.time_seconds > fast_after_downbeat.time_seconds


def test_unknown_style_and_chord_do_not_crash():
    events = AccompanimentEngine().generate(chord(symbol="Mystery", root=1, quality="unknown"), style="unknown")

    assert events

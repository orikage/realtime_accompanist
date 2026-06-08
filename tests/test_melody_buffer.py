from realtime_accompanist.domain.melody_buffer import MelodyBuffer
from realtime_accompanist.domain.models import NoteEvent


def test_buffer_keeps_recent_notes_and_limits_length():
    buffer = MelodyBuffer(max_events=3)
    for index, note in enumerate([60, 62, 64, 65]):
        buffer.add(NoteEvent(note=note, velocity=80, start_time=float(index), duration=0.25, beat=float(index)))

    assert [event.note for event in buffer.notes] == [62, 64, 65]
    assert [event.note for event in buffer.recent_seconds(now=3.0, seconds=1.1)] == [64, 65]


def test_histogram_weights_duration_velocity_recency_and_strong_beat():
    buffer = MelodyBuffer()
    buffer.add(NoteEvent(note=60, velocity=110, start_time=0.0, duration=1.0, beat=0.0))
    buffer.add(NoteEvent(note=62, velocity=60, start_time=0.0, duration=0.2, beat=0.5))

    histogram = buffer.pitch_class_histogram(now=1.0)

    assert histogram[0] > histogram[2]
    assert sum(histogram.values()) > 0


def test_empty_buffer_histogram_is_safe():
    assert MelodyBuffer().pitch_class_histogram(now=0.0) == {}


from realtime_accompanist.domain.key_estimator import KeyEstimator
from realtime_accompanist.domain.models import NoteEvent


def notes(sequence):
    return [
        NoteEvent(note=note, velocity=90, start_time=index * 0.25, duration=0.25, beat=float(index))
        for index, note in enumerate(sequence)
    ]


def test_c_major_phrase_ranks_c_major_first():
    result = KeyEstimator().estimate(notes([60, 62, 64, 67, 64, 62, 60]))

    assert result[0].name == "C major"
    assert result[0].confidence > 0.55


def test_a_minor_phrase_keeps_a_minor_near_top():
    result = KeyEstimator().estimate(notes([69, 72, 76, 79, 76, 72, 69]), limit=4)

    assert "A minor" in [candidate.name for candidate in result[:2]]


def test_strange_and_empty_input_do_not_crash():
    result = KeyEstimator().estimate([NoteEvent(note=200, velocity=0, start_time=0, duration=-1, beat=0)])
    assert result

    empty = KeyEstimator().estimate([])
    assert empty[0].name == "C major"
    assert empty[0].confidence == 0.0


def test_bias_can_nudge_major_or_minor_candidates():
    phrase = notes([60, 64, 67, 69])
    major = KeyEstimator().estimate(phrase, bias="major")[0]
    minor = KeyEstimator().estimate(phrase, bias="minor")[0]

    assert major.mode == "major"
    assert minor.mode == "minor"


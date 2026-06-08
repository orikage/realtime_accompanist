from realtime_accompanist.domain.chord_estimator import ChordEstimator
from realtime_accompanist.domain.key_estimator import KeyEstimator
from realtime_accompanist.domain.models import NoteEvent


def notes(sequence):
    return [
        NoteEvent(note=note, velocity=96, start_time=index * 0.25, duration=0.5, beat=float(index))
        for index, note in enumerate(sequence)
    ]


def estimate(sequence, bias="auto"):
    melody = notes(sequence)
    keys = KeyEstimator().estimate(melody, bias=bias)
    return ChordEstimator().estimate(melody, keys)


def test_c_triad_ranks_c_first():
    chords = estimate([60, 64, 67, 72], bias="major")

    assert chords[0].symbol == "C"
    assert chords[0].confidence > 0.5


def test_a_c_e_g_ranks_am_and_c_high():
    chords = estimate([69, 72, 76, 79], bias="minor")
    top = [candidate.symbol for candidate in chords[:3]]

    assert "Am" in top
    assert "C" in top


def test_f_a_c_ranks_f_in_c_major_context():
    melody = notes([65, 69, 72])
    keys = KeyEstimator().estimate(notes([60, 62, 64, 65, 67, 69, 71, 72]), bias="major")
    chords = ChordEstimator().estimate(melody, keys)

    assert chords[0].symbol == "F"


def test_single_note_and_empty_input_are_safe():
    single = estimate([64])
    assert single

    empty = ChordEstimator().estimate([], KeyEstimator().estimate([]))
    assert empty
    assert all(0.0 <= candidate.confidence <= 1.0 for candidate in empty)


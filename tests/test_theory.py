from realtime_accompanist.domain.theory import (
    chord_tones,
    diatonic_triads,
    major_scale,
    natural_minor_scale,
    note_name,
    pitch_class,
)


def test_pitch_class_and_note_name_wrap_midi_values():
    assert pitch_class(60) == 0
    assert pitch_class(73) == 1
    assert note_name(13) == "C#/Db"


def test_scales_are_returned_as_pitch_classes():
    assert major_scale(0) == {0, 2, 4, 5, 7, 9, 11}
    assert natural_minor_scale(9) == {9, 11, 0, 2, 4, 5, 7}


def test_chord_tones_support_basic_qualities():
    assert chord_tones(0, "major") == {0, 4, 7}
    assert chord_tones(9, "minor") == {9, 0, 4}
    assert chord_tones(11, "diminished") == {11, 2, 5}
    assert chord_tones(0, "fifth") == {0, 7}


def test_diatonic_triads_for_c_major_and_a_minor():
    c_major = diatonic_triads(0, "major")
    assert [chord.symbol for chord in c_major[:6]] == ["C", "Dm", "Em", "F", "G", "Am"]

    a_minor = diatonic_triads(9, "minor")
    assert [chord.symbol for chord in a_minor[:4]] == ["Am", "Bdim", "C", "Dm"]


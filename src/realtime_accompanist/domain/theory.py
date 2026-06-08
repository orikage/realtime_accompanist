from __future__ import annotations

from realtime_accompanist.domain.models import Chord

NOTE_NAMES = ("C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B")
MAJOR_INTERVALS = (0, 2, 4, 5, 7, 9, 11)
NATURAL_MINOR_INTERVALS = (0, 2, 3, 5, 7, 8, 10)


def pitch_class(note: int) -> int:
    return note % 12


def note_name(pc: int) -> str:
    return NOTE_NAMES[pc % 12]


def major_scale(root_pc: int) -> set[int]:
    return {(root_pc + interval) % 12 for interval in MAJOR_INTERVALS}


def natural_minor_scale(root_pc: int) -> set[int]:
    return {(root_pc + interval) % 12 for interval in NATURAL_MINOR_INTERVALS}


def chord_tones(root_pc: int, quality: str) -> set[int]:
    quality = quality.lower()
    intervals = {
        "major": (0, 4, 7),
        "minor": (0, 3, 7),
        "diminished": (0, 3, 6),
        "sus": (0, 5, 7),
        "fifth": (0, 7),
        "unknown": (0, 7),
    }.get(quality, (0, 7))
    return {(root_pc + interval) % 12 for interval in intervals}


def chord_symbol(root_pc: int, quality: str) -> str:
    root = note_name(root_pc)
    if quality == "major":
        return root
    if quality == "minor":
        return f"{root}m"
    if quality == "diminished":
        return f"{root}dim"
    if quality == "sus":
        return f"{root}sus"
    if quality == "fifth":
        return f"{root}5"
    return root


def diatonic_triads(root_pc: int, mode: str) -> list[Chord]:
    if mode == "minor":
        degrees = NATURAL_MINOR_INTERVALS
        qualities = ("minor", "diminished", "major", "minor", "minor", "major", "major")
        romans = ("i", "ii°", "III", "iv", "v", "VI", "VII")
    else:
        degrees = MAJOR_INTERVALS
        qualities = ("major", "minor", "minor", "major", "major", "minor", "diminished")
        romans = ("I", "ii", "iii", "IV", "V", "vi", "vii°")

    chords: list[Chord] = []
    for interval, quality, roman in zip(degrees, qualities, romans):
        chord_root = (root_pc + interval) % 12
        chords.append(
            Chord(
                symbol=chord_symbol(chord_root, quality),
                root=chord_root,
                quality=quality,
                tones=chord_tones(chord_root, quality),
                roman=roman,
            )
        )
    return chords


def chord_from_symbol(symbol: str) -> Chord:
    normalized = symbol.strip()
    if not normalized:
        normalized = "C"

    quality = "major"
    root_name = normalized
    if normalized.endswith("dim"):
        quality = "diminished"
        root_name = normalized[:-3]
    elif normalized.endswith("sus"):
        quality = "sus"
        root_name = normalized[:-3]
    elif normalized.endswith("5"):
        quality = "fifth"
        root_name = normalized[:-1]
    elif normalized.endswith("m") and len(normalized) > 1:
        quality = "minor"
        root_name = normalized[:-1]

    root_lookup = {
        "C": 0,
        "C#": 1,
        "Db": 1,
        "D": 2,
        "D#": 3,
        "Eb": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "Gb": 6,
        "G": 7,
        "G#": 8,
        "Ab": 8,
        "A": 9,
        "A#": 10,
        "Bb": 10,
        "B": 11,
    }
    root = root_lookup.get(root_name, 0)
    return Chord(symbol=chord_symbol(root, quality), root=root, quality=quality, tones=chord_tones(root, quality))


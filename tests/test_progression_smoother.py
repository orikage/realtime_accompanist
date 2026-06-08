from realtime_accompanist.domain.models import Chord, ChordCandidate
from realtime_accompanist.domain.progression_smoother import ProgressionSmoother


def candidate(symbol, root, confidence):
    return ChordCandidate(
        chord=Chord(symbol=symbol, root=root, quality="major", tones={root, (root + 4) % 12, (root + 7) % 12}),
        score=confidence,
        confidence=confidence,
    )


def test_smoother_holds_current_when_candidate_barely_wins():
    smoother = ProgressionSmoother(min_beats_between_changes=0.0, switch_margin=0.15)
    current = candidate("C", 0, 0.6)
    selected = smoother.select([candidate("G", 7, 0.68), current], current=current, beat=4.0)

    assert selected.symbol == "C"


def test_smoother_allows_stronger_candidate_at_boundary():
    smoother = ProgressionSmoother(min_beats_between_changes=4.0, switch_margin=0.08)
    current = candidate("C", 0, 0.55)
    selected = smoother.select([candidate("G", 7, 0.8), current], current=current, beat=4.0)

    assert selected.symbol == "G"


def test_manual_override_wins_once():
    smoother = ProgressionSmoother()
    selected = smoother.select([candidate("C", 0, 0.5)], current=None, beat=0.0, manual_override="Am")

    assert selected.symbol == "Am"


def test_low_confidence_keeps_current_chord():
    smoother = ProgressionSmoother(confidence_floor=0.35)
    current = candidate("C", 0, 0.7)
    selected = smoother.select([candidate("F", 5, 0.2)], current=current, beat=8.0)

    assert selected.symbol == "C"


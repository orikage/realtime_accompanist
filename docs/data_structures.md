# Data Structures

## NoteEvent

```python
@dataclass
class NoteEvent:
    note: int
    velocity: int
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    start_beat: float | None = None
    end_beat: float | None = None
    channel: int | None = None
```

## KeyCandidate

```python
@dataclass
class KeyCandidate:
    root_pc: int
    mode: Literal["major", "minor"]
    name: str
    score: float
    confidence: float
```

## ChordCandidate

```python
@dataclass
class ChordCandidate:
    root_pc: int
    quality: str
    name: str
    roman: str | None
    tones: tuple[int, ...]
    score: float
    confidence: float
```

## SelectedChord

```python
@dataclass
class SelectedChord:
    chord: ChordCandidate
    selected_at_bar: int
    selected_at_beat: float
    source: Literal["auto", "manual", "lock"]
```

## SystemState

```python
@dataclass
class SystemState:
    running: bool
    bpm: float
    bar: int
    beat: float
    style: str
    mode_bias: Literal["auto", "major", "minor"]
    key_lock: str | None
    chord_lock: str | None
    key_candidates: list[KeyCandidate]
    chord_candidates: list[ChordCandidate]
    selected_key: KeyCandidate | None
    selected_chord: SelectedChord | None
    confidence: float
    density: float
```

## Pattern JSON Example

```json
{
  "name": "lofi",
  "bpm_default": 82,
  "channels": {
    "drums": 10,
    "bass": 2,
    "chords": 3,
    "arp": 4
  },
  "density_levels": {
    "low": {
      "drums": true,
      "bass": false,
      "chords": "sparse",
      "arp": false
    },
    "medium": {
      "drums": true,
      "bass": true,
      "chords": "sparse",
      "arp": false
    },
    "high": {
      "drums": true,
      "bass": true,
      "chords": "full",
      "arp": true
    }
  },
  "bass_pattern": [
    {"beat": 1.0, "degree": 1, "duration": 0.5},
    {"beat": 2.5, "degree": 5, "duration": 0.5},
    {"beat": 3.0, "degree": 1, "duration": 0.5}
  ],
  "chord_pattern": [
    {"beat": 1.0, "voicing": "closed", "duration": 1.5},
    {"beat": 3.0, "voicing": "closed", "duration": 1.0}
  ],
  "drum_pattern": [
    {"beat": 1.0, "note": 36, "velocity": 80},
    {"beat": 2.0, "note": 38, "velocity": 70},
    {"beat": 3.0, "note": 36, "velocity": 75},
    {"beat": 4.0, "note": 38, "velocity": 70}
  ]
}
```

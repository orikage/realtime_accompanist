# Codex Task Breakdown

## Task 1: Project skeleton

Create a Python project with modules:

- app/main.py
- app/models.py
- app/theory.py
- app/melody_buffer.py
- app/key_estimator.py
- app/chord_estimator.py
- app/progression_smoother.py
- app/midi_input.py
- app/clock.py
- app/accompaniment.py
- app/sound_engine.py
- tests/

Use pyproject.toml.

## Task 2: Music theory primitives

Implement:

- pitch_class(note: int) -> int
- note_name(pc: int) -> str
- major_scale(root_pc)
- natural_minor_scale(root_pc)
- triads for major/minor keys
- chord tones for major, minor, diminished, sus, fifth/no3 optional

## Task 3: Melody buffer

Implement a buffer that stores recent note events.

Requirements:

- add note_on/note_off or finalized NoteEvent
- get notes within last N seconds
- get notes within last N beats if clock available
- compute weighted pitch-class histogram

Weighting:

- duration weight
- velocity weight
- recency weight
- strong beat bonus

## Task 4: Key estimator

Implement rule-based key estimation.

Input:

- list of NoteEvent or pitch-class histogram

Output:

- ranked KeyCandidate list

Candidate keys:

- 12 major
- 12 natural minor

Scoring:

- scale membership
- tonic weight
- dominant weight
- final note bonus
- long note bonus

Tests:

- C D E G E D C should rank C major high
- A C E G should rank A minor and C major high
- F G A C should rank F major high

## Task 5: Chord estimator

Implement chord candidate scoring.

Input:

- recent notes
- key candidates
- previous selected chord

Output:

- ranked ChordCandidate list

Candidate chords:

For selected or top key:

Major key diatonic triads:
I, ii, iii, IV, V, vi, vii°

Minor key diatonic triads:
i, ii°, III, iv, v, VI, VII

Scoring:

- note in chord tones
- melody emphasis on root/third/fifth
- chord is diatonic in key
- previous chord transition preference
- bass movement penalty
- repetition penalty optional

Tests:

- notes A C E G should rank Am and C high
- notes C E G should rank C high
- notes F A C should rank F high in C major context

## Task 6: Progression smoother

Implement a selector that chooses one chord at bar boundaries.

Rules:

- avoid changing chord if new top candidate barely beats current
- prefer common progressions
- penalize large root motion if not musically common
- hold previous chord when confidence is low
- allow manual override from UI

## Task 7: MIDI input

Implement basic MIDI input using mido/python-rtmidi.

Requirements:

- list available devices
- select device by name or first available
- parse note_on/note_off
- produce NoteEvent with duration
- handle note_on velocity=0 as note_off

## Task 8: CLI prototype

Create a CLI that:

- reads MIDI input
- updates estimates
- prints top keys and chords every 250ms

## Task 9: Sound output

Implement minimal sound engine.

Options:

- send MIDI out to external synth/DAW
- use FluidSynth if installed

Requirements:

- play chord pad
- play bass note
- all notes off panic

## Task 10: Accompaniment engine

Implement pattern-driven accompaniment.

Pattern JSON should define:

- drum events
- bass pattern relative to chord root
- chord rhythm
- instrument channels
- density levels

Initial style: Lo-fi.

## Task 11: Web UI

Implement a simple Web UI.

Backend:

- FastAPI
- WebSocket state updates

Frontend:

- current key candidates
- current chord candidates
- selected chord
- confidence
- style
- buttons for style/chord/major-minor/key lock

## Task 12: Demo mode

Implement deterministic demo mode without real MIDI.

It should feed predefined note sequences for:

- C major demo
- ambiguous Am/C demo
- genre switch demo

This is useful when hardware is unavailable.

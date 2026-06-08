# Architecture

## Overall

```text
MIDI Keyboard (or Web Keyboard)
  |
  v
Note Input (note_on / note_off / add_note)
  |
  v
Melody Buffer (ring buffer, max 128 events)
  |
  +-- recent_beats(KEY_WINDOW=16) --> Key Estimator
  |                                     |
  +-- recent_beats(CHORD_WINDOW=4) --> Chord Estimator
  |                                     |
  v                                     v
Musical Clock (BPM, beat, bar)     Chord Candidates
  |                                     |
  +-- bar boundary tick ----------> Progression Smoother
                                        |
                                        v
                                   Selected Chord
                                        |
                                        v
                                   Accompaniment Engine
                                        |
                                        v
                                   Accompaniment Events
                                        |
                                        v
                                   WebSocket broadcast --> Web UI
                                        |
                                        v
                                   Browser WebAudio (continuous loop)
```

## Processing Loop

1. User plays notes (MIDI or Web keyboard)
2. `note_on` → buffer records start time; `note_off` → computes duration, adds to buffer
3. On every server tick (~100ms):
   - Check if bar boundary crossed
   - If yes: run windowed estimation → smoother selects chord → regenerate accompaniment
4. `snapshot()` always uses windowed data:
   - Key estimation: last **16 beats** (~4 bars at 4/4)
   - Chord estimation: last **4 beats** (~1 bar at 4/4)
5. WebSocket broadcasts state to all connected clients
6. Client plays accompaniment as a **continuous loop** (one bar at a time, repeating)

## Modules

### clock (NEW)

Responsibilities:

- BPM-based beat/bar position tracking
- Bar boundary detection
- Seconds-to-next-beat/bar calculation
- Start/stop/reset lifecycle

### melody_buffer

Responsibilities:

- Ring buffer of recent NoteEvents (max 128)
- Window queries: `recent_seconds()`, `recent_beats()`
- Pitch class histogram with duration/velocity/recency weighting

### key_estimator

Responsibilities:

- 12 tonic × 2 mode (major/minor) candidate scoring
- Windowed input: receives only last 16 beats of notes
- Scale match, tonic/dominant emphasis, phrase start/end weighting
- Major/Minor bias support

### chord_estimator

Responsibilities:

- Diatonic triad candidates from estimated key
- Windowed input: receives only last 4 beats of notes
- Melody-to-chord-tone matching with duration/velocity weighting
- Root motion transition scoring
- Relative major/minor cross-candidates for ambiguous melodies

### progression_smoother

Responsibilities:

- Prevents chord flickering (min 4 beats between changes)
- Confidence floor: holds current chord if top candidate is too weak
- Switch margin: requires top candidate to clearly beat current
- Manual override support
- Chord changes only at bar boundaries (enforced by session tick)

### accompaniment_engine

Responsibilities:

- Style-specific drum/bass/pad patterns (lofi, jpop, game_bgm)
- Density control: low/medium/high based on confidence
- MIDI-compatible event generation

### session (application layer)

Responsibilities:

- Owns clock, buffer, estimators, smoother, accompaniment engine
- `note_on` / `note_off` for real-time MIDI-style input
- `add_note` for simplified web input (instant duration)
- `tick()` called by server loop: checks bar boundary, runs estimation pipeline
- `snapshot()` returns full UI state with windowed estimation
- Key lock, style change, bias change, manual chord override, reset

### web app (FastAPI)

Responsibilities:

- REST API for note input and controls
- WebSocket state broadcast
- Lifespan-managed tick loop (~100ms interval)
- Static file serving for Web UI

## State Model

```python
{
    "bpm": 90.0,
    "beat": 12.5,
    "bar": 3,
    "beat_in_bar": 0.5,
    "style": "lofi",
    "bias": "auto",
    "key_lock": false,
    "density": "medium",
    "confidence": 0.72,
    "selected_chord": "Am",
    "key_candidates": [...],
    "chord_candidates": [...],
    "next_likely": ["F", "Dm", "G"],
    "recent_notes": [...],
    "accompaniment_events": [...],
    "clock_running": true
}
```

## Quantization Policy

- UI state: updated immediately on note input and on every tick
- Chord selection: only at **bar boundaries** (via tick loop)
- Manual chord override: applied immediately (force flag)
- Accompaniment regeneration: on chord change or style change
- Client playback: continuous bar-length loop

## Key Design Decisions

1. **Windowed estimation, not full-history**: Key uses 16-beat window, chord uses 4-beat window. This matches R2/R3 requirements and ensures the system responds to the melody being played *now*, not notes from minutes ago.

2. **Bar-boundary chord changes**: Chord selection happens at bar boundaries, not on every note. This prevents the "chord flickering" problem and produces musically natural transitions (R5).

3. **Continuous accompaniment loop**: The client plays accompaniment in a repeating bar-length loop. New chord selections update the loop content, but the rhythm doesn't restart on every note.

4. **note_on/note_off separation**: Supports real MIDI-style input with held notes and measured durations, while `add_note` provides a convenience method for web input.

5. **Clock-driven tick**: The server runs a ~100ms tick loop that drives the estimation pipeline. This decouples note input timing from chord selection timing.

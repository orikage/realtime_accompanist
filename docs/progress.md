# Progress And Handoff

Last updated: 2026-06-08 JST

## Current Status

The system has been rearchitected to match the original requirements: **phrase-based windowed estimation** with a **musical clock** driving chord changes at **bar boundaries**, and **continuous accompaniment loop** playback.

Previous state: single-note reactive system (every note triggered full-history re-estimation and one-shot accompaniment).

Current state: clock-driven, window-based estimation with continuous bar-looping accompaniment.

## Key Changes In This Session

### 1. Musical Clock (`domain/clock.py`) — NEW
- BPM-based beat/bar position tracking
- Bar/beat boundary detection
- Start/stop/reset lifecycle
- BPM changes preserve accumulated position

### 2. Windowed Estimation — FIXED
- **Key estimation**: uses last 16 beats (~4 bars) via `MelodyBuffer.recent_beats()`
- **Chord estimation**: uses last 4 beats (~1 bar) via `MelodyBuffer.recent_beats()`
- Previously used full note history (100+ notes), now uses contextually relevant window
- Matches R2 ("直近2〜4小節") and R3 ("直近1小節") requirements

### 3. Session Rearchitecture — MAJOR CHANGE
- `tick()` method called by server loop every ~100ms
- Chord changes only at bar boundaries (not on every note input)
- `note_on`/`note_off` for real MIDI-style input with measured duration
- `add_note` preserved for simplified web input
- Key lock feature added
- Demo phrases now use realistic beat-positioned notes

### 4. Continuous Accompaniment — FIXED
- Server tick loop broadcasts state via WebSocket
- Client plays accompaniment in repeating bar-length loop
- Chord changes update loop content without restarting rhythm
- Note input and accompaniment playback are decoupled

### 5. FastAPI Modernization
- Migrated from deprecated `on_event` to `lifespan` context manager
- Added `/api/note-on`, `/api/note-off`, `/api/controls/key-lock` endpoints

## Repository State

- Branch: `claude/amazing-roentgen-6f5205`
- Working tree: modified (not yet committed)

## Test Status

```text
47 passed
Total coverage: 90.55%
Coverage gate: 85%
```

New tests added:
- `test_clock.py`: 8 tests for MusicalClock
- `test_session_api.py`: expanded from 6 to 14 tests (windowed estimation, tick, note_on/off, key lock, demo phrases)

## Architecture Snapshot

```text
src/realtime_accompanist/
  domain/
    clock.py           NEW — Musical clock with BPM/beat/bar tracking
    melody_buffer.py   Window query methods now used by session
    key_estimator.py   Unchanged (receives windowed input from session)
    chord_estimator.py Unchanged (receives windowed input from session)
    progression_smoother.py  Unchanged
    accompaniment.py   Unchanged
    theory.py          Unchanged
    models.py          Unchanged
  application/
    session.py         MAJOR REWORK — clock-driven, windowed, tick-based
  web/
    app.py             Tick loop, lifespan, new endpoints
    static/app.js      Continuous accompaniment loop, note_on/off, WebSocket
```

## Known Gaps And Risks

MIDI hardware input is not implemented yet.
- Current mitigation: `note_on`/`note_off` API matches MIDI semantics, Web keyboard uses pointer down/up.
- Next step: thin MIDI adapter calling `session.note_on`/`session.note_off`.

Audio output is WebAudio synth only.
- Current mitigation: browser-based synth with drums, bass, pad voices.
- Next step: FluidSynth or MIDI output adapter.

Static Pages demo has not been updated for the new frontend.
- The `site/` directory still has the old one-shot accompaniment code.
- Next step: sync `site/` with `src/realtime_accompanist/web/static/` or decide canonical source.

## Suggested Next Tasks

1. **MIDI adapter**: thin adapter using `mido` or `rtmidi` that maps hardware note_on/note_off to `session.note_on`/`session.note_off`.

2. **Sync static Pages demo**: update `site/` to match the new continuous-loop frontend, or set up a build/copy step.

3. **BPM tap tempo**: allow user to tap a button to set BPM from actual rhythm.

4. **Confidence-driven density in real time**: currently density is computed per-snapshot, but could be smoothed over time.

5. **Browser test**: Playwright test for demo → continuous loop → style switch flow.

## Handoff Prompt

```text
You are continuing the realtime_accompanist project.

Read these first:
- docs/progress.md
- docs/goal.md
- docs/architecture.md
- README.md

Current state:
- System was rearchitected: clock-driven, windowed estimation, bar-boundary chord changes, continuous accompaniment loop.
- Tests: 47 passed, 90.55% coverage.
- The key change: estimation now uses windowed data (16-beat for key, 4-beat for chord) instead of full history.

Do not replace the architecture with a large framework.
Keep MIDI/audio as thin adapters around the tested domain logic.
Before changing behavior, add or update tests.
Run:
python -m pytest --cov=realtime_accompanist --cov-report=term-missing --cov-fail-under=85
```

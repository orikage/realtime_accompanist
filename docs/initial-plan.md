# Initial Development Plan

## Direction

Build a small, web-testable MVP before wiring hardware-dependent MIDI or audio. The core product experience is:

> A right-hand melody is entered, key and chord candidates move in realtime, and accompaniment events are generated without musical breakage.

## MVP Scope

- Domain logic for pitch classes, scales, key candidates, chord candidates, chord smoothing, and accompaniment events.
- FastAPI backend with endpoints for note input, demo phrases, style changes, bias changes, chord override, reset, and state inspection.
- Static Web UI that can inject note events without MIDI hardware.
- Automated tests for theory, estimation, smoothing, accompaniment generation, session behavior, and API behavior.

## Non-Goals For This Iteration

- Real MIDI device enumeration.
- FluidSynth or DAW output.
- Deep-learning composition.
- A large multi-agent orchestration layer.

## Quality Gate

- The app starts locally.
- The Web UI can input notes and show estimates.
- All tests pass in `.venv`.
- Hardware-dependent work remains isolated from tested domain logic.

## Design Notes

The implementation uses a light domain/application/web split. It is intentionally not a full DDD model, but the important rules are kept away from FastAPI and browser code so they can be changed safely.


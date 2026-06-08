# Progress And Handoff

Last updated: 2026-06-08 JST

## Current Status

The project has a working MVP for a realtime accompanist demo.

The important product decision is that MIDI hardware and audio output are not required for the current automated verification loop. The core melody input, key estimation, chord estimation, smoothing, and accompaniment-event generation can be exercised from the Web UI and from tests.

## Repository State

- Branch: `main`
- Remote: `https://github.com/orikage/realtime_accompanist.git`
- Latest pushed commit: `20b465d Serve Pages demo from repository root`
- Working tree at handoff: clean

Recent commits:

```text
20b465d Serve Pages demo from repository root
5f2ac34 Enable GitHub Pages deployment from Actions
41ae398 Build realtime accompanist MVP with CI and Pages
```

## Published Demo

GitHub Pages:

```text
https://orikage.github.io/realtime_accompanist/
```

The Pages demo is a static browser-only version. It does not call the FastAPI backend. It exists so the UI and estimation experience can be viewed from GitHub Pages.

Verified on 2026-06-08:

- Public URL returns HTTP 200.
- `Demo C` works in browser.
- It shows `C major`, selected chord `C`, confidence `100%`.
- Generated accompaniment events are displayed.
- Browser console had no errors during the check.
- No horizontal overflow was observed in the checked viewport.

## Local App

Run:

```powershell
.\scripts\run_dev.ps1
```

Open:

```text
http://127.0.0.1:8000
```

The local app is the fuller FastAPI-backed version with:

- Static Web UI
- REST API
- WebSocket state endpoint
- Web note input
- Demo phrase input
- Style changes
- Bias changes
- Manual chord override
- Reset

## CI/CD

Workflow:

```text
.github/workflows/ci-pages.yml
```

Current behavior:

- Runs on pushes to `main`.
- Runs on pull requests.
- Installs the Python package in editable mode with dev dependencies.
- Runs coverage-gated tests:

```powershell
python -m pytest --cov=realtime_accompanist --cov-report=term-missing --cov-fail-under=85
```

- Deploys `site/` to GitHub Pages after tests pass.

Latest checked GitHub Actions runs:

```text
completed success  Serve Pages demo from repository root  CI and Pages
completed success  pages build and deployment              pages-build-deployment
completed success  Enable GitHub Pages deployment from Actions  CI and Pages
```

Note: GitHub emitted a Node.js 20 deprecation annotation for upstream actions. The workflow sets `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true`, so the job succeeds while forcing Node 24 where GitHub supports it.

## Test Status

Latest local quality gate:

```text
31 passed
Total coverage: 91.90%
Coverage gate: 85%
```

Known warning:

```text
StarletteDeprecationWarning from fastapi.testclient importing Starlette TestClient
```

This is dependency-level noise, not a failing behavior in the app.

Current automated coverage includes:

- Music theory primitives
- Melody buffer
- Key estimator
- Chord estimator
- Progression smoother
- Accompaniment event generation
- FastAPI session and API behavior
- Invalid API payload handling
- Static GitHub Pages artifact checks
- Root Pages files matching the `site/` artifact files

## Architecture Snapshot

Important folders:

```text
src/realtime_accompanist/
  domain/        Pure-ish music rules and estimation logic
  application/   AccompanistSession use case/state orchestration
  web/           FastAPI app and backend-served static UI
site/            GitHub Pages static browser demo
docs/            Goal, ZIP-derived requirements, architecture, plans, handoff docs
tests/           Automated regression and quality tests
```

Design intent:

- Keep MIDI and audio hardware adapters outside the core domain logic.
- Keep estimation and accompaniment generation testable without hardware.
- Treat chord inference as candidates with confidence, not as a single guaranteed truth.
- Use light domain/application/web separation rather than heavy DDD.

## Important Files For Next Session

- `docs/goal.md`: original project goal derived from the pasted text.
- `docs/initial-plan.md`: implementation direction chosen for the MVP.
- `README.md`: run, test, Pages, and architecture summary.
- `src/realtime_accompanist/application/session.py`: main app orchestration.
- `src/realtime_accompanist/domain/key_estimator.py`: key estimation.
- `src/realtime_accompanist/domain/chord_estimator.py`: chord estimation.
- `src/realtime_accompanist/domain/progression_smoother.py`: chord selection smoothing.
- `src/realtime_accompanist/domain/accompaniment.py`: accompaniment event generation.
- `src/realtime_accompanist/web/app.py`: FastAPI API and WebSocket.
- `site/app.js`: static Pages demo logic.
- `.github/workflows/ci-pages.yml`: CI and Pages deployment.

## Completed Work

- Saved `/goal` to `docs/goal.md`.
- Copied ZIP-derived planning/spec documents to `docs/`.
- Built Python package with `pyproject.toml`.
- Implemented domain logic for theory, key candidates, chord candidates, smoothing, and accompaniment events.
- Implemented FastAPI-backed Web UI for MIDI-free I/O testing.
- Implemented static GitHub Pages demo.
- Added automated tests and coverage gate.
- Added GitHub Actions CI/CD.
- Enabled and verified GitHub Pages deployment.
- Pushed current work to GitHub.
- Replaced the Web keyboard grid with a piano-style keyboard:
  - 10 white keys from C4 to E5.
  - 7 black keys overlaid between the white keys.
  - Works in both the static GitHub Pages demo and the FastAPI-backed local UI.
  - UI updates before WebAudio arming so note input remains responsive even when browser audio setup is delayed.

## Known Gaps And Risks

MIDI hardware input is not implemented yet.

- Current mitigation: Web note input and demo phrases exercise the same core logic.
- Recommended next step: add a thin MIDI adapter behind an interface and test parsing with synthetic messages.

Audio output is not implemented yet.

- Current mitigation: accompaniment is represented as deterministic events.
- Recommended next step: add a sound/MIDI output adapter and keep unit tests focused on generated event contracts.

Static Pages and FastAPI UI have duplicated frontend logic.

- Current mitigation: tests ensure root Pages files match `site/` files.
- Risk: backend-served UI under `src/realtime_accompanist/web/static/` can drift from Pages UI.
- Recommended next step: either share generated assets or add a simple copy/check script.

Musical correctness is intentionally heuristic.

- Current mitigation: tests cover representative C major, A minor, C/E/G, A/C/E/G, F/A/C, smoothing, low confidence, and empty input behavior.
- Recommended next step: add golden phrase fixtures from actual demo melodies.

## Suggested Next Tasks

1. Add a `midi` adapter module with a small interface:
   - `list_devices()`
   - `open_input(name=None)`
   - `iter_note_events()`
   - Synthetic tests for `note_on`, `note_off`, and velocity-zero note-off.

2. Add an output adapter:
   - Start with MIDI event export/logging before FluidSynth.
   - Keep `AccompanimentEvent` as the tested contract.

3. Add frontend regression checks:
   - Use a browser automation test for `Demo C`, style switch, bias switch, and manual chord override.
   - This can be Playwright-based later if a Node test stack is introduced.

4. Reduce frontend duplication:
   - Decide whether `site/` or `src/realtime_accompanist/web/static/` is canonical.
   - Add a script to sync the other location.

5. Add real demo phrase fixtures:
   - C major clear phrase.
   - A minor/C ambiguous phrase.
   - Phrase designed to show low confidence.
   - Phrase designed to show style differences.

## Handoff Prompt

Use this prompt to continue in a new session:

```text
You are continuing the realtime_accompanist project.

Read these first:
- docs/progress.md
- docs/goal.md
- README.md
- docs/initial-plan.md

Current state:
- GitHub Pages is published at https://orikage.github.io/realtime_accompanist/
- CI/CD is in .github/workflows/ci-pages.yml
- Tests currently pass with 31 tests and 91.90% coverage.
- The MVP intentionally supports Web I/O before real MIDI hardware.

Do not replace the architecture with a large framework.
Keep MIDI/audio as thin adapters around the tested domain logic.
Before changing behavior, add or update tests.
Run:
python -m pytest --cov=realtime_accompanist --cov-report=term-missing --cov-fail-under=85

Recommended next task:
Add a thin MIDI input adapter with synthetic message tests, while preserving the Web I/O demo.
```

from fastapi.testclient import TestClient

from realtime_accompanist.application.session import AccompanistSession
from realtime_accompanist.web.app import create_app


def test_session_updates_state_from_web_note_input():
    session = AccompanistSession()
    for note in [60, 62, 64, 67, 72]:
        session.add_note(note=note, velocity=100, duration=0.4)

    state = session.snapshot()

    assert state["key_candidates"][0]["name"] == "C major"
    assert state["chord_candidates"]
    assert state["selected_chord"] is not None
    assert state["recent_notes"][-1]["name"] == "C"


def test_session_snapshot_includes_clock_fields():
    session = AccompanistSession(bpm=120.0)
    session.add_note(note=60, velocity=100, duration=0.4)

    state = session.snapshot()

    assert "bar" in state
    assert "beat_in_bar" in state
    assert "clock_running" in state
    assert "key_lock" in state
    assert state["clock_running"] is True


def test_session_windowed_estimation():
    session = AccompanistSession(bpm=120.0)
    for note in [69, 72, 76, 79, 76, 72]:
        session.add_note(note=note, velocity=90, duration=0.3)
    for note in [60, 64, 67, 72, 67, 64, 60, 64]:
        session.add_note(note=note, velocity=100, duration=0.5)

    state = session.snapshot()
    assert state["key_candidates"][0]["name"] == "C major"


def test_session_tick_triggers_chord_change():
    session = AccompanistSession(bpm=120.0)
    for note in [60, 64, 67]:
        session.add_note(note=note, velocity=100, duration=0.4)

    state = session.tick()

    assert state["selected_chord"] is not None
    assert state["accompaniment_events"]


def test_session_note_on_and_off():
    session = AccompanistSession()
    session.note_on(60, velocity=100)
    session.note_off(60)

    state = session.snapshot()

    assert len(state["recent_notes"]) == 1
    assert state["recent_notes"][0]["note"] == 60


def test_session_key_lock():
    session = AccompanistSession()
    for note in [60, 64, 67, 72]:
        session.add_note(note=note, velocity=100, duration=0.4)

    state = session.toggle_key_lock()
    assert state["key_lock"] is True

    state = session.toggle_key_lock()
    assert state["key_lock"] is False


def test_api_accepts_note_io_and_returns_estimates():
    client = TestClient(create_app())
    for note in [60, 64, 67]:
        response = client.post("/api/notes", json={"note": note, "velocity": 100, "duration": 0.4})
        assert response.status_code == 200

    state = client.get("/api/state").json()

    assert state["key_candidates"][0]["name"] == "C major"
    assert state["chord_candidates"][0]["symbol"] == "C"
    assert len(state["accompaniment_events"]) > 0
    event = state["accompaniment_events"][0]
    for field in ["part", "note", "beat", "duration_beats", "velocity", "time_seconds"]:
        assert field in event
        assert event[field] is not None


def test_api_note_on_and_off():
    client = TestClient(create_app())

    on_response = client.post("/api/note-on", json={"note": 60, "velocity": 100})
    assert on_response.status_code == 200

    off_response = client.post("/api/note-off", json={"note": 60})
    assert off_response.status_code == 200

    state = off_response.json()
    assert len(state["recent_notes"]) == 1


def test_api_supports_controls_demo_and_reset():
    client = TestClient(create_app())

    assert client.post("/api/controls/style", json={"style": "game_bgm"}).json()["style"] == "game_bgm"
    assert client.post("/api/controls/bias", json={"bias": "minor"}).json()["bias"] == "minor"
    demo_state = client.post("/api/demo/c-major").json()
    assert demo_state["recent_notes"]

    reset_state = client.post("/api/reset").json()
    assert reset_state["recent_notes"] == []
    assert reset_state["selected_chord"] is None
    assert reset_state["accompaniment_events"] == []


def test_api_key_lock_toggle():
    client = TestClient(create_app())
    client.post("/api/demo/c-major")

    state = client.post("/api/controls/key-lock").json()
    assert state["key_lock"] is True

    state = client.post("/api/controls/key-lock").json()
    assert state["key_lock"] is False


def test_api_rejects_invalid_note_payload():
    client = TestClient(create_app())

    response = client.post("/api/notes", json={"note": 200, "velocity": 100, "duration": 0.4})

    assert response.status_code == 422


def test_invalid_style_and_bias_are_ignored_without_corrupting_state():
    client = TestClient(create_app())

    style_state = client.post("/api/controls/style", json={"style": "unknown"}).json()
    bias_state = client.post("/api/controls/bias", json={"bias": "atonal"}).json()

    assert style_state["style"] == "lofi"
    assert bias_state["bias"] == "auto"


def test_manual_chord_override_is_reflected_in_state():
    client = TestClient(create_app())
    client.post("/api/demo/c-major")

    state = client.post("/api/controls/chord", json={"symbol": "Am"}).json()

    assert state["selected_chord"] == "Am"


def test_demo_phrases_produce_meaningful_results():
    session = AccompanistSession()

    state = session.load_demo("c-major")
    assert state["key_candidates"][0]["name"] == "C major"
    assert state["selected_chord"] is not None
    assert state["accompaniment_events"]

    state = session.load_demo("ambiguous")
    assert state["selected_chord"] is not None
    top_keys = [k["name"] for k in state["key_candidates"][:3]]
    assert any("minor" in k for k in top_keys) or any("major" in k for k in top_keys)

    state = session.load_demo("genre-switch")
    assert state["selected_chord"] is not None

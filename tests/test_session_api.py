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


def test_api_accepts_note_io_and_returns_estimates():
    client = TestClient(create_app())
    for note in [60, 64, 67]:
        response = client.post("/api/notes", json={"note": note, "velocity": 100, "duration": 0.4})
        assert response.status_code == 200

    state = client.get("/api/state").json()

    assert state["key_candidates"][0]["name"] == "C major"
    assert state["chord_candidates"][0]["symbol"] == "C"


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

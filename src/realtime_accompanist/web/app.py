from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from realtime_accompanist.application.session import AccompanistSession


class NotePayload(BaseModel):
    note: int = Field(ge=0, le=127)
    velocity: int = Field(default=96, ge=0, le=127)
    duration: float = Field(default=0.35, gt=0, le=8)


class StylePayload(BaseModel):
    style: str


class BiasPayload(BaseModel):
    bias: str


class ChordPayload(BaseModel):
    symbol: str


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, state: dict) -> None:
        for websocket in list(self._connections):
            try:
                await websocket.send_json(state)
            except RuntimeError:
                self.disconnect(websocket)


def create_app(session: AccompanistSession | None = None) -> FastAPI:
    app = FastAPI(title="Realtime Accompanist")
    app.state.session = session or AccompanistSession()
    app.state.manager = ConnectionManager()

    async def publish(state: dict) -> dict:
        await app.state.manager.broadcast(state)
        return state

    @app.get("/api/state")
    def state() -> dict:
        return app.state.session.snapshot()

    @app.post("/api/notes")
    async def add_note(payload: NotePayload) -> dict:
        return await publish(app.state.session.add_note(payload.note, payload.velocity, payload.duration))

    @app.post("/api/controls/style")
    async def set_style(payload: StylePayload) -> dict:
        return await publish(app.state.session.set_style(payload.style))

    @app.post("/api/controls/bias")
    async def set_bias(payload: BiasPayload) -> dict:
        return await publish(app.state.session.set_bias(payload.bias))

    @app.post("/api/controls/chord")
    async def select_chord(payload: ChordPayload) -> dict:
        return await publish(app.state.session.select_chord(payload.symbol))

    @app.post("/api/reset")
    async def reset() -> dict:
        return await publish(app.state.session.reset())

    @app.post("/api/demo/{name}")
    async def demo(name: str) -> dict:
        return await publish(app.state.session.load_demo(name))

    @app.websocket("/ws/state")
    async def websocket_state(websocket: WebSocket) -> None:
        await app.state.manager.connect(websocket)
        await websocket.send_json(app.state.session.snapshot())
        try:
            while True:
                await websocket.receive_text()
                await websocket.send_json(app.state.session.snapshot())
        except WebSocketDisconnect:
            app.state.manager.disconnect(websocket)

    static_dir = Path(__file__).with_name("static")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    return app


app = create_app()


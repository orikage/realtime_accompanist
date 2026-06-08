from __future__ import annotations

from realtime_accompanist.domain.models import AccompanimentEvent, Chord


class AccompanimentEngine:
    CHANNELS = {"drums": 9, "bass": 1, "pad": 2}

    def generate(self, chord: Chord, bpm: float = 90, style: str = "lofi", density: str = "medium") -> list[AccompanimentEvent]:
        safe_bpm = max(float(bpm), 1.0)
        style_key = style if style in {"lofi", "jpop", "game_bgm"} else "lofi"
        density_key = density if density in {"low", "medium", "high"} else "medium"
        events: list[AccompanimentEvent] = []

        drum_beats = {
            "lofi": [(0.0, 36, 62), (1.0, 38, 48), (2.0, 36, 58), (3.0, 38, 46)],
            "jpop": [(0.0, 36, 82), (0.5, 42, 46), (1.0, 38, 76), (2.0, 36, 80), (3.0, 38, 76)],
            "game_bgm": [(0.0, 36, 72), (1.0, 42, 55), (2.0, 38, 70), (3.0, 42, 55)],
        }[style_key]
        for beat, note, velocity in drum_beats:
            events.append(self._event("drums", note, beat, 0.1, velocity, safe_bpm))

        if density_key in {"medium", "high"}:
            for beat, note_pc in [(0.0, chord.root), (2.0, (chord.root + 7) % 12)]:
                events.append(self._event("bass", 36 + note_pc, beat, 0.9, 78 if density_key == "high" else 64, safe_bpm))

        pad_tones = sorted(chord.tones) or [chord.root, (chord.root + 7) % 12]
        if density_key == "low":
            pad_tones = [chord.root, (chord.root + 7) % 12]
        for tone in pad_tones:
            events.append(self._event("pad", 60 + tone, 0.0, 3.8, 66 if density_key == "high" else 52, safe_bpm))

        if density_key == "high":
            for beat, tone in zip((0.5, 1.5, 2.5, 3.5), pad_tones * 2):
                events.append(self._event("pad", 72 + tone, beat, 0.35, 50, safe_bpm))

        return sorted(events, key=lambda event: (event.beat, event.part, event.note))

    def _event(self, part: str, note: int, beat: float, duration: float, velocity: int, bpm: float) -> AccompanimentEvent:
        return AccompanimentEvent(
            part=part,
            note=note,
            beat=beat,
            duration_beats=duration,
            velocity=velocity,
            channel=self.CHANNELS[part],
            time_seconds=beat * 60.0 / bpm,
        )


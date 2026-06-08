# Architecture

## Overall

```text
MIDI Keyboard
  ↓
MIDI Input Layer
  ↓
Melody Buffer
  ↓
Key Estimator
  ↓
Chord Estimator
  ↓
Progression Smoother
  ↓
Accompaniment Engine
  ↓
MIDI Output / FluidSynth / DAW
  ↓
Speaker

Parallel:
State Store → WebSocket → Web UI
```

## Modules

### midi_input

責務:

- MIDIデバイス一覧取得
- MIDI note_on/note_off受信
- velocity取得
- note duration計算
- clockに対するbeat/bar位置付与

出力:

```python
NoteEvent(note=60, velocity=82, start_time=1.23, duration=0.45, beat=2.0)
```

### clock

責務:

- BPM管理
- beat/bar位置計算
- 小節頭/拍頭イベント発火
- 伴奏スケジューリング

MVPでは固定BPMでよい。
将来的にはtap tempoやMIDI clockに対応。

### melody_buffer

責務:

- 直近ノート履歴保持
- 2小節/4小節窓の取得
- 強拍、長音、終端音などの特徴量計算

### key_estimator

責務:

- 12キー major/minorの候補スコア計算
- 確信度算出

### chord_estimator

責務:

- 現在キーに基づく候補コード生成
- メロディとの一致度計算
- 直前コードとの遷移スコア計算
- 候補ランキング出力

### progression_smoother

責務:

- コードが頻繁に変わりすぎないよう補正
- 小節単位/拍単位でコードを確定
- ベースラインの跳躍を抑える
- 確信度が低い場合は曖昧コード/sus/no3/5度中心にする

### accompaniment_engine

責務:

- スタイル別伴奏パターン読込
- ドラム/ベース/コード/アルペジオ生成
- 確信度に応じた密度制御
- MIDI出力イベント生成

### sound_engine

責務:

- FluidSynthや外部MIDIポートへの出力
- channel割当
- program change
- note_on/note_off送信

### ui_server

責務:

- 現在状態をWebSocketで配信
- UIからの操作を受け取る
  - style change
  - key lock
  - chord select
  - major/minor bias
  - start/stop

## State Model

```python
@dataclass
class SystemState:
    bpm: float
    bar: int
    beat: float
    style: str
    key_candidates: list[KeyCandidate]
    chord_candidates: list[ChordCandidate]
    selected_key: str | None
    selected_chord: str | None
    confidence: float
    density: float
    mode: str
```

## Processing Loop

1. MIDI event received
2. Update note state and melody buffer
3. Recompute key candidates
4. Recompute chord candidates
5. Update UI state immediately
6. On next beat/bar boundary:
   - choose chord via smoother
   - schedule accompaniment pattern
   - send MIDI to sound engine

## Quantization Policy

- UI: immediate update
- Pad chord: bar boundary preferred
- Bass: beat or bar boundary
- Drums: continuous loop
- Fill: bar end

## Suggested Folder Structure

```text
realtime_accompanist/
  pyproject.toml
  README.md
  app/
    main.py
    midi_input.py
    clock.py
    melody_buffer.py
    theory.py
    key_estimator.py
    chord_estimator.py
    progression_smoother.py
    accompaniment.py
    sound_engine.py
    ui_server.py
    models.py
  patterns/
    jpop.json
    lofi.json
    game_bgm.json
  web/
    index.html
    src/
      App.tsx
  tests/
    test_key_estimator.py
    test_chord_estimator.py
```

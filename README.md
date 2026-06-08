# Realtime Accompanist

MIDIキーボードで右手メロディを弾いたときに、直近フレーズからキー・コード候補を推定し、伴奏イベントを生成する展示向けMVPです。

現時点ではMIDI実機に依存する部分を急がず、Web画面からノート入力を行えるようにしています。これにより、推定ロジック、スムージング、伴奏生成、APIを自動テストで確認できます。

## Run

```powershell
.\scripts\run_dev.ps1
```

Open:

```text
http://127.0.0.1:8000
```

## GitHub Pages

Static browser demo:

```text
https://orikage.github.io/realtime_accompanist/
```

The Pages version runs without the FastAPI backend, so it is useful for showing the estimation UI and accompaniment-event generation on GitHub Pages. The local FastAPI app remains the fuller Web/API version for MIDI adapter work.

## Test

```powershell
.\.venv\Scripts\python -m pytest --cov=realtime_accompanist --cov-report=term-missing --cov-fail-under=85
```

GitHub Actions runs the same coverage-gated test command before deploying Pages.

## What Works

- Web UIからノート入力
- デモフレーズ入力
- キー候補推定
- コード候補推定
- 手動コード選択
- Major / Minor / Auto バイアス
- Lo-fi / J-POP / Game BGM スタイル切替
- 伴奏イベント生成
- Web APIとWebSocketの状態配信

## Architecture

```text
src/realtime_accompanist/
  domain/        # 音楽理論、推定、スムージング、伴奏イベント生成
  application/   # セッション状態とユースケース
  web/           # FastAPI と静的Web UI
tests/           # MIDI実機なしで回せる自動テスト
docs/            # 添付ZIPと/goal由来の資料
```

MIDIや音源出力は今後の外部I/Oアダプタとして追加する想定です。中心ロジックは外部I/Oから分離してあるため、実機テストが難しい部分をWeb入力で代替できます。

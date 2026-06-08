# Realtime Accompanist

MIDIキーボードで右手メロディを弾くと、直近フレーズからキー・コード候補を推定し、ドラム・ベース・コード伴奏をリアルタイム生成する展示向けAI伴奏楽器です。

## How It Works

1. メロディを弾く（Web鍵盤 or MIDI）
2. 直近4小節のノートからキー候補を推定
3. 直近1小節のノートからコード候補を推定
4. 小節頭でコードを確定し、伴奏パターンを生成
5. ブラウザで伴奏を連続ループ再生

推定は確定ではなく候補と確信度として扱い、確信度に応じて伴奏の密度が変わります。

## Run

```powershell
.\scripts\run_dev.ps1
```

Open:

```text
http://127.0.0.1:8000
```

## Test

```powershell
python -m pytest --cov=realtime_accompanist --cov-report=term-missing --cov-fail-under=85
```

47 tests, 90%+ coverage. GitHub Actions runs the same coverage-gated test command.

## What Works

- Web鍵盤によるメロディ入力（note_on/note_off対応）
- デモフレーズ入力（C major / Ambiguous / Genre Switch）
- ウィンドウベースのキー候補推定（直近16ビート）
- ウィンドウベースのコード候補推定（直近4ビート）
- 小節頭でのコード切替（ProgressionSmoother）
- 手動コード選択
- Key Lock（キー固定）
- Major / Minor / Auto バイアス
- Lo-fi / J-POP / Game BGM スタイル切替
- 確信度に応じた伴奏密度変更
- 連続伴奏ループ再生（WebAudio）
- WebSocket による状態リアルタイム配信
- 音楽クロック（BPM・拍・小節管理）

## Architecture

```text
src/realtime_accompanist/
  domain/
    clock.py             音楽クロック（BPM・拍・小節）
    melody_buffer.py     ノート履歴バッファ（ウィンドウクエリ）
    key_estimator.py     キー推定（直近16ビート）
    chord_estimator.py   コード推定（直近4ビート）
    progression_smoother.py  コード遷移スムージング
    accompaniment.py     伴奏パターン生成
    theory.py            音楽理論ユーティリティ
    models.py            ドメインモデル
  application/
    session.py           セッション管理（クロック駆動ティック）
  web/
    app.py               FastAPI（REST + WebSocket + ティックループ）
    static/              Web UI
tests/                   自動テスト（47テスト、90%+カバレッジ）
docs/                    要件・アーキテクチャ・進捗
```

MIDIや音源出力は今後の外部I/Oアダプタとして追加する想定です。コアロジックは外部I/Oから分離してあるため、Web入力で代替テスト可能です。

# MVP Plan

## v0.1: 推定表示版

Goal: MIDI入力からキー候補・コード候補をリアルタイム表示する。

Scope:

- MIDI input
- melody buffer
- key estimation
- chord candidate estimation
- CLI or Web UI display

No sound required at this stage.

Acceptance Criteria:

- MIDIキーボードで弾いたノートが認識される
- 直近ノート履歴が表示される
- C-D-E-Gなどを弾くとC majorが上位に出る
- A-C-E-Gなどを弾くとAm/C候補が出る
- 候補とスコアが更新され続ける

## v0.2: パッド伴奏版

Goal: 1小節ごとにコードを選び、パッド音を鳴らす。

Scope:

- fixed BPM
- bar boundary detection
- selected chord
- pad chord output via FluidSynth or MIDI out

Acceptance Criteria:

- 推定コードが小節頭で反映される
- コードが毎拍暴れない
- 確信度が低い時は薄い音になる、またはコードを保留する

## v0.3: ベース・ドラム追加版

Goal: 伴奏らしくする。

Scope:

- drum loop
- bass root/fifth pattern
- chord pad
- style: Lo-fi only

Acceptance Criteria:

- メロディに合わせてベースとパッドが変わる
- ドラムは固定ループで安定
- 伴奏が破綻しない

## v0.4: 展示UI版

Goal: Maker Faireで見せられるUIを作る。

Scope:

- Web UI
- Key display
- Chord candidates
- Confidence meter
- Current style
- Density meter
- Chord selection buttons
- Major/Minor toggle

Acceptance Criteria:

- 観客が画面を見て現在の推定状態を理解できる
- 候補コードをタップすると次小節から反映される
- Major/Minor選択で伴奏方向が変わる

## v0.5: ジャンル切替版

Goal: 同じメロディで伴奏の雰囲気を変えられる。

Scope:

- J-POP
- Lo-fi
- Game BGM

Acceptance Criteria:

- UIからジャンルを切り替えられる
- ドラム/ベース/コードパターンが変わる
- 推定エンジンは共通

## v1.0: 展示可能版

Minimum Demo Set:

- Demo 1: メロディから伴奏立ち上がり
- Demo 2: ジャンル切替
- Demo 3: AIが迷うUI
- Demo 4: 観客がコード候補を選ぶ

Hardware:

- MIDI keyboard
- N100 mini PC or laptop
- audio interface optional
- small speaker
- monitor/tablet

Reliability Features:

- Key Lock
- Style Lock
- Manual Chord Assist
- Panic button: all notes off
- Reset button

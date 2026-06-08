# Requirements

## Product Concept

右手でメロディを弾くだけで、システムがキー・コード候補を推定し、リアルタイムに伴奏してくれる展示型AI楽器。

## Must Requirements

### R1. MIDIキーボード入力

初期MVPではマイク入力や鼻歌入力は扱わない。
MIDI入力のみを対象にする。

取得する情報:

- note number
- note on/off
- velocity
- start time
- duration
- timing within beat/bar

理由:

- 音高検出が不要
- ノイズに強い
- 展示会場でも安定する
- レイテンシを下げやすい

### R2. 直近フレーズからキー推定

直近2〜4小節程度のノート履歴からキー候補を推定する。

表示例:

```text
C major: 68%
A minor: 55%
G major: 43%
F major: 39%
```

重み付け要素:

- スケール内音への一致
- 長く鳴った音
- 強拍の音
- フレーズ終端の音
- 何度も出た音
- 直近に出た音

### R3. コード候補推定

直近1小節、または現在拍周辺からコード候補を複数出す。

表示例:

```text
Current chord candidates:
Am 62%
C  58%
F  41%
Dm 33%
```

スコアリング要素:

- メロディ音がコードトーンに含まれるか
- 現在キー内のダイアトニックコードか
- 直前コードから自然に進行するか
- ベースラインが跳びすぎないか
- 同じコードが続きすぎていないか
- 小節頭/フレーズ終端に合うか

### R4. 自動伴奏生成

MVPでは生成AIではなく、伴奏パターン駆動で実装する。

出力パート:

- drums
- bass
- chord instrument: piano, electric piano, pad
- optional arpeggio

推奨音源:

- FluidSynth + SoundFont
- またはDAW/MIDI out
- WebAudioも可

### R5. 低遅延

目標:

- 鍵盤入力からUI反映: ほぼ即時
- 鍵盤入力から伴奏の反応: 100ms以内を目標
- コード切替: 拍頭または小節頭に量子化

注意:

推定値はリアルタイム更新してよいが、伴奏のコード変更は拍頭/小節頭に限定する方が自然。

### R6. 推定過程を見せるUI

最低限表示する情報:

- current key candidates
- current chord candidates
- confidence
- selected style
- next likely chords
- accompaniment density

UI例:

```text
Key: C major 72%

Now:
Am 61%
C  55%
F  32%

Next likely:
F / Dm / G

Style:
Lo-fi Pop

Confidence:
██████░░░░
```

## Optional Requirements

### O1. ジャンル切替

同じメロディに対して伴奏スタイルを切り替える。

初期候補:

- J-POP
- Lo-fi
- Game BGM

将来候補:

- City Pop
- Jazz
- EDM
- Rock

### O2. AIの迷いを音に反映する

確信度が低いとき:

- ドラムだけ
- パッド薄め
- ベース弱めまたは無し
- sus/5度中心の曖昧な和音

確信度が高いとき:

- ベース追加
- 明確なコード伴奏
- アルペジオ追加
- フィルイン追加

### O3. 観客が候補コードを選べる

UI上に候補を表示し、タップ/クリックで選択できる。

例:

```text
[Am] [C] [F] [Dm]
```

選択されたコードは次の小節または拍頭で反映する。

### O4. Major/Minor方向付け

観客が以下を選べる。

```text
[Major] [Minor]
```

同じメロディでも明るい/暗い解釈に寄せられる。

### O5. ループ録音

1〜4小節のメロディまたは伴奏をループ化し、その上に演奏できる。

### O6. Ableton Link / MIDI Clock対応

他機材やDAWとの同期用。
初期MVPでは後回し。

## Explicit Non-Goals

### N1. 音声入力はやらない

初期MVPでは鼻歌・マイク入力は対象外。
理由:

- 展示会場がうるさい
- ピッチ検出が不安定
- 和音分離が難しい
- レイテンシが増える

### N2. 完全なAI作曲は狙わない

深層学習やTransformerでの完全生成は初期MVP対象外。
ルールベース推定 + コード進行補正 + 伴奏パターンで始める。

### N3. 正しいコードの完全推定を売りにしない

売り文句:

OK: メロディからキー・コード候補を推定し、確信度に応じてリアルタイム伴奏します。
NG: メロディだけから正しいコードを完全推定します。

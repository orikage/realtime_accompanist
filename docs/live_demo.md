# Live Demo Plan

## Demo Title

右手だけでバンドがついてくるAI伴奏楽器

## 展示卓構成

```text
MIDIキーボード
N100ミニPC or laptop
小型スピーカー
モニター or タブレット
Web UI
```

## Demo 1: 何も知らない状態から伴奏が立ち上がる

### 説明

「いまから右手だけで適当にメロディを弾きます。コードは押さえません。システムが勝手にキーとコード候補を推定して、伴奏を足します。」

### 演奏例

```text
C - D - E - G | E - D - C
```

### 期待挙動

0〜2秒:

```text
Key: Unknown
Chord: Unknown
Output: click + light drums
```

3〜5秒:

```text
Key: C major 58%
Chord: C 46% / Am 31%
Output: pad appears
```

6〜10秒:

```text
Key: C major 76%
Chord: C -> G -> Am -> F
Output: bass + drums + piano
```

### 見せ場

最初はスカスカだった音が、弾いているうちにバンドっぽく立ち上がる。

## Demo 2: 同じメロディでジャンル切替

同じフレーズを弾きながらジャンルを切り替える。

### J-POP

```text
Drums: 8-beat
Bass: root + fifth
Chord: piano comping
```

### Lo-fi

```text
Drums: laid-back
Bass: soft sub
Chord: electric piano
```

### Game BGM

```text
Drums: light
Bass: octave pattern
Chord: arpeggio
```

### 見せ場

同じメロディなのに、伴奏の解釈が変わる。

## Demo 3: AIが迷う

わざと曖昧なフレーズを弾く。

```text
A - C - E - G
```

これは Am7 にも C6 にも見える。

### UI表示例

```text
Key: C major 52% / A minor 49%

Chord candidates:
Am 64%
C  61%
F  29%
```

### 期待挙動

最初はAmともCとも取れる薄いパッド。
その後、F - E - D - C のように弾くとC major側に寄る。

```text
Key: C major 74%
Chord: C -> F -> G
```

### 見せ場

間違えたのではなく、曖昧さを保持しているように見える。

## Demo 4: 観客参加

観客に一つだけ選ばせる。

```text
このメロディ、明るくしますか？ 暗くしますか？
[Major] [Minor]
```

または:

```text
次のコード候補:
[F] [Dm] [G] [Am]
```

観客が選ぶと伴奏がそちらに寄る。

## Demo 5: 失敗時の逃げ道

もし推定が暴れたら、以下の展示モードに切り替える。

- Key Lock: C major / A minor固定
- Style Lock: Lo-fi固定
- Chord Assist: 候補コードを手動選択
- Density Auto: 確信度が低いと伴奏を薄くする

これによりデモ失敗を体験に変換できる。

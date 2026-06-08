# UI Spec

## Goal

展示で「AIがいまどう解釈しているか」を見せる。
音だけでは伝わりづらいため、推定状態を大きく表示する。

## Main Screen

```text
┌────────────────────────────────────┐
│ Realtime Melody Accompanist         │
├────────────────────────────────────┤
│ Key: C major 72%                    │
│      A minor 51%                    │
│                                    │
│ Current Chord Candidates            │
│ [Am 61%] [C 55%] [F 32%] [Dm 25%]  │
│                                    │
│ Selected: Am                        │
│ Next likely: F / Dm / G             │
│                                    │
│ Style: Lo-fi      BPM: 82           │
│ Confidence: ██████░░░░              │
│ Density: Medium                     │
│                                    │
│ [J-POP] [Lo-fi] [Game BGM]          │
│ [Major] [Minor] [Auto]              │
│ [Key Lock] [Chord Assist] [Reset]   │
└────────────────────────────────────┘
```

## Required Controls

### Style Buttons

- J-POP
- Lo-fi
- Game BGM

### Bias Buttons

- Auto
- Major
- Minor

### Chord Candidate Buttons

Current chord candidates are clickable.
When clicked, the selected chord is applied at the next bar boundary.

### Safety Buttons

- Reset estimates
- Panic: all notes off
- Key lock
- Disable accompaniment

## Visual Behavior

- Top key candidate should be large
- Confidence meter should be obvious
- Chord candidates should reorder dynamically
- Manual selection should be highlighted
- Low confidence should use a visual state like “Listening...” or “Still unsure”

## Demo Mode UI

Provide demo buttons:

- Demo: C major phrase
- Demo: Ambiguous Am/C
- Demo: Genre switch

This allows showing the system without MIDI hardware.

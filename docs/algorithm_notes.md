# Algorithm Notes

## Pitch Class

MIDI note to pitch class:

```python
pc = note % 12
```

Pitch class names:

```text
0 C
1 C#/Db
2 D
3 D#/Eb
4 E
5 F
6 F#/Gb
7 G
8 G#/Ab
9 A
10 A#/Bb
11 B
```

## Scale Definitions

Major scale intervals:

```python
[0, 2, 4, 5, 7, 9, 11]
```

Natural minor scale intervals:

```python
[0, 2, 3, 5, 7, 8, 10]
```

## Key Scoring Draft

For each candidate key:

```text
score = 0
for note in recent_notes:
    pc = note.note % 12
    weight = 1.0
    weight += duration_bonus
    weight += velocity_bonus
    weight += strong_beat_bonus
    weight += recency_bonus

    if pc in scale:
        score += 1.0 * weight
    else:
        score -= 0.7 * weight

    if pc == tonic:
        score += 0.5 * weight
    if pc == dominant:
        score += 0.25 * weight
```

Then normalize scores with softmax-like mapping or min-max.

## Chord Candidate Generation

For a major key:

```text
I: major
II: minor
iii: minor
IV: major
V: major
vi: minor
vii°: diminished
```

For a natural minor key:

```text
i: minor
ii°: diminished
III: major
iv: minor
v: minor
VI: major
VII: major
```

## Chord Scoring Draft

```text
score = 0
for note in recent_notes:
    pc = note.note % 12
    weight = note_weight(note)

    if pc in chord.tones:
        score += 1.0 * weight
    elif pc in key.scale:
        score += 0.1 * weight
    else:
        score -= 0.4 * weight

if chord is diatonic:
    score += 1.0

score += transition_score(previous_chord, chord)
score -= bass_jump_penalty(previous_chord.root, chord.root)
```

## Transition Preferences

Simple common transitions:

```text
I -> V, vi, IV, ii
ii -> V, IV
iii -> vi, IV
IV -> I, V, ii
V -> I, vi
vi -> IV, ii, V
vii° -> I
```

For minor:

```text
i -> VI, iv, v, VII
iv -> v, VII, i
v -> i, VI
VI -> VII, iv
aVII -> i, III
```

MVPではざっくりでよい。

## Confidence to Density

```python
if confidence < 0.35:
    density = "low"
elif confidence < 0.65:
    density = "medium"
else:
    density = "high"
```

Low density behavior:

- drums only or light drums
- pad uses root+fifth or sus
- no bass or very sparse bass

Medium:

- bass root/fifth
- sparse chords

High:

- full triads/sevenths
- stronger bass
- optional arp/fill

## Smoothing

Use hysteresis:

```text
switch chord only if new_score > current_score + threshold
```

Use hold time:

```text
minimum chord duration = 1 bar or 2 beats
```

Use manual override:

```text
manual selected chord wins for next bar
```

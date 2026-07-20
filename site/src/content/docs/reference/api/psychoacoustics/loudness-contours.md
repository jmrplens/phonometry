---
title: "psychoacoustics.loudness_contours"
description: "Public API of phonometry.psychoacoustics.loudness_contours (auto-generated)."
sidebar:
  label: "loudness_contours"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Normal equal-loudness-level contours per ISO 226:2023.

Implements Formula (1) (clause 4.1: SPL of a pure tone from its loudness
level) and Formula (2) (clause 4.2: the inverse) with the Table 1 (p. 4)
parameters at the 29 preferred third-octave frequencies of ISO 266.

## equal_loudness_contour

```python
equal_loudness_contour(phon: float) -> Tuple[np.ndarray, np.ndarray]
```

Normal equal-loudness-level contour (ISO 226:2023 Formula 1).

Returns the sound pressure levels of pure tones judged equally loud as
a 1 kHz tone at `phon` dB SPL, at the 29 preferred third-octave
frequencies of Table 1.

Validity (clause 4.1): 20 phon to 90 phon between 20 Hz and 4 kHz, and
up to 80 phon between 5 kHz and 12.5 kHz; above 80 phon the returned
contour therefore stops at 4 kHz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `phon` | Loudness level in phons (20 to 90). |

**Returns:** Tuple `(frequencies, spl)` in Hz and dB re 20 uPa.

## hearing_threshold

```python
hearing_threshold() -> Tuple[np.ndarray, np.ndarray]
```

Threshold of hearing T_f (ISO 226:2023 Table 1).

**Returns:** Tuple `(frequencies, threshold)` in Hz and dB re 20 uPa.

## loudness_level

```python
loudness_level(spl: float, frequency: float) -> float
```

Loudness level of a pure tone (ISO 226:2023 Formula 2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `spl` | Sound pressure level of the tone in dB re 20 uPa. |
| `frequency` | Tone frequency in Hz; must be one of the 29 preferred third-octave frequencies of Table 1 (the standard specifies no interpolation between them). |

**Returns:** Loudness level in phons. Values outside 20-90 phon (80 above 4 kHz) are extrapolations the standard labels as informative only.

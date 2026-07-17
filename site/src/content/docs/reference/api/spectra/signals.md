---
title: "metrology.signals"
description: "Public API of phonometry.metrology.signals (auto-generated)."
sidebar:
  label: "signals"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Deterministic colored-noise test signals.

Gaussian noise with an exact power-law spectral slope, for exercising and
validating spectral estimators: white (0 dB/octave), pink (-3.01), red
(-6.02, also called Brownian), blue (+3.01) and violet (+6.02). The
autospectral density follows `Gxx(f) ∝ f^α` with `α` = 0, -1, -2, +1
and +2 respectively, so the level changes by exactly `3.01·α` dB per
octave (`10·lg 2 = 3.0103` dB).

The colors are synthesized by filtering seeded white Gaussian noise in the
frequency domain: the DFT of the white record is multiplied by the exact
magnitude response `|H(f)| = (f/f_ref)^(α/2)` bin by bin (a zero-phase
FIR filter applied circularly), so the *expected* spectrum follows the
power law exactly at every synthesis bin above DC and a measured slope
deviates only by the random error of the spectral estimate (thousandths of
a dB per octave over a three-decade regression) - not the piecewise or
few-pole approximations whose pink slope ripples by fractions of a dB. The
DC bin is zeroed for the colored variants (a power law has no finite DC
value) and the record is rescaled to the requested RMS exactly.

With the same `seed` the generator is fully deterministic across runs.

## noise_signal

```python
noise_signal(
    fs: float,
    seconds: float = 1.0,
    *,
    color: Literal['white', 'pink', 'red', 'blue', 'violet'] = 'white',
    rms: float = 1.0,
    seed: int | None = None,
) -> NDArray[np.float64]
```

Generate Gaussian noise with an exact power-law spectral slope.

`Gxx(f) ∝ f^α` with α = 0 (white), -1 (pink, -3.01 dB/octave),
-2 (red/Brownian, -6.02), +1 (blue, +3.01) or +2 (violet, +6.02),
shaped by an exact frequency-domain filter (see the module docstring),
zero-mean and rescaled to the requested RMS exactly.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate, in Hz. |
| `seconds` | Duration, in seconds (at least 16 samples). |
| `color` | Noise color: `'white'`, `'pink'`, `'red'`, `'blue'` or `'violet'`. |
| `rms` | Root-mean-square value of the returned record. |
| `seed` | Seed for `numpy.random.default_rng`; the same seed reproduces the same record. `None` draws fresh entropy. |

**Returns:** The noise record, `round(fs·seconds)` samples.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs or parameters are invalid. |

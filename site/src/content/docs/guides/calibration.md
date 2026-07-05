---
title: "Calibration and dBFS"
description: "Physical SPL calibration and digital full-scale analysis."
---

PyOctaveBand can return results in physical **Sound Pressure Level (dB SPL)** or
digital **decibels relative to Full Scale (dBFS)**.

## Physical Calibration (Sound Level Meter)

To get accurate SPL measurements from a digital recording, you must first
calculate the sensitivity of your measurement chain using a reference tone
(e.g., 94 dB @ 1 kHz).

```python
from pyoctaveband import octavefilter, calculate_sensitivity

# 1. Record your 94dB calibrator signal
# ref_signal = ... (your recording)

# 2. Calculate sensitivity factor
sensitivity = calculate_sensitivity(ref_signal, target_spl=94.0)

# 3. Apply calibration to your measurements
spl, freq = octavefilter(signal, fs, calibration_factor=sensitivity)
# Now 'spl' values are in real-world dB SPL!
```

The same `calibration_factor` works across the whole library: `octavefilter`,
`OctaveFilterBank`, `leq`, `laeq` and `ln_levels`.

## Digital Analysis (dBFS)

If you are working with digital audio files (e.g., WAV, FLAC) and want to
analyze levels relative to Full Scale rather than physical pressure, you can use
the `dbfs=True` parameter.

In this mode:

* **0 dBFS** corresponds to a numeric signal level of 1.0 (RMS or Peak).
* `calibration_factor` does not apply (dBFS is relative to digital full scale).
* Useful for analyzing headroom, digital mastering, or normalized signals.

```python
# Assume 'signal' is normalized between -1.0 and 1.0
spl_dbfs, freq = octavefilter(signal, fs, dbfs=True)
# Results will be negative (e.g., -20 dBFS)
```

## RMS vs Peak Levels

PyOctaveBand supports two measurement modes to align with professional software
like BK:

- **RMS (`mode='rms'`)**: Energy-based level (standard).
- **Peak (`mode='peak'`)**: Absolute maximum value reached in the frame
  (Peak-holding).

```python
# Measure peak-holding levels for impact analysis
spl_peak, freq = octavefilter(signal, fs, mode='peak')
```

:::note
`mode='peak'` measures the absolute maximum of the **filtered** band signal,
which includes the filter's onset transient (overshoot). Signals that start
abruptly may read up to ~1 dB high. This is inherent to IIR band filters
(an analog SLM behaves the same way), not a processing artifact.
:::

## Integer audio input

Integer signals (e.g. int16 from `scipy.io.wavfile.read`) are converted to
float64 internally before any squaring, so calibration and level results are
identical whether you pass the raw integer array or a float conversion.

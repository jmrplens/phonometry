---
title: "Frequency Weighting (A, C, G, Z)"
description: "A/C/Z frequency weighting per IEC 61672-1 (class 1, with a high-frequency accuracy mode) and G-weighting for infrasound per ISO 7196."
---

Frequency weighting curves simulate the human ear's sensitivity. A, C and Z
are specified by **IEC 61672-1:2013**; the infrasound G curve is specified by
**ISO 7196:1995**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses.svg" alt="A, C and Z frequency weighting curves with a zoom showing the positive region of the A curve (+1.27 dB at 2.5 kHz)" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses_dark.svg" alt="A, C and Z frequency weighting curves with a zoom showing the positive region of the A curve (+1.27 dB at 2.5 kHz)" style="width:80%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import weighting_filter

# Measure each curve's response: weight a centered unit impulse and take
# its spectrum (1 s buffer -> 1 Hz frequency resolution).
fs = 48000
impulse = np.zeros(fs)
impulse[fs // 2] = 1.0
freqs = np.fft.rfftfreq(fs, 1 / fs)

fig, ax = plt.subplots(figsize=(9, 5))
for curve in ("A", "C", "Z"):
    spectrum = np.fft.rfft(weighting_filter(impulse, fs, curve=curve))
    ax.semilogx(freqs[1:], 20 * np.log10(np.abs(spectrum[1:]) + np.finfo(float).eps),
                label=curve)
ax.set(xlim=(10, 20000), ylim=(-80, 10),
       xlabel="Frequency [Hz]", ylabel="Response [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

* **A-Weighting (`A`):** Standard for environmental noise (IEC 61672-1).
* **C-Weighting (`C`):** Used for peak sound pressure and high-level noise.
* **Z-Weighting (`Z`):** Zero weighting, completely flat response.
* **G-Weighting (`G`):** Infrasound weighting per ISO 7196 (see below).

## 1. Where the curves come from

The A and C curves are inverted equal-loudness contours, frozen into filters:
**A** approximates the inverse of the historic 40-phon contour (quiet levels,
where the ear discards bass most aggressively) and **C** the flatter ~100-phon
one (loud levels). IEC 61672-1:2013 (Annex E) defines both analytically from
four corner frequencies:

$$
f_1 = 20.599\ \text{Hz}, \quad f_2 = 107.653\ \text{Hz}, \quad
f_3 = 737.862\ \text{Hz}, \quad f_4 = 12194.217\ \text{Hz}
$$

C is a band-pass with double poles at $f_1$ and $f_4$ (2 zeros at the origin);
A adds the $f_2$ and $f_3$ poles (4 zeros), which is why it keeps falling
through the low-mids. Both are normalized to exactly 0 dB at 1 kHz. Z is the
absence of weighting. The full pole/zero derivation is in the
[Theory](/phonometry/reference/theory/) page.

## 2. Basic usage

```python
import numpy as np
from phonometry import weighting_filter

# recording: a calibrated microphone capture (Pa) — recorded through your measurement chain. Synthesized here so the guide runs standalone.
fs = 48000
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# Apply A-weighting to the raw recording
weighted_signal = weighting_filter(recording, fs, curve='A')

# Apply C-weighting for peak analysis
c_weighted_signal = weighting_filter(recording, fs, curve='C')
```

## 3. Infrasound: G-weighting (ISO 7196)

The **G frequency weighting** (ISO 7196:1995) rates infrasound the way A-weighting
rates audible noise. It is defined by a pole-zero configuration with 0 dB gain at
10 Hz, rises at 12 dB/octave from 1 Hz to 20 Hz (matching the steep growth of
perception in that band) and falls off at 24 dB/octave outside it. Use it for
sources with significant energy below 20 Hz (wind turbines, HVAC, blasting):

```python
from phonometry import weighting_filter

# Uses `recording` and `fs` from the snippet above.
g_weighted = weighting_filter(recording, fs, curve='G')
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/g_weighting_response.svg" alt="G-weighting frequency response from 0.1 Hz to 1 kHz with the ISO 7196 Table 2 nominal values overlaid" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/g_weighting_response_dark.svg" alt="G-weighting frequency response from 0.1 Hz to 1 kHz with the ISO 7196 Table 2 nominal values overlaid" style="width:80%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import weighting_filter

# Measure the G response: weight a centered unit impulse and take its
# spectrum. A long buffer gives the resolution the infrasound range
# needs (20 s -> 0.05 Hz).
fs = 4000
impulse = np.zeros(20 * fs)
impulse[impulse.size // 2] = 1.0
freqs = np.fft.rfftfreq(impulse.size, 1 / fs)
spectrum = np.fft.rfft(weighting_filter(impulse, fs, curve="G"))

fig, ax = plt.subplots(figsize=(9, 5))
ax.semilogx(freqs[1:],
            20 * np.log10(np.abs(spectrum[1:]) + np.finfo(float).eps))
ax.plot(10, 0, "o", color="tab:red", label="0 dB at 10 Hz")
ax.set(xlim=(0.1, 1000), ylim=(-90, 15),
       xlabel="Frequency [Hz]", ylabel="G-weighting response [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

The implementation follows the ISO 7196 Table 1 pole/zero values exactly and is
verified in CI against every Table 2 nominal response value (0.25 Hz to 315 Hz).
`WeightingFilter(fs, "G")` supports the same multichannel and stateful block
processing as A/C. Levels measured with the G curve are reported as
L<sub>pG</sub> (or L<sub>Geq</sub> for the equivalent level over time).

## 4. `weighting_filter()` / `WeightingFilter` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D or 2D array | any | non-empty | 2D is `[channels, samples]` |
| `fs` | int | Hz | > 0 | |
| `curve` | str | — | `'A'` (default), `'C'`, `'G'`, `'Z'` | `'G'` per ISO 7196 (infrasound); `'Z'` is a bypass |
| `high_accuracy` | bool | — | default `True` (function); class default `None` resolves to `not stateful` | Internal oversampling (up to 8×, reaching ≥ 144 kHz at common audio rates, e.g. 96 kHz input ×2) keeps A/C in class 1 up to 16 kHz; silently ignored for G, whose 0.25–315 Hz range the plain design already renders exactly |
| `stateful` | bool (class only) | — | default `False` | Carries filter state across blocks (streaming) |
| `steady_ic` | bool (class only) | — | default `False` | Steady-state initial conditions (no onset transient) |

## 5. Reusable filter object

If you weight many signals with the same parameters, design the filter once:

```python
from phonometry import WeightingFilter

# Uses `recording` and `fs` from the snippet above.
wf = WeightingFilter(fs, "A")
signals = [recording]                # your batch of recordings
for recording in signals:
    weighted = wf.filter(recording)
```

## 6. High-frequency accuracy (`high_accuracy`)

A plain bilinear-transform design compresses the response near Nyquist: at
fs = 48 kHz the A-curve error at 12.5 kHz reaches −2.7 dB, outside the IEC
61672-1 **class 1** tolerance (+2.0/−2.5 dB).

By default (`high_accuracy=True`), phonometry designs and runs the weighting
filter at an internally oversampled rate (≥ 144 kHz) and decimates back, keeping
the response within class 1 tolerances up to 16 kHz (error ≈ −0.5 dB at
12.5 kHz for fs = 48 kHz).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf.svg" alt="A-weighting high-frequency accuracy at 48 kHz: analytic curve versus plain bilinear versus oversampled design, with error subplot" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf_dark.svg" alt="A-weighting high-frequency accuracy at 48 kHz: analytic curve versus plain bilinear versus oversampled design, with error subplot" style="width:80%">

*The plain bilinear design (red) crosses the class 1 tolerance near 12.5 kHz;
the oversampled design (blue) stays close to the analytic curve.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import weighting_filter

# Measured response of both designs at fs = 48 kHz: weight a centered
# unit impulse and take its spectrum...
fs = 48000
impulse = np.zeros(fs)
impulse[fs // 2] = 1.0
freqs = np.fft.rfftfreq(fs, 1 / fs)[1:]

# ...versus the analytic IEC 61672-1 A-curve built from the four corner
# frequencies of section 1, normalized to 0 dB at 1 kHz.
f1, f2, f3, f4 = 20.599, 107.653, 737.862, 12194.217
gain = (f4**2 * freqs**4) / ((freqs**2 + f1**2)
        * np.sqrt((freqs**2 + f2**2) * (freqs**2 + f3**2))
        * (freqs**2 + f4**2))
analytic = 20 * np.log10(gain / gain[np.argmin(np.abs(freqs - 1000))])

fig, ax = plt.subplots(figsize=(9, 5))
ax.semilogx(freqs, analytic, "k--", label="Analytic (IEC 61672-1)")
for high_accuracy, label in ((False, "Plain bilinear"),
                             (True, "Oversampled (default)")):
    weighted = weighting_filter(impulse, fs, curve="A",
                                high_accuracy=high_accuracy)
    response = 20 * np.log10(np.abs(np.fft.rfft(weighted))
                             + np.finfo(float).eps)[1:]
    ax.semilogx(freqs, response, label=label)
ax.set(xlim=(1000, 20000), ylim=(-12, 3),
       xlabel="Frequency [Hz]", ylabel="A-weighting response [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

- `high_accuracy=False` restores the legacy plain-bilinear behavior.
- **Stateful (block) processing** always uses the legacy design: the internal
  FIR resampling is incompatible with block continuity. Passing
  `high_accuracy=True` together with `stateful=True` raises a `ValueError`.

```python
from phonometry import WeightingFilter, weighting_filter

# Uses `recording` and `fs` from the snippet above.
# Explicit legacy behavior
y = weighting_filter(recording, fs, curve="A", high_accuracy=False)

# Stateful block processing (legacy design, state carried between blocks)
wf = WeightingFilter(fs, "A", stateful=True)
blocks = [recording]                 # your sequence of recording blocks
for block in blocks:
    weighted = wf.filter(block)
```

See [Block Processing](/phonometry/guides/block-processing/) for the streaming workflow and
[Theory](/phonometry/reference/theory/) for the analytic curve definitions.

## 7. Verifying the IEC 61672-1 class

`verify_weighting_class` checks a weighting filter against the acceptance
limits of **IEC 61672-1:2013** (Table 3). It evaluates the filter's relative
response at the *exact* base-10 frequency behind each nominal label below
Nyquist (Table 3's design goals are computed at $f = 1000 \cdot 10^{n/10}$,
e.g. 15 848.9 Hz for "16 kHz"; IEC 61672-3 tests at the same frequencies),
subtracts the design-goal weighting, and reports the performance class per
frequency with its margin in dB. A dense logarithmic sweep additionally
enforces subclause 5.5.7 *between* the nominal frequencies — the deviation
from the analytic Annex E goal must stay within the larger of the two
adjacent limits, so a resonance or notch between nominals cannot pass — and
when Table 3 rows with finite lower limits fall beyond Nyquist the verdict is
flagged `range_limited` (it then attests the checked frequencies only, not
full 10 Hz-20 kHz conformance):

```python
from phonometry import WeightingFilter, verify_weighting_class

result = verify_weighting_class(WeightingFilter(48000, "A"))
print(result["overall_class"])          # 1
print(result["range_limited"])          # False
print(result["between_nominals"])       # {'worst_freq': ..., 'margin_class1_db': ...}
print(result["bands"][20])
# {'freq': 1000.0, 'class': 1, 'deviation_db': 0.0, 'margin_class1_db': 0.7, 'margin_class2_db': 1.0}
```

The Table 3 acceptance mask itself is public too: `weighting_class_limits(1)`
returns the 34 nominal frequencies with the lower/upper deviation limits (a
lower limit of `-inf` means only the upper limit applies). The limits qualify
the *deviation* from the design goal, so they are the same for A, C and Z.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_class_mask.svg" alt="A and C weighting deviations at 48 kHz threading within the IEC 61672-1 Table 3 class 1 acceptance corridor, with the wider class 2 limits dotted" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_class_mask_dark.svg" alt="A and C weighting deviations at 48 kHz threading within the IEC 61672-1 Table 3 class 1 acceptance corridor, with the wider class 2 limits dotted" style="width:80%">

*The oversampled A and C designs (blue, purple) stay near zero deviation,
well inside the class 1 corridor (shaded); the wider class 2 limits are
dotted. The corridor widens at the band extremes where only a one-sided
limit applies.*

---

**Standards.** IEC 61672-1:2013, *Electroacoustics — Sound level meters —
Part 1: Specifications* — the A, C and Z frequency-weighting curves (the
Annex E analytic definition from four corner frequencies, normalized to 0 dB
at 1 kHz), the class 1 tolerances the `high_accuracy` design keeps up to
16 kHz, and the Table 3 class 1/class 2 acceptance limits checked by
`verify_weighting_class`. ISO 7196:1995, *Acoustics — Frequency-weighting characteristic for
infrasound measurements* — the G-weighting pole/zero definition (Table 1),
verified against every Table 2 nominal response value (0.25 Hz to 315 Hz).

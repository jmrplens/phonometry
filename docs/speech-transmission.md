← [Documentation index](README.md)

# Speech Transmission Index (IEC 60268-16)

A public-address system, an intercom, a reverberant lecture hall — each is a
*transmission channel* between a talker's mouth and a listener's ear, and each
degrades speech in its own way. The **Speech Transmission Index** (STI) of
IEC 60268-16 rates that channel with a single number in [0, 1] by measuring
how much of the speech *envelope* survives the trip. This page covers the
modulation-transfer physics behind the index, the indirect method from a
measured room impulse response, and the direct STIPA measurement with its
standardized test signal.

> [!NOTE]
> **STI vs SII.** The STI characterises a *transmission channel* — how much of
> the speech modulation a room or sound system preserves — while the SII
> predicts intelligibility from *audibility*: how much of the speech spectrum
> clears the noise and the hearing threshold at the listener's ear. For the
> latter, see the [Speech Intelligibility Index guide](speech-intelligibility.md).

## 1. The modulation transfer function

Reverberation and noise do not muffle speech uniformly — they blur its
*envelope*: the slow (0.63–12.5 Hz) intensity modulations that carry
syllables. STI quantifies how much of that modulation survives from mouth
to ear, per octave band, as the **modulation transfer function** m(F). A
delta-like channel keeps m = 1 (STI = 1); reverberation low-passes the
envelope following Schroeder's closed form, and steady noise scales it:

$$
m(F) = \frac{1}{\sqrt{1 + \left(2\pi F\,\frac{T_{60}}{13.8}\right)^2}}
\cdot \frac{1}{1 + 10^{-\mathrm{SNR}/10}}
$$

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60.svg" alt="STI versus reverberation time with the IEC 60268-16 Annex F rating bands shaded" width="80%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain.svg" alt="STI measurement chain: STIPA source signal through the room to the microphone and the MTF analysis" width="92%"></picture>

## 2. Indirect and direct (STIPA) measurement

```python
import numpy as np
from phonometry import sti_from_impulse_response, stipa, stipa_signal

fs = 48000
# A measured room impulse response (synthesized decay so the example runs)
ir = np.random.default_rng(0).standard_normal(fs) * np.exp(-6.9 * np.arange(fs) / fs / 0.5)

# Indirect method: from a measured room impulse response
res = sti_from_impulse_response(ir, fs, snr=25.0)
print(f"STI = {res.sti:.2f}  ({res.rating})")   # e.g. 0.62 (D)

# Direct STIPA measurement: play stipa_signal() in the room, record it
test = stipa_signal(fs, seconds=18.0, level_db=80.0)
recording = test                       # in practice, the microphone signal after playback
res = stipa(recording, fs)
res.plot()   # per-band modulation transfer index (MTI) bars, STI + rating in the title
```

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from phonometry import sti_from_impulse_response

fs = 48000

# STI vs reverberation time: sweep sti_from_impulse_response over synthetic
# exponential decays (white noise x exp(-6.9077 t / T60)) at a T60 grid —
# exactly the physics behind the curve above:
rng = np.random.default_rng(0)
t60_grid = np.array([0.3, 0.5, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0, 4.0, 5.0])
sti_values = []
for t60 in t60_grid:
    t = np.arange(int(2 * t60 * fs)) / fs
    ir = rng.standard_normal(t.size) * np.exp(-6.9077 * t / t60)
    sti_values.append(sti_from_impulse_response(ir, fs).sti)

fig, ax = plt.subplots()
ax.semilogx(t60_grid, sti_values, "o-")
ax.set_xlabel("Reverberation time T60 [s]")
ax.set_ylabel("STI")
ax.set_ylim(0.0, 1.0)
ax.grid(True, which="both", alpha=0.3)
plt.show()
```

</details>

`stipa` emits a `UserWarning` when the recording is shorter than the
recommended 15 s (IEC 60268-16 STIPA practice, 15 s to 25 s): below that the
slow modulation components are averaged over too few periods and the STI is
biased low (an ideal loopback gives STI ≈ 0.956 at 5 s vs ≈ 0.998 at 18 s).

The implementation follows **Edition 5 (2020)**: Edition 4's normative PDF
is the base and every Ed. 5 change is source-attributed in the code — the
only numeric delta is the revised male speech spectrum of clause A.6.1.
CI checks the standard's own verification vectors: the six weighting-factor
band pairs to ±0.001 STI, the m ↔ STI mapping table, the level-dependent
masking control points, and Schroeder-form decays at four T₆₀ values.

The analyzer is also verified end to end against the **IEC 60268-16 rev 5
verification test bench** signals from [stipa.info](https://www.stipa.info)
(Embedded Acoustics BV): the direct-method modulation-depth staircase
(Annex C.3.2), the indirect-method exponential decays against the closed-form
Schroeder MTF (C.3.3), the filter-bank slope test with a +41 dB unmodulated
adjacent-octave tone (C.4.2, m ≥ 0.5), the weighting-factor band pairs (A.2.2)
and the filter-bank phase-distortion test with half-octave edge carriers
(A.3.1.2, |STI bias| < 0.01 over TI = 0.1–0.9). All five suites pass with the
level-dependent features disabled, as the bench prescribes. The 49 certified
WAVs stay local (third-party data, not committed); CI re-derives the same
signal constructions synthetically in the conformance suite.

### `sti_from_impulse_response()` / `stipa()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `ir` / `x` | 1D array | any / Pa | non-empty | IR (indirect) or STIPA recording (direct) |
| `fs` | int | Hz | > 0 | |
| `snr` | float or 7-vector, optional | dB | default `None` | Adds steady-noise degradation |
| `level` | 7-vector, optional | dB SPL | default `None` | Enables auditory masking + reception threshold (Tables A.2/A.3) |
| `ambient` | 7-vector, optional | dB SPL | needs `level` | Ambient noise band levels |
| `reference` | 1D array, optional (`stipa`) | — | default `None` | Measured source signal instead of the nominal m = 0.55 |

Both return `STIResult`: `sti`, `mti` (7 bands), `mtf` (7×14 or 7×2),
`band_levels`, `rating` (Annex F letter `A+`…`U`).

## See also

- [Room Acoustics](room-acoustics.md) — the measured impulse response the
  indirect method consumes, and the open-plan metrics (ISO 3382-3) built on
  per-position STI.
- [Speech Intelligibility Index](speech-intelligibility.md) — the
  audibility-based ANSI S3.5 index that complements the STI.
- [Psychoacoustics](psychoacoustics.md) — loudness, sharpness, tonality and
  roughness of the received sound.
- [Theory](theory.md) — the modulation-transfer derivation and the m ↔ STI
  mapping.

---

**Standards.** IEC 60268-16:2020 (Edition 5), *Sound system equipment —
Part 16: Objective rating of speech intelligibility by speech transmission
index* — the modulation transfer function and the m ↔ STI mapping, the STIPA
test signal and direct method, the indirect method from the impulse response,
auditory masking and the reception threshold (Tables A.2/A.3), the revised
male speech spectrum (clause A.6.1) and the Annex F rating letters.

← [Documentation index](README.md)

# Room-noise criteria (NC / RC Mark II)

Steady background noise in an occupied room — from ventilation, diffusers or
distant traffic — is rated against a family of **octave-band criterion curves**.
**ANSI/ASA S12.2-2019**, *Criteria for Evaluating Room Noise*, defines two
spectrum-in ratings that phonometry implements: the **Noise Criteria (NC)**
rating by the tangency method, and the **Room Criteria Mark II (RC)** rating
with its rumble/hiss spectral tag. Both work on octave-band sound pressure
levels over the ten bands from 16 Hz to 8000 Hz.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_noise_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_noise.svg" alt="The two ANSI S12.2 rating methods from one octave-band spectrum: on the left the NC tangency method (from the Table 1 curves, the NC value in each band, then NC equals the highest curve touched, giving NC-NN with a governing band); on the right the RC Mark II method (the mid-frequency average LMF of the 500, 1000 and 2000 Hz levels rounded to give RC-NN, then the spectral tag R for rumble, H for hiss or N for neutral by the clause D.3 deviation rules, giving RC-NN with a tag)" width="94%"></picture>

## 1. Noise Criteria — the tangency method

The **NC curves** (ANSI/ASA S12.2-2019 Table 1) are a family of octave-band
limits, each designated by its value at 1000 Hz (NC-15 up to NC-70). The
**tangency method** rates a measured spectrum by the value of the **highest NC
curve it touches**: for each octave band, the NC index whose curve passes
through the measured level is found, and the rating is the maximum across bands.
The band where that maximum occurs — the one that pushes the spectrum up against
the curves — is reported as the **governing band**.

```python
import numpy as np
import phonometry as ph

# Octave-band SPL, 16 Hz - 8000 Hz (a ventilation-dominated room).
spl = np.array([62.0, 62.0, 59.0, 57.0, 52.0, 42.0, 35.0, 29.0, 24.0, 19.0])

nc = ph.noise_criterion(spl)
print(round(nc.rating, 1))        # 42.5
print(nc.governing_frequency)     # 250.0  (the tangent band)
```

Because the rating interpolates between the tabulated curves it is a continuous
number: an NC rating of `42.5` sits half-way between NC-40 and NC-45. A subset
of the octave bands may be supplied together with their centre frequencies
(`ph.noise_criterion(levels, frequencies)`), which is convenient when only the
speech-interference bands were measured.

## 2. Room Criteria Mark II — rating and spectral tag

The **RC Mark II** curves (ANSI/ASA S12.2-2019 Annex D, Table D.1) have a
constant slope of **−5 dB/octave**, keyed to their value at 1000 Hz, with the
16 Hz level equal to the 31.5 Hz level and a low-frequency floor of 55 dB.
The numerical rating is the **mid-frequency average** `LMF` — the mean of the
500, 1000 and 2000 Hz levels — rounded to the nearest decibel (clause D.4):

$$
\text{LMF} = \tfrac{1}{3}\left(L_{500} + L_{1000} + L_{2000}\right),
\qquad \text{RC} = \operatorname{round}(\text{LMF}).
$$

A **spectral tag** then describes the *character* of the noise by how the
spectrum deviates from the reference RC curve (clause D.3): **rumble** (`R`)
when a band at or below 500 Hz exceeds the curve by more than 5 dB, **hiss**
(`H`) when a band at or above 1000 Hz exceeds it by more than 3 dB, and
**neutral** (`N`) when neither happens.

```python
import numpy as np
import phonometry as ph

spl = np.array([62.0, 62.0, 59.0, 57.0, 52.0, 42.0, 35.0, 29.0, 24.0, 19.0])

rc = ph.room_criterion(spl)
print(rc.label)             # RC-35(R)   -  a rumbly room
print(round(rc.lmf, 1))     # 35.3
print(rc.classification)    # R
```

The strong low-frequency content of this spectrum lifts the 63–250 Hz bands
well above the reference curve, so the noise is tagged `R` (rumble) — the
subjective "throb" of an oversized air handler.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/room_noise_criteria_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/room_noise_criteria.svg" alt="Two panels for the same ventilation-dominated room spectrum. Left: the measured octave-band levels over the NC curve family, with a red diamond marking the tangent point at 250 Hz that sets the NC-42.5 rating. Right: the same spectrum over the reference RC-35 curve, with the low-frequency bands rising through the shaded rumble tolerance (+5 dB below 500 Hz) so the noise is classified RC-35(R), and the hiss tolerance (+3 dB at and above 1000 Hz) shaded for comparison" width="96%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

spl = np.array([62.0, 62.0, 59.0, 57.0, 52.0, 42.0, 35.0, 29.0, 24.0, 19.0])

# One line each:
ph.noise_criterion(spl).plot()
ph.room_criterion(spl).plot()
plt.show()

# By hand, mirroring what NCResult.plot() / RCResult.plot() draw:
from phonometry.room_noise import NC_CURVES, NC_INDICES, OCTAVE_BANDS
nc, rc = ph.noise_criterion(spl), ph.room_criterion(spl)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

for row, idx in zip(NC_CURVES, NC_INDICES):
    ax1.plot(OCTAVE_BANDS, row, color="#bbbbbb", lw=0.8)
ax1.plot(OCTAVE_BANDS, spl, "o-", label="Measured")
gov = spl[OCTAVE_BANDS == nc.governing_frequency][0]
ax1.plot([nc.governing_frequency], [gov], "D", color="#d62728")
ax1.set_xscale("log"); ax1.set_title(f"NC-{nc.rating:g}")

ref = rc.reference_curve
low, high = OCTAVE_BANDS <= 500, OCTAVE_BANDS >= 1000
ax2.plot(OCTAVE_BANDS, ref, "s--", color="#7f7f7f", label=f"Reference RC-{rc.rating}")
ax2.fill_between(OCTAVE_BANDS[low], ref[low], ref[low] + 5, color="#ffbb78", alpha=0.35)
ax2.fill_between(OCTAVE_BANDS[high], ref[high], ref[high] + 3, color="#aec7e8", alpha=0.45)
ax2.plot(OCTAVE_BANDS, spl, "o-", label="Measured")
ax2.set_xscale("log"); ax2.set_title(rc.label)
plt.show()
```

</details>

The `NCResult` carries the `rating`, the `governing_frequency` and the measured
`levels`; the `RCResult` carries the `rating`, the `lmf`, the `classification`,
the `reference_curve` and a convenience `label` in the `RC-NN(A)` form. Each
exposes a `.plot()` that renders its panel above.

The balanced noise criteria (NCB), the room noise criterion for fluctuating
low-frequency noise (RNC, which needs a time series rather than a single
spectrum) and the numeric quality-assessment index (QAI, which the standard
defers to external references) are not part of this module.

---

**Standards.** ANSI/ASA S12.2-2019, *Criteria for Evaluating Room Noise* — the
NC curves and the tangency method (Table 1), and the RC Mark II curves
(Annex D, Table D.1), the mid-frequency-average rating (clause D.4) and the
neutral/rumble/hiss spectral tag (clause D.3).

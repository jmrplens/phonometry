---
title: "Impulsive-sound prominence (NT ACOU 112)"
description: "The NT ACOU 112:2002 Nordtest method for the prominence of impulsive sounds: the predicted prominence P from the onset rate and level difference of each impulse (clause 7), the graduated adjustment KI added to LAeq (clause 8), and the rating level over a reference time interval."
---

Noise with prominent impulses — hammering, riveting, pile driving — is more
annoying than a steady sound of the same equivalent level. **NT ACOU 112:2002**
(a Nordtest method) quantifies how *prominent* an impulse is and turns it into a
graduated adjustment `KI` added to the measured `LAeq`. The prominence is read
from two properties of each impulse's onset in the A-weighted, time-weighting-F
level history: how fast it rises (the **onset rate**) and how far it rises (the
**level difference**).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ntacou112.svg" alt="Flow from the A-weighted level history (an onset is where the gradient exceeds 10 dB/s) to the onset rate and level difference, the predicted prominence P = 3 lg(OR) + 2 lg(LD), the adjustment KI = 1.8 (P - 5) for P above 5, and the rating level over the reference time" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ntacou112_dark.svg" alt="Flow from the A-weighted level history (an onset is where the gradient exceeds 10 dB/s) to the onset rate and level difference, the predicted prominence P = 3 lg(OR) + 2 lg(LD), the adjustment KI = 1.8 (P - 5) for P above 5, and the rating level over the reference time" style="width:82%">

## 1. Predicted prominence (clause 7)

For each candidate impulse the **predicted prominence** `P` combines the onset
rate (in dB/s) and the level difference (in dB) on a logarithmic scale
(Formula 1):

$$
P = 3\,\lg(\text{onset rate}) + 2\,\lg(\text{level difference}).
$$

The coefficients were fitted to listening tests and `P` is designed to peak
around 15 for very sudden, loud impulses. The impulse with the **highest** `P`
over a 30-minute period governs. A level rise only *qualifies* as an impulse
when its onset rate exceeds 10 dB/s (clause 4.5; clause 8 applies the
adjustment "for sounds with onset rates larger than 10 dB/s" only):
`impulse_prominence` marks non-qualifying events in its `qualifies` mask,
warns about them, and never lets them set the governing prominence or a
`KI` (the adjustment is 0 dB when no event qualifies).

```python
import phonometry as ph

# Three candidate impulses: (onset rate dB/s, level difference dB).
result = ph.impulse_prominence([1200.0, 300.0, 60.0], [32.0, 18.0, 11.0])
print(result.per_impulse.round(2))  # [12.25  9.94  7.42]
print(round(result.prominence, 2))  # 12.25  (the governing impulse)
print(round(result.adjustment, 2))  # 13.05  dB
```

A single impulse can be evaluated directly with `predicted_prominence`:

```python
import phonometry as ph

# P = 3*lg(1000) + 2*lg(30) = 9 + 2.95 = 11.95.
print(round(ph.predicted_prominence(1000.0, 30.0), 4))  # 11.9542
```

## 2. Adjustment to LAeq (clause 8)

Below a prominence of 5 the impulse is not audible enough to matter; above it
the adjustment grows linearly (Formula 2):

$$
K_I = 1.8\,(P - 5)\ \text{dB} \quad (P > 5), \qquad K_I = 0 \quad (P \le 5).
$$

```python
import phonometry as ph

print(float(ph.impulse_adjustment(10.0)))  # 9.0 dB
print(float(ph.impulse_adjustment(5.0)))   # 0.0 dB (at the threshold)
```

The adjustment is applied to `LAeq,30min` from the single event with the
highest prominence. The **rating level** over a longer reference time combines
the impulse-adjusted equivalent levels of the sub-intervals (clause 8, Note 1):

$$
L_{Ar,T} = 10\,\lg\left(\frac{1}{T}\sum_N \Delta t_N\,
10^{(L_{Aeq,N} + K_{I,N})/10}\right).
$$

```python
import phonometry as ph

# Two 30-min periods: one impulsive (KI = 7.6 dB), one quiet.
print(round(ph.rating_level([72.0, 66.0], [7.6, 0.0], [30.0, 30.0], 60.0), 2))
# 76.78 dB
```

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_onset_detection.webm" autoplay loop muted controls playsinline title="Animation: an A-weighted level history drawing out, with the onset stretch (gradient above 10 dB/s) highlighted and the onset rate, level difference, prominence P and adjustment KI shown live" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_onset_detection_dark.webm" autoplay loop muted controls playsinline title="Animation: an A-weighted level history drawing out, with the onset stretch (gradient above 10 dB/s) highlighted and the onset rate, level difference, prominence P and adjustment KI shown live" style="width:88%"></video>

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_prominence.svg" alt="Left: the predicted prominence P rising with onset rate on a log axis for level differences of 5, 15 and 30 dB, reaching about 15 for a sudden loud impulse. Right: the adjustment KI, flat at zero up to the threshold P = 5 then linear, with three impulses marked and the governing one at KI = 13 dB" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_prominence_dark.svg" alt="Left: the predicted prominence P rising with onset rate on a log axis for level differences of 5, 15 and 30 dB, reaching about 15 for a sudden loud impulse. Right: the adjustment KI, flat at zero up to the threshold P = 5 then linear, with three impulses marked and the governing one at KI = 13 dB" style="width:96%">

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

# One line for the adjustment curve with the impulses marked:
ph.impulse_prominence([1200.0, 300.0, 60.0], [32.0, 18.0, 11.0]).plot()
plt.show()

# By hand, the left panel — P vs onset rate for three level differences:
orate = np.logspace(1, 4, 200)
for ld in (5.0, 15.0, 30.0):
    plt.plot(orate, ph.predicted_prominence(orate, np.full_like(orate, ld)),
             label=f"LD = {ld:g} dB")
plt.xscale("log"); plt.legend(); plt.show()
```

</details>

The `ImpulseProminenceResult` carries the `per_impulse` prominences, the governing
`prominence` and its `adjustment`, and its `.plot()` draws the `KI(P)` curve
with the impulses marked. The method is a supplement to the environmental-noise
measurement of [ISO 1996-2](/phonometry/guides/levels/).

---

**Standards.** NT ACOU 112:2002 (Nordtest), *Prominence of impulsive sounds and
for adjustment of LAeq* — the predicted prominence (clause 7, Formula 1), the
adjustment to LAeq (clause 8, Formula 2) and the rating level (clause 8,
Note 1), with the onset defined in clauses 4.5-4.7.

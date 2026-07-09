← [Documentation index](README.md)

# Impulsive-sound prominence (NT ACOU 112)

Noise with prominent impulses — hammering, riveting, pile driving — is more
annoying than a steady sound of the same equivalent level. **NT ACOU 112:2002**
(a Nordtest method) quantifies how *prominent* an impulse is and turns it into a
graduated adjustment `KI` added to the measured `LAeq`. The prominence is read
from two properties of each impulse's onset in the A-weighted, time-weighting-F
level history: how fast it rises (the **onset rate**) and how far it rises (the
**level difference**).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ntacou112_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ntacou112.svg" alt="Flow from the A-weighted time-weighting-F level history, where an onset is a stretch whose gradient exceeds 10 dB/s, to the per-impulse onset rate and level difference, then the predicted prominence P equals 3 times log of the onset rate plus 2 times log of the level difference (the highest P over 30 minutes governs), then the adjustment KI equals 1.8 times (P minus 5) dB for P above 5 and zero otherwise, and finally the rating level combining the impulse-adjusted equivalent levels over the reference time" width="82%"></picture>

## 1. Predicted prominence (clause 7)

For each candidate impulse the **predicted prominence** `P` combines the onset
rate (in dB/s) and the level difference (in dB) on a logarithmic scale
(Formula 1):

$$
P = 3\,\lg(\text{onset rate}) + 2\,\lg(\text{level difference}).
$$

The coefficients were fitted to listening tests and `P` is designed to peak
around 15 for very sudden, loud impulses. The impulse with the **highest** `P`
over a 30-minute period governs.

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
L_{Ar,T} = 10\,\lg\!\left(\frac{1}{T}\sum_N \Delta t_N\,
10^{(L_{Aeq,N} + K_{I,N})/10}\right).
$$

```python
import phonometry as ph

# Two 30-min periods: one impulsive (KI = 7.6 dB), one quiet.
print(round(ph.rating_level([72.0, 66.0], [7.6, 0.0], [30.0, 30.0], 60.0), 2))
# 76.78 dB
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_prominence_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_prominence.png" alt="Two panels. Left: the predicted prominence P rising with onset rate (log axis) for level differences of 5, 15 and 30 dB, reaching about 15 for a very sudden, loud impulse. Right: the adjustment KI as a function of prominence, flat at zero up to the threshold P = 5 and then linear at 1.8 dB per unit, with three example impulses marked and the governing one at KI = 13 dB" width="96%"></picture>

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
measurement of ISO 1996-2.

---

**Standards.** NT ACOU 112:2002 (Nordtest), *Prominence of impulsive sounds and
for adjustment of LAeq* — the predicted prominence (clause 7, Formula 1), the
adjustment to LAeq (clause 8, Formula 2) and the rating level (clause 8,
Note 1), with the onset defined in clauses 4.5-4.7.

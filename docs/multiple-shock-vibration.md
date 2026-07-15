← [Documentation index](README.md)

# Multiple-shock whole-body vibration (ISO 2631-5)

Vibration that contains repeated **mechanical shocks** — off-road vehicles,
high-speed marine craft, earth-moving machinery — loads the lumbar spine far
more than its equivalent r.m.s. level suggests. **ISO 2631-5:2018** predicts
the resulting spinal response and the risk of lumbar injury from the measured
vertical seat acceleration. phonometry implements the normative **Clause 5**
spinal-response model and the **Annex C** health-effect assessment. (The Annex A
/ Annex E finite-element model is distributed by ISO as separate software and is
out of scope here.)

The boundary with the basic method is explicit. ISO 2631-1 declares its r.m.s.
evaluation normally sufficient up to a crest factor of 9, and offers the
running r.m.s./MTVV and the VDV beyond it; ISO 2631-5 is the additional method
for the regime past those, where the record contains repeated shocks. Its
clause 4 then splits that regime in two: *severe* conditions with possible
free fall or loss of contact with the seat and a dominant z-axis (military
off-road vehicles, high-speed marine craft) use the Clause 5 model implemented
here, while *less severe* conditions in which the occupant stays seated
throughout (tractors, forestry and earth-moving machinery on rough ground)
belong to the Annex A finite-element model. In case of doubt the delineation
is quantitative: when the band-limited vertical peak acceleration exceeds
9.81 m/s² (1 g, the free-fall threshold), Clause 5 and Annex C apply.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso2631_5_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso2631_5.svg" alt="Flow from the vertical seat acceleration az(t), band-limited per ISO 2631-1, through the spinal response Az(t) from the seat-to-spine transfer function (one zero, six poles), the acceleration dose Dz = 1.07 times the sixth root of the sum of the positive response peaks to the sixth power and the daily dose Dzd, the compressive stress Sd = mz times Dzd, the age-cumulated stress variable R, and finally the Weibull probability of lumbar injury" width="86%"></picture>

## 1. Spinal response (clause 5.2)

A seat-to-spine transfer function ``H(f)`` — one complex zero and six complex
poles, unity transmissibility at 0 Hz and a resonance near 5 Hz — maps the
measured seat acceleration to the vertical spinal response ``Az(t)``
(Formula 1/2):

$$
A_z(t) = \mathcal{F}^{-1}\!\left[H(f)\,\mathcal{F}[a_z(t)]\right].
$$

The input record must be **conditioned (DC-removed)**: because `H` is unity at
0 Hz by design, a DC offset — e.g. the 1 g gravity component of a DC-coupled
accelerometer — passes straight into `Az(t)` and corrupts the positive response
peaks of the dose. Subtract the mean (or high-pass) before processing.

```python
import phonometry as ph

# The transmissibility peaks near the ~5 Hz spinal resonance.
print(round(abs(ph.seat_to_spine_transfer([2.0])[0]), 2))  # 1.06
print(round(abs(ph.seat_to_spine_transfer([5.0])[0]), 2))  # 1.54
```

## 2. Acceleration dose (clause 5.3)

The **acceleration dose** combines the positive response peaks ``Az,i`` (each
the maximum between two consecutive zero crossings) with a sixth-power law, so
the largest shocks dominate (Formula 3):

$$
D_z = 1.07\left(\sum_i A_{z,i}^{\,6}\right)^{1/6}.
$$

A daily dose scales the measured dose to the daily exposure time ``td`` over the
measurement time ``tm`` (Formula 4): ``Dzd = Dz * (td/tm)**(1/6)``.

```python
import phonometry as ph

# Five 40 m/s2 response peaks in a day (the Annex C worked example).
print(round(ph.dose_from_peaks([40.0] * 5), 2))  # 55.97  m/s2
```

## 3. Injury risk (Annex C)

The daily dose becomes a daily **compressive stress** ``Sd = mz * Dzd``
(Formula C.1), where ``mz`` (0.029 MPa per m/s² for an 82 kg male, 0.025 for a
64 kg female) converts acceleration to vertebral stress. The stress accumulates
over the exposure years against the ageing spine's reducing ultimate strength
``Su = 6.75 - Sage*(b+i)`` (Formulae C.3/C.4):

$$
R = \left[\sum_{i=0}^{n-1}
\left(\frac{S_d\,N^{1/6}}{S_{u,i} - S_{\mathrm{stat}}}\right)^{6}\right]^{1/6},
$$

and a Weibull model gives the probability of lumbar injury (Formula C.5):

$$
\Pi(R) = 1 - \exp\!\left[-\left(\frac{R}{\alpha}\right)^{\beta}\right].
$$

```python
import phonometry as ph

# Annex C worked example: 5 x 40 m/s2/day, 82 kg male, age 20 for 20 years,
# 120 days/year.
dz = ph.dose_from_peaks([40.0] * 5)
sd = ph.compression_dose(dz)                     # 1.62 MPa
r = ph.injury_risk(sd, start_age=20, years=20, days_per_year=120)
print(round(r, 2))                               # 1.22
print(round(100 * ph.injury_probability(r)))     # 37  % risk of injury
```

From a measured time history the whole chain is one call:

```python
import numpy as np
import phonometry as ph

# A synthetic 10 s seat record at 256 Hz with five 60 m/s2 shocks (stand-in
# for a measured az(t)).
fs = 256.0
az = np.zeros(2560)
az[256::512] = 60.0
result = ph.multiple_shock_assessment(
    az, fs, start_age=20, years=20, days_per_year=120, sex="male",
)
print(round(result.acceleration_dose, 2))  # 20.94  m/s2
print(round(result.risk, 2))               # 0.46
print(round(result.probability, 2))        # 0.03
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/multiple_shock_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/multiple_shock.svg" alt="Two panels. Left: the seat-to-spine transmissibility rising to about 1.6 near a 5 Hz resonance then rolling off to near zero by 80 Hz. Right: the probability of lumbar injury as a Weibull function of the stress variable R for male and female, with the 10, 50 and 90 percent risk levels marked and the Annex C male worked example at R = 1.22, about 37 percent" width="96%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

# Left: the seat-to-spine transfer function magnitude.
f = np.logspace(np.log10(0.5), np.log10(80.0), 400)
plt.plot(f, np.abs(ph.seat_to_spine_transfer(f)))
plt.xscale("log"); plt.show()

# Right: the injury-probability curve with this assessment's R marked
# (az/fs as in the snippet above).
fs = 256.0
az = np.zeros(2560)
az[256::512] = 60.0
ph.multiple_shock_assessment(
    az, fs, start_age=20, years=20, days_per_year=120,
).plot()
plt.show()
```

</details>

The `MultipleShockResult` carries the dose ``Dz``, the daily dose ``Dzd``, the
compressive stress ``Sd``, the stress variable ``R``, the injury probability and
the response peaks, and its `.plot()` draws the injury-probability curve with the
10/50/90 % risk thresholds of Table C.2. This complements the r.m.s.,
running-r.m.s./MTVV and VDV metrics of [Human Vibration](human-vibration.md)
(ISO 2631-1).

## References

- Griffin, M. J. (1996). *Handbook of human vibration*. Academic Press.
  ISBN 978-0-12-303041-2.
  [Publisher page](https://shop.elsevier.com/books/handbook-of-human-vibration/griffin/978-0-12-303041-2).
  Background on whole-body shock exposure, spinal biodynamics and the
  lumbar health effects that the ISO 2631-5 dose model quantifies.

---

**Standards.** ISO 2631-5:2018, *Mechanical vibration and shock — Evaluation of
human exposure to whole-body vibration — Part 5: Method for evaluation of
vibration containing multiple shocks* — the seat-to-spine transfer function
(clause 5.2, Formula 1), the acceleration and daily dose (clause 5.3,
Formulae 3-5) and the Annex C assessment of adverse health effects (Formulae
C.1, C.3-C.5, Tables C.1/C.2).

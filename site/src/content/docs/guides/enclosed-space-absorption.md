---
title: "Sound absorption in enclosed spaces (EN 12354-6)"
description: "The EN 12354-6:2003 prediction of a room's total equivalent sound absorption area and reverberation time from the absorption of its surfaces and objects (the normative Clause 4 model): the absorption area of Formula 1, the object and air terms, and the reverberation time of Formula 5."
---

**EN 12354-6:2003** predicts the **total equivalent sound absorption area** of a
room and its **reverberation time** from the absorption of its surfaces and
objects — the design counterpart of the measured reverberation time. It is the
absorption member of the EN 12354 building-acoustics family (the airborne and
impact insulation members live in
[Predicting Sound Insulation (EN 12354)](/phonometry/guides/insulation-prediction/)). phonometry
implements the normative Clause 4 model. (The informative Annex D method for
irregular spaces is out of scope.)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_en12354_6.svg" alt="Flow from the room surfaces and objects into the total equivalent absorption area A, the object fraction psi, and the reverberation time T = 55.3/c0 times V times (1 minus psi) over A" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_en12354_6_dark.svg" alt="Flow from the room surfaces and objects into the total equivalent absorption area A, the object fraction psi, and the reverberation time T = 55.3/c0 times V times (1 minus psi) over A" style="width:82%">

## 1. Equivalent absorption area (clause 4.3)

The total equivalent absorption area sums, over the surfaces $i$, the objects
$j$ and the object arrays $k$, each surface's area times its absorption
coefficient, the equivalent absorption areas of the objects, the object arrays
(groups of identical objects treated as an absorbing surface of area $S_k$),
and the air absorption (Formula 1):

$$
A = \sum_i \alpha_{s,i}\,S_i + \sum_j A_{\mathrm{obj},j}
    + \sum_k \alpha_{s,k}\,S_k + A_{\mathrm{air}}.
$$

For hard, irregular objects whose absorption is not measured, an empirical
estimate from the volume is used (Formula 4): `Aobj = Vobj**(2/3)`.

```python
import phonometry as ph

# EN 12354-6 Annex E, bare room (29.75 m3), 1000 Hz octave band.
surfaces = [(12.39, 0.05), (12.39, 0.02), (10.90, 0.04),
            (10.90, 0.04), (6.55, 0.04), (6.55, 0.04)]
print(round(ph.equivalent_absorption_area(surfaces), 2))  # 2.26  m2
print(round(float(ph.hard_object_absorption(0.65)), 3))   # 0.75  m2
```

Air absorption uses the power attenuation coefficient `m` (Formula 2):
`Aair = 4*m*V*(1 - psi)`. Below 1 kHz and for rooms under 200 m³ it can be
neglected.

## 2. Reverberation time (clause 4.4)

The reverberation time follows from the absorption area, the volume and the
object fraction `psi = sum(Vobj)/V` (Formula 5):

$$
T = \frac{55.3}{c_0}\,\frac{V\,(1 - \psi)}{A},
$$

where the speed of sound `c0 = 345.6 m/s` makes the factor `55.3/c0` the
familiar `0.16`.

```python
import phonometry as ph

surfaces = [(12.39, 0.05), (12.39, 0.02), (10.90, 0.04),
            (10.90, 0.04), (6.55, 0.04), (6.55, 0.04)]
a = ph.equivalent_absorption_area(surfaces)
print(round(ph.reverberation_time(a, 29.75), 1))          # 2.1  s

# Annex E case 2: add furniture (hard objects) to the same room.
volumes = [0.15, 0.60, 0.05, 0.05, 0.65, 0.65]
aobj = ph.hard_object_absorption(volumes)
psi = ph.object_fraction(volumes, 29.75)                  # 0.072
a2 = ph.equivalent_absorption_area(surfaces, objects=aobj)
print(round(a2, 2), round(ph.reverberation_time(a2, 29.75, object_fraction=psi), 1))
# 5.03 0.9
```

Per octave band, one call takes the surfaces (with per-band absorption
coefficients) and the air condition and returns the whole spectrum:

```python
import phonometry as ph

# Per-band absorption coefficients (125 Hz to 8 kHz) for each surface.
plaster = [0.02, 0.03, 0.03, 0.04, 0.05, 0.05, 0.05]
tile = [0.15, 0.35, 0.65, 0.85, 0.90, 0.90, 0.85]
result = ph.enclosed_space_reverberation(
    [(54.0, plaster), (20.0, plaster), (20.0, tile)],
    volume=60.0, air_condition="20C_50-70",
)
print(result.reverberation_time.round(2))
# [2.13 1.03 0.62 0.48 0.43 0.42 0.4 ]
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosed_space_absorption.svg" alt="Two panels for a 60 cubic metre office with a bare versus acoustically-treated ceiling: the equivalent absorption area per octave band, much higher with the acoustic ceiling, and the reverberation time falling from about five seconds at low frequency for the bare room to under one second with the acoustic ceiling" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosed_space_absorption_dark.svg" alt="Two panels for a 60 cubic metre office with a bare versus acoustically-treated ceiling: the equivalent absorption area per octave band, much higher with the acoustic ceiling, and the reverberation time falling from about five seconds at low frequency for the bare room to under one second with the acoustic ceiling" style="width:96%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph

plaster = [0.02, 0.03, 0.03, 0.04, 0.05, 0.05, 0.05]
tile = [0.15, 0.35, 0.65, 0.85, 0.90, 0.90, 0.85]
walls_floor = [(54.0, plaster), (20.0, plaster)]
for ceiling in (plaster, tile):
    ph.enclosed_space_reverberation(
        [*walls_floor, (20.0, ceiling)], 60.0, air_condition="20C_50-70",
    ).plot()
plt.show()
```

</details>

The `ReverberationResult` carries the per-band absorption area and reverberation
time, the volume and the object fraction, and its `.plot()` draws the
reverberation-time spectrum. This is the prediction counterpart of the measured
reverberation time in
[Room Acoustics](/phonometry/guides/room-acoustics/) (ISO 3382) and
of the reverberation-room absorption of
[Acoustic Materials](/phonometry/guides/materials/) (ISO 354).

## 3. Where the input data comes from

**Surface coefficients.** The standard expects the $\alpha_{s,i}$ to come
from laboratory measurements to EN ISO 354, the reverberation-room method
of [Acoustic Materials](/phonometry/guides/materials/); theoretical,
empirical or field values are admitted as long as the data source is
stated. ISO 354 delivers one-third-octave data, and an octave-band
calculation takes the arithmetic mean of the three thirds as its input. A
reverberation-room coefficient can exceed 1.0 (edge diffraction scatters
more energy into the sample than its flat area intercepts); it enters
Formula 1 as measured, without clamping, because the same diffuse-field
convention that produced it is the one the model assumes.

**Furniture and occupants.** Objects contribute through three routes:
a measured equivalent absorption area $A_{obj}$ when one exists (persons
and seating have tabulated values in the informative Annex C), the
Formula 4 estimate $V_{obj}^{2/3}$ for hard, irregular, unmeasured objects
(furniture, machinery), and object *arrays* rated as an absorbing surface
$\alpha_s S_k$ when many similar objects cover a zone (an audience, a
storage rack). Objects also displace air: their summed volume enters the
object fraction $\psi$ that shortens $T$ in Formula 5 beyond what their
absorption alone would.

**Air.** The air term $A_{air} = 4mV(1-\psi)$ uses the power attenuation
coefficient $m$ from the standard's Table 1, resolved by the
`air_condition` strings (temperature and relative-humidity class, derived
from ISO 9613-1); it only matters above 1 kHz and grows with the volume.

**Validity limits (clause 4.6).** The model assumes an ordinary,
reasonably diffuse room: no dimension more than 5 times another, opposite
surface pairs whose coefficients differ by less than a factor of 3 (unless
scattering objects are present) and an object fraction below 0.2. Outside
those limits the field is not diffuse and the model errs on the optimistic
side: the standard's own accuracy clause records measured reverberation
times up to twice the prediction in low-diffusivity rooms. The classical
alternatives for those cases live in
[Reverberation-time prediction](/phonometry/guides/reverberation-prediction/).

## References

- European Committee for Standardization. (2003). *Building acoustics —
  Estimation of acoustic performance of buildings from the performance of
  elements — Part 6: Sound absorption in enclosed spaces*
  (EN 12354-6:2003).
  [BSI Knowledge record (BS EN 12354-6:2003)](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-of-buildings-from-the-performance-of-elements-sound-absorption-in-enclosed-spaces).
  The Clause 4 model, its input-data rules and its validity limits.
- International Organization for Standardization. (2003). *Acoustics —
  Measurement of sound absorption in a reverberation room* (ISO 354:2003).
  [iso.org catalogue](https://www.iso.org/standard/34545.html).
  The laboratory measurement the surface and array coefficients come from.
- Kuttruff, H. (2016). *Room acoustics* (6th ed.). CRC Press.
  [doi:10.1201/9781315372150](https://doi.org/10.1201/9781315372150).
  The statistical reverberation theory the standard's formulae specialise.

---

**Standards.** EN 12354-6:2003, *Building acoustics — Estimation of acoustic
performance of buildings from the performance of elements — Part 6: Sound
absorption in enclosed spaces* — the total equivalent absorption area
(clause 4.3, Formulae 1-4, Table 1) and the reverberation time (clause 4.4,
Formula 5), validated against the three worked cases of Annex E.

## See also

- API reference: [`room.enclosed_space_absorption`](/phonometry/reference/api/rooms/enclosed-space-absorption/).

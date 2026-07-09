← [Documentation index](README.md)

# Sound absorption in enclosed spaces (EN 12354-6)

**EN 12354-6:2003** predicts the **total equivalent sound absorption area** of a
room and its **reverberation time** from the absorption of its surfaces and
objects — the design counterpart of the measured reverberation time. It is the
absorption member of the EN 12354 building-acoustics family (the airborne and
impact insulation members live in [Building Acoustics](building-acoustics.md)).
phonometry implements the normative Clause 4 model. (The informative Annex D
method for irregular spaces is out of scope.)

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_en12354_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_en12354_6.svg" alt="Flow from the room surfaces (area and absorption per band) and objects (volume, giving an equivalent area Vobj to the two-thirds power) into the total equivalent absorption area A = sum of alpha times S plus the object areas plus air absorption, then the object fraction psi, and finally the reverberation time T = 55.3/co times V times (1 minus psi) over A" width="82%"></picture>

## 1. Equivalent absorption area (clause 4.3)

The total equivalent absorption area sums each surface's area times its
absorption coefficient, the equivalent absorption areas of objects, and the air
absorption (Formula 1):

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

Air absorption uses the power attenuation coefficient ``m`` (Formula 2):
`Aair = 4*m*V*(1 - psi)`. Below 1 kHz and for rooms under 200 m³ it can be
neglected.

## 2. Reverberation time (clause 4.4)

The reverberation time follows from the absorption area, the volume and the
object fraction `psi = sum(Vobj)/V` (Formula 5):

$$
T = \frac{55{,}3}{c_0}\,\frac{V\,(1 - \psi)}{A},
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
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosed_space_absorption_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosed_space_absorption.png" alt="Two panels for a 60 cubic metre office with a bare versus an acoustically-treated ceiling. Left: the equivalent absorption area per octave band, much higher across mid and high frequencies with the acoustic ceiling. Right: the reverberation time per octave band, falling from around five seconds at low frequency for the bare room to under one second with the acoustic ceiling" width="96%"></picture>

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
reverberation time in [Room and Building Acoustics](room-acoustics.md)
(ISO 3382) and of the reverberation-room absorption of
[Acoustic Materials](materials.md) (ISO 354).

---

**Standards.** EN 12354-6:2003, *Building acoustics — Estimation of acoustic
performance of buildings from the performance of elements — Part 6: Sound
absorption in enclosed spaces* — the total equivalent absorption area
(clause 4.3, Formulae 1-4, Table 1) and the reverberation time (clause 4.4,
Formula 5), validated against the three worked cases of Annex E.

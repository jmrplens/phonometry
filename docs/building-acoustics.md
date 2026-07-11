← [Documentation index](README.md)

# Building Acoustics & Sound Insulation

This guide continues from the [Room Acoustics guide](room-acoustics.md):
the same impulse response, measured either side of a partition, yields its sound
insulation. Where room acoustics describes the sound field inside a single space,
building acoustics describes how much of that field passes *between* spaces. This
page follows the insulation chain — field airborne, impact and façade insulation
with single-number ratings (ISO 16283-1/2/3, ISO 717-1/2), the laboratory
characterisation of a building element (ISO 10140), the prediction of in-situ
performance from flanking transmission (EN 12354-1/2), and the measurement
uncertainty that qualifies every rating (ISO 12999-1).

## 1. Field insulation and single-number ratings (ISO 16283-1, ISO 717-1)

To rate a wall or floor, measure the energy-average level in the **source**
room ($L_1$) and the **receiving** room ($L_2$) per one-third-octave band
and form the level difference $D = L_1 - L_2$. Two normalisations make it
comparable between rooms. The **standardized level difference** references
the receiving-room reverberation time $T$ to $T_0 = 0.5$ s (so with
$T = 0.5$ s, $D_{nT} = D$ exactly), and the **apparent sound reduction
index** normalises by the partition area $S$ and the Sabine absorption area
$A$:

$$
D_{nT} = D + 10 \log_{10} \frac{T}{T_0}, \qquad
R' = D + 10 \log_{10} \frac{S}{A}, \qquad A = \frac{0.16\ V}{T}.
$$

Positions are energy-averaged with
$L = 10 \log_{10}\left( \frac{1}{n} \sum_i 10^{L_i/10} \right)$.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup.svg" alt="Field airborne insulation setup: a loudspeaker in the source room, microphones energy-averaged in source and receiving rooms across the common partition" width="92%"></picture>

The band spectrum is collapsed to one number by the **reference-curve
method** of ISO 717-1: a fixed reference curve is shifted in 1 dB steps
toward the measured curve until the sum of *unfavourable* deviations
(where the measurement falls below the reference) is as large as possible
but not more than 32.0 dB (16 one-third-octave bands) or 10.0 dB (5 octave
bands). The rating (`Rw`, `R'w`, `DnT,w` …) is the shifted reference read at
500 Hz. The **spectrum adaptation terms** $C$ (pink noise) and $C_{tr}$
(urban traffic) add the low-frequency penalty of a real source.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating.svg" alt="Measured one-third-octave sound reduction index with the shifted ISO 717-1 reference curve and the resulting weighted rating at 500 Hz" width="80%"></picture>

```python
import numpy as np
from phonometry import airborne_insulation, weighted_rating, energy_average_level

# Energy-average several microphone positions in one room (dB)
print(round(float(energy_average_level([60.0, 66.0])), 1))   # 64.0

# Field insulation per band; area S and volume V add R'
l1 = np.full(16, 80.0)                                # source-room levels
l2 = np.full(16, 40.0)                                # receiving-room levels
t2 = np.full(16, 0.5)                                 # receiving-room T (s)
ins = airborne_insulation(l1, l2, t2, area=10.0, volume=50.0)
print(round(float(ins.dnt[0]), 1))                   # 40.0  (= D since T = T0)
print(round(float(ins.r_prime[0]), 1))               # 38.0

# Single-number rating from a measured 16-band R spectrum (ISO 717-1 Annex C)
R = [20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
     28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5]
w = weighted_rating(R)
print(w.rating, w.c, w.ctr)                          # 30 -2 -3  ->  Rw(C;Ctr) = 30(-2;-3)

w.plot()   # measured R' vs shifted ISO 717-1 reference, deviations shaded (needs matplotlib)
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# One line — measured curve vs the shifted ISO 717-1 reference, deviations shaded:
w.plot()
plt.show()

# By hand, from the band curve the result now carries:
fig, ax = plt.subplots()
ax.semilogx(w.band_centers, w.measured, "o-", label="Measured R'")
ax.semilogx(w.band_centers, w.shifted_reference, "s--", label="Shifted reference")
ax.fill_between(w.band_centers, w.measured, w.shifted_reference,
                where=w.measured < w.shifted_reference, interpolate=True,
                alpha=0.3, label="Unfavourable deviations")
ax.set_xlabel("Frequency [Hz]")
ax.set_ylabel("Sound reduction index [dB]")
ax.set_title(f"Rw = {w.rating} dB  (C={w.c:+d}; Ctr={w.ctr:+d})")
ax.legend()
plt.show()
```

</details>

Compute `l1`, `l2` and `t2` on the same 16 one-third-octave bands from
100 Hz to 3150 Hz — obtain `t2` from
`room_parameters(ir, fs, limits=(100, 3150), fraction=3).t30`, for example — and
pass them to `airborne_insulation`. Feed that function's `dnt` (or `r_prime`)
spectrum to `weighted_rating`, so every band aligns index-by-index with the
ISO 717-1 reference curve.

### `airborne_insulation()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `l1` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Source-room levels (2D is energy-averaged) |
| `l2` | 1D or 2D array | dB | same band count | Receiving-room levels |
| `t2` | 1D array | s | > 0, one per band | Receiving-room reverberation time |
| `area` | float, optional | m² | > 0, with `volume` | Partition area `S` (enables `R'`) |
| `volume` | float, optional | m³ | > 0, with `area` | Receiving-room volume `V` |
| `t0` | float | s | default `0.5` | Reference reverberation time `T0` |

### `weighted_rating()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `values_by_band` | 1D array | dB | 16 (thirds) or 5 (octaves) | Measured `R`, `R'`, `DnT` … per band |
| `bands` | str or `None` | — | `'third-octave'` / `'octave'` / `None` | `None` infers from the count |

`airborne_insulation()` returns an `AirborneInsulationResult` (`d`, `dnt`,
`r_prime` or `None`); `weighted_rating()` returns a `WeightedRatingResult`
(`rating`, `c`, `ctr`, `unfavourable_sum`, all integers except the sum).

### Impact sound (ISO 16283-2, ISO 717-2)

Footstep noise is rated the other way round. Instead of how much a floor
*blocks*, impact insulation measures how much a standardized **tapping
machine** on the floor above puts into the room below — so a *higher* number
is *worse*. The energy-average impact sound pressure level $L_i$ in the
receiving room is normalised like the airborne case, but with a sign flip on
the reverberation term:

$$
L'_{nT} = L_i - 10 \log_{10} \frac{T}{T_0}, \qquad
L'_n = L_i + 10 \log_{10} \frac{A}{A_0}, \quad
A_0 = 10\ \text{m}^2,\ A = \frac{0.16\ V}{T}.
$$

The **standardized** impact level $L'_{nT}$ ($T_0 = 0.5$ s for dwellings)
needs only the receiving-room $T$, so with $T = 0.5$ s it equals $L_i$; the
**normalized** level $L'_n$ (referenced to a 10 m² absorption area) also needs
the receiving-room volume. Note the **minus** sign — more reverberation
*lowers* $L'_{nT}$, opposite to the airborne $D_{nT}$.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impact_setup_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impact_setup.svg" alt="Field impact insulation setup: a standardized tapping machine on the floor of the source room above, microphones energy-averaged in the receiving room below, and the receiving-room reverberation time" width="92%"></picture>

The single-number rating (ISO 717-2) shifts the same style of reference curve,
but an **unfavourable deviation now occurs where the measurement *exceeds* the
reference** (impact noise is worse when higher) — the sign opposite to
ISO 717-1. The rating (`Ln,w`, `L'n,w`, `L'nT,w`) is the shifted reference read
at 500 Hz; for octave bands it is then reduced by 5 dB. The spectrum
adaptation term $C_I = L_{n,\text{sum}} - 15 - L_{n,w}$ uses the energetic sum
over 100–2500 Hz (16-band thirds excluding 3150 Hz) or 125–2000 Hz (octaves).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating.svg" alt="Measured one-third-octave normalized impact sound pressure level with the shifted ISO 717-2 reference curve and the resulting weighted rating read at 500 Hz" width="80%"></picture>

```python
import numpy as np
from phonometry import impact_insulation, weighted_impact_rating

# 16 one-third-octave impact levels Li (100 Hz - 3150 Hz), dB, from the
# ISO 717-2 Annex C worked example, and the receiving-room T per band.
li = np.array([62.1, 63.2, 63.5, 66.2, 68.5, 70.0, 71.7, 73.1,
               73.8, 73.5, 73.8, 73.3, 73.1, 73.0, 72.4, 71.2])
t2 = np.full(16, 0.5)

imp = impact_insulation(li, t2, volume=50.0)
print(round(float(imp.l_n_t[0]), 1))          # 62.1  (= Li since T = T0)
print(round(float(imp.l_n[0]), 1))            # 64.1  normalized to A0 = 10 m^2

# Weighted impact rating + spectrum adaptation term CI (ISO 717-2)
res_imp = weighted_impact_rating(imp.l_n_t)
print(res_imp.rating, res_imp.ci, res_imp.unfavourable_sum)   # 79 -11 28.0  ->  L'nT,w(CI)=79(-11)

# Octave-band data carry the extra -5 dB reduction (Clause 4.3.2)
octave = np.array([65.3, 64.5, 58.0, 55.8, 43.0])
print(weighted_impact_rating(octave).rating)  # 54

res_imp.plot()   # measured L'nT vs shifted ISO 717-2 reference, measured-above shaded (needs matplotlib)
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# One line — measured L'nT vs the shifted ISO 717-2 reference (measured-above shaded):
res_imp.plot()
plt.show()

# By hand, from the band curve the result now carries (note the opposite sign:
# an unfavourable deviation is where the MEASURED level exceeds the reference).
# Here the input was l_n_t, so the rated quantity is the field level L'nT,w:
fig, ax = plt.subplots()
ax.semilogx(res_imp.band_centers, res_imp.measured, "o-", label="Measured L'nT")
ax.semilogx(res_imp.band_centers, res_imp.shifted_reference, "s--", label="Shifted reference")
ax.fill_between(res_imp.band_centers, res_imp.shifted_reference, res_imp.measured,
                where=res_imp.measured > res_imp.shifted_reference, interpolate=True,
                alpha=0.3, label="Unfavourable deviations")
ax.set_xlabel("Frequency [Hz]")
ax.set_ylabel("Impact sound pressure level [dB]")
ax.set_title(f"L'nT,w = {res_imp.rating} dB  (CI={res_imp.ci:+d})")
ax.legend()
plt.show()
```

</details>

Feed `impact_insulation`'s `l_n_t` (or `l_n`) straight into
`weighted_impact_rating`; the rating and `CI` reproduce the ISO 717-2 Annex C
values (thirds `L'nT,w = 79`, `CI = −11`; octave `54`, `CI = 0`).

#### `impact_insulation()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `li` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Energy-average impact SPL (2D is averaged over positions) |
| `t2` | 1D array | s | > 0, one per band | Receiving-room reverberation time |
| `volume` | float, optional | m³ | > 0 | Receiving-room `V` (enables `L'n`) |
| `t0` | float | s | default `0.5` | Reference reverberation time `T0` |

#### `weighted_impact_rating()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `values_by_band` | 1D array | dB | 16 (thirds) or 5 (octaves) | Measured `Ln`, `L'n` or `L'nT` per band |
| `bands` | str or `None` | — | `'third-octave'` / `'octave'` / `None` | `None` infers from the count |

`impact_insulation()` returns an `ImpactInsulationResult` (`l_n_t`, `l_n` or
`None`); `weighted_impact_rating()` returns an `ImpactRatingResult` (`rating`,
`ci` integers, `unfavourable_sum` in dB).

### Field façade insulation (ISO 16283-3)

The same source/receiver logic reaches the building **façade**, but now the
source is *outdoors* — a loudspeaker at 45° or the road traffic itself. Rather
than a level difference across an internal partition, ISO 16283-3 references the
receiving-room level $L_2$ to the level **2 m in front of the façade**
$L_{1,2m}$, giving the level difference $D_{2m}$ and, exactly as in the airborne
case, its standardized and normalized forms:

$$
D_{2m} = L_{1,2m} - L_2, \quad
D_{2m,nT} = D_{2m} + 10 \log_{10}\frac{T}{T_0}, \quad
D_{2m,n} = D_{2m} - 10 \log_{10}\frac{A}{A_0},
$$

with $T_0 = 0.5$ s, $A_0 = 10$ m² and $A = 0.16\ V/T$ (dwellings). When the
microphone sits **on the test element** (surface level $L_{1,s}$) the *element*
method also yields an apparent sound reduction index, carrying a fixed
angle-of-incidence correction — $-1.5$ dB for the 45° loudspeaker method,
$-3$ dB for the all-angle road-traffic method:

$$
R'_{45°} = L_{1,s} - L_2 + 10 \log_{10}\frac{S}{A} - 1.5, \qquad
R'_{tr,s} = L_{1,s} - L_2 + 10 \log_{10}\frac{S}{A} - 3.
$$

The façade quantity is airborne, so its single-number rating uses the
**ISO 717-1** reference curve through `weighted_rating` unchanged (Annex F).

```python
import numpy as np
from phonometry import facade_insulation, weighted_rating

# Outdoor level 2 m in front of the façade, receiving-room level and T per
# one-third-octave band; surface_level is the microphone on the test element.
l1_2m = np.full(16, 75.0)                              # L1,2m outdoors
l2 = np.full(16, 33.0)                                 # receiving-room L2
t2 = np.full(16, 0.5)                                  # receiving-room T (s)

fac = facade_insulation(l1_2m, l2, t2, volume=50.0, area=11.5,
                        surface_level=np.full(16, 78.0), method="loudspeaker")
print(round(float(fac.d_2m[0]), 1))                    # 42.0  D2m = L1,2m - L2
print(round(float(fac.d_2m_nt[0]), 1))                 # 42.0  (= D2m since T = T0)
print(round(float(fac.d_2m_n[0]), 1))                  # 40.0  normalized to A0 = 10 m^2
print(round(float(fac.r_prime[0]), 1))                 # 42.1  R'45deg (loudspeaker, -1.5 dB)

# The road-traffic element method carries the -3 dB all-angle correction instead
tr = facade_insulation(l1_2m, l2, t2, volume=50.0, area=11.5,
                       surface_level=np.full(16, 78.0), method="road_traffic")
print(round(float(tr.r_prime[0]), 1))                  # 40.6  R'tr,s (traffic, -3 dB)

# The façade quantity is airborne: rate D2m,nT with the ISO 717-1 engine
print(weighted_rating(fac.d_2m_nt).rating)             # 42  Dls,2m,nT,w

fac.plot()   # per-band D2m,nT with D2m, D2m,n and R' overlaid (needs matplotlib)
```

`surface_level`, `area` and `volume` are all optional: with only `l1_2m`, `l2`
and `t2` the function returns `d_2m` and `d_2m_nt`; add `volume` for `d_2m_n`;
add `surface_level` **and** `area` **and** `volume` for `r_prime`. Positions are
energy-averaged with the surface-level formula (Clause 9.5.1); band levels are
assumed already corrected for background noise.

#### `facade_insulation()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `l1_2m` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Level 2 m in front of the façade `L1,2m` |
| `l2` | 1D or 2D array | dB | same band count | Receiving-room levels |
| `t2` | 1D array | s | > 0, one per band | Receiving-room reverberation time |
| `area` | float, optional | m² | > 0, with `surface_level`, `volume` | Test-element area `S` (enables `R'`) |
| `volume` | float, optional | m³ | > 0 | Receiving-room `V` (enables `D2m,n`; required for `R'`) |
| `surface_level` | 1D/2D array, optional | dB | same band count | Surface level `L1,s` on the element (enables `R'`) |
| `method` | str | — | `'loudspeaker'` (−1.5 dB) / `'road_traffic'` (−3 dB) | Angle-of-incidence correction of `R'` |
| `t0` | float | s | default `0.5` | Reference reverberation time `T0` |
| `frequencies` | 1D array, optional | Hz | — | Band centres carried on the result for plotting |

`facade_insulation()` returns a `FacadeInsulationResult` (`d_2m`, `d_2m_nt`,
`d_2m_n` or `None`, `r_prime` or `None`, `frequencies`); feed any 16-band façade
quantity to `weighted_rating` for its ISO 717-1 single number.

## 2. Laboratory measurement (ISO 10140)

Everything above is a **field** measurement (the primed quantities $R'$, $L'_n$):
the number a real building achieves, flanking transmission and all. To rate an
element on its own — a wall type, a floating floor, a window — you take it to a
qualified **laboratory** (ISO 10140), where suppressed flanking makes the
*direct* transmission the whole story. The formulas lose their primes: the
**sound reduction index** $R$ (not $R'$) and the **normalized impact level**
$L_n$ (not $L'_n$), with the receiving room's absorption area $A = 0.16\ V/T$
now a known property of the facility:

$$
R = L_1 - L_2 + 10 \log_{10}\frac{S}{A}, \qquad
L_n = L_i + 10 \log_{10}\frac{A}{A_0}, \quad A_0 = 10\ \text{m}^2.
$$

| | Field (ISO 16283) | Laboratory (ISO 10140) |
| :--- | :--- | :--- |
| Airborne | $R'$ apparent (with flanking) | $R$ direct (flanking suppressed) |
| Impact | $L'_n$ apparent | $L_n$ direct |
| Absorption area | measured in the room | property of the facility |

The single-number ratings reuse the very same ISO 717-1/2 engines
(`weighted_rating`, `weighted_impact_rating`) — an $R$ spectrum rates to $R_w$
exactly as an $R'$ spectrum rated to $R'_w$. Before forming the index the
receiving-room levels must be **corrected for background noise** (Clause 4.3):
the energy subtraction $10 \log_{10}(10^{L_{sb}/10} - 10^{L_b/10})$ applies for a
6–15 dB signal-to-background margin, a fixed 1.3 dB correction (the *limit of
measurement*) at or below 6 dB, and no correction at or above 15 dB.

```python
import numpy as np
from phonometry import (lab_airborne_insulation, lab_impact_insulation,
                        background_correction)

# Source/receiving levels and receiving-room T over the 16 one-third-octave
# bands; S is the free test-opening area, V the receiving-room volume.
l1 = np.full(16, 80.0)
l2 = np.full(16, 40.0)
t2 = np.full(16, 0.5)
lab = lab_airborne_insulation(l1, l2, t2, area=10.0, volume=50.0)
print(round(float(lab.r[0]), 1))              # 38.0  R = L1 - L2 + 10 lg(S/A)
print(round(float(lab.absorption[0]), 1))     # 16.0  A = 0.16 V / T (m^2)
print(lab.rating.rating, lab.rating.c, lab.rating.ctr)   # 38 0 0  ->  Rw(C;Ctr)

# Impact: the tapping-machine level Li normalized to A0 = 10 m^2 gives Ln
li = np.array([62.1, 63.2, 63.5, 66.2, 68.5, 70.0, 71.7, 73.1,
               73.8, 73.5, 73.8, 73.3, 73.1, 73.0, 72.4, 71.2])
imp = lab_impact_insulation(li, t2, volume=50.0)
print(round(float(imp.l_n[0]), 1))            # 64.1  Ln = Li + 10 lg(A/A0)
print(imp.rating.rating, imp.rating.ci)       # 81 -11  ->  Ln,w(CI)

# Background correction: margins 6 / 1 / 20 dB -> capped / capped / unchanged
corrected = background_correction([30.0, 33.0, 50.0], [24.0, 32.0, 30.0])
print(np.round(corrected, 1))                 # [28.7 31.7 50.0]  (1.3 dB cap twice)

lab.rating.plot()   # measured R vs shifted ISO 717-1 reference (needs matplotlib)
```

A margin at or below 6 dB emits a `LabInsulationWarning` and flags the band as
the limit of measurement; catch it with `warnings.simplefilter("error",
LabInsulationWarning)`. The automatic rating is formed only when exactly 16
one-third-octave or 5 octave values are supplied (`rating` is `None` otherwise).

### `lab_airborne_insulation()` / `lab_impact_insulation()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `l1` / `l2` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Source / receiving levels (airborne) |
| `li` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Impact SPL from the tapping machine (impact) |
| `t2` | 1D array | s | > 0, one per band | Receiving-room reverberation time |
| `area` | float | m² | > 0 | Free test-opening area `S` (airborne only) |
| `volume` | float | m³ | > 0 | Receiving-room volume `V` |

`lab_airborne_insulation()` returns a `LabAirborneInsulationResult` (`r`,
`absorption`, `rating`); `lab_impact_insulation()` a
`LabImpactInsulationResult` (`l_n`, `absorption`, `rating`);
`background_correction(signal_and_background, background)` returns the corrected
levels directly.

## 3. Predicting performance (EN 12354)

A laboratory rating describes an element in isolation, yet the sound a building
actually transmits also travels *around* the partition — along the floor, up the
façade, through the flanking walls — re-radiating into the receiving room. This
**flanking transmission** is the whole difference between the laboratory $R$ and
the field $R'$. EN 12354 predicts the in-situ apparent rating from the
laboratory ratings of the elements plus the vibration transmission of their
junctions.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths.svg" alt="The direct path Dd through the separating element and the three flanking paths Ff, Df and Fd across each junction between a flanking element and the separating element" width="92%"></picture>

Each junction between a flanking element and the separating element carries
three paths — $Ff$ (flanking→flanking), $Df$ (direct→flanking) and $Fd$
(flanking→direct) — alongside the single direct path $Dd$. The **simplified
single-number model** combines them energetically (Formula 26):

$$
R'_w = -10 \log_{10}\Big[ 10^{-R_{Dd,w}/10}
      + \sum 10^{-R_{Ff,w}/10} + \sum 10^{-R_{Df,w}/10}
      + \sum 10^{-R_{Fd,w}/10} \Big],
$$

with the direct path $R_{Dd,w} = R_{s,w} + \Delta R_{Dd,w}$ (Formula 27) and each
flanking path (Formula 28a)

$$
R_{ij,w} = \tfrac{R_{i,w} + R_{j,w}}{2} + \Delta R_{ij,w} + K_{ij}
         + 10 \log_{10}\frac{S_s}{l_0\ l_f},
$$

where $l_0 = 1$ m is the reference coupling length, $l_f$ the junction coupling
length and $K_{ij}$ the junction's **vibration reduction index** (Annex E,
empirical in the mass ratio $M = \log_{10}(m'_{\perp,i}/m'_i)$).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo.svg" alt="Per-path sound reduction indices for the EN 12354-1 Annex H.3 example and each path's share of the transmitted energy, showing the direct path dominating at R'w = 52 dB" width="80%"></picture>

```python
import numpy as np
from phonometry import (junction_vibration_reduction, flanking_element,
                        predicted_airborne_insulation)

# EN 12354-1 Annex H.3: a separating wall Rs,w = 57 dB, area Ss = 11.5 m², with
# four flanking elements. The simplified model reads each junction's Kij at
# 500 Hz from the mass ratio m'perp / m' (Annex E) — here the floor's rigid
# cross-junction (the mass ratio is itself rounded, hence 12.5 vs Annex 12.4):
print(round(junction_vibration_reduction("rigid_cross", "through", 1.61), 1))  # 12.5  KFf
print(round(junction_vibration_reduction("rigid_cross", "corner",  1.61), 1))  #  8.9  KFd = KDf

# Build each element's three flanking paths (Ff, Df, Fd) from the Annex H
# tabulated Kij, then combine the direct path Dd energetically (Formula 26).
elements = [   # (name, Rw, KFf, KFd = KDf, coupling length lf)
    ("floor",    49, 12.4,  8.9, 4.50),
    ("ceiling",  46, 14.4,  9.2, 4.50),
    ("facade",   42, 12.6,  6.7, 2.55),
    ("int-wall", 33, 33.5, 15.7, 2.55),
]
paths = []
for name, rw, k_ff, k_fd, lf in elements:
    paths += flanking_element(label=name, r_flanking=rw, r_separating=57,
                              k_ff=k_ff, k_fd=k_fd, k_df=k_fd,
                              separating_area=11.5, coupling_length=lf)

res = predicted_airborne_insulation(r_direct=57.0, flanking_paths=paths)
print(round(res.r_prime_w, 1))                          # 52.2  ->  R'w = 52 dB
print(res.dominant.label, round(res.dominant.fraction, 2))   # Dd 0.33 (direct dominates)
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# Uses `paths` and `res` from the snippet above.
# Per-path sound reduction index and each path's share of the transmitted
# energy for the Annex H.3 result computed above.
labels = [p.label for p in res.paths]
r_w = [p.r_w for p in res.paths]
frac = [100.0 * p.fraction for p in res.paths]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
ax1.bar(labels, r_w, color="tab:blue")
ax1.axhline(res.r_prime_w, ls="--", color="k", label=f"R'w = {res.r_prime_w:.1f} dB")
ax1.set_ylabel("Path Rij,w [dB]"); ax1.legend()
ax2.bar(labels, frac, color="tab:orange")
ax2.set_ylabel("Energy share [%]"); ax2.set_xlabel("Transmission path")
for ax in (ax1, ax2):
    ax.tick_params(axis="x", rotation=45)
fig.suptitle("EN 12354-1 Annex H.3 — flanking transmission")
fig.tight_layout()
plt.show()
```

</details>

Every added flanking path strictly lowers $R'_w$ below the direct $R_{Dd,w} = 57$;
`res.paths` exposes each path's share of the transmitted energy so the dominant
path is visible. `flanking_element` is a convenience that builds one junction's
three paths at once; the single-path constructor behind it, `flanking_path`,
builds one `Ff`, `Df` or `Fd` path at a time (Formula 28a). Clause 4.4.2 also
enforces a floor $K_{ij} \ge K_{ij,\min}$ from the junction geometry — compute
it with `junction_min_vibration_reduction` and pass it to
`flanking_path(..., kij_min=...)`, which raises a below-floor $K_{ij}$ to the
minimum:

```python
from phonometry import junction_min_vibration_reduction
# Kij,min = 10 lg[lf·l0·(1/Si + 1/Sj)]; large elements give a low (here negative)
# floor, so a realistic tabulated Kij is rarely clamped.
print(round(junction_min_vibration_reduction(coupling_length=4.5,
                                             s_i=11.5, s_j=11.5), 1))     # -1.1
```

The impact counterpart (EN 12354-2, Formula 21) is a direct subtraction:
$L'_{n,w} = L_{n,w,eq} - \Delta L_w + K$, with the bare-floor equivalent level
$L_{n,w,eq} = 164 - 35 \log_{10}(m'/m'_0)$ (Annex B), the covering improvement
$\Delta L_w$ (ISO 717-2) and the flanking correction $K$ from Table 1.

```python
from phonometry import (equivalent_impact_level, impact_flanking_correction,
                        predicted_impact_insulation, standardized_impact_level)

# EN 12354-2 Annex E.3: a 0.14 m concrete floor (m' = 322 kg/m²) with a floating
# floor (ΔLw = 33 dB), rooms one above the other, mean flanking mass 145 kg/m².
ln_eq = equivalent_impact_level(322.0)                   # 164 - 35 lg(m')
k = impact_flanking_correction(322.0, 145.0)             # Table 1 (sep 322, flk 145)
imp = predicted_impact_insulation(ln_w_eq=ln_eq, delta_l_w=33.0, k_correction=k)
print(round(ln_eq, 1), k, round(imp.l_prime_n_w, 1))     # 76.2 2 45.2  ->  L'n,w = 45 dB
print(round(standardized_impact_level(imp.l_prime_n_w, 50.0), 1))   # 43.0  L'nT,w
```

### `junction_vibration_reduction()` / `flanking_element()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `junction_type` | str | — | `'rigid_cross'` / `'rigid_t'` / `'flexible_t'` / `'lightweight_facade'` | Junction geometry (Annex E) |
| `path` | str | — | `'through'` (K13) / `'corner'` (K12 = K23) | Path branch |
| `mass_ratio` | float | — | > 0 | `m'⊥,i / m'i` (Formula E.2) |
| `frequency` | float | Hz | default `500` | Only `flexible_t` is frequency-dependent |
| `r_flanking` / `r_separating` | float | dB | — | Weighted indices of the flanking / separating element |
| `k_ff` / `k_fd` / `k_df` | float | dB | — | Junction `Kij` for the three paths |
| `separating_area` | float | m² | > 0 | Separating-element area `Ss` |
| `coupling_length` | float | m | > 0 | Junction coupling length `lf` |
| `delta_r_ff` / `delta_r_fd` / `delta_r_df` | float | dB | default `0` | Lining improvements per path |

### `flanking_path()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `label` | str | — | — | Display name of the path |
| `kind` | str | — | `'Ff'` / `'Df'` / `'Fd'` | Which flanking branch the path is |
| `r_source` / `r_receive` | float | dB | — | Weighted indices of the source-side / receive-side elements |
| `k_ij` | float | dB | — | Junction vibration-reduction index for this path |
| `separating_area` | float | m² | > 0 | Separating-element area `Ss` |
| `coupling_length` | float | m | > 0 | Junction coupling length `lf` |
| `delta_r` | float | dB | default `0` | Lining improvement on this path |
| `kij_min` | float | dB | default `None` | When given, `k_ij` is floored at this Formula E.4 minimum |

`predicted_airborne_insulation()` returns an `AirbornePredictionResult`
(`r_prime_w`, `r_direct_w`, `paths` of `PathContribution`, `dominant`);
`predicted_impact_insulation()` an `ImpactPredictionResult` (`l_prime_n_w`,
`ln_w_eq`, `delta_l_w`, `k_correction`). The simplified model carries a reported
standard deviation of about 2 dB (Clause 5).

### Façade insulation & radiated power (EN 12354-3 / -4)

Parts 3 and 4 predict the two directions across the building envelope, both from
the same energy summation of the element **transmission factors**
$\tau = 10^{-R/10}$, area-weighted by $S_i/S$ (a small element or air path enters
through its element-normalized level difference $D_{n,e}$ with the reference area
$A_0 = 10\ \text{m}^2$):

$$
R' = -10 \log_{10}\!\Big( \sum_i \tfrac{S_i}{S}\,10^{-R_i/10}
                          + \sum_k \tfrac{A_0}{S}\,10^{-D_{n,e,k}/10} \Big).
$$

**Part 3 — outdoor → indoor.** From $R'$ (Formula 10) follow the loudspeaker- and
traffic-referenced indices $R_{45} = R'+1$ and $R_{tr,s} = R'$, and the primary
output, the standardized level difference at 2 m (Formula 13)

$$
D_{2m,nT} = R' + \Delta L_{fs} + 10 \log_{10}\frac{V}{6\,T_0\,S}, \qquad T_0 = 0.5\ \text{s},
$$

with the façade-shape term $\Delta L_{fs}$ (Annex C; 0 dB for a flat reflecting
façade). Single-number ratings reuse EN ISO 717-1 (`weighted_rating`).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/facade_prediction_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/facade_prediction.svg" alt="Per-element partial sound reduction indices and the resulting façade apparent reduction R' and standardized level difference D2m,nT for the EN 12354-3 Annex F worked example, the air inlet limiting the low bands" width="80%"></picture>

```python
from phonometry import FacadeElement, facade_sound_reduction

# EN 12354-3 Annex F: an 11.3 m² façade (V = 50 m³, flat so ΔLfs = 0) of a double
# wall, a window, a small skylight and an acoustically-treated air inlet (a Dn,e
# element).
elements = [
    FacadeElement("wall",     area=6.0, r=[41, 46, 52, 58, 64]),   # octave 125-2000
    FacadeElement("window",   area=4.5, r=[23, 22, 30, 36, 37]),
    FacadeElement("skylight", area=0.5, r=[24, 27, 30, 33, 30]),
    FacadeElement("air inlet", dn_e=[28, 23, 25, 38, 44]),         # small element
]
fac = facade_sound_reduction(elements, area=11.3, volume=50.0,
                             frequencies=[125, 250, 500, 1000, 2000], bands="octave")
print(fac.r_tr_s_w, fac.c_tr, fac.d_2m_nt_w)   # 31 -3 33  (Rtr,s,w / Ctr / D2m,nT,w)
```

**Part 4 — indoor → outdoor.** The sound power level radiated by a segment
(Formula 2) is $L_W = L_{p,in} + C_d - R' + 10 \log_{10}(S/S_0)$ with $S_0 = 1$ m²
and the inside-field diffusivity term $C_d$ (Annex B; −6 dB ideal diffuse, −5 dB
average industrial). Openings are elements whose "R" is the silencer insertion
loss (a bare opening is 0 dB). The exterior level follows from the simplified
Annex E attenuation $A_{tot}$ of a finite radiating side, $L_p = L_W - A_{tot}$.

```python
from phonometry import (FacadeElement, radiated_sound_power,
                        outdoor_attenuation, outdoor_level)

# EN 12354-4 Annex G, side 1: a 10×20 m concrete wall segment with a 6×4 m
# industrial door, inside level Lp,in, Cd = -5 dB, R' capped at 40 dB (Annex G).
bands = [63, 125, 250, 500, 1000, 2000, 4000, 8000]
seg = radiated_sound_power(
    [FacadeElement("wall", area=176.0, r=[32, 36, 36, 33, 39, 49, 57, 63]),
     FacadeElement("door", area=24.0,  r=[21, 23, 28, 30, 30, 30, 30, 30])],
    lp_in=[70, 74, 76, 72, 70, 67, 62, 57], area=200.0, c_d=-5.0,
    r_prime_cap=40.0, octave_bands=bands)
print(round(seg.l_w[0], 1), round(seg.l_w[1], 1))     # 59.8 61.2  (LW at 63/125 Hz)

# Exterior level 5 m in front of the centre of the 60×10 m side (LWA = 62.9 dB(A)).
a_tot = outdoor_attenuation(width=60.0, height=10.0, distance=5.0)
print(round(a_tot, 1), round(outdoor_level(62.9, a_tot), 1))   # 26.3 36.6
```

> **Worked-example note.** The 2000 worked examples carry small internal rounding
> inconsistencies at the higher octave bands (Part 3's printed $R'$ disagrees with
> its own per-element partial indices at 1 k/2 k; Part 4's $R'$ rows above 500 Hz
> disagree with its Table G.2 inputs). The implementation is faithful to the
> formulas — it reproduces the low bands, every single-number rating and the whole
> Annex E propagation exactly.

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt

# Uses `fac` (the Part 3 result) and its band centres from the snippet above.
x = np.arange(5)
fig, ax = plt.subplots(figsize=(9, 5.5))
for name, rp in fac.element_r.items():
    ax.plot(x, rp, "--", alpha=0.6, marker=".", label=f"Rp — {name}")
ax.plot(x, fac.r_prime, "k-", lw=2.5, marker="o", label="R′ (façade)")
ax.plot(x, fac.d_2m_nt, lw=2, marker="s", label="D2m,nT")
ax.set_xticks(x); ax.set_xticklabels([125, 250, 500, 1000, 2000])
ax.set_xlabel("Frequency [Hz]"); ax.set_ylabel("Index / level difference [dB]")
ax.set_title("EN 12354-3 façade sound insulation (Annex F)")
ax.legend(ncol=2); ax.grid(alpha=0.4)
fig.tight_layout(); plt.show()
```

</details>

### `FacadeElement` / `facade_sound_reduction()` / `radiated_sound_power()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `FacadeElement.area` | float | m² | > 0 for `r` / `insertion_loss` | Element area $S_i$ (ignored for `dn_e`) |
| `FacadeElement.r` / `dn_e` / `insertion_loss` | float or seq | dB | give exactly one | Area element $R_i$ / small-element $D_{n,e}$ / opening insertion loss |
| `facade_sound_reduction(area)` | float | m² | > 0 | Total façade area $S$ |
| `facade_sound_reduction(volume)` | float | m³ | > 0 | Receiving-room volume $V$ (Formula 13) |
| `facade_sound_reduction(delta_l_fs)` | float | dB | default `0` | Façade-shape term $\Delta L_{fs}$ (Annex C) |
| `radiated_sound_power(lp_in)` | float or seq | dB | — | Inside level $L_{p,in}$ per band |
| `radiated_sound_power(c_d)` | float | dB | default `-6` | Diffusivity term $C_d$ (Annex B) |
| `radiated_sound_power(r_prime_cap)` | float | dB | default `40` (`None` off) | Field cap on $R'$ (Annex G) |
| `radiated_sound_power(octave_bands)` | seq of int | Hz | default `None` | Octave centres matching the bands; enables the A-weighted $L_{WA}$ |
| `facade_sound_reduction(frequencies)` | seq | Hz | default `None`; length = band count | Band centres carried on the result for plotting |
| `outdoor_attenuation(width, height, distance)` | float | m | > 0 | Finite radiating side and reception distance (Annex E) |
| `outdoor_level(l_w, attenuation)` | float or seq | dB | broadcast-compatible | Exterior $L_p$ from one or more sides (Formula E.1) |

`facade_sound_reduction()` returns a `FacadePredictionResult` (`r_prime`, `r_45`,
`r_tr_s`, `d_2m_nt`, `element_r`, and the `r_tr_s_w` / `d_2m_nt_w` / `c_tr` single
numbers); `radiated_sound_power()` a `RadiatedPowerResult` (`l_w`, `r_prime`,
`l_w_dba`). Both expose `.plot()`.

## 4. Measurement uncertainty (ISO 12999-1)

A rating without an uncertainty is only half a result. ISO 12999-1 does not
re-measure anything; it tabulates the **standard uncertainty** $u$ of every
sound-insulation quantity — derived from inter-laboratory tests — and prescribes
how to expand and combine it. Which standard deviation is $u$ depends on the
**measurement situation** (Clause 5.2):

| Situation | Meaning | Standard uncertainty $u$ |
| :--- | :--- | :--- |
| **A** | laboratory characterisation (ISO 10140) | reproducibility $\sigma_R$ |
| **B** | same location, different teams | in-situ $\sigma_{situ}$ |
| **C** | same location, same operator repeated | repeatability $\sigma_r$ |

The expanded uncertainty is $U = k\ u$ (Formula 2) with the coverage factor $k$
of Table 8. A two-sided interval $Y = y \pm U$ (Formula 3, $k = 1.96$ at 95 %)
*reports* a value; the **one-sided** factor ($k = 1.65$ at 95 %) *declares
conformity* with a requirement (Formulae 4/5).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso12999_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso12999.svg" alt="ISO 12999-1 uncertainty flow: standard uncertainty from the tables, reduced by repeated measurements and combined in quadrature, then expanded by the Table 8 coverage factor into a two-sided report or a one-sided conformity decision" width="82%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo.svg" alt="A weighted rating reported with its two-sided 95 % expanded uncertainty in situations A, B and C, the reproducibility uncertainty widest and the repeatability uncertainty narrowest" width="80%"></picture>

```python
from phonometry import (band_uncertainty, single_number_uncertainty,
                        uncertain_value, satisfies_lower_requirement)

# Situation B (same building, different teams) -> the in-situ standard deviation.
print(single_number_uncertainty("r_w", "B"))       # 0.9  dB  (Table 3)
u = band_uncertainty("airborne", "B")              # per-band u (Table 2)
print(len(u.frequencies), u.uncertainties[10])     # 21 1.1  (the 500 Hz band)

# Report R'w = 52 dB with a two-sided 95 % interval (k = 1.96, Table 8):
uv = uncertain_value(52.0, "rprime_w", "B")        # aliases resolve to r_w
print(uv.coverage_factor, round(uv.expanded_uncertainty, 1))    # 1.96 1.8
print(round(uv.lower, 1), round(uv.upper, 1))      # 50.2 53.8  ->  52 ± 1.8 dB

# Declaring conformity uses the ONE-sided factor (k = 1.65): does R'w provably
# clear a 50 dB requirement?
uc = uncertain_value(52.0, "rprime_w", "B", one_sided=True)
print(satisfies_lower_requirement(52.0, uc.expanded_uncertainty, 50.0))   # True
```

Impact quantities offer situations B/C only (Table 4, no 500 Hz band in the 2020
edition), and $\Delta L$ only situation A. Descriptors are case-insensitive with
aliases (`rprime_w`/`dnt_w`→`r_w`, `lprime_n_w`→`ln_w`); combine independent
components in quadrature with `combine_uncertainties`, and reduce by $m$
independent measurements with `reduce_by_independent_measurements` ($u/\sqrt{m}$).

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import uncertain_value

# The same R'w = 52 dB reported in each situation with its two-sided 95 % U.
situations = ["A", "B", "C"]
vals = [uncertain_value(52.0, "r_w", s) for s in situations]

fig, ax = plt.subplots(figsize=(7, 4))
ax.errorbar(situations, [v.value for v in vals],
            yerr=[v.expanded_uncertainty for v in vals],
            fmt="o", capsize=8, color="tab:blue")
for s, v in zip(situations, vals):
    ax.annotate(f"±{v.expanded_uncertainty:.1f}", (s, v.upper),
                textcoords="offset points", xytext=(8, 4))
ax.set_ylabel("R'w [dB]"); ax.set_xlabel("Measurement situation")
ax.set_title("R'w = 52 dB with 95 % expanded uncertainty (ISO 12999-1)")
fig.tight_layout()
plt.show()
```

</details>

### `band_uncertainty()` / `single_number_uncertainty()` / `uncertain_value()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `measurand` | str | — | `'airborne'` / `'impact'` / `'impact_reduction'` | Selects Table 2 / 4 / 6 |
| `quantity` | str | — | `'r_w'`, `'ln_w'`, `'delta_lw'` (+ aliases, `+c`/`+ctr` variants) | Single-number descriptor |
| `situation` | str | — | `'A'` / `'B'` / `'C'` | Measurement situation (Clause 5.2) |
| `value` | float | dB | — | Best estimate `y` to attach `U` to |
| `coverage` | float | — | default `0.95` | Confidence level (Table 8) |
| `one_sided` | bool | — | default `False` | One-sided factor for conformity checks |
| `upper_limit` | bool | — | default `False` | Select the σR95 upper limit (airborne, situation A) |

`band_uncertainty()` returns a `BandUncertainty` (`frequencies`,
`uncertainties`, `.to_arrays()`); `single_number_uncertainty()` a float;
`uncertain_value()` an `UncertainValue` (`value`, `standard_uncertainty`,
`coverage_factor`, `expanded_uncertainty`, `.lower`, `.upper`). The read-only
`COVERAGE_FACTORS` mapping exposes Table 8 keyed by `(confidence, one_sided)`.

## 5. Sound insulation by intensity (ISO 15186)

The laboratory method of §2 reads the transmitted power *indirectly*, from the
receiving-room level and its absorption area — which breaks down when flanking
paths leak power the room integrates in anyway. The **sound-intensity** method
(ISO 15186) sidesteps that: an intensity probe scans a measurement surface that
encloses the specimen and measures the radiated power *directly*, so only the
element under test contributes. It is the tool of choice when flanking is high
(ISO 15186-1:2000, Clause 1). From the source-room level $L_{p1}$ and the
average normal intensity level $L_{In}$ over the surface (area $S_m$), for a
specimen of area $S$,

$$
R_I = L_{p1} - 6 - \left[ L_{In} + 10 \log_{10}\frac{S_m}{S} \right],
$$

where the $6$ dB is the diffuse-field offset between the sound pressure level
and the incident intensity level. The same formula gives the apparent index
$R'_I$ in the field (ISO 15186-2). Because the intensity method slightly
*underestimates* the power radiated into a real receiving room, a **modified
index** $R_{I,M} = R_I + K_c$ reproduces the ISO 10140-2 pressure result; the
adaptation term $K_c$ (Annex B) is $10 \log_{10}(1 + S_{b2}\lambda/8V_2)$ for a
well-defined room, or the room-independent $10 \log_{10}(1 + 61.4/f)$. For small
elements the **element normalized level difference** replaces $10\lg(S_m/S)$
with $10\lg(S_m/A_0) + 10\lg N$ ($A_0 = 10\ \text{m}^2$, $N$ element units).

```python
import numpy as np
from phonometry import (intensity_sound_reduction, adaptation_term_kc,
                        surface_pressure_intensity_indicator)

# Source-room level Lp1 and the average normal intensity level LIn over the
# measurement surface (Sm), for a specimen of area S; 16 one-third-octave bands.
lp1 = np.full(16, 85.0)
l_in = np.full(16, 40.0)
freqs = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
         1000, 1250, 1600, 2000, 2500, 3150]   # nominal 1/3-octave centres
kc = adaptation_term_kc(freqs)                  # Annex B (B.2)
res = intensity_sound_reduction(lp1, l_in, measurement_area=12.0, area=10.0, kc=kc)
print(round(float(res.r_i[0]), 2))          # 38.21  RI = Lp1 - 6 - [LIn + 10 lg(Sm/S)]
print(round(float(res.r_i_modified[0]), 2)) # 40.29  RI,M = RI + Kc
print(res.rating.rating)                     # 38  ->  RI,w (ISO 717-1 engine)

# Qualify the measurement surface: FpI = Lp - LIn must stay < 10 dB (< 6 dB when
# the receiving side is absorbing); the probe's residual index must exceed FpI+10.
fpi = surface_pressure_intensity_indicator(np.full(16, 46.0), l_in)
print(round(float(fpi[0]), 1))               # 6.0

res.plot()   # measured RI vs shifted ISO 717-1 reference (needs matplotlib)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_insulation_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_insulation.svg" alt="Intensity sound reduction index RI and the Kc-modified index RI,M across the one-third-octave bands, with the Annex B adaptation lift shaded between the two curves" width="80%"></picture>

*The modified index $R_{I,M} = R_I + K_c$ lifts $R_I$ — most at the low bands,
where $K_c$ is largest — so an intensity measurement reproduces the ISO 10140-2
pressure result. The automatic rating is formed only for exactly 16
one-third-octave or 5 octave values (`rating`/`rating_modified` are `None`
otherwise). Subareas scanned separately are combined first with
`combine_subareas` (Formulas (11)-(12)).*

### `intensity_sound_reduction()` / `adaptation_term_kc()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `lp1` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Source-room sound pressure level |
| `l_in` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Normal intensity level over the surface |
| `measurement_area` | float | m² | > 0 | Measurement-surface area `Sm` |
| `area` | float | m² | > 0 | Specimen area `S` |
| `kc` | 1D array | dB | one per band / `None` | Adaptation term for the modified index |
| `freq` | 1D array | Hz | > 0 | Midband frequencies (`adaptation_term_kc`) |
| `boundary_area` / `volume` | float | m² / m³ | > 0, both or neither | Room `Sb2` / `V2` for Formula (B.1) |

`intensity_sound_reduction()` returns an `IntensityReductionResult` (`r_i`,
`r_i_modified`, `rating`, `rating_modified`);
`intensity_element_normalized_difference()` an
`IntensityElementNormalizedResult` (`d_i_n_e`, `rating`);
`surface_pressure_intensity_indicator()` and `combine_subareas()` return arrays.

## 6. Field survey method (ISO 10052)

The engineering methods above buy accuracy with effort — swept microphones,
per-band reverberation times, careful background correction. For a quick check
in a dwelling, ISO 10052 defines a **survey (control) method**: octave bands, a
hand-held meter, and a single quantity — the **reverberation index**
`k = 10 lg(T/T0)` (`T0 = 0.5 s`) — to carry the receiving-room correction. Every
survey quantity is then just an addition of `k`: the standardized level
difference `DnT = D + k`, the normalized `Dn = D + k + 10 lg(A0 T0 / (0.16 V))`,
the apparent `R' = D + k + 10 lg(S T0 / (0.16 V))` (using `V/7.5` for `S` where
that is larger), and, for impacts and façades, `L'nT = Li - k` and
`D2m,nT = D2m + k`. The clause references follow ISO 10052:2021; the formulas
and the reverberation-index table are identical in the harmonized
EN ISO 10052:2004+A1:2010.

The reverberation index is either **measured** — feed the reverberation time to
`reverberation_index(T)` — or, in a control survey, **estimated** from the room
type and volume with `estimate_reverberation_index(V, room)` (Table 4:
furnished `"kitchen"` / `"bathroom"` / `"furnished"`, or the unfurnished
construction classes `"a"`–`"h"` and the mixed `"a+e"`…`"d+h"`). A fourth
quantity unique to this method is **service-equipment noise** `LXY` — the
energy average of three A- or C-weighted positions.

```python
import numpy as np
from phonometry import (reverberation_index, estimate_reverberation_index,
                        survey_airborne_insulation, survey_service_equipment_level)

# Octave-band levels (125-2000 Hz) and the measured receiving-room T.
l1 = np.array([88.0, 90.0, 92.0, 92.0, 90.0])
l2 = np.array([55.0, 51.0, 47.0, 41.0, 35.0])
k = reverberation_index([0.70, 0.60, 0.50, 0.45, 0.40])   # k = 10 lg(T/0.5)
res = survey_airborne_insulation(l1, l2, k, volume=50.0, area=12.0)
print(np.round(res.d_nt, 1))          # [34.5 39.8 45.  50.5 54. ]  DnT = D + k
print(res.rating.rating, res.rating.c)        # 49 -1  ->  DnT,w (C)
print(res.r_prime_rating.rating)               # 48  ->  R'w

# No reverberation time measured? Estimate k from Table 4 (heavy walls, hard
# floor, 35-60 m3 -> class "g").
k_est = estimate_reverberation_index(50.0, "g")
print(k_est)                                   # [4.5 5.  5.5 5.5 5.5]

# Service-equipment noise: energy average of three A-weighted positions.
se = survey_service_equipment_level([35.0, 30.0, 32.0], 3.0, volume=50.0)
print(round(float(se.l_xy), 1), round(float(se.l_xy_nt), 1))   # 32.8 29.8

res.plot()   # DnT vs shifted ISO 717-1 reference (needs matplotlib)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/survey_insulation_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/survey_insulation.svg" alt="Survey-method airborne insulation: the raw level difference D and the standardized DnT across the five octave bands, with the reverberation-index correction k shaded between them" width="80%"></picture>

*The reverberation index `k = 10 lg(T/T0)` shifts the raw level difference `D`
into the standardized `DnT` — up where the room is live (`T > T0`), down where
it is dead. The automatic rating is formed only for exactly 5 octave (or 16
one-third-octave) values.*

### `survey_airborne_insulation()` and friends — parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `l1` / `l2` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Source / receiving (or outdoor `l1_2m`) levels |
| `li` | 1D or 2D array | dB | one/band, or `(positions, bands)` | Impact levels (energy-averaged over positions) |
| `reverberation_index` | scalar or 1D array | dB | one per band | `k` from `reverberation_index` or `estimate_reverberation_index`; `survey_service_equipment_level()` also accepts a scalar `k` |
| `volume` | float | m³ | > 0 | Receiving-room `V` (for `Dn` / `L'n` / `R'` / normalized) |
| `area` | float | m² | > 0 | Common-partition `S` (airborne `R'`; `V/7.5` rule applied) |
| `measurements` | array | dB | exactly 3 | Service-equipment positions (`survey_service_equipment_level`) |
| `room` | str | — | `"kitchen"`/`"bathroom"`/`"furnished"`/`"a"`–`"h"`/`"a+e"`… | `estimate_reverberation_index` room class (Table 4) |

`survey_airborne_insulation()` returns a `SurveyAirborneResult` (`d`, `d_nt`,
`d_n`, `r_prime`, `rating`, `r_prime_rating`); `survey_impact_insulation()` a
`SurveyImpactResult` (`l_i`, `l_nt`, `l_n`, `rating`);
`survey_facade_insulation()` a `SurveyFacadeResult`;
`survey_service_equipment_level()` a `SurveyServiceEquipmentResult` (`l_xy`,
`l_xy_nt`, `l_xy_n`).

## 7. Floor-covering impact improvement (ISO 16251-1)

ISO 16251-1:2014 is a laboratory method for the **improvement of impact sound
insulation** $\Delta L$ of a soft, locally-reacting floor covering (carpet, PVC,
linoleum). The two ISO 10140 rooms are replaced by a small softly-supported
concrete plate; a standard tapping machine excites it and the structure-borne
**acceleration level** on the underside is measured with and without the
covering. For locally-reacting coverings that acceleration-level difference
equals the ISO 10140 impact sound reduction.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/floor_covering_improvement_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/floor_covering_improvement.svg" alt="ISO 16251-1 floor-covering impact sound improvement: the improvement delta-L of a soft carpet rising with frequency across one-third-octave bands from 100 Hz to 3150 Hz, with the shaded improvement area and the weighted single-number delta-Lw annotated" width="80%"></picture>

**Acceleration level (Formula (1)).** $L_a = 10\lg(\langle a^2\rangle / a_0^2)$ dB,
reference $a_0 = 10^{-6}\ \text{m/s}^2$. **Background correction (Formula (2))**
follows the ISO 10140 three-branch rule (unchanged ≥ 15 dB; energy subtraction
for 6 ≤ margin < 15 dB; the 1.3 dB limit below 6 dB, flagged as $> \Delta L$).
The improvement is the position-averaged difference
$\Delta L = L_0 - L_1$ (Formulae (3)/(4)); octaves follow
$\Delta L_\text{oct} = -10\lg[\tfrac{1}{3}\sum 10^{-\Delta L_n/10}]$ (Formula (5)).

**Weighted improvement.** $\Delta L_w$ is the ISO 717-2 weighted reduction: the
improvement is applied to the heavyweight **reference floor** $L_{n,r,0}$
(ISO 717-2 Table 4), $L_{n,r} = L_{n,r,0} - \Delta L$, and
$\Delta L_w = 78 - L_{n,r,w}$ — computed by `weighted_impact_improvement()`, which
reuses the verified ISO 717-2 rating engine.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import impact_improvement

freqs = [100, 125, 160, 200, 250, 315, 400, 500,
         630, 800, 1000, 1250, 1600, 2000, 2500, 3150]
bare = np.full(16, 78.0)                       # bare-plate acceleration level
covering = bare - np.array([0, 0, 1, 2, 4, 7, 11, 15,
                            18, 21, 23, 25, 27, 28, 29, 30])
res = impact_improvement(bare, covering, freqs)
print(res.delta_lw)   # weighted improvement delta-Lw (ISO 717-2)
res.plot()
plt.show()
```
</details>

```python
from phonometry import impact_improvement, weighted_impact_improvement

# delta-Lw straight from an improvement spectrum (16 one-third-octave bands):
delta_l = [0, 0, 1, 2, 4, 7, 11, 15, 18, 21, 23, 25, 27, 28, 29, 30]
print(weighted_impact_improvement(delta_l))    # e.g. 19 dB

# From the measured bare/covered acceleration levels, with a background trace:
res = impact_improvement(bare_levels, covered_levels, freqs, background=bg)
res.improvement       # delta-L per band
res.delta_lw          # weighted single number (None off the 16 rating bands)
res.limited           # bands at the 1.3 dB limit of measurement (> delta-L)
res.octave_bands()    # (octave freqs, delta-L_oct) via Formula (5)
```

---

## 8. Laboratory flanking transmission (ISO 10848)

ISO 10848:2006/2010 is the laboratory method that **measures** the junction
**vibration reduction index** $K_{ij}$ that the EN 12354 prediction of §3 takes
as an input, together with the overall flanking descriptors $D_{n,f}$
(airborne) and $L_{n,f}$ (impact). It is the measurement counterpart of the
empirical `junction_vibration_reduction()` of §3.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/flanking_transmission_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/flanking_transmission.svg" alt="ISO 10848 junction vibration reduction index Kij rising across one-third-octave bands from 100 Hz to 5000 Hz for a rigid T-junction of two heavy walls, with the single-number mean Kij over 200-1250 Hz drawn as a dashed line" width="80%"></picture>

**Vibration reduction index (Formula (13)).**
$K_{ij} = \overline{D}_{v,ij} + 10\lg\!\big(l_{ij} / \sqrt{a_i a_j}\big)$ dB, from
the direction-averaged velocity level difference
$\overline{D}_{v,ij} = \tfrac{1}{2}(D_{v,ij} + D_{v,ji})$ (Formula (11), which
makes $K_{ij}$ symmetric), the common-edge junction length $l_{ij}$ and the
**equivalent absorption lengths** $a_j = 2.2\pi^2 S_j /(T_{s,j} c_0)\sqrt{f_\text{ref}/f}$
(Formula (12), $f_\text{ref} = 1000$ Hz). For lightweight well-damped elements
$a_j = S_j / l_0$ ($l_0 = 1$ m) and Formula (13) reduces to the simplified
Formula (14). The related **total loss factor** is $\eta = 2.2/(f T_s)$.

**Overall descriptors.** $D_{n,f} = L_1 - L_2 - 10\lg(A/A_0)$ (Formula (4),
airborne) and $L_{n,f} = L_2 + 10\lg(A/A_0)$ (Formula (5), tapping machine),
$A_0 = 10\ \text{m}^2$; their $D_{n,f,w}$ / $L_{n,f,w}$ single numbers reuse the
ISO 717 rating engines. The single-number $\overline{K}_{ij}$ is the arithmetic
mean over 200–1250 Hz (Annex A).

**Validity.** $K_{ij}$ rests on a statistical-energy-analysis simplification:
`strong_coupling_satisfied()` checks the Formula (15) inequality, and — for the
heavy junctions of Part 4 — `modal_density()`, `band_mode_count()` and
`modal_overlap_factor()` (Formulae (5)/(4)/(6)) flag the bands where the mode
count is too low for $K_{ij}$ to be reliable. Because ISO 10848 contains no
worked numeric example, conformance is anchored on closed-form identities
(simplified $K_{ij}$, $a_j$ at $f_\text{ref}$, $\eta$).

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import vibration_reduction_index

freqs = [100, 125, 160, 200, 250, 315, 400, 500, 630,
         800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
# Direction-averaged velocity level difference of a rigid T-junction (dB):
dv = np.array([4.5, 4.8, 5.2, 5.6, 6.0, 6.5, 7.0, 7.6, 8.1, 8.7,
               9.2, 9.8, 10.3, 10.9, 11.4, 11.9, 12.3, 12.7])
res = vibration_reduction_index(
    dv, junction_length=4.0, area_i=12.0, area_j=10.0, frequency=freqs,
    structural_reverberation_time_i=0.35, structural_reverberation_time_j=0.40,
)
print(res.single_number)   # mean Kij over 200-1250 Hz (Annex A)
res.plot()
plt.show()
```
</details>

```python
from phonometry import (
    direction_averaged_level_difference, vibration_reduction_index,
    normalized_flanking_level_difference, modal_overlap_factor,
)

# Kij from both excitation directions (symmetric via the direction average):
dbar = direction_averaged_level_difference(dv_ij, dv_ji)
res = vibration_reduction_index(dbar, lij, s_i, s_j, frequency=freqs,
                                structural_reverberation_time_i=ts_i,
                                structural_reverberation_time_j=ts_j)
res.k_ij           # Kij per band (Formula (13))
res.single_number  # mean Kij over 200-1250 Hz, or None without the band set
res.octave_bands() # Kij combined into octave bands

# Overall airborne flanking descriptor and a Part-4 modal-overlap validity check:
dnf = normalized_flanking_level_difference(l1, l2, absorption_area)
m = modal_overlap_factor(area, critical_freq, ts)   # M < 0.25 -> exclude band
```

---

**Standards.** ISO 16283-1:2014, ISO 16283-2 and ISO 16283-3:2016, *Acoustics —
Field measurement of sound insulation in buildings and of building elements* —
the level differences, normalisations and element methods of §1; ISO 717-1 and
ISO 717-2 — the reference-curve single-number ratings and the spectrum
adaptation terms C, Ctr and CI; ISO 10140-2:2010, ISO 10140-3:2010 and ISO 10140-4:2010 — the
laboratory R and Ln with the background-noise correction of §2; EN 12354-1:2000
and EN 12354-2:2000 — the simplified flanking-transmission predictions of §3
(Annex E junctions, worked examples H.3 and E.3); EN 12354-3:2000 and
EN 12354-4:2000 — the façade sound insulation and outdoor-radiation predictions
of §3 (Annex F and Annex G worked examples); ISO 12999-1:2020 — the
standard uncertainties per measurement situation and the coverage factors
of §4; its precision framework builds on ISO 5725 (context, not
implemented directly); ISO 15186-1:2000 and ISO 15186-2:2003 — the
sound-intensity sound reduction index $R_I$, its $K_c$-modified form and the
element normalized level difference of §5 (laboratory and field);
ISO 10052:2021 (harmonized as EN ISO 10052:2004+A1:2010) — the field survey
method of §6: the reverberation-index correction, the standardized/normalized
airborne, impact and façade quantities, and service-equipment noise;
ISO 16251-1:2014 — the small-mock-up laboratory method for the impact-sound
improvement $\Delta L$ of floor coverings of §7, with $\Delta L_w$ via the
ISO 717-2 reference floor; ISO 10848-1:2006, ISO 10848-2:2006, ISO 10848-3:2006
and ISO 10848-4:2010 — the laboratory measurement of flanking transmission of
§8: the vibration reduction index $K_{ij}$, the equivalent absorption length,
the normalized flanking descriptors $D_{n,f}$ / $L_{n,f}$ and the
modal-overlap validity checks that feed the EN 12354 prediction of §3.

## See also

- [Room Acoustics](room-acoustics.md) — the impulse response,
  room parameters and sound absorption that this guide's insulation chain builds on.
- [Levels](levels.md) — energy averaging and the level metrics behind
  source/receiving-room levels.
- [Filter Banks](filter-banks.md) — the IEC 61260 fractional-octave filters
  used for the insulation spectra.
- [Sound Power](sound-power.md) — the `LW` methods that share the
  absorption-area machinery of the receiving room.
- [Theory](theory.md) — the reference-curve derivation behind the
  weighted single-number ratings.

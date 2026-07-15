← [Documentation index](README.md)

# Laboratory Insulation Measurement

To rate a building element on its own (a wall type, a floating floor, a
window) you take it to a qualified laboratory, where suppressed flanking makes
the direct transmission the whole story. This page covers the laboratory
chain: the ISO 10140 sound reduction index and normalized impact level, the
sound-intensity alternative of ISO 15186, the small-mock-up floor-covering
improvement of ISO 16251-1 and the flanking-transmission measurement of
ISO 10848. Field measurement and ratings live in
[Field Insulation Measurement and Ratings](insulation-field.md), and the
prediction that consumes these laboratory ratings in
[Predicting Sound Insulation (EN 12354)](insulation-prediction.md).

## Laboratory measurement (ISO 10140)

An [ISO 16283 field measurement](insulation-field.md) yields the primed
quantities ($R'$, $L'_n$): the number a real building achieves, flanking
transmission and all. To rate an
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

## Sound insulation by intensity (ISO 15186)

The ISO 10140 laboratory method above reads the transmitted power *indirectly*, from the
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
`combine_subareas` (Formulas (11)-(12)); a subarea whose net energy flows back
towards the specimen enters with a negative area, applying the minus-sign rule
of Clause 6.4.6 while $S_m$ keeps the unsigned area sum.*

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

## Floor-covering impact improvement (ISO 16251-1)

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
reuses the verified ISO 717-2 rating engine. A clause 6.3 measurement spans 18
bands (100–5000 Hz, optionally extended to 50 Hz); the rating is formed on the
100–3150 Hz sub-range of whatever spectrum contains it. The statement of
results (clause 8 e)) also carries the spectrum adaptation term
$C_{I,\Delta} = C_{I,r,0} - C_{I,r}$ (ISO 717-2:2020 Formula (A.4)), exposed as
`ci_delta` on the result and standalone as
`impact_improvement_adaptation_term()`.

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
freqs = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
         1000, 1250, 1600, 2000, 2500, 3150]
bare_levels = [72, 73, 74, 74, 75, 75, 76, 76, 77, 77, 78, 78, 79, 79, 80, 80]
covered_levels = [b - d for b, d in zip(bare_levels, delta_l)]
bg = [40.0] * 16
res = impact_improvement(bare_levels, covered_levels, freqs, background=bg)
res.improvement       # delta-L per band
res.delta_lw          # weighted single number (rated on the 100-3150 Hz sub-range)
res.ci_delta          # spectrum adaptation term CI,delta (Formula (A.4))
res.limited           # bands at the 1.3 dB limit of measurement (> delta-L)
res.octave_bands()    # (octave freqs, delta-L_oct) via Formula (5)
```

## Laboratory flanking transmission (ISO 10848)

ISO 10848:2006/2010 is the laboratory method that **measures** the junction
**vibration reduction index** $K_{ij}$ that the [EN 12354 prediction](insulation-prediction.md) takes
as an input, together with the overall flanking descriptors $D_{n,f}$
(airborne) and $L_{n,f}$ (impact). It is the measurement counterpart of the
empirical `junction_vibration_reduction()` of that prediction.

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
mean over 200–1250 Hz for one-third-octave bands, or over 125–1000 Hz for
octave bands (Annex A).

**Validity.** $K_{ij}$ rests on a statistical-energy-analysis simplification:
`strong_coupling_satisfied()` checks the Formula (15) inequality, and — for the
heavy junctions of Part 4 — `modal_density()`, `band_mode_count()` and
`modal_overlap_factor()` (Formulae (5)/(4)/(6)) quantify where the mode count
is too low for $K_{ij}$ to be reliable. Pass the per-band modal overlap factor
to `vibration_reduction_index(..., modal_overlap=M)`: bands with $M < 0.25$
are flagged in `result.bracketed` and excluded from the single-number
$\overline{K}_{ij}$, as Part 4 Clause 9 requires. Because ISO 10848 contains no
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
import numpy as np
from phonometry import (
    direction_averaged_level_difference, vibration_reduction_index,
    normalized_flanking_level_difference, modal_overlap_factor,
)

freqs = [200, 250, 315, 400, 500, 630, 800, 1000, 1250]
lij, s_i, s_j = 4.0, 12.0, 10.0     # junction length (m), element areas (m^2)
ts = np.linspace(0.30, 0.10, 9)     # structural reverberation time Ts (s)
dv_ij = [5.6, 6.0, 6.5, 7.0, 7.6, 8.1, 8.7, 9.2, 9.8]    # element i excited (dB)
dv_ji = [6.4, 6.8, 7.3, 7.8, 8.4, 8.9, 9.5, 10.0, 10.6]  # element j excited (dB)

# Kij from both excitation directions (symmetric via the direction average):
dbar = direction_averaged_level_difference(dv_ij, dv_ji)
res = vibration_reduction_index(dbar, lij, s_i, s_j, frequency=freqs,
                                structural_reverberation_time_i=ts,
                                structural_reverberation_time_j=ts)
res.k_ij           # Kij per band (Formula (13))
res.single_number  # mean Kij over 200-1250 Hz, or None without the band set
res.octave_bands() # Kij in octave bands (its single number averages 125-1000 Hz)

# Overall airborne flanking descriptor and a Part-4 modal-overlap validity check:
dnf = normalized_flanking_level_difference(np.full(9, 75.0), np.full(9, 42.0),
                                           absorption_area=np.full(9, 12.0))
m = modal_overlap_factor(s_i, critical_frequency=85.0,
                         structural_reverberation_time=ts)
res_m = vibration_reduction_index(dbar, lij, s_i, s_j, frequency=freqs,
                                  modal_overlap=m)   # M < 0.25 bands bracketed
res_m.bracketed    # per-band flags; bracketed bands leave the single number
```

---

**Standards.** ISO 10140-2:2010, ISO 10140-3:2010 and ISO 10140-4:2010 — the
laboratory R and Ln with the background-noise correction; ISO 15186-1:2000 and
ISO 15186-2:2003 — the sound-intensity sound reduction index $R_I$, its
$K_c$-modified form and the element normalized level difference (laboratory
and field); ISO 16251-1:2014 — the small-mock-up laboratory method for the
impact-sound improvement $\Delta L$ of floor coverings, with $\Delta L_w$ via
the ISO 717-2 reference floor; ISO 10848-1:2006, ISO 10848-2:2006,
ISO 10848-3:2006 and ISO 10848-4:2010 — the laboratory measurement of flanking
transmission: the vibration reduction index $K_{ij}$, the equivalent
absorption length, the normalized flanking descriptors $D_{n,f}$ / $L_{n,f}$
and the modal-overlap validity checks that feed the EN 12354 prediction.

## See also

- [Field Insulation Measurement and Ratings](insulation-field.md):
  the in-building airborne, impact and façade measurements, their single-number
  ratings and their uncertainty.
- [Predicting Sound Insulation (EN 12354)](insulation-prediction.md):
  the flanking model that consumes the laboratory $R$, $L_n$ and $K_{ij}$.
- [Sound Power](sound-power.md) — the `LW` methods that share the
  absorption-area machinery of the receiving room.

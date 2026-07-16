← [Documentation index](README.md)

# Predicting Sound Insulation (EN 12354)

A laboratory rating describes an element in isolation; a building also
transmits sound along every flanking path. This page covers the EN 12354
prediction of in-situ performance from laboratory element data: the airborne
and impact flanking models of EN 12354-1/2 with their junction vibration
reduction indices, and the façade insulation and outdoor radiation of
EN 12354-3/4. The measured quantities the model is checked against live in
[Field Insulation Measurement and Ratings](insulation-field.md); the
laboratory inputs come from
[Laboratory Insulation Measurement](insulation-lab.md).

## Predicting performance (EN 12354)

A laboratory rating describes an element in isolation, yet the sound a building
actually transmits also travels *around* the partition — along the floor, up the
façade, through the flanking walls — re-radiating into the receiving room. This
**flanking transmission** is the whole difference between the laboratory $R$ and
the field $R'$. EN 12354 predicts the in-situ apparent rating from the
laboratory ratings of the elements plus the vibration transmission of their
junctions.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths.svg" alt="The direct path Dd through the separating element and the three flanking paths Ff, Df and Fd across each junction between a flanking element and the separating element" width="92%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_flanking_paths_dark.gif"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_flanking_paths.gif" alt="Animation: energy pulses leave the source room over the direct Dd path and the flanking Ff, Fd and Df paths, shrinking at each element and junction, and every path label lights up as its pulse re-radiates into the receiving room" width="640" height="360" loading="lazy"></picture>

[Watch the high-resolution video (WebM)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_flanking_paths.webm)

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
enforces a floor $K_{ij} \ge K_{ij,\min}$ from the junction geometry
(Formula 29). Pass the flanking-element area to
`flanking_element(..., flanking_area=...)` and the clamp is applied
automatically per path; or compute the floor yourself with
`junction_min_vibration_reduction` and pass it to
`flanking_path(..., kij_min=...)`, which raises a below-floor $K_{ij}$ to the
minimum:

```python
from phonometry import junction_min_vibration_reduction
# Kij,min = 10 lg[lf·l0·(1/Si + 1/Sj)]; large elements give a low (here negative)
# floor, so a realistic tabulated Kij is rarely clamped; but small, light
# elements can push it above the tabulated value (e.g. lf = 4 m, S = 1.5 m²
# gives 7.3 dB, over the 5 dB lightweight floor).
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

# Exact Formula (3): L'nT,w = L'n,w - 10 lg(0.032 V). Annex E.3's own rounding
# of the factor to 10 lg(V/30) sits 0.18 dB below; both give L'nT,w = 43 dB.
print(round(standardized_impact_level(imp.l_prime_n_w, 50.0), 1))   # 43.2  L'nT,w
```

The airborne counterpart of that closure is Formula (5b),
$D_{nT} = R' + 10\lg(0.32\,V/S_s)$, exposed as `standardized_level_difference`;
it closes the Annex H.3 example (`standardized_level_difference(52.2, 50.0,
11.5)` gives 53.6 dB, the printed $V/(3S)$ chain 53.8 dB, both rounding to
$D_{nT,w} = 54$ dB).

### `junction_vibration_reduction()` / `flanking_element()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `junction_type` | str | — | `'rigid_cross'` / `'rigid_t'` / `'flexible_t'` / `'lightweight_facade'` / `'lightweight_double_homogeneous'` / `'lightweight_double_coupled'` / `'corner'` / `'thickness_change'` | Junction geometry (Annex E.3-E.9) |
| `path` | str | — | `'through'` (K13) / `'corner'` (K12 = K23) / `'double_leaf'` (K24) | Path branch |
| `mass_ratio` | float | — | > 0 | `m'⊥,i / m'i` (Formula E.2) |
| `frequency` | float | Hz | default `500` | `flexible_t` and the E.7/E.8 double-leaf junctions are frequency-dependent |
| `r_flanking` / `r_separating` | float | dB | — | Weighted indices of the flanking / separating element |
| `k_ff` / `k_fd` / `k_df` | float | dB | — | Junction `Kij` for the three paths |
| `separating_area` | float | m² | > 0 | Separating-element area `Ss` |
| `coupling_length` | float | m | > 0 | Junction coupling length `lf` |
| `delta_r_ff` / `delta_r_fd` / `delta_r_df` | float | dB | default `0` | Lining improvements per path |
| `flanking_area` | float | m² | default `None` | Flanking-element area `SF`; enables the automatic `Kij,min` clamp (Clause 4.4.2 / Formula 29) |

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
| `kij_min` | float | dB | default `None` | When given, `k_ij` is floored at this Formula (29) minimum |

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
façade; `facade_shape_level_difference` looks it up from the Figure C.2 table
for galleries, balconies and terraces, interpolating over the underside
absorption $\alpha_w$). Single-number ratings reuse EN ISO 717-1
(`weighted_rating`).

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
# industrial door, inside level Lp,in, Cd = -5 dB. The 40 dB cap on R' is an
# Annex G example footnote (field leaks), not part of Formula (2)/(3): pass it
# explicitly to reproduce Annex G; by default no cap is applied.
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
| `facade_sound_reduction(delta_l_fs)` | float | dB | default `0` | Façade-shape term $\Delta L_{fs}$ (Annex C; look it up with `facade_shape_level_difference`) |
| `radiated_sound_power(lp_in)` | float or seq | dB | — | Inside level $L_{p,in}$ per band |
| `radiated_sound_power(c_d)` | float | dB | default `-6` | Diffusivity term $C_d$ (Annex B) |
| `radiated_sound_power(r_prime_cap)` | float | dB | default `None` (off) | Optional field cap on $R'$, an Annex G example footnote (it uses 40 dB), not part of Formula (2)/(3) |
| `radiated_sound_power(octave_bands)` | seq of int | Hz | default `None` | Octave centres matching the bands; enables the A-weighted $L_{WA}$ |
| `facade_sound_reduction(frequencies)` | seq | Hz | default `None`; length = band count | Band centres carried on the result for plotting |
| `outdoor_attenuation(width, height, distance)` | float | m | > 0 | Finite radiating side and reception distance (Annex E) |
| `outdoor_level(l_w, attenuation)` | float or seq | dB | broadcast-compatible | Exterior $L_p$ from one or more sides (Formula E.1) |

`facade_sound_reduction()` returns a `FacadePredictionResult` (`r_prime`, `r_45`,
`r_tr_s`, `d_2m_nt`, `element_r`, and the `r_tr_s_w` / `d_2m_nt_w` / `c_tr` single
numbers); `radiated_sound_power()` a `RadiatedPowerResult` (`l_w`, `r_prime`,
`l_w_dba`). Both expose `.plot()`.

---

**Standards.** EN 12354-1:2000 and EN 12354-2:2000 — the simplified
flanking-transmission predictions (Annex E junctions, worked examples H.3 and
E.3); EN 12354-3:2000 and EN 12354-4:2000 — the façade sound insulation and
outdoor-radiation predictions (Annex F and Annex G worked examples).

## See also

- [Field Insulation Measurement and Ratings](insulation-field.md):
  the measured in-situ quantities the prediction is checked against.
- [Laboratory Insulation Measurement](insulation-lab.md): the
  ISO 10140 ratings and ISO 10848 junction data the model consumes.
- [Sound absorption in enclosed spaces (EN 12354-6)](enclosed-space-absorption.md):
  the absorption member of the same EN 12354 family.
- [Dynamic stiffness of resilient materials (EN 29052-1)](dynamic-stiffness.md):
  the s' input to the EN 12354-2 floating-floor term.
- API reference: [`building.building_prediction`](https://jmrplens.github.io/phonometry/reference/api/building/building-prediction/) and [`building.facade_prediction`](https://jmrplens.github.io/phonometry/reference/api/building/facade-prediction/).

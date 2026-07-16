← [Documentation index](README.md)

# Reverberation-time prediction (Sabine · Eyring · Fitzroy · Arau-Puchades)

The **reverberation time** $T$ — the time for the sound-energy level to fall by
60 dB after the source stops — is predicted here from a room's **volume**,
**boundary areas** and the **sound-absorption coefficients** of its surfaces,
through the classical statistical-acoustics formulae. This is the design-stage
counterpart of the *measured* reverberation time of
[Room Acoustics](room-acoustics.md) (ISO 3382) and complements the EN 12354-6
model of [Sound absorption in enclosed spaces](enclosed-space-absorption.md),
which specialises the same physics to that standard's Clause 4.

phonometry offers five models, ordered by how much they account for a
**non-uniform** absorption distribution:

| Model | Absorption term in $T = k\,V / (\text{term} + 4mV)$ | Best for |
|:---|:---|:---|
| **Sabine** | $A = \sum_i S_i\alpha_i$ | low, uniform absorption |
| **Eyring** (Norris-Eyring) | $-S\ln(1-\bar\alpha)$ | strong, uniform absorption |
| **Millington-Sette** | $-\sum_i S_i\ln(1-\alpha_i)$ | a few very absorptive surfaces |
| **Fitzroy** | area-weighted **arithmetic** mean of three axial Eyring times | anisotropic rooms |
| **Arau-Puchades** | area-weighted **geometric** mean of the same three | anisotropic rooms (author-preferred) |

with the Sabine constant $k = 24\ln 10 / c_0$ (so $k = 0.161$ for
$c_0 = 343\ \mathrm{m/s}$) and the air-absorption term $4mV$.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reverberation_models_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reverberation_models.svg" alt="Reverberation time per octave band for a 10 by 7 by 3.5 metre room with an absorptive floor and ceiling but hard walls, computed by five models. Fitzroy gives the longest times, Sabine and Eyring the mid-range, Millington-Sette the shortest, and Arau-Puchades sits between Eyring and Sabine" width="82%"></picture>

## 1. Sabine, Eyring and Millington-Sette

The three statistical models take the room volume and a list of
`(area, absorption_coefficient)` surfaces. **Sabine** is exact only for low,
uniform absorption; **Eyring** replaces the absorption area by
$-S\ln(1-\bar\alpha)$ and is correct where Sabine overestimates $T$ (a live
room with strong absorption); **Millington-Sette** sums the Eyring term surface
by surface, so a single perfectly absorbing surface drives $T$ to zero.

$$
T_{\text{Sab}} = \frac{k V}{\sum_i S_i\alpha_i}, \qquad
T_{\text{Eyr}} = \frac{k V}{-S\ln(1-\bar\alpha)}, \qquad
T_{\text{Mil}} = \frac{k V}{-\sum_i S_i\ln(1-\alpha_i)}.
$$

```python
import phonometry as ph

# A shoebox 8 x 5 x 3 m (V = 120 m3, S = 158 m2), uniform alpha = 0.2.
surfaces = [(40.0, 0.2), (40.0, 0.2), (24.0, 0.2),
            (24.0, 0.2), (15.0, 0.2), (15.0, 0.2)]
print(round(ph.sabine_reverberation_time(120.0, surfaces), 3))            # 0.612 s
print(round(ph.eyring_reverberation_time(120.0, surfaces), 3))            # 0.548 s
print(round(ph.millington_sette_reverberation_time(120.0, surfaces), 3))  # 0.548 s
```

For a **uniform** distribution Eyring and Millington-Sette coincide, and both
fall below Sabine — Sabine's over-estimate at high absorption is the reason
Eyring exists. As $\alpha \to 0$, $-S\ln(1-\bar\alpha) \to \sum_i S_i\alpha_i$
and Eyring reduces to Sabine. Air absorption enters every model through the
power-attenuation coefficient $m$ (in neper per metre, from
[atmospheric absorption](room-acoustics.md)):

```python
import phonometry as ph

m = ph.air_attenuation_m(2000.0, temperature=20.0, relative_humidity=50.0)
surfaces = [(40.0, 0.3), (40.0, 0.3), (24.0, 0.3),
            (24.0, 0.3), (15.0, 0.3), (15.0, 0.3)]
print(round(ph.eyring_reverberation_time(120.0, surfaces, air_attenuation=m), 3))
```

Every statistical model also assumes a **diffuse field**, and low
frequencies break that assumption first: below the Schroeder frequency the
room responds as a set of discrete modes, not as a reverberant mixture. The
2D FDTD simulation below drives a rigid 5 m by 3.5 m room exactly on its
(2,1) mode and then between two modes; the standing-wave pattern that
builds up on resonance is what Sabine and Eyring cannot see.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_dark.gif"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes.gif" alt="Animation: a 2D FDTD simulation of a 5 by 3.5 metre room driven at the 84 Hz (2,1) mode and at an off-mode frequency; on resonance a standing-wave pattern with fixed nodal lines grows to dominate the RMS pressure map, off resonance the forced response stays weak and disorganised" width="640" height="360" loading="lazy"></picture>

[Watch the high-resolution video (WebM)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes.webm)

## 2. Fitzroy and Arau-Puchades (anisotropic rooms)

When the absorption is concentrated on one axis — a carpeted floor and an
acoustic ceiling against otherwise hard walls — a single mean $\bar\alpha$
misrepresents the field. **Fitzroy** and **Arau-Puchades** split a rectangular
(shoebox) room into the three pairs of opposing walls and combine the *axial*
Eyring reverberation times $T_i$ (each using the whole surface $S$ and the mean
absorption $\bar\alpha_i$ of the wall pair perpendicular to axis $i$):

$$
T_{\text{Fitz}} = \sum_i \frac{S_i}{S}\,T_i \quad(\text{arithmetic}), \qquad
T_{\text{Arau}} = \prod_i T_i^{\,S_i/S} \quad(\text{geometric}).
$$

```python
import phonometry as ph

# 8 x 5 x 3 m room, absorptive x-wall pair (alpha 0.5), hard elsewhere (0.1).
dims = (8.0, 5.0, 3.0)
absorption = (0.5, 0.1, 0.1)   # mean alpha of the (x, y, z) wall pairs
print(round(ph.arau_puchades_reverberation_time(dims, absorption), 3))  # 0.812 s
print(round(ph.fitzroy_reverberation_time(dims, absorption), 3))        # 0.974 s
```

By the arithmetic-geometric-mean inequality the Arau-Puchades time never exceeds
the Fitzroy time; Fitzroy is known to over-predict when one wall pair is very
reflective, which is why Arau-Puchades recommends the geometric mean. Both
reduce exactly to Eyring for a uniform absorption distribution.

## 3. Comparing the five models per band

`reverberation_time_models` builds the six boundary surfaces of a rectangular
room from its dimensions and the three wall-pair mean absorptions, then
evaluates all five models on a common footing and returns a
`ReverberationModelResult` whose `.plot()` draws the figure above.

```python
import phonometry as ph

# 10 x 7 x 3.5 m room, absorptive floor/ceiling against harder walls.
res = ph.reverberation_time_models(
    (10.0, 7.0, 3.5),
    (
        [0.06, 0.07, 0.08, 0.09, 0.10, 0.10],   # x-pair: hard end walls
        [0.12, 0.14, 0.16, 0.18, 0.20, 0.20],   # y-pair: lightly treated walls
        [0.30, 0.50, 0.65, 0.78, 0.82, 0.80],   # z-pair: carpet + acoustic ceiling
    ),
    frequencies=[125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0],
)
print(res.sabine.round(2))         # [0.74 0.47 0.37 0.31 0.3  0.3 ]
print(res.arau_puchades.round(2))  # [0.79 0.51 0.38 0.29 0.26 0.27]
print(res.fitzroy.round(2))        # [1.02 0.79 0.66 0.57 0.51 0.51]
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph

m = ph.air_attenuation_m([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0], 20.0, 50.0)
ph.reverberation_time_models(
    (10.0, 7.0, 3.5),
    (
        [0.06, 0.07, 0.08, 0.09, 0.10, 0.10],
        [0.12, 0.14, 0.16, 0.18, 0.20, 0.20],
        [0.30, 0.50, 0.65, 0.78, 0.82, 0.80],
    ),
    air_attenuation=m,
    frequencies=[125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0],
).plot()
plt.show()
```

</details>

---

**References.** W. C. Sabine, *Collected Papers on Acoustics* (1922); C. F.
Eyring, "Reverberation time in 'dead' rooms", *J. Acoust. Soc. Am.* **1** (1930)
217; G. Millington, "A modified formula for reverberation", *J. Acoust. Soc.
Am.* **4** (1932) 69; D. Fitzroy, "Reverberation formula which seems to be more
accurate with nonuniform distribution of absorption", *J. Acoust. Soc. Am.*
**31** (1959) 893; H. Arau-Puchades, "An improved reverberation formula",
*Acustica* **65** (1988) 163 (Formula 18). Textbook treatments: A. Carrión
Isbert, *Diseño acústico de espacios arquitectónicos* (1998); F. A. Everest &
K. C. Pohlmann, *Master Handbook of Acoustics*, 4th ed. Air absorption follows
ISO 9613-1:1993 (see [Room Acoustics](room-acoustics.md)). The conformance suite
is anchored on a **real worked example** — Everest's Fig. 7-22 Example 1
(an untreated 23.3 × 16 × 10 ft room), whose six printed Sabine reverberation
times the SI implementation reproduces to ≤ 0.02 s — reinforced by hand-computed
closed-form values and the model identities (every model collapses to Eyring for
uniform absorption; Eyring collapses to Sabine as $\alpha \to 0$), which
transitively carry that real-data anchor to the whole family.

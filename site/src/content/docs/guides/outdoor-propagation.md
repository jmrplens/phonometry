---
title: "Outdoor Sound Propagation"
description: "Atmospheric absorption of sound (ISO 9613-1) and the ISO 9613-2 general method for outdoor sound propagation from a point source: geometrical divergence, atmospheric absorption, ground effect, barrier screening and the meteorological correction, with a per-term octave-band attenuation breakdown."
---

Predicting the noise a distant source delivers to a receiver outdoors is a
book-keeping exercise: start from the source **sound power** and subtract, band
by band, every mechanism that attenuates the sound on its way — spherical
spreading, the air itself, the ground, and any barrier in between. This page
covers the two parts of ISO 9613 that supply those terms: **ISO 9613-1**, the
pure-tone atmospheric absorption coefficient $\alpha$, and **ISO 9613-2**, the
general method that assembles $\alpha$ with divergence, ground and screening
into an octave-band prediction. The atmospheric coefficient also closes the loop
with room acoustics, since ISO 354 defers its air power-attenuation coefficient
$m$ entirely to $\alpha$.

## 1. Atmospheric absorption (ISO 9613-1)

Air is not lossless. A propagating tone bleeds energy into shear viscosity and
heat conduction — the *classical and rotational* losses that grow as $f^2$ — and
into the **vibrational relaxation** of the oxygen and nitrogen molecules, each an
energy store that resonates near a humidity- and temperature-dependent
relaxation frequency. ISO 9613-1:1993, Eq. (5) collects all of this into the
pure-tone attenuation coefficient $\alpha$, in decibels per metre:

$$
\alpha = 8.686\ f^2 \Big[ 1.84\times10^{-11} \big(p_a/p_r\big)^{-1} \big(T/T_0\big)^{1/2}
       + \big(T/T_0\big)^{-5/2} \big( 0.01275\ \tfrac{e^{-2239.1/T}}{f_{rO} + f^2/f_{rO}}
       + 0.1068\ \tfrac{e^{-3352.0/T}}{f_{rN} + f^2/f_{rN}} \big) \Big],
$$

with the oxygen and nitrogen relaxation frequencies $f_{rO}$, $f_{rN}$
(Eq. (3)/(4)), the reference conditions $T_0 = 293.15$ K and $p_r = 101.325$ kPa
(Clause 4.2), and the molar water-vapour concentration $h$ obtained from the
relative humidity by the Annex B psychrometric conversion. Two features dominate
the shape: at low frequency $\alpha \propto f^2$, so it rises steeply; and near
each relaxation frequency the matching term peaks and rolls off. Between them
$\alpha$ climbs about two decades from 50 Hz to 10 kHz, and — because humidity
sets $f_{rO}$ — sweeping the humidity moves a relaxation peak across the band, so
the driest air is not always the least absorbing.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/air_absorption_alpha.png" alt="ISO 9613-1 pure-tone atmospheric attenuation coefficient alpha in dB/km against frequency on log-log axes, for four temperature and humidity combinations, showing the f-squared low-frequency growth and the humidity-dependent relaxation roll-off" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/air_absorption_alpha_dark.png" alt="ISO 9613-1 pure-tone atmospheric attenuation coefficient alpha in dB/km against frequency on log-log axes, for four temperature and humidity combinations, showing the f-squared low-frequency growth and the humidity-dependent relaxation roll-off" style="width:80%">

*The dry 20 °C / 10 % curve absorbs most at mid frequencies, but the humid
curves overtake it below ~200 Hz — the relaxation signature.*

```python
import numpy as np
from phonometry import air_attenuation, air_attenuation_m

bands = [63, 125, 250, 500, 1000, 2000, 4000, 8000]   # octave-band centres [Hz]

# Pure-tone attenuation coefficient alpha [dB/m] at 20 °C, 50 % RH, one atmosphere
alpha = air_attenuation(bands, temperature=20.0, relative_humidity=50.0)
print(np.round(alpha * 1000.0, 2))          # in dB/km, as Table 1 tabulates
# [  0.12   0.44   1.31   2.73   4.66   9.89  29.67 105.29]

# Reproduce an ISO 9613-1 Table 1 cell exactly (10 °C, 70 %, 1 kHz)
cell = air_attenuation(1000.0, 10.0, 70.0, exact_midband=True) * 1000.0
print(round(float(cell), 2))                # 3.66  (dB/km, Table 1)

# Feed real conditions into the ISO 354 power attenuation coefficient m [1/m]
m = air_attenuation_m([1000.0, 4000.0], temperature=20.0, relative_humidity=50.0)
print(np.round(m, 5))                        # [0.00107 0.00683]
```

`air_attenuation` returns dB/m (Table 1 prints dB/km, i.e. $\times 1000$); it is
fully vectorized over `frequencies` with scalar temperature, humidity and
pressure. Passing `exact_midband=True` snaps each requested frequency onto the
exact one-third-octave midband $f_m = 1000 \cdot 10^{k/10}$ (Eq. (6), Note 5)
used to compute Table 1, so the library reproduces every tabulated point to under
0.4 % — the standard's own three-significant-figure precision, far inside its
stated $\pm 10$ % accuracy (Clause 7.1). Inputs outside the tabulated ranges
(−20…+50 °C, 10…100 % RH, 50…10 000 Hz, or above the 200 kPa validity envelope)
still compute but raise an `AtmosphericAbsorptionWarning`; non-physical inputs
(non-positive frequency, humidity outside 0…100 %, sub-absolute-zero
temperature) raise `ValueError`. `air_attenuation_m` composes $\alpha$ with the
ISO 354 conversion $m = \alpha/(10 \lg e)$ so an ISO 354 caller can feed real
atmospheric conditions straight into `absorption_area` /
`absorption_coefficient` instead of hand-entering $m$.

### `air_attenuation()` / `air_attenuation_m()` parameters

| Parameter | Type / shape | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `frequencies` | scalar or 1D array | Hz | > 0 | Vectorized; 50–10 000 Hz tabulated |
| `temperature` | float | °C | default `20.0` | −20…+50 tabulated; outside warns |
| `relative_humidity` | float | % | default `50.0` | 10…100 tabulated; `[0, 100]` allowed |
| `pressure` | float | kPa | default `101.325` | ≤ 200 valid (Clause 7); above warns |
| `exact_midband` | bool | — | default `False` | Snap to $f_m = 1000\cdot10^{k/10}$ (reproduces Table 1) |

`air_attenuation` returns $\alpha$ in dB/m; `air_attenuation_m` returns
$m = \alpha/(10 \lg e)$ in 1/m for ISO 354.

## 2. General method of calculation (ISO 9613-2)

ISO 9613-2:1996 predicts the octave-band level at a receiver **downwind** of a
point source (or under the equivalent moderate temperature inversion, Clause 5).
The equivalent-continuous downwind level is

$$
L_{fT}(DW) = L_W + D_c - A, \qquad A = A_{div} + A_{atm} + A_{gr} + A_{bar} + A_{misc},
$$

(Eq. (3)/(4)) where $L_W$ is the octave-band sound power level, $D_c$ the
directivity correction (directivity index plus a solid-angle index
$D_\Omega$), and $A$ the total attenuation. The library implements the four
general terms of Clause 7; the informative $A_{misc}$ (foliage, industrial
sites, housing; Annex A) and reflections off vertical obstacles (Clause 7.5) are
**not implemented** — the standard treats them as informative and they are left
to the caller.

The geometry of the screening term fixes the vocabulary — the diffraction edge
splits the source-to-receiver distance into $d_{ss}$ and $d_{sr}$, and the extra
path length over the edge is $z = d_{ss} + d_{sr} - d$:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_outdoor_geometry.svg" alt="ISO 9613-2 source-barrier-receiver geometry: a point source at height hs, a barrier whose top edge splits the path into dss and dsr, and a receiver at height hr, with the blocked direct ray and the diffracted ray over the edge, the path difference z and the Dz formula" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_outdoor_geometry_dark.svg" alt="ISO 9613-2 source-barrier-receiver geometry: a point source at height hs, a barrier whose top edge splits the path into dss and dsr, and a receiver at height hr, with the blocked direct ray and the diffracted ray over the edge, the path difference z and the Dz formula" style="width:92%">

### The four attenuation terms

* **Geometrical divergence** $A_{div} = 20 \log_{10}(d/d_0) + 11$ dB, $d_0 = 1$ m
  (Eq. (7)): spherical spreading from a point source. Exactly 51 dB at 100 m,
  +6 dB per distance doubling. The $+11$ ($= 10 \lg 4\pi$) sets the level at the
  1 m reference distance.
* **Atmospheric absorption** $A_{atm} = \alpha\ d$ (Eq. (8)) with $\alpha$ the
  ISO 9613-1 coefficient — negligible at low frequency, dominant at 8 kHz over
  long paths.
* **Ground effect** $A_{gr} = A_s + A_r + A_m$ (Eq. (9)) sums a source, receiver
  and middle region, each from the Table 3 functions $a'/b'/c'/d'$ and its
  ground factor $G$ (0 = hard/reflective, 1 = porous/absorbing). A **negative**
  $A_{gr}$ is a net *gain* from constructive ground reflection.
* **Screening** by a barrier is the diffraction insertion loss
  $D_z = 10 \log_{10}\big[ 3 + (C_2/\lambda)\ C_3\ z\ K_{met} \big]$ (Eq. (14)),
  capped at 20 dB (single edge) or 25 dB (double edge). For a top-edge barrier
  the ground effect of the screened path folds into it,
  $A_{bar} = D_z - A_{gr} \ge 0$ (Eq. (12), Note 13); for a lateral barrier
  $A_{bar} = D_z$ and the ground term is retained (Eq. (13)).

`outdoor_propagation_attenuation` assembles the four terms into an
`OutdoorAttenuation` result whose per-band arrays sum, band by band, to
`a_total`, so the divergence, atmospheric, ground and barrier contributions stay
separable. The stacked breakdown makes the frequency character obvious: the
barrier helps most at high frequency (short wavelength) until it saturates at the
cap, atmospheric absorption bites only at 8 kHz, and the ground dip lives in the
mid bands.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/outdoor_attenuation_breakdown.png" alt="ISO 9613-2 per-octave-band attenuation breakdown as a stacked bar of Adiv, Aatm, Agr and Abar with the total A overlaid, for a 200 m path over porous ground with a 4 m barrier" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/outdoor_attenuation_breakdown_dark.png" alt="ISO 9613-2 per-octave-band attenuation breakdown as a stacked bar of Adiv, Aatm, Agr and Abar with the total A overlaid, for a 200 m path over porous ground with a 4 m barrier" style="width:80%">

```python
import numpy as np
from phonometry import (
    Barrier, outdoor_propagation_attenuation, predicted_receiver_level,
)

bands = [63, 125, 250, 500, 1000, 2000, 4000, 8000]   # octave-band centres [Hz]

# A point source and receiver 1.5 m high, 200 m apart over porous ground
# (G = 1), screened midway by a barrier that raises the path over its top edge
# (dss = dsr ~ 101 m). Geometry feeds the pathlength-difference equations.
barrier = Barrier(source_to_edge=101.0, edge_to_receiver=101.0)
att = outdoor_propagation_attenuation(
    200.0, source_height=1.5, receiver_height=1.5, frequencies=bands,
    ground_source=1.0, ground_middle=1.0, ground_receiver=1.0,
    barrier=barrier, temperature=15.0, humidity=70.0,
)
print(np.round(att.a_div, 1))     # [57. 57. 57. 57. 57. 57. 57. 57.]  divergence
print(np.round(att.a_gr, 2))      # [-4.65  2.34 13.79  9.76  1.3  -0.   -0.   -0.  ]
print(np.round(att.a_bar, 2))     # [13.78  8.89  0.    6.69 18.01 20.   20.   20.  ]
print(np.round(att.a_total, 1))   # [66.2 68.3 71.  73.9 77.1 78.8 82.3 96. ]

# Predicted receiver level from an octave-band sound power Lw = 95 dB
lw = np.full(len(bands), 95.0)
lp = predicted_receiver_level(
    lw, 200.0, 1.5, 1.5, bands, 1.0, 1.0, 1.0,
    barrier=barrier, temperature=15.0, humidity=70.0,
)
print(np.round(lp, 1))            # [28.8 26.7 24.  21.1 17.9 16.2 12.7 -1. ]
```

`predicted_receiver_level` composes $L_{fT}(DW) = L_W + D_c - A$ with
$D_c = $ `directivity_index` $+ $ `d_omega`. Pass `c0=` to subtract the
meteorological correction $C_{met}$ (Eq. (21)/(22)) band by band for a long-term
average — note the standard applies $C_{met}$ to the A-weighted level, so the
per-band form here is a **convenience**, not a literal reading of Clause 8.

### Ground: the alternative A-weighted method

When only the A-weighted receiver level matters and the sound travels over
porous or mostly-porous ground (and is not a pure tone), 7.3.2 offers a simpler
closed form $A_{gr} = 4.8 - (2 h_m/d)[17 + 300/d] \ge 0$ (Eq. (10), negative
results clamped to zero), paired with the solid-angle index $D_\Omega$
(Eq. (11)) that must then be added to $D_c$. These are exposed as
`ground_attenuation_alternative` and `directivity_omega`, but they are **not
auto-wired** into `outdoor_propagation_attenuation` (which always uses the
general per-region method of 7.3.1); combine them by hand when the alternative
method is appropriate.

```python
from phonometry import (
    ground_attenuation_alternative, directivity_omega, meteorological_correction,
)

# Alternative ground term (mean path height hm = 2 m, d = 200 m)
print(round(ground_attenuation_alternative(200.0, 2.0), 2))          # 4.43 dB
# Its companion solid-angle index (add to Dc when using Eq. (10))
print(round(directivity_omega(1.5, 1.5, 200.0), 2))                  # 3.01 dB
# Long-term meteorological correction (C0 = 2 dB) to subtract from LAT(DW)
print(round(meteorological_correction(200.0, 1.5, 1.5, 2.0), 2))     # 1.7 dB
```

### `Barrier` and the screening term

The `Barrier` dataclass describes the diffraction geometry directly, which is
the cleanest match to Eq. (14)/(16)/(17). Single diffraction (a thin screen)
leaves `edge_separation=None` ($C_3 = 1$); giving the edge spacing `e` selects
double (thick-barrier) diffraction with the $C_3$ factor of Eq. (15) and the
25 dB cap. `ground_reflections_by_image=True` switches $C_2$ from 20 to 40
(reflections handled by image sources), and `lateral=True` selects vertical-edge
diffraction (Eq. (13), $K_{met}=1$, ground term retained).

### `outdoor_propagation_attenuation()` parameters

| Parameter | Type / shape | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `distance` | float | m | > 0 | Straight-line source–receiver distance $d$ |
| `source_height` / `receiver_height` | float | m | ≥ 0 | $h_s$, $h_r$ above ground |
| `frequencies` | 1D array | Hz | default 8 octaves 63–8000 | `DEFAULT_FREQUENCIES` |
| `ground_source` / `ground_middle` / `ground_receiver` | float | — | `[0, 1]`, default `0.0` | Ground factor $G$ (0 hard, 1 porous) |
| `barrier` | `Barrier` or None | — | default `None` | Screening obstacle |
| `temperature` / `humidity` / `pressure` | float | °C / % / kPa | 20 / 70 / 101.325 | Passed to $A_{atm}$ |
| `projected_distance` | float or None | m | default $\sqrt{d^2-(h_s-h_r)^2}$ | Ground-plane $d_p$ |

Returns an `OutdoorAttenuation` with `a_div`, `a_atm`, `a_gr`, `a_bar`,
`a_total` and `d_omega`, all one value per band.

### `Barrier` fields

| Field | Type | Units | Default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `source_to_edge` | float | m | — | $d_{ss}$, source to first edge |
| `edge_to_receiver` | float | m | — | $d_{sr}$, (last) edge to receiver |
| `parallel_distance` | float | m | `0.0` | Component $a$ parallel to the edge |
| `edge_separation` | float or None | m | `None` | $e$; given ⇒ double diffraction (25 dB cap) |
| `ground_reflections_by_image` | bool | — | `False` | `True` ⇒ $C_2 = 40$ |
| `lateral` | bool | — | `False` | `True` ⇒ vertical-edge diffraction (Eq. (13)) |

The method's stated accuracy is $\pm 1$ to $\pm 3$ dB for broadband noise up to
1000 m (Table 5). See the [Theory](/phonometry/reference/theory/) page for the full derivation, the
[Room and Building Acoustics guide](/phonometry/guides/room-acoustics/) for how $\alpha$ feeds
ISO 354, and the [Levels guide](/phonometry/guides/levels/) for the ISO 9612 occupational
exposure that consumes A-weighted levels.

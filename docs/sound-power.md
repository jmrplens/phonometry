← [Documentation index](README.md)

# Sound Power

Sound *pressure* depends on where you stand and on the room you stand in;
sound **power** does not. The sound power level `LW` is the total acoustic
energy per second a source radiates, referenced to `P0 = 1 pW`, and it is
the device-independent **emission** descriptor that goes on a datasheet,
feeds a room prediction (ISO 12354) or is checked against a noise-emission
limit. This page covers the three routes phonometry implements to obtain it
and when to reach for each: an enveloping *pressure* surface in the field
(ISO 3744/3746), the diffuse field of a *reverberation room* (ISO 3741),
*intensity* scanning over a surface (ISO 9614-2), and — for the highest
accuracy — the precision grades in an *anechoic room* (ISO 3745) and by
precision *intensity* scanning (ISO 9614-3).

## Choosing a method

All deliver the same quantity — a per-band `LW` and an A-weighted total
`LWA` — but under different environments, accuracy grades and practical
constraints.

| Method | Standard | Measured quantity | Environment | Accuracy grade | Use when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Enveloping surface | **ISO 3744** (engineering) / **ISO 3746** (survey) | Sound pressure on a hemisphere or box | Essentially free field over one or more reflecting planes | Grade 2 (`σR0 ≈ 1.5 dB`) / grade 3 (`≈ 3.0 dB`) | In situ or a large room; no special test facility available |
| Reverberation room | **ISO 3741** | Sound pressure in the diffuse field | Qualified hard-walled reverberation room | Grade 1 (precision) | Highest accuracy for steady, broadband sources in a lab |
| Intensity scanning | **ISO 9614-2** | Normal sound intensity scanned over a surface | Almost any, tolerant of steady extraneous noise | Grade 2 / 3 (from per-band field indicators) | On-site with background noise, or one machine among many |
| Anechoic room | **ISO 3745** | Sound pressure on a fixed microphone array | Qualified anechoic or hemi-anechoic room | Grade 1 (precision) | Reference-grade emission in a free-field laboratory |
| Precision intensity scanning | **ISO 9614-3** | Scanned normal intensity, tighter criteria | Almost any, tolerant of steady extraneous noise | Grade 1 (precision) | Precision on-site, with the ISO 9614-3 field-indicator checks |

The pressure methods correct the surface level for the room (`K2`) and for
background noise (`K1`); the reverberation method needs a *qualified* room
but reaches precision grade; intensity rejects steady background energy at
the cost of a two-microphone probe and a per-band validity check. The rest
of the page walks each in turn.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_methods_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sound_power_methods.svg" alt="The three sound power routes side by side: an enveloping pressure surface over a reflecting plane (ISO 3744/3746), a source in a reverberation room sampled by microphones (ISO 3741) and an intensity probe scanning a surface around the source (ISO 9614-2)" width="92%"></picture>

## 1. Enveloping surface, sound pressure (ISO 3744 / ISO 3746)

Place the source on a reflecting plane and imagine a **measurement surface**
of area `S` wrapping it: a hemisphere for a compact source, a box (right
parallelepiped) for a large or elongated one. Sample the sound pressure
level at an array of microphone positions on that surface, energy-average
them, and the sound power follows because a diffuse-enough surface captures
all the radiated energy:

$$
\bar{L}_p = 10 \log_{10}\left( \frac{1}{N_M} \sum_i 10^{L_{pi}/10} \right), \qquad
L_W = \bar{L}_p - K_1 - K_2 + 10 \log_{10}\frac{S}{S_0},\quad S_0 = 1\ \text{m}^2 .
$$

Two corrections clean up the surface level. The **background-noise
correction** removes the energy that would have been there with the source
switched off, from the margin `ΔLp` between source-on and background levels,

$$
K_1 = -10 \log_{10}\left( 1 - 10^{-\Delta L_p/10} \right),
$$

and the **environmental correction** removes the reverberant build-up of the
test room from its equivalent absorption area `A`,

$$
K_2 = 10 \log_{10}\left( 1 + \frac{4 S}{A} \right).
$$

The surface area is a closed form of the geometry: a hemisphere is
`S = 2πr²` over one reflecting plane (halved and quartered for two and three
planes), and a one-plane box is `S = 4(ab + bc + ca)` with
`a = 0.5·l1 + d`, `b = 0.5·l2 + d`, `c = l3 + d` for measurement distance
`d`. ISO 3746 (survey) shares every formula but is coarser: fewer
microphone positions, a 3 dB background criterion instead of 6 dB, and
validity up to `K2 ≤ 7 dB` instead of 4 dB.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sound_power_surfaces_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sound_power_surfaces.svg" alt="Measurement surfaces of ISO 3744: a hemisphere of radius r enveloping a compact source on a reflecting plane, and a right parallelepiped (box) at measurement distance d around a large source, both with microphone positions marked" width="88%"></picture>

```python
import numpy as np
from phonometry import sound_power_pressure, measurement_positions

# Octave-band SPL (dB) at the 10 hemisphere positions of ISO 3744 (Annex B),
# with the source running, plus the background spectrum with it switched off.
freqs = np.array([63, 125, 250, 500, 1000, 2000, 4000, 8000])
base = np.array([70.0, 74.0, 78.0, 80.0, 79.0, 76.0, 72.0, 66.0])
rng = np.random.default_rng(0)
levels = base + rng.normal(0.0, 0.5, size=(10, 8))     # (positions, bands)
background = np.full((10, 8), 55.0)

# ISO 3744 Annex B microphone coordinates on a radius-1.5 m hemisphere.
mic_xyz = measurement_positions("hemisphere", radius=1.5, reflecting_planes=1)
print(mic_xyz.shape)                                    # (10, 3)

res = sound_power_pressure(
    levels, "hemisphere", radius=1.5, reflecting_planes=1,
    background_levels=background, frequencies=freqs,
    reverberation_time=0.6, room_volume=300.0,          # room data -> K2
)
print(round(res.surface_area, 2))                       # 14.14 m^2 (= 2*pi*1.5^2)
print(round(float(res.environmental_correction[0]), 2)) # K2 = 2.32 dB
print(round(res.sound_power_level_a, 1))                # LWA = 92.4 dB
print(round(res.uncertainty, 1))                        # U = 3.0 dB (2*sigma_R0)
print(np.round(res.sound_power_level, 1))               # per-band LW

res.plot()   # sound power level bars per band, LWA in the title (needs matplotlib)
```

The A-weighted total `LWA` is combined from the band powers with the ISO 3744
Annex E A-weighting corrections, so it needs `frequencies`. Passing the room
data (`reverberation_time` + `room_volume`, or `absorption_area`, or
`mean_absorption_coefficient` + `room_surface`) enables `K2`; omit it and the
field is treated as free (`K2 = 0`). If the background margin drops below the
grade criterion or `K2` exceeds the validity limit, a `SoundPowerWarning`
flags that the levels are upper bounds — the determination still returns.

### `sound_power_pressure()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `levels_positions` | 2D array | dB | `(NM, NB)` | One row per position, one column per band (or a single A-weighted column) |
| `surface` | str | — | `'hemisphere'` / `'box'` | Measurement-surface shape |
| `radius` | float | m | > 0 (hemisphere) | Hemisphere radius `r` |
| `dimensions` | (float, float, float) | m | > 0 (box) | Reference-box `(l1, l2, l3)` |
| `distance` | float | m | > 0 (box) | Measurement distance `d` |
| `reflecting_planes` | int | — | `1` / `2` / `3`, default `1` | Halves/quarters the hemisphere area |
| `background_levels` | 2D array or spectrum | dB | `(NM, NB)`, or `(NB,)` / `(1, NB)` | Enables `K1`; a single spectrum broadcasts to every position |
| `frequencies` | 1D array | Hz | nominal band centres | Enables `LWA` (Annex E) |
| `absorption_area` | float or 1D array | m² | > 0 | `A` for `K2` (direct); per-band array → per-band `K2` |
| `reverberation_time`, `room_volume` | float/array, float | s, m³ | > 0 | `A = 0.16 V/T` for `K2`; per-band `T` → per-band `K2` |
| `mean_absorption_coefficient`, `room_surface` | float/array, float | —, m² | `(0,1]`, > 0 | `A = α·Sv` (Eq. A.7); per-band `α` → per-band `K2` |
| `grade` | str | — | `'engineering'` (default) / `'survey'` | ISO 3744 vs ISO 3746 |
| `omc_uncertainty` | float | dB | default `0.0` | `σomc`, operating/mounting instability, folded into `U` |

Returns a `SoundPowerResult`: `sound_power_level` (per-band `LW`),
`surface_pressure_level` (`Lp` after K1/K2), `mean_pressure_level`,
`background_correction`/`environmental_correction` (`K1`/`K2`),
`directivity_index` (apparent `DIi*` per microphone position **and** frequency
band, shape `(NM, NB)`; ISO 3744 clause 8.6), `surface_area`,
`sound_power_level_a` (`LWA`), `uncertainty` (expanded, 95 %) and `grade`.
`measurement_positions('hemisphere', radius=…, reflecting_planes=…, tones=…,
grade=…)` returns the normative `(N, 3)` microphone coordinates (Table B.1 for
tonal sources, B.2 for broadband).

## 2. Reverberation room, precision grade (ISO 3741)

In a qualified hard-walled **reverberation room** the field is diffuse, so a
handful of microphones sample the whole radiated energy and the method
reaches grade 1. The sound power comes from the mean room level `Lp(ST)`,
the Sabine absorption area `A = (55.26/c)·(V/T60)` and a chain of small
corrections (ISO 3741 Eq. 20):

$$
L_W = \bar{L}_p + 10 \log_{10}\frac{A}{A_0} + 4.34\ \frac{A}{S}
      + 10 \log_{10}\left( 1 + \frac{S c}{8 V f} \right) + C_1 + C_2 - 6 .
$$

The bracketed term is the **Waterhouse correction**: near the room
boundaries the sound energy density is higher than in the interior, and
this term (which vanishes as frequency grows) restores the energy the
interior microphones miss. `C1` (reference-quantity) and `C2`
(radiation-impedance) carry the result to the reference meteorological
conditions of 23 °C and 101.325 kPa,

$$
C_1 = -10 \log_{10}\frac{p_s}{p_{s0}} + 5 \log_{10}\frac{273.15 + \theta}{314}, \qquad
C_2 = -10 \log_{10}\frac{p_s}{p_{s0}} + 15 \log_{10}\frac{273.15 + \theta}{296},
$$

with the speed of sound `c = 20.05·√(273 + θ)`. The **comparison method**
replaces the absorption-area, Waterhouse and `C1` terms by a reference sound
source of known power `LW(RSS)` measured in the same room, so the room need
not be characterised: `LW = LW(RSS) + (Lp(ST) − Lp(RSS) + C2)`.

```python
import numpy as np
from phonometry import sound_power_reverberation, sound_power_comparison

# One-third-octave mean room SPL (dB), 100 Hz - 10 kHz, and the room's T60.
freqs = np.array([100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000,
                  1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000],
                 dtype=float)
lp = np.linspace(80.0, 70.0, freqs.size)
t60 = np.full(freqs.size, 2.0)

rev = sound_power_reverberation(
    lp, t60, volume=200.0, surface_area=220.0, frequencies=freqs,
    temperature=20.0, static_pressure=101.0,
)
print(round(rev.speed_of_sound, 1))                     # c = 343.2 m/s
print(round(float(rev.absorption_area[0]), 1))          # A = 16.1 m^2 at 100 Hz
print(round(float(rev.waterhouse_correction[0]), 2))    # 1.68 dB at 100 Hz
print(round(float(rev.sound_power_level[0]), 1))        # LW = 87.9 dB
print(round(rev.sound_power_level_a, 1))                # LWA = 92.1 dB

# Comparison method: a reference source of known LW measured at the same spots.
lw_rss = np.full(freqs.size, 85.0)
lp_rss = np.linspace(78.0, 69.0, freqs.size)
cmp = sound_power_comparison(lp, lp_rss, lw_rss, frequencies=freqs, temperature=20.0)
print(round(float(cmp.sound_power_level[0]), 1), cmp.method)   # 86.9 comparison

rev.plot()   # reverberation-room LW spectrum, LWA in the title (needs matplotlib)
```

`levels` may be a 1D mean spectrum or a 2D `(NM, NB)` array averaged over
positions. When the room volume, its reverberation time or the microphone
count fail an ISO 3741 qualification criterion (Table 1 minimum volume, the
`V/S` reverberation floor, fewer than 6 positions, or an inter-position
spread above 1.5 dB), an advisory `SoundPowerWarning` is emitted and the
result still returns.

### `sound_power_reverberation()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `levels` | 1D or 2D array | dB | per band, or `(NM, NB)` | Mean room SPL; 2D is energy-averaged over positions |
| `t60` | float or 1D array | s | > 0 | Room reverberation time (scalar broadcasts) |
| `volume` | float | m³ | > 0 | Room volume `V` |
| `surface_area` | float | m² | > 0 | Total room surface `S` (Waterhouse, `A/S`) |
| `frequencies` | 1D array | Hz | one per band | Required (Waterhouse needs `f`); enables `LWA` |
| `background_levels` | 1D or 2D array | dB | matches `levels` | Per-band `K1` (frequency-dependent criterion) |
| `temperature` | float | °C | default `23.0` | Sets `c`, `C1`, `C2` |
| `static_pressure` | float | kPa | default `101.325` | Sets `C1`, `C2` |

`sound_power_comparison(levels, levels_ref, lw_ref, *, frequencies=None,
background_levels=…, background_levels_ref=…, temperature=23.0,
static_pressure=101.325)` takes the same room levels plus the reference
source's levels and known power.

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `levels_ref` | 1D or 2D array | dB | matches `levels` | Mean room SPL with the reference source (RSS) running |
| `lw_ref` | 1D array | dB | per band | Known sound power `LW(RSS)` of the reference source |
| `background_levels` | 1D or 2D array | dB | matches `levels` | Background for the test source; per-band `K1` on `Lp(ST)` |
| `background_levels_ref` | 1D or 2D array | dB | matches `levels_ref` | Background for the **reference** source; per-band `K1` on `Lp(RSS)` |

`background_levels_ref` background-corrects the reference-source room level
`Lp(RSS)` exactly as `background_levels` does for the test source; both need
`frequencies` (the ISO 3741 criterion is frequency-dependent). Both return a
`ReverberationSoundPowerResult`
(`sound_power_level`, `mean_pressure_level`, `absorption_area`,
`waterhouse_correction`, `background_correction`, `c1`, `c2`,
`speed_of_sound`, `sound_power_level_a`, `method`; the absorption/Waterhouse/`c1`
fields are `NaN` for the comparison method).

## 3. Intensity scanning (ISO 9614-2)

Sound **intensity** is the net energy flux, so it distinguishes energy
*leaving* the source from steady energy merely passing through the surface —
which is why the intensity method tolerates background noise that would
defeat the pressure methods. A p-p probe (see the
[Sound Intensity guide](intensity.md)) is swept continuously over each of
`N` segments of a surface enclosing the source, reporting the segment-averaged
signed normal intensity `<In,i>`. The partial powers sum to the total:

$$
P_i = \langle I_{n,i} \rangle\ S_i, \qquad P = \sum_i P_i, \qquad
L_W = 10 \log_{10}\frac{P}{P_0},\quad P_0 = 1\ \text{pW} .
$$

A band in which `P < 0` (net inflow, from a stronger source outside the
surface) is **not determinable** and reported as `NaN`. Two normative field
indicators qualify each band. The **surface pressure-intensity indicator**
`FpI` measures how reactive the field is, and the **negative-partial-power
indicator** `F+/-` measures how much energy circulates in and out:

$$
F_{pI} = [L_p] - L_W + 10 \log_{10}\frac{S}{S_0}, \qquad
F_{+/-} = 10 \log_{10}\frac{\sum_i \lvert P_i \rvert}{\lvert \sum_i P_i \rvert} .
$$

The probe's **dynamic capability** `Ld = δpI0 − K` (pressure-residual
intensity index minus the bias factor `K`, 10 dB for grade 2 and 7 dB for
grade 3) must exceed `FpI` (criterion 1); `F+/- ≤ 3 dB` is criterion 2
(mandatory for grade 2); and the two repeated sweeps must agree within the
Table 2 limit `s` per segment (criterion 3). A band is **engineering** grade
when criteria 1, 2 and 3 hold, **survey** when 1 and 3 hold, else `none`.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe.svg" alt="A two-microphone p-p sound intensity probe: two pressure microphones separated by a spacer, from which the pressure gradient and hence the normal intensity are estimated" width="70%"></picture>

```python
import numpy as np
from phonometry import sound_power_intensity

# 6 surface segments x 6 octave bands: signed normal intensity (W/m^2) from two
# repeated sweeps, the segment areas, and the per-segment surface SPL (dB).
freqs = np.array([125, 250, 500, 1000, 2000, 4000], dtype=float)
areas = np.full(6, 0.5)                                 # 0.5 m^2 per segment
rng = np.random.default_rng(0)
scan1 = np.abs(rng.normal(1e-4, 2e-5, size=(6, 6)))     # (segments, bands)
scan2 = scan1 * (1.0 + rng.normal(0.0, 0.02, size=(6, 6)))
pressure = np.full((6, 6), 80.0)

res = sound_power_intensity(
    scan1, areas, normal_intensity_2=scan2, pressure_levels=pressure,
    pressure_residual_index=12.0, frequencies=freqs,
    band_type="octave", grade="engineering",
)
print(np.round(res.sound_power_level, 1))               # per-band LW
print(round(res.sound_power_level_a, 1))                # LWA over determinable bands
print(round(float(res.dynamic_capability_index[0]), 1)) # Ld = 12 - 10 = 2.0 dB
print(round(float(res.surface_pressure_intensity_index[0]), 2))   # FpI
print(list(res.achieved_grade))                         # per-band grade

res.plot()   # LW spectrum; non-positive (undeterminable) bands hatched (needs matplotlib)
```

Supplying `normal_intensity_2` (the second sweep) averages the two for the
partial powers and evaluates criterion 3; `pressure_levels` enables `FpI`;
`pressure_residual_index` (`δpI0`) plus a second sweep enables the per-band
achieved grade. The probe's finite-difference intensity has a
frequency-dependent bias handled in the [intensity guide](intensity.md).

### `sound_power_intensity()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `normal_intensity` | 2D array | W/m² | `(N_seg, N_bands)` | Signed segment-averaged normal intensity `<In,i>` (first sweep) |
| `areas` | 1D array | m² | > 0, `(N_seg,)` | Segment areas `Si` |
| `normal_intensity_2` | 2D array | W/m² | same shape | Second sweep → criterion 3 and averaging |
| `pressure_levels` | 2D array | dB | same shape | Segment SPL `Lpi` → `FpI` |
| `pressure_residual_index` | float or 1D array | dB | — | `δpI0` → `Ld` / criterion 1 |
| `frequencies` | 1D array | Hz | nominal centres | `LWA` and Table 2 limits |
| `band_type` | str | — | `'third'` (default) / `'octave'` | Table 2 lookup |
| `grade` | str | — | `'engineering'` (default) / `'survey'` | Selects `K` |
| `repeatability_limit` | float or 1D array | dB | default Table 2 | Override criterion-3 `s` |

Returns a `SoundPowerIntensityResult`: `partial_power`/`partial_power_level`
per segment and band, `sound_power`/`sound_power_level` (band total, `NaN`
where `negative_band`), `surface_pressure_intensity_index` (`FpI`),
`negative_partial_power_index` (`F+/-`), `repeatability`,
`dynamic_capability_index` (`Ld`), `achieved_grade`, `surface_area`,
`sound_power_level_a` and `grade`.

## 4. Precision grade, anechoic room (ISO 3745)

When the highest accuracy is required, ISO 3745 measures sound power in a
qualified **anechoic** or **hemi-anechoic** room, where the free field lets a
fixed array of microphones sample the radiated sound pressure directly. It is the
grade-1 counterpart to the enveloping-surface method of Section 1, with
standardized microphone coordinates, a per-position background correction and an
explicit meteorological correction.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_precision_anechoic_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_precision_anechoic.svg" alt="ISO 3745 precision sound power in an anechoic room: wedge-lined walls, the device under test at the centre and a hemispherical array of microphones at a fixed radius, with the sound power level formed from the surface-averaged pressure plus the area, background and meteorological corrections" width="92%"></picture>

**Sound power level (Clause 8).** The band sound power level is the
surface-averaged pressure level plus the surface term and the corrections:

$$
L_W = \overline{L_p} + 10\lg\frac{S}{S_0} + C_1 + C_2 + C_3,
$$

with $S = 4\pi r^2$ over the sphere or $S = 2\pi r^2$ over the hemisphere,
$S_0 = 1\ \text{m}^2$. $C_1$ and $C_2$ are the meteorological corrections
(reference and radiation-impedance terms); $C_3$ accounts for air absorption over
the measurement radius. The microphone positions are the standardized
unit-vector arrays of Tables D.1 (sphere), E.1 (hemisphere) and E.2 (hemisphere,
broadband).

```python
import numpy as np
import phonometry as ph

# The 40 standardized hemisphere positions (unit vectors scaled by the radius).
pos = ph.precision_positions("hemisphere", radius=1.0, count=40)
print(pos.shape)                      # (40, 3)

# Octave/third-octave band SPL (dB) at each of the 40 positions; here a uniform
# 74 dB in one band. The result carries S = 2*pi*r^2 and LW with C1+C2+C3.
levels = np.full((40, 1), 74.0)
res = ph.sound_power_anechoic(levels, "hemisphere", radius=1.0)
print(round(res.surface_area, 3))                 # 6.283  (2*pi*1^2)
print(np.round(res.sound_power_level, 2))         # [81.85]
```

**Background and meteorological corrections.** The $K_1$ background correction is
applied **per position** and floored where the signal-to-background difference is
small (Eq. 11); the meteorological correction is evaluated from the measured
temperature and static pressure.

```python
import numpy as np
import phonometry as ph

# K1 for a 6 dB signal-to-background difference in a <=200 Hz edge band: the
# floor is 1.26 dB (Eq. 11). Source and background levels are [positions, bands].
k1 = ph.precision_background_correction(
    np.array([[56.0]]), np.array([[50.0]]), np.array([200.0]))
print(round(float(k1[0, 0]), 4))      # 1.2563

# Meteorological corrections at the 23 C, 101.325 kPa reference (Eq. 16):
mc = ph.meteorological_corrections(23.0, 101.325)
print(round(mc.c1, 4), round(mc.c2, 4))   # -0.1282 0.0

# Expanded uncertainty (Clause 10.5 EXAMPLE): sigma_R0 = 0.5, sigma_omc = 2.0,
# k = 2 -> U = 4.1 dB.
print(round(ph.precision_uncertainty(0.5, 2.0, 2.0), 3))   # 4.123
```

Over several bands `sound_power_anechoic` returns a plottable
`PrecisionSoundPowerResult` carrying the per-band `LW` and the A-weighted total:

```python
import numpy as np
import phonometry as ph

# A mid-frequency-peaked machine measured over the 40-position hemisphere array
# (Annex E). levels_positions is the (40, NB) surface pressure spectrum: a base
# spectrum peaked near 1 kHz plus a small per-position spatial spread.
freqs = np.array([125, 250, 500, 1000, 2000, 4000, 8000], float)
base = 70.0 + 8.0 * np.exp(-(np.log2(freqs / 1000.0) ** 2) / 2.0)
rng = np.random.default_rng(7)
levels = base[None, :] + rng.normal(0.0, 1.0, (40, freqs.size))

result = ph.sound_power_anechoic(levels, "hemisphere", radius=1.0, frequencies=freqs)
print(round(result.sound_power_level_a, 1))   # 89.3
result.plot()   # LW spectrum, LWA in the title (needs matplotlib)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/precision_anechoic_power_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/precision_anechoic_power.png" alt="The precision sound power level spectrum of a mid-frequency-peaked machine measured over the ISO 3745 hemisphere array, one bar per band peaking near 1 kHz, with the A-weighted total of 89.3 dB(A) in the title" width="88%"></picture>

*One bar per band: the surface-averaged pressure plus the area, background and
meteorological corrections give `LW(f)`, and the A-weighted energy sum across
bands gives the single-number `LWA` in the title.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# result is the PrecisionSoundPowerResult computed above. One line:
result.plot()
plt.show()

# By hand: a bar spectrum of LW with the A-weighted total in the title.
freqs = result.frequencies
positions = np.arange(freqs.size)
fig, ax = plt.subplots()
ax.bar(positions, result.sound_power_level, width=0.7, color="#1f77b4")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frequency [Hz]")
ax.set_ylabel("Sound power level LW [dB]")
ax.set_title(
    f"Precision sound power (ISO 3745)  LWA = {result.sound_power_level_a:.1f} dB(A)")
plt.show()
```

</details>

## 5. Precision intensity scanning (ISO 9614-3)

ISO 9614-3 is the grade-1 scanning method: like ISO 9614-2 it integrates the
normal intensity over a surface enclosing the source, but with a continuous
scan, tighter field-indicator criteria and an explicit uncertainty budget.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_intensity_scan_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_intensity_scan.svg" alt="ISO 9614-3 precision sound intensity scanning: a source enclosed by a measurement surface divided into segments, a two-microphone intensity probe scanned along a serpentine path over each segment, and the sound power formed by summing the normal intensity times segment area, subject to the field-indicator acceptance criteria" width="92%"></picture>

**Power and level (Clause 7).** The partial power of each segment is
$P_i = I_{n,i}\,S_i$; the total $P = \sum_i P_i$ gives
$L_W = 10\lg(P/P_0)$, $P_0 = 1\ \text{pW}$. A band whose net intensity is
negative (more power flowing in than out) is flagged not-applicable rather than
logged. The field indicators (temporal variability $F_T$, the signed and
unsigned pressure–intensity indicators, and the non-uniformity $F_S$) drive the
five acceptance criteria.

```python
import numpy as np
import phonometry as ph

# A fully enclosing surface with a uniform normal intensity In = W/S recovers
# the source power exactly: LW = 10*lg(W/P0). Here W = 100 uW -> 80 dB.
areas = np.array([0.5, 1.0, 0.25, 2.0])
w = 1.0e-4
i_n = np.full(areas.shape, w / float(areas.sum()))
res = ph.sound_power_intensity_precision(i_n, areas)
print(round(float(res.sound_power[0]), 6))          # 0.0001
print(round(float(res.sound_power_level[0]), 2))    # 80.0
```

Across several bands the result carries the per-band `LW` (`NaN` where the net
power is non-positive) and flags those bands `not_applicable`:

```python
import numpy as np
import phonometry as ph

# Four partial surfaces scanned over five one-third-octave bands. Each cell of
# partial_intensity is the signed normal intensity In_i (W/m^2); areas are the
# partial-surface areas Si. The 250 Hz band has net-negative power (a locally
# reactive field), so ISO 9614-3 flags it not-applicable (clause 9.2) -> NaN.
freqs = np.array([250, 500, 1000, 2000, 4000], float)
areas = np.array([0.5, 1.0, 0.75, 0.5])
base_intensity = np.array([2.0e-6, 8.0e-6, 2.0e-5, 1.0e-5, 3.0e-6])
partial_intensity = base_intensity[None, :] * np.array([1.0, 1.1, 0.9, 1.05])[:, None]
partial_intensity[:, 0] = [2.0e-6, -3.0e-6, -4.0e-6, -1.0e-6]   # net-negative band

result = ph.sound_power_intensity_precision(partial_intensity, areas, frequencies=freqs)
print(result.not_applicable_band.tolist())   # [True, False, False, False, False]
print(round(result.sound_power_level_a, 1))   # 80.6
result.plot()   # LW spectrum; the not-applicable band is hatched (needs matplotlib)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_scan_power_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_scan_power.png" alt="The precision intensity-scanning sound power level spectrum over five one-third-octave bands, four determinate bars and a hatched, greyed 250 Hz band flagged not-applicable because its net intensity is negative, with the A-weighted total of 80.6 dB(A) in the title" width="88%"></picture>

*The 250 Hz band nets negative (more energy flowing in than out), so ISO 9614-3
declares it not-applicable — the figure hatches and greys it while the four
determinate bands and the A-weighted total stand.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

# result is the PrecisionIntensityResult computed above. One line:
result.plot()
plt.show()

# By hand: determinate bands as LW bars; a not-applicable band (its LW is NaN)
# is flagged by a full-height greyed, hatched span rather than a zero-height bar.
freqs = result.frequencies
positions = np.arange(freqs.size)
neg = result.not_applicable_band
lw = np.nan_to_num(result.sound_power_level)
fig, ax = plt.subplots()
ax.bar(positions[~neg], lw[~neg], width=0.7, color="#1f77b4")
for pos in positions[neg]:
    ax.axvspan(pos - 0.35, pos + 0.35, facecolor="#888888", alpha=0.28,
               hatch="//", edgecolor="#888888")
ax.set_xticks(positions)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frequency [Hz]")
ax.set_ylabel("Sound power level LW [dB]")
ax.set_title(
    f"Precision intensity scanning (ISO 9614-3)  "
    f"LWA = {result.sound_power_level_a:.1f} dB(A)")
plt.show()
```

</details>

## See also

- [Sound Intensity (p-p)](intensity.md) — the two-microphone probe, its
  finite-difference bias and the ISO 9614-1 field indicators behind the
  scanning method.
- [Room and Building Acoustics](room-acoustics.md) — the reverberation time
  and equivalent absorption area (ISO 354) that feed `K2` and the ISO 3741
  absorption area; impact and airborne insulation.
- [Levels](levels.md) — energy averaging and the A-weighting behind `LWA`.
- [Theory](theory.md) — the Waterhouse, K1/K2 and C1/C2 derivations.

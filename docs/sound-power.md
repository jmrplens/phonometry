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
and *intensity* scanning over a surface (ISO 9614-2).

## Choosing a method

All three deliver the same quantity — a per-band `LW` and an A-weighted
total `LWA` — but under different environments, accuracy grades and
practical constraints.

| Method | Standard | Measured quantity | Environment | Accuracy grade | Use when |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Enveloping surface | **ISO 3744** (engineering) / **ISO 3746** (survey) | Sound pressure on a hemisphere or box | Essentially free field over one or more reflecting planes | Grade 2 (`σR0 ≈ 1.5 dB`) / grade 3 (`≈ 3.0 dB`) | In situ or a large room; no special test facility available |
| Reverberation room | **ISO 3741** | Sound pressure in the diffuse field | Qualified hard-walled reverberation room | Grade 1 (precision) | Highest accuracy for steady, broadband sources in a lab |
| Intensity scanning | **ISO 9614-2** | Normal sound intensity scanned over a surface | Almost any, tolerant of steady extraneous noise | Grade 2 / 3 (from per-band field indicators) | On-site with background noise, or one machine among many |

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
| `background_levels` | 2D array | dB | same shape as `levels` | Enables `K1` |
| `frequencies` | 1D array | Hz | nominal band centres | Enables `LWA` (Annex E) |
| `absorption_area` | float | m² | > 0 | `A` for `K2` (direct) |
| `reverberation_time`, `room_volume` | float | s, m³ | > 0 | `A = 0.16 V/T` for `K2` |
| `mean_absorption_coefficient`, `room_surface` | float | —, m² | `(0,1]`, > 0 | `A = α·Sv` for `K2` |
| `grade` | str | — | `'engineering'` (default) / `'survey'` | ISO 3744 vs ISO 3746 |
| `omc_uncertainty` | float | dB | default `0.0` | `σomc`, operating/mounting instability, folded into `U` |

Returns a `SoundPowerResult`: `sound_power_level` (per-band `LW`),
`surface_pressure_level` (`Lp` after K1/K2), `mean_pressure_level`,
`background_correction`/`environmental_correction` (`K1`/`K2`),
`directivity_index` (apparent `DIi*` per microphone position), `surface_area`,
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
```

`levels` may be a 1D mean spectrum or a 2D `(NM, NB)` array averaged over
positions. When the room volume, its reverberation time or the microphone
count fail an ISO 3741 qualification criterion (Table 1 minimum volume, the
`V/S` reverberation floor, fewer than 6 positions, or an inter-position
spread above 1.5 dB), an advisory `SoundPowerWarning` is raised and the
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
source's levels and known power. Both return a `ReverberationSoundPowerResult`
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

## See also

- [Sound Intensity (p-p)](intensity.md) — the two-microphone probe, its
  finite-difference bias and the ISO 9614-1 field indicators behind the
  scanning method.
- [Room and Building Acoustics](room-acoustics.md) — the reverberation time
  and equivalent absorption area (ISO 354) that feed `K2` and the ISO 3741
  absorption area; impact and airborne insulation.
- [Levels](levels.md) — energy averaging and the A-weighting behind `LWA`.
- [Theory](theory.md) — the Waterhouse, K1/K2 and C1/C2 derivations.

← [Documentation index](../../README.md)

# Railway rolling-stock noise: the ISO 3095 type test

A train passing a microphone is two sources at once, the vehicle and the track
it runs on. ISO 3095 is the type test of rolling stock: it fixes where the
microphones stand, what they record and how the runs are averaged, and for the
test at constant speed it fixes the track as well, through the rail roughness
of EN 15610 and the track decay rates of EN 15461. The implemented texts are
ISO 3095:2013 (third edition), the transit exposure level of ISO 3095:2005 read
from BS EN ISO 3095:2005, EN 15610:2009 read from BS EN 15610:2009 and
EN 15461:2008+A1:2010 read from BS EN 15461:2008+A1:2010, each identical to the
European or international text.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_pass_by_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_pass_by.svg" alt="A-weighted level with time weighting F against time over a 14 s record of a 100 m unit passing at 80 km/h, 7.5 m from the track: the level rises from about 64 dB to a plateau near 82 dB and falls back; the shaded measurement interval runs from 4 s to 8.5 s, the pass-by time of the unit, with the equivalent level of 81.3 dB over it and the maximum of 81.9 dB marked" width="92%"></picture>

## 1. Four tests, and the one that needs a track

| Test | Quantity | Microphones | Result | Clause |
| :--- | :--- | :--- | :--- | :--- |
| Stationary | $L_{p\mathrm{Aeq},T}$, $T \geq 20$ s | 7,5 m from the track centreline, 1,2 m above the top of rail, every 3 m to 5 m along both sides, plus two at 30° off each end of the unit (only the ends with a cab for a trailer unit) | Positions energy averaged by length; mean of three sets, rounded | 5 |
| Constant speed | $L_{p\mathrm{Aeq},T_p}$ | 7,5 m and 1,2 m; 25 m and 3,5 m allowed from 200 km/h | Mean of three runs, rounded; the louder side | 6 |
| Starting, maximum level | $L_{p\mathrm{AFmax}}$ | 7,5 m and 1,2 m, 10 m ahead of the unit and along a unit over 50 m | Highest rounded mean | 7.5 |
| Starting, averaged level | $L_{p\mathrm{Aeq},T}$ | 25 m and 3,5 m, 10 m ahead of the unit | Highest rounded mean | 7.6 |
| Braking | $L_{p\mathrm{AFmax}}$, from 30 km/h | 7,5 m and 1,2 m, opposite the first car at standstill | Highest rounded mean | 8 |

Three runs are valid when they lie within 3 dB of each other (9.3). Only the
constant-speed test needs a reference track (6.2).

## How the measurement goes

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_rolling_stock_site_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_rolling_stock_site.svg" alt="Section across the track and plan of an ISO 3095 pass-by site: microphone A 7.5 m from the track centreline and 1.2 m above the top of rail, B at 7.5 m and 3.5 m, C at 25 m and 3.5 m for 200 km/h and above; in plan, the shaded triangle between the microphone and the track reaching 2d either side that must allow free propagation, and a circle of radius 3d free of large reflecting objects" width="92%"></picture>

| Requirement | Value | Clause |
| :--- | :--- | :--- |
| Microphone | 7,5 m from the track centreline, 1,2 m above the top of rail, both sides; 25 m and 3,5 m allowed from 200 km/h | 6.4.1 |
| Free propagation | The triangle to twice the microphone distance either side: ground 0 m to −2 m from the top of rail, no other track, no snow, water, ice, tarmac or concrete, nobody inside | 6.1.1 |
| Reflecting objects | None large within three times the measurement distance | 6.1.1 |
| Background | At least 10 dB under the pass-by level | 6.1.3 |
| Record | Starting and ending at least 10 dB below the level at the front and at the rear | 6.6.3 |
| Track | Roughness under Figure 2, decay rates over Figure 3, curve radius and gradient of 6.2.2 | 6.2 |

## 2. The pass-by level and the transit exposure level

The constant-speed quantity is $L_{p\mathrm{Aeq},T}$ over the pass-by time
$T_p = l/v$ of the unit (6.6.3). The 2005 edition also defined the transit
exposure level, the energy of the whole passage spread over the pass-by time,
$\mathrm{TEL} = L_{p\mathrm{Aeq},T} + 10 \lg (T/T_p)$ (ISO 3095:2005, 3.14,
Formula 10); Formula B.1 of the 2013 edition keeps the same form for a single
trailer, over the pass-by time of half the unit.

```python
import numpy as np
from phonometry import environment

fs = 16000
length_m, speed_kmh, distance_m = 100.0, 80.0, 7.5
tp = environment.pass_by_time(length_m, speed_kmh=speed_kmh)
t = np.arange(int(14.0 * fs)) / fs
front_s = 4.0
x_front = speed_kmh / 3.6 * (t - front_s)
angle = np.arctan(x_front / distance_m) - np.arctan((x_front - length_m) / distance_m)
rng = np.random.default_rng(3095)
p = 0.25 * np.sqrt(angle / np.pi + 1e-4) * rng.standard_normal(t.size)

passby = environment.pass_by_measurement(p, fs, start_s=front_s, end_s=front_s + tp)
print(round(tp, 2), round(passby.equivalent_level_db, 1), round(passby.max_level_db, 1))
# 4.5 81.3 81.9
whole = environment.pass_by_measurement(
    p, fs, start_s=0.0, end_s=14.0, pass_by_time_s=tp,
    front_passing_s=front_s, rear_passing_s=front_s + tp,
)
print(round(whole.equivalent_level_db, 1), round(whole.normalized_level_db, 1))
# 77.1 82.0   L_pAeq,T over the record, and TEL
```

## 3. Three runs and a rounded mean

`rolling_stock_test` averages the runs of each position, rounds the mean to
the integer (a half goes up) and keeps the highest; `stationary_test` averages
a set on energy weighted by length, $(\pi/2) \times 7{,}5$ m for the end
positions (Formulae 1 and 2). `type_test_speeds`, `minimum_curve_radius` and
`acceleration_test_positions` (Figure 10) state the small rules around them.

```python
test = environment.rolling_stock_test(
    {"left": [81.3, 82.1, 81.6], "right": [80.4, 80.9, 81.2]}
)
print(dict(test.reported_levels_db), test.final_level_db, test.valid)
# {'left': 82.0, 'right': 81.0} 82.0 True
print(environment.acceleration_test_positions(108.0))
# [-10.  17.  44.]
```

## 4. The reference track

**Rail roughness (EN 15610).** A record is cleared of narrow upward spikes
(7.2), raised to where a wheel of 0,375 m radius would rest (7.3), and turned into a
one-third octave band spectrum by Method A (7.4.2) with the band synthesis of
Annex C, $L_r = 10 \lg (r_\mathrm{RMS}^2 / r_0^2)$ with $r_0 = 1\ \mu$m. The
limit is Figure 2 of ISO 3095, which prints its twenty-two values beside the
points (`REFERENCE_TRACK_ROUGHNESS_LIMIT_DB`); the Annex B listing of EN 15610
prints them again.

**Track decay rate (EN 15461).** From the band magnitudes of the responses on
the hammer grid of Figure 2, Formula 1 gives
$\mathrm{DR} = 4{,}343 / \sum |A(x_n)|^2/|A(x_0)|^2\,\Delta x_n$ dB/m, with the floor
$\mathrm{DR}_\mathrm{min} = 4{,}343/x_\mathrm{max}$ of Formula 2. The limits are the table beside Figure 3
of ISO 3095 (`REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M`).

**The verdict.** `check_reference_track` judges both, and the curve radius and
gradient of 6.2.2, into one verdict read from `.passes` (it has no truth value
of its own). Annex C accepts a roughness over the limit when its effect on the
pass-by level is at most 1 dB (`check_small_roughness_deviations`, on the quadratic average of the rails, at the speed judged and against the limit judged), and Annex E
bounds what the roughness of two sites could change (`roughness_comparability`).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_track_roughness_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_track_roughness.svg" alt="Roughness level in dB re 1 µm of two rails against wavelength, with the Figure 2 limit falling from 17.1 dB at 40 cm to −11.0 dB at 0.315 cm; both rails lie under it except in the 4 cm to 2.5 cm bands, where one or both exceed it by up to 2.4 dB; the track passes through Annex C, with an effect of 0.57 dB" width="88%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_track_decay_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_track_decay.svg" alt="Vertical and lateral track decay rates in dB/m on a logarithmic axis from 100 Hz to 5 kHz, both above the Figure 3 lower limits drawn dashed" width="88%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_small_deviation_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_small_deviation.svg" alt="Measured and revised A-weighted pass-by spectra at 160 km/h, the revised one 0.7 dB to 1.6 dB lower at 1 kHz, 1.25 kHz and 1.6 kHz; the Annex C effect is 0.57 dB, accepted" width="88%"></picture>

## 5. The uncertainty of Annex G

$u = a/\sqrt{3}$ for an input known by its limits (Formula G.2),
$u_\mathrm{c} = \sqrt{\sum u^2}$ (Formula G.5) and $U = 2u_\mathrm{c}$ (Formula
G.6). `pass_by_uncertainty` reproduces the worked budget of Table G.2:
55,68 dB, 0,83 dB and 1,66 dB.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_uncertainty_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rolling_stock_uncertainty.svg" alt="Each input's share of the variance of the Table G.2 result, largest first, led by the level linearity of the meter, the tripod and the ground level; combined uncertainty 0.83 dB, expanded 1.66 dB" width="88%"></picture>

The printed tables disagree in three places (the 25 m distance of Table G.1
printed as 0,004 dB; the ground level at 7,5 m, 0,55 dB in Table G.1 and
0,30 dB in Table G.2; the wind screen interval with its bounds out of order),
and the spike-removal loop of the EN 15610 listing leaves out the change of
sign of 7.2 c) and never ends on a sharp bend of the rail; see the
[errata registry](../../ERRATA.md).

## What this page does not cover

The measurement itself (the stationary mesh, finding $T_1$ and $T_2$ inside a
train, the site and weather checks, Annex B beyond Formula B.1), the speed
normalisation of 6.7.1, which has no formula, the tonal difference of 6.7.2,
Annex F, the editing of rail defects and Method B of EN 15610, the measurement
of the frequency response functions of EN 15461, and the roughness of wheels.

## See also

- [CNOSSOS-EU railway source emission](cnossos-rail-emission.md): the
  prediction side, from roughness spectra to a sound power per metre.
- [Road-surface noise: the statistical pass-by method](road-surface-pass-by.md):
  the road's counterpart.
- [Errata in published sources](../../ERRATA.md): the ISO 3095 and EN 15610
  entries.
- API reference: [`environment.sources.rolling_stock_noise`](https://jmrplens.github.io/phonometry/reference/api/environment/rolling-stock-noise/).

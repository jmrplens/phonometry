← [Documentation index](README.md)

# Room and Building Acoustics

Room and building acoustics start from one measurement: the **impulse
response** (IR) between a source and a receiver. Filter it into bands and
integrate it, and it yields reverberation time, clarity and speech
intelligibility; measure it either side of a wall and it yields the sound
insulation of the partition. This page follows that chain in measurement
order — acquiring the IR (ISO 18233), turning it into room parameters
(ISO 3382-1/2), spatial speech metrics for open-plan offices
(ISO 3382-3), field airborne, impact and façade insulation with
single-number ratings (ISO 16283-1/2/3, ISO 717-1/2), the laboratory
characterisation of a building element (ISO 10140), the prediction of
in-situ performance from flanking transmission (EN 12354-1/2), the
measurement uncertainty that qualifies every rating (ISO 12999-1) and,
closing the loop, the sound absorption of a material in a reverberation
room (ISO 354).

## 1. Impulse-response acquisition (ISO 18233)

A room behaves, to a good approximation, as a **linear time-invariant**
system, so everything about it is contained in its IR. You could fire a
pistol and record the tail, but a deterministic excitation played through
a loudspeaker and *deconvolved* recovers the same IR with 20–30 dB more
effective signal-to-noise ratio (ISO 18233). Two excitations are provided.

**Exponential sine sweep (ESS, Annex B).** The instantaneous frequency
rises exponentially,

$$
f(t) = f_1 \left( \frac{f_2}{f_1} \right)^{t/T},
$$

so the time spent per octave is constant and the excitation mimics
pink noise (constant energy per fractional-octave band). The IR is
recovered by linear (zero-padded, non-circular) spectral division,

$$
H = \frac{Y\ \overline{X}}{|X|^2 + \varepsilon},
$$

with a small Tikhonov term $\varepsilon$ guarding the band edges where the
sweep has little energy. Because a low-to-high sweep places harmonic
distortion at *negative* arrival times, distortion separates cleanly from
the linear IR and is discarded by keeping only the causal part. The
`"farina"` method reaches the same result by convolving the recording with
the analytic inverse filter; it assumes the reference sweep was generated
with the default amplitude and fade, so use the spectral method for a
non-unit-amplitude or custom-fade sweep.

**Maximum-length sequence (MLS, Annex A).** An order-`N` binary sequence of
length $2^N-1$ whose circular autocorrelation is a near-perfect delta; the
IR follows from circular cross-correlation of the recorded period with the
sequence. MLS excites at constant amplitude and is quick to average, but it
is more sensitive to time variance (draughts, temperature drift) and cannot
be fed as much power as a sweep. **Prefer the sweep** for rooms and
partitions; reach for MLS when the excitation must be periodic or the
hardware favours a two-level signal.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement.svg" alt="ISO 18233 indirect measurement chain: an ESS sweep or MLS excitation drives a loudspeaker into the room, a microphone captures the response, and deconvolution (correlation or inverse filter) recovers the impulse response" width="92%"></picture>

```python
import numpy as np
from scipy.signal import fftconvolve
from phonometry import sweep_signal, impulse_response, mls_signal, mls_impulse_response

fs = 48000
# A 3 s, 20 Hz - 20 kHz sweep is a good broadband room excitation
# sweep: excitation you play through the loudspeaker
sweep = sweep_signal(fs, 20.0, 20000.0, 3.0)

# Deconvolve the recorded response back to the impulse response
system = np.zeros(fs); system[100] = 1.0; system[2000] = 0.4   # direct + reflection
# recorded: mic capture of the played sweep (here simulated by convolution with a synthetic room)
recorded = fftconvolve(sweep, system)
ir = impulse_response(recorded, sweep, fs, method="spectral")
print(int(np.argmax(np.abs(ir))))                    # 100: direct sound recovered

# Farina inverse-filter variant (needs the sweep band)
ir_f = impulse_response(recorded, sweep, fs, method="farina", f_range=(20.0, 20000.0))

# Periodic MLS: excite with >= 2 periods, average, cross-correlate
mls = mls_signal(16)                                 # length 2**16 - 1 = 65535
rec = fftconvolve(np.tile(mls, 2), system)[: 2 * mls.size]
ir_m = mls_impulse_response(rec, mls)
print(int(np.argmax(np.abs(ir_m))))                  # 100
```

### `sweep_signal()` / `inverse_filter()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `fs` | int | Hz | > 0 | Sampling frequency |
| `f1` | float | Hz | > 0, at/below lowest band | Sweep start frequency |
| `f2` | float | Hz | `f1 < f2 <= fs/2` | Sweep stop frequency |
| `seconds` | float | s | any; longer ⇒ more SNR | Sweep duration |
| `amplitude` | float | — | default `1.0` | Peak amplitude |
| `fade` | float | — | `[0, 0.5)`, default `0.01` | Half-Hann fade fraction (kills start/stop transients) |

### `impulse_response()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `recorded` | 1D array | any | non-empty | Recorded system response |
| `reference` | 1D array | any | non-empty | The emitted sweep |
| `fs` | int | Hz | > 0 | Sample rate |
| `method` | str | — | `'spectral'` (default) / `'farina'` | `'farina'` requires `f_range` |
| `f_range` | (float, float) | Hz | default `None` | `(f1, f2)` of the sweep (Farina only) |
| `regularization` | float | — | default `1e-6` | Tikhonov term as a fraction of peak spectral energy |
| `length` | int, optional | samples | default `len(recorded)` | Samples of causal IR to return |
| `return_full` | bool | — | default `False` | Return the full sequence (distortion in the tail) |

`mls_signal(order)` takes an integer `order` in 2–20 (sequence length
$2^{\text{order}}-1$); `mls_impulse_response(recorded, mls, length=None)`
needs `recorded` to span an integer number of MLS periods.

## 2. Decay analysis and room parameters (ISO 3382-1/2)

The IR is filtered into octave (or one-third-octave) bands and each band is
turned into a **decay curve** by Schroeder backward integration of the
squared IR:

$$
E(t) = \int_t^{\infty} p^2(\tau)\ d\tau, \qquad
L(t) = 10 \log_{10} \frac{E(t)}{E(0)}\ \text{dB}.
$$

Integrating *backwards* removes the fluctuation that plagues a raw squared
IR and yields a smooth curve whose slope is the decay rate. Background
noise would make $E(t)$ level off, so integration is truncated where the
fitted decay line crosses the noise floor and the missing tail is
compensated assuming an exponential decay.

Reverberation times come from a least-squares line fit over an evaluation
range, extrapolated to a full 60 dB drop, $T = -60/\text{slope}$:
**EDT** over 0 to −10 dB (perceived reverberance), **T20** over −5 to −25 dB
and **T30** over −5 to −35 dB. Energy splits at an early/late boundary give
**clarity** and **definition**,

$$
C_{te} = 10 \log_{10} \frac{\int_0^{te} p^2\ dt}{\int_{te}^{\infty} p^2\ dt}\ \text{dB}, \qquad
D_{50} = \frac{\int_0^{0.05} p^2\ dt}{\int_0^{\infty} p^2\ dt},
$$

with $te = 50$ ms → C50 (speech) and $te = 80$ ms → C80 (music), plus the
**centre time** $T_s = \int t\ p^2\ dt / \int p^2\ dt$. Each parameter has a
**just-noticeable difference** (ISO 3382-1 Table A.1: EDT 5 %, C80 1 dB,
D50 0.05, Ts 10 ms) that sets how precisely it is worth reporting.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay.png" alt="Squared impulse response with its Schroeder backward-integrated decay curve, and the EDT, T20 and T30 regression windows marked" width="80%"></picture>

*The jagged squared IR (grey) integrates to the smooth Schroeder curve
(blue); the EDT, T20 and T30 windows are fitted on that curve and each
extrapolated to a 60 dB decay.*

```python
import numpy as np
from phonometry import decay_curve, room_parameters

fs = 48000
# Single-slope decay with T = 1 s: p^2 = exp(-13.8155 t)  (60/ln(10)/13.8155 = 1)
t = np.arange(fs) / fs
# ir: measured room impulse response; a synthetic single-slope decay stands in here.
ir = np.concatenate([np.zeros(10), np.exp(-13.8155 * t / 2.0)])

time, level = decay_curve(ir, fs)                    # Schroeder curve (0 dB at t = 0)

res = room_parameters(ir, fs, limits=None)           # broadband single band
print(round(float(res.t30[0]), 2))                   # 1.0  s
print(round(float(res.c80[0]), 2))                   # 3.05 dB
print(round(float(res.d50[0]), 3))                   # 0.499
print(round(float(res.ts[0]) * 1000, 0))             # 72 ms

# Octave bands 125 Hz - 4 kHz (ISO 3382-1 default); use fraction=3 for thirds
octaves = room_parameters(ir, fs)
print(octaves.frequency)                             # ~[126, 251, 501, 1000, 1995, 3981]
print(octaves.t30_valid)                             # per-band dynamic-range flags

octaves.plot()               # per-band EDT/T20/T30 + C50/C80 bars (needs matplotlib)
decay_curve(ir, fs).plot()   # Schroeder decay with EDT/T20/T30 fit overlays
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# One line — Schroeder decay with the EDT/T20/T30 straight-line fits:
decay = decay_curve(ir, fs)          # a DecayCurve (still unpacks as time, level)
decay.plot()
plt.show()

# By hand, the decay is just the Schroeder curve; mark the evaluation levels:
fig, ax = plt.subplots()
ax.plot(time, level, color="#1f77b4", label="Schroeder decay")
for db in (-5.0, -25.0, -35.0):      # T20 / T30 evaluation-window edges
    ax.axhline(db, ls=":", alpha=0.4)
ax.set_xlabel("Time [s]")
ax.set_ylabel("Level re steady state [dB]")
ax.set_ylim(top=3.0)
ax.legend()
plt.show()
```

</details>

For this single-slope decay EDT, T20 and T30 all return ≈ 1.0 s, and the
energy parameters match their closed forms (C80 = 3.05 dB, D50 = 0.499,
Ts = 72 ms). A real room has a steeper early slope, so EDT < T30.

### `room_parameters()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `ir` | 1D array | any | non-silent | Measured impulse response |
| `fs` | int | Hz | > 0 | Sample rate |
| `limits` | (float, float) or `None` | Hz | default `(125.0, 4000.0)` | Band-centre limits; `None` = broadband single band |
| `fraction` | int | — | `1` (octave, default) / `3` (third) | Bandwidth fraction |
| `zero_phase` | bool | — | default `False` | Forward-backward octave filtering (ISO 3382-2 §7.3 NOTE, which relaxes $BT > 16$ to $BT > 4$); removes the filter group delay before the backward integration and roughly halves the 125 Hz short-decay T30 bias (~+4.9 % → +2.4 % at $T$ = 0.2 s). `decay_curve` accepts it too |

Returns a `RoomAcousticsResult`: `frequency` (band centres, or `None`
broadband), `edt`/`t20`/`t30` (s), `c50`/`c80` (dB), `d50`, `ts` (s),
`dynamic_range` (dB), the `edt_valid`/`t20_valid`/`t30_valid` flags (ISO
3382-1 §5.3.3: noise ≥ 25 dB below the peak for EDT, tightened to 46 dB for
T20 and 54 dB for T30 so the tail-compensation bias of a flagged-valid value
stays within the 5 % JND) and `curvature`
$C = 100\ (T_{30}/T_{20} - 1)$ % (values above 10 % flag a non-straight
decay). `decay_curve(ir, fs, band=None, fraction=1, zero_phase=False)` returns
just the `(time, level)` curve for one band or the broadband response.

## 3. Open-plan offices (ISO 3382-3)

Open-plan acoustics are about **speech privacy**: how fast a talker's speech
fades to unintelligibility as you walk away. Levels and STI are measured
along a line of workstations (at least 4 positions, 6–10 preferred), and
four single-number quantities summarise the room. The **spatial decay
rate** of A-weighted speech is the slope of the level against
$\lg(r/r_0)$, scaled to a per-doubling figure using only the 2–16 m
positions,

$$
D_{2,S} = -\lg(2)\ b, \qquad L = a + b\ \lg(r/r_0),\ r_0 = 1\ \text{m},
$$

with **Lp,A,S,4m** read off the same line at 4 m. The **distraction
distance** rD (STI = 0.50) and **privacy distance** rP (STI = 0.20) come
from a linear regression of STI against distance. Good offices push rD
below ~5 m; poor ones leave speech distracting past 10 m.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay.png" alt="Open-plan spatial decay: A-weighted speech level and STI against source distance on a log axis, with the D2,S regression, the Lp,A,S,4m marker at 4 m and the rD and rP distance crossings" width="80%"></picture>

```python
import numpy as np
from phonometry import open_plan_metrics

r = np.array([2.0, 4.0, 6.0, 8.0, 12.0, 16.0])       # distances from the talker (m)
lp = 65.0 - 7.0 * np.log2(r)                          # A-weighted speech level (dB)
sti = 0.70 - 0.03 * r                                 # STI per position

m = open_plan_metrics(r, lp, sti)
print(round(m.d2s, 1), round(m.lp_as_4m, 1))         # 7.0 dB, 51.0 dB
print(round(m.rd, 1), round(m.rp, 1))                # 6.7 m, 16.7 m
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# Spatial decay: measured Lp,A,S vs distance on a log axis, the D2,S
# regression rebuilt from the result fields, and STI with the rD / rP
# crossings on a twin axis:
b = -m.d2s / np.log10(2.0)                 # regression slope vs lg(r)
a = m.lp_as_4m - b * np.log10(4.0)         # intercept from the 4 m level
rr = np.logspace(np.log10(2.0), np.log10(16.0), 100)

fig, ax = plt.subplots()
ax.semilogx(r, lp, "o", label="Measured Lp,A,S")
ax.semilogx(rr, a + b * np.log10(rr), "--", label=f"D2,S = {m.d2s:.1f} dB")
ax.plot(4.0, m.lp_as_4m, "D", label=f"Lp,A,S,4m = {m.lp_as_4m:.0f} dB")
ax.set_xlabel("Distance from the talker r [m]")
ax.set_ylabel("A-weighted speech level [dB]")
ax.set_xlim(1.8, 20.0)

twin = ax.twinx()
twin.semilogx(r, sti, "s-", color="#2ca02c", label="STI")
twin.axvline(m.rd, ls=":", color="#2ca02c")
twin.axvline(m.rp, ls=":", color="#9467bd")
twin.annotate(f"rD = {m.rd:.1f} m", (m.rd, 0.52))
twin.annotate(f"rP = {m.rp:.1f} m", (m.rp, 0.22))
twin.set_ylabel("STI")
twin.set_ylim(0.0, 1.0)

lines, labels = ax.get_legend_handles_labels()
tl, tlab = twin.get_legend_handles_labels()
ax.legend(lines + tl, labels + tlab, loc="best")
plt.show()
```

</details>

### `open_plan_metrics()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `positions_m` | 1D array | m | ≥ 4 positions, all > 0 | Source-to-receiver distances |
| `spl_a_speech` | 1D array | dB | same length | A-weighted speech level `Lp,A,S,n` per position |
| `sti_values` | 1D array | — | same length | STI per position (full IEC 60268-16 method) |

Returns an `OpenPlanResult` with `d2s`, `lp_as_4m`, `rd` and `rp`.
`d2s`/`lp_as_4m` are `nan` if fewer than two positions fall in 2–16 m;
`rd`/`rp` are `nan` when STI does not decrease with distance. The per-position
STI can itself be measured with the STIPA tools in the
[Psychoacoustics guide](psychoacoustics.md).

## 4. Field insulation and single-number ratings (ISO 16283-1, ISO 717-1)

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating.png" alt="Measured one-third-octave sound reduction index with the shifted ISO 717-1 reference curve and the resulting weighted rating at 500 Hz" width="80%"></picture>

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating.png" alt="Measured one-third-octave normalized impact sound pressure level with the shifted ISO 717-2 reference curve and the resulting weighted rating read at 500 Hz" width="80%"></picture>

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

## 5. Laboratory measurement (ISO 10140)

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

## 6. Predicting performance (EN 12354)

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo.png" alt="Per-path sound reduction indices for the EN 12354-1 Annex H.3 example and each path's share of the transmitted energy, showing the direct path dominating at R'w = 52 dB" width="80%"></picture>

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

Every added flanking path strictly lowers $R'_w$ below the direct $R_{Dd,w} = 57$;
`res.paths` exposes each path's share of the transmitted energy so the dominant
path is visible. Clause 4.4.2 also enforces a floor $K_{ij} \ge K_{ij,\min}$ from
the junction geometry — compute it with `junction_min_vibration_reduction` and
pass it to `flanking_path(..., kij_min=...)`, which raises a below-floor $K_{ij}$
to the minimum:

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

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

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

`predicted_airborne_insulation()` returns an `AirbornePredictionResult`
(`r_prime_w`, `r_direct_w`, `paths` of `PathContribution`, `dominant`);
`predicted_impact_insulation()` an `ImpactPredictionResult` (`l_prime_n_w`,
`ln_w_eq`, `delta_l_w`, `k_correction`). The simplified model carries a reported
standard deviation of about 2 dB (Clause 5).

## 7. Measurement uncertainty (ISO 12999-1)

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo.png" alt="A weighted rating reported with its two-sided 95 % expanded uncertainty in situations A, B and C, the reproducibility uncertainty widest and the repeatability uncertainty narrowest" width="80%"></picture>

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

## 8. Sound absorption (ISO 354)

The equivalent absorption area `A` that drives `R'`, `L'n`, the ISO 3744 `K2`
environmental correction and the ISO 3741 absorption term is itself measured in
a reverberation room (ISO 354).
Measure the room's reverberation time **empty** ($T_1$) and again **with the
test specimen installed** ($T_2$); the specimen's absorption is the difference
of the two Sabine areas, and dividing by the covered area gives the absorption
coefficient:

$$
A = \frac{55.3\ V}{c\ T} - 4 V m, \qquad
\alpha_s = \frac{A_2 - A_1}{S}, \qquad c = 331 + 0.6\ t ,
$$

with $c$ from the room air temperature $t$ in °C (valid 15–30 °C) and $m$ the
power attenuation coefficient of air (default 0; convert an ISO 9613-1
$\alpha$ in dB/m with `attenuation_from_alpha`). Because edge and diffraction
effects can scatter more energy than the sample's flat area intercepts,
$\alpha_s$ may exceed 1.0 and is never clamped (ISO 354 Clause 3.7).

```python
import numpy as np
from phonometry import absorption_area, absorption_coefficient

# Third-octave reverberation times of a 200 m^3 room, empty (T1) and with a
# 10.8 m^2 absorber sample installed (T2).
t1 = np.array([5.0, 4.0, 3.0])
t2 = np.array([3.0, 2.5, 2.0])

a_empty = absorption_area(t1, volume=200.0, temperature=20.0)
print(np.round(a_empty, 2))                    # [ 6.45  8.06 10.75] m^2

alpha = absorption_coefficient(t1, t2, volume=200.0, sample_area=10.8,
                               temperature1=20.0)
print(np.round(alpha, 3))                      # [0.398 0.448 0.498]
```

`T1` and `T2` are exactly the reverberation times `room_parameters` returns, so
an ISO 3382-2 decay measurement of the empty and treated room flows straight
into `absorption_coefficient`. A room volume below the 150 m³ minimum or a
sample area outside 10–12 m² raises an advisory `AbsorptionWarning`; the result
still returns.

### `absorption_area()` / `absorption_coefficient()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `t60` / `t1`, `t2` | 1D array | s | > 0 | Reverberation time(s); `t1` empty, `t2` with specimen |
| `volume` | float | m³ | > 0 | Room volume `V` (advisory below 150 m³) |
| `sample_area` | float | m² | > 0 | Area `S` the specimen covers (coefficient only) |
| `temperature` / `temperature1`, `temperature2` | float | °C | default `20.0`, 15–30 | Sets `c` via Eq. (6); `temperature2` defaults to `temperature1` |
| `speed_of_sound` (`…1`, `…2`) | float, optional | m/s | > 0 | Overrides the temperature-derived `c` |
| `m` (`m1`, `m2`) | float or 1D array | 1/m | ≥ 0, default `0` | Air power attenuation coefficient |

`absorption_area()` returns the equivalent absorption area `A` (m²) with the
shape of `t60`; `absorption_coefficient()` returns `alpha_s`;
`attenuation_from_alpha(alpha)` converts an ISO 9613-1 `alpha` (dB/m) to `m`.

## See also

- [Sound Power](sound-power.md) — the `LW` methods that consume the ISO 354
  absorption area (the ISO 3744 `K2` and the ISO 3741 absorption term).

- [Psychoacoustics and Speech Intelligibility](psychoacoustics.md) — STI/STIPA
  feeds the open-plan `sti_values`; loudness and sharpness.
- [Filter Banks](filter-banks.md) — the IEC 61260 fractional-octave filters
  used for band decay curves and insulation spectra.
- [Levels](levels.md) — energy averaging and the level metrics behind
  source/receiving-room levels.
- [Theory](theory.md) — Schroeder integration, regression windows and the
  reference-curve derivation.

---
title: "Room & Building Acoustics"
description: "Impulse-response acquisition (ISO 18233), room parameters EDT/T20/T30/C50/C80/Ts (ISO 3382-1/2), open-plan speech metrics (ISO 3382-3) and field sound insulation with weighted ratings (ISO 16283-1, ISO 717-1)."
---

Room and building acoustics start from one measurement: the **impulse
response** (IR) between a source and a receiver. Filter it into bands and
integrate it, and it yields reverberation time, clarity and speech
intelligibility; measure it either side of a wall and it yields the sound
insulation of the partition. This page follows that chain in measurement
order — acquiring the IR (ISO 18233), turning it into room parameters
(ISO 3382-1/2), spatial speech metrics for open-plan offices
(ISO 3382-3), and finally field insulation and single-number ratings
(ISO 16283-1, ISO 717-1).

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement.svg" alt="ISO 18233 indirect measurement chain: an ESS sweep or MLS excitation drives a loudspeaker into the room, a microphone captures the response, and deconvolution (correlation or inverse filter) recovers the impulse response" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement_dark.svg" alt="ISO 18233 indirect measurement chain: an ESS sweep or MLS excitation drives a loudspeaker into the room, a microphone captures the response, and deconvolution (correlation or inverse filter) recovers the impulse response" style="width:92%">

```python
import numpy as np
from scipy.signal import fftconvolve
from phonometry import sweep_signal, impulse_response, mls_signal, mls_impulse_response

fs = 48000
# A 3 s, 20 Hz - 20 kHz sweep is a good broadband room excitation
sweep = sweep_signal(fs, 20.0, 20000.0, 3.0)

# Deconvolve the recorded response back to the impulse response
system = np.zeros(fs); system[100] = 1.0; system[2000] = 0.4   # direct + reflection
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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay.png" alt="Squared impulse response with its Schroeder backward-integrated decay curve, and the EDT, T20 and T30 regression windows marked" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay_dark.png" alt="Squared impulse response with its Schroeder backward-integrated decay curve, and the EDT, T20 and T30 regression windows marked" style="width:80%">

*The jagged squared IR (grey) integrates to the smooth Schroeder curve
(blue); the EDT, T20 and T30 windows are fitted on that curve and each
extrapolated to a 60 dB decay.*

```python
import numpy as np
from phonometry import decay_curve, room_parameters

fs = 48000
# Single-slope decay with T = 1 s: p^2 = exp(-13.8155 t)  (60/ln(10)/13.8155 = 1)
t = np.arange(fs) / fs
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
```

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay.png" alt="Open-plan spatial decay: A-weighted speech level and STI against source distance on a log axis, with the D2,S regression, the Lp,A,S,4m marker at 4 m and the rD and rP distance crossings" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay_dark.png" alt="Open-plan spatial decay: A-weighted speech level and STI against source distance on a log axis, with the D2,S regression, the Lp,A,S,4m marker at 4 m and the rD and rP distance crossings" style="width:80%">

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
[Psychoacoustics guide](/phonometry/guides/psychoacoustics/).

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup.svg" alt="Field airborne insulation setup: a loudspeaker in the source room, microphones energy-averaged in source and receiving rooms across the common partition" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup_dark.svg" alt="Field airborne insulation setup: a loudspeaker in the source room, microphones energy-averaged in source and receiving rooms across the common partition" style="width:92%">

The band spectrum is collapsed to one number by the **reference-curve
method** of ISO 717-1: a fixed reference curve is shifted in 1 dB steps
toward the measured curve until the sum of *unfavourable* deviations
(where the measurement falls below the reference) is as large as possible
but not more than 32.0 dB (16 one-third-octave bands) or 10.0 dB (5 octave
bands). The rating (`Rw`, `R'w`, `DnT,w` …) is the shifted reference read at
500 Hz. The **spectrum adaptation terms** $C$ (pink noise) and $C_{tr}$
(urban traffic) add the low-frequency penalty of a real source.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating.png" alt="Measured one-third-octave sound reduction index with the shifted ISO 717-1 reference curve and the resulting weighted rating at 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_dark.png" alt="Measured one-third-octave sound reduction index with the shifted ISO 717-1 reference curve and the resulting weighted rating at 500 Hz" style="width:80%">

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
```

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

## See also

- [Psychoacoustics and Speech Intelligibility](/phonometry/guides/psychoacoustics/) — STI/STIPA
  feeds the open-plan `sti_values`; loudness and sharpness.
- [Filter Banks](/phonometry/guides/filter-banks/) — the IEC 61260 fractional-octave filters
  used for band decay curves and insulation spectra.
- [Levels](/phonometry/guides/levels/) — energy averaging and the level metrics behind
  source/receiving-room levels.
- [Theory](/phonometry/reference/theory/) — Schroeder integration, regression windows and the
  reference-curve derivation.

---
title: "Room Acoustics"
description: "Impulse-response acquisition (ISO 18233), room parameters EDT/T20/T30/C50/C80/Ts (ISO 3382-1/2), open-plan speech metrics (ISO 3382-3) and sound absorption in a reverberation room (ISO 354)."
---

Room acoustics starts from one measurement: the **impulse response** (IR)
between a source and a receiver. Filter it into bands and integrate it, and
it yields reverberation time, clarity and speech intelligibility — everything
about the sound field inside a single room. This page follows that chain in
measurement order — acquiring the IR (ISO 18233), turning it into room
parameters (ISO 3382-1/2), spatial speech metrics for open-plan offices
(ISO 3382-3) and, closing the loop, the sound absorption of a material in a
reverberation room (ISO 354). For sound insulation *between* spaces — the same
IR measured either side of a partition — see the companion
[Building Acoustics & Sound Insulation guide](/phonometry/guides/building-acoustics/).

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

`sweep_signal`/`mls_signal` return plain arrays, ready to write to a WAV file
and play. `impulse_response`/`mls_impulse_response` return an
`ImpulseResponseResult` — a drop-in for the raw IR array (`np.asarray(ir)`,
indexing and `ir.size` all keep working, so `room_parameters(ir, fs)` is
unchanged) that also carries the sample rate and method and adds an `.plot()`.

**The two excitations.** The exponential sweep sweeps its energy up the
spectrum over the whole signal, while the MLS is a flat-spectrum two-level
sequence — visible as the near-constant magnitude on the right.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/excitation_signals.png" alt="ISO 18233 excitation signals: the exponential sine sweep waveform and its spectrogram showing the exponential frequency rise, and a maximum-length sequence with its flat magnitude spectrum" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/excitation_signals_dark.png" alt="ISO 18233 excitation signals: the exponential sine sweep waveform and its spectrogram showing the exponential frequency rise, and a maximum-length sequence with its flat magnitude spectrum" style="width:96%">

<details>
<summary>Show the code for this figure</summary>

```python
from phonometry import sweep_signal, mls_signal, plot_excitation

fs = 48000
sweep = sweep_signal(fs, 50.0, 20000.0, 1.0)   # ESS excitation
mls = mls_signal(12).astype(float)             # length 2**12 - 1

# One-liner: waveform + spectrogram (sweep), sequence + flat spectrum (MLS)
plot_excitation(sweep, fs, kind="sweep")
plot_excitation(mls, fs, kind="mls")

# By hand: the sweep spectrogram and the MLS magnitude spectrum
import numpy as np
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.specgram(sweep, NFFT=1024, Fs=fs, noverlap=512)
ax1.set(xlabel="Time [s]", ylabel="Frequency [Hz]", title="Sweep spectrogram")
spec = np.abs(np.fft.rfft(mls))
freqs = np.fft.rfftfreq(mls.size, d=1.0 / fs)
ax2.semilogx(freqs[1:], 20 * np.log10(spec[1:] / np.median(spec[1:])))
ax2.set(xlabel="Frequency [Hz]", ylabel="Magnitude [dB]", title="MLS spectrum (flat)")
```

</details>

**The recovered impulse response.** Deconvolving the recording gives the
broadband IR: the direct sound, discrete early reflections and the decaying
diffuse tail. Its `.plot()` shows the waveform above and the log-magnitude
envelope with the Schroeder energy-decay curve below — the straight decay
whose slope becomes the reverberation time in §2.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_response.png" alt="Recovered room impulse response: the normalized waveform with the direct sound and reflections labelled, and below it the log-magnitude envelope in dB with the Schroeder energy-decay curve" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_response_dark.png" alt="Recovered room impulse response: the normalized waveform with the direct sound and reflections labelled, and below it the log-magnitude envelope in dB with the Schroeder energy-decay curve" style="width:88%">

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
from scipy.signal import fftconvolve
from phonometry import sweep_signal, impulse_response

fs = 48000
sweep = sweep_signal(fs, 20.0, 20000.0, 1.5)
# A synthetic room: direct sound + two reflections + a decaying diffuse tail
system = np.zeros(int(0.7 * fs))
system[80], system[1400], system[3100] = 1.0, 0.5, 0.32
ir = impulse_response(fftconvolve(sweep, system), sweep, fs, length=system.size)

# One-liner: waveform + log-magnitude / Schroeder decay
ir.plot()

# By hand: the normalized log-magnitude envelope in dB
import matplotlib.pyplot as plt
h = np.asarray(ir)
t = np.arange(h.size) / fs
plt.plot(t, 20 * np.log10(np.abs(h) / np.max(np.abs(h))))
plt.ylim(-80, 5)
plt.xlabel("Time [s]"); plt.ylabel("Level re peak [dB]")
```

</details>

**Where to measure.** One IR characterises a single source–receiver pair; a
reported room parameter is the spatial average over several. ISO 3382-1
(performance spaces) asks for at least two source positions and microphones
spaced $\geq 2$ m apart, $\geq 1$ m from any surface, at $1.2$ m
(seated-ear) height, avoiding symmetric placements; ISO 3382-2 fixes the
minimum number of source, microphone and source–microphone combinations per
accuracy grade (survey / engineering / precision).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_measurement.svg" alt="Room-acoustics measurement setup: a top-view room plan with two loudspeaker source positions and six microphone positions with the ISO 3382-1 spacing rules, and the ISO 3382-2 table of minimum positions for the survey, engineering and precision grades" style="width:94%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_measurement_dark.svg" alt="Room-acoustics measurement setup: a top-view room plan with two loudspeaker source positions and six microphone positions with the ISO 3382-1 spacing rules, and the ISO 3382-2 table of minimum positions for the survey, engineering and precision grades" style="width:94%">

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_open_plan.svg" alt="ISO 3382-3 open-plan measurement line from the source at 1 m along positions from 2 m to 16 m, feeding the four single-number quantities D2,S, Lp,A,S,4m, rD and rP" style="width:86%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_open_plan_dark.svg" alt="ISO 3382-3 open-plan measurement line from the source at 1 m along positions from 2 m to 16 m, feeding the four single-number quantities D2,S, Lp,A,S,4m, rD and rP" style="width:86%">

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

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# One line: the D2,S regression rebuilt from the result fields, with the
# rD / rP crossings marked (the figure above adds the measured points and
# the STI axis on top of it):
m.plot()
plt.show()
```

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

Returns an `OpenPlanResult` with `d2s`, `lp_as_4m`, `rd` and `rp`; its
`.plot()` redraws the Clause 6.2 spatial-decay regression from those four
fields and marks `rd` / `rp`.
`d2s`/`lp_as_4m` are `nan` if fewer than two positions fall in 2–16 m;
`rd`/`rp` are `nan` when STI does not decrease with distance. The per-position
STI can itself be measured with the STIPA tools in the
[Speech Transmission Index guide](/phonometry/guides/speech-transmission/).

## 4. Sound absorption (ISO 354)

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

- [Building Acoustics & Sound Insulation](/phonometry/guides/building-acoustics/) — field,
  laboratory and predicted sound insulation between spaces, and its measurement uncertainty.
- [Sound Power](/phonometry/guides/sound-power/) — the `LW` methods that consume the
  ISO 354 absorption area (the ISO 3744 `K2` and the ISO 3741 absorption term).
- [Speech Transmission Index](/phonometry/guides/speech-transmission/) — the STI/STIPA
  measurement that feeds the open-plan `sti_values`.
- [Psychoacoustics](/phonometry/guides/psychoacoustics/) — loudness, sharpness and the other
  perception metrics of what the room delivers.
- [Filter Banks](/phonometry/guides/filter-banks/) — the IEC 61260 fractional-octave filters
  used for band decay curves and insulation spectra.
- [Levels](/phonometry/guides/levels/) — energy averaging and the level metrics behind
  source/receiving-room levels.
- [Theory](/phonometry/reference/theory/) — Schroeder integration, regression windows and the
  reference-curve derivation.

---

**Standards.** ISO 18233:2006 (application of new measurement methods — the
swept-sine and MLS acquisition of impulse responses); ISO 3382-1:2009 and
ISO 3382-2:2008 (reverberation time and room parameters from the Schroeder
decay); ISO 3382-3:2012 (open-plan office speech metrics); ISO 354:2003
(sound absorption in a reverberation room). Validated against closed-form
decays and the standards' own parameter definitions in the
[conformance report](https://github.com/jmrplens/phonometry/blob/main/docs/CONFORMANCE.md).

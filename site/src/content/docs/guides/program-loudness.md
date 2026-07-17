---
title: "Programme loudness and true peak (ITU-R BS.1770 / EBU R 128)"
description: "The ITU-R BS.1770-5 programme-loudness algorithm and the EBU R 128 normalisation practice: K-weighting, gated integrated loudness in LUFS, the EBU Mode momentary and short-term meters of Tech 3341, the Tech 3342 loudness range and the oversampled true-peak level in dBTP."
---

**ITU-R BS.1770-5** defines how broadcast and streaming measure the loudness
of a programme: **K-weighting**, mean-square power in **gated 400 ms blocks**
and a channel-weighted sum, reported in **LKFS/LUFS**. **EBU R 128** builds
the normalisation practice on top of it (every programme is levelled to
**−23.0 LUFS** with a true-peak ceiling of **−1 dBTP**), and its companions
EBU Tech 3341 and Tech 3342 add the *EBU Mode* meter (momentary, short-term
and integrated loudness) and the *loudness range* (LRA). phonometry
implements the full chain in the `broadcast` namespace and validates every
synthesizable EBU test signal against its official tolerance.

## 1. K-weighting and the loudness measure (Annex 1)

The signal first passes a two-stage pre-filter: a ~+4 dB high-frequency
shelf modelling the head as a rigid sphere, then the RLB high-pass. The
concatenation is the **K-weighting**. The loudness over an interval is the
channel-weighted sum of the mean-square powers $z_i$ (Formula 2):

$$
L_K = -0.691 + 10 \log_{10} \sum_i G_i\, z_i \quad \text{LKFS},
$$

where the constant cancels the K-weighting gain at 997 Hz and $G_i$ weighs
each channel (1.0 for the front channels, 1.41 for the surrounds, LFE
excluded, Table 3). The Recommendation anchors the scale: a 0 dB FS 997 Hz
sine on one front channel reads −3.01 LKFS. The unit is written LKFS by the
ITU and LUFS by the EBU; they are identical, and 1 LU is 1 dB.

```python
import numpy as np
from phonometry import broadcast

fs = 48000
t = np.arange(20 * fs) / fs
x = np.zeros((5, t.size))                     # L, R, C, Ls, Rs
x[0] = np.sin(2 * np.pi * 997.0 * t)          # 0 dB FS on the left channel
print(round(broadcast.integrated_loudness(x, fs), 2))   # -3.01  LKFS
```

The biquad coefficients are tabulated at 48 kHz (Tables 1-2) and returned
verbatim at that rate; any other rate re-derives them through the analog
prototype so the response matches the specification (within 0.02 dB at
32 kHz and above; rates below 16 kHz are rejected):

```python
import numpy as np
from phonometry import broadcast

(b1, a1), (b2, a2) = broadcast.k_weighting_coefficients(48000)
print(b1)   # [ 1.53512486 -2.69169619  1.19839281]  (Table 1, verbatim)
y = broadcast.k_weighting(np.random.default_rng(0).standard_normal(48000),
                          48000)              # the filtered signal itself
```

## 2. Gating and the programme loudness

The **integrated** (programme) loudness divides the measurement into gating
blocks of 400 ms overlapping 75 % and gates them twice (Formulae 3-7):
blocks below the absolute threshold **−70 LKFS** are dropped; the loudness
of the survivors minus 10 LU sets the **relative threshold**, and the blocks
above both gates define the result. The gate keeps long quiet passages
(atmosphere, pauses, applause tails) from dragging the level of the
foreground down:

```python
import numpy as np
from phonometry import broadcast

fs = 48000
def tone(level_dbfs, seconds):
    t = np.arange(int(seconds * fs)) / fs
    return 10 ** (level_dbfs / 20) * np.sin(2 * np.pi * 1000.0 * t)

# 10 s of programme at -23 dBFS followed by 30 s of quiet ambience.
x = np.concatenate([tone(-23.0, 10.0), tone(-50.0, 30.0)])
res = broadcast.program_loudness(np.vstack([x, x]), fs)
print(round(res.integrated, 1))            # -23.1  LUFS (the tail is gated)
print(round(res.relative_threshold, 1))    # -39.0  LUFS
```

An ungated mean over the same 40 s would sit near −29 LUFS: the gating is
what makes wide-loudness-range programmes match on air. EBU R 128 normalises
this integrated value to **−23.0 LUFS**; where the target is not practically
achievable (live programmes, for example) a tolerance of ±1.0 LU is
permitted, and quality-control workflows allow ±0.2 LU for measurement
error.

## 3. EBU Mode: momentary, short-term, integrated

EBU Tech 3341 defines the three time scales of a compliant meter, and one
call computes them all:

* **Momentary (M)**: sliding 400 ms window, no gating;
* **Short-term (S)**: sliding 3 s window, no gating;
* **Integrated (I)**: the gated programme loudness above,

plus **Max M** and **Max S**, the true peak and the LRA:

```python
import numpy as np
from phonometry import broadcast

fs = 48000
def tone(level_dbfs, seconds):
    t = np.arange(int(seconds * fs)) / fs
    return 10 ** (level_dbfs / 20) * np.sin(2 * np.pi * 1000.0 * t)

# EBU Tech 3341 test case 3: -36 / -23 / -36 dBFS steps.
x = np.concatenate([tone(-36.0, 10.0), tone(-23.0, 60.0), tone(-36.0, 10.0)])
res = broadcast.program_loudness(np.vstack([x, x]), fs)
print(round(res.integrated, 1), round(res.max_momentary, 1),
      round(res.max_short_term, 1))         # -23.0 -23.0 -23.0
```

The frozen `ProgramLoudnessResult` carries the M and S series with their
time axes, the maxima, the thresholds, the LRA with its percentile edges,
the per-channel true peaks and the channel weights; its `.plot()` draws the
loudness trace of the programme:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/program_loudness.svg" alt="EBU R 128 metering of a one-minute synthetic programme with ambience, dialogue, music and fade-out sections: the grey momentary loudness breathes around the blue short-term trace, the red dashed integrated loudness sits exactly on the -23 LUFS target, and a shaded band marks the loudness range between its 10th and 95th percentile edges" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/program_loudness_dark.svg" alt="EBU R 128 metering of a one-minute synthetic programme with ambience, dialogue, music and fade-out sections: the grey momentary loudness breathes around the blue short-term trace, the red dashed integrated loudness sits exactly on the -23 LUFS target, and a shaded band marks the loudness range between its 10th and 95th percentile edges" style="width:96%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from phonometry import broadcast

fs = 48000
rng = np.random.default_rng(1770)
sos = signal.butter(2, 2000.0, fs=fs, output="sos")
chunks = []
for level, seconds in [(-38, 8), (-23, 16), (-17, 12), (-25, 16), (-45, 8)]:
    noise = signal.sosfilt(sos, rng.standard_normal(int(seconds * fs)))
    noise /= np.sqrt(np.mean(noise ** 2))
    t = np.arange(noise.size) / fs
    wobble = 1 + 0.22 * np.sin(2 * np.pi * 0.9 * t) \
        + 0.14 * np.sin(2 * np.pi * 2.83 * t + 1.0)
    chunks.append(10 ** (level / 20) * noise * wobble)
x = np.concatenate(chunks)

# Normalise the programme to the R 128 target, then meter it.
gain = -23.0 - broadcast.integrated_loudness(np.vstack([x, x]), fs)
x *= 10 ** (gain / 20)
broadcast.program_loudness(np.vstack([x, x]), fs).plot()
plt.show()
```

</details>

## 4. Loudness range (EBU Tech 3342)

The **loudness range** quantifies how much the loudness varies on a
macroscopic time scale, in LU. It is the spread between the **10th and 95th
percentiles** of the short-term loudness distribution after a cascaded gate:
an absolute threshold at −70 LUFS, then a relative threshold **−20 LU**
below the level of what survived (deliberately deeper than the −10 LU of
the integrated measure, so quiet-but-real foreground still counts). The
percentiles keep a single gunshot or a fade-out from inflating the value:

```python
import numpy as np
from phonometry import broadcast

fs = 48000
def tone(level_dbfs, seconds):
    t = np.arange(int(seconds * fs)) / fs
    return 10 ** (level_dbfs / 20) * np.sin(2 * np.pi * 1000.0 * t)

# EBU Tech 3342 test case 1: 20 s at -20 dBFS, then 20 s at -30 dBFS.
x = np.concatenate([tone(-20.0, 20.0), tone(-30.0, 20.0)])
res = broadcast.program_loudness(np.vstack([x, x]), fs)
print(round(res.loudness_range, 1))         # 10.0  LU
```

`loudness_range()` is also available standalone on any short-term loudness
vector, following the Tech 3342 reference implementation (including its
nearest-rank percentile indexing). The EBU does not recommend LRA for
programmes shorter than a minute: too few 3 s windows.

## 5. True peak (Annex 2)

Digital sample peaks lie: the true maximum of the reconstructed waveform
generally falls *between* samples, and a sample-peak meter under-reads a
badly phased tone at $f_s/4$ by 3 dB (worst case
$20\log_{10}\cos(\pi f_{\mathrm{norm}}/n)$ for oversampling ratio $n$).
BS.1770-5 Annex 2 therefore meters the **true peak** on a signal oversampled
to at least 192 kHz (4× at 48 kHz), in **dBTP** (dB relative to 100 % full
scale):

```python
import numpy as np
from phonometry import broadcast

fs = 48000
t = np.arange(fs) / fs
# A full-scale fs/4 tone whose peaks fall exactly between samples.
x = np.sin(2 * np.pi * (fs / 4) * t + np.pi / 4)
print(round(float(broadcast.true_peak_level(x, fs, oversample=1)), 2))  # -3.01
print(round(float(broadcast.true_peak_level(x, fs)), 2))                #  0.12
```

The interpolator recovers the inter-sample excursion the sample grid missed
(the residual +0.12 dB is interpolation ripple from the abrupt tone edges,
inside the +0.2/−0.4 dB tolerance that EBU Mode meters must meet).
EBU R 128 caps production at **−1 dBTP**; distribution codecs often need
more headroom. This is the same oversampled-peak machinery behind the
C-weighted `lc_peak` of
[Integrated & Statistical Levels](/phonometry/guides/levels/).

## 6. Multichannel programmes and Annex 3

With 1, 2, 5 or 6 channels the Table 3 weights apply automatically (channel
order `L, R, C, Ls, Rs`, or `L, R, C, LFE, Ls, Rs` with the LFE excluded).
For any other loudspeaker layout (22.2, 4+7+0 and the rest of the BS.2051
advanced sound systems), Annex 3 derives the weight of each channel from its
loudspeaker position: 1.41 (+1.5 dB) for mid-layer side loudspeakers
(60° ≤ |azimuth| ≤ 120°, |elevation| < 30°), 1.0 elsewhere:

```python
from phonometry import broadcast

print(broadcast.channel_weight(110.0, 0.0))    # 1.41  (M+110, side)
print(broadcast.channel_weight(110.0, 35.0))   # 1.0   (U+110, upper layer)
weights = broadcast.channel_weight([0, 30, -30, 90, -90], [0, 0, 0, 0, 0])
# -> [1. 1. 1. 1.41 1.41]; pass as program_loudness(..., weights=weights)
```

Object-based audio (Annex 4) is measured by rendering to a loudspeaker
configuration first and metering the render; the rendering itself is out of
scope here.

## 7. Validation

Every synthesizable "minimum requirements" signal of EBU Tech 3341 (cases
1-6 and 9-23) and Tech 3342 (cases 1-4) runs in the test suite with its
official tolerance (±0.1 LU for loudness, +0.2/−0.4 dB for true peak, ±1 LU
for LRA), alongside the 997 Hz anchor and the closed-form under-read bound
of Annex 2 Attachment 1. Cases 7-8 and the LRA cases 5-6 use authentic
programme material distributed by the EBU and are not synthesizable; they
run against the official EBU loudness test set (fetched from the EBU, whose
licence covers technical testing only, so the audio is never committed) and
all four pass within tolerance. The
independent [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) meter is
a useful cross-check for real recordings; it was not used as a source for
this implementation.

## References

- International Telecommunication Union. (2023). *Algorithms to measure
  audio programme loudness and true-peak audio level* (Recommendation
  ITU-R BS.1770-5).
  [ITU-R publication](https://www.itu.int/rec/R-REC-BS.1770).
  The K-weighting, channel weights, gating and true-peak algorithms.
- European Broadcasting Union. (2023). *Loudness normalisation and permitted
  maximum level of audio signals* (EBU R 128).
  [tech.ebu.ch/publications/r128](https://tech.ebu.ch/publications/r128).
  The −23.0 LUFS target, the −1 dBTP ceiling and the normalisation practice.
- European Broadcasting Union. (2023). *Loudness metering: 'EBU Mode'
  metering to supplement loudness normalisation* (EBU Tech 3341).
  [tech.ebu.ch/publications/tech3341](https://tech.ebu.ch/publications/tech3341).
  The M/S/I time scales and the minimum-requirements test signals.
- European Broadcasting Union. (2023). *Loudness range: A measure to
  supplement loudness normalisation* (EBU Tech 3342).
  [tech.ebu.ch/publications/tech3342](https://tech.ebu.ch/publications/tech3342).
  The LRA algorithm, its reference implementation and its test signals.
- European Broadcasting Union. (2023). *Guidelines for production of
  programmes in accordance with EBU R 128* (EBU Tech 3343).
  [tech.ebu.ch/publications/tech3343](https://tech.ebu.ch/publications/tech3343).
  The production practice around the numbers on this page.
- Steinmetz, C. J., & Reiss, J. D. (2021). *pyloudnorm: A simple yet
  flexible loudness meter in Python*. 150th AES Convention.
  [github.com/csteinmetz1/pyloudnorm](https://github.com/csteinmetz1/pyloudnorm).
  An independent BS.1770 implementation, useful as a cross-check.

## Standards

ITU-R BS.1770-5 (11/2023), *Algorithms to measure audio programme loudness
and true-peak audio level*: the K-weighting pre-filter (Annex 1, Tables
1-2), the channel-weighted loudness and two-stage gating (Annex 1, Formulae
1-7, Table 3), the true-peak estimation guidelines (Annex 2 and its
Attachment 1 under-read bound) and the position-dependent channel weights
for advanced sound systems (Annex 3, Tables 4-5). EBU R 128 (2023),
*Loudness normalisation and permitted maximum level of audio signals*: the
−23.0 LUFS target level and −1 dBTP maximum. EBU Tech 3341 (2023): the EBU
Mode momentary/short-term/integrated time scales, validated against the
synthesizable Table 1 minimum-requirements signals with their official
tolerances. EBU Tech 3342 (2023): the loudness range, validated against its
Table 1 signals at ±1 LU.

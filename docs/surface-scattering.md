← [Documentation index](README.md)

# Surface Scattering, Diffusion and In-situ Absorption

How a surface returns incident sound — how much it scatters away from the
specular direction, how uniformly it spreads what it scatters, and how much it
absorbs — is measured by a family of dedicated methods. The **reverberation
room** gives the random-incidence *scattering coefficient* of a surface by
comparing decays with the sample held still and rotating (ISO 17497-1). A
**free-field goniometer** measures the polar response of the reflected sound and
condenses it into a *diffusion coefficient* (ISO 17497-2). And out on a road, a
loudspeaker and a single microphone recover the *in-situ absorption* of the
pavement, either over an extended surface by subtracting the incident wave
(ISO 13472-1) or through a small tube pressed onto the surface (ISO 13472-2).
This page covers all four.

The scattering and diffusion coefficients answer different questions and are not
interchangeable: scattering is *how much* energy leaves the specular direction;
diffusion is *how evenly* the reflected energy is spread over angle.

## 1. Random-incidence scattering coefficient (ISO 17497-1)

The scattering coefficient $s$ is the fraction of reflected energy that does
**not** leave the surface in the specular direction. ISO 17497-1 measures it in a
reverberation room from four reverberation-time situations: with the test sample
mounted on a turntable and held **stationary**, and with the turntable
**rotating** (which averages the phase-coherent specular reflection away), each
with and without a reflecting base plate.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_scattering_reverb_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_scattering_reverb.svg" alt="ISO 17497-1 random-incidence scattering setup: a reverberation room with the test sample on a turntable, a rotating loudspeaker boom and a microphone, measuring reverberation time with the sample stationary (giving the random-incidence absorption) and rotating (giving the specular absorption), from which the scattering coefficient is derived" width="92%"></picture>

**Absorption from reverberation time (Clause 6).** Each situation converts to a
Sabine absorption coefficient with the standard's own air-attenuation term:

$$
\alpha = 55.3\,\frac{V}{S}\left(\frac{1}{c_2 T_2} - \frac{1}{c_1 T_1}\right)
        - 4\,\frac{V}{S}\,(m_2 - m_1),
$$

where $V$ is the room volume, $S$ the sample area, $T$ the reverberation time,
$c$ the speed of sound (Eq. (2): $c = 343.2\sqrt{(273.15+t)/293.15}$) and $m$ the
power attenuation coefficient of air. The **stationary** pair gives the
random-incidence absorption $\alpha_s$ (Eq. (1)); the **rotating** pair gives the
specular absorption $\alpha_{spec}$ (Eq. (4)).

**Scattering coefficient (Eq. (5)).** The two combine into

$$
s = \frac{\alpha_{spec} - \alpha_s}{1 - \alpha_s}.
$$

A fully specular surface reflects all its non-absorbed energy in the specular
direction, so $\alpha_{spec} = \alpha_s$ and $s = 0$; a strong diffuser sends
energy everywhere, raising $\alpha_{spec}$ towards 1 and $s$ towards 1.

```python
import phonometry as ph

# Four reverberation-time situations reduced to two absorption coefficients.
# alpha_s from the stationary pair (Eq. 1); alpha_spec from the rotating pair
# (Eq. 4). V = 200 m^3, S = 10 m^2, c = 343.2 m/s throughout.
alpha_s = ph.random_incidence_absorption(200.0, 10.0, c1=343.2, T1=8.0,
                                         c2=343.2, T2=6.0)
alpha_spec = ph.specular_absorption_coefficient(200.0, 10.0, c3=343.2, T3=7.5,
                                                c4=343.2, T4=5.0)
s = ph.scattering_coefficient(alpha_spec, alpha_s)   # Eq. (5)
print(round(float(alpha_s), 4))     # 0.1343
print(round(float(alpha_spec), 4))  # 0.2148
print(round(float(s), 4))           # 0.0931
```

**Base-plate check (Clause 6.4, Table 1).** The empty base plate must itself
scatter only negligibly, or it would bias the result. ISO 17497-1 caps the
base-plate scattering coefficient per one-third-octave band; the library exposes
those limits and a checker.

```python
from phonometry import (
    BASE_PLATE_BANDS_HZ, BASE_PLATE_MAX_SCATTERING, check_base_plate_scattering,
)

# The normative per-band ceilings (Table 1): 0.05 up to 500 Hz, rising to 0.25.
# BASE_PLATE_BANDS_HZ is the band tuple; BASE_PLATE_MAX_SCATTERING maps band -> ceiling.
print(BASE_PLATE_BANDS_HZ[0], BASE_PLATE_MAX_SCATTERING[100])   # 100 0.05

# A base plate whose measured scattering stays under the ceiling passes silently;
# an over-limit band raises a ScatteringDiffusionWarning listing the offenders.
check_base_plate_scattering([0.02] * len(BASE_PLATE_BANDS_HZ))
```

## 2. Diffusion coefficient (ISO 17497-2)

The diffusion coefficient $d$ measures the **spatial uniformity** of the
reflected sound, not how much is scattered. A goniometer sweeps a receiver over a
polar arc and records the reflected level $L_i$ at each angle; the coefficient is
the normalised autocorrelation of the polar energy distribution.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_diffusion_goniometer_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_diffusion_goniometer.svg" alt="ISO 17497-2 free-field diffusion goniometer: a test sample on a turntable, a fixed loudspeaker source, and a semicircular arc of receiver microphones sampling the reflected polar response, from which the autocorrelation diffusion coefficient is computed" width="92%"></picture>

**Autocorrelation (Formula (5)).** For $n$ receivers at equal angular spacing,
with $p_i = 10^{L_i/10}$ the band energy at receiver $i$,

$$
d = \frac{\left(\sum_i p_i\right)^2 - \sum_i p_i^2}
         {(n-1)\,\sum_i p_i^2}.
$$

A perfectly uniform polar response ($L_i$ all equal) gives $d = 1$; a single
sharp specular lobe gives $d = 0$. When receivers subtend unequal solid angles,
Formula (6) area-weights each energy by $N_i$ from Formula (8) — and those area
factors are evaluated in **radians**, which is why a 5° spacing at the zenith
produces a weight near 1.57, not 51.9.

```python
import phonometry as ph

# Polar response of a diffuser (levels in dB at equally spaced receivers).
levels = [70.0, 74.0, 68.0, 72.0]
d = ph.directional_diffusion_coefficient(levels)   # Formula (5)
print(round(float(d), 4))            # 0.7367

# Normalise against a flat reference surface to isolate the diffuser's effect
# (Formula (7)): d_n = (d - d_ref) / (1 - d_ref).
d_n = ph.normalized_diffusion_coefficient(d, 0.10)
print(round(float(d_n), 4))          # 0.7075

# Random-incidence value: average the band coefficients over source positions,
# with the standard's 2-D weighting (0 deg -> 1, +/-30/+/-60 deg -> 3).
from phonometry import TWO_DIMENSIONAL_SOURCE_WEIGHTS
d_random = ph.random_incidence_diffusion(
    [0.5, 0.2, 0.2, 0.2, 0.2], weights=TWO_DIMENSIONAL_SOURCE_WEIGHTS)
print(round(float(d_random), 4))     # 0.2231
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/scattering_diffusion_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/scattering_diffusion.png" alt="Left: two polar responses and their autocorrelation diffusion coefficients, a diffusing surface with a high coefficient against a flat specular surface with a near-zero coefficient. Right: the ISO 17497-1 base-plate maximum-scattering limit as a step curve over one-third-octave bands with a compliant sample scattering curve below it" width="88%"></picture>

## 3. In-situ road absorption — subtraction technique (ISO 13472-1)

Out in the field there is no reverberation room. ISO 13472-1 measures the sound
absorption of a road surface (or any extended flat surface) *in situ* by firing
an impulse from a loudspeaker at height $d_s$ down onto the surface and recording
the impulse response at a microphone at height $d_m$. The **incident** and
**reflected** components are separated in time with an Adrienne window; their
transfer function gives the reflection factor and hence the absorption.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insitu_subtraction_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insitu_subtraction.svg" alt="ISO 13472-1 in-situ road absorption by the subtraction technique: a loudspeaker at 1.25 m and a microphone at 0.25 m above the road surface, with the direct and road-reflected ray paths and a free-field reference measurement, the reflected component isolated by an Adrienne time window" width="92%"></picture>

**Geometrical spreading (Clause 4.1).** The reflected wave travels farther than
the direct wave, so it is attenuated by the geometrical-spreading factor

$$
K_r = \frac{d_s - d_m}{d_s + d_m},
$$

which equals $2/3$ for the mandatory geometry $d_s = 1.25$ m, $d_m = 0.25$ m.
The absorption follows from the windowed incident and reflected spectra
$H_i$, $H_r$:

$$
\alpha(f) = 1 - \frac{1}{K_r^2}\left|\frac{H_r(f)}{H_i(f)}\right|^2.
$$

```python
import numpy as np
import phonometry as ph

# A band-limited incident impulse response and a synthetic road reflection
# hr = Kr * r0 * delayed(hi): a reflection of magnitude r0 = 0.4, delayed by the
# extra path, and scaled by the geometrical-spreading factor Kr.
fs, n = 48000.0, 4096
t = np.arange(n) / fs
hi = np.zeros(n)
hi[:64] = np.hanning(64) * np.cos(2.0 * np.pi * 1500.0 * t[:64])

kr = ph.geometric_spreading_factor()          # (ds - dm)/(ds + dm) = 2/3
hr = kr * 0.4 * np.roll(hi, 96)

# Narrow-band absorption, then reduced to one-third octaves over 250-4000 Hz.
alpha = ph.insitu_absorption_coefficient(hi, hr)   # 1 - (1/Kr^2)|Hr/Hi|^2
freq = np.fft.rfftfreq(n, 1.0 / fs)
centres, band = ph.one_third_octave_absorption(freq, alpha)
print(round(kr, 4))                # 0.6667
print(round(float(band[2]), 3))    # 0.84  (alpha = 1 - 0.4^2 = 0.84)
```

**Adrienne window (Clause 6.4).** The time window that isolates the reflection
mandates only a sharp leading edge, a 5 ms flat portion and a cosine-squared or
Blackman-Harris trailing edge — the exact durations are reported per measurement,
not fixed, so they are configurable here.

```python
from phonometry import adrienne_window

# Default: 0.5 ms leading edge, 5 ms flat top, 5 ms Blackman-Harris trailing.
w = adrienne_window(48000.0)
print(w.shape[0])          # 504 samples at 48 kHz
print(round(float(w.max()), 3))   # 1.0  (flat top and edges meet at unity)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/road_absorption_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/road_absorption.png" alt="Left: the Adrienne temporal window returned by the library, showing the sharp leading edge, the 5 ms flat portion and the Blackman-Harris trailing edge. Right: an in-situ one-third-octave absorption spectrum computed from a synthetic road reflection via the reflection-factor route" width="88%"></picture>

**Maximum sampled area (Annex A).** The finite time window limits how much of the
surface contributes to the reflection. The maximum sampled area is a circle whose
radius the library computes from the geometry and window width; the Annex A worked
example ($d_s = 1.25$ m, $d_m = 0.25$ m, $c = 340$ m/s, 5 ms flat window) gives
about 1.34 m.

```python
import phonometry as ph
print(round(ph.max_sampled_area_radius(5.0e-3), 3))   # 1.343  (metres)
```

## 4. In-situ road absorption — spot method (ISO 13472-2)

For smaller patches, ISO 13472-2 seals a short circular tube onto the surface and
measures the absorption with the two-microphone transfer-function method of
ISO 10534-2. The library provides the spot-method geometry and validity helpers;
the transfer-function DSP itself is the impedance-tube routine
`two_microphone_impedance` (see [Acoustic Materials](materials.md)).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_spot_tube_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_spot_tube.svg" alt="ISO 13472-2 spot method: a short circular tube sealed onto the road surface with a loudspeaker at the top and two microphones flush in the tube wall at spacing s, measuring absorption over 250 to 1600 Hz via the ISO 10534-2 two-microphone transfer-function method" width="92%"></picture>

**Plane-wave limits (Clause 5.4).** The tube supports only plane waves below

$$
f_u = 0.58\,\frac{c_0}{d},
$$

with $d$ the tube diameter, and the microphone spacing $s$ must sit between
$0.05\,c_0/f_{min}$ and $0.45\,c_0/f_{max}$. The reported range is the
one-third-octave bands 250–1600 Hz.

```python
import phonometry as ph

# Upper usable frequency of a 100 mm tube and the valid spacing window.
print(round(ph.spot_tube_upper_frequency(0.100, 343.0), 1))      # 1989.4 Hz
s_min, s_max = ph.spot_microphone_spacing_bounds(
    343.0, f_min=220.0, f_max=1800.0)
print(round(s_min, 3), round(s_max, 3))    # 0.078 0.086  (metres)
```

---

**Standards implemented on this page:** ISO 17497-1:2004 (scattering
coefficient), ISO 17497-2:2012 (diffusion coefficient), ISO 13472-1:2002 (in-situ
absorption, extended surface), ISO 13472-2:2010 (in-situ absorption, spot
method). Numerical conformance against the standards' worked examples and closed
forms is tracked in [CONFORMANCE.md](CONFORMANCE.md).

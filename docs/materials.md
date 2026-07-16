← [Documentation index](README.md)

# Acoustic Materials

Characterising an absorber or a partition is a laboratory exercise with three
distinct instruments behind it. The **reverberation room** delivers a spectrum of
sound-absorption coefficients that ISO 11654 collapses into a single rated number
$\alpha_w$ with a letter class. The **flow rig** — steady or oscillating —
measures how hard air is to push through a porous sample, the airflow resistance
that governs its low-frequency behaviour (ISO 9053-1/-2). And the **impedance
tube** recovers, at normal incidence, the full complex surface impedance,
reflection factor and absorption of a small sample, and — with four microphones —
its transmission loss (ISO 10534-1/-2, ASTM E2611). This page covers all three.

## 1. Sound-absorption rating (ISO 11654)

ISO 354 measures the sound-absorption coefficient $\alpha_s$ of a material in
one-third-octave bands in a reverberation room. ISO 11654:1997 turns that
spectrum into a single-number rating comparable across products.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso11654_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso11654.svg" alt="ISO 11654 rating flow: measured alpha_s becomes practical alpha_p per octave band, the reference curve is shifted to best fit, alpha_w is read at 500 Hz with shape indicators, giving the absorption class A to E" width="82%"></picture>

**Practical absorption coefficient (Clause 4.1).** The one-third-octave data are
first grouped into octave bands, each the arithmetic mean of its three thirds:

$$
\alpha_{p,i} = \tfrac{1}{3}\big(\alpha_{i1} + \alpha_{i2} + \alpha_{i3}\big),
$$

evaluated to the second decimal and then rounded in steps of $0.05$ (the
Clause 4.1 NOTE fixes the rounding, e.g. $0.92 \to 0.90$); rounded means above
$1.00$ are set to $1.00$. The five rating bands are 250, 500, 1000, 2000 and
4000 Hz.

**Weighted absorption (Clause 4.2).** A fixed reference curve
$\{250{:}\,0.80,\ 500{:}\,1.00,\ 1000{:}\,1.00,\ 2000{:}\,1.00,\ 4000{:}\,0.90\}$
is shifted downwards, towards the measured $\alpha_p$, in steps of $0.05$ until
the sum of the **unfavourable** deviations — taken only where the measurement
lies below the shifted curve, with magnitude $(\text{curve} - \text{measured})$ —
is no more than $0.10$. The weighted coefficient $\alpha_w$ is the shifted-curve
value read at 500 Hz.

**Shape indicators (Clause 4.3).** When a practical coefficient exceeds the
shifted curve by $0.25$ or more, a shape indicator is appended: `L` at 250 Hz,
`M` at 500 or 1000 Hz, `H` at 2000 or 4000 Hz (e.g. `0.60(M)`).

**Absorption class (Table B.1).** Finally $\alpha_w$ maps to a class: A
(0.90–1.00), B (0.80–0.85), C (0.60–0.75), D (0.30–0.55), E (0.15–0.25), or "not
classified" (0.00–0.10). Because $\alpha_w$ is always a multiple of $0.05$ these
ranges partition the grid exactly.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_rating_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_rating.svg" alt="ISO 11654 weighted sound absorption rating: the practical absorption spectrum plotted against the shifted reference curve over 250 Hz to 4000 Hz, with the unfavourable deviation at 250 Hz shaded and the weighted coefficient alpha_w read at 500 Hz" width="80%"></picture>

*The Annex A.2 worked example: the reference curve is shifted down by 0.40 until
the unfavourable deviations sum to 0.05 (≤ 0.10), giving $\alpha_w = 0.60$; the
500 Hz peak overshoots the shifted curve by ≥ 0.25, adding the `M` indicator, so
the rating is $0.60(\text{M})$, class C.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import weighted_absorption

# ISO 11654 Annex A.2 practical coefficients at 250/500/1000/2000/4000 Hz
result = weighted_absorption([0.35, 1.00, 0.65, 0.60, 0.55])
result.plot()   # practical curve vs shifted reference, deviations shaded
plt.show()
```

</details>

```python
from phonometry import weighted_absorption, absorption_class

# ISO 11654 Annex A.2 practical coefficients at 250/500/1000/2000/4000 Hz
alpha_p = [0.35, 1.00, 0.65, 0.60, 0.55]

result = weighted_absorption(alpha_p)
print(result.rating_label)          # 0.60(M)
print(result.alpha_w)               # 0.6
print(result.absorption_class)      # C
print(round(result.unfavourable_sum, 2))  # 0.05

# A bare alpha_w also maps straight to its class (Table B.1)
print(absorption_class(0.85))       # B
```

`weighted_absorption` accepts the five octave-band $\alpha_p$ values (as a
sequence or a `{frequency: value}` mapping); pass the fifteen one-third-octave
$\alpha_s$ values to `practical_absorption_coefficient` first if you are starting
from raw ISO 354 data. The result carries the shifted reference curve and the
per-band deviations, and its `.plot()` renders the figure above.

## 2. Airflow resistance (ISO 9053-1/-2)

The airflow resistance quantifies how strongly a porous material opposes a steady
or slowly-oscillating flow. Both parts share the same three quantities and units
(ISO 9053-1:2018, Clause 3):

$$
R = \frac{\Delta p}{q_v}\ \left[\text{Pa·s/m}^3\right], \qquad
R_s = R\,A\ \left[\text{Pa·s/m}\right], \qquad
\sigma = \frac{R_s}{d}\ \left[\text{Pa·s/m}^2\right],
$$

with $\Delta p$ the pressure difference across the specimen, $q_v$ the volumetric
flow, $A$ the cross-section and $d$ the thickness. Note the specific airflow
resistance $R_s$ is in **Pa·s/m** (not Pa·s/m²); the airflow resistivity $\sigma$
is $R_s$ per metre of thickness.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_airflow_resistance_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_airflow_resistance.svg" alt="Airflow resistance measurement rigs: the ISO 9053-1 static method with a specimen in a holder, a steady laminar flow q_v and a differential manometer reading the pressure drop; and the ISO 9053-2 alternating method with an oscillating piston driving a cavity terminated by the specimen or an airtight plug, and a microphone reading the cavity level" width="92%"></picture>

**Static method (ISO 9053-1:2018).** A steady laminar flow is stepped up and the
pressure difference plotted against the linear velocity $u = q_v/A$. A regression
of at least second order **constrained through the origin**, $\Delta p = a\,u +
b\,u^2$, is fitted, and $\Delta p$ and $R_s$ are read at the reference velocity
$u = 0.5\ \text{mm/s}$ (Clause 7.5); the highest velocity must not exceed
15 mm/s. Because $R_s = \Delta p/u = a + b\,u$, the linear term $a$ is the
zero-velocity specific airflow resistance.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airflow_resistance_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airflow_resistance.svg" alt="ISO 9053-1 static-method airflow resistance: the measured pressure drop against linear airflow velocity, fitted with a through-origin quadratic, with the specific airflow resistance evaluated at the 0.5 mm/s reference velocity" width="80%"></picture>

*The slightly super-linear pressure drop is fitted through the origin; the
specific airflow resistance is the fit read at 0.5 mm/s.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import static_airflow_resistance

area = np.pi * 0.05**2                      # 100 mm diameter cell [m^2]
u = np.array([0.5, 1, 2, 4, 8, 12]) * 1e-3  # linear velocity [m/s]
dp = 1.6e4 * u + 4.0e5 * u**2               # measured pressure drop [Pa]
r = static_airflow_resistance(u, dp, area=area, thickness=0.05)

u_fit = np.linspace(0.0, 13e-3, 200)
dp_fit = r.linear_coefficient * u_fit + r.quadratic_coefficient * u_fit**2
fig, ax = plt.subplots()
ax.plot(u_fit * 1e3, dp_fit, label="Through-origin fit  dp = a u + b u^2")
ax.plot(u * 1e3, dp, "o", label="Measured pressure drop")
ax.plot(r.evaluation_velocity * 1e3, r.pressure_drop, "D",
        label="Evaluation at 0.5 mm/s")
ax.set_xlabel("Linear airflow velocity u [mm/s]")
ax.set_ylabel("Pressure drop dp [Pa]")
ax.set_title(f"R_s = {r.specific_resistance:.0f} Pa·s/m")
ax.legend()
plt.show()
```

</details>

```python
import numpy as np
from phonometry import static_airflow_resistance

area = np.pi * 0.05**2            # 100 mm diameter cell [m^2]
u = np.array([0.5, 1, 2, 4, 8, 12]) * 1e-3      # linear velocity [m/s]
dp = 1.6e4 * u + 4.0e5 * u**2                    # measured pressure drop [Pa]

r = static_airflow_resistance(u, dp, area=area, thickness=0.05)
print(round(r.specific_resistance))   # 16200   R_s [Pa*s/m]
print(round(r.resistivity))           # 324000  sigma [Pa*s/m^2]
print(round(r.linear_coefficient))    # 16000   a = R_s at u -> 0
```

**Alternating method (ISO 9053-2:2020).** A piston oscillating at 1–4 Hz drives
an alternating flow into a cavity terminated either by the specimen or by an
airtight plug; the resistance follows from the sound-pressure-level difference
between the two terminations (Formula (2)):

$$
R = \frac{\kappa'\,P_S}{2\pi f\,V}\cdot\frac{h_t}{h_s}\cdot
    10^{(L_{p,s} - L_{p,t})/20},
$$

where $\kappa'$ is the **effective** ratio of specific heats. Heat conduction
between the oscillating air and the cavity walls makes the compression not fully
adiabatic; the normative Annex A corrects $\kappa$ down to

$$
\kappa' = \frac{\kappa}{\sqrt{1 + (\kappa-1)\tfrac{S}{V}b
          + \tfrac{1}{2}\big((\kappa-1)\tfrac{S}{V}b\big)^2}},
\qquad b = \sqrt{\frac{2 c_0 l_h}{\omega}},\quad
l_h = \frac{k_a}{\rho_0 c_0 C_P},
$$

with $S$ and $V$ the cavity surface and volume and $b$ the thermal
boundary-layer thickness. For the Annex A.3 example cavity this gives
$\kappa' = 1.370$, about 2 % below the adiabatic 1.4008.

```python
from phonometry import effective_kappa, alternating_airflow_resistance

# Annex A.3 cavity: closed cylinder 100 mm x 100 mm, piston at 2 Hz
kp = effective_kappa(cavity_surface=0.0471, cavity_volume=7.854e-4, frequency=2.0)
print(round(kp, 3))               # 1.37   effective ratio of specific heats

R = alternating_airflow_resistance(
    level_specimen=74.0, level_termination=90.0,
    piston_stroke_specimen=14e-3, piston_stroke_termination=1.4e-3,
    frequency=2.0, cavity_volume=7.854e-4, kappa_prime=kp,
)
print(round(R))                   # 222956  airflow resistance R [Pa*s/m^3]
```

Pass the `effective_kappa` result to `alternating_airflow_resistance` for an
Annex-A-conforming figure; its `kappa_prime` argument otherwise defaults to the
uncorrected adiabatic 1.4. The call warns (via `AirflowResistanceWarning`) when
the piston frequency leaves 1–4 Hz or the Formula (3)/(4) validity criteria fail.

## 3. Impedance tube (ISO 10534-1/-2, ASTM E2611)

The impedance tube measures a small sample at **normal incidence**. Two standards
share the geometry but differ in method and sign convention, so the library keeps
their helpers separate and never mixes them.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impedance_tube_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impedance_tube.svg" alt="ISO 10534-2 two-microphone impedance tube: a loudspeaker radiating a plane wave down the tube, two microphones flush in the wall at spacing s and distance x1 from the specimen face, the test specimen against a rigid backing, and the incident and reflected waves" width="92%"></picture>

**Working frequency range (ISO 10534-2, Clause 4).** Everything the tube
reports assumes the field inside is a single plane wave, and the geometry sets
both ends of the usable band. Above the cut-on of the first cross-sectional
mode the field stops being planar: a circular tube of diameter $d$ needs
$f\,d < 0.58\,c_0$ (Eq. (2); $f\,d < 0.50\,c_0$ for a rectangular tube,
Eq. (3)). The microphone spacing $s$ must also stay clear of the
half-wavelength singularity of the transfer-function method,
$f\,s < 0.45\,c_0$ (Eq. (4)). At the low end the opposite problem appears: a
spacing much shorter than the wavelength leaves almost no phase difference
between the microphones to measure, so the Clause 4.2 guideline keeps the
spacing above 5 % of the wavelength:

$$
\frac{c_0}{20\,s} \;<\; f \;<\;
\min\!\left(0.58\,\frac{c_0}{d},\ 0.45\,\frac{c_0}{s}\right).
$$

No single tube covers the building-acoustics range. A 100 mm tube with a
100 mm spacing works from roughly 170 Hz to 1.5 kHz; reaching the 5 kHz bands
takes a small tube (29 mm) with a close spacing, which in turn cannot see the
low bands. Laboratories therefore pair a large and a small tube (or one tube
with two spacings) and splice the spectra; the two must agree in the overlap
bands, and a mismatch there points at the sample cut or mounting, not at the
physics.

```python
from phonometry import plane_wave_frequency_range

# A 100 mm tube with 100 mm spacing, and a 29 mm tube with 20 mm spacing.
f_l, f_u = plane_wave_frequency_range(0.100, 343.2, diameter=0.100)
print(round(f_l, 1), round(f_u, 1))     # 171.6 1544.4
f_l, f_u = plane_wave_frequency_range(0.020, 343.2, diameter=0.029)
print(round(f_l, 1), round(f_u, 1))     # 858.0 6864.0
```

**Standing-wave-ratio method (ISO 10534-1).** A probe traverses the standing wave
and reads the level difference $\Delta L = L_\text{max} - L_\text{min}$ between a
pressure maximum and the adjacent minimum. The standing-wave ratio, reflection
magnitude and absorption follow in closed form:

$$
s = 10^{\Delta L/20}, \qquad |r| = \frac{s-1}{s+1}, \qquad
\alpha = 1 - |r|^2.
$$

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impedance_tube_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impedance_tube.svg" alt="ISO 10534-1 standing-wave-ratio method: the absorption coefficient and the reflection factor magnitude as functions of the standing-wave level difference, showing that a 9.54 dB difference corresponds to a standing-wave ratio of 3, a reflection magnitude of 0.5 and an absorption of 0.75" width="80%"></picture>

*A small level difference means a near-perfect absorber; a level difference of
9.54 dB gives $s = 3$, $|r| = 0.5$ and $\alpha = 0.75$.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import (
    standing_wave_absorption, standing_wave_ratio_from_level,
    standing_wave_reflection_magnitude,
)

level_diff = np.linspace(0.5, 40.0, 300)    # L_max - L_min [dB]
swr = standing_wave_ratio_from_level(level_diff)
fig, ax = plt.subplots()
ax.plot(level_diff, standing_wave_absorption(swr),
        label="Absorption coefficient alpha")
ax.plot(level_diff, standing_wave_reflection_magnitude(swr), "--",
        label="Reflection factor magnitude |r|")
ax.set_xlabel("Standing-wave level difference L_max - L_min [dB]")
ax.set_ylabel("alpha, |r|")
ax.legend()
plt.show()
```

</details>

```python
from phonometry import standing_wave_absorption, standing_wave_ratio_from_level

s = float(standing_wave_ratio_from_level(9.542))   # level difference [dB] -> SWR
print(round(s, 2))                                  # 3.0
print(round(float(standing_wave_absorption(s)), 2)) # 0.75
```

**Transfer-function method (ISO 10534-2).** Two fixed microphones measure the
complex transfer function $H_{12}$; from it the reflection factor at the sample
face, the absorption and the normalised surface impedance follow (Eqs. (17)–(19)):

$$
r = \frac{H_{12} - H_I}{H_R - H_{12}}\,e^{\,2 j k_0 x_1}, \qquad
\alpha = 1 - |r|^2, \qquad \frac{Z}{\rho c_0} = \frac{1+r}{1-r},
$$

with $H_I = e^{-j k_0 s}$, $H_R = e^{+j k_0 s}$, microphone spacing $s$ and $x_1$
the distance from the sample to the farther microphone.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_standing_wave_tube_dark.gif"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_standing_wave_tube.gif" alt="Animation: incident and reflected waves sum into a standing wave inside the impedance tube; a rigid termination gives deep envelope nodes, a porous sample gives shallow ones, sampled by the two wall microphones" width="640" height="360" loading="lazy"></picture>

[Watch the high-resolution video (WebM)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_standing_wave_tube.webm)

```python
import numpy as np
from phonometry import (
    tube_wavenumber, reflection_factor,
    absorption_from_reflection, normalized_surface_impedance,
)

f = np.array([500.0, 1000.0, 1800.0])
x1, spacing, c0 = 0.12, 0.03, 343.2
k0 = tube_wavenumber(f, c0)

# A measured transfer function H12 (here synthesised from r = 0.3 - 0.4j)
target = 0.3 - 0.4j
x2 = x1 - spacing
h12 = (np.exp(1j*k0*x2) + target*np.exp(-1j*k0*x2)) / \
      (np.exp(1j*k0*x1) + target*np.exp(-1j*k0*x1))

r = reflection_factor(h12, spacing=spacing, x1=x1, wavenumber=k0)
print(np.round(absorption_from_reflection(r), 3))     # [0.75 0.75 0.75]
print(np.round(normalized_surface_impedance(r), 2))   # Z / rho c0
# [1.15-1.23j 1.15-1.23j 1.15-1.23j]
```

The high-level `two_microphone_impedance` wraps this chain and returns an
`ImpedanceTubeResult` with absorption, reflection factor, surface impedance and
normalised impedance, applying the plane-wave frequency-range check and optional
tube attenuation; correct any microphone mismatch beforehand with
`apply_mic_calibration`. Its `.plot()` draws the absorption spectrum
$\alpha(f)$ with the reflection-factor magnitude $|r|$ overlaid.

**Transmission loss (ASTM E2611).** With four microphones — two upstream, two
downstream of the sample — a two-load (or one-load) measurement recovers the
sample's transfer matrix, whose entries give the normal-incidence transmission
loss, reflection and wavenumber:

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_astm_tube_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_astm_tube.svg" alt="ASTM E2611 four-microphone transmission-loss tube: a sound source, two microphones upstream and two downstream of the test specimen at spacings s1 and s2 and offsets l1 and l2, an adjustable termination for the two-load method, the upstream A and B and downstream C and D travelling waves, and the transfer matrix and transmission-loss relations" width="92%"></picture>

$$
\mathrm{TL} = 20\log_{10}\left|\frac{T_{11} + T_{12}/\rho c
             + \rho c\,T_{21} + T_{22}}{2}\right|.
$$

```python
import numpy as np
from phonometry import air_layer_transfer_matrix

# An air layer is a known transfer matrix; TL = 0 dB (nothing is lost)
f = np.array([500.0, 1000.0, 2000.0])
k0 = 2*np.pi*f / 343.2
rho_c = 1.186 * 343.2
tm = air_layer_transfer_matrix(thickness=0.05, wavenumber=k0,
                               characteristic_impedance=rho_c)
print(np.round(tm.transmission_loss(rho_c), 6))   # [0. 0. 0.]
```

`transfer_matrix_two_load` / `transfer_matrix_one_load` build the
`TransferMatrix` from the four measured microphone transfer functions
`(H1, H2, H3, H4)` of each load; its methods
(`transmission_loss`, `reflection_hard_backed`, `absorption_hard_backed`,
`characteristic_impedance_material`, `material_wavenumber`) then read off the
ASTM E2611 quantities.

**Mounting pitfalls.** Most bad tube data are made at the sample holder, long
before the signal processing. The recurring failures:

- **Perimeter gaps.** A specimen cut slightly undersize leaves an air sliver
  along the tube wall. Sound short-circuits around and behind the sample, and
  the gap itself resonates, so the measured absorption grows a spurious
  low-to-mid-frequency hump. Cut for a snug slide fit and seal the rim (a thin
  film of petroleum jelly is the classic remedy) without loading the front
  face.
- **Compression.** A specimen cut oversize and forced in is denser than the
  product it is supposed to represent: the flow resistivity rises, a limp
  frame is stiffened, and the absorption curve shifts and flattens. The result
  is repeatable and wrong.
- **Hidden back cavity.** If the specimen does not sit flush on the rigid
  backing, the unintended air layer acts as a quarter-wavelength cavity and
  moves the absorption peak down in frequency, flattering the material.
  Backing air gaps are perfectly legitimate mountings, but only when they are
  deliberate, dimensioned and reported with the result.
- **Face not plane.** A bulging, tilted or torn front face scatters into
  cross-sectional modes below the nominal cut-on and breaks the
  normal-incidence assumption the equations rest on. Cut with a sharp tool;
  do not tear fibrous materials to size.
- **One specimen is not the material.** Porous products are inhomogeneous at
  the scale of a tube sample. Measure several cuts and average; a spread
  between specimens is product variance worth reporting, not measurement noise
  to hide.

## Tube or reverberation room?

The tube and the reverberation room both deliver a number called the
"absorption coefficient", and the two are routinely confused. They are
different physical quantities, measured under different sound fields, and they
do not match, sometimes not even closely.

The tube measures a **normal-incidence** coefficient: one plane wave, one
angle, a specimen a few centimetres across, and a complex reflection factor
that keeps magnitude and phase. ISO 354 measures the **random-incidence**
coefficient $\alpha_s$: a diffuse field striking a sample of 10 m² to 12 m²
from every direction at once, recovered from the change in the room's decay
time through Sabine's formula, an energy average with no phase left in it.
Because the diffuse field finds more ways into an absorber than the single
normal-incidence wave (oblique waves travel a longer path inside the layer),
$\alpha_s$ usually comes out higher. For a locally reacting surface the two
are linked by Paris' angular average, which defines the statistical
absorption coefficient

$$
\alpha_{st} = \int_0^{\pi/2} \alpha(\theta)\,\sin 2\theta\,\mathrm{d}\theta,
$$

an integral that weights the oblique angles most heavily; evaluating it
needs the
angle-dependent $\alpha(\theta)$ from the measured surface impedance, not just
the normal-incidence coefficient itself.

**Why ISO 354 values exceed 1.** A ratio of absorbed to incident energy cannot
exceed one, yet reverberation-room reports of $\alpha_s = 1.05$ to $1.20$ for
thick porous absorbers are routine and correct by the method. Sabine's formula
converts the decay-time change into an equivalent absorption area $A$, and
$\alpha_s = A/S$ divides by the *geometric* sample area $S$. Diffraction at
the sample edges lets the specimen drain energy from a sound field wider than
its footprint (the edge effect), so the equivalent area can exceed the
geometric one. Such values are not errors, but they are not portable either:
they depend on the sample size and perimeter, which is exactly why ISO 354
fixes both. The ISO 11654 rating simply truncates: practical coefficients
above $1.00$ are set to $1.00$ (section 1), and prediction software clips at
one before summing absorption areas.

**Which to use.** They answer different questions. The reverberation-room
value is the one that feeds diffuse-field prediction: Sabine reverberation
estimates, the equivalent absorption areas of
[EN 12354-6](enclosed-space-absorption.md) and the $\alpha_w$ rating and
class, all of which expect random incidence over a mounted, finite sample
(ISO 354's Annex B mounting types exist because the mounting is part of the
result). The tube value is the laboratory and development tool: it needs only
a few square centimetres of material, resolves magnitude *and* phase, and its
surface impedance pins down the parameters of porous-material models in the
Allard and Atalla tradition, with the airflow resistivity of section 2 as the
first input; the fitted model then predicts the layer at any angle, thickness
or backing. What the tube number is *not* is a drop-in substitute for
$\alpha_s$: feeding normal-incidence coefficients into a Sabine or EN 12354-6
budget systematically underpredicts the installed absorption.

## 4. Sound-absorption measurement uncertainty (ISO 12999-2)

A rated absorption coefficient means little without its uncertainty. ISO
12999-2:2020 gives the standard uncertainty `u` of the quantities produced by a
reverberation-room measurement (ISO 354) and its ratings (ISO 11654, EN 1793-1),
estimated from inter-laboratory tests to ISO 5725. It is the sound-absorption
companion of the sound-insulation uncertainty of ISO 12999-1
([Field Insulation Measurement and Ratings](insulation-field.md)).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_uncertainty_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_uncertainty.svg" alt="ISO 12999-2 sound absorption coefficient uncertainty: the measured alpha_s spectrum over one-third-octave bands from 63 Hz to 5000 Hz with a shaded plus-or-minus U band at coverage factor k = 2, reproducing the standard's worked Table 4 example" width="80%"></picture>

**One-third-octave bands (Clause 5).** For the sound-absorption coefficient the
reproducibility standard deviation is `σR = m·αs + n` (Formula (1)), and for the
equivalent absorption area `σR = m·AT + n·S` with `S = 10 m²` (Formula (2)), where
`m` and `n` are the frequency-dependent constants of Table 1 (63–5000 Hz). The
repeatability value is `σr = 0.6·σR` (Formula (3)).

**Practical coefficient (Clause 6).** For the ISO 11654 practical coefficient
`σR = m·αp + n` in octave bands with the constants of Table 2 (250–4000 Hz);
again `σr = 0.6·σR`.

**Single numbers (Clause 7).** The weighted coefficient `αw` has a constant
standard uncertainty (`σR = 0.035`, `σr = 0.020`); the EN 1793-1 single-number
rating `DLα,NRD` scales with the value (`σR = 0.10·DLα`, `σr = 0.02·DLα`).

**Reporting (Clause 8).** The expanded uncertainty is `U = k·u` (Formula (10))
with the Table 3 coverage factor `k` (`k = 2.0` at 95 %, Gaussian). The reported
`U` is rounded to two decimals for absorption coefficients and one decimal for
the equivalent area and `DLα,NRD`.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import sound_absorption_coefficient_uncertainty

# ISO 12999-2 Table 4 worked example: alpha_s per one-third-octave band.
freqs = [63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
         630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
alpha_s = [0.33, 0.35, 0.39, 0.38, 0.37, 0.36, 0.36, 0.36, 0.43, 0.49,
           0.58, 0.63, 0.68, 0.71, 0.73, 0.75, 0.77, 0.79, 0.81, 0.81]
result = sound_absorption_coefficient_uncertainty(alpha_s, freqs, confidence=0.95)
result.plot()   # alpha_s with the +/-U (k = 2) reproducibility ribbon
plt.show()
```
</details>

```python
from phonometry import (
    sound_absorption_coefficient_uncertainty,
    weighted_coefficient_uncertainty,
    single_number_rating_uncertainty,
)

# Reproducibility uncertainty of alpha_s at 1000 Hz (Table 1: m=0.040, n=0.015).
r = sound_absorption_coefficient_uncertainty([0.68], [1000], confidence=0.95)
print(round(float(r.standard_uncertainty[0]), 4))            # 0.0422 (sigma_R)
print(float(r.reported_expanded_uncertainty[0]))             # 0.08  (U, k=2)

# Single-number ratings (Clause 7 worked examples).
print(float(weighted_coefficient_uncertainty(0.70).reported_expanded_uncertainty[0]))  # 0.07
print(float(single_number_rating_uncertainty(8.1).reported_expanded_uncertainty[0]))   # 1.6
```

## References

- Allard, J. F., & Atalla, N. (2009). *Propagation of sound in porous media:
  Modelling sound absorbing materials* (2nd ed.). Wiley.
  ISBN 978-0-470-74661-5.
  [doi:10.1002/9780470747339](https://doi.org/10.1002/9780470747339).
  The porous-material theory behind the measured quantities: airflow
  resistivity as a model input, and the surface impedance and absorption the
  tube recovers.
- Cox, T. J., & D'Antonio, P. (2017). *Acoustic absorbers and diffusers:
  Theory, design and application* (3rd ed.). CRC Press.
  ISBN 978-1-4987-4099-9.
  [doi:10.1201/9781315369211](https://doi.org/10.1201/9781315369211).
  Absorber measurement and design in practice: the tube and room methods side
  by side, mountings, and the edge-effect discussion behind the
  tube-or-reverberation-room section.
- International Organization for Standardization. (2003). *Acoustics —
  Measurement of sound absorption in a reverberation room* (ISO 354:2003).
  [iso.org catalogue](https://www.iso.org/standard/34545.html).
  The reverberation-room method that produces the $\alpha_s$ spectra rated by
  ISO 11654, including the Annex B specimen mountings.
- International Organization for Standardization. (1998). *Acoustics —
  Determination of sound absorption coefficient and impedance in impedance
  tubes — Part 2: Transfer-function method* (ISO 10534-2:1998; adopted in
  Europe as EN ISO 10534-2:2001, the edition implemented here; since
  revised as [ISO 10534-2:2023](https://www.iso.org/standard/81294.html)).
  [iso.org catalogue](https://www.iso.org/standard/22851.html).
  The two-microphone transfer-function method and its plane-wave
  frequency-range limits.
- ASTM International. (2019). *Standard test method for normal incidence
  determination of porous material acoustical properties based on the
  transfer matrix method* (ASTM E2611-19).
  [ASTM store](https://store.astm.org/e2611-19.html).
  The four-microphone transfer-matrix method behind the transmission-loss
  helpers.
- International Organization for Standardization. (2018). *Acoustics —
  Determination of airflow resistance — Part 1: Static airflow method*
  (ISO 9053-1:2018).
  [iso.org catalogue](https://www.iso.org/standard/69869.html).
  The static method of section 2, with the through-origin regression and the
  0.5 mm/s reference velocity.

---

**Standards.** ISO 11654:1997 (weighted sound-absorption rating); ISO 9053-1:2018
(static airflow resistance); ISO 9053-2:2020 (alternating airflow resistance);
BS EN ISO 10534-1:2001 and BS EN ISO 10534-2:2001 (impedance tube); ASTM E2611-19
(four-microphone transmission loss); ISO 12999-2:2020 (sound-absorption
measurement uncertainty). Every equation is derived from the standard
text; the [conformance report](CONFORMANCE.md) validates the library against the
standards' own worked examples (ISO 11654 Annex A, ISO 9053-2 Annex A.3,
ISO 12999-2 Tables 4/5) and closed-form identities.

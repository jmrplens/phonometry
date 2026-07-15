---
title: "Underwater sound propagation"
description: "Closed-form underwater propagation: geometrical spreading plus volume absorption (Francois-Garrison, Ainslie-McColm, Thorp), the speed of sound in sea water (UNESCO/Chen-Millero, Del Grosso, Mackenzie), the sonar equation, seabed reflection loss (Rayleigh) and the ocean ambient-noise spectrum (Wenz wind/thermal plus JOMOPANS-ECHO ship traffic)."
---

Closed-form underwater propagation, complementing the reference levels of the
[Underwater acoustics](/phonometry/guides/underwater-acoustics/) page: the
**transmission loss**, the **speed of sound** in sea water, the **sonar
equation**, **seabed reflection loss** and the **ocean ambient-noise** spectrum.

## Transmission loss

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss.svg" alt="Underwater transmission loss versus range at 10 kHz with the geometrical-spreading and volume-absorption contributions drawn separately, loss increasing downward" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss_dark.svg" alt="Underwater transmission loss versus range at 10 kHz with the geometrical-spreading and volume-absorption contributions drawn separately, loss increasing downward" style="width:82%">

The transmission loss is `TL = spreading + α·R`. Geometrical spreading is
`20·lg R` (spherical), `10·lg R` (cylindrical) or spherical up to a transition
range then cylindrical (`"practical"`). The volume absorption `α` (dB/km) comes
from **Francois–Garrison** (1982, default and reference), **Ainslie–McColm**
(1998) or **Thorp** (1967, frequency-only); the first two agree to within ~10 %
across 100 Hz–1 MHz.

```python
import numpy as np
import phonometry as ph

ranges = np.linspace(10.0, 20_000.0, 400)
tl = ph.transmission_loss(ranges, 10e3, law="practical", transition_range=1000.0,
                          temperature=10.0, salinity=35.0, depth=100.0)
print(tl.absorption_coefficient, tl.tl[-1])
tl.plot()   # TL vs range with the spreading/absorption split (needs matplotlib)
```

## Speed of sound in sea water

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_sound_speed.svg" alt="A sea-water sound-speed profile from the UNESCO equation: warm mixed layer, thermocline, a sound-channel axis at the minimum, and the speed rising with pressure at depth" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_sound_speed_dark.svg" alt="A sea-water sound-speed profile from the UNESCO equation: warm mixed layer, thermocline, a sound-channel axis at the minimum, and the speed rising with pressure at depth" style="width:60%">

`sea_water_sound_speed(T, S, depth, model=…)` uses the **UNESCO / Chen–Millero**
equation (default, in the Wong & Zhu 1995 ITS-90 form), **Del Grosso** (1974) or
**Mackenzie** (1981). Depth is converted to pressure with Leroy & Parthiot
(1998). The three agree to within ~1 m/s; Mackenzie's canonical check value is
`1550.744 m/s` at 25 °C, 35 ppt, 1000 m.

```python
import numpy as np
import phonometry as ph

c = ph.sea_water_sound_speed(25.0, 35.0, 1000.0, model="mackenzie")  # 1550.744
depths = np.linspace(0.0, 3000.0, 121)
temps = 4.0 + 14.0 / (1.0 + (np.maximum(depths - 80.0, 0.0) / 250.0) ** 2)
profile = ph.sound_speed_profile(depths, temps, 35.0, model="unesco")
profile.plot()   # sound speed vs depth (needs matplotlib)
```

The $c(z)$ minimum acts as a waveguide (the SOFAR channel): wavefronts that
stray from the axis are refracted back toward it, while sound generated
outside the channel leaks away to depth, as the simulation below shows with an
intentionally exaggerated gradient. This trapping is why low-frequency sound
can cross entire oceans.

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animation: a 2D FDTD simulation of a low-frequency pulse in a SOFAR-like underwater sound channel with the sound-speed profile drawn beside the field; launched on the channel axis the wavefronts refract back toward the sound-speed minimum and stay trapped, launched near the surface the energy crosses the channel and leaks away to depth" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ducting_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animation: a 2D FDTD simulation of a low-frequency pulse in a SOFAR-like underwater sound channel with the sound-speed profile drawn beside the field; launched on the channel axis the wavefronts refract back toward the sound-speed minimum and stay trapped, launched near the surface the energy crosses the channel and leaks away to depth" style="width:88%"></video>

## Sonar equation

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation.svg" alt="The passive sonar equation: signal excess falling with transmission loss and crossing zero, the detection limit, at the figure of merit" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation_dark.svg" alt="The passive sonar equation: signal excess falling with transmission loss and crossing zero, the detection limit, at the figure of merit" style="width:82%">

The sonar equation gives the **signal excess** `SE` (detection when `SE ≥ 0`)
and the **figure of merit** (the maximum allowable transmission loss at
`SE = 0`). Passive: `SE = SL − TL − (NL − DI) − DT`. Active (monostatic):
`SE = SL − 2·TL + TS − (NL − DI) − DT`, or reverberation-limited with `RL`.

```python
import numpy as np
import phonometry as ph

tl = np.linspace(40.0, 120.0, 400)
se = ph.passive_sonar_equation(source_level=140.0, transmission_loss=tl,
                               noise_level=60.0, directivity_index=15.0,
                               detection_threshold=8.0)
print(se.figure_of_merit)
se.plot()   # signal excess vs transmission loss (needs matplotlib)
```

Sonar, propagation and ambient levels are in dB re a plane wave of 1 µPa rms
(spectrum levels). Source levels (below) use the source convention, dB re
1 µPa²/Hz **at 1 m**.

## Seabed reflection loss

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seabed_reflection.svg" alt="Bottom reflection loss versus grazing angle for a fast sandy seabed: zero loss below the critical grazing angle, rising sharply above it" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seabed_reflection_dark.svg" alt="Bottom reflection loss versus grazing angle for a fast sandy seabed: zero loss below the critical grazing angle, rising sharply above it" style="width:82%">

A plane wave striking the seabed reflects with the fluid–fluid **Rayleigh
reflection coefficient**. For a faster bottom (`c2 > c1`) there is a **critical
grazing angle** `φc = arccos(c1/c2)`, below which the wave is totally reflected
(`|R| = 1`, zero loss). The bottom loss is `BL = −20·lg|R|`.

```python
import numpy as np
import phonometry as ph

phi = np.linspace(0.0, 90.0, 361)   # grazing angle from the interface, degrees
bl = ph.bottom_reflection_loss(phi, rho1=1000.0, c1=1500.0,   # water
                               rho2=1900.0, c2=1650.0)          # sand
print(bl.critical_angle)            # 24.6°
bl.plot()   # bottom loss vs grazing angle (needs matplotlib)
```

## Ocean ambient noise

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ocean_ambient_noise.svg" alt="Wenz ambient-noise spectrum levels for two wind speeds, with wind noise falling at 5 dB per octave and thermal noise rising above about 50 kHz" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ocean_ambient_noise_dark.svg" alt="Wenz ambient-noise spectrum levels for two wind speeds, with wind noise falling at 5 dB per octave and thermal noise rising above about 50 kHz" style="width:82%">

The ambient-noise spectrum level is the energy sum of the physically grounded
Wenz components: **wind / sea-surface** noise via the "rule of fives" (the
historical 25 dB anchor at 1 kHz for 5 knots is re 20 µPa, i.e. ~51 dB re 1 µPa;
strictly valid ~500 Hz–5 kHz) and **Mellen thermal** noise
(dominant above ~50 kHz). The wide example range keeps the wind curve plotted
beyond ~5 kHz only as an extrapolation to show the thermal crossover. A
**shipping** spectrum may be supplied by the caller.

```python
import numpy as np
import phonometry as ph

freqs = np.logspace(2, 5.5, 300)
noise = ph.ocean_ambient_noise(freqs, wind_speed_knots=15.0)
noise.plot()   # composite spectrum with wind/thermal components (needs matplotlib)
```

## Ship-traffic source level

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ship_traffic_noise.svg" alt="JOMOPANS-ECHO predicted source-level spectra for a container ship, a cruise ship and a tug, with cargo vessels showing a low-frequency hump below 100 Hz" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ship_traffic_noise_dark.svg" alt="JOMOPANS-ECHO predicted source-level spectra for a container ship, a cruise ship and a tug, with cargo vessels showing a low-frequency hump below 100 Hz" style="width:82%">

When no measured spectrum is available, a ship's source level can be
**estimated** from its class, speed and length with **JOMOPANS-ECHO**
(MacGillivray & de Jong 2021, the default, validated against 1862 measurements),
**RANDI 3.1** or **Wales & Heitmeyer** (2002).

```python
import phonometry as ph

ship = ph.ship_source_spectrum(18.0, 300.0, vessel_class="containership")
ship.plot()                     # source spectral density vs frequency
print(ph.VESSEL_CLASSES)        # the 13 JOMOPANS-ECHO vessel classes

# Feed the prediction into the ambient noise as the shipping term:
noise = ph.ocean_ambient_noise(ship.frequency, wind_speed_knots=10.0,
                               shipping=ship.source_psd)
```

## Numerical solvers

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/numerical_propagation.png" alt="A Munk sound-speed profile, ray paths forming convergence zones, and normal-mode versus parabolic-equation transmission loss agreeing in trend" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/numerical_propagation_dark.png" alt="A Munk sound-speed profile, ray paths forming convergence zones, and normal-mode versus parabolic-equation transmission loss agreeing in trend" style="width:100%">

For range-independent environments the field can be computed numerically with
three solvers (Jensen et al., *Computational Ocean Acoustics*):

- **`normal_modes`** — the depth-separated Sturm-Liouville eigenproblem solved by
  finite differences, summed into transmission loss (validated against the ideal
  waveguide's exact modes).
- **`ray_trace`** — the ray-trajectory equations integrated with Runge-Kutta,
  vectorised over all rays at once (validated against a linear gradient's
  circular arcs).
- **`parabolic_equation`** — the standard (Tappert) PE via the split-step Fourier
  algorithm (validated against free-field spherical spreading).

```python
import numpy as np
import phonometry as ph

z = np.linspace(0.0, 5000.0, 60)
eta = 2.0 * (z - 1300.0) / 1300.0
c = 1500.0 * (1.0 + 0.00737 * (eta - 1.0 + np.exp(-eta)))   # Munk profile
ph.ray_trace(z, c, source_depth=1000.0,
             launch_angles_deg=np.linspace(-12, 12, 21), max_range=100e3).plot()

modes = ph.normal_modes(50.0, [0.0, 200.0], [1500.0, 1500.0],
                        source_depth=50.0, receiver_depth=100.0)
ph.parabolic_equation(50.0, [0.0, 200.0], [1500.0, 1500.0],
                      source_depth=50.0, max_range=20e3).plot()
```

All three assume a range-independent water column with a pressure-release
surface.

## See also

- API reference: [`underwater.propagation`](/phonometry/reference/api/underwater/propagation/), [`underwater.numerical_propagation`](/phonometry/reference/api/underwater/numerical-propagation/) and [`underwater.sound_speed`](/phonometry/reference/api/underwater/sound-speed/).

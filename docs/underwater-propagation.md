← [Documentation index](README.md)

# Underwater sound propagation: transmission loss, sound speed, sonar, seabed and ambient noise

Closed-form underwater propagation: the **transmission loss** (geometrical
spreading plus volume absorption), the **speed of sound** in sea water, the
**sonar equation**, **seabed reflection loss** and the **ocean ambient-noise**
spectrum (wind, thermal and shipping-traffic contributions). These complement
the underwater reference levels (ISO 18405/17208/18406) in
[Underwater Acoustics](underwater-acoustics.md).

## 1. Transmission loss

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_transmission_loss.svg" alt="Underwater transmission loss versus range at 10 kHz: the total loss with the geometrical-spreading and volume-absorption contributions drawn separately, loss increasing downward" width="82%">
</picture>

The transmission loss is `TL = spreading + α·R`. Geometrical spreading is
`20·lg R` (spherical), `10·lg R` (cylindrical) or spherical up to a transition
range `R0` and cylindrical beyond it (`"practical"`). The volume absorption
coefficient `α` (dB/km) comes from one of three models: **Francois–Garrison**
(1982, the default and reference), **Ainslie–McColm** (1998, a legible
simplification) or **Thorp** (1967, frequency-only).

```python
import numpy as np
import phonometry as ph

# Absorption coefficient at 10 kHz, 10 °C, 35 ppt, 100 m, pH 8 (dB/km).
# seawater_absorption accepts scalar or array frequencies and returns an array.
alpha = ph.seawater_absorption(10e3, temperature=10.0, salinity=35.0,
                               depth=100.0, model="francois-garrison")[0]
print(f"α = {alpha:.3f} dB/km")

ranges = np.linspace(10.0, 20_000.0, 400)
tl = ph.transmission_loss(ranges, 10e3, law="practical", transition_range=1000.0,
                          temperature=10.0, salinity=35.0, depth=100.0)
print(tl.absorption_coefficient, tl.tl[-1])
tl.plot()   # TL vs range with the spreading/absorption split (needs matplotlib)
```

`transmission_loss` returns a `TransmissionLossResult` with `tl`, `spreading`,
`absorption` (arrays), the `frequency` and the `absorption_coefficient`
(dB/km). Francois–Garrison and Ainslie–McColm agree to within ~10 % across
100 Hz–1 MHz, so either is a good cross-check of the other.

## 2. Speed of sound in sea water

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_sound_speed_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/underwater_sound_speed.svg" alt="A sea-water sound-speed profile computed with the UNESCO equation: a warm mixed layer near the surface, a thermocline where the speed drops, a sound-channel axis at the minimum, and the speed rising again with pressure at depth" width="62%">
</picture>

`sea_water_sound_speed(T, S, depth, model=…)` evaluates the sound speed with the
**UNESCO / Chen–Millero** equation (default, the international standard, in the
Wong & Zhu 1995 ITS-90 form), **Del Grosso** (1974) or **Mackenzie** (1981). The
UNESCO and Del Grosso equations use pressure, so depth is first converted with
the Leroy & Parthiot (1998) formula (`depth_to_pressure`). The three agree to
within ~1 m/s in their common domain; Mackenzie's canonical check value is
`1550.744 m/s` at 25 °C, 35 ppt, 1000 m.

```python
import numpy as np
import phonometry as ph

c = ph.sea_water_sound_speed(25.0, 35.0, 1000.0, model="mackenzie")  # 1550.744

# A profile: warm mixed layer, thermocline, isothermal deep layer.
depths = np.linspace(0.0, 3000.0, 121)
temps = 4.0 + 14.0 / (1.0 + (np.maximum(depths - 80.0, 0.0) / 250.0) ** 2)
profile = ph.sound_speed_profile(depths, temps, 35.0, model="unesco")
profile.plot()   # sound speed vs depth (needs matplotlib)
```

## 3. Sonar equation

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sonar_equation.svg" alt="The passive sonar equation: signal excess falling with transmission loss, crossing zero (the detection limit) at the figure of merit" width="82%">
</picture>

The sonar equation combines the performance terms into the **signal excess**
`SE` (detection when `SE ≥ 0`) and the **figure of merit** (the maximum
allowable transmission loss at `SE = 0`). Passive:
`SE = SL − TL − (NL − DI) − DT`. Active (monostatic):
`SE = SL − 2·TL + TS − (NL − DI) − DT`, or reverberation-limited with `RL` in
place of `NL − DI`.

```python
import numpy as np
import phonometry as ph

tl = np.linspace(40.0, 120.0, 400)
se = ph.passive_sonar_equation(source_level=140.0, transmission_loss=tl,
                               noise_level=60.0, directivity_index=15.0,
                               detection_threshold=8.0)
print(se.figure_of_merit)   # max allowable one-way TL at SE = 0
se.plot()   # signal excess vs transmission loss (needs matplotlib)

# Active, monostatic (two-way loss, target strength):
ph.active_sonar_equation(220.0, 70.0, target_strength=15.0, noise_level=60.0,
                         directivity_index=20.0, detection_threshold=10.0)
```

Sonar, propagation and ambient levels are in dB re a plane wave of 1 µPa rms
(spectrum levels are referred to a 1 Hz band). Source levels (§6) instead use
the source convention, dB re 1 µPa²/Hz **at 1 m**.

## 4. Seabed reflection loss

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seabed_reflection_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seabed_reflection.svg" alt="Bottom reflection loss versus grazing angle for a fast sandy seabed: zero loss below the critical grazing angle (total reflection) rising sharply above it" width="82%">
</picture>

A plane wave striking the seabed reflects with the fluid–fluid **Rayleigh
reflection coefficient** (Medwin & Clay). For a faster bottom (`c2 > c1`) there
is a **critical grazing angle** `φc = arccos(c1/c2)`, below which the wave is
totally reflected (`|R| = 1`, zero loss). The bottom loss is `BL = −20·lg|R|`.

```python
import numpy as np
import phonometry as ph

phi = np.linspace(0.0, 90.0, 361)   # grazing angle from the interface, degrees
bl = ph.bottom_reflection_loss(phi, rho1=1000.0, c1=1500.0,  # water
                               rho2=1900.0, c2=1650.0)         # sand
print(bl.critical_angle)            # 24.6° for this sand/water pair
bl.plot()                           # bottom loss vs grazing angle (needs matplotlib)
```

`bottom_reflection_loss` returns a `BottomLossResult` with `reflection_loss`,
the complex `reflection_coefficient` and the `critical_angle` (`None` for a
slower bottom). `reflection_coefficient(…)` and `critical_angle(c1, c2)` are
also exposed directly. The model is lossless (real densities and sound speeds);
sediment attenuation is out of scope.

## 5. Ocean ambient noise

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ocean_ambient_noise_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ocean_ambient_noise.svg" alt="Wenz ambient-noise spectrum levels for two wind speeds: wind-dominated at mid frequencies falling at 5 dB per octave and thermal noise rising above about 50 kHz" width="82%">
</picture>

The ambient-noise spectrum level (dB re 1 µPa²/Hz) is the energy sum of the two
physically grounded Wenz components: **wind / sea-surface** noise via the "rule
of fives" (`25 − (5/3)·10·(lg f_kHz − lg(U/5))`, 25 dB at 1 kHz for 5 knots) and
**Mellen thermal** noise (`4π·k·T·ρ·f²/c`, dominant above ~50 kHz). A
**shipping** spectrum may be supplied by the caller — for example one predicted
by the traffic model in §6.

```python
import numpy as np
import phonometry as ph

freqs = np.logspace(2, 5.5, 300)
noise = ph.ocean_ambient_noise(freqs, wind_speed_knots=15.0)
noise.plot()   # composite spectrum with wind/thermal components (needs matplotlib)

# Individual components are available directly:
ph.wind_noise_spectrum(1000.0, 5.0)      # 25 dB (the rule-of-fives anchor)
ph.thermal_noise_spectrum(5e4)           # molecular thermal-noise limit
```

The wind component is strictly valid over roughly 500 Hz–5 kHz; the wide example
range keeps it plotted mainly to show where the thermal component takes over
above ~50 kHz (the wind curve beyond ~5 kHz is an extrapolation). The
low-frequency turbulence band and a built-in distant-shipping model are out of
scope (Wenz notes these bands are strongly variable); a shipping spectrum is
supplied through the `shipping` argument.

## 6. Ship-traffic source level

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ship_traffic_noise_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ship_traffic_noise.svg" alt="JOMOPANS-ECHO predicted source-level spectra for a container ship, a cruise ship and a tug: cargo vessels show a low-frequency hump below 100 Hz" width="82%">
</picture>

When no measured spectrum is available, a ship's underwater source level can be
**estimated** from its class, speed and length. Three semi-empirical models are
available: **JOMOPANS-ECHO** (MacGillivray & de Jong 2021, per vessel class,
validated against 1862 measurements, the default), **RANDI 3.1** and
**Wales & Heitmeyer** (2002). All return the source spectral-density level and
the decidecade-band source level.

```python
import phonometry as ph

# A container ship at 18 knots, 300 m long (JOMOPANS-ECHO default):
ship = ph.ship_source_spectrum(18.0, 300.0, vessel_class="containership")
ship.plot()                     # source spectral density vs frequency

print(ph.VESSEL_CLASSES)        # the 13 JOMOPANS-ECHO vessel classes

# Feed the predicted spectrum into the ambient noise as the shipping term:
noise = ph.ocean_ambient_noise(ship.frequency, wind_speed_knots=10.0,
                               shipping=ship.source_psd)
```

`ship_source_spectrum` returns a `ShipTrafficSpectrum` with `source_psd`
(dB re 1 µPa²/Hz m) and `band_level` (dB re 1 µPa m). Cargo vessels (container
ships, bulkers, vehicle carriers, tankers) carry an extra low-frequency hump
below 100 Hz. The implementation is validated to the authors' own reference
calculator (File S1) to better than 0.01 dB.

## Standards & sources

- Speed of sound: UNESCO / Chen & Millero (1977, Wong & Zhu 1995 ITS-90),
  Del Grosso (1974), Mackenzie (1981), Leroy & Parthiot (1998).
- Absorption: Francois & Garrison (1982), Ainslie & McColm (1998), Thorp (1967).
- Sonar equation: Urick, *Principles of Underwater Sound*.
- Seabed reflection: Medwin & Clay, *Fundamentals of Acoustical Oceanography*
  (Rayleigh fluid–fluid reflection coefficient).
- Ambient noise: Wenz (1962); Carey & Evans, *Ocean Ambient Noise* (2011) — the
  wind "rule of fives" and the Mellen thermal-noise derivation.
- Ship-traffic source level: MacGillivray & de Jong (2021),
  *J. Mar. Sci. Eng.* 9(4) 369 (CC-BY, JOMOPANS-ECHO), which also reproduces
  RANDI 3.1 and Wales & Heitmeyer (2002).

Numerical solvers (ray tracing, normal modes, the parabolic equation) are a
separate, future addition.

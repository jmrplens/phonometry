← [Documentation index](README.md)

# Underwater sound propagation: transmission loss, sound speed and the sonar equation

Closed-form underwater propagation: the **transmission loss** (geometrical
spreading plus volume absorption), the **speed of sound** in sea water and the
**sonar equation**. These complement the underwater reference levels
(ISO 18405/17208/18406) in [Underwater Acoustics](underwater-acoustics.md).

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

All levels are in dB (re a plane wave of 1 µPa rms; spectrum levels, i.e.
referred to a 1 Hz band).

## Standards & sources

- Speed of sound: UNESCO / Chen & Millero (1977, Wong & Zhu 1995 ITS-90),
  Del Grosso (1974), Mackenzie (1981), Leroy & Parthiot (1998).
- Absorption: Francois & Garrison (1982), Ainslie & McColm (1998), Thorp (1967).
- Sonar equation: Urick, *Principles of Underwater Sound*.

Numerical solvers (ray tracing, normal modes, the parabolic equation) are a
separate, future addition.

---
title: "Underwater sound propagation: transmission loss, sound speed and the sonar equation"
description: "Closed-form underwater propagation: geometrical spreading plus volume absorption (Francois-Garrison, Ainslie-McColm, Thorp), the speed of sound in sea water (UNESCO/Chen-Millero, Del Grosso, Mackenzie) and the passive/active sonar equation."
---

Closed-form underwater propagation, complementing the reference levels of the
[Underwater acoustics](/phonometry/guides/underwater-acoustics/) page: the
**transmission loss**, the **speed of sound** in sea water and the **sonar
equation**.

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

All levels are in dB (re a plane wave of 1 µPa rms; spectrum levels). Numerical
solvers (ray tracing, normal modes, the parabolic equation) are a separate,
future addition.

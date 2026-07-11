← [Documentation index](README.md)

# Sound power from surface vibration (ISO/TS 7849)

The airborne sound power a machine radiates through the structure-borne
vibration of its outer surface can be estimated from the surface vibratory
velocity and a **radiation factor** `ε` (the radiation efficiency), without an
acoustic measurement. The radiated power is (ISO/TS 7849-1, Formula 6)

$$
P = Z_c \, \langle v^2 \rangle \, S \, \varepsilon \quad [\mathrm{W}],
$$

with `Z_c` the characteristic impedance of air, `⟨v²⟩` the mean-square vibratory
velocity over the radiating area `S`. Expressed in levels (velocity level re
`v₀ = 5·10⁻⁸ m/s`), the A-weighted sound power level is (Formula 12 / 15)

$$
L_W = L_v + 10\lg\frac{S}{S_0} + 10\lg\varepsilon
      + 10\lg\frac{Z_{c,n}}{Z_{c,0}},
$$

where `S₀ = 1 m²`, the normalized impedance `Z_{c,n} = 411 N·s/m³` and the
reference `Z_{c,0} = 400 N·s/m³` give the fixed `10 lg(411/400) = 0.118 dB`
term. This module feeds the structure-borne source and building prediction
standards (ISO 9611, EN 15657, EN 12354-5).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/vibration_sound_power_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/vibration_sound_power.svg" alt="Radiated sound power level per octave band of a vibrating surface, comparing the ISO/TS 7849-1 upper limit with a fixed radiation factor of one against the ISO/TS 7849-2 engineering value with a measured radiation factor, with the band-summed totals marked" width="82%"></picture>

## 1. The two parts

The two parts differ only in the radiation factor. **Part 1 (survey)** assumes
`ε = 1` and yields the *upper limit* `L_W,max`, needing only the velocity level
and the area. **Part 2 (engineering)** applies a frequency-band radiation factor
`εⱼ` determined (per ISO 9614) as `εⱼ = Pⱼ/(Z_{c,n}·⟨vⱼ²⟩·S)`.

```python
import numpy as np
import phonometry as ph

bands = np.array([250.0, 500.0, 1000.0, 2000.0])
lv = np.array([82.0, 85.0, 83.0, 79.0])          # mean velocity level per band [dB]

# Part 1 upper limit (epsilon = 1):
upper = ph.sound_power_from_vibration(lv, area=1.6, frequencies=bands)
print(round(upper.total_level, 1))               # e.g. 89.4  dB re 1 pW

# Part 2 engineering value with a measured radiation factor:
eps = np.array([0.45, 0.75, 0.95, 1.00])
eng = ph.sound_power_from_vibration(lv, area=1.6, radiation_factor=eps, frequencies=bands)
print(np.round(eng.sound_power_level, 1))        # per-band L_W
```

## 2. Velocity level, calibration and the radiation factor

The velocity level is `L_v = 20·lg(v/v₀)` (Formula 3); a sinusoidal calibration
acceleration converts as `L_v = 20·lg(â/(2πf·v₀·√2))` (Formula 8). The radiation
factor comes from an independently measured power:

```python
import phonometry as ph

# The standard's worked calibration EXAMPLE: 9.81 m/s^2 at 100 Hz.
print(round(float(ph.velocity_level_from_acceleration(9.81, 100.0)), 1))   # 106.9 dB

# Radiation factor from a measured power (ISO 9614): eps = P / (Zc <v^2> S).
eps = ph.radiation_factor(3.0e-4, area=2.0, mean_square_velocity=(1e-3)**2)
print(round(float(eps), 3))                                                # 0.365
```

Surface velocity levels from several positions are combined with the energetic
mean `mean_velocity_level` (Formula 10) or its area-weighted form (Formula 11),
and the correction `extraneous_velocity_correction` removes extraneous
vibration per Table 2.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

bands = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
lv = np.array([78.0, 82.0, 85.0, 83.0, 79.0, 74.0])
eps = np.array([0.20, 0.45, 0.75, 0.95, 1.00, 1.00])
x = np.arange(bands.size)
plt.bar(x - 0.2, ph.radiated_sound_power_level(lv, 1.6), width=0.4, label="Part 1 (ε=1)")
plt.bar(x + 0.2, ph.radiated_sound_power_level(lv, 1.6, radiation_factor=eps),
        width=0.4, label="Part 2 (ε measured)")
plt.xticks(x, [f"{b:g}" for b in bands]); plt.legend()
plt.xlabel("Frequency [Hz]"); plt.ylabel("$L_W$ [dB re 1 pW]"); plt.show()
```

</details>

---

**Standards.** ISO/TS 7849-1:2009 (*survey method using a fixed radiation
factor*) and ISO/TS 7849-2:2009 (*engineering method including determination of
the adequate radiation factor*), *Acoustics — Determination of airborne sound
power levels emitted by machinery using vibration measurement*: the radiated
power `P = Z_c⟨v²⟩Sε` (Formula 6), the velocity level and its calibration
(Formulae 3, 8), the mean over the surface (Formulae 10/11), the extraneous
correction (Table 2), the radiation factor (Formula 4/8) and the sound power
level (Formulae 12/15). Conformance is anchored on the standard's own worked
calibration example, the exact round-trip between the radiation factor and
`L_W = 10 lg(P/P₀)`, and the fixed impedance term.

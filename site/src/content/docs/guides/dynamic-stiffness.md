---
title: "Dynamic stiffness of resilient materials (EN 29052-1)"
description: "The EN 29052-1:1992 determination of the dynamic stiffness per unit area of resilient materials under floating floors from the load-plate resonance: the apparent stiffness of Formula 4, the enclosed-gas term of Formula 7, the airflow-resistivity regimes of clause 8.2, and the floating-floor natural frequency of Formula 2."
---

A **floating floor** is a heavy floating slab resting on a resilient layer; the
two form a mass-spring system whose **natural frequency** governs how much the
floor improves impact and airborne insulation. **EN 29052-1:1992** (identical to
ISO 9052-1:1989) measures the **dynamic stiffness per unit area** `s'` of the
resilient layer from the resonance of a standard load plate on a
200 mm × 200 mm specimen. `s'` is the input to the floating-floor impact
improvement (ISO 16251) covered in
[Building acoustics](/phonometry/guides/building-acoustics/) and to the
EN 12354-2 impact model.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness.svg" alt="Floating-floor natural frequency versus the resilient layer's dynamic stiffness per unit area for a light and a heavy floating floor, with a worked design point" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness_dark.svg" alt="Floating-floor natural frequency versus the resilient layer's dynamic stiffness per unit area for a light and a heavy floating floor, with a worked design point" style="width:82%">

## 1. Dynamic stiffness and resonance

The dynamic stiffness per unit area is a dynamic force per area divided by the
resulting change in thickness (Formula 1): `s' = (F/S)/Δd`. The resiliently
supported floor is a resonator whose natural frequency (Formula 2) and, in the
laboratory arrangement, measured resonant frequency (Formula 3) are

$$
f_0 = \frac{1}{2\pi}\sqrt{\frac{s'}{m'}}, \qquad
f_r = \frac{1}{2\pi}\sqrt{\frac{s'_t}{m'_t}},
$$

so the **apparent** dynamic stiffness follows from the resonance (Formula 4):

$$
s'_t = 4\pi^2\,m'_t\,f_r^2 .
$$

```python
import phonometry as ph

# Standard 8 kg load plate on the 0.04 m2 specimen -> m't = 200 kg/m2;
# the fundamental resonance is measured at 25 Hz.
s_t = ph.apparent_dynamic_stiffness(resonant_frequency=25.0, total_mass_per_area=200.0)
print(round(s_t / 1e6, 3))                              # 4.935  MN/m3

# Installed on a 120 kg/m2 floating screed with s' = 10 MN/m3:
print(round(ph.natural_frequency(10e6, 120.0), 1))      # 45.9  Hz
```

## 2. The enclosed-gas term and airflow resistivity

For an air-permeable material the enclosed pore air adds a parallel stiffness
from its isothermal compression (Formula 7): `s'a = p₀/(d·ε)`, with `p₀` the
atmospheric pressure, `d` the loaded thickness and `ε` the porosity. The
standard's worked NOTE (`p₀ = 0.1 MPa`, `ε = 0.9`) is `s'a = 111/d` MN/m³ for
`d` in millimetres:

```python
import phonometry as ph

print(round(ph.enclosed_gas_stiffness(thickness=0.020, porosity=0.9) / 1e6, 2))
# 5.56  MN/m3   (the NOTE's 111/20 = 5.55 MN/m3)
```

The dynamic stiffness of the *installed* material is then set by the lateral
airflow resistivity `r` (clause 8.2): `s' = s't` for `r ≥ 100 kPa·s/m²`,
`s' = s't + s'a` for `10 ≤ r < 100 kPa·s/m²`, and for `r < 10 kPa·s/m²` the
method only resolves `s' = s't` when the gas term is negligible.
`floating_floor_resonance` chains the whole determination:

```python
import phonometry as ph

res = ph.floating_floor_resonance(
    resonant_frequency=25.0, total_mass_per_area=200.0,
    floor_mass_per_area=120.0,
    airflow_resistivity=50.0, thickness=0.020, porosity=0.9,
)
print(round(res.dynamic_stiffness / 1e6, 2), round(res.natural_frequency, 1))
# 10.49 47.1
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

s = np.logspace(np.log10(2.0), np.log10(100.0), 300)   # MN/m3
for m in (40.0, 120.0):
    plt.semilogx(s, ph.natural_frequency(s * 1e6, m), label=f"m' = {m:g} kg/m²")
plt.xlabel("Dynamic stiffness s' [MN/m³]"); plt.ylabel("Natural frequency f₀ [Hz]")
plt.legend(); plt.show()
```

</details>

The `DynamicStiffnessResult` carries the apparent, enclosed-gas and installed
stiffnesses, the test resonance and the installed-floor natural frequency, and
its `.plot()` draws the `f₀(s')` design curve.

---

**Standards.** EN 29052-1:1992 (= ISO 9052-1:1989), *Acoustics — Determination
of dynamic stiffness — Part 1: Materials used under floating floors in
dwellings*: the dynamic stiffness per unit area (Formula 1), the resonance
relations (Formulae 2-4), the enclosed-gas term (Formula 7, clause 8.2 NOTE
`s'a = 111/d` MN/m³) and the airflow-resistivity regimes (Formulae 5-6).
Conformance is anchored on the standard's own numeric NOTE plus hand-computed
closed-form values of the resonance relations.

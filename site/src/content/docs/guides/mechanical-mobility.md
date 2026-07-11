---
title: "Mechanical mobility and the FRF family (ISO 7626-1)"
description: "The ISO 7626-1:2011 family of motion-per-force frequency-response functions: receptance, mobility and accelerance with their dynamic-stiffness, impedance and apparent-mass reciprocals (Table 1), conversion through the receptance pivot, and the single-degree-of-freedom reference resonator whose driving-point mobility peaks at 1/c on resonance (Annex A)."
---

Mechanical **mobility** is the complex ratio of a velocity response to the
force that produces it, `Y = v/F`. It is one member of a family of
motion-per-force **frequency-response functions** (FRFs): which one is used
depends only on whether the motion is a displacement, a velocity or an
acceleration, and each has a force-per-motion reciprocal. **ISO 7626-1:2011**
defines the whole family (Table 1) and the single-degree-of-freedom (SDOF)
reference resonator (Annex A). This FRF backbone underpins the structure-borne
source and transmission standards — ISO 9611, ISO 10846, EN 15657 and
EN 12354-5.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/mechanical_mobility.svg" alt="Normalized receptance, mobility and accelerance magnitudes of a single-degree-of-freedom resonator on a log-log frequency axis, all peaking at the resonance" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/mechanical_mobility_dark.svg" alt="Normalized receptance, mobility and accelerance magnitudes of a single-degree-of-freedom resonator on a log-log frequency axis, all peaking at the resonance" style="width:82%">

## 1. The frequency-response-function family (Table 1)

For a harmonic motion `x·e^{jωt}` the velocity is `jω·x` and the acceleration
`−ω²·x`, so all three motion-per-force FRFs follow from the receptance `H` by a
power of `jω`, and each has a force-per-motion reciprocal:

| Motion | FRF (motion / force) | Unit | Reciprocal (force / motion) | Unit |
|---|---|---|---|---|
| displacement | receptance `H = x/F` | m/N | dynamic stiffness `1/H` | N/m |
| velocity | mobility `Y = jω·H` | m/(N·s) | impedance `1/Y` | N·s/m |
| acceleration | accelerance `A = −ω²·H` | 1/kg | apparent mass `1/A` | kg |

`convert_frf` moves between any two of the six FRFs, pivoting through the
receptance. A **driving-point** FRF has the response and force at the same point
(`i = j`); a **transfer** FRF has them at different points.

```python
import phonometry as ph

# A mobility of 2e-3 m/(N.s) at 80 Hz, expressed as the other FRFs:
Y = 2e-3
print(round(abs(ph.convert_frf(Y, 80.0, "mobility", "impedance")), 1))     # 500.0  N.s/m
print(f"{abs(ph.convert_frf(Y, 80.0, 'mobility', 'accelerance')):.3f}")    # 1.005  1/kg
```

## 2. The SDOF reference resonator (Annex A)

The canonical closed-form reference is a mass `m`, viscous damping `c` and
stiffness `k`, whose receptance is

$$
H(\omega) = \frac{1}{k - \omega^2 m + j\,\omega c}, \qquad
\omega_0 = \sqrt{k/m}.
$$

At the resonance `ω0` the driving-point mobility is **purely real** and equal to
`1/c` — the mobility peak measures the damping — while the static receptance
(`ω → 0`) is the compliance `1/k`:

```python
import numpy as np
import phonometry as ph

m, k, c = 2.0, 8000.0, 5.0
f0 = ph.resonance_frequency(m, k)             # 10.07 Hz

y0 = complex(ph.sdof_mobility(f0, m, k, c))
print(round(y0.real, 4), round(y0.imag, 6))   # 0.2 0.0   -> |Y(f0)| = 1/c
print(round(complex(ph.sdof_receptance(1e-6, m, k, c)).real, 7))  # 0.000125 = 1/k
```

## 3. The `MobilityResult` bundle

`sdof_mobility_result` bundles the FRF over frequency into a `MobilityResult`,
which exposes `.magnitude`, `.phase`, `.to(target)` (any Table-1 kind) and a
`.plot()` of `|Y(f)|` with the resonance marked:

```python
import numpy as np
import phonometry as ph

f = np.logspace(np.log10(0.5), np.log10(200.0), 400)
res = ph.sdof_mobility_result(f, mass=2.0, stiffness=8000.0, damping=5.0)
z = res.to("impedance")                        # impedance = 1/Y per frequency
print(res.frequencies[int(np.argmax(res.magnitude))].round(1))   # ~10.1 Hz
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

m, k, c = 2.0, 8000.0, 5.0
f = np.logspace(np.log10(0.5), np.log10(200.0), 500)
w = 2.0 * np.pi * f
h = ph.sdof_receptance(f, m, k, c)
for label, frf in (("receptance |H|", np.abs(h)),
                   ("mobility |Y|", np.abs(1j * w * h)),
                   ("accelerance |A|", np.abs(-(w**2) * h))):
    plt.loglog(f, frf / frf.max(), label=label)
plt.axvline(ph.resonance_frequency(m, k), ls="--", color="0.6")
plt.xlabel("Frequency [Hz]"); plt.ylabel("Normalized magnitude")
plt.legend(); plt.show()
```

</details>

---

**Standards.** ISO 7626-1:2011, *Mechanical vibration and shock — Experimental
determination of mechanical mobility — Part 1: Basic terms and definitions, and
transducer specifications* — the FRF family and its reciprocals (Table 1), the
driving-point / transfer distinction, and the single-degree-of-freedom reference
resonator (Annex A). Conformance is anchored on the closed-form SDOF identities:
the driving-point mobility peak `|Y(ω0)| = 1/c`, the static receptance
`H(0) = 1/k`, and the exact Table-1 reciprocity `impedance·mobility = 1`.

---
title: "Mechanical mobility and the FRF family (ISO 7626-1)"
description: "The ISO 7626-1:2011 family of motion-per-force frequency-response functions: receptance, mobility and accelerance with their dynamic-stiffness, impedance and apparent-mass reciprocals (Table 1), conversion through the receptance pivot, the closed-form SDOF resonator whose driving-point mobility peaks at 1/c on resonance, and the ISO 7626-2:2015 measurement-side acceptance criteria."
---

Mechanical **mobility** is the complex ratio of a velocity response to the
force that produces it, `Y = v/F`. It is one member of a family of
motion-per-force **frequency-response functions** (FRFs): which one is used
depends only on whether the motion is a displacement, a velocity or an
acceleration, and each has a force-per-motion reciprocal. **ISO 7626-1:2011**
defines the whole family (Table 1, with the 3.1.2 mobility definition), and the
classic closed-form single-degree-of-freedom (SDOF) resonator serves as the
reference for those definitions. **ISO 7626-2:2015** adds the measurement side:
FRF estimation from measured signals and its acceptance criteria. This FRF
backbone underpins the structure-borne source and transmission standards —
ISO 9611, ISO 10846, EN 15657 and EN 12354-5.

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
(`i = j`); a **transfer** FRF has them at different points. Note that the
force-per-motion kinds are element-wise reciprocals — the *free* quantities of
ISO 7626-1, 3.1.4; the *blocked* matrix quantities of Table 1 do not invert
element-wise for multi-coordinate systems (Table 1 also names `F/a` the
"effective mass", the quantity called apparent mass here).

```python
import phonometry as ph

# A mobility of 2e-3 m/(N.s) at 80 Hz, expressed as the other FRFs:
Y = 2e-3
print(round(abs(ph.convert_frf(Y, 80.0, "mobility", "impedance")), 1))     # 500.0  N.s/m
print(f"{abs(ph.convert_frf(Y, 80.0, 'mobility', 'accelerance')):.3f}")    # 1.005  1/kg
```

The choice between the three motion FRFs is one of convenience, not physics:
they carry the same information and `convert_frf` moves between them exactly.
Accelerance is what an accelerometer-based measurement delivers directly;
mobility is the natural currency of the structure-borne power standards
(power is force times velocity, so `P = ½·Re{Y}·|F|²` at a contact); the
reciprocals appear whenever a source is described by what it imposes rather
than by how it responds. Reading a driving-point mobility plot is a
structural diagnosis in itself: below a resonance the magnitude climbs
proportionally to frequency along a **stiffness line** (`|Y| ≈ ω/k`), above
it the magnitude falls along a **mass line** (`|Y| ≈ 1/(ωm)`), and the height
of the peak between them measures the damping.

## 2. The SDOF reference resonator (closed form)

The canonical closed-form reference — expressed in the Table 1 / 3.1.2 FRF
taxonomy — is a mass `m`, viscous damping `c` and stiffness `k`, whose
receptance is

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

## 3. Measured FRFs and their acceptance criteria (ISO 7626-2)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_mobility_rig.svg" alt="ISO 7626 mobility measurement: a free-free beam on soft suspension driven by an exciter through an impedance head at the driving point, an accelerometer at a transfer point, and an impact hammer as the alternative excitation" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_mobility_rig_dark.svg" alt="ISO 7626 mobility measurement: a free-free beam on soft suspension driven by an exciter through an impedance head at the driving point, an accelerometer at a transfer point, and an impact hammer as the alternative excitation" style="width:92%">

In the ISO 7626-2 arrangement the structure hangs on a suspension soft enough
that its rigid-body modes fall well below the first elastic resonance, an
exciter drives one point through an **impedance head** (a transducer stack
measuring force and acceleration at the same point, which is what makes a
driving-point FRF possible), and accelerometers pick up the response
elsewhere for the transfer FRFs. ISO 7626-5 covers the impact-hammer
alternative, which trades the exciter's controlled spectrum for speed.

Processing measured random-excitation records per ISO 7626-2, 8.1.3 — the H1
estimator `Ĥ = G(response, force)/G(force, force)` — and the ordinary coherence
`γ² = |Gxy|²/(Gxx·Gyy)` used for its data-quality checks are the library's
existing spectral estimators [`transfer_function` and
`coherence`](/phonometry/guides/electroacoustics/) (H1 is their default). On
top of them, two ISO 7626-2 acceptance criteria are provided:

* **Operational rigid-mass calibration (7.5.2).** The measured FRF of a freely
  suspended rigid block of known mass must agree within ±5 % with `|A| = 1/m`
  (accelerance) or `|Y| = 1/(2πf·m)` (mobility).
* **Random error (Annex A + 8.1.3).** Enough spectra must be averaged that the
  normalized random error `ε = √((1−γ²)/(2nγ²))` at each resonance of a
  driving-point mobility is below 5 %.

```python
import numpy as np
import phonometry as ph

# A 10 kg calibration block: |A| must be 1/m = 0.100 1/kg at every frequency.
f = np.array([20.0, 100.0, 500.0])
res = ph.rigid_mass_calibration_check([0.100, 0.102, 0.097], f, mass=10.0)
print(res.passed, res.within_tolerance.tolist())   # True [True, True, True]

# The Annex A example: coherence 0.8 needs about 75 averages for < 5 %.
print(round(float(ph.random_error_percent(0.8, 75)), 2))   # 4.08  %
```

## 4. The `MobilityResult` bundle

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

## References

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3rd ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  The standard monograph on structural vibration: point and transfer
  mobilities of beams and plates, and the power flow `P = ½·Re{Y}·|F|²` that
  makes mobility the working quantity of this page.
- International Organization for Standardization. (2011). *Mechanical
  vibration and shock — Experimental determination of mechanical mobility —
  Part 1: Basic terms and definitions, and transducer specifications*
  (ISO 7626-1:2011).
  [iso.org catalogue](https://www.iso.org/standard/50426.html).
  The Table 1 FRF family and the free/blocked distinctions implemented here.
- International Organization for Standardization. (2015). *Mechanical
  vibration and shock — Experimental determination of mechanical mobility —
  Part 2: Measurements using single-point translation excitation with an
  attached vibration exciter* (ISO 7626-2:2015).
  [iso.org catalogue](https://www.iso.org/standard/62483.html).
  The measurement side: H1 processing, rigid-mass calibration and the
  random-error criterion.

---

**Standards.** ISO 7626-1:2011, *Mechanical vibration and shock — Experimental
determination of mechanical mobility — Part 1: Basic terms and definitions, and
transducer specifications* — the FRF family and its reciprocals (Table 1, the
3.1.2 mobility and 3.1.4 free-quantity definitions) and the driving-point /
transfer distinction. ISO 7626-2:2015, *Part 2: Measurements using single-point
translation excitation with an attached vibration exciter* — the 8.1.3 H1
processing of random excitation, the 7.5.2 rigid-mass operational calibration
(±5 %) and the Annex A random-error criterion (< 5 % at resonances).
Conformance is anchored on the closed-form SDOF identities (consistent with the
Table 1 / 3.1.2 definitions): the driving-point mobility peak `|Y(ω0)| = 1/c`,
the static receptance `H(0) = 1/k`, the exact Table-1 reciprocity
`impedance·mobility = 1`, the rigid-mass calibration values (`|A| = 0.100` 1/kg
for 10 kg; `|Y| = 1.59155e-4` m/(N·s) at 100 Hz) and the Annex A example
(γ² = 0.8, n = 75 → ε = 4.08 %).

## See also

- API reference: [`vibration.mechanical_mobility`](/phonometry/reference/api/vibration/mechanical-mobility/).

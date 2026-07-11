← [Documentation index](README.md)

# Dynamic transfer stiffness of resilient elements (ISO 10846)

The vibro-acoustic transfer property of a resilient element — a vibration
isolator, mount, bellows or hose — is its **dynamic transfer stiffness** `k₂₁`,
the frequency-dependent ratio of the *blocking force* on the output (receiver)
side to the displacement on the input (source) side (ISO 10846-1, 3.7):

$$
k_{2,1} = \frac{F_{2,b}}{u_1} \quad [\mathrm{N/m}].
$$

Because a vibration isolator is only effective between structures of large
driving-point stiffness, the force it delivers to the receiver approximates this
blocking force (ISO 10846-1, Eq. 7), so `k₂₁` is the quantity that characterises
the isolator's transmission. `k₂₁` feeds the structure-borne source and building
prediction standards — ISO 9611, EN 15657 and EN 12354-5.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/transfer_stiffness_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/transfer_stiffness.svg" alt="Dynamic transfer stiffness level of a Kelvin-Voigt isolator: the true level (flat at 120 dB, rising with the damping term at high frequency) and the indirect-method estimate, which diverges at the mass/spring resonance where the transmissibility is not small and converges to the true level above three times the resonance" width="82%"></picture>

## 1. The transfer-stiffness level and loss factor

Results are reported as a **level** re the reference stiffness `k₀ = 1 N/m`
(ISO 10846-2 and -3, 3.17), and in the low-frequency range where inertial forces
in the element are negligible the **loss factor** is the tangent of the phase
angle of `k₂₁` (ISO 10846-1, 3.8):

$$
L_k = 10\lg\frac{|k_{2,1}|^2}{k_0^2} = 20\lg\frac{|k_{2,1}|}{k_0}, \qquad
\eta = \frac{\mathrm{Im}(k_{2,1})}{\mathrm{Re}(k_{2,1})}.
$$

```python
import phonometry as ph

# A resilient mount with |k2,1| = 1 MN/m and a 5 % loss factor:
k = 1e6 * (1.0 + 0.05j)
print(round(float(ph.transfer_stiffness_level(k)), 2))   # 120.00  dB re 1 N/m
print(round(float(ph.loss_factor(k)), 3))                # 0.05
```

## 2. Direct and indirect determination

The **direct method** (ISO 10846-2) measures the blocked output force and the
input displacement, `k₂₁ = F₂,b/u₁`. The **indirect method** (ISO 10846-3) loads
the output with a compact blocking mass `m₂` and measures the vibration
transmissibility `T = u₂/u₁`; the blocking force is then the inertia force of the
mass (ISO 10846-3, Eq. 1):

$$
k_{2,1} = -(2\pi f)^2\,(m_2 + m_f)\,T \qquad (T \ll 1),
$$

with `m_f` the mass of the output flange. The approximation is valid well above
the mass/spring resonance, where `T` is small.

```python
import numpy as np
import phonometry as ph

# Indirect method: a 10 kg blocking mass, transmissibility 0.01 at 500 Hz.
k = ph.transfer_stiffness_indirect(500.0, 0.01, blocking_mass=10.0)
print(f"{abs(complex(k)):.3e}")            # 9.870e+05  N/m

# Bundle a swept measurement into a result carrying its level and loss factor:
f = np.logspace(1.5, 3.3, 200)
t = ph.base_transmissibility(f, mass=8.0, stiffness=1e6, damping=120.0)
res = ph.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
print(round(float(res.level[-1]), 1))      # ~126  dB re 1 N/m (high-f)
```

The `TransferStiffnessResult` carries the complex `k₂₁` and exposes `.level`,
`.loss_factor`, `.magnitude`, `.to("impedance"/"apparent_mass")` and `.plot()`.

## 3. Relation to the FRF family

The dynamic stiffness is a member of the frequency-response-function family
(ISO 10846-1, Annex A / Table A.2): it is the reciprocal of the receptance and
relates to the mechanical impedance `Z` and effective mass `m_eff` by
`k = jω·Z = −ω²·m_eff`. These conversions are the same as the
[mechanical-mobility](mechanical-mobility.md) `convert_frf` pivot:

```python
import phonometry as ph

k = 1e6 + 5e4j                                  # N/m, at 250 Hz
Z = ph.convert_frf(k, 250.0, "dynamic_stiffness", "impedance")
print(abs(complex(ph.convert_frf(Z, 250.0, "impedance", "dynamic_stiffness"))))  # 1.0012e6
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

k, c, m2 = 1e6, 120.0, 8.0
f0 = np.sqrt(k / m2) / (2 * np.pi)
f = np.logspace(np.log10(f0 / 5), np.log10(f0 * 40), 600)
w = 2 * np.pi * f
t = ph.base_transmissibility(f, m2, k, c)
plt.semilogx(f, ph.transfer_stiffness_level(k + 1j * w * c), label="true $L_k$")
plt.semilogx(f, ph.transfer_stiffness_level(ph.transfer_stiffness_indirect(f, t, m2)),
             "--", label="indirect method")
plt.axvline(f0, ls=":", color="0.6"); plt.legend()
plt.xlabel("Frequency [Hz]"); plt.ylabel("$L_k$ [dB re 1 N/m]"); plt.show()
```

</details>

---

**Standards.** ISO 10846 (parts 1-5), *Acoustics and vibration — Laboratory
measurement of vibro-acoustic transfer properties of resilient elements*: the
dynamic transfer stiffness `k₂₁ = F₂,b/u₁` and its FRF relations (Part 1,
clause 5 and Annex A / Table A.2), the level `L_k` re 1 N/m and the loss factor
(Parts 2 and 3, clauses 3.8/3.17), the direct method (Part 2) and the indirect
method `k₂₁ = −(2πf)²(m₂+m_f)T` (Part 3, Formula 1). Parts 4 and 5 extend the
same quantities to elements other than supports and to the driving-point
low-frequency method. Conformance is anchored on the standard's closed-form
definitions: the level of a decade of stiffness, the indirect inertia relation,
and the Table-A.2 identity `k = jω·Z`.

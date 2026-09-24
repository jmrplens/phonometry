← [Documentation index](../../README.md)

# Dynamic transfer stiffness of resilient elements (ISO 10846)

The vibro-acoustic transfer property of a resilient element (a vibration
isolator, mount, bellows or hose) is its **dynamic transfer stiffness**
$k_{2,1}$, the frequency-dependent ratio of the *blocking force* on the output
(receiver) side to the displacement on the input (source) side
(ISO 10846-1, 3.7):

$$
k_{2,1} = \frac{F_{2,\mathrm{b}}}{u_1} \quad [\mathrm{N/m}].
$$

Because a vibration isolator is only effective between structures of large
driving-point stiffness, the force it delivers to the receiver approximates this
blocking force (ISO 10846-1, Eq. 7), so $k_{2,1}$ is the quantity that
characterises the isolator's transmission. $k_{2,1}$ feeds the structure-borne
source and building prediction standards: ISO 9611, EN 15657 and EN 12354-5.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/transfer_stiffness_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/transfer_stiffness.svg" alt="Dynamic transfer stiffness level of a Kelvin-Voigt isolator: the true level (flat at 120 dB, rising with the damping term at high frequency) and the indirect-method estimate, which diverges at the mass/spring resonance where the transmissibility is not small and converges to the true level above three times the resonance" width="82%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import vibration

# Kelvin-Voigt isolator k + jwc loaded by an 8 kg blocking mass.
k, c, m2 = 1.0e6, 120.0, 8.0
f0 = np.sqrt(k / m2) / (2.0 * np.pi)
f = np.logspace(np.log10(f0 / 5.0), np.log10(f0 * 40.0), 600)

k_true = k + 1j * 2.0 * np.pi * f * c
t = vibration.base_transmissibility(f, m2, k, c)
k_indirect = vibration.transfer_stiffness_indirect(f, t, m2)  # warns where T is not small

# One line: the indirect determination bundled as a result draws its own
# Lk(f) level spectrum:
res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=m2)
res.plot()
plt.show()

# By hand, the true element stiffness against the indirect-method estimate:
fig, ax = plt.subplots()
ax.semilogx(f, vibration.transfer_stiffness_level(k_true),
            label="true $L_k$ of $k+j\\omega c$")
ax.semilogx(f, vibration.transfer_stiffness_level(k_indirect), "--",
            label="indirect method $-(2\\pi f)^2 m_2 T$")
ax.axvline(f0, color="0.6", linestyle=":", label="resonance $f_0$")
ax.set(xlabel="Frequency [Hz]", ylabel="Transfer stiffness level $L_k$ [dB re 1 N/m]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

## 1. The transfer-stiffness level and loss factor

Results are reported as a **level** re the reference stiffness
$k_0 = 1\ \text{N/m}$ (ISO 10846-2 and -3, 3.17), and in the low-frequency range
where inertial forces in the element are negligible the **loss factor** is the
tangent of the phase angle of $k_{2,1}$ (ISO 10846-1, 3.8):

$$
L_k = 10\log_{10}\frac{|k_{2,1}|^2}{k_0^2} = 20\log_{10}\frac{|k_{2,1}|}{k_0}, \qquad
\eta = \frac{\mathrm{Im}(k_{2,1})}{\mathrm{Re}(k_{2,1})}.
$$

```python
from phonometry import vibration

# A resilient mount with |k2,1| = 1 MN/m and a 5 % loss factor:
k = 1e6 * (1.0 + 0.05j)
print(round(float(vibration.transfer_stiffness_level(k)), 2))   # 120.01  dB re 1 N/m
print(round(float(vibration.loss_factor(k)), 3))                # 0.05
```

## 2. Direct and indirect determination

Why a *blocked* force rather than, say, the isolator's transmissibility?
Because a transmissibility is a property of a whole assembly: it changes with
whatever masses and stiffnesses the isolator happens to connect, so data
measured on one rig would not transfer to another installation. The blocked
force per unit input displacement is a property of the element alone, and it
predicts the force the element delivers to any receiver that is much stiffer
than the element itself, which is exactly the situation a vibration isolator
is designed for. ISO 10846 therefore sandwiches the isolator between a driven
input mass and an output that is either rigidly blocked or loaded with a
known mass:

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_transfer_stiffness_rig_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_transfer_stiffness_rig.svg" alt="ISO 10846 transfer-stiffness rigs: the isolator under test between a driven excitation mass and either a blocked output with a force transducer, the direct method, or a resiliently supported blocking mass, the indirect method" width="92%"></picture>

The **direct method** (ISO 10846-2) measures the blocked output force and the
input displacement, $k_{2,1} = F_{2,\mathrm{b}}/u_1$. The **indirect method**
(ISO 10846-3) loads the output with a compact blocking mass $m_2$ and measures
the vibration transmissibility $T = u_2/u_1$; the blocking force is then the
inertia force of the mass (ISO 10846-3, Eq. 1):

$$
k_{2,1} = -(2\pi f)^2\,(m_2 + m_\mathrm{f})\,T \qquad (T \ll 1),
$$

with $m_\mathrm{f}$ the mass of the output flange. The approximation is valid well above
the mass/spring resonance, where $T$ is small.

```python
import numpy as np
from phonometry import vibration

# Indirect method: a 10 kg blocking mass, transmissibility 0.01 at 500 Hz.
k = vibration.transfer_stiffness_indirect(500.0, 0.01, blocking_mass=10.0)
print(f"{abs(complex(k)):.3e}")            # 9.870e+05  N/m

# Bundle a swept measurement into a result carrying its level and loss factor:
f = np.logspace(1.5, 3.3, 200)
t = vibration.base_transmissibility(f, mass=8.0, stiffness=1e6, damping=120.0)
res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
print(round(float(res.levels[-1]), 1))      # 125.1  dB re 1 N/m (high-f)

res.plot()   # the Lk(f) level spectrum, as in the figure above (needs matplotlib)
```

The `TransferStiffnessResult` carries the complex $k_{2,1}$ and exposes `.levels`,
`.loss_factor`, `.magnitude`, `.to("impedance"/"apparent_mass")`,
`.band_average()` (section 4) and `.plot()`.

**Test-report fiche.** `TransferStiffnessResult.report(path)` renders a one-page
dynamic-transfer-stiffness characterisation report for a resilient element
(ISO 10846-1:2008 definition; determined by the direct method, ISO 10846-2:2008,
or the indirect blocking-mass method, ISO 10846-3:2002). The sheet shows the
$L_k(f)$ level spectrum beside a compact table of characteristic points (the
determination method, the blocking mass for the indirect method, the frequency
range, and the low-frequency stiffness plateau $|k_{2,1}|$, its level $L_k$
and the loss factor there), then the one-third-octave band levels
$L_{k,\mathrm{av}}$ of section 4 that the test report of both parts presents
(ISO 10846-2 9 m), ISO 10846-3 10 j)), and a boxed low-frequency $L_k$. The
characteristic points are read at the lowest *valid* line and the spectrum
draws the excluded lines apart; a band of fewer than five valid lines prints
its line count instead of a level. It is a characterisation, so there is no
pass/fail verdict; `language="es"` renders the Spanish fiche. The fiche always
embeds the $L_k(f)$ spectrum, so it needs both the report and plot extras
(`pip install "phonometry[report,plot]"`).

[![ISO 10846 dynamic-transfer-stiffness example report: a metadata header, a table of the FRF characteristic points (method, frequency range and low-frequency stiffness, level and loss factor) beside the transfer-stiffness level spectrum, the 21 one-third-octave band levels from 20 Hz to 2 kHz, and the boxed low-frequency level](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/iso10846_transfer_stiffness_example.webp)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/iso10846_transfer_stiffness_example.pdf)

The two methods split the frequency axis between them. The direct method
works from 1 Hz, the lower bound of the ISO 10846-2 scope (in practice the
floor is set by the rig and its instrumentation), up to where the test rig's
own resonances intrude (typically a few hundred hertz for large elements); the
indirect method only becomes valid well above the blocking-mass/spring
resonance, where the transmissibility is small, and extends the
characterisation into the kilohertz range. A full isolator dataset is
usually the two spliced together. Hydraulic mounts are outside the
single-spectrum description altogether: their stiffness is
amplitude-dependent by design, so one $L_k(f)$ does not characterise them.

## 3. Validity of the indirect method

ISO 10846-3 (clause 6) requires the $T \ll 1$ approximation to be accurate
within **1 dB** (12 % of the stiffness magnitude), which bounds the usable
frequency range on both sides:

* **Impedance mismatch (Inequality 2).** Valid only where
  $\Delta L_{1,2} = L_{a1} - L_{a2} \ge 20\ \text{dB}$, i.e. $|T| \le 0.1$, the
  constant `TRANSMISSIBILITY_LIMIT`. `transfer_stiffness_indirect` computes the
  per-band $|T|$ and emits a `TransferStiffnessWarning` when any band exceeds
  it (routine near or below the mass/spring resonance, as in the figure
  above); the result it builds marks those bands as not valid.
* **Rigid blocking mass (Inequality 3).** Above an upper frequency $f_3$ the
  blocking mass no longer moves as a rigid body; results are valid only while
  its measured effective mass $m_{2,\text{eff}} = 2F_2/(a'_1 + a''_1)$ (Eq. 4)
  stays within 1 dB of the rigid mass:
  $|10\log_{10}(m_{2,\text{eff}}^2/m_2^2)| \le 1\ \text{dB}$.
  `effective_blocking_mass` finds $f_3$ from that measurement (section 5).
* **Linearity (clause 7.6).** Two input spectra 10 dB apart must give
  transfer-stiffness levels within 1.5 dB.

Inequality 2 is computed with the indirect method itself and Inequality 3
through the effective mass of section 5; the linearity criterion (ISO 10846-3
clause 7.6, and clause 7.7 of Parts 2, 4 and 5) is described here and left to
the operator, as are the preload, creep and temperature conditioning.

The blocking-force idealisation itself is quantified by ISO 10846-1, Eq. (6):
for an isolator of output driving-point stiffness $k_{2,2}$ on a termination of
stiffness $k_\mathrm{t}$, the delivered force is $F_2/F_{2,\mathrm{b}} = 1/(1 + k_{2,2}/k_\mathrm{t})$,
within 10 % of the blocking force for $|k_{2,2}| < 0.1\,|k_\mathrm{t}|$ (Eq. 7):

```python
import warnings
from phonometry import vibration

# |T| = 0.5 violates Inequality (2): the indirect result is flagged.
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    vibration.transfer_stiffness_indirect(50.0, 0.5, blocking_mass=10.0)
print(caught[0].category.__name__)                     # TransferStiffnessWarning

# Blocking-force approximation at the 10 % limit (ISO 10846-1, Eq. 6):
print(round(abs(complex(vibration.blocking_force_ratio(1e5, 1e6))), 4))   # 0.9091
```

## 4. One value per one-third-octave band

A swept or stepped measurement gives $k_{2,1}$ at hundreds of lines, and every
part of the series reports it as one value per one-third-octave band: the
squared magnitude averaged over the $n$ lines the band holds (ISO 10846-2
Formula (6), -3 Formula (7), -4 Formula (11), -5 Formula (6)),

$$
k_\mathrm{av} = \left\{ \frac{1}{n} \sum_{i=1}^{n} \lvert k_{2,1}(f_i) \rvert^2 \right\}^{1/2},
\qquad L_{k,\mathrm{av}} = 10 \lg \frac{k_\mathrm{av}^2}{k_0^2},
$$

"where the summation is performed over a minimum of $n = 5$ frequencies".
Averaging the square rather than the level weights the peaks, and the phase is
lost. The five lines are also a requirement on the measurement (the analyser
shall resolve at least five distinct frequencies per band), so
`band_averaged_stiffness` gives a band of one to four lines no value (NaN) and
a `TransferStiffnessWarning`. It assigns each line to the base-ten band that
encloses it, names the bands by their ISO 266 centres, and leaves out first the
lines that failed an adequacy condition: the indirect result marks the lines
with $|T| > 0.1$, so its `.band_average()` averages only the valid part of the
sweep.

```python
import warnings
import numpy as np
from phonometry import vibration

# Direct method, a Kelvin-Voigt mount k + jwc, lines every 2 Hz:
f = np.arange(90.0, 1120.0, 2.0)
k21 = 1.0e6 + 1j * 2.0 * np.pi * f * 80.0
direct = vibration.TransferStiffnessResult(
    frequencies=f, transfer_stiffness=vibration.transfer_stiffness_direct(k21 * 1e-6, 1e-6)
)
bands = direct.band_average()
print(bands.nominal_frequencies[[0, -1]], bands.line_counts[[0, -1]])  # [ 100. 1000.] [ 12 114]
print(round(float(bands.levels[-1]), 2))                               # 120.99  dB re 1 N/m

# Indirect method on an 8 kg blocking mass: |T| falls to 0.1 at 187.5 Hz, so the
# lines up to 186 Hz fail Inequality (2) and never reach the average; the 200 Hz
# band averages its 18 lines from 188 Hz up.
t = vibration.base_transmissibility(f, mass=8.0, stiffness=1.0e6, damping=120.0)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", vibration.TransferStiffnessWarning)
    indirect = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
bands = indirect.band_average()
print(bands.nominal_frequencies[0], bands.line_counts[0])  # 200.0 18
bands.plot()   # the band levels, the undetermined bands marked (needs matplotlib)
```

## 5. Checking the rig from the measured spectra

Three of the adequacy conditions of the series are level differences or a
mass, and can be judged from what the rig measured. Each check returns the
condition frequency by frequency with an overall `.passes`, draws itself with
`.plot()`, and warns (`TransferStiffnessWarning`) where the condition fails.

* **The output is blocked**, $\Delta L_{1,2} = L_{a1} - L_{a2} \ge 20$ dB
  (ISO 10846-5 Inequality (1); Inequality (1) of Part 2, (2) of Parts 3 and
  4): `check_blocked_output`.
* **The input moves in one direction**, the excitation direction at least
  15 dB above each perpendicular one (Part 5 Inequality (2); (3) of Part 2,
  (5) of Part 3, (7) of Part 4): `check_unwanted_input`, the loudest unwanted
  direction deciding. ISO 10846-2 7.6.1 sends the exclusion of the lines that
  fail it to "6.1, Inequality (1)", the blocked-output condition, where 6.4,
  Inequality (3), is meant (see the [errata](../../ERRATA.md)).
* **The mass in front of the output force transducers is light enough** for
  the direct method (ISO 10846-4 Inequality (3), ISO 10846-2 Inequality (2)),
  $m_0 \le 0{,}06 \times 10^{L_{F2}/20} / 10^{L_{a2}/20}$ kg with $L_{F2}$ re
  1 µN and $L_{a2}$ re 1 µm/s², that is $0{,}06\,|F_2|/|a_2|$. On the bound the
  force levels differ by 0,51 dB (inertia force in phase) to 0,54 dB (against
  it): the 0,5 dB of NOTE 1, which ISO 10846-4 prints as "05 dB" (see the
  [errata](../../ERRATA.md)). `check_output_mass` returns the limit and that
  worst-case bias, `bias_bound_db`.

For the indirect method, ISO 10846-4 Formula (6) (ISO 10846-3 Formula (4))
measures the effective mass of the blocking mass,
$m_{2,\mathrm{eff}} = |2F_2/(a'_1 + a''_1)|$, and its upper limit $f_3$ is the
lowest frequency at which it departs from $m_2$ by more than 1 dB,
Inequality (5), a departure below 40 Hz being ignored.
`effective_blocking_mass` interpolates that crossing.

```python
import numpy as np
from phonometry import vibration

f = [63.0, 125.0, 250.0]
check = vibration.check_blocked_output(f, [110.0, 110.0, 110.0], [85.0, 88.0, 86.0])
print(check.holds, check.passes)                        # [ True  True  True] True

# m0 = 0.4 kg (output flange, force distribution plate, half the transducers):
mass = vibration.check_output_mass([125.0], 0.4, [120.0], [100.0])
print(mass.mass_limit_kg, mass.passes, mass.bias_bound_db.round(3))   # [0.6] True [0.355]

fe = np.geomspace(20.0, 5000.0, 400)
m_eff = 20.0 * (1.0 + (fe / 3000.0) ** 2)
ones = np.ones(fe.size, dtype=complex)
block = vibration.effective_blocking_mass(fe, m_eff * ones, ones, ones, blocking_mass_kg=20.0)
print(round(block.upper_frequency_limit_hz, 1))         # 1047.9  Hz
```

## 6. The driving-point method (ISO 10846-5)

With the output of the element blocked, the input force and the input
acceleration give the driving-point stiffness (Formula (3)),
$k_{1,1}(f) = F_1/u_1 = -(2\pi f)^2 F_1/a_1$, which equals the transfer
stiffness only at low frequencies. The upper limiting frequency
$f_\mathrm{UL}$ of clause 6.2 is the lowest frequency at which the
driving-point stiffness level is 2 dB below its average from 1 Hz to 20 Hz; up
to it the band averages of $k_{1,1}$ stand for those of $k_{2,1}$ within 2 dB
(Formula (7)). `driving_point_stiffness` computes $k_{1,1}$, finds
$f_\mathrm{UL}$, checks Inequalities (1) and (2) when given the output or the
unwanted accelerations, and its `.band_average()` averages only the valid
lines at or below $f_\mathrm{UL}$ (8.3: "if $f \le f_\mathrm{UL}$"). The 2 dB
for those bands is the standard's statement, which Annex B assumes again
(B.3.5); the 6.2 criterion only watches $k_{1,1}$ fall below its own
low-frequency value.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/driving_point_stiffness_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/driving_point_stiffness.svg" alt="Driving-point stiffness level of a 1 MN/m element driven through a 2 kg force distribution plate: flat at 120 dB at low frequency and falling away as the plate's inertia grows, with the threshold 2 dB below the 1 to 20 Hz value, the upper limiting frequency at 52.2 Hz and the band averages below it, all within the plus or minus 2 dB of Formula (7)" width="82%"></picture>

```python
import numpy as np
from phonometry import vibration

f = np.arange(1.0, 200.0, 0.2)          # the 0.2 Hz lines of 7.5
w = 2.0 * np.pi * f
k21 = 1.0e6 * (1.0 + 0.05j)
res = vibration.driving_point_stiffness(f, (k21 - w**2 * 2.0) * 1e-6, -(w**2) * 1e-6)
print(round(res.upper_limiting_frequency_hz, 1))    # 52.2  Hz

# Annex B: u from signal 0.3, instrumentation 0.5, repeatability p/sqrt(3),
# test rig 1/(2 sqrt 3), driving-point discrepancy 2/sqrt 3 and linearity
# 1.5/(2 sqrt 3) dB, and U = 2u (B.3).
budget = vibration.driving_point_uncertainty(119.3, repeatability_range_db=0.6)
print(round(budget.combined_uncertainty_db, 3))    # 1.405  dB
print(round(budget.expanded_uncertainty_db, 2))    # 2.81  dB
```

The three rectangular terms of the budget are the expressions Annex B prints,
0,289, 1,155 and 0,433 dB. Table B.1 carries them rounded up to one decimal,
0,3, 1,2 and 0,5 dB, the conservative rounding an uncertainty may take
(ISO/IEC Guide 98-3, 7.2.6); the library keeps the expressions, and every term
can be passed in to reproduce the table.

## 7. Relation to the FRF family

The dynamic stiffness is a member of the frequency-response-function family
(ISO 10846-1, Annex A / Table A.2): it is the reciprocal of the receptance and
relates to the mechanical impedance $Z$ and effective mass $m_\text{eff}$ by
$k = j\omega Z = -\omega^2 m_\text{eff}$. These conversions are the same as the
[mechanical-mobility](mechanical-mobility.md) `convert_frf` pivot:

```python
from phonometry import vibration

k = 1e6 + 5e4j                                  # N/m, at 250 Hz
Z = vibration.convert_frf(k, 250.0, "dynamic_stiffness", "impedance")
print(abs(complex(vibration.convert_frf(Z, 250.0, "impedance", "dynamic_stiffness"))))  # 1.0012e6
```

## 8. Test-report fiche

`TransferStiffnessResult.report(path)` renders a one-page
dynamic-transfer-stiffness characterisation report for a resilient element
(ISO 10846-1:2008 definition; determined by the direct method, ISO 10846-2:2008,
or the indirect blocking-mass method, ISO 10846-3:2002). The sheet shows the
$L_k(f)$ level spectrum beside a compact table of characteristic points (the
determination method, the blocking mass for the indirect method, the frequency
range, and the low-frequency stiffness plateau $|k_{2,1}|$, its level $L_k$
and the loss factor there), then the one-third-octave band levels
$L_{k,\mathrm{av}}$ of section 4 that the test report of both parts presents
(ISO 10846-2 9 m), ISO 10846-3 10 j)), and a boxed low-frequency $L_k$. The
characteristic points are read at the lowest *valid* line and the spectrum
draws the excluded lines apart; a band of fewer than five valid lines prints
its line count instead of a level. It is a characterisation, so there is no
pass/fail verdict; `language="es"` renders the Spanish fiche. The fiche always
embeds the $L_k(f)$ spectrum, so it needs both the report and plot extras
(`pip install "phonometry[report,plot]"`).

```python
import numpy as np
from phonometry import ReportMetadata, vibration

# Ten lines in every one-third-octave band from 20 Hz to 2 kHz:
freqs = 1000.0 * 10.0 ** ((np.arange(-175, 35) + 0.5) / 100.0)
k21 = 1e6 + 1j * (2 * np.pi * freqs) * 80.0     # Kelvin-Voigt element k + jwc
u1 = 1e-6 + 0j
k = vibration.transfer_stiffness_direct(k21 * u1, u1)     # direct method: k2,1 = F2,b/u1
res = vibration.TransferStiffnessResult(frequencies=freqs, transfer_stiffness=k)
res.report(
    "transfer_stiffness.pdf",
    metadata=ReportMetadata(
        specimen="Rubber vibration isolator",
        measurement_standard="ISO 10846-2",
    ),
)   # one-page fiche (needs phonometry[report,plot])
```

The example fiche is regenerated with `make reports` and kept in the
repository. Click the preview to open the PDF:

[![ISO 10846 dynamic-transfer-stiffness example report: a metadata header, a table of the FRF characteristic points (the determination method, the frequency range and the low-frequency stiffness, level and loss factor) beside the transfer-stiffness level spectrum, the 21 one-third-octave band levels from 20 Hz to 2 kHz, and the boxed low-frequency level](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/iso10846_transfer_stiffness_example.webp)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/iso10846_transfer_stiffness_example.pdf)

*Dynamic-transfer-stiffness fiche (`TransferStiffnessResult.report`): the FRF
characteristic points, the transfer-stiffness level spectrum and its
one-third-octave band levels.*

## See also

- [Mechanical mobility and the FRF family (ISO 7626-1)](mechanical-mobility.md):
  the source/receiver mobility rule that says when a blocked force is the right
  description at all, and the FRF vocabulary this page's conversions belong to.
- [Structure-borne sound power of equipment (EN 15657)](../../buildings/design/structure-borne-power.md):
  the source characterisation that sits on the other side of the isolator.
- [Installed structure-borne sound (EN 12354-5)](../../buildings/design/installed-structure-borne.md):
  the prediction that consumes $k_{2,1}$ together with both mobilities and
  turns it into a level in a receiving room.
- API reference: [`vibration.structural.transfer_stiffness`](https://jmrplens.github.io/phonometry/reference/api/vibration/transfer-stiffness/) and [`vibration.structural.mechanical_mobility`](https://jmrplens.github.io/phonometry/reference/api/vibration/mechanical-mobility/).
- Theory: [Point mobilities and radiation efficiency](../../reference/theory/vibration.md#point-mobilities-and-radiation-efficiency-cremer-5-hopkins-29): the mobility and impedance definitions the transfer stiffness is the reciprocal of.

## References

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3rd ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  Vibration isolation theory: why an isolator's performance depends on the
  source and receiver mobilities, the physics behind the blocked-force
  characterisation.
- International Organization for Standardization. (2008). *Acoustics and
  vibration — Laboratory measurement of vibro-acoustic transfer properties of
  resilient elements — Part 1: Principles and guidelines* (ISO 10846-1:2008).
  [iso.org catalogue](https://www.iso.org/standard/38936.html).
  The principles part of the series: the blocking-force idealisation and the
  FRF relations this page implements.

## Standards

ISO 10846 (parts 1-5), *Acoustics and vibration — Laboratory
measurement of vibro-acoustic transfer properties of resilient elements*: the
dynamic transfer stiffness $k_{2,1} = F_{2,\mathrm{b}}/u_1$ and its FRF relations (Part 1,
clause 5 and Annex A / Table A.2), the level $L_k$ re 1 N/m and the loss factor
(Parts 2 and 3, clauses 3.8/3.17), the direct method (Part 2) and the indirect
method $k_{2,1} = -(2\pi f)^2 (m_2 + m_\mathrm{f}) T$ (Part 3, Formula 1) with its
validity
conditions (Part 3, clause 6: Inequalities 2 and 3; clause 7.6 linearity) and
the blocking-force approximation (Part 1, Eqs. 6/7). Part 4 (2003) extends the
same quantities to elements other than supports, with the output-mass limit of
its Inequality (3), the effective blocking mass of its Formula (6) and the
band average of its Formula (11); Part 5 (2008) is the driving-point
low-frequency method, with Formula (3), the upper limiting frequency of 6.2,
Formula (7) and the Annex B budget. Conformance is anchored on the standard's
closed-form definitions: the level of a decade of stiffness, the indirect
inertia relation, the Table-A.2 identity $k = j\omega Z$, the
$|T| = 0.1 \leftrightarrow \Delta L_{1,2} = 20\ \text{dB}$ validity
limit and its 1 dB (12 %) accuracy bound, the Eq. (6) force ratio $1/1.1$, and
the linearity criterion (7.7 of Part 2, 7.6 of Part 3); Parts 4 and 5 print no
worked example, and their rows are closed forms too (a band of identical lines
averages to itself, a massless spring gives a flat stiffness, the output mass
on its bound biases the force by 0,51 to 0,54 dB, the 0,5 dB of NOTE 1).

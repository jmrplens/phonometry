← [Documentation index](../../README.md)

# Free-field corrections of a sound level meter (IEC 62585)

A periodic test of a sound level meter by IEC 61672-3 drives the microphone
with a sound calibrator, a comparison coupler or an electrostatic actuator,
and none of those is the plane progressive wave the meter is specified for.
The test needs, at each frequency, the **correction** that turns what the
meter indicates on that source into what it would indicate in a free field of
the same level, and the manufacturer states it in the manual. IEC 62585:2012
gives the methods for finding those corrections, the uncertainty they may
carry, and the adjustment value the manual quotes at the calibration check
frequency. This page runs every step on a synthetic class 1 meter and on the
two worked budgets the standard prints.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_correction_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_correction.svg" alt="The free-field correction of a synthetic meter at the nine exact octaves from 63 Hz to 16 kHz: on a multi-frequency calibrator by Formula (D.7), rising from about 0 dB up to 1 kHz to 5 dB at 16 kHz with the range of three microphones around it, and on an electrostatic actuator by Formula (F.13), zero at 1 kHz and 7.4 dB at 16 kHz" width="100%"></picture>

## The adjustment value at the calibration check frequency

The manufacturer sets the sensitivity so that the free-field response deviates
as little as it can from the incident level over the whole frequency range,
then applies the calibrator and reads `L4`; the manual states
`Delta L = L1 - L4` as a fixed number (Annex A, clause 8). The text prints no
formula for the fit, and `metrology.adjustment_value` takes the least-squares
reading, the adjustment `s = -sum(w d) / sum(w)` with weights `w = 1/t²` for
the tolerance `t` at each frequency:

```python
import numpy as np
from phonometry import filters, metrology

f3 = metrology.exact_frequencies(63, 16000, fraction=3)   # 25 exact one-third octaves
nominal, lower, upper = filters.weighting_class_limits(1)  # IEC 61672-1 Table 3, class 1
band = (nominal >= 63) & (nominal <= 16000)
tolerance = np.minimum(upper, -lower)[band]                # the narrower side at each band

x3 = f3 / 1000
response = 0.4 + 0.12 * np.cos(3 * np.log(x3)) - 0.3 * (x3 / 8) ** 2   # indication less field, dB
a = metrology.adjustment_value(
    f3, 94.0 + response, 94.35, calibrator_level_db=94.0, tolerance_db=tolerance
)
print(round(a.sensitivity_adjustment_db, 2), round(a.adjustment_db, 2))  # -0.37 0.02
print(round(a.check_frequency_offset_db, 2))                           # 0.15
```

The adjusted meter reads a free field 0,15 dB high at 1 kHz: the offset the
fit chose so the response sits inside the tolerances everywhere else.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_adjustment_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_adjustment.svg" alt="The free-field deviation of the synthetic meter before and after the adjustment of Annex A, 63 Hz to 16 kHz, inside the class 1 tolerance band; Delta L = 0.02 dB" width="88%"></picture>

## How the measurement goes

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_free_field_corrections_setup_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_free_field_corrections_setup.svg" alt="The readings of IEC 62585: a meter and a type LS2P reference microphone read the same free field in turn, then the same source, a sound calibrator (Formula (D.7)), a comparison coupler with both face to face (Formula (E.6)) or an electrostatic actuator on the meter (Formula (F.13))" width="92%"></picture>

| Requirement | Value | Clause |
| :--- | :--- | :--- |
| Environment | 80 kPa to 105 kPa, 20 °C to 26 °C, 25 % to 70 % relative humidity; below 97 kPa an extra component enters the budget | 6 |
| Free-field mounting | On a rod of the microphone's diameter; source more than 1 m away and at least six times the largest dimension of the meter | 6 |
| Samples | Three calibrators, three microphones and one meter; five microphones for a typical response, five windscreens | 7 |
| Source level | 70 dB to 125 dB in a calibrator or coupler; 80 dB to 105 dB on the display with an actuator | 12, 13, 14 |
| Frequencies | Exact base-ten frequencies of Annex H | 10, B.2, C.2 |

## The corrections for a calibrator, a coupler and an actuator

Every method compares the meter with a type LS2P reference microphone, whose
free-field correction `C_FF,RM` comes from IEC/TS 61094-7 and is an input. On
a calibrator (Formula (D.7)),
`C_FF,SLM = (L_ind1 - L_ind3) - (L_ind2 - L_ind4) - (L_p,F1 - L_p,F2) + (L_p,P1 - L_p,P2) + C_FF,RM`:

```python
f = metrology.exact_frequencies(63, 16000, fraction=1)   # the nine exact octaves
x = f / 1000
c_ff_rm = 0.05 * x**1.3                        # C_FF,RM of the reference: illustrative
free = 0.1 * np.sin(np.log(x)) - 0.05 * x**1.2  # the meter in a free field, re the field
pressure = -0.1 * x**1.5                        # the meter on the calibrator, re its level
spread = np.array([[0.0], [0.02], [-0.03]]) * x**0.8   # three microphones of the model

c = metrology.sound_calibrator_correction(
    f,
    94.0 + free + spread,          # L_ind1: the meter in the free field
    94.0 + c_ff_rm,                # L_ind2: the reference in its place
    94.0 + pressure + spread / 2,  # L_ind3: the calibrator on the meter
    94.0,                          # L_ind4: the calibrator on the reference
    reference_free_field_correction_db=c_ff_rm,
)
print(c.correction_db.round(2))  # [-0.04 -0.09 -0.1  -0.05  0.05  0.23  0.63  1.72  4.95]
print(c.clause, c.formula)       # 12 D.7
```

`metrology.comparison_coupler_correction` names its two readings in the
coupler by what each is of, `slm_coupler_level_db` and
`reference_coupler_level_db`, because Formulas (E.4) to (E.6) exchange the two
labels Figure E.1 defines (an [erratum](../../ERRATA.md)).
`metrology.electrostatic_actuator_correction` returns the correction of
Formula (F.13), normalised to the calibration check frequency, where it is
zero.

## The uncertainty budget of Annex I

`metrology.correction_uncertainty_budget` takes the fifteen components of
Table I.1 as Table I.2 states them, divides each by its divisor (`√3`, 2 for
`C_FF,RM`, 1 for the repeatability), combines them on
`metrology.combine_uncertainty` and takes the coverage factor from the
Welch-Satterthwaite effective degrees of freedom at 95 %:

```python
table_i2 = {
    "a1": 0.005, "a2": 0.005, "a3": 0.005, "a4": 0.005, "a5": 0.05, "a6": 0.0,
    "a7": 0.06, "a8": 0.025, "a9": 0.025, "a10": 0.029, "a11": 0.013,
    "a12": 0.013, "a13": 0.0, "a14": 0.005, "a15": 0.03,
}
b1 = metrology.correction_uncertainty_budget(table_i2, repeatability_dof=2, frequency_hz=1000)
print(round(b1.combined_uncertainty_db, 4), round(b1.effective_dof, 2))   # 0.059 29.98
print(round(b1.coverage_factor, 2), round(b1.expanded_uncertainty_db, 2))  # 2.04 0.12
```

Tables I.2 and I.3 both reproduce. Table I.2 prints `k = 2,11`, which is not
the factor its own 29,98 degrees of freedom give: at 95 % that is 2,04, and
2,11 is the one for about 17 (an [erratum](../../ERRATA.md)).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_uncertainty_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_uncertainty.svg" alt="The standard uncertainty of each of the fifteen components of Table I.1 at 1 kHz (u_c = 0.0590 dB, k = 2.04, U = 0.121 dB) and at 8 kHz (u_c = 0.1400 dB, k = 2.00, U = 0.280 dB)" width="100%"></picture>

## The maximum permitted uncertainty, and the verdict

| Clause | Correction for | Maximum expanded uncertainty |
| :--- | :--- | :--- |
| 9 | Reflections from the case, diffraction round the microphone | 0,25 dB up to and including 4 kHz; 0,35 dB above |
| 10 | The microphone's deviation from a uniform response | 0,25 dB from 63 Hz to 4 kHz; 0,35 dB to 8 kHz; 0,45 dB above |
| 11 | Windscreens and similar accessories | 0,20 dB up to and including 4 kHz; 0,30 dB above |
| 12, 13, 14 | A calibrator, a coupler, an actuator | 0,25 dB up to and including 4 kHz; 0,35 dB below 10 kHz; 0,50 dB from 10 kHz |

`metrology.verify_correction_uncertainty` judges the expanded uncertainty at
each frequency against the maximum of the clause, and for clauses 12 to 14 the
range of the corrections over the microphones too; the verdict carries
`passes`, and `bool()` of it raises. `.report()` renders the documentation of
clause 15 n) and o) as a one-page fiche:

```python
v = metrology.verify_correction_uncertainty(
    f, 0.12 + 0.02 * x**0.8, clause=c.clause, correction_db=c.correction_db,
    correction_range_db=c.range_db,
)
print(v.passes)   # True
```

[![One-page fiche of the corrections of a class 1 meter on its calibrator with their expanded uncertainty, coverage factor, maximum, range over three microphones and verdict at the nine exact octaves, and a PASS verdict against clause 12](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/iec62585_free_field_correction_example.webp)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/iec62585_free_field_correction_example.pdf)

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_verification_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_verification.svg" alt="The expanded uncertainty of the calibrator's corrections and their range over three microphones, under the stepped maximum of clause 12" width="88%"></picture>

## Exact frequencies

Annex H gives the exact base-ten frequencies by Formula (H.1),
`f_x = 1000 · 10^(3x/10b)` Hz, with `b = 12` for one-twelfth octaves:

```python
h = metrology.exact_frequencies(1000, 10000)   # the 41 rows of Table H.1
print(h.size, (h[[1, 31, 40]] / 1000).round(6))   # 41 [ 1.059254  5.956621 10.      ]
```

All 41 values of Table H.1 reproduce; its exponent column prints `10^(31/80)`
for index 31, where the value is `10^(31/40)` (an [erratum](../../ERRATA.md)).

## What this guide covers

Implemented: the adjustment value of Annex A (the least-squares fit is this
library's reading of a text that prints no formula); the free-field
corrections for a multi-frequency calibrator, a comparison coupler and an
electrostatic actuator (Formulas (D.7), (E.6) and (F.13)), averaged over the
determinations with their range kept; the uncertainty budget of Annex I with
the fifteen components of Table I.1, the static-pressure component of clause 6
and the Welch-Satterthwaite coverage factor; the maxima of clauses 9 to 14 as
a verdict and a fiche; and the exact frequencies of Annex H. Not implemented:
the measurements themselves, the techniques of Annex G, the free-field
correction of the reference microphone (an input from IEC/TS 61094-7), and the
comparison of the corrections with the IEC 61672-1 acceptance limits that
clause 15 p) asks for separately.

## See also

- [Random-incidence and diffuse-field response (IEC 61183)](random-incidence.md):
  the response of the meter to sound from every direction.
- [Measurement uncertainty](gum-uncertainty.md): the GUM law of propagation
  and the Welch-Satterthwaite degrees of freedom the budget is built on.
- [Compliance and verification](compliance-verification.md): what the
  IEC 61672-1 class of a meter asserts.
- [Errata in published sources](../../ERRATA.md): Table I.2, Table H.1 and
  Formulas (E.4) to (E.6).
- API reference: [`metrology.free_field_corrections`](https://jmrplens.github.io/phonometry/reference/api/metrology/free-field-corrections/).

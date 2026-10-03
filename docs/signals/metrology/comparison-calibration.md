← [Documentation index](../../README.md)

# Microphone calibration by comparison (IEC 61094-5 and IEC 61094-8)

A working standard microphone is not calibrated by reciprocity. It is put
beside a reference microphone whose sensitivity is already known, or in its
place, both are exposed to the same sound pressure, and the ratio of their
output voltages carries the reference's sensitivity over to it. IEC
61094-5:2016 does this in a **pressure field**, in a coupler or a jig; IEC
61094-8:2012 does it in a **free field**, in an anechoic room or behind a
time window. Annex D of the first part writes the model once for both,
`M_test = M_ref · R_V / R_P`, and `metrology.comparison_calibration` computes
it in sensitivity levels, `L_test = L_ref + 20 lg R_V - 20 lg R_P + sum(C_j)`,
with `R_V` the ratio of the output voltages, `R_P` that of the effective sound
pressures (reduced to unity by the procedure) and `C_j` the corrections each
part asks for. This page runs a pressure calibration of a WS2P against an
LS2P and a free-field calibration of a WS2F on synthetic readings, so every
step can be checked against the sensitivities that built them.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_calibration_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_calibration.svg" alt="The sensitivity level of a WS2P calibrated in a pressure field against an LS2P, 250 Hz to 20 kHz, and of a WS2F calibrated in a free field by substitution, 500 Hz to 20 kHz, each with a band of its expanded uncertainty and the reference's level it was compared with: the pressure level in the coupler, the free-field level in the free field" width="100%"></picture>

## How the measurement goes

With **simultaneous excitation** both microphones sit in the field at once,
each on its own measuring channel; in a coupler or a jig they face each other
about 1 mm apart (IEC 61094-5 5.1.2). With **sequential excitation** they take
the same place in turn: either the exchange does not change the sound pressure
significantly, or any change is detected and corrected, for example with a
monitor microphone near the source (IEC 61094-5 5.1.3, IEC 61094-8 5.2, 6.5
and A.2).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_comparison_calibration_setup_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_comparison_calibration_setup.svg" alt="The readings of a comparison calibration: in a coupler, the reference and the microphone under test read on two channels, then interchanged (IEC 61094-5 Annex C, Formula (C.3)); in a free field, the reference and then the microphone under test at the same point, each read against a monitor microphone near the source (IEC 61094-8 A.2)" width="100%"></picture>

| Requirement | Value | Clause |
| :--- | :--- | :--- |
| Reference conditions | 23,0 °C, 101,325 kPa, 50 % relative humidity | 61094-5 and 61094-8, 4 |
| Simultaneous, in a coupler or a jig | Diaphragms about 1 mm apart; the microphones interchanged and the measurement repeated | 61094-5, 5.1.2 |
| Sequential | The exchange does not change the sound pressure significantly, or any change is detected and corrected, for example with a monitor microphone; a monitor, when used, senses the changes at the test position | 61094-5, 5.1.3; 61094-8, 5.2, 6.5 |
| Free-field mounting | On a semi-infinite rod of the microphone's diameter | 61094-8, 6.7 |
| Reported uncertainty | Expanded, with `k = 2`, at each frequency | 61094-5, 7.9; 61094-8, 8.8 |

## A pressure calibration by simultaneous excitation

Annex C removes the gains of the two channels and the asymmetry of the
coupler: with the reference on channel 1 the level reading difference is
`L_C12`, after the interchange it is `L_C21`, and Formula (C.3) gives
`L_ref - L_test = (L_C12 - L_C21) / 2`. Here the channels differ by 0,55 dB,
port A hears up to 0,13 dB more than port B, and each reading is repeated
three times:

```python
import numpy as np
from phonometry import metrology

f = metrology.exact_frequencies(250, 20000, fraction=3)   # 20 exact one-third octaves
x = f / 1000
l_ref = -38.0 + 0.04 * np.log10(x) - 0.25 * (x / 20) ** 2   # the LS2P's certificate, dB re 1 V/Pa
l_true = -38.6 + 0.08 * np.log10(x) + 0.2 * (x / 12) ** 2 - 0.5 * (x / 20) ** 4   # the WS2P: unknown

gain_1, gain_2 = 0.35, -0.20      # the two measuring channels, dB
field_a = 0.03 * np.sqrt(x)       # port A of the coupler hears 0.015 dB to 0.13 dB more
rng = np.random.default_rng(61094)
noise = rng.normal(0.0, 0.004, (2, 3, f.size))   # three repeats of each reading
l_c12 = (l_ref + gain_1) - (l_true + gain_2) + field_a + noise[0]   # reference on channel 1
l_c21 = (l_true + gain_1) - (l_ref + gain_2) + field_a + noise[1]   # interchanged

c = metrology.simultaneous_comparison(f, l_ref, l_c12, l_c21)
print(c.determinations, c.sensitivity_level_db[[2, 8, 19]].round(2))   # 3 [-38.63 -38.58 -38.44]
print(np.abs(c.sensitivity_level_db - l_true).max().round(3))           # 0.003
```

A pressure calibration without the interchange is refused, since 5.1.2
requires it. The "mean of the two ratios" 5.1.2 asks for is taken in
decibels, as Annex C does: the geometric mean, the only one in which the gains
cancel exactly (the arithmetic mean of the two ratios here would sit 0,018 dB
to 0,027 dB high).

IEC 61094-5 6.6 corrects the reference's sensitivity to the conditions of the
test when the two microphones are different models, and IEC 61094-8 7.6 does
it whatever the models. `metrology.environmental_sensitivity_correction`
corrects a sensitivity level for the static pressure, the temperature and the
humidity to first order, from the microphone's own coefficients in the units
IEC 61094-2 Annex D gives them:

```python
env = metrology.environmental_sensitivity_correction(
    f,
    static_pressure_kpa=99.2,        # the laboratory during the test
    temperature_c=21.5,
    relative_humidity_percent=45.0,
    static_pressure_coefficient_db_per_kpa=-0.005,   # the LS2P's own coefficients
    temperature_coefficient_db_per_k=0.002,
)   # from its certificate's 101.325 kPa, 23.0 °C and 50 %
print(env.correction_db[0].round(4))   # 0.0076
```

## The uncertainty budget of Annex D

Table D.1 is a worked budget for a set-up like this one at 2 kHz, in the
coupler of Figure A.1, which is for frequencies up to 10 kHz (A.1; above, the
jig of A.2 reaches 20 kHz). `metrology.IEC61094_5_TABLE_D1` holds each of its
eight rows with its printed standard uncertainty, and the stated value and
divisor of the seven that state one; the repeatability row states no value
and prints 0,025 dB as a standard uncertainty.
`metrology.comparison_uncertainty_budget` combines the components on
`metrology.combine_uncertainty` and multiplies by `k = 2`:

```python
d1 = {
    "reference": 0.025, "capacitance": 0.006, "non_linearity": 0.017,
    "impedance": 0.003, "polarizing_voltage": 0.005, "repeatability": 0.025,
    "drift": 0.017, "rounding": 0.003,
}   # Table D.1, standard uncertainties at 2 kHz
b = metrology.comparison_uncertainty_budget(d1, frequency_hz=2000)
print(round(b.combined_uncertainty_db, 4), round(b.expanded_uncertainty_db, 3))   # 0.0437 0.087
print(round(b.linear_combined_uncertainty_db, 4))                                  # 0.0436
```

D.3 prints 0,040 dB and 0,08 dB, which are not the root-sum-square of its own
eight components (an [erratum](../../ERRATA.md)). The strict calculation in
linear form D.3 mentions, and does not print, gives 0,043 614 dB; the Spanish
UNE-EN 61094-5:2017 leaves six of the eight values of Table D.1 blank and prints
0,004 dB in D.3. With one budget per frequency, the expanded uncertainty goes
to the calibration, which draws it as a band:

```python
budgets = [
    metrology.comparison_uncertainty_budget(
        {**d1, "impedance": 0.003 + 0.09 * (fx / 20000) ** 2}, frequency_hz=fx
    )
    for fx in f
]
u = [bb.expanded_uncertainty_db for bb in budgets]
c = metrology.simultaneous_comparison(
    f, l_ref, l_c12, l_c21, reference_environment=env, expanded_uncertainty_db=u
)
print(np.round(u, 3)[[0, 16, 19]])                  # [0.087 0.101 0.205]
print(c.sensitivity_mv_per_pa[[2, 8, 19]].round(2))  # [11.72 11.78 11.98]
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_budget_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_budget.svg" alt="The standard uncertainty of each component of IEC 61094-5 Table D.1 at 2000 Hz, u_c = 0.0437 dB and U = 0.087 dB, and of a free-field budget with the components of IEC 61094-8 Table 2 at 8000 Hz, u_c = 0.1317 dB and U = 0.263 dB" width="100%"></picture>

## A WS3 microphone in the jig

Table A.1 gives the corrections to add to the sensitivity level of a WS3
microphone calibrated against an LS2aP in the jig of Figure A.4, with an
expanded uncertainty of a tenth of each:

```python
j = metrology.jig_diameter_correction()
print(j.correction_db[[0, 9, 13]])          # [-0.004 -0.235 -1.443]
print(j.standard_uncertainty_db[13].round(4))   # 0.0722
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_jig_correction_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_jig_correction.svg" alt="The corrections of IEC 61094-5 Table A.1 from -0.004 dB at 1 kHz to -1.443 dB at 20 kHz, with a band of a tenth of each" width="88%"></picture>

## A free-field calibration by substitution

By IEC 61094-8 A.2 each microphone is read against the monitor, and the
quotient of the two ratios is the output ratio corrected for any change of
the source: `20 lg R_V = 20 lg(V_test / V_mon,2) - 20 lg(V_ref / V_mon,1)`,
with `V_ref` and `V_mon,1` the output voltages of the reference and the
monitor in the first reading and `V_test` and `V_mon,2` those of the second.
The reference here is an LS2P calibrated in a pressure field, so it takes
the free-field to pressure difference of IEC/TS 61094-7 (illustrative values
below), and the source drifts by 0,25 dB between the readings:

```python
ff = metrology.exact_frequencies(500, 20000, fraction=3)
xf = ff / 1000
c_ff = 0.05 * xf**1.3            # the LS2P's free-field to pressure difference: illustrative
l_ref_p = -38.0 + 0.04 * np.log10(xf) - 0.25 * (xf / 20) ** 2   # its pressure calibration
l_ws2f = -38.3 + 0.1 * np.log10(xf) - 0.3 * (xf / 20) ** 3      # the WS2F: unknown
field_1 = 74.0 + 0.05 * np.sin(xf)   # the free field while the reference is in place
field_2 = field_1 + 0.25             # the source has drifted by the time the WS2F is
monitor = -40.0                      # the monitor microphone near the source, dB re 1 V/Pa


def free_field_budget(fx):
    x20 = fx / 20000
    return metrology.comparison_uncertainty_budget(
        {
            "reference": 0.06 + 0.14 * x20,    # pressure calibration and IEC/TS 61094-7
            "source_stability": 0.01,
            "positioning": 0.02,
            "alignment": 0.01 + 0.04 * x20**2,
            "free_field": 0.03 + 0.12 * x20**2,
            "non_linearity": 0.017,
            "rounding": 0.003,
            "repeatability": 0.02,
        },
        frequency_hz=fx,
        field="free_field",
    )


free = metrology.sequential_comparison(
    ff,
    l_ref_p,
    l_ref_p + c_ff + field_1,     # the reference's output, dB re 1 V
    l_ws2f + field_2,             # the WS2F's output in its place
    reference_monitor_level_db=monitor + field_1,
    test_monitor_level_db=monitor + field_2,
    field="free_field",
    reference_free_field_difference_db=c_ff,
    expanded_uncertainty_db=[free_field_budget(fx).expanded_uncertainty_db for fx in ff],
)
print(bool(np.abs(free.sensitivity_level_db - l_ws2f).max() < 1e-9))   # True
print(free.expanded_uncertainty_db[[0, 12, 16]].round(2))              # [0.16 0.26 0.51]
```

Table 2 of IEC 61094-8 lists the components and prints no values; the ones
above are illustrative. `metrology.IEC61094_8_TABLE_1` holds the typical
expanded uncertainty of each way of calibrating the reference:

```python
row = metrology.IEC61094_8_TABLE_1["primary_pressure"]
print(row.expanded_uncertainty_1khz_db, row.expanded_uncertainty_10khz_db)   # 0.12 0.4
```

## The effective free-field region of a time window

A time window of length `tau` simulates a free field inside a prolate
spheroid with the source and the microphone at its foci, `d` apart, and the
major diameter `A = d + tau c` (Formula (B.1)), at the speed of sound of the
IEC 61094-2 Annex F air:

```python
r = metrology.free_field_region(1.0, 0.005)   # 1 m, a 5 ms window, at 23.0 °C
print(round(r.speed_of_sound, 1), round(r.major_axis_m, 2))     # 345.9 2.73
print(round(r.semi_minor_axis_m, 2), round(r.rod_clearance_m, 2))   # 1.27 0.86
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_region_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/free_field_region.svg" alt="The effective free-field region of a 5 ms window at 1 m, an ellipse 2.73 m long with the source and the microphone at its foci, and the mounting rod running out past its end" width="88%"></picture>

## The diffuse-field comparison of IEC 61183

The diffuse-field method of IEC 61183 clause 5 is a sequential comparison
without a monitor, and the library computes it through the same model:

```python
d = metrology.diffuse_field_sensitivity(
    [1000.0, 2000.0], [94.3, 94.6], [94.0, 94.1],
    reference_random_incidence_level_db=[-26.0, -26.2],
)
s = metrology.sequential_comparison([1000.0, 2000.0], [-26.0, -26.2], [94.0, 94.1], [94.3, 94.6])
print(d.diffuse_field_level_db, s.sensitivity_level_db)   # [-25.7 -25.7] [-25.7 -25.7]
```

## What this guide covers

Implemented: the level model of IEC 61094-5 D.2; the simultaneous excitation
with the interchange of Annex C (Formulas (C.1) to (C.3)), required for a
pressure calibration; the sequential excitation against a monitor microphone;
the average over the determinations; the environmental correction to first
order (this library's reading of 6.6 and 7.6, which print no formula); the
reference's free-field to pressure difference in a free-field calibration;
the WS3 corrections of Table A.1, whose 10 % expanded uncertainty, printed
without a coverage factor, is read with the `k = 2` of 7.9 and D.2; the
budgets of Table D.1 and IEC 61094-8 Table 2 with `k = 2`; Tables A.1, D.1,
1 and 2 as published data; and the effective free-field region of Formula
(B.1). Not implemented: the
measurements themselves and the phase of the sensitivity; the corrections for
the difference of the acoustic impedances (7.4, 7.5) and for non-uniform
pressure beyond Table A.1 (6.5); the time-selective processing of IEC 61094-8
Annex B and the qualification of the free field by ISO 26101; the values of
IEC/TS 61094-7, which are inputs, and the reciprocity calibration of the
reference, which is in
[Microphone calibration by reciprocity](reciprocity-calibration.md); the second special case of Table D.1, a microphone calibrated as a
system with its preamplifier (0,002 dB, and under 0,02 dB above 200 Hz),
which a budget takes through `additional_components`.

## See also

- [Microphone calibration by reciprocity (IEC 61094-2 and IEC 61094-3)](reciprocity-calibration.md):
  the primary calibration of the laboratory standard microphone a comparison
  takes as its reference.
- [Free-field corrections of a sound level meter (IEC 62585)](free-field-corrections.md):
  a meter compared with an LS2P reference in the same way.
- [Random-incidence and diffuse-field response (IEC 61183)](random-incidence.md):
  the diffuse-field comparison that computes through the same model.
- [Measurement uncertainty](gum-uncertainty.md): the GUM law of propagation
  the budgets are combined by.
- [Errata in published sources](../../ERRATA.md): IEC 61094-5 D.3, UNE-EN
  61094-5:2017 Table D.1, IEC 61094-8 8.4 and Formula (B.10).
- API reference: [`metrology.comparison_calibration`](https://jmrplens.github.io/phonometry/reference/api/metrology/comparison-calibration/).

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
step can be checked against the sensitivities that built them, then the
time-selective processing of IEC 61094-8 Annex B, the phase of the
sensitivity, the effect of different acoustic impedances (IEC 61094-5 7.4
and 7.5) with the air between two microphones by the circuit the part refers
to, the correction for microphones of different diameters by the model it
refers to (6.5), and the validation of a jig or a coupler (6.7).

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

### Beyond Table A.1: microphones of different diameters

"The effect of a non-uniform pressure distribution over the surface of the
diaphragm will be significantly greater if the test and reference
microphones are of different diameters. A theoretical model which can be
used to apply corrections and assess the uncertainties in this case is given
in the literature (for example [1])" (6.5). Its reference [1], Barham,
Barrera-Figueroa and Avison, Metrologia 51 (2014) 129, is where Table A.1
comes from. The gap between the diaphragms is a cylinder of the reference's
front-cavity radius `a` and length `L`, closed by the reference and driven,
in a radially symmetrical field, through the annulus round the smaller
microphone. Its pressure is a series of the radial modes of the cavity,
`p(r, z) = sum C_n cosh(mu_n z) J0(k_n r/a)` with `J1(k_n) = 0`, and each
microphone reads it averaged over its diaphragm with its radial sensitivity,
the deflection of a membrane under a uniform pressure,
`J0(j01 (f/f0) r/a)/J0(j01 f/f0) - 1`, `f0` being the diaphragm's resonance
frequency and `b` taking the place of `a` for the test microphone. The correction is the ratio of the two averages,
`-20 lg|R_P|`. `metrology.diameter_sound_field_correction` computes it from
the geometry and the two resonance frequencies, at the speed of sound of the
IEC 61094-2 Annex F air:

```python
ws3 = {
    "reference_radius_m": 4.650e-3,        # an LS2: its front cavity and diaphragm
    "test_diaphragm_radius_m": 2.065e-3,   # a WS3: its diaphragm
    "test_outer_radius_m": 2.975e-3,       # and its outline
    "separation_m": 0.5e-3,                # Figure A.4
    "reference_resonance_frequency_hz": 22000,
    "test_resonance_frequency_hz": 100000,
}   # the inputs of Table 1 of [1]
model = metrology.diameter_sound_field_correction(j.frequencies_hz, **ws3)
print(round(model.speed_of_sound, 1), model.correction_db[[0, 9, 13]].round(3))   # 345.9 [-0.004 -0.233 -1.434]
print(np.abs(model.correction_db - j.correction_db).max().round(4))               # 0.0093
print((model.separation_change_db / np.abs(model.correction_db))[[0, 13]].round(3))   # [0.063 0.054]
```

At the reference air of clause 4 the model is within 0,0093 dB of every row
of Table A.1, inside the 0,144 dB the NOTE gives the largest correction as
its expanded uncertainty; the paper prints no speed of sound, and at
344,8 m/s the model gives every row to the thousandth printed. As printed,
the paper's formulas with its own inputs do not give its own table: the
library reads the radial sensitivity of its Formula (4) less 1 and the
annulus of its Formula (2) from the WS3's overall radius, the two readings
that do (an [erratum](../../ERRATA.md)). A.2 sets the expanded uncertainty of
Table A.1 at 10 % of each correction, "which is approximately the change
observed by doubling the distance between the microphones";
`separation_change_db` is that change by the model, of the order A.2 states
and below it. Table A.1 holds for one pair of microphones at the one
separation of Figure A.4 and at fourteen frequencies; the model holds for any
test microphone that fits inside its reference's front cavity, any
separation, and any frequency below the two resonance frequencies:

```python
f12 = metrology.exact_frequencies(1000, 20000, fraction=12)   # every twelfth of an octave
fine = metrology.diameter_sound_field_correction(f12, **ws3)
print(f12.size, round(f12[50]), fine.correction_db[50].round(3))   # 53 17783 -1.141
```

`fine.correction_db` goes to a calibration through `corrections_db=` as
Table A.1 does. The model assumes a radially symmetrical field, which is why
6.5 and A.2 ask for a coaxial source in the far field or a diffuse field.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_diameter_correction_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_diameter_correction.svg" alt="The correction of a WS3 microphone against an LS2 by the model of IEC 61094-5 6.5, at every twelfth of an octave from 1 kHz to 20 kHz, from -0.004 dB at 1 kHz to -0.233 dB at 8 kHz and -1.427 dB just under 20 kHz, with the fourteen rows of Table A.1 as diamonds on it, and dashed above it the correction at twice the separation, 1 mm, about 6 % smaller" width="88%"></picture>

## A free-field calibration by substitution

By IEC 61094-8 A.2 each microphone is read against the monitor, and the
quotient of the two ratios is the output ratio corrected for any change of
the source: `20 lg R_V = 20 lg(V_test / V_mon,2) - 20 lg(V_ref / V_mon,1)`,
with `V_ref` and `V_mon,1` the output voltages of the reference and the
monitor in the first reading and `V_test` and `V_mon,2` those of the second.
The monitor's two readings go together, as a `metrology.MonitorReadings`.
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
    monitor=metrology.MonitorReadings(
        reference_level_db=monitor + field_1, test_level_db=monitor + field_2
    ),
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

## Time-selective processing (Annex B)

Annex B turns a room that is not anechoic into a free field: an impulse
response separates the direct sound from the reflections in time, a window
keeps the first, and a Fourier transform gives the frequency response of the
direct sound alone (B.1.1). The impulse response can come from a stepped sine
taken to the time domain by Formula (B.3)
(`metrology.stepped_sine_impulse_response`), from a sweep or a maximum length
sequence (`room.impulse_response`, `room.mls_impulse_response`), or from a
direct impulse. `metrology.time_selective_response` weights it with a time
window and evaluates Formula (B.2) at any frequency. The window "normally has
'tapered' edges" (B.1.2) and a rectangular one "is not recommended because it
usually leads to spectral leakage" (B.1.3), so the default is a Tukey window
with an eighth of it tapered at each edge, a proportion the library chose.

Here an LS2P reference and a WS2F stand in turn 1 m from the source, and a
reflection off the rig arrives along a path of 1,48 m. The WS2F hears it off
axis, so it does not cancel in the ratio of the two outputs as the direct
sound does (8.5). Each is measured by a stepped sine from 0 Hz to 100 kHz in
50 Hz steps; the microphones are illustrative:

```python
c0 = metrology.free_field_region(1.0, 0.005).speed_of_sound   # 345.9 m/s at 23.0 °C
f_step = np.arange(0.0, 100000.0 + 1.0, 50.0)   # 0 Hz to 100 kHz in 50 Hz steps


def mic(fx, level_db, f0, d):   # a microphone's sensitivity, V/Pa: illustrative
    return 10 ** (level_db / 20) / (1 - (fx / f0) ** 2 + 1j * d * fx / f0)


direct, rig = 1.0 / c0, 1.48 / c0   # the direct sound over 1 m, the rig's reflection over 1.48 m


def heard(m, off_axis):   # each step: the direct sound and the rig's reflection
    return m * (
        np.exp(-2j * np.pi * f_step * direct)
        + 0.25 * off_axis * np.exp(-2j * np.pi * f_step * rig)
    )


ir_ref = metrology.stepped_sine_impulse_response(f_step, heard(mic(f_step, -38.0, 22000, 1.1), 1.0))
ir_ws2f = metrology.stepped_sine_impulse_response(
    f_step, heard(mic(f_step, -26.4, 18000, 0.9), 1 / (1 + 1j * f_step / 6000))
)   # the WS2F hears the reflection off axis
print(ir_ref.duration_s, round(ir_ref.sample_rate_hz))   # 0.02 200050
```

The impulse response lasts the inverse of the frequency step, 20 ms (B.2.2:
120 Hz is enough in a small anechoic room "because the primary reflections
all occur before 8 ms", about 30 Hz in a large one). B.2.1 says the
increment "will determine the time domain resolution"; it is the length it
sets, as B.2.2 says (an [erratum](../../ERRATA.md)). `ir_ws2f.plot()` draws
the whole record:

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/stepped_sine_impulse_response_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/stepped_sine_impulse_response.svg" alt="The WS2F's impulse response from the stepped sine of 0 Hz to 100 kHz in 50 Hz steps, normalised to its peak, over the whole 20 ms record: the direct sound at 2.89 ms with a short ringing, the rig's reflection at 4.28 ms at about a tenth of the peak, and nothing after them up to 20 ms. The title gives the 50 Hz step and the 20.00 ms length" width="88%"></picture>

The window has to end before the reflection arrives. A point on the boundary of the region of
Formula (B.1) reflects along a path of `A = d + tau c`, so a reflection whose
path is `L` stays outside while `tau <= (L - d) / c`:

```python
tau = metrology.reflection_free_window_s(1.0, 1.48)
window = {"window_start_s": direct - 0.0005, "window_end_s": direct + tau}
ref = metrology.time_selective_response(ir_ref.impulse_response, ir_ref.sample_rate_hz, **window)
ws2f = metrology.time_selective_response(ir_ws2f.impulse_response, ir_ws2f.sample_rate_hz, **window)
print(round(1000 * tau, 2), round(ref.frequency_resolution_hz))   # 1.39 530
```

A window of 1,89 ms tells frequencies apart no closer than 530 Hz, the
low-frequency limit 6.2.3 warns time-selective techniques have. The levels
and phases through the window are the two outputs of a substitution:

```python
fw = metrology.exact_frequencies(1900, 20000, fraction=3)   # 2 kHz to 20 kHz
m_ref = mic(fw, -38.0, 22000, 1.1)   # the reference's free-field sensitivity, from its certificate
tsel = metrology.sequential_comparison(
    fw,
    20 * np.log10(np.abs(m_ref)),
    ref.level_db_at(fw),
    ws2f.level_db_at(fw),
    field="free_field",
    phase=metrology.SequentialComparisonPhase(
        reference_sensitivity_phase_deg=np.degrees(np.angle(m_ref)),
        reference_output_phase_deg=ref.phase_deg_at(fw),
        test_output_phase_deg=ws2f.phase_deg_at(fw),
    ),
)
m_ws2f = mic(fw, -26.4, 18000, 0.9)   # what the page knows the WS2F to be
print(tsel.sensitivity_level_db[[0, 6, 10]].round(2))   # [-26.34 -25.46 -26.6 ]
print(bool(np.abs(tsel.sensitivity_level_db - 20 * np.log10(np.abs(m_ws2f))).max() < 1e-4))   # True
record = 20 * np.log10(np.abs(ws2f.record_response_at(fw) / ref.record_response_at(fw)))
print(np.abs(record - 20 * np.log10(np.abs(m_ws2f / m_ref))).max().round(2))   # 1.91
```

Through the window the WS2F's sensitivity comes back to within 0,0001 dB;
from the whole record, the reflection included, it would be up to 1,91 dB
off.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_selective_response_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_selective_response.svg" alt="Left, the WS2F's impulse response from a stepped-sine measurement, its direct sound at 2.89 ms and the rig's reflection at 4.28 ms, with a Tukey window 1.89 ms long from 2.39 ms that ends as the reflection arrives. Right, its frequency response from 1 kHz to 40 kHz: through the window it is the smooth response of the direct sound, and from the whole record it ripples round it, from 2.45 dB below to 1.89 dB above up to 16 kHz" width="100%"></picture>

**The direct impulse method** (B.6) drives the source with a short
rectangular pulse, whose spectrum is Formula (B.10); its first zero, `1/(2b)`,
"must be approximately an order of magnitude higher than the upper limit of
the frequency range of interest". The formula is that of a pulse lasting
`2b`, although the text calls `b` the duration (an
[erratum](../../ERRATA.md)), and `metrology.rectangular_pulse` takes the
whole duration:

```python
T = metrology.rectangular_pulse_duration_s(20000)   # a first zero ten times 20 kHz
pulse = metrology.rectangular_pulse(T, amplitude_v=10.0)
print(T, pulse.half_duration_s, round(pulse.first_zero_hz))   # 5e-06 2.5e-06 200000
print(pulse.level_db_at([20000.0]).round(2))                  # [-0.14]
```

The responses to several pulses, averaged synchronously
(`signals.time_synchronous_average`; B.6.2 counts on `10 lg n` dB of
signal-to-noise ratio from `n` of them), go to `time_selective_response` with
`excitation=pulse`, which divides the pulse's spectrum out.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rectangular_pulse_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rectangular_pulse.svg" alt="The spectrum of a 5 microsecond rectangular pulse relative to its value at 0 Hz, from 0 to 500 kHz: flat to within 0.14 dB up to the 20 kHz upper limit, falling to its first zero at 200 kHz and a second at 400 kHz" width="88%"></picture>

## The phase of the sensitivity

Both parts carry the phase over with the modulus: IEC 61094-5 5.1.1
calculates "the sensitivity (both modulus and phase) of the test
microphone", and IEC 61094-8 5.1 "both the modulus and phase of the
free-field sensitivity of the microphone under test". D.2 holds for the complex
ratios, so the phase follows the level term by term,
`phi_test = phi_ref + arg R_V - arg R_P`, and the interchange of Annex C
cancels the phase shifts of the two channels and of the coupler as (C.3)
cancels their gains: `phi_ref - phi_test = (Phi_C12 - Phi_C21) / 2`, with
`Phi_C12` the phase of channel 1's reading re channel 2's. Neither part prints
this form; it is (C.3) written for the complex ratio. The phase inputs go
together, as a `metrology.SimultaneousComparisonPhase` here and a
`metrology.SequentialComparisonPhase` in a sequential calibration, whose
monitor's phases go with its levels in its `metrology.MonitorReadings`. The
pressure calibration above, with the phase of each reading:

```python
phi_ref = np.degrees(np.angle(1 / (1 - (f / 22000) ** 2 + 1.1j * f / 22000)))   # the LS2P's certificate: illustrative
phi_true = np.degrees(np.angle(1 / (1 - (f / 18000) ** 2 + 0.9j * f / 18000)))   # the WS2P: unknown
shift_1, shift_2 = 1.5 * x, -0.8 * x   # the two channels' phase shifts, degrees
late_a = 0.4 * x                       # port A hears the field later, degrees
jitter = np.random.default_rng(5).normal(0.0, 0.02, (2, 3, f.size))
p12 = (phi_ref + shift_1) - (phi_true + shift_2) + late_a + jitter[0]   # reference on channel 1
p21 = (phi_true + shift_1) - (phi_ref + shift_2) + late_a + jitter[1]   # interchanged
cp = metrology.simultaneous_comparison(
    f, l_ref, l_c12, l_c21,
    phase=metrology.SimultaneousComparisonPhase(
        reference_sensitivity_phase_deg=phi_ref,
        channel_phase_difference_deg=p12,
        interchanged_channel_phase_difference_deg=p21,
    ),
)
print(cp.sensitivity_phase_deg[[2, 8, 16, 19]].round(1))   # [  -1.1   -4.6  -35.9 -102.9]
print(np.abs(cp.sensitivity_phase_deg - phi_true).max().round(3))   # 0.016
```

The difference of the two readings is twice the phase difference of the
microphones, so it is taken into one turn before it is halved: the result is
unique while they differ by less than 90°. In a free field the phases are
those at the acoustic centres (IEC 61094-8 5.1), which 7.3 positions "at the
measurement points"; in a sequential substitution each goes in turn to the
same point, where `arg R_P` is 0, and a delay common to the two readings,
like the travel time from the source in the time-selective example, cancels
in their quotient.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_phase_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_phase.svg" alt="The phase of the sensitivity against frequency. Left, the WS2P calibrated in a coupler through the interchange, from 250 Hz to 20 kHz: near the LS2P reference's phase up to 4 kHz, then falling faster, to -35.9 degrees at 10 kHz and -102.9 degrees at 20 kHz against the reference's -32.2 and -79.9. Right, the WS2F calibrated through the time window from 2 kHz to 20 kHz, the same shape" width="100%"></picture>

## Microphones of different acoustic impedance

"Differences in the acoustic impedance between the test and reference
microphones can cause the sound pressure at the test and reference
microphones to differ" (7.4), most where a pressure and a free-field
microphone meet above 10 kHz (7.5). Neither clause prints a model: 7.4 sends
the reader to the literature and 7.5 asks for the error to be estimated and
added to the budget. `metrology.impedance_pressure_ratio` writes the effect
for two circuits with each microphone's equivalent volume,
`V_e = kappa_r p_s,r / (j omega Z_a)` (IEC 61094-1 6.2.2, `kappa_r` = 1,40):
`R_P = (V_x + V_e,ref) / (V_x + V_e,test)`. In a closed coupler small against
the wavelength a sequential substitution changes the pressure by the ratio of
the two admittance sums of IEC 61094-2 Formula (3), `V_x` being the rest of
the load (the gas, the source, a monitor); for a simultaneous excitation
Table D.1 puts "the acoustical impedance of the microphone [...] in series
with that of the air in the space between the two microphones", so that the
two "see slightly different pressures [...] (see 7.4 and [2])": each diaphragm takes the pressure of a common source behind the same
series impedance, and `V_x` is the equivalent volume of that impedance,
which the circuit of [2] gives (below).
`metrology.ReciprocityMicrophone`, the microphone of
[the reciprocity calibration](reciprocity-calibration.md), holds the lumped
parameters of IEC 61094-2 E.4, the low-frequency volume, the resonance
frequency and the loss factor, and its `complex_equivalent_volume_m3` gives
`V_e` from them. Its ratio to the low-frequency volume holds no `kappa_r`, so
with the 10 mm³ that Table 3 of IEC 61094-1 gives an LS2P, `V_e` is the
volume of 6.2.2 with its 1,40. E.4 finds the representation "of sufficient
accuracy" up to "about 1,3 times the resonance frequency of the microphone",
20,8 kHz for the WS2F below. The front cavity the microphone also holds
enters the transfer impedance of a coupler, not `V_e`:

```python
fi = metrology.exact_frequencies(1000, 20000, fraction=3)
front = {"front_cavity_volume_m3": 34e-9, "front_cavity_depth_m": 0.5e-3,
         "front_cavity_diameter_m": 9.3e-3}   # an LS2aP's (Table C.1 of IEC 61094-2)
lumped_ls2p = metrology.ReciprocityMicrophone(
    equivalent_volume_m3=10e-9, resonance_frequency_hz=22000, loss_factor=1.1, **front
)   # an LS2P: 10 mm³ (IEC 61094-1 Table 3); the resonance and loss: illustrative
lumped_ws2f = metrology.ReciprocityMicrophone(
    equivalent_volume_m3=30e-9, resonance_frequency_hz=16000, loss_factor=0.5, **front
)   # a more compliant WS2F: illustrative
rp = metrology.impedance_pressure_ratio(
    fi,
    reference_equivalent_volume_m3=lumped_ls2p.complex_equivalent_volume_m3(fi),
    test_equivalent_volume_m3=lumped_ws2f.complex_equivalent_volume_m3(fi),
    coupling_equivalent_volume_m3=600e-9,   # the coupler's gas, source and monitor: illustrative
)
print(rp.level_difference_db[[0, 10, 13]].round(3))      # [-0.281 -0.421  0.37 ]
print(rp.standard_uncertainty_db[[0, 10, 13]].round(3))  # [0.163 0.243 0.213]
```

A monitor that senses "changes in the sound pressure at the test/reference
microphone position" (5.1.3) takes this ratio out. Without one,
`rp.level_difference_db` and `rp.phase_difference_deg` go to the comparison
as `pressure_level_difference_db` and as the `pressure_phase_difference_deg`
of its phase inputs. Where
the ratio is estimated rather than corrected for, `rp.standard_uncertainty_db`
is the `"impedance"` component of the budget: the level difference read as
the semi-range of a rectangular distribution, as Table D.1 reads its
0,005 dB at 2 kHz. The same row warns about exactly this pairing: "When
microphones have significantly differing impedances (for example WS2F
microphone compared against LS2P at frequencies above 10 kHz), the
measurement uncertainty can be considerably larger and should be established
experimentally." Above 10 kHz the value here is the model's estimate, not
that experiment; where the ratio crosses 0 dB, near 16 kHz, it gives almost
nothing at all.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_impedance_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_impedance.svg" alt="The pressure ratio of a WS2F in the place of an LS2P in a closed coupler, from 1 kHz to 20 kHz. Left, its level: -0.28 dB at 1 kHz, falling to -0.44 dB at 12.5 kHz, crossing 0 dB at 16 kHz past the WS2F's resonance and reaching +0.37 dB at 20 kHz, with its standard uncertainty dashed from 0.16 dB to 0.25 dB, dropping to almost nothing at 16 kHz where the level crosses 0 dB. Right, its phase, about 0.7 degrees at 8 kHz and peaking at 4.86 degrees at 16 kHz" width="100%"></picture>

### The air between the two microphones

The "Microphone impedance" row of Table D.1 refers the simultaneous
excitation to its reference [2], Jarvis, NPL Report CIRA(EXT) 010 (1996).
Its Appendix B models a symmetric coupler as a ladder from a source in its
middle: on each side a mass `Z_L`, the compliance `Z_c` of that side's half
of the volume, a second `Z_L` and the microphone, with
`Z_c = kappa p0 / (j omega V/2)`, `Z_L = j omega rho (L/4) / (3 pi r^2)` and
`V = pi r^2 L` for a tube of length `L` and radius `r`. Seen from each
diaphragm, the middle of the ladder is a pressure common to both behind one
impedance, `Z_x = Z_L + Z_L Z_c/(Z_L + Z_c)`, so each diaphragm takes
`p Z_a/(Z_a + Z_x)`, the divider above, and the ratio of the two is the one
Appendix B prints. `metrology.air_gap_series_impedance_pa_s_m3` gives `Z_x`
for a coupler of known length and radius. Appendix B's example is an LS2P
against a high sensitivity WS2P in a tube 2 mm long and 12,7 mm across, each
microphone a resistance, a mass and a compliance in series:

```python
fj = np.arange(100.0, 20000.0 + 1.0, 100.0)   # Appendix B's frequencies
w = 2 * np.pi * fj


def z_mic(r, c, m):   # Z_m = r + j w m + 1/(j w c), Appendix B
    return r + 1j * w * m + 1 / (1j * w * c)


def v_e(z):           # the equivalent volume of IEC 61094-1 6.2.2
    return 1.40 * 101325 / (1j * w * z)


z_x = metrology.air_gap_series_impedance_pa_s_m3(fj, gap_length_m=2e-3, gap_radius_m=6.35e-3)
gap = metrology.impedance_pressure_ratio(
    fj,
    reference_equivalent_volume_m3=v_e(z_mic(330e6, 48e-15, 1210)),   # the LS2P of Appendix B
    test_equivalent_volume_m3=v_e(z_mic(7e7, 2.6e-13, 820)),           # its high sensitivity WS2P
    coupling_impedance_pa_s_m3=z_x,
)
print(gap.level_difference_db[[69, 199]].round(4))   # [ 0.0064 -0.025 ]
print(gap.phase_difference_deg[124].round(3))         # -0.158
```

The WS2P hears 0,0064 dB more than the LS2P at 7 kHz and 0,025 dB less at
20 kHz, and lags it by up to 0,158° at 12,5 kHz. Appendix B draws the same
curves for `P1/P2`, the LS2P re the WS2P, so the other way up, with its
1,21 kg/m³ for the density of the air; with that density the conformance
report reproduces them. In the published scan its impedance of the LS2P
shows no imaginary unit on the mass term, where blank space stands; the
second microphone's has it, and the graph needs it (an
[erratum](../../ERRATA.md)).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_air_gap_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_air_gap.svg" alt="The pressure ratio of the high sensitivity WS2P re the LS2P of Jarvis (1996) Appendix B in a coupler 2 mm long and 12.7 mm across, from 100 Hz to 20 kHz. Left, its level: nothing up to 1 kHz, rising to +0.0064 dB at 7 kHz, crossing 0 dB near 10 kHz and falling to -0.025 dB at 20 kHz, with its standard uncertainty dashed. Right, its phase: nothing up to 2 kHz, falling to -0.158 degrees at 12.5 kHz and back to -0.09 degrees at 20 kHz" width="100%"></picture>

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

## Validating a jig or a coupler

"Calibrations performed in any particular jig or coupler shall be validated
by comparison with calibrations performed in other jigs and couplers and
alternative sound sources. A separate validation is necessary for each
different type of microphone. If the test microphone is a laboratory
standard microphone, then the jig or coupler can be validated by comparing
a comparison calibration with a reciprocity calibration. For some
microphones, it can be necessary to use more than one jig and/or coupler to
cover a full frequency range with low uncertainty" (6.7).
`metrology.verify_jig_or_coupler` sets a calibration made in the jig or
coupler beside another calibration of the same microphone, a comparison made
elsewhere or, for a laboratory standard microphone, the
`ReciprocityCalibration` of [the reciprocity
calibration](reciprocity-calibration.md) with the index of that microphone,
and compares them at the frequencies they share. The clause prints no
criterion. The library reads "validated" as the two agreeing within the
expanded uncertainty of their difference, `|L_cal - L_val| <= U_Δ`, which
for two independent calibrations is the root-sum-square
`U_Δ = sqrt(U_cal^2 + U_val^2)`; two calibrations that share a component
are correlated, and the part they share comes out of it (below).

Here the jig of A.2 is validated against the coupler of A.1 for the WS2P of
the first example, the coupler used up to the 10 kHz it is for. Near
6,3 kHz the jig has a standing wave close to the microphones, the anomaly
Barham et al. found in a test box at that frequency, and the field moves
between the reading and the interchange, so (C.3) no longer cancels it:

```python
fv = f[6:]   # the jig of A.2, 1 kHz to 20 kHz
mode = 0.5 * np.exp(-(((fv / 1000 - 6.3) / 0.6) ** 2))   # the field moves near 6.3 kHz
jitter = np.random.default_rng(42).normal(0.0, 0.01, (2, 3, fv.size))
j12 = (l_ref[6:] + gain_1) - (l_true[6:] + gain_2) + field_a[6:] + mode + jitter[0]
j21 = (l_true[6:] + gain_1) - (l_ref[6:] + gain_2) + field_a[6:] + jitter[1]
jig = metrology.simultaneous_comparison(fv, l_ref[6:], j12, j21, expanded_uncertainty_db=u[6:])
coupler = metrology.simultaneous_comparison(
    f[:17], l_ref[:17], l_c12[:, :17], l_c21[:, :17], expanded_uncertainty_db=u[:17]
)   # the coupler of A.1, up to 10 kHz
check = metrology.verify_jig_or_coupler(jig, coupler)
print(check.passes, check.failing_frequencies_hz.round())    # False [6310.]
print(check.unvalidated_frequencies_hz.round())              # [12589. 15849. 19953.]
print(check.difference_db[8].round(3), check.expanded_uncertainty_db[8].round(3))   # -0.247 0.128
```

The jig agrees with the coupler at every frequency they share but 6,3 kHz,
where they differ by 0,247 dB against 0,128 dB, and above 10 kHz it is not
validated at all, the coupler not reaching there: a second set-up has to
validate it there, as 6.7 allows. `check.normalised_difference` is the
difference in units of its expanded uncertainty, -1,93 at 6,3 kHz.

### Calibrations that share a reference

Both calibrations here take the same LS2P as their reference, so the first
row of Table D.1, the calibration of that reference (0,025 dB, the
"±0,05 dB with a coverage factor of k = 2" of its certificate), is in both
budgets. Whatever error that calibration carries moves the two sensitivity
levels together and cancels in their difference, while the root-sum-square
counts it twice. In the terms of the GUM, two levels that each depend on a
common quantity with a sensitivity of 1 have its variance as their
covariance (JCGM 100:2008 F.1.2.3, Formula (F.2), whose sensitivity
coefficients are then both 1), and the law of propagation for correlated inputs
(5.2.2, Formula (13)) gives for the difference

`u_Δ^2 = u_cal^2 + u_val^2 - 2 u_sh^2`

with `u_sh` the standard uncertainty of what the two share.
`shared_standard_uncertainty_db` takes it, one value or one per frequency of
the calibration, and the band becomes
`U_Δ = sqrt(U_cal^2 + U_val^2 - 2 (k u_sh)^2)` with the `k = 2` of 7.9:

```python
shared = metrology.verify_jig_or_coupler(jig, coupler, shared_standard_uncertainty_db=0.025)
print(shared.passes, shared.failing_frequencies_hz.round())                                # False [6310.]
print(shared.expanded_uncertainty_db[8].round(3), shared.normalised_difference[8].round(2))   # 0.106 -2.32
print(shared.correlation_coefficient[8].round(2))                                           # 0.31
```

The band narrows from 0,124 dB to 0,101 dB at the low frequencies and from
0,128 dB to 0,106 dB at 6,3 kHz, where the two calibrations are correlated
with a coefficient of 0,31, the reference's variance over the product of
their standard uncertainties (Formula (14)). The verdict does not change
here: the jig still fails at 6,3 kHz alone, now by 2,32 times the
uncertainty of the difference. A pair that agrees within the root-sum-square
can fail once the shared part is out of it. Which components the two share
is the laboratory's to say: the calibration of a reference both use, its
drift since then (the row "Drift in reference microphone sensitivity since
last calibration", 0,017 dB) for two calibrations made close together, a
measuring chain they both go through. Only a component that enters both
levels with the same sign and size belongs here. A reciprocity calibration
made in the same set of three microphones as the reference's is not such a
case: in IEC 61094-2:2009 Formula (7) (folio 12) the electrical transfer
impedances of the two pairs that go through the third microphone are in the
numerator of one microphone's sensitivity and in the denominator of the
other's, so those measurements enter the two levels with opposite signs.
Their covariance is negative and widens the uncertainty of the difference
beyond the root-sum-square, which `shared_standard_uncertainty_db` cannot
express; only the factors common to both levels with the same sign may be
given there. A shared part larger than either calibration's standard
uncertainty is refused, since nothing can be shared beyond the whole of it.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_jig_validation_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/comparison_jig_validation.svg" alt="The difference between the WS2P calibrated in the jig and in the coupler at the eleven frequencies they share, 1 kHz to 10 kHz, inside a shaded band of plus or minus the expanded uncertainty of the difference with the reference they share taken out, 0.101 dB widening to 0.124 dB at 10 kHz, and dotted around it the band of two independent calibrations, 0.124 dB widening to 0.143 dB: within 0.008 dB of zero everywhere but 6.3 kHz, where it falls to -0.247 dB, outside both bands and marked with a cross; three dashed vertical lines at 12.6 kHz, 15.8 kHz and 20 kHz mark the frequencies of the jig the coupler does not cover" width="88%"></picture>

The clause prints neither a criterion nor an example, so the conformance
report checks the verdict against its own definition. Jarvis and Watkins
(1997), NPL Report CIRA(EXT) 022, who compared jig calibrations of working
standard microphones at NPL with reciprocity calibrations of the same
microphones, print no numeric criterion either: their Figures 6 and 7
(folio 4) plot the differences, and the text judges them against "the
typical repeatability" of the measurements (folio 2), one standard
deviation drawn as a band in Figure 7 and never printed as a number, with
no number a criterion could be checked against. The residual differences
"of less than 0.1 dB" of folio 5 report a result rather than set a test, and
the report says nothing about what the two calibrations share. The shared
part has printed numbers, in the GUM: two items
calibrated against the same standard, of relative standard uncertainty
$10^{-4}$, are correlated with coefficients of about 0,5, 0,990 and 1,000
for comparisons of $100 \times 10^{-6}$, $10 \times 10^{-6}$ and
$1 \times 10^{-6}$ (F.1.2.3, Example 2). The conformance
report checks `correlation_coefficient` against them, and the difference of
two calibrations with the budget of Table D.1 against the seven rows left
once the reference's cancels.

## What this guide covers

Implemented: the level model of IEC 61094-5 D.2; the simultaneous excitation
with the interchange of Annex C (Formulas (C.1) to (C.3)), required for a
pressure calibration; the sequential excitation against a monitor microphone;
the average over the determinations; the phase of the sensitivity (61094-5
5.1.1, 61094-8 5.1), the phase form of (C.3) and of the monitor ratios being
this library's reading of the complex ratio, as neither part prints it; the
environmental correction to first order (this library's reading of 6.6 and
7.6, which print no formula); the reference's free-field to pressure
difference in a free-field calibration; the WS3 corrections of Table A.1,
whose 10 % expanded uncertainty, printed without a coverage factor, is read
with the `k = 2` of 7.9 and D.2; the pressure ratio of microphones of
different acoustic impedance (7.4, 7.5) in a closed coupler by the printed
IEC 61094-2 Formula (3) and, for a simultaneous excitation, in series with
the air between them, by the circuit of Appendix B of Jarvis (1996), the
part's reference [2], whose series impedance the library gives for a coupler
of known length and radius (read with the imaginary unit its first
microphone's mass term has lost in the published scan), with the lumped equivalent
volume of IEC 61094-2 E.4 and IEC 61094-1 6.2.2, and its standard
uncertainty as Table D.1 reads a semi-range (which, above 10 kHz for a WS2F
against an LS2P, the row asks to be established experimentally); the
correction for a test microphone smaller than its reference (6.5) by the
model of Barham et al. (2014), the part's reference [1], for any geometry
and separation, read with the radial sensitivity of its Formula (4) less 1
and the annulus of its Formula (2) from the overall radius, the readings
that give its Table 2, which is Table A.1, with the change on doubling the
separation that A.2 names, its uncertainty left to the caller; the
validation of a jig or a coupler against another calibration of the same
microphone (6.7), whose criterion, agreement within the expanded uncertainty
of the difference, the root-sum-square of the two less what they share by
the GUM law of propagation for correlated inputs (JCGM 100:2008 5.2.2 and
F.1.2.3), is this library's reading, the clause printing none and Jarvis
and Watkins (1997) no numeric one, only a component that enters both levels
with the same sign and size counting as shared; the budgets of Table D.1 and IEC 61094-8 Table 2 with `k = 2`;
Tables A.1, D.1, 1 and 2 as published data; the effective free-field region
of Formula (B.1) and the longest window it allows for a reflection; the time
window of B.1.3 with the tapered edges of B.1.2, Formula (B.2) through it, the stepped sine of B.2 by Formula
(B.3) and the rectangular pulse of B.6 (Formula (B.10)). Not implemented: the
measurements themselves, and the choice of the set-ups a jig or a coupler
is validated against, for each type of microphone (6.7); the sweeps, the maximum length sequences and the random noise of B.3 to B.5,
which are `room.impulse_response`, `room.mls_impulse_response` and
`electroacoustics.transfer_function` elsewhere in the library, and the
synchronous averaging of B.6.2, which is `signals.time_synchronous_average`;
the qualification of the free field by ISO 26101, on [its own
page](../../devices/emission/free-field-qualification.md); the values of
IEC/TS 61094-7, which are inputs, and the reciprocity calibration of the
reference, which is in
[Microphone calibration by reciprocity](reciprocity-calibration.md); the second special case of Table D.1, a microphone calibrated as a
system with its preamplifier (0,002 dB, and under 0,02 dB above 200 Hz),
which a budget takes through `additional_components`; a covariance that
widens the uncertainty of the difference, as between two microphones of the
same reciprocity set through the pairs with the third (IEC 61094-2:2009
Formula (7)), which `verify_jig_or_coupler` does not take.

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
  61094-5:2017 Table D.1, IEC 61094-8 8.4, B.2.1 and Formula (B.10),
  Barham et al. (2014) Formulas (1), (2) and (4), and Jarvis (1996)
  Appendix B.
- API reference: [`metrology.comparison_calibration`](https://jmrplens.github.io/phonometry/reference/api/metrology/comparison-calibration/).

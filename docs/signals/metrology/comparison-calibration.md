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
sensitivity and the effect of different acoustic impedances (IEC 61094-5 7.4
and 7.5).

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
with that of the air in the space between the two microphones" and prints no
circuit; the library reads it as a divider, each diaphragm behind the same
series impedance from the common field, and `V_x` is the equivalent volume
of that impedance. That form is the library's reading, not the part's.
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
the air between them, a divider that is this library's reading of the one
sentence of Table D.1 that describes it, with the lumped equivalent volume
of IEC 61094-2 E.4 and IEC 61094-1 6.2.2, and its standard uncertainty as
Table D.1 reads a semi-range (which, above 10 kHz for a WS2F against an
LS2P, the row asks to be established experimentally); the budgets of Table D.1 and IEC 61094-8 Table 2 with `k = 2`;
Tables A.1, D.1, 1 and 2 as published data; the effective free-field region
of Formula (B.1) and the longest window it allows for a reflection; the time
window of B.1.3 with the tapered edges of B.1.2, Formula (B.2) through it, the stepped sine of B.2 by Formula
(B.3) and the rectangular pulse of B.6 (Formula (B.10)). Not implemented: the
measurements themselves; the value of the series impedance of the air between
two microphones, which the parts leave to the literature and to experiment,
and the corrections for non-uniform pressure beyond Table A.1 (6.5); the
sweeps, the maximum length sequences and the random noise of B.3 to B.5,
which are `room.impulse_response`, `room.mls_impulse_response` and
`electroacoustics.transfer_function` elsewhere in the library, and the
synchronous averaging of B.6.2, which is `signals.time_synchronous_average`;
the qualification of the free field by ISO 26101, on [its own
page](../../devices/emission/free-field-qualification.md); the values of
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
  61094-5:2017 Table D.1, IEC 61094-8 8.4, B.2.1 and Formula (B.10).
- API reference: [`metrology.comparison_calibration`](https://jmrplens.github.io/phonometry/reference/api/metrology/comparison-calibration/).

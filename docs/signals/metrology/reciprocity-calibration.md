← [Documentation index](../../README.md)

# Microphone calibration by reciprocity (IEC 61094-2 and IEC 61094-3)

A laboratory standard microphone is calibrated without a reference
microphone. Two microphones are coupled acoustically, one drives and the other
receives, and the electrical transfer impedance `Z_e,12 = U_2/i_1` that is
measured is the product of their sensitivities times the acoustic transfer
impedance of whatever couples them: `M_1 M_2 = Z_e,12 / Z_a,12`. In a coupler
(IEC 61094-2:2009) `Z_a,12` is the acoustic impedance of a small enclosed
volume of gas; in a free field (IEC 61094-3:2016, read with its corrigendum
COR1:2016) it is that of a spherical wave between the two acoustic centres.
Three microphones measured in pairs give three products, and each sensitivity
follows from them alone. The modules are `metrology.reciprocity_coupler`,
`metrology.reciprocity_free_field` and `metrology.reciprocity_calibration`.
The readings on this page are synthetic, built from sensitivities the page
knows, so every step can be checked against them.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_pressure_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_pressure.svg" alt="The pressure sensitivity level of three LS1P microphones calibrated by reciprocity in a plane-wave coupler, 25 Hz to 10 kHz, and the heat-conduction and capillary corrections to the transfer impedance of one pair" width="100%"></picture>

## How the measurement goes

Three microphones, two of them reciprocal, or two and an auxiliary sound
source, one of them reciprocal (5.1.1). Each pair is measured in turn: one is
driven by a current, measured across a calibrated impedance in series with
it, and the other's open-circuit voltage is read by the insert voltage
technique (5.3). In a coupler the two face each other across a cavity of
known shape; in a free field, on their principal axes in an anechoic room.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_reciprocity_setup_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_reciprocity_setup.svg" alt="The readings of a reciprocity calibration: in a coupler, the transmitter driven by a current i_1 and the receiver read as U_2, the pairs of the triad in turn, Formula (2) and Formula (7) of IEC 61094-2; in a free field, the same pair face to face with the distance d_m12 between the diaphragms and d_12 between the acoustic centres, Formulas (7) and (8) of IEC 61094-3" width="100%"></picture>

| Requirement | Value | Clause |
| :--- | :--- | :--- |
| Reference conditions | 23,0 °C, 101,325 kPa, 50 % relative humidity | 61094-2 and 61094-3, 4 |
| Polarizing voltage | 200,0 V recommended, and the one used reported | 61094-2, 6.2; 61094-3, 6.2 |
| Plane-wave coupler | Distance between the diaphragms 0,5 to 0,75 times the diameter | 61094-2, C.2 |
| Large-volume coupler | Length to diameter about 0,3, with a wave-motion correction | 61094-2, C.3 |
| Free-field distance | Greater than ten nominal diameters | 61094-3, 7.3 |
| Free-field mounting | On a cylinder of the microphone's diameter at least twenty diameters long | 61094-3, 6.4 |
| Reported uncertainty | Expanded, `k = 2` (61094-2) or for a 95 % coverage probability (61094-3) | 61094-2, 7.5; 61094-3, 7.8 |

## The microphones, the coupler and the transfer impedance

Each microphone enters through its lumped acoustic impedance (Annex E: the
equivalent volume, the resonance frequency and the loss factor) and its front
cavity (E.2, E.3). Figure C.2 draws each microphone of a large-volume
coupler with its face a distance F back from the cavity, through a bore of
the front-cavity diameter B: `LargeVolumeCoupler` takes that length as
`port_length_m`, and the two bores of the LS1P coupler of Table C.2 add 2,4 %
to its volume, a tenth of a decibel on each sensitivity. `check_coupler`
holds the coupler to what its formulas need: `omega rho a^2 > 100 eta` for
Formulas (A.3) and (A.4), the domain `0,125 < R < 8`, `X > 5` of the
approximation (A.2), and the Annex F conditions. The ratio C.2 recommends is
reported, and so is a frequency below 20 Hz with the approximation, where A.2
asks for the full solution or a larger uncertainty component.

```python
import numpy as np
from phonometry import fluids, metrology

mics = tuple(
    metrology.ReciprocityMicrophone(
        equivalent_volume_m3=v,
        resonance_frequency_hz=f0,
        loss_factor=d,
        front_cavity_volume_m3=0.534e-6,   # measured, E.3
        front_cavity_depth_m=1.95e-3,      # D of Table C.1
        front_cavity_diameter_m=18.6e-3,   # B of Table C.1
    )
    for v, f0, d in ((148e-9, 8200.0, 1.05), (141e-9, 8350.0, 1.00), (152e-9, 8050.0, 1.10))
)
coupler = metrology.PlaneWaveCoupler(
    length_m=7.5e-3,
    diameter_m=18.6e-3,
    capillary=metrology.CapillaryTube(length_m=0.05, radius_m=0.2e-3, count=2),
)
conditions = {"temperature_c": 22.4, "static_pressure_pa": 100200.0, "relative_humidity_percent": 46.0}
f = metrology.exact_frequencies(20, 10000, fraction=3)
check = metrology.check_coupler(f, coupler, mics, **conditions)
print(check.passes, round(check.length_to_diameter_ratio, 3), check.ratio_recommended)   # True 0.613 True

large = metrology.LargeVolumeCoupler(length_m=12.55e-3, diameter_m=42.88e-3, port_length_m=0.80e-3)   # E, C, F of Table C.2
print(round(large.cavity_volume_m3 * 1e9), round(large.closed_volume_m3(mics[:2]) * 1e9))   # 18124 19626 (mm³)
```

A plane-wave coupler is the transmission line of Formula (4), with the losses
of Formulas (A.3) to (A.5) and the excess volume of each front cavity
(7.3.3.1); a large-volume coupler is the compliance of Formula (3), its volume
multiplied by `Delta_H = kappa / (1 + (kappa - 1) E_V)` of Formula (A.1).
Both are divided by `Delta_C = 1 + n Z''_a,12 / Z_a,C` of Formula (6) for the
capillary tubes of Annex B.

```python
pairs = ((0, 1), (1, 2), (2, 0))
za = [metrology.coupler_transfer_impedance(f, coupler, mics[i], mics[j], **conditions) for i, j in pairs]
print(za[0].heat_conduction_correction_db[[1, 16, 25]].round(3))   # [-0.287 -0.051  0.004]
print(za[0].capillary_correction_db[[1, 16, 25]].round(3))         # [-0.213  0.011 -0.   ]
```

`temperature_transfer_function` sums Gerber's full solution, which A.2
requires below 20 Hz unless the uncertainty component is increased instead,
and which gives every entry of Table A.1 to its stated 0,000 01; Formula (A.2)
is the approximation. The capillary impedance gives Tables B.1 and B.2, whose
"0,1667 mm" radius is 1/6 mm, to within 0,002 GPa·s/m³: the residue reaches
0,0011 in the real part and 0,0018 in the imaginary near the resonances of
the tubes, and 0,0005 and 0,0007 from 20 Hz to 250 Hz, a little more than the
printed half-unit (the 4,288 below against the printed 4,287).

```python
print(metrology.temperature_transfer_function(1.0, 100.0).round(5))                          # (0.97179+0.02758j)
print(metrology.temperature_transfer_function(1.0, 100.0, method="approximation").round(5))  # (0.97179+0.02758j)
air = fluids.air(temperature_c=23.0, static_pressure_pa=101325.0, relative_humidity_percent=50.0)
tube = metrology.capillary_tube_impedance([20.0, 1000.0], length_m=0.05, radius_m=1 / 6000, gas=air)
print((tube.impedance_pa_s_m3 / 1e9).round(3))   # [3.015+0.097j 8.331+4.288j]
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_coupler_physics_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_coupler_physics.svg" alt="The heat-conduction correction of the LS1P large-volume coupler of Table C.2 with its two bores, from 0.61 dB at 2.5 Hz to 0.01 dB at 10 kHz, and the real and imaginary parts of the input impedance of an open capillary tube 50 mm long and 1/6 mm in radius at the reference conditions, 20 Hz to 20 kHz, with six resonances from 1.33 kHz to 17.7 kHz" width="100%"></picture>

Table C.3 is the wave-motion correction of the air-filled large-volume
coupler for LS1P microphones:

```python
print(metrology.large_volume_wave_motion_correction([1000.0, 2000.0]).correction_db)   # [-0.002 -0.06 ]
```

## The pressure sensitivities

Formula (2) gives the product of each pair and Formula (7) the three complex
sensitivities. A product does not change when every sensitivity changes sign
together, so the sign of the square root is a convention: the library takes
the branch continuous in frequency with a non-negative real part at the
lowest frequency. With two microphones, the ratio measured against an
auxiliary source replaces the third pair, Formula (8).

```python
true = [m0 * m.complex_equivalent_volume_m3(f) / m.equivalent_volume_m3 for m0, m in zip((0.0496, 0.0473, 0.0512), mics)]
ze = [true[i] * true[j] * z.transfer_impedance_pa_s_m3 for (i, j), z in zip(pairs, za)]   # Formula (2)

c = metrology.pressure_reciprocity(f, ze, za)
print(c.sensitivity_level_db[:, 16].round(2))    # [-26.03 -26.44 -25.76]
print(c.sensitivity_mv_per_pa[:, 16].round(2))   # [49.93 47.64 51.51]
print(np.abs(c.sensitivity_v_per_pa - true).max() < 1e-15)   # True
```

```python
pair = metrology.pressure_reciprocity_pair(f, ze[0], za[0], true[0] / true[1])
print(pair.sensitivity_level_db[:, 16].round(2))   # [-26.03 -26.44]
```

## A free-field calibration

Formula (7) of IEC 61094-3 carries the distance between the acoustic centres,
the density of the air, the phase of the spherical wave and its attenuation
over the distance between the diaphragms; the attenuation is the five steps of
Annex B and the wave number takes the speed of sound with the dispersion of
IEC 61094-2 F.3. Formulas (8) and (9) as printed omit the factor `-j` of
Formula (7), which turns the phase by 45°; the library follows Formula (7).

```python
ff = metrology.exact_frequencies(1000, 40000, fraction=3)
ffc = {"temperature_c": 23.1, "static_pressure_pa": 101100.0, "relative_humidity_percent": 52.0}
att = metrology.reciprocity_air_attenuation(ff, **ffc)
print(att.attenuation_db_per_m[[0, 10, 13, 15]].round(4))   # [0.0053 0.1348 0.4713 0.9877]
```

```python
ratio = ff / 23000.0
true_ff = [m0 / (1.0 - ratio**2 + 1.3j * ratio) for m0 in (0.0128, 0.0124, 0.0131)]
centre = 4.5e-3 / (1.0 + (ff / 30000.0) ** 2)
ze_ff = [
    metrology.free_field_transfer_impedance(
        ff, true_ff[i], true_ff[j], diaphragm_distance_m=0.25, acoustic_centres_m=(centre, centre), **ffc
    )
    for i, j in pairs
]   # Formula (D.1)
cf = metrology.free_field_reciprocity(
    ff, ze_ff, diaphragm_distances_m=(0.25, 0.25, 0.25), acoustic_centres_m=(centre, centre, centre), **ffc
)
print(cf.sensitivity_level_db[:, 10].round(2))   # [-37.76 -38.03 -37.55]
print(np.abs(cf.sensitivity_v_per_pa - true_ff).max() < 1e-15)   # True
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_free_field_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_free_field.svg" alt="The free-field sensitivity level of three LS2aP microphones calibrated by reciprocity, 1 kHz to 40 kHz, and the attenuation of sound in air by Annex B" width="100%"></picture>

The acoustic centre comes from the inverse-distance law (6.5), and
`check_free_field_arrangement` holds the arrangement to the ten diameters 7.3
recommends between the microphones, the twenty 6.4 recommends along the
supporting cylinder and the accuracy domain of B.2:

```python
r = np.array([0.15, 0.20, 0.25, 0.30, 0.40, 0.50])
alpha = metrology.reciprocity_air_attenuation([10000.0], **ffc).attenuation_np_per_m[0]
p = 0.85 * np.exp(-alpha * r) / (r - 2.4e-3)     # your readings at one frequency
print(round(1000 * metrology.acoustic_centre(r, p, attenuation_np_per_m=alpha).position_m, 2))   # 2.4
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_acoustic_centre_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_acoustic_centre.svg" alt="The inverse of the measured sound pressure corrected for the attenuation against the distance from the reference point, with the least-squares line crossing zero at the acoustic centre, 2.4 mm" width="100%"></picture>

```python
arrangement = metrology.check_free_field_arrangement(
    ff, diaphragm_distances_m=(0.25, 0.25, 0.25), microphone_diameter_m=13.2e-3, support_length_m=0.3, **ffc
)
print(arrangement.passes, arrangement.annex_a_range)   # True True
```

## The uncertainty budgets

Both parts list their components in Table 1 and find those of the acoustic
transfer impedance by changing each parameter by its uncertainty one at a
time; `coupler_parameter_uncertainty` and `free_field_parameter_uncertainty`
do that, from the standard uncertainties gathered in a
`CouplerInputUncertainties` or a `FreeFieldInputUncertainties` (one left at
zero adds no component), and `reciprocity_uncertainty_budget` combines
everything with `k = 2`.

```python
pu = metrology.coupler_parameter_uncertainty(
    f, coupler, mics,
    metrology.CouplerInputUncertainties(
        u_coupler_length_m=3e-6, u_coupler_diameter_m=3e-6, u_capillary_radius_m=2e-6,
        u_static_pressure_pa=10.0, u_temperature_k=0.05, u_relative_humidity_percent=2.0,
        u_front_cavity_depth_m=3e-6, u_front_cavity_volume_m3=1e-9, u_equivalent_volume_m3=1e-9,
        u_resonance_frequency_hz=50.0, u_loss_factor=0.03,
    ),
    **conditions,
)
print(pu.components_db["capillary_tube_dimensions"][[1, 16]].round(4))   # [0.0086 0.0002]

x = f / 10000
b = metrology.reciprocity_uncertainty_budget(
    f,
    {
        **pu.components_db,
        "series_impedance": 0.002, "voltage_ratio": 0.003, "cross_talk": 0.001 + 0.004 * x**2,
        "polarizing_voltage": 0.0025, "radial_wave_motion": 0.03 * x**2,
        "heat_conduction_theory": 0.002, "repeatability": 0.004, "rounding": 0.0006,
    },
)
print(b.expanded_uncertainty_db[[1, 16, 25]].round(3))   # [0.023 0.015 0.041]

pf = metrology.free_field_parameter_uncertainty(
    ff,
    metrology.FreeFieldInputUncertainties(
        u_distance_m=0.1e-3, u_acoustic_centre_m=0.5e-3, u_static_pressure_pa=20.0, u_temperature_k=0.1,
        u_relative_humidity_percent=2.0, u_air_attenuation_ratio=0.1 / np.sqrt(3.0),
    ),
    diaphragm_distances_m=(0.25, 0.25, 0.25), acoustic_centres_m=(centre, centre, centre), **ffc,
)
xf = ff / 40000
bf = metrology.reciprocity_uncertainty_budget(
    ff,
    {
        **pf.components_db,
        "series_impedance": 0.002, "voltage_ratio": 0.003, "cross_talk": 0.002 + 0.01 * xf,
        "noise": 0.005, "reflections": 0.01 + 0.02 * xf, "polarizing_voltage": 0.0025, "repeatability": 0.01,
    },
    field="free_field",
)
print(bf.expanded_uncertainty_db[[0, 10, 15]].round(3))   # [0.049 0.054 0.072]
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_budgets_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/reciprocity_budgets.svg" alt="The uncertainty budgets of microphone 1 of the pressure triad, 25 Hz to 10 kHz, and of the free-field triad, 1 kHz to 40 kHz, each component and the expanded uncertainty" width="100%"></picture>

## What this guide covers

Implemented: Formulas (2) to (8) of IEC 61094-2 with Annexes A (Gerber's full
solution and the approximation (A.2), Formulas (A.3) to (A.5)), B, C (Tables
C.1, C.2 and C.3, with the frequency scaling of C.3 for hydrogen) and E
(Formula (E.1)); Formulas (6) to (9) and (D.1) of IEC 61094-3 with COR1, the
attenuation of Annex B, the acoustic centre of 6.5 and the arrangement of 6.4
and 7.3; Table 1 of both parts and their one-at-a-time recalculation. Table
A.1 of IEC 61094-2 is reproduced to its stated 0,000 01 and Table B.1 of IEC
61094-3 to its last figure; Tables B.1 and B.2 of IEC 61094-2 to within
0,002 GPa·s/m³. Read from the text: dimension F of Table C.2 is the length of
the bore Figure C.2 draws between each microphone face and the cavity.
Not implemented: the measurements themselves; the radial wave-motion
corrections of plane-wave couplers; the environmental corrections, which are
the first-order correction of the comparison guide; the determination of the
microphone parameters of E.3 and E.4; Formula (4) of IEC 61094-3, which needs
the radiation impedance and the scattering factor; the time-selective
processing of Annex D; the acoustic centres of Annex A, printed only as a
figure.

## See also

- [Microphone calibration by comparison (IEC 61094-5 and IEC 61094-8)](comparison-calibration.md):
  carrying a reciprocity-calibrated reference over to a working standard
  microphone.
- [Humid air](../../fluids/humid-air.md): the IEC 61094-2 Annex F air.
- [Measurement uncertainty](gum-uncertainty.md): the GUM the budgets are
  combined by.
- [Errata in published sources](../../ERRATA.md): IEC 61094-2 Tables B.1 and
  B.2, IEC 61094-3 Formulas (8) and (9), and B.2 Step 1.
- API reference: [`metrology.reciprocity_calibration`](https://jmrplens.github.io/phonometry/reference/api/metrology/reciprocity-calibration/),
  [`metrology.reciprocity_coupler`](https://jmrplens.github.io/phonometry/reference/api/metrology/reciprocity-coupler/),
  [`metrology.reciprocity_free_field`](https://jmrplens.github.io/phonometry/reference/api/metrology/reciprocity-free-field/).

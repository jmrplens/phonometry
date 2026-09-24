← [Documentation index](../../README.md)

# Random-incidence and diffuse-field response (IEC 61183)

A sound level meter is calibrated for sound arriving from one direction, its
reference direction, and most of the sound it measures arrives from all of
them. Its microphone and its case are not transparent at high frequency, so a
meter that reads a plane wave from the front correctly reads a field from
every direction low. IEC 61183:1994 gives the two ways of finding by how much:
the **free-field method** rotates the instrument in an anechoic room and
weights the reading for each direction by the share of the sphere it stands
for, and the **diffuse-field method** compares the instrument with a reference
instrument in a reverberation room. This page runs both on a synthetic meter:
a microphone whose pattern has, at each frequency, the directivity Table B.1
prints for a type LS2aP/LS2F laboratory standard microphone, on a case that
narrows it in the plane the case sits in.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/random_incidence_directivity_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/random_incidence_directivity.svg" alt="The synthetic meter at 8 kHz: its polar response in the X-Y and X-Z planes relative to the reference direction, with 10 lg gamma = 2.66 dB, and the weight of each 10 degree reading, from 0.10 % at the poles to 2.18 % at 90 degrees" width="88%"></picture>

## The directivity factor

The directivity factor of Formulas (2) and (3) is the ratio of what the meter
reads for a plane wave from its reference direction to what it reads, on
average over the sphere, for the same wave from every direction:
`gamma = 4 pi / integral of 10^(-0,1 [L_rd - L(phi, alpha)]) |sin phi| d alpha d phi`.
An omnidirectional meter has `gamma = 1`. The random-incidence sensitivity
level is the free-field sensitivity level for the reference direction less the
directivity index, `G_RI = G_F - 10 lg gamma` with `G_F = L_rd - L_o`
(Formula (1)); `G_F` depends on the individual meter and `gamma` only on its
geometry, so one measurement of `gamma` serves every meter of a model (4.2).

### How the measurement goes

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_random_incidence_setup_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_random_incidence_setup.svg" alt="The two calibrations of IEC 61183: in an anechoic room the meter is turned on a turntable in front of a fixed source, its microphone on the axis of rotation, reading L_o, L_rd, L(phi, h) and L(phi, v); in a reverberation room the reference meter and the meter under test are moved in turn along the same circular path, reading L_D,ref and L_D" width="92%"></picture>

| Requirement | Value | Clause |
| :--- | :--- | :--- |
| Anechoic room | Meets ISO 3745; pure tones or random noise, bands no wider than one-third octave, filters of IEC 61260 class 0 or 1 | 4.10 |
| Source | Far enough that the level varies by less than ±1 dB within 0,3 m of the microphone | A.2.2 |
| Signal | At least 20 dB above the background, and held constant during each rotation | A.2.3 |
| Turntable | The acoustical centre of the microphone on the axis of rotation, the reference direction and the source in the plane of rotation | A.2.1, A.4.2 |
| Rotations | 360° in the X-Y plane, then the meter turned 90° about its own axis and 360° again, the X-Z plane | A.4.5, A.4.6 |
| Angular step | Small enough that no element of the sphere exceeds 3 %; 10° leaves 2,2 % | A.1.6, A.1.7 |
| Pure tones | `G_F` and `gamma` may need the rms average of at least eight tones per one-third-octave band, spaced evenly on a logarithmic axis | 4.11 |
| Reverberation room | Meets ISO 3741; broadband or filtered random noise, bands no wider than one-third octave | 5.6 |
| Integration time | Long enough that repeated results scatter by less than 0,05 dB: 2 min from 500 Hz, 8 min from 250 Hz, 15 min from 125 Hz, longer below | 5.6, B.1.4 |
| Microphone path | Both microphones moved in turn along the same circular path, not parallel to any wall, of radius the larger of 1 m and three times the largest dimension of the meter; two uncorrelated omnidirectional sources of about equal power help the diffusivity | B.1.3, B.1.4 |
| Reference meter | A directivity factor as near unity as possible; a type LS2aP/LS2F or LS2bP microphone is recommended | B.1.1, B.1.2 |

## Readings in two planes, and what each is worth

Annex A rotates the meter through 360° in the X-Y plane and again in the X-Z
plane, in equal steps. The elements of the sphere are rings cut into quarters
by the planes, so each reading is weighted by the factor of Formulas (A.1) and
(A.2), `K(phi) = (1/8)[cos(phi - dphi/2) - cos(phi + dphi/2)]` and
`K(0) = K(180°) = (1/4)[1 - cos(dphi/2)]`:

```python
from phonometry import metrology

k = metrology.adjustment_factors(10.0)   # 36 factors, 0° to 350°
print(k[[0, 1, 9]].round(5))             # [0.00095 0.00378 0.02179]
print(round(2 * k.sum(), 12))            # 1.0
print(round(100 * metrology.largest_element_fraction(10.0), 2))  # 2.18
```

All ten rows of Table A.1 come out to the five decimals it prints. A.1.6 asks
for the largest element to be no more than 3 % of the sphere; at 10° steps it
is the one at 90°, 2,18 %, the "approximately 2,2 %" of A.1.7, and a step of
15° (3,26 %) warns with a `SphereDivisionWarning`. `planes=4` gives the four
planes at 45° of NOTE 2 of A.6, which halve every factor.

The 72 factors sum to one only when the readings at 0° and 180° enter both
sums of Formula (A.3). The paragraph under it says those readings "have only
to be taken into account once": they have to be measured once. Counted in one
sum only, the factors add up to 0,998 097 and `10 lg gamma` comes out high by
`-10 lg(1 - gamma K(0) [10^(-0,1 [L_rd - L(0°)]) + 10^(-0,1 [L_rd - L(180°)])])`:
0,008 dB for a meter that reads the same in every direction, about 0,02 dB at
`10 lg gamma = 7 dB`. The library counts them in both sums, and the
omnidirectional meter has `gamma = 1` exactly.

```python
import numpy as np

def pattern_db(phi_deg, n, floor=0.02):
    """L(phi) - L_rd of a meter whose squared pressure is (1 - b)[(1 + cos phi)/2]^n + b."""
    lobe = ((1 + np.cos(np.radians(phi_deg))) / 2) ** n
    return 10 * np.log10((1 - floor) * lobe + floor)

phi = np.arange(0, 360, 10)
levels = 94.0 + np.vstack((pattern_db(phi, 0.785),    # X-Y plane (h), 8 kHz
                           pattern_db(phi, 0.98)))    # X-Z plane (v), the case narrows it
d = metrology.directivity_factor(levels)
print(round(d.gamma, 3), round(d.directivity_index_db, 2))   # 1.845 2.66
d.plot()                  # the polar response, one curve per plane
d.plot(view="weights")    # K(phi) of each reading
```

## One plane, or 38 equal elements

A rotationally symmetric meter needs one rotation (Formula (A.4)), and the
note to A.1.8 offers 38 directions of equal-area elements, 2,6 % of the sphere
each, every reading weighing the same (Formula (A.5)):

```python
a = metrology.axisymmetric_directivity_factor(levels[0])
print(round(a.directivity_index_db, 2))   # 2.45

horizontal, vertical = metrology.equal_area_incidence_angles()
print(horizontal[:6].round(1))   # [ 0.  32.6 50.8 65.1 77.8 90. ]
e = metrology.equal_area_directivity_factor(
    94.0 + pattern_db(horizontal, 0.785), 94.0 + pattern_db(vertical, 0.98)
)
print(round(e.directivity_index_db, 2))   # 2.66
```

The X-Y plane alone has the 2,45 dB Table B.1 prints for the microphone at
8 kHz; the case adds the other 0,21 dB. Each equal-area direction halves its
element's area in polar angle, which reproduces the list the note prints
except 77,9° and 282,1°, where the construction gives 77,85° and 282,15°: all
the other pairs of the printed list sum to 180,0° about the grazing direction,
and 77,9° + 102,2° is 180,1°. The two are in the [errata register](../../ERRATA.md).

## The random-incidence sensitivity level, band by band

The synthetic meter at every preferred frequency Table B.1 prints, its X-Y
plane given the `10 lg gamma` of the microphone at that band, and its
free-field sensitivity level rolling off above 10 kHz:

```python
bands = sorted(metrology.IEC61183_TABLE_B1)   # the 30 preferred frequencies, 25 Hz to 20 kHz

def meter(frequency_hz):
    """The synthetic meter at one band: the X-Y plane has the 10 lg gamma Table B.1
    prints for the microphone, and the case narrows the X-Z plane."""
    target = metrology.IEC61183_TABLE_B1[frequency_hz].directivity_index_db
    n = 0.98 / (10 ** (-target / 10) - 0.02) - 1   # the exponent with that index
    return metrology.directivity_factor(
        94.0 + np.vstack((pattern_db(phi, n), pattern_db(phi, 1.25 * n))))

index = [meter(f).directivity_index_db for f in bands]
g_f = -10 * np.log10(1 + (np.array(bands) / 25000) ** 4)   # L_rd - L_o at each band
r = metrology.random_incidence_sensitivity(bands, g_f, index)
shown = np.isin(r.frequencies_hz, [1000, 4000, 8000, 16000])
print(r.correction_db[shown].round(2))              # [-0.06 -0.95 -2.66 -5.62]
print(r.random_incidence_level_db[shown].round(2))  # [-0.06 -0.95 -2.71 -6.29]
r.plot()
r.plot(view="correction")
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/random_incidence_correction_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/random_incidence_correction.svg" alt="G_F of the synthetic meter from 25 Hz to 20 kHz, flat to 8 kHz and rolling off to -1.5 dB at 20 kHz, and G_RI on it up to 800 Hz and then falling to about -2.7 dB at 8 kHz and -8.5 dB at 20 kHz; and the correction between them, -7 dB at 20 kHz" width="88%"></picture>

The correction is what a meter calibrated in a free field reads low in a
random-incidence field: negligible up to about 1 kHz and several decibels by
10 kHz. It is why a meter is specified for one field or the other:
IEC 61672-1:2013 applies its frequency-weighting limits to the free-field or
to the random-incidence response, as applicable (5.5.4), and has the
random-incidence response determined by the free-field method of IEC 61183
(5.5.5). One meter cannot be flat for both.

## The diffuse-field method

The meter under test and a reference meter are placed in turn at the same
positions in a reverberation room; the difference of what they indicate,
`dG_D = L_D - L_D,ref` (Formula (8)), is added to the diffuse-field
sensitivity level of the reference: `G_RI,ref` for a reference calibrated by
clause 4 (Formula (9)), `G_F,ref - 10 lg gamma_ref` for a free-field
calibrated one (Formula (10)), `G_P,ref + Delta_DP` for a pressure calibrated
one (Formula (11)). Annex B recommends a type LS2aP/LS2F or LS2bP microphone
as the reference, Table B.1 prints `10 lg gamma` and `Delta_DP` of the first,
and Formulas (10) and (11) take their
correction from it unless told otherwise:

In an 80 dB diffuse field the meter indicates the field plus its
random-incidence level (1.2), and a reference LS2aP whose pressure sensitivity
level is 0 dB the field plus its `Delta_DP`:

```python
print(metrology.IEC61183_TABLE_B1[8000.0])
# ReferenceMicrophoneRow(directivity_index_db=2.45, diffuse_pressure_difference_db=1.2)

delta_dp = np.array([metrology.IEC61183_TABLE_B1[f].diffuse_pressure_difference_db
                     for f in bands])
dd = metrology.diffuse_field_sensitivity(
    bands,
    80.0 + r.random_incidence_level_db,  # L_D, the meter under test
    80.0 + delta_dp,                     # L_D,ref, a pressure-calibrated LS2aP
    reference_pressure_level_db=0.0,     # G_P,ref; Delta_DP from Table B.1
)
print(dd.reference_correction_db[shown])            # [0.   0.25 1.2  3.05]
print(dd.diffuse_field_level_db[shown].round(2))    # [-0.06 -0.95 -2.71 -6.29]
dd.plot()
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diffuse_field_sensitivity_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diffuse_field_sensitivity.svg" alt="Formula (11) on the synthetic meter from 25 Hz to 20 kHz: Delta_DP of Table B.1 rising to 3.05 dB at 16 kHz, the level difference of Formula (8) falling to about -10.7 dB at 20 kHz, and their sum G_D retracing the random-incidence level" width="88%"></picture>

The two methods meet: the diffuse-field sensitivity level may be used
interchangeably with the random-incidence one (1.2), and the comparison in a
room returns the level the anechoic measurement gave.

## What this guide covers

Implemented: the calculations of both methods of IEC 61183:1994, the
adjustment factors of Formulas (6), (7), (A.1) and (A.2) for any step and any
number of planes, with the halving of NOTE 2 of A.6; the 3 % criterion of
A.1.6 as a warning; the directivity factor from two or more planes, from one
plane under rotational symmetry and from 38 equal-area elements (Formulas
(A.3) to (A.5)); the random-incidence sensitivity level of Formulas (1) and
(A.6); the diffuse-field sensitivity level by the three routes of Formulas (8)
to (11); and Table B.1. Not implemented: the measurements themselves (the
ISO 3745 anechoic and ISO 3741 reverberation rooms, the source, the turntable,
the signal-to-noise ratio of A.2.3 and the integration times of B.1.4), the
averaging of at least eight tones per band (4.11). The corrections of
IEC 62585 that bring a measurement made with a sound calibrator, a comparison
coupler or an electrostatic actuator to the meter's free-field response are
on [their own page](free-field-corrections.md); its corrections for the case,
the microphone and the windscreen (clauses 9 to 11) are not implemented.

## See also

- [Free-field corrections](free-field-corrections.md): IEC 62585, the
  corrections that bring a meter on a calibrator, a coupler or an actuator to
  its free-field response, for a meter with a free-field microphone.
- [Calibration and dBFS](calibration.md): the calibrator tone that sets the
  pressure sensitivity every level of a meter starts from.
- [Compliance and verification](compliance-verification.md): what the
  IEC 61672-1 class of a meter asserts, and which of its tests the library
  runs.
- [Microphone characterisation](../../devices/electroacoustics/microphones.md):
  the IEC 60268-4 directivity index of a microphone on its own.
- [Errata in published sources](../../ERRATA.md): the two equal-area angles.
- API reference: [`metrology.random_incidence`](https://jmrplens.github.io/phonometry/reference/api/metrology/random-incidence/).

← [Documentation index](../../README.md)

# Hearing Protectors (ISO 4869-1, -2 and -6)

A hearing protector is not measured on a coupler. ISO 4869-1 seats it on
sixteen people and records the threshold shift each of them gets, so what
comes back from the laboratory is a **distribution**: one attenuation per
subject per octave band, with a spread that is often a third of the mean.
ISO 4869-2 is the standard that turns that distribution into a number someone
can act on, and the first thing it does is refuse to use the mean.

## Where the distribution comes from (ISO 4869-1)

Each of sixteen subjects finds a threshold for one-third-octave bands of pink
noise at the octave frequencies from 125 Hz to 8 kHz (63 Hz optional), with open
ears and with the protector in place, and the attenuation is the difference
(4.6.2):

$$
A_{j,f} = L_{\mathrm{occluded},j,f} - L_{\mathrm{open},j,f}
$$

Annex A models the attenuation as the measured value plus three zero-mean
inputs (method, equipment, environment); within one laboratory the combined
standard uncertainty is the standard deviation of the mean, $u = s/\sqrt{N}$,
and $U_{95} = 2u$.

```python
import numpy as np
from phonometry import hearing

# ISO 4869-1 Table A.3: one earmuff on sixteen subjects, 125 Hz to 8 kHz.
table_a3 = np.array([
    [9.6, 13.5, 27.5, 32.4, 35.2, 29.1, 28.5],  [14.1, 20.2, 25.8, 32.0, 28.9, 35.3, 35.7],
    [21.8, 27.8, 28.3, 46.6, 37.4, 40.1, 38.7], [18.5, 22.2, 36.5, 44.8, 39.1, 30.6, 33.5],
    [15.6, 21.9, 31.8, 42.5, 38.9, 38.3, 37.1], [18.7, 28.6, 31.3, 39.0, 35.6, 35.3, 29.4],
    [23.0, 26.5, 34.0, 41.3, 40.8, 38.7, 35.9], [17.3, 21.7, 25.0, 30.7, 38.6, 37.9, 40.8],
    [19.4, 19.6, 28.0, 36.6, 40.7, 34.9, 39.4], [11.6, 20.4, 22.6, 38.0, 39.2, 33.9, 30.3],
    [20.5, 21.8, 29.2, 40.7, 36.2, 35.7, 38.4], [18.3, 19.6, 26.2, 34.6, 32.7, 34.9, 26.6],
    [15.1, 17.5, 30.1, 39.0, 39.4, 38.2, 39.5], [21.7, 20.8, 28.3, 39.5, 38.1, 40.0, 38.4],
    [15.9, 17.8, 26.0, 40.6, 38.0, 40.2, 37.2], [11.8, 18.4, 29.6, 37.2, 40.8, 36.0, 29.9],
])
reat = hearing.real_ear_attenuation(table_a3)
print(np.round(reat.mean_db, 1))                  # [17.1 21.1 28.8 38.5 37.5 36.2 35. ]
print(np.round(reat.expanded_uncertainty_db, 1))  # [2.  1.9 1.7 2.2 1.6 1.6 2.3]

# Annex B, Table B.1: a second test of the same earmuff, printed as means and U95.
test_2_mean = [16.8, 21.0, 28.3, 38.2, 35.5, 34.6, 38.9]
test_2_u95 = [1.6, 1.2, 1.4, 1.5, 1.5, 1.7, 2.5]
difference = hearing.assess_attenuation_difference(
    reat, test_2_mean, second_expanded_uncertainty_db=test_2_u95
)
print(np.round(difference.criterion_db, 1))  # [2.5 2.3 2.2 2.7 2.2 2.3 3.4]
print(difference.significant_frequencies)    # [8000.]
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_protector_reat_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_protector_reat.svg" alt="Left: the sound attenuation of one earmuff on sixteen subjects at the seven test signals from 125 Hz to 8 kHz, one faint line per subject, with the mean drawn over them and the expanded uncertainty of the mean as error bars, attenuation increasing downwards. Right: the difference between the means of two tests of the same earmuff as one bar per test signal, with the root sum of squares of the two expanded uncertainties marked over each bar; only the 8 kHz bar clears its mark and is hatched" width="92%"></picture>

Two means differ significantly at the 5 % level when
$|m_1 - m_2| > \sqrt{U_{95,1}^2 + U_{95,2}^2}$ (B.1.2), which for two equal
uncertainties is $\sqrt{2}\,U_{95}$. Tables A.2 and B.2 give typical budgets
(`hearing.REAT_WITHIN_LABORATORY_UNCERTAINTY`,
`hearing.REAT_BETWEEN_LABORATORY_UNCERTAINTY`), and B.1.1 evaluates the minimum
difference on the rounded 2,3 dB its table prints, writing that input out:
"$\sqrt{2}$ × 2,3 dB = 3,3 dB". From the unrounded 2.27 dB it is 3.21 dB. The
sound field of the test room (4.2.2, with Table 1 for the rotated directional
microphone) is judged by `hearing.check_reat_sound_field`, whose verdict passes
only when the rotation of b) was measured as well as the positions of a).

## The distribution first (Clause 5)

All three methods take a mean less a multiple of its own spread, and differ in
what they take it over. The octave-band method takes it over the attenuations
of each band, and the result is the assumed protection value:

$$
APV_{fx} = m_f - \alpha\, s_f
$$

$\alpha$ is the inverse standard normal cumulative distribution at the
protection performance $x$ (Table 1), so $APV_{f84}$ with $\alpha = 1$ is the
attenuation 84 % of wearers reach or beat, and $APV_{f98}$ with $\alpha = 2$ is
what all but one in fifty reach.

The HML and SNR methods never form that value. They rate each subject first,
against the eight reference noises of Table 2 or the pink noise of Table 3, and
take the same reduction over those ratings (Formulae (3) to (5) and (19)). What
the three share is the choice of $x$ and its $\alpha$.

```python
import numpy as np
from phonometry import hearing

# ISO 4869-1 attenuation: 16 subjects, eight octave bands from 63 Hz to 8 kHz.
attenuation = np.array([
    [4, 8, 13, 18, 20, 30, 35, 30],   [6, 12, 16, 21, 29, 35, 47, 35],
    [10, 16, 17, 23, 25, 32, 48, 37], [3, 7, 12, 18, 20, 25, 33, 30],
    [8, 10, 16, 16, 25, 27, 43, 32],  [4, 7, 10, 15, 19, 32, 35, 31],
    [5, 5, 9, 16, 20, 25, 30, 28],    [15, 15, 21, 26, 25, 38, 46, 38],
    [5, 6, 10, 13, 19, 22, 29, 28],   [9, 9, 10, 19, 20, 27, 37, 31],
    [9, 16, 18, 24, 25, 35, 44, 39],  [5, 6, 11, 12, 17, 20, 28, 28],
    [7, 10, 17, 22, 25, 35, 41, 44],  [6, 8, 16, 18, 19, 19, 30, 33],
    [10, 12, 17, 25, 28, 33, 45, 40], [12, 13, 17, 27, 29, 38, 49, 41],
], dtype=float)

apv = hearing.assumed_protection_value(attenuation)          # x = 84 % by default
print(np.round(apv.apv, 1))    # [ 4.1  6.4 10.7 14.9 18.8 23.4 31.3 28.9]
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_protector_methods_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_protector_methods.svg" alt="Left: the mean sound attenuation of a hearing protector across the eight octave bands from 63 Hz to 8 kHz, with its standard deviation shaded either side and the assumed protection value for 84 % of wearers drawn a full standard deviation below the mean. Right: the predicted noise level reduction as a function of the difference between the C-weighted and A-weighted levels of the noise, drawn as two straight segments through the H, M and L anchors, with the eight reference noises scattered at their own differences and the three methods' answers for one noise boxed" width="92%"></picture>

*Left, the protector: the assumed protection value sits a full standard
deviation below the mean, and the gap is widest where the spread is, at 4 kHz.
Right, the method: the HML line and the eight reference noises it was fitted
on, with the three methods' answers for the same noise.*

## Three methods, in decreasing order of what they need

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_hearing_protector_chain_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_hearing_protector_chain.svg" alt="Calculation chain: the ISO 4869-1 attenuation grid of sixteen subjects, one protection performance for all three methods, and the octave-band, HML and SNR columns, each combining what the protector is reduced to with what it needs from the noise and ending at 81 dB, 82 dB and 82 dB" width="88%"></picture>

*One protector model on sixteen subjects, reduced three ways and met with one
noise. Only the octave-band method goes through the assumed protection value;
HML and SNR rate each subject first and take the spread out over those ratings,
and the three land within a decibel of each other.*

**The octave-band method (Clause 6)** is the most faithful and the only one
that sees the shape of the noise: subtract the assumed protection value band by
band from the A-weighted spectrum and sum what is left (Formula (2)).

**The HML method (Clause 7)** collapses the protector to three numbers, the
predicted noise level reduction it gives for reference noises whose
$(L_{p,C} - L_{p,A})$ is $-2$, $+2$ and $+10$ dB, fitted across the eight
reference spectra of Table 2. Applying them needs only the C- and A-weighted
levels of the real noise, through two straight segments that meet at $+2$ dB.

**The SNR method (Clause 8)** collapses it to one number against a pink noise
and subtracts it from the C-weighted level. Clauses 7.3 and 8.3 both allow the
unweighted level in place of the C-weighted one, which reads high for noise
with a lot of very low frequency content.

```python
noise = [75.0, 84.0, 86.0, 88.0, 97.0, 99.0, 97.0, 96.0]   # LpA = 104, LpC = 103 dB
octave = hearing.octave_band_protected_level(noise, apv)
hml = hearing.hml_rating(attenuation)
snr = hearing.snr_rating(attenuation)

print(octave.reported_level)                                          # 81
print(hml.reported)                                                   # (24, 18, 13)
print(hearing.hml_protected_level(104.0, 103.0, hml).reported_level)  # 82
print(snr.reported)                                                   # 21
print(hearing.snr_protected_level(snr, l_p_c=103.0).reported_level)   # 82
```

The three answer the same question and rarely agree exactly: 81 dB, 82 dB and
82 dB for one protector in one noise. The NOTE that closes the Introduction
puts differences of 3 dB or less between comparable protectors below the
resolution of the exercise. The ordering is not a ranking: the octave-band
method uses more information and is the one to prefer when the spectrum is
available, while HML and SNR exist precisely for when it is not.

The values that enter the HML and SNR applications are the **rounded** ones:
Clauses 7.2 and 8.2 round the ratings to the nearest integer, which is what a
protector is published with. The octave-band method starts at 63 Hz when both the
noise and the protector have data there and at 125 Hz when either does not
(Clause 6); the HML and SNR computations start at 125 Hz always.

One caution about the reference spectra: Annex C reprints Table 2 as its
Table C.1 and the reprint disagrees with the original in two cells. Table 2 is
the one that reproduces the annex's own worked results, and it is the one this
library carries; the discrepancy is registered in [ERRATA](../../ERRATA.md).

## Active noise reduction earmuffs (ISO 4869-6)

An active noise reduction earmuff adds a cancellation circuit to a passive
shell, and a threshold test cannot see it. ISO 4869-6 measures the two halves
on the same sixteen subjects: the ISO 4869-1 attenuation with the circuit off,
in octave bands, and the active insertion loss, the level at each ear with the
circuit off minus the level with it on, measured with a microphone in the ear
canal in one-third-octave bands. Clause 5.5 interpolates the passive side into
one-third octaves (linearly in hertz, as ISO's calculation workbook does it),
keeps the ear with the lower insertion loss in each band, adds the two, folds
each octave back with Formula (1) and rates the sixteen results with ISO 4869-2
at 84 %.

```python
# ISO 4869-6 Table A.3: the lower-ear active insertion loss, 63 Hz to 8 kHz.
table_a3_anr = np.array([
    [18.4, 23.9, 21.6, 5.2, -4.5, -0.2, -1.3, -1.0], [19.4, 23.0, 21.7, 5.7, -6.4, -0.4, 0.8, -1.9],
    [19.7, 23.1, 20.8, 3.6, -4.2, -2.9, 0.2, -0.6], [19.8, 23.1, 18.7, 2.2, -4.9, -0.5, -0.2, 0.2],
    [20.5, 24.5, 20.2, 3.1, -4.4, -2.9, -1.4, 0.3], [18.8, 24.4, 20.8, 3.9, -4.3, -2.6, -0.4, -0.2],
    [21.7, 24.4, 22.2, 4.7, -5.2, -5.1, -1.5, -0.3], [20.5, 22.7, 24.3, 8.8, -8.8, -3.1, -4.8, -0.7],
    [22.9, 23.2, 20.7, 5.4, -6.5, -2.8, -0.5, -1.0], [21.9, 22.9, 23.1, 8.8, -8.4, -4.9, -2.6, -0.7],
    [23.7, 24.6, 20.8, 3.4, -6.4, -0.1, -0.3, -0.6], [22.0, 23.9, 20.3, 3.0, -4.2, -0.8, -1.0, 0.3],
    [23.2, 24.3, 20.9, 4.6, -5.6, -0.1, -0.5, -1.0], [21.5, 23.5, 23.3, 5.9, -5.2, -3.1, -3.6, -1.6],
    [24.3, 24.2, 22.5, 4.2, -6.3, -2.5, -0.9, -0.5], [23.8, 24.9, 20.7, 3.8, -4.8, -0.5, -0.3, 0.2],
])
insertion = hearing.active_insertion_loss(table_a3_anr)
print(np.round(insertion.mean_db, 1))                  # [21.4 23.8 21.4  4.8 -5.6 -2.  -1.1 -0.6]
print(np.round(insertion.expanded_uncertainty_db, 1))  # [0.9 0.4 0.7 0.9 0.7 0.8 0.7 0.3]
```

Table A.3 prints its $u$ and $U_{95}$ rows from the rounded row above each, so
six of its eight $U_{95}$ cells are a tenth above the value Annex A defines;
see [ERRATA](../../ERRATA.md). On ISO's calculation example the circuit raises
$L$ from 12 dB to 19 dB and lowers $H$ from 24 dB to 21 dB, because it adds
sound from 1 kHz up (`hearing.anr_total_attenuation`), and
`hearing.assess_anr_linearity` finds the highest external level at which every
ear still follows the 5 dB steps of 5.4.4 within ±1 dB.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_protector_anr_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_protector_anr.svg" alt="Left: averaged over sixteen subjects, the passive attenuation of an active noise reduction earmuff interpolated into one-third-octave bands, the active insertion loss of the ear with the lower value, their sum, and the assumed protection value at 84 % in each octave band. Right: the active insertion loss of each subject in one-third-octave bands, with the mean and the expanded uncertainty of the mean as error bars and a line at zero" width="92%"></picture>

## References

- International Organization for Standardization (2018). *Acoustics — Hearing
  protectors — Part 2: Estimation of effective A-weighted sound pressure levels
  when hearing protectors are worn* (ISO 4869-2:2018).
  [iso.org catalogue](https://www.iso.org/standard/65582.html).
  The implemented standard: Clauses 5 to 8 and the worked examples of
  Annexes A to D.
- International Organization for Standardization (2018). *Acoustics — Hearing
  protectors — Part 1: Subjective method for the measurement of sound
  attenuation* (ISO 4869-1:2018).
  [iso.org catalogue](https://www.iso.org/standard/65581.html).
  Where the per-subject attenuation values come from: 4.6, Annex A, Annex B
  and 4.2.2 with Table 1, validated against Tables A.2, A.3, B.1 and B.2.
- International Organization for Standardization (2019). *Acoustics — Hearing
  protectors — Part 6: Determination of sound attenuation of active noise
  reduction earmuffs* (ISO 4869-6:2019). The active insertion loss, its
  uncertainty, the total attenuation of 5.5 and the linear-operation check of
  5.4.4, validated against Tables A.2 and A.3 and ISO's calculation workbook.

## Standards

ISO 4869-1:2018, which measures the attenuation (4.6), gives the uncertainty of
its mean (Annex A, Tables A.2 and A.3), the test of whether two measurements
differ (Annex B, Tables B.1 and B.2) and the sound-field conditions of the test
room (4.2.2, Table 1). ISO 4869-2:2018, which defines the assumed protection
value $APV_{fx}$ (Clause 5), the octave-band method (Clause 6), the $H$, $M$ and
$L$ values (Clause 7) and the single number rating $SNR$ (Clause 8).
ISO 4869-6:2019, which adds the active insertion loss of an active noise
reduction earmuff to that attenuation (5.4, 5.5, Annex A).

## See also

- [Occupational Noise Exposure (ISO 9612)](occupational-exposure.md): the daily
  exposure level the protected level feeds into.
- [Noise-induced hearing loss (ISO 1999)](noise-induced-hearing-loss.md): what
  the exposure the protector did not stop does over a working life.
- [Hearing threshold (age and reference zero)](hearing-threshold.md): the
  baseline any protected exposure is judged against.
- API reference: [`hearing.real_ear_attenuation`](https://jmrplens.github.io/phonometry/reference/api/hearing/real-ear-attenuation/),
  [`hearing.hearing_protectors`](https://jmrplens.github.io/phonometry/reference/api/hearing/hearing-protectors/)
  and [`hearing.active_noise_reduction`](https://jmrplens.github.io/phonometry/reference/api/hearing/active-noise-reduction/).

← [Documentation index](../../README.md)

# Audiometric Test Methods (ISO 8253-1 and -2)

An audiogram is a set of hearing threshold levels, and each of them rests on a
room quiet enough not to mask the faintest tone, a rule that turns "heard" and
"not heard" into one number, and an uncertainty. ISO 8253-1 sets all three out
for earphones and bone vibrators, and ISO 8253-2 adds what a loudspeaker needs:
a room whose sound field is known.

## Is the room quiet enough? (ISO 8253-1 Clause 11)

Tables 2 and 4 give the maximum permissible ambient sound pressure level
$L_{S,\mathrm{max}}$ per one-third-octave band from 31.5 Hz to 8 kHz, for air
conduction with supra-aural earphones and for bone conduction, and for the
lowest test frequency (125 Hz, 250 Hz or, with earphones, 500 Hz). An earphone
that excludes more noise adds the difference of the attenuations of Table 3, a
lowest hearing threshold level other than 0 dB is added band by band, and a
threshold shift of +5 dB instead of +2 dB adds 8 dB (11.1 and the NOTEs):

$$
L_{S,\mathrm{max}}' = L_{S,\mathrm{max}}
+ \left(A_\mathrm{earphone} - A_\mathrm{supra\text{-}aural}\right)
+ L_\mathrm{HT,min} + \Delta
$$

```python
import numpy as np
from phonometry import hearing

# One-third-octave ambient levels of a single-walled booth, 31.5 Hz to 8 kHz.
booth = [50, 48, 45, 43, 40, 36, 30, 24, 19, 16, 14, 12, 11,
         10, 10, 10, 9, 9, 9, 8, 8, 8, 8, 8, 8]
supra_aural = hearing.check_audiometric_ambient_noise(booth)
print(supra_aural.passes, supra_aural.lowest_measurable_hearing_level_db)  # False 3.0
insert = hearing.check_audiometric_ambient_noise(booth, earphone="ER-3A")
print(insert.passes)                                                       # True
bone = hearing.check_audiometric_ambient_noise(
    booth, presentation="bone", lowest_test_frequency_hz=250
)
print(bone.lowest_measurable_hearing_level_db)                             # 6.0
```

`presentation="sound field"` judges the room against ISO 8253-2 Table 2, up to
12.5 kHz, derived from ISO 8253-1 for binaural listening (footnote a); laid side
by side, its cells are ISO 8253-1 Table 4 less 3 dB. For narrow-band noise as
the test signal, footnote b asks for lower limits and prints no figure, so the
check applies the table as printed. A measurement that leaves bands out does not
pass, and `noise_floor_db=` flags the bands within 6 dB of the meter's own floor
(11.1).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/audiometry_test_room_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/audiometry_test_room.svg" alt="The same booth's ambient spectrum against the air-conduction limits from 125 Hz: with supra-aural earphones it exceeds them from 63 Hz to 160 Hz, marked with crosses; with ER-3A insert earphones the limits are raised by the extra attenuation and the room qualifies" width="92%"></picture>

## From responses to a threshold (6.2 to 7.5)

- **Ascending method** (6.2.3.2, 6.2.4.2): 10 dB down after each response, 5 dB
  up after each miss; the threshold is the lowest level answered in more than
  half of the ascents, once three of at most five end at one level (two of
  three, shortened). The presentation sequence can be replayed, and the result
  gives the level to present next.
- **Bracketing method** (6.2.4.3): the mean of the averaged ascent and descent
  levels, rounded to the nearest 5 dB step (the library sends a tie up; the
  clause gives no rule for it).
- **Automatic recording** (6.3.5): the first reversal and both ends of
  excursions of 3 dB or less are ignored, and the mean of the averaged peaks and
  valleys is rounded **up** to the next whole decibel.
- **Sweep-frequency audiometry** (7.5): the three nearest peaks and valleys on a
  log-frequency axis, or a running average of six reversals.

```python
series = hearing.ascending_method_threshold(
    presentation_levels_db=[30, 20, 25, 15, 20, 25, 15, 20, 10, 15, 20, 25],
    responses=[1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1],
    familiarization_level_db=40.0,
)
print(series.ascent_levels_db, series.threshold_db)   # [25. 25. 20. 25.] 25.0
print(hearing.bracketing_method_threshold([30, 30, 35], [30, 35, 35]).threshold_db)  # 35.0
tracing = hearing.automatic_audiometry_threshold(
    [38, 22, 31, 21, 32, 20, 30, 29, 31, 19, 30, 20, 31, 21]
)
print(tracing.mean_db, tracing.threshold_db)          # 25.75 26.0
```

Each rule carries its clause's reliability test: a spread of more than 10 dB
between the levels it combines.

Three more rules judge the levels once found. `hearing.check_retest_agreement`
applies Step 3 of 6.2.3.2: the repeat at 1 kHz agrees to 5 dB or less, or a
change of 10 dB or more sends the test back to the further frequencies.
`hearing.audiogram_cautions` flags an air-conduction level of 40 dB or more
(cross-hearing, 6.2.3.2) and a bone-conduction level at the average vibrotactile
threshold of 8.4, 40, 60 and 70 dB at 250 Hz, 500 Hz and 1 kHz for the mastoid
and about 10 dB lower for the forehead
(`hearing.VIBROTACTILE_HEARING_LEVELS_DB`).

```python
print(hearing.check_retest_agreement(25.0, 35.0).retest_further_frequencies)  # True
cautions = hearing.audiogram_cautions(
    [250, 500, 1000, 2000], air_conduction_db=[20, 25, 30, 45],
    bone_conduction_db=[40, 20, 25, 40],
)
print(cautions.cross_hearing, cautions.vibrotactile)
# [False False False  True] [ True False False False]
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/audiometry_threshold_rules_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/audiometry_threshold_rules.svg" alt="Left: an ascending series of twelve presentations, the four ascents ending at 25, 25, 20 and 25 dB and the threshold of 25 dB. Right: an automatic recording, its ignored reversals grey, the peaks averaging 31 dB, the valleys 20.5 dB and the threshold 26 dB" width="92%"></picture>

## The uncertainty of a threshold (Annex A)

Eight uncorrelated inputs with a sensitivity coefficient of 1:
$u = \sqrt{\sum u_i^2}$ and $U = 2u$. With the typical values of A.3, air
conduction below 4 kHz without masking gives the example of Table A.2:

```python
budget = hearing.audiometric_uncertainty(1000.0)
print(np.round(budget.components_db[:4], 1))                   # [2.5 2.3 2.9 2. ]
print(round(budget.combined_db, 1), round(budget.expanded_db))  # 4.9 10
```

## The sound field (ISO 8253-2)

`hearing.check_free_sound_field` (5.2: ±1 dB at the lateral positions up to
4 kHz, ±2 dB above, the axial pair at 0.15 m within ±1 dB of the inverse
distance law), `hearing.check_quasi_free_sound_field` (5.4: ±2 dB, the axial
pair at 0.10 m, and a usable frequency range) and
`hearing.check_diffuse_sound_field` (5.3: six positions within ±2.5 dB, the ear
sides within 3 dB, and from 500 Hz a directional microphone's variation within
Table 1) qualify the room band by band; the directional test is a requirement,
and without it a diffuse field does not pass. The same diffuse-field check
serves ISO 4869-3 on the [hearing protectors](hearing-protectors.md) page.
`hearing.incidence_correction` reads the off-axis increases of Annex B, which
the text announces from 200 Hz and the table prints from 125 Hz (see
[ERRATA](../../ERRATA.md)).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/audiometry_sound_field_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/audiometry_sound_field.svg" alt="Left: a quasi-free field whose lateral and axial deviations leave 125 Hz and 250 Hz outside the field, usable from 500 Hz to 8000 Hz. Right: a diffuse field within all its limits, its directional variation under the 5 dB of Table 1" width="92%"></picture>

## References

- International Organization for Standardization (2010). *Acoustics —
  Audiometric test methods — Part 1: Pure-tone air and bone conduction
  audiometry* (ISO 8253-1:2010). Clause 11 with Tables 2 to 4, the threshold
  rules of 6.2.4, 6.3.5 and 7.5, the repeat and the cautions of 6.2.3.2 and
  8.4, and Annex A, validated against Tables 2 to 4, the levels of 8.4 and
  Table A.2.
- International Organization for Standardization (2009). *Acoustics —
  Audiometric test methods — Part 2: Sound field audiometry with pure-tone and
  narrow-band test signals* (ISO 8253-2:2009). The sound fields of 5.2 to 5.4,
  the ambient limits of Table 2 and the off-axis increases of Table B.1.

## Standards

ISO 8253-1:2010, which sets the maximum permissible ambient levels of an
audiometric test room (Clause 11, Tables 2 to 4), the rules that turn responses
into a hearing threshold level (6.2.4, 6.3.5, 7.5), the repeat at 1 kHz and the
cautions that judge that level (6.2.3.2, 8.4), and its uncertainty (Annex A). ISO 8253-2:2009, which qualifies a sound field as free,
quasi-free or diffuse (Clause 5), sets its ambient limits (Clause 6) and prints
the off-axis increases of Annex B.

## See also

- [Hearing threshold (age and reference zero)](hearing-threshold.md): the
  audiometric zero the hearing levels are measured from.
- [Hearing Protectors (ISO 4869-1, -2, -3 and -6)](hearing-protectors.md): the
  same diffuse-field test on the site where an earmuff is screened.
- API reference: [`hearing.audiometry`](https://jmrplens.github.io/phonometry/reference/api/hearing/audiometry/)
  and [`hearing.sound_field_audiometry`](https://jmrplens.github.io/phonometry/reference/api/hearing/sound-field-audiometry/).

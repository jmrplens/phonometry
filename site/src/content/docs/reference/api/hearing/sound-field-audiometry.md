---
title: "hearing.sound_field_audiometry"
description: "The sound field of an audiometric test room (ISO 8253-2:2009)."
sidebar:
  label: "sound_field_audiometry"
---

The sound field of an audiometric test room (ISO 8253-2:2009).

Sound field audiometry presents the test signal through one or more
loudspeakers instead of earphones, so the room becomes part of the
instrument. ISO 8253-2 specifies three sound fields a room may be qualified
as (Clause 5), each measured with the test subject and the chair absent and
with the same signals the audiometry will use (5.1):

- a **free sound field** (5.2): the loudspeaker at least 1 m from the
  reference point, the level 0,15 m to the left, right, above and below it
  within ±1 dB of the level at it up to and including 4 kHz and within ±2 dB
  above, the two ear-side positions within 3 dB of each other above 4 kHz,
  and the difference between the points 0,15 m in front of and behind it on
  the reference axis within ±1 dB of what the inverse distance law gives,

  $$
  \Delta L_\mathrm{theory} = 20 \lg \frac{r + d}{r - d}\ \mathrm{dB}
  $$

  with $r$ the distance from the loudspeaker to the reference point and
  $d$ = 0,15 m. Its NOTE says only an anechoic room meets it.
- a **quasi-free sound field** (5.4): the same arrangement with ±2 dB at the
  four lateral positions and the axial pair at $d$ = 0,10 m. Its usable
  frequency range is the range in which the requirements are met.
- a **diffuse sound field** (5.3): the level at six positions 0,15 m from the
  reference point, on the front-back, right-left and up-down axes, within
  ±2,5 dB of the level at it and the two ear-side positions within 3 dB of
  each other; from 500 Hz up, the levels a directional microphone reads at
  the reference point in the directions of the largest and the smallest
  incident energy stay within the variation Table 1 allows for the
  microphone's front-to-random sensitivity index (5 dB for an index of 5 dB
  or more, 4,5 dB for 4,5 dB, 4 dB for 4 dB, and a microphone below 4 dB is
  not suitable).

[`check_free_sound_field`](/phonometry/reference/api/hearing/sound-field-audiometry/#check_free_sound_field), [`check_quasi_free_sound_field`](/phonometry/reference/api/hearing/sound-field-audiometry/#check_quasi_free_sound_field) and
[`check_diffuse_sound_field`](/phonometry/reference/api/hearing/sound-field-audiometry/#check_diffuse_sound_field) judge those conditions band by band. The
diffuse-field judgement is the same one ISO 4869-3:2007, 5.2.2, asks of the
random-incidence field of its test site, with its own Table 1;
[`phonometry.hearing.check_random_incidence_field`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#check_random_incidence_field) runs it with that
table and returns the same [`DiffuseSoundFieldCheck`](/phonometry/reference/api/hearing/sound-field-audiometry/#diffusesoundfieldcheck).

**The ambient noise (Clause 6, Table 2).** The maximum permissible ambient
sound pressure levels for sound field audiometry, in one-third-octave bands
from 31,5 Hz to 12,5 kHz, for a lowest test frequency of 125 Hz or 250 Hz,
are [`SOUND_FIELD_AMBIENT_LIMITS_DB`](/phonometry/reference/api/hearing/sound-field-audiometry/#sound_field_ambient_limits_db). Its footnote a says they are
derived from ISO 8253-1 for binaural listening, and prints no offset; laid
side by side, from 31,5 Hz to 8 kHz each cell is the bone-conduction limit of
ISO 8253-1:2010 Table 4 less 3 dB, an observation the library makes on the
two printed tables and not a figure the footnote gives. Footnote b asks for
lower limits, by an amount it does not print, when narrow-band noise is the
test signal.
[`phonometry.hearing.check_audiometric_ambient_noise`](/phonometry/reference/api/hearing/audiometry/#check_audiometric_ambient_noise) judges a measured
spectrum against them with `presentation="sound field"`.

**Off-axis loudspeakers (Annex B, informative).** No standardized reference
threshold exists for a loudspeaker away from 0° incidence (4.8, NOTE 1).
Table B.1 prints how much higher the sound pressure level is at the ear
closest to the loudspeaker at 45° and 90°, rounded to the nearest 0,5 dB, which
[`INCIDENCE_CORRECTIONS_DB`](/phonometry/reference/api/hearing/sound-field-audiometry/#incidence_corrections_db) carries and [`incidence_correction`](/phonometry/reference/api/hearing/sound-field-audiometry/#incidence_correction)
reads. The paragraph above the table announces it from 200 Hz; its rows start
at 125 Hz, and the library carries every printed row (see `docs/ERRATA.md`).

Clause, table and annex numbers refer to ISO 8253-2:2009(E).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_diffuse_sound_field

```python
check_diffuse_sound_field(
    position_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    directional_levels_db: ArrayLike | None = None,
    front_to_random_index_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> DiffuseSoundFieldCheck
```

Is the sound field of the test room diffuse? (ISO 8253-2, 5.3).

Measured with the test subject and the chair absent, with the signals the
audiometry will use:

- a) the level at each of the six positions 0,15 m from the reference
  point, front and back, left and right, up and down, read with an
  omnidirectional microphone kept in one orientation, stays within
  ±2,5 dB of the level at the reference point, and the extreme right and
  left positions within 3 dB of each other;
- b) from 500 Hz up, the levels a directional microphone reads at the
  reference point in the directions of the largest and smallest incident
  energy stay within the variation Table 1 allows for its front-to-random
  sensitivity index ([`DIFFUSE_FIELD_VARIATION_LIMITS`](/phonometry/reference/api/hearing/sound-field-audiometry/#diffuse_field_variation_limits)).

The readings of b) are taken in as many directions as the microphone and
the loudspeakers need, including the two planes where the extremes are
expected (footnote a); the variation is the largest less the smallest of
them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `position_levels_db` | The level at each position per test signal, in dB, keyed `"front"`, `"back"`, `"left"`, `"right"`, `"up"` and `"down"`. |
| `reference_levels_db` | The level at the reference point per test signal, in dB. |
| `directional_levels_db` | The levels the directional microphone read at the reference point, a `(directions, bands)` grid in dB on the same band axis; bands below 500 Hz are not read and may be NaN. `None` leaves b) unjudged, and the verdict then does not pass. |
| `front_to_random_index_db` | The microphone's front-to-random sensitivity index, in dB, one number or one per band; required with `directional_levels_db`. A band where it is below 4 dB, or NaN, is left unjudged, since Table 1 says the microphone is not suitable there. |
| `frequencies` | The frequencies of the test signals, in hertz, or `None` for the eleven audiometric frequencies from 125 Hz to 8 kHz. |

**Returns:** [`DiffuseSoundFieldCheck`](/phonometry/reference/api/hearing/sound-field-audiometry/#diffusesoundfieldcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a position is missing or unknown, if the bands do not match, if a reading is given without its index or the other way round, if a single index is below 4 dB, or if a band from 500 Hz up has fewer than two finite readings. |

## check_free_sound_field

```python
check_free_sound_field(
    lateral_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    front_levels_db: ArrayLike,
    back_levels_db: ArrayLike,
    loudspeaker_distance_m: float,
    frequencies: ArrayLike | None = None,
) -> FreeSoundFieldCheck
```

Is the sound field of the test room free? (ISO 8253-2, 5.2).

Measured with the test subject and the chair absent, the loudspeaker at
the head height of a seated listener with its reference axis through the
reference point:

- a) the loudspeaker is at least 1 m from the reference point;
- b) the level 0,15 m from the reference point to the left, right, above
  and below it stays within ±1 dB of the level at it up to and including
  4 kHz and within ±2 dB above, and above 4 kHz the right and left
  positions differ by 3 dB at most;
- c) the level at the point 0,15 m in front of the reference point on the
  reference axis less the level 0,15 m behind it stays within ±1 dB of the
  inverse distance law,

  $$
  \Delta L_\mathrm{theory} = 20 \lg \frac{r + 0{,}15\ \mathrm{m}} {r - 0{,}15\ \mathrm{m}}\ \mathrm{dB}
  $$

  with $r$ the distance from the loudspeaker to the reference
  point, the point source the law assumes.

Pure tones may only be used in a field that meets this (4.2), and the NOTE
to 5.2 says only an anechoic room does.

**Parameters**

| Name | Description |
| :--- | :--- |
| `lateral_levels_db` | The level at each lateral position per test signal, in dB, keyed `"left"`, `"right"`, `"up"` and `"down"`. |
| `reference_levels_db` | The level at the reference point per test signal, in dB. |
| `front_levels_db` | The level on the reference axis 0,15 m in front of the reference point, towards the loudspeaker, in dB. |
| `back_levels_db` | The level 0,15 m behind it, in dB. |
| `loudspeaker_distance_m` | $r$, in metres. A distance under 1 m is judged, not refused: the verdict fails a). |
| `frequencies` | The test frequencies, in hertz, or `None` for the eleven audiometric frequencies from 125 Hz to 8 kHz. |

**Returns:** [`FreeSoundFieldCheck`](/phonometry/reference/api/hearing/sound-field-audiometry/#freesoundfieldcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a position is missing or unknown, if the bands do not match, or if the distance is not larger than 0,15 m. |

## check_quasi_free_sound_field

```python
check_quasi_free_sound_field(
    lateral_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    front_levels_db: ArrayLike,
    back_levels_db: ArrayLike,
    loudspeaker_distance_m: float,
    frequencies: ArrayLike | None = None,
) -> FreeSoundFieldCheck
```

Is the sound field of the test room quasi-free? (ISO 8253-2, 5.4).

The field a room that is not anechoic can still offer, measured with the
test subject and the chair absent and all other working conditions kept:

- a) the loudspeaker's reference point is at least 1 m from the
  reference point;
- b) the level 0,15 m from the reference point to the left, right, above
  and below it stays within ±2 dB of the level at it;
- c) the level 0,10 m in front of the reference point on the reference
  axis less the level 0,10 m behind it stays within ±1 dB of the inverse
  distance law,

  $$
  \Delta L_\mathrm{theory} = 20 \lg \frac{r + 0{,}10\ \mathrm{m}} {r - 0{,}10\ \mathrm{m}}\ \mathrm{dB}
  $$

The usable frequency range of the field is the range in which these hold,
which [`FreeSoundFieldCheck.usable_frequencies`](/phonometry/reference/api/hearing/sound-field-audiometry/#freesoundfieldcheckusable_frequencies) gives.

**Parameters**

| Name | Description |
| :--- | :--- |
| `lateral_levels_db` | The level at each lateral position per test signal, in dB, keyed `"left"`, `"right"`, `"up"` and `"down"`. |
| `reference_levels_db` | The level at the reference point per test signal, in dB. |
| `front_levels_db` | The level on the reference axis 0,10 m in front of the reference point, towards the loudspeaker, in dB. |
| `back_levels_db` | The level 0,10 m behind it, in dB. |
| `loudspeaker_distance_m` | $r$, in metres. A distance under 1 m is judged, not refused: the verdict fails a). |
| `frequencies` | The test frequencies, in hertz, or `None` for the eleven audiometric frequencies from 125 Hz to 8 kHz. |

**Returns:** [`FreeSoundFieldCheck`](/phonometry/reference/api/hearing/sound-field-audiometry/#freesoundfieldcheck) with `field="quasi-free"`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a position is missing or unknown, if the bands do not match, or if the distance is not larger than 0,10 m. |

## DIFFUSE_FIELD_VARIATION_LIMITS

*Constant* (`tuple`).

```python
DIFFUSE_FIELD_VARIATION_LIMITS = ((5.0, 5.0), (4.5, 4.5), (4.0, 4.0))
```

## DiffuseSoundFieldCheck

```python
DiffuseSoundFieldCheck(
    frequencies: np.ndarray,
    position_deviation_db: np.ndarray,
    left_right_difference_db: np.ndarray,
    directional_variation_db: np.ndarray,
    allowable_variation_db: np.ndarray,
    standard: str,
    positions: tuple[str, ...] = ('front', 'back', 'left', 'right', 'up', 'down'),
)
```

Whether a sound field is diffuse enough, band by band.

The verdict of ISO 8253-2:2009, 5.3, and of the random-incidence field of
ISO 4869-3:2007, 5.2.2, which ask the same two things and differ only in
the Table 1 that turns a microphone's front-to-random sensitivity index
into the variation it may read.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | The centre frequencies of the test signals, in hertz. |
| `position_deviation_db` | The level at each of the six positions 0,15 m from the reference point less the level at it, one row per position in the order of `positions`, in dB. |
| `left_right_difference_db` | The difference between the right and left positions per band, as an absolute value, in dB. |
| `directional_variation_db` | The largest less the smallest level the directional microphone read at the reference point per band, in dB, or NaN where no reading was given or the band is below 500 Hz. |
| `allowable_variation_db` | What the Table 1 allows that variation per band, in dB, or NaN where it is not judged: below 500 Hz, without a directional reading, or where the microphone's index is below the table's last row. |
| `standard` | The clause this check applies, for the figure and the messages. |
| `positions` | The position names, in row order. |

The directional test is a requirement, not an option: a band from 500 Hz
up without a suitable microphone's reading is not judged,
`directionality_judged` says so, and `passes` is `False`
until it is. `uniform` and `balanced` still give the verdict
of the six positions on their own.

### DiffuseSoundFieldCheck.balanced

*property*

Per band, whether right and left differ by 3 dB at most.

**Returns:** One boolean per band.

### DiffuseSoundFieldCheck.diffuse

*property*

Per band, whether the directional variation stays within Table 1.

Bands the test does not reach, below 500 Hz, count as meeting it; a
band from 500 Hz up that was not judged reads `False`.

**Returns:** One boolean per band.

### DiffuseSoundFieldCheck.directional_judged

*property*

Per band, whether the directional test was judged.

**Returns:** `True` where a suitable microphone's reading was given, and below 500 Hz, where the test does not apply.

### DiffuseSoundFieldCheck.directional_required

*property*

Per band, whether the directional test applies (500 Hz and up).

**Returns:** One boolean per band.

### DiffuseSoundFieldCheck.directionality_judged

*property*

Whether every band from 500 Hz up was judged by a suitable microphone.

**Returns:** `True` when none is left unjudged.

### DiffuseSoundFieldCheck.passes

*property*

Whether the field qualifies as diffuse, every requirement judged.

**Returns:** `True` when every band meets the six positions, the right-left difference and the directional test.

### DiffuseSoundFieldCheck.plot()

```python
DiffuseSoundFieldCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each condition against its limit, band by band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the worst position deviation curve. |

**Returns:** The axes.

### DiffuseSoundFieldCheck.uniform

*property*

Per band, whether all six positions stay within ±2,5 dB.

**Returns:** One boolean per band.

## FreeSoundFieldCheck

```python
FreeSoundFieldCheck(
    field: str,
    frequencies: np.ndarray,
    lateral_deviation_db: np.ndarray,
    axis_difference_db: np.ndarray,
    inverse_distance_difference_db: float,
    loudspeaker_distance_m: float,
    axis_offset_m: float,
    positions: tuple[str, ...] = ('left', 'right', 'up', 'down'),
)
```

Whether a free or quasi-free sound field is met, band by band.

The verdict of ISO 8253-2:2009, 5.2 (free) or 5.4 (quasi-free).

**Attributes**

| Name | Description |
| :--- | :--- |
| `field` | `"free"` or `"quasi-free"`. |
| `frequencies` | The frequencies of the test signals, in hertz. |
| `lateral_deviation_db` | The level at each of the four positions 0,15 m from the reference point less the level at it, one row per position in the order of `positions`, in dB. |
| `axis_difference_db` | The level at the axial point in front of the reference point, towards the loudspeaker, less the level at the one behind it, per band, in dB. |
| `inverse_distance_difference_db` | What the inverse distance law gives for that difference, $20 \lg((r + d)/(r - d))$, in dB. |
| `loudspeaker_distance_m` | $r$, the distance from the loudspeaker to the reference point, in metres. |
| `axis_offset_m` | $d$, how far the axial points sit from the reference point: 0,15 m for a free field, 0,10 m for a quasi-free one. |
| `positions` | The lateral position names, in row order. |

### FreeSoundFieldCheck.balanced

*property*

Per band, whether right and left differ by 3 dB at most above 4 kHz.

5.2 b) asks it of a free field above 4 kHz only; below, and for a
quasi-free field, the band reads `True`.

**Returns:** One boolean per band.

### FreeSoundFieldCheck.compliant

*property*

Per band, whether every positional requirement is met.

**Returns:** One boolean per band.

### FreeSoundFieldCheck.distance_adequate

*property*

Whether the loudspeaker is at least 1 m from the reference point.

**Returns:** `True` when 5.2 a) or 5.4 a) is met.

### FreeSoundFieldCheck.follows_inverse_distance_law

*property*

Per band, whether the axial difference is within ±1 dB of the law.

**Returns:** One boolean per band.

### FreeSoundFieldCheck.inverse_distance_deviation_db

*property*

The axial difference less what the inverse distance law gives, in dB.

**Returns:** One value per band.

### FreeSoundFieldCheck.lateral_tolerance_db

*property*

The tolerance of the four lateral positions per band, in dB.

**Returns:** ±1 dB up to and including 4 kHz and ±2 dB above for a free field (5.2 b)), ±2 dB throughout for a quasi-free one (5.4 b)).

### FreeSoundFieldCheck.left_right_difference_db

*property*

The difference between the right and left positions, in dB.

**Returns:** Its absolute value per band.

### FreeSoundFieldCheck.passes

*property*

Whether the field qualifies at every test frequency given.

**Returns:** `True` when the loudspeaker distance and every band meet the clause.

### FreeSoundFieldCheck.plot()

```python
FreeSoundFieldCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the lateral and axial conditions against their limits.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the worst lateral deviation curve. |

**Returns:** The axes.

### FreeSoundFieldCheck.uniform

*property*

Per band, whether all four lateral positions stay within tolerance.

**Returns:** One boolean per band.

### FreeSoundFieldCheck.usable_frequencies

*property*

The frequencies at which the field meets its requirements, in hertz.

For a quasi-free field this is its usable frequency range (5.4).

**Returns:** The frequencies of the compliant bands.

## incidence_correction

```python
incidence_correction(
    frequencies: ArrayLike,
    *,
    incidence_angle_deg: float,
) -> np.ndarray
```

How much louder the nearer ear is with the loudspeaker off axis (Table B.1).

The increase in sound pressure level at the ear closest to the
loudspeaker at 45° or 90° incidence, relative to 0°, rounded to the
nearest 0,5 dB as Annex B prints it. The annex is informative and says
no standardized reference threshold exists for these angles (4.8,
NOTE 1); how a report uses the increase is left to it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Test frequencies in hertz, each one of [`INCIDENCE_CORRECTION_FREQUENCIES_HZ`](/phonometry/reference/api/hearing/sound-field-audiometry/#incidence_correction_frequencies_hz). |
| `incidence_angle_deg` | 45 or 90. |

**Returns:** The increase per frequency, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for another angle, or a frequency Table B.1 does not list. |

## INCIDENCE_CORRECTION_FREQUENCIES_HZ

*Constant* (`tuple`).

```python
INCIDENCE_CORRECTION_FREQUENCIES_HZ = (125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1500.0, 1600.0, 2000.0, 2500.0, 3000.0, 3150.0, 4000.0, 5000.0, 6000.0, 6300.0, 8000.0, 10000.0, 12500.0)
```

## INCIDENCE_CORRECTIONS_DB

*Constant* (`mapping`).

```python
INCIDENCE_CORRECTIONS_DB = {45.0: array([0.5, 1. , 1. , 1. , 1.5, 2.5, 3. , 3.5, 3.5, 4. , 4. , 3.5, 3.5,
       3. , 3.5, 5. , 5. , 4. , 6. , 7.5, 7.5, 5.5, 4.5, 1.5]), 90.0: array([ 1. ,  1.5,  1.5,  2. ,  2.5,  3.5,  4.5,  5. ,  5. ,  5.5,  6. ,
        5. ,  4.5,  2. ,  2. ,  2.5,  2. , -0.5,  4. ,  9.5, 10. ,  8.5,
        6. ,  8. ])}
```

## SOUND_FIELD_AMBIENT_BANDS_HZ

*Constant* (`tuple`).

```python
SOUND_FIELD_AMBIENT_BANDS_HZ = (31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0, 12500.0)
```

## SOUND_FIELD_AMBIENT_LIMITS_DB

*Constant* (`mapping`).

```python
SOUND_FIELD_AMBIENT_LIMITS_DB = {125.0: array([52., 44., 38., 32., 27., 22., 17., 14., 12., 10.,  8.,  6.,  5.,
        5.,  4.,  4.,  4.,  5.,  5.,  3.,  1., -1.,  1.,  6., 12., 14.,
       15.]), 250.0: array([60., 53., 46., 41., 36., 32., 25., 18., 12., 10.,  8.,  6.,  5.,
        5.,  4.,  4.,  4.,  5.,  5.,  3.,  1., -1.,  1.,  6., 12., 14.,
       15.])}
```

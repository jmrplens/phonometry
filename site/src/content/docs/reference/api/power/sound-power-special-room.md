---
title: "emission.sound_power_special_room"
description: "Sound power level of a small movable source in a special reverberation test room: ISO 3743-2:2018 (engineering grade 2), the direct method and the comparison method."
sidebar:
  label: "sound_power_special_room"
---

Sound power level of a small movable source in a special reverberation
test room: ISO 3743-2:2018 (engineering grade 2), the direct method and the
comparison method.

Part 1 of ISO 3743 asks little of the room and pays with a reference sound
source at every determination. Part 2 turns that round: the room is built to
a specification tight enough that the sound power can be read off the mean
room level alone. It is at least 70 m³ (and at most 300 m³ when the 4 kHz and
8 kHz octaves matter, 6.2), its floor reflects (absorption coefficient below
0,06) and its walls and ceiling absorb alike, each within 0,5 and 1,5 times
their mean (6.4), and above all its reverberation time follows a prescribed
curve (6.3): within 0,9 and 1,1 times $R\,T_\mathrm{nom}$ (0,8 and 1,2
above 6,3 kHz), with the reverberation parameter

$$
R = 1 + \frac{257}{f V^{1/3}} \tag{Formula 1}
$$

or, for a room that is not nearly cubical, $R = 1 + cS/(8Vf)$, and a
nominal reverberation time $T_\mathrm{nom}$ between 0,5 s and 1,0 s.
The rise of $R$ at low frequencies is the Waterhouse correction built
into the room: the energy stored near the boundaries of a small room is
compensated by a longer reverberation time instead of a term in the
equation. So the direct method reduces to (10.2)

$$
L_W = \overline{L_p} - 10 \log_{10}\frac{T_\mathrm{nom}}{T_0} + 10 \log_{10}\frac{V}{V_0} - 13\ \mathrm{dB} \tag{Formula 9}
$$

for each octave band and for the A-weighted level measured as such, with
$T_0$ = 1 s and $V_0$ = 1 m³; the 13 dB instead of the 14 dB of
other standards, and the slope of the reverberation time, account for the
energy density near the surfaces and near the source (NOTE to 10.2). The
comparison method replaces the room by a reference sound source measured at
no fewer than six positions (10.3):

$$
L_{W\mathrm{e}} = L_{p\mathrm{e}} + \left(L_{W\mathrm{r}} - L_{p\mathrm{r}}\right) \tag{Formula 10}
$$

Both methods take the mean of the measured levels as the energy mean of all
of them (Formula 8) after correcting each one for background noise by the
stepped Table 4, 2 dB at a 4 dB or 5 dB margin, 1 dB from 6 dB to 8 dB,
0,5 dB at 9 dB and 10 dB and nothing above; a margin below 4 dB leaves the
level unreportable unless the report says the requirement of 6.5 was not met.
The table gives whole-decibel differences, and the library reads a measured
difference at the nearest whole decibel (a margin of 5,4 dB takes the 5 dB
row, one of 5,5 dB the 6 dB row), anything above 10 dB taking the last row.

Annex E carries the level to the reference meteorological conditions with the
radiation-impedance correction $C_2$ of ISO 3743-1:2010 Annex A, and
Annex F forms the A-weighted level from octave bands with Table F.1, which is
ISO 3743-1:2010 Table B.1. Clause 11 prints its own typical upper bounds of
$\sigma_{R0}$ (Table 5): 5,0 dB at 125 Hz, 3,0 dB at 250 Hz, 2,0 dB from
500 Hz to 4 kHz, 3,0 dB at 8 kHz and 2,0 dB A-weighted.

The room is qualified by [`check_special_room_reverberation`](/phonometry/reference/api/power/sound-power-special-room/#check_special_room_reverberation) (6.2, 6.3
and the climate of 6.6), [`check_special_room_surfaces`](/phonometry/reference/api/power/sound-power-special-room/#check_special_room_surfaces) (6.4) and
[`check_special_room_suitability`](/phonometry/reference/api/power/sound-power-special-room/#check_special_room_suitability) (6.7, the octave-band power of a
calibrated reference source determined in the room against its calibration,
Table 1). The number of source locations and microphone positions follows
from the survey of 9.4 by [`special_room_source_locations`](/phonometry/reference/api/power/sound-power-special-room/#special_room_source_locations) (Table 3),
which also reads the spectral character of 9.5.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_special_room_reverberation

```python
check_special_room_reverberation(
    reverberation_time_s: ArrayLike,
    frequencies: ArrayLike,
    *,
    volume_m3: float,
    nominal_reverberation_time_s: float | None = None,
    surface_area_m2: float | None = None,
    speed_of_sound: float | None = None,
    method: Method = 'direct',
    relative_humidity_percent: float | None = None,
    temperature_c: float | None = None,
    reverberation_relative_humidity_percent: float | None = None,
    reverberation_temperature_c: float | None = None,
    source_volume_m3: float | None = None,
) -> SpecialRoomReverberationCheck
```

Is this room's reverberation time the one ISO 3743-2:2018 prescribes?
6.2, 6.3 and 6.6.

The measured reverberation time shall lie between $0{,}9\,R\, T_\mathrm{nom}$ and $1{,}1\,R\,T_\mathrm{nom}$ in every band (0,8
and 1,2 above 6,3 kHz), with $R$ from Formula (1) or its NOTE
([`reverberation_parameter`](/phonometry/reference/api/power/sound-power-special-room/#reverberation_parameter)), and $T_\mathrm{nom}$ between
0,5 s and 1,0 s. Annex B finds $T_\mathrm{nom}$ "by centring the
measured values of T (normalized to the reverberation time at 1 000 Hz)
within the limiting curves" (B.5) and prints no rule for it. The library
takes the one whose verdict is the requirement of 6.3 itself: the
$T_\mathrm{nom}$ that leaves the most margin, minimising the largest
deviation of any band from the ideal curve measured against that band's
own tolerance, so that a room passes whenever some $T_\mathrm{nom}$
puts every band within its curves. If the curve is followed exactly this
gives Formula (B.2),
$T_\mathrm{nom} = T_{1\,000}/R(1\,000\ \mathrm{Hz})$.

The EXAMPLE of B.5 departs from this rule. On the curve of Figure B.4 it
reads $T/T_\mathrm{nom}$ = 1,09 at 1 kHz and
$T_\mathrm{nom}$ = 0,8 s/1,09 = 0,73 s, where the rule gives 1,05
and 0,76 s, 0,17 dB apart in the $L_W$ of Formula (9). The 1,09 is
the midpoint of the extreme ratios taken against the 0,9 and 1,1 limits
alone, the wider limits above 6,3 kHz left out, and it puts the 250 Hz
band of Figure B.4 at 1,13 R, above the 1,1 R within which the NOTE to
Figure B.3 says the data are centred; Figure B.3 draws that band, and
those at 100 Hz and 10 kHz, where 1,09 does not put them (see
`docs/ERRATA.md`). A value supplied in `nominal_reverberation_time_s`,
the printed 0,73 s among them, is checked as given instead.

6.2 adds the volume: at least 70 m³, and at most 300 m³ when the 4 kHz
and 8 kHz octaves are within the frequency range, which the direct method
needs and the comparison method does not (NOTE). 6.6 adds the climate:
the product $H(\theta + 5\ ^\circ\mathrm{C})$ during the test shall
stay within ±10 % of its value while the reverberation time was measured,
checked when all four climate values are given. Clause 5 recommends a
noise source of at most 1 % of the room's volume, 0,7 m³ in a room of
70 m³; given `source_volume_m3`, the check reads it, and warns above it,
but keeps it out of the verdict, the clause saying "should".

**Parameters**

| Name | Description |
| :--- | :--- |
| `reverberation_time_s` | Measured reverberation time per band, in seconds, in one-third-octave bands as Figure B.3 has them. |
| `frequencies` | Band centre frequencies, in hertz. |
| `volume_m3` | Volume of the test room, in cubic metres. |
| `nominal_reverberation_time_s` | $T_\mathrm{nom}$ to check, in seconds; `None` centres it. |
| `surface_area_m2` | Room surface area for the NOTE form of $R$, in square metres, with `speed_of_sound`. |
| `speed_of_sound` | Speed of sound for the NOTE form, in metres per second. |
| `method` | `'direct'` (default) or `'comparison'`, for the 300 m³ ceiling. |
| `relative_humidity_percent` | Relative humidity during the test, in per cent. |
| `temperature_c` | Temperature during the test, in degrees Celsius. |
| `reverberation_relative_humidity_percent` | Relative humidity while the reverberation time was measured, in per cent. |
| `reverberation_temperature_c` | Temperature while the reverberation time was measured, in degrees Celsius. |
| `source_volume_m3` | Volume of the noise source to be tested, in cubic metres, for the recommendation of clause 5; `None` skips it. |

**Returns:** The verdict, as a [`SpecialRoomReverberationCheck`](/phonometry/reference/api/power/sound-power-special-room/#specialroomreverberationcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for reverberation times that are not positive and finite, a length mismatch, the refusals of [`reverberation_parameter`](/phonometry/reference/api/power/sound-power-special-room/#reverberation_parameter), an unknown method, a climate given in part or out of range, or a source volume that is not positive. |

## check_special_room_suitability

```python
check_special_room_suitability(
    measured_power_levels: ArrayLike,
    calibrated_power_levels: ArrayLike,
    frequencies: ArrayLike,
) -> SpecialRoomSuitabilityCheck
```

Is the room suitable for broad-band sources? ISO 3743-2:2018, 6.7.

A small broad-band reference sound source calibrated by ISO 3741, or by
ISO 6926 and ISO 3745 (step 1), has its octave-band power levels
determined in the room by this standard (step 2); the differences from
the calibration (step 3) may not exceed Table 1 (step 4): ±5 dB at
125 Hz, ±3 dB from 250 Hz to 4 kHz and ±4 dB at 8 kHz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `measured_power_levels` | The reference source's octave-band power levels determined in the room, in decibels. |
| `calibrated_power_levels` | Its calibrated levels, in decibels. |
| `frequencies` | Octave centres from 125 Hz to 8 kHz, ascending. |

**Returns:** The verdict, as a [`SpecialRoomSuitabilityCheck`](/phonometry/reference/api/power/sound-power-special-room/#specialroomsuitabilitycheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for non-finite levels, mismatched lengths, or bands outside Table 1. |

## check_special_room_surfaces

```python
check_special_room_surfaces(
    surface_absorption_coefficients: ArrayLike,
    floor_absorption_coefficients: ArrayLike,
    frequencies: ArrayLike,
    *,
    surface_areas_m2: ArrayLike | None = None,
) -> SpecialRoomSurfaceCheck
```

Are the room's surfaces treated as ISO 3743-2:2018, 6.4 asks?

The floor shall be reflective, its absorption coefficient below 0,06, and
apart from the floor no surface may absorb significantly differently from
the others: in each octave band the mean absorption coefficient of each
wall and of the ceiling lies within 0,5 and 1,5 times the mean of the
walls and ceiling. The clause does not say how that mean is formed; with
`surface_areas_m2` it is weighted by area, which is the room's own mean,
and without them it is the plain mean of the surfaces.

**Parameters**

| Name | Description |
| :--- | :--- |
| `surface_absorption_coefficients` | Mean absorption coefficient of each wall and of the ceiling, `(surfaces, bands)`, at least two surfaces. |
| `floor_absorption_coefficients` | The floor's coefficient per band. |
| `frequencies` | Octave-band centre frequencies, in hertz. |
| `surface_areas_m2` | Area of each wall and of the ceiling, in square metres, for the area-weighted mean; `None` for the plain mean. |

**Returns:** The verdict, as a [`SpecialRoomSurfaceCheck`](/phonometry/reference/api/power/sound-power-special-room/#specialroomsurfacecheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for coefficients outside [0, 1], fewer than two surfaces, mismatched bands, or areas that are not one positive value per surface. |

## reverberation_parameter

```python
reverberation_parameter(
    frequencies: ArrayLike,
    volume_m3: float,
    *,
    surface_area_m2: float | None = None,
    speed_of_sound: float | None = None,
) -> np.ndarray
```

The reverberation parameter $R$ of ISO 3743-2:2018, 6.3.

$$
R = 1 + \frac{257}{f V^{1/3}} \tag{Formula 1}
$$

for a room that is nearly cubical, or, by the NOTE to 6.3, the more robust

$$
R = 1 + \frac{c\,S}{8 V f}
$$

for any shape, which is the Waterhouse factor of ISO 3741 turned into a
target for the reverberation time. The two agree for a cube when
$c = 257 \times 8/6 = 342{,}7$ m/s, which is the speed of sound
Formula (1) carries inside its constant. For 70 m³ the value at 1 kHz is
the 1,06 of Formula (B.2).

6.3 sends a 70 m³ room to Figure 1 instead, but the printed curve runs
0,03 to 0,04 above Formula (1) from 100 Hz to 160 Hz and about 0,01 below
it from 1 600 Hz up (see `docs/ERRATA.md`), so Formula (1) is used for
that volume too and nothing is read off the figure.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Band centre frequencies, in hertz. |
| `volume_m3` | Volume of the test room, in cubic metres. |
| `surface_area_m2` | Total surface area of the room, in square metres; with `speed_of_sound` it selects the NOTE form. |
| `speed_of_sound` | Speed of sound, in metres per second, required with `surface_area_m2` and refused without it. |

**Returns:** $R$ per frequency.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive frequency, volume, area or speed, or only one of the NOTE's two inputs. |

## sound_power_special_room

```python
sound_power_special_room(
    levels: ArrayLike,
    frequencies: ArrayLike,
    *,
    volume_m3: float,
    nominal_reverberation_time_s: float,
    background_levels: ArrayLike | None = None,
    a_weighted_levels: ArrayLike | None = None,
    a_weighted_background_levels: ArrayLike | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    sigma_omc_db: float | None = None,
    coverage_factor: float = 2.0,
) -> SpecialRoomSoundPowerResult
```

Sound power level in a special reverberation test room, direct method
(ISO 3743-2:2018, 10.2).

Every measured level is corrected for background noise by Table 4 at its
own microphone position (9.8), the corrected levels are energy-averaged
over all positions and source locations (Formula 8), and

$$
L_W = \overline{L_p} - 10 \log_{10}\frac{T_\mathrm{nom}}{T_0} + 10 \log_{10}\frac{V}{V_0} - 13\ \mathrm{dB} \tag{Formula 9}
$$

in each octave band. Given the A-weighted levels as well, the same
formula gives the A-weighted sound power level directly, which is how
clause 4 describes the method; `sound_power_level_a` is in any case the
Annex F total of the octave bands.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Measured octave-band levels, in decibels: `(bands,)` for a microphone traverse, `(NM, bands)` for fixed positions, or `(NS, NM, bands)` for several source locations (9.4). |
| `frequencies` | Nominal octave centres from 63 Hz to 8 kHz, ascending (Table F.1; 63 Hz under its footnote). |
| `volume_m3` | Volume of the test room, in cubic metres. |
| `nominal_reverberation_time_s` | $T_\mathrm{nom}$ of the room (6.3), in seconds, as [`check_special_room_reverberation`](/phonometry/reference/api/power/sound-power-special-room/#check_special_room_reverberation) finds it. |
| `background_levels` | Background levels, `(NM, bands)` or one `(bands,)` spectrum for every position, in decibels; `None` applies no correction, warns, and leaves `background_requirement_met` `False`. |
| `a_weighted_levels` | The A-weighted levels measured with the source, one per position (`(NM,)` or `(NS, NM)`) or one traverse level, in decibels; `None` leaves the direct A-weighted level `NaN`. |
| `a_weighted_background_levels` | The A-weighted background, one level or one per position, in decibels. |
| `temperature_c` | Air temperature at the test, in degrees Celsius. |
| `static_pressure_kpa` | Static pressure at the test, in kilopascals. |
| `sigma_omc_db` | Operating-and-mounting standard deviation (11.2), in decibels; `None` leaves the total and expanded uncertainty `NaN`. |
| `coverage_factor` | `k` of Formula (13), 2 by default. |

**Returns:** [`SpecialRoomSoundPowerResult`](/phonometry/reference/api/power/sound-power-special-room/#specialroomsoundpowerresult) with `method='direct'`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels or a background of an inadmissible shape or not finite, frequencies outside Table F.1, a non-positive volume or nominal reverberation time, a climate out of range, a negative `sigma_omc_db` or a coverage factor that is not positive. |

## sound_power_special_room_comparison

```python
sound_power_special_room_comparison(
    levels: ArrayLike,
    levels_ref: ArrayLike,
    lw_ref: ArrayLike,
    frequencies: ArrayLike,
    *,
    background_levels: ArrayLike | None = None,
    background_levels_ref: ArrayLike | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    sigma_omc_db: float | None = None,
    coverage_factor: float = 2.0,
) -> SpecialRoomSoundPowerResult
```

Sound power level in a special reverberation test room, comparison
method (ISO 3743-2:2018, 10.3).

A reference source meeting Annex A stands on the floor at least 1,5 m from
any wall; its mean octave-band level $L_{p\mathrm{r}}$ is determined
at no fewer than six microphone positions, and that of the source under
test, $L_{p\mathrm{e}}$, as for the direct method, both after the
Table 4 background correction (9.8) and the mean of Formula (8). Then

$$
L_{W\mathrm{e}} = L_{p\mathrm{e}} + \left(L_{W\mathrm{r}} - L_{p\mathrm{r}}\right) \tag{Formula 10}
$$

and the A-weighted level follows from the octave bands by Annex F (10.4).
The room drops out, so neither its volume nor its reverberation time is
needed, and the 300 m³ ceiling of 6.2 does not apply (NOTE).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Levels of the source under test, `(bands,)`, `(NM, bands)` or `(NS, NM, bands)`, in decibels. |
| `levels_ref` | Levels of the reference source, `(NMr, bands)`, at least six positions (10.3), or one traverse level `(bands,)`. |
| `lw_ref` | The reference source's calibrated octave-band power level $L_{W\mathrm{r}}$, `(bands,)`, in decibels. |
| `frequencies` | Nominal octave centres from 63 Hz to 8 kHz. |
| `background_levels` | Background for the source under test, as in [`sound_power_special_room`](/phonometry/reference/api/power/sound-power-special-room/#sound_power_special_room). |
| `background_levels_ref` | Background at the reference source's positions; `None` reuses `background_levels` when it fits them. |
| `temperature_c` | Air temperature at the test, in degrees Celsius. |
| `static_pressure_kpa` | Static pressure at the test, in kilopascals. |
| `sigma_omc_db` | Operating-and-mounting standard deviation, in decibels. |
| `coverage_factor` | `k` of Formula (13), 2 by default. |

**Returns:** [`SpecialRoomSoundPowerResult`](/phonometry/reference/api/power/sound-power-special-room/#specialroomsoundpowerresult) with `method='comparison'`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels of an inadmissible shape, a reference spectrum of other bands, a background that fits neither source, frequencies outside Table F.1, a climate out of range, a negative `sigma_omc_db` or a coverage factor that is not positive. |

## special_room_background_correction

```python
special_room_background_correction(
    levels: ArrayLike,
    background_levels: ArrayLike,
) -> np.ndarray
```

The background correction of ISO 3743-2:2018 Table 4 (9.8).

The decibels to subtract from a level measured with the source operating
to leave the level of the source alone, read from the difference between
that level and the background level alone: 2 dB for a difference of 4 dB
or 5 dB, 1 dB for 6 dB to 8 dB, 0,5 dB for 9 dB and 10 dB, and nothing
for a difference above 10 dB.

The table gives whole decibels, and the difference is read at the nearest
whole decibel. A difference below 4 dB takes the 4 dB row and warns: the
accuracy is then reduced, and 9.8 allows the level to be reported only
with the statement that the background requirement was not fulfilled.
The informative Annex D treats the table as a rounding of
$-10 \lg (1 - 10^{-0{,}1 \Delta L_p})$; the normative text is the
table, and that is what is applied.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Levels measured with the source operating, in decibels. |
| `background_levels` | Background levels alone, broadcasting against `levels`, in decibels. |

**Returns:** The correction to subtract, in decibels, of the broadcast shape.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for non-finite or empty inputs, or shapes that do not broadcast. |

## special_room_source_locations

```python
special_room_source_locations(
    levels: ArrayLike,
    frequencies: ArrayLike,
    *,
    microphone_positions: int = 6,
    a_weighted_levels: ArrayLike | None = None,
) -> SourceLocationPlan
```

The number of source locations for a number of microphone positions,
from the survey of ISO 3743-2:2018, 9.4 (Table 3), and the spectral
character of 9.5.

At one source location, six microphone positions record the sound
pressure level (step 1), and per octave band and for A-weighting

$$
s_\mathrm{M} = (n - 1)^{-1/2} \left[ \sum_{i=1}^{n} \left(L_{pi} - \overline{L_p}\right)^2 \right]^{1/2} \tag{Formula 4}
$$

about the arithmetic mean when the six levels span no more than 5 dB and
about their energy mean (Formula 5) when they span more (step 2). Table 3
then gives the minimum number of source locations for 3, 6 or 12
microphone positions (step 3), by $s_\mathrm{M}$ class (below
2,3 dB, 2,3 dB to 4 dB, above 4 dB) and band. The same classes read the
spectrum (9.5): broad-band below 2,3 dB, narrow-band components possible
up to 4 dB, a discrete tone possible above; their suspected presence
shall be reported.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Survey levels, `(n, bands)`, six rows in 9.4, in decibels. |
| `frequencies` | Octave centres from 125 Hz to 8 kHz, ascending. |
| `microphone_positions` | The column of Table 3 to read, 3, 6 (default) or 12. |
| `a_weighted_levels` | The six A-weighted levels, `(n,)`, for the A-weighted row; `None` leaves it unevaluated. |

**Returns:** The [`SourceLocationPlan`](/phonometry/reference/api/power/sound-power-hard-walled/#sourcelocationplan).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels that are not a finite 2D array of at least two positions, bands outside 125 Hz to 8 kHz, a column Table 3 does not have, or A-weighted levels not one per position. |

## SpecialRoomReverberationCheck

```python
SpecialRoomReverberationCheck(
    frequencies: np.ndarray,
    reverberation_time_s: np.ndarray,
    reverberation_parameter: np.ndarray,
    nominal_reverberation_time_s: float,
    centred: bool,
    lower_limit: np.ndarray,
    upper_limit: np.ndarray,
    volume_m3: float,
    method: str,
    climate_product_change: float = nan,
    source_volume_m3: float = nan,
)
```

Qualification of a special reverberation test room by its
reverberation time, volume and climate (ISO 3743-2:2018, 6.2, 6.3, 6.6).

`reverberation_time_s` is the measured $T$ per band and
`reverberation_parameter` the $R$ of Formula (1) (or its NOTE);
`nominal_reverberation_time_s` is $T_\mathrm{nom}$, supplied or,
with `centred` `True`, found by centring the measured values within
the limiting curves. `lower_limit` and `upper_limit` are the bounds on
$T/(R\,T_\mathrm{nom})$, 0,9 and 1,1, or 0,8 and 1,2 above 6,3 kHz.
`volume_m3` is the room and `method` the determination it is being
qualified for, which decides whether the 300 m³ ceiling applies.
`climate_product_change` is the relative change of
$H(\theta + 5\ ^\circ\mathrm{C})$ between the reverberation
measurement and the test, `NaN` when the climates were not given.
`source_volume_m3` is the volume of the noise source to be tested in
the room, `NaN` when it was not given; clause 5 recommends at most 1 %
of the room, which `source_size_recommended` reads and
`passes` leaves out, the clause saying "should" where 6.2, 6.3 and
6.6 say "shall".

### SpecialRoomReverberationCheck.band_within

*property*

Per band, whether `T` lies within the limiting curves.

### SpecialRoomReverberationCheck.climate_stable

*property*

Whether $H(\theta + 5)$ stayed within ±10 % (6.6); `None`
when the climates were not given.

### SpecialRoomReverberationCheck.nominal_in_range

*property*

Whether $T_\mathrm{nom}$ is between 0,5 s and 1,0 s (6.3).

### SpecialRoomReverberationCheck.normalized_ratio

*property*

$T/(R\,T_\mathrm{nom})$ per band, which 6.3 bounds.

### SpecialRoomReverberationCheck.passes

*property*

Whether the room qualifies on every requirement that was evaluated
(6.2, 6.3 and 6.6); the recommendation of clause 5 on the size of the
source is read by `source_size_recommended` and left out.

### SpecialRoomReverberationCheck.plot()

```python
SpecialRoomReverberationCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $T/T_\mathrm{nom}$ within the limiting curves, laid out
as Figure B.3 of the standard, with the limits widening above the
6,3 kHz band as the text of 6.3 says (the figure widens them at
6,3 kHz already; see `docs/ERRATA.md`).

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the measured curve. |

**Returns:** The axes.

### SpecialRoomReverberationCheck.ratio_to_nominal

*property*

$T/T_\mathrm{nom}$ per band, the quantity Figure B.3 draws.

### SpecialRoomReverberationCheck.source_size_recommended

*property*

Whether the source is at most 1 % of the room, as clause 5
recommends; `None` when no source volume was given.

### SpecialRoomReverberationCheck.volume_large_enough

*property*

Whether the room is at least 70 m³ (6.2).

### SpecialRoomReverberationCheck.volume_small_enough

*property*

Whether the 300 m³ ceiling of 6.2 is kept where it applies.

It applies to the direct method when the 8 kHz octave, and with it the
4 kHz one, is within the measured range; the NOTE lifts it for the
comparison method.

## SpecialRoomSoundPowerResult

```python
SpecialRoomSoundPowerResult(
    frequencies: np.ndarray,
    sound_power_level: np.ndarray,
    mean_pressure_level: np.ndarray,
    background_correction: np.ndarray,
    background_requirement_met: np.ndarray,
    mean_reference_level: np.ndarray,
    reference_power_level: np.ndarray,
    volume_m3: float,
    nominal_reverberation_time_s: float,
    c2: float,
    sigma_r0: np.ndarray,
    sigma_r0_a: float,
    sigma_omc: float,
    coverage_factor: float,
    sound_power_level_a: float,
    sound_power_level_a_direct: float,
    mean_a_weighted_level: float,
    background_requirement_met_a: bool,
    method: str,
    microphone_positions: int,
    source_positions: int,
)
```

Result of an ISO 3743-2:2018 determination in a special reverberation
test room.

`method` is `'direct'` (Formula 9) or `'comparison'` (Formula 10).
`sound_power_level` is the octave-band $L_W$ at the
meteorological conditions of the test; the `..._ref` properties add the
Annex E correction `c2`, which 10.2 and 10.3 require above 500 m.

`mean_pressure_level` is the mean background-corrected level of the
source under test, $\overline{L_p}$ (Formula 8) or
$L_{p\mathrm{e}}$, and `background_correction` the per-band shift
the Table 4 corrections made to it. `background_requirement_met` is
`True` only where a background was measured and every margin, of the
source and, for the comparison method, of the reference source, reached
the 4 dB of 6.5 and 9.8. For the comparison method
`mean_reference_level` is $L_{p\mathrm{r}}$ and
`reference_power_level` $L_{W\mathrm{r}}$; for the direct method
both are `NaN` and `volume_m3` and `nominal_reverberation_time_s`
carry the room instead (`NaN` for the comparison method).

`sound_power_level_a` is the Annex F total of the octave bands;
`sound_power_level_a_direct` is Formula (9) applied to the mean
A-weighted level `mean_a_weighted_level`, which is how clause 4 reads
the A-weighted level of the direct method, both `NaN` where the
A-weighted levels were not measured or the method is the comparison one;
`background_requirement_met_a` is the 4 dB test of 6.5 on the
A-weighted levels, `False` where there was nothing to test.
`sigma_r0` is Table 5 per band (`NaN` at 63 Hz) and `sigma_r0_a` its
A-weighted row; the uncertainty properties follow Formulae (12) and (13).

### SpecialRoomSoundPowerResult.expanded_uncertainty

*property*

`U = k sigma_tot` per band (Formula 13), in decibels.

### SpecialRoomSoundPowerResult.expanded_uncertainty_a

*property*

`U` of the A-weighted level (Formula 13), in decibels: 5,7 dB for
`sigma_omc` = 2,0 dB and `k` = 2, the 11.5 EXAMPLE.

### SpecialRoomSoundPowerResult.plot()

```python
SpecialRoomSoundPowerResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the octave-band spectrum with the A-weighted total annotated.

A band whose background margin fell below 4 dB is hatched as not
meeting 9.8, and the expanded uncertainty is drawn as an error bar
where `sigma_omc` was given. Requires matplotlib
(`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the band bars. |

**Returns:** The axes.

### SpecialRoomSoundPowerResult.report()

```python
SpecialRoomSoundPowerResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render the ISO 3743-2 determination as a one-page test sheet.

The sheet states the method and its accuracy grade (the direct or the
comparison method in a special reverberation test room,
ISO 3743-2:2018, grade 2), an optional metadata header, the per-band
table of the mean level (and, for the comparison method, of the
reference sound source) and the determined `LW`, the spectrum, the
boxed A-weighted level with the expanded uncertainty and its coverage
factor, an optional verdict against a declared limit, and a basis strip
with Formula 8 and Formula 9 or 10. The boxed level of the direct
method is the one clause 4 describes, Formula (9) on the A-weighted
sound pressure levels, where they were measured; the Annex F total of
the octave bands is stated beside it. A band whose background
requirement was not met is marked `*` and named beneath the table,
as 9.8 asks.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata) for the header, the footer identity and, via `requirement`, a declared A-weighted limit the boxed level is checked against (lower is better). |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | When `True` the table adds the per-band shift of the Table 4 background corrections. |
| `language` | Sheet language: `"en"` (default) or `"es"`. |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"` or `language` is unknown. |
| ImportError | If reportlab (or, for the figure, matplotlib) is not installed (`pip install phonometry[report]`). |

### SpecialRoomSoundPowerResult.sigma_tot

*property*

Formula (12) per band, in decibels; `NaN` without `sigma_omc`.

### SpecialRoomSoundPowerResult.sigma_tot_a

*property*

Formula (12) with the A-weighted row of Table 5, in decibels.

### SpecialRoomSoundPowerResult.sound_power_level_a_ref

*property*

The Annex F total of `sound_power_level_ref`, `LWA + C2`.

### SpecialRoomSoundPowerResult.sound_power_level_ref

*property*

`LW + C2` under the reference meteorological conditions (E.1).

## SpecialRoomSuitabilityCheck

```python
SpecialRoomSuitabilityCheck(
    frequencies: np.ndarray,
    difference_db: np.ndarray,
    limit_db: np.ndarray,
)
```

The suitability evaluation of ISO 3743-2:2018, 6.7 (Table 1).

`difference_db` is, per octave band, the sound power level of a
calibrated broad-band reference source determined in the room less its
calibrated value, and `limit_db` the Table 1 bound on its magnitude.

### SpecialRoomSuitabilityCheck.band_within

*property*

Per band, whether the difference stays within Table 1.

### SpecialRoomSuitabilityCheck.passes

*property*

Whether the room is suitable for broad-band sources (step 4 of 6.7).

### SpecialRoomSuitabilityCheck.plot()

```python
SpecialRoomSuitabilityCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the difference per band within the ± Table 1 limits.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the difference bars. |

**Returns:** The axes.

## SpecialRoomSurfaceCheck

```python
SpecialRoomSurfaceCheck(
    frequencies: np.ndarray,
    surface_absorption: np.ndarray,
    floor_absorption: np.ndarray,
    mean_absorption: np.ndarray,
)
```

Qualification of a special reverberation test room by its surfaces
(ISO 3743-2:2018, 6.4).

`surface_absorption` holds the mean absorption coefficient of each wall
and of the ceiling per octave band, `(surfaces, bands)`,
`floor_absorption` that of the floor, and `mean_absorption` the mean of
the walls and ceiling that each is compared with, weighted by their areas
when those were given.

### SpecialRoomSurfaceCheck.floor_reflective

*property*

Per band, whether the floor absorbs less than 0,06.

### SpecialRoomSurfaceCheck.passes

*property*

Whether both criteria of 6.4 hold in every band.

### SpecialRoomSurfaceCheck.plot()

```python
SpecialRoomSurfaceCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each surface's coefficient within the 0,5 to 1,5 band of the
mean, and the floor against its 0,06, with every coefficient outside
6.4 ringed and the verdict in the title.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the surface curves. |

**Returns:** The axes.

### SpecialRoomSurfaceCheck.surface_ratio

*property*

Each wall's and the ceiling's coefficient over the mean, per band;
1 where the mean is zero, since every surface then absorbs alike.

### SpecialRoomSurfaceCheck.surface_within

*property*

Per wall or ceiling and band, `(surfaces, bands)`, whether the
coefficient lies within 0,5 and 1,5 times the mean.

### SpecialRoomSurfaceCheck.surfaces_uniform

*property*

Per band, whether every wall and the ceiling lie within 0,5 and 1,5
times the mean.

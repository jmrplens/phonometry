---
title: "emission.sound_power_hard_walled"
description: "Sound power and sound energy levels of a small movable source in a hard-walled test room, by comparison with a reference sound source: ISO 3743-1:2010 (engineering grade 2)."
sidebar:
  label: "sound_power_hard_walled"
---

Sound power and sound energy levels of a small movable source in a
hard-walled test room, by comparison with a reference sound source:
ISO 3743-1:2010 (engineering grade 2).

The room is an ordinary one: nearly empty, with smooth hard walls, no
surface anywhere absorbing more than 0,20 of the incident power (4.3), at
least 40 m³ and forty times the reference box (4.2). Such a room is not
diffuse enough to be read on its own the way ISO 3741 reads a qualified
reverberation room, so the room is not modelled at all: a calibrated
reference sound source (RSS) stands where the source under test (ST) stood
and the same microphones listen to both. The room then drops out of the
difference, and the octave-band sound power level of the source is the
calibrated power of the reference carried across by the difference of the
two mean levels, each corrected for background noise (8.1.4):

$$
L_W = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}} + \overline{L'_{p(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1 \tag{Eq. 14}
$$

The mean levels are energy averages over the $N_\mathrm{M}$ microphone
positions or traverses (Eq. 10, 11, 12), and when the preliminary survey of
7.4 asked for more than one source location the levels at each position are
first energy-averaged over the $N_\mathrm{S}$ locations (Eq. 9).

Unlike ISO 3741 and ISO 3747, the background correction is taken once per
band from the two *means*, not position by position (8.1.3):

$$
K_1 = -10 \log_{10}\!\left(1 - 10^{-0.1\,\Delta L_p}\right), \qquad \Delta L_p = \overline{L'_{p(\mathrm{ST})}} - \overline{L_{p(\mathrm{B})}} \tag{Eq. 13}
$$

with three rules around it: above 15 dB there is nothing to correct, from
6 dB to 15 dB Eq. (13) applies, and below 6 dB the correction is fixed at
1,3 dB, "the value for $\Delta L_p$ = 6 dB", and the band becomes an
upper bound that the report has to flag. The same rule gives
$K_{1(\mathrm{RSS})}$ from the reference source's mean, but a band
where it is the reference source's margin that falls short is no upper bound:
$K_{1(\mathrm{RSS})}$ enters Eq. (14) with a plus sign, so the capped
correction pulls $L_W$ down, not up. 8.1.3 gives the upper-bound
reading to the margin of the source under test alone, and such a band only
fails the background requirement of 4.5, which is all the library says of it.

A source that emits bursts has a sound energy level instead (8.2): the
single event levels of each position are reduced to the level of one event
(Eq. 15 or Eq. 16), averaged over the source locations (Eq. 17) and the
positions (Eq. 18), corrected by the same rule (Eq. 19), and

$$
L_J = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}} + \overline{L'_{E(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1 \tag{Eq. 20}
$$

Eq. (19) subtracts a time-averaged background level from a time-integrated
event level, exactly as ISO 3744:2010 Eq. (21) does, and asks only that both
be measured over one integration time $T$. The library reads the
background as its exposure over that $T$, $L_{p(\mathrm{B})} + 10 \log_{10}(T/T_0)$, which is the reading under which the insistence on one
$T$ does any work (see `docs/ERRATA.md`), so `integration_time_s` is
required with a background.

Annex A carries either level to the reference meteorological conditions of
101,325 kPa and 23,0 °C with the radiation-impedance correction
$C_2 = -10 \log_{10}(p_\mathrm{s}/p_{\mathrm{s},0}) + 15 \log_{10} [(273{,}15 + \theta)/\theta_1]$, $\theta_1$ = 296 K, the expression
ISO 3741:2010 and ISO 3747:2010 print digit for digit; the static pressure
follows from the altitude by Eq. (A.2), which is ISO 3747:2010 Eq. (C.2)
([`static_pressure_from_altitude`](/phonometry/reference/api/power/sound-power-in-situ/#static_pressure_from_altitude)). The correction
is required above 500 m (8.1.4). Annex B forms the A-weighted totals from the
octave bands with the Table B.1 corrections, which are ISO 3744:2010 Table E.2
digit for digit, 63 Hz row included under its footnote.

Clause 9 estimates the uncertainty as $\sigma_\mathrm{tot} = \sqrt{\sigma_{R0}^2 + \sigma_\mathrm{omc}^2}$ (Eq. 22) and $U = k\,\sigma_\mathrm{tot}$ (Eq. 23), with $k$ = 2 (9.5), and Table 3 gives
the typical upper bound of $\sigma_{R0}$ per octave band: 3,0 dB at
125 Hz, 2,0 dB at 250 Hz, 1,5 dB from 500 Hz to 4 kHz, 2,5 dB at 8 kHz and
1,5 dB for the A-weighted level of a flat spectrum. The middle row of the
printed table reads "400 to 5 000" under an octave heading, which is a
one-third-octave range; the library reads it as the four octaves it spans
(see `docs/ERRATA.md`).

The room itself is qualified in three steps, which
[`check_hard_walled_room`](/phonometry/reference/api/power/sound-power-hard-walled/#check_hard_walled_room) evaluates together: its volume against the
reference box (4.2), the absorption of its surfaces (4.3), and the acoustic
adequacy of 4.4, eight mean octave levels of a highly directional source
turned through four horizontal and four vertical orientations, whose largest
spread in each band from 125 Hz to 8 kHz may not exceed the Table 3 value.
The preliminary survey of 7.4, six microphone positions whose standard
deviation decides how many source locations the determination needs
(Table 2), is [`hard_walled_source_locations`](/phonometry/reference/api/power/sound-power-hard-walled/#hard_walled_source_locations).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_hard_walled_room

```python
check_hard_walled_room(
    orientation_levels: ArrayLike,
    frequencies: ArrayLike,
    *,
    volume_m3: float,
    reference_box_m: ArrayLike,
    absorption_coefficients: ArrayLike | None = None,
) -> HardWalledRoomCheck
```

Is this room a hard-walled test room? ISO 3743-1:2010, 4.2 to 4.4.

The acoustic criterion of 4.4 turns a highly directional broadband source,
directivity index at least 5 dB above 500 Hz, through four horizontal and
four vertical orientations, each time taking the mean background-corrected
octave level over the microphone positions. The room suits the method if
in every band from 125 Hz to 8 kHz the largest difference between any two
of the eight means stays within the standard deviation of reproducibility
of Table 3. The NOTE allows a source of the type to be tested in place of
the directional one, which then qualifies the room for that type only.

4.2 adds the size: at least 40 m³ and forty times the reference box, whose
largest dimension is at most 1,0 m in a room of up to 100 m³ and 2,0 m in
a larger one. 4.3 adds the surfaces: no portion of any boundary absorbing
more than 0,20 at any frequency of interest; Table 1 describes the rooms
that meet it in words, and the coefficients are optional here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `orientation_levels` | Mean octave-band levels of the directional source, one row per orientation (eight in 4.4), `(orientations, bands)`, in decibels. |
| `frequencies` | Nominal octave mid-band frequencies from 125 Hz to 8 kHz, one per band, ascending. |
| `volume_m3` | Volume of the test room, in cubic metres. |
| `reference_box_m` | The three dimensions of the reference box, in metres (4.1). |
| `absorption_coefficients` | Sound absorption coefficients of the boundary surfaces, any shape (per surface and per band, say); only the largest is read. `None` leaves 4.3 unevaluated. |

**Returns:** The verdict, as a [`HardWalledRoomCheck`](/phonometry/reference/api/power/sound-power-hard-walled/#hardwalledroomcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels that are not a finite 2D array of at least two orientations, frequencies outside 125 Hz to 8 kHz, a non-positive volume or box dimension, or an absorption coefficient outside [0, 1]. |

## hard_walled_source_locations

```python
hard_walled_source_locations(
    levels: ArrayLike,
    frequencies: ArrayLike,
) -> SourceLocationPlan
```

The number of source locations from the preliminary survey of
ISO 3743-1:2010, 7.4 (Table 2).

For a source with audible discrete tones or narrow bands of noise, at
least six fixed microphone positions record the uncorrected level of the
source under test, and their standard deviation per band

$$
s_\mathrm{M} = \left[ \frac{1}{N_\mathrm{M(pre)} - 1} \sum_{i=1}^{N_\mathrm{M(pre)}} \left( L'_{pi(\mathrm{pre})} - \overline{L'_{p(\mathrm{pre})}} \right)^2 \right]^{1/2} \tag{Eq. 7}
$$

about their arithmetic mean (Eq. 8) decides the number of source
locations: one up to 2,5 dB, two in the same room up to 4,0 dB, and above
that two in the same room plus two more in another room of different
dimensions that still complies with 4.4.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Preliminary levels, `(NM, bands)` with at least six rows, in decibels. |
| `frequencies` | Nominal octave mid-band frequencies, one per band. |

**Returns:** The [`SourceLocationPlan`](/phonometry/reference/api/power/sound-power-hard-walled/#sourcelocationplan).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels that are not a finite 2D array of at least two positions, or frequencies that are not octave centres. |

## HardWalledRoomCheck

```python
HardWalledRoomCheck(
    frequencies: np.ndarray,
    level_range_db: np.ndarray,
    limit_db: np.ndarray,
    orientations: int,
    volume_m3: float,
    reference_box_volume_m3: float,
    largest_box_dimension_m: float,
    minimum_volume_m3: float,
    box_dimension_limit_m: float,
    max_absorption_coefficient: float,
    minimum_microphone_distance_m: float,
)
```

Qualification of a hard-walled test room (ISO 3743-1:2010, 4.2 to 4.4).

`level_range_db` is, per octave band, the largest difference between
the mean levels of any two of the directional source's orientations
(4.4), and `limit_db` the Table 3 value it may not exceed.
`volume_m3` is the room, `reference_box_volume_m3` and
`largest_box_dimension_m` the reference box of 4.1, and
`minimum_volume_m3` / `box_dimension_limit_m` what 4.2 asks of them.
`max_absorption_coefficient` is the largest sound absorption coefficient
of any portion of the boundary surfaces, `NaN` when none was supplied,
against the 0,20 of 4.3. `minimum_microphone_distance_m` is the
$d_\mathrm{min} = 0{,}3\,V^{1/3}$ of 7.3 that keeps the microphones
in the reverberant field, stated for the setup rather than judged.

### HardWalledRoomCheck.acoustically_adequate

*property*

The 4.4 criterion: every band within Table 3.

### HardWalledRoomCheck.band_adequate

*property*

Per band, whether the spread stays within Table 3 (4.4).

### HardWalledRoomCheck.box_fits

*property*

The size criterion of 4.2 on the largest reference-box dimension.

### HardWalledRoomCheck.passes

*property*

Whether the room qualifies on every criterion that was evaluated.

### HardWalledRoomCheck.plot()

```python
HardWalledRoomCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the orientation spread per band against the Table 3 limit.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the spread bars. |

**Returns:** The axes.

### HardWalledRoomCheck.surfaces_hard

*property*

The 4.3 criterion, `None` when no absorption was supplied.

### HardWalledRoomCheck.volume_adequate

*property*

The volume criterion of 4.2: at least 40 m³ and 40 reference boxes.

Both volumes are rounded to nine decimal places before they are
compared: forty times a box measured in decimal metres can come out a
last bit above a room volume that equals it, and 4.2 asks for "at
least".

## HardWalledSoundPowerResult

```python
HardWalledSoundPowerResult(
    frequencies: np.ndarray,
    sound_power_level: np.ndarray,
    sound_energy_level: np.ndarray,
    mean_source_level: np.ndarray,
    mean_reference_level: np.ndarray,
    mean_background_level: np.ndarray,
    reference_power_level: np.ndarray,
    background_correction: np.ndarray,
    background_correction_ref: np.ndarray,
    background_requirement_met: np.ndarray,
    upper_bound: np.ndarray,
    c2: float,
    sigma_r0: np.ndarray,
    sigma_r0_a: float,
    sigma_omc: float,
    coverage_factor: float,
    sound_power_level_a: float,
    sound_energy_level_a: float,
    quantity: str,
    microphone_positions: int,
    source_positions: int,
)
```

Result of an ISO 3743-1:2010 determination in a hard-walled test room.

`quantity` says which of the two determinations this is: `'power'`
carries the octave-band sound power level `LW` (Eq. 14) in
`sound_power_level` with `sound_energy_level` all `NaN`, and
`'energy'` the sound energy level `LJ` (Eq. 20) in
`sound_energy_level` with `sound_power_level` all `NaN`. Both are at
the meteorological conditions of the test; the `..._ref` properties add
the Annex A correction `c2`, which 8.1.4 requires above 500 m.

`mean_source_level` is the uncorrected mean level of the source under
test, $\overline{L'_{p(\mathrm{ST})}}$ (Eq. 10) or
$\overline{L'_{E(\mathrm{ST})}}$ (Eq. 18), and
`mean_reference_level` that of the reference sound source,
$\overline{L'_{p(\mathrm{RSS})}}$ (Eq. 11); `mean_background_level`
is $\overline{L_{p(\mathrm{B})}}$ (Eq. 12), `NaN` where no
background was measured, and `reference_power_level` the calibrated
$L_{W(\mathrm{RSS})}$. `background_correction` and
`background_correction_ref` are $K_1$ and
$K_{1(\mathrm{RSS})}$ per band, and `background_requirement_met`
is `True` only where a background was measured and both margins reached
the 6 dB of 4.5. `upper_bound` marks the bands that 8.1.3 calls upper
bounds: the margin of the source under test was measured and fell below
6 dB while the reference source's margin met it, so the capped
$K_1$ leaves the level too high. A band where the reference source's
margin falls short is not one: the capped $K_{1(\mathrm{RSS})}$
pulls the level down, so it is flagged by `background_requirement_met`
alone, and so is every band when no background was measured.

`sigma_r0` is the Table 3 value per band (`NaN` at 63 Hz, which the
table does not reach) and `sigma_r0_a` its A-weighted row; with
`sigma_omc` the properties give `sigma_tot` (Eq. 22) and the expanded
uncertainty (Eq. 23) for `coverage_factor`, all `NaN` without it.
`microphone_positions` is $N_\mathrm{M}$ (1 for a traverse),
`source_positions` is $N_\mathrm{S}$, and
`sound_power_level_a` / `sound_energy_level_a` are the Annex B totals
of the level that was determined (`NaN` for the other).

### HardWalledSoundPowerResult.expanded_uncertainty

*property*

`U = k sigma_tot` per band (Eq. 23), in decibels.

### HardWalledSoundPowerResult.expanded_uncertainty_a

*property*

`U = k sigma_tot` of the A-weighted level (Eq. 23), in decibels.

With `sigma_omc` = 2,0 dB and `k` = 2 this is the 5 dB of the 9.5
EXAMPLE.

### HardWalledSoundPowerResult.plot()

```python
HardWalledSoundPowerResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the determined spectrum with the A-weighted total annotated.

One bar per octave band of `LW` (or `LJ`), a band that 8.1.3 makes
an upper bound hatched and named as one, a band that fails the
background requirement of 4.5 otherwise cross-hatched and named as
that, and the expanded uncertainty as an error bar where `sigma_omc`
was given. Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the band bars. |

**Returns:** The axes.

### HardWalledSoundPowerResult.report()

```python
HardWalledSoundPowerResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render the ISO 3743-1 determination as a one-page test sheet.

The sheet states the method and its accuracy grade (the comparison
with a reference sound source in a hard-walled test room,
ISO 3743-1:2010, grade 2), an optional metadata header, the per-band
table of the mean level of the source, the mean level and the
calibrated sound power level of the reference sound source and the
determined `LW` (or `LJ`), the spectrum, the boxed A-weighted level
with the expanded uncertainty and its coverage factor, an optional
verdict against a declared limit, and a basis strip with the Eq. 14
(or Eq. 20) chain and its corrections. A band that is an upper bound
is marked `*` and named one beneath the table, with the background
requirement not fulfilled, which 8.1.3 asks a report to state in its
tables; any other band whose background requirement was not met is
marked `†` and named as not fulfilling it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata) for the header (`client`, `specimen` the noise source, `test_room`, `instrumentation`, the climate and `test_date`), the footer identity and, via `requirement`, a declared A-weighted limit the result is checked against (lower is better). |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | When `True` the table adds the mean background level and the background corrections `K1` and `K1(RSS)`. |
| `language` | Sheet language: `"en"` (default) or `"es"`. |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"` or `language` is unknown. |
| ImportError | If reportlab (or, for the figure, matplotlib) is not installed (`pip install phonometry[report]`). |

### HardWalledSoundPowerResult.sigma_tot

*property*

$\sigma_\mathrm{tot} = \sqrt{\sigma_{R0}^2 + \sigma_\mathrm{omc}^2}$ per band (Eq. 22), in decibels; `NaN` without
`sigma_omc` and at 63 Hz.

### HardWalledSoundPowerResult.sigma_tot_a

*property*

Eq. (22) with the A-weighted row of Table 3, in decibels.

### HardWalledSoundPowerResult.sound_energy_level_a_ref

*property*

The A-weighted total of `sound_energy_level_ref` (Eq. B.2).

### HardWalledSoundPowerResult.sound_energy_level_ref

*property*

`LJ + C2` under the reference meteorological conditions (Eq. A.3);
`NaN` for a power determination.

### HardWalledSoundPowerResult.sound_power_level_a_ref

*property*

The A-weighted total of `sound_power_level_ref`.

`C2` is the same in every band, so it passes through Eq. (B.1)
unchanged: the total moves by `C2` too.

### HardWalledSoundPowerResult.sound_power_level_ref

*property*

`LW + C2` under the reference meteorological conditions (Eq. A.1);
`NaN` for an energy determination.

## reproducibility_from_round_robin

```python
reproducibility_from_round_robin(
    total_db: float,
    operating_db: float,
) -> float
```

The standard deviation of reproducibility of the method from a round
robin test (ISO 3743-1:2010 Eq. 24).

$$
\sigma'_{R0} = \sqrt{\sigma'^2_\mathrm{tot} - \sigma'^2_\mathrm{omc}}
$$

A round robin gives the total standard deviation $\sigma'_\mathrm{tot}$
of one source, which still carries the instability of that source's
operating and mounting conditions; taking it out in quadrature leaves
what the method itself contributes. ISO 3743-2:2018 prints the same
relation as its Formula (14) with a plus sign, which would make the
method's share larger than the total it is extracted from; the sentence
after it (the result is imprecise when $\sigma_\mathrm{tot}$ is only
slightly higher than $\sigma_\mathrm{omc}$) holds only for the
difference, and the library evaluates the difference for both parts (see
`docs/ERRATA.md`).

The clause adds a condition on the inputs: to keep the result from being
a small number of low accuracy, $\sigma_\mathrm{omc}$ should not
exceed $\sigma_\mathrm{tot}/\sqrt{2}$. Beyond it this warns; the
value is still returned.

**Parameters**

| Name | Description |
| :--- | :--- |
| `total_db` | $\sigma'_\mathrm{tot}$ of the round robin, in decibels. |
| `operating_db` | $\sigma'_\mathrm{omc}$ of the source used in it, in decibels. |

**Returns:** $\sigma'_{R0}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if either is negative or not finite, or `operating_db` exceeds `total_db`, which no round robin can produce. |

## sound_energy_hard_walled

```python
sound_energy_hard_walled(
    event_levels: ArrayLike,
    levels_ref: ArrayLike,
    lw_ref: ArrayLike,
    frequencies: ArrayLike,
    *,
    events: int | None = None,
    background_levels: ArrayLike | None = None,
    integration_time_s: float | None = None,
    background_levels_ref: ArrayLike | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    sigma_omc_db: float | None = None,
    coverage_factor: float = 2.0,
) -> HardWalledSoundPowerResult
```

Sound energy level of a source emitting bursts, in a hard-walled test
room, by comparison with a reference sound source (ISO 3743-1:2010, 8.2).

The single event levels come in one of the two forms 7.6 admits. Measured
one event at a time, the $N_\mathrm{e}$ events are on the first axis
and Eq. (15) takes their energy mean; measured once over
$N_\mathrm{e}$ successive events, Eq. (16) subtracts
$10 \log_{10} N_\mathrm{e}$. The level of one event is then
averaged over the source locations (Eq. 17) and the positions (Eq. 18),
corrected by the rule of 8.2.3 around Eq. (19), and

$$
L_J = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}} + \overline{L'_{E(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1 \tag{Eq. 20}
$$

The reference source is steady and measured time-averaged over 30 s
(7.6), so $K_{1(\mathrm{RSS})}$ follows 8.1.3 unchanged. For a
source steady over the interval $T$ this gives
$L_J = L_W + 10 \log_{10}(T/T_0)$, $T_0$ = 1 s (3.4 NOTE 1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `event_levels` | Measured (uncorrected) octave-band single event levels, in decibels. With `events` `None`: `(Ne, bands)` for a traverse, `(Ne, NM, bands)` or `(Ne, NS, NM, bands)`, one entry per event on the first axis (Eq. 15). With `events`: `(bands,)`, `(NM, bands)` or `(NS, NM, bands)`, one measurement encompassing `events` events (Eq. 16). |
| `levels_ref` | Time-averaged levels of the reference sound source, `(NM, bands)` or `(bands,)`, as in [`sound_power_hard_walled`](/phonometry/reference/api/power/sound-power-hard-walled/#sound_power_hard_walled). |
| `lw_ref` | Calibrated sound power level of the reference source, `(bands,)`, in decibels. |
| `frequencies` | Nominal octave mid-band frequencies, one per band. |
| `events` | The number $N_\mathrm{e}$ of events one measurement encompasses (Eq. 16); `None` when the events are on the first axis. Fewer than five warns (7.6). |
| `background_levels` | Time-averaged background levels `Lpi(B)`, `(NM, bands)` or `(bands,)`, in decibels; requires `integration_time_s`. `None` applies no correction, warns and leaves `background_requirement_met` `False` throughout. |
| `integration_time_s` | The integration time `T` of the single event levels, in seconds. The background is compared as its exposure over the same `T`, $L_{p(\mathrm{B})} + 10 \log_{10}(T/T_0)$, so that Eq. (19) subtracts one energy from another. |
| `background_levels_ref` | Background for the reference-source measurement; `None` reuses `background_levels`, compared with the time-averaged reference level as it stands. |
| `temperature_c` | Air temperature at the test, in degrees Celsius. |
| `static_pressure_kpa` | Static pressure at the test, in kilopascals. |
| `sigma_omc_db` | Operating-and-mounting standard deviation, in decibels. |
| `coverage_factor` | `k` of Eq. (23), 2 by default. |

**Returns:** [`HardWalledSoundPowerResult`](/phonometry/reference/api/power/sound-power-hard-walled/#hardwalledsoundpowerresult) with `quantity='energy'`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an `event_levels` rank neither form admits, a non-integer or non-positive `events`, a background without its `integration_time_s`, a non-positive `integration_time_s`, or any refusal of [`sound_power_hard_walled`](/phonometry/reference/api/power/sound-power-hard-walled/#sound_power_hard_walled). |

## sound_power_hard_walled

```python
sound_power_hard_walled(
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
) -> HardWalledSoundPowerResult
```

Sound power level of a small movable source in a hard-walled test room,
by comparison with a reference sound source (ISO 3743-1:2010, 8.1).

The octave-band time-averaged levels of the source under test are
energy-averaged over the source locations, if the survey of 7.4 asked for
more than one (Eq. 9), and over the microphone positions (Eq. 10); those of
the reference source, placed where the source under test stood (7.2), over
the same positions (Eq. 11), and the background likewise (Eq. 12). Each
mean is corrected for background noise by the rule of 8.1.3 around
Eq. (13), and

$$
L_W = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}} + \overline{L'_{p(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1 \tag{Eq. 14}
$$

at the meteorological conditions of the test; `sound_power_level_ref`
adds the Annex A correction and `sound_power_level_a` is the Annex B
total.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Measured (uncorrected) octave-band time-averaged levels of the source under test, in decibels: `(bands,)` for one microphone traverse (NOTE to 8.1.2), `(NM, bands)` for fixed positions, or `(NS, NM, bands)` for several source locations (Eq. 9). |
| `levels_ref` | The same for the reference sound source at the same microphone positions, `(NM, bands)`, or its traverse level `(bands,)`. |
| `lw_ref` | Calibrated octave-band sound power level of the reference source `LW(RSS)`, `(bands,)`, in decibels. |
| `frequencies` | Nominal octave mid-band frequencies, one per band, ascending, from 125 Hz to 8 kHz; 63 Hz is accepted where the room and the instrumentation are satisfactory there (3.11, Table B.1 footnote). |
| `background_levels` | Octave-band background levels `Lpi(B)`, `(NM, bands)` or one averaged `(bands,)` spectrum, in decibels. `None` applies no correction, warns and leaves `background_requirement_met` `False` throughout (4.5, 7.5). |
| `background_levels_ref` | Background for the reference-source measurement, same shapes; `None` reuses `background_levels`. |
| `temperature_c` | Air temperature at the test, in degrees Celsius. |
| `static_pressure_kpa` | Static pressure at the test, in kilopascals (Eq. A.2 gives it from the altitude, [`static_pressure_from_altitude`](/phonometry/reference/api/power/sound-power-in-situ/#static_pressure_from_altitude)). |
| `sigma_omc_db` | Standard deviation of the operating and mounting conditions of the source (9.2, Eq. C.1), in decibels; `None` leaves `sigma_tot` and the expanded uncertainty `NaN`. |
| `coverage_factor` | `k` of Eq. (23), 2 by default as 9.5 prescribes; 1,6 for a one-sided comparison with a limit (9.1). |

**Returns:** [`HardWalledSoundPowerResult`](/phonometry/reference/api/power/sound-power-hard-walled/#hardwalledsoundpowerresult) with `quantity='power'`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a level array is not finite or of an admissible shape, the reference or background levels do not match the source's positions and bands, `frequencies` are not distinct ascending octave centres of Table B.1, the climate is out of range, `sigma_omc_db` is negative, or `coverage_factor` is not positive. |

## SourceLocationPlan

```python
SourceLocationPlan(
    standard: str,
    frequencies: np.ndarray,
    standard_deviation_db: np.ndarray,
    source_locations: np.ndarray,
    additional_room_locations: np.ndarray,
    microphone_positions: int,
    spectral_character: tuple[str, ...] | None = None,
    a_weighted_standard_deviation_db: float = nan,
    a_weighted_source_locations: int = 0,
    a_weighted_spectral_character: str | None = None,
)
```

How many source locations a determination needs, from a preliminary
survey of the room (ISO 3743-1:2010 7.4, Table 2; ISO 3743-2:2018 9.4,
Table 3).

`standard_deviation_db` is the estimated standard deviation
$s_\mathrm{M}$ of the preliminary levels per band, and
`source_locations` the minimum number $N_\mathrm{S}$ of source
locations its table asks for, in the same room. Part 1 sends a band above
4 dB to a second room as well: `additional_room_locations` counts the
locations there, two in such a band and zero elsewhere, and always zero
for Part 2. `microphone_positions` is the $N_\mathrm{M}$ the
numbers are read for: the preliminary positions of Part 1, the column of
Part 2's Table 3.

`spectral_character` is Part 2's 9.5 reading of $s_\mathrm{M}$ per
band, `'broadband'`, `'narrow-band'` or `'discrete tone'`, and
`None` for Part 1, which draws no such conclusion. The `a_weighted_...`
fields are the same for the A-weighted row of Part 2 when A-weighted
levels were surveyed, `NaN`, 0 and `None` otherwise.

### SourceLocationPlan.other_room_required

*property*

Whether a band of Part 1 sends the determination to a second room.

### SourceLocationPlan.plot()

```python
SourceLocationPlan.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $s_\mathrm{M}$ per band against the table's class limits,
with the number of source locations over each bar.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the standard-deviation bars. |

**Returns:** The axes.

### SourceLocationPlan.required_source_locations

*property*

The largest $N_\mathrm{S}$ any band (or the A-weighted row)
asks for in the test room, which is the number a single determination
covering them all has to use.

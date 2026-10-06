---
title: "hearing.earmuff_insertion_loss"
description: "The insertion loss of an earmuff on an acoustic test fixture (ISO 4869-3:2007)."
sidebar:
  label: "earmuff_insertion_loss"
---

The insertion loss of an earmuff on an acoustic test fixture (ISO 4869-3:2007).

ISO 4869-3 measures an earmuff without a listener. The acoustic test fixture
(ATF) is a metal cylinder of 135 mm diameter with its end faces 145 mm apart,
a pressure microphone flush with one of them and a spacer that carries the
headband (5.1). In a random-incidence field or a plane progressive wave, the
level at the microphone is measured without the earmuff and again with it
seated on the fixture, and the difference in each one-third-octave band is
the insertion loss (3.5, 5.4.2):

$$
IL_f = L_{\mathrm{open},f} - L_{\mathrm{occl},f}
$$

in bands from at least 63 Hz to 8 kHz (5.3), from at least three fittings
unless the device's repeatability is known (5.4.3), reported to the nearest
0,1 dB and drawn with increasing values downwards (Clause 6).

**What it is for, and what it is not (Clause 1).** The method checks
production spreads for type approval or certification and the change of
performance with age, and makes sure the samples sent for the subjective
test of ISO 4869-1 are typical of their type. It is not the basic type test,
and its data "are not intended to be quoted as representing the real-ear
sound attenuation of an ear-muff, nor the protection provided by the
ear-muff"; the Introduction adds that its results are not those of
ISO 4869-1. So [`EarmuffInsertionLossResult`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#earmuffinsertionlossresult) is not an input of
[`phonometry.hearing.assumed_protection_value`](/phonometry/reference/api/hearing/hearing-protectors/#assumed_protection_value),
[`phonometry.hearing.hml_rating`](/phonometry/reference/api/hearing/hearing-protectors/#hml_rating) or
[`phonometry.hearing.snr_rating`](/phonometry/reference/api/hearing/hearing-protectors/#snr_rating): those take the real-ear attenuation of
sixteen subjects, [`phonometry.hearing.real_ear_attenuation`](/phonometry/reference/api/hearing/real-ear-attenuation/), and
nothing here converts one into the other.

**The test site (5.1.4, 5.2).** [`check_random_incidence_field`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#check_random_incidence_field) judges
the random-incidence field of 5.2.2 with the diffuse-field judgement of
ISO 8253-2:2009, 5.3, and this standard's Table 1
([`RANDOM_INCIDENCE_VARIATION_LIMITS`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#random_incidence_variation_limits)); Annex A notes that the ATF
itself may serve as the directional microphone where its front-to-random
index, [`ATF_FRONT_TO_RANDOM_INDEX_DB`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#atf_front_to_random_index_db), reaches 4 dB.
[`check_plane_progressive_wave`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#check_plane_progressive_wave) judges the plane wave of 5.2.3, and
[`verify_fixture_isolation`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#verify_fixture_isolation) the acoustic isolation of the fixture with
its isolation cup (5.1.4).

**The uncertainty (Annex B).** The insertion loss is modelled as the two
levels plus three zero-mean inputs for the fixture, the sound field and the
equipment (Formula (B.1)), all normal with a sensitivity coefficient of 1,
so

$$
u = \sqrt{\sum_i (c_i u_i)^2}, \qquad U = 2u
$$

(Formula (B.2)). The standard uncertainty of each level is the standard
deviation of the mean of the repeated measurements; Table B.1 prints typical
values, 0,5 dB open, 1,0 dB occluded, 0,3 dB, 0,5 dB and 0,2 dB, which give
$u$ = 1,3 dB and $U$ = 2,6 dB
([`EARMUFF_INSERTION_LOSS_UNCERTAINTY`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#earmuff_insertion_loss_uncertainty)).

Clause, table and formula numbers refer to ISO 4869-3:2007(E).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ATF_FRONT_TO_RANDOM_INDEX_DB

*Constant* (`mapping`).

```python
ATF_FRONT_TO_RANDOM_INDEX_DB = {500.0: 1.7, 630.0: 2.2, 800.0: 2.8, 1000.0: 3.2, 1250.0: 4.6, 1600.0: 4.6, 2000.0: 6.3, 2500.0: 6.5, 3150.0: 5.9, 4000.0: 2.9, 5000.0: -0.6, 6300.0: 5.1, 8000.0: 5.9}
```

## check_plane_progressive_wave

```python
check_plane_progressive_wave(
    end_face_levels_db: ArrayLike,
    *,
    facing_levels_db: ArrayLike | None = None,
    facing_away_levels_db: ArrayLike | None = None,
    front_to_rear_index_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> PlaneProgressiveWaveCheck
```

Is the plane progressive wave of the test site good enough? (5.2.3).

With the fixture removed:

- the levels at the two points the centres of the fixture's end faces
  normally occupy, each read at 0° incidence, differ by 2 dB at most;
- from the 500 Hz band up, a directional microphone at the reference point
  reads at least 10 dB more facing the source than turned 180° away from
  it, the microphone having a front-to-rear sensitivity index greater
  than 15 dB (different microphones may serve different bands).

During the insertion loss measurement the fixture is turned so that the
wave meets its end faces at grazing incidence; that is its orientation,
not a condition judged here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `end_face_levels_db` | The levels at the two end-face points, a `(2, bands)` grid in dB. |
| `facing_levels_db` | The directional microphone's level facing the source per band, in dB; bands below 500 Hz may be NaN. |
| `facing_away_levels_db` | Its level facing away, per band, in dB. |
| `front_to_rear_index_db` | The microphone's front-to-rear sensitivity index, one number or one per band, in dB. |
| `frequencies` | The centre frequencies, in hertz, or `None` for the 22 bands of 63 Hz to 8 kHz. |

**Returns:** [`PlaneProgressiveWaveCheck`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#planeprogressivewavecheck). Without the directional readings the directional test is not judged and the verdict does not pass.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an end-face grid that is not two rows of finite levels, directional readings given in part, or arrays that do not match. |

## check_random_incidence_field

```python
check_random_incidence_field(
    position_levels_db: Mapping[str, ArrayLike],
    reference_levels_db: ArrayLike,
    *,
    directional_levels_db: ArrayLike | None = None,
    front_to_random_index_db: ArrayLike | None = None,
    frequencies: ArrayLike | None = None,
) -> DiffuseSoundFieldCheck
```

Is the random-incidence field of the test site good enough? (5.2.2).

With the fixture removed, the level read by an omnidirectional microphone
kept in one orientation at six positions 150 mm from the reference point,
on the front-back, right-left and up-down axes, stays within ±2,5 dB of
the level at the reference point, and the right and left positions within
3 dB of each other; from the 500 Hz band up, the levels a directional
microphone reads at the reference point in any two directions, the
directions of the extremes among them, stay within the variation Table 1
allows for its front-to-random sensitivity index
([`RANDOM_INCIDENCE_VARIATION_LIMITS`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#random_incidence_variation_limits)).

This is the diffuse-field judgement of ISO 8253-2:2009, 5.3, with this
standard's Table 1, and it returns the same
[`DiffuseSoundFieldCheck`](/phonometry/reference/api/hearing/sound-field-audiometry/#diffusesoundfieldcheck). The fixture itself
may be the directional microphone in the bands where its index
([`ATF_FRONT_TO_RANDOM_INDEX_DB`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#atf_front_to_random_index_db)) reaches 4 dB; pass the index band
by band, NaN where it has none, and the bands it cannot judge are left
unjudged.

**Parameters**

| Name | Description |
| :--- | :--- |
| `position_levels_db` | The level at each position per band, in dB, keyed `"front"`, `"back"`, `"left"`, `"right"`, `"up"` and `"down"`. |
| `reference_levels_db` | The level at the reference point per band, in dB. |
| `directional_levels_db` | The directional microphone's readings at the reference point, a `(directions, bands)` grid in dB; bands below 500 Hz are not read and may be NaN. `None` leaves the directional test unjudged, and the verdict then does not pass. |
| `front_to_random_index_db` | The directional microphone's front-to-random sensitivity index, in dB, one number or one per band; required with `directional_levels_db`. |
| `frequencies` | The centre frequencies, in hertz, or `None` for the 22 bands of 63 Hz to 8 kHz. |

**Returns:** [`DiffuseSoundFieldCheck`](/phonometry/reference/api/hearing/sound-field-audiometry/#diffusesoundfieldcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a position is missing or unknown, if the bands do not match, if a reading is given without its index or the other way round, if a single index is below 4 dB, or if a band from 500 Hz up has fewer than two finite readings. |

## earmuff_insertion_loss

```python
earmuff_insertion_loss(
    open_levels_db: ArrayLike,
    occluded_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    isolation_cup_levels_db: ArrayLike | None = None,
    fixture_uncertainty_db: float = 0.3,
    sound_field_uncertainty_db: float = 0.5,
    equipment_uncertainty_db: float = 0.2,
) -> EarmuffInsertionLossResult
```

The insertion loss of an earmuff on the acoustic test fixture (5.4).

The level at the fixture's microphone is measured without the earmuff,
the earmuff is seated on the fixture (5.4.1), and after about 30 s the
level is measured again (5.4.2); the difference in each one-third-octave
band is the insertion loss. With repeated fittings (5.4.3) it is the mean
open level less the mean occluded level:

$$
IL_f = \overline{L}_{\mathrm{open},f} - \overline{L}_{\mathrm{occl},f}
$$

Annex B's uncertainty is evaluated band by band: the standard uncertainty
of each mean level is the standard deviation of the mean of its repeated
measurements (B.3), or Table B.1's typical 0,5 dB open and 1,0 dB occluded
when fewer than two were given, and the three $\delta$ terms default
to Table B.1's 0,3 dB, 0,5 dB and 0,2 dB.

The result is an insertion loss on a fixture. It screens production and
ageing and is not the real-ear attenuation ISO 4869-2 needs (Clause 1);
use [`phonometry.hearing.real_ear_attenuation`](/phonometry/reference/api/hearing/real-ear-attenuation/) for that.

**Parameters**

| Name | Description |
| :--- | :--- |
| `open_levels_db` | The levels without the earmuff, one spectrum or a `(repetitions, bands)` grid, in dB. |
| `occluded_levels_db` | The levels with it, one spectrum or one per fitting, in dB. |
| `frequencies` | The centre frequencies, in hertz, or `None` for the 22 bands of 63 Hz to 8 kHz ([`EARMUFF_TEST_BANDS_HZ`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#earmuff_test_bands_hz)). |
| `isolation_cup_levels_db` | The level with the isolation cup in place of the earmuff per band, in dB, to check that it reads at least 10 dB lower (5.3). |
| `fixture_uncertainty_db` | $u(\delta_1)$, in dB. |
| `sound_field_uncertainty_db` | $u(\delta_2)$, in dB. |
| `equipment_uncertainty_db` | $u(\delta_3)$, in dB. |

**Returns:** [`EarmuffInsertionLossResult`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#earmuffinsertionlossresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels that are not finite, grids of different bands, cup levels that do not match, frequencies that do not fit, or an uncertainty that is negative or not finite. |

## EARMUFF_INSERTION_LOSS_UNCERTAINTY

*Constant* (`phonometry.hearing.earmuff_insertion_loss.InsertionLossUncertaintyBudget`).

## EARMUFF_TEST_BANDS_HZ

*Constant* (`tuple`).

```python
EARMUFF_TEST_BANDS_HZ = (63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0)
```

## EarmuffInsertionLossResult

```python
EarmuffInsertionLossResult(
    insertion_loss_db: np.ndarray,
    repetition_insertion_loss_db: np.ndarray,
    open_levels_db: np.ndarray,
    occluded_levels_db: np.ndarray,
    open_uncertainty_db: np.ndarray,
    occluded_uncertainty_db: np.ndarray,
    fixture_uncertainty_db: float,
    sound_field_uncertainty_db: float,
    equipment_uncertainty_db: float,
    frequencies: np.ndarray,
    isolation_cup_levels_db: np.ndarray | None = None,
)
```

The insertion loss of an earmuff on the test fixture (5.4, Annex B).

A screening quantity, not an attenuation at the ear: Clause 1 says the
data are not to be quoted as the real-ear attenuation of the earmuff nor
as the protection it provides, and nothing in the library feeds them to
the ISO 4869-2 methods.

**Attributes**

| Name | Description |
| :--- | :--- |
| `insertion_loss_db` | $IL_f$, the mean open level less the mean occluded level per band, in dB, unrounded. |
| `repetition_insertion_loss_db` | The mean open level less each fitting's occluded level, one row per repetition, in dB. |
| `open_levels_db` | The levels without the earmuff, one row per measurement, in dB. |
| `occluded_levels_db` | The levels with it, one row per fitting, in dB. |
| `open_uncertainty_db` | The standard uncertainty of the mean open level per band, in dB: the standard deviation of the mean when at least two open measurements were given, else Table B.1's 0,5 dB. |
| `occluded_uncertainty_db` | That of the mean occluded level, from at least two fittings, else Table B.1's 1,0 dB. |
| `fixture_uncertainty_db` | $u(\delta_1)$, in dB. |
| `sound_field_uncertainty_db` | $u(\delta_2)$, in dB. |
| `equipment_uncertainty_db` | $u(\delta_3)$, in dB. |
| `frequencies` | The centre frequencies, in hertz. |
| `isolation_cup_levels_db` | The level with the isolation cup in place of the earmuff per band, in dB, or `None`. |

### EarmuffInsertionLossResult.budget()

```python
EarmuffInsertionLossResult.budget(
    frequency: float,
) -> InsertionLossUncertaintyBudget
```

The budget of Table B.1 for one band of this measurement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | A centre frequency of the measurement, in hertz. |

**Returns:** [`InsertionLossUncertaintyBudget`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#insertionlossuncertaintybudget).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a frequency the measurement does not have. |

### EarmuffInsertionLossResult.expanded_uncertainty_db

*property*

The expanded uncertainty per band, $U = 2u$ (B.4), in dB.

**Returns:** One value per band.

### EarmuffInsertionLossResult.floor_adequate

*property*

Per band, whether the isolation cup reads 10 dB lower at least (5.3).

**Returns:** One boolean per band, or `None` without cup levels.

### EarmuffInsertionLossResult.floor_margin_db

*property*

The mean occluded level less the isolation cup's, per band, in dB.

**Returns:** The margin, or `None` when no cup levels were given.

### EarmuffInsertionLossResult.level_drift_db

*property*

How far the open level strayed from its first measurement, in dB.

5.3 keeps the test signal within ±1 dB of the level set before the
measurement; with one open measurement nothing can be seen and the
drift reads 0.

**Returns:** The largest absolute departure per band.

### EarmuffInsertionLossResult.level_stable

*property*

Per band, whether the open level stayed within ±1 dB (5.3).

**Returns:** One boolean per band.

### EarmuffInsertionLossResult.plot()

```python
EarmuffInsertionLossResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the insertion loss as Clause 6 asks, increasing downwards.

The scale is IEC 60263's 50 dB per decade of frequency, which Clause 6
asks of every graph, so given axes take that aspect too.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the insertion loss curve. |

**Returns:** The axes.

### EarmuffInsertionLossResult.repetitions

*property*

The number of fittings measured.

**Returns:** The count of occluded measurements.

### EarmuffInsertionLossResult.repetitions_sufficient

*property*

Whether at least three fittings were measured (5.4.3).

Fewer are allowed when the device's repeatability is known, which is
the tester's judgement.

**Returns:** `True` from three repetitions.

### EarmuffInsertionLossResult.reported_db

*property*

The insertion loss as Clause 6 reports it, to the nearest 0,1 dB.

**Returns:** One value per band, halves rounded upwards.

### EarmuffInsertionLossResult.response_smooth

*property*

Whether adjacent bands of the open level differ by 5 dB at most (5.3).

**Returns:** `True` when the system's one-third-octave response has no step larger than 5 dB between neighbouring bands.

### EarmuffInsertionLossResult.standard_uncertainty_db

*property*

The combined standard uncertainty per band (Formula (B.2)), in dB.

**Returns:** One value per band.

## FixtureIsolationCheck

```python
FixtureIsolationCheck(frequencies: np.ndarray, isolation_db: np.ndarray)
```

Whether the test fixture isolates its microphone well enough (5.1.4).

The requirement is the clause's, read from the bands as
`required_db`, so a check cannot be built against another one.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | The centre frequencies, in hertz. |
| `isolation_db` | The acoustic isolation (3.7), the level with the isolation cup absent less the level with it sealed on, per band, in dB. |

### FixtureIsolationCheck.margin_db

*property*

The isolation less the requirement per band, in dB.

**Returns:** Negative where the fixture falls short, NaN where nothing is required.

### FixtureIsolationCheck.passes

*property*

Whether the fixture's isolation meets 5.1.4 in every band.

**Returns:** `True` when no band falls short.

### FixtureIsolationCheck.plot()

```python
FixtureIsolationCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the isolation against the requirement, band by band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the isolation curve. |

**Returns:** The axes.

### FixtureIsolationCheck.required_db

*property*

The least isolation 5.1.4 asks per band, in dB.

**Returns:** 50 dB from 63 Hz to 250 Hz, 65 dB from 315 Hz to 4 kHz and 55 dB above; NaN below 63 Hz, where it asks nothing.

### FixtureIsolationCheck.sufficient

*property*

Per band, whether the isolation reaches the requirement.

**Returns:** One boolean per band; `True` where nothing is required.

## InsertionLossUncertaintyBudget

```python
InsertionLossUncertaintyBudget(
    open_level_db: float,
    occluded_level_db: float,
    fixture_db: float,
    sound_field_db: float,
    equipment_db: float,
)
```

The uncertainty budget of an insertion loss (Annex B, Table B.1).

Five normal inputs with a sensitivity coefficient of 1 (B.3), so the
combined standard uncertainty is their root sum of squares (Formula
(B.2)) and the expanded one twice that (B.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `open_level_db` | The standard uncertainty of $L_\mathrm{open}$, the standard deviation of the mean of repeated measurements, in dB. |
| `occluded_level_db` | That of $L_\mathrm{occl}$, which also carries the refitting of the earmuff, in dB. |
| `fixture_db` | $\delta_1$, the fixture's departure from its specification, in dB. |
| `sound_field_db` | $\delta_2$, the field's departure from an ideal random-incidence field or plane wave, in dB. |
| `equipment_db` | $\delta_3$, the measuring equipment, in dB. |

### InsertionLossUncertaintyBudget.combined_db

*property*

$u = \sqrt{\sum (c_i u_i)^2}$ (Formula (B.2)), in dB.

**Returns:** The combined standard uncertainty, unrounded.

### InsertionLossUncertaintyBudget.components_db

*property*

The five standard uncertainties in the order of Table B.1, in dB.

**Returns:** The components.

### InsertionLossUncertaintyBudget.expanded_db

*property*

$U = 2u$ (B.4), in dB.

**Returns:** The expanded uncertainty, unrounded.

### InsertionLossUncertaintyBudget.labels

*property*

The five input quantities of Table B.1, in its order.

**Returns:** Their symbols.

### InsertionLossUncertaintyBudget.plot()

```python
InsertionLossUncertaintyBudget.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the five contributions as bars, with the combined value.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the contribution bars. |

**Returns:** The axes.

## PlaneProgressiveWaveCheck

```python
PlaneProgressiveWaveCheck(
    frequencies: np.ndarray,
    end_face_difference_db: np.ndarray,
    front_to_back_db: np.ndarray,
    front_to_rear_index_db: np.ndarray,
)
```

Whether the plane progressive wave of the test site is good enough (5.2.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | The centre frequencies, in hertz. |
| `end_face_difference_db` | The difference between the levels at the two points the centres of the fixture's end faces occupy, as an absolute value per band, in dB. |
| `front_to_back_db` | From 500 Hz up, the level a directional microphone at the reference point reads facing the source less the level facing away from it, per band, in dB; NaN below 500 Hz or where not measured. |
| `front_to_rear_index_db` | The microphone's front-to-rear sensitivity index per band, in dB, NaN where not given. |

### PlaneProgressiveWaveCheck.directional_required

*property*

Per band, whether the directional test applies (500 Hz and up).

**Returns:** One boolean per band.

### PlaneProgressiveWaveCheck.directionality_judged

*property*

Whether every band from 500 Hz up was read with a suitable microphone.

**Returns:** `True` when none is left unjudged.

### PlaneProgressiveWaveCheck.end_faces_matched

*property*

Per band, whether the two end-face positions are within 2 dB.

**Returns:** One boolean per band.

### PlaneProgressiveWaveCheck.microphone_suitable

*property*

Per band, whether the microphone's front-to-rear index exceeds 15 dB.

**Returns:** One boolean per band; `False` where no index was given.

### PlaneProgressiveWaveCheck.passes

*property*

Whether the plane wave qualifies, every requirement judged.

**Returns:** `True` when every band meets both conditions.

### PlaneProgressiveWaveCheck.plot()

```python
PlaneProgressiveWaveCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw both conditions against their limits, band by band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the end-face difference curve. |

**Returns:** The axes.

### PlaneProgressiveWaveCheck.progressive

*property*

Per band, whether facing the source reads at least 10 dB more.

Bands below 500 Hz count as meeting it; a band from 500 Hz up without
a suitable microphone's reading reads `False`.

**Returns:** One boolean per band.

## RANDOM_INCIDENCE_VARIATION_LIMITS

*Constant* (`tuple`).

```python
RANDOM_INCIDENCE_VARIATION_LIMITS = ((5.0, 5.0), (4.0, 4.0))
```

## verify_fixture_isolation

```python
verify_fixture_isolation(
    open_levels_db: ArrayLike,
    cup_levels_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> FixtureIsolationCheck
```

Does the test fixture isolate its microphone well enough? (5.1.4).

With the test signal of 5.3 at the actual test site, the microphone is
covered by an acoustic isolation test cup sealed to the fixture, and the
acoustic isolation (3.7) is the level without the cup less the level with
it. 5.1.4 asks for at least 50 dB in the bands centred from 63 Hz to
250 Hz, 65 dB from 315 Hz to 4 kHz, and 55 dB above. Airborne and
structure-borne paths both count, which is why the fixture sits on a
resilient mounting (5.1.2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `open_levels_db` | The level at the microphone without the cup, per band, in dB. |
| `cup_levels_db` | The level with the cup sealed on, per band, in dB. |
| `frequencies` | The centre frequencies, in hertz, or `None` for the 22 bands of 63 Hz to 8 kHz. |

**Returns:** [`FixtureIsolationCheck`](/phonometry/reference/api/hearing/earmuff-insertion-loss/#fixtureisolationcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for levels that are not finite or do not match the bands. |

---
title: "metrology.sound_level_meter"
description: "Periodic tests of a sound level meter (IEC 61672-3:2013): the verdict."
sidebar:
  label: "sound_level_meter"
---

Periodic tests of a sound level meter (IEC 61672-3:2013): the verdict.

IEC 61672-3:2013 is the short list of tests a laboratory runs on a working
sound level meter every year or two, to show that it still meets the class it
was built to under IEC 61672-1:2013. The laboratory measures; this module
grades what it measured, clause by clause, and writes the statement Clause 22
prescribes for the outcome.

**The rule.** Every result is judged by the conformance rule of IEC TC 29
that 4.1 states ([`phonometry.metrology.verify_conformance`](/phonometry/reference/api/metrology/conformance/#verify_conformance)): the
measured deviation from the design goal within the acceptance limits **and**
the laboratory's actual expanded uncertainty, for a coverage probability of
95 %, within the maximum permitted by Table B.1 of IEC 61672-1, both limits
inclusive. A result whose uncertainty exceeds its maximum "shall not be used
to evaluate conformance" (4.3): it is neither a pass nor, by itself, a
failure of the meter, [`SoundLevelMeterPeriodicVerification.unusable`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationunusable)
lists it and the verdict does not pass while it is there.

**The manufacturer's correction data (4.4).** The acoustical test of the
frequency weighting (Clause 12) and the electrical one (Clause 13, 13.7)
correct the indications with the manufacturer's free-field or
random-incidence correction data, whose uncertainty the laboratory's budget
carries. The laboratory's uncertainty without it "shall not exceed" the
maximum; when the total exceeds the maximum only because of it, "testing may
proceed", and the result is one that did not conform, with the reason the
NOTE to 22 t) gives in the statement. The record takes that uncertainty
beside the total,
[`SoundLevelMeterPeriodicMeasurements.acoustic_weighting_uncertainties_without_correction_data_db`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicmeasurements)
and its Clause 13 twin, and a result it clears is listed under
[`SoundLevelMeterPeriodicVerification.over_maximum_by_correction_data`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationover_maximum_by_correction_data)
and [`SoundLevelMeterPeriodicVerification.failed`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationfailed) rather than under
`unusable`. Without it the total is all the verdict knows, and 4.3 applies.

**What is graded**, with the acceptance limits of IEC 61672-1:2013 each clause
of IEC 61672-3 points to and the maximum of its Table B.1:

* `acoustic_weighting` (12): the relative frequency weighting at 125 Hz and
  8 kHz, relative to 1 kHz (12.7, 12.15), against Table 3, with 0,60 dB and
  0,70 dB;
* `electrical_weighting` (13): every frequency weighting the meter provides
  at the octave frequencies of 13.4 (63 Hz to 16 kHz for class 1, to 8 kHz for
  class 2), against Table 3, with 0,60 dB up to 4 kHz, 0,70 dB above it and
  1,00 dB above 10 kHz;
* `weighting_at_1khz` (14.2): C and Z against A at 1 kHz, 5.5.9, +/-0,2 dB,
  with 0,20 dB;
* `time_weighting_at_1khz` (14.3): S and time-averaged against F at 1 kHz,
  5.8.3, +/-0,1 dB, with 0,20 dB (the maximum uncertainty is larger than the
  acceptance limit, as the page prints them);
* `long_term_stability` (15): the final minus the initial indication over
  25 min to 35 min, 5.14.2, +/-0,1 dB (class 1) or +/-0,3 dB (class 2), with
  0,10 dB;
* `level_linearity` (16): the level linearity deviations at 8 kHz on the
  reference level range, 5.6.5, +/-0,8 dB or +/-1,1 dB, with 0,30 dB; and
  the absence of an overload or under-range indication within the linear
  operating range the instruction manual states (16.4; IEC 61672-1 5.6.10);
* `range_linearity` (17): the level linearity deviations including the
  level range control, the same limits;
* `toneburst` (18): the 4 kHz toneburst responses of 18.5 to 18.7 less the
  reference responses of Table 4, against its limits, with 0,30 dB;
* `c_peak` (19): $L_\mathrm{Cpeak} - L_\mathrm{C}$ for one cycle at
  8 kHz and the two half cycles at 500 Hz, less the reference differences of
  Table 5, against its limits, with 0,35 dB; and the absence of an overload
  indication while those signals are applied (19.3, 19.5);
* `overload` (20): the difference between the positive and the negative
  one-half-cycle input levels that first cause an overload indication,
  5.11.3, 1,5 dB either way, with 0,25 dB; and the latching of the indicator
  (20.5);
* `high_level_stability` (21): the final minus the initial indication over
  5 min near the top of the least-sensitive range, 5.15.2, +/-0,1 dB or
  +/-0,3 dB, with 0,10 dB.

**What is recorded, not graded.** The indications at the calibration check
frequency before and after adjustment (Clause 10) and the self-generated
noise (Clause 11), which "is reported for information only and is not used to
assess conformance to a requirement" and without an uncertainty (11.1.2,
NOTE 2). Both are still part of a complete test, so a record without them is
incomplete. The environmental conditions (Clause 7) are checked against the
ranges of 7.1, and a test outside them is not a valid periodic test: its
statement says so before anything its results would say.

**What a complete test covers.** 8.1 asks for every test of a design feature
IEC 61672-1 requires and the meter provides. A record shows a feature through
the results it holds, and [`SoundLevelMeterFeatures`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterfeatures) declares the
optional ones the meter has or lacks, as its instruction manual states them;
the verdict holds the record to both: frequency weighting A always and C for
class 1 (5.1.9, 5.1.10), C as well for a meter that measures C-weighted peak
sound level, which "shall also be able to measure C-weighted time-averaged
sound levels" (5.1.10), and every weighting declared or named by a clause of
the record, tested in Clause 13, in the self-generated noise of 11.2 and, C
and Z, in 14.2. The displays are held to the same rule both ways: the F, S
and time-averaged displays are tested in the toneburst tests of Clause 18,
where 18.2 calculates the sound exposure level from the time-averaged one for
a meter that does not measure it, and a display another clause shows is
compared with F in 14.3: S for a meter whose S-time-weighted toneburst
response Clause 18 holds, time-averaged for a meter whose overload indication
Clause 20 holds, as 20.1 tests only a meter that displays time-averaged sound
level. Clause 20 in turn is required of a meter 14.3 shows to display
time-averaged sound level, Clause 17 of a meter with more than one level
range (17.1) and Clause 19 of one that measures C-weighted peak sound level.
A measured clause is held to the extent its procedure gives: the steps of
Clause 16 rise from the starting point in 5 dB steps until within 5 dB of
the upper boundary of the linear operating range and in 1 dB steps from
there up to the first overload indication, and fall the same way down to the
first under-range indication (16.3), so the record carries that range, the
starting point and the two indications; Clause 17 records 5 dB above the
first indication of under-range on every level range, the reference one
included (17.4), and the reference sound level held on every other one
(17.3), whose number the declared features give. A declared feature carries
what IEC 61672-1 makes of it: a meter without frequency weighting C measures
no C-weighted peak sound level (5.1.10), one without the F time weighting has
no S either (5.1.9), and one without F, a time-averaged display or sound
exposure level indicates nothing 5.1.9 asks of a sound level meter and is
refused.
[`SoundLevelMeterPeriodicVerification.missing`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationmissing) names the clauses a
complete test lacks, [`SoundLevelMeterPeriodicVerification.incomplete`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationincomplete)
what a measured clause is short of,
[`SoundLevelMeterPeriodicVerification.not_applicable`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationnot_applicable) the clauses a
feature declared absent takes out, and
[`SoundLevelMeterPeriodicVerification.undeclared`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationundeclared) the features the
record neither shows nor declares, which a record that left their tests out
cannot be told from: the verdict does not pass while one is open.

**The tables.** The acceptance limits of Table 3 are read through
[`phonometry.filters.weighting_class_limits`](/phonometry/reference/api/filters/weighting-compliance/#weighting_class_limits), which already publishes
them. Table 4 (the reference toneburst responses), Table 5 (the reference
differences of the C-weighted peak) and Table B.1 (the maximum-permitted
uncertainties) are published here, read-only, as [`IEC61672_TABLE_4`](/phonometry/reference/api/metrology/sound-level-meter/#iec61672_table_4),
[`IEC61672_TABLE_5`](/phonometry/reference/api/metrology/sound-level-meter/#iec61672_table_5) and [`IEC61672_TABLE_B1`](/phonometry/reference/api/metrology/sound-level-meter/#iec61672_table_b1).

**What a pass here is, and is not.** It is a verdict on the numbers put in:
the preliminary inspection (Clause 5), the power supply (Clause 6), the
calibrator's own conformance to IEC 60942 (Clause 9, which
[`phonometry.metrology.verify_sound_calibrator`](/phonometry/reference/api/metrology/sound-calibrator/#verify_sound_calibrator) grades), the general
test requirements of 8.2 to 8.5 (among them the confirmation of 8.4 that an
electrical output used for the tests reads as the display does) and the
source of the correction data (12.2 to 12.6) are the laboratory's record. And
even a
meter that passes every periodic test supports no general conclusion about the
specifications of IEC 61672-1 unless the model's pattern approval under
IEC 61672-2 is publicly available and the correction data for the acoustical
test came from the instruction manual (Clause 1; 22 r and s): the statement
the verdict writes is the one Clause 22 prescribes for the case at hand. Both
are the laboratory's to declare, as 22 c) and 12.5 have it state them, and
the verdict assumes neither: without both declared it writes 22 s).

Oracle: BS EN 61672-3:2013 (IEC 61672-3:2013) and BS EN 61672-1:2013
(IEC 61672-1:2013), PDF page = printed folio + 2 in both. Tables 3 (folio
22), 4 (25), 5 (28) and B.1 (42 and 43) of Part 1; the clauses of Part 3 on
folios 6 to 19.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ACOUSTIC_TEST_FREQUENCIES_HZ

*Constant* (`tuple`).

```python
ACOUSTIC_TEST_FREQUENCIES_HZ = (125.0, 8000.0)
```

## ELECTRICAL_TEST_FREQUENCIES_HZ

*Constant* (`mapping`).

```python
ELECTRICAL_TEST_FREQUENCIES_HZ = {1: (63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0), 2: (63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)}
```

## IEC61672_TABLE_4

*Constant* (`mapping`).

## IEC61672_TABLE_5

*Constant* (`tuple`).

```python
IEC61672_TABLE_5 = (PeakReference(signal='one cycle', nominal_frequency_hz=31.5, reference_difference_db=2.5, class_1_limits_db=(-2.0, 2.0), class_2_limits_db=(-3.0, 3.0)), PeakReference(signal='one cycle', nominal_frequency_hz=500.0, reference_difference_db=3.5, class_1_limits_db=(-1.0, 1.0), class_2_limits_db=(-2.0, 2.0)), PeakReference(signal='one cycle', nominal_frequency_hz=8000.0, reference_difference_db=3.4, class_1_limits_db=(-2.0, 2.0), class_2_limits_db=(-3.0, 3.0)), PeakReference(signal='positive half cycle', nominal_frequency_hz=500.0, reference_difference_db=2.4, class_1_limits_db=(-1.0, 1.0), class_2_limits_db=(-2.0, 2.0)), PeakReference(signal='negative half cycle', nominal_frequency_hz=500.0, reference_difference_db=2.4, class_1_limits_db=(-1.0, 1.0), class_2_limits_db=(-2.0, 2.0)))
```

## IEC61672_TABLE_B1

*Constant* (`tuple`).

## MaxUncertaintyRow

```python
MaxUncertaintyRow(
    requirement: str,
    reference: str,
    max_uncertainty: float,
    unit: str = 'dB',
    lower_hz: float | None = None,
    upper_hz: float | None = None,
    includes_lower: bool = True,
)
```

One row of IEC 61672-1:2013 Table B.1, a maximum-permitted uncertainty.

**Attributes**

| Name | Description |
| :--- | :--- |
| `requirement` | The requirement, as the "Requirement" column prints it. |
| `reference` | The "Table or subclause" column, as printed (decimal commas included). |
| `max_uncertainty` | The maximum-permitted expanded uncertainty for a coverage probability of 95 %, in `unit`. |
| `unit` | `"dB"`, or `"dB/s"` for the two decay rates of 5.8.2, which the page prints in one cell ("3,50 dB/s for F; 0,40 dB/s for S") and this table in two rows. |
| `lower_hz` | The lower end of the frequency range the row covers, in hertz, or `None` for a row that is not banded by frequency. |
| `upper_hz` | The upper end, inclusive, in hertz, or `None`. |
| `includes_lower` | Whether `lower_hz` belongs to the row; the page writes the bands after the first as "> 1 kHz to 2 kHz". |

### MaxUncertaintyRow.contains()

```python
MaxUncertaintyRow.contains(frequency_hz: float) -> bool
```

Whether a nominal frequency falls in the row's band.

A row that is not banded by frequency contains every frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | The nominal frequency, in hertz. |

**Returns:** `True` inside the band, its included ends counted.

## PeakReference

```python
PeakReference(
    signal: str,
    nominal_frequency_hz: float,
    reference_difference_db: float,
    class_1_limits_db: tuple[float, float],
    class_2_limits_db: tuple[float, float],
)
```

One row of IEC 61672-1:2013 Table 5, the C-weighted peak reference difference.

**Attributes**

| Name | Description |
| :--- | :--- |
| `signal` | The test signal: `"one cycle"`, `"positive half cycle"` or `"negative half cycle"`. |
| `nominal_frequency_hz` | The nominal frequency of the steady signal it is extracted from, in hertz (the test uses the exact frequency of Annex D, NOTE to Table 5). |
| `reference_difference_db` | The reference difference $L_\mathrm{Cpeak} - L_\mathrm{C}$, in decibels. |
| `class_1_limits_db` | The class 1 acceptance limits on the deviation from it, `(lower, upper)`, in decibels. |
| `class_2_limits_db` | The class 2 acceptance limits, in decibels. |

### PeakReference.limits_db()

```python
PeakReference.limits_db(meter_class: int) -> tuple[float, float]
```

The `(lower, upper)` acceptance limits for a class, in decibels.

**Parameters**

| Name | Description |
| :--- | :--- |
| `meter_class` | 1 or 2. |

**Returns:** The limits of that class's column.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for another class. |

## PERIODIC_TEST_ENVIRONMENT

*Constant* (`mapping`).

```python
PERIODIC_TEST_ENVIRONMENT = {'static_pressures_kpa': (80.0, 105.0), 'air_temperatures_c': (20.0, 26.0), 'relative_humidities_percent': (25.0, 70.0)}
```

## SLM_PERIODIC_REQUIREMENTS

*Constant* (`tuple`).

```python
SLM_PERIODIC_REQUIREMENTS = ('acoustic_weighting', 'electrical_weighting', 'weighting_at_1khz', 'time_weighting_at_1khz', 'long_term_stability', 'level_linearity', 'range_linearity', 'toneburst', 'c_peak', 'overload', 'high_level_stability')
```

## SoundLevelMeterFeatures

```python
SoundLevelMeterFeatures(
    *,
    c_weighting: bool | None = None,
    z_weighting: bool | None = None,
    f_time_weighting: bool | None = None,
    s_time_weighting: bool | None = None,
    time_averaged: bool | None = None,
    sound_exposure_level: bool | None = None,
    level_ranges: int | None = None,
    c_weighted_peak: bool | None = None,
)
```

Which optional design features of IEC 61672-1:2013 a sound level meter has.

IEC 61672-3:2013 8.1: the periodic tests "apply only for those design
features that are required by IEC 61672-1 and that are available in the
sound level meter submitted for test. All such features shall be
tested." A record shows that a meter has a feature by holding its
results; it cannot show that the meter lacks one, and a meter with one
level range reads the same as a record that left Clause 17 out. The
instruction manual says which features the meter has (IEC 61672-1
5.1.9, 5.1.10, 5.1.12), and each field carries that answer: `True` the
meter has the feature, `False` it has not, `None` (the default) not
declared, and for the level ranges their number. The verdict owes the
tests of every feature declared or shown, lists the clauses a feature
declared absent takes out of the test under
[`SoundLevelMeterPeriodicVerification.not_applicable`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationnot_applicable), and holds a
feature neither declared nor shown as an open question that keeps the
test incomplete, under
[`SoundLevelMeterPeriodicVerification.undeclared`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationundeclared), as it holds the
number of level ranges of a meter Clause 17 shows to have several, which
17.3 and 17.4 cover. A feature declared absent takes with it the one IEC
61672-1 makes depend on it: without frequency weighting C the meter
measures no C-weighted peak sound level (5.1.10), and without the F time
weighting it has no S (5.1.9). Frequency weighting A has no field: every
meter has it (5.1.9).

**Attributes**

| Name | Description |
| :--- | :--- |
| `c_weighting` | Frequency weighting C, tested in 11.2, 13 and 14.2. A class 1 meter has it, and so does a meter that measures C-weighted peak sound level (IEC 61672-1 5.1.10). |
| `z_weighting` | Frequency weighting Z, tested in 11.2, 13 and 14.2, optional for both classes (5.1.10). |
| `f_time_weighting` | The F time weighting: the maximum F-time-weighted toneburst responses of Clause 18, and the display 14.3 compares the others with. A time-weighting meter has it (5.1.9), so a meter with S has F. |
| `s_time_weighting` | The S time weighting: 14.3 and the maximum S-time-weighted toneburst responses of Clause 18. |
| `time_averaged` | A display of time-averaged sound level: 14.3, the overload indication of Clause 20 (20.1) and the sound exposure level of the tonebursts, which 18.2 calculates from it when the meter does not measure sound exposure level. |
| `sound_exposure_level` | The measurement of sound exposure level: the sound exposure level toneburst responses of Clause 18 (18.2). |
| `level_ranges` | How many level ranges the meter has, as the instruction manual identifies them (IEC 61672-1 5.1.12): 1 for a meter with one, which takes Clause 17 out (17.1), and for more, the number 17.4 covers, the reference level range included, and 17.3 every one besides it. |
| `c_weighted_peak` | The measurement of C-weighted peak sound level: Clause 19. |

## SoundLevelMeterPeriodicMeasurements

```python
SoundLevelMeterPeriodicMeasurements(
    *,
    static_pressures_kpa: Sequence[float] | None = None,
    air_temperatures_c: Sequence[float] | None = None,
    relative_humidities_percent: Sequence[float] | None = None,
    calibration_check_initial_db: float | None = None,
    calibration_check_adjusted_db: float | None = None,
    self_noise_microphone_db: float | None = None,
    self_noise_electrical_db: Mapping[str, float] | None = None,
    acoustic_weighting_deviations_db: Sequence[float] | None = None,
    acoustic_weighting_uncertainties_db: Sequence[float] | None = None,
    acoustic_weighting_uncertainties_without_correction_data_db: Sequence[float] | None = None,
    electrical_weighting_deviations_db: Mapping[str, Sequence[float]] | None = None,
    electrical_weighting_uncertainties_db: Mapping[str, Sequence[float]] | None = None,
    electrical_weighting_uncertainties_without_correction_data_db: Mapping[str, Sequence[float]] | None = None,
    weighting_at_1khz_deviations_db: Mapping[str, float] | None = None,
    weighting_at_1khz_uncertainties_db: Mapping[str, float] | None = None,
    time_weighting_at_1khz_deviations_db: Mapping[str, float] | None = None,
    time_weighting_at_1khz_uncertainties_db: Mapping[str, float] | None = None,
    long_term_stability_db: float | None = None,
    long_term_stability_uncertainty_db: float | None = None,
    linearity_deviations_db: Sequence[float] | None = None,
    linearity_uncertainties_db: Sequence[float] | None = None,
    linearity_levels_db: Sequence[float] | None = None,
    linear_operating_range_db: Sequence[float] | None = None,
    linearity_starting_point_db: float | None = None,
    linearity_overload_level_db: float | None = None,
    linearity_under_range_level_db: float | None = None,
    range_linearity_deviations_db: Mapping[str, Sequence[float]] | None = None,
    range_linearity_uncertainties_db: Mapping[str, Sequence[float]] | None = None,
    toneburst_responses_db: Mapping[str, Sequence[float]] | None = None,
    toneburst_uncertainties_db: Mapping[str, Sequence[float]] | None = None,
    c_peak_differences_db: Sequence[float] | None = None,
    c_peak_uncertainties_db: Sequence[float] | None = None,
    c_peak_overload_indicated: bool | None = None,
    overload_difference_db: float | None = None,
    overload_uncertainty_db: float | None = None,
    overload_latched: bool | None = None,
    high_level_stability_db: float | None = None,
    high_level_stability_uncertainty_db: float | None = None,
)
```

What a laboratory measured in the periodic tests of IEC 61672-3:2013.

Every graded result comes with the actual expanded uncertainty the
laboratory calculated for it, for a coverage probability of 95 % (4.2),
in the same position or under the same key. A clause left at `None` was
not measured. Levels and deviations are in decibels, and every field is
keyword-only, so the unit in its name is written at the call site.

**Attributes**

| Name | Description |
| :--- | :--- |
| `static_pressures_kpa` | Clause 7: the static pressure at the start and the end of the tests at least (7.2), in kilopascals. |
| `air_temperatures_c` | The air temperature at the same times, in degrees Celsius. |
| `relative_humidities_percent` | The relative humidity, in per cent. |
| `calibration_check_initial_db` | Clause 10: the indication at the calibration check frequency on the sound calibrator before any adjustment. |
| `calibration_check_adjusted_db` | The indication after adjustment (the same number when none was needed). |
| `self_noise_microphone_db` | 11.1: the A-weighted self-generated noise with the microphone installed, on the most-sensitive level range; reported for information only, without an uncertainty. |
| `self_noise_electrical_db` | 11.2: the self-generated noise with the electrical input-signal device, keyed by frequency weighting (`"A"`, `"C"`, `"Z"`), every weighting the meter provides. |
| `acoustic_weighting_deviations_db` | 12.16: the deviations of the relative frequency weighting from its design goal at 125 Hz and 8 kHz, in that order ([`ACOUSTIC_TEST_FREQUENCIES_HZ`](/phonometry/reference/api/metrology/sound-level-meter/#acoustic_test_frequencies_hz)), after the corrections of 12.14. |
| `acoustic_weighting_uncertainties_db` | Their uncertainties. |
| `acoustic_weighting_uncertainties_without_correction_data_db` | Optional, for 4.4: the same uncertainties without the uncertainty of the manufacturer's free-field or random-incidence correction data, never more than the totals. A result whose total exceeds its maximum and whose uncertainty without that data does not is a result that did not conform, for that reason, rather than one 4.3 forbids using. |
| `electrical_weighting_deviations_db` | 13.9: for every frequency weighting the meter provides, keyed `"A"`, `"C"`, `"Z"`, the corrected relative frequency weightings, which are the deviations from the design goal, at [`ELECTRICAL_TEST_FREQUENCIES_HZ`](/phonometry/reference/api/metrology/sound-level-meter/#electrical_test_frequencies_hz) for the class in order, NaN at a frequency not measured. |
| `electrical_weighting_uncertainties_db` | The same keys and shape. |
| `electrical_weighting_uncertainties_without_correction_data_db` | Optional, for 4.4: the same without the uncertainty of the manufacturer's correction data, which 13.7 applies too; the same keys, shape and gaps. |
| `weighting_at_1khz_deviations_db` | 14.2: the C-weighted and Z-weighted indications at 1 kHz less the A-weighted one, keyed `"C"` and `"Z"`. |
| `weighting_at_1khz_uncertainties_db` | The same keys. |
| `time_weighting_at_1khz_deviations_db` | 14.3: the A-weighted S-time-weighted (`"S"`) and time-averaged (`"eq"`) indications at 1 kHz less the F-time-weighted one. |
| `time_weighting_at_1khz_uncertainties_db` | The same keys. |
| `long_term_stability_db` | 15.3: the final less the initial A-weighted indication over 25 min to 35 min of operation. |
| `long_term_stability_uncertainty_db` | Its uncertainty. |
| `linearity_deviations_db` | 16: the level linearity deviations at 8 kHz on the reference level range, indicated less anticipated level, one per step of 16.3, in any order. |
| `linearity_uncertainties_db` | Their uncertainties. |
| `linearity_levels_db` | The anticipated level of each 16 result, which labels it and shows which steps of 16.3 the record holds. |
| `linear_operating_range_db` | The lower and the upper boundary of the linear operating range at 8 kHz on the reference level range, as the instruction manual states them (IEC 61672-1 5.6.10): the extent the steps of 16.3 cover and 16.4 holds to the limits. |
| `linearity_starting_point_db` | The starting point the instruction manual gives for the tests of level linearity at 8 kHz on the reference level range (16.2; IEC 61672-1 5.6.11). |
| `linearity_overload_level_db` | The anticipated level of the step that first caused an indication of overload, which the rising steps of 16.3 stop short of. |
| `linearity_under_range_level_db` | The anticipated level of the step that first caused an indication of under-range, which the falling steps of 16.3 stop short of. |
| `range_linearity_deviations_db` | 17.5: the level linearity deviations including the level range control, at 1 kHz, keyed `"17.3"` (the reference sound level of 17.2 held on each level range besides the reference one, NaN where it is not displayed) and `"17.4"` (5 dB above the first indication of under-range on each level range, NaN where not measured). `"17.4"` starts with the reference level range, which 17.4 tests "for each level range" as well, and then takes the other ranges in the order of `"17.3"`, so it holds one value more; 17.3 has no reading on the reference range, where the reference sound level of 17.2 deviates by zero by construction (IEC 61672-1 5.6.3). |
| `range_linearity_uncertainties_db` | The same keys, shape and gaps. |
| `toneburst_responses_db` | 18: the toneburst responses relative to the steady level, keyed `"F"` ($L_\mathrm{AFmax} - L_\mathrm{A}$), `"S"` ($L_\mathrm{ASmax} - L_\mathrm{A}$) and `"E"` ($L_\mathrm{AE} - L_\mathrm{A}$), each at [`TONEBURST_TEST_DURATIONS_MS`](/phonometry/reference/api/metrology/sound-level-meter/#toneburst_test_durations_ms) in order, NaN where not measured. The deviation from Table 4 is taken by the verdict. |
| `toneburst_uncertainties_db` | The same keys and shape. |
| `c_peak_differences_db` | 19.6: $L_\mathrm{Cpeak} - L_\mathrm{C}$ for one cycle at 8 kHz, a positive half cycle at 500 Hz and a negative half cycle at 500 Hz, in that order, NaN where not measured. The deviation from Table 5 is taken by the verdict. |
| `c_peak_uncertainties_db` | Their uncertainties. |
| `c_peak_overload_indicated` | Whether any of those signals caused an overload indication, which 19.3 and 19.5 forbid. |
| `overload_difference_db` | 20.4: the level of the positive one-half-cycle input signal that first caused an overload indication less that of the negative one. |
| `overload_uncertainty_db` | Its uncertainty. |
| `overload_latched` | 20.5: whether the overload indicator latched on as IEC 61672-1 5.11.5 specifies. |
| `high_level_stability_db` | 21.3: the final less the initial A-weighted indication over 5 min of exposure near the upper boundary of the least-sensitive level range. |
| `high_level_stability_uncertainty_db` | Its uncertainty. |

## SoundLevelMeterPeriodicRequirement

```python
SoundLevelMeterPeriodicRequirement(
    name: str,
    clause: str,
    tables: str,
    labels: tuple[str, ...],
    verifications: tuple[ConformanceVerification, ...],
    checks: tuple[tuple[str, bool], ...] = (),
    over_maximum_by_correction_data: tuple[str, ...] = (),
)
```

The verdict on one requirement of IEC 61672-3:2013.

**Attributes**

| Name | Description |
| :--- | :--- |
| `name` | The requirement, one of [`SLM_PERIODIC_REQUIREMENTS`](/phonometry/reference/api/metrology/sound-level-meter/#slm_periodic_requirements). |
| `clause` | The clause of IEC 61672-3:2013 that tests it. |
| `tables` | Where IEC 61672-1:2013 prints its acceptance limits and maximum-permitted uncertainty. |
| `labels` | What each result is (the frequency, the weighting, the toneburst or the signal), in the order given. |
| `verifications` | One [`ConformanceVerification`](/phonometry/reference/api/metrology/conformance/#conformanceverification) per result, on the deviation from the design goal. |
| `checks` | The yes/no requirements of the clause, each `(what, held)`: no overload or under-range indication within the linear operating range (16.4), no overload indication during the C-weighted peak test (19.3, 19.5) and the latching of the overload indicator (20.5). |
| `over_maximum_by_correction_data` | The results whose actual uncertainty exceeds its maximum only because it includes the uncertainty of the manufacturer's free-field or random-incidence correction data (4.4): results that did not conform, for that reason, and not results 4.3 forbids using. |

### SoundLevelMeterPeriodicRequirement.failed

*property*

The results that did not conform, and the failed checks.

A result outside its acceptance limits and measured with an
acceptable uncertainty, or one of
`over_maximum_by_correction_data` (4.4). A result that is
`unusable` shows nothing about the meter (4.3) and is not here.

### SoundLevelMeterPeriodicRequirement.failure_reason()

```python
SoundLevelMeterPeriodicRequirement.failure_reason(label: str) -> str
```

Why a result or a check did not complete, as 22 t) states it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `label` | One of `failed`. |

**Returns:** The reason, in the words of the NOTE to 22 t) where it prints them.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a label that did not fail. |

### SoundLevelMeterPeriodicRequirement.passes

*property*

Whether every result conforms (4.1) and every check held.

### SoundLevelMeterPeriodicRequirement.plot()

```python
SoundLevelMeterPeriodicRequirement.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw every result of the requirement against its limits.

As IEC 61672-1:2013 Figure C.1 draws its examples: the acceptance
limits, the deviation from the design goal, the actual uncertainty as
its error bar and the maximum permitted as the band behind it. The
electrical test of the frequency weightings, whose limits run from
0,7 dB to 16 dB, is drawn as each result's margin to its nearer limit
instead. A result whose uncertainty exceeds its maximum is drawn
hollow, as 4.3 forbids using it, and a result of
`over_maximum_by_correction_data` as one that did not conform
(4.4). The title names the clause and its verdict above the clause's
heading.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the verdict markers. |

### SoundLevelMeterPeriodicRequirement.title

*property*

What the clause tests, as its heading reads.

### SoundLevelMeterPeriodicRequirement.unusable

*property*

The results whose uncertainty exceeds the maximum permitted (4.3).

All of them but those of `over_maximum_by_correction_data`,
which 4.4 lets the test proceed with.

## SoundLevelMeterPeriodicVerification

```python
SoundLevelMeterPeriodicVerification(
    meter_class: int,
    pattern_approval_public: bool,
    corrections_in_manual: bool,
    measurements: SoundLevelMeterPeriodicMeasurements,
    requirements: tuple[SoundLevelMeterPeriodicRequirement, ...],
    features: SoundLevelMeterFeatures = ...,
)
```

The IEC 61672-3:2013 verdict on the periodic tests of a sound level meter.

**Attributes**

| Name | Description |
| :--- | :--- |
| `meter_class` | The class the meter was tested as, 1 or 2. |
| `pattern_approval_public` | Whether evidence is publicly available that the model passed the pattern evaluation of IEC 61672-2 (22 c). |
| `corrections_in_manual` | Whether the correction data for the acoustical test of the frequency weighting came from the instruction manual (12.3) rather than from another manufacturer (12.4). |
| `measurements` | The record the verdict was reached on. |
| `requirements` | One [`SoundLevelMeterPeriodicRequirement`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicrequirement) per requirement measured, in the order of the standard. |
| `features` | The optional features declared for the meter (8.1); every one left at `None` when none were declared. |

### SoundLevelMeterPeriodicVerification.conditions_outside

*property*

The environmental readings outside the ranges of 7.1.

Periodic tests "shall be performed within" 80 kPa to 105 kPa, 20 °C to
26 °C and 25 % to 70 % (7.1); a test outside them is not a valid
periodic test, whatever its results.

### SoundLevelMeterPeriodicVerification.failed

*property*

`(clause, result)` for every result that did not conform or check failed.

A result outside its limits with an acceptable uncertainty, a result
over its maximum only by the manufacturer's correction data (4.4),
and a failed yes/no check.

### SoundLevelMeterPeriodicVerification.incomplete

*property*

`(clause, what is short)` for every measured clause short of a result.

A clause not measured at all is in `missing` instead; see the
module docstring for what 8.1 makes a complete test.

### SoundLevelMeterPeriodicVerification.missing

*property*

The clauses a complete periodic test holds that the record lacks.

Clauses 7, 10, 11, 12, 13, 15, 16, 18 and 21 for every meter; 14.2 for
a meter with C or Z, which class 1 always has (IEC 61672-1 5.1.10)
and any clause of a class 2 record can show, a C-weighted peak result
included (5.1.10); 14.3 for a meter with F that another clause shows
to display S (an S toneburst of Clause 18) or time-averaged sound
level (the overload test of Clause 20, 20.1); Clause 20 for a meter
14.3 shows to display time-averaged sound level (`"eq"`), which
20.1 tests; and each of them, Clause 17 and Clause 19 as well, for a
meter whose `features` declare what the clause tests. A record
cannot show that a meter lacks a feature: a feature neither declared
nor shown is under `undeclared`, and a clause a feature
declared absent takes out is under `not_applicable`.

### SoundLevelMeterPeriodicVerification.not_applicable

*property*

`(clause, why)` for every clause the declared features take out.

8.1 applies the periodic tests only to the features the meter has:
14.2 to a meter with C or Z besides A, 14.3 to one with F and S or a
time-averaged display, Clause 17 to one with more than one level
range (17.1), Clause 19 to one that measures C-weighted peak sound
level and Clause 20 to one that displays time-averaged sound level
(20.1). A clause is here when `features` declare the meter
without what it tests, or without the feature it needs: Clause 19
for a meter declared without frequency weighting C (IEC 61672-1
5.1.10). It is neither `missing` nor needed for a pass.

### SoundLevelMeterPeriodicVerification.over_maximum_by_correction_data

*property*

`(clause, result)` for every result over its maximum only by 4.4.

Its uncertainty exceeds the maximum only because it includes the
uncertainty of the manufacturer's correction data: the test
proceeds, and the result is one that did not conform (4.4), for the
reason the NOTE to 22 t) gives. Each is in `failed` as well.

### SoundLevelMeterPeriodicVerification.passes

*property*

Whether the meter completed the periodic tests successfully.

Every clause a complete test holds was measured on everything it
requires (nothing `missing` or `incomplete`), every
optional feature is declared or shown (nothing `undeclared`),
the tests were within the environmental conditions of 7.1, and every
result conforms: no
deviation outside its limits, no uncertainty above its maximum and no
failed check.

### SoundLevelMeterPeriodicVerification.plot()

```python
SoundLevelMeterPeriodicVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw every graded clause at its margin to its acceptance limits.

One slot per clause, however many results it holds: each result's
distance from its deviation to the nearer acceptance limit is a dash,
and the result that decides the clause is marked over them with its
actual uncertainty as error bar; a result at or above zero lies
within its limits. The mark is a cross for a result that did not
conform, one over its maximum only by the manufacturer's correction
data included (4.4), hollow for one 4.3 forbids using, and otherwise
a diamond at the result nearest its limit. Each requirement's own
[`SoundLevelMeterPeriodicRequirement.plot`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicrequirementplot) draws its results one
by one.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the verdict markers. |

### SoundLevelMeterPeriodicVerification.requirement()

```python
SoundLevelMeterPeriodicVerification.requirement(
    name: str,
) -> SoundLevelMeterPeriodicRequirement
```

The verdict on one requirement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`SLM_PERIODIC_REQUIREMENTS`](/phonometry/reference/api/metrology/sound-level-meter/#slm_periodic_requirements). |

**Returns:** Its [`SoundLevelMeterPeriodicRequirement`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicrequirement).

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | when that requirement was not measured. |

### SoundLevelMeterPeriodicVerification.statement

*property*

The statement IEC 61672-3:2013 Clause 22 prescribes for the result.

In this order, the first that applies: a notice when the tests were
not performed within the conditions of 7.1, as tests outside them are
not periodic tests to IEC 61672-3, whatever their results, and none
of 22 r), s) and t) is theirs; 22 t) when a result exceeds its limits, a
check fails or a result exceeds its maximum only by the uncertainty
of the manufacturer's correction data (4.4), followed by the tests
not completed and why, as a result that did not conform settles the
verdict whatever the others are; the 4.3 notice when results cannot
be used; a notice naming the clauses not measured, what a clause
lacks and the features not declared, as 22 r) and s) both need the
results of all the periodic tests; and otherwise 22 r) with a public
pattern approval and correction data from the manual, or 22 s)
without either, which carries the caveat of Clause 1.

### SoundLevelMeterPeriodicVerification.undeclared

*property*

`(feature, what is open)` for every feature neither declared nor shown.

A feature the record shows through a result is the meter's; one the
record holds no result of may be absent from the meter or left out of
the test, and only `features` can tell the two apart (8.1). Each
such feature, a field of [`SoundLevelMeterFeatures`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterfeatures), keeps the
test from passing until it is declared. The sound exposure level is
not asked for when the meter displays time-averaged sound level, from
which 18.2 calculates it anyway. The number of level ranges stays open
for a meter Clause 17 shows to have several until it is declared, as
17.4 covers every level range and 17.3 every one besides the
reference level range.

### SoundLevelMeterPeriodicVerification.unusable

*property*

`(clause, result)` for every result 4.3 forbids using.

## TONEBURST_TEST_DURATIONS_MS

*Constant* (`mapping`).

```python
TONEBURST_TEST_DURATIONS_MS = {'F': (200.0, 2.0, 0.25), 'S': (200.0, 2.0), 'E': (200.0, 2.0, 0.25)}
```

## ToneburstReference

```python
ToneburstReference(
    duration_ms: float,
    reference_response_db: float,
    class_1_limits_db: tuple[float, float],
    class_2_limits_db: tuple[float, float],
)
```

One row of IEC 61672-1:2013 Table 4, the reference 4 kHz toneburst response.

**Attributes**

| Name | Description |
| :--- | :--- |
| `duration_ms` | The toneburst duration $T_\mathrm{b}$, in milliseconds. |
| `reference_response_db` | The reference response $\delta_\mathrm{ref}$ relative to the steady sound level, in decibels: Equation (7) rounded to a tenth for a maximum time-weighted level, Equation (8) for a sound exposure level. |
| `class_1_limits_db` | The class 1 acceptance limits on the deviation from it, `(lower, upper)`, in decibels. |
| `class_2_limits_db` | The class 2 acceptance limits, in decibels. |

### ToneburstReference.limits_db()

```python
ToneburstReference.limits_db(meter_class: int) -> tuple[float, float]
```

The `(lower, upper)` acceptance limits for a class, in decibels.

**Parameters**

| Name | Description |
| :--- | :--- |
| `meter_class` | 1 or 2. |

**Returns:** The limits of that class's column.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for another class. |

## verify_sound_level_meter_periodic

```python
verify_sound_level_meter_periodic(
    meter_class: int,
    measurements: SoundLevelMeterPeriodicMeasurements,
    *,
    pattern_approval_public: bool = False,
    corrections_in_manual: bool = False,
    features: SoundLevelMeterFeatures | None = None,
) -> SoundLevelMeterPeriodicVerification
```

Grade the periodic tests of a sound level meter, IEC 61672-3:2013.

Each requirement measured is judged result by result by the conformance
rule of IEC TC 29 (4.1), with the acceptance limits IEC 61672-1:2013
prints for it and the maximum-permitted uncertainties of its Table B.1;
see the module docstring for which clause reads which. The verdict passes
when the record is complete, the tests were performed within the
conditions of 7.1 and every result conforms; its
[`statement`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverificationstatement) is the text
Clause 22 prescribes for the case. A frequency-weighting result whose
uncertainty exceeds its maximum only because of the manufacturer's
correction data is a result that did not conform, by 4.4, when the record
gives the uncertainty without that data. The optional features of the
meter (8.1) are what `features` declares and what the record shows; a
feature neither declared nor shown keeps the verdict from passing, as a
record that left a test out reads the same as a meter without the
feature.

**Parameters**

| Name | Description |
| :--- | :--- |
| `meter_class` | The class the meter is tested as, 1 or 2. |
| `measurements` | The laboratory's results and uncertainties. |
| `pattern_approval_public` | Whether evidence is publicly available, from an independent testing organization, that the model passed the pattern evaluation of IEC 61672-2. Without it a passing meter still supports no general conclusion about IEC 61672-1 (Clause 1), and the statement is 22 s) rather than 22 r). |
| `corrections_in_manual` | Whether the correction data for the acoustical test of the frequency weighting were provided in the instruction manual (12.3). Data from another source (12.4) lead to 22 s) as well, and so does a source not declared: 12.5 has the laboratory state it, and 22 r) is written only on both declarations. |
| `features` | Which optional design features of IEC 61672-1 the meter has, and how many level ranges, as its instruction manual states them: a [`SoundLevelMeterFeatures`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterfeatures), or `None` for none declared. A feature declared present owes its tests, and one declared absent takes its clauses out of the test. |

**Returns:** A [`SoundLevelMeterPeriodicVerification`](/phonometry/reference/api/metrology/sound-level-meter/#soundlevelmeterperiodicverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a class other than 1 or 2, a Clause 13 row of the wrong length for the class, a record with nothing graded in it, or `features` that the class or a result of the record contradicts. |

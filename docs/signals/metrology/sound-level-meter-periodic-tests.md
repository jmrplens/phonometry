← [Documentation index](../../README.md)

# Periodic tests of a sound level meter (IEC 61672-3)

A sound level meter in service goes back to a laboratory every year or two
for its **periodic tests**, the short list of key checks IEC 61672-3:2013
keeps "to the minimum considered necessary" (Clause 1). The laboratory
measures; `metrology.verify_sound_level_meter_periodic` grades what it
measured, clause by clause, against the acceptance limits of IEC 61672-1:2013
and the maximum-permitted uncertainties of its Table B.1, and writes the
statement Clause 22 prescribes for the outcome. It runs none of the tests.
This page grades the record of a synthetic class 1 meter whose one fault is a
0.25 ms toneburst.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/slm_periodic_verdict_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/slm_periodic_verdict.svg" alt="Every graded clause of the periodic tests of a synthetic class 1 meter in one slot, from 12 to 21: each result's margin to its nearer acceptance limit as a blue dash, the 27 of Clause 13 and the 25 steps of Clause 16 included, and the result that decides the clause marked over them; every clause above zero except 18, whose maximum F-weighted response to the 0.25 ms toneburst is a red cross at -0.4 dB" width="100%"></picture>

## The rule every clause is graded by

A result conforms when its measured deviation from the design goal is within
the acceptance limits of IEC 61672-1 **and** the laboratory's actual expanded
uncertainty (95 % coverage) is within the maximum of Table B.1, both limits
inclusive (4.1); each result is one `metrology.verify_conformance`. A result
whose uncertainty exceeds its maximum "shall not be used to evaluate
conformance" (4.3): it is listed under `unusable`, apart from `failed`, and
the verdict does not pass while it is there. The exception is 4.4: when the
total exceeds the maximum only because it carries the uncertainty of the
manufacturer's free-field or random-incidence correction data (Clauses 12
and 13), "testing may proceed" and the result is one that did not conform,
provided the uncertainty without that data, which the record takes beside
the total, is within the maximum.

| Clause | Test | Acceptance limits (IEC 61672-1) | Maximum uncertainty (Table B.1) |
| :--- | :--- | :--- | :--- |
| 12 | Frequency weighting with acoustical signals, at 125 Hz and 8 kHz relative to 1 kHz | Table 3 | 0.60 dB up to 4 kHz, 0.70 dB above |
| 13 | Every frequency weighting with electrical signals, 63 Hz to 16 kHz (class 1) or to 8 kHz (class 2) | Table 3 | 0.60 dB, 0.70 dB above 4 kHz, 1.00 dB above 10 kHz |
| 14.2 | C and Z against A at 1 kHz | ±0.2 dB (5.5.9) | 0.20 dB |
| 14.3 | S and time-averaged against F at 1 kHz | ±0.1 dB (5.8.3) | 0.20 dB |
| 15 | Long-term stability, 25 min to 35 min | ±0.1 dB, class 2 ±0.3 dB (5.14.2) | 0.10 dB |
| 16 | Level linearity at 8 kHz on the reference level range | ±0.8 dB, class 2 ±1.1 dB (5.6.5) | 0.30 dB |
| 17 | Level linearity including the level range control, at 1 kHz | ±0.8 dB, class 2 ±1.1 dB (5.6.5) | 0.30 dB |
| 18 | 4 kHz tonebursts of 200 ms, 2 ms and 0.25 ms | Table 4 | 0.30 dB |
| 19 | C-weighted peak: one cycle at 8 kHz, half cycles at 500 Hz | Table 5 | 0.35 dB |
| 20 | Overload indication, positive against negative half cycle | 1.5 dB (5.11.3) | 0.25 dB |
| 21 | High-level stability, 5 min near the top of the least-sensitive range | ±0.1 dB, class 2 ±0.3 dB (5.15.2) | 0.10 dB |

The maximum uncertainty of 14.3 is twice its acceptance limit, as the pages
print them, and Part 3 grades the level linearity against 5.6.5 alone: the
1 dB to 10 dB change of 5.6.6 is a pattern-evaluation requirement
(IEC 61672-2, 9.8.1.7) Part 3 never mentions. Clauses 10 and 11 (the
calibration check and the self-generated noise) are records, not tests;
Clauses 16, 19 and 20 add the yes/no requirements of 16.4 (no overload or
under-range indication inside the linear operating range), 19.3, 19.5 and
20.5.

## Grading a record

The toneburst responses and the C-weighted peak differences go in as
measured, relative to the steady level, and the verdict takes the deviation
from Tables 4 and 5; everything else goes in as the deviation its clause
defines. Clause 16 also carries what shows that its steps cover 16.3, the 25
steps of an 80 dB linear operating range, and the meter's two level ranges,
which no record can count, are declared beside it.

```python
from phonometry import metrology

record = metrology.SoundLevelMeterPeriodicMeasurements(
    # Clause 7: the conditions at the start and the end of the tests.
    static_pressures_kpa=[100.9, 100.7],
    air_temperatures_c=[22.8, 23.3],
    relative_humidities_percent=[48.0, 46.0],
    # Clauses 10 and 11: recorded, not graded.
    calibration_check_initial_db=93.8,
    calibration_check_adjusted_db=94.0,
    self_noise_microphone_db=16.9,
    self_noise_electrical_db={"A": 11.8, "C": 13.9, "Z": 19.2},
    # Clause 12: 125 Hz and 8 kHz, relative to 1 kHz, after the corrections.
    acoustic_weighting_deviations_db=[0.3, -0.9],
    acoustic_weighting_uncertainties_db=[0.28, 0.45],
    # Clause 13: every weighting, at the nine octaves from 63 Hz to 16 kHz.
    electrical_weighting_deviations_db={
        "A": [0.1, 0.1, 0.0, 0.0, 0.0, 0.0, -0.1, -0.3, -0.9],
        "C": [0.2, 0.1, 0.0, 0.0, 0.0, 0.0, -0.1, -0.4, -1.2],
        "Z": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.2, -0.8],
    },
    electrical_weighting_uncertainties_db={
        w: [0.14] * 7 + [0.18, 0.25] for w in ("A", "C", "Z")
    },
    # Clause 14: C and Z against A, S and time-averaged against F, at 1 kHz.
    weighting_at_1khz_deviations_db={"C": 0.0, "Z": 0.1},
    weighting_at_1khz_uncertainties_db={"C": 0.12, "Z": 0.12},
    time_weighting_at_1khz_deviations_db={"S": 0.0, "eq": 0.05},
    time_weighting_at_1khz_uncertainties_db={"S": 0.12, "eq": 0.12},
    # Clause 15: the long-term stability.
    long_term_stability_db=0.04,
    long_term_stability_uncertainty_db=0.07,
    # Clause 16 at 8 kHz: the linear operating range and the starting point
    # the manual states, each step by its anticipated level, up from the
    # starting point in 5 dB steps and in 1 dB steps from within 5 dB of the
    # upper boundary, then down the same way, and the levels that first
    # indicated overload and under-range.
    linear_operating_range_db=[40.0, 120.0],
    linearity_starting_point_db=94.0,
    linearity_levels_db=[
        94.0, 99.0, 104.0, 109.0, 114.0, 119.0, 120.0, 121.0, 122.0,
        89.0, 84.0, 79.0, 74.0, 69.0, 64.0, 59.0, 54.0, 49.0, 44.0,
        43.0, 42.0, 41.0, 40.0, 39.0, 38.0,
    ],
    linearity_deviations_db=[
        0.0, 0.0, 0.1, 0.1, 0.1, 0.1, 0.0, -0.1, -0.2,
        0.0, 0.0, 0.0, -0.1, 0.0, 0.0, 0.1, 0.1, 0.1, 0.2,
        0.2, 0.3, 0.3, 0.4, 0.5, 0.6,
    ],
    linearity_uncertainties_db=[0.18] * 25,
    linearity_overload_level_db=123.0,
    linearity_under_range_level_db=37.0,
    # Clause 17 at 1 kHz: 5 dB above the first under-range indication on
    # both level ranges, the reference one first (17.4), and the reference
    # level held on the other one (17.3).
    range_linearity_deviations_db={"17.3": [0.1], "17.4": [0.1, -0.2]},
    range_linearity_uncertainties_db={"17.3": [0.18], "17.4": [0.18, 0.18]},
    # Clause 18: the responses at 200 ms, 2 ms and 0.25 ms (S: 200 ms, 2 ms).
    toneburst_responses_db={
        "F": [-1.1, -18.2, -30.4],
        "S": [-7.5, -27.4],
        "E": [-7.0, -27.1, -36.6],
    },
    toneburst_uncertainties_db={
        "F": [0.2, 0.2, 0.25],
        "S": [0.2, 0.2],
        "E": [0.2, 0.2, 0.25],
    },
    # Clause 19: one cycle at 8 kHz, then the two half cycles at 500 Hz.
    c_peak_differences_db=[3.9, 2.5, 2.2],
    c_peak_uncertainties_db=[0.3, 0.3, 0.3],
    c_peak_overload_indicated=False,
    # Clauses 20 and 21.
    overload_difference_db=0.4,
    overload_uncertainty_db=0.2,
    overload_latched=True,
    high_level_stability_db=0.03,
    high_level_stability_uncertainty_db=0.07,
)
meter = metrology.SoundLevelMeterFeatures(level_ranges=2)
result = metrology.verify_sound_level_meter_periodic(1, record, features=meter)
print(result.passes)  # False
print(result.failed)  # (('18', 'F, 0.25 ms'),)

row = metrology.IEC61672_TABLE_4["F"][-1]
print(row.duration_ms, row.reference_response_db, row.limits_db(1))
# 0.25 -27.0 (-3.0, 1.0)
worst = result.requirement("toneburst").verifications[2]
print(round(worst.deviation, 2), worst.lower_limit)  # -3.4 -3.0
```

The meter read -30.4 dB for the 0.25 ms toneburst, 3.4 dB below the
reference of Table 4, where class 1 allows 3.0 dB, with an uncertainty within
the 0.30 dB of Table B.1: the result is usable and the clause fails. The
module publishes Tables 4, 5 and B.1 of IEC 61672-1 as `IEC61672_TABLE_4`,
`IEC61672_TABLE_5` and `IEC61672_TABLE_B1`; Table 3 is read through
`filters.weighting_class_limits`.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/slm_periodic_toneburst_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/slm_periodic_toneburst.svg" alt="The eight toneburst results of clause 18 as IEC 61672-1 Figure C.1 draws its examples: each deviation from Table 4 with its uncertainty, the maximum-permitted band and the acceptance limits; only F at 0.25 ms, at -3.4 dB, lies below its -3.0 dB limit" width="92%"></picture>

## What a complete test holds

8.1 asks for every test of a design feature IEC 61672-1 requires and the
meter provides, and the record shows the features whose results it holds:
Clauses 7, 10, 11, 12, 13, 15, 16, 18 and 21 for every meter; A in Clause 13
always, and C for class 1 and for a meter with a C-weighted peak (5.1.9,
5.1.10); every weighting any of 13, 11.2 and 14.2 names in all three (C and
Z only in 14.2); the F, S and time-averaged displays in the tonebursts of
Clause 18, the sound exposure level calculated from the time-averaged one
when the meter does not measure it (18.2), and 14.3 for the displays Clause
18 (S) and Clause 20 (time-averaged) show; Clause 20 for a meter with a
time-averaged display (20.1); and the conditions of 7.1 (80 kPa to 105 kPa,
20 °C to 26 °C, 25 % to 70 %), recorded at the start and the end (7.2).
A measured clause is held to its extent. Clause 16 rises from the starting
point in 5 dB steps until within 5 dB of the upper boundary of the linear
operating range, then in 1 dB steps up to, but not including, the first
indication of overload, and falls the same way to the first indication of
under-range (16.3): a wider step, or a record without the levels to tell,
leaves it incomplete, and an overload or under-range indication inside the
linear operating range, where IEC 61672-1 5.6.10 says the meter shows
neither, fails it (16.4). Clause 17 reads 5 dB above the first under-range
indication on every level range, the reference one included and first
(17.4, "for each level range"), and the reference level held on every other
one (17.3, NaN where a range does not display it); on the reference range
17.3 would read the level 17.2 set, a deviation of zero by construction
(IEC 61672-1 5.6.3).

A record cannot show a feature the meter lacks: a meter with one level range
reads the same as a record that left Clause 17 out, and a meter without
C-weighted peak as one without Clause 19. `metrology.SoundLevelMeterFeatures`,
passed as `features=`, carries what the instruction manual says: `True` for a
feature the meter has, `False` for one it lacks, `None` (the default) for one
not declared. A feature declared present owes its tests, one declared absent
takes its clauses out, and one neither declared nor shown keeps the verdict
from passing. The level ranges are a number, `level_ranges`, since a record
cannot count them either: 1 takes Clause 17 out, and a larger number is how
many ranges 17.4 covers, the reference one included, and 17.3 besides it. A feature
declared absent takes with it the one IEC 61672-1 makes depend on it: no
C-weighted peak without frequency weighting C (5.1.10), so Clause 19 is not
applicable, and no S without F (5.1.9); a declaration without F, a
time-averaged display and sound exposure level is refused (5.1.9). `missing`, `incomplete`, `undeclared`, `not_applicable` and
`conditions_outside` say what is short, open or out of the test. The
verdict's figure gives each graded clause one slot, every result a dash and
the one that decides the clause marked over them, and names each graded
clause the record does not hold as not measured, not declared or not
applicable.

```python
import dataclasses

basic = dataclasses.replace(
    record,
    range_linearity_deviations_db=None,
    range_linearity_uncertainties_db=None,
    c_peak_differences_db=None,
    c_peak_uncertainties_db=None,
    c_peak_overload_indicated=None,
)
unsaid = metrology.verify_sound_level_meter_periodic(1, basic)
print([name for name, _ in unsaid.undeclared])
# ['level_ranges', 'c_weighted_peak']
declared = metrology.verify_sound_level_meter_periodic(
    1,
    basic,
    features=metrology.SoundLevelMeterFeatures(
        level_ranges=1, c_weighted_peak=False
    ),
)
print(declared.undeclared, [clause for clause, _ in declared.not_applicable])
# () ['17', '19']

no_s = dataclasses.replace(
    record,
    toneburst_responses_db={"F": [-1.1, -18.2, -30.4], "E": [-7.0, -27.1, -36.6]},
    toneburst_uncertainties_db={"F": [0.2, 0.2, 0.25], "E": [0.2, 0.2, 0.25]},
)
short = metrology.verify_sound_level_meter_periodic(1, no_s, features=meter)
print(short.passes, short.incomplete[0][0])  # False 18

one_step = dataclasses.replace(
    record,
    linearity_levels_db=[94.0],
    linearity_deviations_db=[0.0],
    linearity_uncertainties_db=[0.18],
)
thin = metrology.verify_sound_level_meter_periodic(1, one_step, features=meter)
print(thin.passes, [clause for clause, _ in thin.incomplete])  # False ['16', '16']

nan = float("nan")
no_reference = dataclasses.replace(
    record,
    range_linearity_deviations_db={"17.3": [0.1], "17.4": [nan, -0.2]},
    range_linearity_uncertainties_db={"17.3": [0.18], "17.4": [nan, 0.18]},
)
open_17 = metrology.verify_sound_level_meter_periodic(1, no_reference, features=meter)
print(open_17.incomplete)
# (('17', '17.4 was not measured on the reference level range, and it tests
#   every level range, the reference one included'),)
```

## The statement of Clause 22

`result.statement` is the first of these that applies: a notice when the
tests were not performed within the conditions of 7.1, as tests outside them
are not periodic tests to IEC 61672-3 whatever their results; 22 t) when a
result fails, 4.4 included, with the tests not completed and why; a notice
when a result is unusable (4.3) or the record is incomplete; 22 r) when every
result passes, the model's IEC 61672-2 approval is public
(`pattern_approval_public=True`) and the acoustical correction data came from
the instruction manual (`corrections_in_manual=True`); and 22 s), with its
caveat that the periodic tests "cover only a limited subset of the
specifications", when every result passes but either is missing. Both
declarations default to `False`: 22 c) and 12.5 have the laboratory state
them, and the verdict assumes neither.

Here the laboratory took the correction data of Clause 12 from the
instruction manual, as 12.3 asks first, and `corrections_in_manual=True` says
so; data from the manufacturer of the microphone or of the calibrator (12.4),
or a source left undeclared, would give 22 s) instead.

```python
fixed = dataclasses.replace(
    record,
    toneburst_responses_db={
        "F": [-1.1, -18.2, -29.6],
        "S": [-7.5, -27.4],
        "E": [-7.0, -27.1, -36.6],
    },
)
again = metrology.verify_sound_level_meter_periodic(
    1,
    fixed,
    pattern_approval_public=True,
    corrections_in_manual=True,
    features=meter,
)
print(again.passes)                                  # True
print(again.statement.endswith("of IEC 61672-1:2013."))  # True
```

A total of 0.85 dB at 8 kHz in Clause 12, past the 0.70 dB of Table B.1 only
because of the manufacturer's correction data, with 0.66 dB without them:

```python
over = dataclasses.replace(
    fixed,
    acoustic_weighting_uncertainties_db=[0.28, 0.85],
    acoustic_weighting_uncertainties_without_correction_data_db=[0.28, 0.66],
)
check = metrology.verify_sound_level_meter_periodic(
    1,
    over,
    pattern_approval_public=True,
    corrections_in_manual=True,
    features=meter,
)
print(check.unusable, check.over_maximum_by_correction_data)
# () (('12', '8 kHz'),)
```

## What this guide covers

Implemented: the conformance rule of 4.1 on every graded result of Clauses 12
to 21, with the limits of IEC 61672-1:2013 and the maxima of its Table B.1;
the unusable results of 4.3 and the exception of 4.4; the yes/no
requirements of 16.4, 19.3, 19.5 and 20.5;
the conditions of 7.1 and 7.2; the completeness of 8.1, from the features
the record shows and those `SoundLevelMeterFeatures` declares present or
absent, with what IEC 61672-1 5.1.9 and 5.1.10 make of a feature declared
absent; the extent of Clause 16 over the steps of 16.3 and of Clause 17
over every level range; and the statements of 22 r), s) and t). Not
implemented: the tests themselves; the level linearity deviations, the
corrected relative frequency weightings and the uncertainty budget are
inputs; the manual, markings, inspection, power supply, general test
requirements (8.2 to 8.5, the electrical output confirmation of 8.4
included), calibrator and correction-data source of Clauses 3 to 9 and 12.2
to 12.6 are the laboratory's record; the 22 l) statement, required when the
free-field correction data come without an uncertainty, is not written.

## See also

- [Compliance and verification](compliance-verification.md): the conformance
  rule of IEC TC 29, and what pattern evaluation and periodic tests attest.
- [Free-field corrections of a sound level meter (IEC 62585)](free-field-corrections.md):
  the corrections the acoustical test of Clause 12 applies.
- [Calibration and dBFS](calibration.md): the sound calibrator of Clause 9
  and its verdict under IEC 60942.
- [Sound level meter](../sound-level-meter.md): the frequency and time
  weightings, and the design verdict on the library's own chain.
- API reference: [`metrology.sound_level_meter`](https://jmrplens.github.io/phonometry/reference/api/metrology/sound-level-meter/).

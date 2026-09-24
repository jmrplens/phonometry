---
title: "metrology.sound_calibrator"
description: "Sound calibrators (IEC 60942:2017): the class tables and the verdict on one."
sidebar:
  label: "sound_calibrator"
---

Sound calibrators (IEC 60942:2017): the class tables and the verdict on one.

A calibrator is the one instrument every calibrated level in this library
leans on: [`phonometry.metrology.sensitivity`](/phonometry/reference/api/metrology/calibration/#sensitivity) turns its tone into the
factor that converts digital units into pascals, so an error in the tone is
an error in every level measured after it. IEC 60942:2017 (EN IEC 60942:2018)
says how good the tone has to be, in three classes: **LS** (laboratory
standard), **1** and **2**, with the designations **LS/M** and **1/M** for
pistonphones that meet their class only once a static-pressure correction from
the manufacturer is applied (5.1.5, Table 1).

**What is graded.** Every requirement of the standard that is a measured
number with an acceptance limit and a maximum-permitted uncertainty:

* `level` (5.3.2): Table 2, with the maximum uncertainty of Table A.1;
* `fluctuation` (5.3.3): Table 2, with Table A.1;
* `frequency` (5.4.2): Table 4, with Table A.2;
* `distortion` (5.6): Table 7, with Table A.3;
* `supply_voltage` (5.3.4): Table 3, with the maximum A.5.5.7 and A.5.5.8
  print in their text;
* `environmental_level` (5.5): Table 5, or the reduced limits of A.6.4.7,
  with Table A.4;
* `environmental_frequency` (5.5): Table 6, or A.6.4.7, with Table A.5;
* `field_immunity` (5.9.4.2): the limits 5.9.4.2 prints, with the maximum of
  A.7.4.8.

Each is judged by the conformance rule of IEC TC 29
([`phonometry.metrology.verify_conformance`](/phonometry/reference/api/metrology/conformance/#verify_conformance), 5.1.15): the measured
deviation within the acceptance limit **and** the laboratory's actual expanded
uncertainty within the maximum permitted, both inclusive. The deviation limits
of the level, the supply-voltage effect, the frequency and the field immunity
bound an *absolute* difference, so a signed deviation is judged against
$\pm$ the limit; the short-term fluctuation and the total distortion +
noise are magnitudes, judged against zero and the limit.

**The tables.** Tables 2, 5 and 7 and Tables A.1, A.3 and A.4 are keyed by a
range of nominal frequencies, published as tuples of [`CalibratorTableRow`](/phonometry/reference/api/metrology/sound-calibrator/#calibratortablerow);
Tables 3, 4 and 6 and Tables A.2 and A.5 hold one figure per class, published as
read-only mappings keyed by `"LS"`, `"1"` and `"2"`. A dash in the printed
table, the ranges of nominal frequency "for which this document provides no
acceptance limits", is `None`: classes LS and 2 are specified only from
160 Hz to 1 250 Hz, and 5.1.2 forbids stating conformance where there is no
limit, so [`verify_sound_calibrator`](/phonometry/reference/api/metrology/sound-calibrator/#verify_sound_calibrator) refuses such a nominal frequency
rather than grading it against a neighbouring row.

**The /M correction is an input.** A class LS/M or 1/M pistonphone's output
follows the ambient static pressure, and its manual gives the correction to
the reference 101,325 kPa (5.1.5, 6.3 i). That correction depends on the
barometer reading and on data only the manufacturer has, so this module does
not compute it: the caller supplies it as
[`SoundCalibratorMeasurements.static_pressure_correction_db`](/phonometry/reference/api/metrology/sound-calibrator/#soundcalibratormeasurements) and it is
added to the measured level before the level is graded (5.3.2, A.5.1.2,
B.4.3.2). Every other calibrator shall not need any environmental correction
(5.1.7), and is refused one.

**The abbreviated environmental test.** A.6.4 lets a laboratory replace the
full temperature and humidity tests (A.6.5 to A.6.7) with a few combined
conditions judged against tighter limits: Table 5 reduced by 0,05 dB for
classes LS and 1 and by 0,10 dB for class 2, and 0,5 %, 0,5 % and 1,3 % for the
frequency (A.6.4.7). A calibrator that meets those is deemed to conform; one
that does not is **not** thereby non-conforming, it has to be given the full
tests (A.6.1.2). `environmental_test="abbreviated"` applies the reduced limits
and the verdict means exactly that.

**What a verdict here is and is not.** It grades the numbers a laboratory
measured; it measures nothing. The requirements that are not numbers with a
tolerance (the markings and the manual of Clause 6, the stabilization time of
5.1.10, the supply indicator of 5.7, the radio-frequency emission limits of
5.9.2 and the electrostatic discharges of 5.9.3) are hardware and paperwork
checks outside it. And 5.1.18 is explicit that full conformance needs both
halves: the model passing the pattern evaluation of Annex A and the specimen
passing the periodic tests of Annex B, whose own verdict names only what was
tested (B.6 g, h).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT

*Constant* (`mapping`).

```python
ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT = {'LS': 0.5, '1': 0.5, '2': 1.3}
```

## ABBREVIATED_LEVEL_REDUCTIONS_DB

*Constant* (`mapping`).

```python
ABBREVIATED_LEVEL_REDUCTIONS_DB = {'LS': 0.05, '1': 0.05, '2': 0.1}
```

## CALIBRATOR_CLASSES

*Constant* (`tuple`).

```python
CALIBRATOR_CLASSES = ('LS', 'LS/M', '1', '1/M', '2')
```

## CALIBRATOR_REQUIREMENTS

*Constant* (`tuple`).

```python
CALIBRATOR_REQUIREMENTS = ('level', 'fluctuation', 'frequency', 'distortion', 'supply_voltage', 'environmental_level', 'environmental_frequency', 'field_immunity')
```

## CalibratorTableRow

```python
CalibratorTableRow(
    lower_hz: float,
    upper_hz: float,
    includes_lower: bool,
    includes_upper: bool,
    class_ls: float | None,
    class_1: float | None,
    class_2: float | None,
)
```

One row of an IEC 60942:2017 table keyed by a range of nominal frequencies.

The printed ranges close and open their ends differently ("31,5 to 63",
"> 63 to \< 160", "> 1 250 to 4 000"), so each row says which of its two
ends it includes. A cell the table prints as a dash, a range the standard
gives that class no limit in, is `None`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `lower_hz` | The lower end of the range of nominal frequencies, in hertz. |
| `upper_hz` | The upper end, in hertz. |
| `includes_lower` | Whether a nominal frequency equal to `lower_hz` belongs to the row. |
| `includes_upper` | Whether a nominal frequency equal to `upper_hz` belongs to the row. |
| `class_ls` | The class LS figure, or `None` for a dash. |
| `class_1` | The class 1 figure, or `None` for a dash. |
| `class_2` | The class 2 figure, or `None` for a dash. |

### CalibratorTableRow.contains()

```python
CalibratorTableRow.contains(nominal_frequency_hz: float) -> bool
```

Whether a nominal frequency falls in this row's range.

**Parameters**

| Name | Description |
| :--- | :--- |
| `nominal_frequency_hz` | The nominal frequency, in hertz. |

**Returns:** `True` inside the range, its included ends counted.

### CalibratorTableRow.for_class()

```python
CalibratorTableRow.for_class(calibrator_class: str) -> float | None
```

The figure this row prints for a class, or `None` for a dash.

**Parameters**

| Name | Description |
| :--- | :--- |
| `calibrator_class` | `"LS"`, `"1"` or `"2"`, or a /M designation, which reads the column of its class (5.1.14). |

**Returns:** The printed figure, or `None` where the table prints a dash.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown class. |

## DISTORTION_ACCEPTANCE_LIMITS_PERCENT

*Constant* (`tuple`).

```python
DISTORTION_ACCEPTANCE_LIMITS_PERCENT = (CalibratorTableRow(lower_hz=31.5, upper_hz=160.0, includes_lower=True, includes_upper=False, class_ls=None, class_1=3.0, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=2.0, class_1=2.5, class_2=3.0), CalibratorTableRow(lower_hz=1250.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=3.0, class_2=None))
```

## DISTORTION_MAX_UNCERTAINTY_PERCENT

*Constant* (`tuple`).

```python
DISTORTION_MAX_UNCERTAINTY_PERCENT = (CalibratorTableRow(lower_hz=31.5, upper_hz=160.0, includes_lower=True, includes_upper=False, class_ls=None, class_1=1.0, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=0.5, class_1=0.5, class_2=1.0), CalibratorTableRow(lower_hz=1250.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=1.0, class_2=None))
```

## ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT

*Constant* (`mapping`).

```python
ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT = {'LS': 0.7, '1': 0.7, '2': 1.7}
```

## ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT

*Constant* (`mapping`).

```python
ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT = {'LS': 0.2, '1': 0.2, '2': 0.2}
```

## ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB

*Constant* (`tuple`).

```python
ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB = (CalibratorTableRow(lower_hz=31.5, upper_hz=160.0, includes_lower=True, includes_upper=False, class_ls=None, class_1=0.25, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=0.1, class_1=0.25, class_2=0.4), CalibratorTableRow(lower_hz=1250.0, upper_hz=4000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.3, class_2=None), CalibratorTableRow(lower_hz=4000.0, upper_hz=8000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.45, class_2=None), CalibratorTableRow(lower_hz=8000.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.6, class_2=None))
```

## ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB

*Constant* (`tuple`).

```python
ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB = (CalibratorTableRow(lower_hz=31.5, upper_hz=160.0, includes_lower=True, includes_upper=False, class_ls=None, class_1=0.25, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=0.1, class_1=0.15, class_2=0.2), CalibratorTableRow(lower_hz=1250.0, upper_hz=4000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.3, class_2=None), CalibratorTableRow(lower_hz=4000.0, upper_hz=8000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.35, class_2=None), CalibratorTableRow(lower_hz=8000.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.4, class_2=None))
```

## FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB

*Constant* (`mapping`).

```python
FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB = {'LS': 0.1, '1': 0.25, '2': 0.45}
```

## FIELD_IMMUNITY_MAX_UNCERTAINTY_DB

*Constant* (`mapping`).

```python
FIELD_IMMUNITY_MAX_UNCERTAINTY_DB = {'LS': 0.05, '1': 0.05, '2': 0.05}
```

## FLUCTUATION_ACCEPTANCE_LIMITS_DB

*Constant* (`tuple`).

```python
FLUCTUATION_ACCEPTANCE_LIMITS_DB = (CalibratorTableRow(lower_hz=31.5, upper_hz=63.0, includes_lower=True, includes_upper=True, class_ls=None, class_1=0.2, class_2=None), CalibratorTableRow(lower_hz=63.0, upper_hz=160.0, includes_lower=False, includes_upper=False, class_ls=None, class_1=0.1, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=0.03, class_1=0.07, class_2=0.15), CalibratorTableRow(lower_hz=1250.0, upper_hz=4000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.07, class_2=None), CalibratorTableRow(lower_hz=4000.0, upper_hz=8000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.07, class_2=None), CalibratorTableRow(lower_hz=8000.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.07, class_2=None))
```

## FLUCTUATION_MAX_UNCERTAINTY_DB

*Constant* (`tuple`).

```python
FLUCTUATION_MAX_UNCERTAINTY_DB = (CalibratorTableRow(lower_hz=31.5, upper_hz=63.0, includes_lower=True, includes_upper=True, class_ls=None, class_1=0.15, class_2=None), CalibratorTableRow(lower_hz=63.0, upper_hz=160.0, includes_lower=False, includes_upper=False, class_ls=None, class_1=0.1, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=0.02, class_1=0.03, class_2=0.05), CalibratorTableRow(lower_hz=1250.0, upper_hz=4000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.03, class_2=None), CalibratorTableRow(lower_hz=4000.0, upper_hz=8000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.03, class_2=None), CalibratorTableRow(lower_hz=8000.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.03, class_2=None))
```

## FREQUENCY_ACCEPTANCE_LIMITS_PERCENT

*Constant* (`mapping`).

```python
FREQUENCY_ACCEPTANCE_LIMITS_PERCENT = {'LS': 0.7, '1': 0.7, '2': 1.7}
```

## FREQUENCY_MAX_UNCERTAINTY_PERCENT

*Constant* (`mapping`).

```python
FREQUENCY_MAX_UNCERTAINTY_PERCENT = {'LS': 0.2, '1': 0.2, '2': 0.2}
```

## LEVEL_ACCEPTANCE_LIMITS_DB

*Constant* (`tuple`).

```python
LEVEL_ACCEPTANCE_LIMITS_DB = (CalibratorTableRow(lower_hz=31.5, upper_hz=63.0, includes_lower=True, includes_upper=True, class_ls=None, class_1=0.3, class_2=None), CalibratorTableRow(lower_hz=63.0, upper_hz=160.0, includes_lower=False, includes_upper=False, class_ls=None, class_1=0.3, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=0.1, class_1=0.25, class_2=0.4), CalibratorTableRow(lower_hz=1250.0, upper_hz=4000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.35, class_2=None), CalibratorTableRow(lower_hz=4000.0, upper_hz=8000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.45, class_2=None), CalibratorTableRow(lower_hz=8000.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.5, class_2=None))
```

## LEVEL_MAX_UNCERTAINTY_DB

*Constant* (`tuple`).

```python
LEVEL_MAX_UNCERTAINTY_DB = (CalibratorTableRow(lower_hz=31.5, upper_hz=63.0, includes_lower=True, includes_upper=True, class_ls=None, class_1=0.2, class_2=None), CalibratorTableRow(lower_hz=63.0, upper_hz=160.0, includes_lower=False, includes_upper=False, class_ls=None, class_1=0.2, class_2=None), CalibratorTableRow(lower_hz=160.0, upper_hz=1250.0, includes_lower=True, includes_upper=True, class_ls=0.1, class_1=0.15, class_2=0.35), CalibratorTableRow(lower_hz=1250.0, upper_hz=4000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.25, class_2=None), CalibratorTableRow(lower_hz=4000.0, upper_hz=8000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.35, class_2=None), CalibratorTableRow(lower_hz=8000.0, upper_hz=16000.0, includes_lower=False, includes_upper=True, class_ls=None, class_1=0.5, class_2=None))
```

## SoundCalibratorMeasurements

```python
SoundCalibratorMeasurements(
    level_deviation_db: float | Sequence[float] | None = None,
    level_uncertainty_db: float | Sequence[float] | None = None,
    static_pressure_correction_db: float | Sequence[float] | None = None,
    fluctuation_db: float | Sequence[float] | None = None,
    fluctuation_uncertainty_db: float | Sequence[float] | None = None,
    frequency_deviation_percent: float | Sequence[float] | None = None,
    frequency_uncertainty_percent: float | Sequence[float] | None = None,
    distortion_percent: float | Sequence[float] | None = None,
    distortion_uncertainty_percent: float | Sequence[float] | None = None,
    supply_voltage_deviation_db: float | Sequence[float] | None = None,
    supply_voltage_uncertainty_db: float | Sequence[float] | None = None,
    environmental_level_deviation_db: float | Sequence[float] | None = None,
    environmental_level_uncertainty_db: float | Sequence[float] | None = None,
    environmental_frequency_deviation_percent: float | Sequence[float] | None = None,
    environmental_frequency_uncertainty_percent: float | Sequence[float] | None = None,
    field_immunity_deviation_db: float | Sequence[float] | None = None,
    field_immunity_uncertainty_db: float | Sequence[float] | None = None,
)
```

What a laboratory measured on a sound calibrator, for IEC 60942:2017.

Each requirement is a pair of fields, the measured deviation and the
actual expanded uncertainty of its measurement for a coverage probability
of 95 %, and each pair is given or left out together. A field takes one
number or a sequence of them, one per measurement condition (the supply
voltages of A.5.5.6 to A.5.5.8, the static pressures, temperatures and
humidities of A.6, the settings of a multi-level calibrator at one
frequency); an uncertainty given as one number applies to all of them.

**Attributes**

| Name | Description |
| :--- | :--- |
| `level_deviation_db` | Measured minus specified sound pressure level (5.3.2), each the mean of at least three couplings (A.5.5.3, B.4.6.3.1), in decibels. For an /M pistonphone, as measured: the correction below is added to it. |
| `level_uncertainty_db` | Its expanded uncertainty, in decibels. |
| `static_pressure_correction_db` | The manufacturer's correction to the reference static pressure for a class LS/M or 1/M pistonphone (5.1.5, B.4.3.2), in decibels, added to `level_deviation_db`. Required for those designations whenever the level is given (`0.0` at the reference pressure) and refused for every other (5.1.7). |
| `fluctuation_db` | The short-term level fluctuation (5.3.3): the larger of the absolute differences between the maximum and the minimum F-weighted level and their mean over 60 s, in decibels. |
| `fluctuation_uncertainty_db` | Its expanded uncertainty, in decibels. |
| `frequency_deviation_percent` | Measured minus specified frequency, in per cent of the specified frequency (5.4.2). |
| `frequency_uncertainty_percent` | Its expanded uncertainty, in per cent of the specified frequency. |
| `distortion_percent` | The total distortion + noise over 22,4 Hz to 22,4 kHz (5.6), in per cent. |
| `distortion_uncertainty_percent` | Its expanded uncertainty, in per cent distortion. |
| `supply_voltage_deviation_db` | The level at a supply voltage at an end of the permitted range minus the level at the nominal voltage (5.3.4), in decibels. |
| `supply_voltage_uncertainty_db` | Its expanded uncertainty, in decibels. |
| `environmental_level_deviation_db` | The level at an environmental condition outside the band of 5.3.2 minus the level at reference conditions (5.5), in decibels; for an /M pistonphone already corrected for static pressure, one correction per condition (A.6.2.3). |
| `environmental_level_uncertainty_db` | Its expanded uncertainty, in decibels. |
| `environmental_frequency_deviation_percent` | The frequency at such a condition minus the frequency at reference conditions, in per cent of the specified frequency (5.5). |
| `environmental_frequency_uncertainty_percent` | Its expanded uncertainty, in per cent of the specified frequency. |
| `field_immunity_deviation_db` | The level in a power- or radio-frequency field minus the level without it (5.9.4.2), in decibels. |
| `field_immunity_uncertainty_db` | Its expanded uncertainty, in decibels, the field measurement excluded (A.7.4.8). |

### SoundCalibratorMeasurements.pairs()

```python
SoundCalibratorMeasurements.pairs(
    requirement: str,
) -> tuple[tuple[float, float], ...]
```

The `(deviation, uncertainty)` pairs measured for a requirement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `requirement` | One of [`CALIBRATOR_REQUIREMENTS`](/phonometry/reference/api/metrology/sound-calibrator/#calibrator_requirements). |

**Returns:** One pair per measurement, empty when it was not measured.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown requirement. |

## SoundCalibratorRequirement

```python
SoundCalibratorRequirement(
    name: str,
    clause: str,
    tables: str,
    verifications: tuple[ConformanceVerification, ...],
)
```

One requirement of IEC 60942:2017, judged on every measurement of it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `name` | The requirement, one of [`CALIBRATOR_REQUIREMENTS`](/phonometry/reference/api/metrology/sound-calibrator/#calibrator_requirements). |
| `clause` | The subclause of IEC 60942:2017 that states it. |
| `tables` | Where its acceptance limit and maximum-permitted uncertainty are printed. |
| `verifications` | One [`ConformanceVerification`](/phonometry/reference/api/metrology/conformance/#conformanceverification) per measurement, in the order they were given. |

### SoundCalibratorRequirement.acceptance_limits

*property*

The `(lower, upper)` acceptance limits, the same for every measurement.

### SoundCalibratorRequirement.max_uncertainty

*property*

The maximum-permitted expanded uncertainty for the requirement.

### SoundCalibratorRequirement.passes

*property*

Whether every measurement of the requirement demonstrates conformance.

### SoundCalibratorRequirement.plot()

```python
SoundCalibratorRequirement.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each measurement against the requirement's limits, as Figure E.1.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.metrology.plot_sound_calibrator_requirement`. |

### SoundCalibratorRequirement.unit

*property*

The unit the requirement is measured in, `"dB"` or `"%"`.

## SoundCalibratorVerification

```python
SoundCalibratorVerification(
    calibrator_class: str,
    nominal_frequency_hz: float,
    environmental_test: str,
    measurements: SoundCalibratorMeasurements,
    requirements: tuple[SoundCalibratorRequirement, ...],
)
```

The IEC 60942:2017 verdict on one setting of a sound calibrator.

**Attributes**

| Name | Description |
| :--- | :--- |
| `calibrator_class` | The designation it was judged as, one of [`CALIBRATOR_CLASSES`](/phonometry/reference/api/metrology/sound-calibrator/#calibrator_classes). |
| `nominal_frequency_hz` | The nominal frequency of the setting, in hertz, which selects the rows of the banded tables. |
| `environmental_test` | `"full"` (Tables 5 and 6) or `"abbreviated"` (the reduced limits of A.6.4.7). |
| `measurements` | The record the verdict was reached on. |
| `requirements` | One [`SoundCalibratorRequirement`](/phonometry/reference/api/metrology/sound-calibrator/#soundcalibratorrequirement) per requirement measured, in the order of [`CALIBRATOR_REQUIREMENTS`](/phonometry/reference/api/metrology/sound-calibrator/#calibrator_requirements). |

### SoundCalibratorVerification.failed

*property*

The names of the requirements that do not pass.

### SoundCalibratorVerification.passes

*property*

Whether every requirement measured demonstrates conformance.

`False` when nothing was measured: a record with no measurement in it
qualifies nothing. With `environmental_test="abbreviated"` a failed
environmental requirement means the full tests of A.6.5 to A.6.7 are
due (A.6.1.2), not that the calibrator does not conform.

### SoundCalibratorVerification.plot()

```python
SoundCalibratorVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw how much of each allowance every measurement uses.

One pair of bars per measurement: the deviation as a share of its
acceptance limit and the uncertainty as a share of its maximum. A
requirement conforms when both of its bars stop at or before 100 %.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.metrology.plot_sound_calibrator_verification`. |

### SoundCalibratorVerification.requirement()

```python
SoundCalibratorVerification.requirement(
    name: str,
) -> SoundCalibratorRequirement
```

The verdict on one requirement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | One of [`CALIBRATOR_REQUIREMENTS`](/phonometry/reference/api/metrology/sound-calibrator/#calibrator_requirements). |

**Returns:** Its [`SoundCalibratorRequirement`](/phonometry/reference/api/metrology/sound-calibrator/#soundcalibratorrequirement).

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | when that requirement was not measured. |

## SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB

*Constant* (`mapping`).

```python
SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB = {'LS': 0.02, '1': 0.06, '2': 0.16}
```

## SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB

*Constant* (`mapping`).

```python
SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB = {'LS': 0.02, '1': 0.04, '2': 0.04}
```

## verify_sound_calibrator

```python
verify_sound_calibrator(
    calibrator_class: str,
    measurements: SoundCalibratorMeasurements,
    *,
    nominal_frequency_hz: float,
    environmental_test: str = 'full',
) -> SoundCalibratorVerification
```

Verify what a laboratory measured on a sound calibrator against IEC 60942:2017.

Every requirement given in `measurements` is judged by the conformance
rule of IEC TC 29 (5.1.15, [`phonometry.metrology.verify_conformance`](/phonometry/reference/api/metrology/conformance/#verify_conformance))
against the acceptance limit and the maximum-permitted uncertainty that
the class and the nominal frequency select, and the calibrator passes when
every measurement of every requirement does. The requirements, their
clauses and tables are listed in the module documentation of
[`phonometry.metrology.sound_calibrator`](/phonometry/reference/api/metrology/sound-calibrator/).

One call judges one setting: a multi-frequency calibrator is verified once
per frequency setting, because the banded tables change with it. For an
LS/M or 1/M pistonphone the level is graded after the manufacturer's
static-pressure correction is added to it (5.3.2, B.4.3.2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `calibrator_class` | `"LS"`, `"LS/M"`, `"1"`, `"1/M"` or `"2"` (Table 1); `1` and `2` may be given as integers. |
| `measurements` | What was measured, as [`SoundCalibratorMeasurements`](/phonometry/reference/api/metrology/sound-calibrator/#soundcalibratormeasurements). |
| `nominal_frequency_hz` | The nominal frequency of the setting, in hertz. It has to be one the class has acceptance limits at: 31,5 Hz to 16 kHz for class 1, 160 Hz to 1 250 Hz for classes LS and 2 (5.1.2). |
| `environmental_test` | `"full"` (default) judges the environmental requirements against Tables 5 and 6; `"abbreviated"` against the reduced limits of A.6.4.7, where a failure calls for the full tests rather than a non-conformance (A.6.1.2). |

**Returns:** The [`SoundCalibratorVerification`](/phonometry/reference/api/metrology/sound-calibrator/#soundcalibratorverification), whose `passes` is the verdict and whose `requirements` carry one verdict each.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown class or environmental test, a nominal frequency the class has no acceptance limit at, a static-pressure correction given for a class that is not an /M pistonphone, or one missing for an /M pistonphone whose level is given. |

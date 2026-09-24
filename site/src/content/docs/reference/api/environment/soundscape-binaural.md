---
title: "environment.assessment.soundscape_binaural"
description: "What a soundscape sounds like at the ears: the binaural analysis of ISO/TS 12913-3:2019 Annex D and ISO/TS 12913-2:2018 Annex D."
sidebar:
  label: "soundscape_binaural"
---

What a soundscape sounds like at the ears: the binaural analysis of
ISO/TS 12913-3:2019 Annex D and ISO/TS 12913-2:2018 Annex D.

A soundscape study records the acoustic environment with an artificial head,
because a binaural recording keeps what a listener hears with both ears. For
the analysis, each of the two channels is processed on its own, after the
recording has been equalized to approximate a monaural microphone
measurement (ISO/TS 12913-3 clause 7, ISO/TS 12913-2 D.4). Every metric of
Table D.1 is determined for each ear, and the **higher of the two values**
is the single representative value "indicating the overall experience"; the
arithmetic mean of the two may be reported as well (D.2). [`binaural_indicators`](/phonometry/reference/api/environment/soundscape-binaural/#binaural_indicators)
does that for a calibrated two-channel recording, with the library's own
implementation of each metric:

* **sound pressure level**, ISO 1996-1: $L_{\mathrm{Aeq},T}$,
  $L_{\mathrm{Ceq},T}$, $L_{\mathrm{AF5},T}$ and
  $L_{\mathrm{AF95},T}$, from [`laeq`](/phonometry/reference/api/signals/levels/#laeq),
  [`leq`](/phonometry/reference/api/signals/levels/#leq) of the C-weighted signal and
  [`ln_levels`](/phonometry/reference/api/signals/levels/#ln_levels) with time weighting F;
* **loudness**, ISO 532-1: $N_5$, $N_\mathrm{average}$,
  $N_\mathrm{rmc}$, $N_{95}$ and the variability ratio
  $N_5/N_{95}$ of D.2, from the time-varying method of
  [`loudness_zwicker`](/phonometry/reference/api/psychoacoustics/zwicker/#loudness_zwicker);
* **psychoacoustic tonality** $T$: Table D.1 names ECMA-74, whose
  current edition (the 22nd, Annex G) refers the psychoacoustic tonality
  calculation to ECMA-418-2 clause 6, which
  [`tonality_ecma`](/phonometry/reference/api/psychoacoustics/tonality-ecma/#tonality_ecma) implements in its
  2025 edition;
* **roughness** $R_{10}$, $R_{50}$ and **fluctuation strength**
  $F_{10}$, $F_{50}$: Table D.1 cites Fastl and Zwicker for both,
  and ISO/TS 12913-2 Annex B notes that no standardized method existed in
  2018. The library computes both with the hearing model of ECMA-418-2:2025
  ([`roughness_ecma`](/phonometry/reference/api/psychoacoustics/roughness-ecma/#roughness_ecma),
  [`fluctuation_strength_ecma`](/phonometry/reference/api/psychoacoustics/fluctuation-strength-ecma/#fluctuation_strength_ecma)), whose
  time-dependent values give the percentiles; the method is named in every
  result, as ISO/TS 12913-2 4.2 requires ("the used calculation method shall
  be reported").

**Sharpness** $S_5$, $S_\mathrm{average}$ and $S_{95}$ are
**not computed**. They are percentiles of a sharpness that varies in time,
and the library's DIN 45692 sharpness
([`sharpness_din`](/phonometry/reference/api/psychoacoustics/sharpness/#sharpness_din)) is taken from the
stationary specific loudness of ISO 532-1; its time-varying loudness does not
publish the specific loudness over time that a time-varying sharpness needs.
The result says so in `not_implemented` rather than filling the row with a
stationary value under a percentile's name.

Recording requirements of ISO/TS 12913-2 Annex D that the signal itself can
show are checked with a [`SoundscapeWarning`](/phonometry/reference/api/environment/soundscape-binaural/#soundscapewarning): a measurement interval
of at least 3 min (D.3) and a sampling frequency of at least 44.1 kHz (D.6).
The equalization (D.4), the position (D.2) and the calibration are the
caller's: the channels are taken as equalized sound pressure, left first.

The ISO/TS 12913-3 implemented is the first edition, of 2019; ISO has since
published ISO/TS 12913-3:2025, which revises Annex A (the questionnaire
analysis, [`phonometry.environment.assessment.soundscape`](/phonometry/reference/api/environment/soundscape/)).

**Computing cost.** The ECMA-418-2 metrics run the full hearing model on
every channel, and on a 3 min recording they take minutes each, tonality
most of all. `parameters` chooses which rows of Table D.1 to compute.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## binaural_indicators

```python
binaural_indicators(
    x: SignalInput,
    fs: float | None = None,
    *,
    calibration_factor: float | None = None,
    field: Literal['free', 'diffuse'] = 'free',
    parameters: Sequence[str] = ('sound_pressure_level', 'loudness', 'sharpness', 'tonality', 'roughness', 'fluctuation_strength'),
) -> BinauralIndicators
```

The metrics of ISO/TS 12913-3 Table D.1 at each ear of a binaural
recording, with their representative values (Annex D, D.2).

Each channel is analysed on its own and every metric is reported for the
left and the right ear; [`BinauralMetric.representative`](/phonometry/reference/api/environment/soundscape-binaural/#binauralmetricrepresentative) is the
higher of the two, the single value D.2 uses "for all metrics
considered", and [`BinauralMetric.mean`](/phonometry/reference/api/environment/soundscape-binaural/#binauralmetricmean) their arithmetic mean. The
loudness row adds the variability ratio $N_5/N_{95}$ D.2 suggests.
Which library function computes which metric, and why the sharpness row
stays empty, is in the module docstring; each metric carries its method.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | The equalized binaural recording, shape `(2, samples)` with the left ear first, in pascals after `calibration_factor`; a [`Signal`](/phonometry/reference/api/io/io/#signal) with two channels brings its own rate and calibration. |
| `fs` | Sampling frequency, in Hz. Required for a bare array; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value that disagrees with it raises. |
| `calibration_factor` | Multiplier from the recorded units to pascals, the same for both channels. An explicit value wins over the one a Signal carries; a bare array with neither is taken to be in pascals. |
| `field` | The sound field the recording was equalized for, `"free"` (default) or `"diffuse"`, passed to the loudness and the hearing-model metrics. |
| `parameters` | The rows of Table D.1 to compute, keys of [`BINAURAL_PARAMETERS`](/phonometry/reference/api/environment/soundscape-binaural/#binaural_parameters); all of them by default. |

**Returns:** A [`BinauralIndicators`](/phonometry/reference/api/environment/soundscape-binaural/#binauralindicators).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a recording that is not two channels, an unknown field or row, or a loudness exceeded 95 % of the time of zero, which leaves $N_5/N_{95}$ undefined. |

**Warns**

| Warning | When |
| :--- | :--- |
| SoundscapeWarning | for a recording shorter than the 3 min of ISO/TS 12913-2 D.3 or sampled below the 44.1 kHz of D.6. |

## BINAURAL_PARAMETERS

*Constant* (`mapping`).

```python
BINAURAL_PARAMETERS = {'sound_pressure_level': BinauralParameter(parameter='Sound pressure level', metrics=('LAeq,T', 'LCeq,T', 'LAF5,T', 'LAF95,T'), average_allowed=False, reference='ISO 1996-1'), 'loudness': BinauralParameter(parameter='Loudness (time-variant loudness)', metrics=('N5', 'Naverage', 'Nrmc', 'N95', 'N5/N95'), average_allowed=True, reference='ISO 532-1'), 'sharpness': BinauralParameter(parameter='Sharpness', metrics=('S5', 'Saverage', 'S95'), average_allowed=True, reference='DIN 45692'), 'tonality': BinauralParameter(parameter='Psychoacoustic tonality', metrics=('T',), average_allowed=True, reference='ECMA 74'), 'roughness': BinauralParameter(parameter='Roughness', metrics=('R10', 'R50'), average_allowed=True, reference='[32]'), 'fluctuation_strength': BinauralParameter(parameter='Fluctuation strength', metrics=('F10', 'F50'), average_allowed=True, reference='[32]')}
```

## BinauralIndicators

```python
BinauralIndicators(
    metrics: Mapping[str, BinauralMetric],
    not_implemented: Mapping[str, str],
    parameters: tuple[str, ...],
    fs: float,
    duration_s: float,
    field: str,
)
```

The binaural analysis of a soundscape recording (ISO/TS 12913-3
Annex D, Table D.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `metrics` | Every metric computed, keyed by its Table D.1 symbol, in the order of the table. |
| `not_implemented` | Every metric of a requested row that the library does not compute, keyed by its symbol, with the reason. |
| `parameters` | The rows of Table D.1 that were requested. |
| `fs` | The sampling frequency of the recording, in Hz. |
| `duration_s` | Its duration, in s. |
| `field` | The sound field the loudness and hearing-model metrics assumed, `"free"` or `"diffuse"`. |

### BinauralIndicators.plot()

```python
BinauralIndicators.plot(
    ax: Axes | None = None,
    *,
    parameter: str | None = None,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot one row of Table D.1: each metric at both ears, with the
representative value marked.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `parameter` | The row to draw, a key of [`BINAURAL_PARAMETERS`](/phonometry/reference/api/environment/soundscape-binaural/#binaural_parameters); `None` draws the first one computed. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the left-ear bars. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the row was not computed or nothing was. |

### BinauralIndicators.reporting_results()

```python
BinauralIndicators.reporting_results() -> dict[str, float]
```

The results ISO/TS 12913-2 A.3 f) requires a report to give.

The representative value of each of $L_{\mathrm{Aeq},T}$,
$L_{\mathrm{Ceq},T}$, $L_{\mathrm{AF5},T}$,
$L_{\mathrm{AF95},T}$, $N_5$, $N_{95}$ and
$N_\mathrm{rmc}$, keyed by those symbols, ready for
[`SoundscapeAcousticEnvironment`](/phonometry/reference/api/environment/soundscape/#soundscapeacousticenvironment).

**Returns:** A new dictionary, symbol to value.

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | if the sound pressure level or the loudness row was not computed. |

### BinauralIndicators.representative()

```python
BinauralIndicators.representative(symbol: str) -> float
```

The single representative value of a metric: the higher ear (D.2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `symbol` | The metric, as Table D.1 prints it. |

**Returns:** The higher of the left and right values.

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | if the metric was not computed; a metric the library does not implement says why in `not_implemented`. |

## BinauralMetric

```python
BinauralMetric(
    symbol: str,
    parameter: str,
    left: float,
    right: float,
    unit: str,
    method: str,
)
```

One metric of Table D.1 at both ears (ISO/TS 12913-3 D.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `symbol` | The metric, as Table D.1 prints it (`"LAeq,T"`, `"N5"`...). |
| `parameter` | The row of Table D.1 it belongs to, a key of [`BINAURAL_PARAMETERS`](/phonometry/reference/api/environment/soundscape-binaural/#binaural_parameters). |
| `left` | The value at the left ear. |
| `right` | The value at the right ear. |
| `unit` | Its unit. |
| `method` | How the library computed it. |

### BinauralMetric.mean

*property*

The arithmetic mean of the two ears, which D.2 allows in addition.

### BinauralMetric.representative

*property*

The higher of the two ears, the single representative value of D.2.

## BinauralParameter

```python
BinauralParameter(
    parameter: str,
    metrics: tuple[str, ...],
    average_allowed: bool,
    reference: str,
)
```

One row of ISO/TS 12913-3 Table D.1, "Metrics and representative
single values".

**Attributes**

| Name | Description |
| :--- | :--- |
| `parameter` | The parameter, as the first column prints it. |
| `metrics` | The metrics to be determined for each channel separately, as their symbols print, in the printed order. |
| `average_allowed` | Whether the row offers "the average of left and right metric values" as an alternative to the higher value; the sound pressure level row does not. |
| `reference` | The document the row cites. |

## SoundscapeWarning

A recording falls short of what ISO/TS 12913-2 Annex D requires of it.

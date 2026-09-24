← [Documentation index](../../README.md)

# Calibration and dBFS

Every level this library reports is only as trustworthy as the one number
this page produces: the sensitivity factor that converts digital units into
pascals. The page covers both reference frames a recording can be analyzed
in: physical **dB SPL**, obtained by calibrating the chain against an
IEC 60942 acoustic calibrator, and digital **dBFS**, levels relative to
full scale with no physical claim attached.

Choosing between them is a question about your measurement chain, not
about preference. Work in dB SPL whenever the result faces a physical
criterion (a noise limit, an exposure threshold, any acoustics standard);
that requires a calibrator recording made through the *same, untouched*
chain as the measurement. Work in dBFS when the signal never had a
calibrated analog front end (loudness normalization, codec and interface
tests, file-only analysis) or when no calibration tone exists, in which
case absolute SPL statements are simply out of reach.

The workflow around the factor matters as much as the formula: derive it
before and re-check it after each session, verify meter and calibrator
periodically in the laboratory (IEC 61672-3 and IEC 60942; Bies, Hansen &
Howard 2017, §3.4), and treat the pre/post difference as your drift bound.
The field, laboratory and drift section below turns that into concrete
rules, and the [Build a sound level meter](../sound-level-meter.md)
walkthrough starts from exactly this step before any level is computed.

## Why calibrate? The theory

A digital recording only knows *numbers*: a full-scale sine wave is ±1.0
regardless of whether it was a whisper or a jet engine. To report physical
sound pressure levels the chain microphone → preamplifier → ADC must be
characterized by a single number, the **sensitivity factor** $S$, that
converts digital units into pascals:

$$
p(t) = S\ x(t) \qquad S = \frac{p_\text{ref}\cdot 10^{L_\text{cal}/20}}{\tilde{x}_\text{ref}}
$$

where $L_\text{cal}$ is the calibrator's level (typically 94 dB, i.e. 1 Pa),
$p_\text{ref} = 20\ \mu\text{Pa}$ and $\tilde{x}_\text{ref}$ is the RMS of
the recorded calibration tone in digital units. `sensitivity()` is
exactly that equation. The factor is valid as long as nothing in the chain
changes: touch the gain knob and you must recalibrate.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_calibration_setup_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_calibration_setup.svg" alt="Calibration chain: sound calibrator coupled on the microphone, preamplifier, ADC and sensitivity producing pascals per digital unit" width="92%"></picture>

## Physical Calibration (Sound Level Meter)

To get accurate SPL measurements from a digital recording, you must first
calculate the sensitivity of your measurement chain using a reference tone
(e.g., 94 dB @ 1 kHz).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_calibration_dataflow_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_calibration_dataflow.svg" alt="Calibration data flow: the calibrator recording and the measurement recording come from the same untouched chain, sensitivity() turns the first into the factor S in pascals per digital unit and, given fs, checks the short-term stability of IEC 60942, every level function accepts that factor as calibration_factor, and the result is levels in dB SPL re 20 µPa; with no calibrator the factor stays at 1 and the samples are read as pascals, so dbfs=True is what gives levels referred to digital full scale" width="92%"></picture>

```python
import numpy as np
from phonometry import filters, metrology

# 1. Record your 94 dB calibrator signal (1 kHz, 1 Pa RMS = 94 dB SPL)
fs = 48000
# calibrator_recording: your recorded 1 kHz calibrator tone (1 Pa RMS = 94 dB SPL).
#   Synthesized here so the guide runs; in a real measurement, record your calibrator.
calibrator_recording = np.sqrt(2) * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)
# recording: the mic capture you want to calibrate, same input chain (Pa after calibration).
#   Synthesized here; in a real measurement this is your recorded signal.
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# 2. Calculate the sensitivity factor
calibration_factor = metrology.sensitivity(calibrator_recording, target_spl=94.0, fs=fs)

# 3. Apply calibration to your measurements
filtered = filters.octave_filter(
    recording, fs,
    calibration=filters.LevelCalibration(factor=calibration_factor))
spl, freq = filtered.levels, filtered.frequencies
# Now 'spl' values are in real-world dB SPL!
```

The same factor works across the whole library: `octave_filter` and
`OctaveFilterBank` take it inside `LevelCalibration(factor=...)`, and `leq`,
`laeq` and `ln_levels` as `calibration_factor=`.

## Calibrator assumptions (IEC 60942)

`sensitivity` assumes the reference recording comes from an acoustic
calibrator as specified by **IEC 60942** (classes LS, 1 and 2):

- The default `target_spl=94.0` matches the common 94 dB @ 1 kHz calibrator
  output (the standard requires the principal level to be at least 90 dB re
  20 µPa; 94 dB and 114 dB are the usual choices).
- The resulting sensitivity inherits the calibrator's class tolerance plus
  the RMS estimation error of your recording. IEC 60942:2017 prints no
  tolerance limit: Table 2 gives the acceptance limit on the generated level
  (0.25 dB for class 1 between 160 Hz and 1.25 kHz) and Table A.1 the
  maximum-permitted uncertainty of the measurement that demonstrates it
  (0.15 dB), and Annex D puts the tolerance limit at their sum, ±0.4 dB.
- IEC 60942 specifies the generated level as a 20 s average: record a few
  seconds of *stable* tone (excluding handling noise at the start/end) for the
  RMS estimate to converge.

The calibrator itself gets its own verdict, from what a laboratory measured
on it: see [Verifying the calibrator itself](#verifying-the-calibrator-itself-iec-609422017)
below. `sensitivity()` does not apply an environmental correction: when the
calibrator's manual asks for a static-pressure correction, apply it yourself
and pass the corrected value as `target_spl`.

### Automatic stability validation

When you pass the sample rate (and `validate=True`, the default),
`sensitivity(ref, fs=fs)` checks the recording the way
IEC 60942:2017 checks the calibrator itself (5.3.3): the *short-term level
fluctuation*, the absolute difference between each of the maximum and minimum
F-time-weighted levels and the mean level, must not exceed the Table 2 limit
for the calibrator's class and nominal frequency, read from the published
`metrology.FLUCTUATION_ACCEPTANCE_LIMITS_DB` (class 1: 0.07 dB at and above
160 Hz, relaxed to 0.10 dB below 160 Hz and 0.20 dB at or below 63 Hz, where
the F time-weighting itself ripples). Pass `frequency=` to select the right row
for non-1 kHz calibrators, and `calibrator_class=` for a class LS (0.03 dB) or
class 2 (0.15 dB) calibrator; where Table 2 gives the class no limit, the
strictest figure of its own column applies. A `CalibrationWarning` flags badly coupled microphones or handling
noise before they silently corrupt every calibrated level. The recording must
be at least 2 s long (1 s for the F-integrator to settle plus 1 s of settled
envelope); shorter recordings get a warning instead of an unreliable verdict.
Without `fs` the check is skipped. Override the limit with
`max_fluctuation_db` or disable with `validate=False`.

The check catches exactly what ruins field calibrations (a loose coupler,
wind, handling noise):

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/calibration_stability_dark.webp"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/calibration_stability.webp" alt="F-weighted level of a stable calibration tone versus a 3 percent amplitude-modulated one against the plus-minus 0.07 dB IEC 60942 class 1 limit" width="80%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import filters

fs = 48000
t = np.arange(int(fs * 6.0)) / fs
stable = 0.5 * np.sin(2 * np.pi * 1000 * t)
# 3 % amplitude modulation at 2 Hz: ~0.14 dB of wobble, clearly over
unstable = stable * (1 + 0.03 * np.sin(2 * np.pi * 2.0 * t))

plt.figure(figsize=(9, 5))
skip = fs                     # discard the F-integrator attack (~8 tau)
for x, label in ((stable, "Stable tone (good coupling)"),
                 (unstable, "3% AM tone (loose coupling)")):
    env = filters.time_weighting(x, fs, mode="fast")[skip:]
    level = 10 * np.log10(np.maximum(env, np.finfo(float).eps))
    plt.plot(t[skip:], level - level.mean(), label=label)
for lim in (0.07, -0.07):
    plt.axhline(lim, linestyle="--", color="gray")
plt.xlabel("Time [s]")
plt.ylabel("F-weighted level re mean [dB]")
plt.legend()
plt.show()
```

</details>

### `sensitivity()` parameters

| Parameter | Type / shape | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `ref_signal` | 1D/2D array | digital units | non-empty, non-silent | Recording of the calibration tone only (trim handling noise) |
| `target_spl` | float | dB re 20 µPa | default `94.0` | The calibrator's nominal level (114 dB calibrators: pass `114.0`) |
| `reference_pressure_pa` | float | Pa | default `2e-5` | Reference pressure $p_0$; rarely changed |
| `fs` | int, optional | Hz | > 0; default `None` | Required for the stability validation; omit to skip it |
| `validate` | bool | — | default `True` | Emit `CalibrationWarning` on unstable/short recordings; needs `fs`, and does nothing without it |
| `max_fluctuation_db` | float, optional | dB | default `None` → Table 2, by class and frequency | Explicit override of the stability limit |
| `frequency` | float | Hz | default `1000.0` | Calibrator's nominal frequency; selects the IEC 60942 Table 2 row |
| `calibrator_class` | str | — | `'LS'`, `'LS/M'`, `'1'`, `'1/M'`, `'2'`; default `'1'` | Calibrator's class designation (Table 1); selects the Table 2 column |
| `narrowband` | bool | — | default `False` | Estimate the tone with a coherent Goertzel detector near `frequency` (needs `fs`) instead of full-band RMS; rejects broadband hum/noise that otherwise inflates the RMS and shrinks every later level (~−0.44 dB at 20 dB SNR). Enable for noisy coupler recordings |

Returns the sensitivity factor (float) to pass as `calibration_factor=` to
`leq`, `laeq`, `ln_levels`, `lc_peak`, `sel` and the dose functions, and as
`calibration=LevelCalibration(factor=...)` to `octave_filter`.

## Field checks, laboratory verification and drift

Calibration lives at three time scales:

- **Every session: the field check.** Couple the calibrator and derive the
  sensitivity before each measurement series, and check it again at the end.
  Normative methods make the second check mandatory and use the pre/post
  difference as a validity gate (a common criterion invalidates the series
  when the two differ by more than 0.5 dB). Whatever the threshold, the
  difference is your drift bound for everything captured in between; carry
  it into the uncertainty budget rather than assuming zero.
- **Periodically: laboratory verification.** A field check only compares the
  chain against the calibrator; it cannot see an error the calibrator and
  meter share, and it says nothing about the response away from 1 kHz.
  IEC 61672-3 defines the periodic tests for the meter (weightings,
  level linearity and ballistics spot-checked against the class limits),
  and IEC 60942 the corresponding tests for the calibrator itself; typical
  laboratory intervals are one to two years.
- **Between checks: drift.** Microphone sensitivity moves with temperature,
  humidity and capsule aging; electronics with battery voltage. A healthy
  class 1 chain drifts a few hundredths of a dB over a session, which is
  why a pre/post difference of half a decibel signals damage rather than
  weather. The largest "drift" of all is a touched gain knob: the factor
  $S$ is valid only while the chain stays exactly as calibrated.

One more class subtlety: tolerances chain. A class 1 measurement requires a
class 1 (or LS) calibrator *and* a class 1 meter; calibrating a class 1
chain with a class 2 calibrator silently downgrades every derived level to
class 2 accuracy, because the calibrator's wider level tolerance enters
$S$ directly.

## Verifying the calibrator itself (IEC 60942:2017)

A field check compares the chain with the calibrator and trusts the calibrator.
What earns that trust is a laboratory's verdict on it, and IEC 60942:2017 says
how the verdict is reached: every requirement is a measured deviation with an
acceptance limit, measured with an expanded uncertainty no larger than a maximum
the standard also prints. `metrology.verify_sound_calibrator` takes what the
laboratory measured and gives that verdict, one requirement at a time; it
measures nothing itself.

| Requirement | Clause | Acceptance limit | Maximum uncertainty | Class 1 at 1 kHz |
| :--- | :--- | :--- | :--- | :--- |
| `level` | 5.3.2 | Table 2 | Table A.1 | ±0.25 dB; 0.15 dB |
| `fluctuation` | 5.3.3 | Table 2 | Table A.1 | 0.07 dB; 0.03 dB |
| `frequency` | 5.4.2 | Table 4 | Table A.2 | ±0.7 %; 0.2 % |
| `distortion` | 5.6 | Table 7 | Table A.3 | 2.5 %; 0.5 % |
| `supply_voltage` | 5.3.4 | Table 3 | A.5.5.7 | ±0.06 dB; 0.04 dB |
| `environmental_level` | 5.5 | Table 5 | Table A.4 | ±0.25 dB; 0.15 dB |
| `environmental_level_in_band` | A.6.2.4 | Table 2 | Table A.4 | ±0.25 dB; 0.15 dB |
| `environmental_frequency` | 5.5 | Table 6 | Table A.5 | ±0.7 %; 0.2 % |
| `field_immunity` | 5.9.4.2 | 5.9.4.2 | A.7.4.8 | ±0.25 dB; 0.05 dB |

The level is the mean of at least three couplings (A.5.5.3), and the level at
each end of the supply range goes into `level_deviation_db` too, because 5.3.4
holds it to Table 2 as well as to Table 3. The static-pressure sweep of A.6.2 is
graded against Table 2 inside the band of 5.3.2 (97 kPa to 105 kPa) and against
Table 5 outside it (A.6.2.4), so its in-band points go into
`environmental_level_in_band` and the rest into `environmental_level`.

Each is judged by the conformance rule the IEC TC 29 instrument standards
written since 2013 share (5.1.15): the deviation within its acceptance limit
**and** the uncertainty within its maximum, both inclusive
(`metrology.verify_conformance`, worked through the printed examples in
[Compliance and verification](compliance-verification.md)).

```python
from phonometry import metrology

record = metrology.SoundCalibratorMeasurements(
    level_deviation_db=0.12, level_uncertainty_db=0.10,
    fluctuation_db=0.02, fluctuation_uncertainty_db=0.02,
    frequency_deviation_percent=-0.05, frequency_uncertainty_percent=0.02,
    distortion_percent=0.9, distortion_uncertainty_percent=0.3,
)
result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
print(result.passes)                                     # True

# The same 0.12 dB, measured elsewhere with 0.17 dB of expanded uncertainty.
other_lab = metrology.SoundCalibratorMeasurements(
    level_deviation_db=0.12, level_uncertainty_db=0.17)
verdict = metrology.verify_sound_calibrator("1", other_lab, nominal_frequency_hz=1000.0)
print(verdict.passes)                                    # False
print(verdict.requirement("level").verifications[0].reason)
# Deviation within acceptance limits BUT uncertainty exceeds maximum-permitted
```

The second verdict is the rule, not the calibrator: a laboratory whose
uncertainty exceeds the 0.15 dB of Table A.1 cannot demonstrate anything about a
class 1 level (5.1.16), and another laboratory may pass the same calibrator.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/calibrator_verification_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/calibrator_verification.svg" alt="Horizontal bars for a class 1 calibrator at 1 kHz, two per measurement: the deviation as a share of its acceptance limit and the expanded uncertainty as a share of its maximum; only the third environmental level reading, 0.28 dB against 0.25 dB, crosses the 100 percent line, and its bar is drawn in red, which the legend names" width="92%"></picture>

Every limit is read from a published, read-only table (`LEVEL_ACCEPTANCE_LIMITS_DB`,
`FLUCTUATION_ACCEPTANCE_LIMITS_DB`, the other acceptance tables and the Annex A
maxima beside them). Classes LS and 2 are specified from 160 Hz to 1.25 kHz only,
and at any other nominal frequency the verifier refuses the class (5.1.2). A
class LS/M or 1/M pistonphone takes the manufacturer's static-pressure correction
as `static_pressure_correction_db`, added to the measured level (5.3.2, B.4.3.2),
and every other calibrator is refused one (5.1.7).
`environmental_test="abbreviated"` applies the reduced limits of A.6.4.7, where
a failure calls for the full environmental tests rather than a non-conformance.
The markings, stabilization time, supply indicator, radio-frequency emissions
and electrostatic discharges of IEC 60942 are hardware and paperwork checks
outside the verdict, and full conformance needs both the pattern evaluation of
Annex A and the periodic tests of Annex B (5.1.18).

## Digital Analysis (dBFS)

If you are working with digital audio files (e.g., WAV, FLAC) and want to
analyze levels relative to Full Scale rather than physical pressure, you can use
the `dbfs=True` parameter.

In this mode:

* **0 dBFS** corresponds to a numeric signal level of 1.0 (RMS or Peak).
* The calibration factor does not apply (dBFS is relative to digital full scale).
* Useful for analyzing headroom, digital mastering, or normalized signals.

```python
import numpy as np
from phonometry import filters

fs = 48000
# recording: the mic capture you want to calibrate, same input chain (Pa after calibration).
#   Synthesized here; in a real measurement this is your recorded signal.
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# Assume 'recording' is normalized between -1.0 and 1.0
filtered = filters.octave_filter(
    recording, fs, calibration=filters.LevelCalibration(dbfs=True))
spl_dbfs, freq = filtered.levels, filtered.frequencies
# Results will be negative (e.g., -20 dBFS)
```

## RMS vs Peak Levels

phonometry supports two measurement modes to align with professional software
like BK:

- **RMS (`mode='rms'`)**: Energy-based level (standard).
- **Peak (`mode='peak'`)**: Absolute maximum value reached in the frame
  (Peak-holding).

```python
import numpy as np
from phonometry import filters

fs = 48000
# recording: the mic capture you want to calibrate, same input chain (Pa after calibration).
#   Synthesized here; in a real measurement this is your recorded signal.
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# Measure peak-holding levels for impact analysis
filtered = filters.octave_filter(recording, fs, mode='peak')
spl_peak, freq = filtered.levels, filtered.frequencies
```

> [!NOTE]
> `mode='peak'` measures the absolute maximum of the **filtered** band signal,
> which includes the filter's onset transient (overshoot). Signals that start
> abruptly may read up to ~1 dB high. This is inherent to IIR band filters
> (an analog SLM behaves the same way), not a processing artifact.

## Integer audio input

Integer signals (e.g. int16 from `scipy.io.wavfile.read`) are converted to
float64 internally before any squaring, so calibration and level results are
identical whether you pass the raw integer array or a float conversion.

## Quick answers

### What calibrator level should I use to calibrate my measurement chain?

The usual choice is 94 dB SPL at 1 kHz (1 Pa RMS), which is what `sensitivity()` assumes with its default `target_spl=94.0`; for a 114 dB calibrator pass `114.0`. IEC 60942 requires the principal level to be at least 90 dB re 20 µPa. Record a few seconds of stable tone, because the standard specifies the generated level as a 20 s average.

### How much drift between the pre and post calibration checks is acceptable?

Derive the sensitivity before each measurement series and check it again at the end: a common criterion invalidates the series when the two differ by more than 0.5 dB. A healthy class 1 chain drifts a few hundredths of a dB over a session, so a half-decibel pre/post difference signals damage rather than weather. Whatever the threshold, carry the difference into the uncertainty budget rather than assuming zero.

### Can I calibrate a class 1 chain with a class 2 calibrator?

You can, but the tolerances chain: a class 1 measurement requires a class 1 (or LS) calibrator per IEC 60942 and a class 1 meter, so a class 2 calibrator silently downgrades every derived level to class 2 accuracy, because its wider level tolerance enters the sensitivity factor $S$ directly. For reference, the class 1 tolerance limit is ±0.4 dB between 160 Hz and 1.25 kHz: the 0.25 dB acceptance limit of IEC 60942:2017 Table 2 plus the 0.15 dB maximum-permitted uncertainty of Table A.1, combined as Annex D describes.

### How do I check that my calibrator conforms to IEC 60942?

Take the laboratory's results (each measured deviation with the expanded uncertainty it was measured with) into a `metrology.SoundCalibratorMeasurements` and call `metrology.verify_sound_calibrator` with the class and the nominal frequency. Each requirement is judged by the conformance rule of 5.1.15: the deviation within the Table 2 to 7 limit and the uncertainty within the Annex A maximum, both inclusive.

## See also

- [Build a sound level meter](../sound-level-meter.md): the walkthrough that starts from this calibration step and ends at a class-checked instrument.
- [Levels](../levels/levels.md): every metric that consumes the `calibration_factor` derived here.
- [Multichannel and Performance](../filters/multichannel.md): one sensitivity per channel when the channels differ.
- [GUM uncertainty](gum-uncertainty.md): propagating the calibrator tolerance and drift bound into a level's uncertainty.
- [Compliance and verification](compliance-verification.md): the conformance rule of IEC TC 29 the calibrator verdict is reached by.
- API reference: [`metrology.calibration`](https://jmrplens.github.io/phonometry/reference/api/metrology/calibration/), [`metrology.sound_calibrator`](https://jmrplens.github.io/phonometry/reference/api/metrology/sound-calibrator/), [`metrology.conformance`](https://jmrplens.github.io/phonometry/reference/api/metrology/conformance/) and [`phonometry`](https://jmrplens.github.io/phonometry/reference/api/filters/phonometry/).

## References

- International Electrotechnical Commission. (2017). *Electroacoustics —
  Sound calibrators* (IEC 60942:2017).
  [IEC webstore](https://webstore.iec.ch/en/publication/30045).
  The calibrator classes, the acceptance limits and maximum-permitted
  uncertainties `verify_sound_calibrator` grades a calibrator against, and the
  short-term stability criterion `sensitivity()` applies to the reference
  recording.
- International Electrotechnical Commission. (2013). *Electroacoustics —
  Sound level meters — Part 3: Periodic tests* (IEC 61672-3:2013).
  [IEC webstore](https://webstore.iec.ch/en/publication/5710).
  The laboratory verification procedure behind the periodic checks
  recommended above.
- Bies, D. A., Hansen, C. H., & Howard, C. Q. (2017). *Engineering noise
  control* (5th ed.). CRC Press.
  [doi:10.1201/9781351228152](https://doi.org/10.1201/9781351228152).
  Sections 3.1.5 and 3.4 (microphone field effects and sound level meter
  calibration: the electrical and acoustic calibration practice this
  page's workflow follows). ISBN 978-1-4987-2405-0.

## Standards

IEC 60942:2017, *Electroacoustics — Sound calibrators*: the
calibrator level and class assumptions behind `sensitivity()` (the 94 dB
principal level, the Table 1 classes and the Table 2 and Table A.1 limits), the
short-term level-fluctuation stability check of the reference recording (5.3.3,
Table 2 limits per class and nominal frequency), and every requirement with an
acceptance limit that `verify_sound_calibrator` grades (Tables 2 to 7, Tables
A.1 to A.5, 5.9.4.2, A.6.4.7) by the conformance rule of 5.1.15.

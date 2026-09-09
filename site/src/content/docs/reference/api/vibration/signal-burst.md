---
title: "vibration.human.signal_burst"
description: "The saw-tooth signal burst of ISO 8041-1:2017, 5.9, and what a meter reads."
sidebar:
  label: "signal_burst"
---

The saw-tooth signal burst of ISO 8041-1:2017, 5.9, and what a meter reads.

Clause 5.9 is the one place where ISO 8041-1 prints an oracle instead of a
requirement. It defines a test signal in Table 6 (folio 17), and then prints
in Tables 7, 8 and 9 (folios 17, 18 and 19) the 228 indications a conforming
human-vibration meter has to show when that signal is applied, each with the
tolerance it is judged against. The standard says where those numbers come
from: "NOTE 1 The response to the saw-tooth signal burst is determined by
digital simulation of the filter characteristics" (folio 16). They are
arithmetic, so a library that implements the weightings and the four
indication quantities can reproduce them, and this module does.

**The signal.** Figure 3 (folio 17) draws it: a bipolar saw-tooth of
amplitude 1 m/s2 from zero to peak, a linear rising ramp and a vertical fall,
with every burst starting at an upward zero crossing and ending at one. That
geometry is load-bearing rather than decorative: a burst started at the peak
reads 28 % high on the single-cycle row of Table 8, four times its tolerance.
Table 6 supplies the rest, per application: the angular frequency, the start
time of the first burst, the burst lengths (1, 2, 4, 8 and 16 cycles, plus a
continuous row), the repeat time and the measurement duration. Six bursts fit
in the printed duration in all three applications.

**Three conventions the tables do not print**, each fixed here by measuring
which reading reproduces the page:

1. *The continuous row starts at t = 0* and fills the printed duration; it
   does not start at the Table 6 start time. Read from zero, the band-limiting
   continuous cell of Table 7 comes out 0,564 9 against the 0,565 printed;
   started at 0,2 s it comes out 0,560 1.
2. *The filtering is zero state.* [`apply_weighting`](/phonometry/reference/api/vibration/exposure/#apply_weighting)
   multiplies in the frequency domain without padding, which is a circular
   convolution, and its own docstring says so. In the continuous row that
   wraps the tail of the record onto its front and erases the switch-on
   transient the linear MTVV is built to catch: filtered circularly, four
   continuous cells of Table 8 sit at Wc -0,81 %, Wm -1,10 %, Wd -3,24 % and
   We -5,19 %; filtered from rest they sit at -0,17 %, -0,31 %, -0,36 % and
   -0,52 %. This module therefore pads the record with zeros before applying
   the response and keeps the first samples back, which is a filter switched
   on at t = 0 with nothing stored in it. The default behaviour of
   [`apply_weighting`](/phonometry/reference/api/vibration/exposure/#apply_weighting) is deliberately left alone:
   the choice belongs to this test, not to every weighted signal.
3. *The MTVV integration time is 1 s* (ISO 2631-1 6.3.1, and the constant
   Annex D of this standard is written around). With any other constant the
   two MTVV columns stop lining up. It is also why the continuous row of the
   linear MTVV repeats the 16-cycle value for whole-body vibration: 16 cycles
   at 15,915 Hz last 1,005 s, so the burst already fills the window.

**Which band limiting the band-limiting row is.** 5.6.6 (folio 14) makes the
band-limiting response a graded quantity of its own, and Tables 7 to 9 give it
18 of their 72 rows. Six of the seven whole-body weightings share the corner
pair 0,4 Hz and 100 Hz of Table 3 and `Wm` does not, so the whole-body row
had to be decided by measurement as well: with the shared pair the 24 printed
cells reproduce to -0,25 % at worst, with the `Wm` pair to +0,67 %. The
hand-arm and low-frequency rows have only one candidate each, `Wh` and
`Wf`.

**What the reproduction is worth.** At the sampling rates recommended per
application, all 228 printed cells come out within 2,3 %, against printed
tolerances of 10 % and 12 %. The three widest are the 2-cycle row of `Wf`
and the 8-cycle row of `We`, cells the page prints to three significant
figures and whose weightings attenuate hardest.

**What a pass means.** The signal-burst response is one clause of a standard
that also grades indication, linearity, overload, timing and environmental
behaviour. A verdict here says the time response of the weighting chain
matches the printed table, and nothing else.

ISO 8041-2:2021 5.9 (folio 11) repeats this clause for personal vibration
exposure meters with the same Table 6 and the same Tables 7 to 9, so one
implementation covers both parts.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## BAND_LIMITING

*Constant* (`str`).

```python
BAND_LIMITING = 'band-limiting'
```

## BURST_TOLERANCE_PERCENT

*Constant* (`dict`).

```python
BURST_TOLERANCE_PERCENT = {'rms': 10.0, 'vdv': 12.0, 'mtvv_linear': 10.0, 'mtvv_exponential': 10.0, 'msdv': 10.0}
```

## sawtooth_burst

```python
sawtooth_burst(
    application: str,
    cycles: int | None,
    *,
    fs: float | None = None,
    amplitude_m_s2: float = 1.0,
) -> NDArray[np.float64]
```

The saw-tooth burst record of ISO 8041-1 Table 6 (folio 17).

The full measurement record: zero everywhere except during the bursts,
which start at `start_time_s` and repeat every `repeat_time_s` until
the printed duration runs out (six bursts, in all three applications).
Each burst is `cycles` whole saw-tooth periods, rising linearly from an
upward zero crossing to `+amplitude_m_s2`, falling vertically to
`-amplitude_m_s2` and ending back at zero, which is the waveform of
Figure 3.

`cycles=None` returns the continuous row of Tables 7 to 9 instead: an
unbroken saw-tooth from `t = 0` to the end of the printed duration. The
start time does not apply to it, and the reason is measured rather than
printed: read from zero, the band-limiting continuous cell of Table 7
comes out 0,564 9 against the 0,565 printed, and read from the start time
it comes out 0,560 1.

The fall is vertical, as Figure 3 draws it. 12.13 (folio 36) allows a real
generator a fall time of up to `1/(5 f2)`, which is
[`SawtoothBurstTest.max_fall_time_s`](/phonometry/reference/api/vibration/signal-burst/#sawtoothbursttest), and that allowance describes
the laboratory rig, not this record.

**Parameters**

| Name | Description |
| :--- | :--- |
| `application` | One of the keys of [`SAWTOOTH_BURST_TESTS`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst_tests). |
| `cycles` | Saw-tooth cycles per burst (1, 2, 4, 8 or 16), or `None` for the continuous row. |
| `fs` | Sampling frequency, in hertz. Finite, positive, and above twice the upper band-limiting corner of the weighting under test, below which the pass band is not represented and the indications would be an artefact of the sampling. `None` takes the recommended rate of the application. |
| `amplitude_m_s2` | Zero-to-peak amplitude, in m/s2. The printed responses are for 1 m/s2 and scale with it. |

**Returns:** The record, in m/s2, `round(duration_s * fs)` samples long.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the application, the burst length or the sampling rate is not one this clause defines, or the amplitude is not finite and positive. |
| TypeError | If `cycles` is neither an integer nor `None`. |

## SAWTOOTH_BURST_TESTS

*Constant* (`dict`).

```python
SAWTOOTH_BURST_TESTS = {'hand-arm': SawtoothBurstTest(application='hand-arm', weightings=('Wh',), band_limiting_weighting='Wh', angular_frequency_rad_s=500.0, start_time_s=0.2, cycle_counts=(1, 2, 4, 8, 16), repeat_time_s=2.0, duration_s=12.0, max_fall_time_s=0.00015886564694485628, recommended_sampling_rate_hz=200000.0), 'whole-body': SawtoothBurstTest(application='whole-body', weightings=('Wb', 'Wc', 'Wd', 'We', 'Wj', 'Wk', 'Wm'), band_limiting_weighting='Wb', angular_frequency_rad_s=100.0, start_time_s=1.0, cycle_counts=(1, 2, 4, 8, 16), repeat_time_s=10.0, duration_s=60.0, max_fall_time_s=0.002, recommended_sampling_rate_hz=20000.0), 'low-frequency-whole-body': SawtoothBurstTest(application='low-frequency-whole-body', weightings=('Wf',), band_limiting_weighting='Wf', angular_frequency_rad_s=2.5, start_time_s=40.0, cycle_counts=(1, 2, 4, 8, 16), repeat_time_s=400.0, duration_s=2400.0, max_fall_time_s=0.31746031746031744, recommended_sampling_rate_hz=200.0)}
```

## SawtoothBurstTest

```python
SawtoothBurstTest(
    application: str,
    weightings: tuple[str, ...],
    band_limiting_weighting: str,
    angular_frequency_rad_s: float,
    start_time_s: float,
    cycle_counts: tuple[int, ...],
    repeat_time_s: float,
    duration_s: float,
    max_fall_time_s: float,
    recommended_sampling_rate_hz: float,
)
```

One application's row of ISO 8041-1 Table 6 (folio 17).

**Attributes**

| Name | Description |
| :--- | :--- |
| `application` | The application key, as [`SAWTOOTH_BURST_TESTS`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst_tests) files it. |
| `weightings` | The frequency weightings the application is tested with, in Table 6 order. |
| `band_limiting_weighting` | The weighting whose Table 3 corners are the band-limiting response of this application's band-limiting row. |
| `angular_frequency_rad_s` | The saw-tooth angular frequency, in radians per second, which is what the table prints. |
| `start_time_s` | When the first burst starts, in seconds. |
| `cycle_counts` | The printed burst lengths, in saw-tooth cycles. |
| `repeat_time_s` | The interval between burst starts, in seconds. |
| `duration_s` | The measurement duration, in seconds. |
| `max_fall_time_s` | The largest fall time 12.13 allows a real generator, in seconds. The record [`sawtooth_burst`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst) synthesises has the ideal vertical fall of Figure 3; this is the laboratory limit, not a property of the synthesised signal. |
| `recommended_sampling_rate_hz` | The rate [`sawtooth_burst`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst) uses when the caller names none. Chosen so that the printed cells are reproduced to a few tenths of a per cent, which is not a normative figure: nothing in the standard prescribes a sampling rate. |

### SawtoothBurstTest.burst_count

*property*

How many bursts the printed duration holds at the repeat time.

### SawtoothBurstTest.frequency_hz

*property*

The saw-tooth frequency, in hertz.

Table 6 prints it beside the angular frequency (79,58 Hz, 15,915 Hz
and 0,397 9 Hz); this is the division, not the rounded decimal.

## signal_burst_indications

```python
signal_burst_indications(
    application: str,
    name: str,
    cycles: int | None,
    *,
    fs: float | None = None,
) -> dict[str, float]
```

What a conforming meter indicates for one row of Tables 7 to 9.

Runs the library chain the standard describes: the burst of
[`sawtooth_burst`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst), the weighting (or the band-limiting response) of
ISO 8041-1 Table 3 applied from rest, and then the indication quantities
the table for that application prints, over the whole measurement
duration. The MTVV columns are the maximum of the running r.m.s. of
ISO 2631-1 Eq. (4) with the 1 s integration time this clause implies, in
the linear and the exponential average of Annex D.

**Parameters**

| Name | Description |
| :--- | :--- |
| `application` | One of the keys of [`SAWTOOTH_BURST_TESTS`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst_tests). |
| `name` | A weighting of that application, or [`BAND_LIMITING`](/phonometry/reference/api/vibration/signal-burst/#band_limiting) for the band-limiting row. |
| `cycles` | Saw-tooth cycles per burst (1, 2, 4, 8 or 16), or `None` for the continuous row. |
| `fs` | Sampling frequency, in hertz. Finite, positive, and above twice the upper band-limiting corner of the weighting under test, below which the pass band is not represented and the indications would be an artefact of the sampling. `None` takes the recommended rate of the application. |

**Returns:** The indications for a 1 m/s2 amplitude burst, keyed by the printed column names of that application's table (`"rms"`, `"vdv"`, `"mtvv_linear"`, `"mtvv_exponential"`, `"msdv"`), in the units of each quantity.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | As for [`sawtooth_burst`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst), and if the weighting belongs to another application. |
| TypeError | If `cycles` is neither an integer nor `None`. |

## SIGNAL_BURST_RESPONSE

*Constant* (`dict`).

## SignalBurstVerification

```python
SignalBurstVerification(
    application: str,
    weighting: str,
    amplitude_m_s2: float,
    cycle_counts: tuple[int | None, ...],
    quantities: tuple[str, ...],
    measured: NDArray[np.float64],
    printed: NDArray[np.float64],
    deviation_percent: NDArray[np.float64],
    tolerance_percent: NDArray[np.float64],
    within_tolerance: NDArray[np.bool_],
)
```

A meter's signal-burst indications against ISO 8041-1 Tables 7 to 9.

**Attributes**

| Name | Description |
| :--- | :--- |
| `application` | The application whose table was used. |
| `weighting` | The row that was graded, a weighting name or [`BAND_LIMITING`](/phonometry/reference/api/vibration/signal-burst/#band_limiting). |
| `amplitude_m_s2` | The zero-to-peak amplitude of the test signal the printed responses were scaled by. |
| `cycle_counts` | The burst lengths that were graded, in printed order, with `None` for the continuous row. |
| `quantities` | The columns that were graded, in printed order. |
| `measured` | The indications as supplied, one row per burst length and one column per quantity. |
| `printed` | The Table 7, 8 or 9 cells they are judged against, scaled by `amplitude_m_s2`. |
| `deviation_percent` | `(measured / printed - 1) * 100`, elementwise. |
| `tolerance_percent` | The printed tolerance of each column, from [`BURST_TOLERANCE_PERCENT`](/phonometry/reference/api/vibration/signal-burst/#burst_tolerance_percent). |
| `within_tolerance` | Whether each cell is inside its tolerance. |

### SignalBurstVerification.passes

*property*

Whether every graded cell is inside its printed tolerance.

True says the time response of this weighting chain matches the
printed table. Clause 5.9 is one of the clauses a meter is graded on,
and the others are hardware measurements this cannot stand in for.

### SignalBurstVerification.plot()

```python
SignalBurstVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the deviations against the printed tolerance band.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the marker series. |

**Returns:** The axes.

### SignalBurstVerification.worst_deviation_percent

*property*

The largest deviation in magnitude, signed as it was measured.

## verify_signal_burst_response

```python
verify_signal_burst_response(
    application: str,
    name: str,
    measured: Mapping[int | None, Mapping[str, float]],
    *,
    amplitude_m_s2: float = 1.0,
) -> SignalBurstVerification
```

Check measured burst indications against ISO 8041-1 Tables 7 to 9.

The acceptance test of 12.13 (folio 36): "The vibration values indicated
in response to the signal bursts, relative to the values of the vibration
amplitude of the input signal, shall be as specified in Table 7, 8 or 9",
within the tolerance printed beside each column.

5.9 (folio 16) says the printed responses "are relative to a 1 m/s2
amplitude signal and shall be multiplied by the amplitude of the actual
test signal", and every one of the five quantities is homogeneous of
degree one in the signal, so `amplitude_m_s2` scales the printed side
exactly.

**Parameters**

| Name | Description |
| :--- | :--- |
| `application` | One of the keys of [`SAWTOOTH_BURST_TESTS`](/phonometry/reference/api/vibration/signal-burst/#sawtooth_burst_tests). |
| `name` | A weighting of that application, or [`BAND_LIMITING`](/phonometry/reference/api/vibration/signal-burst/#band_limiting). |
| `measured` | The indications, keyed by burst length (`None` for the continuous row) and then by printed column name. Every row has to report the same columns, so that the verdict is a rectangle rather than a ragged set. |
| `amplitude_m_s2` | The zero-to-peak amplitude of the test signal, in m/s2. |

**Returns:** The verdict, as a [`SignalBurstVerification`](/phonometry/reference/api/vibration/signal-burst/#signalburstverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the application, the weighting or a burst length is not one this clause defines, if a column is not printed for that application, if the rows disagree about which columns they report, if `measured` is empty, if an indication is negative or not finite, or if the amplitude is not finite and positive. |
| TypeError | If a burst length is neither an integer nor `None`. |

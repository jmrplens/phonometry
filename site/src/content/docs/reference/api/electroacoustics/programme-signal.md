---
title: "electroacoustics.programme_signal"
description: "The simulated programme signal of IEC 60268-1:1985, Clause 7."
sidebar:
  label: "programme_signal"
---

The simulated programme signal of IEC 60268-1:1985, Clause 7.

A loudspeaker, an amplifier or a headphone is rated with one tone at a time,
but it is used with programme: speech and music, whose power is spread over
the whole audio band and concentrated in its middle. IEC 60268-1:1985 Clause 7
defines a noise that stands in for that programme in a measurement, the
**simulated programme signal**:

    A signal, whose mean power spectral density closely resembles the average
    of the mean power spectral densities of a wide range of programme
    material, including both speech and music of several kinds, is stationary
    weighted Gaussian noise without amplitude limiting, the weighted power
    spectrum being in accordance with Table II and Figure 1, page 22, when
    measured with third-octave filters in accordance with IEC Publication 225.

Table II gives the relative level of each one-third-octave band from 20 Hz to
20 kHz with its tolerance: 0 dB from 250 Hz to 800 Hz, falling to
$-13{,}5$ dB at 20 Hz and $-21{,}6$ dB at 20 kHz
([`SIMULATED_PROGRAMME_SPECTRUM`](/phonometry/reference/api/electroacoustics/programme-signal/#simulated_programme_spectrum)). The Note under the clause adds that the
power of the whole signal is about 12,5 dB above the 0 dB of one band, which is
the power sum of the 31 relative levels, 12,56 dB.

The filter of Figure 2
----------------------

"Such a signal may be obtained from a pink-noise source by means of the filter
circuit shown in Figure 2." The circuit is a passive ladder of five
capacitors driven from the e.m.f. of the pink-noise source through 430 ohm,
which includes the source's own output impedance:

* a series 2,2 µF capacitor into a node shunted by 3,3 kohm and 91 nF;
* a series 330 ohm and 2,2 µF into a node shunted by 3,3 kohm and 68 nF;
* a series 0,47 µF into the 10 kohm output resistor, loaded by at least
  100 kohm; "the effect of the load impedance may be taken into account by
  adjusting the value of the 10 kohm resistor", so the 10 kohm is the whole
  shunt the network sees.

[`programme_signal_filter`](/phonometry/reference/api/electroacoustics/programme-signal/#programme_signal_filter) is the exact transfer function of that ladder,
the voltage across the 10 kohm over the source e.m.f., from its nodal
equations. The two 2,2 µF capacitors with the resistors behind them make the
low-frequency roll-off and the 91 nF and 68 nF shunts the high-frequency one;
the passband loss is about 4 dB. Pink noise has equal power in every
one-third-octave band, so the band levels of its output are the power average
of $|H|^2$ over each band, and in ideal one-third-octave bands they fall
inside every tolerance of Table II once the level is set: the worst band is
the 5 kHz one, 1,1 dB below its printed level against a tolerance of 1 dB
when the 0 dB of the table is put on the 630 Hz band, and 0,18 dB inside it
with the level that centres the whole curve in the tolerances. Figure 2 is a
realisation within tolerance, not the definition: the definition is Table II.

The generator
-------------

[`simulated_programme_signal`](/phonometry/reference/api/electroacoustics/programme-signal/#simulated_programme_signal) synthesises the signal in the frequency
domain: a white Gaussian spectrum, shaped and transformed back to a record
that is stationary and Gaussian, as the clause asks, at any sample rate and
with no bilinear warping near the Nyquist frequency. It offers two shapes.
The default puts every band on Table II itself: a power spectral density that
is a straight line in decibels against the logarithm of frequency between the
band centres, whose nodes are set so that the power of each band, integrated
over it in closed form, is the printed level, and which carries on at the
slope of its end segments below 20 Hz and above 20 kHz. Every band then keeps
its whole tolerance for the fluctuation of a finite record. The other is the
circuit of Figure 2, pink noise of slope $f^{-1/2}$ in amplitude
multiplied by the complex response of the ladder; at 0,18 dB from its nearest
limit it leaves a short record little room, and a 20 s record at 48 kHz falls
outside the tolerance of the 31,5 Hz or 40 Hz band for some seeds.

The clause asks for the noise "without amplitude limiting". IEC 60268-7:2010
8.3.2 asks for the opposite when it rates the long-term maximum source e.m.f.
of a headphone: the programme signal "with additional clipping", with "a
peak-to-r.m.s ratio between 1,8 and 2,2". `peak_to_rms` clips the record at
the level that gives the requested ratio after clipping and rescales it.
Clipping spreads power into the weak upper bands: at a ratio of 2,0 it lifts
the 20 kHz band by about half a decibel against the middle of the spectrum,
inside its tolerance of 3 dB.

The verdict
-----------

[`check_programme_signal`](/phonometry/reference/api/electroacoustics/programme-signal/#check_programme_signal) judges one-third-octave band levels against
Table II. The table is a relative spectrum: its 0 dB is not a level the signal
has to reach, it is where the bands are referred to. The check therefore looks
for the level that places every band inside its tolerance. Each band allows a
window of levels, $[T_i - t_i^- - L_i,\ T_i + t_i^+ - L_i]$, and the
spectrum conforms when the windows overlap; the level reported is the middle
of the overlap, where the smallest margin is largest. Bands that are not
given are not judged, so a record sampled at 44,1 kHz, which cannot hold the
20 kHz band, is judged on the other 30.

Neither amendment of 1988 touches Clause 7: Amendment 1 replaces Table AII,
the tone-burst response of the quasi-peak meter of Appendix A, and
Amendment 2 replaces 12.1, the three coils that make a uniform magnetic field.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_programme_signal

```python
check_programme_signal(
    frequencies_hz: ArrayLike,
    band_levels_db: ArrayLike,
) -> ProgrammeSignalCheck
```

Is this one-third-octave spectrum the programme signal of IEC 60268-1?

Clause 7 asks for a weighted power spectrum "in accordance with Table II
and Figure 1 [...] when measured with third-octave filters". Table II is a
relative spectrum, so the band levels are judged up to a constant: the
spectrum conforms when one level places every band inside its tolerance
(see the module docstring). Only the bands given are judged.

The band levels can come from any one-third-octave analyser, for instance
[`phonometry.filters.octave_filter`](/phonometry/reference/api/filters/core/#octave_filter) with `fraction=3`, whose exact
band centres (19,95 Hz, 25,12 Hz, ...) are read as the nominal ones of the
table.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Band centre frequencies, in Hz, nominal or exact, each a band of Table II (20 Hz to 20 kHz) and none repeated. |
| `band_levels_db` | The band levels, in dB, on any reference. |

**Returns:** A [`ProgrammeSignalCheck`](/phonometry/reference/api/electroacoustics/programme-signal/#programmesignalcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs differ in length, a frequency is not a band of Table II or appears twice, a level is not finite, or fewer than two bands are given. |

## programme_signal_filter

```python
programme_signal_filter(frequencies_hz: ArrayLike) -> NDArray[np.complex128]
```

The transfer function of the filter of IEC 60268-1:1985 Figure 2.

The voltage across the 10 kohm output resistor over the e.m.f. of the
pink-noise source, from the nodal equations of the ladder (see the module
docstring for the circuit). The source's output impedance is part of the
first 430 ohm and the 10 kohm is the whole output shunt, the two
conventions the figure's notes state.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequencies, in Hz, any shape; each must be positive. |

**Returns:** The complex response, dimensionless, with the shape of `frequencies_hz`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a frequency is not a positive finite number. |

## ProgrammeSignalCheck

```python
ProgrammeSignalCheck(
    frequencies_hz: NDArray[np.float64],
    band_levels_db: NDArray[np.float64],
)
```

A one-third-octave spectrum judged against IEC 60268-1:1985 Table II.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The nominal frequencies of the bands judged, in Hz, ascending. |
| `band_levels_db` | The band levels as given, in dB, in the order of `frequencies_hz`. |

Table II's relative levels and tolerances at the bands, and the offset
that refers the levels to them, are read from the table, so a check
cannot be built against other tolerances.

### ProgrammeSignalCheck.binding_bands_hz

*property*

The bands at the smallest margin, in Hz.

The level is placed in the middle of the window every band allows, so
the smallest margin is reached by at least two bands, one against its
upper limit and one against its lower; those are the bands that fix
the verdict.

### ProgrammeSignalCheck.deviations_db

*property*

Each band's level, referred by `offset_db`, minus Table II, in dB.

### ProgrammeSignalCheck.margin_db

*property*

The smallest distance of a band from its nearer limit, in dB.

Negative when the spectrum cannot be placed inside the tolerances: its
magnitude is then the excursion of the worst band.

### ProgrammeSignalCheck.offset_db

*property*

The level added to the band levels to refer them to Table II, in dB.

The middle of the window of levels that keeps every band inside its
tolerance, or, when no level does, the level that shares the worst
excursion equally between the two sides.

### ProgrammeSignalCheck.passes

*property*

Whether some level places every band inside its tolerance.

### ProgrammeSignalCheck.plot()

```python
ProgrammeSignalCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the referred band levels inside the tolerances of Table II.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the band levels' `Axes.plot`. |

**Returns:** The axes.

### ProgrammeSignalCheck.relative_levels_db

*property*

Table II's relative levels at the bands, in dB.

### ProgrammeSignalCheck.tolerance_minus_db

*property*

The lower tolerances of Table II at the bands, in dB.

### ProgrammeSignalCheck.tolerance_plus_db

*property*

The upper tolerances of Table II at the bands, in dB.

## ProgrammeSpectrumBand

```python
ProgrammeSpectrumBand(
    relative_level_db: float,
    tolerance_plus_db: float,
    tolerance_minus_db: float,
)
```

One row of IEC 60268-1:1985 Table II.

**Attributes**

| Name | Description |
| :--- | :--- |
| `relative_level_db` | The relative level of the one-third-octave band, in dB. |
| `tolerance_plus_db` | The upper tolerance, in dB, as printed (a positive number). |
| `tolerance_minus_db` | The lower tolerance, in dB, as printed (a positive number). |

## simulated_programme_signal

```python
simulated_programme_signal(
    fs: int,
    seconds: float,
    *,
    rms: float = 1.0,
    spectrum: Literal['table', 'figure_2'] = 'table',
    peak_to_rms: float | None = None,
    seed: int | None = None,
) -> NDArray[np.float64]
```

The simulated programme signal of IEC 60268-1:1985 Clause 7.

Stationary Gaussian noise whose one-third-octave spectrum follows Table II,
synthesised in the frequency domain (see the module docstring). The record
is zero-mean and scaled to `rms` exactly.

Two realisations are offered. `"table"` (default) puts every band of
Table II on its printed level: the power spectral density is linear in
decibels against the logarithm of frequency between the band centres,
continued at the slope of the end segments below 20 Hz and above 20 kHz,
and its nodes are set so that each band's power, integrated over the band
in closed form, is the printed level. Every band then has its whole
tolerance for the random fluctuation of a finite record. `"figure_2"` is
pink noise through the filter of Figure 2 ([`programme_signal_filter`](/phonometry/reference/api/electroacoustics/programme-signal/#programme_signal_filter)),
the circuit the clause offers: inside the tolerances, but only 0,18 dB
inside at its worst band, so a short record can fall outside them.

The clause asks for the noise "without amplitude limiting", and so does
this by default. `peak_to_rms` clips it instead, for the limiting
voltages of IEC 60268-7:2010 8.3.2, which drive a headphone with the
programme signal "with additional clipping" and a peak-to-r.m.s. ratio
between 1,8 and 2,2: the record is clipped symmetrically at the level that
leaves exactly that ratio after clipping, then rescaled to `rms`.

A one-third-octave band at 20 Hz is 4,6 Hz wide, so its level fluctuates
by about $4{,}34/\sqrt{4{,}6\,T}$ dB over a record of $T$
seconds: 0,4 dB in 30 s. Table II allows 3 dB there; the 0,5 dB bands of
the middle need a few seconds.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate, in hertz. |
| `seconds` | Duration, in seconds. |
| `rms` | RMS value of the record, in whatever unit it is scaled to. |
| `spectrum` | `"table"` (default) for the band levels of Table II, `"figure_2"` for pink noise through the filter of Figure 2. |
| `peak_to_rms` | The ratio of the peak value to the RMS value after clipping, or `None` (default) for no clipping. It must be above 1 and below the ratio the unclipped record already has. |
| `seed` | Seed for `numpy.random.default_rng`; the same seed reproduces the same record. |

**Returns:** The signal, `round(fs * seconds)` samples.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an input is invalid, or `peak_to_rms` is not below the ratio of the unclipped record. |

## SIMULATED_PROGRAMME_SPECTRUM

*Constant* (`mapping`).

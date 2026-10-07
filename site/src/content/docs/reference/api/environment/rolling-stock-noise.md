---
title: "environment.sources.rolling_stock_noise"
description: "The noise a railway vehicle emits, measured by ISO 3095:2013."
sidebar:
  label: "rolling_stock_noise"
---

The noise a railway vehicle emits, measured by ISO 3095:2013.

ISO 3095 is the type test of rolling stock: how a train, a locomotive or a
wagon is measured so that two units measured on two tracks can be compared.
It has four tests and one condition that makes the constant-speed test
comparable at all, the track.

**Clause 5, standing still.** Microphones 7,5 m from the track centreline and
1,2 m high stand opposite the middle of equal areas 3 m to 5 m long along both
sides of every car, plus two at 30° on a 7,5 m half circle off each end of
the unit, only off the ends with a cab for a trailer unit (5.5.1.1). The
level $L^i_{p\mathrm{Aeq},T}$ of every position, over at least 20 s, is
energy averaged weighted by the length $l_i$ each position stands for,
$(\pi/2) \times 7{,}5$ m for the end positions
([`STATIONARY_END_POSITION_LENGTH_M`](/phonometry/reference/api/environment/rolling-stock-noise/#stationary_end_position_length_m)):

$$
\langle L_{p\mathrm{Aeq},T} \rangle_\mathrm{unit} = 10 \lg \left( \sum_{i=1}^{n} \frac{l_i}{l_\mathrm{tot}} 10^{L^i_{p\mathrm{Aeq},T}/10} \right), \qquad l_\mathrm{tot} = \sum_{i=1}^{n} l_i
$$

(Formulae 1 and 2, [`stationary_unit_level`](/phonometry/reference/api/environment/rolling-stock-noise/#stationary_unit_level); Formula 3 is the same over
one car). The result is the mean of three such sets rounded to the nearest
integer decibel (5.8.1, [`stationary_test`](/phonometry/reference/api/environment/rolling-stock-noise/#stationary_test)).

**Clause 6, at constant speed.** The pass-by level
$L_{p\mathrm{Aeq},T_p}$ is the A-weighted equivalent level over the
pass-by time $T_p$ of the unit, from its front to its rear for a fixed
formation (6.6.3, [`pass_by_measurement`](/phonometry/reference/api/environment/rolling-stock-noise/#pass_by_measurement)), at 7,5 m and 1,2 m, or 25 m
and 3,5 m at 200 km/h and above. Three runs per speed and side give a mean
rounded to the integer; the louder side is the result (6.7.1,
[`rolling_stock_test`](/phonometry/reference/api/environment/rolling-stock-noise/#rolling_stock_test)). The test speeds are 80 km/h and the maximum
speed, or the maximum alone up to 80 km/h (6.6.2, [`type_test_speeds`](/phonometry/reference/api/environment/rolling-stock-noise/#type_test_speeds)).
The 2005 edition also defined the **transit exposure level**, the energy of
a whole train's passage normalised to its pass-by time,

$$
\mathrm{TEL} = 10 \lg \left( \frac{1}{T_p} \int_0^T \frac{p_\mathrm{A}^2(t)}{p_0^2}\,\mathrm{d}t \right) = L_{p\mathrm{Aeq},T} + 10 \lg \frac{T}{T_p}
$$

(ISO 3095:2005, 3.14, Formulae 8 and 10, [`transit_exposure_level`](/phonometry/reference/api/environment/rolling-stock-noise/#transit_exposure_level)). The
2013 edition dropped it; its Annex B.4 keeps the same form, with the pass-by
time of half the unit, for a single trailer at the end of a train
(Formula B.1).

**Clauses 7 and 8, starting and braking.** Starting is measured two ways:
the maximum $L_{p\mathrm{AFmax}}$ at 7,5 m at a cross section 10 m ahead
of the unit and at further positions along a long unit
([`acceleration_test_positions`](/phonometry/reference/api/environment/rolling-stock-noise/#acceleration_test_positions)), or $L_{p\mathrm{Aeq},T}$ at
25 m over the passage of the unit. Braking from 30 km/h is measured by
$L_{p\mathrm{AFmax}}$ opposite the first car at standstill. Each takes
three runs per position, averages them, rounds to the integer and keeps the
highest (7.5.4, 7.6.4, 8.7). Three runs are valid when they are no more than
3 dB apart (9.3).

**6.2, the reference track.** A constant-speed result is comparable only on
a track whose rail roughness is below the limit of Figure 2 and whose decay
rates are above the limits of Figure 3, both printed as numbers on the page
([`REFERENCE_TRACK_ROUGHNESS_LIMIT_DB`](/phonometry/reference/api/environment/rolling-stock-noise/#reference_track_roughness_limit_db),
[`REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M`](/phonometry/reference/api/environment/rolling-stock-noise/#reference_track_decay_limits_db_per_m)). The roughness is measured by
EN 15610 ([`acoustic_roughness`](/phonometry/reference/api/environment/acoustic-roughness/)) and the
decay rates by EN 15461 ([`track_decay`](/phonometry/reference/api/environment/track-decay/));
[`check_reference_track`](/phonometry/reference/api/environment/rolling-stock-noise/#check_reference_track) brings the two together with the curve radius
and gradient of 6.2.2. A track whose roughness exceeds the limit in a few
bands can still be accepted by Annex C when the exceedance changes the
pass-by level by no more than 1 dB ([`check_small_roughness_deviations`](/phonometry/reference/api/environment/rolling-stock-noise/#check_small_roughness_deviations)),
and Annex E bounds how much two tracks' roughness could change a pass-by level
([`roughness_comparability`](/phonometry/reference/api/environment/rolling-stock-noise/#roughness_comparability)).

**The rest.** Annex A characterises impulsive noise by the fastest rise of
$L_{p\mathrm{AF}}(t)$ ([`impulsiveness_rise_speed`](/phonometry/reference/api/environment/rolling-stock-noise/#impulsiveness_rise_speed)); 6.3.4 accepts
a vehicle next to the unit under test when it adds no more than 2 dB
([`check_adjacent_vehicle_neutrality`](/phonometry/reference/api/environment/rolling-stock-noise/#check_adjacent_vehicle_neutrality)); Annex D.4.2 corrects for a
steady background ([`background_level_increase`](/phonometry/reference/api/environment/rolling-stock-noise/#background_level_increase)); and Annex G sums an
uncertainty budget whose example, Table G.2, is the numerical oracle of this
module ([`pass_by_uncertainty`](/phonometry/reference/api/environment/rolling-stock-noise/#pass_by_uncertainty)).

**Roundings.** 5.8.1, 6.7.1, 7.5.4, 7.6.4 and 8.7 round to the nearest integer
decibel and 6.3.4 to one decimal, without a rule for a value on the half; a
half goes up here, a convention of this module, and so does a mean that binary
arithmetic lands a hair under it (runs of 70,1 dB, 70,3 dB and 71,1 dB average
to 70,5 dB and give 71 dB).

Read from ISO 3095:2013 (third edition) and, for the transit exposure level,
BS EN ISO 3095:2005 (second edition).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## acceleration_test_positions

```python
acceleration_test_positions(unit_length_m: float) -> NDArray[np.float64]
```

Where the microphones of the maximum level starting test stand, 7.5.1.1.

One at the front cross section, 10 m ahead of the front of the unit. A
unit longer than 50 m also has one 10 m ahead of its middle, and when
those two are more than 50 m apart the gap is split into equal spacings of
no more than 50 m (Figure 10: a 108 m unit has positions 10 m ahead of it
and 17 m and 44 m behind its front).

**Parameters**

| Name | Description |
| :--- | :--- |
| `unit_length_m` | The length $l$ of the unit, in metres. |

**Returns:** The positions, in metres behind the front of the unit at standstill, the front cross section first at -10 m; read-only.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a length that is not positive. |

## AdjacentVehicleNeutrality

```python
AdjacentVehicleNeutrality(
    with_adjacent_level_db: float,
    unit_level_db: float,
)
```

Whether a vehicle next to the unit under test is acoustically neutral, 6.3.4.

**Parameters**

| Name | Description |
| :--- | :--- |
| `with_adjacent_level_db` | $L_{p\mathrm{Aeq},T_{p1}}$, over the units under test and the adjacent vehicle together, in dB. |
| `unit_level_db` | $L_{p\mathrm{Aeq},T_p}$, over the units under test alone, in dB. |

### AdjacentVehicleNeutrality.difference_db

*property*

How much the adjacent vehicle adds, from the levels rounded to one decimal, in dB.

### AdjacentVehicleNeutrality.passes

*property*

Whether the adjacent vehicle adds no more than 2,0 dB.

### AdjacentVehicleNeutrality.plot()

```python
AdjacentVehicleNeutrality.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the two levels and the 2 dB the adjacent vehicle may add.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the bars. |

**Returns:** The axes drawn on.

## background_level_increase

```python
background_level_increase(
    measured_level_db: ArrayLike,
    background_level_db: ArrayLike,
) -> float | NDArray[np.float64]
```

How much a steady background raises a measured level, Formula D.1.

$$
\Delta L = L_\mathrm{meas} - 10 \lg \left( 10^{L_\mathrm{meas}/10} - 10^{L_\mathrm{bg}/10} \right)
$$

The informative procedure of Annex D.4.2 for sites that cannot meet the
10 dB margin of 5.2.3, 6.1.3, 7.2.3 and 8.1.3; it is used only when the
level stands more than 3 dB above the background, and band by band for a
spectrum.

**Parameters**

| Name | Description |
| :--- | :--- |
| `measured_level_db` | $L_\mathrm{meas}$, the level measured with the unit, in dB; one value or one per band. |
| `background_level_db` | $L_\mathrm{bg}$, the background alone, in dB. |

**Returns:** $\Delta L$, in dB, as one value or one per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For levels that are not finite, of different lengths, or no more than 3 dB above the background. |

## check_adjacent_vehicle_neutrality

```python
check_adjacent_vehicle_neutrality(
    with_adjacent_level_db: float,
    unit_level_db: float,
) -> AdjacentVehicleNeutrality
```

Is the vehicle next to the unit under test acoustically neutral? 6.3.4.

It is when it is of the same class as the unit, or when the pass-by level
over the units under test and the adjacent vehicle,
$L_{p\mathrm{Aeq},T_{p1}}$, is no more than 2,0 dB above the level
over the units alone, $L_{p\mathrm{Aeq},T_p}$, both rounded to one
decimal for the comparison (Figure 5). This is the second test; it is
made at least once for each tested speed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `with_adjacent_level_db` | $L_{p\mathrm{Aeq},T_{p1}}$, in dB. |
| `unit_level_db` | $L_{p\mathrm{Aeq},T_p}$, in dB. |

**Returns:** The verdict.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a level that is not finite. |

## check_reference_track

```python
check_reference_track(
    roughness: Sequence[AcousticRoughnessSpectrum],
    decay_rates: Sequence[TrackDecayRate],
    *,
    speed_kmh: float,
    curve_radius_m: float | None = None,
    track_gradient_ratio: float | None = None,
    small_deviations: SmallRoughnessDeviation | None = None,
    roughness_limit_db: Mapping[float, float] = mappingproxy({0.4: 17.1, 0.315: 15.0, 0.25: 13.0, 0.2: 11.0, 0.16: 9.0, 0.125: 7.0, 0.1: 4.9, 0.08: 2.9, 0.063: 0.9, 0.05: -1.1, 0.04: -3.2, 0.0315: -5.0, 0.025: -5.6, 0.02: -6.2, 0.016: -6.8, 0.0125: -7.4, 0.01: -8.0, 0.008: -8.6, 0.0063: -9.2, 0.005: -9.8, 0.004: -10.4, 0.00315: -11.0}),
    decay_limits_db_per_m: Mapping[str, Mapping[float, float]] = mappingproxy({'vertical': mappingproxy({250.0: 2.0, 315.0: 2.0, 400.0: 6.0, 500.0: 6.0, 630.0: 6.0, 800.0: 2.19, 1000.0: 0.8, 1250.0: 0.8, 1600.0: 0.8, 2000.0: 0.8, 2500.0: 0.8, 3150.0: 0.8, 4000.0: 0.8, 5000.0: 0.8}), 'lateral': mappingproxy({250.0: 2.04, 315.0: 1.38, 400.0: 0.94, 500.0: 0.64, 630.0: 0.43, 800.0: 0.29, 1000.0: 0.2, 1250.0: 0.2, 1600.0: 0.32, 2000.0: 0.5, 2500.0: 0.5, 3150.0: 0.5, 4000.0: 0.5, 5000.0: 0.5})}),
) -> ReferenceTrackCheck
```

Is this track a reference track for a constant-speed type test? 6.2.

**6.2.5.** The roughness of every rail (every line, when 6.4.3 of EN 15610
asks for three) must cover at least 0,003 m to 0,10 m up to 190 km/h and
0,003 m to 0,25 m above, and must not exceed the limit of Figure 2 in any
band (EN 15610 clause 8). A small exceedance is accepted when Annex C
finds its effect on the pass-by level at most 1 dB: pass the result of
[`check_small_roughness_deviations`](/phonometry/reference/api/environment/rolling-stock-noise/#check_small_roughness_deviations) for the speed. A line analysed
by the digital filters of EN 15610 Method B
([`filtered_roughness_spectrum`](/phonometry/reference/api/environment/acoustic-roughness/#filtered_roughness_spectrum))
must also have at least 15 m of record analysed once 2 m are discarded
at either end of each record (EN 15610 7.4.3), judged on the record
length its average carries.

**6.2.6.** The vertical and the lateral decay rates of every set of
measurements must be at least the limits of Figure 3 in every band from
250 Hz to 5 000 Hz (EN 15461 clause 8). When the rates come with their
grid, clause 7 and 6.7 of EN 15461 are judged too: every rate at least
twice the floor of Formula 2, and the farthest response 10 dB below the
direct one.

**6.2.2.** When given, the curve radius must be at least
[`minimum_curve_radius`](/phonometry/reference/api/environment/rolling-stock-noise/#minimum_curve_radius) of the speed, and the gradient at most 5:1 000
(the gradient applies where powered units are tested).

**Parameters**

| Name | Description |
| :--- | :--- |
| `roughness` | The roughness spectra, one per rail or line, each the average of its records (EN 15610 7.6). |
| `decay_rates` | The decay rates, vertical and lateral, of every set. |
| `speed_kmh` | The test speed, in km/h. |
| `curve_radius_m` | The radius of curvature of the track, in metres; not judged when omitted. |
| `track_gradient_ratio` | The gradient, rise over length (5:1 000 is 0,005); not judged when omitted. |
| `small_deviations` | The Annex C verdict of this speed, computed on the quadratic average of `roughness` ([`average_roughness_spectra`](/phonometry/reference/api/environment/acoustic-roughness/#average_roughness_spectra), C.2.1) against `roughness_limit_db` (Formula C.1), which accepts a roughness exceedance whose effect is small. |
| `roughness_limit_db` | The roughness limit; Figure 2 by default. |
| `decay_limits_db_per_m` | The decay-rate limits, a band-to-rate mapping for each of the two directions; Figure 3 by default. |

**Returns:** The verdict, with every requirement and its numbers.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a speed that is not positive, a radius or gradient that is not a valid number, decay limits that leave out a direction, limits with a band that is not positive or two keys in one one-third octave band, or an Annex C verdict of another speed, of another roughness or against another roughness limit. |

## check_small_roughness_deviations

```python
check_small_roughness_deviations(
    roughness: AcousticRoughnessSpectrum,
    noise_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    speed_kmh: float,
    limit_db: Mapping[float, float] = mappingproxy({0.4: 17.1, 0.315: 15.0, 0.25: 13.0, 0.2: 11.0, 0.16: 9.0, 0.125: 7.0, 0.1: 4.9, 0.08: 2.9, 0.063: 0.9, 0.05: -1.1, 0.04: -3.2, 0.0315: -5.0, 0.025: -5.6, 0.02: -6.2, 0.016: -6.8, 0.0125: -7.4, 0.01: -8.0, 0.008: -8.6, 0.0063: -9.2, 0.005: -9.8, 0.004: -10.4, 0.00315: -11.0}),
) -> SmallRoughnessDeviation
```

May a track whose roughness exceeds the limit still be used? Annex C.

**Step 1 (C.2.1).** The just-compliant spectrum is the measured one held
down to the limit, $\min[L^\mathrm{measured}(\lambda), L^\mathrm{limit}(\lambda)]$ (Formula C.1); where the limit sets no value
the measured level stands.

**Step 2 (C.2.2).** Both spectra are carried from wavelength to frequency
at the train speed, $f = v/\lambda$, and the energy of each band is
shared among the normalised one-third octave bands in proportion to the
width it covers ([`redistributed_band_energies`](/phonometry/reference/api/environment/acoustic-roughness/#redistributed_band_energies),
the Annex C algorithm of EN 15610 adapted to bands of unequal width). The
correction is $\Delta L_{r,\mathrm{rail}}(f) = L^\mathrm{measured}(f) - L^\mathrm{corrected}(f)$ (Formula C.2), zero where no roughness band reaches.

**Step 3 (C.2.3).** The revised noise spectrum is the measured one less
the correction (Formula C.3), and the effect is the energy sum of the
measured spectrum less that of the revised one (Formula C.4). The track is
compliant when that is at most 1 dB (C.3), judged for one pass-by at each
speed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `roughness` | The measured roughness of the test section, the spectra of its rails quadratically averaged ([`average_roughness_spectra`](/phonometry/reference/api/environment/acoustic-roughness/#average_roughness_spectra)). |
| `noise_levels_db` | The A-weighted one-third octave spectrum of the pass-by, $L_{p\mathrm{Aeq},T_p}(f)$, in dB. |
| `frequencies_hz` | Its nominal band frequencies, in hertz. |
| `speed_kmh` | The train speed, in km/h. |
| `limit_db` | The upper limit, nominal wavelength in metres to level; Figure 2 by default. The verdict records it, and [`check_reference_track`](/phonometry/reference/api/environment/rolling-stock-noise/#check_reference_track) takes the verdict only when it judges the track against the same limit (6.2.5 and C.2.1). |

**Returns:** The verdict, the limit it was judged against and every intermediate spectrum.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a speed that is not positive, a noise spectrum that does not match its bands, or a limit with a wavelength that is not positive or two in one one-third octave band. |

## impulsiveness_rise_speed

```python
impulsiveness_rise_speed(
    times_s: ArrayLike,
    levels_db: ArrayLike,
) -> RiseSpeedResult
```

The rise speed that characterises impulsive noise, Annex A.

The rising slopes of $L_{p\mathrm{AF}}(t)$ are the stretches where
it increases from one sample to the next without a break; only those that
rise by 10 dB or more count. Each gives its steepest rise

$$
s_j = \max \left[ \frac{\mathrm{d}L_{p\mathrm{AF}}(t)}{\mathrm{d}t} \right]\ \mathrm{dB/s}
$$

(Formula A.1), taken here as the largest difference quotient between
neighbouring samples, and the result is the largest of them,
$s = \max(s_j)$. The history should be sampled finely enough for the
derivative to mean something; [`pass_by_measurement`](/phonometry/reference/api/environment/rolling-stock-noise/#pass_by_measurement) stores it every
10 ms.

**Parameters**

| Name | Description |
| :--- | :--- |
| `times_s` | The sample times, in seconds, increasing. |
| `levels_db` | $L_{p\mathrm{AF}}(t)$, in dB. |

**Returns:** The slopes and their rise speeds.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For arrays of different lengths, fewer than two samples, or times that do not increase. |

## minimum_curve_radius

```python
minimum_curve_radius(speed_kmh: float) -> float
```

The smallest radius of curvature the test track may have, 6.2.2.

1 000 m for tests up to 70 km/h, 3 000 m above 70 km/h and up to
120 km/h, 5 000 m above 120 km/h.

**Parameters**

| Name | Description |
| :--- | :--- |
| `speed_kmh` | The test speed, in km/h. |

**Returns:** The minimum radius, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a speed that is not positive. |

## pass_by_measurement

```python
pass_by_measurement(
    signal: SignalInput,
    fs: float | None = None,
    *,
    start_s: float,
    end_s: float,
    pass_by_time_s: float | None = None,
    front_passing_s: float | None = None,
    rear_passing_s: float | None = None,
    history_interval_s: float = 0.01,
) -> PassByMeasurement
```

The pass-by quantities of one record, 6.5 and 6.6.3.

The record is A-weighted (IEC 61672-1) and the equivalent level

$$
L_{p\mathrm{Aeq},T} = 10 \lg \left( \frac{1}{T} \int_{T_1}^{T_2} \frac{p_\mathrm{A}^2(t)}{p_0^2}\,\mathrm{d}t \right)
$$

is taken over the measurement interval (3.14); it is the pass-by level
$L_{p\mathrm{Aeq},T_p}$ when the interval is the unit's pass-by
time, from its front to its rear for a fixed formation, from the centre of
the first unit under test to the centre of the last within a train
(6.6.3). $L_{p\mathrm{AF}}(t)$ is the A-weighted level with time
weighting F, whose integrator starts from the mean square of the first
125 ms so the record's start does not read as an onset; its maximum
within the interval is $L_{p\mathrm{AFmax}}$ (3.13). Given the
pass-by time $T_p$, the result also carries the energy of the
interval spread over it, the transit exposure level of ISO 3095:2005
([`PassByMeasurement.normalized_level_db`](/phonometry/reference/api/environment/rolling-stock-noise/#passbymeasurementnormalized_level_db)).

6.6.3 asks that the record start at least 10 dB below the level when the
front of the train is opposite the microphone and end 10 dB below the
level at its rear; the result keeps both margins.

**Parameters**

| Name | Description |
| :--- | :--- |
| `signal` | The sound pressure record in pascals, unweighted, one channel, or a mono [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal), whose calibration is applied. |
| `fs` | The sampling rate, in hertz; a Signal brings its own. |
| `start_s` | $T_1$, in seconds from the start of the record. |
| `end_s` | $T_2$, in seconds. |
| `pass_by_time_s` | $T_p$, in seconds, to normalise the interval to ([`pass_by_time`](/phonometry/reference/api/environment/rolling-stock-noise/#pass_by_time)). |
| `front_passing_s` | When the front of the train is opposite the microphone, in seconds; `start_s` when omitted, as for a fixed formation. |
| `rear_passing_s` | When its rear is; `end_s` when omitted. |
| `history_interval_s` | The interval the level history is stored at, in seconds. |

**Returns:** The levels of the record.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a record of more than one channel, an empty record, an interval that is empty or runs past the record, or times that are negative. |

## pass_by_time

```python
pass_by_time(unit_length_m: float, *, speed_kmh: float) -> float
```

The time $T_p = l/v$ a unit takes to pass a point, in seconds.

ISO 3095:2005 3.14 defines it for a whole train as its overall length
divided by its speed. For the single trailer unit of Annex B.4 the
pass-by time of Formula B.1 is that of half the unit, so pass half its
length.

**Parameters**

| Name | Description |
| :--- | :--- |
| `unit_length_m` | The length of the unit or train, over buffers, in metres. |
| `speed_kmh` | Its speed, in km/h. |

**Returns:** $T_p$, in seconds.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a length or speed that is not positive. |

## pass_by_uncertainty

```python
pass_by_uncertainty(
    reading_db: float,
    inputs: Sequence[Quantity],
    *,
    coverage_factor: float = 2.0,
) -> PassByUncertainty
```

The uncertainty of a rolling stock noise result, Annex G.

The standard uncertainties of the input quantities combine as

$$
u_\mathrm{c}(y) = \sqrt{\sum_{i=1}^{N} u^2(x_i)}, \qquad U = k\,u_\mathrm{c}(y), \qquad k = 2
$$

(Formulae G.5 and G.6), and their mean value corrections, which Table G.1
gives for the unsymmetrical ranges, are added to the reading. An input
known only by its limits $\pm a$ has $u = a/\sqrt{3}$ (Formula
G.2): build it with [`phonometry.metrology.rectangular`](/phonometry/reference/api/metrology/uncertainty/#rectangular).

**Parameters**

| Name | Description |
| :--- | :--- |
| `reading_db` | The reading $L_p$, in dB. |
| `inputs` | The input quantities as [`phonometry.metrology.Quantity`](/phonometry/reference/api/metrology/uncertainty/#quantity) objects, whose `value` is the mean value correction in dB and whose `uncertainty` is the standard uncertainty in dB. An input without a name is called by its place, `x1`, `x2`, ..., primed (`x1'`) when another input was given that name. |
| `coverage_factor` | $k$; 2 by G.5. |

**Returns:** The budget.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | See [`PassByUncertainty`](/phonometry/reference/api/environment/rolling-stock-noise/#passbyuncertainty). |

## PassByMeasurement

```python
PassByMeasurement(
    times_s: NDArray[np.float64],
    levels_db: NDArray[np.float64],
    start_s: float,
    end_s: float,
    equivalent_level_db: float,
    max_level_db: float,
    front_level_db: float,
    rear_level_db: float,
    record_start_level_db: float,
    record_end_level_db: float,
    pass_by_time_s: float | None = None,
)
```

The levels of one pass-by record, 6.5 and 6.6.3.

**Parameters**

| Name | Description |
| :--- | :--- |
| `times_s` | The times of the stored level history, in seconds from the start of the record. |
| `levels_db` | $L_{p\mathrm{AF}}(t)$, the A-weighted level with time weighting F, at `times_s`, in dB. |
| `start_s` | $T_1$, the start of the measurement time interval. |
| `end_s` | $T_2$, its end, in seconds. |
| `equivalent_level_db` | $L_{p\mathrm{Aeq},T}$ over $T_1$ to $T_2$, in dB; the pass-by level $L_{p\mathrm{Aeq},T_p}$ when the interval is the pass-by time. |
| `max_level_db` | $L_{p\mathrm{AFmax}}$ within the interval, in dB. |
| `front_level_db` | $L_{p\mathrm{AF}}$ when the front of the train is opposite the microphone, in dB. |
| `rear_level_db` | $L_{p\mathrm{AF}}$ when its rear is, in dB. |
| `record_start_level_db` | $L_{p\mathrm{AF}}$ at the start of the record, in dB. |
| `record_end_level_db` | $L_{p\mathrm{AF}}$ at its end, in dB. |
| `pass_by_time_s` | $T_p$, in seconds, when given. |

### PassByMeasurement.end_margin_db

*property*

How far the record ends below the level at the rear, in dB (6.6.3).

### PassByMeasurement.exposure_level_db

*property*

The single event level $L_{p\mathrm{Aeq},T} + 10 \lg (T/T_0)$, $T_0 = 1$ s (2005, Formula 7).

### PassByMeasurement.measurement_time_s

*property*

$T = T_2 - T_1$, in seconds.

### PassByMeasurement.normalized_level_db

*property*

The energy of the interval spread over $T_p$, in dB; `None` without it.

$10 \lg \bigl( \frac{1}{T_p} \int_T p_\mathrm{A}^2 / p_0^2 \, \mathrm{d}t \bigr)$: the transit exposure level of ISO 3095:2005 3.14 for a whole
train, and the $L_{p\mathrm{Aeq},T_p}$ of Formula B.1 for a single
trailer unit, whose $T_p$ is that of half the unit.

### PassByMeasurement.plot()

```python
PassByMeasurement.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the level history with the measurement interval, as Figure 7 does.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the level history line. |

**Returns:** The axes drawn on.

### PassByMeasurement.recording_interval_sufficient

*property*

Whether the record starts and ends at least 10 dB down, 6.6.3.

### PassByMeasurement.start_margin_db

*property*

How far the record starts below the level at the front, in dB (6.6.3).

## PassByUncertainty

```python
PassByUncertainty(
    reading_db: float,
    names: tuple[str, ...],
    corrections_db: tuple[float, ...],
    standard_uncertainties_db: tuple[float, ...],
    coverage_factor: float = 2.0,
)
```

An uncertainty budget of a rolling stock noise result, Annex G.

The measurand is the reading plus uncorrelated corrections,
$Y = \sum X_i$ (Formula G.1), so every sensitivity coefficient is 1
(Formula G.4).

**Parameters**

| Name | Description |
| :--- | :--- |
| `reading_db` | The reading $L_p$, in dB. |
| `names` | The name of each input quantity. |
| `corrections_db` | The mean value correction $\Delta L_p$ of each input, in dB (0 for a symmetric interval). |
| `standard_uncertainties_db` | Its standard uncertainty $u(x_i)$, in dB. |
| `coverage_factor` | $k$, 2 by G.5. |

### PassByUncertainty.combined_uncertainty_db

*property*

$u_\mathrm{c}(y) = \sqrt{\sum u^2(x_i)}$, Formula G.5, in dB.

### PassByUncertainty.expanded_uncertainty_db

*property*

$U = k\,u_\mathrm{c}(y)$, Formula G.6, in dB.

### PassByUncertainty.level_db

*property*

The result $y$, the reading plus every mean value correction, in dB.

### PassByUncertainty.plot()

```python
PassByUncertainty.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each input's share of the variance, largest first, as Figure G.1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the bars. |

**Returns:** The axes drawn on.

### PassByUncertainty.variance_ratios

*property*

Each input's share of the variance of the result, as Figure G.1 draws it.

## PREFERRED_PASS_BY_SPEEDS_KMH

*Constant* (`tuple`).

```python
PREFERRED_PASS_BY_SPEEDS_KMH = (20.0, 40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 200.0, 250.0, 300.0, 320.0, 350.0)
```

## REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M

*Constant* (`mapping`).

```python
REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M = {'vertical': {250.0: 2.0, 315.0: 2.0, 400.0: 6.0, 500.0: 6.0, 630.0: 6.0, 800.0: 2.19, 1000.0: 0.8, 1250.0: 0.8, 1600.0: 0.8, 2000.0: 0.8, 2500.0: 0.8, 3150.0: 0.8, 4000.0: 0.8, 5000.0: 0.8}, 'lateral': {250.0: 2.04, 315.0: 1.38, 400.0: 0.94, 500.0: 0.64, 630.0: 0.43, 800.0: 0.29, 1000.0: 0.2, 1250.0: 0.2, 1600.0: 0.32, 2000.0: 0.5, 2500.0: 0.5, 3150.0: 0.5, 4000.0: 0.5, 5000.0: 0.5}}
```

## REFERENCE_TRACK_ROUGHNESS_LIMIT_DB

*Constant* (`mapping`).

```python
REFERENCE_TRACK_ROUGHNESS_LIMIT_DB = {0.4: 17.1, 0.315: 15.0, 0.25: 13.0, 0.2: 11.0, 0.16: 9.0, 0.125: 7.0, 0.1: 4.9, 0.08: 2.9, 0.063: 0.9, 0.05: -1.1, 0.04: -3.2, 0.0315: -5.0, 0.025: -5.6, 0.02: -6.2, 0.016: -6.8, 0.0125: -7.4, 0.01: -8.0, 0.008: -8.6, 0.0063: -9.2, 0.005: -9.8, 0.004: -10.4, 0.00315: -11.0}
```

## ReferenceTrackCheck

```python
ReferenceTrackCheck(
    speed_kmh: float,
    roughness: tuple[AcousticRoughnessSpectrum, ...],
    decay_rates: tuple[TrackDecayRate, ...],
    roughness_limit_db: Mapping[float, float],
    decay_limits_db_per_m: Mapping[str, Mapping[float, float]],
    small_deviations: SmallRoughnessDeviation | None = None,
    *,
    curve_radius_m: float | None = None,
    track_gradient_ratio: float | None = None,
)
```

The verdict on a test track against the reference conditions of ISO 3095 6.2.

**Parameters**

| Name | Description |
| :--- | :--- |
| `speed_kmh` | The test speed the track was judged for, in km/h. |
| `roughness` | The roughness spectra of the rails, one per rail or line, each already averaged over its records. |
| `decay_rates` | The decay rates, vertical and lateral, of each set of measurements. |
| `roughness_limit_db` | The roughness limit judged against, held as a read-only copy. |
| `decay_limits_db_per_m` | The decay-rate limits judged against, held as read-only copies. |
| `small_deviations` | The Annex C verdict the roughness limit was judged by, when the roughness exceeds the limit and one was given; `None` otherwise. |
| `curve_radius_m` | The radius of curvature of the track, in metres, or `None` when it was not judged. |
| `track_gradient_ratio` | The gradient, rise over length, or `None` when it was not judged. |

`conditions`, `passes` and `failed` are read from these
fields and the limits of 6.2, so none of them is a field.

### ReferenceTrackCheck.conditions

*property*

Every requirement judged, in the order of the clause.

Read from the roughness, the decay rates, the limits, the Annex C
verdict and the radius and gradient when given.

### ReferenceTrackCheck.failed

*property*

The requirements that do not hold.

### ReferenceTrackCheck.passes

*property*

Whether every requirement judged holds and none was left unjudged for want of data.

The curve radius and the gradient are judged only when given; the
roughness and both decay rates are always required, and so is the
length of a line analysed by EN 15610 Method B.

### ReferenceTrackCheck.plot()

```python
ReferenceTrackCheck.plot(
    ax: Axes | None = None,
    *,
    panel: str = 'roughness',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the roughness spectra against Figure 2, or the decay rates against Figure 3.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `panel` | `"roughness"` or `"decay"`. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the measured spectra. |

**Returns:** The axes drawn on.

## RiseSpeedResult

```python
RiseSpeedResult(
    times_s: NDArray[np.float64],
    levels_db: NDArray[np.float64],
    slopes: tuple[tuple[int, int], ...],
    rise_speeds_db_per_s: tuple[float, ...],
)
```

The impulsive character of a level history, Annex A.

**Parameters**

| Name | Description |
| :--- | :--- |
| `times_s` | The times of the history, in seconds. |
| `levels_db` | $L_{p\mathrm{AF}}(t)$, in dB. |
| `slopes` | The first and last sample of every slope that rises without a break by at least 10 dB. |
| `rise_speeds_db_per_s` | The steepest rise $s_j$ of each slope, in dB/s (Formula A.1). |

### RiseSpeedResult.plot()

```python
RiseSpeedResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the history with the slopes that count and the steepest rise.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the history line. |

**Returns:** The axes drawn on.

### RiseSpeedResult.rise_speed_db_per_s

*property*

The rise speed $s = \max(s_j)$, in dB/s; `None` when no slope rises 10 dB.

## rolling_stock_test

```python
rolling_stock_test(
    samples_db: Mapping[str, ArrayLike],
    *,
    method: str = 'constant_speed',
) -> RollingStockTestResult
```

The result of a constant-speed, starting or braking test, 6.7.1, 7.5.4, 7.6.4, 8.7.

Each position's runs are averaged arithmetically and rounded to the
nearest integer decibel, and the result is the highest of those: the
louder side at constant speed and in the averaged level method, the
loudest position in the maximum level method and in braking. A speed
normalisation, when one is required, goes on the runs before this
(6.7.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `samples_db` | The runs of each position, in dB, keyed by a name for the position (`"left"`, `"right"`, `"front, direction 1"`). |
| `method` | One of [`ROLLING_STOCK_TEST_METHODS`](/phonometry/reference/api/environment/rolling-stock-noise/#rolling_stock_test_methods). |

**Returns:** The test.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | See [`RollingStockTestResult`](/phonometry/reference/api/environment/rolling-stock-noise/#rollingstocktestresult). |

## ROLLING_STOCK_TEST_METHODS

*Constant* (`tuple`).

```python
ROLLING_STOCK_TEST_METHODS = ('constant_speed', 'acceleration_maximum', 'acceleration_averaged', 'braking')
```

## RollingStockTestResult

```python
RollingStockTestResult(
    method: str,
    samples_db: Mapping[str, tuple[float, ...]],
)
```

A test decided by the highest rounded mean of three runs per position.

**Parameters**

| Name | Description |
| :--- | :--- |
| `method` | One of [`ROLLING_STOCK_TEST_METHODS`](/phonometry/reference/api/environment/rolling-stock-noise/#rolling_stock_test_methods). |
| `samples_db` | The runs of each position, in dB, keyed by the position's name: $L_{p\mathrm{Aeq},T_p}$ at constant speed, $L_{p\mathrm{AFmax}}$ when starting (maximum level method) and braking, $L_{p\mathrm{Aeq},T}$ when starting (averaged level method). |

### RollingStockTestResult.final_level_db

*property*

The test result: the highest rounded mean (6.7.1, 7.5.4, 7.6.4, 8.7).

### RollingStockTestResult.governing_position

*property*

The position whose rounded mean is the result, the first on a tie.

### RollingStockTestResult.mean_levels_db

*property*

The arithmetic mean of each position's runs, in dB, unrounded.

### RollingStockTestResult.plot()

```python
RollingStockTestResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw every run, each position's rounded mean and the result.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the mean markers. |

**Returns:** The axes drawn on.

### RollingStockTestResult.positions

*property*

The positions, in the order given.

### RollingStockTestResult.reported_levels_db

*property*

Each position's mean rounded to the nearest integer decibel.

### RollingStockTestResult.spreads_db

*property*

The spread of each position's runs, in dB (9.3).

### RollingStockTestResult.valid

*property*

Whether every position's runs lie within 3 dB of each other (9.3).

When they do not, 9.3 asks for more runs; braking with squeal may
not get there, and 8.7 NOTE 1 then reports the runs without a mean.

## roughness_comparability

```python
roughness_comparability(
    roughness_1: AcousticRoughnessSpectrum,
    roughness_2: AcousticRoughnessSpectrum,
    noise_levels_1_db: ArrayLike,
    noise_levels_2_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    speed_kmh: float,
) -> RoughnessComparability
```

Bound how much the roughness of two tracks could change a pass-by level, Annex E.

**E.2.1.** The minimum and maximum envelopes of the two measured roughness
spectra are taken band by band (Formula E.1). **E.2.2.** The two measured
spectra and the two envelopes are carried to frequency at the train speed
as in Annex C, and each measured spectrum gets two correcting spectra, its
difference from each envelope (Formula E.2). **E.2.3.** Each situation's
noise spectrum is revised by its two corrections (Formula E.3), the
energy-summed difference of measured and revised gives
$\Delta L^{\mathrm{min},i} \ge 0$ and
$\Delta L^{\mathrm{max},i} \le 0$ (Formula E.4), and the bound is
the largest of their magnitudes (Formula E.5). It is an approximate bound
for roughness alone, not a prediction (E.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `roughness_1` | The measured roughness of test situation 1. |
| `roughness_2` | That of test situation 2. |
| `noise_levels_1_db` | The A-weighted pass-by spectrum measured in situation 1, in dB. |
| `noise_levels_2_db` | That of situation 2, in dB. |
| `frequencies_hz` | The nominal bands of both noise spectra, in hertz. |
| `speed_kmh` | The train speed of both pass-bys, in km/h. |

**Returns:** The four differences and the bound.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For spectra with no band in common, a speed that is not positive, or noise spectra that do not match their bands. |

## RoughnessComparability

```python
RoughnessComparability(
    speed_kmh: float,
    roughness_1: AcousticRoughnessSpectrum,
    roughness_2: AcousticRoughnessSpectrum,
    frequencies_hz: NDArray[np.float64],
    noise_levels_1_db: NDArray[np.float64],
    noise_levels_2_db: NDArray[np.float64],
    level_differences_db: tuple[float, float, float, float],
)
```

How much two tracks' roughness could change a pass-by level, Annex E.

**Parameters**

| Name | Description |
| :--- | :--- |
| `speed_kmh` | The train speed, in km/h. |
| `roughness_1` | The measured roughness of test situation 1. |
| `roughness_2` | That of test situation 2. |
| `frequencies_hz` | The nominal bands of the two noise spectra, in hertz. |
| `noise_levels_1_db` | The A-weighted pass-by spectrum of situation 1, in dB. |
| `noise_levels_2_db` | That of situation 2, in dB. |
| `level_differences_db` | $\Delta L^{\mathrm{min},1}$, $\Delta L^{\mathrm{max},1}$, $\Delta L^{\mathrm{min},2}$ and $\Delta L^{\mathrm{max},2}$ of Formula E.4, in dB, in that order. |

### RoughnessComparability.bound_db

*property*

$\Delta L_{p\mathrm{Aeq},T_p}$ of Formula E.5, in dB.

The largest magnitude of the four differences: the most the roughness
difference between the two situations could change the pass-by level.

### RoughnessComparability.envelope_max

*property*

The maximum envelope of the two roughness spectra, Formula E.1.

### RoughnessComparability.envelope_min

*property*

The minimum envelope of the two roughness spectra, Formula E.1.

### RoughnessComparability.plot()

```python
RoughnessComparability.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the two roughness spectra and their envelopes, as Figure E.1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the maximum envelope. |

**Returns:** The axes drawn on.

## SmallRoughnessDeviation

```python
SmallRoughnessDeviation(
    speed_kmh: float,
    roughness: AcousticRoughnessSpectrum,
    limit_db: Mapping[float, float],
    corrected_roughness_levels_db: NDArray[np.float64],
    frequencies_hz: NDArray[np.float64],
    roughness_correction_db: NDArray[np.float64],
    noise_levels_db: NDArray[np.float64],
)
```

The acceptance of small roughness exceedances by their effect on the noise, Annex C.

**Parameters**

| Name | Description |
| :--- | :--- |
| `speed_kmh` | The train speed of the pass-by, in km/h. |
| `roughness` | The quadratically averaged measured roughness. |
| `limit_db` | The upper limit the roughness was held down to, nominal wavelength in metres to level, held as a read-only copy. |
| `corrected_roughness_levels_db` | The just-compliant spectrum of Formula C.1, band by band with `roughness`, in dB re 1 µm. |
| `frequencies_hz` | The nominal one-third octave bands of the noise spectrum, in hertz. |
| `roughness_correction_db` | $\Delta L_{r,\mathrm{rail}}(f)$ of Formula C.2, in dB. |
| `noise_levels_db` | The measured A-weighted spectrum $L^\mathrm{measured}_{p\mathrm{Aeq},T_p}(f)$, in dB. |

### SmallRoughnessDeviation.exceeded

*property*

Whether the measured roughness exceeds the limit in any band at all.

### SmallRoughnessDeviation.impact_db

*property*

$\Delta L_{p\mathrm{Aeq},T_p}$ of Formula C.4, in dB.

The energy sum of the measured spectrum less that of the revised one:
an upper bound on what the exceedance added to the pass-by level.

### SmallRoughnessDeviation.passes

*property*

Whether the effect is at most 1 dB, C.3.

### SmallRoughnessDeviation.plot()

```python
SmallRoughnessDeviation.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the measured and revised noise spectra and the correction.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the measured spectrum. |

**Returns:** The axes drawn on.

### SmallRoughnessDeviation.revised_noise_levels_db

*property*

$L^\mathrm{revised}_{p\mathrm{Aeq},T_p}(f)$ of Formula C.3, in dB.

## STATIONARY_END_POSITION_LENGTH_M

*Constant* (`float`).

```python
STATIONARY_END_POSITION_LENGTH_M = 11.780972450961723
```

## stationary_test

```python
stationary_test(
    levels_db: ArrayLike,
    lengths_m: ArrayLike,
) -> StationaryTestResult
```

The stationary test of a unit from its measured mesh, 5.7 and 5.8.1.

Each set gives the unit level of Formula 1, and the result is the mean of
the sets rounded to the nearest integer decibel
([`StationaryTestResult.reported_level_db`](/phonometry/reference/api/environment/rolling-stock-noise/#stationarytestresultreported_level_db)). The samples of a
position are valid when they are no more than 3 dB apart (9.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | One row per set, one column per position of the whole mesh of 5.5.1.1 at 1,2 m, in dB; at least three sets. |
| `lengths_m` | The length each position stands for, in metres. |

**Returns:** The test.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | See [`StationaryTestResult`](/phonometry/reference/api/environment/rolling-stock-noise/#stationarytestresult). |

## stationary_unit_level

```python
stationary_unit_level(levels_db: ArrayLike, lengths_m: ArrayLike) -> float
```

The length-weighted energy average of a stationary mesh, Formulae 1 to 3.

$$
\langle L_{p\mathrm{Aeq},T} \rangle = 10 \lg \left( \sum_{i=1}^{n} \frac{l_i}{l_\mathrm{tot}} 10^{L^i_{p\mathrm{Aeq},T}/10} \right)
$$

over the positions of the whole unit (Formula 1) or of one car (Formula
3). The mesh is the whole one of 5.5.1.1 before any reduction: an omitted
position takes the level of the equivalent one measured (5.5.1.2), and an
end position stands for [`STATIONARY_END_POSITION_LENGTH_M`](/phonometry/reference/api/environment/rolling-stock-noise/#stationary_end_position_length_m).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L^i_{p\mathrm{Aeq},T}$ of each position, in dB. |
| `lengths_m` | The length $l_i$ each position stands for, in metres. |

**Returns:** The average, in dB, unrounded.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For levels that are not finite, lengths that are not positive, or arrays of different lengths. |

## StationaryTestResult

```python
StationaryTestResult(
    levels_db: NDArray[np.float64],
    lengths_m: NDArray[np.float64],
)
```

The stationary test of a unit, 5.8.1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L^i_{p\mathrm{Aeq},T}$, one row per set of measurements (one sample at every position) and one column per position, in dB. |
| `lengths_m` | The length each position stands for, in metres. |

### StationaryTestResult.mean_level_db

*property*

The arithmetic mean of the set levels, in dB, unrounded.

### StationaryTestResult.plot()

```python
StationaryTestResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the level of every position and the unit level.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the position bars. |

**Returns:** The axes drawn on.

### StationaryTestResult.position_spreads_db

*property*

The spread of the samples of each position across the sets, in dB (9.3).

### StationaryTestResult.reported_level_db

*property*

The test result: the mean rounded to the nearest integer decibel (5.8.1).

### StationaryTestResult.set_levels_db

*property*

$\langle L_{p\mathrm{Aeq},T} \rangle_\mathrm{unit}$ of each set, Formula 1, in dB.

### StationaryTestResult.valid

*property*

Whether every position's samples lie within 3 dB of each other (5.7, 9.3).

## TrackCondition

```python
TrackCondition(
    clause: str,
    requirement: str,
    holds: bool | None,
    detail: str,
)
```

One requirement of the reference track and whether it holds.

[`ReferenceTrackCheck.conditions`](/phonometry/reference/api/environment/rolling-stock-noise/#referencetrackcheckconditions) builds these rows from the track
it holds each time it is read; no verdict reads a row built elsewhere.

**Parameters**

| Name | Description |
| :--- | :--- |
| `clause` | Where the requirement is written (`"6.2.5"`). |
| `requirement` | What it asks, in words. |
| `holds` | Whether it holds; `None` when the input to judge it was not given. |
| `detail` | The numbers it was judged on. |

## transit_exposure_level

```python
transit_exposure_level(
    equivalent_level_db: float,
    *,
    measurement_time_s: float,
    pass_by_time_s: float,
) -> float
```

The transit exposure level of a train, ISO 3095:2005 3.14.

$$
\mathrm{TEL} = L_{p\mathrm{Aeq},T} + 10 \lg \frac{T}{T_p}
$$

(Formula 10): the energy of the whole passage, measured over a time
$T$ that runs from 10 dB below the level at the front to 10 dB below
the level at the rear, spread over the pass-by time $T_p$ alone. It
is Formula 9's $\mathrm{SEL} + 10 \lg (T_0/T_p)$ written with the
equivalent level.

**Parameters**

| Name | Description |
| :--- | :--- |
| `equivalent_level_db` | $L_{p\mathrm{Aeq},T}$ over the measurement time, in dB. |
| `measurement_time_s` | $T$, in seconds. |
| `pass_by_time_s` | $T_p$, in seconds ([`pass_by_time`](/phonometry/reference/api/environment/rolling-stock-noise/#pass_by_time)). |

**Returns:** TEL, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a level that is not finite or times that are not positive. |

## type_test_speeds

```python
type_test_speeds(max_speed_kmh: float) -> tuple[float, ...]
```

The speeds a unit is type tested at, 6.6.2.

Above 80 km/h, at 80 km/h and at the maximum speed; at or below it, at
the maximum speed alone. Further tests are run at the preferred speeds of
[`PREFERRED_PASS_BY_SPEEDS_KMH`](/phonometry/reference/api/environment/rolling-stock-noise/#preferred_pass_by_speeds_kmh).

**Parameters**

| Name | Description |
| :--- | :--- |
| `max_speed_kmh` | The maximum speed $v_\mathrm{max}$ of the unit, in km/h. |

**Returns:** The type-test speeds, in km/h, slowest first.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a speed that is not positive. |

---
title: "environment.sources.track_decay"
description: "How fast vibration dies away along a rail (EN 15461:2008+A1:2010)."
sidebar:
  label: "track_decay"
---

How fast vibration dies away along a rail (EN 15461:2008+A1:2010).

A rail struck by a wheel carries the vibration away along itself as vertical
and lateral bending waves, and the length of rail that radiates rolling noise
is set by how fast those waves decay. The **track decay rate** is that
attenuation in decibels per metre, one value per one-third octave band (3.6),
and a vehicle type test by ISO 3095 needs a track whose decay rates are at
least the lower limits of its Figure 3
([`REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M`](/phonometry/reference/api/environment/rolling-stock-noise/#reference_track_decay_limits_db_per_m)).

**The measurement (clause 6).** An accelerometer is fixed to the rail at the
middle of a sleeper bay, and an instrumented hammer strikes the rail at a grid
of positions measured in sleeper bays from it: every quarter bay out to bay 2
and a half, then every half bay to bay 4, every bay to bay 8, and then at bays
10, 12, 16, 20, 24, 30, 36, 42, 48, 54 and 66 (6.7 and Figure 2,
[`TRACK_DECAY_EXCITATION_INDICES`](/phonometry/reference/api/environment/track-decay/#track_decay_excitation_indices)). The frequency response between force
and response at each position, in mobility or accelerance, is reduced to its
one-third octave band magnitude $A(x_n)$; the one at the accelerometer
itself is the direct response $A(x_0)$.

**Clause 7 and Annex A, the rate.** If the response decayed as
$A(x) = A(0)\,\mathrm{e}^{-\beta x}$, the decay rate would be
$\mathrm{DR} = 20 \lg \mathrm{e}^{\beta} = 8{,}686\,\beta$ dB/m, and the integral of the
squared response along the rail would be $|A(0)|^2 / 2\beta$ (A.1). The
standard estimates it from that integral rather than from a fitted slope,

$$
\mathrm{DR} = \frac{4{,}343}{\displaystyle\sum_{n=0}^{n_\mathrm{max}} \frac{|A(x_n)|^2}{|A(x_0)|^2} \, \Delta x_n}\ \mathrm{dB/m}
$$

(Formula 1, A.3), where $\Delta x_n$ is the length of rail each
position stands for: from halfway to the position before it to halfway to the
one after it, from 0 to halfway for the direct response and symmetrical about
the last position (A.2) ([`track_decay_rate`](/phonometry/reference/api/environment/track-decay/#track_decay_rate)). The summation is dominated
by the first 10 dB of decay, which is what radiates.

**Formula 2, the floor.** A grid that stops at $x_\mathrm{max}$ cannot
measure a rate below $\mathrm{DR}_\mathrm{min} = 4{,}343 / x_\mathrm{max}$; a
band whose rate is less than twice that is unsuitable, and its value only an
upper bound on the true one (clause 7). The response at the far end of the
grid also has to be at least 10 dB below the direct one in every band (6.7).

Read from BS EN 15461:2008+A1:2010, which is identical to EN
15461:2008+A1:2010 (its national foreword).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## TRACK_DECAY_DIRECTIONS

*Constant* (`tuple`).

```python
TRACK_DECAY_DIRECTIONS = ('vertical', 'lateral')
```

## TRACK_DECAY_EXCITATION_INDICES

*Constant* (`tuple`).

```python
TRACK_DECAY_EXCITATION_INDICES = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 16.0, 20.0, 24.0, 30.0, 36.0, 42.0, 48.0, 54.0, 66.0)
```

## track_decay_excitation_positions

```python
track_decay_excitation_positions(
    *,
    sleeper_spacing_m: float = 0.6,
) -> NDArray[np.float64]
```

The hammer positions of Figure 2, in metres from the accelerometer.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sleeper_spacing_m` | The distance between sleepers, in metres; the 0,6 m 6.7 prescribes for a rail without periodic supports by default. |

**Returns:** The 29 distances of [`TRACK_DECAY_EXCITATION_INDICES`](/phonometry/reference/api/environment/track-decay/#track_decay_excitation_indices) times the sleeper spacing, read-only.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a spacing that is not positive. |

## track_decay_rate

```python
track_decay_rate(
    responses: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    distances_m: ArrayLike | None = None,
    sleeper_spacing_m: float = 0.6,
    direction: str = 'vertical',
) -> TrackDecayRate
```

The decay rate of a rail from its responses along it (clause 7, Formula 1).

$$
\mathrm{DR} = \frac{4{,}343}{\displaystyle\sum_{n=0}^{n_\mathrm{max}} \frac{|A(x_n)|^2}{|A(x_0)|^2} \, \Delta x_n}
$$

in each band, with $\Delta x_n$ the length of rail each position
stands for (A.2). Mobility and accelerance give the same rates, since only
the ratio to the direct response enters.

**Parameters**

| Name | Description |
| :--- | :--- |
| `responses` | The one-third octave band magnitudes $\vert A(x_n)\vert $, one row per excitation position, nearest first, the direct response in the first row, and one column per band. Magnitudes, not levels: a level in decibels is `10 ** (level / 20)`. |
| `frequencies_hz` | The nominal frequency of each band, in hertz; 6.6 asks for at least 100 Hz to 5 000 Hz. |
| `distances_m` | The excitation positions, in metres from the accelerometer, starting at 0 and increasing. When omitted, the 29 positions of Figure 2 at `sleeper_spacing_m`. |
| `sleeper_spacing_m` | The sleeper spacing the Figure 2 grid is laid out in, in metres, when `distances_m` is omitted. |
| `direction` | `"vertical"` or `"lateral"`. |

**Returns:** The rates, with the grid and the responses they came from.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For responses that are not positive and finite, a grid that is not finite, has fewer than two positions, does not start at 0 or does not strictly increase, frequencies that do not name distinct bands in increasing order, or shapes that do not agree. |

## TrackDecayRate

```python
TrackDecayRate(
    direction: str,
    frequencies_hz: NDArray[np.float64],
    decay_rates_db_per_m: NDArray[np.float64],
    distances_m: NDArray[np.float64] | None = None,
    responses: NDArray[np.float64] | None = None,
)
```

The decay rates of a rail in one direction, by one-third octave band (EN 15461).

Built by [`track_decay_rate`](/phonometry/reference/api/environment/track-decay/#track_decay_rate) from a set of frequency responses, or
directly from the rates of a report, which is all the ISO 3095 check
needs.

**Parameters**

| Name | Description |
| :--- | :--- |
| `direction` | `"vertical"` or `"lateral"`. |
| `frequencies_hz` | The nominal band frequencies, in hertz. |
| `decay_rates_db_per_m` | The decay rate of each band, in dB/m. |
| `distances_m` | The excitation positions, in metres from the accelerometer: the direct one at 0 m first, then strictly increasing, at least two in all; `None` for rates taken from a report. |
| `responses` | The magnitude $\vert A(x_n)\vert $ of each response, one row per position and one column per band, positive and finite, in whatever unit the mobility or accelerance was measured in; `None` for rates taken from a report. |

### TrackDecayRate.far_field_drops_db

*property*

How far the response at the farthest position is below the direct one, per band, in dB (6.7).

### TrackDecayRate.far_field_sufficient

*property*

Whether the farthest response is at least 10 dB below the direct one in every band (6.7).

### TrackDecayRate.minimum_measurable_db_per_m

*property*

The floor $4{,}343 / x_\mathrm{max}$ of Formula 2, in dB/m; `None` without the grid.

### TrackDecayRate.plot()

```python
TrackDecayRate.plot(
    ax: Axes | None = None,
    *,
    limit_db_per_m: Mapping[float, float] | None = None,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the rates as EN 15461 9.2 presents them.

Decay rate on a logarithmic axis from 0,01 dB/m to 100 dB/m against
equidistant one-third octave bands, with the bands clause 7 finds
unsuitable marked and a lower limit drawn when one is given.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `limit_db_per_m` | A lower limit, nominal frequency to rate, such as one direction of [`REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M`](/phonometry/reference/api/environment/rolling-stock-noise/#reference_track_decay_limits_db_per_m). |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the rate line. |

**Returns:** The axes drawn on.

### TrackDecayRate.rate_at()

```python
TrackDecayRate.rate_at(frequency_hz: float) -> float
```

The decay rate of the band a nominal frequency names, in dB/m.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | A nominal band frequency, in hertz. |

**Returns:** The rate of that band.

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | If the spectrum has no such band. |

### TrackDecayRate.suitable

*property*

Per band, whether the floor of Formula 2 is at most half the rate (clause 7).

A band that is not is an upper bound on the true rate. Every band is
taken as suitable when the grid is not known.

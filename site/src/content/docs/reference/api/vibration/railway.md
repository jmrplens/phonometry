---
title: "vibration.immission.railway"
description: "Evaluating the vibration of a passing train (DIN 45672-2:1995-07)."
sidebar:
  label: "railway"
---

Evaluating the vibration of a passing train (DIN 45672-2:1995-07).

A train passing a building puts vibration into the ground for twenty seconds
and then leaves, and DIN 45672-2 is the procedure that turns those twenty
seconds into numbers that can be compared: between two measuring points on the
way from the track to the building, between two dates either side of a
mitigation measure, and between one train and the next. It is measured with
the meter of DIN 45669-1 in its railway working range, 4 Hz to 315 Hz, and it
is an evaluation standard rather than an assessment one: it says how to reduce
a record, not what the result may be.

**Three stretches of one record** (Clause 5). $T_1$ is about four
seconds with the largest vibration in its middle, where the characteristic
values of the passage are read. $T_2$ is the passage itself, from where
the amplitude first reaches about a quarter of its usual maxima to where it
falls back to it. $T_3$ is the whole event, and it is the one an event
value is formed over. Every quantity below carries the index of the stretch it
came from.

**The quantities** (Clause 6). The running r.m.s. $\tilde v_F(t)$ with
$\tau = 125$ ms (Formula (1)) and its level against
$v_0 = 5 \cdot 10^{-8}$ m/s (Formula (2)); the interval r.m.s.
$\tilde v_j$ of Formula (4), or the approximation of Formula (5) formed
from the running r.m.s.; and the **event value** of Formula (8), the interval
r.m.s. of $T_3$ referred to one hour, $v_E = \tilde v_3 \sqrt{T_3/3600\,\mathrm{s}}$, whose square adds across the passages of an hour
(Formula (10)). The same quantities in third-octave bands from 4 Hz to 315 Hz
give the interval and maximum third-octave levels of Formulae (6) and (7).

**Narrow band** (Clause 7.3). The one-sided power spectral density of Formula
(12), blockwise with a Hanning window and at least half a block of overlap, at
the resolution of 1,25 Hz the standard recommends because it resolves the
resonance of an ordinary floor. Adding its lines back into third octaves is
Formula (23), and Table 1 fixes how many lines each band takes: a number
recommended for comparability rather than derived, which is why it is a
table here.

**What this does not do.** The standard is a method of reduction, so there is
no verdict anywhere in it, and none here: what the numbers mean for people and
buildings is DIN 4150-2 and DIN 4150-3. The calibration checks of Clause 7.3.3
test an analyser, which this module is not.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## amplitude_distribution

```python
amplitude_distribution(
    velocity_mm_s: ArrayLike,
    *,
    bins: int = 101,
) -> AmplitudeDistribution
```

The amplitude distribution of a stretch of velocity (Clause 6.3).

Clause 6.3 forms it over $T_2$ by DIN 55350-23, which is a histogram
normalised to unit area: equal bins across the range of the stretch.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The velocity of the stretch, in millimetres per second (1-D). |
| `bins` | How many equal bins span the range of the stretch (default 101, odd so that zero sits in the middle of one). |

**Returns:** The density and its cumulative function, as an [`AmplitudeDistribution`](/phonometry/reference/api/vibration/railway/#amplitudedistribution).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record or fewer than two bins. |

## AmplitudeDistribution

```python
AmplitudeDistribution(
    edges_mm_s: NDArray[np.float64],
    density_per_mm_s: NDArray[np.float64],
    cumulative: NDArray[np.float64],
)
```

How often each velocity occurred in a stretch, Formula (11).

**Attributes**

| Name | Description |
| :--- | :--- |
| `edges_mm_s` | The bin edges, in millimetres per second. |
| `density_per_mm_s` | $p_2(v)$, the amplitude distribution density, one value per bin, in 1/(mm/s); it integrates to one. |
| `cumulative` | $P_2(v)$, its integral up to the upper edge of each bin, rising from zero to one. |

## band_sum_level

```python
band_sum_level(levels_db: ArrayLike) -> float
```

The sum level $\Sigma L$ of a spectrum, Annex B, Formula (B.3).

$10 \lg \sum 10^{0,1 L(f_{Tn})}$, the energy sum of the bands.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The band levels, in decibels. |

**Returns:** $\Sigma L$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty or non-finite input. |

## centred_interval

```python
centred_interval(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    duration_s: float = 4.0,
) -> tuple[float, float]
```

The stretch $T_1$ of Clause 5 a), centred on the largest amplitude.

Clause 5 a) asks for the largest vibration to sit about in the middle of
$T_1$, and this puts it exactly there, or as near as the record
allows: a stretch that would run off either end is moved back inside it
rather than cut, so it keeps its length.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The velocity, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `duration_s` | The length of the stretch, in seconds (default 4 s). |

**Returns:** `(start, end)`, in seconds from the start of the record. A record shorter than *duration_s* is returned whole.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record or a non-positive rate or duration. |

## combined_event_velocity

```python
combined_event_velocity(event_velocities_mm_s: ArrayLike) -> float
```

The event value of every passage in one hour, Formula (10), in mm/s.

Event values add in square, because each is already the energy of its
passage spread over the same hour: $v_{E,\mathrm{ges}} = \sqrt{\sum v_{En}^2}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `event_velocities_mm_s` | The event values of the passages, in millimetres per second. |

**Returns:** $v_{E,\mathrm{ges}}$, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty, non-finite or negative input. |

## elastic_insertion_loss

```python
elastic_insertion_loss(
    levels_before_db: ArrayLike,
    levels_after_db: ArrayLike,
) -> NDArray[np.float64]
```

The insertion loss $D_e(f_{Tn})$ of Annex B, Formula (B.1), in dB.

The drop in the third-octave structure-borne level at one point of a
transmission path when an elastic element is built in. Annex B says it and
it bears repeating: the value belongs to the point it was measured at. The
difference spectrum of Formula (B.2) is the same subtraction between any
two spectra.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_before_db` | The third-octave levels before, in decibels. |
| `levels_after_db` | The levels after, at the same point, in decibels. |

**Returns:** $L_1 - L_2$ per band, positive where the element reduces the level.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the two do not match band for band. |

## evaluate_train_passage

```python
evaluate_train_passage(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    t2_s: tuple[float, float],
    t1_s: tuple[float, float] | None = None,
    t3_s: tuple[float, float] | None = None,
    upper_band_hz: float = 315.0,
) -> TrainPassage
```

Reduce one passage to the quantities of Clauses 5 to 7.

The record goes through the band limitation of the DIN 45669-1 railway
working range first, as it does inside the meter, and every quantity is
read from what is left: the running r.m.s. and its maximum, the peak, the
interval r.m.s. of the three stretches, the event value, the weighted
severity DIN 4150-2 reads, and the third-octave levels of Figure 6.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The velocity of the passage as the transducer gives it, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz: an integer, for the third-octave bank, and high enough to carry the 315 Hz range. |
| `t2_s` | $T_2$, the passage itself, `(start, end)` in seconds. Clause 5 b) reads it off the record, from about a quarter of the most frequent maxima back down to the same amplitude, which is a judgement about the record, so it is asked for rather than guessed. |
| `t1_s` | $T_1$; `None` (default) centres four seconds on the largest amplitude inside $T_2$, or all of $T_2$ when that is shorter. An explicit one may not be longer than $T_2$. |
| `t3_s` | $T_3$; `None` (default) takes the whole record. |
| `upper_band_hz` | The highest third octave, a nominal centre in hertz: 315 (default) or down to 80, the special case of DIN 45672-1. |

**Returns:** The reduced passage, as a [`TrainPassage`](/phonometry/reference/api/vibration/railway/#trainpassage).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a rate the chain or the upper band cannot take, a stretch outside the record, stretches that do not nest or a $T_1$ longer than $T_2$, or an upper band that is not a nominal centre from 80 Hz to 315 Hz. |

## EVENT_REFERENCE_DURATION_S

*Constant* (`float`).

```python
EVENT_REFERENCE_DURATION_S = 3600.0
```

## event_velocity

```python
event_velocity(interval_rms_mm_s: float, duration_s: float) -> float
```

The event value $v_E$ of Formula (8), in mm/s.

The interval r.m.s. of the whole event referred to one hour,
$v_E = \tilde v_3 \sqrt{T_3 / 3600\,\mathrm{s}}$: the constant
velocity that, held for an hour, carries the energy the passage carried.

**Parameters**

| Name | Description |
| :--- | :--- |
| `interval_rms_mm_s` | $\tilde v_3$, in millimetres per second. Clause 6.2 allows $\tilde v_{F3}$ of Formula (5) in its place. |
| `duration_s` | $T_3$, in seconds. |

**Returns:** $v_E$, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative velocity or a non-positive duration. |

## event_velocity_level

```python
event_velocity_level(interval_rms_mm_s: float, duration_s: float) -> float
```

The event level $L_{vE}$ of Formula (9), in dB.

$20 \lg(\tilde v_3 / v_0) + 10 \lg(T_3 / 3600\,\mathrm{s})$, which
is [`event_velocity`](/phonometry/reference/api/vibration/railway/#event_velocity) as a level against
[`VELOCITY_LEVEL_REFERENCE_MM_S`](/phonometry/reference/api/vibration/railway/#velocity_level_reference_mm_s).

**Parameters**

| Name | Description |
| :--- | :--- |
| `interval_rms_mm_s` | $\tilde v_3$, in millimetres per second, positive. |
| `duration_s` | $T_3$, in seconds. |

**Returns:** $L_{vE}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive velocity or duration. |

## interval_rms

```python
interval_rms(
    values: ArrayLike,
    fs_hz: float,
    *,
    interval_s: tuple[float, float],
) -> float
```

The interval r.m.s. of Formula (4), or of Formula (5).

Formula (4) averages the square of the velocity over the stretch. Handed
the running r.m.s. of [`running_velocity_rms`](/phonometry/reference/api/vibration/railway/#running_velocity_rms) instead, the same
average is Formula (5), which Clause 6.1 calls a good approximation of
Formula (4) and which is what a meter reading its display produces.

**Parameters**

| Name | Description |
| :--- | :--- |
| `values` | The velocity or its running r.m.s., in any unit (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `interval_s` | The stretch `(start, end)`, in seconds from the start of the record. |

**Returns:** $\tilde v_j$, in the unit of *values*.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a non-positive rate, or an interval that is empty or runs outside the record. |

## narrowband_psd

```python
narrowband_psd(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    resolution_hz: float = 1.25,
) -> SpectralDensityResult
```

The one-sided power spectral density of Formula (12), in (mm/s)²/Hz.

Clause 7.3.1 asks for blocks of $1/\Delta f$, a Hanning window
(Formula (18)), at least half a block of overlap and a linear average of
the blocks, which is the Welch estimate
[`power_spectral_density`](/phonometry/reference/api/signals/spectra/#power_spectral_density) makes. Its lines add
back to the mean square of the stretch, which is Formula (14).

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The velocity of the stretch, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `resolution_hz` | The line spacing $\Delta f$, in hertz (default 1,25 Hz). The block holds `round(fs / resolution)` samples, so the spacing actually used is `fs` over that count. |

**Returns:** The spectrum, as a [`SpectralDensityResult`](/phonometry/reference/api/signals/spectra/#spectraldensityresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record, a non-positive rate or resolution, or a stretch shorter than one block. |

## NARROWBAND_RESOLUTION_HZ

*Constant* (`float`).

```python
NARROWBAND_RESOLUTION_HZ = 1.25
```

## passage_average_level

```python
passage_average_level(
    levels_db: ArrayLike,
    *,
    axis: int | None = None,
) -> float | NDArray[np.float64]
```

The energy average of levels over repeated passages (Clause 9), in dB.

$10 \lg \langle 10^{L/10} \rangle$, the level of
[`passage_average_velocity`](/phonometry/reference/api/vibration/railway/#passage_average_velocity).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The levels of the passages, in decibels. A 2-D array of third-octave spectra, one row per passage, averages band by band with `axis=0`. |
| `axis` | The axis the passages run along; `None` (default) averages every value. |

**Returns:** The average level: a float, or one level per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty or non-finite input. |

## passage_average_velocity

```python
passage_average_velocity(interval_rms_mm_s: ArrayLike) -> float
```

The energy average of r.m.s. values over repeated passages (Clause 9).

Clause 9 averages the results of a class of trains energetically, which
for r.m.s. values is the root of the mean square, $\sqrt{\langle \tilde v^2 \rangle}$. The same holds for narrow-band spectra, whose power
spectral densities average arithmetically line by line.

**Parameters**

| Name | Description |
| :--- | :--- |
| `interval_rms_mm_s` | One r.m.s. value per passage, in millimetres per second. |

**Returns:** The energy average, in millimetres per second.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty, non-finite or negative input. |

## PASSAGE_BANDS_HZ

*Constant* (`tuple`).

```python
PASSAGE_BANDS_HZ = (4.0, 315.0)
```

## passage_energy_spectral_density

```python
passage_energy_spectral_density(
    psd: ArrayLike,
    duration_s: float,
) -> NDArray[np.float64]
```

The energy spectral density of $T_2$, Formula (13), in (mm/s)²/Hz².

Formula (13) writes $e_2 = |V_2|^2/4$ with the one-sided Fourier
spectrum $V = 2X$ of Formula (16), which is $|X|^2$, the
two-sided density. Set beside Formula (12) that is $e_2 = G_2 T_2 / 2$, and it means the lines of $e_2$ over positive frequencies add up
to half the energy of the stretch where the lines of $G_2$ add up to
all of its mean square. This returns the formula as printed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `psd` | $G_2$, the power spectral density of the stretch, in (mm/s)²/Hz, as [`narrowband_psd`](/phonometry/reference/api/vibration/railway/#narrowband_psd) gives it. |
| `duration_s` | $T_2$, in seconds. |

**Returns:** $e_2$ at the same lines, in (mm/s)²/Hz².

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative or non-finite density or a non-positive duration. |

## running_acceleration_level

```python
running_acceleration_level(
    acceleration_m_s2: ArrayLike,
    fs_hz: float,
    *,
    time_constant_s: float = 0.125,
) -> NDArray[np.float64]
```

The running acceleration level $L_{aF}(t)$ of Formula (3), in dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `acceleration_m_s2` | The acceleration, in metres per second squared (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `time_constant_s` | See [`running_velocity_rms`](/phonometry/reference/api/vibration/railway/#running_velocity_rms). |

**Returns:** $20 \lg(\tilde a_F / a_0)$ with $a_0 = 10^{-6}$ m/s², the reference DIN EN 21683 gives and the one the rest of this package's acceleration levels use.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record or a non-positive rate or constant. |

## running_velocity_level

```python
running_velocity_level(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    time_constant_s: float = 0.125,
) -> NDArray[np.float64]
```

The running velocity level $L_{vF}(t)$ of Formula (2), in dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The velocity, in millimetres per second (1-D). |
| `fs_hz` | Sampling frequency, in hertz. |
| `time_constant_s` | See [`running_velocity_rms`](/phonometry/reference/api/vibration/railway/#running_velocity_rms). |

**Returns:** $20 \lg(\tilde v_F / v_0)$ with $v_0$ = [`VELOCITY_LEVEL_REFERENCE_MM_S`](/phonometry/reference/api/vibration/railway/#velocity_level_reference_mm_s), one value per sample. A sample whose running r.m.s. is still exactly zero, before the first nonzero sample, is `-inf`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record or a non-positive rate or constant. |

## running_velocity_rms

```python
running_velocity_rms(
    velocity_mm_s: ArrayLike,
    fs_hz: float,
    *,
    time_constant_s: float = 0.125,
) -> NDArray[np.float64]
```

The running r.m.s. $\tilde v_F(t)$ of Formula (1), in mm/s.

The exponential average the formula integrates, started from rest. Clause
4 says what that costs at the start of a record and so why the averaging
has to be running before the train arrives. It puts the cost at 14 % after
$2\tau$ and 2 % after $4\tau$, which are the shortfalls of the
mean square, $e^{-2}$ and $e^{-4}$; the running r.m.s. itself,
which is what Figure 3 draws, is 7 % and 0,9 % short.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The velocity, in millimetres per second (1-D), as measured or in one third-octave band of it. |
| `fs_hz` | Sampling frequency, in hertz. |
| `time_constant_s` | The time constant, in seconds (default 0,125 s, "Fast"). |

**Returns:** $\tilde v_F(t)$, one value per sample, in mm/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad record or a non-positive rate or constant. |

## spectral_density_level

```python
spectral_density_level(psd: ArrayLike) -> NDArray[np.float64]
```

The level of a power spectral density, as Figure 7 draws it, in dB.

$10 \lg(G / G_0)$ with $G_0 = (5 \cdot 10^{-8}\,\mathrm{m/s})^2 /\mathrm{Hz}$, the square of [`VELOCITY_LEVEL_REFERENCE_MM_S`](/phonometry/reference/api/vibration/railway/#velocity_level_reference_mm_s) per
hertz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `psd` | The density, in (mm/s)²/Hz. |

**Returns:** The level at each line, in decibels; `-inf` where the density is exactly zero.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative or non-finite density. |

## T1_DURATION_S

*Constant* (`float`).

```python
T1_DURATION_S = 4.0
```

## THIRD_OCTAVE_LINES

*Constant* (`dict`).

```python
THIRD_OCTAVE_LINES = {4.0: 1, 5.0: 1, 6.3: 1, 8.0: 2, 10.0: 2, 12.5: 2, 16.0: 3, 20.0: 3, 25.0: 5, 31.5: 6, 40.0: 7, 50.0: 9, 63.0: 12, 80.0: 14, 100.0: 18, 125.0: 23, 160.0: 29, 200.0: 37, 250.0: 46, 315.0: 58, 400.0: 74, 500.0: 92}
```

## third_octaves_from_narrowband

```python
third_octaves_from_narrowband(
    frequencies_hz: ArrayLike,
    psd: ArrayLike,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]
```

Add a narrow-band spectrum back into third octaves, Formula (23).

Each band takes the number of lines Table 1 gives it, and the band r.m.s.
is the square root of their summed power, $\sqrt{\sum G(f_k)\, \Delta f}$. The table gives the counts and not the lines, so the choice is
stated here: the lines nearest the nominal centre on a logarithmic axis.
Wherever the count is what a sixth of an octave either side of the centre
holds, which is every band but two, those are exactly the lines inside the
band's nominal edges; at 10 Hz and 12,5 Hz, where the table departs from
the edges, they are 10 and 11,25 Hz, then 12,5 and 13,75 Hz.

It is a rule of nominal bands and it behaves like one. Nominal edges do
not meet: six lines fall between two bands and are in neither (71,25 Hz,
141,25 Hz and 142,5 Hz, and 353,75 Hz to 356,25 Hz), and five are in two
(178,75 Hz, 223,75 Hz, and 446,25 Hz to 448,75 Hz). The bands therefore
do not add up to the spectrum exactly, and a tone that sits in one of the
gaps is in no band at all; that is the comparability the table buys.

A band is returned only if the spectrum holds all its lines: a spectrum
that starts above the lowest bands or stops inside a band leaves those
bands out rather than filling them with the lines of a neighbour.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The line frequencies of the spectrum, in hertz, evenly spaced at 1,25 Hz. |
| `psd` | The one-sided power spectral density at those lines, in (mm/s)²/Hz. |

**Returns:** `(centres, rms)`: the nominal centres of the bands the spectrum holds whole, from [`THIRD_OCTAVE_LINES`](/phonometry/reference/api/vibration/railway/#third_octave_lines), in hertz, and the band r.m.s. in each, in mm/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For mismatched or non-finite inputs, a negative density, uneven spacing, or a spacing Table 1 is not written for. |

## TrainPassage

```python
TrainPassage(
    velocity_mm_s: NDArray[np.float64],
    running_rms_mm_s: NDArray[np.float64],
    peak_velocity_mm_s: float,
    running_rms_max_mm_s: float,
    kbf_max: float,
    interval_rms_mm_s: tuple[float, float, float],
    intervals_s: tuple[tuple[float, float], ...],
    event_velocity_mm_s: float,
    event_level_db: float,
    band_centres_hz: NDArray[np.float64],
    band_interval_levels_db: NDArray[np.float64],
    band_max_levels_db: NDArray[np.float64],
    fs_hz: float,
)
```

One passage reduced the way Clauses 5 to 7 reduce it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `velocity_mm_s` | The velocity the meter's railway band limitation leaves, one value per sample. |
| `running_rms_mm_s` | $\tilde v_F(t)$ of it. |
| `peak_velocity_mm_s` | $v_\mathrm{max}$, the largest absolute velocity of the passage (Clause 6.3). |
| `running_rms_max_mm_s` | $\tilde v_{F\mathrm{max}}$, the maximum of the running r.m.s. |
| `kbf_max` | $KB_{F\mathrm{max}}$, the maximum of the weighted severity of DIN 45669-1 over the same stretch, which DIN 4150-2 reads. |
| `interval_rms_mm_s` | $\tilde v_1$, $\tilde v_2$ and $\tilde v_3$ of Formula (4), in that order. |
| `intervals_s` | The three stretches `(start, end)`, in seconds. |
| `event_velocity_mm_s` | $v_E$ of Formula (8), from $T_3$. |
| `event_level_db` | $L_{vE}$ of Formula (9). |
| `band_centres_hz` | The nominal third-octave centres analysed. |
| `band_interval_levels_db` | $L_{vFj}(f_{Tn})$ of Formula (6), one row per stretch, $T_1$ to $T_3$. |
| `band_max_levels_db` | $L_{vF\mathrm{max}}(f_{Tn})$ of Formula (7), over $T_3$. |
| `fs_hz` | The sampling frequency of the record. |

### TrainPassage.plot()

```python
TrainPassage.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the running level with the three stretches marked on it.

Requires matplotlib (`pip install phonometry[plot]`). The spectra of
Figure 6 are `plot_spectrum`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_train_passage`. |

**Returns:** The `Axes`.

### TrainPassage.plot_spectrum()

```python
TrainPassage.plot_spectrum(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the interval and maximum third-octave levels, as Figure 6 does.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_train_passage_spectrum`. |

**Returns:** The `Axes`.

## VELOCITY_LEVEL_REFERENCE_MM_S

*Constant* (`float`).

```python
VELOCITY_LEVEL_REFERENCE_MM_S = 5e-05
```

## velocity_psd_from_voltage

```python
velocity_psd_from_voltage(
    psd_v2_per_hz: ArrayLike,
    *,
    sensitivity_v_per_mm_s: float,
    gain: float,
) -> NDArray[np.float64]
```

A density measured in volts, in the unit of the velocity (Annex A).

The transducer's transfer coefficient $\kappa_A$ and the amplifier's
gain $\kappa_V$ multiply the velocity, so they divide its density in
square: $G_{vv} = G_{\mathrm{V}} / (\kappa_A^2 \kappa_V^2)$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `psd_v2_per_hz` | The density the analyser shows, in V²/Hz. |
| `sensitivity_v_per_mm_s` | $\kappa_A$, in volts per millimetre per second (Annex A uses 0,030). |
| `gain` | $\kappa_V$, the amplifier gain, in volts per volt (Annex A uses 10). |

**Returns:** The density of the velocity, in (mm/s)²/Hz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative or non-finite density or a non-positive coefficient. |

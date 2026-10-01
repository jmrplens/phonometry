---
title: "environment.assessment.wind_turbine_modulation"
description: "Amplitude modulation of wind turbine sound at a receptor (IEC TS 61400-11-2:2024, clause 13)."
sidebar:
  label: "wind_turbine_modulation"
---

Amplitude modulation of wind turbine sound at a receptor (IEC TS 61400-11-2:2024, clause 13).

A turbine's level rises and falls once per blade passage, the "swish" or
"thump" a neighbour describes. Clause 13 of IEC TS 61400-11-2:2024 rates it
with the reference method of the UK Institute of Acoustics Amplitude
Modulation Working Group (the AMWG Final Report, 2016), which the TS
implements (13.2) with more specific outputs and the worst case band in each
bin. The input is a series of A-weighted 100 ms `Leq` values summed over
seven one-third-octave bands (13.6.2.1.1):
[`amplitude_modulation_band_levels`](/phonometry/reference/api/environment/wind-turbine-modulation/#amplitude_modulation_band_levels) forms it from logged band levels.

**The 10 s block** (13.6.2.3), [`amplitude_modulation_block`](/phonometry/reference/api/environment/wind-turbine-modulation/#amplitude_modulation_block). The 100
values are de-trended with a cubic least-squares fit, transformed with a
rectangular-window DFT of 0.1 Hz resolution and turned into the power
spectrum

$$
S_{xx} = \frac{|F\{x\}|^2}{m^2}, \qquad m = 100 \tag{12}
$$

The highest local maximum inside the user's range of fundamental modulation
frequencies is the fundamental. Its prominence is the line itself over the
linear mean of the two lines beyond each adjacent line,

$$
p_\mathrm{AM} = \frac{L_\mathrm{pk}}{L_\mathrm{m}} \tag{13}
$$

and a block with no local maximum in the range, or with
$p_\mathrm{AM} < 4$, is "prominence-failed". The second and third
harmonics join if a local maximum sits at (or within one or two lines of)
twice and three times the fundamental and both the fundamental alone and the
harmonic alone swing more than 1.5 dB peak to peak. Three lines about each
kept component, with their negative-frequency mirrors, are transformed back,
and the modulation depth is the 95th percentile of the reconstructed series
minus its 5th percentile (`L5 - L95`).

**The 10 min period** (13.6.3), [`amplitude_modulation_period`](/phonometry/reference/api/environment/wind-turbine-modulation/#amplitude_modulation_period): the AM
rating is the 90th percentile of the valid 10 s depths when at least 30 of the
60 blocks are valid, and 0 dB otherwise, with the mean and the mode of the
valid fundamental frequencies.

**The bins** (13.6.4), [`bin_amplitude_modulation`](/phonometry/reference/api/environment/wind-turbine-modulation/#bin_amplitude_modulation): the 10 min ratings
of each band are averaged per 1 m/s wind speed bin and 30 degree sector, the
zeros included, and each bin reports the band with the highest mean.

Where the TS and the AMWG Final Report part ways, the TS is implemented: a
period with fewer than 30 valid blocks is kept at 0 dB and counted in its bin
(TS 13.6.3, 13.6.4), where the AMWG discards it (Figure 4.2.2); and the band is
chosen per bin (TS 13.6.4), where the AMWG chooses one band for the whole
survey by regressing the three bands' ratings against each other (Figure
4.2.1, 4.3.2). 13.6.4 also leaves out of the bin mean "any excluded periods
due to pf or other exclusions"; read literally, that would drop the very
periods 13.6.3 rates 0 dB (their blocks failed the prominence test), and the
"including 0 values" of the same sentence, with the count of non-zero values
13.6.4 asks for, would mean nothing. It is read as the periods the
practitioner excludes, the `excluded` flags of
[`bin_amplitude_modulation`](/phonometry/reference/api/environment/wind-turbine-modulation/#bin_amplitude_modulation). The TS says both "at least 50 %" (13.6.2.2)
and "greater than 50 % (30 valid 10 s blocks)" (13.6.3) of a period's blocks;
a period of exactly 30 valid blocks is rated, as 13.6.2.2 and the AMWG (4.4.4,
"at least 50 % (i.e. 30)") both say.

Two steps the TS leaves open are read as the IOA's published reference code
reads them: the percentiles interpolate linearly between the order
statistics, and the spectrum runs from 0.1 Hz to 4.9 Hz, without the zero
frequency the de-trending has emptied and without the Nyquist line, whose
three-line window would have no mirror of its own.

A spectral line within rounding of zero is read as zero: a line no larger than
the square of $10^{-9}$ of the block's largest absolute level. Once
de-trended, a steady block, or one that follows a cubic, holds nothing else, so
it has no local maximum and is prominence-failed, the block of 13.6.2.3 d) in
which "there is no significant AM" (the AMWG Final Report, 4.5.2 step 4:
"either no AM, or the block is corrupted"). Read as they come out of the fit,
its rounding lines would decide its status by their last bits.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AM_BLOCK_SAMPLES

*Constant* (`int`).

```python
AM_BLOCK_SAMPLES = 100
```

## AM_EXCEEDANCE_THRESHOLDS_DB

*Constant* (`tuple`).

```python
AM_EXCEEDANCE_THRESHOLDS_DB = (3.0, 6.0, 9.0)
```

## AM_FREQUENCY_BANDS_HZ

*Constant* (`mapping`).

```python
AM_FREQUENCY_BANDS_HZ = {1: (50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0), 2: (100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0), 3: (200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0), 4: (400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0), 5: (800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0), 6: (1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0)}
```

## AM_MINIMUM_VALID_BLOCKS

*Constant* (`int`).

```python
AM_MINIMUM_VALID_BLOCKS = 30
```

## AM_MODULATION_FREQUENCY_LIMITS_HZ

*Constant* (`tuple`).

```python
AM_MODULATION_FREQUENCY_LIMITS_HZ = (0.3, 1.6)
```

## AM_PERIOD_BLOCKS

*Constant* (`int`).

```python
AM_PERIOD_BLOCKS = 60
```

## AM_PROMINENCE_THRESHOLD

*Constant* (`float`).

```python
AM_PROMINENCE_THRESHOLD = 4.0
```

## AM_SAMPLE_INTERVAL_S

*Constant* (`float`).

```python
AM_SAMPLE_INTERVAL_S = 0.1
```

## amplitude_modulation_band_levels

```python
amplitude_modulation_band_levels(
    band_levels_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    band: int,
    weighting: Literal['A', 'Z'],
) -> NDArray[np.float64]
```

Band-limited A-weighted 100 ms levels of one AM band (13.6.2.1.1).

The 100 ms one-third-octave band `Leq` values of the seven bands of
`band` are A-weighted, if they were logged unweighted, and summed
logarithmically sample by sample into the `LAeq,100ms (BP)` series the
10 s analysis takes. The A-weighting is the IEC 61672-1:2013 Table 3
value at each nominal centre frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_levels_db` | The logged band levels, in dB: one row per 100 ms sample and one column per one-third-octave band (a single sample may be given as one row). |
| `frequencies_hz` | Nominal centre frequency of each column, in Hz; it must include the seven centres of `band`. |
| `band` | The AM band number, 1 to 3 (13.6.2.1.1) or 4 to 6 (Annex G.3), as an integer; see [`AM_FREQUENCY_BANDS_HZ`](/phonometry/reference/api/environment/wind-turbine-modulation/#am_frequency_bands_hz). |
| `weighting` | `"A"` when the band levels are already A-weighted, `"Z"` when the A-weighting is still to be applied. Required: a wrong guess is a 20 dB to 30 dB error at the lowest bands. |

**Returns:** The band-limited `LAeq,100ms` series, in dB, one value per sample.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the band is not one of the band numbers (`1.5` and `True` are not), a band centre is missing or duplicated, the weighting is neither `"A"` nor `"Z"`, or the levels are not finite. |

## amplitude_modulation_block

```python
amplitude_modulation_block(
    levels_db: ArrayLike,
    *,
    modulation_frequency_range_hz: Sequence[float],
) -> ModulationBlock
```

Analyse one 10 s block of 100 ms levels (IEC TS 61400-11-2, 13.6.2.3).

Steps a) to f) of 13.6.2.3 and the reconstruction after them: cubic
de-trending, a rectangular-window DFT of 0.1 Hz resolution, the power
spectrum of Equation (12), the fundamental as the highest local maximum
within `modulation_frequency_range_hz`, its prominence (Equation (13))
against the threshold of 4, the second and third harmonics under the two
1.5 dB conditions, and the modulation depth `L5 - L95` of the series
transformed back from three lines about each kept component.

The local maxima, the fundamental, the harmonics and the prominence are
read with the lines at rounding set to zero: a line no larger than
$(10^{-9} L)^2$, $L$ the largest absolute level of the block.
A steady block, or one that follows a cubic, then has no local maximum
and is `NO_PEAK` rather than a verdict drawn from the last bits of its
levels, and a peak whose masking lines hold only rounding has an infinite
prominence. [`ModulationBlock.power_spectrum`](/phonometry/reference/api/environment/wind-turbine-modulation/#modulationblock) keeps every line as
Equation (12) gives it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The 100 band-limited A-weighted `Leq,100ms` values of the block, in dB (see [`amplitude_modulation_band_levels`](/phonometry/reference/api/environment/wind-turbine-modulation/#amplitude_modulation_band_levels)). |
| `modulation_frequency_range_hz` | `(low, high)` range, in Hz, where the fundamental modulation frequency is expected: the blade passage frequencies of the turbines with some tolerance (13.6.2.1.2), within 0.3 Hz to 1.6 Hz (13.2). |

**Returns:** A [`ModulationBlock`](/phonometry/reference/api/environment/wind-turbine-modulation/#modulationblock).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the block does not hold 100 finite values or the range is outside 0.3 Hz to 1.6 Hz or holds no spectrum line. |

## amplitude_modulation_period

```python
amplitude_modulation_period(
    levels_db: ArrayLike,
    *,
    modulation_frequency_range_hz: Sequence[float],
    excluded_blocks: ArrayLike | None = None,
) -> ModulationPeriod
```

Rate one 10 min period of 100 ms levels (IEC TS 61400-11-2, 13.6.3).

The 6 000 values are cut into sixty consecutive 10 s blocks, each analysed
by [`amplitude_modulation_block`](/phonometry/reference/api/environment/wind-turbine-modulation/#amplitude_modulation_block). With at least 30 valid blocks the
rating is the 90th percentile of their depths and the mean and mode of
their fundamentals are reported; otherwise the rating is 0 dB and no
modulation frequency is given. That 0 dB period is kept, and counted in
its bin by [`bin_amplitude_modulation`](/phonometry/reference/api/environment/wind-turbine-modulation/#bin_amplitude_modulation), as the TS says (13.6.3,
13.6.4); the AMWG Final Report discards it instead.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | The 6 000 band-limited `LAeq,100ms` values of the period, in dB, synchronised to the hour (13.6.3). |
| `modulation_frequency_range_hz` | `(low, high)` range of the fundamental, in Hz, as for [`amplitude_modulation_block`](/phonometry/reference/api/environment/wind-turbine-modulation/#amplitude_modulation_block). |
| `excluded_blocks` | Optional sixty flags, `True` for a block the practitioner excludes by hand (13.6.2.2); those blocks are not analysed and do not count as valid. The TS notes that standard practice excludes whole 10 min periods, so excluding single blocks is an adaptation to be justified. |

**Returns:** A [`ModulationPeriod`](/phonometry/reference/api/environment/wind-turbine-modulation/#modulationperiod).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the period does not hold 6 000 finite values or the exclusion flags are not sixty booleans (or 0 and 1). |

## bin_amplitude_modulation

```python
bin_amplitude_modulation(
    ratings_db: ArrayLike,
    wind_speeds_m_s: ArrayLike,
    wind_directions_deg: ArrayLike | None = None,
    *,
    bands: Iterable[int] = (1, 2, 3),
    excluded: ArrayLike | None = None,
    sector_width_deg: float = 30.0,
) -> BinnedModulation
```

Bin 10 min AM ratings and pick the worst band per bin (13.6.4).

Each 10 min period is a data point of its rating in each band, aligned
with the period's wind speed and direction. Wind speed bins are 1 m/s
wide and centred on the integers (0.5 m/s to 1.5 m/s is bin 1);
direction sectors are `sector_width_deg` wide and the first is centred
on north (345 degrees to 15 degrees for 30 degree sectors). The mean
rating of each bin includes the 0 dB of unrated periods; `excluded`
periods are left out altogether. Each bin reports the band with the
highest mean.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ratings_db` | The 10 min ratings, in dB, one row per period and one column per band of `bands` (see [`ModulationPeriod.rating_db`](/phonometry/reference/api/environment/wind-turbine-modulation/#modulationperiod)). |
| `wind_speeds_m_s` | The reference wind speed of each period, in m/s. |
| `wind_directions_deg` | The wind direction of each period, in degrees from north, or `None` to bin by wind speed alone. |
| `bands` | The AM band numbers of the columns, as integers. |
| `excluded` | Optional flags, `True` for a period the practitioner excluded; 13.6.4 leaves excluded periods out of the bin mean, whatever the reason. A period rated 0 dB for having fewer than 30 valid blocks is not excluded: it counts, at 0 dB, since 13.6.4 averages "including 0 values" and 13.6.3 assigns that 0 to such a period (the "excluded periods due to pf" of 13.6.4 are read as periods excluded by hand). |
| `sector_width_deg` | Width of the direction sectors, in degrees; it must divide 360. Wider sectors (downwind, crosswind) are reached by rotating the directions so that the sector of interest is centred on zero. |

**Returns:** A [`BinnedModulation`](/phonometry/reference/api/environment/wind-turbine-modulation/#binnedmodulation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes disagree, a value is not finite, a wind speed is negative, a band is not a band number or is repeated, the exclusion flags are not booleans (or 0 and 1), or the sector width does not divide 360 degrees. |

## BinnedModulation

```python
BinnedModulation(
    bands: tuple[int, ...],
    wind_speeds_m_s: NDArray[np.float64],
    wind_directions_deg: NDArray[np.float64] | None,
    counts: NDArray[np.int64],
    nonzero_counts: NDArray[np.int64],
    mean_ratings_db: NDArray[np.float64],
    type_a_uncertainty_db: NDArray[np.float64],
    exceedance_percent: NDArray[np.float64],
    *,
    selected_bands: NDArray[np.int64],
    selected_ratings_db: NDArray[np.float64],
)
```

AM ratings binned by wind speed and direction (IEC TS 61400-11-2, 13.6.4).

One row per occupied bin, sorted by wind direction sector then wind
speed; one column per band in `bands`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `bands` | The AM bands analysed, in the column order of the arrays. |
| `wind_speeds_m_s` | Centre of each bin's 1 m/s wind speed class. |
| `wind_directions_deg` | Centre of each bin's direction sector, or `None` when the ratings were binned by wind speed alone. |
| `counts` | Number of 10 min data points in each bin. |
| `nonzero_counts` | Number of those with a non-zero rating, per band. |
| `mean_ratings_db` | Mean 10 min rating per bin and band, the zeros of unrated periods included (13.6.4), in dB. |
| `type_a_uncertainty_db` | Standard deviation of that mean, Equation (9) of 10.3.3 (13.6.5); NaN for a bin of one data point. |
| `exceedance_percent` | Percentage of the bin's data points rated above 3 dB, 6 dB and 9 dB ([`AM_EXCEEDANCE_THRESHOLDS_DB`](/phonometry/reference/api/environment/wind-turbine-modulation/#am_exceedance_thresholds_db)), shape `(bins, bands, 3)`. |
| `selected_bands` | The band with the highest mean rating in each bin, the lowest-numbered of equally high ones. |
| `selected_ratings_db` | The mean rating of that band, in dB. |

### BinnedModulation.plot()

```python
BinnedModulation.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the worst-band mean rating of each bin against wind speed.

One line per direction sector, in its own colour (or one line when
binned by wind speed alone), each point labelled with the band that
bin selected. The twelve 30° sectors of 13.7 take twelve colours;
narrower sectors past the twelfth take them again, in the same order.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the lines. |

**Returns:** The axes.

## ModulationBlock

```python
ModulationBlock(
    levels_db: NDArray[np.float64],
    detrended_db: NDArray[np.float64],
    frequencies_hz: NDArray[np.float64],
    power_spectrum: NDArray[np.float64],
    modulation_frequency_range_hz: tuple[float, float],
    *,
    status: ModulationBlockStatus,
    fundamental_frequency_hz: float | None,
    prominence: float | None,
    harmonic_frequencies_hz: tuple[float, ...],
    reconstructed_db: NDArray[np.float64],
    modulation_depth_db: float | None,
)
```

The analysis of one 10 s block (IEC TS 61400-11-2:2024, 13.6.2.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `levels_db` | The 100 band-limited `LAeq,100ms` values analysed, in dB. |
| `detrended_db` | `levels_db` minus its cubic least-squares fit, in dB. |
| `frequencies_hz` | The spectrum lines, 0.1 Hz to 4.9 Hz. |
| `power_spectrum` | $S_{xx}$ of Equation (12) at those lines, from the positive frequencies (the half magnitude the TS allows). |
| `modulation_frequency_range_hz` | The user's range of fundamental modulation frequencies, in Hz. |
| `status` | [`ModulationBlockStatus`](/phonometry/reference/api/environment/wind-turbine-modulation/#modulationblockstatus) of the block. |
| `fundamental_frequency_hz` | The fundamental modulation frequency, the highest local maximum in the range, in Hz; `None` for `NO_PEAK`. |
| `prominence` | The prominence ratio $p_\mathrm{AM}$ of Equation (13); `None` for `NO_PEAK`, infinite for a peak whose masking lines hold nothing above rounding. |
| `harmonic_frequencies_hz` | The frequencies of the harmonics kept in the reconstruction, second before third; empty when none is. |
| `reconstructed_db` | The reconstructed series, in dB about zero; empty for a prominence-failed block. |
| `modulation_depth_db` | `L5 - L95` of the reconstructed series, in dB; `None` unless the block is valid. |

### ModulationBlock.included_frequencies_hz

*property*

The spectrum lines transformed back, three about each component.

### ModulationBlock.plot()

```python
ModulationBlock.plot(
    ax: Axes | None = None,
    *,
    kind: Literal['spectrum', 'series'] = 'spectrum',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the block's power spectrum (Figure 1) or its two time series.

`kind="spectrum"` draws $S_{xx}$ with the range of fundamental
frequencies, the lines kept in the reconstruction and the prominence,
as Figure 1 of the TS does. `kind="series"` draws the de-trended
series with the reconstructed one over it and the `L5` and `L95`
of the reconstruction.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `kind` | `"spectrum"` (default) or `"series"`. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the primary artist. |

**Returns:** The axes.

### ModulationBlock.valid

*property*

Whether the block carries a modulation depth (13.6.2.2).

## ModulationBlockStatus

```python
ModulationBlockStatus(*values)
```

Why a 10 s block counts or does not (13.6.2.2 and 13.6.2.3).

`VALID` blocks carry a modulation depth. `NO_PEAK` and
`LOW_PROMINENCE` are the two prominence-failed (pf) outcomes of
13.6.2.3 d) and e): no local maximum inside the range of fundamental
frequencies, or a prominence ratio under 4. A steady block, or one that
follows a cubic, is `NO_PEAK`: once de-trended it holds nothing but
rounding, the case in which d) considers "that there is no significant
AM". `EXCLUDED` is a block the practitioner excluded by hand (13.6.2.2,
third bullet).

## ModulationPeriod

```python
ModulationPeriod(
    blocks: tuple[ModulationBlock, ...],
    modulation_depths_db: NDArray[np.float64],
    fundamental_frequencies_hz: NDArray[np.float64],
    *,
    valid_blocks: int,
    rated: bool,
    rating_db: float,
    mean_modulation_frequency_hz: float | None,
    mode_modulation_frequency_hz: float | None,
)
```

The AM rating of one 10 min period (IEC TS 61400-11-2:2024, 13.6.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `blocks` | The sixty [`ModulationBlock`](/phonometry/reference/api/environment/wind-turbine-modulation/#modulationblock) analyses, in time order. |
| `modulation_depths_db` | The depth of each block, in dB; NaN where the block is not valid. |
| `fundamental_frequencies_hz` | The fundamental of each valid block, in Hz; NaN elsewhere. |
| `valid_blocks` | Number of valid blocks, the `n` number of 13.6.2.2. |
| `rated` | Whether at least 30 blocks are valid (13.6.2.2). |
| `rating_db` | The AM rating of the period, in dB: the 90th percentile of the valid depths when `rated`, else 0 dB (13.6.3). |
| `mean_modulation_frequency_hz` | Mean fundamental of the valid blocks, in Hz; `None` when not `rated`. |
| `mode_modulation_frequency_hz` | Most frequent fundamental of the valid blocks, in Hz, the lowest of equally frequent ones; `None` when not `rated`. |

### ModulationPeriod.plot()

```python
ModulationPeriod.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the 10 s depths through the period and the 10 min rating.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the 10 s depths. |

**Returns:** The axes.

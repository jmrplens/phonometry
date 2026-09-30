---
title: "environment.sources.acoustic_roughness"
description: "The acoustic roughness of a rail, measured directly on it (EN 15610:2009)."
sidebar:
  label: "acoustic_roughness"
---

The acoustic roughness of a rail, measured directly on it (EN 15610:2009).

Rolling noise is excited by the unevenness of the wheel and rail running
surfaces, and the rail's share of it, its **acoustic roughness**
$r(x)$, is the height of the running surface along the rail (3.1). EN
15610 measures it with a probe that follows a line on the rail head and turns
the record into a one-third octave band spectrum of wavelength, which is how
a test track is shown to be smooth enough for a vehicle type test (ISO 3095,
6.2.5, whose limit lives in
[`REFERENCE_TRACK_ROUGHNESS_LIMIT_DB`](/phonometry/reference/api/environment/rolling-stock-noise/#reference_track_roughness_limit_db)).

**Clause 7, the processing.** A record goes through three stages before its
spectrum is taken (7.1): the data of joints, welds and rail defects are edited
out by the operator (Annex A shows what is and is not a defect); narrow upward
spikes from particles on the rail are removed (7.2,
[`remove_roughness_spikes`](/phonometry/reference/api/environment/acoustic-roughness/#remove_roughness_spikes)); and every point is raised to where a wheel
of 0,375 m radius would stand on it, because the probe tip is far smaller than
a wheel and reaches into pits a wheel rolls over (7.3,
[`curvature_processed_roughness`](/phonometry/reference/api/environment/acoustic-roughness/#curvature_processed_roughness)).

**The spectrum.** Method A of 7.4.2 ([`acoustic_roughness_spectrum`](/phonometry/reference/api/environment/acoustic-roughness/#acoustic_roughness_spectrum))
cuts the record into segments at least 1 m long overlapping by half, removes
the mean and the linear trend of each, applies a Hanning window and averages
the squared magnitudes of their discrete Fourier transforms into a narrow band
spectrum. The one-third octave band value is the energy sum of the narrow
band lines, the two lines that straddle a band edge counted only for the
portion of their width inside the band (Annex C,
[`redistributed_band_energies`](/phonometry/reference/api/environment/acoustic-roughness/#redistributed_band_energies)). The level is

$$
L_r = 10 \lg \frac{r_\mathrm{RMS}^2}{r_0^2}\ \mathrm{dB}, \qquad r_0 = 1\ \mathrm{\mu m}
$$

(3.3, Formula 1). A record of a given length only resolves wavelengths up to
a quarter of it (7.5), so a 1 m segment reports down to the 0,25 m band.

**7.6, the average.** The spectra of the records of one line are averaged on
their mean squares, without weighting by where along the test section they
were taken ([`average_roughness_spectra`](/phonometry/reference/api/environment/acoustic-roughness/#average_roughness_spectra)), and 6.4.3 sets how many lines
a rail needs by the width of its reference surface
([`roughness_measurement_lines`](/phonometry/reference/api/environment/acoustic-roughness/#roughness_measurement_lines)). Clause 8 compares every average with the
limit and allows no band above it; that verdict, with the flexibility of ISO
3095 Annex C, is
[`check_reference_track`](/phonometry/reference/api/environment/rolling-stock-noise/#check_reference_track).

**What is left to the tester.** Method B, the digital one-third octave
filters of 7.4.3 on records of at least 5 m, is not implemented: Method A is
the one Annex B uses by default and the one the Fourier synthesis of Annex C
serves. The spike height $h$ of 7.2 is not defined by the clause; it is
read here, as the Annex B listing computes it, as the height of the peak above
the straight line the spike is replaced by.

Read from BS EN 15610:2009, which is identical to EN 15610:2009 (its national
foreword).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## acoustic_roughness_spectrum

```python
acoustic_roughness_spectrum(
    roughness_um: ArrayLike,
    *,
    sample_spacing_m: float,
    spike_removal: bool = True,
    curvature_processing: bool = True,
    segment_length_m: float = 1.0,
) -> AcousticRoughnessSpectrum
```

The one-third octave band acoustic roughness of a record (7.2 to 7.4, Method A).

The record is processed as 7.1 asks, spikes first
([`remove_roughness_spikes`](/phonometry/reference/api/environment/acoustic-roughness/#remove_roughness_spikes)) and curvature next
([`curvature_processed_roughness`](/phonometry/reference/api/environment/acoustic-roughness/#curvature_processed_roughness)), then cut into segments of
`segment_length_m` overlapping by half. Each has its mean and linear
trend removed and a Hanning window applied; the squared magnitudes of
their discrete Fourier transforms are averaged into a one-sided spectral
density normalised by the window's energy, so that its sum over the lines
is the mean square of the roughness. Each one-third octave band of
wavenumber then collects the lines within it and the portions of the two
straddling its edges (Annex C, [`redistributed_band_energies`](/phonometry/reference/api/environment/acoustic-roughness/#redistributed_band_energies)), and
the level is $10 \lg (r^2_\mathrm{RMS} / r_0^2)$ with
$r_0 = 1\ \mathrm{\mu m}$ (Formula 1).

The bands reported are those whose nominal wavelength is at most a
quarter of the segment length (7.5) and whose upper edge lies below the
Nyquist wavenumber of the sampling.

**Parameters**

| Name | Description |
| :--- | :--- |
| `roughness_um` | The roughness record, in micrometres, at equal intervals, with joints, welds and defects already edited out. |
| `sample_spacing_m` | The sampling interval, in metres; 5.5 asks for 1 mm or less. |
| `spike_removal` | Whether to apply 7.2 first. |
| `curvature_processing` | Whether to apply 7.3 next. |
| `segment_length_m` | The length of each Fourier segment, in metres; at least 1 m (7.4.2). |

**Returns:** The spectrum, longest wavelength first, with the record length and the number of segments averaged.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a sampling interval above 1 mm, a segment shorter than 1 m, or a record shorter than one segment. |

## AcousticRoughnessSpectrum

```python
AcousticRoughnessSpectrum(
    wavelengths_m: NDArray[np.float64],
    levels_db: NDArray[np.float64],
    record_length_m: float | None = None,
    segment_count: int | None = None,
)
```

A one-third octave band spectrum of acoustic rail roughness (EN 15610).

Built by [`acoustic_roughness_spectrum`](/phonometry/reference/api/environment/acoustic-roughness/#acoustic_roughness_spectrum) from a record, by
[`average_roughness_spectra`](/phonometry/reference/api/environment/acoustic-roughness/#average_roughness_spectra) from several, or directly from the band
levels of a report, which is all the ISO 3095 checks need.

**Parameters**

| Name | Description |
| :--- | :--- |
| `wavelengths_m` | The nominal band wavelengths, in metres, from the longest to the shortest as clause 9 draws them; each names the base-ten one-third octave band of wavenumber it is nominal for. |
| `levels_db` | The acoustic roughness level $L_r$ of each band, dB re 1 µm. |
| `record_length_m` | The length of roughness the spectrum was taken from, in metres; `None` when not known. |
| `segment_count` | How many Fourier segments were averaged into it; `None` when not known. |

### AcousticRoughnessSpectrum.bands

*property*

The band index $k$ of each wavelength, centred on $10^{k/10}$ per metre.

### AcousticRoughnessSpectrum.level_at()

```python
AcousticRoughnessSpectrum.level_at(wavelength_m: float) -> float
```

The level of the band a nominal wavelength names, dB re 1 µm.

**Parameters**

| Name | Description |
| :--- | :--- |
| `wavelength_m` | A nominal band wavelength, in metres. |

**Returns:** The level of that band.

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | If the spectrum has no such band. |

### AcousticRoughnessSpectrum.plot()

```python
AcousticRoughnessSpectrum.plot(
    ax: Axes | None = None,
    *,
    limit_db: Mapping[float, float] | None = None,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the spectrum as EN 15610 clause 9 presents it.

Level against wavelength in decreasing order, one octave to 10 dB, with
a limit curve when one is given.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Axes to draw on; a new figure is made when omitted. |
| `limit_db` | A limit spectrum to draw with it, nominal wavelength in metres to level, such as [`REFERENCE_TRACK_ROUGHNESS_LIMIT_DB`](/phonometry/reference/api/environment/rolling-stock-noise/#reference_track_roughness_limit_db). |
| `language` | `"en"` or `"es"`. |
| `kwargs` | Passed to the spectrum line. |

**Returns:** The axes drawn on.

## average_roughness_spectra

```python
average_roughness_spectra(
    spectra: Sequence[AcousticRoughnessSpectrum],
) -> AcousticRoughnessSpectrum
```

The mean square average of roughness spectra of one line (7.6).

$$
L_r = 10 \lg \left( \frac{1}{N} \sum_{n=1}^{N} 10^{L_{r,n}/10} \right)
$$

band by band, with no weighting for where along the test section each
record was taken. ISO 3095 C.2.1 averages the spectra of a test section
the same way ("quadratically averaged") before comparing them with the
limit. Only the bands every spectrum has are averaged.

**Parameters**

| Name | Description |
| :--- | :--- |
| `spectra` | The spectra to average. |

**Returns:** The average, with the record lengths and segment counts summed when every spectrum carries them.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For no spectrum, or spectra with no band in common. |

## curvature_processed_roughness

```python
curvature_processed_roughness(
    roughness_um: ArrayLike,
    *,
    sample_spacing_m: float,
    curve_radius_m: float = 0.375,
) -> NDArray[np.float64]
```

The record as a wheel of radius 0,375 m would ride it (7.3).

At every sample $x_i$ a circle $C_i(x)$ of radius
$R$ passes through $r(x_i)$ with its centre above the
record, and the point is raised by the largest amount the record stands
above that circle:

$$
r'(x_i) = \max_x \left[ r(x) - C_i(x) \right] + r(x_i) = \max_x \left[ r(x) - \left( R - \sqrt{R^2 - (x - x_i)^2} \right) \right].
$$

A pit narrower than the circle is bridged at the height where the circle
rests on its rims; a crest is unchanged, since the circle through it lies
above its flanks. Only the samples whose circle height is within the range
of the record can win the maximum, so the search is limited to them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `roughness_um` | The roughness record, in micrometres, usually after [`remove_roughness_spikes`](/phonometry/reference/api/environment/acoustic-roughness/#remove_roughness_spikes). |
| `sample_spacing_m` | The sampling interval, in metres. |
| `curve_radius_m` | The radius $R$ of the circle, in metres; the 0,375 m of 7.3 by default. |

**Returns:** A new array $r'(x)$, in micrometres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an invalid record, spacing or radius. |

## redistributed_band_energies

```python
redistributed_band_energies(
    source_lower: ArrayLike,
    source_upper: ArrayLike,
    energies: ArrayLike,
    target_lower: ArrayLike,
    target_upper: ArrayLike,
) -> NDArray[np.float64]
```

Band energies moved onto other bands in proportion to their overlap (Annex C).

EN 15610 Annex C builds a one-third octave band from narrow band lines of
width $\gamma$: every line wholly inside the band counts in full and
the two lines that straddle its edges count for the portions
$\gamma_1$ and $\gamma_{n_k}$ of their width that lie inside
it,

$$
L_k = 10 \lg \left[ \frac{\gamma_1}{\gamma} S_1 + \sum_{j=2}^{n_k - 1} S_j + \frac{\gamma_{n_k}}{\gamma} S_{n_k} \right]
$$

(Formula C.1). Written for source bands of any width, that is the energy of
each source band shared among the target bands in proportion to how much
of its width, on the linear axis, each target band covers, which is the
form ISO 3095 Annex C asks for when the bands being shared are one-third
octaves of wavelength carried onto frequency ("adapted to non-constant
frequency bandwidths"). The energy of a source band outside every target
band is dropped.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_lower` | Lower edges of the source bands, on any linear axis (hertz, cycles per metre). |
| `source_upper` | Their upper edges, on the same axis. |
| `energies` | The energy of each source band: a mean square, not a level. |
| `target_lower` | Lower edges of the target bands, on the same axis. |
| `target_upper` | Their upper edges. |

**Returns:** The energy of each target band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For edges that are not finite, not increasing within a band or not one per band, or a negative energy. |

## remove_roughness_spikes

```python
remove_roughness_spikes(
    roughness_um: ArrayLike,
    *,
    sample_spacing_m: float,
) -> NDArray[np.float64]
```

The record with its narrow upward spikes replaced by straight lines (7.2).

A spike is a sample where the second derivative of the roughness falls
below $-10^7\ \mathrm{\mu m/m^2}$ and the first derivative changes
sign; its edges are the samples either side of it where the magnitude of
the first derivative falls below $5 \times 10^3\ \mathrm{\mu m/m}$,
and its width $w$ is the distance between them. It is removed, by
linear interpolation between its edges, when its height $h$ above
that line satisfies

$$
h > \frac{w^2}{a}, \qquad a = 3\ \mathrm{m},
$$

with $h$ and $w$ in metres, and the procedure is repeated
until a sweep removes nothing. A narrow peak is taken for a particle of
dirt; a broad one is roughness a wheel does feel, and stays.

The derivatives are central differences, as in the Annex B listing. That
listing repeats its sweep while any second derivative is below the
threshold, change of sign or not, which never ends on a sharp bend with
no extremum nor on a sharp peak the height test keeps; the sweep here
stops when a pass removes no spike, which is what "until no further spike
is detected" can mean for a peak that is detected and kept.

**Parameters**

| Name | Description |
| :--- | :--- |
| `roughness_um` | The roughness record $r(x)$, in micrometres, sampled at equal intervals, with joints, welds and defects already edited out (7.1 a) 1)). |
| `sample_spacing_m` | The sampling interval, in metres. |

**Returns:** A new array, the record with the spikes removed, in micrometres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a record that is not a finite one-dimensional array of at least three samples, or a spacing that is not positive. |

## roughness_measurement_lines

```python
roughness_measurement_lines(reference_width_mm: float) -> tuple[int, float]
```

How many parallel lines a rail's reference surface is measured on (6.4.3).

Up to 20 mm wide, one line on the centre line of the reference surface;
above 20 mm and up to 30 mm, three lines 5 mm apart; above 30 mm, three
lines 10 mm apart. More lines may be measured, but those compared with the
acceptance criteria follow this rule (6.4.3 NOTE).

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_width_mm` | The width $w_\mathrm{ref}$ of the reference surface, in millimetres. |

**Returns:** The number of lines and the distance between neighbouring lines, in millimetres (0 for a single line).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a width that is not positive. |

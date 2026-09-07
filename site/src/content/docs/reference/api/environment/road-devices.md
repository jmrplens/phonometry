---
title: "environment.propagation.road_devices"
description: "Single-number ratings of road traffic noise reducing devices (EN 1793)."
sidebar:
  label: "road_devices"
---

Single-number ratings of road traffic noise reducing devices (EN 1793).

A barrier beside a road is not judged band by band. It is judged by two
numbers, and both are the same operation on a spectrum nobody measures on
site: the normalised traffic noise spectrum of **EN 1793-3:1997**, eighteen
one-third octave bands from 100 Hz to 5 kHz carrying relative A-weighted
levels $L_i$ that stand for what a road sounds like at the roadside.

* **EN 1793-1:2012** rates absorption. What matters to the neighbour is the
  energy the device sends back across the road, so the rating is what is
  *not* absorbed, in decibels (Clause 5):

  $$
  DL_\alpha = -10 \lg\left| 1 - \frac{\sum_{i=1}^{18} \alpha_{\mathrm{S}i}\, 10^{0.1 L_i}} {\sum_{i=1}^{18} 10^{0.1 L_i}} \right|
  $$

  A measured $\alpha_\mathrm{S}$ can exceed one band by band, which
  can push the weighted ratio past 1 and leave the logarithm without an
  argument. The clause says so and fixes it: the ratio is limited to 0,99.

* **EN 1793-2:2012** rates airborne insulation with the same weighting
  (Clause 5.2), on the transmitted energy rather than the absorbed:

  $$
  DL_R = -10 \lg\left| \frac{\sum_{i=1}^{18} 10^{0.1 L_i}\, 10^{-0.1 R_i}} {\sum_{i=1}^{18} 10^{0.1 L_i}} \right|
  $$

Both are reported rounded to the nearest integer (EN 1793-1 Clause 6.1,
EN 1793-2 Clause 7.1), and both have a normative category ladder in their
Annex A: A1 to A5 for absorption, B1 to B4 for insulation, with A0 and B0
reserved for "not determined". The categories are read off the reported
integer, which is why the ladders have no gaps between their steps.

The two ratings answer different questions and are not comparable. A device
can be a perfect reflector and still keep the noise out (high $DL_R$,
low $DL_\alpha$); a device can be highly absorptive and let sound
through (the other way round). The declaration carries both.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ABSORPTION_CATEGORIES

*Constant* (`tuple`).

```python
ABSORPTION_CATEGORIES = (('A1', -2147483648, 3), ('A2', 4, 7), ('A3', 8, 11), ('A4', 12, 15), ('A5', 16, 2147483648))
```

## ABSORPTION_RATIO_LIMIT

*Constant* (`float`).

```python
ABSORPTION_RATIO_LIMIT = 0.99
```

## airborne_insulation_rating

```python
airborne_insulation_rating(
    sound_reduction_index_db: ArrayLike,
) -> RoadDeviceRating
```

`DL_R`, the EN 1793-2 single-number rating of airborne insulation.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sound_reduction_index_db` | $R$ in decibels, in the eighteen one-third octave bands of [`TRAFFIC_NOISE_BANDS_HZ`](/phonometry/reference/api/environment/road-devices/#traffic_noise_bands_hz). |

**Returns:** The rating, its reported integer and its Annex A category.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the input does not cover the eighteen bands, or is not finite. |

## INSULATION_CATEGORIES

*Constant* (`tuple`).

```python
INSULATION_CATEGORIES = (('B1', -2147483648, 14), ('B2', 15, 24), ('B3', 25, 34), ('B4', 35, 2147483648))
```

## NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB

*Constant* (`tuple`).

```python
NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB = (-20.0, -20.0, -18.0, -16.0, -15.0, -14.0, -13.0, -12.0, -11.0, -9.0, -8.0, -9.0, -10.0, -11.0, -13.0, -15.0, -16.0, -18.0)
```

## RoadDeviceRating

```python
RoadDeviceRating(
    rating: float,
    reported: int,
    category: str,
    quantity: str,
    bands_hz: NDArray[np.float64],
    values: NDArray[np.float64],
    weights: NDArray[np.float64],
)
```

One single-number rating of a road traffic noise reducing device.

**Attributes**

| Name | Description |
| :--- | :--- |
| `rating` | The rating before rounding, in dB. `DLα` (EN 1793-1) or `DL_R` (EN 1793-2), depending on `quantity`. |
| `reported` | The same rating rounded to the nearest integer, which is what a test report carries and what the category is read off. |
| `category` | The Annex A category of the reported value, `"A1"` to `"A5"` for absorption or `"B1"` to `"B4"` for insulation. |
| `quantity` | `"absorption"` or `"insulation"`. |
| `bands_hz` | The eighteen band centre frequencies, in Hz. |
| `values` | The per-band input the rating was weighted from: the sound absorption coefficients, or the sound reduction indices in dB. |
| `weights` | The normalised traffic noise spectrum, in dB. |

### RoadDeviceRating.plot()

```python
RoadDeviceRating.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the per-band input against the spectrum that weights it.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## RoadDeviceWarning

Raised when a rating is computed on data the standard bounds.

## sound_absorption_rating

```python
sound_absorption_rating(
    absorption_coefficients: ArrayLike,
) -> RoadDeviceRating
```

`DLα`, the EN 1793-1 single-number rating of sound absorption.

**Parameters**

| Name | Description |
| :--- | :--- |
| `absorption_coefficients` | $\alpha_\mathrm{S}$ in the eighteen one-third octave bands of [`TRAFFIC_NOISE_BANDS_HZ`](/phonometry/reference/api/environment/road-devices/#traffic_noise_bands_hz). |

**Returns:** The rating, its reported integer and its Annex A category.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the input does not cover the eighteen bands, or is not finite. |

**Warns**

| Warning | When |
| :--- | :--- |
| RoadDeviceWarning | If the weighted ratio reaches the 0,99 limit of Clause 5, which means the rating is the limit and not the data. |

## TRAFFIC_NOISE_BANDS_HZ

*Constant* (`tuple`).

```python
TRAFFIC_NOISE_BANDS_HZ = (100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0)
```

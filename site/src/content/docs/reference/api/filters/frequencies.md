---
title: "filters.frequencies"
description: "Frequency calculation logic according to ANSI/IEC standards."
sidebar:
  label: "frequencies"
---

Frequency calculation logic according to ANSI/IEC standards.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## FractionalOctaveBands

```python
FractionalOctaveBands(
    frequencies: NDArray[np.float64],
    lower_edges: NDArray[np.float64],
    upper_edges: NDArray[np.float64],
    labels: tuple[str, ...],
)
```

A set of fractional-octave bands: centres, edges and nominal labels.

What [`nominal_frequencies`](/phonometry/reference/api/filters/frequencies/#nominal_frequencies) returns and what an
[`OctaveFilterBank`](/phonometry/reference/api/filters/core/#octavefilterbank) is designed on. The three
frequency arrays are read-only, in hertz, one value per band in ascending
order; the labels are the IEC 61260-1 nominal mid-band frequencies, as
text (`"31.5"`, `"1k"`). It is a record with named fields rather than
a tuple, so it cannot be unpacked by position: read `.frequencies`,
`.lower_edges`, `.upper_edges` or `.labels`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | The exact mid-band frequencies $f_\mathrm{m}$, in hertz (IEC 61260-1:2014 5.4). |
| `lower_edges` | The lower band-edge frequencies $f_1$, in hertz. |
| `upper_edges` | The upper band-edge frequencies $f_2$, in hertz. |
| `labels` | The nominal mid-band frequency of each band, as a string. |

## nominal_frequencies

```python
nominal_frequencies(
    fraction: float,
    limits: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[Any] | None = None,
) -> FractionalOctaveBands
```

The fractional-octave bands that cover a frequency range.

The mid-band frequencies are the base-ten series of IEC 61260-1:2014 5.4,
$f_\mathrm{m} = 1000\,G^{x/b}$ Hz with $G = 10^{3/10}$ (an
even `fraction` shifts the series by half a band), and the band edges
sit a factor $G^{1/(2b)}$ either side of each centre. The first band
is the one nearest `limits[0]` and the last the first whose upper edge
reaches `limits[1]`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fraction` | Bandwidth fraction `b` (e.g., 1 for octaves, 3 for one-third octaves). |
| `limits` | `[f_min, f_max]` in hertz, a sequence or an array of the two (Default: `[12, 20000]`). |

**Returns:** A [`FractionalOctaveBands`](/phonometry/reference/api/filters/frequencies/#fractionaloctavebands) with the exact centres (`.frequencies`), the band edges (`.lower_edges` and `.upper_edges`) and the nominal labels (`.labels`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive or non-finite `fraction`. |
| TypeError | if `fraction` is not a single number. |

## normalized_frequencies

```python
normalized_frequencies(fraction: int | np.integer[Any]) -> list[float]
```

Standardized IEC center frequencies.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fraction` | 1 or 3 (Octave or 1/3 Octave). |

**Returns:** List of standard frequencies.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a `fraction` other than 1 and 3. |
| TypeError | if `fraction` is a flag, a text or an array where a whole number goes. |

---
title: "materials.diffusers.predicted_diffusion"
description: "Normalized diffusion coefficients as a book computes them, one row per angle."
sidebar:
  label: "predicted_diffusion"
---

Normalized diffusion coefficients as a book computes them, one row per angle.

A diffusion coefficient says how even a surface's polar response is, and a
scattering coefficient says how much energy left the specular direction. A
surface can score high on one and low on the other, which is why ISO 17497 is
two documents and why this subpackage keeps two catalogues.
`.measured_scattering` holds what a turntable measured; this holds what a
boundary element model computed, and the difference is not a detail of
provenance. Nobody built these surfaces.

Why keep a table of predictions at all
---------------------------------------
Because the table is a designer's argument, and the argument is in the
numbers. It walks one semicylinder up to twelve, and the diffusion coefficient
at 1 kHz goes from 0.93 to 0.22: a single device and an array of the same
device are not the same surface, however identical the cross-section. It walks
a set of semiellipses from 1 cm deep to 30 cm, and at 5 kHz the coefficient
goes from 0.02 to 0.65. Neither of those follows from a formula in the book,
and a reader with a measurement of one diffuser has nothing to compare it
against without something like this.

The angle is a row, not a column
---------------------------------
The page prints three lines per surface, headed 0, 57 and Random, so a surface
is three rows here and [`variant`](/phonometry/reference/api/io/io/#cataloguerow)
says which. The first two carry [`NormalizedDiffusionSpectrum.angle_of_incidence_deg`](/phonometry/reference/api/materials/predicted-diffusion/#normalizeddiffusionspectrum);
the random one has none to carry, because it is an arithmetic mean over ten
angles and belongs to no single one, and asking it for the field gets that
sentence rather than a number.

What the numbers are worth
--------------------------
They are a two-dimensional prediction of a thin panel with an open back, as
the book's own Section 5.2.5 says, so they stand for single-plane devices such
as semicircular arcs and not for a two-dimensional array of anything. The
random incidence row is an arithmetic average over ten angles without Paris's
formulation, which a measurement to ISO 17497-2 would apply, so it is not the
same average a laboratory would report. Both facts are quoted in the `about`
of the data file, in the book's words.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## DIFFUSION_BANDS_HZ

*Constant* (`tuple`).

```python
DIFFUSION_BANDS_HZ = (100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000)
```

## diffusion_named

```python
diffusion_named(name: str) -> tuple[NormalizedDiffusionSpectrum, ...]
```

Every published row whose description or section heading contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | A fragment of the printed description or of the numbered heading above it, matched without case. The heading is where the geometry is, so `"semiellipse"` and `"Schroeder"` find their sections and `"6 periods"` finds the rows that say so. |

**Returns:** The rows that match, in the order the tables are read, which is empty when no page has one. A surface answers with its three angles.

## NormalizedDiffusionSpectrum

```python
NormalizedDiffusionSpectrum(
    *,
    name: str,
    source: str,
    table: str = '',
    variant: str = '',
    basis: Mapping[str, str] = ...,
    approximate: frozenset[str] = frozenset(),
    derived: Mapping[str, str] = ...,
    converted: Mapping[str, tuple[str, str]] = ...,
    carried: Mapping[str, str] = ...,
    ranges: Mapping[str, tuple[float | None, float | None]] = ...,
    bounded_above: frozenset[str] = frozenset(),
    bounded_below: frozenset[str] = frozenset(),
    reported: Mapping[str, tuple[float | tuple[float, float], ...]] = ...,
    unquantified: Mapping[str, str] = ...,
    uncertainty: Mapping[str, float] = ...,
    not_derivable: Mapping[str, str] = ...,
    misprinted: Mapping[str, str] = ...,
    attributed_to: Mapping[str, str] = ...,
    group: str = '',
    note: str = '',
    diffusion_coefficient_100: float | None = None,
    diffusion_coefficient_125: float | None = None,
    diffusion_coefficient_160: float | None = None,
    diffusion_coefficient_200: float | None = None,
    diffusion_coefficient_250: float | None = None,
    diffusion_coefficient_315: float | None = None,
    diffusion_coefficient_400: float | None = None,
    diffusion_coefficient_500: float | None = None,
    diffusion_coefficient_630: float | None = None,
    diffusion_coefficient_800: float | None = None,
    diffusion_coefficient_1000: float | None = None,
    diffusion_coefficient_1250: float | None = None,
    diffusion_coefficient_1600: float | None = None,
    diffusion_coefficient_2000: float | None = None,
    diffusion_coefficient_2500: float | None = None,
    diffusion_coefficient_3150: float | None = None,
    diffusion_coefficient_4000: float | None = None,
    diffusion_coefficient_5000: float | None = None,
    angle_of_incidence_deg: float | None = None,
)
```

One surface at one angle of incidence, with its coefficient in each band.

**Attributes**

| Name | Description |
| :--- | :--- |
| `diffusion_coefficient_100` | Normalized diffusion coefficient in the 100 Hz one-third octave band, dimensionless, as printed. |
| `diffusion_coefficient_125` | The same in the 125 Hz band. |
| `diffusion_coefficient_160` | The same in the 160 Hz band. |
| `diffusion_coefficient_200` | The same in the 200 Hz band. |
| `diffusion_coefficient_250` | The same in the 250 Hz band. |
| `diffusion_coefficient_315` | The same in the 315 Hz band. |
| `diffusion_coefficient_400` | The same in the 400 Hz band. |
| `diffusion_coefficient_500` | The same in the 500 Hz band. |
| `diffusion_coefficient_630` | The same in the 630 Hz band. |
| `diffusion_coefficient_800` | The same in the 800 Hz band. |
| `diffusion_coefficient_1000` | The same in the 1 kHz band. |
| `diffusion_coefficient_1250` | The same in the 1.25 kHz band. |
| `diffusion_coefficient_1600` | The same in the 1.6 kHz band. |
| `diffusion_coefficient_2000` | The same in the 2 kHz band. |
| `diffusion_coefficient_2500` | The same in the 2.5 kHz band. |
| `diffusion_coefficient_3150` | The same in the 3.15 kHz band. |
| `diffusion_coefficient_4000` | The same in the 4 kHz band. |
| `diffusion_coefficient_5000` | The same in the 5 kHz band. |
| `angle_of_incidence_deg` | The angle the row was computed at, in degrees from the normal, as the page heads its line. `None` on a random incidence row, which is a mean over ten angles and is not one of them; [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) says so rather than leaving the caller to guess at a zero. |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `basis` | What the source says a value is: a field name, or `"row"` for the whole row, to one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases). Hopkins marks most of his Poisson ratios "Estimate", and those cells hold `"estimated"`; a datasheet that declares a class under a product standard would hold `"declared"`. A field with no entry takes the row's, and a row with neither is one whose source does not say, which is a different answer from any of the five. `basis_of` reads it. Independent of `derived`: this is what the source claims for a cell, that is what this library computed. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and it always follows again from the row's own cells. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page gives by reference to another of its rows (`carried` does). |
| `converted` | Field to `(figure, unit)`, the page's figure and the unit it is in, for a value this row holds in a unit the page does not use. Ver and Beranek print their damping materials in degrees Fahrenheit and pounds per square inch, and the row holds degrees Celsius and pascals, so `("3e5", "psi")` sits beside a modulus in pascals. The figure is kept as the page writes it, so the cell can always be read back in the page's own terms. The unit is the one the page prints with the figure or over its column. Long prints the figures of his musician bare, and the sabins recorded for them are a reading of the table, which is set in inches and pounds and names sabins on the next row; that row's note says so. A figure a packaged table prints with another SI prefix, such as the megapascals of Rossing Table 15.5, is held in the base unit with no entry here, and the table's `about` says so. |
| `carried` | Field to where the page gives it from, for a value the page gives by reference to another of its rows rather than on this one: a cell left blank under a block whose first row prints the figure, as in Ver and Beranek Table 8.7, or a description that reads "Parecido al anterior" and prints no row number, as three rows of Harris Chapter 32 do, which refers to the row above it. The value is the page's, and this says which of its rows gives it. |
| `ranges` | `(low, high)` for each field the page prints as an interval rather than a value. One end is `None` only for a bound whose open side the quantity has no limit on; the end the page prints is always a number, and a two-sided interval has two. |
| `bounded_above` | The subset of `ranges` the page prints as `< x` or `<= x`, where the low end is a floor and not a measurement. |
| `bounded_below` | The subset of `ranges` the page prints as `> x` or `>= x`, where the high end is the ceiling the quantity cannot pass and not a measurement: Cox gives an aerogel a porosity of `>0.75`, and the 1 beside it is what a porosity is, not what anybody measured. A quantity with no such ceiling leaves that end `None` rather than borrowing a number for it: ASHRAE prints `>45` for a duct wall whose radiated sound the background swamped, and a transmission loss has no value it cannot pass, so the open end is empty. It is never an infinity, which is not a number the page has and not a token JSON can carry. |
| `reported` | Field to the values the page lists for it, for a cell that prints several with no single one: `"25, 207, 230"` or `"96, 200-450"`, readings from as many studies. Each entry is a number or a `(low, high)` pair. Not a range, because the page did not print one, and not variants, because the page does not say which is which. |
| `unquantified` | Field to what the page printed in place of a number, for a cell that is neither empty nor numeric: `"Varies with frequency"`, `"model"`, `"…"` for a row of dots. What the page printed, and never a sentence about why the number is missing: `why_missing` composes that sentence around it, so a caller and a published table both get the cell as it reads on the page. |
| `uncertainty` | Field to the plus-or-minus the page prints beside the value, in the same unit. Cox prints an effective flow resistivity of `(540 +/- 92) x 10^3`, and two of his rows print an uncertainty as large as the value itself. What the interval means is not stated on the page, so it is not stated here either: it is the number the page prints beside the value and nothing more. |
| `misprinted` | Field to what the page prints there and why it cannot be that, for a cell whose defect is confirmed and registered in `docs/ERRATA.md`. The number is not served, because a catalogue that handed it over would put a value its own registry calls wrong behind every calculation downstream; it is not dropped either, because a reader reproducing the book needs to see what the book says. This is the narrowest of the hedges and the one that costs most to claim: a cell earns it only when the defect follows from the page itself or from something as settled as the molar mass of a named molecule, and never from one book disagreeing with another. |
| `not_derivable` | Field to why this library leaves it empty although the arithmetic would reach it. Bies leaves the speed of his aluminium honeycomb panels blank, and the modulus and the density beside it are effective ones, so `sqrt(E/rho)` would put a one-dimensional speed on a panel that has none. A row says so here, and nothing fills the cell afterwards. |
| `attributed_to` | Credit for a cell the book takes from someone else. Keyed by field name, or by `"row"` or `"table"` when the credit covers all of one. |
| `group` | The heading of the block this row sits under, when the table prints its rows in named groups: Cox files each material under `"Fibrous materials"`, `"Cellular materials"`, `"Granular materials"` or `"Other"`. Empty for a table that prints one list. |
| `note` | What the page says about this row beyond its numbers. |

### NormalizedDiffusionSpectrum.bands()

```python
NormalizedDiffusionSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### NormalizedDiffusionSpectrum.basis_of()

```python
NormalizedDiffusionSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### NormalizedDiffusionSpectrum.diffusion_coefficient()

```python
NormalizedDiffusionSpectrum.diffusion_coefficient(band_hz: int) -> float
```

The coefficient in one band, or a refusal that says what the page had.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | A one-third octave centre frequency from [`DIFFUSION_BANDS_HZ`](/phonometry/reference/api/materials/predicted-diffusion/#diffusion_bands_hz). |

**Returns:** The printed normalized diffusion coefficient, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the page has no number in that band, naming the row, the band and what the cell held instead; or when *band_hz* is not a band these tables print. |

### NormalizedDiffusionSpectrum.is_approximate()

```python
NormalizedDiffusionSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### NormalizedDiffusionSpectrum.is_derived()

```python
NormalizedDiffusionSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### NormalizedDiffusionSpectrum.printed()

```python
NormalizedDiffusionSpectrum.printed(
    field_name: str,
    *,
    wanted_by: str = 'the caller',
) -> float
```

One quantity this page prints, or a refusal that says what it had.

Every quantity of a row is optional, because the pages print different
columns, so a caller passing one into a function that requires a float
has to narrow it. Doing it here beats an assertion at each call site:
the refusal names the field, who wanted it and what the page had in
that cell, which is the difference between a cell the book left empty
and a cell holding the word "model".

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | The quantity wanted. |
| `wanted_by` | What wants it, named in the message. |

**Returns:** The value, as a float.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the page did not print a number there. |

### NormalizedDiffusionSpectrum.spectrum()

```python
NormalizedDiffusionSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### NormalizedDiffusionSpectrum.why_missing()

```python
NormalizedDiffusionSpectrum.why_missing(field_name: str) -> str
```

Why this field is `None`, in the page's own terms.

A catalogue that answers `None` and stops is asking the caller to
guess whether the material has no such property, whether the book
measured it and printed a dash, or whether the cell holds something
that is not a number. Each of those is a different answer.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** What the page had in that cell, or the empty string when the field is not missing at all. A field the page has no column for and this library cannot derive, because the cells it would need are themselves a range, answers that it does not follow.

**Raises**

| Exception | When |
| :--- | :--- |
| AttributeError | for a name this class does not have, because a misspelt field would otherwise answer as if the cell were empty. |

## PUBLISHED_DIFFUSION

*Constant* (`mapping`).

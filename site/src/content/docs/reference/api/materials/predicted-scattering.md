---
title: "materials.diffusers.predicted_scattering"
description: "Scattering coefficients a book computed, kept apart from the ones measured."
sidebar:
  label: "predicted_scattering"
---

Scattering coefficients a book computed, kept apart from the ones measured.

`.measured_scattering` holds what turntables measured under ISO 17497-1.
This holds the three tables of Cox & D'Antonio's Appendix C, which are
boundary element predictions of the correlation scattering coefficient, and
they are a separate catalogue for one reason: a row that says 0.45 because a
solver said so and a row that says 0.45 because a reverberation room said so
are not interchangeable, and a caller who mixes them without meaning to has no
way of finding out afterwards.

Three tables, three shapes
--------------------------
Table C.1 and Table C.2 are three-dimensional predictions of 3 m by 3 m
single-plane diffusers, at normal and at random incidence, over the one-third
octave bands from 250 Hz to 4 kHz; the angle is in the table's title, so every
row of one carries the same one. Table C.3 is two-dimensional, runs from
100 Hz to 5 kHz, and prints three lines per surface at 0, 56.9 and random
incidence, so there the angle is a field that varies inside the table. All
three are [`PredictedScatteringSpectrum`](/phonometry/reference/api/materials/predicted-scattering/#predictedscatteringspectrum), and
[`PredictedScatteringSpectrum.model`](/phonometry/reference/api/materials/predicted-scattering/#predictedscatteringspectrum) says which solver produced the row.

What the book says these are worth
-----------------------------------
More than usual, because the book spends a page on it. The correlation
scattering coefficient "interprets any absorption as being scattering", so the
formulation "needs to be revised for surfaces that partially absorb"; the
random incidence values of the two-dimensional table "tend to have raised
values at low frequencies"; and the coefficient "does not discriminate between
different diffusers in a consistent manner", because it reads a redirection as
a dispersion. Each of those is quoted in the `about` of the table it belongs
to, with the page. A row here is a modelling result to compare against, not a
specification.

The summary rows
----------------
Each group of Tables C.1 and C.2 closes with a row labelled `"h/L = 20"` or
`"h/L = 40"`, which cannot be read at face value: every surface of every
group has L = 20 cm and h between 2 and 10 cm, so the ratio is between 0.1 and
0.5. Read as a percentage they resolve, and three of the six carry exactly the
values of a row of their own group, which is how the reading was settled. The
book explains them nowhere. They are kept as rows, because they are rows.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## predicted_scattering_named

```python
predicted_scattering_named(
    name: str,
) -> tuple[PredictedScatteringSpectrum, ...]
```

Every predicted row whose description or heading contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | A fragment of the printed description or of the heading above it, matched without case. The headings are where the topology is: `"sinusoidal"`, `"batten"`, `"triangle"`, since a row of its own reads `"h = 4 cm, L = 20 cm"`. |

**Returns:** The rows that match, in the order the tables are read, which is empty when no table has one.

## PredictedScatteringSpectrum

```python
PredictedScatteringSpectrum(
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
    scattering_coefficient_100: float | None = None,
    scattering_coefficient_125: float | None = None,
    scattering_coefficient_160: float | None = None,
    scattering_coefficient_200: float | None = None,
    scattering_coefficient_250: float | None = None,
    scattering_coefficient_315: float | None = None,
    scattering_coefficient_400: float | None = None,
    scattering_coefficient_500: float | None = None,
    scattering_coefficient_630: float | None = None,
    scattering_coefficient_800: float | None = None,
    scattering_coefficient_1000: float | None = None,
    scattering_coefficient_1250: float | None = None,
    scattering_coefficient_1600: float | None = None,
    scattering_coefficient_2000: float | None = None,
    scattering_coefficient_2500: float | None = None,
    scattering_coefficient_3150: float | None = None,
    scattering_coefficient_4000: float | None = None,
    scattering_coefficient_5000: float | None = None,
    angle_of_incidence_deg: float | None = None,
    model: str = '',
)
```

One computed surface at one angle, band by band.

The band fields and the reading method come from
`ScatteringBands`,
which a measured row carries too, and the two classes are siblings rather
than one inheriting from the other, so a caller narrowing on the type
learns which kind of number they hold. The two fields below are what a
prediction has and a measurement does not.

The two three-dimensional tables start at 250 Hz, so their four lowest
band fields are `None` on every row: the book says the coefficient
below that "should be taken to be 0" and prints nothing, and filling
those cells with zeros would put the book's advice into the data where
nobody could tell it from a computed value.

**Attributes**

| Name | Description |
| :--- | :--- |
| `angle_of_incidence_deg` | The angle the row was computed at, in degrees from the normal. `None` where the page prints a word instead of a number: "Random" on an average over angles, "All/any" on the plane surface that scatters nothing at any of them, and [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) says which. |
| `model` | The solver behind the row, as the table's own title and the section that describes it give it: a two-dimensional or a three-dimensional boundary element prediction. It is not a hedge and not a note: it is what separates these rows from the measured ones. |
| `scattering_coefficient_100` | Scattering coefficient in the 100 Hz one-third octave band, dimensionless, as printed. `None` where the table prints nothing there, which is not the same as zero: a zero is a surface that sends every ray back along the specular direction. |
| `scattering_coefficient_125` | The same in the 125 Hz band. |
| `scattering_coefficient_160` | The same in the 160 Hz band. |
| `scattering_coefficient_200` | The same in the 200 Hz band. |
| `scattering_coefficient_250` | The same in the 250 Hz band. |
| `scattering_coefficient_315` | The same in the 315 Hz band. |
| `scattering_coefficient_400` | The same in the 400 Hz band. |
| `scattering_coefficient_500` | The same in the 500 Hz band. |
| `scattering_coefficient_630` | The same in the 630 Hz band. |
| `scattering_coefficient_800` | The same in the 800 Hz band. |
| `scattering_coefficient_1000` | The same in the 1 kHz band. |
| `scattering_coefficient_1250` | The same in the 1.25 kHz band. |
| `scattering_coefficient_1600` | The same in the 1.6 kHz band. |
| `scattering_coefficient_2000` | The same in the 2 kHz band. |
| `scattering_coefficient_2500` | The same in the 2.5 kHz band. |
| `scattering_coefficient_3150` | The same in the 3.15 kHz band. |
| `scattering_coefficient_4000` | The same in the 4 kHz band. |
| `scattering_coefficient_5000` | The same in the 5 kHz band. |
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

### PredictedScatteringSpectrum.bands()

```python
PredictedScatteringSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### PredictedScatteringSpectrum.basis_of()

```python
PredictedScatteringSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### PredictedScatteringSpectrum.is_approximate()

```python
PredictedScatteringSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### PredictedScatteringSpectrum.is_derived()

```python
PredictedScatteringSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### PredictedScatteringSpectrum.printed()

```python
PredictedScatteringSpectrum.printed(
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

### PredictedScatteringSpectrum.scattering_coefficient()

```python
PredictedScatteringSpectrum.scattering_coefficient(band_hz: int) -> float
```

The coefficient in one band, or a refusal that says what the page had.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | A one-third octave centre frequency from [`SCATTERING_BANDS_HZ`](/phonometry/reference/api/materials/measured-scattering/#scattering_bands_hz). |

**Returns:** The scattering coefficient, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the table has no number in that band, naming the row, the band and what the cell held instead; or when *band_hz* is not a band these tables print. |

### PredictedScatteringSpectrum.spectrum()

```python
PredictedScatteringSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### PredictedScatteringSpectrum.why_missing()

```python
PredictedScatteringSpectrum.why_missing(field_name: str) -> str
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

## PUBLISHED_PREDICTED_SCATTERING

*Constant* (`mapping`).

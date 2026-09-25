---
title: "materials.diffusers.measured_scattering"
description: "Scattering coefficients as the books print them, one row per surface."
sidebar:
  label: "measured_scattering"
---

Scattering coefficients as the books print them, one row per surface.

A geometric room acoustics model asks for one number per surface per band,
the scattering coefficient, and has no way of working it out. The rest of
this subpackage computes it: `.reverberation_room_scattering` runs the
ISO 17497-1 procedure on four reverberation times, and `.design`
predicts a polar response from a well sequence. This module holds what other
people measured, so that a modeller who has neither a turntable nor a
boundary element solver has somewhere to start, and so that a measurement
made here has published values to sit beside.

Scattering is not diffusion, and both live here
------------------------------------------------
ISO 17497 is two documents and two quantities. Part 1 measures the
*scattering coefficient*, the fraction of reflected energy that leaves the
specular direction, from four reverberation times in a room with a turning
table; it says nothing about where that energy goes. Part 2 measures the
*diffusion coefficient*, how even the polar response is, and a surface can
score high on one and low on the other. A catalogue that put them in one
field would let a caller pass a diffusion coefficient to a model that wants
a scattering coefficient, which is a silent error, so they are two classes
and two catalogues: [`PUBLISHED_SCATTERING`](/phonometry/reference/api/materials/measured-scattering/#published_scattering) here, and the diffusion
coefficients of ISO 17497-2 where they belong.

The band is the field
---------------------
These tables are set in one-third octave bands, so each band is a field of
its own, `scattering_coefficient_1000` and so on, with the band's centre
frequency in hertz as the suffix and no unit because the quantity has none.
Every hedge of [`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow) is keyed
by field name, so a band the page leaves empty says so through
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) rather than
answering zero, and a zero here would read as a perfectly specular surface.
[`ScatteringCoefficientSpectrum.bands`](/phonometry/reference/api/materials/measured-scattering/#scatteringcoefficientspectrumbands) and
[`spectrum`](/phonometry/reference/api/materials/measured-scattering/#scatteringcoefficientspectrumspectrum) hand the row back as a
spectrum for the caller who wants one.

What the numbers are worth
--------------------------
A row is a surface of that description, measured once, by one team, in one
room. Cox prints no uncertainty and no laboratory, and the spread between
teams is not small: the same battens, 10 cm high and 10 cm wide on a 20 cm
period, appear twice in Appendix D, credited to two different papers, and
read 0.28 and 0.44 at 630 Hz. Nothing is wrong with either; that is how wide
the method is. A coefficient above one is likewise not an error but what the
formula gave, since ISO 17497-1 derives it from a ratio of reverberation
times and puts no ceiling on the result.

The surfaces are described, not named. A row reads `"h = w = 10 cm,
L = 2h"` and means nothing without the group heading above it, so
[`group`](/phonometry/reference/api/io/io/#cataloguerow) carries that
heading and [`scattering_named`](/phonometry/reference/api/materials/measured-scattering/#scattering_named) matches on either.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PUBLISHED_SCATTERING

*Constant* (`mapping`).

## SCATTERING_BANDS_HZ

*Constant* (`tuple`).

```python
SCATTERING_BANDS_HZ = (100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000)
```

## scattering_named

```python
scattering_named(
    name: str,
    *,
    catalogue: Mapping[str, ScatteringCoefficientSpectrum] | None = None,
) -> tuple[ScatteringCoefficientSpectrum, ...]
```

Every row whose description or group contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | A fragment of the printed description or of the group heading above it, matched without case. The headings are where the useful words are: `"pyramid"`, `"vegetation"`, `"batten"`, since a row of its own reads `"h = w = 10 cm, L = 2h"`. |
| `catalogue` | The rows to search in place of [`PUBLISHED_SCATTERING`](/phonometry/reference/api/materials/measured-scattering/#published_scattering): a catalogue of your own that [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) returns, `PUBLISHED_SCATTERING \| mine` to search both at once, or any mapping of key to row (Default: `None`, which searches [`PUBLISHED_SCATTERING`](/phonometry/reference/api/materials/measured-scattering/#published_scattering)). |

**Returns:** The rows that match, in catalogue order, which is empty when no row has one.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a *catalogue* that is not a mapping, or that holds a row that is not a [`ScatteringCoefficientSpectrum`](/phonometry/reference/api/materials/measured-scattering/#scatteringcoefficientspectrum), naming its key. |

## ScatteringCoefficientSpectrum

```python
ScatteringCoefficientSpectrum(
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
    provenance: Provenance | None = None,
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
)
```

One measured surface of a published table, band by band.

The geometry is part of [`name`](/phonometry/reference/api/io/io/#cataloguerow), as the page prints
it, and the family it belongs to is [`group`](/phonometry/reference/api/io/io/#cataloguerow): pulling
`h` and `L` into fields would mean deciding what the height of a
randomly arranged array of blocks is, and the pages do not agree on which
letters they use.

The band fields and the reading method come from
`ScatteringBands`,
which a computed row carries too. What this class says, and what its name
is for, is that the numbers were measured. It does not inherit from the
predicted class and the predicted class does not inherit from it, so a
caller narrowing on the type gets a straight answer.

**Attributes**

| Name | Description |
| :--- | :--- |
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
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and on every row the library builds it follows again from the row's own cells: `from_printed` writes it, and nothing else in the library does. One a caller passes to the literal constructor is the caller's word, which the row keeps and `printed_fields` leaves out with its value, as it leaves out every derived one. When the printed cells a value rests on do not all have one `basis`, the text names the basis of each, so a modulus worked out from a plate speed and a Poisson ratio Hopkins marks as an estimate says it rests on that estimate. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page gives by reference to another of its rows (`carried` does). |
| `converted` | Field to `(figure, unit)`, the page's figure and the unit it is in, for a value this row holds in a unit the page does not use. Ver and Beranek print their damping materials in degrees Fahrenheit and pounds per square inch, and the row holds degrees Celsius and pascals, so `("3e5", "psi")` sits beside a modulus in pascals. The figure is kept as the page writes it, so the cell can always be read back in the page's own terms. The unit is the one the page prints with the figure or over its column. Long prints the figures of his musician bare, and the sabins recorded for them are a reading of the table, which is set in inches and pounds and names sabins on the next row; that row's note says so. A figure written in another unit of the same kind as the field's (`thickness_m` for `thickness_mm`, `flow_resistivity_kpa_s_m2` for `flow_resistivity_pa_s_m2`) is converted by `from_printed` and recorded here, whether it is a value, the end of a range or one of several readings; for a range the figure is the printed end of a bound, or both ends as `"5 to 10"`, and for readings the list as the page gives it. A packaged table transcribed in the base unit with only its SI prefix changed, such as the megapascals of Rossing Table 15.5, holds no entry here, and the table's `about` says so. |
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
| `provenance` | The document the row was read from, for a row read from a caller's catalogue file: its kind, version, the day it was consulted, the laboratory and the report. `None` on every packaged row, whose `source` cites a page. A refusal names the document by its kind (`"the datasheet prints an upper bound of ..."`), where a row without one says `"the page"`; and the fields of its `field_test_standards` are fields of the row. |

### ScatteringCoefficientSpectrum.bands()

```python
ScatteringCoefficientSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### ScatteringCoefficientSpectrum.basis_of()

```python
ScatteringCoefficientSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### ScatteringCoefficientSpectrum.from_printed()

*classmethod*

```python
ScatteringCoefficientSpectrum.from_printed(**cells: Any) -> Self
```

A row built from the cells its page prints, completed and marked.

The one path that works anything out. The cells are what the page
prints, under the field names of the class and with the hedges each
cell carries, as a data file writes them. A figure written in another
unit of the same kind as its field (`thickness_m` for
`thickness_mm`, `flow_resistivity_kpa_s_m2` for
`flow_resistivity_pa_s_m2`), or in a unit the class takes as an
alias of its own (an
[`AbsorptionAreaSpectrum`](/phonometry/reference/api/materials/measured/#absorptionareaspectrum) takes
`absorption_area_125_ft2` for `absorption_area_125_m2`), is
converted on its digits with an exact factor and rounded once,
whether it is a value or stands as the key of a hedge (the ends of a
range, the readings of a list and a plus-or-minus convert with it),
and `converted` records the figure and its unit. Every number
of one cell is written in one unit. The row is then
built and held to the contract the class docstring lists, so every
cell is checked before any arithmetic reads it. Last, the class
fills what follows from those cells (a modulus from a plate speed, a
density and a Poisson ratio), never over a cell that holds a value
or one the row says something else about, and `derived` says
how each filled value was reached and, when the cells it rests on
do not share one `basis`, the basis of each. Cells the
arithmetic cannot take are refused rather than turned into a value
that would be wrong: a modulus of 1 GPa and a shear modulus of
0.1 GPa give a Poisson ratio of 4, which no isotropic solid has, and
a row whose cells are not meant to give a value says so in
`not_derivable`, which keeps the arithmetic from running.

`Cls(...)` stays literal: it holds what it is given and works
nothing out. To change a cell of a row and have what follows from
it follow again, change it in `printed_fields` and build again
here; `dataclasses.replace` would copy the derived values as they
were:

```text
cells = row.printed_fields()
cells["density_kg_m3"] = 2400.0
row = type(row).from_printed(**cells)
```

**Parameters**

| Name | Description |
| :--- | :--- |
| `cells` | The printed cells, as keywords of the class. |

**Returns:** The row, with what follows from its cells filled in.

**Raises**

| Exception | When |
| :--- | :--- |
| CatalogueError | for a cell the contract refuses; for a `derived` among the cells, which is this method's to write; for a figure under a unit alias that is not a finite number, or that names a cell given under its own name or under another alias as well; for the numbers of one cell written in two units, a name two fields of one kind could both take, or a figure whose text field saying what it is of is empty; and for printed cells a value that follows from them cannot be worked out of, naming the value and the cells. |
| TypeError | for a name that is neither a field of the class nor a unit alias of one. |

### ScatteringCoefficientSpectrum.is_approximate()

```python
ScatteringCoefficientSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### ScatteringCoefficientSpectrum.is_derived()

```python
ScatteringCoefficientSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### ScatteringCoefficientSpectrum.printed()

```python
ScatteringCoefficientSpectrum.printed(
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

### ScatteringCoefficientSpectrum.printed_fields()

```python
ScatteringCoefficientSpectrum.printed_fields() -> dict[str, Any]
```

The cells the page prints, as `from_printed` takes them.

Every field, the name, the citation, the table and every hedge
included, except the values this library derived, `derived`
itself, and a field left at a default that holds nothing (a quantity
the page leaves out, an empty text or hedge). A text field whose
default says something is kept even when it holds no text: the
`per` of an area per unit is a person unless the row says
otherwise, and a row that leaves it empty has said otherwise. A
value converted from the page's unit and one the page gives by
reference to another of its rows are the page's, so they stay, with
`converted` and `carried` beside them.

For every row `from_printed` builds, and so for every packaged
one, `type(row).from_printed(**row.printed_fields())` is the row
again, and changing a cell before building it again is how a row is
edited without carrying a derived value that no longer follows from
it. A `derived` passed to the literal constructor is the caller's
own; it is left out here with its value, like every derived one, so
building again gives back only what the class works out.

**Returns:** A new dictionary of constructor keywords. The values are the ones the row holds, frozen as the row holds them.

### ScatteringCoefficientSpectrum.scattering_coefficient()

```python
ScatteringCoefficientSpectrum.scattering_coefficient(band_hz: int) -> float
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

### ScatteringCoefficientSpectrum.spectrum()

```python
ScatteringCoefficientSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### ScatteringCoefficientSpectrum.values_at()

```python
ScatteringCoefficientSpectrum.values_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
```

The row's value at each of *frequencies_hz*, or a refusal.

The adapter for a function that takes one value per band by position
(the absorption of a surface in a reverberation formula, the
transmission loss of a panel at the frequencies an enclosure model
asks for), because an array handed over by position cannot say
which band is missing and a row can. Each frequency is read as the
band of these tables whose centre is nearest on a logarithmic scale,
and matches it when it lies within a sixth of the spacing between
bands: a sixth of an octave for octave bands, an eighteenth for
one-third octave bands. That takes the nominal centre, the exact
base-ten one and the exact base-two one alike (160 Hz, 158.49 Hz and
157.49 Hz are one band) and never reaches the next band. A band the
row does not print is refused, as [`printed`](/phonometry/reference/api/io/io/#cataloguerowprinted)
refuses it, with what the page had there; it is never read as zero
and never filled from its neighbours.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Band centre frequencies, in hertz, of any shape. |

**Returns:** A new array of the same shape, one value per frequency.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a frequency that is not finite and positive, for one that matches none of the bands, naming the nearest, and for a band this row does not print, naming the row, the band and what the page had in that cell. |

### ScatteringCoefficientSpectrum.why_missing()

```python
ScatteringCoefficientSpectrum.why_missing(field_name: str) -> str
```

Why this field is `None`, in the page's own terms.

A catalogue that answers `None` and stops is asking the caller to
guess whether the material has no such property, whether the book
measured it and printed a dash, or whether the cell holds something
that is not a number. Each of those is a different answer.

The sentence names the document by its kind: `"the datasheet"`,
`"the test report"`, and `"the page"` for a row with no
`provenance`, which is every packaged one. For a cell the row
holds in another unit than the page's, a bound, a range or a list
quotes the page's figure and unit first and the row's value after
it: `"the datasheet prints a lower bound of 5 kPa s/m2 (5000 Pa
s/m2) and no value"`, never a figure the page does not print.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** What the page had in that cell, or the empty string when the field is not missing at all. A field the page has no column for and this library cannot derive, because the cells it would need are themselves a range, answers that it does not follow.

**Raises**

| Exception | When |
| :--- | :--- |
| AttributeError | for a name this class does not have, because a misspelt field would otherwise answer as if the cell were empty. |

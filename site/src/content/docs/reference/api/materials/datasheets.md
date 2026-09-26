---
title: "materials.absorbers.datasheets"
description: "Sound absorption as a data sheet or a test report prints it."
sidebar:
  label: "datasheets"
---

Sound absorption as a data sheet or a test report prints it.

The absorption tables of the books ([`measured`](/phonometry/reference/api/materials/measured/))
print one Sabine coefficient per octave and rarely say how it was measured. A
product's data sheet, its declaration of performance and the laboratory's
test report print something narrower and better defined, and they print it
in two shapes that are not the same quantity:

* the **sound absorption coefficient** $\alpha_\mathrm{s}$ of ISO 354,
  one value per one-third octave band as the reverberation room measured it,
  which can exceed 1 (ISO 354 3.9, NOTE 2, gives diffraction effects as the
  reason) and carries every digit the laboratory reported; and
* the **practical sound absorption coefficient** $\alpha_\mathrm{p}$ of
  ISO 11654 Clause 4.1, one value per octave band from 125 Hz to 4 kHz, the
  mean of the three one-third octaves in it rounded in steps of 0,05 and
  capped at 1,00.

The two are two classes here, [`ThirdOctaveAbsorptionSpectrum`](/phonometry/reference/api/materials/datasheets/#thirdoctaveabsorptionspectrum) and
[`PracticalAbsorptionSpectrum`](/phonometry/reference/api/materials/datasheets/#practicalabsorptionspectrum), because the band resolution and the
rounding are part of what the number is, and a row that held either under
one name would let an $\alpha_\mathrm{p}$ pass for a measurement it
was averaged and rounded from. The quantity lives in the class, never in a
flag, and a catalogue file says which one it holds by its `row_type`.

Both carry the single-number rating the sheet prints beside the bands, the
weighted sound absorption coefficient $\alpha_\mathrm{w}$ of ISO 11654
Clause 4.2 with its shape indicators and its class, and both work it out
again from the bands with [`PracticalAbsorptionSpectrum.rating`](/phonometry/reference/api/materials/datasheets/#practicalabsorptionspectrumrating) or
[`ThirdOctaveAbsorptionSpectrum.rating`](/phonometry/reference/api/materials/datasheets/#thirdoctaveabsorptionspectrumrating). The printed rating is kept as
printed; the one worked out is the library's, and when a catalogue file is
read the two are compared and any difference is noted beside the catalogue,
never reconciled.

The 125 Hz octave of $\alpha_\mathrm{p}$ is defined like the others
(ISO 11654 Clause 4.1 forms $\alpha_\mathrm{p}$ for each octave band,
and Clause 5.2 plots it from 125 Hz) and is not rated: the reference curve
starts at 250 Hz, and Clause 1 says the rating is not appropriate below it.
So a row holds it and [`PracticalAbsorptionSpectrum.rating`](/phonometry/reference/api/materials/datasheets/#practicalabsorptionspectrumrating) never reads
it.

Nothing here ships with data. A caller's own catalogue holds these rows, read
by [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) from the file the caller typed from
the sheet.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PracticalAbsorptionSpectrum

```python
PracticalAbsorptionSpectrum(
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
    weighted_absorption_coefficient: float | None = None,
    shape_indicator: str = '',
    absorption_class: str = '',
    noise_reduction_coefficient: float | None = None,
    mounting: str = '',
    thickness_mm: float | None = None,
    construction_depth_mm: float | None = None,
    practical_absorption_coefficient_125: float | None = None,
    practical_absorption_coefficient_250: float | None = None,
    practical_absorption_coefficient_500: float | None = None,
    practical_absorption_coefficient_1000: float | None = None,
    practical_absorption_coefficient_2000: float | None = None,
    practical_absorption_coefficient_4000: float | None = None,
)
```

One specimen of a data sheet, with its practical coefficient per octave.

The practical sound absorption coefficient $\alpha_\mathrm{p}$ of
ISO 11654 Clause 4.1 is the mean of the three one-third-octave
coefficients of ISO 354 inside an octave, worked out to the second
decimal, rounded in steps of 0,05 and set to 1,00 when it rounds above.
Six values from 125 Hz to 4 kHz all ending in 0 or 5 look like these,
though only a sheet that names them says so. A row of this class holds
them as printed, a value above 1,00 or off the steps included: the
reader of a catalogue file notes such a value, and nothing here corrects
it.

A declaration under a product standard declares the coefficients as a
level no result falls below (EN 13162 Clause 4.3.11 does, for mineral
wool), so a sheet that says it declares them is recorded with
[`basis`](/phonometry/reference/api/io/io/#cataloguerow) `"declared"`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `practical_absorption_coefficient_125` | $\alpha_\mathrm{p}$ in the 125 Hz octave band, dimensionless. Defined like the others and not rated (ISO 11654 Clause 1). |
| `practical_absorption_coefficient_250` | The same in the 250 Hz band. |
| `practical_absorption_coefficient_500` | The same in the 500 Hz band. |
| `practical_absorption_coefficient_1000` | The same in the 1 kHz band. |
| `practical_absorption_coefficient_2000` | The same in the 2 kHz band. |
| `practical_absorption_coefficient_4000` | The same in the 4 kHz band. |
| `weighted_absorption_coefficient` | The weighted sound absorption coefficient $\alpha_\mathrm{w}$ the sheet prints (ISO 11654 Clause 4.2), dimensionless: the shifted reference curve read at 500 Hz, a multiple of 0,05 from 0 to 1. |
| `shape_indicator` | The shape indicators printed after it, the letters only: `"MH"` for `0,70(MH)` (ISO 11654 Clause 4.3). Empty when the sheet prints none, which on a sheet that prints the rating is also what a curve without an excess looks like. |
| `absorption_class` | The sound absorption class of ISO 11654 Annex B, `"A"` to `"E"` or `"Not classified"`, as the sheet prints it. |
| `noise_reduction_coefficient` | The NRC a sheet prints under ASTM C423, dimensionless: the mean of the Sabine coefficients at 250, 500, 1000 and 2000 Hz rounded to 0,05. Held as printed; no function of this library works it out, so nothing compares it. |
| `mounting` | The test mounting as the sheet prints it: `"A"` for a specimen laid against the room surface, `"E-200"` for one over an air space whose suffix is the distance in millimetres from its exposed face to the room surface behind it (ISO 354 Annex B). Empty for a sheet that prints none, which is not the same as mounting A. |
| `thickness_mm` | The thickness of the specimen, in millimetres. |
| `construction_depth_mm` | The depth of construction ISO 11654 Clause 5.4 asks a result to state for a product mounted over an air space, in millimetres: from the room surface to the exposed face of the absorber (its Figure 2), which is what some sheets call the total construction height. It is not the air space alone: the absorber's thickness is part of it. |
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

### PracticalAbsorptionSpectrum.bands()

```python
PracticalAbsorptionSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### PracticalAbsorptionSpectrum.basis_of()

```python
PracticalAbsorptionSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### PracticalAbsorptionSpectrum.from_printed()

*classmethod*

```python
PracticalAbsorptionSpectrum.from_printed(**cells: Any) -> Self
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

### PracticalAbsorptionSpectrum.is_approximate()

```python
PracticalAbsorptionSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### PracticalAbsorptionSpectrum.is_derived()

```python
PracticalAbsorptionSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### PracticalAbsorptionSpectrum.practical_absorption_coefficient()

```python
PracticalAbsorptionSpectrum.practical_absorption_coefficient(
    band_hz: int,
) -> float
```

The practical coefficient in one octave, or a refusal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | An octave-band centre frequency from 125 Hz to 4000 Hz. |

**Returns:** The printed $\alpha_\mathrm{p}$, as a float.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the sheet has no number in that band, naming the row, the band and what the cell held instead; or when *band_hz* is not one of the six octaves. |

### PracticalAbsorptionSpectrum.printed()

```python
PracticalAbsorptionSpectrum.printed(
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

### PracticalAbsorptionSpectrum.printed_fields()

```python
PracticalAbsorptionSpectrum.printed_fields() -> dict[str, Any]
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

### PracticalAbsorptionSpectrum.rating()

```python
PracticalAbsorptionSpectrum.rating() -> AbsorptionRatingResult
```

The weighted sound absorption coefficient of the row's octaves.

[`weighted_absorption`](/phonometry/reference/api/materials/rating/#weighted_absorption) on the five rating
bands, 250 Hz to 4 kHz (ISO 11654 Clause 4.2), which snaps each
value to the 0,05 grid and caps it at 1,00 as Clause 4.1 would have.
The 125 Hz band is not read. The rating the sheet prints beside the
bands is not consulted either: this is the one the bands give, and
[`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) notes when the two differ.

**Returns:** The [`AbsorptionRatingResult`](/phonometry/reference/api/materials/rating/#absorptionratingresult), with $\alpha_\mathrm{w}$, the shape indicators and the class.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a rating band the row does not print, naming the row, the band and what the sheet had there; nothing is filled in for it. |

### PracticalAbsorptionSpectrum.spectrum()

```python
PracticalAbsorptionSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### PracticalAbsorptionSpectrum.values_at()

```python
PracticalAbsorptionSpectrum.values_at(
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

### PracticalAbsorptionSpectrum.why_missing()

```python
PracticalAbsorptionSpectrum.why_missing(field_name: str) -> str
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

## ThirdOctaveAbsorptionSpectrum

```python
ThirdOctaveAbsorptionSpectrum(
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
    weighted_absorption_coefficient: float | None = None,
    shape_indicator: str = '',
    absorption_class: str = '',
    noise_reduction_coefficient: float | None = None,
    mounting: str = '',
    thickness_mm: float | None = None,
    construction_depth_mm: float | None = None,
    absorption_coefficient_50: float | None = None,
    absorption_coefficient_63: float | None = None,
    absorption_coefficient_80: float | None = None,
    absorption_coefficient_100: float | None = None,
    absorption_coefficient_125: float | None = None,
    absorption_coefficient_160: float | None = None,
    absorption_coefficient_200: float | None = None,
    absorption_coefficient_250: float | None = None,
    absorption_coefficient_315: float | None = None,
    absorption_coefficient_400: float | None = None,
    absorption_coefficient_500: float | None = None,
    absorption_coefficient_630: float | None = None,
    absorption_coefficient_800: float | None = None,
    absorption_coefficient_1000: float | None = None,
    absorption_coefficient_1250: float | None = None,
    absorption_coefficient_1600: float | None = None,
    absorption_coefficient_2000: float | None = None,
    absorption_coefficient_2500: float | None = None,
    absorption_coefficient_3150: float | None = None,
    absorption_coefficient_4000: float | None = None,
    absorption_coefficient_5000: float | None = None,
    absorption_coefficient_6300: float | None = None,
    absorption_coefficient_8000: float | None = None,
    absorption_coefficient_10000: float | None = None,
)
```

One specimen of a test report, with its coefficient per one-third octave.

The sound absorption coefficient $\alpha_\mathrm{s}$ of ISO 354,
as the reverberation room measured it: one value per one-third octave
band, 100 Hz to 5 kHz in the standard's range and from 50 Hz to 10 kHz
where a laboratory reports more. A value above 1 is common and not an
error: ISO 354 (3.9, NOTE 2) says a coefficient evaluated from
reverberation times can exceed 1,0, for example because of diffraction
effects. Nothing here caps it.

`practical` turns the row into its practical coefficients, and
`rating` rates it; both leave out an octave the row cannot give
all three of its one-third octaves for. A negative coefficient, which a
measurement can give in a band where the specimen adds almost nothing to
the room's absorption, is never read as 0 nor left out of a mean: the
octave it falls in gets no practical coefficient, and `rating`
refuses it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `absorption_coefficient_50` | $\alpha_\mathrm{s}$ in the 50 Hz one-third octave band, dimensionless, as printed. |
| `absorption_coefficient_63` | The same in the 63 Hz band. |
| `absorption_coefficient_80` | The same in the 80 Hz band. |
| `absorption_coefficient_100` | The same in the 100 Hz band. |
| `absorption_coefficient_125` | The same in the 125 Hz band. |
| `absorption_coefficient_160` | The same in the 160 Hz band. |
| `absorption_coefficient_200` | The same in the 200 Hz band. |
| `absorption_coefficient_250` | The same in the 250 Hz band. |
| `absorption_coefficient_315` | The same in the 315 Hz band. |
| `absorption_coefficient_400` | The same in the 400 Hz band. |
| `absorption_coefficient_500` | The same in the 500 Hz band. |
| `absorption_coefficient_630` | The same in the 630 Hz band. |
| `absorption_coefficient_800` | The same in the 800 Hz band. |
| `absorption_coefficient_1000` | The same in the 1 kHz band. |
| `absorption_coefficient_1250` | The same in the 1.25 kHz band. |
| `absorption_coefficient_1600` | The same in the 1.6 kHz band. |
| `absorption_coefficient_2000` | The same in the 2 kHz band. |
| `absorption_coefficient_2500` | The same in the 2.5 kHz band. |
| `absorption_coefficient_3150` | The same in the 3.15 kHz band. |
| `absorption_coefficient_4000` | The same in the 4 kHz band. |
| `absorption_coefficient_5000` | The same in the 5 kHz band. |
| `absorption_coefficient_6300` | The same in the 6.3 kHz band. |
| `absorption_coefficient_8000` | The same in the 8 kHz band. |
| `absorption_coefficient_10000` | The same in the 10 kHz band. |
| `weighted_absorption_coefficient` | The weighted sound absorption coefficient $\alpha_\mathrm{w}$ the sheet prints (ISO 11654 Clause 4.2), dimensionless: the shifted reference curve read at 500 Hz, a multiple of 0,05 from 0 to 1. |
| `shape_indicator` | The shape indicators printed after it, the letters only: `"MH"` for `0,70(MH)` (ISO 11654 Clause 4.3). Empty when the sheet prints none, which on a sheet that prints the rating is also what a curve without an excess looks like. |
| `absorption_class` | The sound absorption class of ISO 11654 Annex B, `"A"` to `"E"` or `"Not classified"`, as the sheet prints it. |
| `noise_reduction_coefficient` | The NRC a sheet prints under ASTM C423, dimensionless: the mean of the Sabine coefficients at 250, 500, 1000 and 2000 Hz rounded to 0,05. Held as printed; no function of this library works it out, so nothing compares it. |
| `mounting` | The test mounting as the sheet prints it: `"A"` for a specimen laid against the room surface, `"E-200"` for one over an air space whose suffix is the distance in millimetres from its exposed face to the room surface behind it (ISO 354 Annex B). Empty for a sheet that prints none, which is not the same as mounting A. |
| `thickness_mm` | The thickness of the specimen, in millimetres. |
| `construction_depth_mm` | The depth of construction ISO 11654 Clause 5.4 asks a result to state for a product mounted over an air space, in millimetres: from the room surface to the exposed face of the absorber (its Figure 2), which is what some sheets call the total construction height. It is not the air space alone: the absorber's thickness is part of it. |
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

### ThirdOctaveAbsorptionSpectrum.absorption_coefficient()

```python
ThirdOctaveAbsorptionSpectrum.absorption_coefficient(band_hz: int) -> float
```

The coefficient in one one-third octave band, or a refusal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | A one-third-octave centre frequency from 50 Hz to 10 kHz. |

**Returns:** The printed $\alpha_\mathrm{s}$, as a float.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the report has no number in that band, naming the row, the band and what the cell held instead; or when *band_hz* is not one of these bands. |

### ThirdOctaveAbsorptionSpectrum.bands()

```python
ThirdOctaveAbsorptionSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### ThirdOctaveAbsorptionSpectrum.basis_of()

```python
ThirdOctaveAbsorptionSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### ThirdOctaveAbsorptionSpectrum.from_printed()

*classmethod*

```python
ThirdOctaveAbsorptionSpectrum.from_printed(**cells: Any) -> Self
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

### ThirdOctaveAbsorptionSpectrum.is_approximate()

```python
ThirdOctaveAbsorptionSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### ThirdOctaveAbsorptionSpectrum.is_derived()

```python
ThirdOctaveAbsorptionSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### ThirdOctaveAbsorptionSpectrum.practical()

```python
ThirdOctaveAbsorptionSpectrum.practical() -> PracticalAbsorptionSpectrum
```

The row's practical coefficients, octave by octave (ISO 11654 4.1).

Each octave from 125 Hz to 4 kHz whose three one-third octaves the
row prints is the mean of the three, worked out to the second decimal
and rounded in steps of 0,05, capped at 1,00, and marked in
[`derived`](/phonometry/reference/api/io/io/#cataloguerow) with the bands it comes
from; when those bands do not share one
[`basis`](/phonometry/reference/api/io/io/#cataloguerow), the text names the basis
of each. An octave with a one-third octave the row does not print
as a number stays empty, and its
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) says it does not
follow from the cells the row has: nothing is borrowed from a
neighbouring band. An octave with a negative one-third-octave
coefficient stays empty too, with the band and the value in its
[`not_derivable`](/phonometry/reference/api/io/io/#cataloguerow): a negative value
is neither read as 0 nor left out of the mean, so
[`PracticalAbsorptionSpectrum.rating`](/phonometry/reference/api/materials/datasheets/#practicalabsorptionspectrumrating) of the result refuses a
rating band this empties, as `rating` refuses the band itself.

The name, the source, the provenance and what the report prints
about the specimen (the mounting, the thickness, the depth of
construction and the printed rating, with every hedge on them) pass
to the practical row unchanged.

**Returns:** A new [`PracticalAbsorptionSpectrum`](/phonometry/reference/api/materials/datasheets/#practicalabsorptionspectrum).

### ThirdOctaveAbsorptionSpectrum.printed()

```python
ThirdOctaveAbsorptionSpectrum.printed(
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

### ThirdOctaveAbsorptionSpectrum.printed_fields()

```python
ThirdOctaveAbsorptionSpectrum.printed_fields() -> dict[str, Any]
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

### ThirdOctaveAbsorptionSpectrum.rating()

```python
ThirdOctaveAbsorptionSpectrum.rating() -> AbsorptionRatingResult
```

The weighted sound absorption coefficient of the row's bands.

[`weighted_absorption_from_third_octave`](/phonometry/reference/api/materials/rating/#weighted_absorption_from_third_octave) on
the fifteen one-third octaves from 200 Hz to 5 kHz: the practical
coefficients of the five rating octaves (ISO 11654 Clause 4.1), then
the reference curve shifted over them (Clause 4.2). The result keeps
the fifteen values it was formed from. The rating the report prints
is not consulted: [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) notes when it
differs from this one.

**Returns:** The [`AbsorptionRatingResult`](/phonometry/reference/api/materials/rating/#absorptionratingresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a band from 200 Hz to 5 kHz the row does not print, naming the row, the band and what the report had there, or for a negative coefficient among them, naming the row, the band and the value. |

### ThirdOctaveAbsorptionSpectrum.spectrum()

```python
ThirdOctaveAbsorptionSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### ThirdOctaveAbsorptionSpectrum.values_at()

```python
ThirdOctaveAbsorptionSpectrum.values_at(
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

### ThirdOctaveAbsorptionSpectrum.why_missing()

```python
ThirdOctaveAbsorptionSpectrum.why_missing(field_name: str) -> str
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

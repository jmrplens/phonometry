---
title: "noise_control.duct_walls"
description: "What a duct wall does to sound, out of it and into it."
sidebar:
  label: "duct_walls"
---

What a duct wall does to sound, out of it and into it.

A duct is not a pipe with a number on it. The sheet it is rolled from is a
partition like any other, and two different things happen across it: the sound
travelling inside the duct leaks out through the wall into the ceiling void, and
the sound already in that void leaks in and is carried away down the duct. The
chapter calls the first breakout and the second break-in, writes them TL_out and
TL_in, and tabulates them apart, because they are not the same number and the
duct is not symmetric about its own wall.

Why they are not one column
---------------------------
Breakout is a wall radiating into a room from a duct that is behaving as a
waveguide; break-in is a wall driven by a diffuse field and feeding a waveguide.
They are separate measurements on separate specimens, and the chapter's own
tables show it: the round ducts it measured for breakout are 200, 350, 560 and
810 mm at 4.6 m, and the ones it measured for break-in are 203, 356, 559 and
813 mm at 4.57 m, with spiral blocks that share not one diameter and not one
length, 300, 610 and 915 mm at 3.6, 7.3 and 3 m against 203, 356, 660 and
813 mm all at 3.05 m. There is no single construction to hang the two numbers
on, so this catalogue holds one row per printed row and each row says, in
[`DuctWallSpectrum.direction`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum), which of the two it is. The rectangular and
flat oval tables do print the same seven sizes, row for row and each at the
same gauge as its twin, and they are still two rows each, because the page
nowhere says the specimen was the same one and a merged row would be this
library making that claim on the chapter's behalf.

What tells one row from another
-------------------------------
The cross section, the length and the gauge of the sheet. A rectangular or flat
oval duct prints two sides, held in [`DuctWallSpectrum.first_side_mm`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum) and
[`DuctWallSpectrum.second_side_mm`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum) in the order the page prints them, which
is not the same order in the two kinds of table; a round or circular one prints
[`DuctWallSpectrum.diameter_mm`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum), and the two tables that print a length per
row put it in [`DuctWallSpectrum.duct_length_m`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum). The gauge is a US
sheet-metal gauge number, and the chapter prints a thickness for one of the six
gauges these tables use, in passing and five folios past the last of them:
"16 ga (1.6 mm thickness)" in the running text on folio 49.37, against tables
that end on folio 49.32, with nothing anywhere for the
18, 20, 22, 24 and 26 the same tables print. So
[`DuctWallSpectrum.sheet_metal_gauge`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum) holds the characters the page prints
and nothing is converted from them.

What a cell can be instead of a number
--------------------------------------
Two things, and a third that is a number with a mark beside it. A cell written
`>45` is a lower bound, because the background sound swamped what the duct
wall was radiating; it is held as a range whose printed end is the number the
page gives and whose other end is left empty, because a transmission loss has
no ceiling and a number put there to stand for one would be read as a
measurement. It is flagged `bounded_below`, so a caller who asks for the band
is refused rather than handed the bound. A cell printed as a rule has no legend
anywhere in the chapter, so it is held as `unquantified` with the glyph the
page prints and no reading of it is supplied.

A cell in parentheses is the third, and it is not a hedge at all: the number is
a measurement and it is held exactly as printed. What the parentheses add is
what the note under Table 32 says they add, "measurements in which background
sound produced greater uncertainty than usual", and no hedge of this library
means that. It is not `approximate`, which is a number an author rounded on
purpose and which the published table reads back as a printed tilde, so the
mark is recorded in the row's note instead and the value is left alone.

Where the rows live
-------------------
In `noise_control/data/ashrae-2019-tables-29-to-34.json`, read at import
through the package-data reader in `phonometry._internal`, the same as every
other catalogue here.

What it is not
--------------
It is not a specification. Only two of the six tables say in their titles how
they were obtained, "Experimentally Measured", and they are the two that carry
the bounds and the parenthesised values the background sound left; the other
four say nothing at all about measurement or calculation and carry no source
line either. The credit for all six is in the running text and travels with
each row in `attributed_to`. Machine-room walls are not here: the chapter's
Table 40 is an ordinary partition, the same quantity
[`phonometry.building.PUBLISHED_TRANSMISSION_LOSS`](/phonometry/reference/api/building/catalogue/#published_transmission_loss) holds from Bies, and it
is published from there.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## DUCT_WALL_BANDS_HZ

*Constant* (`tuple`).

```python
DUCT_WALL_BANDS_HZ = (63, 125, 250, 500, 1000, 2000, 4000, 8000)
```

## duct_wall_named

```python
duct_wall_named(name: str) -> tuple[DuctWallSpectrum, ...]
```

Every duct wall whose printed label contains *name*, without case.

A tuple and not one row, and a long one: the label a duct table prints is
its size, and the same size is printed by the breakout table and by the
break-in table, so the plain answer to `"305 × 305 mm"` is two rows that
are two different quantities. Read [`DuctWallSpectrum.direction`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum) to
tell them apart, and [`DuctWallSpectrum.sheet_metal_gauge`](/phonometry/reference/api/noise_control/duct-walls/#ductwallspectrum) to tell
apart two rows of one diameter.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | Part of a row label, as its page prints it, with the unit its column heading carries: `"610"`, `"305 × 1220"`, `"152 mm"`. |

**Returns:** The matching rows, in catalogue order. Empty when none match.

## DuctWallSpectrum

```python
DuctWallSpectrum(
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
    transmission_loss_63_db: float | None = None,
    transmission_loss_125_db: float | None = None,
    transmission_loss_250_db: float | None = None,
    transmission_loss_500_db: float | None = None,
    transmission_loss_1000_db: float | None = None,
    transmission_loss_2000_db: float | None = None,
    transmission_loss_4000_db: float | None = None,
    transmission_loss_8000_db: float | None = None,
    direction: str = '',
    shape: str = '',
    printed_table: str = '',
    sheet_metal_gauge: str = '',
    first_side_mm: float | None = None,
    second_side_mm: float | None = None,
    diameter_mm: float | None = None,
    duct_length_m: float | None = None,
)
```

One duct wall of one printed table, in one of the two directions.

The hedges a cell can carry instead of a number are the ones every
catalogue row has. What this class adds is that the quantity is only half
named by the column: a transmission loss here is a breakout or a break-in
transmission loss, never both, and `direction` is what says which.

**Attributes**

| Name | Description |
| :--- | :--- |
| `transmission_loss_63_db` | The transmission loss in the 63 Hz octave band, in decibels, in the direction `direction` names. |
| `transmission_loss_125_db` | The same in the 125 Hz band. |
| `transmission_loss_250_db` | The same in the 250 Hz band. |
| `transmission_loss_500_db` | The same in the 500 Hz band. |
| `transmission_loss_1000_db` | The same in the 1 kHz band. |
| `transmission_loss_2000_db` | The same in the 2 kHz band. |
| `transmission_loss_4000_db` | The same in the 4 kHz band. |
| `transmission_loss_8000_db` | The same in the 8 kHz band, which only the two rectangular tables print a column for. |
| `direction` | `"breakout"` for the sound that leaves the duct through its wall, `"break-in"` for the sound that enters it through the same wall. Two rows of the same size and gauge in the two directions are two measurements and not two columns of one. |
| `shape` | What the table's own title calls the duct: `"rectangular"`, `"round"`, `"flat oval"` or `"circular"`. The chapter uses "round" for its breakout table and "circular" for its break-in one although the geometry is the same, and each row keeps the word its own page prints. |
| `printed_table` | Which table of the chapter this row is printed in, `"Table 29"` to `"Table 34"`. |
| `sheet_metal_gauge` | The gauge of the sheet, exactly as printed, including the asterisk that marks an internally lined duct. It is a US sheet-metal gauge number, and the chapter converts one of the six these tables use, "16 ga (1.6 mm thickness)" in the running text of folio 49.37, and none of the other five, so no thickness is offered here. |
| `first_side_mm` | The first of the two sides a rectangular or flat oval duct prints, in millimetres. The page does not say which side is the width, and it does not print them in one order: the rectangular tables put the smaller first and the flat oval tables the larger. |
| `second_side_mm` | The second of those two sides, in millimetres. |
| `diameter_mm` | The diameter of a round or circular duct, in millimetres. In one block of one table a printed diameter covers three consecutive rows, and the two whose cell the page leaves blank carry it down from the row that prints it: `carried["diameter_mm"]` names that row, and `is_derived("diameter_mm")` answers `False`, because the number is the page's and this library computed nothing. |
| `duct_length_m` | The length of the duct that was measured, in metres, for the two tables that print one per row. The four tables that do not say in a note that their data are for a length of 6.1 m, which is how the page writes it. |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `basis` | What the source says a value is: a field name, or `"row"` for the whole row, to one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases). Hopkins marks most of his Poisson ratios "Estimate", and those cells hold `"estimated"`; a datasheet that declares a class under a product standard would hold `"declared"`. A field with no entry takes the row's, and a row with neither is one whose source does not say, which is a different answer from any of the five. `basis_of` reads it. Independent of `derived`: this is what the source claims for a cell, that is what this library computed. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and on every row the library builds it follows again from the row's own cells: `from_printed` writes it, and nothing else in the library does. One a caller passes to the literal constructor is the caller's word, which the row keeps and `printed_fields` leaves out with its value, as it leaves out every derived one. When the printed cells a value rests on do not all have one `basis`, the text names the basis of each, so a modulus worked out from a plate speed and a Poisson ratio Hopkins marks as an estimate says it rests on that estimate. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page gives by reference to another of its rows (`carried` does). |
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

### DuctWallSpectrum.bands()

```python
DuctWallSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### DuctWallSpectrum.basis_of()

```python
DuctWallSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### DuctWallSpectrum.from_printed()

*classmethod*

```python
DuctWallSpectrum.from_printed(**cells: Any) -> Self
```

A row built from the cells its page prints, completed and marked.

The one path that works anything out. The cells are what the page
prints, under the field names of the class and with the hedges each
cell carries, as a data file writes them. A figure written under a
unit the class takes as an alias of its own (an
[`AbsorptionAreaSpectrum`](/phonometry/reference/api/materials/measured/#absorptionareaspectrum) takes
`absorption_area_125_ft2` for `absorption_area_125_m2`) is
converted on its digits with an exact factor and rounded once, and
`converted` records the figure and its unit. The row is then
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
| CatalogueError | for a cell the contract refuses; for a `derived` among the cells, which is this method's to write; for a figure under a unit alias that is not a finite number, or that names a cell given under its own name or under another alias as well; and for printed cells a value that follows from them cannot be worked out of, naming the value and the cells. |
| TypeError | for a name that is neither a field of the class nor a unit alias of one. |

### DuctWallSpectrum.is_approximate()

```python
DuctWallSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### DuctWallSpectrum.is_break_in

*property*

Whether this row is the sound entering the duct through its wall.

### DuctWallSpectrum.is_breakout

*property*

Whether this row is the sound leaving the duct through its wall.

### DuctWallSpectrum.is_derived()

```python
DuctWallSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### DuctWallSpectrum.printed()

```python
DuctWallSpectrum.printed(
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

### DuctWallSpectrum.printed_fields()

```python
DuctWallSpectrum.printed_fields() -> dict[str, Any]
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

### DuctWallSpectrum.spectrum()

```python
DuctWallSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### DuctWallSpectrum.transmission_loss_db()

```python
DuctWallSpectrum.transmission_loss_db(band_hz: int) -> float
```

The loss in one band, or a refusal that says what the page had.

Which of the two transmission losses it is follows from
`direction`, and the two are never mixed in one row.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | An octave-band centre frequency between 63 Hz and 8 kHz; [`bands`](/phonometry/reference/api/io/io/#bandedrowbands) says which ones this row fills. |

**Returns:** The printed transmission loss, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the page has no number in that band, naming the row, the band and what the cell held instead, which for these tables is a lower bound, a rule the chapter never explains, or a column the table does not print at all; or when *band_hz* is not a band these tables print. |

### DuctWallSpectrum.values_at()

```python
DuctWallSpectrum.values_at(frequencies_hz: ArrayLike) -> NDArray[np.float64]
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

### DuctWallSpectrum.why_missing()

```python
DuctWallSpectrum.why_missing(field_name: str) -> str
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

## PUBLISHED_DUCT_TRANSMISSION_LOSS

*Constant* (`mapping`).

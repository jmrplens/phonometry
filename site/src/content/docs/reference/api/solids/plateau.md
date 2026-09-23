---
title: "solids.plateau"
description: "The three numbers a panel needs before its transmission loss can be sketched."
sidebar:
  label: "plateau"
---

The three numbers a panel needs before its transmission loss can be sketched.

A single panel does not attenuate sound the way the mass law says it does. The
mass law is a straight line rising six decibels an octave, and a real panel
leaves it twice: once at the bottom, where the panel is stiff and resonant
rather than limp, and once near the coincidence frequency, where a bending
wave in the panel and a sound wave in the air travel at the same speed along
the surface and the panel stops resisting at all. Between those two departures
the curve flattens into a plateau.

The plateau method is the cheap way to draw that shape. Rather than solving
the plate model, it places the plateau from three numbers that depend only on
what the panel is made of: how much mass a millimetre of it brings, how high
the plateau sits, and how wide it is in frequency. Norton & Karczub draw the
mass law first, then "the coincidence region is approximated by a horizontal
line whose height is obtained from Table 3.1"; the plateau starts where that
line meets the mass law, at a frequency A, ends at B, which the frequency
ratio places relative to A, and above B the curve rises at 10 dB per octave.
This module holds those three numbers, for the eight materials the table
lists, and [`phonometry.building.plateau_transmission_loss`](/phonometry/reference/api/building/panel-transmission/#plateau_transmission_loss) draws the
curve from them: its `building.PLATEAU_MATERIALS` is built from the rows
here, so the table is typed once.

Why the first column is not a density
-------------------------------------
[`PlateauMaterial.surface_density_per_mm_kg_m2`](/phonometry/reference/api/solids/plateau/#plateaumaterial) is kilograms per square
metre per millimetre of thickness, which is the material's density divided by
a thousand. Aluminium's 2.66 is 2660 kg/m3. It is held in the unit the page
prints rather than converted to a density, because the method is applied with
it in that form: multiply by the thickness in millimetres and the surface
density of the panel falls out. Converting it would make a caller divide by a
thousand again at the point of use, and a catalogue that stores a quantity in
a unit nobody uses it in has made the reader's work harder to look tidier.

What this is not
----------------
It is not a transmission loss spectrum. One of the three numbers is a
transmission loss, [`PlateauMaterial.coincidence_height_db`](/phonometry/reference/api/solids/plateau/#plateaumaterial), the level of
the plateau in decibels, and it holds only over the plateau and only as the
method's approximation to it. The measured and tabulated insulation of real
constructions lives in
[`PUBLISHED_TRANSMISSION_LOSS`](/phonometry/reference/api/building/catalogue/#published_transmission_loss), and the duct walls
in [`PUBLISHED_DUCT_TRANSMISSION_LOSS`](/phonometry/reference/api/noise_control/duct-walls/#published_duct_transmission_loss).

Where the rows live
-------------------
In `solids/data/norton-karczub-2003-table-3-1.json`, read at import through
the package-data reader in `phonometry._internal`, the same as every other
catalogue here.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## plateau_material_named

```python
plateau_material_named(name: str) -> tuple[PlateauMaterial, ...]
```

Every row whose printed name contains *name*, case insensitively.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | Part of a material name, as the page prints it. |

**Returns:** The matching rows, in the order the tables list them. Empty when nothing matches, which is not an error: a caller asking whether a material is tabulated gets an empty answer rather than an exception.

## PlateauMaterial

```python
PlateauMaterial(
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
    surface_density_per_mm_kg_m2: float | None = None,
    coincidence_height_db: float | None = None,
    plateau_frequency_ratio: float | None = None,
)
```

One material's plateau-method constants, as a page printed them.

**Attributes**

| Name | Description |
| :--- | :--- |
| `surface_density_per_mm_kg_m2` | The mass a square metre of this material brings per millimetre of thickness, in kg/m2 per mm. It is the density divided by a thousand and is held as the page prints it; see the module docstring for why. |
| `coincidence_height_db` | The height of the plateau, in decibels: the transmission loss the method gives the panel over the coincidence region, drawn as a horizontal line. It depends on the material and not on the thickness, which moves the plateau along the frequency axis and leaves its level where it is. |
| `plateau_frequency_ratio` | The ratio of the two frequencies that bound the plateau, which the page writes B/A: A where the plateau meets the mass law, B where the curve starts to rise again. Dimensionless. |
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

### PlateauMaterial.basis_of()

```python
PlateauMaterial.basis_of(field_name: str) -> str
```

What the source says this field is: measured, declared, estimated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say. Otherwise one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

### PlateauMaterial.is_approximate()

```python
PlateauMaterial.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### PlateauMaterial.is_derived()

```python
PlateauMaterial.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### PlateauMaterial.printed()

```python
PlateauMaterial.printed(
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

### PlateauMaterial.why_missing()

```python
PlateauMaterial.why_missing(field_name: str) -> str
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

## PUBLISHED_PLATEAU_DATA

*Constant* (`mapping`).

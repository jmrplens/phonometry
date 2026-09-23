---
title: "materials.absorbers.carpets"
description: "Carpets, rated by their noise reduction coefficient and described by their pile."
sidebar:
  label: "carpets"
---

Carpets, rated by their noise reduction coefficient and described by their pile.

A carpet is the one absorber most rooms already have, and what it absorbs
depends less on the fibre than on how much pile there is and what it is laid
on: the chapter's own text says the type of fibre, nylon or wool, has no
significant effect on the absorption. Two tables of Harris say so side by side: carpets on bare concrete and
carpets on a hair pad, with the pile's weight, height, surface and fibre
beside a single number, the noise reduction coefficient: 0.25 to 0.55 on
concrete, 0.40 to 0.70 on the pad.

What the number is
------------------
The noise reduction coefficient, [`Carpet.noise_reduction_coefficient`](/phonometry/reference/api/materials/carpets/#carpet), is
the arithmetic mean of the sound absorption coefficients at 250, 500, 1000 and
2000 Hz rounded to the nearest 0.05. It is one number for four bands, so no
band can be recovered from it, and a carpet rated 0.50 may absorb very little
at 125 Hz. The measured absorption of materials band by band is in
[`PUBLISHED_ABSORPTION`](/phonometry/reference/api/materials/measured/#published_absorption).

What the page got wrong
-----------------------
The pile weight is printed twice, in kg/m2 and in oz/yd2, and five of the
eleven pairs of Table 30.2 are not each other. Three follow from the imperial
half at 0.035 kg/m2 per oz/yd2 instead of the 0.033906 of the definition, one
follows at neither, and one has lost a digit of its imperial half to a decimal
comma. They are registered in `docs/ERRATA.md`; the four whose kilograms are
in doubt serve no pile weight and say why, and the fifth serves its kilograms,
which Table 30.3 confirms.

Where the rows live
-------------------
In `materials/absorbers/data/harris-1995-table-30-2.json` and
`-30-3.json`, read at import through the package-data reader in
`phonometry._internal`, the same as every other catalogue here.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## Carpet

```python
Carpet(
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
    pile_weight_kg_m2: float | None = None,
    pile_height_mm: float | None = None,
    pile_surface: str = '',
    fibre: str = '',
    mounting: str = '',
    noise_reduction_coefficient: float | None = None,
)
```

One carpet as a page printed it: its pile, what it is laid on, and its NRC.

The [`name`](/phonometry/reference/api/io/io/#cataloguerow) is the
construction the page prints, woven, knitted or knotted, and the
[`variant`](/phonometry/reference/api/io/io/#cataloguerow) is the pile
surface and the fibre, which is what tells two rows of one construction
apart.

**Attributes**

| Name | Description |
| :--- | :--- |
| `pile_weight_kg_m2` | The weight of the pile, in kg/m2, as the page prints its SI half. |
| `pile_height_mm` | The height of the pile, in millimetres. |
| `pile_surface` | Whether the pile is cut or looped, in the page's words. |
| `fibre` | The fibre, in the page's words. |
| `mounting` | What the carpet is laid on, which is what separates the two tables and raises the rating. |
| `noise_reduction_coefficient` | The NRC, dimensionless. |
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

### Carpet.basis_of()

```python
Carpet.basis_of(field_name: str) -> str
```

What the source says this field is: measured, declared, estimated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say. Otherwise one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

### Carpet.is_approximate()

```python
Carpet.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### Carpet.is_derived()

```python
Carpet.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### Carpet.printed()

```python
Carpet.printed(field_name: str, *, wanted_by: str = 'the caller') -> float
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

### Carpet.why_missing()

```python
Carpet.why_missing(field_name: str) -> str
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

## carpets_named

```python
carpets_named(name: str) -> tuple[Carpet, ...]
```

Every published carpet whose construction, surface or fibre contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | Part of what the page prints, in Spanish, matched without regard to case: `"nylon"` answers with every nylon carpet of both tables, and `"de nudo"` with every knotted one. |

**Returns:** The matching rows, in the order the tables list them. Empty when nothing matches, which is not an error.

## PUBLISHED_CARPETS

*Constant* (`mapping`).

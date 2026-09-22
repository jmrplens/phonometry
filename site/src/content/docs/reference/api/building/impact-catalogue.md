---
title: "building.impact_catalogue"
description: "Impact insulation as a handbook prints it, one row per floor-ceiling."
sidebar:
  label: "impact_catalogue"
---

Impact insulation as a handbook prints it, one row per floor-ceiling.

The impact insulation class is a single number for a whole assembly. It is not
a property of the slab, and it is not a property of the covering: it is what a
tapping machine did on one floor built one way, with one ceiling under it, and
it moves by fifty-five points between a bare concrete slab, which these pages
rate 25, and the same slab under a wool carpet, which they rate 80. The models
of `phonometry.building.prediction` compute the improvement a covering
gives; this module holds what was measured on floors that exist, so a
prediction has something published to sit beside.

Two quantities, and never both on one row
-----------------------------------------
Tables 32.1 to 32.7 print [`ImpactInsulation.impact_insulation_class`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation),
the IIC of a whole floor-ceiling assembly. Table 32.8 prints
[`ImpactInsulation.impact_insulation_class_improvement`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation), the delta-IIC a
surface treatment adds to a hard massive floor. They are different quantities
and no row of this catalogue carries both: one is a rating, the other is a
difference between two ratings, and a caller who added the second to the first
would be adding a difference to an absolute with nothing in the arithmetic to
say so. Both are dimensionless.

There is no spectrum here
-------------------------
The IIC is a single-number rating and these pages print no frequency band at
all: no impact sound pressure level per octave, none per third octave, and no
reference curve. A caller after a band-by-band impact level will not find one
in this catalogue, and nothing here can be turned into one.

How a row is identified
-----------------------
The page numbers its constructions 1 to 38 straight through the seven tables,
with a letter where a construction is printed as two lettered rows, and that
printed number is the key of the row: `"harris-1995-tables-32-1-to-32-8/34A"`
is the row the page calls 34A. It has to be, because about a dozen descriptions
are printed in full and refer to another row rather than repeating the
structural floor: "Igual que 1 salvo que...", "Mismo suelo estructural que el
18". The printed text is kept whole in `name`, the row it
points at is in [`ImpactInsulation.refers_to_row`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation), and resolving it is one
lookup: `PUBLISHED_IMPACT_INSULATION[f"{row.table}/{row.refers_to_row}"]`.
Table 32.8 numbers nothing, so its six rows are keyed by a slug of the printed
treatment. A lettered pair is two rows and not one row in two conditions, which
is why no row of this catalogue fills
`variant`: 34A and 34B are
each printed with a description and a rating of their own.

Where the rows live
-------------------
In `building/data/harris-1995-tables-32-1-to-32-8.json`, read at import
through the package-data reader in `phonometry._internal`, the same as every
other catalogue here.

What the page got wrong
-----------------------
These tables print every dimension twice, in SI and in US customary units, and
nineteen of the three hundred and twenty pairs are not each other: row 9 gives
16 in as 30,8 cm where the other eighteen 16 in of these tables are 40,6 cm,
row 31 gives 2 in as 10,1 cm, row 38 gives 44 oz/yd2 as 1,99 kg/m2 where 28 and
30 give it as 1,5. They are registered as one entry in `docs/ERRATA.md` and
nothing here quietly repairs them: the printed description is kept whole and
the seventeen rows that carry one mark the cell in
`misprinted`. One of the
nineteen reaches a quantity rather than prose, which is why
[`ImpactInsulation.layer_density_kg_m3`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation) is empty on row 35A.

What it is not
--------------
It is not a specification and it is not a prediction. The chapter says the
tables hold "datos de mediciones" collected from a 1967 report prepared for the
Federal Housing Administration by the National Bureau of Standards, and Table
32.8 credits a 1963 paper by Zeller; each row carries the one that covers its
table in `attributed_to`,
because a row read on its own would otherwise answer the same source for both.
No laboratory, no test standard and no uncertainty is named for any row. Table
32.8 carries a footnote of its own worth reading before its numbers are used
anywhere: over wood-joist floors the improvement may be substantially smaller
than the one printed.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## impact_insulation_named

```python
impact_insulation_named(name: str) -> tuple[ImpactInsulation, ...]
```

Every published row whose printed description contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | A fragment of the printed description, matched without case. The descriptions are in the language the page is set in, and they are the only thing matched: there is no short name for a construction the page describes in a paragraph. |

**Returns:** The matching rows, in catalogue order. Empty when none match. A tuple and not one row, because a description is not a name and several constructions share most of their words.

## ImpactInsulation

```python
ImpactInsulation(
    *,
    name: str,
    source: str,
    table: str = '',
    variant: str = '',
    approximate: frozenset[str] = frozenset(),
    derived: Mapping[str, str] = ...,
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
    impact_insulation_class: float | None = None,
    impact_insulation_class_improvement: float | None = None,
    refers_to_row: str = '',
    has_section_drawing: bool = False,
    layer_density_kg_m3: float | None = None,
)
```

One floor-ceiling construction or surface treatment, as printed.

The name, the citation and the hedges a cell can carry instead of a number
are the ones every catalogue row has. What this class adds is that its two
quantities are never both filled: a row is a rating or an improvement on a
rating, and which one it is says which table it came from.

**Attributes**

| Name | Description |
| :--- | :--- |
| `impact_insulation_class` | The IIC of the whole floor-ceiling assembly this row describes, dimensionless. Filled by Tables 32.1 to 32.7, and never on a row that gives an improvement. Two rows print no class at all and leave it empty, which `why_missing` says. |
| `impact_insulation_class_improvement` | The delta-IIC an elastic surface treatment adds over a hard massive structural floor, dimensionless. Filled by Table 32.8 alone. It is a difference between two ratings and not a rating, so it is not comparable with `impact_insulation_class` and is not to be added to one from another row: the page gives the improvement over the floor it was measured on, and its own footnote says that over wood joists it may be substantially smaller. |
| `refers_to_row` | The row this row's printed description refers to instead of repeating the structural floor, named by the number the table prints in its own column. Empty when the description stands on its own. The description itself is printed in full and is kept whole in `name`; this is only the thing it inherits. |
| `has_section_drawing` | Whether the "Esquema" cell of this row holds a drawing of the section. That cell prints no text of any kind, so there is nothing to transcribe and nothing else is recorded about it. The rows that only refer to another one carry no drawing. |
| `layer_density_kg_m3` | A mass density the running description buries, in kilograms per cubic metre, lifted out so it can be read without parsing prose. Three rows print one and it is the density of one layer, which is why the field says layer and not slab: on row 5 it is a semi-rigid polyurethane foam, on row 35A a compressed paper-pulp board and only on row 37A the structural concrete. Which layer is named by the row's `note`, and it is never a density of the assembly. Row 35A serves none, because the page prints that one cell twice and the two printings disagree; `why_missing` hands back both. |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read. |
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

### ImpactInsulation.is_approximate()

```python
ImpactInsulation.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### ImpactInsulation.is_derived()

```python
ImpactInsulation.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how.

### ImpactInsulation.printed()

```python
ImpactInsulation.printed(
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

### ImpactInsulation.why_missing()

```python
ImpactInsulation.why_missing(field_name: str) -> str
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

## PUBLISHED_IMPACT_INSULATION

*Constant* (`mappingproxy`).

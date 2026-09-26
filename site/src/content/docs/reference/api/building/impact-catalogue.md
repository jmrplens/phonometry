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

Three quantities, and never two on one row
------------------------------------------
Tables 32.1 to 32.7 print [`ImpactInsulation.impact_insulation_class`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation),
the IIC of a whole floor-ceiling assembly. Table 32.8 prints
[`ImpactInsulation.impact_insulation_class_improvement`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation), the delta-IIC a
surface treatment adds to a hard massive floor. They are different quantities
and no row of this catalogue carries both: one is a rating, the other is a
difference between two ratings, and a caller who added the second to the first
would be adding a difference to an absolute with nothing in the arithmetic to
say so. Both are dimensionless.

The first edition of the handbook, in its Spanish translation of 1977, prints
a third: [`ImpactInsulation.impact_sound_improvement_db`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation), the average
improvement in impact sound insulation a finish, a floating screed or a timber
floor gives over a bare concrete slab, in decibels. It predates the IIC and is
not one: it is a level difference averaged over frequency, and nothing on the
page turns it into a rating or a rating into it. Tables 19.2 to 19.4 fill it
and nothing else, and Table 19.4 adds the load each floor was measured under.

There is no spectrum here
-------------------------
The IIC is a single-number rating and these pages print no frequency band at
all: no impact sound pressure level per octave, none per third octave, and no
reference curve. Neither do Tables 19.2 to 19.4 of the 1977 edition, whose
chapter draws some of those improvements as curves against frequency in
Figures 19.6 to 19.8; the figures are not transcribed. A caller after a
band-by-band impact level will not find one in this catalogue, and nothing
here can be turned into one.

How a row is identified
-----------------------
The page numbers its constructions 1 to 38 straight through the seven tables,
with a letter where a construction is printed as two lettered rows, and that
printed number is the key of the row: `"harris-1995-tables-32-1-to-32-8/34A"`
is the row the page calls 34A. It has to be, because about a dozen descriptions
are printed in full and refer to another row rather than repeating the
structural floor: "Igual que 1 salvo que...", "Mismo suelo estructural que el
18". The printed text is kept whole in [`name`](/phonometry/reference/api/io/io/#cataloguerow), the row it
points at is in [`ImpactInsulation.refers_to_row`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation), and resolving it is one
lookup: `PUBLISHED_IMPACT_INSULATION[f"{row.table}/{row.refers_to_row}"]`.
Table 32.8 numbers nothing, so its six rows are keyed by a slug of the printed
treatment. A lettered pair is two rows and not one row in two conditions, which
is why no row of Chapter 32 fills
[`variant`](/phonometry/reference/api/io/io/#cataloguerow): 34A and 34B are
each printed with a description and a rating of their own.

The 1977 tables number nothing either, and are keyed by a slug of the printed
description in the same way. Table 19.4 prints one timber floor twice,
unloaded and loaded, with nothing but the load to tell the two apart, so its
rows carry the load in the key and in
[`variant`](/phonometry/reference/api/io/io/#cataloguerow): that pair is one
floor in two conditions, and Table 19.4 is the only table here whose rows fill
it.

Where the rows live
-------------------
In `building/data/harris-1995-tables-32-1-to-32-8.json` and one file per
table of Harris (1977), `harris-1977-table-19-2.json` to `-19-4.json`, read
at import through the package-data reader in `phonometry._internal`, the same
as every other catalogue here.

What the page got wrong
-----------------------
These tables print every dimension twice, in SI and in US customary units, and
nineteen of the three hundred and twenty-one pairs are not each other: row 9 gives
16 in as 30,8 cm where the other eighteen 16 in of these tables are 40,6 cm,
row 31 gives 2 in as 10,1 cm, row 38 gives 44 oz/yd2 as 1,99 kg/m2 where 28 and
30 give it as 1,5. They are registered as one entry in `docs/ERRATA.md` and
nothing here quietly repairs them: the printed description is kept whole and
the seventeen rows that carry one mark the cell in
[`misprinted`](/phonometry/reference/api/io/io/#cataloguerow). One of the
nineteen reaches a quantity rather than prose, which is why
[`ImpactInsulation.layer_density_kg_m3`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation) is empty on row 35A.

What it is not
--------------
It is not a specification and it is not a prediction. The chapter says the
tables hold "datos de mediciones" collected from a 1967 report prepared for the
Federal Housing Administration by the National Bureau of Standards, and Table
32.8 credits a 1963 paper by Zeller; each row of Chapter 32 carries the one
that covers its table in
[`attributed_to`](/phonometry/reference/api/io/io/#cataloguerow), because a
row read on its own would otherwise answer the same source for both. The 1977
tables credit no source and their rows carry none. No laboratory, no test
standard and no uncertainty is named for any row. Table
32.8 carries a footnote of its own worth reading before its numbers are used
anywhere: over wood-joist floors the improvement may be substantially smaller
than the one printed.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## impact_insulation_named

```python
impact_insulation_named(
    name: str,
    *,
    catalogue: Mapping[str, ImpactInsulation] | None = None,
) -> tuple[ImpactInsulation, ...]
```

Every row whose printed description contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | A fragment of the printed description, matched without case. The descriptions are in the language the page is set in, and they are the only thing matched: there is no short name for a construction the page describes in a paragraph. |
| `catalogue` | The rows to search in place of [`PUBLISHED_IMPACT_INSULATION`](/phonometry/reference/api/building/impact-catalogue/#published_impact_insulation): a catalogue of your own that [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) returns, `PUBLISHED_IMPACT_INSULATION \| mine` to search both at once, or any mapping of key to row (Default: `None`, which searches [`PUBLISHED_IMPACT_INSULATION`](/phonometry/reference/api/building/impact-catalogue/#published_impact_insulation)). |

**Returns:** The matching rows, in catalogue order. Empty when none match. A tuple and not one row, because a description is not a name and several constructions share most of their words.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a *catalogue* that is not a mapping, or that holds a row that is not an [`ImpactInsulation`](/phonometry/reference/api/building/impact-catalogue/#impactinsulation), naming its key. |

## ImpactInsulation

```python
ImpactInsulation(
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
    impact_insulation_class: float | None = None,
    impact_insulation_class_improvement: float | None = None,
    impact_sound_improvement_db: float | None = None,
    added_load_pa: float | None = None,
    refers_to_row: str = '',
    has_section_drawing: bool = False,
    layer_density_kg_m3: float | None = None,
)
```

One floor-ceiling construction or surface treatment, as printed.

The name, the citation and the hedges a cell can carry instead of a number
are the ones every catalogue row has. What this class adds is that its
three results are never filled together: a row is a rating (Tables 32.1 to
32.7), an improvement on a rating (Table 32.8) or an improvement in
decibels (the 1977 Tables 19.2 to 19.4), and which one it is says which
table it came from. The load a 1977 floor was measured under is a
condition of the measurement, not a result, and sits beside the
improvement it qualifies.

**Attributes**

| Name | Description |
| :--- | :--- |
| `impact_insulation_class` | The IIC of the whole floor-ceiling assembly this row describes, dimensionless. Filled by Tables 32.1 to 32.7, and never on a row that gives an improvement. Two rows print no class at all and leave it empty, which [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) says. |
| `impact_sound_improvement_db` | The average improvement in impact sound insulation a floor treatment gives over a bare concrete floor, in decibels, as Harris (1977) Tables 19.2 to 19.4 print it. It is a level difference averaged over frequency and not a rating, so it is not comparable with `impact_insulation_class` or with `impact_insulation_class_improvement`, which are dimensionless. |
| `added_load_pa` | The load a floor of Harris (1977) Table 19.4 was measured under, in pascals. The page prints it in kg/cm2, the technical atmosphere of 98 066.5 Pa, and prints 0 for an unloaded floor, which is held as zero: it is a condition of the measurement and was printed. Empty on every row of every other table, which prints no load. |
| `impact_insulation_class_improvement` | The delta-IIC an elastic surface treatment adds over a hard massive structural floor, dimensionless. Filled by Table 32.8 alone. It is a difference between two ratings and not a rating, so it is not comparable with `impact_insulation_class` and is not to be added to one from another row: the page gives the improvement over the floor it was measured on, and its own footnote says that over wood joists it may be substantially smaller. |
| `refers_to_row` | The row this row's printed description refers to instead of repeating the structural floor, named by the number the table prints in its own column. Empty when the description stands on its own. The description itself is printed in full and is kept whole in [`name`](/phonometry/reference/api/io/io/#cataloguerow); this is only the thing it inherits. |
| `has_section_drawing` | Whether the "Esquema" cell of this row holds a drawing of the section. That cell prints no text of any kind, so there is nothing to transcribe and nothing else is recorded about it. The four rows whose description is nothing but a reference to another row carry no drawing, and neither do the six rows of Table 32.8, which has no such cell; every other row has one. |
| `layer_density_kg_m3` | A mass density the running description buries, in kilograms per cubic metre, lifted out so it can be read without parsing prose. Three rows print one and it is the density of one layer, which is why the field says layer and not slab: on row 5 it is a semi-rigid polyurethane foam, on row 35A a compressed paper-pulp board and only on row 37A the structural concrete. Which layer is named by the row's [`note`](/phonometry/reference/api/io/io/#cataloguerow), and it is never a density of the assembly. Row 35A serves none, because the page prints that one cell twice and the two printings disagree; [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) hands back both. |
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

### ImpactInsulation.basis_of()

```python
ImpactInsulation.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### ImpactInsulation.from_printed()

*classmethod*

```python
ImpactInsulation.from_printed(**cells: Any) -> Self
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

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

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

### ImpactInsulation.printed_fields()

```python
ImpactInsulation.printed_fields() -> dict[str, Any]
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

### ImpactInsulation.why_missing()

```python
ImpactInsulation.why_missing(field_name: str) -> str
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

## PUBLISHED_IMPACT_INSULATION

*Constant* (`mapping`).

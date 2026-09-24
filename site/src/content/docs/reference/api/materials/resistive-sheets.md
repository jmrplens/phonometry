---
title: "materials.absorbers.resistive_sheets"
description: "Thin resistive facings, and the resistance of one square metre of them."
sidebar:
  label: "resistive_sheets"
---

Thin resistive facings, and the resistance of one square metre of them.

A porous absorber is usually covered, and what covers it is a wire mesh, a
glass cloth or a sheet of sintered metal. The cover is thin enough that it
stores no sound and absorbs almost none by itself, and thin enough that what
it does to the layer behind it is settled by one number: the pressure drop
across it divided by the face velocity through it, which the chapter these
rows come from writes `R_s = dp/v` and calls the specific, or unit-area,
flow resistance.

Not the flow resistivity, which is the other catalogue
------------------------------------------------------
[`PUBLISHED_POROUS`](/phonometry/reference/api/materials/catalogue/#published_porous) holds a flow
**resistivity**, `sigma`, in Pa s/m2: a property of a bulk material, per
metre of it, which has to be multiplied by a thickness before it means
anything. This catalogue holds a flow **resistance**, `R_s`, in Pa s/m: a
property of a facing as supplied, already integrated through whatever
thickness it has, and there is no thickness to multiply by. The two are one
letter apart in most books and a factor of the thickness apart in every
calculation, so they are held under two field names that cannot be confused:
`flow_resistivity_pa_s_m2` there and
[`specific_flow_resistance_pa_s_m`](/phonometry/reference/api/materials/resistive-sheets/#resistivesheet) here. A mesh of
24.6 Pa s/m is not a material of 24.6 Pa s/m2.

The unit has three spellings in the literature and they are all the same
thing: N s/m3, Pa s/m, and the mks rayl of an older tradition. The pages here
use the first and the third: TABLE 8.5 and TABLE 8.7 head their resistance
column `N · s/m3`, and TABLE 8.6 heads its own "Flow Resistance, mks rayls
(N · s/m3)". Pa s/m is this library's spelling of that same unit, and it is
the one in the field name.

What the pages print twice, and what they print once
----------------------------------------------------
TABLE 8.5 prints every one of its quantities twice, but only three of the four
pairs are one quantity in two systems of units: the wire count in wires per
centimetre and wires per inch, the wire diameter in micrometres and mils, the
mass in kg/m2 and lb/ft2. The fourth pair prints the flow resistance in N s/m3
and again as a multiple of `rho_0 c_0`, which is no unit at all. TABLE 8.7
prints its thickness and its mass in the two systems of units, and its flow
resistance the two ways TABLE 8.5 does. This catalogue keeps the SI
printing of each pair of units, so the numbers here are the page's own digits
rather than arithmetic on them, and that leaves the customary printing free to
check the SI one. It is how the first of the two defects these pages carry was
found: the finest wire mesh of TABLE 8.5 is printed as 0.31 kg/m2 beside
0.63 lb/ft2, when 0.31 kg/m2 is 0.063 lb/ft2 and the decimal point of the pound
cell is one place too far right, and the entry in `docs/ERRATA.md` argues it.
The row keeps the kilogramme cell, which the column above it and the weave of
the mesh both support, and its
[`note`](/phonometry/reference/api/io/io/#cataloguerow) records the pound
cell. The note and not a hedge, because the defective cell is the restatement:
this catalogue holds no customary column, so there is no cell here to refuse.

TABLE 8.6 is the one that does not print everything twice. It prints its
surface density twice, and its weave and its flow resistance once each and in
one unit. The two surface densities disagree by about eleven per cent on all
thirteen rows, one wrong factor rather than thirteen slips, and the page does
not say which of the two columns carries it: the row holds the gramme per
square metre the page prints, in [`surface_density_g_m2`](/phonometry/reference/api/materials/resistive-sheets/#resistivesheet),
and its note gives the ounce per square yard beside it, with the entry in
`docs/ERRATA.md` that argues the pair. Thirteen of the twenty-nine flow
resistances published here therefore have no second printing to check them at
all, and nothing but the second reader stands behind them.

Where the rows live
-------------------
In `absorbers/data/`, one file per printed table:
`ver-beranek-2006-table-8-5.json`, `ver-beranek-2006-table-8-6.json` and
`ver-beranek-2006-table-8-7.json`, read at import through the package-data
reader in `phonometry._internal`, the same as every other catalogue here.
One file per published table is what makes a key mean something: a row of the
glass cloth table is keyed `"ver-beranek-2006-table-8-6/glass_cloth_120"`,
and its [`source`](/phonometry/reference/api/io/io/#cataloguerow) names that
table, that PDF page and that printed folio and nothing else.

What it is not
--------------
It is not a specification. These are commercial products, the cloths and the
sintered sheets named by their manufacturers' own codes and the wire meshes by
nothing but their mesh count, and the pages give no measurement method, no
laboratory and no standard for any of the three tables. What they do give is
two conditions, and each reaches the rows it belongs to: TABLE 8.7 prints its
flow resistance for "Air, 70°F", which is in the note of all eleven sintered
sheets and matters because the resistance of a facing follows the viscosity of
the air; and footnote a of TABLE 8.6 says its surface densities are "Averaged
over a large sample.", which is in the note of all thirteen cloths. The
running text adds the warning that matters most, about the two cloth tables:
the values "represent the linear part of the flow resistance, which is
appropriate for design use only if the particle velocity is low", and above
140 dB the resistance has to be measured as a function of face velocity
instead. The eleven sintered sheets are the exception the same page makes for
them, and a conditional one: backed by a honeycomb-partitioned air space they
"remain linear up to high sound pressure levels and for high-Mach-number
grazing flow", and their table prints a nonlinearity factor where the two
cloth tables print none.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PUBLISHED_FLOW_RESISTANCE

*Constant* (`mapping`).

## resistive_sheet_named

```python
resistive_sheet_named(name: str) -> tuple[ResistiveSheet, ...]
```

Every facing a page labels *name*, matched whole and without case.

Whole and not in part, unlike the other catalogues of this library, and
the reason is what these pages use for names: a mesh count, a four-digit
cloth number, a manufacturer's product code. A search that matched part
of a name would answer `"12"` with the twelve-wire mesh, the cloth
numbered 120, the cloth numbered 126 and the four sintered sheets FM 122,
FM 125, FM 126 and FM 127, none of which has anything to do with any
other.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | The label as its page prints it: `"80"`, `"1584"`, `"FM 122"`. |

**Returns:** The matching rows, in catalogue order. Empty when none match.

## ResistiveSheet

```python
ResistiveSheet(
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
    specific_flow_resistance_pa_s_m: float | None = None,
    normalized_flow_resistance: float | None = None,
    wires_per_cm: float | None = None,
    wire_diameter_um: float | None = None,
    weave_construction: str = '',
    thickness_mm: float | None = None,
    mass_per_area_kg_m2: float | None = None,
    surface_density_g_m2: float | None = None,
    nonlinearity_factor: float | None = None,
)
```

One thin resistive facing, as its published table prints it.

The name, the citation and the hedges a cell can carry instead of a
number are the ones every catalogue row has. What varies here is which
columns a row has at all: a wire mesh is described by how many wires it
has to the centimetre and how thick they are, a glass cloth by its weave,
and a sintered sheet by its thickness and how far from linear it goes, so
no two of the three tables print the same columns and every quantity below
is optional.

**Attributes**

| Name | Description |
| :--- | :--- |
| `specific_flow_resistance_pa_s_m` | The resistance of unit area of the facing, `R_s`, in pascal seconds per metre, which is the N s/m3 the three tables print and the mks rayls TABLE 8.6 also heads its column with. Per unit **area**, so unlike the flow resistivity of [`PUBLISHED_POROUS`](/phonometry/reference/api/materials/catalogue/#published_porous) it is not multiplied by a thickness. |
| `normalized_flow_resistance` | The same resistance divided by the characteristic impedance of air, dimensionless, as two of the tables print it in a column of their own. Kept rather than recomputed because the two tables do not normalize by the same impedance: `reference_impedance_pa_s_m` recovers the one each row was divided by. |
| `wires_per_cm` | Wires per centimetre of the woven mesh, as TABLE 8.5 heads the column and prints it again as wires per inch beside it. One count and not two: the page says nothing about the two directions of the weave, where the glass cloth table prints a count for each. |
| `wire_diameter_um` | Diameter of the wire, in micrometres. |
| `weave_construction` | The weave of a glass cloth, as the page prints it and as text rather than as a number: two counts under one heading, "Construction, Ends × Picks", over a length the page never states. `"60 × 58"`. Empty on a row from a table that prints no such column. |
| `thickness_mm` | Thickness of the sintered sheet, in millimetres. It is a property of the sheet, not something the flow resistance is divided by: see the module docstring. |
| `mass_per_area_kg_m2` | Mass per unit area, `rho_s`, in kg/m2, as TABLE 8.5 and TABLE 8.7 head the column and print it. The chapter names it beside the flow resistance as the second thing that characterises a thin layer. |
| `surface_density_g_m2` | The same quantity as TABLE 8.6 prints it, under its own heading, "Surface Density", in grammes per square metre and averaged over a large sample per its footnote a. A second name for one quantity because nothing here is converted and a cell printed in g/m2 is held in g/m2; no row has both, since no table prints both. Its second printing, in oz/yd2, disagrees with it: see the module docstring and `docs/ERRATA.md`. |
| `nonlinearity_factor` | How far the sintered sheet departs from a linear resistance: its table's footnote b defines it as the ratio of the flow resistances obtained at flow velocities of 500 and 20 cm/s. A facing at 1 would be linear; these run from 1.8 to 5. |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `basis` | What the source says a value is: a field name, or `"row"` for the whole row, to one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases). Hopkins marks most of his Poisson ratios "Estimate", and those cells hold `"estimated"`; a datasheet that declares a class under a product standard would hold `"declared"`. A field with no entry takes the row's, and a row with neither is one whose source does not say, which is a different answer from any of the five. `basis_of` reads it. Independent of `derived`: this is what the source claims for a cell, that is what this library computed. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and it always follows again from the row's own cells: `from_printed` writes it, and nothing else in the library does. When the printed cells a value rests on do not all have one `basis`, the text names the basis of each, so a modulus worked out from a plate speed and a Poisson ratio Hopkins marks as an estimate says it rests on that estimate. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page gives by reference to another of its rows (`carried` does). |
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

### ResistiveSheet.basis_of()

```python
ResistiveSheet.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### ResistiveSheet.from_printed()

*classmethod*

```python
ResistiveSheet.from_printed(**cells: Any) -> Self
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
do not share one `basis`, the basis of each.

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
| CatalogueError | for a cell the contract refuses; for a `derived` among the cells, which is this method's to write; for a figure under a unit alias that is not a finite number, or that names a cell given under its own name as well. |
| TypeError | for a name that is neither a field of the class nor a unit alias of one. |

### ResistiveSheet.is_approximate()

```python
ResistiveSheet.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### ResistiveSheet.is_derived()

```python
ResistiveSheet.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### ResistiveSheet.printed()

```python
ResistiveSheet.printed(
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

### ResistiveSheet.printed_fields()

```python
ResistiveSheet.printed_fields() -> dict[str, Any]
```

The cells the page prints, as `from_printed` takes them.

Every field that holds something, the name, the citation, the table
and every hedge included, except the values this library derived
and `derived` itself. A value converted from the page's unit
and one the page gives by reference to another of its rows are the
page's, so they stay, with `converted` and `carried`
beside them. `type(row).from_printed(**row.printed_fields())` is
the row again, and changing a cell before building it again is how a
row is edited without carrying a derived value that no longer
follows from it.

**Returns:** A new dictionary of constructor keywords. The values are the ones the row holds, frozen as the row holds them.

### ResistiveSheet.reference_impedance_pa_s_m()

```python
ResistiveSheet.reference_impedance_pa_s_m() -> float
```

The impedance this row's own two resistance columns were divided by.

Two of the three tables print the flow resistance twice, once in
N s/m3 and once as a multiple of `rho_0 c_0`, and neither says what
they took `rho_0 c_0` to be. Dividing one column by the other gives
it back, and it is worth asking for: the five wire mesh rows give 407
to 421 Pa s/m, and the sintered metal rows give 400 except for the
one block whose columns are 350 and 0.88, which gives 397.7. The two
normalized columns are not on the same scale, and a caller comparing
them without noticing would be out by two to five per cent, depending
on which wire mesh row it is.

It is not a property of the facing. It is a property of the page.

**Returns:** The characteristic impedance implied by the row, in Pa s/m.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the row has only one of the two columns, which is every row of the glass cloth table, naming what the page had instead. |

### ResistiveSheet.why_missing()

```python
ResistiveSheet.why_missing(field_name: str) -> str
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

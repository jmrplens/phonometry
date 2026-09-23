---
title: "solids.catalogue"
description: "Solid materials as one published table prints them."
sidebar:
  label: "catalogue"
---

Solid materials as one published table prints them.

A caller who needs a Young's modulus for plasterboard has two bad options and
one good one. They can type a number they half remember, or they can open a
book and copy a row by hand into their script, which is the same thing with
extra steps. The good one is to read the row from a catalogue that says which
page it came from, and that is what this module is.

What it is careful about
------------------------
A materials table is not a list of measurements. Hopkins Table A2 marks most
of its Poisson ratios and internal loss factors with a footnote that reads,
in full, "Estimate", and it prints some of its densities as a range rather
than a number, some of its loss factors as an upper bound, and one of its wave
speeds with a note that the material is orthotropic and the figure quoted is
an effective value. A catalogue that flattened all of that into floats would
be claiming twenty-five measured Poisson ratios where the page offers four.

So every row carries what the cell actually said: [`SolidMaterial.basis`](/phonometry/reference/api/solids/catalogue/#solidmaterial)
holds `"estimated"` for each field the page marks as an estimate, which
[`basis_of`](/phonometry/reference/api/io/io/#cataloguerowbasis_of) reads back,
[`SolidMaterial.ranges`](/phonometry/reference/api/solids/catalogue/#solidmaterial) carries the seven cells printed as an interval
(two densities, two speeds and three loss factors),
[`SolidMaterial.bounded_above`](/phonometry/reference/api/solids/catalogue/#solidmaterial) names the two of those loss factors the
page prints as an upper bound rather than a band, and
[`SolidMaterial.attributed_to`](/phonometry/reference/api/solids/catalogue/#solidmaterial) carries the per-cell credit for the rows
whose columns come from different authors. A field the table leaves
empty is `None` and not a guess.

Where the rows live
-------------------
In `solids/data/hopkins-2007-table-a2.json`, one record per material, read
at import through the package-data reader in `phonometry._internal`. Rows are
data: keeping them in a file means a second table is a second file rather than
a longer literal, means a changed digit is one line of a diff, and means the
citation is written once, in the file that holds the rows it belongs to. The
provenance gate reads it from there too, so the comment above the constant and
the page it names cannot drift apart.

What it is not
--------------
It is not a specification. Block densities vary by manufacturer, boards vary
by batch, and Hopkins says as much by printing ranges where a range is what is
known. Use a row to reproduce a worked example, to sanity-check a measurement,
or to get an order of magnitude; use a measurement for anything that has to be
right.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PUBLISHED_SOLIDS

*Constant* (`mapping`).

## SolidMaterial

```python
SolidMaterial(
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
    density_kg_m3: float | None = None,
    youngs_modulus_pa: float | None = None,
    shear_modulus_pa: float | None = None,
    poisson_ratio: float | None = None,
    longitudinal_speed_m_s: float | None = None,
    bar_longitudinal_speed_m_s: float | None = None,
    plate_longitudinal_speed_m_s: float | None = None,
    bulk_longitudinal_speed_m_s: float | None = None,
    transverse_speed_m_s: float | None = None,
    loss_factor: float | None = None,
    flexural_loss_factor: float | None = None,
    longitudinal_loss_factor: float | None = None,
    in_situ_loss_factor: float | None = None,
    thickness_critical_frequency_product_m_hz: float | None = None,
    borrowed: Mapping[str, str] = ...,
)
```

One row of a published materials table, with what the cell said.

Every quantity is optional, because no two of the books this catalogue
reads print the same columns: Hopkins gives a plate speed and no modulus,
Mechel a modulus and no speed, Cremer both plus a shear modulus, Arau
neither. A field is `None` when the page had nothing to put there, and
`why_missing` says what it had instead.

**The three longitudinal speeds are three fields**, and a fourth holds the
one a page prints without saying which it is. They are three different
waves and the books do not agree on what to call them. Cremer's
`c_LII` and Bies' `sqrt(E/rho)` are the bar speed; Hopkins'
quasi-longitudinal is the plate speed; and the bulk speed is neither. At
`nu = 0.3` the plate speed is 4.8 per cent above the bar speed and the
bulk speed is 16 per cent above it, which is the figure Cremer prints
under his Eq. (3.32) with the warning that it matters which one is meant.
One field holding whichever the page happened to print is the mistake this
catalogue exists to prevent, so there is no field that means "whichever
one the page happened to print". `longitudinal_speed_m_s` is not
that: it means the page printed a longitudinal speed and said nothing
about which, which is a statement about the source rather than a shrug
about the wave.

**The loss factors are four fields** for the same reason. A flexural loss
factor is measured in bending and a longitudinal one is not; an in-situ
one is not a property of the material at all, but of a panel installed in
a building, support and radiation included; and a page that prints one
without saying which it is has said something weaker than any of the
three, which is what [`loss_factor`](/phonometry/reference/api/vibration/transfer-stiffness/#loss_factor) holds.

The name, the citation, the variant and the hedges a cell can carry
instead of a number (`basis`, `ranges`, `reported`,
`unquantified`, `approximate`, `derived`, `converted`,
`carried`, `attributed_to`) are the ones every catalogue row has;
one is this catalogue's own and is described below. A cell the page
marks as an estimate holds `"estimated"` in
[`SolidMaterial.basis`](/phonometry/reference/api/solids/catalogue/#solidmaterial), and `row.basis_of(field) == "estimated"`
is the question to ask before reading it as a measurement, which is the
mistake this catalogue exists to prevent.

**Attributes**

| Name | Description |
| :--- | :--- |
| `density_kg_m3` | Density `rho`, in kg/m3. |
| `youngs_modulus_pa` | Young's modulus `E`, in pascals. |
| `shear_modulus_pa` | Shear modulus `G`, in pascals. |
| `poisson_ratio` | Poisson's ratio `nu`. |
| `longitudinal_speed_m_s` | A longitudinal speed for a page that prints one and does not say which of the three it is. Long's Table 12.1 does, with no modulus and no Poisson ratio beside it, so there is nothing on the page to settle it and nothing here that guesses. |
| `bar_longitudinal_speed_m_s` | `sqrt(E/rho)`, the quasi-longitudinal speed on a rod, in m/s. |
| `plate_longitudinal_speed_m_s` | `sqrt(E/(rho(1-nu^2)))`, the quasi-longitudinal speed on a plate, in m/s. |
| `bulk_longitudinal_speed_m_s` | the pure longitudinal speed in an unbounded solid, in m/s. |
| `transverse_speed_m_s` | `sqrt(G/rho)`, the shear wave speed, in m/s. |
| `loss_factor` | Internal loss factor for a page that prints one and does not say which wave it was measured with. Mechel, Long and Arau all do. It is a separate field from the two below rather than a guess at which of them it is. |
| `flexural_loss_factor` | Internal loss factor measured in bending. |
| `longitudinal_loss_factor` | Internal loss factor measured with longitudinal waves. |
| `in_situ_loss_factor` | Loss factor of a panel of this material as installed, which combines the internal, support and radiation losses and is therefore not a material constant. |
| `thickness_critical_frequency_product_m_hz` | The `h.f_c` column, in m Hz, a property of the material alone and the cheapest cross-check there is between books that share no other column. |
| `borrowed` | Field to the material it was taken from, for the cells a book fills from a similar material rather than leaving empty. |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `basis` | What the source says a value is: a field name, or `"row"` for the whole row, to one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases). Hopkins marks most of his Poisson ratios "Estimate", and those cells hold `"estimated"`; a datasheet that declares a class under a product standard would hold `"declared"`. A field with no entry takes the row's, and a row with neither is one whose source does not say, which is a different answer from any of the five. `basis_of` reads it. Independent of `derived`: this is what the source claims for a cell, that is what this library computed. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read, and it always follows again from the row's own cells. A value converted from the unit the page prints is not derived (`converted` holds it), and neither is one the page carries from another row (`carried` does). |
| `converted` | Field to `(figure, unit)`, the number and the unit the page prints, for a value this row holds in another unit. Ver and Beranek print their damping materials in degrees Fahrenheit and pounds per square inch, and the row holds degrees Celsius and pascals, so `("3e5", "psi")` sits beside a modulus in pascals. The figure is kept as the page writes it, so the cell can always be read back in the page's own terms. |
| `carried` | Field to where the page carries it from, for a cell the page leaves blank because the value is printed once for a block of rows: a figure on the first row of a group, or "Parecido al anterior". The value is the page's, and this says which of its rows prints it. |
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

### SolidMaterial.basis_of()

```python
SolidMaterial.basis_of(field_name: str) -> str
```

What the source says this field is: measured, declared, estimated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say. Otherwise one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

### SolidMaterial.is_approximate()

```python
SolidMaterial.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### SolidMaterial.is_derived()

```python
SolidMaterial.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or prints on another row and leaves blank on this one, answers `False`: the number is the page's, and `converted` or `carried` says so.

### SolidMaterial.printed()

```python
SolidMaterial.printed(
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

### SolidMaterial.why_missing()

```python
SolidMaterial.why_missing(field_name: str) -> str
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

## solids_named

```python
solids_named(name: str) -> tuple[SolidMaterial, ...]
```

Every published row for a material, across the books.

Comparing two books is the point of holding both, and it has to be a
deliberate act: a lookup that returned one row for "steel" would be
choosing between published values on the caller's behalf.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | The material name as a table prints it, matched without regard to case: `"Steel"`, `"steel"`. |

**Returns:** The rows whose [`SolidMaterial.name`](/phonometry/reference/api/solids/catalogue/#solidmaterial) matches, in the order the tables are read, which is empty when no page names it.

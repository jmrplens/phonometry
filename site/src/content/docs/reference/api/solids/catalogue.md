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

So every row carries what the cell actually said: [`SolidMaterial.estimated`](/phonometry/reference/api/solids/catalogue/#solidmaterial)
names the fields the page marks as estimates, [`SolidMaterial.ranges`](/phonometry/reference/api/solids/catalogue/#solidmaterial)
carries the seven cells printed as an interval (two densities, two speeds and
three loss factors), [`SolidMaterial.bounded_above`](/phonometry/reference/api/solids/catalogue/#solidmaterial) names the two of those
loss factors the page prints as an upper bound rather than a band, and
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

*Constant* (`mappingproxy`).

## SolidMaterial

```python
SolidMaterial(
    *,
    name: str,
    source: str,
    table: str = '',
    variant: str = '',
    density_kg_m3: float | None = None,
    youngs_modulus_pa: float | None = None,
    shear_modulus_pa: float | None = None,
    poisson_ratio: float | None = None,
    bar_longitudinal_speed_m_s: float | None = None,
    plate_longitudinal_speed_m_s: float | None = None,
    bulk_longitudinal_speed_m_s: float | None = None,
    transverse_speed_m_s: float | None = None,
    flexural_loss_factor: float | None = None,
    longitudinal_loss_factor: float | None = None,
    in_situ_loss_factor: float | None = None,
    thickness_critical_frequency_product_m_hz: float | None = None,
    estimated: frozenset[str] = frozenset(),
    approximate: frozenset[str] = frozenset(),
    derived: Mapping[str, str] = ...,
    borrowed: Mapping[str, str] = ...,
    ranges: Mapping[str, tuple[float, float]] = ...,
    bounded_above: frozenset[str] = frozenset(),
    unquantified: Mapping[str, str] = ...,
    attributed_to: Mapping[str, str] = ...,
    note: str = '',
)
```

One row of a published materials table, with what the cell said.

Every quantity is optional, because no two of the books this catalogue
reads print the same columns: Hopkins gives a plate speed and no modulus,
Mechel a modulus and no speed, Cremer both plus a shear modulus, Arau
neither. A field is `None` when the page had nothing to put there, and
`why_missing` says what it had instead.

**The three longitudinal speeds are three fields**, because they are three
different waves and the books do not agree on what to call them. Cremer's
`c_LII` and Bies' `sqrt(E/rho)` are the bar speed; Hopkins'
quasi-longitudinal is the plate speed; they differ by 16 per cent at
`nu = 0.3`, which Cremer says in so many words. One field holding
whichever the page happened to print is the mistake this catalogue exists
to prevent, so there is no such field.

**The loss factors are three fields** for the same reason. A flexural loss
factor is measured in bending and a longitudinal one is not; an in-situ
one is not a property of the material at all, but of a panel installed in
a building, support and radiation included.

**Attributes**

| Name | Description |
| :--- | :--- |
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"single crystal"`, `"13 C, 11 per cent bituminous content"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in [`PUBLISHED_SOLIDS`](/phonometry/reference/api/solids/catalogue/#published_solids). |
| `density_kg_m3` | Density `rho`, in kg/m3. |
| `youngs_modulus_pa` | Young's modulus `E`, in pascals. |
| `shear_modulus_pa` | Shear modulus `G`, in pascals. |
| `poisson_ratio` | Poisson's ratio `nu`. |
| `bar_longitudinal_speed_m_s` | `sqrt(E/rho)`, the quasi-longitudinal speed on a rod, in m/s. |
| `plate_longitudinal_speed_m_s` | `sqrt(E/(rho(1-nu^2)))`, the quasi-longitudinal speed on a plate, in m/s. |
| `bulk_longitudinal_speed_m_s` | the pure longitudinal speed in an unbounded solid, in m/s. |
| `transverse_speed_m_s` | `sqrt(G/rho)`, the shear wave speed, in m/s. |
| `flexural_loss_factor` | Internal loss factor measured in bending. |
| `longitudinal_loss_factor` | Internal loss factor measured with longitudinal waves. |
| `in_situ_loss_factor` | Loss factor of a panel of this material as installed, which combines the internal, support and radiation losses and is therefore not a material constant. |
| `thickness_critical_frequency_product_m_hz` | The `h.f_c` column, in m Hz, a property of the material alone and the cheapest cross-check there is between books that share no other column. |
| `estimated` | Fields the page marks as an estimate rather than a measurement. Reading one of these as a measurement is the mistake this catalogue exists to prevent. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read. |
| `borrowed` | Field to the material it was taken from, for the cells a book fills from a similar material rather than leaving empty. |
| `ranges` | `(low, high)` for each field the page prints as an interval rather than a value. |
| `bounded_above` | The subset of `ranges` the page prints as `< x` or `<= x`, where the low end is a floor and not a measurement. |
| `unquantified` | Field to what the page said in place of a number, for a cell that is neither empty nor numeric: `"varies with frequency"`. |
| `attributed_to` | Credit for a cell the book takes from someone else. Keyed by field name, or by `"row"` or `"table"` when the credit covers all of one. |
| `note` | What the page says about this row beyond its numbers. |

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

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how.

### SolidMaterial.is_estimate()

```python
SolidMaterial.is_estimate(field_name: str) -> bool
```

Whether the page marks this field as an estimate rather than a value.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page carries an estimate footnote there.

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

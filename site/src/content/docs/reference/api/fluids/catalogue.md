---
title: "fluids.catalogue"
description: "Fluid states read from a printed page."
sidebar:
  label: "catalogue"
---

Fluid states read from a printed page.

A density and a speed of sound stand behind every level this library computes,
and most of them are computed: [`air`](/phonometry/reference/api/fluids/air/),
[`ideal_gas`](/phonometry/reference/api/fluids/gas/#ideal_gas) and [`sea_water`](/phonometry/reference/api/fluids/water/#sea_water)
take the conditions that were measured and return the state that follows. A
few are not. Some books print a table of fluids the way they print a table of
solids, a density and a speed of sound at a stated temperature, and those are
read rather than derived. This is where they live.

The distinction is carried in [`model`](/phonometry/reference/api/fluids/fluids/#fluid), which
every state already uses to say what produced it. A computed state names the
closed form, the annex or the fit; a state from here names the table, with its
PDF page and its printed folio, because the table is what produced it and a
reader checking the number needs the page rather than the name of an equation
that was never used. The citation lives once, in the data file beside the
rows, the same shape the solid and porous catalogues use.

Not every named air in this library is here
-------------------------------------------
Four more sit elsewhere in the tree, each beside the model or the standard
that fixes it, and they disagree: the absorber models propagate through
343 m/s at 1,205 kg/m3, the airflow-resistance annex through 345,87 at 1,186,
EN/ISO 12354 through 340 at 1,29, and the acoustic solver defaults to 343 at
1,2. None of them is wrong. Each is the air its own document assumes, and
substituting one for another would change a number that document prints, which
is why each stays with the clause that prints it rather than being gathered
here.

Gathering them would also invert the dependency this package exists at the
bottom of: `fluids` is part of the transverse toolbox precisely so that any
domain may import it, and a catalogue here that imported `materials`,
`building` and `simulation` to reach them would make the medium depend on
three of the domains that stand on it. The comparison a reader wants is a
documentation artefact, and it is built as one: the published-catalogues page
of the site lists all of them side by side, gathered by a script that is free
to see the whole tree.

Gases are the other half, and they are not states
-------------------------------------------------
A book that prints a table of gases prints something different from a table of
fluids: not a density and a speed of sound, which a gas only has once a
temperature and a pressure are named, but the ratio of specific heats and the
molar mass, which close the ideal-gas state at any temperature and pressure.
So the gases live in a
catalogue of their own, [`PUBLISHED_GASES`](/phonometry/reference/api/fluids/catalogue/#published_gases), and reach a state through
[`Gas.ideal_state`](/phonometry/reference/api/fluids/catalogue/#gasideal_state), which is [`ideal_gas`](/phonometry/reference/api/fluids/gas/#ideal_gas) with the
citation carried along. Air appears in both, and it should: Bies prints it once
as a state at 20 degC and once as a pair of constants, and those are two
different readings of the same gas.

What it is not
--------------
It is not a table of fluid properties to look values up in. Air at 23 degC and
50 per cent relative humidity is [`air`](/phonometry/reference/api/fluids/air/), which computes
it from the conditions that were measured; sea water is
[`sea_water`](/phonometry/reference/api/fluids/water/#sea_water). Use a row here to reproduce a book's own
number.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## Gas

```python
Gas(
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
    molar_mass_kg_mol: float | None = None,
    heat_capacity_ratio: float | None = None,
)
```

One gas of a published table: the two numbers that close its state.

A table of gases does not print a density and a speed of sound, because a
gas does not have one: it has whichever the temperature and the pressure
give it. What it prints instead is the pair that fixes the whole family,
the ratio of specific heats and the molar mass, and
`ideal_state` walks from that pair to the ideal-gas state at
whichever temperature and pressure the caller asks for.
That is the difference between this catalogue and
[`PUBLISHED_FLUIDS`](/phonometry/reference/api/fluids/catalogue/#published_fluids), which holds states: a row there is one condition
a book measured, a row here is every condition its two constants close under
the ideal-gas relations.

The hedges of [`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow) apply
unchanged. A cell printed as an interval is a range and not a value, which
is what saturated steam is in the table this reads first.

**Attributes**

| Name | Description |
| :--- | :--- |
| `molar_mass_kg_mol` | Molar mass `M`, in kg/mol, as the page prints it. The gas tables print kg/mol rather than g/mol, so the number in the cell is 0,028 97 for air. |
| `heat_capacity_ratio` | Ratio of specific heats `gamma`, which is `c_p/c_v` and therefore above 1 for every gas. |
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

### Gas.basis_of()

```python
Gas.basis_of(field_name: str) -> str
```

What the source says this field is: measured, declared, estimated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say. Otherwise one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

### Gas.ideal_state()

```python
Gas.ideal_state(
    *,
    temperature_c: float,
    static_pressure_pa: float | None = None,
) -> Fluid
```

The gas at one state, through the ideal-gas closure.

**Parameters**

| Name | Description |
| :--- | :--- |
| `temperature_c` | Temperature `t`, in degrees Celsius. |
| `static_pressure_pa` | Static pressure `p`, in pascals. Omitted means one standard atmosphere, and [`ideal_gas`](/phonometry/reference/api/fluids/gas/#ideal_gas) says so with a warning. |

**Returns:** The [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) the two printed constants give at that state, carrying this row's citation in its model so the state can be traced back to the page.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the page did not print both constants, naming the one it left out and what the cell held instead. |

### Gas.is_approximate()

```python
Gas.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### Gas.is_derived()

```python
Gas.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or prints on another row and leaves blank on this one, answers `False`: the number is the page's, and `converted` or `carried` says so.

### Gas.printed()

```python
Gas.printed(field_name: str, *, wanted_by: str = 'the caller') -> float
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

### Gas.why_missing()

```python
Gas.why_missing(field_name: str) -> str
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

## gases_named

```python
gases_named(name: str) -> tuple[Gas, ...]
```

Every published row for a gas name, across the tables.

Two books printing one gas is worth having, because the pair they print is
not always the same pair: for carbon dioxide one of them gives 1,30 and
the other 1,33. That is 2,3 per cent on the ratio and, since the speed of
sound goes as its square root, 1,2 per cent on the speed, which a reader
deserves to see both sides of rather than whichever this library happened
to load first.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | The gas as a table names it, matched without regard to case and ignoring a parenthesis the page adds: `"air"` answers with the row Hopkins prints as `"Air (dry)"`. |

**Returns:** The rows whose [`Gas.name`](/phonometry/reference/api/fluids/catalogue/#gas) matches, in the order the tables are read, which is empty when no page names it.

## PUBLISHED_FLUIDS

*Constant* (`mapping`).

## PUBLISHED_GASES

*Constant* (`mapping`).

---
title: "fluids.nonlinearity"
description: "The nonlinearity parameter B/A of liquids, as a handbook tabulates it."
sidebar:
  label: "nonlinearity"
---

The nonlinearity parameter B/A of liquids, as a handbook tabulates it.

Sound in a fluid is linear only in the limit of a vanishing amplitude. At a
finite one the pressure is not proportional to the change in density, and the
first term of the departure is what B/A measures. Expanding the adiabatic
pressure in the condensation `s = (rho - rho0) / rho0` gives
`p - p0 = A s + (B/2) s**2 + ...`, with `A = rho0 (dp/drho)_s`, which is
`rho0 c0**2`, and `B = rho0**2 (d2p/drho2)_s`: Rossing's equations (8.7) to
(8.9). B/A is the ratio of those two, dimensionless. It sets how fast a finite wave steepens towards a shock, how
strongly two beams generate their sum and difference frequencies, and with it
the output of a parametric array; the coefficient of nonlinearity is
`1 + B/(2A)`. In the rows below water sits between 4.2 and 6.2, the organic
liquids mostly between 6 and 12, the liquid metals between 2.7 and 7.8, and
air, for comparison, is 0.4 because an ideal gas has `B/A = gamma - 1`.

What the rows are
-----------------
Each row is one published value: a substance, the temperature it was measured
at, the value, and the paper it comes from. Three of Rossing's tables print a
reference beside every value and the fourth credits one paper in its caption,
and that is not decoration: at 30 °C water
prints four values between 5.18 and 5.38 from four papers, and toluene prints
5.6 at 20 °C from one paper and 8.929 at 30 °C from another. A caller who
wants "the" B/A of a liquid has to choose, and the row carries in
[`attributed_to`](/phonometry/reference/api/io/io/#cataloguerow) the full
reference the chapter's list gives for that number, so that the choice can be
made on the paper and not on the digits. Where the page prints a
plus-or-minus beside the value it is in
[`uncertainty`](/phonometry/reference/api/io/io/#cataloguerow).

Table 8.2 is the only one that prints a pressure, from 0.1 to 50 MPa, and its
rows carry it; the other three say "at atmospheric pressure" in the caption and
print no number, so their rows hold none rather than a 101 325 Pa the page did
not write. For six of the liquefied gases of Table 8.4 the caption cannot be
right: they are above their normal boiling point, liquid only under a pressure
the page does not give, and their rows say so.

What it is not
--------------
It is not a model. Nothing here interpolates between two temperatures or
between two papers, and no function in this library computes B/A from a sound
speed yet; a caller who needs a value at 25 °C where the table prints 20 and 30
has to decide how, and between which references.

Where the rows live
-------------------
In `fluids/data/rossing-2014-table-8-1.json` to `-8-4.json`, one file per
printed table, read at import through the package-data reader in
`phonometry._internal`, the same as every other catalogue here.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## nonlinearity_named

```python
nonlinearity_named(name: str) -> tuple[NonlinearityParameter, ...]
```

Every published value whose substance name contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | Part of a substance's name as the page prints it, matched without regard to case: `"water"` answers with every row of Tables 8.1 and 8.2 and with the sea water of Table 8.4. |

**Returns:** The matching rows, in the order the tables list them. Empty when nothing matches, which is not an error.

## NonlinearityParameter

```python
NonlinearityParameter(
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
    b_over_a: float | None = None,
    temperature_c: float | None = None,
    static_pressure_pa: float | None = None,
    year: int | None = None,
)
```

One published value of B/A, with the conditions it was measured at.

**Attributes**

| Name | Description |
| :--- | :--- |
| `b_over_a` | The nonlinearity parameter B/A. Dimensionless. |
| `temperature_c` | The temperature the value was measured at, in degrees Celsius. Table 8.2 prints it in kelvin and it is converted at 273.15 K exactly; the liquefied gases of Table 8.4 are far below zero and are held as the negative temperatures the page prints. |
| `static_pressure_pa` | The static pressure the value was measured at, in pascals, on the rows of the one table that prints it. Empty on every other row, whose caption says atmospheric pressure without a number. |
| `year` | The year the page prints beside the value, on the rows of the one table that prints one; it is the year of the row's reference. Six rows print a year their reference contradicts and serve none. |
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

### NonlinearityParameter.basis_of()

```python
NonlinearityParameter.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### NonlinearityParameter.is_approximate()

```python
NonlinearityParameter.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### NonlinearityParameter.is_derived()

```python
NonlinearityParameter.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### NonlinearityParameter.printed()

```python
NonlinearityParameter.printed(
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

### NonlinearityParameter.why_missing()

```python
NonlinearityParameter.why_missing(field_name: str) -> str
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

## PUBLISHED_NONLINEARITY

*Constant* (`mapping`).

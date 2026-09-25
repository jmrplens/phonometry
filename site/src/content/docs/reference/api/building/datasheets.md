---
title: "building.datasheets"
description: "Sound insulation as a data sheet or a test report prints it."
sidebar:
  label: "datasheets"
---

Sound insulation as a data sheet or a test report prints it.

The transmission loss tables of the books
([`catalogue`](/phonometry/reference/api/building/catalogue/)) print a field-incidence loss per
octave, rarely with a standard or a laboratory behind it. A product's data
sheet and a laboratory's test report print two quantities that are measured
to a standard and rated to another, and that are held here in a class each:

* the **sound reduction index** $R$ of an element measured in a
  laboratory to ISO 10140-2, one value per one-third octave band, rated to
  $R_\mathrm{w}$ with its spectrum adaptation terms $C$ and
  $C_\mathrm{tr}$ (ISO 717-1), and to the terms of the enlarged
  frequency ranges of its Annex B when the report prints the bands they
  need: [`SoundReductionSpectrum`](/phonometry/reference/api/building/datasheets/#soundreductionspectrum);
* the **reduction of impact sound pressure level** $\Delta L$ of a
  floor covering or a floating floor, defined by ISO 10140-1 Annex H
  (Equation (H.1), $\Delta L = L_\mathrm{n0} - L_\mathrm{n}$ on a
  reference floor) with the levels measured by ISO 10140-3, one value per
  one-third octave band, rated to $\Delta L_\mathrm{w}$ against the
  heavyweight reference floor of ISO 717-2, with the adaptation terms
  $C_{\mathrm{I},\Delta}$ and $C_\mathrm{I,r}$ of its Clause A.2.2:
  [`ImpactImprovementSpectrum`](/phonometry/reference/api/building/datasheets/#impactimprovementspectrum).

A book's transmission loss is not a laboratory's $R$, and a covering's
$\Delta L_\mathrm{w}$ is not the averaged improvement some handbooks
print (`impact_sound_improvement_db`
is one): each quantity has its own class and its own field names, so the
mistake of taking one for the other shows at the call.

Each row carries the ratings the sheet prints beside the bands, as printed,
and works them out again from the bands with its `rating()`. When a
catalogue file is read, [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) compares the
two and notes any difference beside the catalogue; it never reconciles
them. A rating the sheet prints and no function of this library works out
(a flanking level difference, an STC or an IIC) has no field here: it goes
in the row's [`note`](/phonometry/reference/api/io/io/#cataloguerow).

Nothing here ships with data. A caller's own catalogue holds these rows,
read by [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) from the file the caller typed
from the sheet.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ImpactImprovementSpectrum

```python
ImpactImprovementSpectrum(
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
    impact_improvement_50_db: float | None = None,
    impact_improvement_63_db: float | None = None,
    impact_improvement_80_db: float | None = None,
    impact_improvement_100_db: float | None = None,
    impact_improvement_125_db: float | None = None,
    impact_improvement_160_db: float | None = None,
    impact_improvement_200_db: float | None = None,
    impact_improvement_250_db: float | None = None,
    impact_improvement_315_db: float | None = None,
    impact_improvement_400_db: float | None = None,
    impact_improvement_500_db: float | None = None,
    impact_improvement_630_db: float | None = None,
    impact_improvement_800_db: float | None = None,
    impact_improvement_1000_db: float | None = None,
    impact_improvement_1250_db: float | None = None,
    impact_improvement_1600_db: float | None = None,
    impact_improvement_2000_db: float | None = None,
    impact_improvement_2500_db: float | None = None,
    impact_improvement_3150_db: float | None = None,
    impact_improvement_4000_db: float | None = None,
    impact_improvement_5000_db: float | None = None,
    weighted_impact_improvement_db: float | None = None,
    reference_floor_adaptation_term_db: float | None = None,
    impact_improvement_adaptation_term_db: float | None = None,
)
```

One covering or floating floor of a report, with its $\Delta L$.

The reduction of impact sound pressure level $\Delta L$ of
ISO 10140-1 Annex H, Equation (H.1): the normalized impact sound
pressure level of a reference floor without the covering less the one
with it, both measured by ISO 10140-3. It is the difference a floor
covering or a floating floor makes to the impact level of the floor, one
value per one-third octave band from 50 Hz to 5 kHz as the report prints
them, and the single numbers of ISO 717-2 printed beside them.
`rating` rates the bands again; the printed numbers stay as
printed.

$\Delta L_\mathrm{w}$ has a field of its own because it is a
rating against the reference floor of ISO 717-2 Table 4, not a mean over
frequency: a handbook's averaged improvement is another quantity, and
this class never reads it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `impact_improvement_50_db` | $\Delta L$ in the 50 Hz one-third octave band, in decibels, as printed. |
| `impact_improvement_63_db` | The same in the 63 Hz band. |
| `impact_improvement_80_db` | The same in the 80 Hz band. |
| `impact_improvement_100_db` | The same in the 100 Hz band. |
| `impact_improvement_125_db` | The same in the 125 Hz band. |
| `impact_improvement_160_db` | The same in the 160 Hz band. |
| `impact_improvement_200_db` | The same in the 200 Hz band. |
| `impact_improvement_250_db` | The same in the 250 Hz band. |
| `impact_improvement_315_db` | The same in the 315 Hz band. |
| `impact_improvement_400_db` | The same in the 400 Hz band. |
| `impact_improvement_500_db` | The same in the 500 Hz band. |
| `impact_improvement_630_db` | The same in the 630 Hz band. |
| `impact_improvement_800_db` | The same in the 800 Hz band. |
| `impact_improvement_1000_db` | The same in the 1 kHz band. |
| `impact_improvement_1250_db` | The same in the 1.25 kHz band. |
| `impact_improvement_1600_db` | The same in the 1.6 kHz band. |
| `impact_improvement_2000_db` | The same in the 2 kHz band. |
| `impact_improvement_2500_db` | The same in the 2.5 kHz band. |
| `impact_improvement_3150_db` | The same in the 3.15 kHz band. |
| `impact_improvement_4000_db` | The same in the 4 kHz band. |
| `impact_improvement_5000_db` | The same in the 5 kHz band. |
| `weighted_impact_improvement_db` | The weighted reduction of impact sound pressure level $\Delta L_\mathrm{w}$ the report prints, in decibels (ISO 717-2 Formulae (1) and (2)). It is what [`predicted_impact_insulation`](/phonometry/reference/api/building/simplified-model/#predicted_impact_insulation) takes as `delta_l_w`, through [`printed`](/phonometry/reference/api/io/io/#cataloguerowprinted). |
| `reference_floor_adaptation_term_db` | $C_\mathrm{I,r}$, the spectrum adaptation term of the reference floor with the covering (ISO 717-2 Clause A.2.2), in decibels, which data sheets of floating floor layers print beside $\Delta L_\mathrm{w}$. |
| `impact_improvement_adaptation_term_db` | $C_{\mathrm{I},\Delta}$, the spectrum adaptation term of the covering (Clause A.2.2, Formula (A.4)), in decibels. |
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

### ImpactImprovementSpectrum.bands()

```python
ImpactImprovementSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### ImpactImprovementSpectrum.basis_of()

```python
ImpactImprovementSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### ImpactImprovementSpectrum.from_printed()

*classmethod*

```python
ImpactImprovementSpectrum.from_printed(**cells: Any) -> Self
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

### ImpactImprovementSpectrum.impact_improvement_db()

```python
ImpactImprovementSpectrum.impact_improvement_db(band_hz: int) -> float
```

The reduction of impact level in one band, or a refusal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | A one-third-octave centre frequency from 50 Hz to 5 kHz. |

**Returns:** The printed $\Delta L$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the report has no number in that band, naming the row, the band and what the cell held instead; or when *band_hz* is not one of these bands. |

### ImpactImprovementSpectrum.is_approximate()

```python
ImpactImprovementSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### ImpactImprovementSpectrum.is_derived()

```python
ImpactImprovementSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### ImpactImprovementSpectrum.printed()

```python
ImpactImprovementSpectrum.printed(
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

### ImpactImprovementSpectrum.printed_fields()

```python
ImpactImprovementSpectrum.printed_fields() -> dict[str, Any]
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

### ImpactImprovementSpectrum.rating()

```python
ImpactImprovementSpectrum.rating() -> ImpactImprovementRatingResult
```

The single numbers of ISO 717-2 worked out from the row's bands.

[`weighted_impact_improvement`](/phonometry/reference/api/building/ratings/#weighted_impact_improvement) and
[`impact_improvement_adaptation_term`](/phonometry/reference/api/building/ratings/#impact_improvement_adaptation_term) on
the 16 one-third octaves 100 Hz to 3150 Hz, and
$C_\mathrm{I,r} = C_\mathrm{I,r,0} - C_{\mathrm{I},\Delta}$
with $C_\mathrm{I,r,0} = -11$ dB (Clause A.2.2).

**Returns:** The [`ImpactImprovementRatingResult`](/phonometry/reference/api/building/ratings/#impactimprovementratingresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a band from 100 Hz to 3150 Hz the row does not print, naming the row, the band and what the report had there. |

### ImpactImprovementSpectrum.spectrum()

```python
ImpactImprovementSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### ImpactImprovementSpectrum.values_at()

```python
ImpactImprovementSpectrum.values_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
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

### ImpactImprovementSpectrum.why_missing()

```python
ImpactImprovementSpectrum.why_missing(field_name: str) -> str
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

## SoundReductionSpectrum

```python
SoundReductionSpectrum(
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
    sound_reduction_index_50_db: float | None = None,
    sound_reduction_index_63_db: float | None = None,
    sound_reduction_index_80_db: float | None = None,
    sound_reduction_index_100_db: float | None = None,
    sound_reduction_index_125_db: float | None = None,
    sound_reduction_index_160_db: float | None = None,
    sound_reduction_index_200_db: float | None = None,
    sound_reduction_index_250_db: float | None = None,
    sound_reduction_index_315_db: float | None = None,
    sound_reduction_index_400_db: float | None = None,
    sound_reduction_index_500_db: float | None = None,
    sound_reduction_index_630_db: float | None = None,
    sound_reduction_index_800_db: float | None = None,
    sound_reduction_index_1000_db: float | None = None,
    sound_reduction_index_1250_db: float | None = None,
    sound_reduction_index_1600_db: float | None = None,
    sound_reduction_index_2000_db: float | None = None,
    sound_reduction_index_2500_db: float | None = None,
    sound_reduction_index_3150_db: float | None = None,
    sound_reduction_index_4000_db: float | None = None,
    sound_reduction_index_5000_db: float | None = None,
    weighted_sound_reduction_index_db: float | None = None,
    spectrum_adaptation_term_db: float | None = None,
    traffic_spectrum_adaptation_term_db: float | None = None,
    spectrum_adaptation_term_50_3150_db: float | None = None,
    spectrum_adaptation_term_50_5000_db: float | None = None,
    spectrum_adaptation_term_100_5000_db: float | None = None,
    traffic_spectrum_adaptation_term_50_3150_db: float | None = None,
    traffic_spectrum_adaptation_term_50_5000_db: float | None = None,
    traffic_spectrum_adaptation_term_100_5000_db: float | None = None,
    surface_density_kg_m2: float | None = None,
    thickness_mm: float | None = None,
    construction: str = '',
)
```

One element of a laboratory report, with its sound reduction index.

The sound reduction index $R$ of ISO 10140-2, measured between two
rooms with the flanking paths suppressed, one value per one-third octave
band from 50 Hz to 5 kHz as the report prints them, and the single
numbers of ISO 717-1 printed beside them. `rating` rates the bands
again; the printed numbers stay as printed.

**Attributes**

| Name | Description |
| :--- | :--- |
| `sound_reduction_index_50_db` | $R$ in the 50 Hz one-third octave band, in decibels, as printed. |
| `sound_reduction_index_63_db` | The same in the 63 Hz band. |
| `sound_reduction_index_80_db` | The same in the 80 Hz band. |
| `sound_reduction_index_100_db` | The same in the 100 Hz band. |
| `sound_reduction_index_125_db` | The same in the 125 Hz band. |
| `sound_reduction_index_160_db` | The same in the 160 Hz band. |
| `sound_reduction_index_200_db` | The same in the 200 Hz band. |
| `sound_reduction_index_250_db` | The same in the 250 Hz band. |
| `sound_reduction_index_315_db` | The same in the 315 Hz band. |
| `sound_reduction_index_400_db` | The same in the 400 Hz band. |
| `sound_reduction_index_500_db` | The same in the 500 Hz band. |
| `sound_reduction_index_630_db` | The same in the 630 Hz band. |
| `sound_reduction_index_800_db` | The same in the 800 Hz band. |
| `sound_reduction_index_1000_db` | The same in the 1 kHz band. |
| `sound_reduction_index_1250_db` | The same in the 1.25 kHz band. |
| `sound_reduction_index_1600_db` | The same in the 1.6 kHz band. |
| `sound_reduction_index_2000_db` | The same in the 2 kHz band. |
| `sound_reduction_index_2500_db` | The same in the 2.5 kHz band. |
| `sound_reduction_index_3150_db` | The same in the 3.15 kHz band. |
| `sound_reduction_index_4000_db` | The same in the 4 kHz band. |
| `sound_reduction_index_5000_db` | The same in the 5 kHz band. |
| `weighted_sound_reduction_index_db` | The weighted sound reduction index $R_\mathrm{w}$ the report prints, in decibels (ISO 717-1 Clause 4.4). |
| `spectrum_adaptation_term_db` | $C$, the adaptation term for spectrum No. 1 (pink noise), in decibels (Clause 4.5). |
| `traffic_spectrum_adaptation_term_db` | $C_\mathrm{tr}$, the adaptation term for spectrum No. 2 (urban traffic), in decibels. |
| `spectrum_adaptation_term_50_3150_db` | $C_{50-3150}$ of ISO 717-1 Annex B, in decibels. |
| `spectrum_adaptation_term_50_5000_db` | $C_{50-5000}$. |
| `spectrum_adaptation_term_100_5000_db` | $C_{100-5000}$. |
| `traffic_spectrum_adaptation_term_50_3150_db` | $C_{\mathrm{tr},50-3150}$. |
| `traffic_spectrum_adaptation_term_50_5000_db` | $C_{\mathrm{tr},50-5000}$. |
| `traffic_spectrum_adaptation_term_100_5000_db` | $C_{\mathrm{tr},100-5000}$. |
| `surface_density_kg_m2` | The mass per unit area of the element, in kilograms per square metre, as the report prints it. |
| `thickness_mm` | The overall thickness of the element, in millimetres. |
| `construction` | The build-up the report describes, as it describes it: the leaves, the studs, the cavity and what fills it. |
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

### SoundReductionSpectrum.bands()

```python
SoundReductionSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### SoundReductionSpectrum.basis_of()

```python
SoundReductionSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### SoundReductionSpectrum.from_printed()

*classmethod*

```python
SoundReductionSpectrum.from_printed(**cells: Any) -> Self
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

### SoundReductionSpectrum.is_approximate()

```python
SoundReductionSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### SoundReductionSpectrum.is_derived()

```python
SoundReductionSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### SoundReductionSpectrum.printed()

```python
SoundReductionSpectrum.printed(
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

### SoundReductionSpectrum.printed_fields()

```python
SoundReductionSpectrum.printed_fields() -> dict[str, Any]
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

### SoundReductionSpectrum.rating()

```python
SoundReductionSpectrum.rating() -> ExtendedWeightedRatingResult
```

The single numbers of ISO 717-1 worked out from the row's bands.

[`weighted_rating_extended`](/phonometry/reference/api/building/ratings/#weighted_rating_extended) on every band
the row prints: $R_\mathrm{w}$, $C$ and
$C_\mathrm{tr}$ from the 16 one-third octaves 100 Hz to
3150 Hz (Clauses 4.4 and 4.5), which the result also carries as the
[`weighted_rating`](/phonometry/reference/api/building/ratings/#weighted_rating) of those bands in its
`core`, and each adaptation term of Annex B whose range the row
prints every band of. A term whose range has a band the row does not
print is `None`: nothing is filled in to reach it.

**Returns:** The [`ExtendedWeightedRatingResult`](/phonometry/reference/api/building/ratings/#extendedweightedratingresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a band from 100 Hz to 3150 Hz the row does not print, naming the row, the band and what the report had there. |

### SoundReductionSpectrum.sound_reduction_index_db()

```python
SoundReductionSpectrum.sound_reduction_index_db(band_hz: int) -> float
```

The sound reduction index in one band, or a refusal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | A one-third-octave centre frequency from 50 Hz to 5 kHz. |

**Returns:** The printed $R$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the report has no number in that band, naming the row, the band and what the cell held instead; or when *band_hz* is not one of these bands. |

### SoundReductionSpectrum.spectrum()

```python
SoundReductionSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### SoundReductionSpectrum.values_at()

```python
SoundReductionSpectrum.values_at(
    frequencies_hz: ArrayLike,
) -> NDArray[np.float64]
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

### SoundReductionSpectrum.why_missing()

```python
SoundReductionSpectrum.why_missing(field_name: str) -> str
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

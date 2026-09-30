---
title: "building.catalogue"
description: "Transmission loss as the books print it, one row per construction."
sidebar:
  label: "catalogue"
---

Transmission loss as the books print it, one row per construction.

A partition's transmission loss is not a property of a material. It is what
one wall, built one way and mounted one way, did in one laboratory, and the
number changes with the studs, the ties, the sealing of the joints and the
size of the specimen. The models of `phonometry.building.prediction`
compute it from mass, stiffness and geometry; this module holds what was
measured, so that a prediction has something published to sit beside.

Why a catalogue of measurements is worth keeping
------------------------------------------------
The mass law gives a straight line. A real partition departs from it at the
critical frequency, at the mass-air-mass resonance of a double leaf and
wherever a stud shorts the two leaves together, and the size of those
departures is what a table like this shows and no formula in the book
reproduces. Two rows of the same brick wall, same mass and same thickness,
differ by 15 dB at 500 Hz and by 9 at 4 kHz because one is tied with strips
and the other with expanded metal, which is the whole argument for resilient
connections and is in the table rather than in the theory.

What the row carries
--------------------
Each octave band is a field of its own, `transmission_loss_500_db` and so
on, with the band's centre frequency in hertz and the unit in the name. Every
hedge of [`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow) works on a band
the way it works on any other field, so a band the page leaves empty says so
through [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing)
rather than answering zero. The thickness and the surface density the page
prints beside the description are fields of their own, because they are what a
reader compares two constructions by, and because the mass law needs the
second one.

What the numbers are worth
--------------------------
Bies calls his values "representative" and says only that they come from tests
published "by manufacturers and testing laboratories", without naming a
measurement standard, a mounting or a source for any row; that sentence is
quoted in full in the `about` of the data file. The qualifier the book does
give is "field incidence", which is the transmission loss of a diffuse field
over the range of angles a laboratory measures, and is what its own theory
computes. So a row here is a published measurement of a construction of that
description, useful for a sanity check and for an order of magnitude, and it
is not a specification of any wall anybody will build.

ASHRAE says as little and says it plainly: its nine machine equipment room
constructions are "compiled from controlled laboratory tests and represent a
condition typically superior to that found in field installations, because the
in situ acoustical performance of any wall, floor, or ceiling is adversely
affected by flanking paths, holes, penetrations, and other anomalies". No
laboratory, standard or reference is named for any of them either. Those rows
are here and the duct walls of the same chapter are not, because a duct wall is
measured in two directions that are different numbers and is indexed by the
duct's cross section, length and sheet gauge; it is published from
[`phonometry.noise_control.duct_walls`](/phonometry/reference/api/noise_control/duct-walls/).

Rossing's Table 11.4 is the same kind of row with fewer bands: twenty-three
common partitions, six octaves from 125 Hz to 4 kHz and a sound transmission
class, with no source, laboratory or standard named for any of them.

Tables that print a rating and nothing else
-------------------------------------------
Chapter 31 of the Spanish edition of Harris prints seven tables of sound
transmission class alone, with no frequency band anywhere: stud walls in six
conditions, concrete block walls of two weights, block walls under six
plasterboard mountings, doors unsealed and sealed, exterior doors, sealed
windows and floor-ceiling systems. Each is a row of this catalogue with every
band empty, and the rating in [`TransmissionLossSpectrum.sound_transmission_class`](/phonometry/reference/api/building/catalogue/#transmissionlossspectrum).
A caller after a spectrum reads the band fields and finds `None`;
[`TransmissionLossSpectrum.transmission_loss_db`](/phonometry/reference/api/building/catalogue/#transmissionlossspectrumtransmission_loss_db) then refuses with the
row and the band, because the page printed nothing there.

Most of those tables print one construction under several conditions, as
columns: the plasterboard layers and the cavity absorbent of Table 31.2, the
sealing of the doors of Table 31.6. A column is a row here, the construction
is its [`name`](/phonometry/reference/api/io/io/#cataloguerow) and the
column its [`variant`](/phonometry/reference/api/io/io/#cataloguerow),
composed from the printed headings above the cell. The window table is
printed the other way round, with the ratings as rows and the glazings as
cells, and is turned so that a row is a window. A row the page leaves blank
is a configuration it does not rate and has no row.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PUBLISHED_TRANSMISSION_LOSS

*Constant* (`mapping`).

## TRANSMISSION_LOSS_BANDS_HZ

*Constant* (`tuple`).

```python
TRANSMISSION_LOSS_BANDS_HZ = (63, 125, 250, 500, 1000, 2000, 4000, 8000)
```

## transmission_loss_named

```python
transmission_loss_named(
    name: str,
    *,
    catalogue: Mapping[str, TransmissionLossSpectrum] | None = None,
) -> tuple[TransmissionLossSpectrum, ...]
```

Every row whose printed description contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | A fragment of the printed description, matched without case. |
| `catalogue` | The rows to search in place of [`PUBLISHED_TRANSMISSION_LOSS`](/phonometry/reference/api/building/catalogue/#published_transmission_loss): a catalogue of your own that [`phonometry.io.read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) returns, `PUBLISHED_TRANSMISSION_LOSS \| mine` to search both at once, or any mapping of key to row (Default: `None`, which searches [`PUBLISHED_TRANSMISSION_LOSS`](/phonometry/reference/api/building/catalogue/#published_transmission_loss)). |

**Returns:** The rows whose description contains it, in catalogue order, which is empty when no row has one. It matches the printed description and nothing else, in the language the page is set in: `"door"` answers with the rows that carry the word, and not with Bies's hollow flush panel or solid hardwood, which the page describes without it, nor with the doors of the Spanish edition of Harris, which are `"puerta"`. The caller reads the thickness, the surface density and the variant to pick the row they mean.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a *catalogue* that is not a mapping, or that holds a row that is not a [`TransmissionLossSpectrum`](/phonometry/reference/api/building/catalogue/#transmissionlossspectrum), naming its key. |

## TransmissionLossSpectrum

```python
TransmissionLossSpectrum(
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
    transmission_loss_63_db: float | None = None,
    transmission_loss_125_db: float | None = None,
    transmission_loss_250_db: float | None = None,
    transmission_loss_500_db: float | None = None,
    transmission_loss_1000_db: float | None = None,
    transmission_loss_2000_db: float | None = None,
    transmission_loss_4000_db: float | None = None,
    transmission_loss_8000_db: float | None = None,
    thickness_mm: float | None = None,
    surface_density_kg_m2: float | None = None,
    sound_transmission_class: float | None = None,
    block_mass_kg: float | None = None,
    refers_to_row: str = '',
)
```

One construction of a published table, with its loss in each band.

**Attributes**

| Name | Description |
| :--- | :--- |
| `transmission_loss_63_db` | Airborne sound transmission loss in the 63 Hz octave band, in decibels, as printed. |
| `transmission_loss_125_db` | The same in the 125 Hz band. |
| `transmission_loss_250_db` | The same in the 250 Hz band. |
| `transmission_loss_500_db` | The same in the 500 Hz band. |
| `transmission_loss_1000_db` | The same in the 1 kHz band. |
| `transmission_loss_2000_db` | The same in the 2 kHz band. |
| `transmission_loss_4000_db` | The same in the 4 kHz band. |
| `transmission_loss_8000_db` | The same in the 8 kHz band. |
| `thickness_mm` | The overall thickness of the construction, in millimetres, as the page prints it beside the description. It is the assembly's thickness and not a leaf's: a double wall prints the pair and the cavity together. |
| `surface_density_kg_m2` | The mass per unit area, in kilograms per square metre, as printed. This is what the mass law takes, and what two rows of the same description are told apart by. |
| `sound_transmission_class` | The single-number rating the page prints beside the spectrum, where it prints one. It is not a band value and it does not follow from the ones beside it: an STC is computed from third-octave data, so a table that prints octave bands and an STC is printing two readings of one measurement and this catalogue keeps both. Empty for a page that rates nothing. |
| `block_mass_kg` | The mass of one masonry block, in kilograms, where a page prints it beside the rating. It is a mass per block and not per square metre, so it is not a surface density and is not comparable with `surface_density_kg_m2`: Harris Table 31.3 tells its lightweight and normal-weight walls of one thickness apart by it. |
| `refers_to_row` | The row this row's printed description refers to instead of repeating itself, named by the number the table prints. Harris Table 31.9 prints three floors once and the rows after them as "Igual que 8"; the printed text is kept whole in [`name`](/phonometry/reference/api/io/io/#cataloguerow), and this is the row it inherits from, resolved as `PUBLISHED_TRANSMISSION_LOSS[f"{row.table}/{row.refers_to_row}"]`. Empty when the description stands on its own. |
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

### TransmissionLossSpectrum.bands()

```python
TransmissionLossSpectrum.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### TransmissionLossSpectrum.basis_of()

```python
TransmissionLossSpectrum.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### TransmissionLossSpectrum.from_printed()

*classmethod*

```python
TransmissionLossSpectrum.from_printed(**cells: Any) -> Self
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

### TransmissionLossSpectrum.is_approximate()

```python
TransmissionLossSpectrum.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### TransmissionLossSpectrum.is_derived()

```python
TransmissionLossSpectrum.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### TransmissionLossSpectrum.printed()

```python
TransmissionLossSpectrum.printed(
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

### TransmissionLossSpectrum.printed_fields()

```python
TransmissionLossSpectrum.printed_fields() -> dict[str, Any]
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

### TransmissionLossSpectrum.spectrum()

```python
TransmissionLossSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### TransmissionLossSpectrum.transmission_loss_db()

```python
TransmissionLossSpectrum.transmission_loss_db(band_hz: int) -> float
```

The loss in one band, or a refusal that says what the page had.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_hz` | An octave-band centre frequency from [`TRANSMISSION_LOSS_BANDS_HZ`](/phonometry/reference/api/building/catalogue/#transmission_loss_bands_hz). |

**Returns:** The printed transmission loss, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the page has no number in that band, naming the row, the band and what the cell held instead; or when *band_hz* is not a band these tables print. |

### TransmissionLossSpectrum.values_at()

```python
TransmissionLossSpectrum.values_at(
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

### TransmissionLossSpectrum.why_missing()

```python
TransmissionLossSpectrum.why_missing(field_name: str) -> str
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

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
reproduces. Two rows of the same brick wall with different wall ties differ by
20 dB at 2 kHz, which is the whole argument for resilient connections, and it
is in the table rather than in the theory.

What the row carries
--------------------
Each octave band is a field of its own, `transmission_loss_500_db` and so
on, with the band's centre frequency in hertz and the unit in the name. Every
hedge of `CatalogueRow` works on a band
the way it works on any other field, so a band the page leaves empty says so
through `why_missing`
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

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PUBLISHED_TRANSMISSION_LOSS

*Constant* (`mappingproxy`).

## TRANSMISSION_LOSS_BANDS_HZ

*Constant* (`tuple`).

```python
TRANSMISSION_LOSS_BANDS_HZ = (63, 125, 250, 500, 1000, 2000, 4000, 8000)
```

## transmission_loss_named

```python
transmission_loss_named(name: str) -> tuple[TransmissionLossSpectrum, ...]
```

Every published row whose printed description contains *name*.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | A fragment of the printed description, matched without case. |

**Returns:** The rows whose description contains it, in the order the tables are read, which is empty when no page has one. It matches the printed description and nothing else: `"door"` answers with the ten rows that carry the word, and not with the hollow flush panel or the solid hardwood, which the page describes without it. The caller reads the thickness and the surface density to pick the row they mean.

## TransmissionLossSpectrum

```python
TransmissionLossSpectrum(
    *,
    name: str,
    source: str,
    table: str = '',
    variant: str = '',
    approximate: frozenset[str] = frozenset(),
    derived: Mapping[str, str] = ...,
    ranges: Mapping[str, tuple[float, float]] = ...,
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
| `name` | The material as the table names it, attribution stripped. |
| `variant` | Which specimen or condition this row is, when the page prints several under one name: `"chemically pure"`, `"direction x"`, `"0.68 mm diameter"`. Empty when the page prints one. |
| `source` | Document, table, PDF page and printed folio. |
| `table` | The data file this row was read from, without the extension, which is also the first half of its key in the catalogue that holds it. |
| `approximate` | Fields the page prints with a `~`. Not an estimate and not an interval: a number the author rounded on purpose. |
| `derived` | Field to how it was computed, for the ones this library worked out from the cells the page did print. A derived value is never stored as if it had been read. |
| `ranges` | `(low, high)` for each field the page prints as an interval rather than a value. |
| `bounded_above` | The subset of `ranges` the page prints as `< x` or `<= x`, where the low end is a floor and not a measurement. |
| `bounded_below` | The subset of `ranges` the page prints as `> x` or `>= x`, where the high end is the ceiling the quantity cannot pass and not a measurement: Cox gives an aerogel a porosity of `>0.75`, and the 1 beside it is what a porosity is, not what anybody measured. |
| `reported` | Field to the values the page lists for it, for a cell that prints several with no single one: `"25, 207, 230"` or `"96, 200-450"`, readings from as many studies. Each entry is a number or a `(low, high)` pair. Not a range, because the page did not print one, and not variants, because the page does not say which is which. |
| `unquantified` | Field to what the page printed in place of a number, for a cell that is neither empty nor numeric: `"Varies with frequency"`, `"model"`, `"…"` for a row of dots. What the page printed, and never a sentence about why the number is missing: `why_missing` composes that sentence around it, so a caller and a published table both get the cell as it reads on the page. |
| `uncertainty` | Field to the plus-or-minus the page prints beside the value, in the same unit. Cox prints an effective flow resistivity of `(540 +/- 92) x 10^3`, and two of his rows print an uncertainty as large as the value itself. What the interval means is not stated on the page, so it is not stated here either: it is the number the page prints beside the value and nothing more. |
| `misprinted` | Field to what the page prints there and why it cannot be that, for a cell whose defect is confirmed and registered in `docs/ERRATA.md`. The number is not served, because a catalogue that handed it over would put a value its own registry calls wrong behind every calculation downstream; it is not dropped either, because a reader reproducing the book needs to see what the book says. This is the narrowest of the hedges and the one that costs most to claim: a cell earns it only when the defect follows from the page itself or from something as settled as the molar mass of a named molecule, and never from one book disagreeing with another. |
| `not_derivable` | Field to why this library leaves it empty although the arithmetic would reach it. Bies leaves the speed of his aluminium honeycomb panels blank, and the modulus and the density beside it are effective ones, so `sqrt(E/rho)` would put a one-dimensional speed on a panel that has none. A row says so here, and nothing fills the cell afterwards. |
| `attributed_to` | Credit for a cell the book takes from someone else. Keyed by field name, or by `"row"` or `"table"` when the credit covers all of one. |
| `group` | The heading of the block this row sits under, when the table prints its rows in named groups: Cox files each material under `"Fibrous materials"`, `"Cellular materials"`, `"Granular materials"` or `"Other"`. Empty for a table that prints one list. |
| `note` | What the page says about this row beyond its numbers. |

### TransmissionLossSpectrum.bands()

```python
TransmissionLossSpectrum.bands() -> tuple[int, ...]
```

The octave bands this row prints a transmission loss for, in hertz.

### TransmissionLossSpectrum.spectrum()

```python
TransmissionLossSpectrum.spectrum() -> dict[int, float]
```

The row as `{band_hz: transmission_loss_db}` over the bands it prints.

A band the page left empty is left out rather than filled with a
zero, which in decibels would read as a partition that transmits
everything.

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

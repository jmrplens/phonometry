---
title: "io"
description: "Files: measurement audio, its calibration sidecar and catalogues of materials."
sidebar:
  label: "io"
---

Files: measurement audio, its calibration sidecar and catalogues of materials.

Every audio function here treats a file as a measurement record rather than
as material to be played back, which fixes the defaults: the native sample
rate is kept (no resampling on load), channels are never mixed down, samples
are never normalized, and integer PCM is scaled by exactly $2^{B-1}$
into float64 -- a power of two, so the scaling is exact in binary floating
point, and a constant that cancels out of every calibrated level because the
calibrator tone is read through the same path (the derivation lives with the
WAV reader's source).

[`read`](/phonometry/reference/api/io/io/#read) returns a [`Signal`](/phonometry/reference/api/io/io/#signal): the samples as `(channels, samples)`
float64 together with the sample rate, the calibration, the channel labels,
the `bext` broadcast provenance (EBU Tech 3285) and the origin record --
one immutable object that any `(x, fs, ...)` function of the library
accepts today via `numpy.asarray`. The base install reads every linear
WAV a sound level meter or field recorder writes (PCM 16/24/32-bit, IEEE
float, `WAVE_FORMAT_EXTENSIBLE`, RF64/BW64 past 4 GiB); the `[audio]`
extra (python-soundfile, which bundles the LGPL libsndfile) adds FLAC, AIFF,
Ogg/Opus and MP3, and lossy sources raise [`LossyCompressionWarning`](/phonometry/reference/api/io/io/#lossycompressionwarning)
because a level computed from a lossy codec is not metrologically defensible.

[`info`](/phonometry/reference/api/io/io/#info) answers from the headers alone -- format, rate, channels, valid
bits, duration, `bext`, cue points -- without decoding a single sample, so
it is safe on a 12-hour RF64. [`read_blocks`](/phonometry/reference/api/io/io/#read_blocks) streams what [`read`](/phonometry/reference/api/io/io/#read)
would return, one [`Signal`](/phonometry/reference/api/io/io/#signal) per block, into the library's stateful
filters. [`write`](/phonometry/reference/api/io/io/#write) produces WAV/BWF (and FLAC with the extra) with exact
integer codes, loud clipping ([`ClippingWarning`](/phonometry/reference/api/io/io/#clippingwarning)), optional TPDF dither
at 16 bits, a `bext` chunk written field by field, and never a silent
normalization. [`convert`](/phonometry/reference/api/io/io/#convert) moves a measurement between lossless
containers with samples, provenance and sidecar intact, and the calibration
travels in a versioned JSON sidecar ([`CalibrationSidecar`](/phonometry/reference/api/io/io/#calibrationsidecar)) next to the
audio, where the audio formats themselves have no field for it.

The rows of the library's published tables of materials are data read from a
file too, and the type they share lives here: [`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow), with
[`BandedRow`](/phonometry/reference/api/io/io/#bandedrow) for a row that prints one value per frequency band. Every
`PUBLISHED_*` catalogue of every package hands out subclasses of it, so a
row keeps the same hedges (a range, a bound, a word, a value converted from
the unit the page prints, a cell carried from another row) and says what
its source claims for each cell through [`CatalogueRow.basis_of`](/phonometry/reference/api/io/io/#cataloguerowbasis_of), one of
[`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases). A row checks itself when it is built, whether a
packaged table or a caller builds it, and [`CatalogueError`](/phonometry/reference/api/io/io/#catalogueerror) is what it
raises for a cell nothing downstream can read: a number that is not finite
or is text, a hedge on a field the row does not have, a value beside a hedge
that says there is none, a density below zero. A packaged table raises it
too for text that is not strict JSON or a table missing its citation.
[`CatalogueRow.from_printed`](/phonometry/reference/api/io/io/#cataloguerowfrom_printed) builds a row from the cells its page prints
and fills what follows from them, which is how every packaged catalogue is
built; [`CatalogueRow.printed_fields`](/phonometry/reference/api/io/io/#cataloguerowprinted_fields) gives those cells back, and
[`BandedRow.values_at`](/phonometry/reference/api/io/io/#bandedrowvalues_at) reads a banded row at an array of frequencies.

The library publishes no manufacturer's data, so a caller's own data sheets,
declarations of performance and test reports live in a catalogue file of
their own, which [`read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) reads into rows of the same classes:
a versioned JSON document with its [`Provenance`](/phonometry/reference/api/io/io/#provenance) (the kind of document,
its version, the day it was consulted, the laboratory and the report), each
cell named as the field it fills or in another unit of the same kind, and
every hedge the packaged tables use. What comes back is a [`Catalogue`](/phonometry/reference/api/io/io/#catalogue),
a read-only mapping keyed like the packaged ones that joins a `PUBLISHED_*`
catalogue with `|` and never lets one row replace another. The problems in
a file are raised at once in one [`CatalogueError`](/phonometry/reference/api/io/io/#catalogueerror), each
[`CatalogueIssue`](/phonometry/reference/api/io/io/#catalogueissue) with the JSON pointer to it (every problem of form,
and the first rule of the row contract each row breaks), and what is only
worth a second look rides on the catalogue as a note with one
[`CatalogueWarning`](/phonometry/reference/api/io/io/#cataloguewarning). [`parse_catalogue`](/phonometry/reference/api/io/io/#parse_catalogue) reads the same from text or
a mapping in memory, and [`write_catalogue`](/phonometry/reference/api/io/io/#write_catalogue) writes rows, a packaged
table among them, as a file that reads back into the same rows. Nothing the
file names is ever imported, and nothing it holds is kept anywhere but in the
objects handed back.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AudioFileInfo

```python
AudioFileInfo(
    path: str,
    container: str,
    format_name: str,
    fs: int,
    channels: int,
    frames: int,
    duration: float,
    bit_depth: int | None,
    *,
    lossy: bool,
    channel_mask: int | None = None,
    channel_labels: tuple[str, ...] | None = None,
    bext: BroadcastMetadata | None = None,
    has_ixml: bool = False,
    cue_points: tuple[CuePoint, ...] = (),
)
```

What [`phonometry.io.info`](/phonometry/reference/api/io/io/#info) learned without reading the samples.

`bit_depth` is the *valid* bits per sample where the notion applies
(for an EXTENSIBLE container the `wValidBitsPerSample` field, so a
20-in-24-bit file reports 20) and `None` for codecs that decode to
float. `lossy` marks codecs that cannot be trusted with the recorded
waveform: the transcribed lossy/companded tags, and any codec outside
the transcription that is not linear PCM/IEEE float, which fails
closed as suspect rather than passing as clean (the
`FormatChunk.lossy` property explains the bias);
[`phonometry.io.read`](/phonometry/reference/api/io/io/#read) warns when asked to read one.
`channel_mask`/`channel_labels`, `bext`, `has_ixml` and
`cue_points` are WAV-family metadata and are `None`/empty for other
containers -- except `bext`, which a FLAC can also carry in its
APPLICATION `riff` block (see [`phonometry.io._flac`](/phonometry/reference/api/io/io/)).

## BandedRow

```python
BandedRow(
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
)
```

One row of a table that prints its quantity once per frequency band.

The catalogues of this library that hold a spectrum read off a page keep
one field per band rather than an array, because every hedge
of [`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow) is keyed by field name and a cell the page left
empty has to say so the way any other cell does. What they then need is
the same three things: which bands this row filled, the row as a spectrum,
and a lookup that refuses rather than answering zero for a band the page
did not print. That is what this holds.

A subclass declares the bands its tables can print and how its band fields
are spelled, and defines the reading method under the name its own domain
uses, because `row.transmission_loss_db(500)` reads better than a generic
verb and says what comes back. `values_at` reads the row at a whole
array of frequencies, for a function that takes one value per band by
position.

**Attributes**

| Name | Description |
| :--- | :--- |
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

### BandedRow.bands()

```python
BandedRow.bands() -> tuple[int, ...]
```

The bands this row prints a value for, in hertz.

### BandedRow.basis_of()

```python
BandedRow.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### BandedRow.from_printed()

*classmethod*

```python
BandedRow.from_printed(**cells: Any) -> Self
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

### BandedRow.is_approximate()

```python
BandedRow.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### BandedRow.is_derived()

```python
BandedRow.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### BandedRow.printed()

```python
BandedRow.printed(
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

### BandedRow.printed_fields()

```python
BandedRow.printed_fields() -> dict[str, Any]
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

### BandedRow.spectrum()

```python
BandedRow.spectrum() -> dict[int, float]
```

The row as `{band_hz: value}` over the bands it prints.

A band the page left empty, or printed as something other than a
number, is left out rather than filled with a zero;
[`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) on that band's field says which it
was.

### BandedRow.values_at()

```python
BandedRow.values_at(frequencies_hz: ArrayLike) -> NDArray[np.float64]
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

### BandedRow.why_missing()

```python
BandedRow.why_missing(field_name: str) -> str
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

## BroadcastMetadata

```python
BroadcastMetadata(
    description: str,
    originator: str,
    originator_reference: str,
    origination_date: str,
    origination_time: str,
    time_reference: int,
    version: int,
    umid: bytes | None,
    loudness_value: float | None,
    loudness_range: float | None,
    max_true_peak_level: float | None,
    max_momentary_loudness: float | None,
    max_short_term_loudness: float | None,
    coding_history: str,
)
```

The `bext` broadcast extension chunk of EBU Tech 3285 (v2, 2011).

Field-by-field transcription of the Tech 3285 `BROADCAST_EXT`
structure. Offsets are into the chunk payload; the fixed part is 602
bytes in *every* version, because each revision claimed its new fields
from the tail of the original reserved block:

=======  ====  =============================  ==========================
Offset   Size  Field                          Held here as
=======  ====  =============================  ==========================
0        256   Description                    `description`
256      32    Originator                     `originator`
288      32    OriginatorReference            `originator_reference`
320      10    OriginationDate (yyyy-mm-dd)   `origination_date`
330      8     OriginationTime (hh-mm-ss)     `origination_time`
338      4     TimeReferenceLow               `time_reference` (low)
342      4     TimeReferenceHigh              `time_reference` (high)
346      2     Version (0, 1 or 2)            `version`
348      64    UMID (SMPTE ST 330), v >= 1    `umid`
412      2     LoudnessValue, v2              `loudness_value`
414      2     LoudnessRange, v2              `loudness_range`
416      2     MaxTruePeakLevel, v2           `max_true_peak_level`
418      2     MaxMomentaryLoudness, v2       `max_momentary_loudness`
420      2     MaxShortTermLoudness, v2       `max_short_term_loudness`
422      180   Reserved (zeros)               (dropped)
602      var   CodingHistory (EBU R98)        `coding_history`
=======  ====  =============================  ==========================

* `time_reference` is the two halves joined into one unsigned 64-bit
  count of **samples since midnight** of the origination date: the
  absolute instant of the file's first sample at single-sample
  resolution, which is what ties an environmental recording to wall
  time. Divide by the sample rate for seconds since midnight.
* The five v2 loudness fields are stored on disk as the int16 of
  100 x value rounded with ties away from zero, the Tech 3285 2.4
  rule (LUFS for the loudness values and
  maxima, LU for the range, dBTP for the true peak); they are returned
  already divided by 100. Tech 3285 fills an unset field with 0x7FFF,
  which is returned as `None`, as are all five for `version < 2`
  (where those bytes are still reserved space). `umid` is likewise
  `None` for `version < 1`.
* The strings are fixed-size ASCII fields padded with NUL; padding is
  stripped and stray non-ASCII bytes are decoded permissively
  (latin-1) rather than making an otherwise sound file unreadable.
  `coding_history` keeps its internal CR/LF line structure (one line
  per coding step, EBU R98 format `A=PCM,F=48000,W=24,M=stereo,T=...`);
  only trailing NUL padding and whitespace are stripped.

## CalibrationSidecar

```python
CalibrationSidecar(
    calibration_factor: float,
    reference_spl: float | None = None,
    calibrator_frequency: float | None = None,
    calibrator_model: str | None = None,
    channel_labels: tuple[str, ...] | None = None,
    phonometry_version: str | None = None,
)
```

The calibration record of one audio file (schema v1, module docstring).

`calibration_factor` is the digital-to-pascal multiplier and the
only mandatory field; the rest document how it was obtained
(`reference_spl`, `calibrator_frequency`, `calibrator_model`)
and what the channels are (`channel_labels`).
`phonometry_version` records the writing library version.

## Catalogue

```python
Catalogue(
    *,
    name: str,
    row_type: type[R],
    about: str,
    provenance: Provenance,
    rows: Mapping[str, R],
    extras: Mapping[str, Mapping[str, str]] = ...,
    conventions: tuple[str, ...] = (),
    notes: tuple[CatalogueIssue, ...] = (),
    schema_version: int = 1,
    file_sha256: str = '',
)
```

A caller's catalogue: rows of one class, keyed as the packaged ones are.

What [`read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) and [`parse_catalogue`](/phonometry/reference/api/io/io/#parse_catalogue) return. It is a
read-only mapping from `"<name>/<key>"` to a row, so it goes wherever a
`PUBLISHED_*` catalogue goes, and a row's [`CatalogueRow.table`](/phonometry/reference/api/io/io/#cataloguerow) is
the catalogue's name. `PUBLISHED_POROUS | mine` reads both as one and
refuses a key both hold rather than letting one row replace the other;
a caller's catalogue can never take a name of the packaged form, so the
keys of the two never meet.

Two catalogues are equal when they hold the same rows under the same
keys, as any two mappings are.

**Attributes**

| Name | Description |
| :--- | :--- |
| `name` | The catalogue's name, the first half of every key. |
| `row_type` | The class every row is. |
| `about` | What the document is and how it was read. |
| `provenance` | The document the rows were read from. A row that narrows it holds its own in [`CatalogueRow.provenance`](/phonometry/reference/api/io/io/#cataloguerow). |
| `rows` | The rows, by key, read-only, in the order of the document. |
| `extras` | The caller's own `x-...` columns, by row key and column, as text: a number keeps the digits it was written with. |
| `conventions` | The notes and legends the document prints for the whole table. |
| `notes` | What is worth a second look, each a [`CatalogueIssue`](/phonometry/reference/api/io/io/#catalogueissue) of severity `"note"`. |
| `schema_version` | The version of the layout the document was written in. |
| `file_sha256` | The SHA-256 of the bytes read, in hexadecimal, so that a report can cite exactly which file its values came from; empty for a document handed over as a mapping, which has no bytes. |

## CATALOGUE_BASES

*Constant* (`tuple`).

```python
CATALOGUE_BASES = ('measured', 'declared', 'calculated', 'estimated', 'extended')
```

## CatalogueError

A catalogue that does not say what a reader needs to trust it.

Raised for a table document that is missing what every table needs (a
citation, an `about`, rows, a key per row) or that holds what JSON
does not (a `NaN`, a name written twice in one object), and for a row
that breaks the contract every row is held to when it is built: a
numeric cell holding text or a `NaN`, a hedge naming a field the row
does not have, a bound with no printed end, a density below zero. A
`ValueError`, because the data is wrong and not the call, whether
it came from a file or from a caller building a row by hand.

`issues` holds the problems found, each a [`CatalogueIssue`](/phonometry/reference/api/io/io/#catalogueissue)
naming where it is. A reader of a catalogue file raises one error for
the whole file, with every problem of form in it and the first rule of
the row contract each row breaks; a row built in Python raises one with
a single issue, located at `"<Python>"`.

## CatalogueIssue

```python
CatalogueIssue(
    *,
    file: str,
    location: str,
    row_key: str = '',
    field: str = '',
    message: str,
    severity: Literal['error', 'note'] = 'error',
)
```

One thing wrong with a catalogue, or worth a second look, and where.

A reader of a catalogue file collects every one of these before it
builds a single row, so one pass over a file shows everything that has
to change in it. A [`CatalogueError`](/phonometry/reference/api/io/io/#catalogueerror) carries the errors; a note
rides on the catalogue that was read, in `Catalogue.notes`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `file` | The file, as the caller named it; empty for a row built in Python. |
| `location` | Where in the file: a JSON pointer (RFC 6901) such as `"/rows/1/porosity"`; `"<Python>"` for a row built in Python. |
| `row_key` | The key of the row, when the issue sits in one. |
| `field` | The field of the row, when the issue is about one cell. |
| `message` | What is wrong and, where it helps, what to write instead. |
| `severity` | `"error"`, which stops the read, or `"note"`, which is kept and read past. |

## CatalogueRow

```python
CatalogueRow(
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
)
```

One row of a published table, with what each cell said.

The quantities are the subclass's business; this holds what surrounds
them. A numeric field of the subclass is `None` whenever the page had
something other than a single number there, and the hedges below say
what: an interval in `ranges`, a list of values in
`reported`, a word in `unquantified`. `why_missing`
reads them back in the page's own terms, so a caller who gets `None`
is not left to guess whether the material has no such property, whether
the book left the cell empty, or whether it printed three numbers.

Every row of every published catalogue is one of these, a frozen and
keyword-only dataclass. A subclass written to hold a quantity no
catalogue of the library publishes is the same, and it leaves out
`slots=True`: on the Python 3.13 releases that predate the fix, a
slotted dataclass that calls `super()` without arguments, as a
`__post_init__` does, raises `TypeError` when it is built.

**A row checks itself when it is built**, whoever builds it, and refuses
with [`CatalogueError`](/phonometry/reference/api/io/io/#catalogueerror) rather than holding a cell nothing
downstream can read. The check is the same for a packaged row, a row a
reader builds from a file and a row written by hand:

1. `name` and `source` are text that is not empty, and so is
   every text a hedge holds: `why_missing` hands a
   `misprinted` or `not_derivable` text back as it is, and
   an empty one would answer as a cell that is not missing at all.
2. A numeric field holds `None` or a finite number, never a `bool`, a
   text or a `NaN`; an `int` field a whole number; a `bool` field
   `True` or `False`; a text field text.
3. A set of field names (`approximate` and the bounds) is frozen
   into a `frozenset`, whatever it was written as.
4. Every mapping is frozen, all the way down: its pairs into tuples.
5. Every key of a hedge names a numeric field of the row. `basis`
   and `attributed_to` also take the `"row"`, and a credit the
   `"table"`; `derived`, `carried` and `misprinted`
   may name a text field too (but not `source` or `table`,
   which are not cells of the page), because a page misprints a name or
   gives a description by reference to another row.
6. `bounded_above` and `bounded_below` name only fields that
   have a range.
7. A range's ends are finite, the low one no higher than the high one,
   and the end the page printed is there; an interval among the
   readings of `reported` runs from low to high as well.
8. A list in `reported` holds at least one reading, and its
   readings are finite; an `uncertainty` is finite and not below
   zero.
9. A field in `unquantified`, `not_derivable` or
   `reported`, or a numeric field in `misprinted`, holds no
   value; a field in `converted` or `carried` holds
   something: a value, a range or a list.
10. `basis` holds only the words of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).
11. A quantity whose unit cannot be negative is not: a field ending in
    `_kg_m3`, `_kg_m2`, `_kg`, `_kg_mol`, `_m_s`, `_pa`,
    `_pa_s_m2`, `_pa_s_m`, `_n_m3`, `_mm`, `_um`, `_m`,
    `_m2`, `_m_hz` or `_per_cm`, in its value, its range and its
    readings. A `porosity` runs from 0 to 1, and the per-cent fields
    that are a share of a whole (`shot_content_percent`,
    `binder_content_percent` and `adhered_area_percent`) from 0 to
    100.
    Nothing else is bounded: a Celsius temperature, a decay rate per
    metre and a level in decibels can be negative, and a size is never
    a reason to refuse a number.

**Two ways to build a row.** `Cls(...)` is literal: the row holds what
it is given, checked and frozen, and nothing is worked out.
`from_printed` takes the cells the page prints, converts a figure
written in a unit the class takes as an alias of its own, builds the
row, fills what its class knows how to work out from those cells, and
marks each filled value in `derived`. It is the one path that
derives anything, and every packaged catalogue is built through it. To
change a cell and have what follows from it follow again, change it in
`printed_fields` and build again with `from_printed`:
`dataclasses.replace` copies the derived values as they were, which
then no longer follow from the cell that changed.

The fields are told apart by their resolved annotations, once per
class, so a subclass annotates each of its own fields as one of
`float | None` (`Optional[float]` is the same annotation),
`int | None`, `bool`, `str`, `frozenset[str]` or
`Mapping[str, ...]` of those; any other annotation, a bare `float`
or `int` included, raises `TypeError` the first time the class
is built, rather than letting a field through unchecked.

**Attributes**

| Name | Description |
| :--- | :--- |
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

### CatalogueRow.basis_of()

```python
CatalogueRow.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### CatalogueRow.from_printed()

*classmethod*

```python
CatalogueRow.from_printed(**cells: Any) -> Self
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

### CatalogueRow.is_approximate()

```python
CatalogueRow.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### CatalogueRow.is_derived()

```python
CatalogueRow.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### CatalogueRow.printed()

```python
CatalogueRow.printed(
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

### CatalogueRow.printed_fields()

```python
CatalogueRow.printed_fields() -> dict[str, Any]
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

### CatalogueRow.why_missing()

```python
CatalogueRow.why_missing(field_name: str) -> str
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

## CatalogueWarning

A catalogue file was read, and some of its cells are worth a second look.

Emitted once per document by [`read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) and
[`parse_catalogue`](/phonometry/reference/api/io/io/#parse_catalogue) when [`Catalogue.notes`](/phonometry/reference/api/io/io/#catalogue) is not empty, with
the count and the first notes. A note never changes a row: a value
measured with no report or laboratory named for it, or a word in place of
a number long enough to be a sentence, is kept as the file writes it.

## ClippingWarning

Warns that samples exceeded full scale and were saturated on write.

## convert

```python
convert(
    src: str | Path,
    dst: str | Path,
    *,
    subtype: str | None = None,
    block_size: int = 1048576,
) -> AudioFileInfo
```

Convert a measurement file, keeping samples, bext and sidecar whole.

See the module docstring for the full contract. Typical uses: an
overnight RF64 archived to FLAC at a third of the size and back
again bit for bit; a 32-bit-float working file flattened to a
24-bit BWF for delivery; a recorder's ADPCM listening copy expanded
to linear WAV (with the lossy warning, and the advice to keep the
original) so tools that only read PCM can open it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `src` | The file to read (any format the readers accept). |
| `dst` | The file to write; the suffix picks the container (WAV family or, with the `[audio]` extra, FLAC). Lossy suffixes are refused by policy. |
| `subtype` | Target sample format; `None` preserves the source's depth (the module docstring's mapping). An explicitly narrower choice quantises with the clipping count reported. |
| `block_size` | Frames per streamed block; the memory ceiling. |

**Returns:** [`phonometry.io.info`](/phonometry/reference/api/io/io/#info) of the written file.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a lossy or unknown target suffix, source and destination naming the same file, a FLAC target that cannot hold the source without an explicit `subtype`, or an invalid `block_size`. |
| ImportError | If source or target needs the `[audio]` extra and it is not installed. |

## CuePoint

```python
CuePoint(
    cue_id: int,
    position: int,
    chunk_id: bytes,
    chunk_start: int,
    block_start: int,
    sample_offset: int,
)
```

One record of the `cue` chunk (1991 RIFF specification).

For the plain `data`-chunk case (no playlist, no wave list), which is
what marker-writing recorders produce, `sample_offset` is the marker's
position in samples from the start of the data.

## info

```python
info(path: str | Path) -> AudioFileInfo
```

Describe an audio file without reading its samples.

For the WAV family this is a single pass over the chunk headers on the
base install, whatever the codec inside -- format, rate, channels,
frames and duration, valid bits, lossy flag, EXTENSIBLE channel mask
and labels, `bext` provenance, `iXML` presence and cue markers --
with a cost independent of file size. Other containers are described
through the `[audio]` extra's header reader. `info` never warns
about lossy content (inspecting a file is not measuring from it);
the `lossy` field carries the fact instead.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | The file to describe. |

**Returns:** The file's description.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the file matches no known audio format. |
| ImportError | If the container needs the `[audio]` extra and it is not installed. |

## LossyCompressionWarning

Warns that samples came through a lossy codec: levels are not defensible.

## parse_catalogue

```python
parse_catalogue(
    document: str | Mapping[str, Any],
    *,
    row_type: type[R],
    label: str = '<document>',
) -> Catalogue[R]
```

Read a catalogue from JSON text, or from a mapping already in memory.

The same reading as [`read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue), for a document that is not a
file: text built in a notebook, a spreadsheet turned into a dictionary, a
test. A mapping has no printed digits, so a figure written in another
unit is converted from the `repr` of its float; a `NaN` is refused as
it is from text, but two members of one name cannot be told apart once a
dictionary has merged them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `document` | JSON text, or a mapping of the same shape. |
| `row_type` | The class of every row, a subclass of [`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow). |
| `label` | What names the document in every issue. |

**Returns:** The catalogue, keyed `"<catalogue>/<key>"`. Its [`file_sha256`](/phonometry/reference/api/io/io/#catalogue) is the SHA-256 of the text's UTF-8 bytes, or empty for a mapping.

**Raises**

| Exception | When |
| :--- | :--- |
| CatalogueError | for everything [`read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) refuses. |
| TypeError | for a *row_type* that is not a catalogue row class, and for a *document* that is neither text nor a mapping. |

**Warns**

| Warning | When |
| :--- | :--- |
| CatalogueWarning | once, when the catalogue carries notes. |

## Provenance

```python
Provenance(
    *,
    kind: str,
    document: str,
    version: str | None,
    consulted: str,
    publisher: str = '',
    issued: str = '',
    url: str = '',
    sha256: str = '',
    page: str = '',
    printed_table: str = '',
    laboratory: str = '',
    accreditation: str = '',
    report: str = '',
    test_date: str = '',
    test_standard: str = '',
    field_test_standards: Mapping[str, str] = ...,
)
```

Which document a catalogue's cells were read from, and how.

A book's table is cited by its page, and the citation of every packaged
row says all there is to say. A manufacturer's data sheet is not a book:
it is revised without notice, the same product has several of them, and
what it prints may be a laboratory's result, a value declared under a
product standard or a figure from a calculation. So a row read from a
caller's catalogue file carries this, and its [`CatalogueRow.source`](/phonometry/reference/api/io/io/#cataloguerow)
is composed from it: for a `"publication"` the document as it is cited,
and for every other kind the document, its publisher, its version, the
page and the table, the report and the laboratory, and the day it was
consulted.

**Attributes**

| Name | Description |
| :--- | :--- |
| `kind` | One of [`PROVENANCE_KINDS`](/phonometry/reference/api/io/io/#provenance_kinds). |
| `document` | The document's title as it prints it. |
| `version` | The revision the document prints (`"Rev. 4"`), or `None` when it prints none, which is a different answer from a version nobody wrote down. |
| `consulted` | The day the document was read, as `YYYY-MM-DD`: a data sheet changes under the same title. |
| `publisher` | Who issues the document. |
| `issued` | When the document says it was issued, as `YYYY`, `YYYY-MM` or `YYYY-MM-DD`, at the precision it prints. |
| `url` | Where the document was found. Never opened by this library. |
| `sha256` | The digest of the file that was read, in hexadecimal, so that the copy can be told apart from a later revision. Never checked against anything by this library. |
| `page` | The page the cells are on. |
| `printed_table` | The label of the table on the page, as it prints it (`"Table 2"`). |
| `laboratory` | The laboratory that made the measurement. |
| `accreditation` | The laboratory's accreditation, as printed. |
| `report` | The number of the test report. |
| `test_date` | When the test was made, as printed. |
| `test_standard` | The standard the test followed, as printed (`"ISO 9053-1:2018"`). |
| `field_test_standards` | Field to the standard a document cites for that property alone, when it names a different one for each; it takes precedence over `test_standard` for that field. |

### Provenance.cited()

```python
Provenance.cited() -> str
```

The citation every row read with this provenance carries as its source.

A publication is cited as its document is, because a book's citation
already names its edition and its page. Every other document is
cited by its title, its publisher, the version it prints (or that it
prints none), the page and the table, the report and the laboratory,
and the day it was consulted, because each of those can change under
the same title.

### Provenance.noun

*property*

The document as the subject of a sentence: `"the datasheet"`.

### Provenance.test_standard_of()

```python
Provenance.test_standard_of(field_name: str) -> str
```

The standard the test of one field followed, as printed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | A field of the row. |

**Returns:** The field's own entry in `field_test_standards`, else `test_standard`, else the empty string.

## PROVENANCE_KINDS

*Constant* (`tuple`).

```python
PROVENANCE_KINDS = ('datasheet', 'declaration_of_performance', 'test_report', 'measurement', 'calculation', 'publication', 'other')
```

## read

```python
read(path: str | Path, *, calibration_factor: float | None = None) -> Signal
```

Read an audio file into a [`Signal`](/phonometry/reference/api/io/io/#signal).

The samples come back float64, at the file's native rate, in the
library's `(channels, samples)` order, scaled by $2^{B-1}$ for
integer sources (exact in binary floating point, and any fixed scaling
cancels out of calibrated results -- see [`phonometry.io._wav`](/phonometry/reference/api/io/io/)).
Nothing else is done to them: no resampling, no normalisation, no
channel mixing -- each of which would silently change the level or the
timing that a measurement depends on, and each of which is a documented
default somewhere in the ecosystem (librosa resamples to 22050 Hz and
mixes to mono; python-acoustics normalised on load).

The base install reads the whole linear WAV family: PCM at any depth,
IEEE float, WAVE_FORMAT_EXTENSIBLE (with its channel labels), BWF
`bext` provenance, RF64/BW64 long recordings. With the `[audio]`
extra (python-soundfile), FLAC, AIFF, Ogg Vorbis, Opus, MP3 and
compressed WAV codecs (ADPCM, A-law/mu-law) decode too; without it,
those raise `ImportError` naming the extra. A lossy source is
read but announced with [`LossyCompressionWarning`](/phonometry/reference/api/io/io/#lossycompressionwarning) and stamped
`lossy=True` on `signal.source`: a level computed from an
approximation of the waveform is not a measurement.

A calibration sidecar beside the file
([`phonometry.io._sidecar`](/phonometry/reference/api/io/io/)) is applied automatically: its
`calibration_factor` fills in when the argument here is `None`
(the explicit argument always wins -- the caller knows more than a
file on disk), and its curated `channel_labels` replace labels
derived from the file's channel mask.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | The file to read. |
| `calibration_factor` | Digital-to-pascal multiplier to attach to the returned signal when the calibration is known (typically from [`phonometry.metrology.sensitivity`](/phonometry/reference/api/metrology/calibration/#sensitivity) on a calibrator recording read through this same function). `None` (the default) takes the sidecar's factor when a sidecar exists, and otherwise leaves the signal in digital full-scale units. |

**Returns:** The signal with its metadata.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the file matches no known audio format, or a sidecar exists but is invalid. |
| ImportError | If the format needs the `[audio]` extra and it is not installed. |

## read_blocks

```python
read_blocks(
    path: str | Path,
    block_size: int,
    *,
    overlap: int = 0,
    calibration_factor: float | None = None,
) -> Iterator[Signal]
```

Stream an audio file as [`Signal`](/phonometry/reference/api/io/io/#signal) blocks.

Yields what [`phonometry.io.read`](/phonometry/reference/api/io/io/#read) would return for the same
file, cut into consecutive pieces of `block_size` frames (the last
piece may be shorter), while holding only one block in memory -- the
way an overnight RF64 flows through `BlockProcessing(stateful=True)`
filters without ever existing as an array. Each block is a `Signal`
carrying what the whole-file read would carry: the rate, the
calibration (from `calibration_factor` or the sidecar, by the same
precedence as `read`), the channel labels, the `bext` provenance
and the origin record. So a block is `read(path)` cropped to its own
span, which is also why its provenance still describes the file, as a
[`crop`](/phonometry/reference/api/io/io/#signalcrop) does. See the module docstring for
the per-backend mechanics and the exact overlap rule.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | The file to stream. |
| `block_size` | Frames per block (at least 1). |
| `overlap` | Frames each block shares with its predecessor (`0 <= overlap < block_size`). |
| `calibration_factor` | Digital-to-pascal multiplier to attach to every block, as in [`read`](/phonometry/reference/api/io/io/#read). `None` (the default) takes the sidecar's factor when a sidecar exists, and otherwise leaves the blocks in digital full-scale units. |

**Returns:** An iterator of Signal blocks.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the geometry is invalid, `calibration_factor` is not a positive finite number, the file matches no known audio format, or a sidecar exists but is invalid (all at the call), or the data chunk is shorter than its header claims (at the block that reaches the end of it). |
| ImportError | If the format needs the `[audio]` extra and it is not installed. |

## read_catalogue

```python
read_catalogue(
    path: str | os.PathLike[str],
    *,
    row_type: type[R],
) -> Catalogue[R]
```

Read a catalogue of your own from a JSON file into rows of *row_type*.

The file holds one table: a header with the document's provenance, and
rows whose cells are named as the fields of *row_type* or in another unit
of the same kind (the module docstring lays it out). Every row is built
through [`CatalogueRow.from_printed`](/phonometry/reference/api/io/io/#cataloguerowfrom_printed), so a row read from a file and
a packaged row with the same cells are the same row, and
[`printed`](/phonometry/reference/api/io/io/#cataloguerowprinted), [`why_missing`](/phonometry/reference/api/io/io/#cataloguerowwhy_missing) and every
method of the class behave alike on both. Every row carries the
document's [`Provenance`](/phonometry/reference/api/io/io/#provenance), narrowed by the row where it narrows it,
and a [`source`](/phonometry/reference/api/io/io/#cataloguerow) composed from it.

The problems in the file are raised together in one
[`CatalogueError`](/phonometry/reference/api/io/io/#catalogueerror), each issue with the JSON pointer to it: every
problem of form, and the first rule of the row contract each row breaks.
The class named in the file is only compared with *row_type*, and nothing
the file names is ever imported.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | The file, whose name ends in `.json` (in any case). |
| `row_type` | The class of every row, a subclass of [`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow) such as `materials.PorousMaterial`. |

**Returns:** The catalogue, keyed `"<catalogue>/<key>"`.

**Raises**

| Exception | When |
| :--- | :--- |
| CatalogueError | for a file larger than 16 MiB, text that is not UTF-8 or not JSON, and the problems the document holds, all at once: every problem of form, and the first rule of the row contract each row breaks. |
| TypeError | for a *row_type* that is not a catalogue row class. |
| ValueError | for a name that does not end in `.json`. |
| OSError | as the file system raises it, untouched. |

**Warns**

| Warning | When |
| :--- | :--- |
| CatalogueWarning | once, when the catalogue carries notes. |

## read_sidecar

```python
read_sidecar(audio_path: str | Path) -> CalibrationSidecar | None
```

Read an audio file's calibration sidecar, if one exists.

Returns `None` when there is no sidecar -- the common case, never an
error. A file *at the sidecar's reserved name* that is not a valid
phonometry calibration record raises instead of being ignored: a
corrupted or foreign file squatting on `*.phonometry.json` beside a
measurement is a problem to surface, not to read past (silently
dropping it would silently drop the calibration).

**Parameters**

| Name | Description |
| :--- | :--- |
| `audio_path` | The audio file whose sidecar to look for. |

**Returns:** The parsed record, or `None` when no sidecar exists.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the sidecar exists but is not valid JSON, does not declare this schema, was written by a newer schema version, or carries malformed fields. |

## sidecar_path

```python
sidecar_path(audio_path: str | Path) -> Path
```

The sidecar filename of an audio file (see the module docstring).

## Signal

```python
Signal(
    data: NDArray[np.float64],
    fs: int,
    calibration_factor: float | None = None,
    channel_labels: tuple[str, ...] | None = None,
    provenance: BroadcastMetadata | None = None,
    source: SignalOrigin | None = None,
)
```

A sampled acoustic signal with its rate, calibration and provenance.

Written `io.Signal` after `from phonometry import io`, or
`phonometry.Signal`: the top level publishes this one class because
seven packages accept one, and those are the two spellings. The module
holding this definition is private, and a name read out of it is the same
object with nothing promising it will stay reachable that way.

Returned by [`phonometry.io.read`](/phonometry/reference/api/io/io/#read); can also be constructed directly
around an array. The object is a drop-in replacement for the bare array:
it implements `__array__`, so `np.asarray(signal)` yields the
samples -- 1-D for one channel, `(channels, samples)` for several --
and the object can be passed straight to the `(x, fs, ...)` functions
of the library. Indexing, `len()` and the `size`/`ndim`/`shape`/
`dtype` attributes forward to that same view, so the object and the
array it stands for never disagree about geometry.

`data` is always stored `(channels, samples)` float64 (a 1-D input
is stored as one channel); `calibration_factor` is the multiplier
converting digital full-scale units to pascals, the same convention as
`signals.levels` (0 dBFS = RMS 1.0), and stays `None` until a
calibration is actually known -- the object never invents one.
`channel_labels` names each channel (e.g. loudspeaker positions from
an EXTENSIBLE channel mask); `provenance` carries the `bext`
broadcast metadata when the file had it; `source` records the file,
container, codec, bit depth and lossy flag of the origin.

### Signal.crop()

```python
Signal.crop(tmin: float | None = None, tmax: float | None = None) -> Signal
```

The samples between *tmin* and *tmax* seconds, as a new Signal.

The edges are seconds from the start of the record, and follow the
half-open convention of a Python slice: the sample at *tmax* is not
included, so cropping `[0, t)` and `[t, end)` partitions the
record with nothing counted twice. `None` means the record's own
edge.

**Parameters**

| Name | Description |
| :--- | :--- |
| `tmin` | Start time, in seconds (default: the beginning). |
| `tmax` | End time, in seconds, exclusive (default: the end). |

**Returns:** A [`Signal`](/phonometry/reference/api/io/io/#signal) over that span, at the same rate.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If an edge is negative, not finite, or if *tmax* is not after *tmin*. |

### Signal.dtype

*property*

### Signal.duration

*property*

Length in seconds.

### Signal.n_channels

*property*

Number of channels.

### Signal.n_samples

*property*

Samples per channel (frames).

### Signal.ndim

*property*

### Signal.pick()

```python
Signal.pick(channels: int | Sequence[int]) -> Signal
```

The chosen channels, as a new Signal.

Indexing a Signal yields the samples, which is what makes it a
drop-in for the array it stands for; the cost is that `sig[0]`
drops the rate, the calibration and the labels on the floor. This
keeps them, so a multichannel take can be narrowed to the channel
under test and stay a measurement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `channels` | One channel index, or a sequence of them, in the order they should appear in the result. |

**Returns:** A [`Signal`](/phonometry/reference/api/io/io/#signal) with those channels, in that order.

**Raises**

| Exception | When |
| :--- | :--- |
| IndexError | If a channel is out of range. |

### Signal.plot()

```python
Signal.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    scale: str = 'linear',
    **kwargs: Any,
) -> Axes
```

Plot the waveform, calibrated to pascals when a calibration is set.

Draws each channel's time-domain waveform; with a
`calibration_factor` the amplitude axis is in pascals, otherwise
in digital full-scale units. `scale="db"` draws the magnitude of
each sample as `20 lg(|p| / 20 uPa)` instead, which needs a
calibrated record to mean anything. That is a waveform in decibels
and not a sound pressure level: an `L_p` is defined on a mean
square over a stated time weighting, and
[`time_weighting`](/phonometry/reference/api/filters/weighting/#time_weighting) is what produces one.
Requires matplotlib
(`pip install phonometry[plot]`); returns the
`Axes`.

### Signal.shape

*property*

### Signal.size

*property*

Total number of samples across all channels.

## SignalOrigin

```python
SignalOrigin(
    path: str,
    container: str,
    format_name: str,
    bit_depth: int | None,
    *,
    lossy: bool,
)
```

Where a [`Signal`](/phonometry/reference/api/io/io/#signal) came from, as read from the file itself.

The name is deliberately not `SignalSource`, which
[`SignalSource`](/phonometry/reference/api/simulation/fdtd/#signalsource) already is (an FDTD
excitation driven by an arbitrary sample sequence). The two could share a
spelling now that each is reached through its own package, and the reason
for the distinction is the better one anyway: this is a passive record --
an origin, not a source of sound.

`bit_depth` is the *valid* bits per sample (an EXTENSIBLE container
holding 20 valid bits in 24 reports 20), or `None` where the notion
does not apply (lossy codecs decode to float, not to a bit depth).
`lossy` records that a lossy decoder produced the samples: levels
computed from such a signal are not metrologically defensible, and the
flag keeps that fact attached to the data after the read-time warning
has scrolled away.

## write

```python
write(
    path: str | Path,
    x: Signal | NDArray[np.generic] | list[float],
    fs: int | None = ...,
    *,
    subtype: str | None = ...,
    bext: BroadcastMetadata | str | None = ...,
    dither: Literal['tpdf'],
    rng: np.random.Generator | int | None = ...,
    sidecar: bool = ...,
) -> None

write(
    path: str | Path,
    x: Signal | NDArray[np.generic] | list[float],
    fs: int | None = ...,
    *,
    subtype: str | None = ...,
    bext: BroadcastMetadata | str | None = ...,
    sidecar: bool = ...,
) -> None
```

Write a signal to an audio file, without ever touching its level.

The counterpart of [`phonometry.io.read`](/phonometry/reference/api/io/io/#read) and the export path for
everything the library generates (IEC 60268-1 test tones, sweeps, MLS,
processed measurements). The WAV subtypes are `PCM_16`, `PCM_24`
(packed in-house; scipy cannot), `PCM_32`, `FLOAT` (float32, the
default: exact for anything that came from a container of up to
24 bits) and `DOUBLE` (float64, bit-exact for computed signals).
Files past the 4 GiB RIFF limit promote to RF64 automatically. A
`.flac` destination writes the lossless archive format through the
`[audio]` extra (integer subtypes up to `PCM_24`, the default
there; see `_write_flac`).

What this function will never do, each a documented ecosystem default
that destroys a measurement: normalise (python-acoustics `to_wav`),
resample, or mix channels. Samples that exceed full scale on an
integer subtype are saturated and *reported* -- see
[`ClippingWarning`](/phonometry/reference/api/io/io/#clippingwarning) and the module docstring for the exact
quantisation math, the +1.0 edge, and why the scaling choice cancels
out of calibrated results.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination file; the suffix picks the container: the WAV family (`.wav`, `.wave`, `.bwf`) on the base install, `.flac` with the `[audio]` extra. Lossy suffixes are refused by decided policy. |
| `x` | A [`Signal`](/phonometry/reference/api/io/io/#signal), or an array in the library's channel convention (1-D mono, 2-D `(channels, samples)`). Float data is quantised per `subtype`; `int16`/`int32` arrays are written as a bit-exact pass-through of their codes. |
| `fs` | Sample rate, Hz. Required for bare arrays; forbidden to disagree with a [`Signal`](/phonometry/reference/api/io/io/#signal)'s own rate. |
| `subtype` | Target sample format (see above); `None` picks `FLOAT` for float data and the matching depth for integer data. |
| `bext` | The broadcast provenance chunk (EBU Tech 3285; see [`phonometry.io._bext`](/phonometry/reference/api/io/io/)). `None` carries the [`Signal`](/phonometry/reference/api/io/io/#signal)'s own provenance when it has one and writes no chunk otherwise; `"loudness"` additionally measures the five R 128 fields with the library's BS.1770 implementation on the samples being written (one extra pass, which is why it is opt-in); a [`BroadcastMetadata`](/phonometry/reference/api/io/io/#broadcastmetadata) is written as given. Every written chunk's CodingHistory is extended -- never replaced -- with phonometry's `A=,F=,W=,M=,T=` line. |
| `dither` | `"tpdf"` adds +/-1 LSB triangular-PDF dither before quantising to `PCM_16` (Lipshitz et al. 1992; see the module docstring); `None` (default) quantises plainly. Refused for any other subtype, where it would only add noise. |
| `rng` | Randomness for the dither noise: a seeded `numpy.random.Generator` (or an int seed) makes the written bytes reproducible, which is what a test or a pinned pipeline needs. `None` (default) draws fresh entropy on every write, and that default is deliberate: dither exists to decorrelate the quantisation error, and repeating one noise pattern across multiple writes would correlate the files with each other, undoing exactly what the dither is for. Refused without `dither`, the only thing it seeds. |
| `sidecar` | When true, also write the calibration sidecar ([`phonometry.io._sidecar`](/phonometry/reference/api/io/io/)) beside the file, carrying the [`Signal`](/phonometry/reference/api/io/io/#signal)'s `calibration_factor` and channel labels so [`phonometry.io.read`](/phonometry/reference/api/io/io/#read) recovers the absolute level with no argument at all. Requires a calibrated [`Signal`](/phonometry/reference/api/io/io/#signal): a sidecar without a calibration would be a promise with nothing behind it. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown suffix or subtype, a missing or conflicting `fs`, a dither request outside `PCM_16`, an `rng` without a `dither` for it to seed, bext metadata that violates Tech 3285 (oversize field, version too old for a carried UMID or loudness), or a sidecar request without a calibrated [`Signal`](/phonometry/reference/api/io/io/#signal). |

## write_catalogue

```python
write_catalogue(
    rows: Mapping[str, CatalogueRow],
    path: str | os.PathLike[str],
    *,
    catalogue: str | None = None,
    about: str | None = None,
    provenance: Provenance | None = None,
    overwrite: bool = False,
) -> tuple[Path, ...]
```

Write rows as a catalogue file that reads back into the same rows.

The document [`read_catalogue`](/phonometry/reference/api/io/io/#read_catalogue) reads, written so that reading it
gives rows equal to these, field for field: the cells each row's page
prints, as [`CatalogueRow.printed_fields`](/phonometry/reference/api/io/io/#cataloguerowprinted_fields) gives them, and never a
derived value, which the reader works out again. A value converted from
another unit is written in that unit, under the name that carries it,
when that reads back to the same float, and otherwise in the field's own
unit with its `converted` record beside it, as the degrees Fahrenheit
and the psi of a damping table are.

A [`Catalogue`](/phonometry/reference/api/io/io/#catalogue) brings its name, its `about`, its provenance, its
legends and its `x-...` columns. A table of the library's own (a
`PUBLISHED_*` catalogue filtered by `row.table`) needs a *catalogue*
name that is not of the packaged form, and takes the table's `about`
and legends, with a provenance that cites the publication as the rows do
and records the day of the export as the day it was consulted: the
edition is in the citation already, and the copy consulted is the
library's on that day. Pass *provenance* for a file that has to come out
the same every day.

The file is written beside its final name and renamed into place, so a
reader never finds half of it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `rows` | A [`Catalogue`](/phonometry/reference/api/io/io/#catalogue), or a mapping of rows of one class. |
| `path` | Where to write, a name ending in `.json` (in any case). |
| `catalogue` | The catalogue's name. Required for a table of the library's own, and for rows of yours that do not share one. |
| `about` | What the document is; required when the rows bring none. |
| `provenance` | The document the rows were read from, in place of the one they bring. |
| `overwrite` | Replace a file already at *path*. |

**Returns:** The paths written.

**Raises**

| Exception | When |
| :--- | :--- |
| CatalogueError | for no rows, rows from more than one table or document, a key a file cannot hold, or a name that is reserved or malformed. |
| TypeError | for rows that are not catalogue rows of one class (fluid states among them), or a *catalogue* or *about* the rows need and do not bring. |
| ValueError | for a name that does not end in `.json`. |
| FileExistsError | for a file at *path* without *overwrite*, and for a symbolic link at *path*. |

## write_sidecar

```python
write_sidecar(
    audio_path: str | Path,
    calibration_factor: float,
    *,
    reference_spl: float | None = None,
    calibrator_frequency: float | None = None,
    calibrator_model: str | None = None,
    channel_labels: tuple[str, ...] | None = None,
) -> Path
```

Write the calibration sidecar beside an audio file.

Serialises schema v1 with every key present (the module docstring's
table); an existing sidecar is replaced, which is the update semantics
a recalibration wants. The audio file itself is never touched.

**Parameters**

| Name | Description |
| :--- | :--- |
| `audio_path` | The audio file the sidecar belongs to (it need not exist yet; writing the sidecar first is fine). |
| `calibration_factor` | Digital-to-pascal multiplier (required, finite, positive). |
| `reference_spl` | The calibrator's known SPL, dB (e.g. 94.0). |
| `calibrator_frequency` | The calibrator tone's nominal frequency, Hz (e.g. 1000.0). |
| `calibrator_model` | Free-text calibrator identification. |
| `channel_labels` | One label per channel of the audio file. |

**Returns:** The path the sidecar was written to.

← [Documentation index](../README.md)

# Your own catalogues

The library publishes the tables of its books and standards, and nothing a
manufacturer prints. A data sheet is revised under the same title without
notice, its terms rarely allow copying it, and the value a project needs is
the one on the sheet the project was specified against, not the one on
today's revision. So the data sheets, declarations of performance, test
reports and measurements of your own live in a catalogue file of yours, and
`phonometry.io` reads that file into rows of the same classes every
`PUBLISHED_*` catalogue hands out. A porous core from your sheet goes into
the porous models as a porous material from a book does, a spectrum from
your test report goes into a room model, and every lookup by name searches
your catalogue, the published one or both at once.

The rows are yours and stay in your objects: the library keeps no copy,
opens no link a file names and sends nothing anywhere. For the same reason a
manufacturer's table pasted into an issue or a pull request is never merged
into the library.

## Start from a published table

The quickest way to see the shape of a file is to write one. `write_catalogue`
writes any published table in the form `read_catalogue` reads, as a template
to copy and edit: here the foam of Allard & Atalla's Table 13.1.

```python
import json
import pathlib

from phonometry import io, materials

allard = {
    key: row
    for key, row in materials.PUBLISHED_POROUS.items()
    if row.table == "allard-2009-table-13-1"
}
written = io.write_catalogue(allard, "template.json", catalogue="template-allard")
print([path.name for path in written])   # ['template.json']

template = json.loads(pathlib.Path("template.json").read_text(encoding="utf-8"))
print(list(template))
# ['schema', 'schema_version', 'catalogue', 'row_type', 'about', 'provenance',
#  'phonometry_version', 'rows']
print(template["provenance"]["kind"])    # publication
print(template["rows"][0]["key"], template["rows"][0]["flow_resistivity_pa_s_m2"])
# foam 12569.0
```

A table of rows of one class goes out whole, with the book as its
provenance and the day of the export as the day it was consulted. What the
library works out from the printed cells (here the shear modulus, from the
Young's modulus and the Poisson ratio) is never written: it is worked out
again when the file is read. A file already at the path is refused with
`FileExistsError` unless you pass `overwrite=True`.

## The document

A catalogue file is one JSON object, UTF-8, with a closed set of keys at the
top:

| Key | What it holds |
|---|---|
| `schema`, `schema_version` | `"phonometry-catalogue"` and `1`. A newer version is refused with "upgrade phonometry". |
| `catalogue` | The catalogue's name, the first half of every key: up to 64 of `a-z`, `0-9`, `.`, `_` and `-`. |
| `row_type` | The name of the row class. It is compared with the class you pass and never imported. |
| `about` | What the document is, how you read it and what units it prints. |
| `provenance` | The document: its `kind`, its title in `document`, its `version` (or `null` when it prints none) and the day you `consulted` it, as `YYYY-MM-DD`, are required. The `kind` is one of `io.PROVENANCE_KINDS`: `datasheet`, `declaration_of_performance`, `test_report`, `measurement`, `calculation`, `publication` or `other`. |
| `basis` | Optional: what the document says every value is, unless a row says otherwise. |
| `conventions` | Optional: the notes and legends the document prints for the whole table. |
| `phonometry_version` | Optional: the version of the library that wrote the file, which `write_catalogue` fills in. It is never read. |
| `rows` | The rows, each with a `key` of its own and a `name`. |

Here is a fictitious data sheet with two rows. The first is the airflow
resistivity the sheet declares under its CE marking, as a lower bound; the
second is the laboratory characterisation page 3 quotes, from its own
report.

```python
panel_40 = """{
  "schema": "phonometry-catalogue",
  "schema_version": 1,
  "catalogue": "panel-40",
  "row_type": "PorousMaterial",
  "about": "Core of the Panel 40 absorber as its data sheet gives it. Page 2 declares the airflow resistivity class under CE marking; page 3 quotes the laboratory characterisation of a 40 mm specimen.",
  "provenance": {
    "kind": "datasheet",
    "document": "Panel 40 technical data sheet",
    "publisher": "Example Acoustics Ltd",
    "version": "Rev. 4",
    "issued": "2026-03",
    "consulted": "2026-09-23",
    "page": "2"
  },
  "basis": "declared",
  "rows": [
    {
      "key": "core-declared",
      "name": "Panel 40 core",
      "variant": "as declared",
      "thickness_mm": 40,
      "frame_density_kg_m3": 40,
      "ranges": {"flow_resistivity_kpa_s_m2": [5, null]},
      "bounded_below": ["flow_resistivity_kpa_s_m2"],
      "note": "the sheet prints the designation code AFr5"
    },
    {
      "key": "core-lab",
      "name": "Panel 40 core",
      "variant": "40 mm specimen",
      "provenance": {
        "page": "3",
        "printed_table": "Table 2",
        "laboratory": "Example Lab",
        "report": "26-014",
        "test_date": "2025-11-04",
        "test_standard": "ISO 9053-1:2018"
      },
      "basis": {"row": "measured", "poisson_ratio": "estimated"},
      "flow_resistivity_pa_s_m2": 12500,
      "uncertainty": {"flow_resistivity_pa_s_m2": 900},
      "porosity": 0.97,
      "tortuosity": 1.02,
      "approximate": ["tortuosity"],
      "viscous_length_um": 95,
      "thermal_length_um": 190,
      "frame_density_kg_m3": 40,
      "thickness_mm": 40,
      "youngs_modulus_pa": 140000,
      "poisson_ratio": 0.0,
      "unquantified": {"structural_loss_factor": "n.m."},
      "x-product-code": "P40-C"
    }
  ]
}"""
pathlib.Path("panel-40.json").write_text(panel_40, encoding="utf-8")

mine = io.read_catalogue("panel-40.json", row_type=materials.PorousMaterial)
print(list(mine))   # ['panel-40/core-declared', 'panel-40/core-lab']

declared = mine["panel-40/core-declared"]
lab = mine["panel-40/core-lab"]
print(lab.source)
# Panel 40 technical data sheet (Example Acoustics Ltd), Rev. 4, p. 3, Table 2;
# report 26-014 (Example Lab); consulted 2026-09-23
print(lab.basis_of("porosity"), lab.basis_of("poisson_ratio"))   # measured estimated
print(declared.basis_of("frame_density_kg_m3"))                  # declared
print(declared.ranges, declared.converted)
# {'flow_resistivity_pa_s_m2': (5000.0, None)}
# {'flow_resistivity_pa_s_m2': ('5', 'kPa s/m2')}
print(mine.extras["panel-40/core-lab"]["x-product-code"])       # P40-C
```

Every key is `"<catalogue>/<key>"`, the form every published catalogue uses,
and every row's `table` is the catalogue's name. A catalogue's name can never
take the form of a packaged table's, a four-digit year followed by a word
(`allard-2009-table-13-1`), so a key of yours and a key of the library never
meet, today or after an update adds a table: `acme-2026-rev4` is refused and
`acme-rev4-2026` is not.

A row may narrow the document's provenance to its own page, table,
laboratory, accreditation, report, test date and standard, as `core-lab`
does, and a standard given for one field (`field_test_standards`) is added to
the document's. A different document is a different file: a row cannot
change the document, its kind or its version. For every kind but a
`publication`, which is cited as its document is, the row's `source` names
the document, its publisher and its version, the page and the table, the
report and the laboratory, and the day it was consulted; the accreditation,
the test date and the standards stay in `row.provenance`. A refusal names the
document by its kind: "the datasheet", "the declaration of performance", "the
test report", "the measurement record" for a `measurement`, "the calculation
note" for a `calculation`, and "the source" for a `publication` or `other`.

Columns of your own go under a name that starts with `x-`: they are kept, as
text, in `Catalogue.extras` and take part in no calculation. A row never
writes `derived`, `table`, `source` or `estimated`: the first three are the
library's to write, and an estimate is a `basis`.

## When the file is wrong

Every problem of form in a file is reported at once, in one
`io.CatalogueError`, each problem an `io.CatalogueIssue` with the file, its
place as a JSON pointer, the row and the field. Here the porosity is written
with a decimal comma and the thickness in inches, a unit the reader does not
convert:

```python
broken = panel_40.replace('"porosity": 0.97', '"porosity": "0,97"')
broken = broken.replace('"thickness_mm": 40,\n      "youngs', '"thickness_inch": 1.6,\n      "youngs')
try:
    io.parse_catalogue(broken, row_type=materials.PorousMaterial, label="panel-40.json")
except io.CatalogueError as error:
    for issue in error.issues:
        print(issue)
# panel-40.json: /rows/1/porosity (row 'core-lab'): expected a number, got the
#   text '0,97'; JSON numbers use a decimal point
# panel-40.json: /rows/1/thickness_inch (row 'core-lab'): 'inch' is not a unit
#   this reader converts; write thickness_mm (mm), thickness_cm (cm),
#   thickness_m (m) or thickness_um (µm)
```

`parse_catalogue` reads the same from text or from a dictionary already in
memory, with `label` naming the document in every issue. A misspelt field is
answered with the field it is most like; a row that is written correctly but
breaks the contract every row keeps (a negative density, a porosity above 1,
a value beside a word that says there is none) is reported with the first
rule it breaks. The reader refuses a `NaN` or an `Infinity`, a name written
twice in one object, a control character or a mark that reorders text, a
file over 16 MiB (checked before a byte of it is read), more than
50 000 rows and nesting past six levels.

What is only worth a second look is not an error. A value whose basis is
`measured` with neither a report nor a laboratory named for it, or a word in
place of a number long enough to be a sentence, is kept as the file writes
it, listed in `Catalogue.notes`, and announced once with an
`io.CatalogueWarning`. A note never changes a row.

## Using the rows

A row read from a file is the same class, built the same way, as a published
one: the same methods take it, and the same functions accept what they
return.

### In the models

`printed()` gives one number the document prints, or refuses with what the
document has there instead. That is the way to hand a cell to any function
that takes a float. `PorousMaterial.medium()` reads its five parameters the
same way, so the laboratory row goes into the transfer-matrix model and the
declared row is refused in the sheet's own terms:

```python
import numpy as np

print(lab.printed("flow_resistivity_pa_s_m2"))   # 12500.0

frequencies = np.array([250.0, 500.0, 1000.0, 2000.0])
core = materials.PorousLayer(thickness=0.040, medium=lab.medium(frequencies))
print(materials.layered_absorber(frequencies, [core]).absorption.round(2))
# [0.15 0.4  0.73 0.98]

try:
    declared.medium(frequencies)
except ValueError as error:
    print(error)
# 'Panel 40 core' has no flow_resistivity_pa_s_m2, which 'johnson_champoux_allard'
# needs: the datasheet prints a lower bound of 5 kPa s/m2 (5000 Pa s/m2) and no
# value (Panel 40 technical data sheet (Example Acoustics Ltd), Rev. 4, p. 2;
# consulted 2026-09-23).
```

The refusal quotes the figure and the unit the sheet prints, then the value
the row holds: a lower bound of AFr5 is not a flow resistivity of
5000 Pa·s/m², and nothing here pretends it is.

### Band by band, into a room model

A row that prints one value per band reads at the frequencies a model asks
for with `values_at()`, which refuses a band the document does not print
rather than reading it as zero. The functions that take their coefficients by
position, such as `room.sabine_reverberation_time`, get an array whose every
entry was printed:

```python
from phonometry import room

tiles = io.parse_catalogue(
    {
        "schema": "phonometry-catalogue",
        "schema_version": 1,
        "catalogue": "ceiling-tiles",
        "row_type": "AbsorptionSpectrum",
        "about": "Octave-band Sabine coefficients a fictitious data sheet prints.",
        "provenance": {
            "kind": "datasheet",
            "document": "Example tile data sheet",
            "publisher": "Example Acoustics Ltd",
            "version": "Rev. 1",
            "consulted": "2026-09-25",
            "laboratory": "Example Lab",
            "report": "26-031",
            "test_standard": "ASTM C423-17",
        },
        "basis": "measured",
        "rows": [
            {
                "key": "tile-e400",
                "name": "Example ceiling tile",
                "mounting": "E400",
                "absorption_coefficient_125": 0.45,
                "absorption_coefficient_250": 0.62,
                "absorption_coefficient_500": 0.78,
                "absorption_coefficient_1000": 0.90,
                "absorption_coefficient_2000": 0.94,
                "absorption_coefficient_4000": 0.91,
            }
        ],
    },
    row_type=materials.AbsorptionSpectrum,
)
tile = tiles["ceiling-tiles/tile-e400"]
bands = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
t60 = room.sabine_reverberation_time(180.0, [(60.0, tile.values_at(bands)), (190.0, 0.04)])
print(t60.round(2))   # [0.84 0.65 0.53 0.47 0.45 0.47]

try:
    tile.values_at([63.0, 125.0])
except ValueError as error:
    print(error)
# 'Example ceiling tile' has no absorption_coefficient_63, which 'the 63 Hz band'
# needs: the datasheet does not give it, and it does not follow from the cells
# that it does (Example tile data sheet (Example Acoustics Ltd), Rev. 1;
# report 26-031 (Example Lab); consulted 2026-09-25).
```

### The plateau method

`building.plateau_transmission_loss` takes a `PlateauMaterial` row as its
`material`, one of the book's or one of yours, and reads its three numbers
through `printed()`. A number you pass explicitly replaces the row's, which
is then not read at all.

```python
from phonometry import building, solids

boards = io.parse_catalogue(
    {
        "schema": "phonometry-catalogue",
        "schema_version": 1,
        "catalogue": "boards",
        "row_type": "PlateauMaterial",
        "about": "Plateau-method constants of a fictitious board, as its data sheet prints them.",
        "provenance": {
            "kind": "datasheet",
            "document": "Example board data sheet",
            "version": "Rev. 2",
            "consulted": "2026-09-25",
        },
        "rows": [
            {
                "key": "board",
                "name": "Example board",
                "surface_density_per_mm_kg_m2": 0.9,
                "coincidence_height_db": 28,
                "plateau_frequency_ratio": 7,
            }
        ],
    },
    row_type=solids.PlateauMaterial,
)
board = boards["boards/board"]
tl = building.plateau_transmission_loss(bands, material=board, thickness_mm=12.5)
print(round(tl.plateau_start), round(tl.plateau_end))   # 522 3656
print(tl.transmission_loss.round(1))   # [15.6 21.6 27.6 28.  28.  29.3]
```

### A floating floor: s' and s't

A resilient layer's data sheet prints one of two different quantities. The
dynamic stiffness $s'$ of the installed layer is what the natural frequency
of a floating floor takes; the apparent dynamic stiffness $s'_\mathrm{t}$ is
what EN 29052-1 measures on a test specimen, and it becomes $s'$ only through
the lateral airflow resistivity of clause 8.2. `ResilientLayer` keeps them in
two fields, `dynamic_stiffness_n_m3` and `apparent_dynamic_stiffness_n_m3`,
and a declared "s' ≤ 9 MN/m³" is a bound, not a stiffness:

```python
layers = io.parse_catalogue(
    {
        "schema": "phonometry-catalogue",
        "schema_version": 1,
        "catalogue": "underlays",
        "row_type": "ResilientLayer",
        "about": "Two underlays of a fictitious data sheet, as it prints them.",
        "provenance": {
            "kind": "datasheet",
            "document": "Example underlay data sheet",
            "publisher": "Example Acoustics Ltd",
            "version": None,
            "consulted": "2026-09-25",
        },
        "basis": "declared",
        "rows": [
            {
                "key": "declared",
                "name": "Underlay 8",
                "thickness_mm": 8,
                "ranges": {"dynamic_stiffness_mn_m3": [None, 9]},
                "bounded_above": ["dynamic_stiffness_mn_m3"],
            },
            {
                "key": "tested",
                "name": "Underlay 20",
                "thickness_mm": 20,
                "apparent_dynamic_stiffness_mn_m3": 7,
                "basis": {"row": "measured"},
                "provenance": {"laboratory": "Example Lab", "report": "26-044"},
            },
        ],
    },
    row_type=materials.ResilientLayer,
)
try:
    layers["underlays/declared"].natural_frequency(mass_per_area_kg_m2=100.0)
except ValueError as error:
    print(error)
# 'Underlay 8' has no dynamic_stiffness_n_m3, which 'the natural frequency of
# EN 29052-1 Formula 2' needs: the datasheet prints an upper bound of 9 MN/m3
# (9000000 N/m3) and no value (Example underlay data sheet (Example Acoustics
# Ltd), no version printed; consulted 2026-09-25).

tested = layers["underlays/tested"]
f0 = tested.natural_frequency(mass_per_area_kg_m2=100.0, airflow_resistivity_pa_s_m2=150_000.0)
print(round(float(f0), 1))   # 42.1
```

The tested layer gives only $s'_\mathrm{t}$, so its natural frequency needs
the lateral airflow resistivity $r$ of clause 8.2: at or above
100 kPa·s/m², $s'$ is $s'_\mathrm{t}$, and below it the call needs the
enclosed-gas stiffness $s'_\mathrm{a}$ of Formula 7 as well, which
`gas_stiffness_n_m3` passes. Without $r$ the call is refused with that
explanation rather than taking one quantity for the other.

### Searching your catalogue and the published ones

Every `*_named` lookup takes `catalogue=`, the rows to search in place of its
own `PUBLISHED_*`. `PUBLISHED_POROUS | mine` joins the two into one read-only
mapping that refuses a key both hold, so one search answers from both:

```python
both = materials.PUBLISHED_POROUS | mine
for row in materials.porous_materials_named("panel 40 core", catalogue=both):
    print(row.table, row.variant)
# panel-40 as declared
# panel-40 40 mm specimen
print(len(materials.porous_materials_named("Foam", catalogue=both)))   # 5
```

Each lookup keeps its own way of matching a name, answers every match in the
order the catalogue holds them and never picks one. It matches without regard
to case or to how an accented letter is stored: a name pasted from a document
that stores "é" as "e" followed by a combining accent finds the row typed with
"é", and the other way round. A row of another class in the catalogue is
refused with `TypeError`, naming its key.

## Writing what the document prints

A document prints more than numbers, and a file writes each thing as what it
is, in the same hedges the published tables use. The subject of each
sentence below is the document's kind: "the datasheet", "the test report".

| The document prints | Written in the file as | `why_missing` answers |
|---|---|---|
| a number | the field, in its unit or another of the same kind | nothing: the value is there |
| nothing | the field left out, or `null` | "the datasheet does not give it, and it does not follow from the cells that it does" |
| `~0.85` | the value, and the field in `"approximate"` | nothing |
| `≤ 30` or `< 30` | `"ranges": {"f": [null, 30]}` and `"bounded_above": ["f"]` | "the datasheet prints an upper bound of 30 and no value" |
| `≥ 5` or `> 5` | `"ranges": {"f": [5, null]}` and `"bounded_below": ["f"]` | "... a lower bound of 5 and no value" |
| `0.30 to 0.50` | `"ranges": {"f": [0.30, 0.50]}` | "the datasheet prints 0.3 to 0.5 and no value" |
| several readings and no single value | `"reported": {"f": [0.30, 0.35, [0.30, 0.40]]}` | "the datasheet lists 0.3, 0.35, 0.3 to 0.4 and no single value" |
| `0.85 ± 0.05` | the value, and `"uncertainty": {"f": 0.05}` | nothing |
| a word or a code where the number goes | `"unquantified": {"f": "AFr5"}` | "the datasheet prints “AFr5” where the number would be" |
| a value you know is wrong | `"misprinted": {"f": "why"}`, with no value | your reason, as you wrote it |
| a value the arithmetic reaches but should not | `"not_derivable": {"f": "why"}` | your reason |
| a blank cell the document gives by reference to another row | the value, and `"carried": {"f": "from the row above"}` | nothing |
| a figure in a unit no family holds | the value in the field's own unit, and `"converted": {"f": ["3e5", "psi"]}` | nothing, and a bound quotes the figure first |
| a credit to a laboratory or an author | `"attributed_to": {"f": "..."}`, or `"row"`, or `"table"` | not asked |
| a yes or a no | `true` or `false`, in a field that holds one | not asked |

A bound declared under a CE marking, `AFr5` for an airflow resistivity of at
least 5 kPa·s/m², is written as the bound, with the code in `note`, as
`core-declared` does. Written as the number 5, it would claim a measurement
the sheet does not make.

## Units

A cell may be written in the unit its field is named for, or in another unit
of the same kind, under the same name with the other unit's suffix:
`thickness_cm` for `thickness_mm`. The figure is converted on the digits the
file writes, with the exact factor, and rounded once, so 0.067 GPa is
67 000 000 Pa, which the product of two floats is not. `converted` keeps the
figure and the unit exactly as the file writes them.

| Kind | Suffixes |
|---|---|
| Length | `_um`, `_mm`, `_cm`, `_m` |
| Mass per area | `_g_m2`, `_kg_m2` |
| Density | `_g_cm3`, `_kg_m3` |
| Pressure and modulus | `_pa`, `_kpa`, `_mpa` (megapascal), `_n_mm2`, `_gpa` |
| Stiffness per area | `_n_m3`, `_mn_m3` |
| Flow resistivity | `_pa_s_m2`, `_kpa_s_m2` |
| Temperature | `_c`, `_k`, moved by its offset in a value, a range and a reading, and by the factor alone in a plus-or-minus |
| Absorption area | `_m2`, `_ft2`, `_ft2_per_1000_ft3`, only in `AbsorptionAreaSpectrum`, and the last only with `per` beside it |

The unit is read by the longest match against every unit the library's fields
use, so a compound unit is never mistaken for a length: a specific flow
resistance in Pa·s/m or a rate per metre takes no other unit, and a name two
fields of one kind could take is refused as ambiguous. A unit the table does
not hold is refused with the spellings the field takes. Every number of one
cell is written in one unit.

## Which row class holds which quantity

A data sheet and a book can print quantities that look alike and are not.
The row classes keep them apart, and the file cannot keep you from writing
one into another's field, so read this before choosing a `row_type`.

- `AbsorptionSpectrum` holds Sabine absorption coefficients in octave bands
  from 63 Hz to 8 kHz, as a book's table prints them or as a data sheet
  prints the result of a reverberation-room test in octaves. The practical
  sound absorption coefficient $\alpha_\mathrm{p}$ of ISO 11654 is not one of
  them: it is a rating, rounded to steps of 0.05 and capped at 1.00, and a
  European data sheet's octave row is usually that. No row class of this
  library holds $\alpha_\mathrm{p}$, nor a one-third-octave
  $\alpha_\mathrm{s}$; do not write either into `AbsorptionSpectrum`.
- `TransmissionLossSpectrum` holds the transmission loss of a construction
  as a book compiles it, in octave bands, from tests the book seldom names:
  Bies qualifies his values as field incidence, ASHRAE's rows come from
  laboratory tests, and Rossing names no source. The sound reduction index
  $R$ of a test report under ISO 10140-2 is measured in one-third-octave
  bands on one product's specimen, in a laboratory where the sound
  transmitted by flanking paths has been shown to be negligible, and it is
  rated with ISO 717-1. It is a different record, and no row class holds it;
  do not write it into `TransmissionLossSpectrum`.
- `ResilientLayer` holds $s'$ in `dynamic_stiffness_n_m3` and
  $s'_\mathrm{t}$ in `apparent_dynamic_stiffness_n_m3`. A test report under
  EN 29052-1 prints $s'_\mathrm{t}$ and, when it can, $s'$; a data sheet
  often prints only "s'". Write each in its own field.
- `PorousMaterial` holds the parameters of a porous frame, `PlateauMaterial`
  the three numbers of the plateau method, `SolidMaterial` the elastic
  constants of a solid. The published catalogues page lists every class with
  its columns.

## What a value is: basis, converted and carried

`basis` says what the document claims a value is, one of
`io.CATALOGUE_BASES`, and `basis_of(field)` answers it for any cell:

| Word | Meaning |
|---|---|
| `measured` | a test result the document gives |
| `declared` | a value, a bound or a class declared under a product standard or a CE marking |
| `calculated` | a figure the document worked out itself, by a standard's model, a program or a formula |
| `estimated` | the document's own estimate |
| `extended` | the result of an extended application of a test |

A cell with no word is one the document does not qualify, which is the honest
answer for most data sheets. The document's `basis` is every row's, a row's
`"row"` entry is every cell's, and a cell's own entry wins over both.

`basis` is what the document says; `derived` is what this library worked
out, from the printed cells, when it built the row. They are independent:
the shear modulus of `core-lab` is derived, and its `derived` text names the
bases it rests on, a measured Young's modulus and an estimated Poisson ratio.
`converted` keeps the figure and the unit of a value converted from another
unit, and `carried` says where a document gives a blank cell from. A file may
write `converted` and `carried` beside a value; it never writes `derived`.

## Editing a row

A row is frozen. To change a cell, take the cells the document prints with
`printed_fields()`, change one and build the row again with `from_printed`,
which works out again what follows from them. `dataclasses.replace` copies
the derived values as they were, beside a cell they no longer follow from:

```python
cells = lab.printed_fields()
cells["youngs_modulus_pa"] = 200_000.0
edited = materials.PorousMaterial.from_printed(**cells)
print(lab.shear_modulus_pa, edited.shear_modulus_pa)   # 70000.0 100000.0
```

## A row class of your own

A quantity no class of this library holds can still live in a catalogue
file, in a row class of your own: a frozen, keyword-only dataclass built on
`io.CatalogueRow`, with every field annotated `float | None`, `int | None`,
`bool`, `str`, `frozenset[str]` or a `Mapping` of those. The reader reads it
like any other, and the other units of a kind apply to your fields too when
the name leaves no doubt, except a temperature, which has to be written in
the unit its field is named for:

```python
import dataclasses


@dataclasses.dataclass(frozen=True, kw_only=True)
class Plasterboard(io.CatalogueRow):
    surface_density_kg_m2: float | None = None
    reaction_to_fire: str = ""


boards_of_mine = io.parse_catalogue(
    {
        "schema": "phonometry-catalogue",
        "schema_version": 1,
        "catalogue": "plasterboards",
        "row_type": "Plasterboard",
        "about": "One board of a fictitious data sheet.",
        "provenance": {
            "kind": "datasheet",
            "document": "Example board range",
            "version": None,
            "consulted": "2026-09-25",
        },
        "rows": [
            {
                "key": "board-12",
                "name": "Board 12.5",
                "surface_density_g_m2": 8600,
                "reaction_to_fire": "A2-s1,d0",
            }
        ],
    },
    row_type=Plasterboard,
)
row = boards_of_mine["plasterboards/board-12"]
print(row.surface_density_kg_m2, row.converted)
# 8.6 {'surface_density_kg_m2': ('8600', 'g/m2')}
```

Leave `slots=True` out of such a class: on Python 3.13 a method of it that
calls `super()` without arguments fails, which is how a `__post_init__` of
your own reaches the row contract. A bare `float` or `int`
annotation is refused with `TypeError` the first time the class is built,
because every cell of a row may be missing. A class built on `BandedRow` is
not supported: its bands are declared in private class variables.

## What never happens

The reader and the rows hold what the document prints and nothing else.

- No band a document does not print is extrapolated, interpolated or filled
  from its neighbours, and none is read as zero.
- Nothing is clipped or rounded: a coefficient of 1.05 stays 1.05, and a
  rating is never moved to a grid.
- No figure is guessed from its size, and no unit is read from inside a cell.
- Nothing is uploaded, cached or copied, and no link a file names is opened.
- Two rows under the same name are both kept and both answered, and no
  lookup chooses between them for you.
- Nothing the file names is imported: only the JSON reader of the standard
  library reads it, and the class name it writes is only compared with the
  class you pass.

## What this guide covers

**Covered.** Reading a catalogue of your own from a JSON file (`io.read_catalogue`) or
from text or a mapping (`io.parse_catalogue`) into the rows every published
catalogue hands out, with its `io.Provenance`, its notes and every problem of
form reported at once with a JSON pointer; writing rows, a published table
among them, back to a file (`io.write_catalogue`); searching yours and the
published ones with every `*_named` lookup; and handing the rows to the
porous models, a room model, the plateau method and a floating floor.

**Not covered.** The reader takes JSON only: a spreadsheet is turned into the document first,
for example as a dictionary handed to `parse_catalogue`. No row class holds
a data sheet's practical absorption coefficient $\alpha_\mathrm{p}$, its
one-third-octave $\alpha_\mathrm{s}$ or a laboratory sound reduction index
$R$, and no rating is recomputed from a spectrum a file holds. No
manufacturer's data ships with the library, and a table pasted into an issue
or a pull request is never merged.

## See also

- [Files](index.md): what the file layer of the library reads and writes, and why.
- [Published catalogues](https://jmrplens.github.io/phonometry/reference/catalogues/): every table the library has read from a page, the same row classes with the book's cells.
- [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md): the models a `PorousMaterial` row goes into.
- [Dynamic stiffness of resilient materials](../materials/resilient/dynamic-stiffness.md): $s'$, $s'_\mathrm{t}$ and clause 8.2 in full.
- [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md): the plateau method a `PlateauMaterial` row draws.
- API reference: [`phonometry.io`](https://jmrplens.github.io/phonometry/reference/api/io/io/).

## References

- Internet Engineering Task Force. (2017). *The JavaScript Object Notation (JSON) Data Interchange Format* (RFC 8259).
  [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc8259).
  The text a catalogue file is. The reader holds a file to it strictly: a NaN or an Infinity, which only some readers accept, and a name written twice in one object, whose meaning RFC 8259 leaves to the reader, are refused.
- Internet Engineering Task Force. (2013). *JavaScript Object Notation (JSON) Pointer* (RFC 6901).
  [rfc-editor.org](https://www.rfc-editor.org/rfc/rfc6901).
  How every problem in a file is located: /rows/1/porosity is the porosity of the second row.
- International Organization for Standardization. (1997). *Acoustics — Sound absorbers for use in buildings — Rating of sound absorption* (ISO 11654:1997).
  [iso.org catalogue](https://www.iso.org/standard/19583.html).
  The practical sound absorption coefficient a European data sheet prints, rounded to steps of 0.05 and capped at 1.00: a rating of a reverberation-room measurement and not a Sabine coefficient, which is why it has no place in AbsorptionSpectrum.
- International Organization for Standardization. (2010). *Acoustics — Laboratory measurement of sound insulation of building elements — Part 2: Measurement of airborne sound insulation* (ISO 10140-2:2010).
  [iso.org catalogue](https://www.iso.org/standard/42088.html).
  The laboratory sound reduction index R a data sheet of a wall or a door prints: one product's specimen, measured in one-third-octave bands in a facility where flanking transmission is negligible and rated with ISO 717-1. It is not the transmission loss a book compiles, which TransmissionLossSpectrum holds.
- International Organization for Standardization. (1989). *Acoustics — Determination of dynamic stiffness — Part 1: Materials used under floating floors in dwellings* (EN 29052-1:1992 (ISO 9052-1:1989)).
  [iso.org catalogue](https://www.iso.org/standard/16620.html).
  The dynamic stiffness s' of an installed layer and the apparent dynamic stiffness s't of a test specimen, two fields of ResilientLayer, and clause 8.2, which turns the second into the first with the lateral airflow resistivity.

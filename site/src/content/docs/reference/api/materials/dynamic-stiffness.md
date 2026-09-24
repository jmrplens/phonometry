---
title: "materials.resilient.dynamic_stiffness"
description: "Dynamic stiffness of resilient materials under floating floors (EN 29052-1:1992)."
sidebar:
  label: "dynamic_stiffness"
---

Dynamic stiffness of resilient materials under floating floors (EN 29052-1:1992).

A floating floor is a heavy floating slab resting on a resilient layer; the
combination is a mass-spring system whose natural frequency governs the impact
and airborne improvement of the floor. EN 29052-1 (identical to ISO 9052-1:1989)
measures the **dynamic stiffness per unit area** `s'` of the resilient layer
from the resonance of a standard load plate on a 200 mm x 200 mm specimen.

The dynamic stiffness per unit area is the ratio of a dynamic force per area to
the resulting change in thickness (Formula 1):

$$
s' = \frac{F/S}{\Delta d} \qquad [\text{N/m}^3]
$$

The resiliently supported floor is a mass-spring resonator; its natural
frequency (Formula 2) and, in the laboratory arrangement, the measured resonant
frequency (Formula 3) are:

$$
f_0 = \frac{1}{2\pi} \sqrt{\frac{s'}{m'}} \qquad \text{(installed floor)}
$$

$$
f_\mathrm{r} = \frac{1}{2\pi} \sqrt{\frac{s'_\mathrm{t}}{m'_\mathrm{t}}} \qquad \text{(test arrangement)}
$$

so the *apparent* dynamic stiffness follows from the resonance (Formula 4):

$$
s'_\mathrm{t} = 4 \pi^2 m'_\mathrm{t} f_\mathrm{r}^2
$$

With an air-permeable resilient material the enclosed gas adds a parallel
stiffness (Formula 7), from the isothermal compression of the pore air:

$$
s'_\mathrm{a} = \frac{p_0}{d\,\epsilon}
$$

($s'_\mathrm{a} = 111/d$ MN/m3 for $p_0 = 0.1$ MPa,
$\epsilon = 0.9$ and `d` in mm, the standard's worked NOTE). The
dynamic stiffness of the installed material is then obtained by airflow
resistivity `r` (clause 8.2):

$$
s' = s'_\mathrm{t}, \qquad r \ge 100~\text{kPa}\cdot\text{s/m}^2 \tag{Formula 5}
$$

$$
s' = s'_\mathrm{t} + s'_\mathrm{a}, \qquad 10 \le r < 100~\text{kPa}\cdot\text{s/m}^2 \tag{Formula 6}
$$

For $r < 10$ kPa.s/m2, `s'a` follows Formula 7; the method only
applies when $s'_\mathrm{t} \gg s'_\mathrm{a}$, otherwise `s'` cannot be resolved.

This module is the resilient-layer characterisation feeding the floating-floor
term of the EN 12354-2 impact model
([`phonometry.building.prediction.simplified_model`](/phonometry/reference/api/building/simplified-model/)). It does **not** feed
ISO 16251-1 ([`phonometry.building.measurement.floor_covering_improvement`](/phonometry/reference/api/building/floor-covering-improvement/)), whose
scope is limited to soft, locally-reacting floor coverings; floating floors
are explicitly excluded there.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## apparent_dynamic_stiffness

```python
apparent_dynamic_stiffness(
    resonant_frequency_hz: ArrayLike,
    total_mass_per_area_kg_m2: float,
) -> np.ndarray | float
```

Apparent dynamic stiffness per unit area `s't` (Formula 4).

Inverts the test resonance $f_\mathrm{r} = (1/2\pi)\sqrt{s'_\mathrm{t}/m'_\mathrm{t}}$ to
$s'_\mathrm{t} = 4 \pi^2 m'_\mathrm{t} f_\mathrm{r}^2$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `resonant_frequency_hz` | Extrapolated resonant frequency `fr`, in hertz (scalar or array). |
| `total_mass_per_area_kg_m2` | Total mass per unit area used during the test `m't`, in kg/m2 (the load plate plus fittings over the 0,04 m2 specimen; the standard's plate gives $m'_\mathrm{t} = 8~\text{kg} / 0.04~\text{m}^2 = 200$ kg/m2). |

**Returns:** The apparent dynamic stiffness per unit area `s't`, in N/m3 (numerically MN/m3 when divided by 1e6).

## DynamicStiffnessResult

```python
DynamicStiffnessResult(
    apparent_stiffness: float,
    gas_stiffness: float,
    dynamic_stiffness: float,
    resonant_frequency: float,
    floor_mass_per_area: float,
    natural_frequency: float,
)
```

Dynamic stiffness of a resilient layer and the floating-floor resonance.

**Attributes**

| Name | Description |
| :--- | :--- |
| `apparent_stiffness` | Apparent dynamic stiffness `s't`, in N/m3. |
| `gas_stiffness` | Enclosed-gas dynamic stiffness `s'a`, in N/m3. |
| `dynamic_stiffness` | Installed dynamic stiffness `s'`, in N/m3. |
| `resonant_frequency` | Measured test resonant frequency `fr`, in hertz. |
| `floor_mass_per_area` | Supported-floor mass per unit area `m'`, kg/m2. |
| `natural_frequency` | Installed-floor natural frequency `f0`, in hertz. |

### DynamicStiffnessResult.plot()

```python
DynamicStiffnessResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot `f0(s')` with this design point marked.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

### DynamicStiffnessResult.report()

```python
DynamicStiffnessResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render an EN 29052-1 dynamic-stiffness test-report fiche to a PDF.

Writes a one-page accredited dynamic-stiffness report (EN 29052-1:1992,
identical to ISO 9052-1:1989): the standard-basis line, an optional
metadata header block (client, specimen, the total mass per unit area
`m't` used during the test, the loaded specimen thickness `d`, test
facility, date, climate ...), a two-panel body with a compact metrics
table (the resonant frequency `fr`, the apparent dynamic stiffness
`s't` of Formula 4, the enclosed-gas term `s'a` of Formula 7 when it
applies, the installed dynamic stiffness `s'` of Clause 8.2 and the
supported-floor natural frequency `f0` of Formula 2) beside the
`f0(s')` design curve, a boxed apparent dynamic stiffness `s't` with
the installed `s'` and the resonance `fr` alongside, and a footer
with the fixed disclaimer. EN 29052-1 is a characterisation, so there is
no pass/fail verdict.

Clause 9 requires every dynamic stiffness per unit area to be stated in
meganewtons per cubic metre to the nearest meganewton per cubic metre,
so the stiffness values are rounded to the nearest MN/m3; the
frequencies are shown to 0,1 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata); `None` produces a body-and-disclaimer fiche. The applicable descriptive fields are `client`, `manufacturer`, `specimen`, `mass_per_area` (the total mass per unit area `m't`), `thickness` (the loaded specimen thickness `d`, in metres, shown in millimetres), `test_room`, `test_date`, `temperature_c`, `relative_humidity_percent`, `measurement_standard`, `laboratory`, `operator`, `report_id` and `notes`. The `requirement` field is ignored (EN 29052-1 has no verdict). |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | Accepted for a uniform `.report()` signature; the dynamic-stiffness fiche has a single body layout, so it has no effect. |
| `language` | Fiche language: `"en"` (default, English, decimal point) or `"es"` (Spanish, decimal comma). |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"`. |
| ImportError | If reportlab or matplotlib is not installed. The fiche always embeds the `f0(s')` design curve, so both are required (`pip install "phonometry[report,plot]"`). |

## DynamicStiffnessWarning

Advisory when the enclosed-gas term makes `s'` unresolvable (clause 8.2).

## enclosed_gas_stiffness

```python
enclosed_gas_stiffness(
    thickness_m: ArrayLike,
    porosity: float,
    *,
    atmospheric_pressure_pa: float = 100000.0,
) -> np.ndarray | float
```

Enclosed-gas dynamic stiffness per unit area `s'a` (Formula 7).

The isothermal compression of the pore air adds a stiffness in parallel
with the material's structure: $s'_\mathrm{a} = p_0 / (d\,\epsilon)$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `thickness_m` | Thickness `d` of the specimen under the static load, in metres (scalar or array). |
| `porosity` | Porosity `epsilon` of the specimen (0-1). |
| `atmospheric_pressure_pa` | Atmospheric pressure `p0`, in pascals (default `STANDARD_ATMOSPHERIC_PRESSURE`, the standard's 0,1 MPa). |

**Returns:** The enclosed-gas dynamic stiffness per unit area `s'a`, in N/m3.

:::note
With the standard's $p_0 = 0.1$ MPa and $\epsilon = 0.9$
this reduces to $s'_\mathrm{a} = 111/d$ MN/m3 for `d` in millimetres
(clause 8.2 NOTE).
:::

## floating_floor_resonance

```python
floating_floor_resonance(
    resonant_frequency_hz: float,
    total_mass_per_area_kg_m2: float,
    floor_mass_per_area_kg_m2: float,
    *,
    airflow_resistivity_kpa_s_m2: float = inf,
    thickness_m: float | None = None,
    porosity: float | None = None,
    atmospheric_pressure_pa: float = 100000.0,
) -> DynamicStiffnessResult
```

Full EN 29052-1 chain: measured resonance -> installed `s'` and `f0`.

Chains the apparent dynamic stiffness (Formula 4), the enclosed-gas term
(Formula 7, when `thickness_m` and `porosity` are given), the airflow
resistivity combination (clause 8.2) and the installed-floor natural
frequency (Formula 2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `resonant_frequency_hz` | Measured resonant frequency `fr`, in hertz. |
| `total_mass_per_area_kg_m2` | Test total mass per unit area `m't`, in kg/m2. |
| `floor_mass_per_area_kg_m2` | Supported-floor mass per unit area `m'`, in kg/m2. |
| `airflow_resistivity_kpa_s_m2` | Lateral airflow resistivity `r`, in kPa.s/m2 (default `inf` -> the high-resistivity case $s' = s'_\mathrm{t}$). |
| `thickness_m` | Specimen thickness `d` under load, in metres. Required together with `porosity` for the enclosed-gas term, which applies when $r < 100$ kPa.s/m2. That condition is on the *value* of `airflow_resistivity_kpa_s_m2` rather than on a literal, so a signature cannot state it: it is checked here and raises. |
| `porosity` | Specimen porosity `epsilon`, required with `thickness_m` (see above). |
| `atmospheric_pressure_pa` | Atmospheric pressure `p0`, in pascals. |

**Returns:** The [`DynamicStiffnessResult`](/phonometry/reference/api/materials/dynamic-stiffness/#dynamicstiffnessresult).

## installed_dynamic_stiffness

```python
installed_dynamic_stiffness(
    apparent_stiffness_n_m3: float,
    *,
    airflow_resistivity_kpa_s_m2: float,
    gas_stiffness_n_m3: float | None = None,
) -> float
```

Dynamic stiffness per unit area `s'` of the installed material (clause 8.2).

Combines the apparent stiffness with the enclosed-gas term according to the
lateral airflow resistivity `r`:

* $r \ge 100$ kPa.s/m2 -> $s' = s'_\mathrm{t}$ (Formula 5);
* $10 \le r < 100$ kPa.s/m2 -> $s' = s'_\mathrm{t} + s'_\mathrm{a}$
  (Formula 6);
* $r < 10$ kPa.s/m2 -> the standard only requires the qualitative
  criterion $s'_\mathrm{t} \gg s'_\mathrm{a}$ (clause 8.2). This implementation
  applies its own engineering threshold: `s'a` below 10 % of `s't` is treated as
  negligible and $s' = s'_\mathrm{t}$ (a [`DynamicStiffnessWarning`](/phonometry/reference/api/materials/dynamic-stiffness/#dynamicstiffnesswarning) is
  emitted; clause 8.2 requires the error caused by disregarding `s'a` to
  be stated in the test report); above it the result is `nan`, as the
  method cannot resolve `s'`.

The airflow resistivity is in kilopascal seconds per square metre, the
unit clause 8.2 states its thresholds in, and it is asked for by name
because the flow resistivities this library holds elsewhere
(`flow_resistivity_pa_s_m2`) are
in pascal seconds per square metre, a thousand times smaller a unit.

**Parameters**

| Name | Description |
| :--- | :--- |
| `apparent_stiffness_n_m3` | Apparent dynamic stiffness `s't`, in N/m3. |
| `airflow_resistivity_kpa_s_m2` | Lateral airflow resistivity `r`, in kPa.s/m2 (ISO 9053). |
| `gas_stiffness_n_m3` | Enclosed-gas dynamic stiffness `s'a`, in N/m3 (see [`enclosed_gas_stiffness`](/phonometry/reference/api/materials/dynamic-stiffness/#enclosed_gas_stiffness)). Required below 100 kPa.s/m2, where Formula 6 adds it and case c) weighs it against `s't`; above, Formula 5 does not use it. |

**Returns:** The installed dynamic stiffness per unit area `s'`, in N/m3 (`nan` when the method cannot resolve it).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive `s't` or `r`, a negative `s'a`, or no `s'a` below 100 kPa.s/m2, where an absent gas term is not a zero one. |

## natural_frequency

```python
natural_frequency(
    dynamic_stiffness_n_m3: ArrayLike,
    mass_per_area_kg_m2: float,
) -> np.ndarray | float
```

Natural frequency `f0` of the resiliently supported floor (Formula 2).

$f_0 = (1/2\pi)\sqrt{s'/m'}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `dynamic_stiffness_n_m3` | Dynamic stiffness per unit area `s'` of the installed layer, in N/m3 (scalar or array). The apparent `s't` of a test specimen is not it; [`installed_dynamic_stiffness`](/phonometry/reference/api/materials/dynamic-stiffness/#installed_dynamic_stiffness) turns one into the other. |
| `mass_per_area_kg_m2` | Mass per unit area of the supported floor `m'`, in kg/m2. |

**Returns:** The natural frequency `f0`, in hertz.

## plot_dynamic_stiffness_rig

```python
plot_dynamic_stiffness_rig(
    ax: Axes | None = None,
    *,
    specimen_side: float = 0.2,
    specimen_thickness: float = 0.02,
    load_mass: float = 8.0,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the dynamic-stiffness resonance rig to scale.

Resilient specimen on the rigid base, the standard square load plate on
top (its mass annotated), the exciter above and an accelerometer on the
plate; defaults are the standard 200 mm square specimen under the 8 kg
plate.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `specimen_side` | Specimen side length, in metres. |
| `specimen_thickness` | Specimen thickness, in metres. |
| `load_mass` | Load-plate mass, in kilograms (annotation). |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the specimen rectangle. |

**Returns:** The axes.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | naming the first of the three that is not finite and positive. |

## PUBLISHED_RESILIENT_LAYERS

*Constant* (`mapping`).

## resilient_layer

```python
resilient_layer(layer: str | ResilientLayer) -> ResilientLayer
```

Look up a published resilient layer, or pass one through.

**Parameters**

| Name | Description |
| :--- | :--- |
| `layer` | A key of [`PUBLISHED_RESILIENT_LAYERS`](/phonometry/reference/api/materials/dynamic-stiffness/#published_resilient_layers), spelled `"<table>/<row>"` like every catalogue key, as `"hopkins-2007-table-a3/mineral_wool_rock_60_30"`, or a [`ResilientLayer`](/phonometry/reference/api/materials/dynamic-stiffness/#resilientlayer) already in hand, such as one built from a product's test report. |

**Returns:** The [`ResilientLayer`](/phonometry/reference/api/materials/dynamic-stiffness/#resilientlayer).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown layer name, listing the keys there are. |

## ResilientLayer

```python
ResilientLayer(
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
    dynamic_stiffness_n_m3: float | None = None,
    apparent_dynamic_stiffness_n_m3: float | None = None,
    density_kg_m3: float | None = None,
    thickness_mm: float | None = None,
)
```

A resilient layer under a floating floor, as its source prints it.

A row of a catalogue like every other ([`CatalogueRow`](/phonometry/reference/api/io/io/#cataloguerow)):
every quantity is optional, because a source prints some columns and not
others, and a cell that holds something other than a number, such as the
bound `s' <= 9 MN/m3` a product declaration prints, is held by the row's
hedges rather than turned into one.

EN 29052-1 names two stiffnesses per unit area, and they are two fields
here. The test measures the apparent stiffness `s't` of a specimen whose
pore air escapes at its sides (Formula 4); clause 8.2 turns it into the
stiffness `s'` of the installed layer, whose pore air cannot, by way of
the lateral airflow resistivity `r` and the enclosed-gas stiffness
`s'a`. Formula 2 takes `s'`. A source that prints `s'` fills
`dynamic_stiffness_n_m3`, which is what Hopkins Table A3 does. A test
report gives `s't` and `s'a`, and `s'` only "if possible" (clause
9 e)); one that leaves `s'` out, like a sheet that gives `s't` alone,
fills `apparent_dynamic_stiffness_n_m3`, and [`natural_frequency`](/phonometry/reference/api/materials/dynamic-stiffness/#natural_frequency)
then needs `r`, and below 100 kPa.s/m2 the report's `s'a`, to go on.

**Attributes**

| Name | Description |
| :--- | :--- |
| `dynamic_stiffness_n_m3` | `s'`, the dynamic stiffness per unit area of the installed layer (clause 8.2), in N/m3. |
| `apparent_dynamic_stiffness_n_m3` | `s't`, the apparent dynamic stiffness per unit area of the test specimen (Formula 4), in N/m3. Not `s'`: for an air-permeable layer the two differ by the enclosed-gas term `s'a`, which "often forms a significant percentage of `s'`" (Hopkins 2007, printed p. 360). |
| `density_kg_m3` | Specimen density, in kg/m3. |
| `thickness_mm` | Nominal uncompressed thickness, in millimetres. |
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

### ResilientLayer.basis_of()

```python
ResilientLayer.basis_of(field_name: str) -> str
```

What the source says this field is, one of [`CATALOGUE_BASES`](/phonometry/reference/api/io/io/#catalogue_bases).

The five are `measured`, `declared`, `calculated`, `estimated`
and `extended`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the field names of this class. |

**Returns:** The field's own entry in `basis`, else the row's, else the empty string, which means the source does not say.

### ResilientLayer.from_printed()

*classmethod*

```python
ResilientLayer.from_printed(**cells: Any) -> Self
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

### ResilientLayer.is_approximate()

```python
ResilientLayer.is_approximate(field_name: str) -> bool
```

Whether the page prints this field with a `~`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page rounded the cell on purpose.

### ResilientLayer.is_derived()

```python
ResilientLayer.is_derived(field_name: str) -> bool
```

Whether this library computed this field instead of reading it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `field_name` | One of the numeric field names of this class. |

**Returns:** `True` when the page did not print it and the value follows from cells that it did. `derived` says how. A value the page prints in another unit, or gives by reference to another of its rows, answers `False`: the number is the page's, and `converted` or `carried` says so.

### ResilientLayer.natural_frequency()

```python
ResilientLayer.natural_frequency(
    mass_per_area_kg_m2: float,
    *,
    airflow_resistivity_pa_s_m2: float | None = None,
    gas_stiffness_n_m3: float | None = None,
) -> float
```

`f0` of a floor of this mass per unit area on this layer.

$f_0 = (1/2\pi)\sqrt{s'/m'}$ (Formula 2), through the module's
[`natural_frequency`](/phonometry/reference/api/materials/dynamic-stiffness/#natural_frequency).

A row that gives `s'` is used as it is, and the two keywords are
refused, because nothing would read them. A row that gives only the
apparent `s't` goes through [`installed_dynamic_stiffness`](/phonometry/reference/api/materials/dynamic-stiffness/#installed_dynamic_stiffness)
first, which is clause 8.2: `s' = s't` at or above 100 kPa.s/m2,
`s' = s't + s'a` from 10 up to 100, and below 10 `s' = s't` only
while `s'a` is negligible (`nan`, with a
[`DynamicStiffnessWarning`](/phonometry/reference/api/materials/dynamic-stiffness/#dynamicstiffnesswarning), when it is not).

The resistivity is taken in pascal seconds per square metre, the unit
every flow resistivity of this library's catalogues is held in, and
divided by a thousand for the kilopascal thresholds of clause 8.2.
The division is correctly rounded and never decreases as its input
grows, so it carries no resistivity across either threshold: exactly
100 000 or 10 000 Pa.s/m2 lands on 100 or 10, and the largest float
below either lands below it. The formula chosen is always the one the
resistivity passed picks.

**Parameters**

| Name | Description |
| :--- | :--- |
| `mass_per_area_kg_m2` | Mass per unit area of the supported floor `m'`, in kg/m2. |
| `airflow_resistivity_pa_s_m2` | Lateral airflow resistivity `r` of the layer (ISO 9053), in Pa.s/m2, for a row that gives only `s't`. |
| `gas_stiffness_n_m3` | Enclosed-gas stiffness `s'a` of the layer (Formula 7, [`enclosed_gas_stiffness`](/phonometry/reference/api/materials/dynamic-stiffness/#enclosed_gas_stiffness)), in N/m3, for a row that gives only `s't` and a resistivity below 100 kPa.s/m2. |

**Returns:** The natural frequency `f0`, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| CatalogueError | for a row that gives only `s't` when no resistivity is passed, saying that `s't` is not `s'` and what to pass; and for a row with no value of either stiffness whose `s't` cell holds something else, such as a declared bound, which it names. |
| ValueError | for a row that gives neither stiffness, naming what its source had in the `s'` cell; for a row that gives `s'` when either keyword is passed; for a resistivity below 100 kPa.s/m2 with no `s'a`; and for a non-positive mass or resistivity. |

### ResilientLayer.printed()

```python
ResilientLayer.printed(
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

### ResilientLayer.printed_fields()

```python
ResilientLayer.printed_fields() -> dict[str, Any]
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

### ResilientLayer.why_missing()

```python
ResilientLayer.why_missing(field_name: str) -> str
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

---
title: "building.regulation.spain"
description: "Spanish building code CTE DB-HR: global indices and requirement checks."
sidebar:
  label: "spain"
---

Spanish building code CTE DB-HR: global indices and requirement checks.

The *Documento Básico HR Protección frente al ruido* of the Spanish Código
Técnico de la Edificación states its requirements in A-weighted global
quantities that are close relatives of, but not identical to, the ISO 717-1
weighted ratings: `RA`, `RA,tr`, `DnT,A` and `D2m,nT,Atr`.

**The global index (Annex A, Formulae (A.5) to (A.7)).** Instead of shifting a
reference curve, DB-HR weights the measured one-third-octave insulation with a
normalised A-weighted source spectrum and sums it energetically:

$$
I_x = -10 \log_{10} \sum_i 10^{(L_{x,i} - X_i)/10} \quad [\mathrm{dBA}]
$$

where `X_i` is the band insulation (`R`, `R'`, `DnT`, `D2m,nT` ...)
and `L_x,i` the normalised spectrum of the source. The sum runs over the
**eighteen** one-third-octave bands 100 Hz to 5 kHz, two more than ISO 717-1's
sixteen: the 4 kHz and 5 kHz bands.

**Which quantity a facade is assessed in (clause 3.1.3.4 point 1).** The name
of the global quantity depends on the dominant outdoor noise, and it is not a
free choice:

* dominant **railway** noise (or railway stations) is assessed as
  `D2m,nT,A` through Formula (A.5), using the Table A.4 railway spectrum;
* dominant **road traffic** or **aircraft** noise is assessed as
  `D2m,nT,Atr` through Formula (A.6), using the Table A.3 road-traffic or
  the Table A.2 aircraft spectrum.

Table H.1 prints the same split. The railway spectrum of Table A.4 happens to
be numerically identical to the road-traffic spectrum of Table A.3, so the two
routes give the same number for a rail-dominant site; the *name* of the
reported quantity still differs, which is why [`d2m_nt_a`](/phonometry/reference/api/building/spain/#d2m_nt_a) and
[`d2m_nt_atr`](/phonometry/reference/api/building/spain/#d2m_nt_atr) are separate entry points rather than one function with a
spectrum switch.

**Relationship with the ISO 717-1 route.** DB-HR Annex H accepts
`DnT,w + C` as an approximation of `DnT,A` (H.1), `D2m,nT,w + C` of
`D2m,nT,A` for trains (H.2) and `D2m,nT,w + Ctr` of `D2m,nT,Atr` for
road traffic (H.3), valid while the two routes differ by less than 1 dB.
Annex H writes those terms as plain `C` and `Ctr` and refers their
definition to UNE-EN ISO 717-1 without narrowing the frequency range; the
reading that they must be the *enlarged-range* terms `C100-5000` and
`Ctr,100-5000`, because the DB-HR indices run to 5 kHz while the ISO 717-1
core range stops at 3150 Hz, is the one the Spanish literature makes explicit
(Avilés López & Perera Martín, note to expressions [7.15] and [7.16]). The
library keeps both routes: this module implements the direct Formula
(A.5)-(A.7) route, which is the normative one for DB-HR, and
[`weighted_rating_extended`](/phonometry/reference/api/building/ratings/#weighted_rating_extended) supplies the
ISO 717-1 route with the enlarged-range adaptation terms.

**Rounding.** DB-HR 3.1.3.1 point 4 requires the final values of the
quantities that define the requirements to be expressed rounded to an integer,
while intermediate values carry one decimal. The result objects therefore
expose the exact value, the one-decimal intermediate and the integer used in
the compliance check.

**Requirements (Clause 2).** Airborne insulation between rooms and against the
outside (Table 2.1, keyed on the day noise index `Ld` of the site), impact
sound pressure level, and reverberation time in classrooms, conference halls,
dining rooms and restaurants.

**Window size (Catálogo de Elementos Constructivos).** Windows are tested on
about 1,8 m2 specimens; larger windows insulate less, and the CEC corrects
`RA` and `RA,tr` by 0 to -3 dB by total window area.

:::note
`"sanitary"` does not mean the same thing here as in
[`phonometry.environment.assessment.spain`](/phonometry/reference/api/environment/spain/). In Table 2.1 of DB-HR
it is the *non-hospital* ambulatory health use of footnote (1) (medical
practices, consulting rooms), deliberately distinct from `"hospital"`;
in the RD 1367/2007 tables it is the *hospitalario* use itself. Both names
reach the top-level [`phonometry`](/phonometry/reference/api/filters/phonometry/) namespace.
:::

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## assess_db_hr

```python
assess_db_hr(
    items: Sequence[tuple[float, DBHRRequirement]],
) -> DBHRAssessment
```

Judge a set of achieved values against their DB-HR requirements.

**Parameters**

| Name | Description |
| :--- | :--- |
| `items` | `(value, requirement)` pairs. |

**Returns:** A [`DBHRAssessment`](/phonometry/reference/api/building/spain/#dbhrassessment).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `items` is empty or a value is not finite. |

## check_db_hr_requirement

```python
check_db_hr_requirement(
    value: float,
    requirement: DBHRRequirement,
) -> DBHRCheck
```

Check an achieved value against a DB-HR requirement.

The achieved value is first rounded as DB-HR prescribes for the quantity
(an integer for the dB quantities that define the requirements, one decimal
for a reverberation time), and the rounded value is compared with the limit.

**Parameters**

| Name | Description |
| :--- | :--- |
| `value` | The achieved value, in the requirement's unit. |
| `requirement` | The [`DBHRRequirement`](/phonometry/reference/api/building/spain/#dbhrrequirement) to check against. |

**Returns:** A [`DBHRCheck`](/phonometry/reference/api/building/spain/#dbhrcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `value` is not finite. |
| TypeError | if `value` is not a single number. |

## d2m_nt_a

```python
d2m_nt_a(
    level_difference: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    spectrum: Literal['pink', 'railway'] = 'pink',
) -> DBHRGlobalIndexResult
```

A-weighted facade level difference `D2m,nT,A` (Formula (A.5)).

The pink-noise global quantity of a facade, a roof or a floor in contact
with the outside air. Clause 3.1.3.4 point 1 makes this the quantity a
**railway-dominant** site is assessed in, evaluated through Formula (A.5)
with the Table A.4 railway spectrum; Table H.1 prints the same split and
Annex H (H.2) gives `D2m,nT,w + C` as its ISO 717-1 approximation.

For a road-traffic or aircraft dominant site the quantity is
`D2m,nT,Atr` instead: use [`d2m_nt_atr`](/phonometry/reference/api/building/spain/#d2m_nt_atr).

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_difference` | Band standardized facade level difference `D2m,nT`, in dB. |
| `frequencies` | Band centre frequencies, in Hz (optional). |
| `spectrum` | `"pink"` (default, Table A.5) or `"railway"` (Table A.4), per the dominant outdoor noise. |

**Returns:** A [`DBHRGlobalIndexResult`](/phonometry/reference/api/building/spain/#dbhrglobalindexresult) named `"D2m,nT,A"`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a spectrum Formula (A.5) does not cover. |
| TypeError | if `spectrum` is not a text. |

## d2m_nt_atr

```python
d2m_nt_atr(
    level_difference: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    spectrum: Literal['traffic', 'aircraft'] = 'traffic',
) -> DBHRGlobalIndexResult
```

A-weighted facade level difference `D2m,nT,Atr` (Formula (A.6)).

The road-traffic global quantity of a facade, a roof or a floor in contact
with the outside air. Clause 3.1.3.4 point 1 makes this the quantity a
**road-traffic or aircraft** dominant site is assessed in, the aircraft
case evaluated through the same Formula (A.6) with the Table A.2 aircraft
spectrum.

A railway-dominant site is assessed as `D2m,nT,A` through Formula (A.5)
instead: use [`d2m_nt_a`](/phonometry/reference/api/building/spain/#d2m_nt_a). The railway spectrum of Table A.4 is
numerically identical to the road-traffic spectrum of Table A.3, so the
two give the same number, but the quantity that the requirement and the
report are stated in is not the same.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_difference` | Band standardized facade level difference `D2m,nT`, in dB. |
| `frequencies` | Band centre frequencies, in Hz (optional). |
| `spectrum` | `"traffic"` (default, Table A.3) or `"aircraft"` (Table A.2), per the dominant outdoor noise. |

**Returns:** A [`DBHRGlobalIndexResult`](/phonometry/reference/api/building/spain/#dbhrglobalindexresult) named `_D2M_NT_ATR`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a spectrum Formula (A.6) does not cover. |
| TypeError | if `spectrum` is not a text. |

## db_hr_airborne_requirement

```python
db_hr_airborne_requirement(
    receiving_room: Literal['protected', 'habitable'],
    source_room: Literal['same_unit', 'other_unit', 'installations', 'activity'],
    *,
    shared_opening: bool = False,
) -> tuple[DBHRRequirement, ...]
```

Airborne insulation requirements between two rooms (DB-HR 2.1.1).

A *protected* room is a habitable room of special protection (bedrooms,
living areas, classrooms, reading rooms, offices); a *habitable* room is
any other occupied room. The source can be another room of the same use
unit (`"same_unit"`, which puts the requirement on the partition `RA`),
a room of a different use unit (`"other_unit"`), or a services or
activity room (`"installations"` / `"activity"`).

When the two rooms share a door or window the DB-HR replaces the
level-difference requirement with a pair of `RA` requirements on the
opening and on the surrounding enclosure; `shared_opening=True` returns
those instead.

**Parameters**

| Name | Description |
| :--- | :--- |
| `receiving_room` | `"protected"` or `"habitable"`. |
| `source_room` | `"same_unit"`, `"other_unit"`, `"installations"` or `"activity"`. |
| `shared_opening` | The two rooms share a door or window. |

**Returns:** A tuple of [`DBHRRequirement`](/phonometry/reference/api/building/spain/#dbhrrequirement), of length one in the general case and two when `shared_opening` applies.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a room either argument does not name, or for `shared_opening` in a case DB-HR does not contemplate (a protected room against a services or activity room, and any `"same_unit"` case). |
| TypeError | if `receiving_room` or `source_room` is not a text. |

## db_hr_facade_requirement

```python
db_hr_facade_requirement(
    ld: float,
    building_use: Literal['residential', 'hospital', 'cultural', 'sanitary', 'educational', 'administrative', 'docente', 'dwelling', 'hospitalario', 'housing', 'office', 'offices', 'teaching'],
    room_type: Literal['bedrooms', 'living', 'classrooms', 'aulas', 'bedroom', 'classroom', 'dormitories', 'dormitorios', 'estancias', 'living_room', 'living_rooms'],
    *,
    dominant_noise: Literal['road', 'railway', 'aircraft'] = 'road',
    quiet_facade: bool = False,
) -> DBHRRequirement
```

Required facade insulation `D2m,nT,Atr` (DB-HR Table 2.1).

The requirement is keyed on the day noise index `Ld` of the site (Annex I
of RD 1513/2005) and on the building use and room type. Two rules modify
it: a facade not directly exposed to the dominant noise (an enclosed
courtyard, a quiet surrounding) is assessed with `Ld` reduced by 10 dBA,
and where aircraft noise dominates the table value is increased by 4 dBA.

When no official `Ld` is available, DB-HR prescribes 60 dBA for
residential acoustic areas.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ld` | Day noise index `Ld` of the site, in dBA. |
| `building_use` | `"residential"`, `"hospital"`, `"cultural"`, `"sanitary"` (non-hospital health premises), `"educational"` or `"administrative"`. |
| `room_type` | `"bedrooms"`, `"living"` (living areas) or `"classrooms"`, per the columns of Table 2.1. |
| `dominant_noise` | `"road"` (default), `"railway"` or `"aircraft"`. This selects the quantity the requirement is stated in as well as the aircraft increment: `"railway"` gives a `D2m,nT,A` requirement (Formula (A.5)) and the other two a `D2m,nT,Atr` one (Formula (A.6)), per clause 3.1.3.4 point 1. |
| `quiet_facade` | Assess with `Ld` reduced by 10 dBA. |

**Returns:** The [`DBHRRequirement`](/phonometry/reference/api/building/spain/#dbhrrequirement), on `D2m,nT,Atr` or, for a railway-dominant site, on `D2m,nT,A`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown use/room combination, an unknown dominant noise, or a non-finite `Ld`. |
| TypeError | if `ld` is not a single number, or `building_use`, `dominant_noise` or `room_type` is not a text. |

## DB_HR_FREQUENCIES_HZ

*Constant* (`tuple`).

```python
DB_HR_FREQUENCIES_HZ = (100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0)
```

## db_hr_global_index

```python
db_hr_global_index(
    band_values: ArrayLike,
    spectrum: Literal['pink', 'traffic', 'railway', 'aircraft'] = 'pink',
    *,
    frequencies: ArrayLike | None = None,
    name: str | None = None,
) -> DBHRGlobalIndexResult
```

A-weighted global insulation index per DB-HR Annex A.

$I_x = -10 \log_{10} \sum_i 10^{(L_{x,i} - X_i)/10}$ over the eighteen
one-third-octave bands 100 Hz to 5 kHz (Formulae (A.5) to (A.7)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_values` | The band insulation `X_i`, in dB. Either exactly the eighteen DB-HR bands, or a longer spectrum together with `frequencies`, from which the eighteen bands are selected. |
| `spectrum` | Normalised spectrum key: `"pink"` (default), `"traffic"`, `"railway"` or `"aircraft"`. |
| `frequencies` | Band centre frequencies, in Hz, one per value. `None` assumes exactly the eighteen DB-HR bands in order, so it is required for any other length. That condition is on the length of `band_values` at run time, which a signature cannot state, so it is checked here and raises rather than being caught by a type checker. |
| `name` | Optional index name carried on the result (e.g. `"R'A"`). |

**Returns:** A [`DBHRGlobalIndexResult`](/phonometry/reference/api/building/spain/#dbhrglobalindexresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown spectrum, a wrong band count, or non-finite values. |
| TypeError | if `spectrum` is not a text. |

## db_hr_impact_requirement

```python
db_hr_impact_requirement(
    receiving_room: Literal['protected', 'habitable'],
    source_room: Literal['other_unit', 'installations', 'activity'],
) -> DBHRRequirement
```

Impact sound requirement `L'nT,w` (DB-HR 2.1.2).

The standardized impact sound pressure level in a protected room adjacent
to a room of another use unit must not exceed 65 dB; against a services or
activity room the limit is 60 dB, and 60 dB also applies to a habitable
room against those. The requirement does not apply to a protected room
horizontally adjacent to a staircase.

**Parameters**

| Name | Description |
| :--- | :--- |
| `receiving_room` | `"protected"` or `"habitable"`. |
| `source_room` | `"other_unit"`, `"installations"` or `"activity"`. |

**Returns:** The [`DBHRRequirement`](/phonometry/reference/api/building/spain/#dbhrrequirement) on `L'nT,w`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a combination DB-HR states no impact limit for. |
| TypeError | if `receiving_room` or `source_room` is not a text. |

## DB_HR_NORMALIZED_SPECTRA

*Constant* (`mapping`).

```python
DB_HR_NORMALIZED_SPECTRA = {'pink': (-30.1, -27.1, -24.4, -21.9, -19.6, -17.6, -15.8, -14.2, -12.9, -11.8, -11.0, -10.4, -10.0, -9.8, -9.7, -9.8, -10.0, -10.5), 'traffic': (-20.0, -20.0, -18.0, -16.0, -15.0, -14.0, -13.0, -12.0, -11.0, -9.0, -8.0, -9.0, -10.0, -11.0, -13.0, -15.0, -16.0, -18.0), 'railway': (-20.0, -20.0, -18.0, -16.0, -15.0, -14.0, -13.0, -12.0, -11.0, -9.0, -8.0, -9.0, -10.0, -11.0, -13.0, -15.0, -16.0, -18.0), 'aircraft': (-23.8, -20.2, -15.4, -13.1, -12.6, -10.4, -9.8, -9.5, -8.7, -9.5, -10.5, -11.0, -12.5, -14.9, -15.9, -18.6, -23.3, -29.9)}
```

## db_hr_party_wall_requirement

```python
db_hr_party_wall_requirement(
    quantity: Literal['D2m,nT,Atr', 'DnT,A'] = 'D2m,nT,Atr',
) -> DBHRRequirement
```

Airborne requirement on a party wall between two buildings (DB-HR 2.1.1 c).

For a habitable or protected room against a *medianería*, DB-HR offers two
alternative routes: either each of the two enclosing leaves reaches
`D2m,nT,Atr` of at least 40 dBA, or the two leaves taken together reach
`DnT,A` of at least 50 dBA. They are alternatives, not cumulative
requirements, so this function returns the one route asked for.

**Parameters**

| Name | Description |
| :--- | :--- |
| `quantity` | `"D2m,nT,Atr"` (default, the per-leaf route, 40 dBA) or `"DnT,A"` (the combined route, 50 dBA). |

**Returns:** The [`DBHRRequirement`](/phonometry/reference/api/building/spain/#dbhrrequirement) of the chosen route.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `quantity` is not a text. |
| ValueError | For an unknown quantity. |

## db_hr_reverberation_requirement

```python
db_hr_reverberation_requirement(
    room_use: Literal['classroom', 'conference_hall', 'lecture_hall', 'aula', 'restaurant', 'dining_room', 'comedor', 'common_area', 'common_areas', 'zonas_comunes'],
    *,
    furnished: bool = False,
) -> DBHRRequirement
```

Reverberation or absorption requirement (DB-HR 2.2).

Classrooms and conference halls under 350 m3 must not exceed 0,7 s empty
(0,5 s with the seating installed); restaurants and dining rooms 0,9 s.
Common areas of residential-public, educational and hospital buildings
that share doors with protected rooms must provide an equivalent absorption
area of at least 0,2 m2 per cubic metre of room volume.

**Parameters**

| Name | Description |
| :--- | :--- |
| `room_use` | `"classroom"` (or `"conference_hall"`), `"restaurant"` (or `"dining_room"`) or `"common_area"`. |
| `furnished` | For a classroom or conference hall, include the seating (the 0,5 s limit). |

**Returns:** The [`DBHRRequirement`](/phonometry/reference/api/building/spain/#dbhrrequirement).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown room use. |
| TypeError | if `room_use` is not a text. |

## DBHRAssessment

```python
DBHRAssessment(checks: tuple[DBHRCheck, ...])
```

A set of DB-HR requirement checks.

**Attributes**

| Name | Description |
| :--- | :--- |
| `checks` | The individual [`DBHRCheck`](/phonometry/reference/api/building/spain/#dbhrcheck) results. |

### DBHRAssessment.passes

*property*

The verdict: every requirement is met.

### DBHRAssessment.plot()

```python
DBHRAssessment.plot(
    ax: Axes | None = None,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the achieved values against their DB-HR limits.

## DBHRCheck

```python
DBHRCheck(requirement: DBHRRequirement, value: float)
```

A DB-HR requirement checked against an achieved value.

The rounding, the margin and the verdict are read from the achieved value
and the requirement, so they are not fields: a check cannot be built to
comply with a value DB-HR fails.

**Attributes**

| Name | Description |
| :--- | :--- |
| `requirement` | The [`DBHRRequirement`](/phonometry/reference/api/building/spain/#dbhrrequirement) checked. |
| `value` | The achieved value, unrounded. |

### DBHRCheck.margin

*property*

How far the reported value clears the limit.

`reported - limit` for a `"min"` requirement and
`limit - reported` for a `"max"` one; non-negative when compliant.

### DBHRCheck.passes

*property*

The verdict: the requirement is met.

The value exactly at the limit after the rounding passes, with a
billionth of a decibel of slack so that binary representation error
in the subtraction cannot turn it into a failure.

### DBHRCheck.reported

*property*

The achieved value rounded half-up as DB-HR prescribes for the quantity.

## DBHRGlobalIndexResult

```python
DBHRGlobalIndexResult(
    value: float,
    intermediate: float,
    reported: int,
    name: str,
    spectrum: Literal['pink', 'traffic', 'railway', 'aircraft'],
    frequencies: np.ndarray,
    band_values: np.ndarray,
    spectrum_levels: np.ndarray,
    band_contributions: np.ndarray,
    reference: str,
)
```

A DB-HR A-weighted global insulation index.

**Attributes**

| Name | Description |
| :--- | :--- |
| `value` | The index, in dBA, unrounded. |
| `intermediate` | The index rounded to one decimal, the form DB-HR prescribes for intermediate quantities and for product specifications. |
| `reported` | The index rounded to an integer, the form DB-HR requires for the quantities that define the requirements (3.1.3.1 point 4). |
| `name` | The index name, e.g. `"RA"` or `_D2M_NT_ATR`. |
| `spectrum` | Key of the normalised spectrum used. |
| `frequencies` | Band centre frequencies, in Hz. |
| `band_values` | The band insulation values `X_i`, in dB. |
| `spectrum_levels` | The normalised spectrum `L_x,i`, in dBA. |
| `band_contributions` | Per-band transmitted level `L_x,i - X_i`, in dBA; the index is minus their energy sum. |
| `reference` | The DB-HR Annex A table the normalised spectrum was read from. |

### DBHRGlobalIndexResult.plot()

```python
DBHRGlobalIndexResult.plot(
    ax: Axes | None = None,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the band insulation with the weighted per-band contributions.

## DBHRRequirement

```python
DBHRRequirement(
    *,
    quantity: str,
    limit: float,
    direction: Literal['min', 'max'],
    unit: str,
    decimals: int,
    reference: str,
    description: str,
)
```

A single DB-HR performance requirement.

**Attributes**

| Name | Description |
| :--- | :--- |
| `quantity` | The quantity the requirement is stated in, e.g. `_DNT_A`, `"L'nT,w"`, `"RA"`, `"T"` or `"A/V"`. |
| `limit` | The limit value, in the quantity's own unit. |
| `direction` | `"min"` when the quantity must be at least the limit, `"max"` when it must be at most the limit. |
| `unit` | The unit the limit is expressed in. |
| `decimals` | Decimal places the achieved value is rounded to before the comparison (DB-HR 3.1.3.1 point 4 for the dB quantities, 3.2.1 for the reverberation time). |
| `reference` | The DB-HR clause the requirement comes from. |
| `description` | The case it applies to, in plain words. |

## dnt_a

```python
dnt_a(
    level_difference: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> DBHRGlobalIndexResult
```

A-weighted standardized level difference `DnT,A` (Formula (A.7)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_difference` | Band standardized level difference `DnT`, in dB. |
| `frequencies` | Band centre frequencies, in Hz (optional). |

**Returns:** A [`DBHRGlobalIndexResult`](/phonometry/reference/api/building/spain/#dbhrglobalindexresult) named `_DNT_A`.

## ra

```python
ra(
    reduction_index: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> DBHRGlobalIndexResult
```

A-weighted global sound reduction index `RA` for pink noise.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reduction_index` | Band sound reduction index `R` (or `R'`), in dB. |
| `frequencies` | Band centre frequencies, in Hz (optional). |

**Returns:** A [`DBHRGlobalIndexResult`](/phonometry/reference/api/building/spain/#dbhrglobalindexresult) named `"RA"`.

## ra_tr

```python
ra_tr(
    reduction_index: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> DBHRGlobalIndexResult
```

A-weighted global sound reduction index `RA,tr` for road-traffic noise.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reduction_index` | Band sound reduction index `R` (or `R'`), in dB. |
| `frequencies` | Band centre frequencies, in Hz (optional). |

**Returns:** A [`DBHRGlobalIndexResult`](/phonometry/reference/api/building/spain/#dbhrglobalindexresult) named `"RA,tr"`.

## window_size_correction

```python
window_size_correction(area: float) -> int
```

Window-size correction of `RA` / `RA,tr`, in dB (CTE CEC).

Windows are tested on specimens of about 1,8 m2; a larger window insulates
less. The Catálogo de Elementos Constructivos of the CTE corrects the
catalogue value by 0 dB up to 2,7 m2, -1 dB over 2,7 to 3,6 m2, -2 dB over
3,6 to 4,6 m2 and -3 dB above 4,6 m2.

**Parameters**

| Name | Description |
| :--- | :--- |
| `area` | Total window area, in m2 (positive). |

**Returns:** The correction, in dB (0, -1, -2 or -3), to be *added* to the catalogue `RA` or `RA,tr`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `area` is not positive and finite. |
| TypeError | if `area` is not a single number. |

---
title: "materials.absorbers.suspended_ceilings"
description: "Suspended ceilings in a reverberation room: EN 16487:2014."
sidebar:
  label: "suspended_ceilings"
---

Suspended ceilings in a reverberation room: EN 16487:2014.

EN ISO 354 measures the sound absorption of a specimen in a reverberation room
and leaves a good deal to the laboratory: how big the specimen is, how it is
mounted, how deep the air space behind it is. For a suspended ceiling those
choices move the answer by more than the measurement uncertainty, so a product
measured in two laboratories could be compared only by accident. This test code
closes them.

**What it fixes.** A specimen area as close to 10,80 m2 as the product allows,
test objects of 0,6 m by 0,6 m butted together with no seal in the joints
between them, the exposed face level with the top of the mounting fixture and
the joint between the specimen and that fixture taped, the edges at an angle to
the room walls, and a mounting fixture of solid material with a surface density
of at least 20 kg/m2. For the type E mounting that a suspended ceiling actually
uses, it fixes the overall depth of construction at 200 mm for the measurement
that CE marking rests on, the substructure at no more than 30 mm wide and 50 mm
deep on a 0,6 m pitch, and
the deflection of the specimen at no more than 5 mm.

**What it costs to ignore the air.** 4.2.1 asks for test conditions under which
the air-absorption correction

$$
\Delta\alpha = \frac{4V(m_2 - m_1)}{S}
$$

of EN ISO 354 Formulae (8) and (9) stays under 0,05 at every frequency, with
the relative humidity at 50 % or more. That correction is the difference between
two measurements of the same room on two different days, and a dry room makes it
large exactly where a ceiling absorbs most.

**What it is worth.** Table 1 is the reproducibility between European
laboratories, from the round robin of Annex A: `+/- 0,23` on the absorption
coefficient at 125 Hz and 250 Hz, falling to `+/- 0,10` at 1 kHz and 2 kHz,
and `+/- 0,08` on the weighted rating, with a coverage factor of 2,8 applied
to the reproducibility standard deviation. The figures hold for a plane absorber
with the type E mounting and for nothing else, which the clause says in as many
words.

Read from BS EN 16487:2014.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## air_absorption_correction

```python
air_absorption_correction(
    *,
    volume_m3: float,
    specimen_area_m2: float,
    attenuation_with: ArrayLike,
    attenuation_empty: ArrayLike,
) -> NDArray[np.float64]
```

The correction 4.2.1 caps, as an absorption coefficient.

$$
\Delta\alpha = \frac{4V(m_2 - m_1)}{S}
$$

the part of EN ISO 354 Formulae (8) and (9) that comes from the air rather
than from the specimen. The two attenuation coefficients belong to the two
measurements, with the specimen and empty, and the correction is their
difference because everything else about the room cancels.

A room measured on two days of different humidity can carry more of this
than the specimen carries of its own absorption at 4 kHz, which is why the
clause caps it at [`AIR_CORRECTION_LIMIT`](/phonometry/reference/api/materials/suspended-ceilings/#air_correction_limit) and asks for 50 % relative
humidity or more.

**Parameters**

| Name | Description |
| :--- | :--- |
| `volume_m3` | $V$ of the reverberation room, in cubic metres. |
| `specimen_area_m2` | $S$ of the specimen, in square metres. |
| `attenuation_with` | $m_2$ per band, in reciprocal metres. |
| `attenuation_empty` | $m_1$ per band, in reciprocal metres. |

**Returns:** $\Delta\alpha$ per band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive volume or area, or coefficients that do not match band for band. |

## AIR_CORRECTION_LIMIT

*Constant* (`float`).

```python
AIR_CORRECTION_LIMIT = 0.05
```

## CEILING_UNCERTAINTY

*Constant* (`dict`).

```python
CEILING_UNCERTAINTY = {125.0: 0.23, 250.0: 0.23, 500.0: 0.11, 1000.0: 0.1, 2000.0: 0.1, 4000.0: 0.13}
```

## CeilingSpecimenCheck

```python
CeilingSpecimenCheck(
    area_m2: float,
    area_error_m2: float,
    mounting: str,
    depth_mm: float | None,
    deflection_ok: bool,
    substructure_ok: bool,
    fixture_ok: bool,
    ce_marking_depth: bool,
    satisfied: bool,
)
```

Whether a test arrangement meets the geometry 4.1.1 fixes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `area_m2` | The specimen area as built, in square metres. |
| `area_error_m2` | How far it sits from the 10,80 m2 the code aims at. |
| `mounting` | The mounting letter the arrangement uses. |
| `depth_mm` | The overall depth of construction, in millimetres, for a type E mounting, or `None` for the others. |
| `deflection_ok` | Whether the deflection stays inside 5 mm. |
| `substructure_ok` | Whether the profile stays inside 30 mm by 50 mm. |
| `fixture_ok` | Whether the mounting fixture is heavy enough. |
| `ce_marking_depth` | Whether the depth is the 200 mm the CE marking data rests on. |
| `satisfied` | Whether every one of the above holds. |

## check_ceiling_specimen

```python
check_ceiling_specimen(
    *,
    area_m2: float,
    mounting: str = 'E',
    depth_mm: float | None = None,
    deflection_mm: float = 0.0,
    substructure_width_mm: float = 0.0,
    substructure_height_mm: float = 0.0,
    fixture_density_kg_m2: float = 20.0,
) -> CeilingSpecimenCheck
```

Does the arrangement meet the geometry of 4.1.1?

**Parameters**

| Name | Description |
| :--- | :--- |
| `area_m2` | The specimen area as built, in square metres. |
| `mounting` | The mounting letter, `"E"` by default. |
| `depth_mm` | The overall depth of construction, in millimetres, required for a type E mounting. |
| `deflection_mm` | The largest deflection of the specimen, in millimetres. |
| `substructure_width_mm` | The substructure profile width, in millimetres. |
| `substructure_height_mm` | Its height, in millimetres. |
| `fixture_density_kg_m2` | The surface density of the mounting fixture, in kilograms per square metre. |

**Returns:** The verdict, as a [`CeilingSpecimenCheck`](/phonometry/reference/api/materials/suspended-ceilings/#ceilingspecimencheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive area or depth, a negative or non-finite deflection, substructure dimension or fixture density, an unknown mounting letter, or a type E arrangement with no depth given. |

## EN16487_COVERAGE_FACTOR

*Constant* (`float`).

```python
EN16487_COVERAGE_FACTOR = 2.8
```

## MAX_DEFLECTION_MM

*Constant* (`float`).

```python
MAX_DEFLECTION_MM = 5.0
```

## MIN_FIXTURE_DENSITY_KG_M2

*Constant* (`float`).

```python
MIN_FIXTURE_DENSITY_KG_M2 = 20.0
```

## MIN_RELATIVE_HUMIDITY_PERCENT

*Constant* (`float`).

```python
MIN_RELATIVE_HUMIDITY_PERCENT = 50.0
```

## MIN_ROOM_EDGE_ANGLE_DEG

*Constant* (`float`).

```python
MIN_ROOM_EDGE_ANGLE_DEG = 10.0
```

## MIN_SUPPORT_SPACING_M

*Constant* (`float`).

```python
MIN_SUPPORT_SPACING_M = 1.2
```

## mounting_type

```python
mounting_type(letter: str) -> str
```

What one mounting letter of EN ISO 354 Annex B means here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `letter` | `"A"`, `"B"`, `"E"` or `"J"`. |

**Returns:** The description in the words of 4.1.1.2.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a letter this test code does not admit. |

## MOUNTING_TYPES

*Constant* (`dict`).

```python
MOUNTING_TYPES = {'A': 'attached directly against a hard surface, with no air space', 'B': 'glued to a hard surface with a 3 mm air space kept by corner shims', 'E': 'suspended from a hard surface with an air space behind it', 'J': 'a discrete absorber, freely suspended or standing'}
```

## reproducibility_uncertainty

```python
reproducibility_uncertainty(
    frequencies: ArrayLike | None = None,
) -> NDArray[np.float64]
```

Table 1, the reproducibility between European laboratories.

The figures are an expanded uncertainty: the round robin of Annex A gives a
reproducibility standard deviation and ISO 5725-6 multiplies it by
[`EN16487_COVERAGE_FACTOR`](/phonometry/reference/api/materials/suspended-ceilings/#en16487_coverage_factor). They hold for a plane absorber with the type E
mounting and a 200 mm overall depth, and 6.2 says plainly that nothing has
been investigated for any other absorber or mounting.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | The nominal octave centres wanted, in hertz; omit for the six the table prints, in order. |

**Returns:** The uncertainty of the absorption coefficient in each band.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a frequency Table 1 does not print. |

## SUBSTRUCTURE_LIMITS_MM

*Constant* (`tuple`).

```python
SUBSTRUCTURE_LIMITS_MM = (30.0, 50.0)
```

## SUBSTRUCTURE_SPACING_M

*Constant* (`float`).

```python
SUBSTRUCTURE_SPACING_M = 0.6
```

## SUPPORT_SECTION_MM

*Constant* (`tuple`).

```python
SUPPORT_SECTION_MM = (50.0, 50.0)
```

## SuspendedCeilingWarning

The test arrangement is outside a condition EN 16487 states.

## TARGET_SPECIMEN_AREA_M2

*Constant* (`float`).

```python
TARGET_SPECIMEN_AREA_M2 = 10.8
```

## TEST_OBJECT_SIZE_M

*Constant* (`tuple`).

```python
TEST_OBJECT_SIZE_M = (0.6, 0.6)
```

## TYPE_E_DEPTH_MM

*Constant* (`float`).

```python
TYPE_E_DEPTH_MM = 200.0
```

## WEIGHTED_UNCERTAINTY

*Constant* (`float`).

```python
WEIGHTED_UNCERTAINTY = 0.08
```

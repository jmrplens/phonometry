---
title: "metrology.reference_values"
description: "Preferred reference values for acoustical and vibratory levels (ISO 1683:2015)."
sidebar:
  label: "reference_values"
---

Preferred reference values for acoustical and vibratory levels (ISO 1683:2015).

A level in decibels is a ratio to a reference value, so the number means
nothing until the reference is known: the same pressure reads 26 dB higher
against the 1 µPa of water than against the 20 µPa of air, and the same
vibration 34 dB higher against 1 nm/s than against 50 nm/s. ISO 1683:2015
fixes one reference per quantity in three tables, and the level functions of
this library count their decibels from them unless the standard they
implement names another:

- **Table 1**, sounds in air and other gases: sound pressure 20 µPa, sound
  exposure (20 µPa)² s, sound power 1 pW, sound energy 1 pJ and sound
  intensity 1 pW/m².
- **Table 2**, sounds in water and other liquids: sound pressure 1 µPa, sound
  exposure 1 µPa² s, sound power 1 pW, sound energy 1 pJ, sound intensity
  1 pW/m², sound particle displacement 1 pm, velocity 1 nm/s and acceleration
  1 µm/s², and a distance of 1 m for the compound quantities of its note c
  (a source level re 1 µPa m, for one).
- **Table 3**, vibratory quantities: displacement 1 pm, velocity 1 nm/s,
  acceleration 1 µm/s² and force 1 µN. Its note b adds the 50 nm/s that is
  also used for structure-borne sound, against which the velocity level comes
  out close to the associated sound pressure and intensity levels.

[`ISO1683_REFERENCE_VALUES`](/phonometry/reference/api/metrology/reference-values/#iso1683_reference_values) holds all of them, keyed by medium and then
by quantity, and every value is in the coherent SI unit its row names, so the
20 µPa of air is `2e-05` Pa:

```text
from phonometry import metrology

p0 = metrology.ISO1683_REFERENCE_VALUES["gas"]["sound_pressure"]
p0.value, p0.unit, p0.printed  # (2e-05, 'Pa', '20 µPa')
```

Note b of Table 2 gives the offset between the two pressure references, a
level re 1 µPa being $10 \lg(20^2/1^2) \approx 26.0$ dB above the same
pressure re 20 µPa; [`phonometry.underwater.in_air_to_underwater_spl`](/phonometry/reference/api/underwater/acoustics/#in_air_to_underwater_spl)
applies it.

The values were transcribed from the Spanish text UNE-EN ISO 1683:2016, which
adopts ISO 1683:2015 unchanged, PDF pages 8 and 9 (printed folios 8 and 9),
and the quantity names are given here in English. A module that counts its
decibels from a different reference keeps it, and names the document it comes
from beside it: DIN 45672-2 defines its own 5·10⁻⁸ m/s for railway vibration
(Formula (2)), and ISO/TS 7849 and ISO 9611 refer the surface velocity to the
same 5·10⁻⁸ m/s, which is the 50 nm/s of note b of Table 3.
`scripts/check_reference_values.py` holds the tree to that: a reference value
declared in the package either points at this table or says where it was read.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ISO1683_REFERENCE_VALUES

*Constant* (`mapping`).

## ReferenceValue

```python
ReferenceValue(
    quantity: str,
    medium: str,
    value: float,
    unit: str,
    printed: str,
    table: str,
)
```

One reference value of ISO 1683:2015, with what it is a reference of.

**Attributes**

| Name | Description |
| :--- | :--- |
| `quantity` | The quantity the value is the reference of, in English (`"sound pressure"`, `"vibratory velocity"`). |
| `medium` | `"gas"` (Table 1), `"liquid"` (Table 2) or `"solid"` (Table 3, structure-borne sound and vibration). |
| `value` | The reference value, in the coherent SI unit `unit` names: 20 µPa is `2e-05` with `unit` `"Pa"`. |
| `unit` | The SI unit of `value`. |
| `printed` | The value as the table prints it, prefix and all. |
| `table` | Where the value is printed: `"Table 1"` to `"Table 3"`, or `"Table 3, note b"` for the 50 nm/s alternative. |

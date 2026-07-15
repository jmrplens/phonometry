---
title: "materials.sound_absorption"
description: "Public API of phonometry.materials.sound_absorption (auto-generated)."
sidebar:
  label: "sound_absorption"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Sound absorption in a reverberation room: BS EN ISO 354:2003.

The mean reverberation time of a reverberation room is measured empty and with
the test specimen installed. From those two reverberation times the equivalent
sound absorption area of the specimen is obtained via Sabine's equation, and for
a plane absorber the sound absorption coefficient follows by dividing by the
covered area (ISO 354:2003, Clauses 4 and 8.1).

Equivalent sound absorption area (ISO 354:2003, Eq. (5) empty room / Eq. (7) with
specimen; identical form):

```text
A = 55,3 * V / (c * T) - 4 * V * m
```

with `V` the room volume (m3), `c` the speed of sound (m/s), `T` the
reverberation time (s) and `m` the power attenuation coefficient of air (1/m).
The speed of sound follows Eq. (6), valid for 15 degC to 30 degC:

```text
c = (331 + 0,6 * t/degC) m/s
```

The equivalent sound absorption area of the specimen and its absorption
coefficient (ISO 354:2003, Eq. (8) and Eq. (9)):

```text
AT = A2 - A1 = 55,3 * V * (1/(c2*T2) - 1/(c1*T1)) - 4 * V * (m2 - m1)
alpha_s = AT / S
```

`alpha_s` may exceed 1,0 (e.g. from diffraction/edge effects) and is not a
percentage (ISO 354:2003, Clause 3.7 NOTE 2); it is therefore never clamped.

The air attenuation coefficient `m` is defined by ISO 354 only through its
conversion from the ISO 9613-1 attenuation coefficient `alpha` (in dB/m)
(ISO 354:2003, 8.1.2.1):

```text
m = alpha / (10 * lg e)
```

ISO 354 otherwise defers the calculation of `alpha` entirely to ISO 9613-1.
`m` is therefore a user-supplied per-band parameter here (default 0, i.e. no air
correction); a caller holding ISO 9613-1 `alpha` values can convert them with
[`attenuation_from_alpha`](/phonometry/reference/api/materials/sound-absorption/#attenuation_from_alpha).

## absorption_area

```python
absorption_area(
    t60: ArrayLike,
    volume: float,
    *,
    temperature: float = 20.0,
    speed_of_sound: float | None = None,
    m: ArrayLike = 0.0,
) -> NDArray[np.float64]
```

Equivalent sound absorption area of a room (ISO 354:2003, Eq. (5)/(7)).

`A = 55,3 * V / (c * T) - 4 * V * m`. This is Sabine's equation with the
air-absorption term; it gives the empty-room area `A1` from `T1` or the
with-specimen area `A2` from `T2` (both equations have identical form).

**Parameters**

| Name | Description |
| :--- | :--- |
| `t60` | Reverberation time(s) `T`, in seconds (scalar or per band). |
| `volume` | Room volume `V`, in cubic metres. |
| `temperature` | Air temperature, in degrees Celsius, used to compute the speed of sound via Eq. (6) when `speed_of_sound` is not given (default 20 degC, i.e. c = 343 m/s). A temperature outside 15..30 degC emits an [`AbsorptionWarning`](/phonometry/reference/api/materials/sound-absorption/#absorptionwarning). A room volume below the 150 m3 minimum of clause 6.1.1 likewise emits an advisory [`AbsorptionWarning`](/phonometry/reference/api/materials/sound-absorption/#absorptionwarning). |
| `speed_of_sound` | Explicit speed of sound `c`, in m/s; overrides `temperature` and Eq. (6) when supplied. |
| `m` | Power attenuation coefficient of air `m`, in 1/m (a scalar or an array matching the shape of `t60`; default 0, i.e. no air correction). A per-band `m` whose shape differs from `t60` raises `ValueError`. Obtain it from an ISO 9613-1 attenuation coefficient with [`attenuation_from_alpha`](/phonometry/reference/api/materials/sound-absorption/#attenuation_from_alpha). |

**Returns:** Equivalent sound absorption area `A`, in square metres, with the shape of `t60`.

## absorption_coefficient

```python
absorption_coefficient(
    t1: ArrayLike,
    t2: ArrayLike,
    volume: float,
    sample_area: float,
    *,
    temperature1: float = 20.0,
    temperature2: float | None = None,
    speed_of_sound1: float | None = None,
    speed_of_sound2: float | None = None,
    m1: ArrayLike = 0.0,
    m2: ArrayLike = 0.0,
) -> NDArray[np.float64]
```

Sound absorption coefficient of a plane absorber (ISO 354:2003, Eq. (9)).

Builds the equivalent sound absorption area of the specimen from Eq. (8),
`AT = A2 - A1 = 55,3*V*(1/(c2*T2) - 1/(c1*T1)) - 4*V*(m2 - m1)`, using the
empty-room reverberation time `T1` and the with-specimen time `T2`, then
returns `alpha_s = AT / S` (Eq. (9)).

The two measurements may be at different temperatures; `c1` and `c2` are
resolved independently. `alpha_s` is returned unclamped and may exceed 1,0
(Clause 3.7 NOTE 2). Because adding an absorber must reduce the reverberation
time, `T2 >= T1` (`alpha_s <= 0`) is non-physical and emits an
[`AbsorptionWarning`](/phonometry/reference/api/materials/sound-absorption/#absorptionwarning). A room volume below the 150 m3 minimum of
clause 6.1.1, or a sample area outside the clause 6.2.1.1 range
(`10 m2 <= S <= 12 m2`, upper limit scaled by `(V/200)^(2/3)` when
`V > 200 m3`), each emit an advisory [`AbsorptionWarning`](/phonometry/reference/api/materials/sound-absorption/#absorptionwarning).

**Parameters**

| Name | Description |
| :--- | :--- |
| `t1` | Empty-room reverberation time(s) `T1`, in seconds. |
| `t2` | With-specimen reverberation time(s) `T2`, in seconds. |
| `volume` | Room volume `V`, in cubic metres. |
| `sample_area` | Area `S` covered by the test specimen, in square metres (for both-sides-exposed absorbers, the area of the two sides; Clause 3.7 NOTE 1). |
| `temperature1` | Empty-room air temperature, in degrees Celsius (default 20). Used for `c1` via Eq. (6) unless `speed_of_sound1` is given. |
| `temperature2` | With-specimen air temperature, in degrees Celsius; defaults to `temperature1`. Used for `c2` unless `speed_of_sound2` is given. |
| `speed_of_sound1` | Explicit `c1` in m/s; overrides `temperature1`. |
| `speed_of_sound2` | Explicit `c2` in m/s; overrides `temperature2`. Defaults to `speed_of_sound1` when that is given but `c2` is not, so overriding only `c1` applies the same speed to both measurements. |
| `m1` | Empty-room air attenuation coefficient `m1`, in 1/m (default 0). |
| `m2` | With-specimen air attenuation coefficient `m2`, in 1/m (default 0). |

**Returns:** Sound absorption coefficient `alpha_s` with the broadcast shape of `t1` and `t2`.

## AbsorptionWarning

Advisory for out-of-range or non-physical ISO 354 absorption inputs.

## attenuation_from_alpha

```python
attenuation_from_alpha(alpha: ArrayLike) -> NDArray[np.float64]
```

Air power attenuation coefficient `m` from ISO 9613-1 `alpha`.

Applies the ISO 354:2003 (8.1.2.1) conversion `m = alpha / (10 * lg e)`,
where `alpha` is the attenuation coefficient in decibels per metre used by
ISO 9613-1 and `m` is the power attenuation coefficient in reciprocal
metres entering Eq. (5)/(7)/(8). ISO 354 itself provides no `alpha` table
or formula (it defers to ISO 9613-1); this helper only performs the unit
conversion for a caller who already holds `alpha` values.

**Parameters**

| Name | Description |
| :--- | :--- |
| `alpha` | Attenuation coefficient, in dB/m (scalar or per band). |

**Returns:** Power attenuation coefficient `m`, in 1/m.

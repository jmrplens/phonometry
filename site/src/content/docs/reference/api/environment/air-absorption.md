---
title: "environmental.air_absorption"
description: "Public API of phonometry.environmental.air_absorption (auto-generated)."
sidebar:
  label: "air_absorption"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Atmospheric absorption of sound: ISO 9613-1:1993.

The attenuation of a pure tone propagating through the atmosphere is governed by
a pure-tone attenuation coefficient `alpha` (in dB/m) that depends on frequency,
temperature, humidity and pressure through the vibrational relaxation of the
oxygen and nitrogen molecules plus classical and rotational losses
(ISO 9613-1:1993, clause 6).

The attenuation coefficient (ISO 9613-1:1993, Eq. (5)):

```text
alpha = 8,686 * f^2 * {
          1,84e-11 * (pa/pr)^-1 * (T/T0)^(1/2)
        + (T/T0)^(-5/2) * [
              0,012 75 * exp(-2239,1/T) * (frO + f^2/frO)^-1
            + 0,106 8  * exp(-3352,0/T) * (frN + f^2/frN)^-1
          ]
      }
```

in decibels per metre, with the oxygen and nitrogen relaxation frequencies
(ISO 9613-1:1993, Eq. (3) and Eq. (4)):

```text
frO = (pa/pr) * [24 + 4,04e4 * h * (0,02 + h)/(0,391 + h)]
frN = (pa/pr) * (T/T0)^(-1/2)
      * [9 + 280 * h * exp{-4,170 * [(T/T0)^(-1/3) - 1]}]
```

Here `T` is the ambient temperature (K), `T0 = 293,15 K` and
`pr = 101,325 kPa` are the reference conditions (ISO 9613-1:1993, clause 4.2),
`pa` is the ambient pressure (kPa) and `h` is the molar concentration of
water vapour as a percentage, obtained from the relative humidity by the
psychrometric conversion (ISO 9613-1:1993, clause 6.4 / Annex B):

```text
h = hr * (psat/pr) / (pa/pr)
psat/pr = 10 ^ (-6,8346 * (T01/T)^1,261 + 4,6151),  T01 = 273,16 K
```

with `hr` the relative humidity (%) and `T01` the triple-point temperature of
water.

Table 1 of ISO 9613-1:1993 tabulates `alpha` (in dB/km) at the reference
pressure for a grid of temperature, relative humidity and one-third-octave
frequency; its rows are labelled with the ISO 266 preferred frequencies but the
coefficients are computed at the exact midband frequencies (Note 5)
`fm = 1000 * 10^(k/10)`, `k` integer. Pass `exact_midband=True` to snap the
requested frequencies onto that grid and reproduce Table 1 exactly.

This module closes the loop with [`phonometry.sound_absorption`](/phonometry/reference/api/materials/sound-absorption/) (ISO 354),
whose air power-attenuation coefficient `m` (1/m) is defined only through the
ISO 9613-1 `alpha` via `m = alpha / (10 * lg e)`. [`air_attenuation_m`](/phonometry/reference/api/environment/air-absorption/#air_attenuation_m)
returns that `m` directly.

## air_attenuation

```python
air_attenuation(
    frequencies: ArrayLike,
    temperature: float = 20.0,
    relative_humidity: float = 50.0,
    pressure: float = 101.325,
    *,
    exact_midband: bool = False,
) -> NDArray[np.float64]
```

Pure-tone atmospheric attenuation coefficient (ISO 9613-1:1993, Eq. (5)).

Evaluates `alpha` in decibels per metre from the oxygen and nitrogen
relaxation frequencies (Eq. (3)/(4)) and the classical, rotational and
vibrational absorption terms (Eq. (5)). Fully vectorized over
`frequencies`; `temperature`, `relative_humidity` and `pressure` are
scalars.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequency or frequencies `f`, in hertz (array-like). |
| `temperature` | Ambient air temperature, in degrees Celsius (default 20 degC, i.e. the reference `T0`). A value outside the -20..+50 degC tabulated range emits an [`AtmosphericAbsorptionWarning`](/phonometry/reference/api/environment/air-absorption/#atmosphericabsorptionwarning); a value at or below absolute zero raises `ValueError`. |
| `relative_humidity` | Relative humidity, in percent, with respect to saturation over liquid water (default 50 %). Outside 10..100 % emits an [`AtmosphericAbsorptionWarning`](/phonometry/reference/api/environment/air-absorption/#atmosphericabsorptionwarning); outside [0, 100] % raises `ValueError`. |
| `pressure` | Ambient atmospheric pressure `pa`, in kilopascals (default 101,325 kPa = one standard atmosphere = `pr`). Above 200 kPa emits an [`AtmosphericAbsorptionWarning`](/phonometry/reference/api/environment/air-absorption/#atmosphericabsorptionwarning); non-positive raises `ValueError`. |
| `exact_midband` | When `True`, each requested frequency is snapped to the nearest exact one-third-octave midband `fm = 1000*10^(k/10)` (Eq. (6)) before evaluation, reproducing the frequencies used for Table 1 (Note 5). Default `False` (use `frequencies` verbatim). |

**Returns:** Attenuation coefficient `alpha`, in dB/m, with the shape of `frequencies`.

:::note
ISO 354:2003 defers its air power-attenuation coefficient `m` (1/m)
entirely to this `alpha` via `m = alpha / (10 * lg e)`. Use
[`air_attenuation_m`](/phonometry/reference/api/environment/air-absorption/#air_attenuation_m) to obtain that `m` for
[`phonometry.sound_absorption.absorption_area`](/phonometry/reference/api/materials/sound-absorption/#absorption_area) /
[`absorption_coefficient`](/phonometry/reference/api/materials/sound-absorption/#absorption_coefficient).
:::

## air_attenuation_m

```python
air_attenuation_m(
    frequencies: ArrayLike,
    temperature: float = 20.0,
    relative_humidity: float = 50.0,
    pressure: float = 101.325,
    *,
    exact_midband: bool = False,
) -> NDArray[np.float64]
```

ISO 354 air power-attenuation coefficient `m` (1/m) from conditions.

Convenience composition of [`air_attenuation`](/phonometry/reference/api/environment/air-absorption/#air_attenuation) (ISO 9613-1 `alpha` in
dB/m) with the ISO 354:2003 (8.1.2.1) conversion `m = alpha / (10 * lg e)`
(via [`phonometry.sound_absorption.attenuation_from_alpha`](/phonometry/reference/api/materials/sound-absorption/#attenuation_from_alpha)). It lets an
ISO 354 caller feed real atmospheric conditions into
[`absorption_area`](/phonometry/reference/api/materials/sound-absorption/#absorption_area) /
[`absorption_coefficient`](/phonometry/reference/api/materials/sound-absorption/#absorption_coefficient) instead of
hand-entering `m`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequency or frequencies `f`, in hertz (array-like). |
| `temperature` | Ambient air temperature, in degrees Celsius (default 20). |
| `relative_humidity` | Relative humidity, in percent (default 50). |
| `pressure` | Ambient atmospheric pressure, in kilopascals (default 101,325). |
| `exact_midband` | Snap frequencies to exact midbands; see [`air_attenuation`](/phonometry/reference/api/environment/air-absorption/#air_attenuation). |

**Returns:** Power attenuation coefficient `m`, in 1/m, with the shape of `frequencies`.

## AtmosphericAbsorptionWarning

Advisory for ISO 9613-1 inputs outside the tabulated/validity ranges.

---
title: "aircraft.rotorcraft_noise"
description: "Public API of phonometry.aircraft.rotorcraft_noise (auto-generated)."
sidebar:
  label: "rotorcraft_noise"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Rotorcraft noise by the hemisphere method (ECAC Doc 32 / NORAH2).

The ECAC Doc 32 rotorcraft-noise method describes a helicopter's highly directive
source with a **noise hemisphere**: one-third-octave-band sound pressure levels on
a spherical grid of azimuth `φ` and polar angle `θ` at a fixed 60 m reference
distance (at ICAO reference atmospheric conditions). Placing that source at a
receiver adds the propagation adjustment `ΔLp = ΔLs + ΔLa + ΔLg (+ ΔLd)`
(spherical spreading, atmospheric absorption, ground effect and — later — shielding).

This module provides the source and propagation primitives (clean-room, from the
NORAH2 guidance SC01.D1.5d, the basis of ECAC Doc 32):

* [`hemisphere_source_level`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#hemisphere_source_level) -- the interpolated source level `L(fc, φ, θ)`
  from a [`RotorcraftHemisphere`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#rotorcrafthemisphere), bilinear over the 10° grid (Eq. 13) with
  nearest-bin fill outside the measured coverage (Eq. 14/15).
* [`spherical_spreading_adjustment`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#spherical_spreading_adjustment) -- `ΔLs = −20·log10(r/60)` (Eq. 24).
* [`atmospheric_adjustment`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#atmospheric_adjustment) -- `ΔLa = −α(f)·(r−60)` with the ISO 9613-1
  pure-tone coefficient (Eq. 26/27), reusing
  [`air_attenuation`](/phonometry/reference/api/environment/air-absorption/#air_attenuation).
* [`ground_effect_adjustment`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#ground_effect_adjustment) -- `ΔLg` for a point source over an impedance
  plane (Chien-Soroka, Eq. 28-35) with the Delany-Bazley one-parameter impedance
  and the CNOSSOS flow-resistivity classes.

Source (clean-room): ECAC Doc 32, 1st ed.; NORAH2 rotorcraft-noise modelling
guidance (EASA.2020.FC.06 SC01.D1.5d), §A.3-A.4. The atmospheric term is validated
against the guidance Table 4 (one-third-octave attenuation per km at ICAO
reference conditions).

## atmospheric_adjustment

```python
atmospheric_adjustment(
    frequencies: NDArray[np.float64] | list[float],
    distance: float,
    *,
    temperature: float = 25.0,
    relative_humidity: float = 70.0,
    pressure: float = 101.325,
    reference_distance: float = 60.0,
) -> NDArray[np.float64]
```

Atmospheric-absorption adjustment `ΔLa` of the hemisphere level (Eq. 26/27).

The hemisphere already includes absorption out to the reference distance
`rh`, so only the excess path `r − rh` is corrected:
`ΔLa = −α(f)·(r − rh)` with the ISO 9613-1 pure-tone coefficient `α`
evaluated at the exact band centre (Eq. 26/27, ICAO reference atmosphere by
default). This matches the guidance Eq. 27 to 0.02 dB/km and the NORAH2
reference implementation. The guidance's alternative per-band mapping (SAE
method by Rickley et al., its Table 4) coincides below 3.15 kHz and deviates
by up to 2.2 dB/km at 8-10 kHz; for a path-dependent band mapping use
[`sae_band_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#sae_band_attenuation).

:::note
The printed guidance Eq. 27 pairs the coefficient `6.6928e-6` with
`fr,O = 630.7` Hz, which evaluates to nonsense (14.3 dB/km at 500 Hz
against Table 4's 3.1). The physically correct pairing (`6.6928e-6`
with the oxygen relaxation frequency, `1.3415e-6` with 630.7 Hz)
reproduces Table 4 and this implementation to 0.02 dB/km; do not
"fix" the code by transcribing the typo.
:::

Bands below the 50 Hz floor of the ISO 9613-1 tabulation (the NORAH grid
starts at 10 Hz) use the same analytic formulas; the advisory out-of-range
warning is suppressed because `α` is negligible there (Table 4 lists
0.0 dB/km for every band up to 50 Hz). The suppression only applies while
every band stays within the 10 kHz top of the NORAH grid; above that the
advisory warning propagates, since `α` is large and extrapolated.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | One-third-octave-band centre frequencies, in Hz. |
| `distance` | Slant distance `r`, in metres (`> 0`; below `rh` the adjustment is a small positive value, i.e. less absorption than the reference path). |
| `temperature` | Air temperature, in °C (default 25 °C, ICAO reference). |
| `relative_humidity` | Relative humidity, in % (default 70 %). |
| `pressure` | Ambient pressure, in kPa (default 101.325). |
| `reference_distance` | Hemisphere reference distance `rh`, in metres (default 60). Pass [`RotorcraftHemisphere.distance`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#rotorcrafthemisphere) when the data uses a non-standard polar distance. |

**Returns:** The adjustment `ΔLa` per band, in dB (added to the level, `<= 0` for `r >= rh`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a distance is not strictly positive. |

## ground_effect_adjustment

```python
ground_effect_adjustment(
    frequencies: NDArray[np.float64] | list[float],
    source_height: float,
    receiver_height: float,
    horizontal_distance: float,
    *,
    flow_resistivity: float | str = 'G',
) -> NDArray[np.float64]
```

Ground-effect adjustment `ΔLg` over an impedance plane (Eq. 28-35).

A point source over a locally-reacting impedance ground produces interference
between the direct and reflected rays. With the spherical reflection
coefficient `Q` (Chien-Soroka) and the Delany-Bazley impedance,
`ΔLg = 10·log10{1 + (r1/r2)²|Q|² + 2(r1/r2)|Q|·I}` (Eq. 29), where `I`
(Eq. 30) is the in-band interference factor.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | One-third-octave-band centre frequencies, in Hz. |
| `source_height` | Source height above the ground `hs`, in metres (clamped to `>= 0.1`). |
| `receiver_height` | Receiver height above the ground `hr`, in metres (clamped to `>= 0.1`). |
| `horizontal_distance` | Horizontal source-receiver distance `dp`, in metres (`> 0`). |
| `flow_resistivity` | Ground flow resistivity `σ` in Pa·s/m², or a CNOSSOS class letter `"A"`-`"H"`. The default `"G"` (20e6, hard surfaces) is the CNOSSOS class covering the paved surroundings typical of heliports; the guidance's own suggestions, concrete `σ = 65e6` for city areas and grass `σ = 200e3` for rural areas (§A.4.3), can be passed as numeric values. |

**Returns:** The adjustment `ΔLg` per band, in dB (added to the level).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs are invalid. |

## hemisphere_source_level

```python
hemisphere_source_level(
    hemisphere: RotorcraftHemisphere,
    azimuth_deg: float,
    polar_deg: float,
) -> NDArray[np.float64]
```

Interpolated source level `L(fc, φ, θ)` from a hemisphere (Eq. 13-15).

The grid is first gap-filled by nearest-bin constant-value extrapolation
(Eq. 14/15, computed once per hemisphere and cached), then the query is a
bilinear interpolation in the energy domain over the four neighbouring
azimuth/polar bins (Eq. 13). Filling the grid before interpolating keeps
partially-measured cells continuous with their fully-measured neighbours
(the valid corners still contribute) instead of snapping to a single bin.

Queries outside the grid clamp to the boundary node and edge-interpolate;
Eq. 14/15 taken literally would return the single nearest node, which
coincides on the boundary nodes but is discontinuous alongside them, so the
smoother clamp is intentional. Bands with no filled bin anywhere in the
grid return `NaN`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `hemisphere` | The [`RotorcraftHemisphere`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#rotorcrafthemisphere) source description. |
| `azimuth_deg` | Emission azimuth `φ`, in degrees. |
| `polar_deg` | Emission polar angle `θ`, in degrees. |

**Returns:** Band levels at `(φ, θ)`, in dB, shape `(F,)`.

## RotorcraftHemisphere

```python
RotorcraftHemisphere(
    frequencies: NDArray[np.float64],
    azimuth: NDArray[np.float64],
    polar: NDArray[np.float64],
    levels: NDArray[np.float64],
    distance: float = 60.0,
)
```

A rotorcraft noise hemisphere (ECAC Doc 32 §A.3.2).

One-third-octave-band sound pressure levels on a regular azimuth/polar grid at
the 60 m reference distance (ICAO reference atmosphere). Missing bins (outside
the measured coverage) are `NaN` and filled by nearest-bin extrapolation on
lookup.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Band centre frequencies, in Hz, shape `(F,)`. |
| `azimuth` | Azimuth angles `φ`, in degrees, shape `(A,)` (`-90` port … `+90` starboard). |
| `polar` | Polar angles `θ`, in degrees, shape `(P,)` (`0` forward … `180` rearward). |
| `levels` | Band levels, in dB, shape `(A, P, F)`. |
| `distance` | Reference distance, in metres (default 60). The standard NORAH database uses 60 m; when the data uses another polar distance (e.g. 70 m hover rings), pass this value as `reference_distance` to [`spherical_spreading_adjustment`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#spherical_spreading_adjustment) and [`atmospheric_adjustment`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#atmospheric_adjustment) so the propagation chain honours it. |

### RotorcraftHemisphere.plot()

```python
RotorcraftHemisphere.plot(ax: Axes | None = None, **kwargs: Any) -> Axes
```

Plot the hemisphere directivity for one band (polar section).

## spherical_spreading_adjustment

```python
spherical_spreading_adjustment(
    distance: float,
    *,
    reference_distance: float = 60.0,
) -> float
```

Spherical-spreading adjustment `ΔLs` of the hemisphere level (Eq. 24).

The hemisphere levels are defined at the reference distance `rh` (60 m in
the standard database), so at slant distance `r` the geometric spreading
adjustment is `ΔLs = −20·log10(r/rh)`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance` | Slant distance `r` from the rotorcraft to the observer, in metres (`> 0`). |
| `reference_distance` | Hemisphere reference distance `rh`, in metres (default 60). Pass [`RotorcraftHemisphere.distance`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/#rotorcrafthemisphere) when the data uses a non-standard polar distance (e.g. 70 m hover rings). |

**Returns:** The spreading adjustment `ΔLs`, in dB (added to the level).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a distance is not strictly positive. |

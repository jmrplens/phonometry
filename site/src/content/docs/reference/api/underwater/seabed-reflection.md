---
title: "underwater.seabed_reflection"
description: "Public API of phonometry.underwater.seabed_reflection (auto-generated)."
sidebar:
  label: "seabed_reflection"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Plane-wave reflection at the seabed (fluid-fluid Rayleigh model).

A plane wave in the water column (density `ρ1`, sound speed `c1`) striking a
fluid sediment half-space (`ρ2`, `c2`) reflects with the Rayleigh pressure
reflection coefficient (Medwin & Clay, Eq. 2.6.11a). Using the grazing angle
`φ` (measured from the interface), the angle of incidence from the normal is
`θ1 = 90° − φ`, Snell's law gives `sinθ2 = (c2/c1)·cosφ` and
`R = (ρ2·c2·sinφ − ρ1·c1·cosθ2) / (ρ2·c2·sinφ + ρ1·c1·cosθ2)`.

* [`critical_angle`](/phonometry/reference/api/underwater/seabed-reflection/#critical_angle) -- the critical grazing angle `φc = arccos(c1/c2)`
  (only when `c2 > c1`); below it the wave is totally reflected (`|R| = 1`).
* [`reflection_coefficient`](/phonometry/reference/api/underwater/seabed-reflection/#reflection_coefficient) -- the complex `R` per grazing angle.
* [`bottom_reflection_loss`](/phonometry/reference/api/underwater/seabed-reflection/#bottom_reflection_loss) -- the bottom loss `BL = −20·lg|R|` (dB),
  returned as a [`BottomLossResult`](/phonometry/reference/api/underwater/seabed-reflection/#bottomlossresult) with a `.plot()`.

Lossless fluid-fluid model (real `ρ`/`c`); sediment attenuation is out of
scope. Densities enter only through the impedance ratio, so any consistent unit
works (kg/m³ by convention).

## bottom_reflection_loss

```python
bottom_reflection_loss(
    grazing_angle: NDArray[np.float64] | list[float] | float,
    *,
    rho1: float = 1000.0,
    c1: float = 1500.0,
    rho2: float,
    c2: float,
) -> BottomLossResult
```

Bottom reflection loss `BL = −20·lg|R|` versus grazing angle (dB).

**Parameters**

| Name | Description |
| :--- | :--- |
| `grazing_angle` | Grazing angle(s) `φ` from the interface, in degrees. |
| `rho1` | Water density `ρ1` (default 1000 kg/m³). |
| `c1` | Sound speed in the water `c1`, in m/s (default 1500). |
| `rho2` | Sediment density `ρ2`. |
| `c2` | Sound speed in the sediment `c2`, in m/s. |

**Returns:** A [`BottomLossResult`](/phonometry/reference/api/underwater/seabed-reflection/#bottomlossresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs are invalid. |

## BottomLossResult

```python
BottomLossResult(
    grazing_angle: NDArray[np.float64],
    reflection_loss: NDArray[np.float64],
    reflection_coefficient: NDArray[np.complex128],
    critical_angle: float | None,
)
```

Bottom reflection loss versus grazing angle (fluid-fluid Rayleigh model).

**Attributes**

| Name | Description |
| :--- | :--- |
| `grazing_angle` | Grazing angles, in degrees. |
| `reflection_loss` | Bottom loss `BL = −20·lg\|R\|` per angle, in dB. |
| `reflection_coefficient` | Complex reflection coefficient per angle. |
| `critical_angle` | The critical grazing angle, in degrees, or `None` if the sediment is not faster than the water. |

### BottomLossResult.plot()

```python
BottomLossResult.plot(ax: Axes | None = None, **kwargs: Any) -> Axes
```

Plot the bottom loss versus grazing angle with the critical angle.

## critical_angle

```python
critical_angle(c1: float, c2: float) -> float
```

Critical grazing angle `φc = arccos(c1/c2)`, in degrees.

Defined only when the sediment is faster than the water (`c2 > c1`); at and
below this grazing angle the wave is totally reflected.

**Parameters**

| Name | Description |
| :--- | :--- |
| `c1` | Sound speed in the water, in m/s. |
| `c2` | Sound speed in the sediment, in m/s. |

**Returns:** The critical grazing angle, in degrees.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `c2 <= c1` (no critical angle exists). |

## reflection_coefficient

```python
reflection_coefficient(
    grazing_angle: NDArray[np.float64] | list[float] | float,
    *,
    rho1: float,
    c1: float,
    rho2: float,
    c2: float,
) -> NDArray[np.complex128]
```

Complex plane-wave pressure reflection coefficient at the seabed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `grazing_angle` | Grazing angle(s) `φ` from the interface, in degrees (`0` grazing to `90` normal incidence). |
| `rho1` | Water density `ρ1` (any consistent unit; kg/m³ by convention). |
| `c1` | Sound speed in the water `c1`, in m/s. |
| `rho2` | Sediment density `ρ2`. |
| `c2` | Sound speed in the sediment `c2`, in m/s. |

**Returns:** The complex reflection coefficient per grazing angle.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs are invalid. |

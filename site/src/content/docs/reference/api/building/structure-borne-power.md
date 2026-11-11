---
title: "building.measurement.structure_borne_power"
description: "Structure-borne sound power of building equipment (UNE-EN 15657:2018; ISO 9611)."
sidebar:
  label: "structure_borne_power"
---

Structure-borne sound power of building equipment (UNE-EN 15657:2018; ISO 9611).

Building service equipment (pumps, fans, boilers, sanitary appliances) injects
**structure-borne sound power** into the building structure it is fixed to.
EN 15657 measures it with the **reception-plate method**: the source is
mounted on a plate of known mass per unit area `m` and area `S` whose
structural loss factor `eta` is known, and the spatial-average vibratory
velocity level of the plate is measured.

The power a resonant plate dissipates equals
$P = \omega\, \eta\, (m S)\, \langle v^2 \rangle$, so the power
**injected into that reception plate** is, in one-third-octave bands
(Formula 14):

$$
L_\mathrm{Ws} = 10 \log_{10}\frac{2 \pi f \eta\, m S}{f_0 m_0 S_0} + L_\mathrm{v} - 60 \qquad \text{dB re 1 pW}
$$

with the references $f_0 = 1$ Hz, $m_0 = 1$ kg (printed as 1 kg;
the quantity it normalises is a mass per unit area, so the reference is
1 kg/m², see `docs/ERRATA.md`), $S_0 = 1$ m²;
the fixed `-60 dB` term is
$10 \log_{10}(v_0^2 / P_0)$ for the EN 15657 velocity reference
$v_0 = 10^{-9}$ m/s and $P_0 = 1$ pW. The spatial mean velocity
level is the energetic average over the `N` plate positions (Formula 12):

$$
L_\mathrm{v} = 10 \log_{10}\!\left( \frac{1}{N} \sum 10^{L_{\mathrm{v},i}/10} \right)
$$

and the plate loss factor follows from its structural reverberation time `Ts`
(Formula 13, identical to the ISO 10848 total loss factor):

$$
\eta = \frac{2.2}{f\, T_\mathrm{s}}
$$

**Formula (14) is plate-specific, not a source descriptor.** The same source
injects a different power into a different receiver; feeding `L_Ws` directly
into EN 12354-5 as a characteristic level mis-states the receiving-room level
by up to ~20 dB. EN 15657 derives the plate-independent source quantities from
two test plates: a *low-mobility* plate (its point mobility and loss factor
are unchanged by the source) and a *high-mobility* plate (loaded by the
source):

- the **equivalent blocked force level** (Formula 15, dB re
  $F_0 = 10^{-6}$ N):
  $L_\mathrm{Fb,eq} = L_\mathrm{Ws,low} - 10 \log_{10}( \operatorname{Re}\{Y_\mathrm{R,low,eq}\} / Y_0 )$
  with the measured low-mobility-plate mobility and $Y_0 = 1$
  m/(N.s);
- the **characteristic reception-plate power level** used by EN 12354-5
  (Formula 17), referred to the standard 10 cm concrete plate of
  characteristic mobility $Y_{\mathrm{R},\infty,\mathrm{low}} = 5 \cdot 10^{-6}$
  m/(N.s) (clause 7.2.4):
  $L_\mathrm{Wsn} = L_\mathrm{Fb,eq} + 10 \log_{10}( Y_{\mathrm{R},\infty,\mathrm{low}} / Y_0 )$;
- the **equivalent free velocity level** (Formula 18, dB re `1e-9 m/s`)
  from the high-mobility plate, and the **source mobility** from both
  (Formula 19). `L_Wsn` plus the mobility corrections of EN 12354-5
  Annex I (see [`phonometry.building.prediction.installed_structure_borne`](/phonometry/reference/api/building/installed-structure-borne/)) close
  the EN 15657 -> EN 12354-5 chain.

The source-side free velocity of ISO 9611:1996 is the direct-measurement
counterpart: velocity levels re $v_0 = 5 \cdot 10^{-8}$ m/s
(clause 7), averaged over
positions with the energy mean of its equation (9), implemented by
[`mean_free_velocity_level`](/phonometry/reference/api/building/structure-borne-power/#mean_free_velocity_level).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## characteristic_reception_plate_power

```python
characteristic_reception_plate_power(
    blocked_force_level: float | np.floating[Any] | np.integer[Any],
    *,
    characteristic_mobility: float = ...,
) -> float

characteristic_reception_plate_power(
    blocked_force_level: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
    *,
    characteristic_mobility: float = ...,
) -> NDArray[np.float64]

characteristic_reception_plate_power(
    blocked_force_level: NumericArrayLike,
    *,
    characteristic_mobility: float = ...,
) -> float | NDArray[np.float64]
```

Characteristic reception-plate power level (UNE-EN 15657:2018, Formula 17).

$L_\mathrm{Wsn} = L_\mathrm{Fb,eq} + 10 \log_{10}(|Y_{\mathrm{R},\infty,\mathrm{low}}|/Y_0)$
with the characteristic mobility of the standard 10 cm concrete reception
plate $Y_{\mathrm{R},\infty,\mathrm{low}} = 5 \cdot 10^{-6}$ m/(N.s) (clause 7.2.4) and
$Y_0 = 1$ m/(N.s). This is the plate-independent source power level
`L_Ws,n` that EN 12354-5 consumes (its Annex I mobility correction
[`phonometry.building.installed_power_from_reception_plate`](/phonometry/reference/api/building/installed-structure-borne/#installed_power_from_reception_plate) then
refers it to the actual receiver).

**Parameters**

| Name | Description |
| :--- | :--- |
| `blocked_force_level` | Equivalent blocked force level `L_Fb,eq` (per band), in dB re 1e-6 N (see [`equivalent_blocked_force_level`](/phonometry/reference/api/building/structure-borne-power/#equivalent_blocked_force_level)). |
| `characteristic_mobility` | `Y_R,inf,low`, in m/(N.s) (Default: 5e-6, clause 7.2.4). |

**Returns:** The characteristic power level `L_Wsn`, in dB re 1 pW. A `float` for a number, an array for a sequence or an array, a zero-dimensional one included.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive characteristic mobility. |
| TypeError | if `characteristic_mobility` is not a single number, or `blocked_force_level` holds a text or a value that is not a real number. |

## equivalent_blocked_force_level

```python
equivalent_blocked_force_level(
    power_level: float | np.floating[Any] | np.integer[Any],
    plate_mobility: complex | np.number[Any],
) -> float

equivalent_blocked_force_level(
    power_level: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
    plate_mobility: NumericArrayLike,
) -> NDArray[np.float64]

equivalent_blocked_force_level(
    power_level: float | np.floating[Any] | np.integer[Any],
    plate_mobility: Sequence[complex] | Sequence[np.number[Any]] | NDArray[np.bool_ | np.number[Any]],
) -> NDArray[np.float64]

equivalent_blocked_force_level(
    power_level: NumericArrayLike,
    plate_mobility: NumericArrayLike,
) -> float | NDArray[np.float64]
```

Equivalent blocked force level, squared (UNE-EN 15657:2018, Formula 15).

$L_\mathrm{Fb,eq} = L_\mathrm{Ws,low} - 10 \log_{10}(\operatorname{Re}\{Y_\mathrm{R,low,eq}\}/Y_0)$
in dB re $F_0 = 10^{-6}$ N,
from the power injected into the *low-mobility* reception plate
(Formula 14) and the equivalent point mobility of that plate (the
arithmetic mean of Re{Y} over the contact points, Formula 16).

**Parameters**

| Name | Description |
| :--- | :--- |
| `power_level` | Injected power level `L_Ws,low` (per band), in dB re 1 pW (see [`structure_borne_power_level`](/phonometry/reference/api/building/structure-borne-power/#structure_borne_power_level)). |
| `plate_mobility` | Equivalent plate mobility `Y_R,low,eq` (per band), in m/(N.s); complex values use their real part (Formula 16). |

**Returns:** The equivalent blocked force level `L_Fb,eq`, in dB re 1e-6 N. A `float` when `power_level` and `plate_mobility` are both numbers, an array when either is a sequence or an array, a zero-dimensional one included.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if `power_level` is not finite, `Re{plate_mobility}` is not positive and finite, or the two shapes do not broadcast together. |
| TypeError | if `power_level` holds a text or a value that is not a real number, or `plate_mobility` holds a text or a value that is not a number. |

## equivalent_free_velocity_level

```python
equivalent_free_velocity_level(
    power_level: float | np.floating[Any] | np.integer[Any],
    plate_mobility: complex | np.number[Any],
) -> float

equivalent_free_velocity_level(
    power_level: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
    plate_mobility: NumericArrayLike,
) -> NDArray[np.float64]

equivalent_free_velocity_level(
    power_level: float | np.floating[Any] | np.integer[Any],
    plate_mobility: Sequence[complex] | Sequence[np.number[Any]] | NDArray[np.bool_ | np.number[Any]],
) -> NDArray[np.float64]

equivalent_free_velocity_level(
    power_level: NumericArrayLike,
    plate_mobility: NumericArrayLike,
) -> float | NDArray[np.float64]
```

Equivalent free velocity level of the source (UNE-EN 15657:2018, Formula 18).

$L_\mathrm{vf,eq} = L_\mathrm{Ws,high} + 10 \log_{10}\left( |Y_\mathrm{R,high,eq}|^2 / (\operatorname{Re}\{Y_\mathrm{R,high,eq}\}\, Y_0) \right) + 60~\text{dB}$
in dB re 1e-9 m/s, from the power injected into the
*high-mobility* reception plate and its equivalent (complex) point
mobility. The plus sign follows the printed formula and the physics
($v_\mathrm{f}^2 = P |Y|^2 / \operatorname{Re}\{Y\}$); it is what makes
Formulae (15) and (18)
combine through Formula (19) into $|Y_\mathrm{S,eq}| = v_\mathrm{f} / F_\mathrm{b}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `power_level` | Injected power level `L_Ws,high` (per band), in dB re 1 pW. |
| `plate_mobility` | Equivalent plate mobility `Y_R,high,eq` (per band, complex), in m/(N.s). |

**Returns:** The equivalent free velocity level `L_vf,eq`, in dB re 1e-9 m/s. A `float` when `power_level` and `plate_mobility` are both numbers, an array when either is a sequence or an array, a zero-dimensional one included.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if `power_level` is not finite, `Re{plate_mobility}` is not positive and finite, or the two shapes do not broadcast together. |
| TypeError | if `power_level` holds a text or a value that is not a real number, or `plate_mobility` holds a text or a value that is not a number. |

## mean_free_velocity_level

```python
mean_free_velocity_level(levels: NumericArrayLike) -> float
```

Mean free velocity level over positions (ISO 9611:1996, equation (9)).

$\overline{L}_{vx} = 10 \log_{10}\left[ \frac{1}{N} \sum 10^{L_{vxi}/10} \right]$, the energy mean of the
free-velocity levels measured at the `N` contact/attachment points of
one direction `x`, each in dB re the ISO 9611 free-velocity reference
$v_0 = 5 \cdot 10^{-8}$ m/s (clause 7). The arithmetic is the
energetic average
(identical to EN 15657 Formula 12, [`spatial_mean_velocity_level`](/phonometry/reference/api/building/structure-borne-power/#spatial_mean_velocity_level));
only the reference differs.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Free velocity levels `Lvxi` at the `N` positions, in dB re 5e-8 m/s. |

**Returns:** The mean free velocity level, in dB re 5e-8 m/s.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an empty, multi-dimensional or non-finite input. |

## plate_loss_factor

```python
plate_loss_factor(
    reverberation_time: NumericArrayLike,
    *,
    frequency: float | np.floating[Any] | np.integer[Any],
) -> float

plate_loss_factor(
    reverberation_time: NumericArrayLike,
    *,
    frequency: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
) -> NDArray[np.float64]

plate_loss_factor(
    reverberation_time: NumericArrayLike,
    *,
    frequency: NumericArrayLike,
) -> float | NDArray[np.float64]
```

Plate loss factor $\eta = 2.2 / (f\, T_\mathrm{s})$ (EN 15657, Formula 13).

Estimated from the plate's structural reverberation time; identical to the
ISO 10848 total loss factor.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Band centre frequency `f`, in hertz (scalar or per band). |
| `reverberation_time` | Structural reverberation time `Ts`, in s. |

**Returns:** The loss factor `eta` (dimensionless) per band. A `float` for a number, an array for a sequence or an array, a zero-dimensional one included.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `frequency` or `reverberation_time` holds a text or a value that is not a real number. |

## reception_plate_power

```python
reception_plate_power(
    velocity_level: NumericArrayLike,
    mass_per_area: float,
    area: float,
    *,
    frequency: NumericArrayLike,
    loss_factor: NumericArrayLike | None = None,
    reverberation_time: NumericArrayLike | None = None,
) -> StructureBornePowerResult
```

Reception-plate injected structure-borne sound power (EN 15657, clause 7).

Provide the plate loss factor directly, or its structural reverberation
time `Ts` (from which $\eta = 2.2/(f\, T_\mathrm{s})$ is computed,
Formula 13).
The result is the power injected into *this* plate (Formula 14); see the
module docstring for the conversion chain to the EN 12354-5 source
quantities.

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_level` | Spatial mean plate velocity level `L_v` (per band), in dB re 1e-9 m/s (see [`spatial_mean_velocity_level`](/phonometry/reference/api/building/structure-borne-power/#spatial_mean_velocity_level)). |
| `frequency` | Band centre frequency `f`, in hertz (scalar or per band). |
| `mass_per_area` | Plate mass per unit area `m`, in kg/m^2 (> 0). |
| `area` | Plate area `S`, in m^2 (> 0). |
| `loss_factor` | Plate loss factor `eta` (per band), or `None` to derive it from `reverberation_time`. |
| `reverberation_time` | Structural reverberation time `Ts`, in s, used when `loss_factor` is `None`. |

**Returns:** The [`StructureBornePowerResult`](/phonometry/reference/api/building/structure-borne-power/#structurebornepowerresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if neither `loss_factor` nor `reverberation_time` is given, or if `velocity_level` or `loss_factor` is neither a scalar nor one value per band. |
| TypeError | if `frequency`, `loss_factor` or `velocity_level` holds a text or a value that is not a real number. |

## source_mobility_from_levels

```python
source_mobility_from_levels(
    free_velocity_level: float | np.floating[Any] | np.integer[Any],
    blocked_force_level: float | np.floating[Any] | np.integer[Any],
) -> float

source_mobility_from_levels(
    free_velocity_level: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
    blocked_force_level: NumericArrayLike,
) -> NDArray[np.float64]

source_mobility_from_levels(
    free_velocity_level: float | np.floating[Any] | np.integer[Any],
    blocked_force_level: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
) -> NDArray[np.float64]

source_mobility_from_levels(
    free_velocity_level: NumericArrayLike,
    blocked_force_level: NumericArrayLike,
) -> float | NDArray[np.float64]
```

Equivalent source mobility magnitude (UNE-EN 15657:2018, Formula 19).

$|Y_\mathrm{S,eq}|^2 / Y_0^2 = 10^{(L_\mathrm{vf,eq} - L_\mathrm{Fb,eq})/10} \cdot 10^{-6}$, the ratio
of the free-velocity (re 1e-9 m/s) and blocked-force (re 1e-6 N)
references makes the constant
$(10^{-9}/10^{-6})^2 = 10^{-6}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `free_velocity_level` | Equivalent free velocity level `L_vf,eq` (per band), in dB re 1e-9 m/s (Formula 10 or 18). |
| `blocked_force_level` | Equivalent blocked force level `L_Fb,eq` (per band), in dB re 1e-6 N (Formula 15). |

**Returns:** The source mobility magnitude `|Y_S,eq|`, in m/(N.s). A `float` when `free_velocity_level` and `blocked_force_level` are both numbers, an array when either is a sequence or an array, a zero-dimensional one included.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-finite level, or two shapes that do not broadcast together. |
| TypeError | if `blocked_force_level` or `free_velocity_level` holds a text or a value that is not a real number. |

## spatial_mean_velocity_level

```python
spatial_mean_velocity_level(levels: NumericArrayLike) -> float
```

Spatial-average velocity level over the plate (EN 15657, Formula 12).

$L_\mathrm{v} = 10 \log_{10}\left( \frac{1}{N} \sum 10^{L_{\mathrm{v},i}/10} \right)$,
the energetic average of the
per-position velocity levels.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Velocity levels `L_v,i` at the `N` positions, in dB. |

**Returns:** The spatial mean velocity level, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an empty, multi-dimensional or non-finite input. |
| TypeError | if `levels` holds a text or a value that is not a real number. |

## structure_borne_power_level

```python
structure_borne_power_level(
    velocity_level: float | np.floating[Any] | np.integer[Any],
    mass_per_area: float,
    area: float,
    loss_factor: float | np.floating[Any] | np.integer[Any],
    *,
    frequency: float | np.floating[Any] | np.integer[Any],
    reference_velocity: float = ...,
) -> float

structure_borne_power_level(
    velocity_level: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
    mass_per_area: float,
    area: float,
    loss_factor: NumericArrayLike,
    *,
    frequency: NumericArrayLike,
    reference_velocity: float = ...,
) -> NDArray[np.float64]

structure_borne_power_level(
    velocity_level: float | np.floating[Any] | np.integer[Any],
    mass_per_area: float,
    area: float,
    loss_factor: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
    *,
    frequency: NumericArrayLike,
    reference_velocity: float = ...,
) -> NDArray[np.float64]

structure_borne_power_level(
    velocity_level: float | np.floating[Any] | np.integer[Any],
    mass_per_area: float,
    area: float,
    loss_factor: float | np.floating[Any] | np.integer[Any],
    *,
    frequency: Sequence[float] | Sequence[np.floating[Any]] | Sequence[np.integer[Any]] | NDArray[np.bool_ | np.integer[Any] | np.floating[Any]],
    reference_velocity: float = ...,
) -> NDArray[np.float64]

structure_borne_power_level(
    velocity_level: NumericArrayLike,
    mass_per_area: float,
    area: float,
    loss_factor: NumericArrayLike,
    *,
    frequency: NumericArrayLike,
    reference_velocity: float = ...,
) -> float | NDArray[np.float64]
```

Structure-borne power injected into the reception plate (EN 15657, Formula 14).

The power a resonant reception plate dissipates, expressed as a level re
1 pW:

$$
L_\mathrm{Ws} = 10 \log_{10}\frac{2 \pi f \eta\, m S}{f_0 m_0 S_0} + L_\mathrm{v} + 10 \log_{10}\frac{v_0^2}{P_0}
$$

With the EN 15657 reference $v_0 = 10^{-9}$ m/s the last term is
-60 dB.

:::note
This is the power injected into *this particular plate*, not a source
descriptor: do **not** feed it into EN 12354-5 as the characteristic
level `L_Ws,c`. Convert it first via
[`equivalent_blocked_force_level`](/phonometry/reference/api/building/structure-borne-power/#equivalent_blocked_force_level) (Formula 15) and
[`characteristic_reception_plate_power`](/phonometry/reference/api/building/structure-borne-power/#characteristic_reception_plate_power) (Formula 17), then apply
the EN 12354-5 Annex I mobility correction
([`phonometry.building.installed_power_from_reception_plate`](/phonometry/reference/api/building/installed-structure-borne/#installed_power_from_reception_plate)).
:::

**Parameters**

| Name | Description |
| :--- | :--- |
| `velocity_level` | Spatial mean plate velocity level `L_v` (scalar or per band), in dB re `v0`. |
| `frequency` | Band centre frequency `f`, in hertz (scalar or array). |
| `mass_per_area` | Plate mass per unit area `m`, in kg/m^2 (> 0). |
| `area` | Plate area `S`, in m^2 (> 0). |
| `loss_factor` | Plate loss factor `eta` (scalar or per band, > 0). |
| `reference_velocity` | Velocity reference `v0` (Default: 1e-9 m/s). |

**Returns:** The structure-borne sound power level `L_Ws`, in dB re 1 pW. A `float` when `velocity_level`, `loss_factor` and `frequency` are all numbers, an array when one of them is a sequence or an array, a zero-dimensional one included.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive mass, area or reference, a frequency or loss factor that is not positive and finite, a non-finite velocity level, or per-band inputs whose shapes do not broadcast together. |
| TypeError | if `area`, `mass_per_area` or `reference_velocity` is not a single number, or `frequency`, `loss_factor` or `velocity_level` holds a text or a value that is not a real number. |

## StructureBornePowerResult

```python
StructureBornePowerResult(
    power_level: NDArray[np.float64],
    velocity_level: NDArray[np.float64],
    loss_factor: NDArray[np.float64],
    mass_per_area: float,
    area: float,
    frequencies: NDArray[np.float64] | None = None,
)
```

Structure-borne sound power injected into a reception plate (EN 15657).

The power level is specific to the measured plate; derive the
plate-independent source quantities with
[`equivalent_blocked_force_level`](/phonometry/reference/api/building/structure-borne-power/#equivalent_blocked_force_level) and
[`characteristic_reception_plate_power`](/phonometry/reference/api/building/structure-borne-power/#characteristic_reception_plate_power) before using EN 12354-5.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Band centre frequencies, in hertz, or `None`. |
| `power_level` | Reception-plate injected power level `L_Ws` per band, in dB re 1 pW (Formula 14). |
| `velocity_level` | Spatial mean plate velocity level `L_v` per band, dB. |
| `loss_factor` | Plate loss factor `eta` per band. |
| `mass_per_area` | Plate mass per unit area `m`, in kg/m^2. |
| `area` | Plate area `S`, in m^2. |

### StructureBornePowerResult.plot()

```python
StructureBornePowerResult.plot(
    ax: Axes | None = None,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the characteristic structure-borne power level per band.

Requires matplotlib (the `[plot]` extra); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `language` | The language of the labels: `"en"` or `"es"`. |

### StructureBornePowerResult.report()

```python
StructureBornePowerResult.report(
    path: str | os.PathLike[str],
    *,
    metadata: ReportMetadata | None = None,
    engine: Literal['reportlab'] = 'reportlab',
    verbose: bool = False,
    language: Literal['en', 'es'] = 'en',
) -> str
```

Render an EN 15657 structure-borne sound power fiche to `path`.

Writes a one-page reception-plate characterization sheet: the
standard-basis line naming the UNE-EN 15657:2018 reception-plate method
(Formula 14), an optional metadata header (client, source equipment,
test environment, instrumentation, climate, date), a per-band table
(nominal octave/one-third-octave frequency, the spatial mean plate
velocity level `Lv` and the injected structure-borne sound power
level `L_Ws`), the `L_Ws(f)` spectrum with a nominal band axis, the
boxed band-summed total `L_Ws` (dB re 1 pW) with the plate mass per
area `m` and area `S`, an optional verdict row against a declared
limit, and a basis strip stating Formula 14 and the conversion to the
plate-independent source quantities (Formulae 15/17) required before
EN 12354-5.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata) supplying the header (`client`, `specimen` the source equipment, `test_room` the test environment, `instrumentation`, `temperature_c`, `relative_humidity_percent`, `pressure`, `test_date`), the footer identity (`laboratory`, `operator`, `report_id`, `notes`) and, via `requirement`, a declared upper limit on the total `L_Ws` (lower is better). The plate mass and area come from the result itself. |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | When `True` the per-band table adds the plate loss factor `eta` column. |
| `language` | Fiche language: `"en"` (default) or `"es"`. |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"` or `language` is unknown. |
| ImportError | If reportlab (or, for the figure, matplotlib) is not installed (the `[report]` extra). |

### StructureBornePowerResult.total_level

*property*

Band-summed power level $10 \log_{10}(\sum 10^{0.1 L_\mathrm{Ws}})$,
in dB.

---
title: "materials.absorbers.porous"
description: "Porous-material models and resonant sheet impedances."
sidebar:
  label: "porous"
---

Porous-material models and resonant sheet impedances.

Two complementary building blocks, all in the $e^{+j \omega t}$
time convention with the forward wave carried by $e^{-j k x}$ (so a
passive medium has $\operatorname{Im}(k) < 0$):

* **Equivalent-fluid models** for the characteristic impedance `Zc` and the
  complex wavenumber `k` of a rigid-frame porous material:

  - the one-parameter **Delany-Bazley** power law in the absorber variable
    $X = \rho_0 f / \sigma$ (Mechel, *Formulas of Acoustics* 2e,
    Sect. G.11 Eqs. (1)-(2); Bies, Hansen & Howard, *Engineering Noise
    Control* 5e, Appendix D Eqs. (D.22)-(D.23) and Table D.1; Hopkins,
    *Sound Insulation*, Eqs. (1.171)-(1.174)), stated valid for
    $0.01 < X < 1.0$ and porosity close to one. Table D.1 also
    provides coefficient sets fitted to polyester (Garai & Pompoli 2005)
    and to foams (Dunn & Davern 1986, Wu 1988), exposed here as presets.
  - the **Miki** modification, regressed on the same Delany-Bazley data under
    a positive-real (passivity) constraint so the model stays well behaved
    below the fit range (Miki 1990, *J. Acoust. Soc. Jpn (E)* 11(1),
    Eqs. (30)-(34), in the variable $f / \sigma$).
  - the five-parameter **Johnson-Champoux-Allard (JCA)** semi-phenomenological
    model with flow resistivity, porosity, tortuosity and the viscous/thermal
    characteristic lengths (Cox & D'Antonio, *Acoustic Absorbers and
    Diffusers* 3e, Eqs. (6.19)-(6.25); Attenborough & Van Renterghem,
    *Predicting Outdoor Sound* 2e, Eqs. (5.13)-(5.14)). The returned
    equivalent-fluid density and bulk modulus are the surface-normalised
    quantities (they absorb the porosity), so
    $Z_\mathrm{c} = \sqrt{\rho_\mathrm{e} K_\mathrm{e}}$ and
    $k = \omega \sqrt{\rho_\mathrm{e} / K_\mathrm{e}}$ hold for every model.
  - the **limp-frame** correction of any of the three rigid-frame models
    (Allard & Atalla, *Propagation of Sound in Porous Media* 2e, Sect. 11.3.4,
    Eqs. (11.53)-(11.55), printed pp. 251-253): a light frame is dragged along
    by the pore fluid, so its inertia has to be carried by the equivalent
    fluid. Only the effective density changes; the bulk modulus is the
    rigid-frame one. See [`limp_frame`](/phonometry/reference/api/materials/porous/#limp_frame) and
    [`decoupling_frequency`](/phonometry/reference/api/materials/porous/#decoupling_frequency).

* **Resonant sheets**: the perforated-plate impedance
  uses the end-corrected air-plug mass and the visco-thermal surface
  resistance (Cox & D'Antonio Eqs. (7.6)/(7.12)/(7.21), end-correction
  variants of Table 7.1); the microperforated plate follows Maa's exact
  short-tube impedance (Maa 1998, *J. Acoust. Soc. Am.* 104(5), Eq. (2),
  with the Eq. (5) end corrections; reproduced as Cox & D'Antonio
  Eqs. (7.33)-(7.35) and built on the same Bessel kernel as Mechel
  Sect. G.3); the membrane is the limp surface
  mass $j \omega m$ (Cox & D'Antonio Eq. (7.14); Bies Eq. (D.96)).
  Each sheet is closed by the shallow-cavity resonance it is designed
  around, [`helmholtz_resonance_frequency`](/phonometry/reference/api/materials/porous/#helmholtz_resonance_frequency) for a perforate and
  [`membrane_resonance_frequency`](/phonometry/reference/api/materials/porous/#membrane_resonance_frequency) for a membrane.

The air all of them propagate through is described by [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid),
which carries the six quantities a visco-thermal model can need (speed of
sound, density, viscosity, Prandtl number, ratio of specific heats and static
pressure) with the values these models were published with. The narrow-channel
models of [`slow_sound`](/phonometry/reference/api/materials/slow-sound/) and
[`metadiffuser`](/phonometry/reference/api/materials/metadiffuser/) take it as a single
argument.

These are the elements a multilayer absorber is assembled from; declaring a
stack of them and solving it with the transfer matrix is the subject of
[`layered`](/phonometry/reference/api/materials/layered/).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## airflow_resistivity_from_bulk_density

```python
airflow_resistivity_from_bulk_density(
    bulk_density_kg_m3: float,
    *,
    fit: FibreResistivityFit,
) -> float
```

Airflow resistivity of a mineral wool from its bulk density (Eq. 1.165).

$r = k_1 \rho_\mathrm{bulk}^{1+k_2} / d_\mathrm{fibre}^2$, the
empirical relation Hopkins gives after Bies (1988) and Nichols (1947), with
the fibre diameter in micrometres.

The relation is a straight line through measured points on a log-log plot,
not a law, so it belongs to the material the points came from. Passing a
bulk density outside the range the fit was made over emits a
[`PorousAbsorberWarning`](/phonometry/reference/api/materials/porous/#porousabsorberwarning) naming both.

**Parameters**

| Name | Description |
| :--- | :--- |
| `bulk_density_kg_m3` | Bulk density of the wool, in kg/m3 (> 0). |
| `fit` | The published `k1`, `k2` pair to use, such as [`ROCK_WOOL_LONGITUDINAL_FIT`](/phonometry/reference/api/materials/porous/#rock_wool_longitudinal_fit). |

**Returns:** The airflow resistivity `r`, in Pa s/m2.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive density. |

## decoupling_frequency

```python
decoupling_frequency(
    flow_resistivity: float,
    *,
    porosity: float,
    frame_density: float,
) -> float
```

Zwikker-Kosten decoupling frequency `Fd` of a porous frame.

$F_\mathrm{d} = \sigma \phi^2 / (2 \pi \rho_1)$ (Allard & Atalla 2e,
Sect. 11.3.4, printed p. 251; the same closed form as their Eq. (6.90),
printed p. 126).
Above `Fd` the visco-inertial coupling between the pore fluid and the
frame is too weak for the acoustic wave to shake the frame, so the
rigid-frame equivalent fluid of [`johnson_champoux_allard`](/phonometry/reference/api/materials/porous/#johnson_champoux_allard) applies;
below it the frame moves and the limp correction of [`limp_frame`](/phonometry/reference/api/materials/porous/#limp_frame)
matters.

**Parameters**

| Name | Description |
| :--- | :--- |
| `flow_resistivity` | Airflow resistivity `sigma`, in Pa s/m2 (> 0). |
| `porosity` | Open porosity `phi` (0 \< phi \<= 1). |
| `frame_density` | Bulk density of the frame `rho1`, in kg/m3 (> 0): the mass of solid per unit volume of material, i.e. the density of the sample as weighed, not the density of the material the fibres are made of. |

**Returns:** The decoupling frequency `Fd`, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a porosity above 1. |

## delany_bazley

```python
delany_bazley(
    frequency: ArrayLike,
    flow_resistivity: float,
    *,
    coefficients: str | tuple[float, ...] = 'delany_bazley',
    fluid: Fluid = ...,
) -> PorousMediumResult
```

Delany-Bazley one-parameter porous model (power laws in `X`).

$Z_\mathrm{c} = \rho c (1 + C_1 X^{-C_2} - j C_3 X^{-C_4})$ and
$k = (\omega/c)(1 + C_5 X^{-C_6} - j C_7 X^{-C_8})$ with
$X = \rho f / \sigma$
(Mechel 2e Sect. G.11 Eqs. (1)-(2); Bies 5e Eqs. (D.22)-(D.23) with the
Table D.1 coefficients; Hopkins Eqs. (1.171)-(1.173)). A
[`PorousAbsorberWarning`](/phonometry/reference/api/materials/porous/#porousabsorberwarning) is raised when any `X` leaves the stated
$0.01 < X < 1.0$ validity range (Hopkins Eq. (1.174)); the values
are still returned.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `flow_resistivity` | Airflow resistivity `sigma`, in Pa s/m2. |
| `coefficients` | Preset name from [`DELANY_BAZLEY_COEFFICIENTS`](/phonometry/reference/api/materials/porous/#delany_bazley_coefficients) (`"delany_bazley"` rockwool/fibreglass default, `"garai_pompoli"` polyester, `"dunn_davern"` / `"wu"` foams) or an explicit `(C1..C8)` tuple. |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air), the air this model was published with). Pass a computed one, such as `fluids.air(temperature_c=30.0, relative_humidity_percent=70.0)`, to work in the air of the room. |

**Returns:** A [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult).

## DELANY_BAZLEY_COEFFICIENTS

*Constant* (`dict`).

```python
DELANY_BAZLEY_COEFFICIENTS = {'delany_bazley': (0.0571, 0.754, 0.087, 0.732, 0.0978, 0.7, 0.189, 0.595), 'garai_pompoli': (0.078, 0.623, 0.074, 0.66, 0.159, 0.571, 0.121, 0.53), 'dunn_davern': (0.114, 0.369, 0.0985, 0.758, 0.168, 0.715, 0.136, 0.491), 'wu': (0.212, 0.455, 0.105, 0.607, 0.163, 0.592, 0.188, 0.544)}
```

## DELANY_BAZLEY_VALIDITY

*Constant* (`tuple`).

```python
DELANY_BAZLEY_VALIDITY = (0.01, 1.0)
```

## fibre_characteristic_lengths

```python
fibre_characteristic_lengths(
    fibre_radius_m: float,
    *,
    bulk_density_kg_m3: float,
    fibre_density_kg_m3: float,
) -> FibreCharacteristicLengths
```

Both characteristic lengths of a fibrous layer, from its geometry.

Allard & Atalla Eqs. (5.29) and (5.30), PDF page 91 (printed p. 81), model
the fibres as infinitely long cylinders of radius `R` and give, for a
porosity close to 1,

$$
\Lambda = \frac{1}{2 \pi L R} \qquad \Lambda' = \frac{1}{\pi L R} = 2 \Lambda
$$

where `L` is the total length of fibre per unit volume. Nobody measures
`L`, so it is eliminated here through its own definition, which for
cylinders is $\rho_\mathrm{bulk} = \rho_\mathrm{fibre} \pi R^2 L$,
leaving $\Lambda = R \rho_\mathrm{fibre} / (2 \rho_\mathrm{bulk})$
from three numbers a table does print. That substitution is arithmetic on
the definition and not a second model.

This is a different model from [`viscous_characteristic_length`](/phonometry/reference/api/materials/porous/#viscous_characteristic_length), not a
second opinion on the same one, and on Hopkins' own rock wool the two drift
apart with density: the cylinder model is the lower estimate throughout, by
a factor of 1,4 at 38 kg/m3 and 1,9 at 155 kg/m3. Which to prefer is a
question about the material, and neither is a substitute for measuring it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fibre_radius_m` | Fibre radius `R`, in metres (> 0). A table that prints a diameter in micrometres wants half of it, divided by a million. |
| `bulk_density_kg_m3` | Bulk density of the layer, in kg/m3 (> 0), below the fibre density: the ratio of the two is the fibre volume fraction, and Eqs. (5.29) and (5.30) are stated for a porosity close to 1. |
| `fibre_density_kg_m3` | Density of the fibre itself, in kg/m3 (> 0). |

**Returns:** The viscous and thermal lengths, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input, or a bulk density at or above the fibre density, which leaves no pore for a length to describe. |

## FibreCharacteristicLengths

```python
FibreCharacteristicLengths(
    viscous_length_m: ForwardRef('float'),
    thermal_length_m: ForwardRef('float'),
)
```

The two characteristic lengths of a fibrous layer, in metres.

## FibreResistivityFit

```python
FibreResistivityFit(
    k1: ForwardRef('float'),
    k2: ForwardRef('float'),
    fibre_diameter_um: ForwardRef('float'),
    bulk_density_range_kg_m3: ForwardRef('tuple[float, float]'),
    direction: ForwardRef('str'),
    source: ForwardRef('str'),
)
```

A published `k1`, `k2` pair of Hopkins Eq. (1.165), and its range.

The pair is not a property of mineral wool in general: `k1` belongs to a
material manufactured in a particular way and `k2` to how its fibres are
oriented, so the fit carries the fibre diameter it was made at and the
bulk-density range it was fitted over, and using it outside that range is
announced rather than silent.

**Attributes**

| Name | Description |
| :--- | :--- |
| `k1` | The constant of the manufacture. |
| `k2` | The exponent of the fibre orientation. |
| `fibre_diameter_um` | Average fibre diameter of the fitted material, in micrometres, which is the unit Eq. (1.165) is written in. |
| `bulk_density_range_kg_m3` | The `(low, high)` the fit was made over. |
| `direction` | `"lateral"` in the plane of the sheet or `"longitudinal"` through it. Mineral wool is anisotropic and the lateral resistivity is the lower of the two. |
| `source` | Document, table or equation, PDF page and printed folio. |

## helmholtz_resonance_frequency

```python
helmholtz_resonance_frequency(
    *,
    cavity_depth: float,
    plate_thickness: float,
    hole_radius: float,
    open_area: float,
    end_correction: float | None = None,
    speed_of_sound: float = 343.0,
) -> float
```

Resonance of a perforated sheet over a shallow cavity (closed form).

$f_0 = (c / 2 \pi) \sqrt{\varepsilon / (t' d)}$ with the
end-corrected plug length $t' = t + 2 \delta a$ (Cox & D'Antonio
3e, Eqs. (7.4)/(7.6), valid for $k d \ll 1$).

**Parameters**

| Name | Description |
| :--- | :--- |
| `cavity_depth` | Cavity depth `d`, in metres. |
| `plate_thickness` | Plate thickness `t`, in metres. |
| `hole_radius` | Hole radius `a`, in metres. |
| `open_area` | Fractional open area `eps` (0..1). |
| `end_correction` | End-correction factor `delta` per end; default [`perforation_end_correction`](/phonometry/reference/api/materials/porous/#perforation_end_correction) of `eps`. |
| `speed_of_sound` | Speed of sound `c` in fluid, in m/s. |

**Returns:** Resonance frequency `f0`, in hertz.

## johnson_champoux_allard

```python
johnson_champoux_allard(
    frequency: ArrayLike,
    flow_resistivity: float,
    *,
    porosity: float,
    tortuosity: float,
    viscous_length: float,
    thermal_length: float,
    fluid: Fluid = ...,
) -> PorousMediumResult
```

Johnson-Champoux-Allard five-parameter rigid-frame model.

Effective density (Cox & D'Antonio 3e, Eq. (6.19)):

$$
\rho_\mathrm{e} = \frac{T \rho}{\phi} \left[1 + \frac{\sigma \phi}{j \omega \rho T} \sqrt{1 + \frac{4 j T^2 \eta \rho \omega}{\sigma^2 L^2 \phi^2}} \right]
$$

and effective bulk modulus (Eq. (6.20)):

$$
K_\mathrm{e} = \frac{\gamma P_0 / \phi}{\gamma - (\gamma - 1) \left[1 + \frac{8 \eta}{j {L'}^2 \mathrm{Pr}\, \omega \rho} \sqrt{1 + \frac{j \rho \omega \mathrm{Pr}\, {L'}^2}{16 \eta}} \right]^{-1}}
$$

with tortuosity `T`, porosity `phi`, viscous/thermal characteristic
lengths `L` / `L'`; then $Z_\mathrm{c} = \sqrt{K_\mathrm{e} \rho_\mathrm{e}}$ and
$k = \omega \sqrt{\rho_\mathrm{e} / K_\mathrm{e}}$ (Eqs. (6.24)-(6.25)). Both
quantities are surface-normalised (the $1/\phi$ factors are
included). The model has the exact limits
$j \omega \rho_\mathrm{e} \to \sigma$ as $\omega \to 0$ and
$\rho_\mathrm{e} \to (T \rho / \phi)(1 + (1 - j) \delta_v / L)$ as
$\omega \to \infty$ (Johnson et al. 1987), pinned in the tests.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `flow_resistivity` | Airflow resistivity `sigma`, in Pa s/m2. |
| `porosity` | Open porosity `phi` (0 \< phi \<= 1). |
| `tortuosity` | High-frequency tortuosity $T = \alpha_\infty$ (>= 1). |
| `viscous_length` | Viscous characteristic length `L`, in metres. |
| `thermal_length` | Thermal characteristic length `L'`, in metres (physically $L' \ge L$). |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air), the air this model was published with). Pass a computed one, such as `fluids.air(temperature_c=30.0, relative_humidity_percent=70.0)`, to work in the air of the room. |

**Returns:** A [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult).

## limp_frame

```python
limp_frame(
    medium: PorousMediumResult,
    frame_density: float,
    *,
    porosity: float = 1.0,
) -> PorousMediumResult
```

Limp-frame correction of a rigid-frame equivalent fluid (A&A 11.3.4).

A light frame (aeronautic-grade fibreglass, felts, screens) is dragged
along by the pore fluid instead of standing still, and the rigid-frame
models of [`delany_bazley`](/phonometry/reference/api/materials/porous/#delany_bazley), [`miki`](/phonometry/reference/api/materials/porous/#miki) and
[`johnson_champoux_allard`](/phonometry/reference/api/materials/porous/#johnson_champoux_allard) have no way to carry that inertia.
Neglecting the stiffness of the frame altogether in the Biot mixed
pressure-displacement formulation leaves an equivalent fluid with the same
bulk modulus and a corrected effective density (Allard & Atalla 2e,
Eqs. (11.53)-(11.55), printed pp. 252-253, after Panneton 2007):

$$
\rho_{\mathrm{limp}} = \frac{\rho_\mathrm{t} \rho_{\mathrm{eq}} - \rho_0^2} {\rho_\mathrm{t} + \rho_{\mathrm{eq}} - 2 \rho_0}
$$

with `rho_eq` the rigid-frame effective density of *medium*, `rho0`
the density of the pore fluid and $\rho_\mathrm{t} = \rho_1 + \phi \rho_0$
the apparent total density of the material. What anchors this
expression is the printed
equation itself, transcribed term by term; Allard & Atalla tabulate no
computed limp density anywhere, so there are no published digits to check
against. The book also states two exact limits in prose, and both are
verified, but they are weaker than they look: neither pins the
$\rho_0^2$ and $2 \rho_0$ terms, since a sign-flipped
variant of Eq. (11.55) satisfies both of them (and even the
$1/\rho_1$ decay of the heavy-frame residual).
They corroborate the transcription rather than determine it:

* **heavy frame**: as $\rho_1 \to \infty$ the correction vanishes
  and the rigid-frame result is recovered (the book's own reading of
  Eq. (11.55));
* **low frequency**: since
  $\rho_{\mathrm{eq}} \to \sigma / (j \omega)$ as
  $\omega \to 0$ (Eq. (5.37)),
  $\rho_{\mathrm{limp}} \to \rho_\mathrm{t}$, a finite real density, where
  the rigid-frame model diverges. The rigid frame forbids rigid-body
  motion of the sample; the limp one allows it, which is why the two
  differ mainly
  at low frequency and why the limp model is the right one for an
  unconstrained sample in an impedance tube.

The corrected medium is a drop-in
[`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult), so it can be handed to
[`PorousLayer`](/phonometry/reference/api/materials/layered/#porouslayer) inside [`layered_absorber`](/phonometry/reference/api/materials/layered/#layered_absorber) exactly like the
rigid-frame one.

Use [`decoupling_frequency`](/phonometry/reference/api/materials/porous/#decoupling_frequency) to see where the frame stops following the
fluid and [`limp_frame_applicable`](/phonometry/reference/api/materials/porous/#limp_frame_applicable) for the published bulk-modulus
rule of thumb on when the frame may be treated as limp at all.

**Parameters**

| Name | Description |
| :--- | :--- |
| `medium` | A rigid-frame [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult) (its `effective_density` is `rho_eq` and its `bulk_modulus` is kept). |
| `frame_density` | Bulk density of the frame `rho1`, in kg/m3 (> 0). |
| `porosity` | Open porosity `phi` (0 \< phi \<= 1, Default: 1,0, the high-porosity assumption of the one-parameter models). |

**Returns:** A [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult) with model `"limp_frame(<base model>)"`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a porosity above 1. |

## limp_frame_applicable

```python
limp_frame_applicable(
    frame_bulk_modulus: float,
    *,
    criterion: str = 'doutres',
    fluid_bulk_modulus: float = 101325.0,
) -> bool
```

Whether the limp-frame model may be used, by published rule of thumb.

Both published criteria compare the bulk modulus of the frame *in vacuum*
`K_c` with that of the fluid in the pores `K_f` (Allard & Atalla 2e,
printed pp. 253-254): Beranek (1947) requires
$\lvert K_c/K_\mathrm{f} \rvert < 0.05$, and the frame structural
interaction study of Doutres et al. (2007) relaxes it to
$\lvert K_c/K_\mathrm{f} \rvert < 0.2$. With `K_f` taken as the
isothermal bulk modulus of fluid, $P_0 = 101.3$ kPa, the relaxed
criterion is the book's statement that
"the limp model is applicable for materials having a bulk modulus lower
than 20 kPa". Neither criterion accounts for boundary or mounting
conditions, and the book notes that a thin light foam decoupled from a
vibrating structure by an air gap behaves limply well above the limit.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frame_bulk_modulus` | Bulk modulus of the frame in vacuum `K_c`, in Pa (>= 0; pass `abs(K_c)` for a complex modulus). |
| `criterion` | Key into [`LIMP_FRAME_CRITERIA`](/phonometry/reference/api/materials/porous/#limp_frame_criteria), `"doutres"` (Default, 0,2) or `"beranek"` (0,05). |
| `fluid_bulk_modulus` | Bulk modulus of the pore fluid `K_f`, in Pa (Default: 101 325, the isothermal value for fluid). |

**Returns:** `True` when $\lvert K_c/K_\mathrm{f} \rvert$ does not exceed the threshold.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a negative modulus or an unknown criterion. |

## LIMP_FRAME_CRITERIA

*Constant* (`dict`).

```python
LIMP_FRAME_CRITERIA = {'beranek': 0.05, 'doutres': 0.2}
```

## membrane_impedance

```python
membrane_impedance(
    frequency: ArrayLike,
    *,
    surface_density: float,
    resistance: float = 0.0,
) -> Complex
```

Transfer impedance of a limp impervious membrane.

$z = r + j \omega m$ - the surface-mass reactance (Cox & D'Antonio
3e, Eq. (7.14); Bies 5e Eq. (D.96)) plus an optional empirical
resistance for the internal/fixing losses.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `surface_density` | Mass per unit area `m`, in kg/m2. |
| `resistance` | Series flow resistance `r`, in Pa s/m (default 0). |

**Returns:** Complex transfer impedance `z`, in Pa s/m.

## membrane_resonance_frequency

```python
membrane_resonance_frequency(
    *,
    surface_density: float,
    cavity_depth: float,
    isothermal: bool = False,
    fluid: Fluid = ...,
) -> float
```

Mass-spring resonance of a membrane over a shallow cavity.

$f_0 = (1 / 2 \pi) \sqrt{\rho c^2 / (m d)}$ for an adiabatic air
spring - numerically the classical $f_0 = 60 / \sqrt{m d}$ (Cox &
D'Antonio 3e, Eq. (7.9)). With `isothermal=True` the spring stiffness
drops by `gamma`, giving $\sim 50 / \sqrt{m d}$ (Eq. (7.10)),
the porous-filled cavity case below about 500 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `surface_density` | Membrane mass per unit area `m`, in kg/m2. |
| `cavity_depth` | Cavity depth `d`, in metres. |
| `isothermal` | Use the isothermal air-spring stiffness. |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air), the air this model was published with). Pass a computed one, such as `fluids.air(temperature_c=30.0, relative_humidity_percent=70.0)`, to work in the air of the room. |

**Returns:** Resonance frequency `f0`, in hertz.

## microperforated_plate_impedance

```python
microperforated_plate_impedance(
    frequency: ArrayLike,
    *,
    thickness: float,
    hole_radius: float,
    open_area: float,
    end_correction: float = 0.85,
    fluid: Fluid = ...,
) -> Complex
```

Transfer impedance of a microperforated plate (Maa's exact model).

The specific impedance of one submillimetre hole is the exact short-tube
result (Maa 1998, Eq. (2); reproduced as Cox & D'Antonio 3e Eq. (7.33)
and the same Bessel kernel as Mechel 2e Sect. G.3):

$$
z_1 = j \omega \rho t \left[1 - \frac{2}{x \sqrt{-j}} \frac{J_1(x \sqrt{-j})}{J_0(x \sqrt{-j})}\right]^{-1}
$$

with the perforate constant $x = a \sqrt{\rho \omega / \eta}$.
Dividing by the open area and adding Maa's Eq. (5) end corrections - the
Rayleigh/Ingard surface resistance
$\sqrt{2 \omega \rho \eta} / (2 \varepsilon)$ and the piston
end-correction reactance
$j \omega \rho (2 \delta a) / \varepsilon$ ($0.85 d$ total
for the default $\delta = 0.85$ per end) - gives the sheet
transfer impedance (Cox & D'Antonio Eq. (7.35)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `thickness` | Plate thickness `t`, in metres. |
| `hole_radius` | Hole radius `a`, in metres (submillimetre for a genuine microperforated design). |
| `open_area` | Fractional open area `eps` (0..1). |
| `end_correction` | End-correction factor `delta` per end (default 0.85, the isolated-orifice value used by Maa). |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air), the air this model was published with). Pass a computed one, such as `fluids.air(temperature_c=30.0, relative_humidity_percent=70.0)`, to work in the air of the room. |

**Returns:** Complex transfer impedance `z`, in Pa s/m.

## miki

```python
miki(
    frequency: ArrayLike,
    flow_resistivity: float,
    *,
    fluid: Fluid = ...,
) -> PorousMediumResult
```

Miki (1990) positive-real modification of the Delany-Bazley model.

In the variable $Y = f / \sigma$ (Miki 1990, Eqs. (30)-(34)):
$Z_\mathrm{c} = \rho c (1 + 0.070 Y^{-0.632} - j 0.107 Y^{-0.632})$ and,
from the propagation constant $\gamma = \alpha + j \beta$ via
$k = \beta - j \alpha$,
$k = (\omega/c)(1 + 0.109 Y^{-0.618} - j 0.160 Y^{-0.618})$. The
regression was constrained to be positive real, so the surface impedance
of a hard-backed layer keeps a non-negative real part even below the
Delany-Bazley range; a [`PorousAbsorberWarning`](/phonometry/reference/api/materials/porous/#porousabsorberwarning) still flags
`Y` outside the fit range $0.01 < f/\sigma < 1.0$ (paper
Sect. 4.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `flow_resistivity` | Airflow resistivity `sigma`, in Pa s/m2. |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air), the air this model was published with). Pass a computed one, such as `fluids.air(temperature_c=30.0, relative_humidity_percent=70.0)`, to work in the air of the room. |

**Returns:** A [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult).

## MIKI_VALIDITY

*Constant* (`tuple`).

```python
MIKI_VALIDITY = (0.01, 1.0)
```

## perforated_plate_impedance

```python
perforated_plate_impedance(
    frequency: ArrayLike,
    *,
    thickness: float,
    hole_radius: float,
    open_area: float,
    end_correction: float | None = None,
    fluid: Fluid = ...,
) -> Complex
```

Transfer impedance of a rigid perforated plate with circular holes.

Acoustic mass with both end corrections and the boundary-layer term
(Cox & D'Antonio 3e, Eq. (7.6)):

$$
m = \frac{\rho}{\varepsilon} \left[t + 2 \delta a + \sqrt{\frac{8 \nu}{\omega}} \left(1 + \frac{t}{2a}\right)\right]
$$

and visco-thermal surface resistance (Eq. (7.12)):

$$
r = \frac{\rho}{\varepsilon} \sqrt{8 \nu \omega} \left(1 + \frac{t}{2a}\right)
$$

giving $z = r + j \omega m$ (the series impedance added on top of
the backing, Eq. (7.21)). Assumes hole radii well above the boundary-layer
thickness; use [`microperforated_plate_impedance`](/phonometry/reference/api/materials/porous/#microperforated_plate_impedance) for submillimetre
holes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `thickness` | Plate thickness `t`, in metres. |
| `hole_radius` | Hole radius `a`, in metres. |
| `open_area` | Fractional open area `eps` (0..1). |
| `end_correction` | End-correction factor `delta` per end; default [`perforation_end_correction`](/phonometry/reference/api/materials/porous/#perforation_end_correction) of `eps`. |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air), the air this model was published with). Pass a computed one, such as `fluids.air(temperature_c=30.0, relative_humidity_percent=70.0)`, to work in the air of the room. |

**Returns:** Complex transfer impedance `z`, in Pa s/m.

## perforation_end_correction

```python
perforation_end_correction(open_area: float) -> float
```

End-correction factor `delta` of a circular perforation.

The Fok-function interaction correction for circular holes (Cox &
D'Antonio 3e, Table 7.1, Nesterov row; no open-area limit):

$$
\delta = 0.85 (1 - 1.47 \varepsilon^{1/2} + 0.47 \varepsilon^{3/2})
$$

Each orifice end adds $\delta a$ of air-plug length, and
$\delta \to 0.85$ for an isolated hole.

**Parameters**

| Name | Description |
| :--- | :--- |
| `open_area` | Fractional open area `eps` of the sheet (0..1). |

**Returns:** End-correction factor `delta` (dimensionless, per end).

## plot_absorber_stack

```python
plot_absorber_stack(
    layers: Sequence[Layer] | Layer,
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw a layered-absorber cross-section to scale, rigid backing at right.

Sound arrives from the left; each layer is drawn with its material fill
and its thickness dimensioned below the stack. A membrane (no physical
depth) is drawn as a thin sheet.

**Parameters**

| Name | Description |
| :--- | :--- |
| `layers` | The layer sequence of [`layered_absorber`](/phonometry/reference/api/materials/layered/#layered_absorber), front layer first, or a single layer. |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the front-layer rectangle. |

**Returns:** The axes.

## porosity_from_bulk_density

```python
porosity_from_bulk_density(
    bulk_density_kg_m3: float,
    *,
    fibre_density_kg_m3: float,
) -> float
```

Porosity of a fibrous material from its two densities (Eq. 1.160).

$\phi = 1 - \rho_\mathrm{bulk} / \rho_\mathrm{fibre}$, which holds
when the fibres are solid and whatever binds them together has negligible
mass. Hopkins states both conditions.

It closes on its own data: at the 2 600 kg/m3 fibre density and the 31 to
155 kg/m3 bulk-density range Hopkins prints for his rock wool, this returns
0,99 and 0,94, which is the porosity range he prints beside them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `bulk_density_kg_m3` | Bulk density of the material, in kg/m3 (> 0). |
| `fibre_density_kg_m3` | Density of the fibre itself, in kg/m3, larger than the bulk density. |

**Returns:** The open porosity `phi`, between 0 and 1.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive density, or a bulk density at or above the fibre density, which is not a porous material. |

## PorousAbsorberWarning

Advisory for porous-model use outside the published fit range.

## PorousMaterial

```python
PorousMaterial(
    *,
    name: str,
    flow_resistivity_pa_s_m2: float,
    porosity: float,
    tortuosity: float,
    viscous_length_um: float,
    thermal_length_um: float,
    frame_density_kg_m3: float,
    thickness_mm: float,
    source: str,
    shear_modulus_pa: complex | None = None,
    poisson_ratio: float | None = None,
    attributed_to: str = '',
)
```

A porous specimen as its source prints it, in library units.

A published parameter set for the rigid-frame and poroelastic models, so a
caller who has not characterised a specimen to ISO 9053 and ISO 10534-2 can
still reproduce a printed example and cite the page it came from. The
models take the parameters as arguments; nothing here is a default for any
of them.

**Attributes**

| Name | Description |
| :--- | :--- |
| `name` | The specimen as the table names it. |
| `flow_resistivity_pa_s_m2` | Airflow resistivity `sigma`, in Pa s/m2. |
| `porosity` | Open porosity `phi`. |
| `tortuosity` | Tortuosity $\alpha_\infty$. |
| `viscous_length_um` | Viscous characteristic length `Lambda`, in micrometres, the unit the tables print it in. The `viscous_length` parameter of [`johnson_champoux_allard`](/phonometry/reference/api/materials/porous/#johnson_champoux_allard) is in **metres**, so this field is not passed to it directly: `medium` makes the conversion, once, and a caller who assembles the argument list by hand divides by a million first. |
| `thermal_length_um` | Thermal characteristic length `Lambda'`, in micrometres. Metres at the model's `thermal_length`, as above. |
| `source` | Document, locator, PDF page and printed folio. A specimen whose columns come off several pages of one book names every one of them, separated by `"; "`. |
| `frame_density_kg_m3` | Frame density `rho1`, in kg/m3. |
| `thickness_mm` | Layer thickness `h` of the specimen as tabulated, in millimetres. It is the thickness of the layer the table describes and not a property of the material: a specimen whose columns come off several pages takes it from the one page that prints an `h`, and the worked examples of the same book use the same material at other thicknesses. |
| `shear_modulus_pa` | Complex in-vacuo shear modulus `N`, in pascals, or `None` when the table prints no elastic constants. `None` together with `poisson_ratio`, because a table that prints one prints the other. |
| `poisson_ratio` | Frame Poisson ratio `nu`, or `None`. |
| `attributed_to` | The source the book itself credits, empty when the number is the book's own. |

### PorousMaterial.frame_constants()

```python
PorousMaterial.frame_constants() -> tuple[complex, float]
```

The in-vacuo frame constants `(N, nu)` the source prints.

The complex shear modulus and the Poisson ratio are what
[`biot_waves`](/phonometry/reference/api/materials/biot/#biot_waves),
[`frame_quarter_wave_resonance`](/phonometry/reference/api/materials/biot/#frame_quarter_wave_resonance) and
[`PoroelasticLayer`](/phonometry/reference/api/materials/layered/#poroelasticlayer) take together, and a
table that prints one prints the other, so they are asked for together
and a specimen characterised as a rigid frame alone says so here rather
than handing out a `None` that fails further down.

**Returns:** `(shear_modulus_pa, poisson_ratio)`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the source prints no elastic constants. |

### PorousMaterial.medium()

```python
PorousMaterial.medium(
    frequency: ArrayLike,
    *,
    model: str = 'johnson_champoux_allard',
    fluid: Fluid = ...,
) -> PorousMediumResult
```

The equivalent fluid of this specimen.

The characteristic lengths are stored in the micrometres both tables
print and converted, here and once, to the metres
[`johnson_champoux_allard`](/phonometry/reference/api/materials/porous/#johnson_champoux_allard) takes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency vector `f`, in hertz. |
| `model` | `"johnson_champoux_allard"` (Default), `"delany_bazley"` or `"miki"`. The last two read the flow resistivity alone, so they describe a coarser specimen than the one the other four parameters pin. |
| `fluid` | The medium, a [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) (Default: [`PUBLISHED_AIR`](/phonometry/reference/api/materials/porous/#published_air)). |

**Returns:** A [`PorousMediumResult`](/phonometry/reference/api/materials/porous/#porousmediumresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown model name. |

## PorousMediumResult

```python
PorousMediumResult(
    frequency: Real,
    characteristic_impedance: Complex,
    wavenumber: Complex,
    effective_density: Complex,
    bulk_modulus: Complex,
    model: str,
    flow_resistivity: float,
    speed_of_sound: float,
    air_density: float,
)
```

Equivalent-fluid characterisation of a porous material.

All arrays share the shape of `frequency`. `characteristic_impedance`
is the complex characteristic impedance `Zc` in Pa s/m as seen from the
material surface, `wavenumber` the complex wavenumber `k` in rad/m
($\operatorname{Im}(k) < 0$ for the $e^{+j \omega t}$
convention), `effective_density` $= Z_\mathrm{c} k / \omega$ and
`bulk_modulus` $= Z_\mathrm{c} \omega / k$ the surface-normalised
equivalent-fluid density and bulk modulus, so that
$Z_\mathrm{c} = \sqrt{\rho_\mathrm{e} K_\mathrm{e}}$ and
$k = \omega \sqrt{\rho_\mathrm{e} / K_\mathrm{e}}$ for every model.

### PorousMediumResult.normalized_impedance

*property*

Characteristic impedance normalised by $\rho c$ of fluid.

### PorousMediumResult.normalized_wavenumber

*property*

Wavenumber normalised by the free-air wavenumber
$k_0 = \omega / c$.

### PorousMediumResult.plot()

```python
PorousMediumResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the normalised `Zc` and `k` components against frequency.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## PUBLISHED_AIR

*Constant* (`phonometry.fluids.Fluid`).

## PUBLISHED_POROUS_MATERIALS

*Constant* (`dict`).

```python
PUBLISHED_POROUS_MATERIALS = {'glass_wool': PorousMaterial(name='Domisol Coffrage glass wool', flow_resistivity_pa_s_m2=40000.0, porosity=0.94, tortuosity=1.06, viscous_length_um=56.0, thermal_length_um=110.0, frame_density_kg_m3=130.0, thickness_mm=3.8, source='Allard & Atalla 2e Table 6.1, PDF page 133 (printed p. 124); Allard & Atalla 2e Sect. 6.5.4, PDF page 132 (printed p. 123); Allard & Atalla 2e Table 11.8, PDF page 281 (printed p. 275)', shear_modulus_pa=(2200000+220000j), poisson_ratio=0.0, attributed_to=''), 'soft_fibrous': PorousMaterial(name='Soft fibrous', flow_resistivity_pa_s_m2=25000.0, porosity=0.98, tortuosity=1.02, viscous_length_um=90.0, thermal_length_um=180.0, frame_density_kg_m3=30.0, thickness_mm=50.0, source='Allard & Atalla 2e Table 11.2, PDF page 260 (printed p. 254)', shear_modulus_pa=None, poisson_ratio=None, attributed_to='')}
```

## ROCK_WOOL_FIBRE_DENSITY_KG_M3

*Constant* (`float`).

```python
ROCK_WOOL_FIBRE_DENSITY_KG_M3 = 2600.0
```

## ROCK_WOOL_LATERAL_FIT

*Constant* (`phonometry.materials.absorbers.porous.FibreResistivityFit`).

## ROCK_WOOL_LONGITUDINAL_FIT

*Constant* (`phonometry.materials.absorbers.porous.FibreResistivityFit`).

## viscous_characteristic_length

```python
viscous_characteristic_length(
    flow_resistivity_pa_s_m2: float,
    *,
    porosity: float,
    tortuosity: float,
    fluid: Fluid = ...,
    shape_factor: float = 1.0,
) -> float
```

The viscous characteristic length from the three measured parameters.

$\Lambda = (8 \eta \alpha_\infty / (\sigma \phi))^{1/2} / c$,
Allard & Atalla Eq. (5.25), PDF page 90 (printed p. 80), after Johnson et
al. (1986), with `c` close to 1.

How close is the question the shape factor exists for, and it is worth
saying what "close" buys. Against the twenty-three specimens Allard & Atalla
print with all four columns, `c = 1` puts $\Lambda$ within a factor
of two of the printed length for eighteen of them, with the middle of the
set near 1,2. The five it misses are the two carpets, the woven screen and
two rows whose lengths the book itself took from a different model, and
there the same arithmetic wants a `c` between 2 and 9,5.

So estimating this length rather than measuring it is worth a factor of two
on a bulk fibrous or open-cell absorber, and nothing at all on a floor
covering or a screen.

**Parameters**

| Name | Description |
| :--- | :--- |
| `flow_resistivity_pa_s_m2` | Airflow resistivity `sigma`, in Pa s/m2 (> 0). |
| `porosity` | Open porosity `phi`, between 0 and 1. |
| `tortuosity` | Tortuosity `alpha_infinity` (>= 1). |
| `fluid` | The saturating fluid, for its dynamic viscosity `eta`. |
| `shape_factor` | The `c` of Eq. (5.25) (> 0). One, unless the micro-geometry is known well enough to say otherwise. |

**Returns:** The viscous characteristic length `Lambda`, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive input or a porosity out of range. |

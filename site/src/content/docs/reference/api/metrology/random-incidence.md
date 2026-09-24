---
title: "metrology.random_incidence"
description: "Random-incidence and diffuse-field sensitivity of a sound level meter (IEC 61183:1994)."
sidebar:
  label: "random_incidence"
---

Random-incidence and diffuse-field sensitivity of a sound level meter
(IEC 61183:1994).

A sound level meter is calibrated for sound arriving from one direction, its
reference direction, and most of the sound it is used on arrives from all of
them. IEC 61183 gives the two ways of finding what the instrument reads in
such a field. The free-field method of clause 4 and Annex A rotates the
instrument in an anechoic room, measures what it indicates for each direction
of incidence, and weights each reading by the solid angle it stands for; the
diffuse-field method of clause 5 and Annex B compares the instrument with a
reference instrument in a reverberation room.

**The free-field method.** The random-incidence sensitivity level is the
free-field sensitivity level for the reference direction less the directivity
of the instrument, Formulas (1) and (A.6):

$$
G_\mathrm{RI} = G_\mathrm{F} - 10\lg\gamma, \qquad G_\mathrm{F} = L_\mathrm{rd} - L_\mathrm{o}
$$

where $L_\mathrm{rd}$ is what the instrument indicates for a plane wave
from the reference direction and $L_\mathrm{o}$ the level of that wave
without the instrument. The directivity factor $\gamma$ is the integral
of Formula (2) over the sphere, with the direction written as the angle
$\phi$ from the reference direction and the angle $\alpha$ about
it in Formula (3):

$$
\gamma = \frac{4\pi}{\displaystyle\int_0^{2\pi}\!\!\int_0^{\pi} 10^{-0{,}1[L_\mathrm{rd} - L(\phi,\alpha)]}\, |\sin\phi|\,\mathrm{d}\alpha\,\mathrm{d}\phi}
$$

and in practice the sum of Formula (4) over `m` angles $\phi_i$ in
steps $\Delta\phi = 2\pi/m$ and `n` planes $\alpha_j$ in steps
$\Delta\alpha = \pi/n$, each reading weighted by the share of the sphere
its element covers, Formula (5). Integrated, Formulas (6) and (7) give

$$
K(\phi_i) = \left|\frac{\Delta\alpha}{4\pi} \left[\cos\left(\phi_i - \frac{\Delta\phi}{2}\right) - \cos\left(\phi_i + \frac{\Delta\phi}{2}\right)\right]\right|, \qquad K(0) = K(\pi) = \frac{2\Delta\alpha}{4\pi} \left[1 - \cos\frac{\Delta\phi}{2}\right]
$$

[`adjustment_factors`](/phonometry/reference/api/metrology/random-incidence/#adjustment_factors) evaluates them for any angular step that divides
the half circle and any number of planes. Two planes at right angles,
$\Delta\alpha = \pi/2$, are Formulas (A.1) and (A.2) of Annex A, whose
factors for 10° steps Table A.1 prints; four planes at 45°, which NOTE 2 of
A.6 asks for when the reference direction is not normal to the diaphragm,
halve them.

The directivity factor then follows by one of three routes, each a function
here returning a [`DirectivityFactor`](/phonometry/reference/api/metrology/random-incidence/#directivityfactor):

* [`directivity_factor`](/phonometry/reference/api/metrology/random-incidence/#directivity_factor), two (or four) planes, Formula (A.3);
* [`axisymmetric_directivity_factor`](/phonometry/reference/api/metrology/random-incidence/#axisymmetric_directivity_factor), one plane for an instrument with
  rotational symmetry about its reference direction, Formula (A.4);
* [`equal_area_directivity_factor`](/phonometry/reference/api/metrology/random-incidence/#equal_area_directivity_factor), the 38 directions of equal-area
  elements of the note to A.1.8, Formula (A.5), at the directions
  [`equal_area_incidence_angles`](/phonometry/reference/api/metrology/random-incidence/#equal_area_incidence_angles) gives.

[`random_incidence_sensitivity`](/phonometry/reference/api/metrology/random-incidence/#random_incidence_sensitivity) applies Formula (1) band by band and
returns a [`RandomIncidenceSensitivity`](/phonometry/reference/api/metrology/random-incidence/#randomincidencesensitivity).

**The diffuse-field method.** The instrument and a reference instrument are
placed in turn at the same positions in a diffuse field, and the difference of
what they indicate, Formula (8), is added to the diffuse-field sensitivity
level of the reference, known in one of three ways: Formula (9) for a
reference calibrated by clause 4, Formula (10) for one calibrated in a free
field with its directivity factor known, and Formula (11) for one calibrated
in a pressure field with the difference between its diffuse-field and
pressure sensitivity levels known. [`diffuse_field_sensitivity`](/phonometry/reference/api/metrology/random-incidence/#diffuse_field_sensitivity) takes
any of the three and returns a [`DiffuseFieldSensitivity`](/phonometry/reference/api/metrology/random-incidence/#diffusefieldsensitivity). Table B.1
prints both the directivity factor and that difference for a type LS2aP/LS2F
laboratory standard microphone, the reference Annex B recommends;
[`IEC61183_TABLE_B1`](/phonometry/reference/api/metrology/random-incidence/#iec61183_table_b1) holds it and supplies them by default.

Two readings the text leaves to the implementer
-----------------------------------------------

**The two poles of Formula (A.3).** Both sums of (A.3) run from 0° to 350°,
and the paragraph under it notes that the readings at 0° and 180° are the same
in the two planes and "have only to be taken into account once". They have to
be *measured* once; they are *counted* in both sums. Each plane's pole factor
of Formula (A.2) covers half of the polar cap, so the 72 factors of Table A.1
sum to exactly one only with the poles in both sums, and an omnidirectional
instrument then has $\gamma = 1$. Counted once, the factors sum to
0,998097, and every directivity factor comes out 0,19 % high: a bias of
0,008 dB on $10\lg\gamma$ that this module does not make.

**The angles of the equal-area elements.** The note to A.1.8 prints the 38
directions to 0,1° without saying how they were placed. Each is the direction
that halves its element's area in polar angle: the cap about each pole takes
1/38 of the sphere, and the nine rings between them 4/38 each, split into
four elements by the two planes. That construction reproduces the note's
list of 20 angles to the 0,1° it is printed to, except two: 77,9° and its
mirror 282,1° break the list's own symmetry about 90° (77,9° + 102,2° is
180,1°, where every other pair sums to 180,0°), the construction gives 77,85°
and 282,15°, and the two are recorded in `docs/ERRATA.md`.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## adjustment_factors

```python
adjustment_factors(
    step_deg: float,
    *,
    planes: int = 2,
) -> NDArray[np.float64]
```

Adjustment factors $K(\phi)$ for one plane of measurements
(IEC 61183:1994, Formulas (6), (7), (A.1) and (A.2)).

The share of the sphere each reading stands for, at the angles
$\phi = 0, \Delta\phi, \ldots, 360° - \Delta\phi$ from the
reference direction, for measurements in `planes` planes through the
reference direction at equal angles $\Delta\alpha = 180°/n$ apart:

$$
K(\phi) = \frac{\Delta\alpha}{4\pi}\, 2\,|\sin\phi| \sin\frac{\Delta\phi}{2}, \qquad K(0) = K(180°) = \frac{2\Delta\alpha}{4\pi} \left[1 - \cos\frac{\Delta\phi}{2}\right]
$$

the first being Formula (6) with the difference of cosines written as a
product. With the two planes of Annex A this is $(1/8)[\cos(\phi - \Delta\phi/2) - \cos(\phi + \Delta\phi/2)]$ and $(1/4)[1 - \cos(\Delta\phi/2)]$, Formulas (A.1) and (A.2), which Table A.1 prints
for 10° steps; with the four planes of NOTE 2 of A.6 every factor is
halved, and with one plane, the rotationally symmetric instrument of
Formula (A.4), doubled.

The factors of all the planes together sum to one: each pole factor covers
half the polar cap in its plane, so the pole readings enter every plane's
sum (see the module notes).

**Parameters**

| Name | Description |
| :--- | :--- |
| `step_deg` | The angular step $\Delta\phi$ in degrees. It has to divide 180° into a whole number of steps, at least two, so that both poles are measured. |
| `planes` | The number of planes $n$ the measurements are made in (Default: 2, the X-Y and X-Z planes of Annex A). |

**Returns:** The `360 / step_deg` factors, read-only, the first at 0°.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a step that does not divide 180°, or a number of planes that is not a whole number of at least one. |

**Warns**

| Warning | When |
| :--- | :--- |
| SphereDivisionWarning | when the largest element is more than 3 % of the sphere (A.1.6), which a step above about 13,8° gives in two planes. |

## axisymmetric_directivity_factor

```python
axisymmetric_directivity_factor(
    levels_db: ArrayLike,
    *,
    reference_level_db: float | None = None,
) -> DirectivityFactor
```

Directivity factor of an instrument with rotational symmetry, from one
plane (IEC 61183:1994, Formula (A.4)).

$$
\gamma = \left(2\sum_{\phi = 0}^{350} K(\phi)\, 10^{-0{,}1[L_\mathrm{rd} - L(\phi,\mathrm{h})]}\right)^{-1}
$$

NOTE 1 of A.4.7: when the instrument is rotationally symmetric about its
reference direction, the X-Z plane repeats the X-Y plane and one rotation
(A.4.5) is enough. This is Formula (A.3) with the two planes equal, and
the factor 2 makes the weights those of [`adjustment_factors`](/phonometry/reference/api/metrology/random-incidence/#adjustment_factors) with
one plane.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L(\phi,\mathrm{h})$ in dB, one plane at $\phi = 0, \Delta\phi, \ldots, 360° - \Delta\phi$: 36 readings for Annex A. |
| `reference_level_db` | $L_\mathrm{rd}$ in dB (Default: None, the reading at 0°). |

**Returns:** The [`DirectivityFactor`](/phonometry/reference/api/metrology/random-incidence/#directivityfactor).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for readings in more than one plane, an odd number of readings or fewer than four, or a value that is not finite. |

**Warns**

| Warning | When |
| :--- | :--- |
| SphereDivisionWarning | when the step leaves an element larger than 3 % of the sphere in the two-plane division the one plane stands for. |

## diffuse_field_sensitivity

```python
diffuse_field_sensitivity(
    frequencies_hz: ArrayLike,
    indicated_level_db: ArrayLike,
    reference_indicated_level_db: ArrayLike,
    *,
    reference_random_incidence_level_db: ArrayLike | None = None,
    reference_free_field_level_db: ArrayLike | None = None,
    reference_directivity_index_db: ArrayLike | None = None,
    reference_pressure_level_db: ArrayLike | None = None,
    reference_diffuse_pressure_difference_db: ArrayLike | None = None,
) -> DiffuseFieldSensitivity
```

Diffuse-field sensitivity level by comparison with a reference sound
level meter (IEC 61183:1994, Formulas (8) to (11)).

$$
\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref} \tag{8}
$$

and then, by the calibration the reference instrument has,

$$
G_\mathrm{D} = \Delta G_\mathrm{D} + G_\mathrm{RI,ref} \tag{9}
$$

$$
G_\mathrm{D} = \Delta G_\mathrm{D} + G_\mathrm{F,ref} - 10\lg\gamma_\mathrm{ref} \tag{10}
$$

$$
G_\mathrm{D} = \Delta G_\mathrm{D} + (G_\mathrm{P,ref} + \Delta_\mathrm{DP}) \tag{11}
$$

Exactly one of `reference_random_incidence_level_db`,
`reference_free_field_level_db` and `reference_pressure_level_db`
selects the formula. For Formulas (10) and (11), the directivity factor
and the diffuse-to-pressure difference of the reference default to Table
B.1, the type LS2aP/LS2F microphone Annex B recommends, at each preferred
frequency from 25 Hz to 20 kHz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The band centres, in Hz, increasing. |
| `indicated_level_db` | $L_\mathrm{D}$, what the instrument under test indicates in the diffuse field, in dB, one per band. |
| `reference_indicated_level_db` | $L_\mathrm{D,ref}$, what the reference instrument indicates at the same positions, in dB. |
| `reference_random_incidence_level_db` | $G_\mathrm{RI,ref}$ in dB, for a reference calibrated by clause 4 (Formula (9)). |
| `reference_free_field_level_db` | $G_\mathrm{F,ref}$ in dB, for a reference calibrated in a free field (Formula (10)). |
| `reference_directivity_index_db` | $10\lg\gamma_\mathrm{ref}$ in dB, with Formula (10) only (Default: None, Table B.1). |
| `reference_pressure_level_db` | $G_\mathrm{P,ref}$ in dB, for a reference calibrated in a pressure field (Formula (11)). |
| `reference_diffuse_pressure_difference_db` | $\Delta_\mathrm{DP}$ in dB, with Formula (11) only (Default: None, Table B.1). |

**Returns:** The [`DiffuseFieldSensitivity`](/phonometry/reference/api/metrology/random-incidence/#diffusefieldsensitivity).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if not exactly one reference calibration is given, a correction is given for a formula that does not take it, a column does not hold one value per band (or a single value), or a default is asked of Table B.1 at a frequency it does not print. |

## DiffuseFieldSensitivity

```python
DiffuseFieldSensitivity(
    frequencies_hz: NDArray[np.float64],
    indicated_level_db: NDArray[np.float64],
    reference_indicated_level_db: NDArray[np.float64],
    reference_sensitivity_level_db: NDArray[np.float64],
    reference_correction_db: NDArray[np.float64],
    route: str,
)
```

The diffuse-field sensitivity level of a sound level meter, by
comparison with a reference instrument (IEC 61183:1994, clause 5).

$$
\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref}, \qquad G_\mathrm{D} = \Delta G_\mathrm{D} + G_\mathrm{D,ref}
$$

where the diffuse-field sensitivity level of the reference,
$G_\mathrm{D,ref}$, is its calibrated sensitivity level plus a
correction that depends on how it was calibrated: none for a
random-incidence calibration, Formula (9); $-10\lg\gamma_\mathrm{ref}$
for a free-field calibration, Formula (10); $+\Delta_\mathrm{DP}$
for a pressure calibration, Formula (11).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | the band centres, in Hz. |
| `indicated_level_db` | $L_\mathrm{D}$, what the instrument under test indicates, in dB. |
| `reference_indicated_level_db` | $L_\mathrm{D,ref}$, what the reference instrument indicates at the same positions, in dB. |
| `reference_sensitivity_level_db` | the reference's calibrated sensitivity level, in dB: $G_\mathrm{RI,ref}$, $G_\mathrm{F,ref}$ or $G_\mathrm{P,ref}$. |
| `reference_correction_db` | what turns that into the reference's diffuse-field sensitivity level, in dB: 0, $-10\lg \gamma_\mathrm{ref}$ or $\Delta_\mathrm{DP}$. |
| `route` | `"random_incidence"` (Formula (9)), `"free_field"` (Formula (10)) or `"pressure"` (Formula (11)). |

### DiffuseFieldSensitivity.diffuse_field_level_db

*property*

$G_\mathrm{D}$, the diffuse-field sensitivity level of the
instrument under test, in dB (Formulas (9) to (11)).

### DiffuseFieldSensitivity.level_difference_db

*property*

$\Delta G_\mathrm{D} = L_\mathrm{D} - L_\mathrm{D,ref}$, in dB
(Formula (8)).

### DiffuseFieldSensitivity.plot()

```python
DiffuseFieldSensitivity.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $G_\mathrm{D}$, $\Delta G_\mathrm{D}$ and
$G_\mathrm{D,ref}$ against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the $G_\mathrm{D}$ curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### DiffuseFieldSensitivity.reference_diffuse_field_level_db

*property*

$G_\mathrm{D,ref}$, the diffuse-field sensitivity level of the
reference instrument, in dB.

## directivity_factor

```python
directivity_factor(
    levels_db: ArrayLike,
    *,
    reference_level_db: float | None = None,
) -> DirectivityFactor
```

Directivity factor from readings in two or more planes
(IEC 61183:1994, Formula (A.3)).

$$
\gamma = \left(\sum_{\phi = 0}^{350} K(\phi)\, 10^{-0{,}1[L_\mathrm{rd} - L(\phi,\mathrm{h})]} + \sum_{\phi = 0}^{350} K(\phi)\, 10^{-0{,}1[L_\mathrm{rd} - L(\phi,\mathrm{v})]}\right)^{-1}
$$

for the 10° steps and two planes of A.4.5 and A.4.6, with the factors of
Table A.1. The angular step is read off the number of readings in a
plane, and the factors are [`adjustment_factors`](/phonometry/reference/api/metrology/random-incidence/#adjustment_factors) for that step and
that number of planes: four planes, as NOTE 2 of A.6 asks for when the
reference direction is not normal to the diaphragm, take half the factors
of Table A.1.

The readings at 0° and 180° are the same in every plane, and A.4.7 says
they have only to be taken into account once. They are measured once and
enter every plane's sum here, which is what makes the factors sum to one
and an omnidirectional instrument read $\gamma = 1$; counted once,
every $10\lg\gamma$ would come out 0,008 dB high.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L(\phi)$ in dB, one row per plane (the first the X-Y plane, `h`; the second the X-Z plane, `v`), each at $\phi = 0, \Delta\phi, \ldots, 360° - \Delta\phi$ from the reference direction: shape `(2, 36)` for Annex A. An instrument measured in one plane under rotational symmetry goes to [`axisymmetric_directivity_factor`](/phonometry/reference/api/metrology/random-incidence/#axisymmetric_directivity_factor). |
| `reference_level_db` | $L_\mathrm{rd}$ in dB (Default: None, the reading at 0° in the first plane, which A.4.4 takes in the same position). |

**Returns:** The [`DirectivityFactor`](/phonometry/reference/api/metrology/random-incidence/#directivityfactor).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than two planes, an odd number of readings in a plane or fewer than four, or a value that is not finite. |

**Warns**

| Warning | When |
| :--- | :--- |
| SphereDivisionWarning | when the step leaves an element larger than 3 % of the sphere (A.1.6). |

## DirectivityFactor

```python
DirectivityFactor(
    incidence_angles_deg: NDArray[np.float64],
    plane_angles_deg: NDArray[np.float64],
    levels_db: NDArray[np.float64],
    weights: NDArray[np.float64],
    reference_level_db: float,
    gamma: float,
    largest_element: float,
    formula: str,
)
```

The directivity factor of a sound level meter at one frequency
(IEC 61183:1994, Formulas (A.3) to (A.5)).

$$
\gamma = \left(\sum K\, 10^{-0{,}1[L_\mathrm{rd} - L]}\right)^{-1}
$$

over every reading, each weighted by the share of the sphere it stands
for. The readings are held flat, one entry per reading, with the plane
each was taken in.

**Attributes**

| Name | Description |
| :--- | :--- |
| `incidence_angles_deg` | $\phi$ of each reading from the reference direction, in degrees. |
| `plane_angles_deg` | $\alpha$ of the plane of each reading, in degrees: 0 for the X-Y plane (`h` in Annex A), 90 for the X-Z plane (`v`), and $180°\,j/n$ for plane $j = 0, \ldots, n - 1$ of `n`. |
| `levels_db` | $L(\phi)$, the level the instrument indicates for each direction, in dB. |
| `weights` | $K$ of each reading, dimensionless; they sum to one. |
| `reference_level_db` | $L_\mathrm{rd}$, in dB. |
| `gamma` | $\gamma$, dimensionless. |
| `largest_element` | the largest element of the division, as a fraction of the sphere (A.1.6). |
| `formula` | the formula applied: `"A.3"` (planes), `"A.4"` (one plane, rotational symmetry) or `"A.5"` (38 equal-area elements). |

### DirectivityFactor.directivity_index_db

*property*

$10\lg\gamma$, in dB: what Formula (1) subtracts from
$G_\mathrm{F}$, and what Table B.1 tabulates.

### DirectivityFactor.plot()

```python
DirectivityFactor.plot(
    ax: Axes | None = None,
    *,
    view: str = 'response',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the directional response or the weight of each reading.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. The `"response"` view needs a polar axes. |
| `view` | `"response"` (default) draws $L(\phi) - L_\mathrm{rd}$ on a polar axes, one curve per plane, with $10\lg\gamma$ in the title; `"weights"` draws the factor $K(\phi)$ of each reading against its angle, in per cent of the sphere. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the curve of the first plane. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if `view` is not one of the two names above, or `ax` is not polar for the response. |

### DirectivityFactor.relative_levels_db

*property*

$L(\phi) - L_\mathrm{rd}$ of each reading, in dB.

## equal_area_directivity_factor

```python
equal_area_directivity_factor(
    horizontal_levels_db: ArrayLike,
    vertical_levels_db: ArrayLike,
    *,
    reference_level_db: float | None = None,
) -> DirectivityFactor
```

Directivity factor from 38 equal-area elements (IEC 61183:1994,
Formula (A.5)).

$$
\gamma = \left(\sum_{n = 1}^{38} \frac{1}{38}\, 10^{-0{,}1[L_\mathrm{rd} - L(n)]}\right)^{-1}
$$

NOTE 2 of A.4.7: with the directions of the note to A.1.8, every element
is 1/38 of the sphere (2,6 %) and every reading weighs the same.

**Parameters**

| Name | Description |
| :--- | :--- |
| `horizontal_levels_db` | $L(n)$ in the horizontal (X-Y) plane, in dB, 20 readings at the directions of [`equal_area_incidence_angles`](/phonometry/reference/api/metrology/random-incidence/#equal_area_incidence_angles), in the order the note prints them (0°, 32,6°, ..., 180°, ..., 327,4°). |
| `vertical_levels_db` | $L(n)$ in the vertical (X-Z) plane, in dB, 18 readings at the same directions without 0° and 180°. |
| `reference_level_db` | $L_\mathrm{rd}$ in dB (Default: None, the horizontal reading at 0°). |

**Returns:** The [`DirectivityFactor`](/phonometry/reference/api/metrology/random-incidence/#directivityfactor).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for readings not 20 and 18, or a value that is not finite. |

## equal_area_incidence_angles

```python
equal_area_incidence_angles() -> tuple[NDArray[np.float64], NDArray[np.float64]]
```

The 38 directions of equal-area elements (IEC 61183:1994, note to
A.1.8).

The sphere is divided into 38 elements of equal area: a cap about each
pole, and nine rings of four elements between them, cut by the horizontal
(X-Y) and vertical (X-Z) planes. Each direction is the one that halves its
element's area in polar angle, so the `k`-th ring from the reference
direction is at

$$
\phi_k = \arccos\left(1 - \frac{4k - 1}{19}\right), \qquad k = 1, \ldots, 9
$$

which is 32,6°, 50,8°, 65,1°, 77,8° and 90° up to grazing incidence. The
note prints the same angles to 0,1°, except 77,9° and its mirror 282,1°,
which are errata (see the module notes).

**Returns:** `(horizontal, vertical)` in degrees, read-only. The horizontal plane holds both poles and runs 0°, $\phi_1, \ldots, \phi_9$, 180°, $360° - \phi_9, \ldots, 360° - \phi_1$: 20 directions in the order the note prints them. The vertical plane holds the same without the poles: 18.

## IEC61183_TABLE_B1

*Constant* (`mapping`).

## largest_element_fraction

```python
largest_element_fraction(step_deg: float, *, planes: int = 2) -> float
```

The largest element a set of incidence angles divides the sphere into,
as a fraction of its surface (IEC 61183:1994, A.1.6 and A.1.7).

The planes cut each ring between the poles into $2n$ elements of
$K(\phi)$ each, the largest at the direction nearest 90°, and leave
the cap about each pole whole, $\sin^2(\Delta\phi/4)$ of the sphere.
A.1.6 asks for the largest to be no more than 3 %; with the two planes of
Annex A and 10° steps it is the element at 90°, 2,18 %, the
"approximately 2,2 %" of A.1.7. One plane measured under rotational
symmetry stands for the same two planes and is judged on their division.

**Parameters**

| Name | Description |
| :--- | :--- |
| `step_deg` | The angular step $\Delta\phi$ in degrees, dividing 180° into a whole number of steps, at least two. |
| `planes` | The number of planes (Default: 2). |

**Returns:** The fraction, between 0 and 1.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | as [`adjustment_factors`](/phonometry/reference/api/metrology/random-incidence/#adjustment_factors). |

## random_incidence_sensitivity

```python
random_incidence_sensitivity(
    frequencies_hz: ArrayLike,
    free_field_level_db: ArrayLike,
    directivity_index_db: ArrayLike,
) -> RandomIncidenceSensitivity
```

Random-incidence sensitivity level from the free-field sensitivity
level and the directivity factor (IEC 61183:1994, Formulas (1) and (A.6)).

$$
G_\mathrm{RI} = G_\mathrm{F} - 10\lg\gamma
$$

at each frequency. $G_\mathrm{F} = L_\mathrm{rd} - L_\mathrm{o}$
depends on the individual instrument and $\gamma$ only on its
dimensions and geometry, so one model's directivity factors serve every
instrument of that model (4.2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The preferred frequencies, in Hz, increasing. |
| `free_field_level_db` | $G_\mathrm{F}$ at each frequency, in dB (A.3). |
| `directivity_index_db` | $10\lg\gamma$ at each frequency, in dB: [`DirectivityFactor.directivity_index_db`](/phonometry/reference/api/metrology/random-incidence/#directivityfactordirectivity_index_db) of the readings at that frequency. |

**Returns:** The [`RandomIncidenceSensitivity`](/phonometry/reference/api/metrology/random-incidence/#randomincidencesensitivity).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for columns of different lengths, a value that is not finite, or frequencies that are not positive and increasing. |

## RandomIncidenceSensitivity

```python
RandomIncidenceSensitivity(
    frequencies_hz: NDArray[np.float64],
    free_field_level_db: NDArray[np.float64],
    directivity_index_db: NDArray[np.float64],
    random_incidence_level_db: NDArray[np.float64],
)
```

The random-incidence sensitivity level of a sound level meter, band by
band (IEC 61183:1994, Formulas (1) and (A.6)).

$G_\mathrm{RI} = G_\mathrm{F} - 10\lg\gamma$ at each frequency.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | the preferred frequencies, in Hz. |
| `free_field_level_db` | $G_\mathrm{F} = L_\mathrm{rd} - L_\mathrm{o}$, the free-field sensitivity level for the reference direction, in dB. |
| `directivity_index_db` | $10\lg\gamma$, in dB. |
| `random_incidence_level_db` | $G_\mathrm{RI}$, in dB. |

### RandomIncidenceSensitivity.correction_db

*property*

$G_\mathrm{RI} - G_\mathrm{F} = -10\lg\gamma$ at each
frequency, in dB: what the instrument reads in a random-incidence
field relative to a plane wave from its reference direction.

### RandomIncidenceSensitivity.plot()

```python
RandomIncidenceSensitivity.plot(
    ax: Axes | None = None,
    *,
    view: str = 'levels',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the sensitivity levels or the correction against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `view` | `"levels"` (default) draws $G_\mathrm{F}$ and $G_\mathrm{RI}$; `"correction"` draws $G_\mathrm{RI} - G_\mathrm{F} = -10\lg\gamma$. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the first curve drawn. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if `view` is not one of the two names above. |

## ReferenceMicrophoneRow

```python
ReferenceMicrophoneRow(
    directivity_index_db: float,
    diffuse_pressure_difference_db: float,
)
```

One row of IEC 61183:1994 Table B.1.

The characteristics of a type LS2aP/LS2F laboratory standard microphone
(IEC 61094-1), the reference Annex B recommends for the diffuse-field
method, at one preferred frequency. The table rounds both to 0,05 dB,
determined with pure tones, with a measurement uncertainty of ±0,03 dB
(B.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `directivity_index_db` | $10\lg\gamma$ of the microphone, in dB: the directivity factor Formula (10) takes as $\gamma_\mathrm{ref}$. |
| `diffuse_pressure_difference_db` | $\Delta_\mathrm{DP}$, its diffuse-field sensitivity level less its pressure sensitivity level, in dB, which Formula (11) adds to a pressure calibration. |

## SphereDivisionWarning

The angular step divides the sphere into elements that are too large.

Emitted when the largest element of the sphere a set of incidence angles
divides it into is more than 3 % of its surface, the limit A.1.6 of
IEC 61183:1994 sets for a reading to stand for the directions around it.

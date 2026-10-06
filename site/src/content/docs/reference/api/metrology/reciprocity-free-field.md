---
title: "metrology.reciprocity_free_field"
description: "Free-field calibration of laboratory standard microphones by reciprocity (IEC 61094-3:2016 with its corrigendum IEC 61094-3:2016/COR1:2016)."
sidebar:
  label: "reciprocity_free_field"
---

Free-field calibration of laboratory standard microphones by reciprocity
(IEC 61094-3:2016 with its corrigendum IEC 61094-3:2016/COR1:2016).

Two microphones face each other in a free field with their principal axes in
line. A current $i_1$ through the transmitter makes it, seen from far
enough, a simple source of strength $M_{\mathrm{f},1} i_1$ placed at its
acoustic centre, and the spherical wave it radiates reaches the acoustic centre
of the receiver at the distance $d_{12}$ as (Formula (6))

$$
p_0 = \mathrm{j}\frac{\rho f}{2 d_{12}} M_{\mathrm{f},1}\,i_1\, \mathrm{e}^{-\mathrm{j}k d_{12}}\,\mathrm{e}^{-\alpha d_{\mathrm{m}12}}
$$

attenuated by the air over $d_{\mathrm{m}12}$, the distance the wave
actually travels between the diaphragms. The receiver turns it into
$U_2 = M_{\mathrm{f},2}\,p_0$, so the product of the two free-field
sensitivities is (Formula (7))

$$
M_{\mathrm{f},1} M_{\mathrm{f},2} = -\mathrm{j}\,\frac{2 d_{12}}{\rho f}\, \frac{U_2}{i_1}\,\mathrm{e}^{\mathrm{j}k d_{12}}\,\mathrm{e}^{\alpha d_{\mathrm{m}12}}
$$

and three pairs give each sensitivity (Formula (8)), or one pair and the ratio
of the two sensitivities measured against an auxiliary source give both
(Formula (9), the complex sensitivity since COR1).

**The factor** $-\mathrm{j}$. Formula (7) carries it and Formulas (8)
and (9) do not, although (8) is the quotient of three products of the form
(7) and (9) the product of one of them with $r_{12}$. The modulus does
not see the difference, and before the corrigendum (9) gave the modulus only;
the phase does, by 45°. The library takes the factor through from Formula (7)
and Formula (D.1), which agree with each other; the defect is recorded in
`docs/ERRATA.md`.

**The attenuation of sound in air** (7.4 and Annex B). $\alpha$ is the
real part of the propagation coefficient, computed by the five steps of B.2
([`reciprocity_air_attenuation`](/phonometry/reference/api/metrology/reciprocity-free-field/#reciprocity_air_attenuation)): ISO 9613-1 adjusted to the
quantities of IEC 61094-2, with the speed of sound at the conditions of the
calibration in the vibrational terms. Step 1 prints the last coefficient of
the saturation vapour pressure as $6{,}3343\,184\,5\cdot10^3$, where
IEC 61094-2 Table F.2, which the step refers to, prints
$6{,}343\,164\,5\times10^3$; the library uses the latter (an erratum).
Table B.1 tabulates the attenuation by ISO 9613-1 itself, as its text says,
and [`air_attenuation`](/phonometry/reference/api/environment/air-absorption/#air_attenuation)
reproduces every one of its 162 entries.

**The wave number** $k = \omega/c$ takes the speed of sound of IEC
61094-2 Annex F ([`air`](/phonometry/reference/api/fluids/air/)), by default with the
dispersion of its NOTE to F.3: $c = c_0[1 + \sum_n c\,\alpha_{\mathrm{v}n}/ (2\pi f_{\mathrm{v}n})]$, a few parts in $10^5$ that reach a few tenths of
a degree of phase at 20 kHz over 0,2 m. Annex B.1 points to it ("including
dispersion effects").

**Acoustic centres** (6.5 and Annex A). The distance $d_{12}$ is between
the acoustic centres, each given as its position on the principal axis
relative to the diaphragm, positive in front of it, a value or one per
frequency; Annex A shows them only as a figure. [`acoustic_centre`](/phonometry/reference/api/metrology/reciprocity-free-field/#acoustic_centre) finds
one from the inverse-distance law, as 6.5 describes.

**The arrangement** (6.4, 7.3). [`check_free_field_arrangement`](/phonometry/reference/api/metrology/reciprocity-free-field/#check_free_field_arrangement) holds the
distance between the microphones to the ten nominal diameters 7.3 recommends
and their supporting cylinders to the twenty 6.4 recommends, and the
conditions to the domain in which Annex B states the accuracy of the
attenuation: its verdict is whether the arrangement is the recommended one.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## acoustic_centre

```python
acoustic_centre(
    distances_m: ArrayLike,
    sound_pressures_pa: ArrayLike,
    *,
    attenuation_np_per_m: float = 0.0,
) -> AcousticCentre
```

The position of the acoustic centre of a microphone used as a source
(IEC 61094-3:2016 6.5).

"In a limited region of the far field, the sound pressure, corrected for
the effect of sound attenuation, will follow the 1/r-law, r being referred
now to the acoustic centre of the microphone. Thus, when plotting the
inverse value of the measured sound pressure as a function of the distance
from an arbitrarily chosen reference point of the microphone (most
conveniently the centre of the diaphragm), a straight line can be fitted
(e.g. by the methods of least squares) through the plotted values. The
intersection of this straight line and the abscissa axis determines the
position of the acoustic centre relative to the reference point."

The pressures may be in any unit proportional to the sound pressure, such
as the receiver's output voltage at one frequency; each is multiplied by
$\mathrm{e}^{\alpha r}$ before it is inverted.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distances_m` | The distances from the reference point, in m, at least three, positive. |
| `sound_pressures_pa` | The modulus of the sound pressure at each, in Pa or any proportional unit, positive. |
| `attenuation_np_per_m` | $\alpha$ at the frequency, in Np/m (Default: 0), from [`reciprocity_air_attenuation`](/phonometry/reference/api/metrology/reciprocity-free-field/#reciprocity_air_attenuation). |

**Returns:** The [`AcousticCentre`](/phonometry/reference/api/metrology/reciprocity-free-field/#acousticcentre).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than three distances, columns of different lengths, values that are not positive and finite, or distances that are all the same. |

## AcousticCentre

```python
AcousticCentre(
    distances_m: NDArray[np.float64],
    inverse_readings: NDArray[np.float64],
    slope: float,
    intercept: float,
)
```

The position of the acoustic centre of a microphone from the
inverse-distance law (IEC 61094-3:2016 6.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `distances_m` | The distances from the reference point of the microphone to the observation points, in m. |
| `inverse_readings` | $1/\vert p\vert $, corrected for the attenuation of sound, at each distance, in the reciprocal of the unit the pressures were given in. |
| `slope` | The slope of the straight line fitted by least squares. |
| `intercept` | Its intercept at zero distance. |

### AcousticCentre.plot()

```python
AcousticCentre.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the inverse pressures, the fitted line and where it crosses the
axis.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the fitted line. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### AcousticCentre.position_m

*property*

The acoustic centre relative to the reference point, in m: where the
fitted line crosses the axis, $-b/a$; positive towards the
observation points, which for a reference point on the diaphragm is in
front of it (Annex A).

## check_free_field_arrangement

```python
check_free_field_arrangement(
    frequencies_hz: ArrayLike,
    *,
    diaphragm_distances_m: Sequence[float],
    microphone_diameter_m: float,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    support_length_m: float | None = None,
) -> FreeFieldArrangementCheck
```

Is this the free-field arrangement IEC 61094-3:2016 recommends?

7.3 recommends a distance between the microphones greater than ten times
their nominal diameter, "to ensure an approximately plane wave in a
suitable region around the receiving microphone"; 6.4 recommends
attaching each microphone to a cylinder of its diameter at least twenty
diameters long; and B.2 states the accuracy of the attenuation within a
domain of temperature, static pressure, water vapour and
frequency-to-pressure ratio. Annex A allows the published acoustic centres
between 150 mm and 500 mm, which is reported without entering the verdict.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies of the calibration, in Hz. |
| `diaphragm_distances_m` | The distance of each pair, in m. |
| `microphone_diameter_m` | The nominal diameter of the microphones, in m (23,77 mm for LS1, 13,2 mm for LS2a: dimension A of Table C.1 of IEC 61094-2). |
| `temperature_c` | The temperature, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `support_length_m` | The length of the supporting cylinder, in m, or `None` if not known. |

**Returns:** The [`FreeFieldArrangementCheck`](/phonometry/reference/api/metrology/reciprocity-free-field/#freefieldarrangementcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for no distance, or a distance, diameter or length that is not positive. |

## free_field_parameter_uncertainty

```python
free_field_parameter_uncertainty(
    frequencies_hz: ArrayLike,
    uncertainties: FreeFieldInputUncertainties,
    *,
    diaphragm_distances_m: Sequence[float],
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0, 0.0),
    microphone: int = 1,
    dispersion: bool = True,
) -> FreeFieldParameterUncertainty
```

The uncertainty components of the free-field acoustic transfer
impedance, one parameter at a time (IEC 61094-3:2016 7.8).

As in IEC 61094-2 7.5, each parameter with a non-zero standard uncertainty
is moved by it, the three products of Formula (7) recomputed with the
electrical transfer impedances held, and the change of the level of
`microphone` by Formula (8) is its component. The distance of each pair
and the acoustic centre of each microphone are moved one at a time, as
independent quantities, and their changes combined in quadrature into the
single rows "Distance" and "Acoustic centres" of Table 1. The attenuation
is moved by a fraction of itself,
[`FreeFieldInputUncertainties.u_air_attenuation_ratio`](/phonometry/reference/api/metrology/reciprocity-free-field/#freefieldinputuncertainties).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `uncertainties` | The standard uncertainty of each input quantity, a [`FreeFieldInputUncertainties`](/phonometry/reference/api/metrology/reciprocity-free-field/#freefieldinputuncertainties). |
| `diaphragm_distances_m` | $d_{\mathrm{m}12}$, $d_{\mathrm{m}23}$, $d_{\mathrm{m}31}$, in m. |
| `temperature_c` | The temperature, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `acoustic_centres_m` | The three acoustic centres, in m. |
| `microphone` | The microphone whose level is analysed, 1, 2 or 3. |
| `dispersion` | Whether $k$ includes dispersion (Default: `True`). |

**Returns:** The [`FreeFieldParameterUncertainty`](/phonometry/reference/api/metrology/reciprocity-free-field/#freefieldparameteruncertainty).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for other than three distances or centres, a microphone that is not 1, 2 or 3, or acoustic-centre uncertainties that are not one value or one per frequency. |

## free_field_reciprocity

```python
free_field_reciprocity(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedances_ohm: Sequence[ArrayLike],
    *,
    diaphragm_distances_m: Sequence[float],
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0, 0.0),
    dispersion: bool = True,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration
```

The free-field sensitivities of three microphones calibrated in pairs
(IEC 61094-3:2016 5.7.1, Formula (8)).

Each pair gives the product of Formula (7), with $d_{ij}$ the
distance between the acoustic centres and $d_{\mathrm{m}ij}$ that
between the diaphragms; facing each other, $d_{ij} = d_{\mathrm{m}ij} - x_i - x_j$ with $x$ the position of each acoustic
centre in front of its diaphragm. The three are solved as Formula (8) asks:

$$
M_{\mathrm{f},1} = \left(-\mathrm{j}\,\frac{2}{\rho f}\, \frac{d_{12}d_{31}}{d_{23}}\,\frac{Z_{\mathrm{e},12}Z_{\mathrm{e},31}} {Z_{\mathrm{e},23}}\,\mathrm{e}^{\mathrm{j}k(d_{12}+d_{31}-d_{23})}\, \mathrm{e}^{\alpha(d_{\mathrm{m}12}+d_{\mathrm{m}31}-d_{\mathrm{m}23})}\right)^{1/2}
$$

with the factor $-\mathrm{j}$ that Formula (7) carries and the
printed Formula (8) drops (module docstring).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `electrical_transfer_impedances_ohm` | $Z_{\mathrm{e},12}$, $Z_{\mathrm{e},23}$ and $Z_{\mathrm{e},31}$, complex, in Ω. |
| `diaphragm_distances_m` | $d_{\mathrm{m}12}$, $d_{\mathrm{m}23}$ and $d_{\mathrm{m}31}$, in m. |
| `temperature_c` | The temperature of the air, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `acoustic_centres_m` | The acoustic centre of microphones 1, 2 and 3, each relative to its diaphragm on the principal axis, positive in front, in m, one value or one per frequency (Default: the centres of the diaphragms, which Annex A allows at sufficiently remote points). |
| `dispersion` | Whether $k$ takes the speed of sound with the dispersion of IEC 61094-2 F.3 (Default: `True`). |
| `corrections_db` | Corrections added to every level (Default: none). |
| `expanded_uncertainty_db` | The expanded uncertainty, in dB (Default: `None`). |

**Returns:** The [`ReciprocityCalibration`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocitycalibration).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for other than three pairs, distances that are not positive or that the acoustic centres use up, or values that are zero or not finite. |

## free_field_reciprocity_pair

```python
free_field_reciprocity_pair(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedance_ohm: ArrayLike,
    sensitivity_ratio: ArrayLike,
    *,
    diaphragm_distance_m: float,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0),
    dispersion: bool = True,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration
```

The complex free-field sensitivities of two microphones and an
auxiliary sound source (IEC 61094-3:2016 5.1.3 and 5.7.2, Formula (9) as
corrected by COR1).

$$
M_{\mathrm{f},1} = \left(-\mathrm{j}\,r_{12}\,\frac{2 d_{12}}{\rho f}\, Z_{\mathrm{e},12}\,\mathrm{e}^{\mathrm{j}k d_{12}}\, \mathrm{e}^{\alpha d_{\mathrm{m}12}}\right)^{1/2}
$$

COR1 replaces "modulus of the" by "complex" in 5.7.2, so the formula gives
the complex sensitivity; the factor $-\mathrm{j}$ is that of
Formula (7), which the printed Formula (9) drops (module docstring).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `electrical_transfer_impedance_ohm` | $Z_{\mathrm{e},12}$, complex, in Ω. |
| `sensitivity_ratio` | $r_{12} = M_{\mathrm{f},1}/M_{\mathrm{f},2}$, complex, measured against the auxiliary source. |
| `diaphragm_distance_m` | $d_{\mathrm{m}12}$, in m. |
| `temperature_c` | The temperature of the air, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `acoustic_centres_m` | The acoustic centres of the two microphones, positive in front of the diaphragm, in m (Default: the diaphragms). |
| `dispersion` | Whether $k$ includes dispersion (Default: `True`). |
| `corrections_db` | Corrections added to both levels (Default: none). |
| `expanded_uncertainty_db` | The expanded uncertainty, in dB (Default: `None`). |

**Returns:** The [`ReciprocityCalibration`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocitycalibration), of two microphones.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a distance that is not positive or that the acoustic centres use up, or values that are zero or not finite. |

## free_field_transfer_impedance

```python
free_field_transfer_impedance(
    frequencies_hz: ArrayLike,
    sensitivity_1_v_per_pa: ArrayLike,
    sensitivity_2_v_per_pa: ArrayLike,
    *,
    diaphragm_distance_m: float,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0),
    dispersion: bool = True,
) -> NDArray[np.complex128]
```

The electrical transfer impedance two microphones of known free-field
sensitivity give (IEC 61094-3:2016 D.4.2, Formula (D.1)).

$$
\frac{U_2}{i_1} = \mathrm{j}\,\frac{\rho f}{2 d_{12}}\,M_{\mathrm{f},1} M_{\mathrm{f},2}\,\mathrm{e}^{-\mathrm{j}k d_{12}}\,\mathrm{e}^{-\alpha d_{\mathrm{m}12}}
$$

Formula (7) turned round. D.4.2 uses it to fill the frequency range below
the lowest measured frequency before a transformation to the time domain,
with the free-field sensitivities taken there from the pressure
sensitivity and the scattering factor (Formula (4)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `sensitivity_1_v_per_pa` | $M_{\mathrm{f},1}$, complex, in V/Pa. |
| `sensitivity_2_v_per_pa` | $M_{\mathrm{f},2}$, complex, in V/Pa. |
| `diaphragm_distance_m` | $d_{\mathrm{m}12}$, in m. |
| `temperature_c` | The temperature of the air, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `acoustic_centres_m` | The two acoustic centres, in m (Default: the diaphragms). |
| `dispersion` | Whether $k$ includes dispersion (Default: `True`). |

**Returns:** $U_2/i_1$, complex, in Ω, at each frequency.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a distance that is not positive or that the acoustic centres use up, or values that are zero or not finite. |

## FreeFieldArrangementCheck

```python
FreeFieldArrangementCheck(
    diaphragm_distances_m: tuple[float, ...],
    microphone_diameter_m: float,
    distances_ok: bool,
    support_length_m: float | None,
    support_ok: bool | None,
    annex_a_range: bool,
    attenuation_accuracy: bool,
)
```

Whether a free-field reciprocity arrangement is the one IEC 61094-3:2016
recommends.

6.4 asks for a distance "great enough" and supporting cylinders "long
compared to the diameter", and puts numbers on both only as
recommendations: ten nominal diameters between the microphones (7.3) and
twenty along the cylinder (6.4). The verdict holds the arrangement to those
numbers, and the conditions to the domain in which B.2 states the accuracy
of the attenuation; an arrangement that fails it is not forbidden, but
falls outside what the standard recommends and what its uncertainty
figures assume.

Built by [`check_free_field_arrangement`](/phonometry/reference/api/metrology/reciprocity-free-field/#check_free_field_arrangement).

**Attributes**

| Name | Description |
| :--- | :--- |
| `diaphragm_distances_m` | The distances between the microphones, in m. |
| `microphone_diameter_m` | The nominal diameter of the microphones, in m. |
| `distances_ok` | Every distance is greater than ten nominal diameters, as 7.3 recommends. |
| `support_length_m` | The length of the cylinder each microphone is attached to, in m, or `None`. |
| `support_ok` | It is at least twenty diameters, as 6.4 recommends, or `None`. |
| `annex_a_range` | Every distance is within 150 mm to 500 mm, where Annex A allows the published acoustic centres. Advisory: it does not enter `passes`. |
| `attenuation_accuracy` | The conditions and every frequency are within the domain in which B.2 states the accuracy of the attenuation. |

### FreeFieldArrangementCheck.passes

*property*

The verdict: the distances and the supports are as 7.3 and 6.4
recommend, and the conditions are where B.2 states the accuracy of
the attenuation.

### FreeFieldArrangementCheck.plot()

```python
FreeFieldArrangementCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each distance against ten diameters and the range of Annex A.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `barh`. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## FreeFieldInputUncertainties

```python
FreeFieldInputUncertainties(
    *,
    u_distance_m: float = 0.0,
    u_acoustic_centre_m: ArrayLike = 0.0,
    u_static_pressure_pa: float = 0.0,
    u_temperature_k: float = 0.0,
    u_relative_humidity_percent: float = 0.0,
    u_air_attenuation_ratio: float = 0.0,
)
```

The standard uncertainty of each input quantity of the free-field
acoustic transfer impedance that [`free_field_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-free-field/#free_field_parameter_uncertainty)
can move: the distance, the three conditions and the air attenuation, rows
Table 1 of IEC 61094-3:2016 lists under "Acoustic transfer impedance", and
the acoustic centres of its "Microphone parameters".

Each one left at zero contributes no component.

**Parameters**

| Name | Description |
| :--- | :--- |
| `u_distance_m` | Of each distance between the diaphragms, in m. |
| `u_acoustic_centre_m` | Of each acoustic centre, in m, one value or one per frequency (Annex A puts it under 2 mm below the resonance frequency, as a bound). It is held as a read-only float64 copy. |
| `u_static_pressure_pa` | Of the static pressure, in Pa. |
| `u_temperature_k` | Of the temperature, in K. |
| `u_relative_humidity_percent` | Of the relative humidity, in percentage points. |
| `u_air_attenuation_ratio` | Of the attenuation coefficient, as a fraction of it. B.2 estimates its accuracy at ±10 %, a standard uncertainty of $0{,}1/\sqrt{3}$ for a rectangular distribution. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an uncertainty that is negative or not finite, or acoustic-centre uncertainties that are not one value or one column. |

## FreeFieldParameterUncertainty

```python
FreeFieldParameterUncertainty(
    frequencies_hz: NDArray[np.float64],
    components_db: Mapping[str, NDArray[np.float64]],
    microphone: int,
)
```

The standard uncertainty of a free-field sensitivity level that each
parameter of the acoustic transfer impedance contributes (IEC
61094-3:2016 7.8).

Built by [`free_field_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-free-field/#free_field_parameter_uncertainty); ready to pass to
[`reciprocity_uncertainty_budget`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocity_uncertainty_budget) with
`field="free_field"`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `components_db` | The component of each parameter, keyed by its name in [`IEC61094_3_TABLE_1`](/phonometry/reference/api/metrology/reciprocity-calibration/#iec61094_3_table_1), in dB at each frequency. |
| `microphone` | The microphone whose level they are for, 1, 2 or 3. |

### FreeFieldParameterUncertainty.plot()

```python
FreeFieldParameterUncertainty.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each component against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the first component's curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## reciprocity_air_attenuation

```python
reciprocity_air_attenuation(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
) -> ReciprocityAirAttenuation
```

The air attenuation coefficient of a free-field reciprocity calibration
(IEC 61094-3:2016 B.2, Steps 1 to 5).

$$
\alpha = f^2\left[18{,}42\times10^{-12}\left(\frac{p_\mathrm{s}}{p_\mathrm{s,r}}\right)^{-1} \left(\frac{T}{T_{20}}\right)^{1/2} + \left(\frac{T}{T_{20}}\right)^{-2}\left( \frac{4{,}3778}{c}\frac{\mathrm{e}^{-2239{,}1/T}}{f_\mathrm{rO} + f^2/f_\mathrm{rO}} + \frac{36{,}6624}{c}\frac{\mathrm{e}^{-3352{,}0/T}}{f_\mathrm{rN} + f^2/f_\mathrm{rN}} \right)\right]
$$

in Np/m, with the relaxation frequencies of Step 3 from the water vapour
mole fraction of Steps 1 and 2, and $c$ the speed of sound of IEC
61094-2 Formula (F.2) at the conditions. B.2 estimates the accuracy at
±10 % within -20 °C to 50 °C, below 200 kPa, for
$0{,}5\times10^{-3} \le x_\mathrm{w} \le 50\times10^{-3}$ and a
frequency-to-pressure ratio of 0,4 Hz/kPa to $10^4$ Hz/kPa
([`ReciprocityAirAttenuation.within_stated_accuracy`](/phonometry/reference/api/metrology/reciprocity-free-field/#reciprocityairattenuationwithin_stated_accuracy)).

Step 1 is computed with the coefficient of IEC 61094-2 Table F.2, which it
refers to, not with the one it prints (`docs/ERRATA.md`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `temperature_c` | $t$, in °C. |
| `static_pressure_pa` | $p_\mathrm{s}$, in Pa. |
| `relative_humidity_percent` | $H$, in %. |

**Returns:** The [`ReciprocityAirAttenuation`](/phonometry/reference/api/metrology/reciprocity-free-field/#reciprocityairattenuation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not positive and increasing, a pressure that is not positive, a humidity outside 0 % to 100 %, or a temperature at or below absolute zero. |

## ReciprocityAirAttenuation

```python
ReciprocityAirAttenuation(
    frequencies_hz: NDArray[np.float64],
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    water_vapour_mole_fraction: float,
    oxygen_relaxation_hz: float,
    nitrogen_relaxation_hz: float,
    speed_of_sound: float,
    classical_np_per_m: NDArray[np.float64],
    oxygen_np_per_m: NDArray[np.float64],
    nitrogen_np_per_m: NDArray[np.float64],
)
```

The attenuation of sound in air of a free-field reciprocity calibration
(IEC 61094-3:2016 7.4 and Annex B), and the speed of sound with dispersion
(IEC 61094-2:2009 F.3, NOTE).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `temperature_c` | $t$, in °C. |
| `static_pressure_pa` | $p_\mathrm{s}$, in Pa. |
| `relative_humidity_percent` | $H$, in %. |
| `water_vapour_mole_fraction` | $x_\mathrm{w}$ (Step 2). |
| `oxygen_relaxation_hz` | $f_\mathrm{rO}$, in Hz (Step 3). |
| `nitrogen_relaxation_hz` | $f_\mathrm{rN}$, in Hz (Step 3). |
| `speed_of_sound` | $c$, the zero-frequency speed of sound of IEC 61094-2 Formula (F.2) at the conditions, in m/s; the one Step 4 divides by. |
| `classical_np_per_m` | $\alpha_\mathrm{cl} + \alpha_\mathrm{rot}$, in Np/m. |
| `oxygen_np_per_m` | $\alpha_\mathrm{vib,O}$, in Np/m. |
| `nitrogen_np_per_m` | $\alpha_\mathrm{vib,N}$, in Np/m. |

### ReciprocityAirAttenuation.attenuation_db_per_m

*property*

$20\lg(\mathrm{e})\,\alpha$, in dB/m, the quantity of Table B.1.

### ReciprocityAirAttenuation.attenuation_np_per_m

*property*

$\alpha = \alpha_\mathrm{cl} + \alpha_\mathrm{rot} + \alpha_\mathrm{vib,O} + \alpha_\mathrm{vib,N}$ (Step 5), in Np/m.

### ReciprocityAirAttenuation.dispersive_speed_of_sound

*property*

The speed of sound at each frequency, in m/s (IEC 61094-2:2009 F.3,
NOTE):

$$
c = c_0\left[1 + \sum_n \frac{c\,\alpha_{\mathrm{v}n}}{2\pi f_{\mathrm{v}n}}\right]
$$

over oxygen and nitrogen, where $c\,\alpha_{\mathrm{v}n}$ does not
depend on $c$ because Step 4 divides by it.

### ReciprocityAirAttenuation.plot()

```python
ReciprocityAirAttenuation.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the attenuation in dB/m and its three parts against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the total-attenuation curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### ReciprocityAirAttenuation.within_stated_accuracy

*property*

Whether each frequency is inside the domain in which B.2 states the
±10 % accuracy of the attenuation.

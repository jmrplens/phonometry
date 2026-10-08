---
title: "metrology.reciprocity_coupler"
description: "Pressure calibration of laboratory standard microphones by reciprocity in a closed coupler (IEC 61094-2:2009)."
sidebar:
  label: "reciprocity_coupler"
---

Pressure calibration of laboratory standard microphones by reciprocity in a
closed coupler (IEC 61094-2:2009).

Two microphones close the two ends of a small cavity. A current $i_1$
through the transmitter makes its diaphragm a source of short-circuit volume
velocity $M_{\mathrm{p},1} i_1$, the gas in the cavity turns that into
the pressure $p_2 = Z_{\mathrm{a},12}\,M_{\mathrm{p},1} i_1$ on the
receiver, and the receiver turns the pressure into its open-circuit voltage,
so (Formula (2))

$$
M_{\mathrm{p},1} M_{\mathrm{p},2} = \frac{1}{Z_{\mathrm{a},12}}\, \frac{U_2}{i_1}
$$

The electrical transfer impedance $U_2/i_1$ is measured; this module
computes the acoustic transfer impedance $Z_{\mathrm{a},12}$ it is
divided by, with every correction the standard gives, and solves the three
products for the sensitivities with
[`reciprocity_calibration`](/phonometry/reference/api/metrology/reciprocity-calibration/).

**Two couplers** (5.4 and Annex C). A *large-volume* coupler, small against
the wavelength, holds a pure compliance, and Formula (3) adds the admittances
of the gas and of the two microphones,

$$
\frac{1}{Z'_{\mathrm{a},12}} = \mathrm{j}\omega\left(\frac{V}{\kappa p_\mathrm{s}} + \frac{V_{\mathrm{e},1}}{\kappa_\mathrm{r} p_\mathrm{s,r}} + \frac{V_{\mathrm{e},2}}{\kappa_\mathrm{r} p_\mathrm{s,r}}\right)
$$

with $V$ the coupler volume plus the two front cavities (7.3.3.1), and
the bores that Figure C.2 draws between each microphone face and the cavity
(dimension F of Table C.2), and $V_\mathrm{e}$ the complex equivalent
volume of each microphone. A
*plane-wave* coupler, of the diameter of the diaphragms, is a transmission line
of length $l_0$ between them (Formula (4)):

$$
\frac{1}{Z'_{\mathrm{a},12}} = \frac{1}{Z_{\mathrm{a},0}}\left[ \left(\frac{Z_{\mathrm{a},0}}{Z_{\mathrm{a},1}} + \frac{Z_{\mathrm{a},0}}{Z_{\mathrm{a},2}}\right)\cosh\gamma l_0 + \left(1 + \frac{Z_{\mathrm{a},0}^2}{Z_{\mathrm{a},1} Z_{\mathrm{a},2}}\right) \sinh\gamma l_0\right]
$$

**Heat conduction** (5.5 and Annex A). In the large-volume coupler the walls
draw heat from the compressed gas and the volume looks larger, by the complex
factor of Formula (A.1),

$$
\Delta_\mathrm{H} = \frac{\kappa}{1 + (\kappa - 1)\,E_V}
$$

where $E_V$ is Gerber's temperature transfer function of a finite
cylinder: [`temperature_transfer_function`](/phonometry/reference/api/metrology/reciprocity-coupler/#temperature_transfer_function) computes it either by the
approximation (A.2) or by the full solution of the reference [A.1], which
A.2 requires below 20 Hz unless the uncertainty component is increased
instead, and which reproduces every entry of Table A.1 to its
stated 0,000 01. In the plane-wave coupler the propagation coefficient and the
wave impedance of Formulas (A.3) and (A.4) carry the losses at the cylindrical
wall, and the admittance of Formula (A.5) those at the two diaphragms.

**Capillary tubes** (5.6 and Annex B). Tubes that equalise the static pressure
shunt the cavity, and Formula (6) divides the transfer impedance by

$$
\Delta_\mathrm{C} = 1 + n\,\frac{Z''_{\mathrm{a},12}}{Z_{\mathrm{a,C}}}
$$

with $Z_{\mathrm{a,C}}$ the input impedance of an open tube of Formulas
(B.1) to (B.3), which [`capillary_tube_impedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#capillary_tube_impedance) computes and Tables B.1
and B.2 test.

**The microphone** (7.3.3 and Annex E). Its acoustic impedance is a lumped
compliance, mass and resistance, written as an equivalent volume, a resonance
frequency and a loss factor ([`ReciprocityMicrophone`](/phonometry/reference/api/metrology/reciprocity-coupler/#reciprocitymicrophone)); its front cavity
adds volume, length and, through the excess of its measured volume over the
cylinder of its depth, a further terminating admittance (7.3.3.1).

The wave-motion corrections of Table C.3 for the air-filled large-volume
coupler of LS1P microphones are [`large_volume_wave_motion_correction`](/phonometry/reference/api/metrology/reciprocity-coupler/#large_volume_wave_motion_correction),
the coupler dimensions of Tables C.1 and C.2 are [`IEC61094_2_TABLE_C1`](/phonometry/reference/api/metrology/reciprocity-coupler/#iec61094_2_table_c1)
and [`IEC61094_2_TABLE_C2`](/phonometry/reference/api/metrology/reciprocity-coupler/#iec61094_2_table_c2), and [`coupler_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_parameter_uncertainty)
finds the uncertainty each coupler and microphone parameter contributes, by the
one-at-a-time recalculation 7.5 describes.

The properties of the gas, $\rho$, $c$, $\kappa$,
$\eta$ and $\alpha_t$, are those of humid air by Annex F
([`air`](/phonometry/reference/api/fluids/air/)) at the conditions of the calibration, or of
any [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) passed as `gas`: 7.3.2.1 allows the
coupler to be filled with hydrogen or helium.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## capillary_tube_impedance

```python
capillary_tube_impedance(
    frequencies_hz: ArrayLike,
    *,
    length_m: float,
    radius_m: float,
    gas: Fluid,
) -> CapillaryTubeImpedance
```

The acoustic input impedance of an open capillary tube (IEC
61094-2:2009 B.1).

Formulas (B.2) and (B.3) give the product and the quotient of the
propagation coefficient and the wave impedance of an infinite tube of
radius $a_\mathrm{t}$,

$$
\gamma Z_{\mathrm{a,t}} = \mathrm{j}\frac{\omega\rho}{\pi a_\mathrm{t}^2} \left[1 - \frac{2 J_1(k a_\mathrm{t})}{k a_\mathrm{t} J_0(k a_\mathrm{t})}\right]^{-1}, \qquad \frac{\gamma}{Z_{\mathrm{a,t}}} = \mathrm{j}\omega\frac{\pi a_\mathrm{t}^2}{\rho c^2} \left[1 + \frac{2(\kappa - 1)}{B k a_\mathrm{t}} \frac{J_1(B k a_\mathrm{t})}{J_0(B k a_\mathrm{t})}\right]
$$

with $k = (-\mathrm{j}\omega\rho/\eta)^{1/2}$ and
$B = (\eta/\rho\alpha_t)^{1/2}$; each follows from their product and
quotient on the branch with a positive real part, and Formula (B.1) gives
$Z_{\mathrm{a,C}} = Z_{\mathrm{a,t}}\tanh\gamma l_\mathrm{C}$. A
tube blocked along its length by a wire has $\Delta_\mathrm{C} = 1$
instead (B.1), which a coupler without a `capillary` stands for.

Tables B.1 and B.2 tabulate $Z_{\mathrm{a,C}}$ at the reference
conditions for tubes 50 mm and 100 mm long and 0,1667 mm, 0,20 mm and
0,25 mm in radius; the first radius is 1/6 mm, which is what the printed
values were computed with.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `length_m` | $l_\mathrm{C}$, in m. |
| `radius_m` | $a_\mathrm{t}$, in m. |
| `gas` | The gas in the tube. |

**Returns:** The [`CapillaryTubeImpedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#capillarytubeimpedance).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a length or radius that is not positive, or frequencies that are not positive and increasing. |

## CapillaryTube

```python
CapillaryTube(length_m: float, radius_m: float, count: int = 1)
```

Identical open capillary tubes that equalise the static pressure of a
coupler (IEC 61094-2:2009 5.6 and Annex B).

**Attributes**

| Name | Description |
| :--- | :--- |
| `length_m` | $l_\mathrm{C}$, the length of each tube, in m. |
| `radius_m` | $a_\mathrm{t}$, its radius, in m. B.1 notes the impedance goes as the fourth power of it, and that a flow calibration may be needed to know the effective radius of a tube that is not circular. |
| `count` | $n$, the number of identical tubes. |

## CapillaryTubeImpedance

```python
CapillaryTubeImpedance(
    frequencies_hz: NDArray[np.float64],
    length_m: float,
    radius_m: float,
    propagation_coefficient_per_m: NDArray[np.complex128],
    wave_impedance_pa_s_m3: NDArray[np.complex128],
)
```

The acoustic input impedance of an open capillary tube (IEC
61094-2:2009 Formulas (B.1) to (B.3)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `length_m` | $l_\mathrm{C}$, in m. |
| `radius_m` | $a_\mathrm{t}$, in m. |
| `propagation_coefficient_per_m` | $\gamma$, complex, in 1/m. |
| `wave_impedance_pa_s_m3` | $Z_{\mathrm{a,t}}$, the wave impedance of an infinite tube, complex, in Pa·s/m³. |

### CapillaryTubeImpedance.impedance_pa_s_m3

*property*

$Z_{\mathrm{a,C}} = Z_{\mathrm{a,t}}\tanh\gamma l_\mathrm{C}$
(Formula (B.1)), in Pa·s/m³.

### CapillaryTubeImpedance.plot()

```python
CapillaryTubeImpedance.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the real and imaginary parts of $Z_{\mathrm{a,C}}$ in
GPa·s/m³, the unit of Tables B.1 and B.2.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the real-part curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## check_coupler

```python
check_coupler(
    frequencies_hz: ArrayLike,
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    microphones: Sequence[ReciprocityMicrophone],
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    gas: Fluid | None = None,
    heat_conduction_method: str = 'exact',
) -> CouplerCheck
```

Do the coupler formulas of IEC 61094-2:2009 hold for this calibration?

For a plane-wave coupler, Formulas (A.3) and (A.4) "are valid for the
frequency range given by $\omega\rho a^2 > 100\eta$" (A.3), which is
required at the lowest frequency; C.2 recommends a ratio of the distance
between the diaphragms to the diameter of 0,5 to 0,75, reported but not
required. For a large-volume coupler with the approximation (A.2), A.2
states its accuracy for $0{,}125 < R < 8$ and $X > 5$, which
is required; below 20 Hz A.2 asks for the full solution or a larger
uncertainty component, which is reported but not required. In air, the
conditions are checked against the domain Annex F states for its
equations (15 °C to 27 °C, 60 kPa to 110 kPa, 10 % to 90 %).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `coupler` | The coupler. |
| `microphones` | The microphones that close it, two or a triad of one type; the first two give the front cavities that add to the volume, surface and length. |
| `temperature_c` | The temperature, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `gas` | Another gas than air, or `None`. |
| `heat_conduction_method` | The method the calibration uses for $E_V$. |

**Returns:** The [`CouplerCheck`](/phonometry/reference/api/metrology/reciprocity-coupler/#couplercheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not positive and increasing, fewer than two microphones, or an unknown method. |

## coupler_parameter_uncertainty

```python
coupler_parameter_uncertainty(
    frequencies_hz: ArrayLike,
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    microphones: Sequence[ReciprocityMicrophone],
    uncertainties: CouplerInputUncertainties,
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    microphone: int = 1,
    gas: Fluid | None = None,
    heat_conduction_method: str = 'exact',
) -> CouplerParameterUncertainty
```

The uncertainty components of the acoustic transfer impedance, one
parameter at a time (IEC 61094-2:2009 7.5).

"Due to the complexity of the final expression for the pressure
sensitivity in Equation (7) the uncertainty analysis of the acoustic
transfer impedance is usually performed by repeating a calculation while
the various components are changed one at a time by their associated
uncertainty. The difference to the result derived by the unchanged
components is then used to determine the standard uncertainty related to
the various components." This is that: each parameter with a non-zero
standard uncertainty is moved by it, the three transfer impedances of the
triad recomputed, and the change of the sensitivity level of
`microphone` by Formula (7), with the measured electrical transfer
impedances held, is its component. A microphone parameter is moved for
each of the three microphones in turn, as three independent quantities,
and their changes combined in quadrature into the one row of Table 1; so
are the length and the radius of the capillary tubes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `coupler` | The coupler, the same for the three pairs. |
| `microphones` | The three microphones. |
| `uncertainties` | The standard uncertainty of each input quantity, a [`CouplerInputUncertainties`](/phonometry/reference/api/metrology/reciprocity-coupler/#couplerinputuncertainties). |
| `temperature_c` | The temperature, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `microphone` | The microphone whose level is analysed, 1, 2 or 3 (Default: 1). |
| `gas` | A [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) for a coupler filled with a gas other than air (7.3.2.1), as in [`coupler_transfer_impedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_transfer_impedance); `None` (default) takes humid air by Annex F at the conditions. A given gas keeps its properties whatever the conditions, so a step in the static pressure, the temperature or the humidity could not move them with it, and an uncertainty on any of the three is refused. |
| `heat_conduction_method` | The method for $E_V$ (Default: `"exact"`). |

**Returns:** The [`CouplerParameterUncertainty`](/phonometry/reference/api/metrology/reciprocity-coupler/#couplerparameteruncertainty), with a component for each parameter given a non-zero uncertainty.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for other than three microphones, a microphone index that is not 1, 2 or 3, an uncertainty on the volume or surface of a plane-wave coupler (they follow from its length and diameter), one on capillary tubes the coupler does not have, or one on the static pressure, the temperature or the humidity of a coupler filled with a given gas. |

## coupler_transfer_impedance

```python
coupler_transfer_impedance(
    frequencies_hz: ArrayLike,
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    transmitter: ReciprocityMicrophone,
    receiver: ReciprocityMicrophone,
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    gas: Fluid | None = None,
    heat_conduction_method: str = 'exact',
) -> CouplerTransferImpedance
```

The acoustic transfer impedance $Z_{\mathrm{a},12}$ of a coupler
closed by two microphones (IEC 61094-2:2009 5.4 to 5.6).

A [`LargeVolumeCoupler`](/phonometry/reference/api/metrology/reciprocity-coupler/#largevolumecoupler) takes Formula (3): the gas of the coupler,
the two bores of Figure C.2 and the two front cavities (7.3.3.1) as one
compliance, its volume multiplied by $\Delta_\mathrm{H}$ of Formula
(A.1) for the heat conduction, in parallel with the equivalent volumes of
the two microphones. The surface the heat conduction sees is that of the
coupler plus the wall of each bore and front cavity and any thread in it
(7.3.2.2): the diaphragm takes the place of the port it closes
([`LargeVolumeCoupler.closed_volume_m3`](/phonometry/reference/api/metrology/reciprocity-coupler/#largevolumecouplerclosed_volume_m3),
[`LargeVolumeCoupler.closed_surface_m2`](/phonometry/reference/api/metrology/reciprocity-coupler/#largevolumecouplerclosed_surface_m2)).

A [`PlaneWaveCoupler`](/phonometry/reference/api/metrology/reciprocity-coupler/#planewavecoupler) takes Formula (4): a line of length
$l_0$, the coupler plus the two front-cavity depths, terminated at
each end by the microphone's acoustic impedance in parallel with the excess
volume of its front cavity (7.3.3.1); the losses of Formulas (A.3) to (A.5)
give $Z''_{\mathrm{a},12}$, and the same line without them
$Z'_{\mathrm{a},12}$.

Both are then divided by $\Delta_\mathrm{C}$ of Formula (6) for the
capillary tubes. The pair is reciprocal, so which microphone transmits does
not change the result.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `coupler` | The coupler. |
| `transmitter` | Microphone (1). |
| `receiver` | Microphone (2). |
| `temperature_c` | The temperature of the gas, in °C. |
| `static_pressure_pa` | The static pressure $p_\mathrm{s}$, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `gas` | A [`Fluid`](/phonometry/reference/api/fluids/fluids/#fluid) for a coupler filled with a gas other than air; `None` (default) takes humid air by Annex F at the three conditions. |
| `heat_conduction_method` | `"exact"` (default) or `"approximation"` for $E_V$ in a large-volume coupler ([`temperature_transfer_function`](/phonometry/reference/api/metrology/reciprocity-coupler/#temperature_transfer_function)). |

**Returns:** The [`CouplerTransferImpedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#couplertransferimpedance).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not positive and increasing, a static pressure that is not positive, or an unknown method. |

## CouplerCheck

```python
CouplerCheck(
    coupler: str,
    length_to_diameter_ratio: float,
    broadband_margin: float | None,
    lowest_x: float | None,
    lowest_frequency_hz: float,
    *,
    heat_conduction_method: str,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    in_air: bool,
)
```

Whether the formulas of IEC 61094-2:2009 apply to a coupler at the
frequencies and conditions of a calibration.

Built by [`check_coupler`](/phonometry/reference/api/metrology/reciprocity-coupler/#check_coupler). The verdicts are read from the figures
and the conditions the check holds, against the ranges the standard
prints, so they are not fields.

**Attributes**

| Name | Description |
| :--- | :--- |
| `coupler` | `"plane_wave"` or `"large_volume"`. |
| `length_to_diameter_ratio` | $R$: for a plane-wave coupler the distance between the diaphragms, $l_0$, over the diameter (C.2, 5.4), for a large-volume one the length of the cavity over its diameter (A.2). |
| `broadband_margin` | For a plane-wave coupler, $\omega\rho a^2/(100\eta)$ at the lowest frequency, which A.3 requires above 1 for Formulas (A.3) and (A.4); `None` otherwise. |
| `lowest_x` | For a large-volume coupler, $X$ at the lowest frequency; `None` otherwise. It binds only the approximation. |
| `lowest_frequency_hz` | The lowest frequency of the calibration, in Hz. |
| `heat_conduction_method` | The method the calibration uses for $E_V$. |
| `temperature_c` | The temperature, in °C. |
| `static_pressure_pa` | The static pressure, in Pa. |
| `relative_humidity_percent` | The relative humidity, in %. |
| `in_air` | Whether the coupler is filled with air, the medium Annex F states its domain for, rather than another gas. |

### CouplerCheck.approximation_valid

*property*

For a large-volume coupler computed with Formula (A.2), whether A.2 states its accuracy.

$0{,}125 < R < 8$ and $X > 5$; `None` with the full
solution or for a plane-wave coupler.

### CouplerCheck.broadband_valid

*property*

Whether Formulas (A.3) and (A.4) hold at every frequency.

### CouplerCheck.conditions_valid

*property*

For air, whether the conditions are within the domain Annex F states for its equations.

15 °C to 27 °C, 60 kPa to 110 kPa and 10 % to 90 %, ends included;
`None` for another gas.

### CouplerCheck.full_solution_advised

*property*

For a large-volume coupler computed with Formula (A.2), whether a frequency is below 20 Hz.

A.2 then asks for the full solution "or the corresponding uncertainty
component shall be increased accordingly"; `None` with the full
solution or for a plane-wave coupler. Advisory: it does not enter
`passes`, because the larger uncertainty is the caller's to
state.

### CouplerCheck.passes

*property*

The verdict: the formulas the calibration uses hold where it uses them.

### CouplerCheck.plot()

```python
CouplerCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot each condition as its margin to the limit it is held to.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `barh`. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### CouplerCheck.ratio_recommended

*property*

For a plane-wave coupler, whether $R$ is within the 0,5 to 0,75 C.2 recommends.

`None` for a large-volume one. Advisory: it does not enter
`passes`.

## CouplerDimensions

```python
CouplerDimensions(
    microphone_diameter_mm: float,
    front_cavity_diameter_mm: float,
    coupler_diameter_mm: float,
    front_cavity_depth_mm: float,
    coupler_length_mm: float | None = None,
    coupler_length_range_mm: tuple[float, float] | None = None,
    port_length_mm: float | None = None,
    tolerance_mm: float | None = None,
)
```

One column of IEC 61094-2:2009 Table C.1 or Table C.2, the nominal
dimensions of a coupler for one type of laboratory standard microphone,
in millimetres as printed.

**Attributes**

| Name | Description |
| :--- | :--- |
| `microphone_diameter_mm` | ø A, the outer diameter of the microphone. |
| `front_cavity_diameter_mm` | ø B. |
| `coupler_diameter_mm` | ø C. |
| `front_cavity_depth_mm` | D. |
| `coupler_length_mm` | E, the nominal length (Table C.2), or `None`. |
| `coupler_length_range_mm` | E as a range (Table C.1), or `None`. |
| `port_length_mm` | F (Table C.2 only), the length of the bore Figure C.2 draws between each microphone face and the cavity, or `None`. |
| `tolerance_mm` | The ± tolerance Table C.2 prints on C, E and F, or `None`. |

## CouplerInputUncertainties

```python
CouplerInputUncertainties(
    *,
    u_coupler_length_m: float = 0.0,
    u_coupler_diameter_m: float = 0.0,
    u_coupler_volume_m3: float = 0.0,
    u_coupler_surface_area_m2: float = 0.0,
    u_capillary_length_m: float = 0.0,
    u_capillary_radius_m: float = 0.0,
    u_static_pressure_pa: float = 0.0,
    u_temperature_k: float = 0.0,
    u_relative_humidity_percent: float = 0.0,
    u_front_cavity_depth_m: float = 0.0,
    u_front_cavity_volume_m3: float = 0.0,
    u_equivalent_volume_m3: float = 0.0,
    u_resonance_frequency_hz: float = 0.0,
    u_loss_factor: float = 0.0,
)
```

The standard uncertainty of each input quantity of the acoustic transfer
impedance in a coupler: those Table 1 of IEC 61094-2:2009 lists under
"Coupler properties" (7.3.2) and "Microphone parameters" (7.3.3) that
[`coupler_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_parameter_uncertainty) can move.

Each one left at zero contributes no component. A microphone parameter is
the uncertainty of that parameter on each of the three microphones.

**Parameters**

| Name | Description |
| :--- | :--- |
| `u_coupler_length_m` | Of the coupler length, in m. |
| `u_coupler_diameter_m` | Of its diameter, in m. |
| `u_coupler_volume_m3` | Of the volume of a large-volume coupler, in m³. |
| `u_coupler_surface_area_m2` | Of its surface, in m². |
| `u_capillary_length_m` | Of the length of the capillary tubes, in m. |
| `u_capillary_radius_m` | Of their radius, in m. |
| `u_static_pressure_pa` | Of the static pressure, in Pa. |
| `u_temperature_k` | Of the temperature, in K. |
| `u_relative_humidity_percent` | Of the relative humidity, in percentage points. |
| `u_front_cavity_depth_m` | Of each front cavity depth, in m. |
| `u_front_cavity_volume_m3` | Of each front cavity volume, in m³. |
| `u_equivalent_volume_m3` | Of each equivalent volume, in m³. |
| `u_resonance_frequency_hz` | Of each resonance frequency, in Hz. |
| `u_loss_factor` | Of each loss factor. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an uncertainty that is negative or not finite. |

## CouplerParameterUncertainty

```python
CouplerParameterUncertainty(
    frequencies_hz: NDArray[np.float64],
    components_db: Mapping[str, NDArray[np.float64]],
    microphone: int,
)
```

The standard uncertainty of a sensitivity level that each parameter of
the acoustic transfer impedance contributes (IEC 61094-2:2009 7.5).

Built by [`coupler_parameter_uncertainty`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_parameter_uncertainty); ready to pass to
[`reciprocity_uncertainty_budget`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocity_uncertainty_budget).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `components_db` | The component of each parameter, keyed by its name in [`IEC61094_2_TABLE_1`](/phonometry/reference/api/metrology/reciprocity-calibration/#iec61094_2_table_1), in dB at each frequency. |
| `microphone` | The microphone whose level they are for, 1, 2 or 3. |

### CouplerParameterUncertainty.plot()

```python
CouplerParameterUncertainty.plot(
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

## CouplerTransferImpedance

```python
CouplerTransferImpedance(
    frequencies_hz: NDArray[np.float64],
    coupler: str,
    adiabatic_impedance_pa_s_m3: NDArray[np.complex128],
    heat_conducting_impedance_pa_s_m3: NDArray[np.complex128],
    capillary_correction: NDArray[np.complex128],
    heat_conduction: HeatConductionCorrection | None = None,
)
```

The acoustic transfer impedance of a coupler closed by two microphones,
with its corrections (IEC 61094-2:2009 5.4 to 5.6).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `coupler` | `"plane_wave"` or `"large_volume"`. |
| `adiabatic_impedance_pa_s_m3` | $Z'_{\mathrm{a},12}$, adiabatic and without losses (Formula (3) or (4)), in Pa·s/m³. |
| `heat_conducting_impedance_pa_s_m3` | $Z''_{\mathrm{a},12}$, corrected for heat conduction (5.5): with $\Delta_\mathrm{H}$ in a large-volume coupler, with Formulas (A.3) to (A.5) in a plane-wave one, in Pa·s/m³. |
| `capillary_correction` | $\Delta_\mathrm{C}$ of Formula (6), 1 without capillary tubes. |
| `heat_conduction` | The [`HeatConductionCorrection`](/phonometry/reference/api/metrology/reciprocity-coupler/#heatconductioncorrection) of a large-volume coupler, `None` for a plane-wave one. |

### CouplerTransferImpedance.capillary_correction_db

*property*

$-20\lg|\Delta_\mathrm{C}|$, the change of
$|Z_{\mathrm{a},12}|$ the tubes cause, in dB.

### CouplerTransferImpedance.heat_conduction_correction_db

*property*

$20\lg|Z''_{\mathrm{a},12}/Z'_{\mathrm{a},12}|$, in dB.

### CouplerTransferImpedance.plot()

```python
CouplerTransferImpedance.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the heat-conduction and capillary corrections of the transfer
impedance, in dB, against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the heat-conduction curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### CouplerTransferImpedance.transfer_impedance_pa_s_m3

*property*

$Z_{\mathrm{a},12} = Z''_{\mathrm{a},12}/\Delta_\mathrm{C}$,
the impedance the electrical transfer impedance is divided by, in
Pa·s/m³.

## heat_conduction_correction

```python
heat_conduction_correction(
    frequencies_hz: ArrayLike,
    *,
    volume_m3: float,
    surface_area_m2: float,
    length_to_diameter_ratio: float,
    gas: Fluid,
    method: str = 'exact',
) -> HeatConductionCorrection
```

The heat-conduction correction $\Delta_\mathrm{H}$ of a closed
cavity (IEC 61094-2:2009 5.5, A.2).

$\Delta_\mathrm{H}$ multiplies the geometrical volume $V$ in
Formula (3). For a coupler closed by microphones, $V$ and the surface
are those of the coupler together with the front cavities (7.3.2.2), which
[`coupler_transfer_impedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_transfer_impedance) assembles; $R$ is that of the
coupler.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `volume_m3` | The total volume, in m³. |
| `surface_area_m2` | The total surface, in m². |
| `length_to_diameter_ratio` | $R$. |
| `gas` | The gas: its thermal diffusivity and ratio of specific heats. |
| `method` | `"exact"` (default) or `"approximation"` ([`temperature_transfer_function`](/phonometry/reference/api/metrology/reciprocity-coupler/#temperature_transfer_function)). |

**Returns:** The [`HeatConductionCorrection`](/phonometry/reference/api/metrology/reciprocity-coupler/#heatconductioncorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a volume, surface or ratio that is not positive, or frequencies that are not positive and increasing. |

## HeatConductionCorrection

```python
HeatConductionCorrection(
    frequencies_hz: NDArray[np.float64],
    length_to_diameter_ratio: float,
    volume_to_surface_m: float,
    x: NDArray[np.float64],
    transfer_function: NDArray[np.complex128],
    heat_capacity_ratio: float,
    method: str,
)
```

The heat-conduction correction of a closed cavity at low frequencies
(IEC 61094-2:2009 5.5 and A.2, Formula (A.1)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `length_to_diameter_ratio` | $R$. |
| `volume_to_surface_m` | $l$, the volume to surface ratio, in m. |
| `x` | $X = f l^2/(\kappa\alpha_t)$ at each frequency. |
| `transfer_function` | $E_V$ at each frequency. |
| `heat_capacity_ratio` | $\kappa$ of the gas. |
| `method` | `"exact"` or `"approximation"`. |

### HeatConductionCorrection.correction_db

*property*

$20\lg|\Delta_\mathrm{H}|$, the apparent increase of the
volume, in dB.

### HeatConductionCorrection.plot()

```python
HeatConductionCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $|\Delta_\mathrm{H}|$ in dB and its phase against frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the modulus curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### HeatConductionCorrection.volume_factor

*property*

$\Delta_\mathrm{H} = \kappa/(1 + (\kappa - 1)E_V)$, the complex
factor on the geometrical volume (Formula (A.1)).

## IEC61094_2_TABLE_C1

*Constant* (`mapping`).

```python
IEC61094_2_TABLE_C1 = {'LS1P': CouplerDimensions(microphone_diameter_mm=23.77, front_cavity_diameter_mm=18.6, coupler_diameter_mm=18.6, front_cavity_depth_mm=1.95, coupler_length_mm=None, coupler_length_range_mm=(3.5, 9.5), port_length_mm=None, tolerance_mm=None), 'LS2aP': CouplerDimensions(microphone_diameter_mm=13.2, front_cavity_diameter_mm=9.3, coupler_diameter_mm=9.3, front_cavity_depth_mm=0.5, coupler_length_mm=None, coupler_length_range_mm=(3.0, 7.0), port_length_mm=None, tolerance_mm=None), 'LS2bP': CouplerDimensions(microphone_diameter_mm=12.15, front_cavity_diameter_mm=9.8, coupler_diameter_mm=9.8, front_cavity_depth_mm=0.7, coupler_length_mm=None, coupler_length_range_mm=(3.5, 6.0), port_length_mm=None, tolerance_mm=None)}
```

## IEC61094_2_TABLE_C2

*Constant* (`mapping`).

```python
IEC61094_2_TABLE_C2 = {'LS1P': CouplerDimensions(microphone_diameter_mm=23.77, front_cavity_diameter_mm=18.6, coupler_diameter_mm=42.88, front_cavity_depth_mm=1.95, coupler_length_mm=12.55, coupler_length_range_mm=None, port_length_mm=0.8, tolerance_mm=0.03), 'LS2aP': CouplerDimensions(microphone_diameter_mm=13.2, front_cavity_diameter_mm=9.3, coupler_diameter_mm=18.3, front_cavity_depth_mm=0.5, coupler_length_mm=3.5, coupler_length_range_mm=None, port_length_mm=0.4, tolerance_mm=0.03), 'LS2bP': CouplerDimensions(microphone_diameter_mm=12.15, front_cavity_diameter_mm=9.8, coupler_diameter_mm=18.3, front_cavity_depth_mm=0.7, coupler_length_mm=3.5, coupler_length_range_mm=None, port_length_mm=0.4, tolerance_mm=0.03)}
```

## IEC61094_2_TABLE_C3

*Constant* (`mapping`).

```python
IEC61094_2_TABLE_C3 = {800.0: 0.0, 1000.0: -0.002, 1250.0: -0.013, 1600.0: -0.034, 2000.0: -0.06, 2500.0: -0.087}
```

## large_volume_wave_motion_correction

```python
large_volume_wave_motion_correction(
    frequencies_hz: ArrayLike,
    *,
    speed_of_sound_ratio: float = 1.0,
) -> WaveMotionCorrection
```

The wave-motion correction of the large-volume coupler used with LS1P
microphones (IEC 61094-2:2009 C.3, Table C.3).

The correction is to be added to the pressure sensitivity level determined
in the air-filled coupler of Table C.2, when it is not practical to
determine it for the individual coupler and microphones. It is nil up to
800 Hz and printed at five frequencies from 1 kHz to 2,5 kHz, where C.3
sets the upper limit of the coupler for LS1P microphones. A frequency
within 2 % of a printed one takes its value; one between two rows is
interpolated linearly in lg f, and flagged.

For a coupler filled with hydrogen, C.3 allows the same corrections "provided
the frequency scale is multiplied by a factor equal to the ratio of the
speed of sound": `speed_of_sound_ratio` is that factor, and each
frequency is read at its value divided by it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `speed_of_sound_ratio` | The speed of sound in the gas re that in air (Default: 1, air). |

**Returns:** The [`WaveMotionCorrection`](/phonometry/reference/api/metrology/reciprocity-coupler/#wavemotioncorrection).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a frequency whose air equivalent is above 2 500 Hz, or a ratio that is not positive. |

## LargeVolumeCoupler

```python
LargeVolumeCoupler(
    length_m: float,
    diameter_m: float,
    port_length_m: float,
    capillary: CapillaryTube | None = None,
    volume_m3: float | None = None,
    surface_area_m2: float | None = None,
)
```

A large-volume coupler: a cylinder much larger than the front cavities
and the equivalent volumes (IEC 61094-2:2009 C.3, Table C.2 and Figure C.2).

Figure C.2 draws each microphone with its face `port_length_m` back
from the cavity: the front cavity, of diameter B, continues through the
wall of the coupler as a bore of length F to the cavity. Each bore adds
$\pi B^2 F/4$ to the volume of Formula (3) and $\pi B F$ to the
surface the heat conduction sees, with B the front-cavity diameter of the
microphone in it ([`coupler_transfer_impedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#coupler_transfer_impedance)). For the coupler of
Table C.2 the two bores of LS1P microphones are 2,4 % of the cavity, about
0,1 dB on each sensitivity.

**Attributes**

| Name | Description |
| :--- | :--- |
| `length_m` | The length of the cavity, in m (dimension E). |
| `diameter_m` | Its diameter, in m (dimension C). |
| `port_length_m` | The length of the bore between each microphone face and the cavity, in m (dimension F of Table C.2: 0,80 mm for LS1P, 0,40 mm for LS2P); zero for microphones whose faces close the cavity. |
| `capillary` | The capillary tubes, or `None`. |
| `volume_m3` | The measured volume of the cavity of length E, without the bores and the front cavities, in m³, or `None` for the cylinder of `length_m` and `diameter_m`. A volume measured between the two microphone faces includes the bores: pass it with `port_length_m=0`. |
| `surface_area_m2` | Its measured surface, in m², or `None` for that of the closed cylinder; measured between the faces, with `port_length_m=0` as well. |

### LargeVolumeCoupler.cavity_surface_m2

*property*

The surface of the cavity of length E, in m²: the measured one, or
the closed cylinder's.

### LargeVolumeCoupler.cavity_volume_m3

*property*

The volume of the cavity of length E, in m³: the measured one, or
the cylinder's.

### LargeVolumeCoupler.closed_surface_m2()

```python
LargeVolumeCoupler.closed_surface_m2(
    microphones: Sequence[ReciprocityMicrophone],
) -> float
```

The surface the heat conduction sees with the coupler closed by two
microphones, in m²: the closed cylinder, the wall of each bore and of
each front cavity, and any thread in it (7.3.2.2); each diaphragm takes
the place of the port it closes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `microphones` | The two microphones that close it. |

**Returns:** The surface, in m².

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for other than two microphones. |

### LargeVolumeCoupler.closed_volume_m3()

```python
LargeVolumeCoupler.closed_volume_m3(
    microphones: Sequence[ReciprocityMicrophone],
) -> float
```

The volume $V$ of Formula (3) with the coupler closed by two
microphones, in m³: the cavity, the two bores and the two front
cavities (7.3.3.1, Figure C.2).

**Parameters**

| Name | Description |
| :--- | :--- |
| `microphones` | The two microphones that close it. |

**Returns:** $V$, in m³.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for other than two microphones. |

## microphone_acoustic_impedance

```python
microphone_acoustic_impedance(
    electrical_admittance_s: ArrayLike,
    blocked_impedance_ohm: ArrayLike,
    pressure_sensitivity_v_per_pa: ArrayLike,
) -> NDArray[np.complex128]
```

The acoustic impedance of a microphone from its electrical admittance
(IEC 61094-2:2009 E.4, Formula (E.1)).

$$
Z_\mathrm{a} = \frac{Z_\mathrm{e,0} - Y^{-1}}{M_\mathrm{p}^2}
$$

with the admittance $Y$ measured while the diaphragm is terminated by
a closed quarter-wavelength tube ($p = 0$), and the blocked
impedance $Z_\mathrm{e,0}$ at 100 kHz to 200 kHz, where the
diaphragm cannot move. E.4 calculates it "by iteration", because the
pressure sensitivity is itself the result of a calibration that used
$Z_\mathrm{a}$: alternate this with
[`pressure_reciprocity`](/phonometry/reference/api/metrology/reciprocity-coupler/#pressure_reciprocity) until both stop changing.

**Parameters**

| Name | Description |
| :--- | :--- |
| `electrical_admittance_s` | $Y$, complex, in S. |
| `blocked_impedance_ohm` | $Z_\mathrm{e,0}$, complex, in Ω. |
| `pressure_sensitivity_v_per_pa` | $M_\mathrm{p}$, complex, in V/Pa. |

**Returns:** $Z_\mathrm{a}$, complex, in Pa·s/m³.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an admittance or a sensitivity of zero, or a value that is not finite. |

## PlaneWaveCoupler

```python
PlaneWaveCoupler(
    length_m: float,
    diameter_m: float,
    capillary: CapillaryTube | None = None,
)
```

A plane-wave coupler: a cylinder of the diameter of the front cavities
(IEC 61094-2:2009 C.2, Table C.1 and Figure C.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `length_m` | The length of the coupler, between its two faces, in m (dimension E); the distance $l_0$ between the diaphragms adds the depths of the two front cavities (7.3.3.1). |
| `diameter_m` | Its diameter, in m (dimension C). |
| `capillary` | The capillary tubes, or `None` for none or tubes blocked by a wire ($\Delta_\mathrm{C} = 1$). |

## pressure_reciprocity

```python
pressure_reciprocity(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedances_ohm: Sequence[ArrayLike],
    acoustic_transfer_impedances: Sequence[ArrayLike | CouplerTransferImpedance],
    *,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration
```

The pressure sensitivities of three microphones calibrated in pairs in
a coupler (IEC 61094-2:2009 5.7.1, Formula (7)).

Each pair gives the product
$M_{\mathrm{p},i} M_{\mathrm{p},j} = Z_{\mathrm{e},ij}/Z_{\mathrm{a},ij}$
(Formula (2)), and Formula (7) solves the three:

$$
|M_{\mathrm{p},1}| = \left\{\left|\frac{Z_{\mathrm{e},12}Z_{\mathrm{e},31}} {Z_{\mathrm{e},23}}\right|\left|\frac{Z''_{\mathrm{a},23}} {Z''_{\mathrm{a},12}Z''_{\mathrm{a},31}}\right|\left|\frac{\Delta_\mathrm{C,12} \Delta_\mathrm{C,31}}{\Delta_\mathrm{C,23}}\right|\right\}^{1/2}
$$

with similar expressions for the other two, and the phase "by a similar
procedure from the phase angle of each term". The library solves the
complex products together, on the branch described in
[`reciprocity_calibration`](/phonometry/reference/api/metrology/reciprocity-calibration/).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `electrical_transfer_impedances_ohm` | $Z_{\mathrm{e},12}$, $Z_{\mathrm{e},23}$ and $Z_{\mathrm{e},31}$, complex, in Ω, each one value or one per frequency. |
| `acoustic_transfer_impedances` | $Z_{\mathrm{a},12}$, $Z_{\mathrm{a},23}$ and $Z_{\mathrm{a},31}$, each a [`CouplerTransferImpedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#couplertransferimpedance) or complex values in Pa·s/m³ already corrected. |
| `corrections_db` | Corrections added to every sensitivity level, by name, in dB: [`large_volume_wave_motion_correction`](/phonometry/reference/api/metrology/reciprocity-coupler/#large_volume_wave_motion_correction) for the large-volume coupler of LS1P microphones (Default: none). |
| `expanded_uncertainty_db` | The expanded uncertainty of the levels, in dB, one value or one per frequency, from [`reciprocity_uncertainty_budget`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocity_uncertainty_budget) (Default: `None`). |

**Returns:** The [`ReciprocityCalibration`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocitycalibration).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for other than three pairs, values that are zero or not finite, or a column of the wrong length. |

## pressure_reciprocity_pair

```python
pressure_reciprocity_pair(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedance_ohm: ArrayLike,
    acoustic_transfer_impedance: ArrayLike | CouplerTransferImpedance,
    sensitivity_ratio: ArrayLike,
    *,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration
```

The pressure sensitivities of two microphones and an auxiliary sound
source (IEC 61094-2:2009 5.1.3 and 5.7.2, Formula (8)).

$$
|M_{\mathrm{p},1}| = \left|\frac{M_{\mathrm{p},1}}{M_{\mathrm{p},2}}\, \frac{Z_{\mathrm{e},12}}{Z''_{\mathrm{a},12}}\,\Delta_\mathrm{C}\right|^{1/2}
$$

with the ratio of the two sensitivities measured by exposing both to the
same pressure of the auxiliary source; only microphone (1) needs to be
reciprocal (5.1.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, increasing. |
| `electrical_transfer_impedance_ohm` | $Z_{\mathrm{e},12}$, complex, in Ω. |
| `acoustic_transfer_impedance` | $Z_{\mathrm{a},12}$, a [`CouplerTransferImpedance`](/phonometry/reference/api/metrology/reciprocity-coupler/#couplertransferimpedance) or complex values in Pa·s/m³. |
| `sensitivity_ratio` | $M_{\mathrm{p},1}/M_{\mathrm{p},2}$, complex, one value or one per frequency. |
| `corrections_db` | Corrections added to both levels (Default: none). |
| `expanded_uncertainty_db` | The expanded uncertainty, in dB (Default: `None`). |

**Returns:** The [`ReciprocityCalibration`](/phonometry/reference/api/metrology/reciprocity-calibration/#reciprocitycalibration), of two microphones.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for values that are zero or not finite, or a column of the wrong length. |

## ReciprocityMicrophone

```python
ReciprocityMicrophone(
    equivalent_volume_m3: float,
    resonance_frequency_hz: float,
    loss_factor: float,
    front_cavity_volume_m3: float,
    front_cavity_depth_m: float,
    front_cavity_diameter_m: float,
    thread_area_m2: float = 0.0,
)
```

The parameters of a laboratory standard microphone that enter the
acoustic transfer impedance (IEC 61094-2:2009 7.3.3 and Annex E).

The acoustic impedance is the lumped series compliance, mass and
resistance of E.4, written as the equivalent volume at low frequencies,
the resonance frequency and the loss factor:

$$
(2\pi f_0)^2 = (m_\mathrm{a} c_\mathrm{a})^{-1},\qquad V_\mathrm{eq} = c_\mathrm{a}\kappa_\mathrm{r} p_\mathrm{s,r},\qquad d = r_\mathrm{a}\,2\pi f_0\,c_\mathrm{a}
$$

E.4 states this representation is generally sufficient up to about 1,3
times the resonance frequency.

**Attributes**

| Name | Description |
| :--- | :--- |
| `equivalent_volume_m3` | $V_\mathrm{eq}$, the low-frequency real part of the equivalent volume, in m³. |
| `resonance_frequency_hz` | $f_0$, where the imaginary part of $Z_\mathrm{a}$ vanishes, in Hz. |
| `loss_factor` | $d$. |
| `front_cavity_volume_m3` | The measured volume of the front cavity, in m³ (7.3.3.1, E.3). |
| `front_cavity_depth_m` | Its depth, in m (E.2). |
| `front_cavity_diameter_m` | Its diameter, in m (dimension B of Tables C.1 and C.2). |
| `thread_area_m2` | The surface an inner thread of the front cavity adds to the cavity wall, in m²; added to $S_0$ in Formula (A.5) (A.3, [A.4]) and to the surface of a large-volume coupler (7.3.2.2). |

### ReciprocityMicrophone.acoustic_impedance_pa_s_m3()

```python
ReciprocityMicrophone.acoustic_impedance_pa_s_m3(
    frequencies_hz: ArrayLike,
) -> NDArray[np.complex128]
```

$Z_\mathrm{a} = r_\mathrm{a} + \mathrm{j}\omega m_\mathrm{a} + 1/(\mathrm{j}\omega c_\mathrm{a})$, in Pa·s/m³.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz, positive. |

**Returns:** $Z_\mathrm{a}$ at each frequency, in Pa·s/m³.

### ReciprocityMicrophone.complex_equivalent_volume_m3()

```python
ReciprocityMicrophone.complex_equivalent_volume_m3(
    frequencies_hz: ArrayLike,
) -> NDArray[np.complex128]
```

The complex equivalent volume $V_\mathrm{e}$ of Formula (3),
in m³, which tends to `equivalent_volume_m3` at low frequencies:

$$
V_\mathrm{e} = \frac{\kappa_\mathrm{r} p_\mathrm{s,r}}{\mathrm{j}\omega Z_\mathrm{a}} = \frac{V_\mathrm{eq}}{1 - (f/f_0)^2 + \mathrm{j}\,d\,f/f_0}
$$

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |

**Returns:** $V_\mathrm{e}$ at each frequency, in m³.

### ReciprocityMicrophone.compliance_m3_per_pa

*property*

$c_\mathrm{a} = V_\mathrm{eq}/(\kappa_\mathrm{r} p_\mathrm{s,r})$,
in m³/Pa.

### ReciprocityMicrophone.mass_kg_m4

*property*

$m_\mathrm{a} = 1/((2\pi f_0)^2 c_\mathrm{a})$, in kg/m⁴.

### ReciprocityMicrophone.resistance_pa_s_m3

*property*

$r_\mathrm{a} = d/(2\pi f_0 c_\mathrm{a})$, in Pa·s/m³.

## temperature_transfer_function

```python
temperature_transfer_function(
    length_to_diameter_ratio: float,
    x: ArrayLike,
    *,
    method: str = 'exact',
) -> NDArray[np.complex128]
```

Gerber's complex temperature transfer function $E_V$ of a
cylindrical cavity (IEC 61094-2:2009 A.2, Formula (A.2) and Table A.1).

$E_V$ is "the ratio of the space average of the sinusoidal
temperature variation associated with the sound pressure to the sinusoidal
temperature variation that would be generated if the walls of the coupler
were perfectly non-conducting", a function of the length-to-diameter ratio
$R$ of the cylinder and of

$$
X = \frac{f\,l^2}{\kappa\,\alpha_t}
$$

with $l$ its volume to surface ratio and $\alpha_t$ the thermal
diffusivity of the gas.

`method="exact"` (default) sums the full solution of the annex's
reference [A.1], which A.2 requires below 20 Hz unless the uncertainty
component is increased instead, and which reproduces all 96
entries of Table A.1 to the 0,000 01 the annex states for them.
`method="approximation"` is Formula (A.2), whose modulus the annex
states accurate to 0,01 % for $0{,}125 < R < 8$ and $X > 5$;
its first two terms are the approximation the annex allows for a coupler
that is not a right circular cylinder.

**Parameters**

| Name | Description |
| :--- | :--- |
| `length_to_diameter_ratio` | $R$, positive. |
| `x` | $X$, one value or several, positive. |
| `method` | `"exact"` or `"approximation"`. |

**Returns:** $E_V$, complex, with the shape of `x`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a ratio or an $X$ that is not positive and finite, or an unknown method. |

## WaveMotionCorrection

```python
WaveMotionCorrection(
    frequencies_hz: NDArray[np.float64],
    correction_db: NDArray[np.float64],
    speed_of_sound_ratio: float,
)
```

The wave-motion correction of the large-volume coupler for LS1P
microphones (IEC 61094-2:2009 C.3, Table C.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The frequencies, in Hz. |
| `correction_db` | The correction added to the pressure sensitivity level, in dB. |
| `speed_of_sound_ratio` | The ratio of the speed of sound in the gas of the coupler to that in air, 1 for air. |

Whether each value was interpolated between rows of the table
(`interpolated`) is read from the frequencies and the ratio, so it
is not a field.

### WaveMotionCorrection.interpolated

*property*

Whether each value was interpolated between rows of Table C.3.

A frequency whose air equivalent lies within 2 % of a printed row
takes that row, and one below the first row takes its nil
correction; any other is interpolated between two rows.

**Returns:** One boolean per frequency.

### WaveMotionCorrection.plot()

```python
WaveMotionCorrection.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the correction against frequency, with the rows of Table C.3.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes to draw on, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the correction curve. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

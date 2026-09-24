---
title: "vibration.structural.transfer_stiffness"
description: "Dynamic transfer stiffness of resilient elements (ISO 10846, Parts 1 to 5)."
sidebar:
  label: "transfer_stiffness"
---

Dynamic transfer stiffness of resilient elements (ISO 10846, Parts 1 to 5).

The vibro-acoustic transfer property of a resilient element (a vibration
isolator, mount, bellows or hose) is its **dynamic transfer stiffness**: the
frequency-dependent ratio of the *blocking force* phasor `F2,b` on the output
(receiver) side to the displacement phasor `u1` on the input (source) side,
with the output blocked (ISO 10846-1, 3.7), in N/m:

$$
k_{2,1} = \frac{F_{2,\mathrm{b}}}{u_1}
$$

For an isolator between two structures of large driving-point stiffness, the
force delivered to the receiver approximates this blocking force (ISO 10846-1,
Equation 7), so $k_{2,1}$ characterises the isolator's transmission.
Results are reported as a **level**, in dB, re the reference stiffness
$k_0 = 1$ N/m (ISO 10846-2 and -3, 3.17):

$$
L_k = 10 \log_{10}\!\left( \frac{|k_{2,1}|^2}{k_0^2} \right) = 20 \log_{10}\!\left( \frac{|k_{2,1}|}{k_0} \right)
$$

and, in the low-frequency range where inertial forces in the element are
negligible, the **loss factor** is the tangent of the phase angle of
$k_{2,1}$ (ISO 10846-1, 3.8):
$\eta = \operatorname{Im}(k_{2,1}) / \operatorname{Re}(k_{2,1})$.

Three laboratory methods determine $k_{2,1}$, in four parts:

* **Direct method** (ISO 10846-2 for resilient supports, ISO 10846-4 for
  other elements): measure the blocked output force `F2,b` and the input
  displacement `u1` directly: $k_{2,1} = F_{2,\mathrm{b}} / u_1$. The
  mass between the element and the output force transducers biases the
  measured force; ISO 10846-4 Inequality (3) (ISO 10846-2 Inequality (2))
  bounds it, see [`check_output_mass`](/phonometry/reference/api/vibration/transfer-stiffness/#check_output_mass).
* **Indirect method** (ISO 10846-3, and ISO 10846-4 for other elements): load
  the output with a compact blocking mass `m2` and measure the vibration
  transmissibility $T = u_2/u_1$; the blocking force is the mass's
  inertia force (ISO 10846-3, Equation 1):
  $k_{2,1} = -(2\pi f)^2 (m_2 + m_\mathrm{f}) T$ for $T \ll 1$,
  where `mf` is the mass of the output flange of the test element. The
  approximation is valid only where $|T| \le 0.1$ (Inequality (2):
  $\Delta L_{1,2} \ge 20$ dB) and while the blocking mass still
  behaves rigidly,
  $|10 \log_{10}(m_{2,\mathrm{eff}}^2/m_2^2)| \le 1$ dB (ISO 10846-3
  Inequality (3), ISO 10846-4 Inequality (5)); see
  [`transfer_stiffness_indirect`](/phonometry/reference/api/vibration/transfer-stiffness/#transfer_stiffness_indirect) and [`effective_blocking_mass`](/phonometry/reference/api/vibration/transfer-stiffness/#effective_blocking_mass).
* **Driving-point method** (ISO 10846-5): measure the input force and the
  input acceleration with the output blocked, which gives the driving-point
  stiffness $k_{1,1}$ (Formula (3)). Below the upper limiting frequency
  $f_\mathrm{UL}$ of clause 6.2 its band averages stand for those of
  $k_{2,1}$ within 2 dB (Formula (7)); see
  [`driving_point_stiffness`](/phonometry/reference/api/vibration/transfer-stiffness/#driving_point_stiffness).

Every part reports the result as one-third-octave-band averages of the squared
magnitude over at least five narrow-band frequencies (ISO 10846-2 Formula (6),
-3 Formula (7), -4 Formula (11), -5 Formula (6)): [`band_averaged_stiffness`](/phonometry/reference/api/vibration/transfer-stiffness/#band_averaged_stiffness).
The adequacy conditions the parts share, the output blocked by 20 dB and the
unwanted input directions 15 dB down, are [`check_blocked_output`](/phonometry/reference/api/vibration/transfer-stiffness/#check_blocked_output) and
[`check_unwanted_input`](/phonometry/reference/api/vibration/transfer-stiffness/#check_unwanted_input), and the Annex B uncertainty budget of
ISO 10846-5 is [`driving_point_uncertainty`](/phonometry/reference/api/vibration/transfer-stiffness/#driving_point_uncertainty).

The dynamic transfer stiffness is a member of the frequency-response-function
family (ISO 10846-1, Annex A / Table A.2):
$k = j\omega Z = -\omega^2 m_{\mathrm{eff}}$, so it converts to
mechanical impedance and effective mass through
[`phonometry.vibration.convert_frf`](/phonometry/reference/api/vibration/mechanical-mobility/#convert_frf) (`"dynamic_stiffness"` \<->
`"impedance"` \<-> `"apparent_mass"`). This module feeds the structure-borne
source and building prediction standards (ISO 9611, EN 15657, EN 12354-5).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## band_averaged_stiffness

```python
band_averaged_stiffness(
    frequencies: ArrayLike,
    stiffness: ArrayLike,
    *,
    valid: ArrayLike | None = None,
) -> BandAveragedStiffness
```

One-third-octave-band averages of a narrow-band stiffness (ISO 10846).

The band average of every part of the series, ISO 10846-2:2008
Formula (6), -3:2002 Formula (7), -4:2003 Formula (11) and -5:2008
Formula (6):

$$
k_\mathrm{av} = \left\{ \frac{1}{n} \sum_{i=1}^{n} \lvert k(f_i) \rvert^2 \right\}^{1/2}
$$

"where the summation is performed over a minimum of n = 5 frequencies".
Averaging the squared magnitude "is chosen to emphasize the maxima in the
stiffness values" (NOTE 1), and the phase is lost (NOTE 3). Each line is
assigned to the base-ten one-third-octave band that encloses it, the bands
named by the ISO 266 centre frequencies the parts ask for.

**Fewer than five lines.** The parts leave no band value to a band that
holds fewer: the analyser shall resolve "at least five distinct
frequencies per one-third-octave band", and a stepped or swept sine shall
put at least five frequencies in "each one-third-octave band for which
stiffness data are determined". Such a band is returned undetermined (NaN)
and a [`TransferStiffnessWarning`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnesswarning) names it. Lines `valid` marks
`False` are left out first, as the parts exclude results that fail their
adequacy conditions; bands beyond the outermost valid line are not listed,
and a band inside the range with no valid line at all is undetermined
without a warning, since its lines were excluded rather than missing.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Narrow-band frequencies $f_i$, in hertz (one-dimensional, distinct). |
| `stiffness` | Dynamic stiffness $k(f_i)$ at each frequency (complex or real, finite), in N/m: a transfer stiffness $k_{2,1}$ or a driving-point stiffness $k_{1,1}$. |
| `valid` | Per frequency, whether the line enters the average (Default: `None`, every line). |

**Returns:** The [`BandAveragedStiffness`](/phonometry/reference/api/vibration/transfer-stiffness/#bandaveragedstiffness).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not one-dimensional, finite, positive and distinct, a stiffness of another length or not finite, a mask that is not boolean or has another length, or no valid line. |

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | when a band holds between one and four valid lines. |

## BandAveragedStiffness

```python
BandAveragedStiffness(
    nominal_frequencies: np.ndarray,
    center_frequencies: np.ndarray,
    stiffness: np.ndarray,
    line_counts: np.ndarray,
)
```

One-third-octave-band averages of a narrow-band dynamic stiffness (ISO 10846).

Every part of the series reduces the narrow-band stiffness to one value
per one-third-octave band by averaging the squared magnitude over the
`n` lines of the band (ISO 10846-2:2008 Formula (6), -3:2002 Formula (7),
-4:2003 Formula (11), -5:2008 Formula (6)):

$$
k_\mathrm{av} = \left\{ \frac{1}{n} \sum_{i=1}^{n} \lvert k(f_i) \rvert^2 \right\}^{1/2}, \qquad n \ge 5
$$

and reports it as the level
$L_{k,\mathrm{av}} = 10 \lg(k_\mathrm{av}^2/k_0^2)$ re
$k_0 = 1$ N/m (ISO 10846-2, -3 and -4 3.18, ISO 10846-5 3.17). A band
holding fewer than [`MIN_FREQUENCIES_PER_BAND`](/phonometry/reference/api/vibration/transfer-stiffness/#min_frequencies_per_band) lines has no value:
its stiffness is NaN and `determined` is `False`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `nominal_frequencies` | Preferred centre frequency of each band (ISO 266), in hertz. |
| `center_frequencies` | Exact base-ten midband frequency $1000 \cdot 10^{x/10}$ of each band, in hertz; a line belongs to the band whose edges, a factor $10^{1/20}$ either side, enclose it. |
| `stiffness` | Band average $k_\mathrm{av}$, in N/m, NaN where the band holds fewer than five lines. |
| `line_counts` | Number of narrow-band lines averaged in each band. |

### BandAveragedStiffness.determined

*property*

Per band, whether it holds enough lines to have a value.

**Returns:** One boolean per band.

### BandAveragedStiffness.levels

*property*

Band level $L_{k,\mathrm{av}}$ re 1 N/m, in dB, NaN where undetermined.

**Returns:** One level per band.

### BandAveragedStiffness.plot()

```python
BandAveragedStiffness.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the band levels, with the undetermined bands marked.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the band-level bars. |

**Returns:** The axes.

## base_transmissibility

```python
base_transmissibility(
    frequency: ArrayLike,
    mass: float,
    stiffness: float,
    damping: float = 0.0,
) -> np.ndarray
```

Transmissibility of a mass on an ideal resilient element (model).

The output mass `m` on a massless Kelvin-Voigt element (spring `k` in
parallel with a viscous damper `c`) driven at the input has the
base-excitation transmissibility

$$
T = \frac{u_2}{u_1} = \frac{k + j\omega c}{k - \omega^2 m + j\omega c}
$$

This ideal-element model is the counterpart of the indirect-method test
arrangement (ISO 10846-3): feeding `T` into
[`transfer_stiffness_indirect`](/phonometry/reference/api/vibration/transfer-stiffness/#transfer_stiffness_indirect) with the same mass recovers the
element's transfer stiffness $k + j\omega c$ in the high-frequency
limit $T \ll 1$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency `f`, in hertz (scalar or array). |
| `mass` | Output mass `m`, in kg. |
| `stiffness` | Element stiffness `k`, in N/m. |
| `damping` | Viscous damping `c`, in N.s/m (Default: 0.0). |

**Returns:** The complex transmissibility `T`.

## blocking_force_ratio

```python
blocking_force_ratio(
    driving_point_stiffness: ArrayLike,
    termination_stiffness: ArrayLike,
) -> np.ndarray
```

Ratio of the delivered force to the blocking force (ISO 10846-1, Eq. 6).

For an isolator driving a receiving structure, the output force for a
given source displacement `u1` is
$F_2 = k_{2,1} u_1 / (1 + k_{2,2}/k_\mathrm{t})$
(Equation (6)), where `k2,2` is the isolator's output driving-point
stiffness (output blocked at the input) and `kt` the dynamic
driving-point stiffness of the termination. This function returns

$$
\frac{F_2}{F_{2,\mathrm{b}}} = \frac{1}{1 + k_{2,2}/k_\mathrm{t}}
$$

the factor by which the delivered force deviates from the blocking force
$F_{2,\mathrm{b}} = k_{2,1} u_1$ of Equation (7). For
$|k_{2,2}| < 0.1 |k_\mathrm{t}|$ the ratio is within 10 % of unity
($1/1.1 = 0.909$ at the limit), which is the
stiffness mismatch that justifies characterising an isolator by its
blocked transfer stiffness alone.

**Parameters**

| Name | Description |
| :--- | :--- |
| `driving_point_stiffness` | Output driving-point stiffness `k2,2` of the isolator (complex, scalar or array), in N/m. |
| `termination_stiffness` | Driving-point stiffness `kt` of the receiving structure (complex, scalar or array, non-zero), in N/m. |

**Returns:** The complex ratio `F2/F2,b`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a zero termination stiffness. |

## check_blocked_output

```python
check_blocked_output(
    frequencies: ArrayLike,
    input_acceleration_level_db: ArrayLike,
    output_acceleration_level_db: ArrayLike,
) -> LevelDifferenceCheck
```

Is the output side blocked well enough for the stiffness to mean anything?

Every part of ISO 10846 is valid "only for those frequencies where"

$$
\Delta L_{1,2} = L_{a1} - L_{a2} \ge 20\ \text{dB}
$$

(ISO 10846-2:2008 Inequality (1), -3:2002 Inequality (2) with `a2` the
acceleration of the blocking mass, -4:2003 Inequality (2), -5:2008
Inequality (1)): a smaller difference means too little stiffness
mismatch between the element and the foundation, or flanking transmission.
For the indirect method the same 20 dB is the $|T| \le 0.1$ of
[`TRANSMISSIBILITY_LIMIT`](/phonometry/reference/api/vibration/transfer-stiffness/#transmissibility_limit).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz (narrow-band lines or band centres). |
| `input_acceleration_level_db` | Input acceleration level $L_{a1}$, in dB, one per frequency. |
| `output_acceleration_level_db` | Output acceleration level $L_{a2}$, in dB re the same reference, one per frequency; `-inf` for an output that does not move. |

**Returns:** The [`LevelDifferenceCheck`](/phonometry/reference/api/vibration/transfer-stiffness/#leveldifferencecheck) (`condition="blocked_output"`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not finite and positive, or level spectra that do not carry one level per frequency. |

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | where $\Delta L_{1,2} < 20$ dB. |

## check_output_mass

```python
check_output_mass(
    frequencies: ArrayLike,
    output_mass_kg: float,
    output_force_level_db: ArrayLike,
    output_acceleration_level_db: ArrayLike,
) -> OutputMassCheck
```

Is the mass in front of the output force transducers light enough?

ISO 10846-4:2003 Inequality (3), and ISO 10846-2:2008 Inequality (2) for
resilient supports:

$$
m_0 \le 0{,}06 \times \frac{10^{L_{F2}/20}}{10^{L_{a2}/20}}\ \text{kg}
$$

with $L_{F2}$ the force level re 1 µN and $L_{a2}$ the
acceleration level re 1 µm/s² of the output side (ISO 10846-4 3.15 and
3.16, the references of ISO 1683). If it fails, NOTE 2 says what to do: a
lighter `m0`, or stiffer (more, or larger) force transducers. See
[`OutputMassCheck`](/phonometry/reference/api/vibration/transfer-stiffness/#outputmasscheck) for the bias it bounds.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz. |
| `output_mass_kg` | The mass `m0` between the element and the output force transducers: the output flange, the force distribution plate and half the mass of the transducers (ISO 10846-4), or the plate and half the transducers for a resilient support (ISO 10846-2), in kg. |
| `output_force_level_db` | Measured output force level $L_{F2}$, in dB re 1 µN, one per frequency. |
| `output_acceleration_level_db` | Output acceleration level $L_{a2}$, in dB re 1 µm/s², one per frequency. |

**Returns:** The [`OutputMassCheck`](/phonometry/reference/api/vibration/transfer-stiffness/#outputmasscheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not finite and positive, a negative mass, or level spectra that do not carry one finite level per frequency. |

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | where `m0` exceeds its limit. |

## check_unwanted_input

```python
check_unwanted_input(
    frequencies: ArrayLike,
    excitation_level_db: ArrayLike,
    unwanted_level_db: ArrayLike,
) -> LevelDifferenceCheck
```

Does the input move in the excitation direction alone, by 15 dB?

Every part of ISO 10846 is valid only where the input acceleration in the
excitation direction exceeds that in the directions perpendicular to it
by at least 15 dB:

$$
L_{a(\mathrm{excitation})} - L_{a(\mathrm{unwanted})} \ge 15\ \text{dB}
$$

(ISO 10846-2:2008 Inequality (3), -3:2002 Inequality (5), -4:2003
Inequality (7), -5:2008 Inequality (2)), the unwanted accelerations read
at the edge of the excitation mass or force distribution plate in the
plane of the input flange. With several unwanted directions, the loudest
one at each frequency decides. (ISO 10846-2:2008 7.6.1, which excludes
the lines that fail this pre-run, prints the reference as "6.1,
Inequality (1)", the blocked-output condition; the condition meant is
6.4, Inequality (3), as the same sentence in Parts 3 to 5 shows. See the
errata register.)

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz. |
| `excitation_level_db` | Acceleration level in the excitation direction, in dB, one per frequency. |
| `unwanted_level_db` | Acceleration level in a perpendicular direction, in dB re the same reference, one per frequency; or one row per direction, shape `(directions, frequencies)`. |

**Returns:** The [`LevelDifferenceCheck`](/phonometry/reference/api/vibration/transfer-stiffness/#leveldifferencecheck) (`condition="unwanted_input"`).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not finite and positive, or level spectra that do not carry one level per frequency. |

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | where the difference is below 15 dB. |

## driving_point_stiffness

```python
driving_point_stiffness(
    frequencies: ArrayLike,
    input_force_n: ArrayLike,
    input_acceleration_m_s2: ArrayLike,
    *,
    output_acceleration_m_s2: ArrayLike | None = None,
    unwanted_acceleration_m_s2: ArrayLike | None = None,
) -> DrivingPointStiffnessResult
```

Dynamic driving-point stiffness of a resilient support (ISO 10846-5 Formula (3)).

$k_{1,1}(f) = -(2\pi f)^2 F_1 / a_1$, from the input force and the
input acceleration measured with the output side of the element blocked.
With the output acceleration given, Inequality (1),
$\Delta L_{1,2} \ge 20$ dB, is checked line by line
([`check_blocked_output`](/phonometry/reference/api/vibration/transfer-stiffness/#check_blocked_output)); with the unwanted accelerations given,
Inequality (2), 15 dB ([`check_unwanted_input`](/phonometry/reference/api/vibration/transfer-stiffness/#check_unwanted_input)). A line that fails
either raises a [`TransferStiffnessWarning`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnesswarning) and is excluded from the
evaluation. The result finds $f_\mathrm{UL}$ (6.2) and averages the
valid lines into bands (Formulas (6), (7)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz, strictly increasing; the sweep needs lines between 1 Hz and 20 Hz for the low-frequency value, and 7.5 asks for a 0,2 Hz spacing there. |
| `input_force_n` | Input force phasor `F1`, in N. |
| `input_acceleration_m_s2` | Input acceleration phasor `a1`, in m/s², non-zero. |
| `output_acceleration_m_s2` | Output-flange acceleration phasor `a2`, in m/s² (Default: `None`, Inequality (1) not checked). |
| `unwanted_acceleration_m_s2` | Input acceleration phasor in a direction perpendicular to the excitation, in m/s², or one row per direction (Default: `None`, Inequality (2) not checked). |

**Returns:** The [`DrivingPointStiffnessResult`](/phonometry/reference/api/vibration/transfer-stiffness/#drivingpointstiffnessresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not finite, positive and strictly increasing, phasors that do not carry one value per frequency, a zero input acceleration, or no adequate line from 1 Hz to 20 Hz. |

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | where Inequality (1) or (2) fails. |

## driving_point_uncertainty

```python
driving_point_uncertainty(
    band_level_db: float,
    *,
    repeatability_range_db: float,
    signal_uncertainty_db: float = 0.3,
    instrumentation_uncertainty_db: float = 0.5,
    test_rig_uncertainty_db: float = 0.2886751345948129,
    discrepancy_uncertainty_db: float = 1.1547005383792517,
    linearity_uncertainty_db: float = 0.43301270189221935,
) -> DrivingPointUncertainty
```

Uncertainty of a band level measured by the driving-point method (ISO 10846-5 Annex B).

Table B.1, built on [`phonometry.metrology.combine_uncertainty`](/phonometry/reference/api/metrology/uncertainty/#combine_uncertainty):

- $\hat{L}_{k,\mathrm{av}}$, signal processing and background
  noise, normal, 0,3 dB (B.3.1);
- $\delta_\mathrm{ins}$, instrumentation, normal, 0,5 dB when only
  the minimum requirements are met, 0,3 dB "with good choices and
  precautions" (B.3.2);
- $\delta_\mathrm{rep}$, installation repeatability, rectangular,
  $p/\sqrt{3}$ for a spread of $2p$ between the highest and
  lowest level of repeated installations (B.3.3);
- $\delta_\mathrm{rig}$, the test rig, rectangular,
  $1/(2\sqrt{3})$ dB (B.3.4);
- $\delta_\mathrm{dps}$, the driving-point stiffness standing for
  the transfer stiffness, rectangular over $\pm 2$ dB,
  $2/\sqrt{3}$ dB (B.3.5);
- $\delta_\mathrm{lin}$, linearity, rectangular,
  $1{,}5/(2\sqrt{3})$ dB (B.3.6).

The last three are the expressions B.3.4 to B.3.6 print, 0,289, 1,155
and 0,433 dB. Table B.1 carries them rounded up to one decimal, 0,3, 1,2
and 0,5 dB, the conservative rounding an uncertainty may take
(ISO/IEC Guide 98-3:2008, 7.2.6); the defaults keep the expressions.
With the defaults and no repeatability spread, $u = 1{,}394$ dB and
$U = 2{,}789$ dB, against 1,456 dB and 2,91 dB with the rounded
table. Every default can be replaced by a reasoned estimate, as the annex
encourages, and the note to (B.3) allows doing so band by band.

**Parameters**

| Name | Description |
| :--- | :--- |
| `band_level_db` | The measured band level $\hat{L}_{k,\mathrm{av}}$, in dB re 1 N/m. |
| `repeatability_range_db` | The difference $2p$ between the highest and lowest band level of repeated installations, in dB (0 for none observed). |
| `signal_uncertainty_db` | Standard uncertainty of $\hat{L}_{k,\mathrm{av}}$, in dB (Default: 0,3). |
| `instrumentation_uncertainty_db` | Standard uncertainty $u_\mathrm{ins}$, in dB (Default: 0,5). |
| `test_rig_uncertainty_db` | Standard uncertainty $u_\mathrm{rig}$, in dB (Default: $1/(2\sqrt{3})$). |
| `discrepancy_uncertainty_db` | Standard uncertainty $u_\mathrm{dps}$, in dB (Default: $2/\sqrt{3}$). |
| `linearity_uncertainty_db` | Standard uncertainty $u_\mathrm{lin}$, in dB (Default: $1{,}5/(2\sqrt{3})$). |

**Returns:** The [`DrivingPointUncertainty`](/phonometry/reference/api/vibration/transfer-stiffness/#drivingpointuncertainty).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-finite band level, or a negative or non-finite spread or standard uncertainty. |

## DrivingPointStiffnessResult

```python
DrivingPointStiffnessResult(
    frequencies: np.ndarray,
    driving_point_stiffness: np.ndarray,
    adequate: np.ndarray | None = None,
)
```

A dynamic driving-point stiffness and the transfer stiffness it stands for (ISO 10846-5).

With the output of the element blocked, the input force and acceleration
give the driving-point stiffness (ISO 10846-5:2008 Formula (3))

$$
k_{1,1}(f) = \frac{F_1}{u_1} = -(2\pi f)^2 \frac{F_1}{a_1}
$$

which equals the transfer stiffness $k_{2,1}$ at low frequencies
only. Clause 6.2 finds where that ends: the upper limiting frequency
$f_\mathrm{UL}$ is "the lowest frequency, at which the driving point
stiffness level becomes 2 dB smaller than the low-frequency stiffness",
the low-frequency value being "the average for 1 Hz to 20 Hz". Below it
the band averages of $k_{1,1}$ stand for those of $k_{2,1}$,
$k_\mathrm{av} = k_{\mathrm{av}(2,1)} \approx k_{\mathrm{av}(1,1)}$,
within 2 dB (Formula (7)).

The low-frequency value is taken as the Formula (6) average of the lines
from 1 Hz to 20 Hz, the one average the part defines for a stiffness; for
the flat stiffness the clause presumes, it and the mean of the levels
agree. The crossing of the 2 dB threshold is interpolated in the logarithm
of frequency between the last line above it and the first line on or
below it, and every line above $f_\mathrm{UL}$ is excluded; a line
exactly on the threshold is $f_\mathrm{UL}$ itself and stays in,
since 8.3 states the 2 dB for $f \le f_\mathrm{UL}$. Lines that
fail Inequality (1) or (2) (`adequate`) are excluded from the
evaluation altogether, as 7.6.1 requires, and so are lines below the
1 Hz at which the method starts.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz, strictly increasing. |
| `driving_point_stiffness` | Complex $k_{1,1}$ at each frequency, in N/m. |
| `adequate` | Per frequency, whether Inequalities (1) and (2) hold, or `None` when they were not checked. |

### DrivingPointStiffnessResult.band_average()

```python
DrivingPointStiffnessResult.band_average() -> BandAveragedStiffness
```

One-third-octave-band averages of $k_{1,1}$ over the valid lines (Formulas (6), (7)).

Only the lines at or below $f_\mathrm{UL}$ are averaged. For
those bands 8.3 states that the band averages of $k_{1,1}$
stand for those of $k_{2,1}$ within 2 dB, and Annex B (B.3.5)
assumes the same $\pm 2$ dB for its uncertainty budget; the
criterion of 6.2 itself only watches $k_{1,1}$ fall below its
own low-frequency value, so the 2 dB is the standard's statement,
not something the average can prove line by line.

Up to 20 Hz the 0,2 Hz line spacing of 7.5 leaves the lowest bands
with fewer than five lines; the NOTE to clause 9 m) accepts
narrow-band data there, so those bands are left undetermined without
a warning.

**Returns:** The [`BandAveragedStiffness`](/phonometry/reference/api/vibration/transfer-stiffness/#bandaveragedstiffness).

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | when a band above 20 Hz holds fewer than [`MIN_FREQUENCIES_PER_BAND`](/phonometry/reference/api/vibration/transfer-stiffness/#min_frequencies_per_band) valid lines. |

### DrivingPointStiffnessResult.levels

*property*

Driving-point stiffness level re 1 N/m at each frequency, in dB.

### DrivingPointStiffnessResult.loss_factor

*property*

Loss factor $\eta = \operatorname{Im}(k_{1,1})/\operatorname{Re}(k_{1,1})$ (Formula (4)).

### DrivingPointStiffnessResult.low_frequency_level_db

*property*

The low-frequency stiffness level of 6.2, in dB re 1 N/m.

**Returns:** $10 \lg$ of the mean squared magnitude over the adequate lines from 1 Hz to 20 Hz, re $k_0^2$.

### DrivingPointStiffnessResult.magnitude

*property*

Driving-point stiffness magnitude $|k_{1,1}|$, in N/m.

### DrivingPointStiffnessResult.plot()

```python
DrivingPointStiffnessResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the driving-point stiffness level with the 6.2 threshold and $f_\mathrm{UL}$.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the level curve. |

**Returns:** The axes.

### DrivingPointStiffnessResult.threshold_level_db

*property*

The level 2 dB below the low-frequency value, whose crossing is $f_\mathrm{UL}$.

**Returns:** The threshold, in dB re 1 N/m.

### DrivingPointStiffnessResult.upper_limiting_frequency_hz

*property*

$f_\mathrm{UL}$ of 6.2, in hertz, or `None` when the sweep never reaches it.

**Returns:** $f_\mathrm{UL}$, or `None`.

### DrivingPointStiffnessResult.valid

*property*

Per frequency, whether the line is evaluated.

A line is evaluated when it is adequate, lies at or above 1 Hz and
lies at or below $f_\mathrm{UL}$: 8.3 states the accuracy of
Formula (7) "if $f \le f_\mathrm{UL}$", so a line that sits
exactly on the 2 dB threshold, and is $f_\mathrm{UL}$ itself,
is kept.

**Returns:** One boolean per frequency.

## DrivingPointUncertainty

```python
DrivingPointUncertainty(budget: UncertaintyResult)
```

Uncertainty budget of a band level measured by the driving-point method (ISO 10846-5 Annex B).

The band level is modelled as the measured one plus five corrections of
zero estimate (Formula (B.1)),

$$
L_{k,\mathrm{av}} = \hat{L}_{k,\mathrm{av}} + \delta_\mathrm{ins} + \delta_\mathrm{rep} + \delta_\mathrm{rig} + \delta_\mathrm{dps} + \delta_\mathrm{lin}
$$

every sensitivity coefficient is 1, the combined standard uncertainty is
the root sum of squares of the six contributions (Formula (B.2)) and the
expanded uncertainty for 95 % coverage is $U = 2u$ (Formula (B.3)),
the six inputs being "assumed to result in a normal distribution".

**Attributes**

| Name | Description |
| :--- | :--- |
| `budget` | The GUM budget, one row per input quantity of Table B.1. |

### DrivingPointUncertainty.band_level_db

*property*

The band level $L_{k,\mathrm{av}}$, in dB re 1 N/m.

### DrivingPointUncertainty.combined_uncertainty_db

*property*

Combined standard uncertainty $u(L_{k,\mathrm{av}})$, in dB (Formula (B.2)).

### DrivingPointUncertainty.coverage_factor

*property*

The coverage factor 2 of Formula (B.3).

### DrivingPointUncertainty.expanded_uncertainty_db

*property*

Expanded uncertainty $U = 2u$, in dB (Formula (B.3)).

### DrivingPointUncertainty.plot()

```python
DrivingPointUncertainty.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the contribution of each input quantity, with `u` and `U`.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the contribution bars. |

**Returns:** The axes.

## effective_blocking_mass

```python
effective_blocking_mass(
    frequencies: ArrayLike,
    force_n: ArrayLike,
    first_acceleration_m_s2: ArrayLike,
    second_acceleration_m_s2: ArrayLike,
    *,
    blocking_mass_kg: float,
) -> EffectiveBlockingMass
```

Effective mass of a blocking mass from one force and two accelerations.

ISO 10846-4:2003 Formula (6) (ISO 10846-3:2002 Formula (4)):
$m_{2,\mathrm{eff}} = |2 F_2 / (a'_1 + a''_1)|$, with the block
supported on soft springs (a mass-spring resonance below 10 Hz), the
force `F2` applied along the axis through its centre of mass, and the
two accelerometers placed symmetrically inside the contact area `S` a
distance $\sqrt{S}$ apart; the force and acceleration measurements
follow ISO 7626-1 and ISO 7626-2. See [`EffectiveBlockingMass`](/phonometry/reference/api/vibration/transfer-stiffness/#effectiveblockingmass) for
`f3`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz, strictly increasing. |
| `force_n` | Excitation force phasor `F2`, in N, one per frequency. |
| `first_acceleration_m_s2` | Acceleration phasor $a'_1$, in m/s², one per frequency. |
| `second_acceleration_m_s2` | Acceleration phasor $a''_1$, in m/s², one per frequency. |
| `blocking_mass_kg` | The mass `m2` of the block, in kg. |

**Returns:** The [`EffectiveBlockingMass`](/phonometry/reference/api/vibration/transfer-stiffness/#effectiveblockingmass).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for frequencies that are not finite, positive and strictly increasing, phasors of another length, a zero or non-finite effective mass, or a non-positive `m2`. |

## EffectiveBlockingMass

```python
EffectiveBlockingMass(
    frequencies: np.ndarray,
    effective_mass_kg: np.ndarray,
    blocking_mass_kg: float,
)
```

Effective mass of a blocking mass over frequency, and its limit `f3`.

The indirect method treats the blocking mass as rigid; above some
frequency it no longer is, and the force it measures departs from
$m_2 a_2$. Driven alone on soft supports through its centre of mass,
with two accelerometers a spacing $\sqrt{S}$ apart inside the contact
area `S`, its effective mass is (ISO 10846-4:2003 Formula (6); the same
quantity is ISO 10846-3:2002 Formula (4))

$$
m_{2,\mathrm{eff}} = \left| \frac{2 F_2}{a'_1 + a''_1} \right|
$$

and the results of the indirect method are presented only up to `f3`,
"the lowest frequency at which the effective mass deviates more than 12 %
(i.e. 1 dB in level) from the mass m2", where
$|\Delta L| = |20 \lg(m_{2,\mathrm{eff}}/m_2)| \le 1$ dB
(ISO 10846-4 Inequality (5), ISO 10846-3 Inequality (3)). A deviation
below 40 Hz is the mass-spring behaviour of the block on its supports and
is ignored in finding `f3`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz, strictly increasing. |
| `effective_mass_kg` | $m_{2,\mathrm{eff}}$ at each frequency, in kg. |
| `blocking_mass_kg` | The mass `m2` of the block, in kg. |

### EffectiveBlockingMass.deviation_db

*property*

$\Delta L = 20 \lg(m_{2,\mathrm{eff}}/m_2)$, in dB.

**Returns:** One deviation per frequency.

### EffectiveBlockingMass.ignored_below_hz

*property*

The 40 Hz below which a deviation is not read as a loss of rigidity, in hertz.

**Returns:** 40.0 (ISO 10846-3 6.2.3, ISO 10846-4 6.3.3.2).

### EffectiveBlockingMass.plot()

```python
EffectiveBlockingMass.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the deviation from `m2` with the 1 dB tolerance and `f3`.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the deviation curve. |

**Returns:** The axes.

### EffectiveBlockingMass.upper_frequency_limit_hz

*property*

`f3`, in hertz, or `None` when the mass stays rigid over the sweep.

The deviation crosses 1 dB between the last line inside it and the
first line (from 40 Hz up) outside it; the crossing is interpolated in
the logarithm of frequency.

**Returns:** `f3`, or `None`.

### EffectiveBlockingMass.valid

*property*

Per frequency, whether it lies below the first line outside 1 dB.

**Returns:** One boolean per frequency.

## indirect_transfer_stiffness_result

```python
indirect_transfer_stiffness_result(
    frequency: ArrayLike,
    transmissibility: ArrayLike,
    blocking_mass: float,
    *,
    flange_mass: float = 0.0,
) -> TransferStiffnessResult
```

Indirect-method transfer stiffness bundled as a [`TransferStiffnessResult`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnessresult).

See [`transfer_stiffness_indirect`](/phonometry/reference/api/vibration/transfer-stiffness/#transfer_stiffness_indirect) for the ISO 10846-3 validity
conditions (Inequalities (2) and (3)); bands with $|T| > 0.1$
trigger a [`TransferStiffnessWarning`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnesswarning), and the result marks them
not [`valid`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnessresult), so that
[`band_average`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnessresultband_average) leaves them out.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequencies `f`, in hertz (array). |
| `transmissibility` | Vibration transmissibility $T = u_2/u_1$ (complex). |
| `blocking_mass` | Blocking mass `m2`, in kg (> 0). |
| `flange_mass` | Output-flange mass `mf`, in kg (Default: 0.0). |

**Returns:** The [`TransferStiffnessResult`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnessresult) (indirect method).

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | where any $\lvert T\rvert > 0.1$ (Inequality (2) violated). |

## LevelDifferenceCheck

```python
LevelDifferenceCheck(
    frequencies: np.ndarray,
    difference_db: np.ndarray,
    limit_db: float,
    condition: Literal['blocked_output', 'unwanted_input'],
)
```

An ISO 10846 level-difference condition judged frequency by frequency.

Two conditions of the series take this form. The output is blocked where
the input acceleration level exceeds the output one by at least 20 dB,
$\Delta L_{1,2} = L_{a1} - L_{a2} \ge 20$ dB (`"blocked_output"`;
ISO 10846-2:2008 Inequality (1), -3:2002 Inequality (2), -4:2003
Inequality (2), -5:2008 Inequality (1)). The input is unidirectional where
the acceleration in the excitation direction exceeds that in every
direction perpendicular to it by at least 15 dB,
$L_{a(\mathrm{excitation})} - L_{a(\mathrm{unwanted})} \ge 15$ dB
(`"unwanted_input"`; ISO 10846-2:2008 Inequality (3), -3:2002
Inequality (5), -4:2003 Inequality (7), -5:2008 Inequality (2)). The
measurements are valid only at the frequencies where the condition holds.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies judged, in hertz. |
| `difference_db` | The level difference at each frequency, in dB (`+inf` where the second level is that of a zero signal). |
| `limit_db` | The least difference the condition accepts, in dB. |
| `condition` | `"blocked_output"` or `"unwanted_input"`. |

### LevelDifferenceCheck.holds

*property*

Per frequency, whether the difference reaches the limit.

**Returns:** One boolean per frequency.

### LevelDifferenceCheck.passes

*property*

Whether the condition holds at every frequency judged.

**Returns:** `True` when no frequency falls short of the limit.

### LevelDifferenceCheck.plot()

```python
LevelDifferenceCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the level difference against its limit, failures marked.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the level-difference curve. |

**Returns:** The axes.

## loss_factor

```python
loss_factor(stiffness: ArrayLike) -> np.ndarray
```

Loss factor
$\eta = \operatorname{Im}(k_{2,1}) / \operatorname{Re}(k_{2,1})$
(ISO 10846-1, 3.8).

Valid in the low-frequency range where inertial forces in the element are
negligible; it is the tangent of the phase angle of the transfer stiffness.

**Parameters**

| Name | Description |
| :--- | :--- |
| `stiffness` | Dynamic transfer stiffness $k_{2,1}$ (complex, scalar or array, with a non-zero real part), in N/m. |

**Returns:** The loss factor `eta` (dimensionless).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a purely imaginary stiffness ($\operatorname{Re}(k_{2,1}) = 0$), for which the loss factor is undefined. |

## MIN_FREQUENCIES_PER_BAND

*Constant* (`int`).

```python
MIN_FREQUENCIES_PER_BAND = 5
```

## OutputMassCheck

```python
OutputMassCheck(
    frequencies: np.ndarray,
    output_mass_kg: float,
    mass_limit_kg: np.ndarray,
)
```

The mass in front of the output force transducers, against its limit.

In the direct method the mass `m0` between the element and the output
force transducers (the output flange, the force distribution plate and
half the transducers) biases the measured force by its own inertia force
$m_0 a_2$. ISO 10846-4:2003 Inequality (3) bounds it, and so does
ISO 10846-2:2008 Inequality (2) for resilient supports, where the mass is
called `m2` and counts the force distribution plate and half the
transducers only:

$$
m_0 \le 0{,}06 \times \frac{10^{L_{F2}/20}}{10^{L_{a2}/20}}\ \text{kg}
$$

with the levels re 1 µN and 1 µm/s² (ISO 10846-4 3.15 and 3.16), so the
bound is $0{,}06\,|F_2|/|a_2|$. Since
$F_\mathrm{b} = F_2 + m_0 a_2$, the force levels differ by at most
$-20 \lg(1 - r)$ dB with $r = m_0 |a_2| / |F_2|$, which at
the bound ($r = 0{,}06$) is 0,54 dB against the 0,51 dB of an
inertia force in phase with the measured one: the "0,5 dB" of NOTE 1.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies judged, in hertz. |
| `output_mass_kg` | The mass `m0`, in kg. |
| `mass_limit_kg` | The right-hand side of the inequality at each frequency, in kg. |

### OutputMassCheck.bias_bound_db

*property*

Largest $|L_{F\mathrm{b}} - L_{F2}|$ the mass can cause, in dB.

$-20 \lg(1 - r)$, reached when the inertia force opposes the
measured force; `inf` where $r \ge 1$, when the mass can
cancel the force altogether.

**Returns:** One bound per frequency, in dB.

### OutputMassCheck.holds

*property*

Per frequency, whether `m0` is within its limit.

**Returns:** One boolean per frequency.

### OutputMassCheck.inertia_ratio

*property*

The inertia force over the measured force, $r = m_0 |a_2| / |F_2|$.

**Returns:** One ratio per frequency; 0,06 where `m0` sits on its limit.

### OutputMassCheck.passes

*property*

Whether `m0` is within its limit at every frequency judged.

**Returns:** `True` when the inequality holds throughout.

### OutputMassCheck.plot()

```python
OutputMassCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the mass limit over frequency against the mass in place.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the mass-limit curve. |

**Returns:** The axes.

## REFERENCE_STIFFNESS

*Constant* (`float`).

```python
REFERENCE_STIFFNESS = 1.0
```

## transfer_stiffness_direct

```python
transfer_stiffness_direct(
    blocking_force: ArrayLike,
    input_displacement: ArrayLike,
) -> np.ndarray
```

Dynamic transfer stiffness by the direct method (ISO 10846-2).

$k_{2,1} = F_{2,\mathrm{b}} / u_1$, the blocked output force phasor over
the input displacement phasor.

**Parameters**

| Name | Description |
| :--- | :--- |
| `blocking_force` | Blocked output force phasor `F2,b` (complex), in N. |
| `input_displacement` | Input displacement phasor `u1` (complex, non-zero), in m. |

**Returns:** The dynamic transfer stiffness $k_{2,1}$, in N/m.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a zero input displacement (dead input channel). |

## transfer_stiffness_indirect

```python
transfer_stiffness_indirect(
    frequency: ArrayLike,
    transmissibility: ArrayLike,
    blocking_mass: float,
    *,
    flange_mass: float = 0.0,
) -> np.ndarray
```

Dynamic transfer stiffness by the indirect method (ISO 10846-3, Eq. 1).

$k_{2,1} = -(2\pi f)^2 (m_2 + m_\mathrm{f}) T$: the blocking force is the
inertia force of a compact blocking mass `m2` (plus the output flange
mass `mf`), derived from the measured vibration transmissibility
$T = u_2/u_1$. Valid for $T \ll 1$ (i.e. well above the
mass/spring resonance).

**Validity (ISO 10846-3, clause 6).** The $T \ll 1$ approximation
of Formula (1) is required accurate within 1 dB, i.e. within 12 % of the
calculated stiffness magnitude. This holds only where Inequality (2) is
met: $\Delta L_{1,2} = L_{a1} - L_{a2} \ge 20$ dB, i.e.
$|T| \le 0.1$ ([`TRANSMISSIBILITY_LIMIT`](/phonometry/reference/api/vibration/transfer-stiffness/#transmissibility_limit)). Lines with
`|T|` above that limit
(routine near or below the mass/spring resonance) trigger a
[`TransferStiffnessWarning`](/phonometry/reference/api/vibration/transfer-stiffness/#transferstiffnesswarning); the result marks each of them as not
valid, and its band average leaves them out. The upper frequency limit
`f3` additionally requires the blocking mass to vibrate as a rigid
body: results are valid only while its effective mass `m2,eff`,
measured per Formula (4) as
$m_{2,\mathrm{eff}} = 2 F_2 / (a'_1 + a''_1)$ (two accelerometers
spaced $D = \sqrt{S}$ across the contact area), stays within 1 dB
of the rigid mass,
$|10 \log_{10}(m_{2,\mathrm{eff}}^2 / m_2^2)| \le 1$ dB
(Inequality (3), 6.2.3); [`effective_blocking_mass`](/phonometry/reference/api/vibration/transfer-stiffness/#effective_blocking_mass) finds `f3`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | Frequency `f`, in hertz (scalar or array). |
| `transmissibility` | Vibration transmissibility $T = u_2/u_1$ (complex, scalar or array; velocity and acceleration ratios have the same value). |
| `blocking_mass` | Blocking mass `m2`, in kg (> 0). |
| `flange_mass` | Output-flange mass `mf`, in kg (Default: 0.0). |

**Returns:** The dynamic transfer stiffness $k_{2,1}$, in N/m.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive frequency or blocking mass. |

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | where any $\lvert T\rvert > 0.1$ (Inequality (2) violated). |

## transfer_stiffness_level

```python
transfer_stiffness_level(
    stiffness: ArrayLike,
    *,
    reference: float = 1.0,
) -> np.ndarray
```

Level of the dynamic transfer stiffness (ISO 10846-2/-3, 3.17).

$L_k = 20 \log_{10}(|k_{2,1}| / k_0)$ dB, with `k0` the reference
stiffness.

**Parameters**

| Name | Description |
| :--- | :--- |
| `stiffness` | Dynamic transfer stiffness $k_{2,1}$ (complex or real, scalar or array, non-zero), in N/m. |
| `reference` | Reference stiffness `k0` (Default: 1 N/m), in N/m. |

**Returns:** The level `L_k`, in dB re `k0`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive reference, a non-finite stiffness, or a zero stiffness magnitude (a dead channel has no level). |

## TransferStiffnessResult

```python
TransferStiffnessResult(
    frequencies: np.ndarray,
    transfer_stiffness: np.ndarray,
    blocking_mass: float | None = None,
    valid: np.ndarray | None = None,
)
```

A dynamic transfer stiffness over frequency (ISO 10846).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Frequencies, in hertz. |
| `transfer_stiffness` | Complex $k_{2,1}$ per frequency, in N/m. |
| `blocking_mass` | Blocking mass `m2` used (indirect method), in kg, or `None` for the direct method. |
| `valid` | Per frequency, whether the line meets the adequacy conditions of its part and so enters the band average (results that fail them "shall be excluded from the evaluation of the dynamic stiffness function", ISO 10846-2, -4 and -5 7.6.1, ISO 10846-3 7.5.1), or `None` when every line does. The indirect method sets it from Inequality (2), $\vert T\vert  \le 0.1$. |

### TransferStiffnessResult.band_average()

```python
TransferStiffnessResult.band_average() -> BandAveragedStiffness
```

One-third-octave-band averages of $k_{2,1}$ (every part's band average).

ISO 10846-2:2008 Formula (6), ISO 10846-3:2002 Formula (7) and
ISO 10846-4:2003 Formula (11) average the squared magnitude over the
narrow-band lines of each band; see [`band_averaged_stiffness`](/phonometry/reference/api/vibration/transfer-stiffness/#band_averaged_stiffness).
Lines `valid` marks as failing their adequacy conditions are
left out, as the parts require.

**Returns:** The [`BandAveragedStiffness`](/phonometry/reference/api/vibration/transfer-stiffness/#bandaveragedstiffness).

**Warns**

| Warning | When |
| :--- | :--- |
| TransferStiffnessWarning | when a band holds fewer than [`MIN_FREQUENCIES_PER_BAND`](/phonometry/reference/api/vibration/transfer-stiffness/#min_frequencies_per_band) valid lines. |

### TransferStiffnessResult.levels

*property*

Transfer-stiffness level `L_k` re 1 N/m, in dB (3.17).

### TransferStiffnessResult.loss_factor

*property*

Loss factor $\eta = \operatorname{Im}/\operatorname{Re}$
per frequency (3.8).

### TransferStiffnessResult.magnitude

*property*

Transfer-stiffness magnitude $|k_{2,1}|$, in N/m.

### TransferStiffnessResult.plot()

```python
TransferStiffnessResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the transfer-stiffness level `L_k(f)`.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

### TransferStiffnessResult.report()

```python
TransferStiffnessResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render a dynamic-transfer-stiffness fiche to a PDF (ISO 10846).

Writes a one-page transfer-stiffness characterisation report for a
resilient element: the standard-basis line naming the determination
method (direct, ISO 10846-2:2008, or indirect blocking-mass,
ISO 10846-3:2002; definition per ISO 10846-1:2008), an optional metadata
header, a two-panel body with a compact table of the FRF's
characteristic points (the method, the blocking mass for the indirect
method, the frequency range, and the low-frequency stiffness plateau
$|k_{2,1}|$, its level `L_k` and the loss factor `eta`
there) beside
the transfer-stiffness level spectrum `L_k(f)`, the one-third-octave
band levels of `band_average` that the test report of
ISO 10846-2 (9 m)) and ISO 10846-3 (10 j)) presents, a boxed
low-frequency `L_k` with the stiffness magnitude and method
alongside, and a footer identity/disclaimer block.

The characteristic points are read at the lowest line `valid`
keeps, since the part excludes the others from the evaluation, and the
spectrum draws the excluded lines apart. A band holding fewer than
five valid lines prints its line count instead of a level. A
transfer-stiffness determination is a characterisation, so there is
no pass/fail verdict.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata) supplying the header identity (`specimen` is the tested resilient element) and the footer identity; the `requirement` field is ignored. |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | Accepted for a uniform `.report()` signature; the transfer-stiffness fiche has a single body layout, so it has no effect. |
| `language` | Fiche language: `"en"` (default, English) or `"es"` (Spanish, with a comma decimal separator). |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"` or `language` is unknown, or `valid` marks every line as failing its adequacy conditions (there is then no value to report). |
| ImportError | If reportlab or matplotlib is not installed. The fiche always embeds the `L_k(f)` spectrum, so both are required (`pip install "phonometry[report,plot]"`). |

### TransferStiffnessResult.to()

```python
TransferStiffnessResult.to(target: str) -> np.ndarray
```

Convert $k_{2,1}$ to an FRF (ISO 10846-1 Annex A / Table A.2).

`target` is `"impedance"` ($Z = k/(j\omega)$) or
`"apparent_mass"` ($m_{\mathrm{eff}} = -k/\omega^2$); see
[`phonometry.vibration.convert_frf`](/phonometry/reference/api/vibration/mechanical-mobility/#convert_frf).

## TransferStiffnessWarning

Advisory when an ISO 10846 adequacy condition or a band count fails.

## TRANSMISSIBILITY_LIMIT

*Constant* (`float`).

```python
TRANSMISSIBILITY_LIMIT = 0.1
```

---
title: "electroacoustics.induction_loop_components"
description: "Components of an audio-frequency induction-loop system: the loop, its amplifier, the neck loop."
sidebar:
  label: "induction_loop_components"
---

Components of an audio-frequency induction-loop system: the loop, its amplifier, the neck loop.

IEC 62489-1:2010, with its Amendment 1:2014 (read in the consolidated BS EN
62489-1:2010+A1:2015), says how the manufacturer of an induction-loop
amplifier, of a loop and of a neck loop measures and states what the
component does. IEC 60118-4:2014 then judges the installed system built from
them ([`phonometry.electroacoustics.induction_loop`](/phonometry/reference/api/electroacoustics/induction-loop/)). This module holds
the parts of IEC 62489-1 that are arithmetic, and the loop formulas both
standards lean on.

The loop and its field
----------------------

A current $I$ in a loop of $N$ turns produces a magnetic field
strength $H$, in amperes per metre, that is proportional to
$N I$ everywhere and falls with distance from the conductor. IEC
60118-4:2014 E.1 gives the one closed form it uses, the field at the centre
of a single-turn square loop of side $d$, in its own plane,

$$
H = \frac{2\sqrt{2}\,I}{\pi d},
$$

and extends it to a rectangle of sides $d_1$ and $d_2$:
"Provided that the sides d1, d2 of a rectangular loop are not extremely
different", $d$ is taken as $\sqrt{d_1 d_2}$
([`loop_centre_field`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loop_centre_field)). Everything else about the field is a figure in
that standard. Here it is computed: [`rectangular_loop_field`](/phonometry/reference/api/electroacoustics/induction-loop-components/#rectangular_loop_field) sums the
Biot-Savart field of the four straight sides exactly, at any point, which is
how the E.1 formula is checked (it is exact for the square and off by 0,35 dB
for a rectangle of aspect ratio 1,5). Two of the figures are reproduced: the
curves of Figure E.2 b), both components within about half a decibel, taken
across the 10-unit width of its 15 by 10 loop, as E.1 describes them (the
figure's panel a) puts the vertical-field line along the length, see
`docs/ERRATA.md`), and the currents of Figure H.1 through
[`loop_current`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loop_current). Figures E.3 to E.5 and A.1 draw the same kind of
pattern and are not checked point by point.

IEC 62489-1:2010 5.4.10.2 fixes where an amplifier's field is measured: 1,4 m
above the centre of a horizontal square loop whose resistance and inductance
equal the rated load. [`loop_current`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loop_current) gives the current that loop needs
for a field strength, and [`loop_dimensions`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loop_dimensions) answers 5.4.11 the other way
round, the largest square loop, or loop of aspect ratio 3:1, whose centre
reaches 400 mA/m at that height with the amplifier's current.

The loop as a load
------------------

The loop is a resistance in series with an inductance (IEC 62489-1 B.2).
The resistance is $R = \rho l / a$ for a conductor of length $l$
and area $a$ ([`loop_resistance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loop_resistance)), with the resistivity of standard
annealed copper, 1/58 ohm square millimetre per metre at 20 degrees Celsius
and a temperature coefficient of 0,00393 per degree (IEC 60028:1925, clause I).
The inductance of a rectangle of round wire is Grover's Formula (58)
([`rectangular_loop_inductance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#rectangular_loop_inductance)); for $N$ turns it is multiplied by
$N^2$, the perfect coupling Table B.1 assumes. The impedance
$|Z| = \sqrt{R^2 + (2\pi f L)^2}$ rises above the frequency where the
reactance equals the resistance, where it is $\sqrt{2}$ times the
resistance (IEC 60118-4 E.3), and the voltage the amplifier has to deliver is
$U = I |Z|$ ([`LoopImpedance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loopimpedance)).

Table B.1 of IEC 62489-1 is the oracle. Its six resistances are reproduced by
the 20 degree resistivity with the perimeter of each loop, which for the
0,35 m by 0,45 m counter loop is 1,6 m and not the printed 1,5 m (see
`docs/ERRATA.md`). Grover's formula reproduces four of its six inductances
to the printed microhenry once the term for the flux inside the wire is left
out: 189, 22, 47 and 109 microhenries. Table B.1 does not say which formula it
used, and the two it does not reproduce, the neck loop (79 against 85) and the
15 m by 40 m loop (206 against 218), are not reached by any reading of the
wire size either, so they are not claimed. The internal term is kept by
default here, because at audio frequencies the skin depth in copper (2 mm at
1 kHz) is larger than the radius of every conductor Table B.1 lists.

The amplifier
-------------

IEC 62489-1 clause 5 lists what an amplifier's specification states, and
which of it is measured. The measured characteristics that are computations
are:

* the maximum (distortion-limited) output current, 5.4.7: the 1 kHz load
  current is raised until the total harmonic distortion across the resistive
  part of the load reaches the rated value, and the current is the total
  voltage across that resistance over its value
  ([`maximum_output_current`](/phonometry/reference/api/electroacoustics/induction-loop-components/#maximum_output_current));
* the compliance voltage, 5.4.8: the maximum positive-going and negative-going
  peak voltages across the rated load, over at least 60 s of the specified
  pink noise, averaged and divided by $\sqrt{2}$
  ([`compliance_voltage`](/phonometry/reference/api/electroacoustics/induction-loop-components/#compliance_voltage));
* the noise, 5.4.9: the equivalent input noise voltage
  $U_\mathrm{n} = U I_\mathrm{n} / I$ and the signal-to-noise ratio
  $S = 10\lg(I_\mathrm{r}^2 / I_\mathrm{n}^2)$ dB
  ([`equivalent_input_noise_voltage`](/phonometry/reference/api/electroacoustics/induction-loop-components/#equivalent_input_noise_voltage),
  [`amplifier_signal_to_noise_ratio`](/phonometry/reference/api/electroacoustics/induction-loop-components/#amplifier_signal_to_noise_ratio));
* the frequency response, 5.4.12: the load current at one-third-octave
  centres from at least 50 Hz to 8 kHz, with the response at 1 kHz taken as
  0 dB ([`amplifier_frequency_response`](/phonometry/reference/api/electroacoustics/induction-loop-components/#amplifier_frequency_response));
* the automatic gain control, 5.4.13: the steady-state output current against
  the source e.m.f., and the recommendation Amendment 1 added as 5.4.13.4, an
  input range of at least 32 dB for an output change of at most 3 dB
  ([`agc_characteristic`](/phonometry/reference/api/electroacoustics/induction-loop-components/#agc_characteristic));
* the phase error of the quadrature network of a phased loop array, 5.4.14:
  the maximum deviation from 90 degrees between the loop currents over 100 Hz
  to 5 kHz ([`quadrature_phase_error`](/phonometry/reference/api/electroacoustics/induction-loop-components/#quadrature_phase_error)).

The rated conditions (5.4.1 to 5.4.6) are what the manufacturer states and are
not measured; the standard measuring conditions of 5.2.2 put the output
current 10 dB below the rated one. The test signal of 5.4.8.2 b) is the pink
noise of IEC 60118-4 6.4, generated by
[`loop_test_noise`](/phonometry/reference/api/electroacoustics/induction-loop/#loop_test_noise).

The neck loop
-------------

Clause 9, added by Amendment 1, specifies a neck loop by the input voltage
that produces 400 mA/m at the telecoil position of the test jig of Annex E,
the smallest magnitude of its input impedance over 100 Hz to 5 kHz rounded to
the nearest ohm, and its frequency response, stated in text as the
frequencies where it differs from the response at 1 kHz by 3 dB
([`neck_loop_characteristics`](/phonometry/reference/api/electroacoustics/induction-loop-components/#neck_loop_characteristics)). The draft Amendment 2 (prEN
62489-1:2010/prA2:2017, read in E DIN EN 62489-1/A2:2017-10) replaces Annex D
with two example specifications: type 1, for audio sources powered by two
primary 1,5 V cells and higher voltage supplies, by a DC resistance of 32 ohm
plus or minus 5 %, and type 2, a neck loop with a transformer or an amplifier,
by an input DC resistance of at least 32 ohm, both reaching 400 mA/m on the
jig with at most 1,06 V at the input ([`NECK_LOOP_TYPES`](/phonometry/reference/api/electroacoustics/induction-loop-components/#neck_loop_types),
[`verify_neck_loop`](/phonometry/reference/api/electroacoustics/induction-loop-components/#verify_neck_loop)). It is a draft, and
this module cites it as one. Its Table D.1 (the field a type 1 loop reaches
from a 3 V and a 9 V battery) rests on a source model the draft does not give
and is not reproduced.

What is not here
----------------

The loop listener and the assistive listening device of Annex F, and the
monitoring devices of clause 10, are specified by values to be met (a
sensitivity of 150 mV into 32 ohm for 400 mA/m, a volume range of 40 dB plus
or minus 5 dB, a THD of 3 %) that are single comparisons with nothing to
compute. The target frequency response of Annex F is stated by two corner
frequencies and two final slopes, with its shape only in Figure F.1. The
electromagnetic exposure of IEC 62489-2 is outside this library.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## agc_characteristic

```python
agc_characteristic(
    source_emf_db: ArrayLike,
    output_level_db: ArrayLike,
) -> AgcCharacteristic
```

The output/input characteristic of an amplifier and its AGC range (5.4.13).

From standard measuring conditions the source e.m.f. is reduced to zero
and raised in steps, the output current being read at each once it has
settled (5.4.13.2), and the result is plotted with the e.m.f. on a
logarithmic abscissa and the output current level in dB referred to the
rated maximum output current (5.4.13.3). Amendment 1 adds the
recommendation of 5.4.13.4: "an input level range of at least 32 dB for a
maximum output level change of 3 dB".

That range is read here as the widest span of input level over which the
output varies by at most 3 dB, on the characteristic interpolated
linearly between the measured steps, and found exactly: its ends are
steps, or the inputs where the line crosses a step's output level or that
level 3 dB up or down. For a characteristic that rises and then holds,
which is what an automatic gain control is (Annex A), it runs from the
input where the output is 3 dB below its top to the highest input
measured.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_emf_db` | Source e.m.f. levels, in dB re any fixed voltage, strictly ascending. |
| `output_level_db` | Output current level at each, in dB re the rated maximum output current. |

**Returns:** An [`AgcCharacteristic`](/phonometry/reference/api/electroacoustics/induction-loop-components/#agccharacteristic).

## AgcCharacteristic

```python
AgcCharacteristic(
    source_emf_db: np.ndarray,
    output_level_db: np.ndarray,
    agc_range_db: float,
    agc_range_start_db: float,
    agc_range_end_db: float,
)
```

The steady-state output/input characteristic of an amplifier (5.4.13).

**Attributes**

| Name | Description |
| :--- | :--- |
| `source_emf_db` | The source e.m.f. levels, in dB, ascending. |
| `output_level_db` | The output current level at each, in dB referred to the rated maximum output current (5.4.13.3). |
| `agc_range_db` | The widest span of input level over which the output level changes by no more than 3 dB, in dB: the quantity IEC 62489-1:2010+A1:2014 5.4.13.4 recommends to be at least 32 dB. |
| `agc_range_start_db` | The input level where that span starts, in dB. |
| `agc_range_end_db` | The input level where it ends, in dB. |

### AgcCharacteristic.plot()

```python
AgcCharacteristic.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw output level against input level, as Figure A.1.

The span of `agc_range_db` is shaded, with the 3 dB output band
it is taken over.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the characteristic's `Axes.plot`. |

### AgcCharacteristic.recommended_range_db

*property*

The range 5.4.13.4 recommends, 32 dB, for comparison with `agc_range_db`.

## amplifier_frequency_response

```python
amplifier_frequency_response(
    frequencies_hz: ArrayLike,
    output_current_a: ArrayLike,
) -> AmplifierFrequencyResponse
```

The frequency response of an amplifier into its rated load (5.4.12).

Under standard measuring conditions, with the automatic gain control and
compression disabled or with the input the manufacturer states, the
signal frequency is stepped through the one-third-octave centres "over the
range of at least 50 Hz to 8 kHz" and the load current measured at each
(5.4.12.2). The result is presented with the response at 1 kHz taken as
0 dB (5.4.12.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The measurement frequencies, in hertz, ascending and including 1000 Hz. |
| `output_current_a` | The RMS load current at each, in amperes. |

**Returns:** An [`AmplifierFrequencyResponse`](/phonometry/reference/api/electroacoustics/induction-loop-components/#amplifierfrequencyresponse).

## amplifier_signal_to_noise_ratio

```python
amplifier_signal_to_noise_ratio(
    rated_current_a: float,
    noise_current_a: float,
) -> float
```

The signal-to-noise ratio of an amplifier (IEC 62489-1:2010 5.4.9.2).

$$
S = 10\lg\frac{I_\mathrm{r}^2}{I_\mathrm{n}^2}\ \mathrm{dB},
$$

the rated output current against the A-weighted output current with the
source e.m.f. reduced to zero.

**Parameters**

| Name | Description |
| :--- | :--- |
| `rated_current_a` | The rated output current $I_\mathrm{r}$, in amperes. |
| `noise_current_a` | The noise output current $I_\mathrm{n}$, in amperes. |

**Returns:** The signal-to-noise ratio, in dB.

## AmplifierFrequencyResponse

```python
AmplifierFrequencyResponse(
    frequencies_hz: np.ndarray,
    output_current_a: np.ndarray,
    response_db: np.ndarray,
)
```

The frequency response of an amplifier into its load (IEC 62489-1:2010 5.4.12).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The measurement frequencies, in hertz, ascending. |
| `output_current_a` | The load current measured at each, in amperes. |
| `response_db` | The current level relative to the one at 1 kHz, in dB, so 0 dB at 1 kHz (5.4.12.3). |

### AmplifierFrequencyResponse.at()

```python
AmplifierFrequencyResponse.at(frequency_hz: ArrayLike) -> np.ndarray
```

The response at any frequency inside the measured range, in dB.

Interpolated linearly against the logarithm of frequency, the way a
response measured at one-third-octave centres is read between them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | Frequencies, in hertz. |

**Returns:** The response there, dB re 1 kHz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a frequency that is not finite and positive, or lies outside the measured range. |

### AmplifierFrequencyResponse.plot()

```python
AmplifierFrequencyResponse.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the response against frequency, 0 dB at 1 kHz (5.4.12.3).

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the response curve's `Axes.plot`. |

## compliance_voltage

```python
compliance_voltage(voltage_v: ArrayLike) -> float
```

The compliance voltage of an amplifier (IEC 62489-1:2010 5.4.8).

The voltage across the rated load is recorded "over a period of at least
60 s" of the specified pink noise with the automatic gain control fully in
operation, or with the RMS output current 6 dB below the maximum output
current (5.4.8.2 c). The magnitudes of its most positive and most negative
peaks are averaged and divided by $\sqrt{2}$ (5.4.8.2 d), which gives
the RMS voltage of the sine with the same peaks.

**Parameters**

| Name | Description |
| :--- | :--- |
| `voltage_v` | The recorded load voltage, in volts, sampled at more than 50 000 samples per second or through more than 25 kHz of bandwidth (5.4.8.2 c). |

**Returns:** The compliance voltage, in volts.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a record that does not swing both ways. |

## equivalent_input_noise_voltage

```python
equivalent_input_noise_voltage(
    source_emf_v: float,
    output_current_a: float,
    noise_current_a: float,
) -> float
```

The equivalent input noise voltage of an amplifier (IEC 62489-1:2010 5.4.9).

With the amplifier below the action of its automatic gain control, a 1 kHz
source e.m.f. $U$ gives an output current $I$; with the e.m.f.
reduced to zero the A-weighted output current is $I_\mathrm{n}$. The
1 kHz input that would give the same current as the noise is

$$
U_\mathrm{n} = \frac{U I_\mathrm{n}}{I}.
$$

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_emf_v` | The 1 kHz source e.m.f., in volts. |
| `output_current_a` | The output current it produces, in amperes. |
| `noise_current_a` | The A-weighted output current with no input, in amperes. |

**Returns:** The equivalent input noise voltage, in volts.

## loop_centre_field

```python
loop_centre_field(
    current_a: float,
    length_m: float,
    *,
    width_m: float | None = None,
    turns: int = 1,
) -> float
```

The field at the centre of a loop, in its plane (IEC 60118-4:2014 E.1).

$$
H = \frac{2\sqrt{2}\,N I}{\pi d},
$$

with $d$ the side of a square loop, or $\sqrt{d_1 d_2}$ for a
rectangle, which E.1 allows "Provided that the sides d1, d2 of a
rectangular loop are not extremely different". For the square it is
exact; for a rectangle
it is the approximation E.1 prints, and [`rectangular_loop_field`](/phonometry/reference/api/electroacoustics/induction-loop-components/#rectangular_loop_field)
gives the exact value, which is larger by
$\sqrt{(d_1^2 + d_2^2)/(2 d_1 d_2)}$: 0,35 dB at an aspect ratio
of 1,5 and 3,3 dB at 4.

**Parameters**

| Name | Description |
| :--- | :--- |
| `current_a` | RMS current in each turn, in amperes. |
| `length_m` | Side of the square, or one side of the rectangle, in metres. |
| `width_m` | The other side of a rectangle, in metres; `None` for a square. |
| `turns` | Number of turns. |

**Returns:** The field strength at the centre, in A/m.

## loop_current

```python
loop_current(
    length_m: float,
    width_m: float,
    *,
    height_m: float = 1.4,
    field_strength_a_per_m: float = 0.4,
    turns: int = 1,
) -> float
```

The current a loop needs for a field strength above its centre.

The exact on-axis field of the rectangle (see the module docstring),
inverted for the current. The defaults are the conditions of IEC
62489-1:2010 5.4.10.2, 400 mA/m at 1,4 m above the centre of the loop
plane, which is also where IEC 60118-4:2014 Figure H.1 plots the current
required against the loop's size and aspect ratio, and the curves of that
figure are reproduced: 4,88 A for a 10 m square and 6,41 A for 10 m by
30 m, read as about 4,89 A and 6,41 A.

**Parameters**

| Name | Description |
| :--- | :--- |
| `length_m` | Length of the loop, in metres. |
| `width_m` | Width of the loop, in metres. |
| `height_m` | Height above the centre of the loop plane, in metres. |
| `field_strength_a_per_m` | The field strength to reach, in A/m. |
| `turns` | Number of turns. |

**Returns:** The RMS current in each turn, in amperes.

## loop_dimensions

```python
loop_dimensions(
    current_a: float,
    *,
    aspect_ratio: float = 1.0,
    height_m: float = 1.4,
    field_strength_a_per_m: float = 0.4,
    turns: int = 1,
) -> tuple[float, float]
```

The largest loop an amplifier's current drives to a field strength (5.4.11).

IEC 62489-1:2010 5.4.11.1 states "the linear dimensions of a square loop,
and a loop of aspect ratio 3:1, for which the magnetic field strength,
measured as specified in 5.4.10.1, is 400 mA/m". Above the centre, the
field of a given current first grows with the loop and then falls, so two
sizes reach any field below the peak. The characteristic is the larger
one: the biggest loop the amplifier can serve, which is the size a
specification is read for.

**Parameters**

| Name | Description |
| :--- | :--- |
| `current_a` | The amplifier's RMS output current into the loop, in amperes. |
| `aspect_ratio` | Long side over short side, at least 1 (1 for the square of 5.4.11.1, 3 for its second loop). |
| `height_m` | Height above the centre of the loop plane, in metres (1,4 m, 5.4.10.2). |
| `field_strength_a_per_m` | The field strength to reach, in A/m (400 mA/m). |
| `turns` | Number of turns. |

**Returns:** `(short_side_m, long_side_m)`, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the current cannot reach the field strength at that height with a loop of any size. |

## loop_impedance

```python
loop_impedance(
    resistance_ohm: float,
    inductance_h: float,
    *,
    frequencies_hz: ArrayLike | None = None,
) -> LoopImpedance
```

The impedance of a loop from its resistance and inductance.

**Parameters**

| Name | Description |
| :--- | :--- |
| `resistance_ohm` | Series resistance, in ohms ([`loop_resistance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loop_resistance), plus that of the feed cable). |
| `inductance_h` | Series inductance, in henries ([`rectangular_loop_inductance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#rectangular_loop_inductance), plus that of the feed cable). |
| `frequencies_hz` | Frequencies to tabulate the magnitude at, in hertz; by default the one-third-octave centres from 50 Hz to 10 kHz. |

**Returns:** A [`LoopImpedance`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loopimpedance).

## loop_resistance

```python
loop_resistance(
    perimeter_m: float,
    conductor_area_mm2: float,
    *,
    turns: int = 1,
    conductor_temperature_c: float = 20.0,
) -> float
```

The resistance of a copper loop (IEC 62489-1:2010 B.2).

$R = \rho N l / a$, with the resistivity of standard annealed copper,
1/58 ohm square millimetre per metre at 20 degrees Celsius, carried to the
conductor's temperature by the coefficient 0,00393 per degree (IEC
60028:1925, clause I). B.2 quotes "approximately 0,017 ohm/m" for 1 mm² at
25 degrees Celsius; Table B.1 is computed at 20 degrees, where its six
rounded resistances hold the resistivity between 1,716 and 1,738 times
$10^{-8}$ ohm metres, and 1/58 is inside that range.

**Parameters**

| Name | Description |
| :--- | :--- |
| `perimeter_m` | Length of one turn, in metres. |
| `conductor_area_mm2` | Cross-sectional area of the conductor, in square millimetres. |
| `turns` | Number of turns. |
| `conductor_temperature_c` | Temperature of the conductor, in degrees Celsius. |

**Returns:** The DC resistance of the loop, in ohms.

## LoopField

```python
LoopField(
    current_a: float,
    length_m: float,
    width_m: float,
    turns: int,
    x_m: np.ndarray,
    y_m: np.ndarray,
    z_m: np.ndarray,
    h_x_a_per_m: np.ndarray,
    h_y_a_per_m: np.ndarray,
    h_z_a_per_m: np.ndarray,
)
```

The magnetic field of a rectangular induction loop at a set of points.

The loop lies in the plane $z = 0$, centred on the origin, with its
sides of length `length_m` along $x$ and `width_m` along
$y$, and the current runs counterclockwise seen from $+z$, so
the field inside the loop points to $+z$. For a horizontal loop on
the floor $z$ is the height and `h_z_a_per_m` the vertical component a
standing listener's telecoil picks up; for a vertical loop on a counter the
same arrays describe it turned on its side.

**Attributes**

| Name | Description |
| :--- | :--- |
| `current_a` | The RMS current in each turn, in amperes. |
| `length_m` | Length of the loop along $x$, in metres. |
| `width_m` | Width along $y$, in metres. |
| `turns` | Number of turns. |
| `x_m` | The points' $x$ coordinates, in metres. |
| `y_m` | The points' $y$ coordinates, in metres. |
| `z_m` | The points' $z$ coordinates, in metres. |
| `h_x_a_per_m` | The $x$ component of the RMS field strength, in A/m. |
| `h_y_a_per_m` | The $y$ component, in A/m. |
| `h_z_a_per_m` | The $z$ component, in A/m. |

### LoopField.level_db()

```python
LoopField.level_db(component: str = 'z') -> np.ndarray
```

The field strength level of one component, dB re 400 mA/m.

**Parameters**

| Name | Description |
| :--- | :--- |
| `component` | `"x"`, `"y"`, `"z"` or `"magnitude"`. |

**Returns:** $20\lg(|H|/0{,}4\ \mathrm{A/m})$; minus infinity where the component vanishes, which is the null line outside a loop.

### LoopField.magnitude_a_per_m

*property*

The magnitude of the field strength vector, in A/m.

### LoopField.plot()

```python
LoopField.plot(
    ax: Axes | None = None,
    *,
    component: str = 'z',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the field strength level along the points, as Figures E.2 and E.3.

The abscissa is the coordinate that varies most among the points, and
the ordinate the level of one component in dB re 400 mA/m, with the
0 dB reference and the plus or minus 3 dB band of IEC 60118-4:2014
8.4.3 around it.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `component` | `"x"`, `"y"`, `"z"` or `"magnitude"`. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the level curve's `Axes.plot`. |

## LoopImpedance

```python
LoopImpedance(
    resistance_ohm: float,
    inductance_h: float,
    frequencies_hz: np.ndarray,
    impedance_ohm: np.ndarray,
)
```

The impedance of a loop, a resistance in series with an inductance.

IEC 62489-1:2010 5.4.3.2 states the rated load "as a series combination of
resistance and inductance", and B.2 represents the loop the same way. The
magnitude $|Z| = \sqrt{R^2 + (2\pi f L)^2}$ is
$\sqrt{2}$ times the resistance at the corner frequency
$f_\mathrm{c} = R/(2\pi L)$, "1,4 times" in IEC 60118-4:2014 E.3,
and the voltage an amplifier has to deliver for a current $I$ is
$U = I|Z|$, the $U_\mathrm{h}$ of E.3.

**Attributes**

| Name | Description |
| :--- | :--- |
| `resistance_ohm` | The series resistance, in ohms. |
| `inductance_h` | The series inductance, in henries. |
| `frequencies_hz` | The frequencies the magnitude is tabulated at, in hertz. |
| `impedance_ohm` | The magnitude of the impedance there, in ohms. |

### LoopImpedance.at()

```python
LoopImpedance.at(frequency_hz: ArrayLike) -> np.ndarray
```

The magnitude of the impedance at any frequency, in ohms.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency_hz` | Frequencies, in hertz, positive and finite. |

**Returns:** $|Z|$ there, in ohms.

### LoopImpedance.corner_frequency_hz

*property*

The frequency where the reactance equals the resistance, in hertz.

### LoopImpedance.drive_voltage()

```python
LoopImpedance.drive_voltage(
    current_a: float,
    frequency_hz: ArrayLike,
) -> np.ndarray
```

The RMS voltage that drives a current through the loop (IEC 60118-4 E.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `current_a` | RMS loop current, in amperes. |
| `frequency_hz` | Frequencies, in hertz, positive and finite. |

**Returns:** $U = I|Z|$, in volts.

### LoopImpedance.plot()

```python
LoopImpedance.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the magnitude of the impedance against frequency.

The resistance is drawn as a floor and the corner frequency marked,
where the magnitude has risen to $\sqrt{2}$ times the resistance.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the impedance curve's `Axes.plot`. |

## maximum_output_current

```python
maximum_output_current(
    resistor_voltage_v: ArrayLike,
    thd_percent: ArrayLike,
    *,
    load_resistance_ohm: float,
    rated_thd_percent: float,
) -> MaximumOutputCurrent
```

The maximum (distortion-limited) output current of an amplifier (5.4.7).

IEC 62489-1:2010 5.4.7.1 defines it as "The maximum current, produced by a
sinusoidal input signal at 1 kHz, deliverable for at least 10 s into the
rated load without exceeding the rated total harmonic distortion (THD)".
5.4.7.2 measures it from standard measuring conditions: the load current
is increased until the total harmonic distortion across the resistive
part of the load equals the rated value, and "The current is then
calculated from the total voltage across the resistive part of the load
and the resistance value". The 10 s the current has to be held for is a
condition on the measurement, not a computation.

The steps of the level are given as the total RMS voltage across the
resistance and the distortion read there, in ascending order of voltage;
the current where the distortion first reaches the rated value is
interpolated linearly between the two steps either side of it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `resistor_voltage_v` | The total RMS voltage across the resistive part of the load at each step, in volts, strictly ascending. |
| `thd_percent` | The total harmonic distortion measured across it at each step, in percent, none of it negative. |
| `load_resistance_ohm` | The resistance of the resistive part of the rated load, in ohms. |
| `rated_thd_percent` | The rated total harmonic distortion (5.4.6), in percent. |

**Returns:** A [`MaximumOutputCurrent`](/phonometry/reference/api/electroacoustics/induction-loop-components/#maximumoutputcurrent).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a negative distortion, which no measurement gives, or when the distortion never reaches the rated value, or already exceeds it at the first step, so the current lies outside the steps measured. |

## MaximumOutputCurrent

```python
MaximumOutputCurrent(
    resistor_voltage_v: np.ndarray,
    load_current_a: np.ndarray,
    thd_percent: np.ndarray,
    load_resistance_ohm: float,
    rated_thd_percent: float,
    maximum_current_a: float,
)
```

The maximum (distortion-limited) output current of an amplifier (5.4.7).

**Attributes**

| Name | Description |
| :--- | :--- |
| `resistor_voltage_v` | The total RMS voltage across the resistive part of the rated load at each step of the level, in volts. |
| `load_current_a` | The load current at each step, that voltage over the resistance, in amperes. |
| `thd_percent` | The total harmonic distortion across the resistive part at each step, in percent. |
| `load_resistance_ohm` | The resistance of the resistive part of the rated load, in ohms. |
| `rated_thd_percent` | The rated total harmonic distortion of 5.4.6, in percent. |
| `maximum_current_a` | The load current at which the distortion first reaches the rated value, interpolated linearly between the two steps either side, in amperes: the characteristic of 5.4.7, stated in amperes (5.4.7.3). |

### MaximumOutputCurrent.plot()

```python
MaximumOutputCurrent.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the distortion against the load current, with the rated THD.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the distortion curve's `Axes.plot`. |

## neck_loop_characteristics

```python
neck_loop_characteristics(
    frequencies_hz: ArrayLike,
    field_strength_level_db: ArrayLike,
    impedance_ohm: ArrayLike,
    *,
    input_voltage_v: float,
) -> NeckLoopCharacteristics
```

The input voltage, input impedance and frequency response of a neck loop.

The loop is arranged on the non-metallic jig of Annex E and the field
measured at the telecoil position with a small inductor, about 3 mm by
10 mm, the size of a behind-the-ear telecoil (9.1.2). The rated input
voltage is applied from a source of less than 0,4 ohm (9.3.2).

A passive loop is linear, so the input voltage for 400 mA/m at 1 kHz
(9.1) follows from the level measured at any voltage:
$U_{400} = U\,10^{-L/20}$, with $L$ the level at 1 kHz in dB
re 400 mA/m. For an active loop that is not linear, measure at the voltage
that gives 0 dB, where the scaling does nothing.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The measurement frequencies, in hertz, ascending and including 1000 Hz. |
| `field_strength_level_db` | The field strength level on the jig at each, in dB re 400 mA/m. |
| `impedance_ohm` | The input impedance at each, in ohms; complex values are reduced to their magnitude, and real ones must be positive. |
| `input_voltage_v` | The input voltage the field was measured with, in volts. |

**Returns:** A [`NeckLoopCharacteristics`](/phonometry/reference/api/electroacoustics/induction-loop-components/#neckloopcharacteristics).

## NECK_LOOP_TYPES

*Constant* (`mapping`).

```python
NECK_LOOP_TYPES = {1: NeckLoopType(description='for audio sources powered by two primary 1.5 V cells and higher voltage supplies', min_dc_resistance_ohm=30.4, max_dc_resistance_ohm=33.6, max_input_voltage_v=1.06), 2: NeckLoopType(description='neck loop with a transformer or an amplifier', min_dc_resistance_ohm=32.0, max_dc_resistance_ohm=inf, max_input_voltage_v=1.06)}
```

## NeckLoopCharacteristics

```python
NeckLoopCharacteristics(
    frequencies_hz: np.ndarray,
    field_strength_level_db: np.ndarray,
    impedance_ohm: np.ndarray,
    input_voltage_v: float,
    reference_input_voltage_v: float,
    minimum_impedance_ohm: float,
    response_db: np.ndarray,
    frequencies_3db_hz: tuple[float, ...],
)
```

What IEC 62489-1:2010+A1:2014 clause 9 states for a neck loop.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The measurement frequencies, in hertz. |
| `field_strength_level_db` | The field strength level on the test jig at each, in dB re 400 mA/m, with `input_voltage_v` applied. |
| `impedance_ohm` | The magnitude of the input impedance at each, in ohms. |
| `input_voltage_v` | The input voltage the field was measured with, in volts. |
| `reference_input_voltage_v` | The input voltage that produces 400 mA/m at 1 kHz at the telecoil position of the jig, the characteristic of 9.1, in volts. |
| `minimum_impedance_ohm` | The smallest magnitude of the input impedance over 100 Hz to 5 kHz, rounded to the nearest ohm (9.2.1). |
| `response_db` | The field strength level relative to the one at 1 kHz, in dB. |
| `frequencies_3db_hz` | The frequencies where the response differs from the one at 1 kHz by 3 dB, which 9.3.3 states when the response is given as text. |

### NeckLoopCharacteristics.plot()

```python
NeckLoopCharacteristics.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the frequency response on the jig, 0 dB at 1 kHz.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the response curve's `Axes.plot`. |

## NeckLoopType

```python
NeckLoopType(
    description: str,
    min_dc_resistance_ohm: float,
    max_dc_resistance_ohm: float,
    max_input_voltage_v: float,
)
```

One neck-loop type of the draft Annex D (prEN 62489-1:2010/prA2:2017).

**Attributes**

| Name | Description |
| :--- | :--- |
| `description` | What the type is, as the draft describes it. |
| `min_dc_resistance_ohm` | The smallest DC input resistance, in ohms. |
| `max_dc_resistance_ohm` | The largest, in ohms; infinite when the draft sets only a floor. |
| `max_input_voltage_v` | The input voltage within which the loop reaches 400 mA/m on the jig of Annex E, in volts. |

## NeckLoopVerification

```python
NeckLoopVerification(
    neck_loop_type: int,
    dc_resistance_ohm: float,
    input_voltage_v: float,
)
```

A neck loop judged against one type of the draft Annex D (prA2:2017).

**Attributes**

| Name | Description |
| :--- | :--- |
| `neck_loop_type` | The type it was judged as, 1 or 2. |
| `dc_resistance_ohm` | The measured DC input resistance, in ohms. |
| `input_voltage_v` | The input voltage that produces 400 mA/m on the jig, in volts. |

The limits of the type (`limits`) are read from
[`NECK_LOOP_TYPES`](/phonometry/reference/api/electroacoustics/induction-loop-components/#neck_loop_types), so a verification cannot be built against other
limits.

### NeckLoopVerification.limits

*property*

The [`NeckLoopType`](/phonometry/reference/api/electroacoustics/induction-loop-components/#necklooptype) judged against.

### NeckLoopVerification.passes

*property*

Whether the loop meets both limits of its type.

### NeckLoopVerification.plot()

```python
NeckLoopVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each measured value as a share of its limit.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars' `Axes.bar`. |

### NeckLoopVerification.resistance_passes

*property*

Whether the DC resistance is inside the type's range.

### NeckLoopVerification.voltage_passes

*property*

Whether 400 mA/m is reached within the type's input voltage.

## quadrature_phase_error

```python
quadrature_phase_error(
    frequencies_hz: ArrayLike,
    phase_difference_deg: ArrayLike,
) -> QuadraturePhaseError
```

The maximum deviation from 90 degrees between two loop currents (5.4.14).

The phase angle between the currents of the two loops, measured across a
low-value series resistor in each (5.4.14.3), is judged over 100 Hz to
5 kHz (5.4.14.2). Either loop may lead: an angle is folded into 0 to 180
degrees before its distance from 90 degrees is taken, so -90 and 270
degrees are as much in quadrature as 90.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The measurement frequencies, in hertz, ascending, at least one of them inside 100 Hz to 5 kHz. |
| `phase_difference_deg` | The phase angle between the loop currents at each, in degrees. |

**Returns:** A [`QuadraturePhaseError`](/phonometry/reference/api/electroacoustics/induction-loop-components/#quadraturephaseerror).

## QuadraturePhaseError

```python
QuadraturePhaseError(
    frequencies_hz: np.ndarray,
    phase_difference_deg: np.ndarray,
    deviation_deg: np.ndarray,
    max_deviation_deg: float,
    max_deviation_frequency_hz: float,
)
```

The phase error of a quadrature network for a phased loop array (5.4.14).

Two adjacent loops fed with currents about 90 degrees apart make a field
whose direction rotates, instead of one that cancels at the nulls. A
deviation $\delta$ from 90 degrees leaves an in-phase component
$\cos(90^\circ - \delta) = \sin\delta$ of one field against the
other, which raises the level where the two add and lowers it where they
subtract, by $20\lg(1 \pm \sin\delta)$ dB (5.4.14.1: at 85 degrees
the in-phase part is $\cos 85^\circ = 0{,}087$).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The measurement frequencies, in hertz. |
| `phase_difference_deg` | The phase angle between the loop currents at each, in degrees. |
| `deviation_deg` | Its absolute deviation from 90 degrees, in degrees. |
| `max_deviation_deg` | The largest deviation over 100 Hz to 5 kHz, the characteristic of 5.4.14.2, in degrees. |
| `max_deviation_frequency_hz` | Where it occurs, in hertz, stated with it (5.4.14.4). |

### QuadraturePhaseError.level_decrease_db

*property*

Where they subtract, the level falls by this, in dB (a negative number).

$20\lg(1 - \sin\delta)$, computed as
$20\lg\left(2\sin^2(45^\circ - \delta/2)\right)$, which is the
same number without the cancellation near 90 degrees. At a deviation
of 90 degrees, currents in phase or in antiphase, the two fields
cancel where they subtract and the fall is minus infinity.

### QuadraturePhaseError.level_increase_db

*property*

Where the in-phase parts add, the level rises by this, in dB.

### QuadraturePhaseError.plot()

```python
QuadraturePhaseError.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the deviation from 90 degrees against frequency.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the deviation curve's `Axes.plot`. |

## rectangular_loop_field

```python
rectangular_loop_field(
    current_a: float,
    length_m: float,
    width_m: float,
    x_m: ArrayLike,
    y_m: ArrayLike,
    z_m: ArrayLike,
    *,
    turns: int = 1,
) -> LoopField
```

The magnetic field of a rectangular loop, by Biot and Savart.

Each of the four sides is a straight filament whose field closes exactly
(see the module docstring), so the result carries no discretisation. It
reproduces the curves of Figure E.2 b) of IEC 60118-4:2014 across the
width of that figure's loop, it is the kind of pattern Figures E.3 to E.5
draw, and at the centre of a square it is the
$2\sqrt{2}I/(\pi d)$ of E.1. The conductor is a filament, so the
field is that of a thin wire everywhere except within a few wire radii of
it. Metal in the building, which Annex F describes, is not modelled.

**Parameters**

| Name | Description |
| :--- | :--- |
| `current_a` | RMS current in each turn, in amperes. |
| `length_m` | Length of the loop along $x$, in metres. |
| `width_m` | Width along $y$, in metres. |
| `x_m` | $x$ coordinates of the points, in metres, with the loop centred on the origin. |
| `y_m` | $y$ coordinates, broadcast against `x_m`. |
| `z_m` | $z$ coordinates (height above the loop plane), broadcast against both. |
| `turns` | Number of turns, all carrying the same current. |

**Returns:** A [`LoopField`](/phonometry/reference/api/electroacoustics/induction-loop-components/#loopfield).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive dimension, a non-finite coordinate or a point on the conductor, where a filament's field is infinite. |

## rectangular_loop_inductance

```python
rectangular_loop_inductance(
    length_m: float,
    width_m: float,
    conductor_area_mm2: float,
    *,
    turns: int = 1,
    internal_inductance: bool = True,
) -> float
```

The inductance of a rectangular loop of round wire (Grover, Formula (58)).

$$
L = \frac{\mu_0}{\pi}\left[a\ln\frac{2a}{\rho} + b\ln\frac{2b}{\rho} + 2\sqrt{a^2 + b^2} - a\sinh^{-1}\frac{a}{b} - b\sinh^{-1}\frac{b}{a} - 2(a + b) + \frac{\mu}{4}(a + b)\right]
$$

for sides $a$ and $b$ and a wire of radius $\rho$
(Grover, *Inductance Calculations*, 1946, p. 60; the factor 0,004
microhenry per centimetre there is $\mu_0/\pi$). The last term is the
flux inside the wire, $\mu = 1$ for copper. For $N$ turns the
single-turn value is multiplied by $N^2$, the perfect coupling IEC
62489-1:2010 Table B.1 assumes.

Table B.1 is reproduced without the internal term
(`internal_inductance=False`): the counter loop, the home loop, the small
room and the typical place of worship come out at 189, 22, 47 and 109
microhenries, as printed. With the term they are about 3 % higher, from
2,7 % for the place of worship to 4,2 % for the counter loop. At audio
frequencies the current fills the wire (the skin depth in copper is 2 mm
at 1 kHz), which is why the term is included by default.

**Parameters**

| Name | Description |
| :--- | :--- |
| `length_m` | One side of the rectangle, in metres. |
| `width_m` | The other side, in metres. |
| `conductor_area_mm2` | Cross-sectional area of the round conductor, in square millimetres; the radius is $\sqrt{a/\pi}$. |
| `turns` | Number of turns. |
| `internal_inductance` | Include the flux inside the wire (the $\mu/4$ term). |

**Returns:** The inductance, in henries.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | when the wire is not thin against the sides, where the formula does not hold. |

## verify_neck_loop

```python
verify_neck_loop(
    dc_resistance_ohm: float,
    input_voltage_v: float,
    *,
    neck_loop_type: int = 1,
) -> NeckLoopVerification
```

Does a neck loop meet one type of the draft Annex D (prA2:2017)?

The draft Amendment 2 to IEC 62489-1 (prEN 62489-1:2010/prA2:2017, read in
E DIN EN 62489-1/A2:2017-10) specifies a type 1 neck loop, for audio
sources powered by two primary 1,5 V cells and higher voltage supplies, by
a DC resistance of 32 ohm plus or minus 5 % and a type 2 neck loop with a
transformer or an amplifier by an input DC resistance of at least 32 ohm,
both reaching 400 mA/m on the jig of Annex E with at most 1,06 V at the
input ([`NECK_LOOP_TYPES`](/phonometry/reference/api/electroacoustics/induction-loop-components/#neck_loop_types)). It is a draft, cited as one.

**Parameters**

| Name | Description |
| :--- | :--- |
| `dc_resistance_ohm` | The measured DC input resistance, in ohms. |
| `input_voltage_v` | The input voltage that produces 400 mA/m on the jig, in volts ([`NeckLoopCharacteristics.reference_input_voltage_v`](/phonometry/reference/api/electroacoustics/induction-loop-components/#neckloopcharacteristics)). |
| `neck_loop_type` | 1 or 2. |

**Returns:** A [`NeckLoopVerification`](/phonometry/reference/api/electroacoustics/induction-loop-components/#neckloopverification).

---
title: "emission.sound_power_high_frequency"
description: "Sound power levels in the 16 kHz octave band: ISO 9295:2015."
sidebar:
  label: "sound_power_high_frequency"
---

Sound power levels in the 16 kHz octave band: ISO 9295:2015.

Some machines emit most of what matters above the range the general methods
cover: the paper noise of a fast printer, the whine of a switched-mode power
supply, the tone of a display. ISO 3741 stops at the 10 kHz one-third octave
band and ISO 3744 at the same place, so ISO 9295 adds the octave band centred
on 16 kHz, from 11,2 kHz to 22,4 kHz (clause 1), and determines the unweighted
sound power level in its three one-third octave bands (12,5, 16 and 20 kHz)
or in the narrow bands that hold its discrete tones.

Four methods are specified. Three of them use a reverberation test room with
a microphone on a rotating boom pointed away from the source (clauses 5.4 and
5.5), and one uses a hemi-anechoic room (clause 9).

**Mean level.** The time-averaged band level over the four orientations of
the equipment ($N = 4$), or over three revolutions of the boom
($N = 3$), is the energy mean of Formula (1):

$$
\overline{L_p} = 10 \lg\!\left[ \frac{1}{N} \sum_{i=1}^{N} 10^{0{,}1 L_i} \right] \mathrm{dB} \tag{1}
$$

A moving microphone spreads a discrete tone over sidebands. The analyser has
to be at least as wide as Formula (2), with $v$ the speed of the
microphone and $c$ the speed of sound; with a narrower FFT the
sidebands are summed on an energy basis, Formula (3):

$$
\Delta f = 2 f \frac{v}{c} \tag{2}
$$

$$
L_\mathrm{tot} = 10 \lg \sum_{i=1}^{N_\mathrm{sb}} 10^{0{,}1 L_i}\ \mathrm{dB} \tag{3}
$$

**Method with the measured reverberation time** (clause 6). Above 10 kHz the
room absorption coefficient cannot be taken as small, so the Eyring relation
gives it from the measured reverberation time $T$, and the room constant
$R$ follows from it ($S$ the total room surface, $V$ its
volume):

$$
R = \frac{S \, \alpha_\mathrm{room}}{1 - \alpha_\mathrm{room}} \tag{4}
$$

$$
\alpha_\mathrm{room} = 1 - \mathrm{e}^{-0{,}16 \, V / (S T)} \tag{5}
$$

The sound power level in each band is then Formula (6):

$$
L_W = \overline{L_{p(\mathrm{ST})}} - 10 \lg\frac{4}{R}\ \mathrm{dB} \tag{6}
$$

**Method with the calculated air absorption** (clause 7). At 10 kHz and
above practically all of the absorption of a reverberation room is in the
air, so the room constant comes from the air absorption coefficient
$\alpha$ in nepers per metre, Formula (7), and Formula (6) is applied
unchanged:

$$
R = \frac{8 \alpha V}{1 - \dfrac{8 \alpha V}{S}} \tag{7}
$$

$\alpha$ is Annex A (normative), which is ISO 9613-1 written in nepers
rather than decibels and evaluated up to 22,4 kHz, where ISO 9613-1 stops at
10 kHz; [`air_absorption_np_per_m`](/phonometry/reference/api/power/sound-power-high-frequency/#air_absorption_np_per_m) evaluates it with the library's
ISO 9613-1 implementation. Tables 1 and 2 print it for 18 °C to 27 °C, 40 %
to 60 % relative humidity and 10 000 Hz to 22 400 Hz.

**Method with a reference sound source** (clause 8). The source under test
and a calibrated reference source are measured in turn with the same
bandwidth. For broadband noise the band level is Formula (8); for discrete
tones the reference source is calibrated as a power spectral density, per
unit bandwidth, and the noise bandwidth $\Delta F$ of the constant
bandwidth analyser puts it back into the band, Formula (9):

$$
L_W = L_{W(\mathrm{FAR})} - \overline{L_{p(\mathrm{FAR})}} + \overline{L_{p(\mathrm{ST})}} \tag{8}
$$

$$
L_W = L_{W(\mathrm{FAR})} - \overline{L_{p(\mathrm{FAR})}} + \overline{L_{p(\mathrm{ST})}} + 10 \lg(\Delta F / 1\ \mathrm{Hz})\ \mathrm{dB} \tag{9}
$$

**Method with a free field over a reflecting plane** (clause 9) is ISO 3744
([`sound_power_pressure`](/phonometry/reference/api/power/sound-power/#sound_power_pressure)) with the three
one-third octave bands of the 16 kHz octave; beyond a measurement radius of
2 m the surface level takes the absorption correction of Formula (10), with
$\alpha$ in decibels per metre:

$$
K = r \cdot \alpha \tag{10}
$$

**Reference meteorological conditions.** Clause 10.1 carries the levels of
the reverberation-room methods to 101,325 kPa and 23,0 °C "de acuerdo con la
Norma ISO 3741", which is the reference-quantity correction $C_1$ and
the radiation-impedance correction $C_2$ of ISO 3741:2010 clause 9.1.4
for a direct method and $C_2$ alone for the comparison with a reference
source, exactly as ISO 3741 Formulae (20) and (21) apply them.

Formulae (4) to (10) carry no worked example in the standard and are pinned
in closed form; Tables 1 and 2 are the numeric oracle of Annex A.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## air_absorption_np_per_m

```python
air_absorption_np_per_m(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float = 101.325,
) -> NDArray[np.float64]
```

Air absorption coefficient $\alpha$ in nepers per metre (ISO 9295 Annex A).

Formulae (A.1) to (A.5) of ISO 9295:2015 are the ISO 9613-1:1993
pure-tone attenuation written for the amplitude in nepers per metre, the
unit Formula (7) takes, so this is the library's ISO 9613-1 evaluation
without its factor 8,686 (Annex A: "multiplicando el valor de
$\alpha$ en Np/m por 8,686 para obtener el valor de $\alpha$
en dB/m"). The difference from
[`air_attenuation`](/phonometry/reference/api/environment/air-absorption/#air_attenuation)
is the range: Annex A evaluates the same formula up to 22,4 kHz, the top
of the 16 kHz octave band, so no advisory is raised between 10 kHz and
22,4 kHz, where ISO 9613-1 stops tabulating.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Frequency or frequencies `f`, in hertz. |
| `temperature_c` | Air temperature, in degrees Celsius. Outside -20 °C to +50 °C emits an [`AtmosphericAbsorptionWarning`](/phonometry/reference/api/environment/air-absorption/#atmosphericabsorptionwarning). |
| `relative_humidity_percent` | Relative humidity `h_r`, in percent. |
| `static_pressure_kpa` | Static pressure `p_s`, in kilopascals (default 101,325 kPa, the pressure Tables 1 and 2 are printed at). |

**Returns:** $\alpha$ in Np/m, with the shape of `frequencies_hz`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive frequency, a temperature at or below absolute zero, a relative humidity outside [0, 100] % or a non-positive static pressure. |

## free_field_absorption_correction

```python
free_field_absorption_correction(
    frequencies_hz: ArrayLike,
    *,
    radius_m: float,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float = 101.325,
) -> NDArray[np.float64]
```

Air absorption correction of the free-field method (ISO 9295 Formula (10)).

$K = r \cdot \alpha$, with $\alpha$ the air absorption in
decibels per metre (Annex A times 8,686). Clause 9.8 adds it to the
surface sound pressure level of ISO 3744 before the sound power is
determined, and only when the measurement radius exceeds 2 m; at 2 m
or less the clause asks for no correction and this returns zero. The
surface level and the sound power level differ by the constant
$10 \lg(S/S_0)$, so adding `K` to the band levels
[`sound_power_pressure`](/phonometry/reference/api/power/sound-power/#sound_power_pressure) returns
is the same thing.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Band centre or tone frequencies, in hertz. |
| `radius_m` | Radius `r` of the measurement hemisphere, in metres. |
| `temperature_c` | Air temperature, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity, in percent. |
| `static_pressure_kpa` | Static pressure, in kilopascals (default 101,325 kPa). |

**Returns:** `K` per frequency, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive radius or the atmospheric inputs [`air_absorption_np_per_m`](/phonometry/reference/api/power/sound-power-high-frequency/#air_absorption_np_per_m) refuses. |

## high_frequency_sound_power

```python
high_frequency_sound_power(
    pressure_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    room_constant_m2: ArrayLike,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    tonal: bool = False,
) -> HighFrequencySoundPowerResult
```

Sound power level in the 16 kHz octave band, direct method (ISO 9295 Formula (6)).

$L_W = \overline{L_{p(\mathrm{ST})}} - 10 \lg(4/R) + C_1 + C_2$
per band: Formula (6), carried to the reference meteorological conditions
by the $C_1$ and $C_2$ of ISO 3741:2010 clause 9.1.4, which
clause 10.1 points to. The same formula serves both direct methods; only
the room constant differs, from the measured reverberation time
([`room_constant_from_reverberation_time`](/phonometry/reference/api/power/sound-power-high-frequency/#room_constant_from_reverberation_time), clause 6) or from the
calculated air absorption ([`room_constant_from_air_absorption`](/phonometry/reference/api/power/sound-power-high-frequency/#room_constant_from_air_absorption),
clause 7).

**Parameters**

| Name | Description |
| :--- | :--- |
| `pressure_levels_db` | $\overline{L_{p(\mathrm{ST})}}$ per band, in dB re 20 µPa, or an `(N, bands)` array of the time-averaged levels of the four orientations ($N = 4$) or three boom revolutions ($N = 3$), energy-averaged by Formula (1). |
| `frequencies_hz` | Band centre or tone frequencies, in hertz, one per band. A frequency outside 11,2 kHz to 22,4 kHz emits a [`SoundPowerWarning`](/phonometry/reference/api/power/sound-power/#soundpowerwarning). |
| `room_constant_m2` | Room constant `R`, in square metres, a scalar or one value per band. |
| `temperature_c` | Air temperature in the room, in degrees Celsius (default 23,0 °C, the reference temperature). |
| `static_pressure_kpa` | Static pressure in the room, in kilopascals (default 101,325 kPa, the reference pressure). |
| `tonal` | `True` when the bands are the narrow bands of discrete tones (clause 6.5), which changes how the result is drawn and read. |

**Returns:** A [`HighFrequencySoundPowerResult`](/phonometry/reference/api/power/sound-power-high-frequency/#highfrequencysoundpowerresult) with `method='direct'`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for non-finite levels, a room constant that is not positive, frequencies that do not match the bands, or a temperature or static pressure ISO 3741 cannot correct from. |

## high_frequency_sound_power_comparison

```python
high_frequency_sound_power_comparison(
    pressure_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    reference_pressure_levels_db: ArrayLike,
    reference_sound_power_levels_db: ArrayLike,
    noise_bandwidth_hz: float | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
) -> HighFrequencySoundPowerResult
```

Sound power level in the 16 kHz octave band against a reference source (ISO 9295 clause 8).

For broadband noise, Formula (8):
$L_W = L_{W(\mathrm{FAR})} - \overline{L_{p(\mathrm{FAR})}} + \overline{L_{p(\mathrm{ST})}}$, per one-third octave band. For
discrete tones, Formula (9) adds $10 \lg(\Delta F / 1\ \mathrm{Hz})$,
because the reference source is then calibrated per unit bandwidth
(clause 8.1) and $\Delta F$ is the noise bandwidth of the constant
bandwidth analyser. Clause 10.1 adds the radiation-impedance correction
$C_2$ of ISO 3741, as ISO 3741 Formula (21) does for its own
comparison method.

**Parameters**

| Name | Description |
| :--- | :--- |
| `pressure_levels_db` | $\overline{L_{p(\mathrm{ST})}}$ per band, in dB re 20 µPa, or an `(N, bands)` array averaged by Formula (1). |
| `frequencies_hz` | Band centre or tone frequencies, in hertz, one per band. |
| `reference_pressure_levels_db` | $\overline{L_{p(\mathrm{FAR})}}$ per band, in dB re 20 µPa, measured with the same bandwidth at the same location (clauses 8.3, 8.4); a 2-D input is averaged by Formula (1) as well. |
| `reference_sound_power_levels_db` | $L_{W(\mathrm{FAR})}$ of the calibrated reference source, in dB re 1 pW, a scalar or one value per band: per band for broadband noise, per hertz for tones. |
| `noise_bandwidth_hz` | $\Delta F$, the noise bandwidth of the analyser, in hertz, which selects Formula (9); `None` (default) selects Formula (8). Clause 8.5.2 allows 1 Hz for a constant percentage analyser, and holds an FFT to 112 Hz or less: a wider one emits a [`SoundPowerWarning`](/phonometry/reference/api/power/sound-power/#soundpowerwarning). |
| `temperature_c` | Air temperature in the room, in degrees Celsius (default 23,0 °C). |
| `static_pressure_kpa` | Static pressure in the room, in kilopascals (default 101,325 kPa). |

**Returns:** A [`HighFrequencySoundPowerResult`](/phonometry/reference/api/power/sound-power-high-frequency/#highfrequencysoundpowerresult) with `method='comparison'`, `tonal` set when `noise_bandwidth_hz` is given.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for non-finite levels, reference levels that do not span the same bands, a non-positive bandwidth, or a temperature or static pressure ISO 3741 cannot correct from. |

## HighFrequencySoundPowerResult

```python
HighFrequencySoundPowerResult(
    frequencies: NDArray[np.float64],
    sound_power_level: NDArray[np.float64],
    mean_pressure_level: NDArray[np.float64],
    room_constant: NDArray[np.float64] | None,
    reference_sound_power_level: NDArray[np.float64] | None,
    reference_pressure_level: NDArray[np.float64] | None,
    noise_bandwidth_hz: float | None,
    c1: float,
    c2: float,
    method: str,
    tonal: bool,
)
```

A sound power determination in the 16 kHz octave band (ISO 9295:2015).

One value per band: a one-third octave band of the 16 kHz octave for
broadband noise, or the narrow band of a discrete tone.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Band centre or tone frequencies, in hertz. |
| `sound_power_level` | $L_W$ per band, in dB re 1 pW, at the reference meteorological conditions of clause 10.1 (Formula (6) plus `c1` and `c2` for the direct method, Formula (8) or (9) plus `c2` for the comparison). |
| `mean_pressure_level` | $\overline{L_{p(\mathrm{ST})}}$ per band, in dB re 20 µPa, the energy mean of Formula (1) over the orientations or revolutions supplied. |
| `room_constant` | The room constant `R` per band, in square metres, for the direct method (Formula (4) or (7)); `None` for the comparison. |
| `reference_sound_power_level` | $L_{W(\mathrm{FAR})}$ per band, in dB re 1 pW (per hertz for the tonal comparison); `None` for the direct method. |
| `reference_pressure_level` | $\overline{L_{p(\mathrm{FAR})}}$ per band, in dB re 20 µPa; `None` for the direct method. |
| `noise_bandwidth_hz` | $\Delta F$ of Formula (9), in hertz, for the tonal comparison; `None` otherwise. |
| `c1` | Reference-quantity correction `C1` of ISO 3741, in dB, for the direct method; `NaN` for the comparison, which does not apply it. |
| `c2` | Radiation-impedance correction `C2` of ISO 3741, in dB. |
| `method` | `'direct'` (clauses 6 and 7) or `'comparison'` (clause 8). |
| `tonal` | `True` when the bands are the narrow bands of discrete tones rather than one-third octave bands of broadband noise. |

### HighFrequencySoundPowerResult.plot()

```python
HighFrequencySoundPowerResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the band levels, with the mean room level they came from.

Broadband bands are drawn as bars over the one-third octave bands; a
tonal determination is drawn as one stem per tone on a frequency axis,
with the line 10 dB below the highest tone that clause 13 c) reports
down to. Requires matplotlib (`pip install phonometry[plot]`);
returns the `Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bar or stem drawing of $L_W$. |

**Returns:** The axes.

### HighFrequencySoundPowerResult.within_10_db_of_maximum

*property*

Bands whose level is within 10 dB of the highest one.

Clause 13 c) and Table 3 ask for the level and the frequency of every
tone that lies within 10 dB of the highest tonal level in the band, so
for a tonal determination this marks the tones the report has to
carry.

## minimum_analyzer_bandwidth_hz

```python
minimum_analyzer_bandwidth_hz(
    tone_frequency_hz: ArrayLike,
    *,
    microphone_speed_m_s: float,
    speed_of_sound: float,
) -> NDArray[np.float64]
```

Narrowest analyser bandwidth that holds a tone seen by a moving microphone.

$\Delta f = 2 f v / c$, ISO 9295:2015 Formula (2). The moving
microphone spreads the energy of a discrete tone over sidebands either
side of its frequency, and an analyser at least this wide collects the
whole tone in one band; a narrower one (an FFT) needs its sidebands
summed with [`tone_level_from_sidebands`](/phonometry/reference/api/power/sound-power-high-frequency/#tone_level_from_sidebands).

**Parameters**

| Name | Description |
| :--- | :--- |
| `tone_frequency_hz` | Centre frequency `f` of the tone, in hertz. |
| `microphone_speed_m_s` | Speed `v` of the microphone along its path, in metres per second. |
| `speed_of_sound` | Speed of sound `c`, in metres per second. |

**Returns:** The minimum bandwidth $\Delta f$, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive or non-finite input. |

## room_absorption_coefficient

```python
room_absorption_coefficient(
    reverberation_time_s: ArrayLike,
    *,
    volume_m3: float,
    surface_area_m2: float,
) -> NDArray[np.float64]
```

Room absorption coefficient from the reverberation time (ISO 9295 Formula (5)).

$\alpha_\mathrm{room} = 1 - \mathrm{e}^{-0{,}16 \, V / (S T)}$, the
Eyring relation solved for the absorption coefficient. Clause 6.1 asks
for it rather than the simpler Sabine one because above 10 kHz the room
absorption coefficient cannot be taken as small compared with unity. The
constant is the 0,16 the formula prints.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reverberation_time_s` | Mean measured reverberation time `T` per band, in seconds (scalar or one value per band); clause 6.2 averages three or four points of the microphone path. |
| `volume_m3` | Room volume `V`, in cubic metres. |
| `surface_area_m2` | Total room surface `S`, in square metres. |

**Returns:** $\alpha_\mathrm{room}$ per band, in (0, 1).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive or non-finite time, volume or surface. |

## room_constant_from_air_absorption

```python
room_constant_from_air_absorption(
    frequencies_hz: ArrayLike,
    *,
    volume_m3: float,
    surface_area_m2: float,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float = 101.325,
) -> NDArray[np.float64]
```

Room constant from the calculated air absorption (ISO 9295 Formula (7)).

$R = 8 \alpha V / (1 - 8 \alpha V / S)$, the room constant of the
method of clause 7, with $\alpha$ in nepers per metre from
[`air_absorption_np_per_m`](/phonometry/reference/api/power/sound-power-high-frequency/#air_absorption_np_per_m) (Annex A). The method takes all of the
room absorption to be in the air, which clause 7.2 holds at 10 kHz and
above; a band below 10 kHz emits a
[`SoundPowerWarning`](/phonometry/reference/api/power/sound-power/#soundpowerwarning), since the walls are no
longer negligible there and the measured reverberation time of
[`room_constant_from_reverberation_time`](/phonometry/reference/api/power/sound-power-high-frequency/#room_constant_from_reverberation_time) is the method to use.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Band centre or tone frequencies, in hertz. |
| `volume_m3` | Room volume `V`, in cubic metres. |
| `surface_area_m2` | Total room surface `S`, in square metres. |
| `temperature_c` | Air temperature in the room, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity in the room, in percent. |
| `static_pressure_kpa` | Static pressure in the room, in kilopascals (default 101,325 kPa). |

**Returns:** `R` per frequency, in square metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive or non-finite volume or surface, for the atmospheric inputs [`air_absorption_np_per_m`](/phonometry/reference/api/power/sound-power-high-frequency/#air_absorption_np_per_m) refuses, or where $8 \alpha V / S \ge 1$: the air alone would then absorb more than the room surface can, and Formula (7) has no finite room constant. |

## room_constant_from_reverberation_time

```python
room_constant_from_reverberation_time(
    reverberation_time_s: ArrayLike,
    *,
    volume_m3: float,
    surface_area_m2: float,
) -> NDArray[np.float64]
```

Room constant from the measured reverberation time (ISO 9295 Formulae (4), (5)).

$R = S \alpha_\mathrm{room} / (1 - \alpha_\mathrm{room})$ with
$\alpha_\mathrm{room}$ from [`room_absorption_coefficient`](/phonometry/reference/api/power/sound-power-high-frequency/#room_absorption_coefficient),
the room constant of the method of clause 6. It goes into
[`high_frequency_sound_power`](/phonometry/reference/api/power/sound-power-high-frequency/#high_frequency_sound_power) as `room_constant_m2`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reverberation_time_s` | Mean measured reverberation time `T` per band, in seconds (scalar or one value per band). |
| `volume_m3` | Room volume `V`, in cubic metres. |
| `surface_area_m2` | Total room surface `S`, in square metres. |

**Returns:** `R` per band, in square metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-positive or non-finite time, volume or surface. |

## tone_level_from_sidebands

```python
tone_level_from_sidebands(sideband_levels_db: ArrayLike) -> float
```

Total level of a tone from its sideband levels (ISO 9295 Formula (3)).

$L_\mathrm{tot} = 10 \lg \sum_{i=1}^{N_\mathrm{sb}} 10^{0{,}1 L_i}$,
the energy sum of the bands adjacent to the tone frequency that carry
its energy when the analyser is narrower than
[`minimum_analyzer_bandwidth_hz`](/phonometry/reference/api/power/sound-power-high-frequency/#minimum_analyzer_bandwidth_hz).

**Parameters**

| Name | Description |
| :--- | :--- |
| `sideband_levels_db` | The $N_\mathrm{sb}$ sideband levels $L_i$, in decibels re 20 µPa. |

**Returns:** $L_\mathrm{tot}$, in decibels re 20 µPa.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an empty or non-finite input. |

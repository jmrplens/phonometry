---
title: "emission.sound_power_reverberation"
description: "Public API of phonometry.emission.sound_power_reverberation (auto-generated)."
sidebar:
  label: "sound_power_reverberation"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Sound power level of a noise source measured in a reverberation test room:
ISO 3741:2010 (precision method, accuracy grade 1).

The source is placed in a hard-walled reverberation room whose reverberant
field is sampled by microphones. Two methods are provided.

The **direct method** derives the sound power from the mean corrected room
sound pressure level `Lp(ST)` and the equivalent absorption area `A` of the
room (ISO 3741:2010 clause 9.1.4, Eq. 20):

```text
Lp(ST) = 10*lg( (1/NM) * sum_i 10^(0,1*Lpi) )                     (Eq. 16)
A      = (55,26/c) * (V/T60)          (Sabine)                    (clause 9.1.4)
c      = 20,05 * sqrt(273 + theta)    speed of sound, m/s
LW = Lp(ST) + 10*lg(A/A0) + 4,34*(A/S) + 10*lg(1 + S*c/(8*V*f))
            + C1 + C2 - 6                                         (Eq. 20)
```

`10*lg(1 + S*c/(8*V*f))` is the Waterhouse boundary correction (energy stored
near the room boundaries); it vanishes as the frequency grows. `C1` (Eq. 20,
reference-quantity correction) and `C2` (radiation-impedance correction) carry
the result to the reference meteorological conditions of clause 4 (23,0 C,
101,325 kPa, 50 %):

```text
C1 = -10*lg(ps/ps0) + 5*lg((273,15+theta)/314)                   (clause 9.1.4)
C2 = -10*lg(ps/ps0) + 15*lg((273,15+theta)/296)
```

The **comparison method** replaces the absorption-area terms by a reference
sound source (RSS) of known sound power `LW(RSS)` measured at the same
positions (ISO 3741:2010 clause 9.1.5, Eq. 21):

```text
LW = LW(RSS) + ( Lp(ST) - Lp(RSS) + C2 )                         (Eq. 21)
```

Both methods cover the one-third-octave bands from 100 Hz to 10 kHz (clause
8.1). Octave-band, A-weighted and total levels follow ISO 3741 Annex F, which
reuses the ISO 3744 Annex E A-weighting band corrections.

## ReverberationSoundPowerResult

```python
ReverberationSoundPowerResult(
    frequencies: np.ndarray | None,
    sound_power_level: np.ndarray,
    mean_pressure_level: np.ndarray,
    absorption_area: np.ndarray,
    waterhouse_correction: np.ndarray,
    background_correction: np.ndarray,
    c1: float,
    c2: float,
    speed_of_sound: float,
    sound_power_level_a: float,
    method: str,
)
```

Result of an ISO 3741:2010 reverberation-room sound power determination.

`sound_power_level` is the per-band `LW` (Eq. 20 direct method, Eq. 21
comparison method). `mean_pressure_level` is the mean corrected room level
`Lp(ST)` (Eq. 16). For the direct method `absorption_area` is the Sabine
equivalent absorption area `A` per band and `waterhouse_correction` the
boundary term `10*lg(1 + S*c/(8*V*f))`; both are `NaN` for the
comparison method. `background_correction` is the effective per-band
background correction `K1` (Eq. 14; zero when no background is supplied).
`c1` and `c2` are the reference-quantity and radiation-impedance
corrections (`c1` is `NaN` for the comparison method, which uses only
`c2`). `speed_of_sound` is `c` at the test temperature.
`sound_power_level_a` is the A-weighted total `LWA` (Annex F Eq. F.2),
computed only when `frequencies` are supplied (`NaN` for several bands
without them; equal to `LW` for a single band). `method` is `'direct'`
or `'comparison'`.

Initialize self.  See help(type(self)) for accurate signature.

### ReverberationSoundPowerResult.plot()

```python
ReverberationSoundPowerResult.plot(
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes
```

Plot the LW spectrum with the A-weighted total annotated.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## sound_power_comparison

```python
sound_power_comparison(
    levels: np.ndarray,
    levels_ref: np.ndarray,
    lw_ref: np.ndarray,
    *,
    frequencies: np.ndarray | None = None,
    background_levels: np.ndarray | None = None,
    background_levels_ref: np.ndarray | None = None,
    temperature: float = 23.0,
    static_pressure: float = 101.325,
) -> ReverberationSoundPowerResult
```

Sound power level in a reverberation room, comparison method (ISO 3741).

A reference sound source of known per-band sound power `lw_ref` is
measured at the same microphone positions as the source under test. The
sound power level in each band follows Eq. (21):

```text
LW = LW(RSS) + ( Lp(ST) - Lp(RSS) + C2 )
```

where `Lp(ST)` and `Lp(RSS)` are the mean room levels (Eq. 16/17) of the
test source and the reference source and `C2` is the radiation-impedance
correction. The absorption-area, Waterhouse and `C1` terms cancel between
the two sources, so the room absorption need not be known.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Mean room SPL per band (1D) or `(NM, NB)` per-position levels of the source under test, in decibels. |
| `levels_ref` | Same, for the reference sound source, in decibels. |
| `lw_ref` | Known sound power level `LW(RSS)` per band, in decibels. |
| `frequencies` | Band mid-frequencies (Hz) for the A-weighted total. |
| `background_levels` | Background levels matching `levels` for `K1`. |
| `background_levels_ref` | Background levels matching `levels_ref`. |
| `temperature` | Air temperature `theta` in the room, in degrees Celsius. |
| `static_pressure` | Static pressure `ps` in the room, in kilopascals. |

**Returns:** [`ReverberationSoundPowerResult`](/phonometry/reference/api/power/sound-power-reverberation/#reverberationsoundpowerresult) (`method='comparison'`).

## sound_power_reverberation

```python
sound_power_reverberation(
    levels: np.ndarray,
    t60: np.ndarray,
    volume: float,
    surface_area: float,
    frequencies: np.ndarray,
    *,
    background_levels: np.ndarray | None = None,
    temperature: float = 23.0,
    static_pressure: float = 101.325,
) -> ReverberationSoundPowerResult
```

Sound power level in a reverberation room, direct method (ISO 3741:2010).

`levels` is either a 1D per-band spectrum of the mean room sound pressure
level or a 2D `(NM, NB)` array (one row per microphone position, one
column per band) that is energy-averaged over positions (Eq. 16). The sound
power level in each band follows Eq. (20):

```text
LW = Lp(ST) + 10*lg(A/A0) + 4,34*(A/S) + 10*lg(1 + S*c/(8*V*f))
            + C1 + C2 - 6
```

with the Sabine equivalent absorption area `A = (55,26/c)*(V/T60)` and the
speed of sound `c = 20,05*sqrt(273 + theta)`. The Waterhouse term
`10*lg(1 + S*c/(8*V*f))` needs the band mid-frequencies, so `frequencies`
is required. `C1` and `C2` carry the result to the reference
meteorological conditions (clause 4).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Mean room SPL per band (1D) or `(NM, NB)` per-position levels, in decibels. |
| `t60` | Reverberation time `T60` per band, in seconds (scalar or one value per band). |
| `volume` | Reverberation-room volume `V`, in cubic metres. |
| `surface_area` | Total room surface area `S`, in square metres. |
| `frequencies` | One-third-octave (or octave) band mid-frequencies, Hz. |
| `background_levels` | Background levels matching `levels` for `K1`. |
| `temperature` | Air temperature `theta` in the room, in degrees Celsius. |
| `static_pressure` | Static pressure `ps` in the room, in kilopascals. |

**Returns:** [`ReverberationSoundPowerResult`](/phonometry/reference/api/power/sound-power-reverberation/#reverberationsoundpowerresult).

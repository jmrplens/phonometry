← [Documentation index](../../README.md)

# Wind turbine sound at a dwelling (IEC TS 61400-11-2)

[IEC 61400-11](wind-turbine-noise.md) measures what a turbine emits, close to
it and downwind. IEC TS 61400-11-2:2024 measures what arrives at a dwelling
several hundred metres away, where the wind that drives the rotor also stirs
the trees, raises the background and bends the sound on its way. The
measurement lasts weeks, and everything is sorted by wind speed and direction
before it is averaged. This page covers the calculations the TS writes down:
the wind speed at the heights the bins need, the bin averages with their
uncertainty, the background correction, the low frequency level indoors, the
emergence, the amplitude modulation rating and the rating level they feed.

## How the measurement goes

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_wind_turbine_receptor_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_wind_turbine_receptor.svg" alt="Section from two wind turbines to a dwelling. The binning wind speed comes from the power curve or the nacelle anemometer, recalculated to 10 m, sampled at 1 Hz or faster and averaged over 10 s to 10 min; a mast or remote sensing device has one height within 40 % of the hub height and another at least 15 m from it; temperature and humidity are read 1 m to 1.5 m above the ground. The free-field microphone stands on a tripod inside a two-stage or oversize wind screen, five wavelengths of the lowest frequency of interest, typically 15 m to 20 m, from the dwelling. A façade microphone is the alternative only where the signal needs it, on a façade plane within 0.05 m over 1 m, its edges more than 1 m away and the turbines within 45 degrees of its normal, and never for tonal audibility, amplitude modulation or impulsivity. A wind rose shows twelve sectors 30 degrees wide from north, the first from 345 to 15 degrees, with speed bins 1 m/s wide centred on integers and the downwind sector within 45 degrees of the line from the turbines. A panel lists the amplitude modulation analysis: 100 ms L_Aeq in one-third octaves from 20 Hz to 10 kHz at least, 10 s blocks, 60 to a 10 min period, wind referred to 10 min averages, free field only" width="100%"></picture>

A free-field microphone with a two-stage or oversize wind screen on a tripod
or a pole is the preferred mounting (8.1.3). A facade microphone raises the
signal-to-noise ratio but cannot be used for tonal audibility, amplitude
modulation or impulsivity (8.1.3); a proxy position is of limited use for them
too (8.1.2). Wind speed and direction come from the turbines or a mast and are
brought to 10 m (9.3); everything acoustic is binned in 1 m/s classes and 30°
sectors (10.1). For amplitude modulation the meter logs 100 ms `LAeq` in
one-third octave bands from 20 Hz to 10 kHz at least (13.6.1).

## Wind speed between heights (Annex K, 9.3.2)

The power law of Equation (K.1), `V_z = V_ref (z / z_ref)^alpha`, moves a wind
speed between heights with the shear exponent `alpha`, and Equation (K.2)
inverts it. The binning wind speed of 9.3.2.1 is a hub height speed brought
to 10 m with the logarithmic profile and `z0ref = 0,05 m` (3.31), which
assumes neutral air. At a wind farm it is the mean of the sound relevant
turbines (9.3.2.3): the quietest are left out while the total drops by no
more than 1 dB.

```python
from phonometry import environment

v10 = environment.power_law_wind_speed(
    8.0, height_m=10.0, reference_height_m=120.0, shear_exponent=0.3
)                                                 # Table K.1
alpha = environment.wind_shear_exponent(
    8.0, 5.0, height_m=120.0, reference_height_m=10.0
)                                                 # Table K.2
v_bin = environment.logarithmic_wind_speed(8.0, height_m=10.0, reference_height_m=120.0)
print(round(v10, 2), round(alpha, 2), round(v_bin, 2))   # 3.8 0.19 5.45

relevant = environment.sound_relevant_turbines([33.5, 38.2, 29.4, 36.9, 25.1, 31.8, 27.0])
print(relevant.indices, round(relevant.total_level_db, 1))   # (1, 3, 0) 42.3
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_shear_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_shear.svg" alt="Left: the power-law profile with a shear exponent of 0.26 through 4.5 m/s at 10 m and 8.6 m/s at 120 m, and the logarithmic profile with a roughness length of 0.05 m through the lower point. Right: the predicted levels of seven turbines at a dwelling, numbered from 1, the three loudest sound relevant, the total of 42.3 dB, the total less 1 dB and the energy sum of the loudest turbines together, which first reaches the total less 1 dB at the third" width="96%"></picture>

## Bin averages and the background (10.3, 11.7)

Each bin averages its intervals by energy (Equation (1)) or arithmetically for
a statistical level (Equation (8)); the type A uncertainty is Equation (2) or
(9), the type B part the root mean square of Equations (3) and (4), combined by
Equation (5). The background is subtracted bin by bin by Equation (6) where the
total is at least 3 dB above it, by a suggested 3 dB where it is at least 0 dB
but less than 3 dB above, and not at all where the background is louder (11.7).

```python
import numpy as np

rng = np.random.default_rng(611)
speeds = rng.uniform(2.6, 11.45, 420)
turbine = 33.0 + 2.0 * np.minimum(speeds, 9.0)
background = 15.0 + 3.4 * speeds
total = 10.0 * np.log10(10.0 ** (turbine / 10.0) + 10.0 ** (background / 10.0))
total_levels = np.round(total + rng.normal(0.0, 1.2, speeds.size), 1)
off_speeds = rng.uniform(2.6, 11.45, 240)
off_levels = np.round(15.0 + 3.4 * off_speeds + rng.normal(0.0, 1.5, 240), 1)

on = environment.bin_sound_levels(total_levels, speeds, type_b_uncertainty_db=0.5)
off = environment.bin_sound_levels(off_levels, off_speeds, type_b_uncertainty_db=0.5)
corrected = on.background_corrected(off)
print(np.round(corrected.turbine_levels_db[-3:], 1), corrected.regimes[-1].value)
# [50.8 50.4 52.2] three_db

prediction = environment.predicted_receptor_level([36.9, 38.2, 33.5], 1.5)
print(round(prediction.combined_uncertainty_db, 2))   # 2.55, Equations (10) and (11)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_bins_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_bins.svg" alt="Left: 420 ten-minute total levels against wind speed with the energy average of each 1 m/s bin and its uncertainty. Right: the total, the background and the corrected turbine level per bin, the 11 m/s bin where the background is within 3 dB circled" width="96%"></picture>

## Low frequency sound indoors (Annex C)

Equation (C.1) predicts the low frequency level band by band from 10 Hz to
200 Hz:
`L_p,LF = L_W,LF - 10 lg(l² + h²) - 11 dB + ΔL_g,LF - ΔL_a - ΔL_σ`, with the
ground correction and the air attenuation of Table C.2 and a facade insulation
such as the Danish rows of Table C.3.

```python
power = 118.0 - np.arange(environment.LOW_FREQUENCY_BANDS_HZ.size, dtype=float)
low = environment.wind_turbine_low_frequency_level(
    np.vstack([power, power, power - 1.0]),
    distance_m=[650.0, 820.0, 1100.0],
    hub_height_m=120.0,
    facade_insulation_db=environment.LOW_FREQUENCY_FACADE_INSULATION_DB[
        "Denmark brick or similar"
    ],
)
print(round(low.outdoor_level_db, 1), round(low.indoor_level_db, 1))   # 35.1 16.5
```

**Why Table C.2 sits under ISO 9613-1.** Its caption says 70 % relative
humidity and 10 °C, and from 125 Hz to 200 Hz its air attenuation is ISO 9613-1
at that atmosphere evaluated at the nominal band centres (0,41, 0,59 and
0,80 dB/km; ISO 9613-1's own Table 1, computed at the exact mid-band of
158,5 Hz, prints 0,584 dB/km at 160 Hz, while the TS's Table 7 follows the exact
mid-bands). From 50 Hz to 100 Hz it prints
0,07, 0,11, 0,17 and 0,26 dB/km where ISO 9613-1 at 70 % gives 0,08, 0,12, 0,19
and 0,28: from 10 Hz to 100 Hz the row is, cell for cell, Table 1.4 of the
Danish statutory order on wind turbine noise (BEK nr. 135 of 2019), set for
80 % relative humidity and 10 °C with Nord2000 band rates and no absorption
below 25 Hz. ISO 9613-1 at 80 % gives 0,07, 0,11, 0,17 and 0,25 dB/km there.
The table joins two atmospheres at 100 Hz, which is in the
[errata register](../../ERRATA.md). The library publishes the row as printed,
`LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM`, and takes other coefficients through
`air_attenuation_db_per_km=`.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_low_frequency_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_low_frequency.svg" alt="Left: the A-weighted low frequency band levels of three turbines outdoors (35.1 dB) and indoors behind the Danish brick facade (16.5 dB). Right: each printed air attenuation cell of Table C.2 minus ISO 9613-1 at 10 degrees C and 70 % and 80 % relative humidity, with the printed rounding strip of plus or minus 0.005 dB/km" width="96%"></picture>

## Emergence (Annex J)

The emergence of Equation (J.1) is the ambient criterion with the turbines
running less the background criterion with them stopped, per wind speed class.

```python
emergence = environment.sound_emergence(
    [38.5, 41.0, 43.5], [33.0, 37.5, 41.5], wind_speeds_m_s=[5.0, 6.0, 7.0]
)
print(emergence.emergence_db)   # [5.5 3.5 2. ]
```

## Amplitude modulation (clause 13)

Clause 13 implements the reference method of the IOA Amplitude Modulation
Working Group (13.2). The input is the 100 ms A-weighted level summed over
seven one-third octave bands (13.6.2.1.1). Each 10 s block (13.6.2.3) is
de-trended with a cubic fit and transformed with a rectangular DFT of 0,1 Hz
resolution into `S_xx = |F{x}|² / m²` (Equation (12)); the highest local
maximum in the user's range is the fundamental, and a block without one or with
a prominence `p_AM = L_pk / L_m` under 4 (Equation (13)) is prominence-failed.
The second and third harmonics join under the two 1,5 dB conditions, three
lines about each kept component are transformed back, and the depth is the
`L5 - L95` of that series. A 10 min period is rated with the 90th percentile of
its valid depths when at least 30 of its 60 blocks are valid, and 0 dB
otherwise (13.6.3); each wind speed bin reports the band with the highest mean
rating (13.6.4).

```python
t = np.arange(100) * 0.1
rng = np.random.default_rng(1340)
levels = np.round(
    38.0
    + 1.2 * np.sin(2 * np.pi * t / 47.0)
    + 2.0 * np.sin(2 * np.pi * 0.8 * t)
    + (4.0 / 6.0) * np.sin(4 * np.pi * 0.8 * t + 0.9)
    + rng.normal(0.0, 1.0, t.size),
    1,
)
block = environment.amplitude_modulation_block(levels, modulation_frequency_range_hz=(0.5, 1.1))
print(block.fundamental_frequency_hz, round(block.prominence, 1))   # 0.8 79.9
print(round(block.modulation_depth_db, 2))                          # 4.95

ratings = np.array([[2.1, 4.6, 3.0], [0.0, 0.0, 0.0], [1.8, 5.2, 3.9],
                    [2.5, 3.9, 4.4], [0.0, 0.0, 0.0], [3.1, 2.2, 5.0]])
binned = environment.bin_amplitude_modulation(ratings, [6.2, 6.4, 5.9, 7.1, 7.3, 6.8])
print(binned.selected_bands, np.round(binned.selected_ratings_db, 2))   # [2 3] [3.27 3.13]
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_modulation_block_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_modulation_block.svg" alt="Left: the power spectrum of one 10 s block with the fundamental at 0.8 Hz, the estimated harmonics and the three lines kept about each component. Right: the de-trended series and the reconstructed one with its L5 and L95, a depth of 4.95 dB" width="96%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_modulation_period_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_modulation_period.svg" alt="Left: the depth of each of the sixty 10 s blocks of a 10 min period, five invalid during a gusty minute, and the rating of 5.84 dB. Right: the mean rating of the worst band per 1 m/s bin of a survey, each point labelled with the band it selected (1 for 50 Hz to 200 Hz, 2 for 100 Hz to 400 Hz, 3 for 200 Hz to 800 Hz)" width="96%"></picture>

**The TS against the AMWG report and code.** The 10 s analysis is the report's
step for step. Where the TS departs, the library follows the TS: a period with
fewer than 30 valid blocks is rated 0 dB and kept in the bin mean (the report
discards it), and the band is chosen per bin (the report chooses one band for
the whole survey). The "excluded periods due to pf or other exclusions" that
13.6.4 leaves out of the bin mean are read as the periods the practitioner
excludes (`excluded=`): read literally they would be the periods 13.6.3 rates
0 dB, and the "including 0 values" of the same sentence would mean nothing. A
period of exactly 30 valid blocks is rated, as 13.6.2.2
and the report say; the bullets of 13.6.3 leave it out, which is in the
[errata register](../../ERRATA.md). The working group's code (v1.4) was used as
an oracle only: the library reproduces its printed sample result (prominence
44.64, fundamental 0.70 Hz and a 10 s rating of 8.38 dB for the 100 Hz to
400 Hz series in the 0.4 Hz to 0.9 Hz range) and its output on synthetic
blocks, as the [conformance report](../../CONFORMANCE.md) shows. The code alone
drops the line at an upper range limit of 0,6 Hz, 0,7 Hz, 1,2 Hz or 1,4 Hz,
because it compares floating-point frequencies and those multiples of 0,1 Hz
come out a little above the limit (sixteen times 0,1 Hz is exactly 1,6 Hz, so
that line is kept); the library works in line indices and keeps every limit's
line.

## The rating level (Annex A) and the tone search (12.5.2.4)

`L_r = L_eq + K`, with `K` the most severe of the tonal, amplitude modulation
and impulsive adjustments (A.1); Figure A.1 gives 0 dB below a depth of 3 dB,
3 dB at 3 dB rising to 5 dB at 10 dB, and 5 dB above. The upper tone search
frequency is the lowest band that ISO 9613-1 attenuates by 20 dB or more over
the distance to the nearest turbine (Table 7).

```python
k_am = environment.amplitude_modulation_adjustment(5.84)
rating = environment.wind_turbine_rating_level(
    41.0, tonal_adjustment_db=2.0, amplitude_modulation_adjustment_db=k_am
)
print(round(k_am, 2), rating.governing, round(rating.rating_level_db, 1))   # 3.81 amplitude_modulation 44.8

search = environment.upper_tone_search_frequency(
    600.0, temperature_c=10.0, relative_humidity_percent=50.0
)
print(search.upper_frequency_hz)   # 4000.0, as Table 7 prints
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_rating_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_receptor_rating.svg" alt="Left: the amplitude modulation adjustment of Figure A.1 against modulation depth with a rating of 5.84 dB marked at 3.8 dB. Right: the tonal, amplitude modulation and impulsive adjustments as bars, amplitude modulation hatched and named in the legend as the one applied, L_r = 44.8 dB" width="96%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tone_search_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tone_search.svg" alt="The ISO 9613-1 attenuation over 600 m at 10 degrees C and 50 % relative humidity per one-third octave band, the 20 dB line and the upper search frequency of 4 kHz" width="84%"></picture>

The row of Table 7 printed for 10 °C and 80 % holds the frequencies the rule
gives at −10 °C and 80 % (10, 5, 2,5 and 2 kHz where 10 °C gives 10, 6,3, 5
and 4 kHz); it is in
the [errata register](../../ERRATA.md) with eight other printed defects.

## What this guide covers

Implemented: the wind speed between heights of Annex K and the binning wind
speed of 9.3.2; the bin averages and uncertainties of Equations (1) to (9), the
background correction of Equations (6) and (7) under 11.7 and the prediction
uncertainty of Equations (10) and (11); the low frequency level of Equation
(C.1) with Tables C.1 to C.3 and C.5; the emergence of Equation (J.1); the
amplitude modulation of clause 13 with the higher bands of Annex G.3; the
rating level of A.1 with Figure A.1; and the upper tone search frequency of
12.5.2.4. Not implemented: the campaign itself (interval selection, filtering
and the auditioning of Annex F), the tonal audibility procedure of 12.5, the
impulsivity of clause 14 beyond the ISO/PAS 1996-3 adjustment, the infrasound
of Annex D, the Swedish and Danish criteria as verdicts, the Nord2000
propagation Annex C builds on, and the faster rotors of Annex G.2, whose
fundamental modulation frequency lies above the 1,6 Hz of 13.2.

## See also

- [Wind-turbine noise (IEC 61400-11)](wind-turbine-noise.md): the emission
  whose sound power levels feed Annex C and the prediction of 10.3.4.
- [Outdoor Sound Propagation](../propagation/outdoor-propagation.md): ISO
  9613-1 air absorption and the ISO 9613-2 chain.
- [Impulsive-sound prominence](../assessment/impulsive-sound.md): the ISO/PAS
  1996-3 adjustment.
- [Errata in published sources](../../ERRATA.md): Tables 7, C.2 and C.4, 13.6.3
  and five more.
- API reference: [`environment.assessment.wind_turbine_receptor`](https://jmrplens.github.io/phonometry/reference/api/environment/wind-turbine-receptor/)
  and [`environment.assessment.wind_turbine_modulation`](https://jmrplens.github.io/phonometry/reference/api/environment/wind-turbine-modulation/).

## References

- International Electrotechnical Commission. (2024). *Wind energy generation
  systems – Part 11-2: Acoustic noise measurement techniques – Measurement of
  wind turbine sound characteristics in receptor position* (IEC TS
  61400-11-2:2024, Edition 1.0). The implemented edition.
- Institute of Acoustics, Amplitude Modulation Working Group. (2016). *A method
  for rating amplitude modulation in wind turbine noise* (Final Report,
  Version 1, 9 August 2016). The reference method of clause 13.
- Institute of Acoustics, Amplitude Modulation Working Group. (2016). *IOA AM
  code*, v1.4, with its sample data.
  [SourceForge](https://sourceforge.net/projects/ioa-am-code/). Used as an
  oracle only.
- Miljøministeriet. (2019). *Bekendtgørelse om støj fra vindmøller* (BEK nr.
  135 af 07/02/2019). Table 1.4, the source of the Table C.2 row.
- International Organization for Standardization. (1993). *Acoustics –
  Attenuation of sound during propagation outdoors – Part 1: Calculation of the
  absorption of sound by the atmosphere* (ISO 9613-1:1993).

<!-- Written by `make llms` from site/src/content/docs/start/tasks.md: edit that page and its Spanish twin, then run `make llms`. -->

← [Documentation index](../README.md) · Published at https://docs.jmrp.io/phonometry/start/tasks/

# What do you need to measure?

The rest of this site is organised by subject, which is right once you know
which subject owns your problem and unhelpful before that. This page is the
other way round: the job on the left, the guide that answers it on the right,
with the standard the guide implements so you can tell before clicking whether
it is the one your client, your reviewer or your regulator will accept.

If your job is not listed, [All guides](../README.md) is the full
inventory, and the [glossary](../reference/glossary.md) goes the other
way again: you have a symbol from a report and you want the guide that computes
it.

## From a recording

| The job | Where it is answered |
|---|---|
| I have a WAV recording and I need A-weighted levels, $L_\mathrm{Aeq}$ and the percentile levels | [Build a sound level meter](../signals/sound-level-meter.md): IEC 61672-1 and IEC 61260-1, the whole chain on one runnable page, from the calibrator tone to the class check of every stage |
| My numbers are not in pascals and I do not know what they are | [Calibration and dBFS](../signals/metrology/calibration.md): the calibrator tone, the sensitivity in pascals per digital unit, the pre/post drift rule and the digital dBFS alternative |
| My file is the meter's own WAV: 24-bit, multichannel, or an overnight RF64, and I want it read and written without touching the level | [Reading and writing measurement audio](../io/audio-files.md): the calibrated `Signal`, the `bext` provenance, streaming, BWF writing and the calibration sidecar |
| I need a spectrum rather than a level | [Filter Banks](../signals/filters/filter-banks.md) for band levels (IEC 61260-1), [Spectral analysis](../signals/spectra/spectral-analysis.md) for a density estimate |

## Rooms and buildings

| The job | Where it is answered |
|---|---|
| The reverberation time of a room I can get into | [Measuring the Room Impulse Response](../buildings/rooms/room-impulse-response.md) for the acquisition (ISO 18233 sweeps and the interrupted-noise alternative), then [Room Acoustics](../buildings/rooms/room-acoustics.md) for $T_{20}$, $T_{30}$, EDT, $C_{50}$, $C_{80}$ and the rest of ISO 3382-1 |
| The reverberation time of a room that does not exist yet | [Reverberation-time prediction](../buildings/rooms/reverberation-prediction.md): the Sabine family, with the section that says which model to use and when every model fails; [Sound absorption in enclosed spaces](../buildings/rooms/enclosed-space-absorption.md) when a design report has to cite EN 12354-6 |
| Whether a room is quiet enough for what happens in it | [Room-noise criteria](../buildings/rooms/room-noise.md): NC, RC Mark II and NR, and the section on choosing between them |
| $R'_w$ or $D_{\mathrm{n}T,\mathrm{w}}$ of a partition I measured on site | [Field Insulation Measurement](../buildings/insulation/insulation-field.md) (ISO 16283-1/-2) for the measurement, then [Insulation Ratings](../buildings/insulation/insulation-ratings.md) (ISO 717-1/-2) for the single number and the adaptation terms |
| Proof that a wall meets the Spanish CTE DB-HR | [Spanish Building Code](../buildings/insulation/spanish-building-code.md): the required quantities, which one each requirement is written against, and the compliance check |
| The insulation of a building I am still designing | [Predicting Sound Insulation (EN 12354)](../buildings/design/insulation-prediction.md), and [Detailed prediction](../buildings/design/detailed-prediction.md) when the flanking paths have to be itemised |

## Machines, products and installations

| The job | Where it is answered |
|---|---|
| The sound power of a machine | [Sound Power](../devices/emission/sound-power.md): start here whatever the facility: its "Choosing a method" section routes to the pressure (ISO 3744/3745/3746), reverberation-room (ISO 3741), intensity (ISO 9614) or surface-vibration (ISO/TS 7849) method |
| A declared emission value for a datasheet or a CE file | [Declaring the noise emission](../devices/emission/sound-power.md#declaring-the-noise-emission-iso-4871): ISO 4871, the declared A-weighted level $L_{WAd}$ and its uncertainty $K_{WA}$ |
| How much a silencer, an enclosure or a duct run will attenuate | [Silencers](../devices/noise-control/silencers.md), [Industrial noise control](../devices/noise-control/noise-control.md) for enclosures and HVAC, [Duct paths](../devices/noise-control/duct-path.md) |
| A loudspeaker, microphone or amplifier measured to its standard | [Electroacoustic measurements](../devices/electroacoustics/electroacoustics.md): IEC 60268-3/-4/-5 |
| The loudness of a programme in LUFS | [Programme loudness and true peak](../devices/broadcast/program-loudness.md): ITU-R BS.1770-5 and EBU R 128 |

## Environment and transport

| The job | Where it is answered |
|---|---|
| $L_\mathrm{den}$, $L_\mathrm{night}$ or a rating level from an environmental survey | [Environmental noise levels](../environment/assessment/environmental-levels.md): ISO 1996-1/-2, the indicators and the adjustments that go on top of them |
| Source power for a road or railway noise map | [CNOSSOS-EU road traffic source emission](../environment/sources/cnossos-road-emission.md) and [railway source emission](../environment/sources/cnossos-rail-emission.md): Annex II of 2002/49/EC, the source side of it |
| The type-test noise of a train, a locomotive or a wagon | [Railway rolling-stock noise](../environment/sources/rolling-stock-noise.md): ISO 3095, on a track judged by EN 15610 and EN 15461 |
| How much a distance, a barrier or the weather takes off | [Outdoor propagation](../environment/propagation/outdoor-propagation.md) (ISO 9613-2), [Ground effect and barriers](../environment/propagation/ground-barriers.md), [Atmospheric refraction](../environment/propagation/atmospheric-refraction.md) |
| How much sound a road barrier sends back, measured where it stands | [Sound reflection of a noise barrier in situ](../environment/propagation/barrier-reflection.md): EN 1793-5, the sound reflection index and $DL_{RI}$ |
| Whether a wind farm is compliant | [Wind turbine noise](../environment/sources/wind-turbine-noise.md): IEC 61400-11 and the tonal audibility assessment; [at the dwelling](../environment/sources/wind-turbine-receptor.md): IEC TS 61400-11-2, the background correction, the amplitude modulation rating and the rating level |
| The certification level of an aircraft flyover | [Aircraft noise: EPNL](../aircraft/aircraft-noise.md): ICAO Annex 16, and [Airport noise contours](../aircraft/airport-noise.md) for the map around the airport |

## People

| The job | Where it is answered |
|---|---|
| Whether a worker is over the daily exposure limit | [Occupational Noise Exposure](../perception/hearing/occupational-exposure.md): ISO 9612, the $L_\mathrm{EX,8h}$ and its uncertainty |
| Loudness in sones, or sharpness, roughness and fluctuation strength | [Loudness](../perception/psychoacoustics/loudness.md) (ISO 532-1/-2/-3), then [Sound quality metrics](../perception/psychoacoustics/sound-quality.md) |
| Whether a tone in a noise is audible, and by how much | [Tone audibility](../perception/psychoacoustics/tone-audibility.md) (ISO/PAS 20065, DIN 45681) and [Tone prominence](../perception/psychoacoustics/tone-prominence.md), whose section on which metric to use covers both |
| The STI of a public-address system | [Speech Transmission Index](../perception/speech/speech-transmission.md): IEC 60268-16, direct and indirect (STIPA) |
| A seat, floor or hand-arm vibration record against the Directive | [Human Vibration](../vibration/human/human-vibration.md): ISO 2631-1 and ISO 5349-1, and [Multiple-shock vibration](../vibration/human/multiple-shock-vibration.md) for ISO 2631-5 |

## Materials, and under water

| The job | Where it is answered |
|---|---|
| The absorption coefficient of a sample | [Sound Absorption Measurement and Rating](../materials/absorbers/absorption-measurement.md) for the reverberation room (ISO 354, ISO 11654), [Impedance Tube](../materials/absorbers/impedance-tube.md) for normal incidence (ISO 10534-2) |
| The airflow resistivity or the dynamic stiffness of a layer | [Airflow resistance](../materials/absorbers/airflow-resistance.md) (ISO 9053-1/-2), [Dynamic stiffness](../materials/resilient/dynamic-stiffness.md) (EN 29052-1) |
| How much a diffuser scatters | [Diffusers and scattering](../materials/diffusers/diffusers.md): ISO 17497-1/-2, and the difference between the two coefficients |
| A ship's radiated noise, or the exposure of a pile-driving campaign | [Underwater acoustics](../underwater/underwater-acoustics.md) (ISO 17208, ISO 18406) then [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md) |
| How far a sound carries in the sea | [Underwater propagation](../underwater/underwater-propagation.md), and [Underwater propagation solvers](../underwater/underwater-solvers.md) when a range-dependent field is needed |

## When more than one method is right

Several guides carry the decision themselves, in a section written for a reader
who has the problem and not yet the method. They are worth opening before the
guide you think you need:

- [Choosing F, S or I](../signals/levels/time-weighting.md#choosing-f-s-or-i): which exponential time weighting a measurement calls for.
- [Which filter architecture should I choose?](../signals/filters/filter-gallery.md#which-filter-architecture-should-i-choose): Butterworth against the four alternatives, and what each trades away.
- [Choosing a criterion: NC, RC Mark II or NR](../buildings/rooms/room-noise.md#3-choosing-a-criterion-nc-rc-mark-ii-or-nr).
- [Choosing a model, and when every model fails](../buildings/rooms/reverberation-prediction.md#4-choosing-a-model-and-when-every-model-fails): Sabine, Eyring, Millington, Fitzroy, Arau.
- [Choosing a method](../devices/emission/sound-power.md#choosing-a-method): the seven routes to sound power and what each facility allows.
- [Choosing a loudness model](../perception/psychoacoustics/advanced-loudness.md#choosing-a-loudness-model): Zwicker, Moore-Glasberg and Sottek.
- [Which measure, and when](../perception/speech/objective-intelligibility.md#4-which-measure-and-when): STI against the intrusive and non-intrusive measures.
- [Which tonality metric, and when](../perception/psychoacoustics/tone-prominence.md#3-which-tonality-metric-and-when).
- [Direct or indirect](../perception/speech/speech-transmission.md#direct-or-indirect-choosing-between-them): full-matrix STI against STIPA.
- [Choosing a model](../underwater/underwater-solvers.md#6-choosing-a-model): normal modes, rays, Gaussian beams and the parabolic equation.

## Before you measure anything

Two habits save more measurements than any of the pages above. Record the
calibrator tone through the same chain, before and after, and treat the
difference as your drift bound. [Getting
Started](getting-started.md) shows why an uncalibrated level is
not approximately right but arbitrary. And read the "What this guide covers"
block at the end of whichever guide you land on: it states which clauses,
annexes and methods are implemented and which are not, which is the question a
reviewer will ask first.

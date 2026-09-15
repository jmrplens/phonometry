← [Documentation index](../../README.md)

# Spatial sound decay in workrooms (ISO 14257, ISO 11690-3)

A reverberation time says what a room does to a decay in time. It says very
little about what a factory hall does to a worker standing 20 m from a press.
The question there is about distance: how much quieter does it get as you walk
away, and how much louder is it than open air would be? ISO 14257 answers both
with one measurement. A calibrated source stands where a machine would, a
microphone walks away from it along a straight path, and the curve of level
against distance is the room's own signature.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/workroom_spatial_decay_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/workroom_spatial_decay.svg" alt="Three panels: the sound distribution value against distance in three octave bands against the free-field line, the rate of spatial decay by distance range, and the Annex B correction against distance" width="88%"></picture>

## The curve, and the line it is read against

A level on its own cannot be compared between rooms, because it depends on how
loud the source was. Equation (1) works with the sound distribution value
`D = L_p - L_W`, the level at a position referred to the sound power of the
source that produced it. The free field is then known exactly: Equation (2) is
`D_ref = 20 lg(r_0/r) - 11 dB` with `r_0 = 1 m`, where the 11 dB is
`10 lg(4 pi r_0^2)` rounded.

```python
from phonometry import room

distances = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0, 48.0]
levels = [98.9, 95.1, 93.0, 92.0, 91.0, 87.9, 85.8, 83.5, 81.5, 77.0, 75.6]

d = room.sound_distribution_value(levels, 110.8)
print(d[:3].round(1))                                          # [-11.9 -15.7 -17.8]
print(room.reference_distribution_value([2.0, 4.0]).round(2))  # [-17.02 -23.04]
```

## Two descriptors, and what each is for

DL2, Equation (5), is the slope: the least-squares fit of `D` against `lg r`,
converted from a decade to a doubling and signed so a decay is positive. A free
field gives 6 dB and any room gives less. DLf, Equations (6) to (8), is the
height: how far above open air the room sits. A room can decay steeply and
still be loud, so the two do not substitute for each other.

```python
res = room.spatial_decay_curve(d, distances, region="middle", far_limit_m=24.0)
print(round(res.decay_rate_db, 2))    # 4.73 dB per doubling
print(round(res.mean_excess_db, 2))   # 7.33 dB
```

The ranges are clause 6.2: near from 1 m to `d1`, middle from `d1` to `d2`, far
beyond `d2`, with 5 m and 16 m the typical pair and the middle range taken to
24 m whenever the room allows. ISO 11690-3, 4.3, says what to expect there:
2 dB to 5 dB per doubling and an excess of 2 dB to 10 dB.

## How the measurement goes

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_workroom_path_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_workroom_path.svg" alt="Section through a factory hall: the test source on the floor, the measurement path parallel to the floor with ten points on it, the clearances at each end, and the three distance ranges under the floor" width="88%"></picture>

Put the source where a machine would stand, with its acoustical centre on the
floor or at least 0,5 m above it, and at least 3 m from any wall or other
reflecting object. Check the margin over the background at every position and in
every one of the six octave bands from 125 Hz to 4 kHz: 10 dB or more needs no
correction, between 6 dB and 10 dB takes the ISO 3744 correction, and under 6 dB
there is no measurement. Walk the path from the source outwards at 1,55 m for a
standing workplace or 1,2 m for a seated one, with no obstacle on the floor below
it and nothing large within 1,5 m of either side, taking a band spectrum at each
of the distances 5.3.2 recommends, measured from the acoustical centre. Stop the
last point 1,5 m short of any wall, then walk a second path at right angles if
the room allows it. The source has to qualify first: Annex A asks for a
directivity index inside ± 2 dB up to 630 Hz, rising to ± 8 dB at 1 kHz.

```python
print(room.omnidirectionality_tolerance_db(800.0))   # 5.0
```

## Taking the source's own curve back out

Close to the source, much of what the microphone hears is the source's own
directivity and the floor reflection under it. Annex B swaps the measured
free-field curve of that source for the theoretical one of Equations (B.2) to
(B.4), which for a source on the floor is the flat 3 dB of a half space.

```python
free_field = [98.8, 94.7, 92.3, 90.3, 88.7, 86.1, 82.6, 79.8, 75.7, 73.7, 67.8]
reference = room.sound_distribution_value(free_field, 110.8)
corrected = room.corrected_distribution_value(d, reference, distances)

fixed = room.spatial_decay_curve(corrected, distances, region="middle", far_limit_m=24.0)
print(round(fixed.decay_rate_db, 2))    # 4.39 dB per doubling
print(round(fixed.mean_excess_db, 2))   # 6.73 dB
```

Annex C prints 4,4 dB per doubling, which is the corrected figure, and 7,3 dB of
excess, which is the uncorrected one. Applying the correction to one descriptor
and not to the other cannot be right, and 28 of the 36 printed results leave
their own rounding if the two are swapped; the entry is in
[Errata](../../ERRATA.md).

## One number, and the design half

Equation (3) weights the six bands by the spectrum of the machine that will
stand there, and Equation (4) fixes that spectrum as A-weighted pink noise so
two rooms can be compared without a machine in mind.

```python
by_band = [-11.9, -13.6, -12.5, -11.9, -12.4, -13.6]   # 125 Hz to 4 kHz
print(round(room.normalized_distribution_value(by_band), 2))   # -12.58
```

ISO 11690-3 sorts prediction into four categories, one diffuse-field and three
geometrical, and pairs each with the detail it has to be fed. Table E.1 reads in
both directions: a reader with a volume and one mean absorption coefficient is
limited to the diffuse-field method, and ray tracing over the real shape needs a
description gathered at that level first.

```python
print(room.detail_is_sufficient("1", room_detail=3,
                                fitting_detail=3, source_detail=1).satisfied)   # False
print(round(room.fitting_density(480.0, 1200.0), 2))                           # 0.1
print(round(room.workstation_level(sound_power_level_db=95.0,
                                   emission_level_db=85.0,
                                   absorption_area_m2=200.0), 2))              # 85.79
```

## What this page does not cover

Predicting the curve. ISO 11690-3 says what a prediction method must model and
how much detail it needs; it prints none, and neither ray tracing nor radiosity
is implemented here. Nor the reverberation-room calibration of the source, which
is ISO 6926 and ISO 3741, nor the directivity survey of Annex A, which needs a
turntable rather than a formula, nor the reporting checklist of clause 7.

## See also

- [Open-plan office acoustics (ISO 3382-3)](open-plan-acoustics.md): the same
  shape of measurement asked about speech rather than machinery.
- [Room acoustics](room-acoustics.md): what a room does to a decay in time.
- [Image sources and the steady-state room field](room-image-sources.md): the
  room constant and the critical distance this measurement so often contradicts.
- [Suspended ceilings (EN 16487)](../../materials/absorbers/suspended-ceilings.md):
  the product test code behind the absorption a workroom ceiling is sold on.
- [Errata in published sources](../../ERRATA.md): the Annex C correction defect
  above, and the two constants of Equations (5) and (8) that differ by 0,3 %.
- API reference: [`room.spatial_decay`](https://jmrplens.github.io/phonometry/reference/api/rooms/spatial-decay/)
  and [`room.workroom_prediction`](https://jmrplens.github.io/phonometry/reference/api/rooms/workroom-prediction/).

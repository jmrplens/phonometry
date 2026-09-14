← [Documentation index](../../README.md)

# Enclosures and cabins measured (ISO 11546, ISO 11957)

A model says what an enclosure should be worth. It takes the transmission loss
of the panels, subtracts a penalty for the reverberant build-up in the cavity
and returns an insertion loss. It is a good number and it is not the one a
buyer can hold anybody to, because it knows nothing about the gap under the
door, the conduit that was run through the wall afterwards, or the fan that was
fitted to keep the machine cool.

These three standards measure what was built. The quantity is a **difference of
two runs**: determine the machine's sound power without the enclosure,
determine it again with the enclosure in place, and subtract band by band. That
is Equation (1) of both parts of ISO 11546, and nothing else in either document
is more complicated than it. The care is all in what "the same determination
twice" means.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosure_cabin_insulation_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/enclosure_cabin_insulation.svg" alt="Three panels. Left: two octave-band sound power spectra of the same machine, one measured without the enclosure and falling from ninety-six to eighty-nine decibels, one measured with it and falling from eighty-eight to sixty-three, with the area between them shaded and the insertion loss drawn against a second axis rising from eight decibels at 125 Hz to twenty-six at 2 kHz, annotated with the A-weighted insertion loss of nineteen point three decibels. Middle: the area ratio a room must reach against its mean absorption coefficient, on logarithmic axes, drawn as two straight falling lines, one for the two-decibel environmental correction limit of the precision and engineering methods and one for the seven-decibel limit of the survey methods, with the seven room descriptions of Table C.2 marked on the upper line. Right: a staircase of the loudspeaker positions an in-situ cabin measurement requires against the largest deviation of the apparent insulation between any two of them, flat at three up to three decibels, stepping to four, five and six, and flat at six thereafter, with the region past six decibels shaded to mark where the excess is reported instead" width="100%"></picture>

*The insertion loss is the gap between two runs; the room has to be
good enough for the method that measured them; and in situ the number of
source positions is decided by the answer.*

## Two parts, one procedure

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_enclosure_cabin_measurement_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_enclosure_cabin_measurement.svg" alt="Two arrangements side by side. On the left, the same machine measured twice on the same dashed measurement surface, once standing free and once inside the enclosure, and the insertion loss is the difference of the two sound powers. On the right, a room driven by a loudspeaker with three microphones in it and an empty cabin inside it with two more, and the insulation is the difference of the two sound pressure levels. A box at the foot carries both equations" width="100%"></picture>

**How the measurement goes.** Pick the base standard first, because Table 1
decides what the result may be called. Fix the measurement surface and keep it
for both runs: determine the sound power without the enclosure, fit it without
moving the machine or the microphones, and determine it again. Where the machine
cannot be run twice, use the reciprocity method or the artificial source of
Annex A and say which. For the cabin, drive the room, take the level in it and
the level inside the empty cabin, and in situ add loudspeaker positions until
the spread of the answer stops asking for more.

**ISO 11546-1** measures in a laboratory, for a **declaration**: the
manufacturer's figure, obtained under conditions a buyer can compare across
suppliers. **ISO 11546-2** measures the same thing **in situ**, for an
**acceptance**: the enclosure as installed, in the room it was installed in,
with the machine it was built for. The two share their definitions, their
equations, their reporting rules and their artificial source word for word.
What changes is the environment, the base standard the levels come from, and,
in part 2, an annex that asks whether the room is good enough at all.

```python
from phonometry import noise_control

bands = [125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]
without = [96.0, 98.0, 99.0, 97.0, 94.0, 89.0]   # dB, machine alone
with_box = [88.0, 86.0, 81.0, 74.0, 68.0, 63.0]  # dB, enclosure fitted

res = noise_control.sound_power_insulation(
    without, with_box, frequencies=bands, band_fraction=1,
)
print(res.rounded())                    # [ 8 12 18 23 26 26] dB
print(round(res.a_weighted_insulation, 1))   # 19.3 dB
```

The A-weighted number is the single figure a declaration carries. Clause 9.4
reports every band value rounded to the nearest decibel. Both parts also
measure a sound pressure insulation at a stated position, Equations (3) and
(4), through `sound_pressure_insulation`: a different quantity with the same
arithmetic, belonging to one microphone position, which is why the standard
makes the position reportable.

## What the method may declare

Table 1 of both parts decides what may be written on the data sheet. Not every
way of determining a sound power gives a spectrum: a survey-grade determination
hands back an A-weighted value and nothing per band, so the band insulation
cannot be declared from it at all.

```python
for entry in noise_control.applicable_methods(condition="in-situ"):
    if not entry.band_values:
        print(entry.base_standard, entry.quantities)
# ISO 3746 ('D_WA',)
# ISO 11202 ('D_pA',)
```

Those two rows exist only in part 2. The laboratory table of part 1 admits no
survey-grade determination at all, and its own footnote goes further: where a
standard has a grade 3 variant, ISO 9614-1 and ISO 11204, that variant is
excluded. A declaration is the one place where the measurement has to be at
least an engineering one, and Table 1 is where the document says so.

The table also decides which substitute source is available where the machine
cannot be run. Clause 1 draws the scope around the actual source rather than
around the substitutes: the part applies to a free-standing enclosure smaller
than 2 m³ without any restriction, and a larger one may still be measured with
its actual source while the base standard's own limit on volume is met. The two
substitutes are the reciprocity method of part 1, 7.2, which puts the enclosure
in a diffuse field and measures inside it and exists in part 1 only; and an
artificial source, the tapping machine of Annex A dropped on an undamped steel
plate, used at several positions and averaged arithmetically, which is the
standard's own word and not the energy mean used almost everywhere else in this
library.

## Is the room good enough?

Annex C of part 2 asks the question the emission standards ask backwards. They
ask what the environmental correction of a room is; the annex asks how much
room a method needs. Holding the correction at the limit Table C.1 sets and
solving for the room gives the ratio of the room's boundary surface to the
measurement surface, which is Figure C.1 in closed form: the curve the annex
asks the reader to read off by eye.

```python
verdict = noise_control.test_environment_applicability(
    base_standard="ISO 3744",
    mean_absorption_coefficient=0.15,
    room_surface_area_m2=520.0,
    measurement_surface_area_m2=14.1,
)
print(round(verdict.required_area_ratio, 1))  # 45.6
print(round(verdict.actual_area_ratio, 1))    # 36.9
print(verdict.applicable)                     # False
```

That room cannot carry a precision determination. It can carry a survey one,
which asks 6,6 rather than 45,6, and the answer that comes back from it is an
A-weighted value with no spectrum behind it. Reading Table 1 after Annex C is
how those two facts stay together. Where nobody measured the absorption, Table
C.2 gives seven room descriptions and their coefficients, from 0,05 for an
empty room with smooth hard walls to 0,5 for a room with a highly absorptive
ceiling and floor; they are `ROOM_ABSORPTION_ESTIMATES`, the same seven rows
ISO 3744 prints in its own Table F.1.

## The cabin is the inverse problem

An enclosure keeps noise **in**. A **cabin** keeps it **out**, and ISO 11957
measures that as the difference between the level in the room and the level
inside the empty cabin. Equation (1) is the laboratory quantity, measured in a
reverberation room to ISO 3741. Equation (2) is the same arithmetic in situ,
where no requirement is placed on the room at all, and the answer carries a
prime to say so. The prime is not decoration: definition 3.6 exists because a
number measured in a room that was never qualified cannot be compared with one
that was, and clause 4 says outright that only data from the same method may be
used when comparing cabins.

```python
room = [88.0, 90.0, 91.0, 89.0, 86.0, 82.0]    # dB, level in the room
inside = [76.0, 72.0, 66.0, 59.0, 52.0, 47.0]  # dB, level in the cabin

cab = noise_control.cabin_insulation(
    room, inside, frequencies=bands, band_fraction=1,
    method="in-situ-loudspeaker",
)
print(cab.symbol, cab.rounded())   # D'_p [12 18 25 30 34 35] dB
```

There is a third method, and it is the one a workplace usually wants: drive the
room with the noise that is actually there. That is the only method for which
the standard defines an A-weighted difference, Equation (3), and
`cabin_insulation` refuses to compute one under any other, because a figure
carrying that symbol which came from a loudspeaker is a claim the document does
not make.

## The count that is read off the answer

Almost every number in a measurement standard is fixed before the measurement:
six microphone positions, 2 m from the cabin, 3 m apart. Clause 7.2.1 of
ISO 11957 has one that is not. The number of loudspeaker positions shall be at
least the largest deviation, in decibels, of the apparent insulation between
any two of them, read in octave bands, starting at three and stopping at six.
It is a criterion that judges the measurement by how much it disagreed with
itself.

```python
by_position = [
    [12.0, 16.0, 25.0, 30.0, 34.0, 35.0],
    [13.5, 18.0, 27.5, 32.0, 36.5, 36.0],
    [11.0, 14.5, 23.0, 28.5, 33.0, 34.0],
]
check = noise_control.check_source_positions(by_position)
print(check.max_octave_spread_db)   # 4.5
print(check.required_positions)     # 5
print(check.satisfied)              # False
```

Two more positions, and the clause adds that the three used first should not be
used again. Past six decibels the excess is stated in the report instead, which
`exceeds_maximum` marks. The other numeric rules are here too:
`check_band_flatness` is the requirement that the three one-third-octave levels
inside an octave differ by at most 6 dB at 125 Hz, 5 dB at 250 Hz and 4 dB
above; `minimum_cabin_clearance_m` is the clearance of 6.2, written exactly as
printed including the low-frequency sentence that relaxes it rather than
tightening it; and `internal_noise_level` is the noise the cabin's own fans
make, corrected for the background only while the margin stays between 6 dB and
10 dB, which is a different rule from the one 6.4 applies to the insulation.

## One number, and what it is worth

All three documents delegate their single number to ISO 717-1, putting their
own quantity where that standard writes the sound reduction index.

```python
rating = noise_control.weighted_cabin_insulation(
    cab.insulation[:5], apparent=True, band_fraction=1,
)
print(rating.rating, rating.c, rating.ctr)   # 28 -1 -5
```

Clause 4 of ISO 11957 calls that the preferred single number and then warns, in
the same paragraph, against reading too much into it: what a cabin is worth
depends on the spectrum it stands in. The annexes answer that objection
directly, estimating the A-weighted insulation against a stated spectrum. The
sign of the A-weighting term is the trap: the annex prints an attenuation,
positive where the weighting takes level away, while a library's band
corrections are the correction itself. Both terms are built from the same table
here, so the answer cannot disagree with its own inputs, and an insulation of
zero returns exactly zero.

```python
spectrum = [92.0, 94.0, 95.0, 93.0, 90.0, 85.0]   # dB, the actual noise
print(round(noise_control.estimated_cabin_noise_insulation(
    spectrum, cab.insulation, frequencies=bands,
), 1))                                             # 25.6 dB
```

Against that spectrum the cabin is worth 25,6 dB(A), where its rating is 28. The
two numbers answer different questions, and the rating is not the one to put in
a hearing-conservation calculation.

## What the report has to say, and what it cannot

Clause 10 of ISO 11957 is unusually candid. In the laboratory the uncertainty of
ISO 3741 carries over from 250 Hz to 10 kHz, and only while the room is at least
twenty times the volume of the cabin. The loudspeaker method in situ adds about
2 dB to the standard deviation. For the actual-noise method the clause states
nothing at all and sends a declared value to ISO 4871.

```python
u = noise_control.uncertainty_conditions(
    room_volume_m3=520.0, cabin_volume_m3=18.0, method="in-situ-loudspeaker",
)
print(round(u.volume_ratio, 1), u.ratio_satisfied)   # 28.9 True
print(u.excess_standard_deviation_db)                # 2.0
```

A measurement whose room is too small for the cabin still returns a number.
What it does not return is the uncertainty statement, and a report that quotes
one anyway is quoting a clause that excluded it.

## What this guide covers

Covered: the arithmetic of all three documents. Equations (1) to (5) of
ISO 11546, Table 1 as data, the ISO 717-1 rating, the estimate of Annex C and
Annex D, the leak, seal and fill ratios, the source clearance, and the whole of
Annex C of part 2 with Table C.1, Table C.2 and Figure C.1 in closed form,
cross-checked against the environmental correction of ISO 3744. Equations (1),
(2) and (3) of ISO 11957 with the prime of definition 3.6, its ISO 717-1
rating, the estimate of Annex A, the source-position criterion of 7.2.1, the
flatness rule of 6.4, the clearance of 6.2, the internal noise level of 6.7 and
the conditions clause 10 attaches its uncertainty to. Ten defects in the
print of the three documents are recorded in the
[errata register](../../ERRATA.md). Not implemented: the prediction of an
insulation, which is a separate page; the test environments themselves; the
artificial source as hardware; and the mounting, instrumentation and reporting
procedure, of which only the rounding computes.

## See also

- [Industrial noise control](noise-control.md): the predicted insertion loss of
  a machine enclosure, which is the quantity this page measures rather than
  computes.
- [Measuring a silencer](silencer-measurement.md): the same distinction for a
  ducted silencer, and the substitution measurement behind a catalogue figure.
- [Sound power in a reverberation room](../emission/sound-power-reverberation.md):
  the determination the cabin laboratory method is carried out in, and the
  background correction all three documents delegate to.
- [Airborne sound insulation ratings](../../buildings/insulation/insulation-ratings.md):
  the ISO 717-1 machinery all three documents borrow for their single number.
- [Errata in published sources](../../ERRATA.md): a column headed with a
  standard that does not exist, a definition that points at the wrong annex,
  and a clearance rule that relaxes the one above it.
- API reference: [`noise_control.enclosure_insulation`](https://jmrplens.github.io/phonometry/reference/api/noise_control/enclosure-insulation/)
  and [`noise_control.cabin_insulation`](https://jmrplens.github.io/phonometry/reference/api/noise_control/cabin-insulation/).

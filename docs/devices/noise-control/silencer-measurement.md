← [Documentation index](../../README.md)

# Measuring a silencer (ISO 7235 and ISO 11691)

Everything a silencer model computes comes from geometry. The figure a
supplier publishes does not. It is an **insertion loss measured by
substitution**: the same rig run twice, once with a plain duct where the
silencer will go and once with the silencer in it, and the difference between
the two receiving-side levels, band by band. Reading a catalogue without
knowing that is how a computed 8,9 dB and a published "25 dB" end up in the
same sentence.

Two standards describe the measurement and differ only in how much they ask
of the laboratory. **ISO 7235:2003** is the full procedure, with a modal
filter decoupling the source, a qualified receiving side, and a stated
measurement uncertainty; it covers silencers, air-terminal units and other
duct elements, with flow and without. **ISO 11691:1995** is the survey-grade
laboratory method without flow, six printed pages carrying two equations, for
silencers whose design velocity does not exceed 15 m/s.

## 1. One subtraction, two numberings

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_silencer_iso7235_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_silencer_iso7235.svg" alt="Two stacked runs on one duct axis. In the upper run, series one, a sealed and lined loudspeaker box feeds a modal filter, then a transition, then the test object, then a test duct with an anechoic wedge termination carrying three microphone positions on a line inclined to the duct axis. The lower run, series two, is identical except that the test object is replaced by an empty substitution duct. Dashed qualification planes are marked at the test object and at the receiving duct. Below, the insertion loss is given as the difference of the two receiving-side levels, third octave by third octave, with the modal-filter attenuation, the reflection-coefficient limit, the substitution-duct tolerance and the signal-to-background rule listed as the standard's own clause numbers" width="92%"></picture>

*The two series are the whole method: everything else in both standards is
about making sure nothing but the test object changed between them.*

The measurement is the same in both:

$$
D_\mathrm{i} = L_{W\mathrm{II}} - L_{W\mathrm{I}}
$$

with $\mathrm{I}$ the series that had the test object and $\mathrm{II}$ the
series that had the substitution duct. ISO 11691 writes the identical thing
as $D = L_{p1} - L_{p2}$, and numbers the two series **the other way round**:
its 1 is the substitution duct. Two standards for one measurement, with
opposite subscripts, is exactly the sort of thing that gets entered backwards,
so the arguments here are named for what was in the duct rather than for
either numbering.

```python
from phonometry import noise_control

substitution = [88.0, 90.0, 91.0, 92.0, 92.0, 91.0]   # dB, empty duct
with_silencer = [84.0, 83.0, 79.0, 72.0, 66.0, 63.0]  # dB, silencer fitted

d_i = noise_control.substitution_insertion_loss(substitution, with_silencer)
print(d_i)                        # [ 4.  7. 12. 20. 26. 28.] dB
```

If the receiving room's absorption moved between the two series, that
difference is not yet the insertion loss. Clause 6.3 puts it right with
$10\lg(T_2/T_1)$, where $T_2$ is the reverberation time measured with the
test object installed. A room that got **deader** while the silencer was in it
was flattering the silencer, and the correction takes that back:

```python
corrected = noise_control.substitution_insertion_loss(
    substitution, with_silencer, reverberation_times=(2.1, 1.8),
)
print(corrected.round(2))         # [ 3.33  6.33 11.33 19.33 25.33 27.33] dB
```

Clause 6.3 also allows $T_2 = T_1$ outright when the test object sits outside
the room, and then the pair can be left out.

## 2. What the number is not

It is not a transmission loss. It is measured against a particular
substitution duct in a particular rig, and it carries that rig with it in two
ways worth naming.

The first is the **limiting insertion loss**: sound flanks along the duct
walls rather than through the silencer, and no arrangement can measure past
what its own flanking lets round. ISO 7235 has the laboratory measure that
ceiling with the substitution duct acoustically blocked and record it as a
function of frequency (7.4). A very large catalogue figure is a claim about
the test arrangement as much as about the device.

The second is the receiving side, which decides how much of the sound the
microphones see at all. ISO 7235 allows three (5.2.4): a reverberation room
to ISO 3741 qualified at least down to the 125 Hz one-third octave, which is
preferred; a test duct with an anechoic termination whose reflection
coefficient is no greater than 0,3; or essentially free-field conditions at
the open end. ISO 11691 keeps only the reverberation room and the free-field
alternatives, and asks for 3,5 m of duct on each side of the silencer.

None of that is arithmetic, which is why the rest of this page is short. The
arithmetic that remains is the part a reader can get wrong on paper.

## 3. Octaves are folded on the energy, not on the decibels

A measurement is made in one-third octaves and often reported in octaves.
ISO 11691 Equation (2) says how, and it is not an average of the three
numbers:

$$
D_\mathrm{oct} = -10 \lg\left[\frac{1}{3}\left(
   10^{-D_1/10} + 10^{-D_2/10} + 10^{-D_3/10}
\right)\right]\ \text{dB}
$$

The average is taken on what the silencer **lets through**. That matters
because a silencer is rarely flat across an octave, and the band that leaks
decides the answer:

```python
thirds = [4.0, 7.0, 12.0, 20.0, 26.0, 28.0]
print(noise_control.octave_insertion_loss(thirds).round(2))
#                                 # [ 6.57 23.28] dB
```

The plain arithmetic means of the same two groups are 7,67 and 24,67 dB, so
reading the decibels rather than the energy would have overstated both
octaves by about a decibel. On a steeper silencer the gap is larger: three
thirds of 30, 30 and 5 dB give **9,7 dB** over the octave, not 21,7. Almost
all the transmitted sound is coming through the one band that does not work,
and Equation (2) is written out rather than described precisely so that this
cannot be got wrong.

ISO 11691 states the assumption it rests on: the sound pressure levels of the
three one-third octaves are taken to be equal in the series run with the
substitution duct, which is what lets their energies be weighted equally.

## 4. Three microphone positions, or five

In a test duct the spatial average comes from at least three microphone
positions equally spaced on a line across the duct, spanning at least a
quarter wavelength of the band, about half way along the duct. Three is
enough only if the three agree. ISO 7235 Table 6 says how closely, and if the
highest and lowest differ by more than that, five positions shall be used:

```python
levels = [70.0, 74.0, 79.0]       # dB at the three key positions
print(noise_control.microphone_spread_limit(125.0))     # 7.0 dB
print(noise_control.microphone_positions_required(levels, 50.0))    # 3
print(noise_control.microphone_positions_required(levels, 125.0))   # 5
```

The same three levels are acceptable at 50 Hz, where the limit is 10 dB, and
not at 125 Hz, where it is 7. The limit falls with frequency because a duct
at low frequency has a standing-wave pattern that three points sample badly,
and at high frequency does not.

One thing to know about Table 6: its rows read 50, 63, 80, 100, 125 and then
`> 160` Hz, so the **160 Hz one-third octave belongs to no row** and is given
no limit at all. Every other row names a single band, and 160 Hz is a
one-third-octave centre like the rest, so it is read here as belonging to the
last row. The gap is in the [errata
register](../../ERRATA.md).

## 5. How repeatable any of this is

Both standards answer, and neither answer is flattering.

ISO 11691 says outright that exact information on the precision of its method
cannot be given, that interlaboratory tests would be needed for a real
reproducibility standard deviation, and that this is what makes it a survey
standard. Its Table 1 offers an estimate only: 2 dB up to the 1,25 kHz
one-third octave and 3 dB above it.

ISO 7235 Table 7 has three columns, and the disagreement between them is the
useful part:

```python
for band in (50.0, 250.0, 1000.0, 4000.0):
    print(band, [
        noise_control.measurement_reproducibility(band, quantity=q)
        for q in ("insertion_loss", "transmission_loss", "intensity")
    ])
# 50.0   [1.5, 3.0, 3.0]
# 250.0  [1.0, 3.0, 1.5]
# 1000.0 [2.0, 3.0, 1.0]
# 4000.0 [3.0, 3.0, 1.0]
```

Insertion loss is measured best in the middle of the range and worst at the
top; the sound-intensity route runs the other way; transmission loss is a
flat 3 dB everywhere. Clause 7.9 explains why: only the insertion-loss column
came from tests, on 1 m long parallel-baffle silencers, and the other two rest
on experience. A column that does not move with frequency is the shape of an
estimate, not of a measurement.

What goes on the report is twice the table value, for a coverage probability
of 95 %:

```python
print(noise_control.measurement_expanded_uncertainty(250.0))    # 2.0 dB
print(noise_control.measurement_expanded_uncertainty(4000.0))   # 6.0 dB
```

A silencer quoted at 25 dB in the 4 kHz band is being quoted to within 6 dB.

## 6. The scope ISO 11691 draws round itself

The survey method is deliberately narrow, and its limits are published rather
than implied. The design velocity may not exceed 15 m/s, because the method
runs the rig with no flow at all and so includes none of the self-generated
noise. It is written for circular silencers from 80 mm to 2 m in diameter, or
rectangular ones of comparable area. And the test ducts have to be close in
cross section to what they feed, between 0,6 and 1,7 times the area of the
silencer or the substitution duct (4.5). Outside that, the joints reflect more
than the method allows for, and the library says so:

```python
print(noise_control.substitution_area_ratio(0.0962, 0.0962))    # 1.0
print(noise_control.SURVEY_MAX_VELOCITY_M_S)                    # 15.0
print(noise_control.SURVEY_AREA_RATIO_RANGE)                    # (0.6, 1.7)
```

## Standards

ISO 7235:2003 and ISO 11691:1995, read from BS EN ISO 7235:2009 and
BS EN ISO 11691:2009, which endorse them without modification. Implemented:
Equation (1) of both standards with the reverberation-time correction of
ISO 7235 6.3; the octave fold of ISO 11691 Equation (2); ISO 7235 Table 6 and
the three-or-five rule of 6.2.1; ISO 11691 Table 1 and all three columns of
ISO 7235 Table 7, with the coverage factor of 7.9; and the scope of
ISO 11691 1.1 and 4.5. Checked in the
[conformance report](../../CONFORMANCE.md); the gap Table 6 leaves at 160 Hz
is in the [errata register](../../ERRATA.md). Not implemented: the facility
requirements themselves, the flow half of ISO 7235 (6.4, 6.5 and Annex B),
and ISO 11820, which measures a silencer in situ.

## See also

- [Silencers](silencers.md): the reactive
  four-pole models this measurement is the counterpart of, and the rig it is
  made on, described in full.
- [Duct-Borne Noise: Fan to Room](duct-path.md):
  where a measured insertion loss goes once it has been bought.
- [HVAC Noise the German Way (VDI 2081)](vdi2081-air-systems.md):
  the splitter-silencer insertion loss predicted from geometry, for comparison
  with what a laboratory would measure.
- [Errata in published sources](../../ERRATA.md): the gap Table 6 of ISO 7235
  leaves at 160 Hz.
- API reference: [`noise_control.silencer_measurement`](https://jmrplens.github.io/phonometry/reference/api/noise_control/silencer-measurement/).

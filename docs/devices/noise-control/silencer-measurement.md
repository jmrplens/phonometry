← [Documentation index](../../README.md)

# Measuring a silencer (ISO 7235 and ISO 11691)

Everything a silencer model computes comes from geometry. The figure a
supplier publishes does not. It is an **insertion loss measured by
substitution**: the same rig run twice, once with a plain duct where the
silencer will go and once with the silencer in it, and the difference between
the two receiving-side levels, band by band. Reading a catalogue without
knowing that is how a computed 8,9 dB and a published "25 dB" end up in the
same sentence.

Two standards describe the measurement, and they differ in scope as much as
in what they ask of the laboratory. **ISO 7235:2003** is the full procedure,
with a modal filter decoupling the source, a qualified receiving side and a
stated measurement uncertainty, and it covers silencers, air-terminal units
and other duct elements, with flow and without. **ISO 11691:1995** is six
printed pages carrying two equations, and it measures silencers and nothing
else, without flow and with none in the answer, up to a design velocity of
15 m/s. A measurement that needs flow, or an object that is not a silencer,
is outside ISO 11691 and belongs to ISO 7235.

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

## 7. The open end, and the two quantities that need it

A duct radiating into a room does not hand the room everything that reaches
its mouth. Well below the frequency at which the mouth is a wavelength across
it is a poor radiator, and most of the energy turns round and travels back up
the duct. Annex B.3 puts a number on it:

$$
D_\mathrm{td} = 10 \lg\left[1 +
   \frac{\Omega}{\left(\dfrac{4\pi f \sqrt{S}}{c}\right)^{2}}\right]\ \text{dB}
$$

The group $4\pi f \sqrt{S} / c$ is the mouth measured in wavelengths, and
$\Omega$ is the solid angle it radiates into. A 350 mm duct flush with a wall
holds back 11 dB at 63 Hz and nothing at all at 2 kHz:

```python
import numpy as np

bands = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0])
area = 0.0962                     # m2, a 350 mm circular duct

d_td = noise_control.open_end_transmission_loss(bands, area)
print(d_td.round(2))              # [11.23  6.14  2.5   0.77  0.21  0.05] dB
```

The solid angle is Table B.1, and the same five values are Table 1 of
ISO 5135. A duct that ends in the middle of the room has twice the space to
radiate into that a flush one has, so it reflects half as much:

```python
free = noise_control.open_end_transmission_loss(
    bands, area, solid_angle=noise_control.RADIATION_SOLID_ANGLES["C"],
)
print(free.round(2))              # [14.07  8.59  4.08  1.43  0.4   0.1 ] dB
```

Equation (B.4) says the same fact the other way round, as a pressure
reflection coefficient, and the two close exactly on the energy:
$D_\mathrm{td} = -10\lg(1 - r^2)$ at every frequency, area and solid angle.
That identity is the conformance anchor for both, because neither is printed
with a worked value. It also has a use of its own: 5.2.4 qualifies a test
duct as anechoic only below $r = 0{,}3$, which this bare open end reaches
somewhere between 500 Hz and 1 kHz.

```python
r = noise_control.open_end_reflection_coefficient(bands, area)
print(r.round(3))                 # [0.962 0.87  0.662 0.404 0.215 0.11 ]
```

The library carries a second closed form for the same physics, Reynolds' as
given by Long, in
[`end_reflection_loss_closed_form`](noise-control.md).
It raises the same argument to 1,88 rather than to 2, and for a circular duct
in free space the two read $10\lg[1 + (c/\pi f d)^2]$ against
$10\lg[1 + (c/\pi f d)^{1,88}]$. They agree closely where the argument is
near 1 and part company at the ends of the range.

Two quantities need it. Equation (6) turns the measured insertion loss of an
air-terminal unit into its transmission loss by putting back what the mouth
was keeping in anyway, so the two are the same number at the top of the range
and eleven decibels apart at the bottom:

```python
d_i = np.array([4.0, 7.0, 12.0, 20.0, 26.0, 28.0])
print(noise_control.measured_transmission_loss(d_i, d_td).round(2))
#                                 # [15.23 13.14 14.5  20.77 26.21 28.05] dB
```

And Equation (7) makes the flow noise a sound power,
$L_W = \overline{L_p} + D_\mathrm{td} + C$, where $C$ is the ISO 3741 level
difference between the power radiated into the room and the average pressure
in it. Clause 6.4 is explicit that $\overline{L_p}$ goes in **without** a
background correction: the two series are reported separately and the reader
subtracts them.

## 8. Where higher-order modes start

The modal filter between the source and the test object exists to stop
higher-order modes reaching the silencer, and its requirement steps at the
frequency where those modes can propagate in the connected ducts: at least
3 dB of longitudinal attenuation of the fundamental at the low-frequency end,
and at least 5 dB above that frequency (5.2.2.3). NOTE 2 prints where it is:

```python
print(round(noise_control.modal_filter_cut_on(diameter=0.4), 1))          # 505.9 Hz
print(round(noise_control.modal_filter_cut_on(larger_dimension=0.5), 1))  # 343.0 Hz
```

The rectangular form, $0{,}5\,c/H$, is exact: the first mode of a rigid
rectangular duct is a half wavelength across the larger dimension. The
circular one, $0{,}59\,c/d$, is rounded. The exact coefficient is the first
zero of $J_1'$ over $\pi$, which is 0,58607, so Equation (4) sits 0,67 %
high: on the 0,4 m duct of the ISO 11691 sound source that is 505,9 Hz where
[`circular_duct_cut_on`](duct-path.md) gives
502,6 Hz. Three and a half hertz does not matter for choosing a modal filter,
and it is worth knowing which of the two numbers is the physics.

## Standards

ISO 7235:2003 and ISO 11691:1995, read from BS EN ISO 7235:2009 and
BS EN ISO 11691:2009, which endorse them without modification. Implemented:
Equation (1) of both standards with the reverberation-time correction of
ISO 7235 6.3; the octave fold of ISO 11691 Equation (2); ISO 7235 Table 6 and
the three-or-five rule of 6.2.1; ISO 11691 Table 1 and all three columns of
ISO 7235 Table 7, with the coverage factor of 7.9; the scope of ISO 11691 1.1
and 4.5; the open-end transmission loss and reflection coefficient of
Equations (B.3) and (B.4) with the solid angles of Table B.1; the transmission
loss of Equation (6) and the flow-noise sound power of Equation (7); and the
cut-on frequencies of Equations (4) and (5). Checked in the
[conformance report](../../CONFORMANCE.md); the gap Table 6 leaves at 160 Hz
is in the [errata register](../../ERRATA.md). Not implemented: the facility
requirements themselves, the volume flow rate and pressure loss coefficient of
6.5, and ISO 11820, which measures a silencer in situ.

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

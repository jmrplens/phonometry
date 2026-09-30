← [Documentation index](../../README.md)

# Audio-Frequency Induction Loops (IEC 60118-4)

A hearing aid switched to its **telecoil** picks up a magnetic field instead
of sound: the voice of a talker, fed to an amplifier that drives a current
round a loop of wire laid in the floor, reaches the listener without the
reverberation and the noise of the room in between. Two IEC standards divide
the work. **IEC 60118-4** says what field the installed system has to produce,
where, and with how little noise, and how an installer shows that it does.
**IEC 62489-1** says how the manufacturer of each component, the amplifier,
the loop as a load and the neck loop, measures and states what it does. This
guide follows both: the reference level and its units, the field a loop
produces, the loop as the load an amplifier drives, the test signals and the
meter, the verdicts on a room, a refuge and a counter, the overload test of
Amendment 1, and the amplifier and the neck loop.

## 1. The reference and the level (IEC 60118-4 3.1, 4.3, E.2, E.6)

Every level in the standard is referred to a magnetic field strength of
**400 mA/m**, 0 dB: $L = 20\lg(H / 0.4\ \mathrm{A/m})$. The reference is chosen
so that a long-term average of −12 dB, 100 mA/m, gives the hearing aid the same
acoustic output as a sound pressure level of 70 dB at its microphone (4.3),
while 0 dB itself is the maximum field strength of 8.2.7, read with a 1 kHz
sine or the combi signal on the true-RMS meter. The field strength is in amperes per metre because it is proportional to the
current in the loop and falls with distance from the conductor; in air the flux
density is $B = \mu_0 H$, so 400 mA/m is about 0.5 µT (E.6).

A telecoil is a small coil on a ferrite rod, and it responds to the component
of the field along its axis: $20\lg|\cos\theta|$, 3 dB down at 45° and 9.3 dB
down at 70° (E.2, Figure E.6). A telecoil in a hearing aid worn upright is
vertical, which is why every measurement of IEC 60118-4 is made with the
pick-up coil vertical unless the users kneel or lie (8.1), and why the
horizontal loop in the floor is the usual design.

```python
import numpy as np
from phonometry import electroacoustics

print(electroacoustics.field_strength_level([0.4, 0.1]).round(2))    # [  0.   -12.04]
print(electroacoustics.field_strength([-3.0, 3.0]).round(3))         # [0.283 0.565] A/m
print(round(float(electroacoustics.magnetic_flux_density(0.4)) * 1e6, 3))  # 0.503 µT
print(electroacoustics.telecoil_response([45.0, 70.0]).round(2))     # [-3.01 -9.32]
```

The ±3 dB window of 10.2 as amended is printed as "283 mA/m to 566 mA/m":
those are $400/\sqrt{2}$ and $400\sqrt{2}$, a factor of $\sqrt{2}$ read as
3 dB; exactly ±3 dB is 283 mA/m to 565 mA/m. E.6 prints the flux density of
1 A/m as 1.256 µT where $4\pi \times 10^{-7}$ rounds to 1.257 µT, a slip the
[errata register](../../ERRATA.md) records.

## 2. The field of a loop (IEC 60118-4 Annex E, IEC 62489-1 5.4.10)

A current $I$ round a loop of $N$ turns produces a field proportional to $NI$
everywhere. IEC 60118-4 E.1 gives the one closed form it uses, the field at the
centre of a single-turn square loop of side $d$, in its plane:

$$
H = \frac{2\sqrt{2}\,I}{\pi d},
$$

and extends it to a rectangle: "Provided that the sides $d_1$, $d_2$ of a
rectangular loop are not extremely different", $d$ is taken as
$\sqrt{d_1 d_2}$. Everything else about the field is a figure in the
standard. `rectangular_loop_field` computes it instead: each of
the four sides is a straight filament whose Biot-Savart field closes exactly,
so the field at any point, in any component, carries no discretisation. At the
centre of a square it is the E.1 formula to machine precision; for a
rectangle, the $\sqrt{d_1 d_2}$ approximation reads low by
$\sqrt{(d_1^2 + d_2^2)/(2 d_1 d_2)}$, 0.35 dB at an aspect ratio of 1.5.

IEC 62489-1 5.4.10.2 fixes where an amplifier's field is stated: **1.4 m above
the centre of a horizontal square loop** whose resistance and inductance equal
the rated load. `loop_current` inverts the exact on-axis field for the current
a loop needs, and `loop_dimensions` answers 5.4.11 the other way round: the
largest square loop, and loop of aspect ratio 3:1, whose centre reaches
400 mA/m at 1.4 m with the amplifier's current.

```python
current = electroacoustics.loop_current(10.0, 14.0, height_m=1.2)
print(round(current, 2))                      # 5.41 A for 400 mA/m above the centre
x = np.linspace(-8.0, 8.0, 641)               # a traverse across the 10 m side, y = 0
field = electroacoustics.rectangular_loop_field(current, 10.0, 14.0, x, 0.0, 1.2)
level = field.level_db("z")
print(x[np.abs(level) <= 3.0][[0, -1]])       # [-4.75  4.75] m within ±3 dB

print(round(electroacoustics.loop_centre_field(1.0, 10.0, width_m=14.0), 4))  # 0.0761 A/m (E.1)
exact = electroacoustics.rectangular_loop_field(1.0, 10.0, 14.0, 0.0, 0.0, 0.0)
print(round(float(exact.h_z_a_per_m), 4))                                   # 0.0782 A/m

print([round(v, 1) for v in electroacoustics.loop_dimensions(5.0)])                    # [10.3, 10.3] m
print([round(v, 1) for v in electroacoustics.loop_dimensions(5.0, aspect_ratio=3.0)])  # [7.4, 22.1] m

print([round(electroacoustics.loop_current(10.0 * r, 10.0), 2) for r in (1, 1.5, 2, 3, 5)])
# [4.88, 5.63, 6.04, 6.41, 6.64] A: Figure H.1 at a 10 m shorter side
```

Two of the standard's figures are reproduced point for point. The currents of
Figure H.1, for 400 mA/m 1.4 m above the centre of a loop against its shorter
side and aspect ratio, come back within the width of the printed line, about
0.01 A at the 10 m end of each curve. The two curves of Figure E.2 b), the
vertical and horizontal components 1.2 units above a 15 by 10 loop, come back
within about half a decibel across the loop's 10-unit width, which is the
traverse E.1 describes ("the distribution of the vertical component across a
loop"). The figure's own panel a) draws the vertical-field line along the
15-unit length instead, where the vertical component would read about 2 dB
higher near the conductor; the [errata register](../../ERRATA.md)
records it.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_field_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_field.svg" alt="The vertical field strength level at 1.2 m above the floor across a 10 m by 14 m loop, driven with the 5.41 A that gives 400 mA/m above the centre: flat near 0 dB in the middle, rising to about +2.3 dB some 1.2 m inside each conductor, then falling steeply to a null just outside the conductor at plus and minus 5.25 m and recovering to about -5 dB beyond it, with the 0 dB reference and the plus or minus 3 dB band of IEC 60118-4 8.4.3" width="88%"></picture>

*The vertical field across the loop at listening height. Inside, it stays
within ±3 dB out to 4.75 m of the 5 m half-width; just above each conductor
the field turns horizontal and the vertical component a telecoil reads
vanishes, and outside the loop it comes back with the opposite sign. That is
the spill a neighbouring room hears, and the reason the useful volume stops
short of the walls.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

x = np.linspace(-8.0, 8.0, 641)
field = electroacoustics.rectangular_loop_field(current, 10.0, 14.0, x, 0.0, 1.2)
ax = field.plot()
ax.set_ylim(-30.0, 8.0)
plt.show()
```

</details>

## 3. The loop as a load (IEC 62489-1 Annex B, IEC 60118-4 E.3)

The loop is a resistance in series with an inductance (IEC 62489-1 5.4.3.2,
B.2). The resistance is $R = \rho N l / a$ for a conductor of length $l$ and
area $a$, with the resistivity of standard annealed copper, 1/58 Ω·mm²/m at
20 °C and 0.00393 per degree (IEC 60028). The inductance of a rectangle of
round wire is Grover's Formula (58); for $N$ turns it is multiplied by $N^2$,
the perfect coupling Table B.1 assumes. The magnitude of the impedance,
$|Z| = \sqrt{R^2 + (2\pi f L)^2}$, is $\sqrt{2}$ times the resistance at the
corner frequency $R/(2\pi L)$, "1.4 times" in IEC 60118-4 E.3, and the voltage
the amplifier has to deliver for a current $I$ is $U = I|Z|$.

Table B.1 of IEC 62489-1 is the oracle. Its resistances all come out of the
20 °C resistivity with the perimeter of each loop, and four of its six
inductances out of Formula (58) without the term for the flux inside the wire:

| Loop | Size [m] | Turns | Area [mm²] | $R$ printed / computed [Ω] | $L$ printed / computed [µH] | $\|Z\|$ at 2 kHz, 5 kHz [Ω] |
| :--- | :--- | ---: | ---: | :--- | :--- | :--- |
| Neck loop | 0.22 diameter | 10 | 0.5 | 0.24 / 0.238 | 85 / not reproduced | 1.09, 2.67 / 1.09, 2.68 |
| Counter loop | 0.35 × 0.45 | 10 | 0.75 | 0.37 / 0.368 | 189 / 189.4 | 2.41, 5.96 / 2.40, 5.95 |
| Home loop | 3 × 4 | 1 | 1.0 | 0.24 / 0.241 | 22 / 22.2 | 0.37, 0.74 / 0.37, 0.73 |
| Small room | 6 × 8 | 1 | 1.5 | 0.32 / 0.322 | 47 / 47.2 | 0.67, 1.52 / 0.67, 1.51 |
| Typical place of worship | 10 × 20 | 1 | 1.5 | 0.69 / 0.690 | 109 / 109.2 | 1.54, 3.50 / 1.53, 3.49 |
| Large place of worship | 15 × 40 | 1 | 2.5 | 0.76 / 0.759 | 218 / not reproduced | 2.85, 6.89 / 2.84, 6.89 |

The impedances are computed from the printed $R$ and $L$. The counter loop's
resistance needs the 1.6 m its sides give, not the 1.5 m the table prints for
its perimeter, which is an erratum. Table B.1 does not say which formula it
used for the inductance, and no reading of the wire size reaches the neck
loop's 85 µH or the large loop's 218 µH, so those two are not claimed.
`rectangular_loop_inductance` keeps the internal term by default, 2.7 % to
4.2 % more on these four loops, because at audio frequencies the skin depth in copper (2 mm at 1 kHz)
exceeds the radius of every conductor in the table: pass
`internal_inductance=False` to reproduce Table B.1. IEC 60118-4 E.3 offers a
rule of thumb for a single-turn square loop of side $d$ over a square metre,
$L = 8d$ µH, and it reads high: for 1.5 mm² wire Formula (58) gives $6.7d$ µH
for a 5 m square and $7.8d$ µH for a 20 m one.

```python
r = electroacoustics.loop_resistance(60.0, 1.5)                  # typical place of worship
l = electroacoustics.rectangular_loop_inductance(10.0, 20.0, 1.5, internal_inductance=False)
z = electroacoustics.loop_impedance(r, l)
print(round(r, 3), round(l * 1e6, 1))            # 0.69 ohm 109.2 µH
print(round(z.corner_frequency_hz))              # 1005 Hz
print(z.at([2000.0, 5000.0]).round(2))           # [1.54 3.5 ] ohm
print(round(electroacoustics.rectangular_loop_inductance(10.0, 20.0, 1.5) * 1e6, 1))  # 112.2 µH
print(round(electroacoustics.loop_resistance(60.0, 1.5, conductor_temperature_c=40.0), 3))  # 0.744 ohm
```

Above its corner frequency the loop's impedance rises 6 dB per octave, so a
voltage-driven loop loses its treble. The usual cure is a **current-drive
amplifier**, whose output resistance, some ten times the loop's, keeps the
current constant while the impedance varies (E.3); the price is voltage, and
the overload test of section 7 is where it is paid.

## 4. Test signals and the meter (IEC 60118-4 6.1, 6.4, 6.6)

The field strength meter is a sound level meter with a magnetic pick-up coil in
place of the microphone, equalized flat within ±1 dB from 50 Hz to 10 kHz, with
a true-RMS detector and the 125 ms averaging of its "F" mode (6.1.3); the peak
programme meter of 6.1.4 is the alternative, and in case of doubt the true-RMS
reading is definitive (6.1.1). `field_strength_meter` reads a record flat or
A-weighted, the latter for the noise measurements of clause 7 and 10.4.

The **pink noise** of 6.4 is band-limited by third-order Butterworth filters at
75 Hz and 6.5 kHz and has a peak-to-peak to RMS ratio of at least 18 dB, a
crest factor of 4; IEC 62489-1 5.4.8.2 b) asks the same signal for 18 dB
±2 dB. Gaussian noise reaches about 5.5 times its RMS in a minute at 48 kHz,
21 dB peak to peak, which meets the first and fails the second, so
`loop_test_noise` clips at 4 times the RMS and rescales, which meets both.
The **combi signal** of 6.6 and Table 2 interleaves 1 kHz tone bursts of at
least 1 s, with 5 ms ramps, with at least four times as much of that noise
6 dB lower: the sine's peaks sit 3 dB below the noise's, and the amplifier runs
cooler than on a steady sine while the level can still be read on the bursts.

```python
fs = 48000
print(electroacoustics.band_limit_response([100.0, 5000.0]).round(2))  # [-0.71 -0.82] dB
noise = electroacoustics.loop_test_noise(fs, 30.0, seed=7)
print(round(20 * np.log10(np.ptp(noise) / np.sqrt(np.mean(noise**2))), 2))  # 18.06 dB

combi = 0.4 * electroacoustics.combi_signal(fs, cycles=2, seed=7)  # sine bursts at 400 mA/m
reading = electroacoustics.field_strength_meter(combi, fs)
print(round(reading.maximum_db, 2), round(reading.equivalent_db, 2))  # 0.0 -3.98 dB
```

6.4 NOTE 2, and NOTE 3 to 5.4.8.2 of IEC 62489-1, print the theoretical
responses of the band-limiting filters as −0.8 dB at 100 Hz and −0.7 dB at
5 kHz. The two filters give −0.71 dB and −0.82 dB, the other way round; the
±1 dB flatness the note explains holds either way. The clause itself asks for
"at least one-third-order" filters, a slip for the third order its B.2.3,
its own NOTE 2 and IEC 62489-1 all name; both are in the errata register.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_combi_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_combi.svg" alt="The F-weighted true-RMS meter reading of two cycles of the combi signal scaled to 400 mA/m, over 10 seconds: each 1-second sine burst rises to 0 dB within a few hundred milliseconds and holds there, and each 4-second stretch of pink noise settles to about -6 dB with fluctuations of a few tenths of a decibel; the maximum indication, 0.0 dB, is marked with a diamond where it occurs, on the reference line" width="88%"></picture>

*The meter on the combi signal. The bursts read 0 dB, the noise 6 dB less, and
the maximum indication, which 8.2.7 reads, is the sine's; the level of the
whole record is 4 dB down, which is what spares the amplifier.*

<details>
<summary>Show the code for this figure</summary>

```python
ax = reading.plot()
ax.set_ylim(-16.0, 4.0)
plt.show()
```

</details>

## 5. How the measurement goes (IEC 60118-4 clauses 7 to 10)

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_induction_loop_measurement_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_induction_loop_measurement.svg" alt="Three panels and a footer. Left, a room in plan with a perimeter loop fed by an amplifier outside it, a dashed useful volume inside the loop and a grid of nine measurement points; the caption says the points are chosen through the volume at 1.2 m seated and 1.7 m standing with the pick-up coil vertical, and that every point has to be within plus or minus 3 dB of 400 mA/m (8.4.3). Middle, the refuge of Figure 2 a): a source, a reference point, and six points at 0 and plus or minus 45 degrees on arcs of 300 mm and 500 mm, taken at 1.2 m and 1.7 m, with the limits plus or minus 6 dB, 0 dB at one point and never above +8 dB (9.5). Right, the counter of Figure 3: a source behind the counter face, a semicircle of 300 mm radius with a point at its bottom and one 150 mm to either side, at 1.2 m, 1.45 m and 1.7 m, with the same limits as a refuge and the note that the +12 dB of Annex A.4 is not 9.5. The footer lists what every system meets: the frequency response within plus or minus 3 dB of 1 kHz from 100 Hz to 5 kHz (8.3.7), the noise with the system on below -47 dB or no more than 1 dB over the loop off (10.4.7), and the loop voltage at the Table 4 frequency of the overload test within the compliance voltage (10.3.3); and, marked as a recommendation, the background noise with the loop off at a signal-to-noise ratio of 47 dB ideal and 32 dB minimum (7.2)" width="100%"></picture>

1. **The site first, loop off** (7.1). Everything else normally in use is on
   and dimmable lighting half-dimmed; the magnetic background noise is read
   A-weighted at enough points of the intended volume, at 1.2 m for seated and
   1.7 m for standing listeners, and it is worth listening to as well, because
   its spectrum decides how disturbing it is.
2. **Set the level** (8.2). With a 1 kHz sine, or the combi signal, and the
   true-RMS meter, the amplifier's controls are set so that the field reaches
   400 mA/m; with speech or pink noise the target is the reading the
   manufacturer states for 400 mA/m (Table 3 gives −6 dB for pink noise on the
   RMS meter). A warm-up of 10 min comes first, and the AGC's release time is
   waited out after every change of input level.
3. **Survey the field and the response** (8.3, 8.4). The level at the selected
   points of the useful volume, and the frequency response at 100 Hz, 1 kHz and
   5 kHz at least, starting with 5 kHz, where metal in the building shows first.
4. **The noise with the system on** (10.4), all inputs muted, A-weighted at
   the same points as the background noise, so the two can be compared point by
   point.
5. **The overload test** (10.3) at the frequency Table 4 gives for the
   programme, then the commissioning with sound sources in their normal places
   and, where possible, a few hearing-aid users present (10.1).

## 6. The site and the installed system (IEC 60118-4 7.2, 8.3.7, 8.4.3, 10.4.7)

The difference between the 0 dB reference and the A-weighted background noise
is the **reference signal-to-noise ratio** of 7.2. Above 47 dB is the ideal,
for theatres and wherever the aesthetic value of speech matters; 32 dB is the
recommended minimum, and a lower ratio "shall be reported and agreed with the
system operator"; as low as 22 dB may be tolerable for short periods, where the
noise "has no significant undesirable tonal quality or is mostly at low
frequencies". These are recommendations, and `assess_background_noise` classes
the site at its noisiest point without folding the class into a verdict;
`noise_is_tonal=True`, there and in `verify_induction_loop_system`, withholds
the 22 dB relaxation from a noise with an undesirable tonal quality.

The requirements of the installed system are four. The maximum field is
**400 mA/m at one point at least** of the useful volume (8.2.1, 8.2.7), and
every selected point is within **±3 dB** of that specified level (8.4.3); the
frequency response is within **±3 dB of the response at 1 kHz from 100 Hz to
5 kHz** at every point (8.3.7); and the noise with the system switched on is
**below −47 dB** where the site's ratio is above 47 dB, otherwise **no more than
1 dB above the loop-off level** at the same point (10.4.7 as amended, which
was 10.2.7). The two sentences of 10.4.7 say "greater than 47 dB" and "less
than 47 dB", so a ratio of exactly 47 dB falls in neither; the 1 dB rule is
applied there, and the gap is in the errata register.
`verify_induction_loop_system` judges each requirement it is given on every
value it covers, and returns one verdict object.

```python
current = electroacoustics.loop_current(10.0, 20.0, height_m=1.2)   # the typical place of worship
x, y = np.meshgrid([-3.5, 0.0, 3.5], [-8.0, -4.0, 0.0, 4.0, 8.0])     # fifteen seats
levels = np.stack([
    electroacoustics.rectangular_loop_field(current, 10.0, 20.0, x, y, height).level_db("z")
    for height in (1.2, 1.7)
])
first = electroacoustics.verify_induction_loop_system(levels)
print(first.passes, first.failed)                                     # False ('field_strength',)
print(round(first.requirement("field_strength").worst_margin_db, 2))  # -1.41 dB, +4.41 at the corners

levels = levels - 2.0          # turned down 2 dB, so the spread straddles 0 dB
off = [-38.5, -36.0, -40.2, -37.1, -35.4]   # loop off, A-weighted, dB re 400 mA/m
on = [-38.1, -35.6, -39.9, -36.6, -35.0]    # system on, inputs muted
verdict = electroacoustics.verify_induction_loop_system(
    levels,
    frequencies_hz=[100.0, 1000.0, 5000.0],
    response_db=[[-0.4, 0.0, -1.8], [-0.3, 0.0, -2.4], [-0.6, 0.0, -3.4]],
    background_noise_levels_db=off,
    system_noise_levels_db=on,
)
site = verdict.background_noise
print(round(site.reference_signal_to_noise_ratio_db, 1), site.category)  # 35.4 acceptable
print(verdict.passes, verdict.failed)                                    # False ('frequency_response',)
for requirement in verdict.requirements:
    print(requirement.name, round(requirement.worst_margin_db, 2))
# field_strength 0.56 / field_strength_reached 2.41
# frequency_response -0.4 / system_noise 0.5
```

The first verdict is the lesson of section 2 again: with 400 mA/m set above the
centre, the seats near the conductors run 4.4 dB hot, and the cure is to set
the level on the spread, not on one point. Turned down 2 dB, the hottest seat
still reads 2.4 dB above the reference, which is what 8.2.7 asks: the maximum
field reaches 400 mA/m somewhere in the volume. A spread set wholly below the
reference, every seat between −3 dB and −0.1 dB, would pass the window of 8.4.3
and fail 8.2.7. The second fails on the far seat at
5 kHz, 3.4 dB down: the loss to metal of Annex F, which the standard gives no
model for. Its correction is the response the installer measures and
equalizes, and the overload test of section 7 is what checks that the
amplifier can afford the lift.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_verification_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_verification.svg" alt="Two panels. Left, the A-weighted background noise at five points with the loop off, between -40.2 and -35.4 dB re 400 mA/m, against horizontal lines at -47 dB (ideal), -32 dB (recommended minimum) and -22 dB (short periods only); the title reads Reference SNR 35.4 dB: acceptable. Right, the worst margin of each requirement as a bar: field strength +0.56 dB, 400 mA/m reached +2.41 dB and system noise +0.50 dB in green, frequency response -0.40 dB in red; the title reads IEC 60118-4, clause 8: fail" width="100%"></picture>

*The site is acceptable but not ideal, so the system-on noise is judged on the
1 dB rule, which it meets by half a decibel. The field meets its window once
the level is set on the spread; the response does not, at one seat and one
frequency, and that is enough to fail the system.*

<details>
<summary>Show the code for this figure</summary>

```python
fig, (ax_site, ax_verdict) = plt.subplots(1, 2, figsize=(13.5, 5.6))
verdict.background_noise.plot(ax_site)
verdict.plot(ax_verdict)
plt.show()
```

</details>

### 6.1 A refuge, a call point and a counter (clause 9 as amended)

A small system is judged at fixed points instead of over a useful volume.
Amendment 1 rewrites clause 9: six points for a disabled refuge or call point,
along the perpendicular and ±45° at 300 mm and 500 mm from the reference point
(Figure 2 a), or on two rows 424 mm and 700 mm wide for a larger source
(Figure 2 b), at 1.2 m and 1.7 m; three points for a counter, on a semicircle
of 300 mm radius at its bottom and 150 mm either side (Figure 3), at 1.2 m,
1.45 m and 1.7 m, the middle height because a poorly designed installation may
have a null there. At every point the level is within **±6 dB** of 400 mA/m
and meets 8.3.7, at one point at least it reaches **0 dB**, and nowhere where
people are expected to stand, which Figure 3 puts outside the semicircle of
points, is it **above +8 dB** (9.5).

```python
points = electroacoustics.small_volume_measurement_points("counter")
print(points.shape, points[0, :, :2].round(3).tolist())
# (3, 3, 3) [[-0.15, 0.26], [0.0, 0.3], [0.15, 0.26]]  x, y in m; z the height

counter = electroacoustics.verify_small_volume_system(
    [[5.1, 4.2, 5.3], [2.0, 1.1, 2.2], [-2.9, -3.8, -2.7]],   # rows at 1.2 m, 1.45 m, 1.7 m
    layout="counter",
    standing_area_levels_db=[6.5, 7.9, 9.2],   # the standing area beside the semicircle
)
print(counter.passes, counter.failed)                                    # False ('standing_area',)
print(round(counter.requirement("standing_area").worst_margin_db, 2))    # -1.2 dB
```

The rows of `field_strength_levels_db` follow the heights of
`small_volume_measurement_points`, lowest first, so the counter above is
strongest at 1.2 m and weakest at 1.7 m. The informative Annex A.4 allows "up to, but not greater than,
+12 dB" at 1.45 m for a counter and calls the counter's requirement less
stringent than a refuge's; 9.5 applies the same limits to both at every
height, and 9.5 is what is applied. Amendment 1 also corrects the key of
Figure 2 a), whose outer radius the 2014 print gave as 200 mm.

By contract, a useful magnetic field volume with representative points of the
installer's choosing may replace the points of 9.2 or 9.3 (9.4). The same
limits of 9.5 hold at every point, and as a minimum the volume has to meet
them at one position at least at each height of the clause it replaces:
1.2 m and 1.7 m for a refuge, 1.2 m, 1.45 m and 1.7 m for a counter. The
layouts `"refuge_useful_volume"` and `"counter_useful_volume"` take the height
of each point, and refuse a set of points that leaves one of those heights
out.

```python
volume = electroacoustics.verify_small_volume_system(
    [4.6, 3.9, 1.8, 0.7, -2.4, -3.1],
    layout="counter_useful_volume",
    heights_m=[1.2, 1.2, 1.45, 1.45, 1.7, 1.7],
)
print(volume.passes)                  # True
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_counter_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_counter.svg" alt="Two panels. Left, the twelve values the standing-area requirement judges, the nine measurement points of the counter between -3.8 and +5.3 dB and the three survey points at 6.5, 7.9 and 9.2 dB, against the +8 dB upper limit, with the last point marked as failing; the title reads Standing area at most +8 dB (9.5): fail. Right, the worst margin of the three requirements of 9.5: the plus or minus 6 dB range +0.7 dB and 400 mA/m reached +5.3 dB in green, the standing area -1.2 dB in red; the title reads IEC 60118-4, clause 9: fail" width="100%"></picture>

*A counter loop that meets its window at all nine points and still fails,
because a customer standing beside the semicircle, close to the counter face,
reads 9.2 dB. A vertical loop in the counter face makes a strong field close
to it by construction, which is what the +8 dB cap and 9.5 NOTE 1 are about.*

<details>
<summary>Show the code for this figure</summary>

```python
fig, (ax_area, ax_verdict) = plt.subplots(1, 2, figsize=(13.5, 5.6))
counter.requirement("standing_area").plot(ax_area)
counter.plot(ax_verdict)
plt.show()
```

</details>

## 7. Commissioning and the overload test (IEC 60118-4 10.2, 10.3 as amended)

Amendment 1 replaces the 1.6 kHz overload test with one tied to the programme.
With a 1 kHz sine set **7 dB below** the field required at a point, the voltage
across the loop is measured and the frequency raised at the same input until
that voltage **doubles**, or the frequency of **Table 4** is reached, whichever
is the higher frequency (10.3.2), and no clipping may appear at the frequency
of Table 4 and that level (10.3.3):

| Programme | Upper limit of the maximum power bandwidth | Test frequency |
| :--- | ---: | ---: |
| Speech for transient use, for example small-volume systems | 1.25 kHz | 2.5 kHz |
| Speech (default) | 1.6 kHz | 3.15 kHz |
| Music | 2.0 kHz | 4.0 kHz |

The test frequency is about twice the upper limit because a sine at the limit
itself would draw an unrealistically high current from the power supply; the
reduced level at twice the frequency loads it the way real programme does
(10.3.1). Of the three ways the amendment lists to detect clipping, the second
compares the loop voltage with the amplifier's **compliance voltage** of
IEC 62489-1, and that one is computable from the loop's impedance and the
current the amplifier puts into it. The verdict is taken at the Table 4
frequency, where 10.3.3 puts the requirement; when the voltage doubles only
above that frequency, the sweep runs on to the doubling, and the rest of it is
drawn and its highest voltage kept as `max_voltage_v`, but not judged. Here
the amplifier lifts its current above 1 kHz to make up the metal loss of
section 6:

```python
lift = electroacoustics.amplifier_frequency_response(
    [100.0, 1000.0, 2000.0, 3150.0, 4000.0, 5000.0, 8000.0],
    [2.0, 2.0, 2.4, 2.9, 3.2, 3.5, 3.6],       # output current, A
)
print(lift.response_db.round(2))                # [0.   0.   1.58 3.23 4.08 4.86 5.11] dB re 1 kHz
speech = electroacoustics.verify_amplifier_overload(current, z, 11.0, current_response=lift)
print(round(speech.test_current_a, 2), round(speech.doubling_frequency_hz))  # 2.65 A 2091 Hz
print(round(speech.end_frequency_hz), round(speech.test_frequency_voltage_v, 2), speech.passes)  # 3150 8.71 True
music = electroacoustics.verify_amplifier_overload(
    current, z, 11.0, programme="music", current_response=lift
)
print(round(music.test_frequency_voltage_v, 2), round(music.headroom_db, 2), music.passes)  # 11.99 -0.75 False
```

The voltage doubles at 2.1 kHz, below the Table 4 frequency in both cases, so
the sweep runs on to 3.15 kHz for speech and to 4 kHz for music. The amplifier
that serves speech with 2 dB to spare clips on music: at 4 kHz the loop wants
12 V and the amplifier has 11 V. That is the trade the equalization of section
6 made, and it is why a correction for metal loss is decided together with the
amplifier and not after it.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_overload_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_overload.svg" alt="Two panels. Left, the magnitude of the impedance of the 10 m by 20 m loop from 50 Hz to 10 kHz, flat at the 0.69 ohm resistance at low frequencies, 0.98 ohm at the 1005 Hz corner frequency marked by a dotted line, and rising 6 dB per octave to about 6.9 ohm at 10 kHz. Right, the RMS loop voltage along the overload sweep for music, from 2.6 V at 1 kHz through the doubling at 2.1 kHz to 12.0 V at the 4 kHz frequency of Table 4, marked with a red diamond as the voltage 10.3.3 judges, crossing the 11 V compliance voltage just below 4 kHz; the title reads Overload test, 2000 Hz programme limit: fail" width="100%"></picture>

*The loop as a load, and the overload sweep for music. The rise of the
impedance above the corner and the lift of the current multiply, and the
crossing with the compliance voltage lies just inside the sweep.*

<details>
<summary>Show the code for this figure</summary>

```python
fig, (ax_z, ax_sweep) = plt.subplots(1, 2, figsize=(13.5, 5.6))
z.plot(ax_z)
music.plot(ax_sweep)
plt.show()
```

</details>

## 8. The amplifier (IEC 62489-1 clause 5)

IEC 62489-1 lists what an amplifier's specification states. The rated
conditions (5.4.1 to 5.4.6) are declared, not measured; standard measuring
conditions put the output current 10 dB below the rated one (5.2.2). The
measured characteristics that are computations are these:

- **Maximum (distortion-limited) output current** (5.4.7): from standard
  measuring conditions the 1 kHz load current is raised until the total
  harmonic distortion across the resistive part of the load reaches the rated
  value, and the current is the total voltage across that resistance over its
  value. It has to be deliverable for at least 10 s, a condition on the
  measurement rather than a computation.
- **Compliance voltage** (5.4.8): the maximum positive-going and negative-going
  peak voltages across the rated load, over at least 60 s of the specified
  pink noise with the AGC fully in operation, averaged and divided by
  $\sqrt{2}$: the RMS voltage of the sine with the same peaks.
- **Noise** (5.4.9): the equivalent input noise voltage
  $U_\mathrm{n} = U I_\mathrm{n} / I$, the 1 kHz input that gives the same
  current as the noise, or the signal-to-noise ratio
  $S = 10\lg(I_\mathrm{r}^2 / I_\mathrm{n}^2)$ dB.
- **Frequency response** (5.4.12): the load current at one-third-octave
  centres from at least 50 Hz to 8 kHz, 0 dB at 1 kHz.
- **Automatic gain control** (5.4.13): the steady-state output current
  against the source e.m.f.; Amendment 1 adds the recommendation of an input
  range of at least **32 dB for an output change of at most 3 dB** (5.4.13.4).
- **Quadrature phase error** (5.4.14): two adjacent loops fed about 90° apart
  make a rotating field instead of nulls; the characteristic is the maximum
  deviation from 90° over 100 Hz to 5 kHz.

```python
steps = electroacoustics.maximum_output_current(
    [2.0, 3.0, 4.0, 4.5, 5.0],            # V across the 0.69 ohm of the rated load
    [0.05, 0.08, 0.3, 1.2, 4.0],          # THD there, %
    load_resistance_ohm=0.69,
    rated_thd_percent=1.0,
)
print(round(steps.maximum_current_a, 2))  # 6.36 A where the THD reaches 1 %

load = np.clip(4.5 * electroacoustics.loop_test_noise(fs, 60.0, seed=3), -14.0, 14.0)
print(round(electroacoustics.compliance_voltage(load), 2))    # 9.9 V: clipping at ±14 V
print(round(electroacoustics.equivalent_input_noise_voltage(0.1, 1.6, 0.00032) * 1e6, 1))  # 20.0 µV
print(round(electroacoustics.amplifier_signal_to_noise_ratio(5.0, 0.00032), 1))            # 83.9 dB

emf = np.arange(-60.0, 1.0, 5.0)                                   # source e.m.f., dB
output = np.where(emf < -40.0, emf + 30.0, -10.0 + 2.5 * (emf + 40.0) / 40.0)
agc = electroacoustics.agc_characteristic(emf, output)
print(round(agc.agc_range_db, 1), agc.recommended_range_db)        # 40.5 32.0 dB

f = np.array([100.0, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000]
             + [1250, 1600, 2000, 2500, 3150, 4000, 5000])
phase = 90.0 - 4.0 * np.log2(f / 700.0) ** 2 / 3.0                 # degrees between the currents
quadrature = electroacoustics.quadrature_phase_error(f, phase)
print(round(quadrature.max_deviation_deg, 2), quadrature.max_deviation_frequency_hz)  # 10.73 5000.0
print(round(quadrature.level_increase_db, 2), round(quadrature.level_decrease_db, 2))  # 1.48 -1.79 dB
```

A deviation $\delta$ from 90° leaves an in-phase component $\sin\delta$ of one
field against the other, which raises the level by $20\lg(1 + \sin\delta)$
where the two add and lowers it by $20\lg(1 - \sin\delta)$ where they
subtract. 5.4.14.1 gives the example of 85°, an in-phase part of 0.087, and
prints the change as "increased or decreased by 0.72 dB"; the rise is 0.72 dB,
the fall 0.79 dB.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_amplifier_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_amplifier.svg" alt="Two panels. Left, the output current level against the source e.m.f. from -60 dB to 0 dB: a slope of one to one up to -40 dB, where the output is -10 dB re the rated maximum current, then a gentle rise to -7.5 dB at 0 dB, with the span from -40.5 dB to 0 dB shaded as the AGC range of 40.5 dB against the 32 dB recommended and a dashed line, in the legend, 3 dB below the highest output. Right, the deviation from 90 degrees between the currents of two loops at the one-third octaves from 100 Hz to 5 kHz, zero near 700 Hz and rising to about 10.5 degrees at 100 Hz and 10.7 degrees at 5 kHz, with the maximum marked at 5000 Hz and the band judged, 100 Hz to 5 kHz, shaded" width="100%"></picture>

*The amplifier's AGC holds its output within 3 dB over 40.5 dB of input, 8.5 dB
more than 5.4.13.4 recommends; the quadrature network is within 11° of
quadrature over the speech band, a rise of 1.5 dB and a fall of 1.8 dB where
the two loops' fields meet.*

<details>
<summary>Show the code for this figure</summary>

```python
fig, (ax_agc, ax_phase) = plt.subplots(1, 2, figsize=(13.5, 5.6))
agc.plot(ax_agc)
quadrature.plot(ax_phase)
plt.show()
```

</details>

## 9. The neck loop (IEC 62489-1 clause 9 and the draft Amendment 2)

A neck loop is a small loop, often about 230 mm across, worn round the neck and
fed from a phone, a music player or a larger piece of equipment. Clause 9,
added by Amendment 1, specifies it on the non-metallic jig of Annex E, with the
field measured at the telecoil position by a small inductor about 3 mm by
10 mm, the size of a behind-the-ear telecoil: the input voltage that produces
400 mA/m at 1 kHz (9.1), the smallest magnitude of the input impedance over
100 Hz to 5 kHz rounded to the nearest ohm (9.2.1), and the frequency response,
stated in text as the frequencies where it differs from the one at 1 kHz by
3 dB (9.3.3). A passive loop is linear, so the voltage for 400 mA/m follows
from a level measured at any voltage.

The draft Amendment 2 (prEN 62489-1:2010/prA2:2017, a draft for comment and
cited as one) replaces Annex D with two example specifications: **type 1**,
"Suitable for audio sources powered by two primary 1,5 V cells and higher
voltage supplies", with a DC resistance of 32 Ω ±5 %, and **type 2**, "Neck
loops with transformer or amplifier", with an input DC resistance of at least
32 Ω, both reaching 400 mA/m on the jig with **at most 1.06 V** at the input.

```python
f = np.array([100.0, 200, 500, 1000, 2000, 5000, 8000, 10000])
z_in = np.abs(32.2 + 2j * np.pi * f * 0.53e-3)     # 32.2 ohm and 0.53 mH, about 25 turns
level = -6.0 + 20 * np.log10(z_in[3] / z_in)       # -6 dB at 1 kHz with 0.5 V applied
neck = electroacoustics.neck_loop_characteristics(f, level, z_in, input_voltage_v=0.5)
print(round(neck.reference_input_voltage_v, 3), neck.minimum_impedance_ohm)  # 0.998 V 32.0 ohm
print([round(v) for v in neck.frequencies_3db_hz])                           # [9723] Hz
draft = electroacoustics.verify_neck_loop(32.4, neck.reference_input_voltage_v, neck_loop_type=1)
print(draft.passes, draft.resistance_passes, draft.voltage_passes)           # True True True
```

The draft's Table D.1, the field a type 1 loop reaches from a 3 V and a 9 V
battery, rests on a model of the source it does not give, and is not
reproduced.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_neck_loop_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/induction_loop_neck_loop.svg" alt="Two panels. Left, the neck loop's frequency response on the jig relative to 1 kHz, flat within 0.05 dB from 100 Hz to 1 kHz, -1.0 dB at 5 kHz and -3.1 dB at 10 kHz, inside a shaded plus or minus 3 dB band, with the -3 dB frequency of 9.7 kHz marked by a dotted line. Right, the DC resistance of 32.4 ohm as 96 % of the 33.6 ohm upper limit of type 1, with that upper limit dashed and the 30.4 ohm lower limit dotted over the bar, and the 0.998 V input for 400 mA/m as 94 % of the 1.06 V limit dashed over its own bar, both bars green; the title reads Neck loop, draft type 1: pass" width="100%"></picture>

*The loop's inductance, not its field, sets the response of a voltage-driven
neck loop: 0.53 mH against 32 Ω puts the corner near 9.7 kHz, well above the
5 kHz of the system requirements.*

<details>
<summary>Show the code for this figure</summary>

```python
fig, (ax_response, ax_verdict) = plt.subplots(1, 2, figsize=(13.5, 5.6))
neck.plot(ax_response)
draft.plot(ax_verdict)
plt.show()
```

</details>

## What this guide covers

**Covered.** IEC 60118-4:2014 with its Amendment 1:2017: the 400 mA/m reference and its
levels (3.1, 4.3), the flux density and the telecoil's cosine law (E.6, E.2),
the true-RMS meter flat or A-weighted (6.1.3), the band-limited pink noise with
its crest factor (6.4) and the combi signal (6.6, Table 2), the background
noise classes of 7.2, the verdict on a system over its useful magnetic field
volume (8.2.7, 8.3.7, 8.4.3, 10.4.7), the measurement points and the verdict of
a refuge, call point or counter as the amendment writes clause 9, at the points
of Figures 2 and 3 or of a useful volume that covers their heights (9.4, 9.5),
and the overload test of 10.3 with Table 4, judged on the compliance voltage
at the Table 4 frequency (10.3.3). The loop's field by Biot-Savart at any
point, which reproduces the centre formula of E.1 and the curves of Figure
E.2 b), and the current and loop size of IEC 62489-1 5.4.10 and 5.4.11, which
reproduce the currents of Figure H.1. The loop as a load (IEC 62489-1 Annex
B): the resistance with the IEC 60028 resistivity and the inductance by
Grover's Formula (58), which reproduce Table B.1 as shown. The amplifier's
maximum output current, compliance voltage, noise, frequency response, AGC
range and quadrature phase error (5.4.7, 5.4.8, 5.4.9, 5.4.12, 5.4.13,
5.4.14), and the neck loop's characteristics (clause 9) with the two types of
the draft Amendment 2, cited as a draft.

**Not covered.** The effect of metal in the building (Annex F) has no model in the standard and
none here: it is the frequency response the installer measures. The peak
programme meter of 6.1.4, the speech signals of 6.3 (ISTS, ITU-T P.50) and the
subjective commissioning of 10.1 are not computations. The loop listener and
assistive listening device of IEC 62489-1 Annex F, and the monitoring devices,
are specified by single values to be met; the draft's Table D.1 rests on a
source model it does not give. The inductances of Table B.1's neck loop and
large loop are not reproduced by any formula tried. The field patterns of
Figures E.3 to E.5 and A.1 are of the kind `rectangular_loop_field` computes
and are not checked point by point. The 10 s for which 5.4.7 asks the maximum
current to be held is a condition on the measurement. The electromagnetic
exposure of IEC 62489-2 is outside this library.

## See also

- [Electroacoustics](electroacoustics.md):
  the IEC 60268-3 distortion measurements and the H1/H2 frequency-response
  estimators behind a measured amplifier response.
- [Microphone Characterisation (IEC 60268-4)](microphones.md):
  the microphone that feeds the loop amplifier, and why a directional one is
  chosen for it.
- [Speech Transmission Index (STI)](../../perception/speech/speech-transmission.md):
  the room the loop bypasses, measured as a transmission index.
- [Frequency Weighting (A, C, Z)](../../signals/levels/weighting.md): the
  A-weighting of IEC 61672-1 that the noise measurements of clause 7 and 10.4
  use.
- API reference: [`electroacoustics.induction_loop`](https://jmrplens.github.io/phonometry/reference/api/electroacoustics/induction-loop/)
  and [`electroacoustics.induction_loop_components`](https://jmrplens.github.io/phonometry/reference/api/electroacoustics/induction-loop-components/).

## References

- Grover, F. W. (1946). *Inductance calculations: Working formulas and
  tables*. D. Van Nostrand. Formula (58), the inductance of a rectangle of
  round wire (pp. 60-61; read in the 1973 Instrument Society of America
  edition), which without its internal term reproduces four of the six
  inductances of Table B.1 of IEC 62489-1.

## Standards

IEC 60118-4:2014, *Electroacoustics – Hearing aids – Part 4: Induction-loop
systems for hearing aid purposes – System performance requirements*, read in
BS EN 60118-4:2015: the reference magnetic field strength (3.1), the meters and
test signals (6.1, 6.4, 6.6, Table 2), the magnetic background noise (7.2), the
maximum field (8.2.7), the frequency response and the useful magnetic field
volume (8.3.7, 8.4.3), Annex E (E.1, Figure E.2, E.2, E.3, E.6) and Figure
H.1. IEC 60118-4:2014/AMD1:2017, read in UNE-EN IEC 60118-4:2016/A1:2018:
clauses 9 and 10 as replaced, with Figures 2 and 3, 9.4, 9.5, 10.2, 10.3 with
Table 4 and 10.4.7. IEC 62489-1:2010+AMD1:2014,
*Audio-frequency induction-loop systems for assisted hearing – Part 1: Methods
of measuring and specifying the performance of system components*, read in
BS EN 62489-1:2010+A1:2015: the amplifier (5.4.7 to 5.4.14), the loop as a load
(Annex B, Table B.1) and the neck loop (clause 9, Annex E). E DIN EN
62489-1/A2:2017-10 (prEN 62489-1:2010/prA2:2017), a draft cited as one: the two
neck-loop types of its Annex D. IEC 60028:1925, *International standard of
resistance for copper*: the resistivity of standard annealed copper and its
temperature coefficient (clause I).

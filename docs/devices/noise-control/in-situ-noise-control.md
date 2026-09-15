← [Documentation index](../../README.md)

# Silencers, screens and barriers in situ (ISO 11820, ISO 11821, ISO 10847)

A laboratory measurement of a noise control device answers one question: what is
this product worth, under conditions chosen so that two products can be
compared. It is the right question when there is a catalogue to write. It is the
wrong one when the silencer is already welded into the duct, the screen has been
standing between the press and the bench for a year, and the barrier was built
before anyone thought of measuring it. These three standards ask the other
question. Each of them measures a device where it already stands, in the
installation it belongs to, with whatever is around it.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/in_situ_noise_control_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/in_situ_noise_control.svg" alt="Three panels: the decibels three standards remove from a measured level against the margin over the background, the four microphone distances of a screen measurement against the screen height, and the reference microphone height of a barrier measurement against the distance from the source to the barrier" width="88%"></picture>

## What in situ costs, and what it buys

The laboratory buys a controlled environment and a substitution measurement:
ISO 7235 runs a source into a test duct with the silencer in place, then with a
straight replacement section of the same length, so the two runs differ by the
silencer alone. In situ neither is available. What is left is the pair of levels
the installation allows, the ratio of the two measurement areas and the
difference of the two field corrections, which is Equation (19) of ISO 11820:
`D_ts = D_tps + 10 lg(S_2/S_1) + K_2 - K_1`.

```python
from phonometry import noise_control

bands = [125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]
source = [98.0, 99.0, 97.0, 95.0, 92.0, 88.0]     # dB, in the duct
receiver = [72.0, 68.0, 60.0, 54.0, 50.0, 49.0]   # dB, in the room it feeds

res = noise_control.in_situ_transmission_loss(
    source, receiver,
    source_area_m2=0.9,      # the duct cross-section
    receiver_area_m2=10.8,   # a quarter of the room absorption at 500 Hz
    frequencies=bands, case=2,
)
print(res.loss_db.round(1))        # [15.2 20.2 26.2 30.2 31.2 28.2] dB
print(res.area_term_db.round(1))   # [-10.8 -10.8 -10.8 -10.8 -10.8 -10.8] dB
```

The area term is negative and that is not a mistake: a duct of 0,9 m² discharging
into a room whose quarter-absorption is 10,8 m² spreads the same power over
twelve times the area, and subtracting that is what stops the room being credited
to the silencer. The term comes back once per band, because the area of a room
is not one number either.

## The twenty installations

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_silencer_in_situ_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_silencer_in_situ.svg" alt="Section through a duct run with the silencer in place, the two measurement surfaces marked as dashed planes with their microphone positions, and the upstream and downstream distances" width="88%"></picture>

**How the measurement goes.** Choose the installation from Figure 1 and read off
which area rule each side takes. Place the source-side surface one and a half
equivalent diameters upstream and the receiver-side one at the distance Equation
(16) gives, or agree on one when that expression falls to zero. Measure the mean
level on each surface, take the extraneous sound off by the energy route where
the sources can be switched, record the temperature on both sides, and measure
the flow: the pressure loss and a velocity profile uniform within 10 %.

A silencer sits between two of four things: a duct, a room with a diffuse field,
a room without one, and open space. Sixteen pairs are transmission measurements
and four more are insertion measurements, and Figure 1 draws all twenty.
`installation_case` carries the area rule clause 9 gives each side, and the two
loss functions refuse a case that belongs to the other quantity. The room area
itself comes from the reverberation time through Equations (6), (10) and (12),
as a quarter of the Sabine equivalent absorption area, and so moves from band to
band with it: `reverberant_surface_area_m2` returns one area per band, and both
loss functions take each area and the field correction as one value or as one
per band.

```python
area = noise_control.reverberant_surface_area_m2(320.0, [1.6, 1.4, 1.2, 1.1, 1.0, 0.9])
res = noise_control.in_situ_transmission_loss(
    source, receiver, source_area_m2=0.9, receiver_area_m2=area,
    frequencies=bands, case=2,
)
print(res.area_term_db.round(1))   # [ -9.6 -10.1 -10.8 -11.2 -11.6 -12.1] dB
print(res.loss_db.round(1))        # [16.4 20.9 26.2 29.8 30.4 26.9] dB
```

A silencer is not measured until the flow is measured too. Clause 9 is here in
full: the total pressure loss of Equation (13), the static difference behind a
change of area of Equation (14), the velocity pressure and the velocity it stands
for, the gas density of Equation (29) and the velocity inside the silencer of
Equation (31), which is the one the regenerated noise answers to.

## The screen you can take away

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_screen_in_situ_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_screen_in_situ.svg" alt="Section through a workshop with the screen, the four microphone distances behind it and the one-metre floor that merges the two nearest ones" width="88%"></picture>

**How the measurement goes.** Microphones on the perpendicular line at a
quarter, a half, once and twice the height, pushed out to 1 m where they fall
inside it, at the operator height. Run with the screen, wheel it away without
touching anything else, run again. Background with the machine off at the same
positions: nothing to correct over 10 dB, the boxed formula between 6 dB and
10 dB, and a refusal under 6 dB.

ISO 11821 has the one thing the other two lack: the device can be removed for a
run. `screen_attenuation` is the difference between the two runs, and the
A-weighted pair of 5.9 is refused with an artificial source, because then the
spectrum weighted is the loudspeaker's. An artificial source has its own test to
pass first, the twelve-position directivity index of definition 3.10 with the
8 dB limit of 5.2.2. 7.4 c) reports the attenuation and its A-weighted value to
the nearest whole decibel: `rounded()` and `rounded_a_weighted()` give them that
way, with an exact half going to the even decibel, while `attenuation_db` keeps
the unrounded difference.

```python
print(noise_control.microphone_distances_m(3.0))   # [1.  1.5 3.  6. ] m
```

A quarter, a half, once and twice the screen height, never closer than 1 m, so
under 4 m the quarter-height position is held out to the floor and under 2 m the
half-height one joins it, which is the only case where two positions coincide. NOTE 2 reads the
spread: the smallest attenuation at the most remote position, the largest at the
nearest, which is why all four are asked for rather than an average.

## The barrier that was built years ago

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_barrier_in_situ_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_barrier_in_situ.svg" alt="Two sections of the same site, before and after the barrier, each with the reference microphone above the top edge and the receiver position" width="88%"></picture>

**How the measurement goes.** Fix the receiver and reference positions first and
keep them for both campaigns. Reference microphone at least 1,5 m above the top
edge on a vertical plane through it, which 7.2.2 states with "shall", and higher
where the source region comes closer than 15 m and the elevation rule of the
NOTE asks for more: the NOTE only ever raises it, so a 3 m barrier 5 m from the
source keeps 4,5 m although its 10 degrees are reached at 4,34 m. Record the wind component, the temperature and
the cloud cover for every run, stop above 5 m/s, repeat at least three times,
and check before the second campaign that the weather still matches within
2 m/s and 10 °C.

The direct method of 8.2.1 needs the site before the barrier was built and
normalises the source with a reference microphone above the top edge, so that a
source that ran differently on the second day does not read as barrier
performance.

```python
from phonometry import environment

res = environment.measured_insertion_loss_direct(
    [76.0, 74.0, 71.0, 67.0, 62.0, 56.0],   # reference, before
    [78.0, 76.0, 73.0, 69.0, 64.0, 58.0],   # reference, after
    [63.0, 61.0, 58.0, 54.0, 49.0, 43.0],   # receiver, before
    [58.0, 53.0, 47.0, 41.0, 35.0, 29.0],   # receiver, after
    frequencies=bands,
)
print(res.insertion_loss_db)   # [ 7. 10. 13. 15. 16. 16.] dB
```

The source was 2 dB louder on the second day in every band and the answer does
not contain those 2 dB. The indirect method of 8.2.2 borrows the "before"
campaign from an equivalent site, which makes it an estimate, and each campaign
carries its own receiver correction: 0 dB in a hemi free field, 6 dB against a
facade.

The weather is part of the measurement. `wind_class` is Table 1, with a downwind
class and a calm one over any distance and an upwind class over short distances
alone; `is_short_distance` is the geometry test of 6.3.1 that decides whether
that class exists at all, and the two campaigns can disagree about it. Past 5 m/s
no measurement is made, the two campaigns must agree within 2 m/s and 10 °C, and
the cloud cover is recorded in the four classes of Table 2.

## One correction, three standards, three answers

ISO 11820 prints a stepped table, positive, to be subtracted, and refuses under
3 dB. ISO 10847 prints a stepped table, negative, to be added, and refuses under
4 dB. ISO 11821 prints no table and boxes the energy subtraction, correcting only
between 6 dB and 10 dB of margin.

```python
print(noise_control.silencer_background_correction_db([9.0]))   # [0.5] dB off
print(environment.barrier_background_correction_db([9.0]))      # [-1.] dB added
print(round(80.0 - noise_control.background_corrected_level_db(
    [80.0], [71.0])[0], 2))                                     # 0.58 dB off
```

Three standards, one margin of 9 dB, three answers. They are three
implementations for that reason, and a conformance check holds them against each
other at the margin where they part. ISO 11820 offers a second route for
switchable extraneous sources, the energy subtraction of Equations (17) and (18),
capped at 3 dB; past the cap the quantity is not determined and only the
inequality of clause 4 may be stated. The cap is judged on the margin, where
Table 1 draws it: a margin of exactly 3 dB takes off 3,02 dB, the printed 3 dB
unrounded, and still determines the level.

## What this guide covers

Implemented: the whole arithmetic of ISO 11820, from the level differences of
Equations (1) to (3) to the flow quantities of Equations (27) to (31), with the
twenty installations of Figure 1; the attenuation, background window, directivity
test, microphone geometry, impulse rule and reporting rounding of ISO 11821; and the direct and
indirect methods, background table, wind and cloud classes, short-distance test,
reference microphone height and hemi-free-field clearance of ISO 10847. Two
defects in the print of ISO 10847 are recorded in the
[errata register](../../ERRATA.md), along with a note that the two stepped
background tables are a difference and not an erratum. Not implemented: the
prediction of a barrier insertion loss or a silencer attenuation, which are
separate pages; the instrument and windscreen requirements; the judgement of site
equivalence; and the report templates.

## See also

- [Enclosures and cabins measured](enclosure-cabin-insulation.md): the same
  in-situ habit of mind applied to a box around a machine and a cabin around an
  operator.
- [Measuring a silencer](silencer-measurement.md): the laboratory method of
  ISO 7235, with the test duct and the substitution run ISO 11820 does without.
- [Industrial noise control](noise-control.md): the predicted insertion loss of a
  screen or an enclosure, which these standards measure rather than compute.
- [Outdoor sound propagation](../../environment/propagation/outdoor-propagation.md):
  the ISO 9613-2 barrier attenuation term a prediction computes for the barrier
  ISO 10847 measures.
- [Errata in published sources](../../ERRATA.md): an upwind wind class printed
  with a positive lower bound, and one prime asked to mean two different things.
- API reference: [`noise_control.silencer_in_situ`](https://jmrplens.github.io/phonometry/reference/api/noise_control/silencer-in-situ/),
  [`noise_control.screen_in_situ`](https://jmrplens.github.io/phonometry/reference/api/noise_control/screen-in-situ/)
  and [`environment.propagation.barrier_in_situ`](https://jmrplens.github.io/phonometry/reference/api/environment/barrier-in-situ/).

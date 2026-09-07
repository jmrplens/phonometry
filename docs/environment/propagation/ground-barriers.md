← [Documentation index](../../README.md)

# Spherical ground effect and advanced barriers (Attenborough / Salomons / Bies)

The [ISO 9613-2 general method](outdoor-propagation.md) folds the ground and
barrier terms into tabulated, energy-based corrections. This page covers the
underlying wave acoustics in `phonometry.environment.propagation.ground_barriers`: the
**spherical-wave reflection coefficient** of a finite-impedance ground
(Weyl-Van der Pol) and the **wave-theoretic diffraction** of a screen, both in
a homogeneous (non-refracting, non-turbulent) atmosphere. These are the physical
core of the Nord2000 / CNOSSOS ground and barrier models, and they show the
frequency-dependent interference structure the octave-band $A_\mathrm{gr}$/$D_z$
terms smooth away.

## 1. Spherical-wave ground effect (Weyl-Van der Pol)

The sound field of a point source above a locally reacting ground is the sum of
a direct wave and a reflected wave weighted by the **spherical-wave reflection
coefficient** $Q$ (Attenborough Eq. 2.40a; Salomons Eq. 3.2):

$$
p = \frac{e^{ikR_1}}{4\pi R_1} + Q\,\frac{e^{ikR_2}}{4\pi R_2},
$$

with $R_1$ the source-receiver distance and $R_2$ the image-source distance.
The coefficient (Attenborough Eq. 2.40c; Salomons Eq. D.58) corrects the
plane-wave coefficient $R_\mathrm{p}$ for the curvature of the wavefront:

$$
Q = R_\mathrm{p} + (1 - R_\mathrm{p})\,F(w), \qquad
R_\mathrm{p} = \frac{Z\cos\theta - 1}{Z\cos\theta + 1},
$$

$$
F(w) = 1 + i\sqrt{\pi}\,w\,e^{-w^2}\operatorname{erfc}(-iw), \qquad
w = \sqrt{\tfrac{i k R_2}{2}}\left(\cos\theta + \tfrac{1}{Z}\right).
$$

Here $Z$ is the ground surface impedance normalized by $\rho c$, $\theta$ is
the angle of incidence from the ground normal
($\cos\theta = (h_\mathrm{s} + h_\mathrm{r})/R_2$), and the boundary-loss factor $F(w)$ is
written through the scaled complementary error function
$e^{-w^2}\operatorname{erfc}(-iw)$, i.e. the Faddeeva function
`scipy.special.wofz`. The second term of $Q$ is the *ground wave* that keeps
the field finite at grazing incidence, where $R_\mathrm{p} \to -1$ and a plane-wave
model would predict silence
(Salomons Eq. D.59, D.60, D.57).

The relative sound level (the *excess attenuation*, dB re free field) is
(Salomons Eq. 3.4):

$$
\Delta L = 20\log_{10}\!\left|\,1 + Q\,\frac{R_1}{R_2}\,e^{i k (R_2 - R_1)}\,\right|.
$$

```python
import numpy as np
from phonometry import environment

bands = np.array([63., 125., 250., 500., 1000., 2000., 4000., 8000.])

# Grassland (effective flow resistivity sigma = 200 kPa.s/m^2), source 1 m and
# receiver 1.5 m high, 50 m apart. The impedance comes from the Delany-Bazley
# porous model of phonometry.materials (a semi-infinite ground).
res = environment.ground_effect(bands, 1.0, 1.5, 50.0, flow_resistivity=2e5)
print(res.excess_attenuation)     # the ground dip (dB re free field)
print(res.reflection_coefficient) # complex Q per band
res.plot()                        # excess attenuation vs frequency
```

The ground impedance is either derived from an effective `flow_resistivity`
(via the `delany_bazley` or `miki` model of
[`phonometry.materials`](../../materials/absorbers/porous-absorbers.md), which model a semi-infinite porous
ground) or supplied directly as a normalized complex `impedance` (a scalar,
per-band array, or a `PorousMediumResult`). A plain `impedance` value is taken
in the $e^{-i\omega t}$ convention of Salomons, in which a passive ground has
$\operatorname{Im}(Z) > 0$; the porous models of `phonometry.materials` work
in the opposite $e^{+j\omega t}$ convention ($\operatorname{Im}(Z) < 0$), so
anything obtained from them (a
`flow_resistivity` or a `PorousMediumResult`) is conjugated internally before
it enters the Weyl-Van der Pol formulas.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ground_effect_spherical_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ground_effect_spherical.svg" alt="Excess attenuation (level re free field) against frequency on a log axis for four ground types. Fresh snow (10 kPa) dips deepest and lowest in frequency, near minus 18 dB around 150 Hz; forest floor (50 kPa) reaches about minus 15 dB near 290 Hz and grassland (200 kPa) about minus 12 dB near 540 Hz; asphalt (20000 kPa) hugs the plus 6 dB hard-ground enhancement limit until a deep dip near 2.4 kHz. A dotted line marks the plus 6 dB hard-ground limit and a solid line the 0 dB free field" width="90%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import environment

freqs = np.geomspace(50.0, 4000.0, 400)
grounds = [
    ("Fresh snow (10 kPa)", 10e3, "#2ca02c"),
    ("Forest floor (50 kPa)", 50e3, "#9467bd"),
    ("Grassland (200 kPa)", 200e3, "#1f77b4"),
    ("Asphalt (20000 kPa)", 20000e3, "#d62728"),
]
fig, ax = plt.subplots(figsize=(11, 6.4))
for label, sigma, color in grounds:
    res = environment.ground_effect(freqs, 1.0, 1.5, 50.0, flow_resistivity=sigma)
    ax.plot(freqs, res.excess_attenuation, color=color, label=label)
ax.axhline(6.0, color="k", ls=":", label="Hard-ground limit (+6 dB)")
ax.axhline(0.0, color="k", lw=0.8)
ax.set_xscale("log")
ax.set_xlabel("Frequency [Hz]")
ax.set_ylabel("Level re free field [dB]")
ax.legend()
plt.show()
```

</details>

**Limits reproduced by the implementation** (each a pinned test or conformance
anchor): an acoustically hard ground ($|Z| \to \infty$) gives $R_\mathrm{p} \to 1$,
$|w| \to 0$, $F \to 1$ and $Q \to 1$, so $\Delta L$ reaches +6 dB in phase;
the effective flow resistivity $\sigma \to \infty$ tends to that hard ground;
grazing incidence ($h_\mathrm{s}, h_\mathrm{r} \to 0$) gives $R_\mathrm{p} \to -1$; and the ground
effect is reciprocal under an exchange of source and receiver heights.

## 2. Advanced barrier diffraction

Three levels of screening beyond the ISO 9613-2 $D_z$ term are provided by
`barrier_insertion_loss` and its building blocks.

**Kurze-Anderson closed form.** The insertion loss of a thin screen as a
function of the Fresnel number $N = (2/\lambda)(A + B - d)$ (Bies Eq. 5.134,
with $A$ and $B$ the two segments of the shortest source-edge-receiver path
and $d$ the straight distance) is (Bies Eq. 5.138; Kurze & Anderson 1971):

$$
\Delta = 5 + 20\log_{10}\!\left(\frac{\sqrt{2\pi N}}{\tanh\sqrt{2\pi N}}\right)\;\text{dB},
$$

which tends to 5 dB at the shadow boundary $N \to 0$ and approximates Maekawa's
point-source curve within about 1.5 dB.

The clip below is that formula as a field. It is the
[2D FDTD solver](../../simulation/fdtd-simulation.md) run twice on one
12 × 7 m half-space over rigid ground with a thin rigid screen 2.5 m tall,
once at 100 Hz and once at 500 Hz, each with a barrier-free reference run over
the same ground so the annotated insertion loss is a true one. The geometry
fixes the path difference at 1.06 m for the receiver it marks, so the Fresnel
number is $N = 0.62$ at 100 Hz and $N = 3.1$ at 500 Hz — the same screen, a
factor of five apart in $N$ purely because $\lambda$ changed — and the field
shows what that buys: about 8 dB against about 17 dB. Two things are worth
watching for. The edge of the lit region running down from the top of the
screen is the shadow boundary, the $N \to 0$ locus where the formula bottoms
out at 5 dB; and inside the shadow the field is a cylindrical wave centred on
the top of the screen, which is what "the edge acts as a secondary source"
looks like. One caveat: the ground in the clip is perfectly rigid, so it shows
diffraction alone and none of the finite-impedance ground effect of section 1
— the coherent four-path model below adds that, and its curve swings tens of
decibels where this one is smooth.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_barrier_dark.gif"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_barrier.gif" alt="Animation: a point source behind a thin 2.5 metre rigid barrier on reflecting ground, simulated at 100 Hz and 500 Hz side by side; the long wavelength diffracts over the edge and fills the shadow zone, the short wavelength is cast into a deep clean shadow" width="640" height="360" loading="lazy"></picture>

[Watch the high-resolution video (WebM)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_barrier.webm)

The thin-screen methods share the same three geometric quantities: the two
diffracted segments over the edge and the straight path they replace. Drawn on
the 4 m screen of the snippets, they differ by just 0.15 m.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ground_barrier_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ground_barrier.svg" alt="Section of the barrier geometry: a loudspeaker source 1 m above the ground, a thin 4 m screen at 50 m and a microphone receiver 1.5 m high at 100 m, the blocked direct path of 100.00 m drawn dashed through the screen and the diffracted path bent over the edge in two segments A = 50.09 m and B = 50.06 m, with the resulting path difference of 0.15 m giving a Fresnel number of 0.44 and a Kurze-Anderson insertion loss of 10.0 dB at 500 Hz, rising to 15.5 dB at 2 kHz" width="92%"></picture>

```python
from phonometry import environment

environment.kurze_anderson_attenuation(0.0)     # 5.0 dB at the shadow boundary

# A 4 m barrier 50 m from a 1 m source, receiver 1.5 m high at 100 m.
il = environment.barrier_insertion_loss(bands, 1.0, 50.0, 4.0, 100.0, 1.5,
                                        method="kurze_anderson")
il.plot()                           # insertion loss vs frequency
```

**Exact rigid half-plane.** With `method="exact"` the wave-theoretic insertion
loss of a rigid thin screen is used: the compact Fresnel-integral form of the
MacDonald / Hadden & Pierce solution (Attenborough Eqs. 9.19-9.20), built from
the auxiliary Fresnel functions. It gives 6 dB at the shadow boundary (the
field is exactly halved, the flat-wedge limit) and tracks Kurze-Anderson through
the shadow zone.

**Thick barriers.** A `thickness` (top width $e$) lengthens the diffracted
path to $A + e + B$, the double-edge Fresnel number
$N = (2/\lambda)(A + B + e - d)$ of
Bies Eq. 5.157, so a thick barrier or a soil mound attenuates monotonically more
than the thin screen of the same height.

**Coherent barrier on the ground.** With a `ground_impedance` (or a
`ground_flow_resistivity`) the four source-image / receiver-image diffracted
paths are combined coherently, each ground reflection weighted by the
spherical-wave coefficient $Q$ above (Attenborough Ch. 9; Bies Sec. 5.3.5).
This exposes the ground-barrier interference structure that a purely energetic
sum of $A_\mathrm{gr}$ and $D_z$ cannot. As a first-order simplification a single
$Q$ (over the
overall source-receiver geometry) weights every bounce rather than a separate
coefficient per image path; the model is coherent and reciprocal but not a full
boundary-element solution.

```python
il = environment.barrier_insertion_loss(bands, 1.0, 50.0, 4.0, 100.0, 1.5,
                                        method="exact", ground_flow_resistivity=2e5)
il.ground        # True: the four-path coherent ground model was applied
il.plot()
```

The three models side by side on the same geometry tell the whole story: the
Kurze-Anderson fit and the exact half-plane track each other to within about
1.5 dB across two decades of Fresnel number, while the coherent ground model
swings tens of decibels around them, up where the barrier removes the
ground-effect dip of the unscreened path, down where the four diffracted paths
interfere destructively.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/barrier_insertion_loss_methods_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/barrier_insertion_loss_methods.svg" alt="Barrier insertion loss against frequency on a log axis for a 4 m screen between a 1 m source at 50 m and a 1.5 m receiver at 100 m. The dashed Kurze-Anderson curve and the solid exact rigid half-plane curve rise together from about 6 dB at 50 Hz to 19 dB at 5 kHz, never more than about 1.5 dB apart; the coherent four-path ground curve oscillates around them, peaking above 45 dB near 230 Hz where the unscreened ground dip is removed and falling below minus 10 dB near 550 Hz, with the dotted Kurze-Anderson 5 dB grazing-limit line underneath" width="90%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import environment

# The 4 m barrier of the snippets above, on a fine frequency grid.
freqs = np.geomspace(50.0, 5000.0, 240)
il_ka = environment.barrier_insertion_loss(freqs, 1.0, 50.0, 4.0, 100.0, 1.5,
                                           method="kurze_anderson")
il_ex = environment.barrier_insertion_loss(freqs, 1.0, 50.0, 4.0, 100.0, 1.5,
                                           method="exact")
il_gr = environment.barrier_insertion_loss(freqs, 1.0, 50.0, 4.0, 100.0, 1.5,
                                           method="exact", ground_flow_resistivity=2e5)
fig, ax = plt.subplots(figsize=(11, 6.4))
ax.semilogx(freqs, il_ka.insertion_loss, "--", label="Kurze-Anderson (thin screen)")
ax.semilogx(freqs, il_ex.insertion_loss, label="Exact rigid half-plane")
ax.semilogx(freqs, il_gr.insertion_loss, label="Exact + coherent ground (four paths)")
ax.axhline(5.0, color="k", ls=":", label="Kurze-Anderson grazing limit (5 dB)")
ax.set(xlabel="Frequency [Hz]", ylabel="Insertion loss [dB]")
ax.legend()
plt.show()
```

</details>

All three curves share the same base geometry, and `.plot_geometry()` draws
it to scale: at these road-traffic distances the 4 m screen is a sliver. For
the thin-screen curves the 0.15 m path difference combines with wavelength in
the Fresnel number; the coherent-ground curve also depends on ground
impedance and image-path interference.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/barrier_geometry_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/barrier_geometry.svg" alt="To-scale section of the barrier geometry of the insertion-loss curves: a source star 1 m above the hatched ground, a thin 4 m screen at 50 m, and a receiver triangle 1.5 m high at 100 m, with the dashed direct path cut by the screen, the solid diffracted path bent over its top edge, the path difference of 0.15 m annotated and the 50 m and 100 m distances dimensioned" width="90%"></picture>

*Drawn to scale the screen almost vanishes: the diffracted path over the top
is only 0.15 m longer than the blocked direct path, and that difference is
the geometric input of the Fresnel number $N = (2/\lambda)(A + B - d)$ that the
thin-screen methods above key on.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import environment

freqs = np.geomspace(50.0, 5000.0, 240)
il = environment.barrier_insertion_loss(freqs, 1.0, 50.0, 4.0, 100.0, 1.5)

# One line: the section to scale, with the path-length difference annotated.
il.plot_geometry()
plt.show()
```

</details>

## 3. What the product declaration says (EN 1793)

Everything above is the barrier as physics. A barrier on sale is a product, and
what its declaration carries is two integers, neither of them a diffraction:
how much of the sound reaching it comes back across the road, and how much of
it goes through. Both are weighted by a spectrum nobody measures on site, the
**normalised traffic noise spectrum** of EN 1793-3: eighteen one-third octave
bands from 100 Hz to 5 kHz, peaking at 1 kHz and twelve decibels down at either
end.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/road_device_ratings_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/road_device_ratings.svg" alt="Three panels over the eighteen one-third octave bands of EN 1793-3. Left: the normalised traffic noise spectrum of EN 1793-3 as bars, running from minus twenty decibels at 100 Hz up to a minus eight decibel peak at 1 kHz and back down to minus eighteen at 5 kHz, with an annotation saying the peak carries the rating, and over them the normalised railway noise spectrum of EN 16272-3-1 as a marker line, lower at 100 Hz and flat from 1.25 to 2.5 kHz where the road one is already falling. Middle: the sound absorption coefficient of two devices, an absorptive cassette rising from 0.15 to 0.98 around 400 Hz and easing to 0.70, rating DL alpha 8 decibels in category A3, and a concrete panel flat at 0.05 rating 0 decibels in category A1. Right: the sound reduction index of two devices, a concrete panel rising from 30 to 53 decibels and rating DL R 42 decibels in category B4, and a metal cassette rising from 21 to 34 decibels and rating 29 decibels in category B3." width="100%"></picture>

*The weighting on the left decides everything, and there are two of them: a road
device is judged by what it does around 1 kHz, a railway one by what it does
between 1,25 and 2,5 kHz.*

**EN 1793-1** rates absorption as the energy the device does *not* send back:

$$
DL_\alpha = -10 \lg\left| 1 -
\frac{\sum_{i=1}^{18} \alpha_{\mathrm{S}i}\, 10^{0,1 L_i}}
     {\sum_{i=1}^{18} 10^{0,1 L_i}} \right|
$$

A reverberation-room $\alpha_\mathrm{S}$ can pass one band by band, which would
push the weighted ratio past 1 and leave the logarithm without an argument.
Clause 5 says so and fixes it: the ratio is limited to 0,99, so no device can
rate above 20 dB however absorptive it measures. `sound_absorption_rating`
warns when that limit is what answered instead of the measurement.

**EN 1793-2** rates airborne insulation with the same weighting, on the
transmitted energy instead:

$$
DL_R = -10 \lg\left|
\frac{\sum_{i=1}^{18} 10^{0,1 L_i}\, 10^{-0,1 R_i}}
     {\sum_{i=1}^{18} 10^{0,1 L_i}} \right|
$$

```python
from phonometry import environment

# A cassette with mineral wool behind a perforated face, in the eighteen
# one-third octave bands of EN 1793-3 from 100 Hz to 5 kHz.
absorption = [0.15, 0.25, 0.40, 0.60, 0.80, 0.95, 0.98, 0.95, 0.92,
              0.90, 0.88, 0.85, 0.82, 0.80, 0.78, 0.75, 0.72, 0.70]
reduction = [21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0,
             30.0, 31.0, 31.0, 32.0, 32.0, 33.0, 33.0, 34.0, 34.0]

absorbed = environment.sound_absorption_rating(absorption)
print(absorbed.reported, absorbed.category)     # 8 A3

through = environment.airborne_insulation_rating(reduction)
print(through.reported, through.category)       # 29 B3
```

Both are reported rounded to the nearest integer (EN 1793-1 Clause 6.1,
EN 1793-2 Clause 7.1), and each has a normative ladder in its Annex A read off
that integer: A1 to A5 for absorption, B1 to B4 for insulation, with A0 and B0
reserved for "not determined". The ladders have no gaps between their steps
because the number they classify is already an integer.

The two are not comparable and a declaration carries both. A plain concrete
panel reflects almost everything across the road and is still the better wall;
an absorptive cassette that keeps the reflection down can be the weaker one.
Which of the two matters is a question about the site, not about the product:
absorption for a road in a cutting or between parallel barriers, insulation for
whatever is directly behind.

### The same two numbers beside a railway

A barrier beside a track is rated the same way and against a different noise.
**EN 16272-3-1:2012** prints the normalised railway noise spectrum over the
same eighteen bands, and its Clauses 5 and 6 are the two formulas above with
that table in the weights. Rolling noise sits higher up than a road: the
railway spectrum is flat within a decibel from 1,25 kHz to 2,5 kHz, where the
road one has already begun to fall away, so an absorber that improves with
frequency is worth more beside a track than beside a road.

```python
from phonometry import environment

# A thick porous absorber, still improving where rolling noise is loudest.
absorption = [0.10, 0.15, 0.22, 0.32, 0.45, 0.60, 0.72, 0.82, 0.88,
              0.92, 0.95, 0.96, 0.96, 0.95, 0.94, 0.93, 0.92, 0.90]

road = environment.sound_absorption_rating(absorption)
rail = environment.sound_absorption_rating(absorption, spectrum="railway")
print(road.reported, rail.reported)          # 8 10
print(road.category, rail.category)          # A3 None
```

The railway parts print no category ladder: their annexes are guidance notes
on using the rating, so a railway rating is the number and nothing more, and
the result says so by carrying `None` where a road device carries its letter.
Clause 6 also carries a slip worth knowing about, since it changes what a
reader goes looking for: it says the sound reduction indices are weighted by
"the normalised traffic noise spectrum defined in Table 1", while Table 1 of
that standard is the railway spectrum and the symbol list under the formula
says railway. It is the road wording of EN 1793-2, left in place when the
clause was copied.

## Relation to ISO 9613-2

The tabulated $A_\mathrm{gr}$ and $D_z$ of the
[ISO 9613-2 method](outdoor-propagation.md)
are octave-band, energy-based engineering fits; `ground_effect` and
`barrier_insertion_loss` are their narrowband wave-acoustic counterparts. Over
hard ground both agree on the +6 dB enhancement and the 5 dB grazing barrier
floor, but only the wave models resolve the interference dips that move with
geometry, frequency and ground impedance, which is why they are the natural
infrastructure for the meteorological schemes of Nord2000 and CNOSSOS.

## What this guide covers

**Covered.** The Weyl-Van der Pol spherical-wave ground reflection coefficient
(`ground_effect`; Attenborough Eq. 2.40a/c, Salomons Eq. 3.2/D.58, with the
Faddeeva-function boundary-loss factor), its hard-ground +6 dB,
grazing-incidence and reciprocity limits pinned as tests; and wave-theoretic
barrier diffraction in `barrier_insertion_loss` — the Kurze-Anderson closed form
(`kurze_anderson_attenuation`, Bies Eq. 5.138), the exact rigid half-plane
(MacDonald / Hadden & Pierce, Attenborough Eqs. 9.19-9.20), thick barriers
through the double-edge Fresnel number (Bies Eq. 5.157) and the coherent
four-path barrier-on-ground model weighted by the `ground_effect` coefficient.

**Not covered.** Both models assume a homogeneous, non-refracting,
non-turbulent atmosphere; a vertical sound-speed gradient is the subject of
[atmospheric refraction](atmospheric-refraction.md) instead. The coherent
barrier-on-ground model weights all four diffracted paths with a single
reflection coefficient $Q$ computed over the overall source-receiver geometry,
not with a separate coefficient per image path — so it is coherent and
reciprocal, but it is not a boundary-element solution.

## See also

- [Outdoor Sound Propagation](outdoor-propagation.md): the octave-band ISO 9613-2 fits these models sit underneath, and the rule an obstacle has to satisfy to be a barrier at all.
- [Atmospheric refraction: rays and the GFPE](atmospheric-refraction.md): the vertical sound-speed gradient both models here assume away.
- [Porous absorbers](../../materials/absorbers/porous-absorbers.md): the Delany-Bazley and Miki models behind `flow_resistivity`, and their fit range.
- Theory: [Outdoor propagation](../../reference/theory/environment-transport.md#outdoor-propagation-general-method-iso-9613-2): the ground and barrier terms of ISO 9613-2 in the context of the whole attenuation sum.
- API reference: [`environment.propagation.ground_barriers`](https://jmrplens.github.io/phonometry/reference/api/environment/ground-barriers/).

## References

- Attenborough, K., & Van Renterghem, T. (2021). *Predicting Outdoor Sound*
  (2nd ed.). CRC Press. ISBN 978-1-138-30655-2.
  [doi:10.1201/9780429470141](https://doi.org/10.1201/9780429470141).
  Chapter 2 (spherical-wave reflection over an impedance ground, the
  Weyl-Van der Pol equation and the boundary-loss factor) and Chapter 9
  (outdoor noise barriers, the MacDonald and Hadden & Pierce diffraction
  solutions).
- Salomons, E. M. (2001). *Computational Atmospheric Acoustics*. Kluwer
  Academic. ISBN 978-1-4020-0390-5.
  [doi:10.1007/978-94-010-0660-6](https://doi.org/10.1007/978-94-010-0660-6).
  Chapter 3 and Appendix D (the two-ray field, the plane- and spherical-wave
  reflection coefficients, and the numerical distance).
- Bies, D. A., Hansen, C. H., & Howard, C. Q. (2017). *Engineering Noise
  Control* (5th ed.). CRC Press. ISBN 978-1-4987-2405-0. Sections 5.2.3
  (spherical-wave ground reflection) and 5.3.5-5.3.7 (Fresnel number,
  Kurze-Anderson, thin- and thick-barrier diffraction and terrain shielding).
- Kurze, U. J., & Anderson, G. S. (1971). Sound attenuation by barriers.
  *Applied Acoustics*, 4(1), 35-53.
  [doi:10.1016/0003-682X(71)90024-7](https://doi.org/10.1016/0003-682X(71)90024-7).
- Hadden, W. J., & Pierce, A. D. (1981). Sound diffraction around screens and
  wedges for arbitrary point source locations. *Journal of the Acoustical
  Society of America*, 69(5), 1266-1276.
  [doi:10.1121/1.385809](https://doi.org/10.1121/1.385809).

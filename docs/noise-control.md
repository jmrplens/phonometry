← [Documentation index](README.md)

# Industrial noise control: silencers, HVAC and enclosures

Three passive measures dominate applied noise control, and the
`noise_control` domain covers all three with the engineering theory of Bies,
Hansen & Howard, *Engineering Noise Control* (5th ed., CRC Press 2017):
**reactive silencers** in a duct (the four-pole transmission-matrix method),
the passive attenuations and regenerated noise of an **HVAC** run, and the
insertion loss of a **machine enclosure**. The radiating piston of the
[electroacoustics](electroacoustics.md) domain is the companion radiator
model.

## 1. Reactive silencers (four-pole method)

A reactive silencer attenuates by *reflecting* sound with impedance
discontinuities. Each acoustic element is a 2×2 **transfer (four-pole)
matrix** relating the sound pressure `p` and the volume velocity `Su` at its
two ends (Bies Eq. (8.133); Munjal, *Acoustics of Ducts and Mufflers*), and a
compound silencer is the ordered matrix product of its elements. A straight
duct of length `L` and area `S` is (Bies Eq. (8.143), no flow)

```text
[ cos(kL)            j (rho c / S) sin(kL) ]
[ j (S / rho c) sin(kL)   cos(kL)          ] ,   k = omega / c,
```

and a side branch of acoustic impedance `Z_b` is the shunt
`[[1, 0], [1/Z_b, 1]]` (Eq. (8.144)). The **transmission loss** follows from
the compound matrix `T` with the port impedances `Z1 = rho c / S_in` and
`Zn = rho c / S_out` (Munjal Eq. (3.27); Bies Eq. (8.141) prints the
`T11`/`T22` impedance weights of this formula inverted and fails the
sudden-expansion limit, see the [errata registry](ERRATA.md))

```text
TL = 10 log10[ (Zn/Z1) (1/4) | T11 + T12/Zn + Z1 T21 + (Z1/Zn) T22 |^2 ] ,
```

which for equal inlet/outlet areas reduces to (Bies Eq. (8.148))

```text
TL = 20 log10( (1/2) | T11 + T12/Zc + Zc T21 + T22 | ) ,   Zc = rho c / S,
```

and the **insertion loss** for a source impedance `Z_s` and a radiation
impedance `Z_r` is the extra attenuation over a direct (zero-length)
connection, so a through connection gives `IL = 0`.

### Expansion chamber

A chamber of area `S_exp` and length `L` between pipes of area `S_duct` has the
closed-form transmission loss (Bies Eq. (8.111)) with area ratio
`m = S_exp / S_duct`:

```text
TL = 10 log10[ 1 + (1/4) (m - 1/m)^2 sin^2(kL) ] ,
```

peaking at `10 log10[1 + (1/4)(m - 1/m)^2]` at `kL = pi/2, 3 pi/2, ...`
(1.94 dB for `m = 2`, 6.55 dB for `m = 4`, 12.18 dB for `m = 8`, 18.10 dB for
`m = 16`) and dropping to 0 at `kL = n pi`, where the chamber is a
half-wavelength long and transparent. The four-pole product reproduces this
exactly.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/silencer_expansion_chamber_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/silencer_expansion_chamber.svg" alt="Expansion-chamber transmission loss against frequency for area ratios m = 2, 4, 8 and 16, showing periodic peaks rising with m at odd multiples of the quarter-wave frequency and troughs returning to 0 dB at every half-wavelength of the chamber length" width="88%"></picture>

```python
import numpy as np
from phonometry import expansion_chamber

freqs = np.linspace(20.0, 2000.0, 2000)
res = expansion_chamber(freqs, length=0.3, chamber_area=0.04, pipe_area=0.01)
print(round(res.transmission_loss.max(), 2))   # 6.55 dB peak (m = 4)
res.plot()                                      # TL (and IL) vs frequency
```

### Side-branch and extended-tube resonators

A **Helmholtz resonator** (`helmholtz_resonator`) and a closed **quarter-wave
tube** (`quarter_wave_resonator`) each short the duct at their tuning
frequency, `f_0 = (c / 2 pi) sqrt(S_neck / (l_e V))` (Bies Eq. (8.46)) and
`f = c / 4 l_e` (Eq. (8.44)), giving a sharp transmission-loss spike there. An
**extended-tube chamber** (`extended_tube_chamber`) buries quarter-wave side
branches in an expansion chamber to fill its troughs; with zero extensions it
reduces exactly to the plain chamber. Advanced layouts chain elements directly
with `duct_matrix`, `shunt_matrix`, `cascade`, `transmission_loss` and
`insertion_loss`.

Each device returns a `ReactiveSilencerResult` with `transmission_loss`,
`insertion_loss` (when source/radiation impedances are given), the compound
`transfer_matrix`, the tuning `resonances` and `.plot()`.

## 2. HVAC duct attenuation and flow noise

`noise_control.hvac` gathers the Bies Chapter 8 duct methods:

- `end_reflection_loss` — the low-frequency reflection back up an open duct end
  (ASHRAE Table 8.14, interpolated over diameter and frequency; it passes
  exactly through the tabulated nodes).
- `elbow_insertion_loss` — the insertion loss per bend for square/round,
  vaned/unvaned and lined/unlined elbows keyed by `W / lambda` (ASHRAE
  Table 8.11).
- `plenum_attenuation` — the plenum-chamber transmission loss by Wells' method
  (Eq. (8.275)), whose reverberant term uses the plenum
  [room constant](room-image-sources.md).
- `flow_noise_straight_duct`, `flow_noise_bend` — the flow-generated (self)
  noise sound power of straight ducts and mitred bends (VDI 2081, Eqs. (8.251),
  (8.254)).

```python
from phonometry.noise_control import hvac

bands = [63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0]
er = hvac.end_reflection_loss(bands, diameter=0.30, termination="flush")
tl = hvac.plenum_attenuation(0.1, 1.0, 20.0, 0.2)      # Wells' method, dB
fn = hvac.flow_noise_straight_duct(bands, flow_velocity=10.0, area=0.04)
```

Rectangular ducts use the equivalent diameter `D = sqrt(4 S / pi)`. Bies 5th
ed. gives the duct end reflection only as the ASHRAE table (no closed form in
that edition); this module reproduces and interpolates it.

## 3. Machine enclosures

A sealed enclosure reduces the radiated noise by its panel transmission loss
`R`, minus a penalty `C` for the reverberant build-up inside the small, hard
cavity (Bies Eqs. (7.103), (7.111)):

```text
IL = R - C ,   C = 10 log10( 0.3 + S_E / R_i ) ,
```

with the external area `S_E` and the interior room constant
`R_i = S_i alpha_i / (1 - alpha_i)` (the same `room_constant` as the
steady-state room field). A hard interior wastes much of the panel `R`; lining
it drives `C` toward its floor `10 log10 0.3 = -5.2 dB`.

**The panel transmission loss `R` is supplied by the caller** — measured, or
predicted by a panel model — as a per-band array or a callable of frequency.
This module never predicts `R` itself; it combines a given `R` with the
interior absorption.

```python
import numpy as np
from phonometry import enclosure_insertion_loss

bands = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
panel_R = np.array([18.0, 24.0, 30.0, 36.0, 42.0, 46.0])   # measured, dB
enc = enclosure_insertion_loss(panel_R, external_area=6.0, internal_area=5.0,
                               internal_absorption=0.3, frequencies=bands)
print(np.round(enc.insertion_loss, 1))          # net IL = R - C per band
enc.plot()
```

`enclosure_insertion_loss` returns an `EnclosureResult` with the panel
`panel_transmission_loss`, the interior `correction`, the net `insertion_loss`,
the interior `room_constant` and `.plot()`.

## Cross-check against the FDTD solver

The four-pole expansion chamber is cross-checked against the independent 2D
[FDTD wave solver](fdtd-simulation.md): a plane-wave duct that widens into a
chamber and narrows back transmits far less at the four-pole TL peak
(`kL = pi/2`) than at the transparent trough (`kL = pi`), and the measured
amplitude ratio reproduces the closed-form peak transmission loss to a fraction
of a decibel (test `tests/noise_control/test_fdtd_crosscheck.py`).

## References

- Bies, D. A., Hansen, C. H., & Howard, C. Q. (2017). *Engineering noise
  control* (5th ed.). CRC Press.
  [doi:10.1201/9781351228152](https://doi.org/10.1201/9781351228152). The
  muffler four-pole method and expansion-chamber TL (§8.8–8.9), the HVAC duct
  methods (§8.11–8.17) and the machine-enclosure noise reduction (§7.4).
- Munjal, M. L. (2014). *Acoustics of ducts and mufflers* (2nd ed.). Wiley.
  [doi:10.1002/9781118443767](https://doi.org/10.1002/9781118443767). The
  transfer-matrix formulation behind the element matrices and the
  transmission loss from the compound matrix (Eq. (3.27)).
- Vér, I. L., & Beranek, L. L. (2006). *Noise and vibration control
  engineering* (2nd ed.). Wiley.
  [doi:10.1002/9780470172568](https://doi.org/10.1002/9780470172568). The
  companion treatment of mufflers, ducts and enclosures.

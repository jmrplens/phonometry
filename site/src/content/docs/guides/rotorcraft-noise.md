---
title: "Rotorcraft noise: the hemisphere method"
description: "The ECAC Doc 32 / NORAH2 rotorcraft-noise hemisphere source model and its propagation adjustments: spherical spreading, atmospheric absorption (ISO 9613-1 / Table 4) and the Chien-Soroka ground effect over CNOSSOS impedance ground."
---

Helicopter noise is strongly directive, so the **ECAC Doc 32** method describes
the source with a **noise hemisphere**: one-third-octave-band sound pressure
levels on a spherical grid of azimuth `φ` and polar angle `θ`, defined at a fixed
**60 m** reference distance under ICAO reference atmospheric conditions. Placing
that source at a receiver adds the propagation adjustment
`ΔLp = ΔLs + ΔLa + ΔLg`.

## The noise hemisphere

A `RotorcraftHemisphere` holds the band levels on the azimuth/polar grid.
`hemisphere_source_level` reads the level at an arbitrary emission direction,
bilinear in the energy domain over the four neighbouring bins (Eq. 13); outside
the measured coverage it falls back to the angularly-nearest filled bin
(Eq. 14/15).

```python
import phonometry as ph

h = ph.RotorcraftHemisphere(frequencies=freqs, azimuth=phi, polar=theta, levels=levels)
lv = ph.hemisphere_source_level(h, 0.0, 90.0)   # source level per band at 60 m
h.plot()                                          # fore-aft directivity
```

## Propagation adjustments

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect.svg" alt="Rotorcraft ground-effect adjustment versus one-third-octave frequency for hard and soft ground, showing low-frequency reinforcement, a deep interference dip and the incoherent high-frequency region" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect_dark.svg" alt="Rotorcraft ground-effect adjustment versus one-third-octave frequency for hard and soft ground, showing low-frequency reinforcement, a deep interference dip and the incoherent high-frequency region" style="width:82%">

The 60 m hemisphere level is carried to the receiver by three adjustments
(§A.4): `spherical_spreading_adjustment` (`ΔLs = −20·log10(r/60)`, Eq. 24),
`atmospheric_adjustment` (`ΔLa = −α(f)·(r − 60)` with the ISO 9613-1 coefficient,
Eq. 26/27), and `ground_effect_adjustment` (direct/reflected interference over an
impedance plane, Chien-Soroka Eq. 28-35, with the Delany-Bazley impedance and the
CNOSSOS flow-resistivity classes `"A"`-`"H"`).

```python
import numpy as np
import phonometry as ph

freqs = 1000.0 * 10.0 ** (np.arange(-13, 11) / 10.0)   # 50 Hz-10 kHz thirds
r = 500.0
received = (lv
            + ph.spherical_spreading_adjustment(r)
            + ph.atmospheric_adjustment(freqs, r)
            + ph.ground_effect_adjustment(freqs, 150.0, 1.5, 500.0, flow_resistivity="D"))
```

Validated against the NORAH2 guidance Table 4 (atmospheric attenuation), the
closed-form inverse-square spreading, the analytic rigid-ground and grazing
limits of the ground effect, and exact hemisphere interpolation at the grid
nodes.

---

**Standards.** ECAC Doc 32, 1st ed. (rotorcraft noise contours); NORAH2 modelling
guidance (EASA.2020.FC.06 SC03.D1.5d) §A.3-A.4: the noise hemisphere, spherical
spreading, atmospheric attenuation (ISO 9613-1, Table 4) and the Chien-Soroka
ground effect (Delany-Bazley impedance, CNOSSOS flow resistivity). Flight-path
integration (SEL/LAmax/EPNL), ground-grid contours and terrain shielding are a
separate later development.

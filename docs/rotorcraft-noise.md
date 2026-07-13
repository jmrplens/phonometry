← [Documentation index](README.md)

# Rotorcraft noise: the hemisphere method (ECAC Doc 32 / NORAH2)

Helicopter noise is strongly directive, so the ECAC Doc 32 method describes the
source with a **noise hemisphere**: one-third-octave-band sound pressure levels on
a spherical grid of azimuth `φ` and polar angle `θ`, measured at a fixed **60 m**
reference distance under ICAO reference atmospheric conditions. Placing that
source at a receiver adds the propagation adjustment
`ΔLp = ΔLs + ΔLa + ΔLg (+ ΔLd)`.

This page covers the source and propagation primitives; the flight-path
integration to `SEL`/`LAmax`/`EPNL` and ground-grid contours, and terrain
shielding, follow in later work.

## 1. The noise hemisphere

A `RotorcraftHemisphere` holds the band levels on the azimuth/polar grid (with
missing bins marked `NaN`). `hemisphere_source_level` reads the source level at an
arbitrary emission direction: the grid is first gap-filled by nearest-bin
constant-value extrapolation (Eq. 14/15, equally-near bins energy-averaged;
computed once and cached), then the lookup is bilinear in the energy domain over
the four neighbouring bins (Doc 32 Eq. 13), so partially-measured cells stay
continuous with their measured corners.

```python
import numpy as np
import phonometry as ph

# A hemisphere: band levels of shape (azimuth, polar, frequency) at 60 m.
h = ph.RotorcraftHemisphere(frequencies=freqs, azimuth=phi, polar=theta, levels=levels)
h.plot()                                   # fore-aft directivity (needs matplotlib)
lv = ph.hemisphere_source_level(h, 0.0, 90.0)   # level per band abeam-below
```

## 2. Propagation adjustments

The hemisphere level at 60 m is carried to the receiver by three adjustments
(Doc 32 §A.4):

- **`spherical_spreading_adjustment(r)`** — `ΔLs = −20·log10(r/60)` (Eq. 24).
- **`atmospheric_adjustment(freqs, r)`** — `ΔLa = −α(f)·(r − 60)` with the
  ISO 9613-1 pure-tone coefficient at the exact band centre (Eq. 26/27), reusing
  the library's `air_attenuation`; this is what the NORAH2 reference
  implementation computes. The guidance's alternative SAE (Rickley) band mapping,
  tabulated in its Table 4, coincides below 3.15 kHz and deviates by up to
  2.2 dB/km at 8-10 kHz.
- **`ground_effect_adjustment(freqs, hs, hr, dp, flow_resistivity=…)`** — the
  interference between the direct and ground-reflected rays over an impedance
  plane (Chien-Soroka, Eq. 28-35), with the Delany-Bazley one-parameter impedance
  and the CNOSSOS flow-resistivity classes `"A"`-`"H"`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect.svg" alt="Rotorcraft ground-effect adjustment versus one-third-octave frequency for hard (asphalt) and soft (grass) ground: low-frequency reinforcement, a deep destructive interference dip, and the incoherent +3 dB high-frequency region, the dip deeper over hard ground" width="82%">
</picture>

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

Validated against the NORAH2 guidance Table 4 (all 31 bands, 10 Hz-10 kHz), the
closed-form inverse-square spreading, the analytic rigid-ground `+6 dB` and
grazing limits of the ground effect, off-node bilinear lookups on the reference
hemispheres of all eleven rotorcraft types, and end to end against the NORAH2
prototype: single-hemisphere emissions of its reference single-event histories
are reproduced to 0.1 dB(A) over hard ground (0.5 dB over soft ground).

---

**Standards.** ECAC Doc 32, 1st ed., *Report on Standard Method of Computing
Rotorcraft Noise Contours*; NORAH2 rotorcraft-noise modelling guidance
(EASA.2020.FC.06 SC03.D1.5d), §A.3-A.4 — the noise hemisphere (§A.3.2), spherical
spreading (Eq. 24), atmospheric attenuation (Eq. 26/27, ISO 9613-1 coefficient,
Table 4) and ground effect (Chien-Soroka, Eq. 28-35, Delany-Bazley impedance,
CNOSSOS flow resistivity). Flight-path integration (SEL/LAmax/EPNL), ground-grid
contours and terrain shielding are a separate later development.

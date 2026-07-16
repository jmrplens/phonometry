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
`hemisphere_source_level` reads the level at an arbitrary emission direction:
the grid is first gap-filled from the angularly-nearest filled bins (Eq. 14/15,
cached), then the lookup is bilinear in the energy domain over the four
neighbouring bins (Eq. 13), so partially-measured cells stay continuous with
their measured corners.

```python
import phonometry as ph

h = ph.RotorcraftHemisphere(frequencies=freqs, azimuth=phi, polar=theta, levels=levels)
lv = ph.hemisphere_source_level(h, 0.0, 90.0)   # source level per band at 60 m
h.plot()                                          # fore-aft directivity
```

## Propagation adjustments

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect.svg" alt="Rotorcraft ground-effect adjustment versus one-third-octave frequency for hard and soft ground, showing low-frequency reinforcement, a deep interference dip and the incoherent high-frequency region" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_ground_effect_dark.svg" alt="Rotorcraft ground-effect adjustment versus one-third-octave frequency for hard and soft ground, showing low-frequency reinforcement, a deep interference dip and the incoherent high-frequency region" style="width:82%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import aircraft

freqs = 1000.0 * 10.0 ** (np.arange(-13, 11) / 10.0)   # 50 Hz-10 kHz thirds
hs, hr, dp = 150.0, 1.5, 500.0                          # overflight geometry
grass = aircraft.ground_effect_adjustment(freqs, hs, hr, dp, flow_resistivity="D")
asphalt = aircraft.ground_effect_adjustment(freqs, hs, hr, dp, flow_resistivity="G")

fig, ax = plt.subplots()
ax.axhline(0.0, color="0.5", linewidth=1.0)
ax.semilogx(freqs, asphalt, marker="o", markersize=3,
            label="Hard (asphalt/concrete, class G)")
ax.semilogx(freqs, grass, marker="s", markersize=3,
            label="Soft (grass/pasture, class D)")
ax.set(xlabel="One-third-octave-band centre frequency [Hz]",
       ylabel="Ground-effect adjustment ΔLg [dB]",
       title="Rotorcraft ground effect (ECAC Doc 32, Chien-Soroka)")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

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

The standard database is recorded at 60 m, the default. If a hemisphere uses a
different polar distance (`h.distance`, e.g. 70 m hover rings), pass it to both
distance-dependent adjustments as `reference_distance=h.distance`.

Validated against the NORAH2 guidance Table 4 (all 31 bands), the closed-form
inverse-square spreading, the analytic rigid-ground and grazing limits of the
ground effect, off-node bilinear lookups on the reference hemispheres of all
eleven rotorcraft types, and end to end against the NORAH2 prototype's
single-event histories (0.1 dB(A) over hard ground, 0.5 dB over soft ground).

## References

- European Civil Aviation Conference. (2026). *Report on standard method of
  computing rotorcraft noise contours* (ECAC.CEAC Doc 32, 1st ed.).
  [ECAC documents page](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements),
  [free PDF](https://www.ecac-ceac.org/images/documents/ECAC-CEAC-DOC_32-REPORT_ON_STANDARD_METHOD_OF_COMPUTING_ROTORCRAFT_NOISE_CONTOURS.pdf).
  The standard rotorcraft contour method whose hemisphere source model and
  propagation adjustments this page implements.
- Olsen, H., Tuinstra, M., & van Oosten, N. (2024). *Rotorcraft noise
  modelling guidance* (Research Project NOISE SC01, deliverable D1.5d,
  contract EASA.2020.FC.06). European Union Aviation Safety Agency.
  [EASA project page](https://www.easa.europa.eu/en/research-projects/environmental-research-rotorcraft-noise),
  [free PDF](https://www.easa.europa.eu/en/downloads/132005/en).
  The equation-level guidance (Eq. 13-35) behind the implementation, with the
  Table 4 attenuation values and the reference hemispheres used as oracles.
- Chien, C. F., & Soroka, W. W. (1975). Sound propagation along an impedance
  plane. *Journal of Sound and Vibration*, 43(1), 9-20.
  [doi:10.1016/0022-460X(75)90200-X](https://doi.org/10.1016/0022-460X(75)90200-X).
  The two-ray interference solution over an impedance plane behind the
  ground-effect adjustment.
- Delany, M. E., & Bazley, E. N. (1970). Acoustical properties of fibrous
  absorbent materials. *Applied Acoustics*, 3(2), 105-116.
  [doi:10.1016/0003-682X(70)90031-9](https://doi.org/10.1016/0003-682X(70)90031-9).
  The one-parameter flow-resistivity impedance model the ground effect
  evaluates.
- Kephalopoulos, S., Paviotti, M., & Anfosso-Lédée, F. (2012). *Common noise
  assessment methods in Europe (CNOSSOS-EU)* (EUR 25379 EN). Publications
  Office of the European Union.
  [doi:10.2788/31776](https://doi.org/10.2788/31776),
  [JRC repository](https://publications.jrc.ec.europa.eu/repository/handle/JRC72550).
  The flow-resistivity ground classes `"A"`-`"H"` accepted by
  `ground_effect_adjustment`.

## Standards

ECAC Doc 32, 1st ed. (rotorcraft noise contours); NORAH2 modelling
guidance (EASA.2020.FC.06 SC01.D1.5d) §A.3-A.4: the noise hemisphere, spherical
spreading, atmospheric attenuation (ISO 9613-1, Table 4) and the Chien-Soroka
ground effect (Delany-Bazley impedance, CNOSSOS flow resistivity). Flight-path
integration (SEL/LAmax/EPNL), ground-grid contours and terrain shielding are a
separate later development.

## See also

- API reference: [`aircraft.rotorcraft_noise`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/).

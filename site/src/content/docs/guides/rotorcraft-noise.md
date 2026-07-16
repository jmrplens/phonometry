---
title: "Rotorcraft noise: the hemisphere method"
description: "The ECAC Doc 32 / NORAH2 rotorcraft-noise hemisphere method: the hemisphere source model, its propagation adjustments, the flight-condition interpolation and track kinematics, and the single-event SEL, LASmax and EPNL with ground-grid contours."
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
from phonometry import aircraft

h = aircraft.RotorcraftHemisphere(frequencies=freqs, azimuth=phi, polar=theta, levels=levels)
lv = aircraft.hemisphere_source_level(h, 0.0, 90.0)   # source level per band at 60 m
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
from phonometry import aircraft

freqs = 1000.0 * 10.0 ** (np.arange(-13, 11) / 10.0)   # 50 Hz-10 kHz thirds
r = 500.0
received = (lv
            + aircraft.spherical_spreading_adjustment(r)
            + aircraft.atmospheric_adjustment(freqs, r)
            + aircraft.ground_effect_adjustment(freqs, 150.0, 1.5, 500.0, flow_resistivity="D"))
```

The standard database is recorded at 60 m, the default. If a hemisphere uses a
different polar distance (`h.distance`, e.g. 70 m hover rings), pass it to both
distance-dependent adjustments as `reference_distance=h.distance`.

## Flight conditions: interpolating between hemispheres

A database records one hemisphere per flight condition (airspeed `V`, path
angle `γ`). Real conditions rarely coincide with a measured one, so the NORAH2
guidance interpolates (Eq. 3-10): both axes are normalised by their database
spans (with the empirical factor `Ffc = 2` on the path angle), a Delaunay
triangulation covers the normalised conditions, and a query inside the convex
hull blends its enveloping triangle with inverse-distance weights in the energy
domain. Outside the hull the nearest condition is adopted unblended, which is
also the behaviour ECAC Doc 32, 1st ed. prescribes for its whole envelope (it
defines no interpolation yet).

```python
from phonometry import aircraft

speeds = [50.0, 70.0, 60.0]                # one hemisphere per condition
angles = [0.0, 0.0, 10.0]                  # path angles, degrees
weights = aircraft.flight_condition_weights(speeds, angles, 60.0, 2.5)
lv = aircraft.interpolated_source_level(
    [h_50_level, h_70_level, h_60_climb], speeds, angles,
    60.0, 2.5, 0.0, 90.0)                  # blended level per band
```

The airspeed, not the ground speed, selects the hemisphere; the weights are
unit-invariant as long as the query matches the database units. A database
lookup triangulation can be passed as `triangles` (the NORAH database ships one
per type; the shipped tables triangulate the raw `(V, γ)` plane, so passing
them reproduces the reference implementation bin for bin). Mirrored-rotor class
members substitute `h.mirrored()` (Eq. 2, `φ → −φ`) and certification-level
offsets enter as `level_offset`.

## Flight-path kinematics

`flight_path_kinematics` derives, from a time-stamped track by central finite
differences, everything the event needs (Eq. 16-21 / Doc 32 Eq. 8-10): ground
speed, airspeed (zero wind), heading, curvature, bank angle
`Φ = atan(K·Vg²/g)` and path angle `γ = atan(ΔZ/ΔS)`. The guidance recommends
smoothing radar tracks (e.g. spline resampling to a 0.5 s cadence) before
differentiating.

```python
kin = aircraft.flight_path_kinematics(times, positions)   # positions (N, 3), m
kin.airspeed, kin.path_angle          # select the hemisphere per point
kin.bank_angle                        # tilts the hemisphere in turns
kin.plot()                            # speed and angle profiles
```

## The single event: SEL, LASmax and EPNL

`rotorcraft_event_level` runs the whole chain for one flyover at one receiver:
per track point the flight condition selects (or blends) the hemispheres, the
emission angles address the source level (the frame is oriented by the heading
and tilted by the bank angle in turns; pitch attitude is implicit in the
hemispheres), and the received one-third-octave history is expressed at
recorded time `tr = te + r/c` (Eq. 22, `c = 346.1 m/s`) and integrated:
`LASmax`, `SEL` over the full history and over the certification 10 dB-down
window (Doc 32 Eq. 27), and `EPNL` per ICAO Annex 16 (Doc 32 Eq. 28).

```python
res = aircraft.rotorcraft_event_level(
    hemispheres, speeds, angles,      # the database
    times, positions,                 # the track (m, z up)
    receiver=(120.0, 0.0),            # ground position of the microphone
    flow_resistivity="D")             # grass site
res.la_max, res.sel, res.epnl         # LASmax, SEL, EPNL
res.plot()                            # the LA(t) time history
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_flyover_event.svg" alt="A-weighted level versus recorded time for a level rotorcraft flyover: a smooth rise to LASmax over the 10 dB-down window and a slower decay, annotated with the SEL and EPNL of the event" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/rotorcraft_flyover_event_dark.svg" alt="A-weighted level versus recorded time for a level rotorcraft flyover: a smooth rise to LASmax over the 10 dB-down window and a slower decay, annotated with the SEL and EPNL of the event" style="width:82%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import aircraft

# A synthetic helicopter-like hemisphere on the standard 31-band, 10° grid.
freqs = 1000.0 * 10.0 ** (np.arange(-20, 11) / 10.0)   # 10 Hz-10 kHz thirds
az = np.arange(-90.0, 91.0, 10.0)
po = np.arange(0.0, 181.0, 10.0)
spectrum = 88.0 - 12.0 * np.log10(freqs / 100.0) ** 2   # broad low-mid hump
levels = (spectrum[None, None, :] - 0.045 * np.abs(po - 80.0)[None, :, None]
          - 0.02 * np.abs(az)[:, None, None])
h = aircraft.RotorcraftHemisphere(freqs, az, po, levels)

speed = 30.87                                           # 60 kt, in m/s
t = np.arange(0.0, 130.01, 0.5)
track = np.column_stack([np.zeros_like(t), speed * (t - 65.0),
                         np.full_like(t, 150.0)])
event = aircraft.rotorcraft_event_level(
    [h], [speed], [0.0], t, track, (120.0, 0.0), flow_resistivity="D")
event.plot()
plt.show()
```

</details>

Radar-track workflows can hand the smoothed per-point `airspeed`, `path_angle`,
`heading` and `bank_angle` directly instead of deriving them from the
positions; when they are derived, the track is in metres and seconds, so the
database airspeeds must then be in m/s.

## Ground-grid contours

`rotorcraft_noise_contour` evaluates the same event over a whole grid in one
vectorised pass per emission step and reduces each receiver's history to the
`SEL` (`metric="exposure"`) or `LASmax` (`metric="maximum"`) footprint:

```python
import numpy as np
from phonometry import aircraft

res = aircraft.rotorcraft_noise_contour(
    hemispheres, speeds, angles, times, positions,
    x=np.linspace(-2000.0, 2000.0, 81),
    y=np.linspace(-3000.0, 3000.0, 121),
    metric="exposure", flow_resistivity="D")
res.plot()                            # filled SEL contours
```

One ground class applies per run; heterogeneous ground and terrain belong to
the topography extension.

## Validation

Validated against the NORAH2 guidance Table 4 (all 31 bands), the closed-form
inverse-square spreading, the analytic rigid-ground and grazing limits of the
ground effect, off-node bilinear lookups on the reference hemispheres of all
eleven rotorcraft types, hand-checked interpolation simplices, closed-form
kinematics and the Lorentzian `SEL − LASmax` flyover integral, and end to end
against the NORAH2 prototype's ARP verification cases: emission angles to
0.01°, retarded times to 0.02 s, every step level of the hard-ground events to
0.08 dB(A) out to 18 km, `LASmax` to 0.03 dB, `SEL` to 0.05 dB over hard ground
(0.4 dB over soft ground), the 187-microphone contour grid to 0.7 dB
worst-case, `PNLTM` to 0.1 dB and `EPNL` to about 1.3 dB (the prototype's
sub-noy-floor perceived-noisiness policy differs from the published Annex 16
law). One documented divergence remains: at far range over
soft ground the prototype damps the coherent two-ray interference of guidance
Eq. 30 towards the incoherent sum (up to 4.9 dB on individual low-level steps
beyond 7 km); neither Doc 32 nor the guidance contains such a term, and this
implementation follows the published equations.

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
guidance (EASA.2020.FC.06 SC01.D1.5d) §A.3-A.5: the noise hemisphere, spherical
spreading, atmospheric attenuation (ISO 9613-1, Table 4), the Chien-Soroka
ground effect (Delany-Bazley impedance, CNOSSOS flow resistivity), the
flight-condition interpolation (Eq. 3-10), the flight-path kinematics
(Eq. 16-21 / Doc 32 Eq. 8-10), recorded time (Eq. 22) and the single-event
metrics SEL/LASmax and EPNL (Doc 32 Eq. 27/28, ICAO Annex 16 App. 2). Terrain
shielding and topography are a separate later development.

## See also

- API reference: [`aircraft.rotorcraft_noise`](/phonometry/reference/api/aeroacoustics/rotorcraft-noise/).

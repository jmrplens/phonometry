---
title: "Aircraft and wind energy"
description: "Transport and energy sources with internationally fixed noise metrics: the ICAO Annex 16 EPNL and ECAC Doc 29 airport machinery, the ECAC Doc 32 rotorcraft hemisphere method, and the IEC 61400-11 wind-turbine emission and tonal audibility."
---

Aircraft and wind turbines are noise sources important enough to have their
own internationally negotiated metrics, each fixed to the last decimal by a
certification or type-testing framework. The three pages of this section
implement those frameworks, and they share a common anatomy: a rigorously
standardised **source descriptor**, plus standardised **propagation
adjustments** that place the source at a receiver.

[Aircraft noise: Effective Perceived Noise Level](/phonometry/guides/aircraft-noise/)
covers fixed-wing certification. The **EPNL** of ICAO Annex 16 condenses a
one-third-octave time history of a flyover into a single EPNdB value through
perceived noisiness, a tone correction and a duration correction; the page
adds the IEC 61265 measurement-system verifier, the SAE ARP 5534 atmospheric
absorption used in the certification chain, and the ECAC Doc 29
noise-power-distance interpolation that turns certified levels into airport
contour inputs.

[Rotorcraft noise: the hemisphere method](/phonometry/guides/rotorcraft-noise/)
covers helicopters, whose strong directivity defeats a single-number source
level. ECAC Doc 32 instead describes the source as a **noise hemisphere**
(band levels on a grid of emission angles at a 60 m reference distance),
propagates each ray with spherical spreading, atmospheric absorption and the
Chien-Soroka ground effect, interpolates between the measured flight
conditions along the track, and integrates the received history into the
single-event SEL, LASmax and EPNL and their ground-grid contours.

[Wind-turbine noise: sound power and tonal audibility](/phonometry/guides/wind-turbine-noise/)
covers IEC 61400-11 type testing: the **apparent sound power level** that
refers the measured immission back to an equivalent point source at the rotor
centre, and the tonal-audibility chain that decides whether a blade-passing,
gearbox or generator tone is audible above its masking noise.

The shared physics connects outward: atmospheric absorption comes from the
same ISO 9613-1 model as
[Outdoor Sound Propagation](/phonometry/guides/outdoor-propagation/), and the
wind-turbine tonality test is a cousin of the tonal-audibility methods in
[Psychoacoustics](/phonometry/guides/sections/psychoacoustics/).

## Pages in this section

- [Aircraft noise: Effective Perceived Noise Level](/phonometry/guides/aircraft-noise/):
  the ICAO Annex 16 EPNL chain, IEC 61265 verifier, SAE ARP 5534 absorption
  and ECAC Doc 29 NPD interpolation.
- [Rotorcraft noise: the hemisphere method](/phonometry/guides/rotorcraft-noise/):
  the ECAC Doc 32 noise-hemisphere source model, its propagation adjustments
  and the single-event metrics and contours.
- [Wind-turbine noise: sound power and tonal audibility](/phonometry/guides/wind-turbine-noise/):
  the IEC 61400-11 apparent sound power level and tonal-audibility chain.

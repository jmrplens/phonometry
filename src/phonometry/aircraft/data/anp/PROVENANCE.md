# ANP database curated subset

This directory ships a **small curated subset** of the EASA/EUROCONTROL Aircraft
Noise and Performance (ANP) database, used by `phonometry.aircraft.anp_fleet` as
the default dataset and by the test suite as a reference oracle.

## Source

- EASA ANP database, archive **version 2.3** (released 14 October 2020), the
  semicolon-delimited CSV export (`archive_anp_v2.3.zip`).
- Public source: <https://www.aircraftnoisemodel.org/> (EASA / EUROCONTROL).

The data was developed by the aircraft manufacturers and collaboratively
reviewed by the US DOT Volpe Center, US FAA, EASA and EUROCONTROL.

## What is included

Only three representative aircraft, chosen to exercise the three Doc 29 engine
mountings and to have both a complete NPD set and a fixed-point trajectory:

| ANP ID   | Aircraft                     | Class      | Mounting   |
|----------|------------------------------|------------|------------|
| `747100` | Boeing 747-100 / JT9D        | Heavy jet  | wing       |
| `727200` | Boeing 727-200               | Narrowbody | fuselage   |
| `PA31`   | Piper PA-31 Navajo           | Propeller  | propeller  |

Per aircraft the subset keeps: the `Aircraft` metadata row, the `SEL` and
`LAmax` NPD curves (approach and departure), the default fixed-point profiles
(approach and departure) and the default weights.

## What was dropped

To keep the subset tiny and focused, the following full-database content is
**not** shipped: every other aircraft type; the `EPNL` and `PNLTM` noise
metrics; procedural-step profiles, aerodynamic/engine coefficients and spectral
classes (not consumed by the Doc 29 NPD/profile chain). The full database is
freely available at the source above; point `load_anp_database(path=...)` at a
directory of the full CSV export to use any aircraft.

## Licence / redistribution

The ANP database is distributed by EASA free of charge for aircraft noise
modelling. This subset is redistributed for reference and testing only; the
authoritative and complete dataset is the one published at the source above.
The CSV files are reproduced verbatim (rows filtered, columns and values
unchanged) so their provenance is verifiable against the published tables.

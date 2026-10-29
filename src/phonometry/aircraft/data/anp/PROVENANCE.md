# EASA ANP database (bundled)

This directory ships the **full EASA/EUROCONTROL Aircraft Noise and Performance
(ANP) database, archive version 2.3**, as the default dataset for
`phonometry.aircraft.anp_fleet` and the reference oracle for the test suite.

## Source

- EASA ANP database, archive **version 2.3** (released 14 October 2020), the
  semicolon-delimited CSV export (`archive_anp_v2.3.zip`).
- Public source: EASA's ANP data page,
  <https://www.easa.europa.eu/en/domains/environment/policy-support-and-research/aircraft-noise-and-performance-anp-data>.

The data was developed by the aircraft manufacturers and collaboratively
reviewed by the US DOT Volpe Center, US FAA, EASA and EUROCONTROL.

## Contents

The complete v2.3 CSV tables are reproduced verbatim (155 aircraft types):

| File | Content |
|------|---------|
| `Aircraft.csv` | Aircraft metadata (engine type, weights, NPD id, mounting) |
| `NPD_data.csv` | Noise-Power-Distance curves (SEL, LAmax, EPNL, PNLTM) |
| `Default_fixed_point_profiles.csv` | Ready-to-use fixed-point trajectories |
| `Default_departure_procedural_steps.csv` | Departure procedural-step profiles |
| `Default_approach_procedural_steps.csv` | Approach procedural-step profiles |
| `Default_weights.csv` | Default weights per stage length |
| `Aerodynamic_coefficients.csv` | Aerodynamic (flap-configuration) coefficients |
| `Jet_engine_coefficients.csv` | Jet-engine thrust coefficients |
| `Propeller_engine_coefficients.csv` | Propeller-engine coefficients |
| `Spectral_classes.csv` | Departure/approach spectral classes |

The `anp_fleet` loader consumes `Aircraft.csv`, `NPD_data.csv` and
`Default_fixed_point_profiles.csv` for the fixed-point trajectories, and the
engine, aerodynamic, weight and procedural-step tables for the ECAC Doc 29
Vol. 2 Appendix B performance model in `flight_performance`, which flies a
published procedure into a profile for aircraft that ship no fixed-point
trajectory. `Spectral_classes.csv` is read as well: the spectral class of
each aircraft's approach and departure NPD is what ECAC Doc 29 Vol. 2
Appendix D recalculates the NPD curves from for a non-reference atmosphere, in
`npd_atmosphere` (`ANPDatabase.spectral_class`,
`ANPDatabase.revised_npd_curves` and the `relative_humidity_percent` of the
event and contour wiring). Its classes 103 and 205 are the ones Appendix D
prints as Table D-2, and they agree with it to the last digit.

The files are the published CSVs with their upstream column layout and values
unchanged (only the `ANP2.3_` filename prefix is dropped), so their provenance
is verifiable against the published tables.

## Licence / redistribution

The tables are reproduced under EASA's copyright notice
(<https://www.easa.europa.eu/en/copyright-disclaimer>), which reads:
"Reproduction is authorised, provided the source is acknowledged, save where
otherwise stated." EASA publishes the archive of version 2.3 as a direct
download on its ANP data page, the public source above, and the archive states
no terms of its own, so that notice is the one that applies.

The source is acknowledged as the notice asks: the tables are the
EASA/EUROCONTROL Aircraft Noise and Performance (ANP) database, archive
version 2.3, developed by the aircraft manufacturers and reviewed by the US DOT
Volpe Center, the US FAA, EASA and EUROCONTROL, as set out under Source above.
Anyone who passes the tables on keeps that acknowledgement with them. The
authoritative and complete dataset remains the one EASA publishes.

phonometry's MIT licence covers phonometry's own code and documentation, not
these tables, which keep EASA's terms. Earlier versions of this note said the
tables were redistributed "for reference and non-commercial use"; that
described why they were bundled and added no condition to EASA's notice.

Point `load_anp_database(path=...)` at a directory of another release to use
different data.

← [Documentation index](README.md)

# Bibliography

Every guide in this documentation closes with two citation blocks: a
`## References` section listing the books and papers that support the physics
on the page (APA style, one bullet per source, each with a DOI or an official
publisher link, and half a sentence on what the entry supports), followed by a
final **Standards.** paragraph naming the normative documents the page
implements, clause by clause. This page collects the References entries of all
guides in one place, grouped by domain: a curated reading list, and the single
source of truth for link checking. Each entry lists the guide pages that cite
it; the list grows as guides gain their References sections.

## General acoustics

- Kinsler, L. E., Frey, A. R., Coppens, A. B., & Sanders, J. V. (2000).
  *Fundamentals of acoustics* (4th ed.). Wiley. ISBN 978-0-471-84789-2.
  [Publisher page](https://www.wiley.com/en-us/Fundamentals+of+Acoustics%2C+4th+Edition-p-9780471847892).
  The standard first course in acoustics: plane and spherical waves, acoustic
  impedance and the level definitions assumed throughout the guides.
  Cited by [Integrated and Statistical Levels](levels.md).
- Rossing, T. D. (Ed.). (2014). *Springer handbook of acoustics* (2nd ed.).
  Springer. ISBN 978-1-4939-0754-0.
  [doi:10.1007/978-1-4939-0755-7](https://doi.org/10.1007/978-1-4939-0755-7).
  A one-volume survey of every domain this library touches, from room
  acoustics to psychoacoustics and underwater sound; the cross-domain
  reference of first resort.
- Beranek, L. L., & Mellow, T. J. (2012). *Acoustics: Sound fields and
  transducers*. Academic Press. ISBN 978-0-12-391421-7.
  [doi:10.1016/C2011-0-05897-0](https://doi.org/10.1016/C2011-0-05897-0).
  Sound fields, radiation and electroacoustic transducers; supports the
  electroacoustics and sound-power material.
  Cited by [Electroacoustics](electroacoustics.md) and
  [Sound Power](sound-power.md).

## Signal processing

- Oppenheim, A. V., & Schafer, R. W. (2010). *Discrete-time signal processing*
  (3rd ed.). Pearson. ISBN 978-0-13-198842-2.
  [Open Library record](https://openlibrary.org/isbn/9780131988422).
  The digital-filter theory behind the SOS cascades, the bilinear transform
  and the multirate decimation used by the filter banks.
  Cited by [Filter Banks](filter-banks.md) and
  [Block Processing](block-processing.md).
- Smith, J. O. *Introduction to digital filters with audio applications*
  (online book). Center for Computer Research in Music and Acoustics (CCRMA),
  Stanford University.
  [ccrma.stanford.edu/~jos/filters](https://ccrma.stanford.edu/~jos/filters/).
  Free companion treatment of digital-filter design and analysis, a good next
  step after the filter-bank guides.
  Cited by [Filter Banks](filter-banks.md).

## Measurement instrumentation

- International Electrotechnical Commission. (2014). *Electroacoustics —
  Octave-band and fractional-octave-band filters — Part 1: Specifications*
  (IEC 61260-1:2014).
  [IEC webstore](https://webstore.iec.ch/en/publication/5063).
  The base-10 band edges and the class acceptance masks of the fractional
  octave banks.
  Cited by [Filter Banks](filter-banks.md).
- International Electrotechnical Commission. (2013). *Electroacoustics —
  Sound level meters — Part 1: Specifications* (IEC 61672-1:2013).
  [IEC webstore](https://webstore.iec.ch/en/publication/5708).
  The A/C/Z weightings, the exponential time weightings and the level
  metrics of the sound level meter, with the tolerance tables used for
  verification.
  Cited by [Integrated and Statistical Levels](levels.md),
  [Frequency Weighting (A, C, G, Z)](weighting.md) and
  [Time Weighting and Integration](time-weighting.md).
- International Electrotechnical Commission. (2013). *Electroacoustics —
  Sound level meters — Part 3: Periodic tests* (IEC 61672-3:2013).
  [IEC webstore](https://webstore.iec.ch/en/publication/5710).
  The periodic laboratory verification of a sound level meter.
  Cited by [Calibration and dBFS](calibration.md).
- International Electrotechnical Commission. (2017). *Electroacoustics —
  Sound calibrators* (IEC 60942:2017).
  [IEC webstore](https://webstore.iec.ch/en/publication/30045).
  The calibrator classes, level tolerances and the short-term stability
  criterion applied to calibration recordings.
  Cited by [Calibration and dBFS](calibration.md).

## Sound power and intensity

- Fahy, F. J. (1995). *Sound intensity* (2nd ed.). E&FN Spon.
  ISBN 978-0-419-19810-9.
  [doi:10.4324/9780203475386](https://doi.org/10.4324/9780203475386).
  The monograph on sound energy flux: active and reactive intensity, the
  p-p estimator and its phase-mismatch error budget.
  Cited by [Sound Power](sound-power.md) and
  [Sound Intensity (p-p)](intensity.md).
- International Organization for Standardization. (2019). *Acoustics —
  Determination of sound power levels of noise sources — Guidelines for the
  use of basic standards* (ISO 3740:2019).
  [iso.org catalogue](https://www.iso.org/standard/45107.html).
  The selection guide for the sound-power family: grades, environments,
  source-size and background criteria.
  Cited by [Sound Power](sound-power.md).
- International Organization for Standardization. (2010). *Acoustics —
  Determination of sound power levels and sound energy levels of noise
  sources using sound pressure — Precision methods for reverberation test
  rooms* (ISO 3741:2010).
  [iso.org catalogue](https://www.iso.org/standard/52053.html).
  The precision reverberation-room method.
  Cited by [Sound Power](sound-power.md).
- International Organization for Standardization. (2010). *Acoustics —
  Determination of sound power levels and sound energy levels of noise
  sources using sound pressure — Engineering methods for an essentially free
  field over a reflecting plane* (ISO 3744:2010).
  [iso.org catalogue](https://www.iso.org/standard/52055.html).
  The enveloping-surface engineering method.
  Cited by [Sound Power](sound-power.md).
- International Organization for Standardization. (2012). *Acoustics —
  Determination of sound power levels and sound energy levels of noise
  sources using sound pressure — Precision methods for anechoic rooms and
  hemi-anechoic rooms* (ISO 3745:2012).
  [iso.org catalogue](https://www.iso.org/standard/45362.html).
  The precision anechoic-room method.
  Cited by [Sound Power](sound-power.md).
- International Organization for Standardization. (1993). *Acoustics —
  Determination of sound power levels of noise sources using sound
  intensity — Part 1: Measurement at discrete points* (ISO 9614-1:1993).
  [iso.org catalogue](https://www.iso.org/standard/17427.html).
  The field indicators and the dynamic-capability criterion of intensity
  measurement.
  Cited by [Sound Intensity (p-p)](intensity.md).
- International Electrotechnical Commission. (1993). *Electroacoustics —
  Instruments for the measurement of sound intensity — Measurements with
  pairs of pressure sensing microphones* (IEC 61043:1993; adopted in Europe
  as EN 61043:1994).
  [IEC webstore](https://webstore.iec.ch/en/publication/4353).
  The p-p instrument standard: the cross-spectral estimator and the
  residual pressure-intensity index.
  Cited by [Sound Intensity (p-p)](intensity.md).

## Room acoustics

- Kuttruff, H. (2016). *Room acoustics* (6th ed.). CRC Press.
  [doi:10.1201/9781315372150](https://doi.org/10.1201/9781315372150).
  The reference monograph on sound fields in rooms: statistical decay
  theory, the Schroeder frequency, absorption and the perceptual room
  parameters.
  Cited by [Room Acoustics](room-acoustics.md),
  [Reverberation-time prediction](reverberation-prediction.md) and
  [Sound absorption in enclosed spaces](enclosed-space-absorption.md).
- Sabine, W. C. (1922). *Collected papers on acoustics*. Harvard University
  Press.
  [Free scan at the Internet Archive](https://archive.org/details/collectedpaperso00sabi).
  The founding reverberation experiments and the Sabine law.
  Cited by [Reverberation-time prediction](reverberation-prediction.md).
- Eyring, C. F. (1930). Reverberation time in "dead" rooms. *The Journal of
  the Acoustical Society of America*, 1(2A), 217-241.
  [doi:10.1121/1.1915175](https://doi.org/10.1121/1.1915175).
  The mean-free-path reverberation formula for strongly absorbing rooms.
  Cited by [Reverberation-time prediction](reverberation-prediction.md).
- Millington, G. (1932). A modified formula for reverberation. *The Journal
  of the Acoustical Society of America*, 4(1), 69-82.
  [doi:10.1121/1.1915588](https://doi.org/10.1121/1.1915588).
  The per-surface logarithmic reverberation formula.
  Cited by [Reverberation-time prediction](reverberation-prediction.md).
- Fitzroy, D. (1959). Reverberation formula which seems to be more accurate
  with nonuniform distribution of absorption. *The Journal of the
  Acoustical Society of America*, 31(7), 893-897.
  [doi:10.1121/1.1907814](https://doi.org/10.1121/1.1907814).
  The axial reverberation formula for anisotropic absorption.
  Cited by [Reverberation-time prediction](reverberation-prediction.md).
- Arau-Puchades, H. (1988). An improved reverberation formula. *Acustica*,
  65(4), 163-180.
  [Publisher record at Ingenta](https://www.ingentaconnect.com/content/dav/aaua/1988/00000065/00000004/art00003).
  The geometric-mean refinement of the axial reverberation formula.
  Cited by [Reverberation-time prediction](reverberation-prediction.md).
- Schroeder, M. R. (1965). New method of measuring reverberation time.
  *The Journal of the Acoustical Society of America*, 37(3), 409-412.
  [doi:10.1121/1.1909343](https://doi.org/10.1121/1.1909343).
  The backward integration of the squared impulse response into a decay
  curve.
  Cited by [Room Acoustics](room-acoustics.md).
- Hak, C. C. J. M., Wenmaekers, R. H. C., & van Luxemburg, L. C. J. (2012).
  Measuring room impulse responses: Impact of the decay range on derived
  room acoustic parameters. *Acta Acustica united with Acustica*, 98(6),
  907-915. [doi:10.3813/aaa.918574](https://doi.org/10.3813/aaa.918574).
  The impulse-to-noise-ratio (INR) analysis of decay-range requirements.
  Cited by [Room Acoustics](room-acoustics.md).
- Everest, F. A. (2001). *Master handbook of acoustics* (4th ed.).
  McGraw-Hill. ISBN 978-0-07-136097-5.
  [Open Library record](https://openlibrary.org/isbn/9780071360975).
  A practical room-acoustics handbook; its Fig. 7-22 worked example anchors
  the reverberation-prediction conformance suite.
  Cited by [Reverberation-time prediction](reverberation-prediction.md).
- Carrión Isbert, A. (1998). *Diseño acústico de espacios arquitectónicos*.
  Edicions UPC. ISBN 978-84-8301-252-9.
  [Open Library record](https://openlibrary.org/books/OL23159935M).
  A Spanish-language textbook on acoustic room design.
  Cited by [Reverberation-time prediction](reverberation-prediction.md).
- Beranek, L. L. (1957). Revised criteria for noise in buildings. *Noise
  Control*, 3(1), 19-27.
  [doi:10.1121/1.2369239](https://doi.org/10.1121/1.2369239).
  The original NC curves and their speech-interference rationale.
  Cited by [Room-noise criteria](room-noise.md).
- Blazier, W. E. (1997). RC Mark II: A refined procedure for rating the
  noise of heating, ventilating, and air-conditioning (HVAC) systems in
  buildings. *Noise Control Engineering Journal*, 45(6), 243-250.
  [doi:10.3397/1.2828446](https://doi.org/10.3397/1.2828446).
  The RC Mark II procedure later codified by ANSI/ASA S12.2 Annex D.
  Cited by [Room-noise criteria](room-noise.md).
- International Organization for Standardization. (2009). *Acoustics —
  Measurement of room acoustic parameters — Part 1: Performance spaces*
  (ISO 3382-1:2009).
  [iso.org catalogue](https://www.iso.org/standard/40979.html).
  Room-parameter definitions, position requirements and just-noticeable
  differences.
  Cited by [Room Acoustics](room-acoustics.md).
- International Organization for Standardization. (2008). *Acoustics —
  Measurement of room acoustic parameters — Part 2: Reverberation time in
  ordinary rooms* (ISO 3382-2:2008).
  [iso.org catalogue](https://www.iso.org/standard/36201.html).
  The accuracy grades and position counts of reverberation measurement.
  Cited by [Room Acoustics](room-acoustics.md).
- International Organization for Standardization. (2012). *Acoustics —
  Measurement of room acoustic parameters — Part 3: Open plan offices*
  (ISO 3382-3:2012).
  [iso.org catalogue](https://www.iso.org/standard/46520.html).
  The open-plan speech-privacy quantities.
  Cited by [Room Acoustics](room-acoustics.md).
- International Organization for Standardization. (2006). *Acoustics —
  Application of new measurement methods in building and room acoustics*
  (ISO 18233:2006).
  [iso.org catalogue](https://www.iso.org/standard/40408.html).
  The swept-sine and MLS acquisition of impulse responses.
  Cited by [Room Acoustics](room-acoustics.md).
- International Organization for Standardization. (2003). *Acoustics —
  Measurement of sound absorption in a reverberation room* (ISO 354:2003).
  [iso.org catalogue](https://www.iso.org/standard/34545.html).
  The reverberation-room absorption measurement behind the surface data.
  Cited by [Room Acoustics](room-acoustics.md) and
  [Sound absorption in enclosed spaces](enclosed-space-absorption.md).
- European Committee for Standardization. (2003). *Building acoustics —
  Estimation of acoustic performance of buildings from the performance of
  elements — Part 6: Sound absorption in enclosed spaces*
  (EN 12354-6:2003).
  [BSI Knowledge record (BS EN 12354-6:2003)](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-of-buildings-from-the-performance-of-elements-sound-absorption-in-enclosed-spaces).
  The absorption member of the EN 12354 prediction family.
  Cited by [Sound absorption in enclosed spaces](enclosed-space-absorption.md).
- Acoustical Society of America. (2019). *Criteria for evaluating room
  noise* (ANSI/ASA S12.2-2019).
  [ANSI webstore](https://webstore.ansi.org/standards/asa/ansiasas122019).
  The NC tangency method and the RC Mark II rating with its spectral tag.
  Cited by [Room-noise criteria](room-noise.md).

## Building acoustics

- Hopkins, C. (2007). *Sound insulation*. Butterworth-Heinemann.
  ISBN 978-0-7506-6526-1.
  [doi:10.4324/9780080550473](https://doi.org/10.4324/9780080550473).
  The comprehensive treatment of airborne and impact sound insulation:
  measurement chains, flanking transmission and the EN 12354 prediction
  framework.
  Cited by [Field Insulation Measurement and Ratings](insulation-field.md),
  [Laboratory Insulation Measurement](insulation-lab.md) and
  [Predicting Sound Insulation (EN 12354)](insulation-prediction.md).
- Vigran, T. E. (2008). *Building acoustics*. CRC Press.
  ISBN 978-0-415-42853-8.
  [doi:10.1201/9781482266016](https://doi.org/10.1201/9781482266016).
  A compact textbook on sound transmission in buildings, from single and
  double constructions to floating floors.
  Cited by [Field Insulation Measurement and Ratings](insulation-field.md),
  [Laboratory Insulation Measurement](insulation-lab.md) and
  [Dynamic stiffness of resilient materials](dynamic-stiffness.md).
- International Organization for Standardization. (2020). *Acoustics —
  Rating of sound insulation in buildings and of building elements — Part 1:
  Airborne sound insulation* (ISO 717-1:2020).
  [iso.org catalogue](https://www.iso.org/standard/77435.html).
  The reference-curve rating and the spectrum adaptation terms C and Ctr.
  Cited by [Field Insulation Measurement and Ratings](insulation-field.md).
- International Organization for Standardization. (2014). *Acoustics — Field
  measurement of sound insulation in buildings and of building elements —
  Part 1: Airborne sound insulation* (ISO 16283-1:2014).
  [iso.org catalogue](https://www.iso.org/standard/55997.html).
  The field airborne measurement method.
  Cited by [Field Insulation Measurement and Ratings](insulation-field.md).
- International Organization for Standardization. (1989). *Acoustics —
  Determination of dynamic stiffness — Part 1: Materials used under floating
  floors in dwellings* (ISO 9052-1:1989).
  [iso.org catalogue](https://www.iso.org/standard/16620.html).
  The resonance method for the dynamic stiffness per unit area, identical to
  EN 29052-1.
  Cited by [Dynamic stiffness of resilient materials](dynamic-stiffness.md).

## Structure-borne sound

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3rd ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  The standard monograph on structural vibration and its radiation:
  mobilities, power flow, vibration isolation, radiation efficiency and
  transmission across junctions.
  Cited by [Mechanical mobility and the FRF family](mechanical-mobility.md),
  [Dynamic transfer stiffness of resilient elements](transfer-stiffness.md),
  [Sound power from surface vibration](vibration-sound-power.md),
  [Structure-borne sound power of building equipment](structure-borne-power.md)
  and [Installed structure-borne sound from equipment](installed-structure-borne.md).
- International Organization for Standardization. (2011). *Mechanical
  vibration and shock — Experimental determination of mechanical mobility —
  Part 1: Basic terms and definitions, and transducer specifications*
  (ISO 7626-1:2011).
  [iso.org catalogue](https://www.iso.org/standard/50426.html).
  The FRF family and its free/blocked distinctions.
  Cited by [Mechanical mobility and the FRF family](mechanical-mobility.md).
- International Organization for Standardization. (2015). *Mechanical
  vibration and shock — Experimental determination of mechanical mobility —
  Part 2: Measurements using single-point translation excitation with an
  attached vibration exciter* (ISO 7626-2:2015).
  [iso.org catalogue](https://www.iso.org/standard/62483.html).
  The attached-exciter measurement method and its acceptance criteria.
  Cited by [Mechanical mobility and the FRF family](mechanical-mobility.md).
- International Organization for Standardization. (2008). *Acoustics and
  vibration — Laboratory measurement of vibro-acoustic transfer properties of
  resilient elements — Part 1: Principles and guidelines* (ISO 10846-1:2008).
  [iso.org catalogue](https://www.iso.org/standard/38936.html).
  The blocking-force idealisation behind the dynamic transfer stiffness.
  Cited by [Dynamic transfer stiffness of resilient elements](transfer-stiffness.md).
- International Organization for Standardization. (2009). *Acoustics —
  Determination of airborne sound power levels emitted by machinery using
  vibration measurement — Part 1: Survey method using a fixed radiation
  factor* (ISO/TS 7849-1:2009).
  [iso.org catalogue](https://www.iso.org/standard/40537.html).
  The upper-limit sound power from surface velocity with ε = 1.
  Cited by [Sound power from surface vibration](vibration-sound-power.md).
- International Organization for Standardization. (2009). *Acoustics —
  Determination of airborne sound power levels emitted by machinery using
  vibration measurement — Part 2: Engineering method including determination
  of the adequate radiation factor* (ISO/TS 7849-2:2009).
  [iso.org catalogue](https://www.iso.org/standard/40538.html).
  The engineering method with a measured band-wise radiation factor.
  Cited by [Sound power from surface vibration](vibration-sound-power.md).
- International Organization for Standardization. (1996). *Acoustics —
  Characterization of sources of structure-borne sound with respect to sound
  radiation from connected structures — Measurement of velocity at the
  contact points of machinery when resiliently mounted* (ISO 9611:1996).
  [iso.org catalogue](https://www.iso.org/standard/17424.html).
  The free-velocity characterization of resiliently mounted sources.
  Cited by [Structure-borne sound power of building equipment](structure-borne-power.md).

## Speech

- Houtgast, T., & Steeneken, H. J. M. (1985). A review of the MTF concept in
  room acoustics and its use for estimating speech intelligibility in
  auditoria. *The Journal of the Acoustical Society of America*, 77(3),
  1069-1077. [doi:10.1121/1.392224](https://doi.org/10.1121/1.392224).
  The modulation-transfer framework the Speech Transmission Index is built on.
  Cited by [Speech Transmission Index](speech-transmission.md).
- French, N. R., & Steinberg, J. C. (1947). Factors governing the
  intelligibility of speech sounds. *The Journal of the Acoustical Society of
  America*, 19(1), 90-119.
  [doi:10.1121/1.1916407](https://doi.org/10.1121/1.1916407).
  The articulation-band experiments behind the band-importance function of the
  Speech Intelligibility Index.
  Cited by [Speech Intelligibility Index](speech-intelligibility.md).

## Psychoacoustics

- Fletcher, H., & Munson, W. A. (1933). Loudness, its definition, measurement
  and calculation. *The Journal of the Acoustical Society of America*, 5(2),
  82-108. [doi:10.1121/1.1915637](https://doi.org/10.1121/1.1915637).
  The original equal-loudness measurements whose 40-phon contour became the
  A-weighting curve.
  Cited by [Frequency Weighting (A, C, G, Z)](weighting.md).
- International Organization for Standardization. (2023). *Acoustics —
  Normal equal-loudness-level contours* (ISO 226:2023).
  [iso.org catalogue](https://www.iso.org/standard/83117.html).
  The modern equal-loudness contours, successors of the Fletcher-Munson
  curves.
  Cited by [Frequency Weighting (A, C, G, Z)](weighting.md).
- Fastl, H., & Zwicker, E. (2007). *Psychoacoustics: Facts and models*
  (3rd ed.). Springer.
  [doi:10.1007/978-3-540-68888-4](https://doi.org/10.1007/978-3-540-68888-4).
  The psychoacoustic-annoyance model and the closed-form fluctuation strength
  for amplitude-modulated broadband noise.
  Cited by [Psychoacoustic annoyance](psychoacoustic-annoyance.md).
- Osses Vecchi, A., García León, R., & Kohlrausch, A. (2016). Modelling the
  sensation of fluctuation strength. *Proceedings of Meetings on Acoustics*,
  28, 050005. [doi:10.1121/2.0000410](https://doi.org/10.1121/2.0000410).
  The fluctuation-strength signal model and its Table 1 literature values.
  Cited by [Psychoacoustic annoyance](psychoacoustic-annoyance.md).
- Felix Greco, G., Merino-Martínez, R., Osses, A., & Lotinga, M. J. B. (2025).
  *SQAT: a sound quality analysis toolbox for MATLAB* (open-source software).
  [github.com/ggrecow/SQAT](https://github.com/ggrecow/SQAT),
  [doi:10.5281/zenodo.7934709](https://doi.org/10.5281/zenodo.7934709).
  The open MATLAB reference used as the numeric oracle for the
  fluctuation-strength cross-checks.
  Cited by [Psychoacoustic annoyance](psychoacoustic-annoyance.md).
- Ecma International. (2024). *ECMA-418-1: Psychoacoustic metrics for ITT
  equipment — Part 1: Prominent discrete tones* (3rd ed.).
  [Free PDF](https://ecma-international.org/wp-content/uploads/ECMA-418-1_3rd_edition_december_2024.pdf).
  The freely downloadable tone-to-noise ratio and prominence ratio methods.
  Cited by [Prominent Discrete Tones](tone-prominence.md).
- Ecma International. (2025). *ECMA-74: Measurement of airborne noise emitted
  by information technology and telecommunications equipment* (22nd ed.).
  [Free PDF](https://ecma-international.org/wp-content/uploads/ECMA-74_22nd_edition_december_2025.pdf).
  The freely downloadable parent emission standard whose Annex D delegates
  tone assessment to ECMA-418-1.
  Cited by [Prominent Discrete Tones](tone-prominence.md).
- International Organization for Standardization. (2016). *Acoustics —
  Objective method for assessing the audibility of tones in noise —
  Engineering method* (ISO/PAS 20065:2016; withdrawn, superseded by
  [ISO/TS 20065:2022](https://www.iso.org/standard/81518.html)).
  [iso.org catalogue](https://www.iso.org/standard/66941.html).
  The engineering method for the objective audibility of tones; the
  implementation follows the 2016 PAS edition.
  Cited by [Objective audibility of tones](tone-audibility.md).

## Hearing and hearing conservation

- International Organization for Standardization. (2017). *Acoustics —
  Statistical distribution of hearing thresholds related to age and gender*
  (ISO 7029:2017). [iso.org catalogue](https://www.iso.org/standard/42916.html).
  The age model of the hearing threshold and its population spread.
  Cited by [Hearing threshold](hearing-threshold.md).
- International Organization for Standardization. (2005). *Acoustics —
  Reference zero for the calibration of audiometric equipment — Part 7:
  Reference threshold of hearing under free-field and diffuse-field listening
  conditions* (ISO 389-7:2005).
  [iso.org catalogue](https://www.iso.org/standard/38976.html).
  The audiometric zero as a sound pressure level.
  Cited by [Hearing threshold](hearing-threshold.md).
- International Organization for Standardization. (2013). *Acoustics —
  Estimation of noise-induced hearing loss* (ISO 1999:2013).
  [iso.org catalogue](https://www.iso.org/standard/45103.html).
  The NIPTS model, its distribution and the HTLAN combination.
  Cited by [Noise-induced hearing loss](noise-induced-hearing-loss.md).
- Passchier-Vermeer, W. (1974). Hearing loss due to continuous exposure to
  steady-state broad-band noise. *The Journal of the Acoustical Society of
  America*, 56(5), 1585–1593.
  [doi:10.1121/1.1903482](https://doi.org/10.1121/1.1903482).
  A field study of the noise exposure-response relations later codified in
  ISO 1999.
  Cited by [Noise-induced hearing loss](noise-induced-hearing-loss.md).
- National Institute for Occupational Safety and Health. (1998). *Criteria for
  a recommended standard: Occupational noise exposure — Revised criteria 1998*
  (DHHS/NIOSH Publication No. 98-126).
  [doi:10.26616/NIOSHPUB98126](https://doi.org/10.26616/NIOSHPUB98126),
  [free PDF](https://www.cdc.gov/niosh/docs/98-126/pdfs/98-126.pdf).
  The freely available criteria document behind the 85 dB(A) recommended
  exposure limit and the hearing-conservation and fence discussion.
  Cited by [Noise-induced hearing loss](noise-induced-hearing-loss.md) and
  [Occupational noise exposure](occupational-exposure.md).
- International Organization for Standardization. (2009). *Acoustics —
  Determination of occupational noise exposure — Engineering method*
  (ISO 9612:2009). [iso.org catalogue](https://www.iso.org/standard/41718.html).
  The three measurement strategies and the Annex C uncertainty budget.
  Cited by [Occupational noise exposure](occupational-exposure.md).
- European Parliament and Council. (2003). *Directive 2003/10/EC on the
  minimum health and safety requirements regarding the exposure of workers to
  the risks arising from physical agents (noise)*. Official Journal of the
  European Union.
  [eur-lex.europa.eu](https://eur-lex.europa.eu/eli/dir/2003/10/oj/eng).
  The EU exposure action and limit values for occupational noise.
  Cited by [Occupational noise exposure](occupational-exposure.md).

## Human vibration

- Griffin, M. J. (1996). *Handbook of human vibration*. Academic Press.
  ISBN 978-0-12-303041-2.
  [Publisher page](https://shop.elsevier.com/books/handbook-of-human-vibration/griffin/978-0-12-303041-2).
  The standard monograph on whole-body and hand-transmitted vibration: the
  biodynamics, discomfort and health-effect evidence behind the weightings,
  dose measures and exposure-response guidance of the vibration guides.
  Cited by [Human Vibration](human-vibration.md) and
  [Multiple-shock whole-body vibration](multiple-shock-vibration.md).
- Mansfield, N. J. (2004). *Human response to vibration*. CRC Press.
  ISBN 978-0-415-28239-0.
  [Publisher page](https://www.routledge.com/Human-Response-to-Vibration/Mansfield/p/book/9780415282390).
  A compact modern textbook on the ISO 2631-1 and ISO 5349 evaluation chains,
  from perception and comfort to the occupational exposure limits.
  Cited by [Human Vibration](human-vibration.md).

## Metrology

- Joint Committee for Guides in Metrology. (2008). *Evaluation of measurement
  data — Guide to the expression of uncertainty in measurement* (JCGM
  100:2008, the GUM). BIPM.
  [doi:10.59161/JCGM100-2008E](https://doi.org/10.59161/JCGM100-2008E),
  [free PDF](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf).
  The law of propagation of uncertainty implemented by the uncertainty module.
  Cited by [Measurement uncertainty](gum-uncertainty.md).
- Joint Committee for Guides in Metrology. (2008). *Evaluation of measurement
  data — Supplement 1 to the "Guide to the expression of uncertainty in
  measurement" — Propagation of distributions using a Monte Carlo method*
  (JCGM 101:2008). BIPM.
  [doi:10.59161/JCGM101-2008](https://doi.org/10.59161/JCGM101-2008),
  [free PDF](https://www.bipm.org/documents/20126/2071204/JCGM_101_2008_E.pdf).
  The Monte Carlo propagation of distributions implemented by the Monte Carlo
  uncertainty engine.
  Cited by [Measurement uncertainty](gum-uncertainty.md).
- International Organization for Standardization. (2020). *Acoustics —
  Determination and application of measurement uncertainties in building
  acoustics — Part 1: Sound insulation* (ISO 12999-1:2020).
  [iso.org catalogue](https://www.iso.org/standard/73930.html).
  The domain-specific reproducibility budget for building-acoustics
  single-number ratings, the companion to the general GUM machinery.
  Cited by [Measurement uncertainty](gum-uncertainty.md).

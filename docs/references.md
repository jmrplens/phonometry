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
  Cited by [Electroacoustics](electroacoustics.md).

## Signal processing

- Oppenheim, A. V., & Schafer, R. W. (2010). *Discrete-time signal processing*
  (3rd ed.). Pearson. ISBN 978-0-13-198842-2.
  [Open Library record](https://openlibrary.org/isbn/9780131988422).
  The digital-filter theory behind the SOS cascades, the bilinear transform
  and the multirate decimation used by the filter banks.
- Smith, J. O. *Introduction to digital filters with audio applications*
  (online book). Center for Computer Research in Music and Acoustics (CCRMA),
  Stanford University.
  [ccrma.stanford.edu/~jos/filters](https://ccrma.stanford.edu/~jos/filters/).
  Free companion treatment of digital-filter design and analysis, a good next
  step after the filter-bank guides.

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

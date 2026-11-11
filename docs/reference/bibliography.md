← [Documentation index](../README.md)

# Bibliography

Every guide in this documentation closes with two citation sections: a
`## References` section listing the books and papers that support the physics
on the page (APA style, one bullet per source, each with half a sentence on
what the entry supports and with its DOI or official publisher link where it
has one), followed by a
`## Standards` section naming the normative documents behind the page, clause
by clause, with what each one is to it: the ones the page implements, and those
it only requires, cites or compares with, which the site prints in its
bibliography but leaves out of the page's standards chips and search field.
This page collects every work the pages of the documentation site cite, the
guides, the theory pages and the published catalogues alike, once each, grouped
by area, and ends each entry with every page that cites it. It is written from
the same data as the site's
[bibliography](https://docs.jmrp.io/phonometry/reference/bibliography/), the references of every
page, so each entry gives the work as the site does; a page with no copy in this
folder, a published catalogue, is linked on the site. Within an area the entries
run in the order of a reference list, by author. The list below is written by
`site/scripts/mirror-bibliography.mjs` from those references, and the docs
workflow fails while it is not what they write.

## General acoustics

The three works here are the ones to reach for when the question does not
belong to any single area. Kinsler et al. is the first course, Rossing the
one-volume survey of every domain this library touches, and Beranek and Mellow
the treatment to open when the question is radiation or transduction. Bies,
Hansen and Howard and Norton and Karczub are the two engineering handbooks the
guides lean on most across areas: the first for room relations and enclosures,
the second for its worked octave-band problems, which several guides are built
around.

- Beranek, L. L., & Mellow, T. J. (2012). *Acoustics: Sound fields and transducers*. Academic Press. https://doi.org/10.1016/C2011-0-05897-0
  ISBN 978-0-12-391421-7. Sound fields, radiation and electroacoustic transducers; supports the electroacoustics and sound-power material.
  Cited by [Sound Power](../devices/emission/sound-power.md), [Sound Power by Pressure Methods](../devices/emission/sound-power-pressure.md), [Sound Power in the Reverberation Room](../devices/emission/sound-power-reverberation.md), [Loudspeaker Characterisation (IEC 60268-5)](../devices/electroacoustics/loudspeakers.md) and [Microphone Characterisation (IEC 60268-4)](../devices/electroacoustics/microphones.md).
- Beranek, L. L., & Mellow, T. J. (2019). [*Acoustics: Sound fields, transducers and vibration*](https://shop.elsevier.com/books/acoustics-sound-fields-transducers-and-vibration/beranek/978-0-12-815227-0) (2nd ed.). Academic Press.
  ISBN 978-0-12-815227-0. The edition the conformance report reads for the baffled-piston radiation impedance and directivity (Eqs. 13.117, 13.118, 4.151, 13.102, numbered as in the first edition), and the one whose Table 7.1 gives the Delany-Bazley amplitudes discussed in [Source properties that are not errata](https://docs.jmrp.io/phonometry/reference/errata/not-errata/).
  Cited by [Loudspeaker Characterisation (IEC 60268-5)](../devices/electroacoustics/loudspeakers.md).
- Bies, D. A., Hansen, C. H., & Howard, C. Q. (2017). *Engineering noise control* (5th ed.). CRC Press. https://doi.org/10.1201/9781351228152
  ISBN 978-1-4987-2405-0. The steady-state room relations (section 6.4, Eqs. 6.43-6.44) behind `steady_state_spl` and `room_constant`, the enclosure insertion loss of section 7.4.2 (Eqs. 7.103, 7.111) that is the library default enclosure model, and Appendix D, which collects the porous-material coefficient sets of Table D.1 and the layered-construction recursions (Eqs. D.91-D.99).
  Cited by [Time Weighting](../signals/levels/time-weighting.md), [Integrated and Statistical Levels](../signals/levels/levels.md), [Calibration and dBFS](../signals/metrology/calibration.md), [Image Sources and the Steady-State Room Field](../buildings/rooms/room-image-sources.md), [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md), [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md), [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md), [Silencers](../devices/noise-control/silencers.md), [Duct-Borne Noise: Fan to Room](../devices/noise-control/duct-path.md), [Room to Room: Partition, Receiving Room, Criterion](../devices/noise-control/room-to-room.md), [Industrial Noise Control: HVAC and Enclosures](../devices/noise-control/noise-control.md), [Theory: Rooms and Buildings](theory/rooms-buildings.md), [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/), [Catalogue of absorption coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/absorption-coefficients/), [Catalogue of transmission loss](https://docs.jmrp.io/phonometry/reference/catalogues/transmission-loss/), [Catalogue of ground surfaces](https://docs.jmrp.io/phonometry/reference/catalogues/ground-surfaces/), [Catalogue of gases](https://docs.jmrp.io/phonometry/reference/catalogues/gases/) and [Catalogue of fluids](https://docs.jmrp.io/phonometry/reference/catalogues/fluids/).
- Kinsler, L. E., Frey, A. R., Coppens, A. B., & Sanders, J. V. (2000). [*Fundamentals of acoustics*](https://www.wiley.com/en-us/Fundamentals+of+Acoustics%2C+4th+Edition-p-9780471847892) (4th ed.). Wiley.
  ISBN 978-0-471-84789-2. The standard first course in acoustics: plane and spherical waves, acoustic impedance and the level definitions assumed throughout the guides.
  Cited by [Integrated and Statistical Levels](../signals/levels/levels.md).
- Norton, M. P., & Karczub, D. G. (2003). *Fundamentals of noise and vibration analysis for engineers* (2nd ed.). Cambridge University Press. https://doi.org/10.1017/CBO9781139163927
  The sound power models of section 4.6 (Table 4.5, Eqs. 4.53-4.56), the room-to-room power balance of section 4.9 (Eqs. 4.92-4.101), the enclosure design equation of section 4.10 (Eqs. 4.102-4.115), the plateau method for panel transmission loss of section 3.9 (Table 3.1), the higher-order acoustic modes of a rigid circular duct of section 7.2 (Table 7.1) and the worked problems 4.16, 4.18 and 4.21 with their printed octave-band answers.
  Cited by [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md), [Plate junctions: wave approach and experimental SEA](../vibration/structural/junction-transmission.md), [Machine fault frequencies](../vibration/machinery/machine-diagnostics.md), [Duct-Borne Noise: Fan to Room](../devices/noise-control/duct-path.md), [Room to Room: Partition, Receiving Room, Criterion](../devices/noise-control/room-to-room.md), [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/), [Catalogue of plateau-method constants](https://docs.jmrp.io/phonometry/reference/catalogues/plateau-method-constants/) and [Catalogue of fluids](https://docs.jmrp.io/phonometry/reference/catalogues/fluids/).
- Rossing, T. D. (Ed.). (2014). *Springer handbook of acoustics* (2nd ed.). Springer. https://doi.org/10.1007/978-1-4939-0755-7
  ISBN 978-1-4939-0754-0. A one-volume survey of every domain this library touches, from room acoustics to psychoacoustics and underwater sound; the cross-domain reference of first resort.
  Cited by [Catalogue of orthotropic wood](https://docs.jmrp.io/phonometry/reference/catalogues/orthotropic-wood/), [Catalogue of transmission loss](https://docs.jmrp.io/phonometry/reference/catalogues/transmission-loss/), [Catalogue of the nonlinearity parameter B/A](https://docs.jmrp.io/phonometry/reference/catalogues/nonlinearity-parameter-ba/) and [Catalogue of the nonlinearity parameter of solids](https://docs.jmrp.io/phonometry/reference/catalogues/nonlinearity-parameter-of-solids/).
- Vér, I. L., & Beranek, L. L. (2006). *Noise and vibration control engineering: Principles and applications* (2nd ed.). Wiley. https://doi.org/10.1002/9780470172568
  ISBN 978-0-471-44942-3. The companion treatment of ducts, silencers and enclosures, and the handbook this library reads its commercial damping materials from: Table 14.1 of chapter 14, "Structural Damping", by Eric E. Ungar and Jeffrey A. Zapfe, which is the only table in the corpus that gives a loss factor with the temperature and the frequency at which it peaks.
  Cited by [Silencers](../devices/noise-control/silencers.md), [Industrial Noise Control: HVAC and Enclosures](../devices/noise-control/noise-control.md), [Catalogue of damping materials](https://docs.jmrp.io/phonometry/reference/catalogues/damping-materials/) and [Catalogue of resistive facings](https://docs.jmrp.io/phonometry/reference/catalogues/resistive-facings/).

## Signal analysis

Oppenheim and Schafer is the filter-theory backbone, and Smith the free
companion when the question is design rather than analysis. Open Bendat and
Piersol whenever a spectral estimate needs an error bar: it is the reference
behind every random-error figure in this area, and the multiple-coherence
chapter has no equivalent elsewhere. The papers are here as sources rather than
as reading, each pinning one estimator: Welch for the overlapped-segment
variance, Harris for the window figures of merit, Thomson and Percival and
Walden for the multitaper method, Knapp and Carter for time delay, McFadden for
synchronous averaging, Golay for the complementary pairs.

- American National Standards Institute. (1983). [*Specification for sound level meters*](https://webstore.ansi.org/standards/asa/ansis11983r20064a1985) (ANSI S1.4-1983).
  Cited by [Special Weightings (G, B, D, AU)](../signals/levels/special-weightings.md) and [Time Weighting](../signals/levels/time-weighting.md).
- American National Standards Institute. (2004). [*Specification for octave-band and fractional-octave-band analog and digital filters*](https://webstore.ansi.org/standards/asa/ansis1112004) (ANSI S1.11-2004). Acoustical Society of America.
  Cited by [Octave and Fractional-Octave Filter Banks](../signals/filters/filter-banks.md), [Filter Architecture Gallery](../signals/filters/filter-gallery.md) and [Filter Class Verification (IEC 61260-1)](../signals/filters/filter-compliance.md).
- Bendat, J. S., & Piersol, A. G. (2010). *Random data: Analysis and measurement procedures* (4th ed.). Wiley. https://doi.org/10.1002/9781118032428
  ISBN 978-0-470-24877-5. The reference for the Welch spectral estimators and their statistical quality, and for the multiple-input/output coherence functions of Chapter 7 (multiple and partial coherence, conditioned spectra) with the Section 9.3 error formulas implemented by `miso_coherence`. Also the correlation and time-delay formulas, the Hilbert-envelope chapter and the log-magnitude/phase Hilbert relation of the minimum-phase utilities.
  Cited by [Multichannel and Performance](../signals/filters/multichannel.md), [Calibrated spectral analysis](../signals/spectra/spectral-analysis.md), [Multiple and partial coherence](../signals/spectra/miso-coherence.md), [Time-frequency analysis](../signals/spectra/time-frequency.md), [Cepstrum, echoes and the envelope spectrum](../signals/spectra/cepstrum-echoes.md), [Correlation, time delay and envelope](../signals/spectra/correlation-delay.md), [Test signals and sample-rate tools](../signals/spectra/test-signals.md), [Data qualification: stationarity and peaks](../signals/metrology/data-qualification.md), [Electroacoustics: distortion and frequency response](../devices/electroacoustics/electroacoustics.md) and [Swept-sine distortion and phase utilities](../devices/electroacoustics/swept-sine-distortion.md).
- Bennett, R. L., & Pearsons, K. S. (1981). [*Handbook of Aircraft Noise Metrics*](https://ntrs.nasa.gov/citations/19810013341) (NASA CR-3406). NASA.
  Cited by [Special Weightings (G, B, D, AU)](../signals/levels/special-weightings.md).
- Bristow-Johnson, R. (2021). [*Audio EQ Cookbook*](https://www.w3.org/TR/audio-eq-cookbook/). W3C Working Group Note (ed. R. Toy), 8 June 2021.
  The biquad coefficient recipes (peaking, shelves, low/high-pass, band-pass, notch, all-pass) and their Q / bandwidth / shelf-slope parameterization, implemented verbatim by `ParametricEQ`.
  Cited by [Octave and Fractional-Octave Filter Banks](../signals/filters/filter-banks.md).
- Golay, M. J. E. (1961). Complementary series. *IRE Transactions on Information Theory*, *7*(2), 82-87. https://doi.org/10.1109/TIT.1961.1057620
  The original construction of the complementary pairs of §1.
  Cited by [System measurement: Golay, shaped sweeps, inversion](../signals/spectra/system-measurement.md).
- Harris, F. J. (1978). On the use of windows for harmonic analysis with the discrete Fourier transform. *Proceedings of the IEEE*, *66*(1), 51-83. https://doi.org/10.1109/PROC.1978.10837
  The window figures of merit (Table 1): equivalent noise bandwidth, coherent gain, scalloping loss, worst-case processing loss, highest sidelobe level and main-lobe width, computed by `window_metrics` for any scipy taper.
  Cited by [Calibrated spectral analysis](../signals/spectra/spectral-analysis.md) and [Time-frequency analysis](../signals/spectra/time-frequency.md).
- Havelock, D., Kuwano, S., & Vorländer, M. (Eds.). (2008). *Handbook of signal processing in acoustics*. Springer. https://doi.org/10.1007/978-0-387-30441-0
  Part I Chapter 6 (Xiang, Digital Sequences): the Golay recursion of §1, the complementary-autocorrelation identity of Eq. (2) and the frequency-domain recovery procedure of Eq. (4) and Fig. 2. ISBN 978-0-387-77698-9.
  Cited by [Cepstrum, echoes and the envelope spectrum](../signals/spectra/cepstrum-echoes.md) and [System measurement: Golay, shaped sweeps, inversion](../signals/spectra/system-measurement.md).
- International Electrotechnical Commission. (1976). *Frequency weighting for the measurement of aircraft noise (D-weighting)* (IEC 537:1976 (withdrawn)).
  Cited by [Special Weightings (G, B, D, AU)](../signals/levels/special-weightings.md).
- International Electrotechnical Commission. (1979). *Sound level meters* (IEC 651:1979).
  Cited by [Frequency Weighting (A, C, Z)](../signals/levels/weighting.md).
- International Electrotechnical Commission. (1982). [*Scales and sizes for plotting frequency characteristics and polar diagrams*](https://webstore.iec.ch/en/publication/1176) (IEC 60263:1982).
  The scale proportions of the characteristic graphs: one frequency decade equal to 25 dB on the ordinate, and the polar diagram on a 25 dB reference-circle radius.
  Cited by [Loudspeaker Characterisation (IEC 60268-5)](../devices/electroacoustics/loudspeakers.md) and [Microphone Characterisation (IEC 60268-4)](../devices/electroacoustics/microphones.md).
- International Electrotechnical Commission. (1985). [*Sound system equipment — Part 1: General*](https://webstore.iec.ch/en/publication/1204) (IEC 60268-1:1985).
  The simulated programme signal of Clause 7, and Appendix A: the quasi-peak network and meter of Table AI, Figure A1 and Tables AII and AIII, and the tone bursts of Clause A2, which start at the zero crossing of the tone with an integral number of full periods, repeat in trains at a stated repetition rate and last the burst durations of Table AII.
  Cited by [Test signals and sample-rate tools](../signals/spectra/test-signals.md), [Headphones and Earphones (IEC 60268-7)](../devices/electroacoustics/headphones.md) and [Quasi-peak programme meter (ITU-R BS.468-4)](../devices/broadcast/quasi-peak.md).
- International Electrotechnical Commission. (1990). [*Filters for the measurement of audible sound in the presence of ultrasound*](https://webstore.iec.ch/en/publication/4296) (IEC 61012:1990).
  Cited by [Special Weightings (G, B, D, AU)](../signals/levels/special-weightings.md).
- International Electrotechnical Commission. (1993). [*Electroacoustics — Specifications for personal sound exposure meters*](https://webstore.iec.ch/en/publication/5054) (IEC 61252:1993).
  Cited by [Integrated and Statistical Levels](../signals/levels/levels.md).
- International Electrotechnical Commission. (1995). [*Electroacoustics — Octave-band and fractional-octave-band filters*](https://webstore.iec.ch/en/publication/5065) (IEC 61260:1995).
  Cited by [Filter Class Verification (IEC 61260-1)](../signals/filters/filter-compliance.md).
- International Electrotechnical Commission. (2003). [*Sound system equipment – Part 5: Loudspeakers*](https://webstore.iec.ch/en/publication/1224) (IEC 60268-5:2003+A1:2007).
  The rated loudspeaker characteristics: rated impedance, rated frequency range, characteristic sensitivity referred to 1 W at 1 m, the effective frequency range against the -10 dB band, the directivity index and the total harmonic distortion against frequency.
  Cited by [Loudspeaker Characterisation (IEC 60268-5)](../devices/electroacoustics/loudspeakers.md).
- International Electrotechnical Commission. (2013). [*Electroacoustics — Sound level meters — Part 1: Specifications*](https://webstore.iec.ch/en/publication/5708) (IEC 61672-1:2013).
  The A/C/Z weightings, the exponential time weightings and the level metrics of the sound level meter, with the tolerance tables used for verification.
  Cited by [Build a sound level meter](../signals/sound-level-meter.md), [Block Processing](../signals/filters/block-processing.md), [Multichannel and Performance](../signals/filters/multichannel.md), [Frequency Weighting (A, C, Z)](../signals/levels/weighting.md), [Time Weighting](../signals/levels/time-weighting.md), [Integrated and Statistical Levels](../signals/levels/levels.md), [Compliance and verification](../signals/metrology/compliance-verification.md), [Free-Field Corrections of a Sound Level Meter (IEC 62585)](../signals/metrology/free-field-corrections.md), [Periodic Tests of a Sound Level Meter (IEC 61672-3)](../signals/metrology/sound-level-meter-periodic-tests.md), [Headphones and Earphones (IEC 60268-7)](../devices/electroacoustics/headphones.md) and [Theory: Signal Analysis](theory/signal-analysis.md).
- International Electrotechnical Commission. (2013). [*Electroacoustics — Sound level meters — Part 3: Periodic tests*](https://webstore.iec.ch/en/publication/5710) (IEC 61672-3:2013).
  The periodic laboratory verification of a sound level meter.
  Cited by [Calibration and dBFS](../signals/metrology/calibration.md), [Compliance and verification](../signals/metrology/compliance-verification.md) and [Periodic Tests of a Sound Level Meter (IEC 61672-3)](../signals/metrology/sound-level-meter-periodic-tests.md).
- International Electrotechnical Commission. (2014). [*Electroacoustics — Octave-band and fractional-octave-band filters — Part 1: Specifications*](https://webstore.iec.ch/en/publication/5063) (IEC 61260-1:2014).
  The base-10 band edges and the class acceptance masks of the fractional octave banks.
  Cited by [Build a sound level meter](../signals/sound-level-meter.md), [Octave and Fractional-Octave Filter Banks](../signals/filters/filter-banks.md), [Filter Architecture Gallery](../signals/filters/filter-gallery.md), [Filter Class Verification (IEC 61260-1)](../signals/filters/filter-compliance.md), [Block Processing](../signals/filters/block-processing.md), [Multichannel and Performance](../signals/filters/multichannel.md), [Compliance and verification](../signals/metrology/compliance-verification.md), [Reporting and source qualification (ISO 3382-1)](../buildings/rooms/reporting-and-qualification.md), [Control Valve Noise (IEC 60534-8-3)](../devices/noise-control/control-valve-noise.md), [Hydrodynamic Valve Noise (IEC 60534-8-4)](../devices/noise-control/valve-cavitation.md) and [Theory: Signal Analysis](theory/signal-analysis.md).
- International Electrotechnical Commission. (2014). [*Sound system equipment – Part 4: Microphones*](https://webstore.iec.ch/en/publication/1221) (IEC 60268-4:2014).
  The rated microphone characteristics: free-field sensitivity and its level re 1 V/Pa, the frequency response and the effective frequency range against the tolerance limits, the directional pattern and the directivity index, the overload sound pressure level, the equivalent sound pressure level due to inherent noise, and the rated impedances and power supply.
  Cited by [Microphone Characterisation (IEC 60268-4)](../devices/electroacoustics/microphones.md).
- International Electrotechnical Commission. (2016). [*Electroacoustics — Octave-band and fractional-octave-band filters — Part 2: Pattern-evaluation tests*](https://webstore.iec.ch/en/publication/24398) (IEC 61260-2:2016).
  Cited by [Filter Class Verification (IEC 61260-1)](../signals/filters/filter-compliance.md) and [Compliance and verification](../signals/metrology/compliance-verification.md).
- International Electrotechnical Commission. (2016). [*Electroacoustics — Octave-band and fractional-octave-band filters — Part 3: Periodic tests*](https://webstore.iec.ch/en/publication/24399) (IEC 61260-3:2016).
  Cited by [Filter Class Verification (IEC 61260-1)](../signals/filters/filter-compliance.md) and [Compliance and verification](../signals/metrology/compliance-verification.md).
- International Electrotechnical Commission. (2017). [*Electroacoustics — Sound calibrators*](https://webstore.iec.ch/en/publication/30045) (IEC 60942:2017).
  The calibrator classes, level tolerances and the short-term stability criterion applied to calibration recordings.
  Cited by [Build a sound level meter](../signals/sound-level-meter.md), [Calibration and dBFS](../signals/metrology/calibration.md), [Compliance and verification](../signals/metrology/compliance-verification.md) and [Periodic Tests of a Sound Level Meter (IEC 61672-3)](../signals/metrology/sound-level-meter-periodic-tests.md).
- International Organization for Standardization. (1995). [*Acoustics — Frequency-weighting characteristic for infrasound measurements*](https://www.iso.org/standard/13813.html) (ISO 7196:1995).
  Cited by [Special Weightings (G, B, D, AU)](../signals/levels/special-weightings.md).
- International Organization for Standardization. (1997). [*Acoustics — Preferred frequencies*](https://www.iso.org/standard/1350.html) (ISO 266:1997).
  Cited by [Octave and Fractional-Octave Filter Banks](../signals/filters/filter-banks.md).
- International Organization for Standardization. (2015). *Acoustics. Preferred reference values for acoustical and vibratory levels* (ISO 1683:2015).
  Cited by [Integrated and Statistical Levels](../signals/levels/levels.md) and [Underwater acoustics: radiated noise and pile driving](../underwater/underwater-acoustics.md).
- International Organization for Standardization. (2021). [*Mechanical vibration and shock — Mechanical mounting of accelerometers*](https://www.iso.org/standard/78160.html) (ISO 5348:2021).
  Cited by [Cepstrum, echoes and the envelope spectrum](../signals/spectra/cepstrum-echoes.md).
- Kirkeby, O., & Nelson, P. A. (1999). [Digital filter design for inversion problems in sound reproduction](https://aes.org/publications/elibrary-page/?id=12098). *Journal of the Audio Engineering Society*, *47*(7/8), 583-595.
  Cited by [System measurement: Golay, shaped sweeps, inversion](../signals/spectra/system-measurement.md).
- Knapp, C. H., & Carter, G. C. (1976). The generalized correlation method for estimation of time delay. *IEEE Transactions on Acoustics, Speech, and Signal Processing*, *24*(4), 320-327. https://doi.org/10.1109/TASSP.1976.1162830
  The GCC framework, the Table I weightings (Roth, SCOT, PHAT) and their conditions, and the maximum-likelihood (Hannan-Thomson) processor.
  Cited by [Correlation, time delay and envelope](../signals/spectra/correlation-delay.md).
- McFadden, P. D. (1987). A revised model for the extraction of periodic waveforms by time domain averaging. *Mechanical Systems and Signal Processing*, *1*(1), 83-95. https://doi.org/10.1016/0888-3270(87)90085-9
  The comb-filter model of synchronous averaging (Eq. 8, magnitude Eq. 9), the revised finite-record model that yields an exactly periodic result, and the observation that a non-harmonic interfering order is best rejected by choosing the number of averages so that a comb node lands on it, not by the habitual power of two.
  Cited by [Time synchronous averaging](../signals/spectra/synchronous-averaging.md).
- Oppenheim, A. V., & Schafer, R. W. (2010). [*Discrete-time signal processing*](https://openlibrary.org/isbn/9780131988422) (3rd ed.). Pearson.
  ISBN 978-0-13-198842-2. The digital-filter theory behind the SOS cascades, the bilinear transform and the multirate decimation used by the filter banks.
  Cited by [Octave and Fractional-Octave Filter Banks](../signals/filters/filter-banks.md), [Block Processing](../signals/filters/block-processing.md) and [Theory: Signal Analysis](theory/signal-analysis.md).
- Percival, D. B., & Walden, A. T. (1993). *Spectral analysis for physical applications: Multitaper and conventional univariate techniques*. Cambridge University Press. https://doi.org/10.1017/CBO9780511622762
  ISBN 978-0-521-43541-3. The multitaper development (Chapter 7) behind `multitaper_psd` and the Slepian-sequence eigenvalue tables that anchor its test oracle.
  Cited by [Calibrated spectral analysis](../signals/spectra/spectral-analysis.md).
- Smith, J. O. (n.d.). [*Introduction to digital filters with audio applications*](https://ccrma.stanford.edu/~jos/filters/). Center for Computer Research in Music and Acoustics (CCRMA), Stanford University.
  Free companion treatment of digital-filter design and analysis, a good next step after the filter-bank guides.
  Cited by [Octave and Fractional-Octave Filter Banks](../signals/filters/filter-banks.md), [Filter Architecture Gallery](../signals/filters/filter-gallery.md) and [Theory: Signal Analysis](theory/signal-analysis.md).
- Thomson, D. J. (1982). Spectrum estimation and harmonic analysis. *Proceedings of the IEEE*, *70*(9), 1055-1096. https://doi.org/10.1109/PROC.1982.12433
  The multitaper method: Slepian tapers, eigenspectra and the adaptive weights implemented by `multitaper_psd`.
  Cited by [Calibrated spectral analysis](../signals/spectra/spectral-analysis.md).
- Welch, P. D. (1967). The use of fast Fourier transform for the estimation of power spectra: A method based on time averaging over short, modified periodograms. *IEEE Transactions on Audio and Electroacoustics*, *15*(2), 70-73. https://doi.org/10.1109/TAU.1967.1161901
  The overlapped-segment variance formula behind the effective number of averages (Bendat & Piersol Section 11.5.2.2, Ref. 11).
  Cited by [Calibrated spectral analysis](../signals/spectra/spectral-analysis.md).

## Files

Standards rather than books: the file layer implements published container
and metadata specifications, and each entry pins the piece of the module
that follows it. Lipshitz, Wannamaker and Vanderkooy is the one paper, and
it settles a single default: what dither to offer, and when offering it
would be a disservice.

- Alliance for Open Media. (n.d.). [*SVT-AV1*](https://gitlab.com/AOMediaCodec/SVT-AV1).
  Cited by [Writing animations and FDTD runs to video](../io/videos.md).
- European Broadcasting Union. (1999). [*Format for CodingHistory field in Broadcast Wave Format files, BWF*](https://tech.ebu.ch/publications/r098) (EBU R 98).
  Cited by [Reading and writing measurement audio](../io/audio-files.md).
- European Broadcasting Union. (2011). [*Specification of the Broadcast Wave Format (BWF) — A format for audio data files in broadcasting, Version 2.0*](https://tech.ebu.ch/publications/tech3285) (EBU Tech 3285).
  The `bext` chunk read and written field by field at its published offsets, including the version-2 loudness values.
  Cited by [Reading and writing measurement audio](../io/audio-files.md).
- FFmpeg project. (n.d.). [*FFmpeg codecs documentation*](https://ffmpeg.org/ffmpeg-codecs.html).
  Cited by [Writing animations and FDTD runs to video](../io/videos.md).
- International Organization for Standardization. (2010). [*Acoustics — Laboratory measurement of sound insulation of building elements — Part 2: Measurement of airborne sound insulation*](https://www.iso.org/standard/42088.html) (ISO 10140-2:2010).
  Cited by [Your own catalogues](../io/material-catalogues.md), [Laboratory Insulation Measurement](../buildings/insulation/insulation-lab.md) and [Reading a material datasheet](../materials/reading-a-datasheet.md).
- International Telecommunication Union. (2025). [*Long-form file format for the international exchange of audio programme materials with metadata*](https://www.itu.int/rec/R-REC-BS.2088/en) (Recommendation ITU-R BS.2088-2).
  The RF64/BW64 64-bit container an overnight recording promotes to, resolved through its `ds64` sizes.
  Cited by [Reading and writing measurement audio](../io/audio-files.md).
- Internet Engineering Task Force. (2005). [*Common Format and MIME Type for Comma-Separated Values (CSV) Files*](https://www.rfc-editor.org/info/rfc4180/) (RFC 4180).
  Cited by [Your own catalogues](../io/material-catalogues.md).
- Internet Engineering Task Force. (2013). [*JavaScript Object Notation (JSON) Pointer*](https://www.rfc-editor.org/info/rfc6901/) (RFC 6901).
  Cited by [Your own catalogues](../io/material-catalogues.md).
- Internet Engineering Task Force. (2017). [*The JavaScript Object Notation (JSON) Data Interchange Format*](https://www.rfc-editor.org/info/rfc8259/) (RFC 8259).
  Cited by [Your own catalogues](../io/material-catalogues.md).
- Internet Engineering Task Force. (2024). [*Free Lossless Audio Codec*](https://datatracker.ietf.org/doc/rfc9639/) (RFC 9639).
  The lossless codec behind the FLAC archive route, and the reason a round trip can return bit-identical codes.
  Cited by [Reading and writing measurement audio](../io/audio-files.md).
- Lipshitz, S. P., Wannamaker, R. A., & Vanderkooy, J. (1992). [Quantization and dither: A theoretical survey](https://aes.org/publications/elibrary-page/?id=7047). *Journal of the Audio Engineering Society*, *40*(5), 355-375.
  Why the optional dither is triangular-PDF at one LSB and offered only at 16 bits.
  Cited by [Reading and writing measurement audio](../io/audio-files.md).
- Wright, A., Andrews, H., & Hutton, B. (2022). [*JSON Schema Validation: A Vocabulary for Structural Validation of JSON*](https://json-schema.org/draft/2020-12/json-schema-validation) (Internet-Draft draft-bhutton-json-schema-validation-01).
  Cited by [Your own catalogues](../io/material-catalogues.md).
- Wright, A., Andrews, H., Hutton, B., & Dennis, G. (2022). [*JSON Schema: A Media Type for Describing JSON Documents*](https://json-schema.org/draft/2020-12/json-schema-core) (Internet-Draft draft-bhutton-json-schema-01).
  Cited by [Your own catalogues](../io/material-catalogues.md).

## Hearing and perception

Fastl and Zwicker is the way in and stays useful long after; Moore is the
better first book if the question is the auditory system rather than the
metric. The standards-side works and the model papers here are sources for one
algorithm each, so read the note before the paper: several are the definitive
statement of a model the guides implement rather than a general treatment of
hearing.

- American National Standards Institute. (1997). [*Methods for calculation of the speech intelligibility index*](https://webstore.ansi.org/standards/asa/ansiasas31997r2017) (ANSI S3.5-1997 (R2017)). Acoustical Society of America.
  Cited by [Speech Intelligibility Index](../perception/speech/speech-intelligibility.md) and [Theory: Perception and Hearing](theory/perception.md).
- Deutsches Institut für Normung. (2005). [*Akustik — Bestimmung der Tonhaltigkeit von Geräuschen und Ermittlung eines Tonzuschlages für die Beurteilung von Geräuschimmissionen*](https://www.dinmedia.de/en/standard/din-45681/76463232) (DIN 45681:2005-03).
  Cited by [Objective audibility of tones in noise (ISO/PAS 20065)](../perception/psychoacoustics/tone-audibility.md).
- Deutsches Institut für Normung. (2009). [*Messtechnische Simulation der Hörempfindung Schärfe*](https://www.dinmedia.de/en/standard/din-45692/117635111) (DIN 45692:2009-08).
  Cited by [Sound Quality Metrics](../perception/psychoacoustics/sound-quality.md) and [Theory: Perception and Hearing](theory/perception.md).
- Ecma International. (2024). [*Psychoacoustic metrics for ITT equipment — Part 1: Prominent discrete tones*](https://ecma-international.org/wp-content/uploads/ECMA-418-1_3rd_edition_december_2024.pdf) (ECMA-418-1:2024 (3rd ed.)).
  The freely downloadable tone-to-noise ratio and prominence ratio methods.
  Cited by [Prominent Discrete Tones (ECMA-418-1)](../perception/psychoacoustics/tone-prominence.md) and [Theory: Perception and Hearing](theory/perception.md).
- Ecma International. (2025). [*Measurement of airborne noise emitted by information technology and telecommunications equipment*](https://ecma-international.org/wp-content/uploads/ECMA-74_22nd_edition_december_2025.pdf) (ECMA-74:2025 (22nd ed.)).
  The freely downloadable parent emission standard whose Annex D delegates tone assessment to ECMA-418-1.
  Cited by [Prominent Discrete Tones (ECMA-418-1)](../perception/psychoacoustics/tone-prominence.md).
- Ecma International. (2025). [*Psychoacoustic metrics for ITT equipment — Part 2 (methods for describing human perception based on the Sottek Hearing Model)*](https://ecma-international.org/publications-and-standards/standards/ecma-418/) (ECMA-418-2:2025).
  Cited by [Advanced Loudness (ISO 532-2/-3, ECMA-418-2)](../perception/psychoacoustics/advanced-loudness.md), [Sound Quality Metrics](../perception/psychoacoustics/sound-quality.md) and [Theory: Perception and Hearing](theory/perception.md).
- European Parliament and Council. (2003). [*Directive 2003/10/EC on the minimum health and safety requirements regarding the exposure of workers to the risks arising from physical agents (noise)*](https://eur-lex.europa.eu/eli/dir/2003/10/oj/eng) (Directive 2003/10/EC). Official Journal of the European Union.
  The EU exposure action and limit values for occupational noise.
  Cited by [Occupational Noise Exposure (ISO 9612)](../perception/hearing/occupational-exposure.md).
- Fastl, H., & Zwicker, E. (2007). *Psychoacoustics: Facts and models* (3rd ed.). Springer. https://doi.org/10.1007/978-3-540-68888-4
  The psychoacoustic-annoyance model and the closed-form fluctuation strength for amplitude-modulated broadband noise.
  Cited by [Loudness](../perception/psychoacoustics/loudness.md), [Sound Quality Metrics](../perception/psychoacoustics/sound-quality.md), [Psychoacoustic annoyance and fluctuation strength](../perception/psychoacoustics/psychoacoustic-annoyance.md) and [Theory: Perception and Hearing](theory/perception.md).
- Felix Greco, G., Merino-Martínez, R., Osses, A., & Lotinga, M. J. B. (2025). [*SQAT: A sound quality analysis toolbox for MATLAB*](https://github.com/ggrecow/SQAT). GitHub. https://doi.org/10.5281/zenodo.7934709
  The open MATLAB reference used as the numeric oracle for the fluctuation-strength cross-checks.
  Cited by [Psychoacoustic annoyance and fluctuation strength](../perception/psychoacoustics/psychoacoustic-annoyance.md).
- Fletcher, H., & Munson, W. A. (1933). Loudness, its definition, measurement and calculation. *The Journal of the Acoustical Society of America*, *5*(2), 82-108. https://doi.org/10.1121/1.1915637
  The original equal-loudness measurements whose 40-phon contour became the A-weighting curve.
  Cited by [Frequency Weighting (A, C, Z)](../signals/levels/weighting.md), [Loudness](../perception/psychoacoustics/loudness.md) and [Theory: Perception and Hearing](theory/perception.md).
- French, N. R., & Steinberg, J. C. (1947). Factors governing the intelligibility of speech sounds. *The Journal of the Acoustical Society of America*, *19*(1), 90-119. https://doi.org/10.1121/1.1916407
  The articulation-band experiments behind the band-importance function of the Speech Intelligibility Index.
  Cited by [Speech Intelligibility Index](../perception/speech/speech-intelligibility.md) and [Theory: Perception and Hearing](theory/perception.md).
- Google. (2019). [*speech_intelligibility_index*](https://github.com/google/speech_intelligibility_index). GitHub.
  Cited by [Theory: Perception and Hearing](theory/perception.md).
- Houtgast, T., & Steeneken, H. J. M. (1985). A review of the MTF concept in room acoustics and its use for estimating speech intelligibility in auditoria. *The Journal of the Acoustical Society of America*, *77*(3), 1069-1077. https://doi.org/10.1121/1.392224
  The modulation-transfer framework the Speech Transmission Index is built on.
  Cited by [Speech Transmission Index (STI)](../perception/speech/speech-transmission.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Electrotechnical Commission. (2011). *Sound system equipment — Part 16: Objective rating of speech intelligibility by speech transmission index* (IEC 60268-16:2011).
  Cited by [Speech Transmission Index (STI)](../perception/speech/speech-transmission.md).
- International Electrotechnical Commission. (2020). [*Sound system equipment — Part 16: Objective rating of speech intelligibility by speech transmission index*](https://webstore.iec.ch/en/publication/26771) (IEC 60268-16:2020 (Edition 5)).
  Cited by [Speech Transmission Index (STI)](../perception/speech/speech-transmission.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Organization for Standardization. (1998). [*Acoustics – Reference zero for the calibration of audiometric equipment – Part 1: Reference equivalent threshold sound pressure levels for pure tones and supra-aural earphones*](https://www.iso.org/standard/30443.html) (ISO 389-1:1998).
  Cited by [Hearing threshold (age and reference zero)](../perception/hearing/hearing-threshold.md).
- International Organization for Standardization. (2005). [*Acoustics — Reference zero for the calibration of audiometric equipment — Part 7: Reference threshold of hearing under free-field and diffuse-field listening conditions*](https://www.iso.org/standard/38976.html) (ISO 389-7:2005).
  The audiometric zero as a sound pressure level.
  Cited by [Hearing threshold (age and reference zero)](../perception/hearing/hearing-threshold.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Organization for Standardization. (2007). *Acoustics — Hearing protectors — Part 3: Measurement of insertion loss of ear-muff type protectors using an acoustic test fixture* (ISO 4869-3:2007).
  Cited by [Hearing Protectors (ISO 4869-1, -2, -3 and -6)](../perception/hearing/hearing-protectors.md).
- International Organization for Standardization. (2009). *Acoustics — Audiometric test methods — Part 2: Sound field audiometry with pure-tone and narrow-band test signals* (ISO 8253-2:2009).
  Cited by [Audiometric Test Methods (ISO 8253-1 and -2)](../perception/hearing/audiometry.md).
- International Organization for Standardization. (2009). [*Acoustics — Determination of occupational noise exposure — Engineering method*](https://www.iso.org/standard/41718.html) (ISO 9612:2009).
  The three measurement strategies and the Annex C uncertainty budget.
  Cited by [Occupational Noise Exposure (ISO 9612)](../perception/hearing/occupational-exposure.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (2010). *Acoustics — Audiometric test methods — Part 1: Pure-tone air and bone conduction audiometry* (ISO 8253-1:2010).
  Cited by [Audiometric Test Methods (ISO 8253-1 and -2)](../perception/hearing/audiometry.md).
- International Organization for Standardization. (2013). [*Acoustics — Estimation of noise-induced hearing loss*](https://www.iso.org/standard/45103.html) (ISO 1999:2013).
  The NIPTS model, its distribution and the HTLAN combination.
  Cited by [Noise-induced hearing loss (ISO 1999)](../perception/hearing/noise-induced-hearing-loss.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Organization for Standardization. (2016). [*Acoustics — Objective method for assessing the audibility of tones in noise — Engineering method*](https://www.iso.org/standard/66941.html) (ISO/PAS 20065:2016).
  Withdrawn and superseded by [ISO/TS 20065:2022](https://www.iso.org/standard/81518.html). The engineering method for the objective audibility of tones; the implementation follows the 2016 PAS edition.
  Cited by [Objective audibility of tones in noise (ISO/PAS 20065)](../perception/psychoacoustics/tone-audibility.md).
- International Organization for Standardization. (2017). [*Acoustics — Methods for calculating loudness — Part 1: Zwicker method*](https://www.iso.org/standard/63077.html) (ISO 532-1:2017).
  Cited by [Loudness](../perception/psychoacoustics/loudness.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Organization for Standardization. (2017). [*Acoustics — Methods for calculating loudness — Part 2: Moore-Glasberg method*](https://www.iso.org/standard/63078.html) (ISO 532-2:2017).
  Cited by [Advanced Loudness (ISO 532-2/-3, ECMA-418-2)](../perception/psychoacoustics/advanced-loudness.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Organization for Standardization. (2017). [*Acoustics — Statistical distribution of hearing thresholds related to age and gender*](https://www.iso.org/standard/42916.html) (ISO 7029:2017).
  The age model of the hearing threshold and its population spread.
  Cited by [Hearing threshold (age and reference zero)](../perception/hearing/hearing-threshold.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Organization for Standardization. (2018). [*Acoustics — Hearing protectors — Part 1: Subjective method for the measurement of sound attenuation*](https://www.iso.org/standard/65581.html) (ISO 4869-1:2018).
  Cited by [Hearing Protectors (ISO 4869-1, -2, -3 and -6)](../perception/hearing/hearing-protectors.md).
- International Organization for Standardization. (2018). [*Acoustics — Hearing protectors — Part 2: Estimation of effective A-weighted sound pressure levels when hearing protectors are worn*](https://www.iso.org/standard/65582.html) (ISO 4869-2:2018).
  Cited by [Hearing Protectors (ISO 4869-1, -2, -3 and -6)](../perception/hearing/hearing-protectors.md).
- International Organization for Standardization. (2019). *Acoustics — Hearing protectors — Part 6: Determination of sound attenuation of active noise reduction earmuffs* (ISO 4869-6:2019).
  Cited by [Hearing Protectors (ISO 4869-1, -2, -3 and -6)](../perception/hearing/hearing-protectors.md).
- International Organization for Standardization. (2023). [*Acoustics — Methods for calculating loudness — Part 3: Moore-Glasberg-Schlittenlacher method*](https://www.iso.org/standard/69856.html) (ISO 532-3:2023).
  Cited by [Advanced Loudness (ISO 532-2/-3, ECMA-418-2)](../perception/psychoacoustics/advanced-loudness.md) and [Theory: Perception and Hearing](theory/perception.md).
- International Organization for Standardization. (2023). [*Acoustics — Normal equal-loudness-level contours*](https://www.iso.org/standard/83117.html) (ISO 226:2023).
  The modern equal-loudness contours, successors of the Fletcher-Munson curves.
  Cited by [Frequency Weighting (A, C, Z)](../signals/levels/weighting.md), [Loudness](../perception/psychoacoustics/loudness.md) and [Theory: Perception and Hearing](theory/perception.md).
- Jensen, J., & Taal, C. H. (2016). An algorithm for predicting the intelligibility of speech masked by modulated noise maskers. *IEEE/ACM Transactions on Audio, Speech, and Language Processing*, *24*(11), 2009-2022. https://doi.org/10.1109/TASLP.2016.2585878
  ESTOI: the row- and column-normalised short-time spectrogram and its spectral-correlation intermediate index.
  Cited by [Objective Intelligibility (STOI & ESTOI)](../perception/speech/objective-intelligibility.md).
- Moore, B. C. J. (2013). *An introduction to the psychology of hearing* (6th ed.). Brill. https://doi.org/10.1163/9789004252424
  The standard textbook on auditory perception; pages 76-77 give the Glasberg and Moore (1990) ERB_N auditory-filter bandwidth and the Cam (ERB_N number) frequency scale the loudness models are written on.
  Cited by [Advanced Loudness (ISO 532-2/-3, ECMA-418-2)](../perception/psychoacoustics/advanced-loudness.md).
- National Institute for Occupational Safety and Health. (1998). [*Criteria for a recommended standard: Occupational noise exposure — Revised criteria 1998*](https://www.cdc.gov/niosh/docs/98-126/pdfs/98-126.pdf) (DHHS/NIOSH Publication No. 98-126). https://doi.org/10.26616/NIOSHPUB98126
  The freely available criteria document behind the 85 dB(A) recommended exposure limit and the hearing-conservation and fence discussion.
  Cited by [Noise-induced hearing loss (ISO 1999)](../perception/hearing/noise-induced-hearing-loss.md) and [Occupational Noise Exposure (ISO 9612)](../perception/hearing/occupational-exposure.md).
- Osses Vecchi, A., García León, R., & Kohlrausch, A. (2016). Modelling the sensation of fluctuation strength. *Proceedings of Meetings on Acoustics*, *28*, 050005. https://doi.org/10.1121/2.0000410
  The fluctuation-strength signal model and its Table 1 literature values.
  Cited by [Psychoacoustic annoyance and fluctuation strength](../perception/psychoacoustics/psychoacoustic-annoyance.md).
- Passchier-Vermeer, W. (1974). Hearing loss due to continuous exposure to steady-state broad-band noise. *The Journal of the Acoustical Society of America*, *56*(5), 1585-1593. https://doi.org/10.1121/1.1903482
  A field study of the noise exposure-response relations later codified in ISO 1999.
  Cited by [Noise-induced hearing loss (ISO 1999)](../perception/hearing/noise-induced-hearing-loss.md) and [Theory: Perception and Hearing](theory/perception.md).
- Pavlovic, C. (n.d.). [*C program developer's kit for the Speech Intelligibility Index (SII.C)*](https://www.sii.to/html/programs.html). Support site for the Speech Intelligibility Index.
  Cited by [Speech Intelligibility Index](../perception/speech/speech-intelligibility.md).
- Taal, C. H., Hendriks, R. C., Heusdens, R., & Jensen, J. (2010). A short-time objective intelligibility measure for time-frequency weighted noisy speech. *2010 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*, 4214-4217. https://doi.org/10.1109/ICASSP.2010.5495701
  The short conference version of STOI.
  Cited by [Objective Intelligibility (STOI & ESTOI)](../perception/speech/objective-intelligibility.md).
- Taal, C. H., Hendriks, R. C., Heusdens, R., & Jensen, J. (2011). An algorithm for intelligibility prediction of time-frequency weighted noisy speech. *IEEE Transactions on Audio, Speech, and Language Processing*, *19*(7), 2125-2136. https://doi.org/10.1109/TASL.2011.2114881
  STOI: the shared one-third-octave front end, the normalisation and signal-to-distortion clipping, and the per-band envelope correlation the index averages.
  Cited by [Objective Intelligibility (STOI & ESTOI)](../perception/speech/objective-intelligibility.md).
- Warnes, G. R. (2018). [*SII: Calculate ANSI S3.5-1997 Speech Intelligibility Index (version 1.0.3.1)*](https://cran.r-project.org/src/contrib/Archive/SII/). CRAN archive.
  Cited by [Theory: Perception and Hearing](theory/perception.md).

## Rooms and buildings

Kuttruff is the reference monograph and the one to own; Long is the
design-side companion when the question is architectural rather than
metrological, and Hopkins is the one to open for anything structure-borne or
flanking. The Sabine, Eyring, Millington, Fitzroy and Arau papers are here as
the sources of the five prediction formulas rather than as reading, and each is
worth opening to see what its author assumed about how absorption is
distributed, which is exactly where the five disagree.

- Acoustical Society of America. (2019). [*Criteria for evaluating room noise*](https://webstore.ansi.org/standards/asa/ansiasas122019) (ANSI/ASA S12.2-2019).
  The normative NC tangency method and the RC Mark II rating of its informative Annex D, with its spectral tag.
  Cited by [Room-noise criteria (NC / RC Mark II)](../buildings/rooms/room-noise.md), [Room to Room: Partition, Receiving Room, Criterion](../devices/noise-control/room-to-room.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Allen, J. B., & Berkley, D. A. (1979). Image method for efficiently simulating small-room acoustics. *The Journal of the Acoustical Society of America*, *65*(4), 943-950. https://doi.org/10.1121/1.382599
  The reflection-count decomposition of the rectangular-room image lattice.
  Cited by [Image Sources and the Steady-State Room Field](../buildings/rooms/room-image-sources.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Arau-Puchades, H. (1988). [An improved reverberation formula](https://www.ingentaconnect.com/content/dav/aaua/1988/00000065/00000004/art00003). *Acustica*, *65*(4), 163-180.
  The geometric-mean refinement of the axial reverberation formula.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md).
- Arau-Puchades, H. (1999). *ABC de la acústica arquitectónica*. Grupo Editorial CEAC.
  ISBN 84-329-2017-7. The Spanish textbook of architectural acoustics, cited in this tree as Arau-Puchades (1999) and not to be confused with his 1988 paper on the reverberation formula. Its Table 4.1 prints the density, the critical frequency of a one-centimetre plate and the damping factor of seventeen solids, and its Table 6.1 the octave-band absorption coefficients of building materials and finishes, each row numbered; the book prints a decimal point.
  Cited by [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/) and [Catalogue of absorption coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/absorption-coefficients/).
- Asociación Española de Normalización. (2018). [*Propiedades acústicas de los elementos de construcción y de los edificios — Mediciones en laboratorio del ruido estructural de los equipos técnicos de los edificios para todas las condiciones de instalación*](https://www.une.org/encuentra-tu-norma/busca-tu-norma/norma?c=N0059781) (UNE-EN 15657:2018).
  Cited by [Structure-borne sound power of equipment (EN 15657)](../buildings/design/structure-borne-power.md).
- ASTM International. (2022). [*Classification for Rating Sound Insulation*](https://www.astm.org/e0413-22.html) (ASTM E413-22).
  Cited by [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md).
- Avilés López, R., & Perera Martín, R. (2017). *Manual de acústica ambiental y arquitectónica*. Paraninfo.
  Cited by [Spanish Building Code (CTE DB-HR)](../buildings/insulation/spanish-building-code.md) and [Spanish Noise Regulation (RD 1367/2007)](../environment/assessment/spanish-noise-regulation.md).
- Barron, M. (2009). *Auditorium acoustics and architectural design* (2nd ed.). Spon Press.
  Cited by [Sound strength G (ISO 3382-1)](../buildings/rooms/sound-strength.md).
- Barron, M., & Lee, L.-J. (1988). Energy relations in concert auditoriums. I. *The Journal of the Acoustical Society of America*, *84*(2), 618-628. https://doi.org/10.1121/1.396840
  Cited by [Sound strength G (ISO 3382-1)](../buildings/rooms/sound-strength.md).
- Barron, M., & Marshall, A. H. (1981). Spatial impression due to early lateral reflections in concert halls: The derivation of a physical measure. *Journal of Sound and Vibration*, *77*(2), 211-232. https://doi.org/10.1016/S0022-460X(81)80020-X
  Cited by [Spatial impression (ISO 3382-1)](../buildings/rooms/spatial-impression.md).
- Beranek, L. L. (1957). Revised criteria for noise in buildings. *Noise Control*, *3*(1), 19-27. https://doi.org/10.1121/1.2369239
  The original NC curves and their speech-interference rationale.
  Cited by [Room-noise criteria (NC / RC Mark II)](../buildings/rooms/room-noise.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Blazier, W. E. (1997). RC Mark II: A refined procedure for rating the noise of heating, ventilating, and air-conditioning (HVAC) systems in buildings. *Noise Control Engineering Journal*, *45*(6), 243-250. https://doi.org/10.3397/1.2828446
  The RC Mark II procedure later codified by ANSI/ASA S12.2 Annex D.
  Cited by [Room-noise criteria (NC / RC Mark II)](../buildings/rooms/room-noise.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Bradley, J. S. (2011). Review of objective room acoustics measures and future needs. *Applied Acoustics*, *72*(10), 713-720. https://doi.org/10.1016/j.apacoust.2011.04.004
  Cited by [Reporting and source qualification (ISO 3382-1)](../buildings/rooms/reporting-and-qualification.md).
- Bradley, J. S., & Soulodre, G. A. (1995). Objective measures of listener envelopment. *The Journal of the Acoustical Society of America*, *98*(5), 2590-2597. https://doi.org/10.1121/1.413225
  Cited by [Spatial impression (ISO 3382-1)](../buildings/rooms/spatial-impression.md).
- Carrión Isbert, A. (1998). [*Diseño acústico de espacios arquitectónicos*](https://openlibrary.org/books/OL23159935M). Edicions UPC.
  ISBN 978-84-8301-252-9. A Spanish-language textbook on acoustic room design.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md).
- Craik, R. J. M., & Wilson, R. (1995). Sound transmission through masonry cavity walls. *Journal of Sound and Vibration 179(1), 79-96*. https://doi.org/10.1006/jsvi.1995.0006
  Cited by [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md).
- Davy, J. L. (1980). The variance of impulse decays. *Acustica*, *44*(1), 51-56.
  Cited by [Stage support and uncertainty (ISO 3382-1)](../buildings/rooms/stage-and-uncertainty.md).
- European Committee for Standardization. (2000). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 1: Airborne sound insulation between rooms*](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-in-buildings-from-the-performance-of-elements-airborne-sound-insulation-between-rooms) (EN 12354-1:2000).
  Cited by [Predicting Sound Insulation (EN 12354)](../buildings/design/insulation-prediction.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- European Committee for Standardization. (2000). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 2: Impact sound insulation between rooms*](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-in-buildings-from-the-performance-of-elements-impact-sound-insulation-between-rooms) (EN 12354-2:2000).
  Cited by [Predicting Sound Insulation (EN 12354)](../buildings/design/insulation-prediction.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- European Committee for Standardization. (2000). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 3: Airborne sound insulation against outdoor sound*](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-in-buildings-from-the-performance-of-elements-airborne-sound-insulation-against-outdoor-sound) (EN 12354-3:2000).
  Cited by [Façade Sound Insulation](../buildings/insulation/facade-insulation.md).
- European Committee for Standardization. (2000). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 4: Transmission of indoor sound to the outside*](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-in-buildings-from-the-performance-of-elements-transmission-of-indoor-sound-to-the-outside) (EN 12354-4:2000).
  Cited by [Façade Sound Insulation](../buildings/insulation/facade-insulation.md).
- European Committee for Standardization. (2003). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 6: Sound absorption in enclosed spaces*](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-of-buildings-from-the-performance-of-elements-sound-absorption-in-enclosed-spaces) (EN 12354-6:2003).
  The absorption member of the EN 12354 prediction family.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md), [Sound absorption in enclosed spaces (EN 12354-6)](../buildings/rooms/enclosed-space-absorption.md), [Theory: Rooms and Buildings](theory/rooms-buildings.md) and [Catalogue of air attenuation](https://docs.jmrp.io/phonometry/reference/catalogues/air-attenuation/).
- European Committee for Standardization. (2009). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 5: Sound levels due to service equipment*](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-of-building-from-the-performance-of-elements-sounds-levels-due-to-the-service-equipment) (EN 12354-5:2009).
  Cited by [Structure-borne sound power of equipment (EN 15657)](../buildings/design/structure-borne-power.md) and [Installed structure-borne sound (EN 12354-5)](../buildings/design/installed-structure-borne.md).
- Everest, F. A. (2001). [*Master handbook of acoustics*](https://openlibrary.org/isbn/9780071360975) (4th ed.). McGraw-Hill.
  ISBN 978-0-07-136097-5. A practical room-acoustics handbook; its Fig. 7-22 worked example anchors the reverberation-prediction conformance suite.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md) and [Catalogue of absorption coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/absorption-coefficients/).
- Eyring, C. F. (1930). Reverberation time in "dead" rooms. *The Journal of the Acoustical Society of America*, *1*(2A), 217-241. https://doi.org/10.1121/1.1915175
  The mean-free-path reverberation formula for strongly absorbing rooms.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md).
- Fitzroy, D. (1959). Reverberation formula which seems to be more accurate with nonuniform distribution of absorption. *The Journal of the Acoustical Society of America*, *31*(7), 893-897. https://doi.org/10.1121/1.1907814
  The axial reverberation formula for anisotropic absorption.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md).
- Foret, R., Chéné, J.-B., & Guigou-Carter, C. (2011). A comparison of the reduction of transmitted impact noise by floor coverings measured using ISO 140-8 and ISO/CD 16251-1. *Forum Acusticum 2011, Aalborg (CSTB)*.
  Cited by [Floor-Covering Impact Improvement (ISO 16251-1)](../buildings/design/impact-improvement.md).
- Gade, A. C. (1989). Investigations of musicians' room acoustic conditions in concert halls. II: Field experiments and synthesis of results. *Acustica*, *69*(6), 249-262.
  Cited by [Stage support and uncertainty (ISO 3382-1)](../buildings/rooms/stage-and-uncertainty.md).
- Hak, C. C. J. M., Wenmaekers, R. H. C., & van Luxemburg, L. C. J. (2012). Measuring room impulse responses: Impact of the decay range on derived room acoustic parameters. *Acta Acustica united with Acustica*, *98*(6), 907-915. https://doi.org/10.3813/aaa.918574
  The impulse-to-noise-ratio (INR) analysis of decay-range requirements.
  Cited by [Room acoustic parameters (ISO 3382-1/2)](../buildings/rooms/room-acoustics.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Hall, R., & Hopkins, C. (2001). The measurement of dynamic stiffness of wall ties used in masonry cavity walls. *Proceedings of the Institute of Acoustics 23(8), 259-266*.
  Cited by [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md).
- Harris, C. M. (Ed.). (1977). *Manual para el control del ruido* (Vol. 1). Instituto de Estudios de Administración Local.
  Instituto de Estudios de Administración Local. The Spanish translation of the first edition of the *Handbook of Noise Control* (McGraw-Hill, 1957), cited in this tree as Harris (1977). Chapter 19, "Control del ruido a través de los sólidos", by Fritz Ingerslev and Cyril M. Harris, prints in its Tables 19.2 to 19.4 the average improvement in impact sound insulation of twenty-three floor finishes, floating screeds and timber floors on a bare concrete floor, and Table 14.2, in Richard N. Hamme's chapter on vibration damping, the decay rate of eight asphalt felt treatments on a standard steel panel.
  Cited by [Catalogue of damping treatments](https://docs.jmrp.io/phonometry/reference/catalogues/damping-treatments/) and [Catalogue of impact insulation](https://docs.jmrp.io/phonometry/reference/catalogues/impact-insulation/).
- Harris, C. M. (Ed.). (1995). *Manual de medidas acústicas y control del ruido* (3rd ed.). McGraw-Hill.
  McGraw-Hill. The Spanish edition of the handbook, cited in this tree as Harris 3e and not to be confused with the window paper of F. J. Harris under Signal processing. Chapter 30 prints in Tables 30.2 and 30.3 the noise reduction coefficient of nineteen carpets on bare concrete and on a hair pad; Chapter 31 prints in seven tables the sound transmission class of stud walls, block walls, doors, sealed windows and floor-ceiling systems, and Chapter 32, "Aislamiento del sonido transmitido por estructuras", prints in its Tables 32.1 to 32.8 the measured impact insulation class of forty-two floor-ceiling constructions and the improvement six elastic surface treatments add over a hard massive floor.
  Cited by [Catalogue of carpets](https://docs.jmrp.io/phonometry/reference/catalogues/carpets/), [Catalogue of transmission loss](https://docs.jmrp.io/phonometry/reference/catalogues/transmission-loss/) and [Catalogue of impact insulation](https://docs.jmrp.io/phonometry/reference/catalogues/impact-insulation/).
- Hidaka, T., Beranek, L. L., & Okano, T. (1995). Interaural cross-correlation, lateral fraction, and low- and high-frequency sound levels as measures of acoustical quality in concert halls. *The Journal of the Acoustical Society of America*, *98*(2), 988-1007. https://doi.org/10.1121/1.414451
  Cited by [Spatial impression (ISO 3382-1)](../buildings/rooms/spatial-impression.md).
- Hopkins, C. (2007). *Sound insulation*. Butterworth-Heinemann. https://doi.org/10.4324/9780080550473
  ISBN 978-0-7506-6526-1. The comprehensive treatment of airborne and impact sound insulation: measurement chains, flanking transmission and the EN 12354 prediction framework.
  Cited by [Field Insulation Measurement (ISO 16283)](../buildings/insulation/insulation-field.md), [Small Rooms: the ISO 16283 Low-Frequency Procedure](../buildings/insulation/low-frequency-procedure.md), [Laboratory Insulation Measurement](../buildings/insulation/insulation-lab.md), [Sound Insulation by Intensity (ISO 15186)](../buildings/insulation/insulation-intensity.md), [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md), [Heavy and Soft Impact Sources (ISO 16283-2)](../buildings/insulation/heavy-impact-sources.md), [Insulation Ratings (ISO 717)](../buildings/insulation/insulation-ratings.md), [Façade Sound Insulation](../buildings/insulation/facade-insulation.md), [Predicting Sound Insulation (EN 12354)](../buildings/design/insulation-prediction.md), [Detailed Per-Band Prediction (ISO 12354)](../buildings/design/detailed-prediction.md), [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md), [Predicting Resilient-Layer Performance](../buildings/design/resilient-layers.md), [Installed structure-borne sound (EN 12354-5)](../buildings/design/installed-structure-borne.md), [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md), [Plate junctions: wave approach and experimental SEA](../vibration/structural/junction-transmission.md), [Theory: Rooms and Buildings](theory/rooms-buildings.md), [Theory: Vibration](theory/vibration.md), [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/), [Catalogue of resilient layers](https://docs.jmrp.io/phonometry/reference/catalogues/resilient-layers/) and [Catalogue of gases](https://docs.jmrp.io/phonometry/reference/catalogues/gases/).
- Hopkins, C., Wilson, R., & Craik, R. J. M. (1999). Dynamic stiffness as an acoustic specification parameter for wall ties used in masonry cavity walls. *Applied Acoustics 58, 51-68*. https://doi.org/10.1016/S0003-682X(98)00068-1
  The measurement behind the 50 mm rows of Hopkins' Table A4: butterfly 1,7 MN/m, double-triangle 16,1 MN/m and vertical-twist 94,0 MN/m.
  Cited by [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md).
- Instituto de Ciencias de la Construcción Eduardo Torroja (CSIC). (n.d.). [*Catálogo informático de elementos constructivos (CEC)*](https://www.codigotecnico.org/Programas/CatalogoElementosConstructivos.html). Código Técnico de la Edificación.
  Cited by [Spanish Building Code (CTE DB-HR)](../buildings/insulation/spanish-building-code.md).
- International Organization for Standardization. (1985). [*Acoustics — Measurement of sound insulation in buildings and of building elements — Part 9: Laboratory measurement of room-to-room airborne sound insulation of a suspended ceiling with a plenum above it*](https://www.iso.org/standard/3965.html) (ISO 140-9:1985).
  Cited by [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md).
- International Organization for Standardization. (1989). [*Acoustics — Determination of dynamic stiffness — Part 1: Materials used under floating floors in dwellings*](https://www.iso.org/standard/16620.html) (EN 29052-1:1992 (ISO 9052-1:1989)).
  The resonance method for the dynamic stiffness per unit area, identical to EN 29052-1.
  Cited by [Your own catalogues](../io/material-catalogues.md), [Floor-Covering Impact Improvement (ISO 16251-1)](../buildings/design/impact-improvement.md), [Predicting Resilient-Layer Performance](../buildings/design/resilient-layers.md) and [Dynamic stiffness of resilient materials](../materials/resilient/dynamic-stiffness.md).
- International Organization for Standardization. (1998). *Acoustics — Recommended practice for the design of low-noise workplaces containing machinery — Part 3: Sound propagation and noise prediction in workrooms* (ISO 11690-3:1998).
  Cited by [Spatial Sound Decay in Workrooms](../buildings/rooms/workroom-sound-decay.md).
- International Organization for Standardization. (2000). [*Acoustics — Measurement of sound insulation in buildings and of building elements using sound intensity — Part 1: Laboratory measurements*](https://www.iso.org/standard/26097.html) (ISO 15186-1:2000).
  Cited by [Sound Insulation by Intensity (ISO 15186)](../buildings/insulation/insulation-intensity.md).
- International Organization for Standardization. (2001). *Acoustics — Measurement and parametric description of spatial sound distribution curves in workrooms for evaluation of their acoustical performance* (ISO 14257:2001).
  Cited by [Spatial Sound Decay in Workrooms](../buildings/rooms/workroom-sound-decay.md).
- International Organization for Standardization. (2002). [*Acoustics — Measurement of sound insulation in buildings and of building elements using sound intensity — Part 3: Laboratory measurements at low frequencies*](https://www.iso.org/standard/31395.html) (ISO 15186-3:2002).
  Cited by [Sound Insulation by Intensity (ISO 15186)](../buildings/insulation/insulation-intensity.md).
- International Organization for Standardization. (2003). [*Acoustics — Measurement of sound absorption in a reverberation room*](https://www.iso.org/standard/34545.html) (ISO 354:2003).
  The reverberation-room absorption measurement behind the surface data.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md), [Sound absorption in enclosed spaces (EN 12354-6)](../buildings/rooms/enclosed-space-absorption.md), [Reading a material datasheet](../materials/reading-a-datasheet.md), [Sound Absorption Measurement and Rating](../materials/absorbers/absorption-measurement.md), [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2003). [*Acoustics — Measurement of sound insulation in buildings and of building elements using sound intensity — Part 2: Field measurements*](https://www.iso.org/standard/30105.html) (ISO 15186-2:2003).
  Cited by [Sound Insulation by Intensity (ISO 15186)](../buildings/insulation/insulation-intensity.md).
- International Organization for Standardization. (2004). *Acoustics — Measurement of sound pressure level from service equipment in buildings — Engineering method* (ISO 16032:2004).
  Cited by [Service-Equipment and Activity Noise (ISO 16032)](../buildings/insulation/service-equipment-noise.md).
- International Organization for Standardization. (2006). [*Acoustics — Application of new measurement methods in building and room acoustics*](https://www.iso.org/standard/40408.html) (ISO 18233:2006).
  The swept-sine and MLS acquisition of impulse responses.
  Cited by [Measuring the Room Impulse Response](../buildings/rooms/room-impulse-response.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2006). [*Acoustics — Laboratory measurement of the flanking transmission of airborne and impact sound between adjoining rooms — Part 1: Frame document*](https://www.iso.org/standard/38284.html) (ISO 10848-1:2006).
  Cited by [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md).
- International Organization for Standardization. (2006). [*Acoustics — Laboratory measurement of the flanking transmission of airborne and impact sound between adjoining rooms — Part 2: Application to light elements when the junction has a small influence*](https://www.iso.org/standard/35004.html) (ISO 10848-2:2006).
  Cited by [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md).
- International Organization for Standardization. (2006). [*Acoustics — Laboratory measurement of the flanking transmission of airborne and impact sound between adjoining rooms — Part 3: Application to light elements when the junction has a substantial influence*](https://www.iso.org/standard/35003.html) (ISO 10848-3:2006).
  Cited by [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md).
- International Organization for Standardization. (2008). [*Acoustics — Measurement of room acoustic parameters — Part 2: Reverberation time in ordinary rooms*](https://www.iso.org/standard/36201.html) (ISO 3382-2:2008).
  The accuracy grades and position counts of reverberation measurement.
  Cited by [Measuring the Room Impulse Response](../buildings/rooms/room-impulse-response.md), [Room acoustic parameters (ISO 3382-1/2)](../buildings/rooms/room-acoustics.md), [Stage support and uncertainty (ISO 3382-1)](../buildings/rooms/stage-and-uncertainty.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2009). [*Acoustics — Measurement of room acoustic parameters — Part 1: Performance spaces*](https://www.iso.org/standard/40979.html) (ISO 3382-1:2009).
  Room-parameter definitions, position requirements and just-noticeable differences.
  Cited by [Measuring the Room Impulse Response](../buildings/rooms/room-impulse-response.md), [Room acoustic parameters (ISO 3382-1/2)](../buildings/rooms/room-acoustics.md), [Sound strength G (ISO 3382-1)](../buildings/rooms/sound-strength.md), [Spatial impression (ISO 3382-1)](../buildings/rooms/spatial-impression.md), [Stage support and uncertainty (ISO 3382-1)](../buildings/rooms/stage-and-uncertainty.md), [Reporting and source qualification (ISO 3382-1)](../buildings/rooms/reporting-and-qualification.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2010). *Acoustics — Laboratory measurement of sound insulation of building elements — Part 1: Application rules for specific products* (ISO 10140-1:2010).
  Cited by [Laboratory Insulation Measurement](../buildings/insulation/insulation-lab.md) and [Reading a material datasheet](../materials/reading-a-datasheet.md).
- International Organization for Standardization. (2010). [*Acoustics — Laboratory measurement of sound insulation of building elements — Part 3: Measurement of impact sound insulation*](https://www.iso.org/standard/42089.html) (ISO 10140-3:2010).
  Cited by [Laboratory Insulation Measurement](../buildings/insulation/insulation-lab.md), [Heavy and Soft Impact Sources (ISO 16283-2)](../buildings/insulation/heavy-impact-sources.md) and [Reading a material datasheet](../materials/reading-a-datasheet.md).
- International Organization for Standardization. (2010). [*Acoustics — Laboratory measurement of sound insulation of building elements — Part 4: Measurement procedures and requirements*](https://www.iso.org/standard/42090.html) (ISO 10140-4:2010).
  Cited by [Laboratory Insulation Measurement](../buildings/insulation/insulation-lab.md).
- International Organization for Standardization. (2010). *Acoustics — Laboratory measurement of sound insulation of building elements — Part 5: Requirements for test facilities and equipment* (ISO 10140-5:2010).
  Cited by [Laboratory Insulation Measurement](../buildings/insulation/insulation-lab.md).
- International Organization for Standardization. (2010). [*Acoustics — Laboratory measurement of the flanking transmission of airborne and impact sound between adjoining rooms — Part 4: Application to junctions with at least one heavy element*](https://www.iso.org/standard/45360.html) (ISO 10848-4:2010).
  Cited by [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md).
- International Organization for Standardization. (2012). [*Acoustics — Measurement of room acoustic parameters — Part 3: Open plan offices*](https://www.iso.org/standard/46520.html) (ISO 3382-3:2012).
  Since revised as [ISO 3382-3:2022](https://www.iso.org/standard/77437.html). The open-plan speech-privacy quantities.
  Cited by [Open-Plan Office Acoustics (ISO 3382-3)](../buildings/rooms/open-plan-acoustics.md), [Spatial Sound Decay in Workrooms](../buildings/rooms/workroom-sound-decay.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2014). [*Acoustics — Field measurement of sound insulation in buildings and of building elements — Part 1: Airborne sound insulation*](https://www.iso.org/standard/55997.html) (ISO 16283-1:2014).
  The field airborne measurement method.
  Cited by [Field Insulation Measurement (ISO 16283)](../buildings/insulation/insulation-field.md), [Small Rooms: the ISO 16283 Low-Frequency Procedure](../buildings/insulation/low-frequency-procedure.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2014). [*Acoustics — Laboratory measurement of the reduction of transmitted impact noise by floor coverings on a small floor mock-up — Part 1: Heavyweight compact floor*](https://www.iso.org/standard/56017.html) (ISO 16251-1:2014).
  Cited by [Floor-Covering Impact Improvement (ISO 16251-1)](../buildings/design/impact-improvement.md).
- International Organization for Standardization. (2016). [*Acoustics — Field measurement of sound insulation in buildings and of building elements — Part 3: Façade sound insulation*](https://www.iso.org/standard/59748.html) (ISO 16283-3:2016).
  Cited by [Small Rooms: the ISO 16283 Low-Frequency Procedure](../buildings/insulation/low-frequency-procedure.md), [Façade Sound Insulation](../buildings/insulation/facade-insulation.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2016). *Acoustics — Requirements for the performance and calibration of reference sound sources used for the determination of sound power levels* (ISO 6926:2016).
  Cited by [Spatial Sound Decay in Workrooms](../buildings/rooms/workroom-sound-decay.md) and [Free Field and Reference Sources (ISO 26101 / ISO 6926)](../devices/emission/free-field-qualification.md).
- International Organization for Standardization. (2017). [*Acoustics — Laboratory and field measurement of flanking transmission for airborne, impact and building service equipment sound between adjoining rooms — Part 1: Frame document*](https://www.iso.org/standard/67226.html) (ISO 10848-1:2017).
  Cited by [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md).
- International Organization for Standardization. (2017). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 1: Airborne sound insulation between rooms*](https://www.iso.org/standard/70242.html) (ISO 12354-1:2017).
  Cited by [Your own catalogues](../io/material-catalogues.md), [Detailed Per-Band Prediction (ISO 12354)](../buildings/design/detailed-prediction.md), [Predicting Resilient-Layer Performance](../buildings/design/resilient-layers.md), [Installed structure-borne sound (EN 12354-5)](../buildings/design/installed-structure-borne.md) and [Catalogue of fluids](https://docs.jmrp.io/phonometry/reference/catalogues/fluids/).
- International Organization for Standardization. (2017). [*Building acoustics — Estimation of acoustic performance of buildings from the performance of elements — Part 2: Impact sound insulation between rooms*](https://www.iso.org/standard/70243.html) (ISO 12354-2:2017).
  Cited by [Detailed Per-Band Prediction (ISO 12354)](../buildings/design/detailed-prediction.md), [Floor-Covering Impact Improvement (ISO 16251-1)](../buildings/design/impact-improvement.md) and [Predicting Resilient-Layer Performance](../buildings/design/resilient-layers.md).
- International Organization for Standardization. (2020). [*Acoustics — Field measurement of sound insulation in buildings and of building elements — Part 2: Impact sound insulation*](https://www.iso.org/standard/77436.html) (ISO 16283-2:2020).
  Cited by [Field Insulation Measurement (ISO 16283)](../buildings/insulation/insulation-field.md), [Small Rooms: the ISO 16283 Low-Frequency Procedure](../buildings/insulation/low-frequency-procedure.md), [Heavy and Soft Impact Sources (ISO 16283-2)](../buildings/insulation/heavy-impact-sources.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2020). [*Acoustics — Rating of sound insulation in buildings and of building elements — Part 1: Airborne sound insulation*](https://www.iso.org/standard/77435.html) (ISO 717-1:2020).
  The reference-curve rating and the spectrum adaptation terms C and Ctr.
  Cited by [Field Insulation Measurement (ISO 16283)](../buildings/insulation/insulation-field.md), [Small Rooms: the ISO 16283 Low-Frequency Procedure](../buildings/insulation/low-frequency-procedure.md), [Linings, Floor Coverings, Joints and Rain (ISO 10140-1)](../buildings/insulation/lab-application-rules.md), [Sound Insulation by Intensity (ISO 15186)](../buildings/insulation/insulation-intensity.md), [Sound Insulation Survey Method (ISO 10052)](../buildings/insulation/insulation-survey.md), [Insulation Ratings (ISO 717)](../buildings/insulation/insulation-ratings.md), [Façade Sound Insulation](../buildings/insulation/facade-insulation.md), [Reading a material datasheet](../materials/reading-a-datasheet.md), [Enclosures and Cabins Measured (ISO 11546, ISO 11957)](../devices/noise-control/enclosure-cabin-insulation.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2020). [*Acoustics — Rating of sound insulation in buildings and of building elements — Part 2: Impact sound insulation*](https://www.iso.org/standard/69867.html) (ISO 717-2:2020).
  Cited by [Field Insulation Measurement (ISO 16283)](../buildings/insulation/insulation-field.md), [Linings, Floor Coverings, Joints and Rain (ISO 10140-1)](../buildings/insulation/lab-application-rules.md), [Sound Insulation Survey Method (ISO 10052)](../buildings/insulation/insulation-survey.md), [Heavy and Soft Impact Sources (ISO 16283-2)](../buildings/insulation/heavy-impact-sources.md), [Insulation Ratings (ISO 717)](../buildings/insulation/insulation-ratings.md), [Floor-Covering Impact Improvement (ISO 16251-1)](../buildings/design/impact-improvement.md), [Reading a material datasheet](../materials/reading-a-datasheet.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2021). [*Acoustics — Field measurements of airborne and impact sound insulation and of service equipment sound — Survey method*](https://www.iso.org/standard/76560.html) (ISO 10052:2021).
  Cited by [Sound Insulation Survey Method (ISO 10052)](../buildings/insulation/insulation-survey.md) and [Service-Equipment and Activity Noise (ISO 16032)](../buildings/insulation/service-equipment-noise.md).
- International Organization for Standardization. (2021). *Acoustics — Laboratory measurement of sound insulation of building elements — Part 1: Application rules for specific products* (ISO 10140-1:2021).
  Cited by [Linings, Floor Coverings, Joints and Rain (ISO 10140-1)](../buildings/insulation/lab-application-rules.md).
- International Organization for Standardization. (2021). [*Acoustics — Laboratory measurement of sound insulation of building elements — Part 2: Measurement of airborne sound insulation*](https://www.iso.org/standard/79487.html) (ISO 10140-2:2021).
  Cited by [Linings, Floor Coverings, Joints and Rain (ISO 10140-1)](../buildings/insulation/lab-application-rules.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2021). [*Acoustics — Laboratory measurement of sound insulation of building elements — Part 3: Measurement of impact sound insulation*](https://www.iso.org/standard/79483.html) (ISO 10140-3:2021).
  Cited by [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2021). [*Acoustics — Laboratory measurement of sound insulation of building elements — Part 4: Measurement procedures and requirements*](https://www.iso.org/standard/73911.html) (ISO 10140-4:2021).
  Cited by [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2021). [*Acoustics — Laboratory measurement of sound insulation of building elements — Part 5: Requirements for test facilities and equipment*](https://www.iso.org/standard/79482.html) (ISO 10140-5:2021).
  Cited by [Linings, Floor Coverings, Joints and Rain (ISO 10140-1)](../buildings/insulation/lab-application-rules.md), [Heavy and Soft Impact Sources (ISO 16283-2)](../buildings/insulation/heavy-impact-sources.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- International Organization for Standardization. (2023). *Acoustics — Measurement of sound pressure level from service equipment or activities in buildings — Engineering method (draft international standard)* (E DIN EN ISO 16032:2023-05).
  Cited by [Service-Equipment and Activity Noise (ISO 16032)](../buildings/insulation/service-equipment-noise.md).
- Japanese Standards Association. (2019). [*Acoustics — Measurement of floor impact sound insulation of buildings — Part 2: Method using standard heavy impact sources*](https://www.jisc.go.jp/) (JIS A 1418-2:2019).
  Cited by [Heavy and Soft Impact Sources (ISO 16283-2)](../buildings/insulation/heavy-impact-sources.md).
- Kim, K. W., Park, S. H., Shin, H. K., & Kim, K. C. (2023). Changes of floor impact sound regulations and future improvement directions in Korea. *Proceedings of Forum Acusticum 2023 (10th Convention of the European Acoustics Association)*. https://doi.org/10.61782/fa.2023.0364
  Cited by [Heavy and Soft Impact Sources (ISO 16283-2)](../buildings/insulation/heavy-impact-sources.md).
- Kosten, C. W., & van Os, G. J. (1962). [Community reaction criteria for external noises](https://openlibrary.org/books/OL58781133M). *The Control of Noise (National Physical Laboratory Symposium No. 12)*, 373-387.
  Published by Her Majesty's Stationery Office. The NR curve family contrasted with NC.
  Cited by [Room-noise criteria (NC / RC Mark II)](../buildings/rooms/room-noise.md).
- Kuttruff, H. (2016). *Room acoustics* (6th ed.). CRC Press. https://doi.org/10.1201/9781315372150
  The reference monograph on sound fields in rooms: statistical decay theory, the Schroeder frequency, absorption and the perceptual room parameters.
  Cited by [Room acoustic parameters (ISO 3382-1/2)](../buildings/rooms/room-acoustics.md), [Image Sources and the Steady-State Room Field](../buildings/rooms/room-image-sources.md), [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md), [Sound absorption in enclosed spaces (EN 12354-6)](../buildings/rooms/enclosed-space-absorption.md), [Room to Room: Partition, Receiving Room, Criterion](../devices/noise-control/room-to-room.md), [2D FDTD wave simulation](../simulation/fdtd-simulation.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Long, M. (2014). *Architectural acoustics* (2nd ed.). Academic Press. https://doi.org/10.1016/C2012-0-03257-5
  The architectural-design companion to the measurement standards: the rectangular-room eigenfrequencies and the Morse/Pierce mode count (Chapter 8), the crowd self-noise of an occupied room (Chapter 17) and the gain-before-feedback criterion of a reinforcement system (Chapter 18).
  Cited by [Open-Plan Office Acoustics (ISO 3382-3)](../buildings/rooms/open-plan-acoustics.md), [Image Sources and the Steady-State Room Field](../buildings/rooms/room-image-sources.md), [Loudspeaker Characterisation (IEC 60268-5)](../devices/electroacoustics/loudspeakers.md), [Duct-Borne Noise: Fan to Room](../devices/noise-control/duct-path.md), [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/) and [Catalogue of absorption coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/absorption-coefficients/).
- Lundeby, A., Vigran, T. E., Bietz, H., & Vorländer, M. (1995). Uncertainties of measurements in room acoustics. *Acta Acustica united with Acustica*, *81*(4), 344-355.
  Cited by [Sound strength G (ISO 3382-1)](../buildings/rooms/sound-strength.md).
- Millington, G. (1932). A modified formula for reverberation. *The Journal of the Acoustical Society of America*, *4*(1), 69-82. https://doi.org/10.1121/1.1915588
  The per-surface logarithmic reverberation formula.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md).
- Ministerio de Fomento (Spain). (2019). [*Código Técnico de la Edificación, Documento Básico HR Protección frente al ruido*](https://www.codigotecnico.org/pdf/Documentos/HR/DBHR.pdf) (CTE DB-HR).
  Cited by [Spanish Building Code (CTE DB-HR)](../buildings/insulation/spanish-building-code.md).
- Ministerio de la Presidencia (Spain). (2007). [*Real Decreto 1367/2007, developing Ley 37/2003 del Ruido on acoustic zoning, quality objectives and acoustic emissions*](https://www.boe.es/buscar/act.php?id=BOE-A-2007-18397) (RD 1367/2007 (BOE-A-2007-18397), consolidated text).
  Cited by [Spanish Building Code (CTE DB-HR)](../buildings/insulation/spanish-building-code.md) and [Spanish Noise Regulation (RD 1367/2007)](../environment/assessment/spanish-noise-regulation.md).
- Sabine, W. C. (1922). [*Collected papers on acoustics*](https://archive.org/details/collectedpaperso00sabi). Harvard University Press.
  The founding reverberation experiments and the Sabine law.
  Cited by [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md).
- Schroeder, M. R. (1965). New method of measuring reverberation time. *The Journal of the Acoustical Society of America*, *37*(3), 409-412. https://doi.org/10.1121/1.1909343
  The backward integration of the squared impulse response into a decay curve.
  Cited by [Room acoustic parameters (ISO 3382-1/2)](../buildings/rooms/room-acoustics.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Vigran, T. E. (2008). *Building acoustics*. CRC Press. https://doi.org/10.1201/9781482266016
  ISBN 978-0-415-42853-8. A compact textbook on sound transmission in buildings, from single and double constructions to floating floors.
  Cited by [Field Insulation Measurement (ISO 16283)](../buildings/insulation/insulation-field.md), [Laboratory Insulation Measurement](../buildings/insulation/insulation-lab.md), [Sound Insulation Survey Method (ISO 10052)](../buildings/insulation/insulation-survey.md), [Laboratory Flanking Transmission (ISO 10848)](../buildings/insulation/flanking-lab.md), [Detailed Per-Band Prediction (ISO 12354)](../buildings/design/detailed-prediction.md), [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md), [Floor-Covering Impact Improvement (ISO 16251-1)](../buildings/design/impact-improvement.md), [Predicting Resilient-Layer Performance](../buildings/design/resilient-layers.md), [Dynamic stiffness of resilient materials](../materials/resilient/dynamic-stiffness.md), [Theory: Rooms and Buildings](theory/rooms-buildings.md), [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/) and [Catalogue of dynamic moduli of resilient materials](https://docs.jmrp.io/phonometry/reference/catalogues/dynamic-modulus-of-resilient-materials/).
- Vorländer, M. (2020). *Auralization: Fundamentals of acoustics, modelling, simulation, algorithms and acoustic virtual reality* (2nd ed.). Springer. https://doi.org/10.1007/978-3-030-51202-6
  The mirror-source model (Chapter 11), with the reflection-factor and delay expressions.
  Cited by [Image Sources and the Steady-State Room Field](../buildings/rooms/room-image-sources.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Witew, I. B., Behler, G. K., & Vorländer, M. (2017). About just noticeable differences for aspects of spatial impressions in concert halls. *Acoustics Australia*, *45*(2), 195-202. https://doi.org/10.1007/s40857-017-0094-7
  Cited by [Reporting and source qualification (ISO 3382-1)](../buildings/rooms/reporting-and-qualification.md).

## Materials and surfaces

Allard and Atalla is the reference for porous media and the transfer-matrix
method, and Cox and D'Antonio for anything a surface scatters rather than
absorbs. The papers are the models themselves, in rough order of scope:
Delany and Bazley and its Miki regression are empirical, Johnson-Koplik-Dashen
and the JCA family are phenomenological with measurable parameters, and Maa is
the microperforated panel in closed form.

- Allard, J. F., & Atalla, N. (2009). *Propagation of sound in porous media: Modelling sound absorbing materials* (2nd ed.). Wiley. https://doi.org/10.1002/9780470747339
  ISBN 978-0-470-74661-5. The porous-material theory linking airflow resistivity, surface impedance and absorption.
  Cited by [Airflow Resistance](../materials/absorbers/airflow-resistance.md), [Impedance Tube](../materials/absorbers/impedance-tube.md), [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md), [Theory: Materials and Surfaces](theory/materials-surfaces.md) and [Catalogue of porous materials](https://docs.jmrp.io/phonometry/reference/catalogues/porous-materials/).
- ASTM International. (2019). [*Standard test method for normal incidence determination of porous material acoustical properties based on the transfer matrix method*](https://store.astm.org/e2611-19.html) (ASTM E2611-19).
  The edition the library implements, since revised as [ASTM E2611-24](https://store.astm.org/e2611-24.html). The four-microphone transfer-matrix transmission-loss method.
  Cited by [Impedance Tube](../materials/absorbers/impedance-tube.md) and [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- Audio Engineering Society. (2001). [*AES information document for room acoustics and sound reinforcement systems — Characterization and measurement of surface scattering uniformity*](https://www.aes.org/publications/standards/list.cfm) (AES-4id-2001).
  Printed in the *Journal of the Audio Engineering Society*, 49(3), 149-165. The single-plane free-field diffusion-coefficient procedure that ISO 17497-2 later standardised.
  Cited by [Diffusers and Their Coefficients](../materials/diffusers/diffusers.md).
- Cox, T. J., & D'Antonio, P. (2017). *Acoustic absorbers and diffusers: Theory, design and application* (3rd ed.). CRC Press. https://doi.org/10.1201/9781315369211
  ISBN 978-1-4987-4099-9. The monograph on absorber and diffuser measurement and design, by the authors behind the ISO 17497-2 diffusion-coefficient method.
  Cited by [Sound Absorption Measurement and Rating](../materials/absorbers/absorption-measurement.md), [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md), [Metamaterial Absorbers](../materials/absorbers/metamaterial-absorbers.md), [Diffusers and Their Coefficients](../materials/diffusers/diffusers.md), [Metadiffusers](../materials/diffusers/metadiffusers.md), [Theory: Materials and Surfaces](theory/materials-surfaces.md), [Catalogue of porous materials](https://docs.jmrp.io/phonometry/reference/catalogues/porous-materials/), [Catalogue of absorption coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/absorption-coefficients/), [Catalogue of scattering coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/scattering-coefficients/), [Catalogue of diffusion coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/diffusion-coefficients/), [Catalogue of predicted scattering coefficients](https://docs.jmrp.io/phonometry/reference/catalogues/predicted-scattering-coefficients/) and [Catalogue of ground surfaces](https://docs.jmrp.io/phonometry/reference/catalogues/ground-surfaces/).
- Delany, M. E., & Bazley, E. N. (1970). Acoustical properties of fibrous absorbent materials. *Applied Acoustics*, *3*(2), 105-116. https://doi.org/10.1016/0003-682X(70)90031-9
  The original one-parameter empirical model for fibrous absorbers: the relations in frequency over flow resistivity, with their stated range of validity. The same model is the one-parameter flow-resistivity ground-impedance model.
  Cited by [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md) and [Rotorcraft noise: the hemisphere method](../aircraft/rotorcraft-noise.md).
- European Committee for Standardization. (2003). *Acoustics — Measurement of sound absorption in a reverberation room* (EN ISO 354:2003).
  Cited by [Suspended Ceilings: the EN 16487 Test Code](../materials/absorbers/suspended-ceilings.md).
- European Committee for Standardization. (2014). *Acoustics — Test code for suspended ceilings — Sound absorption* (EN 16487:2014).
  Cited by [Suspended Ceilings: the EN 16487 Test Code](../materials/absorbers/suspended-ceilings.md).
- European Committee for Standardization. (2014). *Suspended ceilings — Requirements and test methods* (EN 13964:2014).
  Cited by [Suspended Ceilings: the EN 16487 Test Code](../materials/absorbers/suspended-ceilings.md).
- European Committee for Standardization. (2015). *Thermal insulation products for buildings — Factory made mineral wool (MW) products — Specification* (EN 13162:2012+A1:2015).
  Cited by [Reading a material datasheet](../materials/reading-a-datasheet.md).
- Hargreaves, T. J., Cox, T. J., Lam, Y. W., & D'Antonio, P. (2000). Surface diffusion coefficients for room acoustics: Free-field measures of single-plane diffusion. *The Journal of the Acoustical Society of America*, *108*(4), 1710-1720. https://doi.org/10.1121/1.1310192
  The free-field diffusion-coefficient method behind ISO 17497-2 and the published N = 7 QRD geometry of the worked example.
  Cited by [Diffusers and Their Coefficients](../materials/diffusers/diffusers.md).
- International Organization for Standardization. (1996). [*Acoustics — Determination of sound absorption coefficient and impedance in impedance tubes — Part 1: Method using standing wave ratio*](https://www.iso.org/standard/18603.html) (ISO 10534-1:1996).
  Implemented as its European adoption, BS EN ISO 10534-1:2001. The standing-wave-ratio method.
  Cited by [Impedance Tube](../materials/absorbers/impedance-tube.md).
- International Organization for Standardization. (1997). [*Acoustics — Sound absorbers for use in buildings — Rating of sound absorption*](https://www.iso.org/standard/19583.html) (ISO 11654:1997).
  The weighted sound-absorption rating $\alpha_\mathrm{w}$, its shape indicators and the absorption class.
  Cited by [Your own catalogues](../io/material-catalogues.md), [Reading a material datasheet](../materials/reading-a-datasheet.md), [Sound Absorption Measurement and Rating](../materials/absorbers/absorption-measurement.md) and [Suspended Ceilings: the EN 16487 Test Code](../materials/absorbers/suspended-ceilings.md).
- International Organization for Standardization. (1998). [*Acoustics — Determination of sound absorption coefficient and impedance in impedance tubes — Part 2: Transfer-function method*](https://www.iso.org/standard/22851.html) (ISO 10534-2:1998).
  Adopted in Europe as EN ISO 10534-2:2001, and since revised as [ISO 10534-2:2023](https://www.iso.org/standard/81294.html). The two-microphone transfer-function method and its plane-wave limits.
  Cited by [Impedance Tube](../materials/absorbers/impedance-tube.md), [In-situ Road-Surface Absorption](../materials/surfaces/road-absorption.md) and [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- International Organization for Standardization. (2002). [*Acoustics — Measurement of sound absorption properties of road surfaces in situ — Part 1: Extended surface method*](https://www.iso.org/standard/35387.html) (ISO 13472-1:2002).
  The edition the library implements, since revised as ISO 13472-1:2022. The subtraction technique with the Adrienne window and the sampled-area radius.
  Cited by [In-situ Road-Surface Absorption](../materials/surfaces/road-absorption.md).
- International Organization for Standardization. (2004). [*Acoustics — Sound-scattering properties of surfaces — Part 1: Measurement of the random-incidence scattering coefficient in a reverberation room*](https://www.iso.org/standard/31397.html) (ISO 17497-1:2004+A1:2014).
  The edition the library implements. The turntable scattering-coefficient method.
  Cited by [Diffusers and Their Coefficients](../materials/diffusers/diffusers.md) and [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- International Organization for Standardization. (2010). [*Acoustics — Measurement of sound absorption properties of road surfaces in situ — Part 2: Spot method for reflective surfaces*](https://www.iso.org/standard/32304.html) (ISO 13472-2:2010).
  The edition the library implements, since revised as ISO 13472-2:2025. The spot-tube method and its plane-wave and spacing limits.
  Cited by [In-situ Road-Surface Absorption](../materials/surfaces/road-absorption.md).
- International Organization for Standardization. (2012). [*Acoustics — Sound-scattering properties of surfaces — Part 2: Measurement of the directional diffusion coefficient in a free field*](https://www.iso.org/standard/55293.html) (ISO 17497-2:2012).
  The goniometer diffusion-coefficient method.
  Cited by [Diffusers and Their Coefficients](../materials/diffusers/diffusers.md), [Metadiffusers](../materials/diffusers/metadiffusers.md) and [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- International Organization for Standardization. (2018). [*Acoustics — Determination of airflow resistance — Part 1: Static airflow method*](https://www.iso.org/standard/69869.html) (ISO 9053-1:2018).
  The static airflow-resistance method and its reference velocity.
  Cited by [Airflow Resistance](../materials/absorbers/airflow-resistance.md) and [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- International Organization for Standardization. (2020). [*Acoustics — Determination and application of measurement uncertainties in building acoustics — Part 2: Sound absorption*](https://www.iso.org/standard/68749.html) (ISO 12999-2:2020).
  The reproducibility and repeatability uncertainties of the reverberation-room quantities and their single-number ratings.
  Cited by [Sound Absorption Measurement and Rating](../materials/absorbers/absorption-measurement.md).
- International Organization for Standardization. (2020). [*Acoustics — Determination of airflow resistance — Part 2: Alternating airflow method*](https://www.iso.org/standard/76744.html) (ISO 9053-2:2020).
  The alternating airflow-resistance method with the Annex A effective ratio of specific heats.
  Cited by [Airflow Resistance](../materials/absorbers/airflow-resistance.md).
- Jiménez, N., Cox, T. J., Groby, J.-P., & Romero-García, V. (2019). [Beyond phase grating diffusers using locally-resonant metamaterials](https://pub.dega-akustik.de/ICA2019/data/articles/000706.pdf). *Proceedings of the 23rd International Congress on Acoustics (ICA 2019)*.
  The congress companion to the metadiffuser paper: the transfer-matrix chain and the slow-sound dispersion picture.
  Cited by [Metadiffusers](../materials/diffusers/metadiffusers.md).
- Jiménez, N., Cox, T. J., Romero-García, V., & Groby, J.-P. (2017). Metadiffusers: Deep-subwavelength sound diffusers. *Scientific Reports*, *7*, 5389. https://doi.org/10.1038/s41598-017-05710-5
  The metadiffuser model: resonator-loaded slits reproducing Schroeder phase profiles and ternary sequences from deep-subwavelength panels.
  Cited by [Metadiffusers](../materials/diffusers/metadiffusers.md), [2D FDTD wave simulation](../simulation/fdtd-simulation.md) and [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- Jiménez, N., Groby, J.-P., Pagneux, V., & Romero-García, V. (2017). Iridescent perfect absorption in critically-coupled acoustic metamaterials using the transfer matrix method. *Applied Sciences*, *7*(6), 618. https://doi.org/10.3390/app7060618
  The slit + Helmholtz-resonator transfer-matrix model and the critical-coupling condition.
  Cited by [Metamaterial Absorbers](../materials/absorbers/metamaterial-absorbers.md), [Metadiffusers](../materials/diffusers/metadiffusers.md) and [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- Jiménez, N., Huang, W., Romero-García, V., Pagneux, V., & Groby, J.-P. (2016). Ultra-thin metamaterial for perfect and quasi-omnidirectional sound absorption. *Applied Physics Letters*, *109*(12), 121902. https://doi.org/10.1063/1.4962328
  The resonator impedance and radiation end corrections, and the published λ/88 perfect absorber.
  Cited by [Metamaterial Absorbers](../materials/absorbers/metamaterial-absorbers.md) and [Metadiffusers](../materials/diffusers/metadiffusers.md).
- Jiménez, N., Romero-García, V., & Groby, J.-P. (2018). Perfect absorption of sound by rigidly-backed high-porous materials. *Acta Acustica united with Acustica*, *104*(3), 396-409. https://doi.org/10.3813/AAA.919183
  The critical-coupling condition applied to a rigidly-backed layer of ordinary high-porosity absorber, connecting the porous-material models of the characterisation section to perfect single-frequency absorption.
  Cited by [Theory: Materials and Surfaces](theory/materials-surfaces.md).
- Jiménez, N., Umnova, O., & Groby, J.-P. (Eds.). (2021). *Acoustic waves in periodic structures, metamaterials, and porous media*. Springer. https://doi.org/10.1007/978-3-030-84300-7
  Volume 143 of the series Topics in Applied Physics. An edited umbrella volume on resonant and periodic sound-absorbing and sound-diffusing structures, from the transfer-matrix and critical-coupling theory of metamaterial absorbers to deep-subwavelength diffusers; the modern metamaterials companion to Cox & D'Antonio.
  Cited by [Metamaterial Absorbers](../materials/absorbers/metamaterial-absorbers.md) and [Metadiffusers](../materials/diffusers/metadiffusers.md).
- Johnson, D. L., Koplik, J., & Dashen, R. (1987). Theory of dynamic permeability and tortuosity in fluid-saturated porous media. *Journal of Fluid Mechanics*, *176*, 379-402. https://doi.org/10.1017/S0022112087000727
  The dynamic-tortuosity model behind the JCA effective density.
  Cited by [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md).
- Maa, D.-Y. (1998). Potential of microperforated panel absorber. *The Journal of the Acoustical Society of America*, *104*(5), 2861-2866. https://doi.org/10.1121/1.423870
  The exact MPP impedance (Eq. 2), end corrections, design formulas and the Fig. 5 example pinned in the tests.
  Cited by [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md) and [Metamaterial Absorbers](../materials/absorbers/metamaterial-absorbers.md).
- Mechel, F. P. (Ed.). (2008). *Formulas of acoustics* (2nd ed.). Springer. https://doi.org/10.1007/978-3-540-76833-3
  ISBN 978-3-540-76832-6. Sections D.3-D.6 (layer reflection, multilayer scheme, diffuse-field integrals) and G.11 (empirical porous relations).
  Cited by [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md), [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/) and [Catalogue of porous materials](https://docs.jmrp.io/phonometry/reference/catalogues/porous-materials/).
- Miki, Y. (1990). Acoustical properties of porous materials — Modifications of Delany-Bazley models. *Journal of the Acoustical Society of Japan (E)*, *11*(1), 19-24. https://doi.org/10.1250/ast.11.19
  The positive-real regression implemented in miki.
  Cited by [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md).
- Stinson, M. R. (1991). The propagation of plane sound waves in narrow and wide circular tubes, and generalization to uniform tubes of arbitrary cross-sectional shape. *The Journal of the Acoustical Society of America*, *89*(2), 550-558. https://doi.org/10.1121/1.400379
  The visco-thermal effective parameters of the slit and the square necks and cavities.
  Cited by [Metamaterial Absorbers](../materials/absorbers/metamaterial-absorbers.md).

## Vibration and structure-borne sound

Cremer, Heckl and Petersson is the structure-borne reference, Hopkins the
building-acoustics companion that carries the measured junction data, and Ewins
the one to open for modal testing and the FRF family. The human-vibration works
are separate in kind: they support the weightings and dose measures rather than
the transmission physics above them.

- Craik, R. J. M. (1996). [*Sound transmission through buildings using statistical energy analysis*](https://openlibrary.org/isbn/9780566075728). Gower.
  ISBN 978-0-566-07572-8. The SEA treatment of airborne and structure-borne transmission in buildings, with the tabulated bending-wave transmission coefficients for X, T, L and in-line junctions.
  Cited by [Plate junctions: wave approach and experimental SEA](../vibration/structural/junction-transmission.md).
- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne sound: Structural vibrations and sound radiation at audio frequencies* (3rd ed.). Springer. https://doi.org/10.1007/b137728
  ISBN 978-3-540-22696-3. The standard monograph on structural vibration and its radiation: mobilities, power flow, vibration isolation, radiation efficiency and transmission across junctions.
  Cited by [Predicting Panel Sound Insulation](../buildings/design/panel-sound-insulation.md), [Structure-borne sound power of equipment (EN 15657)](../buildings/design/structure-borne-power.md), [Installed structure-borne sound (EN 12354-5)](../buildings/design/installed-structure-borne.md), [Mechanical mobility and the FRF family (ISO 7626-1)](../vibration/structural/mechanical-mobility.md), [Transfer stiffness of resilient elements (ISO 10846)](../vibration/structural/transfer-stiffness.md), [Sound power from surface vibration (ISO/TS 7849)](../devices/emission/vibration-sound-power.md), [Elastic waves and fluid-solid coupling](../simulation/elastic-waves.md), [Theory: Rooms and Buildings](theory/rooms-buildings.md), [Theory: Vibration](theory/vibration.md) and [Catalogue of solids](https://docs.jmrp.io/phonometry/reference/catalogues/solids/).
- Cremer, L., Heckl, M., & Ungar, E. E. (1973). *Structure-borne sound: Structural vibrations and sound radiation at audio frequencies* (1st ed.). Springer. https://doi.org/10.1007/978-3-662-10118-6
  ISBN 978-3-540-06002-4. The original derivation of the wave parameters χ and ψ and the bending-wave transmission coefficients for junctions of plates.
  Cited by [Plate junctions: wave approach and experimental SEA](../vibration/structural/junction-transmission.md).
- Deutsches Institut für Normung. (1995). *Schwingungsmessungen in der Umgebung von Schienenverkehrswegen — Teil 2: Auswerteverfahren* (DIN 45672-2:1995-07).
  Cited by [Vibration next to a railway (DIN 45672)](../vibration/immission/railway-vibration.md).
- Deutsches Institut für Normung. (1999). *Erschütterungen im Bauwesen — Teil 2: Einwirkungen auf Menschen in Gebäuden* (DIN 4150-2:1999-06).
  Cited by [Vibration and people in buildings (DIN 4150-2)](../vibration/immission/people-in-buildings.md) and [Railway vibration by category of train (E DIN 4150-2)](../vibration/immission/railway-categories.md).
- Deutsches Institut für Normung. (1999). *Erschütterungen im Bauwesen — Teil 3: Einwirkungen auf bauliche Anlagen* (DIN 4150-3:1999-02).
  Cited by [Vibration damage to structures](../vibration/structural/structural-damage.md) and [Measuring vibration immission (DIN 45669-1)](../vibration/immission/vibration-meter.md).
- Deutsches Institut für Normung. (2001). *Erschütterungen im Bauwesen — Teil 1: Vorermittlung von Schwingungsgrößen* (DIN 4150-1:2001-06).
  Cited by [Predicting vibration before measuring (DIN 4150-1)](../vibration/immission/vibration-prediction.md).
- Deutsches Institut für Normung. (2005). *Messung von Schwingungsimmissionen — Teil 2: Messverfahren* (DIN 45669-2:2005-06).
  Cited by [Vibration damage to structures](../vibration/structural/structural-damage.md), [Measuring vibration immission (DIN 45669-1)](../vibration/immission/vibration-meter.md) and [Vibration and people in buildings (DIN 4150-2)](../vibration/immission/people-in-buildings.md).
- Deutsches Institut für Normung. (2009). *Schwingungsmessungen in der Umgebung von Schienenverkehrswegen — Teil 1: Messverfahren* (DIN 45672-1:2009-12).
  Cited by [Vibration next to a railway (DIN 45672)](../vibration/immission/railway-vibration.md).
- Deutsches Institut für Normung. (2010). *Messung von Schwingungsimmissionen — Teil 1: Schwingungsmesser — Anforderungen und Prüfungen* (DIN 45669-1:2010-09).
  Cited by [Measuring vibration immission (DIN 45669-1)](../vibration/immission/vibration-meter.md), [Vibration next to a railway (DIN 45672)](../vibration/immission/railway-vibration.md) and [Vibration and people in buildings (DIN 4150-2)](../vibration/immission/people-in-buildings.md).
- Deutsches Institut für Normung. (2012). *Messung von Schwingungsimmissionen — Teil 1: Schwingungsmesser — Anforderungen und Prüfungen, Berichtigung 1* (DIN 45669-1 Ber 1:2012-12).
  Cited by [Measuring vibration immission (DIN 45669-1)](../vibration/immission/vibration-meter.md).
- Deutsches Institut für Normung. (2023). *Erschütterungen im Bauwesen — Teil 2: Einwirkungen auf Menschen in Gebäuden* (E DIN 4150-2:2023-08).
  Cited by [Railway vibration by category of train (E DIN 4150-2)](../vibration/immission/railway-categories.md) and [Predicting railway vibration (E DIN 45672-3)](../vibration/immission/railway-prediction.md).
- Deutsches Institut für Normung. (2023). *Schwingungsmessung an Schienenverkehrswegen — Teil 3: Prognoseverfahren auf Basis von Terzspektren* (E DIN 45672-3:2023-02).
  Cited by [Predicting railway vibration (E DIN 45672-3)](../vibration/immission/railway-prediction.md).
- European Parliament and Council. (2002). [*Directive 2002/44/EC on the minimum health and safety requirements regarding the exposure of workers to the risks arising from physical agents (vibration)*](https://eur-lex.europa.eu/eli/dir/2002/44/oj/eng) (Directive 2002/44/EC). Official Journal of the European Union.
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md).
- Griffin, M. J. (1996). [*Handbook of human vibration*](https://shop.elsevier.com/books/handbook-of-human-vibration/griffin/978-0-12-303041-2). Academic Press.
  ISBN 978-0-12-303041-2. The standard monograph on whole-body and hand-transmitted vibration: the biodynamics, discomfort and health-effect evidence behind the weightings, dose measures and exposure-response guidance of the vibration guides.
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md), [Multiple-shock whole-body vibration (ISO 2631-5)](../vibration/human/multiple-shock-vibration.md), [Verifying a human-vibration meter](../vibration/human/meter-verification.md) and [Theory: Vibration](theory/vibration.md).
- International Organization for Standardization. (1996). [*Acoustics — Characterization of sources of structure-borne sound with respect to sound radiation from connected structures — Measurement of velocity at the contact points of machinery when resiliently mounted*](https://www.iso.org/standard/17424.html) (ISO 9611:1996).
  The free-velocity characterization of resiliently mounted sources.
  Cited by [Structure-borne sound power of equipment (EN 15657)](../buildings/design/structure-borne-power.md).
- International Organization for Standardization. (1997). [*Mechanical vibration and shock — Evaluation of human exposure to whole-body vibration — Part 1: General requirements*](https://www.iso.org/standard/7612.html) (ISO 2631-1:1997).
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md).
- International Organization for Standardization. (2001). [*Mechanical vibration — Measurement and evaluation of human exposure to hand-transmitted vibration — Part 1: General requirements*](https://www.iso.org/standard/32355.html) (ISO 5349-1:2001).
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md).
- International Organization for Standardization. (2001). [*Mechanical vibration — Measurement and evaluation of human exposure to hand-transmitted vibration — Part 2: Practical guidance for measurement at the workplace*](https://www.iso.org/standard/27511.html) (ISO 5349-2:2001).
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md).
- International Organization for Standardization. (2001). [*Mechanical vibration and shock — Evaluation of human exposure to whole-body vibration — Part 4: Guidelines for the evaluation of the effects of vibration and rotational motion on passenger and crew comfort in fixed-guideway transport systems*](https://www.iso.org/standard/32178.html) (ISO 2631-4:2001).
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md).
- International Organization for Standardization. (2002). [*Acoustics and vibration — Laboratory measurement of vibro-acoustic transfer properties of resilient elements — Part 3: Indirect method for determination of the dynamic stiffness of resilient supports for translatory motion*](https://www.iso.org/standard/34560.html) (ISO 10846-3:2002).
  Cited by [Transfer stiffness of resilient elements (ISO 10846)](../vibration/structural/transfer-stiffness.md).
- International Organization for Standardization. (2003). *Acoustics and vibration — Laboratory measurement of vibro-acoustic transfer properties of resilient elements — Part 4: Dynamic stiffness of elements other than resilient supports for translatory motion* (ISO 10846-4:2003).
  Cited by [Transfer stiffness of resilient elements (ISO 10846)](../vibration/structural/transfer-stiffness.md).
- International Organization for Standardization. (2003). [*Mechanical vibration and shock — Evaluation of human exposure to whole-body vibration — Part 2: Vibration in buildings (1 Hz to 80 Hz)*](https://www.iso.org/standard/23012.html) (ISO 2631-2:2003).
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md).
- International Organization for Standardization. (2008). [*Acoustics and vibration — Laboratory measurement of vibro-acoustic transfer properties of resilient elements — Part 1: Principles and guidelines*](https://www.iso.org/standard/38936.html) (ISO 10846-1:2008).
  The blocking-force idealisation behind the dynamic transfer stiffness.
  Cited by [Transfer stiffness of resilient elements (ISO 10846)](../vibration/structural/transfer-stiffness.md).
- International Organization for Standardization. (2008). [*Acoustics and vibration — Laboratory measurement of vibro-acoustic transfer properties of resilient elements — Part 2: Direct method for determination of the dynamic stiffness of resilient supports for translatory motion*](https://www.iso.org/standard/38937.html) (ISO 10846-2:2008).
  Cited by [Transfer stiffness of resilient elements (ISO 10846)](../vibration/structural/transfer-stiffness.md).
- International Organization for Standardization. (2008). *Acoustics and vibration — Laboratory measurement of vibro-acoustic transfer properties of resilient elements — Part 5: Driving point method for determination of the low-frequency transfer stiffness of resilient supports for translatory motion* (ISO 10846-5:2008).
  Cited by [Transfer stiffness of resilient elements (ISO 10846)](../vibration/structural/transfer-stiffness.md).
- International Organization for Standardization. (2009). [*Acoustics — Determination of airborne sound power levels emitted by machinery using vibration measurement — Part 1: Survey method using a fixed radiation factor*](https://www.iso.org/standard/40537.html) (ISO/TS 7849-1:2009).
  The upper-limit sound power from surface velocity with ε = 1.
  Cited by [Sound power from surface vibration (ISO/TS 7849)](../devices/emission/vibration-sound-power.md) and [Theory: Vibration](theory/vibration.md).
- International Organization for Standardization. (2009). [*Acoustics — Determination of airborne sound power levels emitted by machinery using vibration measurement — Part 2: Engineering method including determination of the adequate radiation factor*](https://www.iso.org/standard/40538.html) (ISO/TS 7849-2:2009).
  The engineering method with a measured band-wise radiation factor.
  Cited by [Sound power from surface vibration (ISO/TS 7849)](../devices/emission/vibration-sound-power.md) and [Theory: Vibration](theory/vibration.md).
- International Organization for Standardization. (2009). *Mechanical vibration — Evaluation of machine vibration by measurements on non-rotating parts — Part 3: Industrial machines with nominal power above 15 kW and nominal speeds between 120 r/min and 15 000 r/min when measured in situ* (ISO 10816-3:2009).
  Cited by [Evaluating machine vibration](../vibration/machinery/machine-vibration-evaluation.md).
- International Organization for Standardization. (2010). *Mechanical vibration and shock — Vibration of fixed structures — Guidelines for the measurement of vibrations and evaluation of their effects on structures* (ISO 4866:2010).
  Cited by [Predicting a building's own frequency](../vibration/structural/building-response.md).
- International Organization for Standardization. (2011). [*Mechanical vibration and shock — Experimental determination of mechanical mobility — Part 1: Basic terms and definitions, and transducer specifications*](https://www.iso.org/standard/50426.html) (ISO 7626-1:2011).
  The FRF family and its free/blocked distinctions.
  Cited by [Mechanical mobility and the FRF family (ISO 7626-1)](../vibration/structural/mechanical-mobility.md), [Mobility by impact excitation (ISO 7626-5)](../vibration/structural/impact-mobility.md) and [Theory: Vibration](theory/vibration.md).
- International Organization for Standardization. (2015). [*Mechanical vibration and shock — Experimental determination of mechanical mobility — Part 2: Measurements using single-point translation excitation with an attached vibration exciter*](https://www.iso.org/standard/62483.html) (ISO 7626-2:2015).
  The attached-exciter measurement method and its acceptance criteria.
  Cited by [Mechanical mobility and the FRF family (ISO 7626-1)](../vibration/structural/mechanical-mobility.md) and [Mobility by impact excitation (ISO 7626-5)](../vibration/structural/impact-mobility.md).
- International Organization for Standardization. (2016). [*Mechanical vibration — Laboratory method for evaluating vehicle seat vibration — Part 1: Basic requirements*](https://www.iso.org/standard/67659.html) (ISO 10326-1:2016).
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md), [Multiple-shock whole-body vibration (ISO 2631-5)](../vibration/human/multiple-shock-vibration.md) and [What a seat does to the vibration](../vibration/human/seat-vibration.md).
- International Organization for Standardization. (2016). [*Mechanical vibration — Measurement and evaluation of machine vibration — Part 1: General guidelines*](https://www.iso.org/standard/63180.html) (ISO 20816-1:2016).
  Cited by [Evaluating machine vibration](../vibration/machinery/machine-vibration-evaluation.md).
- International Organization for Standardization. (2017). [*Human response to vibration — Measuring instrumentation — Part 1: General purpose vibration meters*](https://www.iso.org/standard/70648.html) (ISO 8041-1:2017).
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md) and [Verifying a human-vibration meter](../vibration/human/meter-verification.md).
- International Organization for Standardization. (2018). [*Mechanical vibration and shock — Evaluation of human exposure to whole-body vibration — Part 5: Method for evaluation of vibration containing multiple shocks*](https://www.iso.org/standard/50905.html) (ISO 2631-5:2018).
  Cited by [Multiple-shock whole-body vibration (ISO 2631-5)](../vibration/human/multiple-shock-vibration.md).
- International Organization for Standardization. (2018). *Mechanical vibration, shock and condition monitoring — Vocabulary* (ISO 2041:2018).
  The damping ratio, the damping coefficient over the critical one (3.2.96), against which Formula (A.3) of ISO 7626-5 is first order.
  Cited by [Mobility by impact excitation (ISO 7626-5)](../vibration/structural/impact-mobility.md).
- International Organization for Standardization. (2019). *Mechanical vibration and shock — Experimental determination of mechanical mobility — Part 5: Measurements using impact excitation with an exciter which is not attached to the structure* (ISO 7626-5:2019).
  The impact-hammer measurement: the force and exponential windows, the average over impacts, the checks on the record and the Annex A correction.
  Cited by [Mobility by impact excitation (ISO 7626-5)](../vibration/structural/impact-mobility.md).
- International Organization for Standardization. (2020). *Mechanical vibration — Measurement and evaluation of machine vibration — Part 9: Gear units* (ISO 20816-9:2020).
  Cited by [Evaluating machine vibration](../vibration/machinery/machine-vibration-evaluation.md).
- International Organization for Standardization. (2021). *Human response to vibration — Measuring instrumentation — Part 2: Personal vibration exposure meters* (ISO 8041-2:2021).
  Cited by [Verifying a human-vibration meter](../vibration/human/meter-verification.md).
- Mansfield, N. J. (2004). [*Human response to vibration*](https://www.routledge.com/Human-Response-to-Vibration/Mansfield/p/book/9780415282390). CRC Press.
  ISBN 978-0-415-28239-0. A compact modern textbook on the ISO 2631-1 and ISO 5349 evaluation chains, from perception and comfort to the occupational exposure limits.
  Cited by [Whole-body and hand-arm vibration](../vibration/human/human-vibration.md) and [Theory: Vibration](theory/vibration.md).

## Environment and transport

Attenborough and Van Renterghem is the modern reference for outdoor sound
and the source of the refraction material; Embleton's review is the shortest
route into ground effect. The barrier papers are the two ends of the same
subject, Kurze and Anderson as the closed-form fit engineering uses and Hadden
and Pierce as the exact wedge solution it approximates. The last three entries
measure what a barrier reflects rather than what it screens: EN 1793-5 is the
in situ method, and the two papers by Garai and Guidorzi are the window
construction behind its low frequency limit and the revision its 2016 edition
adopted.

- Attenborough, K., & Van Renterghem, T. (2021). *Predicting outdoor sound* (2nd ed.). CRC Press. https://doi.org/10.1201/9780429470806
  ISBN 978-1-4987-4007-4 (hbk), 978-0-429-47080-6 (ebk). Ground impedance models, the spherical-wave reflection coefficient behind the ground dip, meteorological effects on barriers, and the chapter 4 pressure-velocity FDTD reference model. Chapters 2 and 9 (spherical-wave ground reflection; outdoor barriers) and Chapter 11 (refraction by wind and temperature gradients, ray models and shadow zones).
  Cited by [Porous and Multilayer Absorbers](../materials/absorbers/porous-absorbers.md), [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md), [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md), [Atmospheric refraction: rays and the GFPE](../environment/propagation/atmospheric-refraction.md), [2D FDTD wave simulation](../simulation/fdtd-simulation.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- British Standards Institution. (2003). [*Description and measurement of environmental noise — Guide to quantities and procedures*](https://knowledge.bsigroup.com/products/description-and-measurement-of-environmental-noise-guide-to-quantities-and-procedures) (BS 7445-1:2003).
  Cited by [Environmental Levels (ISO 1996-1/-2)](../environment/assessment/environmental-levels.md).
- Deutsches Institut für Normung. (2006). *Akustik — Software-Erzeugnisse zur Berechnung der Geräuschimmission im Freien — Qualitätsanforderungen und Prüfbestimmungen* (DIN 45687:2006-05).
  Cited by [Quality of Outdoor Sound Software (ISO 17534-1)](../environment/propagation/software-quality.md).
- European Committee for Standardization. (1997). *Road traffic noise reducing devices — Test method for determining the acoustic performance — Part 3: Normalized traffic noise spectrum* (EN 1793-3:1997).
  Cited by [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md) and [Sound reflection of a noise barrier in situ](../environment/propagation/barrier-reflection.md).
- European Committee for Standardization. (2009). *Railway applications — Noise emission — Rail roughness measurement related to rolling noise generation* (EN 15610:2009).
  Cited by [Railway rolling-stock noise: the ISO 3095 type test](../environment/sources/rolling-stock-noise.md).
- European Committee for Standardization. (2010). *Railway applications — Noise emission — Characterisation of the dynamic properties of track sections for pass by noise measurements* (EN 15461:2008+A1:2010).
  Cited by [Railway rolling-stock noise: the ISO 3095 type test](../environment/sources/rolling-stock-noise.md).
- European Committee for Standardization. (2012). *Railway applications — Track — Noise barriers and related devices acting on airborne sound propagation — Test method for determining the acoustic performance — Part 3-1: Normalized railway noise spectrum and single number ratings for diffuse field applications* (EN 16272-3-1:2012).
  Cited by [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md).
- European Committee for Standardization. (2012). *Road traffic noise reducing devices — Test method for determining the acoustic performance — Part 1: Intrinsic characteristics of sound absorption under diffuse sound field conditions* (EN 1793-1:2012).
  Cited by [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md).
- European Committee for Standardization. (2012). *Road traffic noise reducing devices — Test method for determining the acoustic performance — Part 2: Intrinsic characteristics of airborne sound insulation under diffuse sound field conditions* (EN 1793-2:2012).
  Cited by [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md).
- European Committee for Standardization. (2016). *Road traffic noise reducing devices — Test method for determining the acoustic performance — Part 5: Intrinsic characteristics — In situ values of sound reflection under direct sound field conditions* (EN 1793-5:2016).
  The in situ sound reflection index of a road noise barrier: the signal subtraction and Adrienne window it shares with ISO 13472-1, the nine-microphone grid, the single number $DL_{RI}$ and the example of Annex B.
  Cited by [Sound reflection of a noise barrier in situ](../environment/propagation/barrier-reflection.md).
- European Union. (2002). [*Directive 2002/49/EC of the European Parliament and of the Council of 25 June 2002 relating to the assessment and management of environmental noise*](https://eur-lex.europa.eu/eli/dir/2002/49/oj) (Directive 2002/49/EC).
  Cited by [CNOSSOS-EU road traffic source emission](../environment/sources/cnossos-road-emission.md) and [CNOSSOS-EU railway source emission](../environment/sources/cnossos-rail-emission.md).
- European Union. (2015). [*Commission Directive (EU) 2015/996 establishing common noise assessment methods according to Directive 2002/49/EC of the European Parliament and of the Council*](https://eur-lex.europa.eu/eli/dir/2015/996/oj) (Directive (EU) 2015/996).
  Cited by [CNOSSOS-EU road traffic source emission](../environment/sources/cnossos-road-emission.md) and [CNOSSOS-EU railway source emission](../environment/sources/cnossos-rail-emission.md).
- European Union. (2018). [*Corrigendum to Commission Directive (EU) 2015/996*](<https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32015L0996R(01)>) (OJ L 5, 10.1.2018, p. 35).
  Cited by [CNOSSOS-EU road traffic source emission](../environment/sources/cnossos-road-emission.md) and [CNOSSOS-EU railway source emission](../environment/sources/cnossos-rail-emission.md).
- European Union. (2021). [*Commission Delegated Directive (EU) 2021/1226 amending, for the purposes of adapting to scientific and technical progress, Annex II to Directive 2002/49/EC as regards common assessment methods for noise*](https://eur-lex.europa.eu/eli/dir_del/2021/1226/oj) (Directive (EU) 2021/1226).
  Cited by [CNOSSOS-EU road traffic source emission](../environment/sources/cnossos-road-emission.md) and [CNOSSOS-EU railway source emission](../environment/sources/cnossos-rail-emission.md).
- Garai, M., & Guidorzi, P. (2000). European methodology for testing the airborne sound insulation characteristics of noise barriers in situ: experimental verification and comparison with laboratory data. *The Journal of the Acoustical Society of America*, *108*(3), 1054-1067. https://doi.org/10.1121/1.1286811
  Section III.D: the window that ends where the first unwanted component arrives, and the first notch of its spectrum as the low frequency limit.
  Cited by [Sound reflection of a noise barrier in situ](../environment/propagation/barrier-reflection.md).
- Guidorzi, P., & Garai, M. (2013). Advancements in sound reflection and airborne sound insulation measurement on noise barriers. *Open Journal of Acoustics*, *3*(2A), 25-38. https://doi.org/10.4236/oja.2013.32A004
  The QUIESST revision the 2016 edition of EN 1793-5 adopted: the nine-microphone grid, the sub-sample alignment and the directivity correction.
  Cited by [Sound reflection of a noise barrier in situ](../environment/propagation/barrier-reflection.md).
- Hadden, W. J., & Pierce, A. D. (1981). Sound diffraction around screens and wedges for arbitrary point source locations. *The Journal of the Acoustical Society of America*, *69*(5), 1266-1276. https://doi.org/10.1121/1.385809
  The exact wedge-diffraction solution whose flat-wedge (thin-screen) limit the barrier insertion loss uses.
  Cited by [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md).
- Institute of Acoustics, Amplitude Modulation Working Group. (2016). *A method for rating amplitude modulation in wind turbine noise*.
  Cited by [Wind turbine sound at a dwelling: IEC TS 61400-11-2](../environment/sources/wind-turbine-receptor.md).
- Institute of Acoustics, Amplitude Modulation Working Group. (2016). [*IOA AM code*](https://sourceforge.net/projects/ioa-am-code/). SourceForge.
  Cited by [Wind turbine sound at a dwelling: IEC TS 61400-11-2](../environment/sources/wind-turbine-receptor.md).
- International Electrotechnical Commission. (2005). [*Wind turbines — Part 14: Declaration of apparent sound power level and tonality values*](https://webstore.iec.ch/en/publication/5432) (IEC TS 61400-14:2005).
  Declared values and their uncertainty for a batch of turbines.
  Cited by [Wind-turbine noise: sound power and tonal audibility](../environment/sources/wind-turbine-noise.md).
- International Electrotechnical Commission. (2018). [*Wind turbines — Part 11: Acoustic noise measurement techniques*](https://webstore.iec.ch/en/publication/63367) (IEC 61400-11:2012+AMD1:2018 CSV).
  The apparent sound power geometry, wind-speed binning and tonal audibility of wind turbines.
  Cited by [Wind-turbine noise: sound power and tonal audibility](../environment/sources/wind-turbine-noise.md).
- International Electrotechnical Commission. (2024). *Wind energy generation systems – Part 11-2: Acoustic noise measurement techniques – Measurement of wind turbine sound characteristics in receptor position* (IEC TS 61400-11-2:2024).
  Cited by [Wind turbine sound at a dwelling: IEC TS 61400-11-2](../environment/sources/wind-turbine-receptor.md).
- International Organization for Standardization. (1993). [*Acoustics — Attenuation of sound during propagation outdoors — Part 1: Calculation of the absorption of sound by the atmosphere*](https://www.iso.org/standard/17426.html) (ISO 9613-1:1993).
  The pure-tone atmospheric attenuation coefficient.
  Cited by [Microphone Calibration by Reciprocity (IEC 61094-2/-3)](../signals/metrology/reciprocity-calibration.md), [Reverberation-time prediction (Sabine, Eyring, Arau)](../buildings/rooms/reverberation-prediction.md), [Sound absorption in enclosed spaces (EN 12354-6)](../buildings/rooms/enclosed-space-absorption.md), [Diffusers and Their Coefficients](../materials/diffusers/diffusers.md), [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md), [Wind turbine sound at a dwelling: IEC TS 61400-11-2](../environment/sources/wind-turbine-receptor.md), [Rotorcraft noise: the hemisphere method](../aircraft/rotorcraft-noise.md), [Sound Power in the 16 kHz Octave (ISO 9295)](../devices/emission/sound-power-high-frequency.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (1994). *Acoustics — Test surface for road vehicle noise measurement* (ISO 10844:1994).
  Cited by [Road-surface noise: the statistical pass-by method](../environment/sources/road-surface-pass-by.md).
- International Organization for Standardization. (1996). [*Acoustics — Attenuation of sound during propagation outdoors — Part 2: General method of calculation*](https://www.iso.org/standard/20649.html) (ISO 9613-2:1996).
  Revised in 2024; the 1996 method is the one the library implements. The implemented outdoor attenuation chain.
  Cited by [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md), [Quality of Outdoor Sound Software (ISO 17534-1)](../environment/propagation/software-quality.md), [CNOSSOS-EU road traffic source emission](../environment/sources/cnossos-road-emission.md), [CNOSSOS-EU railway source emission](../environment/sources/cnossos-rail-emission.md), [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (1997). *Acoustics — Characterization of pavement texture by use of surface profiles — Part 1: Determination of Mean Profile Depth* (ISO 13473-1:1997).
  Cited by [Road-surface noise: the statistical pass-by method](../environment/sources/road-surface-pass-by.md).
- International Organization for Standardization. (1997). *Acoustics — Measurement of the influence of road surfaces on traffic noise — Part 1: Statistical Pass-By method* (ISO 11819-1:1997).
  Cited by [Road-surface noise: the statistical pass-by method](../environment/sources/road-surface-pass-by.md).
- International Organization for Standardization. (2005). *Railway applications — Acoustics — Measurement of noise emitted by railbound vehicles* (ISO 3095:2005).
  Cited by [Railway rolling-stock noise: the ISO 3095 type test](../environment/sources/rolling-stock-noise.md).
- International Organization for Standardization. (2007). *Acoustics — Description, measurement and assessment of environmental noise — Part 2: Determination of sound pressure levels* (ISO 1996-2:2007).
  Cited by [Environmental Levels (ISO 1996-1/-2)](../environment/assessment/environmental-levels.md).
- International Organization for Standardization. (2009). *Acoustics — Framework for calculating a distribution of sound exposure levels for impulsive sound events for the purposes of environmental noise assessment* (ISO 13474:2009).
  Cited by [Impulsive Sound Exposure Statistics (ISO 13474)](../environment/assessment/sel-distribution.md).
- International Organization for Standardization. (2013). *Acoustics — Railway applications — Measurement of noise emitted by railbound vehicles* (ISO 3095:2013).
  Cited by [Railway rolling-stock noise: the ISO 3095 type test](../environment/sources/rolling-stock-noise.md).
- International Organization for Standardization. (2014). *Acoustics — Soundscape — Part 1: Definition and conceptual framework* (ISO 12913-1:2014).
  Cited by [Soundscape Analysis (ISO/TS 12913)](../environment/assessment/soundscape.md).
- International Organization for Standardization. (2015). *Acoustics — Software for the calculation of sound outdoors — Part 1: Quality requirements and quality assurance* (ISO 17534-1:2015).
  Cited by [Quality of Outdoor Sound Software (ISO 17534-1)](../environment/propagation/software-quality.md).
- International Organization for Standardization. (2015). [*Acoustics — Software for the calculation of sound outdoors — Part 3: Recommendations for quality assured implementation of ISO 9613-2 in software according to ISO 17534-1*](https://www.iso.org/standard/66128.html) (ISO/TR 17534-3:2015).
  Cited by [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md) and [Quality of Outdoor Sound Software (ISO 17534-1)](../environment/propagation/software-quality.md).
- International Organization for Standardization. (2016). [*Acoustics — Description, measurement and assessment of environmental noise — Part 1: Basic quantities and assessment procedures*](https://www.iso.org/standard/59765.html) (ISO 1996-1:2016).
  The environmental rating framework and its Table A.1 category adjustments.
  Cited by [Environmental Levels (ISO 1996-1/-2)](../environment/assessment/environmental-levels.md), [Impulsive-sound prominence (NT ACOU 112)](../environment/assessment/impulsive-sound.md), [Impulsive Sound Exposure Statistics (ISO 13474)](../environment/assessment/sel-distribution.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (2017). [*Acoustics — Description, measurement and assessment of environmental noise — Part 2: Determination of sound pressure levels*](https://www.iso.org/standard/59766.html) (ISO 1996-2:2017).
  The environmental measurement standard: its Annex J adopts the engineering method for tonal audibility, and the audibility criterion IEC 61400-11 reuses comes from the Annex C of its 2007 edition.
  Cited by [Objective audibility of tones in noise (ISO/PAS 20065)](../perception/psychoacoustics/tone-audibility.md), [Environmental Levels (ISO 1996-1/-2)](../environment/assessment/environmental-levels.md), [Wind-turbine noise: sound power and tonal audibility](../environment/sources/wind-turbine-noise.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (2018). *Acoustics — Soundscape — Part 2: Data collection and reporting requirements* (ISO/TS 12913-2:2018).
  Cited by [Soundscape Analysis (ISO/TS 12913)](../environment/assessment/soundscape.md).
- International Organization for Standardization. (2019). *Acoustics — Soundscape — Part 3: Data analysis* (ISO/TS 12913-3:2019).
  Cited by [Soundscape Analysis (ISO/TS 12913)](../environment/assessment/soundscape.md).
- International Organization for Standardization. (2022). [*Acoustics — Description, measurement and assessment of environmental noise — Part 3: Objective method for the measurement of prominence of impulsive sounds and for adjustment of LAeq*](https://www.iso.org/standard/77035.html) (ISO/PAS 1996-3:2022).
  The ISO successor built on the NT ACOU 112 prominence: the objective onset-analysis method `impulsive_sound_adjustment` implements, from the level history $L_{p\mathrm{AF}}$ (Clause 4), the onset detection and the least-squares onset rate (Clauses 3.3-3.5) to the prominence (Clause 5, Formula 2) and the adjustment $K_\mathrm{I}$ (Clause 6, Formula 3).
  Cited by [Impulsive-sound prominence (NT ACOU 112)](../environment/assessment/impulsive-sound.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- Jefatura del Estado (Spain). (2003). [*Ley 37/2003, de 17 de noviembre, del Ruido*](https://www.boe.es/buscar/act.php?id=BOE-A-2003-20976) (Ley 37/2003 (BOE-A-2003-20976), consolidated text).
  Cited by [Spanish Noise Regulation (RD 1367/2007)](../environment/assessment/spanish-noise-regulation.md).
- Kephalopoulos, S., Paviotti, M., & Anfosso-Lédée, F. (2012). [*Common noise assessment methods in Europe (CNOSSOS-EU)*](https://publications.jrc.ec.europa.eu/repository/handle/JRC72550) (EUR 25379 EN). Publications Office of the European Union. https://doi.org/10.2788/31776
  The common EU noise-mapping framework, contrasted with ISO 9613-2; its flow-resistivity ground classes are reused by the rotorcraft ground effect.
  Cited by [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md), [CNOSSOS-EU road traffic source emission](../environment/sources/cnossos-road-emission.md), [CNOSSOS-EU railway source emission](../environment/sources/cnossos-rail-emission.md) and [Rotorcraft noise: the hemisphere method](../aircraft/rotorcraft-noise.md).
- Kurze, U. J., & Anderson, G. S. (1971). Sound attenuation by barriers. *Applied Acoustics*, *4*(1), 35-53. https://doi.org/10.1016/0003-682X(71)90024-7
  The closed-form fit to Maekawa's chart in the Fresnel number.
  Cited by [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md).
- Maekawa, Z. (1968). Noise reduction by screens. *Applied Acoustics*, *1*(3), 157-173. https://doi.org/10.1016/0003-682X(68)90020-0
  The screen-attenuation chart against Fresnel number that barrier engineering formulas descend from.
  Cited by [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- Miljøministeriet. (2019). *Bekendtgørelse om støj fra vindmøller* (BEK nr. 135 af 07/02/2019).
  Cited by [Wind turbine sound at a dwelling: IEC TS 61400-11-2](../environment/sources/wind-turbine-receptor.md).
- Mitchell, A., Oberman, T., Aletta, F., & et al. (2024). [*The International Soundscape Database (ISD), v1.0*](https://doi.org/10.5281/zenodo.10672568). Zenodo.
  Cited by [Soundscape Analysis (ISO/TS 12913)](../environment/assessment/soundscape.md).
- Nordtest. (2002). [*Acoustics: Prominence of impulsive sounds and for adjustment of LAeq*](https://www.nordtest.info/wp/2002/05/01/acoustics-prominence-of-impulsive-sounds-and-for-adjustment-of-laeq-nt-acou-112/) (NT ACOU 112:2002).
  The freely downloadable onset-rate prominence method.
  Cited by [Impulsive-sound prominence (NT ACOU 112)](../environment/assessment/impulsive-sound.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- Salomons, E. M. (2001). *Computational atmospheric acoustics*. Kluwer Academic Publishers. https://doi.org/10.1007/978-94-010-0660-6
  ISBN 978-1-4020-0390-5. The wave-based theory of outdoor sound (parabolic equation, fast field program, refraction, turbulence) behind the engineering approximations of ISO 9613-2.
  Cited by [Outdoor Sound Propagation](../environment/propagation/outdoor-propagation.md), [Spherical ground effect and advanced barriers](../environment/propagation/ground-barriers.md), [Atmospheric refraction: rays and the GFPE](../environment/propagation/atmospheric-refraction.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- Verein Deutscher Ingenieure. (1993). *Anwendung statistischer Methoden bei der Kennzeichnung schwankender Geräuschimmissionen* (VDI 3723 Blatt 1:1993-05).
  Cited by [Quality of Outdoor Sound Software (ISO 17534-1)](../environment/propagation/software-quality.md).

## Aircraft noise

The certification documents come first here, because the quantity is defined
by them and not by a textbook; the SAE practices are the atmospheric and
spectral machinery they call up. Read ECAC Doc 29 when the question is a
contour around an airport rather than a level under a flight path.

- Chien, C. F., & Soroka, W. W. (1975). Sound propagation along an impedance plane. *Journal of Sound and Vibration*, *43*(1), 9-20. https://doi.org/10.1016/0022-460X(75)90200-X
  The two-ray interference solution over an impedance plane behind the rotorcraft ground effect.
  Cited by [Rotorcraft noise: the hemisphere method](../aircraft/rotorcraft-noise.md).
- European Civil Aviation Conference. (2016). [*Report on standard method of computing noise contours around civil airports, Volume 2: Technical guide*](https://www.ecac-ceac.org/images/documents/ECAC-Doc_29_4th_edition_Dec_2016_Volume_2.pdf) (ECAC.CEAC Doc 29, 4th ed.).
  The European airport noise-contour method: NPD interpolation and the single-event segment calculation. Listed with the other ECAC documents on the [ECAC documents page](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).
  Cited by [Airport Noise (ECAC Doc 29)](../aircraft/airport-noise.md) and [The ANP fleet database](../aircraft/anp-fleet.md).
- European Civil Aviation Conference. (2026). [*Report on standard method of computing noise contours around civil airports, Volume 2: Technical guide*](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements) (ECAC.CEAC Doc 29, 5th ed.).
  Appendix D: the SAE AIR-1845 rates that normalise the NPD data and their recalculation for a non-reference atmosphere, with its worked example.
  Cited by [NPD data for the air at the airport](../aircraft/npd-atmosphere.md).
- European Civil Aviation Conference. (2026). [*Report on standard method of computing noise contours around civil airports, Volume 3: Reference cases and verification framework*](https://www.ecac-ceac.org/images/documents/ECAC-CEAC-DOC_29_5th_Edition-REPORT_ON_STANDARD_METHOD_OF_COMPUTING_NOISE_CONTOURS_AROUND_CIVIL_AIRPORTS-Volume_3-REFERENCE_CASES_AND_VERIFICATION_FRAMEWORK.pdf) (ECAC.CEAC Doc 29, 5th ed.).
  The reference cases and workbook used to validate the single-event chain. Listed with the other ECAC documents on the [ECAC documents page](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).
  Cited by [Airport Noise (ECAC Doc 29)](../aircraft/airport-noise.md).
- European Civil Aviation Conference. (2026). [*Report on standard method of computing rotorcraft noise contours*](https://www.ecac-ceac.org/images/documents/ECAC-CEAC-DOC_32-REPORT_ON_STANDARD_METHOD_OF_COMPUTING_ROTORCRAFT_NOISE_CONTOURS.pdf) (ECAC.CEAC Doc 32, 1st ed.).
  The standard rotorcraft contour method built on the noise hemisphere. Listed with the other ECAC documents on the [ECAC documents page](https://www.ecac-ceac.org/documents/ecac-documents-and-international-agreements).
  Cited by [Rotorcraft noise: the hemisphere method](../aircraft/rotorcraft-noise.md).
- European Union Aviation Safety Agency. (2020). [*Aircraft Noise and Performance (ANP) database, version 2.3*](https://www.easa.europa.eu/en/domains/environment/policy-support-and-research/aircraft-noise-and-performance-anp-data). EASA.
  Cited by [The ANP fleet database](../aircraft/anp-fleet.md).
- International Civil Aviation Organization. (2017). [*Annex 16 to the Convention on International Civil Aviation: Environmental protection — Volume I: Aircraft noise*](https://store.icao.int/en/annex-16-environmental-protection-volume-i-aircraft-noise) (ICAO Annex 16, Vol. I, 8th ed.).
  The aircraft noise-certification standard whose Appendix 2 defines the EPNL procedure.
  Cited by [Aircraft noise: Effective Perceived Noise Level](../aircraft/aircraft-noise.md) and [Rotorcraft noise: the hemisphere method](../aircraft/rotorcraft-noise.md).
- International Civil Aviation Organization. (2018). [*Environmental technical manual — Volume I: Procedures for the noise certification of aircraft*](https://store.icao.int/en/environmental-technical-manual-volume-1-procedures-for-the-noise-certification-of-aircraft-doc-9501-1) (Doc 9501, 3rd ed.).
  The certification guidance whose worked examples (tone correction, integrated-method EPNL) serve as numeric oracles.
  Cited by [Aircraft noise: Effective Perceived Noise Level](../aircraft/aircraft-noise.md).
- International Electrotechnical Commission. (1995). [*Electroacoustics — Instruments for measurement of aircraft noise — Performance requirements for systems to measure one-third-octave-band sound pressure levels in noise certification of transport-category aeroplanes*](https://webstore.iec.ch/en/publication/5076) (IEC 61265:1995).
  Since revised as [IEC 61265:2018](https://webstore.iec.ch/en/publication/32635); the 1995 edition is the one the library implements. The aircraft-noise measurement-system performance tolerances.
  Cited by [Aircraft noise: Effective Perceived Noise Level](../aircraft/aircraft-noise.md).
- International Organization for Standardization. (1978). *Acoustics — Procedure for describing aircraft noise heard on the ground* (ISO 3891:1978).
  Withdrawn. Annex A gives the SAE ARP 866A attenuation coefficient that ECAC Doc 29 Appendix D keeps as its legacy route; Annex C is a worked tone-correction example.
  Cited by [NPD data for the air at the airport](../aircraft/npd-atmosphere.md) and [Sound Power of Multisource Industrial Plants](../devices/emission/sound-power-plant.md).
- Olsen, H., Tuinstra, M., & van Oosten, N. (2024). [*Rotorcraft noise modelling guidance*](https://www.easa.europa.eu/en/downloads/132005/en) (Research Project NOISE SC01, deliverable D1.5d, contract EASA.2020.FC.06). European Union Aviation Safety Agency.
  The NORAH2 equation-level modelling guidance, whose tables and reference hemispheres serve as oracles. The research project is described on its [EASA project page](https://www.easa.europa.eu/en/research-projects/environmental-research-rotorcraft-noise).
  Cited by [Rotorcraft noise: the hemisphere method](../aircraft/rotorcraft-noise.md).
- SAE International. (2006). [*Method for predicting lateral attenuation of airplane noise*](https://www.sae.org/standards/air5662-method-predicting-lateral-attenuation-airplane-noise/) (SAE AIR 5662).
  The soft-ground lateral-attenuation model adopted by ECAC Doc 29.
  Cited by [Airport Noise (ECAC Doc 29)](../aircraft/airport-noise.md).
- SAE International. (2012). [*Standard values of atmospheric absorption as a function of temperature and humidity*](https://www.sae.org/standards/arp866b-standard-values-atmospheric-absorption-a-function-temperature-humidity/) (SAE ARP 866B, stabilized 2012).
  The predecessor SAE atmospheric-absorption practice, source of the older 50 dB-limited Approximate Method.
  Cited by [Aircraft noise: Effective Perceived Noise Level](../aircraft/aircraft-noise.md).
- SAE International. (2013). [*Application of pure-tone atmospheric absorption losses to one-third octave-band data*](https://www.sae.org/standards/arp5534-application-pure-tone-atmospheric-absorption-losses-one-third-octave-band-data/) (SAE ARP 5534, reaffirmed 2021).
  The SAE-Method one-third-octave-band atmospheric absorption for aircraft flyover spectra.
  Cited by [Aircraft noise: Effective Perceived Noise Level](../aircraft/aircraft-noise.md) and [NPD data for the air at the airport](../aircraft/npd-atmosphere.md).

## Underwater acoustics

Urick for the vocabulary and the sonar equation, Ainslie for the modern
quantity system ISO 18405 codified and for worked numbers, and Jensen et al.
only when you reach the numerical solvers, where it is the standard reference.
Francois and Garrison, Ainslie and McColm, and Thorp are three absorption
models of decreasing scope rather than three alternatives.

- Ainslie, M. A. (2010). *Principles of sonar performance modelling*. Springer. https://doi.org/10.1007/978-3-540-87662-5
  The systematic treatment of underwater acoustical quantities in the line that ISO 18405 standardised, the Weston energy-flux propagation regimes of shallow water, the sonar equations with seven fully numeric worked examples, and the orca audiogram.
  Cited by [Underwater acoustics: radiated noise and pile driving](../underwater/underwater-acoustics.md), [Underwater sound propagation](../underwater/underwater-propagation.md) and [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md).
- Ainslie, M. A., & McColm, J. G. (1998). A simplified formula for viscous and chemical absorption in sea water. *The Journal of the Acoustical Society of America*, *103*(3), 1671-1672. https://doi.org/10.1121/1.421258
  The legible simplified seawater absorption formula.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Breeding, J. E., Jr., Pflug, L. A., Bradley, M., Walrod, M. H., & McBride, W. (1996). *Research Ambient Noise Directionality (RANDI) 3.1 physics description* (`NRL/FR/7176--95-9628`). Naval Research Laboratory.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Carey, W. M., & Evans, R. B. (2011). *Ocean ambient noise: Measurement and theory*. Springer. https://doi.org/10.1007/978-1-4419-7832-5
  The modern treatment of ocean ambient noise: the wind "rule of fives" and the Mellen thermal-noise derivation.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Chen, C.-T., & Millero, F. J. (1977). Speed of sound in seawater at high pressures. *The Journal of the Acoustical Society of America*, *62*(5), 1129-1135. https://doi.org/10.1121/1.381646
  The UNESCO international-standard sound-speed equation.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Del Grosso, V. A. (1974). New equation for the speed of sound in natural waters (with comparisons to other equations). *The Journal of the Acoustical Society of America*, *56*(4), 1084-1091. https://doi.org/10.1121/1.1903388
  The alternative pressure-based sound-speed equation.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Finneran, J. J. (2016). [*Auditory weighting functions and TTS/PTS exposure functions for marine mammals exposed to underwater noise*](https://apps.dtic.mil/sti/citations/AD1026445) (Technical Report 3026). SSC Pacific.
  The band-pass weighting-function form and the audiogram equation that the NMFS and Southall criteria both adopt.
  Cited by [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md).
- Francois, R. E., & Garrison, G. R. (1982). Sound absorption based on ocean measurements: Part I: Pure water and magnesium sulfate contributions. *The Journal of the Acoustical Society of America*, *72*(3), 896-907. https://doi.org/10.1121/1.388170
  The pure-water and magnesium-sulfate halves of the reference seawater absorption model.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Francois, R. E., & Garrison, G. R. (1982). Sound absorption based on ocean measurements. Part II: Boric acid contribution and equation for total absorption. *The Journal of the Acoustical Society of America*, *72*(6), 1879-1890. https://doi.org/10.1121/1.388673
  The boric-acid term and the complete total-absorption equation.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- International Organization for Standardization. (2016). [*Underwater acoustics — Quantities and procedures for description and measurement of underwater sound from ships — Part 1: Requirements for precision measurements in deep water used for comparison purposes*](https://www.iso.org/standard/62408.html) (ISO 17208-1:2016).
  Cited by [Underwater acoustics: radiated noise and pile driving](../underwater/underwater-acoustics.md).
- International Organization for Standardization. (2017). [*Underwater acoustics — Measurement of radiated underwater sound from percussive pile driving*](https://www.iso.org/standard/62407.html) (ISO 18406:2017).
  Cited by [Underwater acoustics: radiated noise and pile driving](../underwater/underwater-acoustics.md) and [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md).
- International Organization for Standardization. (2017). [*Underwater acoustics — Terminology*](https://www.iso.org/standard/62406.html) (ISO 18405:2017).
  Cited by [Underwater acoustics: radiated noise and pile driving](../underwater/underwater-acoustics.md), [Underwater sound propagation](../underwater/underwater-propagation.md), [Underwater propagation solvers](../underwater/underwater-solvers.md) and [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md).
- International Organization for Standardization. (2019). [*Underwater acoustics — Quantities and procedures for description and measurement of underwater sound from ships — Part 2: Determination of source levels from deep water measurements*](https://www.iso.org/standard/62409.html) (ISO 17208-2:2019).
  Cited by [Underwater acoustics: radiated noise and pile driving](../underwater/underwater-acoustics.md).
- Jensen, F. B., Kuperman, W. A., Porter, M. B., & Schmidt, H. (2011). *Computational ocean acoustics* (2nd ed.). Springer. https://doi.org/10.1007/978-1-4419-8678-8
  The reference monograph on numerical propagation: normal modes, ray tracing, Gaussian beams and the parabolic equation.
  Cited by [Underwater propagation solvers](../underwater/underwater-solvers.md).
- Leroy, C. C., & Parthiot, F. (1998). Depth-pressure relationships in the oceans and seas. *The Journal of the Acoustical Society of America*, *103*(3), 1346-1352. https://doi.org/10.1121/1.421275
  The depth-to-pressure conversion used by the sound-speed equations.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- MacGillivray, A., & de Jong, C. (2021). A reference spectrum model for estimating source levels of marine shipping based on automated identification system data. *Journal of Marine Science and Engineering*, *9*(4), 369. https://doi.org/10.3390/jmse9040369
  The open-access JOMOPANS-ECHO ship source-level model and its reference calculator.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Mackenzie, K. V. (1981). Nine-term equation for sound speed in the oceans. *The Journal of the Acoustical Society of America*, *70*(3), 807-812. https://doi.org/10.1121/1.386920
  The depth-based nine-term sound-speed equation.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Medwin, H. (1975). Speed of sound in water: A simple equation for realistic parameters. *The Journal of the Acoustical Society of America*, *58*(6), 1318-1319. https://doi.org/10.1121/1.380790
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Medwin, H., & Clay, C. S. (1998). [*Fundamentals of acoustical oceanography*](https://shop.elsevier.com/books/fundamentals-of-acoustical-oceanography/medwin/978-0-12-487570-8). Academic Press.
  ISBN 978-0-12-487570-8. Ocean acoustics from first principles; the fluid-fluid Rayleigh reflection coefficient of the seabed model, and the closed-form travel time along the circular-arc ray of a linear sound-speed gradient (Equation 3.3.20).
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md) and [Underwater propagation solvers](../underwater/underwater-solvers.md).
- Munk, W. H. (1974). Sound channel in an exponentially stratified ocean, with application to SOFAR. *The Journal of the Acoustical Society of America*, *55*(2), 220-226. https://doi.org/10.1121/1.1914492
  The canonical deep-water sound-speed profile used by the solver examples.
  Cited by [Underwater propagation solvers](../underwater/underwater-solvers.md).
- National Marine Fisheries Service. (2018). [*2018 Revision to: Technical Guidance for Assessing the Effects of Anthropogenic Sound on Marine Mammal Hearing (Version 2.0)*](https://www.fisheries.noaa.gov/s3/2023-05/TECHMEMOGuidance508.pdf) (NOAA Technical Memorandum NMFS-OPR-59). National Oceanic and Atmospheric Administration.
  The auditory weighting parameters and PTS onset thresholds of the 2018 guidance, with the Appendix D worked example.
  Cited by [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md).
- National Marine Fisheries Service. (2024). [*2024 Update to: Technical Guidance for Assessing the Effects of Anthropogenic Sound on Marine Mammal Hearing (Version 3.0)*](https://www.fisheries.noaa.gov/s3/2024-11/Tech_Memo-Guidance_-3.0-_OCT-2024-508_OPR1.pdf) (NOAA Technical Memorandum NMFS-OPR-71). National Oceanic and Atmospheric Administration.
  The current U.S. guidance: revised weighting parameters and the auditory injury onset criteria that supersede the 2018 PTS thresholds.
  Cited by [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md).
- Southall, B. L., Finneran, J. J., Reichmuth, C., Nachtigall, P. E., Ketten, D. R., Bowles, A. E., Ellison, W. T., Nowacek, D. P., & Tyack, P. L. (2019). Marine mammal noise exposure criteria: Updated scientific recommendations for residual hearing effects. *Aquatic Mammals*, *45*(2), 125-232. https://doi.org/10.1578/AM.45.2.2019.125
  The peer-reviewed hearing groups, group audiograms and TTS/PTS onset criteria, with the errata of 45(5), 569-572.
  Cited by [Marine-mammal noise exposure](../underwater/marine-mammal-exposure.md).
- Thorp, W. H. (1967). Analytic description of the low-frequency attenuation coefficient. *The Journal of the Acoustical Society of America*, *42*(1), 270. https://doi.org/10.1121/1.1910566
  The frequency-only low-frequency absorption formula.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Urick, R. J. (1983). [*Principles of underwater sound*](https://openlibrary.org/books/OL9317725M) (3rd ed.). McGraw-Hill.
  Reprinted in 1996 by Peninsula Publishing. ISBN 978-0-932146-62-5. The classic monograph on underwater sound: level conventions, ship radiated noise and the sonar-equation framework.
  Cited by [Underwater acoustics: radiated noise and pile driving](../underwater/underwater-acoustics.md) and [Underwater sound propagation](../underwater/underwater-propagation.md).
- Wales, S. C., & Heitmeyer, R. M. (2002). An ensemble source spectra model for merchant ship-radiated noise. *The Journal of the Acoustical Society of America*, *111*(3), 1211-1231. https://doi.org/10.1121/1.1427355
  The ensemble merchant-ship source-spectrum model.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Wenz, G. M. (1962). Acoustic ambient noise in the ocean: Spectra and sources. *The Journal of the Acoustical Society of America*, *34*(12), 1936-1956. https://doi.org/10.1121/1.1909155
  The classic ambient-noise survey behind the wind and thermal spectrum components.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).
- Wong, G. S. K., & Zhu, S. (1995). Speed of sound in seawater as a function of salinity, temperature, and pressure. *The Journal of the Acoustical Society of America*, *97*(3), 1732-1736. https://doi.org/10.1121/1.413048
  The ITS-90 recast of the UNESCO sound-speed coefficients, the implemented form.
  Cited by [Underwater sound propagation](../underwater/underwater-propagation.md).

## Sources and devices

These are the works behind emission rather than immission. Munjal is the
reference for ducts and mufflers and the source of the transfer-matrix
formulation; Fahy is the one to open for intensity, where the finite-difference
approximation and its errors are derived rather than asserted. The last six
entries are the broadcast-loudness chain, which is a normative stack of its own:
ITU-R BS.1770 defines the algorithms, EBU R 128 fixes the target level and the
ceiling, and the three EBU Tech documents supply the meter behaviour, the
loudness range and the production practice, together with the test signals the
implementation is validated against.

- Air-Conditioning, Heating and Refrigeration Institute. (n.d.). *Procedure for estimating occupied space sound levels in the application of air terminals and air outlets* (AHRI Standard 885).
  Cited by [Duct-Borne Noise: Fan to Room](../devices/noise-control/duct-path.md).
- American Society of Heating, Refrigerating and Air-Conditioning Engineers. (2019). *ASHRAE handbook: HVAC applications (SI edition), Chapter 49, Noise and vibration control*. ASHRAE.
  ISBN 978-1-947192-13-3. The design chapter this library reads its duct walls from: Tables 29 to 34, the breakout and break-in transmission loss of a rectangular, round and flat oval duct wall band by band, and Table 40, nine machine equipment room walls, floors and ceilings with their Sound Transmission Class.
  Cited by [Duct-Borne Noise: Fan to Room](../devices/noise-control/duct-path.md), [Catalogue of transmission loss](https://docs.jmrp.io/phonometry/reference/catalogues/transmission-loss/) and [Catalogue of duct walls](https://docs.jmrp.io/phonometry/reference/catalogues/duct-walls/).
- Arnold, F. (1999). *Experimentelle und numerische Untersuchung zur Schalleistungsbestimmung in Strömungskanälen*. VDI Verlag.
  Cited by [Sound Power in a Duct](../devices/emission/sound-power-in-duct.md).
- Asociación Española de Normalización y Certificación. (1999). *Electroacústica — Instrumentos para la medida de la intensidad acústica — Medida por medio de un par de micrófonos de presión* (UNE-EN 61043:1999).
  Cited by [Sound Intensity (p-p)](../devices/emission/intensity.md).
- Asociación Española de Normalización y Certificación. (2010). *Acústica — Determinación de los niveles de potencia acústica de las fuentes de ruido a partir de la intensidad del sonido — Parte 1: Medición en puntos discretos* (UNE-EN ISO 9614-1:2010).
  Cited by [Sound Intensity (p-p)](../devices/emission/intensity.md).
- Audio Engineering Society. (2015). [*AES standard method for digital audio engineering — Measurement of digital audio equipment*](https://www.aes.org/publications/standards/search.cfm?docID=21) (AES17-2015).
  Cited by [Electroacoustics: distortion and frequency response](../devices/electroacoustics/electroacoustics.md) and [Quasi-peak programme meter (ITU-R BS.468-4)](../devices/broadcast/quasi-peak.md).
- Barron, R. F. (2003). *Industrial noise control and acoustics*. Marcel Dekker.
  Cited by [Room to Room: Partition, Receiving Room, Criterion](../devices/noise-control/room-to-room.md).
- European Broadcasting Union. (2023). [*Guidelines for production of programmes in accordance with EBU R 128*](https://tech.ebu.ch/publications/tech3343) (EBU Tech 3343).
  The production practice behind the numbers: what to normalise, when, and what a loudness target does and does not constrain.
  Cited by [Programme loudness and true peak (BS.1770 / EBU R 128)](../devices/broadcast/program-loudness.md).
- European Broadcasting Union. (2023). [*Loudness metering: 'EBU Mode' metering to supplement loudness normalisation*](https://tech.ebu.ch/publications/tech3341) (EBU Tech 3341).
  The momentary, short-term and integrated time scales, and the Table 1 minimum-requirements test signals with their tolerances, which are synthesizable and are what the implementation is checked against.
  Cited by [Programme loudness and true peak (BS.1770 / EBU R 128)](../devices/broadcast/program-loudness.md).
- European Broadcasting Union. (2023). [*Loudness normalisation and permitted maximum level of audio signals*](https://tech.ebu.ch/publications/r128) (EBU R 128).
  The −23.0 LUFS target level, the −1 dBTP ceiling and the normalisation practice built on them.
  Cited by [Programme loudness and true peak (BS.1770 / EBU R 128)](../devices/broadcast/program-loudness.md).
- European Broadcasting Union. (2023). [*Loudness range: A measure to supplement loudness normalisation*](https://tech.ebu.ch/publications/tech3342) (EBU Tech 3342).
  The loudness range algorithm, its reference implementation and its Table 1 test signals, matched to ±1 LU.
  Cited by [Programme loudness and true peak (BS.1770 / EBU R 128)](../devices/broadcast/program-loudness.md).
- European Committee for Standardization. (2015). *Railway applications – Track – Noise barriers and related devices acting on airborne sound propagation – Test method for determining the acoustic performance – Part 7: Extrinsic characteristics – In situ values of insertion loss* (CEN/TS 16272-7:2015).
  Cited by [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- Fahy, F. J. (1995). *Sound intensity* (2nd ed.). E&FN Spon. https://doi.org/10.4324/9780203475386
  ISBN 978-0-419-19810-9. The monograph on sound energy flux: active and reactive intensity, the p-p estimator and its phase-mismatch error budget.
  Cited by [Sound Intensity (p-p)](../devices/emission/intensity.md), [Sound Power by Intensity Scanning](../devices/emission/sound-power-intensity.md), [Theory: Signal Analysis](theory/signal-analysis.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- Farina, A. (2000). [*Simultaneous measurement of impulse response and distortion with a swept-sine technique*](https://www.aes.org/e-lib/browse.cfm?elib=10211) (108th AES Convention, Paris, preprint 5093).
  The exponential-sweep deconvolution and the L·ln(n) packing of the harmonic impulse responses ahead of the linear one.
  Cited by [Swept-sine distortion and phase utilities](../devices/electroacoustics/swept-sine-distortion.md).
- Grover, F. W. (1946). *Inductance calculations: Working formulas and tables*. D. Van Nostrand.
  Cited by [Audio-Frequency Induction Loops (IEC 60118-4)](../devices/electroacoustics/induction-loops.md).
- International Electrotechnical Commission. (1925). *International standard of resistance for copper* (IEC 60028:1925).
  Cited by [Audio-Frequency Induction Loops (IEC 60118-4)](../devices/electroacoustics/induction-loops.md).
- International Electrotechnical Commission. (1991). *Acoustics — Measurement of airborne noise emitted by steam turbines and driven machinery* (IEC 61063:1991).
  Cited by [Sound Power of Steam Turbine Sets (IEC 61063)](../devices/emission/sound-power-turbines.md).
- International Electrotechnical Commission. (1993). [*Electroacoustics — Instruments for the measurement of sound intensity — Measurements with pairs of pressure sensing microphones*](https://webstore.iec.ch/en/publication/4353) (IEC 61043:1993).
  Adopted in Europe as EN 61043:1994. The p-p instrument standard: the cross-spectral estimator and the residual pressure-intensity index.
  Cited by [Compliance and verification](../signals/metrology/compliance-verification.md), [Sound Intensity (p-p)](../devices/emission/intensity.md) and [Theory: Signal Analysis](theory/signal-analysis.md).
- International Electrotechnical Commission. (2005). *Industrial-process control valves — Part 8-4: Noise considerations — Prediction of noise generated by hydrodynamic flow* (IEC 60534-8-4:2005).
  Cited by [Hydrodynamic Valve Noise (IEC 60534-8-4)](../devices/noise-control/valve-cavitation.md).
- International Electrotechnical Commission. (2010). *Industrial-process control valves — Part 8-3: Noise considerations — Control valve aerodynamic noise prediction method* (IEC 60534-8-3:2010).
  Cited by [Control Valve Noise (IEC 60534-8-3)](../devices/noise-control/control-valve-noise.md) and [Hydrodynamic Valve Noise (IEC 60534-8-4)](../devices/noise-control/valve-cavitation.md).
- International Electrotechnical Commission. (2010). *Sound system equipment – Part 7: Headphones and earphones* (IEC 60268-7:2010).
  Cited by [Headphones and Earphones (IEC 60268-7)](../devices/electroacoustics/headphones.md).
- International Electrotechnical Commission. (2013). [*Sound system equipment – Part 3: Amplifiers*](https://webstore.iec.ch/en/publication/1220) (IEC 60268-3:2013).
  Cited by [Electroacoustics: distortion and frequency response](../devices/electroacoustics/electroacoustics.md) and [Headphones and Earphones (IEC 60268-7)](../devices/electroacoustics/headphones.md).
- International Electrotechnical Commission. (2014). *Audio-frequency induction-loop systems for assisted hearing – Part 1: Methods of measuring and specifying the performance of system components* (IEC 62489-1:2010+AMD1:2014).
  Cited by [Audio-Frequency Induction Loops (IEC 60118-4)](../devices/electroacoustics/induction-loops.md).
- International Electrotechnical Commission. (2014). *Electroacoustics – Hearing aids – Part 4: Induction-loop systems for hearing aid purposes – System performance requirements* (IEC 60118-4:2014).
  Cited by [Audio-Frequency Induction Loops (IEC 60118-4)](../devices/electroacoustics/induction-loops.md).
- International Electrotechnical Commission. (2017). *Audio-frequency induction-loop systems for assisted hearing – Part 1: Methods of measuring and specifying the performance of system components – Amendment 2 (draft)* (E DIN EN 62489-1/A2:2017-10).
  Cited by [Audio-Frequency Induction Loops (IEC 60118-4)](../devices/electroacoustics/induction-loops.md).
- International Electrotechnical Commission. (2017). *Electroacoustics – Hearing aids – Part 4: Induction-loop systems for hearing aid purposes – System performance requirements – Amendment 1* (IEC 60118-4:2014/AMD1:2017).
  Cited by [Audio-Frequency Induction Loops (IEC 60118-4)](../devices/electroacoustics/induction-loops.md).
- International Organization for Standardization. (1993). [*Acoustics — Determination of sound power levels of noise sources using sound intensity — Part 1: Measurement at discrete points*](https://www.iso.org/standard/17427.html) (ISO 9614-1:1993).
  The field indicators and the dynamic-capability criterion of intensity measurement.
  Cited by [Sound Intensity (p-p)](../devices/emission/intensity.md), [Theory: Signal Analysis](theory/signal-analysis.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (1994). *Acoustics — Determination of sound power levels of multisource industrial plants for evaluation of sound pressure levels in the environment — Engineering method* (ISO 8297:1994).
  The contour round a whole industrial plant, its area, proximity and air absorption terms and the uncertainty of Table 1.
  Cited by [Sound Power of Multisource Industrial Plants](../devices/emission/sound-power-plant.md).
- International Organization for Standardization. (1995). [*Acoustics – Measurement of sound insulation in buildings and of building elements – Part 3: Laboratory measurements of airborne sound insulation of building elements*](https://www.iso.org/standard/3958.html) (ISO 140-3:1995).
  Cited by [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- International Organization for Standardization. (1995). [*Acoustics — Determination of sound insulation performances of enclosures — Part 1: Measurements under laboratory conditions (for declaration purposes)*](https://www.iso.org/standard/19500.html) (ISO 11546-1:1995).
  Cited by [Enclosures and Cabins Measured (ISO 11546, ISO 11957)](../devices/noise-control/enclosure-cabin-insulation.md) and [Industrial Noise Control: HVAC and Enclosures](../devices/noise-control/noise-control.md).
- International Organization for Standardization. (1995). [*Acoustics — Determination of sound insulation performances of enclosures — Part 2: Measurements in situ (for acceptance and verification purposes)*](https://www.iso.org/standard/21033.html) (ISO 11546-2:1995).
  Cited by [Enclosures and Cabins Measured (ISO 11546, ISO 11957)](../devices/noise-control/enclosure-cabin-insulation.md) and [Industrial Noise Control: HVAC and Enclosures](../devices/noise-control/noise-control.md).
- International Organization for Standardization. (1995). *Acoustics — Measurement of insertion loss of ducted silencers without flow — Laboratory survey method* (ISO 11691:1995).
  Cited by [Measuring a Silencer (ISO 7235 and ISO 11691)](../devices/noise-control/silencer-measurement.md).
- International Organization for Standardization. (1995). [*Acoustics — Noise emitted by machinery and equipment — Determination of emission sound pressure levels at a work station and at other specified positions from the sound power level*](https://www.iso.org/standard/21254.html) (ISO 11203:1995).
  Cited by [Emission Sound Pressure at a Work Station](../devices/emission/workstation-emission.md).
- International Organization for Standardization. (1996). [*Acoustics — Declaration and verification of noise emission values of machinery and equipment*](https://www.iso.org/standard/10855.html) (ISO 4871:1996).
  The noise-emission declaration: the dual/single-number forms, $L_{WAd} = L_{WA} + K_{WA}$ and the clause 6.2 verification.
  Cited by [Sound Power](../devices/emission/sound-power.md).
- International Organization for Standardization. (1996). *Acoustics — Determination of sound insulation performances of cabins — Laboratory and in situ measurements* (ISO 11957:1996).
  Cited by [Enclosures and Cabins Measured (ISO 11546, ISO 11957)](../devices/noise-control/enclosure-cabin-insulation.md).
- International Organization for Standardization. (1996). [*Acoustics — Determination of sound power levels of noise sources using sound intensity — Part 2: Measurement by scanning*](https://www.iso.org/standard/21247.html) (ISO 9614-2:1996).
  Cited by [Sound Power by Intensity Scanning](../devices/emission/sound-power-intensity.md).
- International Organization for Standardization. (1996). *Acoustics — Measurements of noise from silencers in situ* (ISO 11820:1996).
  Cited by [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- International Organization for Standardization. (1997). [*Acoustics – Determination of sound power levels of noise from air-terminal devices, air-terminal units, dampers and valves by measurement in a reverberation room*](https://www.iso.org/standard/22490.html) (ISO 5135:1997).
  Cited by [Measuring a Silencer (ISO 7235 and ISO 11691)](../devices/noise-control/silencer-measurement.md).
- International Organization for Standardization. (1997). *Acoustics — In-situ determination of insertion loss of outdoor noise barriers of all types* (ISO 10847:1997).
  Cited by [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- International Organization for Standardization. (1997). *Acoustics — Measurement of the in situ sound attenuation of a removable screen* (ISO 11821:1997).
  Cited by [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- International Organization for Standardization. (1998). [*Acoustics – Guidelines for noise control by silencers*](https://www.iso.org/standard/23775.html) (ISO 14163:1998).
  Cited by [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- International Organization for Standardization. (2002). [*Acoustics — Determination of sound power levels of noise sources using sound intensity — Part 3: Precision method for measurement by scanning*](https://www.iso.org/standard/24012.html) (ISO 9614-3:2002).
  Cited by [Sound Power by Intensity Scanning](../devices/emission/sound-power-intensity.md).
- International Organization for Standardization. (2003). [*Acoustics — Determination of sound power radiated into a duct by fans and other air-moving devices — In-duct method*](https://www.iso.org/obp/ui/#iso:std:iso:5136:ed-2:v1:en) (ISO 5136:2003).
  Cited by [Sound Power in a Duct](../devices/emission/sound-power-in-duct.md).
- International Organization for Standardization. (2003). [*Acoustics — Laboratory measurement procedures for ducted silencers and air-terminal units — Insertion loss, flow noise and total pressure loss*](https://www.iso.org/standard/30385.html) (ISO 7235:2003).
  Cited by [Silencers](../devices/noise-control/silencers.md), [Measuring a Silencer (ISO 7235 and ISO 11691)](../devices/noise-control/silencer-measurement.md) and [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- International Organization for Standardization. (2009). [*Quantities and units – Part 1: General*](https://www.iso.org/standard/30669.html) (ISO 80000-1:2009).
  Cited by [Enclosures and Cabins Measured (ISO 11546, ISO 11957)](../devices/noise-control/enclosure-cabin-insulation.md) and [Silencers, Screens and Barriers In Situ](../devices/noise-control/in-situ-noise-control.md).
- International Organization for Standardization. (2010). [*Acoustics — Determination of sound power levels and sound energy levels of noise sources using sound pressure — Engineering methods for an essentially free field over a reflecting plane*](https://www.iso.org/standard/52055.html) (ISO 3744:2010).
  The enveloping-surface engineering method.
  Cited by [Spatial Sound Decay in Workrooms](../buildings/rooms/workroom-sound-decay.md), [Sound Power by Pressure Methods](../devices/emission/sound-power-pressure.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (2010). *Acoustics — Determination of sound power levels and sound energy levels of noise sources using sound pressure — Engineering methods for small movable sources in reverberant fields — Part 1: Comparison method for a hard-walled test room* (ISO 3743-1:2010).
  The comparison with a reference sound source in a hard-walled room.
  Cited by [Sound Power in Small Test Rooms (ISO 3743)](../devices/emission/sound-power-test-rooms.md).
- International Organization for Standardization. (2010). [*Acoustics — Determination of sound power levels and sound energy levels of noise sources using sound pressure — Engineering/survey methods for use in situ in a reverberant environment*](https://www.iso.org/standard/46426.html) (ISO 3747:2010).
  The in situ comparison against a reference sound source.
  Cited by [Sound Power in Situ by Comparison (ISO 3747)](../devices/emission/sound-power-in-situ.md).
- International Organization for Standardization. (2010). [*Acoustics — Determination of sound power levels and sound energy levels of noise sources using sound pressure — Precision methods for reverberation test rooms*](https://www.iso.org/standard/52053.html) (ISO 3741:2010).
  The precision reverberation-room method.
  Cited by [Sound Power in the Reverberation Room](../devices/emission/sound-power-reverberation.md), [Sound Power in Small Test Rooms (ISO 3743)](../devices/emission/sound-power-test-rooms.md), [Sound Power in Situ by Comparison (ISO 3747)](../devices/emission/sound-power-in-situ.md), [Sound Power in the 16 kHz Octave (ISO 9295)](../devices/emission/sound-power-high-frequency.md), [Measuring a Silencer (ISO 7235 and ISO 11691)](../devices/noise-control/silencer-measurement.md), [Enclosures and Cabins Measured (ISO 11546, ISO 11957)](../devices/noise-control/enclosure-cabin-insulation.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (2010). [*Acoustics — Determination of sound power levels and sound energy levels of noise sources using sound pressure — Survey method using an enveloping measurement surface over a reflecting plane*](https://www.iso.org/standard/52056.html) (ISO 3746:2010).
  Cited by [Sound Power by Pressure Methods](../devices/emission/sound-power-pressure.md) and [Sound Power of Steam Turbine Sets (IEC 61063)](../devices/emission/sound-power-turbines.md).
- International Organization for Standardization. (2010). [*Acoustics — Noise emitted by machinery and equipment — Determination of emission sound pressure levels at a work station and at other specified positions applying accurate environmental corrections*](https://www.iso.org/standard/54906.html) (ISO 11204:2010).
  Cited by [Emission Sound Pressure at a Work Station](../devices/emission/workstation-emission.md).
- International Organization for Standardization. (2010). [*Acoustics — Noise emitted by machinery and equipment — Determination of emission sound pressure levels at a work station and at other specified positions applying approximate environmental corrections*](https://www.iso.org/standard/54907.html) (ISO 11202:2010).
  Cited by [Emission Sound Pressure at a Work Station](../devices/emission/workstation-emission.md).
- International Organization for Standardization. (2010). [*Acoustics — Noise emitted by machinery and equipment — Determination of emission sound pressure levels at a work station and at other specified positions in an essentially free field over a reflecting plane with negligible environmental corrections*](https://www.iso.org/standard/54908.html) (ISO 11201:2010).
  Cited by [Emission Sound Pressure at a Work Station](../devices/emission/workstation-emission.md).
- International Organization for Standardization. (2012). [*Acoustics — Determination of sound power levels and sound energy levels of noise sources using sound pressure — Precision methods for anechoic rooms and hemi-anechoic rooms*](https://www.iso.org/standard/45362.html) (ISO 3745:2012).
  The precision anechoic-room method.
  Cited by [Sound Power by Pressure Methods](../devices/emission/sound-power-pressure.md) and [Theory: Environment and Transport](theory/environment-transport.md).
- International Organization for Standardization. (2013). [*Acoustics – Rating of sound insulation in buildings and of building elements – Part 1: Airborne sound insulation*](https://www.iso.org/standard/51968.html) (ISO 717-1:2013).
  Cited by [Enclosures and Cabins Measured (ISO 11546, ISO 11957)](../devices/noise-control/enclosure-cabin-insulation.md).
- International Organization for Standardization. (2014). [*Acoustics — Noise emitted by machinery and equipment — Guidelines for the use of basic standards for the determination of emission sound pressure levels at a work station and at other specified positions*](https://www.iso.org/standard/35377.html) (ISO 11200:2014).
  Cited by [Emission Sound Pressure at a Work Station](../devices/emission/workstation-emission.md).
- International Organization for Standardization. (2015). *Acoustics — Determination of high-frequency sound power levels emitted by machinery and equipment* (ISO 9295:2015).
  Cited by [Sound Power in the 16 kHz Octave (ISO 9295)](../devices/emission/sound-power-high-frequency.md).
- International Organization for Standardization. (2017). *Acoustics — Determination of sound power levels and sound energy levels of noise sources using sound pressure — Precision methods for anechoic rooms and hemi-anechoic rooms — Amendment 1* (ISO 3745:2012/Amd.1:2017).
  Cited by [Free Field and Reference Sources (ISO 26101 / ISO 6926)](../devices/emission/free-field-qualification.md).
- International Organization for Standardization. (2017). *Acoustics — Test methods for the qualification of free-field environments* (ISO 26101:2017).
  Cited by [Free Field and Reference Sources (ISO 26101 / ISO 6926)](../devices/emission/free-field-qualification.md).
- International Organization for Standardization. (2018). *Acoustics — Determination of sound power levels of noise sources using sound pressure — Engineering methods for small, movable sources in reverberant fields — Part 2: Methods for special reverberation test rooms* (ISO 3743-2:2018).
  The direct and comparison methods of a special reverberation room.
  Cited by [Sound Power in Small Test Rooms (ISO 3743)](../devices/emission/sound-power-test-rooms.md).
- International Organization for Standardization. (2019). [*Acoustics — Determination of sound power levels of noise sources — Guidelines for the use of basic standards*](https://www.iso.org/standard/45107.html) (ISO 3740:2019).
  The selection guide for the sound-power family: grades, environments, source-size and background criteria.
  Cited by [Sound Power](../devices/emission/sound-power.md).
- International Telecommunication Union. (1986). [*Measurement of audio-frequency noise voltage level in sound broadcasting*](https://www.itu.int/rec/R-REC-BS.468/en) (Recommendation ITU-R BS.468-4).
  Cited by [Electroacoustics: distortion and frequency response](../devices/electroacoustics/electroacoustics.md), [Microphone Characterisation (IEC 60268-4)](../devices/electroacoustics/microphones.md) and [Quasi-peak programme meter (ITU-R BS.468-4)](../devices/broadcast/quasi-peak.md).
- International Telecommunication Union. (2023). [*Algorithms to measure audio programme loudness and true-peak audio level*](https://www.itu.int/rec/R-REC-BS.1770/en) (Recommendation ITU-R BS.1770-5).
  The K-weighting pre-filter (Annex 1, Tables 1-2), the channel-weighted loudness and its two-stage gating (Annex 1, Formulae 1-7 and Table 3), the true-peak estimation guidelines (Annex 2) and the position-dependent channel weights for advanced sound systems (Annex 3, Tables 4-5), in the edition approved in November 2023. It is also the loudness algorithm behind `bext="loudness"`, implemented in the broadcast area and reused when an audio file is written.
  Cited by [Reading and writing measurement audio](../io/audio-files.md) and [Programme loudness and true peak (BS.1770 / EBU R 128)](../devices/broadcast/program-loudness.md).
- Müller, S., & Massarani, P. (2001). [Transfer-function measurement with sweeps](https://aes.org/publications/elibrary-page/?id=10189). *Journal of the Audio Engineering Society*, *49*(6), 443-471.
  The sweep-measurement monograph behind the practice notes: inverse filters, fades and distortion rejection, and the synthesis of a sweep from a magnitude spectrum and a group delay (Secs. 4.2-4.3).
  Cited by [System measurement: Golay, shaped sweeps, inversion](../signals/spectra/system-measurement.md) and [Swept-sine distortion and phase utilities](../devices/electroacoustics/swept-sine-distortion.md).
- Munjal, M. L. (2014). *Acoustics of ducts and mufflers* (2nd ed.). Wiley. https://doi.org/10.1002/9781118443767
  The transfer-matrix formulation, the element matrices and the transmission loss from the compound matrix (Eq. (3.27)), and the reference treatment of dissipative and combined mufflers.
  Cited by [Silencers](../devices/noise-control/silencers.md).
- Novak, A., Lotton, P., & Simon, L. (2015). Synchronized swept-sine: Theory, application and implementation. *Journal of the Audio Engineering Society*, *63*(10), 786-798. https://doi.org/10.17743/jaes.2015.0071
  The synchronization condition that makes harmonic phases system properties, the closed-form inverse-filter spectrum used for the deconvolution and the fractional-sample separation.
  Cited by [Swept-sine distortion and phase utilities](../devices/electroacoustics/swept-sine-distortion.md).
- Reethof, G., & Ward, W. C. (1986). A theoretically based valve noise prediction method for compressible fluids. *Journal of Vibration, Acoustics, Stress, and Reliability in Design*, *108*(3), 329-338. https://doi.org/10.1115/1.3269349
  Cited by [Control Valve Noise (IEC 60534-8-3)](../devices/noise-control/control-valve-noise.md).
- Steinmetz, C. J., & Reiss, J. D. (2021). [pyloudnorm: A simple yet flexible loudness meter in Python](https://github.com/csteinmetz1/pyloudnorm). *150th AES Convention*.
  An independent BS.1770 implementation, useful as a cross-check on a gated-loudness result.
  Cited by [Programme loudness and true peak (BS.1770 / EBU R 128)](../devices/broadcast/program-loudness.md).
- Verein Deutscher Ingenieure. (2001). *Geräuscherzeugung und Lärmminderung in Raumlufttechnischen Anlagen* (VDI 2081 Blatt 1:2001-07).
  Cited by [Duct-Borne Noise: Fan to Room](../devices/noise-control/duct-path.md) and [HVAC Noise the German Way (VDI 2081)](../devices/noise-control/vdi2081-air-systems.md).
- Verein Deutscher Ingenieure. (2005). *Geräuscherzeugung und Lärmminderung in Raumlufttechnischen Anlagen — Beispiele* (VDI 2081 Blatt 2:2005-05).
  Cited by [HVAC Noise the German Way (VDI 2081)](../devices/noise-control/vdi2081-air-systems.md).

## Wave simulation

There is no governing standard for this area, so its literature is its
evidence. Bilbao is the way in for finite-difference schemes in acoustics,
Virieux the original staggered-grid elastic formulation, and Moczo et al. the
review that collects the stability and dispersion analysis the solvers are
checked against.

- Brekhovskikh, L. M., & Godin, O. A. (1990). *Acoustics of layered media I: Plane and quasi-plane waves*. Springer. https://doi.org/10.1007/978-3-642-52369-4
  The fluid-solid oracles: the oblique reflection coefficient with mode conversion, the exact Scholte characteristic equation and the three-media layer transmission.
  Cited by [Elastic waves and fluid-solid coupling](../simulation/elastic-waves.md).
- Consortium for Python Data API Standards. (n.d.). [*Python array API standard*](https://data-apis.org/array-api/latest/).
  Cited by [Where a simulation runs: NumPy, CuPy and torch](../simulation/compute.md).
- Moczo, P., Kristek, J., Galis, M., Pazak, P., & Balazovjech, M. (2007). The finite-difference and finite-element modeling of seismic wave propagation and earthquake motion. *Acta Physica Slovaca*, *57*(2), 177-406. https://doi.org/10.2478/v10155-010-0084-x
  The heterogeneous effective grid parameters (harmonic shear modulus, arithmetic density) and the stress-imaging free surface.
  Cited by [Elastic waves and fluid-solid coupling](../simulation/elastic-waves.md).
- van Vossen, R., Robertsson, J. O. A., & Chapman, C. H. (2002). Finite-difference modeling of wave propagation in a fluid-solid configuration. *Geophysics*, *67*(2), 618-624. https://doi.org/10.1190/1.1468623
  The fluid-solid benchmark of the staggered scheme: the effective-parameter averages, the soft-bed Scholte configuration and the points-per-wavelength rule for interface waves.
  Cited by [Elastic waves and fluid-solid coupling](../simulation/elastic-waves.md).
- Virieux, J. (1986). P-SV wave propagation in heterogeneous media: velocity-stress finite-difference method. *Geophysics*, *51*(4), 889-901. https://doi.org/10.1190/1.1442147
  The elastic velocity-stress scheme on the fully staggered cell, its Courant bound and dispersion relations, and the liquid as the shear-free limit.
  Cited by [Elastic waves and fluid-solid coupling](../simulation/elastic-waves.md).
- Williams, E. G. (1999). *Fourier acoustics: Sound radiation and nearfield acoustical holography*. Academic Press. https://doi.org/10.1016/B978-0-12-753960-7.X5000-1
  The Helmholtz integral equation behind the near-to-far-field transformation, with the outgoing free-space Green function and the far-field limit.
  Cited by [2D FDTD wave simulation](../simulation/fdtd-simulation.md).

## Metrology

The GUM and its supplements are the normative framework; everything else
here supports one qualification criterion. Read the GUM first even if the
question is Monte Carlo, because Supplement 1 is written as a departure from
it.

- Asociación Española de Normalización. (2017). *Electroacústica — Micrófonos de medida — Parte 5: Métodos para la calibración en presión de los micrófonos patrones de trabajo por comparación* (UNE-EN 61094-5:2017).
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- Audio Engineering Society. (2020). [*AES standard method for digital audio engineering — Measurement of digital audio equipment*](https://www.aes.org/publications/standards/search.cfm?docID=21) (AES17-2020).
  Cited by [Calibration and dBFS](../signals/metrology/calibration.md).
- Barham, R., Barrera-Figueroa, S., & Avison, J. E. M. (2014). Secondary pressure calibration of measurement microphones. *Metrologia*, *51*(3), 129-138. https://doi.org/10.1088/0026-1394/51/3/129
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- International Electrotechnical Commission. (1992). *Measurement microphones — Part 1: Specifications for laboratory standard microphones* (IEC 61094-1:1992).
  Cited by [Random-Incidence and Diffuse-Field Response (IEC 61183)](../signals/metrology/random-incidence.md).
- International Electrotechnical Commission. (1994). *Electroacoustics — Random-incidence and diffuse-field calibration of sound level meters* (IEC 61183:1994).
  Cited by [Random-Incidence and Diffuse-Field Response (IEC 61183)](../signals/metrology/random-incidence.md).
- International Electrotechnical Commission. (2000). *Measurement microphones – Part 1: Specifications for laboratory standard microphones* (IEC 61094-1:2000).
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- International Electrotechnical Commission. (2006). *Measurement microphones — Part 7: Values for the difference between free-field and pressure sensitivity levels of laboratory standard microphones* (IEC/TS 61094-7:2006).
  Cited by [Free-Field Corrections of a Sound Level Meter (IEC 62585)](../signals/metrology/free-field-corrections.md) and [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- International Electrotechnical Commission. (2009). [*Electroacoustics — Measurement microphones — Part 2: Primary method for pressure calibration of laboratory standard microphones by the reciprocity technique*](https://webstore.iec.ch/en/publication/4486) (IEC 61094-2:2009).
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md), [Microphone Calibration by Reciprocity (IEC 61094-2/-3)](../signals/metrology/reciprocity-calibration.md), [Humid air](../fluids/humid-air.md) and [Catalogue of fluids](https://docs.jmrp.io/phonometry/reference/catalogues/fluids/).
- International Electrotechnical Commission. (2012). *Electroacoustics – Measurement microphones – Part 8: Methods for determining the free-field sensitivity of working standard microphones by comparison* (IEC 61094-8:2012).
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- International Electrotechnical Commission. (2012). *Electroacoustics — Methods to determine corrections to obtain the free-field response of a sound level meter* (IEC 62585:2012).
  Cited by [Free-Field Corrections of a Sound Level Meter (IEC 62585)](../signals/metrology/free-field-corrections.md) and [Periodic Tests of a Sound Level Meter (IEC 61672-3)](../signals/metrology/sound-level-meter-periodic-tests.md).
- International Electrotechnical Commission. (2013). [*Electroacoustics — Sound level meters — Part 2: Pattern evaluation tests*](https://webstore.iec.ch/en/publication/5709) (IEC 61672-2:2013).
  Cited by [Compliance and verification](../signals/metrology/compliance-verification.md) and [Periodic Tests of a Sound Level Meter (IEC 61672-3)](../signals/metrology/sound-level-meter-periodic-tests.md).
- International Electrotechnical Commission. (2016). *Electroacoustics – Measurement microphones – Part 3: Primary method for free-field calibration of laboratory standard microphones by the reciprocity technique* (IEC 61094-3:2016).
  Cited by [Microphone Calibration by Reciprocity (IEC 61094-2/-3)](../signals/metrology/reciprocity-calibration.md).
- International Electrotechnical Commission. (2016). *Electroacoustics – Measurement microphones – Part 5: Methods for pressure calibration of working standard microphones by comparison* (IEC 61094-5:2016).
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- International Organization for Standardization. (2020). [*Acoustics — Determination and application of measurement uncertainties in building acoustics — Part 1: Sound insulation*](https://www.iso.org/standard/73930.html) (ISO 12999-1:2020).
  The domain-specific reproducibility budget for building-acoustics single-number ratings, the companion to the general GUM machinery.
  Cited by [Measurement uncertainty (GUM and Monte Carlo)](../signals/metrology/gum-uncertainty.md), [Field Insulation Measurement (ISO 16283)](../buildings/insulation/insulation-field.md) and [Theory: Rooms and Buildings](theory/rooms-buildings.md).
- Jarvis, D. R. (1996). [*Methods for determining the pressure sensitivity of working standard microphones: a report on Euromet project A311*](https://eprintspublications.npl.co.uk/439/) (NPL Report CIRA(EXT) 010). National Physical Laboratory.
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- Jarvis, D. R., & Watkins, S. (1997). *Methods for determining the pressure sensitivity of IEC type WS3 measurement microphones* (NPL Report CIRA(EXT) 022). National Physical Laboratory.
  Cited by [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md).
- Joint Committee for Guides in Metrology. (2008). [*Evaluation of measurement data — Guide to the expression of uncertainty in measurement*](https://www.bipm.org/documents/20126/2071204/JCGM_100_2008_E.pdf) (JCGM 100:2008, the GUM). BIPM. https://doi.org/10.59161/JCGM100-2008E
  The law of propagation of uncertainty implemented by the uncertainty module.
  Cited by [Measurement uncertainty (GUM and Monte Carlo)](../signals/metrology/gum-uncertainty.md), [Free-Field Corrections of a Sound Level Meter (IEC 62585)](../signals/metrology/free-field-corrections.md), [Microphone Calibration by Comparison (IEC 61094-5/-8)](../signals/metrology/comparison-calibration.md), [Microphone Calibration by Reciprocity (IEC 61094-2/-3)](../signals/metrology/reciprocity-calibration.md) and [Theory: Signal Analysis](theory/signal-analysis.md).
- Joint Committee for Guides in Metrology. (2008). [*Evaluation of measurement data — Supplement 1 to the "Guide to the expression of uncertainty in measurement" — Propagation of distributions using a Monte Carlo method*](https://www.bipm.org/documents/20126/2071204/JCGM_101_2008_E.pdf) (JCGM 101:2008). BIPM. https://doi.org/10.59161/JCGM101-2008
  The Monte Carlo propagation of distributions implemented by the Monte Carlo uncertainty engine.
  Cited by [Measurement uncertainty (GUM and Monte Carlo)](../signals/metrology/gum-uncertainty.md) and [Theory: Signal Analysis](theory/signal-analysis.md).
- Rice, S. O. (1945). Mathematical analysis of random noise. *The Bell System Technical Journal*, *24*(1), 46-156. https://doi.org/10.1002/j.1538-7305.1945.tb00453.x
  The original derivations of the expected level-crossing and maxima rates and the peak distribution of Gaussian noise that Bendat & Piersol Section 5.5 presents (their Ref. 6; Parts I-II are in volume 23, 1944).
  Cited by [Data qualification: stationarity and peaks](../signals/metrology/data-qualification.md).
- Wald, A., & Wolfowitz, J. (1940). On a test whether two samples are from the same population. *The Annals of Mathematical Statistics*, *11*(2), 147-162. https://doi.org/10.1214/aoms/1177731909
  The exact conditional distribution of the number of runs, from which the runs-about-the-median acceptance regions are computed.
  Cited by [Data qualification: stationarity and peaks](../signals/metrology/data-qualification.md).

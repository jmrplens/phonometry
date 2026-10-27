---
title: "Errata in Jarvis (1996)"
description: "Errata in Jarvis (1996): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on Jarvis (1996). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Jarvis (1996), NPL Report CIRA(EXT) 010, Appendix B (the imaginary unit of the first microphone's mass missing from the published scan)

- **Location:** Appendix B "Uncertainties caused by differences in acoustic
  impedance between the test and reference microphones" (printed folio 25),
  the acoustic impedances of the two microphones of the example. The report
  is reference [2] of IEC 61094-5:2016, which refers the air between two
  microphones to it in Table D.1 and in 7.4. Non-normative source: a
  laboratory report.
- **The print:** the parameters are listed as $r_1$, "$c$ = 48·10^-15" and
  $m_1$ for the LS2P, and $r_2$, $c_2$ and $m_2$ for the high sensitivity WS2P;
  the impedances read
  $Z_{m1}(w) = r_1 + w\cdot\ m + \frac{1}{\mathrm{i}\cdot w\cdot c_1}$ and
  $Z_{m2}(w)\ \ r_2 + w\cdot\mathrm{i}\cdot m_2 + \frac{1}{\mathrm{i}\cdot w\cdot c_2}$.
- **The problem:** the mass term of the first microphone shows neither the
  imaginary unit of the second's nor its subscript, and its compliance is
  listed as $c$ against the $c_1$ the formula uses. Read literally, $w\,m_1$
  is a resistance, not the reactance of a mass, and the circuit then gives
  0.117° and 0.0273 dB at 20 kHz, where the two graphs printed on folio 27
  end at about 0.09° and 0.025 dB;
  $r_1 + \mathrm{i}\,w\,m_1 + 1/(\mathrm{i}\,w\,c_1)$ gives 0.089° and
  0.0255 dB there, and the dip of about -0.0065 dB near 7 kHz and the phase
  peak of about 0.16° near 12.5 kHz that the graphs show. The glyphs were
  most likely lost in the reproduction rather than left out by the author:
  the folio is a worksheet whose graphs are computed from the expressions it
  displays, and blank space stands exactly where "i·" and the subscript "1"
  belong, as it does where the same folio loses other thin glyphs, the
  ":=" after $Z_{m2}(w)$, $\kappa$ and $p_0$ and the subscript of $c_1$ in
  its definition.
- **Evidence:** the two impedances as the scan shows them, the blank space
  in place of the missing glyphs, and the circuit of the same appendix
  recomputed with each reading against the printed graphs, the phase at
  20 kHz telling the two apart most clearly. Verified on PDF pages 28 and 30
  (printed pp. 25 and 27) of NPL Report CIRA(EXT) 010 (1996), the scan the
  National Physical Laboratory publishes.
- **Library behaviour:** `metrology.air_gap_series_impedance_pa_s_m3` is
  checked against the ratio Appendix B prints, with $\mathrm{i}\,w\,m_1$, and
  against the extremes of the graphs and their values at 20 kHz (the
  conformance rows on Jarvis 1996,
  [`tests/metrology/test_comparison_diameter_gap_validation.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_comparison_diameter_gap_validation.py)).
- **Status:** unreported (laboratory report rather than a standard, and a
  defect of the published scan).

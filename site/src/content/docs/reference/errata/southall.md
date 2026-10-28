---
title: "Errata in Southall et al. (2019)"
description: "Errata in Southall et al. (2019): 1 defect in the printed text, with the evidence and what phonometry does about it."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

This is the entry of the [errata registry](/phonometry/reference/errata/) on Southall et al. (2019). The registry's introduction says how each claim is checked against the printed page and what the status of an entry means.

## Southall et al. (2019), Aquatic Mammals 45(2), Table 7 (impulsive peak SPL)

*Peer-reviewed journal paper, not a standard.*

- **Location:** Table 7 (printed p. 156), the impulsive-noise TTS and PTS
  onset criteria; the two in-air carnivore rows PCA and OCA.
- **The print:** PCA TTS peak SPL 138 and PTS peak SPL 144; OCA TTS peak SPL
  161 and PTS peak SPL 167 $\text{dB re } 20\ \mu\text{Pa}$.
- **The problem:** all four are typographical errors. The authors' own errata
  (*Aquatic Mammals* 45(5), 569-572, DOI 10.1578/AM.45.5.2019.569) names all
  four on printed p. 569, "There are four typographical errors in Table 7 on
  page 156", and reprints the corrected table on printed p. 570: PCA 155 and
  161, OCA 170 and 176. The same errata also corrects the column headed "B" in
  Table 5 to the parameter b of Eq. (2), which it likewise calls a
  typographical error.
- **Evidence:** the errata itself, which names each wrong value and its
  replacement, corroborated by the article's own extrapolation rule. Note
  first what does *not* discriminate. The PTS peak = TTS peak + 6 dB rule of
  printed p. 155 is satisfied by the printed pair as well ($144 - 138 = 6$,
  just as $161 - 155 = 6$), so it says nothing about which pair is right. Nor
  does the duplication visible in the printed rows, where the peak-SPL TTS
  entry equals that same row's PTS-onset **SEL** entry (PCA 123 / 138 / 138 /
  144 and OCA 146 / 161 / 161 / 167, reading TTS SEL, TTS peak, PTS SEL, PTS
  peak): for these two in-air rows that equality is forced by two rules the
  article states on printed p. 155, both adding 15 dB to the same base TTS
  SEL, so it would hold whatever the SEL values were. An earlier revision of
  this entry read that equality as the signature of a column slip; it is
  instead the printed table being internally consistent with the article's own
  in-air method, which is what makes the errata the only thing that settles
  the matter.
  - **Value.** The corrected numbers are close to what the article's
    extrapolation rule produces, with the caveat that the rule is not stated
    for these rows. Printed p. 155 sets the impulsive peak-SPL TTS onset of a
    group without direct data at the hearing threshold at the frequency of
    best sensitivity $f_0$ plus 159 dB, and restricts that rule explicitly to
    the in-water groups: "For other species groups **in water** (LF, SI, PCW,
    and OCW), 159 dB was added to the value of the hearing threshold at f₀".
    It works the rule through for PCW: "Peak SPL TTS onset was estimated as
    212 dB re 1 µPa (53 dB at f₀ + 159 dB)". Evaluating the Table 2 group
    audiogram at the Table 4 $f_0$ reproduces the three in-water rows the
    errata does not touch (SI 219.6 against a published 220; PCW 212.5 against
    212; OCW 226.1 against 226), which validates the rule where the article
    applies it. Extending it to the two in-air carnivore rows, which the
    article does not do, gives PCA $-4.6\ \text{dB re } 20\ \mu\text{Pa}$ at
    2.3 kHz and OCA $11.4\ \text{dB re } 20\ \mu\text{Pa}$ at 10 kHz, hence
    **154.4** and **170.4**. Those reproduce the corrected 155 and 170 to
    within 0.6 dB and are 16 dB and 9 dB away from the printed 138 and 161,
    which is what makes them corroborating rather than confirming; note that
    154.4 rounds to 154, not to 155, and an earlier revision of this entry
    claimed that it rounded to the corrected value.
  - **A second, unrepaired inconsistency.** Printed p. 155 states that for the
    in-air carnivores specifically "a nominal 15 dB offset is used ... between
    the SEL-based TTS threshold and the peak SPL-based threshold", which
    reproduces the *printed* 138 and 161 from the SEL column. That sentence,
    not the +159 dB rule, is the one the article's own method applies to PCA
    and OCA. The errata resolves the conflict in favour of values consistent
    with the +159 dB rule, so it supersedes the sentence as well as the table;
    the sentence is left standing in the article.
  Verified on PDF page 31 (printed p. 155) and PDF page 32 (printed p. 156) of
  Southall et al. (2019), Aquatic Mammals 45(2), which carry the "in water
  (LF, SI, PCW, and OCW)" restriction, the 15 dB in-air offset in the same
  paragraph, both statements of the +6 dB rule, and the article's Table 7 with
  the PCA row 123 / 138 / 138 / 144 and the OCA row 146 / 161 / 161 / 167. The
  errata is a publication of its own, *Aquatic Mammals* 45(5), 569-572, bound
  at the end of the copy the authors distribute: verified there on PDF page
  109 (printed p. 569), which names all four values and their replacements,
  and PDF page 110 (printed p. 570), which reprints Table 7 with PCA 123 / 155
  / 138 / 161 and OCA 146 / 170 / 161 / 176.
- **Library behaviour:** the errata-corrected values are the ones implemented
  in
  [`bioacoustics/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/bioacoustics/weighting.py),
  pinned by `test_southall_table_7_errata_values_are_implemented`, with the
  +159 dB rule itself checked against the audiogram in
  `test_southall_impulsive_peak_spl_is_threshold_at_f0_plus_159_db` for the
  in-water groups the article restricts it to and, separately and with the
  extrapolation labelled as such, for PCA and OCA.
- **Status:** reported by the authors themselves (errata published 2019).

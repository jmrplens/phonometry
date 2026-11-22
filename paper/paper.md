---
title: "phonometry: standard-conformant acoustic measurement in Python"
tags:
  - Python
  - acoustics
  - signal processing
  - psychoacoustics
  - building acoustics
  - noise
  - metrology
authors:
  - name:
      given-names: José Manuel
      surname: Requena-Plens
    orcid: 0000-0003-1250-6212
    affiliation: 1
affiliations:
  - name: Independent researcher, València, Spain
    index: 1
date: 22 November 2026
bibliography: paper.bib
---

# Summary

`phonometry` is a pure-Python library, built on NumPy [@harris2020array] and
SciPy [@virtanen2020scipy], for acoustic measurement, analysis and prediction.
It covers sound level metrology, fractional-octave filtering, psychoacoustics,
speech intelligibility and hearing, room and building acoustics, acoustic
materials, sound power, human and structural vibration, environmental,
aircraft and transport noise, underwater acoustics, electroacoustics,
broadcast loudness and wave simulation. A result with several quantities is
an immutable record that nearly always draws its own figure and, where its
standard defines a reporting format, renders a one-page report.

What distinguishes the library is not the breadth of that list but how each
entry on it is built and verified. Every standardized metric is implemented
from the text of its governing standard, clause by clause, and every other
model from its primary published source, rather than from a secondary
description or another implementation. Where a standard publishes worked
examples, tolerance tables or nominal responses, those numbers are transcribed
into the test suite as oracles: the IEC 61672-1 weighting tolerances
[@iec61672], the IEC 61260-1 filter class limits [@iec61260], the ISO 532-1
loudness test signals [@iso532], the ISO 717-1 rating examples [@iso717],
and hundreds more. In release 4.0.1, continuous integration enforces 1899
numerical conformance checks across 111 domains, against 230 normative
designations and 121 further published sources, on every change, and the
per-check report (source and clause, expected value, computed value, delta,
verdict) is published with the documentation
(<https://phonometry.dev/reference/conformance/>).
A regression that moves a computed value outside a standard's acceptance limit
fails the build, so the conformance claim cannot silently stop being true
between releases. \autoref{fig:mask} shows one such check as the user sees it:
the realized A and C frequency weightings against the class limits of
IEC 61672-1:2013 Table 3.

![Deviation of the library's A and C frequency weightings (48 kHz) from the
design goal, against the class 1 and class 2 acceptance limits of
IEC 61672-1:2013 Table 3. The same tolerance table is transcribed in the test
suite, so this figure and the CI gate share their
oracle.\label{fig:mask}](weighting-class-mask.png){ width=90% }

# Statement of need

Researchers, acousticians and noise consultants routinely have to defend a
number against a tolerance table: a time-weighted sound level, a weighted
insulation rating, a declared sound power level. Two implementations of the
same standardized metric can nevertheless disagree, and when they do, the user
is left to guess which one the standard would side with, because the
verification evidence behind each implementation is typically partial,
informal or unpublished.

`phonometry` exists to close that gap. The project began in 2020 as
`PyOctaveBand`, a single-module octave-band filter, and took its present name
at release 3.0.0 in July 2026; the scope described here was built on that core
during 2026 and released in stages from 3.1.0 (July) to 4.0.0 (November). Its
contribution is a method as much as a library: implement from the primary
normative source, transcribe the standard's own reference values as test
oracles, and publish the full conformance evidence. Where a standard publishes
no numerical example, the implementation is anchored to the closed-form
expressions of the normative text and pinned with a synthesized case; the
conformance report labels these weaker anchorings as such instead of rounding
them up. The library targets practitioners who need defensible numbers
(measurement against IEC 61672-1 and IEC 61260-1, ratings under ISO 717 and
related building-acoustics standards, environmental indicators under ISO
1996), educators who want each quantity traceable to its defining clause, and
researchers who need a verified baseline against which to compare new methods.

# State of the field

The scientific-Python acoustics ecosystem is strong on foundations; its
normative verification, where present, is done metric by metric.
`python-acoustics` [@pythonacoustics] long served as the general-purpose
toolbox for acousticians, covering weighting, octave bands and several ISO
calculations; its repository is archived. Its community successor,
`acoustic-toolbox` [@acoustictoolbox], replaced its own IEC 61672-1 time and
frequency weighting with this library's (then named `PyOctaveBand`) in January
2026, after users reported the time-weighting filter as wrong
(<https://github.com/Universite-Gustave-Eiffel/acoustic-toolbox/pull/44>).
`pyfar` [@pyfar] is an actively developed family of packages for acoustics
research (signal classes, DSP, I/O of measurement formats, and the ISO 3382
room parameters in `pyrato`), designed as a foundation rather than as an
implementation of the standardized metric catalogue; since version 0.8 its A
and C weighting and fractional-octave filters come with checks against the
class limits of IEC 61672-1 and IEC 61260-1. Specialised toolboxes validate
individual metrics against their reference data: `MOSQITO` [@mosqito] and, in
MATLAB, `SQAT` [@sqat] do so for sound quality metrics, including Zwicker
loudness against the ISO 532-1 test signals.

Contributing the conformance method to one of the Python projects was
considered and rejected for a scope reason: per-check normative verification
only pays off when it is systematic, across the breadth of a library and
enforced in its own continuous integration, and none of the existing projects
is structured around that contract. To the author's knowledge, no library in
this space publishes conformance evidence that is unified (one harness, one
report), granular (per check, with the expected value and the delta) and live
(regenerated and enforced on every change). That is the niche `phonometry`
occupies; for signal-processing foundations it coexists with `pyfar`.

# Software design

Three design decisions carry the method. First, a computation that yields
several quantities, or a judgment against a limit, returns a typed, frozen
dataclass rather than a tuple, a bare array or a bare boolean, while a single
number stays a number: the result object keeps its numbers together with the
key parameters behind them, nearly every result exposes a `plot()` method that
draws the conventional figure for that quantity, and the results of metrics
whose standards define a reporting format (insulation ratings, absorption
classes, declared noise emission) add a `report()` method that renders a
one-page report (\autoref{fig:fiche}). The trade-off is verbosity against
provenance: a frozen result is a self-documenting evidence trail, which is
what a defensible number needs, at the cost of one attribute access compared
with returning arrays.

![The `report()` method of an airborne insulation result: a one-page test
report stating the test conditions, the measured curve, the shifted reference
curve of ISO 717-1:2020, and the weighted rating with its spectrum adaptation
terms.\label{fig:fiche}](iso717-report-fiche.png){ width=55% }

Second, the implementation is pure Python on NumPy and SciPy, with optional
Numba [@lam2015numba] acceleration for the heaviest kernels and
block-processing entry points for signals that do not fit in memory. A
compiled core would be faster still, but clause-by-clause auditability of the
numerical code, the property the whole project trades on, favours readable
Python whose lines can be mapped to the formulas they implement.

Third, the oracles live inside the test suite, not in a separate validation
document. Standards' worked examples and tolerance tables are transcribed as
test expectations, and the published conformance report is generated from the
same run that gates merges. The alternative, a hand-maintained validation
report, was rejected because it can silently drift from the code; here the
report cannot exist in a state the tests did not produce. The library is
organised in twenty-one subpackages, one per subject area, and a function is
reached through the one that owns it (`building.airborne_insulation`,
`underwater.propagation_loss`), so the call site says which area a quantity
belongs to. The documentation, in English and Spanish, pairs every metric with
a guide and a reference page that cites the clauses and formula numbers
implemented.

# Research impact statement

The realized impact belongs to the filtering core, published in 2020 as the
single-module `PyOctaveBand` and copied into research code before it was
packaged. The code released with the sound field reconstruction study of
@fernandezgrande2023 ships a copy and builds its one-third-octave error
metrics on it, the example script released with the DNN-based hearing-aid
model of @drakopoulos2023 plots one-third-octave spectra with a bundled copy
[@drakopoulos2023code], and the unmanned-aircraft auralisation code written at
the University of Salford [@uasevent] computes its band levels with it. Since
it was packaged on PyPI in January 2026, `acoustic-toolbox` declares it as a
dependency, and a third-party sound level meter package [@pythonslm] depends
on `phonometry`. Fifteen users other than the author have opened issues and
two have contributed merged changes. For the wider library, released from July
2026, the case is one of near-term significance and rests on two public,
reproducible materials. The per-check conformance report lets a study that
uses `phonometry` as a baseline name the normative checks that baseline
passes. The errata registry documents more than 350 defects found in the
published sources (misprints, examples that contradict their own normative
clauses, broken cross-references), each with its evidence, the reading the
library implements and whether it has been reported to the issuing body.

# AI usage disclosure

Generative AI tools were used throughout the development of the library, its
documentation and this paper. Anthropic's Claude Code, with the Claude models
Opus 4.8, 5 and 5.5, Fable 5, 5.1 and 5.2, Sonnet 5 and Haiku 5, drafted code,
tests and documentation prose from the author's clause-by-clause readings of
the normative texts, and AI review services (CodeRabbit, GitHub Copilot,
Gemini Code Assist, Greptile and Sourcery) commented on pull requests. The
domain knowledge the library encodes, the normative readings, the measurement
practice and the resolution of ambiguities in the texts, comes from the
author's prior research work in acoustics. The verification framework this
paper describes is also the mechanism by which AI-assisted output is
controlled: where a standard prints worked examples or tolerance tables, the
metric must reproduce them in the test suite before it ships, and the
per-check conformance report is public. The core design decisions are the
author's: the normative-source-only implementation policy, the
oracle-transcription method, the result-object architecture and the errata
registry. All AI-assisted output was reviewed, edited and validated by the
author, who is responsible for everything that enters the project.

# Acknowledgements

The author thanks the users who reported numerical discrepancies over the
years (several of the conformance checks exist because someone asked why two
implementations disagreed), and the colleagues of his research years at the
Universitat Politècnica de València, at the Gandia campus (EPSG) and at the
Institute for Instrumentation in Molecular Imaging (i3M, UPV--CSIC), where
the measurement practice behind this library was formed. This work received
no external funding.

# References

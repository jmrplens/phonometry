---
title: "Core signal analysis"
description: "The measurement core of phonometry: fractional octave filter banks, frequency and time weighting, integrated and statistical levels, calibrated spectral and correlation analysis, physical calibration and measurement uncertainty, and how those pieces chain into a sound level meter in code."
---

Everything in phonometry starts here. This section covers the chain that turns
a raw digital signal into standards-compliant acoustic numbers: split it into
**fractional octave bands** (ANSI S1.11 / IEC 61260-1), shape it with the
**frequency weightings** of IEC 61672-1, smooth it with the **Fast/Slow/Impulse
time ballistics**, and integrate it into **Leq and statistical levels**. It is,
in effect, a sound level meter decomposed into composable functions, and every
other section of the documentation builds on it: a loudness model consumes
calibrated band levels, a room parameter starts from a filtered impulse
response, an environmental rating is an adjusted Leq.
[Build a sound level meter](/phonometry/guides/sound-level-meter/) assembles
that chain end to end on a single runnable page; it is the best starting point
if you want to see the whole area at work before opening the deep guides.

Around the level chain sit the general signal-analysis tools:
**calibrated spectral estimates** (Welch PSD and cross-spectral density with
confidence intervals), **correlation and time-delay estimation** and the
**Hilbert envelope**, all stated with the Bendat & Piersol error analysis.
And two transversal concerns complete the core. **Calibration** decides what
the digital samples mean physically: results can be referenced to a measured
calibrator tone or a known sensitivity (dB SPL), or stay in digital full
scale (dBFS). **Measurement uncertainty** (the GUM and its Monte Carlo
supplement) qualifies any result computed from uncertain inputs, which is
what makes a number defensible in a report.

If you are new to the library, read
[Filter Banks](/phonometry/guides/filter-banks/) first: it introduces the band
decomposition every other page assumes. Then
[Integrated and Statistical Levels](/phonometry/guides/levels/) shows the
metrics most measurements end in, and
[Calibration and dBFS](/phonometry/guides/calibration/) anchors them to
physical units.

## [Octave filtering](/phonometry/guides/sections/octave-filtering/)

Fractional octave band decomposition and the two ways to scale it: streaming
blocks and multichannel arrays.

- [Filter Banks](/phonometry/guides/filter-banks/): the five filter
  architectures, their frequency responses, band decomposition and zero-phase
  offline filtering.
- [Block Processing](/phonometry/guides/block-processing/): stateful streaming
  analysis that carries filter state across buffers, for signals that never
  fit in memory.
- [Multichannel and Performance](/phonometry/guides/multichannel/): vectorized
  analysis of many channels at once, with performance notes.

## [Levels and weighting](/phonometry/guides/sections/levels-weighting/)

From weighted signal to reported level: the frequency weightings, the time
ballistics and the integrated, statistical and rating levels.

- [Frequency Weighting (A, C, G, Z)](/phonometry/guides/weighting/): the
  IEC 61672-1 ear-response curves and the ISO 7196 infrasound G-weighting.
- [Time Weighting](/phonometry/guides/time-weighting/): Fast, Slow and Impulse
  exponential ballistics per IEC 61672-1.
- [Integrated and Statistical Levels](/phonometry/guides/levels/): Leq and
  LAeq, percentile levels L10/L50/L90, LCpeak and SEL, noise dose (IEC 61252),
  Lden and rating levels (ISO 1996-1), and octave spectrograms.

## [Signals and spectra](/phonometry/guides/sections/signals-spectra/)

Fine-grained frequency- and time-domain analysis, every estimate calibrated
and carrying its statistical quality.

- [Calibrated spectral analysis](/phonometry/guides/spectral-analysis/): the
  Bendat & Piersol Welch estimators with their statistical quality: PSD and
  cross-spectral density with chi-square confidence intervals, the coherent
  output spectrum with the spectral SNR, 1/n-octave smoothing and
  exact-slope colored-noise generators.
- [Correlation, time delay and envelope](/phonometry/guides/correlation-delay/):
  correlation estimates with the Bendat & Piersol random errors, time-delay
  estimation by direct correlation, cross-spectrum phase slope and the
  Knapp & Carter GCC weightings, sub-sample impulse-response delay and
  alignment, and the Hilbert envelope.

## [Calibration and uncertainty](/phonometry/guides/sections/calibration-uncertainty/)

What the numbers mean and how much to trust them.

- [Calibration and dBFS](/phonometry/guides/calibration/): physical SPL
  calibration from a calibrator tone (IEC 60942) or a known sensitivity, and
  the digital dBFS mode.
- [Measurement uncertainty (GUM and Monte Carlo)](/phonometry/guides/gum-uncertainty/):
  the law of propagation of uncertainty and the Monte Carlo method of
  ISO/IEC Guide 98-3, with expanded uncertainty and coverage intervals.

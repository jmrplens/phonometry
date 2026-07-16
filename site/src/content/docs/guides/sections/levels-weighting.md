---
title: "Levels and weighting"
description: "From weighted signal to reported number: the IEC 61672-1 frequency weightings and Fast/Slow/Impulse ballistics, and the integrated, statistical, dose and rating levels built on them."
---

A sound level meter does three things to a calibrated signal, in order: it
**weights it in frequency** to mimic the ear's sensitivity, it **smooths it in
time** with a standardised ballistic, and it **integrates it into a level**.
The three pages of this section implement exactly that chain, one page per
stage, following **IEC 61672-1:2013** closely enough that the weightings are
verified against the standard's own tolerance tables in CI.

[Frequency Weighting (A, C, G, Z)](/phonometry/guides/weighting/) covers the
first stage. The A-curve tracks hearing sensitivity at moderate levels and
dominates regulation; C is nearly flat and serves peaks and low-frequency
checks; Z is unweighted by definition; and the G-curve of **ISO 7196** extends
the idea into infrasound, where conventional weightings are blind.

[Time Weighting](/phonometry/guides/time-weighting/) covers the second stage:
the exponential Fast (125 ms), Slow (1 s) and Impulse ballistics that decide
how quickly a displayed level follows the sound. phonometry implements the
exact time constants, verified against the toneburst responses of the
standard.

[Integrated and Statistical Levels](/phonometry/guides/levels/) is the payoff:
the equivalent continuous level Leq and its A-weighted LAeq, the percentile
levels L10/L50/L90 that describe fluctuating noise, LCpeak and SEL, the noise
dose of IEC 61252, the day-evening-night level Lden and the rating levels of
**ISO 1996-1** with their adjustments, plus the octave spectrogram for
visualising level against time and band at once. This is the page where most
practical measurements end, and where the environmental and occupational
sections pick up.

## Pages in this section

- [Frequency Weighting (A, C, G, Z)](/phonometry/guides/weighting/): the
  IEC 61672-1 A/C/Z curves and the ISO 7196 infrasound G-weighting.
- [Time Weighting](/phonometry/guides/time-weighting/): Fast, Slow and
  Impulse exponential ballistics.
- [Integrated and Statistical Levels](/phonometry/guides/levels/): Leq and
  LAeq, percentile levels, LCpeak/SEL, noise dose, Lden and rating levels,
  and octave spectrograms.

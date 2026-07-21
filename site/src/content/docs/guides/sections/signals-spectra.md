---
title: "Signals and spectra"
description: "Frequency- and time-domain signal analysis in phonometry: calibrated Welch spectral estimates with their statistical quality, and correlation, time-delay estimation and the Hilbert envelope."
---

Band levels answer *how much*; this section answers *what is in the signal*.
Where the rest of the core works in fractional octave bands, these pages work
with the fine-grained estimators of classical signal analysis: spectral
densities, correlation functions, delays and envelopes. They share one
discipline, taken from Bendat & Piersol: every estimate is **calibrated** (the
same dB SPL / dBFS reference frames as the rest of the library) and carries
its **statistical quality**, so a spectrum is not just a curve but a curve
with a confidence interval.

[Calibrated spectral analysis](/phonometry/guides/spectral-analysis/) is the
frequency-domain half. The Welch power and cross-spectral density estimators
report their effective number of averages, normalized random errors and
chi-square confidence intervals; the coherent output spectrum splits a
measured output into the part explained by an input and the part that is
noise, with a spectral signal-to-noise ratio; fractional-octave smoothing
bridges back to the banded world; and the colored-noise generators synthesize
white, pink, red, blue and violet test signals with an exact power-law slope.

[Time-frequency analysis](/phonometry/guides/time-frequency/) is the view in
between: the calibrated STFT spectrogram shows what happens *when* - a
passing siren, an impact, a run-up - with every cell reading an absolute
level in the same scaling as the Welch estimators, and the zoom FFT computes
the spectrum of a narrow band on an arbitrarily fine grid to separate tones
closer than a practical FFT bin.

[Correlation, time delay and envelope](/phonometry/guides/correlation-delay/)
is the time-domain half. Auto- and cross-correlation come with the
Bendat & Piersol normalizations and random errors; time-delay estimation
offers the direct correlator, the cross-spectrum phase slope and the
Knapp & Carter generalized cross-correlation weightings (Roth, SCOT, PHAT,
maximum likelihood); impulse responses can be delayed and aligned with
sub-sample precision; and the Hilbert transform yields the envelope with
instantaneous phase and frequency.

These estimators feed the rest of the library: transfer functions and
distortion analysis build on the cross-spectral machinery, room impulse
response work leans on delay estimation and alignment, and the
[uncertainty pages](/phonometry/guides/sections/calibration-uncertainty/)
supply the error-analysis vocabulary the estimates are stated in.

## Pages in this section

- [Calibrated spectral analysis](/phonometry/guides/spectral-analysis/):
  Welch PSD/CSD with chi-square confidence intervals, the coherent output
  spectrum and spectral SNR, 1/n-octave smoothing and exact-slope
  colored-noise generators.
- [Time-frequency analysis](/phonometry/guides/time-frequency/): the
  calibrated STFT spectrogram in absolute units (dB SPL for pascals) with
  the time-versus-frequency resolution trade-off, and the zoom FFT that
  resolves tones closer than a practical FFT bin.
- [Correlation, time delay and envelope](/phonometry/guides/correlation-delay/):
  correlation estimates with their random errors, time-delay estimation by
  direct correlation, phase slope and GCC weightings, sub-sample
  impulse-response alignment, and the Hilbert envelope.

---
title: "Octave filtering"
description: "Fractional octave band analysis in phonometry: the ANSI S1.11 / IEC 61260-1 filter banks and their architectures, stateful block processing for streaming signals, and vectorized multichannel analysis."
---

Acoustic analysis rarely wants a raw FFT: standards, ratings and human hearing
all work in **fractional octave bands**, frequency intervals whose width grows
proportionally with frequency. phonometry implements them as banks of
recursive filters whose **-3 dB points sit exactly on the ANSI S1.11 band
edges**, so band levels are comparable whichever filter architecture computes
them, and whose designs are verified against the class tolerances of
**IEC 61260-1:2014**.

The foundation page is [Filter Banks](/phonometry/guides/filter-banks/). It
covers the five architectures (Butterworth, Chebyshev I/II, Elliptic and
Bessel), what their frequency responses trade against each other, how a signal
is decomposed into 1/1, 1/3 or arbitrary 1/b octave bands, and the zero-phase
offline mode for analysis where filter delay must not smear the result. Under
the hood every bank is a cascade of second-order sections with multirate
decimation, which is what keeps low-frequency bands numerically stable.

The other two pages scale that foundation along two independent axes.
[Block Processing](/phonometry/guides/block-processing/) scales it in *time*:
signals that never fit in memory (hour-long recordings, live monitoring,
embedded loggers) are processed buffer by buffer with carried filter state, so
the result is bit-identical to processing the whole signal at once.
[Multichannel and Performance](/phonometry/guides/multichannel/) scales it in
*channels*: microphone arrays and multichannel recordings are analysed
vectorized, one call for all channels, with notes on where the computation
time actually goes.

Read them in that order. Everything downstream (levels, loudness, room
parameters) consumes the band signals or band levels these pages produce.

## Pages in this section

- [Filter Banks](/phonometry/guides/filter-banks/): the five filter
  architectures, frequency responses, band decomposition and zero-phase
  filtering.
- [Block Processing](/phonometry/guides/block-processing/): stateful streaming
  workflows with carried filter state.
- [Multichannel and Performance](/phonometry/guides/multichannel/): vectorized
  multichannel analysis and performance notes.

---
title: "Psychoacoustics"
description: "The perceptual metrics of sound: loudness models (ISO 532, ECMA-418-2), sharpness, tonality and roughness, the two tonal-assessment methods (ECMA-418-1 prominence and ISO/PAS 20065 audibility), and the Fastl & Zwicker psychoacoustic annoyance."
---

Psychoacoustics replaces the question "how many decibels?" with "what does the
listener perceive?". Its base quantity is **loudness**: a perceptual magnitude
in sones, computed by auditory models that account for the ear's filtering,
masking and compression. On top of loudness sit the **sound quality**
sensations that distinguish two equally loud sounds: sharpness (high-frequency
emphasis), tonality (audible discrete tones) and roughness (fast modulation).
And on top of those sits a combined **annoyance** metric that weighs them into
a single scalar.

[Loudness](/phonometry/guides/loudness/) is the foundation page. It covers the
three model families phonometry ships (Zwicker per ISO 532-1, Moore-Glasberg
per ISO 532-2/3, and the Sottek Hearing Model of ECMA-418-2) together with the
ISO 226:2023 equal-loudness contours that anchor the perceptual scale for pure
tones. [Sound Quality Metrics](/phonometry/guides/sound-quality/) adds
sharpness per DIN 45692 and the ECMA-418-2 tonality and roughness that share
the Sottek front-end.

Tones in noise get two dedicated pages because two different questions are
asked of them.
[Prominent Discrete Tones (ECMA-418-1)](/phonometry/guides/tone-prominence/)
answers a product-noise question: is this tone *prominent* by the
tone-to-noise and prominence-ratio criteria used in IT-equipment declarations?
[Objective audibility of tones in noise (ISO/PAS 20065)](/phonometry/guides/tone-audibility/)
answers an environmental one: by how many decibels does the tone exceed its
masking threshold, the audibility that feeds the tonal penalty of
ISO 1996-2.

[Psychoacoustic annoyance and fluctuation strength](/phonometry/guides/psychoacoustic-annoyance/)
closes the chain with the Fastl & Zwicker model, which combines loudness,
sharpness, roughness and the slow-modulation sensation of fluctuation strength
into a single annoyance value. Read it last: it consumes everything the other
pages define.

## Pages in this section

- [Loudness](/phonometry/guides/loudness/): Zwicker, Moore-Glasberg and
  Sottek loudness in sones, plus the ISO 226:2023 equal-loudness contours.
- [Sound Quality Metrics](/phonometry/guides/sound-quality/): sharpness
  (DIN 45692) and ECMA-418-2 tonality and roughness.
- [Prominent Discrete Tones (ECMA-418-1)](/phonometry/guides/tone-prominence/):
  tone-to-noise and prominence ratios with prominence verdicts.
- [Objective audibility of tones in noise (ISO/PAS 20065)](/phonometry/guides/tone-audibility/):
  the audibility of a tone above the masking threshold, feeding the
  ISO 1996-2 tonal adjustment.
- [Psychoacoustic annoyance and fluctuation strength](/phonometry/guides/psychoacoustic-annoyance/):
  the Fastl & Zwicker annoyance model and the fluctuation-strength models it
  consumes.

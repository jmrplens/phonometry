---
title: "Why PyOctaveBand"
description: "IEC 61672-1 compliance verification and comparison with other libraries."
---

How PyOctaveBand's time weighting relates to the **IEC 61672-1:2013** standard
(Electroacoustics — Sound level meters), and how it differs from other Python
libraries such as `python-acoustics`. This page summarizes the analysis
originally published in
[issue #38](https://github.com/jmrplens/PyOctaveBand/issues/38).

## Design philosophy

Standard time weighting is defined as a **continuous function of time** via the
differential equation

$$
\tau \frac{dy(t)}{dt} + y(t) = x^2(t)
$$

which corresponds to a stable first-order low-pass filter with a pole in the
left half-plane ($s = -1/\tau$).

| | PyOctaveBand | python-acoustics |
| :--- | :--- | :--- |
| Output | Continuous time-weighted envelope (one value per sample) | Stepped output (one value every τ seconds) |
| Input units | Raw sound pressure (Pa); squared internally | Energetic quantity (Pa²) expected as input |
| Filter | Stable exponential averaging (pole at $s=-1/\tau$) | Theoretically unstable design (pole in the right half-plane) stabilized by resetting the filter state every τ seconds |
| Behavior | True IEC time weighting | Closer to a block integrator ($L_{eq,\tau}$) |

A pole on the negative real axis corresponds to a decaying exponential impulse
response ($h(t) \propto e^{-t/\tau}$) — exactly what "exponential time
weighting" means: past events are forgotten exponentially. A pole on the
positive real axis grows without bound; block-resetting hides this but changes
the measurement's nature.

## Verification against IEC 61672-1 (tone bursts)

The rigorous test for time weighting is the **Tone Burst Response**
(IEC 61672-1, Table 3), using a 4 kHz sine burst referenced to the steady-state
level.

**PyOctaveBand results (FAST):**

| Burst duration | IEC target (dB) | PyOctaveBand (dB) | Error (dB) | Status |
| :--- | :--- | :--- | :--- | :--- |
| 200 ms | −1.0 | −0.98 | +0.02 | ✅ PASS |
| 50 ms | −4.8 | −4.82 | −0.02 | ✅ PASS |
| 10 ms | −11.1 | −11.14 | −0.04 | ✅ PASS |
| 1 ms | −20.9 | −20.99 | −0.09 | ✅ PASS |

**python-acoustics results (FAST, squared signal passed as required by that
library):**

| Burst duration | IEC target (dB) | python-acoustics (dB) | Error (dB) | Status |
| :--- | :--- | :--- | :--- | :--- |
| 200 ms | −1.0 | −0.97 | +0.03 | ✅ PASS |
| 50 ms | −4.8 | −3.93 | **+0.87** | ⚠️ FAIL |
| 10 ms | −11.1 | −10.90 | +0.20 | ✅ PASS |
| 1 ms | −20.9 | −20.90 | +0.00 | ✅ PASS |

PyOctaveBand maintains high precision across all test cases. The block-based
approach deviates significantly (> 0.8 dB) for the 50 ms burst because 125 ms
blocks cannot resolve short transient events accurately — the result depends on
how the burst aligns with the block boundaries.

## What this means in practice

- If you need **standard-compliant Fast/Slow/Impulse envelopes** (sound level
  meter behavior, one level per sample), use PyOctaveBand's
  [`time_weighting`](/PyOctaveBand/guides/time-weighting/).
- If you need **block-averaged Leq per interval**, that is a different, equally
  valid metric — you can compute it with [`leq`](/PyOctaveBand/guides/levels/) over consecutive
  slices.
- Both libraries are useful; they just answer different questions. The
  discrepancy reported in issue #38 comes from comparing a continuous envelope
  against a block integrator, not from an implementation error.

## Beyond time weighting

The same standards-first approach applies across the library:

- Filter banks place their −3 dB points on the **ANSI S1.11** band edges for
  every architecture (including Chebyshev II and Bessel, where scipy's raw
  parametrization would not).
- A/C weighting stays within **IEC 61672-1 class 1** tolerances up to 16 kHz at
  common audio rates via internal oversampling (see
  [Frequency Weighting](/PyOctaveBand/guides/weighting/)).
- The IEC tone-burst targets above are enforced in the test suite, so
  regressions are caught in CI.

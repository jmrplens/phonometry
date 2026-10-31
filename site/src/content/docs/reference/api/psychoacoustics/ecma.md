---
title: "psychoacoustics.loudness.ecma"
description: "Psychoacoustic loudness per ECMA-418-2:2025 (4th ed., Sottek Hearing Model)."
sidebar:
  label: "ecma"
---

Psychoacoustic loudness per ECMA-418-2:2025 (4th ed., Sottek Hearing Model).

Clean-room implementation of the loudness signal chain of ECMA-418-2:2025:

* the shared auditory *front-end* of Clause 5 - trigonometric fade-in and
  zero-padding (5.1.2), the cascaded outer & middle/inner ear filter
  (5.1.3, Table 1), the 53-band gammatone-like auditory filter bank
  (5.1.4, Formulae 6-17), band-dependent segmentation (5.1.5, Table 4),
  half-wave rectification (5.1.6), block RMS (5.1.7), the compressive
  nonlinearity that maps sound pressure to specific loudness (5.1.8,
  Formula 23, Table 2) and the threshold in quiet (5.1.9, Table 3),
  yielding the specific basis loudness `N'_basis(l, z)` (Formula 25)
  and, summed over the bands, the total basis loudness `N_basis(l)`
  (Formula 26) that the audibility criterion of Clause 5.1.9 reads;
* the autocorrelation-based split into tonal and noise specific loudness
  with the full Clause 6.2.3 band averaging, including the
  cross-block-size-group ACF recomputation (Clause 6.2.2-6.2.7,
  Formulae 27-48; `_tonal_noise_split`, shared with the tonality
  metric so both report the same underlying N'_tonal); and
* the loudness assembly of Clause 8 - the tonal/noise power average
  (8.1.1, Formulae 113-114), the average specific loudness (8.1.2),
  the time-dependent loudness (8.1.3, Formula 116) and the single
  representative value (8.1.4, Formula 117).

The front-end helpers (`_ear_filter_sos`, `_auditory_bandpass`
and the band-parameter tables) are written to be reused by the later
tonality and roughness metrics of the same standard without refactoring.

The calibration constant `c_N` of Formula (23) is fixed by the standard so
that a 1 kHz sinusoid at 40 dB SPL yields 1 sone_HMS. With the full
Clause 6.2.3 averaging this chain computes 0.9845 sone_HMS (-1.55 %,
outside the +/-0.25 % adjustment the standard allows for c_N; c_N is kept
at the verbatim tabulated value rather than retuned). The residual is
driven by the mandated band averaging around the block-size-boundary bands
excited by the tone's lower flank (~800-900 Hz): without any band
averaging the chain reads 0.955, with averaging restricted to
same-block-size neighbours 0.996, and with the full cross-group
recomputation 0.9845. The block-time smoothing stage and the fade-in/LP
transient contribute \< 0.01 % (the value is signal-length invariant).

ECMA-418-2 prints no value of the total basis loudness N_basis for any
signal (its Annex A is a figure of equal-loudness contours), so the tests
hold it to a closed form instead: for a steady free-field tone whose period
is a whole number of samples, the block RMS of Formula 22 is the RMS of the
band output exactly, and N'_basis(z) and N_basis follow from the
steady-state response of the printed ear filter (Formulae 4 and 5, Table 1)
and auditory filters (Formulae 8-10 and 13-17), the nonlinearity and the
threshold in quiet (Formulae 23-25, Tables 2 and 3) and the sum of
Formula 26.

The API is monaural: the quadratic-mean binaural combination of
Formula (118) (Clause 8.1.5) is not implemented: analyse each channel
separately.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AUDIBILITY_THRESHOLD_SONE_HMS

*Constant* (`float`).

```python
AUDIBILITY_THRESHOLD_SONE_HMS = 0.01
```

## EcmaLoudness

```python
EcmaLoudness(
    loudness: float,
    specific_loudness: np.ndarray,
    bark: np.ndarray,
    frequencies: np.ndarray,
    times: np.ndarray,
    loudness_vs_time: np.ndarray,
    basis_loudness_vs_time: np.ndarray,
    last_evaluated_block: int,
    field: Literal['free', 'diffuse'],
)
```

Result of an ECMA-418-2:2025 (Sottek) loudness calculation.

`loudness` is the single representative loudness N in sone_HMS
(Formula 117).  `specific_loudness` is the average specific loudness
N'(z) in sone_HMS/Bark_HMS over the 53 auditory bands (Formula 115),
with `bark` the critical-band-rate scale z (0,5..26,5 Bark_HMS) and
`frequencies` the band centre frequencies F(z).  `times` and
`loudness_vs_time` hold the time-dependent loudness N(l) at 187,5 Hz
(Formula 116).  `field` records the assumed sound field.

`basis_loudness_vs_time` is the total basis loudness N_basis(l) in
sone_HMS (Formula 26) at the same `times`, the quantity Clause 5.1.9
compares with its audibility criterion,
[`AUDIBILITY_THRESHOLD_SONE_HMS`](/phonometry/reference/api/psychoacoustics/ecma/#audibility_threshold_sone_hms) (0,01 sone_HMS). It is the
specific basis loudness N'_basis(l, z) of Formula (25), the front-end's
output before the tonal and noise split, summed over the 53 bands with
dz = 0,5. Each band computes it at its own block size, the segmentation
Clause 5.1.5.1 (Table 4) prescribes for tonality and loudness, and is
resampled by linear interpolation onto the common 187,5 Hz grid of the
1024-sample blocks (Clause 6.2.6, Table 6), the grid the tonal and noise
loudness are resampled to.

Two readings in this are the library's, as Clause 5.1.9 prints neither.
Formula (26) is printed without a time index, which Clause 5.1.7 drops
because every block is processed alike, so the library gives one value
per block of that grid. And Clause 5.1.9 names no segmentation: roughness
and fluctuation strength segment with the fixed blocks of Clause 5.1.5.2
and pad by Clause 5.1.2.2, so the N_basis they form differs from this one
for a sound that changes in time (a 60 ms 1 kHz burst at 3 dB SPL reaches
0,021 sone_HMS here and 0,0025 with the 16384-sample blocks of
roughness); the library reads it on the Table 4 segmentation that the
loudness of Clause 8 is built on.

`last_evaluated_block` is l_end of Formula (40), the index in `times`
of the last block that holds the signal: Clause 6.2.6 removes the results
of the zero padding after it, where a signal cut off abruptly leaves the
auditory filters ringing. The library compares N_basis with the criterion
block by block up to that block and calls the signal audible if it
exceeds it in any of them,
`(basis_loudness_vs_time[: last_evaluated_block + 1] > 0.01).any()`;
the block-by-block comparison and the any-block rule are the library's
reading too, since Clause 5.1.9 says neither how blocks are compared nor
how their verdicts combine. No block is dropped from the series: the
0 \<= l \<= 56 transient blocks that Formulae (115) and (117) leave out,
and the blocks after l_end, are kept, as `loudness_vs_time` keeps them.

### EcmaLoudness.plot()

```python
EcmaLoudness.plot(
    ax: None = None,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> tuple[Axes, Axes]

EcmaLoudness.plot(
    ax: Axes,
    *,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the average specific loudness N'(z) (see `phonometry._plot.psychoacoustics`).

Adds a loudness-vs-time panel.  Requires matplotlib
(`pip install "phonometry[plot]"`).

## loudness_ecma

```python
loudness_ecma(
    x: Signal | ArrayLike,
    fs: float | None = None,
    field: Literal['free', 'diffuse'] = 'free',
) -> EcmaLoudness
```

Psychoacoustic loudness per ECMA-418-2:2025 (Sottek Hearing Model).

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Calibrated sound pressure signal in pascals. Accepts a [`phonometry.io.Signal`](/phonometry/reference/api/io/io/#signal), which is where "calibrated" comes from without arithmetic: this model reads absolute levels, so an uncalibrated record is taken as if one digital unit were one pascal and the answer is wrong by however far that is from true. |
| `fs` | Sampling rate in Hz. Signals not at 48 kHz are resampled (Clause 5.1.1). Required for a bare array; a [`Signal`](/phonometry/reference/api/io/io/#signal) brings its own, and an explicit value that disagrees with it raises instead of silently winning. |
| `field` | `"free"` (default) or `"diffuse"` sound field, selecting the outer/middle-ear filter of Clause 5.1.3. |

**Returns:** An [`EcmaLoudness`](/phonometry/reference/api/psychoacoustics/ecma/#ecmaloudness) with the single loudness value N (Formula 117), the average specific loudness N'(z) (Formula 115), the time-dependent loudness N(l) (Formula 116), the total basis loudness N_basis(l) (Formula 26) the audibility criterion of Clause 5.1.9 is compared with, and the last evaluated block l_end (Formula 40).

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `fs` is not a single number, or `field` is not a text. |

The 1 kHz / 40 dB SPL sinusoid defines 1 sone_HMS via the calibration
constant of Formula (23); with the full Clause 6.2.3 averaging this
chain computes 0.9845 sone_HMS for it (see the module docstring for the
residual's origin). Monaural only (no Clause 8.1.5 binaural combination).

# EBU programme-loudness — derived validation data

## What this folder contains

`ebu_programme_block_loudness.npz` holds **block-loudness series** measured from
the authentic-programme cases of the *EBU loudness test set* (v04). They are used
by the test suite to validate the gating and loudness-range stages of
`phonometry.broadcast.program_loudness` against the EBU Tech 3341/3342 targets
without any network access.

| Array | Blocks | Source case | Content |
| :--- | :--- | :--- | :--- |
| `nlr_momentary` | 400 ms / 100 ms hop | Tech 3341 case 7 (NLR narration) | Momentary loudness series, LUFS (the BS.1770-5 integrated-loudness gate input) |
| `nlr_short_term` | 3 s / 100 ms hop | Tech 3342 case 5 (NLR) | Short-term loudness series, LUFS (the loudness-range input) |
| `wlr_momentary` | 400 ms / 100 ms hop | Tech 3341 case 8 (WLR movie/drama) | Momentary loudness series, LUFS |
| `wlr_short_term` | 3 s / 100 ms hop | Tech 3342 case 6 (WLR) | Short-term loudness series, LUFS |

The series were measured with `phonometry.broadcast.program_loudness` from
`seq-3341-7_seq-3342-5-24bit.wav` (NLR) and
`seq-3341-2011-8_seq-3342-6-24bit-v02.wav` (WLR), then stored rounded to
0.0001 LU (three orders of magnitude below the official tolerances). They pin
the integrated loudness to `-23.0 LUFS` and the loudness range to `5 LU` (NLR)
and `15 LU` (WLR), the EBU-published targets for those cases.

## Why only the derived series, not the audio

These are **measurement data, not audio**: a per-block loudness envelope at a
100 ms hop cannot reconstruct the programme signal. The authentic-programme WAVs
themselves are **not** committed. The EBU loudness test set is distributed free
for technical testing, but its cases 7/8 and 5/6 use real programme material
(narration and a movie/drama segment) that carries its own third-party rights,
so redistributing the audio in this repository is out of scope. The committed
series carry none of that content and are safe to version.

## Source and authorship

- Derived from the **EBU loudness test set** (v04), © EBU (European Broadcasting
  Union), distributed for technical testing at
  <https://tech.ebu.ch/publications/ebu-loudness-test-set>.
- The target values reproduced by these series are defined in **EBU Tech 3341**
  (loudness metering) and **EBU Tech 3342** (loudness range), which in turn build
  on ITU-R BS.1770.
- The `.npz` itself is an original transcription of numeric measurements, not an
  EBU file.

## Purpose and scope of use

The series are consumed by `tests/broadcast/test_ebu_material_series.py` to
demonstrate that this library's independent gating and loudness-range
implementation reproduces the EBU authentic-programme targets, everywhere
including CI cells without network access. They are **not** part of the
`phonometry` package and are not installed with it.

The full signal chain (the K-weighting front end included) is exercised against
the original audio in `tests/broadcast/test_ebu_material_oracle.py`, which runs
only where the EBU set is present locally (point `EBU_LOUDNESS_TEST_SET` at it,
or drop it under `plan/dsp-sources/ebu-loudness-test-set/`); that test skips
otherwise. The synthesizable EBU cases are covered with generated signals in
`tests/broadcast/test_program_loudness.py`.

## Removal policy

If you represent the EBU and consider that publishing these derived series
exceeds the intended use of the test set, please open an issue or contact the
maintainer (see `CITATION.cff`) and they will be removed promptly, together
with the `tests/broadcast/test_ebu_material_series.py` tests that read them.

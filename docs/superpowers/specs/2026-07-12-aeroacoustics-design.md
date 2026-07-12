# Aeroacoustics domain design (ICAO EPNL, IEC 61400-11, IEC 61265)

**Status:** approved (design), 2026-07-12
**Task:** #19 PR-B (aeroacoustics), delivered as two PRs.
**Scope decision:** all three standards, split into **PR-B1 (aircraft noise:
ICAO Annex 16 EPNL + IEC 61265 verifier)** and **PR-B2 (wind-turbine noise:
IEC 61400-11)**.

## Purpose

Add an aeroacoustics domain to `phonometry`, implemented clean-room from the
standard texts with worked-example / closed-form numeric oracles. Two
independent sub-domains — aircraft noise certification and wind-turbine acoustic
noise — plus a small aircraft-noise measurement-system verifier.

Follows the established project conventions: one concept per module, a frozen
dataclass result with a `.plot()`, plotting in `_plotting.py` behind
`TYPE_CHECKING`, conformance via `@register(domain, standard, quantity)`,
four-variant figures (`.svg`/`_dark`/`_es`/`_es_dark`), docs EN + site EN/ES.

---

## PR-B1 — Aircraft noise (ICAO Annex 16 EPNL + IEC 61265)

### Module `src/phonometry/aircraft_noise.py` (ICAO Annex 16, Vol. I, App. 2)

Effective Perceived Noise Level, the aircraft noise-certification metric. Five
steps, implementing **Appendix 2** (the modern analytic formulation).

Public functions (primitives that build to the headline metric, mirroring the
underwater module's SPL/SEL/peak layering):

- `perceived_noisiness(spl, *, appendix=2) -> NDArray` — per-band noy `n(i)`
  from 24 one-third-octave SPLs (50 Hz–10 kHz), analytic piecewise form with the
  Table A2-3 constants `SPL(a..e)`, `M(b..e)`.
- `perceived_noise_level(spl) -> float` — `PNL = 40 + (10/lg2)·lg N`, with total
  noisiness `N = 0.85·n_max + 0.15·Σn`.
- `tone_correction(spl) -> float` — `C` via the slope/"encircling" method
  (Steps 1–10), 1.5 dB threshold, frequency split at 500 Hz / 5000 Hz, max 6⅔.
- `effective_perceived_noise_level(spectra, *, dt=0.5) -> EPNLResult` — the
  end-to-end metric from a spectral time history (rows = 0.5 s records, cols =
  24 bands): per-record `PNL(k)`, `C(k)`, `PNLT(k)`, the maximum `PNLTM`, the
  10-dB-down integration limits `kF..kL`, the duration correction `D`, and
  `EPNL = PNLTM + D = 10·lg(Σ 10^(PNLT/10)) − 13`.

`EPNLResult` (frozen dataclass): `frequencies`, `times`, `pnl`, `tone_correction`,
`pnlt`, `pnltm`, `duration_correction`, `epnl`, `band_limits (kF, kL)`. `.plot()`
draws PNL and PNLT vs time, marking `PNLTM` and the 10-dB-down band.

Constants: the full Table A2-3 (24×9) as a module-level array; `10/lg2`,
duration reference `T0 = 10 s`, `Δt = 0.5 s`, the −13 dB constant, the noy
breakpoints, the tone-correction factor tables.

### IEC 61265 verifier — `verify_aircraft_noise_system`

A `verify_...`-style conformance helper (added to the existing metrology
verification module, **not** a new module), checking supplied measured
performance against IEC 61265:1995 tolerances:

- **Table 1** — microphone directional-response tolerances (9 freq rows × 5
  angle columns, dB), including the §4.4.2 "intermediate angle → greater-angle
  limit" rule.
- Scalar tolerances: free-field sensitivity (§4.4.1 ±1.0/±2.0 dB), frequency
  response (§4.5.1 ±1.5 dB), linearity (§4.5.2 ±0.4/±0.5 dB), readout resolution
  (§4.7 0.1 dB), environmental (§4.8 ±0.2/±0.5 dB).
- The one-third-octave filter chain **delegates to the existing IEC 61260
  class-2 verifier** (§4.6) — no new filter mathematics.

Returns a structured pass/fail result per checked quantity.

### PR-B1 oracle strategy (clean-room)

- **Full EPNL end-to-end**: the ICAO Doc 9501 ETM Vol I (2018) worked examples —
  Table 3-6 (SPL spectrum → noy → PNL), Table 3-7 (turbofan tone correction →
  `C`), Table 4-4 (integrated-method reference-condition EPNL). Values
  transcribed verbatim as expected results. `plan/SGAR_2018_ETM_Vol_I.pdf`.
- **noy transcription guards**: the Table A2-3 breakpoints
  (`SPL(b)→n=1`, `SPL(d)→n=0.1`, `SPL(e)→n=0.3`) — exact per-band anchors.
- **PNL / duration correction**: closed-form, hand-computed anchors from a
  synthetic noy vector / PNLT series.
- **Tone correction**: the Annex 16 Table A1-3 spectrum (`C = 2.0 dB` at 2500 Hz,
  F = 6) — the slope/background machinery is identical across appendices, so it
  validates the Appendix-2 routine too.
- **IEC 61265**: Table 1 transcribed verbatim.

---

## PR-B2 — Wind-turbine noise (IEC 61400-11:2012+A1:2018)

### Module `src/phonometry/wind_turbine_noise.py`

Two closed-form concepts of the standard:

- `apparent_sound_power_level(lp, r1, *, board=True) -> float` (+ geometry
  helper `slant_distance(hub_height, rotor_diameter)` → `R1 = √(H² + (H+D/2)²)`):
  `L_WA = L_p − 6 + 10·lg(4π R1²/S0)`, `S0 = 1 m²`; band energy sum Eq (27).
- `tonal_audibility(spectrum, freqs, *, ...) -> TonalAudibilityResult` — the
  full tonality chain: critical bandwidth Eq (30) (Zwicker, with the 20–70 Hz →
  20–120 Hz rule), line classification (L₇₀%, masking/tone, Hanning 1.5 factor),
  masking-noise level Eq (31), tonality `ΔL_tn` Eq (32), the audibility criterion
  `L_a = −2 − lg(1 + (f/502)^2.5)` Eq (34), tonal audibility `ΔL_a` Eq (33), and
  the ≥ −3 dB reporting limit Eqs (35)/(36). Self-contained — does not depend on
  the ISO/TS 20065 masking index (the 2024 immission TS variant is out of scope).

Result dataclasses (frozen) with `.plot()`: apparent sound power spectrum;
tonality narrowband spectrum with the masking level and identified tone lines.

Optional companion: `tonal_adjustment(mean_audibility) -> float` — the ISO
1996-2 Table J.1 `K_T(ΔL)` step function (reproduced in IEC TS 61400-11-2:2024
Annex A), a transcribable-oracle step table.

### PR-B2 oracle strategy (clean-room)

No end-to-end numeric example exists in the standard, so:
- **Closed-form constants** (Eqs 30/31/34, S0, −6 dB, 1.5 Hanning factor,
  502 Hz / 2.5, −3 dB limit) as exact anchors.
- **Synthesized narrowband spectra** with hand-derived expected tonal audibility
  (a clean tone on a flat noise floor → known `ΔL_tn`, `L_a`, `ΔL_a`).
- **Apparent sound power** hand-computed from geometry.
- **`K_T(ΔL)`** step table transcribed verbatim (ISO 1996-2 Table J.1).

---

## Non-goals

- The full IEC 61400-11 measurement pipeline (10 s averaging, per-bin Type-A/B
  uncertainty budgets, met-mast data, power-curve normalization) — implement the
  closed forms; the data pipeline is out of scope (no sample dataset exists).
- The IEC TS 61400-11-2:2024 immission tonality via ISO/TS 20065 — Part 11's own
  closed-form audibility criterion (Eq 34) is used instead.
- ICAO Appendix 1 (older tabular noy) — Appendix 2 is the implementation target;
  Appendix 1 constants are only used where they coincide (tone-correction oracle).

## Validation gate (both PRs)

Per-PR: ruff + mypy (`src scripts`) + bandit + full pytest + conformance report
(`161 + N` checks, regenerated exactly as the Makefile) + site build; subagent
review after each step; CI green + bot-review pass before squash-merge.

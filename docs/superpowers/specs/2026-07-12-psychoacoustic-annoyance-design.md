# Psychoacoustic annoyance (PA) and fluctuation strength — design

Date: 2026-07-12
Branch: `feat/psychoacoustic-annoyance` (one PR)
Task: #17 (psychoacoustics), remaining part after ISO/PAS 20065.

## Goal

Close the modern sound-quality set in `phonometry` by adding **psychoacoustic
annoyance (PA)** and **fluctuation strength (F)**, integrating with the existing
loudness (ISO 532-1 Zwicker → `n5`), sharpness (DIN 45692) and roughness
(ECMA-418-2) implementations. Neither PA nor fluctuation strength has an ISO
standard; both come from Fastl & Zwicker, *Psychoacoustics: Facts and Models*.

## Sources and oracle strategy (clean-room)

- **Formulae:** Fastl & Zwicker (2006) — Chapter 10 (fluctuation strength,
  Eqs 10.2/10.3, calibration definition) and Chapter 16 (PA, Eqs 16.2–16.4).
  Primary origin of the PA model: **Widmann (1992)** PhD thesis, TU München
  (formula fully reproduced in Fastl & Zwicker Ch 16; thesis itself not
  required). PDF of the book is in `plan/`.
- **Signal→F model:** Osses, García, Kohlrausch (2016), *Modelling the sensation
  of fluctuation strength*, Proc. ICA 2016 (PDF in `plan/`).
- **Cross-check oracle:** SQAT (ggrecow/SQAT, CC-BY-NC) —
  `FluctuationStrength_Osses2016` and `PsychoacousticAnnoyance_Zwicker1999`
  (SQAT notes the PA model is properly attributed to Widmann 1992). Used **only
  as a numeric oracle** for cross-checking; no code is copied (same clean-room
  posture used for ECMA roughness).

Oracle status per quantity:

| Quantity | Oracle | Status |
|---|---|---|
| PA (Eqs 16.2–16.4) | Closed form; unit-stimulus self-consistency + SQAT example | **Exact** |
| F, AM broadband noise (Eq 10.2) | Closed form | **Exact** |
| F calibration point | Definition: 1 kHz / 60 dB / 100 % AM / 4 Hz = 1 vacil | **Exact (by definition)** |
| F from signal (Osses 2016, Eq 10.3) | No normative oracle → cross-check SQAT on canonical AM/FM sweeps + calibration | **Clean-room, cross-checked** (documented, like ECMA roughness ≈1.073) |

## Formulae

Psychoacoustic annoyance (Fastl & Zwicker Eqs 16.2–16.4):

```
PA = N5 · sqrt(1 + wS² + wFR²)
wS  = (S − 1.75) · 0.25 · lg(N5 + 10)          for S > 1.75 acum, else 0
wFR = (2.18 / N5^0.4) · (0.4·F + 0.6·R)
```
with N5 in sone, S in acum, F in vacil, R in asper.

Fluctuation strength, AM broadband noise (Eq 10.2):

```
F_BBN = 5.8·(1.25·m − 0.25)·[0.05·(L/dB) − 1] / [(fmod/5Hz)² + (4Hz/fmod) + 1.5]  vacil
```

Fluctuation strength, general signal model (Eq 10.3, Osses 2016):

```
F = 0.008 · Σ_z (ΔL(z)/dB·Bark) / [(fmod/4Hz) + (4Hz/fmod)]  vacil
```
where ΔL(z) is the temporal masking depth per critical band (implemented via the
specific-loudness temporal variation of the Osses 2016 model). Band-pass
characteristic peaks near 4 Hz effective modulation frequency.

## Architecture

Two new modules, following the one-method-per-module convention
(`loudness_zwicker.py`, `roughness_ecma.py`, `sharpness.py`).

### `src/phonometry/fluctuation_strength.py`

- `fluctuation_strength(signal, fs, *, field='free') -> FluctuationStrengthResult`
  — general signal model (Osses 2016 / Eq 10.3): auditory filtering into
  critical bands → temporal envelope per band → modulation analysis →
  specific fluctuation strength integrated over the Bark scale with the 4-Hz
  band-pass weighting. Result exposes `.fluctuation_strength` (vacil),
  `.specific` (per Bark), `.time` / time-varying trace if produced, `.plot()`.
- `fluctuation_strength_am_noise(level_db, modulation_factor, mod_frequency) ->
  float` — closed form Eq 10.2 (vacil). Exact.
- Module constants: calibration reference, band-pass constants.

### `src/phonometry/psychoacoustic_annoyance.py`

- `psychoacoustic_annoyance(n5, sharpness, fluctuation_strength, roughness) ->
  PsychoacousticAnnoyanceResult` — Eqs 16.2–16.4 from the four quantities.
  Exact. Result exposes `PA`, `w_s`, `w_fr` and the inputs; `.plot()` optional
  (bar of the term contributions).
- `psychoacoustic_annoyance_from_signal(signal, fs, *, field='free') ->
  PsychoacousticAnnoyanceResult` — convenience that computes N5
  (`loudness_zwicker`), S (`sharpness_din`), R (`roughness_ecma`) and F
  (`fluctuation_strength`) from the waveform and combines. **Documented model
  mixing** (Zwicker N5/S + ECMA/Sottek R + Osses F): a pragmatic composite,
  clearly caveated in the docstring and guide.

### Integration points (existing code, no refactor)

- `ZwickerLoudness.n5` already provides N5 (percentile loudness).
- `sharpness_din` → S in acum.
- `roughness_ecma` → R in asper.
- New `fluctuation_strength` → F in vacil.

## Error handling

- Reuse project validation idioms: positive/finite scalar guards, 1-D signal
  checks, `fs` positive, `field in {'free','diffuse'}`.
- `psychoacoustic_annoyance` validates N5 ≥ 0, S ≥ 0, F ≥ 0, R ≥ 0 finite; wS
  clamps to 0 for S ≤ 1.75 acum per the formula.
- No `assert` in `src/` (bandit); use `raise ValueError`.

## Testing

- `tests/test_fluctuation_strength.py`: closed-form Eq 10.2 exact values;
  calibration reference tone ≈ 1 vacil (documented tolerance); parametric
  band-pass shape (peak near 4 Hz; monotonic trends vs m and level);
  cross-check against SQAT reference points for the four canonical sweeps
  (AM tones/BBN vs fmod, FM tones vs fmod/deviation); validation-error tests;
  `.plot()` smoke.
- `tests/test_psychoacoustic_annoyance.py`: exact PA from unit stimuli and from
  a worked (N5,S,F,R) tuple; wS clamp at S = 1.75; wFR term; monotonicity;
  from-signal convenience smoke + consistency; validation-error tests; plot smoke.
- Reference constants in `tests/reference_data.py` (PA worked value, F Eq-10.2
  values, calibration, SQAT cross-check points).

## Conformance (scripts/conformance_report.py)

New domain **"Psychoacoustic annoyance & fluctuation strength (Fastl & Zwicker)"**:
- PA from a documented (N5,S,F,R) tuple → exact.
- F Eq 10.2 for an AM-BBN case → exact.
- F calibration tone → ≈ 1 vacil (documented tolerance; clean-room note).
- Byte-stable regeneration via `make conformance` (NO `2>&1`).

## Docs & figures

- New guide `docs/psychoacoustic-annoyance.md` + site EN/ES guides with §PA and
  §fluctuation strength, `<details>` double-snippet figure code, model-mixing
  caveat, oracle-status note. api-reference rows; README TOC; astro sidebar.
- Figures ×4 variants via `generate_graphs.py`: (a) F band-pass characteristic
  vs modulation frequency; (b) PA term contributions / PA of example stimuli.
  Committed; `check_figures.py` clean.

## Deliverables / gate

Full local gate before push: `ruff check .`, `mypy src scripts`, `bandit -r
src`, `pytest`, conformance N/N + no drift, site build (i18n + build +
html-validate), `check_figures.py`. Subagent review after implementation; fix
findings in a second pass. CI green; then squash-merge PR (authorized flow).

## Risks

- The Osses 2016 signal→F model is the largest, weakest-oracle piece. Mitigation:
  the exact closed form (Eq 10.2) and calibration are the verifiable backbone;
  the general model is cross-checked against SQAT on canonical sweeps and its
  clean-room status is documented (as with ECMA roughness).
- Model mixing in `psychoacoustic_annoyance_from_signal` — mitigated by keeping
  the exact `psychoacoustic_annoyance(n5,s,f,r)` as the primary API and
  documenting the composite convenience clearly.

## Out of scope (YAGNI)

- No new loudness/sharpness/roughness models (reuse existing).
- No FM/AM synthesis helpers beyond what tests need.
- Widmann (1992) thesis retrieval (formula already covered).

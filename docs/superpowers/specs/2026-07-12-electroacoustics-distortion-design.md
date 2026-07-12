# Electroacoustics: distortion and frequency response — design

Date: 2026-07-12
Branch: `feat/electroacoustics-distortion` (one PR)
Task: #18 (electroacoustics).

## Goal

Add the electroacoustic distortion metrics (IEC 60268-3:2013 + AES17-2015) and
frequency-response / coherence estimators (Bendat & Piersol) to `phonometry`.
All quantities have a strong analytic oracle: synthetic signals with known
distortion, and known LTI systems for the transfer-function estimators.

## Sources and oracle strategy (clean-room)

- **IEC 60268-3:2013** (`plan/`) clauses 14.12.x: total harmonic distortion,
  nth-order harmonic distortion, modulation distortion (SMPTE-type, n = 2/3),
  difference-frequency distortion (CCIF-type, n = 2/3), total difference-
  frequency distortion, dynamic intermodulation distortion (DIM), weighted THD.
- **AES17-2015** (`plan/`) clause 6.3: THD+N ratio (fundamental removed by a
  standard notch filter, Q 1.2–3; residual level − total level, dB) and SINAD.
- **Bendat & Piersol (2010), Random Data 4e** (`plan/`): the H1 = Gxy/Gxx and
  H2 = Gyy/Gyx frequency-response estimators and the ordinary coherence
  γ² = |Gxy|²/(Gxx·Gyy).
- **Oracle:** analytic throughout. THD from a signal with known harmonic
  amplitudes (`THD_F = √(Σaₙ²)/a₁`); THD+N from a fundamental plus known noise;
  SINAD = −THD+N (dB); SMPTE/CCIF from known intermodulation products; DIM from
  the IEC 60268-3 Table 2 component set; H1/H2 recovering a known IIR response
  with γ² = 1 noiseless and γ² = SNR/(1+SNR) with additive output noise. Prose
  background from the TrueNAS technical-book library if needed.

## Formulae

Harmonic distortion (IEC 60268-3 14.12.2–3, 14.12.5):
```
THD_F = √(Σ_{n≥2} aₙ²) / a₁                       (relative to fundamental)
THD_R = √(Σ_{n≥2} aₙ²) / √(Σ_{n≥1} aₙ²)           (relative to total RMS)
d_n   = aₙ / √(Σ_{k≥1} a_k²)                        (nth-order, relative to total)
```
THD+N (AES17 6.3.1): notch the fundamental, `THD+N = 20·lg(V_residual/V_total)`
dB; `SINAD = −THD+N` dB.

Intermodulation (IEC 60268-3):
- Modulation distortion / SMPTE (14.12.7): tones f₁ (low, large) + f₂ (high),
  4:1; n-th order = RMS of sidebands f₂ ± n·f₁ relative to f₂.
- Difference-frequency / CCIF (14.12.8): two equal high tones f₁, f₂; 2nd order
  at f₂ − f₁, 3rd order at 2f₁ − f₂ and 2f₂ − f₁.
- DIM (14.12.9): 15 kHz sine + 3.15 kHz low-pass-filtered square wave, 1:4;
  intermodulation components per Table 2.

Frequency response (Bendat & Piersol): H1, H2 as above; magnitude in dB and
phase; coherence γ² ∈ [0, 1].

## Architecture

Two new modules, one-concept-per-module (matching the project convention).

### `src/phonometry/distortion.py`

Signal-domain distortion metrics (FFT internally; Hann/flat-top window, exact
harmonic-bin picking). Functions return scalars (ratios and/or dB):
- `thd(signal, fs, fundamental=None, *, kind='F', n_harmonics=10) -> float`
- `harmonic_distortion(signal, fs, fundamental, order) -> float`
- `thd_plus_noise(signal, fs, fundamental=None, *, bandwidth=None, notch_q=…) -> float`
- `sinad(signal, fs, fundamental=None, *, bandwidth=None) -> float`
- `weighted_thd(signal, fs, fundamental=None, *, weighting='A') -> float`
- `modulation_distortion(signal, fs, f_low, f_high, *, orders=(2,3)) -> float` (SMPTE)
- `difference_frequency_distortion(signal, fs, f1, f2, *, order=2) -> float` (CCIF)
- `total_difference_frequency_distortion(signal, fs, f1, f2) -> float`
- `dynamic_intermodulation_distortion(signal, fs, *, f_sine=15000, f_square=3150) -> float` (DIM)
- `harmonic_analysis(signal, fs, fundamental=None, *, n_harmonics=10) -> HarmonicDistortionResult`
  bundling the fundamental, harmonic levels, THD/THD+N/SINAD and a `.plot()`
  (annotated magnitude spectrum with the harmonics marked).

### `src/phonometry/frequency_response.py`

Two-channel input/output analysis (Welch-averaged Hann segments via
`scipy.signal.csd`/`welch`, following `intensity.py`):
- `transfer_function(x, y, fs, *, estimator='H1', nperseg=…, overlap=0.5) ->
  FrequencyResponseResult` — `estimator ∈ {'H1','H2'}`.
- `coherence(x, y, fs, *, nperseg=…) -> tuple[frequencies, gamma_squared]`.
- `FrequencyResponseResult`: `frequencies`, complex `response`,
  `magnitude_db`, `phase`, `coherence`, `estimator`; `.plot()` = Bode
  (magnitude + phase) plus a coherence panel.

### Reuse (no refactor)

`scipy.signal.csd/welch/get_window`; the Welch conventions already used in
`intensity.py`; the A-weighting design in `parametric_filters.py` for
`weighted_thd`.

## Error handling

Project idioms: 1-D finite signals, `fs > 0`, positive fundamental/tone
frequencies, `kind ∈ {'F','R'}`, `estimator ∈ {'H1','H2'}`, equal-length x/y for
the two-channel functions, `nperseg` ≤ signal length. No `assert` in `src/`
(bandit). Fundamental auto-detection uses the largest spectral peak when
`fundamental` is None.

## Testing

- `tests/test_distortion.py`: exact THD_F/THD_R and nth-order from a synthesized
  harmonic signal; THD+N and SINAD from fundamental + known noise; SMPTE and
  CCIF from known intermodulation products; DIM component picking; weighted THD;
  fundamental auto-detection; validation errors; `.plot()` smoke.
- `tests/test_frequency_response.py`: H1/H2 recover a known IIR magnitude/phase
  on white-noise excitation; coherence ≈ 1 noiseless and drops as
  SNR/(1+SNR) with additive output noise; H1 vs H2 bias under input/output
  noise; validation errors; `.plot()` smoke.
- Reference constants in `tests/reference_data.py`.

## Conformance (scripts/conformance_report.py)

New domain **"Electroacoustics: distortion & frequency response"**:
- THD_F of a known synthetic signal (exact).
- THD+N / SINAD of a fundamental-plus-noise signal (AES17 notch, exact).
- SMPTE and CCIF IMD of a known two-tone signal (exact).
- H1 recovers a known first-order IIR gain at a reference frequency (exact).
- Coherence = 1 for a noiseless LTI path (exact).
Byte-stable regeneration via `make conformance` (NO `2>&1`).

## Docs & figures

- New guide `docs/electroacoustics.md` + site EN/ES guides: distortion metrics
  (THD/THD+N/SINAD/IMD/DIM/weighted THD) and frequency response (H1/H2 +
  coherence), with `<details>` figure-code snippets and a Standards footer.
  api-reference rows; README TOC; astro sidebar (a new "Electroacoustics" group
  or under an existing one).
- Figures ×4 variants: (a) annotated harmonic magnitude spectrum with the THD
  value; (b) Bode magnitude + coherence of a known system. Committed;
  `check_figures.py` clean.

## Deliverables / gate

Full local gate: `ruff check .`, `mypy src scripts`, `bandit -r src`, `pytest`,
conformance N/N + no drift, site build (i18n + build + html-validate),
`check_figures.py`. Subagent review after implementation (also confirms the
final public-symbol names); fix findings in a second pass. CI green; squash-merge.

## Risks

- **DIM** (14.12.9) is the most intricate (square-wave synthesis + Table 2
  component set); anchored on the standard's own component table.
- Windowing/leakage in the FFT-based metrics: use coherent-gain-corrected
  windows and integer-period synthesis in tests so the analytic oracle is exact.

## Out of scope (YAGNI)

- No loudspeaker/microphone full test suites (IEC 60268-4/5/7) beyond the shared
  distortion metrics.
- No Hv/Hs (total least squares) transfer-function estimator — H1/H2 + coherence
  cover the task; add later only if needed.
- Final public-symbol/module names may be tuned by the end-of-PR review.

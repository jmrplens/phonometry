# Underwater Acoustics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ISO 18405 / ISO 17208-1/-2 / ISO 18406 underwater-acoustics quantities to `phonometry`.

**Architecture:** Three one-concept modules — `underwater_acoustics.py` (reference levels re 1 µPa), `ship_radiated_noise.py` (RNL + monopole source level), `pile_driving_noise.py` (single-strike/cumulative SEL + peak) — each with a frozen result dataclass and `.plot()` where a figure adds value. Closed-form/analytic oracles throughout.

**Tech Stack:** Python 3.13+, NumPy, SciPy, matplotlib (optional plot extra); pytest; ruff; mypy; bandit.

## Global Constraints

- Use the project `.venv` for every tool (`.venv/bin/python|pytest|ruff|mypy|bandit`).
- No `assert` in `src/` (bandit); `ValueError` for invalid inputs; frozen dataclass + `.plot()` idiom; plotting in `_plotting.py` under TYPE_CHECKING.
- CI gate: `ruff check .`, `mypy src scripts`, `bandit -r src`, `pytest`, conformance byte-stable, site build (`pnpm run check:i18n && build && html-validate`), `check_figures.py`.
- Regenerate CONFORMANCE.md exactly as the Makefile: `... --file-header > docs/CONFORMANCE.md` WITHOUT `2>&1`.
- Figures: four variants (`.svg`, `_dark.svg`, `_es.svg`, `_es_dark.svg`) via set_lang/set_theme; deterministic.
- Spanish chat prose; no Claude attribution in commits/PRs.
- Reference values: p₀ = 1e-6 Pa, E₀ = 1e-12 Pa²s.

---

### Task 1: `underwater_acoustics.py` — reference levels (ISO 18405)

**Files:**
- Create: `src/phonometry/underwater_acoustics.py`
- Test: `tests/test_underwater_acoustics.py`
- Modify: `src/phonometry/__init__.py` (exports), `tests/reference_data.py`

**Interfaces produced:**
- `UNDERWATER_REFERENCE_PRESSURE: float = 1e-6`
- `UNDERWATER_REFERENCE_EXPOSURE: float = 1e-12`
- `sound_pressure_level(pressure, *, reference=UNDERWATER_REFERENCE_PRESSURE) -> float`
- `sound_exposure_level(pressure, fs, *, reference=UNDERWATER_REFERENCE_EXPOSURE) -> float`
- `peak_sound_pressure_level(pressure, *, reference=UNDERWATER_REFERENCE_PRESSURE) -> float`
- `background_noise_correction(signal_plus_noise_db, noise_db) -> float` (+ `UnderwaterAcousticsWarning`)
- `underwater_to_in_air_spl(level) -> float`, `in_air_to_underwater_spl(level) -> float` (±26.0206 dB)

Oracles: tone of amplitude A, RMS A/√2 → SPL = 20·lg((A/√2)/p₀). SEL of a tone over T s = SPL + 10·lg(T). Peak = 20·lg(A/p₀). Reference conversion = 20·lg(20e-6/1e-6) = 26.0206 dB.

- [ ] Write tests: SPL/SEL/peak of a known tone; background correction (S+N=10 dB, N=3 dB → 20·lg(10^1−10^0.3)); its warning when margin < 3 dB (returns uncorrected); ±26.02 dB round-trip; validation errors (non-1D, non-finite, fs≤0).
- [ ] Implement; export; add reference constants.
- [ ] `ruff`/`mypy`/`pytest` green; commit.

### Task 2: `ship_radiated_noise.py` — RNL + monopole source level (ISO 17208-1/-2)

**Files:**
- Create: `src/phonometry/ship_radiated_noise.py`
- Test: `tests/test_ship_radiated_noise.py`
- Modify: `src/phonometry/__init__.py`, `src/phonometry/_plotting.py` (`plot_ship_source_level`)

**Interfaces produced:**
- `radiated_noise_level(rms_pressure, distance) -> float`  # 20·lg(p/p₀)+20·lg(r/r₀)
- `hydrophone_depths(cpa_distance, angles=(15.0,30.0,45.0)) -> NDArray`  # depth = cpa·tan(angle)
- `source_level_uncertainty(frequency) -> float`  # 5 (≤100 Hz) / 3 (125 Hz–16 kHz) / 4 (>16 kHz) dB
- `monopole_source_level(rnl, frequency, draught, *, c=1500.0) -> ShipSourceLevelResult`
- `ShipSourceLevelResult(frequencies, rnl, delta_l, source_level, source_depth, sound_speed)` + `.plot()`

Oracle: ΔL = −10·lg[(2u⁴+14u²)/(14+2u²+u⁴)], u = k·d_s, k = 2πf/c, d_s = 0.7·D. Check ΔL at u where analytic (e.g. u→∞ ⇒ −10·lg(2) = −3.0103 dB; a mid u by direct formula). LRN(p=2 µPa, r=100 m) = 20·lg(2)+20·lg(100) = 6.0206+40 = 46.0206.

- [ ] Write tests: LRN closed form; ΔL vs Formula 3 at u∈{0.5,1,5} and the −3.01 dB high-u limit; d_s=0.7·D; hydrophone depths (cpa·tan); uncertainty table bins; array RNL → per-band Ls; `.plot()` smoke; validation errors.
- [ ] Implement + `plot_ship_source_level` (RNL, Ls, ΔL vs frequency, log-x).
- [ ] Green; commit.

### Task 3: `pile_driving_noise.py` — SEL / cumulative / peak (ISO 18406)

**Files:**
- Create: `src/phonometry/pile_driving_noise.py`
- Test: `tests/test_pile_driving_noise.py`
- Modify: `src/phonometry/__init__.py`, `src/phonometry/_plotting.py` (`plot_pile_strike`)

**Interfaces produced:**
- `single_strike_sel(pressure, fs) -> float`  # reuses underwater sound_exposure_level
- `cumulative_sel(single_sels) -> float`  # 10·lg(Σ 10^(SELₙ/10))
- `cumulative_sel_identical(sel_ss, n_strikes) -> float`  # sel_ss + 10·lg(N)
- `pile_strike_metrics(pressure, fs) -> PileStrikeResult(single_strike_sel, peak_spl, spl, pulse_duration, ...)` + `.plot()`

Oracle: identical strikes SEL_cum = SEL_ss + 10·lg(N). Differing: energy sum. Pulse duration = t(95%)−t(5%) of cumulative energy.

- [ ] Write tests: single-strike SEL of a synthetic pulse; cumulative identical = SEL_ss+10·lg(N); differing via energy sum; peak level; pulse duration on a boxcar-ish pulse; `.plot()` smoke; validation.
- [ ] Implement + `plot_pile_strike` (waveform + cumulative energy, 5%/95% markers).
- [ ] Green; commit.

### Task 4: Conformance domain

**Files:** Modify `scripts/conformance_report.py`, regenerate `docs/CONFORMANCE.md`.

Domain "Underwater acoustics (ISO 18405/17208/18406)": SPL exact, SEL exact, peak exact, RNL exact, ΔL vs Formula 3 exact, cumulative SEL = SEL_ss+10·lg(N) exact.

- [ ] Add `@register` checks reusing synthetic signals; regenerate WITHOUT `2>&1`; verify N/N and no drift; commit.

### Task 5: Figures ×4

**Files:** Modify `scripts/generate_graphs.py` (`generate_ship_source_level`, `generate_pile_driving`), add ES strings; create 8 SVGs in `.github/images/`.

- [ ] Add two generators (deterministic; seeded rng where needed); ES translations; run for en/es × light/dark; visually inspect; determinism diff; `check_figures.py` (new files only); commit.

### Task 6: Docs (EN guide + site EN/ES + api-reference + indices + sidebar)

**Files:** Create `docs/underwater-acoustics.md`, `site/src/content/docs/guides/underwater-acoustics.md`, `site/.../es/guides/underwater-acoustics.md`; modify `docs/api-reference.md`, `docs/README.md`, `README.md`, `site/astro.config.mjs`.

- [ ] Write guides (formulae, `<details>` figure snippets, Standards footer); add api-reference rows; indices; astro sidebar group "Underwater acoustics"; site build green (i18n+build+html-validate); commit.

### Task 7: Review, gate, PR

- [ ] Full local gate (ruff, mypy, bandit, pytest, conformance no-drift, site build, check_figures).
- [ ] Subagent review (confirms names + correctness); fix findings in a 2nd pass.
- [ ] Push; open PR on `feat/underwater-acoustics`; watch CI; review bot comments; squash-merge.

## Self-Review

- Spec coverage: Task 1↔ISO 18405 primitives + conversion + background correction; Task 2↔ISO 17208 RNL/geometry/uncertainty/source level; Task 3↔ISO 18406 SEL/cumulative/peak/duration; Tasks 4–6↔conformance/figures/docs; Task 7↔gate/review/merge. All spec sections covered.
- Placeholders: none — formulae and oracle numbers are concrete.
- Type consistency: `sound_exposure_level` reused by `single_strike_sel`; `ShipSourceLevelResult`/`PileStrikeResult` names consistent between tasks and `_plotting.py`.

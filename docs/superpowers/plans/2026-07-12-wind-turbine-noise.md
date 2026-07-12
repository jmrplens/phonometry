# Wind-Turbine Noise (IEC 61400-11) Implementation Plan — PR-B2

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** Implement the IEC 61400-11:2012+A1:2018 closed forms — the apparent
sound power level and the tonal-audibility chain — as `wind_turbine_noise.py`.

**Architecture:** One module with the apparent-sound-power geometry/level, the
tonality chain, and the ISO 1996-2 tonal-adjustment step table, each returning
floats or a frozen result with `.plot()`.

## Global Constraints

Same as PR-B1 (Python floor, `from __future__ import annotations`, typed numpy,
`float(...)` wraps; Spanish chat prose, no Claude attribution; clean-room
oracles from the standard / hand-derived; gate = ruff + mypy `src scripts` +
bandit + pytest + conformance regenerated exactly as the Makefile;
subagent review after implementation).

## Reference formulas (IEC 61400-11:2012+A1:2018)

- Geometry: `R0 = H + D/2` (Eq 1, horizontal axis); slant distance
  `R1 = sqrt(H² + R0²)`.
- Apparent sound power per band (Eq 26): `L_WA,i = L_p,i − 6 + 10·lg(4π R1²/S0)`,
  `S0 = 1 m²`. Total (Eq 27): `L_WA = 10·lg(Σ_i 10^{L_WA,i/10})`.
- Critical bandwidth (Eq 30): `CBW = 25 + 75·[1 + 1.4·(fc/1000)²]^0.69` Hz; for a
  candidate tone in 20-70 Hz the band is fixed to 20-120 Hz (CBW = 100 Hz).
- Tonality chain: `L_70%` = energy mean of the 70 % lowest-level lines in the
  critical band; masking lines are those below `L_70% + 6 dB`; `L_pn,avg` =
  energy mean of the masking lines; a line is a "tone" if above `L_pn,avg + 6`;
  tone level `L_pt` = energy sum of the tone lines (÷1.5 Hanning if ≥2 summed);
  masking level (Eq 31) `L_pn = L_pn,avg + 10·lg(CBW / ENBW)`, effective noise
  bandwidth `ENBW = 1.5·Δf`; tonality (Eq 32) `ΔL_tn = L_pt − L_pn`; audibility
  criterion (Eq 34) `L_a = −2 − lg(1 + (f/502)^2.5)`; tonal audibility (Eq 33)
  `ΔL_a = ΔL_tn − L_a`; a tone is reported when `ΔL_a ≥ −3 dB`.
- Tonal adjustment `K_T(ΔL)` (ISO 1996-2 Table J.1, via IEC TS 61400-11-2:2024
  Annex A): ≤0→0, (0,2]→1, (2,4]→2, (4,6]→3, (6,9]→4, (9,12]→5, >12→6.

## Hand-derived oracle (synthetic clean tone on a flat floor)

Δf = 2 Hz, tone at 500 Hz level 60 dB, all other lines 30 dB, band 440-560 Hz.
- `CBW(500) = 25 + 75·(1 + 1.4·0.25)^0.69 = 117.26 Hz` (independent closed form).
- All noise lines equal → `L_70% = 30`, masking lines all at 30 → `L_pn,avg = 30`.
- Tone (60 > 36) is a single tone line → `L_pt = 60` (no Hanning division).
- `ENBW = 1.5·2 = 3.0`; `L_pn = 30 + 10·lg(117.26/3.0) = 45.92 dB`.
- `ΔL_tn = 60 − 45.92 = 14.08 dB`.
- `L_a = −2 − lg(1 + (500/502)^2.5) = −2.299 dB`.
- `ΔL_a = 14.08 − (−2.299) = 16.38 dB`.

---

### Task 1: critical bandwidth + apparent sound power

**Files:** Create `src/phonometry/wind_turbine_noise.py`; Test
`tests/test_wind_turbine_noise.py`.

**Produces:** `critical_bandwidth(fc) -> float`, `slant_distance(hub_height,
rotor_diameter) -> float`, `apparent_sound_power_level(band_levels, r1) -> float`.

- [ ] Failing tests:
  - `critical_bandwidth(500.0) == pytest.approx(117.256, abs=0.02)`; the
    20-70 Hz band gives `critical_bandwidth(50.0) == 100.0`.
  - `slant_distance(80.0, 100.0) == pytest.approx(np.hypot(80.0, 130.0))`.
  - `apparent_sound_power_level([L], r1)` for a single band equals
    `L − 6 + 10·lg(4π r1²)`; multi-band uses the energy sum.
- [ ] Implement, run, commit `feat(wind-turbine): critical bandwidth + apparent sound power (IEC 61400-11)`.

### Task 2: tonal audibility chain

**Files:** Modify the module; Test same file.

**Produces:** `@dataclass(frozen=True) TonalAudibilityResult` (`tone_frequency`,
`critical_bandwidth`, `tone_level`, `masking_level`, `tonality`,
`audibility_criterion`, `tonal_audibility`, `is_audible`, plus `frequencies`,
`levels` for `.plot()`); `tonal_audibility(levels, frequencies, *,
tone_frequency=None) -> TonalAudibilityResult`.

- [ ] Failing test on the synthetic tone above:
```python
df = 2.0
freqs = np.arange(440.0, 560.0 + df, df)
levels = np.full(freqs.size, 30.0)
levels[np.argmin(np.abs(freqs - 500.0))] = 60.0
res = tonal_audibility(levels, freqs)
assert res.critical_bandwidth == pytest.approx(117.256, abs=0.02)
assert res.tone_level == pytest.approx(60.0, abs=1e-6)
assert res.masking_level == pytest.approx(45.92, abs=0.05)
assert res.tonality == pytest.approx(14.08, abs=0.05)
assert res.audibility_criterion == pytest.approx(-2.299, abs=0.01)
assert res.tonal_audibility == pytest.approx(16.38, abs=0.06)
assert res.is_audible is True
```
- [ ] Implement the chain (auto-detect the tone as the max line if
  `tone_frequency` is None; window the critical band about it; classify lines;
  Eqs 31-34). Run, commit `feat(wind-turbine): tonal audibility chain (IEC 61400-11 Eqs 30-34)`.

### Task 3: tonal adjustment + plotting + exports

**Files:** Modify the module, `_plotting.py`, `__init__.py`.

**Produces:** `tonal_adjustment(mean_audibility) -> float` (Table J.1 step);
`plot_tonal_audibility` (narrowband spectrum with the critical band, masking
level and the tone line marked); `TonalAudibilityResult.plot`.

- [ ] Failing tests: `tonal_adjustment(-1) == 0`, `tonal_adjustment(1) == 1`,
  `tonal_adjustment(5) == 3`, `tonal_adjustment(13) == 6`; boundary
  `tonal_adjustment(2) == 1` and `tonal_adjustment(2.0001) == 2`; a `.plot()`
  smoke test.
- [ ] Implement, export the public symbols in `__init__.py`, run, commit
  `feat(wind-turbine): tonal adjustment step + plotting + exports`.

### Task 4: conformance domain

**Files:** Modify `scripts/conformance_report.py`.

- [ ] Add `_WIND_TURBINE = "Wind-turbine noise (IEC 61400-11)"` with checks:
  critical bandwidth at 500 Hz (117.256), apparent sound power single band,
  tonal audibility of the synthetic tone (16.38), and `K_T(5) == 3`.
- [ ] Regenerate CONFORMANCE.md (exact Makefile command, no `2>&1`); expect
  169/169. Commit `feat(wind-turbine): conformance domain (IEC 61400-11)`.

### Task 5: figure ×4 variants

**Files:** Modify `scripts/generate_graphs.py`; add 4 SVGs.

- [ ] `generate_wind_turbine_tonality()` — a narrowband spectrum with the tone,
  the critical band shaded, the masking level line and the tonal audibility
  annotated; wire into `generate_all` with ES translations; produce
  `wind_turbine_tonality{,_dark,_es,_es_dark}.svg`.
- [ ] Run generator, verify determinism, commit `feat(wind-turbine): tonality figure (x4 variants)`.

### Task 6: docs EN + site EN/ES + indices

**Files:** Create `docs/wind-turbine-noise.md`, site EN/ES guides; modify
`docs/api-reference.md`, `docs/README.md`, `README.md`, `site/astro.config.mjs`.

- [ ] Write guides (apparent sound power + tonal audibility), add API rows,
  README/docs-README entries, sidebar entry (EN/ES). Build site (expect success).
  Commit `docs(wind-turbine): EN guide + site EN/ES, api-reference, indices`.

## Self-review checklist
- Oracles independent: closed-form CBW/geometry/K_T + hand-derived synthetic-tone
  audibility (not mirrored from the SUT).
- Signatures consistent (`TonalAudibilityResult` fields used by `.plot()`).
- Full gate green; CONFORMANCE regenerated without drift.

# Aircraft Noise (ICAO EPNL + IEC 61265) Implementation Plan — PR-B1

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Implement the ICAO Annex 16 Vol. I Appendix 2 Effective Perceived Noise
Level (EPNL) and an IEC 61265 aircraft-noise measurement-system verifier.

**Architecture:** One module `aircraft_noise.py` with the four EPNL primitives
building to `effective_perceived_noise_level`, returning a frozen `EPNLResult`
with `.plot()`. The IEC 61265 verifier goes into the existing `compliance.py`
(pattern of `verify_filter_class`/`verify_weighting_class`, returning a dict).

**Tech Stack:** numpy; matplotlib (optional, `.plot()`); pytest.

## Global Constraints

- Python: match repo floor; `from __future__ import annotations`; full type hints,
  numpy arrays typed `NDArray[np.float64]`; wrap numpy scalar returns in `float(...)`
  for mypy.
- Chat prose to the user in Spanish; code/docstrings/commits in English.
- No Claude attribution in commits or PR.
- Clean-room: implement from the standard; oracles are the ICAO worked examples
  transcribed below and closed-form anchors — never mirror the SUT.
- Gate before push: `.venv/bin/ruff check .`, `.venv/bin/mypy src scripts`,
  `.venv/bin/bandit -q -r src`, `.venv/bin/pytest`, and regenerate
  `docs/CONFORMANCE.md` EXACTLY as `.venv/bin/python scripts/conformance_report.py
  --file-header > docs/CONFORMANCE.md` (NO `2>&1`).
- Subagent review after each task; fix findings in a second pass.

## Reference data (ICAO Annex 16 App. 2 Table A2-3 — noy constants)

24 one-third-octave bands, f = 50…10000 Hz. Columns SPL(a),SPL(b),SPL(c),SPL(d),
SPL(e),M(b),M(c),M(d),M(e). SPL(a)=∞ (np.inf) and M(c)=NaN where "not applicable"
(bands 10–21). Verbatim (see spec + subagent report):

```
i  f     SPL(a) SPL(b) SPL(c) SPL(d) SPL(e)  M(b)      M(c)      M(d)      M(e)
1  50    91.0   64     52     49     55      0.043478  0.030103  0.079520  0.058098
2  63    85.9   60     51     44     51      0.040570  0.030103  0.068160  0.058098
3  80    87.3   56     49     39     46      0.036831  0.030103  0.068160  0.052288
4  100   79.0   53     47     34     42      0.036831  0.030103  0.059640  0.047534
5  125   79.8   51     46     30     39      0.035336  0.030103  0.053013  0.043573
6  160   76.0   48     45     27     36      0.033333  0.030103  0.053013  0.043573
7  200   74.0   46     43     24     33      0.033333  0.030103  0.053013  0.040221
8  250   74.9   44     42     21     30      0.032051  0.030103  0.053013  0.037349
9  315   94.6   42     41     18     27      0.030675  0.030103  0.053013  0.034859
10 400   inf    40     40     16     25      0.030103  nan       0.053013  0.034859
11 500   inf    40     40     16     25      0.030103  nan       0.053013  0.034859
12 630   inf    40     40     16     25      0.030103  nan       0.053013  0.034859
13 800   inf    40     40     16     25      0.030103  nan       0.053013  0.034859
14 1000  inf    40     40     16     25      0.030103  nan       0.053013  0.034859
15 1250  inf    38     38     15     23      0.030103  nan       0.059640  0.034859
16 1600  inf    34     34     12     21      0.029960  nan       0.053013  0.040221
17 2000  inf    32     32     9      18      0.029960  nan       0.053013  0.037349
18 2500  inf    30     30     5      15      0.029960  nan       0.047712  0.034859
19 3150  inf    29     29     4      14      0.029960  nan       0.047712  0.034859
20 4000  inf    29     29     5      14      0.029960  nan       0.053013  0.034859
21 5000  inf    30     30     6      15      0.029960  nan       0.053013  0.034859
22 6300  inf*   31     31     10     17      0.029960  0.029960  0.068160  0.037349
23 8000  44.3   37     34     17     23      0.042285  0.029960  0.079520  0.037349
24 10000 50.7   41     37     21     29      0.042285  0.029960  0.059640  0.043573
```
(band 22 SPL(a): report shows "∞*"; treat as inf — branch (a) inactive, M(c)=M(b)=0.029960.)

noy piecewise (analytic, App. 2 §4.7.3), antilog = 10^x:
```
SPL >= SPL(a):            n = 10^( M(c)·(SPL − SPL(c)) )
SPL(b) <= SPL < SPL(a):   n = 10^( M(b)·(SPL − SPL(b)) )
SPL(e) <= SPL < SPL(b):   n = 0.3·10^( M(e)·(SPL − SPL(e)) )
SPL(d) <= SPL < SPL(e):   n = 0.1·10^( M(d)·(SPL − SPL(d)) )
SPL < SPL(d):             n = 0
```

Total noisiness / PNL:  `N = 0.85·max(n) + 0.15·Σn`;  `PNL = 40 + (10/log10(2))·log10(N)` (N>0 else PNL=0).

Tone-correction factor table (App. 2 Table A2-2), F = SPL − SPL″, thresholds:
```
50 ≤ f < 500 and 5000 < f ≤ 10000:
   1.5 ≤ F < 3  -> C = F/3 − 0.5
   3   ≤ F < 20 -> C = F/6
   F ≥ 20       -> C = 3⅓
500 ≤ f ≤ 5000:
   1.5 ≤ F < 3  -> C = 2F/3 − 1
   3   ≤ F < 20 -> C = F/3
   F ≥ 20       -> C = 6⅔
F < 1.5 -> C = 0
```

---

### Task 1: perceived_noisiness (noy)

**Files:** Create `src/phonometry/aircraft_noise.py`; Test `tests/test_aircraft_noise.py`.

**Interfaces — Produces:**
- `NOY_BANDS: NDArray` (24 centre freqs), `_A2_3` constant table.
- `perceived_noisiness(spl: NDArray|list[float]) -> NDArray[np.float64]` (len 24).

- [ ] **Step 1 — failing tests (breakpoint anchors, independent of SUT):**
```python
import numpy as np, pytest
from phonometry.aircraft_noise import perceived_noisiness, NOY_BANDS

def test_noy_breakpoints():
    # At SPL(b) n=1; at SPL(e) n=0.3; at SPL(d) n=0.1 (per Table A2-3).
    # Band 14 (1000 Hz): SPL(b)=40, SPL(e)=25, SPL(d)=16.
    b14 = list(NOY_BANDS).index(1000.0)
    spl = np.full(24, -999.0); spl[b14] = 40.0
    assert perceived_noisiness(spl)[b14] == pytest.approx(1.0, rel=1e-6)
    spl[b14] = 25.0
    assert perceived_noisiness(spl)[b14] == pytest.approx(0.3, rel=1e-6)
    spl[b14] = 16.0
    assert perceived_noisiness(spl)[b14] == pytest.approx(0.1, rel=1e-6)

def test_noy_floor_below_spld_is_zero():
    b14 = list(NOY_BANDS).index(1000.0)
    spl = np.full(24, -999.0); spl[b14] = 10.0  # < SPL(d)=16
    assert perceived_noisiness(spl)[b14] == 0.0

def test_noy_requires_24_bands():
    with pytest.raises(ValueError):
        perceived_noisiness([1.0, 2.0, 3.0])
```
- [ ] **Step 2 — run, expect fail** (`pytest tests/test_aircraft_noise.py -k noy -v`).
- [ ] **Step 3 — implement** the module header, `NOY_BANDS`, `_A2_3` array (from the table above), `_validate_spectrum` (must be length-24, finite except allow the sentinel? — no: require finite; tests use −999 as "quiet", which is finite and < SPL(d) → 0, fine), and `perceived_noisiness` with the piecewise form (vectorized with np.select over the 5 conditions, guarding NaN M(c) by only using branch (a) where SPL≥SPL(a) which is never true when SPL(a)=inf).
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit** `feat(aircraft): ICAO noy perceived noisiness (Annex 16 App. 2)`.

### Task 2: perceived_noise_level (PNL)

**Files:** Modify `aircraft_noise.py`; Test same file.

**Interfaces — Produces:** `perceived_noise_level(spl) -> float`.

- [ ] **Step 1 — failing test (closed-form hand anchor):**
```python
from phonometry.aircraft_noise import perceived_noise_level
def test_pnl_closed_form():
    # Single band at 1000 Hz, SPL=40 -> n=1, all others 0 -> N=0.85*1+0.15*1=1.0
    # PNL = 40 + (10/log10 2)*log10(1) = 40.0
    b14 = list(NOY_BANDS).index(1000.0)
    spl = np.full(24, -999.0); spl[b14] = 40.0
    assert perceived_noise_level(spl) == pytest.approx(40.0, abs=1e-6)

def test_pnl_two_equal_bands():
    # two bands each n=1 -> nmax=1, sum=2 -> N=0.85+0.15*2=1.15
    # PNL = 40 + 33.2193*log10(1.15)
    b14 = list(NOY_BANDS).index(1000.0); b11 = list(NOY_BANDS).index(500.0)
    spl = np.full(24, -999.0); spl[b14] = 40.0; spl[b11] = 40.0  # SPL(b)@500=40 -> n=1
    expected = 40.0 + (10.0/np.log10(2.0))*np.log10(1.15)
    assert perceived_noise_level(spl) == pytest.approx(expected, rel=1e-9)
```
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** `perceived_noise_level` (N then PNL; if N<=0 return 0.0).
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit** `feat(aircraft): perceived noise level PNL`.

### Task 3: tone_correction — validated against ETM Table 3-7

**Files:** Modify `aircraft_noise.py`; Test same file.

**Interfaces — Produces:**
- `tone_correction(spl) -> float` (the max C over bands).
- `_tone_background(spl) -> tuple[NDArray, NDArray]` internal: returns (SPL'' , F) so the
  test can validate the intermediate background per band. (Prefix `_`, importable in test.)

Algorithm (App. 2 §4.3, start at band index 2 = 80 Hz):
1. s(i)=SPL(i)−SPL(i−1) for i≥3 (1-based); s(3) undefined.
2. encircle s(i) where |s(i)−s(i−1)|>5.
3. encircle SPL: if s(i) encircled & s(i)>0 & s(i)>s(i−1) → mark SPL(i); elif s(i)≤0 & s(i−1)>0 → mark SPL(i−1).
4. SPL′: unmarked→SPL; marked i in 3..23 → mean(SPL(i−1),SPL(i+1)); marked band24 → SPL(23)+s(23).
5. s′(i)=SPL′(i)−SPL′(i−1); s′(3)=s′(4); s′(25)=s′(24).
6. s̄(i)=mean(s′(i),s′(i+1),s′(i+2)) for i=3..23.
7. SPL″(3)=SPL(3); SPL″(i)=SPL″(i−1)+s̄(i−1) for i=4..24.
8. F(i)=SPL(i)−SPL″(i), keep F≥1.5.
9. C(i) per Table A2-2 above.
10. C = max_i C(i).

- [ ] **Step 1 — failing test (ETM Vol I Table 3-7 turbofan oracle):**
```python
from phonometry.aircraft_noise import tone_correction, _tone_background
# bands 1..24; bands 1-2 blank -> use a low floor (-999) so slopes start at band 3.
SPL_37 = [-999.0,-999.0, 70,62,70,80,82,83,76,80,80,79,78,80,78,76,79,85,79,78,71,60,54,45]

def test_tone_correction_etm_table_37():
    # ETM Vol I Table 3-7: max tone correction C(k) = 2.0 dB at 2500 Hz (band 18).
    assert tone_correction(SPL_37) == pytest.approx(2.0, abs=1e-6)

def test_tone_correction_background_column():
    # SPL'' (Step 7) at bands 5,6,18,24 from Table 3-7 col 9 (71, 77+2/3, 79, 45).
    spl_dd, F = _tone_background(SPL_37)
    assert spl_dd[4]  == pytest.approx(71.0, abs=0.05)      # 125 Hz
    assert spl_dd[5]  == pytest.approx(77.0+2/3, abs=0.05)  # 160 Hz
    assert spl_dd[17] == pytest.approx(79.0, abs=0.05)      # 2500 Hz
    assert F[17]      == pytest.approx(6.0, abs=0.05)       # F=85-79=6

def test_tone_correction_none_when_flat():
    assert tone_correction(np.linspace(60, 60, 24)) == 0.0
```
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** `_tone_background` and `tone_correction`. Use 0-based numpy;
      keep the band-3 start. Careful with the encircle mean using neighbours.
- [ ] **Step 4 — run, expect pass.** If the SPL'' column disagrees, fix the algorithm
      (do NOT relax the oracle) — this is the transcription guard.
- [ ] **Step 5 — commit** `feat(aircraft): tone correction (encircling method) + ETM oracle`.

### Task 4: effective_perceived_noise_level + EPNLResult — validated against ETM Table 4-4

**Files:** Modify `aircraft_noise.py`; Test same file.

**Interfaces — Produces:**
- `@dataclass(frozen=True) class EPNLResult` with: `frequencies`, `times`,
  `pnl` (NDArray), `tone_correction` (NDArray), `pnlt` (NDArray), `pnltm` (float),
  `duration_correction` (float), `epnl` (float), `band_limits` (tuple[int,int]),
  `.plot(ax=None, **kw)`.
- `effective_perceived_noise_level(spectra, *, dt=0.5, reference_time=10.0) -> EPNLResult`.
  `spectra`: shape (K, 24). `dt`: scalar or length-K per-record durations.
- Helper `epnl_from_pnlt(pnlt, dt, *, reference_time=10.0) -> tuple[float,float,int,int]`
  returning (epnl, pnltm, kF, kL) — the duration/limit machinery, so it can be tested
  directly against Table 4-4 without a full spectral history.

Duration machinery (App. 2 §4.5/§4.6):
- `PNLTM = max(pnlt)`.
- 10-dB-down limits: kF = index on the rising side whose PNLT is **nearest** to
  `PNLTM − 10`; kL = nearest on the falling side. (ETM Table 4-4 confirms "nearest
  sample", not "first crossing": record 28 = 86.96 < 87.40 is chosen as kL because
  |86.96−87.40| < |88.75−87.40|.)
- `EPNL = 10·log10( Σ_{k=kF..kL} 10^(PNLT(k)/10)·dt(k) ) − 10·log10(reference_time)`.
- `D = EPNL − PNLTM`.

- [ ] **Step 1 — failing test (ETM Vol I Table 4-4 integrated-method oracle):**
```python
from phonometry.aircraft_noise import epnl_from_pnlt
PNLTR = [84.62,85.84,85.37,88.57,88.82,88.03,88.76,87.06,86.92,90.39,89.89,91.00,
         90.08,89.71,89.61,90.21,91.14,92.10,93.68,94.89,95.87,97.06,97.40,96.23,
         94.73,92.30,88.75,86.96,85.41,83.88,83.01]
DTR = [0.3950,0.3950,0.3951,0.3951,0.3952,0.3953,0.3954,0.3956,0.3957,0.3960,0.3963,
       0.3967,0.3973,0.3981,0.3992,0.4009,0.4033,0.4066,0.4108,0.4153,0.4196,0.4231,
       0.4256,0.4273,0.4285,0.4294,0.4299,0.4304,0.4307,0.4309,0.4311]

def test_epnl_table_44():
    epnl, pnltm, kF, kL = epnl_from_pnlt(np.array(PNLTR), np.array(DTR))
    assert pnltm == pytest.approx(97.40, abs=1e-6)
    assert (kF, kL) == (3, 27)                 # 0-based -> records 4 and 28
    assert epnl == pytest.approx(92.61892, abs=5e-3)   # ETM: 92.61892 EPNdB

def test_epnl_uniform_dt_reduces_to_minus_13():
    # With dt=0.5, ref=10: EPNL = 10log10(sum 10^(PNLT/10)) - 13.0103
    p = np.array([90.0, 95.0, 90.0])
    epnl, pnltm, _, _ = epnl_from_pnlt(p, 0.5)
    # all within 10 dB of 95 -> full sum
    expected = 10*np.log10(np.sum(10**(p/10)))*1 + 10*np.log10(0.5) - 10*np.log10(10.0)
    assert epnl == pytest.approx(10*np.log10(np.sum(0.5*10**(p/10)))-10*np.log10(10.0), rel=1e-9)
```
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** `epnl_from_pnlt`, then `effective_perceived_noise_level`
      (loops records: pnl(k), C(k), pnlt(k)=pnl+C; then epnl_from_pnlt) and `EPNLResult`.
      `dt` scalar broadcasts to length-K.
- [ ] **Step 4 — run, expect pass.** Tune only the implementation, never the 92.61892 oracle.
- [ ] **Step 5 — commit** `feat(aircraft): EPNL end-to-end + EPNLResult (ETM Table 4-4 oracle)`.

### Task 5: plotting + package exports

**Files:** Modify `src/phonometry/_plotting.py`, `src/phonometry/__init__.py`; Test same file.

- [ ] **Step 1 — failing smoke test:**
```python
def test_epnl_result_plot_smoke():
    import matplotlib; matplotlib.use("Agg")
    from phonometry import effective_perceived_noise_level
    rng = np.random.default_rng(0)
    spectra = 60 + 20*np.exp(-((np.arange(20)[:,None]-10)**2)/8) + rng.standard_normal((20,24))
    res = effective_perceived_noise_level(spectra)
    assert res.plot() is not None
```
- [ ] **Step 2 — run, expect fail** (import error).
- [ ] **Step 3 — implement** `plot_epnl(result, ax=None, **kw)` in `_plotting.py` (PNL and
      PNLT vs time, mark PNLTM and shade kF..kL), `EPNLResult.plot` delegating to it, and
      export `perceived_noisiness, perceived_noise_level, tone_correction,
      effective_perceived_noise_level, EPNLResult` from `__init__.py`.
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit** `feat(aircraft): EPNL plotting + exports`.

### Task 6: IEC 61265 verify_aircraft_noise_system

**Files:** Modify `src/phonometry/compliance.py`; Test `tests/test_compliance.py` (or new
`tests/test_aircraft_noise_system.py`).

**Interfaces — Produces:**
- `IEC61265_DIRECTIONAL: dict` — Table 1 tolerances (freq → {angle → dB}).
- `verify_aircraft_noise_system(*, directional=None, freq_response=None,
  linearity=None, ...) -> Dict[str, Any]` — each supplied measurement checked vs
  tolerance; returns `{"passed": bool, "checks": [{"quantity","limit","value","ok"}...]}`.

Table 1 (max |sensitivity(0°) − sensitivity(angle)| in dB), rows = band kHz:
```
freq(kHz): 30°  60°  90°  120° 150°
0.05–1.6 : 0.5  0.5  1.0  1.0  1.0
2.0      : 0.5  0.5  1.0  1.0  1.0
2.5      : 0.5  0.5  1.0  1.5  1.5
3.15     : 0.5  1.0  1.5  2.0  2.0
4.0      : 0.5  1.0  2.0  2.5  2.5
5.0      : 0.5  1.5  2.5  3.0  3.0
6.3      : 1.0  2.0  3.0  4.0  4.0
8.0      : 1.5  2.5  4.0  5.5  5.5
10.0     : 2.0  3.5  5.5  6.5  7.5
```
Rule §4.4.2: for an intermediate angle use the greater angle's limit.

- [ ] **Step 1 — failing tests (Table 1 verbatim oracle):**
```python
from phonometry.compliance import verify_aircraft_noise_system
def test_61265_directional_pass():
    # measured diffs at 4 kHz within limits (0.4,0.9,1.9,2.4,2.4 <= 0.5,1.0,2.0,2.5,2.5)
    meas = {4000.0: {30:0.4, 60:0.9, 90:1.9, 120:2.4, 150:2.4}}
    r = verify_aircraft_noise_system(directional=meas)
    assert r["passed"] is True
def test_61265_directional_fail():
    meas = {4000.0: {90: 2.5}}  # limit 2.0 at 4 kHz/90 deg
    r = verify_aircraft_noise_system(directional=meas)
    assert r["passed"] is False
```
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** the table + verifier (directional first; then optional scalar
      checks freq_response ±1.5, linearity ±0.4/±0.5, resolution 0.1, environmental ±0.2/±0.5).
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit** `feat(aircraft): IEC 61265 measurement-system verifier`.

### Task 7: conformance domain

**Files:** Modify `scripts/conformance_report.py`.

- [ ] **Step 1 — add** `_AIRCRAFT = "Aircraft noise (ICAO Annex 16 / IEC 61265)"` and
      `@register` checks returning `numeric(...)`: (a) noy at 1000 Hz SPL(b)=40 → 1.0;
      (b) tone correction Table 3-7 → 2.0; (c) EPNL Table 4-4 → 92.61892; (d) IEC 61265
      directional limit at 4 kHz/90° → 2.0. Use the same oracle values as the tests.
- [ ] **Step 2 — regenerate** CONFORMANCE.md (exact Makefile command, no `2>&1`); expect
      `(161 + N)/(161 + N) checks passed` printed to stderr, file has no drift beyond the
      new section.
- [ ] **Step 3 — commit** `feat(aircraft): conformance domain (ICAO EPNL / IEC 61265)`.

### Task 8: figures ×4 variants

**Files:** Modify `scripts/generate_graphs.py`; add 4 SVGs under `.github/images/`.

- [ ] **Step 1 — add** `generate_epnl()` producing an EPNL PNL/PNLT-vs-time figure via
      `EPNLResult.plot()` from a synthetic realistic flyover spectral history; wire it into
      `generate_all` with the ES `_ES_EXACT` translations; produce `epnl.svg`,
      `epnl_dark.svg`, `epnl_es.svg`, `epnl_es_dark.svg`.
- [ ] **Step 2 — run** the generator; verify 4 files exist and `scripts/check_figures.py`
      (if part of gate) passes by tolerance.
- [ ] **Step 3 — commit** `feat(aircraft): EPNL figure (x4 variants)`.

### Task 9: docs EN + site EN/ES + indices

**Files:** Create `docs/aircraft-noise.md`, `site/src/content/docs/guides/aircraft-noise.md`,
`site/src/content/docs/es/guides/aircraft-noise.md`; Modify `docs/api-reference.md`,
`docs/README.md`, `README.md`, `site/astro.config.mjs`.

- [ ] **Step 1 — write** the EN guide (EPNL five steps, IEC 61265 verifier), the site EN/ES
      guides with frontmatter + `<details>` double-snippet, add API-reference rows, README
      table row, docs/README entry, sidebar entry (EN/ES).
- [ ] **Step 2 — build** the site (`npm --prefix site run build` or the repo's command); expect success.
- [ ] **Step 3 — commit** `docs(aircraft): EN guide + site EN/ES, api-reference, indices`.

## Self-review checklist (run after implementation)
- Every EPNL step has an oracle: noy breakpoints (T1), PNL closed form (T2), tone
  correction ETM Table 3-7 (T3), EPNL ETM Table 4-4 (T4), IEC 61265 Table 1 (T6).
- No oracle value mirrors the implementation; all are transcribed or hand-derived.
- Signatures consistent across tasks (`EPNLResult` fields used by `.plot()` in T5).
- Full gate green; CONFORMANCE regenerated without drift.

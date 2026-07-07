# Numerical Conformance Report — Design

Reframes the CI PR comment into a persistent, self-contained **numerical
conformance report**: every PR now shows the library's normative conformance
at a glance (each implemented standard → expected value/range → computed
result → pass/fail with deviation), not just "CI passed".

## Deliverables

| File | Role |
|---|---|
| `scripts/conformance_report.py` | The conformance harness: a registry of checks + Markdown renderer. Retires and absorbs `scripts/benchmark_filters.py`. |
| `tests/reference_data.py` | Single source of truth for the shared normative tables (IEC 61672-1 Table 3, ISO 7196 Table 2, ISO 717-1 Annex C R). Dependency-free (stdlib only) so it imports in CI without `pytest`. Imported by both the tests and the harness. |
| `tests/test_conformance_report.py` | Fast smoke test: registry runs, every check passes on `main`, Markdown is well-formed. |
| `.github/scripts/comment_pr.py` | Rewritten: conformance report is the lead; test/coverage table collapsed below. |
| `.github/workflows/python-app.yml` | `pr-comment` job runs the harness (was: `benchmark_filters.py`). |

Retired: `scripts/benchmark_filters.py`, `filter_benchmark_report.md`, and the
four orphaned `.github/images/benchmark/*.png`. Its numerical content
(per-architecture class-1 margins, weighting deviations) is folded into the
report's "Numerical validation" section; the non-conformance parts
(performance/scaling/crossover plots) are dropped to keep one source.

## Registry design

Each check is a zero-argument callable returning an `Outcome(expected,
computed, delta, passed)`, registered with a decorator that pins its domain,
standard designation + clause citation, and quantity:

```python
@register("Room & building acoustics", "ISO 717-1 Annex C, Table C.1",
          "Weighted sound reduction index Rw (C;Ctr)")
def _chk_iso717_rw() -> Outcome:
    exp = ref.ISO717_1_ANNEX_C_EXPECTED
    res = ph.weighted_rating(ref.ISO717_1_ANNEX_C_R)     # library call
    ok = res.rating == exp["rw"] and res.c == exp["c"] and res.ctr == exp["ctr"]
    return Outcome(f"Rw {exp['rw']} (C {exp['c']}; Ctr {exp['ctr']})",
                   f"Rw {res.rating} (C {res.c}; Ctr {res.ctr})",
                   f"sum {res.unfavourable_sum:.1f} dB", ok)
```

The `numeric(expected, computed, tol, unit=..., rel=...)` helper builds the
`Outcome` for scalar checks (formats expected±tol, delta, pass/fail).

**Where expected values come from (no drift):**
- **Shared tables** — `tests/reference_data` (weighting/insulation) and the
  ISO 532-1 fixtures (`tests/data/*.json`, `*.txt`) are imported, not
  re-hardcoded. The refactored test files (`test_iec_weighting_table3.py`,
  `test_g_weighting.py`, `test_insulation.py`) now import the same constants,
  so tests and report can't disagree.
- **Same library function** — the filter-class checks call the exact
  `verify_filter_class` the tests use.
- **Closed forms** — the rest synthesize an input with an analytically known
  output (plane wave `I = p²/ρc`, monopole `Lp = LW − 10·lg(2πr²)`,
  exponential IR → `T30`, ISO 3741 Eq. 20 inversion, `Leq` of a sine, …), so
  the reference is self-verifying and citation-anchored.

Rendering: a headline (`N/N checks pass across D domains and S standards`), a
"Numerical validation — filters & weightings" section (two tables:
per-architecture IEC 61260-1 class margins; A/C/G worst-case deviation +
headroom), then one conformance table per domain. Status uses HTML entities
(`&#9989;`/`&#10060;`) that render as ✅/❌ on GitHub while keeping the source
emoji-free.

**Adding a check** (the documented pattern): write a zero-arg function
returning `Outcome`, decorate with `@register(domain, standard+clause,
quantity)`. Pull the expected value from `tests/reference_data` (add the table
there if new) or synthesize a closed form. The smoke test picks it up
automatically via `pytest.mark.parametrize("check", cr.CHECKS)`.

## Coverage — wired vs pending

**Wired (21 checks · 17 standards · 6 domains):**

| Domain | Standards wired |
|---|---|
| Filters & weightings | IEC 61260-1:2014 (octave + 1/3-oct butterworth class); IEC 61672-1:2013 (A, C weighting deviation); ISO 7196:1995 (G weighting) |
| Levels & dosimetry | IEC 61672-1 (Leq); IEC 61252:1995 (LEX,8h); ISO 1996-1:2016 (Lden) |
| Psychoacoustics | ISO 532-1:2017 (Zwicker N); DIN 45692:2009 (sharpness); ISO 226:2023 (equal-loudness contour) |
| Speech intelligibility | IEC 60268-16:2020 (STI weighting pair; uniform-MTF mapping) |
| Intensity & sound power | IEC 61043:1994 (plane-wave I); ISO 3744:2010 (monopole LW); ISO 9614-2:1996 (intensity-scan LW); ISO 3741:2010 (reverberation inversion) |
| Room & building acoustics | ISO 3382-2:2008 (T30); ISO 717-1 (Rw/C/Ctr); ISO 354:2003 (absorption area); ISO 3382-3:2012 (open-plan D2,S) |

**Pending (test-backed reference values already exist — one `@register`
each to wire):**
- Filters/weightings: IEC 61672-1 Table 4 time-weighting (FAST/SLOW toneburst,
  SEL); IEC 61672-1 §5.13 Table 5 LCpeak; IEC 61260-1 E3 nominal-frequency
  rounding.
- Levels/calibration: IEC 60942:2017 Table 2 fluctuation limits;
  ISO 1996-1 Ldn + composite rating level.
- Psychoacoustics: ISO 532-1 Annex B.4/B.5 time-varying Nmax/N5;
  ECMA-418-1:2024 TNR/PR critical-band worked examples.
- Speech: IEC 60268-16 auditory-masking table; STIPA loopback.
- Intensity/power: ISO 9614-1 field indicators F2/F3/F4 + dynamic capability
  index; ISO 3744 K1/K2 corrections, box surface, A-weighted LWA;
  ISO 3741 comparison method + Waterhouse; ISO 18233:2006 MLS/sweep IR.
- Room/building: ISO 3382-1 C50/C80/D50/Ts/EDT/T20 closed forms;
  ISO 16283-1/2 DnT,w / L′nT,w pipelines; ISO 717-2 impact Ln,w/CI (Annex C).

Note: the ECMA-418-2 tonality metric (`c_T`) referenced in the brief is **not**
present in this repo — `tonality.py` implements ECMA-418-**1** (TNR/PR), which
is wired-pending above.

## Verification

- Harness runs in **~2.7 s** locally, deterministic, no network.
- `make check` (ruff `.` + bandit `-r src` + full `pytest`): **green** —
  740 passed, 12 skipped; ruff, mypy `--strict`, bandit all clean on the new
  Python.
- Smoke test: 23 cases (one per registered check + registry/render assertions).

## Full rendered output (local run)

````markdown
## Numerical conformance report

&#9989; **21/21 conformance checks pass** across 6 domains and 17 standards - filters class 1 - weightings within IEC 61672-1 class 1.

### Numerical validation - filters &amp; weightings

IEC 61260-1:2014 class verification per filter architecture (order 6, one-third-octave, 100 Hz-10 kHz, fs = 48 kHz). A positive margin means the class-1 acceptance limits are met with that much room.

| Architecture | Overall class | Min class-1 margin | Min class-2 margin |
|:---|:---:|:---:|:---:|
| butter | class 1 | +0.400 dB | +0.600 dB |
| cheby1 | none | -1.246 dB | -0.837 dB |
| cheby2 | class 1 | +0.400 dB | +0.600 dB |
| ellip | none | -1.218 dB | -0.813 dB |
| bessel | none | -4.133 dB | -3.133 dB |

Frequency-weighting worst-case deviation of the designed digital filter from the normative curve, with the remaining class-1 / tolerance headroom (A/C: IEC 61672-1 Table 3; G: ISO 7196 A.3).

| Curve | fs | Worst deviation | Min headroom |
|:---|:---:|:---:|:---:|
| A | 48 kHz | -0.902 dB @ 20000 Hz | +0.700 dB |
| A | 96 kHz | -0.515 dB @ 20000 Hz | +0.700 dB |
| C | 48 kHz | -0.935 dB @ 20000 Hz | +0.700 dB |
| G | 48 kHz | +0.047 dB @ 1 Hz | +0.953 dB |

### Filters & weightings

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61260-1:2014 Table 1 | Octave-band filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61260-1:2014 Table 1 | One-third-octave filter class (butterworth, fs=48 kHz) | class 1 | class 1 (margin +0.400 dB) | +0.400 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | A-weighting deviation vs class-1 limits (fs=48 kHz) | within class-1 limits | worst -0.902 dB @ 20000 Hz | headroom +0.700 dB | &#9989; |
| IEC 61672-1:2013 Table 3 | C-weighting deviation vs class-1 limits (fs=48 kHz) | within class-1 limits | worst -0.935 dB @ 20000 Hz | headroom +0.700 dB | &#9989; |
| ISO 7196:1995 Table 2 / A.3 | G-weighting deviation vs +/-1 dB tolerance (fs=48 kHz) | within class-1 limits | worst +0.047 dB @ 1 Hz | headroom +0.953 dB | &#9989; |

### Levels & dosimetry

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61672-1:2013 (Leq) | Leq of a 1 Pa 1 kHz sine | 90.97 dB (+/-0.05 dB) | 90.969 dB | -0.0009 dB | &#9989; |
| IEC 61252:1995 (LEX,8h) | 8 h exposure to 90 dB(A) noise | 90 dB (+/-0.05 dB) | 90.008 dB | 0.00809 dB | &#9989; |
| ISO 1996-1:2016 3.6.4 | Lden, constant 60 dB in day/evening/night | 66.3952 dB (+/-0 dB) | 66.3952 dB | 0 dB | &#9989; |

### Psychoacoustics

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 532-1:2017 Annex B.2 | Zwicker loudness N, stationary test signal 1 | 83.2957 sone (+/-0.1%) | 83.2957 sone | -0.00004 sone | &#9989; |
| DIN 45692:2009 Clause 6 | Sharpness of the standard 1 kHz reference signal | 1 acum (+/-0 acum) | 1 acum | 0 acum | &#9989; |
| ISO 226:2023 Table B.1 | Equal-loudness contour, 60 phon @ 2 kHz | 60 dB SPL (+/-0.05 dB SPL) | 59.998 dB SPL | -0.0025 dB SPL | &#9989; |

### Speech intelligibility

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 60268-16:2020 A.2.2 | STI weighting-factor pair (500 Hz + 1 kHz bands) | 0.398 (+/-0.001) | 0.398 | 0 | &#9989; |
| IEC 60268-16:2020 A.3.1.2 | Uniform MTF m=0.5 maps to STI=0.5 | 0.5 (+/-0.01) | 0.5 | 0 | &#9989; |

### Intensity & sound power

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| IEC 61043:1994 Clause 5 | Plane-wave intensity I = p^2 / (rho c) | 0.00238 W/m^2 (+/-1.5%) | 0.00239 W/m^2 | 0.00001 W/m^2 | &#9989; |
| ISO 3744:2010 Eq. 18 | Monopole hemisphere recovers LW (r=4 m) | 95 dB (+/-0 dB) | 95 dB | 0 dB | &#9989; |
| ISO 9614-2:1996 Eq. 12 | Intensity scan recovers LW of an enclosed source | 90 dB (+/-0.000001 dB) | 90 dB | 0 dB | &#9989; |
| ISO 3741:2010 Eq. 20 | Reverberation-room method inverts to a known LW | 0 dB error | 0 dB | 0 dB | &#9989; |

### Room & building acoustics

| Standard | Quantity | Expected (norm) | Computed | &#916; | Status |
|:---|:---|:---|:---|:---|:---:|
| ISO 3382-2:2008 5.3.3 | T30 from a synthetic exponential decay (T=1.0 s) | 1 s (+/-1%) | 1 s | 0 s | &#9989; |
| ISO 717-1 Annex C, Table C.1 | Weighted sound reduction index Rw (C;Ctr) | Rw 30 (C -2; Ctr -3) | Rw 30 (C -2; Ctr -3) | sum 31.8 dB | &#9989; |
| ISO 354:2003 Eq. 5/8 | Sabine inversion recovers absorption area | 9.212828 m^2 (+/-0 m^2) | 9.212828 m^2 | 0 m^2 | &#9989; |
| ISO 3382-3:2012 Clause 6.2 | Open-plan spatial decay rate D2,S (-6 dB/doubling) | 6 dB (+/-0 dB) | 6 dB | 0 dB | &#9989; |
````

# Underwater acoustics — design (PR-A of task #19)

Date: 2026-07-12
Branch: `feat/underwater-acoustics` (one PR)
Task: #19, part A (submarine acoustics). Part B (aeroacoustics: ICAO EPNL,
IEC 61265, IEC 61400-11) is a separate later PR.

## Goal

Add the underwater-acoustics quantities of ISO 18405, ISO 17208-1/-2 and
ISO 18406 to `phonometry`: the reference levels (referred to 1 µPa), ship
radiated-noise level and equivalent monopole source level, and the pile-driving
single-strike / cumulative sound exposure and peak levels. All quantities have
an exact analytic oracle (closed forms and synthetic signals of known energy).

## Sources (all in `plan/`, clean-room)

- **ISO 18405:2017** — terminology. Reference values (p₀ = 1 µPa, E₀ =
  1 µPa²s) and the definitions of sound pressure level, sound exposure level and
  peak sound pressure level realised as the shared level primitives.
- **ISO 17208-1:2016** — deep-water radiated noise from ships: the measurement
  geometry (three hydrophones at 15°/30°/45° depression angles at the closest
  point of approach dCPA = max(100 m, ship length)), background-noise
  correction, and the radiated noise level (RNL).
- **ISO 17208-2:2019** — conversion of RNL to equivalent monopole source level
  via the Lloyd's-mirror surface correction (Formula 3), the 0.7·draught source
  depth (Formula 1), and the tabulated source-level uncertainty (5/3/4 dB by
  frequency range).
- **ISO 18406:2017** — percussive pile driving: single-strike sound exposure
  level (Formulae 3–4), SPL/Leq (Formula 7), peak sound pressure level, pulse
  duration (90 % energy) and cumulative sound exposure level over N strikes
  (Formulae 8–9).

## Formulae (all exact)

Reference levels (dB re 1 µPa; ISO 18405 / ISO 18406):
```
SPL   = 10·lg( <p²> / p₀² )                       (Formula 7)
SEL   = 10·lg( ∫ p² dt / E₀ ),  E₀ = 1 µPa²s      (Formulae 3–4)
Lp,pk = 20·lg( max|p| / p₀ )                       (peak, zero-to-peak)
```
Background-noise correction (energy subtraction; valid when S+N − N ≥ 3 dB):
```
L_signal = 10·lg( 10^(L_sn/10) − 10^(L_n/10) )
```
Ship radiated noise and source level (ISO 17208):
```
LRN = 20·lg(p_rms/p₀) + 20·lg(r/r₀)   dB re 1 µPa·m
d_s = 0.7·D                            (D = mean draught)
ΔL  = −10·lg[ (2(k·d_s)⁴ + 14(k·d_s)²) / (14 + 2(k·d_s)² + (k·d_s)⁴) ] dB,  k = 2πf/c
Ls  = LRN + ΔL                         (equivalent monopole broadside source level)
```
Pile driving cumulative exposure (ISO 18406):
```
SEL_cum = 10·lg( Σₙ 10^(SELₙ/10) );  for N identical strikes = SEL_ss + 10·lg(N)
```

## Architecture — three modules (one concept each)

### `src/phonometry/underwater_acoustics.py` (ISO 18405)
Shared reference constants and level primitives, referred to 1 µPa:
- `UNDERWATER_REFERENCE_PRESSURE = 1e-6` (Pa), `UNDERWATER_REFERENCE_EXPOSURE = 1e-12` (Pa²s)
- `sound_pressure_level(pressure)` → SPL, dB re 1 µPa
- `sound_exposure_level(pressure, fs)` → SEL, dB re 1 µPa²s
- `peak_sound_pressure_level(pressure)` → dB re 1 µPa (zero-to-peak)
- `background_noise_correction(signal_plus_noise_db, noise_db)` → corrected
  level; emits an `UnderwaterAcousticsWarning` when the 3 dB validity margin is
  not met (returns the uncorrected level, per ISO 17208-1).
- `underwater_to_in_air_spl(level)` / `in_air_to_underwater_spl(level)` — the
  ±26.0 dB reference-pressure conversion (20 µPa ↔ 1 µPa), documented as a
  level-reference change (not an energy/intensity equivalence).

### `src/phonometry/ship_radiated_noise.py` (ISO 17208-1/-2)
- `radiated_noise_level(rms_pressure, distance)` → LRN, dB re 1 µPa·m
- `hydrophone_depths(cpa_distance, angles=(15,30,45))` → the three measurement
  depths from the depression angles (ISO 17208-1 geometry helper)
- `source_level_uncertainty(frequency)` → the tabulated expanded uncertainty
  (5 dB ≤100 Hz, 3 dB 125 Hz–16 kHz, 4 dB >16 kHz)
- `monopole_source_level(rnl, frequency, draught, *, c=1500.0)` →
  `ShipSourceLevelResult` with per-frequency `rnl`, `delta_l`, `source_level`,
  the source depth `d_s` and `c`; `.plot()` draws RNL, Ls and ΔL vs frequency.
  Accepts scalar or per-band arrays; `rnl` may be the mean of the three
  depression-angle RNLs.

### `src/phonometry/pile_driving_noise.py` (ISO 18406)
- `single_strike_sel(pressure, fs)` → SEL_ss (reuses the level primitive)
- `cumulative_sel(single_sels)` → SEL_cum from a sequence of per-strike SELs;
  `cumulative_sel_identical(sel_ss, n_strikes)` → SEL_ss + 10·lg(N)
- `pile_strike_metrics(pressure, fs)` → `PileStrikeResult` (single-strike SEL,
  peak SPL, SPL/Leq, 90 %-energy pulse duration); `.plot()` draws the strike
  waveform with the 5 %/95 % energy markers and the cumulative pulse energy.

### Reuse (no refactor)
The octave-band filter bank (`OctaveFilterBank`) for optional band-level SEL is
left to the caller; the existing plotting conventions (`_plotting.py`,
TYPE_CHECKING imports) and the frozen-dataclass-plus-`.plot()` idiom are followed.

## Error handling

Project idioms: 1-D finite pressure signals, `fs > 0`, positive distance /
draught / frequency, `c > 0`, `n_strikes ≥ 1`. No `assert` in `src/` (bandit).
`ValueError` for invalid inputs; a dedicated `UnderwaterAcousticsWarning` for the
background-noise 3 dB margin.

## Testing

- `tests/test_underwater_acoustics.py`: SPL/SEL/peak of a synthetic tone of known
  amplitude and duration (analytic); background-noise correction and its 3 dB
  warning; the ±26 dB reference conversion round-trip; validation errors.
- `tests/test_ship_radiated_noise.py`: LRN from known p_rms and distance;
  ΔL(k·d_s) against Formula 3 at several k·d_s plus the k·d_s→∞ ⇒ −3 dB limit;
  d_s = 0.7·D; hydrophone depths; uncertainty table; `.plot()` smoke.
- `tests/test_pile_driving_noise.py`: single-strike SEL of a synthetic pulse;
  cumulative SEL = SEL_ss + 10·lg(N) for identical strikes and the energy sum for
  differing strikes; peak level; pulse duration; `.plot()` smoke.
- Reference constants in `tests/reference_data.py`.

## Conformance (`scripts/conformance_report.py`)

New domain **"Underwater acoustics (ISO 18405/17208/18406)"**:
- SPL and SEL of a synthetic signal of known energy (exact).
- Peak sound pressure level of a known waveform (exact).
- RNL from known p_rms and distance (exact).
- ΔL surface correction at a known k·d_s against Formula 3 (exact).
- Cumulative SEL = SEL_ss + 10·lg(N) for N identical strikes (exact).
Byte-stable regeneration via `make conformance` (NO `2>&1`).

## Docs & figures

- New guide `docs/underwater-acoustics.md` + site EN/ES guides, with `<details>`
  figure-code snippets and a Standards footer; api-reference rows; README TOC;
  a new "Underwater acoustics" astro sidebar group.
- Figures ×4 variants:
  (a) ship equivalent monopole source level — RNL, Ls and the ΔL surface
      correction vs frequency for a known draught;
  (b) pile-driving strike — the pressure waveform with SEL_ss / peak markers and
      the cumulative-energy curve (5 %/95 % duration bounds).
- `check_figures.py` clean; deterministic SVG.

## Deliverables / gate

Full local gate: `ruff check .`, `mypy src scripts`, `bandit -r src`, `pytest`,
conformance N/N + no drift, site build (i18n + build + html-validate),
`check_figures.py`. Subagent review after implementation (also confirms the final
public-symbol names); fix findings in a second pass. CI green; review the bot
comments; squash-merge.

## Out of scope (YAGNI)

- **General underwater propagation modelling** (ray tracing, parabolic equation,
  normal modes): not part of ISO 18405/17208/18406, no oracle here — a distinct
  future domain, deliberately excluded.
- ISO 17208-1 Annex B correction formulae for non-standard geometries beyond the
  standard three-hydrophone deep-water case.
- Part B of task #19 (aeroacoustics) — separate PR.

## Risks

- The Lloyd's-mirror ΔL (Formula 3) diverges as k·d_s → 0 (grazing/low
  frequency); documented and guarded so callers understand the low-frequency
  limit rather than hitting a silent overflow.
- Final public-symbol/module names may be tuned by the end-of-PR review.

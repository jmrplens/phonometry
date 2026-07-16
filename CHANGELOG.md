# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Four new physics-based 2D FDTD documentation animations (WebM + poster
  for the site, GIF for the GitHub docs, EN + ES, light + dark), each
  simulated with `scripts/fdtd2d.py` and annotated on canvas:
  `anim_fdtd_barrier` (a thin rigid screen on reflecting ground driven at
  100 Hz vs 500 Hz side by side, with the measured insertion loss at a
  shadow-zone receiver, embedded in the outdoor-propagation guide),
  `anim_fdtd_ground_effect` (a 400 Hz source over a rigid plane forming
  the direct + image-source interference lobes, with the level on an 8 m
  arc converging to the two-path model and its predicted nulls, embedded
  in the outdoor-propagation and aircraft-noise guides),
  `anim_fdtd_ducting` (a low-frequency pulse trapped by a SOFAR-like
  sound-speed channel vs a near-surface source that leaks to depth, with
  the c(z) profile inset, embedded in the underwater-propagation guide)
  and `anim_fdtd_diffusion` (a plane wavefront onto a flat panel vs an
  N = 7 quadratic-residue Schroeder diffuser, with the scattered field
  and the ISO 17497-2 arc diffusion coefficients, embedded in the
  surface-scattering guide).
- Seven new mechanism animations (WebM + poster for the site, GIF for the
  GitHub docs, EN + ES, light + dark): the ISO 10534-2 standing wave in the
  impedance tube (rigid vs porous termination), the EN 12354-1 flanking
  paths Dd/Ff/Fd/Df, the ISO 9614-2 intensity scan accumulating partial
  powers into L_W, the ISO 18233 sweep deconvolution into the impulse
  response, the ISO 532-1 specific-loudness pattern and its integral, the
  same source measured in an anechoic and a reverberation room converging
  to one L_W, and comb filtering from a single floor reflection; embedded
  in the materials, insulation-prediction, sound-power, intensity,
  room-acoustics and loudness guides (EN + ES) with deferred loading, plus
  a `--anim NAME` flag on `scripts/generate_graphs.py` to re-render a
  single clip.
- `scripts/fdtd2d.py`: a small deterministic 2D acoustic FDTD engine
  (staggered-grid pressure-velocity leapfrog, heterogeneous c/rho maps,
  rigid walls, sponge absorbing layers, Gaussian-pulse and CW sources,
  frame subsampling for animation rendering) with physics and determinism
  tests, backing the physics-based documentation animations.
- `anim_fdtd_room_modes`: a 2D FDTD documentation clip driving a rigid
  5 m × 3,5 m room on its (2,1) mode and between modes, showing the
  standing-wave pattern and the RMS mode map growing to dominance on
  resonance while the off-mode response stays weak and disorganised;
  embedded in the room-acoustics and reverberation-prediction guides
  (EN + ES).
- Clause 5.3.8 Step 3 inside `analyze_spectrum` (DIN 45681 / ISO PAS 20065):
  audible tones sharing a critical band are energy-summed (Formula (17),
  shared lines counted once) into a combined FG entry rated at the most
  audible member, with the exactly-two-tones-below-1000-Hz separation
  exception (Formulae (18)/(19)); the new `group_sizes` field on
  `ToneAudibilityResult` tells single tones from FG entries and the decisive
  audibility now follows Step 4 as printed.
- DIN 45681:2005-03 Anhang I oracle: the Tabelle I.9 wind-energy-plant
  spectrum reproduces the decisive Tabelle I.10 row end to end (LS 41,71 /
  LT 68,10 / dL 12,52 / u 3,18 dB), Tabelle I.11 rows j = 45/48 pin the
  Formulae (12)-(14) chain, the printed 5 FG row pins the two-tone
  combination decision, and Tabelle A.1 pins Formula (2) at 24 printed
  bandwidths.
- `verify_weighting_class`: a dense IEC 61672-1 5.5.7 sweep between the
  nominal frequencies (analytic Annex E design goal, larger of the adjacent
  limits) so a resonance or notch between nominals can no longer pass, and a
  `range_limited` flag when Table 3 rows with finite lower limits fall
  beyond Nyquist.
- `Barrier(line_of_sight_clear=True)`: the ISO 9613-2 negative-z sign
  convention when the sight line passes above the top edge; Eq. (14) is
  evaluated with Kmet = 1 and Dz decays continuously from 10 lg 3 at grazing
  to 0, never granting screening credit below the sight line.
- `wind_turbine_tonality`: the IEC 61400-11 9.5.2 possible-tone screening
  and a `has_identified_tone` flag (spectra without an identified tone must
  be excluded from the 9.5.1 bin averaging); `slant_distance` gains the
  vertical-axis Formula 2 (`rotor_axis="vertical"`, R0 = H + D).
- `uncertainty_from_repeated_measurements`: the primary ISO 1996-2
  Formulae (17)+(19) energy-domain route as `standard_uncertainty`, with the
  Note 2 substitute kept as `approximate_uncertainty` and a spread warning.
- `ResidualCorrectionResult.reportable_upper_bound`: the uncorrected
  measured level, the value 10.4 permits reporting when the margin is 3 dB
  or less; `ImpulseProminenceResult.qualifies`: the NT ACOU 112 clause 4.5
  onset-rate qualification mask.
- Published-oracle promotions: GUM Annex H.1 end to end through
  `combine_uncertainty` (uc = 31,71 nm, U99 = 92,1 nm), GUM Annex H.2 as the
  correlated Equation (16) oracle (uc(R/X/Z) = 0,071/0,295/0,236 ohm),
  GUM-S1 Tables 2 and 3 coverage intervals (+/-3,92 Gaussian, +/-3,88
  rectangular with a seeded Monte Carlo conformance entry), the full
  ISO 9613-2 Table 2 grid (6 conditions x 8 octave bands at exact midbands)
  and the IEC 61260-1 Table F.1 breakpoints with both E.3.4 rounding
  examples.
- New warning classes: `WindTurbineNoiseWarning`, `UncertaintyWarning` and
  `ImpulseProminenceWarning`.
- `itu_r_468_weighting`: the ITU-R BS.468-4 Table 1 weighting-network
  response (identical to the IEC 60268-1 Appendix A network that
  IEC 60268-3 14.12.11 requires), interpolated per the recommendation's own
  log-frequency rule; `weighted_thd` now defaults to it (`'468'`), keeps
  `'A'`/`'C'` as labelled options and documents the 31,5 Hz - 400 Hz
  fundamental validity range.
- AES17 measurement-bandwidth chain for `thd_plus_noise`, `sinad` and
  `harmonic_analysis`: both the residual and the total signal are measured
  through a 20 Hz high-pass plus the standard low-pass (clauses 5.2.5 /
  6.3.1) with a configurable `bandwidth` (default 20 kHz;
  `bandwidth=None` keeps the full-Nyquist measurement).
- `ModulationDistortionResult`: `modulation_distortion` now returns the
  IEC 60268-3 14.12.7 per-order values `d2`/`d3` together with the
  SMPTE-analyzer combined RMS as the explicitly labelled `smpte` field.
- Hearing and electroacoustics oracle expansion: the SII quiet condition at
  the official worksheet full precision plus a discriminating
  noise-plus-hearing-loss case and the independent R package Example C.2;
  the IEC 60268-16 Ed.5 C.3.2 STIPA direct-method staircase (m = 0 to 1
  through the full audio path, tolerance 0,05); the clipped-sine THD
  Fourier constants; a full-signal DIM regression (1,536 MHz synthesis of
  the standard test signal through a weak polynomial nonlinearity,
  FIR-decimated to 192 kHz, checked against an exact-bin FFT oracle); the
  H1 input-noise bias SNR/(1+SNR); the printed ITU-R 468 response values
  with the AES17 CCIR-RMS cross-check; and the effective notch-Q
  validation on the applied zero-phase response.
- ISO 532-1 Annex B.4 level-ramp oracles (Test signals 6-9): the tone and
  pink-noise ramps are regenerated from parameters measured on the official
  electronic-attachment WAVs and pinned to the workbook Nmax/N5 with
  tolerances calibrated against those WAVs; the sub-1-sone phon conversion
  and the NX percentile are now confirmed line by line against the
  attachment's Annex A.4 reference program source.
- `docs/ERRATA.md` entry for IEC 60268-3:2013 clause 14.12.9.2 f): the
  printed DIM denominator ("U2") contradicts the 14.12.9.1 definition
  (the output amplitude at f_s), which the library follows.
- ISO/PAS 20065:2016 extended uncertainty of the audibility (Clauses 5.4/6):
  `audibility_uncertainty` propagates the uniform 3 dB narrow-band level
  uncertainty through the audibility chain to the extended uncertainty U
  (90 % bilateral coverage, k = 1,645) and `mean_audibility_uncertainty`
  combines the per-spectrum values through the Formula (20) mean;
  `analyze_spectrum` reports the per-tone U on its result. Verified against
  the printed Table E.2 U column (decisive tone to 0,006 dB), the 2 FG row
  and the Annex E Step 4 mean uncertainty (1,38 dB).
- ISO 532-1 stationary `time_skip` parameter (Annex B.1's TimeSkip: the
  stationary calculation starts from 0,2 s when validating against the
  official recordings, excluding leading silence and the filterbank
  transient from the mean square).
- Psychoacoustics oracle expansion: the shipped ISO 532-1 Annex B.4 Test
  signal 13 and a B.3 pink-noise bounds check; all 21 DIN 45692 Table A.2
  rows and all 20 Table A.3 broadband rows at the normative 5 % / 0,05 acum
  tolerance (plus a non-definitional Table A.2 conformance row at 2,5 kHz);
  the ISO 532-2 Annex B phon columns; the ISO 532-3 Annex C.3 multi-tone
  complexes, the C.1.2/C.1.3 sone columns and the Annex C.1 anchor pinned at
  32/44,1/48 kHz native rates; the ECMA-418-2 decision thresholds as
  constants-tests (audibility 0,01 sone_HMS, prominent tonality 0,4 tu_HMS,
  prominent roughness 0,2 asper); a loudness/tonality N'_tonal
  cross-consistency test on the shared Clause 6.2 intermediate; the
  fluctuation-strength carrier sweep (F&Z Fig. 10.5 trend) and the Osses
  Table 1 AM-broadband-noise row as a trend cross-check; and the full
  ISO/PAS 20065 Tables E.2/E.3/E.4 columns (LG, av, band limits, per-tone
  and mean uncertainties, all-spectra tone records).
- ECMA-418-1 TNR/PR degenerate-input warnings: peaks within one bin of the
  89,1 Hz / 11,2 kHz range edge (bin snapping can flip the prominence
  verdict) and critical bands at numeric-noise power (silence, DC) now warn;
  the `prominent` verdict is documented as the numeric criterion only (the
  clause 11.8/12.8 aural examination and clause 8/9 hearing-threshold screen
  are the caller's responsibility).
- `docs/ERRATA.md` entries for the review findings: the ECMA-418-1 clause
  4.1.2 "11 220 Hz" range misprint, the internally inconsistent
  ECMA-418-2 clause 5.1.5.2 last-block formula, the ISO/PAS 20065 clause
  5.3.4 edge-steepness print that contradicts the executable DIN 45681
  Annex J program, and the Osses 2016 Eq. (3) Bark-constant exponent typo.

- Underwater printed-source oracles promoted to tests and the conformance
  report: the Wong & Zhu (1995) ITS-90 check tables pin the UNESCO and
  Del Grosso sound-speed refits at 17 printed grid points each (agreement
  within the printed 0.001 m/s resolution), the Francois & Garrison (1982,
  Part II) Table IV pins the total seawater absorption at 21 printed points
  spanning 0.4 kHz-1 MHz (within half a unit of the last printed digit), and
  the Wales & Heitmeyer (2002) ensemble merchant-ship mean spectrum is pinned
  against the paper's printed closed form and asymptote statements
  (exponents -3.6/-1.76, 340 Hz breakpoint).
- `docs/ERRATA.md`: a versioned registry of the defects found in published
  standards and guidance documents during implementation (misprints, worked
  examples contradicting their own normative text, ambiguous wording), each
  with the evidence, the library's disposition and a report status.
- ISO 7626-2:2015 measurement-side acceptance criteria:
  `rigid_mass_calibration_check` implements the 7.5.2 operational calibration
  on a rigid block of known mass (|A| = 1/m or |Y| = 1/(2 pi f m) within
  +/-5 %, per-band pass flags in a `RigidMassCalibrationResult`) and
  `random_error_percent` the Annex A normalized random error
  eps = sqrt((1-gamma^2)/(2 n gamma^2)) with the 8.1.3 < 5 % averaging
  criterion; measured-FRF processing per 8.1.3 (H1) and coherence checks are
  documented through the existing `transfer_function`/`coherence` estimators.
- ISO 10846-1:2008 Equation (6): `blocking_force_ratio` quantifies the
  blocking-force approximation F2/F2,b = 1/(1 + k2,2/kt) (within 10 % for
  |k2,2| < 0,1 |kt|, Eq. (7)).
- Vibration oracles promoted to tests and the conformance report: the nine
  printed ISO 8041-1:2017 Annex B design-goal tables (318 bands) with a
  Table 5 tolerance-envelope check and the Wb/Wc/Wd/We/Wf/Wj design-goal
  points, the ISO 2631-5:2018 Annex C NOTE 5 female worked example
  (Sd = 1,40 MPa, R = 0,97) and the Annex D Table D.1 digital-filter
  cross-check of Formula 1, the ISO 7626-2 rigid-mass calibration values and
  Annex A random-error example, the omega = 1000 rad/s rigid-mass decade
  identity, the ISO 10846-3 validity anchors (|T| = 0,1 <->
  DeltaL1,2 = 20 dB, model bias 1,1 within 1 dB / 12 %), the ISO 10846-1
  Eq. (6) force ratio 1/1,1 and the 7.6 linearity criterion (10 dB input
  step within 1,5 dB).
- ISO 717 enlarged frequency ranges: `weighted_rating_extended` computes the
  Annex B spectrum adaptation terms (C50-3150, C50-5000, C100-5000 and the
  Ctr counterparts, Table B.1 spectra) and `weighted_impact_rating_extended`
  the CI,50-2500 term of ISO 717-2:2020 A.2.1; both offer the 0,1 dB
  reference-curve shift and one-decimal reductions for uncertainty statements
  (ISO 12999-1:2020 Annex B), reproducing the printed Rw = 57,4 dB example
  and the A.2.2 constants Ln,r,0,w = 77,6 dB / CI,r,0 = -10,3 dB.
- ISO 16251-1 statement of results: the floor-covering improvement now rates
  any spectrum containing the 16 bands 100-3150 Hz (the clause 6.3 18-band
  range included) and exposes the spectrum adaptation term CI,delta
  (ISO 717-2:2020 Formula (A.4)) as `ci_delta` /
  `impact_improvement_adaptation_term`.
- EN 15657:2018 source-quantity chain: `equivalent_blocked_force_level`
  (Formula 15), `characteristic_reception_plate_power` (Formula 17,
  Y_R,inf,low = 5e-6 m/(N s)), `equivalent_free_velocity_level` (Formula 18)
  and `source_mobility_from_levels` (Formula 19), plus the EN 12354-5 Annex I
  mobility correction `installed_power_from_reception_plate`; the raw
  Formula (14) level is re-documented as the plate-injected power.
- ISO 9611:1996 `mean_free_velocity_level` (equation (9) energy mean over
  contact points, v0 = 5e-8 m/s) with a conformance check.
- EN 12354-1 Annex E junction families E.7 (lightweight double leaf with
  homogeneous elements), E.8 (coupled double-leaf walls) and E.9 (corner and
  thickness change), and the E.5 K24 double-leaf branch (clamp read as
  -4 dB <= K24 <= 0 dB; the 2000 print's "0 <= K24 <= -4 dB" is a misprint).
- EN 12354-1 Formula (5b) `standardized_level_difference` (DnT,w from R'w,
  exact 0,32 V/Ss form) closing both Annex H.3 examples to 54 dB.
- EN 12354-3 Annex C facade-shape term lookup
  `facade_shape_level_difference` (Figure C.2, all nine shapes, alpha_w
  interpolation).
- ISO 10848-4 Clause 9 modal-overlap bracketing: `vibration_reduction_index`
  accepts the per-band modal overlap factor, flags M < 0,25 bands as
  `bracketed` and excludes them from the single-number Kij.
- ISO 15186-1 Clause 6.4.6 negative-direction subareas: `combine_subareas`
  accepts signed subarea areas (minus sign for reverse energy flow) with
  Sm = sum(|Smi|), raising when the signed energy sum is not positive.
- Oracles promoted to tests and the conformance report: ISO 717-1:2020
  Annex C Table C.2 (enlarged 50-5000 Hz range), ISO 717-2 Annex C Table C.1
  covered floor (64, -3, 30,0 dB) and Table C.2 improvement (15 dB,
  CI,delta = -9 dB), ISO 12999-1:2020 Annex B single numbers and
  uncorrelated/correlated uncertainties, all 12 printed EN 12354-1 Annex H.3
  path values with the DnT,w closures, the remaining EN 12354-4 Table G.9
  reception cells, ISO 10140-5 Tables B.1/C.1 reference elements and floors
  end-to-end, the printed ISO 15186-1 Table B.1 Kc rows, and the EN 12354-5
  Annex I whirlpool (Table I.6a) and flushing cistern (Tables I.8/I.9)
  worked examples replacing the former formula-restatement checks.

- Underwater validation: independent image-source absolute TL anchors for the
  normal-mode and parabolic-equation solvers, the published UNESCO EOS-80
  canonical sound-speed check value (Fofonoff & Millard 1983), six additional
  JOMOPANS File S1 oracle rows, the Ainslie-McColm Table I reference oceans
  against Francois-Garrison, Wenz-chart graphical anchors for the wind noise,
  and the RANDI 3.1 report's representative source levels (Table 2) for the
  ship-spectrum model; two new conformance checks (198 total).
- ECAC Doc 32 rotorcraft: `reference_distance` parameter on
  `spherical_spreading_adjustment` and `atmospheric_adjustment` for hemispheres
  recorded at a non-standard polar distance, and an end-to-end propagation-chain
  oracle against the NORAH2 prototype single-event histories (0.1 dB(A) over
  hard ground) plus off-node bilinear spot checks on the reference hemispheres
  of all eleven rotorcraft types.
- ECAC Doc 29 airport noise: landing-rollout modelling (`landing_roll` mask;
  reduced noise fraction Eq. 4-21b, nearest-end geometry, no directivity term)
  and per-segment bank angle (`bank`, §4.5.2 sign convention). ICAO Annex 16
  EPNL: the bandsharing adjustment ΔB (App. 2 §4.4.2/4.4.3), exposed as
  `EPNLResult.bandsharing_adjustment`, and a `start_band` parameter on
  `tone_correction` for the helicopter 50 Hz procedure.
- STIPA certified-bench verification: the IEC 60268-16 rev 5 verification
  test-bench signals from stipa.info (Embedded Acoustics BV) run as a local
  end-to-end oracle over `stipa` / `sti_from_impulse_response` (49 WAVs
  across Annexes C.3.2 modulation-depth staircase, C.3.3 exponential decays,
  C.4.2 filter slope, A.2.2 weighting factors and A.3.1.2 phase distortion;
  the suite skips cleanly when the local data is absent), plus seven synthetic
  conformance checks that re-derive the same constructions in CI (one of them
  replacing the previous C.3.2 m = 0,5 check, so the total grows by six): the
  C.3.2 staircase at m = 0,2/0,5/0,8 (±0,01 STI), the C.3.3 RT60 = 1 s decay
  against the closed-form Schroeder MTF (±0,005), the C.4.2 slope criterion
  (m ≥ 0,5 under a +41 dB unmodulated adjacent-octave tone) and the
  A.2.2/A.3.1.2 audio-path checks (257 checks total).

### Changed

- The documentation animations now render at 300 DPI (2400x1350, from
  800x450) for crisp playback on high-density displays, keeping the same
  8x4.5 figure so no layout re-tuning is needed. The VP9 WebM encode gains
  screen-content tuning and row multithreading (`-tune-content screen
  -row-mt 1 -deadline good -cpu-used 4`), which roughly halves the encode
  time at the same file size; the GitHub GIF fallback stays at 640 px. All
  16 clips (four language x theme variants each) now render on a spawned
  process pool, one grouped task per clip so each FDTD field is simulated
  once and reused across its variants; `make animations` and the `--jobs`
  flag drive it, while `--anim NAME` keeps the single-clip re-render
  sequential. The site `<video>` embeds and posters follow the new intrinsic
  size. A handful of on-canvas readability fixes ride along: Spanish decimal
  commas in the FDTD time readouts, repositioned time and caption labels so
  they clear tick labels and legends, a legible dark pill behind the ducting
  channel-axis label, a mathtext `L_W` subscript in the two-rooms readout,
  and the onset magnifier kept fully inside its panel.
- The four Tier-1 documentation animations are redesigned as mechanism
  infographics instead of line-plot reveals: `anim_time_weighting` shows the
  tone burst driving the IEC 61672-1 RC detector (square-law rectifier,
  capacitor charging/draining, F/S/I meter needles), `anim_onset_detection`
  scans L_AF with a magnifier and lights the NT ACOU 112 OR/LD/P/KI decision
  chain, `anim_instantaneous_intensity` animates a two-microphone p-p probe
  with p/u phasors and a flipping intensity arrow (active vs reactive), and
  `anim_schroeder` fills the tail energy of the squared impulse response
  while the decay curve and T20/T30 fits emerge on a companion axis. A
  shared scaffold (schematic axes, mic symbols, meter gauges, pipeline
  boxes, updatable arrows) backs all clips; filenames and the WebM/GIF
  variant pipeline are unchanged. Every animation embed now loads deferred
  with its space pre-reserved: `_save_animation` exports a poster still per
  WebM variant (`anim_<name>[_es][_dark]_poster.jpg`, a frame inside the
  closing hold; JPEG so the posters stay outside the SVG/PNG `make graphs` /
  `check_figures.py` pipeline, refreshable via `make posters` /
  `--posters`), the site `<video>` embeds use `preload="none"` plus the
  poster and explicit `width`/`height` (no `autoplay`), and the GitHub-docs
  GIF embeds carry `loading="lazy"` with their intrinsic size, so no clip
  fetches eagerly and none shifts the layout while loading. Future clips
  inherit the convention automatically.
- `scripts/generate_graphs.py` renders the documentation figures on a
  process pool: each (figure, language, theme) combination is an independent
  task (spawned workers, language/theme applied per task), except the five
  psychoacoustic figures whose `lru_cache`-memoised ECMA-418-2 / ISO 532
  analyses render their four variants grouped in one worker so the cache
  reuse of the sequential run is preserved. Output is byte-identical to the
  sequential run (all 624 committed assets hash-equal on the same machine);
  the full four-variant regeneration drops from 196 s to 53 s on a 12-core
  dev box. New CLI flags: `--jobs N` (default: cores minus two, capped at 8;
  `--jobs 1` keeps the old in-process sequential path) and `--figure NAME`
  (repeatable single-figure filter); `--animations` / `--all` are unchanged
  and the clips still render sequentially.
- ECMA-418-2 chain: the per-lag Python loop of the unbiased ACF
  normalization (Formulae 27-29) is now column-vectorised, the Clause 6.2.3
  neighbour-band averaging accumulates without the stacked copy, the ACF
  normalization reuses the block-RMS energy array, and the roughness
  Clause 7.1.7 pchip
  interpolation runs all 53 bands in one call. Outputs are bit-identical
  (guarded by bitwise equivalence tests against retained reference loops and
  the golden baseline); on the 0.5 s bench signal `loudness_ecma` drops from
  2.78 s to 2.00 s, `tonality_ecma` from 2.74 s to 2.01 s and
  `roughness_ecma` from 0.24 s to 0.23 s. The remaining runtime is the
  standard-mandated 16384-point DFTs, which no bit-preserving reformulation
  (rfft, one-sided magnitudes, batched or alternative FFT backends) can
  reduce.
- ECAC Doc 29 `noise_contour` now evaluates the grid with one vectorised pass
  per flight-path segment instead of a per-point Python loop; numerically
  identical (guarded by the golden baseline and a scalar-equivalence test)
  and ~45x faster on small grids, several hundred times on production-size
  grids (30 000 points in ~0.2 s).

### Fixed

- G-weighting (ISO 7196) digital design is now sample-rate aware: at the low
  sample rates common for infrasound recordings, 315 Hz approaches Nyquist
  and the un-prewarped bilinear design warped the upper response; the design
  now oversamples toward 48 kHz so the response at 315 Hz stays within a few
  hundredths of a dB of the 48 kHz design at any rate (at 48 kHz and above
  the design is unchanged).
- STI analysis filter bank is now zero-phase (forward-backward filtering):
  the single-pass bank failed two normative verification criteria of
  IEC 60268-16:2020 on the certified test bench - the C.4.2 filter-slope
  test (an unmodulated tone one octave below the observed band, 41 dB
  louder, leaked with only ~31 dB attenuation and dragged the measured m
  down to ~0,1 against the m ≥ 0,5 criterion) and the A.3.1.2
  phase-distortion limit (STI bias reached -0,020 at TI = 0,9 against the
  < 0,01 criterion). Zero-phase filtering removes the phase bias by
  construction and doubles the effective skirt attenuation to ~63 dB one
  octave out; all 49 certified bench signals now pass (worst slope-test
  m = 0,937, worst edge-carrier bias -0,0029). STI values on ordinary
  signals of the recommended >= 15 s duration shift by at most ~0,003
  (larger only below the minimum-duration warning threshold; the
  sti_vs_t60 figures are regenerated accordingly).
- `stipa` no longer raises when an octave band of the recording carries no
  energy: dead bands read m = 0 (TI = 0, the worst-case reading of a real
  meter) under an `STIWarning`, so component-level verification signals
  that deliberately occupy only some bands (IEC 60268-16 C.4.2) remain
  measurable.
- DIN 45681 / ISO PAS 20065 single-line tones: the tone level of a K = 1 run
  is the line level itself (Formula (7)); the Hanning bandwidth correction
  applies only to K > 1 sums (Formula (8)). The unconditional -1,76 dB
  understated every single-line audibility and could flip weak
  near-bin-centred tones to inaudible.
- `verify_weighting_class` and the conformance report's A/C branch evaluate
  the SOS at the exact base-10 frequencies behind the Table 3 nominal labels
  (Table 3 NOTE; IEC 61672-3 13.3), removing a pairing bias of up to
  0,27 dB; `verify_filter_class` evaluates the Table 1 breakpoints exactly
  with `sosfreqz` instead of interpolating off the grid (the 16-point floor
  now reproduces the dense-grid verdict).
- IEC 61400-11 tone classification anchors the 10 dB cut, the reported tone
  frequency and the Formula 34 criterion to the highest classified tone
  line (9.5.3/9.5.4), not the probed candidate; truncated critical bands
  warn and candidates below 20 Hz are rejected.
- ISO 1996-2 residual correction: with a margin of 3 dB or less no
  correction is allowed and the uncorrected level is the reportable upper
  bound (the previous wording inverted the bound);
  `gaussian_residual_level` rejects inverted percentile orderings.
- ISO 9613-2 `atmospheric_absorption` evaluates alpha at the exact base-10
  midbands (the Table 2 convention; ~1,3 % high at 8 kHz before); grazing
  barrier geometry (z = 0) now yields Dz = 10 lg 3 instead of 0.
- GUM `combine_uncertainty`: a correlated budget with finite input degrees
  of freedom carries undefined effective dof (the GUM defines no correlated
  Welch-Satterthwaite form; r = 0,999 with nu = 5 previously produced
  k95 ~ 2e151) and `expanded()` then requires an explicit coverage factor;
  the finite-difference step is the input uncertainty with a 64-ULP floor,
  preserving locality for large-magnitude inputs while a tiny uncertainty
  on a large value no longer underflows to uc = 0; `monte_carlo` rejects
  trials < 2.
- NT ACOU 112: level rises with onset rates at or below 10 dB/s no longer
  produce a KI adjustment (clauses 4.5/8).
- `sensitivity()` rejects non-finite reference samples (a NaN propagated
  silently to a NaN calibration factor); docstring thresholds aligned with
  IEC 60942:2017 Table 2 and the plain-bilinear weighting class notes with
  the measured behaviour (class 1 holds at 44,1/48 kHz, degrades at
  fs <= 32 kHz).
- SII (ANSI S3.5-1997): the equivalent disturbance spectrum level is the
  clause 5.6 maximum of the equivalent masking and internal noise levels,
  not their energy sum; the index for a hearing-impaired listener in
  moderate noise was underestimated by up to 0,042 (0,1841 vs the
  standard's 0,2185 for normal speech in flat 30 dB noise with a flat
  40 dB loss). Confirmed against the official worksheet (=MAX in every
  band) and the R CRAN worked example.
- IEC 60268-3 intermodulation reworked to the clause-exact quantities:
  `modulation_distortion` reports the per-order arithmetic sideband sums
  over the f2 output (14.12.7.2 g-h) instead of one combined RMS;
  `difference_frequency_distortion` references U_2,ref = 2 U_2,f2 and sums
  the third-order products arithmetically (14.12.8.1) instead of halving
  the reference (+6 dB on d2, +3 dB on d3); and
  `total_difference_frequency_distortion` implements 14.12.10.1 directly
  (only the two in-band products over the tone-amplitude sum, standard
  8 kHz / 11,95 kHz tones as defaults) instead of sqrt(d2^2 + d3^2).
- Intermodulation product search windows no longer swallow neighbouring
  components: octave-spaced clean tones read 0 instead of d2 = 1,0, DC
  offsets no longer leak into d3, out-of-band products clamp to
  (0, Nyquist), and the two TDFD products can no longer double-count.
- THD+N/SINAD measured noise over the full Nyquist band: at fs = 192 kHz
  white noise read +7 dB versus the AES17 band-limited value and a DC
  offset was counted as noise; both now pass through the AES17
  measurement-bandwidth chain by default.
- The AES17 standard notch was designed at the nominal Q but applied
  zero-phase (filtfilt squares the response), so the applied quality
  factor was 0,644x nominal (a requested 2,0 acted as 1,29; requests below
  ~1,87 silently fell outside the AES17 [1,2, 3] range). The design Q is
  now compensated by sqrt(1 + sqrt(2)) so the applied response has the
  requested quality factor.
- `thd` returned 0,0 when no harmonic of the fundamental fitted below
  Nyquist (for example a 20 kHz fundamental at fs = 48 kHz); it now raises,
  and captures shorter than 64 samples are rejected.
- THD/SINAD documentation labelled both THD conventions as the
  IEC 60268-3 14.12.2-3 quantity and cited AES17 for SINAD; the R
  convention is now identified as the 14.12.3.2 formula and SINAD as
  derived from the AES17 THD+N (AES17 does not define SINAD).
- Psychoacoustic annoyance combined the weightings as
  N5*sqrt(1 + wS^2 + wFR^2) where Fastl & Zwicker Eq. (16.2) prints
  PA = N5*(1 + sqrt(wS^2 + wFR^2)); every PA with a nonzero
  sharpness/fluctuation/roughness contribution was 13-29 % low, and the
  worked reference value had been hand-computed with the same wrong form.
  The worked tuple now anchors PA = 37,0478.
- ECMA-418-2 roughness omitted the mandatory Clause 5.1.2 5 ms fade-in and
  its calibration signal was synthesized with the carrier (not the overall
  signal) at 60 dB SPL. With both corrected the chain reproduces the
  Clause 7 reference to 0,99990 asper with the tabulated c_R; the former
  "+7,35 % clean-room methodology variance" narrative was wrong and is
  removed everywhere.
- ECMA-418-2 loudness skipped the cross-block-size-group ACF recomputation
  of Clause 6.2.3 (tonal content near the block-size boundaries was
  mis-stated by up to -9,5 %); loudness and tonality now share one full
  Clause 6.2.3 tonal/noise split and report identical N'_tonal. The 1 kHz /
  40 dB calibration computes 0,9845 sone_HMS with the verbatim c_N; the
  residual's origin is documented in the module. The common time grid is
  sized from the 1024-sample stage (no more trailing edge-held samples) and
  the tonality band-range arguments are validated per Formulae 56/57.
- Fluctuation strength transcribed the misprinted Bark constant 0,76e-4 from
  Osses 2016 Eq. (3); the Zwicker-Terhardt formula and the paper's own
  anchors require 0,76e-3. The 47 filter centres now span 50 Hz-13,2 kHz
  (was 491 Hz-20 kHz with 12 duplicate edge bands) and carrier-frequency
  behaviour matches F&Z Fig. 10.5 (C_FS = 0,279, near the paper's 0,2490).
- ISO 532-1 Annex B validation tests had silently skipped since the test
  tree reorganization (broken relative fixtures path behind a skip guard);
  the path is fixed and an in-repo presence assertion prevents a recurrence.
- DIN 45692 Aures/von Bismarck sharpness variants used self-derived
  normalization constants where Formulas (B.1)/(B.2) print the literal
  k = 0,11 (every Aures result was +4,2 % against the published formula);
  the reference sound now lands near, not exactly at, 1 acum
  (0,96/1,02 acum) and is asserted non-circularly.
- ISO 532-1 filterbank tables were mislabelled (Table A.1 is the reference
  section; the per-band deviations and gains are Table A.2), and the
  sone-to-phon mapping documents the reference-program provenance of its
  exact 10/lg 2 factor and 3 phon floor.
- Underwater Francois-Garrison absorption used the Medwin & Clay textbook
  transcription of the boric-acid factor (8.68/c); the original paper prints
  8.86/c and only that value reproduces the paper's own Table IV (the
  transcription biased boric-dominated bands at 0.6-30 kHz by up to 1.7 %).
- ISO 10846-3 indirect method returned out-of-validity results silently:
  `transfer_stiffness_indirect` now computes the per-band transmissibility
  magnitude and emits a `PhonometryWarning` where |T| > 0,1 (Inequality (2):
  DeltaL1,2 < 20 dB, outside the 1 dB / 12 % accuracy of Formula (1)),
  exposes the limit as `TRANSMISSIBILITY_LIMIT`, and documents the
  blocking-mass rigidity criterion 10 lg(m2,eff^2/m2^2) <= 1 dB
  (Inequality (3)) with the Formula (4) effective-mass measurement.
- SDOF clause attributions for ISO 7626-1: the closed-form resonator
  (H = 1/(k - w^2 m + jwc), peak mobility 1/c) was cited as "Annex A", which
  covers matrix impedance/mobility relations; module, tests, docs and
  conformance now cite it as closed form consistent with the Table 1 / 3.1.2
  definitions, and the mobility definition citation is corrected from 3.1 to
  3.1.2.
- Zero-denominator edges in the vibration FRF modules raise an explicit
  ValueError instead of propagating inf/NaN: `transfer_stiffness_direct`
  with a zero input displacement, `transfer_stiffness_level` of a zero
  magnitude, `loss_factor` of a purely imaginary stiffness, and
  `convert_frf` of a zero value through a force-per-motion reciprocal.
- Documentation: `convert_frf`/`MobilityResult.to` reciprocals are the free
  quantities of ISO 7626-1 3.1.4 (blocked matrix quantities do not invert
  element-wise; Table 1 names F/a the effective mass), the ISO 2631-5 input
  record must be conditioned (DC-removed) since the seat-to-spine transfer
  is unity at 0 Hz, and `weighted_acceleration` notes that ISO tables
  tabulate at true one-third-octave centres 10^(n/10), not nominal labels.
- ISO 10848 octave-band single-number Kij averaged the wrong range: the
  one-third-octave 200-1250 Hz mask was reused on octave centres, dropping
  the 125 Hz octave (a +0,5 dB bias per dB/octave of Kij slope); octave
  results now average 125-1000 Hz per Annex A, and `octave_bands()` validates
  that the input groups into whole octave triples.
- EN 12354-2 Formula (3) standardization used the Annex E.3 rounding
  10 lg(V/30); `standardized_impact_level` now applies the exact
  10 lg(0,032 V) form (the E.3 rounding stays documented), removing a
  constant -0,18 dB bias.
- `flanking_element` never applied the mandatory Kij,min floor of EN 12354-1
  Clause 4.4.2 / Formula (29); passing the flanking-element area now clamps
  each path automatically.
- EN 12354-4 `radiated_sound_power` no longer caps R' at 40 dB by default:
  the cap is an Annex G worked-example footnote, not part of Formula (2)/(3)
  (pass `r_prime_cap=40.0` to reproduce Annex G).
- `equivalent_impact_level` warns outside the 100-600 kg/m2 envelope of the
  EN 12354-2 Annex B relation; `structure_borne_power_level` validates the
  loss factor; the EN 12354-5 coupling terms validate source/receiver
  mobilities instead of silently returning NaN/inf;
  `single_number_uncertainty_uncorrelated` validates finiteness of both
  inputs.
- Documentation corrections: the EN 15657 Formula (14) level is the
  reception-plate injected power (not the characteristic source level; the
  EN 12354-5 chain needs the Formula (15)/(17) conversion), the EN 12354-4
  Annex E (E.2a)/(E.2b) branches do not "meet within rounding" (about
  -0,7 dB step for a square side), the `modal_overlap_factor` docstring no
  longer claims an exclusion the code did not apply, and
  `materials/dynamic_stiffness` no longer points to ISO 16251-1 (whose scope
  excludes floating floors).

#### Previously in Unreleased

- Underwater Wenz wind noise was referenced to the historical 20 µPa
  (0.0002 dyn/cm²) pressure while labelled dB re 1 µPa: every wind spectrum
  level (and the ambient composite) was 26.02 dB low and the wind/thermal
  crossover appeared at ~12 kHz instead of ~63 kHz. The rule-of-fives anchor
  is now 25 + 20·lg(20) = 51.02 dB re 1 µPa²/Hz at 1 kHz / 5 kn, matching the
  published Wenz chart; slopes unchanged, figures regenerated.
- Underwater `normal_modes` derives its default depth grid from the physics,
  restricts the eigensolve to the propagating band, discards eigenvalues
  inside the finite-difference error band about cutoff (previously a spurious
  extra mode could appear at under-resolved settings) and warns when a
  retained near-cutoff mode needs a finer grid.
- Underwater `ray_trace` evaluates the sound-speed gradient exactly per
  profile segment instead of smoothing kinks through an interpolated fine
  grid (turning-depth errors of metres on thermocline profiles).
- Underwater documentation accuracy: ISO 17208-2 uncertainty band edges and
  the standard's 16-20 kHz gap, Ainslie-McColm ~10 % agreement caveat at
  domain corners, the inherent Francois-Garrison A3 step at 20 °C, published
  validity domains of the sound-speed equations, wind-speed validity of the
  Wenz law, the paraxial (~±15-20°) validity of the standard PE, and stale
  cross-references; `sound_speed_profile` now evaluates in a single
  vectorised pass.
- ECAC Doc 32 rotorcraft: hemisphere gap-fill now fills the grid first and
  interpolates over all four corners (Eq. 14/15 before Eq. 13), so cells with
  some missing corners keep their measured corners instead of snapping to the
  single nearest bin; nearest-bin ties are compared through dot products
  (well-conditioned near zero angular distance); single-row/column grids are
  handled explicitly; the low-band advisory warning is no longer emitted for
  the standard 10-40 Hz NORAH bands; and the atmospheric docstring states the
  pure-tone choice and its deviation from the guidance's SAE band mapping
  (up to 2.2 dB/km at 8-10 kHz) instead of overclaiming Table 4.
- ECAC Doc 29: behind takeoff ground-roll segments the lateral attenuation and
  installation effect now use the §4.5.5 nearest-end geometry (previously the
  track perpendicular, which zeroed both terms on the extended centreline and
  overpredicted behind-the-runway levels by up to about 10 dB); runway segments
  use the Eq. 4-13b average speed (V = 0 start-of-roll waypoints are now
  accepted); the exposure elevation angle on inclined segments follows the
  equivalent-level-path convention (Fig. 4-6); maximum-level metrics use the
  nearest-end lateral geometry behind/ahead; NPD lookups clamp to the
  recommended 30 m floor (also fixes a crash for receivers exactly under the
  path). Validated against seven branch-covering receptor events of the ECAC
  Doc 29 Vol 3 Part 1 reference workbook.

## [3.2.0] - 2026-07-13

### Added

- Twelve domain namespaces: `phonometry.metrology`, `.psychoacoustics`,
  `.hearing`, `.emission`, `.room`, `.materials`, `.building`, `.vibration`,
  `.environmental`, `.aircraft`, `.underwater` and `.electroacoustics`, each a
  curated subpackage usable as `from phonometry import aircraft as air`. The
  flat top-level API is unchanged and remains the primary surface.

### Changed

- The internal package layout is reorganized into the domain subpackages
  above; every pre-3.2 flat module path (for example `phonometry.insulation`,
  `phonometry.underwater_acoustics`) keeps importing for one deprecation
  cycle and warns on attribute access. They are removed in 4.0.

### Deprecated

- The pre-3.2 flat module paths (see Changed). Pickles created with 3.2
  reference the new module paths and will not unpickle under 3.1.

## [3.1.0] - 2026-07-13

### Added

- `air_attenuation()` and `air_attenuation_m()` (with the
  `AtmosphericAbsorptionWarning`) — pure-tone atmospheric absorption coefficient
  α per ISO 9613-1:1993 (Eq. 3–5) from frequency, temperature, humidity and
  pressure; reproduces Table 1 to under 0,4 % and exposes the ISO 354 power
  attenuation coefficient m = α/(10 lg e). `exact_midband=True` snaps onto the
  Table 1 midbands.
- ISO 9613-2:1996 outdoor sound propagation: `outdoor_propagation_attenuation()`
  and `predicted_receiver_level()` with the `OutdoorAttenuation` per-term
  breakdown, plus the individual terms `geometric_divergence()`,
  `atmospheric_absorption()`, `ground_attenuation()` (general 7.3.1),
  `ground_attenuation_alternative()` / `directivity_omega()` (alternative 7.3.2),
  `barrier_attenuation()` with the `Barrier` geometry dataclass, and
  `meteorological_correction()`. `DEFAULT_FREQUENCIES` gives the nominal octave
  bands.
- `task_based_exposure()`, `job_based_exposure()` and `full_day_exposure()`
  (with `Task`, `ExposureResult` and `OccupationalExposureWarning`) — ISO 9612:2009 daily
  noise exposure LEX,8h by the three measurement strategies and the normative
  Annex C uncertainty budget (k = 1,65 one-sided 95 %, the C.6 I(I−1) vs
  C.12 N−1 sampling asymmetry, Table C.4 and the LEX,8h + U upper limit); the
  Annex D/E/F worked examples reproduce to the standard's printed precision.
- Documentation: new **Outdoor Sound Propagation** guide (ISO 9613-1/2, EN + ES),
  an **ISO 9612 occupational exposure** section in the Levels guide, theory and
  API-reference sections, four new figures each (air absorption α(f), the
  per-term attenuation breakdown and the exposure-uncertainty example) and the
  source–barrier–receiver geometry diagram. Conformance report adds seven
  ISO 9613-2 / ISO 9612 checks (41 total).

- `loudness_moore_glasberg()`, `loudness_moore_glasberg_from_spectrum()` and
  `loudness_moore_glasberg_from_third_octave()` with the `MooreGlasbergLoudness`
  result and its `.plot()` — stationary Moore-Glasberg loudness per
  ISO 532-2:2017 (level-dependent roex excitation pattern on the ERB-number/Cam
  scale, compressive specific loudness and binaural inhibition), anchored so a
  1 kHz / 40 dB SPL tone is 1.000 sone.
- `loudness_moore_glasberg_time()` and `MooreGlasbergTimeVaryingLoudness` (with
  `.plot()`) — time-varying Moore-Glasberg-Schlittenlacher loudness per
  ISO 532-3:2023: the short-term S′(t) and long-term S″(t) loudness traces, the
  peak long-term loudness N_max and percentile long-term loudness.
- `loudness_ecma()` and `EcmaLoudness` (with `.plot()`) — Sottek Hearing Model
  loudness per ECMA-418-2:2025 (sone_HMS) on the 53-band Bark_HMS auditory
  front-end; a 1 kHz / 40 dB SPL tone calibrates to ≈ 1 sone_HMS.
- `tonality_ecma()` and `EcmaTonality` (with `.plot()`) — ECMA-418-2:2025
  tonality (tu_HMS) from the autocorrelation of the band signal, with the
  time-dependent tonality T(l), the average specific tonality T′(z) and the
  per-band tonal frequency; a 1 kHz / 40 dB tone calibrates to ≈ 1 tu_HMS.
- `roughness_ecma()` and `EcmaRoughness` (with `.plot()`) — ECMA-418-2:2025
  roughness (asper), a new capability, from the band-envelope modulation
  analysis; the reference 1 kHz carrier 100 %-AM at 70 Hz, 60 dB SPL calibrates
  to ≈ 1 asper.

- One-line canonical `.plot()` method on every public result object —
  `ZwickerLoudness`, `STIResult`, `RoomAcousticsResult`, `DecayCurve`,
  `WeightedRatingResult`, `ImpactRatingResult`, `SoundPowerResult`,
  `ReverberationSoundPowerResult`, `SoundPowerIntensityResult` and
  `IntensityResult` — reproducing each result's documentation figure in a
  single call (`res.plot()`). matplotlib stays a soft dependency: importing
  and computing work without it, and `.plot()` raises a clear `ImportError`
  with `pip install phonometry[plot]` guidance when it is missing. The
  renderers create their own figure when `ax` is `None`, always return the
  Matplotlib `Axes` (an array for multi-panel figures) and never call
  `plt.show()`, so they compose into larger layouts. To feed those
  figures, `WeightedRatingResult` and `ImpactRatingResult` now also carry
  `band_centers`, `measured` and `shifted_reference`, exposing the ISO 717
  measured curve and shifted reference behind each single-number rating.
- `sweep_signal()`, `inverse_filter()`, `impulse_response()`, `mls_signal()`
  and `mls_impulse_response()` — deterministic-excitation impulse-response
  acquisition per ISO 18233:2006 (exponential sine sweep with spectral and
  Farina deconvolution, maximum-length sequences), verified by recovering
  known impulse responses at the correct sample lags.
- `decay_curve()`, `room_parameters()` and `RoomAcousticsResult` — room
  acoustic parameters per ISO 3382-1:2009 / 3382-2:2008 (Schroeder backward
  integration with noise truncation and tail compensation; EDT/T20/T30,
  C50/C80, D50, Ts with dynamic-range validity flags and curvature),
  verified against the exponential-decay closed forms within their JNDs.
- `open_plan_metrics()` and `OpenPlanResult` — open-plan-office spatial
  speech metrics per ISO 3382-3:2012 (spatial decay rate D2,S and Lp,A,S,4m
  from the log-distance regression, distraction distance rD and privacy
  distance rP from the STI-vs-distance line).
- `airborne_insulation()`, `weighted_rating()`, `energy_average_level()`
  and the `AirborneInsulationResult` / `WeightedRatingResult` dataclasses —
  field airborne sound insulation per ISO 16283-1:2014 (D, DnT, R') and
  single-number weighted ratings with C/Ctr per ISO 717-1 (reference-curve
  method), verified against the ISO 717-1 Annex C worked example.
- `impact_insulation()`, `weighted_impact_rating()` and the
  `ImpactInsulationResult` / `ImpactRatingResult` dataclasses — field impact
  sound insulation per ISO 16283-2 (standardized L'nT and normalized L'n from
  the tapping-machine impact level) and single-number weighted impact ratings
  with the CI adaptation term per ISO 717-2 (reference-curve method, octave
  −5 dB rule), verified against the ISO 717-2 Annex C examples (Ln,w = 79,
  CI = −11; octave 54, CI = 0).
- `facade_insulation()` and `FacadeInsulationResult` (with `.plot()`) — field
  façade sound insulation per ISO 16283-3:2016: the level difference D2m from
  the level 2 m in front of the façade, its standardized D2m,nT and normalized
  D2m,n forms, and the apparent element-method sound reduction index R′45°
  (loudspeaker, −1.5 dB) / R′tr,s (road traffic, −3 dB), rated to a single
  number with the ISO 717-1 airborne engine.
- `lab_airborne_insulation()`, `lab_impact_insulation()`,
  `background_correction()` and the `LabAirborneInsulationResult` /
  `LabImpactInsulationResult` dataclasses (with `.plot()`) plus the
  `LabInsulationWarning` — laboratory sound insulation per ISO 10140: the direct
  sound reduction index R (Part 2) and normalized impact level Ln (Part 3) with
  the Sabine absorption area A = 0,16 V/T (Part 4), background-noise correction
  with the 6/15 dB limit-of-measurement rule, and single-number ratings via the
  reused ISO 717-1/2 engines.
- `predicted_airborne_insulation()`, `predicted_impact_insulation()`,
  `junction_vibration_reduction()`, `junction_min_vibration_reduction()`,
  `flanking_path()`, `flanking_element()`, `combine_linings()`,
  `equivalent_impact_level()`, `impact_flanking_correction()`,
  `standardized_impact_level()` and the `AirbornePredictionResult` /
  `ImpactPredictionResult` / `FlankingPath` / `PathContribution` dataclasses —
  building acoustic performance prediction per EN 12354-1/-2:2000 (simplified
  single-number model): the apparent R′w from the direct path and the twelve
  flanking paths of four elements (Ff/Df/Fd each) with the Annex E junction
  vibration reduction index Kij and the Kij,min
  floor, and the apparent L′n,w from the bare-floor equivalent level, covering
  improvement and Table 1 flanking correction. Verified against the EN 12354-1
  Annex H.3 (R′w = 52 dB) and EN 12354-2 Annex E.3 (L′n,w = 45 dB) worked
  examples.
- `band_uncertainty()`, `single_number_uncertainty()`,
  `single_number_uncertainty_uncorrelated()`,
  `maximum_repeatability_standard_deviation()`, `coverage_factor()`,
  `expanded_uncertainty()`, `uncertain_value()`, `combine_uncertainties()`,
  `prediction_input_uncertainty()`, `reduce_by_independent_measurements()`,
  `satisfies_lower_requirement()`, `satisfies_upper_requirement()`, the
  `BandUncertainty` / `UncertainValue` dataclasses and the `COVERAGE_FACTORS`
  mapping — measurement uncertainty in building acoustics per ISO 12999-1:2020:
  the tabulated standard uncertainties for the three measurement situations
  (A/B/C, Tables 1–7 and Annex D), the expanded uncertainty U = k·u with the
  Table 8 coverage factors, and the combination, reduction and conformity rules
  (Annexes A/B/C, one-sided and two-sided).
- `absorption_area()`, `absorption_coefficient()`, `attenuation_from_alpha()`
  and `AbsorptionWarning` — sound absorption in a reverberation room per
  ISO 354:2003 (equivalent absorption area from the empty and with-specimen
  reverberation times via Sabine's equation with the air-attenuation term, and
  the plane-absorber coefficient αs, left unclamped per Clause 3.7), with
  room-volume and sample-area qualification advisories.
- `sound_power_pressure()`, `measurement_positions()`,
  `background_noise_correction()`, `environmental_correction()` and
  `SoundPowerResult` / `SoundPowerWarning` — sound power level from surface
  sound pressure per ISO 3744:2010 (engineering) and ISO 3746:2010 (survey):
  hemisphere and box measurement surfaces, background (K1) and environmental
  (K2) corrections, A-weighted total, directivity index and expanded
  uncertainty.
- `sound_power_reverberation()`, `sound_power_comparison()` and
  `ReverberationSoundPowerResult` — precision-grade sound power in a
  reverberation room per ISO 3741:2010 (direct method with Sabine absorption
  area, Waterhouse boundary correction and C1/C2 meteorological corrections;
  comparison method against a reference sound source), with room-qualification
  advisories.
- `sound_power_intensity()` and `SoundPowerIntensityResult` — sound power by
  sound-intensity scanning per ISO 9614-2:1996 (partial powers over the
  measurement surface, FpI and F+/− field indicators, per-segment
  repeatability and the per-band achieved engineering/survey grade).
- `loudness_zwicker()` / `loudness_zwicker_from_spectrum()` — Zwicker
  loudness per ISO 532-1:2017 (stationary and time-varying), a clean-room
  port of the normative reference program with the full Annex B validation
  set in CI (25 test cases, per-sample tolerance bands).
- `sharpness_din()` — sharpness in acum per DIN 45692:2009 with the Aures
  and von Bismarck variants, verified against the Table A.2 targets.
- `sti_from_impulse_response()`, `stipa()` and `stipa_signal()` — Speech
  Transmission Index per IEC 60268-16 Ed. 5 (indirect and direct STIPA
  methods, Ed. 5 male spectrum, Annex F ratings), verified against the
  standard's weighting-pair and m-mapping vectors and the Schroeder
  closed form.
- `sound_intensity()`, `field_indicators()`, `dynamic_capability_index()` —
  two-microphone p-p sound intensity per IEC 61043 (cross-spectral
  estimator, finite-difference bias correction validated against Table 3)
  with the ISO 9614-1 Annex A field indicators.
- `weighting_filter(..., curve="G")` — G frequency weighting for infrasound
  (ISO 7196:1995), verified against every Table 2 nominal response value.
- `equal_loudness_contour()`, `loudness_level()`, `hearing_threshold()` —
  ISO 226:2023 normal equal-loudness-level contours (Formulae 1-2, Table 1),
  verified against the Annex B tables.
- `tone_to_noise_ratio()` and `prominence_ratio()` — prominent discrete tone
  assessment per ECMA-418-1:2024 (clauses 10-12), including proximate-tone
  combination and the low-frequency truncated band.
- `lden()`, `ldn()`, `composite_rating_level()` — environmental noise
  descriptors per ISO 1996-1:2016 (3.6.4/3.6.5 and clause 6.5).
- `calculate_sensitivity(..., narrowband=True)` — opt-in coherent
  single-frequency (Goertzel) tone estimator that locks to the calibrator
  tone near `frequency` and rejects broadband hum/noise in the reference
  take, which otherwise inflates the RMS and biases the sensitivity by
  `-10*lg(1 + 1/SNR)` (about -0.42 dB at 10 dB SNR). The default keeps the
  legacy broadband-RMS behaviour.
- `decay_curve(..., zero_phase=...)` and `room_parameters(..., zero_phase=...)`
  — optional forward-backward (time-reversed) octave filtering permitted by
  ISO 3382-2:2008 Clause 7.3 NOTE (relaxing B*T > 16 to B*T > 4). It removes
  the octave filter's group delay before the backward integration, roughly
  halving the 125 Hz short-decay T30 bias. Default off (causal).
- `sound_intensity(..., bias_correct=True)` — optional per-bin
  finite-difference correction `(k*dr)/sin(k*dr)` (IEC 61043:1994, 7.3)
  applied to the band and broadband intensity totals so they no longer
  under-read toward `max_valid_frequency`. Default off (legacy totals).
- **STIPA (IEC 60268-16):** `stipa()` now emits a `UserWarning` for
  recordings shorter than the recommended 15 s, where the recovered
  modulation depths (and STI) are biased low.
- `tone_to_noise_ratio()` / `prominence_ratio()` (ECMA-418-1) now warn when
  the FFT resolution is too coarse to resolve the tone band (fewer than
  ~3 bins across the 15 % tone half-width), which biases TNR/PR at low
  frequencies.
- `mls_impulse_response()` (ISO 18233) now warns when the recovered impulse
  response still carries energy at the end of the MLS period, the symptom of
  an impulse response longer than one period aliasing circularly (choose a
  higher MLS order).
- `practical_absorption_coefficient()`, `weighted_absorption()` and
  `absorption_class()` — practical sound-absorption coefficient and the weighted
  rating αw with shape indicators (L/M/H) and class A–E per ISO 11654:1997.
- Impedance-tube absorption, surface impedance and transmission loss
  (`impedance_tube` module) per ISO 10534-1/-2:1998 (standing-wave and
  transfer-function methods) and the four-microphone transmission-loss method of
  ASTM E2611, with the ISO/ASTM speed-of-sound and air-density models.
- `airflow_resistance()`, `specific_airflow_resistance()`, `airflow_resistivity()`
  and `static_airflow_resistance()` — airflow resistance of porous materials by
  the steady (ISO 9053-1:2018) and alternating (ISO 9053-2:2020) methods.
- `random_incidence_absorption()`, `specular_absorption_coefficient()`,
  `directional_diffusion()` and the ISO 17497-1/-2 scattering/diffusion
  coefficients — scattering and diffusion of surfaces (ISO 17497-1:2004 random-
  incidence scattering, ISO 17497-2:2012 directional diffusion).
- In-situ road-surface absorption (`road_absorption` module) per
  ISO 13472-1/-2 (extended surface and Adrienne temporal-windowing methods) with
  the geometric-spreading and reflection-factor machinery.
- Precision sound power in an anechoic/hemi-anechoic room (ISO 3745:2012) and by
  discrete-point intensity scanning (ISO 9614-3:2002).
- Human vibration exposure (`human_vibration` module) per ISO 8041-1:2017 /
  ISO 2631-1:1997 (whole-body) and ISO 5349-1:2001 (hand-arm): the frequency
  weightings, running RMS/MTVV, vibration dose value (VDV), motion-sickness dose,
  daily exposure A(8), HAV daily exposure and lifetime VWF, and the
  Directive 2002/44/EC action/limit-value assessment.
- `spinal_response()`, `acceleration_dose()`, `daily_dose()` and `daily_dose_multi()`
  (`multiple_shock_vibration` module) — adverse health effect of multiple shocks
  on the lumbar spine per ISO 2631-5:2018 (seat-to-spine models, the Se dose and
  daily equivalent static compressive stress Sed).
- `verify_weighting_class()` — frequency-weighting (A/C/Z) conformance to the
  IEC 61672-1:2013 Table 3 class-1/2 acceptance limits.
- `verify_filter_class()` — one-third-octave and octave band-filter conformance
  to IEC 61260-1:2014 / ANSI S1.11-2004, including class 0.
- `speech_intelligibility_index()` and `standard_speech_spectrum()` — the Speech
  Intelligibility Index per ANSI S3.5-1997 (critical-band, one-third-octave and
  octave procedures) with the standard normal/raised/loud/shout vocal-effort
  speech spectra.
- `noise_criterion()` / `room_criterion()` — NC and RC Mark II room-noise ratings
  per ANSI/ASA S12.2-2019.
- `age_threshold()` and `reference_threshold()` — age-associated hearing threshold
  (median and percentiles) per ISO 7029:2017 with the ISO 389-7:2019 free/diffuse-
  field reference threshold of hearing.
- `nipts()` and `htlan()` — noise-induced permanent threshold shift and the
  hearing threshold level associated with age and noise per ISO 1999:2013.
- Measurement uncertainty (`uncertainty` module): `rectangular()`, `triangular()`,
  `u_shaped()`, `combine_uncertainty()`, `coverage_factor()`,
  `expanded_uncertainty()` and `monte_carlo()` — the GUM framework (ISO/IEC
  Guide 98-3:2008) law-of-propagation-of-uncertainty and the Supplement 1 Monte
  Carlo method.
- `impulse_prominence()`, `impulse_adjustment()` and `rating_level()` — impulsive-
  sound prominence and the LAeq adjustment/rating level per Nordtest NT ACOU 112.
- Environmental-noise determination per ISO 1996-2:2017: the tonal-audibility
  adjustment (engineering method) and the associated measurement uncertainty.
- Reverberation-time prediction from room geometry and surface absorption by the
  Sabine, Eyring, Millington-Sette, Fitzroy and Arau-Puchades models.
- Façade sound insulation and indoor→outdoor radiation prediction per
  EN 12354-3:2000 and EN 12354-4:2000.
- Sound absorption in enclosed spaces (`enclosed_space_absorption` module) —
  `equivalent_absorption_area()` and `enclosed_space_reverberation()` per
  EN 12354-6:2003 (surface and object absorption, air absorption, reverberation
  time).
- Sound insulation by the intensity method per ISO 15186-1:2000
  (intensity-based sound reduction index).
- Field survey method per ISO 10052:2021, including the Table 3 reverberation-
  time estimator.
- Sound-absorption measurement uncertainty (`absorption_uncertainty` module) per
  ISO 12999-2:2020.
- Impact-sound improvement of floor coverings on a lightweight mock-up per
  ISO 16251-1:2014.
- Laboratory flanking transmission per ISO 10848 (the vibration reduction index
  Kij from velocity-level differences).
- `apparent_dynamic_stiffness()`, `installed_dynamic_stiffness()`,
  `natural_frequency()` and `floating_floor_resonance()` — dynamic stiffness of
  resilient materials per EN 29052-1:1992.
- `sdof_mobility()`, `sdof_accelerance()`, `sdof_receptance()`, `convert_frf()`
  and `resonance_frequency()` — mechanical mobility and the frequency-response-
  function family per ISO 7626-1:2011.
- `transfer_stiffness_direct()`, `transfer_stiffness_indirect()`,
  `transfer_stiffness_level()`, `loss_factor()` and `base_transmissibility()` —
  dynamic transfer stiffness of resilient elements per ISO 10846 (direct and
  indirect/transmissibility methods).
- `radiated_sound_power_level()`, `radiation_factor()`, `mean_velocity_level()`
  and `velocity_level_from_acceleration()` — sound power radiated from a vibrating
  surface per ISO/TS 7849-1/-2:2009.
- `structure_borne_power_level()`, `reception_plate_power()` and
  `spatial_mean_velocity_level()` — structure-borne sound power of building
  equipment by the reception-plate method per EN 15657:2017.
- `installed_structure_borne_power_level()`, `installed_source_prediction()` and
  the coupling-term functions — installed structure-borne sound from building
  equipment per EN 12354-5:2009.
- `tonal_audibility()` (`tone_audibility` module) — objective audibility of tones
  in noise by the Aures method per ISO/PAS 20065:2016 (tonal audibility ΔL and
  the tonal adjustment K).
- `psychoacoustic_annoyance()` and `psychoacoustic_annoyance_from_signal()` —
  Fastl & Zwicker psychoacoustic annoyance from loudness, sharpness, roughness
  and fluctuation strength.
- `thd()`, `thd_plus_noise()`, `sinad()`, `weighted_thd()` and
  `modulation_distortion()` — harmonic and intermodulation distortion per
  IEC 60268-3 / AES17, and `transfer_function()` / `coherence()` — H1/H2 frequency-
  response and coherence estimators (Bendat & Piersol).
- Underwater acoustics reference levels and metrics (`underwater_acoustics`):
  `sound_pressure_level()`, `sound_exposure_level()`, `peak_sound_pressure_level()`
  and the in-air↔underwater conversions per ISO 18405:2017; ship radiated-noise
  source levels (`ship_radiated_noise`) per ISO 17208-1/-2 with the ISO 18406
  hydrophone-depth and uncertainty machinery; and pile-driving SEL metrics
  (`pile_driving_noise`), single-strike and cumulative.
- Underwater sound propagation: `transmission_loss()`, `spreading_loss()` and
  `seawater_absorption()` (`underwater_propagation`); `sea_water_sound_speed()`
  and `sound_speed_profile()` (`underwater_sound_speed`); and the passive/active
  `sonar_equation`.
- Underwater seabed reflection (`seabed_reflection`: `critical_angle()`,
  `reflection_coefficient()`, `bottom_reflection_loss()`), ambient noise, and
  shipping-traffic source spectra (`ship_traffic_noise`, JOMOPANS-ECHO).
- Numerical underwater propagation solvers (`numerical_propagation`):
  `normal_modes()`, `ray_trace()` and `parabolic_equation()`.
- Aircraft noise (`aircraft_noise`): `perceived_noisiness()`,
  `perceived_noise_level()`, `tone_correction()`, `epnl_from_pnlt()` and
  `effective_perceived_noise_level()` — the Effective Perceived Noise Level per
  ICAO Annex 16 Vol. I Appendix 2 — plus `verify_aircraft_noise_system()`
  (IEC 61265 measurement-system tolerances).
- Wind-turbine noise (`wind_turbine_noise`): `apparent_sound_power_level()`,
  `slant_distance()` and `wind_turbine_tonality()` per IEC 61400-11.
- `sae_band_attenuation()` — one-third-octave-band atmospheric absorption by the
  SAE Method of SAE ARP 5534:2021 (pure-tone coefficient from ISO 9613-1).
- Airport noise (`airport_noise`, ECAC Doc 29): `npd_level()` / `npd_curve()`
  noise-power-distance interpolation; the single-event `event_level()` and
  ground-grid `noise_contour()` with the segment corrections
  `impedance_adjustment()`, `lateral_attenuation()`,
  `engine_installation_correction()`, `duration_correction()`,
  `noise_fraction()` and `start_of_roll_directivity()`.
- Rotorcraft noise (`rotorcraft_noise`, ECAC Doc 32 / NORAH2): the
  `RotorcraftHemisphere` source with `hemisphere_source_level()`, and the
  propagation adjustments `spherical_spreading_adjustment()`,
  `atmospheric_adjustment()` and `ground_effect_adjustment()` (Chien-Soroka).

### Changed

- Library-wide audit: shared input-validation and energy-summation helpers,
  consistent numeric types and a common warning base; the `.plot()` convention
  completed on every public result object; concept-based renames of the public
  API carried through a deprecation cycle; the three overloaded guides split by
  topic; and full EN/ES bilingual documentation with a complete API reference.
- Documentation figures migrated to deterministic, byte-reproducible SVG (with a
  tolerance-based CI check), new explanatory diagrams and Tier-1 animations added.

- `decay_curve()` now returns a `DecayCurve` dataclass (`time`, `level`,
  `band`) with a `.plot()` method instead of a bare `(time, level)` tuple.
  Backward compatible: `time, level = decay_curve(ir, fs)` still unpacks
  because `DecayCurve` iterates as `(time, level)`.
- `lc_peak()` now polyphase-oversamples the C-weighted signal (new
  `oversample` parameter, default 8) before peak detection, recovering the
  true inter-sample peak. Sustained high-frequency tones previously
  under-read by up to ~1.15 dB at fs = 48 kHz (e.g. an 8 kHz tone, 6.0
  samples/cycle); LCpeak now tracks the analytic peak within about +/-0.5 dB.
  Reported LCpeak values shift upward for HF-rich signals; pass
  `oversample=1` for the legacy on-grid behaviour.
- `OctaveFilterBank` / `octavefilter` default `attenuation` raised from 60 to
  72 dB. scipy's `cheby2` pins the equiripple deep-stopband floor at exactly
  `attenuation`, so the former 60 dB default sat 10 dB inside the IEC
  61260-1:2014 class 1 deep-stopband limit; 72 dB makes the default cheby2
  bank class 1 (same +0.400 dB passband margin as `butter`). Numerical
  outputs change for cheby2 users — and for elliptic (`ellip`) banks, which
  consume `attenuation` as their stopband attenuation `rs` — who relied on
  the previous default.
- Weighting-filter `high_accuracy` internal oversample target raised from
  96 to 144 kHz, so fs = 48 kHz now oversamples x3 (was x2). This halves the
  high-frequency residual vs the analytic A/C curves (48 kHz: -1.11 -> -0.44
  dB @16k, -2.10 -> -0.85 dB @20k) and removes the 48k-worse-than-44.1k
  asymmetry. High-accuracy weighting outputs shift for all rates below
  144 kHz (48/96/128 kHz included) — e.g. 96 kHz by +0.86 dB @16k / +1.63 dB
  @20k — always toward the analytic curve.
- Calibrator stability validation updated from IEC 60942:2003 to
  IEC 60942:2017 (Ed. 4): the deviations |max − mean| and |min − mean| are
  each compared against the limit, using the
  frequency-dependent Table 2 class 1 limits (0.07 dB in 160 Hz - 1.25 kHz);
  `calculate_sensitivity()` gains a `frequency` parameter.
- `ln_levels()` now discards 5*tau (was 2*tau) of the time-weighting
  integrator attack before computing the percentiles. At 2*tau the F
  integrator is only 86 % settled, so the leading ramp dragged the low
  percentiles down (~0.15 dB L10-L90 spread on a steady 2 s tone); 5*tau
  cuts that ~12x and matches the skip already used by the calibration
  stability check. Percentile values on short records shift slightly.

### Fixed

- **Sharpness (DIN 45692):** the informative Aures and von Bismarck variants
  are now anchored to exactly 1.00 acum on the clause 6 reference sound via
  per-variant normalization constants (previously 0.959 / 1.019 from a
  shared hard-coded factor).
- **Loudness (ISO 532-1):** N5/N10 percentiles are now computed on the
  full-rate 2000 Hz weighted-loudness series instead of the 4x-decimated
  500 Hz trace, removing an up-to-3% decimation-phase ambiguity. The
  500 Hz `time`/`loudness_vs_time` output and Nmax are unchanged.
- **Room acoustics (ISO 3382):** T20/T30 reverberation-time validity flags
  now require 46 dB / 54 dB of dynamic range (was 35 dB / 45 dB) to
  absorb the positive bias of the tail compensation and keep a flagged-valid
  decay time within the 5% JND (ISO 3382-2 Table A.1).
- **Impulse-response (ISO 18233):** `impulse_response(method="farina")` now
  raises `ValueError` when handed a zero-padded reference sweep (which
  silently produced a wrong inverse filter) instead of returning garbage;
  pass the unpadded sweep or use `method="spectral"`.

## [3.0.0] - 2026-07-06

### ⚠️ Breaking changes

- **The library is now `phonometry`** (formerly `PyOctaveBand`). Install with
  `pip install phonometry` and `import phonometry`. The API is unchanged — a
  plain rename of the import is a complete migration. The final
  `PyOctaveBand 2.1.0` release on PyPI is a transition stub that depends on
  `phonometry` and re-exports it under the old `pyoctaveband` module name with
  a `DeprecationWarning`, so `pip install -U PyOctaveBand` keeps existing code
  working. The last state under the old name is preserved in the locked
  [`pyoctaveband-v2`](https://github.com/jmrplens/phonometry/tree/pyoctaveband-v2) branch.
- **Python >= 3.13 required** (was >= 3.11). CI now tests 3.13 and 3.14
  (3.15 will be added once it reaches a stable release).

### Added

- `lc_peak()` — C-weighted peak level (IEC 61672-1 §5.13), verified against
  the Table 5 one-cycle/half-cycle tone-burst responses.
- `sel()` — sound exposure level (SEL/LAE), with class 1 conformance tests for
  the Table 4 LAE tone-burst column.
- `sound_exposure()` and `lex_8h()` — occupational noise dose (Pa²·h and
  normalized 8 h exposure level, IEC 61252).
- `calculate_sensitivity(..., validate=True)` — calibration-tone stability
  validation per IEC 60942 (short-term level fluctuation, class 1 limit),
  emitting `CalibrationWarning` on unstable or too-short recordings.

## [2.0.0] - 2026-07-06

### ⚠️ Numerical behavior changes

Results differ from 1.2.x for the following cases — all of them bring the
output in line with the governing standards:

- **Chebyshev II banks** now place their −3 dB points on the ANSI S1.11 band
  edges. Previously the band edges received the full stopband `attenuation`
  (−60 dB by default), underestimating broadband band levels by ~2.8 dB
  vs Butterworth. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- **Bessel banks** are designed with `norm="mag"`: −3 dB lands on the band
  edges (previously ~−10 dB, a ~2.2 dB broadband error). ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- **A/C frequency weighting** defaults to `high_accuracy=True`: the filter is
  designed and run at an internally oversampled rate (≥ 96 kHz), keeping the
  response within IEC 61672-1 class 1 tolerances up to 16 kHz at common audio
  rates (previously −2.67 dB at 12.5 kHz for fs = 48 kHz, outside class 1).
  Stateful weighting keeps the legacy design; `high_accuracy=True` with
  `stateful=True` raises. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))

### Added

- `verify_filter_class()`: verify a bank against the IEC 61260-1:2014
  class 1/2 acceptance limits (Table 1, transcribed from the official text)
  with per-band margins; `class_limits()` exposes the limit curves. ([#64](https://github.com/jmrplens/PyOctaveBand/pull/64))
- Standards-compliance test layer transcribed from the official texts:
  IEC 61672-1:2013 Table 4 tone-burst suite (F/S, 1 s to 1 ms) and Table 3
  full 34-frequency A/C weighting sweep within class 1 limits. ([#64](https://github.com/jmrplens/PyOctaveBand/pull/64))
- `CITATION.cff` and `.zenodo.json` metadata; Codecov coverage upload and
  quality badges. ([#64](https://github.com/jmrplens/PyOctaveBand/pull/64))
- Documentation: four new auto-generated figures (group delay, IEC
  toneburst, block continuity, IEC class mask), Mermaid diagrams, more
  equations, and a full SEO/GEO layer for the docs site (JSON-LD,
  llms.txt, AI-crawler opt-in, WCAG2AA gates). ([#66](https://github.com/jmrplens/PyOctaveBand/pull/66))
- `leq()`, `laeq()` and `ln_levels()` (L10/L50/L90 statistical levels from the
  Fast/Slow/Impulse envelope, with optional A/C weighting). ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `OctaveFilterBank.spectrogram()`: short-time band levels (bands × frames),
  multichannel-aware, with bounded-memory windowing. ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `zero_phase=True` option in `OctaveFilterBank.filter()` and `spectrogram()`:
  forward-backward filtering (no group delay) for offline analysis. ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `TimeWeighting` stateful class for block processing (block outputs match a
  single continuous call exactly). ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `weighting_filter(..., high_accuracy=...)` and
  `WeightingFilter(..., high_accuracy=...)` parameter. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- PEP 561 `py.typed` marker: downstream type checkers now receive the
  library's strict annotations.
- Documentation website (English/Español) at
  https://jmrplens.github.io/PyOctaveBand/ with theme-aware auto-generated
  figures, plus topic pages under `docs/`. ([#61](https://github.com/jmrplens/PyOctaveBand/pull/61))

### Fixed

- Integer input (e.g. int16 audio from `scipy.io.wavfile.read`) no longer
  overflows silently: `time_weighting` returned negative energies and
  `calculate_sensitivity` produced factors ~315× off. All inputs are converted
  to float64. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- `cheby2` with `attenuation <= 3.01 dB` now raises instead of silently
  producing NaN coefficients. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- `zero_phase` no longer crashes on heavily decimated bands shorter than the
  default `sosfiltfilt` padding. ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- The weighting-curves documentation figure measured a truncated impulse
  response through the resampling path (~2.4 dB low); the measurement is now
  guarded by tests. ([#63](https://github.com/jmrplens/PyOctaveBand/pull/63))

### Performance

- `octavefilter()` reuses cached filter-bank designs across calls (~3.3×
  faster in loops). ([#59](https://github.com/jmrplens/PyOctaveBand/pull/59))
- `numba` and `matplotlib` are optional extras (`[perf]`, `[plot]`, `[full]`);
  a pure-Python impulse kernel and lazy plotting imports keep full
  functionality without them. ([#59](https://github.com/jmrplens/PyOctaveBand/pull/59))

## [1.2.3] - 2026-05-30

### Fixed

- Importing the package no longer forces the matplotlib Agg backend. ([#53](https://github.com/jmrplens/PyOctaveBand/pull/53))

## [1.2.2] - 2026-05-09

### Added

- Configurable time weighting initial state (`initial_state`: `'zero'`,
  `'first'`, scalar or per-channel array). ([#49](https://github.com/jmrplens/PyOctaveBand/pull/49))

## [1.2.1] - 2026-03-08

### Added

- IEC 61260-1 nominal frequency labels (`nominal=True`). ([#46](https://github.com/jmrplens/PyOctaveBand/pull/46))

## [1.1.5] - 2026-03-08

### Fixed

- Overloads, `WeightingFilter` multichannel state, version sync and SonarCloud
  CI. ([#45](https://github.com/jmrplens/PyOctaveBand/pull/45))

## [1.1.4] - 2026-03-08

### Added

- Stateful block-wise processing for `OctaveFilterBank` and
  `WeightingFilter`. ([#42](https://github.com/jmrplens/PyOctaveBand/pull/42))
- macOS and Windows in the CI test matrix. ([#40](https://github.com/jmrplens/PyOctaveBand/pull/40))

## [1.1.1] - 2026-01-07

### Changed

- DSP core enhancements: vectorization, IEC standards alignment and
  precision. ([#35](https://github.com/jmrplens/PyOctaveBand/pull/35))

## [1.0.0] - 2026-01-06

Initial PyPI release: fractional octave filter banks (Butterworth,
Chebyshev I/II, Elliptic, Bessel), A/C/Z weighting, Fast/Slow/Impulse time
weighting, Linkwitz-Riley crossover, calibration and dBFS modes,
multichannel support.

[Unreleased]: https://github.com/jmrplens/phonometry/compare/v3.2.0...HEAD
[3.2.0]: https://github.com/jmrplens/phonometry/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/jmrplens/phonometry/compare/v3.0.0...v3.1.0
[3.0.0]: https://github.com/jmrplens/phonometry/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/jmrplens/phonometry/compare/v1.2.3...v2.0.0
[1.2.3]: https://github.com/jmrplens/PyOctaveBand/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/jmrplens/PyOctaveBand/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.5...v1.2.1
[1.1.5]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.1...v1.1.4
[1.1.1]: https://github.com/jmrplens/PyOctaveBand/compare/v1.0.0...v1.1.1
[1.0.0]: https://github.com/jmrplens/PyOctaveBand/releases/tag/v1.0.0

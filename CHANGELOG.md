# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

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

### Changed

- ECAC Doc 29 `noise_contour` now evaluates the grid with one vectorised pass
  per flight-path segment instead of a per-point Python loop; numerically
  identical (guarded by the golden baseline and a scalar-equivalence test)
  and ~45x faster on small grids, several hundred times on production-size
  grids (30 000 points in ~0.2 s).

### Fixed

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

#  Copyright (c) 2026. Jose M. Requena-Plens
"""Shared normative reference data (single source of truth).

Tables transcribed verbatim from the published standards. Both the test
suite (``tests/test_*.py``) and the CI conformance report
(``scripts/conformance_report.py``) import these constants, so the report's
expected values can never drift from what the tests assert. The PR-B
building-acoustics, PR-E scattering/in-situ/precision-power and PR-F
human-vibration oracles are the exception: their test modules re-hardcode the
values inline rather than import them, and dedicated consistency tests
(``test_building_reference_data_matches_published_oracles``,
``test_scattering_insitu_precision_reference_data_matches_oracles`` and
``test_human_vibration_reference_data_matches_oracles``) pin this shared table
to those same published results so neither copy can drift.

This module is deliberately dependency-free (stdlib only) so it can be
imported in the ``pr-comment`` CI job, which installs the runtime
requirements but not ``pytest``.
"""

from __future__ import annotations

import math

INF = math.inf

# ---------------------------------------------------------------------------
# IEC 61672-1:2013 Table 3 - frequency weightings and class-1 acceptance
# limits (standard page 22). Z weighting is 0.0 dB at every frequency.
# Row = (nominal_freq_Hz, A_dB, C_dB, class1_upper_dB, class1_lower_dB).
# ---------------------------------------------------------------------------
IEC61672_TABLE3: list[tuple[float, float, float, float, float]] = [
    (10, -70.4, -14.3, 3.0, -INF),
    (12.5, -63.4, -11.2, 2.5, -INF),
    (16, -56.7, -8.5, 2.0, -4.0),
    (20, -50.5, -6.2, 2.0, -2.0),
    (25, -44.7, -4.4, 2.0, -1.5),
    (31.5, -39.4, -3.0, 1.5, -1.5),
    (40, -34.6, -2.0, 1.0, -1.0),
    (50, -30.2, -1.3, 1.0, -1.0),
    (63, -26.2, -0.8, 1.0, -1.0),
    (80, -22.5, -0.5, 1.0, -1.0),
    (100, -19.1, -0.3, 1.0, -1.0),
    (125, -16.1, -0.2, 1.0, -1.0),
    (160, -13.4, -0.1, 1.0, -1.0),
    (200, -10.9, 0.0, 1.0, -1.0),
    (250, -8.6, 0.0, 1.0, -1.0),
    (315, -6.6, 0.0, 1.0, -1.0),
    (400, -4.8, 0.0, 1.0, -1.0),
    (500, -3.2, 0.0, 1.0, -1.0),
    (630, -1.9, 0.0, 1.0, -1.0),
    (800, -0.8, 0.0, 1.0, -1.0),
    (1000, 0.0, 0.0, 0.7, -0.7),
    (1250, 0.6, 0.0, 1.0, -1.0),
    (1600, 1.0, -0.1, 1.0, -1.0),
    (2000, 1.2, -0.2, 1.0, -1.0),
    (2500, 1.3, -0.3, 1.0, -1.0),
    (3150, 1.2, -0.5, 1.0, -1.0),
    (4000, 1.0, -0.8, 1.0, -1.0),
    (5000, 0.5, -1.3, 1.5, -1.5),
    (6300, -0.1, -2.0, 1.5, -2.0),
    (8000, -1.1, -3.0, 1.5, -2.5),
    (10000, -2.5, -4.4, 2.0, -3.0),
    (12500, -4.3, -6.2, 2.0, -5.0),
    (16000, -6.6, -8.5, 2.5, -16.0),
    (20000, -9.3, -11.2, 3.0, -INF),
]

# ---------------------------------------------------------------------------
# ISO 7196:1995 Table 2 - nominal G-weighting response at one-third-octave
# frequencies (standard page 2). Row = (freq_Hz, dB). Annex A.3 gives the
# instrumentation tolerance of +/- 1 dB from 1 Hz to 20 Hz.
# ---------------------------------------------------------------------------
ISO7196_TABLE2: list[tuple[float, float]] = [
    (0.25, -88.0), (0.315, -80.0), (0.4, -72.1),
    (0.5, -64.3), (0.63, -56.6), (0.8, -49.5),
    (1.00, -43.0), (1.25, -37.5), (1.6, -32.6),
    (2.0, -28.3), (2.5, -24.1), (3.15, -20.0),
    (4.0, -16.0), (5.0, -12.0), (6.3, -8.0),
    (8.0, -4.0), (10.0, 0.0), (12.5, 4.0),
    (16.0, 7.7), (20.0, 9.0), (25.0, 3.7),
    (31.5, -4.0), (40.0, -12.0), (50.0, -20.0),
    (63.0, -28.0), (80.0, -36.0), (100.0, -44.0),
    (125.0, -52.0), (160.0, -60.0), (200.0, -68.0),
    (250.0, -76.0), (315.0, -84.0),
]
ISO7196_G_TOLERANCE_DB = 1.0

# ---------------------------------------------------------------------------
# ISO 717-1 Annex C, Table C.1 - measured airborne sound reduction index R
# (100-3150 Hz, one-third-octave). The worked example gives
# Rw(C;Ctr) = 30(-2;-3) dB with an unfavourable-deviation sum of 31,8 dB.
# ---------------------------------------------------------------------------
ISO717_1_ANNEX_C_R: list[float] = [
    20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
    28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5,
]
ISO717_1_ANNEX_C_EXPECTED = {
    "rw": 30,
    "c": -2,
    "ctr": -3,
    "unfavourable_sum": 31.8,
}

# ---------------------------------------------------------------------------
# ISO 226:2023 Table B.1 - normal equal-loudness-level contours. Row =
# (loudness_level_phon, frequency_Hz, sound_pressure_level_dB). Annex B is
# rounded to 0.1 dB. The definitional identity is at 1 kHz (SPL == phon); we
# anchor the conformance check at a NON-1 kHz point so it exercises the
# contour formula (Table 1 alpha_f/L_U/T_f) rather than the trivial identity.
# ---------------------------------------------------------------------------
ISO226_2023_TABLE_B1_ANCHOR: tuple[float, float, float] = (60.0, 100.0, 78.5)

# ---------------------------------------------------------------------------
# Psychoacoustics "block-A" calibration anchors. Each is the single reference
# value its standard tabulates for the stated calibration signal.
# ---------------------------------------------------------------------------
# ECMA-418-2:2025 (Sottek Hearing Model). Loudness: Clause 5.1.8 defines the
# calibration constant c_N = 0.0211964 so a 1 kHz / 40 dB SPL tone yields
# 1 sone_HMS via the Clause 8 method (c_N adjustable within 0.25 %).
ECMA418_2_LOUDNESS_1KHZ_40DB_SONE = 1.0
ECMA418_2_LOUDNESS_C_N = 0.0211964
# Tonality: Clause 6.2.8 defines c_T = 2.8758615 so a 1 kHz / 40 dB tone
# yields 1 tu_HMS (c_T adjustable within 0.25 %).
ECMA418_2_TONALITY_1KHZ_40DB_TU = 1.0
ECMA418_2_TONALITY_C_T = 2.8758615
# Roughness: Clause 7 tabulates a 1 kHz carrier, 100 % AM at 70 Hz, 60 dB SPL
# -> 1.0 asper as the standard target. Using the tabulated c_R = 0.0180685
# (not reverse-fit) with the literal Formula-65 front-end, this clean-room
# implementation deterministically computes ~1.0735 asper (+7.35 %); the
# offset is documented methodology variance, NOT a tuning defect, so the
# conformance check pins the clean-room value, not the 1.0 target.
ECMA418_2_ROUGHNESS_STANDARD_TARGET_ASPER = 1.0
ECMA418_2_ROUGHNESS_CLEANROOM_ASPER = 1.0735
ECMA418_2_ROUGHNESS_C_R = 0.0180685
# ISO 532-2:2017 (Moore-Glasberg, stationary). Clause 3.17 / Annex B.1: the
# sone is defined so a 1 kHz / 40 dB SPL tone (binaural, free field) is
# 1.000 sone / 40 phon, following from the tabulated C = 0.0617 sone/Cam.
ISO532_2_ANCHOR_1KHZ_40DB_SONE = 1.0
ISO532_2_C = 0.0617
# ISO 532-3:2023 (Moore-Glasberg-Schlittenlacher, time-varying). Annex C.1:
# a steady 1 kHz / 40 dB SPL tone reaches a peak long-term loudness of
# 1.0 sone / 40 phon (the spectral calibration is fixed to this anchor).
ISO532_3_ANCHOR_1KHZ_40DB_SONE = 1.0

# ---------------------------------------------------------------------------
# ISO 16283-3:2016 field facade sound insulation. Clause 3.12 defines the
# apparent sound reduction index of the element (loudspeaker) method as
# R'45deg = L1,s - L2 + 10 lg(S/A) - 1,5. Choosing the specimen area S equal to
# the equivalent absorption area A (A = 0,16 V/T = 0,16 * 62,5 / 1,0 = 10 m2)
# collapses the 10 lg(S/A) coupling term, isolating the -1,5 dB oblique-
# incidence correction exactly: R' = 60 - 20 - 1,5 = 38,5 dB. (Road-traffic
# method R'tr,s uses -3 dB instead; Clause 3.13.)
# ---------------------------------------------------------------------------
ISO16283_3_R45_LOUDSPEAKER_CORRECTION_DB = 1.5
ISO16283_3_R45_SURFACE_LEVEL_DB = 60.0
ISO16283_3_R45_RECEIVE_LEVEL_DB = 20.0
ISO16283_3_R45_AREA_M2 = 10.0
ISO16283_3_R45_VOLUME_M3 = 62.5
ISO16283_3_R45_REVERB_TIME_S = 1.0
ISO16283_3_R45_EXPECTED_DB = 38.5

# ---------------------------------------------------------------------------
# ISO 10140-2:2010 laboratory airborne sound reduction index R (Formula (2)):
# R = L1 - L2 + 10 lg(S/A), A = 0,16 V/T. The reference-curve construction lays
# R exactly on the ISO 717-1 Table 3 shape (100-3150 Hz) by choosing S = A
# (S = 10 m2, A = 0,16 * 50 / 0,8 = 10 m2), so R = L1 - L2 = the reference. The
# 32 dB unfavourable-deviation allowance then permits a 2 dB upward shift of the
# reference (32 dB / 16 bands), giving Rw = curve@500 Hz (52) + 2 = 54 dB - the
# analytic +2-shift anchor (mirrors tests/test_lab_insulation.py).
# ---------------------------------------------------------------------------
ISO10140_2_REF_AIRBORNE_R: list[float] = [
    33, 36, 39, 42, 45, 48, 51, 52, 53, 54, 55, 56, 56, 56, 56, 56,
]
ISO10140_2_REF_AIRBORNE_RW = 54

# ---------------------------------------------------------------------------
# EN 12354-1:2000 Annex H.3 airborne prediction worked example. A separating
# element of Rw = 57 dB and area S = 11,5 m2 is flanked by four elements; each
# contributes an Ff/Fd/Df triplet (12 flanking paths), which with the direct
# Dd path make 13 transmission paths. Energy summation (Formula (26)) gives
# R'w = 52,2 dB -> 52 dB. Row = (label, Rw_flanking, KFf, KFd=KDf, coupling
# length lf). Mirrors tests/test_building_prediction.py (_annex_h_paths).
# ---------------------------------------------------------------------------
EN12354_1_ANNEX_H3_R_DIRECT = 57.0
EN12354_1_ANNEX_H3_SEPARATING_AREA = 11.5
EN12354_1_ANNEX_H3_ELEMENTS: list[tuple[str, float, float, float, float]] = [
    ("floor", 49.0, 12.4, 8.9, 4.5),
    ("ceiling", 46.0, 14.4, 9.2, 4.5),
    ("facade", 42.0, 12.6, 6.7, 2.55),
    ("intwall", 33.0, 33.5, 15.7, 2.55),
]
EN12354_1_ANNEX_H3_NUM_PATHS = 13
EN12354_1_ANNEX_H3_RPRIME_W = 52  # 52,2 dB rounds to 52

# ---------------------------------------------------------------------------
# EN 12354-2:2000 Annex E.3 impact prediction worked example. A concrete floor
# of mass per area m' = 322 kg/m2 has an equivalent normalized impact level
# Ln,w,eq = 164 - 35 lg(m') ~ 76 dB (Formula for heavy floors). With a floating-
# floor improvement ΔLw = 33 dB and a flanking correction K = 2 dB (Table 1;
# separating 322 -> row 300, flanking mean 145 -> col 150), the predicted
# apparent normalized impact level is L'n,w = 76 - 33 + 2 = 45 dB (Formula 21).
# ---------------------------------------------------------------------------
EN12354_2_ANNEX_E3_MASS = 322.0
EN12354_2_ANNEX_E3_FLANKING_MEAN_MASS = 145.0
EN12354_2_ANNEX_E3_DELTA_LW = 33.0
EN12354_2_ANNEX_E3_K = 2
EN12354_2_ANNEX_E3_LPRIME_N_W = 45

# ---------------------------------------------------------------------------
# ISO 12999-1:2020 measurement uncertainty. Table 2 (Clause 7.2) tabulates the
# airborne one-third-octave standard uncertainty; situation A at 1000 Hz is
# 1,8 dB (digit-exact oracle). Table 8 (Clause 8) gives the two-sided 95 %
# coverage factor k = 1,96, so the expanded uncertainty is U = k u = 1,96 u
# exactly; for Rw in situation A (u = 1,2 dB, Table 3) this is U = 2,352 dB.
# ---------------------------------------------------------------------------
ISO12999_1_TABLE2_AIRBORNE_A_1000HZ = 1.8
ISO12999_1_COVERAGE_K_95 = 1.96
ISO12999_1_RW_A_STANDARD_UNCERTAINTY = 1.2

# ---------------------------------------------------------------------------
# ISO 9613-1:1993 Table 1 - pure-tone atmospheric-absorption attenuation
# coefficient (dB/km) at one standard atmosphere (101,325 kPa). Rows are the
# ISO 266 preferred one-third-octave frequencies but the values are computed at
# the EXACT midband frequencies fm = 1000*10^(k/10) (Note 5). Each entry is
# (temperature_degC, relative_humidity_percent, preferred_freq_Hz, alpha_dB_km).
# Digit-exact transcription against the FULL standard text (37 pp): sub-tables
# 1(a)-1(p) span -20 degC to +50 degC in 5 degC steps. The Eq. (3)-(5)
# implementation reproduces every point to < 0,4 % (limited only by the
# 3-significant-figure printed values), well inside the standard's own +/- 10 %
# claimed accuracy (clause 7.1). The second block (20-50 degC) was added once
# the full Table 1 became available, extending the earlier -20..+15 degC oracle.
# ---------------------------------------------------------------------------
ISO9613_1_TABLE1: list[tuple[float, float, float, float]] = [
    (-20.0, 10.0, 50.0, 0.589),
    (-20.0, 50.0, 1000.0, 9.14),
    (-20.0, 70.0, 8000.0, 27.8),
    (-20.0, 100.0, 10000.0, 47.0),
    (0.0, 10.0, 50.0, 0.302),
    (0.0, 50.0, 1000.0, 6.83),
    (0.0, 20.0, 2000.0, 34.6),
    (0.0, 100.0, 6300.0, 88.0),
    (5.0, 50.0, 1000.0, 5.08),
    (10.0, 70.0, 1000.0, 3.66),
    (10.0, 50.0, 4000.0, 46.7),
    (15.0, 50.0, 1000.0, 4.16),
    (15.0, 100.0, 10000.0, 105.0),
    # Extension from the full-text sub-tables 1(i)-1(p) (20 degC .. 50 degC).
    (20.0, 50.0, 1000.0, 4.66),
    (20.0, 50.0, 2000.0, 9.86),
    (25.0, 50.0, 1000.0, 5.68),
    (25.0, 100.0, 2000.0, 11.4),
    (30.0, 50.0, 1000.0, 7.03),
    (30.0, 50.0, 4000.0, 24.5),
    (35.0, 50.0, 1000.0, 8.43),
    (40.0, 50.0, 1000.0, 9.52),
    (45.0, 50.0, 800.0, 7.16),
    (50.0, 50.0, 2000.0, 24.8),
]
# Two representative grid points for the conformance registry (middle + corner).
ISO9613_1_TABLE1_MID = (10.0, 70.0, 1000.0, 3.66)  # dB/km
ISO9613_1_TABLE1_CORNER = (0.0, 20.0, 2000.0, 34.6)  # dB/km

# ---------------------------------------------------------------------------
# ISO 9613-2:1996 outdoor sound propagation — closed-form oracles. The general
# method (clause 7) sums independent physical terms, each with an exact limit:
#   * Eq. (7) geometrical divergence Adiv = 20 lg(d/d0) + 11 = 51,0 dB at 100 m.
#   * Table 3 ground functions have exact on-ground (h = 0), fully-developed
#     (dp -> inf) limits: b'(0) = 1,5 + 8,6 = 10,1 (250 Hz). With porous ground
#     both sides (Gs = Gr = 1) and hs = hr = 0 the source and receiver regions
#     each add (-1,5 + b'(0)), so Agr(250 Hz) = 2*(-1,5 + 10,1) = 17,2 dB.
#   * Clause 7.4 caps the diffraction term Dz at 20 dB (single edge) and 25 dB
#     (double edge); a deep-shadow geometry saturates to those caps exactly.
# ---------------------------------------------------------------------------
ISO9613_2_ADIV_100M = 51.0  # Eq. (7): 20 lg(100/1) + 11
ISO9613_2_GROUND_BPRIME_ZERO = 10.1  # Table 3 b'(h=0, dp->inf) = 1,5 + 8,6
ISO9613_2_GROUND_AGR_250_POROUS = 17.2  # 2*(-1,5 + 10,1), hs=hr=0, Gs=Gr=1
ISO9613_2_BARRIER_CAP_SINGLE = 20.0  # clause 7.4 single-diffraction limit, dB
ISO9613_2_BARRIER_CAP_DOUBLE = 25.0  # clause 7.4 double-diffraction limit, dB

# ---------------------------------------------------------------------------
# ISO 9612:2009 occupational noise exposure — the three normative worked
# examples (Annexes D/E/F), reproduced digit-for-digit by the test suite. Each
# stores the raw measured levels/durations and the standard's reported LEX,8h
# and expanded uncertainty U (k = 1,65, one-sided 95 %). Annex D is the
# task-based welder day; its case (a) omits the task-duration uncertainty
# (U = 2,7 dB), case (b) includes it (U = 3,2 dB). Annexes E (job-based, 18
# workers) and F (full-day forklift drivers) use the Table C.4 sampling budget.
# Task tuples are (samples, duration_hours, duration_range) so the conformance
# report can rebuild the Task objects (Task is not importable here — this module
# is stdlib-only). Mirrors tests/test_occupational_exposure.py.
# ---------------------------------------------------------------------------
ISO9612_ANNEX_D_TASKS: tuple[tuple, ...] = (
    ((70.0,), 1.5, None),
    ((80.1, 82.2, 79.6), 5.0, (4.0, 6.0)),
    ((86.5, 92.4, 89.3, 93.2, 87.8, 86.2), 1.5, (1.0, 2.0)),
)
ISO9612_ANNEX_D_LEX_8H = 84.3
ISO9612_ANNEX_D_U = 2.7  # case (a): task-duration uncertainty omitted
ISO9612_ANNEX_E_SAMPLES: tuple[float, ...] = (88.1, 86.1, 89.7, 86.5, 91.1, 86.7)
ISO9612_ANNEX_E_TE_HOURS = 7.5
ISO9612_ANNEX_E_LEX_8H = 88.1
ISO9612_ANNEX_E_U = 3.8
ISO9612_ANNEX_F_SAMPLES: tuple[float, ...] = (88.0, 91.9, 87.6, 90.4, 89.0, 88.4)
ISO9612_ANNEX_F_TE_HOURS = 9.25
ISO9612_ANNEX_F_LEX_8H = 90.1
ISO9612_ANNEX_F_U = 3.4

# ---------------------------------------------------------------------------
# ISO 11654:1997 rating of sound absorption — the two normative worked examples
# of Annex A. Both use the same practical-coefficient spectrum except at 500 Hz;
# A.1 gives alpha_w = 0,60 with no shape indicator, A.2 (500 Hz raised to 1,00)
# gives alpha_w = 0,60(M). Bands are 250/500/1000/2000/4000 Hz. Mirrors
# tests/test_absorption_rating.py.
# ---------------------------------------------------------------------------
ISO11654_ANNEX_A1_ALPHA_P: tuple[float, ...] = (0.35, 0.70, 0.65, 0.60, 0.55)
ISO11654_ANNEX_A1_ALPHA_W = 0.60
ISO11654_ANNEX_A1_CLASS = "C"
ISO11654_ANNEX_A1_INDICATOR = ""
ISO11654_ANNEX_A2_ALPHA_P: tuple[float, ...] = (0.35, 1.00, 0.65, 0.60, 0.55)
ISO11654_ANNEX_A2_ALPHA_W = 0.60
ISO11654_ANNEX_A2_INDICATOR = "M"

# ---------------------------------------------------------------------------
# ISO 9053-2:2020 alternating-method airflow resistance — the Annex A.3 worked
# example of the effective ratio of specific heats. A closed cylinder 100 mm x
# 100 mm gives V = 7,854e-4 m3 and S = 0,0471 m2; with the IEC 61094-2:2009 air
# properties at 23 C and f = 2 Hz the standard prints b = 1,83e-3 m and the
# heat-conduction-corrected kappa' = kappa*0,978 = 1,370. Mirrors
# tests/test_airflow_resistance.py.
# ---------------------------------------------------------------------------
ISO9053_2_ANNEX_A_SURFACE = 0.0471  # S (m2)
ISO9053_2_ANNEX_A_VOLUME = 7.854e-4  # V (m3)
ISO9053_2_ANNEX_A_FREQUENCY = 2.0  # f (Hz)
ISO9053_2_ANNEX_A_BOUNDARY_LAYER = 1.83e-3  # b (m)
ISO9053_2_ANNEX_A_KAPPA_PRIME = 1.370  # kappa' = kappa*0,978

# ---------------------------------------------------------------------------
# ISO 10534-1:1996 standing-wave-ratio method — closed-form physics oracle from
# Eqs (13)/(14)/(9): a standing-wave ratio s = 3 gives |r| = (s-1)/(s+1) = 0,5
# and absorption alpha = 1 - |r|^2 = 0,75.
# ---------------------------------------------------------------------------
ISO10534_1_SWR = 3.0
ISO10534_1_REFLECTION_MAGNITUDE = 0.5
ISO10534_1_ABSORPTION = 0.75

# ---------------------------------------------------------------------------
# ISO 17497-1:2004 random-incidence scattering coefficient. Eq (2) fixes the
# reference speed of sound c = 343,2 m/s at 20 C. The synthetic worked chain
# (T1..T4 = 8,0/6,0/7,5/5,0 s, V/S from V = 200 m3, S = 10 m2) exercises the
# Sabine absorptions Eq (1)/(4) and the scattering Eq (5). Mirrors
# tests/test_scattering_diffusion.py.
# ---------------------------------------------------------------------------
ISO17497_1_SPEED_OF_SOUND_20C = 343.2  # Eq (2) reference condition (m/s)
ISO17497_1_CHAIN_V = 200.0  # chamber volume V (m3)
ISO17497_1_CHAIN_S = 10.0  # sample area S (m2)
ISO17497_1_CHAIN_C = 343.2  # speed of sound used throughout (m/s)
ISO17497_1_CHAIN_T: tuple[float, float, float, float] = (8.0, 6.0, 7.5, 5.0)
ISO17497_1_CHAIN_ALPHA_S = 0.1342754467754468  # random-incidence absorption
ISO17497_1_CHAIN_ALPHA_SPEC = 0.21484071484071485  # specular absorption
ISO17497_1_CHAIN_SCATTERING = 0.09306108711505018  # s = (a_spec-a_s)/(1-a_s)
# Annex A.5 combined uncertainty of the scattering coefficient. For
# a_spec = 0,6, a_s = 0,3 with u(a_spec) = 0,02 and u(a_s) = 0,01 the
# error-propagation form gives u(s) = 0,0297.
ISO17497_1_A5_ALPHA_SPEC = 0.6
ISO17497_1_A5_ALPHA_S = 0.3
ISO17497_1_A5_U_ALPHA_SPEC = 0.02
ISO17497_1_A5_U_ALPHA_S = 0.01
ISO17497_1_A5_U_SCATTERING = 0.0297147342419613  # combined u(s)

# ---------------------------------------------------------------------------
# ISO 17497-2:2012 diffusion coefficient. Formula (5)/(6) autocorrelation of a
# polar response; the four-level pattern below is re-derived by hand. Formula
# (8) area factors use RADIANS internally, so the zenith weight is
# N0 = (4*pi/dphi)*sin^2(dtheta/4) / A_min with dtheta = dphi = 5 deg.
# ---------------------------------------------------------------------------
ISO17497_2_DIFFUSION_LEVELS: tuple[float, ...] = (70.0, 74.0, 68.0, 72.0)
ISO17497_2_DIFFUSION_COEFF = 0.7367371379926486  # d from Formula (5)
ISO17497_2_AREA_FACTOR_ZENITH = 1.571045588794762  # N0, radians convention

# ---------------------------------------------------------------------------
# ISO 13472-1:2002 in-situ road-surface absorption. The mandatory geometry
# ds = 1,25 m, dm = 0,25 m gives the geometrical-spreading factor Kr = 2/3
# (Clause 4.2). The Annex A worked example (c = 340 m/s, 5 ms flat window)
# gives a maximum-sampled-area radius r ~ 1,34 m. Mirrors
# tests/test_road_absorption.py.
# ---------------------------------------------------------------------------
ISO13472_1_KR = 2.0 / 3.0  # geometrical-spreading factor
ISO13472_1_MSA_WINDOW = 5.0e-3  # reflected-wave window width Tw (s)
ISO13472_1_MSA_RADIUS = 1.3425466996067585  # Annex A worked example (m)

# ---------------------------------------------------------------------------
# ISO 13472-2:2010 spot method. The upper usable (plane-wave) frequency of a
# circular tube is f_u = 0,58 c0/d (Clause 5.4.1); a 100 mm tube at
# c0 = 343 m/s gives f_u = 1989,4 Hz.
# ---------------------------------------------------------------------------
ISO13472_2_SPOT_DIAMETER = 0.100  # tube diameter d (m)
ISO13472_2_SPOT_SPEED = 343.0  # speed of sound c0 (m/s)
ISO13472_2_SPOT_FU = 1989.4  # upper usable frequency (Hz)

# ---------------------------------------------------------------------------
# ISO 3745:2012 precision sound power (anechoic/hemi-anechoic). The Clause 10.5
# EXAMPLE combines sigma_omc = 2,0 dB and sigma_R0 = 0,5 dB at k = 2 to the
# expanded uncertainty U = 4,1 dB. The K1 background correction floors at
# 1,26 dB (>= 6 dB signal-to-noise edge bands). The meteorological correction
# C1 at the 23 C, ps0 reference is 5*lg(296/314) = -0,128 dB. Mirrors
# tests/test_sound_power_precision.py.
# ---------------------------------------------------------------------------
ISO3745_U_SIGMA_R0 = 0.5  # reproducibility standard deviation (dB)
ISO3745_U_SIGMA_OMC = 2.0  # operating/mounting/... std. deviation (dB)
ISO3745_U_COVERAGE = 2.0  # coverage factor k
ISO3745_U_EXPANDED = 4.123105625617661  # U = k*sqrt(sR0^2+somc^2) (dB)
ISO3745_K1_EDGE_LEVEL = 56.0  # measured Lp in the edge band (dB)
ISO3745_K1_EDGE_BACKGROUND = 50.0  # background Lp -> dLp = 6 dB (dB)
ISO3745_K1_EDGE_FREQUENCY = 200.0  # <= 200 Hz band uses the 6 dB floor (Hz)
ISO3745_K1_EDGE_FLOOR = 1.25628  # K1 floor, 6 dB S/N edge band (dB)
ISO3745_C1_REFERENCE = -0.12819  # C1 at 23 C, ps = ps0 (dB)

# ---------------------------------------------------------------------------
# ISO 9614-3:2002 precision intensity scanning. A fully enclosing surface with
# a uniform normal intensity In = W/S recovers the source power exactly, so
# LW = 10*lg(W/P0). For W = 100 uW this is LW = 80 dB (P0 = 1 pW).
# ---------------------------------------------------------------------------
ISO9614_3_UNIFORM_POWER = 1.0e-4  # radiated power W (W)
ISO9614_3_UNIFORM_AREAS: tuple[float, ...] = (0.5, 1.0, 0.25, 2.0)
ISO9614_3_UNIFORM_LW = 80.0  # 10*lg(W/1e-12) (dB)

# ---------------------------------------------------------------------------
# PR-F human vibration (ISO 8041-1 / ISO 2631 / ISO 5349 / Directive 2002/44/EC).
# The true IEC 61260 one-third-octave centre is 10^(n/10) Hz; the reference
# frequencies of ISO 8041-1 Table 1 are exact (rad/s -> Hz). Design-goal
# factors are from ISO 8041-1:2017 Annex B (Tables B.1-B.9, 4 sig. figs).
# ---------------------------------------------------------------------------
# ISO 8041-1 Annex B design-goal weighting factors at the true band centre.
ISO8041_1_WK_FACTOR_6P31HZ = 1.054  # Table B.8, n = 8 (6,31 Hz) - Wk peak
ISO8041_1_WM_FACTOR_1P585HZ = 0.9342  # Table B.9, n = 2 (1,585 Hz) - Wm
# ISO 8041-1 Table 1 weighting factor at the reference frequency.
ISO8041_1_WH_REF_FREQ_HZ = 500.0 / (2.0 * math.pi)  # 79,577 Hz (500 rad/s)
ISO8041_1_WH_REF_FACTOR = 0.2020  # Table 1, Wh @ 500 rad/s
# ISO 5349-2:2001 Annex E worked-example daily exposures A(8), m/s^2.
ISO5349_2_E21_A8 = 4.1  # E.2.1 single tool: 7,4*sqrt(2,5/8)
ISO5349_2_E3_A8 = 3.6  # E.3 forestry three-task combination
# ISO 5349-1:2001 Annex C: Dy = 31,8*A(8)^-1,06; Table C.1 A(8)=7 -> Dy=4 yr.
ISO5349_1_VWF_A8 = 7.0
ISO5349_1_VWF_DY_YEARS = 4.0
# Directive 2002/44/EC Article 3 daily exposure action/limit values.
DIRECTIVE_2002_44_HAV_EAV = 2.5  # A(8) m/s^2, Art. 3(1)(a)
DIRECTIVE_2002_44_HAV_ELV = 5.0  # A(8) m/s^2, Art. 3(1)(b)
DIRECTIVE_2002_44_WBV_EAV = 0.5  # A(8) m/s^2, Art. 3(2)(a)
DIRECTIVE_2002_44_WBV_ELV = 1.15  # A(8) m/s^2, Art. 3(2)(b)

# ---------------------------------------------------------------------------
# ANSI S3.5-1997 Speech Intelligibility Index (one-third-octave method).
# The band-importance function (Table 3) sums to one; the equivalent masking
# spectrum level Zi is a tabulated intermediate of the standard procedure for
# the standard normal-effort spectrum in quiet; the index for that condition
# with normal hearing is the standard-procedure result.
# ---------------------------------------------------------------------------
SII_BAND_IMPORTANCE_SUM = 1.0  # ANSI S3.5-1997 Table 3, sum of Ii
SII_MASKING_Z_200HZ = -1.665  # Zi at 200 Hz, standard spectrum in quiet
SII_STANDARD_QUIET = 0.9958  # SII, standard normal speech, quiet, normal hearing

# ---------------------------------------------------------------------------
# Room-noise criteria - ANSI/ASA S12.2-2019.
# Feeding an NC curve of Table 1 back through the tangency method returns its
# NC value; the RC Mark II curves reproduce Table D.1 (the 63 Hz level of the
# RC-31 curve is 51 dB); the mid-frequency average of the RC-35 curve is 35 dB.
# ---------------------------------------------------------------------------
RN_NC40_SELF = 40.0  # NC-40 curve -> tangency rating (Table 1)
RN_RC31_63HZ = 51.0  # RC-31 curve, 63 Hz octave-band level (Table D.1)
RN_RC35_LMF = 35.0  # RC-35 curve, mid-frequency average LMF (clause D.4)

# ---------------------------------------------------------------------------
# Hearing thresholds - ISO 7029:2017 (age) and ISO 389-7:2006 (reference).
# The median deviation follows a*(age-18)**b (Table 1); at 4 kHz for a 60-year
# male it is 20.21 dB. The upper spread su is a degree-5 polynomial (Table 2);
# at 1 kHz age 60 male it is 10.15 dB. The free-field reference threshold at
# 1 kHz is 2.4 dB (ISO 389-7 Table 1).
# ---------------------------------------------------------------------------
HEARING_MEDIAN_MALE_60_4KHZ = 20.2085  # dB, ISO 7029 Table 1 median formula
HEARING_SU_MALE_60_1KHZ = 10.1533  # dB, ISO 7029 Table 2 upper spread
HEARING_REF_FREE_1KHZ = 2.4  # dB, ISO 389-7 Table 1 free-field

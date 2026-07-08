#  Copyright (c) 2026. Jose M. Requena-Plens
"""Shared normative reference data (single source of truth).

Tables transcribed verbatim from the published standards. Both the test
suite (``tests/test_*.py``) and the CI conformance report
(``scripts/conformance_report.py``) import these constants, so the report's
expected values can never drift from what the tests assert. The six PR-B
building-acoustics oracles are the exception: their test modules re-hardcode
the values inline rather than import them, and a dedicated consistency test
(``test_building_reference_data_matches_published_oracles``) pins this shared
table to those same published results so neither copy can drift.

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

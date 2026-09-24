#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Hearing: thresholds, noise-induced loss and occupational exposure.

The listener rather than the sound. ISO 389-7 fixes the reference
threshold of hearing, ISO 7029 the statistical distribution of thresholds
with age, ISO 1999 the noise-induced permanent threshold shift those
thresholds acquire under exposure, and ISO 9612 the exposure itself -
the task-based, job-based and full-day strategies of Annexes D, E and F,
each with the LEX,8h and the uncertainty its worked example prints.
"""

from __future__ import annotations

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
# is stdlib-only). Mirrors tests/hearing/test_occupational_exposure.py.
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
# Hearing thresholds - ISO 7029:2017 (age) and ISO 389-7:2005 (reference).
# The median deviation follows a*(age-18)**b (Table 1); at 4 kHz for a 60-year
# male it is 20.21 dB. The upper spread su is a degree-5 polynomial (Table 2);
# at 1 kHz age 60 male it is 10.15 dB. The free-field reference threshold at
# 1 kHz is 2.4 dB (ISO 389-7 Table 1).
# ---------------------------------------------------------------------------
ISO7029_MEDIAN_MALE_60_4KHZ = 20.2085  # dB, ISO 7029 Table 1 median formula
ISO7029_SU_MALE_60_1KHZ = 10.1533  # dB, ISO 7029 Table 2 upper spread
ISO389_7_REF_FREE_1KHZ = 2.4  # dB, ISO 389-7 Table 1 free-field

# ---------------------------------------------------------------------------
# ISO 389-1:1998, the audiometric zero of a supra-aural earphone. Read from
# the rendered printed pages: Table 1 (folio 8) for the two named models on
# an IEC 60303 coupler, Table 2 (folio 10) for any other supra-aural earphone
# on an IEC 60318 artificial ear. Both tables round to the nearest half
# decibel, which their notes say in as many words.
# ---------------------------------------------------------------------------
ISO389_1_DT48_1KHZ = 8.0  # dB, Table 1, Beyer DT 48 with a flat cushion
ISO389_1_TDH39_1KHZ = 7.0  # dB, Table 1, Telephonics TDH 39 with MX 41/AR
ISO389_1_TDH39_125HZ = 45.0  # dB, Table 1, the low end of the same column
ISO389_1_OTHER_6300HZ = 21.0  # dB, Table 2, the peak of the artificial ear

# ---------------------------------------------------------------------------
# Noise-induced hearing loss - ISO 1999:2013, Annex D worked examples (dB).
# Table D.2 (L_EX,8h = 90 dB, 20 years) at 4 kHz: median NIPTS = 13 dB and the
# most-susceptible tenth (fractile 0.9) = 18 dB. Table D.4 (100 dB, 40 years)
# at 3 kHz, fractile 0.9 = 60 dB.
# ---------------------------------------------------------------------------
ISO1999_N50_4K_90_20 = 13.0  # median NIPTS, 4 kHz, 90 dB, 20 yr
ISO1999_N10_4K_90_20 = 18.0  # worst-10 % NIPTS, 4 kHz, 90 dB, 20 yr
ISO1999_N10_3K_100_40 = 60.0  # worst-10 % NIPTS, 3 kHz, 100 dB, 40 yr

# ---------------------------------------------------------------------------
# Noise-induced hearing loss - ISO 1999:2013, Annex C worked example (risk of
# noise-induced hearing loss and disability). A highly screened male
# population aged 50 exposed to L_EX,8h = 90 dB for 30 years, assessed on the
# 1/2/4 kHz frequency combination, at the percentage Q = 10 % (the
# most-susceptible tenth; the library fractile 0.9).
#
# The annex's own printed inputs are the Table A.3 age-associated thresholds
# H = 14, 21 and 36 dB and the Table D.2 shifts N = 0, 9 and 19 dB. The
# quantities pinned here are the results the annex derives from them:
#   C.5   the 4 kHz shift after the Formula (1) compression,
#         19 - 36 x 19 / 120 = 13,3 dB;
#   C.8   the 1/2/4 kHz mean shift, (0 + 9 + 13,3) / 3 = 7,4 dB;
#   C.3   the 1/2/4 kHz mean age threshold, (14 + 21 + 36) / 3 = 23,7 dB;
#   C.11  the combined threshold, 23,7 + 7,4 = 31,1 dB.
# The annex applies the compression only where it matters: "when (H + N) <
# 40 dB, the NIPTS can be taken directly from Table D.2", so of these three
# bands only 4 kHz (36 + 19 dB) is compressed.
# ---------------------------------------------------------------------------
ISO1999_ANNEX_C_H = (14.0, 21.0, 36.0)  # Table A.3 H, male 50 yr, Q = 10 %
ISO1999_ANNEX_C_N = (0.0, 9.0, 19.0)  # Table D.2 NIPTS, 90 dB, 30 yr, Q = 10 %
ISO1999_ANNEX_C_N_4K_COMPRESSED = 13.3  # C.5, dB
ISO1999_ANNEX_C_COMPRESSION_FENCE = 40.0  # H + N above which the annex compresses
ISO1999_ANNEX_C_N_MEAN = 7.4  # C.8, dB
ISO1999_ANNEX_C_H_MEAN = 23.7  # C.3, dB
ISO1999_ANNEX_C_HTLAN = 31.1  # C.11, dB

# ---------------------------------------------------------------------------
# ISO 4869-2:2018 - the effective A-weighted level behind a hearing protector.
# Four informative annexes carry one worked example between them, all built on
# the same 16-subject attenuation grid of Table A.1, and every one of them
# reproduces from the printed inputs:
#   A   m_f and s_f per band, exactly. The annex's own APV row is the
#       difference of the ROUNDED m_f and s_f it displays, which differs from
#       Formula (1) applied to the data by 0,1 dB at 250 Hz, 500 Hz and
#       4 kHz; both readings are pinned below.
#   B   the octave-band method: the per-band net levels and L'p,A84 = 81,4 dB,
#       81 dB after rounding.
#   C   the HML method: all 16 x 8 PNR values, all 16 H/M/L triples, the three
#       means, the three standard deviations, H84/M84/L84 = 24/18/13 dB, and
#       the application PNR84 = 22,5 dB -> L'p,A84 = 81,5 dB -> 82 dB.
#   D   the SNR method: all 16 SNRj, SNRm, SNRs, SNR84 = 21 dB and both of its
#       applications, which land on 82 dB.
#
# Table C.1 reprints Table 2 and disagrees with it in two cells; Table 2 is
# the one that reproduces Annex C. See docs/ERRATA.md.
# ---------------------------------------------------------------------------
#: Table A.1: sound attenuation in dB, one row per test subject, over the
#: eight octave bands from 63 Hz to 8 kHz.
ISO4869_2_ATTENUATION: list[list[float]] = [
    [4.0, 8.0, 13.0, 18.0, 20.0, 30.0, 35.0, 30.0],
    [6.0, 12.0, 16.0, 21.0, 29.0, 35.0, 47.0, 35.0],
    [10.0, 16.0, 17.0, 23.0, 25.0, 32.0, 48.0, 37.0],
    [3.0, 7.0, 12.0, 18.0, 20.0, 25.0, 33.0, 30.0],
    [8.0, 10.0, 16.0, 16.0, 25.0, 27.0, 43.0, 32.0],
    [4.0, 7.0, 10.0, 15.0, 19.0, 32.0, 35.0, 31.0],
    [5.0, 5.0, 9.0, 16.0, 20.0, 25.0, 30.0, 28.0],
    [15.0, 15.0, 21.0, 26.0, 25.0, 38.0, 46.0, 38.0],
    [5.0, 6.0, 10.0, 13.0, 19.0, 22.0, 29.0, 28.0],
    [9.0, 9.0, 10.0, 19.0, 20.0, 27.0, 37.0, 31.0],
    [9.0, 16.0, 18.0, 24.0, 25.0, 35.0, 44.0, 39.0],
    [5.0, 6.0, 11.0, 12.0, 17.0, 20.0, 28.0, 28.0],
    [7.0, 10.0, 17.0, 22.0, 25.0, 35.0, 41.0, 44.0],
    [6.0, 8.0, 16.0, 18.0, 19.0, 19.0, 30.0, 33.0],
    [10.0, 12.0, 17.0, 25.0, 28.0, 33.0, 45.0, 40.0],
    [12.0, 13.0, 17.0, 27.0, 29.0, 38.0, 49.0, 41.0],
]
#: Table A.1, the printed ``m_f`` and ``s_f`` rows, in dB.
ISO4869_2_MEAN = [7.4, 10.0, 14.4, 19.6, 22.8, 29.6, 38.8, 34.1]
ISO4869_2_STANDARD_DEVIATION = [3.3, 3.6, 3.6, 4.6, 4.0, 6.2, 7.4, 5.2]
#: Table A.1, the printed ``APV_f84`` row, which subtracts the two rows above
#: as displayed rather than as computed.
ISO4869_2_APV84_PRINTED = [4.1, 6.4, 10.8, 15.0, 18.8, 23.4, 31.4, 28.9]

#: Annex B: the octave-band levels of the example noise, in dB, and the
#: frequency weighting A the annex prints beside them.
ISO4869_2_ANNEX_B_NOISE = [75.0, 84.0, 86.0, 88.0, 97.0, 99.0, 97.0, 96.0]
ISO4869_2_ANNEX_B_A_WEIGHTING = [-26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0, -1.1]
#: Annex B: the last row of Table B.1, ``Lp + A - APV`` per band, in dB.
ISO4869_2_ANNEX_B_NET = [44.7, 61.5, 66.6, 69.8, 78.2, 76.8, 66.6, 66.0]
ISO4869_2_ANNEX_B_EFFECTIVE = 81.4  # dB, before rounding
ISO4869_2_ANNEX_B_REPORTED = 81  # dB, after rounding
ISO4869_2_ANNEX_B_LPA = 104.0  # dB, the A-weighted level of the same noise
ISO4869_2_ANNEX_B_LPC = 103.0  # dB, its C-weighted level (Annex C.2, D.2)

#: Annex C, Table C.2: the printed ``Hj``, ``Mj`` and ``Lj`` per subject, dB.
ISO4869_2_ANNEX_C_H = [
    27.8,
    34.5,
    32.1,
    26.0,
    28.7,
    27.2,
    25.6,
    33.8,
    23.5,
    27.1,
    33.1,
    21.6,
    33.0,
    21.6,
    34.2,
    36.7,
]
ISO4869_2_ANNEX_C_M = [
    20.1,
    24.8,
    24.9,
    19.6,
    21.2,
    18.0,
    18.0,
    26.5,
    16.9,
    19.4,
    25.5,
    15.9,
    24.3,
    19.1,
    26.2,
    27.1,
]
ISO4869_2_ANNEX_C_L = [
    14.7,
    18.2,
    20.2,
    13.9,
    16.4,
    12.5,
    11.4,
    22.2,
    11.9,
    13.5,
    20.9,
    12.0,
    17.7,
    15.6,
    19.0,
    19.5,
]
#: Annex C, the sixth row of Table C.2: ``PNRj6`` per subject, in dB. The two
#: cells Table C.1 misprints are the ones this row is sensitive to.
ISO4869_2_ANNEX_C_PNR_NOISE6 = [
    18.5,
    22.7,
    23.5,
    17.9,
    19.7,
    16.3,
    15.9,
    25.4,
    15.3,
    17.6,
    24.2,
    14.7,
    22.3,
    18.2,
    23.9,
    24.7,
]
ISO4869_2_ANNEX_C_MEANS = (29.2, 21.7, 16.2)  # Hm, Mm, Lm in dB
ISO4869_2_ANNEX_C_DEVIATIONS = (4.8, 3.8, 3.5)  # Hs, Ms, Ls in dB
ISO4869_2_ANNEX_C_HML84 = (24, 18, 13)  # H84, M84, L84 in dB
ISO4869_2_ANNEX_C_PNR84 = 22.5  # dB
ISO4869_2_ANNEX_C_EFFECTIVE = 81.5  # dB, before rounding
ISO4869_2_ANNEX_C_REPORTED = 82  # dB, after rounding

#: Annex D, Table D.2: the printed ``SNRj`` per subject, in dB.
ISO4869_2_ANNEX_D_SNR = [
    23.1,
    27.7,
    28.0,
    22.3,
    24.1,
    21.2,
    20.7,
    29.8,
    19.7,
    22.4,
    28.7,
    18.8,
    27.2,
    21.4,
    28.9,
    29.9,
]
ISO4869_2_ANNEX_D_MEAN = 24.6  # SNRm, dB
ISO4869_2_ANNEX_D_DEVIATION = 3.9  # SNRs, dB
ISO4869_2_ANNEX_D_SNR84 = 21  # dB
ISO4869_2_ANNEX_D_REPORTED = 82  # dB, both applications

#: Table C.1's two misprinted cells, at 250 Hz and 500 Hz of the sixth
#: reference noise. Kept so the test that tells the two tables apart names
#: what it is refusing.
ISO4869_2_TABLE_C1_NOISE6 = [82.0, 89.4, 93.5, 95.6, 93.0, 90.1, 83.0]

# ---------------------------------------------------------------------------
# ISO 4869-1:2018 - real-ear attenuation at threshold, its uncertainty and the
# Annex B significance test. Read on the printed pages: Tables A.2 and A.3 on
# folios 12-13 (PDF pages 18-19), B.1.1 on folio 14 (PDF 20), Table B.1 on
# folio 15 (PDF 21), Table B.2 and the text of B.2 on folio 16 (PDF 22), and
# Table 1 on folio 4 (PDF 10).
#   A.2, B.2  every combined and expanded cell is the root sum of squares of
#             the three printed components, times 2 for U95, rounded last;
#   A.3       all 28 derived cells (mean, sigma, u = sigma/4, U95 = 2u) come
#             from the 16 x 7 grid at full precision, as its NOTE 2 says;
#   B.1       test 2 is printed rounded only, so its U95 and mean are the
#             printed ones. The root-sum-of-squares row reproduces all seven
#             cells and the verdict is "significant at 8 kHz only"; the
#             difference row agrees within 0,1 dB: six cells round to the
#             print, and 8 kHz is 0,056 dB off (3,944 against the printed
#             4,0) because m2 is printed rounded.
#   B.1.1, B.2  the minimum differences are sqrt(2) times the ROUNDED U95 of
#             the tables, which the text writes out ("sqrt(2) x 2,3 dB =
#             3,3 dB"): 3,3 and 2,3 dB within, 9,3 and 6,9 dB between.
# ---------------------------------------------------------------------------
#: The seven test signals of 4.1, in hertz; 63 Hz is optional and not used by
#: the worked example.
ISO4869_1_FREQUENCIES = [125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0]

#: Table A.3: earmuff attenuation in dB, one row per test subject, 125 Hz to
#: 8 kHz. Also test 1 of Table B.1.
ISO4869_1_TABLE_A3: list[list[float]] = [
    [9.6, 13.5, 27.5, 32.4, 35.2, 29.1, 28.5],
    [14.1, 20.2, 25.8, 32.0, 28.9, 35.3, 35.7],
    [21.8, 27.8, 28.3, 46.6, 37.4, 40.1, 38.7],
    [18.5, 22.2, 36.5, 44.8, 39.1, 30.6, 33.5],
    [15.6, 21.9, 31.8, 42.5, 38.9, 38.3, 37.1],
    [18.7, 28.6, 31.3, 39.0, 35.6, 35.3, 29.4],
    [23.0, 26.5, 34.0, 41.3, 40.8, 38.7, 35.9],
    [17.3, 21.7, 25.0, 30.7, 38.6, 37.9, 40.8],
    [19.4, 19.6, 28.0, 36.6, 40.7, 34.9, 39.4],
    [11.6, 20.4, 22.6, 38.0, 39.2, 33.9, 30.3],
    [20.5, 21.8, 29.2, 40.7, 36.2, 35.7, 38.4],
    [18.3, 19.6, 26.2, 34.6, 32.7, 34.9, 26.6],
    [15.1, 17.5, 30.1, 39.0, 39.4, 38.2, 39.5],
    [21.7, 20.8, 28.3, 39.5, 38.1, 40.0, 38.4],
    [15.9, 17.8, 26.0, 40.6, 38.0, 40.2, 37.2],
    [11.8, 18.4, 29.6, 37.2, 40.8, 36.0, 29.9],
]
#: Table A.3, the four derived rows as printed, in dB.
ISO4869_1_TABLE_A3_MEAN = [17.1, 21.1, 28.8, 38.5, 37.5, 36.2, 35.0]
ISO4869_1_TABLE_A3_SIGMA = [3.9, 3.9, 3.5, 4.5, 3.2, 3.2, 4.6]
ISO4869_1_TABLE_A3_U = [1.0, 1.0, 0.9, 1.1, 0.8, 0.8, 1.1]
ISO4869_1_TABLE_A3_U95 = [2.0, 1.9, 1.7, 2.2, 1.6, 1.6, 2.3]

#: Table B.1, test 2, as printed (the individual data are not given), in dB.
ISO4869_1_TABLE_B1_MEAN_2 = [16.8, 21.0, 28.3, 38.2, 35.5, 34.6, 38.9]
ISO4869_1_TABLE_B1_SIGMA_2 = [3.1, 2.4, 2.7, 3.1, 3.0, 3.3, 4.9]
ISO4869_1_TABLE_B1_U95_2 = [1.6, 1.2, 1.4, 1.5, 1.5, 1.7, 2.5]
#: Table B.1, the last two rows: |m1 - m2| and sqrt(U95,1^2 + U95,2^2), in dB.
ISO4869_1_TABLE_B1_DIFFERENCE = [0.3, 0.1, 0.5, 0.3, 2.0, 1.6, 4.0]
ISO4869_1_TABLE_B1_CRITERION = [2.5, 2.3, 2.2, 2.7, 2.2, 2.3, 3.4]
#: B.1.2: "not significantly different in the frequency range 125 Hz to
#: 4 000 Hz. At 8 000 Hz a significant difference is seen."
ISO4869_1_TABLE_B1_SIGNIFICANT = [8000.0]

#: Tables A.2 and B.2: the three components (u_meth, u_eq, u_env) in dB, then
#: the printed combined u and expanded U95, keyed by protector, one tuple per
#: column (<250 Hz, 250 Hz up to 4 kHz, >4 kHz).
ISO4869_1_TABLE_A2: dict[str, list[tuple[float, float, float, float, float]]] = {
    "earplug": [
        (1.5, 0.2, 0.5, 1.6, 3.2),
        (1.0, 0.2, 0.5, 1.1, 2.3),
        (1.5, 0.2, 0.5, 1.6, 3.2),
    ],
    "earmuff": [
        (1.0, 0.2, 0.5, 1.1, 2.3),
        (0.6, 0.2, 0.5, 0.8, 1.6),
        (1.0, 0.2, 0.5, 1.1, 2.3),
    ],
}
ISO4869_1_TABLE_B2: dict[str, list[tuple[float, float, float, float, float]]] = {
    "earplug": [
        (4.0, 0.3, 0.8, 4.1, 8.2),
        (3.2, 0.3, 0.8, 3.3, 6.6),
        (3.2, 0.3, 0.8, 3.3, 6.6),
    ],
    "earmuff": [
        (1.8, 0.3, 0.8, 2.0, 4.0),
        (2.3, 0.3, 0.8, 2.5, 4.9),
        (3.2, 0.3, 0.8, 3.3, 6.6),
    ],
}

#: B.1.1 and B.2: the minimum differences for 250 Hz to 4 kHz, in dB, keyed
#: (table, protector): the rounded U95 the text reads and the difference it
#: prints from it.
ISO4869_1_MINIMUM_DIFFERENCES: dict[tuple[str, str], tuple[float, float]] = {
    ("A.2", "earplug"): (2.3, 3.3),
    ("A.2", "earmuff"): (1.6, 2.3),
    ("B.2", "earplug"): (6.6, 9.3),
    ("B.2", "earmuff"): (4.9, 6.9),
}

#: Table 1: (lowest free-field rejection, allowable field variation) in dB,
#: from 25 dB and up down to 10 dB; below 10 dB "Microphone not suitable".
ISO4869_1_TABLE_1: list[tuple[float, float]] = [
    (25.0, 20.0),
    (20.0, 15.0),
    (15.0, 10.0),
    (10.0, 5.0),
]

# ---------------------------------------------------------------------------
# ISO 4869-6:2019 - total attenuation of active noise reduction earmuffs.
#
# Two oracles. The printed pages: Table A.2 on folio 9 (PDF page 15) and the
# 16 x 8 active insertion loss of Table A.3 on folio 10 (PDF page 16), with its
# mean, sigma, u and U95 rows. And the calculation workbook ISO publishes for
# 5.5 at https://standards.iso.org/iso/4869/-6/ed-1/en/ (file
# "ISO_4869-6_-_Calculation_example.xlsx", sheet "Tabelle1", retrieved
# 2026-09-23, 50 349 bytes), which the standard names in 5.5 as the example of
# its detailed computations. Every value below was read from the workbook's
# stored cells, as stored: its inputs (the MIRE levels of both ears in both
# modes, and the REAT of ISO 4869-1) and the result of the steps of its chain.
# The MIRE levels carry one decimal except subject 16 from 100 Hz up (rows 44,
# 45, 84 and 85, columns G to AA), which the workbook stores with two (48.29,
# 72.09, ...) in both modes alike, so its insertion loss has one decimal too.
# The workbook rounds some steps to one decimal with ROUND(., 1) and leaves
# the others as they come:
#   rows 134-149  the ear with the lower active insertion loss, 5.5 b),
#                 IF(left < right, left, right), not rounded;
#   rows 182-197  the REAT interpolated LINEARLY IN HERTZ between the nominal
#                 octave frequencies, extended with the end segments, 5.5 a),
#                 rounded;
#   rows 206-221  their sum, 5.5 c), a plain sum of the two rounded or
#                 one-decimal rows above, not rounded again;
#   rows 230-245  Formula (1), 5.5 d), rounded;
#   rows 247-249  mean and STDEV of the octave totals, each rounded, and
#                 APV84 as their difference, 5.5 e).
# The stored values of the unrounded rows carry binary noise
# (17.300000000000004); they are transcribed to their one decimal.
# The lower-ear rows 134-149 at the octave frequencies ARE Table A.3 of the
# standard, cell for cell. The grids are kept one workbook row per line, the
# way the sheet lays them out, and parsed on import.
# ---------------------------------------------------------------------------


def _workbook_rows(text: str) -> list[list[float]]:
    """One list of floats per non-empty line of a whitespace-separated block."""
    return [[float(v) for v in line.split()] for line in text.strip().splitlines()]


def _workbook_ears(text: str) -> list[list[list[float]]]:
    """Consecutive line pairs (left ear, then right) grouped per subject."""
    rows = _workbook_rows(text)
    return [[rows[i], rows[i + 1]] for i in range(0, len(rows), 2)]


#: The one-third-octave bands of the workbook, 50 Hz to 10 kHz, in hertz.
ISO4869_6_THIRD_OCTAVES = [
    50.0,
    63.0,
    80.0,
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
]

#: Workbook rows 54-85: MIRE level at the ear in the passive mode, dB, one
#: [left ear, right ear] pair per subject, 50 Hz to 10 kHz.
ISO4869_6_WORKBOOK_PASSIVE_LEVELS = _workbook_ears(
    """
 72.3  73.8  72.1  72.1  75.0  74.4  74.4  73.9  73.3  71.2  68.5  64.8  60.4  56.3  58.4  58.7  58.0  48.4  41.0  45.0  52.6  52.2  44.9  44.1
 68.7  72.1  72.8  73.0  73.9  74.2  72.2  70.4  70.0  67.0  64.3  60.3  52.8  53.7  53.9  54.4  57.4  54.5  48.3  44.1  46.6  43.4  36.5  37.2
 73.1  74.2  72.6  71.8  75.1  74.8  74.8  73.9  73.3  70.5  67.4  63.9  59.0  56.2  58.2  57.5  60.8  56.9  52.1  50.1  48.8  47.8  40.5  49.4
 69.3  72.7  72.4  72.7  73.6  73.7  71.8  70.6  70.2  67.4  64.0  54.5  52.8  52.0  53.2  52.8  55.6  53.1  47.7  44.2  44.6  37.7  33.6  41.9
 73.8  74.1  72.4  71.7  75.3  73.8  74.9  74.2  74.0  70.8  68.2  65.4  57.4  55.9  57.6  57.7  59.6  54.7  51.2  46.3  46.5  43.1  43.3  50.1
 71.7  73.7  72.3  70.9  72.4  72.2  71.8  70.7  70.3  66.9  64.5  59.8  56.9  55.6  55.4  53.6  55.1  50.2  43.3  43.0  46.8  41.5  34.6  37.5
 72.9  73.9  72.9  72.4  75.0  73.8  74.5  74.5  73.4  70.3  68.2  64.3  61.2  58.9  59.3  58.0  59.9  54.7  50.3  44.8  49.0  45.8  39.9  43.0
 70.3  73.0  71.7  70.8  72.0  71.8  71.1  71.0  70.4  67.4  64.9  59.5  57.1  56.5  57.7  56.9  56.6  50.9  45.6  47.4  50.8  41.7  35.4  40.8
 72.7  73.5  72.1  72.0  74.3  74.1  74.2  73.7  72.6  69.5  67.6  64.0  60.1  56.3  57.3  55.4  54.5  51.9  46.3  43.4  48.0  42.0  33.1  39.8
 69.3  72.2  70.8  69.6  70.4  71.9  70.3  70.9  70.1  67.3  64.8  60.3  57.0  55.3  56.4  55.3  53.2  47.3  42.8  39.4  44.8  40.0  33.4  36.9
 72.4  72.9  71.5  71.5  73.4  73.7  72.8  71.5  71.1  67.8  66.2  62.4  58.0  54.6  55.8  53.8  53.7  51.7  46.2  41.2  47.2  45.0  33.7  41.3
 69.4  71.7  71.5  71.8  73.0  73.6  69.6  67.8  67.7  64.2  62.1  57.4  50.2  52.1  53.6  53.8  56.1  50.4  44.9  37.8  42.2  41.1  37.3  48.3
 71.6  73.5  71.0  70.0  73.3  73.6  74.4  73.4  72.2  71.1  68.0  67.6  58.5  51.5  52.6  50.5  48.9  47.2  47.3  51.0  52.5  47.2  43.7  48.7
 69.7  74.3  71.9  70.5  71.9  74.0  73.0  72.0  70.5  68.1  64.6  62.3  52.9  51.5  50.9  47.5  48.0  43.5  41.1  43.7  39.5  37.3  41.5  43.8
 72.2  73.9  71.9  70.7  73.4  74.0  74.6  73.8  73.3  71.1  68.1  66.1  60.1  52.2  50.3  48.5  51.0  46.6  43.9  41.2  45.0  42.4  38.9  42.8
 69.6  73.9  72.5  71.4  73.1  74.6  72.5  70.4  71.0  68.4  65.0  59.2  53.7  51.8  51.6  51.3  54.0  51.9  46.7  44.8  44.6  35.3  44.2  47.0
 71.8  73.3  71.6  71.6  72.6  74.3  73.4  72.2  71.7  65.8  64.9  59.5  54.1  51.1  51.6  49.5  53.4  51.1  42.9  37.6  42.4  41.7  36.6  43.2
 69.9  73.3  74.0  74.2  71.3  73.8  71.3  70.0  69.9  66.1  64.1  53.7  52.0  52.3  52.9  53.4  53.4  47.7  43.5  39.7  41.9  32.0  35.8  40.9
 72.1  73.2  71.6  70.8  74.5  74.9  76.1  74.5  74.1  70.0  68.0  64.5  57.3  49.2  50.3  48.6  50.1  48.3  44.7  45.7  48.1  40.5  39.2  41.4
 69.5  72.9  72.6  72.9  73.5  74.7  72.5  70.4  71.0  68.4  66.3  58.3  55.2  54.4  55.1  57.1  55.7  48.3  43.5  45.2  54.9  49.0  44.4  44.7
 74.3  74.6  72.9  72.2  75.4  74.8  76.9  75.8  76.1  70.9  69.3  66.1  55.5  52.0  53.3  53.0  57.2  54.4  51.4  48.8  52.9  42.2  40.4  38.7
 72.9  74.9  73.5  72.1  71.2  73.2  73.8  73.7  73.1  69.5  67.4  62.9  53.4  53.0  51.2  52.0  55.7  53.2  49.1  44.5  45.4  38.4  38.5  42.0
 74.2  75.2  74.2  73.7  76.5  75.7  77.1  75.6  76.3  72.7  70.2  67.1  58.7  57.2  59.3  58.7  59.6  55.2  49.5  49.5  47.2  43.7  44.8  49.3
 73.1  75.8  74.5  73.6  73.1  74.2  73.7  73.4  72.4  69.6  67.4  62.6  57.4  55.7  56.0  57.5  59.5  51.8  46.4  46.6  42.5  40.1  44.0  46.8
 73.9  74.7  73.3  73.2  76.2  75.2  76.6  75.2  75.6  71.0  69.0  64.2  59.3  55.4  56.8  56.3  58.8  54.3  47.2  45.7  54.5  48.3  34.5  40.4
 74.3  77.2  75.8  74.6  74.1  74.2  73.2  71.8  71.4  68.3  66.3  61.9  56.4  57.2  56.5  56.9  60.5  55.3  48.5  43.9  48.1  48.1  35.2  39.4
 71.9  72.4  71.0  71.0  74.7  74.9  75.6  73.5  72.9  69.1  67.4  63.8  58.7  52.2  53.4  52.1  52.9  49.4  45.9  48.1  50.1  44.4  38.9  42.1
 72.3  74.6  74.4  74.7  75.5  76.7  75.0  73.1  73.4  69.8  67.9  63.5  57.9  56.9  55.9  55.9  56.8  50.6  46.3  45.3  55.7  47.3  45.1  44.4
 75.1  77.0  74.5  73.5  77.0  76.0  77.4  77.1  78.0  71.9  70.0  65.6  59.2  53.5  56.4  56.2  54.5  48.0  44.7  46.7  52.4  44.7  36.4  42.6
 71.8  76.4  74.0  72.6  72.6  74.7  74.3  72.5  72.5  69.7  67.8  63.9  55.7  53.9  54.4  53.8  50.5  44.5  43.8  46.7  47.1  40.5  31.9  37.9
 73.6  75.3  73.3  72.09  74.99  73.19  75.19  73.79  72.79  68.39  67.19  62.59  56.69  53.09  55.09  55.59  58.19  53.79  48.39  44.49  45.59  42.39  38.99  38.29
 69.8  74.1  72.7  71.59  71.39  71.09  71.09  70.19  70.09  67.29  65.69  59.49  55.79  54.69  55.79  55.99  56.09  47.49  43.59  44.99  47.09  40.09  37.39  43.09
"""
)

#: Workbook rows 14-45: MIRE level at the ear in the active mode, dB, likewise.
ISO4869_6_WORKBOOK_ACTIVE_LEVELS = _workbook_ears(
    """
 53.3  53.3  50.9  48.8  51.1  49.6  50.5  51.6  56.3  59.1  63.3  65.5  65.9  60.3  59.5  58.0  58.2  54.9  45.4  46.0  52.8  52.0  45.9  41.3
 51.4  53.7  52.2  49.4  49.8  49.2  48.6  48.8  52.8  54.6  59.0  58.7  58.5  58.2  55.9  54.3  57.2  57.2  51.1  45.4  46.2  42.8  36.4  37.3
 53.9  53.3  50.6  48.6  50.7  49.3  50.1  51.1  55.6  57.7  61.7  63.1  65.8  61.7  60.6  58.2  60.0  56.4  50.2  48.8  49.2  49.1  42.4  48.7
 51.8  53.3  52.5  51.0  50.6  49.8  47.9  48.9  52.6  54.4  56.7  52.3  59.4  58.4  55.8  54.0  56.0  54.7  48.5  43.4  42.7  35.1  33.4  39.8
 56.8  54.4  51.2  49.7  52.2  49.2  51.2  53.4  56.8  59.2  64.6  67.4  64.4  60.1  59.5  57.6  59.8  57.9  51.7  46.1  46.2  44.1  42.6  48.6
 51.6  52.1  49.5  47.2  47.9  46.0  47.1  49.0  53.3  55.3  60.3  59.0  61.9  59.4  57.2  54.2  58.0  56.4  46.1  41.9  46.2  41.3  35.2  36.9
 55.5  54.1  51.6  48.5  50.1  49.0  52.0  54.4  57.5  60.0  66.0  66.1  67.2  62.1  60.6  57.8  58.3  56.0  50.0  44.7  48.8  45.6  38.6  41.9
 51.1  52.5  50.4  48.4  48.9  49.5  50.5  52.3  55.8  57.7  61.6  62.1  63.4  61.4  60.2  58.3  57.1  53.8  46.7  47.6  50.5  41.6  35.2  39.6
 53.7  53.0  50.1  48.7  49.4  49.4  50.7  52.6  56.2  58.9  64.5  65.5  66.0  59.4  58.9  55.8  55.5  56.8  49.8  42.8  47.8  42.6  32.8  39.4
 49.8  51.6  49.0  46.5  45.9  47.4  48.0  50.7  53.9  56.1  60.4  60.8  62.8  59.7  57.8  56.1  56.1  55.0  48.6  40.8  44.8  40.6  32.7  37.6
 52.6  52.2  49.7  47.7  48.1  47.9  48.5  50.5  54.7  57.2  62.3  64.1  64.2  58.9  57.8  55.0  56.3  56.8  50.1  41.6  46.6  45.1  33.9  40.9
 51.7  52.9  51.1  48.8  48.6  48.3  45.3  47.0  50.9  52.3  57.1  56.2  56.0  56.2  54.9  52.9  57.7  54.5  47.6  38.2  41.9  41.0  36.5  48.0
 51.6  51.8  48.2  46.8  48.9  49.5  50.2  51.2  54.9  58.6  63.3  67.4  64.0  56.0  54.4  52.0  52.9  54.1  52.1  52.3  53.6  48.9  44.0  49.1
 46.9  50.9  47.8  45.5  45.7  46.8  45.8  47.2  51.8  54.9  58.6  58.7  57.1  56.7  53.3  48.9  53.1  52.2  47.7  45.2  39.6  37.2  40.9  43.2
 51.6  52.0  49.1  46.1  47.5  47.3  47.5  48.5  52.6  55.3  59.3  60.7  63.4  61.0  57.9  52.6  54.1  52.8  52.2  46.0  47.1  43.0  39.6  44.7
 49.5  53.4  51.3  50.0  50.4  49.9  47.4  46.1  51.3  52.9  56.1  52.7  56.6  58.5  54.2  51.5  55.1  53.9  48.4  45.9  43.2  33.7  40.8  46.3
 47.4  48.9  47.2  47.2  46.7  47.2  47.2  49.0  53.4  52.9  59.5  58.4  60.3  56.6  53.7  51.4  56.2  54.3  47.4  38.1  42.4  42.4  37.6  41.9
 47.0  50.4  51.1  51.3  48.1  49.8  47.7  49.3  52.7  54.4  58.2  53.6  59.7  58.8  55.9  54.7  55.1  51.6  44.9  40.1  41.7  31.9  34.6  39.8
 46.8  47.9  46.3  45.5  48.6  48.0  49.0  48.7  54.0  54.5  59.2  59.2  60.7  57.6  55.1  51.3  55.0  53.3  48.9  48.3  48.4  40.9  39.8  41.8
 47.6  51.0  50.7  51.0  50.6  50.4  48.1  47.3  53.2  54.1  57.5  52.0  57.7  58.3  54.1  53.9  56.0  51.1  46.0  47.7  55.2  49.3  45.1  44.7
 50.6  50.9  49.2  48.5  50.8  50.5  53.9  55.0  59.4  59.8  65.9  68.3  63.5  57.4  56.3  54.7  57.3  54.2  51.0  49.0  52.6  44.0  41.0  38.7
 48.6  50.6  49.2  47.8  46.2  47.0  48.9  50.3  55.2  57.0  62.2  61.5  60.8  59.4  54.2  53.2  55.5  53.2  49.6  44.8  45.6  37.8  39.0  41.6
 52.2  53.2  52.2  51.7  52.6  51.6  54.3  55.3  60.2  61.6  67.2  68.9  64.9  61.0  61.2  58.8  59.1  59.3  53.2  50.5  47.2  43.6  43.9  47.9
 49.5  52.2  50.9  50.0  47.1  47.5  48.5  50.5  54.4  56.7  62.1  61.4  62.3  59.9  57.8  57.3  60.3  57.8  51.6  47.0  42.7  39.1  43.7  46.1
 50.1  50.9  49.5  49.4  51.1  50.3  52.4  53.3  58.6  59.2  64.4  65.4  66.1  61.0  59.1  57.5  58.9  55.7  49.8  46.0  52.5  46.0  34.6  40.7
 51.1  54.0  52.6  51.4  49.8  50.3  49.7  50.9  54.6  56.3  61.4  60.7  61.9  61.4  58.2  57.2  59.9  56.8  51.7  44.4  47.3  48.0  36.2  38.7
 48.1  48.6  47.2  47.2  48.9  48.8  50.1  50.1  55.3  55.7  61.5  62.2  63.0  57.4  55.7  53.3  56.0  56.7  49.4  49.7  49.8  45.7  38.5  41.5
 50.8  53.1  52.9  53.2  52.0  52.1  49.9  49.8  54.2  55.9  61.0  60.5  61.4  60.5  56.4  54.2  56.4  56.8  50.3  48.9  55.7  47.1  46.7  43.7
 50.8  52.7  50.2  49.2  52.8  51.4  53.5  54.6  59.4  59.2  65.8  65.8  66.0  57.7  58.0  56.2  55.3  52.1  45.6  47.5  52.1  44.0  35.4  41.4
 47.3  51.9  49.5  48.1  47.3  49.2  49.8  49.9  54.8  57.3  62.8  61.9  62.9  60.2  56.6  54.8  53.0  51.4  46.9  47.6  47.1  40.6  32.4  37.3
 49.8  51.5  49.5  48.29  50.09  46.39  49.79  51.09  54.89  55.99  63.39  62.49  63.39  57.39  57.19  55.79  58.09  57.39  50.29  44.19  45.39  42.29  37.99  36.59
 46.0  50.3  48.9  47.79  45.99  46.89  48.79  49.49  54.19  56.39  61.19  59.89  62.39  59.49  57.69  56.69  56.59  53.79  46.99  45.29  45.99  39.09  37.19  41.79
"""
)

#: Workbook rows 158-173: the REAT of the same sixteen subjects, dB, at the
#: octave frequencies 63 Hz to 8 kHz.
ISO4869_6_WORKBOOK_REAT = _workbook_rows(
    """
 11.7  15.7   8.6  10.7  25.6  22.7  43.0  38.0
 12.7  20.3  15.7  13.4  23.0  24.3  36.7  42.0
 21.0  22.7  17.7  18.0  27.4  31.0  36.3  45.0
 21.6  22.0  21.0  13.4  24.7  30.3  36.3  42.3
 10.6  10.0  11.7  16.0  24.6  23.4  38.0  42.4
 12.3  13.3  12.3  17.6  30.0  22.6  39.3  43.3
 11.0  10.0  10.0  13.6  24.3  25.4  36.3  37.4
 16.0  12.0  11.3  13.0  28.7  25.7  38.0  35.0
 11.4  11.6  11.0  13.7  29.3  24.3  42.7  37.6
 12.7  12.0   8.0   9.0  32.7  25.6  37.0  41.0
 14.0  10.3   7.7  15.0  21.0  22.7  33.3  33.0
 19.3  18.3  15.6  16.3  21.0  26.4  32.7  31.0
 13.7  15.4  12.6  13.4  22.0  19.0  40.0  33.3
 13.0  15.3   6.7  12.0  23.0  28.7  40.4  38.0
 16.7  21.6  18.4  18.0  33.7  37.7  57.0  50.6
 10.7  15.0  10.0  11.7  25.0  22.0  32.0  38.7
"""
)

#: Workbook rows 134-149: the lower-ear active insertion loss, dB, 5.5 b).
ISO4869_6_WORKBOOK_LOWER_EAR = _workbook_rows(
    """
 17.3  18.4  20.6  23.3  23.9  24.8  23.6  21.6  17.0  12.1   5.2  -0.7  -5.7  -4.5  -2.0   0.1  -0.2  -6.5  -4.4  -1.3  -0.2   0.2  -1.0  -0.1
 17.5  19.4  19.9  21.7  23.0  23.9  23.9  21.7  17.6  12.8   5.7   0.8  -6.8  -6.4  -2.6  -1.2  -0.4  -1.6  -0.8   0.8  -0.4  -1.3  -1.9   0.7
 17.0  19.7  21.2  22.0  23.1  24.6  23.7  20.8  17.0  11.6   3.6  -2.0  -7.0  -4.2  -1.9  -0.6  -2.9  -6.2  -2.8   0.2   0.3  -1.0  -0.6   0.6
 17.4  19.8  21.3  22.4  23.1  22.3  20.6  18.7  14.6   9.7   2.2  -2.6  -6.3  -4.9  -2.5  -1.4  -0.5  -2.9  -1.1  -0.2   0.2   0.1   0.2   1.1
 19.0  20.5  21.8  23.1  24.5  24.5  22.3  20.2  16.2  10.6   3.1  -1.5  -5.9  -4.4  -1.6  -0.8  -2.9  -7.7  -5.8  -1.4   0.0  -0.6   0.3  -0.7
 17.7  18.8  20.4  23.0  24.4  25.3  24.3  20.8  16.4  10.6   3.9  -1.7  -6.2  -4.3  -2.0  -1.2  -2.6  -5.1  -3.9  -0.4   0.3  -0.1  -0.2   0.3
 20.0  21.7  22.8  23.2  24.4  24.1  24.2  22.2  17.3  12.5   4.7   0.2  -5.5  -5.2  -2.4  -1.5  -5.1  -8.7  -6.6  -1.5  -1.1  -1.7  -0.3  -0.4
 20.1  20.5  21.2  21.4  22.7  24.7  25.1  24.3  19.7  15.5   8.8   5.4  -3.3  -8.8  -7.6  -4.1  -3.1  -6.2  -8.3  -4.8  -2.1  -0.6  -0.7  -1.9
 22.9  22.9  22.9  22.9  23.2  24.0  23.6  20.7  17.2  11.7   5.4   0.1  -7.7  -6.5  -3.0  -1.9  -2.8  -3.9  -4.5  -0.5   0.0  -0.7  -1.0   1.1
 21.9  21.9  21.9  21.9  22.9  24.3  24.4  23.1  17.8  14.3   8.8   5.3  -3.4  -8.4  -4.8  -2.7  -4.9  -5.0  -4.2  -2.6  -0.3  -0.4  -0.7  -0.4
 23.7  23.7  23.7  23.7  24.6  24.3  23.0  20.8  16.7  11.1   3.4  -2.2  -8.0  -6.4  -3.0  -1.7  -0.1   0.0  -0.5  -0.3  -0.2  -1.8  -0.6   0.0
 22.0  22.0  22.0  22.0  23.9  24.1  22.8  20.3  16.1  11.1   3.0  -1.8  -6.2  -4.2  -1.9  -0.1  -0.8  -6.0  -5.2  -1.0  -0.2   0.1   0.3   0.7
 23.2  23.2  23.2  23.2  24.3  23.9  23.5  20.9  16.8  11.8   4.6  -1.2  -6.8  -5.6  -2.3  -1.2  -0.1  -1.5  -3.2  -0.5   0.8   0.1  -1.0  -0.3
 21.5  21.5  21.5  21.5  23.5  24.6  25.1  23.3  17.6  13.4   5.9   1.6  -4.3  -5.2  -2.3  -1.2  -3.1  -7.3  -4.0  -3.6   0.0  -1.3  -1.6   0.6
 24.3  24.3  24.3  24.3  24.2  24.6  23.9  22.5  17.7  12.4   4.2  -0.2  -7.2  -6.3  -2.2  -1.0  -2.5  -6.9  -3.1  -0.9   0.0  -0.1  -0.5   0.6
 23.8  23.8  23.8  23.8  24.9  24.2  22.3  20.7  15.9  10.9   3.8  -0.4  -6.7  -4.8  -2.1  -0.7  -0.5  -6.3  -3.4  -0.3   0.2   0.1   0.2   1.3
"""
)

#: Workbook rows 182-197: the REAT in one-third-octave bands, interpolated,
#: extrapolated and rounded to 0,1 dB, 5.5 a).
ISO4869_6_WORKBOOK_REAT_THIRDS = _workbook_rows(
    """
 10.9  11.7  12.8  14.1  15.7  13.7  11.4   8.6   9.1   9.9  10.7  14.6  19.6  25.6  24.9  23.9  22.7  27.8  34.4  43.0  41.8  40.1  38.0  35.5
 11.1  12.7  14.8  17.2  20.3  19.0  17.5  15.7  15.1  14.3  13.4  15.9  19.2  23.0  23.3  23.8  24.3  27.4  31.4  36.7  38.0  39.7  42.0  44.7
 20.6  21.0  21.5  22.0  22.7  21.3  19.7  17.7  17.8  17.9  18.0  20.4  23.6  27.4  28.3  29.6  31.0  32.3  34.0  36.3  38.5  41.3  45.0  49.4
 21.5  21.6  21.7  21.8  22.0  21.7  21.4  21.0  19.0  16.4  13.4  16.3  20.2  24.7  26.1  28.1  30.3  31.8  33.8  36.3  37.8  39.8  42.3  45.3
 10.7  10.6  10.4  10.2  10.0  10.5  11.0  11.7  12.8  14.3  16.0  18.2  21.2  24.6  24.3  23.9  23.4  27.1  31.8  38.0  39.1  40.5  42.4  44.6
 12.1  12.3  12.6  12.9  13.3  13.0  12.7  12.3  13.7  15.5  17.6  20.8  25.0  30.0  28.2  25.6  22.6  26.8  32.2  39.3  40.3  41.6  43.3  45.3
 11.2  11.0  10.7  10.4  10.0  10.0  10.0  10.0  10.9  12.2  13.6  16.4  20.0  24.3  24.6  25.0  25.4  28.1  31.7  36.3  36.6  36.9  37.4  38.0
 16.8  16.0  14.9  13.6  12.0  11.8  11.6  11.3  11.7  12.3  13.0  17.1  22.4  28.7  28.0  26.9  25.7  28.8  32.8  38.0  37.3  36.3  35.0  33.5
 11.4  11.4  11.5  11.5  11.6  11.4  11.2  11.0  11.7  12.6  13.7  17.8  23.1  29.3  28.1  26.3  24.3  28.9  34.9  42.7  41.4  39.8  37.6  35.1
 12.8  12.7  12.5  12.3  12.0  10.9   9.6   8.0   8.3   8.6   9.0  15.2  23.2  32.7  30.9  28.4  25.6  28.5  32.2  37.0  38.0  39.3  41.0  43.0
 14.8  14.0  13.0  11.8  10.3   9.6   8.7   7.7   9.6  12.1  15.0  16.6  18.6  21.0  21.4  22.0  22.7  25.4  28.8  33.3  33.2  33.1  33.0  32.9
 19.5  19.3  19.0  18.7  18.3  17.5  16.7  15.6  15.8  16.0  16.3  17.5  19.1  21.0  22.4  24.2  26.4  28.0  30.0  32.7  32.3  31.7  31.0  30.2
 13.3  13.7  14.2  14.7  15.4  14.6  13.7  12.6  12.8  13.1  13.4  15.6  18.6  22.0  21.3  20.2  19.0  24.3  31.1  40.0  38.3  36.1  33.3  30.0
 12.5  13.0  13.6  14.4  15.3  12.9  10.1   6.7   8.1   9.9  12.0  14.9  18.6  23.0  24.4  26.4  28.7  31.6  35.4  40.4  39.8  39.0  38.0  36.8
 15.7  16.7  18.0  19.6  21.6  20.7  19.7  18.4  18.3  18.2  18.0  22.1  27.4  33.7  34.7  36.1  37.7  42.5  48.8  57.0  55.4  53.3  50.6  47.4
  9.8  10.7  11.9  13.3  15.0  13.6  12.0  10.0  10.4  11.0  11.7  15.2  19.7  25.0  24.3  23.2  22.0  24.5  27.8  32.0  33.7  35.9  38.7  42.1
"""
)

#: Workbook rows 206-221: the total attenuation per one-third octave, dB, 5.5 c).
ISO4869_6_WORKBOOK_TOTAL_THIRDS = _workbook_rows(
    """
 28.2  30.1  33.4  37.4  39.6  38.5  35.0  30.2  26.1  22.0  15.9  13.9  13.9  21.1  22.9  24.0  22.5  21.3  30.0  41.7  41.6  40.3  37.0  35.4
 28.6  32.1  34.7  38.9  43.3  42.9  41.4  37.4  32.7  27.1  19.1  16.7  12.4  16.6  20.7  22.6  23.9  25.8  30.6  37.5  37.6  38.4  40.1  45.4
 37.6  40.7  42.7  44.0  45.8  45.9  43.4  38.5  34.8  29.5  21.6  18.4  16.6  23.2  26.4  29.0  28.1  26.1  31.2  36.5  38.8  40.3  44.4  50.0
 38.9  41.4  43.0  44.2  45.1  44.0  42.0  39.7  33.6  26.1  15.6  13.7  13.9  19.8  23.6  26.7  29.8  28.9  32.7  36.1  38.0  39.9  42.5  46.4
 29.7  31.1  32.2  33.3  34.5  35.0  33.3  31.9  29.0  24.9  19.1  16.7  15.3  20.2  22.7  23.1  20.5  19.4  26.0  36.6  39.1  39.9  42.7  43.9
 29.8  31.1  33.0  35.9  37.7  38.3  37.0  33.1  30.1  26.1  21.5  19.1  18.8  25.7  26.2  24.4  20.0  21.7  28.3  38.9  40.6  41.5  43.1  45.6
 31.2  32.7  33.5  33.6  34.4  34.1  34.2  32.2  28.2  24.7  18.3  16.6  14.5  19.1  22.2  23.5  20.3  19.4  25.1  34.8  35.5  35.2  37.1  37.6
 36.9  36.5  36.1  35.0  34.7  36.5  36.7  35.6  31.4  27.8  21.8  22.5  19.1  19.9  20.4  22.8  22.6  22.6  24.5  33.2  35.2  35.7  34.3  31.6
 34.3  34.3  34.4  34.4  34.8  35.4  34.8  31.7  28.9  24.3  19.1  17.9  15.4  22.8  25.1  24.4  21.5  25.0  30.4  42.2  41.4  39.1  36.6  36.2
 34.7  34.6  34.4  34.2  34.9  35.2  34.0  31.1  26.1  22.9  17.8  20.5  19.8  24.3  26.1  25.7  20.7  23.5  28.0  34.4  37.7  38.9  40.3  42.6
 38.5  37.7  36.7  35.5  34.9  33.9  31.7  28.5  26.3  23.2  18.4  14.4  10.6  14.6  18.4  20.3  22.6  25.4  28.3  33.0  33.0  31.3  32.4  32.9
 41.5  41.3  41.0  40.7  42.2  41.6  39.5  35.9  31.9  27.1  19.3  15.7  12.9  16.8  20.5  24.1  25.6  22.0  24.8  31.7  32.1  31.8  31.3  30.9
 36.5  36.9  37.4  37.9  39.7  38.5  37.2  33.5  29.6  24.9  18.0  14.4  11.8  16.4  19.0  19.0  18.9  22.8  27.9  39.5  39.1  36.2  32.3  29.7
 34.0  34.5  35.1  35.9  38.8  37.5  35.2  30.0  25.7  23.3  17.9  16.5  14.3  17.8  22.1  25.2  25.6  24.3  31.4  36.8  39.8  37.7  36.4  37.4
 40.0  41.0  42.3  43.9  45.8  45.3  43.6  40.9  36.0  30.6  22.2  21.9  20.2  27.4  32.5  35.1  35.2  35.6  45.7  56.1  55.4  53.2  50.1  48.0
 33.6  34.5  35.7  37.1  39.9  37.8  34.3  30.7  26.3  21.9  15.5  14.8  13.0  20.2  22.2  22.5  21.5  18.2  24.4  31.7  33.9  36.0  38.9  43.4
"""
)

#: Workbook rows 230-245: the octave-band total of Formula (1), rounded to
#: 0,1 dB, 5.5 d).
ISO4869_6_WORKBOOK_TOTAL_OCTAVES = _workbook_rows(
    """
 30.1  38.4  29.1  16.2  17.5  22.5  34.2  37.1
 31.1  41.2  35.8  19.3  15.3  23.9  33.9  40.4
 39.8  45.1  37.6  21.3  20.2  27.6  34.3  43.3
 40.8  44.4  36.9  16.2  17.3  28.3  35.0  42.2
 30.9  34.2  31.0  19.1  18.3  20.7  30.2  41.8
 31.1  37.2  32.6  21.4  22.2  21.7  32.5  43.1
 32.4  34.0  30.8  18.7  17.5  20.7  29.1  36.5
 36.5  35.3  33.9  23.3  19.8  22.7  28.4  33.5
 34.3  34.8  31.2  19.7  19.1  23.3  34.6  37.1
 34.6  34.7  29.2  19.9  22.6  22.8  31.5  40.3
 37.6  34.7  28.3  17.3  13.4  22.3  30.8  32.1
 41.3  41.5  34.7  18.7  15.7  23.6  28.1  31.3
 36.9  38.6  32.4  17.3  14.7  19.9  32.1  32.0
 34.5  37.2  28.8  18.4  17.0  25.0  34.6  37.1
 41.0  44.9  39.0  23.5  24.0  35.3  49.7  49.9
 34.5  38.1  29.2  16.5  16.6  20.3  28.0  38.5
"""
)

#: Workbook row 247: ROUND(AVERAGE(.), 1) of the octave totals, dB.
ISO4869_6_WORKBOOK_MEAN = [35.5, 38.4, 32.5, 19.2, 18.2, 23.8, 32.9, 38.5]

#: Workbook row 248: ROUND(STDEV(.), 1) of the octave totals, dB.
ISO4869_6_WORKBOOK_SD = [3.8, 3.9, 3.4, 2.3, 3.0, 3.9, 5.1, 5.0]

#: Workbook row 249: APV84, the rounded mean less the rounded SD, dB.
ISO4869_6_WORKBOOK_APV84 = [31.7, 34.5, 29.1, 16.9, 15.2, 19.9, 27.8, 33.5]

#: Table A.3 (folio 10, PDF page 16): the active insertion loss of the ear
#: with the lower value, dB, one line per subject, 63 Hz to 8 kHz.
ISO4869_6_TABLE_A3 = _workbook_rows(
    """
 18.4  23.9  21.6   5.2  -4.5  -0.2  -1.3  -1.0
 19.4  23.0  21.7   5.7  -6.4  -0.4   0.8  -1.9
 19.7  23.1  20.8   3.6  -4.2  -2.9   0.2  -0.6
 19.8  23.1  18.7   2.2  -4.9  -0.5  -0.2   0.2
 20.5  24.5  20.2   3.1  -4.4  -2.9  -1.4   0.3
 18.8  24.4  20.8   3.9  -4.3  -2.6  -0.4  -0.2
 21.7  24.4  22.2   4.7  -5.2  -5.1  -1.5  -0.3
 20.5  22.7  24.3   8.8  -8.8  -3.1  -4.8  -0.7
 22.9  23.2  20.7   5.4  -6.5  -2.8  -0.5  -1.0
 21.9  22.9  23.1   8.8  -8.4  -4.9  -2.6  -0.7
 23.7  24.6  20.8   3.4  -6.4  -0.1  -0.3  -0.6
 22.0  23.9  20.3   3.0  -4.2  -0.8  -1.0   0.3
 23.2  24.3  20.9   4.6  -5.6  -0.1  -0.5  -1.0
 21.5  23.5  23.3   5.9  -5.2  -3.1  -3.6  -1.6
 24.3  24.2  22.5   4.2  -6.3  -2.5  -0.9  -0.5
 23.8  24.9  20.7   3.8  -4.8  -0.5  -0.3   0.2
"""
)

#: Table A.3, the four derived rows as printed, dB.
ISO4869_6_TABLE_A3_MEAN = [21.4, 23.8, 21.4, 4.8, -5.6, -2.0, -1.1, -0.6]
ISO4869_6_TABLE_A3_SIGMA = [1.9, 0.7, 1.4, 1.9, 1.4, 1.7, 1.4, 0.6]
ISO4869_6_TABLE_A3_U = [0.5, 0.2, 0.4, 0.5, 0.4, 0.4, 0.4, 0.2]
ISO4869_6_TABLE_A3_U95 = [1.0, 0.4, 0.8, 1.0, 0.8, 0.8, 0.8, 0.4]
#: The bands (indices, 63 Hz first) at which the printed u and U95 are NOT
#: sigma/4 and 2 sigma/4 of the sixteen printed rows at full precision: u at
#: 250 Hz, U95 at 63, 250, 500, 1 000, 4 000 and 8 000 Hz. Each row is the
#: formula on the ROUNDED row above it (1,4 / 4 = 0,35 -> 0,4; U95 = 2u as
#: printed); see docs/ERRATA.md.
ISO4869_6_TABLE_A3_U_ROUNDED_FROM_SIGMA = (2,)
ISO4869_6_TABLE_A3_U95_ROUNDED_FROM_U = (0, 2, 3, 4, 6, 7)

#: Table A.2 (folio 9, PDF page 15): (u_meth, u_eq, u_env) and the printed
#: combined u and expanded U95, dB.
ISO4869_6_TABLE_A2 = (0.6, 0.3, 0.4, 0.78, 1.6)

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The distribution of sound exposure levels of impulsive events (ISO 13474:2009).

Annex A of ISO 13474:2009 carries one worked example end to end: a TOW
anti-tank missile launcher heard at 3 020 m, its A-weighted single-event sound
exposure level under 27 excess-attenuation classes, the probability of each
class by day, by night and over 07:00 to 19:00, the probability density of
the classes, and the exceedance levels and long-term levels read from the
distribution once it has been spread for turbulence.

Every number was read on the rasterized page of BS ISO 13474:2009, which
reproduces ISO 13474:2009 (first edition, 2009-06-15) without modification:
Table A.3 on printed folio 32 (PDF page 40), Table A.4 on folio 33 (PDF page
41), the running text of Annex A on folio 34 (PDF page 42) and Figure A.3 on
folio 36 (PDF page 44).

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: Table A.3, printed folio 32 (PDF page 40): for each excess-attenuation class
#: ``n``, the A-weighted single-event sound exposure level at location A in dB,
#: and its probability of occurrence by day, by night and over the period from
#: 07:00 to 19:00, in that order. The three groups of Table A.2 are the rows 1
#: to 7, 8 to 18 and 19 to 27. The day cell of row 21 is printed "0,2042"
#: without the thin space of every other cell; the digits are the same.
ISO13474_TABLE_A3: tuple[tuple[int, float, float, float, float], ...] = (
    (1, 30.5, 0.0360, 0.0000, 0.0288),
    (2, 31.2, 0.0053, 0.0000, 0.0042),
    (3, 31.3, 0.0003, 0.0000, 0.0002),
    (4, 36.1, 0.0731, 0.0664, 0.0718),
    (5, 38.3, 0.0951, 0.0966, 0.0954),
    (6, 38.8, 0.0634, 0.0962, 0.0700),
    (7, 39.2, 0.0000, 0.0000, 0.0000),
    (8, 30.8, 0.2037, 0.1151, 0.1860),
    (9, 31.8, 0.1087, 0.0295, 0.0929),
    (10, 31.8, 0.0184, 0.0000, 0.0147),
    (11, 33.7, 0.0279, 0.0268, 0.0277),
    (12, 40.2, 0.0001, 0.0084, 0.0018),
    (13, 41.0, 0.0000, 0.0000, 0.0000),
    (14, 41.6, 0.0549, 0.0665, 0.0572),
    (15, 42.2, 0.0482, 0.0445, 0.0475),
    (16, 42.4, 0.0209, 0.0172, 0.0202),
    (17, 42.7, 0.0039, 0.0033, 0.0038),
    (18, 43.1, 0.0003, 0.0003, 0.0003),
    (19, 28.4, 0.0000, 0.0069, 0.0014),
    (20, 30.8, 0.0356, 0.0798, 0.0444),
    (21, 32.2, 0.2042, 0.2310, 0.2096),
    (22, 42.3, 0.0001, 0.0215, 0.0044),
    (23, 43.6, 0.0000, 0.0260, 0.0052),
    (24, 44.5, 0.0000, 0.0263, 0.0053),
    (25, 45.2, 0.0000, 0.0194, 0.0039),
    (26, 45.5, 0.0000, 0.0153, 0.0031),
    (27, 46.1, 0.0000, 0.0030, 0.0006),
)

#: Folio 31 (PDF page 39), the paragraph above Table A.3: the 07:00 to 19:00
#: probability is the average of the day and night probabilities "using, for
#: this location and period of interest (07:00 to 19:00), daytime and
#: night-time proportions equal to 80 % and 20 %, respectively".
ISO13474_ANNEX_A_DAY_FRACTION: float = 0.8
ISO13474_ANNEX_A_NIGHT_FRACTION: float = 0.2

#: Table A.4, printed folio 33 (PDF page 41): for each class ``m`` in order of
#: increasing level, the level in dB, its probability over 07:00 to 19:00, the
#: lower and upper class boundaries in dB and the probability density in 1/dB.
ISO13474_TABLE_A4: tuple[tuple[int, float, float, float, float, float], ...] = (
    (1, 28.4, 0.0014, 27.35, 29.45, 0.0007),
    (2, 30.5, 0.0288, 29.45, 30.65, 0.0240),
    (3, 30.8, 0.1860, 30.65, 30.80, 1.2399),
    (4, 30.8, 0.0444, 30.80, 31.00, 0.2222),
    (5, 31.2, 0.0042, 31.00, 31.25, 0.0170),
    (6, 31.3, 0.0002, 31.25, 31.55, 0.0008),
    (7, 31.8, 0.0929, 31.55, 31.80, 0.3714),
    (8, 31.8, 0.0147, 31.80, 32.00, 0.0736),
    (9, 32.2, 0.2096, 32.00, 32.95, 0.2206),
    (10, 33.7, 0.0277, 32.95, 34.90, 0.0142),
    (11, 36.1, 0.0718, 34.90, 37.20, 0.0312),
    (12, 38.3, 0.0954, 37.20, 38.55, 0.0707),
    (13, 38.8, 0.0700, 38.55, 39.00, 0.1555),
    (14, 39.2, 0.0000, 39.00, 39.70, 0.0000),
    (15, 40.2, 0.0018, 39.70, 40.60, 0.0020),
    (16, 41.0, 0.0000, 40.60, 41.30, 0.0000),
    (17, 41.6, 0.0572, 41.30, 41.90, 0.0954),
    (18, 42.2, 0.0475, 41.90, 42.25, 0.1356),
    (19, 42.3, 0.0044, 42.25, 42.35, 0.0438),
    (20, 42.4, 0.0202, 42.35, 42.55, 0.1008),
    (21, 42.7, 0.0038, 42.55, 42.90, 0.0108),
    (22, 43.1, 0.0003, 42.90, 43.35, 0.0007),
    (23, 43.6, 0.0052, 43.35, 44.05, 0.0074),
    (24, 44.5, 0.0053, 44.05, 44.85, 0.0066),
    (25, 45.2, 0.0039, 44.85, 45.35, 0.0078),
    (26, 45.5, 0.0031, 45.35, 45.80, 0.0068),
    (27, 46.1, 0.0006, 45.80, 46.40, 0.0010),
)

#: Folio 34 (PDF page 42): the standard deviation of the turbulent spread and
#: the number of subclasses each class of the example was divided into.
ISO13474_ANNEX_A_SIGMA_DB: float = 5.0
ISO13474_ANNEX_A_SUBCLASSES: int = 10

#: Folio 34 (PDF page 42): "In this example, the mean value was shifted by an
#: amount, Δµ, equal to 1,04 dB [from Equation (22)]". Equation (22) gives
#: σ² ln 10 / 20 = 2,878 dB at the 5 dB of the same paragraph; 1,04 dB is its
#: value at σ = 3 dB. The long-term level LT2 and the curve of Figure A.2 were
#: computed with 2,878 dB (see docs/ERRATA.md).
ISO13474_ANNEX_A_PRINTED_SHIFT_DB: float = 1.04

#: Figure A.3, printed folio 36 (PDF page 44): the exceedance levels printed
#: beside the cumulative curve, keyed by the percentage of events exceeding
#: them, in dB.
ISO13474_FIGURE_A3_EXCEEDANCE_DB: dict[int, float] = {
    95: 21.7,
    50: 31.5,
    10: 40.6,
    5: 43.2,
    1: 48.0,
}

#: Figure A.3: "LT1 = 37,0 dB" (Equation (7) with a single atmospheric
#: absorption class of probability 1) and "LT2 = 37,0 dB" (Equation (A.4)),
#: which folio 35 says agree when rounded to 0,1 dB.
ISO13474_FIGURE_A3_LT1_DB: float = 37.0
ISO13474_FIGURE_A3_LT2_DB: float = 37.0

#: Figures A.2 and A.3 (folios 35 and 36) draw their curves from x = 15 dB,
#: where the cumulative curve of Figure A.3 starts at exactly 1. The printed
#: exceedance levels are reproduced to the printed digit when the curve is
#: accumulated from this lower limit, 1 - ∫₁₅ˣ ρ*(x') dx', rather than as the
#: integral of Equation (24) to infinity (see docs/ERRATA.md).
ISO13474_FIGURE_A3_LOWER_LIMIT_DB: float = 15.0

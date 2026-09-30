#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Quality requirements for outdoor sound software (ISO 17534-1:2015).

Every number was read on the printed page of BS ISO 17534-1:2015, the UK
implementation of ISO 17534-1:2015 (first edition), whose pages carry the
ISO 17534-1:2015(E) text: Table B.2 on printed folio 16 (PDF page 24), and
Table C.1, Formulas (C.1) and (C.2) and the worked example that follows them
on printed folio 20 (PDF page 28). The worked TRC form of ISO/TR 17534-3:2015
(first edition), Table 69, was read on its printed page 53 (PDF page 59).
VDI 3723 Blatt 1:1993-05, the guideline DIN 45687:2006-05 names as the source
of Table C.1, was read on its Seite 7 and 8 (PDF pages 7 and 8; the copy is a
scan without a text layer).

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: Table C.1, printed folio 20 (PDF page 28): for each number ``N`` of random
#: sample values, the ranking positions ``R(q0,1)`` and ``R(q0,9)``, as
#: ``(N, R(q0,1), R(q0,9))``. The table is printed as two blocks side by side,
#: 20 to 35 on the left and 36 to 50 on the right.
ISO17534_1_TABLE_C1: tuple[tuple[int, int, int], ...] = (
    (20, 2, 19),
    (21, 2, 20),
    (22, 2, 21),
    (23, 2, 22),
    (24, 2, 23),
    (25, 2, 24),
    (26, 3, 24),
    (27, 3, 25),
    (28, 3, 26),
    (29, 3, 27),
    (30, 3, 28),
    (31, 3, 29),
    (32, 3, 30),
    (33, 3, 31),
    (34, 3, 32),
    (35, 3, 33),
    (36, 4, 33),
    (37, 4, 34),
    (38, 4, 35),
    (39, 4, 36),
    (40, 4, 37),
    (41, 4, 38),
    (42, 4, 39),
    (43, 4, 40),
    (44, 4, 41),
    (45, 4, 42),
    (46, 5, 42),
    (47, 5, 43),
    (48, 5, 44),
    (49, 5, 45),
    (50, 5, 46),
)

#: The EXAMPLE after Formula (C.2), printed folio 20 (PDF page 28): "The
#: following 25 random sample values (sorted in ascending order) resulted for
#: the level differences between two calculation variants", Delta L in dB, in
#: the order of their ranks R = 1 to 25. Printed as "-1,4", "-1", "1", "3" and
#: so on, to the decimals shown here.
ISO17534_1_EXAMPLE_DIFFERENCES_DB: tuple[float, ...] = (
    -1.4,
    -1.0,
    -0.4,
    0.8,
    1.0,
    1.0,
    1.0,
    1.2,
    1.4,
    1.4,
    1.4,
    1.6,
    1.8,
    1.8,
    2.0,
    2.0,
    2.0,
    2.2,
    2.2,
    2.4,
    2.6,
    2.8,
    2.8,
    3.0,
    3.4,
)

#: The same EXAMPLE: "With the number of random samples N = 25, the ranking
#: positions are as follows: R(q0,1) = 2 and R(q0,9) = 24."
ISO17534_1_EXAMPLE_RANKS: tuple[int, int] = (2, 24)

#: The same EXAMPLE: "As a result, the quantiles are as follows: q0,1 = -1 dB
#: and q0,9 = 3 dB", in dB.
ISO17534_1_EXAMPLE_QUANTILES_DB: tuple[float, float] = (-1.0, 3.0)

#: Table B.2, printed folio 16 (PDF page 24), the TRC form of the test case
#: "T XX": for each centre frequency of octave band and for the total
#: "(63 Hz up to 8 000 Hz)", the upper and lower limits of the certified
#: A-weighted result and the software calculation result, in dB, as
#: ``(row, upper, lower, result)``. Every row answers "yes" to "Result inside
#: tolerances" and carries "-" as its comment.
ISO17534_1_TABLE_B2: tuple[tuple[str, float, float, float], ...] = (
    ("63 Hz", 13.75, 13.65, 13.7),
    ("125 Hz", 19.55, 19.45, 19.5),
    ("250 Hz", 21.15, 21.05, 21.1),
    ("500 Hz", 26.05, 25.95, 26.0),
    ("1 000 Hz", 34.85, 34.75, 34.8),
    ("2 000 Hz", 37.05, 36.95, 37.0),
    ("4 000 Hz", 34.15, 34.05, 34.1),
    ("8 000 Hz", 21.65, 21.55, 21.6),
    ("Total", 40.65, 40.55, 40.60),
)

#: ISO/TR 17534-3:2015, Table 69, printed page 53 (PDF page 59): "Example of a
#: TRC-form based on test case 1", the A-weighted limits of the certified
#: results of T01 and an exemplary software calculation result, in dB, as
#: ``(row, upper, lower, result)``. Every row answers "yes" to "Result inside
#: tolerances", including 250 Hz, whose printed 31,0 lies below its lower
#: limit 31,05 (docs/ERRATA.md).
ISO17534_3_TABLE_69: tuple[tuple[str, float, float, float], ...] = (
    ("63 Hz", 13.75, 13.65, 13.7),
    ("125 Hz", 23.81, 23.71, 23.8),
    ("250 Hz", 31.15, 31.05, 31.0),
    ("500 Hz", 36.22, 36.12, 36.2),
    ("1 000 Hz", 39.00, 38.90, 38.9),
    ("2 000 Hz", 39.42, 39.32, 39.4),
    ("4 000 Hz", 36.52, 36.42, 36.5),
    ("8 000 Hz", 23.99, 23.89, 23.9),
    ("Total", 44.34, 44.24, 44.3),
)

#: VDI 3723 Blatt 1:1993-05, Tabelle 6, Seite 8 (PDF page 8): "Schätzung des
#: 90-%-Überschreitungspegels L_x;90", the ranking position ``k`` of the 90 %
#: exceedance level in a sample of ``n`` values sorted in ascending order, as
#: ``(n, k)`` for n = 20 to 50. DIN 45687 F.4 bases R(q0,1) of Table C.1 on
#: this column. The table starts at n = 2 (no ``k`` below n = 6) and ends at
#: n = 50: "Die Werte in den Tabellen 4 bis 6 sind auf n = 50 begrenzt"
#: (Seite 7).
VDI3723_1_TABLE_6_K: tuple[tuple[int, int], ...] = (
    (20, 2),
    (21, 2),
    (22, 2),
    (23, 2),
    (24, 2),
    (25, 2),
    (26, 3),
    (27, 3),
    (28, 3),
    (29, 3),
    (30, 3),
    (31, 3),
    (32, 3),
    (33, 3),
    (34, 3),
    (35, 3),
    (36, 4),
    (37, 4),
    (38, 4),
    (39, 4),
    (40, 4),
    (41, 4),
    (42, 4),
    (43, 4),
    (44, 4),
    (45, 4),
    (46, 5),
    (47, 5),
    (48, 5),
    (49, 5),
    (50, 5),
)

#: VDI 3723 Blatt 1:1993-05, Tabelle 5, Seite 7 (n up to 36) and Seite 8 (37
#: to 50): "Schätzung des 10-%-Überschreitungspegels L_x;10", the ranking
#: position ``k`` of the 10 % exceedance level, as ``(n, k)`` for n = 20 to
#: 50. DIN 45687 F.4 bases R(q0,9) of Table C.1 on this column.
VDI3723_1_TABLE_5_K: tuple[tuple[int, int], ...] = (
    (20, 19),
    (21, 20),
    (22, 21),
    (23, 22),
    (24, 23),
    (25, 24),
    (26, 24),
    (27, 25),
    (28, 26),
    (29, 27),
    (30, 28),
    (31, 29),
    (32, 30),
    (33, 31),
    (34, 32),
    (35, 33),
    (36, 33),
    (37, 34),
    (38, 35),
    (39, 36),
    (40, 37),
    (41, 38),
    (42, 39),
    (43, 40),
    (44, 41),
    (45, 42),
    (46, 42),
    (47, 43),
    (48, 44),
    (49, 45),
    (50, 46),
)

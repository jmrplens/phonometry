#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Random-incidence and diffuse-field calibration of sound level meters
(IEC 61183:1994).

Annex A prints the adjustment factors of the free-field method for 10° steps
in two planes (Table A.1), says how large the largest element of that division
is (A.1.7), and lists the 38 directions of an equal-area division (note to
A.1.8). Every number was read on the printed page of BS EN 61183:1995, the
English text of EN 61183:1994, which is IEC 1183:1994 (now IEC 61183:1994)
unchanged: A.1.7 on printed folio 9 (PDF page 13), Table A.1 and the note to
A.1.8 on folio 10 (PDF page 14).

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: Table A.1, printed folio 10 (PDF page 14): "Adjustment factors K(phi) for
#: calculation of random-incidence sensitivity level with Delta alpha = pi/2
#: radians (90°)", 10° steps in two orthogonal planes. Each row is the angles
#: of incidence it prints, in degrees, and the factor it prints to five
#: decimals.
IEC61183_TABLE_A1: tuple[tuple[tuple[int, ...], float], ...] = (
    ((0, 180), 0.00095),
    ((10, 170, 190, 350), 0.00378),
    ((20, 160, 200, 340), 0.00745),
    ((30, 150, 210, 330), 0.01089),
    ((40, 140, 220, 320), 0.01401),
    ((50, 130, 230, 310), 0.01669),
    ((60, 120, 240, 300), 0.01887),
    ((70, 110, 250, 290), 0.02047),
    ((80, 100, 260, 280), 0.02146),
    ((90, 270), 0.02179),
)

#: The angular step Table A.1 is printed for, in degrees.
IEC61183_TABLE_A1_STEP_DEG = 10.0

#: A.1.7, printed folio 9 (PDF page 13): "If angular increments of 10° are
#: chosen, the surface area of the sphere is divided into 70 sub-areas. The
#: largest of these is approximately 2,2 % of the total surface area of the
#: sphere and hence less than the 3 % criterion."
IEC61183_A17_SUB_AREAS = 70
IEC61183_A17_LARGEST_PERCENT = 2.2

#: A.1.6, printed folio 8 (PDF page 12): "The largest element should be no
#: more than 3 % of the total surface area of the sphere."
IEC61183_A16_LIMIT_PERCENT = 3.0

#: Note to A.1.8, printed folio 10 (PDF page 14): "The area of each element
#: will be 2,6 % of the total surface area of the sphere."
IEC61183_EQUAL_AREA_ELEMENT_PERCENT = 2.6

#: Note to A.1.8, printed folio 10 (PDF page 14): the 20 angles of incidence
#: of the equal-area division in the horizontal plane, in the order printed;
#: the vertical plane takes "the same angles with the exception of 0° and
#: 180°".
IEC61183_EQUAL_AREA_HORIZONTAL_DEG: tuple[float, ...] = (
    0.0, 32.6, 50.8, 65.1, 77.9, 90.0, 102.2, 114.9, 129.2, 147.4,
    180.0, 212.6, 230.8, 245.1, 257.8, 270.0, 282.1, 294.9, 309.2, 327.4,
)  # fmt: skip

#: The two printed angles of that list that break its symmetry about 90°
#: (docs/ERRATA.md): 77,9° + 102,2° = 180,1° where all the other pairs sum to
#: 180,0°, and 282,1° mirrors 77,9°. The equal-area construction gives
#: 77,846° and 282,154°, which round to 77,8° and 282,2°.
IEC61183_EQUAL_AREA_ERRATA_DEG: dict[float, float] = {77.9: 77.8, 282.1: 282.2}

#: Table B.1, printed folio 14 (PDF page 18): "Characteristics of a type
#: LS2aP/LS2F microphone". Each row is the preferred frequency as printed, the
#: lowest and highest frequency it covers in Hz (the first row covers 25 Hz to
#: 800 Hz), "10 times the logarithm to the base ten of the directivity factor
#: gamma" in dB, and the "difference between diffuse-field and pressure
#: sensitivity levels Delta_DP" in dB.
IEC61183_TABLE_B1_PRINTED: tuple[tuple[str, float, float, float, float], ...] = (
    ("25 to 800", 25.0, 800.0, 0.00, 0.00),
    ("1 000", 1000.0, 1000.0, 0.05, 0.00),
    ("1 250", 1250.0, 1250.0, 0.10, 0.00),
    ("1 600", 1600.0, 1600.0, 0.20, 0.05),
    ("2 000", 2000.0, 2000.0, 0.20, 0.10),
    ("2 500", 2500.0, 2500.0, 0.35, 0.10),
    ("3 150", 3150.0, 3150.0, 0.65, 0.15),
    ("4 000", 4000.0, 4000.0, 0.85, 0.25),
    ("5 000", 5000.0, 5000.0, 1.25, 0.40),
    ("6 300", 6300.0, 6300.0, 1.80, 0.65),
    ("8 000", 8000.0, 8000.0, 2.45, 1.20),
    ("10 000", 10000.0, 10000.0, 3.30, 1.90),
    ("12 500", 12500.0, 12500.0, 4.30, 2.70),
    ("16 000", 16000.0, 16000.0, 5.30, 3.05),
    ("20 000", 20000.0, 20000.0, 6.70, 2.20),
)

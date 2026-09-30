#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound from service equipment in buildings (ISO/DIS 16032:2023).

The draft of the second edition of ISO 16032 prints no worked example. What it
does print are the tables and the one number its text computes, and those are
transcribed here as printed, defects included, so a test can tell the cells the
library takes from the print from the cells it corrects.

Every number was read on the printed page of E DIN EN ISO 16032:2023-05, the
German publication of the draft prEN ISO 16032:2023 (ISO/DIS 16032:2023),
whose English text runs from PDF page 35 on with its own folios: Clause 9 on
folio 9 and 10 (PDF pages 47 and 48), Table 2 on folio 10 (PDF page 48) and
Table A.1 on folio 12 (PDF page 50). The German text on folio 19 (PDF page 23)
prints the same Table A.1, with the same cells.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: Clause 9, folio 10 (PDF page 48): "A difference of 4 dB corresponds to a
#: correction value of 2,2 dB. If the difference is less than 4 dB the
#: correction value shall be limited to 2,2 dB." The difference and the
#: correction, in dB.
ISO16032_BACKGROUND_LIMIT_DB: tuple[float, float] = (4.0, 2.2)

#: Table A.1, folio 12 (PDF page 50): one-third-octave band centre in Hz, the
#: A-weighting and the C-weighting in dB, as printed. The C cells at 25 Hz
#: (printed "-5") and from 1 600 Hz to 10 000 Hz (printed "0") are the defect
#: registered in docs/ERRATA.md.
ISO16032_TABLE_A1_THIRD: tuple[tuple[float, float, float], ...] = (
    (25.0, -44.7, -5.0),
    (31.5, -39.4, -3.0),
    (40.0, -34.6, -2.0),
    (50.0, -30.2, -1.3),
    (63.0, -26.2, -0.8),
    (80.0, -22.5, -0.5),
    (100.0, -19.1, -0.3),
    (125.0, -16.1, -0.2),
    (160.0, -13.4, -0.1),
    (200.0, -10.9, 0.0),
    (250.0, -8.6, 0.0),
    (315.0, -6.6, 0.0),
    (400.0, -4.8, 0.0),
    (500.0, -3.2, 0.0),
    (630.0, -1.9, 0.0),
    (800.0, -0.8, 0.0),
    (1000.0, 0.0, 0.0),
    (1250.0, 0.6, 0.0),
    (1600.0, 1.0, 0.0),
    (2000.0, 1.2, 0.0),
    (2500.0, 1.3, 0.0),
    (3150.0, 1.2, 0.0),
    (4000.0, 1.0, 0.0),
    (5000.0, 0.5, 0.0),
    (6300.0, -0.1, 0.0),
    (8000.0, -1.1, 0.0),
    (10000.0, -2.5, 0.0),
)

#: Table A.1, folio 12 (PDF page 50): the octave columns, band centre in Hz
#: (the first printed "31"), A-weighting and C-weighting in dB, as printed.
ISO16032_TABLE_A1_OCTAVE: tuple[tuple[float, float, float], ...] = (
    (31.5, -39.4, -3.0),
    (63.0, -26.2, -0.8),
    (125.0, -16.1, -0.2),
    (250.0, -8.6, 0.0),
    (500.0, -3.2, 0.0),
    (1000.0, 0.0, 0.0),
    (2000.0, 1.2, -0.2),
    (4000.0, 1.0, -0.8),
    (8000.0, -1.1, -3.0),
)

#: The one-third-octave cells of Table A.1 whose C-weighting the library takes
#: from IEC 61672-1:2013 Table 3 instead of the print, in Hz.
ISO16032_TABLE_A1_C_DEFECT_HZ: tuple[float, ...] = (
    25.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
)

#: Table 2, folio 10 (PDF page 48): each printed row as (one-third-octave band
#: centres in Hz, octave band centres in Hz, reproducibility standard deviation
#: in dB). The last band row prints "800 to 10 000" and "1 000 to 8 000".
ISO16032_TABLE_2_BANDS: tuple[
    tuple[tuple[float, ...], tuple[float, ...], float], ...
] = (
    ((25.0, 31.5, 40.0), (31.5,), 1.9),
    ((50.0, 63.0, 80.0), (63.0,), 1.9),
    ((100.0, 125.0, 160.0), (125.0,), 1.9),
    ((200.0, 250.0, 315.0), (250.0,), 1.5),
    ((400.0, 500.0, 630.0), (500.0,), 1.2),
    (
        (
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
        ),
        (1000.0, 2000.0, 4000.0, 8000.0),
        1.0,
    ),
)

#: Table 2, folio 10 (PDF page 48): the A- and C-weighted rows, in dB.
ISO16032_TABLE_2_WEIGHTED: tuple[tuple[str, float], ...] = (("A", 0.8), ("C", 1.2))

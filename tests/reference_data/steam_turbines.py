#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Airborne noise of steam turbine sets (IEC 61063:1991).

The numbers the test code fixes, read on the rasterized printed page of
BS EN 61063:1996, the English text of EN 61063:1996, which is IEC 1063:1991
without modification. The standard prints no worked example, so these cells
are its whole numeric content: Table 1 on printed folio 4 (PDF page 10),
Table 2 on printed folio 8 (PDF page 14), the 1 m measurement distance of 7.1
on printed folio 7 (PDF page 13), the 7 dB limit of 8.3 on printed folio 9
(PDF page 15) and of A.3.3 on printed folio 12 (PDF page 18), and the limits
of 4.2, 4.3, 7.2.2 and the NOTE of 8.3 on printed folios 5, 6, 8 and 9.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: Table 2, printed folio 8 (PDF page 14): "Correction to be subtracted from
#: sound pressure level measured with sound source operating", in dB, keyed by
#: the "Difference between sound pressure level measured with sound source
#: operating and background sound pressure level alone", in dB. The last row
#: is printed "> 10" and "0,0"; it is keyed here by 11, the first whole
#: decibel above 10.
IEC61063_TABLE_2_DB: dict[int, float] = {
    3: 3.0,
    4: 2.0,
    5: 2.0,
    6: 1.0,
    7: 1.0,
    8: 1.0,
    9: 0.5,
    10: 0.5,
    11: 0.0,
}

#: Table 1, printed folio 4 (PDF page 10): the standard deviation of the
#: A-weighted sound power level by the survey method, in dB, for "a source
#: which produces sounds that contain prominent discrete tones" and for one
#: whose sounds "are uniformly distributed in frequency".
IEC61063_TABLE_1_DB: dict[str, float] = {"tonal": 5.0, "broadband": 4.0}

#: 7.1, printed folio 7: "The measurement distance (d) is 1 m."
IEC61063_MEASUREMENT_DISTANCE_M = 1.0

#: 8.3, printed folio 9, and A.3.3, printed folio 12: the largest environmental
#: correction K, in dB.
IEC61063_K_LIMIT_DB = 7.0

#: 4.2, printed folio 5: the background "should be at least 3 dB below".
IEC61063_BACKGROUND_CRITERION_DB = 3.0

#: 4.3, printed folio 6: "the wind speed shall be less than 6 m/s", and a
#: windscreen "for wind speeds above 1 m/s".
IEC61063_WIND_LIMIT_M_S = 6.0
IEC61063_WINDSCREEN_ABOVE_M_S = 1.0

#: NOTE of 7.2.2, printed folio 8: the overhead positions may be deleted when
#: their exclusion changes the sound power level by no "more than 1,0 dB".
IEC61063_OVERHEAD_EFFECT_DB = 1.0

#: NOTE of 8.3, printed folio 9: when the range of the position levels "does
#: not exceed 5 dB", a simple arithmetic average "should not differ by more
#: than 0,7 dB" from Equation (2).
IEC61063_ARITHMETIC_RANGE_DB = 5.0
IEC61063_ARITHMETIC_DEVIATION_DB = 0.7

#: A.3.3, printed folios 12 and 13: K <= 7 "means that the ratio of the
#: absorption area A to the area S of the measurement surface shall be equal
#: to or greater than 1".
IEC61063_MINIMUM_RATIO = 1.0

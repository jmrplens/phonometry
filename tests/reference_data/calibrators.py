#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound calibrators and the TC 29 conformance rule, as the pages print them.

Transcribed from the rasterised pages of IEC 60942:2017 (read in UNE-EN IEC
60942:2018, which carries the IEC text unchanged; PDF page = printed folio + 8)
and of IEC 61672-1:2013 (read in BS EN 61672-1:2013; PDF page = folio + 2).
Every range of nominal frequencies is kept as the printed string, "31,5 to 63"
or "> 63 to < 160", so the tests read which ends a row includes off the page
rather than off the library. A dash is ``None``. Columns are class LS, class 1
and class 2, in that order.
"""

from __future__ import annotations

#: Table 2 (folio 16, PDF page 24): range, then the sound pressure level
#: acceptance limits (LS, 1, 2) and the short-term level fluctuation limits
#: (LS, 1, 2), in dB.
IEC60942_TABLE2: list[
    tuple[
        str,
        tuple[float | None, float | None, float | None],
        tuple[float | None, float | None, float | None],
    ]
] = [
    ("31,5 to 63", (None, 0.30, None), (None, 0.20, None)),
    ("> 63 to < 160", (None, 0.30, None), (None, 0.10, None)),
    ("160 to 1 250", (0.10, 0.25, 0.40), (0.03, 0.07, 0.15)),
    ("> 1 250 to 4 000", (None, 0.35, None), (None, 0.07, None)),
    ("> 4 000 to 8 000", (None, 0.45, None), (None, 0.07, None)),
    ("> 8 000 to 16 000", (None, 0.50, None), (None, 0.07, None)),
]

#: Table 3 (folio 16, PDF page 24): supply-voltage effect, dB (LS, 1, 2).
IEC60942_TABLE3 = (0.02, 0.06, 0.16)

#: Table 4 (folio 17, PDF page 25): frequency, % (LS, 1, 2).
IEC60942_TABLE4 = (0.7, 0.7, 1.7)

#: Table 5 (folio 18, PDF page 26): level over the environmental range, dB.
IEC60942_TABLE5: list[tuple[str, tuple[float | None, float | None, float | None]]] = [
    ("31,5 to < 160", (None, 0.25, None)),
    ("160 to 1 250", (0.10, 0.25, 0.40)),
    ("> 1 250 to 4 000", (None, 0.30, None)),
    ("> 4 000 to 8 000", (None, 0.45, None)),
    ("> 8 000 to 16 000", (None, 0.60, None)),
]

#: Table 6 (folio 18, PDF page 26): frequency over the environmental range, %.
IEC60942_TABLE6 = (0.7, 0.7, 1.7)

#: Table 7 (folio 19, PDF page 27): maximum total distortion + noise, %.
IEC60942_TABLE7: list[tuple[str, tuple[float | None, float | None, float | None]]] = [
    ("31,5 to < 160", (None, 3.0, None)),
    ("160 to 1 250", (2.0, 2.5, 3.0)),
    ("> 1 250 to 16 000", (None, 3.0, None)),
]

#: Table A.1 (folio 28, PDF page 36): maximum-permitted uncertainty for the
#: generated level (LS, 1, 2) and the short-term fluctuation (LS, 1, 2), dB.
#: The last range prints as ">8 000 to 16 000", without the space the other
#: rows put after the sign.
IEC60942_TABLE_A1: list[
    tuple[
        str,
        tuple[float | None, float | None, float | None],
        tuple[float | None, float | None, float | None],
    ]
] = [
    ("31,5 to 63", (None, 0.20, None), (None, 0.15, None)),
    ("> 63 to < 160", (None, 0.20, None), (None, 0.10, None)),
    ("160 to 1 250", (0.10, 0.15, 0.35), (0.02, 0.03, 0.05)),
    ("> 1 250 to 4 000", (None, 0.25, None), (None, 0.03, None)),
    ("> 4 000 to 8 000", (None, 0.35, None), (None, 0.03, None)),
    (">8 000 to 16 000", (None, 0.50, None), (None, 0.03, None)),
]

#: Table A.2 (folio 29, PDF page 37): frequency, % (LS, 1, 2).
IEC60942_TABLE_A2 = (0.2, 0.2, 0.2)

#: Table A.3 (folio 30, PDF page 38): total distortion + noise, %.
IEC60942_TABLE_A3: list[tuple[str, tuple[float | None, float | None, float | None]]] = [
    ("31,5 to < 160", (None, 1.0, None)),
    ("160 to 1 250", (0.5, 0.5, 1.0)),
    ("> 1 250 to 16 000", (None, 1.0, None)),
]

#: Table A.4 (folio 32, PDF page 40): level over the environmental range, dB.
IEC60942_TABLE_A4: list[tuple[str, tuple[float | None, float | None, float | None]]] = [
    ("31,5 to < 160", (None, 0.25, None)),
    ("160 to 1 250", (0.10, 0.15, 0.20)),
    ("> 1 250 to 4 000", (None, 0.30, None)),
    ("> 4 000 to 8 000", (None, 0.35, None)),
    ("> 8 000 to 16 000", (None, 0.40, None)),
]

#: Table A.5 (folio 35, PDF page 43): frequency over the environmental
#: range, % (LS, 1, 2).
IEC60942_TABLE_A5 = (0.2, 0.2, 0.2)

#: A.5.5.7 and A.5.5.8 (folios 26 and 27, PDF pages 34 and 35), in the text:
#: the maximum uncertainty of the supply-voltage difference, 0,02 dB for
#: class LS and 0,04 dB for classes 1 and 2.
IEC60942_SUPPLY_VOLTAGE_MAX_U = (0.02, 0.04, 0.04)

#: 5.9.4.2 (folio 21, PDF page 29): level change in a power- or
#: radio-frequency field, dB (LS, 1, 2); and A.7.4.8 (folio 40, PDF page 48):
#: 0,05 dB maximum uncertainty for all classes.
IEC60942_FIELD_IMMUNITY = (0.10, 0.25, 0.45)
IEC60942_FIELD_IMMUNITY_MAX_U = 0.05

#: A.6.4.7 (folio 34, PDF page 42): the abbreviated test reduces the Table 5
#: limits by 0,05 dB (LS and 1) and 0,10 dB (class 2), and holds the frequency
#: to 0,5 %, 0,5 % and 1,3 %.
IEC60942_ABBREVIATED_REDUCTIONS = (0.05, 0.05, 0.10)
IEC60942_ABBREVIATED_FREQUENCY = (0.5, 0.5, 1.3)

#: The "Reasons for conformance or non-conformance" column, word for word, as
#: Table E.1 and Table C.1 both print it, keyed by the outcome number of
#: IEC 60942:2017 E.2.2 and IEC 61672-1:2013 C.2.2.
TC29_REASONS: dict[int, str] = {
    1: "Deviation within acceptance limits AND uncertainty within maximum-permitted",
    2: "Deviation within acceptance limits BUT uncertainty exceeds maximum-permitted",
    3: "Deviation exceeds acceptance limits",
    4: "Deviation exceeds acceptance limits AND uncertainty exceeds maximum-permitted",
}

#: IEC 60942:2017 Table E.1 (folio 52, PDF page 60): example number, absolute
#: measured deviation from design goal, acceptance limit, actual uncertainty
#: and maximum-permitted uncertainty (all dB), whether it conforms, and the
#: outcome number whose reason the table prints.
IEC60942_TABLE_E1: list[tuple[int, float, float, float, float, bool, int]] = [
    (1, 0.40, 0.25, 0.12, 0.15, False, 3),
    (2, 0.35, 0.25, 0.12, 0.15, False, 3),
    (3, 0.20, 0.25, 0.13, 0.15, True, 1),
    (4, 0.00, 0.25, 0.14, 0.15, True, 1),
    (5, 0.00, 0.25, 0.17, 0.15, False, 2),
    (6, 0.25, 0.25, 0.10, 0.15, True, 1),
    (7, 0.25, 0.25, 0.15, 0.15, True, 1),
    (8, 0.40, 0.25, 0.50, 0.20, False, 4),
]

#: IEC 61672-1:2013 Table C.1 (folio 45, PDF page 47): example number,
#: measured deviation from design goal, the acceptance limits "+1,0; -1,2" as
#: (upper, lower), actual and maximum-permitted uncertainty (all dB), whether
#: it conforms, and the outcome number whose reason the table prints.
IEC61672_1_TABLE_C1: list[
    tuple[int, float, tuple[float, float], float, float, bool, int]
] = [
    (1, 1.7, (1.0, -1.2), 0.3, 0.5, False, 3),
    (2, 1.1, (1.0, -1.2), 0.3, 0.5, False, 3),
    (3, 1.0, (1.0, -1.2), 0.3, 0.5, True, 1),
    (4, 0.0, (1.0, -1.2), 0.3, 0.5, True, 1),
    (5, 0.0, (1.0, -1.2), 0.9, 0.5, False, 2),
    (6, -0.5, (1.0, -1.2), 0.3, 0.5, True, 1),
    (7, -1.2, (1.0, -1.2), 0.3, 0.5, True, 1),
    (8, -1.3, (1.0, -1.2), 0.3, 0.5, False, 3),
    (9, -2.0, (1.0, -1.2), 0.3, 0.5, False, 3),
    (10, -2.0, (1.0, -1.2), 0.7, 0.5, False, 4),
]

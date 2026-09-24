#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Corrections for the free-field response of a sound level meter
(IEC 62585:2012).

Annex I prints two worked uncertainty budgets of a correction measured with a
comparison coupler (Annex E), at 1 kHz (Table I.2) and at 8 kHz (Table I.3),
and Annex H prints the exact one-twelfth-octave frequencies of the decade from
1 kHz to 10 kHz (Table H.1). Every number was read on the rasterized printed
page of BS EN 62585:2012, the English text of EN 62585:2012, which is
IEC 62585:2012 unchanged: Table H.1 on printed folio 35 (PDF page 37), Table
I.1 on folio 37 (PDF page 39), Table I.2 on folio 38 (PDF page 40) and Table
I.3 on folio 39 (PDF page 41). The maxima of clauses 9 to 14 are on folios 13
to 16 (PDF pages 15 to 18).

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: Table I.2, printed folio 38 (PDF page 40): the "Value +/- dB" column of the
#: 15 components at 1 kHz, keyed by descriptor.
IEC62585_TABLE_I2_VALUES_DB: dict[str, float] = {
    "a1": 0.005,
    "a2": 0.005,
    "a3": 0.005,
    "a4": 0.005,
    "a5": 0.05,
    "a6": 0.0,
    "a7": 0.06,
    "a8": 0.025,
    "a9": 0.025,
    "a10": 0.029,
    "a11": 0.013,
    "a12": 0.013,
    "a13": 0.0,
    "a14": 0.005,
    "a15": 0.03,
}

#: Table I.2: the ``u_i(C_FF,SLM)`` column as printed, to its four decimals.
IEC62585_TABLE_I2_STANDARD_DB: dict[str, float] = {
    "a1": 0.0029,
    "a2": 0.0029,
    "a3": 0.0029,
    "a4": 0.0029,
    "a5": 0.0289,
    "a6": 0.0,
    "a7": 0.03,
    "a8": 0.0144,
    "a9": 0.0144,
    "a10": 0.0167,
    "a11": 0.0075,
    "a12": 0.0075,
    "a13": 0.0,
    "a14": 0.0029,
    "a15": 0.03,
}

#: Table I.2: the degrees of freedom of the repeatability (a15), the one
#: component that is not "infinity".
IEC62585_REPEATABILITY_DOF = 2

#: Table I.2: "Combined standard uncertainty u(C_FF,SLM) dB 0,059 0".
IEC62585_TABLE_I2_COMBINED_DB = 0.0590

#: Table I.2: "Effective degree of freedom = 29,98".
IEC62585_TABLE_I2_EFFECTIVE_DOF = 29.98

#: Table I.2: "(normal) k = 2,11", an erratum (docs/ERRATA.md): the Student
#: factor for 95 % at 29,98 degrees of freedom is 2,04, and 2,11 is the one
#: for about 17.
IEC62585_TABLE_I2_PRINTED_K = 2.11

#: Table I.2: the expanded uncertainty, printed "0,12" with a subscript guard
#: digit "(4)", 0,124 dB, which is 2,11 times 0,0590.
IEC62585_TABLE_I2_PRINTED_EXPANDED_DB = 0.124

#: Table I.2: the expanded uncertainty the page's own numbers give, to the
#: guard digit the table prints it with: the Student factor for 95 % at the
#: 29,98 effective degrees of freedom, 2,042, times the combined standard
#: uncertainty, 0,05903 dB, is 0,1206 dB, that is 0,12(1).
IEC62585_TABLE_I2_EXPANDED_DB = 0.121

#: Table I.3, printed folio 39 (PDF page 41): the values at 8 kHz, which differ
#: from those at 1 kHz in four components.
IEC62585_TABLE_I3_VALUES_DB: dict[str, float] = {
    **IEC62585_TABLE_I2_VALUES_DB,
    "a7": 0.17,
    "a11": 0.104,
    "a12": 0.104,
    "a15": 0.06,
}

#: Table I.3: the ``u_i`` of the four components that change, as printed.
IEC62585_TABLE_I3_STANDARD_DB: dict[str, float] = {
    "a7": 0.085,
    "a11": 0.0600,
    "a12": 0.0600,
    "a15": 0.06,
}

#: Table I.3: "Combined standard uncertainty ... 0,140".
IEC62585_TABLE_I3_COMBINED_DB = 0.140

#: Table I.3: "(normal) k = 2" and "Effective degrees of freedom >30".
IEC62585_TABLE_I3_K = 2.0
IEC62585_TABLE_I3_DOF_ABOVE = 30.0

#: Table I.3: the expanded uncertainty, "0,28".
IEC62585_TABLE_I3_EXPANDED_DB = 0.28

#: Table H.1, printed folio 35 (PDF page 37): "Exact frequencies for
#: one-twelfth-octave steps over one decade", the column "Exact f_x calculated"
#: in kHz, index 0 to 40. The exponent column prints 10^(31/80) for index 31,
#: an erratum (docs/ERRATA.md); the calculated value beside it is 10^(31/40).
IEC62585_TABLE_H1_KHZ: tuple[float, ...] = (
    1.000000, 1.059254, 1.122018, 1.188502, 1.258925, 1.333521, 1.412538,
    1.496236, 1.584893, 1.678804, 1.778279, 1.883649, 1.995262, 2.113489,
    2.238721, 2.371374, 2.511886, 2.660725, 2.818383, 2.985383, 3.162278,
    3.349654, 3.548134, 3.758374, 3.981072, 4.216965, 4.466836, 4.731513,
    5.011872, 5.308844, 5.623413, 5.956621, 6.309573, 6.683439, 7.079458,
    7.498942, 7.943282, 8.413951, 8.912509, 9.440609, 10.000000,
)  # fmt: skip

#: Clauses 9 to 14, printed folios 13 to 16 (PDF pages 15 to 18): the maximum
#: permitted expanded uncertainty, as ``(clause, nominal frequency in Hz,
#: value in dB)`` at a frequency either side of each boundary and on it.
IEC62585_MAXIMA: tuple[tuple[int, float, float], ...] = (
    # Clause 9: 0,25 dB up to and including 4 kHz, 0,35 dB above.
    (9, 4000.0, 0.25),
    (9, 5000.0, 0.35),
    # Clause 10: 0,25 dB from 63 Hz to 4 kHz, 0,35 dB to 8 kHz, 0,45 dB above.
    (10, 63.0, 0.25),
    (10, 4000.0, 0.25),
    (10, 5000.0, 0.35),
    (10, 8000.0, 0.35),
    (10, 10000.0, 0.45),
    # Clause 11: 0,20 dB up to and including 4 kHz, 0,30 dB above.
    (11, 4000.0, 0.20),
    (11, 5000.0, 0.30),
    # Clauses 12 to 14: 0,25 dB to 4 kHz, 0,35 dB above 4 kHz up to 10 kHz,
    # 0,50 dB at and above 10 kHz.
    (12, 4000.0, 0.25),
    (12, 8000.0, 0.35),
    (12, 10000.0, 0.50),
    (13, 4000.0, 0.25),
    (13, 8000.0, 0.35),
    (13, 10000.0, 0.50),
    (14, 4000.0, 0.25),
    (14, 8000.0, 0.35),
    (14, 10000.0, 0.50),
)

#: Clause 6, printed folio 10 (PDF page 12): below 97 kPa, "an expanded
#: uncertainty (k=2) of 0,15 dB at frequencies less than and equal to 3 kHz
#: and 0,25 dB for frequencies above 3 kHz", as ``(frequency in Hz, value in
#: dB)``: well inside each band, at the nominal 3 kHz, and at the exact
#: one-twelfth-octave frequencies either side of it (Table H.1, 2,985 383 and
#: 3,162 278 kHz).
IEC62585_STATIC_PRESSURE_LIMIT_KPA = 97.0
IEC62585_STATIC_PRESSURE_EXPANDED_DB = (
    (1000.0, 0.15),
    (2985.383, 0.15),
    (3000.0, 0.15),
    (3162.278, 0.25),
    (8000.0, 0.25),
)

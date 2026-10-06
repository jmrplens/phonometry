#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Headphones and the simulated programme signal: IEC 60268-7 and IEC 60268-1.

Every value is read off the rasterised page. IEC 60268-1:1985 (bilingual,
PDF page = French folio + 2, English folio + 2): Clause 7 on PDF page 15
(folio 13), Table II on PDF page 23 (folio 21), Figures 1 and 2 on PDF page 24
(folio 22). Its Amendment 1 (1988-01) replaces Table AII and its Amendment 2
(1988-06) replaces 12.1; neither touches Clause 7. IEC 60268-7:2010 (Edition
3.0, PDF page = folio + 2).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# IEC 60268-1:1985 Table II (PDF page 23, folio 21): nominal frequency in Hz,
# relative level in dB, tolerance in dB (the + and - columns are equal in
# every row). The 630 Hz row closes the left half and opens the right one.
# ---------------------------------------------------------------------------
IEC60268_1_TABLE_II: tuple[tuple[float, float, float], ...] = (
    (20.0, -13.5, 3.0),
    (25.0, -10.2, 2.0),
    (31.5, -7.4, 1.0),
    (40.0, -5.2, 1.0),
    (50.0, -3.5, 1.0),
    (63.0, -2.3, 1.0),
    (80.0, -1.4, 1.0),
    (100.0, -0.9, 0.8),
    (125.0, -0.5, 0.6),
    (160.0, -0.2, 0.5),
    (200.0, -0.1, 0.5),
    (250.0, 0.0, 0.5),
    (315.0, 0.0, 0.5),
    (400.0, 0.0, 0.5),
    (500.0, 0.0, 0.5),
    (630.0, 0.0, 0.5),
    (800.0, 0.0, 0.5),
    (1000.0, -0.1, 0.6),
    (1250.0, -0.3, 0.7),
    (1600.0, -0.6, 0.8),
    (2000.0, -1.0, 1.0),
    (2500.0, -1.6, 1.0),
    (3150.0, -2.5, 1.0),
    (4000.0, -3.7, 1.0),
    (5000.0, -5.1, 1.0),
    (6300.0, -7.0, 1.0),
    (8000.0, -9.4, 1.0),
    (10000.0, -11.9, 1.0),
    (12500.0, -14.8, 1.5),
    (16000.0, -18.2, 2.0),
    (20000.0, -21.6, 3.0),
)

#: Clause 7 Note (folio 13): "the power level of the signal measured over the
#: full frequency range is approximately 12.5 dB higher than the indicated zero
#: relative level, which is measured over 1/3 octave".
IEC60268_1_FULL_RANGE_EXCESS_DB = 12.5

#: Figure 2 (folio 22): the component values of the filter, in ohms and
#: farads, in the order the signal meets them, and the load the note allows.
IEC60268_1_FIGURE2_OHM_FARAD: tuple[tuple[str, float], ...] = (
    ("series source resistor", 430.0),
    ("series capacitor", 2.2e-6),
    ("first shunt resistor", 3300.0),
    ("first shunt capacitor", 91e-9),
    ("second series resistor", 330.0),
    ("second series capacitor", 2.2e-6),
    ("second shunt resistor", 3300.0),
    ("second shunt capacitor", 68e-9),
    ("output series capacitor", 0.47e-6),
    ("output resistor", 10e3),
)
IEC60268_1_FIGURE2_MIN_LOAD_OHM = 100e3

#: Clause 3 (PDF page 11, folio 9): "If a measurement relates to a reference
#: frequency, then, in the absence of a clear reason to the contrary, this
#: shall be the standard reference frequency of 1 000 Hz." IEC 60268-7 refers
#: its comparison responses to "the standard reference frequency" (8.6.3.1,
#: 8.6.4.1) without defining it.
IEC60268_1_STANDARD_REFERENCE_FREQUENCY_HZ = 1000.0

# ---------------------------------------------------------------------------
# IEC 60268-7:2010 Clause 4 (PDF page 12, folio 10): "8 Ω as "08R0", 32 Ω as
# "32R0" and 600 Ω as "06R2"".
# ---------------------------------------------------------------------------
IEC60268_7_IMPEDANCE_CODES: dict[float, str] = {
    8.0: "08R0",
    32.0: "32R0",
    600.0: "06R2",
}

# ---------------------------------------------------------------------------
# 7.2 b) (folio 15) and 8.3.3 (folio 19): 94 dB re 20 µPa at the standard
# measuring frequency of 500 Hz; the alternative of 1 mW in the rated
# impedance; 7.1 NOTE (folio 14): IEC 61938 specifies a source impedance of
# 120 ohm; 8.3.1 NOTE 2 (folio 18): a rated source e.m.f. of 5 V.
# ---------------------------------------------------------------------------
IEC60268_7_STANDARD_LEVEL_DB = 94.0
IEC60268_7_STANDARD_FREQUENCY_HZ = 500.0
IEC60268_7_WORKING_POWER_W = 1e-3
IEC60268_7_IEC61938_SOURCE_IMPEDANCE_OHM = 120.0
IEC60268_7_IEC61938_SOURCE_EMF_V = 5.0

#: 8.2.1 b) (folio 17): the lowest modulus in the rated range is "not less
#: than 80 % of the rated value"; 8.2.2.2 c) (folio 18): "at least over the
#: frequency range 20 Hz to 20 kHz".
IEC60268_7_RATED_IMPEDANCE_FRACTION = 0.8
IEC60268_7_IMPEDANCE_RANGE_HZ = (20.0, 20000.0)

#: 8.3.2.2 b) (folio 19): "a peak-to-r.m.s ratio between 1,8 and 2,2".
IEC60268_7_LIMITING_PEAK_TO_RMS = (1.8, 2.2)

#: 8.3.6.2 b) (folio 21): "a change of at least 1 dB in the sensitivity", and
#: the measurements "at voltages 1 dB lower and 1 dB higher".
IEC60268_7_PROTECTION_STEP_DB = 1.0

#: 8.6.3.2 d) (folio 24) and 8.6.3.3: at least eight test persons, and 16 for
#: a reference headphone of the substitution method; 8.6.5.3 (folio 27) asks
#: the same 16 of the headphone that replaces the sound field.
IEC60268_7_MIN_PERSONS = 8
IEC60268_7_MIN_REFERENCE_PERSONS = 16

#: 8.6.5.2 c) and f) (folio 26): the 500 Hz band "within 3 dB", the fittings
#: repeated on "a difference exceeding 2,5 dB".
IEC60268_7_LEVEL_MATCH_DB = 3.0
IEC60268_7_MAX_FITTING_DIFFERENCE_DB = 2.5

#: 8.7.3 (folio 28): 70 Hz and 600 Hz, ratio 4:1, NOTE 1 "-1,9 dB at 70 Hz and
#: -14,0 dB at 600 Hz"; the second-order products "at 530 Hz and 670 Hz", the
#: third-order "at 460 Hz and 740 Hz"; Formula (3) prints U_470 (see
#: docs/ERRATA.md).
IEC60268_7_MODULATION_HZ = (70.0, 600.0)
IEC60268_7_MODULATION_LEVELS_DB = {70.0: -1.9, 600.0: -14.0}
IEC60268_7_SECOND_ORDER_HZ = (530.0, 670.0)
IEC60268_7_THIRD_ORDER_HZ = (460.0, 740.0)
IEC60268_7_FORMULA3_PRINTED_HZ = 470.0

#: 8.7.4.1 (folio 28): two tones "separated in frequency by 80 Hz, each giving
#: half the rated input voltage".
IEC60268_7_DIFFERENCE_FREQUENCY_HZ = 80.0

#: Annex B (folio 42): a) 5 mm2, b) ratio 0,6 and the adult 45 mm2, c)
#: 130 mm3, d) 3 dB, e) 15 dB.
IEC60268_7_ANNEX_B = {
    "entrance_area_mm2": 5.0,
    "canal_area_ratio": 0.6,
    "adult_canal_area_mm2": 45.0,
    "volume_mm3": 130.0,
    "neighbour_difference_db": 3.0,
    "sealed_attenuation_db": 15.0,
}

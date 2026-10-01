#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Audiometric test methods and the earmuff on its test fixture.

ISO 8253-1:2010 (pure-tone air and bone conduction audiometry, read on
BS EN ISO 8253-1:2010, where printed folio n is PDF page n + 8): the maximum
permissible ambient sound pressure levels of Tables 2 and 4, the earphone
attenuations of Table 3 and the uncertainty budget of Annex A. ISO
8253-2:2009 (sound field audiometry, printed folio n on PDF page n + 6): the
ambient limits of Table 2, the microphone requirements of Table 1 and the
off-axis increases of Table B.1. ISO 4869-3:2007 (the earmuff on an acoustic
test fixture, printed folio n on PDF page n + 4): Table 1, Table A.1 and the
uncertainty budget of Table B.1. Every value was read on the rasterized page,
except :data:`ISO8253_2_BINAURAL_OFFSET_DB`, which the library derives from two
of them.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# ISO 8253-1:2010, Tables 2 to 4 (folios 17 to 19, PDF pages 25 to 27)
# ---------------------------------------------------------------------------
#: The one-third-octave mid-frequencies of Tables 2 to 4, in hertz.
ISO8253_1_BANDS_HZ: tuple[float, ...] = (
    31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0,
    400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0,
    3150.0, 4000.0, 5000.0, 6300.0, 8000.0,
)  # fmt: skip

#: Table 2: L_S,max for air conduction with supra-aural earphones, in dB,
#: keyed by the lowest test tone frequency.
ISO8253_1_TABLE_2: dict[float, tuple[float, ...]] = {
    125.0: (56, 52, 47, 42, 38, 33, 28, 23, 20, 19, 18, 18, 18, 18, 20, 23,
            25, 27, 30, 32, 34, 36, 35, 34, 33),
    250.0: (66, 62, 57, 52, 48, 43, 39, 30, 20, 19, 18, 18, 18, 18, 20, 23,
            25, 27, 30, 32, 34, 36, 35, 34, 33),
    500.0: (78, 73, 68, 64, 59, 55, 51, 47, 42, 37, 33, 24, 18, 18, 20, 23,
            25, 27, 30, 32, 34, 36, 35, 34, 33),
}  # fmt: skip

#: Table 3: average sound attenuation of three earphones, in dB; the HDA 200
#: prints a dash below 63 Hz.
ISO8253_1_TABLE_3: dict[str, tuple[float, ...]] = {
    "supra-aural": (0, 0, 0, 1, 1, 2, 3, 4, 5, 5, 5, 6, 7, 9, 11, 15, 18, 21,
                    26, 28, 31, 32, 29, 26, 24),
    "ER-3A": (33, 33, 33, 33, 33, 33, 33, 34, 35, 36, 37, 37, 38, 37, 37, 37,
              35, 34, 33, 35, 37, 40, 41, 42, 43),
    "HDA 200": (math.nan, math.nan, math.nan, 17, 16, 15, 15, 15, 16, 16, 18,
                20, 23, 25, 27, 29, 30, 31, 32, 37, 41, 46, 45, 45, 44),
}  # fmt: skip

#: Table 4: L_S,max for bone conduction, in dB, keyed by the lowest test tone
#: frequency.
ISO8253_1_TABLE_4: dict[float, tuple[float, ...]] = {
    125.0: (55, 47, 41, 35, 30, 25, 20, 17, 15, 13, 11, 9, 8, 8, 7, 7, 7, 8,
            8, 6, 4, 2, 4, 9, 15),
    250.0: (63, 56, 49, 44, 39, 35, 28, 21, 15, 13, 11, 9, 8, 8, 7, 7, 7, 8,
            8, 6, 4, 2, 4, 9, 15),
}  # fmt: skip

#: The NOTEs to Tables 2 and 4: a threshold shift of +5 dB instead of +2 dB
#: raises every limit by this, in dB.
ISO8253_1_RELAXED_ALLOWANCE_DB = 8.0

# ---------------------------------------------------------------------------
# ISO 8253-1:2010, 6.2.3.2 and 8.4 (folios 9 and 13, PDF pages 17 and 21)
# ---------------------------------------------------------------------------
#: 8.4: the hearing level at which the vibrotactile threshold lies on average
#: for a bone vibrator on the mastoid, in dB, keyed by frequency in hertz.
ISO8253_1_VIBROTACTILE_DB: dict[float, float] = {250.0: 40.0, 500.0: 60.0, 1000.0: 70.0}
#: 8.4 NOTE: for forehead placement the values are about this much lower.
ISO8253_1_FOREHEAD_OFFSET_DB = 10.0
#: 6.2.3.2: a hearing level of this much or more calls for caution
#: (cross-hearing).
ISO8253_1_CROSS_HEARING_DB = 40.0
#: 6.2.3.2 Step 3: agreement to this much or less, and a change of this much
#: or more that sends the test back to further frequencies.
ISO8253_1_RETEST_AGREEMENT_DB = 5.0
ISO8253_1_RETEST_DISAGREEMENT_DB = 10.0

# ---------------------------------------------------------------------------
# ISO 8253-1:2010, Annex A (folios 24 to 27, PDF pages 32 to 35)
# ---------------------------------------------------------------------------
#: A.3.3: the audiometer's standard uncertainty, air conduction up to 4 kHz,
#: 5 dB steps, as printed.
ISO8253_1_A33_EQUIPMENT_DB = 2.3
#: A.3.4: the transducer's standard uncertainty up to and above 4 kHz.
ISO8253_1_A34_TRANSDUCER_DB = (2.9, 3.9)
#: Table A.2: the four standard uncertainties of the example, in dB.
ISO8253_1_TABLE_A2_COMPONENTS_DB = (2.5, 2.3, 2.9, 2.0)
#: A.6: the combined standard uncertainty and the expanded one, rounded to
#: the nearest full decibel.
ISO8253_1_TABLE_A2_U_DB = 4.9
ISO8253_1_TABLE_A2_EXPANDED_DB = 10.0

# ---------------------------------------------------------------------------
# ISO 8253-2:2009 (folios 7, 9 and 15; PDF pages 13, 15 and 21)
# ---------------------------------------------------------------------------
#: Table 2: the ambient limits for sound field audiometry, 31,5 Hz to
#: 12,5 kHz, in dB, keyed by the lowest test tone frequency.
ISO8253_2_BANDS_HZ: tuple[float, ...] = ISO8253_1_BANDS_HZ + (10000.0, 12500.0)
ISO8253_2_TABLE_2: dict[float, tuple[float, ...]] = {
    125.0: (52, 44, 38, 32, 27, 22, 17, 14, 12, 10, 8, 6, 5, 5, 4, 4, 4, 5,
            5, 3, 1, -1, 1, 6, 12, 14, 15),
    250.0: (60, 53, 46, 41, 36, 32, 25, 18, 12, 10, 8, 6, 5, 5, 4, 4, 4, 5,
            5, 3, 1, -1, 1, 6, 12, 14, 15),
}  # fmt: skip

#: Table 1: (front-to-random sensitivity index, allowable variation), dB.
ISO8253_2_TABLE_1: tuple[tuple[float, float], ...] = (
    (5.0, 5.0),
    (4.5, 4.5),
    (4.0, 4.0),
)

#: Table B.1: the test frequencies and the increase at the nearer ear for
#: 45 and 90 degrees of incidence, in dB. The rows start at 125 Hz although
#: the paragraph above the table announces 200 Hz.
ISO8253_2_TABLE_B1_HZ: tuple[float, ...] = (
    125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0,
    1250.0, 1500.0, 1600.0, 2000.0, 2500.0, 3000.0, 3150.0, 4000.0, 5000.0,
    6000.0, 6300.0, 8000.0, 10000.0, 12500.0,
)  # fmt: skip
ISO8253_2_TABLE_B1: dict[float, tuple[float, ...]] = {
    45.0: (0.5, 1, 1, 1, 1.5, 2.5, 3, 3.5, 3.5, 4, 4, 3.5, 3.5, 3, 3.5, 5, 5,
           4, 6, 7.5, 7.5, 5.5, 4.5, 1.5),
    90.0: (1, 1.5, 1.5, 2, 2.5, 3.5, 4.5, 5, 5, 5.5, 6, 5, 4.5, 2, 2, 2.5, 2,
           -0.5, 4, 9.5, 10, 8.5, 6, 8),
}  # fmt: skip

#: Footnote a to Table 2 says the sound-field limits are derived from ISO
#: 8253-1 for binaural listening and prints no offset. Laid side by side, from
#: 31,5 Hz to 8 kHz each is the bone-conduction limit of ISO 8253-1 Table 4
#: less this, in dB: an observation on the two transcribed tables, not a
#: value the footnote prints.
ISO8253_2_BINAURAL_OFFSET_DB = 3.0

# ---------------------------------------------------------------------------
# ISO 4869-3:2007 (folios 4, 9 and 11; PDF pages 8, 13 and 15)
# ---------------------------------------------------------------------------
#: Table 1, read with the text of 5.2.2 for an index of exactly 5 dB.
ISO4869_3_TABLE_1: tuple[tuple[float, float], ...] = ((5.0, 5.0), (4.0, 4.0))

#: Table A.1: the front-to-random sensitivity index of an ATF with a WS1P
#: microphone, in dB.
ISO4869_3_TABLE_A1: dict[float, float] = {
    500.0: 1.7, 630.0: 2.2, 800.0: 2.8, 1000.0: 3.2, 1250.0: 4.6,
    1600.0: 4.6, 2000.0: 6.3, 2500.0: 6.5, 3150.0: 5.9, 4000.0: 2.9,
    5000.0: -0.6, 6300.0: 5.1, 8000.0: 5.9,
}  # fmt: skip

#: Table B.1: the five standard uncertainties, open level, occluded level,
#: fixture, sound field and equipment, in dB, and the combined value printed
#: under it.
ISO4869_3_TABLE_B1_COMPONENTS_DB = (0.5, 1.0, 0.3, 0.5, 0.2)
ISO4869_3_TABLE_B1_U_DB = 1.3
#: B.4: the expanded uncertainty, U = 2u.
ISO4869_3_B4_EXPANDED_DB = 2.6

#: 5.1.4: the least acoustic isolation of the fixture, as (first band, last
#: band, isolation) in hertz and dB; "higher" runs to the top of the range.
ISO4869_3_ISOLATION: tuple[tuple[float, float, float], ...] = (
    (63.0, 250.0, 50.0),
    (315.0, 4000.0, 65.0),
    (5000.0, 8000.0, 55.0),
)

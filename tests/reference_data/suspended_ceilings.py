#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for the suspended-ceiling test code (EN 16487:2014).

EN 16487 is a test code: it fixes the arrangement EN ISO 354 leaves open and
prints no worked example. Its own numbers are Table 1 and the limits of clause
4, which the library carries as constants. What is here is the rest: the
chain the air-absorption correction of 4.2.1 hangs off, anchored on printed
pages of four other documents, and three real suspended-ceiling test reports
whose arrangements, room climates and ratings nobody in this project chose.
The reports are cited, not reproduced.

The documents are:

* BS EN 16487:2014, Table 1 on printed folio 14 (PDF page 16), checked a second
  time against the Spanish adoption UNE-EN 16487:2015, Tabla 1 on printed folio
  16.
* ISO 9613-1:1993, Table 1, and ISO 12999-2:2020, Table 3.
* T. E. Vigran, *Building Acoustics*, Taylor & Francis, 2008.
* T. J. Cox and P. D'Antonio, *Acoustic Absorbers and Diffusers*, 3rd edition,
  CRC Press, 2017.
* Sound Research Laboratories Ltd (UKAS testing laboratory 0444), Test
  Certificate No. 13441, contract C/24570, 4 March 2020, page 1 of 1.
* SP Swedish National Testing and Research Institute, report P302808,
  Enclosure 24, 14 July 2003, single page.
* CSTB (COFRAC accreditation 1-0305), Test Report No. AC14-26051052/10, ref.
  93/149, Test 21, 14 May 2014, single page, whose STANDARDS line reads
  "EN ISO 354, EN ISO 11654, prEN 16487".
* G. van Hout, *The Acoustic Performance of Suspended Ceiling Systems*, master
  of engineering thesis, University of Canterbury, 2016.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# EN 16487:2014 Table 1 and the coverage factors
# ---------------------------------------------------------------------------

#: Table 1, printed folio 14 (PDF page 16): the reproducibility uncertainty of
#: the sound absorption coefficient of a plane absorber, type E, 200 mm, by
#: octave band, and of the weighted rating. The 125 Hz row carries footnote a
#: (the band is not part of the weighted rating) and the last row footnote b
#: (the weighted figure is computed with no rounding anywhere in the
#: EN ISO 11654 chain).
EN16487_TABLE_1_UNCERTAINTY: dict[str, float] = {
    "125 Hz": 0.23,
    "250 Hz": 0.23,
    "500 Hz": 0.11,
    "1 kHz": 0.10,
    "2 kHz": 0.10,
    "4 kHz": 0.13,
}
EN16487_TABLE_1_WEIGHTED_UNCERTAINTY: float = 0.08

#: The coverage factor the NOTE under Table 1 names, ISO 5725-6's 2,8, and the
#: 2,0 of ISO 12999-2:2020 Table 3 at 95 % (printed folio 6) for the general
#: method. EN 16487 prints no reproducibility standard deviation anywhere, so
#: what is checkable is that each document's factor is the one used for its
#: own table.
EN16487_TABLE_1_COVERAGE_FACTOR: float = 2.8
ISO12999_2_TABLE_3_COVERAGE_FACTOR_95: float = 2.0

# ---------------------------------------------------------------------------
# The chain 4.2.1 hangs off
# ---------------------------------------------------------------------------

#: ISO 9613-1:1993, Table 1, printed folio 9 (PDF page 12), in decibels per
#: kilometre: the caption on printed folio 5 gives the unit and the standard
#: atmosphere of 101,325 kPa. Keyed by (air temperature in degrees Celsius,
#: relative humidity in percent), which are the sub-table and the column:
#: (i) at 20 degC and (j) at 25 degC. Only the cells the air-correction cases
#: consume are transcribed. Note 5 of 6.4 says the table was evaluated at the
#: exact one-third-octave midbands.
ISO9613_1_TABLE_1_DB_PER_KM: dict[tuple[float, float], dict[float, float]] = {
    # Sub-table (i), "Air temperature: 20 degC".
    (20.0, 50.0): {500.0: 2.73, 1000.0: 4.66, 2000.0: 9.86, 4000.0: 2.94e1},
    (20.0, 60.0): {500.0: 2.79, 1000.0: 4.80, 2000.0: 9.25, 4000.0: 2.54e1},
    (20.0, 90.0): {
        125.0: 2.72e-1,
        250.0: 9.66e-1,
        500.0: 2.71,
        1000.0: 5.30,
        2000.0: 9.06,
        4000.0: 2.02e1,
    },
    # Sub-table (j), "Air temperature: 25 degC", on the same printed folio.
    (25.0, 90.0): {
        125.0: 2.35e-1,
        250.0: 8.76e-1,
        500.0: 2.80,
        1000.0: 6.44,
        2000.0: 1.10e1,
        4000.0: 2.08e1,
    },
}

#: Vigran (2008), Eq. (4.41) on printed page 122 (PDF page 143): the factor
#: EN ISO 354:2003 8.1.2.1 writes only as ``m = alpha / (10 lg(e))``, printed
#: as a number to four figures.
VIGRAN_EQ_4_41_TEN_LG_E: float = 4.343

#: Vigran (2008), Eq. (4.42) and the Example on printed page 123 (PDF page
#: 144): a 100 m3 room with ``m`` read off Figure 4.8 as 0,05 1/m at 8 kHz, and
#: "The air absorption alone then gives an absorption area of 20 m2". The
#: volume in cubic metres, ``m`` in reciprocal metres and the area in square
#: metres. The arrangement is a classroom, not a reverberation-room test.
VIGRAN_EXAMPLE_VOLUME_M3: float = 100.0
VIGRAN_EXAMPLE_M_PER_M: float = 0.05
VIGRAN_EXAMPLE_AIR_ABSORPTION_M2: float = 20.0

#: Cox and D'Antonio (2017), Table 4.2 on printed page 104 (PDF page 161): "Air
#: absorption constant m1 at 20 degC and normal atmospheric pressure in
#: 10-3 m-1", at the nominal octave centres in hertz the book uses verbatim.
#: Only the three humidity rows, in percent, at or above the 50 % of 4.2.2 are
#: carried, because the drier ones describe conditions this test code does not
#: allow. The 40 % row is also the one cell of the printed table that is a
#: rounding of a rounding: at 63 Hz the book prints 0.035, which is ISO
#: 9613-1's already-rounded 1,50 x 10-1 dB/km converted, against 0.03447 from
#: the model itself. The table prints its cells to different numbers of
#: decimals, so each is judged at its own.
COX_TABLE_4_2_BANDS_HZ: tuple[float, ...] = (
    63.0,
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
    8000.0,
)
COX_TABLE_4_2_M_MILLI: dict[float, tuple[float, ...]] = {
    50.0: (0.028, 0.1, 0.3, 0.63, 1.07, 2.28, 6.83, 24.24),
    60.0: (0.024, 0.088, 0.28, 0.64, 1.11, 2.14, 5.9, 20.48),
    70.0: (0.021, 0.077, 0.26, 0.64, 1.15, 2.08, 5.32, 17.88),
}

# ---------------------------------------------------------------------------
# Sound Research Laboratories, certificate No. 13441 (2020)
# ---------------------------------------------------------------------------

#: A Combison dB42 ceiling on an E-200 mounting, measured to BS EN ISO
#: 354:2003. The conditions block prints the room volume in cubic metres, the
#: specimen area in square metres and both climates; the "Test 9" table prints
#: T1 and T2 in seconds and alpha_s per band. The six octave centres in hertz
#: Table 1 of EN 16487 covers are the ones carried.
SRL_13441_BANDS_HZ: tuple[float, ...] = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)
SRL_13441_T1_S: tuple[float, ...] = (7.66, 6.79, 5.34, 5.39, 4.15, 2.09)
SRL_13441_T2_S: tuple[float, ...] = (3.94, 3.44, 2.63, 2.53, 2.15, 1.46)
SRL_13441_ALPHA_S: tuple[float, ...] = (0.56, 0.66, 0.88, 0.96, 1.03, 0.96)
SRL_13441_VOLUME_M3: float = 300.0
SRL_13441_AREA_M2: float = 10.7
SRL_13441_DEPTH_MM: float = 200.0

#: Empty room and room with sample, as the certificate prints them: degrees
#: Celsius, percent relative humidity, millibars.
SRL_13441_EMPTY: tuple[float, float, float] = (17.5, 41.0, 1005.0)
SRL_13441_WITH_SPECIMEN: tuple[float, float, float] = (16.2, 44.0, 996.0)

#: The same certificate, lower on the page: the fifteen one-third-octave
#: alpha_s from 200 Hz to 5000 Hz that EN ISO 11654 rates, the five octave
#: alpha_p it formed from them, and the rating it prints, as (alpha_w, shape
#: indicator, absorption class).
SRL_13441_THIRD_OCTAVE_ALPHA_S: tuple[float, ...] = (
    0.61,
    0.66,
    0.84,
    0.87,
    0.88,
    0.93,
    0.93,
    0.96,
    1.02,
    1.02,
    1.03,
    1.04,
    1.06,
    0.96,
    0.98,
)
SRL_13441_ALPHA_P: tuple[float, ...] = (0.70, 0.90, 0.95, 1.00, 1.00)
SRL_13441_RATING: tuple[float, str, str] = (0.95, "", "A")

# ---------------------------------------------------------------------------
# SP Sweden, report P302808 (2003), and CSTB, report AC14-26051052/10 (2014)
# ---------------------------------------------------------------------------

#: SP P302808: an Acces C ceiling at a mounting depth of 200 mm, surface area
#: 10,8 m2, room volume 200 m3; the climate of the empty room and on the
#: object, as degrees Celsius and percent relative humidity; the five octave
#: alpha_p and the rating it prints, alpha_w = 0,9, class A. The report is from
#: eleven years before the test code existed.
SP_P302808_VOLUME_M3: float = 200.0
SP_P302808_AREA_M2: float = 10.8
SP_P302808_DEPTH_MM: float = 200.0
SP_P302808_EMPTY: tuple[float, float] = (20.0, 90.0)
SP_P302808_WITH_SPECIMEN: tuple[float, float] = (24.0, 89.0)
SP_P302808_ALPHA_P: tuple[float, ...] = (0.80, 0.85, 0.85, 0.95, 0.95)
SP_P302808_RATING: tuple[float, str, str] = (0.90, "", "A")

#: CSTB AC14-26051052/10: Hygiene Meditec A on an E-50 mounting, 10,5 m2; the
#: climate empty and with the sample, as degrees Celsius and percent relative
#: humidity; the five octave alpha_p and the rating it prints, 0,70(MH), class
#: C. Both high-frequency bands sit exactly 0,25 above the shifted curve, and
#: the accepted shift leaves an unfavourable sum of exactly 0,10, which is what
#: makes the case discriminating.
CSTB_AC14_AREA_M2: float = 10.5
CSTB_AC14_DEPTH_MM: float = 50.0
CSTB_AC14_EMPTY: tuple[float, float] = (18.0, 62.0)
CSTB_AC14_WITH_SPECIMEN: tuple[float, float] = (19.0, 58.0)
CSTB_AC14_ALPHA_P: tuple[float, ...] = (0.40, 0.85, 1.00, 0.95, 0.85)
CSTB_AC14_RATING: tuple[float, str, str] = (0.70, "MH", "C")

#: van Hout (2016), printed page 27 (PDF page 45): the E-400 mounting of a
#: university reverberation room and its 3 600 mm by 3 000 mm specimen, in
#: square metres and millimetres.
VAN_HOUT_AREA_M2: float = 10.8
VAN_HOUT_DEPTH_MM: float = 400.0

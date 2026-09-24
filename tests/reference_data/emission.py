#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound power and sound intensity: what a source emits and how well we know it.

The determination standards and their uncertainty budgets: the precision
free-field method of ISO 3745 with its reproducibility and environmental
corrections, the field-indicator scheme of ISO 9614-3 for scanning
intensity, and the IEC 61043 instrument specification - Table 2 residual
pressure-intensity index and the phase-mismatch error the index implies.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ISO 3745:2012 precision sound power (anechoic/hemi-anechoic). The Clause 10.5
# EXAMPLE combines sigma_omc = 2,0 dB and sigma_R0 = 0,5 dB at k = 2 to the
# expanded uncertainty U = 4,1 dB. The K1 background correction floors at
# 1,26 dB (>= 6 dB signal-to-noise edge bands). The meteorological correction
# C1 at the 23 C, ps0 reference is 5*lg(296/314) = -0,128 dB. Mirrors
# tests/emission/test_sound_power_precision.py.
# ---------------------------------------------------------------------------
ISO3745_U_SIGMA_R0 = 0.5  # reproducibility standard deviation (dB)
ISO3745_U_SIGMA_OMC = 2.0  # operating/mounting/... std. deviation (dB)
ISO3745_U_COVERAGE = 2.0  # coverage factor k
ISO3745_U_EXPANDED = 4.123105625617661  # U = k*sqrt(sR0^2+somc^2) (dB)
ISO3745_K1_EDGE_LEVEL = 56.0  # measured Lp in the edge band (dB)
ISO3745_K1_EDGE_BACKGROUND = 50.0  # background Lp -> dLp = 6 dB (dB)
ISO3745_K1_EDGE_FREQUENCY = 200.0  # <= 200 Hz band uses the 6 dB floor (Hz)
ISO3745_K1_EDGE_FLOOR = 1.25628  # K1 floor, 6 dB S/N edge band (dB)
ISO3745_C1_REFERENCE = -0.12819  # C1 at 23 C, ps = ps0 (dB)

# ---------------------------------------------------------------------------
# ISO 9614-3:2002 precision intensity scanning. A fully enclosing surface with
# a uniform normal intensity In = W/S recovers the source power exactly, so
# LW = 10*lg(W/P0). For W = 100 uW this is LW = 80 dB (P0 = 1 pW).
# ---------------------------------------------------------------------------
ISO9614_3_UNIFORM_POWER = 1.0e-4  # radiated power W (W)
ISO9614_3_UNIFORM_AREAS: tuple[float, ...] = (0.5, 1.0, 0.25, 2.0)
ISO9614_3_UNIFORM_LW = 80.0  # 10*lg(W/1e-12) (dB)

# ---------------------------------------------------------------------------
# IEC 61043:1993 (EN 61043:1994) Table 2, standard page 14: minimum
# pressure-residual intensity index delta_pI0 requirements, in decibels, for
# probes, processors and instruments at the 25 mm nominal microphone
# separation. Transcribed digit for digit and cross-checked against the same
# table as reproduced in Fahy, "Sound Intensity" 2nd ed., Table 6.1 (printed
# page 136), which agrees exactly. Note 1 of the table: for a microphone
# separation x in millimetres, add 10 lg(x/25) dB to every figure.
# Row = (nominal_third_octave_Hz, probe_class1, probe_class2,
#        processor_class1, processor_class2, instrument_class1,
#        instrument_class2).
# ---------------------------------------------------------------------------
IEC61043_TABLE2: list[tuple[float, float, float, float, float, float, float]] = [
    (50, 13, 7, 19, 13, 12, 6),
    (63, 14, 8, 20, 14, 13, 7),
    (80, 15, 9, 21, 15, 14, 8),
    (100, 16, 10, 22, 16, 15, 9),
    (125, 17, 11, 23, 17, 16, 10),
    (160, 18, 12, 24, 18, 17, 11),
    (200, 19, 13, 25, 19, 18, 12),
    (250, 20, 14, 26, 20, 19, 13),
    (315, 20, 15, 26, 20, 19, 14),
    (400, 20, 16, 26, 20, 19, 14.5),
    (500, 20, 17, 26, 20, 19, 15),
    (630, 20, 18, 26, 20, 19, 16),
    (800, 20, 18, 26, 20, 19, 16),
    (1000, 20, 18, 26, 20, 19, 16),
    (1250, 20, 18, 26, 20, 19, 16),
    (1600, 20, 18, 26, 20, 19, 16),
    (2000, 20, 18, 26, 20, 19, 16),
    (2500, 20, 18, 26, 20, 19, 16),
    (3150, 20, 18, 26, 20, 19, 16),
    (4000, 20, 18, 26, 20, 19, 16),
    (5000, 20, 18, 26, 20, 19, 16),
    (6300, 20, 18, 26, 20, 19, 16),
]

# Fahy, "Sound Intensity" 2nd ed., section 6.8 (printed page 135), explaining
# the effect of the Table 2 requirement on the allowable channel phase
# mismatch: "a specified value of delta_pI0 of 20 dB corresponds to a phase
# mismatch of one-hundredth of the phase difference kd ...: at 1000 Hz, this
# corresponds to a phase mismatch of about 0.26 degrees" (25 mm separation).
IEC61043_PHASE_INDEX_DB = 20.0
IEC61043_PHASE_FREQUENCY_HZ = 1000.0
IEC61043_PHASE_SPACING_M = 0.025
IEC61043_PHASE_MISMATCH_DEG = 0.26

# ---------------------------------------------------------------------------
# ISO 9614-1:1993 (UNE-EN ISO 9614-1:2010, the Spanish official version of
# EN ISO 9614-1:2009, which adopts the 1993 ISO text unchanged). Four printed
# tables, transcribed cell for cell from the rendered pages; the page offset of
# this edition is zero, so PDF page N carries printed folio N.
#
# The three graded tables share one shape and one asymmetry: grades 1 and 2 are
# tabulated band by band with the A-weighted cell blank, and grade 3 carries
# only an A-weighted value with every band cell blank. A blank below is None,
# and it is blank in the print, not zero and not "not applicable".
# ---------------------------------------------------------------------------

# Table 1, "Factor de error de desviación, K" (printed p. 11), in dB, by grade.
ISO9614_1_TABLE_1_K: dict[str, float] = {
    "precision": 10.0,
    "engineering": 10.0,
    "survey": 7.0,
}

# Rows of Table 2 and Table B.2, which share their two frequency columns:
# (octave centre range in Hz, one-third-octave centre range in Hz). The 6 300 Hz
# row has no octave counterpart, and the last row of each table is A-weighted
# and has no frequency column at all.
ISO9614_1_BAND_ROWS: list[tuple[tuple[float, float] | None, tuple[float, float]]] = [
    ((63.0, 125.0), (50.0, 160.0)),
    ((250.0, 500.0), (200.0, 630.0)),
    ((1000.0, 4000.0), (800.0, 5000.0)),
    (None, (6300.0, 6300.0)),
]

# Table 2, "Incertidumbre en la determinación de los niveles de potencia
# sonora" (printed p. 13): the standard deviation s in dB, as
# (grade 1, grade 2, grade 3) per row of ISO9614_1_BAND_ROWS. Footnote 1: the
# true level lies within +/- 2s of the measured one with 95 % confidence.
# Footnote 2 fixes the A-weighted range at 63 Hz to 4 kHz or 50 Hz to 6,3 kHz;
# footnote 3 calls the grade-3 value tentative.
ISO9614_1_TABLE_2_S: list[tuple[float | None, float | None, float | None]] = [
    (2.0, 3.0, None),
    (1.5, 2.0, None),
    (1.0, 1.5, None),
    (2.0, 2.5, None),
]
ISO9614_1_TABLE_2_S_A_WEIGHTED: tuple[float | None, float | None, float | None] = (
    None,
    None,
    4.0,
)

# Table B.1, "Factor de error Delta" (printed p. 25): one row for all bands and
# one A-weighted row, each as (grade 1, grade 2, grade 3).
ISO9614_1_TABLE_B1_ALL_BANDS: tuple[float | None, float | None, float | None] = (
    0.20,
    0.29,
    None,
)
ISO9614_1_TABLE_B1_A_WEIGHTED: tuple[float | None, float | None, float | None] = (
    None,
    None,
    0.60,
)

# Table B.2, "Valores para el factor C" (printed p. 25): the criterion-2 factor
# C, as (grade 1, grade 2, grade 3) per row of ISO9614_1_BAND_ROWS, then the
# A-weighted row whose footnote reads "63 Hz a 4 kHz ó 50 Hz a 6,3 kHz".
ISO9614_1_TABLE_B2_C: list[tuple[float | None, float | None, float | None]] = [
    (19.0, 11.0, None),
    (29.0, 19.0, None),
    (57.0, 29.0, None),
    (19.0, 14.0, None),
]
ISO9614_1_TABLE_B2_C_A_WEIGHTED: tuple[float | None, float | None, float | None] = (
    None,
    None,
    8.0,
)

# Table B.3, "Acciones a tomar para incrementar el grado de precisión de la
# determinación" (printed p. 26): the criterion of each row and the action code
# or codes Figure B.1 routes it to. The second row prints "a o b", two
# alternatives under one criterion.
ISO9614_1_TABLE_B3: list[tuple[str, tuple[str, ...]]] = [
    ("F1 > 0,6", ("e",)),
    ("F2 > Ld o (F3 - F2) > 3 dB", ("a", "b")),
    ("No se satisface el criterio 2 y 1 dB <= (F3 - F2) <= 3 dB", ("c",)),
    (
        "No se satisface el criterio 2, (F3 - F2) <= 1 dB y el procedimiento "
        "del apartado 8.3.2 o bien falla, o bien no se selecciona",
        ("d",),
    ),
]

# ---------------------------------------------------------------------------
# ISO 5136:2003 (as reproduced in BS EN ISO 5136:2009), sound power radiated
# into a duct by fans, in-duct method. Every value below was read from the
# rendered page of the PDF (the printed folio is the PDF page index minus 10);
# the decimal comma of the print is written as a point.
# ---------------------------------------------------------------------------
#: The 27 nominal one-third-octave bands of Annex C Table C.1 (PDF page 44,
#: printed p. 34), j = 1 (50 Hz) to j_max = 27 (20 kHz), in hertz.
ISO5136_BANDS: tuple[int, ...] = (
    50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000,
    1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500,
    16000, 20000,
)  # fmt: skip
#: Table C.1, the A-weighting C_j "according to IEC 60651", dB, one per band
#: of ISO5136_BANDS.
ISO5136_TABLE_C1: tuple[float, ...] = (
    -30.2, -26.2, -22.5, -19.1, -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2,
    -1.9, -0.8, 0.0, 0.6, 1.0, 1.2, 1.3, 1.2, 1.0, 0.5, -0.1, -1.1, -2.5,
    -4.3, -6.6, -9.3,
)  # fmt: skip
#: Table 2 (PDF page 17, printed p. 7), "Values of the standard deviation of
#: reproducibility for the sampling tube": the printed rows, two of which are
#: ranges ("80 to 100", "125 to 4 000"), as (lowest band, highest band,
#: sigma_R in dB).
ISO5136_TABLE_2_SIGMA_R: tuple[tuple[int, int, float], ...] = (
    (50, 50, 3.5),
    (63, 63, 3.0),
    (80, 100, 2.5),
    (125, 4000, 2.0),
    (5000, 5000, 2.5),
    (6300, 6300, 3.0),
    (8000, 8000, 3.5),
    (10000, 10000, 4.0),
)
#: Table 3 (PDF page 18, printed p. 8), "Extrapolated values" of sigma_R above
#: 10 kHz, dB, which clause 4 suggests for bands that are "not considered part
#: of this International Standard".
ISO5136_TABLE_3_SIGMA_R: tuple[tuple[int, float], ...] = (
    (12500, 4.5),
    (16000, 5.0),
    (20000, 5.5),
)
#: Annex D, Eqs (D.1) to (D.3) (PDF page 45, printed p. 35): for d = 0,5 m
#: at 1 000 Hz, C3,4 = (1,85 + 0,038 U) dB, which the print evaluates to
#: "≈ 2,4 dB" at U = 15 m/s (outlet duct) and "≈ 1,3 dB" at U = -15 m/s
#: (inlet duct); the two products are exactly 2,42 and 1,28.
ISO5136_ANNEX_D_A0 = 1.85  # dB
ISO5136_ANNEX_D_A1 = 0.038  # dB s/m
ISO5136_ANNEX_D_DIAMETER = 0.5  # m
ISO5136_ANNEX_D_FREQUENCY = 1000.0  # Hz
ISO5136_ANNEX_D_OUTLET: tuple[float, float] = (15.0, 2.4)  # (U, printed C3,4)
ISO5136_ANNEX_D_INLET: tuple[float, float] = (-15.0, 1.3)  # (U, printed C3,4)
#: Table D.1 (PDF pages 45 and 46, printed pp. 35 and 36), "Value of
#: correction C3,4 in decibels for d = 0,5 m and different flow velocities U":
#: the six columns are U = 5, -5, 15, -15, 30 and -30 m/s, the 27 rows are the
#: bands of ISO5136_BANDS. Transcribed as printed, to the printed 0,1 dB; the
#: page prints "2", "0" and "16" for cells the text layer carries as "2,0",
#: "0,0" and "16,0". The two cells of the worked example, 1 000 Hz at
#: +/-15 m/s, are the ones the print frames in bold.
ISO5136_TABLE_D1_VELOCITIES: tuple[float, ...] = (5.0, -5.0, 15.0, -15.0, 30.0, -30.0)
ISO5136_TABLE_D1: tuple[tuple[float, ...], ...] = (
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 50 Hz
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 63 Hz
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 80 Hz
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 100 Hz
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 125 Hz
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 160 Hz
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 200 Hz
    (0.1, -0.2, 0.4, -0.5, 0.8, -0.9),  # 250 Hz
    (-0.5, -0.8, -0.2, -1.1, 0.2, -1.5),  # 315 Hz
    (-0.3, -0.6, 0.0, -0.9, 0.5, -1.3),  # 400 Hz
    (-0.2, -0.5, 0.2, -0.8, 0.6, -1.2),  # 500 Hz
    (0.2, -0.1, 0.6, -0.4, 1.1, -0.9),  # 630 Hz
    (1.2, 0.9, 1.6, 0.5, 2.1, 0.0),  # 800 Hz
    (2.0, 1.7, 2.4, 1.3, 3.0, 0.7),  # 1 000 Hz
    (2.8, 2.4, 3.3, 2.0, 4.0, 1.4),  # 1 250 Hz
    (3.4, 2.9, 4.0, 2.4, 4.9, 1.7),  # 1 600 Hz
    (4.0, 3.3, 4.7, 2.7, 5.8, 1.8),  # 2 000 Hz
    (4.5, 3.7, 5.4, 2.9, 6.9, 1.9),  # 2 500 Hz
    (5.2, 4.1, 6.5, 3.1, 8.4, 2.1),  # 3 150 Hz
    (6.2, 4.9, 7.7, 3.8, 10.2, 2.8),  # 4 000 Hz
    (6.8, 5.3, 8.7, 4.2, 11.8, 3.2),  # 5 000 Hz
    (7.9, 6.1, 10.1, 4.7, 13.7, 3.8),  # 6 300 Hz
    (9.3, 7.0, 12.2, 5.6, 16.2, 4.9),  # 8 000 Hz
    (10.5, 7.6, 13.9, 5.9, 17.9, 5.6),  # 10 000 Hz
    (11.6, 8.0, 16.0, 6.7, 19.5, 6.4),  # 12 500 Hz
    (13.1, 8.7, 18.2, 7.5, 21.2, 7.3),  # 16 000 Hz
    (14.8, 9.4, 20.2, 8.4, 23.6, 7.9),  # 20 000 Hz
)
#: Half of the last printed place of Table D.1: a cell reproduces when the
#: polynomial lands within it of the printed value. The comparison has to be a
#: tolerance rather than a rounding rule, because the table rounds to 0,1 dB
#: and the polynomial lands wherever it lands: the widest gap over the 162
#: cells is the 4 000 Hz row at U = +5 m/s, where 6,151 dB is printed as 6,2,
#: which is 0,049 dB away and only just inside the budget.
ISO5136_TABLE_D1_TOLERANCE_DB = 0.05
#: Clause 1.1 (PDF page 11, printed p. 1): the maximum mean flow velocity at
#: the microphone head per shield, m/s, and the test-duct diameter range, m.
ISO5136_MAX_VELOCITY: dict[str, float] = {
    "foam-ball": 15.0,
    "nose-cone": 20.0,
    "sampling-tube": 40.0,
}
ISO5136_DUCT_DIAMETER_RANGE: tuple[float, float] = (0.15, 2.0)
#: Clause 5.3.3.4 NOTE and the footnote of Tables A.1 to A.6 (PDF pages 28
#: and 35 to 40): the sampling-tube coefficients extend to |U| <= 60 m/s for
#: information only.
ISO5136_SAMPLING_TUBE_INFORMATIVE_VELOCITY = 60.0
#: Clause 5.3.4.3 (PDF page 29, printed p. 19): Eq. (8) and its "under normal
#: conditions, c = 340 m/s".
ISO5136_C_NORMAL = 340.0
#: Clause 8.2 (PDF pages 33 and 34, printed pp. 23 and 24): S0 = 1 m^2 and
#: (rho c)_0 = 400 N s/m^3 of Eq. (12).
ISO5136_S0 = 1.0
ISO5136_RHO_C_0 = 400.0
#: Clause 9.2 (PDF page 34, printed p. 24): the expanded uncertainty at 95 %
#: coverage is twice the standard deviation of reproducibility of clause 4.
ISO5136_COVERAGE_FACTOR = 2.0


# ---------------------------------------------------------------------------
# ISO 9295:2015 Tables 1 and 2: the air absorption coefficient alpha, in Np/m,
# at a static pressure of 101,325 kPa, transcribed from the Spanish adoption
# UNE-EN ISO 9295:2015 (October 2015), PDF pages 15 and 16, printed folios 15
# and 16. Rows are the 26 frequencies from 10 000 Hz to 22 400 Hz; each row
# holds 12 cells, temperature by temperature and 40 %, 50 %, 60 % relative
# humidity within each temperature. The cells are read as printed, with the
# digit groups joined ("0,027 7" is 0.0277); the two cells set with a
# displaced group, "0,04 4" and "0,05 50", are read as the digits they show.
# The BS EN ISO 9295 draft of 2013 (DPC 13/30264708) prints the same 624 cells.
#
# ISO9295_MISPRINTED_CELLS names the 43 cells Annex A contradicts, each read on
# the printed page: (table, Hz, degC, %) -> (the print, Annex A to the four
# decimals the table carries). In every one the fourth decimal Annex A gives is
# 0. The other 581 are Annex A rounded to four decimals when the temperature is
# converted as theta + 273,16 K, which is how the tables were computed
# (ISO9295_TABLE_KELVIN_OFFSET); with theta + 273,15 K, the library's
# conversion, 61 of them move by one unit of the fourth decimal and none by more
# than 0,000 063 Np/m. For one misprinted cell the two conversions round
# differently: 19 500 Hz, 23 degC, 50 % is 0,054 0 by the table's conversion
# and 0,054 1 by the library's, against the 0,054 4 printed.
# Mirrors tests/emission/test_sound_power_high_frequency.py.
# ---------------------------------------------------------------------------
ISO9295_FREQUENCIES_HZ: tuple[float, ...] = tuple(
    10_000.0 + 500.0 * i for i in range(25)
) + (22_400.0,)
ISO9295_TABLE_1_TEMPERATURES_C: tuple[float, ...] = (18.0, 20.0, 21.0, 22.0)
ISO9295_TABLE_2_TEMPERATURES_C: tuple[float, ...] = (23.0, 24.0, 25.0, 27.0)
ISO9295_HUMIDITIES_PERCENT: tuple[float, ...] = (40.0, 50.0, 60.0)
ISO9295_TABLE_KELVIN_OFFSET = 273.16  # the Celsius offset the tables were computed with
ISO9295_MISPRINT_COUNT = 43
# One printed row per line, as the page sets it.
# fmt: off
ISO9295_TABLE_1_NP_PER_M: tuple[tuple[float, ...], ...] = (
    (0.0239, 0.0198, 0.0168, 0.0223, 0.0183, 0.0155, 0.0215, 0.0176, 0.0149, 0.0207, 0.0169, 0.0143),  # 10000 Hz
    (0.0259, 0.0216, 0.0184, 0.0243, 0.0200, 0.0170, 0.0234, 0.0192, 0.0163, 0.0226, 0.0185, 0.0157),  # 10500 Hz
    (0.0280, 0.0234, 0.0200, 0.0263, 0.0217, 0.0185, 0.0254, 0.0209, 0.0178, 0.0245, 0.0201, 0.0171),  # 11000 Hz
    (0.0301, 0.0253, 0.0217, 0.0284, 0.0236, 0.0201, 0.0274, 0.0227, 0.0193, 0.0265, 0.0218, 0.0186),  # 11500 Hz
    (0.0322, 0.0273, 0.0234, 0.0305, 0.0254, 0.0217, 0.0295, 0.0245, 0.0209, 0.0286, 0.0236, 0.0201),  # 12000 Hz
    (0.0344, 0.0293, 0.0252, 0.0326, 0.0273, 0.0234, 0.0316, 0.0264, 0.0226, 0.0307, 0.0254, 0.0217),  # 12500 Hz
    (0.0365, 0.0313, 0.0271, 0.0348, 0.0293, 0.0252, 0.0338, 0.0283, 0.0242, 0.0328, 0.0273, 0.0234),  # 13000 Hz
    (0.0387, 0.0334, 0.0290, 0.0370, 0.0313, 0.0277, 0.0366, 0.0303, 0.0266, 0.0355, 0.0292, 0.0251),  # 13500 Hz
    (0.0409, 0.0355, 0.0309, 0.0392, 0.0334, 0.0288, 0.0382, 0.0323, 0.0278, 0.0372, 0.0312, 0.0268),  # 14000 Hz
    (0.0430, 0.0376, 0.0329, 0.0415, 0.0355, 0.0307, 0.0405, 0.0344, 0.0296, 0.0394, 0.0332, 0.0286),  # 14500 Hz
    (0.0452, 0.0398, 0.0349, 0.0437, 0.0376, 0.0326, 0.0428, 0.0365, 0.0315, 0.0417, 0.0353, 0.0304),  # 15000 Hz
    (0.0474, 0.0420, 0.0369, 0.0460, 0.0398, 0.0346, 0.0451, 0.0386, 0.0334, 0.0444, 0.0374, 0.0323),  # 15500 Hz
    (0.0496, 0.0442, 0.0390, 0.0483, 0.0420, 0.0366, 0.0474, 0.0408, 0.0354, 0.0464, 0.0395, 0.0342),  # 16000 Hz
    (0.0517, 0.0464, 0.0411, 0.0506, 0.0442, 0.0386, 0.0497, 0.0433, 0.0374, 0.0487, 0.0417, 0.0362),  # 16500 Hz
    (0.0539, 0.0486, 0.0432, 0.0529, 0.0464, 0.0407, 0.0521, 0.0452, 0.0395, 0.0511, 0.0439, 0.0382),  # 17000 Hz
    (0.0560, 0.0509, 0.0454, 0.0552, 0.0487, 0.0428, 0.0544, 0.0475, 0.0415, 0.0535, 0.0462, 0.0402),  # 17500 Hz
    (0.0581, 0.0531, 0.0476, 0.0575, 0.0510, 0.0455, 0.0568, 0.0498, 0.0437, 0.0558, 0.0484, 0.0423),  # 18000 Hz
    (0.0602, 0.0554, 0.0498, 0.0598, 0.0533, 0.0472, 0.0591, 0.0521, 0.0458, 0.0582, 0.0508, 0.0444),  # 18500 Hz
    (0.0623, 0.0576, 0.0520, 0.0620, 0.0556, 0.0494, 0.0615, 0.0544, 0.0488, 0.0607, 0.0531, 0.0466),  # 19000 Hz
    (0.0643, 0.0599, 0.0543, 0.0643, 0.0580, 0.0516, 0.0638, 0.0568, 0.0502, 0.0631, 0.0554, 0.0488),  # 19500 Hz
    (0.0664, 0.0622, 0.0566, 0.0666, 0.0603, 0.0539, 0.0662, 0.0591, 0.0525, 0.0655, 0.0578, 0.0511),  # 20000 Hz
    (0.0684, 0.0644, 0.0589, 0.0688, 0.0627, 0.0562, 0.0685, 0.0615, 0.0548, 0.0679, 0.0602, 0.0533),  # 20500 Hz
    (0.0704, 0.0667, 0.0612, 0.0711, 0.0651, 0.0585, 0.0709, 0.0639, 0.0571, 0.0703, 0.0626, 0.0555),  # 21000 Hz
    (0.0724, 0.0689, 0.0635, 0.0733, 0.0675, 0.0609, 0.0732, 0.0664, 0.0594, 0.0727, 0.0651, 0.0579),  # 21500 Hz
    (0.0743, 0.0712, 0.0658, 0.0755, 0.0699, 0.0632, 0.0755, 0.0688, 0.0618, 0.0752, 0.0675, 0.0602),  # 22000 Hz
    (0.0759, 0.0730, 0.0677, 0.0773, 0.0718, 0.0651, 0.0774, 0.0707, 0.0637, 0.0771, 0.0695, 0.0621),  # 22400 Hz
)
ISO9295_TABLE_2_NP_PER_M: tuple[tuple[float, ...], ...] = (
    (0.0199, 0.0162, 0.0138, 0.0191, 0.0156, 0.0133, 0.0184, 0.0151, 0.0129, 0.0171, 0.0144, 0.0121),  # 10000 Hz
    (0.0217, 0.0178, 0.0151, 0.0209, 0.0171, 0.0146, 0.0201, 0.0165, 0.0141, 0.0187, 0.0153, 0.0132),  # 10500 Hz
    (0.0236, 0.0194, 0.0165, 0.0228, 0.0187, 0.0159, 0.0219, 0.0188, 0.0154, 0.0203, 0.0167, 0.0144),  # 11000 Hz
    (0.0256, 0.0211, 0.0179, 0.0247, 0.0203, 0.0173, 0.0238, 0.0195, 0.0167, 0.0221, 0.0182, 0.0156),  # 11500 Hz
    (0.0276, 0.0227, 0.0194, 0.0266, 0.0219, 0.0187, 0.0257, 0.0211, 0.0181, 0.0239, 0.0197, 0.0169),  # 12000 Hz
    (0.0296, 0.0245, 0.0209, 0.0286, 0.0236, 0.0202, 0.0276, 0.0228, 0.0195, 0.0257, 0.0212, 0.0182),  # 12500 Hz
    (0.0317, 0.0263, 0.0225, 0.0307, 0.0254, 0.0217, 0.0297, 0.0245, 0.0211, 0.0276, 0.0228, 0.0196),  # 13000 Hz
    (0.0339, 0.0282, 0.0242, 0.0328, 0.0272, 0.0233, 0.0317, 0.0263, 0.0225, 0.0296, 0.0245, 0.0211),  # 13500 Hz
    (0.0361, 0.0301, 0.0259, 0.0355, 0.0291, 0.0255, 0.0339, 0.0281, 0.0241, 0.0316, 0.0262, 0.0225),  # 14000 Hz
    (0.0383, 0.0321, 0.0276, 0.0372, 0.0311, 0.0266, 0.0366, 0.0330, 0.0257, 0.0337, 0.0288, 0.0244),  # 14500 Hz
    (0.0406, 0.0341, 0.0294, 0.0394, 0.0333, 0.0284, 0.0382, 0.0319, 0.0274, 0.0358, 0.0298, 0.0256),  # 15000 Hz
    (0.0429, 0.0362, 0.0312, 0.0417, 0.0355, 0.0301, 0.0405, 0.0338, 0.0291, 0.0388, 0.0316, 0.0272),  # 15500 Hz
    (0.0452, 0.0383, 0.0331, 0.0444, 0.0371, 0.0322, 0.0428, 0.0359, 0.0309, 0.0402, 0.0335, 0.0289),  # 16000 Hz
    (0.0476, 0.0404, 0.0355, 0.0464, 0.0392, 0.0338, 0.0451, 0.0379, 0.0327, 0.0425, 0.0355, 0.0306),  # 16500 Hz
    (0.0499, 0.0426, 0.0369, 0.0487, 0.0413, 0.0357, 0.0474, 0.0440, 0.0346, 0.0448, 0.0375, 0.0323),  # 17000 Hz
    (0.0523, 0.0448, 0.0389, 0.0511, 0.0435, 0.0377, 0.0498, 0.0421, 0.0365, 0.0471, 0.0395, 0.0341),  # 17500 Hz
    (0.0548, 0.0471, 0.0411, 0.0536, 0.0457, 0.0397, 0.0522, 0.0443, 0.0384, 0.0495, 0.0416, 0.0366),  # 18000 Hz
    (0.0572, 0.0494, 0.0431, 0.0566, 0.0488, 0.0417, 0.0547, 0.0465, 0.0404, 0.0519, 0.0437, 0.0378),  # 18500 Hz
    (0.0596, 0.0517, 0.0452, 0.0585, 0.0503, 0.0438, 0.0572, 0.0488, 0.0424, 0.0543, 0.0459, 0.0398),  # 19000 Hz
    (0.0621, 0.0544, 0.0473, 0.0609, 0.0526, 0.0459, 0.0597, 0.0511, 0.0445, 0.0568, 0.0481, 0.0417),  # 19500 Hz
    (0.0646, 0.0564, 0.0495, 0.0634, 0.0549, 0.0488, 0.0622, 0.0534, 0.0466, 0.0593, 0.0503, 0.0437),  # 20000 Hz
    (0.0677, 0.0588, 0.0517, 0.0666, 0.0573, 0.0502, 0.0647, 0.0558, 0.0487, 0.0618, 0.0526, 0.0458),  # 20500 Hz
    (0.0695, 0.0612, 0.0544, 0.0685, 0.0597, 0.0524, 0.0672, 0.0582, 0.0509, 0.0644, 0.0549, 0.0478),  # 21000 Hz
    (0.0722, 0.0637, 0.0563, 0.0711, 0.0622, 0.0547, 0.0698, 0.0606, 0.0531, 0.0669, 0.0573, 0.0550),  # 21500 Hz
    (0.0745, 0.0661, 0.0586, 0.0735, 0.0646, 0.0577, 0.0724, 0.0633, 0.0553, 0.0695, 0.0597, 0.0521),  # 22000 Hz
    (0.0765, 0.0681, 0.0605, 0.0756, 0.0666, 0.0588, 0.0744, 0.0655, 0.0571, 0.0716, 0.0616, 0.0538),  # 22400 Hz
)
# fmt: on
ISO9295_MISPRINTED_CELLS: dict[tuple[int, float, float, float], tuple[str, float]] = {
    (1, 13500.0, 20.0, 60.0): ("0,027 7", 0.0270),
    (1, 13500.0, 21.0, 40.0): ("0,036 6", 0.0360),
    (1, 13500.0, 21.0, 60.0): ("0,026 6", 0.0260),
    (1, 13500.0, 22.0, 40.0): ("0,035 5", 0.0350),
    (1, 15500.0, 22.0, 40.0): ("0,044 4", 0.0440),
    (1, 16500.0, 21.0, 50.0): ("0,043 3", 0.0430),
    (1, 18000.0, 20.0, 60.0): ("0,045 5", 0.0450),
    (1, 19000.0, 21.0, 60.0): ("0,048 8", 0.0480),
    (1, 20000.0, 22.0, 60.0): ("0,051 1", 0.0510),
    (2, 10000.0, 27.0, 50.0): ("0,014 4", 0.0140),
    (2, 11000.0, 25.0, 50.0): ("0,018 8", 0.0180),
    (2, 11500.0, 23.0, 50.0): ("0,021 1", 0.0210),
    (2, 13000.0, 25.0, 60.0): ("0,021 1", 0.0210),
    (2, 13500.0, 27.0, 60.0): ("0,021 1", 0.0210),
    (2, 14000.0, 24.0, 40.0): ("0,035 5", 0.0350),
    (2, 14000.0, 24.0, 60.0): ("0,025 5", 0.0250),
    (2, 14500.0, 24.0, 50.0): ("0,031 1", 0.0310),
    (2, 14500.0, 25.0, 40.0): ("0,036 6", 0.0360),
    (2, 14500.0, 25.0, 50.0): ("0,033 0", 0.0300),
    (2, 14500.0, 27.0, 50.0): ("0,028 8", 0.0280),
    (2, 14500.0, 27.0, 60.0): ("0,024 4", 0.0240),
    (2, 15000.0, 24.0, 50.0): ("0,033 3", 0.0330),
    (2, 15500.0, 24.0, 50.0): ("0,035 5", 0.0350),
    (2, 15500.0, 27.0, 40.0): ("0,038 8", 0.0380),
    (2, 16000.0, 24.0, 40.0): ("0,044 4", 0.0440),
    (2, 16000.0, 24.0, 60.0): ("0,032 2", 0.0320),
    (2, 16500.0, 23.0, 60.0): ("0,035 5", 0.0350),
    (2, 17000.0, 25.0, 50.0): ("0,04 4", 0.0400),
    (2, 18000.0, 23.0, 60.0): ("0,041 1", 0.0410),
    (2, 18000.0, 27.0, 60.0): ("0,036 6", 0.0360),
    (2, 18500.0, 24.0, 40.0): ("0,056 6", 0.0560),
    (2, 18500.0, 24.0, 50.0): ("0,048 8", 0.0480),
    (2, 19500.0, 23.0, 50.0): ("0,054 4", 0.0540),
    (2, 20000.0, 24.0, 60.0): ("0,048 8", 0.0480),
    (2, 20500.0, 23.0, 40.0): ("0,067 7", 0.0670),
    (2, 20500.0, 24.0, 40.0): ("0,066 6", 0.0660),
    (2, 21000.0, 23.0, 60.0): ("0,054 4", 0.0540),
    (2, 21500.0, 23.0, 40.0): ("0,072 2", 0.0720),
    (2, 21500.0, 24.0, 40.0): ("0,071 1", 0.0710),
    (2, 21500.0, 27.0, 60.0): ("0,05 50", 0.0500),
    (2, 22000.0, 24.0, 60.0): ("0,057 7", 0.0570),
    (2, 22000.0, 25.0, 50.0): ("0,063 3", 0.0630),
    (2, 22400.0, 25.0, 50.0): ("0,065 5", 0.0650),
}

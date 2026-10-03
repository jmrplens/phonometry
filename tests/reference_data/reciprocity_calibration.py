#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Primary calibration of laboratory standard microphones by reciprocity
(IEC 61094-2:2009 in a coupler, IEC 61094-3:2016 with COR1:2016 in a free
field).

IEC 61094-2 prints three tables meant for testing a program: Gerber's
temperature transfer function E_V (Table A.1, "accurate to 0,000 01") and the
real and imaginary parts of the input impedance of six open capillary tubes at
the reference conditions (Tables B.1 and B.2, "intended to be used when
testing a calculation program"). It also prints the nominal coupler dimensions
of Tables C.1 and C.2, the wave-motion corrections of the large-volume coupler
for LS1P microphones (Table C.3), the low-frequency validity of the broad-band
solution (A.3) and the list of uncertainty components (Table 1). IEC 61094-3
prints the attenuation of sound in air at nine laboratory conditions (Table
B.1, computed by ISO 9613-1) and its own list of uncertainty components (Table
1).

Every number was read on the rasterized printed page. BS EN 61094-2:2009, the
English text of EN 61094-2:2009 which is IEC 61094-2:2009 unchanged: Table 1
on printed folio 19 (PDF page 21), Table A.1 on folio 21 (PDF page 23), A.3 on
folio 22 (PDF page 24), Tables B.1 and B.2 on folios 24 and 25 (PDF pages 26
and 27), Tables C.1, C.2 and C.3 on folios 28 to 30 (PDF pages 30 to 32), the
reference conditions of clause 4 on folio 7 (PDF page 9). IEC 61094-3:2016
(Edition 2.0, 2016-06, English-French): Table 1 on folios 17 and 18 (PDF pages
19 and 20) and Table B.1 on folio 22 (PDF page 24).

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: IEC 61094-2:2009 and IEC 61094-3:2016 clause 4: 23,0 °C, 101,325 kPa, 50 %.
IEC61094_RECIPROCITY_REFERENCE_CONDITIONS: tuple[float, float, float] = (
    23.0,
    101325.0,
    50.0,
)

#: IEC 61094-2:2009 Table A.1, printed folio 21 (PDF page 23): Gerber's E_V,
#: keyed by X, as ((real, imaginary) at R = 0,2, at R = 0,5, at R = 1). "The
#: figures given are considered accurate to 0,000 01."
IEC61094_2_TABLE_A1: dict[float, tuple[tuple[float, float], ...]] = {
    1.0: ((0.72127, 0.24038), (0.71996, 0.22323), (0.72003, 0.22146)),
    2.0: ((0.80092, 0.17722), (0.80122, 0.16986), (0.80128, 0.16885)),
    3.0: ((0.83727, 0.14818), (0.83751, 0.14304), (0.83754, 0.14236)),
    4.0: ((0.85907, 0.13003), (0.85920, 0.12614), (0.85922, 0.12563)),
    5.0: ((0.87393, 0.11732), (0.87402, 0.11421), (0.87403, 0.11380)),
    7.0: ((0.89343, 0.10030), (0.89348, 0.09807), (0.89349, 0.09777)),
    10.0: ((0.91082, 0.08477), (0.91086, 0.08321), (0.91086, 0.08300)),
    20.0: ((0.93693, 0.06086), (0.93694, 0.06007), (0.93694, 0.05997)),
    30.0: ((0.94850, 0.05002), (0.94851, 0.04950), (0.94851, 0.04942)),
    40.0: ((0.95540, 0.04349), (0.95541, 0.04310), (0.95541, 0.04304)),
    60.0: ((0.96358, 0.03568), (0.96359, 0.03541), (0.96359, 0.03538)),
    80.0: ((0.96846, 0.03098), (0.96846, 0.03078), (0.96846, 0.03076)),
    100.0: ((0.97179, 0.02776), (0.97179, 0.02761), (0.97179, 0.02758)),
    200.0: ((0.98005, 0.01972), (0.98005, 0.01964), (0.98005, 0.01963)),
    400.0: ((0.98590, 0.01399), (0.98590, 0.01395), (0.98590, 0.01395)),
    800.0: ((0.99003, 0.00992), (0.99003, 0.00990), (0.99003, 0.00989)),
}

#: The length-to-diameter ratios of the three columns of Table A.1.
IEC61094_2_TABLE_A1_RATIOS: tuple[float, float, float] = (0.2, 0.5, 1.0)

#: The six tubes of Tables B.1 and B.2, in the order of their columns, as
#: (length in mm, radius in mm) as printed: 50 mm at 0,1667, 0,20 and 0,25 mm,
#: then 100 mm at the same three radii. The radius printed 0,1667 mm is 1/6 mm:
#: the printed values come back with 1/6 mm, and with 0,1667 mm the real part
#: comes out about 0,08 % low (8e-4 relative, up to 0,005 GPa s/m3), beyond
#: the last printed digit.
IEC61094_2_TABLE_B_TUBES: tuple[tuple[float, float], ...] = (
    (50.0, 0.1667),
    (50.0, 0.20),
    (50.0, 0.25),
    (100.0, 0.1667),
    (100.0, 0.20),
    (100.0, 0.25),
)

#: IEC 61094-2:2009 Tables B.1 and B.2, printed folios 24 and 25 (PDF pages 26
#: and 27): the input impedance of an open capillary tube at the reference
#: conditions, in GPa s/m3, as printed. Each row is the frequency in Hz, then
#: (real, imaginary) for the six tubes in the order of
#: :data:`IEC61094_2_TABLE_B_TUBES`. Table B.1 prints its last real part,
#: 20 kHz for the 100 mm tube of 0,25 mm radius, as "2.021" with a point, and
#: Table B.2 prints the imaginary part at 800 Hz for the 100 mm tube of
#: 0,1667 mm as "-3,89" with two decimals; both are read as the numbers they
#: write.
IEC61094_2_TABLE_B: tuple[tuple[float, tuple[tuple[float, float], ...]], ...] = (
    (
        20.0,
        (
            (3.015, 0.097),
            (1.454, 0.074),
            (0.596, 0.049),
            (6.034, 0.096),
            (2.911, 0.114),
            (1.193, 0.090),
        ),
    ),
    (
        25.0,
        (
            (3.016, 0.122),
            (1.455, 0.092),
            (0.596, 0.061),
            (6.037, 0.120),
            (2.913, 0.143),
            (1.194, 0.112),
        ),
    ),
    (
        31.5,
        (
            (3.017, 0.154),
            (1.455, 0.116),
            (0.596, 0.077),
            (6.043, 0.152),
            (2.917, 0.180),
            (1.196, 0.141),
        ),
    ),
    (
        40.0,
        (
            (3.019, 0.195),
            (1.456, 0.147),
            (0.597, 0.098),
            (6.052, 0.192),
            (2.923, 0.228),
            (1.199, 0.180),
        ),
    ),
    (
        50.0,
        (
            (3.021, 0.244),
            (1.458, 0.184),
            (0.598, 0.123),
            (6.066, 0.240),
            (2.931, 0.285),
            (1.203, 0.225),
        ),
    ),
    (
        63.0,
        (
            (3.026, 0.307),
            (1.460, 0.232),
            (0.599, 0.155),
            (6.088, 0.300),
            (2.946, 0.359),
            (1.210, 0.283),
        ),
    ),
    (
        80.0,
        (
            (3.033, 0.390),
            (1.464, 0.295),
            (0.601, 0.197),
            (6.124, 0.378),
            (2.970, 0.456),
            (1.222, 0.361),
        ),
    ),
    (
        100.0,
        (
            (3.043, 0.488),
            (1.470, 0.369),
            (0.604, 0.246),
            (6.178, 0.467),
            (3.006, 0.570),
            (1.240, 0.452),
        ),
    ),
    (
        125.0,
        (
            (3.060, 0.611),
            (1.480, 0.462),
            (0.609, 0.308),
            (6.264, 0.573),
            (3.063, 0.711),
            (1.270, 0.567),
        ),
    ),
    (
        160.0,
        (
            (3.090, 0.783),
            (1.496, 0.592),
            (0.618, 0.396),
            (6.416, 0.705),
            (3.168, 0.907),
            (1.323, 0.731),
        ),
    ),
    (
        200.0,
        (
            (3.134, 0.981),
            (1.521, 0.743),
            (0.632, 0.496),
            (6.638, 0.829),
            (3.326, 1.125),
            (1.406, 0.923),
        ),
    ),
    (
        250.0,
        (
            (3.204, 1.230),
            (1.561, 0.933),
            (0.653, 0.623),
            (6.985, 0.923),
            (3.589, 1.383),
            (1.547, 1.170),
        ),
    ),
    (
        315.0,
        (
            (3.322, 1.557),
            (1.628, 1.186),
            (0.688, 0.792),
            (7.540, 0.896),
            (4.061, 1.668),
            (1.815, 1.502),
        ),
    ),
    (
        400.0,
        (
            (3.531, 1.993),
            (1.747, 1.527),
            (0.749, 1.021),
            (8.355, 0.488),
            (4.940, 1.848),
            (2.378, 1.923),
        ),
    ),
    (
        500.0,
        (
            (3.868, 2.513),
            (1.940, 1.948),
            (0.848, 1.306),
            (9.074, -0.676),
            (6.287, 1.418),
            (3.532, 2.203),
        ),
    ),
    (
        630.0,
        (
            (4.501, 3.192),
            (2.310, 2.533),
            (1.033, 1.711),
            (8.677, -2.737),
            (7.339, -0.771),
            (5.629, 0.932),
        ),
    ),
    (
        800.0,
        (
            (5.805, 3.992),
            (3.109, 3.354),
            (1.433, 2.325),
            (6.378, -3.89),
            (5.313, -3.149),
            (4.380, -2.506),
        ),
    ),
    (
        1000.0,
        (
            (8.331, 4.287),
            (4.884, 4.216),
            (2.374, 3.186),
            (4.354, -3.030),
            (3.006, -2.594),
            (1.928, -2.129),
        ),
    ),
    (
        1250.0,
        (
            (12.122, 1.347),
            (9.001, 3.171),
            (5.376, 3.733),
            (3.546, -1.381),
            (2.127, -1.156),
            (1.147, -0.944),
        ),
    ),
    (
        1600.0,
        (
            (9.201, -5.328),
            (7.936, -4.376),
            (6.752, -3.270),
            (4.171, 0.430),
            (2.408, 0.455),
            (1.195, 0.280),
        ),
    ),
    (
        2000.0,
        (
            (4.332, -4.500),
            (3.027, -3.769),
            (1.956, -2.958),
            (6.325, 0.265),
            (4.404, 0.975),
            (2.523, 1.222),
        ),
    ),
    (
        2500.0,
        (
            (2.698, -1.998),
            (1.638, -1.665),
            (0.894, -1.281),
            (4.986, -1.700),
            (3.723, -1.549),
            (2.774, -1.341),
        ),
    ),
    (
        3150.0,
        (
            (2.808, 0.489),
            (1.579, 0.241),
            (0.783, 0.049),
            (4.412, 0.204),
            (2.660, 0.197),
            (1.392, 0.051),
        ),
    ),
    (
        4000.0,
        (
            (5.917, 2.431),
            (3.529, 2.282),
            (1.745, 1.690),
            (5.245, -1.070),
            (4.024, -0.858),
            (3.079, -0.516),
        ),
    ),
    (
        5000.0,
        (
            (5.959, -2.799),
            (4.838, -2.427),
            (3.917, -1.945),
            (5.058, 0.209),
            (3.258, 0.437),
            (1.767, 0.403),
        ),
    ),
    (
        6300.0,
        (
            (3.307, 0.181),
            (1.940, -0.041),
            (1.012, -0.193),
            (4.580, -0.071),
            (2.921, -0.098),
            (1.673, -0.222),
        ),
    ),
    (
        8000.0,
        (
            (6.581, -1.231),
            (5.380, -0.589),
            (4.133, 0.227),
            (4.696, -0.041),
            (3.034, -0.029),
            (1.751, -0.141),
        ),
    ),
    (
        10000.0,
        (
            (4.180, 0.867),
            (2.461, 0.637),
            (1.257, 0.331),
            (4.977, -0.053),
            (3.360, 0.152),
            (1.949, 0.209),
        ),
    ),
    (
        12500.0,
        (
            (3.909, -0.548),
            (2.545, -0.705),
            (1.546, -0.769),
            (4.765, -0.281),
            (3.335, -0.294),
            (2.277, -0.276),
        ),
    ),
    (
        16000.0,
        (
            (4.047, -0.217),
            (2.594, -0.406),
            (1.540, -0.538),
            (4.757, -0.175),
            (3.267, -0.187),
            (2.142, -0.226),
        ),
    ),
    (
        20000.0,
        (
            (4.531, 0.426),
            (2.809, 0.341),
            (1.516, 0.134),
            (4.847, -0.107),
            (3.322, 0.000),
            (2.021, 0.032),
        ),
    ),
)

#: IEC 61094-2:2009 Table C.1, folio 28: the nominal dimensions of plane-wave
#: couplers in mm, (ø A, ø B, ø C, D, E minimum, E maximum), per type.
IEC61094_2_TABLE_C1_MM: dict[str, tuple[float, ...]] = {
    "LS1P": (23.77, 18.6, 18.6, 1.95, 3.5, 9.5),
    "LS2aP": (13.2, 9.3, 9.3, 0.5, 3.0, 7.0),
    "LS2bP": (12.15, 9.8, 9.8, 0.7, 3.5, 6.0),
}

#: IEC 61094-2:2009 Table C.2, folio 29: the nominal dimensions of
#: large-volume couplers in mm, (ø A, ø B, ø C, D, E, F), per type, with a
#: tolerance of ± 0,03 mm on C, E and F.
IEC61094_2_TABLE_C2_MM: dict[str, tuple[float, ...]] = {
    "LS1P": (23.77, 18.6, 42.88, 1.95, 12.55, 0.80),
    "LS2aP": (13.2, 9.3, 18.30, 0.5, 3.50, 0.40),
    "LS2bP": (12.15, 9.8, 18.30, 0.7, 3.50, 0.40),
}
IEC61094_2_TABLE_C2_TOLERANCE_MM = 0.03

#: IEC 61094-2:2009 Table C.3, folio 30: the wave-motion correction in dB,
#: keyed by frequency in Hz; the first row is printed "≤ 800".
IEC61094_2_TABLE_C3_DB: dict[float, float] = {
    800.0: 0.000,
    1000.0: -0.002,
    1250.0: -0.013,
    1600.0: -0.034,
    2000.0: -0.060,
    2500.0: -0.087,
}

#: IEC 61094-2:2009 A.3, folio 22: "Equations (A.3) - (A.4) are valid for the
#: frequency range given by omega rho a**2 > 100 eta. This corresponds to
#: frequencies higher than 3 Hz and 12 Hz for plane-wave couplers as given in
#: Table C.1 for type LS1P and LS2aP microphones respectively."
IEC61094_2_A3_LOWEST_HZ: dict[str, float] = {"LS1P": 3.0, "LS2aP": 12.0}

#: IEC 61094-2:2009 Table 1, folio 19: each measured quantity and the
#: subclauses it is referred to, in the table's order, as printed.
IEC61094_2_TABLE_1_TEXT: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Series impedance", ("7.2",)),
    ("Voltage ratio", ("7.2",)),
    ("Cross-talk", ("7.2",)),
    ("Inherent and ambient noise", ("7.2",)),
    ("Distortion", ("7.2",)),
    ("Frequency", ("7.2",)),
    ("Receiver ground shield", ("6.3",)),
    ("Transmitter ground shield", ("6.3", "7.2")),
    ("Coupler length", ("7.3.2.1",)),
    ("Coupler diameter", ("7.3.2.1",)),
    ("Coupler volume", ("7.3.2.1", "7.3.2.2")),
    ("Coupler surface area", ("7.3.2.1", "7.3.2.2")),
    ("Unintentional coupler/microphone leakage", ()),
    ("Capillary tube dimensions", ("7.3.2.3",)),
    ("Static pressure", ("7.3.2.4",)),
    ("Temperature", ("7.3.2.4",)),
    ("Relative humidity", ("7.3.2.4",)),
    ("Front cavity depth", ("7.3.3.1",)),
    ("Front cavity volume", ("7.3.3.1",)),
    ("Equivalent volume", ("7.3.3.2",)),
    ("Resonance frequency", ("7.3.3.2",)),
    ("Loss factor", ("7.3.3.2",)),
    ("Diaphragm compliance", ("7.3.3.2",)),
    ("Diaphragm mass", ("7.3.3.2",)),
    ("Diaphragm resistance", ("7.3.3.2",)),
    ("Additional heat conduction caused by front cavity thread", ("7.3.3.1",)),
    ("Polarizing voltage", ("6.5.3", "7.3.3.3")),
    ("Heat conduction theory", ("Annex A",)),
    ("Adding of excess volume", ("7.3.3.1", "7.4")),
    ("Viscosity losses", ("7.4",)),
    ("Radial wave-motion", ("6.4", "7.3.2.1", "7.4")),
    ("Rounding error", ()),
    ("Repeatability of measurements", ()),
    ("Static pressure corrections", ("6.5", "Annex D")),
    ("Temperature corrections", ("6.5", "Annex D")),
)

#: IEC 61094-3:2016 Table 1, folios 17 and 18: each measured quantity and the
#: subclauses it is referred to, in the table's order, as printed.
IEC61094_3_TABLE_1_TEXT: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Series impedance", ("7.2",)),
    ("Voltage ratio", ("7.2",)),
    ("Cross-talk", ("7.2",)),
    ("Inherent and ambient noise", ("7.2",)),
    ("Distortion", ("7.2",)),
    ("Reflections from surroundings", ("7.2", "7.3")),
    ("Frequency", ("7.2",)),
    ("Receiver shield", ("6.3",)),
    ("Transmitter shield", ("6.3", "7.2")),
    ("Distance", ("6.4", "6.5")),
    ("Static pressure", ("6.6.2", "7.6")),
    ("Temperature", ("6.6.3", "7.6")),
    ("Relative humidity", ("6.6.4", "7.6")),
    ("Standing waves between microphones", ("7.3",)),
    ("Air attenuation", ("7.4", "Annex B")),
    ("Acoustic centres", ("6.5",)),
    ("Polarizing voltage", ("6.2", "7.5")),
    ("Deviation from plane-waves", ("6.4", "7.3")),
    ("Mathematical manipulations", ()),
    ("Rounding error", ()),
    ("Repeatability of measurements", ()),
    ("Static pressure corrections", ("6.6", "Annex C")),
    ("Temperature corrections", ("6.6", "Annex C")),
)

#: IEC 61094-3:2016 Table B.1, folio 22: the nine conditions of its columns,
#: (temperature in °C, relative humidity in %), all at 101,325 kPa.
IEC61094_3_TABLE_B1_CONDITIONS: tuple[tuple[float, float], ...] = (
    (21.0, 25.0),
    (21.0, 50.0),
    (21.0, 80.0),
    (23.0, 25.0),
    (23.0, 50.0),
    (23.0, 80.0),
    (25.0, 25.0),
    (25.0, 50.0),
    (25.0, 80.0),
)

#: IEC 61094-3:2016 Table B.1, printed folio 22 (PDF page 24): the attenuation
#: of sound pressure in air in dB/m, "calculated according to ISO 9613-1", at
#: 101,325 kPa, keyed by frequency in kHz, nine columns in the order of
#: :data:`IEC61094_3_TABLE_B1_CONDITIONS`.
IEC61094_3_TABLE_B1: dict[float, tuple[float, ...]] = {
    1.0: (0.0054, 0.0048, 0.0054, 0.0054, 0.0052, 0.0059, 0.0054, 0.0057, 0.0063),
    1.25: (0.0075, 0.0059, 0.0063, 0.0072, 0.0062, 0.0069, 0.0070, 0.0067, 0.0076),
    1.6: (0.0111, 0.0075, 0.0077, 0.0104, 0.0078, 0.0083, 0.0099, 0.0082, 0.0091),
    2.0: (0.0162, 0.0099, 0.0093, 0.0149, 0.0099, 0.0099, 0.0140, 0.0102, 0.0107),
    2.5: (0.0240, 0.0134, 0.0116, 0.0220, 0.0132, 0.0121, 0.0203, 0.0132, 0.0129),
    3.15: (0.0365, 0.0192, 0.0153, 0.0332, 0.0184, 0.0155, 0.0304, 0.0180, 0.0161),
    4.0: (0.0565, 0.0287, 0.0212, 0.0514, 0.0271, 0.0210, 0.0469, 0.0259, 0.0212),
    5.0: (0.0846, 0.0426, 0.0299, 0.0773, 0.0397, 0.0291, 0.0706, 0.0374, 0.0287),
    6.3: (0.1267, 0.0649, 0.0441, 0.1170, 0.0601, 0.0421, 0.1076, 0.0561, 0.0407),
    8.0: (0.1882, 0.1010, 0.0673, 0.1767, 0.0933, 0.0635, 0.1645, 0.0866, 0.0605),
    10.0: (0.2643, 0.1527, 0.1013, 0.2539, 0.1411, 0.0949, 0.2405, 0.1308, 0.0896),
    12.5: (0.3578, 0.2292, 0.1535, 0.3537, 0.2131, 0.1434, 0.3429, 0.1980, 0.1347),
    16.0: (0.4771, 0.3541, 0.2435, 0.4885, 0.3327, 0.2275, 0.4889, 0.3115, 0.2132),
    20.0: (0.5929, 0.5139, 0.3682, 0.6266, 0.4901, 0.3452, 0.6468, 0.4641, 0.3240),
    25.0: (0.7123, 0.7256, 0.5514, 0.7737, 0.7061, 0.5207, 0.8224, 0.6794, 0.4910),
    31.5: (0.8421, 1.0019, 0.8244, 0.9332, 0.9998, 0.7876, 1.0166, 0.9828, 0.7491),
    40.0: (0.9947, 1.3445, 1.2191, 1.1136, 1.3795, 1.1847, 1.2326, 1.3915, 1.1419),
    50.0: (1.1758, 1.7135, 1.7083, 1.3157, 1.8007, 1.6930, 1.4636, 1.8612, 1.6594),
}

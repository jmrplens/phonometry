#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Soundscape reference data: ISO/TS 12913-3:2019 and a subset of the ISD.

Two kinds of data live here and they are kept apart.

**Printed values of ISO/TS 12913-3:2019** (first edition, 2019-12), read on
the page: the range of the coordinates of Formulas (A.1) and (A.2), clause A.3
(PDF page 11, printed folio 5); the scale values of Table A.1 (PDF page 10,
folio 4) and Table B.1 (PDF page 14, folio 8); and the rows of Table D.1 (PDF
page 19, folio 13).

**A derived subset of the International Soundscape Database (ISD) v1.0**, for
consistency checks only, never as a calibration oracle. Source: A. Mitchell,
T. Oberman, F. Aletta et al., "The International Soundscape Database (ISD)"
v1.0, Zenodo, DOI 10.5281/zenodo.10672568, licensed CC BY 4.0. Changes made
here: from the file "ISD v1.0 Data.csv" of that deposit, the median of each of
the eight perceived affective quality answers per location, over every
response at the location whatever the language of its questionnaire, the
number of responses and of recordings per location, and the median over a
location's recordings of the published LAeq and N5 were computed; and the
eight answers of the 93 responses at Regent's Park Japanese Garden (survey
version engISO2018) are copied as they are, ``None`` for a blank. The survey
codes each answer 1 to 5 with 5 for "strongly agree", which is the orientation
of the scale values of ISO/TS 12913-3 Table A.1 for part 2; the location
medians bear it out, "pleasant" being at or above "annoying" at every location
but one, Euston Tap (above at 22, equal at 3). The audio of the database is
not used: its recordings carry a per-channel normalisation that the deposit
does not document.
"""

#: ISO/TS 12913-3:2019 A.3 (PDF page 11, folio 5): "The range of the
#: coordinates that results from the formulas is +-(4 + sqrt(32)) = +-9,66".
ISO12913_3_COORDINATE_RANGE_PRINTED = 9.66

#: ISO/TS 12913-3:2019 Table A.1 (PDF page 10, folio 4): the scale values
#: assigned to the five response categories of each part of Method A, from the
#: left-hand box to the right-hand one.
ISO12913_3_TABLE_A1_SCALE_VALUES = {
    1: (1, 2, 3, 4, 5),
    2: (5, 4, 3, 2, 1),
    3: (5, 4, 3, 2, 1),
    4: (1, 2, 3, 4, 5),
}

#: ISO/TS 12913-3:2019 Table B.1 (PDF page 14, folio 8): the scale values of
#: the source ranking of Method B, part 2.
ISO12913_3_TABLE_B1_RANKS = (1, 2, 3, 4, 5, 6, 7, 8)

#: ISO/TS 12913-2:2018 Annex C, the response categories of the four parts of
#: Method A from the left-hand box to the right-hand one, keyed by the figure
#: that prints them: Figures C.2 and C.3 on PDF page 21 (printed p. 15),
#: Figures C.4, C.5 and C.6 on PDF page 22 (printed p. 16).
ISO12913_2_METHOD_A_CATEGORIES = {
    "C.2": ("Not at all", "A little", "Moderately", "A lot", "Dominates completely"),
    "C.3": ("Not at all", "A little", "Moderately", "A lot", "Dominates completely"),
    "C.4": (
        "Strongly agree",
        "Agree",
        "Neither agree, nor disagree",
        "Disagree",
        "Strongly disagree",
    ),
    "C.5": ("Very good", "Good", "Neither good, nor bad", "Bad", "Very bad"),
    "C.6": ("Not at all", "Slightly", "Moderately", "Very", "Perfectly"),
}

#: ISO/TS 12913-2:2018 Figure C.4 (PDF page 22, printed p. 16): the eight
#: scales of the perceived affective quality, in the order printed.
ISO12913_2_FIGURE_C4_ATTRIBUTES = (
    "pleasant",
    "chaotic",
    "vibrant",
    "uneventful",
    "calm",
    "annoying",
    "eventful",
    "monotonous",
)

#: ISO/TS 12913-3:2019 Table D.1 (PDF page 19, folio 13): parameter, the
#: metrics determined for each channel, whether the representative value may
#: be the average of the ears as well as the higher one, and the reference.
ISO12913_3_TABLE_D1 = (
    (
        "Sound pressure level",
        ("LAeq,T", "LCeq,T", "LAF5,T", "LAF95,T"),
        False,
        "ISO 1996-1",
    ),
    (
        "Loudness (time-variant loudness)",
        ("N5", "Naverage", "Nrmc", "N95", "N5/N95"),
        True,
        "ISO 532-1",
    ),
    ("Sharpness", ("S5", "Saverage", "S95"), True, "DIN 45692"),
    ("Psychoacoustic tonality", ("T",), True, "ECMA 74"),
    ("Roughness", ("R10", "R50"), True, "[32]"),
    ("Fluctuation strength", ("F10", "F50"), True, "[32]"),
)

#: ISD v1.0, per location: name, responses, recordings, the median of the
#: eight answers (pleasant, chaotic, vibrant, uneventful, calm, annoying,
#: eventful, monotonous), and the median over the recordings of the published
#: LAeq [dB] and N5 [sone]. Derived as the module docstring says; CC BY 4.0.
ISD_LOCATION_MEDIANS = (
    ("CamdenTown", 105, 68, (3, 4, 4, 2, 2, 3, 4, 3), 69.96, 33.80),
    ("CampoPrincipe", 116, 24, (5, 2, 3, 3, 4, 1, 3, 2), 60.96, 16.15),
    ("CarloV", 126, 53, (5, 2, 3, 2, 4, 1, 3, 2), 55.15, 11.15),
    ("DadongSquare", 364, 364, (4, 2, 4, 4, 4, 2, 3, 2), 68.66, 27.00),
    ("EustonTap", 100, 56, (2, 4, 3, 3, 2, 3, 3, 3), 69.45, 31.00),
    ("LianhuashanParkEntrance", 62, 28, (4, 3, 4, 4, 3, 2, 3, 3), 71.05, 29.90),
    ("LianhuashanParkForest", 60, 29, (4, 3, 4, 3, 3, 2, 3, 3), 84.13, 67.20),
    ("MarchmontGarden", 105, 80, (4, 2, 3, 3, 4, 2, 3, 2), 55.14, 11.75),
    ("MiradorSanNicolas", 33, 17, (5, 2, 3, 2, 4, 1.5, 4, 2), 67.91, 24.30),
    ("MonumentoGaribaldi", 32, 19, (4, 2, 3, 3, 4, 2, 3, 2), 53.31, 10.25),
    ("Noorderplantsoen", 97, 59, (4, 3, 4, 2, 4, 2, 4, 2), 60.09, 17.20),
    ("OlympicSquare", 337, 337, (4, 2, 4, 3, 4, 2, 3, 2), 60.93, 17.40),
    ("PancrasLock", 95, 50, (4, 3, 3, 2, 4, 2, 3, 2), 59.02, 14.80),
    ("PingshanPark", 69, 39, (4, 3, 4, 4, 3, 2, 3, 3), 68.11, 24.40),
    ("PingshanStreet", 101, 49, (3, 4, 3, 3, 3, 3, 3, 3), 63.04, 19.20),
    ("PlazaBibRambla", 24, 14, (5, 2, 3, 3, 4, 1, 3, 2), 65.73, 20.20),
    ("RegentsParkFields", 118, 68, (5, 2, 3, 3, 4, 1, 3, 2), 53.12, 9.97),
    ("RegentsParkJapan", 93, 65, (5, 1, 4, 3, 5, 1, 3, 2), 59.74, 15.50),
    ("RussellSq", 149, 86, (4, 2, 4, 2, 4, 1, 3, 2), 66.12, 22.95),
    ("SanMarco", 99, 45, (4, 4, 4, 2, 2, 2, 4, 1), 69.53, 26.90),
    ("StPaulsCross", 66, 45, (4, 2.5, 4, 2, 4, 2, 3, 2), 61.83, 17.40),
    ("StPaulsRow", 72, 43, (4, 3, 4, 2, 3, 2, 3, 3), 63.34, 18.20),
    ("TateModern", 153, 100, (4, 3, 4, 2, 4, 2, 4, 2), 63.00, 18.40),
    ("TorringtonSq", 115, 71, (3, 4, 4, 3, 2, 3, 3, 2), 63.51, 21.30),
    ("ZhongshanPark", 452, 452, (3, 3, 4, 3, 3, 2, 3, 3), 66.27, 23.95),
    ("ZhongshanSquare", 446, 446, (4, 3, 4, 3, 3, 2, 3, 3), 63.33, 19.10),
)

#: ISD v1.0, the eight answers of each of the 93 responses at Regent's Park
#: Japanese Garden (LocationID RegentsParkJapan), in the attribute order above,
#: ``None`` for a blank. Copied from the deposit; CC BY 4.0.
ISD_REGENTS_PARK_JAPAN_ANSWERS = (
    (5, 1, 5, 1, 5, 1, 4, 1),
    (5, 1, 4, 1, 5, 1, 4, 1),
    (4, 3, 3, 2, 3, 2, 4, 4),
    (4, 4, 3, 3, 4, 3, 3, 3),
    (4, 3, 4, 3, 4, 3, 3, 3),
    (5, 1, 4, 3, 2, 4, 4, 3),
    (5, 1, 4, 3, 5, 1, 3, 1),
    (4, 3, 3, 1, 2, 2, 5, 1),
    (1, 2, 4, 3, 5, 2, 4, 5),
    (5, 2, 4, 2, 4, 2, 4, 3),
    (5, 1, 5, None, 4, 1, 4, 1),
    (5, 1, 5, 2, 5, 1, 3, 2),
    (5, 1, 4, 1, 5, 1, 4, 1),
    (5, 2, 5, 4, 5, 1, 3, 1),
    (3, 2, 2, 3, 4, 2, 3, 3),
    (5, 1, 4, 4, 4, 1, 4, 2),
    (5, 1, 5, 2, 5, 2, 4, 1),
    (5, 2, 5, 2, 5, 2, 5, 4),
    (4, 2, 5, 2, 4, 1, 3, 3),
    (5, 1, 4, 1, 4, 1, 5, 1),
    (5, 1, 2, 4, 5, 1, 4, 5),
    (5, 2, 5, 4, 4, 2, 2, 3),
    (5, 1, 4, 2, 5, 1, 3, 1),
    (4, 2, 5, 1, 3, 1, 2, 3),
    (5, 2, 3, 3, 4, 1, 3, 3),
    (4, 1, 2, 3, 5, 1, 5, 3),
    (5, 1, 5, 1, 5, 1, 5, 1),
    (5, 4, 4, 3, 5, 1, 3, 1),
    (5, 1, 3, 1, 5, 1, 3, 1),
    (4, 1, 4, 1, 5, 1, 4, 1),
    (5, 2, 4, 3, 4, 1, 4, 3),
    (4, 2, 4, 2, 2, 2, 2, 2),
    (5, 2, 4, 2, 4, 1, 4, 2),
    (4, 1, 5, 1, 5, 1, 3, 4),
    (5, 2, 3, 3, 5, 1, 3, 2),
    (1, 4, 2, 1, 2, 1, 2, 4),
    (5, 1, 4, 2, 3, 1, 4, 1),
    (5, 1, 4, 1, 4, 1, 3, 1),
    (5, 3, 3, 3, 5, 1, 1, 1),
    (4, 3, 2, 5, 2, 3, 2, 3),
    (3, 2, 4, 3, 2, 4, 3, 3),
    (4, 1, 4, 3, 2, 1, 3, 2),
    (5, 1, 3, 2, 5, 1, 2, 1),
    (5, 1, 5, 1, 5, 1, 4, 1),
    (5, 1, 4, 3, 5, 1, 1, 1),
    (5, 1, 4, 2, 5, 2, 2, 2),
    (5, 3, 5, 2, 3, 1, 4, 2),
    (5, 1, 3, 3, 5, 1, 3, 1),
    (5, 1, 3, 4, 5, 1, 3, 3),
    (4, 2, 4, 3, 5, 1, 3, 3),
    (5, 2, 4, 2, 5, 1, 4, 3),
    (5, 2, 5, 2, 5, 1, 3, 2),
    (5, 1, 4, 4, 4, 1, 1, 1),
    (5, 1, 2, 3, 4, 1, 3, 2),
    (5, 1, 5, 3, 4, 2, 4, 1),
    (4, 1, 4, 1, 4, 2, 4, 2),
    (5, 1, 4, 3, 5, 1, 1, 1),
    (5, 1, 4, 4, 5, 1, 1, 1),
    (5, 1, 4, 3, 5, 1, 3, 1),
    (5, 1, 2, 1, 5, 1, 1, 1),
    (5, 1, 3, 1, 4, 1, 4, 3),
    (1, 5, 1, 5, 4, 5, 1, 5),
    (5, 1, 1, 1, 5, 1, 1, 2),
    (5, 1, 3, 4, 5, 1, 2, 4),
    (5, 1, 1, 1, 5, 1, 5, 1),
    (4, 1, 1, 4, 5, 1, 1, 1),
    (5, 1, 4, 3, 5, 1, 2, 2),
    (5, 2, 2, 4, 5, 1, 2, 3),
    (5, 1, 2, 2, 4, 1, 4, 1),
    (4, 3, 4, 4, 4, 2, 3, 1),
    (5, 1, 3, 2, 4, 2, 3, 1),
    (5, 1, 5, 1, 5, 1, 3, 1),
    (5, 1, 2, 3, 4, 2, 1, 2),
    (5, 2, 4, 2, 5, 1, 4, 1),
    (4, 2, 4, 2, 4, 1, 3, 1),
    (5, 1, 4, 3, 5, 1, 3, 1),
    (5, 1, 4, 1, 5, 1, 3, 1),
    (5, 1, 4, 3, 4, 2, 4, 2),
    (5, 2, 4, 1, 5, 1, 3, 1),
    (4, 3, 3, 3, 5, 1, 4, 3),
    (4, 3, 4, 3, 4, 1, 3, 3),
    (5, 3, 3, 3, 5, 1, 3, 3),
    (5, 3, 4, 3, 4, 2, 3, 3),
    (5, 1, 3, 4, 5, 1, 1, 2),
    (5, 3, 5, 1, 4, 1, 4, 1),
    (5, 1, 4, 2, 5, 1, 4, 1),
    (4, 3, 4, 3, 4, 3, 3, 3),
    (5, 1, 3, 3, 5, 1, 3, 2),
    (5, 1, 4, 3, 5, 2, 3, 1),
    (5, 2, 4, 3, 5, None, 1, 1),
    (5, 1, 4, 2, 5, 1, 4, 1),
    (5, 1, 5, 1, 5, 1, 5, 1),
    (5, 1, 5, 1, 5, 1, 3, 1),
)

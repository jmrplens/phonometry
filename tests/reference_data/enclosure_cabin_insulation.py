#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for enclosures and cabins measured where they stand.

ISO 11546-1:1995, ISO 11546-2:1995 and ISO 11957:1996 print no worked numeric
example, so every number here was read on the printed page of a document that
measured or worked the same quantity and owes nothing to this library. Each
banner names the document, its edition, the PDF page and the printed folio,
and says what the numbers can pin: the arithmetic the standards share with the
document, never the measurement procedure, the applicability of Table 1 or the
test environment, unless the banner says otherwise.

The documents are:

* R. C. Payne and D. J. Simmons, "Environmental correction factor K2A",
  National Physical Laboratory report CIRA(EXT) 009, April 1996, Crown
  copyright: five real rooms measured three ways.
* F. Heisterkamp, "Machine Noise: Experimental Study of the Local
  Environmental Correction for the Emission Sound Pressure Level", Acoustics
  2024, 6(1), 177-203, open access: one BAuA workroom assessed by three test
  engineers.
* R. F. Barron, *Industrial Noise Control and Acoustics*, Marcel Dekker, New
  York, 2003 (ISBN 0-8247-0701-X), Example 7-8: a machine enclosure predicted
  by the book's own model.
* R. J. Peters, B. J. Smith and M. Hollins, *Acoustics and Noise Control*, 3rd
  edition, Routledge, 2011, Example 1.13.
* D. A. Harris (ed.), *Noise Control Manual*, Noise Control Association, Van
  Nostrand Reinhold, 1991 (Springer reprint, ISBN 978-1-4757-6011-8),
  Appendix 3.
* W. Schirmer (ed.), *Technischer Laermschutz*, 2nd edition, Springer, 2006,
  and the 3rd edition with J. Huebelt, Springer Vieweg, 2023, 10.8.1.
* Suva, W. Lips, *Laermbekaempfung durch Kapselungen*, Bestellnummer 66026.d,
  revised edition March 2010.
* DGUV, Laermschutz-Arbeitsblatt IFA-LSA 01-243, *Geraeuschminderung durch
  Kapselung*, October 2014.
* ISO 3741:2010 and ISO 3744:2010, and ISO 717-1:2013 Annex C, the documents
  clauses 6.4, 8 and Annex A of ISO 11957 delegate to; the rating column of
  that Annex C is :data:`reference_data.ISO717_1_ANNEX_C_R`.
* Three accredited laboratory reports of cabins rated to clause 8 of
  ISO 11957, named at their spectra.

The rounding examples of ISO 80000-1 that clause 9.4 of ISO 11546 is held to
are in :mod:`reference_data.rounding`.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# ISO 11546-2:1995 Annex C, the two tables of the standard itself
# ---------------------------------------------------------------------------

#: Table C.1 "Requirements concerning environmental correction K2 and
#: background noise", PDF page 16, printed folio 12: for each base standard,
#: the largest environmental correction K_2 it tolerates and the smallest
#: margin dL it needs over the background, both in decibels, with ``None``
#: where the cell prints a dash. ISO 9614-1 and ISO 9614-2 share one column.
#: The last column is headed ISO 10204, which is no standard; its own footnote
#: names ISO 11204, and that is the key here (see the errata registry).
ISO11546_2_TABLE_C1_DB: dict[str, tuple[float | None, float | None]] = {
    "ISO 3743-1": (None, 6.0),
    "ISO 3744": (2.0, 6.0),
    "ISO 3746": (7.0, 3.0),
    "ISO 3747": (None, 3.0),
    "ISO 9614-1": (None, None),
    "ISO 9614-2": (None, None),
    "ISO 11201": (2.0, 6.0),
    "ISO 11202": (7.0, 3.0),
    "ISO 11204": (7.0, 6.0),
}

#: Table C.2 "Approximate values of the mean sound absorption coefficient,
#: alpha, for different room configurations", PDF page 17, printed folio 13,
#: read on the printed page. Both columns are transcribed, because the
#: description is the whole of what this table says: the coefficient is only
#: its key. The same seven rows and the same wording are printed in BS EN ISO
#: 11546-2:2009, printed folio 13 (PDF page 19). The 2010 editions of the sound
#: power standards print a longer table under the same title and it is not
#: this one: ISO 3744:2010 Table A.1 (printed folio 36) and ISO 3746:2010 Table
#: A.1 (printed folio 24) carry eight rows, adding 0,30 for a room with an
#: absorbing ceiling and bare walls, and reword two of the seven.
ISO11546_2_TABLE_C2: dict[float, str] = {
    0.05: (
        "Nearly empty room with smooth hard walls made of concrete, brick, "
        "plaster or tile"
    ),
    0.1: "Partly empty room; room with smooth walls",
    0.15: "Room with furniture; rectangular machinery room; rectangular industrial room",
    0.2: (
        "Irregularly shaped room with furniture; irregularly shaped machinery "
        "room or industrial room"
    ),
    0.25: (
        "Room with upholstered furniture; machinery or industrial room with a "
        "small amount of sound-absorbing material on ceiling or walls "
        "(e.g. partially absorptive ceiling)"
    ),
    0.35: "Room with sound-absorbing materials on both ceiling and walls",
    0.5: "Room with large amounts of sound-absorbing materials on ceiling and walls",
}

# ---------------------------------------------------------------------------
# NPL CIRA(EXT) 009 (1996): the environmental correction of five real rooms
# ---------------------------------------------------------------------------

#: Table 8 on PDF page 19, printed folio 15: the area of each of the four
#: measurement surfaces the reference sound source was measured over, in
#: square metres. Surfaces 1 and 2 have the same area, so every quantity
#: computed from area alone comes out the same for both, which the printed
#: tables confirm.
NPL_SURFACE_M2: dict[int, float] = {1: 14.1, 2: 14.1, 3: 28.2, 4: 49.6}

#: Table 9 on PDF page 20, printed folio 16: for each of the five rooms, the
#: area of its boundary surfaces in square metres, its volume in cubic metres,
#: the A-weighted reverberation time in seconds, and the two ends of the range
#: of mean absorption coefficients the report reads off the table of room
#: descriptions in Annex A of ISO 3744:1994 and ISO 3746:1995, the editions its
#: references 4 and 5 name. The report reproduces that table as its Table 1,
#: seven rows that are Table C.2 of ISO 11546-2 under another name; the 2010
#: editions print a different one with eight. Rooms A and E are given a single
#: coefficient rather than a range.
NPL_ROOMS: dict[str, tuple[float, float, float, float, float]] = {
    # S_V in m2, V in m3, T (A-weighted) in s, alpha from, alpha to
    "A": (134.0, 91.5, 0.2, 0.5, 0.5),
    "B": (168.0, 116.0, 0.5, 0.1, 0.25),
    "C": (373.0, 428.0, 1.3, 0.1, 0.25),
    "D": (834.0, 1188.0, 1.0, 0.2, 0.5),
    "E": (358.0, 274.0, 2.3, 0.05, 0.05),
}

#: Table 6 on PDF page 15, printed folio 11: the boundary area it prints for
#: room E, in square metres, where Table 9 prints 358 m2 for the same room and
#: the same volume. Table 9 is the one that pairs the area with the volume and
#: the reverberation time.
NPL_TABLE_6_ROOM_E_SURFACE_M2: float = 258.0

#: Table 8 again: the A-weighted sound power level of the reference sound
#: source as ISO 3744 measured it in each room and on each surface, in
#: decibels re 1 pW, and the level the source was calibrated to under ISO 6926.
NPL_SOUND_POWER_DB: dict[str, dict[int, float]] = {
    "A": {1: 90.9, 2: 91.5, 3: 91.9, 4: 92.0},
    "B": {1: 94.2, 2: 94.3, 3: 95.2},
    "C": {1: 94.3, 2: 94.4, 3: 96.0},
    "D": {1: 91.2, 2: 91.8, 3: 92.2, 4: 92.8},
    "E": {1: 96.1, 2: 96.4, 3: 98.6},
}
NPL_REFERENCE_SOURCE_DB: float = 90.9

#: Tables 10 to 14 on PDF pages 22 to 24, printed folios 18 to 20,
#: ``absolute`` row: the measured K_2A of each room and measurement surface, in
#: decibels, against the 90,9 dB re 1 pW the reference sound source was
#: calibrated to. This is a measurement, not an evaluation of a formula, and it
#: is the ground truth the applicability rows are judged against.
NPL_MEASURED_K2A: dict[str, dict[int, float]] = {
    "A": {1: 0.0, 2: 0.6, 3: 1.0, 4: 1.1},
    "B": {1: 3.3, 2: 3.4, 3: 4.3},
    "C": {1: 3.4, 2: 3.5, 3: 5.1},
    "D": {1: 0.3, 2: 0.9, 3: 1.3, 4: 1.9},
    "E": {1: 5.2, 2: 5.5, 3: 7.7},
}

#: The same tables, ``reverberation (A-wt)`` row: K_2A as the authors computed
#: it from their Eq. (3), K_2 = 10 lg (1 + 4 S/A), with the room absorption of
#: their Eq. (5), A = 0,16 V/T. That is the pair ISO 3744 prints as Eq. (A.2)
#: and Eq. (A.3), and the pair ISO 11546-2 leans on through Annex C.
NPL_REVERBERATION_K2A: dict[str, dict[int, float]] = {
    "A": {1: 2.5, 2: 2.5, 3: 4.0, 4: 5.7},
    "B": {1: 4.0, 2: 4.0, 3: 6.0},
    "C": {1: 3.2, 2: 3.2, 3: 5.0},
    "D": {1: 1.1, 2: 1.1, 3: 2.0, 4: 3.1},
    "E": {1: 5.9, 2: 5.9, 3: 8.4},
}

#: The same tables, ``estimated room absorption`` row, as the two bounds each
#: cell prints; the lower bound goes with the upper end of the absorption
#: range. These are printed values, and they are deliberately **not** an
#: oracle: they do not follow the report's own Eq. (3), but
#: 10 lg (1 + S/(alpha S_V)) with the factor 4 dropped, which the test and the
#: conformance row on that column record so that the exclusion is not quietly
#: reversed later.
NPL_ESTIMATED_K2A: dict[str, dict[int, tuple[float, float]]] = {
    "A": {1: (0.8, 0.8), 2: (0.8, 0.8), 3: (1.5, 1.5), 4: (2.4, 2.4)},
    "B": {1: (1.3, 2.6), 2: (1.3, 2.6), 3: (2.2, 4.3)},
    "C": {1: (0.6, 1.3), 2: (0.6, 1.3), 3: (1.1, 2.3)},
    "D": {1: (0.1, 0.4), 2: (0.1, 0.4), 3: (0.3, 0.7), 4: (0.1, 1.1)},
    "E": {1: (2.7, 2.7), 2: (2.7, 2.7), 3: (4.3, 4.3)},
}

# ---------------------------------------------------------------------------
# Heisterkamp (2024): one BAuA workroom, three assessments
# ---------------------------------------------------------------------------

#: Table 3 on PDF page 10, printed folio 186: what three test engineers of
#: different experience assessed for one and the same workroom, as mean
#: absorption coefficient, boundary surface area in square metres and the
#: absorption area A = alpha S_V the table prints beside them in square metres,
#: followed by the K_2A each assessment yields on the two reference measurement
#: surfaces the same folio defines, in decibels. The table's fourth column
#: holds column means rather than a fourth assessment, so it is not a case. The
#: printed A is rounded (engineer 2's 0,15 x 173,0 lands on the tie at 25,95
#: and prints 25,9), which is why alpha and S_V are the inputs, never it.
BAUA_ENGINEERS: dict[str, tuple[float, float, float, float, float]] = {
    # alpha, S_V in m2, A in m2, K_2A at 0,5 m, K_2A at 1 m
    "Test Eng. 1": (0.15, 174.0, 26.1, 7.1, 9.2),
    "Test Eng. 2": (0.15, 173.0, 25.9, 7.1, 9.3),
    "Test Eng. 3": (0.30, 174.3, 52.3, 4.9, 6.7),
}

#: Folio 186 again: the reference measurement surface for a workstation 0,5 m
#: from the machine, and for one at 1 m, in square metres.
BAUA_SURFACES_M2: tuple[float, float] = (26.9, 48.3)

#: Table 4 on PDF page 11, printed folio 187: the equivalent absorption area
#: each of the two rooms was measured to have with a reference sound source, in
#: square metres, then the K_2A computed from it at 0,5 m, at 1 m and on the
#: 25,1 m2 measurement surface the source itself stood on, in decibels.
BAUA_DIRECT: dict[str, tuple[float, float, float, float]] = {
    # A in m2, K_2A at 0,5 m, K_2A at 1 m, K_2A on the 25,1 m2 surface
    "workroom": (55.2, 4.7, 6.5, 4.5),
    "former reverberation room": (97.7, 3.2, 4.7, 3.1),
}

#: Folio 187: the measurement surface the direct method used, in square
#: metres, printed rounded from the 2 m hemisphere the text defines, and the
#: A-weighted sound power level of the reference sound source, in decibels.
BAUA_DIRECT_SURFACE_M2: float = 25.1
BAUA_SOURCE_POWER_DB: float = 90.67

#: Folio 187 again: the average A-weighted level on that surface in each room,
#: in decibels. The workroom cell closes on its own absorption area through the
#: author's Eq. (9); the other does not (it would need 79,74 dB), which is why
#: only the absorption areas of Table 4 are used as inputs.
BAUA_LEVEL_IN_SITU_DB: dict[str, float] = {
    "workroom": 81.17,
    "former reverberation room": 81.08,
}

# ---------------------------------------------------------------------------
# Barron (2003), Example 7-8: a machine enclosure
# ---------------------------------------------------------------------------

#: Table 7-5 "Solution for Example 7-8" on PDF page 320, printed folio 308: a
#: machine in a 1,80 m by 1,20 m by 1,00 m plywood enclosure, with the operator
#: 3 m away in a room 20 m by 20 m by 4 m. The octave band centres in hertz,
#: which are exactly the mandatory octave range of clause 6.2 of ISO 11546-1;
#: the machine sound power, the power radiated once the enclosure is in place,
#: the insertion loss, the power ratio W/W_out, and the sound pressure levels
#: at the operator without and with the enclosure, all in decibels except the
#: ratio and printed to 0,1 dB. The example is a prediction, not an ISO 11546
#: or ISO 11957 measurement: the insertion loss comes from the sound power
#: balance of the book's Equation (7-85), and only the arithmetic that follows
#: is shared with the standards.
BARRON_TABLE_7_5_OCTAVES_HZ: tuple[float, ...] = (
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
)
BARRON_TABLE_7_5_LW_DB: tuple[float, ...] = (103.0, 109.0, 114.0, 117.0, 113.0, 107.0)
BARRON_TABLE_7_5_LW_OUT_DB: tuple[float, ...] = (92.0, 95.4, 97.0, 98.2, 94.2, 82.7)
BARRON_TABLE_7_5_IL_DB: tuple[float, ...] = (11.0, 13.6, 17.0, 18.8, 18.9, 24.3)
BARRON_TABLE_7_5_POWER_RATIO: tuple[float, ...] = (
    12.70,
    22.78,
    50.29,
    76.10,
    77.81,
    267.6,
)
BARRON_TABLE_7_5_LP_WITHOUT_DB: tuple[float, ...] = (
    93.4,
    98.5,
    102.9,
    104.6,
    102.8,
    95.5,
)
BARRON_TABLE_7_5_LP_WITH_DB: tuple[float, ...] = (82.4, 84.9, 85.9, 85.8, 83.9, 71.2)

#: The rest of Table 7-5 and of Example 7-8 on printed folios 307 and 308 (PDF
#: pages 319 and 320): the room constant by octave band, in square metres, the
#: 1 120 m2 of boundary of the 20 m by 20 m by 4 m room and the 3 m from the
#: machine to the operator, with a directivity factor of unity. The room
#: constant is the column to feed a field calculation: the absorption
#: coefficient the row above it prints at 2 kHz, 0,043, gives 50,32 m2, and the
#: printed 47,88 m2 is what 0,041 gives.
BARRON_TABLE_7_5_ROOM_CONSTANT_M2: tuple[float, ...] = (
    40.62,
    51.55,
    60.19,
    84.30,
    47.88,
    66.44,
)
BARRON_TABLE_7_5_ABSORPTION_AT_2_KHZ: float = 0.043
BARRON_EXAMPLE_7_8_SURFACE_M2: float = 1120.0
BARRON_EXAMPLE_7_8_OPERATOR_DISTANCE_M: float = 3.0

#: The one band of Table 7-5 where the sound power rows do not close on
#: themselves, in hertz. At 2 000 Hz the table prints L_W,out = 94,2 dB while
#: 113 - 18,9 = 94,1, and the table's own L_p(OB) of 83,9 dB follows 94,1 rather
#: than 94,2, so it is the printed L_W,out that is 0,1 dB high there and the
#: printed insertion loss that is right. A slip in a textbook, not in a
#: standard, so it is recorded here and not in docs/ERRATA.md.
BARRON_TABLE_7_5_INCONSISTENT_BAND_HZ: float = 2000.0

#: The two A-weighted sound pressure levels of the same example, in decibels,
#: printed in the running text rather than in the table: PDF page 321, printed
#: folio 309, "L_A = 108.4 dBA (without the enclosure)", and PDF page 323,
#: printed folio 311, "L_A = 89.8 dBA (with the enclosure)". Each is printed to
#: a tenth, so their difference, D_pA, carries a tenth of its own; the book
#: never prints it.
BARRON_EXAMPLE_7_8_LPA_WITHOUT_DBA: float = 108.4
BARRON_EXAMPLE_7_8_LPA_WITH_DBA: float = 89.8

# ---------------------------------------------------------------------------
# Peters, Smith and Hollins (2011), Example 1.13: one enclosure, two machines
# ---------------------------------------------------------------------------

#: Example 1.13 on PDF pages 31 and 32, printed folios 16 and 17: two machines
#: measured at one reception point in octave bands, the octave band centres in
#: hertz, and the attenuation of one enclosure in decibels. The example carries
#: its own A-weighting, the ISO 3744 Annex E values rounded to whole decibels.
SMITH_EXAMPLE_1_13_OCTAVES_HZ: tuple[float, ...] = (
    63.0,
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
    8000.0,
)
SMITH_EXAMPLE_1_13_ATTENUATION_DB: tuple[float, ...] = (
    4.0,
    9.0,
    15.0,
    21.0,
    24.0,
    30.0,
    27.0,
    26.0,
)

#: The two source spectra of that example, in decibels, and the A-weighted
#: attenuation the answer box on folio 17 gives for each.
SMITH_EXAMPLE_1_13_MACHINES: dict[str, tuple[tuple[float, ...], float]] = {
    "machine A": ((105.0, 107.0, 99.0, 94.0, 91.0, 87.0, 82.0, 79.0), 14.0),
    "machine B": ((68.0, 79.0, 82.0, 87.0, 92.0, 96.0, 89.0, 81.0), 27.0),
}

# ---------------------------------------------------------------------------
# Harris (1991), Appendix 3: four enclosure cases
# ---------------------------------------------------------------------------

#: The octave levels at the worker's station before any treatment, in
#: decibels, over the bands of Table 7-5 above, from Figure A3-2 on PDF page
#: 135, printed folio 125, and Figure A3-8 on PDF page 141, printed folio 131,
#: which both start from the same spectrum; and the A-weighted level the
#: figures print for it.
HARRIS_BEFORE_DB: tuple[float, ...] = (108.0, 103.0, 99.0, 104.0, 101.0, 85.0)
HARRIS_BEFORE_DBA: float = 107.0

#: The four cases of those two figures: the per-band reduction of each, in
#: decibels, and the A-weighted level the figure prints once it is applied.
#: Example 1 prints its insertion loss as one row; Example 3 prints a room
#: adjustment and a transmission loss, added here, which is exact arithmetic on
#: the printed lines but a construction rather than a quotation. Example 3 is a
#: personnel enclosure, nearer ISO 11957 in subject, and is kept because the
#: estimator is the same formula. The book adds bands pairwise from a
#: difference table (Figure A3-1, PDF page 130, printed folio 120), which costs
#: about 0,7 dB at worst: Example 1(a) prints 94 dBA where its own pairwise
#: chain lands on 94,5 and an energy sum gives 94,7, so a comparison belongs on
#: the reduction and never on the rounded total.
HARRIS_CASES: dict[str, tuple[tuple[float, ...], float]] = {
    "Example 1(a), plywood": ((13.0, 11.0, 12.0, 12.0, 13.0, 15.0), 94.0),
    "Example 1(b), plywood and insulation": (
        (18.0, 17.0, 23.0, 30.0, 38.0, 40.0),
        81.0,
    ),
    "Example 3(a), plain wall": ((16.0, 24.0, 40.0, 49.0, 50.0, 41.0), 77.0),
    "Example 3(b), insulated wall": ((24.0, 36.0, 50.0, 58.0, 61.0, 46.0), 68.0),
}

# ---------------------------------------------------------------------------
# Schirmer (2006, 2023), 10.8.1: the leak ratio of a real enclosure
# ---------------------------------------------------------------------------

#: An enclosure 6 m by 5 m by 3 m high with a 0,25 m2 exhaust opening. The 2nd
#: edition prints its walls and roof as S_K = 96 m2 - 0,25 m2 = 95,75 m2 on PDF
#: page 323, printed folio 303, and the opening fraction
#: q = S_O/(S_K + S_O) = 2,6e-3 on PDF page 324, printed folio 304; the 3rd
#: edition prints the same numbers at the same clause, on PDF pages 517 and
#: 518, printed folios 499 and 500. The 96 m2 is the book's own modelling
#: choice, walls and roof with the opening counted in and the floor left out.
#: The areas in square metres; q to the two significant figures printed.
SCHIRMER_OPENING_M2: float = 0.25
SCHIRMER_SURFACE_M2: float = 96.0
SCHIRMER_WALLS_M2: float = 95.75
SCHIRMER_LEAK_RATIO: float = 2.6e-3

# ---------------------------------------------------------------------------
# Suva 66026.d (2010) and IFA-LSA 01-243 (2014)
# ---------------------------------------------------------------------------

#: Suva 66026.d, clause 6.2.1 on PDF page 17, printed folio 15: the
#: manufacturer's octave sound power levels of a converter set, the octave band
#: centres in hertz and the levels in decibels, of which the guide says "Diese
#: Werte ergeben L_WA = 104 dB". The guide prints the integer alone.
SUVA_OCTAVES_HZ: tuple[float, ...] = (
    63.0,
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
    8000.0,
)
SUVA_LW_DB: tuple[float, ...] = (91.0, 98.0, 102.0, 101.0, 99.0, 98.0, 91.0, 85.0)
SUVA_LWA_DB: float = 104.0

#: IFA-LSA 01-243, Anhang: the two installed enclosures whose A-weighted level
#: at the workstation is printed both before and after, and the reduction the
#: sheet prints, in decibels: Beispiel 1 on PDF page 22, printed folio 22, and
#: Beispiel 3 with its level before on folio 23 and after on folio 25 (PDF
#: pages 23 and 25). The levels are printed rounded ("rund 100 dB(A)",
#: "ca. 104 dB"). Its second example is left out: the level with the enclosure
#: in place is never printed there, so the only way to feed it is to subtract
#: the printed 21 dB from the printed 95 dB, which is the answer run backwards.
IFA_LSA_01_243_ENCLOSURES: dict[str, tuple[float, float, float]] = {
    # without, with, the printed reduction, all in dB(A)
    "punching machine, Beispiel 1": (100.0, 80.0, 20.0),
    "emery machine, Beispiel 3": (104.0, 84.0, 20.0),
}

# ---------------------------------------------------------------------------
# The documents ISO 11957 delegates to
# ---------------------------------------------------------------------------

#: ISO 3741:2010 9.1.2, the clause 6.4 of ISO 11957 sends the background
#: correction to. It prints Equation (14) on PDF page 28, printed folio 19, and
#: evaluates it at two arguments on PDF page 29, printed folio 20: "K1i shall be
#: set to 1,26 dB (the value for dLpi = 6 dB)" at 200 Hz and below and at
#: 6 300 Hz and above, and "to 0,46 dB (the value for dLpi = 10 dB)" from 250 Hz
#: to 5 000 Hz. The margin in decibels against the printed K_1 in decibels.
ISO3741_K1_PRINTED_DB: dict[float, float] = {6.0: 1.26, 10.0: 0.46}

#: ISO 717-1:2013 Annex C, Table C.1, PDF page 24, printed folio 16: the two
#: A-weighted spectra the adaptation terms are formed against, in decibels,
#: over the sixteen one-third-octave rating bands from 100 Hz to 3 150 Hz.
ISO717_1_SPECTRUM_ONE_DB: tuple[float, ...] = (
    -29.0,
    -26.0,
    -23.0,
    -21.0,
    -19.0,
    -17.0,
    -15.0,
    -13.0,
    -12.0,
    -11.0,
    -10.0,
    -9.0,
    -9.0,
    -9.0,
    -9.0,
    -9.0,
)
ISO717_1_SPECTRUM_TWO_DB: tuple[float, ...] = (
    -20.0,
    -20.0,
    -18.0,
    -16.0,
    -15.0,
    -14.0,
    -13.0,
    -12.0,
    -11.0,
    -9.0,
    -8.0,
    -9.0,
    -10.0,
    -11.0,
    -13.0,
    -15.0,
)

#: The "-10 lg sum" the same table prints under each spectrum, in decibels.
#: Both are truncated rather than rounded, which the ellipsis of the table
#: marks: "sum = 147,619 9 ... x 10-5", "-10 lg sum = 28,308...".
ISO717_1_PRINTED_SUM_TERM_DB: tuple[float, float] = (28.308, 26.859)

#: ISO 3744:2010 Annex E, Table E.1, PDF page 69, printed folio 60: the
#: one-third-octave C_k over the same sixteen bands, in decibels. Annex A of
#: ISO 11957 takes the spectrum unweighted and an attenuation A_i that is
#: positive where the weighting takes level away, so A_i = -C_k and the printed
#: A-weighted spectra are de-weighted with these before they are handed over.
ISO3744_TABLE_E1_CK_DB: tuple[float, ...] = (
    -19.1,
    -16.1,
    -13.4,
    -10.9,
    -8.6,
    -6.6,
    -4.8,
    -3.2,
    -1.9,
    -0.8,
    0.0,
    0.6,
    1.0,
    1.2,
    1.3,
    1.2,
)

# ---------------------------------------------------------------------------
# Three cabins rated to clause 8 of ISO 11957 by the laboratories that measured
# them, each D_p over the sixteen rating bands from 100 Hz to 3 150 Hz
# ---------------------------------------------------------------------------

#: SGS-CSTC Standards Technical Services, Shunde Branch, test report
#: SDHL260400706101HI of 7 May 2026, PDF page 3, folio "Page 3 of 4": D_p of a
#: meeting pod measured in a 200 m3 reverberation room, in decibels, rated there
#: at D_p,w = 32 dB. The report also prints 36,2 dB at 4 000 Hz and 36,4 dB at
#: 5 000 Hz, which the rating does not read.
SGS_POD_DP_DB: tuple[float, ...] = (
    11.0,
    22.5,
    24.0,
    26.0,
    29.3,
    32.1,
    28.3,
    30.6,
    31.9,
    34.9,
    34.5,
    33.2,
    32.1,
    33.7,
    32.6,
    33.2,
)
SGS_POD_OUTSIDE_RATING_DB: tuple[float, float] = (36.2, 36.4)
SGS_POD_RATING_DB: int = 32

#: AGH University, Department of Mechanics and Vibroacoustics, report 5.5.130.
#: of August 2023, PDF page 10, folio "Strona 10 z 10": D of an acoustic booth
#: measured in a 180,4 m3 reverberation room, in decibels, rated there at
#: D_p,w = 22 dB. The printed table runs from 50 Hz to 10 kHz; the eight bands
#: outside the rating range play no part in it.
AGH_BOOTH_DP_DB: tuple[float, ...] = (
    10.0,
    20.1,
    14.7,
    19.3,
    20.6,
    19.9,
    23.2,
    20.4,
    17.6,
    19.1,
    18.8,
    20.2,
    21.8,
    24.4,
    26.8,
    28.3,
)
AGH_BOOTH_RATING_DB: int = 22

#: AGH University, Laboratorium Akustyki Technicznej, report 5.5.130.680 of
#: October 2017, PDF page 11, folio "Strona 11 z 12": D_p of a telephone booth
#: measured in the same room, tabulated to whole decibels, in decibels, and
#: rated there at D_p,w = 30 dB. The plotted curve on the same card carries
#: finer values than the table, so the laboratory rated unrounded data.
EURONOVA_BOOTH_DP_DB: tuple[float, ...] = (
    12.0,
    18.0,
    14.0,
    15.0,
    20.0,
    25.0,
    28.0,
    31.0,
    31.0,
    33.0,
    34.0,
    34.0,
    31.0,
    30.0,
    32.0,
    33.0,
)
EURONOVA_BOOTH_RATING_DB: int = 30

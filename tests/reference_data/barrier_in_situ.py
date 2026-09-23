#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for an outdoor barrier measured in situ (ISO 10847:1997).

ISO 10847:1997 prints no worked example. The people who followed it published
their campaigns, and five documents carry a barrier measurement from the
printed levels to the printed insertion loss; two more reprint a table or a
class ISO 10847 states without an example of its own. Every number here was
read on the printed page, and each banner names the document, the printed
folio and the PDF page, and says which part of clause 8.2 the numbers reach:
a campaign that agrees with the subtraction says nothing about the wind
classes, the background table or the receiver correction.

The documents are:

* W. Lindeman, "Comparison of Noise Barrier Insertion-Loss Methodologies",
  Transportation Research Record 1033, Transportation Research Board, 1985.
* R. Cordero and others, "Metodología experimental para medida pérdidas por
  inserción de pantallas acústicas de carretera", 41 Congreso Nacional de
  Acústica, León, 2010, paper AAM_026.
* A. Jagniatinskis, B. Fiks and M. Mickaitis, "Determination of Insertion Loss
  of Acoustic Barriers under Specific Conditions", Procedia Engineering 187,
  2017.
* L. Rodiño and F. Masson, "Diseño e implementación de una barrera acústica
  para motores fuera de borda", XIII Congreso Argentino de Acústica, Buenos
  Aires, 2015, paper AdAA2015-A009.
* C. S. Y. Lee and G. G. Fleming, *Measurement of Highway-Related Noise*,
  FHWA-PD-96-046, Federal Highway Administration, May 1996.
* CEN/TS 16272-7:2015, which reprints the background table.

The tie-break clause 10 c) leaves open is Rule A of ISO 80000-1:2009 Annex B,
whose printed examples are in :mod:`reference_data.rounding`.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Cordero and others (2010): a window in the place of a barrier
# ---------------------------------------------------------------------------

#: Tabla 1 "Niveles equivalentes de los puntos de evaluación", printed folio 5
#: (PDF page 5): the four A-weighted levels of each case, in the argument order
#: of ``measured_insertion_loss_direct``, that is (L_ref,B, L_ref,A, L_r,B,
#: L_r,A), in decibels. "Antes" is the window open and "despues" the window
#: closed, so the two roles of 8.2.1 are filled by a window rather than by a
#: barrier: what these numbers anchor is the subtraction and the reporting
#: rule, not the procedure. The second case is the same campaign with the
#: background deliberately raised at the measurement point alone.
CORDERO_TABLA_1_DBA: dict[str, tuple[float, float, float, float]] = {
    "sin ruido": (61.0, 64.3, 55.6, 46.1),
    "con ruido": (61.2, 63.7, 56.0, 49.0),
}

#: Tabla 2, printed folio 6 (PDF page 6): the insertion loss of each case
#: reported to the nearest decibel, in decibels, which the running text prints
#: as "13 dBA".
CORDERO_TABLA_2_DBA: dict[str, int] = {"sin ruido": 13, "con ruido": 10}

#: Folio 6: the one value the campaign prints before rounding, "9,5 dBA", for
#: the case with the background raised at the receiver alone.
CORDERO_UNROUNDED_CON_RUIDO_DBA: float = 9.5

# ---------------------------------------------------------------------------
# Lindeman (1985): one barrier by both methods
# ---------------------------------------------------------------------------

#: TABLE 8 "Calculations for Insertion Loss Based on Direct Method Test at
#: Site 1", printed folio 39 (PDF page 7): the runs whose four levels and
#: insertion loss are all printed, in the argument order of
#: ``measured_insertion_loss_direct``, in dBA. Runs 4 and 5 print no "before"
#: reference level and no insertion loss.
LINDEMAN_TABLE_8_DBA: dict[str, tuple[float, float, float, float]] = {
    "run 2": (64.5, 67.1, 58.5, 53.6),
    "run 3": (63.1, 65.5, 57.3, 51.0),
}

#: TABLE 8 column (7), "Insertion Loss", for those two runs, in dBA.
LINDEMAN_TABLE_8_INSERTION_LOSS_DBA: dict[str, float] = {"run 2": 7.5, "run 3": 8.7}

#: Run 1 of TABLE 8, in the same order, and the insertion loss its column (7)
#: prints, in dBA. Its own four levels give 5,8 dB, and TABLES 4 and 5 on
#: printed folio 37 (PDF page 5) reach two of those levels a second time
#: through their own arithmetic, with column (3) printing their difference as
#: 6,6 dB, so what is defective is the printed insertion loss and not a level.
#: The note's mean, 7,5 dBA, is the mean of the defective column. Neither is an
#: expected value.
LINDEMAN_TABLE_8_RUN_1_DBA: tuple[float, float, float, float] = (64.2, 65.4, 57.6, 53.0)
LINDEMAN_TABLE_8_RUN_1_PRINTED_DBA: float = 6.2

#: TABLE 13 "Calculations Based on Indirect Measured Method", printed folio 41
#: (PDF page 9): five runs, with the equivalent site as the "before" pair
#: (MIC 3 the reference, MIC 4 the receiver) and the barrier site as the
#: "after" one (MIC 1 and MIC 2), all in dBA. Run 4 takes its "before"
#: receiver level from TABLE 12 on the same folio, which prints 61,1 where
#: column (2) of TABLE 13 repeats run 3's 60,2. The table contradicts itself
#: there rather than leaving the choice open: its own column (3) prints 7,7 for
#: that run, and 68,8 - 60,2 is 8,6. Both receivers stand in the open, so C_r
#: and C'_r are zero and the runs exercise the site pairing of 8.2.2 rather
#: than the facade branch.
LINDEMAN_TABLE_13_DBA: dict[str, tuple[float, ...]] = {
    "reference before": (66.7, 72.2, 66.1, 68.8, 67.4),
    "reference after": (65.4, 67.1, 65.5, 65.9, 66.9),
    "receiver before": (61.2, 65.3, 60.2, 61.1, 62.4),
    "receiver after": (53.0, 53.6, 51.0, 54.6, 52.7),
}

#: TABLE 13 column (7) run by run, and the mean its note reports, in dBA.
LINDEMAN_TABLE_13_INSERTION_LOSS_DBA: tuple[float, ...] = (6.9, 6.6, 8.6, 3.6, 9.2)
LINDEMAN_TABLE_13_MEAN_DBA: float = 7.0

#: The "before" receiver level column (2) of TABLE 13 misprints for run 4, a
#: repeat of run 3's, in dBA.
LINDEMAN_TABLE_13_RUN_4_MISPRINT_DBA: float = 60.2

# ---------------------------------------------------------------------------
# FHWA-PD-96-046 (1996): the manual's own worked example and wind classes
# ---------------------------------------------------------------------------

#: Clause 6.6.3 "Insertion Loss", printed folio 84 (PDF page 101), and the same
#: example again in FHWA-HEP-18-065 on printed folios 108 and 109: the levels
#: its worked example lists, in decibels. L_edge is an FHWA reflections and
#: edge-diffraction adjustment defined in clause 6.6.2, with no counterpart
#: anywhere in ISO 10847, so it is applied outside the function under test
#: rather than fed to it.
FHWA_6_6_3_REFERENCE_BEFORE_DB: float = 77.7
FHWA_6_6_3_REFERENCE_AFTER_DB: float = 78.2
FHWA_6_6_3_RECEIVER_BEFORE_DB: float = 65.0
FHWA_6_6_3_EDGE_DB: float = -0.5

#: The example contradicts itself, and that is the whole of the difference
#: between its two published answers: the list gives a receiver level of
#: 56,3 dB, the expression under it types 56,2 dB, and the FHWA Noise Barrier
#: Design Handbook prints 8,7 dB for the first (clause 15.1.2.1) where these
#: two manuals print 8,8 dB for the second. The "after" receiver level and the
#: insertion loss of each reading, in decibels.
FHWA_6_6_3_PRINTED_DB: dict[str, tuple[float, float]] = {
    "as the expression types it": (56.2, 8.8),
    "as the list gives it": (56.3, 8.7),
}

#: Table 3 "Classes of wind conditions", printed folio 35 (PDF page 52): the
#: three printed intervals of the source-to-receiver vector component of the
#: wind, in metres per second. The upwind row prints as an interval, "-1 to
#: -5", where ISO 10847 Table 1 prints "+ 1 to - 5"; that is the corroboration
#: the errata entry rests on. FHWA prints one flat set of classes with no
#: distance split, so it is read against the short-distance table of
#: ISO 10847, the only one with an upwind class at all. Neither document says
#: which class a shared endpoint belongs to.
FHWA_TABLE_3_WIND_CLASSES_M_S: dict[str, tuple[float, float]] = {
    "upwind": (-5.0, -1.0),
    "calm": (-1.0, 1.0),
    "downwind": (1.0, 5.0),
}

# ---------------------------------------------------------------------------
# CEN/TS 16272-7:2015: the background table reprinted
# ---------------------------------------------------------------------------

#: Clause 7.3.7 and Table 4, printed folio 14 (PDF page 15): the same
#: correction as ISO 10847 Table 3 in two grouped rows, the margins of each row
#: against the correction to add, in decibels. The grouping is part of what it
#: says: two rows and not six.
CEN_TS_16272_7_TABLE_4_DB: tuple[tuple[tuple[float, ...], float], ...] = (
    ((4.0, 5.0), -2.0),
    ((6.0, 7.0, 8.0, 9.0), -1.0),
)

#: The same clause: the margin under which the results are invalid and the
#: margin its prose asks for, in decibels.
CEN_TS_16272_7_MINIMUM_MARGIN_DB: float = 4.0
CEN_TS_16272_7_PREFERRED_MARGIN_DB: float = 10.0

# ---------------------------------------------------------------------------
# Jagniatinskis and others (2017): a highway campaign
# ---------------------------------------------------------------------------

#: Table 1 on printed folio 293 (PDF page 5) and the conclusion on folio 294
#: (PDF page 6): three A-weighted results, each as the level at the reference
#: point, the level at the site point and the "environment correction" the
#: paper prints, in dBA and with the minus sign the table prints it with, then
#: the insertion loss it reports. That correction is the "before" difference
#: of 8.2.1 printed as a single number with its sign reversed,
#: 76,0 - 56,3 - 9,1 = 10,6 dBA being how the table closes, so the two levels
#: behind it are free. Site 1 is a 5 m barrier with the receiver 30 m away and
#: site 2 a separate 6 m barrier at 20 m. The third entry is site 1 read from
#: its total level instead of the residual one, which is where the 8,0 dBA of
#: folio 294 comes from. The residual levels came from an ISO 1996 extraction
#: of the connected-road traffic, which is not the background treatment of
#: ISO 10847 6.4.
JAGNIATINSKIS_TABLE_1_DBA: dict[str, tuple[float, float, float, float]] = {
    "site 1, residual": (76.0, 56.3, -9.1, 10.6),
    "site 2, residual": (75.4, 55.0, -6.9, 13.5),
    "site 1, total": (76.0, 58.9, -9.1, 8.0),
}

# ---------------------------------------------------------------------------
# Rodino and Masson (2015): a screen with no reference microphone
# ---------------------------------------------------------------------------

#: Tabla 2 on printed folio 7 (PDF page 7): the level at the crew position
#: without the screen and with it, for three engine settings, unweighted ("Z")
#: and A-weighted ("A"), in decibels, with the insertion loss the table
#: reports. No reference microphone was used, so 8.2.1 degenerates to the plain
#: difference of the two receiver levels. What that anchors is the sign,
#: positive for a screen that works, and the degenerate reduction itself; the
#: paper cites ISO 14509 rather than ISO 10847, and the screen sits in the near
#: field of the source.
RODINO_TABLA_2_DB: dict[str, tuple[float, float, float]] = {
    "Z, motor 100%": (117.6, 111.9, 5.7),
    "Z, motor 75%": (106.5, 104.0, 2.5),
    "Z, punto muerto": (73.8, 73.3, 0.5),
    "A, motor 100%": (89.0, 87.9, 1.1),
    "A, motor 75%": (81.5, 80.0, 1.5),
    "A, punto muerto": (55.4, 53.7, 1.7),
}

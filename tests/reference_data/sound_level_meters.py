#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound level meters: IEC 61672-1:2013 Tables 3, 4, 5 and B.1, IEC 61672-3:2013 Clause 22.

Transcribed from the rasterised pages of BS EN 61672-1:2013 and BS EN
61672-3:2013 (PDF page = printed folio + 2 in both), as the page prints them:
decimal commas, the "±" of a symmetric limit and the "+a; -b" of an
asymmetric one, thousands grouped with a space. The tests parse these strings
rather than share numbers with the library, so a slip in either transcription
shows as a mismatch.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# BS EN 61672-1:2013 Table 3 (folio 22): the acceptance limits, class 1 then
# class 2, at the nominal frequencies the periodic tests of IEC 61672-3 read,
# the nine octaves from 63 Hz to 16 kHz of 13.4 (125 Hz and 8 kHz are those of
# the acoustical test of 12.7 too). Class 2 is tested to 8 kHz only.
# ---------------------------------------------------------------------------
IEC61672_1_TABLE_3_TEST_LIMITS: tuple[tuple[str, str, str], ...] = (
    ("63", "±1,0", "±2,0"),
    ("125", "±1,0", "±1,5"),
    ("250", "±1,0", "±1,5"),
    ("500", "±1,0", "±1,5"),
    ("1 000", "±0,7", "±1,0"),
    ("2 000", "±1,0", "±2,0"),
    ("4 000", "±1,0", "±3,0"),
    ("8 000", "+1,5; -2,5", "±5,0"),
    ("16 000", "+2,5; -16,0", "+5,0; -∞"),
)

# ---------------------------------------------------------------------------
# BS EN 61672-1:2013 Table 4 (folio 25): reference 4 kHz toneburst responses
# and acceptance limits. Columns: toneburst duration T_b in ms, the reference
# response of LAFmax - LA (Eq. (7)), of LAE - LA (Eq. (8)), then the class 1
# and class 2 acceptance limits the two columns share.
# ---------------------------------------------------------------------------
IEC61672_1_TABLE_4_F_AND_E: tuple[tuple[str, str, str, str, str], ...] = (
    ("1 000", "0,0", "0,0", "±0,5", "±1,0"),
    ("500", "-0,1", "-3,0", "±0,5", "±1,0"),
    ("200", "-1,0", "-7,0", "±0,5", "±1,0"),
    ("100", "-2,6", "-10,0", "±1,0", "±1,0"),
    ("50", "-4,8", "-13,0", "±1,0", "+1,0; -1,5"),
    ("20", "-8,3", "-17,0", "±1,0", "+1,0; -2,0"),
    ("10", "-11,1", "-20,0", "±1,0", "+1,0; -2,0"),
    ("5", "-14,1", "-23,0", "±1,0", "+1,0; -2,5"),
    ("2", "-18,0", "-27,0", "+1,0; -1,5", "+1,0; -2,5"),
    ("1", "-21,0", "-30,0", "+1,0; -2,0", "+1,0; -3,0"),
    ("0,5", "-24,0", "-33,0", "+1,0; -2,5", "+1,0; -4,0"),
    ("0,25", "-27,0", "-36,0", "+1,0; -3,0", "+1,5; -5,0"),
)

# The second block of Table 4: LASmax - LA (Eq. (7)), with limits of its own.
IEC61672_1_TABLE_4_S: tuple[tuple[str, str, str, str], ...] = (
    ("1 000", "-2,0", "±0,5", "±1,0"),
    ("500", "-4,1", "±0,5", "±1,0"),
    ("200", "-7,4", "±0,5", "±1,0"),
    ("100", "-10,2", "±1,0", "±1,0"),
    ("50", "-13,1", "±1,0", "+1,0; -1,5"),
    ("20", "-17,0", "+1,0; -1,5", "+1,0; -2,0"),
    ("10", "-20,0", "+1,0; -2,0", "+1,0; -3,0"),
    ("5", "-23,0", "+1,0; -2,5", "+1,0; -4,0"),
    ("2", "-27,0", "+1,0; -3,0", "+1,0; -5,0"),
)

# ---------------------------------------------------------------------------
# BS EN 61672-1:2013 Table 5 (folio 28): reference differences LCpeak - LC and
# acceptance limits. Columns: number of cycles in the test signal, nominal
# frequency in Hz, reference difference, class 1 and class 2 limits.
# ---------------------------------------------------------------------------
IEC61672_1_TABLE_5: tuple[tuple[str, str, str, str, str], ...] = (
    ("one", "31,5", "2,5", "±2,0", "±3,0"),
    ("one", "500", "3,5", "±1,0", "±2,0"),
    ("one", "8 000", "3,4", "±2,0", "±3,0"),
    ("positive half cycle", "500", "2,4", "±1,0", "±2,0"),
    ("negative half cycle", "500", "2,4", "±1,0", "±2,0"),
)

# ---------------------------------------------------------------------------
# BS EN 61672-1:2013 Table B.1 (folios 42 and 43): maximum-permitted
# uncertainties of measurement for a coverage probability of 95 %, in dB
# unless the cell says otherwise. Columns: requirement, table or subclause,
# maximum-permitted uncertainty, as printed.
# ---------------------------------------------------------------------------
IEC61672_1_TABLE_B1: tuple[tuple[str, str, str], ...] = (
    ("Directional response: θ = 30°", "Table 2; 250 Hz to 1 kHz", "0,25"),
    ("Directional response: θ = 30°", "Table 2; >1 kHz to 2 kHz", "0,25"),
    ("Directional response: θ = 30°", "Table 2; >2 kHz to 4 kHz", "0,35"),
    ("Directional response: θ = 30°", "Table 2; >4 kHz to 8 kHz", "0,45"),
    ("Directional response: θ = 30°", "Table 2; >8 kHz to 12,5 kHz", "0,55"),
    ("Directional response: θ = 90° & 150°", "Table 2; 250 Hz to 1 kHz", "0,25"),
    ("Directional response: θ = 90° & 150°", "Table 2; >1 kHz to 2 kHz", "0,45"),
    ("Directional response: θ = 90° & 150°", "Table 2; >2 kHz to 4 kHz", "0,45"),
    ("Directional response: θ = 90° & 150°", "Table 2; >4 kHz to 8 kHz", "0,85"),
    ("Directional response: θ = 90° & 150°", "Table 2; >8 kHz to 12,5 kHz", "1,15"),
    ("Frequency weightings A, C, Z", "Table 3, 10 Hz to 4 kHz", "0,60"),
    ("Frequency weightings A, C, Z", "Table 3, >4 kHz to 10 kHz", "0,70"),
    ("Frequency weightings A, C, Z", "Table 3, >10 kHz to 20 kHz", "1,00"),
    ("A vs. C or Z at 1 kHz", "5.5.9", "0,20"),
    ("Level linearity deviation", "5.6.5", "0,30"),
    ("1 dB to 10 dB change in level", "5.6.6", "0,25"),
    ("F and S decay rates", "5.8.2", "3,50 dB/s for F; 0,40 dB/s for S"),
    ("F vs. S level at 1 kHz", "5.8.3", "0,20"),
    ("Toneburst response", "5.9.2, Table 4", "0,30"),
    ("Repeated tonebursts", "5.10.1, Table 4", "0,30"),
    ("Overload indication", "5.11.3", "0,25"),
    ("C-weighted peak sound levels", "5.13.3, Table 5", "0,35"),
    ("Stability during continuous operation", "5.14.2", "0,10"),
    ("High-level stability", "5.15.2", "0,10"),
    ("Analogue electrical output", "5.19.2", "0,15"),
    ("Power supply voltage", "5.23.2", "0,20"),
    ("Static pressure influence", "6.2.1; 6.2.2", "0,30"),
    ("Air temperature influence", "6.3.3; 6.3.4", "0,30"),
    ("Humidity influence", "6.4", "0,30"),
    ("Combined temperature and humidity", "6.3.3, 6.3.4, 6.4", "0,35"),
    ("AC and radio-frequency fields", "6.6.6", "0,30"),
)

# ---------------------------------------------------------------------------
# The acceptance limits IEC 61672-3:2013 points to in the text of IEC
# 61672-1:2013, as printed: 5.5.9 (folio 21), 5.6.5 (23), 5.8.3 (24),
# 5.11.3 (27), 5.14.2 (28) and 5.15.2 (29). Class 1 then class 2; a clause
# that does not distinguish the classes prints one figure for both.
# ---------------------------------------------------------------------------
IEC61672_1_TEXT_LIMITS: dict[str, tuple[str, str]] = {
    "5.5.9": ("± 0,2", "± 0,2"),
    "5.6.5": ("±0,8", "±1,1"),
    "5.8.3": ("±0,1", "±0,1"),
    "5.11.3": ("1,5", "1,5"),
    "5.14.2": ("±0,1", "±0,3"),
    "5.15.2": ("±0,1", "±0,3"),
}

# ---------------------------------------------------------------------------
# BS EN 61672-3:2013 22 r), s) and t) (folios 18 and 19): the statements of
# the documentation, as printed, with "class Y" and the date "–" for the
# laboratory to fill in ("replace class Y with class 1 or class 2 ... replace
# date '–' by the year of issue of this second edition").
# ---------------------------------------------------------------------------
IEC61672_3_STATEMENT_R = (
    "The sound level meter submitted for testing successfully completed the "
    "periodic tests of IEC 61672-3:–, for the environmental conditions under "
    "which the tests were performed. As evidence was publicly available, from "
    "an independent testing organization responsible for approving the results "
    "of pattern-evaluation tests performed in accordance with IEC 61672-2:–, to "
    "demonstrate that the model of sound level meter fully conformed to the "
    "class Y specifications in IEC 61672-1:–, the sound level meter submitted "
    "for testing conforms to the class Y specifications of IEC 61672-1:–."
)
IEC61672_3_STATEMENT_S = (
    "The sound level meter submitted for testing successfully completed the "
    "periodic tests of IEC 61672-3:–, for the environmental conditions under "
    "which the tests were performed. However, no general statement or "
    "conclusion can be made about conformance of the sound level meter to the "
    "full specifications of IEC 61672-1:– because (a) evidence was not publicly "
    "available, from an independent testing organization responsible for "
    "pattern approvals, to demonstrate that the model of sound level meter "
    "fully conformed to the class Y specifications in IEC 61672-1:– or "
    "correction data for acoustical test of frequency weighting were not "
    "provided in the Instruction Manual and (b) because the periodic tests of "
    "IEC 61672-3:– cover only a limited subset of the specifications in "
    "IEC 61672-1:–."
)
IEC61672_3_STATEMENT_T = (
    "The sound level meter submitted for periodic testing did not successfully "
    "complete the class Y tests of IEC 61672-3:–. The sound level meter did not "
    "conform to the class Y specifications of IEC 61672-1:–."
)

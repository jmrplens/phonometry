#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Ver & Beranek 2e TABLE 14.1, read a second time from the page.

The catalogue in :mod:`phonometry.solids.damping` and this module were
transcribed from the rendered page by two readers who never saw each other's
work, and compared cell by cell before either was kept: 136 cells, no
difference. This is the second reading, kept as the oracle the tests check
against.

Every value is **as the page prints it**, in the page's own units: the loss
factor is dimensionless, the three temperatures are in degrees Fahrenheit and
the four moduli are in pounds per square inch, written in the table's own
``NeM`` notation where ``M`` is the power of ten. A string that is not a number
is a cell corrupted in the printing; the three of them are registered in
``docs/ERRATA.md``. Keeping the printed units here rather than the converted
ones is what lets the tests check the conversion as well as the transcription.
"""

from __future__ import annotations

#: The columns of the table, in printed order: the greatest loss factor, the
#: three temperatures at which it occurs, and the four moduli.
VER_BERANEK_14_1_COLUMNS: tuple[str, ...] = (
    "ηmax",
    "10 Hz",
    "100 Hz",
    "1000 Hz",
    "Emax",
    "Emin",
    "Etrans",
    "EI,max",
)

#: One entry per printed row: the material as the page names it, then one
#: value per column of :data:`VER_BERANEK_14_1_COLUMNS`.
VER_BERANEK_14_1: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Antiphon-13", ("1.8", "25", "75", "120", "3e5", "1.2e3", "1.9e4", "3.e3e")),
    ("blachford Aquaplas", ("0.5", "50", "80", "125", "1.6e6", "3e4", "2.2e5", "1.1e5")),
    ("Barry Controls H-326", ("0.8", "−40", "−25", "−10", "6e5", "3e3", "4.2e4", "3.4e4")),
    ("Dow Corning Sylgard 188", ("0.6", "60", "80", "110", "2.2e4", "3e2", "2.6e3", "1.5e3")),
    ("EAR C-1002", ("1.9", "23", "55", "90", "3e5", "2e2", "7.7e3", "1.5e4")),
    ("EAR C-2003", ("1.0", "45", "70", "100", "8e5", "6e2", "2.2e4", "2.2e4")),
    ("lord LD-400", ("0.7", "50", "80", "125", "3e6", "3.3e3", "1e5", "7e4")),
    ("Soundcoat DYAD 601", ("1.0", "15", "50", "75", "3e5", "1.5e2", "6.7e3", "6.7e3")),
    ("Soundcoat DYAD 606", ("1.0", "70", "100", "130", "3G5", "1.2e2", "6e3", "6e3")),
    ("Soundcoat DYAD 609", ("1.0", "125", "150", "185", "2e5", "6e2", "1.1e4", "1.1e4")),
    ("Soundcoat N", ("1.5", "15", "30", "70", "3e5", "7e1", "4.6e3", "6.9e3")),
    ("3M ISD-110", ("1.7", "80", "115", "150", "3e4", "3e1", "1e3", "1.7e3")),
    ("3M ISD-112", ("1.2", "10", "40", "80", "1.3e5", "8e1", "3.2e3", "3.9e3")),
    ("3M ISD-113", ("1.1", "−45", "−20", "15", "1.5e5", "3e2", "2.1e2", "2.3e2")),
    ("3m 468", ("0.8", "15", "50", "85", "1.4e5", "3e1", "2e3", "1.6e3")),
    ("3M ISD-830", ("1.0", "−75", "−50", "−20", "2e5", "1.5e2", "5.5e3", "5.5e3")),
    ("GE SMRD", ("0.9", "50", "80", "125", "e35", "5e3", "3.9e4", "3.5e4")),
)

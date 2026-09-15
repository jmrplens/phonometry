#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed oracles for a removable screen measured in situ (ISO 11821:1997).

ISO 11821:1997 prints no worked example, so every level pair here was read on
the printed page of another document that subtracts one. Clauses 5.8 and 5.9
are that subtraction, and 5.7 is the energy subtraction of a background, so
what these numbers anchor is the arithmetic and the rounding, not a method:
each banner says where its case sits against the scope of the standard.

The documents are:

* Randall F. Barron, *Industrial Noise Control and Acoustics*, Marcel Dekker,
  New York, 2003. Its electronic edition carries the folio in the text layer
  only, so the folios cited for it are the book's own pagination; the PDF page
  is the folio plus 12.
* Colin H. Hansen, *Noise Control: From Concept to Application*, Taylor &
  Francis, 2005, in the Taylor & Francis e-Library edition of the same year.
  The folio is printed in the running head; the PDF page is the folio plus 8.
* Sound Research Laboratories Ltd, *Noise Control in Industry*, third edition,
  E. & F.N. Spon, London, 1991.
* ISO 140-3:1995, which prints the value of the energy subtraction at the
  lower edge of the ISO 11821 window.

The background correction table of Barron (2003) Table 3-4, its Example 3-6
and the ten motor levels of its Table 3-2 are already in
:mod:`reference_data.silencer_in_situ`, where ISO 11820 uses them, and the four
positions of IFA-LSA 01-234 (2020) Tab. 4.4 with the differences its Tab. 4.5
prints between them are in :mod:`reference_data.spatial_decay`, where
ISO 14257 uses them. They are read from there rather than copied.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Barron (2003), Examples 7-9 and 7-10: a barrier and a screen
# ---------------------------------------------------------------------------

#: Table 7-6, PDF page 328, folio 316: the octave band centres of Example 7-9,
#: in hertz, and the two rows printed under them, in decibels, without the
#: barrier and with it. The case is a concrete barrier around an outdoor
#: transformer station, which the Introduction of ISO 11821 sends to
#: ISO 10847, so what it pins is the subtraction of 5.8 and 5.9.
BARRON_TABLE_7_6_BANDS_HZ: tuple[float, ...] = (
    63.0,
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
    8000.0,
)
BARRON_TABLE_7_6_UNSCREENED_DB: tuple[float, ...] = (
    71.6,
    75.6,
    69.6,
    65.6,
    65.6,
    59.6,
    54.6,
    48.6,
)
BARRON_TABLE_7_6_SCREENED_DB: tuple[float, ...] = (
    64.0,
    66.3,
    57.9,
    51.2,
    48.2,
    39.2,
    31.2,
    24.4,
)

#: PDF page 329, folio 317: the only two band reductions the example works out
#: in prose, in decibels. The other six follow from the two rows of Table 7-6
#: by subtraction and are nowhere on the page, so they are not claimed as
#: printed.
BARRON_EXAMPLE_7_9_PRINTED_REDUCTIONS_DB: dict[str, float] = {
    "63 Hz": 7.6,
    "8000 Hz": 24.2,
}

#: PDF pages 327 and 329, folios 315 and 317: the A-weighted level without the
#: barrier and with it, in decibels, and the reduction printed between them.
BARRON_EXAMPLE_7_9_A_WEIGHTED_DB: tuple[float, float] = (69.6, 55.3)
BARRON_EXAMPLE_7_9_A_REDUCTION_DB: float = 14.3

#: PDF page 326, folio 314: the receiver stands 30 m from the transformer and
#: the barrier 10 m from it, so the position is this far from the barrier, in
#: metres.
BARRON_EXAMPLE_7_9_SCREEN_DISTANCE_M: float = 20.0

#: Example 7-10, PDF pages 331 to 333, folios 319 to 321: a machine screened
#: from its operator indoors, the level in the 1000 Hz octave without the
#: screen and with it, and the reduction, in decibels. Both levels are
#: Barron's own prediction, which is why the case anchors the subtraction and
#: not a measurement. The screen stands 1,00 m from the machine and the
#: operator 3,00 m from it, so the position is 2 m from the screen.
BARRON_EXAMPLE_7_10_DB: tuple[float, float, float] = (92.3, 84.0, 8.3)
BARRON_EXAMPLE_7_10_SCREEN_DISTANCE_M: float = 2.0

# ---------------------------------------------------------------------------
# Hansen (2005), Example 6.23: an open-plan office screen
# ---------------------------------------------------------------------------

#: Example 6.23, PDF pages 325 and 326, folios 317 and 318: the octave band
#: centres in hertz, the total level at the receiver with the screen out and
#: in, in decibels, and the "Reduction due to barrier" row of folio 318, which
#: prints the difference rounded to the whole decibel. The case is an office
#: screen, which ISO 11821 sends to ISO 10053; the rounding is the one 7.4 c)
#: asks for.
HANSEN_EXAMPLE_6_23_BANDS_HZ: tuple[float, float, float] = (500.0, 1000.0, 2000.0)
HANSEN_EXAMPLE_6_23_UNSCREENED_DB: tuple[float, float, float] = (48.8, 55.1, 52.9)
HANSEN_EXAMPLE_6_23_SCREENED_DB: tuple[float, float, float] = (39.0, 39.9, 33.3)
HANSEN_EXAMPLE_6_23_REDUCTION_DB: tuple[int, int, int] = (10, 15, 20)

# ---------------------------------------------------------------------------
# Sound Research Laboratories (1991): three paths round one screen
# ---------------------------------------------------------------------------

#: *Noise Control in Industry*, 3rd edition, PDF page 188, folio 177: the level
#: without the screen, in decibels, and the level with it by the three paths
#: together and by each path alone, in that order. The 71 dB for the three
#: together is the book's decibel-addition rule of thumb rather than the
#: energy sum of the paths, which is 71,687 dB and would make the reduction
#: 8,3 dB; the pair is used exactly as printed.
SRL_1991_UNSCREENED_DB: float = 80.0
SRL_1991_SCREENED_DB: dict[str, float] = {
    "screen": 71.0,
    "path 1": 65.0,
    "path 2": 70.0,
    "path 3": 62.0,
}

# ---------------------------------------------------------------------------
# The background correction of 5.7 at the edges of its window
# ---------------------------------------------------------------------------

#: Hansen (2005) Example 3.25, PDF pages 154 and 155, folios 146 and 147: the
#: level measured, the background under it and the corrected level printed,
#: in decibels. The first margin is exactly 10 dB, the upper edge of the
#: window of 5.7.
HANSEN_EXAMPLE_3_25_DB: tuple[tuple[float, float, float], ...] = (
    (90.0, 80.0, 89.5),
    (86.6, 80.0, 85.5),
)

#: ISO 140-3:1995 6.5, PDF page 13, folio 7: the correction printed for a
#: background 6 dB under the measured level, in decibels, which ISO 3744:2010
#: 8.2.3 prints too. Neither sibling reads the margin the way 5.7 does: both
#: apply it as a floor below 6 dB, where ISO 11821 refuses the measurement.
ISO140_3_SIX_DB_MARGIN_CORRECTION_DB: float = 1.3

# ---------------------------------------------------------------------------
# Barron (2003), Example 3-5: the logarithmic mean under a directivity index
# ---------------------------------------------------------------------------

#: Example 3-5, PDF pages 80 and 81, folios 68 and 69: the energy mean printed
#: over the ten levels of Table 3-2 (PDF page 73, folio 61), which
#: :data:`reference_data.silencer_in_situ.BARRON_EXAMPLE_3_3_LEVELS_DB`
#: carries, and over the ring of three at 41,4 degrees from the vertical,
#: positions 2 to 4, in decibels. Ten positions on a hemisphere, where
#: definition 3.10 reads twelve on a horizontal circle, so what they anchor is
#: the mean and not the index.
BARRON_EXAMPLE_3_5_MEANS_DB: dict[str, float] = {
    "ten positions": 80.6,
    "ring of three": 81.8,
}

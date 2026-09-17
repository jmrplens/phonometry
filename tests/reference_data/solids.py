#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Elastic constants of solids, and the wave speeds printed beside them.

The one table this file carries is the ``h.f_c`` column of Hopkins Table A2,
which is the oracle for :func:`phonometry.solids.thickness_critical_frequency_product`.
It is a strong one: twenty-five materials, one constant, and a heading that
states the speed of sound the column was computed for, so a wrong constant
cannot hide behind a rounding.

Source: Hopkins (2007) Table A2, PDF pages 635-636. The two pages are
landscape and neither prints a folio of its own; they sit between folios 607
and 610. The heading reads ``h.f_c (m.Hz) (assuming c0 = 343 m/s)``.
"""

from __future__ import annotations

#: The speed of sound Table A2 states in its own heading, in m/s.
HOPKINS_A2_SPEED_OF_SOUND_M_S = 343.0

#: ``(material, plate wave speed in m/s, h.f_c in m Hz)`` for every row of
#: Table A2 that prints both columns.
HOPKINS_A2_PLATE_SPEED_AND_HFC: tuple[tuple[str, float, float], ...] = (
    (
        "Aircrete/Autoclaved Aerated Concrete (AAC) blocks (solid) connected with mortar or thin joint compound",
        1900.0,
        34.1,
    ),
    ("Aluminium", 5100.0, 12.7),
    ("Bricks (solid) connected with mortar", 2700.0, 24.0),
    (
        "Calcium-silicate blocks (solid) connected with thin joint compound",
        2500.0,
        25.9,
    ),
    ("Chipboard", 2200.0, 29.5),
    ("Clinker concrete blocks (solid) connected with mortar", 1850.0, 35.1),
    ("Clinker concrete blocks (solid) connected with mortar", 2200.0, 29.5),
    ("Clinker concrete slabs", 1910.0, 34.0),
    ("Concrete – cast in situ", 3800.0, 17.1),
    ("Dense aggregate blocks (solid) connected with mortar", 3200.0, 20.3),
    ("Expanded clay blocks (solid) connected with mortar", 2300.0, 28.2),
    ("Glass", 5200.0, 12.5),
    ("Lightweight aggregate blocks (solid) connected with mortar", 2200.0, 29.5),
    ("Medium Density Fibreboard (MDF)", 2560.0, 25.3),
    ("Mortar", 2450.0, 26.5),
    ("Oriented Strand Board (OSB)", 2570.0, 25.2),
    ("Perspex, plexiglass", 2350.0, 27.6),
    ("Plaster – gypsum based", 1610.0, 40.3),
    ("Plasterboard – combination of flue gas gypsum and natural gypsum", 1810.0, 35.8),
    ("Plasterboard – gypsum with glass fibre and other additives", 2010.0, 32.3),
    ("Plasterboard – natural gypsum", 1490.0, 43.5),
    ("Plywood (Birch)", 3850.0, 16.8),
    ("Sand-cement screed", 3250.0, 20.0),
    ("Steel", 5270.0, 12.3),
    ("Timber (soft wood) used for joists, studs or battens", 5000.0, 13.0),
)

#: The steel row on its own, which also prints a density and a Poisson ratio
#: and so closes the loop back to a Young's modulus:
#: ``(density in kg/m3, Poisson ratio, plate speed in m/s, h.f_c in m Hz)``.
HOPKINS_A2_STEEL: tuple[float, float, float, float] = (7800.0, 0.28, 5270.0, 12.3)

#: The band a structural steel's Young's modulus has to fall in, in pascals.
#: Table A2 prints no modulus at all, which is the reason the inverse exists;
#: this is the sanity check on what the inverse returns, not an oracle, and it
#: is written as a range because that is all a textbook value is.
STRUCTURAL_STEEL_YOUNGS_MODULUS_BAND_PA = (1.95e11, 2.05e11)


# ---------------------------------------------------------------------------
# The rest of Table A2, which is what makes it a catalogue rather than a
# column. Three things the page says are not numbers, and they are the reason
# this transcription exists separately from the library's own copy:
#
#   - footnote b reads, in full, "Estimate", and it sits on most of the
#     Poisson ratios and most of the loss factors;
#   - two densities, one speed and one loss factor are printed as a range, and
#     two more loss factors as an upper bound, so they have no single value;
#   - four rows credit an author other than the book, and the steel row credits
#     two different ones in three different cells.
#
# A catalogue that dropped any of that would read as twenty-five measured
# Poisson ratios where the page offers four. Mirrors
# tests/solids/test_catalogue.py.
# ---------------------------------------------------------------------------
#: ``(key, density in kg/m3 or None, Poisson ratio, loss factor or None)`` for
#: every row, in the order the page prints them. ``None`` is a cell the table
#: leaves as a dash, a range or a bound, never a cell this file guessed.
HOPKINS_A2_ROWS: tuple[tuple[str, float | None, float, float | None], ...] = (
    ("aircrete", None, 0.2, 0.0125),
    ("aluminium", 2700.0, 0.34, None),
    ("brick", None, 0.2, 0.01),
    ("calcium_silicate_block", 1800.0, 0.2, 0.01),
    ("chipboard", 760.0, 0.3, 0.01),
    ("clinker_concrete_block_1030", 1030.0, 0.2, 0.01),
    ("clinker_concrete_block_1720", 1720.0, 0.2, 0.01),
    ("clinker_concrete_slab", 1725.0, 0.2, 0.01),
    ("concrete_cast_in_situ", 2200.0, 0.2, 0.005),
    ("dense_aggregate_block", 2000.0, 0.2, 0.01),
    ("expanded_clay_block", 800.0, 0.2, 0.007),
    ("glass", 2500.0, 0.24, None),
    ("lightweight_aggregate_block", 1400.0, 0.2, 0.01),
    ("mdf", 760.0, 0.3, 0.01),
    ("mortar", 1600.0, 0.2, 0.013),
    ("osb", 590.0, 0.3, 0.01),
    ("perspex", 1250.0, 0.3, None),
    ("plaster_gypsum", 650.0, 0.2, 0.012),
    ("plasterboard_natural_gypsum", 860.0, 0.3, 0.0141),
    ("plasterboard_flue_gas_gypsum", 680.0, 0.3, 0.0125),
    ("plasterboard_glass_fibre", 800.0, 0.3, None),
    ("plywood_birch", 710.0, 0.3, 0.016),
    ("sand_cement_screed", 2000.0, 0.2, 0.01),
    ("steel", 7800.0, 0.28, None),
    ("timber_softwood", 440.0, 0.3, None),
)

#: The rows whose Poisson ratio carries footnote b. Twenty-one of twenty-five:
#: the four that do not are aluminium, glass, mortar and steel.
HOPKINS_A2_MEASURED_POISSON = ("aluminium", "glass", "mortar", "steel")

#: The rows whose loss factor carries footnote b, so the value is an estimate
#: and not a measurement.
HOPKINS_A2_ESTIMATED_LOSS_FACTOR = (
    "brick",
    "chipboard",
    "clinker_concrete_block_1030",
    "clinker_concrete_block_1720",
    "clinker_concrete_slab",
    "concrete_cast_in_situ",
    "dense_aggregate_block",
    "expanded_clay_block",
    "lightweight_aggregate_block",
    "mdf",
    "osb",
    "plaster_gypsum",
)

#: The cells the page prints as an interval: ``key -> (field, low, high)``.
HOPKINS_A2_RANGES: tuple[tuple[str, str, float, float], ...] = (
    ("aircrete", "density_kg_m3", 400.0, 800.0),
    ("aircrete", "longitudinal_speed_m_s", 1600.0, 2300.0),
    ("brick", "density_kg_m3", 1500.0, 2000.0),
    ("glass", "loss_factor", 0.003, 0.006),
    ("osb", "longitudinal_speed_m_s", 2200.0, 3500.0),
)

#: The two loss factors the page prints as ``<= x``, with their ``x``.
HOPKINS_A2_UPPER_BOUNDS: tuple[tuple[str, float], ...] = (
    ("aluminium", 0.001),
    ("steel", 0.0001),
)

#: The rows the book credits to someone other than itself, and the steel row
#: that credits two authors across three cells.
HOPKINS_A2_ATTRIBUTIONS: tuple[tuple[str, str], ...] = (
    ("aluminium", "Heckl, 1981"),
    ("calcium_silicate_block", "Schmitz et al., 1999"),
    ("clinker_concrete_block_1030", "Rindel, 1994"),
    ("clinker_concrete_block_1720", "Rindel, 1994"),
    ("clinker_concrete_slab", "Rindel, 1994"),
    ("mortar", "Maysenholder and Horvatic, 1998"),
    ("plasterboard_natural_gypsum", "Hopkins, 1999"),
    ("plasterboard_flue_gas_gypsum", "Hopkins, 1999"),
)

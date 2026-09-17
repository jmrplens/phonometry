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
    ("aircrete", "plate_longitudinal_speed_m_s", 1600.0, 2300.0),
    ("brick", "density_kg_m3", 1500.0, 2000.0),
    ("glass", "flexural_loss_factor", 0.003, 0.006),
    ("osb", "plate_longitudinal_speed_m_s", 2200.0, 3500.0),
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


# ---------------------------------------------------------------------------
# Cremer 3e Table 4.3, "Mechanical properties of metals at 20 C"
# PDF page 201 (printed p. 191)
# ---------------------------------------------------------------------------
#: Every row as the page prints it: key, density in kg/m3, modulus and shear
#: modulus in pascals, Poisson ratio, ``c_LII`` and ``c_T`` in m/s. Lead and
#: copper each print two specimens under one name, which share every column
#: but the flexural loss factor, so they are two rows.
CREMER_4_3_ROWS: tuple[tuple[str, float, float, float, float, float, float], ...] = (
    ("aluminium", 2700.0, 72e9, 27e9, 0.34, 5200.0, 3100.0),
    ("lead_chemically_pure", 11300.0, 17e9, 6e9, 0.43, 1250.0, 730.0),
    ("lead_antimonial", 11300.0, 17e9, 6e9, 0.43, 1250.0, 730.0),
    ("iron", 7800.0, 200e9, 77e9, 0.30, 5050.0, 3100.0),
    ("steel", 7800.0, 210e9, 77e9, 0.31, 5100.0, 3100.0),
    ("gold", 19300.0, 80e9, 28e9, 0.423, 2000.0, 1200.0),
    ("copper_polycrystal", 8900.0, 125e9, 46e9, 0.35, 3700.0, 2300.0),
    ("copper_single_crystal", 8900.0, 125e9, 46e9, 0.35, 3700.0, 2300.0),
    ("magnesium", 1740.0, 43e9, 17e9, 0.29, 5000.0, 3100.0),
    ("brass", 8500.0, 95e9, 36e9, 0.33, 3200.0, 2100.0),
    ("nickel", 8900.0, 205e9, 77e9, 0.30, 4800.0, 2900.0),
    ("silver", 10500.0, 80e9, 29e9, 0.37, 2700.0, 1600.0),
    ("bismuth", 9800.0, 3.3e9, 1.3e9, 0.38, 580.0, 360.0),
    ("zinc", 7130.0, 13.1e9, 5e9, 0.33, 1350.0, 850.0),
    ("tin", 7280.0, 4.4e9, 1.6e9, 0.39, 780.0, 470.0),
)

#: How far the page's own columns may disagree with the three relations that
#: tie them together, as a fraction. The table prints two significant figures
#: for most cells, so the worst row, bismuth, is 8.7 per cent out on the shear
#: modulus purely from ``1.3`` standing for ``1.196``; every other row is
#: inside 5 per cent on all three at once.
CREMER_4_3_CONSISTENCY_TOLERANCE = 0.09

#: The two rows that print two specimens under one name, and what tells them
#: apart in the Remarks column.
CREMER_4_3_VARIANTS: tuple[tuple[str, str], ...] = (
    ("lead_chemically_pure", "chemically pure"),
    ("lead_antimonial", "antimonial"),
    ("copper_polycrystal", "polycrystal"),
    ("copper_single_crystal", "single crystal"),
)

#: Every bracketed reference the Remarks column carries, resolved against the
#: chapter's own list on PDF page 243 (printed p. 233). Twelve of the fifteen
#: rows credit someone; steel, and the two copper specimens, credit nobody.
CREMER_4_3_ATTRIBUTIONS: tuple[tuple[str, str, str], ...] = (
    (
        "aluminium",
        "flexural_loss_factor",
        "Wegel and Walter, 1953; Zemanek and Rudnik, 1961; Becker and Oberst, 1956",
    ),
    ("lead_chemically_pure", "flexural_loss_factor", "Wegel and Walter, 1953"),
    ("lead_antimonial", "flexural_loss_factor", "Wegel and Walter, 1953"),
    (
        "iron",
        "flexural_loss_factor",
        "Wegel and Walter, 1953; Bennewitz and Rotger, 1936; Becker and Oberst, 1956",
    ),
    ("gold", "flexural_loss_factor", "Forster and Koster, 1937"),
    ("magnesium", "longitudinal_loss_factor", "Becker and Oberst, 1956"),
    ("brass", "flexural_loss_factor", "Wegel and Walter, 1953"),
    ("nickel", "longitudinal_loss_factor", "Becker and Oberst, 1956"),
    (
        "silver",
        "flexural_loss_factor",
        "Bordoni, Nuovo and Verdini, 1959; Forster and Koster, 1937",
    ),
    ("bismuth", "longitudinal_loss_factor", "Becker and Oberst, 1956"),
    ("zinc", "longitudinal_loss_factor", "Becker and Oberst, 1956"),
    ("tin", "longitudinal_loss_factor", "Becker and Oberst, 1956"),
)

#: The two Hopkins rows whose density the page prints only as a range, so no
#: modulus follows and neither do the two speeds that would come from one.
#: They keep the plate speed the page printed.
HOPKINS_A2_ROWS_WITHOUT_A_DERIVED_SPEED: tuple[str, ...] = ("aircrete", "brick")

#: Cremer states the gap between the bar speed and the pure longitudinal speed
#: on PDF page 47 (printed p. 37), under Eq. (3.32): "For mu = 0.3, the
#: difference between these two speeds amounts to 16 %".
CREMER_BAR_TO_BULK_AT_NU_0_3 = 0.16

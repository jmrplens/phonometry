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

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Gases, and the two columns a table prints beside the two it computes.

Source: Hopkins (2007) Table A1 "Properties of gases", PDF page 634 (printed
p. 607). Four columns: the ratio of specific heats, the molar mass, and the
phase velocity and density at the conditions its own footnote states, "normal
temperature and pressure (20 degC, 1,013 x 10^5 Pa)".

The first two are what the ideal-gas closure takes and the last two are what it
returns, so the table is a four-column oracle for
:func:`phonometry.fluids.ideal_gas` that cost nothing to write down.
"""

from __future__ import annotations

#: The conditions the footnote of Table A1 states.
HOPKINS_A1_TEMPERATURE_C = 20.0
HOPKINS_A1_STATIC_PRESSURE_PA = 1.013e5

#: ``(gas, ratio of specific heats, molar mass in kg/mol, phase velocity in
#: m/s, density in kg/m3)``, every row of Table A1.
HOPKINS_A1_GASES: tuple[tuple[str, float, float, float, float], ...] = (
    ("Air (dry)", 1.41, 0.02895, 345.0, 1.205),
    ("Argon", 1.67, 0.040, 319.0, 1.662),
    ("Carbon dioxide", 1.33, 0.044, 271.0, 1.842),
    ("Nitrogen", 1.41, 0.028, 350.0, 1.165),
    ("Oxygen", 1.41, 0.032, 328.0, 1.331),
    ("Sulphur hexafluoride", 1.33, 0.146, 149.0, 6.2),
)

#: The four rows whose density the ideal-gas closure reproduces to the printed
#: precision. The other two are the ones that measure how far it goes.
HOPKINS_A1_IDEAL_DENSITY_GASES = ("Air (dry)", "Argon", "Nitrogen", "Oxygen")

#: How far the closure is from the printed density for the two heavy
#: molecules, as a fraction: carbon dioxide and sulphur hexafluoride. This is
#: the compressibility factor, not an error in the arithmetic.
HOPKINS_A1_COMPRESSIBILITY_GAP = {
    "Carbon dioxide": 0.007,
    "Sulphur hexafluoride": 0.021,
}

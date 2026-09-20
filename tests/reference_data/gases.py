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
#: molecules, as a fraction of the printed value: carbon dioxide and sulphur
#: hexafluoride. It is ``1 - Z``, the compressibility factor's distance from
#: unity, because a real gas has ``rho = p M / (Z R T)`` and the ideal density
#: is therefore ``Z`` times the real one. It is not an error in the
#: arithmetic.
HOPKINS_A1_COMPRESSIBILITY_GAP = {
    "Carbon dioxide": 0.007,
    "Sulphur hexafluoride": 0.021,
}

#: ``(gas, molar mass in kg/mol, ratio of specific heats)``, every row of Bies,
#: Hansen & Howard (2017) Table C.2 "Molecular weights and ratios of specific
#: heats for some commonly used gases", PDF page 751 (printed p. 722), read off
#: the rendered page. Thirty-seven rows, no empty cell, no footnote marker, and
#: the page prints no credit: the five references the appendix gives are tied by
#: name to Table C.1. Saturated steam is the only interval and is carried as the
#: pair it prints.
BIES_C2_GASES: tuple[tuple[str, float, float | tuple[float, float]], ...] = (
    ("Acetylene", 0.02604, 1.30),
    ("Air", 0.02897, 1.40),
    ("Ammonia", 0.01730, 1.32),
    ("Argon", 0.03995, 1.67),
    ("Benzene", 0.07811, 1.12),
    ("Isobutane", 0.05812, 1.10),
    ("n-Butane", 0.05812, 1.11),
    ("Isobutylene", 0.05611, 1.11),
    ("Carbon dioxide", 0.04401, 1.30),
    ("Carbon monoxide", 0.02801, 1.40),
    ("Chlorine", 0.07091, 1.31),
    ("Ethane", 0.03007, 1.22),
    ("Ethylene", 0.02805, 1.22),
    ("Fluorine", 0.01900, 1.36),
    ("Freon 11", 0.13737, 1.14),
    ("Freon 12", 0.12091, 1.13),
    ("Freon 13", 0.10446, 1.14),
    ("Freon 22", 0.08047, 1.18),
    ("Helium", 0.00400, 1.66),
    ("n-Heptane", 0.10020, 1.05),
    ("Hydrogen", 0.00202, 1.41),
    ("Hydrogen chloride", 0.03646, 1.41),
    ("Hydrogen fluoride", 0.02001, 0.97),
    ("Methane", 0.01604, 1.32),
    ("Methyl chloride", 0.05049, 1.24),
    ("Natural gas (representative)", 0.01774, 1.27),
    ("Neon", 0.02018, 1.64),
    ("Nitric oxide", 0.06301, 1.40),
    ("Nitrogen", 0.02801, 1.40),
    ("Octane", 0.11423, 1.66),
    ("Oxygen", 0.03200, 1.40),
    ("Pentane", 0.07215, 1.06),
    ("Propane", 0.04410, 1.15),
    ("Propylene", 0.04208, 1.14),
    ("Saturated steam", 0.01802, (1.25, 1.32)),
    ("Sulphur dioxide", 0.06406, 1.26),
    ("Superheated steam", 0.01802, 1.315),
)

#: The gases both tables print, with the pair each one gives, so that two
#: readings of one gas can be held against each other. Bies first, Hopkins
#: second. Hopkins names dry air "Air (dry)" and Bies names it "Air".
SHARED_GASES = (
    ("Air", (0.02897, 1.40), (0.02895, 1.41)),
    ("Argon", (0.03995, 1.67), (0.040, 1.67)),
    ("Carbon dioxide", (0.04401, 1.30), (0.044, 1.33)),
    ("Nitrogen", (0.02801, 1.40), (0.028, 1.41)),
    ("Oxygen", (0.03200, 1.40), (0.032, 1.41)),
)

#: How far apart the two books are allowed to be on the gases they both print,
#: as a fraction of the larger reading. The molar masses are the same physical
#: constant read to different precision, so what separates them is the rounding
#: of the coarser printing: Hopkins gives argon two significant figures, 0.040
#: against 0.039 95, and that last digit is the widest gap at 0,13 per cent.
#: The ratios of specific heats are measurements, and carbon dioxide at 1,30
#: against 1,33 is the only pair further apart than a rounding digit.
SHARED_GAS_TOLERANCE = {"molar_mass_kg_mol": 0.002, "heat_capacity_ratio": 0.023}

#: The six cells of Table C.2 whose printed value is registered as a defect in
#: ``docs/ERRATA.md``, and the column each one is in. Four molar masses that do
#: not belong to the molecule their row names, and two ratios of specific heats
#: outside what the quantity can be.
BIES_C2_MISPRINTED = {
    "Ammonia": "molar_mass_kg_mol",
    "Fluorine": "molar_mass_kg_mol",
    "Freon 22": "molar_mass_kg_mol",
    "Nitric oxide": "molar_mass_kg_mol",
    "Hydrogen fluoride": "heat_capacity_ratio",
    "Octane": "heat_capacity_ratio",
}

#: What each row's molecule actually weighs, in g/mol, from the 2021 IUPAC
#: standard atomic weights, for the rows whose name fixes a formula. The two
#: mixtures, air and natural gas, have none and are left out. This is the
#: independent side of the comparison that makes four cells of the table a
#: defect: thirty-one of the thirty-five reproduce their formula mass to better
#: than 0,05 per cent, helium and hydrogen miss by the last printed digit, and
#: the four exceptions miss by 1,6 to 110 per cent.
FORMULA_MASSES_G_MOL = {
    "Acetylene": 26.038,
    "Ammonia": 17.031,
    "Argon": 39.95,
    "Benzene": 78.114,
    "Isobutane": 58.122,
    "n-Butane": 58.122,
    "Isobutylene": 56.106,
    "Carbon dioxide": 44.009,
    "Carbon monoxide": 28.010,
    "Chlorine": 70.900,
    "Ethane": 30.069,
    "Ethylene": 28.054,
    "Fluorine": 37.996,
    "Freon 11": 137.359,
    "Freon 12": 120.907,
    "Freon 13": 104.455,
    "Freon 22": 86.465,
    "Helium": 4.0026,
    "n-Heptane": 100.205,
    "Hydrogen": 2.016,
    "Hydrogen chloride": 36.458,
    "Hydrogen fluoride": 20.006,
    "Methane": 16.043,
    "Methyl chloride": 50.485,
    "Neon": 20.180,
    "Nitric oxide": 30.006,
    "Nitrogen": 28.014,
    "Octane": 114.232,
    "Oxygen": 31.998,
    "Pentane": 72.151,
    "Propane": 44.097,
    "Propylene": 42.081,
    "Saturated steam": 18.015,
    "Sulphur dioxide": 64.058,
    "Superheated steam": 18.015,
}

#: How far a row may sit from its formula mass and still be the page rounding
#: rather than a misprint, as a fraction. Hydrogen, printed 2.02 against 2.016,
#: is the widest of the rows that are not defects.
FORMULA_MASS_TOLERANCE = 0.0021

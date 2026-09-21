#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Absorption coefficients as one book prints them, read a second time.

Source: Bies, Hansen & Howard (2017) Table 6.2 "Sabine absorption coefficients
for some commonly used materials", PDF pages 367 to 369 (printed pp. 338 to
340). Columns: the 63, 125, 250, 500, 1000, 2000 and 4000 Hz octave bands.

This transcription was made from the rendered pages independently of the one
in the package's data file, by a second reader who never saw the first, and
the two were compared cell by cell before either was kept: fifty-nine rows,
seven bands, no difference. The test suite holds the catalogue against this
copy so that a later edit to one cannot pass unnoticed by the other.

A name printed over a heading row and an indented sub-row is written here as
``"<heading> / <sub-row>"``, the way the page reads it; the catalogue holds the
heading as the name and the sub-row as the variant. The two rows the page
prints as an absorption area per person, marked with S alpha-bar (m2) in the
name, are tagged ``AREA``; every other row is a coefficient, tagged ``COEF``.
"""

from __future__ import annotations

#: One row is a coefficient.
COEF = "coefficient"

#: One row is an equivalent absorption area per person, in square metres.
AREA = "area"

#: The octave bands Table 6.2 prints, in the order of the value tuples below.
BIES_6_2_BANDS_HZ = (63, 125, 250, 500, 1000, 2000, 4000)

#: ``(group heading, name as printed, kind, values per band)``, every row of
#: Table 6.2 in the order printed. ``None`` is an empty cell.
BIES_6_2_ABSORPTION: tuple[tuple[str, str, str, tuple[float | None, ...]], ...] = (
    (
        "Concert hall seats",
        "Unoccupied – heavily upholstered seats (Beranek and Hidaka, 1998)",
        COEF,
        (None, 0.65, 0.76, 0.81, 0.84, 0.84, 0.81),
    ),
    (
        "Concert hall seats",
        "Unoccupied – medium upholstered seats",
        COEF,
        (None, 0.54, 0.62, 0.68, 0.70, 0.68, 0.66),
    ),
    (
        "Concert hall seats",
        "Unoccupied – light upholstered seats",
        COEF,
        (None, 0.36, 0.47, 0.57, 0.62, 0.62, 0.60),
    ),
    (
        "Concert hall seats",
        "Unoccupied – very light upholstered seats",
        COEF,
        (None, 0.35, 0.40, 0.41, 0.38, 0.33, 0.27),
    ),
    (
        "Concert hall seats",
        "Unoccupied – average well-upholstered seating areas",
        COEF,
        (0.28, 0.44, 0.60, 0.77, 0.84, 0.82, 0.70),
    ),
    (
        "Concert hall seats",
        "Unoccupied – leather-covered upholstered seating areas",
        COEF,
        (None, 0.40, 0.50, 0.58, 0.61, 0.58, 0.50),
    ),
    (
        "Concert hall seats",
        "Unoccupied – metal or wood seats",
        COEF,
        (None, 0.15, 0.19, 0.22, 0.39, 0.38, 0.30),
    ),
    (
        "Concert hall seats",
        "Unoccupied – concert hall, no seats / halls lined with thin wood or other materials <3 cm thick",
        COEF,
        (None, 0.16, 0.13, 0.10, 0.09, 0.08, 0.08),
    ),
    (
        "Concert hall seats",
        "Unoccupied – concert hall, no seats / Halls lined with heavy materials",
        COEF,
        (None, 0.12, 0.10, 0.08, 0.08, 0.08, 0.08),
    ),
    (
        "Concert hall seats",
        "100% occupied audience (orchestra and chorus areas) – upholstered seats",
        COEF,
        (0.34, 0.52, 0.68, 0.85, 0.97, 0.93, 0.85),
    ),
    (
        "Concert hall seats",
        "Audience, per person seated S ᾱ(m²)",
        AREA,
        (None, 0.23, 0.37, 0.44, 0.45, 0.45, 0.45),
    ),
    (
        "Concert hall seats",
        "Audience, per person standing S ᾱ(m²)",
        AREA,
        (None, 0.15, 0.37, 0.43, 0.44, 0.44, 0.43),
    ),
    (
        "Concert hall seats",
        "Wooden pews – 100% occupied",
        COEF,
        (None, 0.57, 0.61, 0.75, 0.86, 0.91, 0.86),
    ),
    (
        "Concert hall seats",
        "Wooden chairs – 100% occupied",
        COEF,
        (None, 0.60, 0.74, 0.88, 0.96, 0.93, 0.85),
    ),
    (
        "Concert hall seats",
        "Wooden chairs – 75% occupied",
        COEF,
        (None, 0.46, 0.56, 0.65, 0.75, 0.72, 0.65),
    ),
    (
        "Walls",
        "Acoustic plaster, 10 mm thick sprayed on solid wall",
        COEF,
        (None, 0.08, 0.15, 0.30, 0.50, 0.60, 0.70),
    ),
    (
        "Walls",
        "Hard surfaces (brick walls, plaster, hard floors, etc.)",
        COEF,
        (None, 0.02, 0.02, 0.03, 0.03, 0.04, 0.05),
    ),
    (
        "Walls",
        "Gypsum board on 50 × 100 mm studs",
        COEF,
        (None, 0.29, 0.10, 0.05, 0.04, 0.07, 0.09),
    ),
    (
        "Walls",
        "Plaster, gypsum or lime, smooth finish; / on brick,",
        COEF,
        (None, 0.013, 0.015, 0.02, 0.03, 0.04, 0.05),
    ),
    (
        "Walls",
        "Plaster, gypsum or lime, smooth finish; / on concrete block,",
        COEF,
        (None, 0.012, 0.09, 0.07, 0.05, 0.05, 0.04),
    ),
    (
        "Walls",
        "Plaster, gypsum or lime, smooth finish; / on lath",
        COEF,
        (None, 0.014, 0.10, 0.06, 0.04, 0.04, 0.03),
    ),
    ("Walls", "Solid timber door", COEF, (None, 0.14, 0.10, 0.06, 0.08, 0.10, 0.10)),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 16 kg/m³, 25 mm thick",
        COEF,
        (None, 0.12, 0.28, 0.55, 0.71, 0.74, 0.83),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 16 kg/m³, 50 mm thick",
        COEF,
        (None, 0.17, 0.45, 0.80, 0.89, 0.97, 0.94),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 16 kg/m³, 75 mm thick",
        COEF,
        (None, 0.30, 0.69, 0.94, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 16 kg/m³, 100 mm thick",
        COEF,
        (None, 0.43, 0.86, 1.0, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 24 kg/m³, 25 mm thick",
        COEF,
        (None, 0.11, 0.32, 0.56, 0.77, 0.89, 0.91),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 24 kg/m³, 50 mm thick",
        COEF,
        (None, 0.27, 0.54, 0.94, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 24 kg/m³, 75 mm thick",
        COEF,
        (None, 0.28, 0.79, 1.0, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 24 kg/m³, 100 mm thick",
        COEF,
        (None, 0.46, 1.0, 1.0, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 48 kg/m³, 50 mm thick",
        COEF,
        (None, 0.3, 0.8, 1.0, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 48 kg/m³, 75 mm thick",
        COEF,
        (None, 0.43, 0.97, 1.0, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 48 kg/m³, 100 mm thick",
        COEF,
        (None, 0.65, 1.0, 1.0, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 60 kg/m³, 25 mm thick",
        COEF,
        (None, 0.18, 0.24, 0.68, 0.85, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Fibreglass or rockwool blanket / 60 kg/m³, 50 mm thick",
        COEF,
        (None, 0.25, 0.83, 1.0, 1.0, 1.0, 1.0),
    ),
    (
        "Acoustic material",
        "Polyurethane foam, 27 kg/m³ 15 mm thick",
        COEF,
        (None, 0.08, 0.22, 0.55, 0.70, 0.85, 0.75),
    ),
    (
        "Floors",
        "Wood platform with large space beneath",
        COEF,
        (None, 0.40, 0.30, 0.20, 0.17, 0.15, 0.10),
    ),
    (
        "Floors",
        "Wood floor on joists",
        COEF,
        (None, 0.15, 0.11, 0.10, 0.07, 0.06, 0.07),
    ),
    (
        "Floors",
        "Concrete or terrazzo",
        COEF,
        (None, 0.01, 0.01, 0.01, 0.02, 0.02, 0.02),
    ),
    (
        "Floors",
        "Concrete block painted",
        COEF,
        (None, 0.01, 0.05, 0.06, 0.07, 0.09, 0.08),
    ),
    (
        "Floors",
        "Linoleum, asphalt, rubber or cork tile on concrete",
        COEF,
        (None, 0.02, 0.03, 0.03, 0.03, 0.03, 0.02),
    ),
    (
        "Floors",
        "Varnished wood joist floor",
        COEF,
        (None, 0.15, 0.12, 0.10, 0.07, 0.06, 0.07),
    ),
    (
        "Floors",
        "Carpet, heavy, on concrete",
        COEF,
        (None, 0.02, 0.06, 0.14, 0.37, 0.60, 0.65),
    ),
    (
        "Floors",
        "Carpet, heavy, on 1.35 kg/ m² hair felt or foam rubber",
        COEF,
        (None, 0.08, 0.24, 0.57, 0.69, 0.71, 0.73),
    ),
    (
        "Floors",
        "Carpet, 5 mm thick, on hard floor",
        COEF,
        (None, 0.02, 0.03, 0.05, 0.10, 0.30, 0.50),
    ),
    (
        "Floors",
        "Carpet, 6 mm thick, on underlay",
        COEF,
        (None, 0.03, 0.09, 0.20, 0.54, 0.70, 0.72),
    ),
    (
        "Floors",
        "Cork floor tiles (3-4 inch thick) – glued down",
        COEF,
        (None, 0.08, 0.02, 0.08, 0.19, 0.21, 0.22),
    ),
    ("Floors", "Glazed tile/marble", COEF, (None, 0.01, 0.01, 0.01, 0.01, 0.02, 0.02)),
    (
        "Ceilings",
        "13 mm mineral tile direct fixed to floor slab",
        COEF,
        (None, 0.10, 0.25, 0.70, 0.85, 0.70, 0.60),
    ),
    (
        "Ceilings",
        "13 mm mineral tile suspended 500 mm below ceiling",
        COEF,
        (None, 0.75, 0.70, 0.65, 0.85, 0.85, 0.90),
    ),
    (
        "Curtains",
        "Light velour, 338 g/m² / hung flat on wall",
        COEF,
        (None, 0.03, 0.04, 0.11, 0.17, 0.24, 0.35),
    ),
    (
        "Curtains",
        "Light velour, 338 g/m² / hung in folds on wall",
        COEF,
        (None, 0.05, 0.15, 0.35, 0.40, 0.50, 0.50),
    ),
    (
        "Curtains",
        "Medium velour, 475 g/m² draped to half area",
        COEF,
        (None, 0.07, 0.31, 0.49, 0.75, 0.70, 0.60),
    ),
    (
        "Curtains",
        "Heavy velour, 610 g/m² draped to half area",
        COEF,
        (None, 0.14, 0.35, 0.55, 0.72, 0.70, 0.65),
    ),
    ("Glass", "Glass, heavy plate", COEF, (None, 0.18, 0.06, 0.04, 0.03, 0.02, 0.02)),
    ("Glass", "Ordinary window", COEF, (None, 0.35, 0.25, 0.18, 0.12, 0.07, 0.04)),
    ("Other", "Stage openings", COEF, (None, 0.30, 0.40, 0.50, 0.60, 0.60, 0.50)),
    (
        "Other",
        "Water (surface of pool)",
        COEF,
        (None, 0.01, 0.01, 0.01, 0.015, 0.02, 0.03),
    ),
    (
        "Other",
        "Orchestra with instruments on podium, 1.5 m² per person",
        COEF,
        (None, 0.27, 0.53, 0.67, 0.93, 0.87, 0.80),
    ),
)

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Absorption coefficients as two books print them, read a second time.

Sources: Bies, Hansen & Howard (2017) Table 6.2 "Sabine absorption
coefficients for some commonly used materials", PDF pages 367 to 369 (printed
pp. 338 to 340), columns the 63, 125, 250, 500, 1000, 2000 and 4000 Hz octave
bands; and Long (2014) Table 7.1 "Absorption Coefficients of Common
Materials", PDF pages 287 to 290 (printed pp. 283 to 286), columns a mount
and the 125 to 4000 Hz octave bands.

Each transcription was made from the rendered pages independently of the one
in the package's data file, by a second reader who never saw the first, and
the two were compared cell by cell before either was kept: fifty-nine rows
and seven bands of Bies, a hundred and two rows, a mount and six bands of
Long, a hundred and sixty-one rows and six bands of Cox, no difference in any
of the three. The test suite holds the catalogue against this copy so that a
later edit to one cannot pass unnoticed by the other.

Bies prints a name over a heading row and an indented sub-row, written here
as ``"<heading> / <sub-row>"``, the way the page reads it; the catalogue holds
the heading as the name and the sub-row as the variant. Long prints a
thickness alone under a bold heading, written here as the thickness alone,
which the catalogue holds as the variant under the heading. Cox prints his
credits as superscript reference numbers, written here as ``(n)``, and a
heading repeated at the top of a page carries ``(cont.)`` the way the reader
met it.

The rows a page prints as an absorption area rather than a coefficient are
tagged ``AREA``, with the numbers in the unit the page uses; every other row
is a coefficient, tagged ``COEF``.
"""

from __future__ import annotations

#: One row is a coefficient.
COEF = "coefficient"

#: One row is an equivalent absorption area per unit, in the page's own unit.
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

#: The octave bands Table 7.1 prints, in the order of the value tuples below.
LONG_7_1_BANDS_HZ = (125, 250, 500, 1000, 2000, 4000)

#: ``(group heading, name as printed, mount as printed, kind, values per
#: band)``, every row of Long 2e Table 7.1 in the order printed. ``None`` is
#: an empty cell. An ``AREA`` row's values are the sabins the page prints.
LONG_7_1_ABSORPTION: tuple[tuple[str, str, str, str, tuple[float | None, ...]], ...] = (
    (
        "Walls",
        "Glass, 1/4″, heavy plate",
        "",
        COEF,
        (0.18, 0.06, 0.04, 0.05, 0.02, 0.02),
    ),
    (
        "Walls",
        "Glass, 3/32″, ordinary window",
        "",
        COEF,
        (0.55, 0.25, 0.18, 0.12, 0.07, 0.04),
    ),
    (
        "Walls",
        "Gypsum board, 1/2″, on 2 × 4 studs",
        "",
        COEF,
        (0.29, 0.10, 0.05, 0.04, 0.07, 0.09),
    ),
    (
        "Walls",
        "Plaster, 7/8″, gypsum or lime, on brick",
        "",
        COEF,
        (0.013, 0.015, 0.02, 0.03, 0.04, 0.05),
    ),
    (
        "Walls",
        "Plaster, on concrete block",
        "",
        COEF,
        (0.12, 0.09, 0.07, 0.05, 0.05, 0.04),
    ),
    ("Walls", "Plaster, 7/8″, on lath", "", COEF, (0.14, 0.10, 0.06, 0.04, 0.04, 0.05)),
    (
        "Walls",
        "Plaster, 7/8″, lath on studs",
        "",
        COEF,
        (0.30, 0.15, 0.10, 0.05, 0.04, 0.05),
    ),
    (
        "Walls",
        "Plywood, 1/4″, 3″ air space, 1″ batt,",
        "",
        COEF,
        (0.60, 0.30, 0.10, 0.09, 0.09, 0.09),
    ),
    (
        "Walls",
        "Soundblox, type B, painted",
        "",
        COEF,
        (0.74, 0.37, 0.45, 0.35, 0.36, 0.34),
    ),
    (
        "Walls",
        "Wood panel, 3/8″, 3-4″ air space",
        "",
        COEF,
        (0.30, 0.25, 0.20, 0.17, 0.15, 0.10),
    ),
    (
        "Walls",
        "Concrete block, unpainted",
        "",
        COEF,
        (0.36, 0.44, 0.51, 0.29, 0.39, 0.25),
    ),
    (
        "Walls",
        "Concrete block, painted",
        "",
        COEF,
        (0.10, 0.05, 0.06, 0.07, 0.09, 0.08),
    ),
    (
        "Walls",
        "Concrete poured, unpainted",
        "",
        COEF,
        (0.01, 0.01, 0.02, 0.02, 0.02, 0.03),
    ),
    (
        "Walls",
        "Brick, unglazed, unpainted",
        "",
        COEF,
        (0.03, 0.03, 0.03, 0.04, 0.05, 0.07),
    ),
    (
        "Walls",
        "Wood paneling, 1/4″, with airspace behind",
        "",
        COEF,
        (0.42, 0.21, 0.10, 0.08, 0.06, 0.06),
    ),
    (
        "Walls",
        "Wood, paneling, 1″, with airspace behind",
        "",
        COEF,
        (0.19, 0.14, 0.09, 0.06, 0.06, 0.05),
    ),
    (
        "Walls",
        "Shredded-wood fiberboard, 2″, on concrete",
        "A",
        COEF,
        (0.15, 0.26, 0.62, 0.94, 0.64, 0.92),
    ),
    (
        "Walls",
        "Carpet, heavy, on 5/8-in perforated mineral fiberboard",
        "",
        COEF,
        (0.37, 0.41, 0.63, 0.85, 0.96, 0.92),
    ),
    (
        "Walls",
        "Brick, unglazed, painted",
        "A",
        COEF,
        (0.01, 0.01, 0.02, 0.02, 0.02, 0.03),
    ),
    (
        "Walls",
        "Light velour, 10 oz per sq yd, hung straight, in contact with wall",
        "",
        COEF,
        (0.03, 0.04, 0.11, 0.17, 0.24, 0.35),
    ),
    (
        "Walls",
        "Medium velour, 14 oz per sq yd, draped to half area",
        "",
        COEF,
        (0.07, 0.31, 0.49, 0.75, 0.70, 0.60),
    ),
    (
        "Walls",
        "Heavy velour, 18 oz per sq yd, draped to half area",
        "",
        COEF,
        (0.14, 0.35, 0.55, 0.72, 0.70, 0.65),
    ),
    (
        "Floors",
        "Floors, concrete or terrazzo",
        "A",
        COEF,
        (0.01, 0.01, 0.015, 0.02, 0.02, 0.02),
    ),
    (
        "Floors",
        "Floors, linoleum, vinyl on concrete",
        "A",
        COEF,
        (0.02, 0.03, 0.03, 0.03, 0.03, 0.02),
    ),
    (
        "Floors",
        "Floors, linoleum, vinyl on subfloor",
        "",
        COEF,
        (0.02, 0.04, 0.05, 0.05, 0.10, 0.05),
    ),
    ("Floors", "Floors, wooden", "", COEF, (0.15, 0.11, 0.10, 0.07, 0.06, 0.07)),
    (
        "Floors",
        "Floors, wooden platform w/airspace",
        "",
        COEF,
        (0.40, 0.30, 0.20, 0.17, 0.15, 0.10),
    ),
    (
        "Floors",
        "Carpet, heavy on concrete",
        "A",
        COEF,
        (0.02, 0.06, 0.14, 0.57, 0.60, 0.65),
    ),
    (
        "Floors",
        "Carpet, on 40 oz (1.35 kg / m²) pad",
        "A",
        COEF,
        (0.08, 0.24, 0.57, 0.69, 0.71, 0.73),
    ),
    (
        "Floors",
        "Indoor-outdoor carpet",
        "A",
        COEF,
        (0.01, 0.05, 0.10, 0.20, 0.45, 0.65),
    ),
    (
        "Floors",
        "Wood parquet in asphalt on concrete",
        "A",
        COEF,
        (0.04, 0.04, 0.07, 0.06, 0.06, 0.07),
    ),
    (
        "Ceilings",
        "Acoustical coating K-13 1″",
        "A",
        COEF,
        (0.08, 0.29, 0.75, 0.98, 0.93, 0.96),
    ),
    ("Ceilings", "1.5″", "A", COEF, (0.16, 0.50, 0.95, 1.06, 1.00, 0.97)),
    ("Ceilings", "2″", "A", COEF, (0.29, 0.67, 1.04, 1.06, 1.00, 0.97)),
    (
        "Ceilings",
        "Acoustical coating K-13 “fc” 1″",
        "A",
        COEF,
        (0.12, 0.38, 0.88, 1.16, 1.15, 1.12),
    ),
    (
        "Ceilings",
        "Glass-fiber roof fabric, 12 oz/yd",
        "",
        COEF,
        (0.65, 0.71, 0.82, 0.86, 0.76, 0.62),
    ),
    (
        "Ceilings",
        "Glass-fiber roof fabric, 37.5 oz/yd",
        "",
        COEF,
        (0.38, 0.23, 0.17, 0.15, 0.09, 0.06),
    ),
    (
        "Acoustical Tile",
        "Standard mineral fiber, 5/8″",
        "E400",
        COEF,
        (0.68, 0.76, 0.60, 0.65, 0.82, 0.76),
    ),
    (
        "Acoustical Tile",
        "Standard mineral fiber, 3/4″",
        "E400",
        COEF,
        (0.72, 0.84, 0.70, 0.79, 0.76, 0.81),
    ),
    (
        "Acoustical Tile",
        "Standard mineral fiber, 1″",
        "E400",
        COEF,
        (0.76, 0.84, 0.72, 0.89, 0.85, 0.81),
    ),
    (
        "Acoustical Tile",
        "Energy mineral fiber, 5/8″",
        "E400",
        COEF,
        (0.70, 0.75, 0.58, 0.63, 0.78, 0.73),
    ),
    (
        "Acoustical Tile",
        "Energy mineral fiber, 3/4″",
        "E400",
        COEF,
        (0.68, 0.81, 0.68, 0.78, 0.85, 0.80),
    ),
    (
        "Acoustical Tile",
        "Energy mineral fiber, 1″",
        "E400",
        COEF,
        (0.74, 0.85, 0.68, 0.86, 0.90, 0.79),
    ),
    (
        "Acoustical Tile",
        "Film faced fiberglass, 1″",
        "E400",
        COEF,
        (0.56, 0.63, 0.69, 0.83, 0.71, 0.55),
    ),
    (
        "Acoustical Tile",
        "Film faced fiberglass, 2″",
        "E400",
        COEF,
        (0.52, 0.82, 0.88, 0.91, 0.75, 0.55),
    ),
    (
        "Acoustical Tile",
        "Film faced fiberglass, 3″",
        "E400",
        COEF,
        (0.64, 0.88, 1.02, 0.91, 0.84, 0.62),
    ),
    (
        "Glass Cloth Acoustical Ceiling Panels",
        "Fiberglass tile, 3/4″",
        "E400",
        COEF,
        (0.74, 0.89, 0.67, 0.89, 0.95, 1.07),
    ),
    (
        "Glass Cloth Acoustical Ceiling Panels",
        "Fiberglass tile, 1″",
        "E400",
        COEF,
        (0.77, 0.74, 0.75, 0.95, 1.01, 1.02),
    ),
    (
        "Glass Cloth Acoustical Ceiling Panels",
        "Fiberglass tile, 1 1/2″",
        "E400",
        COEF,
        (0.78, 0.93, 0.88, 1.01, 1.02, 1.00),
    ),
    (
        "Seats and Audience",
        "Unoccupied well-upholstered seats",
        "",
        COEF,
        (0.19, 0.37, 0.56, 0.67, 0.61, 0.59),
    ),
    (
        "Seats and Audience",
        "Unoccupied leather-covered seats",
        "",
        COEF,
        (0.19, 0.57, 0.56, 0.67, 0.61, 0.59),
    ),
    (
        "Seats and Audience",
        "Wooden pews, occupied",
        "",
        COEF,
        (0.57, 0.44, 0.67, 0.70, 0.80, 0.72),
    ),
    (
        "Seats and Audience",
        "Fabric well-upholstered seats, with perforated seat pans, unoccupied",
        "",
        COEF,
        (0.19, 0.37, 0.56, 0.67, 0.61, 0.59),
    ),
    (
        "Seats and Audience",
        "Leather-covered upholstered seats, unoccupied",
        "",
        COEF,
        (0.44, 0.54, 0.60, 0.62, 0.58, 0.50),
    ),
    (
        "Seats and Audience",
        "Audience, seated in upholstered seats",
        "",
        COEF,
        (0.39, 0.57, 0.80, 0.94, 0.92, 0.87),
    ),
    (
        "Seats and Audience",
        "Congregation, seated in wooden pews",
        "",
        COEF,
        (0.57, 0.61, 0.75, 0.86, 0.91, 0.86),
    ),
    (
        "Seats and Audience",
        "Chair, metal or wood seat, unoccupied",
        "",
        COEF,
        (0.15, 0.19, 0.22, 0.39, 0.38, 0.30),
    ),
    (
        "Seats and Audience",
        "Students, informally dressed, seated in tablet-arm chairs",
        "",
        COEF,
        (0.30, 0.41, 0.49, 0.84, 0.87, 0.84),
    ),
    ("Duct Liners", "1/2″", "", COEF, (0.11, 0.51, 0.48, 0.70, 0.88, 0.98)),
    ("Duct Liners", "1″", "", COEF, (0.16, 0.54, 0.67, 0.85, 0.97, 1.01)),
    ("Duct Liners", "1 1/2″", "", COEF, (0.22, 0.73, 0.81, 0.97, 1.03, 1.04)),
    ("Duct Liners", "2″", "", COEF, (0.33, 0.90, 0.96, 1.07, 1.07, 1.09)),
    (
        "Duct Liners",
        "Aeroflex Type 150, 1″",
        "F",
        COEF,
        (0.13, 0.51, 0.46, 0.65, 0.74, 0.95),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 150, 2″",
        "F",
        COEF,
        (0.25, 0.73, 0.94, 1.03, 1.02, 1.09),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 200, 1/2″",
        "F",
        COEF,
        (0.10, 0.44, 0.29, 0.39, 0.63, 0.81),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 200, 1″",
        "F",
        COEF,
        (0.15, 0.59, 0.53, 0.78, 0.85, 1.00),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 200, 2″",
        "F",
        COEF,
        (0.28, 0.81, 1.04, 1.10, 1.06, 1.09),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 300, 1/2″",
        "F",
        COEF,
        (0.09, 0.43, 0.31, 0.43, 0.66, 0.98),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 300, 1″",
        "F",
        COEF,
        (0.14, 0.56, 0.63, 0.82, 0.99, 1.04),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 150, 1″",
        "A",
        COEF,
        (0.06, 0.24, 0.47, 0.71, 0.85, 0.97),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 150, 2″",
        "A",
        COEF,
        (0.20, 0.51, 0.88, 1.02, 0.99, 1.04),
    ),
    (
        "Duct Liners",
        "Aeroflex Type 300, 1″",
        "A",
        COEF,
        (0.08, 0.28, 0.65, 0.89, 1.01, 1.04),
    ),
    (
        "Building Insulation - Fiberglass",
        "3.5″ (R-11) (insulation exposed to sound)",
        "A",
        COEF,
        (0.34, 0.85, 1.09, 0.97, 0.97, 1.12),
    ),
    (
        "Building Insulation - Fiberglass",
        "6.0″ (R-19) (insulation exposed to sound)",
        "A",
        COEF,
        (0.64, 1.14, 1.09, 0.99, 1.00, 1.21),
    ),
    (
        "Building Insulation - Fiberglass",
        "3.5″ (R-11) (FRK facing exposed to sound)",
        "A",
        COEF,
        (0.56, 1.11, 1.16, 0.61, 0.40, 0.21),
    ),
    (
        "Building Insulation - Fiberglass",
        "6.0″ (R-19) (FRK facing exposed to sound)",
        "A",
        COEF,
        (0.94, 1.33, 1.02, 0.71, 0.56, 0.39),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 1″ thick",
        "A",
        COEF,
        (0.03, 0.22, 0.69, 0.91, 0.96, 0.99),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 2″ thick",
        "A",
        COEF,
        (0.22, 0.82, 1.21, 1.10, 1.02, 1.05),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 3″ thick",
        "A",
        COEF,
        (0.53, 1.19, 1.21, 1.08, 1.01, 1.04),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 4″ thick",
        "A",
        COEF,
        (0.84, 1.24, 1.24, 1.08, 1.00, 0.97),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 1″ thick",
        "E400",
        COEF,
        (0.65, 0.94, 0.76, 0.98, 1.00, 1.14),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 2″ thick",
        "E400",
        COEF,
        (0.66, 0.95, 1.06, 1.11, 1.09, 1.18),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 3″ thick",
        "E400",
        COEF,
        (0.66, 0.93, 1.13, 1.10, 1.11, 1.14),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 3lb/ft³, 4″ thick",
        "E400",
        COEF,
        (0.65, 1.01, 1.20, 1.14, 1.10, 1.16),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 1″ thick",
        "A",
        COEF,
        (0.08, 0.25, 0.74, 0.95, 0.97, 1.00),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 2″ thick",
        "A",
        COEF,
        (0.19, 0.74, 1.17, 1.11, 1.01, 1.01),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 3″ thick",
        "A",
        COEF,
        (0.54, 1.12, 1.23, 1.07, 1.01, 1.05),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 4″ thick",
        "A",
        COEF,
        (0.75, 1.19, 1.17, 1.05, 0.97, 0.98),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 1″ thick",
        "E400",
        COEF,
        (0.68, 0.91, 0.78, 0.97, 1.05, 1.18),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 2″ thick",
        "E400",
        COEF,
        (0.62, 0.95, 0.98, 1.07, 1.09, 1.22),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 3″ thick",
        "E400",
        COEF,
        (0.66, 0.92, 1.11, 1.12, 1.10, 1.19),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, 6lb/ft³, 4″ thick",
        "E400",
        COEF,
        (0.59, 0.91, 1.15, 1.11, 1.11, 1.19),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 1″ thick",
        "A",
        COEF,
        (0.12, 0.74, 0.72, 0.68, 0.53, 0.24),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 2″ thick",
        "A",
        COEF,
        (0.51, 0.65, 0.86, 0.71, 0.49, 0.26),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 3″ thick",
        "A",
        COEF,
        (0.84, 0.88, 0.86, 0.71, 0.52, 0.25),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 4″ thick",
        "A",
        COEF,
        (0.88, 0.90, 0.84, 0.71, 0.49, 0.23),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 1″ thick",
        "E400",
        COEF,
        (0.48, 0.60, 0.80, 0.82, 0.52, 0.35),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 2″ thick",
        "E400",
        COEF,
        (0.50, 0.61, 0.99, 0.83, 0.51, 0.35),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 3″ thick",
        "E400",
        COEF,
        (0.59, 0.64, 1.09, 0.81, 0.50, 0.33),
    ),
    (
        "Fiberglass Board (FB)",
        "FB, FRK faced, 4″ thick",
        "E400",
        COEF,
        (0.61, 0.69, 1.08, 0.81, 0.48, 0.34),
    ),
    (
        "Miscellaneous",
        "Musician (per person), with instrument",
        "",
        AREA,
        (4.0, 8.5, 11.5, 14.0, 15.0, 12.0),
    ),
    (
        "Miscellaneous",
        "Air, Sabins per 1000 cubic feet @ 50% RH",
        "",
        AREA,
        (None, None, None, 0.9, 2.3, 7.2),
    ),
)


#: The octave bands Cox Appendix A prints, in the order of the value tuples
#: below.
COX_A_BANDS_HZ = (125, 250, 500, 1000, 2000, 4000)

#: ``(group heading, name as printed, values per band)``, every row of
#: Cox & D'Antonio 3e Appendix A in the order printed. The reference markers
#: the page prints as superscripts are written ``(n)`` here, and a heading
#: repeated at the top of a page carries ``(cont.)`` the way the reader met
#: it. Every cell of this table is a number: the appendix has no empty cell.
COX_A_ABSORPTION: tuple[tuple[str, str, tuple[float, ...]], ...] = (
    (
        "Curtains or drapes",
        "Light velour 0.338 kg/m2 hung straight in contact with wall(1)",
        (0.04, 0.05, 0.11, 0.18, 0.3, 0.35),
    ),
    (
        "Curtains or drapes",
        "Medium velour 0.475 kg/m2, hung straight(1)",
        (0.05, 0.07, 0.13, 0.22, 0.32, 0.35),
    ),
    (
        "Curtains or drapes",
        "Medium velour 0.475 kg/m2, draped to half area(1)",
        (0.07, 0.31, 0.49, 0.75, 0.7, 0.6),
    ),
    (
        "Curtains or drapes",
        "Heavy velour, 0.61 kg/m2 hung straight(1)",
        (0.05, 0.12, 0.35, 0.48, 0.38, 0.36),
    ),
    (
        "Curtains or drapes",
        "Heavy velour, 0.61 kg/m2 draped to half area(1)",
        (0.14, 0.35, 0.55, 0.77, 0.7, 0.6),
    ),
    ("Variation with draping", "Hung straight(2)", (0.04, 0.16, 0.19, 0.17, 0.2, 0.25)),
    (
        "Variation with draping",
        "Draped to half area(2)",
        (0.15, 0.25, 0.3, 0.28, 0.35, 0.4),
    ),
    (
        "Variation with draping",
        "Draped to 40% of area(2)",
        (0.19, 0.31, 0.35, 0.34, 0.44, 0.5),
    ),
    (
        "Variation with draping",
        "Curtains in folds against wall(3)",
        (0.05, 0.15, 0.35, 0.4, 0.5, 0.5),
    ),
    (
        "Cotton curtains, 0.475 kg/m2",
        "Draped to 7/8 area(4,5)",
        (0.03, 0.12, 0.15, 0.27, 0.37, 0.42),
    ),
    (
        "Cotton curtains, 0.475 kg/m2",
        "Draped to 3/4 area(4,5)",
        (0.04, 0.23, 0.4, 0.57, 0.53, 0.4),
    ),
    (
        "Cotton curtains, 0.475 kg/m2",
        "Draped to 1/2 area(4,5)",
        (0.07, 0.37, 0.49, 0.81, 0.65, 0.54),
    ),
    ("Carpet", "Carpet heavy, on concrete(2)", (0.02, 0.06, 0.14, 0.37, 0.6, 0.65)),
    (
        "Carpet",
        "Heavy carpet (same as line above) on foam rubber or 1.35 kg/m2 hair felt(2)",
        (0.08, 0.24, 0.57, 0.69, 0.71, 0.73),
    ),
    (
        "Carpet",
        "Heavy carpet (same as 2 lines above) with latex backing on foam rubber or 1.35 kg/m2 hair felt(2)",
        (0.08, 0.27, 0.39, 0.34, 0.48, 0.63),
    ),
    ("Carpet", "Haircord on felt(6)", (0.1, 0.15, 0.25, 0.3, 0.3, 0.3)),
    ("Carpet", "Pile and thick felt(6)", (0.07, 0.25, 0.5, 0.5, 0.6, 0.65)),
    (
        "Carpet",
        "No underlay (pad), woven wool loop, 1.2 kg/m2 2.4 mm pile height(2)",
        (0.1, 0.16, 0.11, 0.3, 0.5, 0.47),
    ),
    (
        "Carpet",
        "No underlay (pad), woven wool loop, 1.4 kg/m2 6.4 mm pile height(2)",
        (0.15, 0.17, 0.12, 0.32, 0.52, 0.57),
    ),
    (
        "Carpet",
        "No underlay (pad) woven wool loop, 2.3 kg/m2 9.5 mm pile height(2)",
        (0.17, 0.18, 0.21, 0.5, 0.63, 0.83),
    ),
    (
        "Carpet",
        "Loop pile tufted carpet,(2) 1.4 kg/m2, hair underlay 1.4 kg/m2",
        (0.03, 0.25, 0.55, 0.7, 0.62, 0.84),
    ),
    (
        "Carpet",
        "Loop pile tufted carpet,(2) 1.4 kg/m2, hair underlay 3.0 kg/m2",
        (0.1, 0.4, 0.62, 0.7, 0.63, 0.88),
    ),
    (
        "Carpet (cont.)",
        "Loop pile tufted carpet,(2) 1.4 kg/m2, hair and jute underlay 3 kg/m2",
        (0.2, 0.5, 0.68, 0.72, 0.65, 0.9),
    ),
    (
        "Carpet (cont.)",
        "Loop pile tufted carpet, 1.4 kg/m2, no underlay(2)",
        (0.04, 0.08, 0.17, 0.33, 0.59, 0.75),
    ),
    (
        "Carpet (cont.)",
        "Loop pile tufted carpet, 0.7 kg/m2, 1.4 kg/m2 hair underlay pad(2)",
        (0.1, 0.19, 0.35, 0.79, 0.69, 0.79),
    ),
    (
        "Carpet (cont.)",
        "16 mm wool pile with underlay(1)",
        (0.2, 0.25, 0.35, 0.4, 0.5, 0.75),
    ),
    (
        "Carpet (cont.)",
        "9.5 mm wool pile no underlay on concrete(1)",
        (0.09, 0.08, 0.21, 0.26, 0.27, 0.37),
    ),
    ("Carpet (cont.)", "Cord carpet(3)", (0.05, 0.05, 0.1, 0.2, 0.45, 0.65)),
    (
        "Carpet (cont.)",
        "Thin (6 mm) carpet on underlay(7)",
        (0.03, 0.09, 0.2, 0.54, 0.7, 0.72),
    ),
    (
        "Carpet (cont.)",
        "6 mm pile carpet bonded to closed-cell foam underlay(7)",
        (0.03, 0.09, 0.25, 0.31, 0.33, 0.44),
    ),
    (
        "Carpet (cont.)",
        "Thick (9 mm) carpet on underlay(2)",
        (0.08, 0.08, 0.3, 0.6, 0.75, 0.8),
    ),
    (
        "Carpet (cont.)",
        "Needle felt 5 mm stuck to concrete(8,9)",
        (0.01, 0.02, 0.05, 0.15, 0.3, 0.4),
    ),
    (
        "Carpet (cont.)",
        "Thin carpet cemented to concrete(10)",
        (0.02, 0.04, 0.08, 0.2, 0.35, 0.4),
    ),
    (
        "Other floors",
        "Wood block/lino/rubber flooring(6)",
        (0.02, 0.04, 0.05, 0.05, 0.1, 0.05),
    ),
    (
        "Other floors",
        "Parquet fixed with asphalt, on concrete(1)",
        (0.04, 0.04, 0.07, 0.06, 0.06, 0.07),
    ),
    ("Other floors", "Wood on solid floor(1)", (0.04, 0.04, 0.03, 0.03, 0.03, 0.02)),
    ("Other floors", "Floors, wood(2)", (0.15, 0.11, 0.1, 0.07, 0.06, 0.07)),
    (
        "Other floors",
        "Wood platform, large airspace below(1)",
        (0.4, 0.3, 0.2, 0.17, 0.15, 0.1),
    ),
    ("Other floors", "Floor boards on joist floor(6)", (0.15, 0.2, 0.1, 0.1, 0.1, 0.1)),
    (
        "Other floors",
        "Floors, concrete or terrazzo(2,11)",
        (0.01, 0.01, 0.015, 0.02, 0.02, 0.02),
    ),
    ("Other floors", "Concrete floor(10)", (0.01, 0.02, 0.02, 0.02, 0.02, 0.02)),
    (
        "Other floors",
        "Linoleum or vinyl stuck to concrete(9,12)",
        (0.02, 0.02, 0.03, 0.04, 0.04, 0.05),
    ),
    (
        "Other floors",
        "Linoleum, asphalt tile, or cork tile on concrete(2,5,13)",
        (0.02, 0.03, 0.03, 0.03, 0.03, 0.02),
    ),
    (
        "Other floors",
        "Layer of rubber, cork, linoleum and underlay, or vinyl and underlay, stuck to concrete(9,14)",
        (0.02, 0.02, 0.04, 0.05, 0.05, 0.1),
    ),
    (
        "Other floors",
        "Cork, lino or rubber tile on solid floor(1)",
        (0.04, 0.03, 0.04, 0.04, 0.03, 0.02),
    ),
    ("Other floors", "25 mm cork on solid backing", (0.05, 0.1, 0.2, 0.55, 0.6, 0.55)),
    ("Other floors", "Slate(1)", (0.01, 0.01, 0.01, 0.02, 0.02, 0.02)),
    (
        "Theatre seating, unoccupied",
        "Beranek's values(15)",
        (0.19, 0.37, 0.56, 0.67, 0.61, 0.59),
    ),
    (
        "Theatre seating, unoccupied",
        "Average of nine modern seating designs, 0.9 m row spacing(16)",
        (0.34, 0.46, 0.64, 0.71, 0.77, 0.85),
    ),
    (
        "Theatre seating, unoccupied",
        "One seat type, 0.8 m row spacing(16)",
        (0.29, 0.39, 0.61, 0.74, 0.83, 0.88),
    ),
    (
        "Theatre seating, unoccupied",
        "Same seat as line above, 0.9 m row spacing(16)",
        (0.25, 0.35, 0.58, 0.7, 0.78, 0.84),
    ),
    (
        "Theatre seating, unoccupied",
        "Same seat as two lines above, 1 m row spacing(16)",
        (0.23, 0.34, 0.52, 0.65, 0.73, 0.75),
    ),
    (
        "Theatre seating, unoccupied",
        "Upholstered seating(6)",
        (0.45, 0.6, 0.73, 0.8, 0.75, 0.64),
    ),
    (
        "Theatre seating, unoccupied",
        "Upholstered seating, well upholstered(17)",
        (0.44, 0.6, 0.77, 0.89, 0.82, 0.7),
    ),
    (
        "Theatre seating, unoccupied",
        "Upholstered seating, leather covered(17)",
        (0.4, 0.5, 0.58, 0.61, 0.58, 0.5),
    ),
    (
        "Seating, occupied",
        "Occupied theatre seating average from References 1 and 16",
        (0.41, 0.58, 0.8, 0.9, 0.92, 0.89),
    ),
    (
        "Seating, occupied",
        "Audience on timber seats (1/m2)(2)",
        (0.16, 0.24, 0.56, 0.69, 0.81, 0.78),
    ),
    (
        "Seating, occupied",
        "Audience on timber seats (2/m2)(2)",
        (0.24, 0.4, 0.78, 0.98, 0.96, 0.87),
    ),
    (
        "Seating, occupied",
        "Orchestra with instruments (1.5 m2/person)(2)",
        (0.27, 0.53, 0.67, 0.93, 0.87, 0.8),
    ),
    (
        "Seating, occupied",
        "Wooden pews (100% occupancy)(17)",
        (0.57, 0.61, 0.75, 0.86, 0.91, 0.86),
    ),
    (
        "Seating, occupied (cont.)",
        "Wooden chairs (100% occupancy)(17)",
        (0.6, 0.74, 0.88, 0.96, 0.93, 0.85),
    ),
    (
        "Seating, occupied (cont.)",
        "Wooden pews (75% occupancy)(17)",
        (0.46, 0.56, 0.65, 0.75, 0.72, 0.65),
    ),
    (
        "Standing audience",
        "2.7 people/m2 (see Reference 18)",
        (0.23, 0.46, 0.95, 1.21, 1.2, 1.14),
    ),
    (
        "Miscellaneous",
        "Water surface in swimming pool(19)",
        (0.01, 0.01, 0.01, 0.01, 0.02, 0.02),
    ),
    (
        "Miscellaneous",
        "Water surface in swimming pool(2)",
        (0.008, 0.008, 0.013, 0.015, 0.02, 0.025),
    ),
    ("Miscellaneous", "Marble or glazed tile(2)", (0.01, 0.01, 0.01, 0.01, 0.02, 0.02)),
    ("Miscellaneous", "Solid wooden door(9,14)", (0.14, 0.1, 0.06, 0.08, 0.1, 0.1)),
    ("Miscellaneous", "Ventilation grille(8,9)", (0.6, 0.6, 0.6, 0.6, 0.6, 0.6)),
    ("Miscellaneous", "Egg boxes(20)", (0.01, 0.07, 0.43, 0.62, 0.51, 0.7)),
    (
        "Miscellaneous",
        "Anechoic chamber wall (wedges)",
        (0.997, 0.997, 0.997, 0.997, 0.997, 0.997),
    ),
    (
        "Wood",
        "Plywood panelling, 1 cm thick(2,11)",
        (0.28, 0.22, 0.17, 0.09, 0.1, 0.11),
    ),
    (
        "Wood",
        "22 mm chipboard, 50 mm cavity filled with mineral wool(9,14)",
        (0.12, 0.04, 0.06, 0.05, 0.05, 0.05),
    ),
    (
        "Wood",
        "3-4 mm plywood sheets, >75 mm cavity with 25-50 mm mineral wool(8,9)",
        (0.5, 0.3, 0.1, 0.05, 0.05, 0.05),
    ),
    ("Wood", "Plywood/hardwood, air space(6)", (0.32, 0.43, 0.12, 0.07, 0.07, 0.11)),
    (
        "Wood",
        "6 mm wood fibreboard on laths, cavity >100 mm deep(9,14)",
        (0.3, 0.2, 0.2, 0.1, 0.05, 0.05),
    ),
    ("Wood", "Fibreboard, solid backing(6)", (0.05, 0.1, 0.15, 0.25, 0.3, 0.3)),
    ("Wood", "Fibreboard, 25 mm air space(6)", (0.3, 0.3, 0.3, 0.3, 0.3, 0.3)),
    (
        "Wood",
        "9.5-12.7 mm wood panelling, 5-10 cm air space behind(1)",
        (0.3, 0.25, 0.2, 0.17, 0.15, 0.1),
    ),
    ("Wood", "Wood, 50 mm thick", (0.01, 0.05, 0.05, 0.04, 0.04, 0.04)),
    ("Concrete", "Rough concrete(21)", (0.02, 0.03, 0.03, 0.03, 0.04, 0.07)),
    (
        "Concrete",
        "Smooth unpainted concrete(9,14)",
        (0.01, 0.01, 0.02, 0.02, 0.02, 0.05),
    ),
    (
        "Concrete",
        "Smooth concrete, painted or glazed(9,14)",
        (0.01, 0.01, 0.01, 0.02, 0.02, 0.02),
    ),
    ("Concrete", "Concrete block, coarse(2)", (0.36, 0.44, 0.31, 0.29, 0.39, 0.25)),
    (
        "Concrete",
        "Concrete block, painted(2,5,13)",
        (0.1, 0.05, 0.06, 0.07, 0.09, 0.08),
    ),
    (
        "Concrete",
        "Porous concrete blocks without surface finish,(9) 400-800 kg/m3",
        (0.05, 0.05, 0.05, 0.08, 0.14, 0.2),
    ),
    (
        "Concrete",
        "Clinker concrete, no surface finish,(8,9) 800 kg/m3",
        (0.1, 0.2, 0.4, 0.6, 0.5, 0.6),
    ),
    ("Bricks and blocks", "Brick, unglazed(2)", (0.03, 0.03, 0.03, 0.04, 0.05, 0.07)),
    (
        "Bricks and blocks",
        "Brickwork, plain painted(6)",
        (0.05, 0.04, 0.02, 0.04, 0.05, 0.05),
    ),
    (
        "Bricks and blocks",
        "Smooth brickwork with flush pointing, painted(19)",
        (0.01, 0.01, 0.02, 0.02, 0.02, 0.02),
    ),
    (
        "Bricks and blocks",
        "Brick, unglazed, painted(2)",
        (0.01, 0.01, 0.02, 0.02, 0.02, 0.03),
    ),
    (
        "Bricks and blocks",
        "Smooth brickwork with flush pointing(9,14)",
        (0.02, 0.03, 0.03, 0.04, 0.05, 0.07),
    ),
    (
        "Bricks and blocks",
        "Smooth brickwork, 10 mm deep pointing, pit sand mortar(8,9)",
        (0.08, 0.09, 0.12, 0.16, 0.22, 0.24),
    ),
    ("Bricks and blocks", "Breeze block(6)", (0.2, 0.3, 0.6, 0.6, 0.5, 0.5)),
    ("Plaster", "Lime cement plaster(14)", (0.02, 0.02, 0.03, 0.04, 0.05, 0.05)),
    ("Plaster", "Glaze plaster(9,14)", (0.01, 0.01, 0.01, 0.02, 0.02, 0.02)),
    (
        "Plaster (cont.)",
        "Painted plaster surface(8,9)",
        (0.02, 0.02, 0.02, 0.02, 0.02, 0.02),
    ),
    (
        "Plaster (cont.)",
        "Plaster with wallpaper on backing paper(9,14)",
        (0.02, 0.03, 0.04, 0.05, 0.07, 0.08),
    ),
    (
        "Plaster (cont.)",
        "Plaster, gypsum, or lime, rough finish on lath(10,22)",
        (0.02, 0.03, 0.04, 0.05, 0.04, 0.03),
    ),
    (
        "Plaster (cont.)",
        "Plaster, gypsum, or lime, smooth finish on lath(2)",
        (0.14, 0.1, 0.06, 0.04, 0.04, 0.03),
    ),
    (
        "Plaster (cont.)",
        "Plaster, gypsum, or lime, smooth finish on lath(10,22)",
        (0.02, 0.02, 0.03, 0.04, 0.04, 0.03),
    ),
    (
        "Plaster (cont.)",
        "Plaster, on laths/studs, air space(6)",
        (0.3, 0.1, 0.1, 0.05, 0.04, 0.05),
    ),
    (
        "Plaster (cont.)",
        "Plaster, gypsum, or lime, smooth finish on tile or brick(2)",
        (0.013, 0.015, 0.02, 0.03, 0.04, 0.05),
    ),
    (
        "Plaster (cont.)",
        "Plaster, lime, or gypsum on solid backing(6)",
        (0.03, 0.03, 0.02, 0.03, 0.04, 0.05),
    ),
    ("Plaster (cont.)", "Acoustics plaster(6)", (0.3, 0.35, 0.5, 0.7, 0.7, 0.7)),
    (
        "Plaster (cont.)",
        "Acoustics plaster, 40 mm thick(23)",
        (0.31, 0.55, 0.84, 0.78, 0.71, 0.54),
    ),
    (
        "Plaster (cont.)",
        "Acoustics plaster, 68 mm thick(23)",
        (0.47, 0.74, 0.76, 0.65, 0.62, 0.49),
    ),
    (
        "Plasterboard",
        "Gypsum board, 1.27 cm nailed to studs with 4.1 m c-t-c(2)",
        (0.29, 0.1, 0.05, 0.04, 0.07, 0.09),
    ),
    (
        "Plasterboard",
        "Plasterboard on frame, 9.5 mm boards, 10 cm empty cavity(9,24)",
        (0.11, 0.13, 0.05, 0.03, 0.02, 0.03),
    ),
    (
        "Plasterboard",
        "Plasterboard on frame, 9.5 mm boards, 10 cm cavity filled with mineral wool(9,24)",
        (0.28, 0.14, 0.09, 0.06, 0.05, 0.05),
    ),
    (
        "Plasterboard",
        "Plasterboard on frame, 13 mm boards, 10 cm empty cavity(9,24)",
        (0.08, 0.11, 0.05, 0.03, 0.02, 0.03),
    ),
    (
        "Plasterboard",
        "Plasterboard on frame, 13 mm boards, 10 cm cavity filled with mineral wool(9,24)",
        (0.3, 0.12, 0.08, 0.06, 0.06, 0.05),
    ),
    (
        "Plasterboard",
        "2 x 13 mm plasterboard on steel frame, 5 cm mineral wool in cavity, surface painted(9,12)",
        (0.15, 0.1, 0.06, 0.04, 0.04, 0.05),
    ),
    (
        "Glazing",
        "Glass, ordinary window glass(2,11)",
        (0.35, 0.25, 0.18, 0.12, 0.07, 0.04),
    ),
    ("Glazing", "Single pane of glass,(6) 3-4 mm", (0.2, 0.15, 0.1, 0.07, 0.05, 0.05)),
    ("Glazing", "Single pane of glass,(6) >4 mm", (0.1, 0.07, 0.04, 0.03, 0.02, 0.02)),
    (
        "Glazing",
        "Single pane of glass, 3 mm(9,24)",
        (0.08, 0.04, 0.03, 0.03, 0.02, 0.02),
    ),
    (
        "Glazing",
        "Double glazing, 2-3 mm glass, 1 cm gap(8,9)",
        (0.1, 0.07, 0.05, 0.03, 0.02, 0.02),
    ),
    (
        "Glazing",
        "Double glazing, 2-3 mm glass, >3 cm gap(9,24)",
        (0.15, 0.05, 0.03, 0.03, 0.02, 0.02),
    ),
    (
        "Glazing",
        "Glass, large panes, heavy glass(2,5,13)",
        (0.18, 0.06, 0.04, 0.03, 0.02, 0.02),
    ),
    (
        "Wools and foam",
        "25 mm fibreglass, rigid backing(25)",
        (0.08, 0.25, 0.45, 0.75, 0.75, 0.65),
    ),
    (
        "Wools and foam",
        "2.54 cm fibreglass,(2) 24 to 48 kg/m3",
        (0.08, 0.25, 0.65, 0.85, 0.8, 0.75),
    ),
    (
        "Wools and foam",
        "2.5 cm fibreglass, 2.5 cm airspace(2)",
        (0.15, 0.55, 0.8, 0.9, 0.85, 0.8),
    ),
    (
        "Wools and foam",
        "5 cm fibreglass, rigid backing(25)",
        (0.21, 0.5, 0.75, 0.9, 0.85, 0.8),
    ),
    (
        "Wools and foam",
        "7.5 cm fibreglass, rigid backing(25)",
        (0.35, 0.65, 0.8, 0.9, 0.85, 0.8),
    ),
    (
        "Wools and foam",
        "10 cm fibreglass, rigid backing(25)",
        (0.45, 0.9, 0.95, 1.0, 0.95, 0.85),
    ),
    (
        "Wools and foam",
        "5 cm mineral wool (40 kg/m3), glued to wall, untreated surface(8,9)",
        (0.15, 0.7, 0.6, 0.6, 0.85, 0.9),
    ),
    (
        "Wools and foam",
        "5 cm mineral wool (40 kg/m3), glued to wall, surface sprayed with thin plastic solution(8,9)",
        (0.15, 0.7, 0.6, 0.6, 0.75, 0.75),
    ),
    (
        "Wools and foam",
        "5 cm mineral wool (70 kg/m3) 30 cm in front of wall(8,9)",
        (0.7, 0.45, 0.65, 0.6, 0.75, 0.65),
    ),
    (
        "Wools and foam (cont.)",
        "5 cm wood-wool set in mortar(8,9)",
        (0.08, 0.17, 0.35, 0.45, 0.65, 0.65),
    ),
    (
        "Wools and foam (cont.)",
        "5.1 cm fibreglass, panels with plastic sheet wrapping and perforated metal facing(2)",
        (0.33, 0.79, 0.99, 0.91, 0.76, 0.64),
    ),
    (
        "Wools and foam (cont.)",
        "5.1 cm fibreglass,(2) 24-48 kg/m3",
        (0.17, 0.55, 0.8, 0.9, 0.85, 0.8),
    ),
    (
        "Wools and foam (cont.)",
        "Acoustic tile, 1.27 cm thick(5)",
        (0.07, 0.21, 0.66, 0.75, 0.62, 0.49),
    ),
    (
        "Wools and foam (cont.)",
        "Acoustic tile, 1.9 cm thick(5)",
        (0.09, 0.28, 0.78, 0.84, 0.73, 0.64),
    ),
    (
        "Wools and foam (cont.)",
        "Polyurethane foam, 2.5 cm thick",
        (0.16, 0.25, 0.45, 0.84, 0.97, 0.87),
    ),
    (
        "Wools and foam (cont.)",
        "Thermafleece, sheep wool absorbent 100 mm thick(26)",
        (0.47, 0.86, 1.0, 0.94, 0.96, 1.02),
    ),
    (
        "Ballast",
        "Ballast or other crushed stone, 3.18 cm, 15.2 deep(2)",
        (0.19, 0.23, 0.43, 0.37, 0.58, 0.62),
    ),
    (
        "Ballast",
        "Ballast or other crushed stone, 3.18 cm, 30.5 cm deep(2)",
        (0.27, 0.58, 0.48, 0.54, 0.73, 0.63),
    ),
    (
        "Ballast",
        "Ballast or other crushed stone, 3.18 cm, 45.7 cm deep(2)",
        (0.41, 0.53, 0.64, 0.84, 0.91, 0.63),
    ),
    (
        "Ballast",
        "Ballast or other crushed stone, 0.64 cm, 15.2 cm deep(2,11)",
        (0.22, 0.64, 0.7, 0.79, 0.88, 0.72),
    ),
    (
        "Microperforated absorber",
        "4 cm cavity(23)",
        (0.08, 0.27, 0.7, 0.35, 0.11, 0.04),
    ),
    (
        "Microperforated absorber",
        "40 cm cavity(23)",
        (0.64, 0.56, 0.41, 0.28, 0.13, 0.06),
    ),
    (
        "Diffusers",
        "Hybrid absorber-diffuser (BAD panel mounted on 2.5 cm fibreglass)(23)",
        (0.17, 0.4, 0.86, 1.0, 0.84, 0.61),
    ),
    (
        "Diffusers",
        "2D N = 7 QRD, design freq. = 500 Hz(23)",
        (0.14, 0.12, 0.14, 0.2, 0.09, 0.12),
    ),
    (
        "Diffusers",
        "2D N = 7 QRD as line above, with cloth covering(23)",
        (0.16, 0.17, 0.28, 0.41, 0.26, 0.3),
    ),
    (
        "Diffusers",
        "1D N = 7 QRD, design freq. = 500 Hz(23)",
        (0.11, 0.1, 0.07, 0.08, 0.06, 0.06),
    ),
    (
        "Diffusers",
        "1D N = 7 QRD as line above, with cloth covering(23)",
        (0.13, 0.14, 0.2, 0.24, 0.2, 0.23),
    ),
    (
        "Green wall systems",
        "Data from Azkorra et al.(27)",
        (0.46, 0.42, 0.36, 0.38, 0.45, 0.5),
    ),
    (
        "Green wall systems",
        "Data from Wong et al.(28) (100% greenery)",
        (0.09, 0.23, 0.43, 0.46, 0.5, 0.48),
    ),
    (
        "Green wall systems",
        "Data from Yang et al.(29)",
        (0.61, 0.62, 0.69, 0.68, 0.68, 0.72),
    ),
    (
        "Top soil ... vegetative cover(29)",
        "0%, bare soil",
        (0.27, 0.57, 0.76, 0.9, 0.89, 0.84),
    ),
    ("Top soil ... vegetative cover(29)", "20%", (0.34, 0.63, 0.79, 0.92, 0.89, 0.81)),
    ("Top soil ... vegetative cover(29)", "40%", (0.39, 0.68, 0.83, 0.95, 0.9, 0.83)),
    ("Top soil ... vegetative cover(29)", "60%", (0.45, 0.72, 0.85, 0.97, 0.9, 0.8)),
    ("Top soil ... vegetative cover(29)", "80%", (0.46, 0.73, 0.85, 0.97, 0.89, 0.72)),
    (
        "Top soil ... vegetative cover(29)",
        "100%, completely covered",
        (0.49, 0.75, 0.89, 0.98, 0.91, 0.73),
    ),
    (
        "Top soil ... moisture content(29)",
        "12.5%",
        (0.26, 0.55, 0.73, 0.89, 0.85, 0.67),
    ),
    ("Top soil ... moisture content(29)", "17%", (0.25, 0.51, 0.69, 0.81, 0.78, 0.57)),
    (
        "Top soil ... moisture content(29)",
        "20.4%",
        (0.23, 0.45, 0.57, 0.64, 0.58, 0.38),
    ),
    ("Top soil ... moisture content(29)", "23.8%", (0.2, 0.36, 0.43, 0.46, 0.38, 0.2)),
    (
        "Top soil ... moisture content(29)",
        "25.4%",
        (0.14, 0.28, 0.33, 0.34, 0.29, 0.12),
    ),
    ("Top soil ... moisture content(29)", "34.1%", (0.07, 0.22, 0.23, 0.24, 0.2, 0.06)),
)


#: The twenty-nine references Cox prints on the page after the table, PDF page
#: 537 (printed p. 480), keyed by the number the rows carry as a superscript
#: and written in the short form the catalogue holds. Transcribed with the
#: table and by the same second reader, so a credit that moved from one row to
#: another fails the comparison the way a moved digit does.
COX_A_REFERENCES: dict[str, str] = {
    "1": "Beranek (1954)",
    "2": "Harris (1991)",
    "3": "Templeton (1997)",
    "4": "Mankovsky (1971)",
    "5": "Everest (2001)",
    "6": "Fry (1987)",
    "7": "Parkin, Humphreys and Cowell (1979)",
    "8": "Kristensen (1984)",
    "9": "Lynge (2001)",
    "10": "Beranek and Hidaka (1998)",
    "11": "Physikalisch-Technische Bundesanstalt (accessed 2003)",
    "12": "Petersen (1983)",
    "13": "Young (1959)",
    "14": "Bobran (1973)",
    "15": "Beranek (1969)",
    "16": "Davies, Orlowski and Lam (1994)",
    "17": "Bies and Hansen (1996)",
    "18": "Adelman-Larsen, Thompson and Gade (2010)",
    "19": "Knudsen and Harris (1953)",
    "20": "Riverbank Acoustical Laboratories (accessed 2008)",
    "21": "ISO/TR 11690-3 (1997)",
    "22": "Davis and Davis (1997)",
    "23": "RPG Diffusor Systems (accessed 2003)",
    "24": "Fasold and Winkler (1976)",
    "25": "Kinsler, Frey, Coppens and Sanders (2000)",
    "26": "Greenshop (accessed 2008)",
    "27": "Azkorra et al. (2015)",
    "28": "Wong et al. (2010)",
    "29": "Yang, Kang and Cheal (2013)",
}


#: What Arau prints where a number would be on the row of air-conditioning
#: grilles: one interval, written once, lying across the first two columns.
RANGE_ACROSS_COLUMNS = "0.15 – 0.50"

#: The octave bands Arau's Table 6.1 prints, in the order of the value tuples
#: below. The page prints the frequencies bare, with no unit anywhere.
ARAU_6_1_BANDS_HZ = (125, 250, 500, 1000, 2000, 4000)

#: ``(printed row number, name as printed, values per band)``, every row of
#: Arau-Puchades (1999) Table 6.1 in the order printed, Spanish and all. A
#: ``(low, high)`` pair is an interval the page writes with the word "a" on a
#: line of its own; ``None`` is a cell the page fills with a dash. Rows 63 to
#: 65 are the air attenuation coefficient m in reciprocal metres rather than an
#: absorption coefficient, and are here because the page prints them in this
#: table; the catalogue does not serve them and the tests say so.
ARAU_6_1_ABSORPTION: tuple[tuple[int, str, tuple[object, ...]], ...] = (
    (1, "Pared de ladrillo", (0.025, 0.025, 0.03, 0.04, 0.05, 0.07)),
    (2, "Pared de ladrillo pintado", (0.01, 0.01, 0.02, 0.02, 0.02, 0.02)),
    (3, "Pared de ladrillo encalada", (0.02, 0.02, 0.02, 0.03, 0.03, None)),
    (4, "Bloque de hormigón áspero", (0.36, 0.44, 0.31, 0.29, 0.39, 0.25)),
    (5, "Bloque de hormigón pintado", (0.10, 0.05, 0.06, 0.07, 0.09, 0.08)),
    (
        6,
        "Hormigón de obra fino",
        (
            (0.01, 0.02),
            (0.01, 0.02),
            (0.02, 0.04),
            (0.02, 0.06),
            (0.02, 0.08),
            (0.03, 0.10),
        ),
    ),
    (7, "Hormigón de obra pintado al esmalte", (0.01, 0.01, 0.01, 0.02, 0.02, 0.02)),
    (8, "Hormigón enfoscado muy fino", (0.004, 0.004, 0.005, 0.006, 0.008, 0.015)),
    (9, "Yeso, escayola, 5 cm", (0.08, 0.06, 0.05, 0.04, 0.04, 0.04)),
    (10, "Yeso, escayola fibrosa, 5 cm", (0.35, 0.30, 0.20, 0.55, 0.10, 0.04)),
    (
        11,
        "Enlucido de paredes",
        (
            (0.01, 0.04),
            (0.01, 0.04),
            (0.02, 0.04),
            (0.03, 0.06),
            (0.04, 0.06),
            (0.03, 0.06),
        ),
    ),
    (12, "Yeso, escayola, con acabado áspero", (0.14, 0.10, 0.06, 0.05, 0.04, 0.03)),
    (13, "Yeso, escayola, con acabado fino", (0.14, 0.10, 0.06, 0.04, 0.04, 0.03)),
    (
        14,
        "Yeso 25 mm con cámara aire en el dorso",
        (0.16, 0.10, 0.06, 0.04, 0.04, 0.04),
    ),
    (
        15,
        "Tablero de cartón yeso de 13 mm con cámara aire en el dorso sujeto por perfiles 5 x 10 cm interdistanciados 40 cm",
        (0.29, 0.10, 0.05, 0.04, 0.07, 0.09),
    ),
    (
        16,
        "Tablero de yeso de 15 mm montado en idénticas condiciones que 15",
        (0.20, 0.08, 0.05, 0.05, 0.05, 0.05),
    ),
    (17, "Mármol o baldosa pulida", (0.01, 0.01, 0.01, 0.01, 0.02, 0.02)),
    (
        18,
        "Contrachapado de madera de 10 mm formando pequeñas cavidades máx. 25 mm en dorso",
        (0.28, 0.22, 0.17, 0.09, 0.10, 0.08),
    ),
    (
        19,
        "Contrachapado de madera de 6 mm con 80 mm cavidad de aire rellenada parcialmente con material absorbente",
        (0.60, 0.30, 0.10, 0.09, 0.09, 0.09),
    ),
    (
        20,
        "Igual que 19, pero sin material absorbente",
        (0.40, 0.18, 0.08, 0.05, 0.04, 0.03),
    ),
    (
        21,
        "Contrachapado de madera de 3 mm con cavidad de aire en el dorso",
        (0.11, 0.21, 0.10, 0.05, 0.03, 0.02),
    ),
    (
        22,
        "Madera fijada sólidamente a una pared o a un sólido",
        (0.04, 0.04, 0.03, 0.03, 0.03, 0.02),
    ),
    (
        23,
        "Plafón de madera de pino de 20 mm y 50 mm de cámara de aire",
        (0.10, 0.11, 0.10, 0.08, 0.08, 0.05),
    ),
    (
        24,
        "Plafón de madera de cedro con cámara en el dorso",
        (0.20, 0.15, 0.15, 0.10, 0.10, 0.10),
    ),
    (
        25,
        "Madera delgada (5 a 10 mm) formando cámara de aire en el dorso",
        (0.42, 0.21, 0.06, 0.05, 0.04, 0.04),
    ),
    (
        26,
        "Madera (10 a 13 mm) formando cámara de aire 50 a 100 mm en el dorso",
        (0.30, 0.25, 0.20, 0.17, 0.15, 0.10),
    ),
    (27, "Madera sólida, 5 cm de espesor", (0.01, 0.05, 0.05, 0.04, 0.04, 0.04)),
    (28, "Vidrios de 6 mm área pequeña", (0.04, 0.04, 0.03, 0.03, 0.02, 0.02)),
    (29, "Vidrios de 6 mm área grande", (0.18, 0.06, 0.04, 0.03, 0.02, 0.018)),
    (30, "Vidrio de 3 mm ventana", (0.35, 0.25, 0.18, 0.12, 0.07, 0.04)),
    (31, "Vitrinas emplomadas 3 mm", (0.64, 0.40, 0.20, 0.13, 0.17, 0.05)),
    (32, "Vidrios pesados luna grande", (0.18, 0.06, 0.04, 0.03, 0.02, 0.02)),
    (33, "Pavimento cerámico", (0.01, 0.01, 0.01, 0.02, 0.02, 0.02)),
    (34, "Baldosa de tierra sobre hormigón", (0.02, 0.03, 0.03, 0.03, 0.03, 0.02)),
    (35, "Loseta de caucho sobre hormigón", (0.019, 0.033, 0.04, 0.036, 0.018, 0.02)),
    (36, "Loseta de linóleo sobre hormigón", (0.04, 0.03, 0.04, 0.04, 0.03, 0.02)),
    (
        37,
        "Loseta de plástico vinílico sobre hormigón",
        (0.04, 0.03, 0.04, 0.04, 0.03, 0.02),
    ),
    (
        38,
        "Losa de corcho de 2 cm encerada y pulida",
        (0.04, 0.03, 0.05, 0.11, 0.07, 0.02),
    ),
    (39, "Parqué sobre rastreles", (0.05, 0.03, 0.06, 0.09, 0.10, 0.20)),
    (40, "Parqué encima de hormigón", (0.04, 0.04, 0.07, 0.06, 0.06, 0.07)),
    (41, "Madera barnizada sobre vigas", (0.15, 0.11, 0.10, 0.07, 0.06, 0.07)),
    (
        42,
        "Plataformas de madera con gran profundidad de aire",
        (0.40, 0.30, 0.20, 0.17, 0.15, 0.10),
    ),
    (43, "Alfombra gruesa encima de hormigón", (0.02, 0.06, 0.14, 0.37, 0.60, 0.65)),
    (
        44,
        "Alfombra gruesa encima de fieltro o caucho espumado",
        (0.08, 0.24, 0.57, 0.69, 0.71, 0.73),
    ),
    (
        45,
        "Alfombra pesada con látex impermeable encima de fieltro o caucho espumado",
        (0.08, 0.27, 0.39, 0.34, 0.48, 0.63),
    ),
    (46, "Moqueta de 10 mm sobre pared", (0.09, 0.08, 0.21, 0.27, 0.27, 0.37)),
    (
        47,
        "Moqueta de 3 mm sobre fieltro encima de hormigón",
        (0.11, 0.14, 0.37, 0.43, 0.27, 0.25),
    ),
    (48, "Moqueta de goma de 5 mm", (0.04, 0.04, 0.08, 0.12, 0.13, 0.10)),
    (
        49,
        "Cortina ligera de algodón de 340 g/m2 de gramaje, plana a la pared",
        (0.03, 0.04, 0.11, 0.17, 0.24, 0.35),
    ),
    (
        50,
        "Cortina de algodón de 480 g/m2 plana a la pared",
        (0.05, 0.07, 0.13, 0.22, 0.32, 0.35),
    ),
    (
        51,
        "Cortina de terciopelo de 620 g/m2 plana a la pared",
        (0.05, 0.12, 0.35, 0.45, 0.38, 0.36),
    ),
    (
        52,
        "Cortina de algodón de 340 g/m2 fruncida al 150 %",
        (0.07, 0.31, 0.49, 0.81, 0.66, 0.54),
    ),
    (
        53,
        "Cortina de algodón de 480 g/m2 fruncida al 150 %",
        (0.07, 0.31, 0.49, 0.75, 0.70, 0.60),
    ),
    (
        54,
        "Cortina de algodón de 620 g/m2 fruncida al 150 %",
        (0.14, 0.35, 0.55, 0.72, 0.70, 0.65),
    ),
    (
        55,
        "Cortina de algodón de 340 g/m2 fruncida al 187,5 %",
        (0.03, 0.12, 0.15, 0.27, 0.37, 0.42),
    ),
    (
        56,
        "Cortina de algodón de 340 g/m2 fruncida al 175 %",
        (0.04, 0.23, 0.40, 0.57, 0.53, 0.40),
    ),
    (57, "Fieltro de 25 mm", (0.18, 0.36, 0.71, 0.79, 0.82, 0.85)),
    (
        58,
        "Fieltro de 25 mm con intervalos de aire a 50 mm",
        (0.35, 0.62, 0.88, 0.92, 0.78, 0.84),
    ),
    (59, "Fibra de vidrio 22 kg/m2 30 mm", (0.10, 0.32, 0.55, 0.66, 0.79, 0.77)),
    (60, "Ídem 50 mm", (0.19, 0.43, 0.77, 0.82, 0.94, 0.83)),
    (61, "Ídem 70 mm", (0.33, 0.65, 0.88, 0.91, 0.97, 0.94)),
    (62, "Ídem 100 mm", (0.54, 0.87, 0.1, 0.96, 0.97, 0.93)),
    (63, "m: Aire (30 % HR) m-1", (None, None, None, None, 0.00327, 0.011)),
    (64, "m: Aire (50 % HR) m-1", (None, None, None, None, 0.0026, 0.0075)),
    (65, "m: Aire (70 % HR) m-1", (None, None, None, None, 0.00196, 0.0065)),
    (66, "Agua (piscinas)", (0.01, 0.01, 0.01, 0.01, 0.02, 0.02)),
    (67, "Abertura de escenario", (0.30, 0.40, 0.50, 0.60, 0.60, 0.50)),
    (
        68,
        "Audiencia ocupando butacas bien tapizadas",
        (0.52, 0.68, 0.85, 0.97, 0.93, 0.85),
    ),
    (69, "Butacas bien tapizadas", (0.49, 0.66, 0.80, 0.88, 0.82, 0.70)),
    (70, "Butacas tapizadas de cuero", (0.44, 0.54, 0.60, 0.62, 0.58, 0.50)),
    (
        71,
        "Bancos de iglesia de madera 100 % ocupados",
        (0.57, 0.61, 0.75, 0.86, 0.91, 0.86),
    ),
    (72, "Asientos de madera 100 % ocupados", (0.60, 0.74, 0.88, 0.96, 0.93, 0.85)),
    (73, "Asientos de madera 75 % ocupados", (0.46, 0.56, 0.65, 0.75, 0.72, 0.65)),
    (74, "Lana de roca 100 kg/m2 30 mm", (0.07, 0.40, 0.88, 0.92, 0.96, 1.05)),
    (75, "Ídem 50 mm", (0.19, 0.74, 0.95, 0.98, 0.96, 1.04)),
    (76, "Ídem 80 mm", (0.35, 0.86, 0.92, 0.99, 1.02, 1.03)),
    (
        77,
        "Espuma de poliuretano de 15 mm con forro de plástico ligero",
        (0.02, 0.08, 0.24, 0.48, 0.72, 0.70),
    ),
    (78, "Ídem 30 mm", (0.13, 0.75, 0.70, 1.02, 1.00, 0.95)),
    (
        79,
        "Espuma de poliuretano con forro film de plástico",
        (0.21, 0.52, 0.64, 0.64, 0.60, 0.62),
    ),
    (
        80,
        "Panel metálico perforado Ø 20 mm p = 14.9 % Cavidad de aire 100 mm. Espesor fibra interior 30 mm. Espesor del plafón perforado 0.95 mm",
        (0.27, 0.78, 0.93, 0.71, 0.55, 0.51),
    ),
    (
        81,
        "Igual que 80 con cavidad de aire 200 mm",
        (None, 0.88, 0.88, 0.63, 0.54, 0.47),
    ),
    (
        82,
        "Igual que 80 con cavidad de aire 400 mm",
        (None, 0.78, 0.66, 0.73, 0.61, 0.48),
    ),
    (
        83,
        "Resonador del tipo figura 6.9 y F.6.7 de ranuras en bloques de hormigón de 200 x 200 x 500 mm con fibra de vidrio en los alveolos",
        (0.72, 0.58, 0.77, 0.72, 0.49, 0.45),
    ),
    (
        84,
        "Igual que 83, pero con alveolos vacíos",
        (0.69, 0.13, 0.07, 0.07, 0.14, 0.15),
    ),
    (
        85,
        "Revestimiento textil de muros 100 % poliamida, masa superficial 0.640, 1.8 mm grueso y reverso de fibras minerales",
        (0.02, 0.03, 0.09, 0.14, 0.29, 0.57),
    ),
    (
        86,
        "Velo rizado 100 % PL VA 1.75 kg/m2 de 6 mm, parte dorsal yute o algodón",
        (0.05, 0.12, 0.17, 0.25, 0.45, 0.88),
    ),
    (87, "Tejido de napa + film PE 3 mm", (0.02, 0.05, 0.10, 0.14, 0.22, 0.24)),
    (
        88,
        "Tejido 53 % algodón 33 % fibra 14 % lino 0.24 kg/m2",
        (0.02, 0.04, 0.07, 0.26, 0.30, 0.15),
    ),
    (
        89,
        "Tela de lino y en el dorso papel 0.48 kg/m2 de 1.2 mm",
        (0.02, 0.03, 0.07, 0.10, 0.14, 0.16),
    ),
    (
        90,
        "Revestimiento textura alveolar textil con fibras y en el dorso espuma de poliuretano 0.650 kg/m2 de 7 mm",
        (0.06, 0.09, 0.14, 0.19, 0.60, 0.88),
    ),
    (91, "Ídem, pero 0.940 kg/m2 de 17 mm", (0.05, 0.19, 0.35, 0.84, 0.98, 0.89)),
    (
        92,
        "Revestimiento textil de suelo o moqueta de terciopelo trenzado 100 % de 1.2 kg/m2 espuma SBR en zona dorsal",
        (0.01, 0.04, 0.09, 0.015, 0.30, 0.38),
    ),
    (
        93,
        "Moqueta con espuma SBR en zona dorsal 2.235 kg/m2, 10 mm",
        (0.03, 0.08, 0.28, 0.33, 0.38, 0.42),
    ),
    (
        94,
        "Moqueta tapiz trenzado 1.575 kg/m2, 5.5 mm",
        (0.01, 0.04, 0.07, 0.18, 0.39, 0.42),
    ),
    (
        95,
        "Pared de baldosa perforada, con lana mineral 5 cm + 50 cm de cámara de aire",
        (0.5, 0.41, 0.35, 0.39, 0.26, 0.32),
    ),
    (
        96,
        "Rejillas del sistema de aire acondicionado",
        (RANGE_ACROSS_COLUMNS, None, None, None, None, None),
    ),
    (
        97,
        "Grava suelta y húmeda de 20 cm de grosor",
        (0.15, 0.25, 0.40, 0.55, 0.60, 0.60),
    ),
    (98, "Suelo áspero", (0.21, 0.52, 0.64, 0.64, 0.60, 0.62)),
    (99, "Hierba 5 cm de altura", (0.11, 0.26, 0.60, 0.69, 0.82, 0.99)),
)

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Eleven tables of airborne and impact insulation, read a second time.

Seven tables of Harris 3e Chapter 31 (Spanish edition), Rossing (2014)
Table 11.4, and Tables 19.2 to 19.4 of Harris (1977), the Spanish edition of
the first Handbook of Noise Control. Each was transcribed by two readers who
never saw each other's work and compared cell by cell before either was
kept: 501 cells over the eleven tables, and not one disagreement. The
comparison still cropped every table from the page and checked the agreed
reading against it, in case both readers made the same slip.

This is the second reading, kept as the oracle the tests check against. Every
cell is **as the page prints it**: decimal commas stay commas, a range keeps
its hyphen, a blank cell is an empty string, and the daggers of the window
table stay on the cells they mark. Each table is a tuple of
``(row label, cells)`` in printed order, with the cells in the order of the
page's columns after the label.
"""

from __future__ import annotations

#: Harris 3e Table 31.2: STC of seven stud walls, without then with cavity
#: absorbent, plasterboard layers 1/1, 1/2 and 2/2.
HARRIS_31_2: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Tirantes de madera de 38 por 89 mm", ("33", "41", "43", "36", "44", "46")),
    ("Tirantes de acero de calibre 24 de 65 mm", ("36", "44", "46", "44", "48", "52")),
    ("Tirantes de acero de calibre 24 de 90 mm", ("39", "45", "50", "45", "49", "56")),
    (
        "Tirantes de madera de 38 por 89 mm con canales flexibles de acero sobre un lado",
        ("40", "44", "52", "48", "52", "56"),
    ),
    (
        "Tirantes de madera de 38 por 89 mm al tresbolillo",
        ("41", "47", "52", "50", "53", "55"),
    ),
    (
        "Tirantes de acero que soportan carga, de 150 mm, con canales flexibles de acero sobre un lado",
        ("45", "51", "56", "56", "58", "61"),
    ),
    (
        "Tirantes de madera dobles de 38 por 89 mm con un espacio de 25 mm entre ellos",
        ("46", "52", "57", "57", "60", "63"),
    ),
)


#: Harris 3e Table 31.3: nominal thickness in mm; lightweight kg per block
#: and STC; normal weight kg per block and STC.
HARRIS_31_3: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("90", ("7", "43", "10", "44")),
    ("150", ("10", "44", "15", "46")),
    ("200", ("13", "45", "17", "48")),
    ("250", ("15", "47", "21", "49")),
    ("300", ("18", "48", "25", "51")),
)


#: Harris 3e Table 31.5: STC without glass fibre on one side and on both,
#: then with glass fibre on one side and on both. Blank cells are blank on
#: the page.
HARRIS_31_5: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Bloques sin revestir", ("50", "", "", "")),
    ("Aplicada directamente", ("50", "49", "", "")),
    ("Cubierta de madera de 40 mm", ("53", "54", "55", "59")),
    ("Canales flexibles de 13 mm", ("51", "49", "54", "49")),
    ("Cubierta flexible de 50 mm", ("52", "52", "59", "64")),
    ("Tirantes de acero de 65 mm", ("58", "57", "60", "72")),
    ("Cubierta flexible de 75 mm", ("57", "", "61", "")),
)


#: Harris 3e Table 31.6: surface density in kg/m2, STC unsealed, STC well
#: sealed.
HARRIS_31_6: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Madera con núcleo hueco", ("7", "17", "20")),
    ("Madera con núcleo macizo", ("20", "20", "28")),
    ("Acero con núcleo hueco (calibre 18)", ("25", "20", "30")),
    (
        "Puertas de comunicación (2 puertas de madera de núcleo hueco, cámara de 100 mm)",
        ("7 each", "22", "26"),
    ),
    (
        "Puertas de comunicación (2 puertas de madera maciza o de acero hueco, con 70 mm de cámara de aire)",
        ("20 each", "28", "40"),
    ),
    (
        "Puertas de comunicación (2 puertas de madera maciza o de acero hueco, con 70 mm de cámara con absorción)",
        ("20 each", "40", "44"),
    ),
    (
        "Puertas de comunicación (2 puertas de madera maciza o de acero hueco, con 230 mm de cámara con absorción)",
        ("20 each", "42", "50"),
    ),
)


#: Harris 3e Table 31.7: weight in kg/m2, weight in lb/ft2, STC. Every door
#: is 45 mm (1 3/4 in) thick, by the column heading.
HARRIS_31_7: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Madera de núcleo hueco", ("7", "1,5", "20")),
    (
        "Madera de núcleo hueco (30 % de área acristalada con vidrio de 3 mm)",
        ("7", "1,5", "19"),
    ),
    ("Madera de núcleo macizo", ("17", "3,6", "26")),
    ("Puerta con cubierta de acero, núcleo de poliuretano rígido", ("16", "3,2", "26")),
    (
        "Puerta de plástico reforzado con fibra de vidrio, núcleo de poliuretano rígido",
        ("12", "2,4", "24"),
    ),
)


#: Harris 3e Table 31.8, as printed: the row label is the STC, and the cells
#: are single glass, double 3 mm and 3 mm, double 6 mm and 6 mm, double 6 mm
#: and L-7 mm.
HARRIS_31_8: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("48", ("", "", "", "100 mm")),
    ("46", ("", "", "120 mm", "60 mm")),
    ("44", ("", "150 mm", "80 mm", "40 mm")),
    ("42", ("", "100 mm", "50 mm", "25 mm")),
    ("40", ("L-20 mm†", "70 mm", "30 mm", "16 mm")),
    ("38", ("L-12 mm†", "50 mm", "20 mm", "10 mm")),
    ("36", ("12 mm", "30 mm", "13 mm", "")),
    ("34", ("L-6 mm†", "20 mm", "8 mm", "")),
    ("32", ("6 mm", "10 mm", "", "")),
    ("30", ("3 mm, 4 mm", "6 mm", "", "")),
)


#: Harris 3e Table 31.9: printed row number; group heading, floor, ceiling,
#: STC.
HARRIS_31_9: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("1", ("Viguetas de hormigón", "Hormigón reforzado 90 mm", "Ninguno", "48")),
    ("2", ("Viguetas de hormigón", "Hormigón reforzado 130 mm", "Ninguno", "52")),
    (
        "3",
        (
            "Perfiles de acero",
            "Perfiles de acero con un tablero de hormigón de 50 mm mínimo",
            "Capas de escayola de 16 mm para revestir los canales en donde encajan los perfiles, con material de absorción en la cámara optativo",
            "53",
        ),
    ),
    (
        "4",
        (
            "Tirantes de madera o marcos",
            "Subsuelo de 19 mm T&G o tablero de láminas de madera de 15,5 mm",
            "Capa de escayola de 16 mm adherida a los canales metálicos flexibles, con material absorbente en la cámara",
            "48",
        ),
    ),
    (
        "5",
        (
            "Tirantes de madera o marcos",
            "Igual que 4, con un tablero adicional de láminas de madera de 15,5 mm en el suelo",
            "Capa de escayola de 16 mm adherida a los canales metálicos flexibles, con material absorbente en la cámara",
            "52",
        ),
    ),
    (
        "6",
        (
            "Tirantes de madera o marcos",
            "Capa de hormigón-escayola de 19 mm (de al menos 34 kg/m²) sobre subsuelo con T&G de 19 mm o con tablero de láminas de madera de 15,5 mm",
            "Dos capas de escayola de 13 mm o 16 mm",
            "55",
        ),
    ),
    (
        "7",
        (
            "Tirantes de madera o marcos",
            "Igual que 6",
            "Dos capas de escayola de 13 mm o 16 mm, adheridas a los canales metálicos flexibles, con material absorbente en la cámara",
            "55",
        ),
    ),
    (
        "8",
        (
            "Tirantes de madera o marcos",
            "Capa de hormigón ligero de 50 mm (de al menos 70 kg/m²) sobre subsuelo con T&G de 19 mm o con tablero de láminas de madera de 15,5 mm",
            "Dos capas de escayola de 13 mm o 16 mm",
            "56",
        ),
    ),
    (
        "9",
        (
            "Tirantes de madera o marcos",
            "Igual que 8",
            "Capa de escayola de 16 mm, adherida a los canales metálicos flexibles",
            "57",
        ),
    ),
    (
        "10",
        (
            "Tirantes de madera o marcos",
            "Igual que 8",
            "Capa de escayola de 16 mm, adherida a los canales metálicos flexibles con material absorbente en la cámara",
            "60",
        ),
    ),
)


#: Rossing (2014) Table 11.4: transmission loss at 125, 250, 500, 1000, 2000
#: and 4000 Hz, then the STC.
ROSSING_11_4: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "1/2 inch drywall on both sides of wooden studs",
        ("17", "31", "33", "40", "38", "36", "33"),
    ),
    (
        "1/2 inch drywall on wooden studs with 2 inches of insulation",
        ("15", "30", "34", "44", "46", "41", "37"),
    ),
    (
        "Double layer of 1/2 inch drywall on wooden studs",
        ("25", "34", "41", "51", "48", "50", "41"),
    ),
    (
        "1/2 inch drywall on staggered wooden studs",
        ("23", "28", "39", "46", "54", "44", "39"),
    ),
    (
        "1/2 inch drywall on staggered wooden studs with 2 inches of insulation",
        ("29", "38", "45", "52", "58", "50", "48"),
    ),
    ("1/2 inch drywall on metal studs", ("22", "27", "43", "47", "37", "46", "39")),
    (
        "1/2 inch drywall on metal studs with 2 inches of insulation",
        ("26", "41", "52", "54", "45", "51", "45"),
    ),
    ("8 inch thick concrete masonry units", ("36", "44", "50", "54", "58", "56", "53")),
    ("Open-plane office partition", ("10", "12", "12", "12", "12", "11", "12")),
    ("4 inch thick brick wall", ("32", "34", "40", "47", "55", "61", "45")),
    (
        "1/2 inch drywall inside/1 inch stucco outside on wooden studs",
        ("21", "33", "41", "46", "47", "51", "42"),
    ),
    ("Single-paned 1/8 inch thick glass", ("18", "21", "26", "31", "33", "22", "26")),
    ("1/2 inch thick laminated glass", ("31", "34", "38", "40", "37", "46", "40")),
    (
        "Double-paned 1/8 inch thick glass with 2 inch air gap",
        ("13", "25", "35", "44", "49", "43", "37"),
    ),
    (
        "Hollow wooden door, 1 3/4 inch thick",
        ("14", "19", "23", "18", "17", "21", "19"),
    ),
    ("Solid wooden door, 1 3/4 inch thick", ("29", "31", "31", "31", "39", "43", "34")),
    ("Hollow metal door, 1 3/4 inch thick", ("24", "23", "29", "31", "24", "40", "28")),
    ("Filled metal door, 1 3/4 inch thick", ("26", "34", "40", "48", "44", "52", "43")),
    (
        "Wood joist floor/ceiling with 1/2 inch plywood subfloor and 1/2 inch drywall",
        ("23", "32", "36", "45", "49", "56", "37"),
    ),
    ("8 inch thick concrete slab floor", ("32", "38", "47", "52", "57", "63", "50")),
    ("Wood plank shingled roof", ("29", "33", "37", "44", "55", "63", "43")),
    (
        "Wood plank shingled roof with 1/2 inch drywall ceiling, 4 inches of insulation",
        ("35", "42", "49", "62", "67", "79", "53"),
    ),
    (
        "Corrugated steel roof with 1 inch of sprayed cellulose",
        ("17", "22", "26", "30", "35", "41", "30"),
    ),
)


#: Harris (1977) Table 19.2: average improvement in impact sound insulation,
#: db.
HARRIS_1977_19_2: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Linóleum, 3,2 mm", ("3",)),
    ("Baldosa de caucho, 3,2 mm", ("5",)),
    ("Asfalto", ("5-7",)),
    ("Suelo de parquet sobre listones", ("7",)),
    ("Plancha de corcho, 8 mm", ("10",)),
    ("Moqueta Wilton, 9,5 mm", ("24",)),
    ("4 mm de linóleum sobre 6,4 mm de plancha de corcho duro", ("6",)),
    ("4 mm de linóleum sobre 6,4 mm de plancha de corcho blando", ("14",)),
    ("4 mm de linóleum sobre 12,8 mm de corcho blando", ("16",)),
    ("4 mm de linóleum sobre 12,8 mm de tablero blando", ("18",)),
)


#: Harris (1977) Table 19.3: average improvement in impact sound insulation,
#: db.
HARRIS_1977_19_3: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("37 mm de franjas de hormigón sobre 12 mm de tablero blando", ("10",)),
    ("37 mm de franjas de hormigón sobre 25 mm de corcho granulado", ("10",)),
    ("37 mm de franjas de hormigón sobre 25 mm de cubierta elástica", ("24",)),
    ("25 mm de asfalto o 12 mm de tablero blando", ("15",)),
    ("37 mm de asfalto sobre 25 mm de lana mineral", ("27",)),
)


#: Harris (1977) Table 19.4: additional load in kg/cm2, average improvement
#: in impact sound insulation, db.
HARRIS_1977_19_4: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Suelo de parquet sobre listones", ("0", "7")),
    (
        "Suelo de parquet sobre listones descansando sobre bandas de corcho de 37 mm",
        ("0", "10"),
    ),
    (
        "Suelo de parquet sobre listones descansando sobre bandas de lana mineral de 25 mm",
        ("0,84", "15"),
    ),
    ("Suelo de parquet (sin listones) sobre 50 mm de arena seca", ("0", "11")),
    ("Suelo de parquet (sin listones) sobre 50 mm de serrín seco", ("0,84", "21")),
    (
        "Suelo de parquet (sin listones) sobre cubierta de lana de vidrio de 18 mm",
        ("0", "27"),
    ),
    (
        "Suelo de parquet (sin listones) sobre cubierta de lana de vidrio de 18 mm",
        ("0,84", "22"),
    ),
    (
        "Suelo de parquet (sin listones) sobre cubierta de lana de vidrio de 25 mm",
        ("0,84", "21"),
    ),
)

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Transmission loss as one book prints it, read a second time.

Source: Bies, Hansen & Howard (2017) Table 7.6, "Representative values of
airborne sound transmission loss for some common structures and materials",
PDF pages 428 to 433 (printed pp. 399 to 404). The table is printed sideways
on the page. Columns: a description, a thickness in millimetres, a surface
weight in kilograms per square metre, and the 63 Hz to 8 kHz octave bands in
decibels.

This transcription was made from the rendered pages independently of the one
in the package's data file, by a second reader who never saw the first, and
the two were compared cell by cell before either was kept: ninety-four rows,
eight bands, a thickness and a weight, no difference.

``None`` is a cell the page prints as an em dash. The names are kept exactly
as printed, "joints scaled" and "no of oak surface" included.
"""

from __future__ import annotations

#: The octave bands Table 7.6 prints, in the order of the value tuples below.
BIES_7_6_BANDS_HZ = (63, 125, 250, 500, 1000, 2000, 4000, 8000)

#: ``(name as printed, thickness in mm, surface weight in kg/m2, values per
#: band)``, every row of Table 7.6 in the order printed.
BIES_7_6_TRANSMISSION_LOSS: tuple[
    tuple[str, float, float | None, tuple[float | None, ...]], ...
] = (
    ("1.5 mm lead sheet", 1.5, 17, (22, 28, 32, 33, 32, 32, 33, 36)),
    ("3 mm lead sheet", 3, 34, (24, 30, 31, 27, 38, 44, 33, 38)),
    ("20 g aluminium sheet, stiffened", 0.9, 2.5, (8, 11, 10, 10, 18, 23, 25, 30)),
    ("6 mm steel plate", 6, 50, (None, 27, 35, 41, 39, 39, 46, None)),
    ("22 g galvanized steel sheet", 0.55, 6, (3, 8, 14, 20, 23, 26, 27, 35)),
    ("20 g galvanized steel sheet", 0.9, 7, (3, 8, 14, 20, 26, 32, 38, 45)),
    ("18 g galvanized steel sheet", 1.2, 10, (8, 13, 20, 24, 29, 33, 39, 44)),
    ("16 g galvanized steel sheet", 1.6, 13, (9, 14, 21, 27, 32, 37, 43, 42)),
    (
        "18 g fluted steel panels stiffened at edges, joints scaled",
        1.2,
        39,
        (25, 30, 20, 22, 30, 28, 31, 31),
    ),
    (
        "Corrugated asbestos sheet, stiffened and sealed",
        6,
        10,
        (20, 25, 30, 33, 33, 38, 39, 42),
    ),
    ("Chipboard sheets on wood framework", 19, 11, (14, 17, 18, 25, 30, 26, 32, 38)),
    ("Fibreboard on wood framework", 12, 4, (10, 12, 16, 20, 24, 30, 31, 36)),
    ("Plasterboard sheets on wood framework", 9, 7, (9, 15, 20, 24, 29, 32, 35, 38)),
    ("2 layers 13 mm plaster board", 26, 22, (None, 24, 29, 31, 32, 30, 35, None)),
    ("Plywood sheets on wood framework", 6, 3.5, (6, 9, 13, 16, 21, 27, 29, 33)),
    ("Plywood sheets on wood framework", 12, 7, (None, 10, 15, 17, 19, 20, 26, None)),
    ("Hardwood (mahogany) panels", 50, 25, (15, 19, 23, 25, 30, 37, 42, 46)),
    ("Woodwork slabs, unplastered", 25, 19, (0, 0, 2, 6, 6, 8, 8, 10)),
    (
        "Woodwork slabs, plastered (12 mm on each face)",
        50,
        75,
        (18, 23, 27, 30, 32, 36, 39, 43),
    ),
    ("Plywood", 6, 3.5, (None, 17, 15, 20, 24, 28, 27, None)),
    ("Plywood", 9, 5, (None, 7, 13, 19, 25, 19, 22, None)),
    ("Plywood", 18, 10, (None, 24, 22, 27, 28, 25, 27, None)),
    ("Lead vinyl curtains", 3, 7.3, (None, 22, 23, 25, 31, 35, 42, None)),
    ("Lead vinyl curtains", 2, 4.9, (None, 15, 19, 21, 28, 33, 37, None)),
    (
        "16 g steel + damping with 100 mm of glass-fibre",
        100,
        25,
        (20, 21, 27, 38, 48, 58, 67, 66),
    ),
    (
        "As above, but covered by 22 g perforated steel",
        100,
        31,
        (25, 27, 31, 41, 51, 60, 65, 66),
    ),
    (
        "As above, but 16 g steel replaced with 5 mm steel plate",
        100,
        50,
        (31, 34, 35, 44, 54, 63, 62, 68),
    ),
    (
        "1.5 mm lead between two sheets of 5 mm plywood",
        11.5,
        25,
        (19, 26, 30, 34, 38, 42, 44, 47),
    ),
    (
        "9 mm asbestos board between two sheets of 18 g steel",
        12,
        37,
        (16, 22, 27, 31, 27, 37, 44, 48),
    ),
    (
        "Compressed straw between two sheets of 3 mm hardboard",
        56,
        25,
        (15, 22, 23, 27, 27, 35, 35, 38),
    ),
    (
        "Single leaf brick, plastered on both sides",
        125,
        240,
        (30, 36, 37, 40, 46, 54, 57, 59),
    ),
    (
        "Single leaf brick, plastered on both sides",
        255,
        480,
        (34, 41, 45, 48, 56, 65, 69, 72),
    ),
    (
        "Single leaf brick, plastered on both sides",
        360,
        720,
        (36, 44, 43, 49, 57, 66, 70, 72),
    ),
    (
        "Solid breeze or clinker, plastered (12 mm both sides)",
        125,
        145,
        (20, 27, 33, 40, 50, 58, 56, 59),
    ),
    (
        "Solid breeze or clinker blocks, unplastered",
        75,
        85,
        (12, 17, 18, 20, 24, 30, 38, 41),
    ),
    (
        "Hollow cinder concrete blocks, painted (cement base paint)",
        100,
        75,
        (22, 30, 34, 40, 50, 50, 52, 53),
    ),
    (
        "Hollow cinder concrete blocks, unpainted",
        100,
        75,
        (22, 27, 32, 32, 40, 41, 45, 48),
    ),
    ("Thermalite blocks", 100, 125, (20, 27, 31, 39, 45, 53, 38, 62)),
    ("Glass bricks", 200, 510, (25, 30, 35, 40, 49, 49, 43, 45)),
    ("Plain brick", 100, 200, (None, 30, 36, 37, 37, 37, 43, None)),
    ("Aerated concrete blocks", 100, 50, (None, 34, 35, 30, 37, 45, 50, None)),
    ("Aerated concrete blocks", 150, 75, (None, 31, 35, 37, 44, 50, 55, None)),
    (
        "280 mm brick, 56 mm cavity, strip ties, outer faces plastered to thickness of 12 mm",
        300,
        380,
        (28, 34, 34, 40, 56, 73, 76, 78),
    ),
    (
        "280 mm brick, 56 mm cavity, expanded metal ties, outer faces plastered to thickness of 12 mm",
        300,
        380,
        (27, 27, 43, 55, 66, 77, 85, 85),
    ),
    (
        "50 mm x 100 mm studs, 12 mm insulating board both sides",
        125,
        19,
        (12, 16, 22, 28, 38, 50, 52, 55),
    ),
    (
        "50 mm x 100 mm studs, 9 mm plasterboard and 12 mm plaster coat both sides",
        142,
        60,
        (20, 25, 28, 34, 47, 39, 50, 56),
    ),
    ("Empty cavity, 45 mm wide", 75, 26, (None, 20, 28, 36, 41, 40, 47, None)),
    (
        "Cavity, 45 mm wide, filled with fibreglass",
        75,
        30,
        (None, 27, 39, 46, 43, 47, 52, None),
    ),
    ("Empty cavity, 86 mm wide", 117, 26, (None, 19, 30, 39, 44, 40, 43, None)),
    (
        "Cavity, 86 mm wide, filled with fibreglass",
        117,
        30,
        (None, 28, 41, 48, 49, 47, 52, None),
    ),
    (
        "Gypsum wall, 16 mm leaves, 200 mm cavity with no sound-absorbing material and no studs",
        240,
        23,
        (None, 33, 39, 50, 64, 51, 59, None),
    ),
    (
        "As above with 88 mm sound-absorbing material",
        240,
        26,
        (None, 42, 56, 68, 74, 70, 73, None),
    ),
    (
        "As above but staggered 4-inch studs",
        240,
        30,
        (None, 35, 50, 55, 62, 62, 68, None),
    ),
    (
        "Gypsum wall, 16 mm leaves, 100 mm cavity, 56 mm thick sound-absorbing material, single 4-inch studs with resilient metal channels on one side to attach the panel to the studs",
        140,
        28,
        (None, 25, 40, 48, 52, 47, 52, None),
    ),
    ("Single glass in heavy frame", 4, 10, (None, 20, 22, 28, 34, 29, 28, None)),
    ("Single glass in heavy frame", 6, 15, (17, 11, 24, 28, 32, 27, 35, 39)),
    ("Single glass in heavy frame", 8, 20, (18, 18, 25, 31, 32, 28, 36, 39)),
    ("Single glass in heavy frame", 9, 22.5, (18, 22, 26, 31, 30, 32, 39, 43)),
    ("Single glass in heavy frame", 16, 40, (20, 25, 28, 33, 30, 38, 45, 48)),
    ("Single glass in heavy frame", 25, 62.5, (25, 27, 31, 30, 33, 43, 48, 53)),
    ("Laminated glass", 13, 32, (None, 23, 31, 38, 40, 47, 52, 57)),
    ("2.44 mm panes, 7 mm cavity", 12, 15, (15, 22, 16, 20, 29, 31, 27, 30)),
    (
        "9 mm panes in separate frames, 50 mm cavity",
        62,
        34,
        (18, 25, 29, 34, 41, 45, 53, 50),
    ),
    (
        "6 mm glass panes in separate frames, 100 mm cavity",
        112,
        34,
        (20, 28, 30, 38, 45, 45, 53, 50),
    ),
    (
        "6 mm glass panes in separate frames, 188 mm cavity",
        200,
        34,
        (25, 30, 35, 41, 48, 50, 56, 56),
    ),
    (
        "6 mm glass panes in separate frames, 188 mm cavity with absorbent blanket in reveals",
        200,
        34,
        (26, 33, 39, 42, 48, 50, 57, 60),
    ),
    (
        "6 mm and 9 mm panes in separate frames, 200 mm cavity, absorbent blanket in reveals",
        215,
        42,
        (27, 36, 45, 58, 59, 55, 66, 70),
    ),
    ("3 mm plate glass, 55 mm cavity", 63, 25, (None, 13, 25, 35, 44, 49, 43, None)),
    ("6 mm plate glass, 55 mm cavity", 70, 35, (None, 27, 32, 36, 43, 38, 51, None)),
    (
        "6 mm and 5 mm glass, 100 mm cavity",
        112,
        34,
        (None, 27, 37, 45, 56, 56, 60, None),
    ),
    (
        "6 mm and 8 mm glass, 100 mm cavity",
        115,
        40,
        (None, 35, 47, 53, 55, 50, 55, None),
    ),
    (
        "Flush panel, hollow core, normal cracks as usually hung",
        43,
        9,
        (1, 12, 13, 14, 16, 18, 24, 26),
    ),
    (
        "Solid hardwood, normal cracks as usually hung",
        43,
        28,
        (13, 17, 21, 26, 29, 31, 34, 32),
    ),
    (
        "Typical proprietary 'acoustic' door, double heavy sheet steel skin, absorbent in air space, and seals in heavy steel frame",
        100,
        None,
        (37, 36, 39, 44, 49, 54, 57, 60),
    ),
    ("2-skin metal door", 35, 16, (None, 26, 26, 28, 32, 32, 40, None)),
    ("Plastic laminated flush wood door", 44, 20, (None, 14, 18, 17, 23, 18, 19, None)),
    ("Veneered surface, flush wood door", 44, 25, (None, 22, 26, 29, 26, 26, 32, None)),
    (
        "Metal door; damped skins, absorbent core, gasketing",
        100,
        94,
        (None, 43, 47, 51, 54, 52, 50, None),
    ),
    (
        "Metal door; damped skins, absorbent core, gasketing",
        180,
        140,
        (None, 46, 51, 59, 62, 65, 62, None),
    ),
    (
        "Metal door; damped skins, absorbent core, gasketing",
        250,
        181,
        (None, 48, 54, 62, 68, 66, 74, None),
    ),
    (
        "Two 16 g steel doors with 25 mm sound-absorbing material on each, and separated by 180 mm air gap",
        270,
        86,
        (None, 50, 56, 59, 67, 60, 70, None),
    ),
    ("Hardwood door", 54, 20, (None, 20, 25, 22, 27, 31, 35, None)),
    ("Hardwood door", 66, 44, (None, 24, 26, 33, 38, 41, 46, None)),
    ("T & G boards, joints scaled", 21, 13, (17, 21, 18, 22, 24, 30, 33, 63)),
    (
        "T & G boards, 12 mm plasterboard ceiling under, with 3 mm plaster skin coat",
        235,
        31,
        (15, 18, 25, 37, 39, 45, 45, 48),
    ),
    (
        "As above, with boards 'floating' on glass-wool mat",
        240,
        35,
        (20, 25, 33, 38, 45, 56, 61, 64),
    ),
    ("Concrete, reinforced", 100, 230, (32, 37, 36, 45, 52, 59, 62, 63)),
    ("Concrete, reinforced", 200, 460, (36, 42, 41, 50, 57, 60, 65, 70)),
    ("Concrete, reinforced", 300, 690, (37, 40, 45, 52, 59, 63, 67, 72)),
    (
        "126 mm reinforced concrete with 'floating' screed",
        190,
        420,
        (35, 38, 43, 48, 54, 61, 63, 67),
    ),
    ("200 mm concrete slabs", 200, 280, (None, 34, 39, 46, 53, 59, 64, 65)),
    ("As above, but oak surface", 212, 282, (None, 34, 41, 46, 55, 64, 70, None)),
    (
        "As above, but carpet + hair felt underlay, no of oak surface",
        200,
        281,
        (None, 34, 36, 46, 55, 66, 72, None),
    ),
    (
        "Gypsum ceiling, mounted resiliently, and vinyl finished wood joist floor with glass-fibre insulation and 75 mm plywood",
        318,
        None,
        (None, 30, 36, 45, 52, 47, 65, None),
    ),
)

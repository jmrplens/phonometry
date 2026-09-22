#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Four tables of damping, resilient and carpet data, read a second time.

Vigran (2008) Table 8.3, Harris (1977) Table 14.2, and Harris 3e Tables 30.2
and 30.3. Each was transcribed by two readers who never saw each other's work
and compared cell by cell before either was kept: 156 cells over the four
tables, and not one disagreement.

This is the second reading, kept as the oracle the tests check against. Every
cell is **as the page prints it**: decimal commas stay commas, a range keeps
the dash the page sets (an en dash in Vigran, a hyphen in Harris), "approx."
stays in the cell, the pile weights and heights keep their imperial half in
parentheses, and the asterisk of Table 14.2 stays on the label it marks.
"""

from __future__ import annotations

#: Vigran (2008) Table 8.3: density in kg/m3, dynamic modulus in MPa under a
#: static load of about 2 kPa.
VIGRAN_8_3: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Glass wool", ("approx. 125", "0.11–0.13")),
    ("Rock wool", ("150–175", "0.27–0.33")),
    ("Rock wool", ("110–135", "0.25–0.30")),
    ("Polystyrene foam", ("10–20", "0.30–3.0")),
    ("Polyurethane foam", ("33–72", "7–19")),
    ("Cork", ("120–250", "10–30")),
)


#: Harris (1977) Table 14.2: decay rate in db/seg at 21 degrees C, bonded
#: area in per cent, weight in kg/m2.
HARRIS_1977_14_2: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("1 pliegue común", ("1-12", "100", "1-2")),
    ("1 pliegue punzado", ("1-6", "100", "1-2")),
    ("1 pliegue muescado", ("1-11", "100", "1-2")),
    ("1 pliegue muescado *", ("21", "No", "1,5")),
    ("Lo mismo, cubierto con alfombra *", ("85", "No", "3,5")),
    ("2 pliegues, muesca+común", ("6-20", "100", "1-2")),
    ("4 pliegues, alternando muesca y común", ("20-40", "100", "3,5-5")),
    ("1 pl. muescado, cubierto con hoja de metal", ("400", "100", "5")),
)


#: Harris 3e Table 30.2: construction; pile weight kg/m2 (oz/yd2), pile
#: height mm (in), surface, fibre, NRC.
HARRIS_30_2: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Tejida", ("1,2 (35)", "4 (0,175)", "Cortado", "Lana", "0,30")),
    ("Tejida", ("1,2 (35)", "4 (0,175)", "Corte", "Lana", "0,35")),
    ("De nudo", ("1,1 (3,2)", "14 (0,56)", "Cortado", "Nylon", "0,50")),
    ("De nudo", ("1,3 (32)", "14 (0,56)", "Cortado", "Acrílica", "0,50")),
    ("De nudo", ("1,5 (43)", "13 (0,50)", "Cortado", "Madera", "0,55")),
    ("Tejida", ("1,5 (44)", "6 (0,25)", "Rizo", "Lana", "0,30")),
    ("Tejida", ("2,3 (66)", "10 (0,375)", "Rizo", "Lana", "0,40")),
    ("Tejida", ("3,1 (88)", "13 (0,50)", "Rizo", "Lana", "0,40")),
    ("De nudo", ("0,5 (15)", "6 (0,25)", "Rizo", "Lana", "0,25")),
    ("De nudo", ("1,4 (40)", "6 (0,25)", "Rizo", "Lana", "0,35")),
    ("De nudo", ("2,1 (60)", "6 (0,25)", "Rizo", "Lana", "0,30")),
)


#: Harris 3e Table 30.3: the same columns as Table 30.2, for carpets on a
#: hair pad.
HARRIS_30_3: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Tejida forrada", ("1,5 (44)", "6 (0,25)", "Cortado", "Lana", "0,40")),
    ("Tejida no forrada", ("1,5 (44)", "6 (0,25)", "Rizo", "Lana", "0,40")),
    ("De punto", ("1,4 (40)", "5-10 (0,2-0,4)", "Rizo", "Lana", "0,65")),
    ("De nudo", ("0,5 (15)", "6 (0,25)", "Rizo", "Nylon", "0,65")),
    ("De nudo", ("1,5 (43)", "6 (0,25)", "Rizo", "Acrílica", "0,50")),
    ("De nudo", ("1,4 (40)", "10 (0,39)", "Rizo", "Lana", "0,60")),
    ("De nudo", ("1,1 (32)", "14 (0,56)", "Cortado", "Nylon", "0,70")),
    ("De nudo", ("1,5 (43)", "13 (0,50)", "Cortado", "Lana", "0,70")),
)


#: Rossing (2014) Table 6.5, read twice: from the page image and from the
#: PDF's own text layer, which agree on all 24 cells. Material or structure;
#: bonding, beta_avg. The minus sign of fused silica is the page's U+2212.
ROSSING_6_5: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Zincblende", ("Covalent", "2.2")),
    ("Flourite", ("Ionic", "3.8")),
    ("FCC", ("Metallic", "5.6")),
    ("FCC (inert gas)", ("van der Waals", "6.4")),
    ("BCC", ("Metallic", "8.2")),
    ("NaCl", ("Ionic", "14.6")),
    ("Fused silica", ("Isotropic", "−3.4")),
    ("YBa2Cu3O7−δ (ceramic)", ("Isotropic", "14.3")),
)

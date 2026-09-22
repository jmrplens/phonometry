#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Harris 3e Tables 32.1 to 32.8, read a second time from the page.

The catalogue in :mod:`phonometry.building.impact_catalogue` and this module
were transcribed from the rendered pages by two readers who never saw each
other's work, and compared cell by cell before either was kept. This is the
second reading, kept as the oracle the tests check against.

Fifty-five cells differed. Thirty-eight of them were the filler text the two
readers wrote for a cell that is a section drawing and prints nothing, and
twelve were about whether a description that refers to another row counts as
printed or as inherited; neither was a disagreement about the page. The five
that were are settled in ``ADJUDICACION.md``, on the rendered page at up to
six times: two fraction glyphs whose small 8 degrades to a k in this copy, and
three decimal marks that the page sets as commas everywhere, including inside
the imperial parentheses. The adjudication went against this reading on all
five, and those five carry the adjudicated text here, because an oracle is
what the page prints and not what a reader thought it printed.

Every value is **as the page prints it**: the rating and the improvement are
dimensionless, the descriptions carry the page's own decimal commas and its
double dimensions, and an empty string is a cell the page leaves blank with no
dash and no convention for the gap.
"""

from __future__ import annotations

#: The columns of Tables 32.1 to 32.7, in printed order. The "Esquema" column
#: is left out: it is a section drawing with no textual equivalent, which is
#: not a thing a transcription can hold.
HARRIS_32_FLOOR_COLUMNS: tuple[str, ...] = (
    "Fila",
    "Descripción",
    "Clase de aislamiento del impacto (IIC)",
)

#: One entry per printed row of Tables 32.1 to 32.7: the row number the page
#: prints in its own column, the description, and the impact insulation class.
#: Two rows print no class, and their third entry is the empty string.
HARRIS_32_FLOORS: tuple[tuple[str, str, str], ...] = (
    (
        "1",
        "Losa de 10 cm (4 in) de espesor de hormigón armado con una malla AWG del número 6, de 15 por 15 cm, colocada en la línea central del plano horizontal de la losa. Todas las cavidades de la superficie están selladas con una mezcla delgada de mortero.",
        "25",
    ),
    (
        "2",
        "Igual que 1 salvo que se adhiere una baldosa de vinilo de 0,32 cm (1/8 in) de grosor al hormigón",
        "28",
    ),
    (
        "3",
        "Igual que 1 salvo que se adhiere tarima de roble de 1,27 cm (1/2 in) de grosor al hormigón",
        "45",
    ),
    (
        "4",
        "Igual que 1, pero con una alfombra de rizo de lana de 0,64 cm (1/4 in) de grosor, con un cañamazo de yute tejido de 0,32 cm (1/8 in) y un forro de espuma de caucho de 0,64 cm (1/4 in).",
        "80",
    ),
    (
        "5",
        "Igual que 1, con tarima de roble de 1,27 cm (1/2 in) de grosor, de 22,8 cm por 22,8 cm (9 por 9 in), con espuma de poliuretano semirrígida de 0,64 cm (1/4 in) de grosor de 35,2 kg/m3 (2,2 lb/ft3), sin planchas de forro.",
        "52",
    ),
    (
        "6",
        "Losa de hormigón armado de 15,2 cm (6 in) de grosor; sobre el lado del suelo, una capa de cemento y arena de 2,2 cm (7/8 in) y revestimiento compuesto de 1,59 cm (5/8 in) de grosor; sobre el lado del techo, 1,27 cm (1/2 in) de masilla.",
        "35",
    ),
    (
        "7",
        "Losa de hormigón armado de 11,1 cm (4 3/8 in) de grosor. Sobre el lado del suelo, una capa de cemento y arena de 1,9 cm (3/4 in), con un revestimiento del suelo de linóleo de 0,32 cm (1/8 in); sobre el lado del techo, una capa de masilla de 0,95 cm (3/8 in).",
        "48",
    ),
    (
        "8",
        "Hormigón armado de 12,7 cm (5 in) de grosor. Sobre el lado del suelo, una capa de lana de vidrio aglutinada con betún y cubierta con papel de construcción. Sobre el pavimento, 1,27 cm (1/2 in) de brea-masilla, con una cobertura de suelo de linóleo. Sobre el lado del techo, una capa de plástico de 1,27 cm (1/2 in).",
        "53",
    ),
    (
        "9",
        "Losa de hormigón armado de 15,2 cm (6 in) de grosor. Sobre el lado del suelo, ensambladura de madera de ranura y lengüeta de 1,9 cm (3/4 in) de grosor, clavada sobre listones de madera de 3,81 cm (1 1/2 in) por 5,1 cm (2 in), con un espaciamiento de 30,8 cm (16 in), que flotan sobre una capa de lana de vidrio de 2,54 cm (1 in) de grosor. Sobre el lado del techo, una capa de masilla de 1,27 cm (1/2 in).",
        "57",
    ),
    (
        "10",
        "Losas prefabricadas de hormigón con canales unidas con mortero sobre centros cada 50,8 cm (20 in). Cada losa tiene un canal trapezoidal de 7,6 cm (3 in) de profundidad, con bases de 27,9 cm (11 in) y 37,5 cm (14 3/4 in). En el lado del suelo, un acabado de cemento y arena de 1,9 cm (3/4 in) de grosor.",
        "32",
    ),
    (
        "11",
        "Suelo de hormigón nervado de 18,4 cm (7 1/4 in). Los nervios tienen 13,3 cm ( 5 1/4 in) por 9,5 cm (3 3/4 in), con espaciamientos de 53,2 cm (21 in) entre los centros; la losa tiene 5,1 cm (2 in) de grosor, con una capa de arena y cemento de 1,9 cm (3/4 in) de grosor. En el lado hacia el techo, listones de madera de 1,58 cm (5/8 in) de grosor, clavados sobre bandas, sujeto mediante tacos y yeso de 1,58 cm (5/8 in) de grosor.",
        "42",
    ),
    (
        "12",
        "Vigas prefabricadas de hormigón trapezoidales con canales de 17,8 cm (7 in), sobre centros separados 35,6 cm (14 in), con los espacios entre ellas rellenos con una mezcla de cemento y arena. En el lado del suelo, una capa de cemento y arena de 3,8 cm (1,5 in) de grosor, con un revestimiento de suelo de madera de 2,54 cm (1 in) de grosor. En el lado hacia el techo, una capa de escayola de 1,9 cm (3/4 in) de grosor sobre listones expandidos de metal.",
        "42",
    ),
    (
        "13",
        "Vigas prefabricadas de hormigón con canales de 12,7 cm (5 in), sobre centros separados 36,8 cm (14,5 in), con los espacios entre las vigas rellenos con una mezcla de cemento y arena. En el lado del suelo, una ensambladura de ranura y lengüeta de madera de 2,2 cm (7/8 in) de grosor, clavada sobre listones de madera de 2,5 cm (1 in) por 5 cm (2 in), 50,8 cm (20 in), sobre una lámina de lana de vidrio de 2,5 cm (1 in), sobre una capa de cemento y arena de 1,9 cm (3/4 in). En el lado del techo, un tablero de escayola de 0,32 cm (1/8 in), clavado a listones de madera de 2,5 cm (1 in) por 5 cm (2 in), con un espaciamiento de 36,8 cm (14,5 in) entre los centros. La anchura total es de 25,4 cm (10 in).",
        "53",
    ),
    (
        "14",
        "Losa armada de 15,6 cm (6 in) con bloques huecos de 30,5 cm (12 in) por 12,7 cm (5 in), con espaciamientos de 40,6 cm (16 in) entre sus centros. En el lado del suelo, una capa de cemento y arena de 3,8 cm (1,5 in), con un acabado de suelo de brea y masilla de 1,6 cm (5/8 in) de grosor sobre fieltro. En el lado del techo, 1,9 cm (3/4 in) de escayola. Espesor total de 21,6 cm (8,5 in).",
        "30",
    ),
    (
        "15",
        "Hormigón armado de 14 cm (5,5 in) de grosor con bloques embebidos de 10 cm (4 in) por 30,5 cm (12 in), con espaciamiento de 36,8 cm (14,5 in) entre sus centros. En el lado del suelo, un pavimento de cemento y arena flotante armado con tela metálica de 3,8 cm (1,5 in) de grosor sobre una placa de lana de vidrio aglutinada con betún de 2,5 cm (1 in), cubierta con papel de construcción; revestimiento del suelo de baldosas termoplásticas. Sobre el lado del techo, una capa de escayola de 1,27 cm (0,5 in). Espesor total de 21,6 cm (8,5 in).",
        "37",
    ),
    (
        "16",
        "Bloques huecos de mampostería de 10,1 cm (4 in) por 31,8 cm (12,5 in), con espaciamiento entre sus centros de 39,4 cm (15,5 in), con los espacios entre los bloques rellenos con 10,1 cm (4 in) de hormigón armado. En el lado del suelo, un pavimento de arena y cemento de 5,1 cm (2 in); suelo de madera de 2,5 cm (1 in), clavado sobre listones de madera de 5,1 cm (2 in) por 2,5 cm (1 in), con espaciamiento de 39,4 cm (15,5 in) entre sus centros, flotando sobre una plancha de lana de vidrio de 2,5 cm (1 in) de grosor. En el lado del techo, una placa de escayola de 1,9 cm (3/4 in). Espesor total de 23,5 cm (9,25 in).",
        "63",
    ),
    (
        "17",
        "Vigas trapezoidales huecas prefabricadas de 15,2 cm (6 in), espaciadas cada 36,9 cm (14,5 in), con bases de 35,6 cm (14 in) y 30,5 cm (12 in). Los espacios entre las vigas están rellenos con hormigón. En el lado del suelo, un acabado de brea y masilla de 1,27 cm (0,5 in). En el lado del techo, una capa de escayola de 1,27 cm (0,5 in). Espesor total: 19 cm (7,5 in).",
        "31",
    ),
    (
        "18",
        "Vigas de hormigón trapezoidales huecas prefabricadas de 12,7 cm (5 in), espaciadas cada 36,7 cm (14,5 in), con bases de 35,6 cm (14 in) y 31,8 cm (12,5 in). Los espacios entre las vigas están rellenos con una mezcla de arena y cemento. En el lado del suelo, una ensambladura de ranura y lengüeta de madera de 2,2 cm (7/8 in) de grosor, clavada sobre listones de madera de 3,8 cm (1,5 in) por 5,1 cm (2 in), distanciados cada 51 cm (20 in), flotando sobre una lámina de lana de vidrio de 2,5 cm (1 in); cobertura de suelo de linóleo. En el lado hacia el techo, una placa de escayola de 1,6 cm (5/8 in). El espesor total es de 22,2 cm (8,75 in).",
        "49",
    ),
    (
        "19",
        "Mismo suelo estructural que el 18. En el lado del suelo, un pavimento de arena y cemento de 2,5 cm (1 in), con revestimiento de baldosas de corcho de 0,48 cm (3/16 in). En el lado del techo, una placa de escayola de 0,95 cm (3/8 in) de grosor, conectada a listones de madera de 5 cm (2 in) por 2,5 cm (1 in), sujetos mediante abrazaderas de metal. El espesor total es de 19,4 cm (7 5/8 in).",
        "51",
    ),
    (
        "20",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), espaciadas cada 40,6 cm (16 in). En el lado del suelo, una ensambladura de ranura y lengüeta de 2,2 cm (7/8 in) clavada sobre listones; en el lado del techo, un tablero de escayola de 0,95 cm (3/8 in) clavado a las viguetas, con las juntas selladas; grosor total de 24,1 cm (9,5 in).",
        "32",
    ),
    (
        "21",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), separadas cada 40,6 cm (16 in). En el lado del suelo, contrachapado C-D de 1,27 cm (0,5 in) de grosor clavado sobre las viguetas, con distancias entre sus centros de 20,3 cm (8 in); suelo de madera de 1,98 cm (25/32 in) de grosor sobre contrachapado. En el lado del techo, un tablero de escayola de 1,27 cm (0,5 in) de grosor, clavado a las viguetas, con centros distanciados 15,2 cm (6 in), con todas las juntas selladas y acabadas; baldosas en el techo pegadas sobre el tablero de escayola. Grosor total de 26 cm (10,25 in).",
        "37",
    ),
    (
        "22",
        "Viguetas de madera de 7,6 cm (3 in) por 17,8 cm (7 in), espaciadas cada 60,1 cm (24 in). En el lado del suelo, suelo de madera de 2,54 cm (1 in) de grosor, clavado a las viguetas, con revestimiento de linóleo. En el lado del techo, una capa de junquillos y yeso de 3,5 cm (1 3/8 in). Grosor total de 24,1 cm (9,5 in).",
        "40",
    ),
    (
        "23",
        "Viguetas de madera de 5,1 cm (2 in) por 25,4 cm (10 in), cada 60,1 cm (24 in). En el lado del suelo, un tablero de 4,7 cm (1 27/32 in) de pulpa de papel de edificación comprimido homogéneo, clavado sobre puntos perpendiculares a las viguetas cada 20,3 cm (8 in), una plancha de cartón de 0,32 cm (1/8 in) pegada sobre el tablero, pegada sobre ésta una capa única de papel de fieltro de edificación y, sobre ella, baldosas de asbestos de vinilo de 0,32 cm (1/8 in) por 22,9 cm (9 in). En el lado del techo, un tablero de escayola de 1,27 cm (0,5 in) de grosor, clavado sobre puntos cada 30,5 cm (12 in), con todas las juntas selladas y acabadas. Grosor total: 31,1 cm (12,25 in).",
        "43",
    ),
    (
        "24",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), cada 40,6 cm (16 in). En el lado del suelo, una ensambladura de fibra de madera de ranura y lengüeta de 3,8 cm (1,5 in) de grosor, clavado a las viguetas, cubierto con cañamazo y alfombra. Grosor total: 25,4 cm (10 in).",
        "56",
    ),
    (
        "25",
        "Viguetas de madera de 5,1 cm (2 in) por 25,4 cm (10 in), cada 40,6 cm (16 in). En el lado del suelo, un tablero de 3,4 cm (1,32 in) de pulpa de papel de edificación comprimido homogéneo, clavado en puntos perpendiculares a las viguetas cada 20,3 cm (8 in); el tablero cubierto con una alfombra de espuma de caucho y una alfombra de nylon. La alfombra tiene un grosor no comprimido de 0,64 cm (0,25 in) de pelo de rizo, 7 rizos por pulgada, con un grosor total de 0,95 cm (3/8 in). En el lado del techo, un tablero de escayola de 1,27 cm (0,5 in), clavado sobre puntos cada 30,5 cm (12 in). Grosor total: 31,7 cm (12,5 in).",
        "57",
    ),
    (
        "26",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), cada 40,6 cm (16 in), con planchas de fibra de vidrio de 7,6 cm (3 in) de grosor grapadas entre las juntas. En el lado del suelo, subsuelo de contrachapado de 1,27 cm (0,5 in) de grosor, clavado a las viguetas cada 20,3 cm (8 in), y sobre él, solado de roble de 1,98 cm (0,78 in) de grosor. En el lado del techo, viguetas de madera de techo de 5,1 cm (2 in) por 10,2 cm (4 in), cada 61 cm (24 in), alternadas con viguetas de suelo; una plancha de yeso de 1,27 cm (0,5 in) de grosor clavada a las viguetas del techo. Las juntas de la plancha del techo selladas y acabadas. Grosor total: 32,3 cm (11,75 in).",
        "43",
    ),
    (
        "27",
        "Viguetas de madera de 5,1 cm (2 in) por 25,4 cm (10 in), cada 40,6 cm (16 in), con listones de fibra mineral de 7,6 cm (3 in) de grosor grapados entre las juntas. En el lado del suelo, subsuelo de contrachapado de 1,27 cm (0,5 in) de grosor, clavado en los bordes cada 15,2 cm (6 in) y en el centro cada 25,4 cm (10 in), capa de papel de construcción y solado de roble de 1,89 cm (0,78 in) de grosor, clavado en la intersección de las viguetas y en medio de ellas. En el lado del techo, una plancha de escayola de 1,6 cm (5/8 in) de grosor, atornillada cada 30,5 cm (12 in) a canales elásticos, colocados cada 61 cm (24 in) sobre centros perpendiculares a las viguetas. Grosor total: 31,45 cm (12,38 in).",
        "46",
    ),
    (
        "28",
        "Viguetas de madera de 5,1 cm (2 in) por 25,4 cm (10 in), cada 40,6 cm (16 in), con listones de fibra mineral de 7,6 cm (3 in) de grosor grapados entre las juntas. En el lado del suelo, subsuelo de contrachapado de 1,27 cm (0,5 in) de grosor, clavado en los bordes cada 15,2 cm (6 in) y en el centro cada 25,4 cm (10 in), capa de papel de construcción y solado de roble de 1,89 cm (0,78 in) de grosor, clavado en la intersección de las viguetas y en medio de ellas; alfombra de 1,5 kg/m2 (44 oz/yd2), con felpudo de pelo de 1,4 kg/m2 (40 oz/yd2), colocada sobre el suelo. En el lado del techo, una plancha de escayola de 1,6 cm (0,63 in) de grosor, clavada a los centros de las viguetas cada 15,2 cm (6 in); todas las juntas selladas y acabadas. Grosor total: 31,6 cm (12,5 in).",
        "58",
    ),
    (
        "29",
        "Parecido al anterior, salvo que la plancha de yeso está atornillada cada 30,4 cm (12 in) al centro de canales elásticos, colocados cada 60,8 cm (24 in) sobre puntos perpendiculares a las viguetas. Grosor total: 33 cm (13 in).",
        "70",
    ),
    (
        "30",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), cada 40,6 cm (16 in). En el lado del suelo, contrachapado burdo regular C-D de 2,86 cm (1,125 in) de grosor, clavado cada 15,2 cm (6 in) a lo largo de la periferia y cada 40,6 cm (16 in) sobre los centros de los cojinetes, cubierto con un felpudo de pelo (40 oz/yd2) y una alfombra de pelo de lana [1,5 kg/m2 (44 oz/yd2)]. El peso total de la alfombra es (4,14 lb/yd2) y el grosor total 0,95 cm (3/8 in). En el lado del techo, viguetas de madera de 5,1 cm (2 in) por 10,2 cm (4 in), sobre centros alternando cada 40,6 cm (16 in) y 20,3 cm (8 in) con respecto a las viguetas del suelo; planchas de fibra de vidrio de 7,6 cm (3 in) grapadas entre las viguetas del techo y una plancha de 1,6 cm (5/8 in) de grosor de escayola clavada sobre las viguetas del techo. Todas las juntas selladas y acabadas y toda la periferia del panel calafateada y sellada. El techo se sujeta de forma independiente a la estructura del suelo. Grosor total: 31,4 cm (12 3/8 in).",
        "",
    ),
    (
        "31",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), cada 40,6 cm (16 in). En el lado del suelo, solado de madera de ensambladura de ranura y lengüeta de 2,2 cm (7/8 in), sobre 2,5 cm (1 in) de plancha de lana de vidrio aglutinada con betún, y listones de madera de 2,5 cm (1 in) por 10,1 cm (2 in), clavados al subsuelo entre las viguetas. En el lado del techo, una capa de escayola de 1,27 cm (0,5 in) sobre un listón expandido de metal. Grosor total: 25,4 cm (10 in).",
        "46",
    ),
    (
        "32",
        "Parecido al anterior, salvo que hay una capa de arena de 5,1 cm (2 in) entre las viguetas. Grosor total: 25,4 cm (10 in).",
        "57",
    ),
    (
        "33",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), cada 40,6 cm (16 in), con planchas de fibra de vidrio de 7,6 cm (3 in) de grosor grapadas entre las juntas. En el lado del suelo, contrachapado burdo C-D de bordes cuadrados de 1,27 cm (0,5 in), clavado cada 15,2 cm (6 in) a lo largo de la periferia y cada 25,4 cm (10 in) a otros cojinetes; una plancha de fibra de caña de 1,27 cm (1/2 in) grapada cada 61 cm (24 in) al contrachapado; bandas de forro de 5,1 cm (2 in) por 7,6 cm (3 in), pegadas cada 40,6 cm (16 in) a la plancha de fibra, en paralelo y a media distancia entre las viguetas; solado de tablas de madera de 2 cm (25/32 in) de grosor. En el lado del techo, canales elásticos cada 60 cm (24 in), atornillados perpendiculares a las viguetas, un tablero de escayola de 1,59 cm (5/8 in), atornillado a los canales cada 30,5 cm (12 in). Todas las juntas selladas y acabadas y toda la periferia del panel calafateada y sellada. Grosor total: 32,4 cm (12,75 in).",
        "51",
    ),
    (
        "34A",
        "Viguetas de madera de 5,1 cm (2 in) por 20,3 cm (8 in), cada 40,6 cm (16 in), con planchas de fibra de vidrio de 7,6 cm (3 in) de grosor grapadas entre las juntas. En el lado del suelo, contrachapado de 1,27 cm (0,5 in) de grosor, clavado cada 15,2 cm (6 in) en la periferia y cada 40,6 cm (16 in) sobre estos cojinetes; una plancha de fibra de caña de 1,27 cm (1/2 in), grapada cada 60 cm (24 in) al contrachapado; bandas de forro de 5 cm (2 in) por 7,5 cm (3 in), pegadas cada 40,6 cm (16 in) a la plancha de fibra, en paralelo y a media distancia entre las viguetas; ensambladura de ranura y lengüeta de 1,6 cm (5/8 in); subsuelo de contrachapado C-D empastado, clavado cada 15,2 cm (6 in) en los bordes y cada 25,4 cm (10 in) sobre otros cojinetes; una lámina de vinilo de 0,19 cm (0,075 in) pegada al subsuelo. En el lado del techo, canales elásticos cada 60 cm (24 in), atornillados perpendiculares a las viguetas; un tablero de escayola de 1,6 cm (5/8 in), atornillado a los canales cada 30,5 cm (12 in). Todas las juntas selladas y acabadas y toda la periferia del panel calafateada y sellada. Grosor total: 32,4 cm (12,75 in).",
        "49",
    ),
    (
        "34B",
        "Parecido al anterior, salvo que la lámina de vinilo es reemplazada por un felpudo de pelo (40 oz/yd2) y una alfombra de pelo de lana (44 oz/yd2). El peso total de la alfombra es 4,14 lb/yd2 y el grosor total 0,95 cm (3/8 in). Grosor total: 34,3 cm (13,5 in).",
        "78",
    ),
    (
        "35A",
        "Viguetas de acero de 20,3 cm (8 in), cada 40,6 cm (16 in). Las viguetas tienen elementos de apoyo, en la parte superior e inferior, de 5,1 cm (2 in) de anchura, agujeros de 0,16 cm (1/16 in) de diámetro cada 76,2 cm (30 in) y un grosor de cuerpo de 0,16 cm (1/16 in). En el lado del suelo, una plancha de pulpa de papel de construcción comprimido homogéneo de 3,41 cm (1,34 in), de 410 kg/m3 (26,1 lb/ft3), clavada cada 20,3 cm (8 in) sobre centros perpendiculares a las viguetas, un tablero de cartón 0,32 cm (1/8 in) pegado a la plancha, una capa única de papel de construcción de fieltro de 15 lb pegada al cartón y baldosas de asbesto de 0,32 cm (1/8 in) pegadas sobre el fieltro. En el lado del techo, una capa de escayola de 1,27 cm (0,5 in), clavada cada 30,5 cm (12 in), con todas las juntas selladas y acabadas. Grosor total: 25,7 cm (10 1/8 in).",
        "40",
    ),
    (
        "35B",
        "Parecido al 35A, salvo que las viguetas de acero están cada 60,1 cm (24 in) y tablero de construcción es de 4,7 cm (1,84 in) de grosor. Grosor total: 27 cm (10 5/8 in).",
        "45",
    ),
    (
        "36A",
        "Las viguetas y el tablero de pulpa de papel de construcción son iguales al 35A, pero éste está cubierto con una alfombra de espuma de caucho y una alfombra de nylon. La alfombra tiene un grosor no comprimido de 0,64 cm (1/4 in), sobre un cañamazo de fibra de yute tejido. La alfombra de nylon tiene un cañamazo tejido de 0,32 cm (1/8 in) y un pelo de 0,64 cm (1/4 in), con una densidad de 2,76 rizos/cm (7 rizos/in), con un grosor total de 0,95 cm (3/8 in). En el lado del techo, una capa de yeso de 1,27 cm (0,5 in), clavada cada 30,5 cm (12 in), con todas las juntas selladas y acabadas. Grosor total: 26,7 cm (10,5 in).",
        "58",
    ),
    (
        "36B",
        "Parecido al 36A, salvo que las viguetas de acero están cada 60,1 cm (24 in) y el tablero de construcción es de 4,7 cm (1,84 in) de grosor. Grosor total: 28 cm (11 in).",
        "63",
    ),
    (
        "37A",
        "Hormigón de arena y gravilla de 6,35 cm (2,5 in) de grosor, de 2370 kg/m3 (148 lb/ft3), sobre unidades de acero ondulado de 0,38 mm (calibre 28), apoyadas mediante juntas de barras de acero de 35,6 cm (14 in); tela asfáltica de 0,32 cm (1/8 in) de grosor pegada al hormigón. En el lado del techo, canales incrustados de 1,9 cm (3/4 in) cada 34,3 cm (13,5 in), sujetos mediante cables a las viguetas; malla de diamantes y listones de metal de 1,5 kg/m2 (3,4 lb/yd2), sujeta mediante cables a los listones incrustados; capa de 1,4 cm (9/16 in) de masilla de yeso perlite, con acabado blanco de 0,16 cm (1/16 in). Grosor total: 47,1 cm (18,56 in).",
        "35",
    ),
    (
        "37B",
        "Parecido al 37A, pero la tela asfáltica es reemplazada por una alfombra y un tejido de fieltro",
        "64",
    ),
    (
        "38",
        "Viguetas de acero de 45,7 cm (18 in), cada 81,3 cm (32 in), con planchas de fibra de vidrio de 7,6 cm (3 in) de grosor entre las viguetas. En el lado del suelo, ensambladura de ranura y lengüeta de contrachapado de 2,86 cm (1 1/8 in) de grosor (graduación 2-4-1), clavada a las viguetas; el contrachapado está cubierto con un felpudo de pelo de 1,81 kg/m2 (40 oz/yd2) y una alfombra de pelo de lana de 1,99 kg/m2 (44 oz/yd2). El peso total de la alfombra es de 2,25 kg/m2 (4,14 lb/yd2) y el grosor total 0,95 cm (3/8 in). En el lado del techo, canales elásticos incrustados cada 61 cm (24 in), atornillados perpendiculares a las viguetas; un tablero de escayola de 1,6 cm (5/8 in), atornillado a los canales cada 30,5 cm (12 in). Todas las juntas selladas y acabadas y toda la periferia del panel calafateada y sellada. Grosor total: 53,3 cm (21 in).",
        "",
    ),
)

#: The columns of Table 32.8, which numbers no row.
HARRIS_32_8_COLUMNS: tuple[str, ...] = (
    "Tratamiento superficial",
    "ΔIIC",
)

#: One entry per printed row of Table 32.8.
HARRIS_32_8: tuple[tuple[str, str], ...] = (
    (
        "Alfombras de pelo de distinto tipo",
        "25 a 30",
    ),
    (
        "Linóleo de 0,25 cm (0,1 in) de grosor sobre fieltro gofrado de 1,0 kg/m2 (1,8 lb/yd2)",
        "19",
    ),
    (
        "Linóleo de corcho de 0,6 cm (0,24 in) de grosor",
        "18",
    ),
    (
        "Linóleo de corcho de 0,45 cm (0,18 in) de grosor",
        "17",
    ),
    (
        "Linóleo de 0,2 cm (0,08 in) a 0,32 cm (0,13 in) de grosor extendido sobre una plancha de corcho de 0,2 cm (0,08 in) a 0,32 cm (0,13 in) de grosor",
        "17",
    ),
    (
        "«Sandwich» de linóleo y corcho de 0,4 cm (0,16 in) de grosor",
        "16",
    ),
)

#: Which of the seven tables each numbered row is printed in. The numbering
#: runs straight through them, so this is the only thing that says where one
#: table ends and the next begins.
HARRIS_32_TABLE_OF_ROW: tuple[tuple[str, str], ...] = (
    ("1", "TABLA 32.1"),
    ("2", "TABLA 32.1"),
    ("3", "TABLA 32.1"),
    ("4", "TABLA 32.1"),
    ("5", "TABLA 32.1"),
    ("6", "TABLA 32.1"),
    ("7", "TABLA 32.1"),
    ("8", "TABLA 32.1"),
    ("9", "TABLA 32.1"),
    ("10", "TABLA 32.2"),
    ("11", "TABLA 32.2"),
    ("12", "TABLA 32.2"),
    ("13", "TABLA 32.2"),
    ("14", "TABLA 32.3"),
    ("15", "TABLA 32.3"),
    ("16", "TABLA 32.3"),
    ("17", "TABLA 32.3"),
    ("18", "TABLA 32.3"),
    ("19", "TABLA 32.3"),
    ("20", "TABLA 32.4"),
    ("21", "TABLA 32.4"),
    ("22", "TABLA 32.4"),
    ("23", "TABLA 32.4"),
    ("24", "TABLA 32.4"),
    ("25", "TABLA 32.4"),
    ("26", "TABLA 32.5"),
    ("27", "TABLA 32.5"),
    ("28", "TABLA 32.5"),
    ("29", "TABLA 32.5"),
    ("30", "TABLA 32.5"),
    ("31", "TABLA 32.6"),
    ("32", "TABLA 32.6"),
    ("33", "TABLA 32.6"),
    ("34A", "TABLA 32.6"),
    ("34B", "TABLA 32.6"),
    ("35A", "TABLA 32.7"),
    ("35B", "TABLA 32.7"),
    ("36A", "TABLA 32.7"),
    ("36B", "TABLA 32.7"),
    ("37A", "TABLA 32.7"),
    ("37B", "TABLA 32.7"),
    ("38", "TABLA 32.7"),
)

#: The twelve rows whose printed description refers to another row instead of
#: repeating the structural floor, and the row each one points at.
HARRIS_32_REFERS_TO: tuple[tuple[str, str], ...] = (
    ("2", "1"),
    ("3", "1"),
    ("4", "1"),
    ("5", "1"),
    ("19", "18"),
    ("29", "28"),
    ("32", "31"),
    ("34B", "34A"),
    ("35B", "35A"),
    ("36A", "35A"),
    ("36B", "36A"),
    ("37B", "37A"),
)

#: The three mass densities the prose buries: the row, the material the page
#: gives the density for, and the value as printed.
HARRIS_32_DENSITIES: tuple[tuple[str, str, str], ...] = (
    ("5", "espuma de poliuretano semirrígida", "35,2 kg/m3"),
    (
        "35A",
        "plancha de pulpa de papel de construcción comprimido homogéneo",
        "410 kg/m3",
    ),
    ("37A", "hormigón de arena y gravilla", "2370 kg/m3"),
)

#: Every pair of these eight tables whose two halves are not each other at the
#: precision they are printed to, read off the page one by one: the row the
#: page numbers, and the pair exactly as it is set. Three hundred and twenty
#: pairs were converted and compared; these nineteen are the ones that fail,
#: and they are one entry of ``docs/ERRATA.md``.
#:
#: The test is one-directional wherever the imperial half is a whole number or
#: a fraction, because on these pages the imperial half is the measurement and
#: the SI half its translation, and two-directional wherever the imperial half
#: is itself printed as a rounded decimal. That is what keeps row 17 off this
#: list: it prints "36,9 cm (14,5 in)" where 14,5 in is 36,83 cm, and 36,9 cm
#: is 14,53 in, which the page would print as the 14,5 in beside it. It is also
#: what keeps the page's coarse roundings off it, "60 cm (24 in)" and "2,5 cm
#: (1 in)" among them: a truncation is still the number.
HARRIS_32_MISPRINTED_PAIRS: tuple[tuple[str, str], ...] = (
    ("9", "30,8 cm (16 in)"),
    ("11", "53,2 cm (21 in)"),
    ("14", "15,6 cm (6 in)"),
    ("18", "36,7 cm (14,5 in)"),
    ("22", "60,1 cm (24 in)"),
    ("23", "60,1 cm (24 in)"),
    ("26", "32,3 cm (11,75 in)"),
    ("27", "1,89 cm (0,78 in)"),
    ("28", "1,89 cm (0,78 in)"),
    ("28", "31,6 cm (12,5 in)"),
    ("29", "60,8 cm (24 in)"),
    ("31", "10,1 cm (2 in)"),
    ("34A", "7,5 cm (3 in)"),
    ("35A", "410 kg/m3 (26,1 lb/ft3)"),
    ("35B", "60,1 cm (24 in)"),
    ("36B", "60,1 cm (24 in)"),
    ("37A", "1,5 kg/m2 (3,4 lb/yd2)"),
    ("38", "1,81 kg/m2 (40 oz/yd2)"),
    ("38", "1,99 kg/m2 (44 oz/yd2)"),
)

#: The rows whose "Esquema" cell holds a section drawing. The four rows that
#: only refer to another one carry none, and Table 32.8 has no such column.
HARRIS_32_DRAWINGS: tuple[str, ...] = (
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34A",
    "35A",
    "36A",
    "37A",
    "38",
)

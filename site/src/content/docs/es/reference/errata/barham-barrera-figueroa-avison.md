---
title: "Erratas de Barham, Barrera-Figueroa & Avison (2014)"
description: "Erratas de Barham, Barrera-Figueroa & Avison (2014): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre Barham, Barrera-Figueroa & Avison (2014). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Barham, Barrera-Figueroa & Avison (2014), Metrologia 51, 129, fórmulas (1), (2) y (4) (un modelo que no da su propia tabla 2)

- **Ubicación:** apartado 3.4 «Dissimilarity in reference and test
  microphones», fórmulas (1) a (5), tabla 1 y tabla 2 (p. 135 impresa). El
  artículo es la referencia [1] de IEC 61094-5:2016 6.5, que remite a él los
  micrófonos de distinto diámetro, y el origen de las correcciones de su tabla
  A.1. Fuente no normativa: un artículo de revista.
- **El impreso:** la fórmula (1),
  $u(r) = \sum D_n J_0(k_n r)\,\mathrm{e}^{\mathrm{i}\omega t}$, con «$k_n$ the
  roots of $J_1(k_n) = 0$»; la fórmula (2),
  $D_n = \frac{2}{a^2 J_0^2(k_n)} \int_b^a J_0(k_n r/a)\,r\,\mathrm{d}r$; la
  fórmula (4), $S(r) = J_0(j_{01}\varpi r/a)/J_0(j_{01}\varpi)$. La tabla 1
  recoge «WS3 microphone overall radius 2.975 mm» y «WS3 microphone diaphragm
  radius (b) 2.065 mm», y ninguna fórmula usa el primero. La tabla 2 imprime,
  «calculated with input data from table 1», -0.004 dB a 1000 Hz, -0.235 dB a
  8000 Hz y -1.443 dB a 20 000 Hz, la columna que IEC 61094-5:2016 adopta como
  tabla A.1.
- **El problema:** evaluado tal como se imprime, con $b$ = 2.065 mm en (2) y en
  (5), el modelo da -0.003 dB, -0.190 dB y -0.986 dB a esas frecuencias a
  344.8 m/s, y ninguna velocidad del sonido da la tabla: a 291.7 m/s sus dos
  extremos redondean a los -0.004 dB y -1.443 dB impresos, pero entonces
  8000 Hz se desvía 0.033 dB y 16 000 Hz 0.091 dB, y el mejor compromiso,
  unos 296.5 m/s, aún falla una fila por 0.054 dB. Dos lecturas
  juntas dan todas las filas de la tabla 2 con su redondeo impreso, y ninguna
  de las dos sola lo hace: la sensibilidad radial de (4) es la deflexión de una
  membrana bajo una presión uniforme,
  $J_0(j_{01}\varpi r/a)/J_0(j_{01}\varpi) - 1$, que es máxima en el centro,
  como dice IEC 61094-5 6.5 que es la sensibilidad de un micrófono, mientras
  que (4) tal como se imprime tiende a una sensibilidad uniforme a baja
  frecuencia; y el límite inferior de (2), el borde interior de la corona por
  la que el sonido entra en el hueco, es el radio exterior, 2.975 mm, mientras
  que el promedio de (5) sobre el micrófono en ensayo recorre el radio de su
  membrana, $b$. La fórmula (1) escribe además $J_0(k_n r)$ donde (2) y (3)
  escriben $J_0(k_n r/a)$: siendo $k_n$ un número puro, el argumento de (1)
  tiene dimensión de longitud. El artículo no imprime ninguna velocidad del
  sonido; a 344.8 m/s las dos lecturas reproducen las catorce filas a la
  milésima de decibelio, y a los 345.9 m/s del aire del apartado 4 de
  IEC 61094-5, con menos de 0.01 dB de diferencia.
- **Evidencia:** el modelo recalculado tal como se imprime y con las dos
  lecturas, frente a la tabla 2. Verificado en la página 8 del PDF (p. 135
  impresa) de Metrologia 51 (2014) 129-138, doi:10.1088/0026-1394/51/3/129, la
  descarga de IOPscience cuya primera página es una portada.
- **Comportamiento de la biblioteca:** `metrology.diameter_sound_field_correction`
  calcula el modelo con las dos lecturas, con $k_n r/a$ en (1); las filas de
  conformidad sobre IEC 61094-5 6.5 reproducen la tabla A.1 a partir de los
  datos de la tabla 1
  ([`tests/metrology/test_comparison_diameter_gap_validation.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_comparison_diameter_gap_validation.py)).
- **Estado:** sin notificar (artículo de revista, no una norma).

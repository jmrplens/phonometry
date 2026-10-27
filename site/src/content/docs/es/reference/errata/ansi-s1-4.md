---
title: "Erratas de ANSI S1.4"
description: "Erratas de ANSI S1.4: 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre ANSI S1.4-1983. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## ANSI S1.4-1983, Table V, celda de 20 Hz tipo 2 (un signo más que perdió su barra)

- **Ubicación:** apartado 5.2, Table V «Tolerance limits on relative response
  levels for sound at random incidence measured on an instrument's
  calibration range», fila de 20 Hz, columna de tipo 2 (p. 6 impresa).
- **El impreso:** la celda lee «**+ 3**», sin segundo término. Sus vecinas de
  columna a 10, 12.5 y 16 Hz leen «+ 5, − ∞», y las celdas de tipo 0 y tipo 1
  de su propia fila leen «± 2» y «± 2.5».
- **El problema:** la tabla tiene una sola notación para un límite solo
  superior, un par «+ n, − ∞», y se usa tres filas por encima de esta celda
  en la misma columna. Esta celda no usa ni esa notación ni el «± n» de su
  fila, así que es o un límite escrito en una forma que la tabla no usa en
  ningún otro sitio o un «±» cuya barra no llegó a imprimirse. La Table V de
  IEC 651:1979, de la que esta tabla es la contraparte estadounidense y con
  la que la columna de tipo 2 concuerda en las otras treinta y tres filas,
  imprime «**±3**» exactamente en esta celda. La lectura pretendida es
  ±3 dB.
- **Evidencia:** la celda y sus vecinas de columna, leídas en la página 16
  del PDF (p. 6 impresa) de ANSI S1.4-1983, contra la misma celda en la
  página 10 del PDF (p. 8 impresa, marcada «[IEC page 19]») de BS 5969:1981,
  la adopción británica idéntica de IEC 651:1979.
- **Comportamiento de la biblioteca:** `_ANSI_S14_TABLE5_12` en
  [`weighting_compliance.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/weighting_compliance.py)
  y su gemela de `reference_data` llevan −3 dB como límite inferior de tipo 2
  a 20 Hz, la más estricta de las dos lecturas, con la nota al lado.
  `test_b_masks_match_reference_data` fija las dos transcripciones una contra
  otra. Ningún veredicto distribuido se mueve: la ponderación B realizada
  queda 0,05 dB por debajo de la nominal a 20 Hz y pasa cualquiera de las dos
  lecturas.
- **Estado:** sin notificar.

---
title: "Erratas de Jarvis (1996)"
description: "Erratas de Jarvis (1996): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre Jarvis (1996). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Jarvis (1996), NPL Report CIRA(EXT) 010, apéndice B (la unidad imaginaria de la masa del primer micrófono, perdida en el escaneo publicado)

- **Ubicación:** apéndice B «Uncertainties caused by differences in acoustic
  impedance between the test and reference microphones» (folio 25 impreso),
  las impedancias acústicas de los dos micrófonos del ejemplo. El informe es la
  referencia [2] de IEC 61094-5:2016, que le remite el aire entre dos
  micrófonos en la tabla D.1 y en 7.4. Fuente no normativa: un informe de
  laboratorio.
- **El impreso:** los parámetros figuran como $r_1$, «$c$ = 48·10^-15» y $m_1$
  para el LS2P, y $r_2$, $c_2$ y $m_2$ para el WS2P de alta sensibilidad; las
  impedancias dicen
  $Z_{m1}(w) = r_1 + w\cdot\ m + \frac{1}{\mathrm{i}\cdot w\cdot c_1}$ y
  $Z_{m2}(w)\ \ r_2 + w\cdot\mathrm{i}\cdot m_2 + \frac{1}{\mathrm{i}\cdot w\cdot c_2}$.
- **El problema:** el término de masa del primer micrófono no muestra ni la
  unidad imaginaria del segundo ni su subíndice, y su compliancia figura como
  $c$ frente al $c_1$ que usa la fórmula. Leído literalmente, $w\,m_1$ es una
  resistencia, no la reactancia de una masa, y el circuito da entonces 0.117°
  y 0.0273 dB a 20 kHz, donde las dos gráficas impresas en el folio 27
  terminan en unos 0.09° y 0.025 dB;
  $r_1 + \mathrm{i}\,w\,m_1 + 1/(\mathrm{i}\,w\,c_1)$ da allí 0.089° y
  0.0255 dB, y el mínimo de unos -0.0065 dB cerca de 7 kHz y el máximo de fase
  de unos 0.16° cerca de 12.5 kHz que muestran las gráficas. Lo más probable
  es que los glifos se perdieran en la reproducción y no que el autor los
  omitiera: el folio es una hoja de cálculo cuyas gráficas salen de las
  expresiones que muestra, y hay un hueco en blanco justo donde van «i·» y el
  subíndice «1», como lo hay donde el mismo folio pierde otros glifos finos,
  el «:=» tras $Z_{m2}(w)$, $\kappa$ y $p_0$ y el subíndice de $c_1$ en su
  definición.
- **Evidencia:** las dos impedancias tal como las muestra el escaneo, el hueco
  en blanco en lugar de los glifos que faltan, y el circuito del mismo
  apéndice recalculado con cada lectura frente a las gráficas impresas, con la
  fase a 20 kHz como lo que mejor separa las dos. Verificado en las páginas 28
  y 30 del PDF (pp. 25 y 27 impresas) del NPL Report CIRA(EXT) 010 (1996), el
  escaneo que publica el National Physical Laboratory.
- **Comportamiento de la biblioteca:** `metrology.air_gap_series_impedance_pa_s_m3`
  se comprueba frente al cociente que imprime el apéndice B, con
  $\mathrm{i}\,w\,m_1$, y frente a los extremos de las gráficas y sus valores a
  20 kHz (las filas de conformidad sobre Jarvis 1996,
  [`tests/metrology/test_comparison_diameter_gap_validation.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_comparison_diameter_gap_validation.py)).
- **Estado:** sin notificar (informe de laboratorio, no una norma, y un
  defecto del escaneo publicado).

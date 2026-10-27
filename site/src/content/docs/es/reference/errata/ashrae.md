---
title: "Erratas de ASHRAE (2019)"
description: "Erratas de ASHRAE (2019): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre ASHRAE (2019). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## ASHRAE (2019) HVAC Applications Handbook, capítulo 49, folio 49.31 (la frase que presenta las tablas de break-in intercambia dos de ellas)

- **Ubicación:** capítulo 49, "Noise and Vibration Control", el párrafo impreso
  bajo la ecuación (24) en la página impresa 49.31 (página 915 del PDF), y los
  títulos de las tablas 32 y 33 impresos en esa misma página. Fuente no
  normativa: un manual de diseño.
- **El impreso:** el párrafo dice "Values for TL_in for rectangular ducts are
  given in Table 32, for round ducts in Table 33, and for flat oval ducts in
  Table 34 (Cummings 1983, 1985)." Las dos tablas que nombra primero se titulan,
  en esa misma página, "Table 32 Experimentally Measured TL_in Versus Frequency
  for Circular Ducts" y "Table 33 TL_in Versus Frequency for Rectangular Ducts".
- **El problema:** las dos primeras tablas están nombradas al revés. La tabla 32
  es la circular y la 33 la rectangular, y la frase dice lo contrario; la
  tercera, la de conducto oval, sí está bien. Lo que imprimen las tablas lo
  resuelve en contra de la frase y no en contra de los títulos. La tabla 32 está
  indexada por un diámetro y una longitud, que es lo que tiene un conducto
  redondo y lo que el capítulo no da a ningún rectangular, y lleva las marcas de
  una tabla medida, una cota inferior y un valor entre paréntesis, bajo la nota
  que las explica; la tabla 33 está indexada por un tamaño de conducto de dos
  lados en milímetros e imprime columna de 8 kHz, cosa que en este capítulo sólo
  hacen las dos tablas rectangulares. La frase equivalente para el breakout, en
  el folio 49.29, empareja esas mismas tres formas con las tablas 29, 30 y 31 en
  el orden rectangular, redondo, oval, y allí los tres títulos impresos
  concuerdan con ella. Sólo esta frase está mal.
- **Evidencia:** verificado en la página 915 del PDF (página impresa 49.31) de
  ASHRAE (2019), *2019 ASHRAE handbook: Heating, ventilating, and
  air-conditioning applications* (ed. SI), capítulo 49, y contra el párrafo de
  breakout de la página 913 del PDF (página impresa 49.29) del mismo capítulo.
  Dos lectores transcribieron la página por separado y ambos leyeron la frase y
  los dos títulos tal como se citan aquí.
- **Qué hace la biblioteca:** nada, y nada hace falta: la referencia cruzada es
  una etiqueta que la biblioteca no lee nunca. Todas las filas de las tablas 32,
  33 y 34 en
  [`PUBLISHED_DUCT_TRANSMISSION_LOSS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/duct_walls.py)
  están archivadas bajo la tabla de cuyo título impreso se leyeron, y `shape`
  lleva la palabra que usa ese título. Esa frase es el único crédito que el
  capítulo da a esas tres tablas, así que todas sus filas la citan literalmente
  en `attributed_to["table"]` y dejan dicho ahí que sus dos primeras tablas
  están al revés.
- **Estado:** sin comunicar.

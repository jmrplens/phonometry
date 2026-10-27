---
title: "Erratas del Real Decreto 1367/2007"
description: "Erratas del Real Decreto 1367/2007: 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre el Real Decreto 1367/2007. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Real Decreto 1367/2007, Anexo IV A.3.3 (tablas de umbrales de Kf y Ki)

- **Ubicación:** Anexo IV, sección A.3.3, las tablas de corrección $K_f$
  (baja frecuencia) y $K_i$ (impulsiva), fila central de cada una.
- **El impreso:** ambas tablas imprimen la fila de 3 dB como «Si 10 > Lf <=
  15» y «Si 10 > Li <= 15» respectivamente (BOE-A-2007-18397, texto
  consolidado).
- **El problema:** la condición tal como está impresa es insatisfacible. Lee
  «10 mayor que Lf» y «Lf como mucho 15» a la vez, lo que seleccionaría
  niveles por debajo de 10 dB, pero la fila de arriba ya asigna esos a 0 dB
  («Si Lf <= 10») y la fila de abajo cubre «Si Lf > 15». Las tres filas solo
  particionan el rango bajo la lectura $10 < L_f \le 15$, así que el «>» es
  una inversión tipográfica de «<».
- **Evidencia:** las filas que la encierran no dejan otra lectura
  consistente; la construcción idéntica aparece en ambas tablas, y las tablas
  equivalentes de los reglamentos de ruido autonómicos que transponen este
  Anexo imprimen `10 < Lf <= 15`. Verificado en la página 26 del PDF (p. 26
  impresa) de Real Decreto 1367/2007, texto consolidado BOE-A-2007-18397, en
  la que el «>» de ambas filas centrales es inequívoco contra los glifos
  «<=» de la misma celda.
- **Comportamiento de la biblioteca:**
  [`low_frequency_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/spain.py)
  e `impulsive_correction` implementan $10 < L \le 15$, con un test de
  regresión fijando las tres ramas en los límites de 10 dB y 15 dB.
- **Estado:** sin notificar (reglamento nacional, no un organismo de
  normalización).

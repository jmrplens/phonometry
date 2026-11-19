---
title: "Erratas del Real Decreto 1367/2007"
description: "Erratas del Real Decreto 1367/2007: 2 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
corrects:
  - "std-rd-1367-2007-boe-a-2007-18397-texto-consolidado"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 2 entradas del [registro de erratas](/es/reference/errata/) sobre el Real Decreto 1367/2007, en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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

## Real Decreto 1367/2007, artículo 30.1 y 30.2 (la orden de metrología atribuida al Ministerio de Fomento)

- **Ubicación:** artículo 30 «Instrumentos de medida», apartados 1 y 2.
- **El impreso:** «Los instrumentos de medida y calibradores utilizados para
  la evaluación del ruido deberán cumplir las disposiciones establecidas en
  la Orden del Ministerio de Fomento, de 25 de septiembre de 2007, por la que
  se regula el control metrológico del Estado de los instrumentos destinados
  a la medición de sonido audible y de los calibradores acústicos»; el
  apartado 2 remite a «la Orden del Ministerio de Fomento, de 25 de
  septiembre de 2007».
- **El problema:** la orden de esa fecha y ese título la dictó otro
  ministerio. Es la Orden ITC/2845/2007, de 25 de septiembre
  (BOE-A-2007-17278), que el Boletín Oficial del Estado publica bajo el
  epígrafe «Ministerio de Industria, Turismo y Comercio» y que firma el
  ministro de ese departamento. El Ministerio de Fomento había dictado la
  orden a la que sustituyó: la disposición derogatoria única de la Orden
  ITC/2845/2007 deroga «la Orden de 16 de diciembre de 1998, del Ministerio
  de Fomento», sobre el control metrológico de los sonómetros. Quien busque
  una orden del Ministerio de Fomento de 25 de septiembre de 2007 no la
  encuentra. La Orden ITC/2845/2007 quedó derogada, con efectos desde el 24
  de octubre de 2020, por la Orden ICT/155/2020, de 7 de febrero
  (BOE-A-2020-2573), y el texto consolidado del artículo 30 sigue diciendo lo
  citado.
- **Evidencia:** una comparación del artículo con la orden, cada uno leído en
  su página: el artículo 30 en la página 16 del PDF (p. 16 impresa) del Real
  Decreto 1367/2007, texto consolidado BOE-A-2007-18397; el epígrafe y el
  título en la página 1 del PDF (p. 40035 impresa), la disposición
  derogatoria única en la página 3 del PDF (p. 40037 impresa) y la firma en
  la página 4 (p. 40038 impresa), de la Orden ITC/2845/2007, BOE núm. 237
  de 3 de octubre de 2007. La derogación por la Orden ICT/155/2020 es la que
  el Boletín Oficial del Estado anota en BOE-A-2007-17278.
- **Comportamiento de la biblioteca:** no hizo falta ningún cambio: la
  biblioteca no calcula ningún requisito de instrumentos a partir del
  artículo 30. La guía de la normativa española de ruido nombra la orden por
  su número y su ministerio, dice que está derogada y recoge los dos
  documentos UNE-EN 61260 del artículo 30.3.
- **Estado:** sin notificar (reglamento nacional, no un organismo de
  normalización).

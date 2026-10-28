---
title: "Erratas de NMFS (2024)"
description: "Erratas de NMFS (2024): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre NMFS (2024). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## NMFS (2024) Updated Technical Guidance v3.0, Tabla 5 / Tabla ES2 (C de los otáridos)

*Documento de guía regulatoria, no una norma.*

- **Ubicación:** Tabla 5 (p. 25 impresa), repetida como Tabla ES2 (p. 3
  impresa) y de nuevo como Tabla 8 (p. 35 impresa): el parámetro de
  ponderación auditiva $C$ del grupo de pinnípedos otáridos en el agua
  (OW / OCW).
- **El impreso:** $C = 1.37\ \text{dB}$.
- **El problema:** el valor correcto es 1.36 dB. El propio NMFS lo declara en
  la nota de la tabla: «During the public comment period, an error was
  identified with the Navy's rounding, where this value should be 1.36,
  instead of 1.37. Because this is such a minor error and to remain
  consistent with the Navy, NMFS decided rely upon the value the Navy
  originally provided.» El documento publica por tanto el dígito equivocado a
  sabiendas.
- **Evidencia:** recálculo independiente de $C$ desde su propia definición,
  el pico negado de $W(f)$, con los parámetros de la misma fila $a = 1.58$,
  $b = 5$, $f_1 = 2.53\ \text{kHz}$, $f_2 = 43.8\ \text{kHz}$:
  $C = 1.3643\ \text{dB}$, que redondea a 1.36. El umbral TTS ponderado
  publicado de la misma fila ($179\ \text{dB} = K + C$ con $K = 178$) no se
  ve afectado por el tercer dígito. El mismo recálculo reproduce todas las
  demás filas de la tabla a los dos decimales impresos, así que la fila OW es
  la única que no redondea desde sus propios parámetros. Verificado en la
  página 36 del PDF (p. 25 impresa), la página 14 del PDF (p. 3 impresa) y la
  página 46 del PDF (p. 35 impresa) de NMFS Updated Technical Guidance
  v3.0:2024, las tres llevando 1.37 con la nota idéntica.
- **Comportamiento de la biblioteca:**
  [`bioacoustics/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/bioacoustics/weighting.py)
  implementa 1.36 y mantiene el 1.37 impreso disponible como
  `WeightingParameters.c_db_as_printed`, para que una evaluación que deba
  reproducir la tabla publicada al pie de la letra aún pueda. Fijado por
  `test_nmfs_2024_otariid_c_uses_the_corrected_1_36`.
- **Estado:** sin notificar (el organismo emisor ya lo tiene documentado).

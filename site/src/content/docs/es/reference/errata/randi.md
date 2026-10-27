---
title: "Erratas de RANDI 3.1 Physics Description"
description: "Erratas de RANDI 3.1 Physics Description: 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre RANDI 3.1 Physics Description. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## RANDI 3.1 Physics Description (NRL, Breeding et al.), Tabla 2

- **Ubicación:** Tabla 2 (niveles de fuente de buques representativos).
- **El impreso:** dos celdas se desvían de las propias Ecs. (2) a (5) del
  informe evaluadas con las longitudes y velocidades medias de la Tabla 1: el
  valor de Merchant a 25 Hz (unos 3 dB alto) y el de Tanker a 300 Hz (en
  torno a 1 dB bajo). La fila de Fishing Vessel no es reproducible desde las
  medias de la Tabla 1 en absoluto (un desplazamiento constante de unos
  3.8 dB sugiere entradas supuestas distintas).
- **El problema:** el informe no declara las entradas exactas usadas para la
  Tabla 2, y dos celdas contradicen sus propias ecuaciones mientras que todas
  las celdas de Large Tanker y Super Tanker concuerdan a 0.06 dB.
- **Evidencia:** recálculo de las 25 celdas desde las Ecs. (2) a (5).
- **Comportamiento de la biblioteca:** el test de regresión fija las filas
  reproducibles y excluye las celdas contradictorias con la justificación en
  el test.
- **Estado:** sin notificar (informe técnico, no una norma).

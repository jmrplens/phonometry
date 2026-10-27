---
title: "Erratas de ITU-R BS.468"
description: "Erratas de ITU-R BS.468: 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre ITU-R BS.468-4. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## ITU-R BS.468-4, Table 2, límite superior de 5 ms (la celda en dB debería leer −6.7)

- **Ubicación:** apartado 2.1, Table 2, «Limiting values — upper limit», la
  columna de 5 ms (p. 4 impresa). El mismo par de celdas está impreso
  idéntico en la Table AII de IEC 60268-1:1985 y en la tabla de la Amendment
  1:1988 que la sustituye, así que el defecto se hereda del texto del CCIR y
  no lo introduce ninguna de las dos ediciones.
- **El impreso:** `46` en la fila (%) y `−6.6` en la fila (dB).
- **El problema:** las dos discrepan. 46 % es 20 lg(0.46) = **−6.745 dB**, y
  −6.6 dB es 46.8 %. Se auditaron las 33 celdas de las Tables 2 y 3 contra su
  propia contraparte; 32 concuerdan dentro de 0.050 dB, el redondeo de un
  porcentaje de dos cifras significativas, y esta se va 0.145 dB. El límite
  *inferior* vecino de 5 ms (`34`, `−9.3`) se va 0.070 dB y es benigno,
  porque 34 % como porcentaje redondeado de dos cifras cubre de 33.5 % a
  34.5 %, es decir de −9.500 dB a −9.241 dB, y −9.3 cae dentro. La celda
  superior no es benigna: 46 % cubre de 45.5 % a 46.5 %, es decir de
  −6.840 dB a −6.651 dB, lo que excluye −6.6.
- **Qué celda está mal:** la de dB. Leída en porcentajes, la ventana de
  aceptación es un −1.4 dB / +1.2 dB muy estable en torno a la lectura de
  referencia para todas las duraciones de 5 ms a 200 ms (+1.18 a +1.24 dB por
  arriba, −1.37 a −1.45 dB por abajo). 46 % sitúa el límite superior de 5 ms
  +1.214 dB por encima de su referencia, sobre ese patrón; 46.774 %, que es
  lo que significa −6.6 dB, lo situaría +1.360 dB por encima, fuera de él.
  Así que 46 % está bien y la celda en dB debería leer **−6.7**.
- **Evidencia:** 20 lg de cada porcentaje impreso comparado con la celda en
  dB impresa a su lado, para las 24 celdas de la Table 2 y las 9 de la Table
  3, y los desplazamientos de los límites superior e inferior en torno a la
  fila de referencia recalculados en las cinco duraciones de 5 ms a 200 ms.
  Verificado en la página 4 del PDF (p. 4 impresa) de la Recomendación ITU-R
  BS.468-4, en la página 33 del PDF (p. 31 impresa) de IEC 60268-1:1985, y en
  la página 3 del PDF (p. 3 impresa) de la Amendment 1:1988 de
  IEC 60268-1:1985.
- **Comportamiento de la biblioteca:** las filas de porcentajes son primarias
  y las filas en dB se derivan de ellas, que es la decisión que esta entrada
  fuerza. Las once ventanas de aceptación se almacenan como porcentajes en
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data) y se comprueban como
  porcentajes, en la suite de tests y en las filas de conformidad «ITU-R
  BS.468-4 Table 2» y «ITU-R BS.468-4 Table 3».
- **Estado:** sin notificar.

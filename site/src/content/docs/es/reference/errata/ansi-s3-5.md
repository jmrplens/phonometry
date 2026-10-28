---
title: "Erratas de ANSI S3.5"
description: "Erratas de ANSI S3.5: 2 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 2 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre ANSI S3.5-1997, en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## ANSI S3.5-1997, ejemplos resueltos del Anexo C (erratas oficiales del WG S3-79)

> **Sin verificar contra la página.** ANSI S3.5-1997 no está en la biblioteca
> local (se tiene la viñeta del paquete de R `SII`, no la norma), así que lo
> que esta entrada llama «el impreso» es la descripción del propio grupo de
> trabajo, no una página que este proyecto haya leído. Los recálculos de
> abajo son independientes y sí se reproducen, pero los *caracteres impresos*
> descansan solo en la lista de erratas. La norma está en la lista de
> adquisiciones pendientes del mantenedor; cuando llegue una copia, la
> entrada debe re-verificarse contra el impreso de las pp. 21-22 impresas y
> retirarse este aviso.

- **Ubicación:** Anexo C, Tabla C.1 (ejemplo resuelto en bandas de octava,
  p. 21) y Tabla C.2 (ejemplo resuelto en tercios de octava, p. 22) de la
  impresión de 1997.
- **El impreso (según las erratas del grupo de trabajo):** (a) Tabla C.1,
  fila $i = 5$, el factor de distorsión por nivel $L_i$ bajo el Step 6 está
  impreso como $0.10$; (b) Tabla C.2, primera fila, la pendiente de
  autoenmascaramiento del habla $C_i$ está impresa como $-45.59$.
- **El problema:** ambas celdas contradicen las propias fórmulas normativas
  de la norma. (a) El apartado 5.7 con las entradas del ejemplo
  ($E'_5 = 20\ \text{dB}$, $U_5 = 9.33\ \text{dB}$) da
  $L_5 = 1 - (20 - 9.33 - 10)/160 = 0.9958$, que a dos decimales se imprime
  $1.00$, no $0.10$. (b) El apartado 5.4 con las entradas del ejemplo
  ($B_1 = 40\ \text{dB}$, $f_1 = 160\ \text{Hz}$) da
  $C_1 = -80 + 0.6 (40 + 10\log_{10} 160 - 6.353) = -46.587$, que se imprime
  $-46.59$, no $-45.59$; la columna $Z_i$ del ejemplo solo es consistente con
  la pendiente corregida ($Z_2$ recalcula a $34.658$ = impreso 34.66 dB,
  mientras que la pendiente con la errata daría 34.76 dB). El ejemplo de la
  Tabla C.1 es el procedimiento de bandas de octava y el de la Tabla C.2 el
  de tercios de octava, así que hay una celda afectada de cada uno.
- **Evidencia:** la lista oficial de erratas publicada por el grupo de
  trabajo S3-79 de la ASA, el comité que mantiene ANSI S3.5, en su sitio de
  soporte (sii.to): «Page 21, Table C1, row i=5, column Li under Step 6: the
  value printed as 0.10 should be changed to 1.00» y «Page 22, Table C2, the
  first row of numbers, value −45.59 should be −46.59»; más el recálculo
  independiente de ambas celdas desde los apartados normativos (arriba). La
  misma lista lleva cinco correcciones más (la grafía de una referencia, la
  redacción de los pies de las Tablas 1-4 registrada en la entrada siguiente,
  la ganancia de inserción $G_i$ que falta en la Ec. 23, y dos arreglos del
  Anexo B, una referencia cruzada «B16» que debería leer «B15» y un cambio de
  redacción sobre la aproximación audiovisual); ninguna de ellas toca una
  fórmula que esta biblioteca implemente. La fuente es la lista de erratas
  del WG S3-79 en sii.to/html/errata.html (capturada el 2026-07-30,
  re-comprobada en vivo el 2026-08-04). No es la página impresa y no puede
  sustituirla, que es por lo que esta entrada lleva el aviso de arriba.
- **Comportamiento de la biblioteca:** no le afecta; la biblioteca calcula
  los valores corregidos desde los apartados normativos y siempre lo hizo.
  Sus anclas del Anexo C.2
  ([`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data),
  `ANSIS3_5_ANNEX_C1*` y `ANSIS3_5_ANNEX_C2*`) fijan la cadena consistente
  con las erratas de ambos ejemplos, contrastada a doble precisión con la
  propia implementación de referencia del grupo de trabajo `SII.C` y sus
  resultados de casos de prueba publicados. La celda de la Tabla C.1 está
  fijada directamente: el factor de distorsión por nivel del apartado 5.7
  para la fila $i = 5$ del ejemplo de bandas de octava del Anexo C.1 calcula
  a $0.99581$, que se imprime como el $1.00$ corregido.
- **Estado:** correcciones publicadas por el grupo de trabajo emisor; nada
  que notificar aguas arriba.

## ANSI S3.5-1997, pies de las Tablas 1 a 4 (errata oficial del WG S3-79)

> **Sin verificar contra la página.** Como en la entrada anterior,
> ANSI S3.5-1997 no está en la biblioteca local, así que la redacción de los
> cuatro pies se toma de la lista de erratas del grupo de trabajo y no de una
> página que este proyecto haya leído. El argumento de que las tablas no
> llevan columna de umbral es independiente y sí se sostiene contra las
> constantes transcritas. Re-verificar contra el impreso de las pp. 3-5
> impresas cuando se adquiera la norma.

- **Ubicación:** los pies de las Tablas 1, 2, 3 y 4 (pp. 3-5 de la impresión
  de 1997), las tablas de constantes de los cuatro procedimientos por bandas:
  banda crítica (21 bandas), banda crítica de contribución igual (17 bandas),
  tercio de octava (18 bandas) y octava (6 bandas).
- **El impreso (según las erratas del grupo de trabajo):** cada pie lista las
  cantidades que la tabla tabula e incluye la locución «hearing threshold
  levels,».
- **El problema:** ninguna de las cuatro tablas tabula un nivel de umbral de
  audición. Cada una lleva la frecuencia central de banda (y, para las Tablas
  1, 2 y 4, los límites de banda), la función de importancia de banda $I_i$,
  el nivel espectral estándar del habla $U_i$ por esfuerzo vocal y el nivel
  espectral de ruido interno de referencia $X_i$. El nivel de umbral de
  audición $T'_i$ es una *entrada del usuario* del procedimiento (apartado
  5.5, donde el nivel espectral de ruido interno equivalente es
  $X'_i = X_i + T'_i$), que es exactamente la cantidad que el pie invita al
  lector a buscar en la tabla y a confundir con $X_i$.
- **Evidencia:** la lista oficial de erratas publicada por el grupo de
  trabajo S3-79 de la ASA, el comité que mantiene ANSI S3.5, en su sitio de
  soporte (sii.to): «Pages 3-5, Tables 1-4: In each of the **figure**
  captions the phrase 'hearing threshold levels,' should be deleted» (la
  lista de erratas del WG S3-79 en sii.to/html/errata.html, capturada el
  2026-07-30, re-comprobada en vivo el 2026-08-04; una revisión anterior de
  esta entrada omitía la palabra «figure» de la cita); más las propias
  tablas, que no tienen tal columna.
- **Comportamiento de la biblioteca:** no le afecta. Las cuatro tablas están
  implementadas con las columnas que de verdad llevan, expuestas por
  procedimiento por `sii_procedure()` como `band_importance`,
  `speech_spectrum` ($U_i$) e `internal_noise` ($X_i$), y el umbral de
  audición sigue siendo el argumento `threshold=` de
  `speech_intelligibility_index`
  ([`src/phonometry/speech/sii.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/speech/sii.py)).
- **Estado:** corrección publicada por el grupo de trabajo emisor; nada que
  notificar aguas arriba.

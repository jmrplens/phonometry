---
title: "Erratas de las fuentes publicadas"
description: "Defectos encontrados en las normas, los documentos de guía y los libros de los que parte la biblioteca: erratas de imprenta, ejemplos resueltos que contradicen su propio articulado y qué hace la biblioteca con cada uno."
---

Implementar una norma en sala limpia significa volver a deducir cada fórmula,
constante y ejemplo resuelto a partir del documento fuente y no del código de
otra persona. Hecho sobre cientos de documentos, ese proceso encuentra
defectos en las propias fuentes: un ejemplo resuelto que contradice su
articulado, una constante a la que la composición tipográfica le comió un
dígito, una referencia cruzada que apunta a la ecuación equivocada.

Esta página es el registro de esos hallazgos. Cada entrada nombra la edición
impresa y el punto exacto, cita lo que dice el documento, muestra por qué no
puede ser correcto, aporta la evidencia independiente y declara qué lectura
implementa la biblioteca y qué test de regresión la fija. Un defecto listado
aquí nunca es un defecto del *método*: en todos los casos la lectura
pretendida se ha podido establecer a partir del propio documento o de la
física.

Léela junto al
[informe de conformidad](/phonometry/es/reference/conformance/), que muestra
los números que calcula la biblioteca; esta página explica el puñado de sitios
donde lo que está mal es el valor esperado impreso.

:::note
Esta página reproduce la edición española del registro, traducida entrada a
entrada. La redacción autoritativa es la inglesa, que es la que se ha
comunicado o se comunicará a los organismos emisores; las citas textuales, las
matemáticas y los valores impresos se reproducen sin traducir, tal como los
imprime cada fuente.
:::

El registro vive en
[`docs/ERRATA.md`](https://github.com/jmrplens/phonometry/blob/main/docs/ERRATA.md)
con su edición española en
[`docs/ERRATA.es.md`](https://github.com/jmrplens/phonometry/blob/main/docs/ERRATA.es.md),
y esta última se trasplanta aquí en tiempo de compilación con
`make site-reports`, que además exige que las dos ediciones lleven las mismas
entradas en el mismo orden, así que ninguna pareja puede discrepar.

<!-- BEGIN GENERATED BODY - transplanted from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never the text below. -->

Durante la implementación en sala limpia de esta biblioteca, cada fórmula,
constante y ejemplo resuelto se vuelve a deducir y a recalcular de forma
independiente a partir de los documentos fuente. Ese proceso saca a la luz, de
cuando en cuando, defectos de las propias fuentes: erratas de imprenta,
ejemplos resueltos que contradicen su propio texto normativo y redacciones
ambiguas. Este fichero registra cada caso confirmado con la evidencia, lo que
hace la biblioteca al respecto y si se ha notificado.

El registro cubre todos los tipos de fuente publicada de los que parte la
biblioteca: normas (ISO, IEC, EN), documentos de guía e informes técnicos
(EASA, ECAC, NRL), libros y artículos de revista. Las fuentes no normativas
quedan marcadas como tales en su entrada.

Las entradas describen las ediciones impresas concretas que se citan. Un
defecto listado aquí no es un defecto del método; en todos los casos la
lectura pretendida se ha podido establecer a partir del propio documento o de
la física, y la biblioteca implementa esa lectura. Cuando la lectura cambia
algún número que la biblioteca da, la entrada nombra la comprobación o el test
que lo fija; cuando el defecto es una etiqueta, una referencia cruzada o una
tabla que la biblioteca nunca lee, la entrada deja constancia de que no hizo
falta ningún cambio.

Leyenda de estados: **sin notificar** (registrado solo aquí) / **notificado**
(comunicado al organismo emisor, con fecha y referencia).

Una afirmación que dependa de los caracteres exactos de una fórmula,
constante, coeficiente, símbolo, desigualdad o celda de tabla se verifica
contra **la página tal como está impresa**, y su punto de Evidencia cita esa
página por índice de página del PDF y folio impreso. El texto extraído puede
localizar una página; nunca se cita como «el impreso», porque las capas de
texto de los PDF borran glifos en silencio (la mayoría de las fuentes citadas
aquí no emiten ningún `√`, así que `f_T/√2` se extrae como `f_T/2`). El
desplazamiento de páginas de cada documento se establece empíricamente, porque
difiere entre documentos y deriva entre capítulos de un mismo libro. Las
entradas que descansan en otra cosa, un recálculo o la comparación de dos
frases, lo dicen en un aviso inicial o figuran en la lista de excepciones de
[`scripts/check_errata_evidence.py`](https://github.com/jmrplens/phonometry/blob/main/scripts/check_errata_evidence.py),
que es la comprobación que hace cumplir la regla; véase
[CONTRIBUTING.md](https://github.com/jmrplens/phonometry/blob/main/CONTRIBUTING.md#6-filing-an-errata-entry).

Esta edición española traduce la prosa del registro entrada a entrada. La
redacción autoritativa es la inglesa de [ERRATA.md](https://github.com/jmrplens/phonometry/blob/main/docs/ERRATA.md), que es la que
se ha comunicado o se comunicará a los organismos emisores; las citas
textuales, las matemáticas y los valores impresos se reproducen aquí sin
traducir, tal como los imprime cada fuente. `make site-reports` mantiene las
dos ediciones con las mismas entradas y en el mismo orden.


---

## ISO 717-2:2020, Anexo C, ejemplo C.1 (C_I del suelo desnudo)

- **Ubicación:** Anexo C, Tabla C.1 (p. 17 impresa) y el cálculo de $C_I$
  impreso en la misma celda.
- **El impreso:** $L_{n,\text{sum}} = 83{,}523\,8\ldots = 84\ \text{dB}$ y
  $C_I = 84 - 15 - 79 = -10\ \text{dB}$ para el ejemplo del suelo desnudo.
- **El problema:** dos defectos independientes en la misma celda. (a) El
  apartado A.2.1 define $C_I$ desde la suma energética de 100 Hz a 2500 Hz
  (las quince primeras bandas de tercio de octava); el valor impreso solo se
  reproduce si se incluye la banda de 3150 Hz, en contradicción con A.2.1. La
  suma correcta de 100 Hz a 2500 Hz es 83,2613 dB, redondeada 83, lo que da
  $C_I = -11$. (b) Incluso leída como la suma de dieciséis bandas, los dígitos
  impresos están mal en la última cifra: la columna $L_n$ del suelo desnudo
  suma 83,523 4 dB, no los 83,523 **8** dB impresos. El defecto queda
  confinado a esa celda, porque la columna con revestimiento de la misma tabla
  imprime $L_{n,\text{sum}} = 76{,}059\,3\ldots$ y se recalcula a
  76,059 29 dB, reproduciendo todos los dígitos impresos. Ni (a) ni (b)
  cambian los 84 dB redondeados, así que solo (a) mueve $C_I$.
- **Evidencia:** recálculo independiente de ambas sumas a partir de los
  niveles por banda impresos (16 bandas 83,523 38 dB, 15 bandas 83,261 27 dB,
  con revestimiento 16 bandas 76,059 29 dB); la edición de 2013 del mismo
  ejemplo imprime $C_I = -11$. Verificado en la página 23 del PDF (p. 17
  impresa) y la página 17 del PDF (p. 11 impresa) de ISO 717-2:2020, y en la
  página 22 del PDF (p. 14 impresa) de ISO 717-2:2013.
- **Comportamiento de la biblioteca:** implementa A.2.1 tal como está escrito
  y fija $C_I = -11$ con el impreso de 2013 como oráculo
  ([`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data), comprobación de
  conformidad «ISO 717-2 Annex C, Table C.1»).
- **Estado:** sin notificar.

## ISO 717-2:2020, Anexo C, ejemplo C.2 (suelo revestido: valor de 800 Hz y cadena del CI)

- **Ubicación:** Anexo C, Tabla C.2 (p. 18 impresa), el ejemplo resuelto de
  $\Delta L_w$ / $\Delta L_\text{lin}$.
- **El impreso:** (a) el valor del suelo de referencia a 800 Hz está impreso
  como 71,0 dB; (b) la línea del $C_I$ imprime
  $L_{n,\text{sum}} = 75{,}252\,7\ldots = 75\ \text{dB}$ y
  $C_I = 75 - 15 - 63 = -3\ \text{dB}$, que alimenta
  $\Delta L_\text{lin} = 78 - 11 - (63 - 3) = 7\ \text{dB}$.
- **El problema:** dos defectos independientes. (a) El suelo de referencia de
  la Tabla 4 normativa vale 71,5 dB a 800 Hz, y la propia columna es una rampa
  limpia de +0,5 dB por tercio de octava desde 67,0 dB a 100 Hz hasta 72,0 dB
  a 1000 Hz, que los 71,0 dB impresos rompen repitiendo la celda de 630 Hz. La
  errata se propaga por su propia fila y hasta el total de la tabla, tres
  celdas más que la tabla imprime y que una revisión anterior de esta entrada
  no nombraba: la celda $L_{n,r,0} - \Delta L$ a 800 Hz está impresa como
  64,0 dB ($= 71{,}0 - 7{,}0$) donde 71,5 da 64,5; la desviación desfavorable
  está impresa como 3,0 dB ($= 64{,}0 - 61$) donde la celda corregida da 3,5;
  y el `Sum 27,9` impreso es la suma de las trece desviaciones desfavorables
  incluyendo ese 3,0, donde la cadena corregida da 28,4. Nada de eso mueve la
  valoración: 28,4 dB sigue por debajo del criterio de desplazamiento de
  32,0 dB, así que $L_{n,w,r} = 63\ \text{dB}$ y
  $\Delta L_w = 15\ \text{dB}$ en cualquier caso. (b) Los 75,2527 dB impresos
  son exactamente la suma energética de la *columna equivocada sobre el rango
  equivocado*: el suelo medido «with covering» sobre las dieciséis bandas
  de 100 Hz a 3150 Hz. A.2.1 define $C_I$ desde el suelo de referencia con
  revestimiento (la columna $L_{n,r,0} - \Delta L$) de 100 Hz a 2500 Hz (15
  bandas), lo que da 75,674 dB (cadena impresa) o 75,710 dB (celda de 800 Hz
  corregida), ambos redondean a 76 dB, así que
  $C_{I,r} = 76 - 15 - 63 = -2$ en cualquier caso, dando
  $C_{I,\Delta} = -11 - (-2) = -9$ y $\Delta L_\text{lin} = 6\ \text{dB}$, no
  la cadena impresa de −3 / −8 / 7 dB.
- **Evidencia:** recálculo independiente de todas las sumas candidatas y de
  todas las celdas de la fila de 800 Hz a partir de los valores por banda
  impresos; el 75,2527 impreso se reproduce con todos sus dígitos solo como la
  suma de 16 bandas de la columna con revestimiento, y todas las demás celdas
  de las columnas $L_{n,r,0} - \Delta L$ y de desviación se reproducen
  exactamente desde el suelo de referencia impreso, así que la fila de 800 Hz
  es la única que no. Verificado en la página 24 del PDF (p. 18 impresa) y la
  página 13 del PDF (p. 7 impresa) de ISO 717-2:2020.
- **Comportamiento de la biblioteca:** deriva el suelo de referencia revestido
  desde los valores normativos de la Tabla 4 y suma según A.2.1, fijando
  $\Delta L_w = 15\ \text{dB}$ y $C_{I,\Delta} = -9$; la comprobación de
  conformidad anota la procedencia explícitamente.
- **Estado:** sin notificar.

## ISO 717-1:2020, Anexo E, Figuras E.3 y E.2 (curvas de referencia dibujadas fuera de la Tabla E.1)

- **Ubicación:** Anexo E, Figura E.3 «Reference curve for standard wall with
  medium critical frequency» (p. 24 impresa), frente a la columna del muro
  ligero de la Tabla E.1 (pp. 24 y 25 impresas). El mismo dibujo es la
  Figura B.3 de ISO 10140-5:2010+A1:2014 (p. 15 impresa), frente a la misma
  columna de su Tabla B.1 (p. 16 impresa).
- **El impreso:** la NOTA de E.1 dice que las Figuras E.1, E.2 y E.3 «as well
  as Table E.1 give typical smoothed values» de las curvas de referencia. La
  Tabla E.1 imprime el muro ligero como 21,3, 23,3 y 25,3 dB a 50, 63 y 80 Hz,
  una meseta de 27,0 dB de 100 Hz a 500 Hz, y luego 28,0 dB a 630 Hz subiendo
  hasta 44,6 dB a 3 150 Hz y 49,4 dB a 5 000 Hz.
- **El problema:** la Figura E.3 no dibuja esa curva. Leída contra su propia
  cuadrícula en los centros de banda, su meseta está en 25,9 dB, 1,1 dB por
  debajo de la tabla, y su rama ascendente va un tercio de octava a la
  izquierda de la de la tabla: la figura marca 30,5 dB a 630 Hz, 35,3 dB a
  1 000 Hz y 42,5 dB a 2 000 Hz, donde la tabla imprime 30,5, 35,1 y 42,3 dB
  una banda más arriba, a 800, 1 250 y 2 500 Hz, y 28,0, 32,8 y 40,0 dB a
  630, 1 000 y 2 000 Hz. La línea se detiene cerca de 2,2 kHz, así que la
  figura no tiene curva para los 2 500 Hz a 5 000 Hz de la tabla. Solo el
  arranque de 50 Hz a 80 Hz coincide con la tabla. El dibujo viene sin
  cambios de ISO 10140-5, cuya edición de 2021 retiró la figura y la tabla en
  favor de ISO 717-1. La Figura E.2, redibujada para la edición de 2020,
  también se aparta de su columna, menos: su codo está cerca de 230 Hz en vez
  de 250 Hz, así que su rama ascendente va hasta 1,2 dB por encima de la tabla
  de 315 Hz a 630 Hz (45,6 dB a 400 Hz donde la tabla imprime 44,4 dB),
  mientras que la Figura B.2 de ISO 10140-5:2010+A1:2014 sigue la misma
  columna con menos de 0,3 dB de diferencia. La Figura E.1 sigue su columna
  con menos de 0,3 dB de diferencia.
- **Evidencia:** la línea de cada figura leída en cada centro de banda de la
  tabla que ilustra; la Figura E.3 da 25,9 dB a 125, 160, 250 y 315 Hz,
  28,0 dB a 500 Hz, 30,5 dB a 630 Hz, 35,3 dB a 1 000 Hz, 37,7 dB a
  1 250 Hz y 42,5 dB a 2 000 Hz, y ninguna línea a 2 500 Hz ni por
  encima; la Figura E.2 da 40,7, 42,8, 45,6, 48,0 y 50,4 dB a 250, 315, 400,
  500 y 630 Hz frente a los 40,0, 41,8, 44,4, 46,8 y 49,3 dB impresos.
  Verificado en las páginas 28 a 31 del PDF (pp. 22 a 25 impresas) de
  ISO 717-1:2020, y en las páginas 22 a 24 del PDF (pp. 14 a 16 impresas) de
  ISO 10140-5:2010+A1:2014.
- **Comportamiento de la biblioteca:** publica la tabla, no las figuras.
  `building.LINING_REFERENCE_ELEMENTS` guarda los 21 valores de cada columna
  de la Tabla E.1, comprobados banda a banda frente a una transcripción de la
  página (comprobación de conformidad «ISO 717-1:2020 Annex E, Table E.1», los
  63 valores por banda), y reproducen todas las magnitudes globales impresas
  bajo cada columna, enteras y con un decimal. No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO 10140-1:2021, Anexo H, Figura H.4 (un CI,r,50-2500 que el suelo de referencia no puede dar)

- **Ubicación:** Anexo H, Figura H.4 «Example of form for expression of
  results» (p. 31 impresa), la línea de valoración bajo el diagrama. El
  formulario de ISO 10140-1:2010+A2:2014, Figura H.4 (p. 27 impresa), lleva
  el mismo término.
- **El impreso:** «Rating in accordance with ISO 717-2: $\Delta L_w$ = dB;
  $C_{I\Delta}$ = dB; $C_{I,r,50\text{–}2\,500}$ = dB». El formulario de 2010
  imprime «$C_{I,r}$ = dB; $C_{I,r,50\text{-}2\,500}$ = dB» en la misma
  línea.
- **El problema:** $C_{I,r}$ es el término de adaptación espectral del suelo de
  referencia con el revestimiento (ISO 717-2:2020 A.2.2), obtenido de
  $L_{n,r} = L_{n,r,0} - \Delta L$ (Fórmula (1)). La Tabla 4 de
  ISO 717-2:2020 define $L_{n,r,0}$ solo de 100 Hz a 3 150 Hz, y el rango
  ampliado de la NOTA de A.2.1 necesita además 50, 63 y 80 Hz, así que no
  existe $L_{n,r}$ en esas tres bandas y ninguno de los dos documentos define
  $C_{I,r,50\text{–}2\,500}$. La propia tabla del formulario pide $\Delta L$
  desde 50 Hz, las tres bandas donde harían falta los valores de referencia.
  H.5 i), que el formulario ilustra, pide $L_{n,r,w}$ y $C_{I,r}$ o
  $L_{n,0,w}$ y $C_{I,0}$, que la Tabla 4 sí puede dar.
- **Evidencia:** la línea de valoración del formulario frente a A.2.1, A.2.2 y
  la Tabla 4 de ISO 717-2:2020, y frente a H.5 h) e i) del mismo anexo.
  Verificado en las páginas 35 y 37 del PDF (pp. 29 y 31 impresas) de
  ISO 10140-1:2021, en las páginas 13, 17 y 18 del PDF (pp. 7, 11 y 12
  impresas) de ISO 717-2:2020, y en la página 36 del PDF (p. 27 impresa) de
  BS EN ISO 10140-1:2010+A2:2014.
- **Comportamiento de la biblioteca:** `building.lab_floor_covering_improvement`
  da las dos valoraciones que pide H.5 i) y ningún
  $C_{I,r,50\text{–}2\,500}$; el término de rango ampliado del suelo desnudo
  medido, que sí está definido, sale de
  `building.weighted_impact_rating_extended`. El formulario mismo lo imprime
  `LabFloorCoveringImprovementResult.report()`, que pone esas dos valoraciones
  junto a $\Delta L_w$ y $C_{I\Delta}$ y escribe, donde iría
  $C_{I,r,50\text{–}2\,500}$, que no se forma porque la Tabla 4 empieza en
  100 Hz. Ningún número de la biblioteca depende del formulario, y no hizo
  falta ningún cambio.
- **Estado:** sin notificar.

## ISO 10140-1:2021, Anexo J, Figura J.7 («weighing curve» por «weighting curve»)

- **Ubicación:** Anexo J, J.5.1, Figura J.7 «Sample form for expression of
  results» (página 50 del PDF, p. 44 impresa), la clave junto a las dos
  últimas filas de la cabecera del formulario.
- **El impreso:** «................ frequency range of weighing curve» sobre
  «__________ test curve».
- **El problema:** «weighing» (pesada) por «weighting» (ponderación). La línea
  de puntos marca el intervalo de frecuencias de la curva de referencia que
  desplaza la valoración de ISO 717-1, la curva de ponderación; una «curva de
  pesada» no es un término de ninguno de los dos documentos. El formulario de
  BS EN ISO 10140-1:2010+A2:2014, Figura J.7, imprime «frequency range of
  weighting curve» en el mismo sitio, así que la letra se perdió en la edición
  de 2021.
- **Evidencia:** verificado en la página 50 del PDF (p. 44 impresa) de
  ISO 10140-1:2021 frente a la página 49 del PDF (p. 40 impresa) de
  BS EN ISO 10140-1:2010+A2:2014.
- **Comportamiento de la biblioteca:** nada que hacer; ningún número depende
  de ello. El formulario que imprime `LabJointInsulationResult.report()`
  rotula la curva «curva de referencia desplazada (ISO 717-1)» y la dibuja
  solo sobre el intervalo de la valoración.
- **Estado:** sin notificar (tipográfico, sin consecuencia numérica).

## ISO 10140-1:2021, Anexo J, Figura J.8 (el intervalo de trabajo dibujado como Δb y explicado como Δbn)

- **Ubicación:** Anexo J, J.5.1, Figura J.8 (página 52 del PDF, p. 46
  impresa), la cota bajo el eje de abscisas y la última línea de la clave. La
  Figura J.8 de BS EN ISO 10140-1:2010+A2:2014 (página 50 del PDF, p. 41
  impresa) imprime la misma pareja.
- **El impreso:** la flecha entre $b_\mathrm{n}$ y $b_\mathrm{n} + 3$ lleva
  la etiqueta «$\Delta b$»; la clave dice «$\Delta b_\mathrm{n}$ working range,
  3 mm».
- **El problema:** una misma magnitud con dos símbolos, y el símbolo que
  explica la clave no es el que está dibujado. El texto que presenta la figura
  solo la nombra con palabras, «indicating the working range of 3 mm» (J.5.1,
  página 51 del PDF, p. 45 impresa), así que nada más en el anexo decide entre
  los dos.
- **Evidencia:** verificado en la página 52 del PDF (p. 46 impresa) de
  ISO 10140-1:2021, el dibujo frente a su clave, con el texto de J.5.1 en la
  página 51 del PDF (p. 45 impresa); y en la página 50 del PDF (p. 41 impresa)
  de BS EN ISO 10140-1:2010+A2:2014.
- **Comportamiento de la biblioteca:** `JointGapSeries.working_range_mm`
  devuelve los dos extremos, $(b_\mathrm{n}, b_\mathrm{n} + 3)$, y su gráfico
  rotula el intervalo sombreado «intervalo de trabajo $\Delta b$ = 3 mm», el
  símbolo del dibujo. Ningún número depende del símbolo, y no hizo falta
  ningún cambio.
- **Estado:** sin notificar (tipográfico, sin consecuencia numérica).

## ISO 2631-5:2018, ejemplos resueltos del Anexo C (fórmula masculina desplegada, R femenino)

- **Ubicación:** Anexo C: el ejemplo resuelto masculino desplegado (varón de
  82 kg, $m_z = 0{,}029\ \text{MPa}/(\text{m/s}^2)$, p. 19 impresa) y la
  NOTA 5 (mujer de 64 kg, $m_z = 0{,}025\ \text{MPa}/(\text{m/s}^2)$, p. 20
  impresa).
- **El impreso:** (a) el ejemplo masculino se despliega como

  $$
  R = \left\{ \sum_{i=0}^{20-1}
  \left[ \frac{1{,}62\ \text{MPa}\,(120)^{1/6}}
  {6{,}75\ \text{MPa} - 0{,}052\ \text{MPa}\,(20+i)} \right]^{6}
  \right\}^{1/6} \approx 1{,}22
  $$

  y (b) la NOTA 5 declara $R = 0{,}97$ para el caso femenino.
- **El problema:** dos defectos independientes. (a) La fórmula masculina
  desplegada omite el término $-S_{\text{stat},i}$ que la Fórmula (C.3)
  normativa pone en el denominador, y que el propio anexo fija en
  $S_\text{stat} = 0{,}029 \cdot 9{,}81 = 0{,}281\ \text{MPa}$ en la frase que
  sigue a la lista de definiciones de la Fórmula (C.3). Evaluada exactamente
  como está desplegada, la suma da $R = 1{,}1497$, que se imprime 1,15, no el
  1,22 impreso; restaurar el término que falta da 1,2168 con el
  $S_\text{stat} = 0{,}281\ \text{MPa}$ impreso y 1,2177 con el exacto
  $m_z \cdot 9{,}81 = 0{,}2845\ \text{MPa}$, es decir, el 1,22 impreso en
  cualquiera de los dos casos. El *resultado* impreso es por tanto correcto y
  la *fórmula* impresa no. (b) El recálculo exacto de la Fórmula (C.3) con los
  propios datos de la NOTA 5 ($m_z = 0{,}025$, coeficiente de edad 0,039,
  $b = 20$, $n = 20$, $N = 120$) da $R = 0{,}9621$, que redondea a 0,96; el
  mismo código reproduce el ejemplo masculino exactamente, y el
  $S_d = 1{,}40\ \text{MPa}$ de la nota coincide con el exacto 1,3992, así que
  la discrepancia queda confinada al último dígito del $R$ femenino impreso.
- **Evidencia:** recálculo término a término de la suma de C.3 bajo ambas
  lecturas del denominador, con el ejemplo masculino como discriminador: el
  1,22 impreso solo es alcanzable con $-S_\text{stat}$, y el 1,15 solo sin él.
  Verificado en las páginas 23 (p. 17 impresa), 24 (p. 18 impresa), 25 (p. 19
  impresa) y 26 (p. 20 impresa) del PDF de ISO 2631-5:2018.
- **Comportamiento de la biblioteca:** implementa la Fórmula (C.3) tal como
  está escrita, con $-S_\text{stat}$; el ancla masculina fija 1,22 y el ancla
  de test femenina conserva el 0,97 impreso con una tolerancia que documenta
  el 0,9621 recalculado.
- **Estado:** sin notificar.

## Ainslie (2010), la Ec. (4.6) frente a su propio folio 177, y el exponente de la Ec. (4.13)

- **Ubicación:** *Principles of Sonar Performance Modelling* (Springer 2010),
  Ec. (4.6) en el folio impreso 127; la densidad del agua de mar citada en el
  apartado 4.4 del folio impreso 177; Ec. (4.13) del folio impreso 135.
- **Lo impreso:** la Ec. (4.6) da la densidad del agua de mar como
  $\hat\rho = 1027 + 4{,}3\times10^{-7}\hat P_\mathrm{w} + 0{,}75[S-35] -
  0{,}16[\hat T-10] - 0{,}004[\hat T-10]^2$, atribuida a Pierce (1989,
  p. 34), con las unidades fijadas por las Ecs. (4.7) a (4.10) del folio 128:
  presión en pascales, temperatura en grados Celsius, densidad en kg/m³. La
  Ec. (4.4) del folio 127 define esa presión como
  $P_\mathrm{w}(z) = P_\mathrm{atm} + \int_0^z \rho g\,\mathrm{d}\zeta$,
  y la Ec. (4.11) del folio 128 la evalúa en $98\,066{,}5 \times 1{,}04 =
  101\,989{,}16$ Pa en superficie. El folio 177 enuncia después, para los
  cocientes que escalan las correlaciones de sedimento de Bachman, «*standard
  conditions involving atmospheric pressure, a temperature of 23 °C, and
  salinity 35*» con $\rho_\mathrm{w} = 1024{,}2$ kg/m³.
- **El problema:** dos defectos de distinta naturaleza.

  (a) El 1024,2 del folio 177 no se sigue de la Ec. (4.6) leída con la
  Ec. (4.4). A 23 °C, salinidad 35 y una atmósfera, la ecuación da 1024,287 9,
  que imprime 1024,3. El 1024,2 impreso es lo que da la ecuación con su término
  de presión a cero, es decir, leyendo $P_\mathrm{w}$ como presión manométrica
  contra la definición que enuncia el mismo capítulo. La diferencia son
  0,043 9 kg/m³, o 4,3 partes por cien mil.

  (b) La Ec. (4.13), que despeja la (4.6) para estimar la salinidad a partir de
  una densidad medida, imprime el coeficiente de presión como
  $4{,}3\times10^{-5}$ donde la (4.6) tiene $4{,}3\times10^{-7}$. Dos órdenes
  de magnitud, y no es otra magnitud reformulada: es el mismo coeficiente en el
  mismo papel. Arrastrado a 23 °C da 1028,63 kg/m³ frente a 1024,29, un error
  del 0,42 %.
- **Evidencia:** la Ec. (4.6) evaluada en las condiciones enunciadas con la
  presión de la Ec. (4.11), contra el valor que imprime el folio 177; y los dos
  exponentes impresos comparados directamente. Verificado en las páginas 157,
  158, 165 y 207 (pp. 127, 128, 135 y 177 impresas) del PDF de la edición
  Springer de 2010.
- **Comportamiento de la biblioteca:** implementa la Ec. (4.6) con la presión
  absoluta que define su propia Ec. (4.4), porque una definición impresa manda
  sobre la cita redondeada de un valor derivado tres capítulos más allá. La
  discrepancia queda por debajo de toda tolerancia de esta biblioteca, así que
  nada depende de la elección; lo que sí dependía era de elegir bando en
  silencio. La Ec. (4.13) no se implementa
  ([`tests/fluids/test_water.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_water.py),
  comprobaciones de conformidad «Sea water (Ainslie 2010)»).
- **Estado:** sin comunicar.

## ISO 9053-2:2020, Anexo A.3 (dos propiedades del aire atribuidas a un documento que no las imprime)

- **Ubicación:** Anexo A.3, folio impreso 13 (página 17 del PDF) para los cuatro
  primeros valores y folio impreso 14 (página 18 del PDF) para el quinto.
- **Lo impreso:** «The following physical properties for air, valid at 23 °C,
  101,325 kPa and 50 % RH, are used for the calculation (values from
  IEC 61094-2:2009):», y a continuación $c_0 = 345{,}9$ m/s, $\rho_0 = 1{,}186$
  kg/m³, $\kappa = 1{,}400\,8$, $k_\mathrm{a} = 0{,}023\,55$ J/(s·m·K) y, a la
  vuelta, $C_\mathrm{P} = 938{,}7$ J/(kg·K).
- **El problema:** dos de los cinco no son valores de IEC 61094-2:2009. La
  Tabla F.1 de esa norma (folio impreso 40) tabula exactamente cinco magnitudes
  en ese estado: $\rho$, $c_0$, $\kappa$, $\eta$ y la **difusividad** térmica
  $\alpha_t = 2{,}115\,317 \times 10^{-5}$ m²/s. No tabula ni la conductividad
  térmica ni el calor específico; ésos aparecen en el Anexo F sólo como las dos
  expresiones de la cláusula F.6, que no imprimen valor. Los tres valores del
  Anexo A.3 que sí cuadran son precisamente las tres celdas de la Tabla F.1
  redondeadas a cuatro cifras ($345{,}866\,52 \to 345{,}9$;
  $1{,}186\,084\,8 \to 1{,}186$; $1{,}400\,757\,3 \to 1{,}400\,8$). Los dos
  que no cuadran son precisamente las dos magnitudes que la Tabla F.1 no imprime:
  evaluada en ese mismo estado, la cláusula F.6 da
  $k_\mathrm{a} = 0{,}025\,434\,1$ J/(s·m·K) y $C_\mathrm{P} = 1013{,}74$
  J/(kg·K), cada uno mayor que el par impreso por el mismo factor 1,0800.

  El factor común no es casualidad ni una diferencia de unidades. El par está
  anclado a la difusividad tabulada: $0{,}023\,55 / (1{,}186 \times
  2{,}115\,317 \times 10^{-5}) = 938{,}708\,5$, que imprime 938,7. O sea, uno
  de los dos vino de otro sitio y el otro se retrocalculó por la Fórmula (F.5)
  para que $\alpha_t$ siguiera saliendo. Cuál de los dos es el ajeno lo decide la
  termodinámica y no una preferencia: $C_\mathrm{P} = 938{,}7$ J/(kg·K) son
  27,19 J/(mol·K), por debajo del suelo del rotor rígido diatómico
  $(7/2)R = 29{,}10$ J/(mol·K), así que no es aire a ninguna temperatura, en
  ninguna unidad, ni por masa ni por mol, y la expresión del Anexo F para
  $C_\mathrm{P}$ no baja de unos 1013 J/(kg·K) en todo el intervalo de 200 K a
  400 K. La conductividad 0,023 55 J/(s·m·K), en cambio, sí es una conductividad
  real del aire: es la que da la expresión del Anexo F cerca de −1,4 °C, fuera
  del dominio de 15 °C a 27 °C que el propio Anexo F imprime.
- **Consecuencia para el ejemplo del anexo:** ninguna. La Fórmula (A.5) usa
  $k_\mathrm{a}$ y $C_\mathrm{P}$ sólo a través de la combinación
  $k_\mathrm{a}/(\rho_0 c_0 C_\mathrm{P})$, donde el factor común se cancela,
  así que los dos pares dan el $b = 1{,}83 \times 10^{-3}$ m y el
  $\kappa' = 1{,}370$ impresos. El defecto es invisible dentro del Anexo A.3 y
  sólo aparece al leer cualquiera de las dos constantes por separado, como
  documento al que se atribuye haberla publicado.
- **Evidencia:** las dos páginas impresas contra la Tabla F.1 (folio impreso 40)
  y la cláusula F.6 (folio impreso 39) de IEC 61094-2:2009; las expresiones de la
  cláusula F.6 evaluadas a 23 °C, 101 325 Pa y 50 % de humedad relativa, que
  reproducen el $\alpha_t$ impreso a $1{,}0 \times 10^{-7}$ relativo; el calor
  molar que implican los 938,7 J/(kg·K) contra el suelo diatómico.
  IEC 61094-2:2009 no es referencia normativa de ISO 9053-2:2020: aparece sólo
  como entrada [4] de la bibliografía. Verificado en la página 17 (p. 13 impresa)
  y la página 18 (p. 14 impresa) del PDF de ISO 9053-2:2020, y en la página 42
  (p. 40 impresa) y la página 41 (p. 39 impresa) del PDF de BS EN 61094-2:2009.
- **Comportamiento de la biblioteca:** las filas de conformidad que reproducen el
  Anexo A.3 pasan los cinco valores que el anexo imprime, así que reproducen la
  norma en vez de limitarse a coincidir con ella. Los valores por defecto que
  recibe quien llama son ese mismo estado del aire calculado desde el Anexo F de
  IEC 61094-2:2009, que es lo que el anexo dice estar usando; los dos caen sobre
  el $b$ y el $\kappa'$ impresos ([`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data),
  comprobaciones de conformidad «ISO 9053-2:2020 Annex A.3»).
- **Estado:** sin comunicar.

## EN 12354-1:2000 Fórmula (E.5) / ISO 12354-1:2017 E.3.4 (errata de la acotación de K24)

- **Ubicación:** EN 12354-1:2000, Anexo E, el bloque de uniones de pared con
  capas elásticas intermedias impreso bajo la Figura E.5 y numerado Fórmula
  (E.5) (p. 46 impresa), y la NOTA 4 de E.3.4 de ISO 12354-1:2017. El Anexo E
  de la edición de 2000 solo tiene dos cláusulas numeradas, E.1 «Determination
  methods» y E.2 «Empirical data», así que «E.5» es un número de fórmula, no
  de cláusula; una revisión anterior de esta entrada lo citaba como cláusula.
- **El impreso:** $K_{24} = 3{,}7 + 14{,}1 M + 5{,}7 M^{2}\ \text{dB}$;
  $0 \le K_{24} \le -4\ \text{dB}$ ; $0\ \text{dB / octave}$, es decir, la
  acotación del término de unión $K_{24}$ es un intervalo vacío; la edición de
  2017 repite la errata de 2000 al pie de la letra.
- **El problema:** el intervalo es imposible tal como está impreso; la figura
  que lo acompaña y la física (el término es una reducción acotada por abajo)
  indican $-4\ \text{dB} \le K_{24} \le 0\ \text{dB}$.
- **Evidencia:** la familia de curvas de la Figura E.5 en la misma página
  recorre la rama de $K_{24}$ desde 0 dB hasta cerca de −4 dB sobre las
  relaciones de masas dibujadas, que es el intervalo leído en el otro orden.
  Verificado en la página 48 del PDF (p. 46 impresa) de EN 12354-1:2000 y la
  página 52 del PDF (p. 46 impresa) de ISO 12354-1:2017.
- **Comportamiento de la biblioteca:** implementa la acotación como
  $-4 \le K_{24} \le 0$ con una nota de errata en el docstring.
- **Estado:** sin notificar.

## EN 12354-1:2000, Figura E.9 (E.7) (K24 expresado en la relación de masas del eje de la figura)

- **Ubicación:** Anexo E, Figura E.9 / Fórmula (E.7) (unión de pared ligera de
  doble hoja con elementos homogéneos), la línea de $K_{24}$.
- **El impreso:** $K_{24} = 3{,}0 - 14{,}1 M + 5{,}7 M^{2}\ \text{dB}$ (para
  $m_2/m_1 > 3$), bajo una figura cuyo eje x es $m_2/m_1$.
- **El problema:** el Anexo E define $M$ por trayectoria de transmisión como
  $M = \lg(m'_{\perp,i}/m'_i)$ (elemento perpendicular sobre el elemento que
  lleva la trayectoria). La trayectoria 2→4 de $K_{24}$ la lleva el elemento
  homogéneo ($m_2 = m_4$) con la hoja ($m_1$) perpendicular, así que el $M$
  por trayectoria es $\log_{10}(m_1/m_2)$, pero la línea impresa de $K_{24}$
  solo casa con la curva de su propia figura cuando $M$ se lee como la
  variable del eje x, $\log_{10}(m_2/m_1)$ (p. ej. −2,4 dB en $m_2/m_1 = 3$,
  −5,4 dB en 10). Leída con el $M$ que declara el anexo, la línea contradice
  la figura en $28{,}2 \cdot |\log_{10}(m_2/m_1)|\ \text{dB}$. La otra línea
  de $K_{24}$ de la misma edición (Figura E.5, Fórmula (E.5)) *sí* sigue el
  $M$ por trayectoria declarado, así que los dos impresos de $K_{24}$ de la
  edición de 2000 usan convenciones distintas en silencio. ISO 12354-1:2017
  E.3.5 imprime la relación de forma consistente en la convención por
  trayectoria de su Fórmula (E.3),
  $K_{24} = 3{,}0 + 14{,}1 M + 5{,}7 M^{2}$; las dos ediciones coinciden
  numéricamente (una revisión anterior de esta entrada leyó el impreso de 2017
  como una errata de signo; la re-deducción contra las figuras de ambas
  ediciones muestra que es un cambio de convención, no un defecto del texto de
  2017).
- **Evidencia:** evaluación numérica de ambas formas contra la curva de la
  Figura E.9. Verificado en la página 44 del PDF (p. 42 impresa), la página 48
  del PDF (p. 46 impresa) y la página 50 del PDF (p. 48 impresa) de
  EN 12354-1:2000, y en la página 53 del PDF (p. 47 impresa) de
  ISO 12354-1:2017, cuyo E.3.5 imprime su línea de K24 junto a una Figura E.7
  que no lleva ningún eje de relación de masas.
- **Comportamiento de la biblioteca:** implementa la convención por
  trayectoria de manera uniforme (`junction_vibration_reduction`,
  mass_ratio = $m'_{\perp,i}/m'_i$ para todas las ramas), así que la rama de
  doble hoja de E.7 toma relaciones hoja-sobre-homogéneo por debajo de 1/3 y
  evalúa $3{,}0 + 14{,}1 M + 5{,}7 M^2$.
- **Estado:** sin notificar.

## EN 12354-2:2000, Fórmula (3) frente al Anexo E.3 (nivel de impacto estandarizado)

- **Ubicación:** Fórmula (3) y ejemplo resuelto E.3.
- **El impreso:** la Fórmula (3) define
  $L'_{nT} = L'_n - 10 \lg(0{,}16 \cdot V/(A_0 \cdot T_0))$, que se reduce
  exactamente a $L'_n - 10 \lg(0{,}032 \cdot V)$, es decir, un volumen de
  referencia de $31{,}25\ \text{m}^3$. El Anexo E.3 declara «from equation
  (3): $L'_{nT,w} = L'_{n,w} - 10 \lg(V/30)$».
- **El problema:** el $V/30$ del anexo es un redondeo de la propia constante
  de la fórmula; las dos variantes difieren en 0,177 dB constantes.
- **Evidencia:** álgebra directa; ambas variantes recalculadas para el caso
  de E.3 (42,959 frente a 42,782 dB, ambas redondean a 43 en ese ejemplo).
  Verificado en la página 7 del PDF (p. 5 impresa) y la página 34 del PDF
  (p. 32 impresa) de EN 12354-2:2000.
- **Comportamiento de la biblioteca:** implementa la forma exacta
  $0{,}032 \cdot V$ y documenta el redondeo del anexo.
- **Estado:** sin notificar.

## EN 12354-3:2000, Fórmula (5) (forma reducida de la diferencia de niveles normalizada)

- **Ubicación:** apartado 3.1.5 «Relations between quantities», Fórmula (5)
  (p. 6 impresa).
- **El impreso:**
  $D_{2m,n} = D_{2m,nT} - 10 \lg[0{,}16\,V/(T_0 A_0)] = D_{2m,nT} - 10 \lg 0{,}32\,V\ \text{dB}$.
- **El problema:** la forma reducida está mal por un factor de diez. Seis
  líneas más arriba, la lista de símbolos del apartado 3.1.4 define $A_0$
  como «the reference equivalent sound absorption area, in square metres, for
  dwellings given as 10 m²», y la lista de símbolos del apartado 3.1.3 de la
  página anterior define $T_0$ como «the reference reverberation time, in
  seconds, for dwellings given as 0,5 s». Así que
  $0{,}16/(T_0 A_0) = 0{,}16/5 = 0{,}032$, no 0,32. Aplicada como está
  impresa, la forma reducida desplaza toda diferencia de niveles de fachada
  normalizada en exactamente $10\log_{10} 10 = 10\ \text{dB}$. El análogo
  exacto de la parte compañera, la Fórmula (3) de EN 12354-2:2000, imprime la
  misma álgebra correctamente:
  $L'_{nT} = L'_n - 10 \lg[0{,}16\,V/(A_0 T_0)] = L'_n - 10 \lg 0{,}032\,V\ \text{dB}$.
  ISO 12354-3:2017 retiró la forma reducida por completo: su Fórmula (5)
  imprime solo $D_{2m,n} = D_{2m,nT} - 10 \lg[C_\text{sab} V/(A_0 T_0)]$ con
  $C_\text{sab} = 0{,}16\ \text{s/m}$.
- **Evidencia:** álgebra directa con los propios $A_0$ y $T_0$ de la norma, y
  la comparación lado a lado con la Fórmula (3) de la Parte 2, reducida
  correctamente. Verificado en la página 8 del PDF (p. 6 impresa) y la página
  7 del PDF (p. 5 impresa) de EN 12354-3:2000, en la página 7 del PDF (p. 5
  impresa) de EN 12354-2:2000 para su Fórmula (3), y en la página 12 del PDF
  (p. 6 impresa) de ISO 12354-3:2017 para las Fórmulas (4) y (5) de 2017.
- **Comportamiento de la biblioteca:** no le afecta. Ningún camino de código
  implementa la forma reducida: el modelo de fachada calcula $D_{2m,nT}$
  desde la Fórmula (13)
  ([`facade.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/prediction/facade.py)), y el
  método de inspección convierte con la forma sin reducir
  $D_{2m,n} = D_{2m} + k + 10\log_{10}[A_0 T_0/(0{,}16 V)]$ del apartado 3.15
  de ISO 10052
  ([`survey_insulation.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/measurement/survey_insulation.py)).
  Las dos constantes de estandarización que *sí* están pre-plegadas en otros
  puntos de la biblioteca son ambas correctas: $0{,}032$ para la forma de
  impacto de la Parte 2 y $0{,}32$ para la forma aérea de la Parte 1,
  $D_{nT} = R' + 10\log_{10}(0{,}16 V/(T_0 S_s))$, cuyo denominador es un
  área y no $A_0$.
- **Estado:** sin notificar.

## EN 12354-3:2000, Fórmula (13) frente a su propio ejemplo del Anexo F (la constante «6»)

- **Ubicación:** apartado 4.1, Fórmula (13) (p. 9 impresa), contra el ejemplo
  resuelto del Anexo F (pp. 27-28 impresas).
- **El impreso:** la Fórmula (13) da
  $D_{2m,nT} = R' + \Delta L_\text{fs} + 10 \lg[V/(6 T_0 S)]\ \text{dB}$,
  mientras que la tabla de resultados de F.1.3 imprime una fila de
  $D_{2m,nT}$ que es exactamente $R' + 1{,}5\ \text{dB}$ en las cinco bandas
  de octava y en la columna de valor único (25,9/23,0/26,4/36,9/39,0 contra
  24,4/21,5/24,9/35,4/37,5, y 29,3 contra 27,8).
- **El problema:** en esta constante el *ejemplo* es autoconsistente y la
  *fórmula* es la discrepante. (Dos celdas de la misma tabla del anexo no se
  siguen de sus filas de elementos, que es el asunto de la entrada siguiente;
  la fila impresa de $+1,5$ dB se cumple en todas las bandas de todos modos,
  así que los dos defectos son independientes.) Con los propios datos del
  ejemplo ($V = 50\ \text{m}^3$, $S = 11{,}3\ \text{m}^2$,
  $T_0 = 0{,}5\ \text{s}$, $\Delta L_\text{fs} = 0$), la forma de Sabine da
  $10\log_{10}[0{,}16 \cdot 50/(0{,}5 \cdot 11{,}3)] = 1{,}5104\ \text{dB}$,
  que es la fila impresa de +1,5 dB; la Fórmula (13) tal como está impresa da
  $10\log_{10}[50/(6 \cdot 0{,}5 \cdot 11{,}3)] = 1{,}6877\ \text{dB}$. La
  brecha es la constante: el «6» de la Fórmula (13) es un
  $1/0{,}16 = 6{,}25$ redondeado, y
  $10\log_{10}(6{,}25/6) = 0{,}177\ \text{dB}$ es exactamente la
  discrepancia. ISO 12354-3:2017 lo sustituyó por una constante de Sabine
  explícita, imprimiendo la Fórmula (4) como
  $D_{2m,nT} = R' + \Delta L_\text{fs} + [10 \lg(C_\text{sab} V/(T_0 S))]$
  con $C_\text{sab} = 0{,}16\ \text{s/m}$, que es la constante que el ejemplo
  de 2000 ya usaba. Una revisión anterior de esta entrada atribuía la fila de
  1,5 dB al ejemplo; la atribución es al revés.
- **Evidencia:** evaluación de ambas constantes contra las filas impresas del
  Anexo F, que concuerdan con 0,16 dentro de los 0,05 dB que lleva la tabla y
  discrepan del 6 redondeado en 0,18 dB uniformes; y la refundición de 2017,
  que adopta la constante del ejemplo. El resultado de valor único del
  ejemplo, $D_{2m,nT,w} = 33\ \text{dB}$, es insensible a la diferencia y se
  reproduce en cualquier caso. Verificado en las páginas 11 (p. 9 impresa),
  29 (p. 27 impresa) y 30 (p. 28 impresa) del PDF de EN 12354-3:2000, y en la
  página 12 del PDF (p. 6 impresa) de ISO 12354-3:2017.
- **Comportamiento de la biblioteca:** implementa la Fórmula (13) tal como
  está impresa, con el 6 redondeado; los datos de test dejan constancia de
  que las filas del Anexo F siguen la constante exacta 0,16 y quedan 0,18 dB
  por debajo del modelo.
- **Estado:** sin notificar.

## EN 12354-3:2000, Anexo F.1.3 (las celdas de R' de 1 kHz y 2 kHz)

- **Ubicación:** Anexo F, tabla F.1.3 «Results for façade» (p. 28 impresa),
  la fila `R' (equation 10)`.
- **El impreso:** $R'$ = 24,4 / 21,5 / 24,9 / 35,4 / 37,5 dB a 125 / 250 /
  500 / 1000 / 2000 Hz.
- **El problema:** las dos últimas celdas no se siguen de las propias filas
  de elementos de la tabla. La Fórmula (10),
  $R' = -10\log_{10} \sum \tau_{e,i}$, aplicada a las cuatro columnas de
  $-10\log_{10} \tau_e$ impresas justo encima, da 24,41 / 21,50 / 24,86 /
  **35,78** / **37,99** dB. Las tres primeras celdas se reproducen dentro de
  los 0,05 dB que lleva la tabla; las celdas de 1 kHz y 2 kHz están impresas
  0,4 dB y 0,5 dB por debajo.
- **Evidencia:** suma energética de las filas de elementos impresas banda a
  banda (1 kHz: 60,7 / 40,0 / 46,6 / 38,5 dB; 2 kHz: 66,7 / 41,0 / 43,6 /
  44,5 dB). La fila de $D_{2m,nT}$ de debajo es un $R' + 1{,}5\ \text{dB}$
  uniforme en todas las bandas, incluidas esas dos, así que hereda el mismo
  desplazamiento, y el resultado de valor único $D_{2m,nT,w} = 33\ \text{dB}$
  es insensible a él y sigue reproduciéndose. Verificado en la página 30 del
  PDF (p. 28 impresa) de EN 12354-3:2000.
- **Comportamiento de la biblioteca:** los datos de test anotan la
  inconsistencia junto al ancla afectada.
- **Estado:** sin notificar.

## EN 12354-5:2009, Tabla F.1 y apartado F.4.2 (fuerza de referencia impresa como 1 pN)

- **Ubicación:** Anexo F, apartado F.4.2: la lista de símbolos de la Fórmula
  (F.9), la frase que introduce la forma cerrada y el pie de la Tabla F.1
  (p. 59 impresa).
- **El impreso:** «$L_F$ is the force level in the source room, in dB re
  1 pN»; «$L_F = 10\lg 2{,}5f/10^{-12}$ dB re 1 pN or
  $L_F = 10\lg 0{,}8f/10^{-12}$ dB re 1 pN for one-third octave bands»; y
  «Table F.1 – Force level $L_F$ re 1 pN for the ISO tapping machine in
  octave bands», cuyas ocho celdas leen 139, 142, 145, 148, 151, 154, 156 y
  156 dB.
- **El problema:** la fuerza de referencia de esos niveles es $10^{-6}$ N, no
  1 pN. Tres lecturas independientes concuerdan, y ninguna es compatible con
  la referencia impresa. **(a) La propia álgebra del anexo.** Un nivel de
  potencia re 1 pW construido desde un nivel de fuerza y una movilidad es
  $L_W = L_F + 10\lg(F_0^2 Y / W_0)$. La Fórmula (D.5a) imprime
  $L_{Ws,c} = L_{F,eq} + 10\lg Y_s$ y la Fórmula (D.9a) imprime
  $L_{Ws,c} = L_F - 5 - 10\lg f$, que es la misma expresión evaluada en la
  movilidad de fuente de tipo masa $Y_s = (2\pi f M)^{-1}$ de un martillo de
  máquina de impactos de 0,5 kg. Ninguna lleva término alguno de
  $F_0^2/W_0$, así que ambas solo cuadran cuando
  $F_0^2 / W_0 = 1\ \text{s}^{-1}$, es decir $F_0 = 10^{-6}$ N; leídas re
  1 pN, cada una se quedaría 120 dB corta respecto al nivel que define. La
  contrapartida en velocidad, la Fórmula (D.10a), sí imprime su término de
  referencia $10\lg(v_\text{ref}^2/W_\text{ref})$ y declara que el resultado
  cancela el $10\lg Z_s$ exactamente, cosa que hace con los $10^{-9}$ m/s que
  la propia norma da como referencia del nivel de velocidad en el apartado
  F.4.2. El anexo es por tanto explícito y correcto con la referencia de
  velocidad y calla la de fuerza. **(b) La máquina que produce la tabla.** La
  máquina de impactos ISO deja caer martillos de 0,5 kg desde 40 mm a diez
  impactos por segundo, así que cada impacto transfiere un momento de
  0,443 N·s y la fuerza es un tren de impulsos de 10 Hz cada uno de cuyos
  armónicos lleva 6,26 N r.m.s. Sumando los armónicos que caen dentro de cada
  banda de octava salen 139,4 / 142,4 / 145,4 / 148,4 / 151,4 / 154,4 dB re
  $10^{-6}$ N de 31,5 Hz a 1 kHz, reproduciendo las seis primeras celdas de
  la Tabla F.1 con margen de 0,5 dB; las celdas de 2 kHz y 4 kHz quedan por
  debajo de esa recta, que es la caída que la propia norma señala con «up
  till about 1000 Hz». Re 1 pN, las mismas celdas describirían fuerzas de
  decenas de micronewtons, que ninguna máquina de impactos produce. **(c) La
  norma compañera.** La Fórmula (15) de EN 15657:2018, que es de donde salen
  en primer lugar los datos de fuente estructural del Anexo D, escribe la
  misma conversión de fuerza a potencia «in dB re $F_0 = 10^{-6}$ N», y
  $10^{-6}$ N es la fuerza de referencia preferida de ISO 1683.
- **Evidencia:** verificado en las páginas 61 y 62 del PDF (pp. 59 y 60
  impresas) de BS EN 12354-5:2009, que llevan el apartado F.4.2 con la lista
  de símbolos de la Fórmula (F.9), la forma cerrada, la Tabla F.1 completa y
  la lista de símbolos de la Fórmula (F.11) con su referencia de velocidad de
  $10^{-9}$ m/s; y en las páginas 45, 48 y 50 del PDF (pp. 43, 46 y 48
  impresas) de la misma edición, que llevan las Fórmulas (D.5a), (D.9a) y
  (D.10a).
- **Comportamiento de la biblioteca:** publica las celdas impresas sin
  cambios y las documenta re $10^{-6}$ N. `tapping_machine_force_level`
  devuelve los ocho valores de la Tabla F.1,
  `tapping_machine_force_level_estimate` la forma cerrada y
  `tapping_machine_characteristic_power_level` la Fórmula (D.9a) tal como
  está impresa;
  `test_table_f1_is_referred_to_1e_6_newton_not_1_piconewton` fija la lectura
  contra la mecánica de la máquina.
- **Estado:** sin notificar.

## EN 12354-5:2009, leyenda de la Figura D.3 (tres curvas bajo un mismo símbolo)

- **Ubicación:** Anexo D, la leyenda de la Figura D.3 (p. 47 impresa).
- **El impreso:** tres filas de leyenda, cada una etiquetada con el mismo
  símbolo: $L_{Ws,c,A} = 124\ \text{dB}$, $L_{Ws,c,A} = 119\ \text{dB}$ y
  $L_{Ws,c,A} = 102\ \text{dB}$.
- **El problema:** el propio pie de la figura lee «Structure-borne sound
  power for the ISO-tapping machine: characteristic source power, installed
  power on a wooden floor and installed power on a concrete floor; the
  A-weighted power level is also indicated». Solo la primera curva es una
  potencia característica; las otras dos son potencias instaladas y sus
  totales ponderados A son $L_{Ws,\text{inst},A}$. Las curvas dibujadas
  zanjan la asignación: la primera es plana en torno a 114,5 dB re 1 pW, que
  es el resultado independiente de la frecuencia de la Fórmula (D.9a) para la
  máquina de impactos, mientras que las otras dos crecen con la frecuencia y
  quedan por debajo, la del suelo de hormigón la más baja, como exige
  $L_{Ws,c} - D_{C,i}$.
- **Evidencia:** verificado en la página 49 del PDF (p. 47 impresa) de
  BS EN 12354-5:2009, la página que lleva la Figura D.3 con su leyenda y su
  pie.
- **Comportamiento de la biblioteca:** no hizo falta ninguno; ningún valor se
  lee de la Figura D.3.
  `test_formula_d9a_is_flat_at_about_115_db_per_third_octave` fija la curva
  característica plana a la que pertenece la primera fila de la leyenda.
- **Estado:** sin notificar.

## ISO 12354-1:2017 Tabla L.3 / ISO 12354-2:2017 Tabla G.3 (sumas de perímetro)

- **Ubicación:** el bloque de datos de entrada bajo la Tabla L.3 (p. 81
  impresa) y el bloque idéntico bajo la Tabla G.3 (p. 38 impresa), que lista
  la suma de absorción perimetral $\sum l_k \alpha_k$ de la Fórmula (C.1)
  para el ejemplo resuelto.
- **El impreso:** un valor por *tipo* de elemento: suelo separador 2,364 m
  ($S = 20\ \text{m}^2$), pared exterior 2,375 m ($S = 11\ \text{m}^2$),
  pared interior 1,840 m ($S = 13{,}75\ \text{m}^2$).
- **El problema:** la Fórmula (C.1) necesita una suma por *elemento*, y el
  ejemplo tiene cinco elementos con tres áreas distintas. Solo dos de los
  tres valores impresos reproducen las columnas que se supone que gobiernan:
  2,375 m con $S = 11\ \text{m}^2$ da la pared exterior 1 exacta, y 1,840 m
  con $S = 13{,}75\ \text{m}^2$ da la pared interior **2** exacta. Los
  2,364 m impresos del suelo separador no reproducen su propia columna en
  ninguna banda (0,074 9 contra los 0,083 1 impresos a 50 Hz, 0,026 4 contra
  0,029 0 a 500 Hz); 2,659 m sí, en todas las bandas. Los dos elementos sin
  valor impreso necesitan 2,548 m (pared exterior 2,
  $S = 13{,}75\ \text{m}^2$) y 1,636 m (pared interior 1,
  $S = 11\ \text{m}^2$).
- **Evidencia:** las cinco sumas re-deducidas desde la Fórmula (C.4),
  $\alpha_k = \sum_j \sqrt{f_{c,j}/f_\text{ref}}\ 10^{-K_{ij}/10}$, sobre la
  propia geometría de uniones del ejemplo con los índices del Anexo E sin
  redondear: 2,659 / 2,375 / 2,548 / 1,636 / 1,839 m. La deducción devuelve
  los dos valores impresos que son autoconsistentes con sus propias columnas
  (2,375 m, y 1,839 m contra los 1,840 m impresos) y aporta los tres que
  faltan o están mal, y entonces todas las columnas de
  $\eta_\text{tot,situ}$ de la Tabla L.3 / G.3 se reproducen a
  $5 \cdot 10^{-5}$. Los valores impresos aplicados al elemento equivocado
  del mismo tipo fallan por mucho más que ese redondeo: 2,375 m en la pared
  exterior 2 da 0,108 5 contra los 0,114 9 impresos a 50 Hz, y 1,840 m en la
  pared interior 1 da 0,085 0 contra 0,077 0.
- **Comportamiento de la biblioteca:** `in_situ_total_loss_factor` toma
  $\sum l_k \alpha_k$ como entrada y `perimeter_absorption_coefficient`
  implementa la Fórmula (C.4); la fixture del Anexo L deduce las cinco sumas
  por esa vía en lugar de usar el bloque impreso, y lo dice
  ([`tests/building/prediction/test_detailed_model.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_detailed_model.py)).
- **Estado:** sin notificar.

## ISO 12354-1:2017 Tabla L.3 / ISO 12354-2:2017 Tabla G.3 (ηint de la pared exterior)

- **Ubicación:** el mismo bloque de datos de entrada, línea de la pared
  exterior.
- **El impreso:** $\eta_\text{int} = 0{,}013$ para las paredes exteriores de
  hormigón celular curado en autoclave de 365 mm.
- **El problema:** la propia especificación de elementos del ejemplo, y la
  Tabla B.3 del Anexo B para el hormigón celular curado en autoclave, dan
  0,012 5. Solo 0,012 5 reproduce el $\eta_\text{tot,situ}$ tabulado: a
  500 Hz la Fórmula (C.1) da
  $0{,}012\,5 + 0{,}001\,41 + 0{,}034\,57 = 0{,}048\,5$, el valor impreso,
  donde 0,013 daría 0,049 0.
- **Evidencia:** recálculo término a término de la Fórmula (C.1) para ambas
  paredes exteriores en todas las bandas con cada $\eta_\text{int}$
  candidato.
- **Comportamiento de la biblioteca:** la fixture del Anexo L usa 0,012 5.
- **Estado:** sin notificar.

## ISO 12354-1:2017, Tabla L.4 (segundo bloque de trayectoria etiquetado 2d)

- **Ubicación:** Anexo L, Tabla L.4 (p. 82 impresa), el bloque derecho
  encabezado «Transmission path 2d».
- **El impreso:** el bloque da $\alpha_{i,\text{situ}}$ = 6,3 a 14,1,
  $D_{v,ij,\text{situ}}$ = 11,0 a 13,6 y $R_{ij}$ = 43,9 a 84,6 dB.
- **El problema:** esos son los números de la trayectoria **4d** (pared
  interior 2 al suelo separador), no de la 2d (pared exterior 2). La Tabla
  L.1 del mismo anexo imprime la columna $R_{4d}$ entera, de 43,9 a 84,6 dB,
  y la columna $R_{ij}$ del bloque es esa columna celda a celda. Lo que lo
  zanja banda a banda son las otras dos columnas, que no admiten confusión:
  la pared exterior 2 tiene $\alpha_{i,\text{situ}} = 10{,}3\ \text{m}$ a
  50 Hz ($S = 13{,}75\ \text{m}^2$, $\eta_\text{tot} = 0{,}114\,9$) mientras
  que la pared interior 2 tiene 6,3 m ($\eta_\text{tot} = 0{,}070\,3$), el
  valor impreso; y $D_{v,ij,\text{situ}}$ sigue el $K_{ij}$ de suelo a pared
  interior de 8,8 dB, que da 11,0 a 13,6 dB, no el de suelo a pared exterior
  de 6,4 dB, que da 9,6 a 11,9 dB.
- **Evidencia:** recálculo independiente de las Fórmulas (10), (11) y (15)
  para ambas trayectorias candidatas en todas las bandas. La trayectoria 4d
  reproduce las tres columnas del bloque, $\alpha_{i,\text{situ}}$ a 0,05 m y
  $D_{v,ij,\text{situ}}$ y $R_{ij}$ a 0,05 dB, que es la resolución impresa.
  La trayectoria 2d se aparta de la columna $R_{ij}$ del bloque entre 0,1 dB
  y 7,0 dB según la banda, y se acerca más entre 100 Hz y 160 Hz (0,5 / 0,5 /
  0,1 dB), así que $R_{ij}$ por sí sola no identifica la trayectoria en esas
  bandas; $\alpha_{i,\text{situ}}$ (10,3 contra 6,3 m a 50 Hz) y
  $D_{v,ij,\text{situ}}$ (de 1,4 dB a 1,7 dB de separación en todas las
  bandas) sí.
- **Comportamiento de la biblioteca:** el test que afirma el bloque lo
  construye como trayectoria 4d y nombra el etiquetado erróneo.
- **Estado:** sin notificar.

## ISO 12354-1:2017, Tabla L.1 (índices globales no enteros)

- **Ubicación:** Anexo L, Tabla L.1 (p. 79 impresa), la fila de $R_w$ y la
  frase que la sigue, y la fila correspondiente de $L_{n,w}$ de la Tabla G.1
  de ISO 12354-2:2017.
- **El impreso:** la fila de $R_w$ da un decimal para cada trayectoria
  (75,1 / 84,5 / 70,6 / … y 57,8 en la columna del total) mientras que la
  frase inmediatamente debajo declara
  $R'_w\,(C\,;\,C_\text{tr}) = 57{,}9\ (-2\,;\,-8)\ \text{dB}$.
- **El problema:** ISO 717-1 valora desplazando la curva de referencia **en
  pasos de 1 dB**, así que un índice global es un entero; los valores
  impresos con un decimal son la curva de referencia desplazada *de forma
  continua* hasta que la suma de desviaciones desfavorables vale exactamente
  32,0 dB. La fila aérea de $R_w$ de la Tabla L.1 *trunca* ese valor continuo
  a un decimal mientras que la frase de debajo redondea, y por eso la misma
  magnitud aparece dos veces como 57,8 y 57,9; la fila de impacto de
  $L_{n,w}$ de la Tabla G.1 redondea en cambio (29,58 se imprime 29,6 y 40,98
  como 41,0), así que el truncamiento es una propiedad solo de la fila aérea.
  Los términos de adaptación espectral heredan el desplazamiento: con el
  índice ISO 717-1 de 57 dB son $C = -1$ y $C_\text{tr} = -7$, y el
  (−2 ; −8) impreso es exactamente el par desplazado por los mismos 0,86 dB.
- **Evidencia:** una resolución por desplazamiento continuo de la curva de
  referencia de ISO 717-1 contra los espectros por banda impresos reproduce
  todos los valores impresos de ambas filas ($R_{Dd}$ 75,12 contra 75,1;
  $R_{D1}$ 84,54 contra 84,5; $R_{11}$ 70,66 contra 70,6; el total 57,86
  contra 57,8 / 57,9; en el lado de impacto $L_{n,Df1}$ 29,58 contra 29,6 y
  el total 40,98 contra 41,0), mientras que los índices ISO 717-1 en pasos de
  1 dB de los mismos espectros son 75, 84, 70 y 57 dB. Verificado en la
  página 85 del PDF (p. 79 impresa) de ISO 12354-1:2017.
- **Comportamiento de la biblioteca:** `weighted_rating` /
  `weighted_impact_rating` implementan ISO 717-1/-2 tal como están escritas,
  así que el modelo detallado devuelve $R'_w = 57\ \text{dB}$ y
  $L'_{n,w} = 41\ \text{dB}$ ($C_I = 2$) para el ejemplo; el test fija esos
  valores y documenta los impresos.
- **Estado:** sin notificar.

## ISO 12354-2:2017, Tabla G.1 (columnas de flancos de 50 Hz a 80 Hz)

- **Ubicación:** Anexo G, Tabla G.1 (p. 36 impresa), las cuatro columnas de
  $L_{n,Df}$, filas de 50 Hz, 63 Hz y 80 Hz.
- **El impreso:** $L_{n,Df1}$ = 47,3 / 44,9 / 46,2 dB.
- **El problema:** la Tabla G.4 del mismo anexo imprime la misma trayectoria
  Df para la pared exterior 1, desde las mismas entradas, como 47,8 / 45,9 /
  47,0 dB. Las dos tablas no pueden estar bien a la vez, y de 100 Hz hacia
  arriba coinciden exactamente.
- **Evidencia:** la Fórmula (12) evaluada desde las propias columnas de la
  Tabla G.3 del anexo ($L_{n,\text{situ}}$, $R_\text{situ}$) y las columnas
  $D_{v,ij,\text{situ}}$ y $\Delta L_\text{situ}$ de la Tabla G.4 da 47,80 /
  45,85 / 46,95 dB, reproduciendo los 47,8 / 45,9 / 47,0 impresos de la Tabla
  G.4 a 0,05 dB y la Tabla G.1 solo de 100 Hz hacia arriba. Llevando el mismo
  recálculo por toda la cadena, la pared exterior 2 queda baja entre 0,5 dB y
  1,0 dB en las mismas tres bandas y las dos paredes interiores bajas hasta
  0,5 dB a 50 Hz y 63 Hz (sus celdas de 80 Hz coinciden). De 100 Hz hacia
  arriba ninguna columna de flancos se desvía más de 0,15 dB. Corregir las
  celdas afectadas sube el total impreso $L'_n$ solo ligeramente: de 58,6 a
  58,7 dB a 50 Hz, de 57,0 a 57,2 dB a 63 Hz, de 55,9 a 56,1 dB a 80 Hz.
- **Comportamiento de la biblioteca:** el test afirma la Tabla G.4 completa,
  la columna directa de la Tabla G.1 en todo el rango, y las columnas de
  flancos de la Tabla G.1 de 100 Hz hacia arriba, nombrando la discrepancia.
- **Estado:** sin notificar.

## ISO 12354-2:2017, Tabla G.8 (Kij de unión y m'i)

- **Ubicación:** Anexo G, Tabla G.8 (p. 40 impresa), la unión rígida en T de
  pared interior con pared exterior.
- **El impreso:** la fila «Int. wall 1/2 - Ext. wall 1/2» da
  $K_{ij} = 6{,}6\ \text{dB}$; la fila de debajo, «Ext. wall 1/2 - Ext. wall
  1/2», da $m'_i = 2{,}19\ \text{kg/m}^2$.
- **El problema:** dos erratas independientes. La rama de esquina de la T
  rígida $K_{12} = 5{,}7 + 5{,}7 M^2$ con
  $M = \log_{10}(360/219) = 0{,}215\,6$ da 5,97, es decir **6,0**, y la Tabla
  L.8 de ISO 12354-1:2017 imprime 6,0 para la unión idéntica del ejemplo
  idéntico. Y la masa por unidad de área de la pared exterior es
  $219{,}0\ \text{kg/m}^2$ en todo el ejemplo, no 2,19 (un factor 100).
- **Evidencia:** evaluación de la rama de esquina según el Anexo E; las demás
  filas de la misma tabla y todo el Anexo L de ISO 12354-1 usan
  $219{,}0\ \text{kg/m}^2$. Verificado en la página 46 del PDF (p. 40
  impresa) de ISO 12354-2:2017, cuyas columnas de masa de la Tabla G.8 se
  encabezan `m'i` y `m'orthogonal`, y la página 89 del PDF (p. 83 impresa) de
  ISO 12354-1:2017.
- **Comportamiento de la biblioteca:** usa 6,0 dB y
  $219{,}0\ \text{kg/m}^2$.
- **Estado:** sin notificar.

## ISO 12354-2:2017, Tabla G.6 (fila mal etiquetada)

- **Ubicación:** Anexo G, Tabla G.6 (p. 40 impresa), unión rígida en cruz de
  pared interior con suelo separador.
- **El impreso:** una fila etiquetada «Ext. wall 1/2 – Int. wall 1/2» con
  `m'i` = 360,0, `m'orthogonal` = 484,0 y $K_{ij} = 11{,}0\ \text{dB}$.
- **El problema:** la Tabla G.6 describe la unión en cruz de *pared interior
  con suelo separador*; ninguna pared exterior concurre en ella. Las masas y
  el valor son los de la trayectoria en línea de la pared interior, y la
  Tabla L.6 de ISO 12354-1:2017 imprime la misma fila correctamente como
  «Int. wall 1/2 - Int. wall 1/2».
- **Evidencia:** la rama pasante de la cruz rígida
  $8{,}7 + 17{,}1 M + 5{,}7 M^2$ con $M = \log_{10}(484/360)$ da 10,99, el
  11,0 impreso, para la pared interior. Verificado en la página 46 del PDF
  (p. 40 impresa) de ISO 12354-2:2017 y la página 89 del PDF (p. 83 impresa)
  de ISO 12354-1:2017.
- **Comportamiento de la biblioteca:** trata la fila como la trayectoria en
  línea de la pared interior.
- **Estado:** sin notificar.

## ISO 12354-1:2017 Tabla L.10 / ISO 12354-2:2017 Tabla G.10 (etiqueta de elemento)

- **Ubicación:** la tabla de datos de entrada del modelo simplificado de
  ambas partes, cuarta fila: Tabla L.10 (p. 84 impresa) y Tabla G.10 (p. 41
  impresa).
- **El impreso:** ISO 12354-1 imprime «Internal wall 4 (F = f = 4)»;
  ISO 12354-2 imprime «Internal wall 4 (f4)»: las dos partes etiquetan la
  fila de forma distinta, y una revisión anterior de esta entrada citaba la
  forma de la Parte 1 para ambas.
- **El problema:** el ejemplo tiene dos paredes interiores; el elemento de
  índice $F = f = 4$ es la pared interior **2**
  ($5{,}00\ \text{m} \times 2{,}75\ \text{m}$, $S = 13{,}75\ \text{m}^2$),
  como la etiquetan las tablas del modelo detallado de los mismos anexos.
- **Evidencia:** los propios $S = 13{,}75\ \text{m}^2$ y
  $l_{ij} = 5{,}0\ \text{m}$ de la fila casan con la pared interior 2 de la
  Tabla L.1 / G.1. Verificado en la página 90 del PDF (p. 84 impresa) de
  ISO 12354-1:2017 y en la página 47 del PDF (p. 41 impresa) de
  ISO 12354-2:2017, con las etiquetas de columna del modelo detallado leídas
  en la página 85 del PDF (p. 79 impresa) de ISO 12354-1:2017 y en la página
  42 del PDF (p. 36 impresa) de ISO 12354-2:2017.
- **Comportamiento de la biblioteca:** no hizo falta ninguno; los números no
  se ven afectados.
- **Estado:** sin notificar.

## ISO 12354-1:2017, Tabla D.1 (1 600 Hz cubierto por dos filas)

- **Ubicación:** Anexo D, Tabla D.1 (p. 39 impresa), en la que se lee la
  mejora del índice global de reducción sonora de un revestimiento interior a
  partir de su frecuencia de resonancia.
- **El impreso:** las dos últimas filas son «630 to 1 600 -> -10» y «1 600 <=
  f0 <= 5 000 -> -5».
- **El problema:** 1 600 Hz pertenece a ambas filas, con valores distintos, y
  el apartado D.2.2 exige que $f_0$ sea «rounded to the centre frequency of
  the one-third-octave band in which fo falls», así que 1 600 Hz es un valor
  en el que la tabla se lee de verdad y no un borde inalcanzable. Como el
  redondeo es obligatorio, la ambigüedad no es un punto único: toda
  frecuencia de resonancia bruta de la banda de 1 600 Hz, es decir de
  1 412,5 Hz a 1 778,3 Hz (bordes de banda de ISO 266), cae en él. Todos los
  demás límites de la tabla son centros de banda distintos (200, 250, 315,
  400, 500 Hz), y ningún otro par de filas se solapa.
- **Evidencia:** la propia tabla impresa, en la página 45 del PDF (p. 39
  impresa) de ISO 12354-1:2017: las dos filas van regladas por separado y
  comparten el extremo al pie de la letra, «630 to 1 600» y «1 600 <= f0 <=
  5 000». Ninguna de las dos filas puede descartarse, porque de 630 Hz a
  1 250 Hz no hay otra entrada y de 2 000 Hz a 5 000 Hz tampoco. La edición
  predecesora da la lectura anterior, sin ambigüedad: la Tabla D.3 de
  EN 12354-1:2000, verificada en la página 43 del PDF (p. 41 impresa) de esa
  edición, imprime el mismo par de filas como «630 - 1 600 -> -10» y
  «> 1 600 -> -5», estrictamente mayor, así que en 2000 exactamente 1 600 Hz
  tomaba -10 dB sin nada que decidir. La reescritura de 2017 sustituyó
  «> 1 600» por «1 600 <= f0 <= 5 000» dejando «630 to 1 600» intacto, que es
  lo que crea el solape; qué pretendía la reescritura en el extremo
  compartido, el texto no lo dice.
- **Comportamiento de la biblioteca:** `weighted_lining_improvement` devuelve
  los -10 dB más conservadores exactamente a 1 600 Hz y -5 dB por encima, la
  lectura de 2000, con la ambigüedad nombrada en el docstring y fijada en
  [`tests/building/prediction/test_resilient_layers.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_resilient_layers.py).
- **Estado:** sin notificar.

- **Relacionado, no una errata:** la NOTA 1 de la misma tabla pone un suelo
  de 0 dB a la rama de 30 Hz a 160 Hz,
  $74{,}4 - 20\log_{10}(f_0) - R_w/2$. Dentro de la caja de validez que el
  apartado D.2.2 declara para la tabla
  ($30\ \text{Hz} \le f_0 \le 160\ \text{Hz}$,
  $20\ \text{dB} \le R_w \le 60\ \text{dB}$) la rama nunca lo alcanza: su
  mínimo es $74{,}4 - 20\log_{10}(160) - 60/2 = 0{,}32\ \text{dB}$. El suelo
  es por tanto inactivo para toda entrada declarada de la tabla, pero no
  siempre lo fue: la edición de 2000 tabulaba la rama baja como cuatro filas
  discretas que terminaban en «160 -> 28 - Rw/2», cuyo mínimo es
  $28 - 60/2 = -2\ \text{dB}$, así que la NOTA 1 operaba allí. El ajuste
  continuo de 2017 queda 2,3 dB por encima en esa esquina y dejó la nota
  vestigial. La biblioteca conserva el suelo porque la nota sigue impresa.

## ISO 15186-1, apartado 3.9, Fórmula (8) (signo del término 10 lg N)

- **Ubicación:** apartado 3.9, Fórmula (8) (p. 3 impresa), la diferencia de
  niveles normalizada de elemento por intensidad para N elementos pequeños de
  edificación medidos juntos. El impreso leído aquí es
  **BS EN ISO 15186-1:2003**, la adopción británica de texto idéntico; la
  entrada llevaba antes el encabezado «:2000», el año de la edición ISO que
  citan los docstrings de la biblioteca, que no es la copia que se leyó.
- **El impreso:**
  $D_{I,n,e} = L_{p1} - 6 - (L_{In} + 10 \lg(S_m/A_0) + 10 \lg(N))$, es
  decir, el término $10 \lg N$ se resta.
- **El problema:** el signo restado no puede deducirse. Medir $N$ unidades
  idénticas dentro de una superficie de medición eleva la potencia
  transmitida (y con ella $L_{In} + 10\log_{10} S_m$) en $10\log_{10} N$, así
  que recuperar el $D_{I,n,e}$ por unidad exige *sumar* $10\log_{10} N$. El
  equivalente en presión, la Fórmula (6) de ISO 10140-2:2010, imprime
  exactamente esa corrección
  ($D_{n,e} = L_1 - L_2 + 10\log_{10}(nA_0/A)$), y la Fórmula (12) de
  ISO 15186-2:2010 imprime la Fórmula (8) sin término alguno de $N$ (el caso
  $N = 1$, con el que ambos signos concuerdan). Tal como está impreso,
  instalar más unidades *bajaría* el índice por unidad en $20\log_{10} N$
  respecto al valor deducible.
- **Evidencia:** deducción desde la relación de sala receptora de campo
  difuso $L_2 = L_W + 10\log_{10}(4/A)$ contra la Fórmula (6) de
  ISO 10140-2:2010; contraste con la Fórmula (12) de ISO 15186-2:2010 y
  Hopkins, *Sound Insulation* (2007), Ec. 3.45. Verificado en la página 11
  del PDF (p. 3 impresa) de BS EN ISO 15186-1:2003, con el contraste leído en
  la página 11 del PDF (p. 11 impresa) de ISO 10140-2:2010. **La parte 3 de la
  propia serie lo zanja:** la ISO 15186-3:2002, apartado 3.9, Fórmula (8),
  enuncia la misma magnitud como
  $D_{I,n,e} = L_{pS} - 9 - [L_{In} - 10 \lg(A_0/S_m) - 10 \lg N]$, cuyo
  corchete lleva el $10 \lg N$ con el signo exterior contrario, es decir el
  $+10\log_{10} N$ que aquí se deduce. Leído en la página 10 del PDF (p. 4
  impresa) de BS EN ISO 15186-3:2010.
- **Comportamiento de la biblioteca:** implementa la forma por unidad
  deducible (`intensity_element_normalized_difference`, $+10\log_{10} N$) y
  emite un aviso siempre que $n > 1$, donde el resultado se desvía del
  impreso.
- **Estado:** sin notificar.

## ISO 15186-3:2002, anexo A, Tabla A.1 (la columna del sándwich de acero no se reproduce con sus propios datos)

- **Ubicación:** anexo A (normativo), A.2 y Tabla A.1, «Calculated sound
  reduction index (at 1 013 hPa and 23 °C)», el ejemplo de calificación con
  el que un laboratorio comprueba su instalación. El ejemplar leído es **BS EN
  ISO 15186-3:2010**, la adopción británica de texto idéntico de la ISO
  15186-3:2002, página 18 del PDF (p. 12 impresa).
- **El impreso:** dos columnas de seis valores en tercios de octava, de 50 Hz
  a 160 Hz. La columna del cartón-yeso va encabezada por «10 kg/m²» sobre un
  «Test opening 10 m²» y da 10,7 / 11,9 / 13,4 / 14,8 / 16,3 / 17,9. La del
  acero va encabezada por «17 kg/m²» sobre un «Test opening 1,25 m × 1,50 m» y
  da 21,3 / 21,2 / 21,7 / 22,7 / 23,8 / 25,1. A.2 añade que «the dimensions of
  the free part of the panel are 1,162 m × 1,412 m».
- **El problema:** ninguna lectura de los datos impresos junto a la columna del
  acero la reproduce. Con el hueco de ensayo (1,875 m²) y la masa declarada,
  los seis valores calculados quedan entre 1,27 dB y 0,72 dB por debajo de los
  impresos. Esa dispersión de 0,55 dB entre ambos extremos descarta cualquier
  masa superficial con esa área, porque un error de masa desplaza
  $R_0 = 20 \lg(\pi f m / \rho c)$ lo mismo en todas las bandas. Con la parte
  libre del panel (1,640744 m²) el residuo queda casi plano, de media
  0,562 dB, pero aun así se abre 0,102 dB de un extremo a otro, que es el ancho
  entero del decimal impreso, así que tampoco es el desplazamiento constante
  que dejaría una masa equivocada por sí sola.

  Ningún dato aislado la cierra dentro de los 0,05 dB que admite una impresión
  de un decimal. La mejor masa superficial sola, sobre la parte libre, es
  18,13 kg/m² y deja 0,051 dB; la mejor presión estática sola son 950 hPa y
  deja 0,051 dB; la mejor temperatura sola, sobre el hueco de ensayo, son 63 °C
  y deja 0,052 dB. Las dos últimas contradicen el encabezado, que fija el clima
  en 1 013 hPa y 23 °C, y la columna del cartón-yeso sí se reproduce justo con
  ese clima, así que las dos columnas no pueden leerse con climas distintos.

  La única lectura que sí reproduce los seis valores mueve dos datos a la vez:
  un área de unos 1,654 m², cercana a la parte libre pero no igual a ella,
  junto con una masa superficial de unos 18,16 kg/m². Esa masa no está al
  alcance de la probeta descrita. El acero macizo de 2,2 mm da entre
  16,9 kg/m² y 17,3 kg/m², y la hoja es un sándwich acero/resina/acero, así que
  su masa superficial queda por fuerza por debajo. La columna del cartón-yeso
  de esa misma tabla, con las mismas fórmulas y el mismo clima, reproduce sus
  seis valores dentro de 0,050 dB.
- **Evidencia:** Fórmulas (A.1) a (A.5) evaluadas a los 1 013 hPa y 23 °C
  declarados, leídas en las páginas 17 y 18 del PDF (pp. 11 y 12 impresas) de
  BS EN ISO 15186-3:2010. La ISO 140-3:1995, C.2.4, que A.2 cita como origen de
  la probeta, describe la hoja de acero/resina/acero de 2,2 mm pero no declara
  masa superficial alguna, así que los 17 kg/m² no vienen de ahí. No consta
  corrigendum al anexo A.
- **Comportamiento de la biblioteca:** `limp_panel_reduction_index` implementa
  las Fórmulas (A.1) a (A.5) tal como se imprimen. La suite de conformidad las
  ancla solo en la columna del cartón-yeso; la del acero no se usa como
  oráculo a propósito.
- **Estado:** sin notificar.

## ISO 10848-1:2006, apartado 8.1.1, Fórmula (20) (π espurio en la frecuencia crítica)

- **Ubicación:** apartado 8.1.1, Fórmula (20), la frecuencia crítica de placa
  delgada que usa el criterio de flancos de la instalación de ensayo de la
  Fórmula (19).
- **El impreso:** $f_c = c_0^{2} / (1{,}8\ c_L \cdot h \cdot \pi)$.
- **El problema:** la constante 1,8 es ya el
  $2\pi/\sqrt{12} \approx 1{,}814$ redondeado de la relación de dispersión de
  placa delgada, así que el $\pi$ extra la cuenta dos veces y desplazaría
  $f_c$ en un factor $\pi$ (p. ej. un elemento de hormigón de 100 mm con
  $c_L = 3500\ \text{m/s}$: 187 Hz sin el $\pi$, 59 Hz con él, lejos de
  cualquier caída medida en la coincidencia).
- **Evidencia:** deducción desde la relación de dispersión de placa delgada
  (Hopkins, *Sound Insulation* (2007), Ec. 2.201,
  $f_c = c_0^2/(1{,}8 c_L h)$); ISO 12354-1:2017 imprime la misma forma sin
  $\pi$ en sus definiciones de símbolos ($f_c = c_0^2/(1{,}8 c_L t)$).
- **Comportamiento de la biblioteca:** implementa la forma sin $\pi$
  (`phonometry.building.measurement.flanking_transmission.critical_frequency`),
  con una nota de errata en el docstring.
- **Estado:** corregido aguas arriba. ISO 10848-1:2017 (segunda edición)
  imprime la forma sin $\pi$ en su Fórmula (5),
  $f_c = c_0^2/(1{,}8 h c_L)$, confirmando el impreso de 2006 como errata. No
  hace falta notificación. La entrada se conserva porque la biblioteca cita
  la edición de 2006, cuyo impreso lleva el defecto; la edición de 2017 queda
  como confirmación.

## ISO 10846-2:2008, 7.6.1 (el ensayo previo de unidireccionalidad remite al 6.1, Desigualdad (1))

- **Ubicación:** apartado 7.6.1, «General», el párrafo del ensayo previo que
  comprueba la dirección del movimiento de entrada.
- **El impreso:** «A further pre-run shall be performed to check that the
  acceleration in the excitation direction exceeds the acceleration in other
  directions. Measurement results, which do not meet the condition of **6.1,
  Inequality (1)**, shall be excluded from the evaluation of the dynamic
  stiffness function.»
- **El problema:** la Desigualdad (1) del 6.1 es la condición de salida
  bloqueada, $\Delta L_{1,2} = L_{a1} - L_{a2} \geqslant 20$ dB, una
  diferencia de niveles entre el lado de entrada y el de salida, que una
  comprobación de las direcciones en la entrada no puede ensayar. La condición
  que ensaya el ensayo previo es la del 6.4, «Unwanted input vibrations»,
  Desigualdad (3),
  $L_{a(\mathrm{excitation})} - L_{a(\mathrm{unwanted})} \geqslant 15$ dB.
  La misma frase en las partes hermanas remite a su propio apartado de
  entradas no deseadas: la ISO 10846-3:2002 7.5.1 al 6.4, la ISO
  10846-4:2003 7.6.1 al 6.5 y la ISO 10846-5:2008 7.6.1 a su Desigualdad (2).
  Seguida tal como está impresa, la frase excluye las líneas en las que la
  salida no está bloqueada y conserva aquellas en las que la entrada se mueve
  en la dirección equivocada.
- **Evidencia:** la referencia leída frente a los apartados a los que puede
  remitir. Verificado en la página 24 del PDF (p. 16 impresa, 7.6.1), la
  página 20 del PDF (p. 12 impresa, 6.1) y la página 21 del PDF (p. 13
  impresa, 6.4) de BS EN ISO 10846-2:2008, la implementación británica de
  ISO 10846-2:2008 (segunda edición); las frases hermanas en la página 33
  del PDF (p. 23 impresa) de BS EN ISO 10846-3:2002, la página 36 del PDF
  (p. 26 impresa) de BS EN ISO 10846-4:2003 y la página 23 del PDF (p. 15
  impresa) de BS EN ISO 10846-5:2009.
- **Comportamiento de la biblioteca:** sigue el destino pretendido.
  `check_unwanted_input` juzga la unidireccionalidad de la Parte 2 con los
  15 dB de su Desigualdad (3), y `check_blocked_output` conserva los 20 dB de
  la Desigualdad (1) para el lado de salida. La referencia no cambia ningún
  número que informe la biblioteca.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## ISO 10846-4:2003, 6.2 NOTA 1 (la cota de la Desigualdad (3) impresa como 05 dB)

- **Ubicación:** apartado 6.2, «Measurement of blocking force in the direct
  method», NOTA 1 a la Desigualdad (3).
- **El impreso:** «Inequality (3) is equivalent to the requirement that
  $|L_{F_\mathrm{b}} - L_{F_2}| \leqslant 05$ dB.»
- **El problema:** falta la coma decimal: la cota es 0,5 dB, no 5 dB. La
  propia Desigualdad (3), $m_0 \leqslant 0{,}06 \times 10^{L_{F2}/20} /
  10^{L_{a2}/20}$ kg, limita la fuerza de inercia $m_0 a_2$ al 6 % de la
  fuerza medida, así que los dos niveles de fuerza difieren como mucho en
  $20\lg 1{,}06 = 0{,}51$ dB con la fuerza de inercia en fase y
  $-20\lg 0{,}94 = 0{,}54$ dB en oposición: 0,5 dB, la décima parte de lo que
  dice la nota. ISO 10846-2:2008, que enuncia la misma desigualdad para
  soportes resilientes (su Desigualdad (2)), imprime la misma nota con la coma
  en su sitio, «$L_{F_2'} - L_{F_2} \leqslant 0{,}5$ dB».
- **Evidencia:** la nota junto a la desigualdad que reformula, y la misma
  nota en la parte hermana. Verificado en la página 30 del PDF (p. 20
  impresa) de BS EN ISO 10846-4:2003, la implementación británica de ISO
  10846-4:2003 (primera edición), y en la página 21 del PDF (p. 13 impresa)
  de BS EN ISO 10846-2:2008.
- **Comportamiento de la biblioteca:** no hizo falta ningún cambio, porque la
  biblioteca calcula la desigualdad, no la nota. `check_output_mass` informa
  del sesgo que puede causar la masa, `bias_bound_db`, que es 0,54 dB sobre
  la cota, y la comprobación de conformidad «ISO 10846-4:2003 6.2 NOTE 1» lo
  contrasta con los 0,5 dB que la nota quiere decir.
- **Estado:** sin notificar.

## UNE-EN 15657:2018, apartado 7.1, Fórmula (14) (masa de referencia dimensionalmente inconsistente con la magnitud que normaliza)

- **Ubicación:** apartado 7.1, la frase que introduce la Fórmula (14) (p. 14
  impresa) y la propia Fórmula (14) (p. 15 impresa), el nivel de potencia
  estructural inyectado en la placa de recepción.
- **El impreso:** la frase lee «a partir del nivel de velocidad promediado
  espacialmente de la placa $L_v$, de la **masa por unidad de superficie**
  $m$, del área de la placa $S$ y del factor de pérdida $\eta$, utilizando
  $f_0 = 1$ Hz, $m_0 = 1$ kg y $S_0 = 1$ m² como referencias», sobre
  $L_{Ws} = \left(10\lg\left(\dfrac{2\pi f m \eta S}{f_0 \cdot m_0 \cdot S_0}\right)\right)\text{dB} + L_v - 60\ \text{dB}$.
- **El problema:** la misma frase define $m$ como una masa por unidad de
  superficie, en kg/m², y su referencia $m_0$ como 1 kg. Con $m$ en kg/m² y
  $S$ en m², el grupo $2\pi f\,\eta\,m\,S / (f_0 m_0 S_0)$ solo es
  adimensional si $m_0$ es 1 kg/m²; tal como está impreso arrastra un m⁻²
  suelto. La constante de cierre confirma la lectura pretendida:
  $10\lg(f_0 m_0 S_0 v_0^2 / P_0) = -60$ dB con $v_0 = 10^{-9}$ m/s y
  $P_0 = 1$ pW cierra en vatios solo cuando $f_0 m_0 S_0$ tiene las unidades
  de una densidad superficial por un área por una frecuencia. El resultado
  numérico no se ve afectado, porque $10\lg(1) = 0$ sea cual sea la unidad
  adjunta, que es por lo que el desliz sobrevive a un ejemplo resuelto.
- **Evidencia:** análisis dimensional de la Fórmula (14) contra la definición
  de $m$ en la frase que la precede, y contra la constante de $-60$ dB con la
  que cierra; la frase y la fórmula se leyeron como imágenes, no desde el
  texto extraído. Verificado en la página 14 del PDF (p. 14 impresa) y la
  página 15 del PDF (p. 15 impresa) de UNE-EN 15657:2018. Solo se leyó la
  adopción en español, así que esta entrada no establece si el impreso inglés
  de EN 15657:2018 lleva la misma referencia.
- **Comportamiento de la biblioteca:** no hizo falta ningún cambio.
  `characteristic_reception_plate_power` toma `mass_per_area` en kg/m² y
  reproduce los propios valores resueltos de la norma, así que la lectura
  pretendida es la implementada; la guía y el docstring conservan la
  referencia impresa y nombran esta entrada a su lado.
- **Estado:** sin notificar.

## ISO 12999-1:2020, Tabla 4 (falta la fila de 500 Hz)

- **Ubicación:** Tabla 4 (incertidumbres in situ por banda).
- **El impreso:** la tabla de la edición de 2020 omite la fila de 500 Hz que
  la edición de 2014 imprime (situación B 1,2 dB / situación C 0,8 dB).
- **El problema:** probable omisión editorial; las filas circundantes no
  cambian entre ediciones y el texto no menciona retirar la banda.
- **Evidencia:** comparación lado a lado de los impresos de 2014 y 2020.
- **Comportamiento de la biblioteca:** sigue el impreso de 2020 tal como está
  publicado, con la omisión documentada en el módulo.
- **Estado:** sin notificar.

## ISO 12999-2:2020, redacción del apartado 8 frente a las Tablas 4 y 5

- **Ubicación:** apartado 8 **«Reporting uncertainties»** (pp. 5-6 impresas),
  la lista de símbolos bajo la Fórmula (10), contra las Tablas 4 y 5
  resueltas (p. 7 impresa). Una revisión anterior de esta entrada llamaba al
  apartado «expression of results», que no es su título impreso.
- **El impreso:** la lista de símbolos define $u$ como «the standard
  uncertainty determined in accordance with Clause 5, Clause 6 or Clause 7
  **rounded to two decimal digits for absorption coefficients** or one
  decimal digit for all other quantities», y la Fórmula (10) forma después
  $U = k \cdot u$.
- **El problema:** las propias Tablas 4 y 5 del documento solo se reproducen
  cuando $U$ se calcula desde el $u$ sin redondear y se redondea al final.
  Ninguna de las dos tablas imprime columna alguna de $u$ (cada una lleva
  solo el coeficiente $\alpha_s$ o $\alpha_p$ y $\pm U$ con $k = 2$), así que
  los valores impresos de $U$ son toda la evidencia, y 11 de los 25 son
  inalcanzables bajo la redacción literal del apartado.
- **Evidencia:** recálculo de las 25 entradas (Tabla 4: 20 filas, Tabla 5: 5
  filas) desde la Fórmula (1) con las constantes de la Tabla 1 y desde la
  Fórmula (4) con las constantes de la Tabla 2, bajo ambos convenios.
  Redondear al final reproduce 25 de 25; redondear primero falla 11 de 25
  (63, 125, 160, 200, 250, 1250, 1600, 2000, 3150 y 4000 Hz de la Tabla 4, y
  250 Hz de la Tabla 5). Una revisión anterior de esta entrada citaba el
  recuento como «10 de 20», que no es ni el numerador correcto ni el número
  correcto de entradas. Verificado en las páginas 9 (p. 3 impresa), 10 (p. 4
  impresa), 11 (p. 5 impresa) y 13 (p. 7 impresa) del PDF de
  ISO 12999-2:2020.
- **Comportamiento de la biblioteca:** redondea al final, casando con las
  tablas; el convenio está documentado y probado.
- **Estado:** sin notificar.

## ISO 12999-2:2020, Tabla 5 (datos de banda de octava bajo un encabezado de tercio de octava)

- **Ubicación:** apartado 8, Tabla 5 «Example for the practical sound
  absorption coefficient, αp, and its expanded uncertainty under
  reproducibility conditions» (p. 7 impresa).
- **El impreso:** la columna de frecuencias de la Tabla 5 se encabeza
  **«One-third octave midband frequency / Hz»** y sus filas son 250, 500,
  1 000, 2 000 y 4 000 Hz.
- **El problema:** esas cinco frecuencias son la serie de bandas de
  **octava** de ISO 11654, que es sobre la que se define el coeficiente de
  absorción sonora práctico $\alpha_p$; no son una serie de tercios de
  octava, y entre ellas no falta ningún tercio de octava. El documento se
  contradice sobre la misma magnitud dos páginas antes: la Tabla 2, que
  aporta las constantes $m$ y $n$ de la Fórmula (4) para exactamente estas
  cinco frecuencias, se encabeza «Octave midband frequency». El mismo texto
  de encabezado figura sobre la Tabla 4 de la misma página, donde es
  correcto: esa tabla lleva una serie genuina de tercios de octava, de 63 Hz
  a 5 000 Hz en 20 filas.
- **Evidencia:** las cinco frecuencias tabuladas mismas, y el encabezado
  «Octave midband frequency» de la Tabla 2 para las mismas constantes de
  $\alpha_p$. Verificado en la página 13 del PDF (p. 7 impresa) y la página
  11 del PDF (p. 5 impresa) de ISO 12999-2:2020.
- **Comportamiento de la biblioteca:** `_TABLE2` en
  [`uncertainty.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/uncertainty.py)
  está indexada por frecuencia central de *octava*, siguiendo la Tabla 2 y la
  definición de $\alpha_p$ de ISO 11654 y no el encabezado de la Tabla 5.
- **Estado:** sin notificar.

## ISO 10052:2021, encabezado del rango de volúmenes de la Tabla 4

- **Ubicación:** Tabla 4 (estimador del índice de reverberación), encabezado
  del rango de volúmenes.
- **El impreso:** el encabezado lee «60 ≤ V < 150» mientras que el cuerpo del
  texto dice que el método se aplica a salas «up to 150 m³».
- **El problema:** el límite $V = 150\ \text{m}^3$ queda incluido por el
  texto y excluido por el encabezado.
- **Evidencia:** comparación directa del encabezado y el texto del apartado.
- **Comportamiento de la biblioteca:** acepta $V = 150$ (sigue el texto), con
  la ambigüedad anotada.
- **Estado:** sin notificar.

## ISO 16283-1:2014, apartado 6 (un tiempo de reverberación de la sala emisora)

- **Ubicación:** apartado 6 «General», el párrafo sobre el tiempo de
  reverberación (p. 6 impresa).
- **El impreso:** «For the reverberation time, the low-frequency procedure
  shall be used for the 50 Hz, 63 Hz, and 80 Hz one-third octave bands in
  **the source and/or receiving room** when its volume is smaller than 25 m³
  (calculated to the nearest cubic metre).»
- **El problema:** ISO 16283-1 no mide ningún tiempo de reverberación de la
  sala emisora, así que no hay nada en la sala emisora a lo que aplicar un
  procedimiento de tiempo de reverberación. El primer párrafo del mismo
  apartado, cinco párrafos y una NOTA antes, lista las mediciones requeridas
  como «the sound pressure levels in both rooms with the source(s) operating,
  the background noise in the receiving room ... and the reverberation times
  **in the receiving room**». El apartado 10, que es donde de verdad se
  especifican los procedimientos de tiempo de reverberación, dice lo mismo
  cuatro veces: su título es «Reverberation time **in the receiving room**
  (default and low-frequency procedure)», su apartado 10.1 acota todo el
  apartado a «the receiving room», su apartado 10.3 bifurca según si «the
  receiving room has a volume larger than or equal to 25 m³», y su apartado
  10.4 aplica el procedimiento de baja frecuencia «when **the receiving
  room** volume is smaller than 25 m³». La locución es correcta dos párrafos
  más arriba, uno de ellos la NOTA, donde le corresponde: el *nivel de
  presión sonora* sí se mide en ambas salas y su procedimiento de baja
  frecuencia sí aplica a cualquiera de las dos. Se arrastró hasta la frase
  del tiempo de reverberación, donde solo existe una sala. Las otras dos
  partes imprimen la misma frase con una sola sala: el apartado 6 de
  ISO 16283-2:2020 y el apartado 6 de ISO 16283-3:2016 leen ambos «in the
  receiving room when its volume is smaller than 25 m³», así que la Parte 1
  es la discrepante de las tres.
- **Evidencia:** la frase en la página 12 del PDF (p. 6 impresa) de
  ISO 16283-1:2014, idéntica en la página 14 del PDF (p. 6 impresa) de
  BS EN ISO 16283-1:2014; el apartado 10 y sus subapartados en las páginas 23
  y 24 del PDF (pp. 17 y 18 impresas) del mismo documento; y la versión de
  una sola sala de la frase en la página 13 del PDF (p. 7 impresa) de
  ISO 16283-2:2020 y la página 16 del PDF (p. 10 impresa) de
  ISO 16283-3:2016.
- **Comportamiento de la biblioteca:** la sustitución por la octava de 63 Hz
  es una operación de sala receptora en todas las partes, siguiendo el
  apartado 10; un procedimiento de sala emisora que lleve un tiempo de
  reverberación de la octava de 63 Hz se rechaza, y una llamada de sala
  emisora no toma tiempo de reverberación alguno. El procedimiento de esquina
  para el *nivel*, que es el párrafo al que pertenece la locución, sí admite
  ambas salas en ISO 16283-1 y el punto de entrada aéreo ofrece ambas.
- **Estado:** sin notificar.

## ISO 16283-2:2020, apartado 8.3 (una sala emisora en una medición de impacto)

- **Ubicación:** apartado 8.3 «Microphone positions», último párrafo (p. 15
  impresa).
- **El impreso:** «For the 50 Hz, 63 Hz and 80 Hz one-third octave bands,
  calculate the low-frequency energy-average sound pressure level **for the
  source and/or receiving room** according to 8.5.»
- **El problema:** una medición de impacto no tiene nivel de presión sonora
  de sala emisora que calcular. Todas las demás formulaciones del mismo
  procedimiento en la misma parte nombran una sola sala: el apartado 6 lo
  introduce como usado «in the receiving room when its volume is smaller than
  25 m³» (p. 6 impresa), el apartado 8.1 repite «in the receiving room»
  (p. 14 impresa), el apartado 8.5 construye $L_\text{i,Corner}$ desde
  esquinas de la sala receptora (p. 16 impresa), y las Fórmulas (1) y (3), a
  las que la misma frase remite al lector, están escritas en $L_\text{i}$, el
  nivel de presión sonora de impacto promedio energético en la sala
  receptora. La locución es correcta allí de donde viene: el apartado 8.3 de
  ISO 16283-1 dice «for the source and/or receiving room» de una medición
  aérea, donde ambas salas sí llevan un nivel. Se copió a la parte de impacto
  y sobrevivió a la revisión sin cambios.
- **Evidencia:** la frase en la página 21 del PDF (p. 15 impresa) de
  ISO 16283-2:2020 junto a la misma frase en la página 23 del PDF (p. 15
  impresa) del texto ISO/DIS 16283-2 circulado como BSI DPC 13/30269186 DC, y
  el original aéreo en la página 21 del PDF (p. 15 impresa) de
  ISO 16283-1:2014.
- **Comportamiento de la biblioteca:** el punto de entrada de impacto toma un
  procedimiento de baja frecuencia de sala receptora y nada más, siguiendo
  los apartados 6, 8.1 y 8.5; solo el punto de entrada aéreo, donde el
  apartado 8.1 de ISO 16283-1 sí admite ambas salas, ofrece uno de sala
  emisora.
- **Estado:** sin notificar.

## ISO 16283-2:2020, apartado 10.3 (una sala receptora de exactamente 25 m³)

- **Ubicación:** apartado 10.3 «Default procedure» del tiempo de
  reverberación (p. 18 impresa).
- **El impreso:** «for all one-third octave bands between 50 Hz and 5 000 Hz
  when the receiving room has a volume **larger than** 25 m³ (calculated to
  the nearest cubic metre) and between 100 Hz and 5 000 Hz when the receiving
  room has a volume smaller than 25 m³ (calculated to the nearest cubic
  metre)».
- **El problema:** una sala receptora que redondea a exactamente 25 m³ no cae
  en ninguna de las dos ramas, así que el apartado no declara rango de
  frecuencias para ella. Las otras dos partes imprimen «larger than **or
  equal to** 25 m³» en la frase por lo demás idéntica, que cierra el límite.
  La lectura pretendida no está en duda: el disparador de los apartados 8.1 y
  10.4 es «smaller than 25 m³» en las tres partes, así que 25 m³ pertenece a
  la rama mayor y toma el rango por defecto completo de 50 Hz a 5 000 Hz.
- **Evidencia:** página 24 del PDF (p. 18 impresa) de ISO 16283-2:2020,
  contra la página 24 del PDF (p. 18 impresa) de ISO 16283-1:2014 y la página
  24 del PDF (p. 18 impresa) de ISO 16283-3:2016, que llevan ambas el «or
  equal to». El hueco no es un desliz de 2020 ni un artefacto de un borrador:
  el texto ISO/DIS en la página 26 del PDF (p. 18 impresa) de
  BSI DPC 13/30269186 DC ya leía igual, y también la edición anterior
  publicada, cuyo apartado 10.3 en la página 25 del PDF (p. 25 impresa) de
  UNE-EN ISO 16283-2:2016, la traducción española de ISO 16283-2:2015, lee
  «un volumen **superior a** 25 m³» sin «o igual a». La redacción ha
  permanecido sin cambios a través de dos ediciones y una revisión.
- **Comportamiento de la biblioteca:** el predicado disparador es el
  «smaller than 25 m³» estricto que comparten las tres partes, así que una
  sala de exactamente 25 m³ toma el procedimiento por defecto en todas las
  partes y no existe hueco.
- **Estado:** sin notificar.

## ISO 17208-2:2019, cobertura de bandas de la incertidumbre del apartado 5

- **Ubicación:** apartado 5 (incertidumbres expandidas representativas), p. 4
  impresa.
- **El impreso:** «5 dB for the low frequency (10 Hz to 100 Hz) bands, 3 dB
  for the mid frequency (125 Hz to 16 000 Hz) bands, and 4 dB for the high
  frequency (**>20 000 Hz**) bands».
- **El problema:** la propia banda de tercio de octava de 20 kHz queda sin
  asignar: el rango medio termina en 16 kHz *inclusive* y el rango alto
  empieza estrictamente por encima de 20 kHz. ISO 17208-1:2016, de la que el
  apartado 5 dice tomar los valores, imprime los mismos tres rangos con
  «**≥20 000 Hz**», que cierra el hueco; la Parte 2 degradó el $\ge$ a un
  $>$. La banda de 20 kHz no es un caso límite para este documento: la Tabla
  1 de ISO 17208-1 exige que la medición cubra «20 000 Hz (minimum)» como su
  banda de tercio de octava superior. Una revisión anterior de esta entrada
  decía «nada cubre de 16 kHz a 20 kHz inclusive», que está mal por el
  extremo inferior: 16 kHz sí está cubierto.
- **Evidencia:** los dos apartados lado a lado. Verificado en la página 10
  del PDF (p. 4 impresa) de ISO 17208-2:2019 y la página 22 del PDF (p. 16
  impresa) de ISO 17208-1:2016.
- **Comportamiento de la biblioteca:** aplica el valor conservador de 4 dB de
  la banda alta desde la banda de 20 kHz hacia arriba, siguiendo la Parte 1,
  con el hueco documentado.
- **Estado:** sin notificar.

## ECMA-418-1:2024 (3.ª edición), NOTA 2 del apartado 4.1.1 (límite superior del rango de tonos discretos)

- **Ubicación:** apartado **4.1.1** «frequency range of interest», NOTA 2
  (p. 2 impresa). Una revisión anterior de esta entrada citaba el apartado
  4.1.2, que es la definición de «ITT equipment» y no dice nada de
  frecuencias.
- **El impreso:** «From viewpoint of test implementation by using FFT
  analyser, the frequency range of discrete tones are between 89,1 Hz and
  11 220 Hz inclusive, referred to *the discrete tone frequency range of
  interest*.»
- **El problema:** todas las fórmulas y tablas de la norma trabajan hasta
  11 200 Hz: los ajustes de bordes de banda de las Tablas 2 y 3 se declaran
  para $11\,200 \ge f_t > 1\,600$, y los apartados 10, 12.3 y 12.4 permiten
  datos FFT con $f_1 < 89{,}1\ \text{Hz}$ y $f_2 > 11\,200\ \text{Hz}$. Los
  dos números son la misma cantidad a distinta precisión y no un error
  tipográfico: $10\,000 \cdot 2^{1/6} = 11\,224{,}6\ \text{Hz}$ es el borde
  superior de la banda de tercio de octava de 10 kHz que cierra el rango de
  interés, que redondea a 11 220 Hz con cuatro cifras significativas y a
  11 200 Hz con tres. Una revisión anterior de esta entrada lo llamaba errata
  y añadía que «ningún otro apartado menciona 11 220 Hz»; la última marca del
  eje x de la Figura 6 (p. 20 impresa) está etiquetada 11220. Lo que sí lleva
  el apartado 4.1 es un defecto estructural: 4.1.2 «ITT equipment» repite al
  pie de la letra la NOTA 1 de 4.1.1 («This range was selected to be
  identical to that of ECMA-74:2022, 3.1.3»), aunque 4.1.2 no define rango
  alguno, y el apartado 10 remite después a «NOTE 1 of 4.1.2» para el rango
  de tonos discretos, que es la nota duplicada y no la NOTA 2 que lo declara.
- **Evidencia:** la aritmética de arriba, y los rangos de las Tablas 2/3 y el
  eje de la Figura 6 leídos junto a la NOTA 2. Verificado en la página 10 del
  PDF (p. 2 impresa), la página 18 del PDF (p. 10 impresa), la página 25 del
  PDF (p. 17 impresa) y la página 28 del PDF (p. 20 impresa) de
  ECMA-418-1:2024 (3.ª edición).
- **Comportamiento de la biblioteca:** usa el rango internamente consistente
  de $89{,}1\ \text{Hz}$ a 11 200 Hz (extremo superior exclusivo según las
  fórmulas), con una nota en el código en
  [`tonality.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tonality.py).
- **Estado:** sin notificar.

## ECMA-418-1:2024 (3.ª edición), Fórmula (21) (término constante repetido)

- **Ubicación:** apartado 12.3, Fórmula (21) (p. 17 impresa), el ajuste de
  curva de la frecuencia del borde inferior $f_{1,L}$ de la banda crítica
  inferior.
- **El impreso:** $f_{1,L} = C_{L,0} + C_{L,0} f_t + C_{L,2} f_t^{2}$.
- **El problema:** el coeficiente lineal repite el término constante. La
  lista de símbolos inmediatamente debajo de la fórmula declara «$C_{L,0}$,
  $C_{L,1}$, $C_{L,2}$ are constants given in Table 2», la Tabla 2 tabula una
  columna $C_{L,1}$, y la Fórmula (22) paralela para el borde superior de
  banda imprime $f_{2,U} = C_{U,0} + C_{U,1} f_t + C_{U,2} f_t^{2}$
  correctamente. La errata es numéricamente fatal, no cosmética: en el rango
  de ajuste central ($171{,}4 \le f_t \le 1\,600$) la Tabla 2 da
  $C_{L,0} = -149{,}5$ y $C_{L,1} = 1{,}001$, así que la forma impresa
  devuelve $-149{,}5 - 149{,}5 f_t - 6{,}90 \cdot 10^{-5} f_t^2$, negativa en
  todas partes, en lugar de un borde de banda un poco por debajo de $f_t$.
- **Evidencia:** la fórmula, su propia lista de símbolos y la Tabla 2 en una
  misma página, con la Fórmula (22) como control consistente. Verificado en
  la página 25 del PDF (p. 17 impresa) de ECMA-418-1:2024 (3.ª edición).
- **Comportamiento de la biblioteca:** implementa la lectura con $C_{L,1}$,
  que es la única que devuelve un borde de banda usable, con una nota en el
  código en
  [`tonality.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tonality.py).
- **Estado:** sin notificar.

## ECMA-418-1:2024 (3.ª edición), apartado 11.3 (referencias de campo sin resolver)

- **Ubicación:** apartado 11.3 «Determination of masking noise level» (p. 12
  impresa), la frase que introduce el ancho de banda crítico.
- **El impreso:** «The critical bandwidth Δf_c is determined from Formula
  **Error! Reference source not found.Error! Reference source not found.**
  with f_0 set equal to the frequency of the discrete tone under
  investigation, f_t».
- **El problema:** dos referencias de campo de procesador de textos sin
  resolver quedaron compuestas, en negrita, en el lugar de los números de
  fórmula, y salieron publicadas en la tercera edición. Los destinos
  pretendidos son inequívocos por el resto de la frase, que pasa a nombrar
  las Fórmulas (4) y (5) o (7) y (8) para los bordes de banda: el ancho de
  banda crítico mismo es la Fórmula (2), y la Fórmula (3) es la relación
  $f_2 - f_1 = \Delta f_c$ que lo convierte en bordes de banda.
- **Evidencia:** el apartado tal como está impreso. Verificado en la página
  20 del PDF (p. 12 impresa), la página 18 del PDF (p. 10 impresa) y la
  página 30 del PDF (p. 22 impresa) de ECMA-418-1:2024 (3.ª edición).
- **Comportamiento de la biblioteca:** no hizo falta ninguno; la biblioteca
  implementa el ancho de banda crítico desde las Fórmulas (3)/(6)
  directamente.
- **Estado:** sin notificar.

## ECMA-418-2:2025 (4.ª edición), apartado 5.1.5.2 (índice del último bloque)

- **Ubicación:** apartado 5.1.5.2, la segmentación de la señal rellenada con
  ceros para los tamaños de bloque de aspereza/intensidad de fluctuación.
- **El impreso:** el índice del último bloque se da como
  $l_\text{last} = \lceil (n + s_b)/s_h \rceil$.
- **El problema:** la fórmula es internamente inconsistente: los bloques
  colocados en ese índice desbordan la señal rellenada con ceros que define
  el apartado 5.1.2.2, y la rejilla temporal resultante de la Fórmula (103)
  deja de ser monótona. La única lectura autoconsistente es detenerse en el
  último bloque que cabe dentro de la señal rellenada y alinearlo a ras con
  su final.
- **Evidencia:** evaluación directa de los índices de comienzo de bloque
  contra la longitud rellenada para los tamaños de bloque/salto del apartado
  7.1.1; la lectura a ras del final reproduce la calibración de aspereza del
  apartado 7 ($1\ \text{asper}$) a $0{,}9999$.
- **Comportamiento de la biblioteca:** implementa la lectura a ras del final
  con una nota en el código en
  [`roughness_ecma.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/roughness_ecma.py).
- **Estado:** sin notificar.

## ECMA-418-2:2025 (4.ª edición), apartado 9.1.4, Fórmula (127) (fase del núcleo HSA)

- **Ubicación:** apartado 9.1.4, Fórmula (127), el núcleo espectral de la
  ventana de análisis de envolvente que usa el High-resolution Spectral
  Analysis.
- **El impreso:** el factor de fase del núcleo es
  $\exp(-j \cdot 2\pi \cdot f_n(k) \cdot (\tilde{s}_b - n_{ze} + n_{zb} - 1))$.
- **El problema:** el núcleo es, por construcción, la DFT de la ventana de
  análisis rectangular de la Fórmula (120) modulada a la tasa candidata; ese
  es el modelo que la Fórmula (124) ajusta al espectro DFT medido. Esa DFT
  tiene la fase
  $\exp(-j \cdot \pi \cdot f_n \cdot (\tilde{s}_b - n_{ze} + n_{zb} - 1))$;
  el factor impreso la duplica (y es además inconsistente con los argumentos
  en $\pi$ de los términos seno impresos de la misma fórmula). Con la fase
  impresa el modelo ajustado no puede reproducir el espectro de una sinusoide
  enventanada sin ruido, contradiciendo la propia afirmación del apartado de
  que el HSA alcanza «theoretically infinite resolution for signals without
  noise».
- **Evidencia:** deducción independiente de la DFT de la ventana más
  recálculo numérico: con $\pi$ el ajuste por mínimos cuadrados recupera la
  parte constante, las amplitudes y las fases de envolventes sintéticas sin
  ruido a precisión de máquina y el residuo de la Fórmula (135) se anula; con
  el $2\pi$ impreso el núcleo se desvía de la DFT de la ventana en cantidades
  del orden del propio núcleo y el residuo se queda del orden de la energía
  de la señal.
- **Comportamiento de la biblioteca:** implementa la lectura con $\pi$,
  fijada por un test de regresión sobre la recuperación exacta de pares de
  líneas sintéticos.
- **Estado:** sin notificar.

## ECMA-418-2:2025 (4.ª edición), apartado 9.1.5, Fórmula (144) (desplazamiento de bin)

- **Ubicación:** apartado 9.1.5, Fórmula (144), la tasa de modulación de un
  máximo local del espectro de potencia de la envolvente.
- **El impreso:** la tasa es el centroide de tres bins ponderado por amplitud
  de la posición del pico **menos uno**, escalado por $\Delta f$.
- **El problema:** el apartado 9.1.4 (bajo la Fórmula (122)) define el índice
  espectral $k$ como el que mapea a la tasa de modulación
  $k \cdot \tilde{r}_s/\tilde{s}_b$ con $k$ empezando en 0. Un máximo local
  simétrico en el bin $k$ tiene centroide $k$, y la fórmula impresa le asigna
  entonces la tasa $(k - 1) \cdot \Delta f$, un bin entero
  ($0{,}73\ \text{Hz}$) por debajo, lo que a tasas de intensidad de
  fluctuación es fatal (una modulación verdadera de $1{,}46\ \text{Hz}$ se
  reportaría como $0{,}73\ \text{Hz}$). El desplazamiento solo es consistente
  con posiciones de línea espectral basadas en 1, contradiciendo la propia
  definición de $k$ de la norma.
- **Evidencia:** contraste de la Fórmula (144) contra el mapeo de $k$ a tasa
  declarado bajo la Fórmula (122).
- **Comportamiento de la biblioteca:** usa el centroide directamente (sin
  desplazamiento) con el $k$ basado en 0 de la Fórmula (122).
- **Estado:** sin notificar.

## ECMA-418-2:2025 (4.ª edición), apartado 9.1.7 (unidades de las constantes de ajuste fino)

- **Ubicación:** apartado 9.1.7, Fórmulas (149)-(152), el ajuste fino por
  Newton amortiguado de la tasa de modulación dominante.
- **El impreso:** paso diferencial $\Delta x = 10^{-5}$, tope del paso
  amortiguado $2 \cdot 10^{-4}$, tolerancia de parada $10^{-7}$ y un límite
  de 40 iteraciones, con el punto de partida
  $x_0 = \tilde{f}_{c,i_\text{max}}$ (una tasa en Hz) y la comprobación de
  fallo
  $|f_{c,1,\text{opt}} - \tilde{f}_{c,i_\text{max}}| > 1{,}25 \cdot \Delta f$.
- **El problema:** las constantes no llevan unidades. Leídas en Hz, el paso
  amortiguado queda topado a $5 \cdot 10^{-5}\ \text{Hz}$ por iteración
  ($2 \cdot 10^{-3}\ \text{Hz}$ en las 40 iteraciones), así que el ajuste no
  puede moverse apreciablemente y la comprobación de fallo de
  $1{,}25 \cdot \Delta f$ ($\approx 0{,}92\ \text{Hz}$) es inalcanzable; el
  apartado entero sería inerte. Leídas como tasas de modulación normalizadas
  $f/\tilde{r}_s$ (la variable en la que se expresan las frecuencias del
  núcleo de la Fórmula (127)), las mismas constantes dan un tope amortiguado
  por iteración de $0{,}075\ \text{Hz}$ ($\approx 2{,}9\ \text{Hz}$ en las 39
  iteraciones), una tolerancia de parada de
  $1{,}5 \cdot 10^{-4}\ \text{Hz}$ y una comprobación de fallo alcanzable,
  todo consistente con el propósito del apartado.
- **Evidencia:** análisis dimensional de las constantes impresas contra la
  resolución espectral de $0{,}7324\ \text{Hz}$ y el umbral de fallo.
- **Comportamiento de la biblioteca:** aplica las constantes como tasas de
  modulación normalizadas.
- **Estado:** sin notificar.

## ECMA-418-2:2025 (4.ª edición), introducción del apartado 9 (referencia cruzada rota)

- **Ubicación:** apartado 9, tercer párrafo de la introducción, sobre la
  predicción de sonoridad basada en HSA.
- **El impreso:** «loudness scaling is improved by using HSA-based loudness
  prediction (see Clause 0)».
- **El problema:** «Clause 0» no existe; el escalado de sonoridad basado en
  HSA se describe en el apartado 9.1.10 (una referencia de campo sin
  resolver).
- **Evidencia:** el propio índice de apartados de la norma.
- **Comportamiento de la biblioteca:** no hizo falta ninguno (el destino
  pretendido es inequívoco).
- **Estado:** sin notificar.

## ISO/PAS 20065:2016, apartado 5.3.4 (pendiente de los flancos de un tono destacado)

- **Ubicación:** apartado 5.3.4, Fórmulas (10)/(11) (p. 9 impresa), la
  pendiente mínima de los flancos de un tono destacado.
- **El impreso:** los dos flancos se escalan de forma distinta:
  $\Delta L_u = (f_T/2) \cdot (L_{T\text{max}} - L_u)/(f_T - f_u) \ge 24\ \text{dB}$
  y
  $\Delta L_o = f_T \cdot (L_{T\text{max}} - L_o)/(f_o - f_T) \ge 24\ \text{dB}$.
- **El problema:** la norma madre DIN 45681:2005-03 imprime $f_T/\sqrt{2}$ en
  **ambos** flancos (Gleichungen (10)/(11), p. 14 impresa), y su programa de
  referencia ejecutable del Anhang J hace lo mismo (`Frequenz(i)/Sqr(2)`).
  Los dos impresos no pueden satisfacerse a la vez. Ninguno de los factores
  ISO es el de DIN: en el flanco inferior $1/2 < 1/\sqrt{2}$, así que el
  impreso ISO devuelve una diferencia de nivel $\sqrt{2}$ **menor** y es por
  tanto **más estricto**; en el flanco superior el divisor falta por
  completo, así que el impreso ISO devuelve $\sqrt{2}$ **mayor** y es **más
  laxo**. Una revisión anterior de esta entrada tenía las dos direcciones al
  revés y describía el flanco superior como «a la mitad», cuando en realidad
  el divisor falta, no está a la mitad. Los tonos límite con pendiente de un
  solo flanco entre $24/\sqrt{2} = 17$ y
  $24 \cdot \sqrt{2} = 34\ \text{dB/octave}$ cambian de clasificación entre
  las dos lecturas.
- **Evidencia:** comparación lado a lado del impreso ISO, el impreso de
  DIN 45681 y el programa del Anhang J de DIN. Los radicales de DIN son
  exactamente el caso para el que existe la regla de la página: `pdftotext`
  pierde el glifo `√` de ambas fórmulas DIN, así que el texto extraído lee
  `f_T/2` y casa con el impreso ISO, mientras que la página misma lee
  `f_T/√2`. Verificado en la página 13 del PDF (p. 9 impresa) de ISO/PAS
  20065:2016 y la página 14 del PDF (p. 14 impresa) de DIN 45681:2005-03.
- **Comportamiento de la biblioteca:** sigue la lectura DIN/$\sqrt{2}$ (casa
  con la única referencia ejecutable), con la elección registrada en
  [`tone_audibility.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tone_audibility.py).
- **Estado:** sin notificar.

## DIN 45681:2005-03, Anhang I, Tabelle I.6, fila «6 FG»

- **Ubicación:** Anhang I, Beispiel I.2 (motor de combustión, espectro
  $j = 1$), Tabelle I.6, la fila combinada «6 FG» de los tres tonos
  $k = 6/7/8$ ($592{,}2$ / $629{,}8$ / $643{,}3\ \text{Hz}$, niveles de tono
  $78{,}31$ / $75{,}00$ / $79{,}75\ \text{dB}$).
- **El impreso:** $L_T = 81{,}11\ \text{dB}$ junto con
  $\Delta L = 9{,}12\ \text{dB}$ (con $L_S = 59{,}53$, $L_G = 76{,}16$,
  $a_v = -2{,}40$ a $592{,}2\ \text{Hz}$).
- **El problema:** las dos celdas se contradicen. El
  $\Delta L = 9{,}12\ \text{dB}$ impreso solo se reproduce desde la suma
  energética *simple* de la Fórmula (17) de los tres niveles de tono
  ($82{,}873\,4\ \text{dB}$): $82{,}87 - 76{,}16 + 2{,}40 = 9{,}11$. El
  $L_T = 81{,}11\ \text{dB}$ impreso es esa misma suma menos exactamente
  $1{,}763\ \text{dB}$, y tomado al pie de la letra daría
  $\Delta L = 7{,}35\ \text{dB}$.
- **Evidencia:** recálculo desde los niveles por tono impresos de la Tabelle
  I.6. El desplazamiento es el discriminador y es una constante, no una
  deduplicación: $82{,}873\,4 - 81{,}11 = 1{,}763\ \text{dB}$, y
  $1{,}76\ \text{dB}$ es $10\log_{10} 1{,}5$, la propia corrección de ancho
  de banda efectivo de Hanning de la norma (apartado 5.3.2). El mismo
  desplazamiento aparece en la fila «5 FG» de la Tabelle I.10 (p. 46
  impresa), donde los dos tonos miembros a $705{,}2$ y $732{,}1\ \text{Hz}$
  tienen $L_T = 55{,}12$ y $54{,}23\ \text{dB}$, suman
  $57{,}708\ \text{dB}$, y se imprimen como $55{,}95\ \text{dB}$,
  $1{,}758\ \text{dB}$ más bajo, y allí el $\Delta L = 3{,}22\ \text{dB}$
  impreso sigue al $L_T$ impreso exactamente
  ($55{,}95 - 55{,}28 + 2{,}55 = 3{,}22$), así que la fila de la Tabelle I.10
  es internamente consistente y la de la Tabelle I.6 no. La tercera fila
  combinada, «2 FG» de la misma Tabelle I.6, no lleva desplazamiento alguno:
  sus tres niveles miembros $64{,}56$ / $67{,}96$ / $68{,}63\ \text{dB}$
  suman $72{,}149\ \text{dB}$ contra unos $72{,}15\ \text{dB}$ impresos, y su
  $\Delta L$ los sigue. Una revisión anterior de esta entrada atribuía la
  celda de $81{,}11\ \text{dB}$ a la deduplicación de líneas compartidas de
  la Anmerkung 2; ese diagnóstico no se sostiene, porque una deduplicación
  quita una cantidad arbitraria de energía mientras que todos los
  desplazamientos observados aquí son los mismos 1,76 dB. Verificado en la
  página 41 del PDF (p. 41 impresa) y la página 46 del PDF (p. 46 impresa) de
  DIN 45681:2005-03.
- **Comportamiento de la biblioteca:** `combined_tone_level` sigue la
  Anmerkung 2 (líneas compartidas contadas una vez), que reproduce el oráculo
  impreso de «2 FG»; para la fila «6 FG» solo se fija la cadena de
  $\Delta L$, con la contradicción registrada en `tests/reference_data/`.
- **Estado:** sin notificar.

## DIN 45681:2005-03, Anhang I, Tabellen I.2 y I.10 (índice de espectro equivocado en un encabezado de columna)

- **Ubicación:** Anhang I, los encabezados de columna de la Tabelle I.2
  (p. 37 impresa, espectro $j = 2$) y la Tabelle I.10 (p. 46 impresa,
  espectro $j = 24$).
- **El impreso:** todas las columnas de la Tabelle I.2 llevan el subíndice
  del índice de espectro 2 (`f_T 2,k`, `f_1 2,k`, `f_2 2,k`, `L_S 2,k`,
  `L_T 2,k`, `L_G 2,k`, `a_v 2,k`, `u_2,k`) salvo la columna de
  audibilidad, que se encabeza **`ΔL_1,k`**. Todas las columnas de la Tabelle
  I.10 llevan el subíndice 24 (`f_T 24,k`, `ΔL 24,k`, `f_1 24,k`,
  `f_2 24,k`, `L_S 24,k`, `L_T 24,k`, `L_G 24,k`, `u 24,k`) salvo la columna
  de enmascaramiento, que se encabeza **`a_v 1,k`**.
- **El problema:** ambas tablas llevan el índice de espectro del *primer*
  espectro en una columna. El propio pie de la Tabelle I.2 lee «des zweiten
  Spektrums (j = 2)» y el de la Tabelle I.10 «des 24. Spektrums (j = 24)», y
  los valores del cuerpo pertenecen a esos espectros: la columna $\Delta L$
  de la Tabelle I.2 es la audibilidad de los tonos de $j = 2$
  ($8{,}53\ \text{dB}$ a $627{,}2\ \text{Hz}$, que la Anmerkung bajo la tabla
  llama «die maßgebliche Differenz ΔL_2»), y la columna $a_v$ de la Tabelle
  I.10 es el índice de enmascaramiento de los tonos de $j = 24$. El índice 1
  está bien en exactamente una tabla del anexo, la Tabelle I.6, que es la
  tabla de $j = 1$ del Beispiel I.2 y lleva `ΔL_1,k` y `a_v 1,k`
  legítimamente.
- **Evidencia:** los propios pies de las tablas, los subíndices de sus
  columnas vecinas y la Anmerkung bajo cada una. Verificado en la página 37
  del PDF (p. 37 impresa), la página 46 del PDF (p. 46 impresa) y la página
  41 del PDF (p. 41 impresa) de DIN 45681:2005-03.
- **Comportamiento de la biblioteca:** no hizo falta ninguno; los números no
  se ven afectados. Las fixtures de regresión indexan ambas tablas por el
  espectro de su pie.
- **Estado:** sin notificar.

## IEC 60268-1:1985, Appendix A, Figura A1 (último condensador en derivación impreso como 41.47 nF)

- **Ubicación:** Appendix A, «Noise weighting network and quasi-peak meter»,
  Figura A1 «Weighting network» (p. 29 impresa), plano 0641/85. El impreso
  francés del mismo arte (p. 28 impresa) lleva el mismo valor como
  `41,47 nF`.
- **El impreso:** el último condensador en derivación de la escalera, el que
  cruza la entrada del amplificador de 600 Ω, está etiquetado **41.47 nF**.
- **El problema:** debería ser **31.47 nF**, que es lo que la Figura 1a de
  ITU-R BS.468-4 imprime para la misma red. Todos los demás elementos de la
  Figura A1 casan exactamente con la Figura 1a de BS.468-4: fuente de 600 Ω,
  13.85 nF, 12.88 mH, 26.82 nF, 33.06 nF, 9.21 nF, 26.49 mH y Z = 600 Ω. La
  lectura pretendida no está en duda, porque el documento se contradice a sí
  mismo: evaluada contra la Table AI, impresa dos páginas antes en el mismo
  anexo, la escalera con 31.47 nF reproduce las 21 filas con un máximo de
  **0.050 dB** y no viola tolerancia alguna, mientras que la escalera con
  41.47 nF se va hasta **2.252 dB** (a 31 500 Hz) con un error cuadrático
  medio de 1.055 dB y **rompe la propia columna de tolerancias de la Table AI
  en siete frecuencias**, todas de 8 000 Hz a 20 000 Hz: −0.40 dB contra
  ±0.40 a 8 kHz, −0.74 contra ±0.60 a 9 kHz, −1.16 contra ±0.80 a 10 kHz,
  −1.85 contra ±1.20 a 12.5 kHz, −1.98 contra ±1.40 a 14 kHz, −2.05 contra
  ±1.60 a 16 kHz y −2.12 contra ±2.00 a 20 kHz. Barrer el condensador para
  minimizar el error contra la Table AI aterriza en 31.4798 nF.
- **Evidencia:** las dos escaleras evaluadas de forma independiente por un
  producto de cadenas ABCD sobre los siete elementos reactivos impresos entre
  la fuente y la carga de 600 Ω impresas, normalizadas a 1 kHz, y comparadas
  fila a fila con la Table AI y su columna de tolerancias. Ni la enmienda
  Amendment 1:1988 (que sustituye solo la Table AII) ni la Amendment 2:1988
  (que sustituye el subapartado 12.1, sobre producir un campo magnético
  alterno uniforme) tocan la Figura A1, así que la errata sigue en pie en el
  documento vigente con sus enmiendas. Verificado en la página 31 del PDF
  (p. 29 impresa) y la página 29 del PDF (p. 27 impresa), que lleva la Table
  AI, de IEC 60268-1:1985, y en la página 1 del PDF (p. 1 impresa) de la
  Recomendación ITU-R BS.468-4.
- **Comportamiento de la biblioteca:** no le afecta. La red de ponderación se
  construye desde los valores de componentes de la Figura 1a de BS.468-4 en
  [`filters/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/weighting.py), con
  31.47 nF, y las filas de la Table 1 son el oráculo. La entrada importa
  porque el subapartado 14.12.11 de IEC 60268-3:2013 remite al lector a «a
  weighting network complying with Appendix A of IEC 60268-1», así que una
  implementación en sala limpia arrancada desde IEC 60268-3 aterriza en el
  condensador equivocado.
- **Estado:** sin notificar.

## IEC 60268-1:1985, Appendix A, Table AII (fila del límite inferior corrida una columna)

- **Ubicación:** Appendix A, Table AII, la característica dinámica con
  ráfagas de tono del medidor de cuasi-pico, fila «Limited values — lower
  limit» (p. 31 impresa).
- **El impreso:** la fila del límite inferior (%) lee
  `13.5 | 22.4 | 34 | 41 | 44 | 44 | 50 | 68` para las columnas de 1, 2, 5,
  10, 20, 50, 100 y 200 ms, mientras que la fila (dB) impresa justo debajo
  lee `−17.4 | −13.0 | −9.3 | −7.7 | −7.1 | −6.0 | −4.7 | −3.3`.
- **El problema:** las celdas de 50 ms y 100 ms contradicen sus propias
  celdas en dB. −6.0 dB es 50.1 %, no 44 %, y −4.7 dB es 58.2 %, no 50 %. La
  fila de porcentajes se ha corrido una columna a la derecha desde 50 ms en
  adelante, arrastrando los valores de 20 ms y 50 ms a las dos celdas
  siguientes; la fila en dB y la celda de 200 ms se quedaron donde les
  corresponde. La Table 2 de ITU-R BS.468-4 imprime `... | 44 | 50 | 58 | 68`
  para las mismas cuatro columnas.
- **Evidencia:** las dos filas de la misma tabla leídas una contra otra, y
  contra la fila correspondiente de la Table 2 de ITU-R BS.468-4.
  **Corregido por la Amendment 1:1988-01**, cuya hoja inglesa se encabeza
  «Page 31 / Replace Table AII by the following:» e imprime la fila del
  límite inferior como `13.5 | 22.4 | 34 | 41 | 44 | 50 | 58 | 68`, casando
  con BS.468-4; todas las demás celdas de la tabla de sustitución son
  idénticas al impreso base, así que esta fila es todo el contenido
  sustantivo de la enmienda. Verificado en la página 33 del PDF (p. 31
  impresa) de IEC 60268-1:1985, en la página 3 del PDF (p. 3 impresa) de la
  Amendment 1:1988 de IEC 60268-1:1985, y en la página 4 del PDF (p. 4
  impresa) de la Recomendación ITU-R BS.468-4.
- **Comportamiento de la biblioteca:** no le afecta. Las once ventanas de
  aceptación están transcritas de las Tables 2 y 3 de BS.468-4 en
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data), que concuerdan con la
  tabla IEC enmendada. Se registra porque el documento base sin enmendar es
  el que probablemente tenga un lector, y ensancha las ventanas de aceptación
  de 50 ms y 100 ms en 1.1 dB y 1.3 dB por abajo.
- **Estado:** sin notificar (corregido por el organismo emisor en 1988).

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

## IEC 60268-1:1985, Appendix A, Table AI (tolerancia de 16 000 Hz impresa como ±1.65)

- **Ubicación:** Appendix A, Table AI, la columna de tolerancias, fila de
  16 000 Hz (p. 27 impresa; el Tableau AI francés en la p. 26 impresa imprime
  el mismo valor).
- **El impreso:** `±1.65 1)`.
- **El problema:** la Table 1 de ITU-R BS.468-4 y la Table 1 de AES17-2015
  imprimen ambas **±1.6** para la misma fila, y la propia nota 1) de la tabla
  es lo que lo zanja: las tolerancias marcadas «are obtained by a linear
  interpolation on a logarithmic graph on the basis of values specified for
  the frequencies used to define the mask, i.e. 31.5 Hz, 100 Hz, 1 000 Hz,
  5 000 Hz, 6 300 Hz, and 20 000 Hz». Interpolado con esa regla entre
  (6 300 Hz, 0 dB) y (20 000 Hz, ±2.0 dB), 16 000 Hz da 1.6137 dB, que
  redondea a 1.6 con un decimal y a 1.61 con dos. Ningún redondeo de la regla
  produce 1.65, y ningún par de anclas alternativo tampoco: tomar la recta de
  6 300 Hz a 31 500 Hz da en cambio 1.6216 dB. El valor es además anómalo
  dentro de su propia columna, que está citada a un decimal en todos los
  demás sitios.
- **Evidencia:** la regla de la nota aplicada a las 14 filas marcadas de la
  misma columna, que reproduce todas y cada una (63 Hz 1.400, 200 Hz 0.8495,
  400 Hz 0.6990, 800 Hz 0.5485, 3 150 y 4 000 Hz 0.5000, 7 100 Hz 0.2070,
  8 000 Hz 0.4136, 9 000 Hz 0.6175, 10 000 Hz 0.7999, 12 500 Hz 1.1863,
  14 000 Hz 1.3825, 31 500 Hz 2.7865) y solo 16 000 Hz discrepa de lo
  impreso. No lo corrigen la Amendment 1:1988 ni la Amendment 2:1988.
  Verificado en la página 29 del PDF (p. 27 impresa) de IEC 60268-1:1985 y en
  la página 2 del PDF (p. 2 impresa) de la Recomendación ITU-R BS.468-4.
- **Comportamiento de la biblioteca:** no hizo falta ninguno. La máscara de
  tolerancias se toma de la Table 1 de BS.468-4, y la curva digital realizada
  se sujeta de todos modos a una cota mucho más estrecha que la máscara: la
  máscara gobierna un instrumento de medición compuesto por el amplificador y
  la red, no la desviación de un filtro respecto de la curva nominal.
- **Estado:** sin notificar.

## IEC 60268-3:2013, apartado 14.12.9.2 f) (denominador del DIM)

- **Ubicación:** apartado 14.12.9.2, punto f) (p. 39 impresa), la fórmula de
  la distorsión de intermodulación dinámica $d_\text{DIM}$.
- **El impreso:**
  $d_\text{DIM} = (\sum_{i=1}^{9} {U'_i}^{2})^{1/2} / U_2 \times 100\ \%$.
- **El problema:** el denominador es uno de los nueve términos de su propio
  numerador. La Table 2 del mismo apartado (p. 38 impresa) define $U_2$ como
  la componente de intermodulación a $f_s - 2f_q = 8{,}70\ \text{kHz}$, y el
  punto d) define $U_1, U_2, \ldots U_i$ como exactamente esas componentes,
  así que la suma $i = 1\ldots9$ recorre $U_1 \ldots U_9$ e incluye $U_2$.
  Entretanto, el apartado definitorio 14.12.9.1 declara la razón de la suma
  r.m.s. de las tensiones de productos de intermodulación de la Table 2 «to
  the amplitude of the output voltage at the frequency f_s», es decir, la
  componente sinusoidal de 15 kHz $U_s$, el convenio de Otala, y el punto d)
  mide «the amplitudes of the sinusoidal signal $U_s$» precisamente para que
  pueda usarse, cosa que la fórmula de f) no hace nunca. El denominador
  debería ser $U_s$. Una revisión anterior de esta entrada decía que «U2 se
  usa en todo 14.12 para la tensión total de salida»; eso es falso, tanto en
  el impreso inglés como en el francés.
- **Evidencia:** la Table 2, el punto d) y el punto f) leídos juntos en ambas
  columnas de idioma de la edición bilingüe; la literatura histórica del DIM
  (Otala) define la razón respecto a la amplitud de la sinusoide. Verificado en la
  página 41 del PDF (p. 39 impresa), la página 40 del PDF (p. 38 impresa),
  que lleva la Table 2, y la página 102 del PDF (p. 100 impresa), que lleva
  el mismo punto f) en la columna francesa, de IEC 60268-3:2013.
- **Comportamiento de la biblioteca:** sigue la definición de 14.12.9.1
  (referencia = la amplitud de salida a $f_s$), con un comentario en el
  código junto a la medición de referencia en
  [`distortion.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/distortion.py).
- **Estado:** sin notificar.

## IEC 60268-16:2011, Table M.1 (la fila beta declara el término de redundancia equivocado)

- **Ubicación:** Annex M, Table M.1 «Example calculation», paso 4, la fila
  etiquetada «Sum of beta\*$MTI$ = $MTI_k$ $\times$ beta weighting» (p. 67
  impresa), justo debajo de la fila alfa homóloga.
- **El impreso:** la etiqueta lee $MTI_k \times \beta_k$, y las siete celdas
  de la fila leen 0,059 | 0,052 | 0,045 | 0,008 | 0,037 | 0,081 | 0,000,
  sumadas en la página siguiente como $\sum \text{beta*}MTI = 0{,}282$.
- **El problema:** la etiqueta y las celdas declaran cantidades distintas, y
  la equivocada es la etiqueta. El apartado A.5.6 de la misma edición (p. 47
  impresa) define el índice como
  $STI = \sum_{k=1}^{7} \alpha_k \times MTI_k -
  \sum_{k=1}^{6} \beta_k \times \sqrt{MTI_k \times MTI_{k+1}}$: el término de
  redundancia es la *media geométrica de dos bandas adyacentes*, no el
  $MTI_k$ de la propia banda. Leído contra la propia fila de MTI de la tabla,
  $\beta_k \times MTI_k$ da 0,062 | 0,051 | 0,044 | 0,008 | 0,036 | 0,076,
  sumando 0,277, que discrepa de cinco de las seis celdas impresas y del
  total impreso. $\beta_k\sqrt{MTI_k MTI_{k+1}}$ reproduce las seis celdas y
  el total de 0,282. La séptima celda no forma parte de ninguna de las dos
  lecturas: la suma de redundancia se detiene en $k = 6$ porque la banda de
  8 kHz no tiene banda por encima con la que emparejarse, así que su 0,000 es
  el marcador de posición de una columna sin pareja de redundancia, no un
  término. La fila alfa de encima, etiquetada de la misma manera, es
  correcta, porque allí la etiqueta y A.5.6 sí concuerdan.
- **Evidencia:** ambas lecturas recalculadas desde la propia fila de MTI del
  paso 4c de la tabla y comparadas celda a celda con la fila impresa y con su
  total impreso; A.5.6 leído contra la etiqueta. El defecto no mueve la
  respuesta de este ejemplo, ya que $1{,}040 - 0{,}277 = 0{,}763$ y
  $1{,}040 - 0{,}282 = 0{,}758$ se imprimen ambos como el STI 0,76 con el que
  termina la tabla, que es como una etiqueta que contradice la fórmula
  normativa sobrevive a un ejemplo resuelto. Verificado en la página 69 del
  PDF (p. 67 impresa) y la página 49 del PDF (p. 47 impresa) de
  IEC 60268-16:2011.
- **Comportamiento de la biblioteca:** implementa A.5.6 con el término de
  redundancia tal como allí está impreso, en
  [`_index_from_corrected_mtf`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/speech/sti.py); el test de
  factores de ponderación por pares de A.2.2 lo fija de forma independiente,
  y las filas de conformidad «IEC 60268-16:2020 A.2.2» e «IEC 60268-16 Annex
  M» leen ambas el índice que produce.
- **Estado:** sin notificar.

## IEC 60268-16:2011, Table M.1 (I_k tabulado un millón de veces sus vecinos)

- **Ubicación:** Annex M, Table M.1, la fila «Combined squared sound pressure
  $I_k$, MPa$^2$» del paso 2 (p. 64 impresa) y del paso 3 (p. 65 impresa),
  leída con las filas $I_{am,k}$ e $I_{rt,k}$ de debajo.
- **El impreso:** para la señal de 77,9 dB de la banda de 125 Hz, el paso 2
  imprime $I_k$ = 61,7, y cuatro filas más abajo imprime $I_{rt,k}$ = 40 000
  para el umbral de recepción de 46 dB de la misma banda.
- **El problema:** dos defectos en una fila. La unidad es imposible: a
  77,9 dB re 20 µPa la presión sonora al cuadrado es
  $0{,}0247\ \text{Pa}^2$, así que la celda no puede ser 61,7 MPa$^2$ bajo
  ninguna lectura del prefijo. Lo que la fila tabula en realidad es la razón
  de intensidades adimensional $10^{L/10} = 61\,722\,596$ dividida por
  $10^{6}$. Y ese divisor no se aplica a las dos cantidades que la norma suma
  a $I_k$ en las filas inmediatamente siguientes: $I_{am,k}$ e $I_{rt,k}$ se
  tabulan como la razón simple, siendo 40 000 el
  $10^{4,6} = 39\,811$ redondeado, sin dividir. Un lector que forme
  $I_k + I_{am,k} + I_{rt,k}$ desde las celdas tal como están impresas
  infravalora su primer término en $10^{6}$. La fila impresa «adjustment to
  remove masking and threshold» es la comprobación: 1,019 a 500 Hz es
  $(I_k + I_{am,k} + I_{rt,k})/I_k$ solo una vez que $I_k$ se restituye a
  26 305 192; formada desde las celdas tal como están impresas, la misma
  expresión lee 19 279.
- **Evidencia:** todas las celdas de ambas filas de $I_k$ recalculadas como
  $10^{L/10}$ desde los niveles combinados impresos encima, y todas las
  celdas de las filas $I_{am,k}$ e $I_{rt,k}$ recalculadas como
  $amf_k \times I_{k-1}$ y $10^{ART_k/10}$; el primer conjunto se reproduce a
  $10^{-6}$ del valor calculado y los otros dos a $10^{0}$. Verificado en la
  página 66 del PDF (p. 64 impresa) y la página 67 del PDF (p. 65 impresa) de
  IEC 60268-16:2011.
- **Comportamiento de la biblioteca:** lleva las tres cantidades en una sola
  escala, la razón simple a $p_0^2 = (20\ \mu\text{Pa})^2$, en la corrección
  de [`sti.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/speech/sti.py); la transcripción en
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data) conserva las celdas
  impresas al pie de la letra y nombra el $10^{6}$ por el que las reescala, y
  la fila de conformidad «IEC 60268-16 Annex M» lee el ajuste que alimentan.
- **Estado:** sin notificar.

## IEC 60268-16:2011, Table M.1 (I_am,k del paso 3 a 250 Hz)

- **Ubicación:** Annex M, Table M.1, paso 3, la fila $I_{am,k}$, columna de
  250 Hz (p. 65 impresa).
- **El impreso:** 2 850 000, el mismo valor que la celda de 500 Hz de al
  lado.
- **El problema:** la celda no redondea desde la cantidad que nombra. Con los
  niveles operacionales impresos dos filas más arriba, $I_{am,k}$ a 250 Hz es
  el factor de enmascaramiento auditivo de la banda de 125 Hz por la
  intensidad combinada de esa banda,
  $0{,}01463507 \times 195\,339\,273 = 2\,858\,804$, que a las tres cifras
  significativas a las que se imprime la fila lee 2 860 000. La celda de
  500 Hz es correcta: su 2 852 252 sí se imprime como 2 850 000. Las dos
  celdas solo se reproducen juntas arrastrando el
  $amf \times 1000 = 14{,}6$ *redondeado* de la fila de arriba en lugar del
  propio factor, y el paso 2 demuestra que eso no es lo que hace la tabla, ya
  que sus dos celdas correspondientes se imprimen separadas, como 508 000 y
  507 000, cosa que solo da el factor sin redondear.
- **Evidencia:** ambas celdas recalculadas desde los niveles operacionales de
  habla y ruido impresos, y el par del paso 2 recalculado de la misma manera
  como control. El defecto no cambia nada aguas abajo: la corrección de
  enmascaramiento y umbral de la banda es 0,985552 con el valor correcto
  contra 0,985596 con el impreso, y la fila imprime 0,986 en cualquier caso.
  Verificado en la página 67 del PDF (p. 65 impresa) y la página 66 del PDF
  (p. 64 impresa) de IEC 60268-16:2011.
- **Comportamiento de la biblioteca:** calcula $I_{am,k}$ desde el factor de
  enmascaramiento sin redondear. La transcripción en
  [`tests/reference_data/`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data) conserva la celda
  impresa y el test
  `test_annex_m_step3_masking_intensity_at_250_hz_is_the_printed_erratum`
  afirma el valor calculado contra 2 858 804 y contra el impreso, para que la
  única celda de la tabla que no es un oráculo no pueda convertirse en uno
  sin hacer ruido.
- **Estado:** sin notificar.

## UNE-EN 61043:1999, apartado 6.1 (el rango de frecuencias de la clase 2, perdido en la traducción)

- **Ubicación:** apartado 6.1 «Rango de frecuencias», la frase de la clase 2,
  de UNE-EN 61043 (abril de 1999), que se declara «la versión oficial, en
  español, de la Norma Europea EN 61043 de enero 1994, que a su vez adopta la
  Norma Internacional CEI 61043:1993».
- **El impreso:** una sola frase, «Los procesadores de clase 2 deberán
  cubrir, al menos, el rango desde 45 Hz a 5,6 kHz en bandas de octava.»
- **El problema:** el texto EN/IEC da a los procesadores de clase 2 dos
  rangos alternativos, no uno: «Class 2 processors shall, at least, cover the
  range from 45 Hz to 7,1 kHz in one-third octave bands, **or** the range
  from 45 Hz to 5,6 kHz in one octave bands» (BS EN 61043:1994, apartado
  6.1). La traducción pierde la primera alternativa. La omisión es normativa
  y no editorial: elimina una de las dos maneras de satisfacer el apartado
  6.1, y un lector solo del texto español concluiría que la clase 2 está
  *definida* sobre bandas de octava, de modo que una cadena de tercios de
  octava verificada sobre las 22 bandas tabuladas de 50 Hz a
  $6{,}3\ \text{kHz}$ no podría acreditar la clase 2 en todo su rango.
- **Evidencia:** lectura lado a lado del apartado 6.1 en ambos impresos. La
  frase de la clase 1 es equivalente palabra por palabra en los dos
  documentos, así que la divergencia queda confinada a la frase de la clase
  2. El impreso español además se contradice a sí mismo: su Tabla 2 tabula el
  índice presión-intensidad residual para procesadores de clase 2 en los 22
  centros de tercio de octava, y su Nota 2, traducida fielmente («Para
  procesadores con análisis en bandas de octavas únicamente, los requisitos
  se aplican únicamente a las frecuencias centrales de las bandas de
  octava»), aparta los procesadores de solo octavas como caso especial. Ambas
  son redundantes si todo procesador de clase 2 es de bandas de octava.
- **Comportamiento de la biblioteca:** implementa la lectura EN/IEC.
  [`verify_intensity_class`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/intensity_compliance.py)
  trata el conjunto completo de 22 bandas de tercio de octava como
  acreditación de cualquiera de las dos clases, y el conjunto de 7 bandas de
  octava (63 Hz a 4 kHz) como alternativa de clase 2 que nunca acredita la
  clase 1, con ambas ramas fijadas por tests de regresión
  ([`tests/emission/test_intensity_compliance.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_intensity_compliance.py)).
- **Estado:** sin notificar (traducción nacional, no el texto del organismo
  emisor).

## IEC 61183:1994, nota de A.1.8 (dos ángulos de igual área que rompen la simetría de su propia lista)

- **Ubicación:** Anexo A, la NOTA que sigue a la lista de símbolos de las
  Fórmulas (A.1) y (A.2), bajo A.1.8 (folio impreso 10), que enumera las
  direcciones de una división de la esfera en 38 elementos de igual área.
- **El impreso:** «The angles of incidence will be 0°, 32,6°, 50,8°, 65,1°,
  **77,9°**, 90°, 102,2°, 114,9°, 129,2°, 147,4°, 180°, 212,6°, 230,8°,
  245,1°, 257,8°, 270°, **282,1°**, 294,9°, 309,2°, 327,4° in the horizontal
  plane and the same angles with the exception of 0° and 180° in the vertical
  plane.»
- **El problema:** la división es simétrica respecto de la dirección rasante:
  la nota pone un solo elemento en cada polo y uno a 90°, y 38 elementos
  iguales con un casquete en cada polo dejan nueve anillos de cuatro
  elementos cada uno, imágenes especulares entre sí respecto de 90°. Todos los
  pares de la lista impresa cumplen esa simetría salvo uno: $32{,}6 + 147{,}4$,
  $50{,}8 + 129{,}2$ y $65{,}1 + 114{,}9$ dan todos $180{,}0°$, mientras que
  $77{,}9 + 102{,}2 = 180{,}1°$. El mismo desliz aparece en la segunda mitad de
  la circunferencia, donde $257{,}8°$ es $180° + 77{,}8°$ pero $282{,}1°$ es
  $360° - 77{,}9°$. La dirección que divide en dos mitades el área de cada
  elemento en ángulo polar, $\phi_k = \arccos[1 - (4k - 1)/19]$, reproduce
  todos los demás ángulos impresos con su 0,1° y da $77{,}846°$ y $282{,}154°$
  para el cuarto anillo, que se leen **77,8°** y **282,2°**.
- **Evidencia:** la construcción evaluada para los nueve anillos y comparada
  con los veinte ángulos impresos. Verificado en la página 14 del PDF (p. 10
  impresa) de BS EN 61183:1995, el texto inglés de EN 61183:1994, que es
  IEC 1183:1994 (hoy IEC 61183:1994) sin cambios.
- **Comportamiento de la biblioteca:** `metrology.equal_area_incidence_angles`
  calcula las direcciones a partir de la construcción en lugar de
  transcribirlas, y la fila de conformidad de la nota comprueba los otros
  dieciocho ángulos impresos; los tests fijan los dos valores corregidos
  ([`tests/metrology/test_random_incidence.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_random_incidence.py)).
  La Fórmula (A.5) pondera cada lectura con 1/38 sea cual sea su dirección,
  así que el desliz no afecta a ningún factor de directividad; solo a dónde se
  coloca la fuente.
- **Estado:** sin notificar.

## IEC 62585:2012, Tabla I.2 (un factor de cobertura que sus propios grados de libertad no dan)

- **Ubicación:** Anexo I, Tabla I.2 «Uncertainty example for a frequency of
  1 kHz» (folio impreso 38), la última fila, «Expanded uncertainty of
  $C_\mathrm{FF,SLM}$».
- **El impreso:** «(normal) **k = 2,11**» junto a «Effective degree of freedom
  = 29,98», con la incertidumbre expandida impresa «0,12» y un dígito de guarda
  en subíndice «(4)», es decir 0,124 dB, sobre una incertidumbre típica
  combinada de «0,059 0» dB.
- **El problema:** el apartado 5 pide el factor de cobertura que da un nivel
  de confianza del 95 %, y el Anexo I calcula los grados de libertad efectivos
  por Welch-Satterthwaite «thereby enabling the coverage factor k to be
  selected to provide a level of confidence of 95 %». Las componentes de la
  propia tabla dan $u_\mathrm{c} = 0{,}0590$ dB y $\nu_\mathrm{eff} =
  u_\mathrm{c}^4 / (0{,}03^4/2) = 29{,}98$, ambos como se imprimen, y el factor
  de Student para el 95 % con 29,98 grados de libertad es $t_{0{,}975}(29{,}98)
  = $ **2,04**, no 2,11; 2,11 es el factor para unos 17 grados de libertad. La
  incertidumbre expandida que resulta es $t_{0{,}975}(29{,}98) \times
  u_\mathrm{c} = 2{,}042\,3 \times 0{,}059\,031 = 0{,}120\,56$ dB, que con su
  dígito de guarda se imprimiría **0,12(1)**; el 0,12(4) impreso es
  $2{,}11 \times 0{,}0590 = 0{,}124\,49$ dB. Con los dos decimales con que se
  da la corrección (componente a14), ambos se leen 0,12 dB.
- **Evidencia:** el balance recalculado a partir de los quince valores y
  divisores impresos, y el cuantil de Student evaluado en los grados de
  libertad impresos. Verificado en la página 40 del PDF (p. 38 impresa) de
  BS EN 62585:2012, el texto inglés de EN 62585:2012, que es IEC 62585:2012
  sin cambios.
- **Comportamiento de la biblioteca:** `metrology.correction_uncertainty_budget`
  toma el factor de cobertura de los grados de libertad efectivos, aquí 2,042,
  y las filas de conformidad de la Tabla I.2 fijan ese factor y la
  incertidumbre expandida que da, 0,121 dB, con los impresos señalados como
  errata
  ([`tests/metrology/test_free_field_corrections.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_free_field_corrections.py)).
- **Estado:** sin notificar.

## IEC 62585:2012, Tabla H.1 (el exponente del índice 31)

- **Ubicación:** Anexo H, Tabla H.1 «Exact frequencies for one-twelfth-octave
  steps over one decade» (folio impreso 35), la fila del índice 31.
- **El impreso:** «Exact $f_x$» **$10^{31/80}$**, junto a «Exact $f_x$
  calculated» 5,956 621 kHz.
- **El problema:** todas las demás filas imprimen el exponente $x/40$, que es
  la Fórmula (H.1), $f_x = f_\mathrm{r} \cdot 10^{3x/10b}$ con $b = 12$, y el
  valor calculado a su lado es $10^{31/40} = 5{,}956\,621$. $10^{31/80}$ daría
  2,441 kHz, fuera de la década que cubre la tabla. El exponente se lee
  **$10^{31/40}$**.
- **Evidencia:** la Fórmula (H.1) evaluada para los 41 índices; los 41
  valores calculados se reproducen con las siete cifras significativas
  impresas. Verificado en la página 37 del PDF (p. 35 impresa) de
  BS EN 62585:2012, el texto inglés de EN 62585:2012, que es IEC 62585:2012
  sin cambios.
- **Comportamiento de la biblioteca:** `metrology.exact_frequencies` evalúa la
  Fórmula (H.1) y nunca lee la columna de exponentes, así que no hizo falta
  ningún cambio; la fila de conformidad de la Tabla H.1 comprueba los 41
  valores calculados.
- **Estado:** sin notificar.

## IEC 62585:2012, Fórmulas (E.4) a (E.6) (las dos lecturas en el acoplador intercambiadas)

- **Ubicación:** Anexo E, Fórmulas (E.4), (E.5) y (E.6) (folio impreso 26),
  frente a la Figura E.1 y sus Fórmulas (E.3A) y (E.3B) (folio impreso 25), la
  lista de símbolos bajo (E.6) y los descriptores a3 y a4 de la Tabla I.1
  (folio impreso 37).
- **El impreso:** Figura E.1: «$L_\mathrm{ind3a} = L_{p,\mathrm{P1}} +
  \Delta L_\mathrm{P,RM}$ (E.3A)» y «$L_\mathrm{ind3b} = L_{p,\mathrm{P2}} +
  \Delta L_\mathrm{P,SLM}$ (E.3B)», con $L_{p,\mathrm{P1}}$ dibujado en el
  micrófono de referencia y $L_{p,\mathrm{P2}}$ en el sonómetro; la lista de
  símbolos: «$L_{p,\mathrm{P1}}$ is the sound pressure level at reference
  microphone in the comparison coupler», «$L_{p,\mathrm{P2}}$ is the sound
  pressure level at sound level meter»; la Tabla I.1: «$L_\mathrm{ind3a}$ Level
  measurement – reference microphone in comparison coupler», «$L_\mathrm{ind3b}$
  Level measurement – sound level meter in comparison coupler». Y después
  «$C_\mathrm{FF,SLM} = (L_\mathrm{ind1} - L_\mathrm{ind3a}) -
  (L_\mathrm{ind2} - L_\mathrm{ind3b}) - (L_{p,\mathrm{F1}} -
  L_{p,\mathrm{F2}}) + (L_{p,\mathrm{P1}} - L_{p,\mathrm{P2}}) +
  C_\mathrm{FF,RM}$ (E.6)».
- **El problema:** la corrección es la respuesta del sonómetro en campo libre
  menos su respuesta en el acoplador, $\Delta L_\mathrm{F,SLM} -
  \Delta L_\mathrm{P,SLM}$, como dice (E.5), y con las definiciones de la
  Figura E.1 eso es $(L_\mathrm{ind1} - L_\mathrm{ind3b}) - (L_\mathrm{ind2} -
  L_\mathrm{ind3a}) - (L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}}) +
  (L_{p,\mathrm{P2}} - L_{p,\mathrm{P1}}) + C_\mathrm{FF,RM}$. Las Fórmulas
  (E.4) a (E.6) son las (D.5) a (D.7) del calibrador con $L_\mathrm{ind3}$ y
  $L_\mathrm{ind4}$ renombrados, así que toman $L_\mathrm{ind3a}$ como el
  sonómetro y $L_\mathrm{ind3b}$ como la referencia, y $L_{p,\mathrm{P1}}$ en
  el sonómetro. Leída con las etiquetas de la propia figura, (E.6) queda a
  $2(\Delta L_\mathrm{P,SLM} - \Delta L_\mathrm{P,RM})$ de la corrección.
  Son las desviaciones de la indicación de cada canal respecto del nivel en el
  acoplador, y el método «requires neither absolute measurements nor an
  absolutely calibrated sound level meter» (E.1, folio impreso 25) mientras el
  canal de referencia lee «the level of the output voltage from the
  microphone» (E.2, paso 2, folio impreso 26), así que el error arrastra la
  diferencia entre las sensibilidades absolutas de los dos canales y está en
  todas las frecuencias: decenas de decibelios cuando un canal lee en
  decibelios re 1 V y el otro en nivel de presión sonora. Solo cuando los dos
  canales leen nivel de presión sonora se reduce al doble de la diferencia
  entre las dos respuestas de presión. O bien la figura, la lista de símbolos
  y la Tabla I.1 intercambian las dos etiquetas, o lo hacen las fórmulas; la
  página no puede sostener ambas cosas.
- **Evidencia:** (E.1) a (E.3B) sustituidas en (E.4), que no se reduce a
  $\Delta L_\mathrm{F,SLM} - \Delta L_\mathrm{P,SLM}$ con las etiquetas de la
  figura y sí con las de las fórmulas. Verificado en las páginas 27 y 28 del
  PDF (pp. 25 y 26 impresas) y en la página 39 del PDF (p. 37 impresa) de
  BS EN 62585:2012, el texto inglés de EN 62585:2012, que es IEC 62585:2012
  sin cambios.
- **Comportamiento de la biblioteca:** `metrology.comparison_coupler_correction`
  nombra sus entradas por lo que mide cada lectura, `slm_coupler_level_db` y
  `reference_coupler_level_db`, así que ninguna de las dos rotulaciones le
  afecta; la fila de conformidad del Anexo E construye las lecturas con las
  etiquetas de la Figura E.1 y los tests fijan el tamaño de la discrepancia
  ([`tests/metrology/test_free_field_corrections.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_free_field_corrections.py)).
- **Estado:** sin notificar.

## IEC 60118-4:2014, 6.4 NOTA 2, e IEC 62489-1:2010, 5.4.8.2 NOTA 3 (las respuestas de los filtros de limitación de banda intercambiadas)

- **Ubicación:** IEC 60118-4:2014, 6.4 «Pink noise signal», NOTE 2 (folio
  impreso 13); IEC 62489-1:2010+A1:2014, 5.4.8.2 b), NOTE 3 (folio impreso
  11), que la repite para la señal de la tensión de cumplimiento.
- **El impreso:** «the theoretical responses of the specified 3rd order
  Butterworth filters are **−0,8 dB at 100 Hz** and **−0,7 dB at 5 kHz**».
- **El problema:** los dos apartados especifican filtros Butterworth de
  tercer orden paso alto y paso bajo «giving −3 dB responses at 75 Hz and
  6,5 kHz». Su respuesta combinada es
  $10\lg\{[1 + (75/f)^6]^{-1}[1 + (f/6\,500)^6]^{-1}\}$ dB. A 100 Hz el
  término del paso alto es $(75/100)^6 = 0{,}178$ y la respuesta
  $-0{,}711$ dB; a 5 kHz el término del paso bajo es $(5\,000/6\,500)^6 =
  0{,}207$ y la respuesta $-0{,}818$ dB. A la décima que imprime la nota se
  leen **−0,7 dB a 100 Hz** y **−0,8 dB a 5 kHz**: los dos valores están
  intercambiados. La planitud de ±1 dB que explica la nota se cumple de
  cualquier modo.
- **Evidencia:** el módulo Butterworth evaluado en las dos frecuencias.
  Verificado en la página 15 del PDF (p. 13 impresa) de BS EN 60118-4:2015,
  el texto inglés de EN 60118-4:2015, que es IEC 60118-4:2014 sin cambios, y
  en la página 13 del PDF (p. 11 impresa) de BS EN 62489-1:2010+A1:2015, el
  texto inglés de EN 62489-1:2010+A1:2015, que es IEC 62489-1:2010 con su
  Modificación 1:2014 sin cambios.
- **Comportamiento de la biblioteca:** `electroacoustics.band_limit_response`
  evalúa los dos filtros, y las filas de conformidad de 6.4 NOTA 2 fijan
  $-0{,}711$ dB a 100 Hz y $-0{,}818$ dB a 5 kHz, con los valores impresos
  nombrados como la errata; `electroacoustics.loop_test_noise` filtra con las
  mismas secciones.
- **Estado:** sin notificar.

## IEC 60118-4:2014, 6.4 (el orden del filtro impreso como «one-third-order»)

- **Ubicación:** 6.4 «Pink noise signal», segundo párrafo (folio impreso 13).
- **El impreso:** «Bandwidth limitation shall be carried out by means of at
  least **one-third-order** Butterworth high pass and low pass filters giving
  −3 dB responses at 75 Hz and 6,5 kHz».
- **El problema:** un filtro no tiene un orden de un tercio: la redacción
  cruza el «third-octave-band spectrum» de la frase anterior con
  «third-order». El B.2.3 del mismo documento dice «The band-limiting filters
  should be at least of the **third-order**», la NOTA 2 de 6.4 habla de «the
  specified **3rd order** Butterworth filters», y el 5.4.8.2 b) de
  IEC 62489-1, que especifica la misma señal, imprime «at least
  **third-order** Butterworth». El apartado se lee «de tercer orden como
  mínimo».
- **Evidencia:** los tres pasajes comparados. Verificado en la página 15 del
  PDF (p. 13 impresa) y en la página 32 del PDF (p. 30 impresa) de
  BS EN 60118-4:2015, el texto inglés de EN 60118-4:2015, que es
  IEC 60118-4:2014 sin cambios, y en la página 13 del PDF (p. 11 impresa) de
  BS EN 62489-1:2010+A1:2015.
- **Comportamiento de la biblioteca:** `electroacoustics.loop_test_noise` y
  `electroacoustics.band_limit_response` usan secciones Butterworth de tercer
  orden; no hizo falta ningún cambio.
- **Estado:** sin notificar (tipográfico, sin consecuencia numérica).

## IEC 60118-4:2014, 6.6 y 8.2.1 (el medidor remitido a 5.1)

- **Ubicación:** 6.6 «Combi signal», tercer párrafo (folio impreso 14), y
  8.2.1 «Characteristic to be specified» (folio impreso 16).
- **El impreso:** 6.6: «to allow either meter specified in **5.1** to reach
  the correct measurement level»; 8.2.1: «measured with a meter as specified
  in **5.1** and a pick-up coil whose magnetic axis is vertical (unless
  otherwise specified – see **6.1**)».
- **El problema:** 5.1 es el apartado «General» del capítulo 5, «Using
  components of a sound system in an induction-loop system» (folio impreso
  11), y no especifica ningún medidor. Los dos medidores se especifican en
  6.1, el de valor eficaz verdadero en 6.1.3 y el medidor de programa de pico
  en 6.1.4, y la bobina de captación vertical «unless otherwise specified» es
  la regla de 8.1 (folio impreso 15), que 7.1 y 10.2.1 citan para las mismas
  palabras. Las referencias se leen **6.1** y **8.1**.
- **Evidencia:** las dos referencias comparadas con los títulos de los
  capítulos 5, 6 y 8. Verificado en las páginas 13, 16, 17 y 18 del PDF
  (pp. 11, 14, 15 y 16 impresas) de BS EN 60118-4:2015, el texto inglés de
  EN 60118-4:2015, que es IEC 60118-4:2014 sin cambios.
- **Comportamiento de la biblioteca:** `electroacoustics.field_strength_meter`
  es el medidor de valor eficaz verdadero de 6.1.3, que 6.1.1 hace definitivo
  en caso de duda; no hizo falta ningún cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 60118-4:2014, Figura 2 a) (el radio exterior acotado como 200 mm)

- **Ubicación:** Figura 2 «Measurement points for disabled refuge and
  similar call-points», leyenda de a) «Magnetic field source of small
  dimensions» (folio impreso 21).
- **El impreso:** «$l_2$ inner radius 300», «$l_3$ **outer radius 200**», con
  $l_3$ acotada en el dibujo desde el anillo interior de puntos hasta el
  exterior.
- **El problema:** un radio exterior de 200 mm quedaría dentro del radio
  interior de 300 mm. Tal como está dibujada, $l_3$ es la distancia entre los
  dos anillos, así que el radio exterior es $l_2 + l_3 = 500$ mm, que es
  también la distancia de la segunda fila de b) a su línea de referencia
  ($l_2 + l_3 = 300 + 200$ mm). La Modificación 1:2017 rehace la leyenda como
  «$l_2 + l_3$ Radio exterior: 500 mm».
- **Evidencia:** la leyenda comparada con las cotas del dibujo y con b).
  Verificado en la página 23 del PDF (p. 21 impresa) de BS EN 60118-4:2015,
  el texto inglés de EN 60118-4:2015, que es IEC 60118-4:2014 sin cambios, y
  en la página 7 del PDF (p. 7 impresa) de UNE-EN IEC 60118-4:2016/A1:2018,
  la edición española de IEC 60118-4:2014/A1:2017.
- **Comportamiento de la biblioteca:**
  `electroacoustics.small_volume_measurement_points` sitúa el anillo exterior
  a 500 mm, como la leyenda modificada, y la fila de conformidad de las
  Figuras 2 y 3 comprueba los dos radios.
- **Estado:** sin notificar (corregido por el organismo emisor en 2017).

## IEC 60118-4:2014, Anexo A.4 frente a 9.5 (+12 dB a 1,45 m en un mostrador)

- **Ubicación:** Anexo A (informativo), A.4 «Specific locations such as help
  and information points, ticket and bank counters», los dos párrafos tras la
  Figura A.2 (folio impreso 29), frente a 9.5 «Requirements for counter
  systems» (folio impreso 24).
- **El impreso:** A.4: «At this height, the field strength level ref.
  400 mA/m at some of the points may be up to, but not greater than,
  **+12 dB**», de las mediciones a 1,45 m, y «For the points in the plan
  view, a **less stringent** requirement is appropriate for a counter
  system». 9.5: «The magnetic field strength level at these points shall be
  ±6 dB ref. 400 mA/m», en «all measurement points specified in Figure 3,
  across both vertical and horizontal ranges», y «The field strength shall
  not be above +8 dB ref. 400 mA/m in the area where people are expected to
  stand».
- **El problema:** la Figura 3 sitúa los puntos del mostrador a 1,2 m,
  1,45 m y 1,7 m, y 9.5 los somete todos a los ±6 dB de un refugio (9.3), con
  el techo de +8 dB en la zona donde se espera que la gente se sitúe, sin
  exceptuar ninguna altura. Nada del apartado normativo es menos exigente para
  un mostrador que para un refugio, y el anexo informativo permite a 1,45 m
  4 dB más de lo que 9.5 permite en cualquier punto. La Modificación 1:2017
  reescribe el capítulo 9 con los mismos límites en su 9.5 y no modifica el
  Anexo A.
- **Evidencia:** los dos pasajes comparados. Verificado en las páginas 26 y
  31 del PDF (pp. 24 y 29 impresas) de BS EN 60118-4:2015, el texto inglés de
  EN 60118-4:2015, que es IEC 60118-4:2014 sin cambios, y en la página 10 del
  PDF (p. 10 impresa) de UNE-EN IEC 60118-4:2016/A1:2018, la edición española
  de IEC 60118-4:2014/A1:2017.
- **Comportamiento de la biblioteca:**
  `electroacoustics.verify_small_volume_system` aplica 9.5 modificado, ±6 dB
  en cada punto de medición y +8 dB en la zona donde se espera que la gente se
  sitúe, a todas las alturas; la fila de conformidad de 9.5 fija los dos
  bordes.
- **Estado:** sin notificar.

## IEC 60118-4:2014, Figura E.2 a) (la línea del campo vertical trazada a lo largo)

- **Ubicación:** Anexo E, Figura E.2 «Strengths of the components of the
  magnetic field due to current in a horizontal rectangular loop at points in
  a plane above or below the loop plane», panel a) (folio impreso 38), frente
  al texto de E.1 que la presenta (folio impreso 36).
- **El impreso:** el panel a) dibuja un bucle «15 units by 10 units» con dos
  líneas discontinuas por su centro. La que va a lo largo de las 15 unidades
  lleva el rótulo «**Vertical** field strength measured along a line parallel
  to this and 1,2 units above or below the loop plane», y la que cruza las
  10 unidades de anchura «**Horizontal** field strength measured along a line
  parallel to this». E.1 dice que «Figure E.2 shows the distribution of the
  vertical component **across** a loop» y que «the horizontal axis gives
  position as a percentage of the loop **width**».
- **El problema:** las dos curvas del panel b) son el recorrido a través de
  las 10 unidades de anchura, como dice E.1, y ninguna es el recorrido a lo
  largo. El campo del bucle, 1,2 unidades por encima y en decibelios respecto
  al campo en su centro y en su plano, da para la componente vertical al 5 %,
  7,5 %, 10 % y 12,5 % de la dimensión $-0{,}3$, $+1{,}1$, $+1{,}7$ y
  $+1{,}9$ dB a través de la anchura, y $+1{,}8$, $+2{,}4$, $+2{,}4$ y
  $+2{,}1$ dB a lo largo; la curva impresa marca en torno a $-0{,}8$,
  $+0{,}8$, $+1{,}5$ y $+1{,}7$ dB, con el máximo cerca del 12,5 %, donde lo
  tiene el campo a través de la anchura, y no cerca del 8,5 %, donde lo tiene
  el campo a lo largo. La componente horizontal dice lo mismo: al $-10$ % es
  $-0{,}1$ dB a través de la anchura y $-4{,}0$ dB a lo largo, y la curva
  marca $-0{,}2$ dB. La línea del campo vertical del panel a) va a través de
  la anchura, sobre la línea rotulada para el campo horizontal.
- **Evidencia:** el campo de Biot-Savart de los cuatro lados del bucle de 15
  por 10 evaluado a lo largo de las dos líneas, frente a las curvas leídas en
  la página sobre su propia cuadrícula. Verificado en las
  páginas 38 y 40 del PDF (pp. 36 y 38 impresas) de BS EN 60118-4:2015, el
  texto inglés de EN 60118-4:2015, que es IEC 60118-4:2014 sin cambios.
- **Comportamiento de la biblioteca:** `electroacoustics.rectangular_loop_field`
  calcula el campo en cualquier punto, y las filas de conformidad de la
  Figura E.2 b) comparan el recorrido a través de la anchura con puntos leídos
  de las dos curvas.
- **Estado:** sin notificar.

## IEC 60118-4:2014, E.6 (la inducción de 1 A/m impresa como 1,256 µT)

- **Ubicación:** Anexo E, E.6 «Magnetic units», la viñeta de la inducción
  magnética (folio impreso 44).
- **El impreso:** «$B = \mu_0\mu_r H$, where $\mu_0$ is the permeability of
  free space ($4\pi \times 10^{-7}$ H/m) [...] the magnetic induction due to a
  field strength of 1 A/m is **1,256 µT**».
- **El problema:** $4\pi \times 10^{-7}\ \mathrm{H/m} \times 1\ \mathrm{A/m} =
  1{,}256\,64\ \mu\mathrm{T}$, que con las cuatro cifras impresas se lee
  **1,257 µT**; el impreso trunca la última cifra en lugar de redondearla. La
  intensidad de campo de 79,58 A/m que la misma viñeta da para un gauss en el
  aire, $10^{-4}\ \mathrm{T}/\mu_0 = 79{,}577$ A/m, está bien redondeada.
- **Evidencia:** $4\pi \times 10^{-7}$ evaluado. Verificado en la página 46
  del PDF (p. 44 impresa) de BS EN 60118-4:2015, el texto inglés de
  EN 60118-4:2015, que es IEC 60118-4:2014 sin cambios.
- **Comportamiento de la biblioteca:**
  `electroacoustics.magnetic_flux_density` multiplica por
  $\mu_0 = 4\pi \times 10^{-7}$ H/m; la fila de conformidad de E.6 lo compara
  con el 1,256 µT impreso con una tolerancia de 0,001 µT y nombra el impreso
  como la errata.
- **Estado:** sin notificar (tipográfico, sin consecuencia numérica).

## IEC 60118-4:2014/A1:2017, 8.4 (remisiones a 10.2.7 que la renumeración deja atrás)

- **Ubicación:** 8.4.1, 8.4.2 y 8.4.3 de IEC 60118-4:2014 (folio impreso
  19), que la Modificación 1:2017 no modifica, frente al capítulo 10 tal como
  lo sustituye la modificación (folios impresos 11 a 13 de la edición
  española).
- **El impreso:** 8.4.1: «The volume within which the requirements
  recommended or specified in Clause 7, 8.2.7, 8.3.7 and **10.2.7** are
  met»; 8.4.2: «See Clause 7, 8.2, 8.3 and **10.2**»; 8.4.3: «the
  requirements in 8.3.7 and **10.2.7** apply». En el texto de 2014, 10.2 es
  «Magnetic noise level due to the system» y 10.2.7 su requisito.
- **El problema:** la Modificación 1 sustituye el texto del capítulo 10. Su
  10.2 es el requisito de la puesta en servicio («Requisitos»), sin 10.2.7, y
  el ruido con el sistema encendido pasa a 10.4, cuyo 10.4.7 lleva palabra
  por palabra la regla del antiguo 10.2.7. La modificación no toca 8.4, así
  que tras ella el volumen de campo magnético útil se define por un apartado
  que ya no existe. Las referencias se leen **10.4.7** y **10.4**.
- **Evidencia:** los títulos del capítulo 10 de los dos textos comparados con
  las remisiones de 8.4. Verificado en las páginas 21 y 26 del PDF (pp. 19 y
  24 impresas) de BS EN 60118-4:2015, el texto inglés de EN 60118-4:2015, que
  es IEC 60118-4:2014 sin cambios, y en las páginas 11 y 13 del PDF (pp. 11 y
  13 impresas) de UNE-EN IEC 60118-4:2016/A1:2018, la edición española de
  IEC 60118-4:2014/A1:2017.
- **Comportamiento de la biblioteca:**
  `electroacoustics.verify_induction_loop_system` juzga el ruido con el
  sistema encendido por 10.4.7 y nombra ese apartado en su veredicto; no hizo
  falta ningún cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 60118-4:2014, 10.2.7, e IEC 60118-4:2014/A1:2017, 10.4.7 (una relación señal-ruido de referencia de 47 dB justos)

- **Ubicación:** 10.2.7 «Requirements» de IEC 60118-4:2014 (folio impreso
  25), y 10.4.7 «Requisitos» de la Modificación 1:2017, que lleva la misma
  regla tras la renumeración (folio impreso 13 de la edición española).
- **El impreso:** 10.2.7: «If the reference signal-to-noise ratio as measured
  in 7.2 is **greater than 47 dB**, the magnetic field strength level at any
  point with the system switched on shall not exceed −47 dB. If the reference
  signal-to-noise ratio is **less than 47 dB** then the magnetic field
  strength level at any point with the system switched on shall not exceed
  that with the system switched off by more than 1 dB.» El 10.4.7 de la
  modificación: «es mayor de 47 dB [...] es menor de 47 dB».
- **El problema:** un emplazamiento cuya relación señal-ruido de referencia
  es de 47 dB justos no cae en ninguna de las dos frases, así que el apartado
  no fija ahí ningún límite al ruido con el sistema encendido, y las dos
  reglas dan límites distintos en ese punto: con el punto más ruidoso a
  −47 dB, la primera limita el ruido del sistema a −47 dB y la segunda a
  −46 dB. El 7.2 solo llama ideal a una relación «greater than 47 dB», lo que
  pone los 47 dB en la rama inferior.
- **Evidencia:** las dos frases de cada edición comparadas. Verificado en la
  página 27 del PDF (p. 25 impresa) de BS EN 60118-4:2015, el texto inglés de
  EN 60118-4:2015, que es IEC 60118-4:2014 sin cambios, y en la página 13 del
  PDF (p. 13 impresa) de UNE-EN IEC 60118-4:2016/A1:2018, la edición española
  de IEC 60118-4:2014/A1:2017.
- **Comportamiento de la biblioteca:**
  `electroacoustics.verify_induction_loop_system` aplica el techo de −47 dB
  solo por encima de 47 dB y la regla de 1 dB a 47 dB y por debajo, y lo dice
  en su docstring.
- **Estado:** sin notificar.

## IEC 62489-1:2010, Tabla B.1 (el perímetro del bucle de mostrador)

- **Ubicación:** Anexo B, Tabla B.1 «Typical loop characteristics» (folio
  impreso 22), la fila «Counter loop».
- **El impreso:** dimensiones «0,35 × 0,45» m, 10 espiras, perímetro
  **1,5** m, sección del conductor 0,75 mm², resistencia 0,37 Ω.
- **El problema:** un rectángulo de 0,35 m por 0,45 m tiene un perímetro de
  $2(0{,}35 + 0{,}45) = 1{,}6$ m, y todas las demás filas imprimen el
  perímetro que dan sus dimensiones: 0,7 m para el diámetro de 0,22 m
  ($\pi \times 0{,}22 = 0{,}69$ m) y 14 m, 28 m, 60 m y 110 m para los cuatro
  rectángulos. La propia resistencia de la fila necesita 1,6 m: con la
  resistividad del cobre recocido patrón a 20 °C, 1/58 Ω·mm²/m (IEC 60028),
  diez espiras de 1,6 m en 0,75 mm² son 0,368 Ω, impresos 0,37, mientras que
  diez espiras de 1,5 m serían 0,345 Ω. La misma resistividad da la
  resistencia impresa de las otras cinco filas a la centésima. El perímetro
  se lee **1,6** m.
- **Evidencia:** $R = \rho N l / a$ evaluada para las seis filas. Verificado
  en la página 24 del PDF (p. 22 impresa) de BS EN 62489-1:2010+A1:2015, el
  texto inglés de EN 62489-1:2010+A1:2015, que es IEC 62489-1:2010 con su
  Modificación 1:2014 sin cambios; la resistividad, en la página 7 del PDF
  (p. 5 impresa) de IEC 60028:1925.
- **Comportamiento de la biblioteca:** `electroacoustics.loop_resistance`
  toma el perímetro, y la fila de conformidad del bucle de mostrador lo
  calcula a partir de los lados, 1,6 m, y nombra el 1,5 m impreso como la
  errata.
- **Estado:** sin notificar.

## IEC 62489-1:2010+A1:2014, 5.4.8.2 a) (la corriente de salida máxima remitida a 5.4.5)

- **Ubicación:** 5.4.8 «Compliance voltage», 5.4.8.2 «Method of
  measurement», paso a) (folio impreso 11).
- **El impreso:** «the loop current is increased to achieve the maximum
  output current as defined in **5.4.5**».
- **El problema:** 5.4.5 es «Rated time for delivery of rated
  distortion-limited output current», un tiempo que declara el fabricante. La
  corriente de salida máxima se define en 5.4.7, «Maximum
  (distortion-limited) output current», como la corriente a 1 kHz que puede
  entregarse durante al menos 10 s a la carga asignada sin superar la
  distorsión armónica total asignada, y el paso c) del mismo apartado la llama
  «the maximum output current, measured in step a)». La referencia se lee
  **5.4.7**. El texto de 2010 imprime la misma remisión con la misma
  numeración; la Modificación 1 no la cambia.
- **Evidencia:** la remisión comparada con los títulos de 5.4.5 y 5.4.7.
  Verificado en las páginas 12 y 13 del PDF (pp. 10 y 11 impresas) de
  BS EN 62489-1:2010+A1:2015, el texto inglés de EN 62489-1:2010+A1:2015, que
  es IEC 62489-1:2010 con su Modificación 1:2014 sin cambios.
- **Comportamiento de la biblioteca:** `electroacoustics.compliance_voltage`
  lee la tensión registrada en la carga, no la corriente, así que no hizo
  falta ningún cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 62489-1:2010+A1:2014, 5.4.14.1 (la caída donde los campos se restan impresa como 0,72 dB)

- **Ubicación:** 5.4.14 «Phase error of quadrature networks for phased loop
  arrays», 5.4.14.1 «Explanation», añadido por la Modificación 1 (folio
  impreso 15).
- **El impreso:** «cos 85° = 0,087, so the in-phase field is increased or
  decreased by **0,72 dB**, depending on where the measurement is taken; in
  some places the fields add; in others they subtract.»
- **El problema:** una componente en fase de 0,087 del campo de referencia
  sube el nivel $20\lg(1 + 0{,}087) = 0{,}72$ dB donde los dos se suman y lo
  baja $20\lg(1 - 0{,}087) = -0{,}79$ dB donde se restan. Las dos cifras no
  son iguales en decibelios, así que el 0,72 dB único es sólo la subida. La
  caída se lee **0,79 dB**.
- **Evidencia:** los dos niveles evaluados a partir del 0,087 impreso.
  Verificado en la página 17 del PDF (p. 15 impresa) de
  BS EN 62489-1:2010+A1:2015, el texto inglés de EN 62489-1:2010+A1:2015, que
  es IEC 62489-1:2010 con su Modificación 1:2014 sin cambios.
- **Comportamiento de la biblioteca:**
  `electroacoustics.QuadraturePhaseError` da la subida y la caída por
  separado, como `level_increase_db` y `level_decrease_db`; las filas de
  conformidad de 5.4.14.1 fijan la subida en el 0,72 dB impreso y la caída en
  $20\lg(1 - \cos 85°) = -0{,}792$ dB, y nombran el impreso como la errata.
- **Estado:** sin notificar.

## IEC 62489-1:2010+A1:2014, F.2.3 (la respuesta objetivo remitida a una Figura 1)

- **Ubicación:** Anexo F, F.2 «Assistive listening device (ALD)», F.2.3
  «Frequency response», añadido por la Modificación 1 (folio impreso 28).
- **El impreso:** «The overall sound-to-electrical output frequency response
  should approximate to the target shown in **Figure 1**.»
- **El problema:** el documento no tiene Figura 1; sus figuras son A.1, E.1 a
  E.4 y F.1. El objetivo que describe la frase siguiente, −3 dB a 350 Hz ±
  50 Hz con una pendiente final de 12 dB/octava y −3 dB a 10 kHz ± 1 kHz con
  una pendiente final de 6 dB/octava, es el que F.1.2 describe con las mismas
  palabras para el receptor de bucle y dibuja en la Figura F.1. La referencia
  se lee **Figura F.1**.
- **Evidencia:** la remisión comparada con F.1.2 y con las figuras que
  contiene el documento. Verificado en las páginas 29 y 30 del PDF (pp. 27 y
  28 impresas) de BS EN 62489-1:2010+A1:2015, el texto inglés de
  EN 62489-1:2010+A1:2015, que es IEC 62489-1:2010 con su Modificación 1:2014
  sin cambios.
- **Comportamiento de la biblioteca:** la biblioteca no implementa los
  receptores del Anexo F, así que no hizo falta ningún cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 61094-5:2016, D.3 (una incertidumbre combinada que sus propias componentes no dan)

- **Ubicación:** Anexo D, apartado D.3 «Combined and expanded uncertainties»
  (folio impreso 21), que combina las ocho componentes de la Tabla D.1 (folio
  impreso 20).
- **El impreso:** «The combined standard uncertainty is found from the
  root-sum-square of the uncertainty components, which gives a value of
  **0,040 dB** [...]. The expanded uncertainty with a coverage factor of 2 is
  then **0,08 dB**.» La Tabla D.1 imprime las ocho incertidumbres típicas
  0,025 (sensibilidad del micrófono de referencia), 0,006 (capacidad), 0,017
  (no linealidad), 0,003 (impedancia), 0,005 (tensión de polarización), 0,025
  (repetibilidad), 0,017 (deriva desde la última calibración) y 0,003
  (redondeo) dB, y D.2 dice que la incertidumbre «arises from eight different
  sources».
- **El problema:** la raíz de la suma de cuadrados de la columna impresa es
  $\sqrt{2 \times 0{,}025^2 + 2 \times 0{,}017^2 + 0{,}006^2 + 0{,}005^2 + 2
  \times 0{,}003^2} = \sqrt{0{,}001\,907} = 0{,}043\,67$ dB, que se lee
  **0,044 dB**, no 0,040 dB; a partir de los valores que cada fila enuncia antes
  de redondear (0,05/2, y 0,01, 0,03, 0,005, $20\lg(200{,}2/200)$, 0,03 y 0,005
  entre $\sqrt{3}$) es 0,043 88 dB. Con $k = 2$ la incertidumbre expandida es
  0,087 dB, **0,09 dB** con los dos decimales que da el apartado, no 0,08 dB.
  El 0,040 dB impreso es la raíz de la suma de cuadrados de siete de las ocho
  componentes, dejando fuera una de las dos filas de 0,017 dB:
  $\sqrt{0{,}001\,907 - 0{,}017^2} = 0{,}040\,2$ dB.
- **Evidencia:** los ocho valores impresos recombinados, y los valores
  enunciados divididos entre sus divisores. Verificado en las páginas 22 y 23
  del PDF (pp. 20 y 21 impresas) de IEC 61094-5:2016, edición 2.0 (2016-05),
  inglés-francés.
- **Comportamiento de la biblioteca:** `metrology.comparison_uncertainty_budget`
  combina las componentes que recibe, 0,0437 dB y 0,087 dB para las de la
  Tabla D.1, y las filas de conformidad de D.3 fijan esos valores con los
  impresos señalados como errata
  ([`tests/metrology/test_comparison_calibration.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_comparison_calibration.py)).
- **Estado:** sin notificar.

## UNE-EN 61094-5:2017, Tabla D.1 y D.3 (seis valores perdidos y la incertidumbre combinada mal impresa en la traducción)

- **Ubicación:** Anexo D, Tabla D.1 «Ejemplo de balance de incertidumbres»
  (pp. 25 y 26 impresas) y D.3 «Incertidumbres combinada y expandida» (p. 27
  impresa) de UNE-EN 61094-5 (febrero de 2017), la versión española de
  EN 61094-5:2016, que adopta IEC 61094-5:2016.
- **El impreso:** la columna «Incertidumbre típica dB» de la Tabla D.1 está
  **vacía** en seis de sus ocho filas, «No linealidad», «Impedancia del
  micrófono», «Voltaje de polarización», «Repetibilidad», «Deriva en la
  sensibilidad del micrófono de referencia desde la última calibración» y
  «Redondeo de los resultados presentados»; sólo las dos primeras filas
  imprimen un valor, 0,025 y 0,006. D.3 dice «lo que da un valor de
  **0,004 dB**». El texto de la primera fila dice «Esto es equivalente a una
  incertidumbre típica de **0,025/2 dB** = 0,025 dB», y el primer caso
  especial habla de «un micrófono de tipo **WG3**».
- **El problema:** el texto inglés imprime los seis valores que la traducción
  pierde, 0,017, 0,003, 0,005, 0,025, 0,017 y 0,003 dB (IEC 61094-5:2016,
  p. 20 impresa), y «0,040 dB» en D.3 (p. 21 impresa), así que el 0,004 dB
  español es la décima parte del valor inglés e incoherente con su propia
  incertidumbre expandida de «0,08 dB» dos líneas más abajo. El texto de la
  fila divide entre 2 los 0,05 dB, no 0,025 dB («0,05/2 dB = 0,025 dB» en el
  inglés), y el caso especial es un micrófono de tipo **WS3**, como dicen el
  inglés, la Tabla A.1 de la misma traducción y el último párrafo del mismo
  caso especial. Quien lea sólo el texto español no puede reconstruir el
  balance: faltan seis de sus ocho componentes, y el valor combinado que
  enuncia no es la suma de nada impreso. El valor combinado inglés es a su vez
  una errata (la entrada sobre IEC 61094-5:2016 D.3, más arriba).
- **Evidencia:** los dos impresos leídos en paralelo. Verificado en las
  páginas 25 a 27 del PDF (pp. 25 a 27 impresas) de UNE-EN 61094-5:2017 y en
  las páginas 22 y 23 del PDF (pp. 20 y 21 impresas) de IEC 61094-5:2016.
- **Comportamiento de la biblioteca:** implementa el texto inglés, cuya Tabla
  D.1 leen los tests y las filas de conformidad; no hizo falta ningún cambio.
- **Estado:** sin notificar (traducción nacional, no el texto del organismo
  emisor).

## IEC 61094-8:2012, 8.4 (una referencia cruzada sin resolver)

- **Ubicación:** subapartado 8.4 «Differences between the sound pressure
  applied to the reference microphone and to the microphone under test»
  (folio impreso 15), su primera frase.
- **El impreso:** «As stated in **Error! Reference source not found.** the
  basis of a comparison method is that the test and reference microphones are
  exposed to a sound field having the same modulus, phase and angle of
  incidence.»
- **El problema:** en lugar de la referencia cruzada se imprimió un campo sin
  resolver del procesador de textos, así que la frase no remite a nada. Lo que
  parafrasea es el principio general de 5.1: «When a calibrated reference
  microphone and a microphone under test are exposed to the same free-field
  sound pressure [...]» (folio impreso 8).
- **Evidencia:** la frase tal como se imprime, leída contra 5.1. Verificado en
  la página 17 del PDF (p. 15 impresa) de BS EN 61094-8:2012, el texto inglés
  de EN 61094-8:2012, que es IEC 61094-8:2012 sin cambios.
- **Comportamiento de la biblioteca:** nada del texto depende de la
  referencia; no hizo falta ningún cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 61094-8:2012, B.2.1 (el rango de frecuencias que se exige a la transformada en el tiempo)

- **Ubicación:** Anexo B, B.2.1 «Outline of method» del método de la
  sinusoide por pasos (folio impreso 25), el párrafo que sigue a las
  Fórmulas (B.2) y (B.3).
- **El impreso:** «The other requirement evident from **Equation B.2** is that
  the frequency range must effectively extend from -∞ to ∞, or 0 to ∞ for a
  single-sided frequency response.» Las fórmulas son, en el folio 24,
  $H(f) = \int_{-\infty}^{\infty} h(t)\exp(-\mathrm{j}2\pi f t)\,\mathrm{d}t$
  (B.2) y
  $h(t) = \int_{-\infty}^{\infty} H(f)\exp(\mathrm{j}2\pi f t)\,\mathrm{d}f$
  (B.3).
- **El problema:** (B.2) integra en el tiempo; la integral en frecuencia, de
  $-\infty$ a $\infty$, es la de (B.3), la transformada inversa que el mismo
  subapartado aplica primero para llevar la respuesta en frecuencia medida al
  dominio del tiempo («an inverse Fourier transform, Equation B.3, can be
  applied to transform this response to the time domain»). La exigencia sobre
  el rango de frecuencias de la medida se desprende de la **Ecuación B.3**.
- **Evidencia:** la variable de integración de las dos fórmulas, leída frente
  al orden en que B.2.1 las aplica. Verificado en las páginas 26 y 27 del PDF
  (pp. 24 y 25 impresas) de BS EN 61094-8:2012, el texto inglés de
  EN 61094-8:2012, que es IEC 61094-8:2012 sin cambios.
- **Comportamiento de la biblioteca:** `metrology.stepped_sine_impulse_response`
  calcula (B.3) y pide la respuesta medida desde 0 Hz, la forma de un solo
  lado del rango que describe la frase; no hizo falta ningún cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 61094-8:2012, B.2.1 (el incremento de frecuencia, al que se atribuye la resolución temporal)

- **Ubicación:** Anexo B, B.2.1 «Outline of method» del método de la
  sinusoide por pasos (folio impreso 25), el párrafo sobre la transformada
  rápida de Fourier.
- **El impreso:** «These require the frequency response to be measured at
  discrete frequencies and linearly spaced frequency increments. The
  frequency increment chosen will determine the **time domain resolution**.»
  El B.2.2, en la misma página: «Because the **length** of the impulse
  response will be the inverse of the size of the frequency step, the size
  of the room will influence the choice of frequency resolution», y fija el
  paso por la duración: 120 Hz «because the primary reflections all occur
  before 8 ms».
- **El problema:** una respuesta medida en $K + 1$ frecuencias $k\,\Delta f$
  desde 0 Hz se transforma en $N = 2K + 1$ muestras separadas
  $1/(N\,\Delta f)$, en torno a $1/(2 f_\mathrm{max})$, a lo largo de una
  duración $1/\Delta f$. El incremento fija la duración de la respuesta al
  impulso, como dice el B.2.2; el paso temporal, la resolución, lo fija el
  rango de frecuencias, que el propio B.2.1 sitúa en «about three times the
  resonance frequency of the microphones». La frase ha de leerse «time domain
  length» o «the length of the time record».
- **Evidencia:** el B.2.1 leído frente al B.2.2 y frente a la transformada
  que aplican los dos. Verificado en la página 27 del PDF (p. 25 impresa) de
  BS EN 61094-8:2012, el texto inglés de EN 61094-8:2012, que es
  IEC 61094-8:2012 sin cambios.
- **Comportamiento de la biblioteca:** `metrology.SteppedSineImpulseResponse`
  sigue el B.2.2: su `duration_s` es $1/\Delta f$ y su `sample_rate_hz` es
  $N\,\Delta f$; no hizo falta ningún cambio.
- **Estado:** sin notificar (defecto de redacción, sin consecuencia
  numérica).

## IEC 61094-8:2012, B.6.1, Fórmula (B.10) (el espectro de un pulso de duración 2b llamado de duración b)

- **Ubicación:** Anexo B, B.6.1 «Outline of methods» del método de excitación
  por impulso directo (folio impreso 28), la Fórmula (B.10) y las frases que
  la rodean.
- **El impreso:** «The Fourier transform, $X(f)$, of a rectangular pulse of
  **duration $b$** and amplitude $a$ is $X(f) = \dfrac{2ab\sin(2\pi f b)}{2\pi
  f b}$ (B.10). The first zero in the spectrum is at $f = 1/(2b)$. [...]
  leading to a requirement for the duration, $b$ of just a few microseconds.»
- **El problema:** la Fórmula (B.10) es la transformada de un pulso de
  amplitud $a$ que dura de $-b$ a $b$, es decir, de duración **$2b$**: su valor
  en $f = 0$ es el área del pulso, $2ab$, y su primer cero, donde $2\pi f b =
  \pi$, está en $1/(2b)$, como dice el texto. Un pulso de duración $b$ tiene la
  transformada $ab \sin(\pi f b)/(\pi f b)$ y su primer cero en $1/b$. La
  fórmula y el primer cero concuerdan entre sí; las palabras «duration $b$»
  discrepan de ambos, y han de leerse «semiduración $b$» o «duración $2b$». La
  conclusión práctica se mantiene con cualquiera de las dos lecturas: un primer
  cero diez veces por encima de un límite superior de 20 kHz, en 200 kHz, pide
  un pulso de 5 µs ($b$ = 2,5 µs según la fórmula), «just a few
  microseconds».
- **Evidencia:** la transformada del pulso rectangular evaluada en frecuencia
  cero y en su primer cero. Verificado en la página 30 del PDF (p. 28 impresa)
  de BS EN 61094-8:2012, el texto inglés de EN 61094-8:2012, que es
  IEC 61094-8:2012 sin cambios.
- **Comportamiento de la biblioteca:** `metrology.rectangular_pulse` sigue la
  fórmula y su primer cero y lee $b$ como la semiduración: toma la duración
  completa $T = 2b$, su `first_zero_hz` es $1/T = 1/(2b)$ y su espectro es
  (B.10) con $b = T/2$. `metrology.rectangular_pulse_duration_s` da
  $T$ = 5 µs para 20 kHz, y las filas de conformidad de B.6.1
  ([`scripts/conformance/domains/comparison_calibration.py`](https://github.com/jmrplens/phonometry/blob/main/scripts/conformance/domains/comparison_calibration.py))
  y los tests fijan el espectro tal como se imprime frente a él
  ([`tests/metrology/test_comparison_phase_impedance_time.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_comparison_phase_impedance_time.py)).
- **Estado:** sin notificar.

## IEC 61094-2:2009, Tablas B.1 y B.2 (un radio impreso con cuatro cifras, un punto decimal y una cifra perdida)

- **Ubicación:** Anexo B, Tabla B.1 «Real part of $Z_{\mathrm{a,C}}$ in
  gigapascal-seconds per cubic metre» (folio impreso 24) y Tabla B.2 «Imaginary
  part of $Z_{\mathrm{a,C}}$» (folio impreso 25), que según B.1 «are intended
  to be used when testing a calculation program based upon Equations B.1 to
  B.3».
- **El impreso:** la primera y la cuarta columna llevan por cabecera
  «$a_\mathrm{t}$ = **0,1667**» (mm). La Tabla B.1 imprime su última entrada,
  20 kHz para el tubo de 100 mm y 0,25 mm de radio, como «**2.021**», con punto
  decimal donde todas las demás entradas de ambas tablas llevan coma, y la
  Tabla B.2 imprime la entrada de 800 Hz del tubo de 100 mm y 0,1667 mm como
  «**–3,89**», con dos decimales donde todas las demás llevan tres.
- **El problema:** las dos columnas de 0,1667 mm se calcularon con un radio de
  1/6 mm, 0,166 67 mm. La impedancia va con la cuarta potencia del radio (B.1),
  así que el redondeo de la cabecera desplaza el resultado un 0,08 %, más que
  la última cifra impresa: las Fórmulas (B.1) a (B.3) en las condiciones de
  referencia dan a 20 Hz 3,013 y 6,029 GPa·s/m³ para los tubos de 50 mm y 100
  mm con 0,1667 mm, y los 3,015 y 6,034 impresos con 1/6 mm. Un programa
  contrastado con la tabla usando el radio tal como está impreso falla la
  prueba por hasta cinco unidades de la última cifra. Los otros dos deslices
  son tipográficos: «2.021» es 2,021, y «–3,89» es la única entrada con dos
  decimales (las fórmulas dan –3,892 con el 1/6 mm de la columna).
- **Evidencia:** las Fórmulas (B.1) a (B.3) evaluadas con el aire del Anexo F a
  23 °C, 101,325 kPa y 50 %, con ambos radios, frente a las columnas impresas.
  Verificado en las páginas 26 y 27 del PDF (pp. 24 y 25 impresas) de BS EN
  61094-2:2009, el texto inglés de EN 61094-2:2009, que es IEC 61094-2:2009 sin
  cambios.
- **Comportamiento de la biblioteca:** `metrology.capillary_tube_impedance`
  toma el radio que se le da; los tests y las filas de conformidad sobre las
  Tablas B.1 y B.2 pasan 1/6 mm para las columnas encabezadas 0,1667 mm y leen
  «2.021» y «–3,89» como los números que escriben
  ([`tests/metrology/test_reciprocity_coupler.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_reciprocity_coupler.py)).
- **Estado:** sin notificar.

## IEC 61094-3:2016, Fórmulas (8) y (9) (el factor −j de la Fórmula (7) perdido)

- **Ubicación:** 5.7.1 «Method using three microphones», Fórmula (8) (folio
  impreso 11), y 5.7.2 «Method using two microphones and an auxiliary sound
  source», Fórmula (9) (folio impreso 12); la Fórmula (7), a partir de la cual
  se construyen ambas, está en el folio 11.
- **El impreso:** Fórmula (7):
  $\underline{M}_{\mathrm{f},1}\underline{M}_{\mathrm{f},2} =
  -\mathrm{j}\,\dfrac{2d_{12}}{\rho
  f}\,\dfrac{\underline{U}_2}{\underline{i}_1}\,\mathrm{e}^{\mathrm{j}kd_{12}}\,\mathrm{e}^{\alpha
  d_{\mathrm{m}12}}$. Fórmula (8): $\underline{M}_{\mathrm{f},1} =
  \left(\dfrac{2}{\rho
  f}\,\dfrac{d_{12}d_{31}}{d_{23}}\,\dfrac{\underline{Z}_{\mathrm{e},12}\underline{Z}_{\mathrm{e},31}}{\underline{Z}_{\mathrm{e},23}}\,\mathrm{e}^{\mathrm{j}k(d_{12}+d_{31}-d_{23})}\,\mathrm{e}^{\alpha(d_{\mathrm{m}12}+d_{\mathrm{m}31}-d_{\mathrm{m}23})}\right)^{1/2}$,
  presentada como «the final expression for the **complex** free-field
  sensitivity». Fórmula (9): $\underline{M}_{\mathrm{f},1} =
  \left(\underline{r}_{12}\,\dfrac{2d_{12}}{\rho
  f}\,\underline{Z}_{\mathrm{e},12}\,\mathrm{e}^{\mathrm{j}kd_{12}}\,\mathrm{e}^{\alpha
  d_{\mathrm{m}12}}\right)^{1/2}$, que COR1 convierte en «the final expression
  for the complex free-field sensitivity» en lugar de «the modulus of the».
- **El problema:** la Fórmula (8) es el cociente
  $\underline{M}_{\mathrm{f},1}^2 =
  (\underline{M}_{\mathrm{f},1}\underline{M}_{\mathrm{f},2})(\underline{M}_{\mathrm{f},3}\underline{M}_{\mathrm{f},1})/(\underline{M}_{\mathrm{f},2}\underline{M}_{\mathrm{f},3})$
  de tres productos de la forma (7), y lleva
  $(-\mathrm{j})(-\mathrm{j})/(-\mathrm{j}) = -\mathrm{j}$; la Fórmula (9) es
  $\underline{r}_{12}$ por un producto, y lleva también $-\mathrm{j}$. Ambas lo
  pierden. El módulo no se ve afectado, por eso la omisión no hacía daño
  mientras (9) daba solo el módulo; la sensibilidad compleja de las fórmulas
  impresas tiene la fase errada en $\arg(-\mathrm{j})/2 = -45°$ a todas las
  frecuencias. La Fórmula (D.1), «obtained from re-arranging Formula (7)», conserva el
  factor ($\mathrm{j}\rho f/2d_{12}$), así que las (8) y (9) impresas son
  además incoherentes con el anexo que extiende sus datos.
- **Evidencia:** los productos de la Fórmula (7) multiplicados y divididos como
  prescriben (8) y (9), y la Fórmula (D.1) leída frente a (7). Verificado en
  las páginas 13, 14 y 29 del PDF (pp. 11, 12 y 27 impresas) de IEC
  61094-3:2016, Edición 2.0 (2016-06), inglés-francés, con IEC
  61094-3:2016/COR1:2016 (2016-12).
- **Comportamiento de la biblioteca:** `metrology.free_field_reciprocity` y
  `metrology.free_field_reciprocity_pair` conservan el factor $-\mathrm{j}$ de
  la Fórmula (7); impedancias de transferencia eléctricas construidas con la
  Fórmula (D.1) a partir de sensibilidades complejas conocidas las devuelven
  exactamente, cosa que las fórmulas impresas no harían
  ([`tests/metrology/test_reciprocity_free_field.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_reciprocity_free_field.py)).
- **Estado:** sin notificar.

## IEC 61094-3:2016, B.2 Paso 1 (un coeficiente de la presión de vapor de saturación mal impreso)

- **Ubicación:** Anexo B, B.2 «Calculation procedure», Paso 1 (folio impreso
  20), que determina la presión de saturación del vapor de agua «(see also IEC
  61094-2:2009, F.2)».
- **El impreso:** $p_\mathrm{sv}(t) = \exp(1{,}237\,884\,7\cdot10^{-5}\cdot T^2 -
  1{,}912\,131\,6\cdot10^{-2}\cdot T + 33{,}937\,110\,47 -
  \mathbf{6{,}3343\,184\,5}\cdot10^3\cdot T^{-1})$. La Tabla F.2 de IEC
  61094-2:2009 (folio impreso 41), a la que remite el paso, imprime los mismos
  cuatro coeficientes con el último como $a_3 = \mathbf{-6{,}343\,164\,5}\times10^3$.
- **El problema:** las cifras están traspuestas y mal agrupadas: 6 334,318 45
  frente a 6 343,164 5. Los tres primeros coeficientes coinciden con la Tabla
  F.2 hasta la última cifra, y el valor de la Tabla F.2 es el de la fórmula
  CIPM-2007 que cita F.2 de IEC 61094-2. Con el coeficiente impreso, la presión
  de vapor de saturación a 23 °C es 2 896,1 Pa en lugar de 2 810,9 Pa, un 3,0 %
  alta, y la atenuación del Paso 5 se desplaza hasta 0,028 dB/m (3,2 %) en las
  nueve condiciones de la Tabla B.1.
- **Evidencia:** los dos impresos leídos uno junto a otro, y la presión de
  vapor de saturación y la atenuación calculadas con cada uno. Verificado en la
  página 22 del PDF (p. 20 impresa) de IEC 61094-3:2016, Edición 2.0 (2016-06),
  inglés-francés, y en la página 43 del PDF (p. 41 impresa) de BS EN
  61094-2:2009, el texto inglés de EN 61094-2:2009, que es IEC 61094-2:2009 sin
  cambios.
- **Comportamiento de la biblioteca:** `metrology.reciprocity_air_attenuation`
  calcula el Paso 1 con el coeficiente de la Tabla F.2, así que su fracción
  molar de vapor de agua es la de `fluids.air`; una fila de conformidad fija
  esa igualdad
  ([`tests/metrology/test_reciprocity_free_field.py`](https://github.com/jmrplens/phonometry/blob/main/tests/metrology/test_reciprocity_free_field.py)).
- **Estado:** sin notificar.

## UNE-EN ISO 9614-1:2010, apartado 9.1 (el signo perdido de «signed magnitude» en la traducción)

- **Ubicación:** apartado 9.1, la lista de símbolos bajo la Fórmula (11)
  $P_i = I_{\mathrm{n}i} \cdot S_i$, de UNE-EN ISO 9614-1 (marzo de 2010),
  que se declara «la versión en español de la Norma Europea EN ISO
  9614-1:2009», la adopción europea de ISO 9614-1:1993.
- **El impreso:** «$I_{\mathrm{n}i}$ es el **módulo** de la componente de la
  intensidad acústica normal medida en la posición $i$ sobre la superficie de
  medida». El original ISO lee «$I_{\mathrm{n}i}$ is the **signed
  magnitude** of the normal sound intensity component measured at position
  $i$ on the measurement surface».
- **El problema:** *módulo* es el valor absoluto, así que el calificador que
  llevaba el signo ha desaparecido, y el signo es de lo que depende el resto
  del método. El impreso español se contradice entonces dos veces. El mismo
  apartado 9.1 da, dos párrafos por debajo de esa línea, la conversión a
  aplicar cuando el nivel de una posición se escribe $(-)\,XX$ dB:
  $I_{\mathrm{n}i} = -I_0 \times 10^{XX/10}$, un $I_{\mathrm{n}i}$ negativo.
  El apartado 3.6.1, que define la mismísima cantidad que la Fórmula (11)
  calcula, llama a $I_{\mathrm{n}i}$ «la componente normal, **con su signo**,
  de la intensidad acústica medida en la posición $i$», y A.2.3 lo llama «el
  **valor algebraico** de la componente de intensidad acústica normal». Y el
  apartado 9.2 hace de que $\sum_i P_i$ *sea negativa* la condición que deja
  una banda de frecuencia fuera del método, cosa que ninguna suma de módulos
  y áreas positivas puede ser jamás. Leído como módulo, el método pierde lo
  único para lo que sirve medir en puntos discretos: separar la energía que
  sale de la fuente de la energía que vuelve a entrar por parte de la
  superficie, que es lo que $F_3$ (Fórmulas (A.6) y (A.7)) y $F_4$ (Fórmulas
  (A.8) y (A.9)) están construidos para cuantificar desde la media algebraica
  del mismo $I_{\mathrm{n}i}$.
- **Evidencia:** los dos impresos de la misma lista de símbolos, puestos lado
  a lado, y los tres apartados españoles leídos unos contra otros. Páginas
  10, 18 y 22 del PDF (pp. 10, 18 y 22 impresas) de UNE-EN ISO 9614-1:2010;
  página 12 del PDF (p. 7 impresa) de ISO 9614-1:1993, donde el calificador
  está presente.
- **Comportamiento de la biblioteca:** implementa la lectura con signo en
  todo el recorrido, que es el texto ISO.
  [`sound_power_intensity_points`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  suma potencias parciales con signo, marca las bandas cuya suma no es
  positiva como fuera del método, y reporta $F_3 - F_2$ como el exceso que
  produce el flujo entrante; `normal_intensity_from_levels` lleva el $(-)$
  del impreso como argumento separado, porque el nivel impreso nunca lo
  contiene. Fijado por
  `test_a_genuinely_negative_partial_power_is_kept_and_summed` y los tests de
  conversión con signo en
  [`tests/emission/test_sound_power_intensity_points.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_intensity_points.py).
- **Estado:** sin notificar (traducción nacional, no el texto del organismo
  emisor: un lector que trabaje desde la edición ISO no tiene nada que
  sortear).

## UNE-EN ISO 9614-1:2010, apartado A.2.3 (barras de módulo sobre el nivel de intensidad algebraico)

- **Ubicación:** Anexo A, apartado A.2.3, la lista «donde» bajo la Fórmula
  (A.6) $F_3 = \overline{L_p} - \overline{L_{I_\mathrm{n}}}$.
- **El impreso:** la segunda entrada de la lista está compuesta
  $\overline{L_{|I_\mathrm{n}|}}$, con las barras de valor absoluto, y lee
  «es el valor algebraico del nivel de intensidad acústica superficial, en
  decibelios, calculado a partir de la ecuación (A.7)». La Fórmula (A.7),
  tres líneas más abajo en la misma página, está etiquetada
  $\overline{L_{I_\mathrm{n}}}$, sin las barras.
- **El problema:** el símbolo con barras es el de A.2.2, el nivel del
  *módulo* medio de la Fórmula (A.5), que es exactamente lo que resta $F_2$.
  Con las barras, $F_3$ y $F_2$ serían el mismo indicador y todo A.2.3 sería
  redundante; la frase junto al símbolo dice «valor algebraico» y apunta a
  (A.7), que toma la media algebraica. El original ISO imprime la misma
  entrada sin las barras y la describe como «the surface normal signed
  intensity level», así que las barras son composición propia de la
  traducción.
- **Evidencia:** el símbolo tal como está compuesto en las dos ediciones, y
  la (A.7) sin barras en la misma página que la entrada con barras. Página 22
  del PDF (p. 22 impresa) de UNE-EN ISO 9614-1:2010; página 15 del PDF (p. 10
  impresa) de ISO 9614-1:1993.
- **Comportamiento de la biblioteca:** no hizo falta ninguno.
  `field_indicators` en
  [`intensity.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/intensity.py) forma $F_3$ desde
  la media algebraica de la Fórmula (A.7) y $F_2$ desde el módulo medio de la
  Fórmula (A.5), que es lo que hace de $F_3 - F_2$ el exceso de flujo
  entrante sobre el que está escrita la compuerta del Anexo B. Registrado
  como defecto de etiqueta.
- **Estado:** sin notificar (traducción nacional, no el texto del organismo
  emisor).

## ISO 9614-1:1993, apartado B.1.3 ($F_4$ remitido a A.2.3, que define $F_3$)

- **Ubicación:** Anexo B, apartado B.1.3, la frase que introduce las dos
  evaluaciones separadas de $F_4$ que consume la Fórmula (B.4).
- **El impreso:** «Calculate indicator $F_4$ separately according to
  **A.2.3**», sobre los dos puntos «a) for the segment subset $N_\alpha$
  having total area $S_\alpha$, and» y «b) for the remaining segments». La
  edición española reproduce el mismo número de apartado: «Calcular el
  indicador $F_4$ separadamente de acuerdo al apartado A.2.3 para: a) el
  subconjunto de segmentos $N_\alpha$ con área total $S_\alpha$, y b) los
  segmentos restantes.»
- **El problema:** A.2.3 es «Negative partial power indicator», que define
  $F_3$ por las Fórmulas (A.6) y (A.7). $F_4$ es A.2.4, «Field
  non-uniformity indicator», Fórmulas (A.8) y (A.9). Seguida tal como está
  impresa, la referencia calcula el indicador equivocado para $F_4(\alpha)$ y
  $F_4(1-\alpha)$, y esos son los que dimensionan las posiciones nuevas en la
  Fórmula (B.4). Ambas ediciones llevan la misma numeración de apartados, así
  que el defecto es del organismo emisor.
- **Evidencia:** la referencia y los títulos de A.2.3 y A.2.4 leídos uno
  contra otro. Páginas 18 y 15 a 16 del PDF (pp. 13 y 10 a 11 impresas) de
  ISO 9614-1:1993; la misma frase en la página 24 del PDF (p. 24 impresa) de
  UNE-EN ISO 9614-1:2010.
- **Comportamiento de la biblioteca:** sigue el destino pretendido.
  $F_4(\alpha)$ y $F_4(1-\alpha)$ se calculan según A.2.4 en
  [`partial_power_concentration`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py).
  La referencia no cambia ningún número que la biblioteca reporte, así que no
  hizo falta ningún otro cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## UNE-EN ISO 9614-1:2010, apartado 10.5 c) (un número de ecuación sustituido por un capítulo que no existe)

- **Ubicación:** apartado 10.5 c), «Datos acústicos», el requisito de informe
  que acompaña al nivel de una banda que no satisface el criterio 2.
- **El impreso:** «Una referencia a la incertidumbre prevista en el nivel de
  potencia acústica determinada para cada banda de frecuencia en la que no se
  satisfaga el criterio 2 del anexo B, **de acuerdo a la ecuación (véase el
  capítulo B.3)**.» El original ISO lee «A statement of the predicted
  uncertainty in the sound power level determined for each frequency band, in
  which criterion 2 of annex B is not satisfied, **according to equation
  (B.3)**.»
- **El problema:** el número que identificaba la ecuación se ha convertido en
  una referencia cruzada y ha cambiado por el camino. «De acuerdo a la
  ecuación ( )» no nombra ecuación alguna, y lo que el paréntesis nombra en
  su lugar no forma parte del documento: el Anexo B se divide en B.1, con
  B.1.1 a B.1.5, y B.2, y ahí se acaba, así que no hay capítulo B.3 que
  consultar. El requisito es inutilizable tal como está impreso a menos que
  el lector reconozca la Fórmula (B.3), el intervalo de confianza del 95 %
  $10 \lg (1 \pm 2 F_4 / \sqrt{N})$, que el apartado B.1.2 introduce con esta
  misma condición adjunta.
- **Evidencia:** los dos impresos del mismo punto, y las divisiones del Anexo
  B según corren sus títulos. Páginas 20 y 23 a 26 del PDF (pp. 20 y 23 a 26
  impresas) de UNE-EN ISO 9614-1:2010; página 14 del PDF (p. 9 impresa) de
  ISO 9614-1:1993, donde el número de ecuación está presente.
- **Comportamiento de la biblioteca:** reporta el intervalo de la Fórmula
  (B.3) para todas las bandas, así que la declaración que pide el apartado
  10.5 c) puede hacerse sobre cualquier banda que la necesite.
  `confidence_interval` en
  [`DiscretePointIntensityResult`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  lleva el par, y `criterion_2` dice a qué bandas aplica el requisito. El
  defecto no cambia ningún número, solo adónde se manda al lector a buscar la
  fórmula.
- **Estado:** sin notificar (traducción nacional, no el texto del organismo
  emisor).

## ISO 9614-1:1993, Tabla B.3 (las acciones c y d reclaman ambas $F_3 - F_2 = 1$ dB)

- **Ubicación:** Tabla B.3, «Actions to be taken to increase grade of
  accuracy of determination», las celdas de criterio de las filas de las
  acciones c y d.
- **El impreso:** la acción c está condicionada a «Criterion 2 not satisfied
  and 1 dB $\leq (F_3 - F_2) \leq$ 3 dB»; la acción d a «Criterion 2 not
  satisfied and $(F_3 - F_2) \leq$ 1 dB, and the procedure of 8.3.2 either
  fails or is not selected». Ambas desigualdades están impresas no estrictas,
  en las dos ediciones.
- **El problema:** las dos filas se solapan exactamente en
  $F_3 - F_2 = 1$ dB, donde la tabla prescribe dos acciones distintas para un
  mismo estado: aumentar la densidad de posiciones uniformemente (c), o
  alejar la superficie y conservar las posiciones (d). Una tabla de decisión
  normativa no es implementable mientras eso se mantenga. El documento lo
  zanja en otro lugar: el quinto rombo de decisión de la Figura B.1 es
  «$(F_3 - F_2) \leq$ 1 dB ?», y su rama **Yes** es la que lleva al
  procedimiento opcional y a la acción d, así que 1 dB pertenece a d y c
  empieza por encima. El apartado 8.3.2 concuerda, abriendo el procedimiento
  opcional «if $F_3 - F_2 \leq$ 1 dB».
- **Evidencia:** las dos celdas de criterio, el rombo y sus ramas, y la
  condición del apartado 8.3.2. Páginas 19, 20 y 12 del PDF (pp. 14, 15 y 7
  impresas) de ISO 9614-1:1993; los mismos tres lugares en las páginas 26, 27
  y 17 del PDF (pp. 26, 27 y 17 impresas) de UNE-EN ISO 9614-1:2010.
- **Comportamiento de la biblioteca:** sigue la Figura B.1 y el apartado
  8.3.2. `required_actions` en
  [`DiscretePointIntensityResult`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  responde a una banda que falla el criterio 2 con la acción c por encima de
  1 dB y la acción d a 1 dB y por debajo, fijado en el propio límite por
  `test_action_d_is_the_action_at_exactly_one_decibel` en
  [`tests/emission/test_sound_power_intensity_points.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_intensity_points.py).
- **Estado:** sin notificar.

## ISO 9614-1:1993, ecuaciones (A.1) y (A.8) (la intensidad normalizadora sin su barra)

- **Ubicación:** Anexo A, apartado A.2.1, ecuación (A.1) del indicador de
  variabilidad temporal $F_1$, y apartado A.2.4, ecuación (A.8) del indicador
  de no uniformidad del campo $F_4$.
- **El impreso:** ambas ecuaciones abren con el factor $1/I_\mathrm{n}$, un
  símbolo sin barra, mientras que la desviación dentro de la suma está
  escrita contra un $\overline{I_\mathrm{n}}$ claramente con barra:
  $F_1 = \frac{1}{I_\mathrm{n}} \sqrt{\frac{1}{M-1}\sum_k (I_{\mathrm{n}k} -
  \overline{I_\mathrm{n}})^2}$ y
  $F_4 = \frac{1}{I_\mathrm{n}} \sqrt{\frac{1}{N-1}\sum_i (I_{\mathrm{n}i} -
  \overline{I_\mathrm{n}})^2}$. Las dos ediciones las componen igual.
- **El problema:** las listas de símbolos que siguen definen solo el de la
  barra («$\overline{I_\mathrm{n}}$ is the mean value of $I_\mathrm{n}$ for
  $M$ short-time-average samples», A.2.1; «$\overline{I_\mathrm{n}}$ is the
  surface normal sound intensity calculated from equation (A.9)», A.2.4). El
  $I_\mathrm{n}$ sin barra es la intensidad normal en un punto del apartado
  3.4, así que tal como está impreso un coeficiente de variación se divide
  por un valor único sin especificar en lugar de por la media en torno a la
  cual se toma su propio numerador. Ambos indicadores son coeficientes de
  variación y no admiten otra normalización.
- **Evidencia:** las dos ecuaciones y las listas de símbolos bajo ellas,
  donde la barra falta sobre el divisor y está intacta sobre el símbolo de
  dentro de la suma. Páginas 15 y 16 del PDF (pp. 10 y 11 impresas) de
  ISO 9614-1:1993; las mismas dos ecuaciones en las páginas 21 y 22 del PDF
  (pp. 21 y 22 impresas) de UNE-EN ISO 9614-1:2010.
- **Comportamiento de la biblioteca:** no hizo falta ninguno. El coeficiente
  de variación tras `field_indicators` y `temporal_variability_indicator` en
  [`intensity.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/intensity.py) divide por la
  media algebraica, y rechaza una media que no sea positiva en lugar de
  dividir por ella. Registrado como defecto tipográfico.
- **Estado:** sin notificar (tipográfico).

## UNE-EN ISO 9614-1:2010, Nota 11 del apartado B.1.3 (la mitad de un nivel, y una recomendación vuelta requisito)

- **Ubicación:** Nota 11, inmediatamente después del bloque de la Fórmula
  (B.4) del apartado B.1.3, que matiza la elección del factor $C$ de la Tabla
  B.2 para una determinación ponderada A.
- **El impreso:** «Si la contribución total al **nivel de** potencia acústica
  ponderado A de las bandas de tercio de octava en el margen de frecuencias
  de 800 Hz a 5 000 Hz es menos de la mitad del **nivel total**, entonces
  **deben** usarse los valores de $C$ para las bandas de tercio de octava de
  200 Hz a 630 Hz.» El original ISO lee «If the total contribution to the
  A-weighted sound **power** from the one-third-octave bands in the frequency
  range 800 Hz to 5 000 Hz is less than half the total **power**, then the
  values of $C$ for the one-third-octave band 200 Hz to 630 Hz **should** be
  used.»
- **El problema:** dos desviaciones en una frase. La mitad de un *nivel* no
  es una operación definida, así que el impreso español declara una condición
  que no puede evaluarse tal como está escrita; el original condiciona sobre
  la mitad de la *potencia*, que es una contribución 3 dB o más por debajo
  del total y es decidible. Y *should*, una recomendación bajo las reglas de
  redacción ISO/IEC, se convierte en *deben*, que se lee como requisito, así
  que los dos impresos ni siquiera coinciden en si la sustitución es
  opcional.
- **Evidencia:** los dos impresos de la misma nota. Página 25 del PDF (p. 25
  impresa) de UNE-EN ISO 9614-1:2010; página 18 del PDF (p. 13 impresa) de
  ISO 9614-1:1993.
- **Comportamiento de la biblioteca:** implementa la lectura en potencia, y
  aplica la sustitución siempre que la condición se cumple en lugar de
  dejarla al llamante, lo que satisface ambos impresos. `_a_weighted_factor`
  en
  [`sound_power_intensity_points.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_intensity_points.py)
  compara la contribución ponderada A sumada de las bandas de 800 Hz a 5 kHz
  con la mitad de la contribución total y lee la fila de 200 Hz a 630 Hz de
  la Tabla B.2 cuando se queda corta.
- **Estado:** sin notificar (traducción nacional, no el texto del organismo
  emisor).

## ISO 3744:2010, 8.3.4, Ecuación (21) (un nivel integrado en el tiempo comparado con uno promediado en el tiempo)

- **Ubicación:** apartado 8.3.4, Ecuación (21) y la lista de símbolos que la
  sigue (página 31 del PDF, p. 25 impresa) de ISO 3744:2010, leída contra las
  definiciones de los apartados 3.3 y 3.4 (página 9 del PDF, p. 3 impresa). La
  misma construcción se imprime como Ecuación (25) de ISO 3741:2010 (página 33
  del PDF, p. 24 impresa, con su lista de símbolos en la página 34 del PDF,
  p. 25 impresa), como Ecuación (14) de ISO 3747:2010 (páginas 22 y 23 del
  PDF, pp. 13 y 14 impresas), como Ecuación (19) de ISO 3743-1:2010 en su
  apartado 8.2.3 (página 25 del PDF, p. 16 impresa) y como Ecuación (15) de
  ISO 3746:2010 en su apartado 8.4.2 (página 25 del PDF, p. 16 impresa), que
  es la vía de grado *survey* que toma la biblioteca con `grade='survey'`.
- **El impreso:** $K_1 = -10 \lg\left(1 - 10^{-0{,}1\,\Delta L_E}\right)$ dB
  con $\Delta L_E = \overline{L'_{E(\mathrm{ST})}} - \overline{L_{p(\mathrm{B})}}$,
  donde $\overline{L'_{E(\mathrm{ST})}}$ «is the mean frequency-band or
  A-weighted single event time-integrated sound pressure level» y
  $\overline{L_{p(\mathrm{B})}}$ «is the mean frequency-band or A-weighted
  time-averaged sound pressure level of the background noise», seguido de
  «The integration time $T = t_2 - t_1$ and other measurement parameters shall
  be the same for the measurement of the single event time-integrated sound
  pressure level $L'_{Ei(\mathrm{ST})}$ and of the background noise level
  $L_{pi(\mathrm{B})}$.»
- **El problema:** los dos niveles no comparten magnitud de referencia, y la
  corrección resta una energía de otra. Por el apartado 3.4, $L_E$ es
  $\int_{t_1}^{t_2} p^2\,\mathrm{d}t$ re $E_0 = (20\ \mu\text{Pa})^2\,\text{s}$;
  por el apartado 3.3, $L_{p,T}$ es $\frac{1}{T}\int_{t_1}^{t_2} p^2\,\mathrm{d}t$
  re $p_0^2$. Su diferencia es un cociente de energías solo cuando $T = 1$ s.
  Sobre el intervalo común $T$ el fondo aporta la energía
  $L_{p(\mathrm{B})} + 10 \lg(T/T_0)$ (la identidad de la NOTA 1 del apartado
  3.4), así que el $\Delta L_E$ impreso supera al cociente de energías
  señal-fondo en $10 \lg(T/T_0)$ y $K_1$ se subestima para todo $T > 1$ s: una
  ráfaga cuya energía está 6 dB por encima de la del fondo en un intervalo de
  10 s se lee 16 dB por encima y no recibe corrección, donde el criterio de
  8.2.3 sitúa $K_1$ en su mayor valor admisible, 1,3 dB. La cadena gemela de
  8.2, donde ambos niveles están promediados en el tiempo, no tiene ese
  término, y 8.3.3 exige promediar los niveles de suceso aislado «in the same
  way as for the time-averaged sound pressure levels described in 8.2.2», así
  que la lectura pretendida es aquella bajo la cual las dos cadenas coinciden
  para una fuente estacionaria durante $T$, $L_J = L_W + 10 \lg(T/T_0)$, y es
  la lectura bajo la cual la insistencia en un único tiempo de integración
  para ambas mediciones sirve de algo.
- **Evidencia:** Verificado en la página 31 del PDF (p. 25 impresa) de
  ISO 3744:2010 para la ecuación y su lista de símbolos, y en la página 9 del
  PDF (p. 3 impresa) para las definiciones de los apartados 3.3 y 3.4 con la
  NOTA 1; la misma construcción leída en las páginas 33 y 34 del PDF (pp. 24 y
  25 impresas) de BS EN ISO 3741:2010, en las páginas 22 y 23 del PDF (pp. 13
  y 14 impresas) de BS EN ISO 3747:2010 y en la página 25 del PDF (p. 16
  impresa) de BS EN ISO 3743-1:2010.
- **Comportamiento de la biblioteca:** `sound_energy_pressure`,
  `sound_energy_reverberation` y `sound_energy_comparison` comparan el fondo
  como su exposición sobre el mismo intervalo,
  $L_{p(\mathrm{B})} + 10 \lg(T/T_0)$, y exigen `integration_time` con el fondo
  de la fuente bajo ensayo, que es el que se compara contra un nivel de suceso.
  La fuente de referencia de `sound_energy_comparison` es estacionaria, así que
  `background_levels_ref` se corrige con la regla promediada en el tiempo de
  9.1.2 y no lleva ventana; los criterios y el tope de 8.2.3 (y de 9.1.2 en ISO 3741) se
  aplican entonces a ese margen. `tests/emission/test_sound_energy.py` fija
  $K_1 = 1{,}2563$ dB para una ráfaga de 78 dB sobre un fondo de 62 dB en una
  ventana de 10 s, y $L_J = L_W + 10 \lg(T/T_0)$ campo a campo en ambas
  familias; el informe de conformidad lleva la identidad como «ISO 3744:2010
  Eq. 23 / clause 3.4 NOTE 1». `sound_energy_hard_walled` lee la Ecuación (19)
  de ISO 3743-1:2010 del mismo modo y exige `integration_time_s` con el fondo;
  `test_steady_source_energy_is_power_plus_10_lg_t` en
  `tests/emission/test_sound_power_hard_walled.py` y la comprobación de
  conformidad «ISO 3743-1:2010 Eq. 20 / clause 3.4 NOTE 1» fijan allí la
  identidad.
- **Estado:** sin notificar.

## ISO 3744:2010, 8.3.4 (la corrección llamada K_1i en el texto y K_1 en la Ecuación (21))

- **Ubicación:** apartado 8.3.4, primera frase y Ecuación (21) (página 31 del
  PDF, p. 25 impresa).
- **El impreso:** «The background noise correction, $K_{1i}$, shall be
  calculated using Equation (21):» seguido de
  $K_1 = -10 \lg\left(1 - 10^{-0{,}1\,\Delta L_E}\right)$ dB con $\Delta L_E$
  formado a partir de las dos medias sobre la superficie de medición,
  $\overline{L'_{E(\mathrm{ST})}}$ y $\overline{L_{p(\mathrm{B})}}$.
- **El problema:** la frase nombra una corrección por posición y la ecuación
  define una sola a partir de medias superficiales. El apartado gemelo 8.2.3
  nombra $K_1$ en ambos sitios y lo forma a partir de las mismas medias
  superficiales (Ecuación (16)), y 8.3.5 resta el $K_1$ sin subíndice en la
  Ecuación (22). El subíndice es la convención por micrófono de los apartados
  9.1.2 y 9.2.2 de ISO 3741:2010 ($K_{1i}$, Ecuaciones (14) y (25)), donde
  cada posición se corrige antes del promedio, y no pertenece a este
  apartado.
- **Evidencia:** Verificado en la página 31 del PDF (p. 25 impresa) de
  ISO 3744:2010, contra el apartado 8.2.3 en la página 29 del PDF (p. 23
  impresa).
- **Comportamiento de la biblioteca:** `sound_energy_pressure` forma un $K_1$
  por banda a partir de las medias superficiales, tal como lo imprime la
  Ecuación (21) y como hace `sound_power_pressure` con la Ecuación (16); no se
  aplica ninguna corrección por posición en la cadena de ISO 3744. No hizo
  falta ningún cambio.
- **Estado:** sin notificar.

## ISO 3745:2012/Amd.1:2017, A.2.4 frente a A.4.3 (dos resoluciones espaciales para un mismo recorrido)

- **Ubicación:** A.2.4 del anexo A de sustitución (página 7 del PDF, p. 3
  impresa) y A.4.3 del mismo anexo (página 9 del PDF, p. 5 impresa) de
  ISO 3745:2012/Amd.1:2017, leídos frente a ISO 26101:2017, A.4.3 (página 17
  del PDF, p. 11 impresa).
- **El impreso:** A.2.4 dice «Within each qualified radius, each microphone
  traverse shall meet the requirements for traverse length of
  ISO 26101:2017, 5.1.4.3 and for spatial resolution of ISO 26101:2017,
  A.4.3.» El A.4.3 de ISO 26101:2017 dice «The spacing shall not exceed
  one-tenth of a wavelength at each frequency of interest below 1 kHz and
  shall not exceed 25 mm at frequencies above 1 kHz.» El A.4.3 de la propia
  modificación dice «The spacing between points shall not exceed a tenth of a
  wavelength at each frequency of interest below 250 Hz and shall not exceed
  100 mm at frequencies above 250 Hz», y su último párrafo recomienda más
  puntos «If a 100 mm spatial resolution traverse indicates» una desviación
  dentro del 10 % del criterio.
- **El problema:** el anexo fija dos resoluciones espaciales para el mismo
  recorrido, las dos con «shall». Entre 250 Hz y 1 kHz la décima de longitud
  de onda de ISO 26101 (de 137 mm a 34 mm a 343 m/s) es más holgada que
  100 mm hasta 343 Hz y más estricta por encima, y por encima de 1 kHz
  ISO 26101 pide 25 mm donde A.4.3 permite 100 mm. Un recorrido muestreado a
  los 100 mm que A.4.3 permite, y que su último párrafo da por supuestos,
  incumple la resolución que exige A.2.4 en todas las frecuencias por encima
  de 343 Hz. El anexo de 2012 tenía una sola regla. Cuál de las dos pretende la
  modificación no se puede decidir con su texto.
- **Evidencia:** Verificado en la página 7 del PDF (p. 3 impresa) y en la
  página 9 del PDF (p. 5 impresa) de ISO 3745:2012/Amd.1:2017, y en la
  página 17 del PDF (p. 11 impresa) de ISO 26101:2017.
- **Comportamiento de la biblioteca:** `check_free_field` juzga las dos y
  informa de cada una por separado: `spacing_met` recoge el A.4.3 modificado e
  `iso26101_spacing_met` el A.4.3 de ISO 26101 que cita A.2.4, y `passes` pide
  las dos, porque las dos están impresas como requisitos. Un laboratorio que
  lea A.4.3 como la regla del anexo ve la segunda marca falsa y la primera
  verdadera. `tests/emission/test_free_field_qualification.py` fija un
  recorrido de 100 mm que cumple A.4.3 por encima de 250 Hz e incumple el
  A.4.3 de ISO 26101 en todas las bandas por encima de 343 Hz.
- **Estado:** sin notificar.

## ISO 6926:2016, anexo A, Fórmula (A.1) (d_0 como la mitad de una longitud que ISO 3745 ya reduce a la mitad)

- **Ubicación:** anexo A (informativo), A.2 a), Fórmula (A.1) y la definición
  de $d_0$ que la sigue (página 22 del PDF, p. 16 impresa) de ISO 6926:2016,
  tercera edición, leída frente a ISO 3745:2012, 3.14 (página 13 del PDF,
  p. 4 impresa). La adopción española UNE-EN ISO 6926:2016 imprime la misma
  definición.
- **El impreso:** $f_\mathrm{k} = \dfrac{c}{2\pi} \cdot \dfrac{1}{d_0}$, con
  «$d_0$ is half the characteristic source dimension of the source (see
  ISO 3745), in metres», y la NOTA «the knee frequency is defined as the
  frequency at which the radiation efficiency has dropped 3 dB relative its
  maximum value at high frequencies». ISO 3745:2012 3.14 define la dimensión
  característica de la fuente, con el mismo símbolo $d_0$, como la «distance
  from the origin of the co-ordinate system to the farthest corner of the
  reference box».
- **El problema:** la longitud que ISO 3745 llama $d_0$ ya es un radio, la
  distancia del centro de la fuente a su esquina más lejana, así que su mitad
  es la cuarta parte del tamaño de la fuente. La NOTA sitúa la frecuencia de
  codo donde la eficiencia de radiación de una esfera pulsante,
  $(ka)^2/(1 + (ka)^2)$, ha caído a la mitad, en $ka = 1$, que es la
  Fórmula (A.1) con $d_0$ igual al radio $a$. Volver a dividir entre dos la
  longitud de ISO 3745 duplica $f_\mathrm{k}$ y sube una octava el cambio
  entre las Fórmulas (A.2) y (A.3). La definición da al símbolo dos
  significados en dos normas que se citan entre sí.
- **Evidencia:** Verificado en la página 22 del PDF (p. 16 impresa) de
  ISO 6926:2016 y en la página 13 del PDF (p. 4 impresa) de
  BS EN ISO 3745:2012; la lectura física descansa en la eficiencia de
  radiación de una esfera pulsante, un recálculo y no un valor impreso.
- **Comportamiento de la biblioteca:** `knee_frequency` toma el $d_0$ que
  entra en la Fórmula (A.1), una longitud del orden de un radio, y su
  docstring remite aquí; qué longitud es queda en manos de quien llama.
  Ningún número que la biblioteca da depende de la elección. No hizo falta
  ningún cambio.
- **Estado:** sin notificar.

## ISO 8297:1994, 3.7 (un término mal escrito en el encabezado de la definición)

- **Ubicación:** definición 3.7 (página 11 del PDF, p. 3 impresa) de BS ISO
  8297:1994, la adopción británica idéntica de ISO 8297:1994.
- **El impreso:** «characteristics height of the plant, $H$».
- **El problema:** «characteristics» por «characteristic». La lista de
  símbolos del apartado 4, en la misma página («Characteristic height of the
  plant, in metres»), y 9.2 c) (página 13 del PDF, p. 5 impresa: «the
  characteristic height of the plant, $H$») escriben el término sin la letra
  de más; el encabezado de la definición es el único sitio que lo nombra de
  otra forma.
- **Evidencia:** verificado en la página 11 del PDF (p. 3 impresa) de BS ISO
  8297:1994, definición 3.7, frente a la lista de símbolos del apartado 4 de
  la misma página y 9.2 c) de la página 13 del PDF (p. 5 impresa).
- **Comportamiento de la biblioteca:** nada que hacer; ningún número depende
  de ello. La altura es `plant_characteristic_height_m` y el
  `characteristic_height_m` del contorno.
- **Estado:** sin notificar.

## ISO 8297:1994, 9.1.1 b) (el ángulo de visión escrito con el símbolo del ángulo a −3 dB del micrófono)

- **Ubicación:** apartado 9.1.1 b) (página 13 del PDF, p. 5 impresa), frente
  a la lista de símbolos del apartado 4 (página 11 del PDF, p. 3 impresa), el
  rótulo del ángulo de visión de la Figura 1 y el apartado 7.1 (página 12 del PDF, p. 4 impresa)
  de BS ISO 8297:1994, la adopción británica idéntica de ISO 8297:1994.
- **El impreso:** «from any point on the measurement contour, the plant area
  shall be seen inside an aspect angle, $\theta$, not greater than 180°
  (see Figure 1)».
- **El problema:** el apartado 4 da a los dos ángulos de la norma dos
  símbolos: $\theta$ es el «Angle at which the sensitivity of a directional
  microphone has fallen by 3 dB», el ángulo que 7.1 exige mayor que ±30° y
  que 10.6 lleva a $\Delta L_\mathrm{M} = 3(1 - \theta/90)$ dB, y $\phi$
  es el «Aspect angle subtended at a microphone position by the extremities
  of the perimeter of the plant area». La Figura 1, a la que remite 9.1.1 b),
  rotula el ángulo de visión $\phi$. El apartado escribe, pues, el ángulo de
  visión con el símbolo del ángulo del micrófono. La Figura 1 escribe además
  la cota como «$\phi < 180°$», estricta, donde el apartado dice «not greater
  than 180°».
- **Evidencia:** verificado en la página 13 del PDF (p. 5 impresa) de BS ISO
  8297:1994, apartado 9.1.1 b), frente a la lista de símbolos de la página 11 del PDF (p. 3
  impresa) y la Figura 1 y el apartado 7.1 de la página 12 del PDF (p. 4
  impresa).
- **Comportamiento de la biblioteca:** el ángulo de visión es el $\phi$ del
  apartado 4 y de la Figura 1, y la cota es la del apartado, como mucho 180°
  (`check_plant_measurement`, requisito `aspect_angle`, y
  `PlantMeasurementContour.aspect_angles_deg`); $\theta$ conserva el
  significado del apartado 4 como `directional_microphone_angle_deg`. No hizo
  falta ningún cambio.
- **Estado:** sin notificar.

## ISO 8297:1994, 10.4 (el término de área escrito con subíndice en minúscula)

- **Ubicación:** apartado 10.4, paso 4 (página 15 del PDF, p. 7 impresa) de
  BS ISO 8297:1994.
- **El impreso:** «Calculate an area term, $\Delta L_\mathrm{s}$, in
  decibels, for the measurement surface (as defined in ISO 3744)».
- **El problema:** la ecuación que sigue a la frase escribe
  $\Delta L_\mathrm{S} = 10 \lg[(2S_\mathrm{m} + hl)/S_0]$ dB con subíndice
  en mayúscula, igual que la lista de símbolos del apartado 4 (página 11 del
  PDF, p. 3 impresa: «$\Delta L_\mathrm{S}$ Area term, in decibels») y la
  suma de 10.8 en la misma página. El texto de 10.4 es el único sitio que
  escribe el subíndice en minúscula; los pasos 5 a 7 nombran sus términos con
  los símbolos de sus ecuaciones.
- **Evidencia:** verificado en la página 15 del PDF (p. 7 impresa) de BS ISO
  8297:1994, apartado 10.4, frente a su propia ecuación y a 10.8 en la misma
  página y a la lista de símbolos de la página 11 del PDF (p. 3 impresa). El
  texto corrido de esta reimpresión va compuesto aparte de sus ecuaciones, así
  que el desliz puede ser de la adopción británica y no de ISO 8297:1994.
- **Comportamiento de la biblioteca:** nada que hacer; el término es
  `PlantSoundPowerResult.area_term_db`, escrito $\Delta L_\mathrm{S}$ en su
  docstring.
- **Estado:** sin notificar.

## ISO 8297:1994, Tabla 3 (la octava de 31,5 Hz impresa como 31 Hz)

- **Ubicación:** Tabla 3, primera fila (página 15 del PDF, p. 7 impresa) de
  BS ISO 8297:1994.
- **El impreso:** la primera frecuencia central de banda de octava de la
  Tabla 3 es «31».
- **El problema:** 7.2 exige que las frecuencias centrales de las bandas
  «correspond to those of ISO 266», cuya banda de octava es 31,5 Hz, y la
  NOTA 8 (página 14 del PDF, p. 6 impresa) llama a esa misma banda
  «31,5 Hz». La fila es la octava de 31,5 Hz; su valor, 0 dB/m, no cambia.
- **Evidencia:** verificado en la página 15 del PDF (p. 7 impresa) de BS ISO
  8297:1994, Tabla 3, frente al apartado 7.2 de la página 13 del PDF (p. 5 impresa) y la NOTA 8
  de la página 14 del PDF (p. 6 impresa).
- **Comportamiento de la biblioteca:** `PLANT_AIR_ABSORPTION_DB_PER_M` asigna
  la fila a 31.5 Hz, la banda que nombra el resto del método. No hizo falta
  cambiar ningún valor.
- **Estado:** sin notificar.

## ISO/PAS 1996-3:2022, apartado 5 (referencias cruzadas de r y d)

- **Ubicación:** apartado 5, Fórmula (2), las definiciones de los símbolos de
  la prominencia
  $P = 3\log_{10}[r/(\text{dB/s})] + 2\log_{10}(d/\text{dB})$.
- **El impreso:** «r is the onset rate (OR) as defined in 3.4» y «d is the
  level difference (LD) as defined in 3.5».
- **El problema:** las dos referencias cruzadas están intercambiadas. Los
  propios términos y definiciones del documento fijan 3.4 como la *diferencia
  de niveles* LD («difference in decibels of L_pAF between the level of the
  end point L_e and the level of the starting point L_s of the onset») y 3.5
  como la *velocidad de aparición* OR («slope in decibels per second of the
  straight line that gives the best approximation to the onset»). Leída al
  pie de la letra, la Fórmula (2) tomaría tres veces el logaritmo de una
  diferencia de niveles más dos veces el logaritmo de una pendiente,
  invirtiendo los pesos que el método asigna a las dos cantidades. Los
  nombres desarrollados de la misma lista («the onset rate (OR)», «the level
  difference (LD)») y las unidades dadas para cada uno («dB/s» para $r$,
  «dB» para $d$) hacen inequívoca la lectura pretendida.
- **Evidencia:** lectura lado a lado de 3.4, 3.5 y la lista de símbolos del
  apartado 5; las unidades impresas con cada símbolo contradicen los números
  de apartado impresos con ellos.
- **Comportamiento de la biblioteca:** implementa la lectura desarrollada,
  ponderando la velocidad de aparición por 3 y la diferencia de niveles por 2
  (`predicted_prominence` en
  [`impulsive_sound.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/impulsive_sound.py)),
  que es además la forma de NT ACOU 112:2002 que el PAS arrastra.
- **Estado:** sin notificar.

## ISO 13474:2009, Anexo A.2 (el nivel de cada clase atribuido a las Ecuaciones (7) y (8))

- **Ubicación:** Anexo A (informativo), A.2, el párrafo sobre la Tabla A.3
  que dice cómo se obtuvieron sus niveles.
- **El impreso:** «For each octave band, the sound exposure level at location
  A was calculated using Equations (7) and (8). From this, the A-weighted
  sound exposure level for each excess-attenuation class was determined.»
- **El problema:** las Ecuaciones (7) y (8) son el nivel medio a largo plazo
  de exposición sonora del suceso y su nivel de evaluación,
  $10 \lg \left[\sum_{k}\sum_{l} \wp_{\mathrm{atm},k}\,\wp_{\mathrm{exc},l}\,10^{0{,}1 L_{E,\mathrm{w},k,l}}\right]$
  dB, con $K$ sumado en el exponente de la Ecuación (8): un único número
  sumado sobre todas las clases, a partir de niveles ya ponderados en
  frecuencia, sin banda de octava ni clase que quede en él. El párrafo
  describe un nivel por banda para cada clase de atenuación en exceso y
  después el nivel ponderado A de cada clase obtenido de él, que son la
  Ecuación (4), $L_{E,k,l}(j)$, y la Ecuación (5). El propio anexo usa la
  Ecuación (7) un paso después, para el LT1, un único valor impreso en la
  Figura A.3 del que dice «calculated using Equation (7)». La referencia
  cruzada debería decir Ecuaciones (4) y (5).
- **Evidencia:** el párrafo leído en la página 39 del PDF (p. 31 impresa), la
  Ecuación (4) en la página 15 del PDF (p. 7 impresa), la Ecuación (5) en la
  página 16 del PDF (p. 8 impresa), las Ecuaciones (7) y (8) en la página 17
  del PDF (p. 9 impresa) y la frase del LT1 en la página 42 del PDF (p. 34
  impresa), todo de BS ISO 13474:2009, la adopción británica de
  ISO 13474:2009 (primera edición, 2009-06-15).
- **Comportamiento de la biblioteca:** los niveles de la Tabla A.3 se toman
  tal como se imprimen; `frequency_weighted_sel` evalúa la Ecuación (5) y
  `long_term_sel` las Ecuaciones (7) y (8)
  ([`exposure_distribution.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/exposure_distribution.py)),
  cada una con la ecuación que le da su apartado. No hizo falta ningún
  cambio.
- **Estado:** sin notificar.

## ISO 13474:2009, Anexo A.2 (el desplazamiento de la Ecuación (22) impreso como 1,04 dB)

- **Ubicación:** Anexo A (informativo), A.2, el párrafo bajo la Figura A.1 que
  dispersa la densidad de las clases por la turbulencia.
- **El impreso:** el párrafo empieza con «a normal distribution having a
  standard deviation equal to 5 dB» y sigue «In this example, the mean value
  was shifted by an amount, Δμ, equal to 1,04 dB [from Equation (22)]»; la
  Figura A.3 repite $\sigma = 5{,}0$ dB.
- **El problema:** la Ecuación (22) es la media de una variable lognormal y
  vale $\Delta\mu = \sigma^2 \ln 10 / 20$, que son $2{,}878$ dB con
  $\sigma = 5$ dB. $1{,}04$ dB es su valor con $\sigma = 3$ dB ($1{,}036$ dB),
  una desviación típica que el anexo no usa. El resto del anexo se calculó con
  $2{,}878$ dB. El desplazamiento mantiene la media energética de cada
  subclase en su centro, y por eso el LT2 impreso de 37,0 dB coincide con el
  LT1 impreso de 37,0 dB; con $\Delta\mu = 1{,}04$ dB y $\sigma = 5$ dB todos
  los niveles de la distribución dispersada suben $1{,}84$ dB, el LT2 queda en
  38,8 dB, el máximo de la Figura A.2 pasa de unos 30,5 dB a 32,3 dB y
  $L_{50}$ queda en 33,3 dB frente a los 31,5 dB impresos.
- **Evidencia:** el párrafo leído en la página 42 del PDF (p. 34 impresa), la
  Ecuación (22) en la página 21 del PDF (p. 13 impresa), las Figuras A.2 y A.3
  en las páginas 43 y 44 del PDF (pp. 35 y 36 impresas), todo de
  BS ISO 13474:2009, la adopción británica de ISO 13474:2009 (primera
  edición, 2009-06-15). Todos los valores se recalcularon a partir de la
  Tabla A.3, en la página 40 del PDF (p. 32 impresa) del mismo documento.
- **Comportamiento de la biblioteca:** el desplazamiento es la Ecuación (22)
  en forma cerrada,
  [`turbulence_level_shift`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/exposure_distribution.py),
  $2{,}878$ dB con 5 dB, y no es un parámetro que se pueda fijar. La
  comprobación de conformidad «ISO 13474:2009 Equation (22)» lo contrasta con
  la integral impresa evaluada por cuadratura, y «ISO 13474:2009 Equation
  (A.4), Figure A.3» mantiene el LT2 en los 37,0 dB impresos.
- **Estado:** sin notificar.

## ISO 13474:2009, Anexo A.2, Figura A.3 (niveles de superación que no son las raíces de la Ecuación (25))

- **Ubicación:** Anexo A (informativo), Figura A.3, los niveles de superación
  impresos junto a la curva acumulada.
- **El impreso:** $L_{95} = 21{,}7$ dB, $L_{50} = 31{,}5$ dB,
  $L_{10} = 40{,}6$ dB, $L_{5} = 43{,}2$ dB y $L_{1} = 48{,}0$ dB, junto a
  $\sigma = 5{,}0$ dB.
- **El problema:** la Ecuación (24) define la probabilidad de que el nivel
  supere $x$ como $\int_x^{\infty} \rho^{*}(x')\,\mathrm{d}x'$ y la Ecuación
  (25) el nivel superado el $n$ % como su raíz. Sobre la distribución de la
  Tabla A.4 dispersada como describe A.2, dan 21,6; 31,5; 40,5; 43,0 y
  47,5 dB: $L_{50}$ coincide y los otros cuatro se imprimen entre 0,1 dB y
  0,5 dB más altos, tanto más cuanto más raro es el nivel. El anexo no dice
  cómo los calculó. Hay una lectura compatible con el impreso: una curva
  acumulada formada desde 15 dB, donde empiezan las curvas dibujadas de las
  Figuras A.2 y A.3 (sus ejes empiezan en 10 dB), y no desde menos infinito,
  $1 - \int_{15}^{x} \rho^{*}(x')\,\mathrm{d}x'$; la curva dibujada de la
  Figura A.3 empieza en 15 dB sobre la línea del 1, que es lo que dibuja esa
  lectura y donde la Ecuación (24) da 0,998. Alimentada con la columna
  de 07:00 a 19:00 de la Tabla A.3 tal como se imprime, que suma 1,0004, da
  21,69; 31,49; 40,58; 43,16 y 47,97 dB, los cinco al dígito impreso; añade
  entonces un 0,17 % a cada superación, el 0,21 % de la distribución por
  debajo de 15 dB menos el 0,04 % en que la columna impresa pasa de uno, lo
  que mueve más los niveles de los porcentajes más pequeños. Alimentada con
  las probabilidades a precisión completa que reproducen la Tabla A.4, la
  misma lectura da 21,69; 31,49; 40,59; 43,17 y 48,05 dB, y $L_{1}$ se
  imprimiría como 48,1 dB. La lectura es por tanto una hipótesis y no una
  reconstrucción de la figura; lo que queda establecido es que cuatro de los
  cinco niveles impresos no son raíces de la Ecuación (25).
- **Evidencia:** la Figura A.3 en la página 44 del PDF (p. 36 impresa), la
  Figura A.2 en la página 43 del PDF (p. 35 impresa) y las Ecuaciones (24) y
  (25) en la página 21 del PDF (p. 13 impresa), todo de BS ISO 13474:2009, la
  adopción británica de ISO 13474:2009 (primera edición, 2009-06-15). Los
  niveles se recalcularon a partir de la Tabla A.3, en la página 40 del PDF
  (p. 32 impresa) del mismo documento.
- **Comportamiento de la biblioteca:** `SelDistribution.exceedance` evalúa la
  Ecuación (24) hasta infinito en forma cerrada y
  `SelDistribution.exceedance_level` resuelve la Ecuación (25)
  ([`exposure_distribution.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/exposure_distribution.py)),
  así que el ejemplo devuelve 21,6; 31,5; 40,5; 43,0 y 47,5 dB. La
  comprobación de conformidad «ISO 13474:2009 Equation (25), Figure A.3»
  mantiene $L_{50}$ en los 31,5 dB impresos; los otros cuatro niveles
  impresos no tienen comprobación de conformidad.
- **Estado:** sin notificar.

## ISO/TS 12913-3:2019, Anexo A.3 (la calidad afectiva percibida llamada parte 3)

- **Ubicación:** Anexo A (informativo), A.3, el párrafo que presenta las
  Fórmulas (A.1) y (A.2).
- **El impreso:** «The results from part 3 (see A.1) are further processed to
  derive the values on two dimensions (pleasantness and eventfulness) for each
  site.»
- **El problema:** los ocho atributos que leen las dos fórmulas (annoying,
  calm, chaotic, eventful, monotonous, pleasant, uneventful, vibrant) son la
  calidad afectiva percibida, que es la parte 2 del cuestionario del Método A
  en todos los demás sitios donde los documentos la nombran: en la Tabla A.1
  de la página anterior («2 (perceived affective quality)»), en el párrafo de
  A.2 que asigna sus valores de escala de 5 a 1 («questionnaire part 2 (see
  Figure C.4 ...)»), en el propio título de A.3 («based on perceived
  affective quality responses») y en ISO/TS 12913-2:2018, C.3.1.3 y Figura
  C.4, «Questionnaire part 2: Perceived affective quality». La parte 3 es la
  valoración global única de la Figura C.5, «Overall, how would you describe
  the present surrounding sound environment?», que no tiene atributos y no
  puede alimentar ninguna de las dos fórmulas. La referencia «(see A.1)» no
  ayuda: A.1 es el apartado general y no nombra ninguna parte. La frase
  debería decir «part 2 (see A.2 and Table A.1)».
- **Evidencia:** la frase en la página 11 del PDF (p. 5 impresa), la Tabla
  A.1 y los párrafos de A.2 en la página 10 del PDF (p. 4 impresa), ambas de
  ISO/TS 12913-3:2019 (primera edición, 2019-12); C.3.1.3 en la página 21 del
  PDF (p. 15 impresa) y las Figuras C.4 y C.5 en la página 22 del PDF (p. 16
  impresa) de ISO/TS 12913-2:2018 (primera edición).
- **Comportamiento de la biblioteca:** `pleasantness_eventfulness` aplica las
  Fórmulas (A.1) y (A.2) a los ocho atributos de la parte 2, la única lectura
  con la que pueden evaluarse
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No hizo falta ningún cambio. La edición de 2025 de ISO/TS 12913-3 revisa el
  Anexo A y no se ha comprobado para esta entrada.
- **Estado:** sin notificar.

## ISO/TS 12913-3:2019, Fórmula (A.3) (un factor 1 suelto)

- **Ubicación:** Anexo A (informativo), A.4, Fórmula (A.3), el coeficiente de
  correlación por rangos de Spearman para rangos sin empates.
- **El impreso:**
  $r_\mathrm{spearman} = 1 - 1\,\dfrac{6\cdot\sum_{i=1}^{n} d_i^2}{n\cdot(n^2 - 1)}$,
  con un «1» entre el signo menos y la fracción.
- **El problema:** el coeficiente para rangos sin empates es
  $1 - 6\sum d_i^2 / \left[n(n^2 - 1)\right]$, que es lo que da la página si
  el «1» suelto se lee como un factor uno. Leído como se escribe un número
  mixto, $1\,\tfrac{a}{b} = 1 + \tfrac{a}{b}$, daría
  $r = -6\sum d_i^2 / \left[n(n^2 - 1)\right]$, que vale cero para dos
  ordenaciones idénticas en lugar de uno. La Fórmula (A.4), en la misma
  página, se reduce al coeficiente habitual cuando no hay empates, así que la
  forma buscada no ofrece dudas; el «1» es un resto de composición.
- **Evidencia:** la Fórmula (A.3) en la página 12 del PDF (p. 6 impresa) de
  ISO/TS 12913-3:2019 (primera edición, 2019-12).
- **Comportamiento de la biblioteca:** `spearman_rank_correlation` evalúa
  $1 - 6\sum d_i^2 / \left[n(n^2 - 1)\right]$ sin empates y la Fórmula (A.4)
  con ellos; las filas de conformidad ligan la primera al coeficiente de
  Pearson de los rangos y la segunda a `scipy.stats.spearmanr`
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO/TS 12913-3:2019, Fórmula (A.4) (la lista de definiciones de los empates)

- **Ubicación:** Anexo A (informativo), A.4, la lista de definiciones bajo la
  Fórmula (A.4), el coeficiente de correlación por rangos de Spearman para
  rangos con empates.
- **El impreso:** «$t_j$ is the number of in $t_j$ tied ranks of the variable
  $x$; $u_j$ is the number of in $u_j$ tied ranks of the variable $y$;
  $k(x)$ and $k(y)$ are the numbers of tied ranks of the variables $x$ and
  $y$», bajo
  $T = \sum_{j=1}^{k(x)} (t_j^3 - t_j)/12$ y
  $U = \sum_{j=1}^{k(y)} (u_j^3 - u_j)/12$.
- **El problema:** las dos primeras definiciones no son frases («the number
  of in $t_j$ tied ranks») y definen $t_j$ por sí mismo. Las sumas necesitan
  que $t_j$ sea el número de valores que comparten el $j$-ésimo rango empatado
  de $x$ ($u_j$ lo mismo para $y$), y que $k(x)$, $k(y)$ sean el número de
  esos grupos de empates en cada variable, que es lo que «the numbers of tied
  ranks» no dice. La lectura buscada es la corrección por empates habitual del
  coeficiente de Spearman, que es lo que hace de (A.4) el coeficiente de
  Pearson de los rangos medios.
- **Evidencia:** la lista de definiciones en la página 13 del PDF (p. 7
  impresa), bajo la Fórmula (A.4) de la página 12 del PDF (p. 6 impresa), de
  ISO/TS 12913-3:2019 (primera edición, 2019-12).
- **Comportamiento de la biblioteca:** `spearman_rank_correlation` suma
  $(t_j^3 - t_j)/12$ sobre los grupos de valores iguales de cada variable, y
  una fila de conformidad liga la Fórmula (A.4) así leída a
  `scipy.stats.spearmanr` sobre 93 respuestas reales con muchos empates
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO/TS 12913-3:2019, Fórmula (B.2) ($x_I$ por $x_i$)

- **Ubicación:** Anexo B (informativo), B.3, la lista de definiciones bajo la
  Fórmula (B.2), la covarianza del coeficiente de correlación de Pearson.
- **El impreso:** «$\bar{x}$ is the arithmetic mean value of the array $x_I$;»
  con una $I$ mayúscula, seguido de «$\bar{y}$ is the arithmetic mean value of
  the array $y_i$;».
- **El problema:** el índice es la $i$ minúscula de la suma de (B.2),
  $\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})/n$, y de la línea de
  $\bar{y}$ justo debajo; $x_I$ no nombra ningún array del anexo.
- **Evidencia:** la lista de definiciones en la página 15 del PDF (p. 9
  impresa) de ISO/TS 12913-3:2019 (primera edición, 2019-12).
- **Comportamiento de la biblioteca:** `pearson_correlation` toma $\bar{x}$
  como la media de los $x_i$
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
  No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO/TS 12913-2:2018, A.3 f), NOTA (exponente 3 por una raíz cúbica)

- **Ubicación:** Anexo A (normativo), A.3 f), la NOTA sobre la sonoridad media
  cúbica $N_\mathrm{rmc}$.
- **El impreso:** «The root mean cubed loudness (cubic mean), Nrmc, is
  computed by determining the mean of all loudness values raised to the power
  of 3 with a subsequent application of the exponent 3 as shown in the
  following formula:
  $N_\mathrm{rmc} = \sqrt[3]{\frac{1}{n}\sum_{i=1}^{n} N_i^3}$».
- **El problema:** el texto y la fórmula de debajo no coinciden. La fórmula
  toma la raíz cúbica de la media de los cubos, un exponente posterior de
  $1/3$, que es lo que es una media cúbica y lo que devuelve una sonoridad en
  sone; el texto dice que el exponente posterior es 3, lo que daría la media
  de los cubos elevada al cubo, $\left(\frac{1}{n}\sum N_i^3\right)^3$, en
  sone a la novena. La frase debería decir «a subsequent application of the
  exponent 1/3». ISO 532-1:2017, 6.4, NOTE, describe con la misma forma la
  media energética del nivel de sonoridad y la acierta: una potencia de
  aproximadamente 3,322 y después una ley de potencia «with the exponent
  lg(2)», su inversa.
- **Evidencia:** la NOTA y su fórmula en la página 14 del PDF (p. 8 impresa)
  de ISO/TS 12913-2:2018 (primera edición, 2018-08); ISO 532-1:2017, 6.4, en
  la página 22 del PDF (p. 16 impresa).
- **Comportamiento de la biblioteca:** `binaural_indicators` calcula
  $N_\mathrm{rmc}$ de cada oído con la fórmula, la raíz cúbica de la media de
  los cubos de la sonoridad en el tiempo, y una fila de conformidad lo liga a
  esa fórmula
  ([`soundscape_binaural.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape_binaural.py)).
  No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO/TS 12913-2:2018, C.3.2.3 frente a la Figura C.7 (tres escalas en el texto, cuatro en la figura)

- **Ubicación:** Anexo C (informativo), C.3.2.3, «Soundwalk data collection
  part 1: Assessment of the sound environment», y la Figura C.7 que le sigue.
- **El impreso:** el texto dice «The participants should assess a site on
  three different five-point unipolar continuous-category scales with
  additional verbal labelling ranging from "not at all" to "extremely".» La
  figura imprime cuatro escalas: «How loud is it here?», «How unpleasant is
  it here?» y «How appropriate is the sound to the surrounding?», rotuladas de
  «not at all» a «extremely», y «How often would you like to visit this place
  again?», rotulada «never», «rarely», «sometimes», «often», «very often».
- **El problema:** el texto y la figura que presenta no coinciden ni en el
  número de escalas ni en sus rótulos. O la cuarta escala forma parte del
  Método B, y el texto debería decir cuatro y nombrar su segundo juego de
  rótulos, o no forma parte, y la figura no debería imprimirla.
  ISO/TS 12913-3:2019, B.2 y la Tabla B.1 hablan de «the five-point unipolar
  continuous-category scales» sin número y no lo resuelven.
- **Evidencia:** C.3.2.3 y la Figura C.7 en la página 24 del PDF (p. 18
  impresa) de ISO/TS 12913-2:2018 (primera edición); B.2 y la Tabla B.1 en
  la página 14 del PDF (p. 8 impresa) de ISO/TS 12913-3:2019.
- **Comportamiento de la biblioteca:** `METHOD_B_SCALES` guarda las cuatro
  escalas de la figura tal como se imprimen, y `method_b_summary` acepta una
  tabla con tres o con cuatro, de modo que un estudio que siguiera cualquiera
  de las dos lecturas se resume con sus propias preguntas
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
- **Estado:** sin notificar.

## ISO/TS 12913-2:2018, Figuras C.2 a C.4 («extend» por «extent», «reponse» por «response»)

- **Ubicación:** Anexo C (informativo), el cuestionario del Método A: las
  preguntas de las Figuras C.2, C.3 y C.4 y la línea de instrucciones de
  cada una.
- **El impreso:** «To what extend do you presently hear the following four
  types of sounds?» (Figura C.2), «To what extend do you presently hear the
  following three types of sounds?» (Figura C.3), «For each of the 8 scales
  below, to what extend do you agree or disagree that the present surrounding
  sound environment is...» (Figura C.4); y «Please tick off one reponse
  alternative per type of sound» (Figuras C.2 y C.3), «Please tick off one
  reponse alternative per scale» (Figura C.4).
- **El problema:** «extend» es un verbo; la pregunta es «to what extent», que
  la Figura C.6 del mismo anexo escribe bien («Overall, to what extent is the
  present surrounding sound environment appropriate to the present place?»).
  «reponse» es una errata de «response». Las figuras son un cuestionario
  pensado para ponerse delante de los participantes tal como se imprime, así
  que los deslices llegan al trabajo de campo si el estudio no los corrige.
- **Evidencia:** las Figuras C.2 y C.3 en la página 21 del PDF (p. 15
  impresa), las Figuras C.4 y C.6 en la página 22 del PDF (p. 16 impresa),
  todo de ISO/TS 12913-2:2018 (primera edición).
- **Comportamiento de la biblioteca:** `METHOD_A_SCALES` y
  `METHOD_A_ALTERNATIVE_PART_1` transcriben las preguntas y las instrucciones
  tal como se imprimen, erratas incluidas, para que la tabla pueda cotejarse
  con la página; el docstring de `QuestionnaireScale` advierte que un estudio
  que imprima su cuestionario a partir de ella debe corregirlas
  ([`soundscape.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/assessment/soundscape.py)).
- **Estado:** sin notificar.

## ISO 3744:2010, H.4.2.7 (la corrección por altitud y el divisor que lleva debajo)

- **Ubicación:** Anexo H (informativo), H.4.2.7 «Meteorological and radiation
  impedance corrections», el párrafo que dimensiona $u_{C_1+C_2}$ a partir de
  la corrección del Anexo G.
- **El impreso:** «At 120 m altitude and 23 °C the correction is zero and at
  500 m altitude the correction is 0,6 dB. Assuming a triangular distribution
  for this uncertainty, the standard deviation is
  $s_\mathrm{met} = 0{,}6/\sqrt{6} = 0{,}3\ \mathrm{dB}$».
- **El problema:** dos defectos independientes en un mismo par de frases.
  (a) El Anexo G, que es normativo y al que ese párrafo remite, da
  $C_1 + C_2 = 0{,}394$ dB a 500 m y 23,0 °C, no 0,6 dB. La lectura se valida
  a sí misma: esas dos mismas ecuaciones dan $-4{,}6 \times 10^{-5}$ dB a 120 m
  y 23,0 °C, que es el «cero» que imprime la misma frase, así que las
  constantes y los términos de temperatura se están leyendo como la norma
  pretende. Los 0,6 dB se alcanzan hacia los 697 m a 23,0 °C, o a 500 m solo
  si el aire está a 30,1 °C.
  (b) $0{,}6/\sqrt{6} = 0{,}245$, no 0,3. El cociente no da el resultado que
  se imprime a su lado: 0,3 dB es exactamente $0{,}6/2$, así que o el divisor
  o el resultado está mal. Para una distribución triangular de semianchura $a$
  la desviación típica es $a/\sqrt{6}$, que es el divisor que la frase nombra.
- **Evidencia:** H.4.2.7 leído en la página 82 del PDF (p. 73 impresa), contra
  las Ecuaciones (G.1) y (G.2) del Anexo G con $a = 2{,}2560 \times 10^{-5}$
  m$^{-1}$, $b = 5{,}2553$, $\theta_0 = 314$ K y $\theta_1 = 296$ K en las
  páginas 73 y 74 del PDF (pp. 64 y 65 impresas), todo de BS EN ISO 3744:2010.
  Ambos valores se recalcularon solo a partir de las ecuaciones impresas.
- **Comportamiento de la biblioteca:** el balance de incertidumbre del
  Anexo H no está modelado, así que ningún número publicado depende de
  ninguna de las dos cifras. La corrección del Anexo G sí se evalúa desde las
  Ecuaciones (G.1) y (G.2) en
  [`reference_atmosphere_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power.py),
  y la comprobación de conformidad «ISO 3744:2010 Annex G / H.4.2.7» fija la
  mitad del párrafo que sí es correcta: la corrección se anula a 120 m y 23 °C.
- **Estado:** sin notificar.

## ISO 9613-2:1996, Tabla 2 (celda de 15 °C / 80 % / 1 kHz)

- **Ubicación:** Tabla 2, «Atmospheric attenuation coefficient α for octave
  bands of noise», fila de 15 °C / 80 % de humedad relativa, columna de
  1 kHz.
- **El impreso:** $\alpha = 4{,}1\ \text{dB/km}$.
- **El problema:** la Tabla 2 es un extracto redondeado de ISO 9613-1, a la
  que el propio apartado remite («For values of α at atmospheric conditions
  not covered in table 2, see ISO 9613-1»). Evaluar la fórmula de tono puro
  de ISO 9613-1 a 1 kHz, $15\ ^\circ\text{C}$, $80\ \%$ de HR y
  $101{,}325\ \text{kPa}$ da $4{,}1511\ \text{dB/km}$, que redondea a
  $4{,}2$, no al $4{,}1$ impreso. Las celdas vecinas de la misma fila
  redondean correctamente (2 kHz: $8{,}338$ -> impreso $8{,}3$; 4 kHz:
  $23{,}86$ -> $23{,}7$ en el centro de banda exacto), igual que las celdas
  de 1 kHz de las otras filas ($15\ ^\circ\text{C}$ / $50\ \%$: $4{,}164$ ->
  impreso $4{,}2$), así que el defecto queda confinado a esta celda.
- **Evidencia:** evaluación independiente del coeficiente de ISO 9613-1 a la
  frecuencia nominal y a la del centro de banda exacto
  ($4{,}1511\ \text{dB/km}$ en ambos casos, siendo 1 kHz las dos).
- **Comportamiento de la biblioteca:** no le afecta. La biblioteca nunca lee
  la Tabla 2: calcula $A_\text{atm}$ desde la fórmula de ISO 9613-1
  directamente
  ([`air_absorption.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/air_absorption.py)),
  así que da $4{,}15\ \text{dB/km}$ para esta condición.
- **Estado:** sin notificar.

## ISO/TR 17534-3:2015, Tabla 20 (q atribuida a la nota al pie equivocada de la Tabla 3 de la ISO 9613-2)

- **Ubicación:** Tabla 20, «Single number step by step results» del caso de
  prueba T08, la fila que nombra el factor de solape de la región media $q$.
- **Lo impreso:** `q (ISO 9613-2:1996, Table 3, footnote 1)`.
- **El problema:** la nota al pie 1 de la Tabla 3 de la ISO 9613-2:1996 trata
  de qué factor de suelo y qué altura toma cada región exterior («For
  calculating $A_s$, take $G = G_s$ and $h = h_s$...»). No dice nada de $q$. El
  factor $q$ lo define la nota al pie 2 de esa misma tabla, que es adonde la
  propia guía manda al lector en los otros cuatro sitios donde imprime la fila:
  la Tabla 3 (T01), la Tabla 8 (T04), la Tabla 14 (T06) y la Tabla 22 (T09)
  dicen todas «Table 3 footnote 2». La Tabla 20 es la única ocurrencia que dice
  footnote 1, y el valor que lleva, $q = 0{,}23$, es el que produce la nota 2.
- **Evidencia:** verificado en la página 23 del PDF (p. 17 impresa) de
  ISO/TR 17534-3:2015, junto con las cuatro ocurrencias coherentes de esa misma
  fila en las páginas 13, 16, 20 y 41 del PDF (pp. 7, 10, 14 y 35 impresas) de
  esa misma edición; las dos notas al pie a las que apunta se leyeron en la
  página 10 del PDF (p. 8 impresa) de ISO 9613-2:1996.
- **Comportamiento de la biblioteca:** no le afecta. El desliz tipográfico está
  en una referencia cruzada, no en un número, y
  [`ground_attenuation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/outdoor_propagation.py)
  implementa $q$ a partir de la nota 2, que es lo que reproduce el 0,23
  impreso.
- **Estado:** sin notificar.

## ISO/TR 17534-3:2015, Tabla 69 (el formulario TRC resuelto responde «yes» a un resultado por debajo de su límite inferior)

- **Ubicación:** Tabla 69, «Example of a TRC-form based on test case 1», la
  fila del caso de prueba T01 en 250 Hz.
- **Lo impreso:** límite superior 31,15, límite inferior 31,05, resultado del
  software (de ejemplo) 31,0, y «yes» en la columna «Result inside
  tolerances».
- **El problema:** 31,0 dB queda 0,05 dB por debajo del límite inferior
  31,05 dB, así que la fila responde «yes» a un resultado fuera de su
  intervalo. El intervalo en sí es correcto: la Tabla 4, los resultados
  espectrales paso a paso del T01, certifica $L_A = 31{,}10$ dB en 250 Hz, y de
  31,05 a 31,15 es ese resultado ±0,05 dB. Todas las demás filas del
  formulario llevan su resultado certificado con un decimal, y todas quedan
  dentro: siete redondeadas, entre ellas 13,70 como 13,7, 23,76 como 23,8 y
  el total 44,29 como 44,3, y la de 1 000 Hz truncada, 38,95 impreso como
  38,9 sobre su límite inferior de 38,90, donde el redondeo da 39,0. Redondeado o truncado, 31,10
  con un decimal es 31,1, y lo más probable es que el resultado de ejemplo
  debiera decir 31,1.
- **Evidencia:** leído en la página 59 del PDF (p. 53 impresa) de
  ISO/TR 17534-3:2015, primera edición, con la Tabla 4 en la página 14 del PDF
  (p. 8 impresa) de la misma edición.
- **Comportamiento de la biblioteca:** no le afecta, porque la biblioteca no
  lee nunca la Tabla 69. Con las nueve filas del formulario,
  [`verify_calculation_results`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/software_quality.py)
  responde «no» solo en la fila de 250 Hz, lo que fija
  `test_table_69_of_iso_tr_17534_3_fails_only_at_250_hz`.
- **Estado:** sin notificar.

## VDI 2081 Blatt 1:2001, apartado 6.7.3 (la lista de símbolos de la ecuación (36) remite A a la propia ecuación (36))

- **Ubicación:** apartado 6.7.3, la lista de símbolos bajo la ecuación (36), la
  entrada del área de absorción equivalente ``A``.
- **Lo impreso:** «A  äquivalente Absorptionsfläche; in m², Gleichung (36)» /
  «A  is the equivalent absorption area; in m², Equation (36)».
- **El problema:** la ecuación (36) es la ecuación de nivel a la que pertenece
  la lista, $L_P = L_W + 10\lg[Q/(4\pi r^2) + 4/A]$, en la que ``A`` es un
  dato de entrada. No define ``A``. La guía lo define dos veces más abajo en el
  mismo apartado: la ecuación (37), $A = 0{,}163\,V/T$, y la ecuación (39),
  $A = \sum \alpha_i S_n + \sum A_n$. La referencia es circular, y está en las
  dos columnas de idioma, así que es un desliz de composición del original y no
  de la traducción.
- **Evidencia:** verificado en la página 43 del PDF (p. 43 impresa) de la
  VDI 2081 Blatt 1:2001-07, con las ecuaciones (37) y (39) en la página 44 del
  PDF (p. 44 impresa) de la misma tirada.
- **Comportamiento de la biblioteca:** no le afecta. El desliz está en una
  referencia cruzada, no en un número:
  [`room_effect`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) toma ``A`` como
  argumento y
  [`sabine_absorption_area`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/steady_field.py)
  implementa la ecuación (37).
- **Estado:** sin reportar.

## VDI 2081 Blatt 1:2001, apartado 6.7.3 (la columna inglesa llama esférica a una propagación semiesférica)

- **Ubicación:** apartado 6.7.3, la frase que dice dónde empieza el campo
  reverberante, justo después de la ecuación (36b).
- **Lo impreso:** en alemán, «Der Nachhallbereich beginnt bei
  **halbkugelförmiger** Schallausbreitung in einer Entfernung, die größer ist
  als $r_H = 0{,}2\sqrt{A}$»; en inglés, «The reverberation area begins as a
  **spherical** sound propagation at a distance which is greater than
  $r_H = 0.2\sqrt{A}$».
- **El problema:** *halbkugelförmig* es semiesférica, no esférica, y la
  constante impresa da la razón al alemán. El radio de reverberación es
  $r_H = \sqrt{Q A / 16\pi}$, que vale $0{,}199\sqrt{A}$ con la $Q = 2$ de un
  semiespacio y $0{,}141\sqrt{A}$ con la $Q = 1$ del espacio entero. Sólo la
  primera redondea al $0{,}2$ impreso. Quien siga la columna inglesa tomará
  $0{,}2\sqrt{A}$ por el radio esférico y situará el campo reverberante un 41 %
  más lejos de lo que toca.
- **Evidencia:** verificado en la página 44 del PDF (p. 44 impresa) de la
  VDI 2081 Blatt 1:2001-07, leyendo las dos columnas de la misma frase una al
  lado de la otra.
- **Comportamiento de la biblioteca:** no le afecta.
  [`critical_distance`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/steady_field.py) toma ``Q`` como
  argumento y deja dicha la lectura semiesférica en su propio texto.
- **Estado:** sin reportar.

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

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), Ec. (27)

- **Ubicación:** sección A.4.2, Ec. (27) (coeficiente de absorción
  atmosférica) y la frase que define sus símbolos, p. 21 impresa.
- **El impreso:** la Ec. (27) empareja el coeficiente
  $6.6928 \cdot 10^{-6}$ con $f_{rO}$ y $1.3415 \cdot 10^{-6}$ con $f_{rN}$,
  y la frase de debajo lee «the variables f_rN = 75692 Hz and f_rO = 630.7 Hz
  represent the vibrational relaxation frequencies of oxygen and nitrogen
  respectively».
- **El problema:** los dos subíndices están intercambiados en la frase de
  definición. Los *valores* casan con los *nombres* que les da (75 692 Hz es
  la frecuencia de relajación del oxígeno y 630.7 Hz la del nitrógeno en las
  condiciones de referencia), pero están asignados a los símbolos opuestos,
  así que la ecuación tal como está impresa multiplica el coeficiente del
  oxígeno por la frecuencia de relajación del nitrógeno y viceversa. Evaluada
  así da 14.2 dB/km a 500 Hz contra el valor de 3.1 dB/km de la propia Tabla
  4 de la guía; con $f_{rO}$ y $f_{rN}$ intercambiados da 3.07 dB/km,
  reproduciendo la Tabla 4 y el coeficiente de tono puro de ISO 9613-1 a
  0.02 dB/km. Una revisión anterior de esta entrada citaba el valor impreso
  como 14.3 dB/km y planteaba el defecto como un emparejamiento erróneo de
  los coeficientes y no como subíndices intercambiados en la definición.
- **Evidencia:** evaluación numérica de la Ec. (27) con la asignación impresa
  y con la asignación intercambiada, contra la celda de 500 Hz de la Tabla 4
  de la misma página. Verificado en la página 20 del PDF (p. 21 impresa) de
  NORAH2 SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** implementa el emparejamiento correcto;
  el docstring del módulo lleva una nota defensiva para que la errata no se
  transcriba como «arreglo».
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), Ec. (21)

- **Ubicación:** sección A.3.3, Ec. (21) (ángulo de la trayectoria de vuelo).
- **El impreso:** $\gamma = \text{acos}(\Delta Z/\Delta S)$.
- **El problema:** el arcocoseno de la razón de ascenso a trayectoria
  devuelve el complemento del ángulo de trayectoria ($90^\circ$ en vuelo
  nivelado, donde $\gamma$ debe ser $0^\circ$) y contradice el propio uso de
  $\gamma$ como ángulo de ascenso/descenso en toda la sección A.3. El Doc 32
  de la CEAC, 1.ª ed., Ec. (10), imprime la forma correcta,
  $\gamma = \text{atan}(\Delta Z/\Delta S)$ con el $\Delta S$ horizontal de
  su Ec. (8).
- **Evidencia:** evaluación en vuelo nivelado; contraste contra la Ec. (10)
  del Doc 32 y contra los ficheros de entrada del prototipo NORAH2, cuyas
  columnas ``Vang`` son ángulos de ascenso/descenso ($0^\circ$ en segmentos
  nivelados).
- **Comportamiento de la biblioteca:** ``flight_path_kinematics`` implementa
  la forma ``atan`` del Doc 32; el docstring del resultado lleva la nota
  defensiva.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), triangulación del §A.3.1

- **Ubicación:** sección A.3.1, pasos 2 a 4 (interpolación de condiciones de
  vuelo), contra las tablas de consulta de triangulación distribuidas con la
  base de datos NORAH2 (``*_triangulation.int``).
- **El impreso:** los pasos 2 y 3 normalizan las condiciones de la base de
  datos (rangos, con $F_{fc} = 2$ en el ángulo de trayectoria) y el paso 4
  calcula «the Delaunay triangulation for the database flight conditions
  γ̄_j and V̄_j», es decir, la de los puntos normalizados, ofreciendo una
  tabla de consulta como equivalente.
- **El problema:** las tablas de consulta distribuidas con la base de datos
  (que la guía dice que forman parte de los datos de hemisferios y no deben
  editarse) son la triangulación de Delaunay de las condiciones $(V, \gamma)$
  brutas, no de las normalizadas: para el conjunto del R22, 14 de los 27
  triángulos distribuidos difieren de la triangulación de Delaunay de las
  condiciones normalizadas. Una triangulación de Delaunay no es invariante
  bajo la normalización anisótropa, así que las dos prescripciones
  seleccionan triángulos envolventes distintos para parte de la envolvente.
  Los pesos de distancia de las Ecs. (7)/(8) sí usan las coordenadas
  normalizadas en el prototipo (verificado contra sus salidas mezcladas).
- **Evidencia:** recálculo de ambas triangulaciones para la base de datos del
  R22; reproducción bin a bin de la selección de hemisferios por paso del
  prototipo con las tablas distribuidas, y de sus niveles mezclados con pesos
  en el espacio normalizado, a 0.05 dB.
- **Comportamiento de la biblioteca:** ``flight_condition_weights`` sigue el
  método impreso (Delaunay de las condiciones normalizadas) por defecto y
  acepta la tabla de consulta de la base de datos vía ``triangles``, que
  reproduce la implementación de referencia exactamente.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), Ec. (46)

- **Ubicación:** sección A.4.5, Ec. (46) (efecto de suelo del lado de la
  fuente ponderado por la difracción).
- **El impreso:** el exponente de ponderación lee
  $(\Delta L_{g,s'} - \Delta L_{d,s})/20$.
- **El problema:** no existe término alguno $\Delta L_{g,s'}$; la prosa
  justo debajo de la ecuación define $\Delta L_{d,s'}$ como «the attenuation
  due to the diffraction between the image source S′ and R», la Ec. (47)
  compañera del lado del receptor imprime el término paralelo correctamente
  como $\Delta L_{d,r'}$, y el método CNOSSOS-EU en el que se basa la sección
  escribe $\Delta_\text{ground}(S,O)$ con $\Delta_\text{dif}(S',R)$ en esa
  posición. El subíndice $g$ es una errata por $d$.
- **Evidencia:** consistencia interna de la sección (su propia prosa y la
  Ec. (47)) y la fuente CNOSSOS-EU de las ecuaciones.
- **Comportamiento de la biblioteca:** implementa el término de difracción de
  la fuente imagen $\Delta L_{d,s'}$ tal como lo define la prosa.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), referencias cruzadas del §A.4.5

- **Ubicación:** sección A.4.5, las definiciones bajo la Ec. (46) (p. 32
  impresa) y la Ec. (47) (p. 33 impresa).
- **El impreso:** cuatro referencias cruzadas a la eq. 44, en **tres**
  redacciones distintas: «calculated as per eq. 44» para $\Delta L_{d,s'}$ y
  de nuevo para $\Delta L_{d,s}$ bajo la Ec. (46); «calculated as in eq. 44»
  para $\Delta L_{d,r'}$ bajo la Ec. (47); y «calculated as in Subsection
  eq. 44» para $\Delta L_{d,s}$ bajo la Ec. (47). Una revisión anterior de
  esta entrada citaba las cuatro con la primera redacción.
- **El problema:** la Ec. (44) es el coeficiente de difracción múltiple
  $C''$; la atenuación por difracción es la Ec. (42). Las cuatro referencias
  cruzadas apuntan al coeficiente auxiliar en lugar de a la fórmula que
  describen, y la cuarta lleva además un «Subsection» colgado sin número de
  subsección detrás.
- **Evidencia:** los términos son atenuaciones en dB, que solo produce la
  Ec. (42); la Ec. (44) es un coeficiente adimensional que consume la
  Ec. (42). Verificado en las páginas 31 y 32 del PDF (pp. 32 y 33 impresas)
  de NORAH2 SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** evalúa los términos de difracción del
  camino imagen y directo con la Ec. (42), usando la Ec. (44) para $C''$
  dentro de ella.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), §A.3.5 Approach 3 (base del ralentí a régimen pleno)

- **Ubicación:** sección A.3.5, Approach 3, paso 3 (p. 18 impresa), contra la
  fila «Fl. idle» de la Tabla 3 (pp. 18-19 impresas).
- **El impreso:** el paso lee «add offset of 12 dB\* to derive out of ground
  hover from the in-ground hover disk, -12 dB\* to derive reduced-rpm idle
  from in-ground hover disk, and -2.5 dB\* to derive full-rpm idle from out
  of ground hover»; la tabla imprime
  $LA_{\mathrm{FL.idle}}(\theta) = LA_{\mathrm{HIGE}}(\theta) - 2.5\ \mathrm{dB}^*$.
- **El problema:** la prosa deriva el ralentí a régimen pleno del
  estacionario fuera del efecto suelo donde la tabla lo deriva del
  estacionario en efecto suelo, y las dos prescripciones caen a 12 dB una de
  otra (por la prosa,
  $LA_{\mathrm{HOGE}}(\theta) - 2.5 = LA_{\mathrm{HIGE}}(\theta) + 9.5$; por
  la tabla, $LA_{\mathrm{HIGE}}(\theta) - 2.5$). Solo la tabla conserva el
  orden físico de las condiciones (ralentí a régimen pleno por encima del
  ralentí a régimen reducido, ambos por debajo del estacionario en efecto
  suelo). El párrafo que introduce estas fases, al final de la sección A.3.3
  (p. 17 impresa), está él mismo sin terminar («For specific phases of a
  flight such as, turns, hover, taxiing»), apuntando a una pasada de edición
  que la sección no recibió.
- **Evidencia:** las correcciones distribuidas con la base de datos pública
  V2.0.74 son todas relativas al disco de estacionario en efecto suelo
  (`Fullrpmidle -2` en el fichero de consulta de interpolación de todos los
  tipos), concordando con la tabla y no con la prosa. Verificado en las
  páginas 16, 17 y 18 del PDF (pp. 17, 18 y 19 impresas) de NORAH2
  SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** `hover_derived_hemisphere` aplica
  todos los desplazamientos de la Tabla 3 desde el hemisferio de estacionario
  en efecto suelo, como imprime la tabla; el docstring declara la condición
  base explícitamente.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), asignación de rodaje del §A.3.5

- **Ubicación:** sección A.3.5, último párrafo (p. 19 impresa).
- **El impreso:** «To include taxiing for helicopters with and without wheels
  into the noise calculation the measured and derived hemispheres for
  in-ground hover and full-rpm idle respectively should be employed.»
- **El problema:** leído al pie de la letra, el «respectively» empareja el
  helicóptero con ruedas con la fuente de estacionario en efecto suelo y el
  sin ruedas con el ralentí a régimen pleno, que es lo contrario de las
  operaciones que modela: un helicóptero sin ruedas solo puede rodar en
  estacionario en efecto suelo, y uno con ruedas rueda por el suelo sobre sus
  ruedas con el rotor a ralentí gobernado, sin producir sustentación. Las dos
  listas se leen transpuestas. Ningún oráculo lo zanja (la publicación
  pública no distribuye caso de verificación de rodaje), así que el
  emparejamiento se corrige solo desde la física de las operaciones.
- **Evidencia:** comparación interna de las dos listas de la prosa contra las
  operaciones que nombran. Verificado en la página 18 del PDF (p. 19 impresa)
  de NORAH2 SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** ninguna función se ve afectada (la
  regla selecciona entre dos hemisferios que el lector ya ha construido); la
  guía de rotorcraft documenta el emparejamiento físico, rodaje sin ruedas
  sobre el hemisferio de estacionario en efecto suelo y rodaje con ruedas
  sobre el de ralentí a régimen pleno, con esta salvedad.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), desplazamientos de la Tabla 3 frente a las correcciones distribuidas

- **Ubicación:** Tabla 3, columna de Approach 3 (pp. 18-19 impresas), contra
  el bloque `&CORRECTIONS` de los ficheros de consulta de interpolación
  distribuidos con la publicación pública NORAH2 V2.0.74.
- **El impreso:** desplazamientos de +12 dB\* (estacionario fuera del efecto
  suelo), -12 dB\* (ralentí a régimen reducido) y -2.5 dB\* (ralentí a
  régimen pleno) desde el disco de estacionario en efecto suelo, con la nota
  del asterisco de que se derivaron de mediciones con micrófonos invertidos
  sobre placas de suelo y «may not be valid for other microphone setups».
- **El problema:** la base de datos de referencia sobre la que se construye
  la guía distribuye valores distintos: cada uno de los once ficheros de
  consulta de triangulación por tipo (``*_triangulation.int``) de la
  publicación pública lleva `Corr_dB` 8, -10 y -2 para las mismas tres
  operaciones, así que las constantes publicadas y la base de datos discrepan
  en 4, 2 y 0.5 dB. La guía, cuya sección A.3.1 declara los datos de consulta
  distribuidos parte de la base de datos de hemisferios y no editables, no
  menciona la diferencia, y su nota cuestiona la validez de los valores
  publicados sin nombrar los que de verdad se distribuyen.
- **Evidencia:** los bloques `&CORRECTIONS` idénticos de los once ficheros de
  consulta de triangulación (``*_triangulation.int``) de la publicación
  pública V2.0.74; las constantes publicadas verificadas en las páginas 17 y
  18 del PDF (pp. 18 y 19 impresas) de NORAH2 SC01.D1.5d
  (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** `hover_derived_hemisphere` usa por
  defecto las constantes publicadas de la Tabla 3 y acepta una corrección
  medida o de base de datos como ``offset_db``; el caso de verificación de
  estacionario de extremo a extremo pasa el +8 dB de la base de datos
  explícitamente, y el docstring registra la divergencia.
- **Estado:** sin notificar.

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

## Osses, García & Kohlrausch (2016), modelo de intensidad de fluctuación, Ec. (3)

- **Ubicación:** Ec. (3), la transformación a razón de banda crítica (Bark)
  del frontal de patrón de excitación.
- **El impreso:**
  $z(f) = 13 \cdot \arctan(0.76 \cdot 10^{-4} \cdot f) + 3.5 \cdot \arctan((f/7500)^2)$.
- **El problema:** el primer coeficiente es el $0.76 \cdot 10^{-3}$ de
  Zwicker-Terhardt con el exponente mal impreso. Las propias anclas del
  artículo desmienten el impreso: declara
  $0.5\ \text{Bark} = 50\ \text{Hz}$ y
  $23.5\ \text{Bark} = 13.2\ \text{kHz}$ (sección 2.1.2) y
  $15\ \text{Bark} = 2.7\ \text{kHz}$ (sección 3.1), todas las cuales exigen
  $10^{-3}$. Con $10^{-4}$, $z(1\ \text{kHz}) = 1.05$ en lugar de
  $8.51\ \text{Bark}$ y los 47 centros de filtro del modelo abarcarían de
  491 Hz a 20 kHz en lugar de 50 Hz a 13.2 kHz.
- **Evidencia:** evaluación de la Ec. (3) bajo ambos exponentes contra las
  anclas Bark/frecuencia impresas del artículo. El rango impreso de la
  sección 2.1.2, «0.5 Bark (50 Hz) to 23.5 Bark (13.2 kHz)», y el ancla de la
  sección 3.1, «15 Bark (2.7 kHz)», se reproducen todos bajo el
  $0.76 \cdot 10^{-3}$ de Zwicker-Terhardt (50.6 Hz, 13.07 kHz y 2.71 kHz) y
  ninguno bajo el exponente impreso. Verificado en la página 4 del PDF (p. 4
  impresa) de Osses, García & Kohlrausch, ICA:2016, con las anclas en la
  página 7 del PDF (p. 7 impresa) del mismo artículo.
- **Comportamiento de la biblioteca:** implementa $0.76 \cdot 10^{-3}$ con
  una nota junto a la fórmula; el test de barrido de frecuencia portadora
  cazaría una regresión al valor impreso
  ([`fluctuation_strength.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/fluctuation_strength.py)).
- **Estado:** sin notificar (artículo de congreso, no una norma).

## Medwin & Clay, Fundamentals of Acoustical Oceanography (1998), Ec. (3.4.30) (coeficiente del ácido bórico)

- **Ubicación:** el término de ácido bórico de Francois-Garrison tal como lo
  transcribe el libro, **Ec. (3.4.30), p. 110 impresa**. Una revisión
  anterior de esta entrada citaba la Ec. 3.4.29, que es la suma de absorción
  total de los tres términos en la p. 109 impresa; el bloque del ácido bórico
  es la ecuación siguiente.
- **El impreso:**
  $A_1 = (8.68/c) \cdot 10^{0.78\,\text{pH} - 5}\ \text{dB km}^{-1}\ \text{kHz}^{-1}$.
- **El problema:** el artículo original (Francois & Garrison 1982, JASA 72,
  Parte II, Ec. (10) y Fig. 7) imprime 8.86; los dígitos están traspuestos.
  Solo 8.86 reproduce la propia Tabla IV del artículo: con 8.68 las celdas
  dominadas por el bórico de $0.6$ a 30 kHz quedan hasta un $1.7\,\%$ por
  debajo de los totales impresos (peor caso relativo 2 kHz, 10 °C, $S = 35$:
  $0.1209$ contra los 0.123 dB/km impresos).
- **Evidencia:** recálculo de todas las celdas muestreadas de la Tabla IV
  bajo ambos coeficientes contra los valores impresos del artículo.
  Verificado en la página 131 del PDF (p. 110 impresa) de Medwin & Clay,
  Fundamentals of Acoustical Oceanography (1998), y en las páginas 8 y 9 del
  PDF (pp. 1886 y 1887 impresas) de Francois & Garrison (1982), JASA 72,
  Parte II, que imprimen el propio
  $A_1 = (8.86/c) \cdot 10^{0.78\,\text{pH} - 5}$ del artículo.
- **Comportamiento de la biblioteca:** implementa el 8.86 del artículo con
  una nota defensiva; el conjunto fijado de la Tabla IV incluye las filas
  dominadas por el bórico.
- **Estado:** sin notificar (libro, no una norma).

## Medwin & Clay (1998), Ec. (3.4.30) (la velocidad del sonido impresa como q)

- **Ubicación:** el mismo bloque de la Ec. (3.4.30), p. 110 impresa, su
  última línea.
- **El impreso:** $q = 1412 + 3.21T + 1.19 S + 0.0167 z\ \text{m/s}$.
- **El problema:** la cantidad que el bloque necesita es la velocidad del
  sonido $c$, que es por lo que dividen las dos líneas de arriba
  ($A_1 = 8.68/c$, y $A_2 = 21.44 S/c$ en el bloque del sulfato de magnesio
  de la misma página). Ningún símbolo $q$ se define en ninguna parte de la
  sección, así que el sistema transcrito no está cerrado: un lector que siga
  los símbolos impresos no tiene valor para $c$. Francois & Garrison 1982
  Parte II imprime el mismo polinomio como
  $c = 1412 + 3.21 T + 1.19 S + 0.0167 D$, introducido por «where c is the
  sound speed (m/s), given approximately by».
- **Evidencia:** el propio uso de $c$ del bloque dos líneas más arriba, y el
  artículo fuente. Verificado en la página 131 del PDF (p. 110 impresa) y la
  página 130 del PDF (p. 109 impresa) de Medwin & Clay (1998), y en la página
  8 del PDF (p. 1886 impresa) de Francois & Garrison 1982 Parte II (JASA 72).
- **Comportamiento de la biblioteca:** no le afecta; el modelo de absorción
  toma la velocidad del sonido del mismo polinomio bajo el nombre `c`.
- **Estado:** sin notificar (libro, no una norma).

---

## Maa (1998), «Potential of microperforated panel absorber», JASA 104(5), Ec. (5b)

- **Ubicación:** Ec. (5b), el coeficiente de reactancia de masa del panel
  microperforado, impreso como
  $k_m = 1 + [1 + k^2/2]^{-1/2} + 0.85\,d/t$.
- **El impreso:** el primer término entre corchetes lee
  $(1 + k^2/2)^{-1/2}$.
- **El problema:** la Ec. (4) del mismo artículo, de la que se factoriza
  (5b), imprime el término como $(3^2 + k^2/2)^{-1/2}$, y solo esa forma
  reproduce el límite de Crandall a $k$ bajo,
  $Z_1 \to (4/3) j\omega\rho_0 t$, de la propia Ec. (3a) del artículo: a
  $k \to 0$ la (5b) impresa da un factor de masa interna de 2 en lugar de
  4/3. La propia Fig. 1 del artículo lo confirma: con
  $0.85 \cdot d/t = 0.85$ el $k_m$ dibujado arranca cerca de $2.2$
  ($= 4/3 + 0.85$) a $k = 0.1$, no en $2.85$.
- **Evidencia:** recálculo de ambas variantes del corchete contra la Ec. (4),
  la Ec. (3a) y la curva de la Fig. 1; la solución exacta de Bessel de la
  Ec. (2) concuerda con la Ec. (4) dentro del $\sim 6\,\%$ que Maa declara
  solo con la forma $3^2$ (la forma 1 yerra en $>30\,\%$ a $k$ bajo).
  Verificado en la página 2 del PDF (p. 2862 impresa) de Maa (1998),
  «Potential of microperforated panel absorber», JASA 104(5), que lleva la
  Ec. (4) y la Ec. (5b) a quince líneas una de otra en la misma columna.
- **Comportamiento de la biblioteca:** implementa la Ec. (2) exacta (sin
  aproximación), así que la errata no entra en el código; el test de
  regresión ``test_maa_exact_vs_wide_range_approximation`` fija la solución
  exacta a la forma corregida de la Ec. (4).
- **Estado:** sin notificar (artículo de revista; la forma correcta aparece
  en los artículos anteriores de Maa de 1975/1987 y en literatura
  secundaria).

## Jiménez, Groby, Pagneux & Romero-García (2017), Appl. Sci. 7(6), 618, Ecs. (7)-(8)

- **Ubicación:** Ecs. (7) y (8), la densidad efectiva y el módulo de
  compresibilidad viscotérmicos de conducto rectangular (la serie de Stinson,
  usada para los cuellos y cavidades cuadrados del absorbente de ranura +
  resonador de Helmholtz).
- **El impreso:** la constante normalizadora inicial de ambas series es 4:
  $\rho_\text{eff} = -\rho_0 \cdot a^2 b^2/(4 \cdot G_\rho^2 \cdot \Sigma)$
  y el factor homólogo $4 \cdot (\gamma - 1) \cdot G_\kappa^2/(a^2 b^2)$
  dentro de $\kappa_\text{eff}$.
- **El problema:** la constante correcta es 64 (un error de factor 16). Solo
  64 reproduce los límites exactos del modelo: al desvanecerse las capas
  límite $\rho_\text{eff} \to \rho_0$ y $\kappa_\text{eff} \to \kappa_0$ (el
  4 impreso da $16 \cdot \rho_0$), y en continua el
  $j\omega \cdot \rho_\text{eff}$ del conducto cuadrado tiende a la
  resistividad de flujo de Poiseuille exacta de Shah-London: el valor de la
  serie $a^6/(64 \cdot S_0) = 28.4542$ casa con $fRe/2 = 28.455$ (en unidades
  de $\eta/a^2$), donde $S_0$ es la suma doble de modos transversales a
  $G = 0$; el 4 impreso da dieciséis veces eso.
- **Evidencia:** evaluación de ambas constantes contra los límites sin capa
  límite y el valor exacto de conducto cuadrado de Shah-London; el límite de
  conducto ancho de la serie también casa con el propio modelo de ranura de
  los artículos (Ec. (6)) solo con 64.
- **Comportamiento de la biblioteca:** implementa 64 con una nota en el
  docstring; los límites están fijados en
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py)
  y la comprobación de conformidad «Poiseuille limit (Stinson 1991)».
- **Estado:** sin notificar (artículo de revista, no una norma).

## Jiménez et al. (2017), Appl. Sci. 7(6), 618 / Sci. Rep. 7, 5389, término de radiación de la ranura

- **Ubicación:** Appl. Sci. Ec. (3), la impedancia de radiación
  característica de las ranuras, y la reimpresión idéntica en los Methods del
  artículo de metadifusores (Sci. Rep. 7, 5389, Ec. (5)).
- **El impreso:**
  $Z_{\Delta l_\text{slit}} = -i\omega \cdot \Delta l_\text{slit} \cdot \rho_0/(\phi t \cdot S_0)$.
- **El problema:** el término modela la masa de radiación añadida de la boca
  de la ranura, pero el prefactor $-i\omega$ impreso es una expresión del
  convenio temporal opuesto ($e^{-i\omega t}$), inconsistente con la cadena
  de matrices de transferencia por lo demás en $e^{+i\omega t}$ de los
  artículos (las matrices de ranura con $+i$ fuera de la diagonal de la
  Appl. Sci. Ec. (2) y la impedancia de resonador tipo cotangente con $-i$).
  Transcrita literalmente en esa cadena, la corrección sube la resonancia del
  panel de ranuras donde una masa añadida debe bajarla: para una ranura de
  1 mm con paso de red de 30 mm y periodo de 50 mm el pico de absorción se
  mueve de 378.6 Hz a 386.8 Hz tal como está impreso, contra 370.8 Hz con el
  signo de masa. Las correcciones de extremo de cuello del mismo modelo se
  comportan correctamente (bajan la resonancia del resonador).
- **Evidencia:** evaluación numérica de ambos signos de la corrección contra
  el panel sin corregir; la dirección de las correcciones de extremo de
  cuello de los mismos artículos como control consistente.
- **Comportamiento de la biblioteca:** usa el signo de masa añadida
  ($+j\omega$ en el convenio $e^{+j\omega t}$ de la biblioteca), conjugando
  el término impreso exactamente igual que conjuga la serie de conducto de
  Stinson de los artículos; dirección y pico están fijados por
  ``test_slit_radiation_correction_lowers_resonance`` en
  [`tests/materials/absorbers/test_slow_sound.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/absorbers/test_slow_sound.py).
- **Estado:** sin notificar (artículos de revista, no normas).

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Tabla 5.1

- **Ubicación:** Tabla 5.1, «Coefficient and exponent values in the Delany
  and Bazley, Miki and modified Miki models», fila «Miki [6,7]», coeficiente
  $r$.
- **El impreso:** $r = 0.0109$.
- **El problema:** la fuente original (Miki 1990, J. Acoust. Soc. Jpn (E)
  11(1), Ec. (34)) imprime
  $\beta(f) = (\omega/c_0)[1 + 0.109 \cdot (f/\sigma)^{-0.618}]$; la tabla
  pierde un dígito. Con 0.0109 la parte real del número de onda de Miki a
  $f/\sigma = 0.01$ es $1.19$ en lugar de $2.88$, inconsistente con la fila
  de Delany-Bazley de la misma tabla ($3.10$ desde sus propios $r = 0.0862$,
  $s = -0.693$) y con la fila del «modified Miki» que el propio libro deriva
  de ella.
- **Evidencia:** comprobación dígito a dígito contra el artículo original de
  Miki (1990) (Ecs. (30)–(34)) y cálculo cruzado de ambas variantes en el
  borde del rango de ajuste. Verificado en la página 168 del PDF (p. 149
  impresa) de Attenborough & Van Renterghem, Predicting Outdoor Sound
  2e:2021, y en la página 4 del PDF (p. 22 impresa) de Miki, J. Acoust. Soc.
  Jpn (E) 11(1):1990.
- **Comportamiento de la biblioteca:** implementa el 0.109 original de Miki;
  el punto de digitalización $f/\sigma = 0.1$ está fijado en
  ``tests/reference_data/`` y en la comprobación de conformidad «Miki 1990
  Eqs. (30)-(34)».
- **Estado:** sin notificar (libro, no una norma).

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Ec. (5.13)

- **Ubicación:** Ec. (5.13), la densidad compleja volumétrica de
  Johnson-Champoux-Allard, con
  $G(\Lambda) = \sqrt{1 - 4iT\eta\rho_0\omega/(R_S^2\Lambda^2\Omega^2)}$.
- **El impreso:** la tortuosidad $T$ aparece a la primera potencia dentro de
  $G(\Lambda)$.
- **El problema:** Johnson et al. (1987) y la formulación JCA estándar (Cox &
  D'Antonio 3e Ec. (6.19); Allard & Atalla) llevan ahí
  $T^2 = \alpha_\infty^2$. El impreso a la primera potencia rompe la asíntota
  de alta frecuencia que define la longitud característica viscosa: con $T^2$
  la densidad tiende a $(T\rho_0/\Omega)(1 + (1 - j)\delta_v/\Lambda)$ con
  $\delta_v = \sqrt{2\eta/\rho_0\omega}$, mientras que la forma impresa
  tiende a una corrección $\delta_v/(\Lambda\sqrt{T})$, que para $T = 2$
  supone un error del $29\,\%$ en el término de capa límite para la misma
  $\Lambda$.
- **Evidencia:** desarrollo asintótico de ambas variantes contra la
  definición de $\Lambda$ de Johnson et al. y contra la Ec. (6.19) de Cox &
  D'Antonio; el test JCA de alta frecuencia de la biblioteca fija el
  comportamiento con $T^2$. Verificado en la página 173 del PDF (p. 154
  impresa) de Predicting Outdoor Sound 2e:2021.
- **Comportamiento de la biblioteca:** implementa la forma estándar con $T^2$
  (Cox & D'Antonio Ec. (6.19)); la asíntota está fijada en
  ``test_high_frequency_density_asymptote``.
- **Estado:** sin notificar (libro, no una norma).

## Bies, Hansen & Howard, Engineering Noise Control 5e (2017), Ec. (8.141)

- **Ubicación:** sección 8.9.1, Ec. (8.141) (p. 461 impresa), la pérdida de
  transmisión de un silenciador desde los elementos de su matriz de cuatro
  polos total.
- **El impreso:**
  $$
  TL = 10 \lg\left[ \left(\frac{1+M_n}{1+M_1}\right)^2 \cdot \tfrac{1}{4} \cdot
  \left| \frac{Z_{A1}}{Z_{An}} T_{11} + \frac{T_{12}}{Z_{An}}
  + Z_{A1} T_{21} + \frac{Z_{An}}{Z_{A1}} T_{22} \right|^2 \right],
  $$
  es decir, con la razón de impedancias $Z_{A1}/Z_{An}$ ponderando $T_{11}$ y
  su inversa ponderando $T_{22}$.
- **El problema:** la fuente que la propia ecuación cita (Munjal, *Acoustics
  of Ducts and Mufflers* 2e, Ec. (3.27), p. 105) lleva el prefactor global
  $Z_{An}/Z_{A1}$ (equivalentemente $\sqrt{S_1/S_n}$ dentro de una forma en
  $20\log_{10}$) con $T_{11}$ sin ponderar y $Z_{A1}/Z_{An}$ sobre $T_{22}$.
  Tal como está impresa, la Ec. (8.141) falla el límite de expansión brusca:
  un elemento de longitud cero ($T = I$) entre $S_1 = 0.01\ \text{m}^2$ y
  $S_n = 0.02\ \text{m}^2$ es una expansión brusca de área con el clásico
  $TL = 10\log_{10}[(1+m)^2/(4m)] = 0.512\ \text{dB}$ ($m = S_n/S_1 = 2$),
  pero la ecuación impresa da
  $\tfrac{1}{4} \cdot (Z_{A1}/Z_{An} + Z_{An}/Z_{A1})^2 = 1.938\ \text{dB}$.
  Leer las razones como un prefactor global $Z_{A1}/Z_{An}$ también está mal:
  da 6.532 dB sobre el mismo oráculo y viola la reciprocidad ($11.34$ contra
  -0.70 dB para una cámara de expansión entre tubos desiguales; una TL
  negativa para un elemento pasivo). La errata es invisible siempre que las
  áreas de entrada y salida son iguales, donde todas las variantes se reducen
  a la Ec. (8.148).
- **Evidencia:** evaluación numérica del elemento identidad de longitud cero
  y de una cámara de expansión de puertos desiguales bajo la forma impresa,
  el prefactor invertido y la Ec. (3.27) de Munjal; solo la forma de Munjal
  reproduce el clásico de la expansión brusca (0.512 dB, en ambos sentidos) y
  es recíproca.
- **Comportamiento de la biblioteca:** `transmission_loss` en
  [`silencers.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencers.py) implementa
  la Ec. (3.27) de Munjal, con el límite de expansión brusca y la
  reciprocidad de la TL fijados por tests de regresión
  ([`tests/noise_control/test_silencers.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_silencers.py))
  y una nota defensiva junto a la fórmula.
- **Estado:** sin notificar (libro, no una norma).

## Long, Architectural Acoustics 2e (2014), Ec. (18.24) (signo de la directividad del micrófono)

- **Ubicación:** capítulo 18, «Multiple Open Microphones», Ec. (18.24)
  (p. 699 impresa), el criterio de estabilidad de ganancia antes de
  realimentación generalizado a varios micrófonos abiertos.
- **El impreso:**
  $Z_S + L_{H-M} + \Delta L_\text{nom} \le L_{H-L} \boldsymbol{+} D_M(\theta) - 10$,
  con el índice de directividad del micrófono entrando en el lado derecho con
  signo más.
- **El problema:** la Ec. (18.24) es la generalización a número de micrófonos
  abiertos de la Ec. (18.20) (p. 698 impresa), que lee
  $Z_S + L_{H-M} \le L_{H-L} \boldsymbol{-} D_M(\theta) - 10$ y que se sigue
  a su vez de la condición de oscilación Ec. (18.19),
  $Z_S + L_{H-M} = L_{H-L} - D_M(\theta)$, obtenida sustituyendo la ganancia
  del lazo de realimentación $G_S = L_{H-M} - L_{H-L} + D_M(\theta)$
  (Ec. (18.18)) en $Z_S + G_S = 0$ (Ec. (18.16)). Poner $N_m = 1$ hace
  $\Delta L_\text{nom} = 0$, así que la Ec. (18.24) debe reducirse a la
  Ec. (18.20) y no lo hace. El signo importa físicamente: $D_M(\theta)$ es
  «usually negative» en la propia definición de Long (en torno a $-2$ a
  -3 dB para un cardioide apuntado al orador), así que tal como está impreso
  un micrófono direccional *costaría* ganancia antes de realimentación en
  lugar de comprarla, invirtiendo la propia conclusión del capítulo de que
  «it is prudent to incorporate a cardioid or hypercardioid microphone into a
  system».
- **Evidencia:** la ecuación impresa lee
  $Z_S + L_{H-M} + \Delta L_\text{nom} \le L_{H-L} + D_M(\theta) - 10$,
  contra $Z_S + L_{H-M} \le L_{H-L} - D_M(\theta) - 10$ dos páginas antes,
  donde la misma posición lleva un menos. (Una revisión anterior de esta
  entrada citaba la extracción de `pdftotext`,
  `Z S þ L HM þ DL nom  L HL þ D M ðqÞ  10`, en la que `þ` es la ligadura que
  este PDF usa para «+» y todos los signos menos se han perdido por completo;
  esa extracción no puede distinguir un más de un menos y nunca debió ser la
  evidencia.) Verificado en la página 697 del PDF (p. 699 impresa) y la
  página 696 del PDF (p. 698 impresa) de Long, Architectural Acoustics 2e
  (2014). El signo menos es el que reproduce los propios casos particulares
  resueltos de Long a $N_m = 1$: con $Z_S = -6\ \text{dB}$, la Ec. (18.21) da
  $L_{H-M} \le L_{H-L} - D_M(\theta) - 4$ (un micrófono omnidireccional 4 dB
  por debajo del nivel medio de la audiencia), y la Ec. (18.22) da
  $L_{H-M} \le L_{H-L} - 2$ para un cardioide a $D_M = -2\ \text{dB}$.
  Ninguno de los dos casos particulares es recuperable desde la Ec. (18.24)
  impresa.
- **Comportamiento de la biblioteca:** `feedback_stability` en
  [`sound_reinforcement.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/sound_reinforcement.py)
  implementa el signo de la Ec. (18.20), con una nota junto al criterio.
  Ambos casos particulares de Long están fijados por tests de regresión
  ([`tests/electroacoustics/test_sound_reinforcement.py`](https://github.com/jmrplens/phonometry/blob/main/tests/electroacoustics/test_sound_reinforcement.py))
  y por las comprobaciones de conformidad «Long, Architectural Acoustics 2e,
  Eq. (18.21)» y «Eq. (18.22)».
- **Estado:** sin notificar (libro, no una norma, así que no normativo).

## Long, Architectural Acoustics 2e (2014), Ec. (17.53) (constante de la cota de comunicación)

- **Ubicación:** capítulo 17, «Restaurant Design», Ec. (17.53) (p. 666
  impresa), la absorción mínima por mesa ocupada para una comunicación entre
  mesas adecuada.
- **El impreso:** $A_\text{tab} > 6.33 r_s^2$.
- **El problema:** la cota es la Ec. (17.52),
  $L_\text{SN} = 10\log_{10}[Q/(4\pi r^2)] + 10\log_{10}[A_\text{tab}/4]$,
  resuelta para $A_\text{tab}$ en el umbral declarado
  $L_\text{SN} > -6\ \text{dB}$, lo que da
  $A_\text{tab} > 16\pi \cdot 10^{-0.6} r_s^2/Q$. Con el $Q = 2$ que el
  capítulo usa para un orador, esa constante es 6.3130, no 6.33. La brecha es
  del $0.27\,\%$, es decir, el último dígito impreso: 6.33 es lo que devuelve
  $16\pi \cdot 10^{-0.6}/2$ si $10^{-0.6}$ se arrastra grueso como 0.252 en
  lugar de 0.251 19. Se clasifica como discrepancia de redondeo y no como
  error estructural de la fórmula, ya que la fórmula misma queda confirmada
  por su compañera (abajo) y ninguna suposición alternativa consistente
  reproduce 6.33 (exigiría $Q = 1.995$).
- **Evidencia:** la Ec. (17.54) inmediatamente siguiente es la misma forma
  cerrada en el umbral de privacidad $L_\text{SN} < -9\ \text{dB}$, y su
  constante impresa 3.16 es exactamente lo que da
  $16\pi \cdot 10^{-0.9}/2 = 3.1640$, confirmando la fórmula y el $Q = 2$.
  Solo la constante de -6 dB está desviada. Lo que *no* discrimina es la
  prosa de Long un párrafo después, «at least 6.3 or more square meters (68
  sq ft) of absorption per table»: 6.313 m² son $67.95\ \text{ft}^2$ y
  6.33 m² son $68.14\ \text{ft}^2$, así que ambos se imprimen como 68 sq ft,
  y ambos redondean a 6.3 m². Una revisión anterior de esta entrada ofrecía
  esa conversión como corroboración. Verificado en la página 665 del PDF
  (p. 666 impresa) de Long, Architectural Acoustics 2e (2014).
- **Comportamiento de la biblioteca:** `absorption_per_table` en
  [`crowd_noise.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/crowd_noise.py) calcula la cota
  desde la Ec. (17.52) en lugar de cablear ninguna de las dos constantes, así
  que ambas cotas se mantienen mutuamente consistentes; el valor 6.313 y el
  3.16 impreso están fijados por tests de regresión
  ([`tests/room/test_crowd_noise.py`](https://github.com/jmrplens/phonometry/blob/main/tests/room/test_crowd_noise.py)) y
  la constante 3.16 por la comprobación de conformidad «Long, Architectural
  Acoustics 2e, Eq. (17.54)».
- **Estado:** sin notificar (libro, no una norma, así que no normativo);
  clasificado como discrepancia de redondeo y no como defecto estructural.

## Long, Architectural Acoustics 2e (2014), Tabla 14.7 (filas de codos redondos)

- **Ubicación:** capítulo 14, Tabla 14.7, «Insertion Loss of Round Elbows»
  (p. 541 impresa), indexada por el producto frecuencia-anchura $f w$ (kHz
  por pulgadas).
- **El impreso:** solo cuatro filas: $f w < 1.9$ → 0 dB; $1.9 < f w < 3.8$ →
  1 dB; $3.8 < f w < 7.5$ → 2 dB; $f w > 15$ → 3 dB.
- **El problema:** la banda $7.5 < f w < 15$ no tiene fila alguna, así que la
  tabla salta de $3.8 < f w < 7.5$ directamente a $f w > 15$. Un cálculo por
  conductos cae en esa banda con normalidad: un codo de $24\ \text{in}$ a
  500 Hz tiene $f w = 12$.
- **Evidencia:** los mismos datos adaptados de la misma fuente ASHRAE
  aparecen en Bies, Hansen & Howard, *Engineering Noise Control* 5e, Tabla
  8.11, indexados por $W/\lambda$ ($= 0.074\,f w$). Su columna de codos
  redondos tiene seis filas, 0/1/2/3/3/3, y da 3 dB para
  $0.55 \le W/\lambda < 1.11$, que es exactamente la banda $7.5 < f w < 15$
  que Long omite. Las cuatro filas de Long se mapean sobre las seis de Bies
  así: las tres primeras coinciden entrada por entrada, la cuarta
  ($f w > 15$, 3 dB) fusiona legítimamente las dos filas superiores idénticas
  de Bies, y la banda sin fila es la cuarta de Bies. Una revisión anterior de
  esta entrada decía que «las Tablas 14.5 y 14.6 llevan ambas seis filas» y
  que «las otras cinco filas de las dos tablas coinciden entrada por
  entrada»; en la página, la Tabla 14.5 lleva seis filas y la Tabla 14.6
  cinco (fusiona las mismas dos bandas superiores idénticas, legítimamente),
  y la Tabla 14.7 imprime cuatro, así que ninguno de los dos recuentos es
  correcto. Verificado en la página 542 del PDF (p. 541 impresa) y la página
  541 del PDF (p. 540 impresa) de Long, Architectural Acoustics 2e (2014).
- **Comportamiento de la biblioteca:** `elbow_insertion_loss` en
  [`hvac.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) lleva la columna
  redonda de seis filas con 3 dB en la banda que falta, fijada por
  `test_elbow_tables_by_frequency_width_product`
  ([`tests/noise_control/test_hvac_long.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_hvac_long.py)).
- **Estado:** sin notificar (libro, no una norma).

## Long, Architectural Acoustics 2e (2014), Ec. 13.28 (unidades de U_G)

- **Ubicación:** capítulo 13, Ec. 13.28 (p. 521 impresa), el coeficiente de
  caída de presión normalizado
  $\xi = 334.9 \cdot \Delta P/(\rho_0 U_G^2)$ del modelo de potencia sonora
  de difusores.
- **El impreso:** la nomenclatura bajo la ecuación da «U_G = flow velocity
  prior to the diffuser (ft/min)» y, en la línea siguiente, «= Q/(60·S_G)
  (for Q in cfm)».
- **El problema:** las dos declaraciones se contradicen. $Q$ en ft³/min
  dividido por $60 S_G$ es una velocidad en **ft/s**, no ft/min, y solo la
  lectura en ft/s hace correcta la constante: $334.9/\rho_0$ con
  $\rho_0 = 0.075\ \text{lb/ft}^3$ es $4465 \cdot \Delta P/U^2$, que es la
  relación estándar de presión de velocidad $\Delta P/(U/4005)^2$ solo cuando
  $U$ se convierte desde ft/s. Leído como ft/min el coeficiente sale 3600
  veces demasiado pequeño. La propia Ec. 13.27 declara $U_G$ en ft/s, así que
  la etiqueta «(ft/min)» bajo la Ec. 13.28 es la discordante.
- **Evidencia:** comprobación dimensional de $Q/(60 S_G)$; reconstrucción de
  la constante $334.9/\rho_0$ desde la relación de presión de velocidad; y la
  frecuencia de pico. Lo que **no** discrimina es el nivel global: la
  Ec. 13.27 lleva $30\log_{10}\xi + 60\log_{10} U_G$, y sustituir la
  Ec. 13.28 hace que la velocidad se cancele idénticamente,
  $30\log_{10}\xi + 60\log_{10} U_G = 30\log_{10}(334.9 \Delta P/\rho_0)$.
  Para el difusor de impulsión de la Tabla 14.9 ($S_G = 4\ \text{ft}^2$,
  $Q = 312$ cfm, $\Delta P = 0.05$ in w.g.) ambas lecturas devuelven por
  tanto el mismo $L_W = 45.18\ \text{dB}$. Una revisión anterior de esta
  entrada afirmaba que la lectura en ft/min «lo falla por 100 dB», cosa
  aritméticamente imposible para una cantidad que no depende de la velocidad
  en absoluto. Lo que sí discrimina es la Ec. 13.32, $f_P = 48.8 U_G$, que es
  el único otro lugar donde entra $U_G$: leída en ft/s la velocidad de
  aproximación es $1.3\ \text{ft/s}$ y el pico cae a 63.4 Hz, es decir, en la
  octava de 63 Hz, así que la forma de la Ec. 13.31 pone 33.4 dB en esa banda
  contra los 33 impresos; leída en ft/min es $78\ \text{ft/min}$, el pico se
  mueve a 3 806 Hz, y la misma forma pone -8.2 dB en la banda de 63 Hz.
  Verificado en la página 522 del PDF (p. 521 impresa) de Long, Architectural
  Acoustics 2e (2014).
- **Comportamiento de la biblioteca:** `diffuser_sound_power` en
  [`hvac.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) lee $U_G$ en ft/s
  internamente (SI en la interfaz), con la fila de la Tabla 14.9 fijada por
  `test_diffuser_sound_power_reproduces_the_table_14_9_row`
  ([`tests/noise_control/test_hvac_long.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_hvac_long.py))
  y la comprobación de conformidad «Long 2e Eqs. 13.27-13.33».
- **Estado:** sin notificar (libro, no una norma).

## Vigran, Building Acoustics (2008), pie de la Figura 8.37 (exponente de la rigidez de la moqueta)

- **Fuente no normativa** (libro).
- **Ubicación:** sección 8.4.2, el pie de la Figura 8.37 en la p. 320 impresa
  / p. 341 del PDF, que etiqueta las curvas de mejora predicha de dos
  revestimientos de suelo colocados sobre un suelo pesado.
- **El impreso:** «Predicted improvement with a linear model: stiffness of
  carpet squares 3.2·10^6 N/m, vinyl covering 5.2·10^6 N/m.» (Vigran escribe
  el separador decimal como punto.)
- **El problema:** el exponente de la moqueta está un orden de magnitud alto.
  El cuerpo del texto que introduce la figura, en la p. 321 impresa, dice de
  las losetas de moqueta que «we have assumed that the covering has the same
  stiffness as used in Figure 8.36», y la Figura 8.36 está etiquetada
  $s = 3.2 \cdot 10^{5}\ \text{N/m}$ dentro del gráfico, el mismo valor que
  el cuerpo del texto de la p. 320 impresa le da. El valor del vinilo del
  mismo pie es correcto.
- **Evidencia:** la p. 320 impresa declara $3.2 \cdot 10^{5}\ \text{N/m}$
  «giving a resonance frequency f0 of approximately 130 Hz with a hammer mass
  of 0.5 kg», y $\sqrt{3.2 \cdot 10^{5}/0.5}/(2\pi) = 127.3\ \text{Hz}$ lo
  reproduce mientras que
  $\sqrt{3.2 \cdot 10^{6}/0.5}/(2\pi) = 402.6\ \text{Hz}$ es una frecuencia
  que no aparece en ningún lugar de la sección. La misma aritmética aplicada
  al valor del vinilo del pie da
  $\sqrt{5.2 \cdot 10^{6}/0.5}/(2\pi) = 513.3\ \text{Hz}$ contra los
  «approximately 510 Hz» impresos en la p. 321, lo que fija la fórmula y la
  masa de martillo que usó el autor. Gráficamente, las dos curvas de
  predicción a trazos de la Fig. 8.37 están a unas dos octavas una de otra,
  casando con la razón de rigideces
  $5.2 \cdot 10^{6}/(3.2 \cdot 10^{5}) = 16.25$ (un factor 4.03 en
  frecuencia) y no con
  $5.2 \cdot 10^{6}/(3.2 \cdot 10^{6}) = 1.63$ (un factor 1.27). Verificado
  en la página 341 del PDF (p. 320 impresa) de Vigran, Building
  Acoustics:2008, en la que ambos exponentes del pie leen 6 sin ambigüedad y
  el cuerpo del texto de la misma página lee
  $3.2 \cdot 10^{5}\ \text{N/m}$, con el argumento circundante leído en la
  página 340 del PDF (p. 319 impresa) y la página 342 del PDF (p. 321
  impresa) de la misma edición.
- **Comportamiento de la biblioteca:** no hizo falta ninguno; la biblioteca
  toma la rigidez del revestimiento del usuario a través de
  `covering_contact_stiffness`, y las frecuencias de corte impresas en las
  que está anclada vienen de Hopkins y no de este pie.
- **Estado:** sin notificar.

## Norton & Karczub, Fundamentals of Noise and Vibration Analysis for Engineers 2e (2003), Ec. (6.56)

- **Ubicación:** sección 6.6.1, Ec. (6.56), el factor de pérdida por
  acoplamiento de dos placas homogéneas unidas por $N$ conexiones puntuales
  (p. 418 impresa).
- **El impreso:** el corchete del denominador
  $(\rho_{s1}^2 h_1^2 c_{L1}^2 + \rho_{s2}^2 h_2^2 c_{L2}^2)$ aparece a la
  primera potencia.
- **El problema:** tal como está impresa, la expresión no es adimensional. El
  prefactor $4 N h_1 c_{L1}/(\sqrt{3}\,\omega S_1)$ ya tiene las dimensiones
  de $\text{m}^2\,\text{s}^{-1}$ sobre $\text{m}^2\,\text{s}^{-1}$, es decir,
  la unidad, así que la razón restante de los dos productos entre corchetes
  debe ser adimensional también. Eso exige que la suma esté al cuadrado,
  $A_1 A_2/(A_1 + A_2)^2$.
- **Evidencia:** la propia respuesta del libro al problema 6.13 (p. 617
  impresa). Con el denominador al cuadrado el par de aluminio de doce pernos
  da $\eta_{12} = 1.43 \cdot 10^{-2}$ a 125 Hz contra el
  $1.44 \cdot 10^{-2}$ impreso, y casa con toda la columna de 125 Hz a 2 kHz
  a mejor del $0.7\,\%$; con el denominador impreso (sin cuadrado) el
  resultado no es un factor de pérdida en absoluto. Verificado en la página
  438 del PDF (p. 418 impresa) de Norton & Karczub, Fundamentals of Noise and
  Vibration Analysis for Engineers 2e:2003.
- **Comportamiento de la biblioteca:**
  `point_connection_coupling_loss_factor` en
  [`junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/structural/junction_transmission.py)
  implementa la forma al cuadrado, con la columna impresa fijada por un test
  de regresión
  ([`tests/vibration/structural/test_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_junction_transmission.py))
  y una nota junto a la fórmula.
- **Estado:** sin notificar (libro, no una norma).

## Norton & Karczub 2e (2003), respuesta del problema 6.13 (columna eta_21)

- **Ubicación:** respuestas a los problemas, problema 6.13 (p. 617 impresa),
  las dos columnas de $\eta_{21}$ de las tablas soldada y atornillada.
- **El impreso:** para las dos placas de aluminio (placa 1: 3 mm,
  2.5 m × 1.2 m; placa 2: 5.5 mm, 2.0 m × 1.2 m) la respuesta da, a 125 Hz,
  $\eta_{21} = 5.77 \cdot 10^{-3}$ (soldada) y $2.64 \cdot 10^{-2}$
  (atornillada).
- **El problema:** ambas columnas son exactamente la columna $\eta_{12}$
  correspondiente multiplicada por $h_2/h_1 = 1.833$. La relación de
  consistencia SEA es $n_1 \eta_{12} = n_2 \eta_{21}$ (Ec. 6.8) con la
  densidad modal de placa plana $n = S\sqrt{12}/(2 c_L h)$ de la Ec. (6.25),
  así que el factor correcto es
  $n_1/n_2 = (S_1 h_2)/(S_2 h_1) = 2.292$. La columna impresa pierde la razón
  de áreas de placa $S_1/S_2 = 1.25$.
- **Evidencia:** la razón de las columnas impresas es 1.8333 a cinco dígitos
  en todas las bandas de ambas tablas, que es $h_2/h_1$ exactamente; las
  propias columnas de $\eta_{12}$ se reproducen desde las Ecs. (6.52) a
  (6.56) a mejor del 0.7 %. Verificado en la página 637 del PDF (p. 617
  impresa) de Norton & Karczub 2e:2003, la página que lleva ambas tablas de
  respuestas.
- **Comportamiento de la biblioteca:** las columnas de $\eta_{12}$ se usan
  como oráculo de regresión; $\eta_{21}$ se obtiene de la Ec. (6.8) con las
  densidades modales completas, y un test fija la razón 2.292 explícitamente
  ([`tests/vibration/structural/test_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_junction_transmission.py)).
- **Estado:** sin notificar (libro, no una norma).

## Norton & Karczub 2e (2003), problema 6.10 (área de la plataforma)

- **Ubicación:** problemas, problema 6.10 (pp. 593-594 impresas) y su
  respuesta (p. 617 impresa): una plataforma de satélite acoplada a un
  cilindro de aluminio, octava de 500 Hz, respuestas impresas
  $\eta_{12} = 4.26 \cdot 10^{-4}$, $\eta_{21} = 3.92 \cdot 10^{-4}$ y
  $\Pi_\text{in} = 1.31\ \text{W}$.
- **El impreso:** el enunciado da la plataforma de aluminio como «5 mm thick
  and 3.5 m × 3 m», es decir, 10.5 m².
- **El problema:** esa área es inconsistente con las tres respuestas
  impresas. La Ec. (6.12) fija
  $E_1/E_2 = (\eta_2 + \eta_{21})/\eta_{12} = 6.554$ desde los factores de
  pérdida impresos solos, mientras que la geometría enunciada con las
  velocidades impresas (27.2 y 13.2 mm/s) da 7.88. La razón de energías es
  independiente de las densidades modales y de la velocidad de onda, así que
  ninguna elección de esas puede reconciliarla; solo el área de la plataforma
  puede. El área que las respuestas implican es 8.73 m², que es
  $3.5 \times 3$ menos la huella $\pi(0.75\ \text{m})^2$ del cilindro que la
  Fig. P6.10 muestra atravesando la plataforma.
- **Evidencia:** con 8.73 m² la inversión de las Ecs. (6.15), (6.8) y (6.10)
  devuelve $\eta_{12} = 4.256 \cdot 10^{-4}$,
  $\eta_{21} = 3.910 \cdot 10^{-4}$ y $\Pi_\text{in} = 1.306\ \text{W}$, es
  decir, las tres respuestas impresas dentro del 0.4 %; la energía y la
  densidad modal del propio cilindro salen sin cambios en cualquier caso.
  Verificado en la página 613 del PDF (p. 593 impresa), que lleva el
  enunciado y sus dimensiones, y la página 637 del PDF (p. 617 impresa), que
  lleva las tres respuestas, de Norton & Karczub 2e:2003.
- **Comportamiento de la biblioteca:** `power_injection_clf` en
  [`experimental_sea.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/structural/experimental_sea.py)
  implementa la inversión tal como está publicada; el test de regresión usa
  el área libre de la plataforma y documenta la discrepancia
  ([`tests/vibration/structural/test_experimental_sea.py`](https://github.com/jmrplens/phonometry/blob/main/tests/vibration/structural/test_experimental_sea.py)).
- **Estado:** sin notificar (libro, no una norma).

## Norton & Karczub 2e (2003), problema 3.14 (factor de pérdida estructural)

- **Ubicación:** problemas, problema 3.14 (p. 580 impresa) y su respuesta
  (p. 611 impresa): la pérdida de transmisión por bandas de octava de un
  panel de aglomerado de 20 mm.
- **El impreso:** el enunciado da al panel un factor de pérdida estructural
  de «~1.5 × 10⁻²»; la respuesta da 27 dB a 8 kHz y 38.6 dB a 16 kHz.
- **El problema:** esos dos valores están por encima de la frecuencia crítica
  del panel (4885 Hz para el aglomerado del Appendix 4,
  $f_c t = 97.7\ \text{m/s}$) y siguen por tanto la Ec. (3.110) de Cremer,
  que contiene $10\log_{10}(\eta)$. Con $\eta = 1.5 \cdot 10^{-2}$ la
  ecuación da 37.0 dB y 48.5 dB, diez decibelios por encima de las respuestas
  impresas; con $\eta = 1.5 \cdot 10^{-3}$ da 27.0 dB y 38.5 dB.
- **Evidencia:** el desplazamiento de 10 dB es exactamente una década de
  $10\log_{10}(\eta)$, y la dependencia en frecuencia del par impreso fija de
  forma independiente $f_c = 4939\ \text{Hz}$ contra el valor del Appendix 4
  de 4885 Hz. Los ocho valores por debajo de la coincidencia se reproducen
  exactamente desde la Ec. (3.104) y no involucran $\eta$. La discrepancia es
  una década en un exponente impreso, así que las dos cifras se leyeron como
  imágenes y no a través de la capa de texto. Verificado en la página 600 del
  PDF (p. 580 impresa) y la página 631 del PDF (p. 611 impresa) de Norton &
  Karczub 2e (2003).
- **Comportamiento de la biblioteca:** el test de regresión usa
  $\eta = 1.5 \cdot 10^{-3}$, el valor que las respuestas impresas exigen
  ([`tests/building/prediction/test_panel_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_panel_transmission.py)).
- **Estado:** sin notificar (libro, no una norma).

---

## Vigran, Building Acoustics (2008), Ec. (9.18) (coeficiente del lado receptor)

- **Ubicación:** sección 9.2.3.2, Ec. (9.18) (p. 339 impresa), el factor de
  transmisión del modelo unidimensional de plénum de techo suspendido según
  Mechel (1980).
- **El impreso:** el denominador lee $m_S L_S \cdot m_R L_R h$ con el $m_R$
  **sin prima**, mientras que el exponente de la misma expresión lleva el
  $m'_R = m_R + s_R \tau_R / h$ con prima de la Ec. (9.17).
- **El problema:** los dos lados del plénum se integran de la misma manera.
  La integral del lado receptor es
  $\int_0^{L_R} \exp(-\varepsilon m'_R x)\,dx = (1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R)$,
  así que el factor que la normaliza debe ser $m'_R L_R$, exactamente igual
  que el del lado emisor es $m_S L_S$. Leída al pie de la letra, la expresión
  impresa no es un factor de transmisión en absoluto: arrastra un
  $m'_R/m_R = 1 + s_R \tau_R/(h m_R)$ espurio, así que crece sin cota cuando
  cae el amortiguamiento del plénum. Dos consecuencias son visibles con
  entradas corrientes ($L_S = L_R = 5\ \text{m}$, $h = 0.6\ \text{m}$,
  $R_S = R_R = 25\ \text{dB}$, $\varepsilon = 2$, $s_S = s_R = 0.5$): el
  modelo **diverge cuando el amortiguamiento del plénum se desvanece**, dando
  $R_\text{cl} = 40.26\ \text{dB}$ a $m_R = 0.01\ \text{1/m}$ pero solo
  26.48 dB a $10^{-4}$ y 6.64 dB a $10^{-6}$, contra los 40.85 dB finitos que
  la lectura deducida devuelve para el mismo plénum desnudo, donde el término
  de fuga $s_R \tau_R/h$ acota el camino; un plénum sin absorbente alguno se
  predice por tanto arbitrariamente peor que el valor limitado por la fuga en
  lugar de igual a él. También **rompe la conservación de la energía**,
  devolviendo $\tau_\text{cl} = 4.45$ a $R_S = R_R = 6\ \text{dB}$,
  $m_R = 0.01$ y $\tau_\text{cl} = 829$ a $R_S = R_R = 0\ \text{dB}$,
  $m_R = 10^{-3}$.
- **Evidencia:** con $m'_R$ en el denominador todas esas patologías
  desaparecen: $\tau_\text{cl}$ se aplana sobre el valor limitado por la fuga
  cuando el amortiguamiento se desvanece, donde la forma impresa sigue
  creciendo, y está acotado por arriba por 1 porque
  $(1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R L_R) \le 1$, y se
  reduce al propio resultado de atenuación pequeña de Vigran, la Ec. (9.19)
  $\tau_\text{cl} = \varepsilon^2 \tau_S \tau_R L_R/(4h)$, siempre que
  $m_S L_S$ y $m'_R L_R$ son ambos pequeños. Con el $m_R$ impreso el mismo
  límite recoge el factor $m'_R/m_R$, que diverge, así que la Ec. (9.18) tal
  como está impresa no se reduce a la Ec. (9.19) en absoluto: las dos
  ecuaciones que el libro presenta como pareja son inconsistentes entre sí.
  Verificado en la página 361 del PDF (p. 339 impresa) de Vigran, Building
  Acoustics:2008, que muestra el denominador llevando el $m_R$ sin prima
  mientras el exponente de la misma expresión lleva el $m'_R$ con prima de la
  Ec. (9.17).
- **Comportamiento de la biblioteca:** `plenum_flanking_reduction_index` en
  [`ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/prediction/ceiling_plenum.py)
  implementa el $m'_R$ deducido en el exponente y en el denominador, con la
  lectura documentada junto a la fórmula, y rechaza un factor de transmisión
  por encima de la unidad en lugar de reportar un índice de reducción sonora
  negativo. Los tests fijan la física que el modelo debe (monotonía en el
  amortiguamiento, la cota $\tau_\text{cl} \le 1$, el tamaño del término de
  fuga de la Ec. (9.17) en un techo realista) y la única propiedad que separa
  las dos lecturas: un plénum desnudo no peor que el valor sin amortiguar de
  la Ec. (9.20)
  ([`tests/building/prediction/test_ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_ceiling_plenum.py)).
- **Estado:** sin notificar (libro, no una norma). El artículo original de
  Mechel de 1980, que Vigran reproduce, no estuvo disponible para comprobar
  si la errata se origina allí.

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

---

## Directiva (UE) 2015/996 de la Comisión, Anexo II 2.2.1 (rango de bandas de octava de la fuente de carretera)

- **Ubicación:** el Anexo, punto 2.2.1, segundo párrafo bajo el encabezado
  «Traffic flow» (DO L 168, 1.7.2015, p. 8).
- **El impreso:** «these sound power levels are calculated for each octave
  band i from 125 Hz to 4 kHz».
- **El problema:** el modelo de fuente de carretera contradice su propia base
  de datos de coeficientes. Todas las tablas dependientes de banda del
  Appendix F, tanto en el texto de 2015 como en la versión sustituida por la
  (UE) 2021/1226, están impresas sobre las ocho bandas de octava de **63 Hz a
  8 kHz** (la Tabla F-3 no tiene columnas de frecuencia), y el punto 2.1.1
  del mismo Anexo define el rango de frecuencias del método como 63 Hz a
  8 kHz. Un cálculo restringido a 125 Hz - 4 kHz descartaría en silencio las
  bandas de 63 Hz y 8 kHz, que el Appendix F tabula como todas las demás.
- **Evidencia:** corregido por la corrección de errores publicada en el
  DO L 5, 10.1.2018, p. 35, que lee íntegra: 'On page 8, in the Annex, in
  point 2.2.1, in the second paragraph under the heading "Traffic flow": for:
  "each octave band i from 125 Hz to 4 kHz", read: "each octave band i from
  63 Hz to 8 kHz"'. La misma corrección de errores añade además «octave
  bands» al rango de frecuencias de 2.1.1. Verificado en la página 8 del PDF
  (p. L 168/8 impresa) de la Directiva (UE) 2015/996:2015 para la
  restricción impresa, en la página 1 del PDF (p. L 5/35 impresa) de la
  corrección de errores para ambos puntos, y en la página 4 del PDF
  (p. L 168/4 impresa) y la página 124 del PDF (p. L 168/124 impresa) de la
  Directiva para el rango conforme.
- **Comportamiento de la biblioteca:**
  [`cnossos_road`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/cnossos_road.py)
  trabaja sobre la rejilla corregida de 63 Hz a 8 kHz
  (`ROAD_OCTAVE_BANDS`), fijada por
  `test_octave_bands_are_the_corrected_range` y por los casos del libro de
  cálculo, cuyos niveles publicados cubren las ocho bandas.
- **Estado:** corregido por el organismo emisor (corrección de errores del 10
  de enero de 2018); registrado porque el texto de 2015 sin corregir sigue
  siendo el que más se descarga y se cita.

---

## Ainslie, Principles of Sonar Performance Modelling (2010), Ec. (9.57)

*Libro, no una norma.*

- **Ubicación:** sección 9.1.1.2.4 (p. 457 impresa), el alcance de transición
  entre los regímenes de decapado de modos y de modo único del modelo de
  flujo de Weston.
- **El impreso:** $r_\text{MS} \approx k^2 H_e^3/(9\eta)$, donde $H$ es la
  profundidad del agua, $H_e$ la profundidad efectiva de Weston de la
  Ec. (9.55), $k = \omega/c_w$ y $\eta$ el gradiente de pérdida por
  reflexión.
- **El problema:** la frase inmediatamente encima prescribe la deducción,
  «estimated by equating θ_n and θ_eff with n = 3/2». Los dos ángulos están a
  cuatro páginas impresas uno de otro, no en la misma página como declaraba
  una revisión anterior de esta entrada:
  - Ec. (9.47), $\theta_\text{eff} = (\pi H/(4\eta r))^{1/2}$, **p. 453
    impresa**, con la **profundidad de agua verdadera $H$** (procede de la
    integral multitrayecto Ec. (9.46), cuyo prefactor $1/(rH)$ es el área de
    cilindro $A_\text{CS} = 2\pi r H$ de la Ec. (9.44), así que $H$ es la
    profundidad que cuenta rebotes de fondo);
  - Ec. (9.56), $\theta_n \approx n\pi/(k H_e)$, **p. 457 impresa**, con la
    **profundidad efectiva $H_e$** (los ángulos de modo los fija la frontera
    aparente de presión nula).

  Igualarlos a $n = 3/2$ da $\pi H/(4\eta r) = 9\pi^2/(4k^2H_e^2)$, es decir
  **$r_\text{MS} = k^2H_e^2H/(9\pi\eta)$**. La forma impresa es mayor en
  $\pi H_e/H$. El factor $\pi$ es incondicional: sobrevive incluso si se
  sustituye $H_e$ por $H$ en la Ec. (9.47), que es presumiblemente como
  surgió el $H_e^3$ impreso, y esa lectura daría $k^2H_e^3/(9\pi\eta)$,
  todavía $\pi$ por debajo del impreso. El residuo $H_e/H$ es la propia
  sustitución de profundidad, y tiende a 1 en alta frecuencia. La otra
  transición de la misma sección, la Ec. (9.50)
  $r_\text{CS} = \pi H/(4\eta\psi_c^2)$, sigue su propia deducción
  exactamente (es donde se cruzan la Ec. (9.42) y la Ec. (9.49)), así que el
  defecto queda confinado a la Ec. (9.57).
- **Evidencia:** la re-deducción simbólica de arriba, comprobada
  numéricamente para $H = 50\ \text{m}$, $f = 250\ \text{Hz}$,
  $c_w = 1500\ \text{m/s}$ sobre el lecho de arena de la Tabla 9.1
  ($\eta = 0.28\ \text{Np/rad}$, $\psi_c = 33.56^\circ$,
  $H_e = 53.63\ \text{m}$, $k = 1.047\ \text{m}^{-1}$):

  | | $r_\text{MS}$ | $\theta_\text{eff}$ allí (Ec. 9.47) |
  |---|---|---|
  | deducción, $k^2H_e^2H/(9\pi\eta)$ | 19.9 km | 4.808° |
  | Ec. (9.57) impresa, $k^2H_e^3/(9\eta)$ | 67.1 km | 2.619° |

  La razón $67.1/19.9$ es $\pi H_e/H = 3.3695$ a todos los dígitos
  arrastrados. La columna de ángulos es una comprobación independiente que no
  depende de cómo se lea la deducción: los dos primeros ángulos de modo de la
  Ec. (9.56) son $\theta_1 = 3.205^\circ$ y $\theta_2 = 6.410^\circ$, así que
  $\theta_{3/2} = 4.808^\circ$. En el alcance deducido el ángulo efectivo es
  exactamente $\theta_{3/2}$, a mitad de camino entre los dos primeros modos,
  que es lo que el texto pide. En el alcance impreso ha caído a 2.619°, **por
  debajo del propio $\theta_1$**: el segundo modo se habría decapado mucho
  antes, así que ese alcance no puede ser donde empieza el régimen de modo
  único. Ambas fórmulas impresas están confirmadas en la página 483 del PDF
  (p. 453 impresa) y la página 487 del PDF (p. 457 impresa) de Ainslie,
  Principles of Sonar Performance Modelling (2010).
- **Comportamiento de la biblioteca:** `weston_regime_boundaries` en
  [`propagation/weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/propagation/weston_regimes.py)
  implementa el $k^2H_e^2H/(9\pi\eta)$ consistente con la deducción, que es
  además lo que mantiene $\theta_\text{eff}$ definido con $H$ en todos los
  puntos donde el módulo evalúa la Ec. (9.47). La regla de igualación está
  fijada por
  `test_mode_stripping_boundary_equates_theta_eff_with_mode_3_over_2`, que
  reconstruye ambos ángulos desde las ecuaciones impresas y no desde la
  implementación, y la definición compartida de $\theta_\text{eff}$ por
  `test_composite_loss_and_the_boundary_use_the_same_effective_angle` (ambos
  en
  [`tests/underwater/propagation/test_weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/tests/underwater/propagation/test_weston_regimes.py)).
- **Estado:** sin notificar (libro, no una norma).

---

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

---

## Southall et al. (2019), Aquatic Mammals 45(2), Tabla 7 (SPL de pico impulsivo)

*Artículo de revista con revisión por pares, no una norma.*

- **Ubicación:** Tabla 7 (p. 156 impresa), los criterios de umbral TTS y PTS
  para ruido impulsivo; las dos filas de carnívoros en el aire PCA y OCA.
- **El impreso:** PCA SPL de pico TTS 138 y SPL de pico PTS 144; OCA SPL de
  pico TTS 161 y SPL de pico PTS 167
  $\text{dB re } 20\ \mu\text{Pa}$.
- **El problema:** los cuatro son errores tipográficos. Las propias erratas
  de los autores (*Aquatic Mammals* 45(5), 569-572,
  DOI 10.1578/AM.45.5.2019.569) nombran los cuatro en la p. 569 impresa,
  «There are four typographical errors in Table 7 on page 156», y reimprimen
  la tabla corregida en la p. 570 impresa: PCA 155 y 161, OCA 170 y 176. Las
  mismas erratas corrigen además la columna encabezada «B» de la Tabla 5 al
  parámetro b de la Ec. (2), que igualmente llaman error tipográfico.
- **Evidencia:** las erratas mismas, que nombran cada valor erróneo y su
  sustituto, corroboradas por la propia regla de extrapolación del artículo.
  Nótese primero lo que *no* discrimina. La regla de pico PTS = pico TTS +
  6 dB de la p. 155 impresa la satisface también el par impreso
  ($144 - 138 = 6$, igual que $161 - 155 = 6$), así que no dice nada sobre
  qué par es el correcto. Tampoco la duplicación visible en las filas
  impresas, donde la entrada de SPL de pico TTS es igual a la entrada **SEL**
  de umbral PTS de la misma fila (PCA 123 / 138 / 138 / 144 y OCA 146 / 161 /
  161 / 167, leyendo SEL TTS, pico TTS, SEL PTS, pico PTS): para estas dos
  filas en el aire esa igualdad la fuerzan dos reglas que el artículo declara
  en la p. 155 impresa, ambas sumando 15 dB al mismo SEL TTS base, así que se
  cumpliría fueran cuales fueran los valores SEL. Una revisión anterior de
  esta entrada leía esa igualdad como la firma de un corrimiento de columna;
  es en cambio la tabla impresa siendo internamente consistente con el propio
  método en el aire del artículo, que es lo que hace de las erratas lo único
  que zanja el asunto.
  - **El valor.** Los números corregidos están cerca de lo que produce la
    regla de extrapolación del artículo, con la salvedad de que la regla no
    se declara para estas filas. La p. 155 impresa fija el umbral TTS de SPL
    de pico impulsivo de un grupo sin datos directos en el umbral de audición
    a la frecuencia de mejor sensibilidad $f_0$ más 159 dB, y restringe esa
    regla explícitamente a los grupos en el agua: «For other species groups
    **in water** (LF, SI, PCW, and OCW), 159 dB was added to the value of the
    hearing threshold at f₀». La desarrolla para PCW: «Peak SPL TTS onset was
    estimated as 212 dB re 1 µPa (53 dB at f₀ + 159 dB)». Evaluar el
    audiograma de grupo de la Tabla 2 en el $f_0$ de la Tabla 4 reproduce las
    tres filas en el agua que las erratas no tocan (SI 219.6 contra un 220
    publicado; PCW 212.5 contra 212; OCW 226.1 contra 226), lo que valida la
    regla donde el artículo la aplica. Extenderla a las dos filas de
    carnívoros en el aire, cosa que el artículo no hace, da PCA
    $-4.6\ \text{dB re } 20\ \mu\text{Pa}$ a 2.3 kHz y OCA
    $11.4\ \text{dB re } 20\ \mu\text{Pa}$ a 10 kHz, de donde **154.4** y
    **170.4**. Esos reproducen los corregidos 155 y 170 con margen de 0.6 dB
    y quedan a 16 dB y 9 dB de los impresos 138 y 161, que es lo que los hace
    corroborantes y no confirmatorios; nótese que 154.4 redondea a 154, no a
    155, y una revisión anterior de esta entrada afirmaba que redondeaba al
    valor corregido.
  - **Una segunda inconsistencia, sin reparar.** La p. 155 impresa declara
    que para los carnívoros en el aire específicamente «a nominal 15 dB
    offset is used ... between the SEL-based TTS threshold and the peak
    SPL-based threshold», lo que reproduce los *impresos* 138 y 161 desde la
    columna SEL. Esa frase, no la regla de +159 dB, es la que el propio
    método del artículo aplica a PCA y OCA. Las erratas resuelven el
    conflicto a favor de valores consistentes con la regla de +159 dB, así
    que dejan sin efecto la frase además de la tabla; la frase queda en pie
    en el artículo.
  Verificado en la página 31 del PDF (p. 155 impresa) y la página 32 del PDF
  (p. 156 impresa) de Southall et al. (2019), Aquatic Mammals 45(2), que
  llevan la restricción «in water (LF, SI, PCW, and OCW)», el desplazamiento
  de 15 dB en el aire en el mismo párrafo, las dos formulaciones de la regla
  de +6 dB, y la Tabla 7 del artículo con la fila PCA 123 / 138 / 138 / 144 y
  la fila OCA 146 / 161 / 161 / 167. Las erratas son una publicación propia,
  *Aquatic Mammals* 45(5), 569-572, encuadernada al final de la copia que
  distribuyen los autores: verificadas allí en la página 109 del PDF (p. 569
  impresa), que nombra los cuatro valores y sus sustitutos, y la página 110
  del PDF (p. 570 impresa), que reimprime la Tabla 7 con PCA 123 / 155 / 138
  / 161 y OCA 146 / 170 / 161 / 176.
- **Comportamiento de la biblioteca:** los valores corregidos por las erratas
  son los implementados en
  [`bioacoustics/weighting.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/bioacoustics/weighting.py),
  fijados por `test_southall_table_7_errata_values_are_implemented`, con la
  propia regla de +159 dB comprobada contra el audiograma en
  `test_southall_impulsive_peak_spl_is_threshold_at_f0_plus_159_db` para los
  grupos en el agua a los que el artículo la restringe y, por separado y con
  la extrapolación etiquetada como tal, para PCA y OCA.
- **Estado:** notificado por los propios autores (erratas publicadas en
  2019).

## Directiva (UE) 2015/996, Anexo II 2.3.2 (conversión de rugosidad en km/h)

- **Ubicación:** el párrafo «Definition» de *Wheel and rail roughness*
  (DO L 168, 1.7.2015, p. 19) y el primer párrafo tras la fórmula (2.3.11)
  (p. 21).
- **El impreso:** «it shall be converted to a frequency spectrum f = v/λ,
  where f is the centre band frequency of a given 1/3 octave band in Hz, λ is
  the wavelength in m, and **v is the train speed in km/h**», y, para el
  ruido de impacto, «using the relation λ = v/f, where f is the 1/3 octave
  band centre frequency in Hz and **v is the s-th vehicle speed of the t-th
  vehicle type in km/h**».
- **El problema:** dimensionalmente imposible. Una frecuencia en hercios es
  una velocidad en metros por segundo dividida por una longitud de onda en
  metros; leer la velocidad en km/h en $f = v/\lambda$ multiplica todas las
  frecuencias por 3,6, situando el espectro de rugosidad entero un factor 3,6
  demasiado alto en frecuencia, que es más de una octava y media.
- **Evidencia:** verificado en la página 19 del PDF (p. L 168/19 impresa) y
  la página 21 del PDF (p. L 168/21 impresa) de la Directiva (UE) 2015/996.
  La corrección de errores del DO L 5, 10.1.2018, p. 35 sustituye «km/h» por
  «m/s» en ambos lugares. La ecuación de flujo (2.3.2) sí toma de verdad su
  velocidad en km/h, que es lo que hace plausible la errata.
- **Comportamiento de la biblioteca:** `roughness_to_frequency` convierte la
  velocidad a m/s antes de dividir, como está corregido, y su docstring lo
  dice. La implementación de referencia que la Comisión publicó con el módulo
  fuente hace lo mismo, y los 123 casos de libro de cálculo commiteados no se
  reproducirían de otro modo.
- **Estado:** sin notificar (corregido por el organismo emisor en 2018).

## Directiva (UE) 2015/996, Appendix G, Tabla G-1, segunda tabla (símbolo equivocado)

- **Ubicación:** Tabla G-1, «Coefficients Lr,TR,i and Lr,VEH,i for rail and
  wheel roughness», segunda tabla (DO L 168, 1.7.2015, pp. 130-131).
- **El impreso:** la segunda tabla está encabezada **$L_{r,VEH,i}$**, el
  mismo símbolo que la primera.
- **El problema:** sus dos columnas son «EN ISO 3095:2013 (Well maintained
  and very smooth)» y «Average network (Normally maintained smooth)», que son
  las clases de rugosidad de carril E y M del dígito 2 del descriptor de vía
  de la Tabla [2.3.b]. La tabla es la rugosidad de **carril** $L_{r,TR,i}$,
  la cantidad que el propio título de la tabla anuncia y que de otro modo
  falta en el Appendix G.
- **Evidencia:** verificado en la página 130 del PDF (p. L 168/130 impresa)
  de la Directiva (UE) 2015/996:2015, la página que lleva el encabezado de la
  segunda tabla. La corrección de errores del DO L 5, 10.1.2018 la retitula
  $L_{r,TR,i}$, y la Directiva Delegada (UE) 2021/1226 de la Comisión, punto
  (20)(a) del Anexo, la reimprime bajo ese símbolo cuando la sustituye,
  verificado en la página 35 del PDF (p. L 269/99 impresa) de esa Directiva.
- **Comportamiento de la biblioteca:** `rail_roughness` devuelve la segunda
  tabla de G-1 como la rugosidad de carril de (2.3.7) y `wheel_roughness`
  devuelve la primera como la rugosidad de rueda, que es la única asignación
  bajo la cual las clases de la Tabla [2.3.b] pueden alcanzarse siquiera.
- **Estado:** sin notificar (corregido por el organismo emisor en 2018).

## Directiva (UE) 2015/996, Appendix G, Tabla G-5, fila de 6 350 Hz (muesca de 50 dB)

- **Ubicación:** Tabla G-5, «Coefficients LW,0,idling for traction noise», la
  fila de 6 350 Hz del par «Diesel locomotive (c. 2 200 kW)» (DO L 168,
  1.7.2015, p. 138).
- **El impreso:** Source A **31,4** dB y Source B **30,7** dB.
- **El problema:** ambos están unos 50 dB por debajo de sus propios vecinos
  en la misma columna: 90,5 / 89,5 dB a 5 000 Hz y 81,2 / 80,6 dB a
  8 000 Hz. Ninguna fuente de tracción física tiene una muesca de 50 dB de un
  tercio de octava de ancho, y ninguna otra columna de la tabla tiene nada
  comparable. Se perdió el dígito inicial 8.
- **Evidencia:** verificado en la página 138 del PDF (p. L 168/138 impresa)
  de la Directiva (UE) 2015/996:2015, que lleva las filas de 5 000, 6 350 y
  8 000 Hz y el encabezado de columna «Diesel locomotive (c. 2 200 kW)». La
  Directiva Delegada (UE) 2021/1226 de la Comisión, punto (20)(f) del Anexo,
  verificado en la página 39 del PDF (p. L 269/103 impresa) de esa Directiva,
  sustituye la 4.ª columna, 25.ª fila por «81,4» y la 5.ª columna, 25.ª fila
  por «80,7», restaurando la caída monótona. Los mismos dos valores aparecen
  como 31,41 y 30,71 en el fichero de catálogo IMAGINE que la Comisión
  distribuye con su módulo fuente de referencia, así que el error es anterior
  a la Directiva.
- **Comportamiento de la biblioteca:** publica los corregidos 81,4 / 80,7 y
  los fija, junto con la afirmación de que ningún valor dista más de 10 dB de
  cualquiera de sus vecinos, en
  `test_table_g5_carries_the_2021_correction_at_6300_hz`.
- **Estado:** sin notificar (corregido por el organismo emisor en 2021).

## Directiva (UE) 2015/996, Appendix G, etiquetas de bandas y longitudes de onda

- **Ubicación:** la columna de frecuencias de las Tablas G-3, G-5 y G-6 y la
  columna de longitudes de onda de la Tabla G-1 (DO L 168, 1.7.2015,
  pp. 129-140).
- **El impreso:** los centros de tercio de octava están etiquetados
  **316 Hz**, **3 160 Hz** y **6 350 Hz**, y las longitudes de onda
  **120 mm**, **12 mm**, **3,2 mm** y **1,2 mm**.
- **El problema:** ninguna de las dos series es la preferente. Los centros
  nominales de tercio de octava de IEC 61260-1 son 315, 3 150 y 6 300 Hz, y
  los números preferentes R10 en torno a esas longitudes de onda son 125,
  12,5, 3,15 y 1,25 mm. Los propios ficheros de catálogo de la Comisión,
  distribuidos con el módulo fuente de referencia, usan la serie de
  longitudes de onda preferente en todo su recorrido.
- **Evidencia:** verificado en las páginas 129, 130, 131, 133, 134, 135, 137
  y 138 del PDF (pp. L 168/129 a L 168/138 impresas) de la Directiva (UE)
  2015/996:2015, que llevan todas las apariciones de las cuatro longitudes de
  onda y de las tres etiquetas de banda. La Directiva Delegada (UE) 2021/1226
  de la Comisión, punto (20)(c) del Anexo, sustituye la sección
  $L_{H,TR,i}$ de la Tabla G-3 de raíz y los puntos (20)(d), (f) y (g)
  sustituyen las tres etiquetas de frecuencia en las secciones restantes y en
  las Tablas G-5 y G-6; las tablas que sustituye de raíz llevan las
  longitudes de onda preferentes. Pero el punto (20)(a) sustituye solo «the
  second table» de la Tabla G-1, así que las etiquetas de longitud de onda
  120, 12, 3,2 y 1,2 mm siguen en pie en la **primera** tabla de G-1, la
  rugosidad de rueda $L_{r,VEH,i}$, que es la única tabla que las conserva.
- **Comportamiento de la biblioteca:** la rejilla de frecuencias es la de
  IEC 61260-1 en todo su recorrido. Las rejillas de longitudes de onda se
  mantienen como están impresas, una por tabla, y cada espectro de rugosidad
  se remuestrea sobre su propia rejilla en lugar de forzarse a una común, que
  es para lo que están `_WAVELENGTHS_WHEEL` y `_WAVELENGTHS_STANDARD`; la
  diferencia entre las dos está fijada por
  `test_wheel_roughness_keeps_the_non_standard_wavelength_grid`.
- **Estado:** sin notificar (etiquetas de frecuencia corregidas por el
  organismo emisor en 2021; las etiquetas de longitud de onda de la rugosidad
  de rueda siguen en pie).

## Directiva (UE) 2015/996, Anexo II 2.3.2, chirrido en curva (extremos sin asignar)

- **Ubicación:** el párrafo *Squeal* (DO L 168, 1.7.2015, p. 21).
- **El impreso:** «The emission level to be used is determined for curves
  with radius below **or equal to** 500 m and for sharper curves and
  branch-outs of points with radii below 300 m», y después «squeal noise
  shall be considered by adding 8 dB for **R < 300 m** and 5 dB for
  **300 m < R < 500 m**».
- **El problema:** los dos intervalos abiertos dejan $R = 300\ \text{m}$ y
  $R = 500\ \text{m}$ sin exceso alguno, y $R = 500\ \text{m}$ está
  explícitamente dentro del alcance que el mismo párrafo acaba de fijar. Una
  curva de 500 m se cae por tanto de una regla escrita para incluirla.
- **Evidencia:** verificado en la página 21 del PDF (p. L 168/21 impresa) de
  la Directiva (UE) 2015/996:2015, en la que las dos desigualdades de la
  frase de la regla son estrictas mientras que la frase de alcance encima de
  ellas lee «below or equal to 500 m». La Directiva Delegada (UE) 2021/1226
  de la Comisión, punto (4)(b) del Anexo, verificado en la página 4 del PDF
  (p. L 269/68 impresa) de esa Directiva, sustituye el párrafo por una tabla
  cuyos intervalos son cerrados, «R <= 300 m» y «300 m < R <= 500 m».
- **Comportamiento de la biblioteca:** `curve_squeal_excess` implementa la
  tabla de 2021, así que $R = 300\ \text{m}$ devuelve 8 dB y
  $R = 500\ \text{m}$ devuelve 5 dB; los límites están fijados en
  `test_curve_squeal_rule_of_2021`.
- **Estado:** sin notificar (corregido por el organismo emisor en 2021).

---

## Allard & Atalla, Propagation of Sound in Porous Media 2e (2009), Ec. (6.85)

*Libro, no una norma.*

- **Ubicación:** sección 6.5.2 (p. 123 impresa), la segunda forma de la razón
  de velocidades de la onda de cizalla $\mu_3$.
- **El impreso:**
  $\mu_3 = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{22})$, ofrecida
  como alternativa a la Ec. (6.84), $\mu_3 = -\rho_{12}/\rho_{22}$.
- **El problema:** las dos formas impresas no son iguales. Sustituir el
  número de onda de cizalla de la Ec. (6.83),
  $\delta_3^2 = (\omega^2/N)(\rho_{11}\rho_{22} - \rho_{12}^2)/\rho_{22}$, en
  la Ec. (6.85) impresa da $-\rho_{12}^2/\rho_{22}^2$, que es la Ec. (6.84)
  multiplicada por el factor espurio $\rho_{12}/\rho_{22}$. El denominador
  debería leer $\omega^2\rho_{12}$.
- **Evidencia:** la propia deducción del libro. La Ec. (6.80), p. 122
  impresa, es
  $-\omega^2\rho_{11}\psi_s - \omega^2\rho_{12}\psi_f = N\nabla^2\psi_s = -N\delta_3^2\psi_s$,
  así que $(N\delta_3^2 - \omega^2\rho_{11})\psi_s = \omega^2\rho_{12}\psi_f$
  y por tanto
  $\mu_3 = \psi_f/\psi_s = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{12})$.
  Con esa lectura las dos formas concuerdan idénticamente allí donde
  $\rho_{12}$ no es cero; a $\rho_{12} = 0$ el cociente corregido es $0/0$
  mientras que la Ec. (6.84) sigue definida y da
  $\mu_3 = -\rho_{12}/\rho_{22} = 0$, que es el valor a usar allí. La forma
  impresa difiere en cambio de la Ec. (6.84) en el factor
  $\rho_{12}/\rho_{22}$, así que coincide con ella solo donde esa razón es
  exactamente 0 o exactamente 1. Con
  $\rho_{12}/\rho_{22} = \rho_0/(\phi\rho_\text{eq}) - 1$ esos dos casos
  piden $\rho_\text{eq} = \rho_0/\phi$ y $\rho_\text{eq} = \rho_0/(2\phi)$,
  ambos reales; la densidad efectiva de un medio poroso con pérdidas es
  compleja, así que ninguno se cumple jamás. Verificado en la página 132 del
  PDF (p. 123 impresa) de Allard & Atalla, Propagation of Sound in Porous
  Media 2e:2009, que lleva ambas formas impresas, y en la página opuesta para
  la Ec. (6.80).
- **Comportamiento de la biblioteca:** `biot_waves` implementa la Ec. (6.84)
  tal como está impresa, y
  `test_shear_velocity_ratio_matches_the_corrected_second_printed_form` la
  comprueba contra la Ec. (6.85) corregida sobre cuatro décadas de
  frecuencia, y afirma además que la forma exactamente como está impresa
  discrepa.
- **Estado:** sin notificar.

---

## Allard & Atalla 2e (2009), Ec. (11.48) y Tabla 11.1 (capa poroelástica)

*Libro, no una norma.*

- **Ubicación:** sección 11.3.3 (pp. 251-252 impresas), la tensión normal del
  fluido $\sigma_{33}^f$ de una capa poroelástica y la matriz $[\Gamma]$ que
  alimenta.
- **El impreso:** la Ec. (11.48) lee

  $$
  \sigma_{33}^f = \sum_i (Q + R\mu_i)(k_t^2 + k_{i3}^2)
  \left\{ -(A_i - A'_i)\cos(k_{i3}x_3) + j(A_i - A'_i)\sin(k_{33}x_3) \right\}
  $$

  y la Tabla 11.1 escribe $k_{i3}$ en las dos columnas que llevan $\mu_1$,
  $D_1$ y $E_1$.
- **El problema:** dos erratas independientes en la misma ecuación, más un
  desliz de subíndice en la tabla.
  - Falta el coeficiente de la amplitud *simétrica* $(A_i + A'_i)$: la
    Ec. (11.48) adjunta ambos términos a $(A_i - A'_i)$, lo que dejaría la
    primera y la tercera columna de $[\Gamma]$ sin entrada alguna de
    $\sigma_{33}^f$, contradiciendo la Tabla 11.1, cuya fila 6 imprime
    $-E_1 \cos(k_{13}x_3)$ y $-E_2 \cos(k_{23}x_3)$ exactamente en esas
    columnas. El primer término es $-(A_i + A'_i)\cos(k_{i3} x_3)$.
  - El seno lleva $k_{33}$, la componente del número de onda de *cizalla*,
    dentro de una suma sobre las dos ondas de compresión $i = 1, 2$. Debe ser
    $k_{i3}$. La Tabla 11.1 da de nuevo la lectura pretendida: su fila 6
    tiene $j E_1 \sin(k_{13}x_3)$ y $j E_2 \sin(k_{23}x_3)$, y cero en ambas
    columnas de cizalla, porque una onda de cizalla no produce dilatación y
    por tanto tampoco $\sigma_{33}^f$.
  - La Tabla 11.1 imprime el subíndice corredero $k_{i3}$ en sus dos primeras
    columnas, que pertenecen a la primera onda de compresión sola: los
    $\mu_1$, $D_1$ y $E_1$ de las mismas columnas hacen de $k_{13}$ la única
    lectura consistente.
- **Evidencia:** las dos lecturas de arriba las fuerza la Tabla 11.1, que la
  misma página declara ser la tabulación de las Ecs. (11.37), (11.38) y
  (11.46)-(11.48). Son también lo que da la relación tensión-deformación
  Ec. (11.41),
  $\sigma_{33}^f = R\,\mathrm{div}\,u_f + Q\,\mathrm{div}\,u_s$, cuando los
  potenciales de desplazamiento de las Ecs. (11.22)-(11.25) se derivan
  directamente. Verificado en la página 257 del PDF (p. 251 impresa) y la
  página 258 del PDF (p. 252 impresa) de Allard & Atalla, Propagation of
  Sound in Porous Media 2e:2009, que llevan la Ec. (11.48) y las dos columnas
  de la Tabla 11.1 tal como están impresas.
- **Comportamiento de la biblioteca:** la $[\Gamma]$ de la Tabla 11.1 está
  implementada con las lecturas corregidas, y
  `test_gamma_matches_the_field_rebuilt_from_the_potentials` comprueba sus
  treinta y seis entradas a tres frecuencias, tres profundidades y tres
  ángulos de incidencia contra el campo reconstruido desde las
  Ecs. (11.22)-(11.28) sin pasar por la tabla.
- **Estado:** sin notificar.

---

## Allard & Atalla 2e (2009), sección 6.6.3 (espesor de la segunda muestra)

*Libro, no una norma.*

- **Ubicación:** sección 6.6.3, p. 129 impresa, las dos muestras de lana de
  vidrio cuyas impedancias de superficie medidas y predichas son las Figuras
  6.10 y 6.11.
- **El impreso:** la primera frase dice que las impedancias se muestran «for
  l = 10 cm and l = 5.4 cm»; dos frases después el pico de la segunda muestra
  se sitúa a «860 Hz for l = 5.6 cm», y el pie de la Figura 6.11 dice «l =
  5.6 cm».
- **El problema:** los dos espesores no pueden estar bien a la vez.
- **Evidencia:** textual, y solo textual. Dos declaraciones impresas llevan
  5.6 cm, la frase del pico de 860 Hz y el pie independiente de la Figura
  6.11, contra una que lleva 5.4 cm; un solo desliz en la frase inicial es la
  explicación más corta que el mismo desliz cometido dos veces. Los números
  **no** lo zanjan, y esta entrada no pretende que lo hagan. El libro no da
  regla de localización de picos, y la respuesta sigue a la regla elegida:
  - Tomando el pico como el máximo de $\text{Im}(Z_s)$, la Ec. (6.107) sobre
    la lana de vidrio de la Tabla 6.1, completamente especificada, da
    863.5 Hz para 5.6 cm (+0.4 % contra los 860 impresos) y 896.2 Hz para
    5.4 cm (+4.2 %), lo que favorece 5.6 cm. Pero la misma regla sitúa la
    muestra indiscutida de 10 cm a 480.0 Hz contra sus 470 impresos, un sesgo
    de +2.1 % del mismo tamaño que el efecto que se resuelve.
  - Tomando el pico como el máximo de $|Z_s - Z_{s,\text{rigid}}|$, que es la
    desviación que el mismo párrafo describe («close to each other, except
    around the peaks which are not predicted by the one-wave model»), la
    muestra de 10 cm aterriza a 469.2 Hz (-0.2 %) y **ambas** frecuencias
    impresas salen entonces del par (10 cm, 5.4 cm): 861.2 Hz para 5.4 cm
    (+0.1 %) contra 831.0 Hz para 5.6 cm (-3.4 %). Esa regla favorece 5.4 cm.
  - Escalar el pico de 10 cm tampoco ayuda, y se inclina al lado contrario de
    la conclusión: $470 \times (10/5.4) = 870\ \text{Hz}$ está a 10 Hz de los
    860 publicados, $470 \times (10/5.6) = 839\ \text{Hz}$ a 21 Hz.
  - La concordancia de «860 Hz» con «5.6 cm» es en todo caso parcialmente
    circular, ya que ambos están en la misma cláusula: contrasta esa frase
    contra sí misma, no cuál de las dos frases es la errata.
  Verificado en la página 138 del PDF (p. 129 impresa) de Allard & Atalla,
  Propagation of Sound in Porous Media 2e:2009, en la que el 5.4 cm solitario
  y el 5.6 cm de la cláusula de 860 Hz están en la misma página, y en la
  página 139 del PDF (p. 130 impresa) de la misma edición para el pie de la
  Figura 6.11, la segunda frase que lleva 5.6 cm.
- **Comportamiento de la biblioteca:** registrado, sin efecto en la
  implementación.
  `test_impedance_peak_of_the_thin_layer_resolves_the_printed_thickness`
  fija el pico de 5.6 cm contra los 860 Hz publicados bajo la regla de
  $\text{Im}(Z_s)$ y comprueba que la lectura de 5.4 cm es la peor de las dos
  bajo esa regla.
- **Estado:** sin notificar, y la más débil de las cuatro entradas de aquí:
  la conclusión descansa en la lectura dos-contra-uno de la página impresa,
  no en un cálculo.

---

## Allard & Atalla 2e (2009), sección 6.5.4 (la razón de velocidades de la onda del esqueleto)

*Libro, no una norma.*

- **Ubicación:** sección 6.5.4, p. 125 impresa, la única frase del libro que
  cita valores calculados de $\mu_b$ para la lana de vidrio de la Tabla 6.1.
- **El impreso:** «The ratio modulus $|\mu_b|$ of the velocities of the frame
  and the air for the frame-borne wave decreases from 1.0 at 50 Hz to 0.82 at
  1500 Hz.»
- **El problema:** los dos valores citados son la *parte real* de $\mu_b$, no
  su módulo. $\mu_b$ es complejo, y la frase nombra el módulo
  explícitamente.
- **Evidencia:** sobre el material de la Tabla 6.1, completamente
  especificado, el modelo da $\mu_b(1500\ \text{Hz}) = 0.811 + 0.473j$. Su
  parte real es **0.811**, a 1.1 % del 0.82 impreso; su módulo es **0.939**,
  a 14.5 %. Leída como la parte real, la frase acierta en ambos extremos y
  describe un descenso monótono: $\text{Re}(\mu_b)$ es 1.002 a 50 Hz y pasa
  por 0.82 a 1467 Hz, a 2.2 % de los 1500 Hz impresos. Leída como el módulo
  no acierta en ninguno: $|\mu_b|$ es 1.002 a 50 Hz pero *sube* a 1.008 hacia
  400 Hz antes de darse la vuelta, y solo alcanza 0.82 a 2634 Hz, un 76 % por
  encima de la frecuencia impresa. Ninguna lectura admisible de las entradas
  impresas cierra esa brecha. Con el factor de pérdida a 0 o a 0.2, la
  longitud viscosa a la mitad o al doble, $\Lambda' = 2\Lambda$ en lugar del
  $1.1 \cdot 10^{-4}\ \text{m}$ impreso, la resistividad a la mitad o al
  doble, la tortuosidad a 1 o el coeficiente de Poisson a 0.3,
  $|\mu_b(1500)|$ se mueve solo entre 0.874 y 1.073. La más cercana de las
  ocho, 0.874 a factor de pérdida cero, sigue a 6.6 % del 0.82 impreso, y
  pierde por completo el cruce de ramas a 495 Hz de la misma sección; la
  única variante que conserva ese cruce ($\Lambda' = 2\Lambda$, 495.2 Hz)
  deja $|\mu_b|$ en 0.937. Leer la frase como $\text{Re}(\mu_b)$ no necesita
  variante alguna. Verificado en la página 134 del PDF (p. 125 impresa) de
  Allard & Atalla, Propagation of Sound in Porous Media 2e:2009, que lleva la
  frase y su 0.82.
- **Comportamiento de la biblioteca:** `biot_waves` calcula $\mu_b$ desde la
  Ec. (6.71) tal como está impresa. La fila de conformidad y
  `test_frame_borne_velocity_ratio_matches_the_two_published_values` están
  escritas contra $\text{Re}(\mu_b)$, y lo dicen.
- **Estado:** sin notificar.

---

## Allard & Atalla 2e (2009), Tabla 11.7 (la figura que nombra su pie)

*Libro, no una norma.*

- **Ubicación:** Tabla 11.7, página 280 del PDF, p. 274 impresa, la tabla de
  parámetros de la moqueta, la pantalla y la capa fibrosa de la sección
  11.7.2.
- **El impreso:** el pie dice «The parameters used to predict the surface
  impedance of the material represented in Figure 11.6».
- **El problema:** la Figura 11.6 está en la p. 266 impresa y es la espuma
  plástica bajo una lámina de lana de vidrio, cuyos parámetros son la Tabla
  11.3. La estructura que tabula la Tabla 11.7, una moqueta en dos capas sobre
  una pantalla impermeable sobre una capa fibrosa, es la Figura 11.16,
  impresa en la misma página que la tabla.
- **Evidencia:** el texto junto a la Figura 11.16 dice que los parámetros del
  material están en la Tabla 11.7, y los cuatro nombres de fila de la tabla
  son las cuatro capas que etiqueta la Figura 11.16. Verificado en la página
  280 del PDF (p. 274 impresa) y en la página 272 del PDF (p. 266 impresa) de
  Allard & Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** las tres filas porosas se transcriben
  tal como están impresas y el `about` del fichero de datos nombra la Figura
  11.16 como la estructura, citando la redacción del pie.
- **Estado:** sin notificar.

---

## Allard & Atalla 2e (2009), Tabla 11.8 (el espesor de la lana de vidrio)

*Libro, no una norma.*

- **Ubicación:** Tabla 11.8, página 281 del PDF, p. 275 impresa, la lana de
  vidrio pegada a una placa de aluminio del ejemplo de transmisión a
  incidencia normal de la sección 11.7.3.
- **El impreso:** la tabla da a la lana de vidrio un espesor de 3,8 mm; el
  texto de la sección 11.7.3, en el folio de al lado, dice «A layer of the
  glass wool studied in Section 6.5.4, of thickness 5 cm, is bonded on to a
  plate of aluminium, of thickness 1 mm».
- **El problema:** los dos espesores difieren en más de un orden de magnitud y
  no pueden describir los dos la capa de la Figura 11.18.
- **Evidencia:** la placa sí concuerda entre ambos, 1 mm en los dos, que es lo
  que sitúa la discrepancia en la celda de la lana de vidrio y no en una
  columna leída fuera de orden. Verificado en la página 281 del PDF (p. 275
  impresa) para la tabla y en la página 280 del PDF (p. 274 impresa) para la
  frase, en Allard & Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** la fila lleva los 3,8 mm impresos y su
  `note` registra la frase. Nada calcula con el espesor: el fluido equivalente
  de esta probeta no lo usa.
- **Estado:** sin notificar.

---

## Allard & Atalla 2e (2009), Tabla 11.9 (el espesor de la placa)

*Libro, no una norma.*

- **Ubicación:** Tabla 11.9, página 282 del PDF, p. 276 impresa, la espuma y
  la placa del ejemplo de transmisión en campo difuso de la sección 11.7.4.
- **El impreso:** la fila de la placa da un espesor de 1,6 mm; el texto de la
  sección 11.7.4, en el folio de al lado, dice «The material is a foam of
  thickness h = 2 . 54 cm bonded onto a 0.6 mm aluminium plate».
- **El problema:** 1,6 frente a 0,6 mm para la misma placa.
- **Evidencia:** la espuma sí concuerda entre ambos, los 25,4 mm de la tabla
  son los 2,54 cm de la frase, lo que deja la discrepancia sólo en la fila de
  la placa. Verificado en la página 282 del PDF (p. 276 impresa) para la tabla
  y en la página 281 del PDF (p. 275 impresa) para la frase, en Allard &
  Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** la placa no es un material poroso y no
  está en el catálogo; la `note` de la fila de la espuma registra la
  discrepancia para que quien reproduzca la figura sepa qué placa supone la
  curva.
- **Estado:** sin notificar.

---

## Allard & Atalla 2e (2009), Tabla 13.2 (el módulo de Young de la lana de roca)

*Libro, no una norma.*

- **Ubicación:** Tabla 13.2, página 341 del PDF, p. 337 impresa, la lana de
  roca de 5,75 cm con una perforación central del ejemplo de doble porosidad.
- **El impreso:** la columna encabezada E (Pa) lleva 4400 para un esqueleto de
  130 kg/m3.
- **El problema:** un módulo de esqueleto de 4,4 kPa a esa densidad da una
  velocidad de onda en el esqueleto de $\sqrt{4400/130} = 5,8$ m/s, así que la
  resonancia de cuarto de onda de una capa de 5,75 cm cae cerca de 25 Hz. El
  texto de la página siguiente dice que el modelo numérico captura «the
  skeleton resonance occurring around 1350 Hz», que el módulo impreso no puede
  producir: 1350 Hz pedirían unos 12,7 MPa, tres órdenes de magnitud por
  encima de la celda.
- **Evidencia:** aritmética sobre las dos celdas de la propia página contra la
  propia frase de la página. Nada en la página dice cuál debería ser el
  módulo, así que esta entrada informa de la incoherencia y no la repara.
  Verificado en la página 341 del PDF (p. 337 impresa) para la tabla y en la
  página 342 del PDF (p. 338 impresa) para la frase, en Allard & Atalla,
  Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** la fila lleva los 4400 Pa impresos y su
  `note` registra la resonancia que informa el texto. Ningún ejemplo de esta
  biblioteca calcula una resonancia de esqueleto a partir de él.
- **Estado:** sin notificar.

---

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix B, Ec. (B-41) (deceleración en descenso)

- **Ubicación:** Appendix B, sección B7.1.1, la deceleración $a$ definida
  bajo la Ec. (B-41), en la página que lleva la Ec. (B-40) y la Ec. (B-41).
- **El impreso:**
  $a = k^2 \left(\left(\left(\mathrm{Pt1(NextSeg)}_{TAS} - w\right)/\cos\gamma\right)^2 - \left(\left(\mathrm{Point1}_{TAS} - w\right)/\cos\gamma\right)^2\right) / \left(2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma\right)$,
  es decir, ambas velocidades respecto al suelo divididas por $\cos\gamma$
  sobre dos veces la longitud oblicua del segmento.
- **El problema:** la pendiente de descenso se cuenta dos veces. La
  deceleración media a lo largo de la trayectoria de vuelo es el cambio del
  cuadrado de la velocidad a lo largo del camino sobre dos veces la longitud
  del camino; la expresión impresa convierte las velocidades a valores a lo
  largo del camino *y* usa una longitud de camino que ya es la oblicua, así
  que sobreestima $|a|$ en $1/\cos^2\gamma$. La Ec. (B-21) de la 4.ª edición
  es autoconsistente, y el denominador no es lo que cambió: lee
  $2 \cdot \Delta s/\cos\gamma$ con $\Delta s$ «the ground distance covered»,
  que es la misma longitud oblicua que la 5.ª edición escribe como
  $2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma$.
  Lo que cambió es el numerador. La Ec. (B-22) de la 4.ª edición define las
  velocidades que divide como *velocidades respecto al suelo*,
  $V = V_C\cos\gamma/\sqrt{\sigma} - w$, es decir, la velocidad verdadera
  resuelta en el plano horizontal, así que dividir cada una por $\cos\gamma$
  restituye correctamente una velocidad a lo largo del camino. La 5.ª edición
  alimenta la Ec. (B-41) con la propia $\mathrm{TAS}$ de los puntos del
  perfil, que ya es a lo largo del camino, y conservó la división. Los
  propios resultados de referencia del Doc 29 lo deciden: de los doce puntos
  del caso 2D del Volumen 3 Parte 2, volado enteramente con ese tipo de paso,
  nueve se alcanzan por la deceleración. Las velocidades respecto al suelo
  simples reproducen el empuje tabulado en cada uno de los doce, peor
  desviación 0.047 lb, mientras que las velocidades divididas impresas se
  quedan cortas en los nueve, por 6.05, 5.47, 4.02, 3.81, 4.56, 4.45, 0.29,
  6.35 y 6.41 lb en orden de perfil: siempre bajas, y nunca dentro de las
  0.05 lb de precisión impresa del propio libro de cálculo. El término de
  resistencia junto a ella sí conserva el $\cos\gamma$ que imprime la misma
  ecuación, cosa que los mismos puntos confirman a las mismas 0.05 lb.
- **Evidencia:** reproducción de la hoja `D1-(Arrival_Results)` del Volumen 3
  Parte 2, caso 2D, bajo cada lectura. Verificado en la página 104 del PDF
  (p. B-31 impresa) de ECAC.CEAC Doc 29, 5.ª ed., Volumen 2: Technical guide,
  que lleva la Ec. (B-40), la Ec. (B-41) y la deceleración bajo ella, y en la
  página 90 del PDF (p. B-15 impresa) de ECAC.CEAC Doc 29, 4.ª edición,
  Volumen 2, que lleva la Ec. (B-21) y, justo debajo, la Ec. (B-22) que
  define sus $V_1$ y $V_2$ como velocidades respecto al suelo y decide así la
  lectura.
- **Comportamiento de la biblioteca:** `flight_performance` calcula la
  deceleración desde las velocidades respecto al suelo simples sobre la
  longitud oblicua, y el docstring del helper lleva la desviación y los
  números de arriba. `test_arrival_case_reproduces_every_profile_point` fija
  los 124 puntos de llegada, y la fila de conformidad *ECAC Doc 29 Appendix B
  approach thrust* fija el empuje de descenso del caso 2A.
- **Estado:** sin notificar.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix B, Ec. (B-18) (gradiente de pista)

- **Ubicación:** Appendix B, sección B6.1.1, la aceleración media $a$
  definida bajo la Ec. (B-18).
- **El impreso:** «$a$ is the average acceleration (ft/s$^2$) along the
  runway, equal to:
  $a = \left(V_C/\sqrt{\sigma}\right)^2/\left(2 \cdot s_{TOw}\right)$», con
  «$V_C$ is the Calibrated Airspeed (**kt**) at *Point2*» y $s_{TOw}$ en pies
  en la misma página.
- **El problema:** la expresión se declara en ft/s$^2$ y evalúa en kt$^2$/ft.
  El factor que falta es $k^2 = 1.68781^2 = 2.8487$, el cuadrado de la
  constante de nudos a pies por segundo que el Doc 29 fija en B2.2 y lleva
  explícitamente en la Ec. (B-24) y la Ec. (B-41), que construyen
  aceleraciones con el mismo tipo de expresión. No es cosmético: $a$ entra
  solo a través de $a/(a - g\,G_R)$, así que infravalorarla en 2.85
  sobrevalora la corrección de gradiente, y en una pendiente ascendente del
  1 % con $V_{CTO} = 162.65$ kt y $s_{TOw} = 4900$ ft los 7.69 ft/s$^2$
  dimensionalmente correctos dan un factor de 1.0437 contra el 1.1353 de la
  lectura literal: un 8.8 % de distancia de despegue. La 4.ª edición lleva la
  misma omisión, así que es heredada y no introducida, e imprime
  $\left(V_C\sqrt{\sigma}\right)^2$ donde la 5.ª imprime
  $\left(V_C/\sqrt{\sigma}\right)^2$; solo la colocación de la 5.ª edición es
  una velocidad que el avión tiene, ya que $V_C/\sqrt{\sigma}$ es la
  velocidad verdadera de la Ec. (B-7).
- **Evidencia:** análisis dimensional contra la Ec. (B-24) y la Ec. (B-41)
  del mismo documento. Verificado en la página 90 del PDF (p. B-17 impresa)
  de ECAC.CEAC Doc 29, 5.ª ed., Volumen 2: Technical guide, y, para la mitad
  heredada, en la página 86 del PDF (p. B-11 impresa) de ECAC.CEAC Doc 29,
  4.ª edición, Volumen 2, donde la misma definición está bajo la Ec. (B-11) y
  lee
  $\left(V_C\cdot\sqrt{\sigma}\right)^2/\left(2\cdot s_{TOw}\right)$,
  ft/s$^2$. Esta no puede arbitrarse contra los resultados de referencia: la
  hoja de casos de salida `C8-(Departure_Cases)` del Volumen 3 Parte 2 no
  tiene columna de gradiente de pista, así que los 17 casos de referencia se
  vuelan a $G_R = 0$, donde la Ec. (B-18) es la identidad.
- **Comportamiento de la biblioteca:** `flight_performance` restituye $k^2$ y
  toma la colocación de $\sqrt{\sigma}$ de la 5.ª edición; el docstring del
  helper declara ambas desviaciones y que ningún caso de referencia puede
  detectar ninguna de las dos.
- **Estado:** sin notificar.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix B, Ec. (B-21) (velocidad a mitad de paso)

- **Ubicación:** Appendix B, sección B6.1.2, el empuje neto corregido a mitad
  de paso $\overline{CNT}$ definido bajo la Ec. (B-21), en la rama que lo
  calcula desde la Ec. (B-12), es decir, para todo avión que lleva la tabla
  de coeficientes de hélice. B4.1 y B4.2 reparten los turbohélices entre
  ellas sin declarar regla, así que este no es el mismo conjunto que «los
  turbohélices»: de los 20 de ANP v2.3, 11 están en la tabla de hélice y
  llegan a la Ec. (B-12), los otros 9 están en la tabla de reactores y llegan
  a la Ec. (B-9), y los 8 aviones de pistón están todos en la tabla de
  hélice.
- **El impreso:** $\overline{CNT}$ «is the Corrected Net Thrust of the
  aircraft when being located at mid-step, i.e. at the altitude
  $Alt = E_{Apt} + \left(\mathrm{Point\ 1\_Height} + \mathrm{Point\ 2\_Height}\right)/2$»,
  y después, bajo «In the case of Eq. B-12,»,
  $V_T = \sqrt{0.5\left(\left(\mathrm{Point\ 2\_TAS}\right)^2 + \left(\mathrm{Point\ 1\_TAS}\right)^2\right)}$,
  la media cuadrática de las dos velocidades verdaderas de los extremos.
- **El problema:** la velocidad contradice la altitud nombrada una línea más
  arriba. Un paso Climb se vuela a una velocidad calibrada mantenida, así que
  la velocidad verdadera a la altitud de mitad de paso está fijada y es
  $V_C/\sqrt{\sigma}$ evaluada en la $\sigma$ de mitad de paso (Ec. B-7); la
  media cuadrática de los dos valores de los extremos es un número distinto.
  Las dos ramas de la misma lista describen por tanto dos aviones distintos
  en el único punto que ambas llaman mitad de paso: la rama de reactores
  imprime
  $V_C = \mathrm{Point\ 2\_TAS} \cdot \sqrt{\sigma_{Point\ 2}}$, que es la
  propia velocidad calibrada mantenida del paso y sitúa así el avión a
  $V_C/\sqrt{\sigma}$ a media subida, mientras que la rama de la Ec. (B-12)
  lo sitúa en la media cuadrática de los extremos. La media se lee además
  como trasplantada. La sección B6.1.3, para el paso Accelerate, está
  construida exactamente sobre esta media cuadrática y es autoconsistente con
  ella, dando a *ambas* ramas la misma
  $\overline{V_T} = \sqrt{\left(V_{T2}^2 + V_{T1}^2\right)/2}$ y
  convirtiéndola para la forma de reactores con la
  $\sqrt{\sigma_{Alt}}$ de mitad de paso; B6.1.2 conserva la línea de la
  Ec. (B-12) pero sustituye la línea de reactores por una cantidad de
  Point 2, y solo una de las dos sobrevive a la sustitución. De los
  candidatos el impreso es el mayor: a $V_C$ constante la velocidad verdadera
  crece convexamente con la altitud, así que la media cuadrática supera a la
  media aritmética, que supera al valor de media altitud. La Ec. (B-12) hace
  el empuje inversamente proporcional a $V_T$, así que la velocidad impresa
  infravalora el empuje a mitad de paso, infravalora $\sin\gamma$ y tiende la
  subida larga.
- **Evidencia:** reproducción de la hoja `D2-(Departure_Results)` del
  Volumen 3 Parte 2 bajo cada lectura. Los cuatro casos de salida de
  turbohélice son los únicos datos de referencia que llegan a esta rama, y
  son unánimes. En el caso 56 el último punto del perfil está impreso a
  400814.3 ft: la lectura de altitud de mitad de paso lo deja a 0.001 ft, la
  media aritmética 323.944 ft largo y la media cuadrática impresa 544.944 ft
  largo, contra los 0.15 ft con los que las distancias de salida casan por lo
  demás. Los casos 8, 28 y 68 dejan el mismo punto final 172.333, 223.003 y
  544.944 ft largo bajo la lectura impresa y 102.535, 132.673 y 323.944 ft
  largo bajo la media aritmética, siempre largo y nunca cerca de la precisión
  impresa; la lectura de altitud de mitad de paso queda a 0.049 ft de todos
  los puntos de los cuatro casos, peor caso el 28. La desviación crece con la
  altura del paso, como debe un error de convexidad: en el caso 8 la lectura
  impresa deja $V_T$ 0.0225 kt por encima del valor de mitad de paso en la
  subida de 1500 ft y 0.1066 kt por encima en la de 2500 ft. Verificado en la
  página 92 del PDF (p. B-19 impresa) de ECAC.CEAC Doc 29, 5.ª ed.,
  Volumen 2: Technical guide, que lleva la frase de la altitud de mitad de
  paso, la $V_C$ de la rama de reactores y la $V_T$ de la rama de la
  Ec. (B-12) en una misma página, y en la página 95 del PDF (p. B-22 impresa)
  del mismo documento para el par de B6.1.3 del que la línea de la Ec. (B-21)
  parece extraída.
- **Comportamiento de la biblioteca:** `flight_performance` evalúa la forma
  de hélice a la velocidad verdadera que el avión tiene a la altitud de mitad
  de paso, y el comentario del helper del paso Climb cita la expresión
  impresa, dice que el modelo se aparta de ella y apunta aquí.
  `test_departure_case_reproduces_every_profile_point` fija los 190 puntos de
  salida, cuatro de cuyos casos se vuelan sobre la Ec. (B-12).
- **Estado:** sin notificar. De las tres desviaciones del Appendix B
  registradas aquí esta es la que los resultados de referencia deciden con
  más nitidez, y la única que cambia un perfil distribuido.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix D, Table D-6c (la última fila es la última fila de la Table D-6b)

- **Ubicación:** Appendix D, Table D-6c «Revised JETW NPD data using
  SAE-ARP-866A», última fila (JETW, SEL, operación D, ajuste de potencia
  22500).
- **El impreso:** 109.8, 106.0, 103.2, 100.2, 95.2, 89.8, 85.8, 81.4, 76.8 y
  72.3 dB de 200 ft a 25000 ft: los diez valores de la última fila de la
  Table D-6b, el mismo avión recalculado con SAE-ARP-5534, impresa unas
  líneas más arriba en la misma página.
- **El problema:** el texto bajo la Table D-5 construye la Table D-6c como los
  niveles de la Table D-6a más los incrementos SAE-ARP-866A de la Table D-5,
  y las otras seis filas de la tabla son exactamente eso, hasta la última
  cifra. La última fila de la Table D-6a (109.7, 105.7, 102.8, 99.5, 94.0,
  88.0, 83.7, 79.0, 73.9 y 68.7 dB) más los incrementos DEP_103 de la
  Table D-5 (+0.2, +0.3, +0.4, +0.6, +0.9, +1.3, +1.5, +1.8, +2.2 y +2.8 dB)
  da 109.9, 106.0, 103.2, 100.1, 94.9, 89.3, 85.2, 80.8, 76.1 y 71.5 dB, y
  los incrementos sin redondear dan los mismos diez valores. Ocho de las diez
  celdas impresas difieren de ellos, hasta 0.8 dB a 25000 ft; las dos que
  coinciden, a 400 ft y a 630 ft, son las dos en que los incrementos de las
  dos vías redondean a la misma suma. La fila se ha copiado de la Table D-6b
  en lugar de calcularse.
- **Evidencia:** recálculo desde las Tables D-6a y D-5 del mismo ejemplo.
  Verificado en la página 133 del PDF (p. D-9 impresa) de ECAC.CEAC Doc 29,
  5.ª ed., Volumen 2: Technical guide, que lleva las Tables D-6a, D-6b y D-6c
  en una misma página, y en la página 132 del PDF (p. D-8 impresa) del mismo
  documento para los incrementos de la Table D-5.
- **Comportamiento de la biblioteca:** `revise_npd_curves` suma el incremento
  a la Table D-6a y da la fila recalculada.
  `test_revised_npd_data_is_table_d6c_but_its_misprinted_row` la fija, y la
  fila de conformidad *ECAC Doc 29 Appendix D Table D-6c* sostiene las otras
  60 celdas de la tabla.
- **Estado:** sin notificar.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix D, texto bajo la Table D-2 (las Tables D-3b y D-3c emparejadas con los métodos cambiados)

- **Ubicación:** Appendix D, el párrafo bajo la Table D-2 que presenta las
  tres tablas de atenuación del ejemplo resuelto.
- **El impreso:** «together with the absorption coefficients in Table D-1 for
  the AIR-1845 atmosphere and using attenuation values calculated using
  SAE-ARP-5534 and SAE-ARP-866A for the specified atmosphere [...]. All three
  sets of attenuation values are listed in Tables D-3a, D-3b and D-3c
  respectively.»
- **El problema:** «respectively» da SAE-ARP-5534 a la Table D-3b y
  SAE-ARP-866A a la Table D-3c, y las tablas se titulan al revés: la
  Table D-3b «calculated using SAE-ARP-866A», la Table D-3c «calculated using
  SAE-ARP-5534». Los valores siguen a los títulos. SAE ARP 5534 reproduce las
  240 celdas de la Table D-3c hasta la cifra impresa, y SAE ARP 866A 208 de las
  240 de la Table D-3b, y las otras 32 (los caminos más largos en las
  frecuencias más altas) a menos de media unidad de la cifra impresa más 7
  partes por millón, mientras que el emparejamiento que declara la frase se
  aparta hasta 177 dB,
  a 10 kHz y 25000 ft (921.851 dB frente a 744.810 dB). El texto posterior a
  las tablas, que da la Table D-4 a SAE-ARP-5534 y la Table D-5 a
  SAE-ARP-866A, también sigue a los títulos.
- **Evidencia:** comparación de la frase con los dos títulos de tabla, y
  recálculo de las dos tablas por los dos métodos. Verificado en la página 128
  del PDF (p. D-4 impresa) de ECAC.CEAC Doc 29, 5.ª ed., Volumen 2: Technical
  guide para la frase, y en las páginas 130 y 131 del PDF (pp. D-6 y D-7
  impresas) del mismo documento para los títulos y los valores de las
  Tables D-3b y D-3c.
- **Comportamiento de la biblioteca:** no hace falta ninguno; la biblioteca
  empareja cada tabla con el método que nombra su título, que es el
  emparejamiento que confirman sus valores. Las filas de conformidad
  *ECAC Doc 29 Appendix D Table D-3b* y *Table D-3c* sostienen las dos tablas.
- **Estado:** sin notificar.

## ISO 3891:1978, anexo A, tabla 9 (siete celdas una unidad por encima de la tabla 10 donde la humedad no interviene)

- **Ubicación:** anexo A, tabla 9 «Sound attenuation coefficient in dB/100 m
  for 1/3 octave band analysis», humedad relativa del 70 %, frente a la
  tabla 10, humedad relativa del 80 %, impresa debajo en la misma página.
- **El impreso:** la tabla 9 imprime 0,2 en 200 Hz y en 250 Hz a 20 °C, 0,4
  en 500 Hz a 35 °C y en 800 Hz a 10 °C, 0,7 en 1 000 Hz a 30 °C, 1,0 en
  1 600 Hz a 25 °C y 2,9 en 5 000 Hz a 25 °C. La tabla 10 imprime 0,1, 0,1,
  0,3, 0,3, 0,6, 0,9 y 2,8 en las mismas siete celdas.
- **El problema:** en estas siete celdas la humedad no entra en el
  coeficiente. El factor $\eta(\delta)$ de A.2 vale 0,200 a partir de
  $\delta = 6{,}50$ (tabla 1), y en cada una de estas celdas $\delta$ supera
  6,50 tanto al 70 % como al 80 %, así que la fórmula da un único valor,
  0,104, 0,130, 0,349, 0,349, 0,642, 0,946 y 2,849 dB/100 m, para las dos
  tablas. La tabla 10 imprime cada uno redondeado; la tabla 9 imprime cada uno
  una unidad de la última cifra por encima, lo que en 200 Hz y 250 Hz a 20 °C
  duplica el coeficiente y choca con sus propias vecinas a 15 °C y 25 °C,
  impresas las dos como 0,1. La misma fórmula, con $\eta$ leído por la
  cuadrática de tres puntos que pide la tabla 1, reproduce las 264 celdas de la
  tabla 10 de 50 Hz a 10 kHz hasta la cifra impresa. Frente a la tabla 9 falla
  ocho celdas más, por una unidad, en las que $\eta$ sí depende de la humedad:
  800 Hz a 5 °C, 1 250 Hz a 0 °C y a 5 °C, 2 000 Hz a 10 °C, 4 000 Hz a 0 °C,
  6 300 Hz a 10 °C y a 20 °C, y 8 000 Hz a 5 °C. Cada una queda a menos de
  0,014 dB/100 m de un límite de redondeo, ninguna de las lecturas de la
  tabla 1 probadas (la cuadrática de tres puntos, la lineal, la cúbica
  monótona, la de Akima y el spline cúbico) las reproduce todas, y ninguna otra
  tabla las contradice, así que no se registran aquí. Cinco de las siete celdas
  de arriba quedan igual de cerca de un límite, a menos de 0,009 dB/100 m; las
  de 200 Hz y 250 Hz, en 0,104 y 0,130, no.
- **Evidencia:** las dos tablas comparadas celda a celda donde A.2 las hace
  iguales, y recálculo de ambas. Verificado en la página 19 del PDF (p. 16
  impresa) de ISO 3891:1978, que lleva las tablas 9 y 10, y en las páginas 14
  y 15 del PDF (pp. 11 y 12 impresas) del mismo documento para la fórmula de
  A.2 y la tabla 1.
- **Comportamiento de la biblioteca:** `arp866a_attenuation` evalúa la
  fórmula y reproduce la tabla 10; la fila de conformidad
  *ISO 3891:1978 Annex A Table 10* sostiene esa tabla,
  `test_iso3891_table_9_contradicts_table_10_where_humidity_drops_out` fija
  las siete celdas, y
  `test_iso3891_table_9_misses_are_the_seven_errata_and_eight_near_boundaries`
  cuenta las quince.
- **Estado:** sin notificar. ISO 3891:1978 está anulada.

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


---

## ISO 3747:2010, E.4.2.6.2 (el signo del nivel de campo directo)

- **Ubicación:** Anexo E (informativo), E.4.2.6.2 «Excess sound pressure,
  measurement distance effect, $\delta_r$», la frase que da la presión
  radiada directamente y las dos frases que se construyen sobre ella.
- **El impreso:** «the directly radiated pressure is approximately
  $L_{p,\mathrm{direct}} = L_W + 10 \lg(2\pi r^2/r_0^2)$ dB. Rearranging
  Equation (A.1) using $L_{p,\mathrm{direct}}$, gives
  $L_{p(\mathrm{RSS}),r} = L_{p,\mathrm{direct}} + \Delta L_f - 3$ dB», y el
  coeficiente de sensibilidad que sigue,
  $c_r = 10^{-0{,}1(\Delta L_f - 3\ \mathrm{dB})}\,8{,}7/r$.
- **El problema:** el campo directo de una fuente sobre un plano reflectante
  decae con la distancia, $L_{p,\mathrm{direct}} = L_W - 10 \lg(2\pi
  r^2/r_0^2)$ dB; el signo más impreso lo hace crecer. Las dos frases
  siguientes solo se sostienen con el signo menos. Sustituyendo
  $L_{p,\mathrm{direct}} = L_W - 20 \lg(r/r_0) - 8$ dB en la Ec. (A.1)
  reordenada, $L_{p(\mathrm{RSS}),r} = L_{W(\mathrm{RSS})} + \Delta L_f - 11 -
  20 \lg(r/r_0)$ dB, sale el $L_{p,\mathrm{direct}} + \Delta L_f - 3$ dB
  impreso, mientras que el signo más da
  $L_{p,\mathrm{direct}} + \Delta L_f - 19\ \mathrm{dB} - 40 \lg(r/r_0)$; y el
  $8{,}7/r$ del coeficiente de sensibilidad es $20/(r \ln 10)$, la derivada de
  $-20 \lg r$, así que el $c_r$ impreso es la derivada de la forma con signo
  menos. Una errata de signo en un anexo informativo.
- **Evidencia:** las tres frases consecutivas de E.4.2.6.2 leídas una contra
  otra y contra la Ec. (A.1). Verificado en la página 47 del PDF (p. 38
  impresa) y en la página 30 del PDF (p. 21 impresa) de BS EN ISO 3747:2010.
- **Comportamiento de la biblioteca:** el balance de incertidumbre del
  Anexo E no está modelado; la biblioteca evalúa la Ec. (A.1) tal como está
  impresa
  ([`excess_sound_pressure_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py)),
  a la que la errata no afecta. No cambia ningún número.
- **Estado:** sin notificar.

## ISO 3747:2010, E.4.2.5 (la corrección por altitud citada contra el Anexo C)

- **Ubicación:** Anexo E (informativo), E.4.2.5 «Radiation impedance
  correction, $C_2$», las frases que dimensionan $u_{C_2}$.
- **El impreso:** «For altitudes less than 500 m above sea level, no
  meteorological correction is required. At 120 m altitude and 23 °C, the
  correction is 0 dB and at 500 m altitude, the correction is 0,6 dB.
  Assuming a triangular distribution for this uncertainty, the standard
  deviation is $u_{C_2} = 0{,}6/\sqrt{6} = 0{,}3$ dB.»
- **El problema:** el Anexo C, normativo, define la corrección como
  $C_2 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + 15 \lg[(273{,}15 +
  \theta)/\theta_\mathrm{ref}]$ con la presión estática de la Ec. (C.2),
  $p_\mathrm{s} = p_{\mathrm{s},0}\,(1 - aH_\mathrm{a})^b$. A 23 °C eso da
  0,07 dB a 120 m ($p_\mathrm{s}$ = 99,89 kPa, de los que el término de
  presión $-10 \lg(p_\mathrm{s}/p_{\mathrm{s},0})$ son 0,06 dB) y 0,26 dB a
  500 m ($p_\mathrm{s}$ = 95,46 kPa), no los 0,6 dB impresos, y la aritmética
  impresa a continuación tampoco cierra: $0{,}6/\sqrt{6} = 0{,}245$, impreso
  0,3. En el Anexo C no aparece ninguna altitud por debajo de la cual «no se
  requiera corrección meteorológica». El ejemplo informativo es inconsistente
  con el anexo normativo que cita.
- **Evidencia:** recálculo de la Ec. (C.2) y de $C_2$ a partir de las
  constantes impresas ($a$ = 2,2560 × 10⁻⁵ m⁻¹, $b$ = 5,255 3,
  $p_{\mathrm{s},0}$ = 1,013 25 × 10⁵ Pa, $\theta_\mathrm{ref}$ = 296 K).
  Verificado en la página 46 del PDF (p. 37 impresa) y en la página 36 del
  PDF (p. 27 impresa) de BS EN ISO 3747:2010.
- **Comportamiento de la biblioteca:** implementa el Anexo C tal como está
  impreso:
  [`static_pressure_from_altitude`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py)
  evalúa la Ec. (C.2) y el `c2` del resultado la corrección, así que un
  emplazamiento a 500 m recibe los 0,26 dB que da el anexo. El balance
  del Anexo E no está modelado. Fijado por
  `test_static_pressure_from_altitude_eq_c2` en
  [`tests/emission/test_sound_power_in_situ.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_situ.py)
  y por la comprobación de conformidad «ISO 3747:2010 Eq. C.2».
- **Estado:** sin notificar.

## ISO 3747:2010, Tabla E.2 (el exceso que perdió su delta)

- **Ubicación:** Anexo E (informativo), Tabla E.2 «Uncertainty budget for
  determinations of $\sigma_{R0}$...», la celda del coeficiente de
  sensibilidad de la fila $\delta_r$ (distancia de medición).
- **El impreso:** $c_i = 10^{-0{,}1(L_f - 3)}\,8{,}7/r$.
- **El problema:** la magnitud del exponente es el *exceso* de nivel de
  presión acústica sobre el campo libre, el $\Delta L_f$ de la Ec. (A.1), no
  un nivel $L_f$; ninguna magnitud llamada $L_f$ está definida en la norma.
  El apartado E.4.2.6.2, que deduce ese mismo coeficiente, lo imprime como
  $c_r = 10^{-0{,}1(\Delta L_f - 3\ \mathrm{dB})}\,8{,}7/r$, y su caso extremo
  resuelto ($\Delta L_f$ = 7,1 dB, $r$ = 6 m) reproduce el 0,6 que allí se
  cita solo con el exceso en el exponente ($10^{-0{,}41} \times 8{,}7/6 =
  0{,}564$). En la tabla se perdió la delta.
- **Evidencia:** la celda de la tabla leída contra el texto que la deduce,
  verificado en la página 44 del PDF (p. 35 impresa) y en la página 47 del PDF
  (p. 38 impresa) de BS EN ISO 3747:2010. La Tabla E.2 es propia de esta
  parte: la fila correspondiente de ISO 3744:2010 lleva el coeficiente de
  campo libre $c_S = 8{,}7/r$ sin factor de exceso alguno, así que el desliz
  no viene heredado de la familia.
- **Comportamiento de la biblioteca:** el balance de incertidumbre del
  Anexo E no está modelado, y el exceso se evalúa desde la Ec. (A.1) en
  [`excess_sound_pressure_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py).
  No cambia ningún número.
- **Estado:** sin notificar.

## ISO 3747:2010, Tabla E.2 (el coeficiente de muestreo que su propio apartado contradice)

- **Ubicación:** Anexo E (informativo), Tabla E.2 «Uncertainty budget for
  determinations of $\sigma_{R0}$...», la celda del coeficiente de
  sensibilidad de la fila $\delta_\mathrm{mic}$ (muestreo).
- **El impreso:** $c_i = 0{,}5$.
- **El problema:** el apartado E.4.2.6.3, que deduce esa misma fila, imprime lo
  contrario junto con su razón: «Sampling directly affects the total
  uncertainty so $c_\mathrm{mic} = 1$». El balance de E.4.2.12 se pone del
  lado del apartado y no de la tabla: su sexto término es $0{,}7^2$, que es la
  contribución de 0,7 dB que cita E.4.2.6.3 tomada con $c_\mathrm{mic} = 1$. La
  fila vecina zanja que el 0,5 no es una convención general de las filas de
  instrumentación, porque E.4.2.7 fija $c_\mathrm{slm} = 0{,}5$ *y se lo gana*:
  las lecturas repetidas con un mismo sonómetro dejan que los errores
  sistemáticos se cancelen, lo que reduce el coeficiente a la mitad, y el
  apartado reproduce entonces el término que la propia tabla suma
  ($0{,}5 \times 0{,}5 = 0{,}25$ dB, citado allí como 0,3 dB para cada una de
  las dos fuentes, y $\sqrt{0{,}3^2 + 0{,}3^2} = 0{,}42$ dB, el 0,4 que suma
  E.4.2.12). La fila de muestreo no lleva deducción semejante, y no puede
  llevarla: $\delta_\mathrm{mic}$ está definido sobre la *diferencia*
  $\Delta L'_{p(\mathrm{ST-RSS})} = L'_{p(\mathrm{ST})} - L'_{p(\mathrm{RSS})}$,
  que ya abarca las dos fuentes, así que no hay una segunda contribución que
  partir por la mitad. La familia da la razón al apartado: la fila
  $\delta_\mathrm{mic}$ correspondiente de la Tabla H.2 de ISO 3744:2010 lleva
  $c_i = 1$, y su H.4.2.9 imprime también $c_\mathrm{mic} = 1$.
- **Evidencia:** la celda de la tabla, el apartado que la deduce y el
  balance que la suma, leídos en las páginas 44, 47 y 50 del PDF (pp. 35,
  38 y 41 impresas) de BS EN ISO 3747:2010; la comparación con la familia en
  las páginas 79 y 82 del PDF (pp. 70 y 73 impresas) de BS EN ISO 3744:2010.
- **Comportamiento de la biblioteca:** el balance de incertidumbre del
  Anexo E no está modelado. La reproducibilidad que publica la biblioteca es
  el $\sigma_{R0}$ tabulado de la Tabla 2, leído por grado de exactitud.
  No cambia ningún número.
- **Estado:** sin notificar.

## ISO 3747:2010, E.4.2.3 (la ecuación de la que se toma la derivada)

- **Ubicación:** Anexo E (informativo), E.4.2.3 «Sound pressure measurement
  repeatability, $\overline{L'_{p(\mathrm{ST})}}$», la frase que introduce el
  coeficiente de sensibilidad $c_{L'_{p(\mathrm{ST})}}$.
- **El impreso:** «It is obtained from the derivative of
  $L_{W\mathrm{ref,atm}}$ [Equation (E.1)], with respect to
  $\overline{L'_{p(\mathrm{ST})}}$.»
- **El problema:** la Ecuación (E.1) es la desviación típica de las
  condiciones de funcionamiento y montaje, $\sigma_\mathrm{omc} =
  \sqrt{\frac{1}{N-1}\sum (L_{p,j} - L_{p\mathrm{av}})^2}$, que no contiene
  ningún $L_{W\mathrm{ref,atm}}$ y no puede derivarse respecto de
  $\overline{L'_{p(\mathrm{ST})}}$. El modelo que lleva
  $L_{W\mathrm{ref,atm}}$ es la Ecuación (E.2), impresa en la página
  siguiente, y derivarla (con $K_1$ sustituido desde la Ec. 7) sí da el
  $c_{L'_{p(\mathrm{ST})}} = 1 + 1/(10^{0,1\Delta L_p} - 1)$ impreso. Una
  errata de referencia cruzada: (E.1) por (E.2).
- **Evidencia:** verificado en la página 45 del PDF (p. 36 impresa), que lleva
  la frase y el coeficiente, contra la página 41 del PDF (p. 32 impresa) para
  la Ec. (E.1) y la página 42 del PDF (p. 33 impresa) para la Ec. (E.2), de
  BS EN ISO 3747:2010. ISO 3741:2010 imprime el mismo coeficiente como «la
  derivada de $L_W$ respecto de $L'_{p(\mathrm{ST})}$», sin número de
  ecuación, así que el número equivocado es propio de esta parte.
- **Comportamiento de la biblioteca:** el balance de incertidumbre del
  Anexo E no está modelado, así que ningún número de la biblioteca depende de
  él. Se registra para que un lector futuro que siga la deducción no acabe en
  la ecuación equivocada.
- **Estado:** sin notificar.

## ISO 3743-1:2010, 9.1, Ecuación (21) (la desviación típica total escrita $\sigma_\mathrm{TO}$)

- **Ubicación:** 9.1 «Methodology», Ecuación (21).
- **El impreso:** $u(L_W) \approx u(L_J) \approx \sigma_\mathrm{TO}$.
- **El problema:** el subíndice es «TO», en mayúsculas. La frase anterior a la
  ecuación llama a la magnitud «the total standard deviation» y la posterior
  «This total standard deviation»; las Ecuaciones (22) y (23) de la página
  siguiente y el título de 9.5 la escriben $\sigma_\mathrm{tot}$, y la parte no
  define en ningún sitio un $\sigma_\mathrm{TO}$. ISO 3743-2:2018 imprime la
  misma ecuación para sus propios métodos, Fórmula (11), como
  $u(L_W) \approx \sigma_\mathrm{tot}$.
- **Evidencia:** verificado en la página 25 del PDF (p. 16 impresa) de BS EN
  ISO 3743-1:2010, contra las Ecuaciones (22) y (23) en la página 26 del PDF
  (p. 17 impresa) y el título de 9.5 en la página 28 del PDF (p. 19 impresa)
  del mismo documento, y la Fórmula (11) en la página 19 del PDF (p. 13
  impresa) de ISO 3743-2:2018.
- **Comportamiento de la biblioteca:** la desviación típica total es el
  `sigma_tot` de `HardWalledSoundPowerResult`,
  $\sqrt{\sigma_{R0}^2 + \sigma_\mathrm{omc}^2}$ por la Ecuación (22). No hizo
  falta ningún cambio.
- **Estado:** sin notificar.

## ISO 3743-1:2010, Tabla 3 (un intervalo de tercios de octava bajo una cabecera de octavas)

- **Ubicación:** 9.4, Tabla 3 «Typical upper bound values of the standard
  deviation of reproducibility of the method, $\sigma_{R0}$, for A-weighted
  sound power levels and sound energy levels determined in accordance with
  this part of ISO 3743», la tercera fila del bloque de octavas.
- **El impreso:** bajo la cabecera «Octave mid-band frequency, Hz» las filas
  dicen 125, 250, «400 to 5 000» y 8 000, con $\sigma_{R0}$ = 3,0, 2,0, 1,5 y
  2,5 dB.
- **El problema:** 400 Hz y 5 000 Hz no son frecuencias centrales de octava,
  sino centros de tercio de octava. Todas las demás filas del bloque son
  octavas, toda la determinación se hace en bandas de octava (3.11, 7.5), y
  las octavas entre 250 Hz y 8 kHz son 500 Hz, 1 kHz, 2 kHz y 4 kHz. La tabla
  es la Tabla 2 de ISO 3744:2010 pasada a octavas: esa tabla lleva la
  cabecera «One-third-octave mid-band frequency» e imprime los mismos cuatro
  valores frente a «100 to 160», «200 to 315», «400 to 5 000» y «6 300 to
  10 000». Las etiquetas primera, segunda y cuarta se reescribieron como las
  octavas de 125 Hz, 250 Hz y 8 000 Hz; la tercera conservó su intervalo de
  tercios. La Tabla 5 de ISO 3743-2:2018, la misma tabla para la parte 2 con
  sus propios valores, rotula esa fila «500 to 4 000». El título arrastra el
  mismo descuido: anuncia la tabla «for A-weighted sound power levels and sound
  energy levels», y sin embargo cuatro de sus cinco filas son bandas de octava
  y solo la última es ponderada A. El apartado 1.4 de la parte da la
  incertidumbre «for measurements made in frequency octave bands and for
  A-weighted frequency calculations performed on them»; la Tabla 2 de ISO
  3744:2010 se titula «for sound power levels and sound energy levels», y la
  Tabla 5 de ISO 3743-2:2018 «for octave band and A-weighted sound power
  levels».
- **Evidencia:** verificado en la página 28 del PDF (p. 19 impresa) de BS EN
  ISO 3743-1:2010, contra 1.4 en la página 10 del PDF (p. 1 impresa) del
  mismo documento, la Tabla 2 en la página 38 del PDF (p. 29 impresa) de BS EN
  ISO 3744:2010 y la Tabla 5 en la página 22 del PDF (p. 16 impresa) de ISO
  3743-2:2018.
- **Comportamiento de la biblioteca:** lee la fila como las cuatro octavas que
  abarca, de 500 Hz a 4 kHz, cada una con 1,5 dB
  ([`sound_power_hard_walled.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_hard_walled.py)).
  Fijado por `test_table3_sigma_r0_per_band_and_a_weighted` en
  [`tests/emission/test_sound_power_hard_walled.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_hard_walled.py)
  y por la comprobación de conformidad «ISO 3743-1:2010 Table 3».
- **Estado:** sin notificar.

## ISO 3743-1:2010, C.4.2.5 (la corrección por altitud de otra norma)

- **Ubicación:** Anexo C (informativo), C.4.2.5 «Radiation impedance
  correction, $C_2$», las frases que dimensionan $s_{C_2}$.
- **El impreso:** «For altitudes less than 500 m, no meteorological correction
  is required. At 120 m altitude and 23 °C the correction is zero and at 500 m
  altitude the correction is 0,4 dB. Assuming a triangular distribution for
  this uncertainty, the standard deviation is
  $s_{C_2} = 0{,}4/\sqrt{6} = 0{,}2\ \mathrm{dB}$.»
- **El problema:** la corrección de esta parte es el $C_2$ del Anexo A,
  $C_2 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + 15 \lg[(273{,}15 +
  \theta)/\theta_1]$ con $\theta_1$ = 296 K y la presión estática de la
  Ecuación (A.2). A 23 °C da 0,07 dB a 120 m ($p_\mathrm{s}$ = 99,89 kPa) y
  0,26 dB a 500 m ($p_\mathrm{s}$ = 95,46 kPa), no cero y 0,4 dB. Los dos
  números impresos son los de la suma $C_1 + C_2$ del apartado 9.1.4 de ISO
  3741:2010, cuyo $C_1 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) +
  5 \lg[(273{,}15 + \theta)/314]$ deja la suma en 0,000 dB a 120 m y en
  0,394 dB a 500 m. Un método de comparación no tiene $C_1$: se cancela entre
  la fuente en ensayo y la fuente sonora de referencia, y por eso el Anexo A
  imprime $C_2$ solo. El divisor es correcto, $0{,}4/\sqrt{6} = 0{,}16$, que
  redondea al 0,2 impreso.
- **Evidencia:** recálculo de la Ecuación (A.2) y de $C_2$ a partir de las
  constantes que imprime el Anexo A ($a$ = 2,256 0 × 10⁻⁵ m⁻¹, $b$ = 5,255 3,
  $p_{\mathrm{s},0}$ = 101,325 kPa, $\theta_1$ = 296 K), y de $C_1 + C_2$ a
  partir del apartado 9.1.4 de ISO 3741:2010. Verificado en la página 41 del
  PDF (p. 32 impresa) y en la página 31 del PDF (p. 22 impresa) de BS EN ISO
  3743-1:2010.
- **Comportamiento de la biblioteca:** implementa el Anexo A tal como está
  impreso: un emplazamiento a 500 m y 23 °C recibe $C_2$ = 0,26 dB en `c2` y
  en `sound_power_level_ref`
  ([`sound_power_hard_walled.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_hard_walled.py)).
  El balance del Anexo C no está modelado. Fijado por
  `test_annex_a_c2_at_500_m_is_0_26_db` en
  [`tests/emission/test_sound_power_hard_walled.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_hard_walled.py)
  y por la comprobación de conformidad «ISO 3743-1:2010 Annex A».
- **Estado:** sin notificar.

## ISO 3743-1:2010, C.4.2.8 y C.4.2.9 (la banda de humedad de ISO 3741 citada en el 30 % en lugar del 50 %)

- **Ubicación:** Anexo C (informativo), C.4.2.8 «Temperature, $\delta_\theta$»
  y C.4.2.9 «Humidity, $\delta_H$», el último párrafo de cada uno.
- **El impreso:** C.4.2.8 «Recommended temperature and humidity ranges given in
  ISO 3741 are ±1 °C and ±3 % $H$ below 20 °C when below 30 % $H$, to a maximum
  of ±5 °C and ±10 % $H$ above 20 °C when above 30 % $H$»; C.4.2.9 «The
  recommended humidity ranges given in ISO 3741 are ±3 %, if $H \leqslant$
  30 %, to a maximum of ±10 %, if $H$ > 30 % $H$».
- **El problema:** la Tabla 3 de ISO 3741:2010 tiene tres columnas de humedad,
  por debajo del 30 %, del 30 % al 50 % y por encima del 50 %, y solo admite
  ±10 % en la última; del 30 % al 50 % admite ±5 %. Las dos cláusulas ponen el
  ±10 % por encima del 30 %, así que la columna central de la tabla que citan
  se pierde. ISO 3743-2:2018 imprime las mismas dos frases en D.4.2.8 y D.4.2.9
  con «above 50 % $H$», que es lo que dice la tabla.
- **Evidencia:** verificado en la página 42 del PDF (p. 33 impresa) de BS EN
  ISO 3743-1:2010, contra la Tabla 3 en la página 18 del PDF (p. 9 impresa) de
  BS EN ISO 3741:2010 y D.4.2.8 y D.4.2.9 en la página 39 del PDF (p. 33
  impresa) de ISO 3743-2:2018.
- **Comportamiento de la biblioteca:** el balance del Anexo C no está modelado
  y nada lee a través de él las tolerancias de ISO 3741. No hizo falta ningún
  cambio.
- **Estado:** sin notificar.

## ISO 3743-2:2018, D.4.2.5 (la corrección por altitud de otra norma)

- **Ubicación:** Anexo D (informativo), D.4.2.5 «Meteorological correction,
  $C_2$», las frases que dimensionan $s_{C_2}$.
- **El impreso:** «For altitudes less than 500 m above sea level, no
  meteorological correction is required. At 120 m altitude and 23 °C the
  correction is zero and at 500 m altitude the correction is 0,4 dB. Assuming
  a triangular distribution for this uncertainty, the standard deviation is
  $s_{C_2} = 0{,}4/\sqrt{6} = 0{,}2$ dB.»
- **El problema:** la misma frase que C.4.2.5 de ISO 3743-1:2010, y el mismo
  defecto. La corrección de esta parte es el $C_2$ de la Fórmula (E.2), que a
  23 °C y con la presión estática de la Fórmula (E.3) vale 0,07 dB a 120 m y
  0,26 dB a 500 m; cero y 0,4 dB son de la suma $C_1 + C_2$ del apartado 9.1.4
  de ISO 3741:2010, y ninguno de los dos métodos de esta parte aplica un $C_1$
  (las Fórmulas (9) y (10) no lo llevan, y la Fórmula (D.2) solo enumera
  $C_2$).
- **Evidencia:** recálculo de las Fórmulas (E.2) y (E.3) a partir de las
  constantes impresas. Verificado en la página 38 del PDF (p. 32 impresa) y en
  la página 42 del PDF (p. 36 impresa) de ISO 3743-2:2018.
- **Comportamiento de la biblioteca:** implementa el Anexo E tal como está
  impreso, con el mismo $C_2$ que la parte 1
  ([`sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_special_room.py)).
  El balance del Anexo D no está modelado. Fijado por
  `test_annex_e_c2_matches_part_1` en
  [`tests/emission/test_sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_special_room.py)
  y por la comprobación de conformidad «ISO 3743-1:2010 Annex A».
- **Estado:** sin notificar.

## ISO 3743-2:2018, 11.3.2, Fórmula (14) (la desviación total y la de funcionamiento, sumadas en lugar de restadas)

- **Ubicación:** 11.3.2 «Round robin test», Fórmula (14).
- **El impreso:** $\sigma'_{R0} = \sqrt{{\sigma'_\mathrm{tot}}^2 +
  {\sigma'_\mathrm{omc}}^2}$.
- **El problema:** la frase que presenta la fórmula dice que la desviación
  típica total de un ensayo interlaboratorio «includes the standard deviation
  $\sigma'_\mathrm{omc}$» y «allows $\sigma'_{R0}$ to be determined», que es la
  Fórmula (12), $\sigma_\mathrm{tot} = \sqrt{\sigma_{R0}^2 +
  \sigma_\mathrm{omc}^2}$, despejada para $\sigma_{R0}$: la desviación de
  funcionamiento sale restando. Con el signo más, la parte del método superaría
  al total del que se extrae. El párrafo siguiente solo tiene sentido con el
  signo menos: la Fórmula (14) «is imprecise if $\sigma_\mathrm{tot}$ is only
  slightly higher than $\sigma_\mathrm{omc}$» y entonces «provides a small
  value of $\sigma_{R0}$», cosa que una suma no puede hacer nunca. ISO
  3743-1:2010 imprime la misma fórmula, la Ecuación (24), con el signo menos.
- **Evidencia:** verificado en la página 20 del PDF (p. 14 impresa) y en la
  página 21 del PDF (p. 15 impresa) de ISO 3743-2:2018, contra la Ecuación
  (24) en la página 27 del PDF (p. 18 impresa) de BS EN ISO 3743-1:2010.
- **Comportamiento de la biblioteca:**
  [`reproducibility_from_round_robin`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_hard_walled.py)
  evalúa la diferencia para las dos partes, y avisa cuando
  $\sigma_\mathrm{omc}$ supera $\sigma_\mathrm{tot}/\sqrt{2}$, como piden las
  dos. Fijado por
  `test_round_robin_reproducibility_is_the_quadrature_difference` en
  [`tests/emission/test_sound_power_hard_walled.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_hard_walled.py)
  y por la comprobación de conformidad «ISO 3743-1:2010 Eq. 24 / ISO
  3743-2:2018 Formula 14».
- **Estado:** sin notificar.

## ISO 3743-2:2018, D.4.2.4 y D.4.2.12 (una contribución del ruido de fondo que no es el producto que nombra, y un balance que no la usa)

- **Ubicación:** Anexo D (informativo), D.4.2.4 «Background noise correction,
  $K_1$», la contribución extrema y la típica, y D.4.2.12 «Typical value for
  direct method, $\sigma_{R0}$», el tercer término de la suma.
- **El impreso:** «The worst case, $\overline{L'_p} - \overline{L_{p(\mathrm{B})}}$
  is 4 dB. This results in a sensitivity coefficient of $c_{K_1}$ = 0,7 and a
  total contribution to uncertainty of 1,7 dB. Typically this contribution
  will be closer to 1,0 dB due to better control of the background noise.»,
  después de «high background noise levels with a standard deviation of 3 dB
  are assumed»; y en D.4.2.12, $\sigma_{R0} = \sqrt{0{,}3^2 + 0{,}4^2 +
  0{,}4^2 + 0{,}2^2 + 0{,}5^2 + 0{,}8^2 + 0{,}2^2 + 0{,}2^2 + 0{,}04^2 +
  0{,}1^2} = 1{,}2$ dB.
- **El problema:** dos defectos. (a) La contribución es el coeficiente de
  sensibilidad por la incertidumbre típica, y el apartado da los dos: con un
  margen de 4 dB, $c_{K_1} = 1/(10^{0{,}4} - 1) = 0{,}66$, impreso 0,7, y
  $u_{K_1}$ = 3 dB, así que la contribución extrema es 2,0 dB (2,1 dB con el
  0,7 redondeado), no 1,7 dB. El 1,7 es el $c_{L'_p} = 1 + c_{K_1}$ que D.4.2.3
  cita para el mismo escenario. C.4.2.4 de ISO 3743-1:2010 hace la misma
  cuenta con su margen de 6 dB y la cierra: 0,3 × 3 dB = 1,0 dB. (b) El tercer
  término de la suma de D.4.2.12, que ocupa el lugar de la fila $K_1$ de la
  Tabla D.2, es 0,4 dB, el valor típico que da C.4.2.4 de ISO 3743-1:2010 para
  la parte 1; el apartado de esta parte pone la contribución típica en 1,0 dB.
  Con 1,0 dB la suma da 1,5 dB en lugar del 1,2 dB impreso.
- **Evidencia:** los propios datos del apartado, recalculados, leídos en la
  página 37 del PDF (p. 31 impresa) y en la página 40 del PDF (p. 34 impresa)
  de ISO 3743-2:2018, contra C.4.2.4 en la página 40 del PDF (p. 31 impresa)
  de BS EN ISO 3743-1:2010.
- **Comportamiento de la biblioteca:** el balance del Anexo D no está
  modelado; la biblioteca publica las cotas superiores típicas de la Tabla 5.
  No cambia ningún número.
- **Estado:** sin notificar.

## ISO 3743-2:2018, D.4.2.11 y Tabla D.2 (un coeficiente del tiempo de reverberación que no es la derivada de ninguna de las dos)

- **Ubicación:** Anexo D (informativo), D.4.2.11 «Reverberation time,
  $T_\mathrm{nom}$», el ejemplo del peor caso, y la fila $T_\mathrm{nom}$ de la
  Tabla D.2.
- **El impreso:** D.4.2.11: «The sensitivity coefficient, $c_T$, due to
  reverberation time is obtained from the derivative of $L_W$ [see Formula
  (9)] with respect to reverberation time. The worst case example assumes a
  source producing dominant noise at about 500 Hz. Using the minimum 0,5 s
  nominal reverberation time from 6.3 and assuming a standard deviation
  $s_T$ = 0,3 s at 500 Hz, the sensitivity coefficient is −5 dB/s and the
  worst case uncertainty contribution $u_T c_T$ = 1 dB.» Tabla D.2:
  $c_T = -4{,}3/T_\mathrm{nom} - 240 \cdot V/(T_\mathrm{nom}^2 \cdot S \cdot c)$.
- **El problema:** la Fórmula (9) depende del tiempo de reverberación solo a
  través de $-10 \lg(T_\mathrm{nom}/T_0)$, cuya derivada es
  $-10/(T_\mathrm{nom} \ln 10) = -4{,}34/T_\mathrm{nom}$: −8,7 dB/s a 0,5 s,
  no −5 dB/s. La Tabla D.2 añade un segundo término que la Fórmula (9) no
  tiene: es la derivada del $4{,}34\,A/S$ de la Ecuación (20) de ISO 3741:2010
  con $A = 55{,}26\,V/(c\,T)$ ($4{,}34 \times 55{,}26 = 240$), así que la tabla
  deriva ISO 3741 y no la fórmula que nombra el apartado; para un cubo de
  70 m³ a 343 m/s lleva el coeficiente a −10,5 dB/s. Y la contribución del
  peor caso no se sigue del propio $u_T = \sqrt{2{,}42\,T_\mathrm{nom}/f +
  s_T^2/N_\mathrm{decays}}$ de la tabla con las 120 caídas que el apartado
  llama típicas: $u_T$ = 0,056 s, y 0,056 s × 8,7 dB/s = 0,5 dB.
- **Evidencia:** verificado en la página 40 del PDF (p. 34 impresa) y en la
  página 36 del PDF (p. 30 impresa) de ISO 3743-2:2018, contra la Fórmula (9)
  en la página 18 del PDF (p. 12 impresa); la razón entre la derivada y el
  coeficiente impreso, 8,69/5 = 1,74, se contrastó con la página, que imprime
  −5 dB/s.
- **Comportamiento de la biblioteca:** el balance del Anexo D no está
  modelado. No cambia ningún número.
- **Estado:** sin notificar.

## ISO 3743-2:2018, Fórmula (D.1) (una suma que empieza en $j = i$)

- **Ubicación:** Anexo D (informativo), D.3, Fórmula (D.1).
- **El impreso:** $\sigma_\mathrm{omc} = \sqrt{\frac{1}{N-1} \sum_{j=i}^{N}
  (L_{p,j} - L_{p\mathrm{av}})^2}$ dB.
- **El problema:** el límite inferior de la suma es $j = i$; el apartado no
  define ningún $i$, y el $N - 1$ del divisor es la desviación típica muestral
  de las $N$ repeticiones, que empieza en $j = 1$. ISO 3743-1:2010 imprime la
  misma fórmula, la Ecuación (C.1), con $j = 1$.
- **Evidencia:** verificado en la página 32 del PDF (p. 26 impresa) de ISO
  3743-2:2018, contra la Ecuación (C.1) en la página 35 del PDF (p. 26
  impresa) de BS EN ISO 3743-1:2010.
- **Comportamiento de la biblioteca:** la desviación típica de las condiciones
  de funcionamiento y montaje se toma del usuario como `sigma_omc_db`; donde la
  biblioteca la calcula a partir de lecturas repetidas, suma sobre todas ellas
  ([`operating_standard_deviation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/workstation.py)).
  No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO 3743-2:2018, D.4.2.8 (la frecuencia de la fórmula definida como $F$)

- **Ubicación:** Anexo D (informativo), D.4.2.8 «Temperature, $\delta_\theta$»,
  la lista de símbolos bajo la fórmula de $c_\theta$.
- **El impreso:** la fórmula lleva $\lg(2{,}6 f)$, y la lista de símbolos
  define «$F$ is the highest frequency significantly affecting the A-weighted
  levels».
- **El problema:** el símbolo es $f$ en la fórmula, en la Tabla D.2 y en la
  lista de símbolos de D.4.2.9, unas líneas más abajo, que define la misma
  magnitud como «$f$ is the highest frequency significantly affecting the A-
  weighted levels»; C.4.2.8 de ISO 3743-1:2010 escribe $f$ en los dos sitios.
- **Evidencia:** verificado en la página 39 del PDF (p. 33 impresa) de ISO
  3743-2:2018, contra C.4.2.8 en la página 42 del PDF (p. 33 impresa) de BS EN
  ISO 3743-1:2010.
- **Comportamiento de la biblioteca:** el balance del Anexo D no está
  modelado. No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO 3743-2:2018, 3.1 (la designación escrita «ISO ISO 3743-2»)

- **Ubicación:** capítulo 3 «Terms and definitions», 3.1 «special
  reverberation test room».
- **El impreso:** «room which meets the requirements of Clause 6 of ISO ISO
  3743-2».
- **El problema:** «ISO» está impreso dos veces. La definición nombra el
  propio documento en el que está, al que el resto de la edición llama «this
  document».
- **Evidencia:** verificado en la página 8 del PDF (p. 2 impresa) de ISO
  3743-2:2018.
- **Comportamiento de la biblioteca:** una etiqueta que la biblioteca no lee.
  No hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO 3743-2:2018, 6.3, Figura 1 (una curva que va por encima de la fórmula (1) en graves)

- **Ubicación:** 6.3, Figura 1 «Values of $R$ at the one-third-octave-band
  centre frequencies for $V$ = 70 m³», y la frase que la precede.
- **El impreso:** 6.3 da $R = 1 + 257/(f V^{1/3})$ como fórmula (1) y dice
  «For a room volume $V$ of 70 m³, the value of $R$ is determined from Figure
  1». La curva de la figura, leída contra su propia cuadrícula (0,2 por
  división), pasa por 1,66 a 100 Hz, 1,54 a 125 Hz, 1,43 a 160 Hz, 1,34 a
  200 Hz, 1,06 a 1 000 Hz y 1,02 a 2 000 Hz.
- **El problema:** la fórmula (1) para 70 m³ da 1,62, 1,50, 1,39, 1,31, 1,06 y
  1,03 en las mismas frecuencias. La figura coincide con ella a 1 000 Hz, la
  frecuencia que usa la fórmula (B.2), pero va entre 0,03 y 0,04 por encima de
  100 Hz a 160 Hz y alrededor de 0,01 por debajo a partir de 1 600 Hz, de
  cuatro a cinco veces el grosor de la línea trazada en graves. La figura a la
  que la cláusula manda una sala de 70 m³ no es, por tanto, la fórmula que la
  misma cláusula da para toda sala, y una sala cuyo tiempo de reverberación
  sigue la figura se mide contra límites un 2,5 % más altos a 100 Hz que una
  que sigue la fórmula.
- **Evidencia:** verificado en la página 10 del PDF (p. 4 impresa) de ISO
  3743-2:2018, la curva leída en cada línea de tercio de octava de la
  cuadrícula contra las horizontales de $R$ = 0 y $R$ = 2, contra la fórmula
  (1) en la página 9 del PDF (p. 3 impresa) del mismo documento.
- **Comportamiento de la biblioteca:** `reverberation_parameter` y
  `check_special_room_reverberation` evalúan la fórmula (1) para cualquier
  volumen, 70 m³ incluido, y no toman nada de la figura
  ([`sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_special_room.py)).
  La diferencia a 100 Hz es una cuarta parte de la tolerancia de ±10 % de 6.3.
  Fijado por `test_formula1_gives_the_1_06_of_formula_b2_for_70_m3` en
  [`tests/emission/test_sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_special_room.py)
  y por la comprobación de conformidad «ISO 3743-2:2018 Formula 1 / Formula
  B.2».
- **Estado:** sin notificar.

## ISO 3743-2:2018, Figura B.3 (las curvas límite ensanchadas en 6,3 kHz, donde 6.3 las ensancha por encima)

- **Ubicación:** Anexo B (informativo), B.5, Figura B.3 «Limiting curves for
  the ratio of the reverberation time $T$ to the nominal reverberation time
  $T_\mathrm{nom}$ for a 70 m³ room».
- **El impreso:** 6.3 fija los límites en $0{,}9\,R\,T_\mathrm{nom}$ y
  $1{,}1\,R\,T_\mathrm{nom}$ y dice «For frequencies above 6,3 kHz, constants
  0,9 and 1,1 shall be replaced by 0,8 and 1,2 respectively». Las dos curvas
  límite de la Figura B.3, leídas contra la propia cuadrícula de la figura
  (0,2 por división), empiezan a separarse por encima de 4 kHz y pasan por
  1,22 y 0,84 en la banda de 6,3 kHz, donde casi han alcanzado las mesetas de
  alrededor de 1,23 y 0,82 que mantienen hasta 10 kHz.
- **El problema:** en 6,3 kHz el texto aún sujeta la banda a 0,9 y 1,1: con
  $R$ = 1,01 para 70 m³ los límites son 0,91 y 1,11. La figura dibuja ya el
  par ancho en esa banda, 0,1 más ancho por cada lado, de modo que una sala
  cuya banda de 6,3 kHz lee 1,15 $R$ cumple frente a la figura e incumple
  frente al texto. El ensanchamiento corresponde a las bandas por encima de
  6,3 kHz, la primera de las cuales es la de 8 kHz.
- **Evidencia:** verificado en la página 28 del PDF (p. 22 impresa) de ISO
  3743-2:2018, las curvas leídas en las abscisas de tercio de octava contra
  las líneas de la cuadrícula en 0 y 1,8, contra 6.3 en la página 9 del PDF
  (p. 3 impresa) del mismo documento.
- **Comportamiento de la biblioteca:** sigue el texto. La tolerancia ancha
  empieza en el borde superior de la banda de 6,3 kHz, así que 8 kHz y 10 kHz
  toman 0,8 y 1,2 y 6,3 kHz conserva 0,9 y 1,1, y
  `SpecialRoomReverberationCheck.plot` dibuja las curvas así
  ([`sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_special_room.py)).
  Fijado por `test_bands_above_6_3_khz_take_the_wider_tolerance` en
  [`tests/emission/test_sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_special_room.py)
  y por la comprobación de conformidad «ISO 3743-2:2018 6.3».
- **Estado:** sin notificar.

## ISO 3743-2:2018, B.5, EXAMPLE (un centrado que deja la curva de la Figura B.4 fuera de los límites)

- **Ubicación:** Anexo B (informativo), B.5 «Example of determination of the
  nominal reverberation time of a room», el EXAMPLE, y la NOTA de la
  Figura B.3.
- **El impreso:** «When the data of Figure B.4 are centred within the
  limiting curves of Figure B.3, it is found that, at 1 000 Hz, the ratio
  $T/T_{1\,000}$ = 1 corresponds to $T/T_\mathrm{nom}$ = 1,09», y así
  $T_\mathrm{nom} = 0{,}8/1{,}09 = 0{,}73$ s; la NOTA de la Figura B.3 dice
  «The data of Figure B.4 are centred within the limiting curves.»
- **El problema:** la curva de la Figura B.4, leída contra su cuadrícula, da
  $T/T_{1\,000}$ = 1,40 a 100 Hz, 1,34 a 200 Hz, 1,30 a 250 Hz, 1,24 a
  315 Hz, 1,00 de 1 000 Hz a 2 000 Hz y 0,80 a 10 kHz. Multiplicadas por 1,09
  y divididas por el $R$ de la fórmula (1) para 70 m³, las bandas de 200 Hz a
  400 Hz superan 1,1, y la de 250 Hz llega a 1,13: centrada como se imprime,
  la sala del ejemplo incumple el requisito de 6.3 que ilustra. El 1,09 es el
  punto medio de las razones extremas $q = (T/T_{1\,000})/R$ tomadas como si
  0,9 y 1,1 valieran en todas las bandas, $2/(q_{\max} + q_{\min})$ con el 0,80
  de 10 kHz como mínimo, aunque 6.3 admite 0,8 ahí; el centrado que usa los
  límites de cada banda deja todas dentro con $T/T_\mathrm{nom}$ = 1,05,
  $T_\mathrm{nom}$ = 0,76 s. La Figura B.3 tampoco dibuja la Figura B.4
  multiplicada por 1,09: su curva de datos está en 1,09 de 1 000 Hz a
  2 000 Hz pero en 1,46 a 100 Hz, 1,37 a 250 Hz y 0,95 a 10 kHz, donde 1,09
  veces la Figura B.4 da 1,52, 1,41 y 0,87.
- **Evidencia:** verificado en la página 28 del PDF (p. 22 impresa) y en la
  página 29 del PDF (p. 23 impresa) de ISO 3743-2:2018, las dos curvas leídas
  en las abscisas de tercio de octava contra sus cuadrículas, con $R$ de la
  fórmula (1) en la página 9 del PDF (p. 3 impresa); las razones son un
  recálculo a partir de esas lecturas.
- **Comportamiento de la biblioteca:** `check_special_room_reverberation`
  centra $T_\mathrm{nom}$ minimizando la mayor desviación de cualquier banda
  respecto a la curva ideal, cada una medida contra su propia tolerancia;
  sobre la curva de la Figura B.4 devuelve 0,76 s y cualifica la sala, a
  0,17 dB de los 0,73 s impresos en el $L_W$ de la fórmula (9). Un valor dado
  en `nominal_reverberation_time_s` se comprueba tal cual, y los 0,73 s
  impresos incumplen en 250 Hz
  ([`sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_special_room.py)).
  Fijado por `test_the_b5_example_centres_the_room_within_its_curves` y
  `test_the_printed_1_09_of_b5_is_the_narrow_midpoint_and_fails_250_hz` en
  [`tests/emission/test_sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_special_room.py)
  y por la comprobación de conformidad «ISO 3743-2:2018 B.5 EXAMPLE».
- **Estado:** sin notificar.

## ISO 3743-2:2018, F.1 (el Anexo F atado al método directo cuando 10.4 le envía el de comparación)

- **Ubicación:** Anexo F (normativo), F.1 «A-weighted sound power levels», la
  frase sobre la fórmula (F.1) y la lista de símbolos que la sigue.
- **El impreso:** «The A-weighted sound power level, $L_{WA}$, determined from
  octave band sound power levels according to 10.2 shall be calculated from
  Formula (F.1)», y «$L_{Wk}$ is the sound power level in the $k$th octave
  band determined according to 10.2».
- **El problema:** 10.2 es el método directo. La única cláusula del documento
  que llama al Anexo F es 10.4, «A-weighted sound power levels determined by
  the comparison method», que le envía las bandas de octava «made ...
  according to 10.3». Leído tal como está impreso, el anexo cubre el método
  que nunca lo cita y deja fuera el que sí lo hace. El Anexo E, el anterior,
  escribe «from the formula in 10.2 or the formula in 10.3».
- **Evidencia:** verificado en la página 43 del PDF (p. 37 impresa) de ISO
  3743-2:2018, contra 10.4 en la página 19 del PDF (p. 13 impresa) y el Anexo
  E en la página 42 del PDF (p. 36 impresa) del mismo documento.
- **Comportamiento de la biblioteca:** la fórmula (F.1) forma
  `sound_power_level_a` con las bandas de octava de los dos métodos, como el
  Anexo E está escrito para ambos
  ([`sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_special_room.py)).
  Fijado por `test_comparison_a_weighted_total_is_annex_f` y
  `test_a_weighted_level_by_formula9_directly` en
  [`tests/emission/test_sound_power_special_room.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_special_room.py).
- **Estado:** sin notificar.

## ISO 5136:2003, Tabla A.5, fila de 5 000 Hz (falta el primer dígito de $a_3$)

- **Ubicación:** Anexo A, Tabla A.5, «Values of coefficients $a_i$ for the
  determination of the combined mean flow velocity and modal correction
  $C_{3,4}$ of the sampling tube for duct diameters 0,8 m $\le d <$ 1,25 m»,
  fila de 5 000 Hz, columna $a_3$.
- **El impreso:** $- ,24 \times 10^{-05}$: un signo menos, un espacio, una
  coma decimal y dos dígitos, sin ningún dígito antes de la coma. Todas las
  demás celdas de las doce tablas de coeficientes de los Anexos A, H e I
  imprimen un dígito antes de la coma.
- **El problema:** el coeficiente no puede leerse del documento, y la fila
  está dentro del rango normativo de la norma (5 000 Hz, $|U| \le 40$ m/s).
  El $a_3$ de la misma banda en las dos tablas vecinas es
  $-1{,}17 \times 10^{-5}$ (Tabla A.4, de 0,5 m a 0,8 m) y
  $-1{,}27 \times 10^{-5}$ (Tabla A.6, de 1,25 m a 2 m), que encierran
  $-1{,}24 \times 10^{-5}$; un primer dígito de 2 o mayor movería $C_{3,4}$
  a 40 m/s en 0,64 dB por unidad del dígito ($a_3 U^3$ con
  $U^3 = 6{,}4 \times 10^4$), cosa que ninguna banda ni tabla vecina
  respalda.
- **Evidencia:** la celda tal como está impresa. Página 39 del PDF (p. 29
  impresa) de ISO 5136:2003, frente a la misma celda de la Tabla A.4 en la
  página 38 del PDF (p. 28 impresa) y de la Tabla A.6 en la página 40 del
  PDF (p. 30 impresa).
- **Comportamiento de la biblioteca:** lee $-1{,}24 \times 10^{-5}$, el
  valor que encierran las vecinas, en `_TABLE_A5` de
  [`sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py).
  El comentario de la tabla y
  `test_table_a5_5000_hz_reads_the_missing_digit_as_one` en
  [`tests/emission/test_sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_duct.py)
  dicen que es una lectura y no el impreso; un ejemplar de la norma en el
  que el dígito haya sobrevivido lo zanjaría.
- **Estado:** sin notificar.

## ISO 5136:2003, Anexo D, Anexo H y Anexo I ($C_{3,4}$ «according to Equation (3)»)

- **Ubicación:** la primera frase del Anexo D, y la frase del Anexo H y del
  Anexo I que introduce sus tablas de coeficientes.
- **El impreso:** «For $d$ = 0,5 m, the values of the coefficients $a_i$ for
  the calculation of $C_{3,4}$ according to Equation (3) are given in Table
  A.4» (Anexo D); «Values for the coefficients $a_i$ necessary to compute the
  mean flow velocity-modal corrections $C_{3,4}$ according to Equation (3)
  are given in Tables H.1 to H.3» (Anexo H) y «... in Tables I.1 to I.3»
  (Anexo I).
- **El problema:** la Ecuación (3) es la frecuencia de corte del primer modo
  transversal, $f_{1,0} = 0{,}586\,(c/D)\sqrt{1 - (U/c)^2}$, en la
  definición de 3.10. El polinomio en $U$ cuyos coeficientes contienen las
  tablas es la Ecuación (7) del apartado 5.3.3.4. El mismo número erróneo se
  imprime tres veces.
- **Evidencia:** páginas 45, 64 y 68 del PDF (pp. 35, 54 y 58 impresas) de
  ISO 5136:2003, frente a la Ecuación (3) en la página 16 del PDF (p. 6
  impresa) y la Ecuación (7) en la página 28 del PDF (p. 18 impresa).
- **Comportamiento de la biblioteca:** evalúa la Ecuación (7);
  [`flow_modal_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py)
  la cita. Ningún número cambia.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## ISO 5136:2003, Anexo B, B.2 paso 4 ($\Delta L_{\max}$ «given in Table C.1»)

- **Ubicación:** Anexo B, apartado B.2, «Comparative procedure using a
  microphone fitted with a nose cone and a microphone fitted with a sampling
  tube», paso 4.
- **El impreso:** «Check whether the difference between the circumferentially
  averaged sound pressure levels obtained with the nose cone and the sampling
  tube ($\overline{L_{p\mathrm{NC}}} - \overline{L_{p\mathrm{ST}}}$) is
  smaller than or equal to the maximum allowable difference $\Delta L_{\max}$
  given in Table C.1.»
- **El problema:** la Tabla C.1 es la ponderación A $C_j$ del Anexo C y no
  contiene ningún $\Delta L_{\max}$. La tabla de la diferencia máxima
  admisible frente a la supresión del ruido de turbulencia
  $\Delta L_\mathrm{t}$ del tubo de muestreo es la Tabla B.1, en la página
  siguiente al paso, y el párrafo dos por encima de los pasos ya remite a
  ella («see Table B.1»).
- **Evidencia:** página 41 del PDF (p. 31 impresa) de ISO 5136:2003, con la
  Tabla B.1 en la página 42 del PDF (p. 32 impresa) y la Tabla C.1 en la
  página 44 del PDF (p. 34 impresa).
- **Comportamiento de la biblioteca:** el procedimiento de relación
  señal-ruido del Anexo B es una cualificación de la medición, no un término
  de $L_W$, y no está implementado. No hizo falta ningún cambio.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## ISO 5136:2003, Anexo B, B.1 («the determination of the combined mean flow velocity»)

- **Ubicación:** Anexo B, apartado B.1, «General», la primera frase.
- **El impreso:** «Two procedures for the determination of the combined mean
  flow velocity are given in B.2 and B.3.»
- **El problema:** el anexo se titula «Determination of the signal-to-noise
  ratio of sound vs. turbulent pressure fluctuation in the test duct», y B.2
  y B.3 determinan esa relación; nada en el anexo determina una «combined
  mean flow velocity», una expresión que es un fragmento de la «combined
  mean flow velocity and modal correction» del apartado 5.3.3.4. La frase
  también cuenta dos procedimientos donde el anexo, con el método de
  coherencia con el que cierra, da tres.
- **Evidencia:** página 41 del PDF (p. 31 impresa) de ISO 5136:2003, el
  título del anexo y la frase en la misma página, y el procedimiento de
  coherencia en la página 43 del PDF (p. 33 impresa).
- **Comportamiento de la biblioteca:** el Anexo B no está implementado; nada
  que cambiar.
- **Estado:** sin notificar (defecto de redacción).

## ISO 5136:2003, apartado 7.4 NOTA (el «diámetro hidráulico» $D_\mathrm{h} = \sqrt{S_{\mathrm{f}2}/\pi}$)

- **Ubicación:** apartado 7.4, la NOTA que sigue a la regla del conducto de
  impulsión para ventiladores grandes de la categoría de instalación D.
- **El impreso:** «The hydraulic diameter of the fan outlet area,
  $S_{\mathrm{f}2}$, is given by $D_\mathrm{h} = \sqrt{S_{\mathrm{f}2}/\pi}$».
- **El problema:** $\sqrt{S/\pi}$ es el radio del círculo de área $S$; su
  diámetro es $\sqrt{4S/\pi} = 2\sqrt{S/\pi}$. Seguida tal como está
  impresa, la longitud «2 $D_\mathrm{h}$» que el apartado pide al conducto de
  impulsión es un diámetro equivalente, no dos, y si la regla pretendida son
  dos diámetros o dos radios no puede zanjarse desde el documento.
- **Evidencia:** página 33 del PDF (p. 23 impresa) de ISO 5136:2003.
- **Comportamiento de la biblioteca:** las longitudes de conducto de los
  apartados 5.2 y 7.4 son geometría de la instalación y no se calculan; nada
  que cambiar.
- **Estado:** sin notificar.

## ISO 5136:2003, Tabla A.2, cabecera de coeficientes (la columna $a_9$ se titula $a9_0$)

- **Ubicación:** Anexo A, Tabla A.2, «Values of coefficients $a_i$ for the
  determination of the combined mean flow velocity and modal correction
  $C_{3,4}$ of the sampling tube for duct diameters 0,2 m $\le d <$ 0,3 m»,
  la fila de cabecera de las columnas de coeficientes, décima columna.
- **El impreso:** una $a$ en cursiva, un 9 en cursiva sobre la línea base y
  un 0 como subíndice, entre un $a_8$ y un $a_{10}$ de la misma fila que sí
  llevan su índice como subíndice.
- **El problema:** un subíndice cero de más en una columna que es $a_9$. La
  misma columna se titula $a_9$ en las Tablas A.1 y A.3 a A.6, la NOTA de
  cada una de ellas suma $a_i U^i$ de $i = 0$ a $i = 10$ sobre las once
  columnas que tiene la fila, y la única celda que esta contiene, el
  $4{,}09 \times 10^{-14}$ de la fila de 20 000 Hz, es el coeficiente de
  $U^9$: un $a_{90}$ no tendría lugar alguno en esa suma.
- **Evidencia:** página 36 del PDF (p. 26 impresa) de ISO 5136:2003, frente a
  la fila de cabecera de la Tabla A.1 en la página 35 del PDF (p. 25
  impresa).
- **Comportamiento de la biblioteca:** la columna se lee como $a_9$.
  `_TABLE_A2` en
  [`sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py)
  lleva la fila de 20 000 Hz como los diez coeficientes $a_0$ a $a_9$, y
  `test_table_a2_20_khz_row_reads_the_last_column_as_a9` en
  [`tests/emission/test_sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_duct.py)
  desarrolla la fila. No cambia ningún valor de coeficiente.
- **Estado:** sin notificar (tipográfico, sin consecuencia numérica).

## ISO 5136:2003, Tabla A.6, fila de 16 000 Hz ($a_1$ impreso con el signo de multiplicación duplicado)

- **Ubicación:** Anexo A, Tabla A.6, «... for duct diameters 1,25 m $\le d
  \le$ 2 m», fila de 16 000 Hz, columna $a_1$.
- **El impreso:** $4{,}52 \times\!\times 10^{-01}$, dos signos de
  multiplicación donde todas las demás celdas imprimen uno.
- **El problema:** solo tipográfico; la mantisa y el exponente son legibles y
  el valor es $4{,}52 \times 10^{-1}$, en línea con el
  $4{,}51 \times 10^{-1}$ de la Tabla A.5 y el $4{,}52 \times 10^{-1}$ de la
  Tabla I.1 en la misma banda. La fila está en el rango informativo por
  encima de 10 kHz.
- **Evidencia:** página 40 del PDF (p. 30 impresa) de ISO 5136:2003.
- **Comportamiento de la biblioteca:** $4{,}52 \times 10^{-1}$ en
  `_TABLE_A6` de
  [`sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py).
- **Estado:** sin notificar (tipográfico, sin consecuencia numérica).

## ISO 5136:2003, Tabla I.2 (continuación), fila de 20 000 Hz (los exponentes de $a_8$ y $a_9$)

- **Ubicación:** Anexo I, Tabla I.2, «... for duct diameters 3,55 m $\le d
  \le$ 5 m», la página de continuación, fila de 20 000 Hz, columnas $a_8$ y
  $a_9$.
- **El impreso:** $a_8 = -5{,}88 \times 10^{-10}$ y
  $a_9 = 2{,}25 \times 10^{-10}$.
- **El problema:** a $U$ = 40 m/s el $a_9$ impreso aporta por sí solo
  $2{,}25 \times 10^{-10} \times 40^9 \approx 5{,}9 \times 10^4$ dB a
  $C_{3,4}$, cosa que ninguna corrección puede ser. La misma fila de las
  tablas vecinas imprime $a_8 = -5{,}90 \times 10^{-12}$ y
  $a_9 = 2{,}25 \times 10^{-13}$ (Tabla I.1) y
  $a_9 = 2{,}25 \times 10^{-13}$ (Tabla I.3), así que los exponentes son
  $-12$ y $-13$ y al impreso le faltan dos y tres décadas. El Anexo I es
  informativo y la fila está en el rango informativo por encima de 10 kHz.
- **Evidencia:** página 72 del PDF (p. 62 impresa) de ISO 5136:2003, frente
  a la misma fila de la Tabla I.1 en la página 70 del PDF (p. 60 impresa) y
  de la Tabla I.3 en la página 74 del PDF (p. 64 impresa).
- **Comportamiento de la biblioteca:** los Anexos informativos H e I quedan
  fuera del alcance que la norma se fija a sí misma (de 0,15 m a 2 m) y no se
  implementan; un conducto de más de 2 m se rechaza. Se registra para que
  una implementación del Anexo I no arrastre los exponentes tal como están
  impresos.
- **Estado:** sin notificar.

## ISO 4869-2:2018, Tabla C.1 (la reimpresión que contradice a la tabla que reimprime)

- **Ubicación:** anexo C (informativo), Tabla C.1, «A-weighted octave-band
  sound pressure levels, $L_{p,\mathrm{A}f(k)i}$, **from Table 2**», página 17
  del PDF (p. 11 impresa), frente a la Tabla 2 normativa que cita, página 11
  del PDF (p. 5 impresa).
- **El impreso:** las dos tablas traen los mismos ocho ruidos de referencia
  sobre las mismas siete bandas de octava, y siete de las ocho filas coinciden
  dígito a dígito. La sexta dice 82,0 / **89,3** / **93,3** / 95,6 / 93,0 /
  90,1 / 83,0 en la Tabla 2 y 82,0 / **89,4** / **93,5** / 95,6 / 93,0 / 90,1 /
  83,0 en la Tabla C.1. Difieren las celdas de 250 Hz y 500 Hz; ninguna más.
- **El problema:** la Tabla C.1 declara en su propio encabezado que procede de
  la Tabla 2, así que una de las dos está mal, y los resultados del propio
  anexo dicen cuál. La Fórmula (15) aplicada a los dieciséis valores de
  atenuación de la Tabla A.1 con la fila de la Tabla 2 reproduce exactos los
  dieciséis $PNR_{j6}$ de la Tabla C.2; con la fila de la Tabla C.1, trece de
  los dieciséis se quedan 0,1 dB cortos. La Tabla 2 es, por tanto, la lectura
  con la que se calculó el ejemplo, y además es la normativa, siendo la
  Tabla C.1 una reimpresión informativa. Quien tome los espectros de
  referencia del anexo C, donde están junto al ejemplo trabajado, obtiene los
  valores $H$ y $M$ de un protector una décima de decibelio por debajo.
- **Evidencia:** Fórmula (15), página 11 del PDF (p. 5 impresa), evaluada
  sobre la Tabla A.1, página 15 del PDF (p. 9 impresa), contra la sexta fila
  de la Tabla C.2, página 18 del PDF (p. 12 impresa), todo ello de la
  ISO 4869-2:2018.
- **Comportamiento de la biblioteca:** `HML_REFERENCE_NOISES` lleva la
  Tabla 2. La suite de tests calcula esa misma fila con los valores de la
  Tabla C.1 y comprueba que falla trece de los dieciséis impresos, de modo que
  las dos lecturas no pueden intercambiarse en silencio.
- **Estado:** sin notificar.

## ISO 4869-6:2019, Tabla A.3 (las filas de incertidumbre salen de la fila redondeada de encima)

- **Ubicación:** anexo A (normativo), Tabla A.3 «An example of ANR earmuff
  active insertion loss test data in dB for a given laboratory», las filas
  «Combined standard uncertainty, $u$, ($\sigma/\sqrt{N}$)» y «Expanded
  uncertainty, $U_{95}$», página 16 del PDF (p. 10 impresa), frente a las
  definiciones de A.1 y A.2 de la página 14 del PDF (p. 8 impresa).
- **El impreso:** la tabla da la pérdida por inserción activa de dieciséis
  sujetos en las frecuencias de octava de 63 Hz a 8 kHz, y después su media, su
  desviación típica $\sigma$, $u$ y $U_{95}$. La fila de $u$ dice 0,5 / 0,2 /
  **0,4** / 0,5 / 0,4 / 0,4 / 0,4 / 0,2 dB y la de $U_{95}$ **1,0** / 0,4 /
  **0,8** / **1,0** / **0,8** / 0,8 / **0,8** / **0,4** dB. El apartado A.2
  define $u$ como «the standard deviation of the individual active insertion
  loss data divided by the square root of the number of test subjects, i.e.
  $\sqrt{16} = 4$», y A.1 define $U_{95}$ como $u$ multiplicada por el factor
  de cobertura $k = 2$. La tabla no lleva ninguna nota sobre cómo redondea.
- **El problema:** con las dieciséis filas impresas, la media y $\sigma$ se
  reproducen en las dieciséis celdas, pero $u$ en 250 Hz vale 0,348 dB, que se
  redondea a 0,3 y no a 0,4, y $U_{95} = 2\sigma/4$ vale 0,935 / 0,355 / 0,697 /
  0,940 / 0,711 / 0,839 / 0,720 / 0,325 dB, que se redondea a 0,9 / 0,4 / 0,7 /
  0,9 / 0,7 / 0,8 / 0,7 / 0,3: seis de las ocho celdas impresas quedan 0,1 dB
  por encima. Cada celda impresa es, en cambio, la fórmula aplicada a la fila
  **redondeada** de encima: $1{,}4 / 4 = 0{,}35$ se imprime 0,4, y cada
  $U_{95}$ es el doble de la $u$ impresa sobre ella. La misma tabla de la
  ISO 4869-1:2018 (su Tabla A.3, con la misma disposición) calcula con
  precisión completa y lo dice en su NOTA 2, «All calculations are made with
  full precision before rounding to one decimal», y sus 28 celdas derivadas se
  reproducen así. Quien aplique A.1 y A.2 a los datos impresos de la
  ISO 4869-6 obtiene una incertidumbre expandida una décima de decibelio por
  debajo de la impresa en seis bandas de ocho, y la página no le dice por qué.
- **Evidencia:** las dieciséis filas y las cuatro filas derivadas de la
  Tabla A.3, página 16 del PDF (p. 10 impresa), recalculadas con
  $u = \sigma/4$ y $U_{95} = 2u$ una vez con precisión completa y otra desde la
  $\sigma$ y la $u$ impresas; A.1 y A.2, página 14 del PDF (p. 8 impresa); todo
  ello de la ISO 4869-6:2019. Para el contraste, la Tabla A.3 de la
  ISO 4869-1:2018 y su NOTA 2, página 19 del PDF (p. 13 impresa).
- **Comportamiento de la biblioteca:** `hearing.active_insertion_loss`
  devuelve $u$ y $U_{95}$ con precisión completa a partir de los datos, como
  las definen A.1 y A.2. La fila de conformidad y
  `tests/hearing/test_active_noise_reduction.py` fijan las filas de la media y
  de $\sigma$ tal como están impresas, reproducen las de $u$ y $U_{95}$ del modo
  en que las forma la tabla y comprueban que la precisión completa difiere
  exactamente en las siete celdas citadas aquí, cada una en 0,1 dB.
- **Estado:** sin notificar.

## VDI 2081 Blatt 1:2001-07, apartado 6.4 (la columna inglesa dice lo contrario que la alemana)

- **Ubicación:** folio impreso 40 (página 40 del PDF), apartado 6.4
  "Verzweigungen" / "Junctions", la frase inmediatamente posterior a la
  ecuación (35).
- **Lo impreso:** la columna alemana dice "Diese in Bild 27 dargestellte Senkung
  des Schallleistungspegels ist **frequenzunabhängig**". La columna inglesa de
  la misma página, traduciendo esa misma frase, dice "This sound power level
  reduction shown in Figure 27 **depends on the frequency**".
- **El problema:** las dos dicen cosas opuestas, y la que manda es la alemana:
  la portada de toda directriz VDI declara que la versión alemana es la
  vinculante y que no se garantiza la traducción inglesa. La alemana es además
  la que concuerda con el resto del documento. La figura 27 de esa misma página
  representa $\Delta L_W$ frente al cociente de secciones
  $S_1 / \sum S_{1,2,3}$ y no tiene eje de frecuencia; la propia ecuación (35),
  $\Delta L_W = |10 \lg (S_1 / \sum_i S_i)|$, no contiene la frecuencia; y el
  ejemplo resuelto de VDI 2081 Blatt 2:2005-05 imprime la reducción de nivel de
  una ramificación como un único número y no como espectro de octava, en las
  tres que tiene (tabla 1, elementos 3, 7 y 16, folios impresos 13 y 15:
  $5{,}6$, $4{,}8$ y $3{,}0$ dB).
- **Mecanismo probable:** el prefijo negativo de "frequenzunabhängig" no está en
  la traducción, lo que convierte "independiente de la frecuencia" en su
  contrario. El resto de la frase no difiere.
- **Consecuencia:** quien trabaje sólo con la columna inglesa buscará una
  dependencia con la frecuencia que ni la ecuación ni la figura tienen, y puede
  concluir que la directriz está incompleta en vez de que la frase está mal
  traducida.
- **Evidencia:** las dos columnas de la misma página impresa leídas una contra
  otra; la figura 27 de esa página; la ecuación (35) que la precede; y las tres
  filas de ramificación del ejemplo resuelto del Blatt 2. Verificado en la
  página 40 del PDF (p. impresa 40) de VDI 2081 Blatt 1:2001-07 y en las páginas
  13 y 15 del PDF (pp. impresas 13 y 15) de VDI 2081 Blatt 2:2005-05.
- **Comportamiento de la biblioteca:**
  [`split_loss`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) con
  `model="vdi2081"` devuelve un solo valor para la ramificación, que es la
  lectura alemana, y reproduce las tres ramificaciones impresas del ejemplo.
- **Estado:** sin comunicar. Los dos impresos están sustituidos (Blatt 1:2022-04
  y Blatt 2:2022-10) y no se dispone de ninguno de los sucesores, así que aquí
  no consta si la traducción se corrigió.

## VDI 2081 Blatt 2:2005-05, tabla 1, elemento 14 (una fila del elemento contradice a la de encima)

- **Ubicación:** tabla 1, folio impreso 15 (página 15 del PDF), elemento 14, el
  codo de sección circular: las filas "$\Sigma L_\mathrm{W}$" y
  "$\Sigma L_\mathrm{W}$ (log)", celda de 8 kHz.
- **Lo impreso:** las dos filas dicen, de 63 Hz a 8 kHz, $68{,}5$ $61{,}7$
  $55{,}7$ $43{,}4$ $30{,}1$ $28{,}5$ $34{,}0$ $34$ y $68{,}5$ $61{,}7$ $55{,}7$
  $43{,}4$ $30{,}1$ $28{,}5$ $34{,}0$ $33{,}6$. Siete celdas coinciden y la
  octava no.
- **El problema:** la segunda fila es la primera con el ruido propio del
  elemento sumado, así que no puede quedar por debajo. El elemento 13 entrega
  los 8 kHz a $37{,}0$ dB, el codo atenúa $3$ dB y la primera fila imprime los
  $34{,}0$ dB que quedan. El ruido propio del codo en esa banda es $-14{,}4$ dB,
  que el mismo elemento imprime dos filas más arriba, y sumarlo mueve el nivel
  menos de $0{,}0001$ dB. La segunda fila debería imprimir $34{,}0$ dB e imprime
  $33{,}6$.

  Leído al revés la celda es igual de inalcanzable: para $33{,}6$ dB tendrían
  que llegar $36{,}6$ dB del elemento 13, y el elemento 13 imprime $37{,}0$ dB
  en su propia fila $\Sigma L_\mathrm{W}$ de esa misma página.
- **Consecuencia:** $0{,}4$ dB en 8 kHz, que se arrastran al elemento 15 y a
  todo lo que viene detrás. El total ponderado A del elemento se imprime como
  $50{,}9$ dB en las dos filas, y eso es lo que lo tapa: en 8 kHz la ponderación
  A vale $-1{,}1$ dB y la banda está $16$ dB por debajo de la de 4 kHz, así que
  $0{,}4$ dB ahí no llegan al primer decimal del total.
- **Evidencia:** las dos filas del elemento 14 y la fila $\Sigma L_\mathrm{W}$
  del elemento 13, con la suma recalculada a precisión completa a partir del
  traspaso, la atenuación y el ruido impresos. Verificado en la página 15 del
  PDF (folio impreso 15) de VDI 2081 Blatt 2:2005-05.
- **Comportamiento de la biblioteca:** las filas de conformidad del elemento 14
  comparan el ruido de flujo que hace el codo, de $26{,}9$ a $-14{,}4$ dB, con
  la fila que lo imprime, y la fila de la cadena lleva los $34{,}0$ dB que da la
  aritmética y no los $33{,}6$ impresos.
- **Estado:** no reportada. La edición está superada y no tenemos la sucesora.

## VDI 2081 Blatt 2:2005-05, tabla 1, elemento 2 (el diámetro hidráulico que imprime no es con el que calcula)

- **Ubicación:** tabla 1, folio impreso 12 (página 12 del PDF), elemento 2, el
  silenciador de láminas: las filas "Hydr. Durchmesser $d_\mathrm{h}$ (m)" y
  "Strouhalzahl $St$".
- **Lo impreso:** $d_\mathrm{h} = 0{,}171$ m, y los ocho números de Strouhal
  $0{,}9$, $1{,}7$, $3{,}4$, $6{,}8$, $13{,}5$, $27{,}0$, $54{,}0$ y $108{,}0$
  en las octavas de 63 Hz a 8 kHz, para una ranura libre $s = 0{,}100$ m, una
  altura de lámina $H = 0{,}600$ m y una velocidad de ranura $v = 14{,}81$ m/s.
- **El problema:** las dos filas se contradicen. El apartado 7.2.4.2 del
  Blatt 1 define $St = f_\mathrm{m} d_\mathrm{h} / v_\mathrm{i}$, así que el
  $d_\mathrm{h}$ impreso y el $St$ impreso se determinan mutuamente. Con los
  $0{,}171$ m impresos los ocho números serían $0{,}73$, $1{,}45$, $2{,}89$,
  $5{,}79$, $11{,}57$, $23{,}15$, $46{,}29$ y $92{,}59$: ninguno redondea sobre
  la fila impresa. Con $d_\mathrm{h} = 2s = 0{,}200$ m salen $0{,}851$,
  $1{,}688$, $3{,}376$, $6{,}752$, $13{,}504$, $27{,}009$, $54{,}018$ y
  $108{,}035$, que redondean sobre los ocho.

  Los dos valores son defendibles como diámetro hidráulico, y por eso esto es
  una incoherencia interna y no un número mal puesto: $4A/P$ de una ranura de
  $0{,}100$ m por $0{,}600$ m vale $0{,}171$ m, mientras que el límite de
  placas paralelas al que tiende una ranura larga y estrecha es
  $2s = 0{,}200$ m. La tabla imprime el primero y calcula con el segundo.
- **Consecuencia:** seguir el $d_\mathrm{h}$ impreso no reproduce ni la fila de
  Strouhal ni el espectro de ruido que va debajo. Con $2s$ el elemento entero
  sale hasta el último decimal impreso: $L_\mathrm{WA} = 52$ dB por la
  ecuación (49) y los ocho niveles de octava de $62{,}7$ a $35{,}6$ dB por las
  ecuaciones (46), (50) y (51), el peor de ellos a 0,046 dB de su celda.
- **Evidencia:** las dos filas del mismo elemento impreso leídas contra el
  apartado 7.2.4.2 del Blatt 1 (folio impreso 53); los dos diámetros candidatos
  evaluados en las ocho octavas; y el espectro de ruido recalculado con cada
  uno. Verificado en la página 12 del PDF (p. impresa 12) de VDI 2081
  Blatt 2:2005-05 y en la página 53 del PDF (p. impresa 53) de VDI 2081
  Blatt 1:2001-07.
- **Comportamiento de la biblioteca:**
  [`silencer_self_noise`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) con
  `model="vdi2081"` toma la ranura libre y usa $2s$, así que reproduce el
  ejemplo resuelto. El docstring dice cuál de los dos toma.
- **Estado:** sin comunicar. Los dos impresos están sustituidos y no se dispone
  de ninguno de los sucesores.

## VDI 2081 Blatt 2:2005-05, tabla 1, elemento 2 (una referencia cruzada al apartado equivocado)

- **Ubicación:** tabla 1, folio impreso 12 (página 12 del PDF), elemento 2, el
  recuadro que dice "Tabelle aus VDI 2081 Blatt 1/7.3.2" junto a los
  coeficientes $a_1$, $a_2$, $b_1$ y $b_2$.
- **Lo impreso:** los coeficientes $0{,}255$, $0{,}015$, $-2{,}82$ y $-2{,}91$
  se atribuyen al apartado 7.3.2 del Blatt 1.
- **El problema:** el apartado 7.3 de VDI 2081 Blatt 1:2001-07 es
  "Luftschalldämmung eines Bauteils", el aislamiento a ruido aéreo de un
  elemento constructivo, y no tiene tal tabla. Los coeficientes están impresos
  en el apartado **7.2.3.2**, "Kulissenschalldämpfer", en el folio impreso 52,
  cuya tabla da exactamente esos cuatro valores en la fila de 200 mm, que es el
  espesor de lámina del elemento.
- **Consecuencia:** quien siga la referencia aterriza en otro capítulo. Los
  valores en sí son correctos.
- **Evidencia:** el apartado citado y el real, leídos los dos de las páginas
  impresas. Verificado en la página 12 del PDF (p. impresa 12) de VDI 2081
  Blatt 2:2005-05 y en la página 52 del PDF (p. impresa 52) de VDI 2081
  Blatt 1:2001-07.
- **Comportamiento de la biblioteca:** ninguno; la biblioteca cita el apartado
  7.2.3.2.
- **Estado:** sin comunicar.

## ISO 11200:2014, anexo B (los dos casos calculan la misma desviación típica de dos maneras distintas)

- **Ubicación:** anexo B, tabla B.1 en el folio impreso 27 (página 33 del PDF) y
  tabla B.3 en el folio impreso 30 (página 36 del PDF). Las dos llevan una fila
  rotulada igual, «Standard deviation of the three values measured,
  $\sigma_{omc}$».
- **Lo impreso:** la tabla B.1 lista las tres lecturas 94,5 dB; 94,3 dB;
  93,8 dB y da $\sigma_{omc} = 0{,}3$ dB. La tabla B.3 lista 79,0 dB; 80,2 dB;
  82,9 dB y da $\sigma_{omc} = 2$ dB.
- **El problema:** usan estimadores distintos. La Ecuación (C.1), impresa
  idéntica en ISO 11201:2010, ISO 11202:2010 e ISO 11204:2010, es la desviación
  típica **muestral**,

  $$
  \sigma_\mathrm{omc} = \sqrt{\frac{1}{N-1}
  \sum_{j=1}^{N} \left( L'_{p,j} - \overline{L'_p} \right)^2}
  $$

  Con $1/(N-1)$ la primera terna da 0,3606 dB, que redondea a **0,4** y no a
  los 0,3 que imprime la tabla; la segunda da 1,9975 dB, que redondea al
  **2,0** que sí imprime. Con $1/N$ la primera da 0,2944 → **0,3**, el valor
  impreso, y la segunda 1,6310 → 1,6, que no está impreso. La tabla B.1 divide
  por tanto entre $N$ y la B.3 entre $N-1$, en el mismo anexo, bajo el mismo
  rótulo y para la misma magnitud.
- **Consecuencia:** no es cosmético, porque el valor se propaga. La tabla B.1
  sigue imprimiendo $\sigma_\mathrm{tot} = 1{,}5$ dB y $U = 2{,}4$ dB a partir
  de $\sigma_{R0} = 1{,}5$ dB. Con los 0,4 dB que da la Ecuación (C.1),
  $\sigma_\mathrm{tot} = \sqrt{1{,}5^2 + 0{,}4^2} = 1{,}552 \to 1{,}6$ dB y
  $U = 1{,}6 \times 1{,}552 = 2{,}48 \to 2{,}5$ dB, porque el factor de
  cobertura se aplica al total sin redondear y no al decibelio con que se
  informa. Quien reproduzca el ejemplo desde las ecuaciones no obtiene la
  incertidumbre que el ejemplo publica.
- **Mecanismo probable:** tres lecturas son la muestra más pequeña que la
  ecuación admite, y es justo donde los dos divisores más se separan:
  $\sqrt{3/2}$ es un 22 % de diferencia. La función de desviación típica
  poblacional de una hoja de cálculo toma $1/N$ por defecto, y con tres puntos
  el desliz basta para cambiar el decibelio redondeado.
- **Evidencia:** las dos tablas leídas en la página impresa, no en el texto
  extraído. Verificado en las páginas 33 y 36 del PDF (folios impresos 27 y 30)
  de ISO 11200:2014, contra la Ecuación (C.1) en la página 32 del PDF (folio
  impreso 26) de ISO 11201:2010.
- **Comportamiento de la biblioteca:**
  [`operating_standard_deviation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/workstation.py)
  implementa la Ecuación (C.1) tal como se imprime, con $1/(N-1)$. Reproduce la
  tabla B.3 y deliberadamente no reproduce los 0,3 dB de la tabla B.1;
  `tests/emission/test_workstation.py` fija las dos mitades para que la
  elección no se mueva.
- **Estado:** sin comunicar.

## ISO 3382-1:2009, A.2.1 (el mismo símbolo nombra dos niveles distintos, con una página de por medio)

- **Ubicación:** anexo A (informativo), A.2.1. La lista «where» bajo las
  Ecuaciones (A.2) y (A.3) en el folio impreso 13 (página 21 del PDF), y la
  lista «where» bajo la Ecuación (A.5) en el folio impreso 14 (página 22 del
  PDF).
- **Lo impreso:** el folio 13 dice «$L_{pE}$ is the sound pressure exposure
  level of $p(t)$», siendo $p(t)$ «the instantaneous sound pressure of the
  impulse response measured at the measurement point», es decir, el receptor de
  la sala bajo ensayo. El folio 14, dentro de la NOTA 1, dice «$L_{pE}$ is the
  spatial-average sound pressure exposure level measured in the reverberation
  room».
- **El problema:** un símbolo, dos magnitudes, el mismo apartado, sin
  subíndice que las distinga y sin nota que avise de la reutilización. La
  segunda es una calibración de la fuente en laboratorio; la primera es la
  medición para la que existe todo el anexo.
- **Consecuencia:** sustituir la (A.5) en la (A.1) tal como están impresos los
  símbolos da

  $$
  G = L_{pE} - L_{pE,10} = L_{pE} - \left[ L_{pE} + 10 \lg (A/S_0) - 37 \right]
    = 37 - 10 \lg (A/S_0)\ \text{dB},
  $$

  donde la sala ha desaparecido y la fuerza sonora depende sólo del área de
  absorción de la cámara reverberante en que se calibró la fuente. La
  sustitución es la que invitan los símbolos impresos, y no tiene sentido.
- **Evidencia:** verificado en las páginas 21 y 22 del PDF (folios impresos 13
  y 14) de BS EN ISO 3382-1:2009.
- **Comportamiento de la biblioteca:**
  [`reverberation_room_reference_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py)
  llama a su argumento `reverberation_room_level`, y el nivel de la sala nunca
  llega hasta él: lo mide
  [`sound_strength`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) a partir de la
  respuesta que se pasa como `ir`. Nada impide que quien llama escriba la
  sustitución a mano, pero ninguna variable hace los dos papeles, y los dos
  nombres dicen cuál es cuál.
- **Estado:** sin comunicar.

## ISO 3382-1:2009, A.2.1 (un barrido de directividad «cada 12,5 grados» que no cierra la circunferencia)

- **Ubicación:** anexo A (informativo), A.2.1, la nota inmediatamente bajo la
  Ecuación (A.4), folio impreso 13 (página 21 del PDF).
- **Lo impreso:** «When making such a measurement in a free field, it is
  necessary to make the measurement at every 12,5° around the sound source and
  to calculate the energy-mean value of the sound pressure exposure levels in
  order to average the directivity of the sound source.»
- **El problema:** $360 / 12{,}5 = 28{,}8$. No hay número entero de pasos de
  12,5° que cierre una vuelta: 28 pasos llegan a 350° y dejan un hueco de 10°,
  29 se pasan hasta 362,5°. La instrucción no puede seguirse literalmente.
- **Consecuencia:** dos laboratorios que «midan cada 12,5°» pueden usar
  conjuntos de acimuts distintos y, para una fuente en el límite de
  directividad de la tabla 1 (±6 dB a 4 kHz), sus medias energéticas difieren.
  El nivel de referencia $L_{pE,10}$ al que llevan todas las rutas de A.2.1 no
  es, por tanto, reproducible sólo desde la instrucción impresa. El barrido de
  cualificación de la fuente de la propia norma, en 4.2.1, usa 5°, que divide
  360 exactamente en 72.
- **Evidencia:** verificado en la página 21 del PDF (folio impreso 13) de
  BS EN ISO 3382-1:2009.
- **Comportamiento de la biblioteca:**
  [`directivity_energy_average`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) toma la
  lectura que la nota sí sostiene: un muestreo uniforme de la vuelta completa
  no más grueso que el paso impreso, es decir al menos
  $\lceil 360 / 12{,}5 \rceil = 29$ acimuts, combinados con la media energética
  que la nota pide. Menos acimuts levantan `ValueError` en lugar de promediar
  una vuelta que nunca se cerró.
- **Estado:** sin comunicar.

## ISO 3382-1:2009, C.2.1 y C.2.2 (la prosa de los dos soportes de escenario se deja un límite de integración)

- **Ubicación:** anexo C (informativo), C.2.1 en el folio impreso 23 (página
  31 del PDF) y C.2.2 en el folio impreso 24 (página 32 del PDF), cada uno en
  la frase que presenta su propia ecuación.
- **Lo impreso:** C.2.1 define el soporte temprano como «the ratio, in
  decibels, of the reflected energy **within the first 0,1 s** relative to
  the direct sound», e imprime

  $$
  ST_\mathrm{Early} = 10 \lg \left[
      \frac{\int_{0,020}^{0,100} p^2(t)\ \mathrm{d}t}
           {\int_{0}^{0,010} p^2(t)\ \mathrm{d}t} \right]\ \mathrm{dB}.
  $$

  C.2.2 define el soporte tardío como «the ratio, in decibels, of the
  reflected energy **after the first 0,1 s** relative to the direct sound», e
  imprime

  $$
  ST_\mathrm{Late} = 10 \lg \left[
      \frac{\int_{0,100}^{1,000} p^2(t)\ \mathrm{d}t}
           {\int_{0}^{0,010} p^2(t)\ \mathrm{d}t} \right]\ \mathrm{dB}.
  $$

- **El problema:** ninguna de las dos frases describe la ecuación que tiene
  al lado. La Ecuación (C.1) empieza en 0,020 s, no en los 0,010 s donde
  termina la ventana del sonido directo, así que el intervalo entre ambos no
  cuenta ni en el numerador ni en el denominador y la prosa no menciona el
  hueco. La Ecuación (C.2) se detiene en 1,000 s, donde la prosa no pone
  ningún límite superior.
- **Consecuencia:** las dos mueven un número, y la primera lo mueve más. En
  un decaimiento exponencial de $T = 2$ s, quien entienda «within the first
  0,1 s» como que empieza donde acaba la ventana del sonido directo recoge
  además el intervalo de 10 ms a 20 ms, que es un 17 % más de energía y
  **0,68 dB** en $ST_\mathrm{Early}$, frente a la desviación típica de 1 dB
  que C.2.4 estima para una sola lectura. El techo que le falta a la (C.2)
  cuesta 0,01 dB en esa misma sala, porque un decaimiento de 2 s ya ha caído
  30 dB al segundo, y llega a 0,2 dB con $T = 4$ s y a 1,0 dB con $T = 8$ s:
  es la catedral, y no la sala de conciertos, lo que separa esa segunda
  omisión.
- **Evidencia:** verificado en las páginas 31 y 32 del PDF (folios impresos
  23 y 24) de BS EN ISO 3382-1:2009.
- **Comportamiento de la biblioteca:**
  [`stage_support`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) integra los límites
  impresos, que son los de
  [`EARLY_SUPPORT_WINDOW_S`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) y
  `LATE_SUPPORT_WINDOW_S`. `tests/room/test_auditorium_stage.py` deja caer una
  llegada en el hueco y otra pasado el techo y exige que ninguna cambie nada.
- **Estado:** sin comunicar.

## ISO 3382-1:2009, Tabla 1 y A.4 (los mismos límites son máximos en un apartado y mínimos en el otro)

- **Ubicación:** el título de la Tabla 1 y el párrafo de 4.2.1 que la
  precede, folio impreso 3 (página 11 del PDF), frente al cuarto párrafo de
  A.4, folio impreso 19 (página 27 del PDF).
- **Lo impreso:** 4.2.1 dice «Table 1 lists the **maximum** acceptable
  deviations from omnidirectionality when averaged over "gliding" 30° arcs in
  a free sound field», y el título de la propia tabla reza «Table 1 —
  **Maximum** deviation of directivity of source in decibels for excitation
  with octave bands of pink noise and measured in free field». A.4 dice «If
  the source directivity is close to the **minimum** limits given in Table 1,
  the measurement should be repeated with the source turned in at least three
  steps totally».
- **El problema:** una tabla, dos palabras opuestas para lo que son sus
  números. Los valores son techos, como dicen su propio título y 4.2.1, y A.4
  los llama suelos.
- **Consecuencia:** la frase de A.4 es la que le dice a un laboratorio cuándo
  hacer trabajo de más, y leída tal cual dice lo contrario de lo que quiere
  decir. Una fuente «close to the minimum limits» sería una casi perfecta, que
  es justo el caso que no necesita repetición ninguna; lo que pide A.4 es
  repetir el barrido de una fuente que apenas pasa el techo, porque ahí es
  donde la orientación de la fuente empieza a importarle a la respuesta. Quien
  tome la palabra al pie de la letra repite la medición con las fuentes
  equivocadas y se la salta con las que la necesitan.
- **Evidencia:** verificado en las páginas 11 y 27 del PDF (folios impresos 3
  y 19) de BS EN ISO 3382-1:2009.
- **Comportamiento de la biblioteca:**
  [`MAX_SOURCE_DIRECTIVITY_DEVIATION_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py)
  y [`source_directivity_limit`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) los
  llevan como los máximos que su propio título hace de ellos. La repetición
  con tres orientaciones de A.4 es un procedimiento, no un cálculo, y la
  biblioteca no lo implementa.
- **Estado:** sin comunicar.

## ISO 3382-1:2009, 4.2.1 (un promedio deslizante cuya ventana no tiene fase declarada)

- **Ubicación:** 4.2.1, el párrafo inmediatamente anterior a la Tabla 1, folio
  impreso 3 (página 11 del PDF).
- **Lo impreso:** «Table 1 lists the maximum acceptable deviations from
  omnidirectionality when averaged over "gliding" 30° arcs in a free sound
  field. In case a turntable cannot be used, measurements per 5° should be
  performed, followed by "gliding" averages, each covering six neighbouring
  points.»
- **El problema:** seis puntos de 5° cubren 30° de arco leídos como seis
  sectores, y 25° leídos como la distancia entre el primero y el último, así
  que las dos frases sólo concuerdan con la lectura por sectores. Y, sobre
  todo, nada dice dónde se sitúan esos seis puntos respecto del arco que
  promedian: la ventana puede adelantarse a su acimut, retrasarse o quedar
  centrada, y el apartado no elige. Tampoco dice cómo se combinan los seis,
  aunque la referencia con la que se comparan sea explícitamente «a 360°
  energetic average».
- **Consecuencia:** en una vuelta completa las ventanas de seis puntos son un
  mismo conjunto cíclico se ancle la ventana por donde se ancle, así que la
  fase desplaza hasta media ventana, 15° del patrón, la orientación con la
  que se reporta cada desviación, y deja las desviaciones intactas. En una
  fuente cercana a su límite de la Tabla 1 eso sigue decidiendo si la
  desviación máxima se reporta sobre un lóbulo o entre dos, que es la
  orientación que la A.4 pide luego girar y volver a medir. Los otros dos
  silencios sí mueven el número: la lectura del span y la ley de combinación
  cambian lo que promedia cada arco, así que dos laboratorios que sigan los
  dos el apartado pueden dar desviaciones máximas distintas para una misma
  fuente, y la norma no da forma de saber cuál de los dos la leyó bien.
- **Evidencia:** verificado en la página 11 del PDF (folio impreso 3) de
  BS EN ISO 3382-1:2009.
- **Comportamiento de la biblioteca:**
  [`gliding_directivity_deviation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/auditorium.py) toma
  la lectura por sectores, promedia los arcos energéticamente igual que la
  referencia, y empieza cada ventana en el acimut contra el que se reporta,
  dando la vuelta al círculo. Su docstring dice que las tres son elecciones.
- **Estado:** sin comunicar.

## IEC 60534-8-3:2010, anexo A (el factor geométrico de tubería se imprime redondeado, y el anexo no calculó con el valor redondeado)

- **Ubicación:** anexo A (informativo), A.2, el bloque «Given data» del folio
  impreso 32 (página 34 del PDF) de BS EN 60534-8-3:2011, frente a la fila de
  la Ecuación (2) de la Tabla A.1 en ese mismo folio.
- **Lo impreso:** los datos de partida dicen «Piping geometry factor:
  $F_\mathrm{p} = 0{,}98$», bajo el encabezado «The following values are used
  in, or determined from, calculations based on IEC 60534-2-1». La Tabla A.1
  imprime luego $p_{vc} = 567\,787$ Pa para el ejemplo 1, y cinco valores más
  para las demás columnas, a partir de
  $p_{vc} = p_1\left[1 - x/(F_{LP}/F_P)^2\right]$ con $F_{LP} = 0{,}792$.
- **El problema:** las dos cosas no pueden ser ciertas a la vez. Despejar
  $(F_{LP}/F_P)^2$ de la Ecuación (2) en cada pareja impresa da 0,647 829,
  0,647 827, 0,647 821, 0,647 829 y 0,647 833 en las cinco columnas que
  imprimen valor, que es $F_p = 0{,}984$ con cuatro cifras en todas ellas. Con
  el 0,98 impreso sale 0,653 128 y $p_{vc} = 571\,294$ Pa, a 3 507 Pa de la
  cifra impresa. El valor es calculado, no un dato: el propio anexo dice que
  viene de la IEC 60534-2-1, y con el coeficiente de pérdida de carga que
  imprime, $\Sigma\zeta = 0{,}86$, sale $F_p = 0{,}984$ para el caso DN 100.
  Es decir, el anexo calculó con tres decimales e imprimió dos.
- **Consecuencia:** se mueve todo lo que viene después. Con el 0,98 impreso
  las cuatro fronteras de régimen salen $x_C = 0{,}287$, $\alpha = 0{,}786$ y
  $x_B = 0{,}578$ frente a los 0,285, 0,784 y 0,576 impresos, y la potencia
  acústica del ejemplo 1 sale 21,9 W frente a los 22,3 W impresos. Nada queda
  muy lejos, y nada reproduce: quien contraste su implementación con el anexo
  A usando el número que el anexo A imprime no cuadra ni una fila.
- **Evidencia:** los datos de partida y los seis valores de $p_{vc}$ leídos de
  la página impresa. Verificado en las páginas 33 y 34 del PDF (pp. impresas 31
  y 32) de BS EN 60534-8-3:2011.
- **Comportamiento de la biblioteca:**
  [`valve_aerodynamic_noise`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves.py) toma
  el cociente como argumento y no guarda ningún valor propio; las filas de
  conformidad y `tests/noise_control/test_valves.py` pasan $0{,}792/0{,}984$ y
  dicen por qué en el fixture.
- **Estado:** sin comunicar.

## IEC 60534-8-3:2010, Tabla A.1 (un diámetro de orificio equivalente diez veces menor, desmentido por la fila de debajo)

- **Ubicación:** anexo A (informativo), Tabla A.1, la fila de la Ecuación (8c)
  del folio impreso 33 (página 35 del PDF), frente a la fila de la Ecuación
  (8a) impresa justo debajo.
- **Lo impreso:** las seis columnas de la fila (8c) dicen $d_0 = 0.010$ m. Los
  datos de partida del folio 31 dan $N_\mathrm{O} = 6$ aberturas de jaula y
  $A = 0{,}00137$ m² para una de ellas, y la Ecuación (8c) es
  $d_o = \sqrt{4 N_o A/\pi}$.
- **El problema:** $\sqrt{4 \times 6 \times 0{,}00137/\pi} = 0{,}102$ m, no
  0,010 m. Los dos numerales son las mismas tres cifras en otro orden. La fila
  de debajo resuelve cuál es: la Ecuación (8a) es $F_d = d_H/d_o$, la fila
  (8b) imprime $d_H = 0{,}030$ m y la fila (8a) imprime $F_d = 0{,}30$ en las
  seis columnas. 0,030/0,102 es 0,30; 0,030/0,010 es 3,0.
- **Consecuencia:** quien tome el $d_o$ impreso obtiene un modificador de
  estilo de válvula de 3,0, un diámetro de chorro diez veces mayor por la
  Ecuación (9) y una frecuencia de pico diez veces menor, lo que desplaza el
  espectro interno de la Ecuación (19) más de tres octavas. El resto de la
  tabla está calculado con 0,102 m, así que el error se queda en esa celda.
- **Evidencia:** las filas (8b), (8c) y (8a) leídas de la página impresa.
  Verificado en las páginas 33 y 35 del PDF (pp. impresas 31 y 33) de
  BS EN 60534-8-3:2011.
- **Comportamiento de la biblioteca:**
  [`valve_style_modifier`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves.py)
  implementa (8b) y (8c) tal como están impresas y devuelve 0,296 para la
  jaula del anexo, que redondea al $F_d$ impreso; el test que lleva el nombre
  de esta entrada fija las dos lecturas para que el $d_o$ impreso no vuelva.
- **Estado:** sin comunicar.

## IEC 60534-8-3:2010, Tabla A.2 (dos factores de frecuencia con el exponente equivocado en una potencia de diez)

- **Ubicación:** anexo A (informativo), A.3, la columna $G_x$ de la Tabla A.2
  del folio impreso 43 (página 45 del PDF), bandas 5 y 10 de 33.
- **Lo impreso:** la columna va $G_{x,4} = 5.6 \times 10^{-9}$,
  $G_{x,5} = 1.4 \times 10^{-9}$, $G_{x,6} = 3.6 \times 10^{-8}$, y más abajo
  $G_{x,9} = 5.8 \times 10^{-7}$, $G_{x,10} = 1.4 \times 10^{-7}$,
  $G_{x,11} = 3.5 \times 10^{-6}$.
- **El problema:** por debajo de la frecuencia de coincidencia interna la
  Tabla 6 hace $G_x$ proporcional a $f_i^4$, así que la columna tiene que
  crecer de forma monótona, y lo hace en todas las bandas menos en esas dos,
  donde baja. Recalcular la Tabla 6 para esta tubería da
  $1{,}4 \times 10^{-8}$ en la banda 5 y $1{,}4 \times 10^{-6}$ en la 10: la
  mantisa está bien en las dos y el exponente es una unidad menor.
- **Consecuencia:** ninguna para el resto del anexo, y eso es lo que lo
  resuelve. Las pérdidas por transmisión impresas dos filas más abajo,
  $TL_5 = -86{,}1$ dB y $TL_{10} = -76{,}2$ dB, son las que da la Ecuación
  (20a) con los factores corregidos; con los impresos saldrían $-96{,}1$ dB y
  $-86{,}3$ dB. La Tabla A.2 calculó con los buenos e imprimió los malos, y
  quien monte un oráculo sólo con la columna $G_x$ hereda un error de 10 dB en
  dos bandas.
- **Evidencia:** la columna $G_x$ leída de la página impresa. Verificado en las
  páginas 45 y 46 del PDF (pp. impresas 43 y 44) de BS EN 60534-8-3:2011; las
  24 pérdidas por transmisión impresas en la segunda son las que la biblioteca
  reproduce con menos de 0,07 dB de diferencia.
- **Comportamiento de la biblioteca:**
  [`pipe_transmission_loss`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves.py)
  calcula $G_x$ a partir de la Tabla 6, y la fila de conformidad «Pipe
  transmission loss, example 7, 24 bands» reproduce todas las pérdidas
  impresas, cosa que los $G_x$ impresos no permitirían.
- **Estado:** sin comunicar.

## IEC 60534-8-4:2005, Ecuación (12) (el número de Strouhal se imprime de una forma en la cláusula y de otra en el anexo)

- **Ubicación:** apartado 5.1, Ecuación (12) del folio impreso 11 (página 13
  del PDF) de BS EN 60534-8-4:2005, contra esa misma ecuación reescrita en la
  fila (12) de la Tabla A.1 del folio impreso 23 (página 25 del PDF).
- **Lo impreso:** la cláusula imprime
  $N_{STR} = \dfrac{0{,}02\,F_L^2\,C}{N_{34}\,x_{Fzp1}^{1,5}\,d\,d_0}
  \left(\dfrac{1}{p_1-p_v}\right)^{0,57}$ y el anexo imprime
  $N_{STR} = \dfrac{0{,}036\,F_L^2\,C\,F_d^{\,0,75}}
  {N_{34}\,x_{Fzp1}^{1,5}\,d\,d_0}
  \left(\dfrac{1}{p_1-p_v}\right)^{0,57}$.
- **El problema:** son dos funciones distintas de la válvula, no dos redondeos
  de una. El anexo lleva un factor $F_d^{0,75}$ que la cláusula no tiene, y una
  constante 1,8 veces mayor. Los exponentes 0,57 y 1,5, el cuadrado de $F_L$ y
  el producto $d\,d_o$ son idénticos en las dos, así que la diferencia está
  toda en el numerador. Los propios números del anexo resuelven cuál evaluó:
  con $C_v = 90$, $F_d = 0{,}42$, $F_L = 0{,}92$, $N_{34} = 1{,}17$,
  $x_{Fzp1} = 0{,}2386$, $d = d_o = 0{,}1$ m y $p_1 - p_v = 997\,680$ Pa, la
  forma del anexo da 0,399 y la de la cláusula 0,425, y la Tabla A.1 imprime
  $N_{Str} = 0{,}399$ en dos de sus tres columnas y 0,243 en la tercera, que
  son la forma del anexo con tres cifras.
- **Consecuencia:** la frecuencia de pico de la Ecuación (11), y con ella todo
  el espectro por bandas del 5.4 y la pérdida por transmisión de la Ecuación
  (16b), que se evalúa en esa frecuencia. Para la válvula del anexo A las dos
  formas se separan un 6 %; para una válvula de un solo orificio con
  $F_d = 1$ la del anexo queda un 80 % por encima de la de la cláusula, cinco
  sextos de octava en la frecuencia de pico. Quien siga la cláusula normativa
  no reproduce ni una sola fila dependiente de la frecuencia del anexo
  informativo.
- **Evidencia:** las dos impresiones tal como aparecen en la página.
  Verificado en la página 13 del PDF (p. impresa 11) y en la página 25 del PDF
  (p. impresa 23) de BS EN 60534-8-4:2005.
- **Comportamiento de la biblioteca:**
  [`jet_strouhal_number`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  admite un argumento ``form`` e implementa las dos. Por defecto va
  ``"annex"``, la forma que reproduce los ejemplos impresos, y la fila de
  conformidad «Strouhal number and turbulent peak (Eqs. (11), (12))» la fija;
  un test con el nombre de esta entrada fija la razón entre ambas.
- **Estado:** sin comunicar.

## IEC 60534-8-4:2005, Tabla A.1 (una pérdida por transmisión por bandas impresa sin su signo menos)

- **Ubicación:** anexo A (informativo), Tabla A.1, la fila de la Ecuación (22a)
  del folio impreso 25 (página 27 del PDF), las tres columnas.
- **Lo impreso:** las tres celdas ponen «TL (8 000 Hz) = 51,76 dB», sin signo
  delante del 5.
- **El problema:** la Ecuación (22a) es $TL(f_i) = TL_{fr} + \Delta TL(f_i)$, y
  la tabla imprime sus dos entradas una fila más arriba y dos folios antes:
  $\Delta TL(8\,000\ \text{Hz}) = -7{,}053$ dB en la fila (22b) de la misma
  página y $TL_{fr} = -44{,}71$ dB en la fila (15) del folio impreso 23. Su
  suma es $-51{,}763$ dB. La fila de abajo también lo resuelve: la Ecuación
  (21) con $L_{pi}(8\,000\ \text{Hz}) = 116{,}3$ dB y los 12,67 dB del
  término geométrico da 51,87 dB contra los 51,8 impresos de $L_{pe,1m}$, y
  con los 116,252 dB sin redondear de la cadena da 51,82; con $+51{,}76$
  daría 155,4 dB.
- **Consecuencia:** ninguna para el anexo, que calculó con el signo bueno e
  imprimió el malo, y 103 dB para quien monte un oráculo con esa celda. Todas
  las demás pérdidas por transmisión de este documento van impresas negativas
  ($-44{,}71$; $-29{,}56$; $-74{,}27$; $-62{,}917$; $-75{,}006$; $-7{,}053$),
  incluida la que está justo encima.
- **Evidencia:** las tres celdas (22a) y las celdas (22b) de encima, leídas en
  la página impresa. Verificado en la página 27 del PDF (p. impresa 25) de
  BS EN 60534-8-4:2005: no hay guion, ni menos, ni raya delante de ninguna de
  las tres, y las celdas (22b) del mismo recorte sí llevan el suyo.
- **Comportamiento de la biblioteca:**
  [`transmission_loss_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  y el ``band_transmission_loss`` de ``valve_hydrodynamic_noise`` devuelven
  $-51{,}76$ dB en esa banda, que es lo que fija la fila de conformidad
  «Frequency route at 8 kHz, examples 1 to 3 (Eqs. (19) to (22))» junto con
  los niveles exteriores que el valor negativo reproduce.
- **Estado:** sin comunicar.

## IEC 60534-8-4:2005, 6.3.2 b) (una fórmula de diámetro de asiento cuya constante no está en la unidad en que se declara su símbolo)

- **Ubicación:** apartado 6.3.2, ítem b), la fórmula destacada sin numerar del
  folio impreso 15 (página 17 del PDF), contra la tabla de símbolos del
  apartado 3 del folio impreso 6 (página 8 del PDF).
- **Lo impreso:** «$d_o = 5{,}2\sqrt{N_{34}\,C_n}$», sin número de ecuación y
  sin unidad en la constante. La tabla de símbolos declara $d_o$ «Seat or
  orifice diameter», unidad **m**.
- **El problema:** las dos cosas no pueden ser. Para la última etapa de
  cualquier interno multietapa real la fórmula devuelve decenas: $C_n = 90$
  como $C_v$, con $N_{34} = 1{,}17$, da 53,4, y un asiento de 53 m no es una
  válvula. Leído en milímetros son 53 mm, la mitad del diámetro interior de la
  válvula DN 100 del anexo A, que es lo que parece una última etapa. La
  IEC 60534-8-3 da esa misma magnitud por otra vía, su Ecuación (27) y el área
  total de paso, y para esta etapa esa vía da 48,4 mm.
- **Consecuencia:** el resultado de esta fórmula alimenta la Ecuación (12),
  donde $d_o$ va en el denominador junto a $d$ en metros. Tomar el número
  impreso como metros hace el número de Strouhal mil veces menor y con él la
  frecuencia de pico, que mueve el espectro diez octavas.
- **Evidencia:** la fórmula y la fila de la tabla de símbolos tal como se
  imprimen. Verificado en la página 17 del PDF (p. impresa 15) y en la página
  8 del PDF (p. impresa 6) de BS EN 60534-8-4:2005. Esta entrada se apoya
  también en la aritmética de la propia fórmula: nada en las páginas 8 a 20 del
  PDF dice la unidad de la constante 5,2.
- **Comportamiento de la biblioteca:**
  [`last_stage_seat_diameter_mm`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  implementa la fórmula como está impresa y lleva la unidad en el nombre, y su
  docstring dice que hay que dividir entre mil antes de pasar el resultado a la
  Ecuación (12). El test con el nombre de esta entrada fija el valor y el orden
  de magnitud.
- **Estado:** sin comunicar.

## IEC 60534-8-4:2005, Ecuación (23b) (la presión de entrada de una etapa calculada desde la siguiente en vez de desde la anterior)

- **Ubicación:** apartado 6.2, Ecuaciones (23a) y (23b) del folio impreso 13
  (página 15 del PDF) de BS EN 60534-8-4:2005.
- **Lo impreso:** la (23a) es «$p_{1,i} = p_1$ para $i = 1$» y la (23b) es
  «$p_{1,i} = p_{1,i+1} - \dfrac{p_1-p_2}{(C_{i-1}/C)^2}$ para
  $i = 2 \ldots n$».
- **El problema:** tal como está impresa, la presión de entrada de cada etapa
  se calcula desde la de la **siguiente** restando una cantidad positiva, así
  que la sucesión crece con $i$: la última etapa arrancaría a la presión más
  alta y la primera a la más baja, lo que contradice la (23a) e invierte el
  flujo. El índice del denominador es $C_{i-1}$, la etapa *anterior* a la que
  se calcula, que es la recursión para la que está escrita la ecuación:
  $p_{1,i} = p_{1,i-1} - (p_1-p_2)/(C_{i-1}/C)^2$. Leída así, la ecuación es la
  ley de resistencias en serie, $1/C^2 = \sum_i 1/C_i^2$: cada etapa se lleva
  una parte del diferencial en proporción inversa al cuadrado de su propia
  capacidad, y las partes suman el total.
- **Consecuencia:** toda magnitud por etapa del apartado 6, ya que la (24a)
  encadena las presiones de salida con las de entrada y la (26) hace el
  cociente de presiones de cada etapa con ambas. Seguir el índice impreso da un
  interno cuya primera etapa ve el diferencial más pequeño, justo lo contrario
  de todo diseño multietapa que describe la cláusula.
- **Evidencia:** las dos ecuaciones tal como se imprimen. Verificado en la
  página 15 del PDF (p. impresa 13) de BS EN 60534-8-4:2005: el subíndice es
  $i+1$ en la presión e $i-1$ en el coeficiente de caudal. Esta entrada se
  apoya también en la contradicción interna entre la (23a) y la (23b).
- **Comportamiento de la biblioteca:**
  [`stage_conditions`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  implementa la recursión hacia delante y lo dice en su docstring; el test con
  el nombre de esta entrada fija que las presiones de entrada bajan a lo largo
  del interno.
- **Estado:** sin comunicar.

## IEC 60534-8-4:2005, Ecuaciones (18a) y (18b) (dos condiciones que no se reparten el dominio)

- **Ubicación:** apartado 5.3, Ecuaciones (18a) y (18b) del folio impreso 12
  (página 14 del PDF) de BS EN 60534-8-4:2005.
- **Lo impreso:** la (18a) termina «for $x_\mathrm{F} \le x_\mathrm{Fz}$» y la
  (18b) termina «for $x_\mathrm{Fzp1} < x_\mathrm{F} \le 1$».
- **El problema:** las dos condiciones están escritas contra dos umbrales
  distintos. $x_\mathrm{Fz}$ es el cociente característico de presiones a los
  6 × 10⁵ Pa para los que están trazadas la estimación de la Ecuación (3a) y
  las Figuras 4 a 9, y $x_\mathrm{Fzp1}$ es ese mismo cociente llevado a la
  presión de entrada real por la Ecuación (3c), así que solo coinciden a esa
  presión. Por encima, $x_\mathrm{Fzp1} < x_\mathrm{Fz}$ y el intervalo entre
  los dos se lo reclaman las dos ecuaciones, la turbulenta por la (18a) y la
  cavitante por la (18b); por debajo no se lo reclama ninguna. Todo lo demás
  del documento prueba el cociente corregido: las condiciones impresas encima
  de la (7a) y la (7b), la región impresa para la (9), la NOTA de la (17) y el
  reparto del 6.3. La (18a) es la única condición del documento que nombra
  $x_\mathrm{Fz}$, y las dos ni siquiera coinciden en la frontera, que la
  (18a) incluye con ≤ y la (18b) excluye con <.
- **Consecuencia:** crece con la presión de entrada, porque es la presión de
  entrada la que separa los dos umbrales. A los 10 bar del anexo A el
  intervalo en disputa es $0{,}2386 < x_\mathrm{F} \le 0{,}2543$ y las dos
  ramas se separan como mucho 0,03 dB dentro de él, porque la Ecuación (9)
  arranca el término de cavitación en exactamente cero en el umbral. A 100 bar
  el intervalo va de 0,179 a 0,254 y las dos ramas llegan a separarse 8 dB; a
  400 bar, 10 dB. Y el servicio de líquido a alta presión es justo donde este
  método sirve para algo.
- **Evidencia:** las dos condiciones tal como se imprimen. Verificado en la
  página 14 del PDF (p. impresa 12) de BS EN 60534-8-4:2005: la (18a) pone
  «for $x_F \le x_{Fz}$», con el subíndice Fz y sin p1, encima de una (18b)
  que pone «for $x_{Fzp1} < x_F \le 1$».
- **Comportamiento de la biblioteca:**
  [`valve_hydrodynamic_noise`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/valves_hydrodynamic.py)
  decide el régimen una sola vez, con $p_1 - p_2$ contra
  $x_\mathrm{Fzp1}(p_1 - p_\mathrm{v})$, que es la prueba que el 5.1 imprime
  para las Ecuaciones (7a) y (7b), y la potencia sonora, la pérdida por
  transmisión, el nivel exterior y el espectro por bandas salen todos de esa
  única marca. El test con el nombre de esta entrada fija que un punto dentro
  del intervalo en disputa sale cavitante.
- **Estado:** sin comunicar.

## IEC 60534-8-4:2005, Tabla A.1 (tres intermedios impresos que sus propias ecuaciones no reproducen)

- **Ubicación:** anexo A (informativo), Tabla A.1: la fila de la Ecuación (17)
  del folio impreso 24 (página 26 del PDF), columnas 2 y 3; la fila de la
  Ecuación (20a) del mismo folio, columna 3; y la fila de la Ecuación (11) del
  folio impreso 23 (página 25 del PDF), columna 1.
- **Lo impreso:** $TL_{cav} = -62{,}917$ y $-75{,}006$;
  $F_{turb}(8\,000\ \text{Hz}) = -36{,}24$; $f_{p,turb} = 494{,}5$ Hz.
- **El problema:** ninguno de los tres se sigue de los valores impresos a su
  lado. La Ecuación (17) con el $TL_{turb}$, el $f_{p,turb}$, el $f_{p,cav}$ y
  el cociente de eficiencias del propio anexo da $-62{,}86$ y $-74{,}93$, a
  0,06 y 0,08 dB. La Ecuación (20a) a 8 kHz con el $f_{p,turb} = 397{,}93$ Hz
  de esa misma columna da $-36{,}18$; los $-36{,}24$ impresos piden 396,0 Hz.
  Y la cadena sin redondeos por las Ecuaciones (12) y (11) da 494,64 Hz en la
  primera columna, mientras que las columnas 2 y 3 reproducen sus 654,35 y
  397,93 Hz hasta la última cifra impresa.
- **Consecuencia:** pequeña y acotada. Ninguno de los tres llega a un resultado
  impreso: los niveles exteriores de las Ecuaciones (18a) y (18b) redondean a
  los mismos 62,7 / 81,0 / 66,9 dB de una forma o de otra, y el nivel por
  bandas de la (19a) también. Solo importa a quien compare intermedios, que se
  encontrará tres filas de cuarenta que no puede casar exactamente y ninguna
  explicación en la página.
- **Evidencia:** las tres filas tal como se imprimen, recalculadas con los
  intermedios impresos a su lado. Verificado en las páginas 25 y 26 del PDF
  (pp. impresas 23 y 24) de BS EN 60534-8-4:2005. Esta entrada se apoya también
  en un recálculo.
- **Comportamiento de la biblioteca:** la fila de conformidad «Cavitating
  transmission loss, examples 2 and 3 (Eq. (17))» lleva una tolerancia de
  0,1 dB y nombra esta entrada como motivo; los tests con su nombre fijan lo
  que dan las ecuaciones y dejan constancia de lo que imprimió el anexo.
- **Estado:** sin comunicar.

## ISO 7235:2003, Tabla 6 (la banda de 160 Hz no pertenece a ninguna fila)

- **Ubicación:** apartado 6.2.1, Tabla 6, «Maximum level differences for three
  microphone positions in the test duct», en la p. impresa 23 (PDF p. 33) de
  BS EN ISO 7235:2009.
- **Lo impreso:** la columna de frecuencias dice 50, 63, 80, 100, 125 y luego
  «$> 160$», con 10, 10, 8, 8, 7 y 6 dB al lado. El encabezado de esa columna
  es «Frequency / Hz».
- **El problema:** la última fila es estrictamente mayor que 160, así que el
  tercio de octava de 160 Hz no lo cubre ninguna fila y la tabla no le fija
  límite alguno. Todas las demás filas nombran un solo centro de banda, y
  160 Hz es un centro de tercio de octava de la misma serie, de modo que el
  hueco está entre las filas y no en las frecuencias que mide el apartado: el
  6.1 mide todos los tercios de octava de 50 Hz a 10 kHz, incluido el de
  160 Hz. La lectura pretendida es «160 y superiores» o «$\geq 160$», que es
  además la única con la que las seis filas se reparten el intervalo.
- **Consecuencia:** la regla a la que sirve la tabla es la que lleva un
  conducto de ensayo de tres posiciones de micrófono a cinco (6.2.1). Leída al
  pie de la letra, un laboratorio que mida la banda de 160 Hz no tiene
  criterio que aplicar y podría quedarse con tres posiciones fuera cual fuera
  la dispersión entre ellas. Leída como se pretende, el límite allí es de
  6 dB.
- **Evidencia:** las seis filas tal como están impresas, leídas en la página.
  Verificado en la PDF p. 33 (p. impresa 23) de BS EN ISO 7235:2009, que asume
  la ISO 7235:2003 sin modificación: la última celda de la columna de
  frecuencias lleva el signo de desigualdad estricta y ninguna barra de igual,
  y las cinco filas de encima llevan números escuetos.
- **Comportamiento de la biblioteca:**
  [`microphone_spread_limit`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_measurement.py)
  devuelve 6 dB desde 160 Hz hacia arriba, y la fila de conformidad
  «Microphone position spread limits (Table 6)» registra la última fila como
  «160 Hz and above». Un test con el nombre del hueco fija el valor en los
  160 Hz mismos.
- **Estado:** sin comunicar.

## EN 16272-3-1:2012, capítulo 6 (un índice ferroviario ponderado con «el espectro normalizado de ruido de tráfico»)

- **Localización:** capítulo 6, «Single-number rating of airborne sound
  insulation $DL_R$», segundo párrafo, en el folio impreso 7 (página 9 del
  PDF) de la BS EN 16272-3-1:2012.
- **Lo impreso:** «The individual sound reduction index values shall be
  weighted according to the normalised **traffic** noise spectrum defined in
  Table 1».
- **El problema:** la tabla 1 de esta norma es el *espectro normalizado de
  ruido ferroviario*, y la definición de $L_i$ tres líneas por debajo de la
  fórmula lo dice con todas las letras: «the relative A-weighted sound
  pressure level (dB) of the normalised railway noise spectrum, as defined in
  Table 1». La palabra «traffic» es la redacción de carretera del capítulo
  5.2 de la EN 1793-2:2012, de donde este capítulo está copiado por lo demás
  al pie de la letra, fórmula incluida. El capítulo 5 de la propia norma, una
  página antes, lo dice bien: «normalised railway noise spectrum defined in
  Table 1».
- **Consecuencia:** ninguna aritmética, porque la frase nombra la tabla 1 y la
  lista de símbolos nombra el espectro ferroviario. Le importa a quien lee,
  que puede tomar «the normalised traffic noise spectrum» por el término
  definido que es en la EN 1793-3 e irse a buscar la tabla de carretera: los
  dos espectros comparten sus dieciocho bandas y difieren hasta en 7 dB banda
  a banda, así que las dos lecturas no dan el mismo índice.
- **Evidencia:** el párrafo tal como está impreso, leído sobre la página.
  Verificado en la página 9 del PDF (p. 7 impresa) de la
  BS EN 16272-3-1:2012: la palabra «traffic» aparece en el párrafo sobre la
  fórmula (2), y la palabra «railway» en la definición de $L_i$ bajo ella.
- **Comportamiento de la biblioteca:**
  [`airborne_insulation_rating`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/noise_reducing_devices.py)
  recibe el espectro por su nombre y pondera un índice ferroviario con la
  tabla ferroviaria, que es lo que dicen la lista de símbolos y la tabla 1. La
  fila de conformidad «EN 16272-3-1:2012 Clause 6 (DLR on the railway
  spectrum)» lo registra.
- **Estado:** sin comunicar.

## EN 1793-5:2016, fórmula (1) frente a la fórmula (4) (un factor de ganancia que multiplica)

- **Ubicación:** apartado 5.2, fórmula (1) y la lista que la sigue, folios
  impresos 15 y 16 (páginas 17 y 18 del PDF); apartado 5.5.1, fórmula (4) y
  el párrafo anterior, folio impreso 25 (página 27 del PDF) de la
  BS EN 1793-5:2016.
- **Lo impreso:** la fórmula (1) cierra el cociente entre la energía reflejada
  y la incidente de cada banda con el producto
  $\cdot\, C_{geo,k} \cdot C_{dir,k}(\Delta f_j) \cdot C_{gain,k}(\Delta f_g)$,
  y la lista de debajo llama a $C_{gain,k}$ «the correction factor to account
  for a change in the amplification settings of the loudspeaker and in the
  sensitivity settings of the individual microphones when changing the
  measurement configuration from free field to in front of the sample under
  test or vice versa». El apartado 5.5.1 lo define después como «the ratio
  between the spectrum obtained from windowing the incident component from the
  impulse response in front of the sample under test and the spectrum of the
  incident component obtained from windowing the free field impulse response»:
  $C_{gain,k}(\Delta f_g) = \int_{\Delta f_g} |F[h_{i,k,D}(t)\, w_{i,k}(t)]|^2\, df \,/\, \int_{\Delta f_g} |F[h_{i,k,FF}(t)\, w_{i,k}(t)]|^2\, df$.
- **El problema:** las dos fórmulas ponen el factor del mismo lado. En la
  fórmula (1) la componente reflejada sale del registro delante del
  dispositivo y la incidente del registro en campo libre, así que una ganancia
  que difiera en un factor de amplitud $g$ entre las dos configuraciones ya
  multiplica el cociente por $g^2$. La fórmula (4) mide exactamente ese $g^2$.
  Multiplicar por él, como imprime la fórmula (1), deja $g^4$ en el índice;
  dividir por él quita el cambio, que es para lo que la lista bajo la
  fórmula (1) dice que sirve el factor. Con el 20 % que el apartado 5.5.1 aún
  acepta ($C_{gain,k} = 1{,}2$), el producto tal como se imprime da el índice
  un 44 % alto, cuando dejar el cambio sin corregir lo habría dado un 20 % alto.
  Los otros dos factores de la fórmula (1) van en el sentido correcto:
  $C_{geo,k} = (d_{r,k}/d_{i,k})^2$ devuelve la divergencia del camino
  reflejado, más largo, y $C_{dir,k}$ divide lo que el altavoz radia hacia el
  micrófono por lo que radia hacia el punto especular.
- **Evidencia:** las dos fórmulas tal como están impresas, leídas sobre la
  página: la fórmula (1) en la página 17 del PDF (p. 15 impresa), su lista en
  la página 18 del PDF (p. 16 impresa) y la fórmula (4) con el párrafo que la
  define en la página 27 del PDF (p. 25 impresa) de la BS EN 1793-5:2016. La
  consecuencia es un recálculo: registros sintéticos de una reflexión de
  amplitud 0,5, con los registros delante del dispositivo escalados por 1,08,
  dan 0,25 en todas las bandas cuando el factor divide y
  $0{,}25 \times 1{,}08^4$ cuando multiplica.
- **Comportamiento de la biblioteca:**
  [`reflection_index`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_reflection.py)
  divide por $C_{gain,k}$ y lo dice en su docstring. La fila de conformidad
  «EN 1793-5:2016 Formulas (1) and (4) (a gain change between configurations)»
  y un test sobre los registros escalados lo fijan.
- **Estado:** sin comunicar.

## EN 1793-5:2016, tabla B.2 (siete incertidumbres expandidas una centésima por debajo de 1,96 veces la $s_R$ impresa)

- **Ubicación:** anexo B.5 y tabla B.2, folios impresos 54 y 55 (páginas 56 y
  57 del PDF) de la BS EN 1793-5:2016; la tabla A.1 en el folio impreso 47
  (página 49 del PDF).
- **Lo impreso:** el anexo B.5 dice que la incertidumbre se estima «using the
  values for the standard deviation of reproducibility given in Table A.1», con
  «a coverage factor of 1,96» y «the maximal ones (last column of Table A.1)».
  La tabla B.2 imprime, frente a una $s_R$ (High) de 0,32, 0,18, 0,12, 0,14,
  0,15, 0,15 y 0,17 en las bandas de 100 Hz, 125 Hz, 500 Hz, 630 Hz, 800 Hz,
  1 250 Hz y 3 150 Hz, una incertidumbre expandida $U$ de 0,62, 0,34, 0,23,
  0,26, 0,28, 0,28 y 0,32.
- **El problema:** 1,96 veces la $s_R$ impresa da 0,63, 0,35, 0,24, 0,27, 0,29,
  0,29 y 0,33 en esas siete bandas, una centésima por encima de cada celda
  impresa. Las otras once bandas se reproducen a la centésima, y también la
  fila de $DL_{RI}$ (1,96 veces 0,81 dB son 1,59 dB, y 7,68 dB más o menos eso
  es el intervalo [6,09; 9,27] dB del anexo B.5). Ningún factor de cobertura
  único reproduce las siete: la celda de 100 Hz pide uno entre 1,922 y 1,953, y
  la de 125 Hz uno entre 1,861 y 1,917.
- **Mecanismo probable:** las siete son coherentes con 1,96 veces una
  desviación típica sin redondear que se redondea a la impresa (0,316 se
  imprime como 0,32, y 1,96 veces 0,316 es 0,619). La impresión no muestra qué
  valores multiplicó el ejemplo; si fueron esos, son valores que quien lee la
  tabla A.1 no tiene.
- **Consecuencia:** una centésima del índice, que es la resolución con la que
  el informe lo declara (apartado 5.11). Un laboratorio que siga el anexo B.5
  con la tabla A.1 tal como está impresa obtiene los valores más altos.
- **Evidencia:** las dos tablas tal como están impresas, leídas sobre la
  página: la tabla B.2 en la página 57 del PDF (p. 55 impresa) y la tabla A.1
  en la página 49 del PDF (p. 47 impresa) de la BS EN 1793-5:2016. Lo demás es
  un recálculo a partir de las celdas impresas.
- **Comportamiento de la biblioteca:**
  [`ReflectionIndexResult.expanded_uncertainty`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_reflection.py)
  multiplica los valores de la tabla A.1 tal como están impresos. La fila de
  conformidad «EN 1793-5:2016 Table B.2 (expanded uncertainty per band)»
  comprueba las once celdas que se siguen de ellos, y un test fija las otras
  siete una centésima por encima de lo impreso.
- **Estado:** sin comunicar.

## EN 1793-5:2016, apartado 5.5.7 frente al 5.8 (un límite de baja frecuencia leído contra las bandas de dos maneras)

- **Ubicación:** apartado 5.5.7, quinto párrafo, folio impreso 33 (página 35
  del PDF), y apartado 5.8, el párrafo sobre otros fines, el tercero tras la
  lista que sigue a la fórmula (12), folio impreso 43 (página 45 del PDF) de la
  BS EN 1793-5:2016.
- **Lo impreso:** apartado 5.5.7: la muestra de cualificación de 4 m por 4 m
  da «a low frequency limit for the reflection index ... of about 160 Hz at
  microphone 2, 170 Hz at microphone 5 and 220 Hz at microphone 8 ..., i.e.
  using the two window lengths specified in 5.5.5 measurements are valid down
  to the 200 Hz one-third octave band». Apartado 5.8: «for a 3,5 m high barrier
  the single number rating of sound reflection is $DL_{RI}$ (400 - 5 000 Hz),
  because 300 Hz is the lowest frequency applicable to all microphones and
  this invalidates the measurements in the 315 one-third octave band and
  below».
- **El problema:** el primer ejemplo conserva una banda cuya frecuencia
  central, 200 Hz, queda por debajo del límite de uno de sus micrófonos,
  220 Hz; el segundo descarta una banda cuya central, 315 Hz, queda por encima
  del límite, 300 Hz. Ninguna regla única que relacione un límite con una
  banda da los dos: contra la frecuencia central, la muestra de 4 m pierde su
  banda de 200 Hz; contra el borde inferior de la banda (178 Hz y 282 Hz), la
  pierde también; contra el borde superior (224 Hz y 355 Hz), la pantalla de
  3,5 m conserva su banda de 315 Hz.
- **Consecuencia:** la banda fiable más baja $m$ de la fórmula (12) no se
  puede deducir de un límite de baja frecuencia con la regla que el apartado
  ilustra, porque las dos ilustraciones no coinciden.
- **Evidencia:** las dos frases tal como están impresas, leídas sobre la
  página: página 35 del PDF (p. 33 impresa) y página 45 del PDF (p. 43
  impresa) de la BS EN 1793-5:2016. Los bordes de banda son los de tercio de
  octava en base diez, $f_m \cdot 10^{\pm 1/20}$.
- **Comportamiento de la biblioteca:**
  [`sound_reflection_rating`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/noise_reducing_devices.py)
  y
  [`reflection_index`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_reflection.py)
  reciben la banda fiable más baja de quien llama, 200 Hz por defecto, que es
  lo que el apartado 5.5.7 fija para la muestra de cualificación y lo que usa
  el anexo B;
  [`reflection_low_frequency_limit`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_reflection.py)
  da el límite de cada micrófono y deja la elección de la banda al informe,
  que declara las dos cosas: el límite de baja frecuencia por el apartado
  5.11 n), y la banda fiable más baja usada en el índice global por el 5.11 q).
- **Estado:** sin comunicar.

## EN 1793-5:2016, tabla 1 frente a la fórmula (7) (de qué es longitud $T_{W,BH}$)

- **Ubicación:** tabla 1, la fila de $T_{W,BH}$, folio impreso 14 (página 16
  del PDF); apartado 5.5.5, NOTA 1 y fórmula (7), folio impreso 31 (página 33
  del PDF) de la BS EN 1793-5:2016.
- **Lo impreso:** tabla 1: «$T_{W,BH}$ Length of the Blackman-Harris trailing
  edge of the Adrienne temporal window». NOTA 1: «A four-term full
  Blackman-Harris window of length $T_{W,BH}$ is:», y la fórmula (7), con
  $0 \le t \le T_{W,BH}$.
- **El problema:** la fórmula (7) sube de casi cero a 1 durante la primera
  mitad de $T_{W,BH}$ y vuelve a bajar durante la segunda, así que, leída con la
  longitud del flanco de bajada dentro, dibuja una campana entera en esos
  2,22 ms en lugar de la caída que describe el apartado 5.5.5. Los flancos de
  la ventana de Adrienne son mitades de la fórmula (7), cada una sobre una
  ventana completa del doble de su longitud, que es la lectura que da la NOTA 1
  y no la tabla 1.
- **Evidencia:** la fila y la nota tal como están impresas, leídas sobre la
  página: página 16 del PDF (p. 14 impresa) y página 33 del PDF (p. 31
  impresa) de la BS EN 1793-5:2016.
- **Comportamiento de la biblioteca:**
  [`adrienne_reflection_window`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_reflection.py)
  toma cada flanco como una mitad de la fórmula (7) sobre el doble de su
  longitud, que da la ventana que dibuja la figura 13; la fila de conformidad
  «EN 1793-5:2016 5.5.5 and 5.5.1 (the three Adrienne windows)» comprueba las
  tres longitudes de cada ventana. Ningún número cambia con la lectura de la
  fila.
- **Estado:** sin comunicar.

## EN 1793-5:2016, apartado 5.5.5 («microphones 1 to 3, microphones 4 to 6 and microphones 1 to 9»)

- **Ubicación:** apartado 5.5.5, último párrafo, folio impreso 32 (página 34
  del PDF) de la BS EN 1793-5:2016; la plantilla de informe del anexo B.1,
  punto (m), folio impreso 49 (página 51 del PDF).
- **Lo impreso:** apartado 5.5.5: «different window lengths for microphones
  1 to 3, microphones 4 to 6 and microphones 1 to 9 may be used». Anexo B.1
  (m): «Adrienne temporal window (State length for each microphone height)»,
  seguido de «Length for microphones 1–3», «Length for microphones 4–6» y
  «Length for microphones 7–9».
- **El problema:** los tres grupos del apartado 5.5.5 se solapan, porque los
  micrófonos 1 a 9 incluyen a los otros seis, y dejan la fila de abajo sin
  grupo propio. La plantilla de la misma norma nombra las filas de la rejilla,
  1 a 3, 4 a 6 y 7 a 9, una longitud de ventana por altura de micrófono; la
  fila de abajo es la que antes alcanza la reflexión en el suelo
  (apartado 5.5.7), así que es la que más necesita una ventana propia en una
  muestra reducida. «1 to 9» se lee como errata por «7 to 9».
- **Evidencia:** el párrafo y la plantilla tal como están impresos, leídos
  sobre la página: página 34 del PDF (p. 32 impresa) y página 51 del PDF
  (p. 49 impresa) de la BS EN 1793-5:2016.
- **Comportamiento de la biblioteca:**
  [`reflection_index`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_reflection.py)
  recibe una longitud de ventana por micrófono, así que se pueden dar las tres
  filas de la plantilla o cualquier otro reparto. Ningún número cambia con la
  lectura.
- **Estado:** sin comunicar.

## EN 1793-5:2016, leyenda de la figura 15 (una distancia desde el altavoz llamada $d_M$, y un elemento B al que le faltan palabras)

- **Ubicación:** apartado 5.6.2.3, la leyenda de la figura 15, folio impreso 38
  (página 40 del PDF); tabla 1, folio impreso 13 (página 15 del PDF) de la
  BS EN 1793-5:2016.
- **Lo impreso:** elemento 1 de la leyenda: «Distance from the loudspeaker
  front panel to the reference plane $d_M$ [m]». Elemento B: «reference
  position midway and B of the sample under test». Tabla 1: «$d_M$ Horizontal
  distance from the source and microphone reference plane to the measurement
  grid; it is equal to $d_M$ = 0,25 m» y «$d_S$ Horizontal distance from the
  front panel of the loudspeaker to the source and microphone reference plane;
  it is equal to: $d_S$ = 1,50 m».
- **El problema:** el elemento 1 pone las palabras de una distancia al símbolo
  de otra. La distancia del panel frontal del altavoz al plano de referencia
  es $d_S$, 1,50 m; $d_M$ es la de 0,25 m del plano a la rejilla, y es la que
  abarca la cota marcada 1 en la figura 15 (a), desde los micrófonos A, B y C
  hasta el plano de referencia discontinuo, sin altavoz dibujado. El dibujo y
  el símbolo coinciden con la tabla 1; las palabras no. El elemento B nombra a
  B dentro de su propia definición y ha perdido palabras: el pie de la figura
  15 (a) llama a B la posición «midway», entre la parte más saliente (A) y la
  menos saliente (C).
- **Consecuencia:** ninguna numérica, porque la tabla 1 y el apartado 3.14
  fijan $d_M$. Quien tome la leyenda al pie de la letra leería $d_M$ como los
  1,50 m del altavoz en lugar de los 0,25 m de la rejilla.
- **Evidencia:** la leyenda, el dibujo y la tabla 1 tal como están impresos,
  leídos sobre la página: página 40 del PDF (p. 38 impresa) y página 15 del PDF
  (p. 13 impresa) de la BS EN 1793-5:2016.
- **Comportamiento de la biblioteca:** no hace falta ninguno; no se lee ningún
  valor de la figura 15. `REFLECTION_SOURCE_DISTANCE_M` y
  `REFLECTION_MICROPHONE_DISTANCE_M` en
  [`barrier_reflection`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_reflection.py)
  llevan $d_S$ = 1,50 m y $d_M$ = 0,25 m tal como los define la tabla 1.
- **Estado:** sin comunicar.

## ISO 8041-1:2017, apartado 12.7 («the appropriate weighting factor (see Table 1)» para `Wf`)

- **Ubicación:** apartado 12.7, folio impreso 30 (página 30 del PDF en la
  edición de ISO, página 38 del PDF de la copia leída aquí), párrafo cuarto. El
  apartado empieza en el folio impreso 29.
- **Lo impreso:** «For each frequency weighting provided, a steady sinusoidal
  electrical signal shall be applied to the electrical input facility at the
  appropriate reference frequency. With an input signal adjusted to indicate
  the reference vibration value on the reference measurement range with
  band-limiting frequency weighting, the indicated frequency-weighted
  vibration values shall equal the indicated band-limited weighted vibration
  value multiplied by the appropriate weighting factor (see Table 1) within
  the tolerance limits of Table 2.»
- **El problema:** el puntero a la Tabla 1 nombra una magnitud con la que el
  ensayo no se puede satisfacer. El ensayo fija la entrada para que la
  indicación *limitada en banda* marque el valor de referencia, así que la
  indicación ponderada en frecuencia que muestra un instrumento conforme es
  $a_\mathrm{ref}\,|H(f_\mathrm{ref})| / |H_\mathrm{BL}(f_\mathrm{ref})|$: el
  factor que cierra la identidad es el **cociente** de las dos respuestas en la
  frecuencia de referencia, no la ponderación global que imprime la Tabla 1. En
  ocho de las nueve ponderaciones la distinción es invisible, porque su
  ponderación de limitación de banda vale entre 0,999 68 y 0,999 97 en su
  propia frecuencia de referencia y las dos lecturas coinciden al 0,03 %. La
  excepción es `Wf`: su frecuencia de referencia, 2,5 rad/s = 0,397 887 Hz,
  cae dentro de su propia falda de limitación de banda, cuyas esquinas sitúa la
  Tabla 3 en 0,08 Hz y 0,63 Hz. Ahí la ponderación de limitación de banda vale
  0,928 078 y la global 0,388 848, valores que la Tabla B.5 imprime como
  0,927 9 y 0,388 4 en el centro de banda vecino de 0,398 1 Hz. Leído como el
  0,388 8 de la Tabla 1, el ensayo exige un valor que la indicación de un
  vibrómetro `Wf` conforme supera en un 7,76 % de ese valor exigido
  ($0{,}418\,982 / 0{,}388\,8 - 1$), frente al ±5 % que la Tabla 2 permite a
  la vibración de cuerpo entero de baja frecuencia: la mitad otra vez por
  encima del límite, en un instrumento sin defecto. Leído como el cociente
  0,418 982, el ensayo es cierto por construcción.
- **Consecuencia:** ninguna para las tablas de la propia norma. El anexo B
  tabula la ponderación de limitación de banda y la global en columnas
  separadas, así que de él se recuperan las dos lecturas; la ambigüedad está
  solo en la frase del apartado 12.7.
- **Evidencia:** el apartado impreso frente a la Tabla 1 (folio impreso 9), la
  Tabla 2 (folio impreso 12), la Tabla 3 (folios impresos 12 y 13) y la
  Tabla B.5. Las dos respuestas a 2,5 rad/s se evalúan con la cascada de las
  Fórmulas (1) a (5) que definen esos mismos parámetros de la Tabla 3, y
  reproducen a cuatro cifras las dos columnas de la Tabla B.5 en el centro de
  banda vecino. Verificado en la página 38 del PDF (p. impresa 30) de
  ISO 8041-1:2017(E).
- **Comportamiento de la biblioteca:**
  [`band_limited_weighting_factor`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/human/instrumentation.py)
  devuelve el cociente, que es la lectura con la que el ensayo se puede
  satisfacer, y su docstring tabula las dos lecturas una al lado de la otra
  para las nueve ponderaciones, de modo que un informe pueda decir cuál usó.
  `reference_indication` devuelve el producto de la Tabla 1, que es la otra
  magnitud y la que trata la fila de condiciones de referencia de esa tabla.
- **Estado:** sin notificar.

## ISO 8041-2:2021, apartado 12.7 («the appropriate weighting factor (see Table 1)» para `Wf`, heredado de la parte 1)

- **Ubicación:** apartado 12.7, folio impreso 26 (página 34 del PDF), el
  segundo párrafo de ese folio. El apartado empieza en el folio impreso 25.
- **Lo impreso:** la frase del apartado 12.7 de la ISO 8041-1:2017 que recoge
  la entrada anterior, palabra por palabra: «With an input signal adjusted to
  indicate the reference vibration value on the reference measurement range
  with band-limiting frequency weighting, the indicated frequency-weighted
  vibration values shall equal the indicated band-limited weighted vibration
  value multiplied by the appropriate weighting factor (see Table 1) within
  the tolerance limits of Table 2.» La Tabla 1 de este documento imprime el
  mismo factor de ponderación de `Wf` a 2,5 rad/s, 0,388 8, y la Tabla 3 los
  mismos parámetros de `Wf`, con las esquinas de limitación de banda en
  0,08 Hz y 0,63 Hz.
- **El problema:** el defecto de la ISO 8041-1:2017, trasladado al medidor
  personal de exposición a vibraciones. La parte 2 mantiene `Wf` entre las
  ponderaciones que puede ofrecer un PVEM, con la misma frecuencia de
  referencia dentro de la misma falda de limitación de banda, así que la
  aritmética de la entrada anterior vale sin cambios: leído como el 0,388 8 de
  la Tabla 1, el párrafo exige un valor que la indicación de un vibrómetro
  `Wf` conforme supera en un 7,76 % de ese valor exigido
  ($0{,}418\,982 / 0{,}388\,8 - 1$), fuera del ±3 % que la segunda fila de la
  Tabla 2 permite a la diferencia y fuera del ±5 % que su primera fila permite
  a una indicación de cuerpo entero de baja frecuencia. Leído como el cociente
  entre la ponderación global y la de limitación de banda en la frecuencia de
  referencia, 0,418 982, el párrafo es cierto por construcción.
- **Evidencia:** el apartado impreso frente a la Tabla 1 (folio impreso 5) y
  las Tablas 2 y 3 (folio impreso 8), cuya fila de `Wf` lleva los parámetros
  que imprime la ISO 8041-1:2017. Verificado en las páginas 13, 16 y 34 del
  PDF (pp. impresas 5, 8 y 26) de ISO 8041-2:2021(E).
- **Consecuencia:** ninguna para las tablas de la propia norma, igual que en
  la parte 1.
- **Comportamiento de la biblioteca:** esta entrada no lo cambia.
  [`band_limited_weighting_factor`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/human/instrumentation.py)
  devuelve el cociente, y sirve a las dos partes porque la parte 2 imprime las
  mismas ponderaciones. La fila de conformidad «ISO 8041-2:2021 Table 2»
  recoge las tolerancias frente a las que se juzga este párrafo.
- **Estado:** sin notificar.

## ISO 8041-2:2021, apartado 12.7 (ponderaciones temporales juzgadas frente a una fila que la Tabla 2 ya no imprime)

- **Ubicación:** apartado 12.7, folio impreso 26 (página 34 del PDF), el
  tercer párrafo de ese folio; leído frente a la Tabla 2 del folio impreso 8,
  al apartado 5.13 del folio impreso 15, al apartado 5.1.2 del folio impreso 6
  y a la Tabla 8 de los folios impresos 13 y 14.
- **Lo impreso:** «For an instrument where time weightings are provided, a
  steady sinusoidal electrical signal shall be applied to the electrical input
  facility at the reference frequency. [...] With the same input signal, the
  indicated vibration values on each time weighting shall equal the indicated
  reference vibration value within the tolerance limits of Table 2.» La
  Tabla 2 imprime dos filas: la tolerancia de indicación a la frecuencia de
  referencia (±4 %, y ±5 % para la vibración de cuerpo entero de baja
  frecuencia) y la diferencia entre una indicación ponderada en frecuencia y
  la limitada en banda multiplicada por el factor de ponderación (±3 %). El
  apartado 5.13, «Running RMS acceleration», dice entero: «Not applicable for
  PVEM.»
- **El problema:** el párrafo es el que la ISO 8041-1:2017 imprime en su
  propio 12.7 (folio impreso 30 de ese documento), con «the vibration meter»
  cambiado por «the PVEM», y allí el límite al que apunta es la tercera fila
  de la Tabla 2 de la parte 1: la indicación del valor eficaz móvil frente a
  la promediada linealmente en el tiempo, ±2 %. La ponderación temporal de esta
  familia de normas es ese valor eficaz móvil; la parte 1 titula sus Tablas 10
  y 11 «Time-weighting decay rates». La parte 2 quitó la fila, porque su 5.13
  declara que el valor eficaz móvil no aplica, y conservó el párrafo que lo
  juzga, así que el párrafo remite ahora a una tabla en la que ninguna fila
  fija un límite para una indicación con ponderación temporal. Y el propio
  documento deja que un PVEM la tenga: su 5.1.2 (folio impreso 6) permite a un
  PVEM de cuerpo entero «optionally, measure exposure characteristics based on
  maximum transient vibration value (MTVV)», que la ISO 8041-1:2017 3.1.2.4,
  adoptada por el apartado 3, define como el «maximum value of the running
  r.m.s. vibration acceleration value when the integration time is equal to
  1 s», y su Tabla 8 (folios impresos 13 y 14) califica en la ráfaga el «MTVV
  linear» y el «MTVV exponential» de ese valor eficaz móvil. Para un PVEM sin
  ponderación temporal el párrafo queda vacío; para uno que da el MTVV, el
  documento no dice a qué límite se somete la indicación en cada ponderación
  temporal.
- **Evidencia:** los tres pasajes impresos entre sí, frente al 5.1.2 y la
  Tabla 8, y frente al 12.7 de la ISO 8041-1:2017 y su Tabla 2, que imprimen la
  fila del valor eficaz móvil para la que se escribió este párrafo. Verificado
  en las páginas 14, 16, 21, 22, 23 y 34 del PDF (pp. impresas 6, 8, 13, 14,
  15 y 26) de ISO 8041-2:2021(E), y en las páginas 13, 20, 28 y 38 del PDF
  (pp. impresas 5, 12, 20 y 30) de ISO 8041-1:2017(E) para la definición del
  MTVV, la Tabla 2 de la parte 1, el título de su Tabla 10 y su 12.7.
- **Consecuencia:** ninguna para las tablas de la propia norma. El defecto es
  una remisión que sobrevivió a su fila.
- **Comportamiento de la biblioteca:**
  [`PVEM_INDICATION_TOLERANCES_PERCENT`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/human/instrumentation.py)
  publica las dos filas que imprime la parte 2 y ninguna fila del valor eficaz
  móvil, así que nada en la biblioteca juzga un PVEM con este párrafo; la fila
  de la parte 1 sigue siendo `RUNNING_RMS_CONSISTENCY_TOLERANCE_PERCENT`,
  documentada como solo de la parte 1. La fila de conformidad «ISO 8041-2:2021
  Table 2» recoge las dos filas.
- **Estado:** sin notificar.

## ISO 8041-2:2021, apartado 12.22 («exited» por «excited»)

- **Ubicación:** apartado 12.22, «Logging capabilities», folio impreso 36
  (página 44 del PDF), el primer párrafo del apartado.
- **Lo impreso:** «Part A of the PVEM shall be placed on a shaker and be
  exited 2 times for at least 300 s each.»
- **El problema:** «exited» (salido) donde el sentido es «excited» (excitado):
  la parte A se coloca en un excitador para hacerla vibrar dos veces, una a
  cada extremo de la pasada de 12 h, y el párrafo siguiente, en el folio
  impreso 37, cuenta las 600 muestras registradas que «correspond to the
  vibration magnitude», que son esas dos excitaciones de 300 s a una muestra
  por segundo. Tal como está impreso, el verbo dice que la parte sale dos veces
  del excitador.
- **Evidencia:** página 44 del PDF (p. impresa 36) de ISO 8041-2:2021(E), y
  página 45 del PDF (p. impresa 37) para las 600 muestras.
- **Consecuencia:** ninguna para las tablas de la propia norma.
- **Comportamiento de la biblioteca:** no le afecta. El ensayo de registro de
  12 h del 12.22 es un ensayo sobre un medidor físico y no está implementado.
- **Estado:** sin notificar (tipográfico, sin consecuencia numérica).

## DIN 45669-1:2010-09, Tabla 9 (una fila de velocidad de pico que contradice la fórmula (5), y la fila KB_F que tiene al lado)

- **Localización:** Tabla 9, folio impreso 35 (página 35 del PDF de la copia
  leída aquí, que imprime sus folios sin desplazamiento), filas «|v|max in mm/s
  bei f_u = 1 Hz und f_o = 80 Hz» y «KB_F(t) ± 2 % Schwankung».
- **Lo impreso:** para una entrada sinusoidal en las frecuencias de ensayo, la
  fila de pico marca 0,852 a 1 Hz, 1,000 a 5,6 Hz, 1,000 a 31,5 Hz, 0,843 a
  80 Hz y 0,249 a 315 Hz; la fila $KB_F$ de esas mismas cinco columnas marca
  0,103, 0,500, 0,693, 0,594 y 0,071.
- **El problema:** las dos filas están calculadas sobre limitaciones de banda
  distintas, y la fila de pico no sigue la fórmula (5) de la propia norma. Con
  $f_u = 1$ Hz y $f_o = 80$ Hz esa fórmula da $|H_{u\mathrm{Soll}}|$ = 0,995 a
  31,5 Hz y 0,100 a 315 Hz, frente a los 1,000 y 0,249 impresos. La fila $KB_F$
  resuelve cuál de las dos es la lectura pretendida: $KB_F$ es
  $|H_{B\mathrm{Soll}}|/\sqrt{2}$ para una sinusoide de 1 mm/s, y a 31,5 Hz eso es
  0,6928 partiendo de 0,995 y 0,6962 partiendo de 1,000, así que el 0,693
  impreso es lo primero; a 315 Hz es 0,0709 partiendo de 0,100 y 0,176
  partiendo de 0,249, así que el 0,071 impreso vuelve a ser lo primero, por un
  factor de dos y medio. El 0,852 a 1 Hz es la misma clase de desviación en el
  otro extremo, frente al 0,842 de la fórmula (5).
- **Evidencia:** la tabla impresa frente a las fórmulas (5) y (6) del folio
  impreso 18 y la nota bajo la fórmula (3), que sitúa las dos esquinas en
  0,8 Hz y 100 Hz. Verificado en la página 35 del PDF (p. impresa 35) de la
  DIN 45669-1:2010-09; las dos filas son celdas contiguas de una misma columna, así que no hay ninguna cuestión de
  desplazamiento ni de transcripción. Con lo que sí encajan las dos celdas
  anómalas es con el máximo que muestra un retenedor de máximo cuando se
  incluye el transitorio de arranque de la limitación de banda: una sinusoide de
  1 mm/s arrancada en un paso por cero da 0,852 a 1 Hz y 0,248 a 315 Hz a
  través de ese mismo filtro. Esa lectura, sin embargo, no es la que muestran
  las otras tres celdas de la fila, así que la fila no sigue de forma
  consistente ni un criterio ni el otro.
- **Consecuencia para las tablas de la propia norma:** se limita a esa fila. La
  Berichtigung 1:2012-12 reescribe la Tabla 8 y no toca la Tabla 9, y las
  indicaciones de referencia del 6.2.3.12, que son los valores que produce la
  misma señal de ensayo a 16 Hz, las reproducen exactamente las fórmulas.
- **Comportamiento de la biblioteca:**
  [`KB_TEST_INDICATIONS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/vibration_meter.py)
  publica las tres filas de la Tabla 9 que siguen a las fórmulas, y el informe
  de conformidad pasa una sinusoide de 1 mm/s por la cadena entera y reproduce los
  quince valores con los tres decimales con que están impresos. La fila de pico
  ni se publica ni se comprueba; el docstring del módulo dice por qué, y el pico
  que muestra un registro se calcula del registro y no de una tabla.
- **Estado:** sin comunicar.

## DIN 45672-1:2009-12, apartado 4.5.1, fórmulas (1) y (5) (la velocidad de la onda de compresión en una barra delgada, y un radicando al que le falta un factor 2)

- **Localización:** apartado 4.5.1, fórmulas (1) a (4) en la página impresa 7
  y fórmula (5) en la página impresa 8 (páginas 7 y 8 del PDF de la copia leída
  aquí, que imprime sus folios sin desplazamiento).
- **Lo impreso:** la fórmula (1) da la velocidad de la onda de compresión como
  $v_p = \sqrt{E/\rho} = \sqrt{G(1-\nu)/(\rho(1-2\nu))}$, la fórmula (3) da
  el coeficiente de Poisson como $\nu = (v_p^2 - 2 v_s^2)/(2(v_p^2 - v_s^2))$,
  y la fórmula (5) da los dos módulos como $G = v_s^2 \rho$ y $E = v_p^2 \rho$.
- **El problema:** las tres no pueden cumplirse a la vez. En el continuo
  ilimitado que el apartado dice describir, la onda de compresión viaja a
  $v_p = \sqrt{2G(1-\nu)/(\rho(1-2\nu))}$, y la fórmula (3) es exactamente la
  inversa de eso junto con $v_s = \sqrt{G/\rho}$ de la fórmula (2). Al segundo
  radical de la fórmula (1) le falta el factor 2, lo que lo deja $\sqrt{2}$
  veces lento con cualquier coeficiente de Poisson. El primero, $\sqrt{E/\rho}$,
  es la velocidad de una onda longitudinal en una barra delgada: con
  $E = 2G(1+\nu)$ da $v_p^2/v_s^2 = 2(1+\nu)$, frente a $2(1-\nu)/(1-2\nu)$ en
  el continuo. Las dos expresiones que la fórmula (1) iguala solo coinciden
  entre sí en $\nu = (\sqrt{17}-1)/8 \approx 0{,}39$. La fórmula (5) es la
  velocidad de la barra despejada para $E$, así que a partir de un $v_p$ medido
  devuelve el módulo de onda P $M = 2G(1-\nu)/(1-2\nu)$ en lugar de $E$, lo que
  sobrestima $E$ un 35 % con $\nu = 0{,}3$ y 3,8 veces con $\nu = 0{,}45$, el
  rango de un suelo saturado.
- **Evidencia:** las tres fórmulas entre sí en las mismas dos páginas, y frente
  a la velocidad de la onda P de un continuo elástico isótropo. Verificado en la
  página 7 del PDF (p. impresa 7) para las fórmulas (1) a (4) y en la página 8
  del PDF (p. impresa 8) para la fórmula (5) de la DIN 45672-1:2009-12: los
  radicales, el factor $(1-\nu)$ sobre $(1-2\nu)$ y la ausencia del factor 2 se
  leen en la página.
- **Consecuencia para las tablas de la propia norma:** ninguna; el apartado no
  imprime valores resueltos. Lo que cambia es un módulo leído de dos
  velocidades medidas.
- **Comportamiento de la biblioteca:**
  [`compression_wave_speed`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/ground.py)
  y
  [`youngs_modulus_from_wave_speeds`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/ground.py)
  implementan las relaciones del continuo de las que la fórmula (3) es la
  inversa, y los tests fijan las dos formas impresas a los factores de arriba,
  así que una edición de vuelta a lo impreso falla.
- **Estado:** sin comunicar.

## DIN 45672-2:1995-07, apartado 4 (el arranque del valor eficaz móvil, dado en valor cuadrático medio)

- **Localización:** apartado 4, último párrafo de la página impresa 3, y la
  Figura 3 de la página impresa 4 (páginas 3 y 4 del PDF de la copia leída
  aquí, que imprime sus folios sin desplazamiento).
- **Lo impreso:** el valor eficaz móvil «erst nach einer Dauer von 2τ mit einer
  Unsicherheit von 14 % und nach einer Dauer von 4τ mit einer Unsicherheit von
  2 % zur Verfügung steht, wobei der Mittelwert des gleitenden Effektivwertes
  für ein harmonisches Signal zugrunde gelegt wurde (siehe Bild 3)»: solo está
  disponible tras $2\tau$ con un 14 % y tras $4\tau$ con un 2 %, tomando la
  media del valor eficaz móvil de una señal armónica.
- **El problema:** el 14 % y el 2 % son lo que le falta al valor cuadrático
  medio móvil, $e^{-2} = 13{,}5$ % y $e^{-4} = 1{,}8$ %, y no al valor eficaz
  móvil que nombra la frase. La fórmula (1) arrancada desde reposo da un valor
  cuadrático medio que crece como $(1 - e^{-t/\tau})$ de su valor final una vez
  promediado el rizado, así que el valor eficaz crece como la raíz de eso, y le
  falta $1 - \sqrt{1 - e^{-2}} = 7{,}0$ % tras $2\tau$ y
  $1 - \sqrt{1 - e^{-4}} = 0{,}9$ % tras $4\tau$: más o menos la mitad de lo
  impreso.
- **Evidencia:** la fórmula (1) en la misma página y la Figura 3 en la
  siguiente, que dibuja $\tilde v_F/\hat v$ de una sinusoide de 8 Hz y de una de
  20 Hz frente al tiempo en unidades de $\tau$, con la media marcada en 0,707.
  En $2\tau$ las dos curvas oscilan alrededor de 0,66, que es el 93 % de 0,707,
  y en $4\tau$ alrededor de 0,70. Verificado en la página 3 del PDF (p.
  impresa 3) y en la página 4 del PDF (p. impresa 4) de la DIN 45672-2:1995-07.
- **Consecuencia para las tablas de la propia norma:** ninguna. El consejo que
  da la frase, arrancar el promediado antes de que llegue el tren, vale de las
  dos maneras; lo que queda sobrestimado es el tamaño del error que cuesta un
  arranque tardío.
- **Comportamiento de la biblioteca:**
  [`running_velocity_rms`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway.py)
  dice a qué magnitud pertenece cada cifra, y el informe de conformidad
  reproduce el 14 % y el 2 % impresos a partir del valor cuadrático medio de la
  fórmula (1) arrancada desde reposo, que es la lectura que encaja con ellos.
- **Estado:** sin comunicar.

## DIN 45669-2:2005-06, apartado 5.1.4 (un apartado de acoplamiento citado con el número equivocado)

- **Localización:** apartado 5.1.4, último párrafo de la página impresa 6
  (página 6 del PDF de la copia leída aquí, que imprime sus folios sin
  desplazamiento).
- **Lo impreso:** «Bei Messungen am Erdreich sollten für die Schwingungsaufnehmer
  die Ankopplungsverfahren nach 5.3.3 angewandt und müssen die durch die
  Ankopplung verursachten Messabweichungen nach 8.2.3 beachtet werden»: en las
  medidas sobre el terreno se aplican los procedimientos de acoplamiento del
  5.3.3 y se tienen en cuenta las desviaciones del 8.2.3.
- **El problema:** el 5.3.3 es «Ankopplung bei weichen Unterlagen», el
  acoplamiento sobre revestimientos blandos de suelo, cuyo procedimiento es el
  útil de puntas de la figura 1 a) clavado a través de una moqueta. El
  acoplamiento al terreno es el 5.3.4, «Ankopplung an das Erdreich», y sus
  procedimientos, la piqueta, el captador enterrado, el sondeo y la placa
  asentada, son el 5.3.4.2 con la tabla 2. La otra referencia de la misma frase,
  el 8.2.3, es «Ankopplung an das Erdreich» y remite al 5.3.4, que es lo que la
  primera referencia quería decir.
- **Evidencia:** la frase de la página impresa 6, el título del 5.3.3 en la
  página impresa 8 y el título del 5.3.4 en la página impresa 9. Verificado en
  la página 6 del PDF (p. impresa 6), la página 8 del PDF (p. impresa 8) y la
  página 9 del PDF (p. impresa 9) de la DIN 45669-2:2005-06.
- **Consecuencia para las tablas de la propia norma:** ninguna; quien siga el
  número va a parar al útil de moqueta en lugar de a la tabla 2.
- **Comportamiento de la biblioteca:**
  [`vibration.immission.coupling`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/coupling.py)
  lleva los límites de montaje suelto del 5.3.2 y el 5.3.3 y la desviación en
  terreno del 5.3.4.1, y su docstring nombra cada uno por el apartado que lo
  imprime.
- **Estado:** sin comunicar.

## DIN 4150-2:1999-06, anexo A, fórmula (A.1b) (un eficaz de máximos por intervalo igualado a una media de cuadrados)

- **Localización:** anexo A, fórmulas (A.1a) y (A.1b) en la página impresa 11
  (página 11 del PDF de la copia leída aquí, que imprime sus folios sin
  desplazamiento).
- **Lo impreso:** la fórmula (A.1a) dice $KB_{FTm,j} = \sqrt{\frac{1}{M_j}
  \sum_{i=1}^{M_j} KB^2_{FTi,j}}$ y, «oder», la fórmula (A.1b) dice
  $KB_{FTm,j} = \frac{1}{Z_j} \sum_{i=1}^{Z_j} KB^2_{FTi,j}$, para el caso en
  que de la clase $j$ solo se midieron $Z_j$ intervalos ocupados.
- **El problema:** la segunda fórmula no lleva raíz sobre la suma, así que su
  lado izquierdo es un eficaz de máximos por intervalo y el derecho una media
  de cuadrados. Las dos están impresas como alternativas para la misma
  magnitud y solo difieren en el número sobre el que promedian, así que o
  llevan raíz las dos o ninguna; la fórmula (A.2) de debajo toma
  $KB^2_{FTm,j}$ como la media de los cuadrados, que es lo que es el lado
  derecho de (A.1b), y el ejemplo 8 resuelto en la página impresa 17 aplica
  (A.1b) con la raíz: $KB_{FTm,1} = \sqrt{\tfrac{1}{3}(0{,}92^2 + 0{,}6^2 +
  0{,}9^2)} = 0{,}82$ «aus Gleichung (A.1b)». O a (A.1b) se le perdió la raíz
  o su lado izquierdo debería decir $KB^2_{FTm,j}$.
- **Evidencia:** las dos fórmulas de la página impresa 11 y el ejemplo de la
  página impresa 17. Verificado en la página 11 del PDF (p. impresa 11) y en la
  página 17 del PDF (p. impresa 17) de la DIN 4150-2:1999-06: el radical de
  (A.1a) está dibujado y el de (A.1b) no aparece en la página.
- **Consecuencia para las tablas de la propia norma:** ninguna; el ejemplo que
  usa la fórmula usa la correcta.
- **Comportamiento de la biblioteca:**
  [`railway_takt_maximum_rms`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/people.py)
  toma la raíz, y los tests lo fijan a los 0,82 y 0,22 del ejemplo 8.
- **Estado:** sin comunicar.

## E DIN 4150-2:2023-08, anexo B, ejemplo 9 (la noche valorada sobre 920 intervalos en vez de 960)

- **Localización:** B.9.3.3, las dos fórmulas de la noche en la página impresa
  44 (página 44 del PDF de la copia leída aquí, que imprime sus folios sin
  desplazamiento), frente al 6.5.3.2 de la página impresa 19.
- **Lo impreso:** $KB_{FTr,\mathrm{nachts}} = \sqrt{\tfrac{1}{920} \cdot (12 \cdot
  (0{,}9 \cdot 0{,}24)^2 + 18 \cdot (1{,}0 \cdot 0{,}44)^2)} = 0{,}066$ para el
  caso sin el proyecto y, con el mismo divisor, $0{,}096 > 0{,}07$ para el caso
  planificado; las fórmulas del día de la misma página dividen por 1920.
- **El problema:** el 6.5.3.2 fija $N_r$ de la fórmula (6) en 1920 intervalos
  de día y 960 de noche, que es lo que son 8 h de intervalos de 30 s. Los dos
  resultados de la noche reproducen 920 exactamente, 0,0663 y 0,0957, y con
  960 son 0,0649 y 0,0937, que se imprimen 0,065 y 0,094. La prueba del 25 %
  que sigue, $0{,}096 > 1{,}25 \cdot 0{,}066 = 0{,}082$, pasa a ser $0{,}094 >
  1{,}25 \cdot 0{,}065 = 0{,}081$ y llega a la misma conclusión.
- **Evidencia:** el divisor 920 en las dos fórmulas de la noche de la página
  impresa 44 y la definición de $N_r$ en la página impresa 19. Verificado en la
  página 44 del PDF (p. impresa 44) y en la página 19 del PDF (p. impresa 19)
  de la E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna; la conclusión
  del ejemplo se sostiene de las dos formas.
- **Comportamiento de la biblioteca:**
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  divide la noche por los 960 del 6.5.3.2, y las filas de conformidad del
  ejemplo 9 comparan con 0,065 y 0,094 diciendo lo que da lo impreso.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, anexo B, figura B.2 b) (máximos por intervalo impresos en la figura que no dan el 0,39 que usa el ejemplo)

- **Localización:** figura B.2 b) en la página impresa 33 (página 33 del PDF) y
  el texto de B.4.3.3 en la página impresa 34.
- **Lo impreso:** la figura rotula los diez intervalos del martillo B con
  $KB_{FTi}$ = 0,3; 0,41; 0,47; 0,43; 0,47; 0,37; 0,31; 0,04; 0,3; 0,41, y el
  texto pone el 0,04 a cero y encuentra «$KB_{FTmb}$ = 0,39».
- **El problema:** el eficaz de esos diez valores con el 0,04 a cero es
  $\sqrt{1{,}3759 / 10} = 0{,}371$, no 0,39. Los rótulos del martillo A de la
  misma figura sí dan el 0,16 que usa el texto. La figura C.3 de la edición de
  1999 no llevaba rótulos y el 0,39 se heredó de ella; el borrador añadió los
  rótulos y no se ajustaron al número. Los ejemplos 4 y 5 usan 0,39 y sus
  veredictos no cambian con 0,37: 0,150 y 0,188 en lugar de 0,154 y 0,195.
- **Evidencia:** los diez rótulos de la página impresa 33 y, en la página
  impresa 34, la frase «Somit ergibt sich aus Bild B.2.» con la línea
  «$KB_{FTma}$ = 0,16 und $KB_{FTmb}$ = 0,39» debajo. Verificado en la página 33 del PDF (p. impresa 33) y en la
  página 34 del PDF (p. impresa 34) de la E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna; los ejemplos 4
  y 5 concluyen lo mismo con cualquiera de los dos valores.
- **Comportamiento de la biblioteca:** las filas de conformidad de los
  ejemplos 4 y 5 de la edición de 1999, cuyo texto y cuyos números repiten
  los ejemplos 4 y 5 del borrador, toman como entradas el 0,16 y el 0,39 que
  imprime el texto; nada se lee de la figura.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, anexo A, figura A.1 (una decisión dibujada con la respuesta al revés)

- **Localización:** figura A.1 en la página impresa 28 (página 28 del PDF), el
  rombo de la columna central bajo la línea de trazos, frente a la misma figura
  de la DIN 4150-2:1999-06, figura B.1 en su página impresa 12.
- **Lo impreso:** el rombo pregunta «KB-Werte > Stufe III?» y su salida «ja»
  lleva a «Weiterer Betrieb ohne besondere Maßnahmen», su salida «nein» a
  «Weiterer Betrieb nur mit besonderen Maßnahmen».
- **El problema:** un valor por encima del escalón III es el caso que necesita
  medidas especiales, que es como está dibujado el rombo de la derecha de la
  misma figura, con la misma pregunta: «ja» hacia las medidas especiales. La
  figura de 1999 imprime el rombo central como «KB-Werte < Stufe III?» con las
  mismas salidas, que se lee bien; la figura redibujada dio la vuelta a la
  comparación y conservó las salidas.
- **Evidencia:** los tres rombos bajo la línea de trazos de la página impresa
  28 del borrador y el rombo central de la página impresa 12 de la edición de
  1999. Verificado en la página 28 del PDF (p. impresa 28) de la
  E DIN 4150-2:2023-08 y en la página 12 del PDF (p. impresa 12) de la
  DIN 4150-2:1999-06.
- **Consecuencia para las tablas de la propia norma:** ninguna; la figura es
  un flujo de gestión y nada de la norma se calcula con ella.
- **Comportamiento de la biblioteca:** ninguno; el flujo del anexo A no está
  implementado.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, anexo B, B.9.3.1 (una ampliación valorada por el apartado de una línea nueva)

- **Localización:** B.9.3.1 en la página impresa 42 (página 42 del PDF).
- **Lo impreso:** «Die Beurteilung erfolgt nach 6.5.3.5.»
- **El problema:** el 6.5.3.5 es la valoración de una línea de nueva
  construcción. El ejemplo 9 es la ampliación de una línea existente con una
  segunda vía, que es el 6.5.3.6, y el ejemplo aplica a continuación la regla
  del 25 % del 6.5.3.6 a su Nullfall y su Planfall.
- **Evidencia:** la frase de la página impresa 42, el título del 6.5.3.5 en la
  página impresa 21 y el del 6.5.3.6 en la página impresa 21. Verificado en la
  página 42 del PDF (p. impresa 42) y en la página 21 del PDF (p. impresa 21)
  de la E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna; el ejemplo
  aplica el apartado correcto.
- **Comportamiento de la biblioteca:**
  [`assess_railway_change`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  es el 6.5.3.6 y su docstring nombra el ejemplo 9 como su caso resuelto.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, 6.5.3.6 (requisitos cumplidos cuando se da una condición, y un ejemplo que las necesita todas)

- **Localización:** 6.5.3.6 en la página impresa 22 (página 22 del PDF de la
  copia leída aquí, que imprime sus folios sin desplazamiento), frente a
  B.9.3.3 y B.9.4 en la página impresa 44.
- **Lo impreso:** «Falls eine der folgenden Bedingungen für den
  Prognoseplanfall vorliegt, gelten die Anforderungen dieses Dokuments als
  eingehalten:», seguido de a) para $KB_{F\mathrm{max}}$ de día, b) para
  $KB_{F\mathrm{max}}$ de noche y c) para $KB_{FTr}$, cada una cumplida bien
  respetando su valor de referencia, bien con un aumento inferior al 25 %
  frente al caso sin el proyecto.
- **El problema:** leído tal como está impreso, basta una condición. El
  ejemplo 9 tiene la b) cumplida, «Für den Prognosefall bleibt der
  $KB_{F\mathrm{max}}$-Wert unverändert bei 0,66», un aumento nulo, y aun así
  concluye en B.9.4 que hay que estudiar medidas correctoras porque
  $KB_{FTr}$ de noche supera $A_r$ y crece más de un 25 %. Las tres letras
  son tres valoraciones de dos magnitudes, y el ejemplo aplica todas las que
  encajan en el caso; «eine der» dice lo contrario.
- **Evidencia:** la frase y sus tres letras en la página impresa 22, y el
  0,66 sin cambios con la conclusión en la página impresa 44. Verificado en la
  página 22 del PDF (p. impresa 22) y en la página 44 del PDF (p. impresa 44)
  de la E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna; el ejemplo
  llega a la conclusión para la que está el apartado.
- **Comportamiento de la biblioteca:**
  [`assess_railway_change`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  exige todas las condiciones que se aplican, como hace el ejemplo, y su
  docstring dice por qué.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, anexo B, B.8.3.4 (un resultado que sus propias entradas de cuatro decimales no dan)

- **Localización:** la última fórmula de B.8.3.4 en la página impresa 39
  (página 39 del PDF), frente a la tabla B.1 en la página impresa 38.
- **Lo impreso:** $KB_{FTr} = \sqrt{\tfrac{1}{1920} \cdot (144 \cdot (1{,}0
  \cdot 0)^2 + 144 \cdot (1{,}0 \cdot 0)^2 + 80 \cdot (0{,}7 \cdot 0{,}406\,1)^2 +
  80 \cdot (0{,}7 \cdot 0{,}567\,6)^2)} = 0{,}099\,8 > 0{,}07$.
- **El problema:** con los 0,406 1 y 0,567 6 de cuatro decimales la fórmula
  da 0,099 72, que se imprime 0,099 7; el 0,099 8 impreso es lo que dan los
  0,406 y 0,568 de tres decimales de la tabla B.1, 0,099 76. Los propios
  pasos de la tabla B.1 dan 0,099 72. Una unidad en el cuarto decimal, y el
  veredicto, 0,07 superado, no depende de ella.
- **Evidencia:** la fórmula y su resultado en la página impresa 39 y los
  valores eficaces de la tabla B.1 en la página impresa 38. Verificado en la
  página 39 del PDF (p. impresa 39) y en la página 38 del PDF (p. impresa 38)
  de la E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:** la fila de conformidad del ejemplo 8
  compara
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  a partir de los 47 pasos con 0,099 7 a media unidad del cuarto decimal, y
  dice lo que da lo impreso.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, anexo B, B.4.3.3 (el eficaz de los máximos por intervalo atribuido a la fórmula (2))

- **Localización:** B.4.3.3 en la página impresa 34 (página 34 del PDF),
  frente a 4.2.5 en la página impresa 12 y 6.4.2 en la página impresa 16.
- **Lo impreso:** «Wegen der Annahme, dass Bild B.2 repräsentativ für die
  gesamten Teileinwirkungszeiten $T_{ea}$ und $T_{eb}$ sei, gilt nach
  Gleichung (2):», seguido de $KB_{FTma} = \sqrt{\tfrac{1}{10} \sum_{i=1}^{10}
  KB^2_{FTia}}$ y lo mismo para el martillo B.
- **El problema:** eso es la fórmula (1) de 4.2.5, el eficaz de los máximos
  por intervalo sobre $N$ intervalos. La fórmula (2) de 6.4.2 es la
  intensidad de valoración a partir de exposiciones parciales, que el
  ejemplo aplica dos líneas después, y el borrador renumeró como (1) la
  fórmula (3) de la edición de 1999, que citaba el ejemplo de 1999.
- **Evidencia:** la frase en la página impresa 34, la fórmula (1) en la
  página impresa 12 y la fórmula (2) en la página impresa 16. Verificado en
  la página 34 del PDF (p. impresa 34), la página 12 del PDF (p. impresa 12)
  y la página 16 del PDF (p. impresa 16) de la E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna; la
  aritmética es la de la fórmula (1).
- **Comportamiento de la biblioteca:** nada que tomar.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, anexo B, B.3.2 (una nota citada bajo el apartado del que se la sacó)

- **Localización:** el último guion de B.3.2 en la página impresa 31 (página
  31 del PDF), frente a la nota bajo 6.3 en la página impresa 15.
- **Lo impreso:** «Es ist zu prüfen, ob das $A_r$-Kriterium hier nicht zu
  berücksichtigen ist (siehe Anmerkung zu 6.2).»
- **El problema:** la nota sobre el criterio $A_r$, las 4 h de día y 2 h de
  noche por encima de las cuales una vibración estacionaria hace que no
  merezca la pena formar $KB_{FTr}$, está impresa bajo 6.3 en el borrador;
  6.2 son los valores de referencia. En la edición de 1999 la misma nota
  estaba bajo 6.2, el procedimiento, y la referencia cruzada del ejemplo no
  se movió con ella.
- **Evidencia:** el guion en la página impresa 31, la nota bajo 6.3 en la
  página impresa 15 y el encabezado de 6.2 en la página impresa 14.
  Verificado en la página 31 del PDF (p. impresa 31), la página 15 del PDF
  (p. impresa 15) y la página 14 del PDF (p. impresa 14) de la
  E DIN 4150-2:2023-08, y la nota bajo 6.2 en la página 6 del PDF
  (p. impresa 6) de la DIN 4150-2:1999-06.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:** nada que tomar.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 4150-2:2023-08, 6.3 (un suceso raro cumplido por debajo del valor superior en la prosa y en él en el diagrama)

- **Localización:** el cuarto guion de 6.3 en la página impresa 15 (página
  15 del PDF), frente a 6.5.1.1 en la página impresa 17 y la figura 2 en la
  página impresa 15.
- **Lo impreso:** «Für selten auftretende, kurzzeitige Einwirkungen ist die
  Anforderung dieses Dokuments eingehalten, wenn $KB_{F\mathrm{max}}$ kleiner
  als $A_o$ ist (siehe 6.5.1)»; 6.5.1.1 dice «wenn die maximale bewertete
  Schwingstärke $KB_{F\mathrm{max}}$ kleiner oder gleich dem (oberen)
  Anhaltswert $A_o$ nach Tabelle 1 ist», y el rombo de la figura 2 pregunta
  «$KB_{F\mathrm{max}} \le A_o$?».
- **El problema:** un suceso raro cuyo $KB_{F\mathrm{max}}$ es igual a $A_o$
  cumple según el apartado y la figura y no según el guion que remite a
  ellos.
- **Evidencia:** el guion y el rombo en la página impresa 15 y la frase de
  6.5.1.1 en la página impresa 17. Verificado en la página 15 del PDF
  (p. impresa 15) y en la página 17 del PDF (p. impresa 17) de la
  E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:**
  [`assess_people_in_buildings`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/people.py)
  lee la frontera como el apartado y el diagrama, igual o por debajo.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 45672-3:2023-02, anexo C, C.3 (dos intensidades de valoración que ponderan por el factor una vez donde la fórmula (11) lo eleva al cuadrado)

- **Localización:** C.3 en la página impresa 34 (página 34 del PDF de la copia
  leída aquí, que imprime sus folios sin desplazamiento) y en la página impresa
  35, frente a la fórmula (11) de la página impresa 23 y al anexo E de la
  página impresa 37.
- **Lo impreso:** con 200 pasos de día y 20 de noche, el factor $\alpha$ = 0,7
  de un tranvía en superficie y $KB_{FTm,Zug}$ = 0,4, la fórmula (11) da
  «$KB_{FTr,Zug,Tag}$ = 0,11» y «$KB_{FTr,Zug,Nacht}$ = 0,05», y C.4 encuentra el
  día superado, «0,11 > $A_{r,Tag}$ = 0,1».
- **El problema:** la fórmula (11) con esas entradas y $N_r$ = 1920 de día y
  960 de noche es $0{,}7 \cdot 0{,}4 \cdot \sqrt{200/1920} = 0{,}090$ y $0{,}7
  \cdot 0{,}4 \cdot \sqrt{20/960} = 0{,}040$. Los valores impresos son lo que
  dan esas mismas entradas con $\alpha$ bajo la raíz una vez en lugar de al
  cuadrado, $0{,}4 \sqrt{0{,}7 \cdot 200/1920} = 0{,}108$ y
  $0{,}4 \sqrt{0{,}7 \cdot 20/960} = 0{,}048$: el ejemplo pondera por el factor
  la energía de la categoría donde la fórmula (11) pondera su amplitud. Con
  el 0,090 de la fórmula el veredicto de C.4 sobre el día se invierte: 0,09
  está por debajo del $A_r$ de 0,1 y el requisito se cumple.
- **Evidencia:** las entradas de la página impresa 34, los dos resultados al
  principio de la página impresa 35 y la valoración debajo de ellos, la
  fórmula y su $N_r$ en la página impresa 23 y los factores en la página
  impresa 37. Verificado en la página 34 del PDF
  (p. impresa 34), la página 35 del PDF (p. impresa 35), la página 23 del PDF
  (p. impresa 23) y la página 37 del PDF (p. impresa 37) de la
  E DIN 45672-3:2023-02.
- **Consecuencia para las tablas de la propia norma:** la conclusión del
  ejemplo para el día, que hay que planificar medidas correctoras, no se sigue
  de sus números.
- **Comportamiento de la biblioteca:**
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py)
  eleva el factor al cuadrado como imprime la fórmula (11), y las filas de
  conformidad de C.3 comparan con el 0,090 y el 0,040 que da para las
  entradas impresas, diciendo que lo impreso pone 0,11 y 0,05.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 45672-3:2023-02, anexo C, tabla C.1 (un nivel suma formado sin la ponderación que prescribe el apartado 7.1)

- **Localización:** tabla C.1 y resultados de C.3 en la página impresa 34
  (página 34 del PDF), frente a las fórmulas (8) y (9) de las páginas impresas
  21 y 22.
- **Lo impreso:** la tabla cierra con la fila
  «Schwinggeschwindigkeitssummenpegel der betrachteten Zugkategorie
  ($L_{v,Zug}$):» y 78,1 dB en su última columna, y C.3 lo lleva a la
  fórmula (9),
  $KB_{FTm,Zug} = c_{T1} v_0 10^{L/20} = 0{,}4$, luego 0,6 por la fórmula (10) y
  «$v_{\max}$ = 1,81 mm/s» por la fórmula (12).
- **El problema:** el apartado 7.1 a) suma primero a cada banda la ponderación
  KB de la tabla 2 (fórmula (8)) y suma las bandas de 4 Hz a 80 Hz. La suma
  energética de los 19 $L_v$ impresos sin ponderación alguna es 78,08 dB, que
  es el 78,1 impreso; la suma ponderada de 4 Hz a 80 Hz es 77,7 dB, y la cadena
  desde ella es 0,385, 0,577 y 1,73 mm/s. El 1,81 mm/s impreso es $3 \cdot
  1{,}5 \cdot 5 \cdot 10^{-5} \cdot 10^{78{,}1/20} = 1{,}808$, así que el ejemplo
  arrastró la suma sin ponderar.
- **Evidencia:** la suma y los tres resultados de la página impresa 34 y las
  fórmulas de las páginas impresas 21 y 22. Verificado en la página 34 del PDF
  (p. impresa 34), la página 21 del PDF (p. impresa 21) y la página 22 del PDF
  (p. impresa 22) de la E DIN 45672-3:2023-02.
- **Consecuencia para las tablas de la propia norma:** los resultados de C.3
  están un 4 % altos frente al procedimiento de la propia norma; los veredictos
  de C.4 son los mismos de las dos formas, 0,6 redondea ambos.
- **Comportamiento de la biblioteca:**
  [`predict_train_category`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  pondera las bandas como dice el 7.1 a) antes de sumarlas; las filas de
  conformidad fijan la cadena impresa desde 78,1 dB y el test fija la
  ponderada.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 45672-3:2023-02, anexo C, C.2 y tabla C.1 (una transmisión al forjado que no sale de ninguna tabla del anexo A, y una figura citada con el número equivocado)

- **Localización:** C.2 en la página impresa 33 (página 33 del PDF) y la
  columna $\Delta L_{v,DF}$ de la tabla C.1 en la página impresa 34, frente a la
  tabla A.5 de la página impresa 27 y la figura 4 de la página impresa 15.
- **Lo impreso:** C.2 dice que la transmisión de la cimentación al forjado del
  ejemplo es «die Übertragungen vom Fundament zur Geschossdecke mit einer
  Deckeneigenfrequenz von 20 Hz aus Bild 3», y la tabla C.1 imprime la columna
  1,9; 2,3; 3,1; 3,5; 5,0; 6,9; 11,5; 17,3; 10,0; 5,4; 1,9; 1,5; −0,8; −2,3;
  −3,8; −5,4; −6,5; −8,1; −9,6 dB de 4 Hz a 250 Hz.
- **El problema:** la figura 3 es la transmisión del terreno a una cimentación
  a nivel del suelo; la transmisión de la cimentación al forjado de un forjado
  de hormigón es la figura 4 y la tabla A.5. Leída en los cocientes de las
  bandas a 20 Hz, la media de la tabla A.5 da 1,60; 2,06; 2,52; 3,26; 4,19;
  6,35; 9,94; 17,26; 9,85; 4,41; 3,27; 3,25; 1,42; 3,89; 2,83 dB hasta 100 Hz y
  nada por encima de un cociente de 5. Solo coincide el pico; ni la media ni
  ninguna de las dos desviaciones de la tabla A.5, ni la columna de 20 Hz de la
  tabla A.1, dan la columna impresa, y la tabla no tiene valores para las cuatro
  últimas bandas que la columna rellena.
- **Evidencia:** la frase de la página impresa 33, la columna de la página
  impresa 34 y la tabla A.5 en las páginas impresas 27 y 28. Verificado en la
  página 33 del PDF (p. impresa 33), la página 34 del PDF (p. impresa 34), la
  página 27 del PDF (p. impresa 27) y la página 28 del PDF (p. impresa 28) de
  la E DIN 45672-3:2023-02.
- **Consecuencia para las tablas de la propia norma:** el ejemplo no puede
  reproducirse a partir de las tablas de la propia norma; su columna de
  transmisión es una entrada.
- **Comportamiento de la biblioteca:** las filas de conformidad de la tabla
  C.1 toman la columna impresa como entrada de la fórmula (1) y fijan la suma;
  [`foundation_to_floor_transfer_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  lee la tabla A.5 tal como está impresa.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 45672-3:2023-02, anexo A, tabla A.6 (una desviación hacia abajo impresa por encima de la media de la que se desvía)

- **Localización:** tabla A.6 en la página impresa 28 (página 28 del PDF), y
  figura 5 en la página impresa 16.
- **Lo impreso:** en los cocientes 0,20, 3,10, 4,00 y 5,00 la columna
  «Standardabweichung nach unten (E–u)» pone 2,37; 5,26; 5,42 y 7,63 dB frente
  a un «Mittelwert (E–m)» de 2,19; 3,55; 3,24 y 3,01 dB, y en 5,00 la
  «Standardabweichung nach oben (E–o)» es 5,40 dB, por debajo de la de abajo.
- **El problema:** una desviación hacia abajo respecto de una media no puede
  estar por encima de ella, y la desviación hacia arriba no puede estar por
  debajo de la de abajo. La figura 5 dibuja el mismo cruce, con su curva 1
  acabando por encima de las curvas 2 y 3, así que la figura se hizo con los
  mismos datos; si se intercambiaron dos columnas en la cola o la estadística
  está mal no se puede saber por la página. La tabla A.5, el forjado de
  hormigón, guarda el orden en todas sus filas.
- **Evidencia:** las cuatro filas de la página impresa 28 y la cola de las
  curvas de la página impresa 16. Verificado en la página 28 del PDF
  (p. impresa 28) y en la página 16 del PDF (p. impresa 16) de la
  E DIN 45672-3:2023-02.
- **Consecuencia para las tablas de la propia norma:** quien tome la desviación
  hacia abajo como el lado seguro de la transmisión de un forjado de madera
  está por encima de la media en esos cocientes.
- **Comportamiento de la biblioteca:**
  [`FOUNDATION_TO_FLOOR_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  lleva la tabla tal como está impresa, su docstring dice dónde falla el orden,
  y no se impone orden alguno entre los tres estadísticos.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 45672-3:2023-02, figuras 5, 6 y 7 (leyendas que nombran la tabla equivocada y la magnitud equivocada)

- **Localización:** la leyenda de la figura 5 en la página impresa 16 (página
  16 del PDF) y las leyendas de eje de las figuras 6 y 7 en las páginas
  impresas 17 y 18.
- **Lo impreso:** la figura 5, la transmisión de la cimentación al forjado de
  los forjados de madera, rotula sus curvas 1, 2 y 3 «Übertragung Fundament →
  Erdgeschoss und Obergeschosse bei Holzbalkendecken» con «(D–u)», «(D–m)» y
  «(D–o)»; las figuras 6 y 7, la transmisión del terreno al forjado, rotulan su eje
  vertical «Pegeldifferenz $\Delta L_{v,DF}(f_{Tn})$ in dB».
- **El problema:** la tabla que dibuja la figura 5, la A.6, llama a sus
  columnas E–u, E–m y E–o; D–u, D–m y D–o son las columnas de la tabla A.5, el
  forjado de hormigón de la figura 4. Y las figuras 6 y 7 dibujan
  $\Delta L_{v,DB}$, la diferencia del terreno al forjado de las tablas A.1 y
  A.2, como dicen sus pies; $\Delta L_{v,DF}$ es la diferencia de la
  cimentación al forjado de las figuras 4 y 5.
- **Evidencia:** las leyendas de las páginas impresas 16, 17 y 18 y las
  cabeceras de columna de las páginas impresas 28, 24 y 25. Verificado en la
  página 16 del PDF (p. impresa 16), la página 17 del PDF (p. impresa 17), la
  página 18 del PDF (p. impresa 18), la página 24 del PDF (p. impresa 24), la
  página 25 del PDF (p. impresa 25) y la página 28 del PDF (p. impresa 28) de
  la E DIN 45672-3:2023-02.
- **Consecuencia para las tablas de la propia norma:** ninguna; los pies y las
  tablas están bien.
- **Comportamiento de la biblioteca:** nada que adoptar; lo implementado son
  las tablas.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 45672-3:2023-02, 5.4.4 (un anexo llamado normativo donde está impreso informativo)

- **Localización:** 5.4.4 en la página impresa 16 (página 16 del PDF de la
  copia leída aquí, que imprime sus folios sin desplazamiento), frente al
  encabezado del anexo A en la página impresa 24.
- **Lo impreso:** «Im normativen Anhang A sind die Werte in Tabellenform für
  alle relevanten Deckeneigenfrequenzen zusammengefasst.»; el anexo se
  encabeza «Anhang A (informativ)».
- **El problema:** las seis tablas de las que se hace la predicción son
  parte de los requisitos o una información, y las dos páginas dicen una
  cosa cada una.
- **Evidencia:** la frase en la página impresa 16 y el encabezado en la
  página impresa 24. Verificado en la página 16 del PDF (p. impresa 16) y en
  la página 24 del PDF (p. impresa 24) de la E DIN 45672-3:2023-02.
- **Consecuencia para las tablas de la propia norma:** ninguna para sus
  valores.
- **Comportamiento de la biblioteca:** las tablas están implementadas tal
  como están impresas, sea cual sea su estatus.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## E DIN 45672-3:2023-02, fórmula (11) (la suma de valoración impresa sin la regla que anula una categoría silenciosa)

- **Localización:** la fórmula (11) y sus símbolos en la página impresa 23
  (página 23 del PDF), frente a la fórmula (6) de la E DIN 4150-2:2023-08 en
  sus páginas impresas 19 y 20.
- **Lo impreso:** «$KB_{FTr} = \sqrt{\sum_{Zug=1}^{N_Z} \tfrac{n_{Zug}}{N_r}
  (\alpha_{Zug} \cdot KB_{FTm,Zug})^2}$», introducida por «Berechnung der
  Beurteilungs-Schwingstärke ($KB_{FTr}$) für den jeweiligen
  Beurteilungszeitraum entsprechend DIN 4150-2», con $N_r$, $N_Z$,
  $n_{Zug}$, $KB_{FTm,Zug}$ y $\alpha_{Zug}$ «nach informativem Anhang E»
  listados debajo y nada más.
- **El problema:** la suma, sus símbolos y los factores del anexo E son la
  fórmula (6) y la tabla 2 del borrador de la DIN 4150-2, que imprime bajo
  su fórmula que una categoría cuyo $KB_{FTm,Zug}$ es igual o inferior a 0,1
  entra como cero. La frase no se reproduce, así que una categoría predicha
  igual o inferior a 0,1 cuenta aquí y no en la valoración que la fórmula
  dice realizar.
- **Evidencia:** la fórmula y su lista de símbolos en la página impresa 23,
  y la frase bajo la fórmula (6) en la página impresa 20 del otro borrador.
  Verificado en la página 23 del PDF (p. impresa 23) de la
  E DIN 45672-3:2023-02 y en la página 20 del PDF (p. impresa 20) de la
  E DIN 4150-2:2023-08.
- **Consecuencia para las tablas de la propia norma:** ninguna; la
  categoría del anexo C está en 0,4.
- **Comportamiento de la biblioteca:** la cadena de
  [`predict_train_category`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/railway_prediction.py)
  acaba en
  [`train_assessment_severity`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/train_categories.py),
  que aplica la regla de la valoración que representa.
- **Estado:** sin comunicar; el documento es un borrador en consulta.

## DIN 4150-1:2001-06, fórmulas (5) y (6) (una distancia cuya unidad está impresa en milímetros)

- **Localización:** las listas de símbolos de la fórmula (5) en la página
  impresa 9 (página 9 del PDF de la copia leída aquí, que imprime sus folios
  sin desplazamiento) y de la fórmula (6) en la página impresa 10.
- **Lo impreso:** «$R$ die Entfernung von der Sprengstelle, in mm;» bajo la
  fórmula (5) y «$R$ die Entfernung von der Fallstelle, in mm;» bajo la fórmula
  (6), cada una con «$R_0$ = 1 m (Bezugsgröße)» en la línea siguiente.
- **El problema:** la distancia entra en las dos fórmulas solo como el
  cociente $R/R_0$ frente a una referencia de 1 m, la fórmula (2) de la página
  impresa 5 define $R$ «in m», y todos los ejes de distancia del anexo A están
  en metros. Una distancia en milímetros frente a una referencia en metros
  pondría el cociente mil veces demasiado alto.
- **Evidencia:** las dos listas de símbolos de las páginas impresas 9 y 10 y
  la definición de $R$ bajo la fórmula (2) en la página impresa 5. Verificado
  en la página 9 del PDF (p. impresa 9), la página 10 del PDF (p. impresa 10)
  y la página 5 del PDF (p. impresa 5) de la DIN 4150-1:2001-06.
- **Consecuencia para las tablas de la propia norma:** ninguna; la norma no
  imprime valores de $k$, $b$ ni $m$ con los que calcular nada.
- **Comportamiento de la biblioteca:**
  [`blast_peak_velocity_mm_s`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/immission/prediction.py)
  e `impact_peak_velocity_mm_s` toman la distancia en metros frente a la
  referencia de 1 m, y sus docstrings dicen que lo impreso pone milímetros.
- **Estado:** sin comunicar.

## DIN 4150-1:2001-06, apartado 5.2.3 (una frecuencia de trabajo baja escrita como alta)

- **Localización:** la primera frase de la página impresa 11 (página 11 del
  PDF), tercer párrafo del apartado 5.2.3.
- **Lo impreso:** «Vibrationsbäre mit tiefer Arbeitsfrequenz ($f$ > 30 Hz)
  können …».
- **El problema:** una frecuencia de trabajo baja no puede ser una por encima
  de 30 Hz, y el párrafo anterior, en la página impresa 10, acaba de decir que
  los vibradores con frecuencias de trabajo altas, $f$ > 35 Hz, son los
  favorables. El signo está al revés; la lectura pretendida es una frecuencia
  por debajo de 30 Hz.
- **Evidencia:** la frase de la página impresa 11 y el «$f$ > 35 Hz» del 5.2.3
  en la página impresa 10. Verificado en la página 11 del PDF (p. impresa 11) y
  en la página 10 del PDF (p. impresa 10) de la DIN 4150-1:2001-06.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:** nada que adoptar; el apartado es texto.
- **Estado:** sin comunicar.

## DIN 4150-1:2001-06, anexo A, figura A.2 (una leyenda que intercambia dos estilos de línea)

- **Localización:** figura A.2 en la página impresa 18 (página 18 del PDF).
- **Lo impreso:** la leyenda dice «—— Ausgleichsgerade Z-Komponente» y «–·–
  Ausgleichsgerade X-Komponente», con ▽ para las medidas Z y ○ para las X.
- **El problema:** en el dibujo la línea de trazo y punto es la más empinada
  de las tres y pasa por las marcas ▽, que son los valores Z que la figura A.1
  imprime en la página impresa 17, de 6,90 mm/s a 270 m a 0,12 mm/s a 1470 m;
  la línea continua es la más tendida y pasa por las marcas ○ de la componente
  X. La línea de trazos y las marcas □ de la componente Y concuerdan con su
  leyenda. Los dos estilos están intercambiados entre la leyenda y el dibujo.
- **Evidencia:** las líneas y las marcas de la página impresa 18 frente a los
  picos Z de la página impresa 17. Verificado en la página 18 del PDF
  (p. impresa 18) y en la página 17 del PDF (p. impresa 17) de la
  DIN 4150-1:2001-06.
- **Consecuencia para las tablas de la propia norma:** ninguna; la figura es
  una ilustración y el anexo A dice que sus números no son base para una
  previsión.
- **Comportamiento de la biblioteca:** nada que adoptar.
- **Estado:** sin comunicar.

## DIN 4150-1:2001-06, anexo A, A.5.1 (un momento excéntrico con la unidad de una fuerza)

- **Localización:** la línea «Vorgang» de A.5.1 en la página impresa 25
  (página 25 del PDF).
- **Lo impreso:** «Vibrator (Exzentermoment 320 N, Frequenz $f$ = 32 Hz)».
- **El problema:** un momento excéntrico es una masa a un radio, en kg·m o
  N·m, que es como A.5.2 imprime en la página impresa 27 su «statisches Moment
  5 kg · m»; un newton es una fuerza. Lo que se quiso decir, 320 N·m o
  32 kg·m, no se puede saber por la página.
- **Evidencia:** la línea de la página impresa 25 y el momento de A.5.2 en la
  página impresa 27. Verificado en la página 25 del PDF (p. impresa 25) y en la
  página 27 del PDF (p. impresa 27) de la DIN 4150-1:2001-06.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:** nada que adoptar; el caso es una
  ilustración.
- **Estado:** sin comunicar.

## DIN 4150-1:2001-06, anexo A, figura A.18 (un punto rotulado todos los grupos en el recuento de una nave)

- **Localización:** la figura A.18 y su leyenda en la página impresa 33
  (página 33 del PDF de la copia leída aquí, que imprime sus folios sin
  desplazamiento), frente a la figura A.16 y A.8.1 en la página impresa 32.
- **Lo impreso:** el sexto punto medido está dibujado en unas 110 máquinas y
  su leyenda dice «6) alle Gruppen»; A.8.1 dice «Betrieb bis 252 Maschinen
  in zwei Maschinensälen», y la tabla de la figura A.16 cuenta 63, 7, 8, 6,
  57, 1, 23, 31, 12, 32, 4, 3 y 5 máquinas en los grupos A a Ge, que son
  252.
- **El problema:** todos los grupos son 252 máquinas, y 110 es lo que suman
  los grupos E, F y G de la nave derecha, la más cercana al punto de medida
  (23, 31 y 56). El punto anterior, «Gruppen F und G», está en 87, que es lo
  que suman esos dos, así que la abscisa es el recuento de los grupos en
  marcha; el rótulo del sexto punto no lo es.
- **Evidencia:** el punto y su leyenda en la página impresa 33, la frase de
  A.8.1 y la tabla en la página impresa 32. Verificado en la página 33 del
  PDF (p. impresa 33) y en la página 32 del PDF (p. impresa 32) de la
  DIN 4150-1:2001-06.
- **Consecuencia para las tablas de la propia norma:** ninguna; el texto
  bajo la figura dice que los valores medidos se quedan quietos por encima
  de unas 60 máquinas porque los grupos que se conectan después están más
  lejos, que es lo que la figura muestra de cualquier modo.
- **Comportamiento de la biblioteca:** nada que tomar; las filas de
  conformidad de la figura A.18 leen la curva dibujada, no los puntos
  medidos.
- **Estado:** sin comunicar.

## ISO 11546-1:1995, 9.4 c) (una magnitud remitida al apartado de incertidumbre)

- **Localización:** el punto 9.4 c) 2) en la página impresa 9 (página 16 del
  PDF de la copia BS EN ISO 11546-1:2009 leída aquí, cuyos folios van siete por
  detrás de las páginas del PDF), frente al apartado 8 de la página impresa 8.
- **Lo impreso:** «2) A-weighted sound power insulation, $D_{WA}$ (see clause
  8);», listado bajo «9.4 Acoustical data» entre las magnitudes que debe
  registrar una medida con la fuente sonora real.
- **El problema:** el apartado 8 de esta parte es «Uncertainty», y no dice nada
  de $D_{WA}$: enuncia las desviaciones típicas que cabe esperar de cada método
  y manda un valor declarado a la ISO 4871. $D_{WA}$ se define en la definición
  3.9 y se calcula con la ecuación (2) del apartado 6.2. Quien siga la remisión
  llega a un apartado que no define la magnitud que fue a buscar.
- **Evidencia:** el punto 9.4 c) 2) de la página impresa 9 y el título y el
  cuerpo del apartado 8 de la página impresa 8. Verificado en la página 16 del
  PDF (p. impresa 9) y en la página 15 del PDF (p. impresa 8) de la
  ISO 11546-1:1995 tal como se publica en la BS EN ISO 11546-1:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna; la ecuación (2)
  está impresa correctamente donde le toca.
- **Comportamiento de la biblioteca:**
  [`sound_power_insulation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  devuelve $D_{WA}$ de la ecuación (2) y cita el apartado 6.2 para ella.
- **Estado:** sin comunicar.

## ISO 11546-1:1995, apartado 8 (una palabra mal escrita en la declaración de incertidumbre)

- **Localización:** el primer párrafo del apartado 8 en la página impresa 8
  (página 15 del PDF).
- **Lo impreso:** «When the actual sound source or the artificial sound source
  method is used, it is expected that measurements in confirmity with this part
  of ISO 11546 will yield standard deviations which are equal to or less than
  those given in the International Standard used».
- **El problema:** «confirmity» por «conformity». La frase es la que ata toda
  la declaración de incertidumbre de la parte a una condición, así que la
  palabra mal escrita es justo la que dice cuándo vale esa declaración.
- **Evidencia:** el primer párrafo del apartado 8 en la página impresa 8.
  Verificado en la página 15 del PDF (p. impresa 8) de la ISO 11546-1:1995 tal
  como se publica en la BS EN ISO 11546-1:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:** nada que tomar; ningún número depende de
  ello.
- **Estado:** sin comunicar.

## ISO 11546-2:1995, anexo C, tabla C.1 (una columna encabezada con una norma que no existe)

- **Localización:** la tabla C.1 en la página impresa 12 (página 18 del PDF
  de la copia BS EN ISO 11546-2:2009 leída aquí, cuyos folios van seis por
  detrás de las páginas del PDF).
- **Lo impreso:** la última columna de la tabla se encabeza «ISO 10204», con
  las llamadas 3) y 4), sobre las celdas $K_2 \leq 7$ y $\Delta L \geq 6$. La
  nota 4) al pie de esa misma tabla dice «If $K_2 \leq 2$, the method
  specified in ISO 11204 is classified as an engineering method».
- **El problema:** la ISO 10204 es una norma de documentos de inspección de
  productos metálicos y no tiene nada que ver con la acústica. La columna es
  la de la ISO 11204, como dice su propia nota al pie y como dice el párrafo
  que hay sobre la tabla: el anexo abre nombrando «ISO 3743-1, ISO 3744,
  ISO 3746, ISO 3747, ISO 9614-1, ISO 9614-2, ISO 11201, ISO 11202 and
  ISO 11204», sin ninguna ISO 10204 entre ellas, y repite la lista antes del
  paso a).
- **Evidencia:** el encabezado de columna y su nota 4) en la tabla C.1 de la
  página impresa 12, frente a las dos listas de esa misma página. Verificado
  en la página 18 del PDF (p. impresa 12) de la ISO 11546-2:1995 tal como se
  publica en la BS EN ISO 11546-2:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna; las dos
  celdas bajo el encabezado son los requisitos de la ISO 11204 y son
  correctas.
- **Comportamiento de la biblioteca:**
  [`TEST_ENVIRONMENT_REQUIREMENTS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  indexa esa columna como `"ISO 11204"`, y un test comprueba que no existe
  ninguna clave `"ISO 10204"`.
- **Estado:** sin comunicar.

## ISO 11546-2:1995, definición 3.11 (una estimación que remite al anexo equivocado)

- **Localización:** la definición 3.11 en la página impresa 3 (página 9 del
  PDF), frente a los anexos C y D de las páginas impresas 12 y 15.
- **Lo impreso:** «**3.11 estimated noise insulation due to the enclosure,**
  $D_{WA,e}$ or $D_{pA,e}$: Calculated reduction in A-weighted sound power or
  sound pressure level obtained from $D_W$ or $D_p$, measured in accordance
  with this part of ISO 11546, and a specific noise spectrum. (See annex C.)»
- **El problema:** el anexo C de esta parte es «Guidelines for evaluating the
  applicability of different test environments for *in situ* measurements», y
  no calcula esa estimación. La magnitud que la definición nombra se calcula
  en el **anexo D**, «Estimated noise insulation due to the enclosure for a
  specific noise spectrum». La remisión es la que lleva la parte 1, donde la
  estimación sí es el anexo C; la parte 2 intercaló antes el anexo del
  entorno de ensayo y el puntero no se movió.
- **Evidencia:** la definición de la página impresa 3 y los títulos de los
  anexos C y D de las páginas impresas 12 y 15. Verificado en la página 9 del
  PDF (p. impresa 3), la página 18 del PDF (p. impresa 12) y la página 21 del
  PDF (p. impresa 15) de la ISO 11546-2:1995 tal como se publica en la
  BS EN ISO 11546-2:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna; la fórmula es
  la misma en las dos partes.
- **Comportamiento de la biblioteca:**
  [`estimated_a_weighted_insulation`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  cita el anexo C de la parte 1 y el anexo D de la parte 2, que es donde cada
  una la imprime.
- **Estado:** sin comunicar.

## ISO 11546-2:1995, anexo C, pasos c) y d) (un subíndice en la mitad equivocada de un cociente)

- **Localización:** el procedimiento por letras del anexo C en la página
  impresa 12 (página 18 del PDF).
- **Lo impreso:** «c) Calculate $S_V/S$ for the actual situation
  ($S_V/S_\text{actual}$)» y «d) If $S_V/S_\text{actual} \geq S_V/S$
  determined from figure C.1, the test environment is estimated to be
  applicable».
- **El problema:** «actual» califica a la situación, no a la superficie de
  medida, pero está impreso como subíndice de $S$ sola, de modo que la
  expresión se lee como $S_V$ partido por una «$S$ actual» y el paso d) se
  lee como la comparación de dos cocientes distintos del mismo $S_V$. En el
  procedimiento hay una sola superficie de medida; los dos lados de la
  desigualdad son el cociente del recinto que se juzga y el cociente leído en
  la figura C.1 para el mismo $\alpha$.
- **Evidencia:** los pasos c) y d) y el párrafo que los precede en la página
  impresa 12. Verificado en la página 18 del PDF (p. impresa 12) de la
  ISO 11546-2:1995 tal como se publica en la BS EN ISO 11546-2:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna; la figura C.1
  es una curva y el anexo no imprime ningún caso resuelto.
- **Comportamiento de la biblioteca:**
  [`test_environment_applicability`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  devuelve `actual_area_ratio` y `required_area_ratio` como dos cocientes con
  nombre de la misma superficie de medida, de modo que la comparación no
  puede leerse al revés.
- **Estado:** sin comunicar.

## ISO 11546-2:1995, anexo C, primer párrafo (una palabra mal escrita en la lista de normas relacionadas)

- **Localización:** el párrafo de apertura del anexo C en la página impresa
  12 (página 18 del PDF).
- **Lo impreso:** «In these standards, detailed requirements concerning
  testing conditions and evironments are stated».
- **El problema:** «evironments» por «environments». La frase es la que
  establece para qué sirve todo el anexo, y el título del anexo, el párrafo
  siguiente y la tabla C.1 escriben la palabra correctamente.
- **Evidencia:** el párrafo de apertura de la página impresa 12, frente al
  título del anexo en esa misma página. Verificado en la página 18 del PDF
  (p. impresa 12) de la ISO 11546-2:1995 tal como se publica en la
  BS EN ISO 11546-2:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:** nada que tomar; ningún número depende
  de ello.
- **Estado:** sin comunicar.

## ISO 11957:1996, 6.2 (una distancia de baja frecuencia que relaja la regla que tiene encima)

- **Localización:** el apartado 6.2 «Cabin locations» en la página impresa 3
  (página 12 del PDF de la copia BS EN ISO 11957:2009 leída aquí, cuyos
  folios van nueve por detrás de las páginas del PDF).
- **Lo impreso:** «For measurements in the frequency range from 100 Hz to
  10 000 Hz, the distance between the cabin and the walls and ceiling of the
  room shall be at least one-half wavelength corresponding to the centre
  frequency of the lowest frequency band of interest. [...] For measurements
  in the frequency range from 50 Hz to 80 Hz, the distance shall be at least
  2 m».
- **El problema:** las dos frases no empalman. Media longitud de onda a
  100 Hz son 1,72 m y crece al bajar la frecuencia, así que a 80 Hz la
  primera regla pediría 2,14 m y a 50 Hz, 3,43 m. La frase que toma el relevo
  por debajo de 100 Hz **rebaja** por tanto el requisito, a 2 m, justo donde
  el argumento de la longitud de onda pide más. La NOTE 11 del apartado 6.4
  hace de 50 Hz a 10 kHz el intervalo preferente, así que la rama relajada es
  la que usa una medida preferente.
- **Evidencia:** las dos frases del apartado 6.2 en la página impresa 3,
  frente a la NOTE 11 del apartado 6.4 en la página impresa 4. Verificado en
  la página 12 del PDF (p. impresa 3) y la página 13 del PDF (p. impresa 4)
  de la ISO 11957:1996 tal como se publica en la BS EN ISO 11957:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna; la norma no
  imprime ninguna disposición resuelta.
- **Comportamiento de la biblioteca:**
  [`minimum_cabin_clearance_m`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  devuelve los 2 m planos de 50 Hz a 80 Hz y media longitud de onda por
  encima, exactamente como está impreso, y un test comprueba que la rama baja
  es la menor de las dos para que la no monotonía no pueda «arreglarse» en
  silencio.
- **Estado:** sin comunicar.

## ISO 11957:1996, 6.2 (una distancia a los difusores que repite la distancia a las paredes)

- **Localización:** la segunda frase de la regla de distancias del apartado
  6.2 en la página impresa 3 (página 12 del PDF).
- **Lo impreso:** «[...] shall be at least one-half wavelength corresponding
  to the centre frequency of the lowest frequency band of interest.
  Furthermore, the distance between the cabin and any diffusing elements in
  the room shall be at least one-half of this wavelength».
- **El problema:** «this wavelength» es la longitud de onda de la banda más
  baja, así que «one-half of this wavelength» es la distancia que la frase
  anterior acaba de exigir a las paredes y al techo. Introducida por
  «Furthermore», la frase se lee como un requisito añadido y enuncia el
  mismo. O es una repetición, o «this wavelength» quería decir la media
  longitud de onda y la distancia a los difusores es un cuarto de la longitud
  de onda; lo impreso no lo decide.
- **Evidencia:** las dos frases, leídas una tras otra, en la página impresa
  3. Verificado en la página 12 del PDF (p. impresa 3) de la ISO 11957:1996
  tal como se publica en la BS EN ISO 11957:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:**
  [`minimum_cabin_clearance_m`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  devuelve una sola distancia para las paredes, el techo y los elementos
  difusores, que es la lectura que llevan las palabras, y lo dice.
- **Estado:** sin comunicar.

## ISO 11957:1996, 6.7 (un método de corrección nombrado con una palabra que no lo es)

- **Localización:** la frase del ruido de fondo del apartado 6.7 en la página
  impresa 5 (página 14 del PDF).
- **Lo impreso:** «If the difference is in the range 6 dB to 10 dB, the result
  of the measurement shall be corrected for the effect of the background
  noise in acdance with ISO 3741».
- **El problema:** «acdance» por «accordance», en la frase que dice qué
  corrección aplicar al nivel de ruido interior. El apartado 6.4 imprime la
  misma instrucción correctamente dos páginas antes.
- **Evidencia:** la frase de la página impresa 5, frente a la frase
  correspondiente del apartado 6.4 en la página impresa 4. Verificado en la
  página 14 del PDF (p. impresa 5) y la página 13 del PDF (p. impresa 4) de
  la ISO 11957:1996 tal como se publica en la BS EN ISO 11957:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:**
  [`internal_noise_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  aplica la corrección de la ISO 3741 dentro de la ventana de 6 dB a 10 dB
  que fija esa misma frase.
- **Estado:** sin comunicar.

## ISO 11957:1996, 7.2.1 (una regla de margen sobre el fondo con dos palabras traspuestas)

- **Localización:** el párrafo del espectro de la fuente del apartado 7.2.1
  en la página impresa 6 (página 15 del PDF).
- **Lo impreso:** «The output shall be sufficiently high to give a sound
  pressure level inside the cabin exceeding the background noise level by at
  least 6 dB and preferably more by than 12 dB for all frequency bands of
  interest».
- **El problema:** «preferably more by than 12 dB» por «preferably by more
  than 12 dB». El mismo requisito está impreso correctamente en el apartado
  6.4, dos páginas antes, que es lo que zanja la lectura buscada.
- **Evidencia:** la frase de la página impresa 6, frente a esa misma frase
  del apartado 6.4 en la página impresa 4. Verificado en la página 15 del PDF
  (p. impresa 6) y la página 13 del PDF (p. impresa 4) de la ISO 11957:1996
  tal como se publica en la BS EN ISO 11957:2009.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:**
  [`MIN_SIGNAL_TO_BACKGROUND_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/cabin_insulation.py)
  y `PREFERRED_SIGNAL_TO_BACKGROUND_DB` llevan 6 dB y 12 dB, y el aviso
  nombra el margen que realmente se alcanzó.
- **Estado:** sin comunicar.

## ISO 11820:1996, ecuaciones (20) y (22) (una razón de temperaturas del revés)

- **Ubicación:** la ecuación (20) de 9.1.3 en la página impresa 11 (página 19
  del PDF) y la ecuación (22) de 9.1.4 en la página impresa 12 (página 20 del
  PDF).
- **Lo impreso:**
  $K_2 - K_1 = 5 \lg\!\left(\dfrac{273 + \theta_1}{273 + \theta_2}\right)$ dB,
  con $\theta_1$ "the temperature, in degrees Celsius, on the receiver side" y
  $\theta_2$ "on the source side"; y, para la pérdida por inserción,
  $K_\mathrm{II} - K_\mathrm{I} = 5 \lg\!\left(\dfrac{273 + \theta_\mathrm{I}}
  {273 + \theta_\mathrm{II}}\right)$ dB, con $\theta_\mathrm{I}$ la temperatura
  con el silenciador y $\theta_\mathrm{II}$ sin él. La frase que sigue a la
  ecuación (20) lo explica: "The different temperatures determine different
  sound velocities which result in different conversion factors from squared
  sound pressure to sound power."
- **El problema:** la razón está invertida, y la frase dice por qué. La
  corrección de campo $K$ es una conversión del cuadrado de la presión acústica
  a potencia acústica, y la norma fija su signo en su propia página: las
  ecuaciones (5) y (7) de la página impresa 3 la suman,
  $L_{W1} = \overline{L_{p1}} + 10\lg(S_1/S_0)$ dB $+\ K_1$ y
  $L_{W2} = \overline{L_{p2}} + 10\lg(S_2/S_0)$ dB $+\ K_2$, con el subíndice 1
  en el lado receptor y el 2 en el lado fuente, que es el mismo reparto que
  usa la ecuación (20). Por tanto $K = -10\lg(\rho c / (\rho c)_0)$ + const. La
  frase sólo cuenta el cambio de $c$, que crece como $\sqrt{T}$, y olvida que
  la densidad baja: la propia ecuación (29) de la norma, en la página impresa
  12, da $\rho_\mathrm{u} = M\,p_\mathrm{amb}/[R(273 + \theta_\mathrm{u})]$, de
  modo que a presión ambiente constante $\rho c$ decae como $T^{-1/2}$ y $K$
  crece como $+5 \lg T$. El gas más caliente necesita entonces la corrección
  *más* positiva, y la diferencia es
  $5 \lg[(273 + \theta_2)/(273 + \theta_1)]$, la inversa de lo impreso. Las dos
  formas impresas llevan la misma inversión, así que es la ecuación y no un
  subíndice mal compuesto en una de ellas.
- **Evidencia:** las tres ecuaciones y las dos leyendas leídas en la página. La
  ecuación (20) con su leyenda y la frase explicativa, y las ecuaciones (18) y
  (19), están en la página 19 del PDF (página impresa 11); las ecuaciones (5) y
  (7) con sus leyendas, en la página 11 del PDF (página impresa 3); la ecuación
  (22) con su leyenda y la ecuación (29) con $R$ = 8 314,4 N·m/(kmol·K), en la
  página 20 del PDF (página impresa 12). Todo de la BS EN ISO 11820:1997, que
  imprime la EN ISO 11820:1996. Otro documento ISO imprime la misma magnitud
  del derecho: la corrección por magnitudes de referencia de la ISO 3741:2010,
  que su propia leyenda llama "a function of the characteristic impedance of
  the air", es $C_1 = -10\lg(p_\mathrm{s}/p_{\mathrm{s},0})$ dB
  $+\ 5\lg[(273{,}15 + \theta)/\theta_0]$ dB, sumada a $L_W$ en la ecuación
  (20) de la página 31 del PDF (página impresa 22) de la BS EN ISO 3741:2010, y
  crece con la temperatura.
- **Consecuencia para las tablas de la propia norma:** la ISO 11820 no imprime
  ningún ejemplo resuelto, así que nada del documento queda mal a la vista. En
  uso, el signo cuesta el doble de la corrección: con un receptor a 20 °C y una
  fuente a 200 °C lo impreso da -1,04 dB donde la impedancia da +1,04 dB, de
  modo que tanto la pérdida por transmisión de la ecuación (19) como la pérdida
  por inserción de la ecuación (21) salen 2,08 dB bajas.
- **Comportamiento de la biblioteca:**
  [`temperature_field_correction_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_in_situ.py)
  devuelve la ecuación tal como está impresa, porque quien tenga delante la
  ISO 11820 tiene que encontrar el número de la norma, y su docstring nombra
  esta entrada. La fila de conformidad "ISO 11820:1996 Eqs. (20) and (22)" fija
  la forma impresa.
- **Estado:** no reportada.

## ISO 10847:1997, tabla 1 (una clase a contraviento con el extremo inferior positivo)

- **Ubicación:** la tabla 1, "Class of wind conditions", en la página impresa
  6 (página 10 del PDF).
- **Lo impreso:** el bloque de distancias cortas de la tabla enumera tres
  clases frente a la componente vectorial de la velocidad del viento en m/s:
  "Downwind + 1 to + 5", "Calm − 1 to + 1" y "Upwind + 1 to − 5".
- **El problema:** "+ 1 to − 5" no es un intervalo. Sus dos extremos van al
  revés, y el inferior es el valor en el que empieza la clase a favor del
  viento dos filas más arriba, así que leída al pie de la letra la clase a
  contraviento empezaría dentro de la de a favor y retrocedería a través de la
  de calma. El carácter defectuoso es el signo del extremo inferior: la clase
  a contraviento es − 1 a − 5, el espejo de la fila a favor, que es además lo
  que significa "upwind" para una componente que 6.3.1 define positiva a lo
  largo de la línea fuente-receptor.
- **Evidencia:** las tres filas de distancias cortas leídas juntas en la
  página impresa 6, frente al bloque de todas las distancias que tienen
  encima, que imprime esas mismas filas a favor y en calma y ninguna a
  contraviento. Verificado en la página 10 del PDF (página impresa 6) de la
  ISO 10847:1997.
- **Consecuencia para las tablas de la propia norma:** ninguna. Ninguna otra
  cláusula calcula con el intervalo.
- **Comportamiento de la biblioteca:**
  [`WIND_CLASSES`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py)
  lleva la clase a contraviento como − 5 m/s a − 1 m/s y
  [`wind_class`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py)
  la devuelve sólo para componentes negativas y distancia corta, que es donde
  la tabla la imprime.
- **Estado:** no reportada.

## ISO 10847:1997, 8.2.2 (una prima a la que se le piden dos significados)

- **Ubicación:** las dos ecuaciones de diferencia de niveles de 8.2.2 y la
  lista de símbolos que las sigue, en la página impresa 11 (página 15 del
  PDF).
- **Lo impreso:** $\Delta L_B = L_{\mathrm{ref},B} - (L_{r,B} - C_r)$ y
  $\Delta L_A = L_{\mathrm{ref},A} - (L_{r,A} - C'_r)$, y a continuación
  "$C_r$ and $C'_r$ are correction factors for the type of receiver position;
  for "hemi free-field": $C_r$ = 0 dB; for "on reflecting surfaces": $C'_r$ =
  6 dB".
- **El problema:** la prima carga con dos significados en la misma cláusula.
  En las ecuaciones separa la campaña "antes" de la "después", porque todos
  los demás símbolos que aparecen en ellas llevan el subíndice B o A. En las
  definiciones separa un tipo de posición de receptor del otro. Tomadas al pie
  de la letra, las dos lecturas juntas componen una regla que no dice ninguna
  otra parte de la norma: que la campaña "antes" se hace en campo semilibre y
  la "después" contra una superficie reflectante.
- **Evidencia:** las dos ecuaciones y la lista de símbolos en la página
  impresa 11, resueltas por la NOTA que cierra esa misma cláusula, "It is
  preferable to choose receiver positions where corrections $C_r$ and $C'_r$
  are essentially the same", que sólo es un consejo si la corrección de cada
  campaña sigue a su propia posición de receptor en lugar de venir fijada por
  la campaña. Verificado en la página 15 del PDF (página impresa 11) de la
  ISO 10847:1997.
- **Consecuencia para las tablas de la propia norma:** ninguna.
- **Comportamiento de la biblioteca:**
  [`measured_insertion_loss_indirect`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py)
  toma `receiver_type_before` y `receiver_type_after`, cada uno
  'hemi_free_field' o 'reflecting_surface' y ambos con el primero por defecto,
  y saca su corrección de `RECEIVER_CORRECTIONS_DB`, que lleva los 0 dB y 6 dB
  impresos. El resultado arrastra las dos correcciones para que un informe
  muestre cuál se aplicó a cada campaña.
- **Estado:** no reportada.

## ISO 14257:2001, anexo C (un ejemplo que corrige uno de sus dos resultados)

- **Ubicación:** C.1 en la página impresa 17 (página 27 del PDF), frente a las
  tablas C.7 y C.9 en la página impresa 23 (página 33 del PDF) y las tablas C.8
  y C.10 en las páginas impresas 23 y 24 (páginas 33 y 34 del PDF).
- **Lo impreso:** C.1 enumera las cuatro cosas que se cumplen en el ejemplo, y
  la segunda es que "the experimental reference curve of the sound source is
  known and used for correcting the values measured in the workroom". La tabla
  C.5 se titula después "Values of $D = L_p - L_W$, in octave bands (corrected
  for background noise)" y la C.6 "Values of $D = L_p - L_W$ ... corrected for
  background noise **and using the experimental reference curves of the
  source**".
- **El problema:** las cuatro tablas de resultados no salen todas de la misma
  curva. Todos los valores de $\mathrm{DL}_2$ de las tablas C.7 y C.8 salen de
  la curva corregida de la tabla C.6, y todos los de
  $\mathrm{DL}_\mathrm{f}$ de las tablas C.9 y C.10 salen de la curva sin
  corregir de la tabla C.5. Si se cambia una por la otra, 28 de los 36
  resultados impresos se salen del redondeo de la tabla en la que están.
- **Evidencia:** las dos curvas están impresas enteras, así que se pueden
  recorrer los dos caminos. Partiendo de la tabla C.6 tal como está, el rango
  medio a 1 kHz da $\mathrm{DL}_2$ = 4,39 dB frente a los 4,4 impresos y
  $\mathrm{DL}_\mathrm{f}$ = 6,73 dB frente a los 7,3; partiendo de la C.5 se
  obtienen 4,73 dB y 7,29 dB. La misma división se da en los tres rangos de
  distancia y en las seis bandas de octava, y en las dos tablas del espectro
  rosa ponderado A. Verificado en las páginas 27, 31 y 33 del PDF (páginas
  impresas 17, 21 y 23) de la EN ISO 14257:2001 publicada como
  BS EN ISO 14257:2001.
- **Consecuencia para las tablas de la propia norma:** ninguna para
  $\mathrm{DL}_2$, que es una pendiente y apenas se mueve con una corrección
  casi constante con la distancia. Para $\mathrm{DL}_\mathrm{f}$, que es un
  nivel, la diferencia llega a 1,4 dB en el rango cercano.
- **Comportamiento de la biblioteca:**
  [`corrected_distribution_value`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py)
  aplica el anexo B cuando se le pide y nunca por su cuenta, así que es quien
  llama el que elige de qué curva sale cada descriptor. La fila de conformidad
  "ISO 14257:2001 Annex C (C.1 against Tables C.7 and C.9)" fija la división, y
  `test_the_annex_corrects_the_decay_but_not_the_excess` en
  [`tests/room/test_spatial_decay.py`](https://github.com/jmrplens/phonometry/blob/main/tests/room/test_spatial_decay.py)
  guarda los dos números para que ninguno se mueva.
- **Estado:** no reportada.

## ISO 14257:2001, ecuación (5) frente a la ecuación (8) (un logaritmo redondeado)

- **Ubicación:** la ecuación (5) de 6.3 en la página impresa 9 (página 19 del
  PDF) y la ecuación (8) de 6.4.3 en la página impresa 10 (página 20 del PDF).
- **Lo impreso:** la ecuación (5) abre con el factor $-0,3$ delante de la
  pendiente de mínimos cuadrados; la ecuación (8), una página después, divide
  $\mathrm{DL}_2(r_n,r_m)$ entre $\lg 2$.
- **El problema:** las dos son la misma conversión, de una tasa por década a
  una tasa por duplicación de distancia, escrita dos veces con distinta
  precisión. $\lg 2$ es 0,301 03, así que el 0,3 impreso se queda un 0,34 %
  corto, y un documento que imprime la forma exacta en una página no tiene por
  qué redondearla en la anterior.
- **Evidencia:** las dos ecuaciones en páginas enfrentadas, las dos
  reproducidas en la entrada anterior a partir de las tablas impresas.
  Verificado en las páginas 19 y 20 del PDF (páginas impresas 9 y 10) de la
  EN ISO 14257:2001.
- **Consecuencia para las tablas de la propia norma:** ninguna que el redondeo
  impreso pueda mostrar: el ejemplo del anexo C se tabula con un decimal y un
  0,34 % de una pendiente de 4 dB son 0,014 dB.
- **Comportamiento de la biblioteca:**
  [`DECADE_TO_DOUBLING`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) lleva el 0,3
  impreso, porque la constante impresa es la que reproduce los resultados
  impresos, y
  [`level_excess_at`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) divide entre
  $\lg 2$ donde lo imprime la ecuación (8). No hay que unificarlos.
- **Estado:** no reportada.

## ISO 14257:2001, ecuación (4) frente a la tabla 1 (una segunda constante redondeada)

- **Ubicación:** la ecuación (4) de 4.2.3 y la tabla 1 justo debajo, las dos en
  la página impresa 4 (página 14 del PDF), frente a la última columna de la
  tabla C.6 en la página impresa 21 (página 31 del PDF) y a la tabla C.10 en
  la página impresa 24 (página 34 del PDF).
- **Lo impreso:** la ecuación (4) cierra con
  $D_\text{Norm} = 10\lg\!\left(\sum_j 10^{(D_j + P_j)/10}\right)$ dB
  $-\ 6,2$ dB, y la tabla 1 da los $P_j$ del espectro de referencia de ruido
  rosa ponderado A como $-16{,}1$; $-8{,}6$; $-3{,}2$; $0$; $1{,}2$; $1$ dB de
  125 Hz a 4 kHz.
- **El problema:** los 6,2 dB son la suma energética de los $P_j$, que es lo
  que normaliza el espectro ponderado a total unidad para que una curva plana
  vuelva sin cambiar, y los seis $P_j$ impresos suman 6,251 5 dB, que redondea
  a 6,3 y no a 6,2. La constante impresa se queda 0,051 dB corta respecto a la
  tabla impresa. Las dos son redondeos de la misma curva hechos por separado:
  los $P_j$ son la ponderación A de la IEC 61672-1 en los seis centros de
  octava, $-16{,}19$; $-8{,}67$; $-3{,}25$; $0$; $1{,}20$; $0{,}96$ dB,
  impresos a un decimal tal como los tabula esa norma, y la suma energética
  de la curva sin redondear es 6,23 dB, que se imprime como el 6,2 de la
  ecuación (4). Cada redondeo es correcto por sí solo y la ecuación impresa
  no lo es: evaluada tal como está impresa, devuelve una curva plana 0,05 dB
  alta. Es un desliz de la misma clase que el $\lg 2$ redondeado de la
  entrada anterior, una constante impresa a un decimal donde el documento
  calcula con más, y la ecuación (3), de la que la ecuación (4) es el caso
  particular para el espectro de la tabla 1, lleva la misma normalización
  exacta, como logaritmo de su denominador.
- **Evidencia:** la ecuación (4), su leyenda y la tabla 1 leídas en la página
  en cuatro impresiones, que coinciden carácter por carácter: ISO
  14257:2001(E), página 10 del PDF (página impresa 4); EN ISO 14257:2001 tal
  como la publica la BS EN ISO 14257:2001, página 14 del PDF (página impresa
  4); UNE-EN ISO 14257:2002, página 9 del PDF (página impresa 9); y DIN EN ISO
  14257:2011-11, página 13 del PDF (página impresa 9), cuyo prólogo nacional
  enumera los errores técnicos corregidos en el texto alemán y no nombra este.
  El anexo zanja con qué constante se calculó. Recorriendo las tablas C.2 a
  C.4 impresas por el anexo B sin redondear, la última columna de la tabla C.6
  vuelve con los seis $P_j$ impresos y su propia suma, 6,251 5 dB, dentro del
  redondeo impreso en las 11 posiciones (peor 0,041 dB, desviaciones de los
  dos signos), y con los 6,2 dB impresos una unidad alta en la última cifra en
  6 de las 11 (peor 0,092 dB, todas las desviaciones positivas, de +0,011 a
  +0,092 dB). La tabla C.10 hace lo mismo: +0,040, +0,004 y +0,045 dB con la
  suma, +0,091, +0,055 y +0,097 dB con 6,2. La ponderación A sin redondear
  con su propia suma deja las mismas 14 celdas dentro del redondeo (peor
  0,047 dB), así que el anexo no dice cuál de las dos normalizaciones exactas
  usó, solo que usó una; con los 6,2 dB impresos no lo consigue ninguna de
  las dos ponderaciones (8 y 9 de 14 fuera). Sobre las columnas de octava
  impresas, ya redondeadas, de la tabla C.6 el reparto es 3 de 11 frente a 7
  de 11. La tabla C.8, una pendiente, no ve la constante, y los 115,7 dB
  ponderados A de la tabla C.2 la vuelven a sumar. Verificado en la página 14
  del PDF (página impresa 4) de la EN ISO 14257:2001 para la ecuación y la
  tabla, y en las páginas 31 y 34 del PDF (páginas impresas 21 y 24) del mismo
  documento para las dos tablas del anexo.
- **Consecuencia para las tablas de la propia norma:** ninguna para el anexo,
  que se normalizó exactamente. Lo que arrastra los 0,051 dB es cualquier
  evaluación de la ecuación impresa, que queda esa cantidad por encima del
  anexo en cada valor normalizado en frecuencia y puede mover una celda
  impresa de las tablas C.6, C.10 y C.12 en una unidad de la última cifra,
  siempre hacia arriba, y nunca más.
- **Comportamiento de la biblioteca:**
  [`NORMALIZED_OFFSET_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) lleva el 6,2
  impreso, por la misma regla que la entrada anterior y que el 11 de la
  ecuación (2): la constante impresa es la que usará quien compare contra la
  página, y la imprimen cuatro impresiones. La normalización exacta es la
  ecuación (3) con los pesos de la tabla 1 como espectro de la máquina, que
  calcula
  [`spectrum_distribution_value`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py),
  así que la lectura del anexo está disponible sin una segunda constante. La
  fila de conformidad "ISO 14257:2001 Annex C, Table C.6 last column" juzga la
  constante impresa contra el anexo a 0,1 dB y dice por qué, la fila
  "ISO 14257:2001 Eq. (4) against Annex C, Table C.6 last column and Table
  C.10" registra que la suma exacta deja los catorce valores dentro del
  redondeo impreso y la constante impresa no, y
  `test_the_annex_normalized_with_the_table_one_sum_and_not_the_printed_offset`
  en [`tests/room/test_spatial_decay.py`](https://github.com/jmrplens/phonometry/blob/main/tests/room/test_spatial_decay.py)
  sujeta los dos recuentos para que ni la constante ni las tolerancias puedan
  moverse.
- **Estado:** no reportada.

## ISO 14257:2001, anexo C, tablas C.11 y C.12 (resultados que la ecuación (8) no da)

- **Ubicación:** las tablas C.11 y C.12 en la página impresa 24 (página 34 del
  PDF), frente a la ecuación (8) de 6.4.3 en la página impresa 10 (página 20
  del PDF) y a la tabla C.5 en la página impresa 21 (página 31 del PDF).
- **Lo impreso:** la tabla C.11 da $\text{DL}'_\text{fr}$ en seis bandas de
  octava a 4 m, 10 m y 30 m de la fuente: 6,2; 4,0; 4,4; 5,2; 5,3; 3,9 a 4 m;
  7,8; 5,4; 6,4; 6,9; 7,7; 5,8 a 10 m; y 10,6; 7,4; 9,3; 7,2; 9,2; 6,1 a 30 m.
  La tabla C.12 da 4,8; 6,8; 8,0 dB para el espectro de ruido rosa ponderado A
  a esas mismas tres distancias.
- **El problema:** la ecuación (8) es lo único del documento que define
  $\text{DL}'_\text{fr}$, y no produce esos números. Evaluada sobre los tres
  rangos de distancia que usa el propio anexo, 2 m a 5 m, 5 m a 24 m y 24 m a
  48 m, con los $D$ impresos de la tabla C.5, se aparta de la tabla C.11 hasta
  1,55 dB, y las filas impresas no son un resultado de la ecuación (8) para
  ninguna tasa de decaimiento: despejando de la ecuación el $\text{DL}_2$ que
  exigiría la fila intermedia salen valores de -28,9 dB a +20,7 dB por
  duplicación de distancia. Lo que son las tres filas es una lectura de la
  medida impresa en una posición de micrófono, por la ecuación (6) y no por la
  (8): la fila de 4 m es la ecuación (6) en la posición de 4 m de la tabla C.5,
  en las seis bandas; la de 10 m es la media de la ecuación (6) en las
  posiciones de 8 m y 12 m que la flanquean, en las seis bandas; y la de 30 m
  es la ecuación (6) en la posición de 32 m con $20\lg 32$ introducido como
  30 dB en vez de 30,103 dB, en cinco bandas de seis.
- **Evidencia:** las tablas C.10, C.11 y C.12 leídas en la página 34 del PDF
  (página impresa 24), las tablas C.5 y C.6 en la página 31 del PDF (página
  impresa 21) y las ecuaciones (6), (7) y (8) con sus leyendas en la página 20
  del PDF (página impresa 10), todo de la EN ISO 14257:2001. Diecisiete de las
  dieciocho celdas de la tabla C.11 vuelven de los $D$ impresos de la tabla C.5
  con la lectura anterior, con la décima que imprime la tabla; la excepción es
  la celda de 125 Hz de la fila de 30 m, que imprime 10,6 donde esa lectura da
  10,7. Los mismos dígitos están impresos en la adopción española, la
  UNE-EN ISO 14257:2002, tabla C.11 en la página impresa 30, así que es el
  anexo y no una de sus impresiones.
- **Consecuencia para las tablas de la propia norma:** sólo las tablas C.11 y
  C.12. Las tasas de decaimiento y los excesos de las tablas C.7 a C.10 no
  quedan afectados, y nada aguas abajo calcula con la C.11.
- **Comportamiento de la biblioteca:**
  [`level_excess_at`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/spatial_decay.py) implementa la
  ecuación (8) tal como está impresa y devuelve los valores de arriba en vez de
  los de la tabla. La fila de conformidad "ISO 14257:2001 Annex C, Tables C.11
  and C.12" registra la diferencia para que la tabla no se confunda con un
  oráculo de la ecuación (8).
- **Estado:** no reportada.

## ISO 11690-3:1998, tabla C.2 (un valor leído en el borde de su propio ábaco)

- **Ubicación:** la tabla C.2 en la página impresa 20 (página 30 del PDF),
  frente a la figura C.1 en la página impresa 19 (página 29 del PDF).
- **Lo impreso:** la fila de la máquina M8 da $L_{WA} - L_{pA}$ = 29 dB,
  $\Delta L_A$ = 10 dB y $L'_{pA}$ = 88 dB, en una sala cuya área de absorción
  equivalente fija C.2.2 en 195 m2.
- **El problema:** la figura C.1, el ábaco del que el anexo dice que se lee
  $\Delta L_A$, tiene un eje vertical que se acaba en 10 dB, y la curva de una
  diferencia de 29 dB se sale por arriba mucho antes de los 195 m2. El 10 dB de
  la tabla es el borde del ábaco y no una lectura suya, y el nivel que arrastra
  a la última columna se queda 2,4 dB corto.
- **Evidencia:** el eje de la figura C.1 va de 0 dB a 10 dB, y la forma cerrada
  que dibuja el ábaco, la corrección ambiental
  $\Delta L_A = 10 \lg(1 + 4S/A)$ de la ISO 3744 con
  $S/S_0 = 10^{(L_{WA}-L_{pA})/10}$, da 12,4 dB para esa fila. Esa misma
  expresión reproduce las otras siete filas de la tabla dentro de 0,4 dB, que es
  el medio decibelio con el que está dibujado el ábaco. Verificado en las
  páginas 29 y 30 del PDF (páginas impresas 19 y 20) de la EN ISO 11690-3:1998
  publicada como BS EN ISO 11690-3:1999.
- **Consecuencia para las tablas de la propia norma:** la última columna de esa
  única fila. Nada más en el documento calcula con ella.
- **Comportamiento de la biblioteca:**
  [`workstation_level_increase`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/workroom_prediction.py)
  evalúa la expresión y no tiene techo, así que devuelve 12,4 dB donde la tabla
  imprime 10. La fila de conformidad "ISO 11690-3:1998 Annex C, Figure C.1 (the
  eighth machine)" lo fija.
- **Estado:** no reportada.

## ISO 11690-3:1998, anexo B (dos puestos de trabajo con las posiciones y los resultados intercambiados)

- **Ubicación:** las tablas B.5 y B.8 en la página impresa 18 (página 28 del
  PDF), frente a la figura B.1 en la página impresa 16 (página 26 del PDF) y a
  las columnas de inmisión de las tablas B.6 y B.9 en la página impresa 18.
- **Lo impreso:** la tabla B.5 sitúa el puesto de trabajo W1 en $x$ = 3 m,
  $y$ = 12 m, $z$ = 1,6 m y el W2 en 17 m, 4 m, 1,6 m, y la tabla B.8 repite
  esas dos posiciones para el caso B. La tabla B.6 da luego, con las dos
  máquinas instaladas, $L_p$ = 82,1 dB en W1 y 80,3 dB en W2; la tabla B.9 da
  86,2 dB en W1 y 85,7 dB en W2 con la máquina de primera elección, y 83,8 dB y
  82,8 dB con la de segunda. La figura B.1 dibuja esos dos puestos al revés: el
  W1 junto a la máquina M2, a la derecha de la sala, y el W2 solo en la esquina
  superior izquierda.
- **El problema:** los resultados corresponden al reparto de la figura y no al
  de las tablas. La máquina M2 está en 17 m, 3 m, 1 m, así que la posición que
  la tabla B.5 llama W2 queda a 1,2 m de ella y la que llama W1 queda a 11,4 m
  de la máquina más próxima. La posición lejana no puede ser la más
  ruidosa de las dos, y los niveles impresos dicen que lo es. Al recalcular el
  caso A con el método de categoría 1 que prescribe el anexo, en la sala de
  20 m por 15 m por 7 m de la tabla B.2 con el coeficiente de absorción medio
  0,15 de la tabla B.3, salen 82,10 dB en 17 m, 4 m, 1,6 m y 80,26 dB en 3 m,
  12 m, 1,6 m: los dos niveles que imprime la tabla B.6, cada uno bajo la
  etiqueta del otro puesto. La tabla B.8 se contradice en su propia fila, porque
  imprime la posición lejana para W1 y a su lado 82 dB, el nivel cercano
  redondeado.
- **Evidencia:** la figura B.1 con las tablas B.2 y B.3 leídas en la página 26
  del PDF (página impresa 16); la tabla B.4 con las posiciones de las máquinas
  en la página 27 del PDF (página impresa 17); las tablas B.5 a B.9 en la
  página 28 del PDF (página impresa 18). Todo de la EN ISO 11690-3:1998 tal
  como la publica la BS EN ISO 11690-3:1999. Con el reparto de la figura los
  seis niveles de la tabla B.9 vuelven dentro de 0,07 dB, y con el de las
  tablas, los cuatro de W1 y W2 fallan entre 0,48 dB y 1,04 dB (el W3 está en
  el mismo sitio en los dos), mientras que el caso A falla 1,8 dB en las dos
  filas.
- **Consecuencia para las tablas de la propia norma:** las columnas de posición
  de las tablas B.5 y B.8 frente a las etiquetas de las tablas B.6 y B.9, en
  los dos casos del anexo. El texto del caso A sigue a las tablas, porque llama
  al W2 "the workstation of M2", así que está del mismo lado de la
  contradicción. Los números en sí son correctos.
- **Comportamiento de la biblioteca:** las filas de conformidad de los dos
  casos del anexo B leen las coordenadas impresas y nunca las etiquetas, y la
  fila "ISO 11690-3:1998 Annex B, Figure B.1 against Tables B.5 and B.8"
  registra que los resultados vuelven en las posiciones que dibuja la figura y
  en ninguna otra. Los 50 dB de fondo que la tabla B.5 imprime junto a W1
  acompañan a esa etiqueta y no a las coordenadas que tiene al lado, así que se
  oyen en la posición que la figura da a W1, junto a la máquina M2. Vale
  0,004 dB: leído al revés el caso A da 82,09 dB y 80,27 dB en vez de 82,10 dB
  y 80,26 dB, y las dos lecturas redondean a la décima que imprime la tabla
  B.6.
- **Estado:** no reportada.

## ISO 11819-1:1997, anexo E (dispersiones de velocidad que no encajan con la regresión impresa a su lado)

- **Ubicación:** anexo E (informativo), el ejemplo de informe de ensayo, tabla
  "Sound level and speed regression data (uncorrected for temperature)" en la
  página impresa 26 (página 34 del PDF). La edición leída es la BS EN ISO
  11819-1:2001, idéntica a la ISO 11819-1:1997.
- **Lo impreso:** para turismos, pesados de dos ejes y pesados de más de dos
  ejes, la tabla da pendientes de regresión de 32,55, 18,76 y 26,74,
  coeficientes de correlación de 0,79, 0,51 y 0,49, desviaciones típicas del
  nivel sonoro de 2,2, 2,5 y 2,3 dB, velocidades medias de 88,5, 75,8 y
  73,7 km/h y desviaciones típicas de la velocidad de 13,3, 7,5 y 6,4 km/h;
  las dos últimas filas llevan la marca "Value converted from the logarithm of
  speed".
- **El problema:** una recta de mínimos cuadrados del nivel frente a $\lg v$
  cumple exactamente $b = r\,s_L / s_{\lg v}$, así que la pendiente, la
  correlación y la dispersión del nivel impresas en una columna fijan la
  dispersión de $\lg v$ de esa columna: $s_{\lg v} = r\,s_L/b$ = 0,0534 para
  los turismos, 0,0680 para los pesados de dos ejes y 0,0421 para los de más
  de dos ejes (de 0,0518 a 0,0550, de 0,0659 a 0,0700 y de 0,0408 a 0,0435
  dentro del redondeo de los tres datos impresos). Los pesados de dos ejes
  tienen por tanto la dispersión de $\lg v$ más ancha de las tres. El
  cociente entre la desviación típica de la velocidad y su media depende sólo
  de esa dispersión: a primer orden es $\ln 10 \, s_{\lg v}$, que da 0,123
  para los turismos, 0,157 para los pesados de dos ejes y 0,097 para los de
  más de dos ejes, y para una velocidad lognormal es
  $\sqrt{\exp[(\ln 10 \, s_{\lg v})^2] - 1}$, que da 0,123, 0,158 y 0,097,
  con los pesados de dos ejes como los más anchos en los dos casos. Las
  desviaciones típicas impresas divididas por las medias impresas dan 0,150,
  0,099 y 0,087, con los turismos como los más anchos, así que las dos columnas
  no pueden salir de las mismas pasadas. A primer orden, $s_v \approx \bar v \ln 10 \, s_{\lg v}$ da
  10,9, 11,9 y 7,2 km/h donde se imprimen 13,3, 7,5 y 6,4 km/h.
- **Evidencia:** las demás columnas de la misma tabla concuerdan entre sí. La
  recta en la velocidad media da el nivel medio impreso a su lado
  ($16{,}6 + 32{,}55 \lg 88{,}5 = 79{,}97$, impreso 80,0; 81,76 y 84,44,
  impresos 81,8 y 84,4), lo que muestra además que la velocidad media es
  $10^{\overline{\lg v}}$; y $s_L\sqrt{1 - r^2}$ da 1,35, 2,15 y 2,00 dB, que
  concuerdan con las desviaciones típicas de los residuos impresas como 1,3,
  2,1 y 2,0 dB dentro del redondeo de los $r$ y $s_L$ impresos (de 1,30 a
  1,39, de 2,10 a 2,20 y de 1,96 a 2,06 dB en ese margen, y de 1,31 a 1,40,
  de 2,13 a 2,24 y de 1,97 a 2,08 dB con el denominador $n - 2$ de un
  residuo). Solo la fila de dispersiones de velocidad desentona, y sigue
  desentonando en ese mismo margen de redondeo. Verificado en la página 34
  del PDF (p. 26 impresa) de la BS EN ISO 11819-1:2001.
- **Consecuencia para el propio ejemplo de la norma:** ninguna para los
  niveles sonoros de vehículo, que solo necesitan las ordenadas en el origen y
  las pendientes. La comprobación del apartado 9.3 que el ejemplo supera se
  sigue superando con las dispersiones que implica la regresión: las
  velocidades de referencia de 80 y 70 km/h quedan dentro de 73,6 a 106,4,
  64,8 a 88,6 y 66,9 a 81,2 km/h.
- **Comportamiento de la biblioteca:**
  [`PassByRegression`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/statistical_pass_by.py)
  da la dispersión de $\lg v$ y la ventana del apartado 9.3 en km/h que se
  deriva de ella, y la batería de conformidad no usa como oráculo las
  dispersiones de velocidad impresas.
- **Estado:** no reportada.

## ISO 11819-1:1997, anexo D (una tabla numerada según el anexo siguiente)

- **Ubicación:** anexo D (informativo), "Example of a normalized reference
  surface", página impresa 22 (página 30 del PDF).
- **Lo impreso:** la única tabla del anexo D lleva por título "Table E.1 —
  Example of surfaces, with sound level data, used to establish a normalized
  reference case for the medium speed range".
- **El problema:** una tabla de un anexo ISO se numera según el anexo en el
  que está, así que esta es la tabla D.1. El anexo E, al que apunta el número,
  contiene un formulario de informe cuyos recuadros no llevan número de tabla,
  así que la etiqueta nombra una tabla que no existe.
- **Evidencia:** verificado en la página 30 del PDF (p. 22 impresa) y en las
  páginas 31 a 34 del PDF (pp. 23 a 26 impresas) de la BS EN ISO 11819-1:2001.
- **Comportamiento de la biblioteca:** no hace falta ninguno.
  `SPB_ANNEX_D_SURFACES_DB` cita la tabla por su anexo y dice que va impresa
  como "Table E.1".
- **Estado:** no reportada.

## Mechel (2008), Tabla 3 (una impedancia de pared que su propia Ecuación (11) no da)

- **Localización:** Tabla 3, "Density and elastic constants of materials", la
  fila "PVC, 30% softener" en la página impresa 530 (página PDF 545), frente a
  la Ecuación (11) de la página impresa 529 (página PDF 544). Fuente no
  normativa: un libro de texto.
- **Lo impreso:** la fila da $\rho$ = 1250 kg/m3, $f_{cr}d$ = 48 Hz m y
  $Z_m$ = 1220, con las columnas del módulo y del factor de pérdidas vacías.
  La Ecuación (11), en la página de enfrente, dice
  $F := f/f_{cr}\ ;\ Z_m := f_{cr}m/Z_0 = (f_{cr}d/Z_0)\,\rho$.
- **El problema:** con la densidad y el $f_{cr}d$ de la propia fila, esa
  definición da $1250 \times 48 / 413 = 145$. El 1220 impreso es 8,4 veces esa
  cifra.
- **Evidencia:** la misma expresión reproduce el resto de la tabla a lo largo
  de cuatro décadas de $Z_m$, de 20 a 1438: treinta y seis de las otras
  treinta y siete filas dentro del 5 por ciento y treinta y cuatro dentro del
  3 por ciento. La otra fila que se sale de esa banda tampoco es un defecto, y
  enseña qué aspecto tiene uno que no lo es: "Plaster board" imprime
  $Z_m$ = 85 como valor único mientras su $f_{cr}d$ es el rango de 31 a 35, y
  85 es el extremo alto de la banda que da la ecuación y no su centro. La
  conclusión no depende del valor que se tome para $Z_0$, que la ecuación
  escribe como símbolo: 400 da 150 y 415 da 144,6, frente a un 1220 impreso.
  Verificado contra la página tal como se imprime en las páginas PDF 544 y 545
  (páginas impresas 529 y 530) de Mechel (2008), *Formulas of Acoustics*,
  2.ª edición.
- **Consecuencia para las tablas del propio libro:** esa única celda. Ninguna
  otra parte del documento calcula con ella, y la densidad y el $f_{cr}d$ de
  la fila, que son las dos columnas que lee esta biblioteca, son coherentes
  entre sí.
- **Comportamiento de la biblioteca:** el catálogo guarda la densidad, el
  $f_{cr}d$ y el factor de pérdidas de cada fila, y no guarda $Z_m$, que es
  una razón de impedancia de pared y no una propiedad del material. La fila
  lleva la discrepancia en su nota. Las pruebas
  `test_the_printed_wall_impedance_follows_from_the_books_own_equation` y
  `test_the_one_row_that_does_not_is_the_one_the_errata_names` de
  [`tests/solids/test_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/solids/test_catalogue.py) fijan
  las dos mitades de la evidencia.
- **Estado:** no reportado.

## Bies 5e (2017), Tabla C.1 (tres velocidades que no se siguen de las dos columnas de las que dice calcularlas)

- **Localización:** Tabla C.1, "Properties of materials", las filas "Brick" y
  "Cork" de la página impresa 719 (página PDF 748) y "Plywood (fir)" de la
  página impresa 720 (página PDF 749), frente al texto de la página impresa 717
  (página PDF 746). Fuente no normativa: un libro de texto.
- **Lo impreso:** la página 717 dice "The speed of sound values in column 4 of
  Table C.1 were calculated from the values in columns 2 and 3", que son el
  módulo de Young en $10^9$ N/m2 y la densidad en kg/m3. Las tres filas dan, en
  ese orden, $E$ = 24 y $\rho$ = 2000 con una velocidad de 3650 m/s; $E$ = 0,1
  y $\rho$ = 250 con 500 m/s; y $E$ = 8,3 y $\rho$ = 600 con 4540 m/s.
- **El problema:** $\sqrt{E/\rho}$ sobre esas celdas da 3464, 632 y 3719 m/s.
  Las velocidades impresas quedan un 5,4 por ciento por encima, un 20,9 por
  ciento por debajo y un 22,1 por ciento por encima de lo que dan las dos
  columnas que tienen al lado.
- **Evidencia:** la misma expresión reproduce el resto de la tabla. De las
  ochenta y siete filas que imprimen el módulo y la densidad como valores
  únicos, setenta y nueve coinciden dentro del 1 por ciento y ochenta y cuatro
  dentro del 3, con una desviación mediana del 0,03 por ciento, y a lo largo de
  velocidades de 190 a 27000 m/s. Sólo estas tres se salen, que es la firma de
  una celda mal impresa y no la de un método más flojo que el que describe la
  página. Cuál de las celdas está mal no se puede saber desde la página: 4540
  m/s saldría de un módulo de 12,4 en vez de 8,3, y 500 m/s de una densidad de
  400 en vez de 250. Verificado contra la página tal como se imprime en las
  páginas PDF 748 y 749 (páginas impresas 719 y 720) de Bies, Hansen y Howard
  (2017), *Engineering Noise Control*, quinta edición.
- **Consecuencia para las tablas del propio libro:** tres celdas. Ninguna otra
  parte del documento calcula con ellas.
- **Comportamiento de la biblioteca:** el catálogo guarda las tres columnas tal
  como se imprimen y no deriva nada por encima, y cada una de las tres filas
  lleva la discrepancia en su nota. La prueba
  `test_three_rows_do_not_follow_from_their_own_two_columns` de
  [`tests/solids/test_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/solids/test_catalogue.py) fija
  las tres, y `test_the_rest_of_the_table_reproduces_to_three_per_cent` fija
  las ochenta y cuatro que sí se siguen, que es lo que convierte a las tres en
  un defecto.
- **Estado:** no reportado.

## Bies 5e (2017), Tabla C.2 (cuatro masas molares que no son las de la molécula de su fila)

- **Localización:** Tabla C.2, "Molecular weights and ratios of specific heats
  for some commonly used gases", las filas "Ammonia", "Fluorine", "Freon 22" y
  "Nitric oxide" de la página impresa 722 (página PDF 751). Fuente no
  normativa: un libro de texto.
- **Lo impreso:** las cuatro filas dan, en la columna encabezada "Molecular
  weight, $M$ kg/mole", 0.01730, 0.01900, 0.08047 y 0.06301.
- **El problema:** la masa molar de un gas se sigue de la molécula que nombra
  la fila, y ninguna de las cuatro lo hace. El amoniaco es NH$_3$, 17.031
  g/mol, no 17.30. El flúor gas es F$_2$, 37.996 g/mol, y 19.00 es la masa
  atómica de un solo átomo de flúor. El Freón 22 es CHClF$_2$, 86.465 g/mol, no
  80.47. El óxido nítrico es NO, 30.006 g/mol, y 63.01 es la masa molar del
  *ácido* nítrico, HNO$_3$.
- **Evidencia:** el resto de la tabla es lo que decide que son erratas y no una
  convención más suelta. Treinta y cinco de las treinta y siete filas nombran
  una molécula cuya masa de fórmula se puede calcular; las dos que no son las
  dos mezclas, el aire y el gas natural. De esas treinta y cinco, treinta y una
  reproducen su masa de fórmula por debajo del 0,05 por ciento, y las dos que
  se salen más se salen sólo por el redondeo de la página: el helio, 4.00
  frente a 4.0026, queda un 0,07 por ciento por debajo, y el hidrógeno, 2.02
  frente a 2.016, un 0,20 por ciento por encima, las dos en el último dígito
  impreso. Así que la precisión de la propia tabla es de dos partes por mil, y
  frente a eso las cuatro excepciones se salen un 1,6, un 6,9, un 50 y un 110
  por ciento. Dos de ellas caen exactamente sobre otra especie, que es la
  forma que tiene un salto de copia: 19.00 es el flúor atómico con un error del
  0,01 por ciento y 63.01 es HNO$_3$ con uno del 0,003 por ciento, la misma
  exactitud que tienen las filas correctas. La relación de calores específicos
  que va al lado de cada una apunta en la misma dirección: 1.36 para el flúor y
  1.40 para el óxido nítrico son valores de gas diatómico, así que las filas
  hablan de F$_2$ y de NO diga lo que diga su columna de masa. Una tabla
  independiente del mismo género coincide en las dos cosas: el *Control Valve
  Sizing Handbook* de Masoneilan (Baker Hughes, BHMN-19540C, 2022), que tabula
  las mismas dos magnitudes para el mismo fin, imprime "Fluorine, F$_2$" con
  una relación de calores específicos de 1.36 en su página 19 y "Ammonia,
  NH$_3$" con un peso molecular de 17.0 en su página 20. Verificado contra la
  página tal como se imprime en la página PDF 751 (página impresa 722) de Bies,
  Hansen y Howard (2017), *Engineering Noise Control*, quinta edición, y en las
  páginas 19 y 20 del manual de Masoneilan.
- **Consecuencia para las tablas del propio libro:** cuatro celdas. Ninguna
  otra parte del documento calcula con ellas; la tabla se ofrece para el ruido
  de válvula de control de la Sección 10.8, donde el gas lo elige quien lee.
  Quien sí tomara una de las cuatro obtendría una velocidad del sonido un 0,8
  por ciento baja para el amoniaco, un 3,7 por ciento alta para el Freón 22, un
  41,4 por ciento alta para el flúor y un 31,0 por ciento baja para el óxido
  nítrico, ya que $c = \sqrt{\gamma R T / M}$.
- **Comportamiento de la biblioteca:** el catálogo guarda la fila y su relación
  de calores específicos, y rechaza la masa molar en vez de servirla: leerla
  levanta un error que nombra la celda, cita lo que imprime la página y apunta
  aquí. Las pruebas `test_a_cell_the_errata_names_is_not_served_as_a_value` y
  `test_the_refusal_quotes_the_printed_number_and_points_at_the_registry` de
  [`tests/fluids/test_gas_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas_catalogue.py)
  fijan las dos mitades, y `test_no_other_cell_of_either_table_is_called_wrong`
  impide que la acusación se extienda a una quinta fila.
- **Estado:** no reportado.

## Bies 5e (2017), Tabla C.2 (dos relaciones de calores específicos que ningún gas puede tener)

- **Localización:** Tabla C.2, "Molecular weights and ratios of specific heats
  for some commonly used gases", las filas "Hydrogen fluoride" y "Octane" de la
  página impresa 722 (página PDF 751). Fuente no normativa: un libro de texto.
- **Lo impreso:** la columna encabezada "Ratio of specific heats, $\gamma$" da
  0.97 para el fluoruro de hidrógeno y 1.66 para el octano.
- **El problema:** la columna es la relación de calores específicos, que es lo
  que dice su propio encabezado y lo que la tabla existe para alimentar en el
  procedimiento de ruido de válvula al que apunta el apéndice, "particularly
  useful for calculating control valve noise (see Section 10.8)". Para
  cualquier sustancia en una sola fase estable $c_p \geq c_v$, así que
  $\gamma \geq 1$ y un 0.97 impreso queda fuera de lo que la magnitud puede
  ser. Eso es una afirmación sobre $c_p/c_v$ y no sobre cualquier exponente que
  alguien escriba $k$: el exponente isentrópico de gas real de un vapor que se
  asocia con fuerza, que es lo que es el fluoruro de hidrógeno, sí puede bajar
  de 1, pero es otra magnitud distinta de la que nombra esta columna y no es la
  que quiere el procedimiento de después. La celda del octano queda fuera de la
  columna por el otro lado: para un gas ideal $\gamma = 1 + 2/f$, donde $f$
  cuenta los grados de libertad activos, y $f \geq 3$ siempre, así que
  $\gamma \leq 5/3 \approx 1.667$ con igualdad sólo para uno monoatómico. El
  octano es C$_8$H$_{18}$, veintiséis átomos, con tres grados de libertad de
  rotación además de los tres de traslación antes de contar ninguna vibración,
  lo que lo deja en $\gamma \leq 4/3$ y en la práctica cerca de 1.05. Esa cota
  es de gas ideal, y un fluido real sí pasa de 5/3 cerca de su punto crítico;
  lo que descarta leer la celda así es que ésta es una columna de gas ideal,
  impresa contra masas molares ideales, que da un valor por gas y no uno por
  estado.
- **Evidencia:** la columna es por lo demás una función limpia de la
  complejidad molecular, que es lo que hace visibles las dos excepciones. Los
  tres gases monoatómicos imprimen de 1.64 a 1.67, los diatómicos de 1.31 a
  1.41, y los poliatómicos van cayendo con el tamaño hasta 1.05. Los dos
  vecinos del octano en esa progresión están en la misma tabla y a un carbono
  de distancia: el n-heptano imprime 1.05 y el pentano 1.06, así que la propia
  tabla dice lo que hace un alcano de ese tamaño. Los vecinos del fluoruro de
  hidrógeno son las demás filas diatómicas, y el cloruro de hidrógeno, el
  haluro siguiente, imprime 1.41. Fuera del libro, el *Control Valve Sizing
  Handbook* de Masoneilan (Baker Hughes, BHMN-19540C, 2022) imprime 1.05 para
  el octano en esa misma columna de $c_p/c_v$ en su página 19, entre el 1.66
  del helio y el 1.07 del pentano, así que la progresión no es la costumbre de
  un solo autor. Verificado contra la página tal como se imprime en la página
  PDF 751 (página impresa 722) de Bies, Hansen y Howard
  (2017), *Engineering Noise Control*, quinta edición, releyendo las dos celdas
  a seis aumentos: 0.97 y 1.66 son lo que imprime la página, sin ningún dígito
  en duda.
- **Consecuencia para las tablas del propio libro:** dos celdas. Quien tomara
  la fila del octano obtendría una velocidad del sonido un 26,0 por ciento
  alta; la del fluoruro de hidrógeno no se puede usar en absoluto, porque una
  velocidad del sonido calculada con una $\gamma$ menor que 1 no es la
  velocidad de nada.
- **Comportamiento de la biblioteca:** el catálogo guarda la fila y su masa
  molar, y rechaza la relación en vez de servirla, igual y con el mismo mensaje
  que las cuatro masas molares de arriba. La guardia independiente es
  [`phonometry.fluids.ideal_gas`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/gas.py), que rechaza
  una relación igual o menor que 1 se la pase quien se la pase, y
  `test_a_ratio_of_specific_heats_at_or_below_one_is_refused` de
  [`tests/fluids/test_gas.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas.py) lo fija.
- **Estado:** no reportado.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Apéndice D (dos filas que la tabla no sabe distinguir)

- **Localización:** Apéndice D, «Random incidence scattering coefficient
  table», el grupo «Pyramids [6]», en las páginas impresas 499 y 500 (PDF 556
  y 557). Fuente no normativa: un libro de texto.
- **Lo impreso:** el grupo tiene cuatro filas. La página impresa 499 trae
  «$h = 30.5$ cm, $L = b = 2h$» y a continuación la misma descripción otra vez,
  con la línea de continuación «One in four pyramid corners raised from
  baseplate» debajo. La página impresa 500 trae «$h = 30.5$ cm, $L = b = h$» y
  después, de nuevo, «$h = 30.5$ cm, $L = b = 2h$» con la misma línea de
  continuación debajo.
- **El problema:** la segunda fila y la cuarta se imprimen con la misma
  descripción, la misma línea de continuación y números distintos: 0,38 frente
  a 0,44 en 1 kHz, 0,74 frente a 0,76 en 2 kHz, y 1,00 frente a una raya en
  5 kHz. Nada de lo impreso junto a una de ellas la distingue de la otra, así
  que quien busque «las pirámides de 30,5 cm con una esquina de cada cuatro
  levantada» encuentra dos respuestas y ninguna forma de elegir. Una tabla de
  valores medidos tiene que identificar sus filas, y esta no lo hace.
- **Evidencia:** las dos páginas leídas a seis aumentos. Las etiquetas son
  carácter por carácter la misma, las líneas de continuación también, y los
  valores difieren en trece de las dieciocho bandas, y sólo coinciden en 100,
  125, 160, 200 y 4000 Hz. La estructura del propio
  bloque es lo que hace evidente la lectura: la tabla empareja una superficie
  sin modificar con su versión modificada, y la página impresa 499 empareja
  $L = b = 2h$ con la suya. La página impresa 500 abre con $L = b = h$, así que
  su segunda fila es donde le toca a la modificada de $L = b = h$, con lo que
  el «2h» impreso sería el defecto. Eso es una lectura del patrón y no algo que
  la página afirme, y la fuente a la que se acredita el grupo, Sharma y
  Bradley, *J. Acoust. Soc. Am.* 134(5), 4095 (2013), es un resumen de congreso
  de una página que esta biblioteca no ha leído, así que el registro anota lo
  que la página hace y no lo que debería haber dicho. Verificado en la página
  PDF 556 (página impresa 499) y en la página PDF 557 (página impresa 500) de
  Cox y D'Antonio (2017), *Acoustic Absorbers and Diffusers*, tercera edición.
- **Comportamiento de la biblioteca:** se guardan las dos filas, con la
  descripción y la línea de continuación tal como se imprimen. Sus claves
  llevan la página impresa, que es lo único que las separa, y
  `test_two_pyramid_rows_are_told_apart_only_by_the_page_they_sit_on` de
  [`tests/materials/diffusers/test_scattering_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_scattering_catalogue.py)
  fija que sigan siendo dos filas con dos espectros.
- **Estado:** no reportado.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Apéndice B (una anchura en centímetros que su propia geometría hace metros)

- **Localización:** Apéndice B, «Normalized diffusion coefficient table»,
  sección 1, la primera superficie de la serie de anchuras, en la página
  impresa 482 (PDF 539). Fuente no normativa: un libro de texto.
- **Lo impreso:** la sección se encabeza «Effect of changing diffuser
  periodicity and width. Semicylinder(s) non-absorbing surfaces, radius 0.3 m
  (1 cm flat section between each period)», y sus cinco superficies se listan
  como «1 period, 0.61 cm wide», «2 periods, 1.22 m wide», «4 cylinders,
  2.44 m wide», «6 periods, 3.66 m wide» y «12 periods, 7.32 m wide».
- **El problema:** la primera anchura está en centímetros y las otras cuatro en
  metros, y la serie se duplica: 0,61, 1,22, 2,44, y después 3,66 y 7,32, que
  son seis y doce veces la primera. Un periodo de la superficie que describe el
  encabezado es un semicilindro de radio $0,3$ m más la sección plana de $1$ cm,
  así que $2 \times 0,3 + 0,01 = 0,61$ m. Una anchura de 0,61 cm son seis
  milímetros, la centésima parte de lo que da la geometría del propio
  encabezado y la centésima parte de lo que pide el resto de la serie.
- **Evidencia:** la misma superficie se lista en la Tabla C.3 del apéndice
  siguiente, bajo un encabezado con la misma geometría, y allí dice «1 period,
  0.61 m wide». O sea que el libro imprime las dos grafías de una misma
  superficie con doce páginas de diferencia, y la métrica es la que sostiene su
  aritmética. Verificado en la página PDF 539 (página impresa 482) y en la
  página PDF 549 (página impresa 492) de Cox y D'Antonio (2017), *Acoustic
  Absorbers and Diffusers*, tercera edición, releyendo la unidad a seis
  aumentos en las dos páginas: el apéndice imprime «cm» y la Tabla C.3 imprime
  «m».
- **Consecuencia para las tablas del propio libro:** la descripción de una
  superficie y la de las tres filas que la llevan. Los números de al lado no
  se ven afectados, que es lo que hace el defecto fácil de pasar por alto y
  digno de registrarse: quien compare un semicilindro medido con esta fila
  estará comparando contra un dispositivo de 0,61 m diga lo que diga la
  etiqueta.
- **Comportamiento de la biblioteca:** la fila conserva la anchura tal como se
  imprime, porque un catálogo que la corrigiera por su cuenta estaría
  afirmando una lectura que la página no hace. Las tres filas de la superficie
  la llevan en su clave y
  `test_every_section_heading_is_kept_whole` de
  [`tests/materials/diffusers/test_diffusion_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/materials/diffusers/test_diffusion_catalogue.py)
  fija que el encabezado con la geometría viaje con ellas, que es lo que
  permite a quien lea ver la contradicción.
- **Estado:** no reportado.

## Cox & D'Antonio, Acoustic Absorbers and Diffusers 3e (2017), Tabla 6.7 (seis porosidades impresas en tanto por ciento en una columna de fracciones)

- **Localización:** Tabla 6.7, «Effective flow resistivity values for ground
  surfaces and other parameters», la columna «Porosity», en las páginas
  impresas 200 y 201 (PDF 257 y 258). Fuente no normativa: un libro de texto.
- **Lo impreso:** la columna se encabeza «Porosity» y no dice su unidad,
  mientras la de al lado se encabeza «Water content (%)». Todas las
  porosidades que imprime son fracciones entre 0,15 y 1 («0.5–0.9» para la
  nieve, «0.24» para el campo deportivo, «0.44» para la arena fina, «0.34–1» y
  otras así para las hierbas ajustadas), salvo en seis filas: «Mineral layer
  beneath mixed deciduous forest» «36.5», «Humus on pine forest floor»
  «58.1», «Pine forest litter (6–7 cm thick)» «38.9», «Grass root layer in
  loamy sand» «48 ± 4», «Loamy sand» «37.5» y «Bare sandy plain» «26.9».
- **El problema:** una porosidad es la fracción de un volumen que está
  abierta, así que no puede pasar de 1, y estas seis son porcentajes impresos
  en una columna que no dice su unidad y que en todas las demás filas lleva
  fracciones. Leídas en la unidad de la propia columna son porosidades de 26,9
  a 58,1, que ningún material tiene; leídas como tanto por ciento son de 0,269
  a 0,581, que es lo que son suelos como estos. La página deja que quien lee
  averigüe cuál de las dos, y un programa que lea la columna tal como se
  imprime se queda con el valor imposible.
- **Evidencia:** verificado en la página PDF 257 (página impresa 200) y en la
  página PDF 258 (página impresa 201) de Cox y D'Antonio (2017), *Acoustic
  Absorbers and Diffusers*, tercera edición: el encabezado no imprime unidad,
  y las seis celdas imprimen los valores citados, la cuarta como «48 ± 4».
- **Comportamiento de la biblioteca:** en
  [`PUBLISHED_GROUND`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/ground_surfaces.py)
  las seis filas dejan vacío `GroundSurface.porosity`, que es una fracción de 0
  a 1, y guardan la celda como `misprinted`: `why_missing("porosity")` y el
  rechazo de `printed("porosity")` citan la cifra que imprime la página, con el
  ± 4, y dicen por qué no se sirve. La biblioteca no la convierte en 0,365 ni en
  las demás, porque la página no imprime la unidad que esa conversión daría
  por supuesta. Toda fila de catálogo comprueba al construirse que una
  porosidad es una fracción.
  `test_the_six_percent_porosities_of_cox_are_held_as_misprinted` y
  `test_why_a_per_cent_porosity_is_missing_quotes_the_page` de
  [`tests/io/test_catalogue_row_contract.py`](https://github.com/jmrplens/phonometry/blob/main/tests/io/test_catalogue_row_contract.py)
  fijan las seis.
- **Estado:** sin notificar.

## Ver & Beranek 2e (2006), TABLA 14.1 (tres módulos con la notación e corrompida en la impresión)

- **Dónde:** TABLA 14.1, «Properties of Some Commercial Damping Materials», en
  la página impresa 598 (página 599 del PDF), dentro del capítulo 14,
  «Structural Damping», de Eric E. Ungar y Jeffrey A. Zapfe. Fuente no
  normativa: un manual.
- **Lo impreso:** las cuatro columnas de módulos van en una notación que la
  propia tabla define en su nota al pie c: «The number following e represents
  the power of 10 by which the number preceding e is to be multiplied; e.g.,
  1.2e3 represents $1.2 \times 10^3$». Todas las celdas del bloque la cumplen
  menos tres. Antiphon-13 imprime `3.e3e` en $E_{I,\max}$; Soundcoat DYAD 606
  imprime `3G5` en $E_{\max}$; y GE SMRD imprime `e35` en $E_{\max}$.
- **El problema:** ninguna de las tres es un número en esa notación. `3.e3e`
  acaba en un marcador de exponente sin dígito detrás y lleva un punto decimal
  sin parte fraccionaria antes del primer marcador; `3G5` pone una G mayúscula
  donde va el marcador, y no hay ninguna otra G mayúscula en la tabla; `e35`
  empieza por el marcador y no tiene mantisa. El valor pretendido no se puede
  recuperar, porque cada cadena admite más de una lectura: `3.e3e` podría ser
  $3 \times 10^3$ con un marcador sobrante o $3.3 \times 10^{-3}$ de otra
  composición, y `e35` podría ser $3 \times 10^5$ o $3.5 \times 10^{?}$.
- **Evidencia:** Verificado en la página 599 del PDF (p. impresa 598) de
  Ver & Beranek, *Noise and Vibration Control Engineering* 2e (2006). Las tres
  cadenas se leen y son lo que la página lleva; las celdas vecinas del mismo
  bloque se leen igual de bien y sí cumplen la notación, así que el defecto es
  de la impresión. Las columnas contiguas tampoco resuelven ninguna de las
  tres. Para Antiphon-13, la relación que el propio capítulo imprime,
  $E_{I,\max} \approx \eta_{\max} E_{\mathrm{trans}}$, da
  $1.8 \times 1.9 \times 10^4 = 3.4 \times 10^4$ psi, compatible con una
  mantisa 3 y un exponente 4; pero la cadena impresa ofrece un 3 y ningún
  exponente legible, y esta biblioteca no publica un valor que ha tenido que
  terminar ella.
- **Qué hace la biblioteca:** las tres celdas se guardan como `misprinted` en
  [`PUBLISHED_DAMPING`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/damping.py), de modo que la
  fila conserva lo que imprime el libro y se niega a servirlo como número.
  Pedir una de ellas con `printed()` lanza excepción y nombra los glifos. Las
  demás celdas de las diecisiete filas se sirven con normalidad.
- **Estado:** sin comunicar.

## Ver & Beranek 2e (2006), TABLA 14.1 (un módulo de transición impreso por debajo del módulo más pequeño de su propia fila)

- **Dónde:** TABLA 14.1, «Properties of Some Commercial Damping Materials»,
  fila «3M ISD-113», en la página impresa 598 (página 599 del PDF), dentro del
  capítulo 14, «Structural Damping», de Eric E. Ungar y Jeffrey A. Zapfe.
  Fuente no normativa: un manual.
- **Lo impreso:** la fila da $\eta_{\max} = 1.1$, temperaturas de pico de
  $-45$, $-20$ y $15\,^\circ\mathrm{F}$, y los cuatro módulos
  $E_{\max} = 1.5\mathrm{e}5$, $E_{\min} = 3\mathrm{e}2$,
  $E_{\mathrm{trans}} = 2.1\mathrm{e}2$ y $E_{I,\max} = 2.3\mathrm{e}2$ psi.
- **El problema:** esa misma página define $E_{\min}$ como «the smallest value
  of $E$», en el párrafo bajo la tabla y otra vez en la nota al pie c, donde
  dice que $E_{\max}$ vale a temperaturas bajas, $E_{\min}$ a altas y
  $E_{\mathrm{trans}}$ en el rango de $\eta_{\max}$, que queda entre ambos.
  Aquí $E_{\mathrm{trans}} = 2.1 \times 10^2$ psi es menor que
  $E_{\min} = 3 \times 10^2$ psi, así que una de las dos celdas contradice la
  definición que la página da de la otra. La página no dice cuál. El
  $E_{\mathrm{trans}}$ impreso lo respalda su vecina a través de la relación
  del propio capítulo, $E_{I,\max} \approx \eta_{\max} E_{\mathrm{trans}}$:
  $1.1 \times 2.1 \times 10^2 = 2.3 \times 10^2$ psi, que es justo lo que
  imprime $E_{I,\max}$. En contra, las otras catorce filas que imprimen los tres
  módulos ponen $E_{\mathrm{trans}}$ entre uno y dos órdenes de magnitud por
  encima de $E_{\min}$, que es donde tendría que estar $E_{\min}$ para que
  esta fila se pareciera a sus vecinas. Ninguna de las dos lecturas sale de la
  página.
- **Evidencia:** Verificado en la página 599 del PDF (p. impresa 598) de
  Ver & Beranek, *Noise and Vibration Control Engineering* 2e (2006). Las
  cuatro celdas de la fila se leen sin ambigüedad en la notación que define la
  nota al pie c, y la frase que define $E_{\min}$ también; el defecto es una
  contradicción entre dos celdas legibles, no una celda ilegible. Tomando
  $E_{\mathrm{trans}} / \sqrt{E_{\max} E_{\min}}$ como prueba de forma sobre
  las quince filas que imprimen los tres, las otras catorce caen entre 0,976
  y 1,054 y esta da 0,031.
- **Qué hace la biblioteca:** las dos celdas se sirven tal como se imprimen,
  porque corregir cualquiera de ellas sería que esta biblioteca eligiera entre
  dos lecturas que la página deja abiertas. La fila lleva una nota que lo
  dice, y el catálogo publicado la muestra; un test comprueba que el orden se
  cumple en todas las demás filas, para que una segunda aparición no pase
  inadvertida.
- **Estado:** sin comunicar.

## Ver & Beranek 2e (2006), TABLA 8.5 (la masa por unidad de superficie de la malla más fina, diez veces mayor en libras)

- **Dónde:** TABLA 8.5, «Mechanical Characteristics and Flow Resistance $R_s$
  of Wire Mesh Cloths», en la página impresa 262 (página 266 del PDF), dentro
  del capítulo 8, «Sound-Absorbing Materials and Sound Absorbers». Fuente no
  normativa: un manual.
- **Lo impreso:** cada magnitud de la tabla se imprime dos veces, pero sólo
  tres de los cuatro pares son una misma magnitud en dos sistemas de unidades:
  el número de hilos, el diámetro del hilo y la masa por unidad de superficie.
  El cuarto imprime la resistencia al flujo en N s/m3 y otra vez como múltiplo
  de $\rho_0 c_0$. La columna de masa por unidad de superficie va,
  en kg/m2 frente a lb/ft2: 1.6 / 0.32, luego 1.2 / 0.25, luego 0.63 / 0.13,
  luego 0.48 / 0.1, y en la última fila, la malla de 80 hilos por centímetro,
  0.31 / 0.63.
- **El problema:** una libra por pie cuadrado son
  $0.45359237 / 0.09290304 = 4.8824$ kg/m2 por las definiciones de la libra y
  el pie, de modo que 0.31 kg/m2 son 0.063 lb/ft2 y no 0.63. El punto decimal
  está un lugar a la derecha. Tres cosas deciden cuál de las dos celdas es la
  defectuosa. Las cuatro filas de arriba convierten dentro del redondeo de su
  propia última cifra, así que la columna por lo demás está bien. La columna
  en libras, tal como se imprime, haría de la malla más fina el tejido más
  pesado de la tabla, el doble que el más grueso, cuando todas las demás
  columnas bajan con la malla. Y el propio tejido da la masa: un tejido
  cuadrado de $n$ hilos por metro y diámetro $d$ lleva $2 n \rho \pi d^2/4$
  por unidad de superficie, que para 8000 hilos por metro de 57 $\mu$m y
  densidad $\rho = 7800$ kg/m3 son 0.32 kg/m2, el 0.31 impreso y no el 0.63
  impreso. La página nunca dice de qué es el hilo, así que esa densidad no
  sale de ella: 7800 kg/m3 son los de un acero inoxidable, y se dice aquí
  porque sin ella el argumento no es reproducible. La misma aritmética con la
  misma densidad reproduce las cuatro filas de arriba con un tres por ciento
  de diferencia.
- **Evidencia:** Verificado en la página 266 del PDF (p. impresa 262) de
  Ver & Beranek, *Noise and Vibration Control Engineering* 2e (2006). Dos
  lectores transcribieron la página por separado y ambos leyeron la celda como
  tres glifos, «0.63», sin ningún cero inicial perdido entre ellos, y ambos
  leyeron 0.31 en la celda contigua. Las otras cuatro filas de esa columna se
  leen igual de bien y convierten correctamente, así que el defecto es de esta
  celda y de la impresión.
- **Qué hace la biblioteca:** este catálogo publica la columna en SI de cada
  par, así que la celda defectuosa no llega a ningún valor servido desde
  [`PUBLISHED_FLOW_RESISTANCE`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py).
  La fila guarda los 0.31 kg/m2 impresos, que la columna y el tejido
  respaldan, y su `note` cita la celda en libras y apunta aquí, de modo que
  quien reproduzca el libro vea lo que el libro dice sin que eso entre en
  ningún cálculo. La nota y no el matiz `misprinted`: ese matiz dice que un
  número no se sirve, y sólo se lee desde la celda que deja vacía, mientras
  que aquí la celda defectuosa es la reformulación en unidades usuales, para
  la que este catálogo no tiene ninguna columna.
- **Estado:** sin comunicar.

## Ver & Beranek 2e (2006), TABLA 8.6 (las dos columnas de densidad superficial discrepan por un mismo factor equivocado en todas las filas)

- **Dónde:** TABLA 8.6, «Mechanical Characteristics and Flow Resistance $R_s$
  of Glass Fiber Cloth», en la página impresa 263 (página 267 del PDF), dentro
  del capítulo 8, «Sound-Absorbing Materials and Sound Absorbers». Fuente no
  normativa: un manual.
- **Lo impreso:** la densidad superficial se imprime dos veces en cada una de
  las trece filas, en oz/yd2 y en g/m2: 3.16 / 96, 5.37 / 164, 6.70 / 204,
  8.90 / 272, 19.2 / 585, 17.7 / 535, 12.3 / 375, 1.87 / 57, 1.94 / 59,
  9.60 / 293, 14.5 / 442, 24.6 / 750 y 12.0 / 366.
- **El problema:** una onza por yarda cuadrada son
  $28.349523125 / 0.83612736 = 33.9057\ldots$ g/m2 por las definiciones de la
  onza y la yarda, ambas exactas. Lo exacto es el cociente; 33.906 es ese
  cociente con tres decimales, y así se escribe aquí cada vez que se cita
  corto. La razón que imprime la tabla está entre 30.2 y
  30.6 en las trece filas y nunca es 33.9, así que las dos columnas no pueden
  ser ambas correctas, y el desvío es el mismo once por ciento en todas: una
  conversión equivocada aplicada a toda la columna, y no trece deslices
  independientes. Cuál de las dos columnas lo lleva, la página no lo dice, y
  ninguna otra columna de la tabla lo decide: el tejido y la resistencia al
  flujo se imprimen una sola vez, en una sola unidad, y ninguno determina una
  densidad superficial.
- **Evidencia:** Verificado en la página 267 del PDF (p. impresa 263) de
  Ver & Beranek, *Noise and Vibration Control Engineering* 2e (2006). Dos
  lectores transcribieron los trece pares por separado y coincidieron en cada
  cifra. Las otras dos tablas del capítulo no son como esta: la TABLA 8.7
  convierte bien su columna de masa en las once filas, y la TABLA 8.5 en
  cuatro de sus cinco, siendo la quinta la única celda defectuosa que registra
  la entrada anterior. Una celda de una fila es un desliz de la imprenta;
  trece filas desviadas por un mismo factor son una columna, que es lo que
  hace de esto una propiedad de esta tabla y no del capítulo.
- **Qué hace la biblioteca:** guarda los gramos por metro cuadrado que
  imprime la página, tal como los imprime, en `surface_density_g_m2`. Todas
  las filas de esta tabla en
  [`PUBLISHED_FLOW_RESISTANCE`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py)
  llevan una `note` que cita los dos valores impresos y el factor exacto entre
  sus unidades y apunta aquí, de modo que la contradicción le llega al lector
  con el número y no en su lugar. La biblioteca ni elige entre las dos
  columnas ni convierte ninguna: publica la que la página imprime en SI y
  cuenta lo que dice la otra. La celda no va en `not_derivable`, que es para
  un valor que esta biblioteca se niega a calcular a partir de celdas que la
  página sí imprime, y nunca para una magnitud que la página imprime ella
  misma. La resistencia al flujo de estos tejidos, que se imprime una vez y en
  una sola unidad, se sirve con normalidad.
- **Estado:** sin comunicar.

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

## Harris 3e (1995), tablas 32.1 a 32.8 (diecinueve pares de unidades cuyas dos mitades no son la misma cantidad)

- **Ubicación:** tablas 32.1 a 32.8, el aislamiento de impacto de conjuntos de
  suelo-techo, en los folios impresos 32.8 a 32.15 (páginas 750 a 757 del
  PDF), dentro del capítulo 32, «Aislamiento del sonido transmitido por
  estructuras», de la edición española. Fuente no normativa: un manual.
- **Lo impreso:** cada dimensión y cada masa de estas ocho tablas se imprime
  dos veces, primero en SI y después, entre paréntesis, en unidades
  estadounidenses, dentro de la descripción corrida de cada construcción:
  «Losa de 10 cm (4 in)», «cada 40,6 cm (16 in)», «alfombra de 1,5 kg/m2
  (44 oz/yd2)». Las ocho tablas imprimen trescientos veintiún pares de esos.
- **El problema:** diecinueve de los trescientos veintiún pares no son la misma
  cantidad. La pulgada son 2,54 cm exactos, la libra 0,45359237 kg exactos y
  la yarda 0,9144 m exactos, así que una libra por pie cúbico son 16,0185
  kg/m3, una libra por yarda cuadrada 0,54249 kg/m2 y una onza por yarda
  cuadrada 33,906 g/m2, y cada par se decide por aritmética y nada más. En
  estas páginas la mitad estadounidense es la medida y la mitad SI su
  traducción, así que un par cuya mitad imperial es un número entero o una
  fracción se comprueba sólo en ese sentido, y uno cuya mitad imperial viene
  ya impresa como decimal redondeado se admite en los dos. Un par está bien
  cuando la mitad SI es la conversión redondeada **o truncada** a la precisión
  con que se imprime, que es lo que perdona el redondeo flojo de todo el
  capítulo: «60 cm (24 in)» y «2,5 cm (1 in)» son truncamientos de 60,96 y
  2,54 y nada más, y la fila 17 imprime «36,9 cm (14,5 in)», donde 36,9 cm son
  14,53 in y la página los imprimiría como las 14,5 in que tiene al lado. Los
  diecinueve de abajo pasan esa prueba. Cada uno nombra la fila que numera la
  página, el par tal como está compuesto y la conversión que falla:
  - **Fila 9** (página 750 del PDF, folio impreso 32.8): «30,8 cm (16 in)»
    para el espaciamiento de los listones. $16 \times 2{,}54 = 40{,}64$ cm,
    que estas ocho tablas imprimen como 40,6 cm dieciocho veces.
  - **Fila 11** (página 751 del PDF, folio impreso 32.9): «53,2 cm (21 in)»
    para el espaciamiento de los nervios. $21 \times 2{,}54 = 53{,}34$ cm, que
    la fila 38 imprime como 53,3 cm.
  - **Fila 14** (página 752 del PDF, folio impreso 32.10): «15,6 cm (6 in)»
    para la losa. $6 \times 2{,}54 = 15{,}24$ cm, que estas ocho tablas
    imprimen como 15,2 cm once veces.
  - **Fila 18** (página 752 del PDF, folio impreso 32.10): «36,7 cm (14,5 in)»
    para el espaciamiento de las vigas. $14{,}5 \times 2{,}54 = 36{,}83$ cm,
    que las filas 13 y 15 imprimen como 36,8 cm.
  - **Fila 22** (página 753 del PDF, folio impreso 32.11): «60,1 cm (24 in)»
    para el espaciamiento de las viguetas. $24 \times 2{,}54 = 60{,}96$ cm,
    que las filas 26, 27, 33 y 38 imprimen como 61 cm.
  - **Fila 23** (página 753 del PDF, folio impreso 32.11): «60,1 cm (24 in)»
    para el espaciamiento de las viguetas, el mismo par otra vez.
  - **Fila 26** (página 754 del PDF, folio impreso 32.12): «32,3 cm
    (11,75 in)» para el grosor total. $11{,}75 \times 2{,}54 = 29{,}85$ cm, y
    32,3 cm son 12,72 in, así que ninguna mitad es la otra.
  - **Fila 27** (página 754 del PDF, folio impreso 32.12): «1,89 cm (0,78 in)»
    para el solado de roble. $0{,}78 \times 2{,}54 = 1{,}98$ cm, que la fila
    26 imprime como 1,98 cm para el mismo solado.
  - **Fila 28** (página 754 del PDF, folio impreso 32.12): «1,89 cm (0,78 in)»
    para ese mismo solado de roble.
  - **Fila 28** (página 754 del PDF, folio impreso 32.12): «31,6 cm (12,5 in)»
    para el grosor total. $12{,}5 \times 2{,}54 = 31{,}75$ cm, que las filas
    16 y 18 imprimen como 31,8 cm y la fila 25 como 31,7 cm.
  - **Fila 29** (página 754 del PDF, folio impreso 32.12): «60,8 cm (24 in)»
    para los canales elásticos. $24 \times 2{,}54 = 60{,}96$ cm.
  - **Fila 31** (página 755 del PDF, folio impreso 32.13): «10,1 cm (2 in)»
    para la sección del listón. $2 \times 2{,}54 = 5{,}08$ cm, que estas ocho
    tablas imprimen como 5,1 cm veintidós veces, la propia fila incluida.
  - **Fila 34A** (página 755 del PDF, folio impreso 32.13): «7,5 cm (3 in)»
    para las bandas de forro. $3 \times 2{,}54 = 7{,}62$ cm, que estas ocho
    tablas imprimen como 7,6 cm diez veces.
  - **Fila 35A** (página 756 del PDF, folio impreso 32.14): «410 kg/m3
    (26,1 lb/ft3)» para la plancha de pulpa de papel comprimido.
    $26{,}1 \times 16{,}0185 = 418{,}1$ kg/m3, y 410 kg/m3 son 25,6 lb/ft3,
    así que ninguna mitad es la otra. La página no dice cuál de las dos lleva
    el defecto, y ninguna otra celda de las ocho tablas lo decide: la fila 5
    imprime 35,2 kg/m3 (2,2 lb/ft3) y la 37A 2370 kg/m3 (148 lb/ft3), y las
    dos convierten bien, que es lo que hace de esto una propiedad de esta
    celda y no del capítulo.
  - **Fila 35B** (página 756 del PDF, folio impreso 32.14): «60,1 cm (24 in)»
    para el espaciamiento de las viguetas de acero.
  - **Fila 36B** (página 756 del PDF, folio impreso 32.14): «60,1 cm (24 in)»
    para el espaciamiento de las viguetas de acero.
  - **Fila 37A** (página 756 del PDF, folio impreso 32.14): «1,5 kg/m2
    (3,4 lb/yd2)» para la malla de diamantes y los listones de metal.
    $3{,}4 \times 0{,}54249 = 1{,}84$ kg/m2, y la fila 38 convierte 4,14
    lb/yd2 en 2,25 kg/m2 con ese mismo factor.
  - **Fila 38** (página 756 del PDF, folio impreso 32.14): «1,81 kg/m2
    (40 oz/yd2)» para el felpudo de pelo. $40 \times 33{,}906 = 1356$ g/m2,
    que la fila 28 imprime como 1,4 kg/m2 para el mismo tejido.
  - **Fila 38** (página 756 del PDF, folio impreso 32.14): «1,99 kg/m2
    (44 oz/yd2)» para la alfombra de pelo de lana.
    $44 \times 33{,}906 = 1492$ g/m2, que las filas 28 y 30 imprimen como
    1,5 kg/m2 para el mismo tejido. Las dos celdas de alfombra de esta fila
    son 1,334 de su propia conversión, así que lo que se aplicó fue un factor
    equivocado al par y no dos cifras que se deslizan por separado.
- **Evidencia:** verificado en las páginas 750 a 757 del PDF (pp. impresas
  32.8-32.15) de Harris (ed.), *Manual de medidas acústicas y control del
  ruido* 3e (1995), la edición española de *Handbook of Acoustical
  Measurements and Noise Control*. Dos lectores transcribieron las ocho tablas
  por separado y coincidieron en los diecinueve pares; cada uno se volvió a
  leer después en su propia página, ampliado, antes de entrar en esta lista.
  Los trescientos veintiún pares se convirtieron y compararon uno a uno, no por
  muestreo, que es lo que hace de la lista algo cerrado y no una recolección
  de lo que alguien se encontró por el camino. Los casos que quedan fuera son
  los que perdona la regla de arriba, y tres de ellos están nombrados allí.
- **Qué hace la biblioteca:** publica todas estas descripciones exactamente
  como las compone la página. Las diecisiete filas que llevan uno de los
  diecinueve pares están marcadas en
  [`PUBLISHED_IMPACT_INSULATION`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/impact_catalogue.py):
  la celda se registra en `misprinted`, citando el par impreso y la conversión
  que falla, de modo que quien reproduzca el libro vea lo que el libro dice y
  quien use el catálogo sepa que no debe. Dieciocho de los diecinueve están
  dentro de la descripción corrida, de donde este catálogo no sirve ninguna
  cantidad, y ahí acaba todo. El decimonoveno es la densidad de la fila 35A,
  que es la única celda de las diecinueve que este catálogo levantaría a un
  campo propio, así que `layer_density_kg_m3` queda vacío ahí y `why_missing`
  devuelve las dos mitades impresas en lugar de elegir una. Las filas 5 y 37A,
  cuyas densidades convierten bien, se sirven con normalidad.
- **Estado:** sin comunicar.

## Norton & Karczub 2e (2003), apéndice 4 (el módulo de Young del corcho, tres potencias de diez por encima)

- **Dónde:** apéndice 4, «Physical properties of some common substances»,
  parte A «Solids», fila «Cork», en la página impresa 605 (página 625 del
  PDF). Fuente no normativa: un libro de texto.
- **Lo impreso:** corcho: densidad $250$ kg/m$^3$, módulo de Young
  $6.2 \times 10^{10}$ Pa, una raya en las celdas del coeficiente de Poisson
  y de la velocidad de barra, velocidad en medio infinito $500$ m/s, producto
  de frecuencia crítica y espesor $130.7$.
- **El problema:** $6.2 \times 10^{10}$ Pa es el módulo de un vidrio, y es el
  valor que la misma tabla imprime para Glass (Pyrex) dos filas más abajo. El
  resto de la fila del corcho lo contradice: con la densidad y la velocidad que
  imprime la propia fila, $\rho c^2 = 250 \times 500^2 = 6.25 \times 10^{7}$
  Pa, unas mil veces menos. La última columna de la tabla concuerda con los
  $500$ m/s y no con el módulo: es $c_0^2/(1.8\,c)$ con $c_0 = 343$ m/s, y
  $343^2/(1.8 \times 500) = 130.7$, que es lo que imprime la página. Los otros
  dos sólidos espumados o celulares del mismo bloque, poliuretano y
  poliestireno, van a $1.9 \times 10^{7}$ y $1.1 \times 10^{7}$ Pa. La mantisa
  es coherente con la fila y el exponente no.
- **Evidencia:** Verificado en la página 625 del PDF (p. impresa 605) de
  Norton & Karczub, *Fundamentals of Noise and Vibration Analysis for
  Engineers* 2e (2003). Los dos módulos, el del corcho y el del Pyrex, se leen
  y son idénticos; la densidad, la velocidad y la última columna de la fila
  del corcho se leen igual de bien y son coherentes entre sí.
- **Qué hace la biblioteca:** la celda se guarda como `misprinted` en
  [`PUBLISHED_SOLIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/catalogue.py), de modo que la
  fila conserva lo que imprime el libro y se niega a servirlo como módulo. La
  página no imprime el exponente que quería decir, así que no se suministra
  ningún valor corregido. El resto de la fila se sirve con normalidad.
- **Estado:** sin comunicar.

## Vigran (2008), tabla 3.1 (un coeficiente de Poisson cuyo segundo extremo ha perdido el punto decimal)

- **Dónde:** tabla 3.1, «Examples of material properties», fila «Aluminium»,
  columna «Poisson's ratio», en la página impresa 88 (página 109 del PDF).
  Fuente no normativa: un libro de texto.
- **Lo impreso:** «0.33–034».
- **El problema:** un coeficiente de Poisson está entre $-1$ y $0.5$, y $034$
  no lo es. La fila de encima, el acero, imprime su intervalo como
  «0.28–0.31» con los dos extremos en decimal, igual que todos los demás
  intervalos de la columna. Al segundo extremo del intervalo del aluminio se
  le ha caído el punto decimal.
- **Evidencia:** Verificado en la página 109 del PDF (p. impresa 88) de
  Vigran, *Building Acoustics* (2008). La celda se lee y dice «0.33–034»; la
  del acero justo encima dice «0.28–0.31».
- **Qué hace la biblioteca:** la celda se guarda como `misprinted` en
  [`PUBLISHED_SOLIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/catalogue.py) y se rechaza.
  El extremo que se quería poner es fácil de adivinar por el patrón, pero la
  página no lo imprime, y esta biblioteca no termina un valor que la página
  dejó sin terminar.
- **Estado:** sin comunicar.

## Rossing (2014), tabla 15.5 (un factor de escala relativo que su propia fila no da)

- **Dónde:** tabla 15.5, «Typical densities and elastic properties of wood
  used for stringed instrument modelling (after Woodhouse)», columna «Maple»,
  fila «Relative scaling factors», en la página impresa 622 (página 632 del
  PDF). Fuente no normativa: un manual.
- **Lo impreso:** la fila imprime su símbolo como $\sqrt[4]{D_1/D_3}$ y los
  valores $1.9$ para la picea y $1.4$ para el arce. El $D_1$ del arce es
  $860$ MPa y su $D_3$, $170$ MPa; la tabla marca con asterisco dos de las
  rigideces del arce como estimaciones, y ninguna de estas dos lo lleva.
- **El problema:** $\sqrt[4]{860/170} = 1.50$, no $1.4$. El factor impreso de
  la picea sí se sigue de su fila: $\sqrt[4]{1100/84} = 1.90$. La misma fila
  imprime la relación y el valor que no la cumple, y la página no dice si lo
  que está mal es el factor o una de las dos rigideces.
- **Evidencia:** Verificado en la página 632 del PDF (p. impresa 622) de
  Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014). El texto de la
  misma página enuncia la relación por su cuenta: «The relative change in
  scaled dimensions is therefore $\sqrt[4]{D_1/D_3}$».
- **Qué hace la biblioteca:** todas las celdas se sirven tal como se imprimen
  en [`PUBLISHED_ORTHOTROPIC_WOOD`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/orthotropic_wood.py),
  porque nada en la página dice cuál de las tres es la equivocada; la fila del
  arce lleva una nota que lo dice, y un test comprueba que la relación se
  cumple en las demás filas.
- **Estado:** sin comunicar.

## Rossing (2014), tabla 11.4 («Open-plane» por una oficina diáfana)

- **Dónde:** tabla 11.4, «Transmission loss and STC values for common
  partitions», novena fila, en la página impresa 413 (página 428 del PDF).
  Fuente no normativa: un manual.
- **Lo impreso:** la fila se rotula «Open-plane office partition», con una
  pérdida por transmisión de $10$ a $12$ dB en todas las bandas y una STC de
  $12$.
- **El problema:** una oficina *open-plan* es una oficina diáfana, sin
  tabiques, y un plano no es una clase de oficina. El rótulo es un desliz
  tipográfico por «Open-plan»; ningún número de la fila se ve afectado, y sus
  valores bajos son los de la mampara que separa puestos en una oficina
  diáfana.
- **Evidencia:** Verificado en la página 428 del PDF (p. impresa 413) de
  Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014); las dos lecturas
  independientes de la página y un recorte de la celda imprimen «Open-plane».
- **Qué hace la biblioteca:** la fila se sirve con el nombre que imprime la
  página, en
  [`PUBLISHED_TRANSMISSION_LOSS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/catalogue.py),
  para que una búsqueda por la palabra impresa la encuentre, y su nota dice
  qué quiere decir.
- **Estado:** sin comunicar.

## Rossing (2014), tabla 8.3 (la línea del 1-pentanol impresa dos veces)

- **Dónde:** tabla 8.3, «B/A values for organic liquids at atmospheric
  pressure», líneas cuarta y quinta del panel izquierdo, en la página impresa
  269 (página 285 del PDF). Fuente no normativa: un manual.
- **Lo impreso:** dos líneas seguidas dicen «1-Pentanol | 20 | 10 | [8.68]»,
  idénticas en todas las celdas.
- **El problema:** todas las demás sustancias de la tabla se nombran una vez y
  dejan el nombre en blanco en sus líneas siguientes, y cada temperatura que
  se repite en una sustancia cita otro artículo o imprime otro valor. Estas dos
  líneas son una sola medida impresa dos veces: las líneas de encima y de
  debajo recorren los 1-alcoholes del propanol al decanol, una línea cada uno
  y todas con el mismo artículo, y el pentanol es el único que aparece dos
  veces.
- **Evidencia:** Verificado en la página 285 del PDF (p. impresa 269) de
  Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014); las dos lecturas
  independientes de la página y un recorte del panel imprimen la línea dos
  veces.
- **Qué hace la biblioteca:** la medida se guarda una vez en
  [`PUBLISHED_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/nonlinearity.py), y su
  nota dice que la página la imprime dos veces.
- **Estado:** sin comunicar.

## Rossing (2014), tabla 8.1 (un año que su propia lista de referencias contradice)

- **Dónde:** tabla 8.1, «B/A values for pure water at atmospheric pressure»,
  columna «Year», las seis filas acreditadas a [8.65], en la página impresa
  268 (página 284 del PDF). Fuente no normativa: un manual.
- **Lo impreso:** las seis filas a 30, 40, 50, 60, 70 y 80 °C acreditadas a
  [8.65] imprimen el año 2001.
- **El problema:** la lista de referencias del capítulo, en la página impresa
  308 (página 324 del PDF), da [8.65] como Plantier, Daridon y Lagourette,
  J. Acoust. Soc. Am. 111, 707-715 (2002). Todas las demás filas de la columna
  imprimen el año que su referencia lleva en esa lista (1974, 1983, 1985, 1989,
  1991), así que la columna es el año de la referencia, y 2001 no es el de
  esta.
- **Evidencia:** Verificado en las páginas 284 y 324 del PDF (pp. impresas 268
  y 308) de Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014), sobre
  las imágenes de las páginas.
- **Qué hace la biblioteca:** en
  [`PUBLISHED_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/nonlinearity.py) las seis
  filas no sirven año y marcan la celda como `misprinted`, citando las dos
  fechas; sus valores y su referencia no cambian.
- **Estado:** sin comunicar.

## Rossing (2014), tabla 8.4 («at atmospheric pressure» para seis gases por encima de su punto de ebullición)

- **Dónde:** tabla 8.4, «B/A values for liquid metals and gases at atmospheric
  pressure», bloque «Liquid gases», en la página impresa 269 (página 285 del
  PDF). Fuente no normativa: un manual.
- **Lo impreso:** el pie da todas las filas a presión atmosférica, y el bloque
  imprime el argón a −183,15 °C, el metano a −153,15, −143,15 y −138,15 °C y el
  nitrógeno a −193,15 y −183,15 °C.
- **El problema:** a una atmósfera el argón hierve a −185,85 °C, el metano a
  −161,49 °C y el nitrógeno a −195,79 °C, así que a esas seis temperaturas cada
  uno es un gas, y solo es líquido a una presión mayor. La propia referencia de
  esas filas, [8.74], se titula en la página 324 del PDF «A study of (B/A) in
  liquified gases as a function of temperature and pressure». No se ponen en
  duda los valores, sino la condición que el pie les atribuye.
- **Evidencia:** Verificado en las páginas 285 y 324 del PDF (pp. impresas 269
  y 308) de Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014), sobre
  las imágenes de las páginas; los puntos de ebullición normales son los del
  NIST Chemistry WebBook.
- **Qué hace la biblioteca:** las seis filas se sirven tal como se imprimen en
  [`PUBLISHED_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/nonlinearity.py), no
  llevan presión, y cada una dice en su nota que la condición del pie no puede
  cumplirse para ella.
- **Estado:** sin comunicar.

## Harris 3e (1995), tabla 30.2 (cinco pesos del pelo cuyas dos mitades no son la misma)

- **Dónde:** tabla 30.2, «Absorción del sonido de alfombras sobre hormigón
  desnudo», columna «Peso del pelo kg/m$^2$ (oz/yd$^2$)», en el folio impreso
  30.22 (página 704 del PDF), capítulo 30 de la edición española. Fuente no
  normativa: un manual.
- **Lo impreso:** cada peso del pelo se imprime dos veces, primero en SI y
  entre paréntesis en unidades estadounidenses: «1,2 (35)», «1,5 (43)» y así,
  once pares en la tabla.
- **El problema:** una onza por yarda cuadrada son $0{,}033906$ kg/m$^2$ por
  definición, y cinco de los once pares no son el mismo número con el
  criterio de la entrada del capítulo 32 (la mitad SI es la conversión
  redondeada o truncada a la precisión con la que se imprime):
  - «2,3 (66)», «3,1 (88)» y «2,1 (60)»: $66 \times 0{,}0339 = 2{,}24$,
    $88 \times 0{,}0339 = 2{,}98$ y $60 \times 0{,}0339 = 2{,}03$. Los tres
    son lo que da $0{,}035$ kg/m$^2$ por oz/yd$^2$, un factor que también
    reproduce todos los pares de las tablas 30.2 y 30.3 que sí cuadran, y por
    eso estos tres salen una décima altos: la columna métrica sigue un factor un
    3 por ciento por encima de la definición.
  - «1,3 (32)»: $32 \times 0{,}0339 = 1{,}08$, y $0{,}035$ da $1{,}12$;
    ninguno llega a $1{,}3$.
  - «1,1 (3,2)»: $3{,}2$ oz/yd$^2$ son $0{,}11$ kg/m$^2$. La misma alfombra,
    de nudo, de nylon cortado con pelo de 14 mm, se imprime «1,1 (32)» en la
    tabla 30.3, así que a la mitad imperial le sobra una coma decimal.
- **Evidencia:** Verificado en la página 704 del PDF (p. impresa 30.22) de
  Harris (ed.), *Manual de medidas acústicas y control del ruido* 3.ª ed.
  (1995); las dos lecturas independientes de la página y un recorte de la
  columna imprimen los cinco pares tal como se citan. Los ocho pares de la
  tabla 30.3, en esa página y la siguiente, cuadran.
- **Qué hace la biblioteca:** en
  [`PUBLISHED_CARPETS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/carpets.py) las
  cuatro filas cuyos kilogramos quedan en duda no sirven peso del pelo y
  marcan la celda como `misprinted`, citando el par; la quinta sirve su 1,1
  kg/m$^2$ y dice en su nota que a las onzas les falta una cifra.
- **Estado:** sin comunicar.

## Rossing (2014), tabla 6.5 («Flourite» por fluorita)

- **Dónde:** tabla 6.5, «Comparison of room-temperature values of the
  ultrasonic nonlinearity parameters of solids», segunda fila, en la página
  impresa 244 (página 261 del PDF). Fuente no normativa: un manual.
- **Lo impreso:** la fila se rotula «Flourite», enlace iónico, beta 3,8.
- **El problema:** la estructura cristalina del fluoruro de calcio es la
  fluorita (*fluorite*); el rótulo intercambia dos letras. Ningún número de la
  fila se ve afectado.
- **Evidencia:** Verificado en la página 261 del PDF (p. impresa 244) de
  Rossing (ed.), *Springer Handbook of Acoustics* 2e (2014), sobre la imagen de
  la página y en la capa de texto del propio PDF, que imprimen las dos
  «Flourite».
- **Qué hace la biblioteca:** la fila se sirve con el nombre impreso en
  [`PUBLISHED_SOLID_NONLINEARITY`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/nonlinearity.py),
  para que una búsqueda por la palabra impresa la encuentre, con la clave
  `fluorite`, y su nota dice qué quiere decir.
- **Estado:** sin comunicar.

## UNE-EN ISO 9295:2015, tablas 1 y 2 (cuarenta y tres celdas donde un 0 del anexo A se imprime como otra cifra)

- **Ubicación:** tablas 1 y 2, «Valores del coeficiente de absorción por el
  aire», en los folios impresos 15 y 16 de la UNE-EN ISO 9295:2015 (octubre
  de 2015), que se declara versión oficial en español de la EN ISO 9295:2015 y
  adopta la ISO 9295:2015 sin modificación. Las dos tablas dan el coeficiente
  de absorción por el aire $\alpha$ en Np/m a una presión estática de
  101,325 kPa, en 26 frecuencias de 10 000 Hz a 22 400 Hz, a 18, 20, 21, 22,
  23, 24, 25 y 27 °C y con humedades relativas del 40 %, el 50 % y el 60 %: 624
  celdas. El apartado 7.2 lleva $\alpha$ de ellas a la constante del recinto de
  la fórmula (7), y el anexo A, normativo, da las fórmulas con las que se
  calculan.
- **Lo impreso:** cada celda lleva cuatro decimales, con coma decimal y la
  última cifra separada, «0,027 7».
- **El problema:** cuarenta y tres celdas contradicen el anexo A, y las
  cuarenta y tres de la misma manera: el valor que da el anexo A acaba en 0, y
  un 0 se imprime como otra cifra. En cuarenta es el cuarto decimal, impreso
  como el tercero repetido («0,027 7» donde el anexo A da 0,027 0). Las otras
  tres son celdas cuyo valor del anexo A acaba en dos ceros (otras dos celdas
  así, ambas 0,020 0 en la tabla 1, a 10 500 Hz, 20 °C y 50 % y a
  11 000 Hz, 18 °C y 60 %, están bien impresas), y ahí es el tercer decimal el
  que toma la cifra anterior: «0,033 0» donde el anexo A da
  0,030 0, y «0,04 4» y «0,05 50», además con los grupos de cifras fuera de
  sitio, donde el anexo A da 0,040 0 y 0,050 0. El defecto se limita a
  los ceros y no es cuestión de redondeo: las otras 581 celdas son el anexo A hasta la
  última cifra (véase la evidencia más abajo), y de las 60 celdas cuyo valor
  del anexo A acaba en 0, estas 43 están mal impresas y 17 se imprimen con su
  0. Los errores van de una unidad del cuarto decimal, cuando la cifra
  repetida es un 1 («0,051 1» por 0,051 0), a 0,005 0 Np/m, donde «0,05 50»
  está por 0,050 0 a 21 500 Hz, 27 °C y 60 %. Las tres celdas cuyo valor del
  anexo A acaba en dos ceros se imprimen exactamente un 10 % altas; llevada a
  la fórmula (7), cualquiera de ellas hace un 10 % mayor el área de absorción
  del aire, y la constante del recinto, y con ella el nivel de potencia
  acústica de la fórmula (6), al menos 0,41 dB demasiado altos. Las
  celdas, por tabla y frecuencia:
  - **Tabla 1, 13 500 Hz** (página 15 del PDF, folio impreso 15): 20 °C y 60 %, «0,027 7» por 0,027 0; 21 °C y 40 %, «0,036 6» por 0,036 0; 21 °C y 60 %, «0,026 6» por 0,026 0; 22 °C y 40 %, «0,035 5» por 0,035 0.
  - **Tabla 1, 15 500 Hz** (página 15 del PDF, folio impreso 15): 22 °C y 40 %, «0,044 4» por 0,044 0.
  - **Tabla 1, 16 500 Hz** (página 15 del PDF, folio impreso 15): 21 °C y 50 %, «0,043 3» por 0,043 0.
  - **Tabla 1, 18 000 Hz** (página 15 del PDF, folio impreso 15): 20 °C y 60 %, «0,045 5» por 0,045 0.
  - **Tabla 1, 19 000 Hz** (página 15 del PDF, folio impreso 15): 21 °C y 60 %, «0,048 8» por 0,048 0.
  - **Tabla 1, 20 000 Hz** (página 15 del PDF, folio impreso 15): 22 °C y 60 %, «0,051 1» por 0,051 0.
  - **Tabla 2, 10 000 Hz** (página 16 del PDF, folio impreso 16): 27 °C y 50 %, «0,014 4» por 0,014 0.
  - **Tabla 2, 11 000 Hz** (página 16 del PDF, folio impreso 16): 25 °C y 50 %, «0,018 8» por 0,018 0.
  - **Tabla 2, 11 500 Hz** (página 16 del PDF, folio impreso 16): 23 °C y 50 %, «0,021 1» por 0,021 0.
  - **Tabla 2, 13 000 Hz** (página 16 del PDF, folio impreso 16): 25 °C y 60 %, «0,021 1» por 0,021 0.
  - **Tabla 2, 13 500 Hz** (página 16 del PDF, folio impreso 16): 27 °C y 60 %, «0,021 1» por 0,021 0.
  - **Tabla 2, 14 000 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 40 %, «0,035 5» por 0,035 0; 24 °C y 60 %, «0,025 5» por 0,025 0.
  - **Tabla 2, 14 500 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 50 %, «0,031 1» por 0,031 0; 25 °C y 40 %, «0,036 6» por 0,036 0; 25 °C y 50 %, «0,033 0» por 0,030 0; 27 °C y 50 %, «0,028 8» por 0,028 0; 27 °C y 60 %, «0,024 4» por 0,024 0.
  - **Tabla 2, 15 000 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 50 %, «0,033 3» por 0,033 0.
  - **Tabla 2, 15 500 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 50 %, «0,035 5» por 0,035 0; 27 °C y 40 %, «0,038 8» por 0,038 0.
  - **Tabla 2, 16 000 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 40 %, «0,044 4» por 0,044 0; 24 °C y 60 %, «0,032 2» por 0,032 0.
  - **Tabla 2, 16 500 Hz** (página 16 del PDF, folio impreso 16): 23 °C y 60 %, «0,035 5» por 0,035 0.
  - **Tabla 2, 17 000 Hz** (página 16 del PDF, folio impreso 16): 25 °C y 50 %, «0,04 4» por 0,040 0.
  - **Tabla 2, 18 000 Hz** (página 16 del PDF, folio impreso 16): 23 °C y 60 %, «0,041 1» por 0,041 0; 27 °C y 60 %, «0,036 6» por 0,036 0.
  - **Tabla 2, 18 500 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 40 %, «0,056 6» por 0,056 0; 24 °C y 50 %, «0,048 8» por 0,048 0.
  - **Tabla 2, 19 500 Hz** (página 16 del PDF, folio impreso 16): 23 °C y 50 %, «0,054 4» por 0,054 0.
  - **Tabla 2, 20 000 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 60 %, «0,048 8» por 0,048 0.
  - **Tabla 2, 20 500 Hz** (página 16 del PDF, folio impreso 16): 23 °C y 40 %, «0,067 7» por 0,067 0; 24 °C y 40 %, «0,066 6» por 0,066 0.
  - **Tabla 2, 21 000 Hz** (página 16 del PDF, folio impreso 16): 23 °C y 60 %, «0,054 4» por 0,054 0.
  - **Tabla 2, 21 500 Hz** (página 16 del PDF, folio impreso 16): 23 °C y 40 %, «0,072 2» por 0,072 0; 24 °C y 40 %, «0,071 1» por 0,071 0; 27 °C y 60 %, «0,05 50» por 0,050 0.
  - **Tabla 2, 22 000 Hz** (página 16 del PDF, folio impreso 16): 24 °C y 60 %, «0,057 7» por 0,057 0; 25 °C y 50 %, «0,063 3» por 0,063 0.
  - **Tabla 2, 22 400 Hz** (página 16 del PDF, folio impreso 16): 25 °C y 50 %, «0,065 5» por 0,065 0.
- **Evidencia:** Verificado en las páginas 15 y 16 del PDF (pp. impresas 15 y
  16) de la UNE-EN ISO 9295:2015, donde cada una de las cuarenta y tres celdas
  se leyó en la página antes de entrar en la lista. El anexo A, en las páginas
  25 y 26 del PDF (pp. impresas 25 y 26) de la misma edición, se evaluó en las
  624 celdas: las 581 que no están en la lista se reproducen hasta el cuarto
  decimal cuando la temperatura se convierte como $\theta + 273{,}16$ K, y de
  las conversiones de $\theta + 273{,}15$ K a $\theta + 273{,}18$ K en pasos
  de 0,002 K es la única que las reproduce todas, así que las tablas se
  calcularon con los 273,16 K del punto triple donde la escala Celsius pone
  273,15 K. Ese desplazamiento es una propiedad de las tablas, no una errata,
  y pequeña: a $\theta + 273{,}15$ K, 61 de las 581 se mueven una unidad del
  cuarto decimal y ninguna más de 0,000 063 Np/m. En una celda de la lista las
  dos conversiones redondean distinto, 19 500 Hz a 23 °C y 50 %, que es
  0,054 0 a 273,16 K y 0,054 1 a 273,15 K frente al 0,054 4 impreso; la
  entrada da siempre la conversión de las propias tablas. El borrador de 2013,
  BS EN ISO 9295 (DPC 13/30264708), imprime las mismas 624 celdas en las
  páginas 15 y 16 del PDF (pp. impresas 7 y 8) de la ISO/DIS 9295, así que el
  defecto pasó del borrador a la norma.
- **Comportamiento de la biblioteca:** no lee las tablas.
  `air_absorption_np_per_m` en
  [`sound_power_high_frequency`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_high_frequency.py)
  evalúa el anexo A con la implementación de la ISO 9613-1 de la biblioteca y
  $T = \theta + 273{,}15$ K, y `room_constant_from_air_absorption` la lleva a
  la fórmula (7). Las 624 celdas están transcritas en
  [`tests/reference_data/emission.py`](https://github.com/jmrplens/phonometry/blob/main/tests/reference_data/emission.py),
  con las cuarenta y tres nombradas en `ISO9295_MISPRINTED_CELLS`;
  [`tests/emission/test_sound_power_high_frequency.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_high_frequency.py)
  y las comprobaciones de conformidad «ISO 9295:2015 Table 1» e «ISO
  9295:2015 Table 2» fijan las 581 hasta la cifra y ciñen cada una de las
  cuarenta y tres a lo que imprime la página: el anexo A con su primer 0 final
  escrito como la cifra anterior.
- **Estado:** sin comunicar.

## UNE-EN ISO 9295:2015, fórmula (A.5) (la frecuencia de relajación del oxígeno escrita con un cero)

- **Ubicación:** anexo A (normativo), «Cálculo del coeficiente de absorción
  por el aire», fórmula (A.5) en el folio impreso 26 de la UNE-EN ISO
  9295:2015 (octubre de 2015), versión oficial en español de la EN ISO
  9295:2015, que adopta la ISO 9295:2015 sin modificación.
- **Lo impreso:** la lista de símbolos del folio impreso 25 define
  $f_{\mathrm{r,O}}$, «frecuencia de relajación del oxígeno», con la letra O, y
  la fórmula (A.3), al principio del folio 26, la calcula con ese nombre. La
  fórmula (A.5), que evalúa $\alpha$ a partir de ella, escribe la misma
  frecuencia como $f_{\mathrm{r,0}}$, con la cifra cero, en los dos sitios
  donde aparece: el denominador $f_{\mathrm{r,0}} + f^2/f_{\mathrm{r,0}}$ del
  término del oxígeno.
- **El problema:** el glifo de (A.5) es la cifra estrecha de
  $p_{\mathrm{s0}}$ en la misma página, no la letra redonda de (A.3), y la capa
  de texto del propio PDF coincide: «f r,O» en la lista de símbolos y en
  (A.3), y «f r,0» dos veces en (A.5). Quien tome el subíndice al pie de la
  letra busca una magnitud $f_{\mathrm{r,0}}$ que el anexo nunca define. La
  fórmula es correcta en cuanto el símbolo se lee como la frecuencia de
  relajación del oxígeno, que es la única frecuencia que da (A.3), así que
  ningún valor de $\alpha$ cambia.
- **Evidencia:** verificado en las páginas 25 y 26 del PDF (pp. impresas 25 y
  26) de la UNE-EN ISO 9295:2015, en la imagen de la página y en la capa de
  texto. El borrador de 2013, BS EN ISO 9295 (DPC 13/30264708), define
  $f_{\mathrm{r,O}}$ en la página 24 del PDF (p. impresa 16) y escribe
  $f_{\mathrm{r,0}}$ en (A.5) en la página 25 del PDF (p. impresa 17), así que
  el desliz pasó del borrador a la norma.
- **Comportamiento de la biblioteca:** no le afecta. `air_absorption_np_per_m`
  en
  [`sound_power_high_frequency`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_high_frequency.py)
  evalúa el anexo A con la implementación de la ISO 9613-1 de la biblioteca,
  que llama `fro` a la frecuencia de relajación del oxígeno, y las 581 celdas
  bien impresas de las tablas 1 y 2 confirman esa lectura.
- **Estado:** sin comunicar.

## IEC 61260-2:2016 / IEC 61260-3:2016, anexo A, Fórmula (A.2) (el coeficiente de los términos de frecuencia sin elevar al cuadrado)

- **Ubicación:** anexo A (informativo), A.1.3, Fórmula (A.2), página impresa
  19 de la IEC 61260-2:2016 y página impresa 16 de la IEC 61260-3:2016, y el
  ejemplo resuelto del A.3.5 en las páginas impresas 21 y 18 respectivamente.
  Las dos partes imprimen el mismo anexo.
- **Lo impreso:** la Fórmula (A.1) es la suma de los coeficientes de
  sensibilidad al cuadrado de la Fórmula (17) de la IEC 61260-1:2014 por las
  incertidumbres típicas al cuadrado, y la Fórmula (A.2) se ofrece como su
  simplificación,
  $$u_{L_\mathrm{c}} = \left[u_{L_\mathrm{in}}^2 + \left(\frac{10}{\ln(10)}\right)^2\left(\frac{u_{T_\mathrm{sweep}}}{T_\mathrm{sweep}}\right)^2 + \left(\frac{10}{\ln(10)}\right)^2\left(\frac{u_{T_\mathrm{avg}}}{T_\mathrm{avg}}\right)^2 + \left(\frac{10}{\ln(f_\mathrm{end}/f_\mathrm{start})\times\ln(10)}\right)\times\left[\left(\frac{u_{f_\mathrm{end}}}{f_\mathrm{end}}\right)^2 + \left(\frac{u_{f_\mathrm{start}}}{f_\mathrm{start}}\right)^2\right]\right]^{1/2}\ \mathrm{dB},$$
  en la que los dos primeros coeficientes llevan el exponente 2 y el tercero
  no. El A.3.5 resuelve después un ejemplo con
  $u_{L_\mathrm{in}} \approx 0{,}042$ dB, $T_\mathrm{sweep} = T_\mathrm{avg} = 20$ s
  con 0,05 s y 0,02 s, $f_\mathrm{end} = 50\,000$ Hz con 5 Hz y
  $f_\mathrm{start} = 0{,}5$ Hz con 0,05 Hz, e imprime
  $u_{L_\mathrm{c}} \approx 0{,}057$ dB, una incertidumbre expandida de
  0,115 dB y 0,128 dB con un visualizador de 0,1 dB de resolución.
- **El problema:** la derivada de la Fórmula (17) respecto a $f_\mathrm{end}$
  es $10/[\ln(f_\mathrm{end}/f_\mathrm{start})\ln(10)\,f_\mathrm{end}]$, y la
  (A.1) la eleva al cuadrado como a todos los demás coeficientes. Sin elevar,
  el coeficiente vale 0,377 para el barrido de cinco décadas del ejemplo, y su
  término de frecuencia es 0,0038 dB² en vez de 0,0014 dB². Tal como está
  impresa, la (A.2) da $u_{L_\mathrm{c}} = 0{,}075$ dB, una incertidumbre
  expandida de 0,150 dB y 0,161 dB con el visualizador; con el cuadrado da
  0,057 dB, 0,115 dB y 0,128 dB, los tres valores que imprimen las dos partes.
  Los dos cálculos usan la $u_{L_\mathrm{in}}$ que deduce el ejemplo,
  0,0416 dB a partir de una resolución de visualizador de 0,1 dB y una
  constancia de 0,03 dB, no los 0,042 dB a los que la redondea, que darían
  0,058 dB. La forma sin cuadrado tampoco está en dB², así que cambia con la
  unidad del nivel.
- **Evidencia:** un recálculo del ejemplo impreso de las dos maneras.
  Verificado en la página 21 del PDF (p. 19 impresa) y en la página 23 del PDF
  (p. 21 impresa) de la IEC 61260-2:2016, y en la página 18 del PDF (p. 16
  impresa) y la página 20 del PDF (p. 18 impresa) de la IEC 61260-3:2016. La
  versión consolidada IEC 61260-2:2016+AMD1:2017 (edición 1.1) imprime la misma
  Fórmula (A.2) en la página 23 del PDF (p. 19 impresa) y los mismos 0,057 dB,
  0,115 dB y 0,128 dB en la página 25 del PDF (p. 21 impresa): la modificación
  solo añade la opción de guía de ondas TEM de la IEC 61000-4-20 al ensayo de
  inmunidad a campos, y el defecto sigue en la edición vigente.
- **Comportamiento de la biblioteca:**
  [`swept_level_uncertainty`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/time_invariance.py)
  eleva el coeficiente al cuadrado, como hace la (A.1), y reproduce 0,057 dB,
  0,115 dB y 0,128 dB; tres filas del informe de conformidad los fijan, y
  `test_formula_a2_as_printed_would_not_reproduce_its_example` en
  [`tests/filters/test_time_invariance.py`](https://github.com/jmrplens/phonometry/blob/main/tests/filters/test_time_invariance.py)
  mantiene la forma impresa en los 0,075 dB que da.
- **Estado:** no reportada.

## IEC 61260-3:2016, B.2.6 (un periodo de promediado que acaba de 6 s a 7 s después de que el barrido pase por 6,3 Hz)

- **Ubicación:** anexo B (informativo), B.2.6, página impresa 20.
- **Lo impreso:** "The averaging period will end 6 s to 7 s after the sweep
  frequency is equal to the lowest midband frequency, 6,3 Hz."
- **El problema:** los propios ajustes del ejemplo lo hacen acabar de 18 s a
  19 s después. El B.2.2 barre de 0,01 Hz a 1 MHz, ocho décadas, en 30 s, es
  decir, 3,75 s por década, y el B.2.3 promedia durante 30 s desde un inicio
  de 0,5 s a 1,5 s antes del barrido. El barrido llega a 6,3 Hz
  $3{,}75 \lg(6{,}3/0{,}01) = 10{,}5$ s después de empezar, que son de 11,0 s a
  12,0 s dentro del promediado, y el promediado acaba a los 30 s. El B.2.3
  comprueba los mismos ajustes en el otro extremo y los acierta: el barrido
  está en 398 kHz a 736 kHz cuando acaba el promediado. La IEC 61260-2:2016
  imprime el mismo ejemplo y, en su propio B.2.6, "18 s to 20 s".
- **Evidencia:** un recálculo a partir del B.2.2 y el B.2.3. Verificado en la
  página 21 del PDF (p. 19 impresa) y en la página 22 del PDF (p. 20 impresa)
  de la IEC 61260-3:2016, y en la página 25 del PDF (p. 23 impresa) de la
  IEC 61260-2:2016.
- **Comportamiento de la biblioteca:** no hace falta ninguno. La frase
  argumenta que la respuesta al impulso del filtro más bajo se ha extinguido
  cuando acaba el promediado, lo que 18 s refuerza, y ningún número del
  ejemplo depende de ella.
  [`verify_time_invariance`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/time_invariance.py)
  dimensiona el promediado a partir del polo más lento del banco que recibe.
- **Estado:** no reportada.

## IEC 61260-2:2016, 7.2.4.3 y Fórmula (3), con IEC 61260-1:2014, 5.16 (la diferencia de la suma tomada en los dos sentidos)

- **Ubicación:** IEC 61260-2:2016, 7.2.4.3 y Fórmula (3) en la página impresa
  11 y 7.2.4.5 en la página impresa 12; IEC 61260-1:2014, 5.16, página impresa
  21.
- **Lo impreso:** el 7.2.4.3 define $\Delta P_j(\Omega_i)$ como "the difference
  between the input signal level minus the reference attenuation and the
  level of the summed output signals" y da
  $$\Delta P_j(\Omega_i) = 10\lg\left[10^{-0{,}1\,\Delta A_{j-1}} + 10^{-0{,}1\,\Delta A_j} + 10^{-0{,}1\,\Delta A_{j+1}}\right]\ \mathrm{dB}.$$
  El 5.16 de la IEC 61260-1 fija los límites "for the difference between (a)
  the level of the input signal minus the reference attenuation and (b) the
  level of the sum of the time-mean-square output signals from adjacent
  filters": +0,8 dB y −1,8 dB para la clase 1, +1,8 dB y −3,8 dB para la
  clase 2. El 7.2.4.5 aplica esos límites a $\Delta P_j(\Omega_i)$
  "calculated according to formula (3)".
- **El problema:** con $\Delta A = A - A_\mathrm{ref}$ y
  $A = L_\mathrm{in} - L_\mathrm{out}$, la Fórmula (3) es el nivel de las
  salidas sumadas menos el nivel de entrada descontada la atenuación de
  referencia, (b) menos (a). El texto de las dos partes nombra (a) menos (b),
  el mismo número con el otro signo. Los límites no son simétricos, así que
  son dos ensayos distintos: un juego cuyas salidas adyacentes suman 1,0 dB
  por encima de la entrada no cumple la clase 1 según la Fórmula (3) y la
  cumple según el texto, y uno cuyas salidas suman 1,0 dB por debajo la
  cumple según la Fórmula (3) y no según el texto.
- **Evidencia:** una comparación de la frase con la fórmula que introduce.
  Verificado en la página 13 del PDF (p. 11 impresa) y en la página 14 del PDF
  (p. 12 impresa) de la IEC 61260-2:2016, y en la página 23 del PDF (p. 21
  impresa) de la BS EN 61260-1:2014. La versión consolidada
  IEC 61260-2:2016+AMD1:2017 (edición 1.1) imprime las mismas palabras y la
  misma Fórmula (3): el 7.2.4.3 va de la página 15 del PDF (p. 11 impresa) a la
  página 16 del PDF (p. 12 impresa), con la Fórmula (3) y el 7.2.4.5 en esta
  última; la modificación no toca el 7.2.4, y el conflicto sigue en la edición
  vigente.
- **Comportamiento de la biblioteca:**
  [`verify_filter_class`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/compliance.py) aplica los
  límites del 5.16 a la Fórmula (3) tal como está impresa, como indica el
  7.2.4.5. Los veredictos que da a los bancos de la propia biblioteca no
  dependen de la lectura: a 48 kHz el banco de octavas suma de −0,06 dB a
  +0,69 dB y el de tercios de octava de −0,25 dB a +0,76 dB, los dos clase 1
  de las dos maneras.
  `test_the_summation_is_what_tones_through_the_bank_read` en
  [`tests/filters/test_pattern_evaluation.py`](https://github.com/jmrplens/phonometry/blob/main/tests/filters/test_pattern_evaluation.py)
  mantiene la Fórmula (3) en lo que lee el banco en marcha.
- **Estado:** no reportada.

## EN 61260:1995, 3.2, NOTA 3 (la razón de octava de base dos rotulada como de base diez)

- **Ubicación:** apartado 3.2, "octave ratio", NOTA 3 y ecuación (2), página
  impresa 4; apartado 3.7, página impresa 5.
- **Lo impreso:** la NOTA 1 del 3.2 dice "This standard permits two options,
  designated base-ten and base-two, for determining an octave-band, or
  fractional-octave-band, frequency ratio." La NOTA 2 dice "For base-ten
  systems, $G_{10} = 10^{3/10}$" como ecuación (1), y la NOTA 3 dice "For
  base-ten systems, $G_2 = 2$" como ecuación (2).
- **El problema:** la NOTA 3 da la razón de base dos, $G_2 = 2$, con el nombre
  del otro sistema, de modo que el apartado nombra dos veces el sistema de base
  diez y ninguna el de base dos. El apartado 3.7 lee la ecuación (2) como se
  pretende: "G represents an octave frequency ratio calculated according to
  equation (1) for base-ten systems or (2) for base-two systems". La NOTA 3
  debería decir "For base-two systems".
- **Evidencia:** leído en la página 8 del PDF (p. 4 impresa) y en la página 9
  del PDF (p. 5 impresa) de la BS EN 61260:1996, que es la EN 61260:1995
  (IEC 61260:1995) con la modificación A1 incorporada, la copia fechada
  "© BSI 23 August 2002".
- **Comportamiento de la biblioteca:** no requiere cambios. Los bancos de
  filtros y [`verify_filter_class`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/compliance.py)
  con `edition="1995"` usan la razón de base diez $G = 10^{3/10}$ de la
  ecuación (1), la que prefiere la NOTA 4, y nada en la biblioteca lee la
  ecuación (2) por su rótulo.
- **Estado:** no reportada.

## IEC 61672-1:2013, tabla 3 (el límite inferior de clase 1 a 6 300 Hz impreso con punto decimal)

- **Ubicación:** tabla 3, "Frequency weightings and acceptance limits", fila
  de 6 300 Hz, columna "Performance class 1", página impresa 22.
- **Lo impreso:** "+1,5; -2.0".
- **El problema:** todos los demás números de la tabla escriben sus
  decimales con coma, como hace la IEC: la celda de clase 2 de
  la misma fila dice "±4,5" y la celda de clase 1 de la fila siguiente
  "+1,5; -2,5". El límite inferior a 6 300 Hz es la única celda escrita con
  punto decimal. El valor no ofrece duda, -2,0 dB, entre el -1,5 dB de
  encima y el -2,5 dB de debajo.
- **Evidencia:** verificado en la página 24 del PDF (p. 22 impresa) de la
  BS EN 61672-1:2013, la implementación británica de la IEC 61672-1:2013
  (segunda edición); la celda es legible y dice "-2.0" junto a "+1,5;".
- **Comportamiento de la biblioteca:** no hace falta ninguno. La biblioteca
  guarda el número, -2.0 dB, en
  [`filters.weighting_class_limits`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/weighting_compliance.py),
  que [`verify_sound_level_meter_periodic`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/metrology/sound_level_meter.py)
  lee para las ponderaciones frecuenciales.
- **Estado:** no reportada.

## ISO 8253-1:2010, 11.1 (la norma de filtros citada como IEC 61620)

- **Ubicación:** apartado 11.1, el párrafo sobre cómo se mide el ruido
  ambiental, página impresa 16.
- **Lo impreso:** «The measurements shall meet the requirements for class 1
  sound level meters of IEC 61672-1 and IEC 61620 and have a noise floor at
  least 6 dB below the sound pressure level being measured.»
- **El problema:** la medición por tercios de octava que pide el 11.1 necesita
  la norma de filtros, la IEC 61260, «Octave-band and fractional-octave-band
  filters», que el capítulo 2 incluye entre las referencias normativas y que
  el 12.4 nombra para el «one-third-octave-band filter set». El capítulo 2 no
  incluye ninguna IEC 61620 y ningún otro apartado la cita: las cifras están
  traspuestas.
- **Evidencia:** la cita leída frente a la lista de la que debería salir.
  Verificado en la página 24 del PDF (p. 16 impresa), en la página 9 del PDF
  (p. 1 impresa) y en la página 30 del PDF (p. 22 impresa) de la BS EN ISO
  8253-1:2010, cuya nota de ratificación adopta la ISO 8253-1:2010 sin
  modificaciones.
- **Comportamiento de la biblioteca:** no hace falta ninguno.
  [`check_audiometric_ambient_noise`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/hearing/audiometry.py)
  recibe los niveles por tercios de octava ya medidos, y su aviso de ruido de
  fondo del equipo es el margen de 6 dB de esa misma frase.
- **Estado:** no reportada (defecto de referencia cruzada, sin consecuencia
  numérica).

## ISO 8253-1:2010, tabla 3, nota a (los nombres de los auriculares marcados con la nota del campo difuso)

- **Ubicación:** tabla 3, nota a, página impresa 18.
- **Lo impreso:** «The values given are based on measurements using pure tones
  in a free sound field and using Telephonics TDH39 with MX 41/AR cushions
  and Beyer DT48 earphones», con la marca de la nota d tras cada uno de los
  tres nombres de producto. La nota d dice «Data are valid for an artificial
  diffuse field according to ISO 4869-1»; la nota e dice «This is a product
  available commercially. This information is given for the convenience of
  users of this International Standard and does not constitute an
  endorsement by ISO of this product.»
- **El problema:** los tres nombres de producto llevan la marca de la nota d,
  que describe los datos del ER-3A y del HDA 200 y dice lo contrario de la
  frase a la que va unida: un campo difuso donde la nota a dice un campo libre
  con tonos puros. La nota que necesitan los nombres de producto es la e, la
  advertencia que los propios encabezados de columna de la tabla ponen a los
  otros dos productos: el encabezado del ER-3A lleva las marcas d, e y f, y el
  del HDA 200, d, e y g.
- **Evidencia:** la nota leída frente a las dos notas que cita y a los
  encabezados de columna. Verificado en la página 26 del PDF (p. 18 impresa)
  de la BS EN ISO 8253-1:2010.
- **Comportamiento de la biblioteca:** no hace falta ninguno. Los valores de
  atenuación de
  [`EARPHONE_ATTENUATION_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/hearing/audiometry.py) son las
  celdas de la tabla y no dependen de las marcas de las notas.
- **Estado:** no reportada (editorial, sin consecuencia numérica).

## ISO 8253-1:2010, A.3.6 (una palabra mal escrita en la incertidumbre del ruido de enmascaramiento)

- **Ubicación:** A.3.6, «Masking noise, $\delta_\mathrm{m}$», página impresa
  25.
- **Lo impreso:** «However, a standard uncertainty of 2 dB may provisionably be
  attributed to $\delta_\mathrm{m}$ with a normal probability distribution if
  masking noise is applied.»
- **El problema:** «provisionably» por «provisionally». Es la palabra que dice
  al lector que los 2 dB son un valor provisional a la espera de cifras mejores,
  así que la errata cae sobre el matiz del valor.
- **Evidencia:** la frase tal como se imprime. Verificado en la página 33 del
  PDF (p. 25 impresa) de la BS EN ISO 8253-1:2010, cuya nota de ratificación
  adopta la ISO 8253-1:2010 sin modificaciones.
- **Comportamiento de la biblioteca:** no hace falta ninguno.
  [`audiometric_uncertainty`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/hearing/audiometry.py) toma los
  2 dB del A.3.6 con `masked=True`; ningún número depende de la palabra.
- **Estado:** no reportada (editorial, sin consecuencia numérica).

## ISO 8253-2:2009, anexo B (la tabla B.1 anunciada desde 200 Hz e impresa desde 125 Hz)

- **Ubicación:** anexo B (informativo), el párrafo sobre la tabla B.1 y la
  propia tabla, página impresa 15.
- **Lo impreso:** «Table B.1 gives figures for the increased sound pressure
  levels at test frequencies from 200 Hz to 12 500 Hz at angles of incidence
  45° and 90°». Las primeras filas de la tabla son 125 Hz (0,5 dB y 1 dB) y
  160 Hz (1 dB y 1,5 dB).
- **El problema:** la tabla empieza en 125 Hz, dos filas por debajo del
  intervalo que el texto le anuncia. Quien se fíe de la frase descarta dos
  filas impresas; quien se fíe de la tabla tiene un texto que dice que no
  están. La fila de 125 Hz es la que necesita la audiometría en campo sonoro,
  cuyo intervalo principal empieza en 125 Hz (capítulo 1).
- **Evidencia:** la frase leída frente a las filas que presenta. Verificado en
  la página 21 del PDF (p. 15 impresa) de la ISO 8253-2:2009.
- **Comportamiento de la biblioteca:**
  [`INCIDENCE_CORRECTIONS_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/hearing/sound_field_audiometry.py)
  lleva todas las filas impresas, de 125 Hz a 12 500 Hz, e
  [`incidence_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/hearing/sound_field_audiometry.py)
  las lee. La comprobación de conformidad «ISO 8253-2:2009 Table B.1» cuenta
  las 48 celdas, entre ellas las cuatro por debajo de 200 Hz.
- **Estado:** no reportada.

## ISO 4869-3:2007, 5.2.2 y tabla 1 (un índice de micrófono de exactamente 5 dB en dos filas)

- **Ubicación:** apartado 5.2.2, el párrafo sobre el ensayo direccional, y la
  tabla 1, página impresa 4.
- **Lo impreso:** 5.2.2: «the range of sound pressure levels at the reference
  point shall be within 5 dB for any two directions of measurement of the
  incident sound energy when measured with a directional microphone with a
  front-to-random sensitivity index of at least 5 dB. For other directional
  microphones, the relationship between the front-to-random sensitivity index
  and the allowable field variations is given in Table 1.» La tabla 1 imprime
  las filas «> 5» (5 dB), «4 to 5» (4 dB) y «< 4» (micrófono no adecuado).
- **El problema:** un micrófono cuyo índice es exactamente 5 dB puede leer
  5 dB según el texto, que pide «at least 5 dB», y 4 dB según la tabla, cuya
  primera fila excluye el 5 y cuya segunda lo incluye. La variación admisible
  del único micrófono que nombra el texto queda, pues, sin decidir en la
  página. La ISO 8253-2:2009, que imprime el mismo ensayo direccional en su
  5.3 b), escribe la primera fila de su propia tabla 1 como «≥ 5».
- **Evidencia:** la tabla leída frente a la frase que la presenta. Verificado
  en la página 8 del PDF (p. 4 impresa) de la ISO 4869-3:2007 y en la página
  13 del PDF (p. 7 impresa) de la ISO 8253-2:2009.
- **Comportamiento de la biblioteca:** sigue al texto.
  [`RANDOM_INCIDENCE_VARIATION_LIMITS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/hearing/earmuff_insertion_loss.py)
  admite 5 dB desde un índice de 5 dB y 4 dB desde 4 dB hasta por debajo de
  5 dB, y la comprobación de conformidad «ISO 4869-3:2007 5.2.2, Table 1» fija
  la fila de 5 dB. Un campo que cumple 4 dB pasa con cualquiera de las dos
  lecturas.
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, Tabla 7 (la fila de 10 °C y 80 % calculada a −10 °C)

- **Ubicación:** 12.5.2.4, Tabla 7 "Upper tone search frequencies based on a
  range of distance and meteorological conditions" (folio impreso 45), la fila
  "10 | 80".
- **Lo impreso:** 10, 5, 2,5 y 2 kHz a 100 m, 300 m, 600 m y 1 000 m.
- **El problema:** el 12.5.2.4 sitúa el techo de la búsqueda de tonos en la
  banda de tercio de octava más baja que la ISO 9613-1 atenúa 20 dB o más en
  la distancia al aerogenerador más cercano. A 10 °C y 80 % de humedad
  relativa esa banda es 10, 6,3, 5 y 4 kHz. Las celdas impresas son lo que da
  la misma regla a −10 °C y 80 %, celda a celda. Las otras cuatro filas se
  reproducen con su propia atmósfera (el "3,2" de la fila de −10 °C y 100 % es
  la banda de 3,15 kHz), así que o la temperatura de la fila perdió su signo
  menos o sus celdas se calcularon a otra temperatura. A los 10 °C y 80 % que
  imprime la fila, se lee **10, 6,3, 5 y 4 kHz**.
- **Evidencia:** la regla del 12.5.2.4 evaluada con la ISO 9613-1 en las
  frecuencias centrales exactas y a 101,325 kPa para las veinte celdas de la
  tabla. Tabla 7 leída en la página 47 del PDF (p. 45 impresa) de la IEC TS
  61400-11-2:2024 (edición 1.0, 2024-03).
- **Comportamiento de la biblioteca:** `upper_tone_search_frequency` aplica la
  regla del 12.5.2.4 y nunca lee la Tabla 7, así que no hizo falta ningún
  cambio. Las filas de conformidad comprueban las cuatro filas que se cumplen
  y la cuarta fila impresa a −10 °C
  (`test_table_7_fourth_row_is_minus_10_degrees` en
  [`tests/environment/assessment/test_wind_turbine_receptor.py`](https://github.com/jmrplens/phonometry/blob/main/tests/environment/assessment/test_wind_turbine_receptor.py)).
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, 12.5.2.6 y 12.5.2.7 (ISO/TS 60025:2022 por ISO/TS 20065:2022)

- **Ubicación:** 12.5.2.6 "Frequency grouping" (folio impreso 46) y 12.5.2.7
  "Determination of mean audibility for each 1 min period" (folio impreso 47).
- **Lo impreso:** el 12.5.2.6 cita primero "ISO method (ISO/TS 20065:2022),
  5.3.8, Step 1 and Step 2", y después "ISO method (ISO/TS 60025:2022),
  5.3.8, Step 3", "ISO method (ISO/TS 60025:2022), Figure D.4" e "ISO method
  (ISO/TS 60025:2022), 5.3.8, Step 1 and Step, in turn"; el 12.5.2.7 cita
  "ISO method (ISO/TS 60025:2022), 5.3.9".
- **El problema:** el 12.1 define el "ISO method" como la ISO/TS 20065, su
  NOTA 1 cita la ISO/TS 20065:2022 y la primera frase del 12.5.2.6 la cita
  bien; no existe ninguna ISO/TS 60025. Las cuatro citas siguientes se leen
  **ISO/TS 20065:2022**, y "Step 1 and Step" se lee "Step 1 and Step 2", los
  dos pasos que nombra la primera frase.
- **Evidencia:** una comparación de las citas entre sí y con el 12.1. Leído en
  la página 44 del PDF (p. 42 impresa), la página 48 del PDF (p. 46 impresa) y
  la página 49 del PDF (p. 47 impresa) de la IEC TS 61400-11-2:2024 (edición
  1.0, 2024-03).
- **Comportamiento de la biblioteca:** no hace falta ninguno. La agrupación de
  frecuencias del 12.5.2.6 y la media de 1 min del 12.5.2.7 no están
  implementadas; la audibilidad tonal que calcula la biblioteca es la de la
  ISO/PAS 20065:2016
  ([`tone_audibility.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/tone_audibility.py)).
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, 13.6.2.2 frente a 13.6.3 (un periodo de 10 min con exactamente 30 bloques válidos)

- **Ubicación:** 13.6.2.2 "Valid data" (folio impreso 51) y 13.6.3 "Signal
  analysis – 10 min results" (folio impreso 54).
- **Lo impreso:** 13.6.2.2: el percentil 90 "is only calculated over the
  distribution of valid 10 s blocks, and only if the 10 min period contains at
  least 50 % valid blocks". 13.6.3: "where the n number is greater than 50 %
  (30 valid 10 s blocks), calculate the 90th percentile of the valid
  modulation depths" y "where the n number is less than 50 % (30 valid 10 s
  blocks), a modulation depth value of 0 is assigned to that 10 min period".
- **El problema:** un periodo de sesenta bloques con exactamente 30 válidos se
  valora según el 13.6.2.2 ("at least 50 %") y no cae en ninguno de los dos
  apartados del 13.6.3, cuyo "greater than" y cuyo "less than" lo dejan fuera.
  El informe final del AMWG que implementa la cláusula (13.2) dice "at least
  50 % (i.e. 30) valid samples" (4.4.4), y el código de referencia del grupo
  de trabajo valora un periodo de 30. Los apartados del 13.6.3 se leen
  **"at least 50 %"** y **"fewer than 50 %"**.
- **Evidencia:** una comparación de los dos apartados y del informe del AMWG.
  Leído en la página 53 del PDF (p. 51 impresa) y en la página 56 del PDF
  (p. 54 impresa) de la IEC TS 61400-11-2:2024 (edición 1.0, 2024-03), y el
  4.4.4 en la página 23 del PDF (p. 20 impresa) del IOA AMWG Final Report,
  Version 1 (9 de agosto de 2016).
- **Comportamiento de la biblioteca:** `amplitude_modulation_period` valora
  un periodo de 30 bloques válidos, como hacen el 13.6.2.2 y el informe del
  AMWG (`AM_MINIMUM_VALID_BLOCKS`); las filas de conformidad fijan los
  periodos de 30 y de 29 bloques válidos
  (`test_periods_agree_with_the_ioa_code_and_the_ts` en
  [`tests/environment/assessment/test_wind_turbine_modulation.py`](https://github.com/jmrplens/phonometry/blob/main/tests/environment/assessment/test_wind_turbine_modulation.py)).
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, Figura 1 ("Power specimen amplitude", "Initiate estimate")

- **Ubicación:** 13.6.2.3, Figura 1 "Power spectrum for a 10 s block" (folio
  impreso 54).
- **Lo impreso:** el eje vertical se rotula "Power specimen amplitude, $S$" y
  la leyenda dice "Initiate estimate of $f_1$ and $f_2$".
- **El problema:** el eje es el espectro de potencia de la Ecuación (12), que
  nombran el título de la figura y el 13.6.2.3 c); "specimen" se lee
  **spectrum**. Las líneas discontinuas son las estimaciones iniciales de los
  armónicos, como dicen la NOTA bajo la figura y las anotaciones dentro de
  ella ("Initial $f_1$ estimate = 1,4 Hz"); "Initiate" se lee **Initial**.
- **Evidencia:** la Figura 1 y su NOTA en la página 56 del PDF (p. 54
  impresa) de la IEC TS 61400-11-2:2024 (edición 1.0, 2024-03).
- **Comportamiento de la biblioteca:** no hace falta ninguno;
  `ModulationBlock.plot()` rotula el eje "Power spectrum $S_{xx}$" y las
  líneas "Estimated harmonics".
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, Tabla C.2 (la atenuación del aire de una atmósfera al 80 % bajo un título que dice 70 %)

- **Ubicación:** anexo C (informativo), C.2, Tabla C.2 "Equation coefficients
  for a rural setting at 70 % humidity and 10 °C" (folio impreso 64), la fila
  "α [dB/km]", y la frase bajo la tabla.
- **Lo impreso:** 0,0, 0,0, 0,0, 0,0, 0,02, 0,03, 0,05, 0,07, 0,11, 0,17,
  0,26, 0,41, 0,59 y 0,80 dB/km de 10 Hz a 200 Hz, y "The air absorption
  coefficient is calculated according to ISO 9613-1."
- **El problema:** la ISO 9613-1 a los 10 °C y 70 % de humedad relativa del
  título, a 101,325 kPa y en las frecuencias centrales nominales, da con dos
  decimales 0,01, 0,01, 0,02 y 0,02 dB/km más que la tabla a 50 Hz, 63 Hz,
  80 Hz y 100 Hz (0,08, 0,12, 0,19 y 0,28), y 0,01 dB/km donde la tabla
  imprime 0,0 de 12,5 Hz a 20 Hz; de 125 Hz a 200 Hz da las celdas impresas.
  Las celdas de 10 Hz a 100 Hz son las de la orden danesa sobre el ruido de
  aerogeneradores, BEK nr. 135 de 7 de febrero de 2019, Tabla 1.4, fijada para
  un **80 %** de humedad relativa y 10 °C, que usa las tasas de atenuación de
  Nord2000 e ignora la absorción del aire por debajo de 25 Hz, como recomienda
  Plovsing (DELTA, 2011), Tabla 5; al 80 % la ISO 9613-1 da 0,07, 0,11, 0,17 y
  0,25 dB/km de 50 Hz a 100 Hz, a menos de 0,01 dB/km de ellas. La fila une
  dos atmósferas en 100 Hz, y quien la recalcule con la del título no puede
  reproducir su mitad baja. La diferencia es de 0,02 dB/km como mucho, unas
  centésimas de decibelio de la Ecuación (C.1) en las distancias a las que se
  aplica el anexo C.
- **Evidencia:** la ISO 9613-1 evaluada con las dos humedades en las catorce
  bandas. Tabla C.2 leída en la página 66 del PDF (p. 64 impresa) de la IEC TS
  61400-11-2:2024 (edición 1.0, 2024-03); la Tabla 1.4 en las páginas 13 y 14
  del PDF (pp. 12 y 13 impresas) de la BEK nr 135 af 07/02/2019; la Tabla 5 en
  la página 25 del PDF (p. 25 impresa) de B. Plovsing, *Beregningsmetode for
  lavfrekvent støj fra vindmøller*, Miljøstyrelsen arbejdsrapport nr. 2, 2011.
- **Comportamiento de la biblioteca:** `LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM`
  guarda la fila tal como se imprime y es el valor por defecto de
  `wind_turbine_low_frequency_level`, que reproduce la TS y la orden danesa;
  quien quiera la ISO 9613-1 con otra atmósfera pasa
  `air_attenuation_db_per_km`. Las filas de conformidad comprueban la fila
  frente a las dos atmósferas
  (`test_table_c2_air_attenuation_to_100_hz_is_the_danish_order_at_80_percent`
  en
  [`tests/environment/assessment/test_wind_turbine_receptor.py`](https://github.com/jmrplens/phonometry/blob/main/tests/environment/assessment/test_wind_turbine_receptor.py)).
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, C.4 (la incertidumbre remitida al 9.2, que trata del muestreo de datos)

- **Ubicación:** anexo C (informativo), C.4 "Uncertainty" (folio impreso 65).
- **Lo impreso:** "The principles from 9.2 on uncertainty can be applied to
  each 1/3-octave band individually."
- **El problema:** el 9.2 es "Data sampling" de las medidas no acústicas y no
  dice nada de la incertidumbre. Los principios son los del **10.3**
  "Uncertainty", al que remiten con el mismo fin el 12.5.4 y el 13.6.5.
- **Evidencia:** una comparación de la remisión con el índice y con el 12.5.4
  y el 13.6.5. Leído en la página 67 del PDF (p. 65 impresa), la página 49 del
  PDF (p. 47 impresa) y la página 57 del PDF (p. 55 impresa) de la IEC TS
  61400-11-2:2024 (edición 1.0, 2024-03).
- **Comportamiento de la biblioteca:** no hace falta ninguno;
  `wind_turbine_low_frequency_level` no calcula ninguna incertidumbre.
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, Tabla C.4 (el término de distancia sumado donde la Ecuación (C.1) lo resta)

- **Ubicación:** anexo C (informativo), C.5, Tabla C.4 "Low frequency
  measurements reporting table" (folio impreso 66), la tercera fila.
- **Lo impreso:** la fila se rotula "+ 10log ($l^2$ +$h^2$)", entre la fila
  de la ponderación A y la fila "− 11 dB".
- **El problema:** la Ecuación (C.1) resta el término,
  $L_{p,\mathrm{LF}} = L_{W,\mathrm{LF}} - 10\lg(l^2 + h^2) - 11\ \mathrm{dB} +
  \Delta L_{g,\mathrm{LF}} - \Delta L_a - \Delta L_\sigma$, y todas las demás
  filas de la tabla llevan el signo con el que entran en la ecuación.
  Rellenada como dice el rótulo, la tabla suma al nivel dos veces el término
  de distancia. La fila se lee **"− 10log ($l^2$ + $h^2$)"**.
- **Evidencia:** la Ecuación (C.1) en la página 65 del PDF (p. 63 impresa) y
  la Tabla C.4 en la página 68 del PDF (p. 66 impresa) de la IEC TS
  61400-11-2:2024 (edición 1.0, 2024-03).
- **Comportamiento de la biblioteca:** `wind_turbine_low_frequency_level`
  evalúa la Ecuación (C.1) y devuelve el término que resta como
  `distance_terms_db`; la fila de conformidad de la Ecuación (C.1) comprueba
  el signo (`test_equation_c1_band_by_band` en
  [`tests/environment/assessment/test_wind_turbine_receptor.py`](https://github.com/jmrplens/phonometry/blob/main/tests/environment/assessment/test_wind_turbine_receptor.py)).
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, G.3 (bandas que acaban en 3 200 Hz y 6 400 Hz, que no son frecuencias centrales)

- **Ubicación:** anexo G (informativo), G.3 "Higher frequency bands" (folio
  impreso 73).
- **Lo impreso:** "These bands are suggested to include the seven 1/3-octave
  bands with centres of: Band 4: 400 Hz to 1 600 Hz; Band 5: 800 Hz to
  3 200 Hz; Band 6: 1 600 Hz to 6 400 Hz".
- **El problema:** 3 200 Hz y 6 400 Hz no son frecuencias centrales de tercio
  de octava. Siete bandas abarcan dos octavas, y la frecuencia central nominal
  dos octavas por encima de 800 Hz es 3 150 Hz, y por encima de 1 600 Hz es
  6 300 Hz; la banda 4 acaba bien solo porque 1 600 Hz es a la vez cuatro
  veces 400 Hz y una frecuencia central nominal. Los extremos se leen
  **3 150 Hz** y **6 300 Hz**.
- **Evidencia:** las siete frecuencias centrales nominales de tercio de octava
  contadas desde cada extremo inferior. Leído en la página 75 del PDF (p. 73
  impresa) de la IEC TS 61400-11-2:2024 (edición 1.0, 2024-03).
- **Comportamiento de la biblioteca:** `AM_FREQUENCY_BANDS_HZ` guarda las
  bandas 5 y 6 con las bandas nominales de 3 150 Hz y 6 300 Hz como séptima.
- **Estado:** no reportada.

## IEC TS 61400-11-2:2024, K.4.9 (una frase que se queda en una coma)

- **Ubicación:** anexo K (informativo), K.4.9 "Roughness length" (folio
  impreso 85).
- **Lo impreso:** "Table K.3 is provided below as a reminder. Since this is a
  crude estimate, valid only for cloudy conditions and long-term average,",
  seguido de líneas en blanco y del párrafo siguiente, "K.4.3 gives some
  guidance on how to determine an apparent roughness length ...".
- **El problema:** la frase tiene una subordinada y ninguna principal; lo que
  implica la estimación burda se pierde. El párrafo siguiente sugiere que iba
  a remitir al lector al K.4.3 para una longitud de rugosidad obtenida del
  emplazamiento.
- **Evidencia:** el K.4.9 en la página 87 del PDF (p. 85 impresa) de la IEC TS
  61400-11-2:2024 (edición 1.0, 2024-03).
- **Comportamiento de la biblioteca:** no hace falta ninguno;
  `ROUGHNESS_LENGTHS_M` guarda la Tabla K.3 y su docstring recoge el aviso de
  la TS de que los valores son una estimación burda.
- **Estado:** no reportada.

## ISO/DIS 16032:2023, anexo A, tabla A.1 (la ponderación C de los tercios de octava a 25 Hz y desde 1 600 Hz)

- **Ubicación:** anexo A (normativo), tabla A.1 «A-weighting and C-weighting
  correction values», la columna de ponderación C de los tercios de octava, en
  el texto inglés de la E DIN EN ISO 16032:2023-05 (p. 12 impresa) y en el
  texto alemán de la misma publicación (Tabelle A.1, p. 19 impresa).
- **El impreso:** la ponderación C de los tercios de octava da −5 dB a 25 Hz,
  −3 dB a 31,5 Hz y −2 dB a 40 Hz, luego de −1,3 dB a −0,1 dB entre 50 Hz y
  160 Hz, y 0 dB en todas las bandas de 200 Hz a 10 000 Hz. Las columnas de
  octava de la misma tabla imprimen −0,2 dB a 2 000 Hz, −0,8 dB a 4 000 Hz y
  −3,0 dB a 8 000 Hz; la primera banda de octava está rotulada «31».
- **El problema:** la columna de tercios contradice a la de octavas que tiene
  al lado a 2 000 Hz, 4 000 Hz y 8 000 Hz, y la IEC 61672-1, cuyas
  ponderaciones nombra el 4.1, da −4,4 dB a 25 Hz y −0,1, −0,2, −0,3, −0,5,
  −0,8, −1,3, −2,0, −3,0 y −4,4 dB de 1 600 Hz a 10 000 Hz. La columna se
  detiene en 1 250 Hz, como si solo se hubiera rellenado su mitad de
  frecuencias bajas; las columnas de ponderación A coinciden con la
  IEC 61672-1 en todas las celdas. Leída tal como está impresa, un nivel
  ponderado C calculado a partir de tercios de octava sobrestima un espectro
  con energía por encima de 1 kHz: un espectro plano de 25 Hz a 10 000 Hz suma
  0,4 dB más que con la ponderación de la IEC 61672-1, un tercio de la
  desviación típica de reproducibilidad de 1,2 dB que la tabla 2 da al valor
  ponderado C.
- **Evidencia:** la columna de tercios frente a la de octavas de la misma
  tabla y frente a la tabla 3 de la IEC 61672-1:2013. Verificado en la página
  50 del PDF (p. 12 impresa) y en la página 23 del PDF (p. 19 impresa) de la
  E DIN EN ISO 16032:2023-05, la publicación alemana del ISO/DIS 16032:2023
  (prEN ISO 16032:2023, texto alemán e inglés), y en la página 24 del PDF
  (p. 22 impresa) de la BS EN 61672-1:2013.
- **Comportamiento de la biblioteca:**
  [`SERVICE_EQUIPMENT_WEIGHTING`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/measurement/service_equipment.py)
  conserva todas las celdas impresas salvo las diez mal impresas, que toman
  los valores de la IEC 61672-1;
  `test_third_octave_c_weighting_departs_from_print_only_in_the_defect` y la
  comprobación de conformidad «ISO/DIS 16032:2023 Annex A, Table A.1 against
  IEC 61672-1:2013 Table 3» fijan qué celdas salen de dónde.
- **Estado:** sin notificar (el documento es un borrador en consulta).

## ISO/DIS 16032:2023, 7.6 (la corrección por ruido de fondo remitida al capítulo 8, el tiempo de reverberación)

- **Ubicación:** 7.6 «Determination of the background sound pressure level»,
  última frase (p. 8 impresa del texto inglés, p. 15 impresa del alemán).
- **El impreso:** «Corrections for background sounds are applied according
  to Clause 8.» El texto alemán dice «Die Korrekturen für
  Hintergrundgeräusche werden nach Abschnitt 8 angewendet.»
- **El problema:** el capítulo 8 es «Measurement of reverberation time»; la
  corrección por ruido de fondo es el capítulo 9, «Correction for background
  noise». En la edición de 2004 la corrección era el capítulo 8 y el 6.6
  remitía a él; el borrador insertó un capítulo delante y no movió la
  referencia.
- **Evidencia:** la referencia leída frente a los títulos de los capítulos
  del borrador y de la edición que revisa. Verificado en la página 46 del PDF
  (p. 8 impresa) y en la página 47 del PDF (p. 9 impresa) de la
  E DIN EN ISO 16032:2023-05 para el texto inglés, en la página 19 del PDF
  (p. 15 impresa) para el alemán, y en la página 13 del PDF (p. 11 impresa) y
  en la página 14 del PDF (p. 12 impresa) de la BS EN ISO 16032:2004.
- **Comportamiento de la biblioteca:** no requiere cambios; la corrección que
  aplica
  [`service_equipment_background_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/measurement/service_equipment.py)
  es la del capítulo 9.
- **Estado:** sin notificar (el documento es un borrador en consulta).

## ISO/DIS 16032:2023, B.10 (la elección de la esquina remitida al capítulo 6)

- **Ubicación:** B.10 «Measurements of unknown sources or under unknown
  operating conditions», último párrafo (p. 19 impresa del texto inglés,
  p. 27 impresa del alemán).
- **El impreso:** «In the case the sound of interest appears very irregularly
  and unpredictable, the selection procedure in clause 6 may be impossible to
  follow.» El texto alemán dice «das Auswahlverfahren nach Abschnitt 6».
- **El problema:** el capítulo 6 es la parte general del método de ensayo y
  no describe ninguna elección. El procedimiento que el párrafo sustituye,
  escoger la esquina con el nivel ponderado C más alto, es el 7.2, y la frase
  que sigue, que pone la posición 1 en la esquina más reflectante y las
  posiciones 2 y 3 «as described», habla del 7.2 y del 7.3.
- **Evidencia:** la referencia leída frente al apartado al que puede
  referirse. Verificado en la página 57 del PDF (p. 19 impresa), en la página
  44 del PDF (p. 6 impresa) y en la página 45 del PDF (p. 7 impresa) de la
  E DIN EN ISO 16032:2023-05, y en la página 31 del PDF (p. 27 impresa) para
  el texto alemán.
- **Comportamiento de la biblioteca:** no requiere cambios; la guía remite al
  lector al 7.2 y
  [`loudest_corner`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/measurement/service_equipment.py)
  lo implementa.
- **Estado:** sin notificar (el documento es un borrador en consulta).

## ISO/DIS 16032:2023, 7.4.1 (sin regla para una dispersión de exactamente 6,0 dB o 9,0 dB)

- **Ubicación:** 7.4.1 «Measurement of the equivalent continuous sound
  pressure level», los cuatro párrafos que siguen al primero (p. 8 impresa
  del texto inglés, pp. 14 y 15 impresas del alemán).
- **El impreso:** tres lecturas separadas «equal to, or less than 3,0 dB»
  siguen adelante; una diferencia que «exceeds 3,0 dB but is less than
  6,0 dB» añade las posiciones 4 y 5, y seis lecturas separadas «less than
  6,0 dB» siguen adelante; una diferencia que «exceeds 6,0 dB but is less than
  9,0 dB» añade las posiciones 6 y 7, y nueve lecturas separadas «less than
  9,0 dB» siguen adelante. «If the difference is larger than 9,0 dB and is
  related to unpredictable time domain variations whereas the readings in the
  corner position confirm the sound source is stable, then the measurement
  session shall be interrupted»: se investigan las causas antes de una serie
  nueva y no se usa ningún dato de la serie interrumpida.
- **El problema:** la escalera no da ningún paso para seis lecturas separadas
  exactamente 6,0 dB (ni «less than 6,0 dB» ni «exceeds 6,0 dB») ni para nueve
  separadas exactamente 9,0 dB (ni «less than» ni «larger than»). Tampoco dice
  adónde llevan tres lecturas separadas 6,0 dB o más, porque el párrafo
  siguiente está escrito para las seis, y las posiciones 6 y 7 solo responden
  a una diferencia «less than 9,0 dB», así que tres o seis lecturas separadas
  ya 9,0 dB o más no tienen ningún paso antes del párrafo de la interrupción,
  cuyas dos condiciones no se pueden decidir leyendo los niveles. El primer
  umbral es inclusivo y los otros dos estrictos, así que el hueco no es
  cuestión de un convenio aplicado de principio a fin.
- **Evidencia:** los cuatro párrafos leídos unos frente a otros. Verificado
  en la página 46 del PDF (p. 8 impresa) de la E DIN EN ISO 16032:2023-05, y
  en las páginas 18 y 19 del PDF (pp. 14 y 15 impresas) para el texto alemán.
  La edición de 2004 no tenía esta escalera: su 6.4.1 fijaba el número de
  lecturas a partir de la diferencia entre dos lecturas en la esquina (página
  13 del PDF, p. 11 impresa, de la BS EN ISO 16032:2004).
- **Comportamiento de la biblioteca:**
  [`check_position_spread`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/measurement/service_equipment.py)
  lee la escalera como una secuencia: una etapa que no se supera pasa a la
  siguiente, y una dispersión igual a un límite estricto no lo supera, así que
  seis lecturas separadas exactamente 6,0 dB añaden las posiciones 6 y 7 y
  nueve separadas exactamente 9,0 dB interrumpen la sesión. Una dispersión
  solo puede crecer al añadir lecturas, así que tres o seis lecturas separadas
  ya 9,0 dB o más interrumpen la sesión en el acto en lugar de pedir
  posiciones que no pueden llevar a un promedio. Si la diferencia se debe a
  variaciones imprevisibles en el tiempo mientras las lecturas en la esquina
  muestran una fuente estable queda en manos de quien mide: la comprobación
  dice que ninguna etapa puede superarse, no por qué. La comprobación de
  conformidad «ISO/DIS 16032:2023 7.4.1» sostiene los dos límites y la
  interrupción anticipada.
- **Estado:** sin notificar (el documento es un borrador en consulta).

## ISO/DIS 16032:2023, 4.8, fórmula (5) (el nivel máximo con ponderación S nombrado dos veces)

- **Ubicación:** 4.8, la lista bajo la fórmula (5) (p. 5 impresa del texto
  inglés, p. 11 impresa del alemán).
- **El impreso:** «$L$ can be $L_\mathrm{Smax}$ or $L_\mathrm{Fmax}$ or
  $L_\mathrm{Smax}$ or $L_\mathrm{eq}$»; la lista bajo la fórmula (6) de la
  misma página dice «$L_\mathrm{Smax}$ or $L_\mathrm{Fmax}$ or
  $L_\mathrm{eq}$».
- **El problema:** $L_\mathrm{Smax}$ aparece repetido; las dos listas quieren
  decir las mismas tres magnitudes, como confirman el 4.6.2, el 4.6.5 y el
  4.6.8, que estandarizan cada una de ellas con la fórmula (5).
- **Evidencia:** las dos listas de la misma página. Verificado en la página 43
  del PDF (p. 5 impresa) de la E DIN EN ISO 16032:2023-05 y en la página 15
  del PDF (p. 11 impresa) para el texto alemán.
- **Comportamiento de la biblioteca:** no requiere cambios; las tres
  magnitudes se estandarizan igual.
- **Estado:** sin notificar (el documento es un borrador en consulta).

## ISO/DIS 16032:2023, 4.2 (las bandas atribuidas a «IEC 612604.3»)

- **Ubicación:** 4.2 «frequency bands», última línea (p. 2 impresa del texto
  inglés, p. 8 impresa del alemán).
- **El impreso:** «with centre frequencies and bandwidths defined in IEC
  612604.3».
- **El problema:** no existe tal documento. La referencia es la IEC 61260,
  que figura en el capítulo 2, pegada al número de la definición siguiente,
  4.3, que viene en la línea de abajo.
- **Evidencia:** la referencia frente al capítulo 2 y al encabezado que la
  sigue. Verificado en la página 40 del PDF (p. 2 impresa) y en la página 39
  del PDF (p. 1 impresa) de la E DIN EN ISO 16032:2023-05, y en la página 12
  del PDF (p. 8 impresa) para el texto alemán.
- **Comportamiento de la biblioteca:** no requiere cambios; las frecuencias
  centrales nominales que acepta el módulo son las de la IEC 61260-1.
- **Estado:** sin notificar (el documento es un borrador en consulta).

## IEC 61063:1991, 8.3 ($L_{p\mathrm{A}I}$ por $L_{p\mathrm{A}i}$)

- **Ubicación:** apartado 8.3, la lista de definiciones bajo la Ecuación (2)
  y la NOTA que la sigue.
- **El impreso:** «$L_{p\mathrm{A}I}$ is the A-weighted sound pressure level
  in decibels at the $i^\mathrm{th}$ measurement position», con una $I$
  mayúscula, y en la NOTA «When the range of values of $L_{p\mathrm{A}I}$
  does not exceed 5 dB, a simple arithmetic average may be used.»
- **El problema:** la Ecuación (2) y la frase que la presenta escriben
  $L_{p\mathrm{A}i}$, con la $i$ minúscula de la suma
  $\sum_{i=1}^{N} 10^{0{,}1 L_{p\mathrm{A}i}}$, y la propia línea de la
  lista habla de la posición $i^\mathrm{th}$; $L_{p\mathrm{A}I}$ no nombra
  ninguna magnitud de la norma.
- **Evidencia:** la Ecuación (2), su lista de definiciones y la NOTA en la
  página 29 del PDF (p. 27 impresa) de la IEC 61063:1991, la primera edición
  bilingüe de 1991-04, cuyo texto francés de la página 28 del PDF (p. 26
  impresa) imprime el mismo $L_{p\mathrm{A}I}$ en la lista y en la NOTA; y en
  la página 15 del PDF (p. 9 impresa) de BS EN 61063:1996, el texto inglés de
  EN 61063:1996, que reproduce sin modificaciones esa misma IEC 61063:1991,
  allí numerada IEC 1063:1991.
- **Comportamiento de la biblioteca:** `turbine_sound_power` promedia los
  niveles corregidos de cada posición, $L_{p\mathrm{A}i}$, por la
  Ecuación (2), y `arithmetic_mean_allowed` lee la NOTA sobre el rango de
  esos mismos niveles
  ([`turbine_noise.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/turbine_noise.py)). No
  hizo falta ningún cambio.
- **Estado:** sin notificar.

## ISO 3095:2013, Tabla G.1 (la incertidumbre típica de la distancia del micrófono de 25 m impresa como 0,004 dB)

- **Ubicación:** anexo G (informativo), Tabla G.1, la fila
  $\delta_\mathrm{distance}$, página impresa 49.
- **Lo impreso:** "for a microphone distance of 25 m: ±0,07 dB" en la columna
  del intervalo de incertidumbre y "for a microphone distance of 25 m:
  0,004 dB" en la de la incertidumbre típica; la línea de 7,5 m de la misma
  fila imprime ±0,23 dB y 0,13 dB.
- **El problema:** el G.3 deduce cada incertidumbre típica de la tabla a
  partir de su intervalo como $u(x_i) = a/\sqrt{3}$ (Fórmula G.2), y así lo
  hacen todas las demás filas: ±0,25 dB da 0,14 dB, ±0,44 dB da 0,25 dB, y la
  línea de 7,5 m de esta fila da $0{,}23/\sqrt{3} = 0{,}13$ dB, como está
  impreso. Para ±0,07 dB la fórmula da $0{,}07/\sqrt{3} = 0{,}040$ dB. El
  0,004 dB impreso es diez veces menor, un cero de más tras la coma decimal;
  la celda debería decir 0,04 dB.
- **Evidencia:** la Tabla G.1 leída en la página 55 del PDF (p. 49 impresa) y
  la Fórmula G.2 en la página 54 del PDF (p. 48 impresa) de la ISO 3095:2013
  (tercera edición, 2013-08-01).
- **Comportamiento de la biblioteca:** la biblioteca no publica la Tabla G.1;
  [`pass_by_uncertainty`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/rolling_stock_noise.py)
  recibe cada entrada como un valor y su incertidumbre típica, y
  `metrology.rectangular(0.0, 0.07)` da los 0,040 dB de la Fórmula G.2. La
  comprobación de conformidad "ISO 3095:2013 Table G.1" fija las dieciocho
  filas rectangulares cuya impresión reproduce la Fórmula G.2 y deja fuera
  esta celda. No hizo falta ningún cambio.
- **Estado:** no reportada.

## ISO 3095:2013, Tabla G.1 frente a la Tabla G.2 (la incertidumbre del nivel del terreno a 7,5 m impresa como 0,55 dB en una y 0,30 dB en la otra)

- **Ubicación:** anexo G (informativo), la fila
  $\delta_\mathrm{ground\ level,7,5}$ de la Tabla G.1, página impresa 49, y la
  fila $\delta_\mathrm{ground\ level}$ de la Tabla G.2, página impresa 51.
- **Lo impreso:** la Tabla G.1 da el intervalo "[0 dB; 1,03 dB]" y la
  incertidumbre típica "0,55 dB" con "$\Delta L_p$ = 0,515 dB" para un
  micrófono a 7,5 m. La Tabla G.2, el ejemplo del G.6 para una medición en
  parado cuyo terreno "over a distance of 7,5 m varies between 0 and 2 m
  below to the top of the rail", usa la misma corrección de 0,515 dB con una
  incertidumbre típica de 0,30 dB.
- **El problema:** la nota a de la Tabla G.1 trata un intervalo asimétrico
  $[a; b]$ como uno simétrico en torno a su media, que es de donde sale la
  corrección $(0 + 1{,}03)/2 = 0{,}515$ dB, y la Fórmula G.2 da entonces la
  semianchura entre $\sqrt{3}$: $0{,}515/\sqrt{3} = 0{,}297$ dB, los 0,30 dB de
  la Tabla G.2. La línea de 25 m de la misma magnitud sigue esa aritmética,
  $0{,}165/\sqrt{3} = 0{,}10$ dB como está impreso. Los 0,55 dB de la Tabla G.1
  no son ni la semianchura ni la anchura entera entre $\sqrt{3}$ (0,59 dB); la
  celda debería decir 0,30 dB. Las dos tablas difieren también en la
  distancia a 7,5 m, donde la Tabla G.1 imprime 0,13 dB y la Tabla G.2 lleva
  0,06 dB sin decir de dónde sale ese valor; los 0,83 dB combinados de la
  Tabla G.2 necesitan sus 0,06 dB (0,13 dB daría 0,84 dB), así que esa
  diferencia se registra aquí y no se corrige.
- **Evidencia:** la Tabla G.1 leída en la página 55 del PDF (p. 49 impresa),
  la Fórmula G.2 y la nota a en la página 54 del PDF (p. 48 impresa), y la
  Tabla G.2 en las páginas 56 y 57 del PDF (pp. 50 y 51 impresas) de la
  ISO 3095:2013 (tercera edición, 2013-08-01).
- **Comportamiento de la biblioteca:** las comprobaciones de conformidad
  "ISO 3095:2013 Table G.2" pasan a
  [`pass_by_uncertainty`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/rolling_stock_noise.py)
  las trece filas de la Tabla G.2 tal como están impresas, con los 0,30 dB y
  los 0,06 dB, y reproducen sus 55,68 dB, 0,83 dB y 1,66 dB. No hizo falta
  ningún cambio.
- **Estado:** no reportada.

## ISO 3095:2013, Tabla G.1 (el intervalo de la pantalla antiviento impreso con los extremos al revés)

- **Ubicación:** anexo G (informativo), Tabla G.1, la fila
  $\delta_\mathrm{slm,\ wind\ screen}$, página impresa 49.
- **Lo impreso:** "Damping of the wind screen", intervalo "[0,12 dB; 0 dB]",
  incertidumbre típica "0,03 dB" y "$\Delta L_p$ = 0,06 dB".
- **El problema:** la nota a escribe un intervalo asimétrico como $[a; b]$, y
  las otras cuatro filas que usan uno ponen primero el extremo inferior:
  "[−0,21 dB; 0 dB]" para el factor de distorsión del calibrador,
  "[−1,5 dB; 1 dB]" para los impulsos, y "[0 dB; 1,03 dB]" y "[0 dB; 0,33 dB]"
  para el nivel del terreno a 7,5 m y a 25 m. Tal como está impreso, el
  intervalo de la pantalla antiviento tiene el extremo inferior por encima
  del superior, y está vacío. Debería decir o bien [−0,12 dB; 0 dB], un
  intervalo que rebaja la lectura escrito como escribe el suyo la fila de la
  distorsión, cuya corrección del valor medio, según la nota a, "increases
  the average sound level", o bien [0 dB; 0,12 dB], escrito como escriben los
  suyos las filas del nivel del terreno. Las dos lecturas dan los 0,03 dB y
  los 0,06 dB impresos, así que la tabla no dice cuál se quiso escribir.
- **Evidencia:** la Tabla G.1 y su nota a leídas en la página 55 del PDF
  (p. 49 impresa) y en la página 54 del PDF (p. 48 impresa) de la
  ISO 3095:2013 (tercera edición, 2013-08-01).
- **Comportamiento de la biblioteca:** la biblioteca no lee ningún intervalo
  de la Tabla G.1; la comprobación de conformidad "ISO 3095:2013 Table G.1"
  usa la semianchura de 0,06 dB y las de la Tabla G.2 la corrección y la
  incertidumbre tal como están impresas. No hizo falta ningún cambio.
- **Estado:** no reportada.

## EN 15610:2009, anexo B, B.9.2 (un bucle de eliminación de picos que no pide el cambio de signo y no termina en un cambio brusco de pendiente)

- **Ubicación:** anexo B (informativo), B.9.2, la sección de eliminación de
  picos del listado de RoughProcess.m, páginas impresas 23 y 24; apartado 7.2,
  páginas impresas 12 y 13.
- **Lo impreso:** el listado repite su pasada con
  `while min(d2rdx2) <-10^7`, y dentro de ella solo trata una muestra como
  pico `if (y < -10^7) && (d1 ~= d2)`, la segunda derivada y un cambio de
  signo de la primera, y solo interpola sobre ella `if height > w^2/3`. El
  apartado 7.2 c) identifica un pico "by the criteria
  $\mathrm{d}^2r/\mathrm{d}x^2 < -10^7\ \mathrm{\mu m/m^2}$ and a change of
  sign for $\mathrm{d}r/\mathrm{d}x$", lo elimina cuando $h > w^2/a$ con
  $a = 3$ m, y termina: "The spike removal procedure shall be repeated until
  no further spike is detected."
- **El problema:** la condición del bucle deja fuera el cambio de signo que
  el 7.2 c) y la propia pasada dentro del bucle piden a un pico. Donde el
  registro cambia bruscamente de pendiente sin un máximo ni un mínimo, su
  segunda derivada baja de $-10^7\ \mathrm{\mu m/m^2}$ sin que haya ahí un
  pico según el 7.2 c), ninguna pasada cambia el registro y el bucle no
  termina. Un carril que sube 20 µm por milímetro y luego 5 µm por milímetro,
  muestreado cada milímetro, tiene un cambio así:
  $\mathrm{d}^2r/\mathrm{d}x^2 = -1{,}5 \times 10^7\ \mathrm{\mu m/m^2}$ en el
  cambio, y $\mathrm{d}r/\mathrm{d}x$ es positiva a los dos lados. Ahí es
  donde el listado se aparta del apartado que ilustra. Con un pico que el
  7.2 c) sí detecta y que la prueba de altura conserva como rugosidad que la
  rueda nota, el listado no hace nada peor que el apartado leído al pie de la
  letra: una cresta de 200 µm de alto, muestreada cada milímetro, cuyos bordes
  sitúa la regla de pendiente del listado a 42 mm uno de otro, tiene
  $\mathrm{d}^2r/\mathrm{d}x^2 = -2 \times 10^7\ \mathrm{\mu m/m^2}$ en la cima
  y $h = 2 \times 10^{-4}$ m por debajo de $w^2/3 = 5{,}9 \times 10^{-4}$ m; se
  detecta en cada pasada y se conserva, así que ni el listado ni "until no
  further spike is detected" se detienen nunca con ella.
- **Evidencia:** el listado leído en las páginas 25 y 26 del PDF (pp. 23 y 24
  impresas), y el apartado 7.2 en las páginas 14 y 15 del PDF (pp. 12 y 13
  impresas) de la BS EN 15610:2009, la implementación británica de la
  EN 15610:2009 (aprobada por el CEN el 16 de abril de 2009). La falta de
  terminación es una ejecución del bucle del listado, transcrito línea a
  línea, sobre el cambio de pendiente y la cresta de arriba.
- **Comportamiento de la biblioteca:**
  [`remove_roughness_spikes`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/acoustic_roughness.py)
  detecta un pico por los dos criterios del 7.2 c) y repite su pasada hasta
  que una pasada no elimina nada, que es como lee "until no further spike is
  detected" para un pico que se detecta y se conserva. Devuelve sin cambios el
  cambio de pendiente y la cresta de arriba;
  `test_a_bend_without_an_extremum_is_no_spike` y
  `test_a_broad_ridge_is_kept_and_the_sweep_ends` en
  [`tests/environment/sources/test_acoustic_roughness.py`](https://github.com/jmrplens/phonometry/blob/main/tests/environment/sources/test_acoustic_roughness.py)
  lo fijan en los dos.
- **Estado:** no reportada.

## EN 15610:2009, anexo B, B.9.2 (filtros del método B pasados hacia delante y hacia atrás, fuera de todas las clases de la EN 61260)

- **Ubicación:** anexo B (informativo), B.9.2, la sección de filtrado digital
  del listado de RoughProcess.m, página impresa 25, descrita en el B.6, página
  impresa 20; apartado 7.4.3, página impresa 15, y apartado 2, página impresa
  5.
- **Lo impreso:** el listado fija los bordes de banda `fsmin=fsc/(2^(1/6))` y
  `fsmax=fsc*(2^(1/6))` alrededor de los centros `fsc=1./wl_d`, diseña cada
  banda con `order=3;` y `[b,a]=butter(order,Wn);`, filtra con
  `rf=filtfilt(b,a,rraw);` y da `specdf(q)=std(rf);` del registro que queda
  tras cortar 2 m de cada extremo. El apartado 7.4.3 dice: "The digital
  filters shall comply with EN 61260", y el apartado 2 fecha esa referencia
  como EN 61260 (IEC 61260:1995).
- **El problema:** `butter(3,Wn)` diseña un filtro paso banda que cae 3 dB en
  `fsmin` y `fsmax`, y `filtfilt` lo pasa hacia delante y luego hacia atrás,
  así que el filtro por el que pasa de verdad el registro tiene el cuadrado de
  su respuesta en módulo: 6,02 dB de caída en sus propios bordes de banda.
  Tomando el `fsc` del listado como frecuencia central exacta y la razón de
  base dos con la que están construidos sus bordes, la tabla 1 de la
  EN 61260:1995 admite justo dentro de un borde de banda una atenuación
  relativa de como mucho 4,5 dB, 5,0 dB y 5,5 dB para las clases 0, 1 y 2, y
  el 4.5.3 limita la respuesta integrada del filtro
  $\Delta B = 10 \lg (B_\mathrm{e}/B_\mathrm{r})$, con $B_\mathrm{e}$ de la
  ecuación (14) y $B_\mathrm{r} = G^{1/(2b)} - G^{-1/(2b)}$ de la ecuación (9),
  a $\pm 0{,}15$ dB, $\pm 0{,}3$ dB y $\pm 0{,}5$ dB. La respuesta al
  cuadrado da $\Delta B = -0{,}59$ dB en todas las bandas de `wl_d` de 0,5 m a
  4 mm con un muestreo de 1 mm, y $-0{,}58$ dB en las bandas de 3,15 mm y
  2,5 mm, donde el muestreo deforma la respuesta. Los
  filtros del listado no cumplen por tanto ninguna clase de la EN 61260 en
  ninguna banda, en ninguno de los dos requisitos, que es lo que el 7.4.3 les
  pide, y una banda de espectro plano se lee unos 0,6 dB por debajo. El mismo
  filtro pasado una sola vez hacia delante caería 3,01 dB en los bordes, con
  $\Delta B$ de $+0{,}15$ dB a $+0{,}20$ dB, dentro de la clase 1. Un comentario de la misma
  sección, "used later for fsc(q)<50 ie lambda >0.02", no concuerda con la
  prueba que hace el código, `if fsc(q)>=20` y `elseif fsc(q)<20`, que manda
  al registro diezmado las bandas de más de 0,05 m.
- **Evidencia:** el listado leído en la página 27 del PDF (p. 25 impresa), el
  B.6 en la página 22 del PDF (p. 20 impresa), el apartado 7.4.3 en la página
  17 del PDF (p. 15 impresa) y el apartado 2 en la página 7 del PDF (p. 5
  impresa) de la BS EN 15610:2009, la implementación británica de la
  EN 15610:2009; la tabla 1 en la página 14 del PDF (p. 10 impresa), la
  ecuación (9) en la página 10 del PDF (p. 6 impresa), las ecuaciones (13) y
  (14) en la página 15 del PDF (p. 11 impresa) y el 4.5.3 en la página 16 del
  PDF (p. 12 impresa) de la BS EN 61260:1996, que es la IEC 61260:1995. Las
  atenuaciones y $\Delta B$ son un recálculo: los filtros del listado
  diseñados con `scipy.signal.butter`, el mismo diseño que la función de
  MATLAB, con un muestreo de 1 mm (y sobre el registro diezmado por 10 para
  `fsc<20`), su respuesta elevada al cuadrado, leída en los bordes de banda e
  integrada con la ecuación (14).
- **Comportamiento de la biblioteca:**
  [`filtered_roughness_spectrum`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/acoustic_roughness.py)
  pasa cada banda una sola vez hacia delante por las secciones de Butterworth
  de orden 4 de
  [`roughness_filter_bank`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/sources/acoustic_roughness.py),
  a la frecuencia de muestreo del propio registro, un banco de clase 0 de la
  EN 61260:1995 en la tabla 1 hasta el número de onda de Nyquist del registro,
  en el 4.5.3 y en el 4.9;
  `test_the_bank_is_class_0_on_table_1_of_en_61260_1995`,
  `test_the_bank_attenuates_class_0_beyond_g4_on_a_record`,
  `test_the_integrated_response_of_every_band_is_within_class_0` y
  `test_the_summation_of_outputs_is_within_class_0` en
  [`tests/environment/sources/test_roughness_method_b.py`](https://github.com/jmrplens/phonometry/blob/main/tests/environment/sources/test_roughness_method_b.py)
  lo fijan, y las comprobaciones de conformidad "EN 15610:2009 7.4.3 and
  EN 61260:1995 Table 1" y "EN 15610:2009 7.4.3 and EN 61260:1995 4.8 and
  Table 1" lo evalúan banda a banda y con tonos que pasan por él.
- **Estado:** no reportada.

## IEC 60268-7:2010, 8.7.3.3, fórmula (3) ($U_{470}$ por el producto a 460 Hz)

- **Ubicación:** 8.7.3.3 c), fórmula (3), p. 28 impresa.
- **El impreso:** «$L_\mathrm{d3} = 20 \log \{(U_{470} + U_{740})/U_{600}\}$», un
  párrafo después del punto b), que dice «the third-order components are at
  460 Hz and 740 Hz».
- **El problema:** la señal de ensayo de 8.7.3.2 es el par de 70 Hz y 600 Hz,
  así que los productos de modulación de tercer orden están en
  $600 \pm 2 \times 70$ Hz, 460 Hz y 740 Hz, como dice el punto b). Ningún
  producto de los dos tonos cae en 470 Hz: el subíndice de la primera tensión
  debería ser 460.
- **Evidencia:** el punto b) y la fórmula (3) en la página 30 del PDF (p. 28
  impresa) de IEC 60268-7:2010, edición 3.0.
- **Comportamiento de la biblioteca:**
  [`headphone_modulation_signal`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  genera el par de 70 Hz y 600 Hz, y `modulation_distortion` lee los productos
  de tercer orden en 460 Hz y 740 Hz; la fila de conformidad de 8.7.3.3 b)
  fija las cuatro frecuencias de los productos.
- **Estado:** sin notificar.

## IEC 60268-7:2010, 8.7.4.2 c), fórmula (5) (un paréntesis que se cierra sin haberse abierto)

- **Ubicación:** 8.7.4.2 c), fórmula (5), p. 29 impresa.
- **El impreso:** «$L_\mathrm{dd3} = 20 \log \{U_{2f2-f1} + U_{2f1-f2})/2\,U_{f2}\}$».
- **El problema:** se abre una llave antes de $U_{2f2-f1}$ y se cierra un
  paréntesis después de $U_{2f1-f2}$ que nunca se abrió, de modo que el
  impreso deja sin decir si $2U_{f2}$ divide a los dos productos o solo al
  segundo. La característica a la que remite 8.7.4.1 es la de IEC
  60268-3:2013, 14.12.8.1 b): «the ratio of the arithmetic sum of the output
  voltages at frequencies $2f_2 - f_1$ and $2f_1 - f_2$ to the reference
  voltage $U_{2,\mathrm{ref}}$ which is equal to twice the output voltage
  $U_{2,f2}$», es decir,
  $20\lg\{(U_{2f_2-f_1} + U_{2f_1-f_2})/2U_{f_2}\}$.
- **Evidencia:** la fórmula (5) en la página 31 del PDF (p. 29 impresa) de
  IEC 60268-7:2010, edición 3.0, leída frente a 14.12.8.1 b) en la página 38
  del PDF (p. 36 impresa) de IEC 60268-3:2013.
- **Comportamiento de la biblioteca:**
  [`difference_frequency_distortion`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/intermodulation.py)
  divide la suma aritmética de los dos productos de tercer orden por la suma
  de las amplitudes de los dos tonos, que es $2U_{f_2}$ para los tonos iguales
  de
  [`headphone_difference_frequency_signal`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py).
  No hizo falta ningún cambio.
- **Estado:** sin notificar.

## IEC 60268-7:2010, 8.7.4.2 a) (la señal de ensayo remitida a 8.7.3.1)

- **Ubicación:** 8.7.4.2 a), p. 28 impresa.
- **El impreso:** «The headphone is brought under standard measuring
  conditions, and then the input signal is changed to that required for the
  measurement (see 8.7.3.1).»
- **El problema:** 8.7.3.1 es el apartado general de la distorsión de
  modulación, una sola frase que remite a IEC 60268-2. La señal que necesita
  la medida de la distorsión por diferencia de frecuencias, dos sinusoides
  separadas 80 Hz que dan cada una la mitad de la tensión de entrada asignada,
  está en 8.7.4.1, unas líneas por encima del punto.
- **Evidencia:** 8.7.3.1, 8.7.4.1 y 8.7.4.2 a) en la página 30 del PDF
  (p. 28 impresa) de IEC 60268-7:2010, edición 3.0.
- **Comportamiento de la biblioteca:** no hace falta ninguno.
  [`headphone_difference_frequency_signal`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  genera la señal de 8.7.4.1.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 60268-7:2010, figura 3, NOTA (el simulador de cabeza y torso citado como IEC 60969)

- **Ubicación:** la NOTA bajo la figura 3, «Illustrated measurement diagram
  by simulated programme signal», p. 16 impresa.
- **El impreso:** «Power summation of the 1/3-octave-analized data
  multiplied by filtering coefficients given by IEC 61672-1 and/or IEC 60969
  gives the corrected voltage.»
- **El problema:** los coeficientes de filtrado a los que se refiere la NOTA
  son los de los dos filtros que 7.4 enumera sobre la figura, la ponderación A
  de IEC 61672-1 y el «free field compensating filter, that is the filter with
  inverse response of the free field response of the manikin specified in IEC
  60959». La propia figura rotula el maniquí «HATS (IEC 60959)», y el
  capítulo 2 incluye IEC TR 60959 entre las referencias normativas; no incluye
  ninguna IEC 60969. Las cifras están transpuestas.
- **Evidencia:** 7.4 y la figura 3 en las páginas 17 y 18 del PDF (pp. 15 y
  16 impresas), y el capítulo 2 en la página 9 del PDF (p. 7 impresa), de IEC
  60268-7:2010, edición 3.0.
- **Comportamiento de la biblioteca:** no hace falta ninguno.
  [`programme_signal_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  recibe la respuesta en campo libre del simulador de cabeza y torso como dato
  y la compensa.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 60268-7:2010, 8.6.3 a 8.6.5 (referencias cruzadas que no llegan a su apartado)

- **Ubicación:** 8.6.3.2 a) y b), 8.6.3.3, 8.6.4.2 a) y b), 8.6.4.3,
  8.6.5.2 a) y b) y 8.6.5.3, pp. 24 a 27 impresas.
- **El impreso:** las medidas por comparación en campo libre y en campo
  difuso llevan el auricular a las condiciones de comparación «(see 7.4 and
  Annex C)» y «(see 7.4 and Annex D)», y cubren «at least the rated frequency
  range (see 8.6.5)»; 8.6.3.3 usa un auricular «measured as described in
  8.6.2.2» y 8.6.4.3 uno «measured as described in 8.6.3.2», con sus
  resultados «calculated as described in 8.6.3.2»; 8.6.5.2 a) remite a
  «8.6.2.2 or 8.6.3.2 and Annex E» para las condiciones, b) a 8.6.5 para el
  rango de frecuencias asignado y lee el micrófono de sonda «through a 1/3
  octave filter with appropriate centre frequency (see 7.5 and Annex B)»;
  8.6.5.3 es «the same as given in 8.6.4.2, except that the sound field is
  replaced by a headphone, previously calibrated by the method of 8.6.4.2,
  using at least 16 test persons».
- **El problema:** 7.4 son las condiciones de medida con la señal de programa
  simulado; las condiciones de comparación en campo libre y en campo difuso son
  7.5.2 y 7.5.3, y las condiciones de medida en el conducto auditivo, con «A
  very small microphone, in accordance with the requirements in Annex B», son
  7.6, no 7.5, que son las condiciones de comparación de sonoridad. El rango de
  frecuencias asignado es 8.6.6, que 8.6.2.2 b) cita bien. La medida directa de
  la que tiene que salir una referencia de sustitución, y cuyo cálculo sigue,
  es 8.6.3.2 en campo libre y 8.6.4.2 en campo difuso; las condiciones que
  toma prestadas 8.6.5.2 a) son las de esos mismos dos métodos, 8.6.3.2 y
  8.6.4.2; y el método directo en el conducto auditivo que repite 8.6.5.3 es
  8.6.5.2. Cada referencia se queda un apartado antes del que describe su
  texto. El segundo 8.6.4.2 de 8.6.5.3 sigue la misma pauta: el auricular que
  sustituye al campo sonoro de una medida en el conducto auditivo tiene que
  calibrarse por el método del conducto auditivo, 8.6.5.2, porque 8.6.4.2 es
  una comparación de sonoridad frente al campo difuso solo y no puede calibrar
  la respuesta en el conducto auditivo en campo libre que 8.6.5.1 a) también
  abarca.
- **Evidencia:** las referencias leídas frente a los apartados que nombran, en
  las páginas 26 a 29 del PDF (pp. 24 a 27 impresas), con 7.4 a 7.6 en las
  páginas 17 a 19 del PDF (pp. 15 a 17 impresas), de IEC 60268-7:2010,
  edición 3.0.
- **Comportamiento de la biblioteca:**
  [`field_comparison_response`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  y `ear_canal_frequency_response` siguen el texto de cada método; el panel de
  16 sujetos de una referencia de sustitución es el de 8.6.3.3 y 8.6.4.3
  (`FieldComparisonResponse.qualifies_as_reference`), y el de 8.6.5.3 se lee
  como un panel del método directo en el conducto auditivo
  (`EarCanalFrequencyResponse.qualifies_as_reference`). La fila de conformidad
  «IEC 60268-7:2010 8.6.5.3 with 8.6.5.2 h)» fija los 8 y los 16 sujetos.
- **Estado:** sin notificar (defecto de referencia cruzada).

## IEC 60268-7:2010, tabla 1 (seis números de apartado que nombran otro apartado)

- **Ubicación:** tabla 1, «Classification of characteristics», p. 32 impresa.
- **El impreso:** las filas «8.3.4 Rated characteristics of protective
  devices», «8.5.1 Rated maximum or working sound pressure level», «8.6.5
  Rated frequency range», «8.7.1 Rated harmonic distortion», «8.7.2 Rated
  modulation distortion» y «8.7.3 Rated difference-frequency distortion».
- **El problema:** en esta edición los dispositivos de protección son 8.3.6
  (8.3.4 es la tensión característica con señal de programa simulado), los
  niveles de presión acústica máximo y de trabajo se especifican en 8.5.2
  (8.5.1 es el apartado general), el rango de frecuencias asignado es 8.6.6, y
  las distorsiones armónica, de modulación y por diferencia de frecuencias son
  8.7.2, 8.7.3 y 8.7.4 (8.7.1 es el apartado general).
- **Evidencia:** la tabla 1 en la página 34 del PDF (p. 32 impresa) leída
  frente al índice de las páginas 4 y 5 del PDF (pp. 2 y 3 impresas) de IEC
  60268-7:2010, edición 3.0.
- **Comportamiento de la biblioteca:** no hace falta ninguno; la biblioteca no
  lee la tabla 1.
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 60268-7:2010, 8.3.4.2 NOTA 1 (un factor de cresta atribuido a IEC 60268-1)

- **Ubicación:** 8.3.4.2, NOTA 1, p. 20 impresa.
- **El impreso:** «IEC 60268-1 specifies the spectrum, filtering circuit and
  crest factor of the simulated programme signal.»
- **El problema:** IEC 60268-1:1985, que el capítulo 2 cita sin fecha,
  especifica el espectro (tabla II, figura 1) y el circuito de filtrado
  (figura 2) y ningún factor de cresta: el capítulo 7 define la señal como
  «stationary weighted Gaussian noise without amplitude limiting». Ninguna de
  las dos modificaciones de 1988 añade uno; la modificación 1 sustituye la
  tabla AII y la modificación 2 sustituye 12.1. El único factor de cresta que
  imprimen las dos partes es la «peak-to-r.m.s ratio between 1,8 and 2,2» del
  propio 8.3.2.2 b) de IEC 60268-7, para la señal recortada de las tensiones
  límite.
- **Evidencia:** la NOTA 1 en la página 22 del PDF (p. 20 impresa) y 8.3.2.2
  b) en la página 21 del PDF (p. 19 impresa) de IEC 60268-7:2010, edición 3.0;
  el capítulo 7 en la página 15 del PDF (p. 13 impresa), la tabla II en la
  página 23 del PDF (p. 21 impresa) y las figuras 1 y 2 en la página 24 del
  PDF (p. 22 impresa) de IEC 60268-1:1985.
- **Comportamiento de la biblioteca:** no hace falta ninguno.
  [`simulated_programme_signal`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/programme_signal.py)
  no recorta por defecto, como pide el capítulo 7, y solo recorta a una
  relación pico/eficaz cuando se le da `peak_to_rms`, que la biblioteca
  atribuye a 8.3.2.2 b).
- **Estado:** sin notificar (defecto de referencia cruzada, sin consecuencia
  numérica).

## IEC 60268-7:2010, 8.5.2 b) y 8.5.3 c) (dos formas de fijar la f.e.m. de 1 mW)

- **Ubicación:** 8.5.2 b), p. 22 impresa; 8.5.3 c) y d), p. 23 impresa.
- **El impreso:** 8.5.2 b) define el nivel de presión acústica de trabajo con
  «a sinusoidal voltage at 500 Hz, in series with the rated source impedance,
  of such value that 1 mW would be dissipated in a pure resistance equal to
  the rated impedance of the headphone, connected in place of it». El método,
  8.5.3 c): «The source e.m.f. is then adjusted so that the voltage across the
  input connector of the headphone is such that it would cause 1 mW to be
  dissipated in a pure resistance equal to the rated impedance of the
  headphone», y d) da el nivel «as the result b) in 8.5.2».
- **El problema:** las dos fijan f.e.m. distintas. Con una impedancia asignada
  $R$, una impedancia de fuente asignada $R_\mathrm{s}$ y 1 mW, la definición
  pide $E = \sqrt{PR}\,(R + R_\mathrm{s})/R$, la f.e.m. que entrega 1 mW a
  $R$ puesta en lugar del auricular; el método pide la f.e.m. que deja
  $\sqrt{PR}$ en bornes del propio auricular, cuya impedancia $Z$ a 500 Hz se
  lleva su parte, $E = \sqrt{PR}\,|Z + R_\mathrm{s}|/|Z|$. Solo coinciden
  cuando $Z$ es la impedancia asignada o $R_\mathrm{s}$ es cero. Un auricular
  de 32 Ω que a 500 Hz presenta 40 Ω, sobre la fuente de 120 Ω de IEC 61938,
  da por el método $20\lg\{(152/32)/(160/40)\} = 1{,}49$ dB menos que por la
  definición, y la impedancia asignada de 8.2.1 b) deja que el módulo quede en
  cualquier valor por encima del 80 % de $R$.
- **Evidencia:** 8.5.2 b) en la página 24 del PDF (p. 22 impresa) y 8.5.3 c)
  y d) en la página 25 del PDF (p. 23 impresa) de IEC 60268-7:2010, edición
  3.0.
- **Comportamiento de la biblioteca:**
  [`working_sound_pressure_level`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  sigue por defecto la definición de 8.5.2 b) a d), y el método de 8.5.3 c)
  cuando recibe la impedancia medida del auricular a 500 Hz como
  `headphone_impedance_ohm`; la fila de conformidad «IEC 60268-7:2010 8.5.2 b)
  and 8.5.3 c)» fija los 1,49 dB.
- **Estado:** sin notificar.

## Propiedades de las fuentes, relacionadas, que no son erratas

Registradas aquí para prevenir futuros «arreglos» que romperían la
concordancia con las fuentes publicadas:

- **Norton & Karczub 2e (2003), apéndice 4 A, las densidades del
  poliestireno, el poliuretano y el PVC:** el apéndice imprime $42$, $72$ y
  $66$ kg/m$^3$, donde Mechel y Bies imprimen $1070$, $900$ y $1400$ para los
  mismos nombres. La diferencia no es un dígito perdido. Cada fila de Norton &
  Karczub imprime también un módulo de Young y una velocidad en medio infinito,
  y los tres cumplen $E = \rho c^2$ con un uno por ciento de margen, lo que
  describe la forma expandida o celular del polímero; los otros libros
  describen la maciza. Ninguna de las dos páginas matiza el nombre. Verificado
  en la página 625 del PDF (p. impresa 605). Se registra aquí, y en `ACCEPTED`
  de `scripts/check_solid_agreement.py`, para que las densidades bajas no se
  «corrijan» a las del polímero macizo.
- **Norton & Karczub 2e (2003), apéndice 4 C, hidrógeno y oxígeno a 0 y
  20 °C:** cada gas se imprime con la misma densidad a las dos temperaturas,
  $0.084$ y $1.43$ kg/m$^3$, mientras su velocidad cambia como debe y el aire,
  en la misma tabla, baja de $1.293$ a $1.21$ en el mismo intervalo. No se
  registra como errata porque las propias columnas de la tabla no lo resuelven:
  $P = \rho c^2/\gamma$ sitúa estas filas entre $96$ y $109$ kPa, no más lejos
  de una atmósfera que las del dióxido de carbono y el vapor. Verificado en la
  página 626 del PDF (p. impresa 606). Los cuatro estados lo dicen en su
  `validity` en [`PUBLISHED_FLUIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/catalogue.py),
  y la página de catálogos publicados lo muestra sobre su densidad.
- **ISO 11546-1:1995, anexos A y B:** la figura B.1 se titula «Source
  spectrum for an artificial sound source constructed according to the
  guidelines given in annex A», mientras que el anexo A, que pide una chapa de
  acero de 4 mm por 800 mm (aprox.) por 300 mm (aprox.), añade en su propio
  último párrafo que «the length of the steel plate used for this measurement
  was 600 mm» y que una fuente construida según el anexo puede dar otro
  espectro. La figura es por tanto la ilustración de una fuente una cuarta
  parte más corta que la longitud aproximada que prescribe el anexo, y el
  anexo lo dice. Verificado en la página 17 del PDF (p. impresa 10) y la
  página 19 del PDF (p. impresa 12) de la ISO 11546-1:1995 tal como se publica
  en la BS EN ISO 11546-1:2009. No se registra como errata porque la propia
  norma declara la diferencia; se registra aquí para que
  [`ARTIFICIAL_SOURCE_EXAMPLE_LWA_DB`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  no se lea como una propiedad de una fuente del anexo A.

- **ISO 7235:2003, Ecuaciones (10), (21) y (22):** la ley de los gases
  ideales viene impresa con
  $R = 287\ \text{N}\cdot\text{m}/(\text{kg}\cdot\text{K})$ y la
  temperatura absoluta escrita como $\theta + 273\ ^\circ\text{C}$. Ninguno
  de los dos es el valor exacto (287,05 y 273,15). El desfase por sí solo deja
  una densidad un 0,051 % alta a 20 °C y la constante de los gases le añade
  otro 0,017 %, para un 0,069 % en total. Es una simplificación y no un
  defecto: la densidad que producen sólo se usa en la presión dinámica de las
  Ecuaciones (16), (19) y (20), y ambas series del coeficiente de pérdida de
  presión llevan el mismo factor, de modo que las Ecuaciones (17) y (18) salen
  **escaladas** por él en vez de desplazadas, un 0,069 % bajas, que queda muy
  por debajo de la incertidumbre de un ensayo de pérdida de presión y es lo que
  muestra un resultado calculado según la norma. La
  biblioteca conserva las dos constantes impresas, como
  [`ISO7235_GAS_CONSTANT`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_measurement.py)
  y `ISO7235_ABSOLUTE_ZERO_OFFSET`, para que un resultado se pueda reproducir
  tal como lo da la norma, y la fila de conformidad «Normal air density
  (Eqs. (10), (21), (22))» deja constancia del tamaño de la diferencia.

- **ISO 12354-1:2017 Tabla L.8 / ISO 12354-2:2017 Tabla G.8, primera fila:**
  la fila etiquetada «Int. wall 1/2 – Ext. wall 1/2» imprime
  $m'_i = 219{,}0\ \text{kg/m}^2$ y $m'_{\perp i}$ (Parte 2:
  $m'_\text{orthogonal}$) $= 360{,}0\ \text{kg/m}^2$, que es la asignación de
  una trayectoria *que sale de la pared exterior*, la dirección opuesta a la
  que da la propia etiqueta de la fila. Leída en la dirección de la fila, el
  elemento que lleva la trayectoria es la pared interior, así que $m'_i$
  debería ser 360,0 y la masa perpendicular 219,0. Es un desliz de etiquetado
  y nada más: la rama es la rama de **esquina** de la T rígida
  $K_{12} = 5{,}7 + 5{,}7 M^2$, donde solo entra $M^2$, así que ambas
  asignaciones devuelven los mismos 5,965 → 6,0 dB. La segunda fila de cada
  tabla, «Ext. wall 1/2 – Ext. wall 1/2», es la rama pasante
  $5{,}7 + 14{,}1 M + 5{,}7 M^2$, donde el signo de $M$ sí importa, y está
  etiquetada y poblada de forma consistente ($M = \log_{10}(360/219)$ da
  9,006 → los 9,0 impresos). Verificado en la página 89 del PDF (p. 83
  impresa) de ISO 12354-1:2017 y la página 46 del PDF (p. 40 impresa) de
  ISO 12354-2:2017. No se registra como errata porque ningún número depende
  de ello; se registra aquí para que un lector futuro no «corrija» el
  convenio por trayectoria de la biblioteca para casar con la fila impresa.
- **Término de agua pura de Francois-Garrison:** las dos cúbicas de $A_3$
  publicadas no se encuentran exactamente en el cambio de 20 °C (un escalón
  de $1 \cdot 10^{-7} f^2\ \text{dB/km}$, 0.1 dB/km a 1 MHz). Inherente a los
  coeficientes publicados.
- **Simplificación de Ainslie-McColm:** la afirmación del artículo de estar
  «within 10 % of Francois-Garrison» se excede marginalmente en las esquinas
  extremas de su dominio declarado (10.4 % a −6 °C / 1 MHz; 12.3 % a 7 km de
  profundidad). Una propiedad del ajuste publicado; ambas transcripciones
  verificadas dígito a dígito.
- **CNOSSOS-EU Anexo II 2.3, número de ecuación que falta:** la sección
  ferroviaria numera sus fórmulas (2.3.1), (2.3.2), (2.3.4), (2.3.5)..., sin
  ninguna (2.3.3) en todo el Anexo II. Verificado en la página 17 del PDF
  (p. L 168/17 impresa) de la Directiva (UE) 2015/996:2015, donde (2.3.2) y
  (2.3.4) están una encima de la otra. No falta nada del método; solo salta
  la numeración.
- **Corrección de errores de CNOSSOS-EU de 2018, códigos de columna de la
  Tabla G-3:** se reporta que la corrección de errores encabeza las siete
  columnas de $L_{r,TR}$ «B/S B/M B/H B/S B/M B/H B/H», donde las tres
  primeras deberían leer «M/S M/M M/H» y la última «W», y la Directiva
  Delegada (UE) 2021/1226 de la Comisión, punto (20)(c) del Anexo, sí
  sustituye ese encabezado por los códigos corregidos más una columna D
  nueva. Se deja sin registrar porque la propia corrección de errores se
  publica solo como HTML en EUR-Lex, así que no pudo obtenerse aquí ninguna
  página impresa suya, y este registro no recoge una afirmación sobre un
  símbolo impreso que no se haya leído de la página. El impreso de 2015 de la
  misma tabla, que sí se leyó, lleva encabezados descriptivos («Mono-block
  sleeper on soft rail pad» y demás) y ningún defecto.
- **Long, Architectural Acoustics 2e, capítulo 17, nivel en la mesa
  adyacente:** el ejemplo del restaurante declara que «at an adjacent table
  3 m (10 ft) away, the direct field level from our conversation is about
  54 dB», donde su propia Ec. (17.50) con los $Q = 2$ y
  $L_W = 70\ \text{dB}$ que producen sus 60 dB a 1.2 m da 52.5 dB. Se deja
  sin registrar porque la lectura pretendida no puede establecerse desde el
  libro: 54 dB es también lo que la misma ecuación da a 2.5 m (54.1 dB, y
  2.5 m es la separación de mesas que el párrafo siguiente deriva), y lo que
  daría una sola duplicación de distancia de 6 dB desde los 60 dB
  redondeados, mientras que el «3 m (10 ft)» impreso es autoconsistente en
  ambas unidades y se repite en el párrafo anterior. `speech_direct_level`
  evalúa la Ec. (17.50) tal como está impresa, así que devuelve 52.5 dB allí;
  no «corregirla» hacia 54 dB.
- **Constante EPNL del Anexo 16 de la OACI:** la constante redondeada 13 del
  Anexo para registros uniformes de 0.5 s difiere de la forma exacta
  $-10\log_{10}(T_0)$ en 0.0103 dB; la biblioteca usa la forma exacta, que la
  referencia integrada del ETM reproduce a cinco decimales.
- **Filas de elementos de la Tabla 14.9 de Long:** la hoja resuelta de ruido
  por conductos del capítulo 14 la produjo un programa comercial, como
  declara el texto que la introduce, y varias de sus filas de elementos no se
  siguen de las tablas impresas a su lado: la fila del ventilador
  (90/86/82/79/77/75/71/61 dB) no es lo que da la Ec. 13.1 con las constantes
  de curvatura hacia delante de la Tabla 13.5 en ese punto de trabajo
  (99/99/89/84/82/77/72/67 dB, y tampoco un desplazamiento de nivel de ello),
  y la fila del conducto flexible (14/14/16/15/17/22/16/13 dB) no es la
  entrada de la Tabla 14.4 para 12 in por 6 ft (3/5/10/15/17/16/9 dB). La
  biblioteca implementa las ecuaciones y tablas impresas, y usa la hoja solo
  para lo que fija de verdad, la aritmética de la cascada; sus filas de
  elementos se introducen tal como están publicadas en
  [`tests/noise_control/test_duct_path.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_duct_path.py).
  El propio redondeo de la hoja tampoco es siempre autoconsistente (la fila 3
  de impulsión imprime un *Sum* de 49 dB a 500 Hz donde $76 - 28 = 48$, y
  después un *Combined* consistente con 48), que es por lo que la comparación
  corre al 1 dB que la hoja impresa lleva.
- **ISO 3747:2010 Tabla E.1, las etiquetas de grado de precisión:** la tabla
  informativa de ejemplos de $\sigma_\mathrm{tot}$ etiqueta sus tres filas
  «0,5 (accuracy grade 1)», «1,5 (accuracy grade 2)» y «3 (accuracy
  grade 3)», mientras que la Tabla 2, normativa, de esta parte da
  $\sigma_{R0}$ = 4,0 dB para el grado 3 de control y el campo de aplicación
  de ISO 3747 cubre solo los grados 2 y 3. Es la ilustración compartida de la
  familia ISO 3740, no una afirmación sobre este método: ISO 3744:2010 imprime
  en su Tabla H.1 la tabla idéntica, con las mismas filas, etiquetas y celdas
  de $\sigma_\mathrm{tot}$, e ISO 3744 cubre solo el grado 2. Verificado en la
  página 42 del PDF (p. 33 impresa) y en la página 27 del PDF (p. 18 impresa)
  de BS EN ISO 3747:2010. La biblioteca lee $\sigma_{R0}$ de la Tabla 2
  normativa (1,5 dB y 4,0 dB, comprobación de conformidad «ISO 3747:2010
  Table 2 / Eq. 22») y usa la Tabla E.1 solo por su fila
  $\sigma_\mathrm{tot}$ = 1,6 / 2,5 / 4,3 frente a $\sigma_{R0}$ = 1,5 dB,
  donde ambas tablas coinciden. No «corregir» la fila de 3 dB a 4,0 dB:
  pertenece a la ilustración de la familia, no a la Tabla 2 de esta parte.
- **ISO 3747:2010 Anexo C, $\theta_\mathrm{ref}$ = 296 K:** el anexo imprime
  la temperatura de referencia de la corrección de impedancia de radiación
  como 296 K junto a una condición de referencia de 23,0 °C, que son
  296,15 K, así que exactamente en las condiciones de referencia
  $C_2 = 15 \lg(296{,}15/296) = +0{,}003\,3$ dB y no cero. El apartado 9.1.4
  de ISO 3741:2010 e ISO 3744:2010 imprimen el mismo $\theta_1$ = 296 K, así
  que es el redondeo de la familia y no una errata de una parte; la
  biblioteca conserva los 296 K en el `C2` compartido de
  [`sound_power_reverberation.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_reverberation.py)
  y fija el residuo (comprobación de conformidad «ISO 3747:2010 Annex C»).
  No «corregirlo» a 296,15 K.
- **ISO 3747:2010 Ec. (14), el margen de ruido de fondo del suceso aislado:**
  $\Delta L_{Ei} = L'_{Ei,q(\mathrm{ST})} - L_{pi(\mathrm{B})}$ resta un nivel
  de ruido de fondo promediado en el tiempo de un nivel de suceso aislado
  integrado en el tiempo, pidiendo solo que ambos se midan con el mismo
  tiempo de integración $T$. La diferencia es un margen verdadero para
  $T$ = 1 s; para un $T$ mayor el ruido de fondo contiene $10 \lg(T/T_0)$ dB
  más energía sobre el intervalo del suceso (apartado 3.4, NOTA 1). La
  Ec. (25) de ISO 3741:2010 y el apartado 8.3.4 de ISO 3744:2010 imprimen la
  misma línea, verificado en la página 23 del PDF (p. 14 impresa) de BS EN
  ISO 3747:2010 y en las páginas correspondientes de las dos normas hermanas,
  así que es la convención de la familia y no se registra contra una parte.
  La biblioteca aplica la Ec. (14) tal como está impresa por defecto y ofrece
  `integration_time` en
  [`sound_energy_in_situ`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_situ.py)
  para llevar antes el ruido de fondo al intervalo del suceso.

- **ISO 5136:2003, apartado 5.3.4.3, el signo de la Ecuación (8):** el
  apartado dice que las correcciones del cono aerodinámico y la bola de
  espuma «are estimated to be negative and of small magnitude», y a
  continuación imprime $C_{3,4} = 10 \lg[1/(1 - U/c)^2]$ dB, que es positiva
  siempre que $U > 0$: a los 20 m/s que se permiten al cono aerodinámico, con
  $c$ = 340 m/s, $+0{,}53$ dB en el lado de impulsión y $-0{,}50$ dB en el de
  aspiración. El signo de la ecuación es el que da la onda plana convectada:
  el flujo de energía de una onda que viaja con el flujo es $(1 + M)^2$ veces
  $p^2/\rho c$, de modo que para una presión dada la potencia es mayor aguas
  abajo y menor aguas arriba. No se registra como errata porque la frase con
  la que se cierra ese mismo párrafo reconcilia las dos: «With this
  simplification, the sound power level obtained by using the nose cone or
  foam ball is expected to be higher than the true sound power level.» La
  corrección negativa es la modal, que no está disponible y se descarta; la
  Ecuación (8) es la parte convectiva que se conserva, y la norma dice en la
  misma frase que lo que queda sesga el $L_W$ hacia arriba. Leído en la
  página 29 del PDF (p. 19 impresa) de ISO 5136:2003. Se registra aquí para
  que nadie «corrija» el signo de la Ecuación (8), que
  [`flow_modal_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/sound_power_in_duct.py)
  implementa tal como está impresa y que fija
  `test_eq8_omnidirectional_shields` en
  [`tests/emission/test_sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_duct.py).

- **Tabla 1 de la ISO 11820:1996 y tabla 3 de la ISO 10847:1997, dos
  correcciones de fondo que no coinciden:** las dos tablas toman el margen
  entre el nivel con la fuente y el nivel sin ella y responden con una
  corrección en decibelios, y responden distinto. La ISO 11820 rechaza por
  debajo de 3 dB y luego quita 3, 2, 2, 1, 1, 1, 0,5 y 0,5 dB hasta un margen
  de 10 dB; la ISO 10847 rechaza por debajo de 4 dB y luego quita 2, 2, 1, 1,
  1 y 1 dB hasta ese mismo margen. Con un margen de 9 dB la primera quita
  0,5 dB y la segunda 1 dB. También difieren los signos, porque la columna de
  la ISO 11820 dice "corrections to be subtracted from sound pressure level
  measured with sound source operating" e imprime sus valores en positivo,
  mientras que la de la ISO 10847 dice "correction to be made to the measured
  sound pressure level" y los imprime en negativo. Ninguna de las dos es una
  errata: son dos tabulaciones, de dos comités, de la misma resta física,
  redondeadas de distinta manera y escritas desde extremos opuestos. Leídas en
  la página 13 del PDF (página impresa 5) de la EN ISO 11820:1996 y en la
  página 11 del PDF (página impresa 7) de la ISO 10847:1997. La biblioteca las
  mantiene separadas como
  [`silencer_background_correction_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_in_situ.py)
  y
  [`barrier_background_correction_db`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py),
  cada una con su convenio de signo y su propio rechazo, y una comprobación de
  conformidad las enfrenta en el margen en el que se separan. No hay que
  fundirlas en un único auxiliar.
- **Beranek & Mellow 2e, tabla 7.1, columna de Delany y Bazley:** la tabla
  imprime $a_1$ a $a_4$ = 0.0511, 0.0768, 0.0858, 0.175 donde
  [`DELANY_BAZLEY_COEFFICIENTS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/porous.py)
  tiene $C_1$, $C_3$, $C_5$, $C_7$ = 0.0571, 0.087, 0.0978, 0.189, de la tabla
  D.1 de Bies 5e. Las cuatro amplitudes se separan entre un 8 % y un 14 % y las
  razones no son constantes (1.117, 1.133, 1.140, 1.080), así que ningún factor
  de escala único las relaciona. El motivo es la variable. La ecuación (7.11)
  de Beranek, impresa sobre la tabla en esa misma página, está escrita en
  $R_f/f$ con exponentes **positivos**, mientras que Delany y Bazley, y Bies
  tras ellos, escriben $X = \rho_0 f / R_f$ con exponentes negativos. Las dos
  formas se diferencian exactamente en $\rho_0^{\,b}$, y despejar
  $C = a\,\rho_0^{\,b}$ fila a fila da $\rho_0$ = 1.16, 1.19, 1.21,
  1.14 kg/m³, que es la densidad del aire en todas ellas; hacer la conversión
  en sentido contrario con $\rho_0$ = 1.18 kg/m³ reproduce las cuatro
  amplitudes impresas con un 1,4 %, un 0,4 %, un 1,5 % y un 2,1 % de
  diferencia. Los exponentes lo corroboran por su cuenta: Beranek imprime
  $b_1$ a $b_4$ = 0.75, 0.73, 0.70, 0.59 frente a $C_2$, $C_4$, $C_6$, $C_8$ =
  0.754, 0.732, 0.700, 0.595, los mismos números con dos decimales. El control
  es la otra columna de la tabla: la variable de Miki es $f/\sigma$ y no lleva
  densidad, y la columna de Miki de Beranek, 0.070, 0.107, 0.109, 0.160 con
  0.632, 0.632, 0.618, 0.618, coincide dígito a dígito con las constantes con
  las que está escrita `miki`. Verificado en la página 352 del PDF (página
  impresa 349) de Beranek & Mellow, *Acoustics: Sound Fields, Transducers and
  Vibration* 2e (2019), y en la página 757 del PDF (página impresa 728) de
  Bies, Hansen & Howard, *Engineering Noise Control* 5e (2017). Ninguno de los
  dos libros se equivoca: imprimen una misma regresión en dos variables. La
  biblioteca sigue a Delany y Bazley a través de Bies, en
  $X = \rho_0 f/\sigma$, de modo que sus amplitudes **no** deben «corregirse»
  hacia las de Beranek, lo que aplicaría la densidad del aire por segunda vez.

- **IEC 60268-7:2010, «the standard reference frequency» junto a la frecuencia
  de medida normalizada de 500 Hz:** 7.2 b) fija «the standard measuring
  frequency» en 500 Hz, y la NOTA de 8.3.3.1 da el motivo para el acoplador,
  «to avoid the effects of diaphragm resonance, leakage and standing waves».
  La parte nombra además «the standard reference frequency» (8.3.6.2 b),
  8.6.3.1, 8.6.4.1, 8.7.2.1, 8.9.1 a)) y nunca la define; IEC 60268-1:1985,
  que cita el capítulo 2, sí lo hace, en el capítulo 3: «If a measurement
  relates to a reference frequency, then, in the absence of a clear reason to
  the contrary, this shall be the standard reference frequency of
  1 000 Hz». Los métodos por comparación empiezan y terminan su secuencia de
  ensayo en «the band centred on 1 kHz» (8.6.3.2 c), 8.6.4.2 c)), mientras que
  la fórmula (1) del método en el conducto auditivo imprime su propia banda de
  referencia, 500 Hz. Los dos términos no siempre se mantienen separados:
  8.7.2.1 especifica la distorsión armónica «at the standard reference
  frequency» y 8.7.2.2 b) aplica la tensión «at the standard measuring
  frequency». No se registra como errata porque cada apartado puede leerse tal
  como está impreso. Leído en la página 11 del PDF (p. 9 impresa) de IEC
  60268-1:1985 y en las páginas 17, 21, 23, 26 a 29 y 31 del PDF (pp. 15, 19,
  21, 24 a 27 y 29 impresas) de IEC 60268-7:2010. La biblioteca refiere por
  defecto las respuestas por comparación de
  [`field_comparison_response`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  a 1 000 Hz, y la respuesta en el conducto auditivo y la respuesta relativa
  del acoplador a 500 Hz; la fila de conformidad «IEC 60268-7:2010 8.6.3.1
  with IEC 60268-1:1985 Clause 3» fija el valor por defecto. No hay que pasar
  las respuestas por comparación a 500 Hz para uniformarlas.

<!-- END GENERATED BODY -->

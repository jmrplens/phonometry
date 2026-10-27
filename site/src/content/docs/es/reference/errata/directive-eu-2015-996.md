---
title: "Erratas de la Directiva (UE) 2015/996"
description: "Erratas de la Directiva (UE) 2015/996: 6 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 6 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre la Directiva (UE) 2015/996, en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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
  (`ROAD_OCTAVE_BANDS_HZ`), fijada por
  `test_octave_bands_are_the_corrected_range` y por los casos del libro de
  cálculo, cuyos niveles publicados cubren las ocho bandas.
- **Estado:** corregido por el organismo emisor (corrección de errores del 10
  de enero de 2018); registrado porque el texto de 2015 sin corregir sigue
  siendo el que más se descarga y se cita.

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

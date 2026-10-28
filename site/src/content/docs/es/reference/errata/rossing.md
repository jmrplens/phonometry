---
title: "Erratas de Rossing (2014)"
description: "Erratas de Rossing (2014): 6 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 6 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Rossing (2014), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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

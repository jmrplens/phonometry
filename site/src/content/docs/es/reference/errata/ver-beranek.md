---
title: "Erratas de Ver & Beranek (2006)"
description: "Erratas de Ver & Beranek (2006): 4 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 4 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Ver & Beranek (2006), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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
  [`PUBLISHED_RESISTIVE_SHEETS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py).
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
  [`PUBLISHED_RESISTIVE_SHEETS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/resistive_sheets.py)
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

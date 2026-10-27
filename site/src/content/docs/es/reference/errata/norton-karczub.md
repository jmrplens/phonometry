---
title: "Erratas de Norton & Karczub (2003)"
description: "Erratas de Norton & Karczub (2003): 5 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 5 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Norton & Karczub (2003), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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
  [`_junction_transmission.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/vibration/structural/_junction_transmission.py)
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
  and 3.5 m × 3 m», es decir, $10.5\ \text{m}^2$.
- **El problema:** esa área es inconsistente con las tres respuestas
  impresas. La Ec. (6.12) fija
  $E_1/E_2 = (\eta_2 + \eta_{21})/\eta_{12} = 6.554$ desde los factores de
  pérdida impresos solos, mientras que la geometría enunciada con las
  velocidades impresas (27.2 y 13.2 mm/s) da 7.88. La razón de energías es
  independiente de las densidades modales y de la velocidad de onda, así que
  ninguna elección de esas puede reconciliarla; solo el área de la plataforma
  puede. El área que las respuestas implican es $8.73\ \text{m}^2$, que es
  $3.5 \times 3$ menos la huella $\pi(0.75\ \text{m})^2$ del cilindro que la
  Fig. P6.10 muestra atravesando la plataforma.
- **Evidencia:** con $8.73\ \text{m}^2$ la inversión de las Ecs. (6.15), (6.8) y (6.10)
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
  de «~$1.5 \times 10^{-2}$»; la respuesta da 27 dB a 8 kHz y 38.6 dB a 16 kHz.
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

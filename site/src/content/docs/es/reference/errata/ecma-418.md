---
title: "Erratas de ECMA-418"
description: "Erratas de ECMA-418: 8 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 8 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre ECMA-418-1:2024 y ECMA-418-2:2025, en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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
  [`_roughness_ecma.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/psychoacoustics/quality/_roughness_ecma.py).
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

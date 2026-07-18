---
title: "Análisis de señal"
description: "El núcleo de medición de phonometry: bancos de filtros de octava fraccional, ponderación frecuencial y temporal, niveles integrados y estadísticos, calibración física e incertidumbre de medida, y cómo esas piezas se encadenan en un sonómetro en código."
---

Todo en phonometry empieza aquí. Esta sección cubre la cadena que convierte
una señal digital en bruto en números acústicos conformes con las normas:
dividirla en **bandas de octava fraccional** (ANSI S1.11 / IEC 61260-1),
moldearla con las **ponderaciones frecuenciales** de IEC 61672-1, suavizarla
con las **balísticas temporales Fast/Slow/Impulse** e integrarla en **Leq y
niveles estadísticos**. Es, en la práctica, un sonómetro descompuesto en
funciones componibles, y todas las demás secciones de la documentación se
apoyan en él: un modelo de sonoridad consume niveles de banda calibrados, un
parámetro de sala parte de una respuesta al impulso filtrada, una valoración
ambiental es un Leq ajustado.

Dos preocupaciones transversales completan el núcleo. La **calibración**
decide qué significan físicamente las muestras digitales: los resultados
pueden referirse a un tono de calibrador medido o a una sensibilidad conocida
(dB SPL), o quedarse en escala digital completa (dBFS). Y la **incertidumbre
de medida** (la GUM y su suplemento de Monte Carlo) cualifica cualquier
resultado calculado a partir de entradas inciertas, que es lo que hace
defendible un número en un informe.

Si acabas de llegar a la biblioteca, lee primero
[Bancos de filtros](/phonometry/es/guides/filter-banks/): presenta la
descomposición en bandas que el resto de páginas da por supuesta. Después,
[Niveles integrados y estadísticos](/phonometry/es/guides/levels/) muestra las
métricas en las que terminan la mayoría de las mediciones, y
[Calibración y dBFS](/phonometry/es/guides/calibration/) las ancla a unidades
físicas.

## [Filtrado en octavas](/phonometry/es/guides/sections/octave-filtering/)

La descomposición en bandas de octava fraccional y las dos maneras de
escalarla: bloques en streaming y arrays multicanal.

- [Bancos de filtros](/phonometry/es/guides/filter-banks/): las cinco
  arquitecturas de filtro, sus respuestas en frecuencia, la descomposición en
  bandas y el filtrado de fase cero fuera de línea.
- [Procesado por bloques](/phonometry/es/guides/block-processing/): análisis
  en streaming con estado, que arrastra el estado de los filtros entre
  búferes, para señales que no caben en memoria.
- [Multicanal y rendimiento](/phonometry/es/guides/multichannel/): análisis
  vectorizado de muchos canales a la vez, con notas de rendimiento.

## [Niveles y ponderación](/phonometry/es/guides/sections/levels-weighting/)

De la señal ponderada al nivel reportado: las ponderaciones frecuenciales,
las balísticas temporales y los niveles integrados, estadísticos y de
valoración.

- [Ponderación frecuencial (A, C, G, Z)](/phonometry/es/guides/weighting/):
  las curvas de respuesta del oído de IEC 61672-1 y la ponderación G para
  infrasonido de ISO 7196.
- [Ponderación temporal](/phonometry/es/guides/time-weighting/): las
  balísticas exponenciales Fast, Slow e Impulse según IEC 61672-1.
- [Niveles integrados y estadísticos](/phonometry/es/guides/levels/): Leq y
  LAeq, niveles percentiles L10/L50/L90, LCpeak y SEL, dosis de ruido
  (IEC 61252), Lden y niveles de valoración (ISO 1996-1), y espectrogramas de
  octava.

## [Calibración e incertidumbre](/phonometry/es/guides/sections/calibration-uncertainty/)

Qué significan los números y cuánto fiarse de ellos.

- [Calibración y dBFS](/phonometry/es/guides/calibration/): calibración SPL
  física a partir de un tono de calibrador (IEC 60942) o de una sensibilidad
  conocida, y el modo digital dBFS.
- [Incertidumbre de medida (GUM y Monte Carlo)](/phonometry/es/guides/gum-uncertainty/):
  la ley de propagación de la incertidumbre y el método de Monte Carlo de
  ISO/IEC Guide 98-3, con incertidumbre expandida e intervalos de cobertura.
- [Análisis espectral calibrado](/phonometry/es/guides/spectral-analysis/):
  los estimadores de Welch de Bendat y Piersol con su calidad estadística:
  PSD y densidad espectral cruzada con intervalos de confianza chi-cuadrado,
  el espectro de salida coherente con la SNR espectral, suavizado en 1/n de
  octava y generadores de ruido de colores con pendiente exacta.
- [Correlación, retardo y envolvente](/phonometry/es/guides/correlation-delay/):
  estimaciones de correlación con los errores aleatorios de Bendat y
  Piersol, estimación del retardo por correlación directa, pendiente de fase
  del espectro cruzado y las ponderaciones GCC de Knapp y Carter, retardo
  submuestral y alineación de respuestas al impulso, y la envolvente de
  Hilbert.

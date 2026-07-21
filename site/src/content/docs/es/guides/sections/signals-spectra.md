---
title: "Señales y espectros"
description: "Análisis de señal en frecuencia y en tiempo en phonometry: estimaciones espectrales de Welch calibradas con su calidad estadística, y correlación, estimación de retardo y la envolvente de Hilbert."
---

Los niveles de banda responden a *cuánto*; esta sección responde a *qué hay
en la señal*. Donde el resto del núcleo trabaja en bandas de octava
fraccional, estas páginas trabajan con los estimadores de grano fino del
análisis de señal clásico: densidades espectrales, funciones de correlación,
retardos y envolventes. Comparten una misma disciplina, tomada de Bendat y
Piersol: cada estimación está **calibrada** (los mismos marcos de referencia
dB SPL / dBFS que el resto de la biblioteca) y lleva consigo su **calidad
estadística**, de modo que un espectro no es solo una curva, sino una curva
con su intervalo de confianza.

[Análisis espectral calibrado](/phonometry/es/guides/spectral-analysis/) es
la mitad del dominio de la frecuencia. Los estimadores de Welch de densidad
espectral de potencia y cruzada reportan su número efectivo de promedios, sus
errores aleatorios normalizados y sus intervalos de confianza chi-cuadrado;
el espectro de salida coherente separa una salida medida en la parte
explicada por una entrada y la parte que es ruido, con una relación
señal-ruido espectral; el suavizado en fracciones de octava tiende el puente
de vuelta al mundo de bandas; y los generadores de ruido de colores
sintetizan señales de prueba blancas, rosas, rojas, azules y violetas con
pendiente exacta en ley de potencias.

[Análisis tiempo-frecuencia](/phonometry/es/guides/time-frequency/) es la
vista intermedia: el espectrograma STFT calibrado muestra qué ocurre
*cuándo* - una sirena que pasa, un impacto, un arranque - con cada celda
leyendo un nivel absoluto en el mismo escalado que los estimadores de
Welch, y la FFT con zoom calcula el espectro de una banda estrecha en una
malla arbitrariamente fina para separar tonos más próximos que un bin
práctico de FFT.

[Correlación, retardo y envolvente](/phonometry/es/guides/correlation-delay/)
es la mitad del dominio del tiempo. La autocorrelación y la correlación
cruzada vienen con las normalizaciones y los errores aleatorios de Bendat y
Piersol; la estimación del retardo ofrece el correlador directo, la pendiente
de fase del espectro cruzado y las ponderaciones de la correlación cruzada
generalizada de Knapp y Carter (Roth, SCOT, PHAT, máxima verosimilitud); las
respuestas al impulso pueden retardarse y alinearse con precisión
submuestral; y la transformada de Hilbert produce la envolvente con fase y
frecuencia instantáneas.

Estos estimadores alimentan al resto de la biblioteca: las funciones de
transferencia y el análisis de distorsión se apoyan en la maquinaria
espectral cruzada, el trabajo con respuestas al impulso de sala descansa en
la estimación de retardo y la alineación, y las
[páginas de incertidumbre](/phonometry/es/guides/sections/calibration-uncertainty/)
aportan el vocabulario de análisis de error en el que se expresan las
estimaciones.

## Páginas de esta sección

- [Análisis espectral calibrado](/phonometry/es/guides/spectral-analysis/):
  PSD/CSD de Welch con intervalos de confianza chi-cuadrado, el espectro de
  salida coherente y la SNR espectral, suavizado en 1/n de octava y
  generadores de ruido de colores con pendiente exacta.
- [Análisis tiempo-frecuencia](/phonometry/es/guides/time-frequency/): el
  espectrograma STFT calibrado en unidades absolutas (dB SPL para pascales)
  con el compromiso de resolución tiempo-frecuencia, y la FFT con zoom que
  resuelve tonos más próximos que un bin práctico de FFT.
- [Correlación, retardo y envolvente](/phonometry/es/guides/correlation-delay/):
  estimaciones de correlación con sus errores aleatorios, estimación del
  retardo por correlación directa, pendiente de fase y ponderaciones GCC,
  alineación submuestral de respuestas al impulso, y la envolvente de
  Hilbert.

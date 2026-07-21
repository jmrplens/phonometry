---
title: "Señales y espectros"
description: "Análisis de señal en frecuencia y en tiempo en phonometry: estimaciones espectrales de Welch calibradas con su calidad estadística, análisis cepstral con detección de ecos y liftering, el espectro de la envolvente, y correlación, estimación de retardo y la envolvente de Hilbert."
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
[Cepstro, ecos y espectro de la envolvente](/phonometry/es/guides/cepstrum-echoes/)
trabaja sobre la *forma* del espectro. El cepstro de potencia, real y
complejo colapsa el rizado espectral periódico en picos de quefrencia, la
detección de ecos lee el retardo y el coeficiente de una reflexión en el
pico cepstral, el liftering separa un espectro logarítmico en envolvente
suave y estructura fina, y el espectro de la envolvente convierte las
modulaciones de amplitud en líneas discretas en la frecuencia de modulación.

[Correlación, retardo y envolvente](/phonometry/es/guides/correlation-delay/)
es la mitad del dominio del tiempo. La autocorrelación y la correlación
cruzada vienen con las normalizaciones y los errores aleatorios de Bendat y
Piersol; la estimación del retardo ofrece el correlador directo, la pendiente
de fase del espectro cruzado y las ponderaciones de la correlación cruzada
generalizada de Knapp y Carter (Roth, SCOT, PHAT, máxima verosimilitud); las
respuestas al impulso pueden retardarse y alinearse con precisión
submuestral; y la transformada de Hilbert produce la envolvente con fase y
frecuencia instantáneas.

[Señales de prueba y herramientas de muestreo](/phonometry/es/guides/test-signals/)
es la caja de herramientas en la que se apoyan las otras dos: salvas de tono
con la conmutación exacta de IEC 60268-1 (inicio en el paso por cero, número
entero de períodos completos, trenes repetitivos), remuestreo polifásico
tras una especificación antialias explícita cuyo filtro diseñado viaja con
el resultado, y retardo fraccionario de banda limitada con frontera lineal o
circular, que comparte su núcleo con la alineación submuestral de respuestas
al impulso.

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
  salida coherente y la SNR espectral, suavizado en 1/n de octava,
  generadores de ruido de colores con pendiente exacta y las figuras de
  mérito de Harris para las ventanas.
- [Cepstro, ecos y espectro de la envolvente](/phonometry/es/guides/cepstrum-echoes/):
  el cepstro de potencia/real/complejo con análisis de quefrencia, detección
  de ecos con el coeficiente de reflexión leído en el pico, liftering paso
  bajo/paso alto, la ida y vuelta homomórfica y el espectro de la envolvente
  de las modulaciones de amplitud.
- [Correlación, retardo y envolvente](/phonometry/es/guides/correlation-delay/):
  estimaciones de correlación con sus errores aleatorios, estimación del
  retardo por correlación directa, pendiente de fase y ponderaciones GCC,
  alineación submuestral de respuestas al impulso, y la envolvente de
  Hilbert.
- [Señales de prueba y herramientas de muestreo](/phonometry/es/guides/test-signals/):
  salvas de tono IEC 60268-1 con conmutación exacta, remuestreo con
  especificación antialias declarada y retardo fraccionario de banda
  limitada.

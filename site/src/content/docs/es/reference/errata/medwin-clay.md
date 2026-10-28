---
title: "Erratas de Medwin & Clay (1998)"
description: "Erratas de Medwin & Clay (1998): 2 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 2 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Medwin & Clay (1998), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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

---
title: "Erratas de Maa (1998)"
description: "Erratas de Maa (1998): 1 defecto del texto impreso, con la evidencia y lo que hace phonometry al respecto."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Esta es la entrada del [registro de erratas](/phonometry/es/reference/errata/) sobre Maa (1998). La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

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

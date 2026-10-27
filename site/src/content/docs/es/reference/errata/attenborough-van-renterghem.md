---
title: "Erratas de Attenborough & Van Renterghem (2021)"
description: "Erratas de Attenborough & Van Renterghem (2021): 2 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 2 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Attenborough & Van Renterghem (2021), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Tabla 5.1

- **Ubicación:** Tabla 5.1, «Coefficient and exponent values in the Delany
  and Bazley, Miki and modified Miki models», fila «Miki [6,7]», coeficiente
  $r$.
- **El impreso:** $r = 0.0109$.
- **El problema:** la fuente original (Miki 1990, J. Acoust. Soc. Jpn (E)
  11(1), Ec. (34)) imprime
  $\beta(f) = (\omega/c_0)[1 + 0.109 \cdot (f/\sigma)^{-0.618}]$; la tabla
  pierde un dígito. Con 0.0109 la parte real del número de onda de Miki a
  $f/\sigma = 0.01$ es $1.19$ en lugar de $2.88$, inconsistente con la fila
  de Delany-Bazley de la misma tabla ($3.10$ desde sus propios $r = 0.0862$,
  $s = -0.693$) y con la fila del «modified Miki» que el propio libro deriva
  de ella.
- **Evidencia:** comprobación dígito a dígito contra el artículo original de
  Miki (1990) (Ecs. (30)–(34)) y cálculo cruzado de ambas variantes en el
  borde del rango de ajuste. Verificado en la página 168 del PDF (p. 149
  impresa) de Attenborough & Van Renterghem, Predicting Outdoor Sound
  2e:2021, y en la página 4 del PDF (p. 22 impresa) de Miki, J. Acoust. Soc.
  Jpn (E) 11(1):1990.
- **Comportamiento de la biblioteca:** implementa el 0.109 original de Miki;
  el punto de digitalización $f/\sigma = 0.1$ está fijado en
  ``tests/reference_data/`` y en la comprobación de conformidad «Miki 1990
  Eqs. (30)-(34)».
- **Estado:** sin notificar (libro, no una norma).

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Ec. (5.13)

- **Ubicación:** Ec. (5.13), la densidad compleja volumétrica de
  Johnson-Champoux-Allard, con
  $G(\Lambda) = \sqrt{1 - 4iT\eta\rho_0\omega/(R_S^2\Lambda^2\Omega^2)}$.
- **El impreso:** la tortuosidad $T$ aparece a la primera potencia dentro de
  $G(\Lambda)$.
- **El problema:** Johnson et al. (1987) y la formulación JCA estándar (Cox &
  D'Antonio 3e Ec. (6.19); Allard & Atalla) llevan ahí
  $T^2 = \alpha_\infty^2$. El impreso a la primera potencia rompe la asíntota
  de alta frecuencia que define la longitud característica viscosa: con $T^2$
  la densidad tiende a $(T\rho_0/\Omega)(1 + (1 - j)\delta_v/\Lambda)$ con
  $\delta_v = \sqrt{2\eta/\rho_0\omega}$, mientras que la forma impresa
  tiende a una corrección $\delta_v/(\Lambda\sqrt{T})$, que para $T = 2$
  supone un error del $29\,\%$ en el término de capa límite para la misma
  $\Lambda$.
- **Evidencia:** desarrollo asintótico de ambas variantes contra la
  definición de $\Lambda$ de Johnson et al. y contra la Ec. (6.19) de Cox &
  D'Antonio; el test JCA de alta frecuencia de la biblioteca fija el
  comportamiento con $T^2$. Verificado en la página 173 del PDF (p. 154
  impresa) de Predicting Outdoor Sound 2e:2021.
- **Comportamiento de la biblioteca:** implementa la forma estándar con $T^2$
  (Cox & D'Antonio Ec. (6.19)); la asíntota está fijada en
  ``test_high_frequency_density_asymptote``.
- **Estado:** sin notificar (libro, no una norma).

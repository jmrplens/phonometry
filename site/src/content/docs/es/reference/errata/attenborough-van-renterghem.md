---
title: "Erratas de Attenborough & Van Renterghem (2021)"
description: "Erratas de Attenborough & Van Renterghem (2021): 3 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
corrects:
  - "doi-10-1201-9780429470806"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 3 entradas del [registro de erratas](/es/reference/errata/) sobre Attenborough & Van Renterghem (2021), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Attenborough & Van Renterghem, Predicting Outdoor Sound 2e (2021), Ec. (4.35)

- **Ubicación:** apartado 4.2.4.1 «Impedance Plane Approach», Ec. (4.35)
  (p. 133 impresa), la actualización de la velocidad de partícula en un
  contorno de impedancia real y constante.
- **El impreso:**
  $$
  v^{l+0.5}_{x(i+0.5,j,k)} = \left[1 + \frac{dt\,c_0 Z_0}{dx}\right]^{-1}
  \left[v^{l-0.5}_{x(i+0.5,j,k)}\left(1 - \frac{dt\,c_0 Z_0}{dx}\right)
  - \frac{2\,dt}{\rho_0\,dx}\,p^{l}_{(i+1,j,k)}\right]
  $$
- **El problema:** la ecuación no se sigue de las dos de las que se
  construye. La Ec. (4.33) y la figura 4.4 están escritas para un contorno
  derecho, «assuming a right boundary»: la celda dentro de la malla es $i$,
  la pared está en $i+0.5$, y «$i+0.5$ is used instead of $i+1$ (that would
  obviously fall outside the grid)». La Ec. (4.33) toma la diferencia entre
  la presión de la pared y $p^{l}_{(i,j,k)}$, y la Ec. (4.34) iguala la
  presión de la pared a la impedancia por la media de las dos velocidades.
  Llevando (4.34), con la impedancia $Z_0 \rho_0 c_0$, a (4.33) y despejando
  la velocidad nueva se obtienen el corchete y el factor impresos con el
  último término $+\,(2\,dt/(\rho_0\,dx))\,p^{l}_{(i,j,k)}$: la presión de la
  celda de dentro de la malla, con signo más. El término impreso, un signo
  menos sobre la presión de la celda $i+1$, es la actualización de un
  contorno izquierdo, cuya celda interior es $i+1$ y cuya normal exterior
  apunta al otro lado.
- **Evidencia:** la deducción anterior, a partir de las ecuaciones y la
  figura leídas en sus páginas: las Ecs. (4.32) y (4.33) con la frase que las
  precede en la página 151 del PDF (p. 132 impresa), y la figura 4.4 con las
  Ecs. (4.34) y (4.35) en la página 152 del PDF (p. 133 impresa) de
  Predicting Outdoor Sound 2e:2021.
- **Comportamiento de la biblioteca:** ningún número depende de la errata.
  El motor FDTD actualiza cada lado del dominio con el signo de su propia
  normal exterior (`_ImpedanceEdge.update` en
  [`fdtd.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/simulation/fdtd.py): los lados derecho e
  inferior suman la presión de la celda interior, los lados izquierdo y
  superior la restan), que es la Ec. (4.35) deducida arriba a la derecha y la
  forma impresa a la izquierda;
  ``tests/simulation/test_fdtd_oblique_impedance.py`` sujeta la reflexión de
  uno de esos lados a la de un plano de reacción local.
- **Estado:** sin notificar (libro, no una norma).

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

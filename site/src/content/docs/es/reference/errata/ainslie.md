---
title: "Erratas de Ainslie (2010)"
description: "Erratas de Ainslie (2010): 2 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 2 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Ainslie (2010), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Ainslie (2010), la Ec. (4.6) frente a su propio folio 177, y el exponente de la Ec. (4.13)

- **Ubicación:** *Principles of Sonar Performance Modelling* (Springer 2010),
  Ec. (4.6) en el folio impreso 127; la densidad del agua de mar citada en el
  apartado 4.4 del folio impreso 177; Ec. (4.13) del folio impreso 135.
- **Lo impreso:** la Ec. (4.6) da la densidad del agua de mar como
  $\hat\rho = 1027 + 4{,}3\times10^{-7}\hat P_\mathrm{w} + 0{,}75[S-35] -
  0{,}16[\hat T-10] - 0{,}004[\hat T-10]^2$, atribuida a Pierce (1989,
  p. 34), con las unidades fijadas por las Ecs. (4.7) a (4.10) del folio 128:
  presión en pascales, temperatura en grados Celsius, densidad en $\text{kg/m}^3$. La
  Ec. (4.4) del folio 127 define esa presión como
  $P_\mathrm{w}(z) = P_\mathrm{atm} + \int_0^z \rho g\,\mathrm{d}\zeta$,
  y la Ec. (4.11) del folio 128 la evalúa en $98\,066{,}5 \times 1{,}04 =
  101\,989{,}16$ Pa en superficie. El folio 177 enuncia después, para los
  cocientes que escalan las correlaciones de sedimento de Bachman, «*standard
  conditions involving atmospheric pressure, a temperature of 23 °C, and
  salinity 35*» con $\rho_\mathrm{w} = 1024{,}2\ \text{kg/m}^3$.
- **El problema:** dos defectos de distinta naturaleza.

  (a) El 1024,2 del folio 177 no se sigue de la Ec. (4.6) leída con la
  Ec. (4.4). A 23 °C, salinidad 35 y una atmósfera, la ecuación da 1024,287 9,
  que imprime 1024,3. El 1024,2 impreso es lo que da la ecuación con su término
  de presión a cero, es decir, leyendo $P_\mathrm{w}$ como presión manométrica
  contra la definición que enuncia el mismo capítulo. La diferencia son
  $0{,}043\,9\ \text{kg/m}^3$, o 4,3 partes por cien mil.

  (b) La Ec. (4.13), que despeja la (4.6) para estimar la salinidad a partir de
  una densidad medida, imprime el coeficiente de presión como
  $4{,}3\times10^{-5}$ donde la (4.6) tiene $4{,}3\times10^{-7}$. Dos órdenes
  de magnitud, y no es otra magnitud reformulada: es el mismo coeficiente en el
  mismo papel. Arrastrado a 23 °C da $1028{,}63\ \text{kg/m}^3$ frente a 1024,29, un error
  del 0,42 %.
- **Evidencia:** la Ec. (4.6) evaluada en las condiciones enunciadas con la
  presión de la Ec. (4.11), contra el valor que imprime el folio 177; y los dos
  exponentes impresos comparados directamente. Verificado en las páginas 157,
  158, 165 y 207 (pp. 127, 128, 135 y 177 impresas) del PDF de la edición
  Springer de 2010.
- **Comportamiento de la biblioteca:** implementa la Ec. (4.6) con la presión
  absoluta que define su propia Ec. (4.4), porque una definición impresa manda
  sobre la cita redondeada de un valor derivado tres capítulos más allá. La
  discrepancia queda por debajo de toda tolerancia de esta biblioteca, así que
  nada depende de la elección; lo que sí dependía era de elegir bando en
  silencio. La Ec. (4.13) no se implementa
  ([`tests/fluids/test_water.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_water.py),
  comprobaciones de conformidad «Sea water (Ainslie 2010)»).
- **Estado:** sin comunicar.

## Ainslie, Principles of Sonar Performance Modelling (2010), Ec. (9.57)

*Libro, no una norma.*

- **Ubicación:** sección 9.1.1.2.4 (p. 457 impresa), el alcance de transición
  entre los regímenes de decapado de modos y de modo único del modelo de
  flujo de Weston.
- **El impreso:** $r_\text{MS} \approx k^2 H_e^3/(9\eta)$, donde $H$ es la
  profundidad del agua, $H_e$ la profundidad efectiva de Weston de la
  Ec. (9.55), $k = \omega/c_w$ y $\eta$ el gradiente de pérdida por
  reflexión.
- **El problema:** la frase inmediatamente encima prescribe la deducción,
  «estimated by equating θ_n and θ_eff with n = 3/2». Los dos ángulos están a
  cuatro páginas impresas uno de otro, no en la misma página como declaraba
  una revisión anterior de esta entrada:
  - Ec. (9.47), $\theta_\text{eff} = (\pi H/(4\eta r))^{1/2}$, **p. 453
    impresa**, con la **profundidad de agua verdadera $H$** (procede de la
    integral multitrayecto Ec. (9.46), cuyo prefactor $1/(rH)$ es el área de
    cilindro $A_\text{CS} = 2\pi r H$ de la Ec. (9.44), así que $H$ es la
    profundidad que cuenta rebotes de fondo);
  - Ec. (9.56), $\theta_n \approx n\pi/(k H_e)$, **p. 457 impresa**, con la
    **profundidad efectiva $H_e$** (los ángulos de modo los fija la frontera
    aparente de presión nula).

  Igualarlos a $n = 3/2$ da $\pi H/(4\eta r) = 9\pi^2/(4k^2H_e^2)$, es decir
  **$r_\text{MS} = k^2H_e^2H/(9\pi\eta)$**. La forma impresa es mayor en
  $\pi H_e/H$. El factor $\pi$ es incondicional: sobrevive incluso si se
  sustituye $H_e$ por $H$ en la Ec. (9.47), que es presumiblemente como
  surgió el $H_e^3$ impreso, y esa lectura daría $k^2H_e^3/(9\pi\eta)$,
  todavía $\pi$ por debajo del impreso. El residuo $H_e/H$ es la propia
  sustitución de profundidad, y tiende a 1 en alta frecuencia. La otra
  transición de la misma sección, la Ec. (9.50)
  $r_\text{CS} = \pi H/(4\eta\psi_c^2)$, sigue su propia deducción
  exactamente (es donde se cruzan la Ec. (9.42) y la Ec. (9.49)), así que el
  defecto queda confinado a la Ec. (9.57).
- **Evidencia:** la re-deducción simbólica de arriba, comprobada
  numéricamente para $H = 50\ \text{m}$, $f = 250\ \text{Hz}$,
  $c_w = 1500\ \text{m/s}$ sobre el lecho de arena de la Tabla 9.1
  ($\eta = 0.28\ \text{Np/rad}$, $\psi_c = 33.56^\circ$,
  $H_e = 53.63\ \text{m}$, $k = 1.047\ \text{m}^{-1}$):

  | | $r_\text{MS}$ | $\theta_\text{eff}$ allí (Ec. 9.47) |
  |---|---|---|
  | deducción, $k^2H_e^2H/(9\pi\eta)$ | 19.9 km | 4.808° |
  | Ec. (9.57) impresa, $k^2H_e^3/(9\eta)$ | 67.1 km | 2.619° |

  La razón $67.1/19.9$ es $\pi H_e/H = 3.3695$ a todos los dígitos
  arrastrados. La columna de ángulos es una comprobación independiente que no
  depende de cómo se lea la deducción: los dos primeros ángulos de modo de la
  Ec. (9.56) son $\theta_1 = 3.205^\circ$ y $\theta_2 = 6.410^\circ$, así que
  $\theta_{3/2} = 4.808^\circ$. En el alcance deducido el ángulo efectivo es
  exactamente $\theta_{3/2}$, a mitad de camino entre los dos primeros modos,
  que es lo que el texto pide. En el alcance impreso ha caído a 2.619°, **por
  debajo del propio $\theta_1$**: el segundo modo se habría decapado mucho
  antes, así que ese alcance no puede ser donde empieza el régimen de modo
  único. Ambas fórmulas impresas están confirmadas en la página 483 del PDF
  (p. 453 impresa) y la página 487 del PDF (p. 457 impresa) de Ainslie,
  Principles of Sonar Performance Modelling (2010).
- **Comportamiento de la biblioteca:** `weston_regime_boundaries` en
  [`propagation/weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/underwater/propagation/weston_regimes.py)
  implementa el $k^2H_e^2H/(9\pi\eta)$ consistente con la deducción, que es
  además lo que mantiene $\theta_\text{eff}$ definido con $H$ en todos los
  puntos donde el módulo evalúa la Ec. (9.47). La regla de igualación está
  fijada por
  `test_mode_stripping_boundary_equates_theta_eff_with_mode_3_over_2`, que
  reconstruye ambos ángulos desde las ecuaciones impresas y no desde la
  implementación, y la definición compartida de $\theta_\text{eff}$ por
  `test_composite_loss_and_the_boundary_use_the_same_effective_angle` (ambos
  en
  [`tests/underwater/propagation/test_weston_regimes.py`](https://github.com/jmrplens/phonometry/blob/main/tests/underwater/propagation/test_weston_regimes.py)).
- **Estado:** sin notificar (libro, no una norma).

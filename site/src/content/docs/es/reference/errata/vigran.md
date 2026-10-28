---
title: "Erratas de Vigran (2008)"
description: "Erratas de Vigran (2008): 3 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 3 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Vigran (2008), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Vigran, Building Acoustics (2008), pie de la Figura 8.37 (exponente de la rigidez de la moqueta)

- **Fuente no normativa** (libro).
- **Ubicación:** sección 8.4.2, el pie de la Figura 8.37 en la p. 320 impresa
  / p. 341 del PDF, que etiqueta las curvas de mejora predicha de dos
  revestimientos de suelo colocados sobre un suelo pesado.
- **El impreso:** «Predicted improvement with a linear model: stiffness of
  carpet squares 3.2·10^6 N/m, vinyl covering 5.2·10^6 N/m.» (Vigran escribe
  el separador decimal como punto.)
- **El problema:** el exponente de la moqueta está un orden de magnitud alto.
  El cuerpo del texto que introduce la figura, en la p. 321 impresa, dice de
  las losetas de moqueta que «we have assumed that the covering has the same
  stiffness as used in Figure 8.36», y la Figura 8.36 está etiquetada
  $s = 3.2 \cdot 10^{5}\ \text{N/m}$ dentro del gráfico, el mismo valor que
  el cuerpo del texto de la p. 320 impresa le da. El valor del vinilo del
  mismo pie es correcto.
- **Evidencia:** la p. 320 impresa declara $3.2 \cdot 10^{5}\ \text{N/m}$
  «giving a resonance frequency f0 of approximately 130 Hz with a hammer mass
  of 0.5 kg», y $\sqrt{3.2 \cdot 10^{5}/0.5}/(2\pi) = 127.3\ \text{Hz}$ lo
  reproduce mientras que
  $\sqrt{3.2 \cdot 10^{6}/0.5}/(2\pi) = 402.6\ \text{Hz}$ es una frecuencia
  que no aparece en ningún lugar de la sección. La misma aritmética aplicada
  al valor del vinilo del pie da
  $\sqrt{5.2 \cdot 10^{6}/0.5}/(2\pi) = 513.3\ \text{Hz}$ contra los
  «approximately 510 Hz» impresos en la p. 321, lo que fija la fórmula y la
  masa de martillo que usó el autor. Gráficamente, las dos curvas de
  predicción a trazos de la Fig. 8.37 están a unas dos octavas una de otra,
  casando con la razón de rigideces
  $5.2 \cdot 10^{6}/(3.2 \cdot 10^{5}) = 16.25$ (un factor 4.03 en
  frecuencia) y no con
  $5.2 \cdot 10^{6}/(3.2 \cdot 10^{6}) = 1.63$ (un factor 1.27). Verificado
  en la página 341 del PDF (p. 320 impresa) de Vigran, Building
  Acoustics:2008, en la que ambos exponentes del pie leen 6 sin ambigüedad y
  el cuerpo del texto de la misma página lee
  $3.2 \cdot 10^{5}\ \text{N/m}$, con el argumento circundante leído en la
  página 340 del PDF (p. 319 impresa) y la página 342 del PDF (p. 321
  impresa) de la misma edición.
- **Comportamiento de la biblioteca:** no hizo falta ninguno; la biblioteca
  toma la rigidez del revestimiento del usuario a través de
  `covering_contact_stiffness`, y las frecuencias de corte impresas en las
  que está anclada vienen de Hopkins y no de este pie.
- **Estado:** sin notificar.

## Vigran, Building Acoustics (2008), Ec. (9.18) (coeficiente del lado receptor)

- **Ubicación:** sección 9.2.3.2, Ec. (9.18) (p. 339 impresa), el factor de
  transmisión del modelo unidimensional de plénum de techo suspendido según
  Mechel (1980).
- **El impreso:** el denominador lee $m_S L_S \cdot m_R L_R h$ con el $m_R$
  **sin prima**, mientras que el exponente de la misma expresión lleva el
  $m'_R = m_R + s_R \tau_R / h$ con prima de la Ec. (9.17).
- **El problema:** los dos lados del plénum se integran de la misma manera.
  La integral del lado receptor es
  $\int_0^{L_R} \exp(-\varepsilon m'_R x)\,dx = (1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R)$,
  así que el factor que la normaliza debe ser $m'_R L_R$, exactamente igual
  que el del lado emisor es $m_S L_S$. Leída al pie de la letra, la expresión
  impresa no es un factor de transmisión en absoluto: arrastra un
  $m'_R/m_R = 1 + s_R \tau_R/(h m_R)$ espurio, así que crece sin cota cuando
  cae el amortiguamiento del plénum. Dos consecuencias son visibles con
  entradas corrientes ($L_S = L_R = 5\ \text{m}$, $h = 0.6\ \text{m}$,
  $R_S = R_R = 25\ \text{dB}$, $\varepsilon = 2$, $s_S = s_R = 0.5$): el
  modelo **diverge cuando el amortiguamiento del plénum se desvanece**, dando
  $R_\text{cl} = 40.26\ \text{dB}$ a $m_R = 0.01\ \text{1/m}$ pero solo
  26.48 dB a $10^{-4}$ y 6.64 dB a $10^{-6}$, contra los 40.85 dB finitos que
  la lectura deducida devuelve para el mismo plénum desnudo, donde el término
  de fuga $s_R \tau_R/h$ acota el camino; un plénum sin absorbente alguno se
  predice por tanto arbitrariamente peor que el valor limitado por la fuga en
  lugar de igual a él. También **rompe la conservación de la energía**,
  devolviendo $\tau_\text{cl} = 4.45$ a $R_S = R_R = 6\ \text{dB}$,
  $m_R = 0.01$ y $\tau_\text{cl} = 829$ a $R_S = R_R = 0\ \text{dB}$,
  $m_R = 10^{-3}$.
- **Evidencia:** con $m'_R$ en el denominador todas esas patologías
  desaparecen: $\tau_\text{cl}$ se aplana sobre el valor limitado por la fuga
  cuando el amortiguamiento se desvanece, donde la forma impresa sigue
  creciendo, y está acotado por arriba por 1 porque
  $(1 - \exp(-\varepsilon m'_R L_R))/(\varepsilon m'_R L_R) \le 1$, y se
  reduce al propio resultado de atenuación pequeña de Vigran, la Ec. (9.19)
  $\tau_\text{cl} = \varepsilon^2 \tau_S \tau_R L_R/(4h)$, siempre que
  $m_S L_S$ y $m'_R L_R$ son ambos pequeños. Con el $m_R$ impreso el mismo
  límite recoge el factor $m'_R/m_R$, que diverge, así que la Ec. (9.18) tal
  como está impresa no se reduce a la Ec. (9.19) en absoluto: las dos
  ecuaciones que el libro presenta como pareja son inconsistentes entre sí.
  Verificado en la página 361 del PDF (p. 339 impresa) de Vigran, Building
  Acoustics:2008, que muestra el denominador llevando el $m_R$ sin prima
  mientras el exponente de la misma expresión lleva el $m'_R$ con prima de la
  Ec. (9.17).
- **Comportamiento de la biblioteca:** `plenum_flanking_reduction_index` en
  [`ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/building/prediction/ceiling_plenum.py)
  implementa el $m'_R$ deducido en el exponente y en el denominador, con la
  lectura documentada junto a la fórmula, y rechaza un factor de transmisión
  por encima de la unidad en lugar de reportar un índice de reducción sonora
  negativo. Los tests fijan la física que el modelo debe (monotonía en el
  amortiguamiento, la cota $\tau_\text{cl} \le 1$, el tamaño del término de
  fuga de la Ec. (9.17) en un techo realista) y la única propiedad que separa
  las dos lecturas: un plénum desnudo no peor que el valor sin amortiguar de
  la Ec. (9.20)
  ([`tests/building/prediction/test_ceiling_plenum.py`](https://github.com/jmrplens/phonometry/blob/main/tests/building/prediction/test_ceiling_plenum.py)).
- **Estado:** sin notificar (libro, no una norma). El artículo original de
  Mechel de 1980, que Vigran reproduce, no estuvo disponible para comprobar
  si la errata se origina allí.

## Vigran (2008), tabla 3.1 (un coeficiente de Poisson cuyo segundo extremo ha perdido el punto decimal)

- **Dónde:** tabla 3.1, «Examples of material properties», fila «Aluminium»,
  columna «Poisson's ratio», en la página impresa 88 (página 109 del PDF).
  Fuente no normativa: un libro de texto.
- **Lo impreso:** «0.33–034».
- **El problema:** un coeficiente de Poisson está entre $-1$ y $0.5$, y $034$
  no lo es. La fila de encima, el acero, imprime su intervalo como
  «0.28–0.31» con los dos extremos en decimal, igual que todos los demás
  intervalos de la columna. Al segundo extremo del intervalo del aluminio se
  le ha caído el punto decimal.
- **Evidencia:** Verificado en la página 109 del PDF (p. impresa 88) de
  Vigran, *Building Acoustics* (2008). La celda se lee y dice «0.33–034»; la
  del acero justo encima dice «0.28–0.31».
- **Qué hace la biblioteca:** la celda se guarda como `misprinted` en
  [`PUBLISHED_SOLIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/solids/catalogue.py) y se rechaza.
  El extremo que se quería poner es fácil de adivinar por el patrón, pero la
  página no lo imprime, y esta biblioteca no termina un valor que la página
  dejó sin terminar.
- **Estado:** sin comunicar.

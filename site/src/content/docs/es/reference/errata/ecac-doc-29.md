---
title: "Erratas de ECAC Doc 29"
description: "Erratas de ECAC Doc 29: 5 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 5 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre ECAC Doc 29, en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix B, Ec. (B-41) (deceleración en descenso)

- **Ubicación:** Appendix B, sección B7.1.1, la deceleración $a$ definida
  bajo la Ec. (B-41), en la página que lleva la Ec. (B-40) y la Ec. (B-41).
- **El impreso:**
  $a = k^2 \left(\left(\left(\mathrm{Pt1(NextSeg)}_{TAS} - w\right)/\cos\gamma\right)^2 - \left(\left(\mathrm{Point1}_{TAS} - w\right)/\cos\gamma\right)^2\right) / \left(2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma\right)$,
  es decir, ambas velocidades respecto al suelo divididas por $\cos\gamma$
  sobre dos veces la longitud oblicua del segmento.
- **El problema:** la pendiente de descenso se cuenta dos veces. La
  deceleración media a lo largo de la trayectoria de vuelo es el cambio del
  cuadrado de la velocidad a lo largo del camino sobre dos veces la longitud
  del camino; la expresión impresa convierte las velocidades a valores a lo
  largo del camino *y* usa una longitud de camino que ya es la oblicua, así
  que sobreestima $|a|$ en $1/\cos^2\gamma$. La Ec. (B-21) de la 4.ª edición
  es autoconsistente, y el denominador no es lo que cambió: lee
  $2 \cdot \Delta s/\cos\gamma$ con $\Delta s$ «the ground distance covered»,
  que es la misma longitud oblicua que la 5.ª edición escribe como
  $2\left(\mathrm{Point1\_Height} - \mathrm{Pt1(NextSeg)\_Height}\right)/\sin\gamma$.
  Lo que cambió es el numerador. La Ec. (B-22) de la 4.ª edición define las
  velocidades que divide como *velocidades respecto al suelo*,
  $V = V_C\cos\gamma/\sqrt{\sigma} - w$, es decir, la velocidad verdadera
  resuelta en el plano horizontal, así que dividir cada una por $\cos\gamma$
  restituye correctamente una velocidad a lo largo del camino. La 5.ª edición
  alimenta la Ec. (B-41) con la propia $\mathrm{TAS}$ de los puntos del
  perfil, que ya es a lo largo del camino, y conservó la división. Los
  propios resultados de referencia del Doc 29 lo deciden: de los doce puntos
  del caso 2D del Volumen 3 Parte 2, volado enteramente con ese tipo de paso,
  nueve se alcanzan por la deceleración. Las velocidades respecto al suelo
  simples reproducen el empuje tabulado en cada uno de los doce, peor
  desviación 0.047 lb, mientras que las velocidades divididas impresas se
  quedan cortas en los nueve, por 6.05, 5.47, 4.02, 3.81, 4.56, 4.45, 0.29,
  6.35 y 6.41 lb en orden de perfil: siempre bajas, y nunca dentro de las
  0.05 lb de precisión impresa del propio libro de cálculo. El término de
  resistencia junto a ella sí conserva el $\cos\gamma$ que imprime la misma
  ecuación, cosa que los mismos puntos confirman a las mismas 0.05 lb.
- **Evidencia:** reproducción de la hoja `D1-(Arrival_Results)` del Volumen 3
  Parte 2, caso 2D, bajo cada lectura. Verificado en la página 104 del PDF
  (p. B-31 impresa) de ECAC.CEAC Doc 29, 5.ª ed., Volumen 2: Technical guide,
  que lleva la Ec. (B-40), la Ec. (B-41) y la deceleración bajo ella, y en la
  página 90 del PDF (p. B-15 impresa) de ECAC.CEAC Doc 29, 4.ª edición,
  Volumen 2, que lleva la Ec. (B-21) y, justo debajo, la Ec. (B-22) que
  define sus $V_1$ y $V_2$ como velocidades respecto al suelo y decide así la
  lectura.
- **Comportamiento de la biblioteca:** `flight_performance` calcula la
  deceleración desde las velocidades respecto al suelo simples sobre la
  longitud oblicua, y el docstring del helper lleva la desviación y los
  números de arriba. `test_arrival_case_reproduces_every_profile_point` fija
  los 124 puntos de llegada, y la fila de conformidad *ECAC Doc 29 Appendix B
  approach thrust* fija el empuje de descenso del caso 2A.
- **Estado:** sin notificar.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix B, Ec. (B-18) (gradiente de pista)

- **Ubicación:** Appendix B, sección B6.1.1, la aceleración media $a$
  definida bajo la Ec. (B-18).
- **El impreso:** «$a$ is the average acceleration (ft/s$^2$) along the
  runway, equal to:
  $a = \left(V_C/\sqrt{\sigma}\right)^2/\left(2 \cdot s_{TOw}\right)$», con
  «$V_C$ is the Calibrated Airspeed (**kt**) at *Point2*» y $s_{TOw}$ en pies
  en la misma página.
- **El problema:** la expresión se declara en ft/s$^2$ y evalúa en kt$^2$/ft.
  El factor que falta es $k^2 = 1.68781^2 = 2.8487$, el cuadrado de la
  constante de nudos a pies por segundo que el Doc 29 fija en B2.2 y lleva
  explícitamente en la Ec. (B-24) y la Ec. (B-41), que construyen
  aceleraciones con el mismo tipo de expresión. No es cosmético: $a$ entra
  solo a través de $a/(a - g\,G_R)$, así que infravalorarla en 2.85
  sobrevalora la corrección de gradiente, y en una pendiente ascendente del
  1 % con $V_{CTO} = 162.65$ kt y $s_{TOw} = 4900$ ft los 7.69 ft/s$^2$
  dimensionalmente correctos dan un factor de 1.0437 contra el 1.1353 de la
  lectura literal: un 8.8 % de distancia de despegue. La 4.ª edición lleva la
  misma omisión, así que es heredada y no introducida, e imprime
  $\left(V_C\sqrt{\sigma}\right)^2$ donde la 5.ª imprime
  $\left(V_C/\sqrt{\sigma}\right)^2$; solo la colocación de la 5.ª edición es
  una velocidad que el avión tiene, ya que $V_C/\sqrt{\sigma}$ es la
  velocidad verdadera de la Ec. (B-7).
- **Evidencia:** análisis dimensional contra la Ec. (B-24) y la Ec. (B-41)
  del mismo documento. Verificado en la página 90 del PDF (p. B-17 impresa)
  de ECAC.CEAC Doc 29, 5.ª ed., Volumen 2: Technical guide, y, para la mitad
  heredada, en la página 86 del PDF (p. B-11 impresa) de ECAC.CEAC Doc 29,
  4.ª edición, Volumen 2, donde la misma definición está bajo la Ec. (B-11) y
  lee
  $\left(V_C\cdot\sqrt{\sigma}\right)^2/\left(2\cdot s_{TOw}\right)$,
  ft/s$^2$. Esta no puede arbitrarse contra los resultados de referencia: la
  hoja de casos de salida `C8-(Departure_Cases)` del Volumen 3 Parte 2 no
  tiene columna de gradiente de pista, así que los 17 casos de referencia se
  vuelan a $G_R = 0$, donde la Ec. (B-18) es la identidad.
- **Comportamiento de la biblioteca:** `flight_performance` restituye $k^2$ y
  toma la colocación de $\sqrt{\sigma}$ de la 5.ª edición; el docstring del
  helper declara ambas desviaciones y que ningún caso de referencia puede
  detectar ninguna de las dos.
- **Estado:** sin notificar.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix B, Ec. (B-21) (velocidad a mitad de paso)

- **Ubicación:** Appendix B, sección B6.1.2, el empuje neto corregido a mitad
  de paso $\overline{CNT}$ definido bajo la Ec. (B-21), en la rama que lo
  calcula desde la Ec. (B-12), es decir, para todo avión que lleva la tabla
  de coeficientes de hélice. B4.1 y B4.2 reparten los turbohélices entre
  ellas sin declarar regla, así que este no es el mismo conjunto que «los
  turbohélices»: de los 20 de ANP v2.3, 11 están en la tabla de hélice y
  llegan a la Ec. (B-12), los otros 9 están en la tabla de reactores y llegan
  a la Ec. (B-9), y los 8 aviones de pistón están todos en la tabla de
  hélice.
- **El impreso:** $\overline{CNT}$ «is the Corrected Net Thrust of the
  aircraft when being located at mid-step, i.e. at the altitude
  $Alt = E_{Apt} + \left(\mathrm{Point\ 1\_Height} + \mathrm{Point\ 2\_Height}\right)/2$»,
  y después, bajo «In the case of Eq. B-12,»,
  $V_T = \sqrt{0.5\left(\left(\mathrm{Point\ 2\_TAS}\right)^2 + \left(\mathrm{Point\ 1\_TAS}\right)^2\right)}$,
  la media cuadrática de las dos velocidades verdaderas de los extremos.
- **El problema:** la velocidad contradice la altitud nombrada una línea más
  arriba. Un paso Climb se vuela a una velocidad calibrada mantenida, así que
  la velocidad verdadera a la altitud de mitad de paso está fijada y es
  $V_C/\sqrt{\sigma}$ evaluada en la $\sigma$ de mitad de paso (Ec. B-7); la
  media cuadrática de los dos valores de los extremos es un número distinto.
  Las dos ramas de la misma lista describen por tanto dos aviones distintos
  en el único punto que ambas llaman mitad de paso: la rama de reactores
  imprime
  $V_C = \mathrm{Point\ 2\_TAS} \cdot \sqrt{\sigma_{Point\ 2}}$, que es la
  propia velocidad calibrada mantenida del paso y sitúa así el avión a
  $V_C/\sqrt{\sigma}$ a media subida, mientras que la rama de la Ec. (B-12)
  lo sitúa en la media cuadrática de los extremos. La media se lee además
  como trasplantada. La sección B6.1.3, para el paso Accelerate, está
  construida exactamente sobre esta media cuadrática y es autoconsistente con
  ella, dando a *ambas* ramas la misma
  $\overline{V_T} = \sqrt{\left(V_{T2}^2 + V_{T1}^2\right)/2}$ y
  convirtiéndola para la forma de reactores con la
  $\sqrt{\sigma_{Alt}}$ de mitad de paso; B6.1.2 conserva la línea de la
  Ec. (B-12) pero sustituye la línea de reactores por una cantidad de
  Point 2, y solo una de las dos sobrevive a la sustitución. De los
  candidatos el impreso es el mayor: a $V_C$ constante la velocidad verdadera
  crece convexamente con la altitud, así que la media cuadrática supera a la
  media aritmética, que supera al valor de media altitud. La Ec. (B-12) hace
  el empuje inversamente proporcional a $V_T$, así que la velocidad impresa
  infravalora el empuje a mitad de paso, infravalora $\sin\gamma$ y tiende la
  subida larga.
- **Evidencia:** reproducción de la hoja `D2-(Departure_Results)` del
  Volumen 3 Parte 2 bajo cada lectura. Los cuatro casos de salida de
  turbohélice son los únicos datos de referencia que llegan a esta rama, y
  son unánimes. En el caso 56 el último punto del perfil está impreso a
  400814.3 ft: la lectura de altitud de mitad de paso lo deja a 0.001 ft, la
  media aritmética 323.944 ft largo y la media cuadrática impresa 544.944 ft
  largo, contra los 0.15 ft con los que las distancias de salida casan por lo
  demás. Los casos 8, 28 y 68 dejan el mismo punto final 172.333, 223.003 y
  544.944 ft largo bajo la lectura impresa y 102.535, 132.673 y 323.944 ft
  largo bajo la media aritmética, siempre largo y nunca cerca de la precisión
  impresa; la lectura de altitud de mitad de paso queda a 0.049 ft de todos
  los puntos de los cuatro casos, peor caso el 28. La desviación crece con la
  altura del paso, como debe un error de convexidad: en el caso 8 la lectura
  impresa deja $V_T$ 0.0225 kt por encima del valor de mitad de paso en la
  subida de 1500 ft y 0.1066 kt por encima en la de 2500 ft. Verificado en la
  página 92 del PDF (p. B-19 impresa) de ECAC.CEAC Doc 29, 5.ª ed.,
  Volumen 2: Technical guide, que lleva la frase de la altitud de mitad de
  paso, la $V_C$ de la rama de reactores y la $V_T$ de la rama de la
  Ec. (B-12) en una misma página, y en la página 95 del PDF (p. B-22 impresa)
  del mismo documento para el par de B6.1.3 del que la línea de la Ec. (B-21)
  parece extraída.
- **Comportamiento de la biblioteca:** `flight_performance` evalúa la forma
  de hélice a la velocidad verdadera que el avión tiene a la altitud de mitad
  de paso, y el comentario del helper del paso Climb cita la expresión
  impresa, dice que el modelo se aparta de ella y apunta aquí.
  `test_departure_case_reproduces_every_profile_point` fija los 190 puntos de
  salida, cuatro de cuyos casos se vuelan sobre la Ec. (B-12).
- **Estado:** sin notificar. De las tres desviaciones del Appendix B
  registradas aquí esta es la que los resultados de referencia deciden con
  más nitidez, y la única que cambia un perfil distribuido.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix D, Table D-6c (la última fila es la última fila de la Table D-6b)

- **Ubicación:** Appendix D, Table D-6c «Revised JETW NPD data using
  SAE-ARP-866A», última fila (JETW, SEL, operación D, ajuste de potencia
  22500).
- **El impreso:** 109.8, 106.0, 103.2, 100.2, 95.2, 89.8, 85.8, 81.4, 76.8 y
  72.3 dB de 200 ft a 25000 ft: los diez valores de la última fila de la
  Table D-6b, el mismo avión recalculado con SAE-ARP-5534, impresa unas
  líneas más arriba en la misma página.
- **El problema:** el texto bajo la Table D-5 construye la Table D-6c como los
  niveles de la Table D-6a más los incrementos SAE-ARP-866A de la Table D-5,
  y las otras seis filas de la tabla son exactamente eso, hasta la última
  cifra. La última fila de la Table D-6a (109.7, 105.7, 102.8, 99.5, 94.0,
  88.0, 83.7, 79.0, 73.9 y 68.7 dB) más los incrementos DEP_103 de la
  Table D-5 (+0.2, +0.3, +0.4, +0.6, +0.9, +1.3, +1.5, +1.8, +2.2 y +2.8 dB)
  da 109.9, 106.0, 103.2, 100.1, 94.9, 89.3, 85.2, 80.8, 76.1 y 71.5 dB, y
  los incrementos sin redondear dan los mismos diez valores. Ocho de las diez
  celdas impresas difieren de ellos, hasta 0.8 dB a 25000 ft; las dos que
  coinciden, a 400 ft y a 630 ft, son las dos en que los incrementos de las
  dos vías redondean a la misma suma. La fila se ha copiado de la Table D-6b
  en lugar de calcularse.
- **Evidencia:** recálculo desde las Tables D-6a y D-5 del mismo ejemplo.
  Verificado en la página 133 del PDF (p. D-9 impresa) de ECAC.CEAC Doc 29,
  5.ª ed., Volumen 2: Technical guide, que lleva las Tables D-6a, D-6b y D-6c
  en una misma página, y en la página 132 del PDF (p. D-8 impresa) del mismo
  documento para los incrementos de la Table D-5.
- **Comportamiento de la biblioteca:** `revise_npd_curves` suma el incremento
  a la Table D-6a y da la fila recalculada.
  `test_revised_npd_data_is_table_d6c_but_its_misprinted_row` la fija, y la
  fila de conformidad *ECAC Doc 29 Appendix D Table D-6c* sostiene las otras
  60 celdas de la tabla.
- **Estado:** sin notificar.

## ECAC Doc 29, 5.ª ed., Volumen 2, Appendix D, texto bajo la Table D-2 (las Tables D-3b y D-3c emparejadas con los métodos cambiados)

- **Ubicación:** Appendix D, el párrafo bajo la Table D-2 que presenta las
  tres tablas de atenuación del ejemplo resuelto.
- **El impreso:** «together with the absorption coefficients in Table D-1 for
  the AIR-1845 atmosphere and using attenuation values calculated using
  SAE-ARP-5534 and SAE-ARP-866A for the specified atmosphere [...]. All three
  sets of attenuation values are listed in Tables D-3a, D-3b and D-3c
  respectively.»
- **El problema:** «respectively» da SAE-ARP-5534 a la Table D-3b y
  SAE-ARP-866A a la Table D-3c, y las tablas se titulan al revés: la
  Table D-3b «calculated using SAE-ARP-866A», la Table D-3c «calculated using
  SAE-ARP-5534». Los valores siguen a los títulos. SAE ARP 5534 reproduce las
  240 celdas de la Table D-3c hasta la cifra impresa, y SAE ARP 866A 208 de las
  240 de la Table D-3b, y las otras 32 (los caminos más largos en las
  frecuencias más altas) a menos de media unidad de la cifra impresa más 7
  partes por millón, mientras que el emparejamiento que declara la frase se
  aparta hasta 177 dB,
  a 10 kHz y 25000 ft (921.851 dB frente a 744.810 dB). El texto posterior a
  las tablas, que da la Table D-4 a SAE-ARP-5534 y la Table D-5 a
  SAE-ARP-866A, también sigue a los títulos.
- **Evidencia:** comparación de la frase con los dos títulos de tabla, y
  recálculo de las dos tablas por los dos métodos. Verificado en la página 128
  del PDF (p. D-4 impresa) de ECAC.CEAC Doc 29, 5.ª ed., Volumen 2: Technical
  guide para la frase, y en las páginas 130 y 131 del PDF (pp. D-6 y D-7
  impresas) del mismo documento para los títulos y los valores de las
  Tables D-3b y D-3c.
- **Comportamiento de la biblioteca:** no hace falta ninguno; la biblioteca
  empareja cada tabla con el método que nombra su título, que es el
  emparejamiento que confirman sus valores. Las filas de conformidad
  *ECAC Doc 29 Appendix D Table D-3b* y *Table D-3c* sostienen las dos tablas.
- **Estado:** sin notificar.

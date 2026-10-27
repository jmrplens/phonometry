---
title: "Propiedades de las fuentes que no son erratas"
description: "Propiedades de las fuentes publicadas que parecen erratas y no lo son, registradas para que nadie corrija la biblioteca para ajustarse a ellas."
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

El [registro de erratas](/phonometry/es/reference/errata/) recoge también propiedades de las fuentes publicadas que parecen defectos y no lo son: una diferencia que la propia fuente declara, un redondeo que comparte con su familia, un valor correcto para una forma del material que los otros libros no describen. Se guardan aquí para que nadie, en el futuro, «corrija» la biblioteca para ajustarse a ellas.

## Propiedades de las fuentes, relacionadas, que no son erratas

Registradas aquí para prevenir futuros «arreglos» que romperían la
concordancia con las fuentes publicadas:

- **Norton & Karczub 2e (2003), apéndice 4 A, las densidades del
  poliestireno, el poliuretano y el PVC:** el apéndice imprime $42$, $72$ y
  $66$ kg/m$^3$, donde Mechel y Bies imprimen $1070$, $900$ y $1400$ para los
  mismos nombres. La diferencia no es un dígito perdido. Cada fila de Norton &
  Karczub imprime también un módulo de Young y una velocidad en medio infinito,
  y los tres cumplen $E = \rho c^2$ con un uno por ciento de margen, lo que
  describe la forma expandida o celular del polímero; los otros libros
  describen la maciza. Ninguna de las dos páginas matiza el nombre. Verificado
  en la página 625 del PDF (p. impresa 605). Se registra aquí, y en `ACCEPTED`
  de `scripts/check_solid_agreement.py`, para que las densidades bajas no se
  «corrijan» a las del polímero macizo.
- **Norton & Karczub 2e (2003), apéndice 4 C, hidrógeno y oxígeno a 0 y
  20 °C:** cada gas se imprime con la misma densidad a las dos temperaturas,
  $0.084$ y $1.43$ kg/m$^3$, mientras su velocidad cambia como debe y el aire,
  en la misma tabla, baja de $1.293$ a $1.21$ en el mismo intervalo. No se
  registra como errata porque las propias columnas de la tabla no lo resuelven:
  $P = \rho c^2/\gamma$ sitúa estas filas entre $96$ y $109$ kPa, no más lejos
  de una atmósfera que las del dióxido de carbono y el vapor. Verificado en la
  página 626 del PDF (p. impresa 606). Los cuatro estados lo dicen en su
  `validity` en [`PUBLISHED_FLUIDS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/catalogue.py),
  y la página de catálogos publicados lo muestra sobre su densidad.
- **ISO 11546-1:1995, anexos A y B:** la figura B.1 se titula «Source
  spectrum for an artificial sound source constructed according to the
  guidelines given in annex A», mientras que el anexo A, que pide una chapa de
  acero de 4 mm por 800 mm (aprox.) por 300 mm (aprox.), añade en su propio
  último párrafo que «the length of the steel plate used for this measurement
  was 600 mm» y que una fuente construida según el anexo puede dar otro
  espectro. La figura es por tanto la ilustración de una fuente una cuarta
  parte más corta que la longitud aproximada que prescribe el anexo, y el
  anexo lo dice. Verificado en la página 17 del PDF (p. impresa 10) y la
  página 19 del PDF (p. impresa 12) de la ISO 11546-1:1995 tal como se publica
  en la BS EN ISO 11546-1:2009. No se registra como errata porque la propia
  norma declara la diferencia; se registra aquí para que
  [`ARTIFICIAL_SOURCE_EXAMPLE_LWA`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/enclosure_insulation.py)
  no se lea como una propiedad de una fuente del anexo A.

- **ISO 7235:2003, Ecuaciones (10), (21) y (22):** la ley de los gases
  ideales viene impresa con
  $R = 287\ \text{N}\cdot\text{m}/(\text{kg}\cdot\text{K})$ y la
  temperatura absoluta escrita como $\theta + 273\ ^\circ\text{C}$. Ninguno
  de los dos es el valor exacto (287,05 y 273,15). El desfase por sí solo deja
  una densidad un 0,051 % alta a 20 °C y la constante de los gases le añade
  otro 0,017 %, para un 0,069 % en total. Es una simplificación y no un
  defecto: la densidad que producen sólo se usa en la presión dinámica de las
  Ecuaciones (16), (19) y (20), y ambas series del coeficiente de pérdida de
  presión llevan el mismo factor, de modo que las Ecuaciones (17) y (18) salen
  **escaladas** por él en vez de desplazadas, un 0,069 % bajas, que queda muy
  por debajo de la incertidumbre de un ensayo de pérdida de presión y es lo que
  muestra un resultado calculado según la norma. La
  biblioteca conserva las dos constantes impresas, como
  [`ISO7235_AIR_GAS_CONSTANT_J_KG_K`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_measurement.py)
  y `ISO7235_ABSOLUTE_ZERO_OFFSET_K`, para que un resultado se pueda reproducir
  tal como lo da la norma, y la fila de conformidad «Normal air density
  (Eqs. (10), (21), (22))» deja constancia del tamaño de la diferencia.

- **ISO 12354-1:2017 Tabla L.8 / ISO 12354-2:2017 Tabla G.8, primera fila:**
  la fila etiquetada «Int. wall 1/2 – Ext. wall 1/2» imprime
  $m'_i = 219{,}0\ \text{kg/m}^2$ y $m'_{\perp i}$ (Parte 2:
  $m'_\text{orthogonal}$) $= 360{,}0\ \text{kg/m}^2$, que es la asignación de
  una trayectoria *que sale de la pared exterior*, la dirección opuesta a la
  que da la propia etiqueta de la fila. Leída en la dirección de la fila, el
  elemento que lleva la trayectoria es la pared interior, así que $m'_i$
  debería ser 360,0 y la masa perpendicular 219,0. Es un desliz de etiquetado
  y nada más: la rama es la rama de **esquina** de la T rígida
  $K_{12} = 5{,}7 + 5{,}7 M^2$, donde solo entra $M^2$, así que ambas
  asignaciones devuelven los mismos 5,965 → 6,0 dB. La segunda fila de cada
  tabla, «Ext. wall 1/2 – Ext. wall 1/2», es la rama pasante
  $5{,}7 + 14{,}1 M + 5{,}7 M^2$, donde el signo de $M$ sí importa, y está
  etiquetada y poblada de forma consistente ($M = \log_{10}(360/219)$ da
  9,006 → los 9,0 impresos). Verificado en la página 89 del PDF (p. 83
  impresa) de ISO 12354-1:2017 y la página 46 del PDF (p. 40 impresa) de
  ISO 12354-2:2017. No se registra como errata porque ningún número depende
  de ello; se registra aquí para que un lector futuro no «corrija» el
  convenio por trayectoria de la biblioteca para casar con la fila impresa.
- **Término de agua pura de Francois-Garrison:** las dos cúbicas de $A_3$
  publicadas no se encuentran exactamente en el cambio de 20 °C (un escalón
  de $1 \cdot 10^{-7} f^2\ \text{dB/km}$, 0.1 dB/km a 1 MHz). Inherente a los
  coeficientes publicados.
- **Simplificación de Ainslie-McColm:** la afirmación del artículo de estar
  «within 10 % of Francois-Garrison» se excede marginalmente en las esquinas
  extremas de su dominio declarado (10.4 % a −6 °C / 1 MHz; 12.3 % a 7 km de
  profundidad). Una propiedad del ajuste publicado; ambas transcripciones
  verificadas dígito a dígito.
- **CNOSSOS-EU Anexo II 2.3, número de ecuación que falta:** la sección
  ferroviaria numera sus fórmulas (2.3.1), (2.3.2), (2.3.4), (2.3.5)..., sin
  ninguna (2.3.3) en todo el Anexo II. Verificado en la página 17 del PDF
  (p. L 168/17 impresa) de la Directiva (UE) 2015/996:2015, donde (2.3.2) y
  (2.3.4) están una encima de la otra. No falta nada del método; solo salta
  la numeración.
- **Corrección de errores de CNOSSOS-EU de 2018, códigos de columna de la
  Tabla G-3:** se reporta que la corrección de errores encabeza las siete
  columnas de $L_{r,TR}$ «B/S B/M B/H B/S B/M B/H B/H», donde las tres
  primeras deberían leer «M/S M/M M/H» y la última «W», y la Directiva
  Delegada (UE) 2021/1226 de la Comisión, punto (20)(c) del Anexo, sí
  sustituye ese encabezado por los códigos corregidos más una columna D
  nueva. Se deja sin registrar porque la propia corrección de errores se
  publica solo como HTML en EUR-Lex, así que no pudo obtenerse aquí ninguna
  página impresa suya, y este registro no recoge una afirmación sobre un
  símbolo impreso que no se haya leído de la página. El impreso de 2015 de la
  misma tabla, que sí se leyó, lleva encabezados descriptivos («Mono-block
  sleeper on soft rail pad» y demás) y ningún defecto.
- **Long, Architectural Acoustics 2e, capítulo 17, nivel en la mesa
  adyacente:** el ejemplo del restaurante declara que «at an adjacent table
  3 m (10 ft) away, the direct field level from our conversation is about
  54 dB», donde su propia Ec. (17.50) con los $Q = 2$ y
  $L_W = 70\ \text{dB}$ que producen sus 60 dB a 1.2 m da 52.5 dB. Se deja
  sin registrar porque la lectura pretendida no puede establecerse desde el
  libro: 54 dB es también lo que la misma ecuación da a 2.5 m (54.1 dB, y
  2.5 m es la separación de mesas que el párrafo siguiente deriva), y lo que
  daría una sola duplicación de distancia de 6 dB desde los 60 dB
  redondeados, mientras que el «3 m (10 ft)» impreso es autoconsistente en
  ambas unidades y se repite en el párrafo anterior. `speech_direct_level`
  evalúa la Ec. (17.50) tal como está impresa, así que devuelve 52.5 dB allí;
  no «corregirla» hacia 54 dB.
- **Constante EPNL del Anexo 16 de la OACI:** la constante redondeada 13 del
  Anexo para registros uniformes de 0.5 s difiere de la forma exacta
  $-10\log_{10}(T_0)$ en 0.0103 dB; la biblioteca usa la forma exacta, que la
  referencia integrada del ETM reproduce a cinco decimales.
- **Filas de elementos de la Tabla 14.9 de Long:** la hoja resuelta de ruido
  por conductos del capítulo 14 la produjo un programa comercial, como
  declara el texto que la introduce, y varias de sus filas de elementos no se
  siguen de las tablas impresas a su lado: la fila del ventilador
  (90/86/82/79/77/75/71/61 dB) no es lo que da la Ec. 13.1 con las constantes
  de curvatura hacia delante de la Tabla 13.5 en ese punto de trabajo
  (99/99/89/84/82/77/72/67 dB, y tampoco un desplazamiento de nivel de ello),
  y la fila del conducto flexible (14/14/16/15/17/22/16/13 dB) no es la
  entrada de la Tabla 14.4 para 12 in por 6 ft (3/5/10/15/17/16/9 dB). La
  biblioteca implementa las ecuaciones y tablas impresas, y usa la hoja solo
  para lo que fija de verdad, la aritmética de la cascada; sus filas de
  elementos se introducen tal como están publicadas en
  [`tests/noise_control/test_duct_path.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_duct_path.py).
  El propio redondeo de la hoja tampoco es siempre autoconsistente (la fila 3
  de impulsión imprime un *Sum* de 49 dB a 500 Hz donde $76 - 28 = 48$, y
  después un *Combined* consistente con 48), que es por lo que la comparación
  corre al 1 dB que la hoja impresa lleva.
- **ISO 3747:2010 Tabla E.1, las etiquetas de grado de precisión:** la tabla
  informativa de ejemplos de $\sigma_\mathrm{tot}$ etiqueta sus tres filas
  «0,5 (accuracy grade 1)», «1,5 (accuracy grade 2)» y «3 (accuracy
  grade 3)», mientras que la Tabla 2, normativa, de esta parte da
  $\sigma_{R0}$ = 4,0 dB para el grado 3 de control y el campo de aplicación
  de ISO 3747 cubre solo los grados 2 y 3. Es la ilustración compartida de la
  familia ISO 3740, no una afirmación sobre este método: ISO 3744:2010 imprime
  en su Tabla H.1 la tabla idéntica, con las mismas filas, etiquetas y celdas
  de $\sigma_\mathrm{tot}$, e ISO 3744 cubre solo el grado 2. Verificado en la
  página 42 del PDF (p. 33 impresa) y en la página 27 del PDF (p. 18 impresa)
  de BS EN ISO 3747:2010. La biblioteca lee $\sigma_{R0}$ de la Tabla 2
  normativa (1,5 dB y 4,0 dB, comprobación de conformidad «ISO 3747:2010
  Table 2 / Eq. 22») y usa la Tabla E.1 solo por su fila
  $\sigma_\mathrm{tot}$ = 1,6 / 2,5 / 4,3 frente a $\sigma_{R0}$ = 1,5 dB,
  donde ambas tablas coinciden. No «corregir» la fila de 3 dB a 4,0 dB:
  pertenece a la ilustración de la familia, no a la Tabla 2 de esta parte.
- **ISO 3747:2010 Anexo C, $\theta_\mathrm{ref}$ = 296 K:** el anexo imprime
  la temperatura de referencia de la corrección de impedancia de radiación
  como 296 K junto a una condición de referencia de 23,0 °C, que son
  296,15 K, así que exactamente en las condiciones de referencia
  $C_2 = 15 \lg(296{,}15/296) = +0{,}003\,3$ dB y no cero. El apartado 9.1.4
  de ISO 3741:2010 e ISO 3744:2010 imprimen el mismo $\theta_1$ = 296 K, así
  que es el redondeo de la familia y no una errata de una parte; la
  biblioteca conserva los 296 K en el `C2` compartido de
  [`_sound_power_reverberation.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/_sound_power_reverberation.py)
  y fija el residuo (comprobación de conformidad «ISO 3747:2010 Annex C»).
  No «corregirlo» a 296,15 K.
- **ISO 3747:2010 Ec. (14), el margen de ruido de fondo del suceso aislado:**
  $\Delta L_{Ei} = L'_{Ei,q(\mathrm{ST})} - L_{pi(\mathrm{B})}$ resta un nivel
  de ruido de fondo promediado en el tiempo de un nivel de suceso aislado
  integrado en el tiempo, pidiendo solo que ambos se midan con el mismo
  tiempo de integración $T$. La diferencia es un margen verdadero para
  $T$ = 1 s; para un $T$ mayor el ruido de fondo contiene $10 \lg(T/T_0)$ dB
  más energía sobre el intervalo del suceso (apartado 3.4, NOTA 1). La
  Ec. (25) de ISO 3741:2010 y el apartado 8.3.4 de ISO 3744:2010 imprimen la
  misma línea, verificado en la página 23 del PDF (p. 14 impresa) de BS EN
  ISO 3747:2010 y en las páginas correspondientes de las dos normas hermanas,
  así que es la convención de la familia y no se registra contra una parte.
  La biblioteca aplica la Ec. (14) tal como está impresa por defecto y ofrece
  `integration_time` en
  [`sound_energy_in_situ`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/_sound_power_in_situ.py)
  para llevar antes el ruido de fondo al intervalo del suceso.

- **ISO 5136:2003, apartado 5.3.4.3, el signo de la Ecuación (8):** el
  apartado dice que las correcciones del cono aerodinámico y la bola de
  espuma «are estimated to be negative and of small magnitude», y a
  continuación imprime $C_{3,4} = 10 \lg[1/(1 - U/c)^2]$ dB, que es positiva
  siempre que $U > 0$: a los 20 m/s que se permiten al cono aerodinámico, con
  $c$ = 340 m/s, $+0{,}53$ dB en el lado de impulsión y $-0{,}50$ dB en el de
  aspiración. El signo de la ecuación es el que da la onda plana convectada:
  el flujo de energía de una onda que viaja con el flujo es $(1 + M)^2$ veces
  $p^2/\rho c$, de modo que para una presión dada la potencia es mayor aguas
  abajo y menor aguas arriba. No se registra como errata porque la frase con
  la que se cierra ese mismo párrafo reconcilia las dos: «With this
  simplification, the sound power level obtained by using the nose cone or
  foam ball is expected to be higher than the true sound power level.» La
  corrección negativa es la modal, que no está disponible y se descarta; la
  Ecuación (8) es la parte convectiva que se conserva, y la norma dice en la
  misma frase que lo que queda sesga el $L_W$ hacia arriba. Leído en la
  página 29 del PDF (p. 19 impresa) de ISO 5136:2003. Se registra aquí para
  que nadie «corrija» el signo de la Ecuación (8), que
  [`flow_modal_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/emission/_sound_power_in_duct.py)
  implementa tal como está impresa y que fija
  `test_eq8_omnidirectional_shields` en
  [`tests/emission/test_sound_power_in_duct.py`](https://github.com/jmrplens/phonometry/blob/main/tests/emission/test_sound_power_in_duct.py).

- **Tabla 1 de la ISO 11820:1996 y tabla 3 de la ISO 10847:1997, dos
  correcciones de fondo que no coinciden:** las dos tablas toman el margen
  entre el nivel con la fuente y el nivel sin ella y responden con una
  corrección en decibelios, y responden distinto. La ISO 11820 rechaza por
  debajo de 3 dB y luego quita 3, 2, 2, 1, 1, 1, 0,5 y 0,5 dB hasta un margen
  de 10 dB; la ISO 10847 rechaza por debajo de 4 dB y luego quita 2, 2, 1, 1,
  1 y 1 dB hasta ese mismo margen. Con un margen de 9 dB la primera quita
  0,5 dB y la segunda 1 dB. También difieren los signos, porque la columna de
  la ISO 11820 dice "corrections to be subtracted from sound pressure level
  measured with sound source operating" e imprime sus valores en positivo,
  mientras que la de la ISO 10847 dice "correction to be made to the measured
  sound pressure level" y los imprime en negativo. Ninguna de las dos es una
  errata: son dos tabulaciones, de dos comités, de la misma resta física,
  redondeadas de distinta manera y escritas desde extremos opuestos. Leídas en
  la página 13 del PDF (página impresa 5) de la EN ISO 11820:1996 y en la
  página 11 del PDF (página impresa 7) de la ISO 10847:1997. La biblioteca las
  mantiene separadas como
  [`silencer_background_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencer_in_situ.py)
  y
  [`barrier_background_correction`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/environment/propagation/barrier_in_situ.py),
  cada una con su convenio de signo y su propio rechazo, y una comprobación de
  conformidad las enfrenta en el margen en el que se separan. No hay que
  fundirlas en un único auxiliar.
- **Beranek & Mellow 2e, tabla 7.1, columna de Delany y Bazley:** la tabla
  imprime $a_1$ a $a_4$ = 0.0511, 0.0768, 0.0858, 0.175 donde
  [`DELANY_BAZLEY_COEFFICIENTS`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/materials/absorbers/porous.py)
  tiene $C_1$, $C_3$, $C_5$, $C_7$ = 0.0571, 0.087, 0.0978, 0.189, de la tabla
  D.1 de Bies 5e. Las cuatro amplitudes se separan entre un 8 % y un 14 % y las
  razones no son constantes (1.117, 1.133, 1.140, 1.080), así que ningún factor
  de escala único las relaciona. El motivo es la variable. La ecuación (7.11)
  de Beranek, impresa sobre la tabla en esa misma página, está escrita en
  $R_f/f$ con exponentes **positivos**, mientras que Delany y Bazley, y Bies
  tras ellos, escriben $X = \rho_0 f / R_f$ con exponentes negativos. Las dos
  formas se diferencian exactamente en $\rho_0^{\,b}$, y despejar
  $C = a\,\rho_0^{\,b}$ fila a fila da $\rho_0$ = 1.16, 1.19, 1.21,
  $1.14\ \text{kg/m}^3$, que es la densidad del aire en todas ellas; hacer la conversión
  en sentido contrario con $\rho_0$ = $1.18\ \text{kg/m}^3$ reproduce las cuatro
  amplitudes impresas con un 1,4 %, un 0,4 %, un 1,5 % y un 2,1 % de
  diferencia. Los exponentes lo corroboran por su cuenta: Beranek imprime
  $b_1$ a $b_4$ = 0.75, 0.73, 0.70, 0.59 frente a $C_2$, $C_4$, $C_6$, $C_8$ =
  0.754, 0.732, 0.700, 0.595, los mismos números con dos decimales. El control
  es la otra columna de la tabla: la variable de Miki es $f/\sigma$ y no lleva
  densidad, y la columna de Miki de Beranek, 0.070, 0.107, 0.109, 0.160 con
  0.632, 0.632, 0.618, 0.618, coincide dígito a dígito con las constantes con
  las que está escrita `miki`. Verificado en la página 352 del PDF (página
  impresa 349) de Beranek & Mellow, *Acoustics: Sound Fields, Transducers and
  Vibration* 2e (2019), y en la página 757 del PDF (página impresa 728) de
  Bies, Hansen & Howard, *Engineering Noise Control* 5e (2017). Ninguno de los
  dos libros se equivoca: imprimen una misma regresión en dos variables. La
  biblioteca sigue a Delany y Bazley a través de Bies, en
  $X = \rho_0 f/\sigma$, de modo que sus amplitudes **no** deben «corregirse»
  hacia las de Beranek, lo que aplicaría la densidad del aire por segunda vez.

- **IEC 60268-7:2010, «the standard reference frequency» junto a la frecuencia
  de medida normalizada de 500 Hz:** 7.2 b) fija «the standard measuring
  frequency» en 500 Hz, y la NOTA de 8.3.3.1 da el motivo para el acoplador,
  «to avoid the effects of diaphragm resonance, leakage and standing waves».
  La parte nombra además «the standard reference frequency» (8.3.6.2 b),
  8.6.3.1, 8.6.4.1, 8.7.2.1, 8.9.1 a)) y nunca la define; IEC 60268-1:1985,
  que cita el capítulo 2, sí lo hace, en el capítulo 3: «If a measurement
  relates to a reference frequency, then, in the absence of a clear reason to
  the contrary, this shall be the standard reference frequency of
  1 000 Hz». Los métodos por comparación empiezan y terminan su secuencia de
  ensayo en «the band centred on 1 kHz» (8.6.3.2 c), 8.6.4.2 c)), mientras que
  la fórmula (1) del método en el conducto auditivo imprime su propia banda de
  referencia, 500 Hz. Los dos términos no siempre se mantienen separados:
  8.7.2.1 especifica la distorsión armónica «at the standard reference
  frequency» y 8.7.2.2 b) aplica la tensión «at the standard measuring
  frequency». No se registra como errata porque cada apartado puede leerse tal
  como está impreso. Leído en la página 11 del PDF (p. 9 impresa) de IEC
  60268-1:1985 y en las páginas 17, 21, 23, 26 a 29 y 31 del PDF (pp. 15, 19,
  21, 24 a 27 y 29 impresas) de IEC 60268-7:2010. La biblioteca refiere por
  defecto las respuestas por comparación de
  [`field_comparison_response`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/headphones.py)
  a 1 000 Hz, y la respuesta en el conducto auditivo y la respuesta relativa
  del acoplador a 500 Hz; la fila de conformidad «IEC 60268-7:2010 8.6.3.1
  with IEC 60268-1:1985 Clause 3» fija el valor por defecto. No hay que pasar
  las respuestas por comparación a 500 Hz para uniformarlas.

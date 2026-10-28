---
title: "Erratas de Long (2014)"
description: "Erratas de Long (2014): 4 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 4 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Long (2014), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Long, Architectural Acoustics 2e (2014), Ec. (18.24) (signo de la directividad del micrófono)

- **Ubicación:** capítulo 18, «Multiple Open Microphones», Ec. (18.24)
  (p. 699 impresa), el criterio de estabilidad de ganancia antes de
  realimentación generalizado a varios micrófonos abiertos.
- **El impreso:**
  $Z_S + L_{H-M} + \Delta L_\text{nom} \le L_{H-L} \boldsymbol{+} D_M(\theta) - 10$,
  con el índice de directividad del micrófono entrando en el lado derecho con
  signo más.
- **El problema:** la Ec. (18.24) es la generalización a número de micrófonos
  abiertos de la Ec. (18.20) (p. 698 impresa), que lee
  $Z_S + L_{H-M} \le L_{H-L} \boldsymbol{-} D_M(\theta) - 10$ y que se sigue
  a su vez de la condición de oscilación Ec. (18.19),
  $Z_S + L_{H-M} = L_{H-L} - D_M(\theta)$, obtenida sustituyendo la ganancia
  del lazo de realimentación $G_S = L_{H-M} - L_{H-L} + D_M(\theta)$
  (Ec. (18.18)) en $Z_S + G_S = 0$ (Ec. (18.16)). Poner $N_m = 1$ hace
  $\Delta L_\text{nom} = 0$, así que la Ec. (18.24) debe reducirse a la
  Ec. (18.20) y no lo hace. El signo importa físicamente: $D_M(\theta)$ es
  «usually negative» en la propia definición de Long (en torno a $-2$ a
  -3 dB para un cardioide apuntado al orador), así que tal como está impreso
  un micrófono direccional *costaría* ganancia antes de realimentación en
  lugar de comprarla, invirtiendo la propia conclusión del capítulo de que
  «it is prudent to incorporate a cardioid or hypercardioid microphone into a
  system».
- **Evidencia:** la ecuación impresa lee
  $Z_S + L_{H-M} + \Delta L_\text{nom} \le L_{H-L} + D_M(\theta) - 10$,
  contra $Z_S + L_{H-M} \le L_{H-L} - D_M(\theta) - 10$ dos páginas antes,
  donde la misma posición lleva un menos. (Una revisión anterior de esta
  entrada citaba la extracción de `pdftotext`,
  `Z S þ L HM þ DL nom  L HL þ D M ðqÞ  10`, en la que `þ` es la ligadura que
  este PDF usa para «+» y todos los signos menos se han perdido por completo;
  esa extracción no puede distinguir un más de un menos y nunca debió ser la
  evidencia.) Verificado en la página 697 del PDF (p. 699 impresa) y la
  página 696 del PDF (p. 698 impresa) de Long, Architectural Acoustics 2e
  (2014). El signo menos es el que reproduce los propios casos particulares
  resueltos de Long a $N_m = 1$: con $Z_S = -6\ \text{dB}$, la Ec. (18.21) da
  $L_{H-M} \le L_{H-L} - D_M(\theta) - 4$ (un micrófono omnidireccional 4 dB
  por debajo del nivel medio de la audiencia), y la Ec. (18.22) da
  $L_{H-M} \le L_{H-L} - 2$ para un cardioide a $D_M = -2\ \text{dB}$.
  Ninguno de los dos casos particulares es recuperable desde la Ec. (18.24)
  impresa.
- **Comportamiento de la biblioteca:** `feedback_stability` en
  [`sound_reinforcement.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/electroacoustics/sound_reinforcement.py)
  implementa el signo de la Ec. (18.20), con una nota junto al criterio.
  Ambos casos particulares de Long están fijados por tests de regresión
  ([`tests/electroacoustics/test_sound_reinforcement.py`](https://github.com/jmrplens/phonometry/blob/main/tests/electroacoustics/test_sound_reinforcement.py))
  y por las comprobaciones de conformidad «Long, Architectural Acoustics 2e,
  Eq. (18.21)» y «Eq. (18.22)».
- **Estado:** sin notificar (libro, no una norma, así que no normativo).

## Long, Architectural Acoustics 2e (2014), Ec. (17.53) (constante de la cota de comunicación)

- **Ubicación:** capítulo 17, «Restaurant Design», Ec. (17.53) (p. 666
  impresa), la absorción mínima por mesa ocupada para una comunicación entre
  mesas adecuada.
- **El impreso:** $A_\text{tab} > 6.33 r_s^2$.
- **El problema:** la cota es la Ec. (17.52),
  $L_\text{SN} = 10\log_{10}[Q/(4\pi r^2)] + 10\log_{10}[A_\text{tab}/4]$,
  resuelta para $A_\text{tab}$ en el umbral declarado
  $L_\text{SN} > -6\ \text{dB}$, lo que da
  $A_\text{tab} > 16\pi \cdot 10^{-0.6} r_s^2/Q$. Con el $Q = 2$ que el
  capítulo usa para un orador, esa constante es 6.3130, no 6.33. La brecha es
  del $0.27\,\%$, es decir, el último dígito impreso: 6.33 es lo que devuelve
  $16\pi \cdot 10^{-0.6}/2$ si $10^{-0.6}$ se arrastra grueso como 0.252 en
  lugar de 0.251 19. Se clasifica como discrepancia de redondeo y no como
  error estructural de la fórmula, ya que la fórmula misma queda confirmada
  por su compañera (abajo) y ninguna suposición alternativa consistente
  reproduce 6.33 (exigiría $Q = 1.995$).
- **Evidencia:** la Ec. (17.54) inmediatamente siguiente es la misma forma
  cerrada en el umbral de privacidad $L_\text{SN} < -9\ \text{dB}$, y su
  constante impresa 3.16 es exactamente lo que da
  $16\pi \cdot 10^{-0.9}/2 = 3.1640$, confirmando la fórmula y el $Q = 2$.
  Solo la constante de -6 dB está desviada. Lo que *no* discrimina es la
  prosa de Long un párrafo después, «at least 6.3 or more square meters (68
  sq ft) of absorption per table»: $6.313\ \text{m}^2$ son $67.95\ \text{ft}^2$ y
  $6.33\ \text{m}^2$ son $68.14\ \text{ft}^2$, así que ambos se imprimen como 68 sq ft,
  y ambos redondean a $6.3\ \text{m}^2$. Una revisión anterior de esta entrada ofrecía
  esa conversión como corroboración. Verificado en la página 665 del PDF
  (p. 666 impresa) de Long, Architectural Acoustics 2e (2014).
- **Comportamiento de la biblioteca:** `absorption_per_table` en
  [`_crowd_noise.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/room/_crowd_noise.py) calcula la cota
  desde la Ec. (17.52) en lugar de cablear ninguna de las dos constantes, así
  que ambas cotas se mantienen mutuamente consistentes; el valor 6.313 y el
  3.16 impreso están fijados por tests de regresión
  ([`tests/room/test_crowd_noise.py`](https://github.com/jmrplens/phonometry/blob/main/tests/room/test_crowd_noise.py)) y
  la constante 3.16 por la comprobación de conformidad «Long, Architectural
  Acoustics 2e, Eq. (17.54)».
- **Estado:** sin notificar (libro, no una norma, así que no normativo);
  clasificado como discrepancia de redondeo y no como defecto estructural.

## Long, Architectural Acoustics 2e (2014), Tabla 14.7 (filas de codos redondos)

- **Ubicación:** capítulo 14, Tabla 14.7, «Insertion Loss of Round Elbows»
  (p. 541 impresa), indexada por el producto frecuencia-anchura $f w$ (kHz
  por pulgadas).
- **El impreso:** solo cuatro filas: $f w < 1.9$ → 0 dB; $1.9 < f w < 3.8$ →
  1 dB; $3.8 < f w < 7.5$ → 2 dB; $f w > 15$ → 3 dB.
- **El problema:** la banda $7.5 < f w < 15$ no tiene fila alguna, así que la
  tabla salta de $3.8 < f w < 7.5$ directamente a $f w > 15$. Un cálculo por
  conductos cae en esa banda con normalidad: un codo de $24\ \text{in}$ a
  500 Hz tiene $f w = 12$.
- **Evidencia:** los mismos datos adaptados de la misma fuente ASHRAE
  aparecen en Bies, Hansen & Howard, *Engineering Noise Control* 5e, Tabla
  8.11, indexados por $W/\lambda$ ($= 0.074\,f w$). Su columna de codos
  redondos tiene seis filas, 0/1/2/3/3/3, y da 3 dB para
  $0.55 \le W/\lambda < 1.11$, que es exactamente la banda $7.5 < f w < 15$
  que Long omite. Las cuatro filas de Long se mapean sobre las seis de Bies
  así: las tres primeras coinciden entrada por entrada, la cuarta
  ($f w > 15$, 3 dB) fusiona legítimamente las dos filas superiores idénticas
  de Bies, y la banda sin fila es la cuarta de Bies. Una revisión anterior de
  esta entrada decía que «las Tablas 14.5 y 14.6 llevan ambas seis filas» y
  que «las otras cinco filas de las dos tablas coinciden entrada por
  entrada»; en la página, la Tabla 14.5 lleva seis filas y la Tabla 14.6
  cinco (fusiona las mismas dos bandas superiores idénticas, legítimamente),
  y la Tabla 14.7 imprime cuatro, así que ninguno de los dos recuentos es
  correcto. Verificado en la página 542 del PDF (p. 541 impresa) y la página
  541 del PDF (p. 540 impresa) de Long, Architectural Acoustics 2e (2014).
- **Comportamiento de la biblioteca:** `elbow_insertion_loss` en
  [`hvac.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) lleva la columna
  redonda de seis filas con 3 dB en la banda que falta, fijada por
  `test_elbow_tables_by_frequency_width_product`
  ([`tests/noise_control/test_hvac_long.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_hvac_long.py)).
- **Estado:** sin notificar (libro, no una norma).

## Long, Architectural Acoustics 2e (2014), Ec. 13.28 (unidades de U_G)

- **Ubicación:** capítulo 13, Ec. 13.28 (p. 521 impresa), el coeficiente de
  caída de presión normalizado
  $\xi = 334.9 \cdot \Delta P/(\rho_0 U_G^2)$ del modelo de potencia sonora
  de difusores.
- **El impreso:** la nomenclatura bajo la ecuación da «U_G = flow velocity
  prior to the diffuser (ft/min)» y, en la línea siguiente, «= Q/(60·S_G)
  (for Q in cfm)».
- **El problema:** las dos declaraciones se contradicen. $Q$ en $\text{ft}^3\text{/min}$
  dividido por $60 S_G$ es una velocidad en **ft/s**, no ft/min, y solo la
  lectura en ft/s hace correcta la constante: $334.9/\rho_0$ con
  $\rho_0 = 0.075\ \text{lb/ft}^3$ es $4465 \cdot \Delta P/U^2$, que es la
  relación estándar de presión de velocidad $\Delta P/(U/4005)^2$ solo cuando
  $U$ se convierte desde ft/s. Leído como ft/min el coeficiente sale 3600
  veces demasiado pequeño. La propia Ec. 13.27 declara $U_G$ en ft/s, así que
  la etiqueta «(ft/min)» bajo la Ec. 13.28 es la discordante.
- **Evidencia:** comprobación dimensional de $Q/(60 S_G)$; reconstrucción de
  la constante $334.9/\rho_0$ desde la relación de presión de velocidad; y la
  frecuencia de pico. Lo que **no** discrimina es el nivel global: la
  Ec. 13.27 lleva $30\log_{10}\xi + 60\log_{10} U_G$, y sustituir la
  Ec. 13.28 hace que la velocidad se cancele idénticamente,
  $30\log_{10}\xi + 60\log_{10} U_G = 30\log_{10}(334.9 \Delta P/\rho_0)$.
  Para el difusor de impulsión de la Tabla 14.9 ($S_G = 4\ \text{ft}^2$,
  $Q = 312$ cfm, $\Delta P = 0.05$ in w.g.) ambas lecturas devuelven por
  tanto el mismo $L_W = 45.18\ \text{dB}$. Una revisión anterior de esta
  entrada afirmaba que la lectura en ft/min «lo falla por 100 dB», cosa
  aritméticamente imposible para una cantidad que no depende de la velocidad
  en absoluto. Lo que sí discrimina es la Ec. 13.32, $f_P = 48.8 U_G$, que es
  el único otro lugar donde entra $U_G$: leída en ft/s la velocidad de
  aproximación es $1.3\ \text{ft/s}$ y el pico cae a 63.4 Hz, es decir, en la
  octava de 63 Hz, así que la forma de la Ec. 13.31 pone 33.4 dB en esa banda
  contra los 33 impresos; leída en ft/min es $78\ \text{ft/min}$, el pico se
  mueve a 3 806 Hz, y la misma forma pone -8.2 dB en la banda de 63 Hz.
  Verificado en la página 522 del PDF (p. 521 impresa) de Long, Architectural
  Acoustics 2e (2014).
- **Comportamiento de la biblioteca:** `diffuser_sound_power` en
  [`hvac.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/hvac.py) lee $U_G$ en ft/s
  internamente (SI en la interfaz), con la fila de la Tabla 14.9 fijada por
  `test_diffuser_sound_power_reproduces_the_table_14_9_row`
  ([`tests/noise_control/test_hvac_long.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_hvac_long.py))
  y la comprobación de conformidad «Long 2e Eqs. 13.27-13.33».
- **Estado:** sin notificar (libro, no una norma).

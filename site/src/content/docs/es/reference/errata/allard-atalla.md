---
title: "Erratas de Allard & Atalla (2009)"
description: "Erratas de Allard & Atalla (2009): 8 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 8 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Allard & Atalla (2009), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Allard & Atalla, Propagation of Sound in Porous Media 2e (2009), Ec. (6.85)

*Libro, no una norma.*

- **Ubicación:** sección 6.5.2 (p. 123 impresa), la segunda forma de la razón
  de velocidades de la onda de cizalla $\mu_3$.
- **El impreso:**
  $\mu_3 = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{22})$, ofrecida
  como alternativa a la Ec. (6.84), $\mu_3 = -\rho_{12}/\rho_{22}$.
- **El problema:** las dos formas impresas no son iguales. Sustituir el
  número de onda de cizalla de la Ec. (6.83),
  $\delta_3^2 = (\omega^2/N)(\rho_{11}\rho_{22} - \rho_{12}^2)/\rho_{22}$, en
  la Ec. (6.85) impresa da $-\rho_{12}^2/\rho_{22}^2$, que es la Ec. (6.84)
  multiplicada por el factor espurio $\rho_{12}/\rho_{22}$. El denominador
  debería leer $\omega^2\rho_{12}$.
- **Evidencia:** la propia deducción del libro. La Ec. (6.80), p. 122
  impresa, es
  $-\omega^2\rho_{11}\psi_s - \omega^2\rho_{12}\psi_f = N\nabla^2\psi_s = -N\delta_3^2\psi_s$,
  así que $(N\delta_3^2 - \omega^2\rho_{11})\psi_s = \omega^2\rho_{12}\psi_f$
  y por tanto
  $\mu_3 = \psi_f/\psi_s = (N\delta_3^2 - \omega^2\rho_{11})/(\omega^2\rho_{12})$.
  Con esa lectura las dos formas concuerdan idénticamente allí donde
  $\rho_{12}$ no es cero; a $\rho_{12} = 0$ el cociente corregido es $0/0$
  mientras que la Ec. (6.84) sigue definida y da
  $\mu_3 = -\rho_{12}/\rho_{22} = 0$, que es el valor a usar allí. La forma
  impresa difiere en cambio de la Ec. (6.84) en el factor
  $\rho_{12}/\rho_{22}$, así que coincide con ella solo donde esa razón es
  exactamente 0 o exactamente 1. Con
  $\rho_{12}/\rho_{22} = \rho_0/(\phi\rho_\text{eq}) - 1$ esos dos casos
  piden $\rho_\text{eq} = \rho_0/\phi$ y $\rho_\text{eq} = \rho_0/(2\phi)$,
  ambos reales; la densidad efectiva de un medio poroso con pérdidas es
  compleja, así que ninguno se cumple jamás. Verificado en la página 132 del
  PDF (p. 123 impresa) de Allard & Atalla, Propagation of Sound in Porous
  Media 2e:2009, que lleva ambas formas impresas, y en la página opuesta para
  la Ec. (6.80).
- **Comportamiento de la biblioteca:** `biot_waves` implementa la Ec. (6.84)
  tal como está impresa, y
  `test_shear_velocity_ratio_matches_the_corrected_second_printed_form` la
  comprueba contra la Ec. (6.85) corregida sobre cuatro décadas de
  frecuencia, y afirma además que la forma exactamente como está impresa
  discrepa.
- **Estado:** sin notificar.

## Allard & Atalla 2e (2009), Ec. (11.48) y Tabla 11.1 (capa poroelástica)

*Libro, no una norma.*

- **Ubicación:** sección 11.3.3 (pp. 251-252 impresas), la tensión normal del
  fluido $\sigma_{33}^f$ de una capa poroelástica y la matriz $[\Gamma]$ que
  alimenta.
- **El impreso:** la Ec. (11.48) lee

  $$
  \sigma_{33}^f = \sum_i (Q + R\mu_i)(k_t^2 + k_{i3}^2)
  \left\{ -(A_i - A'_i)\cos(k_{i3}x_3) + j(A_i - A'_i)\sin(k_{33}x_3) \right\}
  $$

  y la Tabla 11.1 escribe $k_{i3}$ en las dos columnas que llevan $\mu_1$,
  $D_1$ y $E_1$.
- **El problema:** dos erratas independientes en la misma ecuación, más un
  desliz de subíndice en la tabla.
  - Falta el coeficiente de la amplitud *simétrica* $(A_i + A'_i)$: la
    Ec. (11.48) adjunta ambos términos a $(A_i - A'_i)$, lo que dejaría la
    primera y la tercera columna de $[\Gamma]$ sin entrada alguna de
    $\sigma_{33}^f$, contradiciendo la Tabla 11.1, cuya fila 6 imprime
    $-E_1 \cos(k_{13}x_3)$ y $-E_2 \cos(k_{23}x_3)$ exactamente en esas
    columnas. El primer término es $-(A_i + A'_i)\cos(k_{i3} x_3)$.
  - El seno lleva $k_{33}$, la componente del número de onda de *cizalla*,
    dentro de una suma sobre las dos ondas de compresión $i = 1, 2$. Debe ser
    $k_{i3}$. La Tabla 11.1 da de nuevo la lectura pretendida: su fila 6
    tiene $j E_1 \sin(k_{13}x_3)$ y $j E_2 \sin(k_{23}x_3)$, y cero en ambas
    columnas de cizalla, porque una onda de cizalla no produce dilatación y
    por tanto tampoco $\sigma_{33}^f$.
  - La Tabla 11.1 imprime el subíndice corredero $k_{i3}$ en sus dos primeras
    columnas, que pertenecen a la primera onda de compresión sola: los
    $\mu_1$, $D_1$ y $E_1$ de las mismas columnas hacen de $k_{13}$ la única
    lectura consistente.
- **Evidencia:** las dos lecturas de arriba las fuerza la Tabla 11.1, que la
  misma página declara ser la tabulación de las Ecs. (11.37), (11.38) y
  (11.46)-(11.48). Son también lo que da la relación tensión-deformación
  Ec. (11.41),
  $\sigma_{33}^f = R\,\mathrm{div}\,u_f + Q\,\mathrm{div}\,u_s$, cuando los
  potenciales de desplazamiento de las Ecs. (11.22)-(11.25) se derivan
  directamente. Verificado en la página 257 del PDF (p. 251 impresa) y la
  página 258 del PDF (p. 252 impresa) de Allard & Atalla, Propagation of
  Sound in Porous Media 2e:2009, que llevan la Ec. (11.48) y las dos columnas
  de la Tabla 11.1 tal como están impresas.
- **Comportamiento de la biblioteca:** la $[\Gamma]$ de la Tabla 11.1 está
  implementada con las lecturas corregidas, y
  `test_gamma_matches_the_field_rebuilt_from_the_potentials` comprueba sus
  treinta y seis entradas a tres frecuencias, tres profundidades y tres
  ángulos de incidencia contra el campo reconstruido desde las
  Ecs. (11.22)-(11.28) sin pasar por la tabla.
- **Estado:** sin notificar.

## Allard & Atalla 2e (2009), sección 6.6.3 (espesor de la segunda muestra)

*Libro, no una norma.*

- **Ubicación:** sección 6.6.3, p. 129 impresa, las dos muestras de lana de
  vidrio cuyas impedancias de superficie medidas y predichas son las Figuras
  6.10 y 6.11.
- **El impreso:** la primera frase dice que las impedancias se muestran «for
  l = 10 cm and l = 5.4 cm»; dos frases después el pico de la segunda muestra
  se sitúa a «860 Hz for l = 5.6 cm», y el pie de la Figura 6.11 dice «l =
  5.6 cm».
- **El problema:** los dos espesores no pueden estar bien a la vez.
- **Evidencia:** textual, y solo textual. Dos declaraciones impresas llevan
  5.6 cm, la frase del pico de 860 Hz y el pie independiente de la Figura
  6.11, contra una que lleva 5.4 cm; un solo desliz en la frase inicial es la
  explicación más corta que el mismo desliz cometido dos veces. Los números
  **no** lo zanjan, y esta entrada no pretende que lo hagan. El libro no da
  regla de localización de picos, y la respuesta sigue a la regla elegida:
  - Tomando el pico como el máximo de $\text{Im}(Z_s)$, la Ec. (6.107) sobre
    la lana de vidrio de la Tabla 6.1, completamente especificada, da
    863.5 Hz para 5.6 cm (+0.4 % contra los 860 impresos) y 896.2 Hz para
    5.4 cm (+4.2 %), lo que favorece 5.6 cm. Pero la misma regla sitúa la
    muestra indiscutida de 10 cm a 480.0 Hz contra sus 470 impresos, un sesgo
    de +2.1 % del mismo tamaño que el efecto que se resuelve.
  - Tomando el pico como el máximo de $|Z_s - Z_{s,\text{rigid}}|$, que es la
    desviación que el mismo párrafo describe («close to each other, except
    around the peaks which are not predicted by the one-wave model»), la
    muestra de 10 cm aterriza a 469.2 Hz (-0.2 %) y **ambas** frecuencias
    impresas salen entonces del par (10 cm, 5.4 cm): 861.2 Hz para 5.4 cm
    (+0.1 %) contra 831.0 Hz para 5.6 cm (-3.4 %). Esa regla favorece 5.4 cm.
  - Escalar el pico de 10 cm tampoco ayuda, y se inclina al lado contrario de
    la conclusión: $470 \times (10/5.4) = 870\ \text{Hz}$ está a 10 Hz de los
    860 publicados, $470 \times (10/5.6) = 839\ \text{Hz}$ a 21 Hz.
  - La concordancia de «860 Hz» con «5.6 cm» es en todo caso parcialmente
    circular, ya que ambos están en la misma cláusula: contrasta esa frase
    contra sí misma, no cuál de las dos frases es la errata.
  Verificado en la página 138 del PDF (p. 129 impresa) de Allard & Atalla,
  Propagation of Sound in Porous Media 2e:2009, en la que el 5.4 cm solitario
  y el 5.6 cm de la cláusula de 860 Hz están en la misma página, y en la
  página 139 del PDF (p. 130 impresa) de la misma edición para el pie de la
  Figura 6.11, la segunda frase que lleva 5.6 cm.
- **Comportamiento de la biblioteca:** registrado, sin efecto en la
  implementación.
  `test_impedance_peak_of_the_thin_layer_resolves_the_printed_thickness`
  fija el pico de 5.6 cm contra los 860 Hz publicados bajo la regla de
  $\text{Im}(Z_s)$ y comprueba que la lectura de 5.4 cm es la peor de las dos
  bajo esa regla.
- **Estado:** sin notificar, y la más débil de las cuatro entradas de aquí:
  la conclusión descansa en la lectura dos-contra-uno de la página impresa,
  no en un cálculo.

## Allard & Atalla 2e (2009), sección 6.5.4 (la razón de velocidades de la onda del esqueleto)

*Libro, no una norma.*

- **Ubicación:** sección 6.5.4, p. 125 impresa, la única frase del libro que
  cita valores calculados de $\mu_b$ para la lana de vidrio de la Tabla 6.1.
- **El impreso:** «The ratio modulus $|\mu_b|$ of the velocities of the frame
  and the air for the frame-borne wave decreases from 1.0 at 50 Hz to 0.82 at
  1500 Hz.»
- **El problema:** los dos valores citados son la *parte real* de $\mu_b$, no
  su módulo. $\mu_b$ es complejo, y la frase nombra el módulo
  explícitamente.
- **Evidencia:** sobre el material de la Tabla 6.1, completamente
  especificado, el modelo da $\mu_b(1500\ \text{Hz}) = 0.811 + 0.473j$. Su
  parte real es **0.811**, a 1.1 % del 0.82 impreso; su módulo es **0.939**,
  a 14.5 %. Leída como la parte real, la frase acierta en ambos extremos y
  describe un descenso monótono: $\text{Re}(\mu_b)$ es 1.002 a 50 Hz y pasa
  por 0.82 a 1467 Hz, a 2.2 % de los 1500 Hz impresos. Leída como el módulo
  no acierta en ninguno: $|\mu_b|$ es 1.002 a 50 Hz pero *sube* a 1.008 hacia
  400 Hz antes de darse la vuelta, y solo alcanza 0.82 a 2634 Hz, un 76 % por
  encima de la frecuencia impresa. Ninguna lectura admisible de las entradas
  impresas cierra esa brecha. Con el factor de pérdida a 0 o a 0.2, la
  longitud viscosa a la mitad o al doble, $\Lambda' = 2\Lambda$ en lugar del
  $1.1 \cdot 10^{-4}\ \text{m}$ impreso, la resistividad a la mitad o al
  doble, la tortuosidad a 1 o el coeficiente de Poisson a 0.3,
  $|\mu_b(1500)|$ se mueve solo entre 0.874 y 1.073. La más cercana de las
  ocho, 0.874 a factor de pérdida cero, sigue a 6.6 % del 0.82 impreso, y
  pierde por completo el cruce de ramas a 495 Hz de la misma sección; la
  única variante que conserva ese cruce ($\Lambda' = 2\Lambda$, 495.2 Hz)
  deja $|\mu_b|$ en 0.937. Leer la frase como $\text{Re}(\mu_b)$ no necesita
  variante alguna. Verificado en la página 134 del PDF (p. 125 impresa) de
  Allard & Atalla, Propagation of Sound in Porous Media 2e:2009, que lleva la
  frase y su 0.82.
- **Comportamiento de la biblioteca:** `biot_waves` calcula $\mu_b$ desde la
  Ec. (6.71) tal como está impresa. La fila de conformidad y
  `test_frame_borne_velocity_ratio_matches_the_two_published_values` están
  escritas contra $\text{Re}(\mu_b)$, y lo dicen.
- **Estado:** sin notificar.

## Allard & Atalla 2e (2009), Tabla 11.7 (la figura que nombra su pie)

*Libro, no una norma.*

- **Ubicación:** Tabla 11.7, página 280 del PDF, p. 274 impresa, la tabla de
  parámetros de la moqueta, la pantalla y la capa fibrosa de la sección
  11.7.2.
- **El impreso:** el pie dice «The parameters used to predict the surface
  impedance of the material represented in Figure 11.6».
- **El problema:** la Figura 11.6 está en la p. 266 impresa y es la espuma
  plástica bajo una lámina de lana de vidrio, cuyos parámetros son la Tabla
  11.3. La estructura que tabula la Tabla 11.7, una moqueta en dos capas sobre
  una pantalla impermeable sobre una capa fibrosa, es la Figura 11.16,
  impresa en la misma página que la tabla.
- **Evidencia:** el texto junto a la Figura 11.16 dice que los parámetros del
  material están en la Tabla 11.7, y los cuatro nombres de fila de la tabla
  son las cuatro capas que etiqueta la Figura 11.16. Verificado en la página
  280 del PDF (p. 274 impresa) y en la página 272 del PDF (p. 266 impresa) de
  Allard & Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** las tres filas porosas se transcriben
  tal como están impresas y el `about` del fichero de datos nombra la Figura
  11.16 como la estructura, citando la redacción del pie.
- **Estado:** sin notificar.

## Allard & Atalla 2e (2009), Tabla 11.8 (el espesor de la lana de vidrio)

*Libro, no una norma.*

- **Ubicación:** Tabla 11.8, página 281 del PDF, p. 275 impresa, la lana de
  vidrio pegada a una placa de aluminio del ejemplo de transmisión a
  incidencia normal de la sección 11.7.3.
- **El impreso:** la tabla da a la lana de vidrio un espesor de 3,8 mm; el
  texto de la sección 11.7.3, en el folio de al lado, dice «A layer of the
  glass wool studied in Section 6.5.4, of thickness 5 cm, is bonded on to a
  plate of aluminium, of thickness 1 mm».
- **El problema:** los dos espesores difieren en más de un orden de magnitud y
  no pueden describir los dos la capa de la Figura 11.18.
- **Evidencia:** la placa sí concuerda entre ambos, 1 mm en los dos, que es lo
  que sitúa la discrepancia en la celda de la lana de vidrio y no en una
  columna leída fuera de orden. Verificado en la página 281 del PDF (p. 275
  impresa) para la tabla y en la página 280 del PDF (p. 274 impresa) para la
  frase, en Allard & Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** la fila lleva los 3,8 mm impresos y su
  `note` registra la frase. Nada calcula con el espesor: el fluido equivalente
  de esta probeta no lo usa.
- **Estado:** sin notificar.

## Allard & Atalla 2e (2009), Tabla 11.9 (el espesor de la placa)

*Libro, no una norma.*

- **Ubicación:** Tabla 11.9, página 282 del PDF, p. 276 impresa, la espuma y
  la placa del ejemplo de transmisión en campo difuso de la sección 11.7.4.
- **El impreso:** la fila de la placa da un espesor de 1,6 mm; el texto de la
  sección 11.7.4, en el folio de al lado, dice «The material is a foam of
  thickness h = 2 . 54 cm bonded onto a 0.6 mm aluminium plate».
- **El problema:** 1,6 frente a 0,6 mm para la misma placa.
- **Evidencia:** la espuma sí concuerda entre ambos, los 25,4 mm de la tabla
  son los 2,54 cm de la frase, lo que deja la discrepancia sólo en la fila de
  la placa. Verificado en la página 282 del PDF (p. 276 impresa) para la tabla
  y en la página 281 del PDF (p. 275 impresa) para la frase, en Allard &
  Atalla, Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** la placa no es un material poroso y no
  está en el catálogo; la `note` de la fila de la espuma registra la
  discrepancia para que quien reproduzca la figura sepa qué placa supone la
  curva.
- **Estado:** sin notificar.

## Allard & Atalla 2e (2009), Tabla 13.2 (el módulo de Young de la lana de roca)

*Libro, no una norma.*

- **Ubicación:** Tabla 13.2, página 341 del PDF, p. 337 impresa, la lana de
  roca de 5,75 cm con una perforación central del ejemplo de doble porosidad.
- **El impreso:** la columna encabezada E (Pa) lleva 4400 para un esqueleto de
  130 kg/m3.
- **El problema:** un módulo de esqueleto de 4,4 kPa a esa densidad da una
  velocidad de onda en el esqueleto de $\sqrt{4400/130} = 5,8$ m/s, así que la
  resonancia de cuarto de onda de una capa de 5,75 cm cae cerca de 25 Hz. El
  texto de la página siguiente dice que el modelo numérico captura «the
  skeleton resonance occurring around 1350 Hz», que el módulo impreso no puede
  producir: 1350 Hz pedirían unos 12,7 MPa, tres órdenes de magnitud por
  encima de la celda.
- **Evidencia:** aritmética sobre las dos celdas de la propia página contra la
  propia frase de la página. Nada en la página dice cuál debería ser el
  módulo, así que esta entrada informa de la incoherencia y no la repara.
  Verificado en la página 341 del PDF (p. 337 impresa) para la tabla y en la
  página 342 del PDF (p. 338 impresa) para la frase, en Allard & Atalla,
  Propagation of Sound in Porous Media 2e:2009.
- **Comportamiento de la biblioteca:** la fila lleva los 4400 Pa impresos y su
  `note` registra la resonancia que informa el texto. Ningún ejemplo de esta
  biblioteca calcula una resonancia de esqueleto a partir de él.
- **Estado:** sin notificar.

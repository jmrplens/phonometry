---
title: "Erratas de Bies, Hansen & Howard (2017)"
description: "Erratas de Bies, Hansen & Howard (2017): 4 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: ""
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 4 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre Bies, Hansen & Howard (2017), en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Bies, Hansen & Howard, Engineering Noise Control 5e (2017), Ec. (8.141)

- **Ubicación:** sección 8.9.1, Ec. (8.141) (p. 461 impresa), la pérdida de
  transmisión de un silenciador desde los elementos de su matriz de cuatro
  polos total.
- **El impreso:**
  $$
  TL = 10 \lg\left[ \left(\frac{1+M_n}{1+M_1}\right)^2 \cdot \tfrac{1}{4} \cdot
  \left| \frac{Z_{A1}}{Z_{An}} T_{11} + \frac{T_{12}}{Z_{An}}
  + Z_{A1} T_{21} + \frac{Z_{An}}{Z_{A1}} T_{22} \right|^2 \right],
  $$
  es decir, con la razón de impedancias $Z_{A1}/Z_{An}$ ponderando $T_{11}$ y
  su inversa ponderando $T_{22}$.
- **El problema:** la fuente que la propia ecuación cita (Munjal, *Acoustics
  of Ducts and Mufflers* 2e, Ec. (3.27), p. 105) lleva el prefactor global
  $Z_{An}/Z_{A1}$ (equivalentemente $\sqrt{S_1/S_n}$ dentro de una forma en
  $20\log_{10}$) con $T_{11}$ sin ponderar y $Z_{A1}/Z_{An}$ sobre $T_{22}$.
  Tal como está impresa, la Ec. (8.141) falla el límite de expansión brusca:
  un elemento de longitud cero ($T = I$) entre $S_1 = 0.01\ \text{m}^2$ y
  $S_n = 0.02\ \text{m}^2$ es una expansión brusca de área con el clásico
  $TL = 10\log_{10}[(1+m)^2/(4m)] = 0.512\ \text{dB}$ ($m = S_n/S_1 = 2$),
  pero la ecuación impresa da
  $\tfrac{1}{4} \cdot (Z_{A1}/Z_{An} + Z_{An}/Z_{A1})^2 = 1.938\ \text{dB}$.
  Leer las razones como un prefactor global $Z_{A1}/Z_{An}$ también está mal:
  da 6.532 dB sobre el mismo oráculo y viola la reciprocidad ($11.34$ contra
  -0.70 dB para una cámara de expansión entre tubos desiguales; una TL
  negativa para un elemento pasivo). La errata es invisible siempre que las
  áreas de entrada y salida son iguales, donde todas las variantes se reducen
  a la Ec. (8.148).
- **Evidencia:** evaluación numérica del elemento identidad de longitud cero
  y de una cámara de expansión de puertos desiguales bajo la forma impresa,
  el prefactor invertido y la Ec. (3.27) de Munjal; solo la forma de Munjal
  reproduce el clásico de la expansión brusca (0.512 dB, en ambos sentidos) y
  es recíproca.
- **Comportamiento de la biblioteca:** `transmission_loss` en
  [`silencers.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/noise_control/silencers.py) implementa
  la Ec. (3.27) de Munjal, con el límite de expansión brusca y la
  reciprocidad de la TL fijados por tests de regresión
  ([`tests/noise_control/test_silencers.py`](https://github.com/jmrplens/phonometry/blob/main/tests/noise_control/test_silencers.py))
  y una nota defensiva junto a la fórmula.
- **Estado:** sin notificar (libro, no una norma).

## Bies 5e (2017), Tabla C.1 (tres velocidades que no se siguen de las dos columnas de las que dice calcularlas)

- **Localización:** Tabla C.1, "Properties of materials", las filas "Brick" y
  "Cork" de la página impresa 719 (página PDF 748) y "Plywood (fir)" de la
  página impresa 720 (página PDF 749), frente al texto de la página impresa 717
  (página PDF 746). Fuente no normativa: un libro de texto.
- **Lo impreso:** la página 717 dice "The speed of sound values in column 4 of
  Table C.1 were calculated from the values in columns 2 and 3", que son el
  módulo de Young en $10^9$ N/m2 y la densidad en kg/m3. Las tres filas dan, en
  ese orden, $E$ = 24 y $\rho$ = 2000 con una velocidad de 3650 m/s; $E$ = 0,1
  y $\rho$ = 250 con 500 m/s; y $E$ = 8,3 y $\rho$ = 600 con 4540 m/s.
- **El problema:** $\sqrt{E/\rho}$ sobre esas celdas da 3464, 632 y 3719 m/s.
  Las velocidades impresas quedan un 5,4 por ciento por encima, un 20,9 por
  ciento por debajo y un 22,1 por ciento por encima de lo que dan las dos
  columnas que tienen al lado.
- **Evidencia:** la misma expresión reproduce el resto de la tabla. De las
  ochenta y siete filas que imprimen el módulo y la densidad como valores
  únicos, setenta y nueve coinciden dentro del 1 por ciento y ochenta y cuatro
  dentro del 3, con una desviación mediana del 0,03 por ciento, y a lo largo de
  velocidades de 190 a 27000 m/s. Sólo estas tres se salen, que es la firma de
  una celda mal impresa y no la de un método más flojo que el que describe la
  página. Cuál de las celdas está mal no se puede saber desde la página: 4540
  m/s saldría de un módulo de 12,4 en vez de 8,3, y 500 m/s de una densidad de
  400 en vez de 250. Verificado contra la página tal como se imprime en las
  páginas PDF 748 y 749 (páginas impresas 719 y 720) de Bies, Hansen y Howard
  (2017), *Engineering Noise Control*, quinta edición.
- **Consecuencia para las tablas del propio libro:** tres celdas. Ninguna otra
  parte del documento calcula con ellas.
- **Comportamiento de la biblioteca:** el catálogo guarda las tres columnas tal
  como se imprimen y no deriva nada por encima, y cada una de las tres filas
  lleva la discrepancia en su nota. La prueba
  `test_three_rows_do_not_follow_from_their_own_two_columns` de
  [`tests/solids/test_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/solids/test_catalogue.py) fija
  las tres, y `test_the_rest_of_the_table_reproduces_to_three_per_cent` fija
  las ochenta y cuatro que sí se siguen, que es lo que convierte a las tres en
  un defecto.
- **Estado:** no reportado.

## Bies 5e (2017), Tabla C.2 (cuatro masas molares que no son las de la molécula de su fila)

- **Localización:** Tabla C.2, "Molecular weights and ratios of specific heats
  for some commonly used gases", las filas "Ammonia", "Fluorine", "Freon 22" y
  "Nitric oxide" de la página impresa 722 (página PDF 751). Fuente no
  normativa: un libro de texto.
- **Lo impreso:** las cuatro filas dan, en la columna encabezada "Molecular
  weight, $M$ kg/mole", 0.01730, 0.01900, 0.08047 y 0.06301.
- **El problema:** la masa molar de un gas se sigue de la molécula que nombra
  la fila, y ninguna de las cuatro lo hace. El amoniaco es NH$_3$, 17.031
  g/mol, no 17.30. El flúor gas es F$_2$, 37.996 g/mol, y 19.00 es la masa
  atómica de un solo átomo de flúor. El Freón 22 es CHClF$_2$, 86.465 g/mol, no
  80.47. El óxido nítrico es NO, 30.006 g/mol, y 63.01 es la masa molar del
  *ácido* nítrico, HNO$_3$.
- **Evidencia:** el resto de la tabla es lo que decide que son erratas y no una
  convención más suelta. Treinta y cinco de las treinta y siete filas nombran
  una molécula cuya masa de fórmula se puede calcular; las dos que no son las
  dos mezclas, el aire y el gas natural. De esas treinta y cinco, treinta y una
  reproducen su masa de fórmula por debajo del 0,05 por ciento, y las dos que
  se salen más se salen sólo por el redondeo de la página: el helio, 4.00
  frente a 4.0026, queda un 0,07 por ciento por debajo, y el hidrógeno, 2.02
  frente a 2.016, un 0,20 por ciento por encima, las dos en el último dígito
  impreso. Así que la precisión de la propia tabla es de dos partes por mil, y
  frente a eso las cuatro excepciones se salen un 1,6, un 6,9, un 50 y un 110
  por ciento. Dos de ellas caen exactamente sobre otra especie, que es la
  forma que tiene un salto de copia: 19.00 es el flúor atómico con un error del
  0,01 por ciento y 63.01 es HNO$_3$ con uno del 0,003 por ciento, la misma
  exactitud que tienen las filas correctas. La relación de calores específicos
  que va al lado de cada una apunta en la misma dirección: 1.36 para el flúor y
  1.40 para el óxido nítrico son valores de gas diatómico, así que las filas
  hablan de F$_2$ y de NO diga lo que diga su columna de masa. Una tabla
  independiente del mismo género coincide en las dos cosas: el *Control Valve
  Sizing Handbook* de Masoneilan (Baker Hughes, BHMN-19540C, 2022), que tabula
  las mismas dos magnitudes para el mismo fin, imprime "Fluorine, F$_2$" con
  una relación de calores específicos de 1.36 en su página 19 y "Ammonia,
  NH$_3$" con un peso molecular de 17.0 en su página 20. Verificado contra la
  página tal como se imprime en la página PDF 751 (página impresa 722) de Bies,
  Hansen y Howard (2017), *Engineering Noise Control*, quinta edición, y en las
  páginas 19 y 20 del manual de Masoneilan.
- **Consecuencia para las tablas del propio libro:** cuatro celdas. Ninguna
  otra parte del documento calcula con ellas; la tabla se ofrece para el ruido
  de válvula de control de la Sección 10.8, donde el gas lo elige quien lee.
  Quien sí tomara una de las cuatro obtendría una velocidad del sonido un 0,8
  por ciento baja para el amoniaco, un 3,7 por ciento alta para el Freón 22, un
  41,4 por ciento alta para el flúor y un 31,0 por ciento baja para el óxido
  nítrico, ya que $c = \sqrt{\gamma R T / M}$.
- **Comportamiento de la biblioteca:** el catálogo guarda la fila y su relación
  de calores específicos, y rechaza la masa molar en vez de servirla: leerla
  levanta un error que nombra la celda, cita lo que imprime la página y apunta
  aquí. Las pruebas `test_a_cell_the_errata_names_is_not_served_as_a_value` y
  `test_the_refusal_quotes_the_printed_number_and_points_at_the_registry` de
  [`tests/fluids/test_gas_catalogue.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas_catalogue.py)
  fijan las dos mitades, y `test_no_other_cell_of_either_table_is_called_wrong`
  impide que la acusación se extienda a una quinta fila.
- **Estado:** no reportado.

## Bies 5e (2017), Tabla C.2 (dos relaciones de calores específicos que ningún gas puede tener)

- **Localización:** Tabla C.2, "Molecular weights and ratios of specific heats
  for some commonly used gases", las filas "Hydrogen fluoride" y "Octane" de la
  página impresa 722 (página PDF 751). Fuente no normativa: un libro de texto.
- **Lo impreso:** la columna encabezada "Ratio of specific heats, $\gamma$" da
  0.97 para el fluoruro de hidrógeno y 1.66 para el octano.
- **El problema:** la columna es la relación de calores específicos, que es lo
  que dice su propio encabezado y lo que la tabla existe para alimentar en el
  procedimiento de ruido de válvula al que apunta el apéndice, "particularly
  useful for calculating control valve noise (see Section 10.8)". Para
  cualquier sustancia en una sola fase estable $c_p \geq c_v$, así que
  $\gamma \geq 1$ y un 0.97 impreso queda fuera de lo que la magnitud puede
  ser. Eso es una afirmación sobre $c_p/c_v$ y no sobre cualquier exponente que
  alguien escriba $k$: el exponente isentrópico de gas real de un vapor que se
  asocia con fuerza, que es lo que es el fluoruro de hidrógeno, sí puede bajar
  de 1, pero es otra magnitud distinta de la que nombra esta columna y no es la
  que quiere el procedimiento de después. La celda del octano queda fuera de la
  columna por el otro lado: para un gas ideal $\gamma = 1 + 2/f$, donde $f$
  cuenta los grados de libertad activos, y $f \geq 3$ siempre, así que
  $\gamma \leq 5/3 \approx 1.667$ con igualdad sólo para uno monoatómico. El
  octano es C$_8$H$_{18}$, veintiséis átomos, con tres grados de libertad de
  rotación además de los tres de traslación antes de contar ninguna vibración,
  lo que lo deja en $\gamma \leq 4/3$ y en la práctica cerca de 1.05. Esa cota
  es de gas ideal, y un fluido real sí pasa de 5/3 cerca de su punto crítico;
  lo que descarta leer la celda así es que ésta es una columna de gas ideal,
  impresa contra masas molares ideales, que da un valor por gas y no uno por
  estado.
- **Evidencia:** la columna es por lo demás una función limpia de la
  complejidad molecular, que es lo que hace visibles las dos excepciones. Los
  tres gases monoatómicos imprimen de 1.64 a 1.67, los diatómicos de 1.31 a
  1.41, y los poliatómicos van cayendo con el tamaño hasta 1.05. Los dos
  vecinos del octano en esa progresión están en la misma tabla y a un carbono
  de distancia: el n-heptano imprime 1.05 y el pentano 1.06, así que la propia
  tabla dice lo que hace un alcano de ese tamaño. Los vecinos del fluoruro de
  hidrógeno son las demás filas diatómicas, y el cloruro de hidrógeno, el
  haluro siguiente, imprime 1.41. Fuera del libro, el *Control Valve Sizing
  Handbook* de Masoneilan (Baker Hughes, BHMN-19540C, 2022) imprime 1.05 para
  el octano en esa misma columna de $c_p/c_v$ en su página 19, entre el 1.66
  del helio y el 1.07 del pentano, así que la progresión no es la costumbre de
  un solo autor. Verificado contra la página tal como se imprime en la página
  PDF 751 (página impresa 722) de Bies, Hansen y Howard
  (2017), *Engineering Noise Control*, quinta edición, releyendo las dos celdas
  a seis aumentos: 0.97 y 1.66 son lo que imprime la página, sin ningún dígito
  en duda.
- **Consecuencia para las tablas del propio libro:** dos celdas. Quien tomara
  la fila del octano obtendría una velocidad del sonido un 26,0 por ciento
  alta; la del fluoruro de hidrógeno no se puede usar en absoluto, porque una
  velocidad del sonido calculada con una $\gamma$ menor que 1 no es la
  velocidad de nada.
- **Comportamiento de la biblioteca:** el catálogo guarda la fila y su masa
  molar, y rechaza la relación en vez de servirla, igual y con el mismo mensaje
  que las cuatro masas molares de arriba. La guardia independiente es
  [`phonometry.fluids.ideal_gas`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/fluids/gas.py), que rechaza
  una relación igual o menor que 1 se la pase quien se la pase, y
  `test_a_ratio_of_specific_heats_at_or_below_one_is_refused` de
  [`tests/fluids/test_gas.py`](https://github.com/jmrplens/phonometry/blob/main/tests/fluids/test_gas.py) lo fija.
- **Estado:** no reportado.

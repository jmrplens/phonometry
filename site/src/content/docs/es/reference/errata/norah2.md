---
title: "Erratas de la guía de rotorcraft NORAH2"
description: "Erratas de la guía de rotorcraft NORAH2: 8 defectos del texto impreso, con la evidencia y lo que hace phonometry con cada uno."
searchTitle: "Erratas"
---

<!-- Generated from docs/ERRATA.es.md by scripts/generate_site_reports.py (`make site-reports`). Edit the source document, never this page. -->

Estas son las 8 entradas del [registro de erratas](/phonometry/es/reference/errata/) sobre la guía de rotorcraft NORAH2, en el orden en que las recoge el registro. La introducción del registro explica cómo se comprueba cada afirmación contra la página impresa y qué significa el estado de una entrada. La redacción autoritativa es la inglesa; las citas textuales, las matemáticas y los valores impresos se reproducen sin traducir.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), Ec. (27)

- **Ubicación:** sección A.4.2, Ec. (27) (coeficiente de absorción
  atmosférica) y la frase que define sus símbolos, p. 21 impresa.
- **El impreso:** la Ec. (27) empareja el coeficiente
  $6.6928 \cdot 10^{-6}$ con $f_{rO}$ y $1.3415 \cdot 10^{-6}$ con $f_{rN}$,
  y la frase de debajo lee «the variables f_rN = 75692 Hz and f_rO = 630.7 Hz
  represent the vibrational relaxation frequencies of oxygen and nitrogen
  respectively».
- **El problema:** los dos subíndices están intercambiados en la frase de
  definición. Los *valores* casan con los *nombres* que les da (75 692 Hz es
  la frecuencia de relajación del oxígeno y 630.7 Hz la del nitrógeno en las
  condiciones de referencia), pero están asignados a los símbolos opuestos,
  así que la ecuación tal como está impresa multiplica el coeficiente del
  oxígeno por la frecuencia de relajación del nitrógeno y viceversa. Evaluada
  así da 14.2 dB/km a 500 Hz contra el valor de 3.1 dB/km de la propia Tabla
  4 de la guía; con $f_{rO}$ y $f_{rN}$ intercambiados da 3.07 dB/km,
  reproduciendo la Tabla 4 y el coeficiente de tono puro de ISO 9613-1 a
  0.02 dB/km. Una revisión anterior de esta entrada citaba el valor impreso
  como 14.3 dB/km y planteaba el defecto como un emparejamiento erróneo de
  los coeficientes y no como subíndices intercambiados en la definición.
- **Evidencia:** evaluación numérica de la Ec. (27) con la asignación impresa
  y con la asignación intercambiada, contra la celda de 500 Hz de la Tabla 4
  de la misma página. Verificado en la página 20 del PDF (p. 21 impresa) de
  NORAH2 SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** implementa el emparejamiento correcto;
  el docstring del módulo lleva una nota defensiva para que la errata no se
  transcriba como «arreglo».
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), Ec. (21)

- **Ubicación:** sección A.3.3, Ec. (21) (ángulo de la trayectoria de vuelo).
- **El impreso:** $\gamma = \text{acos}(\Delta Z/\Delta S)$.
- **El problema:** el arcocoseno de la razón de ascenso a trayectoria
  devuelve el complemento del ángulo de trayectoria ($90^\circ$ en vuelo
  nivelado, donde $\gamma$ debe ser $0^\circ$) y contradice el propio uso de
  $\gamma$ como ángulo de ascenso/descenso en toda la sección A.3. El Doc 32
  de la CEAC, 1.ª ed., Ec. (10), imprime la forma correcta,
  $\gamma = \text{atan}(\Delta Z/\Delta S)$ con el $\Delta S$ horizontal de
  su Ec. (8).
- **Evidencia:** evaluación en vuelo nivelado; contraste contra la Ec. (10)
  del Doc 32 y contra los ficheros de entrada del prototipo NORAH2, cuyas
  columnas ``Vang`` son ángulos de ascenso/descenso ($0^\circ$ en segmentos
  nivelados).
- **Comportamiento de la biblioteca:** ``flight_path_kinematics`` implementa
  la forma ``atan`` del Doc 32; el docstring del resultado lleva la nota
  defensiva.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), triangulación del §A.3.1

- **Ubicación:** sección A.3.1, pasos 2 a 4 (interpolación de condiciones de
  vuelo), contra las tablas de consulta de triangulación distribuidas con la
  base de datos NORAH2 (``*_triangulation.int``).
- **El impreso:** los pasos 2 y 3 normalizan las condiciones de la base de
  datos (rangos, con $F_{fc} = 2$ en el ángulo de trayectoria) y el paso 4
  calcula «the Delaunay triangulation for the database flight conditions
  γ̄_j and V̄_j», es decir, la de los puntos normalizados, ofreciendo una
  tabla de consulta como equivalente.
- **El problema:** las tablas de consulta distribuidas con la base de datos
  (que la guía dice que forman parte de los datos de hemisferios y no deben
  editarse) son la triangulación de Delaunay de las condiciones $(V, \gamma)$
  brutas, no de las normalizadas: para el conjunto del R22, 14 de los 27
  triángulos distribuidos difieren de la triangulación de Delaunay de las
  condiciones normalizadas. Una triangulación de Delaunay no es invariante
  bajo la normalización anisótropa, así que las dos prescripciones
  seleccionan triángulos envolventes distintos para parte de la envolvente.
  Los pesos de distancia de las Ecs. (7)/(8) sí usan las coordenadas
  normalizadas en el prototipo (verificado contra sus salidas mezcladas).
- **Evidencia:** recálculo de ambas triangulaciones para la base de datos del
  R22; reproducción bin a bin de la selección de hemisferios por paso del
  prototipo con las tablas distribuidas, y de sus niveles mezclados con pesos
  en el espacio normalizado, a 0.05 dB.
- **Comportamiento de la biblioteca:** ``flight_condition_weights`` sigue el
  método impreso (Delaunay de las condiciones normalizadas) por defecto y
  acepta la tabla de consulta de la base de datos vía ``triangles``, que
  reproduce la implementación de referencia exactamente.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), Ec. (46)

- **Ubicación:** sección A.4.5, Ec. (46) (efecto de suelo del lado de la
  fuente ponderado por la difracción).
- **El impreso:** el exponente de ponderación lee
  $(\Delta L_{g,s'} - \Delta L_{d,s})/20$.
- **El problema:** no existe término alguno $\Delta L_{g,s'}$; la prosa
  justo debajo de la ecuación define $\Delta L_{d,s'}$ como «the attenuation
  due to the diffraction between the image source S′ and R», la Ec. (47)
  compañera del lado del receptor imprime el término paralelo correctamente
  como $\Delta L_{d,r'}$, y el método CNOSSOS-EU en el que se basa la sección
  escribe $\Delta_\text{ground}(S,O)$ con $\Delta_\text{dif}(S',R)$ en esa
  posición. El subíndice $g$ es una errata por $d$.
- **Evidencia:** consistencia interna de la sección (su propia prosa y la
  Ec. (47)) y la fuente CNOSSOS-EU de las ecuaciones.
- **Comportamiento de la biblioteca:** implementa el término de difracción de
  la fuente imagen $\Delta L_{d,s'}$ tal como lo define la prosa.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), referencias cruzadas del §A.4.5

- **Ubicación:** sección A.4.5, las definiciones bajo la Ec. (46) (p. 32
  impresa) y la Ec. (47) (p. 33 impresa).
- **El impreso:** cuatro referencias cruzadas a la eq. 44, en **tres**
  redacciones distintas: «calculated as per eq. 44» para $\Delta L_{d,s'}$ y
  de nuevo para $\Delta L_{d,s}$ bajo la Ec. (46); «calculated as in eq. 44»
  para $\Delta L_{d,r'}$ bajo la Ec. (47); y «calculated as in Subsection
  eq. 44» para $\Delta L_{d,s}$ bajo la Ec. (47). Una revisión anterior de
  esta entrada citaba las cuatro con la primera redacción.
- **El problema:** la Ec. (44) es el coeficiente de difracción múltiple
  $C''$; la atenuación por difracción es la Ec. (42). Las cuatro referencias
  cruzadas apuntan al coeficiente auxiliar en lugar de a la fórmula que
  describen, y la cuarta lleva además un «Subsection» colgado sin número de
  subsección detrás.
- **Evidencia:** los términos son atenuaciones en dB, que solo produce la
  Ec. (42); la Ec. (44) es un coeficiente adimensional que consume la
  Ec. (42). Verificado en las páginas 31 y 32 del PDF (pp. 32 y 33 impresas)
  de NORAH2 SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** evalúa los términos de difracción del
  camino imagen y directo con la Ec. (42), usando la Ec. (44) para $C''$
  dentro de ella.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), §A.3.5 Approach 3 (base del ralentí a régimen pleno)

- **Ubicación:** sección A.3.5, Approach 3, paso 3 (p. 18 impresa), contra la
  fila «Fl. idle» de la Tabla 3 (pp. 18-19 impresas).
- **El impreso:** el paso lee «add offset of 12 dB\* to derive out of ground
  hover from the in-ground hover disk, -12 dB\* to derive reduced-rpm idle
  from in-ground hover disk, and -2.5 dB\* to derive full-rpm idle from out
  of ground hover»; la tabla imprime
  $LA_{\mathrm{FL.idle}}(\theta) = LA_{\mathrm{HIGE}}(\theta) - 2.5\ \mathrm{dB}^*$.
- **El problema:** la prosa deriva el ralentí a régimen pleno del
  estacionario fuera del efecto suelo donde la tabla lo deriva del
  estacionario en efecto suelo, y las dos prescripciones caen a 12 dB una de
  otra (por la prosa,
  $LA_{\mathrm{HOGE}}(\theta) - 2.5 = LA_{\mathrm{HIGE}}(\theta) + 9.5$; por
  la tabla, $LA_{\mathrm{HIGE}}(\theta) - 2.5$). Solo la tabla conserva el
  orden físico de las condiciones (ralentí a régimen pleno por encima del
  ralentí a régimen reducido, ambos por debajo del estacionario en efecto
  suelo). El párrafo que introduce estas fases, al final de la sección A.3.3
  (p. 17 impresa), está él mismo sin terminar («For specific phases of a
  flight such as, turns, hover, taxiing»), apuntando a una pasada de edición
  que la sección no recibió.
- **Evidencia:** las correcciones distribuidas con la base de datos pública
  V2.0.74 son todas relativas al disco de estacionario en efecto suelo
  (`Fullrpmidle -2` en el fichero de consulta de interpolación de todos los
  tipos), concordando con la tabla y no con la prosa. Verificado en las
  páginas 16, 17 y 18 del PDF (pp. 17, 18 y 19 impresas) de NORAH2
  SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** `hover_derived_hemisphere` aplica
  todos los desplazamientos de la Tabla 3 desde el hemisferio de estacionario
  en efecto suelo, como imprime la tabla; el docstring declara la condición
  base explícitamente.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), asignación de rodaje del §A.3.5

- **Ubicación:** sección A.3.5, último párrafo (p. 19 impresa).
- **El impreso:** «To include taxiing for helicopters with and without wheels
  into the noise calculation the measured and derived hemispheres for
  in-ground hover and full-rpm idle respectively should be employed.»
- **El problema:** leído al pie de la letra, el «respectively» empareja el
  helicóptero con ruedas con la fuente de estacionario en efecto suelo y el
  sin ruedas con el ralentí a régimen pleno, que es lo contrario de las
  operaciones que modela: un helicóptero sin ruedas solo puede rodar en
  estacionario en efecto suelo, y uno con ruedas rueda por el suelo sobre sus
  ruedas con el rotor a ralentí gobernado, sin producir sustentación. Las dos
  listas se leen transpuestas. Ningún oráculo lo zanja (la publicación
  pública no distribuye caso de verificación de rodaje), así que el
  emparejamiento se corrige solo desde la física de las operaciones.
- **Evidencia:** comparación interna de las dos listas de la prosa contra las
  operaciones que nombran. Verificado en la página 18 del PDF (p. 19 impresa)
  de NORAH2 SC01.D1.5d (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** ninguna función se ve afectada (la
  regla selecciona entre dos hemisferios que el lector ya ha construido); la
  guía de rotorcraft documenta el emparejamiento físico, rodaje sin ruedas
  sobre el hemisferio de estacionario en efecto suelo y rodaje con ruedas
  sobre el de ralentí a régimen pleno, con esta salvedad.
- **Estado:** sin notificar.

## Guía de rotorcraft NORAH2 SC01.D1.5d (EASA.2020.FC.06), desplazamientos de la Tabla 3 frente a las correcciones distribuidas

- **Ubicación:** Tabla 3, columna de Approach 3 (pp. 18-19 impresas), contra
  el bloque `&CORRECTIONS` de los ficheros de consulta de interpolación
  distribuidos con la publicación pública NORAH2 V2.0.74.
- **El impreso:** desplazamientos de +12 dB\* (estacionario fuera del efecto
  suelo), -12 dB\* (ralentí a régimen reducido) y -2.5 dB\* (ralentí a
  régimen pleno) desde el disco de estacionario en efecto suelo, con la nota
  del asterisco de que se derivaron de mediciones con micrófonos invertidos
  sobre placas de suelo y «may not be valid for other microphone setups».
- **El problema:** la base de datos de referencia sobre la que se construye
  la guía distribuye valores distintos: cada uno de los once ficheros de
  consulta de triangulación por tipo (``*_triangulation.int``) de la
  publicación pública lleva `Corr_dB` 8, -10 y -2 para las mismas tres
  operaciones, así que las constantes publicadas y la base de datos discrepan
  en 4, 2 y 0.5 dB. La guía, cuya sección A.3.1 declara los datos de consulta
  distribuidos parte de la base de datos de hemisferios y no editables, no
  menciona la diferencia, y su nota cuestiona la validez de los valores
  publicados sin nombrar los que de verdad se distribuyen.
- **Evidencia:** los bloques `&CORRECTIONS` idénticos de los once ficheros de
  consulta de triangulación (``*_triangulation.int``) de la publicación
  pública V2.0.74; las constantes publicadas verificadas en las páginas 17 y
  18 del PDF (pp. 18 y 19 impresas) de NORAH2 SC01.D1.5d
  (EASA.2020.FC.06):2024.
- **Comportamiento de la biblioteca:** `hover_derived_hemisphere` usa por
  defecto las constantes publicadas de la Tabla 3 y acepta una corrección
  medida o de base de datos como ``offset_db``; el caso de verificación de
  estacionario de extremo a extremo pasa el +8 dB de la base de datos
  explícitamente, y el docstring registra la divergencia.
- **Estado:** sin notificar.

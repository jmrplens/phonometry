---
title: "Los mismos bits en cualquier máquina"
description: "Determinismo: por qué deriva la coma flotante, cómo un filtro sigue igual byte a byte en cualquier CPU, BLAS o número de hilos, qué difiere y la evidencia."
---

Un filtro de ponderación diseñado por phonometry es el mismo filtro, byte a
byte, en cualquier máquina que ejecute las mismas rutinas de la biblioteca
C: cualquier juego de kernels BLAS, cualquier número de hilos, cualquier
semilla de hash y cualquier CPU, con o sin AVX-512, salvo por una elección
que hace la propia biblioteca C. glibc en x86-64 lleva su arcotangente dos
veces, compilada con multiply-add fusionado y sin él, y elige una según el
procesador; las dos redondean unas pocas entradas hacia vecinos opuestos,
así que un procesador sin FMA diseña algunos filtros de otra manera, entre
ellos la ponderación A a 44,1&nbsp;kHz, aunque no las ponderaciones A, D ni
468 a 48&nbsp;kHz. Entre bibliotecas C los bytes todavía no coinciden, por
la misma razón: la arcotangente es la única trascendente que el diseño sigue
tomando del `math` de la plataforma. Cada una de las demás trascendentes
está escrita en aritmética que IEEE&nbsp;754 fija, y los dos pasos que
pasan por una biblioteca numérica, las raíces polinómicas de LAPACK y los
productos BLAS que forma SciPy, se nombran más abajo, en Alcance. Esta
página nombra lo que queda y mide lo que hace. Dentro de una
plataforma, los coeficientes que diseña un portátil son los que diseña un
clúster, así que un veredicto de conformidad, una figura publicada o un
filtro embarcado en una cadena de medida es un artefacto reproducible y no
el relato de una máquina sobre sí misma.

Esa frase no es el comportamiento normal del Python científico, y esta página
registra lo que costó, con los números.

## Por qué la coma flotante deriva entre hosts

IEEE 754 fija cada operación *individual*: dados dos dobles, su suma, resta,
producto, cociente y raíz cuadrada son el mismo patrón de bits en toda
máquina conforme. Todo lo que va más allá de una operación es por donde se
escapa la reproducibilidad, por tres puertas distintas.

**Las reducciones pueden reasociarse.** Una suma de muchos términos no tiene
orden definido, y un BLAS elige el que conviene a los registros vectoriales
que encuentra en tiempo de ejecución. phonometry midió lo que eso cuesta
sobre su propio ajuste de ponderaciones: dos juegos de kernels de OpenBLAS
coincidieron en todas las decisiones de aceptación de la búsqueda de
Levenberg-Marquardt durante treinta y nueve pasos consecutivos mientras los
costes que comparaban derivaban de 3&nbsp;&times;&nbsp;10⁻¹³ a
1&nbsp;&times;&nbsp;10⁻⁴ de separación, y las dos ejecuciones aterrizaron
después en **filtros distintos**: 5&nbsp;&times;&nbsp;10⁻⁵ de separación en
el coeficiente principal, 0,002&nbsp;dB en respuesta, unos visibles
0,0225&nbsp;pt en una curva dibujada. Un optimizador en un valle plano
amplifica lo que haga el último bit.

**Las trascendentes vectorizadas se despachan.** numpy elige los kernels de
`log`, `exp`, `tan`, `power`, `arctan` y `sin` según lo que ofrece la CPU, y
los kernels AVX-512 no coinciden hasta el último bit con los que corre una
máquina sin AVX-512. Medido bajo Intel SDE emulando Skylake-X contra el mismo
host en nativo: cada una de esas seis devuelve un digest distinto sobre las
mismas entradas. La fuga llega más lejos que los sitios de llamada obvios:
`numpy.geomspace` es `10 ** linspace(...)`, así que la propia rejilla de
frecuencias sobre la que se evalúa cada residuo del ajuste salía distinta
bajo AVX-512, y todos los pasos aguas abajo la heredaban.

**La libm de la plataforma es una elección de plataforma.** `math.log` es el
`log` que traiga la biblioteca C. El de glibc y el de Apple son ambos exactos
hasta cerca de media ulp, lo que significa que en un puñado de entradas
redondean legítimamente a vecinos *opuestos*, así que un bucle de diseño
construido sobre `math.log` devolvía filtros distintos en macOS y en Linux
sin nada en ningún sitio que lo dijera. Lo mismo valía para cualquier otra
trascendente que traiga la biblioteca C, y por eso la ponderación A a
48&nbsp;kHz llegó a dar tres digests en las tres plataformas de la matriz de
CI.

## Qué fija phonometry

El camino de diseño determinista responde a cada puerta en su terreno, en
`filters._weighting_design` y los módulos fijados que lo acompañan,
`filters._pinned_log`, `filters._pinned_exp` y `filters._pinned_trig`:

- **Sus propias reducciones.** Cada suma que el ajuste compara o con la que
  resuelve se pliega por pares en una forma que fija el código, y las
  ecuaciones normales se resuelven por eliminación gaussiana escrita a mano,
  el mismo algoritmo que corre el `dgesv` de LAPACK con el orden ya fuera de
  la elección de una biblioteca. El plegado por pares es además el orden
  *más exacto*: un redondeo O(&epsilon;&nbsp;log&nbsp;n) contra el
  O(&epsilon;&nbsp;n) de un acumulador corrido, así que no se sacrificó
  nada.
- **Aritmética real donde la compleja se despacha.** El producto complejo y
  el módulo complejo fusionan operaciones de forma distinta por CPU, así que
  los dos puntos donde el camino entregaba a numpy una expresión compleja
  están escritos en aritmética real.
- **Trascendentes fijadas.** Dentro de la iteración, el logaritmo corre tres
  cuartos de millón de veces por diseño, la exponencial una vez por factor y
  por evaluación, y la potencia una vez por punto de la rejilla en cada
  ronda de Lawson. Cada una es la propia rutina de glibc deletreada en
  operaciones numpy que IEEE&nbsp;754 fija exactamente, aritmética simple,
  trabajo de bits enteros y consultas de tabla: el `log` de tablas y el
  `log10` construido sobre él, y el `exp` y la `pow` de optimized-routines de
  ARM tal como glibc los compila para un procesador con multiply-add
  fusionado, cada multiply-add que fusiona esa compilación reproducido por
  una emulación exacta (redondeo a impar, según Boldo y Melquiond). El `sin`,
  que se toma dos veces por diseño, la `tan`, tres, y el módulo de una
  raíz compleja salen correctamente redondeados, en aritmética entera
  exacta. Sus bits son suyos en toda máquina, que es más fuerte que llamar a
  la libm de nadie. Una llamada sigue siendo de la plataforma: la
  arcotangente, una vez por diseño sobre los 257 puntos de la rejilla de
  frecuencias. Deletrearla igual es el paso que falta para un único digest en
  todas partes, y el valor correctamente redondeado no basta por sí solo: la
  arcotangente de glibc redondea al otro lado 19 de las 15&nbsp;866
  arcotangentes que evalúa el corpus, así que solo su propia rutina deja los
  coeficientes publicados en Linux donde están, y además su compilación con
  multiply-add fusionado, la que deletrean `exp` y `pow`: la arcotangente de
  glibc, como su `sin` y su `tan`, redondea distinto en sus dos
  compilaciones.
- **La rejilla deletreada.** La rejilla geométrica de frecuencias se genera
  término a término con los extremos fijados, así que el ajuste evalúa las
  mismas frecuencias en todas partes.

## La evidencia

Cada afirmación de arriba está medida, y la mayoría las re-miden tests que
corren en CI:

- **91.658.333 entradas, cero excepciones.** Cada valor distinto que el
  corpus de diseño entero pasa a su logaritmo se capturó y se comparó bit a
  bit contra el `log` de glibc: idéntico en todos, más alrededor de cien
  millones de sorteos adversariales sobre el rango completo de exponentes,
  la banda cercana a uno, los números subnormales (los «denormalizados» de
  la literatura clásica) y los bordes de las ramas. Una búsqueda
  adversarial encontró también el límite honesto: en torno a una
  entrada de cada treinta millones, en una banda estrecha, cuyo logaritmo
  verdadero queda a media ulp de ambos vecinos y donde las dos
  implementaciones se separan en el último bit. Ninguna puede alcanzar un
  diseño, porque en el camino de diseño la rutina fijada *es* la
  definición.
- **El corpus es byte-idéntico.** Los diseños de siete curvas a diecinueve
  frecuencias de muestreo, 133 en total, dan el mismo SHA-256 único antes y
  después de vectorizar el logaritmo, y otra vez después de fijar la
  exponencial, la potencia, el logaritmo decimal, `sin`, `tan` y los
  módulos complejos: ningún coeficiente, figura ni valor de conformidad
  publicado se movió.
- **La exponencial y la potencia, bit a bit.** Cada valor distinto que el
  corpus pasa a `exp` (677&nbsp;596) y a `pow` (580&nbsp;455) devuelve los
  bits de glibc, y también cada uno de 120 millones de sorteos sobre el
  dominio de cada rutina, con los bordes del desbordamiento y del
  subdesbordamiento y los resultados subnormales. La emulación del
  multiply-add fusionado devuelve el `fma` de la biblioteca C en cada uno de
  30 millones de sorteos, la mitad casi cancelándose.
- **Correctamente redondeado donde glibc lo está.** En los 70 valores de `sin`,
  los 105 de `tan` y los 67 módulos complejos que evalúa el corpus, glibc devuelve
  el valor correctamente redondeado, así que las rutinas correctamente
  redondeadas devuelven ahí sus bits. Fuera del corpus eso descansa en la
  precisión de glibc y no en una prueba: de todas las frecuencias de
  muestreo enteras entre 100&nbsp;Hz y 200&nbsp;kHz, 5&nbsp;864 de los
  1&nbsp;399&nbsp;307 diseños (frecuencia, curva) encuentran un `sin` o una
  `tan` que glibc redondea al otro lado, y esos diseños pueden moverse al
  fijarlos, en lo que una ulp del arranque crece a través del ajuste.
  Ninguno está en una frecuencia con la que se comprueba la biblioteca; de
  las frecuencias habituales, 50&nbsp;kHz para A, B, C y D y 100&nbsp;kHz
  para AU, que pasa de `7ee0fe06b2a91373` a `ec6c060d4b27d1b9`.
- **Ninguna biblioteca C salvo la de la arcotangente.** Con cada resultado que
  la biblioteca C devuelve a un diseño empujado una unidad en el último
  lugar, mediante una capa entre Python y la biblioteca C, los diseños no se
  mueven, salvo cuando se empuja el de la arcotangente, que los mueve todos.
  Con musl, otra biblioteca C, el corpus entero da el SHA-256 de glibc en
  cuanto la arcotangente coincide, y lo mismo las ponderaciones A y D a
  48&nbsp;kHz con glibc y con musl en ARM de 64 bits, la familia de
  procesadores de la pata de macOS de la matriz de CI, en emulación.
- **Digest a digest entre entornos.** Los diseños son bit-idénticos entre
  este host y el mismo host bajo emulación AVX-512, bajo cada juego de
  kernels de OpenBLAS seleccionable, cada número de hilos y cada semilla de
  hash; las comparaciones entorno contra entorno están fijadas como tests.
- **Un digest en tres plataformas, salvo la arcotangente.** Con solo el
  logaritmo fijado, la ponderación A a 48&nbsp;kHz daba `991833ff389afe91` en
  Linux (glibc, x86-64), `4efa1818bd80e23a` en macOS (arm64) y
  `79852a57e60961c8` en Windows (x86-64). Ahora un test de la matriz de CI la
  diseña con una arcotangente correctamente redondeada propia, que es la de
  glibc en los 257 puntos de esa rejilla, y sostiene `991833ff389afe91` en
  las tres plataformas: ninguna otra rutina de la biblioteca C llega al
  diseño, y los pasos de BLAS y LAPACK están en Alcance. El diseño que
  entrega una máquina sigue tomando la arcotangente de la plataforma, así
  que un segundo test lo diseña así y sostiene el mismo digest allí donde la
  arcotangente de la plataforma está correctamente redondeada en los 257
  puntos, como lo está la de glibc, y el digest propio medido de la
  plataforma donde no. Con glibc en x86-64 sin FMA el diseño que se entrega
  daba `43f786ffab5c4dd4` antes de fijarlo y da ahora `991833ff389afe91`.
  Los tests de respuesta
  que corren en esas tres plataformas sujetan el diseño A a 0,013&nbsp;dB de
  su prototipo analógico en toda su banda de ajuste, lo que acota lo que
  pueda suponer en respuesta cualquier diferencia que quede.

## Compruébalo tú

Dos diseños son el mismo diseño, y los bytes tienen nombre:

```python
import hashlib
from phonometry import filters

una = filters.WeightingFilter(48000, "A").sos
otra = filters.WeightingFilter(48000, "A").sos
print(una.tobytes() == otra.tobytes())                   # True
digest = hashlib.sha256(una.tobytes()).hexdigest()
print(digest[:16])                                       # 991833ff389afe91 en Linux
```

La segunda línea es la clave: esos dieciséis dígitos hexadecimales, la
cabeza del SHA-256, no son «lo que salió en mi máquina», son el digest de la
ponderación A a 48&nbsp;kHz de esta versión en cualquier máquina Linux con
glibc, la pata que fija la matriz de CI, y en cualquier otra plataforma cuya
arcotangente coincida con la de glibc en la rejilla. Si una
versión futura mueve un coeficiente a propósito, el digest se mueve con ella
y el cambio es un suceso documentado, nunca una propiedad de tu hardware.

## Alcance

La garantía cubre el camino de diseño determinista de ponderaciones de punta
a punta dentro de una plataforma, y el procesamiento por bloques compone con
ella: una cascada con
estado alimentada bloque a bloque es bit-idéntica a una sola pasada sobre el
registro entero, así que el streaming no gasta la garantía. Las funciones de
análisis generales construidas sobre numpy y SciPy en su forma corriente
siguen siendo reproducibles en una misma máquina pero pueden diferir en los
últimos bits entre CPUs, que es la condición normal del Python científico;
el tratamiento determinista se aplica donde importa la identidad de un
filtro.

Dos pasos de la cascada realizada pasan por una biblioteca y no por la
biblioteca C: los polos del prototipo de BS.468-4 son las raíces
polinómicas de numpy, que calcula LAPACK, y las secciones de segundo orden
las forma SciPy, cuyos productos de polinomios pasan por el BLAS. Los dos
dan los mismos bytes con cada juego de kernels de OpenBLAS y en las
compilaciones de ARM de 64 bits y de musl medidas; un BLAS que fusionara
esos productos movería los diseños D y G, medido fusionándolos a propósito,
y el framework Accelerate que enlaza la compilación de numpy para macOS no se
mide aquí. El `zpk2sos` de SciPy toma también módulos complejos, a través
del valor absoluto complejo propio de numpy, un bucle que numpy elige según
el procesador y no el `hypot` de la biblioteca C, pero solo para emparejar
polos con ceros y compararlos con una tolerancia: empujados una ulp, todos
ellos, no mueven ninguna de las ponderaciones A, D, 468 ni AU a
48&nbsp;kHz, la C a 44,1&nbsp;kHz ni la G a 1&nbsp;kHz.

El relato de ingeniería completo vive con el código, en los docstrings de
módulo de
[`filters/_weighting_design.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_weighting_design.py),
[`filters/_pinned_log.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_log.py),
[`filters/_pinned_exp.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_exp.py)
y
[`filters/_pinned_trig.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_trig.py),
y los tests que lo sostienen están en
[`tests/filters/test_weighting_design.py`](https://github.com/jmrplens/phonometry/blob/main/tests/filters/test_weighting_design.py)
y los tres `tests/filters/test_pinned_*.py` que lo acompañan.

## Véase también

- [Informe de conformidad](/phonometry/es/reference/conformance/): contra qué se comprueban los números; esta página es la razón de que las comprobaciones lean igual en todas partes.
- [Erratas de las fuentes publicadas](/phonometry/es/reference/errata/): la otra mitad de la historia de la evidencia: donde lo que está mal es el valor esperado impreso.
- [Ponderaciones en frecuencia](/phonometry/es/signals/levels/weighting/): la guía de las curvas que realiza el diseño determinista.
- [Procesamiento por bloques](/phonometry/es/signals/filters/block-processing/): la identidad de streaming en la que se apoya la sección de alcance.

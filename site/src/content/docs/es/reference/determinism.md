---
title: "Los mismos bits en cualquier máquina"
description: "Determinismo: por qué deriva la coma flotante, cómo un filtro sigue igual byte a byte en cualquier CPU, BLAS o número de hilos, qué difiere y la evidencia."
---

Un filtro de ponderación diseñado por phonometry es el mismo filtro, byte a
byte, sean cuales sean la biblioteca C, el número de hilos o la semilla de
hash con que se diseñe, sea cual sea el compilador con que se construyó
numpy, y en cualquier procesador x86-64, con o sin AVX-512 o multiply-add
fusionado, corra allí el juego de kernels de OpenBLAS que corra. La única
reserva son dos pasos de la cascada realizada que pasan por
una biblioteca numérica y no por la biblioteca C, las raíces polinómicas de
LAPACK y los productos BLAS que forma SciPy, que en ARM de 64 bits, según se
midió, separan algunos diseños de las otras curvas y ninguno de la
ponderación A; Alcance, más abajo, los nombra y dice qué se midió. En el
ajuste del diseño de ponderaciones no queda ninguna rutina de la biblioteca
C: cada trascendente que toma está escrita en aritmética que IEEE&nbsp;754
fija o calculada correctamente redondeada en aritmética entera exacta, así
que glibc, la libm de Apple, musl y el runtime de Windows, y las dos
compilaciones que glibc lleva para x86-64, no tienen voz en sus bits. Esta
página registra lo que se fijó y mide lo que hace. Los coeficientes que
diseña un portátil son los que diseña un clúster, así que un veredicto de
conformidad, una figura publicada o un filtro embarcado en una cadena de
medida es un artefacto reproducible y no el relato de una máquina sobre sí
misma.

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
- **Aritmética real donde la compleja se despacha o se fusiona.** El
  producto complejo y el módulo complejo fusionan operaciones de forma
  distinta por CPU, y el producto y el cociente complejos de numpy son
  bucles de C que un compilador puede fusionar en multiply-adds: numpy
  compilado con clang, como en macOS y Windows, lo hace, y numpy compilado
  con GCC, como en Linux, no. Así que cada punto donde el camino entregaba a
  numpy o a SciPy una expresión compleja está escrito en aritmética real,
  los pasos de numpy en el orden de numpy, cada uno redondeado una vez: la
  curva impresa a la que apunta el ajuste, la lectura que fija la ganancia
  que se entrega y la transformada bilineal con su ganancia, que
  `bilinear_zpk` de SciPy forma como un producto de números complejos.
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
  que se toma dos veces por diseño, la `tan`, tres, la arcotangente, una vez
  por diseño sobre los 257 puntos de la rejilla de frecuencias, y el módulo
  de una raíz compleja salen correctamente redondeados: el double más
  cercano al valor exacto, hallado en aritmética entera exacta con el bucle
  de Ziv. Sus bits son suyos en toda máquina, que es más fuerte que llamar a
  la libm de nadie, y en el ajuste no queda ninguna rutina de la biblioteca
  C. Para la arcotangente eso tuvo un precio en Linux: la de glibc redondea
  al otro lado 19 de las 15&nbsp;866 arcotangentes que evalúan los diseños
  comprobados, así que el valor correctamente redondeado movió seis de los
  133 diseños comprobados en sus últimos bits. La rutina de glibc, que los
  habría dejado donde estaban, es la IBM Accurate Mathematical Library, con
  licencia LGPL-2.1-or-later, y no se transcribe en este paquete MIT.
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
- **El corpus se movió donde lo hizo la arcotangente, y en ningún otro
  sitio.** Los diseños de siete curvas a diecinueve frecuencias de muestreo,
  133 en total, dan el mismo SHA-256 único antes y después de vectorizar el
  logaritmo, y otra vez después de fijar la exponencial, la potencia, el
  logaritmo decimal, `sin`, `tan` y los módulos complejos. La arcotangente
  correctamente redondeada movió después seis de ellos en sus últimos bits:
  las ponderaciones A y C a 44,1 y 88,2&nbsp;kHz, la D a 88,2&nbsp;kHz y la G
  a 1,5&nbsp;kHz. Las 19 arcotangentes que glibc redondea mal llegan a 32 de
  los 133 diseños; en los otros 26 la frecuencia que difiere en una ulp da
  el mismo nivel objetivo hasta el último bit, así que el ajuste nunca la
  ve. Con la arcotangente de glibc de vuelta, el corpus da otra vez su
  SHA-256 anterior, y los seis que se movieron siguen dentro de las cotas de
  respuesta que sostienen los tests.
- **La exponencial y la potencia, bit a bit.** Cada valor distinto que el
  corpus pasa a `exp` (677&nbsp;596) y a `pow` (580&nbsp;455) devuelve los
  bits de glibc, y también cada uno de 120 millones de sorteos sobre el
  dominio de cada rutina, con los bordes del desbordamiento y del
  subdesbordamiento y los resultados subnormales. La emulación del
  multiply-add fusionado devuelve el `fma` de la biblioteca C en cada uno de
  30 millones de sorteos, la mitad casi cancelándose.
- **La arcotangente, contra el valor exacto.** La arcotangente fijada
  devuelve el double correctamente redondeado, calculado de forma
  independiente por una biblioteca de precisión arbitraria a 200 bits, en
  cada uno de los 15&nbsp;866 valores distintos que le pasan los diseños
  comprobados, en 572&nbsp;386 valores de borde (cada potencia de dos desde
  el subnormal más pequeño hasta el double más grande con 64 vecinos a cada
  lado, los ceros con signo, los infinitos, NaN y las dos bandas donde la
  respuesta deja de ser el argumento o el double más cercano a &pi;/2), en
  60 millones de patrones de bits aleatorios sobre toda la recta de los
  doubles y en 150 millones de sorteos cuya magnitud está entre 2⁻⁶² y 2⁶²,
  donde la rutina hace su trabajo de verdad. Con
  la primera pasada recortada a 56 bits, donde entre un cuarto y un tercio
  de las entradas necesita una segunda y solo la cota de error decide, otros
  60 millones de sorteos salen también correctamente redondeados, y esa
  cota, comparada con el valor exacto en un millón de evaluaciones a cinco
  precisiones de trabajo, nunca se usó más que a medias. En CI las
  respuestas se comprueban con cotas racionales exactas sobre la tangente,
  sin evaluar ninguna arcotangente.
- **Correctamente redondeado, donde glibc lo está y donde no.** En los 70
  valores de `sin`, los 105 de `tan` y los 67 módulos complejos que evalúa
  el corpus, glibc devuelve el valor correctamente redondeado, así que las
  rutinas correctamente redondeadas devuelven ahí sus bits; en 19 de sus
  arcotangentes no lo hace, como se dice arriba. Fuera del corpus la
  coincidencia descansa en la precisión de glibc y no en una prueba: de
  todas las frecuencias de muestreo enteras entre 100&nbsp;Hz y
  200&nbsp;kHz, 5&nbsp;864 de los 1&nbsp;399&nbsp;307 diseños (frecuencia,
  curva) encuentran un `sin` o una `tan` que glibc redondea al otro lado, y
  45&nbsp;526 leen un nivel objetivo que la arcotangente de glibc cambia, y
  esos diseños pueden moverse en Linux al fijarlas, en lo que una ulp crece
  a través del ajuste. De las frecuencias habituales que deja fuera el
  conjunto comprobado, 50&nbsp;kHz para A, B, C y D y 100&nbsp;kHz para AU
  encuentran un `sin` o una `tan` (AU pasa de `7ee0fe06b2a91373` a
  `ec6c060d4b27d1b9`), y 176,4&nbsp;kHz para A, B y C la arcotangente.
- **Ninguna biblioteca C.** Con cada resultado que devuelve la biblioteca C
  empujado una unidad en el último lugar, mediante una capa entre Python y
  la biblioteca C, el de la arcotangente incluido, doce diseños (la
  ponderación A a 48, 44,1, 88,2 y 192&nbsp;kHz, la C a 44,1 y
  88,2&nbsp;kHz, la D a 48 y 88,2&nbsp;kHz, la G a 1 y 1,5&nbsp;kHz, y la
  468 y la AU a 48&nbsp;kHz) no se mueven ni un bit, mientras que con el
  código anterior a la arcotangente fijada se movían todos. musl, otra
  biblioteca C, diseña el corpus entero con el SHA-256 de glibc sin
  sustituir nada, y lo mismo la compilación de glibc sin FMA. En ARM de 64
  bits, la familia de procesadores de la pata de macOS de la matriz de CI,
  en emulación con musl, 100 de los 133 diseños son los mismos bytes, y los
  otros 33 se separan en los dos pasos de biblioteca que nombra Alcance,
  ninguno en la aritmética propia de este paquete.
- **Digest a digest entre entornos.** Los diseños son bit-idénticos entre
  este host y el mismo host bajo emulación AVX-512, bajo cada juego de
  kernels de OpenBLAS seleccionable, cada número de hilos y cada semilla de
  hash; las comparaciones entorno contra entorno están fijadas como tests.
- **Un digest en tres plataformas.** Con solo el logaritmo fijado, la
  ponderación A a 48&nbsp;kHz daba `991833ff389afe91` en Linux (glibc,
  x86-64), `4efa1818bd80e23a` en macOS (arm64) y `79852a57e60961c8` en
  Windows (x86-64). Con todas las trascendentes fijadas aún daba
  `5f5e34e5d3a8aa6e` en macOS y en Windows, un mismo valor para los dos: la
  transformada bilineal de SciPy tomaba la ganancia como un producto de
  números complejos, por el bucle de numpy que clang fusiona y GCC no. Un
  test que fusiona esos productos y cocientes en cualquier plataforma
  reproduce ese digest con el código que llamaba a SciPy, y con la
  transformada escrita en aritmética real diseña `991833ff389afe91`, y con
  ella sin cambios los diseños bilineales simples de todas las curvas a
  48&nbsp;kHz. Un test de la matriz de CI diseña la ponderación A tal como
  se entrega, sin sustituir nada, y la sostiene en `991833ff389afe91` en las
  tres plataformas, y la ponderación A a 44,1&nbsp;kHz en
  `dbea4b7fc4ad972b`; un
  segundo test diseña las dos otra vez con una arcotangente que no le debe
  nada a la rutina fijada, la respuesta de la biblioteca C llevada hasta el
  double correctamente redondeado con cotas racionales exactas, y cae en
  los mismos digests. Con glibc en x86-64 sin FMA la ponderación A a
  48&nbsp;kHz daba `43f786ffab5c4dd4` antes de fijar las rutinas, y la
  segunda compilación de la arcotangente aún separaba nueve de los 133
  diseños comprobados de la compilación con FMA hasta que se fijó; las dos
  compilaciones diseñan ahora el corpus entero con un mismo SHA-256.
  Los tests de respuesta
  que corren en esas tres plataformas sujetan el diseño A a 0,013&nbsp;dB de
  su prototipo analógico en 20&nbsp;001 frecuencias de su banda de ajuste,
  en cada una de las seis frecuencias de muestreo que comprueban; dos
  plataformas cuyos bytes aún difirieran podrían diferir hasta el doble,
  0,026&nbsp;dB, en una de esas frecuencias.

## Compruébalo tú

Dos diseños son el mismo diseño, y los bytes tienen nombre:

```python
import hashlib
from phonometry import filters

una = filters.WeightingFilter(48000, "A").sos
otra = filters.WeightingFilter(48000, "A").sos
print(una.tobytes() == otra.tobytes())                   # True
digest = hashlib.sha256(una.tobytes()).hexdigest()
print(digest[:16])                                       # 991833ff389afe91
```

La segunda línea es la clave: esos dieciséis dígitos hexadecimales, la
cabeza del SHA-256, no son «lo que salió en mi máquina», son el digest de la
ponderación A a 48&nbsp;kHz de esta versión en cualquier máquina, el que la
matriz de CI sostiene por igual en Linux, macOS y Windows. Si una
versión futura mueve un coeficiente a propósito, el digest se mueve con ella
y el cambio es un suceso documentado, nunca una propiedad de tu hardware.

## Alcance

La garantía cubre el camino de diseño determinista de ponderaciones de punta
a punta, dentro de los dos pasos de biblioteca que siguen: en cualquier
plataforma para la ponderación A, que la matriz de CI sostiene en Linux,
macOS y Windows, y para las otras curvas allí donde esos dos pasos dan los
mismos bytes. El procesamiento por bloques compone con ella: una cascada con
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
dan los mismos bytes con cada juego de kernels de OpenBLAS en x86-64, con
glibc y con musl. En ARM de 64 bits no siempre: medido con musl en
emulación, con el OpenBLAS que numpy trae ahí, 100 de los 133 diseños
comprobados son los bytes de x86-64, entre ellos la ponderación A en las
diecinueve frecuencias, y los otros 33 se separan justo en estos dos pasos.
Los polos del prototipo 468 salen distintos en sus últimos bits, lo que
alcanza a los diecinueve diseños 468; en catorce diseños de las
ponderaciones B, C, D, G y AU (la D a 1,5, 32, 88,2 y 96&nbsp;kHz, la G a
200&nbsp;Hz y a 1, 88,2, 96 y 192&nbsp;kHz, la AU a 32, 44,1 y
88,2&nbsp;kHz, la B a 96&nbsp;kHz y la C a 48&nbsp;kHz) el prototipo que
devuelve el ajuste y su transformada bilineal son iguales hasta el bit, y
solo difieren las secciones que SciPy forma con ellos. El framework
Accelerate que enlaza la compilación de numpy para macOS no se mide aquí,
así que para esas curvas no se afirman los bytes de macOS; la ponderación
A, cuyas secciones salen iguales en ARM de 64 bits, la sostiene el test de
CI en macOS. El `zpk2sos` de SciPy toma también módulos complejos, a través
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

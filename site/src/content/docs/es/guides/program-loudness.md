---
title: "Sonoridad de programa y pico verdadero (UIT-R BS.1770 / EBU R 128)"
description: "El algoritmo de sonoridad de programa de la Rec. UIT-R BS.1770-5 y la práctica de normalización de EBU R 128: ponderación K, sonoridad integrada con puertas en LUFS, los medidores momentáneo y de corto plazo del modo EBU de Tech 3341, el rango de sonoridad de Tech 3342 y el nivel de pico verdadero por sobremuestreo en dBTP."
---

La **Rec. UIT-R BS.1770-5** define cómo miden la sonoridad de un programa la
radiodifusión y el streaming: **ponderación K**, potencia cuadrática media en
**bloques de 400 ms con puertas** y suma ponderada por canal, expresada en
**LKFS/LUFS**. **EBU R 128** construye encima la práctica de normalización
(todo programa se nivela a **−23,0 LUFS** con un techo de pico verdadero de
**−1 dBTP**), y sus documentos compañeros EBU Tech 3341 y Tech 3342 añaden el
medidor en *modo EBU* (sonoridad momentánea, de corto plazo e integrada) y el
*rango de sonoridad* (LRA). phonometry implementa la cadena completa en el
espacio de nombres `broadcast` y valida cada señal de prueba EBU
sintetizable con su tolerancia oficial.

## 1. La ponderación K y la medida de sonoridad (Anexo 1)

La señal atraviesa primero un prefiltro de dos etapas: un realce de agudos
de ~+4 dB que modela la cabeza como una esfera rígida y después el paso alto
RLB. Su concatenación es la **ponderación K**. La sonoridad en un intervalo
es la suma ponderada por canal de las potencias cuadráticas medias $z_i$
(Fórmula 2):

$$
L_K = -0.691 + 10 \log_{10} \sum_i G_i\, z_i \quad \text{LKFS},
$$

donde la constante cancela la ganancia de la ponderación K a 997 Hz y $G_i$
pondera cada canal (1,0 los canales frontales, 1,41 los envolventes, LFE
excluido, Tabla 3). La Recomendación ancla la escala: un seno de 997 Hz a
0 dB FS en un canal frontal marca −3,01 LKFS. La unidad se escribe LKFS en
la UIT y LUFS en la EBU; son idénticas, y 1 LU es 1 dB.

```python
import numpy as np
from phonometry import broadcast

fs = 48000
t = np.arange(20 * fs) / fs
x = np.zeros((5, t.size))                     # L, R, C, Ls, Rs
x[0] = np.sin(2 * np.pi * 997.0 * t)          # 0 dB FS en el canal izquierdo
print(round(broadcast.integrated_loudness(x, fs), 2))   # -3.01  LKFS
```

Los coeficientes de los biquads están tabulados a 48 kHz (Tablas 1-2) y a
esa frecuencia se devuelven literalmente; cualquier otra frecuencia los
rederiva a través del prototipo analógico para que la respuesta coincida con
la especificación (dentro de 0,02 dB a 32 kHz y por encima; las frecuencias
por debajo de 16 kHz se rechazan):

```python
import numpy as np
from phonometry import broadcast

(b1, a1), (b2, a2) = broadcast.k_weighting_coefficients(48000)
print(b1)   # [ 1.53512486 -2.69169619  1.19839281]  (Tabla 1, literal)
y = broadcast.k_weighting(np.random.default_rng(0).standard_normal(48000),
                          48000)              # la propia señal filtrada
```

## 2. Las puertas y la sonoridad de programa

La sonoridad **integrada** (de programa) divide la medición en bloques de
400 ms con solape del 75 % y les aplica dos puertas (Fórmulas 3-7): los
bloques por debajo del umbral absoluto de **−70 LKFS** se descartan; la
sonoridad de los supervivientes menos 10 LU fija el **umbral relativo**, y
los bloques por encima de ambas puertas definen el resultado. Las puertas
evitan que los pasajes silenciosos largos (ambientes, pausas, colas de
aplausos) arrastren hacia abajo el nivel del primer plano:

```python
import numpy as np
from phonometry import broadcast

fs = 48000
def tono(nivel_dbfs, segundos):
    t = np.arange(int(segundos * fs)) / fs
    return 10 ** (nivel_dbfs / 20) * np.sin(2 * np.pi * 1000.0 * t)

# 10 s de programa a -23 dBFS seguidos de 30 s de ambiente silencioso.
x = np.concatenate([tono(-23.0, 10.0), tono(-50.0, 30.0)])
res = broadcast.program_loudness(np.vstack([x, x]), fs)
print(round(res.integrated, 1))            # -23.1  LUFS (la cola se descarta)
print(round(res.relative_threshold, 1))    # -39.0  LUFS
```

Una media sin puertas sobre los mismos 40 s quedaría cerca de −29 LUFS: las
puertas son lo que hace que los programas de gran rango de sonoridad casen
en antena. EBU R 128 normaliza este valor integrado a **−23,0 LUFS**; cuando
el objetivo no es alcanzable en la práctica (programas en directo, por
ejemplo) se permite una tolerancia de ±1,0 LU, y los flujos de control de
calidad admiten ±0,2 LU por error de medida.

## 3. Modo EBU: momentánea, corto plazo, integrada

EBU Tech 3341 define las tres escalas temporales de un medidor conforme, y
una sola llamada las calcula todas:

* **Momentánea (M)**: ventana deslizante de 400 ms, sin puertas;
* **Corto plazo (S)**: ventana deslizante de 3 s, sin puertas;
* **Integrada (I)**: la sonoridad de programa con puertas anterior,

más **Max M** y **Max S**, el pico verdadero y el LRA:

```python
import numpy as np
from phonometry import broadcast

fs = 48000
def tono(nivel_dbfs, segundos):
    t = np.arange(int(segundos * fs)) / fs
    return 10 ** (nivel_dbfs / 20) * np.sin(2 * np.pi * 1000.0 * t)

# Caso de prueba 3 de EBU Tech 3341: escalones de -36 / -23 / -36 dBFS.
x = np.concatenate([tono(-36.0, 10.0), tono(-23.0, 60.0), tono(-36.0, 10.0)])
res = broadcast.program_loudness(np.vstack([x, x]), fs)
print(round(res.integrated, 1), round(res.max_momentary, 1),
      round(res.max_short_term, 1))         # -23.0 -23.0 -23.0
```

El `ProgramLoudnessResult` congelado lleva las series M y S con sus ejes de
tiempo, los máximos, los umbrales, el LRA con sus bordes percentiles, los
picos verdaderos por canal y las ponderaciones de canal; su `.plot()` dibuja
la traza de sonoridad del programa:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/program_loudness_es.svg" alt="Medición EBU R 128 de un programa sintético de un minuto con secciones de ambiente, diálogo, música y fundido: la sonoridad momentánea gris respira alrededor de la traza azul de corto plazo, la sonoridad integrada discontinua roja cae exactamente sobre el objetivo de -23 LUFS y una banda sombreada marca el rango de sonoridad entre sus percentiles 10 y 95" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/program_loudness_es_dark.svg" alt="Medición EBU R 128 de un programa sintético de un minuto con secciones de ambiente, diálogo, música y fundido: la sonoridad momentánea gris respira alrededor de la traza azul de corto plazo, la sonoridad integrada discontinua roja cae exactamente sobre el objetivo de -23 LUFS y una banda sombreada marca el rango de sonoridad entre sus percentiles 10 y 95" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from phonometry import broadcast

fs = 48000
rng = np.random.default_rng(1770)
sos = signal.butter(2, 2000.0, fs=fs, output="sos")
trozos = []
for nivel, segundos in [(-38, 8), (-23, 16), (-17, 12), (-25, 16), (-45, 8)]:
    ruido = signal.sosfilt(sos, rng.standard_normal(int(segundos * fs)))
    ruido /= np.sqrt(np.mean(ruido ** 2))
    t = np.arange(ruido.size) / fs
    vaiven = 1 + 0.22 * np.sin(2 * np.pi * 0.9 * t) \
        + 0.14 * np.sin(2 * np.pi * 2.83 * t + 1.0)
    trozos.append(10 ** (nivel / 20) * ruido * vaiven)
x = np.concatenate(trozos)

# Normalizar el programa al objetivo de R 128 y medirlo.
ganancia = -23.0 - broadcast.integrated_loudness(np.vstack([x, x]), fs)
x *= 10 ** (ganancia / 20)
broadcast.program_loudness(np.vstack([x, x]), fs).plot()
plt.show()
```

</details>

## 4. Rango de sonoridad (EBU Tech 3342)

El **rango de sonoridad** cuantifica cuánto varía la sonoridad en una escala
temporal macroscópica, en LU. Es la separación entre los **percentiles 10 y
95** de la distribución de sonoridad de corto plazo tras una puerta en
cascada: un umbral absoluto de −70 LUFS y después un umbral relativo
**−20 LU** por debajo del nivel de lo que sobrevivió (deliberadamente más
profundo que los −10 LU de la medida integrada, para que el primer plano
silencioso pero real siga contando). Los percentiles impiden que un disparo
aislado o un fundido inflen el valor:

```python
import numpy as np
from phonometry import broadcast

fs = 48000
def tono(nivel_dbfs, segundos):
    t = np.arange(int(segundos * fs)) / fs
    return 10 ** (nivel_dbfs / 20) * np.sin(2 * np.pi * 1000.0 * t)

# Caso de prueba 1 de EBU Tech 3342: 20 s a -20 dBFS y 20 s a -30 dBFS.
x = np.concatenate([tono(-20.0, 20.0), tono(-30.0, 20.0)])
res = broadcast.program_loudness(np.vstack([x, x]), fs)
print(round(res.loudness_range, 1))         # 10.0  LU
```

`loudness_range()` también está disponible de forma independiente sobre
cualquier vector de sonoridad de corto plazo, siguiendo la implementación de
referencia de Tech 3342 (incluida su indexación de percentiles por rango más
cercano). La EBU no recomienda el LRA para programas de menos de un minuto:
demasiado pocas ventanas de 3 s.

## 5. Pico verdadero (Anexo 2)

Los picos por muestra engañan: el máximo verdadero de la forma de onda
reconstruida cae en general *entre* muestras, y un medidor de pico por
muestra infravalora 3 dB un tono a $f_s/4$ con la fase desafortunada (peor
caso $20\log_{10}\cos(\pi f_{\mathrm{norm}}/n)$ para una razón de
sobremuestreo $n$). Por eso el Anexo 2 de BS.1770-5 mide el **pico
verdadero** sobre la señal sobremuestreada hasta al menos 192 kHz (4× a
48 kHz), en **dBTP** (dB respecto al 100 % de la escala completa):

```python
import numpy as np
from phonometry import broadcast

fs = 48000
t = np.arange(fs) / fs
# Un tono a fs/4 a plena escala cuyos picos caen justo entre muestras.
x = np.sin(2 * np.pi * (fs / 4) * t + np.pi / 4)
print(round(float(broadcast.true_peak_level(x, fs, oversample=1)), 2))  # -3.01
print(round(float(broadcast.true_peak_level(x, fs)), 2))                #  0.12
```

El interpolador recupera la excursión entre muestras que la rejilla de
muestreo perdió (el residuo de +0,12 dB es rizado de interpolación de los
bordes abruptos del tono, dentro de la tolerancia de +0,2/−0,4 dB que deben
cumplir los medidores en modo EBU). EBU R 128 limita la producción a
**−1 dBTP**; los códecs de distribución suelen necesitar más margen. Es la
misma maquinaria de pico sobremuestreado que sostiene el `lc_peak` ponderado
C de [Niveles integrados y estadísticos](/phonometry/es/guides/levels/).

## 6. Programas multicanal y el Anexo 3

Con 1, 2, 5 o 6 canales las ponderaciones de la Tabla 3 se aplican solas
(orden de canales `L, R, C, Ls, Rs`, o `L, R, C, LFE, Ls, Rs` con el LFE
excluido). Para cualquier otra disposición de altavoces (22.2, 4+7+0 y el
resto de sistemas de sonido avanzados de BS.2051), el Anexo 3 deriva la
ponderación de cada canal de la posición de su altavoz: 1,41 (+1,5 dB) para
los altavoces laterales de la capa media (60° ≤ |acimut| ≤ 120°,
|elevación| < 30°), 1,0 en el resto:

```python
from phonometry import broadcast

print(broadcast.channel_weight(110.0, 0.0))    # 1.41  (M+110, lateral)
print(broadcast.channel_weight(110.0, 35.0))   # 1.0   (U+110, capa superior)
pesos = broadcast.channel_weight([0, 30, -30, 90, -90], [0, 0, 0, 0, 0])
# -> [1. 1. 1. 1.41 1.41]; se pasa como program_loudness(..., weights=pesos)
```

El audio basado en objetos (Anexo 4) se mide renderizando primero a una
configuración de altavoces y midiendo el render; el renderizado en sí queda
fuera de este alcance.

## 7. Validación

Cada señal sintetizable de "requisitos mínimos" de EBU Tech 3341 (casos 1-6
y 9-23) y de Tech 3342 (casos 1-4) se ejecuta en la batería de tests con su
tolerancia oficial (±0,1 LU en sonoridad, +0,2/−0,4 dB en pico verdadero,
±1 LU en LRA), junto con el ancla de 997 Hz y la cota de infravaloración en
forma cerrada del Anexo 2, Adjunto 1. Los casos 7-8 y los casos 5-6 del LRA
usan material de programa auténtico distribuido por la EBU y no son
sintetizables; se ejecutan contra el conjunto oficial de pruebas de sonoridad
de la EBU (descargado de la propia EBU, cuya licencia cubre solo pruebas
técnicas, así que el audio nunca se incorpora al repositorio) y los cuatro
pasan dentro de tolerancia; las series de sonoridad por bloques medidas de
esos ficheros se incorporan como datos simples, de modo que las etapas de
gating y LRA de estos casos se ejecutan también en todas partes sin el
audio. El medidor independiente
[pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) es un contraste útil
con grabaciones reales; no se usó como fuente de esta implementación.

## Referencias

- Unión Internacional de Telecomunicaciones. (2023). *Algorithms to measure
  audio programme loudness and true-peak audio level* (Recomendación
  UIT-R BS.1770-5).
  [Publicación UIT-R](https://www.itu.int/rec/R-REC-BS.1770).
  La ponderación K, las ponderaciones de canal, las puertas y el algoritmo
  de pico verdadero.
- Unión Europea de Radiodifusión. (2023). *Loudness normalisation and
  permitted maximum level of audio signals* (EBU R 128).
  [tech.ebu.ch/publications/r128](https://tech.ebu.ch/publications/r128).
  El objetivo de −23,0 LUFS, el techo de −1 dBTP y la práctica de
  normalización.
- Unión Europea de Radiodifusión. (2023). *Loudness metering: 'EBU Mode'
  metering to supplement loudness normalisation* (EBU Tech 3341).
  [tech.ebu.ch/publications/tech3341](https://tech.ebu.ch/publications/tech3341).
  Las escalas temporales M/S/I y las señales de prueba de requisitos
  mínimos.
- Unión Europea de Radiodifusión. (2023). *Loudness range: A measure to
  supplement loudness normalisation* (EBU Tech 3342).
  [tech.ebu.ch/publications/tech3342](https://tech.ebu.ch/publications/tech3342).
  El algoritmo del LRA, su implementación de referencia y sus señales de
  prueba.
- Unión Europea de Radiodifusión. (2023). *Guidelines for production of
  programmes in accordance with EBU R 128* (EBU Tech 3343).
  [tech.ebu.ch/publications/tech3343](https://tech.ebu.ch/publications/tech3343).
  La práctica de producción alrededor de los números de esta página.
- Steinmetz, C. J., y Reiss, J. D. (2021). *pyloudnorm: A simple yet
  flexible loudness meter in Python*. 150.ª Convención de la AES.
  [github.com/csteinmetz1/pyloudnorm](https://github.com/csteinmetz1/pyloudnorm).
  Una implementación independiente de BS.1770, útil como contraste.

## Normas

Rec. UIT-R BS.1770-5 (11/2023), *Algorithms to measure audio programme
loudness and true-peak audio level*: el prefiltro de ponderación K (Anexo 1,
Tablas 1-2), la sonoridad ponderada por canal y las puertas en dos etapas
(Anexo 1, Fórmulas 1-7, Tabla 3), las directrices de estimación del pico
verdadero (Anexo 2 y la cota de infravaloración de su Adjunto 1) y las
ponderaciones de canal dependientes de la posición para sistemas de sonido
avanzados (Anexo 3, Tablas 4-5). EBU R 128 (2023), *Loudness normalisation
and permitted maximum level of audio signals*: el nivel objetivo de
−23,0 LUFS y el máximo de −1 dBTP. EBU Tech 3341 (2023): las escalas
temporales momentánea/corto plazo/integrada del modo EBU, validadas frente a
las señales sintetizables de requisitos mínimos de su Tabla 1 con sus
tolerancias oficiales. EBU Tech 3342 (2023): el rango de sonoridad, validado
frente a las señales de su Tabla 1 con ±1 LU.

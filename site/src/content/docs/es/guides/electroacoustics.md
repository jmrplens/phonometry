---
title: "Electroacústica: distorsión y respuesta en frecuencia"
description: "Distorsión IEC 60268-3 — distorsión armónica total y de orden n, THD+N y SINAD (AES17), intermodulación SMPTE y CCIF, intermodulación dinámica (DIM) y THD ponderada — más los estimadores de respuesta en frecuencia H1/H2 de Bendat y Piersol y la coherencia ordinaria."
---

Dos pilares de la caracterización de equipos de audio, a partir de una señal
capturada: cuánto **distorsiona** un amplificador o un transductor un tono de
prueba, y qué **respuesta en frecuencia** revela una medición de entrada/salida.
Esta página cubre el conjunto de distorsión de la IEC 60268-3 — distorsión
armónica total y de orden n, THD+N y SINAD (AES17), las mediciones de
intermodulación SMPTE y CCIF, la intermodulación dinámica (DIM) y la THD
ponderada — y los estimadores de respuesta en frecuencia `H1`/`H2` de Bendat y
Piersol con la coherencia ordinaria `γ²`. Toda magnitud tiene un oráculo
analítico exacto, así que los valores son verificables y no ajustados.

## 1. Distorsión armónica (IEC 60268-3 14.12.2–5)

Un dispositivo no lineal alimentado con un seno puro en `f₁` devuelve el
fundamental más armónicos en `2f₁, 3f₁, …`. La **distorsión armónica total**
combina las amplitudes armónicas `aₙ`, ya sea respecto al fundamental
(`kind='F'`) o respecto al RMS total (`kind='R'`):

$$
\mathrm{THD}_F = \frac{\sqrt{\sum_{n\ge 2} a_n^2}}{a_1}, \qquad
\mathrm{THD}_R = \frac{\sqrt{\sum_{n\ge 2} a_n^2}}{\sqrt{\sum_{n\ge 1} a_n^2}},
\qquad
d_n = \frac{a_n}{\sqrt{\sum_{k\ge 1} a_k^2}}.
$$

`dₙ` es la distorsión armónica de orden n (el armónico n respecto al total). Los
tonos deben caer en las líneas de la FFT — usa muestreo coherente (un número
entero de periodos) o una ventana de baja fuga — para leer las amplitudes sin
fuga espectral.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/distortion_es.svg" alt="Espectro de magnitud de un ensayo con tono único de 1 kHz en dB respecto al fundamental, con los cinco primeros armónicos marcados sobre un suelo de ruido de banda ancha, anotado con THD (F), THD (R), THD+N y SINAD" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/distortion_es_dark.svg" alt="Espectro de magnitud de un ensayo con tono único de 1 kHz en dB respecto al fundamental, con los cinco primeros armónicos marcados sobre un suelo de ruido de banda ancha, anotado con THD (F), THD (R), THD+N y SINAD" style="width:82%">

```python
import phonometry as ph

thd_f = ph.thd(signal, fs, 1000.0, kind="F")          # respecto al fundamental
thd_r = ph.thd(signal, fs, 1000.0, kind="R")          # respecto al RMS total
d2 = ph.harmonic_distortion(signal, fs, 1000.0, 2)    # armónico de 2º orden
```

`harmonic_analysis` agrupa el fundamental, las amplitudes armónicas y la THD
(ambas convenciones), THD+N y SINAD en un único resultado representable:

```python
res = ph.harmonic_analysis(signal, fs, 1000.0)
print(res.thd_f, res.thd_r, res.thd_plus_noise, res.sinad_db)
res.plot()   # espectro armónico anotado (necesita matplotlib)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

fs = 48000
n = fs                     # 1 s -> líneas de 1 Hz; los armónicos caen en líneas
t = np.arange(n) / fs
f0 = 1000.0
amps = {1: 1.0, 2: 0.02, 3: 0.012, 4: 0.006, 5: 0.003}
sig = sum(a * np.sin(2 * np.pi * k * f0 * t) for k, a in amps.items())
sig = sig + np.random.default_rng(2026).standard_normal(n) * 1.2e-2

res = ph.harmonic_analysis(sig, fs, f0, n_harmonics=len(amps))
res.plot()
plt.show()
```

</details>

## 2. THD+N y SINAD (AES17-2015 6.3)

Mientras que la THD cuenta solo los armónicos, la **THD+N** compara *todo salvo
el fundamental* — armónicos **y** ruido — con la señal total. AES17 elimina el
fundamental con un filtro de muesca normalizado (`1,2 ≤ Q ≤ 3`) y toma la razón
entre el residuo y el RMS total; el **SINAD** es su recíproco en dB:

$$
\mathrm{THD{+}N} = \frac{V_\text{residuo}}{V_\text{total}}, \qquad
\mathrm{SINAD} = -20\lg(\mathrm{THD{+}N})\ \mathrm{dB}.
$$

```python
import phonometry as ph

ratio = ph.thd_plus_noise(signal, fs, 1000.0)          # razón (0..)
db = ph.thd_plus_noise(signal, fs, 1000.0, as_db=True)  # 20·lg(razón) dB
sinad_db = ph.sinad(signal, fs, 1000.0)                 # = -db
```

Como la THD+N incluye el suelo de ruido, es igual o mayor que la THD de solo
armónicos; el `SINAD` es el correspondiente margen señal-a-ruido-y-distorsión en
dB. La muesca descarta internamente un transitorio de arranque/parada, así que la
medición requiere una captura estacionaria y suficientemente larga.

### 2.1 THD ponderada (IEC 60268-3 14.12.11)

`weighted_thd` pondera en frecuencia el residuo tras la muesca (ponderación A por
defecto) antes de tomar la razón, de modo que se tiene en cuenta el énfasis
perceptual de los productos de distorsión:

```python
import phonometry as ph

print(ph.weighted_thd(signal, fs, 1000.0, weighting="A"))
```

## 3. Distorsión por intermodulación (IEC 60268-3 14.12.7–10)

Cuando dos tonos atraviesan una no linealidad, laten entre sí y producen
productos de suma y diferencia. La IEC 60268-3 normaliza tres ensayos:

- **Distorsión de modulación** (tipo SMPTE, 14.12.7): un tono grave grande
  `f_low` y un tono agudo pequeño `f_high` (1:4). La distorsión de orden n es el
  RMS de las bandas laterales en `f_high ± (n−1)·f_low`, respecto a `f_high`.
- **Distorsión por frecuencia diferencia** (tipo CCIF, 14.12.8): dos tonos agudos
  iguales `f₁ < f₂`. El segundo orden queda en `f₂ − f₁`; el tercero en
  `2f₁ − f₂` y `2f₂ − f₁`. `total_difference_frequency_distortion` combina ambos
  en RMS.
- **Intermodulación dinámica** (DIM, 14.12.9): un seno de 15 kHz más una onda
  cuadrada de 3,15 kHz filtrada en paso bajo (1:4). La DIM es el RMS de los
  productos de intermodulación `|k·f_square ± f_sine|` que caen por debajo de
  `f_sine` (Tabla 2 de la IEC 60268-3), respecto al seno de 15 kHz.

```python
import phonometry as ph

smpte = ph.modulation_distortion(signal, fs, 60.0, 7000.0)          # SMPTE
ccif2 = ph.difference_frequency_distortion(signal, fs, 13e3, 14e3, order=2)  # CCIF
ccif_total = ph.total_difference_frequency_distortion(signal, fs, 13e3, 14e3)
dim = ph.dynamic_intermodulation_distortion(signal, fs)             # DIM (15k/3,15k)
```

## 4. Respuesta en frecuencia y coherencia (Bendat y Piersol)

Dada una entrada `x` y la salida `y` de un dispositivo, la **respuesta en
frecuencia** `H(f)` se estima a partir de los autoespectros y el espectro cruzado
promediados con Welch. Bendat y Piersol (*Random Data*, 4ª ed.) dan dos
estimadores, que difieren en qué canal soporta el ruido, más la **coherencia
ordinaria** `γ²` — la fracción de la potencia de salida explicada linealmente por
la entrada:

$$
H_1 = \frac{G_{xy}}{G_{xx}}, \qquad H_2 = \frac{G_{yy}}{G_{yx}}, \qquad
\gamma^2 = \frac{|G_{xy}|^2}{G_{xx}\,G_{yy}} \in [0, 1].
$$

`H1` es insesgado cuando el ruido está en la salida, y `H2` cuando está en la
entrada; para un camino lineal sin ruido ambos recuperan la respuesta verdadera y
`γ² = 1`. El ruido aditivo a la salida sesga `H2` al alza y baja la coherencia
hasta `SNR/(1+SNR)`.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/frequency_response_es.svg" alt="Magnitud de Bode de una respuesta en frecuencia estimada con H1 que sigue la respuesta verdadera de un sistema paso banda, con la coherencia ordinaria debajo cayendo hacia los bordes de banda donde la señal de salida es débil frente al ruido" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/frequency_response_es_dark.svg" alt="Magnitud de Bode de una respuesta en frecuencia estimada con H1 que sigue la respuesta verdadera de un sistema paso banda, con la coherencia ordinaria debajo cayendo hacia los bordes de banda donde la señal de salida es débil frente al ruido" style="width:82%">

```python
import phonometry as ph

res = ph.transfer_function(x, y, fs, estimator="H1")
print(res.magnitude_db, res.phase, res.coherence)
res.plot()   # magnitud/fase de Bode + coherencia (necesita matplotlib)

freqs, gamma2 = ph.coherence(x, y, fs)
```

La coherencia necesita promediarse sobre varios segmentos de Welch para ser
significativa — un único segmento da `γ² ≡ 1` por construcción.

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sp
import phonometry as ph

fs = 48000
n = 400000
rng = np.random.default_rng(7)
x = rng.standard_normal(n)
b, a = sp.butter(2, [400.0, 4000.0], btype="band", fs=fs)   # dispositivo bajo ensayo
y = sp.lfilter(b, a, x)
y = y + rng.standard_normal(n) * np.sqrt(np.mean(y ** 2)) * 0.05   # ruido de salida

res = ph.transfer_function(x, y, fs, estimator="H1")
res.plot()
plt.show()
```

</details>

---

**Normas.** IEC 60268-3:2013, *Sound system equipment – Part 3: Amplifiers*
(cláusulas 14.12.2–14.12.11): distorsión armónica total `THD_F`/`THD_R`,
distorsión armónica de orden n `dₙ`, intermodulación de modulación (SMPTE) y por
frecuencia diferencia (CCIF), distorsión total por frecuencia diferencia,
intermodulación dinámica (DIM) y THD ponderada. AES17-2015, *Measurement of
digital audio equipment* (cláusula 6.3): la razón THD+N mediante el filtro de
muesca normalizado, y el SINAD. Bendat y Piersol (2010), *Random Data: Analysis
and Measurement Procedures* (4ª ed., Wiley): los estimadores de respuesta en
frecuencia `H1` y `H2` y la coherencia ordinaria `γ²`. Todas las magnitudes se
verifican contra oráculos analíticos exactos (señales sintéticas con amplitudes
armónicas/de intermodulación conocidas y un camino LTI conocido).

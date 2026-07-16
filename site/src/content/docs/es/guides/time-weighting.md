---
title: "Ponderación temporal"
description: "Ponderación temporal Fast, Slow e Impulse según IEC 61672-1."
---

La medición precisa de SPL requiere capturar la energía en ventanas temporales
específicas. phonometry implementa las constantes de tiempo exactas de la norma
**IEC 61672-1:2013**.

## 1. El detector exponencial

La aguja de un sonómetro no puede seguir la forma de onda de presión — muestra
un *valor cuadrático medio* móvil con memoria exponencial. Formalmente
(IEC 61672-1, 3.8):

$$
\tau\ \frac{dy}{dt} + y = x^2(t)
\quad\Longleftrightarrow\quad
y(t) = \frac{1}{\tau} \int_{-\infty}^{t} x^2(\xi)\ e^{-(t-\xi)/\tau}\ d\xi
$$

un paso-bajo de primer orden sobre la señal al cuadrado. La constante de tiempo
τ fija el compromiso: **Fast** (125 ms) sigue fluctuaciones del tipo del habla
y **Slow** (1 s) estabiliza la lectura para ruido cuasi estacionario. Tras un
escalón, la envolvente alcanza el 63 % de su valor final en un τ y ~99,97 %
tras 8τ — por eso los análisis de nivel descartan los primeros instantes de una
grabación.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_time_weighting_es.svg" alt="La cadena del detector exponencial: la presión de banda se eleva al cuadrado, se suaviza con un paso bajo RC de un polo con constante de tiempo tau y se convierte a decibelios, con las constantes de tiempo Fast, Slow e Impulse indicadas" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_time_weighting_es_dark.svg" alt="La cadena del detector exponencial: la presión de banda se eleva al cuadrado, se suaviza con un paso bajo RC de un polo con constante de tiempo tau y se convierte a decibelios, con las constantes de tiempo Fast, Slow e Impulse indicadas" style="width:88%">

## 2. Las tres ponderaciones temporales

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_time_weighting_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_time_weighting_es_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: una ráfaga de tono excita el detector exponencial RC, el condensador se carga y se descarga, y las agujas de los medidores Rápida, Lenta e Impulso siguen su propia balística" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_time_weighting_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_time_weighting_es_dark_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: una ráfaga de tono excita el detector exponencial RC, el condensador se carga y se descarga, y las agujas de los medidores Rápida, Lenta e Impulso siguen su propia balística" style="width:88%"></video>

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_weighting_analysis_es.svg" alt="Respuestas de las ponderaciones temporales Fast, Slow e Impulse a una ráfaga de ruido" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_weighting_analysis_es_dark.svg" alt="Respuestas de las ponderaciones temporales Fast, Slow e Impulse a una ráfaga de ruido" style="width:80%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from phonometry import time_weighting

fs = 48000
t = np.arange(int(fs * 4)) / fs
burst = np.zeros_like(t)  # ráfaga de ruido de 0.5 s (Pa) que empieza en t = 1 s
rng = np.random.default_rng(42)
burst[fs:int(1.5 * fs)] = 0.2 * rng.standard_normal(int(0.5 * fs))

p0 = 2e-5
plt.figure()
for mode in ('fast', 'slow', 'impulse'):
    envelope = time_weighting(burst, fs, mode=mode)
    plt.plot(t, 10 * np.log10(np.maximum(envelope, 1e-12) / p0**2), label=mode)
plt.xlabel('Tiempo [s]')
plt.ylabel('Nivel [dB SPL]')
plt.legend()
plt.show()
```

</details>

* **Fast (`fast`):** τ = 125 ms. Estándar para fluctuaciones de ruido.
* **Slow (`slow`):** τ = 1000 ms. Estándar para ruido estacionario.
* **Impulse (`impulse`):** ponderación temporal **asimétrica**. 35 ms de subida para
  capturar ataques rápidos y 1500 ms de caída para facilitar la lectura.

```python
import numpy as np
from phonometry import time_weighting

# recording: una captura de micrófono calibrada (Pa) — grabada con tu cadena de medición. Sintetizada aquí para que la guía funcione por sí sola.
fs = 48000
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# Calcular la envolvente de energía (valor cuadrático medio)
energy_envelope = time_weighting(recording, fs, mode='fast')
# dB SPL respecto a 20 μPa
spl_t = 10 * np.log10(energy_envelope / (2e-5)**2)

print(f"Nivel Fast en régimen permanente: {spl_t[-1]:.1f} dB SPL")
# Nivel Fast en régimen permanente: 77.0 dB SPL
```

La ponderación temporal Impulse asimétrica usa dos constantes — ataque rápido y caída
lenta — conmutando por muestra según el signo del cambio:

$$
y[n] = y[n-1] + \alpha \ (x^2[n] - y[n-1]), \qquad
\alpha = \begin{cases}1 - e^{-1/(f_s \cdot 0{,}035)} & x^2[n] > y[n-1]\\[2pt] 1 - e^{-1/(f_s \cdot 1{,}5)} & \text{en otro caso}\end{cases}
$$

## 3. Parámetros de `time_weighting()` / `TimeWeighting`

| Parámetro | Tipo | Unidades | Rango / por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D o 2D | presión (cualquier escala) | no vacío | Se eleva al cuadrado internamente; la salida es una envolvente cuadrática media |
| `fs` | int | Hz | > 0 | |
| `mode` | str | — | `'fast'` (por defecto), `'slow'`, `'impulse'` | τ = 125 ms / 1 s / ataque de 35 ms + caída de 1,5 s |
| `TimeWeighting(fs, mode)` (clase) | — | — | — | Variante con estado para streaming: `process(x)` conserva el estado del integrador entre bloques |

La salida tiene las unidades de $x^2$: toma `10*log10(y / p0**2)` para SPL o
usa las funciones de nivel, que lo hacen por ti.

## 4. Respuesta temporal verificada (IEC 61672-1, Tabla 4)

La respuesta de la envolvente Fast a ráfagas de tono de 4 kHz cae exactamente
sobre los valores de referencia de la norma — el ejemplo de abajo verifica la
fila de la ráfaga Fast de 200 ms; la batería de CI cubre la Tabla 4 completa,
de 1 s a 1 ms en F y de 1 s a 2 ms en S, con límites de aceptación de clase 1:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_burst_iec_es.svg" alt="Respuestas de la envolvente Fast a ráfagas de 200, 50 y 10 ms alcanzando exactamente los valores de la Tabla 4 de IEC 61672-1" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_burst_iec_es_dark.svg" alt="Respuestas de la envolvente Fast a ráfagas de 200, 50 y 10 ms alcanzando exactamente los valores de la Tabla 4 de IEC 61672-1" style="width:80%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from phonometry import time_weighting

fs = 48000
t = np.arange(int(fs * 2)) / fs
tone = np.sin(2 * np.pi * 4000 * t)

# Referencia Fast en régimen permanente del tono continuo
reference = time_weighting(tone, fs, mode='fast')[int(1.5 * fs):].mean()

# Ráfaga de 200 ms del mismo tono (objetivo de la Tabla 4 de IEC 61672-1: -1.0 dB)
burst = np.zeros_like(t)
burst[int(0.5 * fs):int(0.7 * fs)] = tone[int(0.5 * fs):int(0.7 * fs)]
envelope = time_weighting(burst, fs, mode='fast')
env_db = 10 * np.log10(np.maximum(envelope / reference, 1e-6))

plt.figure()
plt.plot(t, env_db, label='Envolvente Fast')
plt.axhline(-1.0, linestyle='--', label='Objetivo IEC −1.0 dB')
plt.xlabel('Tiempo [s]')
plt.ylabel('Nivel respecto al régimen permanente [dB]')
plt.legend()
plt.show()
```

</details>

## 5. Estado inicial

Por defecto, el integrador exponencial parte del reposo (`y[-1] = 0`). Pasar
`initial_state=None` deja ese comportamiento por defecto, mientras que
`initial_state='zero'` lo solicita explícitamente. Si el segmento grabado
comienza con una señal estacionaria ya presente, puedes partir de la energía de
la primera muestra:

```python
# Usa `recording` y `fs` del snippet anterior.
energy_envelope = time_weighting(recording, fs, mode='fast', initial_state='first')
```

## 6. Procesado por bloques

Para procesar por bloques, pasa el último valor de salida del bloque anterior
como `initial_state` del siguiente en lugar de reiniciar en cada bloque:

```python
state = None

# audio_blocks: fotogramas consecutivos de tu grabación calibrada (Pa),
#   transmitidos desde tu tarjeta de sonido o leídos de un WAV por bloques.
for block in audio_blocks:
    energy_envelope = time_weighting(block, fs, mode='fast', initial_state=state)
    state = energy_envelope[-1]
```

Para bloques multicanal con el tiempo en el último eje, lleva un estado por
canal: usa `state = energy_envelope[..., -1]`. Un `initial_state` escalar se
aplica a todos los canales, mientras que un array debe coincidir (o difundirse)
con la forma sin el eje temporal, p. ej. `(n_channels,)` para una entrada de
forma `(n_channels, n_samples)`.

O deja que la clase `TimeWeighting` lleve el estado por ti:

```python
from phonometry import TimeWeighting

tw = TimeWeighting(fs, mode='fast')
# audio_blocks: fotogramas consecutivos de tu grabación calibrada (Pa),
#   transmitidos desde tu tarjeta de sonido o leídos de un WAV por bloques.
for block in audio_blocks:
    energy_envelope = tw.process(block)
```

Las salidas concatenadas por bloques son exactamente iguales a una única llamada
continua (verificado para los tres modos, mono y multicanal). Llama a
`tw.reset()` para volver al reposo.

## 7. Nota de rendimiento

El modo `impulse` usa un kernel asimétrico que se compila JIT cuando
[numba](https://numba.pydata.org/) está instalado (`pip install phonometry[perf]`).
Sin numba, un fallback en Python puro produce resultados idénticos, solo que más
lento.

Consulta [Niveles integrados y estadísticos](/phonometry/es/guides/levels/)
para las métricas Leq/LN construidas sobre estas envolventes, y
[Por qué phonometry](/phonometry/es/reference/why-phonometry/) para la
verificación con ráfagas de tono de IEC 61672-1.

---

**Normas.** IEC 61672-1:2013, *Electroacoustics — Sound level meters —
Part 1: Specifications* — el detector exponencial de ponderación temporal
(cláusula 3.8) con las constantes de tiempo F y S (cláusula 5.7), y las
respuestas de referencia a ráfagas de tono de 4 kHz de la Tabla 4 (límites de
aceptación de clase 1) usadas para verificar la respuesta temporal en CI.

## Véase también

- Referencia de la API: [`metrology.parametric_filters`](/phonometry/es/reference/api/filters/parametric-filters/).

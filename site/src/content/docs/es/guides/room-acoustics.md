---
title: "Acústica de salas"
description: "Adquisición de la respuesta al impulso (ISO 18233), parámetros de sala EDT/T20/T30/C50/C80/Ts (ISO 3382-1/2), métricas de habla en oficinas diáfanas (ISO 3382-3) y absorción sonora en sala reverberante (ISO 354)."
---

La acústica de salas parte de una única medición: la **respuesta al impulso**
(RI) entre una fuente y un receptor. Fíltrala en bandas e intégrala, y da el
tiempo de reverberación, la claridad y la inteligibilidad del habla —todo
sobre el campo sonoro dentro de un único recinto. Esta página sigue esa cadena
en orden de medición: adquirir la RI (ISO 18233), convertirla en parámetros de
sala (ISO 3382-1/2), métricas espaciales del habla para oficinas diáfanas
(ISO 3382-3) y, cerrando el ciclo, la absorción sonora de un material en una
sala reverberante (ISO 354). Para el aislamiento acústico *entre* recintos —la
misma RI medida a ambos lados de un cerramiento— consulta la guía complementaria
[Medición del aislamiento en campo e índices](/phonometry/es/guides/insulation-field/).

## 1. Adquisición de la respuesta al impulso (ISO 18233)

Una sala se comporta, con buena aproximación, como un sistema **lineal e
invariante en el tiempo**, así que todo sobre ella está contenido en su RI.
Podrías disparar una pistola y grabar la cola, pero una excitación
determinista reproducida por un altavoz y *deconvolucionada* recupera la
misma RI con 20–30 dB más de relación señal-ruido efectiva (ISO 18233). Se
proporcionan dos excitaciones.

**Barrido sinusoidal exponencial (ESS, Anexo B).** La frecuencia
instantánea crece exponencialmente,

$$
f(t) = f_1 \left( \frac{f_2}{f_1} \right)^{t/T},
$$

de modo que el tiempo invertido por octava es constante y la excitación
imita al ruido rosa (energía constante por banda de octava fraccionaria).
La RI se recupera mediante división espectral lineal (con relleno de ceros,
no circular),

$$
H = \frac{Y\ \overline{X}}{|X|^2 + \varepsilon},
$$

con un pequeño término de Tikhonov $\varepsilon$ que protege los extremos de
banda donde el barrido tiene poca energía. Como un barrido de grave a agudo
sitúa la distorsión armónica en tiempos de llegada *negativos*, la distorsión
se separa limpiamente de la RI lineal y se descarta conservando solo la parte
causal. El método `"farina"` llega al mismo resultado convolucionando la
grabación con el filtro inverso analítico; supone que el barrido de
referencia se generó con la amplitud y el desvanecimiento por defecto, así
que usa el método espectral con un barrido de amplitud distinta de la unidad
o con desvanecimiento personalizado.

**Secuencia de longitud máxima (MLS, Anexo A).** Una secuencia binaria de
orden `N` y longitud $2^N-1$ cuya autocorrelación circular es una delta casi
perfecta; la RI se obtiene de la correlación cruzada circular del periodo
grabado con la secuencia. La MLS excita con amplitud constante y es rápida de
promediar, pero es más sensible a la varianza temporal (corrientes de aire,
deriva de temperatura) y no admite tanta potencia como un barrido.
**Prefiere el barrido** para salas y cerramientos; recurre a la MLS cuando la
excitación deba ser periódica o el hardware favorezca una señal de dos
niveles.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement_es.svg" alt="Cadena de medición indirecta ISO 18233: una excitación (barrido ESS o MLS) alimenta un altavoz en la sala, un micrófono capta la respuesta y la deconvolución (correlación o filtro inverso) recupera la respuesta al impulso" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement_es_dark.svg" alt="Cadena de medición indirecta ISO 18233: una excitación (barrido ESS o MLS) alimenta un altavoz en la sala, un micrófono capta la respuesta y la deconvolución (correlación o filtro inverso) recupera la respuesta al impulso" style="width:92%">

```python
import numpy as np
from scipy.signal import fftconvolve
from phonometry import sweep_signal, impulse_response, mls_signal, mls_impulse_response

fs = 48000
# Un barrido de 3 s, 20 Hz - 20 kHz es una buena excitación de sala de banda ancha
# sweep: excitación que reproduces por el altavoz
sweep = sweep_signal(fs, 20.0, 20000.0, 3.0)

# Deconvoluciona la respuesta grabada para recuperar la respuesta al impulso
system = np.zeros(fs); system[100] = 1.0; system[2000] = 0.4   # directo + reflexión
# recorded: captura de micrófono del barrido reproducido (aquí simulada por convolución con una sala sintética)
recorded = fftconvolve(sweep, system)
ir = impulse_response(recorded, sweep, fs, method="spectral")
print(int(np.argmax(np.abs(ir))))                    # 100: sonido directo recuperado

# Variante de filtro inverso de Farina (necesita la banda del barrido)
ir_f = impulse_response(recorded, sweep, fs, method="farina", f_range=(20.0, 20000.0))

# MLS periódica: excita con >= 2 periodos, promedia, correlaciona
mls = mls_signal(16)                                 # longitud 2**16 - 1 = 65535
rec = fftconvolve(np.tile(mls, 2), system)[: 2 * mls.size]
ir_m = mls_impulse_response(rec, mls)
print(int(np.argmax(np.abs(ir_m))))                  # 100
```

`sweep_signal`/`mls_signal` devuelven arrays simples, listos para escribir en
un WAV y reproducir. `impulse_response`/`mls_impulse_response` devuelven ahora
un `ImpulseResponseResult` — un sustituto directo del array de la RI
(`np.asarray(ir)`, la indexación y `ir.size` siguen funcionando, de modo que
`room_parameters(ir, fs)` no cambia) que además guarda la frecuencia de
muestreo y el método y añade un `.plot()`.

**Las dos excitaciones.** El barrido exponencial desplaza su energía hacia
frecuencias altas a lo largo de toda la señal, mientras que la MLS es una
secuencia de dos niveles con espectro plano — visible como la magnitud
casi constante de la derecha.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/excitation_signals_es.png" alt="Señales de excitación ISO 18233: la forma de onda del barrido sinusoidal exponencial y su espectrograma con el ascenso exponencial de frecuencia, y una secuencia de longitud máxima con su espectro de magnitud plano" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/excitation_signals_es_dark.png" alt="Señales de excitación ISO 18233: la forma de onda del barrido sinusoidal exponencial y su espectrograma con el ascenso exponencial de frecuencia, y una secuencia de longitud máxima con su espectro de magnitud plano" style="width:96%">

<details>
<summary>Ver el código de esta figura</summary>

```python
from phonometry import sweep_signal, mls_signal, plot_excitation

fs = 48000
sweep = sweep_signal(fs, 50.0, 20000.0, 1.0)   # excitación ESS
mls = mls_signal(12).astype(float)             # longitud 2**12 - 1

# Una línea: forma de onda + espectrograma (barrido), secuencia + espectro (MLS)
plot_excitation(sweep, fs, kind="sweep")
plot_excitation(mls, fs, kind="mls")

# A mano: el espectrograma del barrido y el espectro de magnitud de la MLS
import numpy as np
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.specgram(sweep, NFFT=1024, Fs=fs, noverlap=512)
ax1.set(xlabel="Tiempo [s]", ylabel="Frecuencia [Hz]", title="Espectrograma del barrido")
spec = np.abs(np.fft.rfft(mls))
freqs = np.fft.rfftfreq(mls.size, d=1.0 / fs)
ax2.semilogx(freqs[1:], 20 * np.log10(spec[1:] / np.median(spec[1:])))
ax2.set(xlabel="Frecuencia [Hz]", ylabel="Magnitud [dB]", title="Espectro de la MLS (plano)")
```

</details>

**La respuesta al impulso recuperada.** Deconvolucionar la grabación da la RI
de banda ancha: el sonido directo, las reflexiones tempranas discretas y la
cola difusa que decae. Su `.plot()` muestra la forma de onda arriba y la
envolvente log-magnitud con la curva de decaimiento de energía de Schroeder
abajo — el decaimiento recto cuya pendiente se convierte en el tiempo de
reverberación del §2.

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_sweep_deconvolution_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_sweep_deconvolution_es_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: el barrido exponencial cruza la sala mientras su espectrograma se construye con copias retardadas de las reflexiones, y después el filtro inverso colapsa toda la grabación en la respuesta al impulso" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_sweep_deconvolution_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_sweep_deconvolution_es_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: el barrido exponencial cruza la sala mientras su espectrograma se construye con copias retardadas de las reflexiones, y después el filtro inverso colapsa toda la grabación en la respuesta al impulso" style="width:88%"></video>

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_response_es.png" alt="Respuesta al impulso de la sala recuperada: la forma de onda normalizada con el sonido directo y las reflexiones etiquetadas, y debajo la envolvente log-magnitud en dB con la curva de decaimiento de energía de Schroeder" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impulse_response_es_dark.png" alt="Respuesta al impulso de la sala recuperada: la forma de onda normalizada con el sonido directo y las reflexiones etiquetadas, y debajo la envolvente log-magnitud en dB con la curva de decaimiento de energía de Schroeder" style="width:88%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import numpy as np
from scipy.signal import fftconvolve
from phonometry import sweep_signal, impulse_response

fs = 48000
sweep = sweep_signal(fs, 20.0, 20000.0, 1.5)
# Una sala sintética: sonido directo + dos reflexiones + cola difusa que decae
system = np.zeros(int(0.7 * fs))
system[80], system[1400], system[3100] = 1.0, 0.5, 0.32
ir = impulse_response(fftconvolve(sweep, system), sweep, fs, length=system.size)

# Una línea: forma de onda + log-magnitud / decaimiento de Schroeder
ir.plot()

# A mano: la envolvente log-magnitud normalizada en dB
import matplotlib.pyplot as plt
h = np.asarray(ir)
t = np.arange(h.size) / fs
plt.plot(t, 20 * np.log10(np.abs(h) / np.max(np.abs(h))))
plt.ylim(-80, 5)
plt.xlabel("Tiempo [s]"); plt.ylabel("Nivel re pico [dB]")
```

</details>

**Dónde medir.** Una RI caracteriza un único par fuente–receptor; un parámetro
de sala se obtiene promediando sobre varios. ISO 3382-1 (espacios para
interpretación) pide al menos dos posiciones de fuente y micrófonos separados
$\geq 2$ m entre sí, $\geq 1$ m de cualquier superficie, a $1{,}2$ m
(altura de oído sentado), evitando colocaciones simétricas; ISO 3382-2 fija el
número mínimo de posiciones de fuente, de micrófono y de combinaciones
fuente–micrófono según el grado de exactitud (control / ingeniería /
precisión).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_measurement_es.svg" alt="Configuración de medición de acústica de salas: una planta de la sala en vista superior con dos posiciones de fuente (altavoz) y seis posiciones de micrófono con las reglas de separación de ISO 3382-1, y la tabla de ISO 3382-2 con el número mínimo de posiciones para los grados de control, ingeniería y precisión" style="width:94%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_room_measurement_es_dark.svg" alt="Configuración de medición de acústica de salas: una planta de la sala en vista superior con dos posiciones de fuente (altavoz) y seis posiciones de micrófono con las reglas de separación de ISO 3382-1, y la tabla de ISO 3382-2 con el número mínimo de posiciones para los grados de control, ingeniería y precisión" style="width:94%">

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_comb_filtering_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_comb_filtering_es_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: al cambiar la altura del micrófono varía el retardo entre el sonido directo y la reflexión del suelo y el filtro en peine de la respuesta en frecuencia se mueve con él; por eso importa la posición de medición cerca de superficies reflectantes" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_comb_filtering_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_comb_filtering_es_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: al cambiar la altura del micrófono varía el retardo entre el sonido directo y la reflexión del suelo y el filtro en peine de la respuesta en frecuencia se mueve con él; por eso importa la posición de medición cerca de superficies reflectantes" style="width:88%"></video>

### Parámetros de `sweep_signal()` / `inverse_filter()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `fs` | int | Hz | > 0 | Frecuencia de muestreo |
| `f1` | float | Hz | > 0, en/por debajo de la banda más baja | Frecuencia inicial del barrido |
| `f2` | float | Hz | `f1 < f2 <= fs/2` | Frecuencia final del barrido |
| `seconds` | float | s | cualquiera; mayor ⇒ más SNR | Duración del barrido |
| `amplitude` | float | — | por defecto `1.0` | Amplitud de pico |
| `fade` | float | — | `[0, 0.5)`, por defecto `0.01` | Fracción de fundido medio Hann (elimina transitorios de inicio/fin) |

### Parámetros de `impulse_response()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `recorded` | array 1D | cualquiera | no vacío | Respuesta del sistema grabada |
| `reference` | array 1D | cualquiera | no vacío | El barrido emitido |
| `fs` | int | Hz | > 0 | Frecuencia de muestreo |
| `method` | str | — | `'spectral'` (por defecto) / `'farina'` | `'farina'` requiere `f_range` |
| `f_range` | (float, float) | Hz | por defecto `None` | `(f1, f2)` del barrido (solo Farina) |
| `regularization` | float | — | por defecto `1e-6` | Término de Tikhonov como fracción de la energía espectral de pico |
| `length` | int, opcional | muestras | por defecto `len(recorded)` | Muestras de RI causal a devolver |
| `return_full` | bool | — | por defecto `False` | Devuelve la secuencia completa (distorsión en la cola) |

`mls_signal(order)` toma un entero `order` en 2–20 (longitud de secuencia
$2^{\text{order}}-1$); `mls_impulse_response(recorded, mls, length=None)`
necesita que `recorded` abarque un número entero de periodos de MLS.

## 2. Análisis del decaimiento y parámetros de sala (ISO 3382-1/2)

La RI se filtra en bandas de octava (o de tercio de octava) y cada banda se
convierte en una **curva de decaimiento** mediante la integración inversa de
Schroeder de la RI al cuadrado:

$$
E(t) = \int_t^{\infty} p^2(\tau)\ d\tau, \qquad
L(t) = 10 \log_{10} \frac{E(t)}{E(0)}\ \text{dB}.
$$

Integrar *hacia atrás* elimina la fluctuación que afecta a la RI al cuadrado
en bruto y produce una curva suave cuya pendiente es la tasa de decaimiento.
El ruido de fondo haría que $E(t)$ se estabilizara, así que la integración se
trunca donde la recta de decaimiento ajustada cruza el suelo de ruido y la
cola que falta se compensa suponiendo un decaimiento exponencial.

Los tiempos de reverberación provienen de un ajuste lineal por mínimos
cuadrados sobre un rango de evaluación, extrapolado a una caída completa de
60 dB, $T = -60/\text{slope}$: **EDT** de 0 a −10 dB (reverberación
percibida), **T20** de −5 a −25 dB y **T30** de −5 a −35 dB. Los repartos de
energía en una frontera temprano/tardío dan la **claridad** y la
**definición**,

$$
C_{te} = 10 \log_{10} \frac{\int_0^{te} p^2\ dt}{\int_{te}^{\infty} p^2\ dt}\ \text{dB}, \qquad
D_{50} = \frac{\int_0^{0{,}05} p^2\ dt}{\int_0^{\infty} p^2\ dt},
$$

con $te = 50$ ms → C50 (habla) y $te = 80$ ms → C80 (música), más el
**tiempo central** $T_s = \int t\ p^2\ dt / \int p^2\ dt$. Cada parámetro
tiene una **diferencia apenas perceptible** (ISO 3382-1 Tabla A.1: EDT 5 %,
C80 1 dB, D50 0,05, Ts 10 ms) que fija con qué precisión merece la pena
informarlo.

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_schroeder_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_schroeder_es_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: la energía de la cola de la respuesta al impulso al cuadrado se rellena desde el final mientras la integral hacia atrás avanza hacia t = 0, y la curva de caída de Schroeder emerge en un eje inferior que termina con las rectas de regresión T20 y T30" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_schroeder_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_schroeder_es_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: la energía de la cola de la respuesta al impulso al cuadrado se rellena desde el final mientras la integral hacia atrás avanza hacia t = 0, y la curva de caída de Schroeder emerge en un eje inferior que termina con las rectas de regresión T20 y T30" style="width:88%"></video>

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay_es.png" alt="Respuesta al impulso al cuadrado con su curva de decaimiento integrada hacia atrás de Schroeder, y las ventanas de regresión EDT, T20 y T30 marcadas" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay_es_dark.png" alt="Respuesta al impulso al cuadrado con su curva de decaimiento integrada hacia atrás de Schroeder, y las ventanas de regresión EDT, T20 y T30 marcadas" style="width:80%">

*La RI al cuadrado dentada (gris) se integra hasta la curva suave de
Schroeder (azul); las ventanas EDT, T20 y T30 se ajustan sobre esa curva y
cada una se extrapola a un decaimiento de 60 dB.*

```python
import numpy as np
from phonometry import decay_curve, room_parameters

fs = 48000
# Decaimiento de pendiente única con T = 1 s: p^2 = exp(-13.8155 t)  (60/ln(10)/13.8155 = 1)
t = np.arange(fs) / fs
# ir: respuesta al impulso de sala medida; aquí la sustituye un decaimiento sintético de pendiente única.
ir = np.concatenate([np.zeros(10), np.exp(-13.8155 * t / 2.0)])

time, level = decay_curve(ir, fs)                    # curva de Schroeder (0 dB en t = 0)

res = room_parameters(ir, fs, limits=None)           # banda única de banda ancha
print(round(float(res.t30[0]), 2))                   # 1.0  s
print(round(float(res.c80[0]), 2))                   # 3.05 dB
print(round(float(res.d50[0]), 3))                   # 0.499
print(round(float(res.ts[0]) * 1000, 0))             # 72 ms

# Bandas de octava 125 Hz - 4 kHz (por defecto en ISO 3382-1); usa fraction=3 para tercios
octaves = room_parameters(ir, fs)
print(octaves.frequency)                             # ~[126, 251, 501, 1000, 1995, 3981]
print(octaves.t30_valid)                             # indicadores de rango dinámico por banda

octaves.plot()               # barras EDT/T20/T30 + C50/C80 por banda (requiere matplotlib)
decay_curve(ir, fs).plot()   # curva de Schroeder con los ajustes EDT/T20/T30
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — la curva de Schroeder con los ajustes rectos EDT/T20/T30:
decay = decay_curve(ir, fs)          # un DecayCurve (se sigue desempaquetando como time, level)
decay.plot()
plt.show()

# A mano, el decaimiento es solo la curva de Schroeder; marca los niveles de evaluación:
fig, ax = plt.subplots()
ax.plot(time, level, color="#1f77b4", label="Curva de Schroeder")
for db in (-5.0, -25.0, -35.0):      # bordes de la ventana de evaluación T20 / T30
    ax.axhline(db, ls=":", alpha=0.4)
ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Nivel re régimen permanente [dB]")
ax.set_ylim(top=3.0)
ax.legend()
plt.show()
```

</details>

Para este decaimiento de pendiente única, EDT, T20 y T30 devuelven todos
≈ 1,0 s, y los parámetros de energía coinciden con sus formas cerradas
(C80 = 3,05 dB, D50 = 0,499, Ts = 72 ms). Una sala real tiene una pendiente
inicial más pronunciada, así que EDT < T30.

Por debajo de la **frecuencia de Schroeder** $f_s \approx 2000\sqrt{T/V}$
estas estadísticas de caída dejan de contar toda la historia: el campo lo
gobiernan **modos propios** discretos. La simulación siguiente excita la
misma sala rígida de 5 m por 3,5 m en su modo (2,1) y después entre dos
modos; en resonancia un patrón de onda estacionaria con líneas nodales
fijas crece hasta dominar el mapa de presión RMS, fuera de resonancia la
sala sigue respondiendo, pero el campo forzado se mantiene débil y nunca
se organiza en ese patrón nodal (2,1).

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: simulación FDTD 2D de una sala de 5 por 3,5 metros excitada en el modo (2,1) de 84 Hz y en una frecuencia fuera de modo; en resonancia un patrón de onda estacionaria con líneas nodales fijas crece hasta dominar el mapa de presión RMS, fuera de resonancia la respuesta forzada se mantiene débil y desorganizada" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_room_modes_es_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: simulación FDTD 2D de una sala de 5 por 3,5 metros excitada en el modo (2,1) de 84 Hz y en una frecuencia fuera de modo; en resonancia un patrón de onda estacionaria con líneas nodales fijas crece hasta dominar el mapa de presión RMS, fuera de resonancia la respuesta forzada se mantiene débil y desorganizada" style="width:88%"></video>

### Parámetros de `room_parameters()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `ir` | array 1D | cualquiera | no silencioso | Respuesta al impulso medida |
| `fs` | int | Hz | > 0 | Frecuencia de muestreo |
| `limits` | (float, float) o `None` | Hz | por defecto `(125.0, 4000.0)` | Límites de centros de banda; `None` = banda única de banda ancha |
| `fraction` | int | — | `1` (octava, por defecto) / `3` (tercio) | Fracción de ancho de banda |
| `zero_phase` | bool | — | defecto `False` | Filtrado de octava hacia delante y atrás (NOTA de ISO 3382-2, 7.3, que relaja $BT > 16$ a $BT > 4$); elimina el retardo de grupo del filtro antes de la integración inversa y reduce aproximadamente a la mitad el sesgo de T30 corto a 125 Hz (~+4,9 % → +2,4 % con $T$ = 0,2 s). `decay_curve` también lo acepta |

Devuelve un `RoomAcousticsResult`: `frequency` (centros de banda, o `None` en
banda ancha), `edt`/`t20`/`t30` (s), `c50`/`c80` (dB), `d50`, `ts` (s),
`dynamic_range` (dB), los indicadores `edt_valid`/`t20_valid`/`t30_valid`
(ISO 3382-1, 5.3.3: ruido ≥ 25 dB por debajo del pico para EDT, endurecido a
46 dB para T20 y 54 dB para T30 para que el sesgo de compensación de cola de un
valor marcado como válido quede dentro de la DAP del 5 %) y `curvature`
$C = 100\ (T_{30}/T_{20} - 1)$ % (valores por encima del 10 % señalan un
decaimiento no recto). `decay_curve(ir, fs, band=None, fraction=1, zero_phase=False)`
devuelve solo la curva `(time, level)` para una banda o la respuesta de banda ancha.

## 3. Oficinas diáfanas (ISO 3382-3)

La acústica de oficinas diáfanas trata de la **privacidad del habla**: con
qué rapidez el habla de un hablante se desvanece hasta la ininteligibilidad a
medida que uno se aleja. Los niveles y el STI se miden a lo largo de una fila
de puestos de trabajo (al menos 4 posiciones, preferiblemente 6–10), y cuatro
magnitudes de un solo número resumen la sala. La **tasa de decaimiento
espacial** del habla ponderada A es la pendiente del nivel frente a
$\lg(r/r_0)$, escalada a una cifra por duplicación usando solo las posiciones
de 2–16 m,

$$
D_{2,S} = -\lg(2)\ b, \qquad L = a + b\ \lg(r/r_0),\ r_0 = 1\ \text{m},
$$

con **Lp,A,S,4m** leído en la misma recta a 4 m. La **distancia de
distracción** rD (STI = 0,50) y la **distancia de privacidad** rP
(STI = 0,20) provienen de una regresión lineal del STI frente a la distancia.
Las buenas oficinas empujan rD por debajo de ~5 m; las malas dejan el habla
molesta más allá de 10 m.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_open_plan_es.svg" alt="Línea de medición de oficina diáfana ISO 3382-3 desde la fuente a 1 m a lo largo de posiciones de 2 m a 16 m, que alimenta las cuatro magnitudes de índice único D2,S, Lp,A,S,4m, rD y rP" style="width:86%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_open_plan_es_dark.svg" alt="Línea de medición de oficina diáfana ISO 3382-3 desde la fuente a 1 m a lo largo de posiciones de 2 m a 16 m, que alimenta las cuatro magnitudes de índice único D2,S, Lp,A,S,4m, rD y rP" style="width:86%">

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay_es.svg" alt="Decaimiento espacial en oficina abierta: nivel de habla ponderado A y STI frente a la distancia a la fuente en eje logarítmico, con la regresión D2,S, el marcador Lp,A,S,4m a 4 m y los cruces de distancia rD y rP" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay_es_dark.svg" alt="Decaimiento espacial en oficina abierta: nivel de habla ponderado A y STI frente a la distancia a la fuente en eje logarítmico, con la regresión D2,S, el marcador Lp,A,S,4m a 4 m y los cruces de distancia rD y rP" style="width:80%">

```python
import numpy as np
from phonometry import open_plan_metrics

r = np.array([2.0, 4.0, 6.0, 8.0, 12.0, 16.0])       # distancias al hablante (m)
lp = 65.0 - 7.0 * np.log2(r)                          # nivel de habla ponderado A (dB)
sti = 0.70 - 0.03 * r                                 # STI por posición

m = open_plan_metrics(r, lp, sti)
print(round(m.d2s, 1), round(m.lp_as_4m, 1))         # 7.0 dB, 51.0 dB
print(round(m.rd, 1), round(m.rp, 1))                # 6.7 m, 16.7 m
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea: la regresión D2,S reconstruida con los campos del resultado,
# con los cruces rD / rP marcados (la figura superior añade además los puntos
# medidos y el eje de STI):
m.plot()
plt.show()
```

```python
import matplotlib.pyplot as plt

# Decaimiento espacial: Lp,A,S medido frente a la distancia en eje logarítmico,
# la regresión D2,S reconstruida con los campos del resultado, y el STI con los
# cruces rD / rP en un eje gemelo:
b = -m.d2s / np.log10(2.0)                 # pendiente de la regresión frente a lg(r)
a = m.lp_as_4m - b * np.log10(4.0)         # ordenada desde el nivel a 4 m
rr = np.logspace(np.log10(2.0), np.log10(16.0), 100)

fig, ax = plt.subplots()
ax.semilogx(r, lp, "o", label="Lp,A,S medido")
ax.semilogx(rr, a + b * np.log10(rr), "--", label=f"D2,S = {m.d2s:.1f} dB")
ax.plot(4.0, m.lp_as_4m, "D", label=f"Lp,A,S,4m = {m.lp_as_4m:.0f} dB")
ax.set_xlabel("Distancia al hablante r [m]")
ax.set_ylabel("Nivel de habla ponderado A [dB]")
ax.set_xlim(1.8, 20.0)

twin = ax.twinx()
twin.semilogx(r, sti, "s-", color="#2ca02c", label="STI")
twin.axvline(m.rd, ls=":", color="#2ca02c")
twin.axvline(m.rp, ls=":", color="#9467bd")
twin.annotate(f"rD = {m.rd:.1f} m", (m.rd, 0.52))
twin.annotate(f"rP = {m.rp:.1f} m", (m.rp, 0.22))
twin.set_ylabel("STI")
twin.set_ylim(0.0, 1.0)

lines, labels = ax.get_legend_handles_labels()
tl, tlab = twin.get_legend_handles_labels()
ax.legend(lines + tl, labels + tlab, loc="best")
plt.show()
```

</details>

### Parámetros de `open_plan_metrics()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `positions_m` | array 1D | m | ≥ 4 posiciones, todas > 0 | Distancias fuente-receptor |
| `spl_a_speech` | array 1D | dB | misma longitud | Nivel de habla ponderado A `Lp,A,S,n` por posición |
| `sti_values` | array 1D | — | misma longitud | STI por posición (método completo de IEC 60268-16) |

Devuelve un `OpenPlanResult` con `d2s`, `lp_as_4m`, `rd` y `rp`; su
`.plot()` redibuja la regresión de decaimiento espacial del apartado 6.2 a
partir de esos cuatro campos y marca `rd` / `rp`.
`d2s`/`lp_as_4m` son `nan` si menos de dos posiciones caen en 2–16 m;
`rd`/`rp` son `nan` cuando el STI no decrece con la distancia. El STI por
posición puede medirse a su vez con las herramientas STIPA de la
[guía del índice de transmisión del habla](/phonometry/es/guides/speech-transmission/).

## 4. Absorción sonora (ISO 354)

El área de absorción sonora equivalente `A` que gobierna `R'`, `L'n`, la
corrección ambiental `K2` de ISO 3744 y el término de absorción de ISO 3741 se
mide a su vez en una sala reverberante
(ISO 354). Mide el tiempo de reverberación de la sala **vacía** ($T_1$) y de
nuevo **con la muestra de ensayo instalada** ($T_2$); la absorción de la muestra
es la diferencia de las dos áreas de Sabine, y dividiendo por el área cubierta
se obtiene el coeficiente de absorción:

$$
A = \frac{55{,}3\ V}{c\ T} - 4 V m, \qquad
\alpha_s = \frac{A_2 - A_1}{S}, \qquad c = 331 + 0{,}6\ t ,
$$

con $c$ a partir de la temperatura del aire de la sala $t$ en °C (válida
15–30 °C) y $m$ el coeficiente de atenuación en potencia del aire (por defecto
0; convierte un $\alpha$ de ISO 9613-1 en dB/m con `attenuation_from_alpha`).
Como los efectos de borde y difracción pueden dispersar más energía de la que
intercepta el área plana de la muestra, $\alpha_s$ puede superar 1,0 y nunca se
satura (ISO 354 Cláusula 3.7).

```python
import numpy as np
from phonometry import absorption_area, absorption_coefficient

# Tiempos de reverberación en tercios de octava de una sala de 200 m^3, vacía (T1)
# y con una muestra absorbente de 10.8 m^2 instalada (T2).
t1 = np.array([5.0, 4.0, 3.0])
t2 = np.array([3.0, 2.5, 2.0])

a_empty = absorption_area(t1, volume=200.0, temperature=20.0)
print(np.round(a_empty, 2))                    # [ 6.45  8.06 10.75] m^2

alpha = absorption_coefficient(t1, t2, volume=200.0, sample_area=10.8,
                               temperature1=20.0)
print(np.round(alpha, 3))                      # [0.398 0.448 0.498]
```

`T1` y `T2` son exactamente los tiempos de reverberación que devuelve
`room_parameters`, así que una medición de decaimiento ISO 3382-2 de la sala
vacía y tratada fluye directamente a `absorption_coefficient`. Un volumen de
sala por debajo del mínimo de 150 m³ o un área de muestra fuera de 10–12 m²
genera un `AbsorptionWarning` de aviso; el resultado se devuelve igualmente.

### Parámetros de `absorption_area()` / `absorption_coefficient()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `t60` / `t1`, `t2` | array 1D | s | > 0 | Tiempo(s) de reverberación; `t1` vacía, `t2` con la muestra |
| `volume` | float | m³ | > 0 | Volumen de la sala `V` (aviso por debajo de 150 m³) |
| `sample_area` | float | m² | > 0 | Área `S` que cubre la muestra (solo coeficiente) |
| `temperature` / `temperature1`, `temperature2` | float | °C | por defecto `20.0`, 15–30 | Fija `c` vía Ec. (6); `temperature2` por defecto es `temperature1` |
| `speed_of_sound` (`…1`, `…2`) | float, opcional | m/s | > 0 | Sobrescribe la `c` derivada de la temperatura |
| `m` (`m1`, `m2`) | float o array 1D | 1/m | ≥ 0, por defecto `0` | Coeficiente de atenuación en potencia del aire |

`absorption_area()` devuelve el área de absorción sonora equivalente `A` (m²)
con la forma de `t60`; `absorption_coefficient()` devuelve `alpha_s`;
`attenuation_from_alpha(alpha)` convierte un `alpha` de ISO 9613-1 (dB/m) a `m`.

## Véase también

- Aislamiento acústico [en campo](/phonometry/es/guides/insulation-field/),
  [en laboratorio](/phonometry/es/guides/insulation-lab/) y
  [de predicción](/phonometry/es/guides/insulation-prediction/) —
  el aislamiento acústico entre recintos en campo, laboratorio y predicción, y su incertidumbre de medición.
- [Potencia sonora](/phonometry/es/guides/sound-power/) — los métodos de `LW` que
  consumen el área de absorción de ISO 354 (el `K2` de ISO 3744 y el término de
  absorción de ISO 3741).
- [Índice de transmisión del habla](/phonometry/es/guides/speech-transmission/) — la
  medición STI/STIPA que alimenta los `sti_values` de oficinas diáfanas.
- [Sonoridad](/phonometry/es/guides/loudness/) y
  [Métricas de calidad sonora](/phonometry/es/guides/sound-quality/) — la sonoridad, el
  sharpness y las demás métricas de percepción de lo que entrega la sala.
- [Bancos de filtros](/phonometry/es/guides/filter-banks/) — los filtros de octava
  fraccionaria IEC 61260 usados para las curvas de decaimiento por banda y los espectros de
  aislamiento.
- [Niveles](/phonometry/es/guides/levels/) — el promediado en energía y las métricas de
  nivel tras los niveles de las salas emisora/receptora.
- [Teoría](/phonometry/es/reference/theory/rooms-buildings/) — la integración de Schroeder, las ventanas de
  regresión y la derivación de la curva de referencia.
- Referencia de la API: [`room.room_acoustics`](/phonometry/es/reference/api/rooms/room-acoustics/), [`room.room_ir`](/phonometry/es/reference/api/rooms/room-ir/) y [`room.open_plan`](/phonometry/es/reference/api/rooms/open-plan/).

---

**Normas.** ISO 18233:2006 (aplicación de nuevos métodos de medición — la
adquisición de respuestas al impulso por barrido y MLS); ISO 3382-1:2009 e
ISO 3382-2:2008 (tiempo de reverberación y parámetros de sala desde el
decaimiento de Schroeder); ISO 3382-3:2012 (métricas de habla en oficinas
abiertas); ISO 354:2003 (absorción sonora en cámara reverberante). Validado
frente a decaimientos de forma cerrada y las definiciones de parámetros de
las propias normas.

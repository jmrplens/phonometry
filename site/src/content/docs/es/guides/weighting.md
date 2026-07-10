---
title: "Ponderación frecuencial (A, C, G, Z)"
description: "Ponderación frecuencial A/C/Z según IEC 61672-1 (clase 1, con modo de precisión en alta frecuencia) y ponderación G de infrasonido según ISO 7196."
---

Las curvas de ponderación frecuencial simulan la sensibilidad del oído humano.
A, C y Z están especificadas en **IEC 61672-1:2013**; la curva G de
infrasonido, en **ISO 7196:1995**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses_es.png" alt="Curvas de ponderación A, C y Z con zoom de la región positiva de la curva A (+1,27 dB en 2,5 kHz)" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses_es_dark.png" alt="Curvas de ponderación A, C y Z con zoom de la región positiva de la curva A (+1,27 dB en 2,5 kHz)" style="width:80%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import weighting_filter

# Medimos la respuesta de cada curva: ponderamos un impulso unitario
# centrado y tomamos su espectro (búfer de 1 s -> resolución de 1 Hz).
fs = 48000
impulse = np.zeros(fs)
impulse[fs // 2] = 1.0
freqs = np.fft.rfftfreq(fs, 1 / fs)

fig, ax = plt.subplots(figsize=(9, 5))
for curve in ("A", "C", "Z"):
    spectrum = np.fft.rfft(weighting_filter(impulse, fs, curve=curve))
    ax.semilogx(freqs[1:], 20 * np.log10(np.abs(spectrum[1:])), label=curve)
ax.set(xlim=(10, 20000), ylim=(-80, 10),
       xlabel="Frecuencia [Hz]", ylabel="Respuesta [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

* **Ponderación A (`A`):** estándar para ruido ambiental (IEC 61672-1).
* **Ponderación C (`C`):** para presión sonora de pico y ruido de alto nivel.
* **Ponderación Z (`Z`):** ponderación cero, respuesta completamente plana.
* **Ponderación G (`G`):** ponderación de infrasonido según ISO 7196 (ver más abajo).

## 1. De dónde vienen las curvas

Las curvas A y C son líneas isofónicas invertidas, congeladas en filtros:
**A** aproxima la inversa de la histórica línea isofónica de 40 fonios (niveles
bajos, donde el oído descarta los graves con más agresividad) y **C** la más
plana de ~100 fonios (niveles altos). IEC 61672-1:2013 (Anexo E) define ambas
analíticamente a partir de cuatro frecuencias de esquina:

$$
f_1 = 20{,}599\ \text{Hz}, \quad f_2 = 107{,}653\ \text{Hz}, \quad
f_3 = 737{,}862\ \text{Hz}, \quad f_4 = 12194{,}217\ \text{Hz}
$$

C es un paso-banda con polos dobles en $f_1$ y $f_4$ (2 ceros en el origen);
A añade los polos $f_2$ y $f_3$ (4 ceros), y por eso sigue cayendo en los
medios-graves. Ambas se normalizan a exactamente 0 dB en 1 kHz. Z es la
ausencia de ponderación. La derivación completa de polos y ceros está en la
página de [Teoría](/phonometry/es/reference/theory/).

## 2. Uso básico

```python
import numpy as np
from phonometry import weighting_filter

# recording: una captura de micrófono calibrada (Pa) — grabada con tu cadena de medición. Sintetizada aquí para que la guía funcione por sí sola.
fs = 48000
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# Aplicar ponderación A a la señal cruda
weighted_signal = weighting_filter(recording, fs, curve='A')

# Aplicar ponderación C para análisis de picos
c_weighted_signal = weighting_filter(recording, fs, curve='C')
```

## 3. Infrasonido: ponderación G (ISO 7196)

La **ponderación frecuencial G** (ISO 7196:1995) valora el infrasonido igual que
la ponderación A valora el ruido audible. Se define por una configuración de
polos y ceros con ganancia de 0 dB en 10 Hz, sube a 12 dB/octava entre 1 Hz y
20 Hz (siguiendo el crecimiento abrupto de la percepción en esa banda) y cae a
24 dB/octava fuera de ella. Úsala con fuentes con energía significativa por
debajo de 20 Hz (aerogeneradores, climatización, voladuras):

```python
from phonometry import weighting_filter

# Usa `recording` y `fs` del snippet anterior.
g_weighted = weighting_filter(recording, fs, curve='G')
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/g_weighting_response_es.png" alt="Respuesta en frecuencia de la ponderación G de 0,1 Hz a 1 kHz con los valores nominales de la Tabla 2 de ISO 7196 superpuestos" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/g_weighting_response_es_dark.png" alt="Respuesta en frecuencia de la ponderación G de 0,1 Hz a 1 kHz con los valores nominales de la Tabla 2 de ISO 7196 superpuestos" style="width:80%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import weighting_filter

# Medimos la respuesta G: ponderamos un impulso unitario centrado y
# tomamos su espectro. Un búfer largo da la resolución que necesita el
# rango de infrasonido (20 s -> 0,05 Hz).
fs = 4000
impulse = np.zeros(20 * fs)
impulse[impulse.size // 2] = 1.0
freqs = np.fft.rfftfreq(impulse.size, 1 / fs)
spectrum = np.fft.rfft(weighting_filter(impulse, fs, curve="G"))

fig, ax = plt.subplots(figsize=(9, 5))
ax.semilogx(freqs[1:], 20 * np.log10(np.abs(spectrum[1:])))
ax.plot(10, 0, "o", color="tab:red", label="0 dB en 10 Hz")
ax.set(xlim=(0.1, 1000), ylim=(-90, 15),
       xlabel="Frecuencia [Hz]", ylabel="Respuesta de la ponderación G [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

La implementación sigue exactamente los polos/ceros de la Tabla 1 de ISO 7196 y
se verifica en CI contra todos los valores nominales de respuesta de la Tabla 2
(0,25 Hz a 315 Hz). `WeightingFilter(fs, "G")` admite el mismo procesado
multicanal y por bloques que A/C. Los niveles medidos con la curva G se
expresan como L<sub>pG</sub> (o L<sub>Geq</sub> para el nivel equivalente).

## 4. Parámetros de `weighting_filter()` / `WeightingFilter`

| Parámetro | Tipo | Unidades | Rango / por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D o 2D | cualquiera | no vacío | 2D es `[channels, samples]` |
| `fs` | int | Hz | > 0 | |
| `curve` | str | — | `'A'` (por defecto), `'C'`, `'G'`, `'Z'` | `'G'` según ISO 7196 (infrasonido); `'Z'` es un bypass |
| `high_accuracy` | bool | — | por defecto `True` (función); en la clase, `None` se resuelve a `not stateful` | Sobremuestreo interno (hasta 8×, ≥ 144 kHz a frecuencias de audio habituales, p. ej. entrada de 96 kHz ×2) que mantiene A/C en clase 1 hasta 16 kHz; con G se ignora en silencio (su rango de 0,25–315 Hz ya es exacto con el diseño simple) |
| `stateful` | bool (solo clase) | — | por defecto `False` | Conserva el estado del filtro entre bloques (streaming) |
| `steady_ic` | bool (solo clase) | — | por defecto `False` | Condiciones iniciales estacionarias (sin transitorio de arranque) |

## 5. Objeto de filtro reutilizable

Si ponderas muchas señales con los mismos parámetros, diseña el filtro una sola vez:

```python
from phonometry import WeightingFilter

# Usa `recording` y `fs` del snippet anterior.
wf = WeightingFilter(fs, "A")
signals = [recording]                # tu lote de grabaciones
for recording in signals:
    weighted = wf.filter(recording)
```

## 6. Precisión en alta frecuencia (`high_accuracy`)

Un diseño con transformación bilineal simple comprime la respuesta cerca de
Nyquist: a fs = 48 kHz el error de la curva A a 12,5 kHz alcanza −2,7 dB, fuera
de la tolerancia **clase 1** de IEC 61672-1 (+2,0/−2,5 dB).

Por defecto (`high_accuracy=True`), phonometry diseña y ejecuta el filtro de
ponderación a una frecuencia interna sobremuestreada (≥ 144 kHz) y diezma de
vuelta, manteniendo la respuesta dentro de las tolerancias de clase 1 hasta
16 kHz (error ≈ −0,5 dB a 12,5 kHz para fs = 48 kHz).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf_es.png" alt="Precisión en alta frecuencia de la ponderación A a 48 kHz: curva analítica frente a bilineal simple y diseño sobremuestreado, con error" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf_es_dark.png" alt="Precisión en alta frecuencia de la ponderación A a 48 kHz: curva analítica frente a bilineal simple y diseño sobremuestreado, con error" style="width:80%">

*El diseño bilineal simple (rojo) cruza la tolerancia de clase 1 cerca de
12,5 kHz; el diseño sobremuestreado (azul) se mantiene junto a la curva analítica.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import weighting_filter

# Respuesta medida de ambos diseños a fs = 48 kHz: ponderamos un impulso
# unitario centrado y tomamos su espectro...
fs = 48000
impulse = np.zeros(fs)
impulse[fs // 2] = 1.0
freqs = np.fft.rfftfreq(fs, 1 / fs)[1:]

# ...frente a la curva A analítica de IEC 61672-1 construida con las
# cuatro frecuencias de esquina de la sección 1, normalizada a 0 dB en 1 kHz.
f1, f2, f3, f4 = 20.599, 107.653, 737.862, 12194.217
gain = (f4**2 * freqs**4) / ((freqs**2 + f1**2)
        * np.sqrt((freqs**2 + f2**2) * (freqs**2 + f3**2))
        * (freqs**2 + f4**2))
analytic = 20 * np.log10(gain / gain[np.argmin(np.abs(freqs - 1000))])

fig, ax = plt.subplots(figsize=(9, 5))
ax.semilogx(freqs, analytic, "k--", label="Analítica (IEC 61672-1)")
for high_accuracy, label in ((False, "Bilineal simple"),
                             (True, "Sobremuestreado (por defecto)")):
    weighted = weighting_filter(impulse, fs, curve="A",
                                high_accuracy=high_accuracy)
    response = 20 * np.log10(np.abs(np.fft.rfft(weighted)))[1:]
    ax.semilogx(freqs, response, label=label)
ax.set(xlim=(1000, 20000), ylim=(-12, 3),
       xlabel="Frecuencia [Hz]", ylabel="Respuesta de la ponderación A [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

- `high_accuracy=False` restaura el comportamiento bilineal clásico.
- El **procesado por bloques (stateful)** usa siempre el diseño clásico: el
  remuestreo FIR interno es incompatible con la continuidad entre bloques. Pasar
  `high_accuracy=True` junto con `stateful=True` lanza un `ValueError`.

```python
from phonometry import WeightingFilter, weighting_filter

# Usa `recording` y `fs` del snippet anterior.
# Comportamiento clásico explícito
y = weighting_filter(recording, fs, curve="A", high_accuracy=False)

# Procesado por bloques con estado (diseño clásico, estado entre bloques)
wf = WeightingFilter(fs, "A", stateful=True)
blocks = [recording]                 # tu secuencia de bloques de señal
for block in blocks:
    weighted = wf.filter(block)
```

Consulta [Procesado por bloques](/phonometry/es/guides/block-processing/) para
el flujo en streaming y [Teoría](/phonometry/es/reference/theory/) para las
definiciones analíticas de las curvas.

---

**Normas.** IEC 61672-1:2013, *Electroacoustics — Sound level meters —
Part 1: Specifications* — las curvas de ponderación frecuencial A, C y Z (la
definición analítica del Anexo E a partir de cuatro frecuencias de esquina,
normalizadas a 0 dB en 1 kHz) y las tolerancias de clase 1 que el diseño
`high_accuracy` mantiene hasta 16 kHz. ISO 7196:1995, *Acoustics —
Frequency-weighting characteristic for infrasound measurements* — la
definición de polos y ceros de la ponderación G (Tabla 1), verificada frente a
todos los valores nominales de respuesta de la Tabla 2 (0,25 Hz a 315 Hz).

---
title: "Tonos discretos prominentes (ECMA-418-1)"
description: "La relación tono-ruido y la relación de prominencia de ECMA-418-1: veredictos FFT de prominencia para tonos discretos frente a criterios dependientes de la frecuencia, con las posiciones de medida de ECMA-74."
---

Los componentes tonales del ruido de maquinaria molestan mucho más de lo que
sugiere su nivel. ECMA-418-1:2024 (referenciada por el Anexo D de ECMA-74)
define dos métodos FFT para decidir si un tono discreto es *prominente*:
`tone_to_noise_ratio()` compara el nivel del tono con el ruido enmascarante de
su banda crítica (apartado 11) y `prominence_ratio()` compara la banda crítica
centrada en el tono con las dos bandas contiguas (apartado 12). Ambos devuelven
un veredicto estructurado frente a los criterios de prominencia dependientes de
la frecuencia.

## 1. Relación tono-ruido y relación de prominencia

```python
import numpy as np
from phonometry import tone_to_noise_ratio, prominence_ratio

fs = 48000
rng = np.random.default_rng(0)
t = np.arange(fs) / fs
x = np.sin(2 * np.pi * 1000 * t) + 0.05 * rng.standard_normal(fs)  # tono de 1 kHz en ruido
tnr = tone_to_noise_ratio(x, fs)            # pico más alto, o tone_freq=...
pr = prominence_ratio(x, fs, tone_freq=1000.0)
print(tnr.ratio_db, tnr.criterion_db, tnr.prominent)
```

Los métodos se apoyan en la **banda crítica** — el ancho de banda de análisis
del oído, $\Delta f_c = 25 + 75\ [1 + 1{,}4(f/1000)^2]^{0{,}69}$ Hz (162 Hz a
1 kHz): a un tono solo lo enmascara el ruido que hay *dentro* de su banda
crítica, así que ambos métodos se centran en esa banda y no en todo el
espectro, pero la usan de forma distinta. La relación tono-ruido trabaja
dentro de la banda, separando sus líneas espectrales en tono y ruido y
restando sus niveles (apartado 11, Fórmulas 9–11); la relación de prominencia,
en cambio, compara la banda *completa* centrada en el tono con la media de sus
dos bandas críticas contiguas (apartado 12, Fórmula 23):

$$
\mathrm{TNR} = L_t - L_n, \qquad
\mathrm{PR} = 10\,\lg\!\frac{W_M}{\tfrac{1}{2}(W_L + W_U)}\ \text{dB},
$$

donde $L_t$ es el nivel del tono (la suma en energía de las líneas tonales por
encima de la línea de base entre los bordes de la banda, Fórmula 9), $L_n$ el
nivel del ruido enmascarante que queda en la banda crítica, reescalado al ancho
de banda crítico completo (Fórmulas 10–11), y $W_M$, $W_L$, $W_U$ las potencias
de las bandas críticas central, inferior y superior (por debajo de
$f_t = 171{,}4$ Hz la banda inferior truncada se reescala a un ancho de banda
de 100 Hz, Fórmula 24).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_es.svg" alt="Espectro promediado de un tono en ruido con la banda crítica sombreada y la relación tono-ruido anotada frente a su criterio de prominencia" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_es_dark.svg" alt="Espectro promediado de un tono en ruido con la banda crítica sombreada y la relación tono-ruido anotada frente a su criterio de prominencia" style="width:80%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch
from phonometry import tone_to_noise_ratio

fs = 48000
rng = np.random.default_rng(21)
t = np.arange(30 * fs) / fs
x = (np.sqrt(2) * 0.1 * np.sin(2 * np.pi * 1000 * t)
     + 0.05 * rng.standard_normal(t.size))
res = tone_to_noise_ratio(x, fs)

# Espectro Hann promediado a 1 Hz (el front-end del apartado 11.1) y la banda
# crítica en torno al tono detectado (bordes aproximados como +/- dfc/2):
f, p = welch(x, fs, window="hann", nperseg=fs, scaling="spectrum")
dfc = 25 + 75 * (1 + 1.4 * (res.frequency / 1000) ** 2) ** 0.69
sel = (f > 700) & (f < 1400)
plt.plot(f[sel], 10 * np.log10(p[sel]))
plt.axvspan(res.frequency - dfc / 2, res.frequency + dfc / 2, alpha=0.15)
plt.title(f"TNR = {res.ratio_db:.1f} dB (criterio {res.criterion_db:.1f} dB)")
plt.xlabel("Frecuencia [Hz]"); plt.ylabel("Potencia por bin [dB]")
plt.show()
```

</details>

Un TNR igual o superior a $8 + 8{,}33\log_{10}(1000/f_t)$ dB por debajo de
1 kHz (8 dB constantes para $f_t \ge 1$ kHz) clasifica el tono como
*prominente*; el criterio del PR es $9 + 10\log_{10}(1000/f_t)$ dB por debajo
de 1 kHz y 9 dB a partir de ahí, aplicado igualmente con $\ge$. Las
frecuencias bajas reciben umbrales más altos porque unas bandas relativamente
más anchas enmascaran más.

**Cuando los dos ratios discrepan.** Cerca de los criterios los veredictos
pueden diferir, porque cada ratio es frágil en una situación distinta. El TNR
tiene que *separar* primero las líneas de la banda crítica en tonales y de
ruido, así que se degrada cuando esa separación es ambigua — un tono montado
sobre una pendiente abrupta de ruido, o componentes muy juntos cuyas faldas se
solapan. El PR no necesita separación alguna, lo que lo convierte en la opción
robusta y automatizable cuando **varios tonos comparten la banda crítica**
(todos caen en $W_M$); a cambio lee de menos cuando una banda *vecina* también
lleva un tono (las bandas laterales dejan de ser ruido) y se sesga en espectros
de pendiente pronunciada, donde las dos bandas laterales ya no estiman el
enmascaramiento en el tono. En la práctica: prefiere el TNR para un tono limpio
y aislado, el PR para complejos multitono que comparten banda, y presenta ambos
cuando ronden sus criterios.

## 2. Dónde medir (ECMA-74) y práctica

ECMA-74 (que delega la evaluación tonal en ECMA-418-1) también fija dónde medir alrededor de un equipo — solo contexto: phonometry implementa las evaluaciones de ECMA-418-1, no el procedimiento de medida del Anexo D de ECMA-74:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_tonality_positions_es.svg" alt="Posiciones de medida de emisión ECMA-74: micrófono del operador sentado a 0,25 m y 1,20 m, y las cuatro posiciones de observador a 1 m" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_tonality_positions_es_dark.svg" alt="Posiciones de medida de emisión ECMA-74: micrófono del operador sentado a 0,25 m y 1,20 m, y las cuatro posiciones de observador a 1 m" style="width:92%">

Los tonos secundarios próximos en la misma banda crítica se combinan según el
apartado 11.6; para complejos armónicos evalúa cada componente (`tone_freq=`).
Ambos métodos trabajan sobre espectros promediados RMS con ventana Hann y no
necesitan calibración absoluta (los ratios son diferencias de nivel).

### Parámetros de `tone_to_noise_ratio()` / `prominence_ratio()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D | cualquiera (vale sin calibrar) | ≥ `fs/resolution_hz` muestras | Los ratios son diferencias de nivel: la calibración se cancela |
| `fs` | int | Hz | > 0 | |
| `tone_freq` | float, opcional | Hz | 89,1–11 200; por defecto `None` | `None` evalúa el pico más alto del rango de interés |
| `resolution_hz` | float | Hz | > 0; por defecto `1.0` | La banda del tono debe quedar dentro del 15 % de la banda crítica (apartado 11.2) |

Ambos devuelven un `ToneAssessment(frequency, ratio_db, criterion_db, prominent)`.

## Véase también

- [Niveles](/phonometry/es/guides/levels/) — los niveles de evaluación de
  ISO 1996-1 cuyos ajustes tonales (Tabla A.1) estos veredictos de prominencia
  justifican objetivamente.
- [Métricas de calidad sonora](/phonometry/es/guides/sound-quality/) — la tonalidad
  psicoacústica T en tu_HMS de ECMA-418-2, la contraparte de modelo auditivo de
  estos ratios FFT.
- [Prominencia de sonidos impulsivos](/phonometry/es/guides/impulse-prominence/) —
  la contraparte NT ACOU 112 para el carácter impulsivo (en lugar de tonal).
- [Teoría](/phonometry/es/reference/theory/perception/) — el modelo de banda crítica y la
  derivación de los criterios.
- Referencia de la API: [`psychoacoustics.tonality`](/phonometry/es/reference/api/psychoacoustics/tonality/).

## Referencias

- Ecma International. (2024). *ECMA-418-1: Psychoacoustic metrics for ITT
  equipment — Part 1: Prominent discrete tones* (3.ª ed.).
  [PDF gratuito](https://ecma-international.org/wp-content/uploads/ECMA-418-1_3rd_edition_december_2024.pdf).
  La norma implementada, de descarga gratuita: los métodos TNR (apartado 11) y
  PR (apartado 12), el modelo de banda crítica y los criterios de prominencia
  de la sección 1.
- Ecma International. (2025). *ECMA-74: Measurement of airborne noise emitted
  by information technology and telecommunications equipment* (22.ª ed.).
  [PDF gratuito](https://ecma-international.org/wp-content/uploads/ECMA-74_22nd_edition_december_2025.pdf).
  La norma de emisión matriz, de descarga gratuita: las posiciones de medida de
  operador y observador de la sección 2, con el Anexo D delegando la evaluación
  de tonos en ECMA-418-1.

---

**Normas.** ECMA-418-1:2024 (3.ª edición), *Psychoacoustic metrics for ITT
equipment — Part 1: Prominent discrete tones* — la relación tono-ruido
(apartado 11), la relación de prominencia (apartado 12), el modelo de banda
crítica y los criterios de prominencia dependientes de la frecuencia.

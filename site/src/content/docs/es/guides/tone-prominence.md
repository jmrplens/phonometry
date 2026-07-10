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
del oído, $\Delta f_c = 25 + 75\ [1 + 1.4(f/1000)^2]^{0.69}$ Hz (162 Hz a
1 kHz): a un tono solo lo enmascara el ruido que hay *dentro* de su banda
crítica, así que ambos ratios comparan el tono exactamente con ese ruido, no
con todo el espectro.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_es.png" alt="Espectro promediado de un tono en ruido con la banda crítica sombreada y la relación tono-ruido anotada frente a su criterio de prominencia" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_es_dark.png" alt="Espectro promediado de un tono en ruido con la banda crítica sombreada y la relación tono-ruido anotada frente a su criterio de prominencia" style="width:80%">

Un TNR por encima de $8 + 8.33\log_{10}(1000/f_t)$ dB (8 dB de 1 kHz hacia
arriba) clasifica el tono como *prominente*; el criterio del PR es
$9 + 10\log_{10}(1000/f_t)$ dB. Las frecuencias bajas reciben umbrales más
altos porque unas bandas relativamente más anchas enmascaran más.

## 2. Dónde medir (ECMA-74) y práctica

ECMA-74 (que delega la evaluación tonal en ECMA-418-1) también fija dónde medir alrededor de un equipo:

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
- [Psicoacústica](/phonometry/es/guides/psychoacoustics/) — la tonalidad
  psicoacústica T en tu_HMS de ECMA-418-2, la contraparte de modelo auditivo de
  estos ratios FFT.
- [Prominencia de sonidos impulsivos](/phonometry/es/guides/impulse-prominence/) —
  la contraparte NT ACOU 112 para el carácter impulsivo (en lugar de tonal).
- [Teoría](/phonometry/es/reference/theory/) — el modelo de banda crítica y la
  derivación de los criterios.

---

**Normas.** ECMA-418-1:2024 (3.ª edición), *Psychoacoustic metrics for ITT
equipment — Part 1: Prominent discrete tones* — la relación tono-ruido
(apartado 11), la relación de prominencia (apartado 12), el modelo de banda
crítica y los criterios de prominencia dependientes de la frecuencia; el
Anexo D de ECMA-74 — las posiciones de medida de emisión, que delegan la
evaluación tonal en ECMA-418-1.

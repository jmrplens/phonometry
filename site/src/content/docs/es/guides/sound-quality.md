---
title: "Métricas de calidad sonora"
description: "Sharpness en acum (DIN 45692) y la tonalidad (tu_HMS) y la aspereza (asper) del modelo de Sottek de ECMA-418-2."
---

Dos sonidos igual de sonoros pueden diferir aún en cuán *afilados*, cuán
*tonales* o cuán *ásperos* son. Esta página cubre las métricas de calidad
sonora que complementan a la sonoridad: el sharpness (DIN 45692) y la
tonalidad y la aspereza de ECMA-418-2 del modelo de Sottek. La sonoridad,
incluida la de ECMA-418-2 que comparte el mismo front-end auditivo, está en
[Sonoridad](/phonometry/es/guides/loudness/).

## Sharpness en acum (DIN 45692)

Dos sonidos pueden ser igual de sonoros y aun así uno se percibe más
"afilado" — siseante, metálico — porque su sonoridad se sitúa más arriba en la
escala Bark. El sharpness es el primer momento del patrón de sonoridad
específica ponderado por g(z):

$$
S = k\ \frac{\int_0^{24} N'(z)\ g(z)\ z\ dz}{\int_0^{24} N'(z)\ dz}\ \text{acum}
$$

con $g(z) = 1$ hasta 15,8 Bark y creciendo exponencialmente a partir de ahí, y
$k$ normalizada para que el sonido de referencia — ruido de ancho de banda
crítico a 1 kHz, 60 dB — sea exactamente **1,00 acum** (DIN 45692 apartado 6;
la $k = 0{,}108$ derivada queda dentro de la ventana normativa 0,105–0,115).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting_es.svg" alt="Ponderación de nitidez g(z) de DIN 45692 frente a la razón de banda crítica en eje logarítmico, comparando las curvas DIN, von Bismarck y Aures con los codos de 15,8 y 15 Bark marcados" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting_es_dark.svg" alt="Ponderación de nitidez g(z) de DIN 45692 frente a la razón de banda crítica en eje logarítmico, comparando las curvas DIN, von Bismarck y Aures con los codos de 15,8 y 15 Bark marcados" style="width:80%">

```python
import numpy as np
from phonometry import sharpness_din

# Una grabación y su calibración para que la guía funcione por sí sola
fs = 48000
x = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)   # cualquier grabación (unidades digitales)
sens = 1.0                                                # calibration_factor a pascales

s = sharpness_din(x, fs, calibration_factor=sens)      # acum
s_aures = sharpness_din(x, fs, method="aures")          # variante del Anexo B
```

CI verifica los valores objetivo de la Tabla A.2 (desde 0,38 acum a 250 Hz
hasta 2,82 acum a 4 kHz) dentro de la tolerancia del 5 % / 0,05 acum de la
norma.

## Tonalidad (ECMA-418-2)

Una componente tonal — un silbido, el tono de paso de pala de un ventilador —
destaca incluso a bajo nivel. ECMA-418-2 la cuantifica a partir de la **función
de autocorrelación** (ACF) de la señal rectificada de cada banda: una componente
periódica (tonal) mantiene una ACF alta a retardo no nulo, y la relación entre
sonoridad tonal y de ruido impulsa la tonalidad específica T′(z). El valor único
T se da en **tu_HMS**, calibrado de modo que un tono de 1 kHz/40 dB sea
≈ 1 tu_HMS; el resultado también sigue la frecuencia tonal f_ton por banda.

```python
import numpy as np
from phonometry import tonality_ecma

fs = 48000
t = np.arange(int(1.2 * fs)) / fs
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * t)

res = tonality_ecma(x, fs, field="free")
peak = int(np.argmax(res.specific_tonality))
print(f"T = {res.tonality:.3f} tu_HMS")                    # 1.000 tu_HMS
print(f"f_ton = {res.tonal_frequencies[peak]:.0f} Hz")     # 999 Hz

res.plot()   # tonalidad específica media T'(z) + T(l) dependiente del tiempo
```

### Parámetros de `tonality_ecma()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | array 1D | Pa | no vacío | Señal de presión calibrada |
| `fs` | float | Hz | > 0 | Se remuestrea a 48 kHz internamente si es necesario |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` | Filtro del oído externo/medio |
| `f_low` | float, opcional | Hz | por defecto `None` | Borde inferior de una banda de usuario para la búsqueda de T(l) |
| `f_high` | float, opcional | Hz | por defecto `None` | Borde superior de la banda de usuario |

Devuelve un `EcmaTonality`: `tonality` (T, tu_HMS), `specific_tonality`
(T′(z), 53 bandas), `bark`, `centre_frequencies`, `tonal_frequencies`
(f_ton,z), `time`, `tonality_vs_time` (T(l)), `tonal_frequency_vs_time`,
`field`.

## Aspereza (ECMA-418-2) — capacidad nueva

La aspereza es la sensación áspera y zumbante de una modulación de amplitud
rápida (aproximadamente 20–300 Hz, con máximo cerca de 70 Hz) — la cualidad de
un ralentí diésel o de un altavoz distorsionado. Es una **métrica nueva** en
phonometry. ECMA-418-2 extrae la envolvente de cada banda, pondera su espectro
de modulación por la tasa y la profundidad de modulación, y correlaciona la
modulación entre bandas; el resultado R se da en **asper**. El sonido de
referencia (portador de 1 kHz, modulado en amplitud al 100 % a 70 Hz, nivel
global de 60 dB SPL) se define como 1 asper — esta implementación de sala
limpia devuelve 0,9999 asper con la constante de calibración tabulada c_R
(Fórmula 104) usada **sin** reajustarla hacia atrás al objetivo.

```python
import numpy as np
from phonometry import roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
x = (1.0 + np.cos(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 1000 * t)
x *= 2e-5 * 10 ** (60 / 20) / np.sqrt(np.mean(x**2))   # nivel global de 60 dB SPL

res = roughness_ecma(x, fs, field="free")
print(f"R = {res.roughness:.4f} asper")   # 0.9999 asper (referencia: 1 asper)

res.plot()   # aspereza R(l50) dependiente del tiempo + mapa de calor de aspereza específica
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo_es.svg" alt="Demostración de calidad sonora ECMA-418-2: un sonido tonal puntúa alta tonalidad y aspereza casi nula, mientras que un sonido modulado en amplitud a 70 Hz puntúa alta aspereza y baja tonalidad" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo_es_dark.svg" alt="Demostración de calidad sonora ECMA-418-2: un sonido tonal puntúa alta tonalidad y aspereza casi nula, mientras que un sonido modulado en amplitud a 70 Hz puntúa alta aspereza y baja tonalidad" style="width:80%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import tonality_ecma, roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
amp = np.sqrt(2) * 2e-5 * 10 ** (60 / 20)

# Un tono puro (tonal, suave) frente a un tono modulado en amplitud a 70 Hz
# (áspero), ambos normalizados a un nivel global de 60 dB SPL:
tone = amp * np.sin(2 * np.pi * 1000 * t)
rough = (1.0 + np.cos(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 1000 * t)
rough *= 2e-5 * 10 ** (60 / 20) / np.sqrt(np.mean(rough**2))

scores = {
    "Tono puro": (tonality_ecma(tone, fs).tonality, roughness_ecma(tone, fs).roughness),
    "Tono AM 70 Hz": (tonality_ecma(rough, fs).tonality, roughness_ecma(rough, fs).roughness),
}
labels = list(scores)
tonal = [scores[k][0] for k in labels]
rough_v = [scores[k][1] for k in labels]
xpos = np.arange(len(labels))
fig, ax = plt.subplots()
ax.bar(xpos - 0.2, tonal, 0.4, label="Tonalidad [tu_HMS]")
ax.bar(xpos + 0.2, rough_v, 0.4, label="Aspereza [asper]")
ax.set_xticks(xpos)
ax.set_xticklabels(labels)
ax.legend()
plt.show()
```

</details>

### Parámetros de `roughness_ecma()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | array 1D | Pa | no vacío | Señal de presión calibrada |
| `fs` | float | Hz | > 0 | Se remuestrea a 48 kHz internamente si es necesario |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` | Filtro del oído externo/medio |

Devuelve un `EcmaRoughness`: `roughness` (R, asper, el percentil 90 de
R(l50)), `specific_roughness` (R′(z), 53 bandas), `bark`, `centre_frequencies`,
`time`, `roughness_vs_time` (R(l50)), `specific_roughness_vs_time`
(array de (n_times, 53)), `field`.

Consulta [Tonos discretos prominentes](/phonometry/es/guides/tone-prominence/)
para los veredictos TNR/PR de ECMA-418-1, el
[índice de transmisión del habla](/phonometry/es/guides/speech-transmission/)
para el STI/STIPA, y [Teoría](/phonometry/es/reference/theory/perception/) para la
matemática subyacente.

## Referencias

- Fastl, H., & Zwicker, E. (2007). *Psychoacoustics: Facts and models*
  (3.ª ed.). Springer.
  [doi:10.1007/978-3-540-68888-4](https://doi.org/10.1007/978-3-540-68888-4).
  La psicoacústica de las sensaciones que cuantifica esta página: el énfasis
  en alta frecuencia tras la agudeza y la percepción de modulación rápida
  tras la aspereza.

## Normas

DIN 45692:2009, *Messtechnische Simulation der Hörempfindung
Schärfe* — sharpness en acum (ponderación del apartado 6, variantes von
Bismarck y Aures del Anexo B, objetivos de la Tabla A.2). ECMA-418-2:2025,
*Psychoacoustic metrics for ITT equipment — Part 2 (methods for describing
human perception based on the Sottek Hearing Model)* — la tonalidad (tu_HMS) y
la aspereza (asper) del modelo de Sottek.

## Véase también

- Referencia de la API: [`psychoacoustics.sharpness`](/phonometry/es/reference/api/psychoacoustics/sharpness/), [`psychoacoustics.tonality_ecma`](/phonometry/es/reference/api/psychoacoustics/tonality-ecma/) y [`psychoacoustics.roughness_ecma`](/phonometry/es/reference/api/psychoacoustics/roughness-ecma/).

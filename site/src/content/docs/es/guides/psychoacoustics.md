---
title: "Psicoacústica e inteligibilidad del habla"
description: "Sonoridad de Zwicker (ISO 532-1), sharpness (DIN 45692) y el índice de transmisión del habla STI/STIPA (IEC 60268-16)."
---

Las métricas de nivel dicen cuánta *presión sonora* hay; las métricas
psicoacústicas dicen qué *percibe* realmente quien escucha. Esta página cubre
la sonoridad (ISO 532-1), el sharpness (DIN 45692) y el índice de transmisión
del habla (IEC 60268-16).

## Sonoridad en sonos (ISO 532-1, Zwicker)

Los decibelios comprimen la percepción: 10 dB más se leen como *el doble de
sonoro*, y dos sonidos con el mismo dB(A) pueden diferir audiblemente según
cómo se reparta su energía entre las **bandas críticas** del oído. El método de
Zwicker modela explícitamente la cadena auditiva — transmisión del oído
externo/medio, análisis en bandas críticas sobre la escala de 24 Bark,
pendientes de enmascaramiento dependientes del nivel — y produce la
**sonoridad N en sonos**, una escala de razón: 4 sonos es el doble de sonoro
que 2 sonos. Por definición, un tono de 1 kHz a 40 dB SPL es 1 sono, y cada
+10 fonios duplica el valor en sonos.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_pattern_es.png" alt="Patrones de sonoridad específica sobre la escala Bark para un sonido de banda estrecha de 1 kHz y un sonido de banda ancha con el mismo nivel de banda" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_pattern_es_dark.png" alt="Patrones de sonoridad específica sobre la escala Bark para un sonido de banda estrecha de 1 kHz y un sonido de banda ancha con el mismo nivel de banda" style="width:80%">

*Mismo nivel de banda, sonoridad muy distinta: la energía repartida entre
muchas bandas críticas (rojo) suma muchos más sonos que el mismo nivel
concentrado en una sola banda (azul). El área bajo N'(z) es la sonoridad
total.*

```python
from phonometry import loudness_zwicker, loudness_zwicker_from_spectrum

# Desde una señal calibrada (Pa): estacionaria o variable en el tiempo
res = loudness_zwicker(x, fs, field="free", calibration_factor=sens)
print(f"N = {res.loudness:.1f} sone  ({res.loudness_level:.0f} phon)")

# Señales variables en el tiempo: la sonoridad percentil N5 es el
# estándar para informes
res = loudness_zwicker(x, fs)          # stationary=False (por defecto)
print(res.n5, res.n10, res.loudness)   # N5, N10, Nmax

# Desde 28 niveles de tercio de octava (25 Hz .. 12.5 kHz)
res = loudness_zwicker_from_spectrum(levels_28, field="diffuse")
```

La implementación es un port de sala limpia del **programa de referencia
normativo** de la norma (Anexo A.4): las doce tablas de datos son exactas
dígito a dígito y el conjunto completo de validación del Anexo B se ejecuta en
CI — el caso de prueba estacionario reproduce el valor publicado hasta el
último dígito impreso, y las trazas N(t) de los pulsos de tono se mantienen
dentro de la banda de tolerancia del 5 % por muestra que fija la norma.

### Parámetros de `loudness_zwicker()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D | Pa (tras calibración) | ≥ 8 ms a 48 kHz | Se remuestrea internamente a 48 kHz si es necesario |
| `fs` | int | Hz | > 0 | |
| `field` | str | — | `'free'` (por defecto) / `'diffuse'` | Corrección de campo sonoro (Tabla A.5) |
| `stationary` | bool | — | por defecto `False` | `True`: un único N a partir del espectro promediado |
| `calibration_factor` | float | Pa por unidad digital | por defecto `1.0` | De `calculate_sensitivity()` |

Devuelve un dataclass `ZwickerLoudness`: `loudness` (N, sonos),
`loudness_level` (fonios), `specific` (N′(z), 240 bins de 0,1 Bark) y, para los
análisis variables en el tiempo, `n5`, `n10`, `time`, `loudness_vs_time`
(traza a 500 Hz).

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
la $k = 0.108$ derivada queda dentro de la ventana normativa 0,105–0,115).

```python
from phonometry import sharpness_din

s = sharpness_din(x, fs, calibration_factor=sens)      # acum
s_aures = sharpness_din(x, fs, method="aures")          # variante del Anexo B
```

CI verifica los valores objetivo de la Tabla A.2 (desde 0,38 acum a 250 Hz
hasta 2,82 acum a 4 kHz) dentro de la tolerancia del 5 % / 0,05 acum de la
norma.

## Índice de transmisión del habla (IEC 60268-16)

La reverberación y el ruido no amortiguan el habla de manera uniforme —
emborronan su *envolvente*: las modulaciones lentas de intensidad
(0,63–12,5 Hz) que transportan las sílabas. El STI cuantifica cuánta de esa
modulación sobrevive de la boca al oído, por banda de octava, como la
**función de transferencia de modulación (MTF)** m(F). Un canal tipo delta
mantiene m = 1 (STI = 1); la reverberación filtra paso-bajo la envolvente
siguiendo la forma cerrada de Schroeder, y el ruido estacionario la escala:

$$
m(F) = \frac{1}{\sqrt{1 + \left(2\pi F\ \frac{T_{60}}{13.8}\right)^2}}
\cdot \frac{1}{1 + 10^{-\mathrm{SNR}/10}}
$$

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60_es.png" alt="STI frente al tiempo de reverberación con las bandas de calificación del Anexo F de IEC 60268-16 sombreadas" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60_es_dark.png" alt="STI frente al tiempo de reverberación con las bandas de calificación del Anexo F de IEC 60268-16 sombreadas" style="width:80%">

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain_es.svg" alt="Cadena de medición del STI: señal de la fuente STIPA a través de la sala hasta el micrófono y el análisis de la MTF" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain_es_dark.svg" alt="Cadena de medición del STI: señal de la fuente STIPA a través de la sala hasta el micrófono y el análisis de la MTF" style="width:92%">

```python
from phonometry import sti_from_impulse_response, stipa, stipa_signal

# Método indirecto: desde una respuesta al impulso medida en la sala
res = sti_from_impulse_response(ir, fs, snr=25.0)
print(f"STI = {res.sti:.2f}  ({res.rating})")   # p. ej. 0.62 (D)

# Medición STIPA directa: reproduce stipa_signal() en la sala y grábala
test = stipa_signal(fs, seconds=18.0, level_db=80.0)
res = stipa(recording, fs)
```

La implementación sigue la **Edición 5 (2020)**: el PDF normativo de la
Edición 4 es la base y cada cambio de la Ed. 5 está atribuido a su fuente en el
código — el único delta numérico es el espectro de habla masculina revisado del
apartado A.6.1. CI comprueba los vectores de verificación de la propia norma:
los seis pares de bandas de los factores de ponderación a ±0,001 STI, la tabla
de correspondencia m ↔ STI, los puntos de control del enmascaramiento
dependiente del nivel y decaimientos con la forma de Schroeder a cuatro valores
de T₆₀.

### Parámetros de `sti_from_impulse_response()` / `stipa()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `ir` / `x` | array 1D | cualquiera / Pa | no vacío | Respuesta al impulso (indirecto) o grabación STIPA (directo) |
| `fs` | int | Hz | > 0 | |
| `snr` | float o vector de 7, opcional | dB | por defecto `None` | Añade la degradación por ruido estacionario |
| `level` | vector de 7, opcional | dB SPL | por defecto `None` | Activa el enmascaramiento auditivo + umbral de recepción (Tablas A.2/A.3) |
| `ambient` | vector de 7, opcional | dB SPL | requiere `level` | Niveles de banda del ruido ambiente |
| `reference` | array 1D, opcional (`stipa`) | — | por defecto `None` | Señal de la fuente medida en lugar del m = 0,55 nominal |

Ambas devuelven `STIResult`: `sti`, `mti` (7 bandas), `mtf` (7×14 o 7×2),
`band_levels`, `rating` (letra del Anexo F, `A+`…`U`).

Consulta [Niveles](/phonometry/es/guides/levels/) para las métricas de
tonalidad y [Teoría](/phonometry/es/reference/theory/) para la matemática
subyacente.

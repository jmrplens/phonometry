---
title: "Intensidad sonora (p-p)"
description: "Intensidad sonora con dos micrófonos según IEC 61043 con los indicadores de campo de ISO 9614-1."
---

La *presión* sonora dice cuánto suena un punto; la **intensidad sonora** dice
hacia dónde *va* la energía. Es el flujo de potencia acústica (W/m²), una
magnitud vectorial con signo — por eso las sondas de intensidad pueden
localizar fuentes, separarlas del ruido de fondo y medir potencia sonora in
situ (ISO 9614) donde una medición de presión por sí sola no puede.

## El principio de dos micrófonos (IEC 61043)

Una sonda p-p sostiene dos micrófonos apareados a una pequeña distancia Δr. La
presión en el centro de la sonda es su media, y la velocidad de partícula
proviene del *gradiente* de presión (ecuación de Euler, en forma de
diferencias finitas):

$$
p = \frac{p_1 + p_2}{2}, \qquad
u = -\frac{1}{\rho_0\ \Delta r}\int (p_2 - p_1)\ dt, \qquad
I = \overline{p\ u}
$$

En la práctica, el estimador trabaja en el dominio de la frecuencia a través
del espectro cruzado de los dos canales (la forma equivalente de la norma):

$$
I(f) = -\ \frac{\mathrm{Im}\lbrace G_{12}(f)\rbrace}{2\pi f\ \rho_0\ \Delta r}
$$

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe_es.svg" alt="Sonda de intensidad p-p de dos micrófonos con la distancia del separador y el eje de medición" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe_es_dark.svg" alt="Sonda de intensidad p-p de dos micrófonos con la distancia del separador y el eje de medición" style="width:92%">

```python
from phonometry import sound_intensity

res = sound_intensity(p1, p2, fs, spacing=0.012, fraction=3,
                      limits=[100, 2500])
print(res.total_intensity_level, res.total_direction)      # LI [dB], ±1
print(res.frequency, res.intensity_level)                  # por banda
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo_es.png" alt="Niveles de presión e intensidad en tercios de octava para una onda plana progresiva frente a una onda estacionaria" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo_es_dark.png" alt="Niveles de presión e intensidad en tercios de octava para una onda plana progresiva frente a una onda estacionaria" style="width:92%">

*Izquierda: en una onda plana progresiva toda la presión se transporta —
L_I ≈ L_p. Derecha: una onda estacionaria no transporta (casi) energía neta —
la presión es alta pero la intensidad se desploma. La diferencia L_p − L_I es
el **índice presión-intensidad**, el indicador de calidad fundamental de toda
medición de intensidad.*

## Saber cuándo fiarse del número

Dos límites físicos acotan toda medición p-p, y el objeto de resultado incluye
ambos:

- **Alta frecuencia**: el gradiente por diferencias finitas subestima I en
  $\sin(k\Delta r)/(k\Delta r)$ — verificado en CI contra la Tabla 3 de
  IEC 61043. `IntensityResult.bias_correction` proporciona el factor y
  `max_valid_frequency` (≈ 0,1·c/Δr; 2,9 kHz para un separador de 12 mm) el
  techo práctico. Los separadores mayores alcanzan frecuencias más bajas; los
  menores, más altas.
- **Campos reactivos**: cuando `pressure_intensity_index` (F2 en ISO 9614-1)
  se acerca al índice residual δ_pI0 de la sonda, dominan los errores de fase.
  Los indicadores de campo del Anexo A de ISO 9614-1 y el criterio de
  capacidad dinámica están disponibles directamente:

```python
from phonometry import field_indicators, dynamic_capability_index

fi = field_indicators(pressure_levels, normal_intensity)   # F2, F3, F4
ld = dynamic_capability_index(18.0)   # δpI0 = 18 dB → Ld = δpI0 − K
ok = ld > fi.f2                                            # criterio 1
```

### Parámetros de `sound_intensity()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `p1`, `p2` | arrays 1D | Pa | misma longitud | Primero el micrófono más cercano a la fuente; invertirlos cambia el signo |
| `fs` | int | Hz | > 0 | |
| `spacing` | float | m | > 0 | Separación entre micrófonos Δr (típ. 6/12/50 mm) |
| `rho` | float | kg/m³ | por defecto `1.204` | Densidad del aire |
| `c` | float | m/s | por defecto `343.0` | Velocidad del sonido (estimaciones de sesgo/validez) |
| `fraction` | int, opcional | — | `1`, `3` o `None` (por defecto) | Integración en bandas de octava/tercio de octava |
| `limits` | lista, opcional | Hz | por defecto el rango de bandas de la librería | Límites del análisis por bandas |

Consulta [Teoría](/phonometry/es/reference/theory/) para las derivaciones y
[Calibración](/phonometry/es/guides/calibration/) para el escalado absoluto de
los dos canales.

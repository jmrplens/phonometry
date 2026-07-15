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
import numpy as np
from phonometry import sound_intensity

fs = 48000
rng = np.random.default_rng(0)
# Las presiones de los dos micrófonos de la sonda en Pa, p1 el más cercano a la fuente.
#   En una medición real son tus dos grabaciones de sonda calibradas;
#   sintetizadas aquí (p2 = p1 retardada una muestra) para que la guía funcione.
p1 = 0.02 * rng.standard_normal(fs)
p2 = np.concatenate(([0.0], p1[:-1]))   # p2 = p1 retardada una muestra

res = sound_intensity(p1, p2, fs, spacing=0.012, fraction=3,
                      limits=[100, 2500])
print(res.total_intensity_level, res.total_direction)      # LI [dB], ±1
print(res.frequency, res.intensity_level)                  # por banda
res.plot()   # Lp frente a LI por banda + el índice presión-intensidad (requiere matplotlib)
```

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_instantaneous_intensity_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_instantaneous_intensity_es_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: una sonda p-p de dos micrófonos con fasores giratorios de presión y velocidad; la flecha de intensidad instantánea cambia de sentido mientras su promedio se estabiliza en un flujo neto para la onda progresiva y en cero para la onda estacionaria" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_instantaneous_intensity_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_instantaneous_intensity_es_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: una sonda p-p de dos micrófonos con fasores giratorios de presión y velocidad; la flecha de intensidad instantánea cambia de sentido mientras su promedio se estabiliza en un flujo neto para la onda progresiva y en cero para la onda estacionaria" style="width:88%"></video>

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo_es.svg" alt="Niveles de presión e intensidad en tercios de octava para una onda plana progresiva frente a una onda estacionaria" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo_es_dark.svg" alt="Niveles de presión e intensidad en tercios de octava para una onda plana progresiva frente a una onda estacionaria" style="width:92%">

*Izquierda: en una onda plana progresiva toda la presión se transporta —
L_I ≈ L_p. Derecha: una onda estacionaria no transporta (casi) energía neta —
la presión es alta pero la intensidad se desploma. La diferencia L_p − L_I es
el **índice presión-intensidad**, el indicador de calidad fundamental de toda
medición de intensidad.*

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# res es el IntensityResult calculado en el ejemplo anterior.
# En una línea — Lp frente a LI por banda, con el índice presión-intensidad en un eje gemelo:
res.plot()
plt.show()

# A mano, con los campos por banda que lleva el resultado — reproduciendo lo que
# dibuja IntensityResult.plot() (etiqueta de barra, leyenda combinada de ambos ejes, título δpI):
fig, ax = plt.subplots()
ax.semilogx(res.frequency, res.pressure_level, "o-", label="Nivel de presión Lp")
ax.semilogx(res.frequency, res.intensity_level, "s--", label="Nivel de intensidad LI")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel [dB]")
twin = ax.twinx()
twin.bar(res.frequency, res.pressure_intensity_index,
         width=res.frequency * 0.2, color="#2ca02c", alpha=0.25,
         label="δpI = Lp − LI")
twin.set_ylabel("Índice presión-intensidad δpI [dB]")
# Combina los manejadores de ambos ejes en una sola leyenda, igual que .plot():
lines, labels = ax.get_legend_handles_labels()
tlines, tlabels = twin.get_legend_handles_labels()
ax.legend(lines + tlines, labels + tlabels)
ax.set_title(f"Lp frente a LI  (δpI total = {res.total_pressure_intensity_index:.1f} dB)")
plt.show()
```

</details>

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

Sobre una superficie de medición, los indicadores de campo del Anexo A de
ISO 9614-1 califican el propio barrido. **F2**, el indicador
presión-intensidad de superficie, es el nivel de presión de superficie menos
el nivel de la *magnitud* media de la intensidad normal — cuanto mayor es,
más cerca está la medición del suelo de error de fase de la sonda. **F3**, el
indicador de potencia parcial negativa, es la misma diferencia tomada con la
intensidad media *con signo* — F3 − F2 > 0 revela potencia que entra por
partes de la superficie. **F4**, el indicador de no uniformidad del campo, es
la dispersión normalizada de las intensidades por posición — cuanto mayor es,
más posiciones de medición necesita la superficie. Junto con el criterio de
capacidad dinámica están disponibles directamente:

```python
import numpy as np
from phonometry import field_indicators, dynamic_capability_index

# Mediciones por posición sobre la superficie de medición de ISO 9614-1
pressure_levels = np.array([74.1, 73.8, 74.5, 73.2])       # Lp por posición (dB)
normal_intensity = np.array([1.2e-5, 1.0e-5, 1.4e-5, 0.9e-5])  # In con signo por posición (W/m²)

fi = field_indicators(pressure_levels, normal_intensity)
print(round(fi.f2, 2), round(fi.f3, 2), round(fi.f4, 3))   # 3.41 3.41 0.197
ld = dynamic_capability_index(18.0)   # δpI0 = 18 dB → Ld = δpI0 − K
print(ld, ld > fi.f2)                                      # 8.0 True (criterio 1)
```

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: una sonda p-p recorre el barrido en serpentina sobre la cara superior de la caja de medición mientras aparecen detrás las flechas de intensidad normal, y las potencias parciales de las cinco caras se acumulan en el nivel de potencia sonora L_W" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_intensity_scan_power_es_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: una sonda p-p recorre el barrido en serpentina sobre la cara superior de la caja de medición mientras aparecen detrás las flechas de intensidad normal, y las potencias parciales de las cinco caras se acumulan en el nivel de potencia sonora L_W" style="width:88%"></video>

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
| `bias_correct` | bool | — | defecto `False` | Aplica la corrección por bin $(k\Delta r)/\sin(k\Delta r)$ (IEC 61043 §7.3) antes de sumar, para que los totales de banda/banda ancha dejen de subestimar cuando $f \to$ `max_valid_frequency`; los bins pasado el primer nulo se dejan sin corregir. El factor `bias_correction` por banda se reporta en ambos casos |

Consulta [Teoría](/phonometry/es/reference/theory/signal-analysis/) para las derivaciones y
[Calibración](/phonometry/es/guides/calibration/) para el escalado absoluto de
los dos canales.

---

**Normas.** IEC 61043:1994, *Electroacoustics — Instruments for the
measurement of sound intensity — Measurements with pairs of pressure sensing
microphones* — el estimador de intensidad por espectro cruzado con dos
micrófonos, la corrección del sesgo por diferencias finitas y el límite de
ancho de banda utilizable (cláusula 7.3, Tabla 3). ISO 9614-1:1993,
*Acoustics — Determination of sound power levels of noise sources using sound
intensity — Part 1: Measurement at discrete points* — el índice
presión-intensidad, los indicadores de campo F2, F3 y F4 del Anexo A y el
criterio de capacidad dinámica (Anexo B).

## Véase también

- Referencia de la API: [`emission.intensity`](/phonometry/es/reference/api/power/intensity/).

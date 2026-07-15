---
title: "Ruido de aerogeneradores: potencia y audibilidad tonal"
description: "La emisión acústica de aerogeneradores de la IEC 61400-11: el nivel de potencia sonora aparente referido al centro del rotor y la cadena de audibilidad tonal (banda crítica de Zwicker, nivel de ruido de enmascaramiento y criterio de audibilidad) que decide si un tono discreto es audible."
---

La IEC 61400-11 mide la emisión acústica de un aerogenerador. Esta página cubre
sus dos magnitudes en forma cerrada: el **nivel de potencia sonora aparente**
referido a una fuente puntual equivalente en el centro del rotor, y la
**audibilidad tonal** que decide si un tono discreto (paso de pala, multiplicadora,
generador) es audible por encima del ruido de enmascaramiento.

## Nivel de potencia sonora aparente

Con el micrófono de referencia sobre una placa en el suelo a la distancia
horizontal `R0 = H + D/2` (altura de buje `H`, diámetro de rotor `D`), la
distancia oblicua al centro del rotor es `R1 = √(H² + R0²)` y el nivel de
potencia sonora aparente es `L_WA,i = L_p,i − 6 + 10·lg(4π R1²/S0)` por banda
(`S0 = 1 m²`), sumado energéticamente sobre las bandas. Los `−6 dB` dan cuenta de
la duplicación de presión en la placa del suelo.

```python
import phonometry as ph

r1 = ph.slant_distance(hub_height=80.0, rotor_diameter=100.0)
lwa = ph.apparent_sound_power_level(band_levels, r1)   # dB re 1 pW
```

## Audibilidad tonal

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tonality_es.svg" alt="Espectro de banda estrecha de un aerogenerador con un tono discreto cerca de 200 Hz sobre un fondo de banda ancha, la banda crítica sombreada, el nivel de ruido de enmascaramiento como línea horizontal y la audibilidad tonal anotada" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tonality_es_dark.svg" alt="Espectro de banda estrecha de un aerogenerador con un tono discreto cerca de 200 Hz sobre un fondo de banda ancha, la banda crítica sombreada, el nivel de ruido de enmascaramiento como línea horizontal y la audibilidad tonal anotada" style="width:82%">

A partir de un espectro de banda estrecha (resolución 1–2 Hz), las líneas en la
**banda crítica** alrededor del tono, `CBW = 25 + 75·[1 + 1.4·(fc/1000)²]^0.69`
Hz, se clasifican en ruido de enmascaramiento y líneas de tono (la media
energética del 70 % más bajo, los criterios de `+6 dB`; las líneas de tono
deben además quedar a menos de 10 dB de la línea *más alta* por encima del
umbral, y esa línea más alta es la frecuencia del tono, apartados
9.5.3/9.5.4). El propio candidato debe superar antes el cribado de *tono
posible* de 9.5.2: un máximo local más de 6 dB por encima de la media
energética de la banda excluyendo el máximo y sus líneas adyacentes. El nivel
de enmascaramiento `L_pn` sigue la Fórmula 31, la tonalidad es
`ΔL_tn = L_pt − L_pn` y la audibilidad tonal es `ΔL_a = ΔL_tn − L_a` con
`L_a = −2 − lg[1 + (f/502)^2.5]`, reportada cuando `ΔL_a ≥ −3 dB` y audible
cuando `ΔL_a > 0`.

```python
import phonometry as ph

res = ph.wind_turbine_tonality(levels, frequencies)   # espectro de banda estrecha
print(res.tone_frequency, res.tonality, res.tonal_audibility, res.is_audible)
res.plot()   # espectro + banda crítica + nivel de enmascaramiento (requiere matplotlib)
```

`wind_turbine_tonality` devuelve un `WindTurbineTonalityResult` con
`critical_bandwidth`, `tone_level`, `masking_level`, `tonality`,
`audibility_criterion`, `tonal_audibility`, `is_audible` y
`has_identified_tone`. Cuando el candidato no supera el cribado de 9.5.2 o
ninguna línea se clasifica como «tono», `has_identified_tone` es `False`: los
campos numéricos son valores de respaldo fuera de la norma y esos espectros
deben **excluirse** del promediado energético de `ΔL_a` sobre los espectros
de un intervalo de velocidad de viento (9.5.1); `is_audible` también exige un
tono identificado. La frecuencia del tono y el criterio `L_a` se anclan a la
línea de tono clasificada más alta, no al candidato sondeado. La fórmula de
audibilidad coincide con la del Anexo C de la ISO 1996-2; lo específico de la
IEC 61400-11 es la determinación de los niveles de tono y enmascaramiento y la
banda crítica de Zwicker a partir del espectro. Para un ajuste de valoración
`K_T`, pasa la audibilidad media al `tonal_adjustment` de la ISO 1996-2.

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import phonometry as ph

df = 2.0
freqs = np.arange(50.0, 400.0 + df, df)
levels = 42.0 - 6.0 * np.log10(freqs / 100.0)
levels[int(np.argmin(np.abs(freqs - 200.0)))] += 22.0   # tono estilo paso de pala
ph.wind_turbine_tonality(levels, freqs, tone_frequency=200.0).plot()
```

</details>

---

**Normas.** IEC 61400-11:2012+A1:2018 (potencia sonora aparente Fórmula 26,
banda crítica Fórmula 30, nivel de enmascaramiento Fórmula 31,
tonalidad/audibilidad Fórmulas 32–34). El flujo completo de medición queda fuera
del alcance aquí.

## Véase también

- Referencia de la API: [`environmental.wind_turbine_noise`](/phonometry/es/reference/api/aeroacoustics/wind-turbine-noise/).

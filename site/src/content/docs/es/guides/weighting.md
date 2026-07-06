---
title: "Ponderación frecuencial (A, C, Z)"
description: "Curvas de ponderación IEC 61672-1 con precisión clase 1 en alta frecuencia."
---

Las curvas de ponderación frecuencial simulan la sensibilidad del oído humano,
según especifica la norma **IEC 61672-1:2013**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses.png" alt="Curvas de ponderación A, C y Z con zoom de la región positiva de la curva A (+1,27 dB en 2,5 kHz)" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses_dark.png" alt="Curvas de ponderación A, C y Z con zoom de la región positiva de la curva A (+1,27 dB en 2,5 kHz)" style="width:80%">

* **Ponderación A (`A`):** estándar para ruido ambiental (IEC 61672-1).
* **Ponderación C (`C`):** para presión sonora de pico y ruido de alto nivel.
* **Ponderación Z (`Z`):** ponderación cero, respuesta completamente plana.

```python
from phonometry import weighting_filter

# Aplicar ponderación A a la señal cruda
weighted_signal = weighting_filter(signal, fs, curve='A')

# Aplicar ponderación C para análisis de picos
c_weighted_signal = weighting_filter(signal, fs, curve='C')
```

## Objeto de filtro reutilizable

Si ponderas muchas señales con los mismos parámetros, diseña el filtro una sola vez:

```python
from phonometry import WeightingFilter

wf = WeightingFilter(fs, "A")
for signal in signals:
    weighted = wf.filter(signal)
```

## Precisión en alta frecuencia (`high_accuracy`)

Un diseño con transformación bilineal simple comprime la respuesta cerca de
Nyquist: a fs = 48 kHz el error de la curva A a 12,5 kHz alcanza −2,7 dB, fuera
de la tolerancia **clase 1** de IEC 61672-1 (+2,0/−2,5 dB).

Por defecto (`high_accuracy=True`), phonometry diseña y ejecuta el filtro de
ponderación a una frecuencia interna sobremuestreada (≥ 96 kHz) y diezma de
vuelta, manteniendo la respuesta dentro de las tolerancias de clase 1 hasta
16 kHz (error ≈ −0,5 dB a 12,5 kHz para fs = 48 kHz).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf.png" alt="Precisión en alta frecuencia de la ponderación A a 48 kHz: curva analítica frente a bilineal simple y diseño sobremuestreado, con error" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf_dark.png" alt="Precisión en alta frecuencia de la ponderación A a 48 kHz: curva analítica frente a bilineal simple y diseño sobremuestreado, con error" style="width:80%">

*El diseño bilineal simple (rojo) cruza la tolerancia de clase 1 cerca de
12,5 kHz; el diseño sobremuestreado (azul) se mantiene junto a la curva analítica.*

- `high_accuracy=False` restaura el comportamiento bilineal clásico.
- El **procesado por bloques (stateful)** usa siempre el diseño clásico: el
  remuestreo FIR interno es incompatible con la continuidad entre bloques. Pasar
  `high_accuracy=True` junto con `stateful=True` lanza un `ValueError`.

```python
# Comportamiento clásico explícito
y = weighting_filter(signal, fs, curve="A", high_accuracy=False)

# Procesado por bloques con estado (diseño clásico, estado entre bloques)
wf = WeightingFilter(fs, "A", stateful=True)
for block in blocks:
    weighted = wf.filter(block)
```

Consulta [Procesado por bloques](/phonometry/es/guides/block-processing/) para
el flujo en streaming y [Teoría](/phonometry/es/reference/theory/) para las
definiciones analíticas de las curvas.

---
title: "Bancos de filtros"
description: "Arquitecturas, respuestas en frecuencia, descomposición por bandas y filtrado de fase cero."
---

phonometry soporta varios tipos de filtro, cada uno con su propia función de
transferencia característica. Todos los bancos sitúan sus **puntos de −3 dB en
los bordes de banda de ANSI S1.11**, de modo que los niveles por banda son
comparables entre arquitecturas.

## Comparación de filtros y zoom

Usamos secciones de segundo orden (SOS) en todos los filtros para garantizar la
estabilidad numérica. La siguiente gráfica compara las arquitecturas centrándose
en el punto de cruce a −3 dB.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison_es.png" alt="Comparación de la respuesta en magnitud de las cinco arquitecturas para la banda de octava de 1 kHz, con zoom en el cruce a -3 dB" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison_es_dark.png" alt="Comparación de la respuesta en magnitud de las cinco arquitecturas para la banda de octava de 1 kHz, con zoom en el cruce a -3 dB" style="width:80%">

| Tipo | Nombre | Ejemplo de uso | Ideal para |
| :--- | :--- | :--- | :--- |
| `butter` | **Butterworth** | `octavefilter(x, fs, filter_type='butter')` | Medición acústica general. |
| `cheby1` | **Chebyshev I** | `octavefilter(x, fs, filter_type='cheby1', ripple=0.1)` | Caída más abrupta a costa de rizado. |
| `cheby2` | **Chebyshev II** | `octavefilter(x, fs, filter_type='cheby2', attenuation=60)` | Banda de paso plana con ceros en la banda atenuada. |
| `ellip` | **Elíptico** | `octavefilter(x, fs, filter_type='ellip', ripple=0.1, attenuation=60)` | Máxima selectividad. |
| `bessel` | **Bessel** | `octavefilter(x, fs, filter_type='bessel')` | Preservar la forma de los transitorios. |

## Galería de respuestas del banco

Vista espectral completa de los bancos para octava (1/1) y tercio de octava (1/3).

| Arquitectura | Octava 1/1 (fraction=1) | Octava 1/3 (fraction=3) |
| :--- | :--- | :--- |
| **Butterworth** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco de filtros Butterworth de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco de filtros Butterworth de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:100%"> |
| **Chebyshev I** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev I de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev I de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:100%"> |
| **Chebyshev II** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev II de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev II de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:100%"> |
| **Elíptico** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco elíptico de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco elíptico de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:100%"> |
| **Bessel** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco Bessel de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Bessel de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:100%"> |

## Uso y ejemplos por tipo de filtro

### 1. Butterworth (`butter`)

El filtro Butterworth es conocido por su **banda de paso máximamente plana**. Es
la elección estándar para mediciones acústicas donde no se admite rizado dentro
de las bandas de frecuencia.

```python
from phonometry import octavefilter
# Medición estándar por defecto
spl, freq = octavefilter(x, fs, filter_type='butter')
```

### 2. Chebyshev I (`cheby1`)

Los filtros Chebyshev tipo I ofrecen una **caída más abrupta** que Butterworth a
cambio de rizado en la banda de paso. Útiles cuando se necesita alta selectividad
cerca de las frecuencias de corte.

```python
# Selectividad con 0.1 dB de rizado en la banda de paso
spl, freq = octavefilter(x, fs, filter_type='cheby1', ripple=0.1)
```

### 3. Chebyshev II (`cheby2`)

También llamado Chebyshev inverso, tiene **banda de paso plana** y rizado en la
banda atenuada. Ofrece una caída más rápida que Butterworth sin afectar a la
señal en la banda de paso. Los bordes de la banda atenuada se colocan
automáticamente para que los puntos de −3 dB caigan en los bordes de banda
(`attenuation` debe ser > 3.01 dB).

```python
# Banda de paso plana con 60 dB de atenuación
spl, freq = octavefilter(x, fs, filter_type='cheby2', attenuation=60)
```

### 4. Elíptico (`ellip`)

Los filtros elípticos (Cauer) tienen la **transición más corta** (caída más
abrupta) para un orden dado. Presentan rizado tanto en la banda de paso como en
la atenuada.

```python
# Máxima selectividad para aislamiento extremo entre bandas
spl, freq = octavefilter(x, fs, filter_type='ellip', ripple=0.1, attenuation=60)
```

### 5. Bessel (`bessel`)

Los filtros Bessel están optimizados para una **respuesta de fase lineal** y un
retardo de grupo mínimo. Preservan la forma de las ondas filtradas (transitorios)
mejor que ningún otro tipo, pero tienen la caída más lenta.

```python
# Ideal para análisis de pulsos y preservación de transitorios
spl, freq = octavefilter(x, fs, filter_type='bessel')
```

### 6. Linkwitz-Riley (`linkwitz_riley`)

Diseñado específicamente para **crossovers de audio**. Los filtros Linkwitz-Riley
(típicamente de 4.º orden, aunque se admite cualquier orden par) permiten dividir
una señal en bandas que, al sumarse, producen una respuesta en magnitud
perfectamente plana y sin diferencia de fase entre bandas en el cruce.

```python
from phonometry import linkwitz_riley
# Dividir la señal en bandas grave y aguda a 1000 Hz
low, high = linkwitz_riley(signal, fs, freq=1000, order=4)
# Reconstrucción: low + high == signal (respuesta plana)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4_es.png" alt="Crossover Linkwitz-Riley de 4.º orden: paso-bajo, paso-alto y su suma plana" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4_es_dark.png" alt="Crossover Linkwitz-Riley de 4.º orden: paso-bajo, paso-alto y su suma plana" style="width:60%">

## Verificar la clase IEC 61260-1

`verify_filter_class` comprueba cada banda de un banco contra los límites de
aceptación de **IEC 61260-1:2014** (Tabla 1, con el mapeo de breakpoints a
fraccionales y la interpolación logarítmica de la norma) e informa de la clase
por banda con su margen en dB:

```python
from phonometry import OctaveFilterBank, verify_filter_class

bank = OctaveFilterBank(fs=48000, fraction=3, order=6)
result = verify_filter_class(bank)
print(result["overall_class"])          # 1, 2 o None
print(result["bands"][0])               # {'freq': ..., 'class': 1, 'margin_class1_db': ...}
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay_es.png" alt="Respuesta Butterworth serpenteando entre las regiones prohibidas de la máscara de clase 1 de IEC 61260-1" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay_es_dark.png" alt="Respuesta Butterworth serpenteando entre las regiones prohibidas de la máscara de clase 1 de IEC 61260-1" style="width:80%">

*La respuesta del Butterworth de orden 6 (azul) serpentea entre las regiones
prohibidas: debe atenuar al menos la máscara roja fuera de la banda y no más
que la morada dentro de ella.*

Con parámetros por defecto (orden 6), **Butterworth cumple clase 1**.
Chebyshev II se queda en clase 2 — limitado exactamente por su `attenuation=60`
frente a los 70 dB exigidos en el stopband lejano (sube `attenuation` para
alcanzar clase 1). Chebyshev I, Elíptico y Bessel no cumplen los límites de
clase con orden 6: el rizado de banda de paso (cheby1/ellip) y la caída lenta
(bessel) violan la máscara.

## Descomposición de la señal y estabilidad

Con `sigbands=True` puedes recuperar las componentes en el dominio del tiempo de
cada banda. Esto permite análisis avanzados o comparar cómo afectan distintas
arquitecturas (p. ej. Butterworth vs Chebyshev) a la fase y al transitorio.

```python
import numpy as np
from phonometry import octavefilter

# 1. Generar una señal (suma de 250 Hz y 1000 Hz)
fs = 48000
t = np.linspace(0, 0.5, int(fs * 0.5), endpoint=False)
y = np.sin(2 * np.pi * 250 * t) + np.sin(2 * np.pi * 1000 * t)

# 2. Comparar arquitecturas (Butterworth vs Chebyshev II)
spl_b, freq, xb_butter = octavefilter(y, fs=fs, fraction=1, sigbands=True, filter_type='butter')
spl_c2, _, xb_cheby2 = octavefilter(y, fs=fs, fraction=1, sigbands=True, filter_type='cheby2')

# 'xb_butter' y 'xb_cheby2' contienen las señales por banda en el dominio del tiempo
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_decomposition_es.png" alt="Descomposición por bandas en el tiempo comparando Butterworth y Chebyshev II, incluida la respuesta al impulso" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_decomposition_es_dark.png" alt="Descomposición por bandas en el tiempo comparando Butterworth y Chebyshev II, incluida la respuesta al impulso" style="width:80%">

*La gráfica compara las respuestas de **Butterworth** (azul, línea continua) y
**Chebyshev II** (rojo, discontinua). El panel inferior muestra la **respuesta al
impulso**, destacando las diferencias de estabilidad y decaimiento transitorio.*

:::note
**¿Por qué las señales parecen desplazadas en el tiempo?**
Los filtros IIR digitales (como Butterworth o Chebyshev) tienen **respuestas de
fase no lineales**, lo que produce un **retardo de grupo** dependiente de la
frecuencia. En la banda de 250 Hz se aprecia que el filtro Chebyshev II tiene un
retardo de propagación distinto al de Butterworth. Es una propiedad física normal
de estas arquitecturas: caídas más agresivas suelen implicar mayor retardo de
grupo y distorsión de fase.
:::

### El retardo de grupo, cuantificado

El retardo de grupo $\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}$ de la
banda de octava de 1 kHz muestra el compromiso directamente: Bessel se mantiene
casi plano en la banda de paso (los transitorios sobreviven), mientras que
Chebyshev I y el Elíptico pagan su caída abrupta con fuertes picos de retardo en
los bordes de banda.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/group_delay_comparison_es.png" alt="Retardo de grupo de la banda de 1 kHz para las cinco arquitecturas: Bessel casi plano, Chebyshev y elíptico con picos en los bordes" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/group_delay_comparison_es_dark.png" alt="Retardo de grupo de la banda de 1 kHz para las cinco arquitecturas: Bessel casi plano, Chebyshev y elíptico con picos en los bordes" style="width:80%">

## Filtrado de fase cero

Para análisis offline puedes eliminar por completo el retardo de grupo:
`zero_phase=True` filtra cada banda hacia delante y hacia atrás
(`scipy.signal.sosfiltfilt`), manteniendo las señales por banda alineadas con la
entrada. La atenuación efectiva se duplica y la opción es incompatible con el
procesado por bloques (stateful).

```python
from phonometry import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3)
spl, freq, xb = bank.filter(y, sigbands=True, zero_phase=True)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison_es.png" alt="Filtrado causal frente a fase cero de una ráfaga: la salida de fase cero queda alineada con la entrada" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison_es_dark.png" alt="Filtrado causal frente a fase cero de una ráfaga: la salida de fase cero queda alineada con la entrada" style="width:80%">

*El filtrado causal retrasa la ráfaga según el retardo de grupo del filtro; el
filtrado de fase cero la mantiene alineada con la entrada.*

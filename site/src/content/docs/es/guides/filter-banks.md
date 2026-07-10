---
title: "Bancos de filtros"
description: "Arquitecturas, respuestas en frecuencia, descomposición por bandas y filtrado de fase cero."
---

phonometry soporta varios tipos de filtro, cada uno con su propia función de
transferencia característica. Todos los bancos sitúan sus **puntos de −3 dB en
los bordes de banda de ANSI S1.11**, de modo que los niveles por banda son
comparables entre arquitecturas.

## 1. Bandas de octava fraccionaria: las matemáticas

IEC 61260-1:2014 construye cada banda a partir de la razón de octava en base 10
$G = 10^{3/10} \approx 1{,}99526$ (es decir, "una octava" *no* es exactamente 2).
Para la fracción de banda $1/b$, las frecuencias centrales y los bordes de
banda siguen (5.2-5.5):

$$
f_m = 1000 \cdot G^{x/b} \quad (b\ \text{impar}), \qquad
f_1 = f_m G^{-1/2b}, \quad f_2 = f_m G^{+1/2b}
$$

de modo que cada banda de tercio de octava abarca
$G^{1/3} \approx 1{,}2589 \approx 10^{1/10}$ — diez bandas por década, y por eso
las frecuencias nominales (25, 31,5, 40 …) se repiten escaladas por 10.
phonometry diseña cada banda como una cascada SOS cuyos puntos de −3 dB caen
exactamente en $f_1$ y $f_2$ en todas las arquitecturas — para Chebyshev II,
Elíptico y Bessel eso exige pre-deformar (pre-warping) el mapeo analítico de los
bordes de banda en lugar de confiar en la parametrización por defecto de SciPy.

### Diezmado multitasa

Una banda de tercio de octava de 25 Hz a 48 kHz abarca unos 5,8 Hz — el
0,024 % de Nyquist — con coeficientes tan rígidos que se vuelven
numéricamente inestables. El banco lo evita filtrando las bandas bajas a una
frecuencia diezmada:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multirate_es.svg" alt="Diezmado multitasa: las bandas altas se filtran a la frecuencia de entrada y las bajas tras un paso-bajo antialiasing y diezmado, para que las secciones SOS se mantengan numéricamente sanas" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multirate_es_dark.svg" alt="Diezmado multitasa: las bandas altas se filtran a la frecuencia de entrada y las bajas tras un paso-bajo antialiasing y diezmado, para que las secciones SOS se mantengan numéricamente sanas" style="width:92%">

## 2. Comparación de filtros y zoom

Usamos secciones de segundo orden (SOS) en todos los filtros para garantizar la
estabilidad numérica. La siguiente gráfica compara las arquitecturas centrándose
en el punto de cruce a −3 dB.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison_es.png" alt="Comparación de la respuesta en magnitud de las cinco arquitecturas para la banda de octava de 1 kHz, con zoom en el cruce a -3 dB" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison_es_dark.png" alt="Comparación de la respuesta en magnitud de las cinco arquitecturas para la banda de octava de 1 kHz, con zoom en el cruce a -3 dB" style="width:80%">

| Tipo | Nombre | Ejemplo de uso | Ideal para |
| :--- | :--- | :--- | :--- |
| `butter` | **Butterworth** | `octave_filter(x, fs, filter_type='butter')` | Medición acústica general. |
| `cheby1` | **Chebyshev I** | `octave_filter(x, fs, filter_type='cheby1', ripple=0.1)` | Caída más abrupta a costa de rizado. |
| `cheby2` | **Chebyshev II** | `octave_filter(x, fs, filter_type='cheby2')` | Banda de paso plana con ceros en la banda atenuada. |
| `ellip` | **Elíptico** | `octave_filter(x, fs, filter_type='ellip', ripple=0.1)` | Máxima selectividad. |
| `bessel` | **Bessel** | `octave_filter(x, fs, filter_type='bessel')` | Preservar la forma de los transitorios. |

## 3. Parámetros de `octave_filter()` / `OctaveFilterBank`

| Parámetro | Tipo | Unidades | Rango / por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `x` | array 1D o 2D | unidades digitales | no vacío | 2D es `[channels, samples]` |
| `fs` | int | Hz | > 0 | |
| `fraction` | int | — | por defecto `1`; habitual `3`; cualquier `b ≥ 1` | Bandas por octava = `b` |
| `order` | int | — | por defecto `6` | Orden SOS por banda |
| `limits` | lista `[lo, hi]` | Hz | por defecto `[12, 20000]` | Rango de análisis |
| `filter_type` | str | — | `'butter'` (por defecto), `'cheby1'`, `'cheby2'`, `'ellip'`, `'bessel'` | Ver la comparación más arriba |
| `ripple` / `attenuation` | float | dB | `ripple` defecto `0.1`; `attenuation` defecto `72.0` | Rizado de banda de paso / atenuación en banda atenuada (cheby/ellip); `cheby2` necesita `attenuation ≥ 70` para clase 1, ya que scipy fija su suelo equirizado en exactamente este valor |
| `show` | bool | — | por defecto `False` | Dibuja la respuesta del banco (requiere matplotlib) |
| `sigbands` | bool | — | por defecto `False` | Devuelve también las señales temporales por banda |
| `mode` | str | — | `'rms'` (por defecto), `'peak'`, `'sum'` | Estadístico por banda devuelto |
| `nominal` | bool | — | por defecto `False` | Devuelve etiquetas nominales (p. ej. `1000`) en vez de las frecuencias centrales exactas |
| `detrend` | bool | — | por defecto `True` | Elimina el offset DC de cada banda antes del nivel (mejora la precisión en graves) |
| `calibration_factor` | float | — | por defecto `1.0` | Escala la entrada a pascales (consulta la guía de Calibración) |
| `dbfs` | bool | — | por defecto `False` | Referencia los niveles a fondo de escala digital en vez de 20 µPa |
| `plot_file` | str o `None` | — | por defecto `None` | Guarda la gráfica de respuesta del banco en esta ruta |
| `zero_phase` | bool | — | por defecto `False` | Filtrado adelante-atrás (offline) |
| `stateful` / `steady_ic` (clase) | bool | — | por defecto `False` | Estado en streaming; consulta [Procesado por bloques](/phonometry/es/guides/block-processing/) |

`verify_filter_class(bank)` comprueba el banco diseñado contra los límites de
aceptación de la Tabla 1 de IEC 61260-1 e informa de la clase (`1`, `2` o `None` si queda fuera de ambas) con los
márgenes por banda.

## 4. Galería de respuestas del banco

Vista espectral completa de los bancos para octava (1/1) y tercio de octava (1/3).

| Arquitectura | Octava 1/1 (fraction=1) | Octava 1/3 (fraction=3) |
| :--- | :--- | :--- |
| **Butterworth** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco de filtros Butterworth de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco de filtros Butterworth de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:100%"> |
| **Chebyshev I** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev I de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev I de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:100%"> |
| **Chebyshev II** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev II de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev II de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:100%"> |
| **Elíptico** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco elíptico de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco elíptico de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:100%"> |
| **Bessel** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6_es.png" alt="Respuesta en frecuencia del banco Bessel de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Bessel de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:100%"> |

## 5. Uso y ejemplos por tipo de filtro

### 1. Butterworth (`butter`)

El filtro Butterworth es conocido por su **banda de paso máximamente plana**. Es
la elección estándar para mediciones acústicas donde no se admite rizado dentro
de las bandas de frecuencia.

```python
import numpy as np
from phonometry import octave_filter

# Una señal calibrada en Pa para que la guía funcione por sí sola
fs = 48000
x = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# Medición estándar por defecto
spl, freq = octave_filter(x, fs, filter_type='butter')
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:60%">

### 2. Chebyshev I (`cheby1`)

Los filtros Chebyshev tipo I ofrecen una **caída más abrupta** que Butterworth a
cambio de rizado en la banda de paso. Útiles cuando se necesita alta selectividad
cerca de las frecuencias de corte.

```python
# Usa `x` y `fs` del snippet anterior.
# Selectividad con 0.1 dB de rizado en la banda de paso
spl, freq = octave_filter(x, fs, filter_type='cheby1', ripple=0.1)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:60%">

### 3. Chebyshev II (`cheby2`)

También llamado Chebyshev inverso, tiene **banda de paso plana** y rizado en la
banda atenuada. Ofrece una caída más rápida que Butterworth sin afectar a la
señal en la banda de paso. Los bordes de la banda atenuada se colocan
automáticamente para que los puntos de −3 dB caigan en los bordes de banda
(`attenuation` debe ser > 3,01 dB).

```python
# Usa `x` y `fs` del snippet anterior.
# Banda de paso plana, 72 dB de atenuación por defecto (clase 1)
spl, freq = octave_filter(x, fs, filter_type='cheby2')
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:60%">

### 4. Elíptico (`ellip`)

Los filtros elípticos (Cauer) tienen la **transición más corta** (caída más
abrupta) para un orden dado. Presentan rizado tanto en la banda de paso como en
la atenuada.

```python
# Usa `x` y `fs` del snippet anterior.
# Máxima selectividad para aislamiento extremo entre bandas
spl, freq = octave_filter(x, fs, filter_type='ellip', ripple=0.1)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:60%">

### 5. Bessel (`bessel`)

Los filtros Bessel están optimizados para una **respuesta de fase lineal** y un
retardo de grupo mínimo. Preservan la forma de las ondas filtradas (transitorios)
mejor que ningún otro tipo, pero tienen la caída más lenta.

```python
# Usa `x` y `fs` del snippet anterior.
# Ideal para análisis de pulsos y preservación de transitorios
spl, freq = octave_filter(x, fs, filter_type='bessel')
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es.png" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es_dark.png" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:60%">

### 6. Linkwitz-Riley (`linkwitz_riley`)

Diseñado específicamente para **crossovers de audio**. Los filtros Linkwitz-Riley
(típicamente de 4.º orden, aunque se admite cualquier orden par) permiten dividir
una señal en bandas que, al sumarse, producen una respuesta en magnitud
perfectamente plana y sin diferencia de fase entre bandas en el cruce.

```python
from phonometry import linkwitz_riley

# Usa `x` y `fs` del snippet anterior.
signal = x
# Dividir la señal en bandas grave y aguda a 1000 Hz
low, high = linkwitz_riley(signal, fs, freq=1000, order=4)
# Reconstrucción: low + high == signal (respuesta plana)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4_es.png" alt="Crossover Linkwitz-Riley de 4.º orden: paso-bajo, paso-alto y su suma plana" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4_es_dark.png" alt="Crossover Linkwitz-Riley de 4.º orden: paso-bajo, paso-alto y su suma plana" style="width:60%">

## 6. Verificar la clase IEC 61260-1

`verify_filter_class` comprueba cada banda de un banco contra los límites de
aceptación de **IEC 61260-1:2014** (Tabla 1, con el mapeo de breakpoints a
fraccionales y la interpolación logarítmica de la norma) e informa de la clase
por banda con su margen en dB:

```python
from phonometry import OctaveFilterBank, verify_filter_class

bank = OctaveFilterBank(fs=48000, fraction=3, order=6)
result = verify_filter_class(bank)
print(result["overall_class"])          # 1
print(result["bands"][0])
# {'freq': 12.589254117941678, 'class': 1, 'margin_class1_db': 0.39999999999997266, 'margin_class2_db': 0.5999999999999727}
```

La propia máscara de aceptación de la Tabla 1 también es pública:
`class_limits(fraction, filter_class, omega)` devuelve los límites
mínimo/máximo de atenuación relativa en frecuencias normalizadas Ω = f/fm —
los mismos límites que usan el verificador y la figura de abajo.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay_es.png" alt="Respuesta Butterworth serpenteando entre las regiones prohibidas de la máscara de clase 1 de IEC 61260-1" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay_es_dark.png" alt="Respuesta Butterworth serpenteando entre las regiones prohibidas de la máscara de clase 1 de IEC 61260-1" style="width:80%">

*La respuesta del Butterworth de orden 6 (azul) serpentea entre las regiones
prohibidas: debe atenuar al menos la máscara roja fuera de la banda y no más
que la morada dentro de ella.*

Con parámetros por defecto (orden 6), **Butterworth cumple clase 1**, y también
lo hace **Chebyshev II**: su valor por defecto de `attenuation` es ahora `72` dB,
superando el límite de clase 1 de 70 dB en el stopband lejano (scipy fija el
suelo equirizado de cheby2 en exactamente `attenuation`, así que cualquier valor
≥ 70 dB cumple; el valor por defecto de 72 dB mantiene el mismo margen de banda
de paso de +0,400 dB que Butterworth). Chebyshev I, Elíptico y Bessel no cumplen
los límites de clase con orden 6: el rizado de banda de paso (cheby1/ellip) y la
caída lenta (bessel) violan la máscara.

## 7. Descomposición de la señal y estabilidad

Con `sigbands=True` puedes recuperar las componentes en el dominio del tiempo de
cada banda. Esto permite análisis avanzados o comparar cómo afectan distintas
arquitecturas (p. ej. Butterworth vs Chebyshev) a la fase y al transitorio.

```python
import numpy as np
from phonometry import octave_filter

# 1. Generar una señal (suma de 250 Hz y 1000 Hz)
fs = 48000
t = np.linspace(0, 0.5, int(fs * 0.5), endpoint=False)
y = np.sin(2 * np.pi * 250 * t) + np.sin(2 * np.pi * 1000 * t)

# 2. Comparar arquitecturas (Butterworth vs Chebyshev II)
spl_b, freq, xb_butter = octave_filter(y, fs=fs, fraction=1, sigbands=True, filter_type='butter')
spl_c2, _, xb_cheby2 = octave_filter(y, fs=fs, fraction=1, sigbands=True, filter_type='cheby2')

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

## 8. Filtrado de fase cero

Para análisis offline puedes eliminar por completo el retardo de grupo:
`zero_phase=True` filtra cada banda hacia delante y hacia atrás
(`scipy.signal.sosfiltfilt`), manteniendo las señales por banda alineadas con la
entrada. La atenuación efectiva se duplica y la banda de paso efectiva se
estrecha, reduciendo el nivel de banda ancha medido en ~0,2 a 0,3 dB por banda
(un tono puro dentro de banda no se ve afectado); prefiere el filtrado hacia
delante cuando el SPL absoluto de banda debe coincidir con el convenio de un
solo paso, y reserva la fase cero para cuando importa la envolvente temporal
(p. ej. decaimiento de reverberación). La opción es incompatible con el
procesado por bloques (stateful).

```python
from phonometry import OctaveFilterBank

# Usa `y` del snippet anterior.
bank = OctaveFilterBank(fs=48000, fraction=3)
spl, freq, xb = bank.filter(y, sigbands=True, zero_phase=True)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison_es.png" alt="Filtrado causal frente a fase cero de una ráfaga: la salida de fase cero queda alineada con la entrada" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison_es_dark.png" alt="Filtrado causal frente a fase cero de una ráfaga: la salida de fase cero queda alineada con la entrada" style="width:80%">

*El filtrado causal retrasa la ráfaga según el retardo de grupo del filtro; el
filtrado de fase cero la mantiene alineada con la entrada.*

---

**Normas.** IEC 61260-1:2014, *Electroacoustics — Octave-band and
fractional-octave-band filters — Part 1: Specifications* — las frecuencias
centrales y los bordes de banda en base 10 del §1 (5.2-5.5), las etiquetas
nominales de banda y los límites de aceptación de clase 1 / clase 2 de la
Tabla 1 (con el mapeo de breakpoints a fraccionales y la interpolación en
frecuencia logarítmica) verificados en el §6. ANSI S1.11-2004, *Octave-Band
and Fractional-Octave-Band Analog and Digital Filters* — el convenio de
bordes de banda sobre el que cada banco sitúa sus puntos de −3 dB. ISO 266
— la serie de frecuencias preferentes tras las etiquetas nominales de banda
que devuelve `nominal_frequencies`.

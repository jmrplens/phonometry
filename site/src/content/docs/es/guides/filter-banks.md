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

### Polos, ceros y estabilidad

Un paso-banda digital es una constelación de polos y ceros en el plano z: los
ceros en DC y Nyquist, o cerca de ellos, sujetan la respuesta lejos de la
banda (hasta el suelo de la banda atenuada, en los diseños equirizados), y
los polos se agrupan justo dentro del círculo unidad en los ángulos
$\omega = 2\pi f / f_s$ que abarca la banda de paso. De ahí salen dos
intuiciones. Primera, la selectividad es proximidad: cuanto más cerca del
círculo unidad están los polos, más abrupta es la banda y más tiempo resuena
el filtro (los picos de retardo de grupo de la sección 7 son esa resonancia,
medida). Segunda, la estabilidad es un margen, no una propiedad de la
arquitectura: un filtro IIR es estable solo mientras todos sus polos
permanecen estrictamente dentro del círculo unidad, y una banda estrecha a
una frecuencia de muestreo alta los empuja hacia fuera (radio del polo
$\approx 1 - \pi B / f_s$ para un ancho de banda $B$) y los aprieta entre
sí, hasta que los coeficientes en doble precisión ya no pueden representar
sus posiciones con exactitud. Las secciones de segundo orden (SOS) desactivan
la mitad del problema: cada par de polos conserva sus propios coeficientes,
de modo que los errores de redondeo quedan localizados en lugar de acumularse
en un único polinomio de orden alto. La otra mitad, la minúscula razón
$B / f_s$ en sí, es lo que arregla el diezmado.

### Diezmado multitasa

Una banda de tercio de octava de 25 Hz a 48 kHz abarca unos 5,8 Hz — el
0,024 % de Nyquist — con coeficientes tan rígidos que se vuelven
numéricamente inestables. El banco lo evita filtrando las bandas bajas a una
frecuencia diezmada:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multirate_es.svg" alt="Diezmado multitasa: las bandas altas se filtran a la frecuencia de entrada y las bajas tras un paso-bajo antialiasing y diezmado, para que las secciones SOS se mantengan numéricamente sanas" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multirate_es_dark.svg" alt="Diezmado multitasa: las bandas altas se filtran a la frecuencia de entrada y las bajas tras un paso-bajo antialiasing y diezmado, para que las secciones SOS se mantengan numéricamente sanas" style="width:92%">

Diezmar por $M$ reescala el problema: el mismo ancho de banda de 5,8 Hz se
vuelve $M$ veces mayor respecto al nuevo Nyquist, el radio de los polos se
separa del círculo unidad y los coeficientes SOS regresan a un rango bien
condicionado. El precio es una contabilidad que el banco paga internamente:
antes de cada etapa de diezmado debe ejecutarse un paso-bajo antialiasing,
porque una componente por encima del nuevo Nyquist que se pliegue hacia abajo
cae *dentro* de las bandas bajas que se están midiendo, y ningún filtro
posterior puede eliminarla.

### Trampas de aliasing

El banco protege sus propias etapas de diezmado, pero solo puede analizar lo
que la cadena de captura le entrega:

- **Plegado en el ADC.** La energía por encima de $f_s/2$ que llega al
  conversor sin un filtro antialiasing analógico se pliega dentro del rango
  de análisis y es indistinguible del sonido real dentro de banda. Las
  tarjetas de sonido lo filtran internamente; las cadenas de instrumentación
  a medida pueden no hacerlo.
- **Remuestreo barato.** Convertir una grabación de 44,1 kHz a 48 kHz con un
  remuestreador de baja calidad deja imágenes que sesgan las bandas más
  altas. Usa un remuestreador polifásico (`scipy.signal.resample_poly`) o,
  más sencillo, analiza a la frecuencia nativa: todas las funciones de
  phonometry aceptan `fs` directamente.
- **Bandas cerca de Nyquist.** Una banda cuyo borde superior se acerca a
  $f_s/2$ no puede realizar su respuesta de diseño: la transformada bilineal
  comprime allí el eje de frecuencias (el mismo efecto que los filtros de
  ponderación contrarrestan con `high_accuracy`). Mantén el borde de la banda
  superior holgadamente por debajo de Nyquist o sube `fs`, y deja que
  `verify_filter_class` informe del margen restante.

## 2. Comparación de filtros y zoom

Usamos secciones de segundo orden (SOS) en todos los filtros para garantizar la
estabilidad numérica. La siguiente gráfica compara las arquitecturas centrándose
en el punto de cruce a −3 dB.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison_es.svg" alt="Comparación de la respuesta en magnitud de las cinco arquitecturas para la banda de octava de 1 kHz, con zoom en el cruce a -3 dB" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison_es_dark.svg" alt="Comparación de la respuesta en magnitud de las cinco arquitecturas para la banda de octava de 1 kHz, con zoom en el cruce a -3 dB" style="width:80%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import sosfreqz
from phonometry import OctaveFilterBank

fs = 48000
fig, ax = plt.subplots(figsize=(9, 5))
for ftype in ("butter", "cheby1", "cheby2", "ellip", "bessel"):
    # limits selecciona únicamente la banda de octava de 1 kHz
    bank = OctaveFilterBank(fs, fraction=1, order=6, limits=[800, 1200],
                            filter_type=ftype)
    idx = int(np.argmin(np.abs(np.array(bank.freq) - 1000)))
    fsd = fs / bank.factor[idx]           # frecuencia real de la banda
    w, h = sosfreqz(bank.sos[idx], worN=16384, fs=fsd)
    ax.semilogx(w, 20 * np.log10(np.abs(h) + 1e-9), label=ftype)
ax.axhline(-3, color="gray", linestyle=":", label="-3 dB")
ax.set(xlim=(100, 8000), ylim=(-80, 5),
       xlabel="Frecuencia [Hz]", ylabel="Magnitud [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

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
| **Butterworth** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6_es.svg" alt="Respuesta en frecuencia del banco de filtros Butterworth de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco de filtros Butterworth de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:100%"> |
| **Chebyshev I** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6_es.svg" alt="Respuesta en frecuencia del banco Chebyshev I de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Chebyshev I de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:100%"> |
| **Chebyshev II** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6_es.svg" alt="Respuesta en frecuencia del banco Chebyshev II de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Chebyshev II de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:100%"> |
| **Elíptico** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6_es.svg" alt="Respuesta en frecuencia del banco elíptico de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco elíptico de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:100%"> |
| **Bessel** | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6_es.svg" alt="Respuesta en frecuencia del banco Bessel de banda de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Bessel de banda de octava" style="width:100%"> | <img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:100%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:100%"> |

<details>
<summary>Mostrar el código de esta figura</summary>

```python
from phonometry import metrology

# Una figura por arquitectura y fracción: la galería completa de respuestas
fs = 48000
for ftype in ("butter", "cheby1", "cheby2", "ellip", "bessel"):
    for fraction in (1, 3):
        # show=True dibuja la respuesta en frecuencia del banco
        metrology.OctaveFilterBank(fs=fs, fraction=fraction, order=6,
                                   limits=[12, 20000], filter_type=ftype,
                                   show=True)
```

</details>

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Butterworth de tercio de octava" style="width:60%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
from phonometry import metrology

# Dibuja la respuesta de este banco (1/3 de octava, orden 6, Butterworth)
metrology.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[12, 20000],
                           filter_type='butter', show=True)
```

</details>

### 2. Chebyshev I (`cheby1`)

Los filtros Chebyshev tipo I ofrecen una **caída más abrupta** que Butterworth a
cambio de rizado en la banda de paso. Útiles cuando se necesita alta selectividad
cerca de las frecuencias de corte.

```python
# Usa `x` y `fs` del snippet anterior.
# Selectividad con 0.1 dB de rizado en la banda de paso
spl, freq = octave_filter(x, fs, filter_type='cheby1', ripple=0.1)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Chebyshev I de tercio de octava" style="width:60%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
from phonometry import metrology

# Dibuja la respuesta de este banco (1/3 de octava, orden 6, Chebyshev I)
metrology.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[12, 20000],
                           filter_type='cheby1', ripple=0.1, show=True)
```

</details>

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Chebyshev II de tercio de octava" style="width:60%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
from phonometry import metrology

# Dibuja la respuesta de este banco (1/3 de octava, orden 6, Chebyshev II)
metrology.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[12, 20000],
                           filter_type='cheby2', show=True)
```

</details>

### 4. Elíptico (`ellip`)

Los filtros elípticos (Cauer) tienen la **transición más corta** (caída más
abrupta) para un orden dado. Presentan rizado tanto en la banda de paso como en
la atenuada.

```python
# Usa `x` y `fs` del snippet anterior.
# Máxima selectividad para aislamiento extremo entre bandas
spl, freq = octave_filter(x, fs, filter_type='ellip', ripple=0.1)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco elíptico de tercio de octava" style="width:60%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
from phonometry import metrology

# Dibuja la respuesta de este banco (1/3 de octava, orden 6, elíptico)
metrology.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[12, 20000],
                           filter_type='ellip', ripple=0.1, show=True)
```

</details>

### 5. Bessel (`bessel`)

Los filtros Bessel están optimizados para una **respuesta de fase lineal** y un
retardo de grupo mínimo. Preservan la forma de las ondas filtradas (transitorios)
mejor que ningún otro tipo, pero tienen la caída más lenta.

```python
# Usa `x` y `fs` del snippet anterior.
# Ideal para análisis de pulsos y preservación de transitorios
spl, freq = octave_filter(x, fs, filter_type='bessel')
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es.svg" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_es_dark.svg" alt="Respuesta en frecuencia del banco Bessel de tercio de octava" style="width:60%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
from phonometry import metrology

# Dibuja la respuesta de este banco (1/3 de octava, orden 6, Bessel)
metrology.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[12, 20000],
                           filter_type='bessel', show=True)
```

</details>

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4_es.svg" alt="Crossover Linkwitz-Riley de 4.º orden: paso-bajo, paso-alto y su suma plana" style="width:60%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4_es_dark.svg" alt="Crossover Linkwitz-Riley de 4.º orden: paso-bajo, paso-alto y su suma plana" style="width:60%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import freqz
from phonometry import linkwitz_riley

# Medimos ambas ramas: dividimos un impulso unitario y tomamos los espectros.
fs = 48000
impulse = np.zeros(fs)
impulse[0] = 1.0
low, high = linkwitz_riley(impulse, fs, freq=1000, order=4)

w, h_lp = freqz(low, worN=8192, fs=fs)
_, h_hp = freqz(high, worN=8192, fs=fs)

fig, ax = plt.subplots(figsize=(9, 5))
ax.semilogx(w, 20 * np.log10(np.abs(h_lp) + 1e-9), label="Paso-bajo (LR4)")
ax.semilogx(w, 20 * np.log10(np.abs(h_hp) + 1e-9), label="Paso-alto (LR4)")
ax.semilogx(w, 20 * np.log10(np.abs(h_lp + h_hp) + 1e-9), "--",
            label="Suma (plana)")
ax.set(xlim=(20, 20000), ylim=(-60, 5),
       xlabel="Frecuencia [Hz]", ylabel="Magnitud [dB]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay_es.svg" alt="Respuesta Butterworth serpenteando entre las regiones prohibidas de la máscara de clase 1 de IEC 61260-1" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay_es_dark.svg" alt="Respuesta Butterworth serpenteando entre las regiones prohibidas de la máscara de clase 1 de IEC 61260-1" style="width:80%">

*La respuesta del Butterworth de orden 6 (azul) serpentea entre las regiones
prohibidas: debe atenuar al menos la máscara roja fuera de la banda y no más
que la morada dentro de ella.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import sosfreqz
from phonometry import OctaveFilterBank, class_limits

fs = 48000
bank = OctaveFilterBank(fs, fraction=1, order=6, limits=[800, 1200])
idx = int(np.argmin(np.abs(np.array(bank.freq) - 1000)))
fm, fsd = bank.freq[idx], fs / bank.factor[idx]
w, h = sosfreqz(bank.sos[idx], worN=2**15, fs=fsd)
att = -20 * np.log10(np.abs(h) + 1e-12)
delta_a = att - np.interp(fm, w, att)     # atenuación relativa

grid = np.logspace(np.log10(0.05), np.log10(8), 2000)
lo1, hi1 = class_limits(1.0, 1, grid)     # atenuación mín/máx de clase 1

fig, ax = plt.subplots(figsize=(9, 5.5))
ax.fill_between(grid, -10, lo1, alpha=0.15, color="tab:red",
                label="Prohibido: atenuación insuficiente")
finite = np.isfinite(hi1)
ax.fill_between(grid[finite], hi1[finite], 90, alpha=0.15, color="tab:purple",
                label="Prohibido: atenuación excesiva")
ax.plot(w / fm, delta_a, label="Butterworth de orden 6")
ax.set(xscale="log", xlim=(0.08, 8), ylim=(-6, 90),
       xlabel="Frecuencia normalizada f / fm",
       ylabel="Atenuación relativa [dB]")
ax.legend()
plt.show()
```

</details>

Con parámetros por defecto (orden 6), **Butterworth cumple clase 1**, y también
lo hace **Chebyshev II**: su valor por defecto de `attenuation` es ahora `72` dB,
superando el límite de clase 1 de 70 dB en el stopband lejano (scipy fija el
suelo equirizado de cheby2 en exactamente `attenuation`, así que cualquier valor
≥ 70 dB cumple; el valor por defecto de 72 dB mantiene el mismo margen de banda
de paso de +0,400 dB que Butterworth). Chebyshev I, Elíptico y Bessel no cumplen
los límites de clase con orden 6: el rizado de banda de paso (cheby1/ellip) y la
caída lenta (bessel) violan la máscara.

### Clase 0 (IEC 61260:1995 / ANSI S1.11-2004)

La clase de prestaciones más estricta, la **clase 0**, la definió la edición
anterior **IEC 61260:1995** y su gemela estadounidense **ANSI S1.11-2004**
(ambas retiradas/sustituidas pero aún referenciadas para instrumentos de
laboratorio); IEC 61260-1:2014 la eliminó. Sus máscaras de clase 1/2 difieren
ligeramente de la edición de 2014, así que vive tras un conmutador `edition` en
lugar de mezclarse con la máscara de 2014:

```python
result = verify_filter_class(bank, edition="1995")   # clases 0, 1, 2
print(result["overall_class"])          # 0  (el Butterworth por defecto la supera)
print(result["bands"][0]["margin_class0_db"])
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_class0_mask_es.svg" alt="Corredores de aceptación anidados en la banda de paso para las clases 0, 1 y 2 de IEC 61260:1995 con la respuesta Butterworth de orden 6 dentro del corredor de clase 0 más estrecho" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_class0_mask_es_dark.svg" alt="Corredores de aceptación anidados en la banda de paso para las clases 0, 1 y 2 de IEC 61260:1995 con la respuesta Butterworth de orden 6 dentro del corredor de clase 0 más estrecho" style="width:80%">

*El corredor de clase 0 (±0,15 dB en el centro de banda) es el más estrecho; la
clase 1 (±0,3 dB) y la clase 2 (±0,5 dB) son progresivamente más anchas. El
Butterworth de orden 6 serpentea dentro de la clase 0 en toda la banda de paso.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import sosfreqz
from phonometry import OctaveFilterBank, class_limits

fs = 48000
bank = OctaveFilterBank(fs, fraction=1, order=6, limits=[800, 1200])
idx = int(np.argmin(np.abs(np.array(bank.freq) - 1000)))
fm, fsd = bank.freq[idx], fs / bank.factor[idx]
w, h = sosfreqz(bank.sos[idx], worN=2**15, fs=fsd)
att = -20 * np.log10(np.abs(h) + 1e-12)
delta_a = att - np.interp(fm, w, att)

# Solo banda de paso: fuera de los bordes el límite máximo es +inf.
g = 10 ** (3 / 10)
grid = np.linspace(g ** -0.5, g ** 0.5, 1500)
pb = (w / fm >= g ** -0.5) & (w / fm <= g ** 0.5)

fig, ax = plt.subplots(figsize=(9, 5.5))
for cls in (2, 1, 0):            # corredores anidados, clase 0 el más estrecho
    lo, hi = class_limits(1.0, cls, grid, edition="1995")
    ax.plot(grid, hi, label=f"Corredor de clase {cls}")
    ax.plot(grid, lo, color=ax.lines[-1].get_color())
ax.plot(w[pb] / fm, delta_a[pb], "k", lw=2, label="Butterworth de orden 6")
ax.set(xscale="log", xlim=(g ** -0.5, g ** 0.5), ylim=(-0.7, 6),
       xlabel="Frecuencia normalizada f / fm",
       ylabel="Atenuación relativa [dB]")
ax.legend()
plt.show()
```

</details>

### Qué significa físicamente una clase

Las máscaras son cotas de error en el peor caso de una *medición*, no
calificaciones abstractas:

- **En la banda de paso** el corredor acota cuánto puede desviarse la lectura
  del contenido dentro de banda: un banco de clase 1 lee un tono de centro de
  banda a ±0,4 dB de su nivel verdadero y uno de clase 2 a ±0,6 dB (Tabla 1
  de 2014; las máscaras de 1995, más estrictas, permitían ±0,3 dB para la
  clase 1 y ±0,15 dB para la clase 0). Hacia los bordes el corredor se
  ensancha, lo que es la admisión honesta de que un tono situado exactamente
  en un borde es genuinamente ambiguo entre dos bandas (ambas lo leen unos
  3 dB por debajo).
- **En la banda atenuada** la máscara de atenuación mínima acota la fuga del
  resto del espectro: lejos de la banda, la clase 1 exige al menos 70 dB de
  atenuación relativa (la razón por la que el valor por defecto de `cheby2`
  es 72 dB). En términos de energía, un tono fuera de banda tiene que ser
  unos 70 dB más fuerte que el contenido propio de la banda para duplicar su
  lectura de energía (+3 dB). La consecuencia práctica: al medir bandas muy
  por debajo de un tono dominante, la lectura toca fondo en la falda de fuga
  unos 70 dB por debajo, y una arquitectura más abrupta (o mayor orden) es la
  única forma de empujar ese suelo más abajo.
- **Para el presupuesto de incertidumbre**, la clase es la contribución del filtro a la
  incertidumbre de la medición: un banco de clase 1 añade hasta unas décimas
  de dB a un nivel de banda, comparable a los demás términos de tolerancia de
  un sonómetro de clase 1, y por eso las cadenas con calidad de instrumento
  especifican la clase de cada etapa en lugar de una única cifra global.

**¿Qué arquitectura alcanza qué clase?** El **valor por defecto de la biblioteca
— Butterworth de orden 6 — cumple clase 0** en las configuraciones que verifica
el conjunto de conformidad (bancos de octava y tercio de octava a 48 kHz), así
que no hace falta ninguna configuración especial para bancos de laboratorio en
ese rango. La tabla siguiente indica la mejor clase que alcanza cada arquitectura
con esa misma configuración de orden 6 / 48 kHz; las demás arquitecturas se
quedan por debajo de clase 0 porque cambian la máscara IEC por otra propiedad
*por construcción*:

| Arquitectura | Mejor clase (orden 6, fs 48 kHz) | Por qué |
| :--- | :---: | :--- |
| `butter` (por defecto) | **0** | Banda de paso máximamente plana, caída monótona — encaja en la máscara |
| `cheby2` | 1 | Banda de paso plana pero la relación de la máscara limita en clase 1 |
| `cheby1` | — | El rizado de banda de paso viola el límite de planitud |
| `ellip` | — | Rizado en banda de paso y atenuada |
| `bessel` | — | Retardo de grupo plano a costa de una caída lenta |

Así que el valor por defecto sensato es el habitual (Butterworth de orden 6):
supera la clase 0 en las configuraciones verificadas, mientras que las
arquitecturas alternativas son opciones deliberadas cuyo propósito (caída más
abrupta, fase lineal) va en contra de la máscara de clase. Fuera de estos
ajustes —`fraction` muy alto o bandas cercanas a Nyquist— vuelve a ejecutar
`verify_filter_class` para confirmar la clase que necesitas, y sube el orden si
una banda necesita más margen.

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_decomposition_es.svg" alt="Descomposición por bandas en el tiempo comparando Butterworth y Chebyshev II, incluida la respuesta al impulso" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_decomposition_es_dark.svg" alt="Descomposición por bandas en el tiempo comparando Butterworth y Chebyshev II, incluida la respuesta al impulso" style="width:80%">

*La gráfica compara las respuestas de **Butterworth** (azul, línea continua) y
**Chebyshev II** (rojo, discontinua). El panel inferior muestra la **respuesta al
impulso**, destacando las diferencias de estabilidad y decaimiento transitorio.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import OctaveFilterBank

fs = 48000
t = np.linspace(0, 0.5, int(fs * 0.5), endpoint=False)
y = np.sin(2 * np.pi * 250 * t) + np.sin(2 * np.pi * 1000 * t)

bank_b = OctaveFilterBank(fs=fs, fraction=1, order=6, limits=[100.0, 2000.0])
bank_c = OctaveFilterBank(fs=fs, fraction=1, order=6, limits=[100.0, 2000.0],
                          filter_type="cheby2")
_, freq, xb_butter = bank_b.filter(y, sigbands=True)
_, _, xb_cheby2 = bank_c.filter(y, sigbands=True)

fig, axes = plt.subplots(len(freq), 1, figsize=(9, 2 * len(freq)), sharex=True)
for ax, fc, xb, xc in zip(axes, freq, xb_butter, xb_cheby2):
    ax.plot(t, xb, label="Butterworth")
    ax.plot(t, xc, "--", label="Chebyshev II")
    ax.set_title(f"Banda de {fc:.0f} Hz")
    ax.set_xlim(0, 0.04)
axes[0].legend()
axes[-1].set_xlabel("Tiempo [s]")
plt.tight_layout()
plt.show()
```

</details>

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/group_delay_comparison_es.svg" alt="Retardo de grupo de la banda de 1 kHz para las cinco arquitecturas: Bessel casi plano, Chebyshev y elíptico con picos en los bordes" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/group_delay_comparison_es_dark.svg" alt="Retardo de grupo de la banda de 1 kHz para las cinco arquitecturas: Bessel casi plano, Chebyshev y elíptico con picos en los bordes" style="width:80%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import group_delay
from phonometry import OctaveFilterBank

fs = 48000
w = np.logspace(np.log10(500), np.log10(2000), 1024)
fig, ax = plt.subplots(figsize=(9, 5))
for ftype in ("butter", "cheby1", "cheby2", "ellip", "bessel"):
    bank = OctaveFilterBank(fs, fraction=1, order=6, limits=[800, 1200],
                            filter_type=ftype)
    idx = int(np.argmin(np.abs(np.array(bank.freq) - 1000)))
    fsd = fs / bank.factor[idx]
    # Retardo de grupo de una cascada SOS = suma del de sus secciones
    gd = sum(group_delay((sec[:3], sec[3:]), w=w, fs=fsd)[1]
             for sec in bank.sos[idx])
    ax.semilogx(w, gd / fsd * 1000, label=ftype)
ax.set(xlim=(500, 2000), xlabel="Frecuencia [Hz]",
       ylabel="Retardo de grupo [ms]")
ax.grid(True, which="both", alpha=0.3)
ax.legend()
plt.show()
```

</details>

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

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison_es.svg" alt="Filtrado causal frente a fase cero de una ráfaga: la salida de fase cero queda alineada con la entrada" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison_es_dark.svg" alt="Filtrado causal frente a fase cero de una ráfaga: la salida de fase cero queda alineada con la entrada" style="width:80%">

*El filtrado causal retrasa la ráfaga según el retardo de grupo del filtro; el
filtrado de fase cero la mantiene alineada con la entrada.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import OctaveFilterBank

fs = 48000
t = np.linspace(0, 0.15, int(fs * 0.15), endpoint=False)
x = np.zeros_like(t)                      # ráfaga de 250 Hz a mitad de trama
start, end = int(0.05 * fs), int(0.10 * fs)
x[start:end] = np.sin(2 * np.pi * 250 * t[start:end]) * np.hanning(end - start)

bank = OctaveFilterBank(fs=fs, fraction=1, order=6, limits=[200.0, 300.0])
_, _, fwd = bank.filter(x, sigbands=True, calculate_level=False)
_, _, zp = bank.filter(x, sigbands=True, calculate_level=False,
                       zero_phase=True)

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(t, x, color="gray", alpha=0.5, label="Ráfaga de entrada (250 Hz)")
ax.plot(t, fwd[0], label="Causal (retardo de grupo)")
ax.plot(t, zp[0], "--", label="zero_phase=True (alineado)")
ax.set(xlabel="Tiempo [s]", ylabel="Amplitud")
ax.legend()
plt.show()
```

</details>

## Referencias

- International Electrotechnical Commission. (2014). *Electroacoustics —
  Octave-band and fractional-octave-band filters — Part 1: Specifications*
  (IEC 61260-1:2014).
  [Catálogo IEC](https://webstore.iec.ch/en/publication/5063).
  Las matemáticas de bordes de banda de la sección 1 y las máscaras de
  aceptación de clase verificadas en la sección 6.
- Oppenheim, A. V., & Schafer, R. W. (2010). *Discrete-time signal processing*
  (3.ª ed.). Pearson. ISBN 978-0-13-198842-2.
  [Ficha en Open Library](https://openlibrary.org/isbn/9780131988422).
  La teoría de polos y ceros, estabilidad y multitasa condensada en la
  sección 1: cascadas SOS, transformada bilineal y diezmado.
- Smith, J. O. *Introduction to digital filters with audio applications*
  (libro en línea). Center for Computer Research in Music and Acoustics
  (CCRMA), Universidad de Stanford.
  [ccrma.stanford.edu/~jos/filters](https://ccrma.stanford.edu/~jos/filters/).
  Tratamiento gratuito y complementario del diseño y análisis de filtros
  digitales, de la geometría de polos y ceros a la estabilidad.

## Normas

IEC 61260-1:2014, *Electroacoustics — Octave-band and
fractional-octave-band filters — Part 1: Specifications* — las frecuencias
centrales y los bordes de banda en base 10 del §1 (5.2-5.5), las etiquetas
nominales de banda y los límites de aceptación de clase 1 / clase 2 de la
Tabla 1 (con el mapeo de breakpoints a fraccionales y la interpolación en
frecuencia logarítmica) verificados en el §6. IEC 61260:1995 y ANSI S1.11-2004,
*Octave-Band and Fractional-Octave-Band … Filters* — la Tabla 1 de la edición
retirada (idéntica entre ambas) aporta la máscara de clase 0 más estricta que
ofrece `edition="1995"`, y el convenio de bordes de banda sobre el que cada
banco sitúa sus puntos de −3 dB. ISO 266
— la serie de frecuencias preferentes en la que se basan las etiquetas nominales de banda
que devuelve `nominal_frequencies`.

## Véase también

- Referencia de la API: [`phonometry`](/phonometry/es/reference/api/filters/phonometry/), [`metrology.core`](/phonometry/es/reference/api/filters/core/) y [`metrology.parametric_filters`](/phonometry/es/reference/api/filters/parametric-filters/).

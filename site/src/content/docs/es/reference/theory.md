---
title: "Teoría"
description: "Normas, matemáticas y decisiones de diseño detrás de PyOctaveBand."
---

## Frecuencias de banda de octava (ANSI S1.11 / IEC 61260)

Las frecuencias centrales (fm) y los bordes (f1, f2) usan una razón en base 10:

$$
G = 10^{0.3}
$$

**Frecuencia central:**

$$
f_m = 1000 \cdot G^{x/b}
$$

(para b impar)

**Bordes de banda:**

$$
f_1 = f_m \cdot G^{-1/2b}, \quad f_2 = f_m \cdot G^{1/2b}
$$

## Resolución frecuencial vs separación de bins FFT

`octavefilter` es un **banco de filtros de octava fraccional en el dominio del
tiempo**, no un estimador espectral FFT/Welch. Por tanto, su resultado no tiene
una resolución frecuencial en el sentido `fs / nfft`.

Para `fraction=3`, la salida contiene un nivel escalar por banda de tercio de
octava. La granularidad relevante es la definición normalizada de la banda:
frecuencia central, borde inferior y borde superior. Como las bandas de octava
fraccional están espaciadas logarítmicamente, su ancho absoluto en Hz crece con
la frecuencia mientras su ancho relativo se mantiene aproximadamente constante.

Por ejemplo, con `fraction=3` y `limits=[12, 20000]`, la banda de tercio de
octava en torno a 1 kHz es aproximadamente:

| Banda nominal | Borde inferior | Centro | Borde superior | Ancho |
| :--- | ---: | ---: | ---: | ---: |
| 1 kHz | 891.25 Hz | 1000.00 Hz | 1122.02 Hz | 230.77 Hz |

Puedes inspeccionar las bandas exactas con:

```python
from pyoctaveband import getansifrequencies

fc, fl, fu, labels = getansifrequencies(fraction=3, limits=[12, 20000])
for label, center, lower, upper in zip(labels, fc, fl, fu):
    print(label, center, lower, upper, upper - lower)
```

Si necesitas bins FFT de banda estrecha para inspección tonal, ejecuta
Welch/FFT sobre la señal original y usa los bordes de banda de PyOctaveBand como
máscaras:

```python
import numpy as np
from scipy import signal
from pyoctaveband import octavefilter, getansifrequencies

fs = 100_000
x = pressure_signal_pa  # señal de presión 1D en Pa

# Niveles de tercio de octava normalizados de PyOctaveBand.
levels, centers = octavefilter(
    x,
    fs=fs,
    fraction=3,
    limits=[12, 20_000],
)

# Las mismas definiciones de banda, incluidos los bordes.
fc, fl, fu, labels = getansifrequencies(fraction=3, limits=[12, 20_000])

# Estimación Welch de banda estrecha sobre la señal original.
nperseg = min(2**15, len(x))
freq_bins, psd = signal.welch(
    x,
    fs=fs,
    window="hann",
    nperseg=nperseg,
    noverlap=nperseg // 2,
    scaling="density",
)

# Ejemplo: listar los bins Welch dentro de la banda más cercana a 1 kHz.
band_index = int(np.argmin(np.abs(np.asarray(fc) - 1000.0)))
in_band = (freq_bins >= fl[band_index]) & (freq_bins <= fu[band_index])

print("Banda de tercio de octava seleccionada:", labels[band_index])
print("Separación de bins Welch:", freq_bins[1] - freq_bins[0], "Hz")
for f, pxx in zip(freq_bins[in_band], psd[in_band]):
    print(f, pxx)
```

Esto mantiene separados los dos conceptos: PyOctaveBand da niveles de octava
fraccional normalizados, mientras Welch da bins FFT de banda estrecha. Con
`fs=100000` y `nperseg=2**15`, la separación de bins Welch es de unos `3.05 Hz`.
La ventana y el solape afectan al leakage y a la varianza del promediado, pero
no cambian la separación de bins de cada segmento FFT.

Con `sigbands=True`, `octavefilter` también puede devolver la forma de onda
filtrada por cada banda. Aplicar Welch/FFT a una de esas señales puede servir
como vista diagnóstica del contenido dentro de esa banda, pero no recupera bins
FFT a partir de los niveles escalares por banda.

## Respuestas en magnitud |H(jw)|

La librería implementa los prototipos clásicos estándar:

**1. Butterworth:** banda de paso máximamente plana.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + (\omega/\omega_c)^{2n}}}
$$

**2. Chebyshev I:** rizado uniforme en la banda de paso, caída más abrupta.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + \epsilon^2 T_n^2(\omega/\omega_c)}}
$$

**3. Chebyshev II:** Chebyshev inverso, rizado uniforme en la banda atenuada,
banda de paso plana.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + \frac{1}{\epsilon^2 T_n^2(\omega_{stop}/\omega)}}}
$$

**4. Elíptico:** rizado en ambas bandas, máxima selectividad.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + \epsilon^2 R_n^2(\omega/\omega_c, L)}}
$$

**5. Bessel:** retardo de grupo máximamente plano (fase lineal).

$$
H(s) = \frac{\theta_n(0)}{\theta_n(s/\omega_0)}
$$

(donde $\theta_n$ es el polinomio de Bessel inverso)

### Colocación de los bordes de banda

Para todas las arquitecturas, el banco sitúa los **puntos de −3 dB en los bordes
de banda**. Dos casos requieren tratamiento especial:

- **Chebyshev II**: en scipy, `Wn` es el borde de la banda *atenuada*.
  PyOctaveBand mapea analíticamente los bordes de −3 dB deseados a bordes de
  banda atenuada — la razón de transición del prototipo es
  $\cosh(\operatorname{acosh}(\sqrt{10^{A/10}-1})/N)$ — aplicando la
  transformación paso-bajo→paso-banda en el dominio bilineal pre-warpeado, de
  modo que el mapeo es exacto incluso para bandas diezmadas cercanas a Nyquist.
- **Bessel**: se diseña con `norm="mag"`, que define el punto de −3 dB
  exactamente en `Wn` (la norma `phase` desplazaría los bordes a unos −10 dB).

## Diseño del banco y estabilidad numérica

Para garantizar **estabilidad total** en todo el espectro audible (incluso a
frecuencias bajas como 16 Hz con frecuencias de muestreo altas), PyOctaveBand
emplea dos estrategias fundamentales:

1. **Secciones de segundo orden (SOS):** todos los filtros se implementan como
   biquads en cascada, evitando la pérdida catastrófica de precisión de las
   funciones de transferencia de orden alto.
2. **Diezmado multitasa:** para las bandas graves, la señal se diezma antes de
   filtrar y se interpola después. Esto mantiene los polos digitales lejos del
   borde del círculo unidad, evitando oscilaciones y ruido. Los bancos
   Chebyshev II reservan margen de diezmado adicional para que sus bordes de
   banda atenuada queden por debajo del Nyquist diezmado.

## Curvas de ponderación (IEC 61672-1)

La función de transferencia de la ponderación A:

$$
R_A(f) = \frac{12194^2 \cdot f^4}{(f^2 + 20.6^2)\sqrt{(f^2 + 107.7^2)(f^2 + 737.9^2)}(f^2 + 12194^2)}
$$

$$
A(f) = 20 \log_{10}(R_A(f)) + 2.00
$$

El filtro digital se obtiene de los polos/ceros analógicos mediante la
transformación bilineal. Como esta comprime las frecuencias cerca de Nyquist, el
modo `high_accuracy` por defecto diseña y ejecuta el filtro a una frecuencia
interna sobremuestreada (≥ 96 kHz) — consulta
[Ponderación frecuencial](/PyOctaveBand/es/guides/weighting/).

## Integración temporal

Implementada como un integrador exponencial IIR de primer orden:

$$
y[n] = \alpha \cdot x^2[n] + (1 - \alpha) \cdot y[n-1]
$$

$$
\alpha = 1 - e^{-1 / (f_s \cdot \tau)}
$$

donde `tau` es la constante de tiempo (p. ej. 125 ms para Fast).

La condición inicial por defecto es `y[-1] = 0`. Usa `initial_state='first'`
para partir de la energía de la primera muestra, o pasa un escalar/array con el
estado cuadrático medio anterior. Consulta
[Por qué PyOctaveBand](/PyOctaveBand/es/reference/why-pyoctaveband/) para la
verificación de esta implementación con ráfagas de tono de IEC 61672-1.

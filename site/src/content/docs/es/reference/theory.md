---
title: "Teoría"
description: "Normas, matemáticas y decisiones de diseño detrás de phonometry."
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
from phonometry import getansifrequencies

fc, fl, fu, labels = getansifrequencies(fraction=3, limits=[12, 20000])
for label, center, lower, upper in zip(labels, fc, fl, fu):
    print(label, center, lower, upper, upper - lower)
```

Si necesitas bins FFT de banda estrecha para inspección tonal, ejecuta
Welch/FFT sobre la señal original y usa los bordes de banda de phonometry como
máscaras:

```python
import numpy as np
from scipy import signal
from phonometry import octavefilter, getansifrequencies

fs = 100_000
x = pressure_signal_pa  # señal de presión 1D en Pa

# Niveles de tercio de octava normalizados de phonometry.
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

Esto mantiene separados los dos conceptos: phonometry da niveles de octava
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
  phonometry mapea analíticamente los bordes de −3 dB deseados a bordes de
  banda atenuada — la razón de transición del prototipo es
  $\cosh(\operatorname{acosh}(\sqrt{10^{A/10}-1})/N)$ — aplicando la
  transformación paso-bajo→paso-banda en el dominio bilineal pre-warpeado, de
  modo que el mapeo es exacto incluso para bandas diezmadas cercanas a Nyquist.
- **Bessel**: se diseña con `norm="mag"`, que define el punto de −3 dB
  exactamente en `Wn` (la norma `phase` desplazaría los bordes a unos −10 dB).

## Diseño del banco y estabilidad numérica

Para garantizar **estabilidad total** en todo el espectro audible (incluso a
frecuencias bajas como 16 Hz con frecuencias de muestreo altas), phonometry
emplea dos estrategias fundamentales:

```mermaid
flowchart LR
    X["Señal de entrada\nfs"] --> D{"¿Banda grave?"}
    D -- "sí" --> R["Diezmar\nresample_poly (1/M)"] --> S1["Filtro SOS de banda\na fs/M"]
    D -- "no" --> S2["Filtro SOS de banda\na fs"]
    S1 --> L["Nivel de banda (RMS/pico)"]
    S2 --> L
    S1 -- "sigbands=True" --> U["Interpolar de vuelta\nresample_poly (M/1)"] --> Y["Señal de banda\na fs"]
    S2 -- "sigbands=True" --> Y
```

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
[Ponderación frecuencial](/phonometry/es/guides/weighting/).

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
[Por qué phonometry](/phonometry/es/reference/why-phonometry/) para la
verificación de esta implementación con ráfagas de tono de IEC 61672-1.

## Ponderación G (ISO 7196)

La curva G extiende la ponderación frecuencial al rango de los infrasonidos. La Tabla 1 de ISO 7196:1995 (p. 2) la define mediante cuatro ceros en el origen y cuatro pares de polos complejos conjugados, dados como coordenadas en Hz (multiplicadas por $2\pi$ para obtener rad/s):

$$
z_{1..4} = 0, \qquad
p = 2\pi \left\{ -0.707 \pm j0.707,\; -19.27 \pm j5.16,\; -14.11 \pm j14.11,\; -5.16 \pm j19.27 \right\} \ \text{Hz}
$$

La ganancia $k$ se elige para que la respuesta sea exactamente **0 dB a 10 Hz** (apartado 4):

$$
k = \left| \frac{\prod_i (j\omega_{10} - p_i)}{\prod_i (j\omega_{10} - z_i)} \right|, \qquad \omega_{10} = 2\pi \cdot 10 \ \text{rad/s}
$$

Los cuatro ceros frente a ocho polos dan forma a la respuesta característica: una subida de aproximadamente **+12 dB/octava entre 1 Hz y 20 Hz**, con caídas de aproximadamente **24 dB/octava** por debajo de 1 Hz y por encima de 20 Hz. Los infrasonidos necesitan su propia curva porque, cerca del umbral de audición, la sonoridad percibida de los tonos de muy baja frecuencia crece con el nivel de presión sonora mucho más abruptamente que a frecuencias medias — un pequeño incremento en dB sobre el umbral produce un gran salto de sonoridad —, de modo que la curva A (anclada en 1 kHz) distorsiona por completo la molestia infrasónica.

Como G actúa sobre 0,25 Hz – 315 Hz, la transformación bilineal simple ya es exacta en ese rango, y no se aplica el sobremuestreo interno usado en los diseños A/C (cuya acción se extiende hasta 16 kHz).

Consulta la [guía de ponderación frecuencial](/phonometry/es/guides/weighting/) para su uso.

## Líneas isofónicas (ISO 226:2023)

Un tono tiene un *nivel de sonoridad* de $L_N$ fonios cuando se juzga igual de sonoro que un tono puro de 1 kHz a $L_N$ dB SPL. La Fórmula (1) de ISO 226:2023 (apartado 4.1, p. 2) da el SPL de un tono puro a la frecuencia $f$ que alcanza el nivel de sonoridad $L_N$:

$$
L_f = \frac{10}{\alpha_f} \log_{10}\!\left[ \left(4 \cdot 10^{-10}\right)^{0.3 - \alpha_f} \left( 10^{\,0.03 L_N} - 10^{\,0.072} \right) + 10^{\,\alpha_f (T_f + L_U)/10} \right] - L_U
$$

La Fórmula (2) (apartado 4.2) la invierte, devolviendo el nivel de sonoridad de un tono a SPL $L_f$:

$$
L_N = \frac{100}{3} \log_{10}\!\left[ \frac{10^{\,\alpha_f (L_f + L_U)/10} - 10^{\,\alpha_f (T_f + L_U)/10}}{\left(4 \cdot 10^{-10}\right)^{0.3 - \alpha_f}} + 10^{\,0.072} \right]
$$

Los tres parámetros provienen de la Tabla 1 (p. 4), tabulados en las 29 frecuencias preferentes de tercio de octava de ISO 266 desde 20 Hz hasta 12,5 kHz:

- $\alpha_f$ — exponente de la percepción de sonoridad a la frecuencia $f$,
- $L_U$ — magnitud de la función de transferencia lineal, normalizada en 1 kHz ($L_U = 0$ en 1 kHz),
- $T_f$ — umbral de audición en $f$, en dB.

La norma **no especifica interpolación** entre las frecuencias tabuladas. La Fórmula (1) está especificada para **20 fonios a 90 fonios** entre 20 Hz y 4 kHz, y solo hasta **80 fonios entre 5 kHz y 12,5 kHz** — por encima de 80 fonios la línea isofónica se detiene, por tanto, en 4 kHz. Los valores fuera de estos límites obtenidos con la Fórmula (2) son extrapolaciones que la norma califica de meramente informativas.

Consulta la [guía de niveles](/phonometry/es/guides/levels/) para su uso.

## Prominencia tonal: TNR y PR (ECMA-418-1)

Ambos métodos operan sobre un espectro de potencia con ventana de Hann promediado en RMS (apartados 11.1 / 12.1) y usan el modelo de bandas críticas del apartado 10. El ancho de banda crítico centrado en un tono a $f$ es (Fórmula 2):

$$
\Delta f_c = 25.0 + 75.0 \left(1.0 + 1.4 \left(\tfrac{f}{1000}\right)^2\right)^{0.69} \ \text{Hz}
$$

Los bordes de banda se colocan **aritméticamente** para $f \le 500$ Hz (Fórmulas 4–5): $f_{1,2} = f \mp \Delta f_c / 2$, y **geométricamente** por encima (Fórmulas 7–8): $f_1 = -\Delta f_c/2 + \sqrt{\Delta f_c^2 + 4 f^2}/2$, $f_2 = f_1 + \Delta f_c$.

**TNR** (apartado 11). La banda del tono abarca los mínimos espectrales a ambos lados del pico dentro del 15 % de $\Delta f_c$ (apartado 11.2). A la potencia del tono se le resta la recta que conecta los bins de los bordes de banda (Fórmula 9): sobre los $N$ bins de la banda del tono, $P_t = \sum_k P_k - (P_{\text{lo}} + P_{\text{hi}})\,N/2$. La potencia del ruido enmascarante es la potencia restante de la banda crítica reescalada al ancho de banda crítico completo (Fórmula 10): $P_n = (P_{\text{band}} - P_t) \cdot \Delta f_c / \Delta f_{\text{band}}$, y $\mathrm{TNR} = 10\log_{10}(P_t/P_n)$ (Fórmula 11). El criterio de prominencia (Fórmulas 12–13) es

$$
\mathrm{TNR}_{\text{crit}} = \begin{cases} 8.0 + 8.33 \log_{10}(1000/f_t) \ \text{dB} & f_t < 1\,\text{kHz} \\ 8.0 \ \text{dB} & f_t \ge 1\,\text{kHz} \end{cases}
$$

**PR** (apartado 12) compara el nivel de la banda crítica centrada en el tono, $L_M$, con la potencia media de las dos bandas críticas **contiguas** $L_L$, $L_U$ (bordes según las Fórmulas ajustadas 21–22 con las Tablas 2–3): $\mathrm{PR} = 10\log_{10} P_M - 10\log_{10}\left[(P_L + P_U)/2\right]$ (Fórmula 23). Para $f_t \le 171.4$ Hz la banda inferior se trunca en 20 Hz y su potencia se reescala a un **ancho de banda de 100 Hz** (Fórmula 24). El criterio (Fórmulas 25–26) es 9,0 dB para $f_t \ge 1$ kHz, y crece como $9.0 + 10.0\log_{10}(1000/f_t)$ por debajo. Los tonos se evalúan dentro del rango de interés de 89,1 Hz – 11,2 kHz (apartados 11.5 / 12.6).

Consulta la [guía de niveles](/phonometry/es/guides/levels/) para su uso.

## Métricas de evento y de dosis

El **nivel de exposición sonora** (SEL; LAE con ponderación A, IEC 61672-1:2013) normaliza la energía de un evento discreto (sobrevuelo de un avión, paso de un tren) a una duración de referencia de 1 s:

$$
\mathrm{SEL} = L_{eq,T} + 10 \log_{10}\!\left(\frac{T}{T_0}\right), \qquad T_0 = 1\ \text{s}
$$

La **exposición sonora** $E$ (IEC 61252, 3.1) es la integral temporal del cuadrado de la presión sonora ponderada A, expresada en pascales al cuadrado por hora:

$$
E = \int_0^T p_A^2(t)\, dt = \overline{p_A^2} \cdot T \quad [\text{Pa}^2\text{h}]
$$

Cuando la grabación es una muestra representativa de una jornada más larga, $E$ escala el cuadrático medio medido por la duración real de la exposición. El **nivel normalizado a 8 h** (IEC 61252, 3.3) convierte la exposición en el nivel estacionario que transporta la misma energía a lo largo de una jornada laboral nominal:

$$
L_{EX,8h} = 10 \log_{10}\!\left(\frac{E}{8\ \text{h} \cdot p_0^2}\right), \qquad p_0 = 20\ \mu\text{Pa}
$$

Es idéntico al $L_{EP,d}$ de la Directiva 86/188/CEE y al $L_{EX,8h}$ de ISO 1999 (BS EN 61252:1995, 3.3 NOTAS 5–6). El ancla de BS EN 61252:1995 (3.3 NOTA 4): una exposición de **3,2 Pa²h corresponde a un $L_{EX,8h}$ de exactamente 90 dB**.

**LCpeak** (IEC 61672-1:2013, subapartado 5.13) es el máximo absoluto de la presión sonora ponderada C expresado en dB, $L_{Cpeak} = 20\log_{10}(\max|p_C(t)|/p_0)$ — la magnitud detrás de los límites de acción laborales de 135/137/140 dB(C). La implementación se verifica contra las respuestas de referencia de un ciclo y de medio ciclo de la Tabla 5.

Consulta la [guía de niveles](/phonometry/es/guides/levels/) para su uso y la [guía de calibración](/phonometry/es/guides/calibration/) para configurar la escala absoluta.

## Descriptores ambientales (ISO 1996-1)

El **nivel día-tarde-noche** $L_{den}$ (ISO 1996-1:2016, 3.6.4) es un promedio energético sobre las 24 h del día con penalizaciones de **+5 dB para la tarde** y **+10 dB para la noche**:

$$
L_{den} = 10 \log_{10}\!\left\{\frac{1}{24}\left[ t_d\, 10^{0.1 L_{day}} + t_e\, 10^{0.1 (L_{evening} + 5)} + t_n\, 10^{0.1 (L_{night} + 10)} \right]\right\}
$$

con duraciones de periodo por defecto $(t_d, t_e, t_n) = (12, 4, 8)$ h — cada país puede definir los periodos de forma distinta (3.6.4 Nota 1). El **nivel día-noche** $L_{dn}$ (3.6.5) prescinde del periodo de tarde:

$$
L_{dn} = 10 \log_{10}\!\left\{\frac{1}{24}\left[ t_d\, 10^{0.1 L_{day}} + t_n\, 10^{0.1 (L_{night} + 10)} \right]\right\}, \qquad (t_d, t_n) = (15, 9)\ \text{h}
$$

Ambos son casos particulares del **nivel de evaluación compuesto de día completo** (6.5, que generaliza las Fórmulas 5–6), donde cada periodo $i$ aporta su nivel de evaluación $L_i$ más un ajuste $K_i$, ponderado por su fracción del día:

$$
L_R = 10 \log_{10}\!\left[ \sum_i \frac{h_i}{24}\, 10^{0.1 (L_i + K_i)} \right], \qquad \sum_i h_i = 24\ \text{h}
$$

Los ajustes $K_i$ cubren las penalizaciones horarias (ISO 1996-1 Tabla A.1: tarde 5 dB, noche 10 dB) así como los ajustes por carácter de la fuente — p. ej. penalizaciones tonales, que las evaluaciones TNR/PR de ECMA-418-1 permiten justificar objetivamente.

Consulta la [guía de niveles](/phonometry/es/guides/levels/) para su uso.

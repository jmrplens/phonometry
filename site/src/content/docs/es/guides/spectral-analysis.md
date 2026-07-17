---
title: "Análisis espectral calibrado"
description: "Los estimadores de Welch de Bendat y Piersol con su calidad estadística: densidad espectral de potencia y cruzada con el número efectivo de promedios, errores aleatorios normalizados e intervalos de confianza chi-cuadrado, el espectro de salida coherente con la relación señal-ruido espectral, suavizado en fracciones de octava con núcleo de potencia constante, y generadores de ruido de colores con pendiente exacta en ley de potencias."
---

Un espectro sin su incertidumbre es media medición. Esta página cubre los
estimadores espectrales de Welch de `phonometry.metrology` que informan,
junto al propio espectro, de la calidad estadística de la estimación
siguiendo a Bendat y Piersol, *Random Data: Analysis and Measurement
Procedures* (4.ª ed., 2010): la **densidad espectral de potencia** y la
**densidad espectral cruzada** con el número efectivo de promedios, el error
aleatorio normalizado y los intervalos de confianza chi-cuadrado; el
**espectro de salida coherente** que separa una salida medida en la parte
explicada linealmente por la entrada y el resto de ruido, con la relación
señal-ruido espectral; un **suavizador en fracciones de octava** con núcleo
de potencia constante; y **generadores de ruido de colores** con pendiente
exacta en ley de potencias para ejercitar todo lo anterior. Cada fórmula de
error es una forma cerrada del libro, verificada por Monte Carlo con semilla
en la batería de tests.

## 1. Densidad espectral de potencia con su error estadístico

`power_spectral_density` estima la densidad autoespectral unilateral
`Gxx(f)` por el método de Welch: el registro se divide en segmentos con
ventana (Hann por defecto) y solape del 50 % cuyos periodogramas se
promedian. No se aplica eliminación de tendencia, así que la calibración
absoluta se conserva: una señal en pascales da `Pa²/Hz`. Hay dos escalados:
`'density'` (unidades²/Hz, integra a la potencia de la señal) y `'spectrum'`
(unidades², lee directamente la potencia de tonos discretos).

Promediar `nd` segmentos independientes da al estimador `2·nd` grados de
libertad chi-cuadrado (ec. 8.162), de donde sale todo lo demás:

$$
\varepsilon_r[\hat{G}_{xx}] = \frac{1}{\sqrt{n_d}}, \qquad
\frac{n\,\hat{G}_{xx}}{\chi^2_{n;\,\alpha/2}} \le G_{xx} \le
\frac{n\,\hat{G}_{xx}}{\chi^2_{n;\,1-\alpha/2}}, \quad n = 2 n_d .
$$

Con segmentos solapados y con ventana los promedios están correlacionados, así
que el resultado informa tanto del número bruto de segmentos (`n_segments`)
como del número **efectivo** de promedios independientes (`n_averages`),
calculado con la fórmula de correlación de ventana de Welch (1967) que
Bendat y Piersol citan en la sección 11.5.2.2: para Hann con solape del 50 %,
aproximadamente 0,95 del número bruto. El error aleatorio y el intervalo de
confianza usan el valor efectivo. En DC, y en Nyquist con longitud de
segmento par, el espectro unilateral tiene una sola componente de Fourier
real, así que esos bins llevan la mitad de grados de libertad y un intervalo
proporcionalmente más ancho.

```python
from phonometry import power_spectral_density

res = power_spectral_density(signal, fs)          # Hann, solape 50 %, IC 95 %
print(res.n_averages, res.random_error)           # nd y 1/sqrt(nd)
print(res.ci_lower[10], res.psd[10], res.ci_upper[10])
res.plot()                                        # PSD en dB con la banda de IC
```

El **sesgo de resolución** es la otra mitad del presupuesto de error: un
ancho de banda de análisis finito `Be` (expuesto como
`resolution_bandwidth`, el ancho de banda de ruido efectivo de la ventana)
suaviza los rasgos espectrales abruptos, siempre en la dirección de reducir
el rango dinámico (ec. 8.139). Para un pico resonante de ancho de banda de
media potencia `Br`, el sesgo normalizado de primer orden es la forma
cerrada de la ec. 8.141, expuesta como `resolution_bias_error`:

$$
\varepsilon_b[\hat{G}_{xx}(f_r)] \approx -\frac{1}{3}\left(\frac{B_e}{B_r}\right)^2 .
$$

```python
from phonometry import resolution_bias_error

eps_b = resolution_bias_error(res.resolution_bandwidth, 25.0)  # pico de Br = 25 Hz
```

Un `Be` estrecho (segmentos largos) suprime el sesgo pero deja menos
promedios y un error aleatorio mayor; los dos requisitos sobre la longitud
de segmento tiran en direcciones opuestas, y ese es exactamente el
compromiso que los números expuestos hacen visible.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/psd_confidence_smoothing_es.svg" alt="Densidad espectral de potencia de Welch de ruido rosa en dB por Hz entre 20 Hz y 20 kHz, con la banda de confianza chi-cuadrado del 95 por ciento sombreada alrededor de la estimación, la curva suavizada en 1/3 de octava encima y la ley de potencias exacta de -3,01 dB por octava como línea discontinua de referencia" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/psd_confidence_smoothing_es_dark.svg" alt="Densidad espectral de potencia de Welch de ruido rosa en dB por Hz entre 20 Hz y 20 kHz, con la banda de confianza chi-cuadrado del 95 por ciento sombreada alrededor de la estimación, la curva suavizada en 1/3 de octava encima y la ley de potencias exacta de -3,01 dB por octava como línea discontinua de referencia" style="width:82%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import (
    fractional_octave_smoothing,
    noise_signal,
    power_spectral_density,
)

fs = 48000.0
x = noise_signal(fs, 20.0, color="pink", seed=11)
res = power_spectral_density(x, fs, nperseg=4096)
band = (res.frequencies >= 20.0) & (res.frequencies <= 20000.0)
freqs = res.frequencies[band]
smooth = fractional_octave_smoothing(res.frequencies, res.psd, 3.0)[band]

fig, ax = plt.subplots(figsize=(10, 6))
ax.fill_between(freqs, 10 * np.log10(res.ci_lower[band]),
                10 * np.log10(res.ci_upper[band]), alpha=0.3,
                label="Intervalo de confianza chi-cuadrado del 95 %")
ax.semilogx(freqs, 10 * np.log10(res.psd[band]), lw=1.0,
            label="Estimación de la PSD de Welch")
ax.semilogx(freqs, 10 * np.log10(smooth), lw=2.2,
            label="Suavizado en 1/3 de octava")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("PSD [dB re 1/Hz]")
ax.legend()
plt.show()
```

</details>

## 2. Densidad espectral cruzada

`cross_spectral_density` estima la `Gxy(f)` compleja entre dos canales con
el mismo núcleo de Welch, e informa de la coherencia ordinaria
`γ²xy = |Gxy|²/(Gxx·Gyy)` junto a los errores aleatorios de Bendat y Piersol
de la magnitud y la fase (ecs. 9.33 y 9.52, con la coherencia medida en
lugar del valor verdadero desconocido, como recomienda el libro para datos
medidos):

$$
\varepsilon_r[|\hat{G}_{xy}|] = \frac{1}{|\gamma_{xy}|\sqrt{n_d}}, \qquad
\mathrm{s.d.}[\hat{\theta}_{xy}] =
\frac{\left(1-\gamma^2_{xy}\right)^{1/2}}{|\gamma_{xy}|\sqrt{2 n_d}} .
$$

Ambos se reducen cuando la coherencia se acerca a uno: un par fuertemente
coherente necesita muchos menos promedios para la misma confianza. La fase
se devuelve desenrollada, así que su pendiente frente a la frecuencia es el
retardo de grupo `τ_g = -dφ/(2π·df)`; para un camino de retardo puro la fase
es lineal y esa pendiente lee directamente el retardo de propagación.

```python
from phonometry import cross_spectral_density

res = cross_spectral_density(x, y, fs)
print(res.magnitude_random_error[100], res.phase_std[100])  # errores del bin 100
res.plot()   # magnitud, fase con banda ±sigma, coherencia
```

## 3. Espectro de salida coherente y SNR espectral

En el modelo de una entrada y una salida, el autoespectro medido de la
salida se separa exactamente en la parte explicada linealmente por la
entrada y el resto no correlacionado (ecs. 9.55–9.57):

$$
G_{vv} = \gamma^2_{xy}\,G_{yy}, \qquad
G_{nn} = \left(1-\gamma^2_{xy}\right) G_{yy}, \qquad
\mathrm{SNR}(f) = \frac{\gamma^2_{xy}}{1-\gamma^2_{xy}} .
$$

`coherent_output_spectrum` devuelve los tres espectros, la relación
señal-ruido espectral (lineal y en dB) y el error aleatorio del estimador de
la salida coherente (ec. 9.73), más la propagación de primer orden del error
de la coherencia a través de la SNR:

$$
\varepsilon_r[\hat{G}_{vv}] =
\frac{\left(2-\gamma^2_{xy}\right)^{1/2}}{|\gamma_{xy}|\sqrt{n_d}}, \qquad
\varepsilon_r[\widehat{\mathrm{SNR}}] = \frac{\sqrt{2}}{|\gamma_{xy}|\sqrt{n_d}} .
$$

Para ruido aditivo no correlacionado en la salida con nivel conocido, la
coherencia tiene la forma cerrada `γ² = SNR/(1+SNR)`, lo que hace toda la
cadena verificable con una señal sintética:

```python
import numpy as np
from phonometry import coherent_output_spectrum, noise_signal

fs = 48000.0
x = noise_signal(fs, 8.0, color="white", seed=1)
noise = noise_signal(fs, 8.0, color="white", rms=0.5, seed=2)
y = 0.8 * x + noise                      # SNR = 0.64/0.25 en toda frecuencia

res = coherent_output_spectrum(x, y, fs)
print(np.median(res.coherence))          # -> SNR/(1+SNR) = 0.719
print(np.median(res.snr_db))             # -> 10·lg(2.56) = 4.1 dB
res.plot()                               # Gyy, Gvv, Gnn y el panel de SNR
```

El campo `coherence_bias` informa del pequeño sesgo positivo del estimador
de coherencia, `b[γ̂²] ≈ (1-γ²)²/nd` (ec. 9.75): despreciable en cuanto `nd`
llega a unos cientos, y otra razón para promediar con generosidad antes de
fiarse de una coherencia baja.

## 4. Suavizado en fracciones de octava

`fractional_octave_smoothing` promedia un espectro sobre una ventana
rectangular de anchura relativa constante: 1/n de octava,
`[f·2^(-1/2n), f·2^(+1/2n)]` alrededor de cada frecuencia. Es el ancho de
banda de resolución de porcentaje constante que Bendat y Piersol recomiendan
para espectros de sistemas resonantes (sección 8.5.3), y el estándar de
facto para presentar respuestas de altavoces y salas. El promedio se calcula
siempre sobre **potencia** (las amplitudes se elevan al cuadrado primero,
los niveles en dB se convierten ida y vuelta), así que se conserva la
potencia de banda y no la amplitud, y un espectro plano pasa exactamente
sin cambios.

```python
from phonometry import fractional_octave_smoothing

smooth_psd = fractional_octave_smoothing(res.frequencies, res.psd, 3.0)
smooth_mag = fractional_octave_smoothing(freqs, np.abs(response), 6.0,
                                         domain="amplitude")  # una FRF |H|
smooth_db = fractional_octave_smoothing(freqs, levels, 3.0, domain="db")  # curva en dB
```

Una sola línea espectral con ordenada de PSD `P` (unidades²/Hz) en un bin de
anchura `Δf` se suaviza al nivel en forma cerrada
`P·Δf / (f₀·(2^{1/2n} - 2^{-1/2n}))` sobre una anchura de núcleo: el oráculo
fijado en los tests.

## 5. Generadores de ruido de colores

`noise_signal` produce ruido gaussiano cuya PSD sigue `Gxx(f) ∝ f^α` de
forma exacta en esperanza: ruido blanco con semilla se moldea en el dominio
de la frecuencia con la respuesta en magnitud exacta `(f/f_ref)^{α/2}` bin a
bin (un filtro de fase cero aplicado de forma circular), así que una
pendiente medida solo se desvía de la ley de potencias por el error
aleatorio de la estimación espectral, no como las aproximaciones rosas por
tramos o de pocos polos cuya pendiente ondula fracciones de dB. El registro
tiene media cero y se reescala exactamente al RMS pedido, y la misma semilla
reproduce el mismo registro bit a bit.

| color | α | pendiente de la PSD |
|---|---|---|
| `white` | 0 | 0 dB/octava |
| `pink` | -1 | -3,01 dB/octava |
| `red` (browniano) | -2 | -6,02 dB/octava |
| `blue` | +1 | +3,01 dB/octava |
| `violet` | +2 | +6,02 dB/octava |

```python
from phonometry import noise_signal

pink = noise_signal(48000, 10.0, color="pink", seed=7)     # determinista
white = noise_signal(48000, 10.0, color="white", rms=0.5, seed=7)
```

Medida sobre tres décadas (20 Hz – 20 kHz) con el estimador de la sección 1,
la pendiente de regresión de cada color cae a unas milésimas de dB/octava
del valor exacto: la batería de conformidad fija la pendiente rosa en
-3,0116 frente al exacto -3,0103.

## Relación con los estimadores H1/H2

Los [estimadores de respuesta en frecuencia](/phonometry/es/guides/electroacoustics/)
`transfer_function` y `coherence`, la sonda de
[intensidad sonora](/phonometry/es/guides/intensity/) de dos micrófonos y
estos estimadores comparten un único núcleo de Welch (misma ventana, misma
política de solape y calibración sin eliminación de tendencia), así que una
PSD, una coherencia y una H1 calculadas con la misma longitud de segmento
son mutuamente consistentes bin a bin.

## Referencias

- Bendat, J. S., y Piersol, A. G. (2010). *Random Data: Analysis and
  Measurement Procedures* (4.ª ed.). Wiley. ISBN 978-0-470-24877-5.
  [doi:10.1002/9781118032428](https://doi.org/10.1002/9781118032428).
  Secciones 5.2 y 8.5 (autoespectros y sus errores aleatorios y de sesgo,
  intervalos chi-cuadrado), 9.1–9.2 (espectros cruzados, espectro de salida
  coherente y sus errores) y 11.5 (procesado de Welch, ventanas y solape).
- Welch, P. D. (1967). The use of fast Fourier transform for the estimation
  of power spectra: A method based on time averaging over short, modified
  periodograms. *IEEE Transactions on Audio and Electroacoustics*, 15(2),
  70–73. [doi:10.1109/TAU.1967.1161901](https://doi.org/10.1109/TAU.1967.1161901).
  La fórmula de varianza con segmentos solapados tras el número efectivo de
  promedios (Bendat y Piersol, sección 11.5.2.2, ref. 11).

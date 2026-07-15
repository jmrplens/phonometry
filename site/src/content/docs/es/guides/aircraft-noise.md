---
title: "Ruido de aeronaves: nivel efectivo de ruido percibido"
description: "El nivel efectivo de ruido percibido (EPNL) de la ICAO Anexo 16 Vol. I Apéndice 2: la molestia percibida y el PNL, la corrección tonal por el método de pendientes, la corrección por duración de 10 dB por debajo, y el verificador de sistema de medida IEC 61265."
---

El **nivel efectivo de ruido percibido (EPNL)** es la métrica de certificación
acústica de las aeronaves de transporte. Condensa una historia temporal
espectral de tercio de octava (cada medio segundo) de un sobrevuelo en un único
número, en EPNdB, mediante cinco pasos del **Anexo 16 de la ICAO, Vol. I,
Apéndice 2**. Esta página cubre las cuatro primitivas que construyen la métrica
y el verificador de sistema de medida IEC 61265. Cada magnitud se valida contra
los ejemplos trabajados del Manual Técnico Ambiental (ETM) Vol. I, ICAO
Doc 9501.

## Molestia percibida y PNL

Cada uno de los 24 niveles de banda de tercio de octava (50 Hz–10 kHz) se
convierte en una **molestia** percibida en noys mediante la ley analítica a
trozos de la Tabla A2-3, y se combinan en la molestia total
`N = 0.85·n_max + 0.15·Σn` y el nivel de ruido percibido
`PNL = 40 + (10/lg2)·lg N`.

```python
import phonometry as ph

noys = ph.perceived_noisiness(spl)      # noys por banda (spl = 24 niveles, dB)
pnl = ph.perceived_noise_level(spl)      # PNdB
```

## Corrección tonal

Las irregularidades espectrales (tonos de ventilador/turbina) se penalizan con
una **corrección tonal** `C`, hallada con el método de pendientes ("encircling"):
las pendientes se suavizan a un espectro de fondo `SPL''`, el exceso tonal
`F = SPL − SPL''` por encima de 1,5 dB se mapea a un factor de corrección
(división de frecuencia en 500 Hz / 5000 Hz, con tope de 6⅔ dB) y se toma el
máximo sobre las bandas. La implementación reproduce exactamente el ejemplo del
turbofán de la Tabla 3-7 del ETM Vol. I (`C = 2,0 dB` en 2500 Hz).

```python
c = ph.tone_correction(spl)              # dB; se suma al PNL para dar PNLT
```

## EPNL

Sobre el sobrevuelo, `PNLT = PNL + C`, su máximo es `PNLTM`, y la métrica integra
`PNLT` sobre la ventana de 10 dB por debajo (los registros más cercanos a
`PNLTM − 10` a cada lado) normalizada a 10 s, de modo que `EPNL = PNLTM + D` con
la corrección por duración `D`.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/epnl_es.svg" alt="Historia temporal del nivel de ruido percibido de un sobrevuelo de aeronave: PNL y el PNLT corregido por tonos en función del tiempo, con el máximo PNLTM marcado y la ventana de integración de 10 dB por debajo sombreada, anotada con el EPNL resultante y la corrección por duración" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/epnl_es_dark.svg" alt="Historia temporal del nivel de ruido percibido de un sobrevuelo de aeronave: PNL y el PNLT corregido por tonos en función del tiempo, con el máximo PNLTM marcado y la ventana de integración de 10 dB por debajo sombreada, anotada con el EPNL resultante y la corrección por duración" style="width:82%">

```python
import phonometry as ph

# spectra: un array (K, 24) de niveles de tercio de octava muestreado cada dt s
res = ph.effective_perceived_noise_level(spectra, dt=0.5)
print(res.epnl, res.pnltm, res.duration_correction, res.band_limits)
res.plot()   # historia temporal PNL/PNLT (requiere matplotlib)
```

`effective_perceived_noise_level` devuelve un `EPNLResult` con el `pnl` por
registro, la `tone_correction`, el `pnlt`, el máximo `pnltm`, la
`duration_correction`, el `epnl` y los `band_limits` de 10 dB por debajo. El
ejemplo del método integrado en condiciones de referencia de la Tabla 4-4 del
ETM Vol. I se reproduce como `EPNL = 92,6 EPNdB`.

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import numpy as np
import phonometry as ph

k, dt = 41, 0.5
idx = np.arange(k)
shape = 15.0 * np.exp(-((np.log10(ph.NOY_BANDS) - np.log10(400.0)) ** 2) / 0.5)
gain = 30.0 * np.exp(-((idx - 20.0) ** 2) / (2 * 5.0**2)) - 5.0
spectra = (55.0 + shape)[None, :] + gain[:, None]
spectra[:, 17] += 12.0 * np.exp(-((idx - 20.0) ** 2) / (2 * 6.0**2))  # tono de ventilador 2500 Hz
ph.effective_perceived_noise_level(spectra, dt).plot()
```

</details>

## Verificación del sistema de medida (IEC 61265)

`verify_aircraft_noise_system` comprueba el rendimiento medido contra las
tolerancias de la IEC 61265:1995: los límites de respuesta direccional del
micrófono (Tabla 1) y los límites escalares de respuesta en frecuencia,
linealidad y resolución. El filtrado de tercio de octava lo cubre la
verificación de clase 2 de filtros IEC 61260 de la librería.

```python
import phonometry as ph

report = ph.verify_aircraft_noise_system(
    directional={4000.0: {30: 0.4, 60: 0.9, 90: 1.9, 120: 2.4, 150: 2.4}},
    frequency_response={1000.0: 1.2},
)
print(report["passed"], report["checks"])
```

## Absorción atmosférica (SAE ARP 5534)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/aircraft_atmospheric_absorption_es.svg" alt="Absorción atmosférica aeronáutica frente a la frecuencia para dos distancias; la atenuación de banda del método SAE queda por debajo del valor de tono puro medio de banda a alta absorción" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/aircraft_atmospheric_absorption_es_dark.svg" alt="Absorción atmosférica aeronáutica frente a la frecuencia para dos distancias; la atenuación de banda del método SAE queda por debajo del valor de tono puro medio de banda a alta absorción" style="width:82%">

Corregir un sobrevuelo medido a condiciones atmosféricas de referencia requiere
la atenuación en bandas de 1/3 de octava sobre el trayecto. El coeficiente de
tono puro es el de ISO 9613-1 (idéntico, según ARP 5534 §3.1) que da
`air_attenuation`; `sae_band_attenuation` añade el **método SAE** (ARP 5534
§3.2.2) que mapea la atenuación de trayecto de tono puro medio de banda
`δ_t = α·s` a la atenuación de banda `δ_B`, consistente con el método exacto
mucho más allá del límite de 50 dB del método aproximado.

```python
import numpy as np
import phonometry as ph

freqs = 1000.0 * 10.0 ** (np.arange(-13, 11) / 10.0)   # tercios 50 Hz–10 kHz
att = ph.sae_band_attenuation(freqs, path_length=7620.0,
                              temperature=25.0, relative_humidity=70.0)
att.plot()   # banda frente a tono puro medio de banda (requiere matplotlib)
```

Válido ~6–32 °C, 20–95 % HR (ventana 14 CFR Part 36), hasta 7620 m, recíproco.

## Ruido de aeropuerto: el motor NPD (ECAC Doc 29)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airport_noise_es.svg" alt="Curvas nivel-potencia-distancia para dos ajustes de potencia; el nivel de evento cae log-linealmente con la distancia oblicua entre los nodos tabulados" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airport_noise_es_dark.svg" alt="Curvas nivel-potencia-distancia para dos ajustes de potencia; el nivel de evento cae log-linealmente con la distancia oblicua entre los nodos tabulados" style="width:82%">

El método de ruido de aeropuerto de ECAC Doc 29 describe la aeronave con tablas
**nivel-potencia-distancia (NPD)**. `npd_level` lee el nivel de evento
(`LAmax`/`SEL`) para una potencia y distancia arbitrarias, interpolando
linealmente en potencia (Ec. 4-3) y log-linealmente en distancia oblicua
(Ec. 4-4).

```python
import phonometry as ph

powers = [12000.0, 20000.0]
distances = [200.0, 400.0, 1000.0, 2000.0, 6300.0, 10000.0]
levels = [[98.5, 92.0, 83.6, 76.8, 63.9, 56.8],
          [107.2, 100.9, 92.7, 86.0, 72.9, 65.6]]
ph.npd_curve(powers, distances, levels, power=20000.0).plot()
```

Es el motor NPD que sustenta el método.

## Contornos de ruido de aeropuerto (evento único)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airport_contour.png" alt="Contorno SEL de un despegue: huella alargada a lo largo de la trayectoria, más intensa cerca del rodaje" style="width:90%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airport_contour_dark.png" alt="Contorno SEL de un despegue: huella alargada a lo largo de la trayectoria, más intensa cerca del rodaje" style="width:90%">

El cálculo de evento único trocea la trayectoria en segmentos y corrige el nivel
base NPD por segmento (§4.3-4.5): `impedance_adjustment` (T, p),
`lateral_attenuation` (β,ℓ), `engine_installation_correction` (φ, montaje),
`duration_correction`, la fracción de segmento finito `noise_fraction` y, detrás
de los segmentos de rodaje de despegue, `start_of_roll_directivity` (ΔSOR).
`event_level` los ensambla y suma en `SEL`/`LAmax`, y `noise_contour` lo evalúa
sobre una malla en tierra (marca los segmentos de rodaje con una máscara
`ground_roll`).

El mecanismo tras estas correcciones de suelo es la interferencia de dos
caminos: la onda directa y su reflexión en el suelo. Abajo, una fuente de
400 Hz a 1,5 m sobre un plano rígido forma el patrón de lóbulos, con la fuente
imagen dibujada como fantasma bajo el suelo y un receptor situado en un mínimo
de interferencia.

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ground_effect_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ground_effect_es_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: simulación FDTD 2D de una fuente puntual de 400 Hz a 1,5 metros sobre suelo rígido; los frentes de onda directo y reflejado en el suelo interfieren y se forma un patrón de lóbulos, la fuente imagen fantasma bajo el suelo explica la geometría y el nivel sobre un arco de 8 metros converge al modelo de fuente imagen de dos caminos con sus mínimos previstos" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ground_effect_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_fdtd_ground_effect_es_dark_poster.jpg" width="800" height="450" loop muted controls playsinline title="Animación: simulación FDTD 2D de una fuente puntual de 400 Hz a 1,5 metros sobre suelo rígido; los frentes de onda directo y reflejado en el suelo interfieren y se forma un patrón de lóbulos, la fuente imagen fantasma bajo el suelo explica la geometría y el nivel sobre un arco de 8 metros converge al modelo de fuente imagen de dos caminos con sus mínimos previstos" style="width:88%"></video>

La directividad de inicio de rodaje es la radiación trasera lobulada del ruido
de chorro: máxima hacia un acimut ψ ≈ 120° respecto al morro, y decreciente al
través (ψ = 90°) y directamente detrás (ψ = 180°).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airport_sor_es.svg" alt="Diagrama polar de la directividad de inicio de rodaje ΔSOR sobre el semicírculo trasero para reactor turbofán y turbohélice, con un lóbulo cerca de 120° respecto al morro" style="width:75%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airport_sor_es_dark.svg" alt="Diagrama polar de la directividad de inicio de rodaje ΔSOR sobre el semicírculo trasero para reactor turbofán y turbohélice, con un lóbulo cerca de 120° respecto al morro" style="width:75%">

```python
import numpy as np
import phonometry as ph

powers = [8000.0, 12000.0]; distances = [60.0, 240.0, 960.0, 3840.0]
sel = [[98.0, 86.0, 74.0, 62.0], [104.0, 92.0, 80.0, 68.0]]
lmax = [[94.0, 82.0, 70.0, 58.0], [100.0, 88.0, 76.0, 64.0]]
xs = np.linspace(0.0, 18000.0, 40)
path = np.column_stack([xs, np.zeros_like(xs), np.clip((xs-1500)*0.11, 0, 2500),
                        np.where(xs < 3000, 12000.0, 10000.0), np.full_like(xs, 82.3)])
ph.noise_contour(path, powers, distances, sel, lmax,
                 x=np.linspace(-2500, 20000, 60), y=np.linspace(-6000, 6000, 48)).plot()
```

Validado contra el workbook de referencia de ECAC Doc 29 5ª ed. Vol 3 Parte 1:
la geometría de segmento, la atenuación lateral, la instalación del motor, la
fracción de ruido y la directividad de inicio de rodaje (turbofán y turbohélice)
reproducen los valores de referencia con < 0,01 dB, y la suma energética de
segmentos coincide con el `SEL` de referencia.

El modelo cubre también el rodaje de aterrizaje (máscara `landing_roll`:
fracción de ruido reducida Ec. 4-21b, geometría al extremo más cercano, sin
término de directividad), el ángulo de alabeo por segmento (`bank`, convención
de signo de §4.5.2), la geometría lateral §4.5.5 al extremo más cercano detrás
del rodaje de despegue, la velocidad media Ec. 4-13b en segmentos de pista y el
suelo recomendado de 30 m en las consultas NPD. Siete eventos de receptor del
workbook de referencia se reproducen end-to-end en la suite de tests.

---

**Normas.** ICAO Anexo 16 Vol. I Apéndice 2 (procedimiento EPNL), ICAO Doc 9501
ETM Vol. I (oráculos de ejemplo trabajado), IEC 61265:1995 (tolerancias del
sistema de medida), SAE ARP 5534:2021 (absorción de banda por el método SAE;
coeficiente de tono puro de ISO 9613-1), ECAC Doc 29 4ª ed. Vol 2 §4.2
(interpolación NPD del nivel de evento) y el cálculo de evento único por
segmentos (ajuste de impedancia, duración, instalación del motor, atenuación
lateral, fracción de ruido, directividad de inicio de rodaje, suma) hasta los
contornos en malla de tierra, validado contra el workbook de referencia de la
Doc 29 5ª ed. Vol 3 Parte 1.

## Véase también

- Referencia de la API: [`aircraft.aircraft_noise`](/phonometry/es/reference/api/aeroacoustics/aircraft-noise/), [`aircraft.airport_noise`](/phonometry/es/reference/api/aeroacoustics/airport-noise/) y [`aircraft.atmospheric_absorption`](/phonometry/es/reference/api/aeroacoustics/atmospheric-absorption/).

---
title: "Índice de transmisión del habla (STI)"
description: "El índice de transmisión del habla de IEC 60268-16: la función de transferencia de modulación, el método indirecto desde una respuesta al impulso medida y la medición STIPA directa con su señal de ensayo normalizada."
---

Un sistema de megafonía, un interfono, un aula reverberante — cada uno es un
*canal de transmisión* entre la boca de quien habla y el oído de quien escucha,
y cada uno degrada el habla a su manera. El **índice de transmisión del habla**
(STI) de IEC 60268-16 califica ese canal con un único número en [0, 1] midiendo
cuánta de la *envolvente* del habla sobrevive al trayecto. Esta página cubre la
física de transferencia de modulación en la que se basa el índice, el método indirecto desde
una respuesta al impulso medida en la sala y la medición STIPA directa con su
señal de ensayo normalizada.

:::note
**STI frente a SII.** El STI caracteriza un *canal de transmisión* — cuánta de
la modulación del habla conserva una sala o un sistema de sonido —, mientras
que el SII predice la inteligibilidad desde la *audibilidad*: cuánto del
espectro del habla supera el ruido y el umbral de audición en el oído de quien
escucha. Para esto último, consulta la
[guía del índice de inteligibilidad del habla](/phonometry/es/guides/speech-intelligibility/).
:::

## 1. La función de transferencia de modulación

La reverberación y el ruido no amortiguan el habla de manera uniforme —
emborronan su *envolvente*: las modulaciones lentas de intensidad
(0,63–12,5 Hz) que transportan las sílabas. El STI cuantifica cuánta de esa
modulación sobrevive de la boca al oído, por banda de octava, como la
**función de transferencia de modulación (MTF)** m(F). Un canal tipo delta
mantiene m = 1 (STI = 1); la reverberación filtra paso-bajo la envolvente
siguiendo la forma cerrada de Schroeder, y el ruido estacionario la escala:

$$
m(F) = \frac{1}{\sqrt{1 + \left(2\pi F\ \frac{T_{60}}{13{,}8}\right)^2}}
\cdot \frac{1}{1 + 10^{-\mathrm{SNR}/10}}
$$

La *profundidad* de modulación es lo que merece la pena medir porque la
inteligibilidad viaja en la profundidad de los valles de la envolvente, no en
la sonoridad de los picos. Quien habla alterna ráfagas de energía (vocales)
con casi silencios (oclusiones, arranques de fricativas) al ritmo de las
sílabas, y quien escucha segmenta el habla oyendo esos valles. Una cola
reverberante rellena los valles por detrás, porque la energía tardía se
esparce en los huecos; el ruido estacionario eleva su suelo. En ambos casos la
profundidad de modulación recibida se encoge, y con ella el contraste entre
sonidos del habla, aunque el nivel medio apenas cambie. El método completo
sondea m(F) en 14 frecuencias de modulación (de 0,63 Hz a 12,5 Hz en pasos de
tercio de octava) en cada una de las 7 bandas de octava de 125 Hz a 8 kHz,
convierte cada m en una relación señal-ruido efectiva acotada a ±15 dB y
combina los resultados, ponderados por banda, en el índice: el STI es una SNR
efectiva de la *envolvente*, llevada a [0, 1].

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60_es.svg" alt="STI frente al tiempo de reverberación con las bandas de calificación del Anexo F de IEC 60268-16 sombreadas" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60_es_dark.svg" alt="STI frente al tiempo de reverberación con las bandas de calificación del Anexo F de IEC 60268-16 sombreadas" style="width:80%">

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain_es.svg" alt="Cadena de medición del STI: señal de la fuente STIPA a través de la sala hasta el micrófono y el análisis de la MTF" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain_es_dark.svg" alt="Cadena de medición del STI: señal de la fuente STIPA a través de la sala hasta el micrófono y el análisis de la MTF" style="width:92%">

## 2. Medición indirecta y directa (STIPA)

```python
import numpy as np
from phonometry import sti_from_impulse_response, stipa, stipa_signal

fs = 48000
# Una respuesta al impulso medida en la sala (decaimiento sintetizado para que el ejemplo funcione)
ir = np.random.default_rng(0).standard_normal(fs) * np.exp(-6.9 * np.arange(fs) / fs / 0.5)

# Método indirecto: desde una respuesta al impulso medida en la sala
res = sti_from_impulse_response(ir, fs, snr=25.0)
print(f"STI = {res.sti:.2f}  ({res.rating})")   # p. ej. 0.62 (D)

# Medición STIPA directa: reproduce stipa_signal() en la sala y grábala
test = stipa_signal(fs, seconds=18.0, level_db=80.0)
recording = test                       # en la práctica, la señal del micrófono tras la reproducción
res = stipa(recording, fs)
res.plot()   # barras del índice de transferencia de modulación (MTI) por banda; STI y valoración en el título
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from phonometry import sti_from_impulse_response

fs = 48000

# STI frente al tiempo de reverberación: barre sti_from_impulse_response sobre
# decaimientos exponenciales sintéticos (ruido blanco x exp(-6.9077 t / T60))
# en una rejilla de T60 — exactamente la física de la curva de arriba:
rng = np.random.default_rng(0)
t60_grid = np.array([0.3, 0.5, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0, 4.0, 5.0])
sti_values = []
for t60 in t60_grid:
    t = np.arange(int(2 * t60 * fs)) / fs
    ir = rng.standard_normal(t.size) * np.exp(-6.9077 * t / t60)
    sti_values.append(sti_from_impulse_response(ir, fs).sti)

fig, ax = plt.subplots()
ax.semilogx(t60_grid, sti_values, "o-")
ax.set_xlabel("Tiempo de reverberación T60 [s]")
ax.set_ylabel("STI")
ax.set_ylim(0.0, 1.0)
ax.grid(True, which="both", alpha=0.3)
plt.show()
```

</details>

`stipa` emite un `UserWarning` cuando la grabación es más corta que los 15 s
recomendados (práctica STIPA de IEC 60268-16, de 15 s a 25 s): por debajo de eso
las componentes de modulación lentas se promedian sobre muy pocos periodos y el
STI queda sesgado a la baja (un lazo ideal da STI ≈ 0,956 a 5 s frente a
≈ 0,998 a 18 s).

La implementación sigue la **Edición 5 (2020)**: el PDF normativo de la
Edición 4 es la base y cada cambio de la Ed. 5 está atribuido a su fuente en el
código — el único delta numérico es el espectro de habla masculina revisado del
apartado A.6.1. CI comprueba los vectores de verificación de la propia norma:
los seis pares de bandas de los factores de ponderación a ±0,001 STI, la tabla
de correspondencia m ↔ STI, los puntos de control del enmascaramiento
dependiente del nivel y decaimientos con la forma de Schroeder a cuatro valores
de T₆₀.

El analizador también se verifica de extremo a extremo con las señales del
**banco de verificación de IEC 60268-16 rev 5** de
[stipa.info](https://www.stipa.info) (Embedded Acoustics BV): la escalera de
profundidad de modulación del método directo (Anexo C.3.2), los decaimientos
exponenciales del método indirecto frente a la MTF de Schroeder en forma
cerrada (C.3.3), la prueba de pendiente del banco de filtros con un tono
adyacente sin modular a +41 dB (C.4.2, m ≥ 0,5), los pares de bandas de los
factores de ponderación (A.2.2) y la prueba de distorsión de fase del banco de
filtros con portadoras en los bordes de media octava (A.3.1.2,
|sesgo de STI| < 0,01 en TI = 0,1–0,9). Las cinco series pasan con las
funciones dependientes del nivel desactivadas, como prescribe el banco. Los 49
WAV certificados permanecen en local (datos de terceros, no versionados); CI
reconstruye las mismas señales de forma sintética en la serie de conformidad.

### ¿Directo o indirecto? Cómo elegir

Cada vía tiene modos de fallo que la norma hace explícitos:

- **Canales no lineales o variantes en el tiempo.** El método indirecto asume
  un canal lineal e invariante en el tiempo: una respuesta al impulso no puede
  representar el recorte, los compresores, el control automático de ganancia
  ni un vocoder. Para un sistema de sonido con procesado no lineal en la
  cadena, mide en directo: la señal STIPA al menos atraviesa la cadena real, y
  la señal del STI completo es la opción fiable cuando la distorsión es severa
  (IEC 60268-16, apartado 6.3 y Tabla 3).
- **Efectos dependientes del nivel.** El STI no es invariante con el nivel: el
  enmascaramiento auditivo y el umbral de recepción actúan sobre los niveles
  de banda *absolutos* en el oyente. Reproduce la señal de ensayo al nivel de
  operación del sistema (la práctica del Anexo J de la norma la fija 3 dB por
  encima del L_Aeq del habla continua en la posición) y pasa `level=` y
  `ambient=` para que el análisis los incluya; una respuesta al impulso medida
  a nivel alto y reescalada después pierde estos efectos por completo.
- **Ruido de fondo impulsivo y fluctuante.** Una herramienta que cae o un
  murmullo durante una medición directa corrompe las profundidades de
  modulación medidas (apartado 7.13). El remedio de la norma es la vía
  indirecta: promedia la respuesta al impulso con MLS o barridos para obtener
  una MTF sin ruido y añade después la degradación por ruido mediante `snr=` o
  `level=`/`ambient=`. Una comprobación rápida es ejecutar el analizador con
  la fuente apagada; el STI residual debería quedar por debajo de 0,20.
- **Dispersión estadística.** La señal STIPA es ruido pseudoaleatorio, así que
  mediciones directas repetidas se dispersan hasta alrededor de 0,03 STI
  incluso en condiciones estacionarias (y más en ruido fluctuante); repite y
  compara en lugar de fiarte de una sola pasada, y respeta la duración mínima
  que señala el `UserWarning` de arriba.

### Parámetros de `sti_from_impulse_response()` / `stipa()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `ir` / `x` | array 1D | cualquiera / Pa | no vacío | Respuesta al impulso (indirecto) o grabación STIPA (directo) |
| `fs` | int | Hz | > 0 | |
| `snr` | float o vector de 7, opcional | dB | por defecto `None` | Añade la degradación por ruido estacionario |
| `level` | vector de 7, opcional | dB SPL | por defecto `None` | Activa el enmascaramiento auditivo + umbral de recepción (Tablas A.2/A.3) |
| `ambient` | vector de 7, opcional | dB SPL | requiere `level` | Niveles de banda del ruido ambiente |
| `reference` | array 1D, opcional (`stipa`) | — | por defecto `None` | Señal de la fuente medida en lugar del m = 0,55 nominal |

Ambas devuelven `STIResult`: `sti`, `mti` (7 bandas), `mtf` (7×14 o 7×2),
`band_levels`, `rating` (letra del Anexo F, `A+`…`U`).

## Véase también

- [Acústica de salas](/phonometry/es/guides/room-acoustics/) — la respuesta al
  impulso medida que consume el método indirecto, y las métricas de oficinas
  diáfanas (ISO 3382-3) construidas sobre el STI por posición.
- [Índice de inteligibilidad del habla](/phonometry/es/guides/speech-intelligibility/) —
  el índice basado en audibilidad de ANSI S3.5 que complementa al STI.
- [Sonoridad](/phonometry/es/guides/loudness/) y
  [Métricas de calidad sonora](/phonometry/es/guides/sound-quality/) — sonoridad, sharpness,
  tonalidad y aspereza del sonido recibido.
- [Teoría](/phonometry/es/reference/theory/perception/) — la derivación de la transferencia
  de modulación y la correspondencia m ↔ STI.
- Referencia de la API: [`hearing.sti`](/phonometry/es/reference/api/speech/sti/).

## Referencias

- Houtgast, T., & Steeneken, H. J. M. (1985). A review of the MTF concept in
  room acoustics and its use for estimating speech intelligibility in
  auditoria. *The Journal of the Acoustical Society of America*, 77(3),
  1069-1077. [doi:10.1121/1.392224](https://doi.org/10.1121/1.392224).
  El marco de transferencia de modulación de la sección 1 y la correspondencia
  m ↔ STI sobre la que se construye el índice.

## Normas

IEC 60268-16:2020 (Edición 5), *Sound system equipment — Part 16:
Objective rating of speech intelligibility by speech transmission index* — la
función de transferencia de modulación y la correspondencia m ↔ STI, la señal
de ensayo STIPA y el método directo, el método indirecto desde la respuesta al
impulso, el enmascaramiento auditivo y el umbral de recepción (Tablas A.2/A.3),
el espectro de habla masculina revisado (apartado A.6.1) y las letras de
valoración del Anexo F.

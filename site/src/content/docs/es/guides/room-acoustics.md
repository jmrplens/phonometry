---
title: "Acústica de salas y edificación"
description: "Adquisición de la respuesta al impulso (ISO 18233), parámetros de sala EDT/T20/T30/C50/C80/Ts (ISO 3382-1/2), métricas de habla en oficinas diáfanas (ISO 3382-3), aislamiento acústico en laboratorio (ISO 10140) y en campo (ISO 16283-1/2/3) a ruido aéreo y a impactos con índices ponderados (ISO 717-1/2), predicción de la transmisión (EN 12354) e incertidumbre de medición (ISO 12999-1), y absorción sonora en sala reverberante (ISO 354)."
---

La acústica de salas y de la edificación parte de una única medición: la
**respuesta al impulso** (RI) entre una fuente y un receptor. Fíltrala en
bandas e intégrala, y da el tiempo de reverberación, la claridad y la
inteligibilidad del habla; mídela a ambos lados de una pared, y da el
aislamiento acústico del cerramiento. Esta página sigue esa cadena en orden
de medición: adquirir la RI (ISO 18233), convertirla en parámetros de sala
(ISO 3382-1/2), métricas espaciales del habla para oficinas diáfanas
(ISO 3382-3), aislamiento en campo a ruido aéreo, a impactos y de fachadas con
índices de un solo número (ISO 16283-1/2/3, ISO 717-1/2), la caracterización en
laboratorio de un elemento constructivo (ISO 10140), la predicción del
comportamiento in situ a partir de la transmisión por flancos (EN 12354-1/2), la
incertidumbre de medición que cualifica cada índice (ISO 12999-1) y, cerrando el
ciclo, la absorción sonora de un material en una sala reverberante (ISO 354).

## 1. Adquisición de la respuesta al impulso (ISO 18233)

Una sala se comporta, con buena aproximación, como un sistema **lineal e
invariante en el tiempo**, así que todo sobre ella está contenido en su RI.
Podrías disparar una pistola y grabar la cola, pero una excitación
determinista reproducida por un altavoz y *deconvolucionada* recupera la
misma RI con 20–30 dB más de relación señal-ruido efectiva (ISO 18233). Se
proporcionan dos excitaciones.

**Barrido sinusoidal exponencial (ESS, Anexo B).** La frecuencia
instantánea crece exponencialmente,

$$
f(t) = f_1 \left( \frac{f_2}{f_1} \right)^{t/T},
$$

de modo que el tiempo invertido por octava es constante y la excitación
imita al ruido rosa (energía constante por banda de octava fraccionaria).
La RI se recupera mediante división espectral lineal (con relleno de ceros,
no circular),

$$
H = \frac{Y\ \overline{X}}{|X|^2 + \varepsilon},
$$

con un pequeño término de Tikhonov $\varepsilon$ que protege los extremos de
banda donde el barrido tiene poca energía. Como un barrido de grave a agudo
sitúa la distorsión armónica en tiempos de llegada *negativos*, la distorsión
se separa limpiamente de la RI lineal y se descarta conservando solo la parte
causal. El método `"farina"` llega al mismo resultado convolucionando la
grabación con el filtro inverso analítico; supone que el barrido de
referencia se generó con la amplitud y el desvanecimiento por defecto, así
que usa el método espectral con un barrido de amplitud distinta de la unidad
o con desvanecimiento personalizado.

**Secuencia de longitud máxima (MLS, Anexo A).** Una secuencia binaria de
orden `N` y longitud $2^N-1$ cuya autocorrelación circular es una delta casi
perfecta; la RI se obtiene de la correlación cruzada circular del periodo
grabado con la secuencia. La MLS excita con amplitud constante y es rápida de
promediar, pero es más sensible a la varianza temporal (corrientes de aire,
deriva de temperatura) y no admite tanta potencia como un barrido.
**Prefiere el barrido** para salas y cerramientos; recurre a la MLS cuando la
excitación deba ser periódica o el hardware favorezca una señal de dos
niveles.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement_es.svg" alt="Cadena de medición indirecta ISO 18233: una excitación (barrido ESS o MLS) alimenta un altavoz en la sala, un micrófono capta la respuesta y la deconvolución (correlación o filtro inverso) recupera la respuesta al impulso" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_ir_measurement_es_dark.svg" alt="Cadena de medición indirecta ISO 18233: una excitación (barrido ESS o MLS) alimenta un altavoz en la sala, un micrófono capta la respuesta y la deconvolución (correlación o filtro inverso) recupera la respuesta al impulso" style="width:92%">

```python
import numpy as np
from scipy.signal import fftconvolve
from phonometry import sweep_signal, impulse_response, mls_signal, mls_impulse_response

fs = 48000
# Un barrido de 3 s, 20 Hz - 20 kHz es una buena excitación de sala de banda ancha
# sweep: excitación que reproduces por el altavoz
sweep = sweep_signal(fs, 20.0, 20000.0, 3.0)

# Deconvoluciona la respuesta grabada para recuperar la respuesta al impulso
system = np.zeros(fs); system[100] = 1.0; system[2000] = 0.4   # directo + reflexión
# recorded: captura de micrófono del barrido reproducido (aquí simulada por convolución con una sala sintética)
recorded = fftconvolve(sweep, system)
ir = impulse_response(recorded, sweep, fs, method="spectral")
print(int(np.argmax(np.abs(ir))))                    # 100: sonido directo recuperado

# Variante de filtro inverso de Farina (necesita la banda del barrido)
ir_f = impulse_response(recorded, sweep, fs, method="farina", f_range=(20.0, 20000.0))

# MLS periódica: excita con >= 2 periodos, promedia, correlaciona
mls = mls_signal(16)                                 # longitud 2**16 - 1 = 65535
rec = fftconvolve(np.tile(mls, 2), system)[: 2 * mls.size]
ir_m = mls_impulse_response(rec, mls)
print(int(np.argmax(np.abs(ir_m))))                  # 100
```

### Parámetros de `sweep_signal()` / `inverse_filter()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `fs` | int | Hz | > 0 | Frecuencia de muestreo |
| `f1` | float | Hz | > 0, en/por debajo de la banda más baja | Frecuencia inicial del barrido |
| `f2` | float | Hz | `f1 < f2 <= fs/2` | Frecuencia final del barrido |
| `seconds` | float | s | cualquiera; mayor ⇒ más SNR | Duración del barrido |
| `amplitude` | float | — | por defecto `1.0` | Amplitud de pico |
| `fade` | float | — | `[0, 0.5)`, por defecto `0.01` | Fracción de fundido medio Hann (elimina transitorios de inicio/fin) |

### Parámetros de `impulse_response()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `recorded` | array 1D | cualquiera | no vacío | Respuesta del sistema grabada |
| `reference` | array 1D | cualquiera | no vacío | El barrido emitido |
| `fs` | int | Hz | > 0 | Frecuencia de muestreo |
| `method` | str | — | `'spectral'` (por defecto) / `'farina'` | `'farina'` requiere `f_range` |
| `f_range` | (float, float) | Hz | por defecto `None` | `(f1, f2)` del barrido (solo Farina) |
| `regularization` | float | — | por defecto `1e-6` | Término de Tikhonov como fracción de la energía espectral de pico |
| `length` | int, opcional | muestras | por defecto `len(recorded)` | Muestras de RI causal a devolver |
| `return_full` | bool | — | por defecto `False` | Devuelve la secuencia completa (distorsión en la cola) |

`mls_signal(order)` toma un entero `order` en 2–20 (longitud de secuencia
$2^{\text{order}}-1$); `mls_impulse_response(recorded, mls, length=None)`
necesita que `recorded` abarque un número entero de periodos de MLS.

## 2. Análisis del decaimiento y parámetros de sala (ISO 3382-1/2)

La RI se filtra en bandas de octava (o de tercio de octava) y cada banda se
convierte en una **curva de decaimiento** mediante la integración inversa de
Schroeder de la RI al cuadrado:

$$
E(t) = \int_t^{\infty} p^2(\tau)\ d\tau, \qquad
L(t) = 10 \log_{10} \frac{E(t)}{E(0)}\ \text{dB}.
$$

Integrar *hacia atrás* elimina la fluctuación que afecta a la RI al cuadrado
en bruto y produce una curva suave cuya pendiente es la tasa de decaimiento.
El ruido de fondo haría que $E(t)$ se estabilizara, así que la integración se
trunca donde la recta de decaimiento ajustada cruza el suelo de ruido y la
cola que falta se compensa suponiendo un decaimiento exponencial.

Los tiempos de reverberación provienen de un ajuste lineal por mínimos
cuadrados sobre un rango de evaluación, extrapolado a una caída completa de
60 dB, $T = -60/\text{slope}$: **EDT** de 0 a −10 dB (reverberación
percibida), **T20** de −5 a −25 dB y **T30** de −5 a −35 dB. Los repartos de
energía en una frontera temprano/tardío dan la **claridad** y la
**definición**,

$$
C_{te} = 10 \log_{10} \frac{\int_0^{te} p^2\ dt}{\int_{te}^{\infty} p^2\ dt}\ \text{dB}, \qquad
D_{50} = \frac{\int_0^{0.05} p^2\ dt}{\int_0^{\infty} p^2\ dt},
$$

con $te = 50$ ms → C50 (habla) y $te = 80$ ms → C80 (música), más el
**tiempo central** $T_s = \int t\ p^2\ dt / \int p^2\ dt$. Cada parámetro
tiene una **diferencia apenas perceptible** (ISO 3382-1 Tabla A.1: EDT 5 %,
C80 1 dB, D50 0,05, Ts 10 ms) que fija con qué precisión merece la pena
informarlo.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay_es.png" alt="Respuesta al impulso al cuadrado con su curva de decaimiento integrada hacia atrás de Schroeder, y las ventanas de regresión EDT, T20 y T30 marcadas" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/schroeder_decay_es_dark.png" alt="Respuesta al impulso al cuadrado con su curva de decaimiento integrada hacia atrás de Schroeder, y las ventanas de regresión EDT, T20 y T30 marcadas" style="width:80%">

*La RI al cuadrado dentada (gris) se integra hasta la curva suave de
Schroeder (azul); las ventanas EDT, T20 y T30 se ajustan sobre esa curva y
cada una se extrapola a un decaimiento de 60 dB.*

```python
import numpy as np
from phonometry import decay_curve, room_parameters

fs = 48000
# Decaimiento de pendiente única con T = 1 s: p^2 = exp(-13.8155 t)  (60/ln(10)/13.8155 = 1)
t = np.arange(fs) / fs
# ir: respuesta al impulso de sala medida; aquí la sustituye un decaimiento sintético de pendiente única.
ir = np.concatenate([np.zeros(10), np.exp(-13.8155 * t / 2.0)])

time, level = decay_curve(ir, fs)                    # curva de Schroeder (0 dB en t = 0)

res = room_parameters(ir, fs, limits=None)           # banda única de banda ancha
print(round(float(res.t30[0]), 2))                   # 1.0  s
print(round(float(res.c80[0]), 2))                   # 3.05 dB
print(round(float(res.d50[0]), 3))                   # 0.499
print(round(float(res.ts[0]) * 1000, 0))             # 72 ms

# Bandas de octava 125 Hz - 4 kHz (por defecto en ISO 3382-1); usa fraction=3 para tercios
octaves = room_parameters(ir, fs)
print(octaves.frequency)                             # ~[126, 251, 501, 1000, 1995, 3981]
print(octaves.t30_valid)                             # indicadores de rango dinámico por banda

octaves.plot()               # barras EDT/T20/T30 + C50/C80 por banda (requiere matplotlib)
decay_curve(ir, fs).plot()   # curva de Schroeder con los ajustes EDT/T20/T30
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — la curva de Schroeder con los ajustes rectos EDT/T20/T30:
decay = decay_curve(ir, fs)          # un DecayCurve (se sigue desempaquetando como time, level)
decay.plot()
plt.show()

# A mano, el decaimiento es solo la curva de Schroeder; marca los niveles de evaluación:
fig, ax = plt.subplots()
ax.plot(time, level, color="#1f77b4", label="Curva de Schroeder")
for db in (-5.0, -25.0, -35.0):      # bordes de la ventana de evaluación T20 / T30
    ax.axhline(db, ls=":", alpha=0.4)
ax.set_xlabel("Tiempo [s]")
ax.set_ylabel("Nivel re régimen permanente [dB]")
ax.set_ylim(top=3.0)
ax.legend()
plt.show()
```

</details>

Para este decaimiento de pendiente única, EDT, T20 y T30 devuelven todos
≈ 1,0 s, y los parámetros de energía coinciden con sus formas cerradas
(C80 = 3,05 dB, D50 = 0,499, Ts = 72 ms). Una sala real tiene una pendiente
inicial más pronunciada, así que EDT < T30.

### Parámetros de `room_parameters()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `ir` | array 1D | cualquiera | no silencioso | Respuesta al impulso medida |
| `fs` | int | Hz | > 0 | Frecuencia de muestreo |
| `limits` | (float, float) o `None` | Hz | por defecto `(125.0, 4000.0)` | Límites de centros de banda; `None` = banda única de banda ancha |
| `fraction` | int | — | `1` (octava, por defecto) / `3` (tercio) | Fracción de ancho de banda |
| `zero_phase` | bool | — | defecto `False` | Filtrado de octava hacia delante y atrás (NOTA de ISO 3382-2, 7.3, que relaja $BT > 16$ a $BT > 4$); elimina el retardo de grupo del filtro antes de la integración inversa y reduce aproximadamente a la mitad el sesgo de T30 corto a 125 Hz (~+4,9 % → +2,4 % con $T$ = 0,2 s). `decay_curve` también lo acepta |

Devuelve un `RoomAcousticsResult`: `frequency` (centros de banda, o `None` en
banda ancha), `edt`/`t20`/`t30` (s), `c50`/`c80` (dB), `d50`, `ts` (s),
`dynamic_range` (dB), los indicadores `edt_valid`/`t20_valid`/`t30_valid`
(ISO 3382-1, 5.3.3: ruido ≥ 25 dB por debajo del pico para EDT, endurecido a
46 dB para T20 y 54 dB para T30 para que el sesgo de compensación de cola de un
valor marcado como válido quede dentro de la DAP del 5 %) y `curvature`
$C = 100\ (T_{30}/T_{20} - 1)$ % (valores por encima del 10 % señalan un
decaimiento no recto). `decay_curve(ir, fs, band=None, fraction=1, zero_phase=False)`
devuelve solo la curva `(time, level)` para una banda o la respuesta de banda ancha.

## 3. Oficinas diáfanas (ISO 3382-3)

La acústica de oficinas diáfanas trata de la **privacidad del habla**: con
qué rapidez el habla de un hablante se desvanece hasta la ininteligibilidad a
medida que uno se aleja. Los niveles y el STI se miden a lo largo de una fila
de puestos de trabajo (al menos 4 posiciones, preferiblemente 6–10), y cuatro
magnitudes de un solo número resumen la sala. La **tasa de decaimiento
espacial** del habla ponderada A es la pendiente del nivel frente a
$\lg(r/r_0)$, escalada a una cifra por duplicación usando solo las posiciones
de 2–16 m,

$$
D_{2,S} = -\lg(2)\ b, \qquad L = a + b\ \lg(r/r_0),\ r_0 = 1\ \text{m},
$$

con **Lp,A,S,4m** leído en la misma recta a 4 m. La **distancia de
distracción** rD (STI = 0,50) y la **distancia de privacidad** rP
(STI = 0,20) provienen de una regresión lineal del STI frente a la distancia.
Las buenas oficinas empujan rD por debajo de ~5 m; las malas dejan el habla
molesta más allá de 10 m.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay_es.png" alt="Decaimiento espacial en oficina abierta: nivel de habla ponderado A y STI frente a la distancia a la fuente en eje logarítmico, con la regresión D2,S, el marcador Lp,A,S,4m a 4 m y los cruces de distancia rD y rP" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/open_plan_decay_es_dark.png" alt="Decaimiento espacial en oficina abierta: nivel de habla ponderado A y STI frente a la distancia a la fuente en eje logarítmico, con la regresión D2,S, el marcador Lp,A,S,4m a 4 m y los cruces de distancia rD y rP" style="width:80%">

```python
import numpy as np
from phonometry import open_plan_metrics

r = np.array([2.0, 4.0, 6.0, 8.0, 12.0, 16.0])       # distancias al hablante (m)
lp = 65.0 - 7.0 * np.log2(r)                          # nivel de habla ponderado A (dB)
sti = 0.70 - 0.03 * r                                 # STI por posición

m = open_plan_metrics(r, lp, sti)
print(round(m.d2s, 1), round(m.lp_as_4m, 1))         # 7.0 dB, 51.0 dB
print(round(m.rd, 1), round(m.rp, 1))                # 6.7 m, 16.7 m
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# Decaimiento espacial: Lp,A,S medido frente a la distancia en eje logarítmico,
# la regresión D2,S reconstruida con los campos del resultado, y el STI con los
# cruces rD / rP en un eje gemelo:
b = -m.d2s / np.log10(2.0)                 # pendiente de la regresión frente a lg(r)
a = m.lp_as_4m - b * np.log10(4.0)         # ordenada desde el nivel a 4 m
rr = np.logspace(np.log10(2.0), np.log10(16.0), 100)

fig, ax = plt.subplots()
ax.semilogx(r, lp, "o", label="Lp,A,S medido")
ax.semilogx(rr, a + b * np.log10(rr), "--", label=f"D2,S = {m.d2s:.1f} dB")
ax.plot(4.0, m.lp_as_4m, "D", label=f"Lp,A,S,4m = {m.lp_as_4m:.0f} dB")
ax.set_xlabel("Distancia al hablante r [m]")
ax.set_ylabel("Nivel de habla ponderado A [dB]")
ax.set_xlim(1.8, 20.0)

twin = ax.twinx()
twin.semilogx(r, sti, "s-", color="#2ca02c", label="STI")
twin.axvline(m.rd, ls=":", color="#2ca02c")
twin.axvline(m.rp, ls=":", color="#9467bd")
twin.annotate(f"rD = {m.rd:.1f} m", (m.rd, 0.52))
twin.annotate(f"rP = {m.rp:.1f} m", (m.rp, 0.22))
twin.set_ylabel("STI")
twin.set_ylim(0.0, 1.0)

lines, labels = ax.get_legend_handles_labels()
tl, tlab = twin.get_legend_handles_labels()
ax.legend(lines + tl, labels + tlab, loc="best")
plt.show()
```

</details>

### Parámetros de `open_plan_metrics()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `positions_m` | array 1D | m | ≥ 4 posiciones, todas > 0 | Distancias fuente-receptor |
| `spl_a_speech` | array 1D | dB | misma longitud | Nivel de habla ponderado A `Lp,A,S,n` por posición |
| `sti_values` | array 1D | — | misma longitud | STI por posición (método completo de IEC 60268-16) |

Devuelve un `OpenPlanResult` con `d2s`, `lp_as_4m`, `rd` y `rp`.
`d2s`/`lp_as_4m` son `nan` si menos de dos posiciones caen en 2–16 m;
`rd`/`rp` son `nan` cuando el STI no decrece con la distancia. El STI por
posición puede medirse a su vez con las herramientas STIPA de la
[guía de Psicoacústica](/phonometry/es/guides/psychoacoustics/).

## 4. Aislamiento en campo e índices de un solo número (ISO 16283-1, ISO 717-1)

Para calificar una pared o un forjado, mide el nivel promediado en energía en
la sala **emisora** ($L_1$) y en la sala **receptora** ($L_2$) por banda de
tercio de octava y forma la diferencia de niveles $D = L_1 - L_2$. Dos
normalizaciones la hacen comparable entre salas. La **diferencia de niveles
estandarizada** refiere el tiempo de reverberación de la sala receptora $T$ a
$T_0 = 0.5$ s (de modo que con $T = 0.5$ s, $D_{nT} = D$ exactamente), y el
**índice de reducción sonora aparente** normaliza por la superficie del
cerramiento $S$ y el área de absorción de Sabine $A$:

$$
D_{nT} = D + 10 \log_{10} \frac{T}{T_0}, \qquad
R' = D + 10 \log_{10} \frac{S}{A}, \qquad A = \frac{0.16\ V}{T}.
$$

Las posiciones se promedian en energía con
$L = 10 \log_{10}\left( \frac{1}{n} \sum_i 10^{L_i/10} \right)$.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup_es.svg" alt="Montaje de aislamiento a ruido aéreo en campo: un altavoz en la sala emisora, micrófonos promediados en energía en las salas emisora y receptora a través del cerramiento común" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_insulation_setup_es_dark.svg" alt="Montaje de aislamiento a ruido aéreo en campo: un altavoz en la sala emisora, micrófonos promediados en energía en las salas emisora y receptora a través del cerramiento común" style="width:92%">

El espectro por bandas se reduce a un número mediante el **método de la curva
de referencia** de ISO 717-1: una curva de referencia fija se desplaza en
pasos de 1 dB hacia la curva medida hasta que la suma de desviaciones
*desfavorables* (donde la medición cae por debajo de la referencia) es lo más
grande posible pero no mayor que 32,0 dB (16 bandas de tercio de octava) o
10,0 dB (5 bandas de octava). El índice (`Rw`, `R'w`, `DnT,w` …) es la
referencia desplazada leída a 500 Hz. Los **términos de adaptación
espectral** $C$ (ruido rosa) y $C_{tr}$ (tráfico urbano) añaden la
penalización en baja frecuencia de una fuente real.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_es.png" alt="Índice de reducción sonora medido en tercios de octava con la curva de referencia de ISO 717-1 desplazada y el índice ponderado resultante a 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_rating_es_dark.png" alt="Índice de reducción sonora medido en tercios de octava con la curva de referencia de ISO 717-1 desplazada y el índice ponderado resultante a 500 Hz" style="width:80%">

```python
import numpy as np
from phonometry import airborne_insulation, weighted_rating, energy_average_level

# Promedia en energía varias posiciones de micrófono en una sala (dB)
print(round(float(energy_average_level([60.0, 66.0])), 1))   # 64.0

# Aislamiento en campo por banda; la superficie S y el volumen V añaden R'
l1 = np.full(16, 80.0)                                # niveles de la sala emisora
l2 = np.full(16, 40.0)                                # niveles de la sala receptora
t2 = np.full(16, 0.5)                                 # T de la sala receptora (s)
ins = airborne_insulation(l1, l2, t2, area=10.0, volume=50.0)
print(round(float(ins.dnt[0]), 1))                   # 40.0  (= D ya que T = T0)
print(round(float(ins.r_prime[0]), 1))               # 38.0

# Índice de un solo número desde un espectro R medido de 16 bandas (ISO 717-1 Anexo C)
R = [20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6,
     28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5]
w = weighted_rating(R)
print(w.rating, w.c, w.ctr)                          # 30 -2 -3  ->  Rw(C;Ctr) = 30(-2;-3)

w.plot()   # R' medido frente a la referencia ISO 717-1 desplazada, desviaciones sombreadas (requiere matplotlib)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — la curva medida frente a la referencia ISO 717-1 desplazada:
w.plot()
plt.show()

# A mano, con los campos de la curva por banda que ahora lleva el resultado:
fig, ax = plt.subplots()
ax.semilogx(w.band_centers, w.measured, "o-", label="R' medido")
ax.semilogx(w.band_centers, w.shifted_reference, "s--", label="Referencia desplazada")
ax.fill_between(w.band_centers, w.measured, w.shifted_reference,
                where=w.measured < w.shifted_reference, interpolate=True,
                alpha=0.3, label="Desviaciones desfavorables")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Índice de reducción sonora [dB]")
ax.set_title(f"Rw = {w.rating} dB  (C={w.c:+d}; Ctr={w.ctr:+d})")
ax.legend()
plt.show()
```

</details>

Calcula `l1`, `l2` y `t2` en las mismas 16 bandas de tercio de octava de
100 Hz a 3150 Hz — obtén `t2` de
`room_parameters(ir, fs, limits=(100, 3150), fraction=3).t30`, por ejemplo — y
pásalos a `airborne_insulation`. Alimenta el espectro `dnt` (o `r_prime`) de esa
función a `weighted_rating`, de modo que cada banda quede alineada índice a
índice con la curva de referencia ISO 717-1.

### Parámetros de `airborne_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `l1` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Niveles de la sala emisora (2D se promedia en energía) |
| `l2` | array 1D o 2D | dB | mismo número de bandas | Niveles de la sala receptora |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `area` | float, opcional | m² | > 0, con `volume` | Superficie del cerramiento `S` (habilita `R'`) |
| `volume` | float, opcional | m³ | > 0, con `area` | Volumen de la sala receptora `V` |
| `t0` | float | s | por defecto `0.5` | Tiempo de reverberación de referencia `T0` |

### Parámetros de `weighted_rating()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `values_by_band` | array 1D | dB | 16 (tercios) o 5 (octavas) | `R`, `R'`, `DnT` … medidos por banda |
| `bands` | str o `None` | — | `'third-octave'` / `'octave'` / `None` | `None` lo infiere del número de bandas |

`airborne_insulation()` devuelve un `AirborneInsulationResult` (`d`, `dnt`,
`r_prime` o `None`); `weighted_rating()` devuelve un `WeightedRatingResult`
(`rating`, `c`, `ctr`, `unfavourable_sum`, todos enteros salvo la suma).

### Ruido de impactos (ISO 16283-2, ISO 717-2)

El ruido de pisadas se califica al revés. En lugar de cuánto *bloquea* un
forjado, el aislamiento a impactos mide cuánto introduce en la sala inferior
una **máquina de impactos normalizada** situada en el forjado superior —así que
un número *mayor* es *peor*. El nivel de presión de ruido de impactos $L_i$
promediado en energía en la sala receptora se normaliza igual que el caso
aéreo, pero con un cambio de signo en el término de reverberación:

$$
L'_{nT} = L_i - 10 \log_{10} \frac{T}{T_0}, \qquad
L'_n = L_i + 10 \log_{10} \frac{A}{A_0}, \quad
A_0 = 10\ \text{m}^2,\ A = \frac{0.16\ V}{T}.
$$

El nivel de impactos **estandarizado** $L'_{nT}$ ($T_0 = 0.5$ s para viviendas)
solo necesita el $T$ de la sala receptora, así que con $T = 0.5$ s es igual a
$L_i$; el nivel **normalizado** $L'_n$ (referido a un área de absorción de
10 m²) necesita además el volumen de la sala receptora. Fíjate en el signo
**menos** —más reverberación *reduce* $L'_{nT}$, al contrario que el $D_{nT}$
aéreo.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impact_setup_es.svg" alt="Montaje de aislamiento a impactos en campo: una máquina de impactos normalizada sobre el suelo de la sala emisora superior, micrófonos promediados en energía en la sala receptora inferior, y el tiempo de reverberación de la sala receptora" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impact_setup_es_dark.svg" alt="Montaje de aislamiento a impactos en campo: una máquina de impactos normalizada sobre el suelo de la sala emisora superior, micrófonos promediados en energía en la sala receptora inferior, y el tiempo de reverberación de la sala receptora" style="width:92%">

El índice de un solo número (ISO 717-2) desplaza el mismo estilo de curva de
referencia, pero una **desviación desfavorable se produce ahora donde la
medición *supera* la referencia** (el ruido de impactos es peor cuanto más
alto) —el signo opuesto a ISO 717-1. El índice (`Ln,w`, `L'n,w`, `L'nT,w`) es
la referencia desplazada leída a 500 Hz; para bandas de octava se reduce además
en 5 dB. El término de adaptación espectral $C_I = L_{n,\text{sum}} - 15 - L_{n,w}$
usa la suma energética sobre 100–2500 Hz (16 tercios excluyendo 3150 Hz) o
125–2000 Hz (octavas).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_es.png" alt="Nivel de presión de ruido de impactos normalizado medido en tercios de octava con la curva de referencia de ISO 717-2 desplazada y el índice ponderado resultante leído a 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impact_rating_es_dark.png" alt="Nivel de presión de ruido de impactos normalizado medido en tercios de octava con la curva de referencia de ISO 717-2 desplazada y el índice ponderado resultante leído a 500 Hz" style="width:80%">

```python
import numpy as np
from phonometry import impact_insulation, weighted_impact_rating

# 16 niveles de impactos Li en tercios de octava (100 Hz - 3150 Hz), dB, del
# ejemplo resuelto del Anexo C de ISO 717-2, y el T de la sala receptora por banda.
li = np.array([62.1, 63.2, 63.5, 66.2, 68.5, 70.0, 71.7, 73.1,
               73.8, 73.5, 73.8, 73.3, 73.1, 73.0, 72.4, 71.2])
t2 = np.full(16, 0.5)

imp = impact_insulation(li, t2, volume=50.0)
print(round(float(imp.l_n_t[0]), 1))          # 62.1  (= Li ya que T = T0)
print(round(float(imp.l_n[0]), 1))            # 64.1  normalizado a A0 = 10 m^2

# Índice de impactos ponderado + término de adaptación espectral CI (ISO 717-2)
res_imp = weighted_impact_rating(imp.l_n_t)
print(res_imp.rating, res_imp.ci, res_imp.unfavourable_sum)   # 79 -11 28.0  ->  L'nT,w(CI)=79(-11)

# Los datos en banda de octava llevan la reducción extra de -5 dB (Cláusula 4.3.2)
octave = np.array([65.3, 64.5, 58.0, 55.8, 43.0])
print(weighted_impact_rating(octave).rating)  # 54

res_imp.plot()   # L'nT medido frente a la referencia ISO 717-2 desplazada, exceso sombreado (requiere matplotlib)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — L'nT medido frente a la referencia ISO 717-2 desplazada (exceso sombreado):
res_imp.plot()
plt.show()

# A mano, con la curva por banda que ahora lleva el resultado (signo opuesto: la
# desviación desfavorable está donde el nivel MEDIDO supera la referencia).
# Aquí la entrada fue l_n_t, así que la magnitud valorada es el nivel de campo L'nT,w:
fig, ax = plt.subplots()
ax.semilogx(res_imp.band_centers, res_imp.measured, "o-", label="L'nT medido")
ax.semilogx(res_imp.band_centers, res_imp.shifted_reference, "s--", label="Referencia desplazada")
ax.fill_between(res_imp.band_centers, res_imp.shifted_reference, res_imp.measured,
                where=res_imp.measured > res_imp.shifted_reference, interpolate=True,
                alpha=0.3, label="Desviaciones desfavorables")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de presión sonora de impacto [dB]")
ax.set_title(f"L'nT,w = {res_imp.rating} dB  (CI={res_imp.ci:+d})")
ax.legend()
plt.show()
```

</details>

Pasa el `l_n_t` (o `l_n`) de `impact_insulation` directamente a
`weighted_impact_rating`; el índice y `CI` reproducen los valores del Anexo C de
ISO 717-2 (tercios `L'nT,w = 79`, `CI = −11`; octava `54`, `CI = 0`).

#### Parámetros de `impact_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `li` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | SPL de impactos promediado en energía (2D se promedia sobre las posiciones) |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `volume` | float, opcional | m³ | > 0 | `V` de la sala receptora (habilita `L'n`) |
| `t0` | float | s | por defecto `0.5` | Tiempo de reverberación de referencia `T0` |

#### Parámetros de `weighted_impact_rating()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `values_by_band` | array 1D | dB | 16 (tercios) o 5 (octavas) | `Ln`, `L'n` o `L'nT` medidos por banda |
| `bands` | str o `None` | — | `'third-octave'` / `'octave'` / `None` | `None` lo infiere del número de bandas |

`impact_insulation()` devuelve un `ImpactInsulationResult` (`l_n_t`, `l_n` o
`None`); `weighted_impact_rating()` devuelve un `ImpactRatingResult` (`rating`,
`ci` enteros, `unfavourable_sum` en dB).

### Aislamiento a ruido aéreo de fachadas en campo (ISO 16283-3)

La misma lógica fuente/receptor alcanza la **fachada** del edificio, pero ahora
la fuente está *en el exterior*: un altavoz a 45° o el propio tráfico rodado. En
lugar de una diferencia de niveles a través de un cerramiento interior,
ISO 16283-3 referencia el nivel de la sala receptora $L_2$ al nivel **2 m frente
a la fachada** $L_{1,2m}$, dando la diferencia de niveles $D_{2m}$ y, exactamente
como en el caso a ruido aéreo, sus formas estandarizada y normalizada:

$$
D_{2m} = L_{1,2m} - L_2, \quad
D_{2m,nT} = D_{2m} + 10 \log_{10}\frac{T}{T_0}, \quad
D_{2m,n} = D_{2m} - 10 \log_{10}\frac{A}{A_0},
$$

con $T_0 = 0.5$ s, $A_0 = 10$ m² y $A = 0.16\ V/T$ (viviendas). Cuando el
micrófono se sitúa **sobre el elemento de ensayo** (nivel superficial $L_{1,s}$),
el método del *elemento* también da un índice de reducción sonora aparente, que
lleva una corrección fija por ángulo de incidencia: $-1.5$ dB para el método del
altavoz a 45° y $-3$ dB para el método de tráfico rodado con todos los ángulos:

$$
R'_{45°} = L_{1,s} - L_2 + 10 \log_{10}\frac{S}{A} - 1.5, \qquad
R'_{tr,s} = L_{1,s} - L_2 + 10 \log_{10}\frac{S}{A} - 3.
$$

La magnitud de fachada es a ruido aéreo, así que su índice de un solo número usa
la curva de referencia de **ISO 717-1** a través de `weighted_rating` sin cambios
(Anexo F).

```python
import numpy as np
from phonometry import facade_insulation, weighted_rating

# Nivel exterior 2 m frente a la fachada, nivel de la sala receptora y T por
# banda de tercio de octava; surface_level es el micrófono sobre el elemento de ensayo.
l1_2m = np.full(16, 75.0)                              # L1,2m en el exterior
l2 = np.full(16, 33.0)                                 # L2 de la sala receptora
t2 = np.full(16, 0.5)                                  # T de la sala receptora (s)

fac = facade_insulation(l1_2m, l2, t2, volume=50.0, area=11.5,
                        surface_level=np.full(16, 78.0), method="loudspeaker")
print(round(float(fac.d_2m[0]), 1))                    # 42.0  D2m = L1,2m - L2
print(round(float(fac.d_2m_nt[0]), 1))                 # 42.0  (= D2m ya que T = T0)
print(round(float(fac.d_2m_n[0]), 1))                  # 40.0  normalizado a A0 = 10 m^2
print(round(float(fac.r_prime[0]), 1))                 # 42.1  R'45deg (altavoz, -1.5 dB)

# El método del elemento por tráfico rodado lleva en su lugar la corrección de -3 dB para todos los ángulos
tr = facade_insulation(l1_2m, l2, t2, volume=50.0, area=11.5,
                       surface_level=np.full(16, 78.0), method="road_traffic")
print(round(float(tr.r_prime[0]), 1))                  # 40.6  R'tr,s (tráfico, -3 dB)

# La magnitud de fachada es a ruido aéreo: valora D2m,nT con el motor de ISO 717-1
print(weighted_rating(fac.d_2m_nt).rating)             # 42  Dls,2m,nT,w

fac.plot()   # D2m,nT por banda con D2m, D2m,n y R' superpuestos (requiere matplotlib)
```

`surface_level`, `area` y `volume` son todos opcionales: solo con `l1_2m`, `l2`
y `t2` la función devuelve `d_2m` y `d_2m_nt`; añade `volume` para `d_2m_n`;
añade `surface_level` **y** `area` **y** `volume` para `r_prime`. Las posiciones
se promedian en energía con la fórmula del nivel superficial (Cláusula 9.5.1);
se asume que los niveles por banda ya están corregidos por ruido de fondo.

#### Parámetros de `facade_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `l1_2m` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Nivel 2 m frente a la fachada `L1,2m` |
| `l2` | array 1D o 2D | dB | mismo número de bandas | Niveles de la sala receptora |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `area` | float, opcional | m² | > 0, con `surface_level`, `volume` | Superficie del elemento de ensayo `S` (habilita `R'`) |
| `volume` | float, opcional | m³ | > 0 | Sala receptora `V` (habilita `D2m,n`; requerido para `R'`) |
| `surface_level` | array 1D/2D, opcional | dB | mismo número de bandas | Nivel superficial `L1,s` sobre el elemento (habilita `R'`) |
| `method` | str | — | `'loudspeaker'` (−1,5 dB) / `'road_traffic'` (−3 dB) | Corrección por ángulo de incidencia de `R'` |
| `t0` | float | s | por defecto `0.5` | Tiempo de reverberación de referencia `T0` |
| `frequencies` | array 1D, opcional | Hz | — | Centros de banda que lleva el resultado para representar |

`facade_insulation()` devuelve un `FacadeInsulationResult` (`d_2m`, `d_2m_nt`,
`d_2m_n` o `None`, `r_prime` o `None`, `frequencies`); pasa cualquier magnitud de
fachada de 16 bandas a `weighted_rating` para su número único de ISO 717-1.

## 5. Medición en laboratorio (ISO 10140)

Todo lo anterior es una medición **en campo** (las magnitudes con prima $R'$,
$L'_n$): el número que un edificio real alcanza, con transmisión por flancos
incluida. Para valorar un elemento por sí solo —un tipo de pared, un suelo
flotante, una ventana— se lleva a un **laboratorio** cualificado (ISO 10140),
donde la transmisión por flancos suprimida hace que la transmisión *directa* sea
toda la historia. Las fórmulas pierden sus primas: el **índice de reducción
sonora** $R$ (no $R'$) y el **nivel de impactos normalizado** $L_n$ (no $L'_n$),
con el área de absorción de la sala receptora $A = 0.16\ V/T$ ahora una propiedad
conocida de la instalación:

$$
R = L_1 - L_2 + 10 \log_{10}\frac{S}{A}, \qquad
L_n = L_i + 10 \log_{10}\frac{A}{A_0}, \quad A_0 = 10\ \text{m}^2.
$$

| | Campo (ISO 16283) | Laboratorio (ISO 10140) |
| :--- | :--- | :--- |
| Ruido aéreo | $R'$ aparente (con flancos) | $R$ directo (flancos suprimidos) |
| Impactos | $L'_n$ aparente | $L_n$ directo |
| Área de absorción | medida en la sala | propiedad de la instalación |

Los índices de un solo número reutilizan los mismísimos motores de ISO 717-1/2
(`weighted_rating`, `weighted_impact_rating`): un espectro $R$ se valora a $R_w$
exactamente igual que un espectro $R'$ se valoraba a $R'_w$. Antes de formar el
índice, los niveles de la sala receptora deben **corregirse por ruido de fondo**
(Cláusula 4.3): la resta energética $10 \log_{10}(10^{L_{sb}/10} - 10^{L_b/10})$
se aplica para un margen señal-fondo de 6–15 dB, una corrección fija de 1,3 dB
(el *límite de medición*) en 6 dB o por debajo, y ninguna corrección en 15 dB o
por encima.

```python
import numpy as np
from phonometry import (lab_airborne_insulation, lab_impact_insulation,
                        background_correction)

# Niveles emisor/receptor y T de la sala receptora en las 16 bandas de tercio
# de octava; S es el área libre de la abertura de ensayo, V el volumen de la sala receptora.
l1 = np.full(16, 80.0)
l2 = np.full(16, 40.0)
t2 = np.full(16, 0.5)
lab = lab_airborne_insulation(l1, l2, t2, area=10.0, volume=50.0)
print(round(float(lab.r[0]), 1))              # 38.0  R = L1 - L2 + 10 lg(S/A)
print(round(float(lab.absorption[0]), 1))     # 16.0  A = 0.16 V / T (m^2)
print(lab.rating.rating, lab.rating.c, lab.rating.ctr)   # 38 0 0  ->  Rw(C;Ctr)

# Impactos: el nivel de la máquina de impactos Li normalizado a A0 = 10 m^2 da Ln
li = np.array([62.1, 63.2, 63.5, 66.2, 68.5, 70.0, 71.7, 73.1,
               73.8, 73.5, 73.8, 73.3, 73.1, 73.0, 72.4, 71.2])
imp = lab_impact_insulation(li, t2, volume=50.0)
print(round(float(imp.l_n[0]), 1))            # 64.1  Ln = Li + 10 lg(A/A0)
print(imp.rating.rating, imp.rating.ci)       # 81 -11  ->  Ln,w(CI)

# Corrección por ruido de fondo: márgenes 6 / 1 / 20 dB -> saturado / saturado / sin cambio
corrected = background_correction([30.0, 33.0, 50.0], [24.0, 32.0, 30.0])
print(np.round(corrected, 1))                 # [28.7 31.7 50.0]  (saturación de 1.3 dB dos veces)

lab.rating.plot()   # R medido frente a la referencia ISO 717-1 desplazada (requiere matplotlib)
```

Un margen en 6 dB o por debajo emite un `LabInsulationWarning` y marca la banda
como el límite de medición; captúralo con `warnings.simplefilter("error",
LabInsulationWarning)`. El índice automático se forma solo cuando se suministran
exactamente 16 valores en tercio de octava o 5 en octava (`rating` es `None` en
caso contrario).

#### Parámetros de `lab_airborne_insulation()` / `lab_impact_insulation()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `l1` / `l2` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | Niveles emisor / receptor (ruido aéreo) |
| `li` | array 1D o 2D | dB | uno/banda, o `(posiciones, bandas)` | SPL de impactos de la máquina de impactos (impactos) |
| `t2` | array 1D | s | > 0, uno por banda | Tiempo de reverberación de la sala receptora |
| `area` | float | m² | > 0 | Área libre de la abertura de ensayo `S` (solo ruido aéreo) |
| `volume` | float | m³ | > 0 | Volumen de la sala receptora `V` |

`lab_airborne_insulation()` devuelve un `LabAirborneInsulationResult` (`r`,
`absorption`, `rating`); `lab_impact_insulation()` un
`LabImpactInsulationResult` (`l_n`, `absorption`, `rating`);
`background_correction(signal_and_background, background)` devuelve los niveles
corregidos directamente.

## 6. Predicción del comportamiento (EN 12354)

Un índice de laboratorio describe un elemento de forma aislada, pero el sonido
que un edificio transmite realmente también viaja *alrededor* del cerramiento
—por el suelo, por la fachada, a través de las paredes de flanco— y se vuelve a
radiar en la sala receptora. Esta **transmisión por flancos** es toda la
diferencia entre el $R$ de laboratorio y el $R'$ de campo. EN 12354 predice el
índice aparente in situ a partir de los índices de laboratorio de los elementos
más la transmisión vibratoria de sus uniones.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths_es.svg" alt="El camino directo Dd a través del elemento separador y los tres caminos de flanco Ff, Df y Fd en cada unión entre un elemento de flanco y el elemento separador" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_flanking_paths_es_dark.svg" alt="El camino directo Dd a través del elemento separador y los tres caminos de flanco Ff, Df y Fd en cada unión entre un elemento de flanco y el elemento separador" style="width:92%">

Cada unión entre un elemento de flanco y el elemento separador lleva tres
caminos —$Ff$ (flanco→flanco), $Df$ (directo→flanco) y $Fd$ (flanco→directo)—
junto al único camino directo $Dd$. El **modelo simplificado de un solo número**
los combina energéticamente (Fórmula 26):

$$
R'_w = -10 \log_{10}\Big[ 10^{-R_{Dd,w}/10}
      + \sum 10^{-R_{Ff,w}/10} + \sum 10^{-R_{Df,w}/10}
      + \sum 10^{-R_{Fd,w}/10} \Big],
$$

con el camino directo $R_{Dd,w} = R_{s,w} + \Delta R_{Dd,w}$ (Fórmula 27) y cada
camino de flanco (Fórmula 28a)

$$
R_{ij,w} = \tfrac{R_{i,w} + R_{j,w}}{2} + \Delta R_{ij,w} + K_{ij}
         + 10 \log_{10}\frac{S_s}{l_0\ l_f},
$$

donde $l_0 = 1$ m es la longitud de acoplamiento de referencia, $l_f$ la longitud
de acoplamiento de la unión y $K_{ij}$ el **índice de reducción vibracional** de
la unión (Anexo E, empírico en la relación de masas
$M = \log_{10}(m'_{\perp,i}/m'_i)$).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo_es.png" alt="Índices de reducción sonora por camino para el ejemplo del Anexo H.3 de EN 12354-1 y la fracción de energía transmitida de cada camino, mostrando el camino directo dominando en R'w = 52 dB" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/prediction_flanking_demo_es_dark.png" alt="Índices de reducción sonora por camino para el ejemplo del Anexo H.3 de EN 12354-1 y la fracción de energía transmitida de cada camino, mostrando el camino directo dominando en R'w = 52 dB" style="width:80%">

```python
import numpy as np
from phonometry import (junction_vibration_reduction, flanking_element,
                        predicted_airborne_insulation)

# EN 12354-1 Anexo H.3: una pared separadora Rs,w = 57 dB, área Ss = 11.5 m², con
# cuatro elementos de flanco. El modelo simplificado lee el Kij de cada unión a
# 500 Hz a partir de la relación de masas m'perp / m' (Anexo E); aquí la unión
# rígida en cruz del suelo (la relación de masas está redondeada, de ahí 12.5 vs Anexo 12.4):
print(round(junction_vibration_reduction("rigid_cross", "through", 1.61), 1))  # 12.5  KFf
print(round(junction_vibration_reduction("rigid_cross", "corner",  1.61), 1))  #  8.9  KFd = KDf

# Construye los tres caminos de flanco (Ff, Df, Fd) de cada elemento a partir del
# Kij tabulado del Anexo H, luego combina el camino directo Dd energéticamente (Fórmula 26).
elements = [   # (nombre, Rw, KFf, KFd = KDf, longitud de acoplamiento lf)
    ("floor",    49, 12.4,  8.9, 4.50),
    ("ceiling",  46, 14.4,  9.2, 4.50),
    ("facade",   42, 12.6,  6.7, 2.55),
    ("int-wall", 33, 33.5, 15.7, 2.55),
]
paths = []
for name, rw, k_ff, k_fd, lf in elements:
    paths += flanking_element(label=name, r_flanking=rw, r_separating=57,
                              k_ff=k_ff, k_fd=k_fd, k_df=k_fd,
                              separating_area=11.5, coupling_length=lf)

res = predicted_airborne_insulation(r_direct=57.0, flanking_paths=paths)
print(round(res.r_prime_w, 1))                          # 52.2  ->  R'w = 52 dB
print(res.dominant.label, round(res.dominant.fraction, 2))   # Dd 0.33 (domina el directo)
```

Cada camino de flanco añadido rebaja estrictamente $R'_w$ por debajo del directo
$R_{Dd,w} = 57$; `res.paths` expone la fracción de energía transmitida de cada
camino, de modo que el camino dominante queda visible. La Cláusula 4.4.2 también
impone un límite inferior $K_{ij} \ge K_{ij,\min}$ a partir de la geometría de la
unión: calcúlalo con `junction_min_vibration_reduction` y pásalo a
`flanking_path(..., kij_min=...)`, que eleva un $K_{ij}$ por debajo del límite
hasta el mínimo:

```python
from phonometry import junction_min_vibration_reduction
# Kij,min = 10 lg[lf·l0·(1/Si + 1/Sj)]; los elementos grandes dan un límite bajo
# (aquí negativo), así que un Kij tabulado realista rara vez se satura.
print(round(junction_min_vibration_reduction(coupling_length=4.5,
                                             s_i=11.5, s_j=11.5), 1))     # -1.1
```

La contrapartida a impactos (EN 12354-2, Fórmula 21) es una resta directa:
$L'_{n,w} = L_{n,w,eq} - \Delta L_w + K$, con el nivel equivalente del suelo
desnudo $L_{n,w,eq} = 164 - 35 \log_{10}(m'/m'_0)$ (Anexo B), la mejora del
revestimiento $\Delta L_w$ (ISO 717-2) y la corrección por flancos $K$ de la
Tabla 1.

```python
from phonometry import (equivalent_impact_level, impact_flanking_correction,
                        predicted_impact_insulation, standardized_impact_level)

# EN 12354-2 Anexo E.3: un forjado de hormigón de 0.14 m (m' = 322 kg/m²) con un
# suelo flotante (ΔLw = 33 dB), salas una sobre otra, masa media de flanco 145 kg/m².
ln_eq = equivalent_impact_level(322.0)                   # 164 - 35 lg(m')
k = impact_flanking_correction(322.0, 145.0)             # Tabla 1 (sep 322, flk 145)
imp = predicted_impact_insulation(ln_w_eq=ln_eq, delta_l_w=33.0, k_correction=k)
print(round(ln_eq, 1), k, round(imp.l_prime_n_w, 1))     # 76.2 2 45.2  ->  L'n,w = 45 dB
print(round(standardized_impact_level(imp.l_prime_n_w, 50.0), 1))   # 43.0  L'nT,w
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# Índice de reducción sonora por camino y fracción de energía transmitida de cada
# camino para el resultado del Anexo H.3 calculado arriba.
labels = [p.label for p in res.paths]
r_w = [p.r_w for p in res.paths]
frac = [100.0 * p.fraction for p in res.paths]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
ax1.bar(labels, r_w, color="tab:blue")
ax1.axhline(res.r_prime_w, ls="--", color="k", label=f"R'w = {res.r_prime_w:.1f} dB")
ax1.set_ylabel("Rij,w del camino [dB]"); ax1.legend()
ax2.bar(labels, frac, color="tab:orange")
ax2.set_ylabel("Fracción de energía [%]"); ax2.set_xlabel("Camino de transmisión")
for ax in (ax1, ax2):
    ax.tick_params(axis="x", rotation=45)
fig.suptitle("EN 12354-1 Anexo H.3 — transmisión por flancos")
fig.tight_layout()
plt.show()
```

</details>

#### Parámetros de `junction_vibration_reduction()` / `flanking_element()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `junction_type` | str | — | `'rigid_cross'` / `'rigid_t'` / `'flexible_t'` / `'lightweight_facade'` | Geometría de la unión (Anexo E) |
| `path` | str | — | `'through'` (K13) / `'corner'` (K12 = K23) | Rama del camino |
| `mass_ratio` | float | — | > 0 | `m'⊥,i / m'i` (Fórmula E.2) |
| `frequency` | float | Hz | por defecto `500` | Solo `flexible_t` depende de la frecuencia |
| `r_flanking` / `r_separating` | float | dB | — | Índices ponderados del elemento de flanco / separador |
| `k_ff` / `k_fd` / `k_df` | float | dB | — | `Kij` de la unión para los tres caminos |
| `separating_area` | float | m² | > 0 | Superficie del elemento separador `Ss` |
| `coupling_length` | float | m | > 0 | Longitud de acoplamiento de la unión `lf` |
| `delta_r_ff` / `delta_r_fd` / `delta_r_df` | float | dB | por defecto `0` | Mejoras del trasdosado por camino |

`predicted_airborne_insulation()` devuelve un `AirbornePredictionResult`
(`r_prime_w`, `r_direct_w`, `paths` de `PathContribution`, `dominant`);
`predicted_impact_insulation()` un `ImpactPredictionResult` (`l_prime_n_w`,
`ln_w_eq`, `delta_l_w`, `k_correction`). El modelo simplificado lleva una
desviación típica declarada de unos 2 dB (Cláusula 5).

## 7. Incertidumbre de medición (ISO 12999-1)

Un índice sin incertidumbre es solo medio resultado. ISO 12999-1 no vuelve a
medir nada; tabula la **incertidumbre típica** $u$ de cada magnitud de
aislamiento acústico —derivada de ensayos interlaboratorio— y prescribe cómo
expandirla y combinarla. Qué desviación típica es $u$ depende de la **situación
de medición** (Cláusula 5.2):

| Situación | Significado | Incertidumbre típica $u$ |
| :--- | :--- | :--- |
| **A** | caracterización en laboratorio (ISO 10140) | reproducibilidad $\sigma_R$ |
| **B** | misma ubicación, equipos distintos | in situ $\sigma_{situ}$ |
| **C** | misma ubicación, mismo operador repetido | repetibilidad $\sigma_r$ |

La incertidumbre expandida es $U = k\ u$ (Fórmula 2) con el factor de cobertura
$k$ de la Tabla 8. Un intervalo bilateral $Y = y \pm U$ (Fórmula 3, $k = 1.96$ al
95 %) *informa* un valor; el factor **unilateral** ($k = 1.65$ al 95 %) *declara
conformidad* con un requisito (Fórmulas 4/5).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_es.png" alt="Un índice ponderado informado con su incertidumbre expandida bilateral al 95 % en las situaciones A, B y C, con la incertidumbre de reproducibilidad más ancha y la de repetibilidad más estrecha" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/insulation_uncertainty_demo_es_dark.png" alt="Un índice ponderado informado con su incertidumbre expandida bilateral al 95 % en las situaciones A, B y C, con la incertidumbre de reproducibilidad más ancha y la de repetibilidad más estrecha" style="width:80%">

```python
from phonometry import (band_uncertainty, single_number_uncertainty,
                        uncertain_value, satisfies_lower_requirement)

# Situación B (mismo edificio, equipos distintos) -> la desviación típica in situ.
print(single_number_uncertainty("r_w", "B"))       # 0.9  dB  (Tabla 3)
u = band_uncertainty("airborne", "B")              # u por banda (Tabla 2)
print(len(u.frequencies), u.uncertainties[10])     # 21 1.1  (la banda de 500 Hz)

# Informa R'w = 52 dB con un intervalo bilateral al 95 % (k = 1.96, Tabla 8):
uv = uncertain_value(52.0, "rprime_w", "B")        # los alias resuelven a r_w
print(uv.coverage_factor, round(uv.expanded_uncertainty, 1))    # 1.96 1.8
print(round(uv.lower, 1), round(uv.upper, 1))      # 50.2 53.8  ->  52 ± 1.8 dB

# Declarar conformidad usa el factor UNILATERAL (k = 1.65): ¿supera R'w de forma
# demostrable un requisito de 50 dB?
uc = uncertain_value(52.0, "rprime_w", "B", one_sided=True)
print(satisfies_lower_requirement(52.0, uc.expanded_uncertainty, 50.0))   # True
```

Las magnitudes a impactos ofrecen solo las situaciones B/C (Tabla 4, sin banda de
500 Hz en la edición de 2020), y $\Delta L$ solo la situación A. Los descriptores
son insensibles a mayúsculas y con alias (`rprime_w`/`dnt_w`→`r_w`,
`lprime_n_w`→`ln_w`); combina componentes independientes en cuadratura con
`combine_uncertainties`, y redúcelas por $m$ mediciones independientes con
`reduce_by_independent_measurements` ($u/\sqrt{m}$).

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
from phonometry import uncertain_value

# El mismo R'w = 52 dB informado en cada situación con su U bilateral al 95 %.
situations = ["A", "B", "C"]
vals = [uncertain_value(52.0, "r_w", s) for s in situations]

fig, ax = plt.subplots(figsize=(7, 4))
ax.errorbar(situations, [v.value for v in vals],
            yerr=[v.expanded_uncertainty for v in vals],
            fmt="o", capsize=8, color="tab:blue")
for s, v in zip(situations, vals):
    ax.annotate(f"±{v.expanded_uncertainty:.1f}", (s, v.upper),
                textcoords="offset points", xytext=(8, 4))
ax.set_ylabel("R'w [dB]"); ax.set_xlabel("Situación de medición")
ax.set_title("R'w = 52 dB con incertidumbre expandida al 95 % (ISO 12999-1)")
fig.tight_layout()
plt.show()
```

</details>

#### Parámetros de `band_uncertainty()` / `single_number_uncertainty()` / `uncertain_value()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `measurand` | str | — | `'airborne'` / `'impact'` / `'impact_reduction'` | Selecciona la Tabla 2 / 4 / 6 |
| `quantity` | str | — | `'r_w'`, `'ln_w'`, `'delta_lw'` (+ alias, variantes `+c`/`+ctr`) | Descriptor de un solo número |
| `situation` | str | — | `'A'` / `'B'` / `'C'` | Situación de medición (Cláusula 5.2) |
| `value` | float | dB | — | Mejor estimación `y` a la que adjuntar `U` |
| `coverage` | float | — | por defecto `0.95` | Nivel de confianza (Tabla 8) |
| `one_sided` | bool | — | por defecto `False` | Factor unilateral para verificaciones de conformidad |
| `upper_limit` | bool | — | por defecto `False` | Selecciona el límite superior σR95 (ruido aéreo, situación A) |

`band_uncertainty()` devuelve una `BandUncertainty` (`frequencies`,
`uncertainties`, `.to_arrays()`); `single_number_uncertainty()` un float;
`uncertain_value()` un `UncertainValue` (`value`, `standard_uncertainty`,
`coverage_factor`, `expanded_uncertainty`, `.lower`, `.upper`). El mapa de solo
lectura `COVERAGE_FACTORS` expone la Tabla 8 indexada por `(confidence, one_sided)`.

## 8. Absorción sonora (ISO 354)

El área de absorción sonora equivalente `A` que gobierna `R'`, `L'n`, la
corrección ambiental `K2` de ISO 3744 y el término de absorción de ISO 3741 se
mide a su vez en una sala reverberante
(ISO 354). Mide el tiempo de reverberación de la sala **vacía** ($T_1$) y de
nuevo **con la muestra de ensayo instalada** ($T_2$); la absorción de la muestra
es la diferencia de las dos áreas de Sabine, y dividiendo por el área cubierta
se obtiene el coeficiente de absorción:

$$
A = \frac{55.3\ V}{c\ T} - 4 V m, \qquad
\alpha_s = \frac{A_2 - A_1}{S}, \qquad c = 331 + 0.6\ t ,
$$

con $c$ a partir de la temperatura del aire de la sala $t$ en °C (válida
15–30 °C) y $m$ el coeficiente de atenuación en potencia del aire (por defecto
0; convierte un $\alpha$ de ISO 9613-1 en dB/m con `attenuation_from_alpha`).
Como los efectos de borde y difracción pueden dispersar más energía de la que
intercepta el área plana de la muestra, $\alpha_s$ puede superar 1,0 y nunca se
satura (ISO 354 Cláusula 3.7).

```python
import numpy as np
from phonometry import absorption_area, absorption_coefficient

# Tiempos de reverberación en tercios de octava de una sala de 200 m^3, vacía (T1)
# y con una muestra absorbente de 10.8 m^2 instalada (T2).
t1 = np.array([5.0, 4.0, 3.0])
t2 = np.array([3.0, 2.5, 2.0])

a_empty = absorption_area(t1, volume=200.0, temperature=20.0)
print(np.round(a_empty, 2))                    # [ 6.45  8.06 10.75] m^2

alpha = absorption_coefficient(t1, t2, volume=200.0, sample_area=10.8,
                               temperature1=20.0)
print(np.round(alpha, 3))                      # [0.398 0.448 0.498]
```

`T1` y `T2` son exactamente los tiempos de reverberación que devuelve
`room_parameters`, así que una medición de decaimiento ISO 3382-2 de la sala
vacía y tratada fluye directamente a `absorption_coefficient`. Un volumen de
sala por debajo del mínimo de 150 m³ o un área de muestra fuera de 10–12 m²
genera un `AbsorptionWarning` de aviso; el resultado se devuelve igualmente.

### Parámetros de `absorption_area()` / `absorption_coefficient()`

| Parámetro | Tipo | Unidades | Rango / valor por defecto | Notas |
| :--- | :--- | :--- | :--- | :--- |
| `t60` / `t1`, `t2` | array 1D | s | > 0 | Tiempo(s) de reverberación; `t1` vacía, `t2` con la muestra |
| `volume` | float | m³ | > 0 | Volumen de la sala `V` (aviso por debajo de 150 m³) |
| `sample_area` | float | m² | > 0 | Área `S` que cubre la muestra (solo coeficiente) |
| `temperature` / `temperature1`, `temperature2` | float | °C | por defecto `20.0`, 15–30 | Fija `c` vía Ec. (6); `temperature2` por defecto es `temperature1` |
| `speed_of_sound` (`…1`, `…2`) | float, opcional | m/s | > 0 | Sobrescribe la `c` derivada de la temperatura |
| `m` (`m1`, `m2`) | float o array 1D | 1/m | ≥ 0, por defecto `0` | Coeficiente de atenuación en potencia del aire |

`absorption_area()` devuelve el área de absorción sonora equivalente `A` (m²)
con la forma de `t60`; `absorption_coefficient()` devuelve `alpha_s`;
`attenuation_from_alpha(alpha)` convierte un `alpha` de ISO 9613-1 (dB/m) a `m`.

## Véase también

- [Potencia sonora](/phonometry/es/guides/sound-power/) — los métodos de `LW` que
  consumen el área de absorción de ISO 354 (el `K2` de ISO 3744 y el término de
  absorción de ISO 3741).
- [Psicoacústica e inteligibilidad del habla](/phonometry/es/guides/psychoacoustics/) — el
  STI/STIPA alimenta los `sti_values` de oficinas diáfanas; sonoridad y sharpness.
- [Bancos de filtros](/phonometry/es/guides/filter-banks/) — los filtros de octava
  fraccionaria IEC 61260 usados para las curvas de decaimiento por banda y los espectros de
  aislamiento.
- [Niveles](/phonometry/es/guides/levels/) — el promediado en energía y las métricas de
  nivel tras los niveles de las salas emisora/receptora.
- [Teoría](/phonometry/es/reference/theory/) — la integración de Schroeder, las ventanas de
  regresión y la derivación de la curva de referencia.

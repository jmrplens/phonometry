---
title: "Acústica de salas y edificación"
description: "Adquisición de la respuesta al impulso (ISO 18233), parámetros de sala EDT/T20/T30/C50/C80/Ts (ISO 3382-1/2), métricas de habla en oficinas diáfanas (ISO 3382-3), aislamiento acústico en campo a ruido aéreo y a impactos con índices ponderados (ISO 16283-1/2, ISO 717-1/2) y absorción sonora en sala reverberante (ISO 354)."
---

La acústica de salas y de la edificación parte de una única medición: la
**respuesta al impulso** (RI) entre una fuente y un receptor. Fíltrala en
bandas e intégrala, y da el tiempo de reverberación, la claridad y la
inteligibilidad del habla; mídela a ambos lados de una pared, y da el
aislamiento acústico del cerramiento. Esta página sigue esa cadena en orden
de medición: adquirir la RI (ISO 18233), convertirla en parámetros de sala
(ISO 3382-1/2), métricas espaciales del habla para oficinas diáfanas
(ISO 3382-3), aislamiento en campo a ruido aéreo y a impactos con índices de
un solo número (ISO 16283-1/2, ISO 717-1/2) y, cerrando el ciclo, la absorción
sonora de un material en una sala reverberante (ISO 354).

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
r = weighted_impact_rating(imp.l_n_t)
print(r.rating, r.ci, r.unfavourable_sum)     # 79 -11 28.0  ->  L'nT,w(CI)=79(-11)

# Los datos en banda de octava llevan la reducción extra de -5 dB (Cláusula 4.3.2)
octave = np.array([65.3, 64.5, 58.0, 55.8, 43.0])
print(weighted_impact_rating(octave).rating)  # 54

r.plot()   # Ln medido frente a la referencia ISO 717-2 desplazada, exceso sombreado (requiere matplotlib)
```

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt

# En una línea — Ln medido frente a la referencia ISO 717-2 desplazada (exceso sombreado):
r.plot()
plt.show()

# A mano, con la curva por banda que ahora lleva el resultado (signo opuesto: la
# desviación desfavorable está donde el nivel MEDIDO supera la referencia):
fig, ax = plt.subplots()
ax.semilogx(r.band_centers, r.measured, "o-", label="Ln medido")
ax.semilogx(r.band_centers, r.shifted_reference, "s--", label="Referencia desplazada")
ax.fill_between(r.band_centers, r.shifted_reference, r.measured,
                where=r.measured > r.shifted_reference, interpolate=True,
                alpha=0.3, label="Desviaciones desfavorables")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Nivel de presión sonora de impacto [dB]")
ax.set_title(f"Ln,w = {r.rating} dB  (CI={r.ci:+d})")
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

## 5. Absorción sonora (ISO 354)

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

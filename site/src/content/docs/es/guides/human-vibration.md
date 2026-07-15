---
title: "Vibración en humanos"
description: "Exposición a vibración de cuerpo completo y mano-brazo: las ponderaciones frecuenciales de ISO 8041-1, el valor eficaz ponderado y las medidas de dosis de ISO 2631-1 (VDV, MTVV, MSDV, factor de cresta), el valor total de vibración y la exposición diaria de 8 horas A(8), con la orientación de exposición de ISO 5349 y los valores de acción y límite de la Directiva 2002/44/CE."
---

La vibración transmitida a una persona se evalúa con la misma cadena de medida
sea cual sea su origen: la aceleración se **pondera en frecuencia** para reflejar
cómo responde el cuerpo a cada frecuencia, se reduce a una aceleración **eficaz
ponderada** (con medidas de dosis para choques y registros largos), se combina
entre ejes en un **valor total de vibración** y, por último, se normaliza a una
**exposición diaria de 8 horas** `A(8)` que se compara con los valores de acción
y límite de la directiva europea.

Las ponderaciones se definen una sola vez, en **ISO 8041-1:2017**, como una
cascada de filtros analógicos; **ISO 2631-1** las aplica a la vibración de cuerpo
completo, **ISO 2631-2** a la vibración en edificios, **ISO 2631-4** al confort
de marcha ferroviaria e **ISO 5349-1/-2** a la vibración transmitida a la mano.
Esta página recorre toda la cadena.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_human_vibration_es.svg" alt="Cadena de medida de vibración de cuerpo completo: un acelerómetro triaxial en la interfaz asiento/cuerpo de una persona sentada mide la aceleración x, y y z; cada eje se limita en banda y se pondera en frecuencia (Wk vertical, Wd horizontal) según ISO 8041-1, se reduce a un valor eficaz ponderado a_w y VDV según ISO 2631-1, se combina en el valor total de vibración a_v, se normaliza a la exposición diaria A(8) y se evalúa frente al VAE y el VLE de la Directiva 2002/44/CE" style="width:94%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_human_vibration_es_dark.svg" alt="Cadena de medida de vibración de cuerpo completo: un acelerómetro triaxial en la interfaz asiento/cuerpo de una persona sentada mide la aceleración x, y y z; cada eje se limita en banda y se pondera en frecuencia (Wk vertical, Wd horizontal) según ISO 8041-1, se reduce a un valor eficaz ponderado a_w y VDV según ISO 2631-1, se combina en el valor total de vibración a_v, se normaliza a la exposición diaria A(8) y se evalúa frente al VAE y el VLE de la Directiva 2002/44/CE" style="width:94%">

## 1. Ponderaciones frecuenciales (ISO 8041-1)

Toda ponderación de vibración humana es el producto de cuatro etapas analógicas
evaluadas en $s = j\,2\pi f$ (ISO 8041-1, fórmulas (1)–(5)): un **paso-alto** y un
**paso-bajo** Butterworth de segundo orden que limitan la banda, una **transición
aceleración–velocidad** que porta la ganancia global $K$ y un **escalón
ascendente**:

$$
H(s) = H_h(s)\,H_l(s)\,H_t(s)\,H_s(s).
$$

Un único conjunto de parámetros de la Tabla 3 $(f_1, Q_1, f_2, Q_2, f_3, f_4,
Q_4, f_5, Q_5, f_6, Q_6, K)$ realiza las nueve ponderaciones — `Wb, Wc, Wd, We,
Wf, Wh, Wj, Wk, Wm` — colapsando su etapa a la unidad cuando un corte se fija en
infinito. La ponderación principal de cuerpo completo es `Wk` (vertical,
superficie del asiento); `Wd` es la ponderación horizontal y `Wh` la de
mano-brazo.

```python
import phonometry as ph

# La respuesta de ponderación global a cualquier frecuencia (ISO 8041-1, fórmula (5)).
resp = ph.frequency_weighting("Wk", [1.0, 6.3096, 20.0])
print(resp.magnitude.round(3))      # [0.482 1.054 0.636]  (factores)
print(resp.magnitude_db.round(2))   # [-6.33  0.46 -3.93]  (dB)
```

Los factores reproducen las tablas de objetivo de diseño del Anexo B de
ISO 8041-1 con sus cuatro cifras significativas: `Wk` presenta una meseta cerca
de −6 dB por debajo de 2 Hz, alcanza +0,46 dB cerca de 6,3 Hz y decae por encima.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/vibration_weighting_es.svg" alt="La ponderación vertical de cuerpo completo Wk en decibelios de 0,4 a 100 Hz: una meseta cerca de -6 dB por debajo de 2 Hz, un pequeño pico de +0,5 dB cerca de 6 Hz y una caída hasta cerca de -21 dB a 100 Hz" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/vibration_weighting_es_dark.svg" alt="La ponderación vertical de cuerpo completo Wk en decibelios de 0,4 a 100 Hz: una meseta cerca de -6 dB por debajo de 2 Hz, un pequeño pico de +0,5 dB cerca de 6 Hz y una caída hasta cerca de -21 dB a 100 Hz" style="width:88%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

result = ph.frequency_weighting("Wk", np.geomspace(0.4, 100.0, 240))

# En una línea:
result.plot()
plt.show()

# A mano, a partir de los campos del resultado, replicando lo que dibuja WeightingResponse.plot():
fig, ax = plt.subplots()
ax.semilogx(result.frequencies, result.magnitude_db, color="#1f77b4")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel("Factor de ponderación [dB]")
ax.set_title("Ponderación vertical de cuerpo completo Wk (ISO 8041-1)")
plt.show()
```

</details>

Para ponderar una señal temporal, `apply_weighting` aplica la respuesta compleja
exacta en el dominio de la frecuencia (de modo que coinciden magnitud *y* fase
con la norma), que luego consumen las métricas de dosis en el tiempo siguientes.

## 2. Aceleración ponderada y medidas de dosis (ISO 2631-1)

La evaluación básica es la **aceleración eficaz ponderada**. A partir de un
espectro de tercios de octava es (ISO 2631-1, ec. (9); la construcción idéntica
da la $a_{hw}$ de mano-brazo de ISO 5349-1, ec. (A.1)):

$$
a_w = \sqrt{\sum_i \left(W_i\,a_i\right)^2},
$$

con $W_i$ el factor de ponderación en el centro de banda $i$ y $a_i$ la
aceleración de banda medida. Los factores se evalúan exactamente en las
frecuencias que se pasan; tenga en cuenta que las tablas ISO (ISO 8041-1
Anexo B, ISO 2631-1 Tabla 3, ISO 5349-1 Tabla A.2) tabulan $W_i$ en los
centros de tercio de octava *verdaderos* $10^{n/10}$ Hz (6,31; 7,943; 15,85;
...), no en las etiquetas nominales de banda (6,3; 8; 16; ...): pase centros
verdaderos al comparar con los factores tabulados.

```python
import numpy as np
import phonometry as ph

# Un espectro vertical de asiento medido (eficaz por tercio de octava, m/s^2).
freqs = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 31.5, 63.0])
accel = np.array([0.20, 0.45, 0.42, 0.25, 0.12, 0.05, 0.02])

result = ph.weighted_acceleration(accel, freqs, "Wk")
print(round(result.overall, 3))          # 0.555  m/s^2 (a_w)
print(result.weighted.round(3))          # W_i * a_i por banda
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighted_acceleration_es.svg" alt="Un espectro de aceleración de asiento de vehículo medido (gris) y su contribución ponderada por Wk (azul) sobre los tercios de octava de 1 a 80 Hz: la ponderación atenúa las bandas bajas y altas pero deja el rango de 4 a 8 Hz casi inalterado, dando un valor eficaz ponderado a_w de aproximadamente 1,03 m/s^2" style="width:90%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighted_acceleration_es_dark.svg" alt="Un espectro de aceleración de asiento de vehículo medido (gris) y su contribución ponderada por Wk (azul) sobre los tercios de octava de 1 a 80 Hz: la ponderación atenúa las bandas bajas y altas pero deja el rango de 4 a 8 Hz casi inalterado, dando un valor eficaz ponderado a_w de aproximadamente 1,03 m/s^2" style="width:90%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

freqs = np.array([1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0, 10.0,
                  12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 63.0, 80.0])
accel = np.array([0.18, 0.24, 0.33, 0.46, 0.52, 0.55, 0.48, 0.39, 0.31, 0.26,
                  0.21, 0.17, 0.13, 0.10, 0.078, 0.060, 0.045, 0.028, 0.020])
result = ph.weighted_acceleration(accel, freqs, "Wk")

# En una línea:
result.plot()
plt.show()

# A mano, replicando lo que dibuja WeightedSpectrum.plot():
pos = np.arange(freqs.size)
fig, ax = plt.subplots()
ax.bar(pos - 0.2, result.band_accelerations, 0.4, color="#bbbbbb",
       label="Sin ponderar $a_i$")
ax.bar(pos + 0.2, result.weighted, 0.4, color="#1f77b4",
       label="Ponderada $W_i a_i$ (Wk)")
ax.set_xticks(pos)
ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax.set_xlabel("Frecuencia [Hz]")
ax.set_ylabel(r"Aceleración eficaz [m/s$^2$]")
ax.set_title(f"Aceleración ponderada ($a_w$ = {result.overall:.3f} m/s²)")
ax.legend()
plt.show()
```

</details>

Cuando el valor eficaz subestima una exposición intermitente o cargada de
choques, ISO 2631-1 añade medidas de dosis calculadas sobre la señal temporal
ponderada: el **valor eficaz móvil** y su máximo, el **valor máximo de vibración
transitoria** `MTVV` (ec. (4), un eficaz móvil de 1 s); el **valor de dosis de
vibración** de cuarta potencia $\text{VDV} = \left(\int a_w^4\,dt\right)^{1/4}$
(ec. (5)); el **valor de dosis de mareo** $\text{MSDV} = \left(\int a_w^2\,dt
\right)^{1/2}$; y el **factor de cresta** (pico / eficaz), cuyo valor por encima
de 9 indica que el método básico es inadecuado.

```python
import numpy as np
import phonometry as ph

fs = 1000.0
raw = np.random.default_rng(0).standard_normal(int(60 * fs))   # registro de 60 s
a_w = ph.apply_weighting(raw, fs, "Wk")                        # señal ponderada

print(round(ph.vibration_dose_value(a_w, fs), 3))   # 0.744  VDV [m/s^1.75]
print(round(ph.mtvv(a_w, fs), 3))                   # 0.265  MTVV [m/s^2]
print(round(ph.crest_factor(a_w), 2))               # 3.74   factor de cresta
```

## 3. Valor total de vibración y exposición diaria `A(8)`

Entre los tres ejes, el **valor total de vibración** combina las aceleraciones
eficaces ponderadas por eje con los factores multiplicadores de postura $k_j$
(ISO 2631-1, ec. (10); para mano-brazo, ISO 5349-1, ec. (1), con todo $k = 1$):

$$
a_v = \sqrt{\sum_j k_j^2\,a_{wj}^2}.
$$

```python
import phonometry as ph

# Salud, sentado: k = 1.4 / 1.4 / 1.0 (ISO 2631-1, 7.2.3).
a_v = ph.vibration_total_value([0.35, 0.28, 0.62], k=[1.4, 1.4, 1.0])
print(round(a_v, 3))     # 0.882  m/s^2
```

La **exposición diaria** normaliza el valor total a una jornada de referencia de
8 horas ($T_0 = 28\,800$ s). Para una sola operación $A(8) = a_v\,\sqrt{T/T_0}$;
varias operaciones se combinan mediante sus exposiciones parciales
$A_i(8) = a_{vi}\,\sqrt{T_i/T_0}$ como $A(8) = \sqrt{\sum_i A_i(8)^2}$ (ISO 5349-1,
ecs. (2)/(3); ISO 5349-2, ecs. (1)–(3)).

`daily_vibration_exposure` construye las exposiciones parciales, las combina y
evalúa el resultado frente a la **Directiva 2002/44/CE** — valor de acción de
mano-brazo `A(8) = 2.5` y valor límite `5` m/s²; acción de cuerpo completo `0.5`
y límite `1.15` m/s² (o un VDV de `9.1` / `21` m/s¹·⁷⁵):

```python
import phonometry as ph

# ISO 5349-2 Anexo E.3: las tres tareas con motosierra de un trabajador forestal.
result = ph.daily_vibration_exposure(
    total_values=[4.6, 6.0, 3.6],                 # a_hv por tarea, m/s^2
    durations_s=[2 * 3600, 1 * 3600, 2 * 3600],   # tiempo de exposición por tarea
    kind="hav",
    labels=["desbrozadora", "tala", "descortezado"],
)
print(result.partials.round(2))            # [2.3  2.12 1.8 ]  A_i(8)
print(round(result.a8, 2))                 # 3.61  m/s^2
print(result.assessment.zone)             # 'action'  (2.5 <= A(8) < 5.0)
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/daily_vibration_exposure_es.svg" alt="Un diagrama de barras de las tres exposiciones parciales de mano-brazo (cerca de 2,3, 2,1 y 1,8 m/s^2) y la A(8) combinada de 3,61 m/s^2, con el valor de acción de exposición de la Directiva 2002/44/CE en 2,5 y el valor límite de exposición en 5,0 m/s^2 marcados como líneas horizontales; la exposición diaria se sitúa en la zona de acción entre ambos" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/daily_vibration_exposure_es_dark.svg" alt="Un diagrama de barras de las tres exposiciones parciales de mano-brazo (cerca de 2,3, 2,1 y 1,8 m/s^2) y la A(8) combinada de 3,61 m/s^2, con el valor de acción de exposición de la Directiva 2002/44/CE en 2,5 y el valor límite de exposición en 5,0 m/s^2 marcados como líneas horizontales; la exposición diaria se sitúa en la zona de acción entre ambos" style="width:82%">

<details>
<summary>Ver el código de esta figura</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

result = ph.daily_vibration_exposure(
    [4.6, 6.0, 3.6], [2 * 3600, 1 * 3600, 2 * 3600], kind="hav",
    labels=["desbrozadora", "tala", "descortezado"],
)

# En una línea:
result.plot()
plt.show()

# A mano, replicando lo que dibuja DailyVibrationExposure.plot():
labels = [*result.labels, "A(8)"]
values = [*result.partials.tolist(), result.a8]
a = result.assessment
fig, ax = plt.subplots()
ax.bar(range(len(values)), values,
       color=["#bbbbbb"] * result.partials.size + ["#1f77b4"])
ax.axhline(a.action_value, color="#2ca02c", ls="--", label=f"VAE = {a.action_value:g}")
ax.axhline(a.limit_value, color="#d62728", ls="--", label=f"VLE = {a.limit_value:g}")
ax.set_xticks(range(len(values)))
ax.set_xticklabels(labels, rotation=30, ha="right")
ax.set_ylabel(r"Exposición diaria A(8) [m/s$^2$]")
ax.legend()
plt.show()
```

</details>

## 4. Orientación exposición–respuesta

Para la vibración transmitida a la mano, el Anexo C de ISO 5349-1 relaciona la
exposición diaria con la vida media de grupo $D_y$ (en años) que produce el dedo
blanco por vibración en el 10 % de un grupo expuesto, $D_y = 31{,}8\,A(8)^{-1{,}06}$
(ec. (C.1)):

```python
import phonometry as ph

print(round(ph.hav_vwf_lifetime_years(7.0), 1))   # 4.0 años (Tabla C.1)
```

Las normas no definen deliberadamente ningún límite seguro — `A(8)` y los valores
de acción y límite de la directiva son la base de cualquier criterio de
exposición. Para la exposición de cuerpo completo, `energy_equivalent_acceleration`
da la magnitud energético-equivalente de ISO 2631-1 ec. (B.3) entre periodos de
distinta magnitud y duración.

---

**Normas.** ISO 8041-1:2017 (definiciones de ponderación y tolerancias);
ISO 2631-1:1997 (evaluación de cuerpo completo); ISO 2631-2:2003 (edificios,
`Wm`); ISO 2631-4:2001 (confort de marcha ferroviaria, `Wb`); ISO 5349-1:2001 e
ISO 5349-2:2001 (vibración transmitida a la mano); Directiva 2002/44/CE (valores
de acción y límite de exposición).

## Véase también

- Referencia de la API: [`vibration.human_vibration`](/phonometry/es/reference/api/vibration/human-vibration/).

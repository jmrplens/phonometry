---
title: "Potencia sonora desde vibración (ISO/TS 7849)"
description: "La estimación según ISO/TS 7849 de la potencia sonora aérea a partir de la vibración superficial de una máquina: la potencia radiada P = Z_c⟨v²⟩Sε, el nivel de velocidad y su calibración, la media sobre la superficie, el factor de radiación ε y el nivel de potencia sonora L_W = L_v + 10 lg(S/S0) + 10 lg(ε) + 10 lg(411/400) — límite superior de la Parte 1 (ε=1) y valor de ingeniería de la Parte 2."
---

La potencia sonora aérea que una máquina radia a través de la vibración
estructural de su superficie exterior puede estimarse a partir de la velocidad
vibratoria de la superficie y un **factor de radiación** `ε` (la eficiencia de
radiación), sin una medición acústica. La potencia radiada es (ISO/TS 7849-1,
Fórmula 6)

$$
P = Z_c \, \langle v^2 \rangle \, S \, \varepsilon \quad [\mathrm{W}],
$$

con `Z_c` la impedancia característica del aire y `⟨v²⟩` la velocidad vibratoria
cuadrática media sobre el área radiante `S`. Expresada en niveles (nivel de
velocidad re `v₀ = 5·10⁻⁸ m/s`), el nivel de potencia sonora con ponderación A es
(Fórmula 12 / 15)

$$
L_W = L_v + 10\lg\frac{S}{S_0} + 10\lg\varepsilon
      + 10\lg\frac{Z_{c,n}}{Z_{c,0}},
$$

donde `S₀ = 1 m²`, la impedancia normalizada `Z_{c,n} = 411 N·s/m³` y la de
referencia `Z_{c,0} = 400 N·s/m³` dan el término fijo `10 lg(411/400) =
0,118 dB`. Este módulo alimenta las normas de fuente estructural y de predicción
en edificación (ISO 9611, EN 15657, EN 12354-5).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/vibration_sound_power_es.svg" alt="Nivel de potencia sonora radiada por banda de octava, comparando el límite superior de la ISO/TS 7849-1 (factor de radiación igual a uno) con el valor de ingeniería de la ISO/TS 7849-2 (factor de radiación medido)" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/vibration_sound_power_es_dark.svg" alt="Nivel de potencia sonora radiada por banda de octava, comparando el límite superior de la ISO/TS 7849-1 (factor de radiación igual a uno) con el valor de ingeniería de la ISO/TS 7849-2 (factor de radiación medido)" style="width:82%">

## 1. Las dos partes

Las dos partes difieren solo en el factor de radiación. La **Parte 1 (control)**
asume `ε = 1` y da el *límite superior* `L_W,max`, necesitando solo el nivel de
velocidad y el área. La **Parte 2 (ingeniería)** aplica un factor de radiación
por banda `εⱼ` determinado (según ISO 9614) como `εⱼ = Pⱼ/(Z_{c,n}·⟨vⱼ²⟩·S)`.

```python
import numpy as np
import phonometry as ph

bands = np.array([250.0, 500.0, 1000.0, 2000.0])
lv = np.array([82.0, 85.0, 83.0, 79.0])          # nivel de velocidad por banda [dB]

# Límite superior de la Parte 1 (epsilon = 1):
upper = ph.sound_power_from_vibration(lv, area=1.6, frequencies=bands)
print(round(upper.total_level, 1))               # p. ej. 89.4  dB re 1 pW

# Valor de ingeniería de la Parte 2 con un factor de radiación medido:
eps = np.array([0.45, 0.75, 0.95, 1.00])
eng = ph.sound_power_from_vibration(lv, area=1.6, radiation_factor=eps, frequencies=bands)
print(np.round(eng.sound_power_level, 1))        # L_W por banda
```

## 2. Nivel de velocidad, calibración y factor de radiación

El nivel de velocidad es `L_v = 20·lg(v/v₀)` (Fórmula 3); una aceleración de
calibración sinusoidal se convierte como `L_v = 20·lg(â/(2πf·v₀·√2))`
(Fórmula 8). El factor de radiación procede de una potencia medida de forma
independiente:

```python
import phonometry as ph

# El EJEMPLO de calibración de la norma: 9,81 m/s^2 a 100 Hz.
print(round(float(ph.velocity_level_from_acceleration(9.81, 100.0)), 1))   # 106.9 dB

# Factor de radiación desde una potencia medida (ISO 9614): eps = P / (Zc <v^2> S).
eps = ph.radiation_factor(3.0e-4, area=2.0, mean_square_velocity=(1e-3)**2)
print(round(float(eps), 3))                                                # 0.365
```

Los niveles de velocidad superficial de varias posiciones se combinan con la
media energética `mean_velocity_level` (Fórmula 10) o su forma ponderada por área
(Fórmula 11), y la corrección `extraneous_velocity_correction` elimina la
vibración extraña según la Tabla 2.

## 3. Cuándo se rompe la hipótesis del factor de radiación

Todo el método descansa en una sustitución: reemplazar la medición acústica
por `ε`. El valor `ε = 1` de la Parte 1 solo se acerca al factor de
radiación real por encima de la **frecuencia crítica (de coincidencia)** de
las partes tipo placa, donde las ondas de flexión viajan más rápido que el
sonido y la superficie radia como un pistón. Por debajo de la coincidencia,
zonas adyacentes de la placa se mueven en contrafase y su radiación se
cancela en gran medida: `ε` cae muy por debajo de uno y baja deprisa al bajar
la frecuencia, de modo que el método de control puede sobrestimar las bandas
graves de una carcasa grande y delgada en 10 dB o más. La misma cancelación hace que las fuentes pequeñas
radien mal (el cortocircuito acústico alrededor de un panel sin bafle). Otras
dos hipótesis son fáciles de violar en campo:

* **La vibración medida debe ser la de la propia máquina.** La vibración que
  entra desde la maquinaria vecina infla `⟨v²⟩`; la Tabla 2 prescribe la
  comprobación con la fuente parada y `extraneous_velocity_correction` la
  aplica.
* **La superficie debe ser el radiador dominante.** El sonido aéreo de
  aberturas, tomas o fuentes internas que esquiva la carcasa medida es
  invisible para una medición de velocidad; el método caracteriza solo la
  parte estructural.

La Parte 2 existe exactamente para el problema del factor de radiación:
sustituye el `ε = 1` fijo por un `εⱼ` banda a banda determinado a partir de una medición de
referencia de la potencia radiada (intensidad ISO 9614), tras lo cual la
medición de velocidad puede repetirse a bajo coste en máquinas nominalmente
idénticas.

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

bands = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
lv = np.array([78.0, 82.0, 85.0, 83.0, 79.0, 74.0])
eps = np.array([0.20, 0.45, 0.75, 0.95, 1.00, 1.00])
x = np.arange(bands.size)
plt.bar(x - 0.2, ph.radiated_sound_power_level(lv, 1.6), width=0.4, label="Parte 1 (ε=1)")
plt.bar(x + 0.2, ph.radiated_sound_power_level(lv, 1.6, radiation_factor=eps),
        width=0.4, label="Parte 2 (ε medido)")
plt.xticks(x, [f"{b:g}" for b in bands]); plt.legend()
plt.xlabel("Frecuencia [Hz]"); plt.ylabel("$L_W$ [dB re 1 pW]"); plt.show()
```

</details>

## Referencias

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3.ª ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  El tratamiento de la eficiencia de radiación tras la sección 3: la
  coincidencia, la cancelación por debajo de la frecuencia crítica y la
  radiación de placas finitas.
- International Organization for Standardization. (2009). *Acoustics —
  Determination of airborne sound power levels emitted by machinery using
  vibration measurement — Part 1: Survey method using a fixed radiation
  factor* (ISO/TS 7849-1:2009).
  [Catálogo iso.org](https://www.iso.org/standard/40537.html).
  El método de límite superior con `ε = 1`.
- International Organization for Standardization. (2009). *Acoustics —
  Determination of airborne sound power levels emitted by machinery using
  vibration measurement — Part 2: Engineering method including determination
  of the adequate radiation factor* (ISO/TS 7849-2:2009).
  [Catálogo iso.org](https://www.iso.org/standard/40538.html).
  El método de ingeniería con un factor de radiación medido por bandas.

---

**Normas.** ISO/TS 7849-1:2009 (*survey method using a fixed radiation factor*) e
ISO/TS 7849-2:2009 (*engineering method including determination of the adequate
radiation factor*), *Acoustics — Determination of airborne sound power levels
emitted by machinery using vibration measurement*: la potencia radiada
`P = Z_c⟨v²⟩Sε` (Fórmula 6), el nivel de velocidad y su calibración (Fórmulas 3,
8), la media sobre la superficie (Fórmulas 10/11), la corrección por vibración
extraña (Tabla 2), el factor de radiación (Fórmula 4/8) y el nivel de potencia
sonora (Fórmulas 12/15). La conformidad se ancla en el ejemplo de calibración de
la propia norma, el round-trip exacto entre el factor de radiación y
`L_W = 10 lg(P/P₀)`, y el término fijo de impedancia.

## Véase también

- Referencia de la API: [`emission.vibration_sound_power`](/phonometry/es/reference/api/power/vibration-sound-power/).

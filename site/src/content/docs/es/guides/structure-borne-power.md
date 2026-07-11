---
title: "Potencia sonora estructural de equipos (EN 15657)"
description: "El método de placa receptora de EN 15657:2018 para el nivel de potencia sonora estructural característica L_Ws de equipos de servicio del edificio: el nivel de velocidad medio espacial (Fórmula 12), el factor de pérdida de la placa η = 2,2/(f·Ts) (Fórmula 13) y L_Ws = 10 lg(2πfηmS) + L_v − 60 dB (Fórmula 14), en placas de baja y alta movilidad."
---

Los equipos de servicio del edificio —bombas, ventiladores, calderas, aparatos
sanitarios— inyectan **potencia sonora estructural** en la estructura del
edificio a la que están fijados, que luego se radia como ruido aéreo en los
recintos contiguos. La **EN 15657:2018** caracteriza tal fuente por su *nivel de
potencia sonora estructural característica* `L_Ws`, medido con el **método de la
placa receptora**: la fuente se monta sobre una placa de masa por unidad de
superficie `m` y área `S` conocidas, cuyo factor de pérdida estructural `η` se
conoce, y se mide la velocidad vibratoria media espacial de la placa. `L_Ws` (con
la movilidad de la placa) es el término de fuente de la predicción de equipos
instalados de EN 12354-5.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/structure_borne_power_es.svg" alt="Nivel de potencia sonora estructural característica por banda de tercio de octava determinado en una placa receptora de baja movilidad y otra de alta movilidad" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/structure_borne_power_es_dark.svg" alt="Nivel de potencia sonora estructural característica por banda de tercio de octava determinado en una placa receptora de baja movilidad y otra de alta movilidad" style="width:82%">

## 1. Las relaciones de la placa receptora

La potencia que disipa una placa resonante es `P = ω·η·(m·S)·⟨v²⟩`, de modo que
el nivel de potencia inyectada en bandas de tercio de octava es (Fórmula 14)

$$
L_{Ws} = 10\lg\!\left(\frac{2\pi f\,\eta\,m\,S}{f_0\,m_0\,S_0}\right)
         + L_v - 60 \;\;[\mathrm{dB\ re\ 1\ pW}],
$$

con las referencias `f₀ = 1 Hz`, `m₀ = 1 kg`, `S₀ = 1 m²`; el término `−60 dB` es
`10 lg(v₀²/P₀)` para la velocidad de referencia de EN 15657 `v₀ = 10⁻⁹ m/s`. La
velocidad de la placa es la media energética espacial sobre las `N` posiciones
(Fórmula 12) y el factor de pérdida procede del tiempo de reverberación
estructural `Ts` (Fórmula 13, idéntica al factor de pérdida total de ISO 10848):

$$
L_v = 10\lg\!\Big(\tfrac{1}{N}\textstyle\sum 10^{L_{v,i}/10}\Big), \qquad
\eta = \frac{2.2}{f\,T_s}.
$$

```python
import numpy as np
import phonometry as ph

bands = np.array([100.0, 200.0, 400.0, 800.0])
lv_i = np.array([88.0, 90.0, 87.0, 89.0, 86.0, 90.0])   # seis posiciones @ 200 Hz
print(round(ph.spatial_mean_velocity_level(lv_i), 2))    # 88.6 dB re 1 nm/s

# Nivel de potencia característica desde la placa receptora (η desde Ts):
res = ph.reception_plate_power(
    velocity_level=np.array([90.0, 87.0, 82.0, 77.0]),
    frequency=bands, mass_per_area=600.0, area=2.0, reverberation_time=0.8,
)
print(np.round(res.power_level, 1))     # L_Ws por banda
print(round(res.total_level, 1))        # nivel sumado en bandas [dB re 1 pW]
```

## 2. Placas de baja y alta movilidad

Dos placas receptoras acotan las condiciones de instalación. En la placa de
*baja movilidad* (pesada) la propia dinámica de la fuente apenas cambia la
movilidad puntual ni el factor de pérdida de la placa; la placa de *alta
movilidad* (ligera) se carga dinámicamente por la fuente, de modo que su tiempo
de reverberación y su movilidad se miden con la fuente fijada. El nivel de
potencia característica junto con la movilidad puntual de la placa (véase la
[movilidad mecánica](/phonometry/es/guides/mechanical-mobility/)) proporcionan la
descripción de la fuente para el modelo de EN 12354-5. El homólogo directo del
lado de la fuente es el nivel de velocidad libre de ISO 9611 (re `5·10⁻⁸ m/s`)
medido en los puntos de contacto de maquinaria montada elásticamente.

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

bands = np.array([50.0, 100.0, 200.0, 400.0, 800.0, 1600.0, 3150.0])
lv_low = np.array([88.0, 90.0, 87.0, 84.0, 80.0, 76.0, 71.0])
low = ph.reception_plate_power(lv_low, bands, mass_per_area=600.0, area=2.0,
                               reverberation_time=0.8)
high = ph.reception_plate_power(lv_low + 6.0, bands, mass_per_area=150.0, area=2.0,
                                reverberation_time=0.5)
x = np.arange(bands.size)
plt.bar(x - 0.2, low.power_level, width=0.4, label="placa de baja movilidad")
plt.bar(x + 0.2, high.power_level, width=0.4, label="placa de alta movilidad")
plt.xticks(x, [f"{b:g}" for b in bands]); plt.legend()
plt.xlabel("Frecuencia [Hz]"); plt.ylabel("$L_{Ws}$ [dB re 1 pW]"); plt.show()
```

</details>

---

**Normas.** EN 15657:2018, *Acoustic properties of building elements and
buildings — Laboratory measurement of structure-borne sound from building
service equipment for all installation conditions*: el método de la placa
receptora (cláusula 7), el nivel de velocidad medio espacial (Fórmula 12), el
factor de pérdida de la placa `η = 2,2/(f·Ts)` (Fórmula 13) y el nivel de
potencia sonora estructural característica `L_Ws` (Fórmula 14). Los niveles de
velocidad de la placa se refieren a `v₀ = 10⁻⁹ m/s`. La conformidad se ancla en
el balance de potencia de la placa resonante `P = ω·η·(m·S)·⟨v²⟩` (del cual la
Fórmula 14 es el nivel) y en la identidad del factor de pérdida.

---
title: "Materiales acústicos"
description: "Caracterización de absorbentes y particiones en laboratorio: la valoración ponderada de absorción sonora alpha_w de ISO 11654 y su clase, la resistencia y resistividad al flujo de aire de ISO 9053-1/-2, y la impedancia superficial, la absorción y la pérdida por transmisión en tubo de impedancia de ISO 10534-1/-2 y ASTM E2611."
---

Caracterizar un absorbente o una partición es un ejercicio de laboratorio con
tres instrumentos distintos detrás. La **cámara reverberante** entrega un espectro
de coeficientes de absorción sonora que ISO 11654 condensa en un único número
valorado $\alpha_w$ con una clase por letra. El **banco de flujo** —estacionario
u oscilante— mide cuánto cuesta empujar aire a través de una muestra porosa, la
resistencia al flujo de aire que gobierna su comportamiento a baja frecuencia
(ISO 9053-1/-2). Y el **tubo de impedancia** recupera, a incidencia normal, la
impedancia superficial compleja completa, el factor de reflexión y la absorción
de una muestra pequeña, y —con cuatro micrófonos— su pérdida por transmisión
(ISO 10534-1/-2, ASTM E2611). Esta página cubre las tres.

## 1. Valoración de la absorción sonora (ISO 11654)

ISO 354 mide el coeficiente de absorción sonora $\alpha_s$ de un material en
bandas de tercio de octava en una cámara reverberante. ISO 11654:1997 convierte
ese espectro en una valoración de número único comparable entre productos.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso11654_es.svg" alt="Flujo de valoración ISO 11654: el alpha_s medido pasa a alpha_p práctico por banda de octava, la curva de referencia se desplaza hasta el mejor ajuste, alpha_w se lee a 500 Hz con indicadores de forma, dando la clase de absorción A a E" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_iso11654_es_dark.svg" alt="Flujo de valoración ISO 11654: el alpha_s medido pasa a alpha_p práctico por banda de octava, la curva de referencia se desplaza hasta el mejor ajuste, alpha_w se lee a 500 Hz con indicadores de forma, dando la clase de absorción A a E" style="width:82%">

**Coeficiente de absorción práctico (cláusula 4.1).** Los datos de tercio de
octava se agrupan primero en bandas de octava, cada una la media aritmética de
sus tres tercios:

$$
\alpha_{p,i} = \tfrac{1}{3}\big(\alpha_{i1} + \alpha_{i2} + \alpha_{i3}\big),
$$

evaluado al segundo decimal y luego redondeado en pasos de $0{,}05$ (la NOTA de la
cláusula 4.1 fija el redondeo, p. ej. $0{,}92 \to 0{,}90$); las medias redondeadas
por encima de $1{,}00$ se fijan en $1{,}00$. Las cinco bandas de valoración son 250,
500, 1000, 2000 y 4000 Hz.

**Absorción ponderada (cláusula 4.2).** Una curva de referencia fija
$\{250{:}\,0{,}80,\ 500{:}\,1{,}00,\ 1000{:}\,1{,}00,\ 2000{:}\,1{,}00,\ 4000{:}\,0{,}90\}$
se desplaza hacia abajo, hacia el $\alpha_p$ medido, en pasos de $0{,}05$ hasta que
la suma de las desviaciones **desfavorables** —tomadas solo donde la medida
queda por debajo de la curva desplazada, con magnitud
$(\text{curva} - \text{medida})$— no supera $0{,}10$. El coeficiente ponderado
$\alpha_w$ es el valor de la curva desplazada leído a 500 Hz.

**Indicadores de forma (cláusula 4.3).** Cuando un coeficiente práctico supera la
curva desplazada en $0{,}25$ o más, se añade un indicador de forma: `L` a 250 Hz,
`M` a 500 o 1000 Hz, `H` a 2000 o 4000 Hz (p. ej. `0.60(M)`).

**Clase de absorción (Tabla B.1).** Por último, $\alpha_w$ se asigna a una clase:
A (0,90–1,00), B (0,80–0,85), C (0,60–0,75), D (0,30–0,55), E (0,15–0,25) o "no
clasificado" (0,00–0,10). Como $\alpha_w$ es siempre un múltiplo de $0{,}05$, estos
rangos particionan la rejilla de forma exacta.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_rating_es.svg" alt="Valoración ponderada de absorción sonora de ISO 11654: el espectro de absorción práctica trazado frente a la curva de referencia desplazada de 250 Hz a 4000 Hz, con la desviación desfavorable a 250 Hz sombreada y el coeficiente ponderado alpha_w leído a 500 Hz" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_rating_es_dark.svg" alt="Valoración ponderada de absorción sonora de ISO 11654: el espectro de absorción práctica trazado frente a la curva de referencia desplazada de 250 Hz a 4000 Hz, con la desviación desfavorable a 250 Hz sombreada y el coeficiente ponderado alpha_w leído a 500 Hz" style="width:80%">

*El ejemplo resuelto del Anexo A.2: la curva de referencia se desplaza hacia
abajo 0,40 hasta que las desviaciones desfavorables suman 0,05 (≤ 0,10), dando
$\alpha_w = 0{,}60$; el pico de 500 Hz sobrepasa la curva desplazada en ≥ 0,25,
añadiendo el indicador `M`, de modo que la valoración es $0{,}60(\text{M})$, clase
C.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
from phonometry import weighted_absorption

# Coeficientes prácticos del Anexo A.2 de ISO 11654 a 250/500/1000/2000/4000 Hz
result = weighted_absorption([0.35, 1.00, 0.65, 0.60, 0.55])
result.plot()   # curva práctica frente a la referencia desplazada
plt.show()
```

</details>

```python
from phonometry import weighted_absorption, absorption_class

# Coeficientes prácticos del Anexo A.2 de ISO 11654 a 250/500/1000/2000/4000 Hz
alpha_p = [0.35, 1.00, 0.65, 0.60, 0.55]

result = weighted_absorption(alpha_p)
print(result.rating_label)          # 0.60(M)
print(result.alpha_w)               # 0.6
print(result.absorption_class)      # C
print(round(result.unfavourable_sum, 2))  # 0.05

# Un alpha_w a secas también se asigna directamente a su clase (Tabla B.1)
print(absorption_class(0.85))       # B
```

`weighted_absorption` acepta los cinco valores de $\alpha_p$ por banda de octava
(como una secuencia o un mapeo `{frecuencia: valor}`); pasa antes los quince
valores de $\alpha_s$ de tercio de octava a `practical_absorption_coefficient`
si partes de datos brutos de ISO 354. El resultado lleva la curva de referencia
desplazada y las desviaciones por banda, y su `.plot()` genera la figura de
arriba.

## 2. Resistencia al flujo de aire (ISO 9053-1/-2)

La resistencia al flujo de aire cuantifica con qué fuerza un material poroso se
opone a un flujo estacionario o lentamente oscilante. Ambas partes comparten las
mismas tres magnitudes y unidades (ISO 9053-1:2018, cláusula 3):

$$
R = \frac{\Delta p}{q_v}\ \left[\text{Pa·s/m}^3\right], \qquad
R_s = R\,A\ \left[\text{Pa·s/m}\right], \qquad
\sigma = \frac{R_s}{d}\ \left[\text{Pa·s/m}^2\right],
$$

con $\Delta p$ la diferencia de presión a través de la probeta, $q_v$ el flujo
volumétrico, $A$ la sección transversal y $d$ el espesor. Nótese que la
resistencia específica al flujo de aire $R_s$ está en **Pa·s/m** (no Pa·s/m²); la
resistividad al flujo de aire $\sigma$ es $R_s$ por metro de espesor.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_airflow_resistance_es.svg" alt="Bancos de medición de la resistencia al flujo de aire: el método estático de ISO 9053-1 con una probeta en un portamuestras, un flujo laminar estacionario q_v y un manómetro diferencial que lee la caída de presión; y el método alterno de ISO 9053-2 con un pistón oscilante que acciona una cavidad terminada por la probeta o por un tapón hermético, y un micrófono que lee el nivel de la cavidad" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_airflow_resistance_es_dark.svg" alt="Bancos de medición de la resistencia al flujo de aire: el método estático de ISO 9053-1 con una probeta en un portamuestras, un flujo laminar estacionario q_v y un manómetro diferencial que lee la caída de presión; y el método alterno de ISO 9053-2 con un pistón oscilante que acciona una cavidad terminada por la probeta o por un tapón hermético, y un micrófono que lee el nivel de la cavidad" style="width:92%">

**Método estático (ISO 9053-1:2018).** Un flujo laminar estacionario se aumenta
por escalones y la diferencia de presión se traza frente a la velocidad lineal
$u = q_v/A$. Se ajusta una regresión de al menos segundo orden **forzada a pasar
por el origen**, $\Delta p = a\,u + b\,u^2$, y $\Delta p$ y $R_s$ se leen a la
velocidad de referencia $u = 0{,}5\ \text{mm/s}$ (cláusula 7.5); la velocidad más
alta no debe superar los 15 mm/s. Como $R_s = \Delta p/u = a + b\,u$, el término
lineal $a$ es la resistencia específica al flujo de aire a velocidad nula.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airflow_resistance_es.svg" alt="Resistencia al flujo de aire por el método estático de ISO 9053-1: la caída de presión medida frente a la velocidad lineal del flujo, ajustada con una cuadrática que pasa por el origen, con la resistencia específica al flujo de aire evaluada a la velocidad de referencia de 0,5 mm/s" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/airflow_resistance_es_dark.svg" alt="Resistencia al flujo de aire por el método estático de ISO 9053-1: la caída de presión medida frente a la velocidad lineal del flujo, ajustada con una cuadrática que pasa por el origen, con la resistencia específica al flujo de aire evaluada a la velocidad de referencia de 0,5 mm/s" style="width:80%">

*La caída de presión, ligeramente superlineal, se ajusta pasando por el origen;
la resistencia específica al flujo de aire es el ajuste leído a 0,5 mm/s.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import static_airflow_resistance

area = np.pi * 0.05**2                      # celda de 100 mm de diámetro [m^2]
u = np.array([0.5, 1, 2, 4, 8, 12]) * 1e-3  # velocidad lineal [m/s]
dp = 1.6e4 * u + 4.0e5 * u**2               # caída de presión medida [Pa]
r = static_airflow_resistance(u, dp, area=area, thickness=0.05)

u_fit = np.linspace(0.0, 13e-3, 200)
dp_fit = r.linear_coefficient * u_fit + r.quadratic_coefficient * u_fit**2
fig, ax = plt.subplots()
ax.plot(u_fit * 1e3, dp_fit, label="Ajuste por el origen  dp = a u + b u^2")
ax.plot(u * 1e3, dp, "o", label="Caída de presión medida")
ax.plot(r.evaluation_velocity * 1e3, r.pressure_drop, "D",
        label="Evaluación a 0.5 mm/s")
ax.set_xlabel("Velocidad lineal del flujo u [mm/s]")
ax.set_ylabel("Caída de presión dp [Pa]")
ax.set_title(f"R_s = {r.specific_resistance:.0f} Pa·s/m")
ax.legend()
plt.show()
```

</details>

```python
import numpy as np
from phonometry import static_airflow_resistance

area = np.pi * 0.05**2            # celda de 100 mm de diámetro [m^2]
u = np.array([0.5, 1, 2, 4, 8, 12]) * 1e-3      # velocidad lineal [m/s]
dp = 1.6e4 * u + 4.0e5 * u**2                    # caída de presión medida [Pa]

r = static_airflow_resistance(u, dp, area=area, thickness=0.05)
print(round(r.specific_resistance))   # 16200   R_s [Pa*s/m]
print(round(r.resistivity))           # 324000  sigma [Pa*s/m^2]
print(round(r.linear_coefficient))    # 16000   a = R_s cuando u -> 0
```

**Método alterno (ISO 9053-2:2020).** Un pistón que oscila a 1–4 Hz acciona un
flujo alterno hacia una cavidad terminada por la probeta o por un tapón
hermético; la resistencia se obtiene de la diferencia de nivel de presión sonora
entre las dos terminaciones (Fórmula (2)):

$$
R = \frac{\kappa'\,P_S}{2\pi f\,V}\cdot\frac{h_t}{h_s}\cdot
    10^{(L_{p,s} - L_{p,t})/20},
$$

donde $\kappa'$ es la razón **efectiva** de calores específicos. La conducción de
calor entre el aire oscilante y las paredes de la cavidad hace que la compresión
no sea plenamente adiabática; el Anexo A normativo corrige $\kappa$ a la baja
hasta

$$
\kappa' = \frac{\kappa}{\sqrt{1 + (\kappa-1)\tfrac{S}{V}b
          + \tfrac{1}{2}\big((\kappa-1)\tfrac{S}{V}b\big)^2}},
\qquad b = \sqrt{\frac{2 c_0 l_h}{\omega}},\quad
l_h = \frac{k_a}{\rho_0 c_0 C_P},
$$

con $S$ y $V$ la superficie y el volumen de la cavidad y $b$ el espesor de la
capa límite térmica. Para la cavidad de ejemplo del Anexo A.3 esto da
$\kappa' = 1{,}370$, cerca de un 2 % por debajo del adiabático 1,4008.

```python
from phonometry import effective_kappa, alternating_airflow_resistance

# Cavidad del Anexo A.3: cilindro cerrado de 100 mm x 100 mm, pistón a 2 Hz
kp = effective_kappa(cavity_surface=0.0471, cavity_volume=7.854e-4, frequency=2.0)
print(round(kp, 3))               # 1.37   razón efectiva de calores específicos

R = alternating_airflow_resistance(
    level_specimen=74.0, level_termination=90.0,
    piston_stroke_specimen=14e-3, piston_stroke_termination=1.4e-3,
    frequency=2.0, cavity_volume=7.854e-4, kappa_prime=kp,
)
print(round(R))                   # 222956  resistencia al flujo de aire R [Pa*s/m^3]
```

Pasa el resultado de `effective_kappa` a `alternating_airflow_resistance` para
una cifra conforme al Anexo A; en caso contrario, su argumento `kappa_prime`
adopta por defecto el adiabático sin corregir 1,4. La llamada avisa (mediante
`AirflowResistanceWarning`) cuando la frecuencia del pistón sale de 1–4 Hz o
fallan los criterios de validez de las Fórmulas (3)/(4).

## 3. Tubo de impedancia (ISO 10534-1/-2, ASTM E2611)

El tubo de impedancia mide una muestra pequeña a **incidencia normal**. Dos
normas comparten la geometría pero difieren en método y convención de signo, así
que la biblioteca mantiene sus ayudantes separados y nunca los mezcla.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impedance_tube_es.svg" alt="Tubo de impedancia de dos micrófonos de ISO 10534-2: un altavoz radiando una onda plana por el tubo, dos micrófonos enrasados en la pared a la separación s y a la distancia x1 de la cara de la probeta, la probeta de ensayo contra un respaldo rígido, y las ondas incidente y reflejada" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_impedance_tube_es_dark.svg" alt="Tubo de impedancia de dos micrófonos de ISO 10534-2: un altavoz radiando una onda plana por el tubo, dos micrófonos enrasados en la pared a la separación s y a la distancia x1 de la cara de la probeta, la probeta de ensayo contra un respaldo rígido, y las ondas incidente y reflejada" style="width:92%">

**Rango de frecuencia de trabajo (ISO 10534-2, cláusula 4).** Todo lo que
informa el tubo supone que el campo interior es una única onda plana, y la
geometría fija los dos extremos de la banda útil. Por encima del corte del
primer modo transversal el campo deja de ser plano: un tubo circular de
diámetro $d$ exige $f\,d < 0{,}58\,c_0$ (Ec. (2); $f\,d < 0{,}50\,c_0$ para un
tubo rectangular, Ec. (3)). La separación de micrófonos $s$ debe además
mantenerse lejos de la singularidad de media longitud de onda del método de la
función de transferencia, $f\,s < 0{,}45\,c_0$ (Ec. (4)). En el extremo bajo
aparece el problema opuesto: una separación mucho menor que la longitud de
onda apenas deja diferencia de fase entre micrófonos que medir, así que la
pauta de la cláusula 4.2 mantiene la separación por encima del 5 % de la
longitud de onda:

$$
\frac{c_0}{20\,s} \;<\; f \;<\;
\min\!\left(0{,}58\,\frac{c_0}{d},\ 0{,}45\,\frac{c_0}{s}\right).
$$

Ningún tubo cubre por sí solo el rango de la acústica de edificios. Un tubo de
100 mm con separación de 100 mm trabaja aproximadamente de 170 Hz a 1,5 kHz;
llegar a las bandas de 5 kHz exige un tubo pequeño (29 mm) con separación
corta, que a su vez no ve las bandas bajas. Los laboratorios emparejan por eso
un tubo grande y uno pequeño (o un tubo con dos separaciones) y empalman los
espectros; ambos deben coincidir en las bandas de solape, y una discrepancia
ahí apunta al corte o al montaje de la muestra, no a la física.

```python
from phonometry import plane_wave_frequency_range

# Un tubo de 100 mm con separación de 100 mm y uno de 29 mm con 20 mm.
f_l, f_u = plane_wave_frequency_range(0.100, 343.2, diameter=0.100)
print(round(f_l, 1), round(f_u, 1))     # 171.6 1544.4
f_l, f_u = plane_wave_frequency_range(0.020, 343.2, diameter=0.029)
print(round(f_l, 1), round(f_u, 1))     # 858.0 6864.0
```

**Método de la razón de onda estacionaria (ISO 10534-1).** Una sonda recorre la
onda estacionaria y lee la diferencia de nivel $\Delta L = L_\text{max} -
L_\text{min}$ entre un máximo de presión y el mínimo adyacente. La razón de onda
estacionaria, la magnitud de reflexión y la absorción se obtienen en forma
cerrada:

$$
s = 10^{\Delta L/20}, \qquad |r| = \frac{s-1}{s+1}, \qquad
\alpha = 1 - |r|^2.
$$

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impedance_tube_es.svg" alt="Método de la razón de onda estacionaria de ISO 10534-1: el coeficiente de absorción y la magnitud del factor de reflexión en función de la diferencia de nivel de la onda estacionaria, mostrando que una diferencia de 9,54 dB corresponde a una razón de onda estacionaria de 3, una magnitud de reflexión de 0,5 y una absorción de 0,75" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/impedance_tube_es_dark.svg" alt="Método de la razón de onda estacionaria de ISO 10534-1: el coeficiente de absorción y la magnitud del factor de reflexión en función de la diferencia de nivel de la onda estacionaria, mostrando que una diferencia de 9,54 dB corresponde a una razón de onda estacionaria de 3, una magnitud de reflexión de 0,5 y una absorción de 0,75" style="width:80%">

*Una diferencia de nivel pequeña significa un absorbente casi perfecto; una
diferencia de nivel de 9,54 dB da $s = 3$, $|r| = 0{,}5$ y $\alpha = 0{,}75$.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import (
    standing_wave_absorption, standing_wave_ratio_from_level,
    standing_wave_reflection_magnitude,
)

level_diff = np.linspace(0.5, 40.0, 300)    # L_max - L_min [dB]
swr = standing_wave_ratio_from_level(level_diff)
fig, ax = plt.subplots()
ax.plot(level_diff, standing_wave_absorption(swr),
        label="Coeficiente de absorción alpha")
ax.plot(level_diff, standing_wave_reflection_magnitude(swr), "--",
        label="Magnitud del factor de reflexión |r|")
ax.set_xlabel("Diferencia de nivel de onda estacionaria L_max - L_min [dB]")
ax.set_ylabel("alpha, |r|")
ax.legend()
plt.show()
```

</details>

```python
from phonometry import standing_wave_absorption, standing_wave_ratio_from_level

s = float(standing_wave_ratio_from_level(9.542))   # diferencia de nivel [dB] -> SWR
print(round(s, 2))                                  # 3.0
print(round(float(standing_wave_absorption(s)), 2)) # 0.75
```

**Método de la función de transferencia (ISO 10534-2).** Dos micrófonos fijos
miden la función de transferencia compleja $H_{12}$; de ella se obtienen el
factor de reflexión en la cara de la muestra, la absorción y la impedancia
superficial normalizada (ecs. (17)–(19)):

$$
r = \frac{H_{12} - H_I}{H_R - H_{12}}\,e^{\,2 j k_0 x_1}, \qquad
\alpha = 1 - |r|^2, \qquad \frac{Z}{\rho c_0} = \frac{1+r}{1-r},
$$

con $H_I = e^{-j k_0 s}$, $H_R = e^{+j k_0 s}$, la separación de micrófonos $s$ y
$x_1$ la distancia de la muestra al micrófono más lejano.

<video class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_standing_wave_tube_es.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_standing_wave_tube_es_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: las ondas incidente y reflejada se suman en una onda estacionaria dentro del tubo de impedancia; una terminación rígida da nodos profundos en la envolvente, una muestra porosa los da poco profundos, muestreados por los dos micrófonos de pared" style="width:88%"></video><video class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_standing_wave_tube_es_dark.webm" preload="none" poster="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_standing_wave_tube_es_dark_poster.jpg" width="2400" height="1350" loop muted controls playsinline title="Animación: las ondas incidente y reflejada se suman en una onda estacionaria dentro del tubo de impedancia; una terminación rígida da nodos profundos en la envolvente, una muestra porosa los da poco profundos, muestreados por los dos micrófonos de pared" style="width:88%"></video>

```python
import numpy as np
from phonometry import (
    tube_wavenumber, reflection_factor,
    absorption_from_reflection, normalized_surface_impedance,
)

f = np.array([500.0, 1000.0, 1800.0])
x1, spacing, c0 = 0.12, 0.03, 343.2
k0 = tube_wavenumber(f, c0)

# Una función de transferencia H12 medida (aquí sintetizada a partir de r = 0.3 - 0.4j)
target = 0.3 - 0.4j
x2 = x1 - spacing
h12 = (np.exp(1j*k0*x2) + target*np.exp(-1j*k0*x2)) / \
      (np.exp(1j*k0*x1) + target*np.exp(-1j*k0*x1))

r = reflection_factor(h12, spacing=spacing, x1=x1, wavenumber=k0)
print(np.round(absorption_from_reflection(r), 3))     # [0.75 0.75 0.75]
print(np.round(normalized_surface_impedance(r), 2))   # Z / rho c0
# [1.15-1.23j 1.15-1.23j 1.15-1.23j]
```

El `two_microphone_impedance` de alto nivel envuelve esta cadena y devuelve un
`ImpedanceTubeResult` con la absorción, el factor de reflexión, la impedancia
superficial y la impedancia normalizada, aplicando la comprobación del rango de
frecuencias de onda plana y la atenuación opcional del tubo; corrige antes
cualquier desajuste de micrófonos con `apply_mic_calibration`. Su `.plot()`
dibuja el espectro de absorción $\alpha(f)$ con el módulo del factor de
reflexión $|r|$ superpuesto.

**Pérdida por transmisión (ASTM E2611).** Con cuatro micrófonos —dos aguas
arriba, dos aguas abajo de la muestra— una medición de dos cargas (o de una
carga) recupera la matriz de transferencia de la muestra, cuyos elementos dan la
pérdida por transmisión a incidencia normal, la reflexión y el número de onda:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_astm_tube_es.svg" alt="Tubo de pérdida por transmisión de cuatro micrófonos de ASTM E2611: una fuente sonora, dos micrófonos aguas arriba y dos aguas abajo de la probeta de ensayo a las separaciones s1 y s2 y los desplazamientos l1 y l2, una terminación ajustable para el método de dos cargas, las ondas viajeras A y B aguas arriba y C y D aguas abajo, y las relaciones de matriz de transferencia y pérdida por transmisión" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_astm_tube_es_dark.svg" alt="Tubo de pérdida por transmisión de cuatro micrófonos de ASTM E2611: una fuente sonora, dos micrófonos aguas arriba y dos aguas abajo de la probeta de ensayo a las separaciones s1 y s2 y los desplazamientos l1 y l2, una terminación ajustable para el método de dos cargas, las ondas viajeras A y B aguas arriba y C y D aguas abajo, y las relaciones de matriz de transferencia y pérdida por transmisión" style="width:92%">

$$
\mathrm{TL} = 20\log_{10}\left|\frac{T_{11} + T_{12}/\rho c
             + \rho c\,T_{21} + T_{22}}{2}\right|.
$$

```python
import numpy as np
from phonometry import air_layer_transfer_matrix

# Una capa de aire es una matriz de transferencia conocida; TL = 0 dB (no se pierde nada)
f = np.array([500.0, 1000.0, 2000.0])
k0 = 2*np.pi*f / 343.2
rho_c = 1.186 * 343.2
tm = air_layer_transfer_matrix(thickness=0.05, wavenumber=k0,
                               characteristic_impedance=rho_c)
print(np.round(tm.transmission_loss(rho_c), 6))   # [0. 0. 0.]
```

`transfer_matrix_two_load` / `transfer_matrix_one_load` construyen la
`TransferMatrix` a partir de las funciones de transferencia de los cuatro
micrófonos `(H1, H2, H3, H4)` medidas en cada carga; sus métodos
(`transmission_loss`, `reflection_hard_backed`,
`absorption_hard_backed`, `characteristic_impedance_material`,
`material_wavenumber`) leen entonces las magnitudes de ASTM E2611.

**Errores de montaje.** La mayoría de los malos datos de tubo se fabrican en
el portamuestras, mucho antes del procesado de señal. Los fallos recurrentes:

- **Holguras perimetrales.** Una probeta cortada ligeramente pequeña deja una
  lámina de aire junto a la pared del tubo. El sonido se cortocircuita
  alrededor y por detrás de la muestra, y la propia holgura resuena, de modo
  que la absorción medida gana una joroba espuria de baja a media frecuencia.
  Corte con ajuste deslizante ceñido y selle el borde (una película fina de
  vaselina es el remedio clásico) sin cargar la cara frontal.
- **Compresión.** Una probeta cortada grande y embutida a la fuerza es más
  densa que el producto que debe representar: la resistividad al flujo sube,
  un esqueleto flexible se rigidiza, y la curva de absorción se desplaza y se
  aplana. El resultado es repetible y erróneo.
- **Cavidad trasera oculta.** Si la probeta no asienta a ras del respaldo
  rígido, la capa de aire involuntaria actúa como cavidad de cuarto de
  longitud de onda y desplaza el pico de absorción hacia abajo en frecuencia,
  favoreciendo al material. Las cámaras de aire traseras son montajes
  perfectamente legítimos, pero solo cuando son deliberadas, dimensionadas y
  declaradas con el resultado.
- **Cara no plana.** Una cara frontal abombada, inclinada o desgarrada
  dispersa hacia modos transversales por debajo del corte nominal y rompe la
  hipótesis de incidencia normal sobre la que descansan las ecuaciones. Corte
  con herramienta afilada; no rasgue los materiales fibrosos a medida.
- **Una probeta no es el material.** Los productos porosos son inhomogéneos a
  la escala de una muestra de tubo. Mida varios cortes y promedie; la
  dispersión entre probetas es varianza del producto que merece declararse,
  no ruido de medida que esconder.

## ¿Tubo o cámara reverberante?

El tubo y la cámara reverberante entregan ambos un número llamado "coeficiente
de absorción", y los dos se confunden de forma rutinaria. Son magnitudes
físicas distintas, medidas bajo campos sonoros distintos, y no coinciden, a
veces ni de lejos.

El tubo mide un coeficiente a **incidencia normal**: una onda plana, un
ángulo, una probeta de unos centímetros y un factor de reflexión complejo que
conserva módulo y fase. ISO 354 mide el coeficiente de **incidencia
aleatoria** $\alpha_s$: un campo difuso que golpea una muestra de 10 a 12 m²
desde todas las direcciones a la vez, recuperado del cambio del tiempo de
caída de la cámara mediante la fórmula de Sabine, un promedio de energía sin
fase alguna. Como el campo difuso encuentra más caminos hacia el interior del
absorbente que la única onda a incidencia normal (las ondas oblicuas recorren
más camino dentro de la capa), $\alpha_s$ suele salir más alto. Para una
superficie de reacción local ambos se conectan mediante el promedio angular
de Paris, que define el coeficiente de absorción estadístico

$$
\alpha_{st} = \int_0^{\pi/2} \alpha(\theta)\,\sin 2\theta\,\mathrm{d}\theta,
$$

una integral que pondera sobre todo los ángulos oblicuos; evaluarla exige el
$\alpha(\theta)$ dependiente del ángulo a partir de la impedancia superficial
medida, no solo el propio coeficiente a incidencia normal.

**Por qué los valores de ISO 354 superan 1.** Un cociente de energía absorbida
sobre incidente no puede superar la unidad y, sin embargo, los informes de
cámara reverberante con $\alpha_s = 1{,}05$ a $1{,}20$ para absorbentes
porosos gruesos son rutinarios y correctos según el método. La fórmula de
Sabine convierte el cambio del tiempo de caída en un área de absorción
equivalente $A$, y $\alpha_s = A/S$ divide por el área *geométrica* de la
muestra $S$. La difracción en los bordes de la muestra permite a la probeta
drenar energía de un campo sonoro más ancho que su huella (el efecto de
borde), de modo que el área equivalente puede superar la geométrica. Esos
valores no son errores, pero tampoco son portables: dependen del tamaño y del
perímetro de la muestra, que es exactamente la razón por la que ISO 354 fija
ambos. La valoración de ISO 11654 simplemente trunca: los coeficientes
prácticos por encima de $1{,}00$ se fijan en $1{,}00$ (sección 1). Las
entradas de predicción no reciben ese recorte silencioso en esta biblioteca:
cada
[estimador del tiempo de reverberación](/phonometry/es/guides/reverberation-prediction/)
aplica su propio dominio matemático, de modo que Sabine y Eyring aceptan los
valores de ISO 354 iguales o superiores a uno tal cual (Eyring siempre que la
absorción media quede por debajo de uno), mientras que Millington-Sette los
rechaza (su logaritmo por superficie diverge en uno) y cualquier ajuste por
debajo de uno queda en manos de quien llama. El presupuesto de área de
absorción equivalente de
[EN 12354-6](/phonometry/es/guides/enclosed-space-absorption/) también acepta
los coeficientes tal cual se suministran.

**Cuál usar.** Responden a preguntas distintas. El valor de cámara
reverberante es el que alimenta la predicción en campo difuso: las
estimaciones de reverberación de Sabine, las áreas de absorción equivalentes
de [EN 12354-6](/phonometry/es/guides/enclosed-space-absorption/) y la
valoración $\alpha_w$ con su clase, todas las cuales esperan incidencia
aleatoria sobre una muestra finita y montada (los tipos de montaje del Anexo B
de ISO 354 existen porque el montaje es parte del resultado). El valor de tubo
es la herramienta de laboratorio y desarrollo: necesita solo unos centímetros
cuadrados de material, resuelve módulo *y* fase, y su impedancia superficial
fija los parámetros de los modelos de material poroso de la tradición de
Allard y Atalla, con la resistividad al flujo de la sección 2 como primera
entrada; el modelo ajustado predice después la capa a cualquier ángulo,
espesor o respaldo. Lo que el número del tubo *no* es, es un sustituto directo
de $\alpha_s$: alimentar coeficientes a incidencia normal en un presupuesto de
Sabine o de EN 12354-6 subestima sistemáticamente la absorción instalada.

## 4. Incertidumbre de medida de la absorción (ISO 12999-2)

Un coeficiente de absorción valorado significa poco sin su incertidumbre. La
ISO 12999-2:2020 da la incertidumbre típica $u$ de las magnitudes que produce una
medida en cámara reverberante (ISO 354) y sus valoraciones (ISO 11654, EN 1793-1),
estimada a partir de ensayos interlaboratorio según ISO 5725. Es la compañera —
en absorción sonora— de la incertidumbre de aislamiento de la ISO 12999-1
([Medición del aislamiento en campo e índices](/phonometry/es/guides/insulation-field/)).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_uncertainty_es.svg" alt="Incertidumbre del coeficiente de absorción sonora ISO 12999-2: el espectro medido de alpha_s en bandas de tercio de octava de 63 Hz a 5000 Hz con una banda sombreada de más-menos U con factor de cobertura k = 2, reproduciendo el ejemplo resuelto de la Tabla 4 de la norma" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/absorption_uncertainty_es_dark.svg" alt="Incertidumbre del coeficiente de absorción sonora ISO 12999-2: el espectro medido de alpha_s en bandas de tercio de octava de 63 Hz a 5000 Hz con una banda sombreada de más-menos U con factor de cobertura k = 2, reproduciendo el ejemplo resuelto de la Tabla 4 de la norma" style="width:80%">

**Bandas de tercio de octava (cláusula 5).** Para el coeficiente de absorción, la
desviación típica de reproducibilidad es $\sigma_R = m\,\alpha_s + n$ (fórmula (1)),
y para el área de absorción equivalente $\sigma_R = m\,A_T + n\,S$ con
$S = 10\ \text{m}^2$ (fórmula (2)), donde $m$ y $n$ son las constantes dependientes
de la frecuencia de la Tabla 1 (63–5000 Hz). El valor de repetibilidad es
$\sigma_r = 0{,}6\,\sigma_R$ (fórmula (3)).

**Coeficiente práctico (cláusula 6).** Para el coeficiente práctico de ISO 11654,
$\sigma_R = m\,\alpha_p + n$ en bandas de octava con las constantes de la Tabla 2
(250–4000 Hz); de nuevo $\sigma_r = 0{,}6\,\sigma_R$.

**Números únicos (cláusula 7).** El coeficiente ponderado $\alpha_w$ tiene una
incertidumbre típica constante ($\sigma_R = 0{,}035$, $\sigma_r = 0{,}020$); la
valoración de número único $DL_{\alpha,\text{NRD}}$ de EN 1793-1 escala con el
valor ($\sigma_R = 0{,}10\,DL_\alpha$, $\sigma_r = 0{,}02\,DL_\alpha$).

**Notificación (cláusula 8).** La incertidumbre expandida es $U = k\,u$
(fórmula (10)) con el factor de cobertura $k$ de la Tabla 3 ($k = 2{,}0$ al 95 %,
gaussiano). El $U$ notificado se redondea a dos decimales para los coeficientes de
absorción y a un decimal para el área equivalente y $DL_{\alpha,\text{NRD}}$.

<details>
<summary>Ver el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
from phonometry import sound_absorption_coefficient_uncertainty

# Ejemplo resuelto de la Tabla 4 de ISO 12999-2: alpha_s por tercio de octava.
freqs = [63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
         630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000]
alpha_s = [0.33, 0.35, 0.39, 0.38, 0.37, 0.36, 0.36, 0.36, 0.43, 0.49,
           0.58, 0.63, 0.68, 0.71, 0.73, 0.75, 0.77, 0.79, 0.81, 0.81]
result = sound_absorption_coefficient_uncertainty(alpha_s, freqs, confidence=0.95)
result.plot()   # alpha_s con la banda +/-U (k = 2) de reproducibilidad
plt.show()
```
</details>

```python
from phonometry import (
    sound_absorption_coefficient_uncertainty,
    weighted_coefficient_uncertainty,
    single_number_rating_uncertainty,
)

# Incertidumbre de reproducibilidad de alpha_s a 1000 Hz (Tabla 1: m=0,040, n=0,015).
r = sound_absorption_coefficient_uncertainty([0.68], [1000], confidence=0.95)
print(round(float(r.standard_uncertainty[0]), 4))            # 0.0422 (sigma_R)
print(float(r.reported_expanded_uncertainty[0]))             # 0.08  (U, k=2)

# Valoraciones de número único (ejemplos resueltos de la cláusula 7).
print(float(weighted_coefficient_uncertainty(0.70).reported_expanded_uncertainty[0]))  # 0.07
print(float(single_number_rating_uncertainty(8.1).reported_expanded_uncertainty[0]))   # 1.6
```

## Referencias

- Allard, J. F., & Atalla, N. (2009). *Propagation of sound in porous media:
  Modelling sound absorbing materials* (2.ª ed.). Wiley.
  ISBN 978-0-470-74661-5.
  [doi:10.1002/9780470747339](https://doi.org/10.1002/9780470747339).
  La teoría del material poroso que sustenta las magnitudes medidas: la resistividad
  al flujo como entrada de modelo, y la impedancia superficial y la absorción
  que recupera el tubo.
- Cox, T. J., & D'Antonio, P. (2017). *Acoustic absorbers and diffusers:
  Theory, design and application* (3.ª ed.). CRC Press.
  ISBN 978-1-4987-4099-9.
  [doi:10.1201/9781315369211](https://doi.org/10.1201/9781315369211).
  La medida y el diseño de absorbentes en la práctica: los métodos de tubo y
  de cámara lado a lado, los montajes y la discusión del efecto de borde que sustenta
  la sección de tubo o cámara reverberante.
- International Organization for Standardization. (2003). *Acoustics —
  Measurement of sound absorption in a reverberation room* (ISO 354:2003).
  [Catálogo iso.org](https://www.iso.org/standard/34545.html).
  El método de cámara reverberante que produce los espectros de $\alpha_s$
  valorados por ISO 11654, incluidos los montajes de probeta del Anexo B.
- International Organization for Standardization. (1998). *Acoustics —
  Determination of sound absorption coefficient and impedance in impedance
  tubes — Part 2: Transfer-function method* (ISO 10534-2:1998; adoptada en
  Europa como EN ISO 10534-2:2001, la edición implementada aquí; revisada
  después como [ISO 10534-2:2023](https://www.iso.org/standard/81294.html)).
  [Catálogo iso.org](https://www.iso.org/standard/22851.html).
  El método de la función de transferencia con dos micrófonos y sus límites
  de rango de onda plana.
- ASTM International. (2019). *Standard test method for normal incidence
  determination of porous material acoustical properties based on the
  transfer matrix method* (ASTM E2611-19, la edición implementada aquí;
  revisada después como [ASTM E2611-24](https://store.astm.org/e2611-24.html)).
  [Tienda ASTM](https://store.astm.org/e2611-19.html).
  El método de matriz de transferencia con cuatro micrófonos que sustenta los
  ayudantes de pérdida por transmisión.
- International Organization for Standardization. (2018). *Acoustics —
  Determination of airflow resistance — Part 1: Static airflow method*
  (ISO 9053-1:2018).
  [Catálogo iso.org](https://www.iso.org/standard/69869.html).
  El método estático de la sección 2, con la regresión por el origen y la
  velocidad de referencia de 0,5 mm/s.

## Normas

ISO 11654:1997 (valoración ponderada de absorción sonora);
ISO 9053-1:2018 (resistencia estática al flujo de aire); ISO 9053-2:2020
(resistencia alterna al flujo de aire); BS EN ISO 10534-1:2001 y BS EN ISO 10534-2:2001
(tubo de impedancia); ASTM E2611-19 (pérdida por transmisión de cuatro
micrófonos); ISO 12999-2:2020 (incertidumbre de medida de la absorción sonora).
Toda ecuación se deriva del texto de la norma y se valida frente a
los ejemplos resueltos de las propias normas (ISO 11654 Anexo A, ISO 9053-2
Anexo A.3, ISO 12999-2 Tablas 4/5) e identidades en forma cerrada.

## Véase también

- Referencia de la API: [`materials.impedance_tube`](/phonometry/es/reference/api/materials/impedance-tube/), [`materials.airflow_resistance`](/phonometry/es/reference/api/materials/airflow-resistance/) y [`materials.absorption_uncertainty`](/phonometry/es/reference/api/materials/absorption-uncertainty/).

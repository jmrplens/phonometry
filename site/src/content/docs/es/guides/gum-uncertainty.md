---
title: "Incertidumbre de medida (GUM y Monte Carlo)"
description: "Los dos métodos de propagación de la GUM: la ley de propagación de la incertidumbre (ISO/IEC Guía 98-3:2008) y el método de Monte Carlo (Suplemento 1) — incertidumbre combinada y expandida, grados de libertad efectivos de Welch–Satterthwaite, evaluaciones de Tipo B e intervalos de cobertura simétricos en probabilidad."
---

Todo resultado de medida está incompleto sin una declaración de su
incertidumbre. La *Guía para la expresión de la incertidumbre de medida* ofrece
dos formas de propagar las incertidumbres de las entradas de un modelo de
medida $y = f(x_1, \dots, x_N)$ hacia la salida: la **ley de propagación de la
incertidumbre** (**ISO/IEC Guía 98-3:2008**, la GUM, cláusula 5) y el **método
de Monte Carlo** (**ISO/IEC Guía 98-3-1:2008**, Suplemento 1, cláusula 7). La
primera combina las incertidumbres típicas analíticamente a través de los
coeficientes de sensibilidad; el segundo propaga numéricamente las
distribuciones de probabilidad completas. Coinciden para modelos lineales y
divergen, de forma reveladora, cuando el modelo es no lineal o las entradas se
alejan de la gaussiana.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_uncertainty_es.svg" alt="Desde un modelo de medida compartido y sus estimaciones de entrada e incertidumbres típicas, dos vías paralelas: la ley de propagación de la GUM (coeficientes de sensibilidad, combinación en cuadratura, grados de libertad efectivos de Welch-Satterthwaite, incertidumbre expandida U igual a k por uc) y el método de Monte Carlo (muestrear cada entrada de su PDF, propagar M ensayos, tomar el intervalo de cobertura simétrico en probabilidad al 95 por ciento)" style="width:88%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_uncertainty_es_dark.svg" alt="Desde un modelo de medida compartido y sus estimaciones de entrada e incertidumbres típicas, dos vías paralelas: la ley de propagación de la GUM (coeficientes de sensibilidad, combinación en cuadratura, grados de libertad efectivos de Welch-Satterthwaite, incertidumbre expandida U igual a k por uc) y el método de Monte Carlo (muestrear cada entrada de su PDF, propagar M ensayos, tomar el intervalo de cobertura simétrico en probabilidad al 95 por ciento)" style="width:88%">

## 1. La ley de propagación de la incertidumbre (GUM, cláusula 5)

Para un modelo $y = f(x_1, \dots, x_N)$ con entradas no correlacionadas, la
incertidumbre típica combinada es la suma en cuadratura de las contribuciones de
las entradas $u_i(y) = |c_i|\,u(x_i)$ ponderadas por los coeficientes de
sensibilidad $c_i = \partial f / \partial x_i$:

$$
u_c^2(y) = \sum_{i=1}^{N} \left(\frac{\partial f}{\partial x_i}\right)^2 u^2(x_i).
$$

`combine_uncertainty` evalúa las sensibilidades por diferencias centradas, de
modo que funciona cualquier modelo invocable — sin derivadas parciales a mano.
Las magnitudes de entrada se describen con una `Quantity` (mejor estimación,
incertidumbre típica, PDF, grados de libertad). Las evaluaciones de Tipo B a
partir de una semianchura $a$ se construyen con `rectangular` ($a/\sqrt{3}$),
`triangular` ($a/\sqrt{6}$) y `u_shaped` ($a/\sqrt{2}$) (GUM, cláusula 4.3).

```python
import phonometry as ph

# Nivel ponderado A: una lectura más correcciones de calibración, de
# instrumento y de posición de media cero. El modelo es su suma.
quantities = [
    ph.Quantity(74.0, 0.0, name="Reading"),
    ph.rectangular(0.0, 0.20, name="Calibration"),
    ph.rectangular(0.0, 0.30, name="Instrument"),
    ph.Quantity(0.0, 0.35, dof=9, name="Position (Type A)"),
]
result = ph.combine_uncertainty(lambda a, b, c, d: a + b + c + d, quantities)

print(round(result.value, 2))                 # 74.0
print(round(result.combined_uncertainty, 3))  # 0.407 dB
print(result.contributions.round(3))          # [0.    0.115 0.173 0.35 ]
print(round(result.effective_dof, 1))         # 16.5

k, U = result.expanded(0.95)
print(round(k, 2), round(U, 2))               # 2.11 0.86  ->  Y = 74.0 ± 0.9 dB
```

La **incertidumbre expandida** $U = k\,u_c$ escala la incertidumbre combinada
por un factor de cobertura $k = t_p(\nu_\text{ef})$ de la distribución $t$ con
los **grados de libertad efectivos** dados por la fórmula de Welch–Satterthwaite
(Anexo G.4). Aquí la única entrada de Tipo A (9 grados de libertad) hace bajar
$\nu_\text{ef}$ hasta unos 16, de modo que $k = 2{,}11$ en lugar del 1,96 de
gran muestra. Las entradas correlacionadas se tratan pasando una matriz de
correlación; una suma totalmente correlacionada se suma entonces linealmente en
vez de en cuadratura. Como la GUM define Welch–Satterthwaite solo para
entradas *independientes*, un presupuesto correlacionado recurre a
$\nu_\text{ef} = \infty$ (GUM 6.3.3): `expanded()` usa entonces el factor de
cobertura de la distribución normal, y un aviso informa de que los grados de
libertad finitos de las entradas no se propagaron. Esta cadena reproduce de
principio a fin los ejemplos resueltos de la propia GUM: el presupuesto del
calibre del anexo H.1 ($u_c = 31{,}7$ nm, $U_{99} = 92$ nm frente a los 32/93
impresos) y la medida correlacionada de resistencia del anexo H.2
($u_c(R) = 0{,}071\ \Omega$, $u_c(X) = 0{,}295\ \Omega$,
$u_c(Z) = 0{,}236\ \Omega$ de la Tabla H.3).

## 2. El método de Monte Carlo (Suplemento 1)

Cuando el modelo es no lineal o las entradas son marcadamente no gaussianas, la
hipótesis gaussiana de la GUM para la salida puede ser inexacta. `monte_carlo`
en cambio muestrea cada entrada de su PDF, evalúa el modelo sobre todos los
ensayos y reporta la media, la desviación típica y el **intervalo de cobertura
simétrico en probabilidad** (igual probabilidad en cada cola, cláusula 7.7).
Las entradas se muestrean de forma independiente —la vía gaussiana
multivariante del Suplemento para magnitudes no independientes (6.4.8) no está
implementada, así que los presupuestos correlacionados corresponden a
`combine_uncertainty`—, el número de ensayos es fijo (sin el procedimiento
adaptativo de 7.9, mínimo 2 ensayos) y el intervalo es el simétrico, no el
intervalo más corto de 5.3.4.

```python
import phonometry as ph

quantities = [
    ph.Quantity(74.0, 0.0, name="Reading"),
    ph.rectangular(0.0, 0.20, name="Calibration"),
    ph.rectangular(0.0, 0.30, name="Instrument"),
    ph.Quantity(0.0, 0.35, dof=9, name="Position (Type A)"),
]
mc = ph.monte_carlo(lambda a, b, c, d: a + b + c + d, quantities,
                    trials=1_000_000, coverage=0.95, seed=1)

print(round(mc.value, 2))                 # 74.0
print(round(mc.standard_uncertainty, 3))  # 0.407 dB  (coincide con la uc de arriba)
print([round(x, 2) for x in mc.interval]) # [73.2, 74.8]
```

Para este modelo casi lineal la incertidumbre típica de Monte Carlo reproduce el
$u_c$ de la GUM con tres cifras y el intervalo al 95 % coincide con $Y \pm U$.
Ambos métodos se validan frente a los ejemplos resueltos de las propias Guías: el
modelo aditivo de cuatro entradas unidad da $u_c = 2{,}0$ (Suplemento 1,
cláusula 9.2), y cuatro entradas rectangulares dan un intervalo de Monte Carlo de
$[-3{,}88,\, 3{,}88]$ (Suplemento 1, cláusula 9.2.3).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/uncertainty_budget_es.svg" alt="Dos paneles para el ejemplo del nivel ponderado A. Izquierda: el balance de incertidumbre de la GUM, un diagrama de barras horizontales de la contribución de cada entrada a la incertidumbre combinada con una línea discontinua en uc de 0,407 dB. Derecha: el histograma de salida de Monte Carlo superpuesto con la gaussiana de la GUM y el intervalo de cobertura del 95 por ciento sombreado; el título indica Y igual a 74,00 dB, U igual a 0,86 dB, k igual a 2,11" style="width:96%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/uncertainty_budget_es_dark.svg" alt="Dos paneles para el ejemplo del nivel ponderado A. Izquierda: el balance de incertidumbre de la GUM, un diagrama de barras horizontales de la contribución de cada entrada a la incertidumbre combinada con una línea discontinua en uc de 0,407 dB. Derecha: el histograma de salida de Monte Carlo superpuesto con la gaussiana de la GUM y el intervalo de cobertura del 95 por ciento sombreado; el título indica Y igual a 74,00 dB, U igual a 0,86 dB, k igual a 2,11" style="width:96%">

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

quantities = [
    ph.Quantity(74.0, 0.0, name="Reading"),
    ph.rectangular(0.0, 0.20, name="Calibration"),
    ph.rectangular(0.0, 0.30, name="Instrument"),
    ph.Quantity(0.0, 0.35, dof=9, name="Position (Type A)"),
]
model = lambda a, b, c, d: a + b + c + d
result = ph.combine_uncertainty(model, quantities)
mc = ph.monte_carlo(model, quantities, trials=1_000_000, coverage=0.95, seed=1,
                    keep_samples=True)
k, U = result.expanded(0.95)

# En una línea por panel — las barras del balance, y el histograma de Monte
# Carlo con su intervalo (la figura del repositorio superpone además la
# gaussiana del GUM):
result.plot()
mc.plot()
plt.show()

# A mano, ambos paneles — las barras del balance y la distribución de salida de Monte Carlo:
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.4))
ax1.barh(result.names, result.contributions)
ax1.axvline(result.combined_uncertainty, ls="--",
            label=f"$u_c$ = {result.combined_uncertainty:.3f} dB")
ax1.invert_yaxis(); ax1.legend()

rng = np.random.default_rng(1)
samples = model(np.full(200_000, 74.0),
                rng.uniform(-0.20, 0.20, 200_000),
                rng.uniform(-0.30, 0.30, 200_000),
                rng.normal(0.0, 0.35, 200_000))
ax2.hist(samples, bins=120, density=True, alpha=0.35, label="Monte Carlo")
ax2.axvspan(*mc.interval, alpha=0.12, label="95 % coverage interval")
ax2.set_title(f"Y = {result.value:.2f} dB,  U = {U:.2f} dB (k = {k:.2f})")
ax2.legend()
plt.show()
```

</details>

El `UncertaintyResult` lleva el `value`, la `combined_uncertainty`, las
`sensitivities`, las `contributions` por entrada y los `effective_dof`; su
`.plot()` dibuja el balance y `.expanded(coverage)` devuelve el par $(k, U)$. El
`MonteCarloResult` lleva el `value`, la `standard_uncertainty`, el `interval` de
cobertura y su `coverage`; con `keep_samples=True` conserva además las
muestras de salida (`samples`), y su `.plot()` dibuja el histograma de salida
con el intervalo de cobertura marcado (el panel derecho de arriba). La incertidumbre de acústica de la edificación de
ISO 12999-1 — que combina términos de reproducibilidad para una magnitud de
número único — es un balance aparte, específico de ese dominio.

---

**Normas.** ISO/IEC Guía 98-3:2008, *Uncertainty of measurement — Part 3: Guide
to the expression of uncertainty in measurement (GUM:1995)* — la ley de
propagación de la incertidumbre (cláusula 5), la evaluación de Tipo B
(cláusula 4.3), la incertidumbre expandida y el factor de cobertura (cláusula 6,
Anexo G) y los grados de libertad efectivos de Welch–Satterthwaite (Anexo G.4).
ISO/IEC Guía 98-3-1:2008, *Supplement 1 — Propagation of distributions using a
Monte Carlo method* — la propagación numérica y el intervalo de cobertura
simétrico en probabilidad (cláusula 7).

## Véase también

- Referencia de la API: [`metrology.uncertainty`](/phonometry/es/reference/api/metrology/uncertainty/).

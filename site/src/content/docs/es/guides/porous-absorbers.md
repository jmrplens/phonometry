---
title: "Absorbentes porosos y multicapa"
description: "Predicción de la absorción a partir de los parámetros del material: los modelos porosos de Delany-Bazley, Miki y Johnson-Champoux-Allard, el solucionador multicapa por matrices de transferencia con capas perforadas, microperforadas (Maa) y de membrana, y la integral de Paris de incidencia aleatoria."
---

A partir de la **resistividad al flujo** de un material poroso — la magnitud
que mide el [banco de flujo](/phonometry/es/guides/materials/) — los modelos
clásicos de fluido equivalente predicen su impedancia característica y su
número de onda complejos, y una pila de capas por **matrices de
transferencia** (mantas porosas, cámaras de aire, paneles perforados y
microperforados, membranas) predice el coeficiente de absorción de toda la
construcción antes de construir nada. Esta página cubre los tres modelos
porosos (Delany–Bazley, Miki, Johnson–Champoux–Allard), el solucionador
multicapa, las capas resonantes de Maa y la integral de incidencia aleatoria
(Paris). Las contrapartes de medida están en
[Materiales acústicos](/phonometry/es/guides/materials/); la valoración del
espectro predicho vive en
[la sección ISO 11654 de esa misma página](/phonometry/es/guides/materials/).

## 1. Modelos de fluido equivalente de un material poroso

Un material poroso de esqueleto rígido se comporta como un *fluido
equivalente* con una impedancia característica compleja $Z_c$ y un número de
onda $k$ (convención temporal $e^{+j\omega t}$, de modo que un medio pasivo
tiene $\mathrm{Im}(k) < 0$).

**Delany–Bazley** (Mechel 2e secc. G.11; Bies 5e apéndice D, tabla D.1;
Hopkins ecs. 1.171–1.174) es la ley de potencias de un parámetro en la
variable del absorbente $X = \rho_0 f / \sigma$:

$$
\frac{Z_c}{\rho_0 c_0} = 1 + C_1 X^{-C_2} - j\,C_3 X^{-C_4}, \qquad
\frac{k}{k_0} = 1 + C_5 X^{-C_6} - j\,C_7 X^{-C_8},
$$

con los coeficientes clásicos de lana de roca/fibra de vidrio
$(0{,}0571,\,0{,}754,\,0{,}087,\,0{,}732,\,0{,}0978,\,0{,}700,\,0{,}189,\,0{,}595)$
y un rango de ajuste declarado $0{,}01 < X < 1{,}0$ (porosidad cercana a
uno). La biblioteca incluye también los juegos de la tabla D.1 ajustados a
poliéster (`"garai_pompoli"`) y a espumas (`"dunn_davern"`, `"wu"`). Fuera
del rango de ajuste se emite un `PorousAbsorberWarning` y los valores
extrapolados se devuelven igualmente — el fallo clásico es una parte real
*negativa* de la impedancia de entrada de la capa a baja frecuencia (Mechel
secc. G.12).

**Miki** (1990) reajustó los mismos datos de Delany–Bazley bajo una
restricción de pasividad (positivo-real), de modo que el modelo se mantiene
físicamente bien comportado por debajo del rango de ajuste; es la elección
habitual cuando un modelo de un parámetro debe evaluarse en banda ancha.

**Johnson–Champoux–Allard (JCA)** es el modelo semifenomenológico de cinco
parámetros (Cox & D'Antonio 3e ecs. 6.19–6.25): la resistividad al flujo
$\sigma$, la porosidad $\phi$, la tortuosidad $\alpha_\infty$ y las
longitudes características viscosa/térmica $\Lambda$, $\Lambda'$ dan la
densidad efectiva y el módulo de compresibilidad con los límites exactos
$j\omega\rho_e \to \sigma$ en continua,
$\rho_e \to (\alpha_\infty \rho_0/\phi)(1 + (1-j)\,\delta_v/\Lambda)$ a alta
frecuencia, y la transición isoterma-adiabática en $K_e$.

```python
import numpy as np
from phonometry import materials

f = np.geomspace(200.0, 4000.0, 200)
db = materials.delany_bazley(f, 20000.0)          # sigma en Pa s/m2
mk = materials.miki(f, 20000.0)
jca = materials.johnson_champoux_allard(
    f, 20000.0, porosity=0.98, tortuosity=1.0,
    viscous_length=8.7e-5, thermal_length=8.7e-5,
)
print(np.round(db.normalized_impedance[0], 3))    # (2.598-2.209j)
print(np.round(mk.normalized_impedance[0], 3))    # (2.286-1.965j)
print(np.round(jca.normalized_impedance[0], 3))   # (2.321-2.075j)

db.plot()   # componentes normalizadas de Zc y k frente a la frecuencia
```

Los tres modelos coinciden estrechamente dentro del rango de ajuste de
Delany–Bazley (Cox & D'Antonio, figs. 6.19–6.21, hacen la misma
comparación); JCA extiende la predicción con base física fuera de él. Un
`PorousMediumResult` construido con datos medidos (por ejemplo los $Z_c$,
$k$ recuperados por la
[reducción de matriz de transferencia ASTM E2611](/phonometry/es/guides/materials/))
se conecta al solucionador de capas exactamente igual que uno modelado.

## 2. Predicción multicapa por matrices de transferencia

Cada capa fluida de espesor $d$ aporta la matriz de cadena (Cox & D'Antonio
ec. 2.29; equivalente a la recursión de impedancias de Bies ec. D.95 y al
esquema de Mechel secc. D.4)

$$
\begin{bmatrix} p \\ u \end{bmatrix}_{\text{frente}} =
\begin{bmatrix}
\cos(k_x d) & j Z_x \sin(k_x d) \\
j \sin(k_x d)/Z_x & \cos(k_x d)
\end{bmatrix}
\begin{bmatrix} p \\ u \end{bmatrix}_{\text{fondo}},
$$

con el número de onda en profundidad
$k_x = \sqrt{k^2 - k_0^2 \sin^2\theta}$ por la ley de Snell y
$Z_x = Z_c k / k_x$. Las láminas resonantes delgadas entran como impedancias
en serie $[[1, z], [0, 1]]$. Cerrar la cadena con una pared rígida (o aire
libre, o cualquier impedancia) da la impedancia de superficie, el factor de
reflexión $R(\theta)$ y $\alpha(\theta) = 1 - |R|^2$. Una única capa porosa
sobre pared rígida se reduce a la forma cerrada de libro
$Z_s = -j Z_c \cot(k d)$ (Mechel secc. D.3, ec. 1).

```python
import numpy as np
from phonometry import materials

f = np.geomspace(200.0, 4000.0, 300)
med = materials.miki(f, 20000.0)
res = materials.layered_absorber(f, [materials.PorousLayer(0.05, med)])
i = np.argmin(np.abs(f - 1000.0))
print(round(res.absorption[i], 3))               # 0.937 a 1 kHz

res.plot()   # alpha(f) con |R| superpuesto
```

El solucionador evalúa las magnitudes físicas mediante una recursión de
admitancias numéricamente robusta (inmune al desbordamiento
$e^{|\mathrm{Im}(k_x)| d}$ de las entradas matriciales crudas en capas
extremadamente atenuantes) y aun así expone la matriz de cadena completa —
recíproca por construcción, $\det T = 1$ — en `transfer_matrix`, lista para
la [maquinaria ASTM E2611](/phonometry/es/guides/materials/)
(`TransferMatrix`).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/porous_absorber_designs_es.svg" alt="Absorción predicha en incidencia normal de cuatro construcciones de 50 mm: una capa porosa absorbe en banda ancha desde frecuencias medias, un panel microperforado sobre cámara presenta su pico cerca de 700 Hz, un panel perforado sobre poroso cerca de 500 Hz y una membrana sobre cámara con poroso cerca de 175 Hz; las líneas verticales punteadas marcan las resonancias de forma cerrada de Helmholtz y de membrana" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/porous_absorber_designs_es_dark.svg" alt="Absorción predicha en incidencia normal de cuatro construcciones de 50 mm: una capa porosa absorbe en banda ancha desde frecuencias medias, un panel microperforado sobre cámara presenta su pico cerca de 700 Hz, un panel perforado sobre poroso cerca de 500 Hz y una membrana sobre cámara con poroso cerca de 175 Hz; las líneas verticales punteadas marcan las resonancias de forma cerrada de Helmholtz y de membrana" style="width:80%">

*Cuatro construcciones, un mismo presupuesto de 50 mm: la capa porosa
funciona en banda ancha pero decae a baja frecuencia; los diseños
microperforado, perforado y de membrana cambian ancho de banda por un pico
resonante situado cada vez más abajo. Las líneas punteadas son las formas
cerradas de cavidad poco profunda — el modelo completo queda por debajo
porque la masa viscosa del tapón de aire y la profundidad finita de la
cámara no son despreciables.*

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import materials as m

f = np.geomspace(50.0, 5000.0, 500)
med = m.miki(f, 20000.0)
med_light = m.miki(f, 10000.0)
designs = {
    "Poroso 50 mm": [m.PorousLayer(0.05, med)],
    "MPP + cámara": [m.MicroperforatedPlateLayer(0.5e-3, 0.15e-3, 0.008),
                     m.AirLayer(0.048)],
    "Perforado + poroso": [m.PerforatedPlateLayer(0.006, 0.0025, 0.05),
                           m.PorousLayer(0.025, med), m.AirLayer(0.019)],
    "Membrana + poroso": [m.MembraneLayer(2.0), m.AirLayer(0.01),
                          m.PorousLayer(0.038, med_light)],
}
fig, ax = plt.subplots()
for label, layers in designs.items():
    ax.semilogx(f, m.layered_absorber(f, layers).absorption, label=label)
ax.set(xlabel="Frecuencia [Hz]", ylabel="Coeficiente de absorción")
ax.legend()
plt.show()
```

</details>

## 3. Láminas resonantes: perforado, microperforado, membrana

**Panel perforado.** Los tapones de aire de los orificios son la masa de un
resonador de Helmholtz: $m = (\rho_0/\varepsilon)\,[t + 2\delta a +
\sqrt{8\nu/\omega}\,(1 + t/2a)]$ con el área abierta $\varepsilon$, el
factor de corrección de extremo $\delta$ por extremo de orificio y la
resistencia viscotérmica
$r = (\rho_0/\varepsilon)\sqrt{8\nu\omega}\,(1 + t/2a)$ (Cox & D'Antonio
ecs. 7.6/7.12). La corrección de extremo por defecto es el ajuste de
interacción de la función de Fok
$\delta = 0{,}85\,(1 - 1{,}47\sqrt{\varepsilon} + 0{,}47\varepsilon^{3/2})$
(tabla 7.1), válido para cualquier área abierta. Para una cámara poco
profunda la resonancia es
$f_0 = (c_0/2\pi)\sqrt{\varepsilon/(t'\,d)}$ (ec. 7.4).

**Panel microperforado (MPP).** Con orificios submilimétricos la capa
límite viscosa llena el orificio y el panel absorbe *sin ningún material
poroso*. La biblioteca implementa la impedancia exacta de tubo corto de Maa
(Maa 1998, ec. 2),

$$
z_1 = j\omega\rho_0 t \left[ 1 -
\frac{2}{x\sqrt{-j}}\,\frac{J_1(x\sqrt{-j})}{J_0(x\sqrt{-j})} \right]^{-1},
\qquad x = a\sqrt{\rho_0 \omega/\eta},
$$

más las correcciones de extremo de la ec. 5 (resistencia superficial
$\tfrac{1}{2}\sqrt{2\omega\rho_0\eta}$ y reactancia de pistón $0{,}85\,d$ en
total), dividida por el área abierta. La constante de perforado $x$ — proporcional al
radio del orificio sobre el espesor de la capa límite viscosa — lo gobierna
todo: en la resonancia $\omega_0 m = \cot(\omega_0 D/c_0)$ la absorción
máxima es $4r/(1+r)^2$ y el ancho de banda de media absorción es
$f_2/f_1 = \pi/\mathrm{arccot}(1+r) - 1$ (Maa, ecs. 9–21, tabla I).

```python
import numpy as np
from phonometry import materials

# Maa (1998), fig. 5: d = t = 0,2 mm, orificios cada 2,5 mm, cámara de 6 cm.
eps = (np.pi / 4.0) * (0.2 / 2.5) ** 2
f = np.linspace(100.0, 4000.0, 2000)
res = materials.layered_absorber(
    f, [materials.MicroperforatedPlateLayer(0.2e-3, 0.1e-3, eps),
        materials.AirLayer(0.06)],
)
i = np.argmax(res.absorption)
print(f"alpha máximo = {res.absorption[i]:.2f} a {f[i]:.0f} Hz")
# alpha máximo = 0.96 a 677 Hz
```

**Membrana.** Una lámina impermeable flexible es la masa superficial
$z = j\omega m$ (Cox ec. 7.14; Bies ec. D.96); sobre una cámara resuena en
el clásico $f_0 \approx 60/\sqrt{m d}$ (adiabático;
$\approx 50/\sqrt{m d}$ cuando la cámara está rellena de poroso y es
isoterma, Cox ecs. 7.9/7.10). Las formas cerradas se exponen como
`helmholtz_resonance_frequency` y `membrane_resonance_frequency`; la
respuesta completa en frecuencia sale de la misma pila de capas.

## 4. Incidencia oblicua y aleatoria

`layered_absorber(..., angle=theta)` evalúa la pila completa de reacción
volumétrica a cualquier ángulo polar; las láminas son de reacción local
(independientes del ángulo) y las capas fluidas refractan según la ley de
Snell — para un MPP sobre cámara esto reproduce exactamente la forma cerrada
oblicua de Maa (ec. 23). El coeficiente de incidencia aleatoria es la
integral de Paris (Mechel secc. D.5, ec. 9)

$$
\alpha_{dif} = \frac{2}{\sin^2\theta_{lim}} \int_0^{\theta_{lim}}
\alpha(\theta)\,\cos\theta\,\sin\theta\,\mathrm{d}\theta,
$$

evaluada por cuadratura de Gauss–Legendre en `diffuse_field_absorption`
(``angle_limit`` por defecto 90°; se usan truncamientos a 75–87°). Para una
superficie de *reacción local* con impedancia normalizada conocida la
integral tiene la forma cerrada de Mechel ec. 10, expuesta como
`statistical_absorption` — su máximo sobre todas las impedancias pasivas es
el **0,951** publicado (en $z \approx 1{,}57$).

```python
import numpy as np
from phonometry import materials

f = np.array([250.0, 500.0, 1000.0, 2000.0])
med = materials.miki(f, 20000.0)
layers = [materials.PorousLayer(0.05, med)]
normal = materials.layered_absorber(f, layers).absorption
diffuse = materials.diffuse_field_absorption(f, layers).absorption
print(np.round(normal, 2))    # [0.26 0.62 0.94 0.95]
print(np.round(diffuse, 2))   # [0.37 0.68 0.9  0.95]

print(round(float(materials.statistical_absorption(1.567 + 0j)), 3))  # 0.951
```

## Notas prácticas

**Rangos de ajuste.** Delany–Bazley avisa (y extrapola) fuera de
$0{,}01 < X < 1$ y Miki fuera de $0{,}01 < f/\sigma < 1$; los valores por
debajo del rango deben tratarse como cualitativos. JCA necesita cuatro parámetros más pero se comporta
físicamente en todo el rango; con
$\Lambda = \Lambda' = \sqrt{8\alpha_\infty\eta/(\phi\sigma)}$ y
$\alpha_\infty = 1$ sigue a Delany–Bazley dentro del rango de ajuste.

**Reacción local frente a volumétrica.** El solucionador de capas es de
reacción volumétrica (el sonido refracta y viaja dentro de las capas).
`statistical_absorption` supone reacción local — buena aproximación para
resistividades altas, cámaras compartimentadas o revestimientos resonantes
delgados; para capas porosas gruesas y ligeras integre el modelo volumétrico
con `diffuse_field_absorption` (Mechel secc. D.6).

**Dónde se comprobaron los números.** Los modelos están fijados dígito a
dígito a las tablas de coeficientes impresas (Bies tabla D.1, Miki
ecs. 30–34), el solucionador a las formas cerradas anteriores y a la
recuperación por `TransferMatrix` de la
[página del tubo de impedancia](/phonometry/es/guides/materials/), el MPP a
la propia aproximación de Maa (acuerdo declarado de ~6 % con la ec. 2
exacta), a su ejemplo de diseño y a su tabla I, y la integral de Paris a su
forma cerrada de reacción local. Tres erratas encontradas en las fuentes
durante este trabajo están registradas en el
[registro de erratas](https://github.com/jmrplens/phonometry/blob/main/docs/ERRATA.md).

## Referencias

- Mechel, F. P. (Ed.). (2008). *Formulas of acoustics* (2.ª ed.). Springer.
  [doi:10.1007/978-3-540-76833-3](https://doi.org/10.1007/978-3-540-76833-3).
  Secciones D.3–D.6 (reflexión en capas, esquema multicapa, integrales de
  campo difuso) y G.11 (relaciones empíricas de porosos).
- Bies, D. A., Hansen, C. H., & Howard, C. Q. (2018). *Engineering noise
  control* (5.ª ed.). CRC Press.
  [doi:10.1201/9781351228152](https://doi.org/10.1201/9781351228152).
  Apéndice D: propiedades de materiales porosos, juegos de coeficientes de
  la tabla D.1 y las recursiones de construcciones en capas D.91–D.99.
- Cox, T. J., & D'Antonio, P. (2017). *Acoustic absorbers and diffusers:
  Theory, design and application* (3.ª ed.). CRC Press.
  [doi:10.1201/9781315369211](https://doi.org/10.1201/9781315369211).
  Modelado por matrices de transferencia (secc. 2.6), modelos porosos
  (secc. 6.5) y ecuaciones de diseño de absorbentes resonantes
  (seccs. 7.3/7.5).
- Attenborough, K., & Van Renterghem, T. (2021). *Predicting
  outdoor sound* (2.ª ed.). CRC Press.
  [doi:10.1201/9780429470806](https://doi.org/10.1201/9780429470806).
  Capítulo 5: modelos de impedancia de suelos, incluida la familia JCA.
- Hopkins, C. (2007). *Sound insulation*. Butterworth-Heinemann.
  [doi:10.4324/9780080550473](https://doi.org/10.4324/9780080550473).
  Sección 1.3.2.2: el modelo de gas equivalente y la forma SI de
  Delany–Bazley.
- Miki, Y. (1990). Acoustical properties of porous materials —
  Modifications of Delany–Bazley models. *Journal of the Acoustical Society
  of Japan (E)*, 11(1), 19–24.
  [doi:10.1250/ast.11.19](https://doi.org/10.1250/ast.11.19).
  La regresión positivo-real implementada en `miki`.
- Maa, D.-Y. (1998). Potential of microperforated panel absorber.
  *Journal of the Acoustical Society of America*, 104(5), 2861–2866.
  [doi:10.1121/1.423870](https://doi.org/10.1121/1.423870).
  La impedancia exacta del MPP (ec. 2), las correcciones de extremo, las
  fórmulas de diseño y el ejemplo de la fig. 5 fijado en los tests.
- Johnson, D. L., Koplik, J., & Dashen, R. (1987). Theory of dynamic
  permeability and tortuosity in fluid-saturated porous media. *Journal of
  Fluid Mechanics*, 176, 379–402.
  [doi:10.1017/S0022112087000727](https://doi.org/10.1017/S0022112087000727).
  El modelo de tortuosidad dinámica tras la densidad efectiva JCA.
- Delany, M. E., & Bazley, E. N. (1970). Acoustical properties of fibrous
  absorbent materials. *Applied Acoustics*, 3(2), 105–116.
  [doi:10.1016/0003-682X(70)90031-9](https://doi.org/10.1016/0003-682X(70)90031-9).
  Las relaciones empíricas originales y su validez declarada.

## Normas

Ningún estándar rige estos modelos de predicción; son métodos de libro y de
revista (Mechel; Bies, Hansen & Howard; Cox & D'Antonio; Attenborough & Van
Renterghem; Miki 1990; Maa 1998; Johnson et al. 1987) implementados en
sala limpia desde las fuentes citadas. Las normas de medida con las que
conectan — ISO 9053-1/-2 (resistividad al flujo), ISO 10534-1/-2 y
ASTM E2611 (tubo de impedancia), ISO 354 / ISO 11654 (absorción de
incidencia aleatoria y su valoración) — viven en
[Materiales acústicos](/phonometry/es/guides/materials/).

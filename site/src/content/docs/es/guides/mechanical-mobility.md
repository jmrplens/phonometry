---
title: "Movilidad mecánica y la familia de FRF (ISO 7626-1)"
description: "La familia de funciones de respuesta en frecuencia movimiento-por-fuerza de la ISO 7626-1:2011: receptancia, movilidad y acelerancia con sus recíprocas rigidez dinámica, impedancia y masa aparente (Tabla 1), la conversión a través de la receptancia como pivote y el resonador de referencia de un grado de libertad cuya movilidad en el punto de excitación alcanza 1/c en resonancia (Anexo A)."
---

La **movilidad** mecánica es el cociente complejo entre una respuesta en
velocidad y la fuerza que la produce, `Y = v/F`. Es un miembro de una familia de
**funciones de respuesta en frecuencia** (FRF) movimiento-por-fuerza: cuál se usa
depende solo de si el movimiento es un desplazamiento, una velocidad o una
aceleración, y cada una tiene una recíproca fuerza-por-movimiento. La
**ISO 7626-1:2011** define la familia completa (Tabla 1) y el resonador de
referencia de un grado de libertad (SDOF, Anexo A). Esta base de FRF sustenta las
normas de fuente y transmisión de ruido estructural: ISO 9611, ISO 10846,
EN 15657 y EN 12354-5.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/mechanical_mobility_es.svg" alt="Magnitudes normalizadas de receptancia, movilidad y acelerancia de un resonador de un grado de libertad en un eje de frecuencia log-log, todas con máximo en la resonancia" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/mechanical_mobility_es_dark.svg" alt="Magnitudes normalizadas de receptancia, movilidad y acelerancia de un resonador de un grado de libertad en un eje de frecuencia log-log, todas con máximo en la resonancia" style="width:82%">

## 1. La familia de funciones de respuesta en frecuencia (Tabla 1)

Para un movimiento armónico `x·e^{jωt}` la velocidad es `jω·x` y la aceleración
`−ω²·x`, de modo que las tres FRF movimiento-por-fuerza se derivan de la
receptancia `H` por una potencia de `jω`, y cada una tiene una recíproca
fuerza-por-movimiento:

| Movimiento | FRF (movimiento / fuerza) | Unidad | Recíproca (fuerza / movimiento) | Unidad |
|---|---|---|---|---|
| desplazamiento | receptancia `H = x/F` | m/N | rigidez dinámica `1/H` | N/m |
| velocidad | movilidad `Y = jω·H` | m/(N·s) | impedancia `1/Y` | N·s/m |
| aceleración | acelerancia `A = −ω²·H` | 1/kg | masa aparente `1/A` | kg |

`convert_frf` pasa entre cualquiera de las seis FRF, usando la receptancia como
pivote. Una FRF de **punto de excitación** tiene la respuesta y la fuerza en el
mismo punto (`i = j`); una FRF de **transferencia** las tiene en puntos
distintos.

```python
import phonometry as ph

# Una movilidad de 2e-3 m/(N.s) a 80 Hz, expresada como las demás FRF:
Y = 2e-3
print(round(abs(ph.convert_frf(Y, 80.0, "mobility", "impedance")), 1))     # 500.0  N.s/m
print(f"{abs(ph.convert_frf(Y, 80.0, 'mobility', 'accelerance')):.3f}")    # 1.005  1/kg
```

## 2. El resonador SDOF de referencia (Anexo A)

La referencia canónica en forma cerrada es una masa `m`, un amortiguamiento
viscoso `c` y una rigidez `k`, cuya receptancia es

$$
H(\omega) = \frac{1}{k - \omega^2 m + j\,\omega c}, \qquad
\omega_0 = \sqrt{k/m}.
$$

En la resonancia `ω0` la movilidad en el punto de excitación es **puramente
real** e igual a `1/c` —el máximo de movilidad mide el amortiguamiento— mientras
que la receptancia estática (`ω → 0`) es la flexibilidad `1/k`:

```python
import numpy as np
import phonometry as ph

m, k, c = 2.0, 8000.0, 5.0
f0 = ph.resonance_frequency(m, k)             # 10.07 Hz

y0 = complex(ph.sdof_mobility(f0, m, k, c))
print(round(y0.real, 4), round(y0.imag, 6))   # 0.2 0.0   -> |Y(f0)| = 1/c
print(round(complex(ph.sdof_receptance(1e-6, m, k, c)).real, 7))  # 0.000125 = 1/k
```

## 3. El objeto `MobilityResult`

`sdof_mobility_result` agrupa la FRF en frecuencia en un `MobilityResult`, que
expone `.magnitude`, `.phase`, `.to(target)` (cualquier tipo de la Tabla 1) y un
`.plot()` de `|Y(f)|` con la resonancia marcada:

```python
import numpy as np
import phonometry as ph

f = np.logspace(np.log10(0.5), np.log10(200.0), 400)
res = ph.sdof_mobility_result(f, mass=2.0, stiffness=8000.0, damping=5.0)
z = res.to("impedance")                        # impedancia = 1/Y por frecuencia
print(res.frequencies[int(np.argmax(res.magnitude))].round(1))   # ~10.1 Hz
```

<details>
<summary>Mostrar el código de esta figura</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

m, k, c = 2.0, 8000.0, 5.0
f = np.logspace(np.log10(0.5), np.log10(200.0), 500)
w = 2.0 * np.pi * f
h = ph.sdof_receptance(f, m, k, c)
for label, frf in (("receptancia |H|", np.abs(h)),
                   ("movilidad |Y|", np.abs(1j * w * h)),
                   ("acelerancia |A|", np.abs(-(w**2) * h))):
    plt.loglog(f, frf / frf.max(), label=label)
plt.axvline(ph.resonance_frequency(m, k), ls="--", color="0.6")
plt.xlabel("Frecuencia [Hz]"); plt.ylabel("Magnitud normalizada")
plt.legend(); plt.show()
```

</details>

---

**Normas.** ISO 7626-1:2011, *Mechanical vibration and shock — Experimental
determination of mechanical mobility — Part 1: Basic terms and definitions, and
transducer specifications* — la familia de FRF y sus recíprocas (Tabla 1), la
distinción punto de excitación / transferencia y el resonador de referencia de
un grado de libertad (Anexo A). La conformidad se ancla en las identidades en
forma cerrada del SDOF: el máximo de movilidad en el punto de excitación
`|Y(ω0)| = 1/c`, la receptancia estática `H(0) = 1/k` y la reciprocidad exacta
de la Tabla 1 `impedancia·movilidad = 1`.

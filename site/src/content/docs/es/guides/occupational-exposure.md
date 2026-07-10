---
title: "Exposición al ruido en el trabajo (ISO 9612)"
description: "Las estrategias de medición basada en tareas, basada en la función y de jornada completa de la ISO 9612 para el nivel de exposición diario LEX,8h, con el presupuesto de incertidumbre del anexo C y el límite superior unilateral al 95 %."
---

Una jornada laboral rara vez se mide de una sola toma: el nivel de exposición
diario sobre el que actúa la normativa hay que componerlo a partir de
*muestras* de un turno real, y declararlo con una incertidumbre que un
higienista pueda defender. `lex_8h` (en
[Niveles](/phonometry/es/guides/levels/)) convierte *una* grabación en un nivel
diario. La ISO 9612:2009 —el método de ingeniería (clase de exactitud 2)— es el
diseño de la medición *en torno* a esa primitiva: cómo muestrear una jornada
laboral real, cómo combinar las partes y cómo adjuntar la incertidumbre
normativa que necesita todo informe de higiene laboral. El módulo
`occupational_exposure` añade las tres **estrategias de medición** y el
presupuesto de incertidumbre del **anexo C** sobre la maquinaria del promediado
en energía.

## 1. Las tres estrategias de medición (apartados 9-11)

La estrategia *basada en tareas* (apartado 9) divide la jornada nominal en
tareas, toma $I \ge 3$ muestras por tarea y suma en energía las contribuciones de
cada tarea

$$
L_{EX,8h,m} = L_{p,A,eqT,m} + 10 \log_{10}(T_m/T_0), \qquad T_0 = 8\ \text{h},
$$

de modo que una tarea ruidosa pero corta contribuye poco. Las estrategias
*basada en la función* (apartado 10) y *de jornada completa* (apartado 11) toman
en cambio $N \ge 5$ (o tres jornadas completas) muestras aleatorias sobre un grupo
de exposición homogéneo y normalizan la duración efectiva de la jornada. El nivel
diario es el mismo en ambos casos; las estrategias difieren en cómo se construye
la **incertidumbre**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/exposure_uncertainty_es.png" alt="Exposición por tareas del anexo D de la ISO 9612: las tres contribuciones de tarea a LEX,8h como barras, la línea del LEX,8h diario sumado en energía y la banda del límite superior unilateral al 95 % LEX,8h + U por encima" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/exposure_uncertainty_es_dark.png" alt="Exposición por tareas del anexo D de la ISO 9612: las tres contribuciones de tarea a LEX,8h como barras, la línea del LEX,8h diario sumado en energía y la banda del límite superior unilateral al 95 % LEX,8h + U por encima" style="width:80%">

```python
from phonometry.occupational_exposure import (
    Task, task_based_exposure, job_based_exposure, full_day_exposure,
)

# ISO 9612 anexo D — la jornada de un soldador dividida en tres tareas. El nivel
# de cada tarea es el promedio en energía de sus muestras Lp,A,eqT; las
# duraciones llevan un rango medido.
tasks = [
    Task(samples=(70.0,), duration_hours=1.5, label="planning/breaks"),
    Task(samples=(80.1, 82.2, 79.6), duration_hours=5.0,
         duration_range=(4.0, 6.0), label="welding"),
    Task(samples=(86.5, 92.4, 89.3, 93.2, 87.8, 86.2), duration_hours=1.5,
         duration_range=(1.0, 2.0), label="cutting/grinding"),
]
res = task_based_exposure(tasks, include_duration_uncertainty=False, warn=False)
print(f"LEX,8h = {res.lex_8h:.1f} dB   U = {res.expanded_uncertainty:.1f} dB")
# LEX,8h = 84.3 dB   U = 2.7 dB
print(f"one-sided 95 % upper limit LEX,8h + U = {res.upper_limit:.1f} dB")   # 87.0 dB
for t in res.tasks:
    print(f"  {t.label:<16} Lp,A,eqT = {t.lp_aeqt:5.1f}   contributes {t.lex_8h_contribution:5.1f} dB")
#   planning/breaks  Lp,A,eqT =  70.0   contributes  62.7 dB
#   welding          Lp,A,eqT =  80.8   contributes  78.7 dB
#   cutting/grinding Lp,A,eqT =  90.1   contributes  82.8 dB

# La misma jornada medida basada en la función (anexo E) y de jornada completa
# (anexo F): ambas usan el presupuesto de muestreo Ec C.9 / Tabla C.4 con
# k = 1.65 (unilateral 95 %).
job = job_based_exposure([88.1, 86.1, 89.7, 86.5, 91.1, 86.7], effective_duration_hours=7.5)
full = full_day_exposure([88.0, 91.9, 87.6, 90.4, 89.0, 88.4], effective_duration_hours=9.25)
print(f"job      LEX,8h = {job.lex_8h:.1f} dB   U = {job.expanded_uncertainty:.1f} dB")
# job      LEX,8h = 88.2 dB   U = 3.8 dB
print(f"full-day LEX,8h = {full.lex_8h:.1f} dB   U = {full.expanded_uncertainty:.1f} dB")
# full-day LEX,8h = 90.1 dB   U = 3.4 dB
```

## 2. El presupuesto de incertidumbre del anexo C

Conviene detallar dos sutilezas. Primero, el factor de cobertura es $k = 1.65$
para un intervalo **unilateral** al 95 % (apartado 14), porque al higienista solo
le importa la cota *superior*: `res.upper_limit` = $L_{EX,8h} + U$ es el valor por
debajo del cual queda el 95 % de las mediciones, el número que se compara con un
valor de acción. Segundo, los métodos por tareas y por función ponderan de forma
distinta la *misma* dispersión de muestras. La incertidumbre de muestreo de la
tarea $u_{1a}$ (Ec. C.6) divide la suma de desviaciones al cuadrado entre
$I(I-1)$ —el error típico de la media, menor en un factor $\sqrt{I}$—, mientras
que la incertidumbre de muestreo por función/jornada completa $u_1$ (Ec. C.12) es
la desviación típica muestral simple con denominador $N-1$, cuya contribución
$c_1 u_1$ se lee luego de la **Tabla C.4** en función de $(N, u_1)$. La misma
dispersión bruta infla, por tanto, más la estimación por función, que es la
penalización que el estándar impone a un muestreo más grueso y con menos
muestras. (El $L_{EX,8h}$ por función impreso es $88.2$ dB donde el anexo E
declara $88.1$: el estándar redondea el nivel de jornada efectiva a $88.4$ antes
de la normalización de la duración; la biblioteca lo mantiene sin redondear.)

Cuando las muestras de una tarea abarcan **3 dB o más** (apartado 9.3), o la
contribución por función $c_1 u_1$ supera 3,5 dB (apartado 10.4), o se cubren
demasiado pocos trabajadores (duración acumulada de la Tabla 1), el resultado fija
`sampling_advisory=True` y, con `warn=True`, emite una `OccupationalExposureWarning` que
recomienda más mediciones. Los niveles de pico $L_{p,Cpeak}$ se declaran **sin**
incertidumbre —el anexo C no da método para ellos (Tabla C.5, Nota 1)—, así que
la incertidumbre de pico queda fuera del alcance. Los tres ejemplos resueltos de
los anexos D/E/F anteriores se reproducen con la precisión impresa de la norma
(el redondeo final del anexo E se explica más arriba), y la teoría se deriva
en la página de [Teoría](/phonometry/es/reference/theory/).

### Parámetros de `task_based_exposure()` / `job_based_exposure()` / `full_day_exposure()`

| Parámetro | Se aplica a | Tipo | Unidades | Rango / def. | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tasks` | tarea | lista de `Task` | — | ≥ 1 | Cada `Task` tiene `samples`, `duration_hours`, `duration_range`/`duration_samples` opcionales, `label`, `instrument` |
| `samples` | función / jornada | secuencia | dB | ≥ 2 (≥ 5 / ≥ 3 recomendado) | Muestras aleatorias `Lp,A,eqT` |
| `effective_duration_hours` | función / jornada | float | h | > 0 | Duración efectiva de la jornada $T_e$ |
| `instrument` | todas | str | — | `'class1'`, `'class2'`, `'personal_exposimeter'` (def.) | Selecciona $u_2$ (Tabla C.5) |
| `u3` | todas | float | dB | def. `1.0` | Incertidumbre de posición del micrófono (apartado C.6) |
| `include_duration_uncertainty` | tarea | bool | — | def. `True` | `False` omite el término $(c_{1b}u_{1b})^2$ (anexo D caso a) |
| `n_workers` / `sample_duration_hours` | función | int / float | — / h | def. `None` | Comprobación de duración acumulada de la Tabla 1 |
| `warn` | todas | bool | — | def. `True` | Emitir `OccupationalExposureWarning` para los avisos de muestreo |

Las tres devuelven un `ExposureResult` con `lex_8h`, `combined_standard_uncertainty`
$u$, `expanded_uncertainty` $U = 1.65\ u$, `upper_limit` = $L_{EX,8h} + U$,
`sampling_advisory` y (basada en tareas) el desglose por tarea en `tasks`.

## Véase también

- [Niveles](/phonometry/es/guides/levels/) — las primitivas de dosis `lex_8h` /
  `sound_exposure` (IEC 61252) y el LCpeak que estas estrategias declaran al
  lado.
- [Incertidumbre de medición](/phonometry/es/guides/gum-uncertainty/) — la
  maquinaria GUM tras las incertidumbres combinadas y expandidas.
- [Teoría](/phonometry/es/reference/theory/) — la derivación de las fórmulas de
  las estrategias y del presupuesto del anexo C.

---

**Normas.** ISO 9612:2009, *Acoustics — Determination of occupational noise
exposure — Engineering method* — las estrategias basada en tareas (apartado 9),
basada en la función (apartado 10) y de jornada completa (apartado 11), el
presupuesto de incertidumbre del anexo C (Ecuaciones C.6, C.9 y C.12, Tablas
C.4/C.5) y el factor de cobertura unilateral k = 1,65 (apartado 14), validado
frente a los ejemplos resueltos de los anexos D, E y F.

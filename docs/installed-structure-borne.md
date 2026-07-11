← [Documentation index](README.md)

# Installed structure-borne sound from equipment (EN 12354-5)

**EN 12354-5:2009** predicts the sound pressure level in a receiving room caused
by building service equipment (pumps, fans, lifts, water installations) that
injects **structure-borne sound** into the building. It closes the
structural-vibroacoustics chain: the source is described by its characteristic
structure-borne sound power level `L_Ws,c` ([EN 15657](structure-borne-power.md)),
the source and receiver point mobilities set how much power is actually coupled
into the structure, and the building transmission carries it to the receiving
room.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/installed_structure_borne_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/installed_structure_borne.svg" alt="The EN 12354-5 cascade per octave band: the characteristic structure-borne power level, the installed power level after subtracting the coupling term, the per-path normalised sound pressure levels, and their energetic total" width="82%"></picture>

## 1. Coupling and installed power

Only part of the characteristic power is injected into the supporting element;
the loss is the **coupling term** `D_C` (always positive), set for a point
excitation by the source mobility `Y_s` and the receiver mobility `Y_i`
(Formula 19b):

$$
D_{C,i} = 10\lg\frac{|Y_s + Y_i|^2}{|Y_s|\,\mathrm{Re}\{Y_i\}},
$$

which reduces to `10 lg(|Y_s|/Re{Y_i})` for a **force source** (high source
mobility, Formula 19c) and to `−10 lg(|Y_s|·Re{Z_i})` for a **velocity source**
(low source mobility, Formula 19d); an elastic support adds its transfer
mobility `Y_k` inside the modulus (Formula 19e). The **installed** power level is
then (Formula 18b) `L_Ws,inst = L_Ws,c − D_C`.

```python
import phonometry as ph

# A near-force source (Y_s >> Y_i) on a concrete floor:
dc = ph.coupling_term(2e-4 + 1e-4j, 3e-5 + 1e-5j)
print(round(float(dc), 2))                                          # ~8.5 dB
print(round(float(ph.installed_structure_borne_power_level(82.0, dc)), 1))  # installed L_Ws
```

## 2. Transmission to the receiving room

Each transmission path `i→j` gives a normalised sound pressure level from the
installed power, the structure-to-airborne adjustment term `D_sa`, the flanking
sound reduction index `R_ij,ref` (EN 12354-1) and the element area (Formula 18a):

$$
L_{n,s,ij} = L_{Ws,\mathrm{inst},i} - D_{sa,i} - R_{ij,\mathrm{ref}}
             - 10\lg\frac{S_i}{S_0} - 10\lg\frac{A_0}{4},
$$

with `S₀ = A₀ = 10 m²`, and the paths combine energetically (Formula 17):

```python
import numpy as np
import phonometry as ph

bands = np.array([250.0, 500.0, 1000.0])
res = ph.installed_source_prediction(
    characteristic_power_level=np.array([80.0, 82.0, 78.0]),
    coupling_term=np.array([9.0, 10.0, 11.0]),
    paths=[
        {"adjustment_term": 5.0,
         "flanking_reduction_index": np.array([50.0, 52.0, 55.0]), "element_area": 12.0},
        {"adjustment_term": 6.0,
         "flanking_reduction_index": np.array([52.0, 54.0, 57.0]), "element_area": 8.0},
    ],
    frequencies=bands,
)
print(np.round(res.total_level, 1))      # total L_n,s per band
print(round(res.overall_level, 1))       # band-summed level [dB]
```

The `InstalledSourceResult` carries the per-path levels, the total per band, the
installed power level and `.overall_level`, and its `.plot()` draws the whole
cascade.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

bands = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
lws_c = np.array([78.0, 82.0, 84.0, 81.0, 77.0, 72.0, 66.0])
ys = (2e-4 + 1e-4j) * (bands / 250.0); yi = (3e-5 + 1e-5j) * np.ones_like(bands)
dc = np.array([float(ph.coupling_term(a, b)) for a, b in zip(ys, yi)])
paths = [{"adjustment_term": 6.0,
          "flanking_reduction_index": np.linspace(44, 62, 7), "element_area": 12.0}]
res = ph.installed_source_prediction(lws_c, dc, paths, frequencies=bands)
res.plot(); plt.show()
```

</details>

---

**Standards.** EN 12354-5:2009, *Building acoustics — Estimation of acoustic
performance of buildings from the performance of elements — Part 5: Sound levels
due to service equipment*: the coupling term (clause 4.4.3, Formulae 19a-19e),
the installed structure-borne power level (Formula 18b), the structure-to-
airborne adjustment term (clause 4.4.4, Formulae 20a/20b), and the normalised
sound pressure level per path and its energetic combination (Formulae 18a, 17).
Conformance is anchored on the coupling-term force-source limit, the installed-
power identity and the area/absorption terms of Formula 18a. `D_sa` and
`R_ij,ref` are inputs (from measurement / EN 12354-1 / Annexes D and F).

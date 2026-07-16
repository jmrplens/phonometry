---
title: "Installed structure-borne sound (EN 12354-5)"
description: "The EN 12354-5:2009 prediction of the sound pressure level in a receiving room from building service equipment injecting structure-borne sound: the coupling term D_C from source and receiver mobilities (Formula 19b-e), the installed power L_Ws,inst = L_Ws,c − D_C (Formula 18b), and the per-path normalised SPL with its energetic total (Formulae 18a/17)."
---

**EN 12354-5:2009** predicts the sound pressure level in a receiving room caused
by building service equipment (pumps, fans, lifts, water installations) that
injects **structure-borne sound** into the building. It closes the
structural-vibroacoustics chain: the source is described by its characteristic
structure-borne sound power level `L_Ws,c`, derived from the EN 15657
reception-plate measurement through the Formula (15)/(17) conversion and a
mobility correction (**not** the raw plate-injected level;
see [EN 15657](/phonometry/guides/structure-borne-power/)); the source and
receiver point mobilities set how much power is actually coupled into the
structure, and the building transmission carries it to the receiving room. The
Annex I mobility correction `installed_power_from_reception_plate` refers the
characteristic reception-plate level `L_Ws,n` to the actual receiver,
`L_Ws,inst = L_Ws,n + 10 lg(Y_∞,i / Y_∞,rec)` with `Y_∞,rec = 5·10⁻⁶ m/(N·s)`;
with the source mobility instead it yields `L_Ws,c` (Annex I.3, Table I.8).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/installed_structure_borne.svg" alt="The EN 12354-5 cascade per octave band: characteristic power, installed power after the coupling term, per-path sound pressure levels and their energetic total" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/installed_structure_borne_dark.svg" alt="The EN 12354-5 cascade per octave band: characteristic power, installed power after the coupling term, per-path sound pressure levels and their energetic total" style="width:82%">

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

EN 12354 parts 1 and 2 handle rooms excited through the air and by the
standard tapping machine; part 5 covers the sources that shake the building
*directly*: pumps, fans, lifts, whirlpool baths, cisterns and the pipework
that ties them into walls and floors. Once the installed power is in the
structure, several elements radiate into the receiving room: the excited
element itself and every element the vibration reaches across the junctions.
Each excited-element/radiating-element pair `i→j` is a transmission path with
its own adjustment term and flanking index:

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_installed_paths.svg" alt="EN 12354-5 installation paths: a pump on resilient mounts injects structure-borne power into the floor slab, the excited floor radiates into the receiving room below, a second path travels along the slab into the flanking wall, and the prediction cascade runs from the characteristic power to the normalised sound pressure level" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_installed_paths_dark.svg" alt="EN 12354-5 installation paths: a pump on resilient mounts injects structure-borne power into the floor slab, the excited floor radiates into the receiving room below, a second path travels along the slab into the flanking wall, and the prediction cascade runs from the characteristic power to the normalised sound pressure level" style="width:92%">

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

## References

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3rd ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  The source-receiver mobility coupling and the structure-borne transmission
  across junctions behind the coupling term and the path model.

---

**Standards.** EN 12354-5:2009, *Building acoustics — Estimation of acoustic
performance of buildings from the performance of elements — Part 5: Sound levels
due to service equipment*: the coupling term (clause 4.4.3, Formulae 19a-19e),
the installed structure-borne power level (Formula 18b), the structure-to-
airborne adjustment term (clause 4.4.4, Formulae 20a/20b), and the normalised
sound pressure level per path and its energetic combination (Formulae 18a, 17).
Conformance is anchored on the coupling-term force-source limit and the
standard's own Annex I worked examples: the whirlpool bath of I.2
(Table I.6a: mobility correction and path 11) and the flushing cistern of I.3
(Tables I.8/I.9: source conversion, all four transmission paths, the
Formula 17 total and its 29 dB(A) closure), within the ±0.15 dB rounding of
the printed one-decimal intermediates. `D_sa` and `R_ij,ref` are inputs (from
measurement / EN 12354-1 / Annexes D and F).

## See also

- API reference: [`building.installed_structure_borne`](/phonometry/reference/api/building/installed-structure-borne/).

← [Documentation index](../../README.md)

# Dynamic stiffness of resilient materials (EN 29052-1)

A **floating floor** is a heavy floating slab resting on a resilient layer; the
two form a mass-spring system whose **natural frequency** governs how much the
floor improves impact and airborne insulation. **EN 29052-1:1992** (identical to
ISO 9052-1:1989) measures the **dynamic stiffness per unit area** $s'$ of the
resilient layer from the resonance of a standard load plate on a
200 mm × 200 mm specimen. $s'$ is the input to the floating-floor term of the
EN 12354-2 impact model covered in
[Predicting Sound Insulation (EN 12354)](../../buildings/design/insulation-prediction.md). (ISO 16251-1 does not apply here:
its scope is limited to soft, locally-reacting floor coverings and explicitly
excludes floating floors.)

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness.svg" alt="Floating-floor natural frequency as a function of the resilient layer's dynamic stiffness per unit area, for a light 40 kg/m² and a heavy 120 kg/m² floating floor, on a logarithmic stiffness axis, with a worked design point at 10 MN/m³ marked" width="82%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import materials

# One line — from a measured resonance, the result draws its own f0(s')
# design curve with the determination marked:
res = materials.floating_floor_resonance(
    resonant_frequency_hz=25.0, total_mass_per_area_kg_m2=200.0,
    floor_mass_per_area_kg_m2=120.0,
    airflow_resistivity_kpa_s_m2=50.0, thickness_m=0.020, porosity=0.9,
)
res.plot()
plt.show()

# By hand, the same design curve for a light and a heavy floating floor:
s = np.logspace(np.log10(2.0), np.log10(100.0), 300)   # MN/m3
for m in (40.0, 120.0):
    plt.semilogx(s, materials.natural_frequency(s * 1e6, m), label=f"m' = {m:g} kg/m²")
plt.xlabel("Dynamic stiffness s' [MN/m³]"); plt.ylabel("Natural frequency f₀ [Hz]")
plt.legend(); plt.show()
```

</details>

## 1. Dynamic stiffness and resonance

The dynamic stiffness per unit area is a dynamic force per area divided by the
resulting change in thickness (Formula 1): $s' = (F/S)/\Delta d$. The resiliently
supported floor is a resonator whose natural frequency (Formula 2) and,
in the laboratory arrangement, measured resonant frequency (Formula 3) are

$$
f_0 = \frac{1}{2\pi}\sqrt{\frac{s'}{m'}}, \qquad
f_\mathrm{r} = \frac{1}{2\pi}\sqrt{\frac{s'_\mathrm{t}}{m'_\mathrm{t}}},
$$

so the **apparent** dynamic stiffness follows from the resonance (Formula 4):

$$
s'_\mathrm{t} = 4\pi^2\,m'_\mathrm{t}\,f_\mathrm{r}^2 .
$$

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_dynamic_stiffness_rig_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_dynamic_stiffness_rig.svg" alt="EN 29052-1 resonance rig in three panels: the three excitation arrangements of Figures 1 to 3, one on a rigid foundation with the load plate driven and measured, two on an isolated baseplate of at least 100 kg where both plates are measured and the exciter drives either the load plate or the baseplate; below, the specimen and load requirements with the plaster bed, the steel load plate and the petroleum-jelly fillet, and the mass-spring model whose response peak gives the resonant frequency" width="92%"></picture>

In the test arrangement the specimen lies between the rigid foundation and a
load plate whose total mass per unit area, plate plus added load, is
200 kg/m² (8 kg on the 0.04 m² specimen). That load reproduces the static
preload of a typical floating floor, about 2 kPa. A vertical exciter drives
the plate, an accelerometer picks up its response, and the fundamental
vertical resonance $f_\mathrm{r}$ of the plate-on-specimen system is read from the
response peak; Formula 4 turns it into $s'_\mathrm{t}$. That extraction is the
laboratory's: the Clause 7 procedures for reading $f_\mathrm{r}$ from the raw
excitation-response signal (sinusoidal, white-noise or pulse excitation,
with the extrapolation to zero force amplitude) are not implemented, and
`apparent_dynamic_stiffness` expects the already-extrapolated $f_\mathrm{r}$.

```python
from phonometry import materials

# Standard 8 kg load plate on the 0.04 m2 specimen -> m't = 200 kg/m2;
# the fundamental resonance is measured at 25 Hz.
s_t = materials.apparent_dynamic_stiffness(resonant_frequency_hz=25.0, total_mass_per_area_kg_m2=200.0)
print(round(s_t / 1e6, 3))                              # 4.935  MN/m3

# Installed on a 120 kg/m2 floating screed with s' = 10 MN/m3:
print(round(materials.natural_frequency(10e6, 120.0), 1))      # 45.9  Hz
```

That little oscillator is small enough to draw at true scale.
`plot_dynamic_stiffness_rig` puts the standard 200 mm specimen under the 8 kg
load plate with the exciter and accelerometer in place.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness_rig_geometry_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/dynamic_stiffness_rig_geometry.svg" alt="To-scale section of the dynamic-stiffness rig: the dotted 200 mm resilient specimen, 20 mm thick, on the hatched rigid foundation, the grey 8 kg load plate on top with the accelerometer ball at its edge, and the exciter block above driving the plate through a red vertical arrow, the specimen side and thickness dimensioned" width="92%"></picture>

*The mass-spring system behind $s'$ at true scale: 20 mm of resilient layer
under the 8 kg plate is all it takes to reproduce the 2 kPa preload of a
floating floor.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import materials

# The standard rig: a 200 mm square specimen under the 8 kg load plate.
materials.plot_dynamic_stiffness_rig()
plt.show()
```

</details>

## 2. The enclosed-gas term and airflow resistivity

For an air-permeable material the enclosed pore air adds a parallel stiffness
from its isothermal compression (Formula 7):
$s'_\mathrm{a} = p_0/(d\,\varepsilon)$, with $p_0$ the atmospheric pressure, $d$ the
loaded thickness and $\varepsilon$ the porosity. The standard's worked NOTE
($p_0 = 0.1\ \text{MPa}$, $\varepsilon = 0.9$) is $s'_\mathrm{a} = 111/d$ MN/m³ for
$d$ in millimetres:

```python
from phonometry import materials

print(round(materials.enclosed_gas_stiffness(thickness_m=0.020, porosity=0.9) / 1e6, 2))
# 5.56  MN/m3   (the NOTE's 111/20 = 5.55 MN/m3)
```

The dynamic stiffness of the *installed* material is then set by the lateral
airflow resistivity $r$ (clause 8.2): $s' = s'_\mathrm{t}$ for
$r \ge 100\ \text{kPa}\cdot\text{s/m}^2$, $s' = s'_\mathrm{t} + s'_\mathrm{a}$ for
$10 \le r < 100\ \text{kPa}\cdot\text{s/m}^2$, and for
$r < 10\ \text{kPa}\cdot\text{s/m}^2$ the method only resolves $s' = s'_\mathrm{t}$
when the gas term is negligible. The resistivity is in kPa·s/m², the unit the
standard thresholds it in and a thousand times the Pa·s/m² ISO 9053 reports,
so it is passed by name, `airflow_resistivity_kpa_s_m2`, with the unit on the
line. `floating_floor_resonance` chains the whole determination:

```python
from phonometry import materials

res = materials.floating_floor_resonance(
    resonant_frequency_hz=25.0, total_mass_per_area_kg_m2=200.0,
    floor_mass_per_area_kg_m2=120.0,
    airflow_resistivity_kpa_s_m2=50.0, thickness_m=0.020, porosity=0.9,
)
print(round(res.dynamic_stiffness / 1e6, 2), round(res.natural_frequency, 1))
# 10.49 47.1

res.plot()   # the f0(s') design curve with this determination marked (needs matplotlib)
```

The `DynamicStiffnessResult` carries the apparent, enclosed-gas and installed
stiffnesses, the test resonance and the installed-floor natural frequency, and
its `.plot()` draws the $f_0(s')$ design curve.

**Test-report fiche.** `DynamicStiffnessResult.report(path)` renders a one-page
accredited dynamic-stiffness test report (EN 29052-1:1992 = ISO 9052-1:1989): a
metadata header (specimen, the total mass per unit area $m'_\mathrm{t}$, the loaded
thickness $d$ in metres shown in mm, test facility, climate), a metrics table (the resonant frequency
$f_\mathrm{r}$, the apparent stiffness $s'_\mathrm{t}$ of Formula 4, the enclosed-gas term $s'_\mathrm{a}$
when it applies, the installed $s'$ of clause 8.2 and the natural frequency
$f_0$ of Formula 2) beside the $f_0(s')$ design curve, and a boxed apparent
dynamic stiffness $s'_\mathrm{t}$ (no pass/fail). Clause 9 rounds every stiffness to the
nearest MN/m³; `language="es"` renders the Spanish fiche. The fiche always
embeds the $f_0(s')$ design curve, so it needs both the report and plot extras
(`pip install "phonometry[report,plot]"`). Clause 6's specimen selection (at
least three 200 mm × 200 mm specimens) is not enforced, and neither is the
Clause 9 report content: the fiche carries the excitation arrangement and the
signal type only when the metadata supplies them.

```python
from phonometry import ReportMetadata, materials

res = materials.floating_floor_resonance(
    resonant_frequency_hz=45.0, total_mass_per_area_kg_m2=200.0,
    floor_mass_per_area_kg_m2=110.0,
    airflow_resistivity_kpa_s_m2=50.0, thickness_m=0.020, porosity=0.9,
)
res.report(
    "dynamic_stiffness.pdf",
    metadata=ReportMetadata(
        specimen="20 mm mineral-wool resilient layer",
        mass_per_area=200.0, thickness=0.020,   # thickness d in metres (20 mm)
        measurement_standard="EN 29052-1",
    ),
)   # one-page fiche (needs phonometry[report,plot])
```

[![EN 29052-1 dynamic-stiffness example report: a metadata header with the total mass per unit area and the loaded thickness, a metrics table of the resonant frequency, the apparent, enclosed-gas and installed dynamic stiffnesses and the natural frequency beside the f0(s') design curve, and the boxed apparent dynamic stiffness s't](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/en29052_dynamic_stiffness_example.webp)](https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/reports/en29052_dynamic_stiffness_example.pdf)

### Published layers, when there is no declared value

Designing a floating floor starts from the manufacturer's $s'$, declared to
EN 29052-1 for that product. When there is none, fifteen measured layers are
published as `PUBLISHED_RESILIENT_LAYERS`, transcribed from Hopkins Table A3
(printed p. 610), whose caption states they were measured according to
ISO 9052-1. The column heading prints $s'$, which the book's own list of
symbols defines as the dynamic stiffness of the installed layer and keeps apart
from the apparent $s'_\mathrm{t}$, so every row holds `dynamic_stiffness_n_m3`
and its natural frequency needs nothing but the mass of the floor. Each layer
is a catalogue row like the rows of every other published table: it carries
the page it was read on, and the four rebond foams carry the second-level
attribution the printed cell gives them.

The key is `"<table>/<row>"`, as in every catalogue: the packaged table,
`hopkins-2007-table-a3`, and then which specimen the row is,
`<material>_<density>_<thickness>`, because four rock-wool rows and four
glass-wool rows differ only by those two numbers and the printed table
separates them by position under a name it prints once.

```python
from phonometry import materials

layer = materials.resilient_layer("hopkins-2007-table-a3/mineral_wool_rock_60_30")
print(layer.name, layer.density_kg_m3, layer.thickness_mm)   # Mineral wool, rock 60.0 30.0
print(layer.source)
# Hopkins (2007) Table A3, PDF page 637 (printed p. 610)
print(round(layer.dynamic_stiffness_n_m3 / 1e6, 1))          # 10.0 MN/m3, as printed
print(round(layer.natural_frequency(mass_per_area_kg_m2=120.0), 1))   # 45.9 Hz under a 120 kg/m2 screed

rebond = materials.PUBLISHED_RESILIENT_LAYERS["hopkins-2007-table-a3/rebond_foam_64_20"]
print(rebond.attributed_to["row"])                           # Hopkins and Hall (2006)
print(round(rebond.natural_frequency(mass_per_area_kg_m2=120.0), 1))  # 43.6
```

These are measured specimens and not declared product values: they are the
order of magnitude to reason with while a product is chosen, not an input to a
compliance calculation. The softest row in the table, 40 mm glass wool at
7 MN/m³, puts the same screed at 38.4 Hz, and the stiffest, 5 mm closed-cell
polyethylene foam at 115 MN/m³, at 155.8 Hz; that spread is the whole design
question.

**A layer that gives only $s'_\mathrm{t}$.** A test report to EN 29052-1 gives
the apparent stiffness $s'_\mathrm{t}$ of its specimen and the enclosed-gas
stiffness $s'_\mathrm{a}$, and it gives $s'$ only "if possible" (clause 9 e));
a sheet that quotes $s'_\mathrm{t}$ alone gives less than the report it came
from. Either way $s'_\mathrm{t}$ is not the $s'$ that Formula 2 takes: for an
air-permeable layer the enclosed gas adds to it, and Hopkins notes that it
often forms a significant percentage of $s'$ (printed p. 360). A
`ResilientLayer` built from such a source holds it in
`apparent_dynamic_stiffness_n_m3`, and its `natural_frequency` refuses to go on
until it is given the lateral airflow resistivity, in Pa·s/m² as ISO 9053
reports it, and, below 100 kPa·s/m², the enclosed-gas stiffness: the
$s'_\mathrm{a}$ the report states, or Formula 7 on the thickness under the
test load, which clause 9 b) has the report state as well and which is not the
nominal thickness a product sheet prints. With them it takes the clause 8.2
branch that resistivity picks:

```python
from phonometry import io, materials

report = materials.ResilientLayer(
    name="Example layer",
    source="Example Acoustics Ltd test report 26-014, p. 2",
    apparent_dynamic_stiffness_n_m3=6.0e6,
)
try:
    report.natural_frequency(mass_per_area_kg_m2=120.0)
except io.CatalogueError as refusal:
    print(refusal)
# 'Example layer' gives the apparent dynamic stiffness s't of a test specimen,
# 6 MN/m3, and not the dynamic stiffness s' of the installed layer [...]: pass
# airflow_resistivity_pa_s_m2 and, below 100 kPa.s/m2 (100000 Pa.s/m2),
# gas_stiffness_n_m3, the enclosed-gas stiffness s'a of Formula 7 [...]

# d = 30 mm under the test load, from the report (clause 9 b)); an s'a the
# report states (clause 9 e)) goes in as gas_stiffness_n_m3 the same way.
gas = materials.enclosed_gas_stiffness(thickness_m=0.030, porosity=0.9)   # 3.7 MN/m3
f0 = report.natural_frequency(
    mass_per_area_kg_m2=120.0,
    airflow_resistivity_pa_s_m2=50_000.0,   # 50 kPa.s/m2: Formula 6, s' = s't + s'a
    gas_stiffness_n_m3=gas,
)
print(round(f0, 1))                                              # 45.3 Hz
```

Read as if it were $s'$, the same 6 MN/m³ would have put the screed at
35.6 Hz, almost 10 Hz too low.

## 3. What the resonance method assumes, and where it bites

The evaluation treats the rig as a single-degree-of-freedom system: the load
plate moves as a rigid piston on a massless spring. That holds while the
specimen is light against the plate and its first internal resonance sits
well above $f_\mathrm{r}$; a heavy or very thick layer starts to act as a distributed
system and the simple Formula 4 reading degrades. Three practical pitfalls
follow from the preload:

* **$s'$ is a stiffness *at the standard preload*.** Resilient layers are
  visibly non-linear in static load: mineral wool stiffens as it compresses,
  some foams soften. The 200 kg/m² load plate fixes the operating point, so
  the tabulated $s'$ strictly describes floors near that surface mass.
  Designing a much heavier screed with the same $s'$ extrapolates beyond the
  measurement.
* **Drive small.** The tangent stiffness is defined for small dynamic
  strains; driving the plate hard pushes the layer into its non-linear range
  and shifts the apparent resonance downward. Keep the excitation at the
  lowest level that gives a clean peak.
* **Respect the contact.** The standard seats the load plate on a thin
  bonding layer (a plaster paste) so the full specimen area carries the
  load. A dry, uneven contact concentrates the force, stiffens the response
  locally and biases $f_\mathrm{r}$ upward.

The natural frequency that matters in the end is not the rig's $f_\mathrm{r}$ but the
installed floor's $f_0$ from Formula 2: the floating floor only improves
insulation well above $f_0$, which is why a low $s'$ (a soft layer under a
heavy slab) is the design goal.

## See also

- [Predicting Resilient-Layer Performance](../../buildings/design/resilient-layers.md):
  what the design side does with $s'$, from the mass-spring resonance to the
  improvement laws above it and their weighted single number.
- [Predicting Sound Insulation (EN 12354)](../../buildings/design/insulation-prediction.md):
  the floating-floor term this measurement feeds.
- [Airflow Resistance](../absorbers/airflow-resistance.md): the
  ISO 9053 determination of the lateral resistivity $r$ that clause 8.2 needs,
  reported there as $\sigma$ in Pa·s/m², the unit
  `ResilientLayer.natural_frequency` takes, while
  `airflow_resistivity_kpa_s_m2` is in kPa·s/m².
- [Resilient layers overview](index.md): where this
  measurement sits among the materials guides.
- API reference: [`materials.resilient.dynamic_stiffness`](https://jmrplens.github.io/phonometry/reference/api/materials/dynamic-stiffness/).
- Theory: [Point mobilities and radiation efficiency](../../reference/theory/vibration.md#point-mobilities-and-radiation-efficiency-cremer-5-hopkins-29): the mass-spring resonance the EN 29052-1 rig measures, seen as a mobility.

## References

- Vigran, T. E. (2008). *Building acoustics*. CRC Press.
  ISBN 978-0-415-42853-8.
  [doi:10.1201/9781482266016](https://doi.org/10.1201/9781482266016).
  Floating-floor design and the role of the resilient layer's dynamic
  stiffness in the impact-sound improvement.
- International Organization for Standardization. (1989). *Acoustics —
  Determination of dynamic stiffness — Part 1: Materials used under floating
  floors in dwellings* (ISO 9052-1:1989).
  [iso.org catalogue](https://www.iso.org/standard/16620.html).
  The international original of EN 29052-1, the method this page implements.

## Standards

EN 29052-1:1992 (= ISO 9052-1:1989), *Acoustics — Determination
of dynamic stiffness — Part 1: Materials used under floating floors in
dwellings*: the dynamic stiffness per unit area (Formula 1), the resonance
relations (Formulae 2-4), the enclosed-gas term (Formula 7, clause 8.2 NOTE
$s'_\mathrm{a} = 111/d$ MN/m³) and the airflow-resistivity regimes (clause 8.2, Formulae
5-6). Conformance is anchored on the standard's own numeric NOTE plus
hand-computed closed-form values of the resonance relations.

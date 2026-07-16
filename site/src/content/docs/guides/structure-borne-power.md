---
title: "Structure-borne sound power of equipment (EN 15657)"
description: "The EN 15657:2018 reception-plate method for building service equipment: the plate-injected power L_Ws = 10 lg(2πfηmS) + L_v − 60 dB (Formula 14), and the plate-independent source quantities: equivalent blocked force (Formula 15), characteristic reception-plate power level (Formula 17), free velocity and source mobility (Formulae 18/19)."
---

Building service equipment — pumps, fans, boilers, sanitary appliances —
injects **structure-borne sound power** into the building structure it is fixed
to, which then re-radiates as airborne noise in adjoining rooms. **EN 15657:2018**
measures it with the **reception-plate method**: the source is mounted on a
plate of known mass per unit area `m` and area `S` whose structural loss factor
`η` is known, and the plate's spatial-average vibratory velocity is measured.
Formula (14) gives the power *injected into that particular plate*; the
plate-independent source quantities (the equivalent blocked force,
Formula 15; the characteristic reception-plate power level `L_Wsn`,
Formula 17; and the equivalent free velocity and source mobility,
Formulae 18/19) are derived from it and are what the EN 12354-5
installed-equipment prediction consumes.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/structure_borne_power.svg" alt="Reception-plate structure-borne sound power level per one-third-octave band determined on a low-mobility and a high-mobility reception plate" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/structure_borne_power_dark.svg" alt="Reception-plate structure-borne sound power level per one-third-octave band determined on a low-mobility and a high-mobility reception plate" style="width:82%">

## 1. The reception-plate relations

Why a plate at all? Characterising the source by its contact forces directly
would mean instrumenting every fixing point in up to six components each
(three forces, three moments), on a machine that must keep running normally.
The reception plate sidesteps the whole contact problem: let the source run
on a resonant plate whose dissipation is known, wait for the steady state,
and then the power the plate dissipates equals the power the source injects,
over all contacts and components at once. One spatial average of the plate
velocity replaces the entire force-measurement problem.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_reception_plate.svg" alt="EN 15657 reception plate: the source machine standing on a resiliently supported plate, accelerometers averaging the plate velocity, and the plate power balance converting the velocity level into the injected structure-borne power level" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_reception_plate_dark.svg" alt="EN 15657 reception plate: the source machine standing on a resiliently supported plate, accelerometers averaging the plate velocity, and the plate power balance converting the velocity level into the injected structure-borne power level" style="width:92%">

The power a resonant plate dissipates is `P = ω·η·(m·S)·⟨v²⟩`, so the injected
power level in one-third-octave bands is (Formula 14)

$$
L_{Ws} = 10\lg\!\left(\frac{2\pi f\,\eta\,m\,S}{f_0\,m_0\,S_0}\right)
         + L_v - 60 \;\;[\mathrm{dB\ re\ 1\ pW}],
$$

with references `f₀ = 1 Hz`, `m₀ = 1 kg`, `S₀ = 1 m²`; the `−60 dB` term is
`10 lg(v₀²/P₀)` for the EN 15657 velocity reference `v₀ = 10⁻⁹ m/s`. The plate
velocity is the energetic spatial average over the `N` positions (Formula 12)
and the loss factor comes from the structural reverberation time `Ts` (Formula
13, identical to the ISO 10848 total loss factor):

$$
L_v = 10\lg\!\Big(\tfrac{1}{N}\textstyle\sum 10^{L_{v,i}/10}\Big), \qquad
\eta = \frac{2.2}{f\,T_s}.
$$

```python
import numpy as np
import phonometry as ph

bands = np.array([100.0, 200.0, 400.0, 800.0])
lv_i = np.array([88.0, 90.0, 87.0, 89.0, 86.0, 90.0])   # six plate positions @ 200 Hz
print(round(ph.spatial_mean_velocity_level(lv_i), 2))    # 88.6 dB re 1 nm/s

# Power level injected into the reception plate (loss factor from Ts):
res = ph.reception_plate_power(
    velocity_level=np.array([90.0, 87.0, 82.0, 77.0]),
    frequency=bands, mass_per_area=600.0, area=2.0, reverberation_time=0.8,
)
print(np.round(res.power_level, 1))     # per-band L_Ws
print(round(res.total_level, 1))        # band-summed level [dB re 1 pW]
```

## 2. Low- and high-mobility plates

Two reception plates bracket the installation conditions. On the *low-mobility*
(heavy) plate the source's own dynamics barely change the plate's point mobility
or loss factor; the *high-mobility* (light) plate is dynamically loaded by the
source, so its reverberation time and mobility are measured with the source
attached. The plate-injected power plus the plate's point mobility (see
[mechanical mobility](/phonometry/guides/mechanical-mobility/)) yield the
source description for the EN 12354-5 model through the conversion chain below.

## 3. From plate power to source quantities (Formulae 15–19)

The plate-injected `L_Ws` is **not** a source descriptor: the same source
injects a different power into a different receiver. EN 15657 derives the
plate-independent quantities: the **equivalent blocked force level**
(Formula 15, re `F₀ = 10⁻⁶ N`) from the low-mobility plate,

$$
L_{Fb,eq} = L_{Ws,\mathrm{low}} - 10\lg\frac{\mathrm{Re}\{Y_{R,\mathrm{low,eq}}\}}{Y_0},
$$

the **characteristic reception-plate power level** that EN 12354-5 consumes
(Formula 17), referred to the standard 10 cm concrete plate of characteristic
mobility `Y_R,∞,low = 5·10⁻⁶ m/(N·s)` (clause 7.2.4),

$$
L_{Wsn} = L_{Fb,eq} + 10\lg\frac{Y_{R,\infty,\mathrm{low}}}{Y_0},
$$

and, from the high-mobility plate, the **equivalent free velocity level**
(Formula 18, re `10⁻⁹ m/s`) and the **source mobility** `|Y_S,eq|`
(Formula 19). The EN 12354-5 Annex I mobility correction
(`installed_power_from_reception_plate`, see
[installed structure-borne sound](/phonometry/guides/installed-structure-borne/))
then refers `L_Wsn` to the actual receiving element.

```python
import phonometry as ph

# EN 12354-5 Annex I.3 (flushing cistern, wall contact, 63 Hz): measured on a
# plate of Y = 5.34e-6 m/(N·s); the wall's characteristic mobility is 24.1e-6.
lfb = ph.equivalent_blocked_force_level(61.7, 5.34e-6)      # Formula (15)
lwsn = ph.characteristic_reception_plate_power(lfb)         # Formula (17)
inst = ph.installed_power_from_reception_plate(lwsn, 24.1e-6)  # Annex I
print(round(float(lwsn), 1), round(float(inst), 1))         # 61.4 68.2  (Table I.8)

# Free velocity (Formula 18) + blocked force close the source mobility (19):
lvf = ph.equivalent_free_velocity_level(70.0, 1.0e-2)
print(float(ph.source_mobility_from_levels(lvf, lfb)))      # |Y_S,eq| in m/(N·s)
```

The direct source-side counterpart is the ISO 9611 free velocity level (re
`v₀ = 5·10⁻⁸ m/s`) measured at the contact points of resiliently mounted
machinery; its equation (9) position average is `mean_free_velocity_level()`.

<details>
<summary>Show the code for this figure</summary>

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
plt.bar(x - 0.2, low.power_level, width=0.4, label="low-mobility plate")
plt.bar(x + 0.2, high.power_level, width=0.4, label="high-mobility plate")
plt.xticks(x, [f"{b:g}" for b in bands]); plt.legend()
plt.xlabel("Frequency [Hz]"); plt.ylabel("$L_{Ws}$ [dB re 1 pW]"); plt.show()
```

</details>

## References

- Cremer, L., Heckl, M., & Petersson, B. A. T. (2005). *Structure-borne
  sound: Structural vibrations and sound radiation at audio frequencies*
  (3rd ed.). Springer. ISBN 978-3-540-22696-3.
  [doi:10.1007/b137728](https://doi.org/10.1007/b137728).
  The plate power balance and the source-receiver mobility framework behind
  the reception-plate method and its Formula 15-19 source quantities.
- International Organization for Standardization. (1996). *Acoustics —
  Characterization of sources of structure-borne sound with respect to sound
  radiation from connected structures — Measurement of velocity at the
  contact points of machinery when resiliently mounted* (ISO 9611:1996).
  [iso.org catalogue](https://www.iso.org/standard/17424.html).
  The free-velocity source characterization that complements the
  reception-plate quantities.

## Standards

EN 15657:2018, *Acoustic properties of building elements and
buildings — Laboratory measurement of structure-borne sound from building
service equipment for all installation conditions*: the reception-plate method
(clause 7), the spatial mean velocity level (Formula 12), the plate loss factor
`η = 2.2/(f·Ts)` (Formula 13), the plate-injected power level `L_Ws`
(Formula 14) and the source-quantity chain: equivalent blocked force
(Formula 15), characteristic reception-plate power level (Formula 17,
`Y_R,∞,low = 5·10⁻⁶ m/(N·s)`), equivalent free velocity (Formula 18) and
source mobility (Formula 19). ISO 9611:1996: the free-velocity source
characterization (equation (9), `v₀ = 5·10⁻⁸ m/s`). The plate velocity levels
are referred to `v₀ = 10⁻⁹ m/s`. Conformance is anchored on the resonant-plate
power balance `P = ω·η·(m·S)·⟨v²⟩` (of which Formula 14 is the level), the
loss-factor identity, and the EN 12354-5 Annex I.3 Table I.8 conversion of the
flushing-cistern source.

## See also

- API reference: [`building.structure_borne_power`](/phonometry/reference/api/building/structure-borne-power/).

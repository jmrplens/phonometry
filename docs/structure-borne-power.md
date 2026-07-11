← [Documentation index](README.md)

# Structure-borne sound power of building equipment (EN 15657)

Building service equipment — pumps, fans, boilers, sanitary appliances —
injects **structure-borne sound power** into the building structure it is fixed
to, which then re-radiates as airborne noise in adjoining rooms. **EN 15657:2018**
characterises such a source by its *characteristic structure-borne sound power
level* `L_Ws`, measured with the **reception-plate method**: the source is
mounted on a plate of known mass per unit area `m` and area `S` whose structural
loss factor `η` is known, and the plate's spatial-average vibratory velocity is
measured. `L_Ws` (with the plate mobility) is the source term of the EN 12354-5
installed-equipment prediction.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/structure_borne_power_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/structure_borne_power.svg" alt="Characteristic structure-borne sound power level per one-third-octave band of a source determined on a low-mobility and a high-mobility reception plate, which agree within the method" width="82%"></picture>

## 1. The reception-plate relations

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

# Characteristic power level from the reception plate (loss factor from Ts):
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
attached. The characteristic power level plus the plate's point mobility (see
[mechanical mobility](mechanical-mobility.md)) provide the source description
for the EN 12354-5 model. The direct source-side counterpart is the ISO 9611
free velocity level (re `5·10⁻⁸ m/s`) measured at the contact points of
resiliently mounted machinery.

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

---

**Standards.** EN 15657:2018, *Acoustic properties of building elements and
buildings — Laboratory measurement of structure-borne sound from building
service equipment for all installation conditions*: the reception-plate method
(clause 7), the spatial mean velocity level (Formula 12), the plate loss factor
`η = 2.2/(f·Ts)` (Formula 13) and the characteristic structure-borne sound power
level `L_Ws` (Formula 14). The plate velocity levels are referred to
`v₀ = 10⁻⁹ m/s`. Conformance is anchored on the resonant-plate power balance
`P = ω·η·(m·S)·⟨v²⟩` (of which Formula 14 is the level) and the loss-factor
identity.

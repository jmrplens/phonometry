← [Documentation index](README.md)

# Sound Intensity (p-p method)

Sound *pressure* tells you how loud a point is; sound **intensity** tells
you where the energy is *going*. It is the acoustic power flux (W/m²), a
signed vector quantity — which is why intensity probes can localize sources,
separate them from background noise and measure sound power in situ
(ISO 9614) where a pressure measurement alone cannot.

## The two-microphone principle (IEC 61043)

A p-p probe holds two matched microphones a small distance Δr apart. The
pressure at the probe center is their mean, and the particle velocity comes
from the pressure *gradient* (Euler's equation, finite-difference form):

$$
p = \frac{p_1 + p_2}{2}, \qquad
u = -\frac{1}{\rho_0\ \Delta r}\int (p_2 - p_1)\ dt, \qquad
I = \overline{p\ u}
$$

In practice the estimator works in the frequency domain through the
cross-spectrum of the two channels (the standard's equivalent form):

$$
I(f) = -\ \frac{\mathrm{Im}\lbrace G_{12}(f)\rbrace}{2\pi f\ \rho_0\ \Delta r}
$$

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe.svg" alt="Two-microphone p-p intensity probe with the spacer distance and the measurement axis" width="92%"></picture>

```python
import numpy as np
from phonometry import sound_intensity

fs = 48000
rng = np.random.default_rng(0)
# The two probe-microphone pressures in Pa, p1 closest to the source.
#   In a real measurement these are your two calibrated probe recordings;
#   synthesized here (p2 = p1 delayed one sample) so the guide runs.
p1 = 0.02 * rng.standard_normal(fs)
p2 = np.concatenate(([0.0], p1[:-1]))   # p2 = p1 delayed one sample

res = sound_intensity(p1, p2, fs, spacing=0.012, fraction=3,
                      limits=[100, 2500])
print(res.total_intensity_level, res.total_direction)      # LI [dB], ±1
print(res.frequency, res.intensity_level)                  # per band
res.plot()   # Lp vs LI per band + the pressure-intensity index (needs matplotlib)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_instantaneous_intensity_dark.gif"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/anim_instantaneous_intensity.gif" alt="Animation: a two-microphone p-p probe with rotating pressure and velocity phasors; the instantaneous intensity arrow flips while its running average settles to a net flow for the progressive wave and to zero for the standing wave" width="88%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo.svg" alt="Third-octave pressure and intensity levels for a plane progressive wave versus a standing wave" width="92%"></picture>

*Left: in a plane progressive wave all pressure is transported —
L_I ≈ L_p. Right: a standing wave carries (almost) no net energy — the
pressure is high but the intensity collapses. The gap L_p − L_I is the
**pressure-intensity index**, the fundamental quality indicator of every
intensity measurement.*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# res is the IntensityResult computed in the example above.
# One line — Lp vs LI per band with the pressure-intensity index on a twin axis:
res.plot()
plt.show()

# By hand, from the per-band fields the result carries — mirroring what
# IntensityResult.plot() draws (bar label, merged twin-axis legend, δpI title):
fig, ax = plt.subplots()
ax.semilogx(res.frequency, res.pressure_level, "o-", label="Pressure level Lp")
ax.semilogx(res.frequency, res.intensity_level, "s--", label="Intensity level LI")
ax.set_xlabel("Frequency [Hz]")
ax.set_ylabel("Level [dB]")
twin = ax.twinx()
twin.bar(res.frequency, res.pressure_intensity_index,
         width=res.frequency * 0.2, color="#2ca02c", alpha=0.25,
         label="δpI = Lp − LI")
twin.set_ylabel("Pressure-intensity index δpI [dB]")
# Merge both axes' handles into a single legend, exactly as .plot() does:
lines, labels = ax.get_legend_handles_labels()
tlines, tlabels = twin.get_legend_handles_labels()
ax.legend(lines + tlines, labels + tlabels)
ax.set_title(f"Lp vs LI  (total δpI = {res.total_pressure_intensity_index:.1f} dB)")
plt.show()
```

</details>

## Knowing when to trust the number

Two physical limits bound every p-p measurement, and the result object
carries both:

- **High frequency**: the finite-difference gradient underestimates I by
  $\sin(k\Delta r)/(k\Delta r)$ — verified in CI against IEC 61043 Table 3.
  `IntensityResult.bias_correction` provides the factor and
  `max_valid_frequency` (≈ 0.1·c/Δr; 2.9 kHz for a 12 mm spacer) the
  practical ceiling. Larger spacers reach lower frequencies, smaller ones
  higher.
- **Reactive fields**: when `pressure_intensity_index` (F2 in ISO 9614-1)
  approaches the probe's residual index δ_pI0, phase errors dominate.

Over a measurement surface, the ISO 9614-1 Annex A field indicators grade the
scan itself. **F2**, the surface pressure-intensity indicator, is the surface
pressure level minus the level of the mean *magnitude* of the normal
intensity — the larger it is, the closer the measurement sits to the probe's
phase-error floor. **F3**, the negative partial power indicator, is the same
difference taken with the *signed* mean intensity — F3 − F2 > 0 reveals power
flowing inward through parts of the surface. **F4**, the field non-uniformity
indicator, is the normalised spread of the per-position intensities — the
larger it is, the more measurement positions the surface needs. Together with
the dynamic-capability criterion they are available directly:

```python
import numpy as np
from phonometry import field_indicators, dynamic_capability_index

# Per-position measurements over the ISO 9614-1 measurement surface
pressure_levels = np.array([74.1, 73.8, 74.5, 73.2])       # Lp per position (dB)
normal_intensity = np.array([1.2e-5, 1.0e-5, 1.4e-5, 0.9e-5])  # signed In per position (W/m²)

fi = field_indicators(pressure_levels, normal_intensity)
print(round(fi.f2, 2), round(fi.f3, 2), round(fi.f4, 3))   # 3.41 3.41 0.197
ld = dynamic_capability_index(18.0)   # δpI0 = 18 dB → Ld = δpI0 − K
print(ld, ld > fi.f2)                                      # 8.0 True (criterion 1)
```

### `sound_intensity()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `p1`, `p2` | 1D arrays | Pa | equal length | Microphone closer to the source first; reversing them flips the sign |
| `fs` | int | Hz | > 0 | |
| `spacing` | float | m | > 0 | Microphone separation Δr (typ. 6/12/50 mm) |
| `rho` | float | kg/m³ | default `1.204` | Air density |
| `c` | float | m/s | default `343.0` | Speed of sound (bias/validity estimates) |
| `fraction` | int, optional | — | `1`, `3` or `None` (default) | Octave/third-octave band integration |
| `limits` | list, optional | Hz | default library band range | Band analysis limits |
| `bias_correct` | bool | — | default `False` | Apply the per-bin $(k\Delta r)/\sin(k\Delta r)$ correction (IEC 61043 §7.3) before summing, so band/broadband totals stop under-reading as $f \to$ `max_valid_frequency`; bins past the first null are left uncorrected. The per-band `bias_correction` factor is reported either way |

See [Theory](theory-signal-analysis.md) for the derivations and [Calibration](calibration.md)
for absolute scaling of the two channels.

---

**Standards.** IEC 61043:1994, *Electroacoustics — Instruments for the
measurement of sound intensity — Measurements with pairs of pressure sensing
microphones* — the two-microphone cross-spectral intensity estimator, the
finite-difference bias correction and the usable-bandwidth bound (clause 7.3,
Table 3). ISO 9614-1:1993, *Acoustics — Determination of sound power levels
of noise sources using sound intensity — Part 1: Measurement at discrete
points* — the pressure-intensity index, the Annex A field indicators F2, F3
and F4, and the dynamic-capability criterion (Annex B).

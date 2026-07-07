---
title: "Sound Intensity (p-p)"
description: "Two-microphone sound intensity per IEC 61043 with the ISO 9614-1 field indicators."
---

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
u = -\frac{1}{\rho_0\,\Delta r}\int (p_2 - p_1)\ dt, \qquad
I = \overline{p\,u}
$$

In practice the estimator works in the frequency domain through the
cross-spectrum of the two channels (the standard's equivalent form):

$$
I(f) = -\,\frac{\mathrm{Im}\{G_{12}(f)\}}{2\pi f\,\rho_0\,\Delta r}
$$

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe.svg" alt="Two-microphone p-p intensity probe with the spacer distance and the measurement axis" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_pp_probe_dark.svg" alt="Two-microphone p-p intensity probe with the spacer distance and the measurement axis" style="width:92%">

```python
from phonometry import sound_intensity

res = sound_intensity(p1, p2, fs, spacing=0.012, fraction=3,
                      limits=[100, 2500])
print(res.total_intensity_level, res.total_direction)      # LI [dB], ±1
print(res.frequency, res.intensity_level)                  # per band
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo.png" alt="Third-octave pressure and intensity levels for a plane progressive wave versus a standing wave" style="width:92%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/intensity_demo_dark.png" alt="Third-octave pressure and intensity levels for a plane progressive wave versus a standing wave" style="width:92%">

*Left: in a plane progressive wave all pressure is transported —
L_I ≈ L_p. Right: a standing wave carries (almost) no net energy — the
pressure is high but the intensity collapses. The gap L_p − L_I is the
**pressure-intensity index**, the fundamental quality indicator of every
intensity measurement.*

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
  approaches the probe's residual index δ_pI0, phase errors dominate. The
  ISO 9614-1 Annex A field indicators and the dynamic-capability criterion
  are available directly:

```python
from phonometry import field_indicators, dynamic_capability_index

fi = field_indicators(pressure_levels, normal_intensity)   # F2, F3, F4
ld = dynamic_capability_index(18.0)   # δpI0 = 18 dB → Ld = δpI0 − K
ok = ld > fi.f2                                            # criterion 1
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

See [Theory](/phonometry/reference/theory/) for the derivations and [Calibration](/phonometry/guides/calibration/)
for absolute scaling of the two channels.

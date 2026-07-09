← [Documentation index](README.md)

# Hearing threshold (age and reference zero)

Two standards describe where the hearing threshold sits. **ISO 7029:2017**
gives the **statistical distribution of the hearing threshold with age** for an
otologically normal population — the slow, high-frequency-first loss known as
presbycusis. **ISO 389-7:2006** fixes the **reference threshold of hearing**,
the audiometric zero (0 dB HL) expressed as a sound pressure level under
free-field and diffuse-field listening. Both are defined over the audiometric
frequencies from 125 Hz to 8000 Hz.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_hearing_threshold_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_hearing_threshold.svg" alt="The hearing-threshold model: age, sex and a population fractile feed the ISO 7029 chain — the median deviation from age 18 (a times (age minus 18) to the power b, from Table 1 by sex), the upper and lower spreads su and sl (degree-5 polynomials in age minus 18, Tables 2 to 5), and the fractile threshold (median plus the standard-normal quantile z of the fractile times the spread), giving the expected hearing threshold level in dB HL, which is referenced to the audiometric zero, the ISO 389-7 free-field or diffuse-field reference threshold" width="82%"></picture>

## 1. Age-related threshold (ISO 7029)

For a person older than 18, the **median** hearing threshold deviation from the
value at age 18 grows as a power law of age (ISO 7029 clause 4.2, Table 1):

$$
\Delta H_{md} = a\,(Y - 18)^{b},
$$

with coefficients $a$, $b$ per frequency and sex. The spread around the median
is modelled by two half-Gaussians whose standard deviations $s_u$ (worse than
the median) and $s_l$ (better) are fifth-degree polynomials in $(Y - 18)$
(clause 4.3, Tables 2–5). Any **population fractile** $Q$ follows from the
standard-normal quantile $z(Q)$ (clause 4.4): $\Delta H_Q = \Delta H_{md} +
z(Q)\,s$, using $s_u$ when $z \ge 0$ and $s_l$ otherwise.

```python
import phonometry as ph

# Median threshold shift of a 65-year-old man, all audiometric frequencies.
result = ph.age_threshold(65, "male", fractile=0.5)
print(result.median.round(1))     # [ 6.6  7.6  8.  9.  10.4 13.4 16.3 21.6 26.2 33.7 39.5]
print(result.median[8].round(1))  # 26.2 dB at 4000 Hz

# The worst-hearing decile (90th percentile) at 4000 Hz:
print(ph.age_threshold(65, "male", fractile=0.9).threshold[8].round(1))  # 50.3
```

The loss is largest at the high frequencies and grows with age — the classic
downward-sloping presbycusis audiogram. Men and women follow different
coefficients (the `sex` argument), and a subset of the audiometric frequencies
can be requested with `frequencies=`.

## 2. Reference threshold of hearing (ISO 389-7)

The audiometric zero is not a fixed sound pressure level: it depends on how the
sound reaches the listener. ISO 389-7:2006 Table 1 gives the reference
threshold for **free-field** (frontal incidence) and **diffuse-field**
listening.

```python
import phonometry as ph

print(ph.reference_threshold("free-field"))
# [22.1 11.4  4.4  2.4  2.4  2.4 -1.3 -5.8 -5.4  4.3 12.6]
print(ph.reference_threshold("diffuse-field")[4])   # 0.8 dB at 1000 Hz
```

The two fields agree at low frequencies and diverge above about 1 kHz, where
the ear-canal resonance and head diffraction make the frontal free field the
more sensitive condition (a lower threshold) around 3–4 kHz.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_threshold_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/hearing_threshold.png" alt="Two panels. Left: the ISO 7029 median hearing-threshold deviation for men at ages 20, 40, 60 and 80, plotted on an inverted (audiogram) axis so worse hearing falls lower, with the 10 to 90 percent fractile band shaded around the 70-year curve; the loss deepens toward the high frequencies and with age. Right: the ISO 389-7 reference threshold of hearing for free-field and diffuse-field listening, which coincide below 1 kHz and diverge above it, dipping to a minimum near 3 to 4 kHz" width="96%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph
from phonometry.hearing import AUDIOMETRIC_FREQUENCIES as f

# One line for the age distribution:
ph.age_threshold(70, "male", 0.5).plot()
plt.show()

# By hand, both panels:
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
for age in (20, 40, 60, 80):
    r = ph.age_threshold(age, "male", 0.5)
    ax1.plot(f, r.median, "o-", label=f"{age} yr")
ax1.set_xscale("log"); ax1.invert_yaxis(); ax1.legend()

ax2.plot(f, ph.reference_threshold("free-field"), "o-", label="Free-field")
ax2.plot(f, ph.reference_threshold("diffuse-field"), "s--", label="Diffuse-field")
ax2.set_xscale("log"); ax2.legend()
plt.show()
```

</details>

The `AgeThresholdResult` carries the `median`, the `spread_upper` and
`spread_lower`, and the `threshold` at the requested fractile, and its
`.plot()` draws the median with the 10–90 % band. The noise-induced permanent
threshold shift of ISO 1999 — which adds a noise component on top of this age
component — is a separate topic.

---

**Standards.** ISO 7029:2017, *Statistical distribution of hearing thresholds
related to age and gender* — the median (clause 4.2, Table 1), the spread
around the median (clause 4.3, Tables 2–5) and its application (clause 4.4).
ISO 389-7:2006, *Reference zero for the calibration of audiometric equipment —
Reference threshold of hearing under free-field and diffuse-field listening
conditions* (Table 1).

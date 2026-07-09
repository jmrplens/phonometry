← [Documentation index](README.md)

# Noise-induced hearing loss (ISO 1999)

**ISO 1999:2013** estimates the hearing loss a population suffers from
occupational noise. It gives the **noise-induced permanent threshold shift**
(NIPTS) — the extra hearing loss caused by the noise, on top of ageing — as a
function of the exposure level, the exposure duration and the audiometric
frequency, together with its spread across a population. It then combines the
noise component with the age component (the ISO 7029 threshold, "database A")
into the **hearing threshold level associated with age and noise** (HTLAN).
Both are defined at the six audiometric frequencies 500 Hz to 6000 Hz, where
noise damage concentrates (the characteristic 4 kHz notch).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_nihl_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_nihl.svg" alt="Two converging lanes. Left: age, sex and a population fractile with database A (ISO 7029) give the age threshold H (HTLA). Right: the 8-hour-normalised exposure level and the exposure duration in years give the median NIPTS N50 (N50 equals u plus v times log of t over t0, times the squared excess of the level over the cut-off L0), then the fractile NIPTS N by adding the standard-normal quantile times the upper or lower spread. The two components combine into the hearing threshold associated with age and noise, HTLAN, equal to H plus N minus H times N over 120" width="86%"></picture>

## 1. Noise-induced permanent threshold shift (clause 6.3)

The median NIPTS for exposure durations of 10 to 40 years grows with the square
of the excess of the noise exposure level over a frequency-dependent cut-off
$L_0$ (ISO 1999 clause 6.3.1, Formula 2, Table 1):

$$
N_{50} = \left[u + v\,\lg\!\frac{t}{t_0}\right](L_{EX,8h} - L_0)^2,
$$

with $t$ the exposure in years and $t_0 = 1$ year; below $L_0$ the effect is
zero. A population **fractile** follows from two half-Gaussians whose spreads
$d_u$ (worse than the median) and $d_l$ (better) are given by Formulae 6/7 and
Table 3: $N_Q = N_{50} + z\,d$ with $z$ the standard-normal quantile, clamped at
zero (clause 6.3.2).

```python
import phonometry as ph

# Median NIPTS after 20 years at an 8 h-normalised level of 90 dB(A).
r = ph.nipts(90.0, 20.0, fractile=0.5)
print(r.frequencies.astype(int))  # [ 500 1000 2000 3000 4000 6000]
print(r.median.round(1))          # [ 0.   0.1  4.1 10.2 12.9  8.5]

# The most-susceptible tenth of the population (90th percentile):
print(ph.nipts(90.0, 20.0, fractile=0.9).value.round(1))
# [ 0.   0.1  7.7 16.2 17.8 13.6]
```

The shift peaks near 4 kHz and deepens with both level and duration. Below the
cut-off — here 500 Hz ($L_0 = 93$ dB) and 1000 Hz ($L_0 = 89$ dB) at 90 dB —
the noise causes no permanent shift. For durations under 10 years the median is
extrapolated from the 10-year value (Formula 3); a subset of the frequencies
can be requested with `frequencies=`.

## 2. Age and noise combined — HTLAN (clause 6.1)

The noise component does not simply add to the age component: ISO 1999
Formula (1) combines them with a compression term that matters once the total
exceeds about 40 dB:

$$
H' = H + N - \frac{H\,N}{120},
$$

where $H$ is the age threshold (HTLA, from ISO 7029 at the same fractile) and
$N$ the NIPTS. `htlan` evaluates both components and their combination.

```python
import phonometry as ph

# A 60-year-old man, 30 years at 95 dB(A), median.
h = ph.htlan(60, "male", 95.0, 30.0, fractile=0.5)
print(h.htla.round(1))       # [ 6.   7.8 12.5 16.6 20.2 25.9]  age alone
print(h.nipts.round(1))      # [ 0.5  3.  11.8 21.6 24.8 17.6]  noise alone
print(h.threshold.round(1))  # [ 6.5 10.7 23.  35.2 40.8 39.8]  age + noise
```

At 4 kHz the age component (20.2 dB) and the noise component (24.8 dB) combine
to 40.8 dB rather than their 45.0 dB sum — the compression term removes 4.2 dB.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/noise_induced_hearing_loss_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/noise_induced_hearing_loss.png" alt="Two panels. Left: the median NIPTS at 95 dB for 10, 20, 30 and 40 years on an inverted (audiogram) axis, with the 10 to 90 percent fractile band around the 40-year curve; the loss deepens toward a maximum near 4 kHz and grows with duration. Right: for a 60-year-old man exposed 30 years at 95 dB, the age component (HTLA), the noise component (NIPTS) and their HTLAN combination, which lies below the simple sum because of the compression term" width="96%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph
from phonometry.iso1999 import NIPTS_FREQUENCIES as f

# One line for the NIPTS spectrum with its fractile band:
ph.nipts(95.0, 40.0, 0.9).plot()
plt.show()

# By hand, both panels:
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.6))
for yr in (10, 20, 30, 40):
    ax1.plot(f, ph.nipts(95.0, yr, 0.5).median, "o-", label=f"{yr} yr")
ax1.set_xscale("log"); ax1.invert_yaxis(); ax1.legend()

h = ph.htlan(60, "male", 95.0, 30.0, 0.5)
ax2.plot(f, h.htla, "o-", label="Age (HTLA)")
ax2.plot(f, h.nipts, "^-", label="Noise (NIPTS)")
ax2.plot(f, h.threshold, "s--", label="Age + noise (HTLAN)")
ax2.set_xscale("log"); ax2.invert_yaxis(); ax2.legend()
plt.show()
```

</details>

The `NiptsResult` carries the `median` (`N50`), the `spread_upper`/`spread_lower`
and the `value` at the requested fractile; the `HtlanResult` carries `htla`,
`nipts` and the combined `threshold`. Both expose `.plot()`. The age component
alone is the subject of the [hearing-threshold](hearing-threshold.md) guide.

---

**Standards.** ISO 1999:2013, *Acoustics — Estimation of noise-induced hearing
loss* — the HTLAN combination (clause 6.1, Formula 1), the median NIPTS
(clause 6.3.1, Formulae 2-3, Table 1) and its statistical distribution
(clause 6.3.2, Formulae 4-7, Tables 2-3), validated against the worked examples
of Annex D. The age component (database A) is ISO 7029:2017.

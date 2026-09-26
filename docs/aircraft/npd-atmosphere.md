← [Documentation index](../README.md)

# NPD data for the air at the airport

The noise-power-distance (NPD) curves of the ANP database were measured in
whatever air the certification tests happened to have, and then normalised to
one atmosphere so that curves from different aircraft can be compared. That
atmosphere is **SAE AIR-1845**: the arithmetic mean of the attenuation rates
recorded in European and US certification tests. It is not a temperature and a
humidity; no real air absorbs exactly like it in every band, and ECAC Doc 29
calls it a purely notional atmosphere.

An airport is not notional. A cold, humid coastal field absorbs less at high
frequency than the average test day, so its aircraft are louder far from the
runway than the database says; a hot, dry one can absorb more. ECAC Doc 29
Vol. 2 Appendix D recalculates the NPD curves for the air of a study, and this
page runs it: from the AIR-1845 rates, through the spectral class that each NPD
carries, to revised curves that feed the event levels and contours of
[Airport noise](airport-noise.md) and [The ANP fleet database](anp-fleet.md).

## The AIR-1845 atmosphere

Table D-1 is the whole of it: one attenuation rate per one-third-octave band,
in decibels per 100 m, from 50 Hz to 10 kHz.

```python
from phonometry import aircraft

rates = aircraft.SAE_AIR1845_ATTENUATION_DB_PER_100M
print(rates[1000.0], rates[10000.0])   # 0.59 9.836 dB/100 m
```

## The spectral class of an NPD

An NPD table gives A-weighted levels, and absorption acts band by band, so the
recalculation needs a spectrum. Every ANP aircraft is assigned two **spectral
classes**, one for approach and one for departure: the average unweighted
spectrum of a family of aircraft at the time of the maximum level, at 1000 ft,
normalised to the same AIR-1845 rates and, for historical reasons, to 70 dB in
the 1 kHz band (Doc 29 Vol. 2, G4.3). The database ships 41 of them in
`Spectral_classes.csv`, and phonometry now reads it.

```python
from phonometry import aircraft

db = aircraft.load_anp_database()
ac = db.aircraft("747100")
print(ac.departure_spectral_class_id, ac.approach_spectral_class_id)   # 107 209
spectrum = ac.spectral_class("D")
print(spectrum.description, spectrum.levels_db[13])   # 4-Engine.Tfan 70.0 dB at 1 kHz
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_spectral_classes_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_spectral_classes.svg" alt="The departure spectral class 103 and the approach class 205 of the ANP database from 50 Hz to 10 kHz at 1000 ft, both through 70 dB at 1 kHz, the approach one carrying more energy above 5 kHz" width="82%">
</picture>

The two spectral classes of the Appendix D example, as the database ships them
and as Table D-2 prints them.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import aircraft

db = aircraft.load_anp_database()
fig, ax = plt.subplots(figsize=(10, 6))
db.spectral_class(103).plot(ax=ax)
db.spectral_class(205).plot(ax=ax, color="tab:red")
ax.set_title("ANP spectral classes 103 and 205 (ECAC Doc 29 Table D-2)")
plt.show()
```

</details>

## The increment, in three steps

With the spectral class $L_{n,\mathrm{ref}}(d_\mathrm{ref})$ at
$d_\mathrm{ref}$ = 1000 ft = 304.8 m and the AIR-1845 rate
$\alpha_{n,\mathrm{ref}}$ of band $n$, Appendix D first adds the reference
attenuation back (Eq. D-1), then takes the spectrum to each NPD distance $d_i$
twice, once in each atmosphere (Eqs. D-2 and D-3), and finally A-weights and
sums both (Eq. D-4). The rates are the decibels lost over 100 m of path, as
Table D-1 prints them, and the distances are in metres, so every attenuation
term carries the conversion $d/(100\,\mathrm{m})$:

$$
\begin{aligned}
L_n(d_\mathrm{ref}) &= L_{n,\mathrm{ref}}(d_\mathrm{ref}) + \alpha_{n,\mathrm{ref}}\,\frac{d_\mathrm{ref}}{100\,\mathrm{m}} \\
L_{n,\mathrm{ref}}(d_i) &= L_n(d_\mathrm{ref}) - 20\lg(d_i/d_\mathrm{ref}) - \alpha_{n,\mathrm{ref}}\,\frac{d_i}{100\,\mathrm{m}} \\
L_{n,\mathrm{atm}}(d_i) &= L_n(d_\mathrm{ref}) - 20\lg(d_i/d_\mathrm{ref}) - \delta_n(d_i)\,\frac{d_i}{100\,\mathrm{m}} \\
\Delta L(d_i) &= 10\lg\sum_n 10^{(L_{n,\mathrm{atm}}(d_i) - A_n)/10} - 10\lg\sum_n 10^{(L_{n,\mathrm{ref}}(d_i) - A_n)/10}
\end{aligned}
$$

Doc 29 prints the same equations with the rates in dB/m. At 1 kHz the rate of
0.59 dB/100 m puts back $0.59 \times 304.8/100$ = 1.80 dB over $d_\mathrm{ref}$,
the 1.798 dB of Table D-3a, and the 70.0 dB of the class becomes the 71.8 dB
that Table D-2 prints at the source. $\delta_n(d_i)$ is the rate of the
specified air in the same unit, which under ARP 5534 also depends on the path
length and the pressure, so $\delta_n(d_i)\,d_i/(100\,\mathrm{m})$ is its band
attenuation over the path; $A_n$ is the nominal A-weighting of IEC 61672-1 as
an attenuation, to 0.1 dB. The increment is added to the NPD level at the same
distance, for every power setting and for $L_\mathrm{max}$ and $L_E$ alike, and
the 70 dB normalisation of the class drops out of it.

```python
import numpy as np
from phonometry import aircraft

db = aircraft.load_anp_database()
increment = aircraft.npd_atmosphere_increment(
    db.spectral_class(103), temperature_c=10.0, relative_humidity_percent=80.0
)
print(round(increment.reference_attenuation_db[13, 3], 3))   # 1.798 dB, 1 kHz over 1000 ft
print(round(increment.source_spectrum_db[13], 1))            # 71.8 dB, Eq. D-1
print(np.round(increment.increment_db, 1))
# [0.1 0.3 0.4 0.7 1.2 1.8 2.1 2.4 2.9 3.6] dB, 200 ft to 25000 ft
```

Those are the numbers of Table D-4. The temperature and the humidity are
keyword-only and have no default: the AIR-1845 atmosphere is not a pair of them.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_increment_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_increment.svg" alt="NPD increment against slant distance at 10 degrees Celsius and 80 percent humidity for the spectral classes 103 and 205 by SAE ARP 5534 and by SAE ARP 866A, rising from near zero at 61 m to between 2.7 and 3.7 dB at 7620 m" width="82%">
</picture>

The increment of Tables D-4 and D-5 for both spectral classes and both
absorption routes, which agree within about 0.3 dB up to 2000 ft and part beyond
it.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import aircraft

db = aircraft.load_anp_database()
fig, ax = plt.subplots(figsize=(10, 6))
for class_id, operation, style, marker in ((103, "DEP", "-", "o"),
                                           (205, "ARR", "--", "s")):
    for route, name, color in (("arp5534", "SAE ARP 5534", "tab:blue"),
                               ("arp866a", "SAE ARP 866A", "tab:red")):
        aircraft.npd_atmosphere_increment(
            db.spectral_class(class_id), absorption=route,
            temperature_c=10.0, relative_humidity_percent=80.0,
        ).plot(ax=ax, color=color, ls=style, marker=marker,
               label=f"{operation}_{class_id}, {name}")
ax.set_title("NPD increment at 10 °C, 80 % (ECAC Doc 29 Tables D-4, D-5)")
plt.show()
```

</details>

## Two absorption routes

**SAE ARP 5534** (`absorption="arp5534"`, the default and the route Doc 29
recommends) maps the pure-tone attenuation over the path to a band attenuation
with the SAE Method, so it depends on the path length and on the pressure. Its
pure-tone coefficient is the one of ISO 9613-1 with the saturation vapour
pressure of ARP 5534 Eqs. 5-6, which is what reproduces all 240 cells of Table
D-3c.

**SAE ARP 866A** (`absorption="arp866a"`, kept for transition) is a rate per
band that depends on temperature and humidity only, implemented from ISO
3891:1978 Annex A as `arp866a_attenuation`. Above 4 kHz it is evaluated at the
lower band edge that Table 2 prints (4500, 5600, 7100 and 9000 Hz). Table 1
asks for "a form of quadratic interpolation" of $\eta(\delta)$ without saying
which: the parabola through three neighbouring entries reproduces all 264 cells
of ISO 3891 Table 10 and is the default of `arp866a_attenuation`, while Doc 29
Table D-3b is reproduced by linear interpolation
(`eta_interpolation="linear"`), which is what the Appendix D route uses. The
two readings part only below $\delta$ = 6.50; from there on Table 1 prints
0.200 and both hold it.

```python
import numpy as np
from phonometry import aircraft

absorption = aircraft.arp866a_attenuation(
    [1000.0, 10000.0], temperature_c=10.0, relative_humidity_percent=80.0
)
print(absorption.evaluation_frequencies_hz)             # [1000. 9000.] Hz
print(np.round(absorption.coefficient_db_per_100m, 3))  # [0.439 9.774] dB/100 m
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_attenuation_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_attenuation.svg" alt="Attenuation over 25000 ft against frequency: the SAE AIR-1845 rates of Table D-1 dashed and SAE ARP 5534 and SAE ARP 866A at 10 degrees Celsius and 80 percent solid, all small below 1 kHz and climbing steeply above it" width="82%">
</picture>

The attenuation of Tables D-3a to D-3c at the longest NPD distance. Over
25000 ft the bands from 1 kHz up carry at most about 1 % of the A-weighted
level in any of the three atmospheres, and the bands from 125 Hz to 500 Hz
about nine tenths of it, so the increment there is decided from 125 Hz to
500 Hz, where ARP 5534 absorbs less than ARP 866A and both less than AIR-1845.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import aircraft

spectrum = aircraft.load_anp_database().spectral_class(103)
fig, ax = plt.subplots(figsize=(10, 6))
for route, reference in (("arp5534", True), ("arp866a", False)):
    aircraft.npd_atmosphere_increment(
        spectrum, absorption=route,
        temperature_c=10.0, relative_humidity_percent=80.0,
    ).plot_attenuation(ax=ax, distance_m=25000 * 0.3048, reference=reference)
plt.show()
```

</details>

## Revised curves, and the chain that reads them

`revise_npd_curves` adds the increment to every power setting of an
`AnpNpdCurves`, and `AnpDatabase.revised_npd_curves` does it with the aircraft's
own spectral class. The event and contour wiring of the database takes the
humidity directly, and recalculates both NPD tables with the temperature and
pressure it already reads for the impedance adjustment.

```python
from phonometry import aircraft

db = aircraft.load_anp_database()
receiver = [6000.0, 0.0, 0.0]
reference = db.event_level("747100", receiver, "D", temperature_c=10.0)
humid = db.event_level(
    "747100", receiver, "D", temperature_c=10.0, relative_humidity_percent=80.0
)
print(round(reference.level, 1), round(humid.level, 1))   # 97.8 99.1 dB SEL
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_revised_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/npd_atmosphere_revised.svg" alt="SEL noise-power-distance curves of a Boeing 747-100 departure revised for 30 degrees Celsius and 30 percent humidity as solid lines over the database curves as dashed lines, falling below them beyond about 1 km" width="82%">
</picture>

A hot, dry day on a four-engined departure: the increment is negative, and
beyond about 1 km the revised curves fall below the database ones, by up to
1.1 dB at 3 km.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import aircraft

revised = aircraft.load_anp_database().revised_npd_curves(
    "747100", "D", "SEL", temperature_c=30.0, relative_humidity_percent=30.0
)
fig, ax = plt.subplots(figsize=(10, 6))
revised.plot(ax=ax)
plt.show()
```

</details>

## Checked against the worked example

Every intermediate table of the Appendix D example is a row of the conformance
report, cell by cell at its printed precision, and all of them agree to the last
digit but two: 32 cells of Table D-3b are printed about 6 parts per million
below the ISO 3891 formula, and the last row of Table D-6c is printed as a copy
of the last row of Table D-6b, which is in the [errata register](../ERRATA.md).
ISO 3891 Table 10 is a row too, all 264 cells. The formula misses 15 cells of
its Table 9 by one printed unit: seven contradict Table 10 where the humidity
drops out of the formula, and are in the same register; the other eight each
lie within 0.014 dB/100 m of a rounding boundary, no reading of Table 1 tried
reproduces them all, and they are left as printed.

## What this guide covers

**Covered.** The recalculation of ANP NPD data for a non-reference atmosphere by
ECAC Doc 29 Vol. 2 Appendix D: the SAE AIR-1845 rates of Table D-1, the spectral
classes of the shipped database, the increment of Eqs. D-1 to D-4 by SAE ARP
5534 or by SAE ARP 866A in the form of ISO 3891:1978 Annex A, the revised NPD
curves, and the event level and contour of an ANP aircraft in the air of a
study.

**Not covered.** An atmosphere that varies along the path, and the rest of
ISO 3891, whose tone-correction example is used only as a check of the ICAO
Annex 16 procedure.

## See also
Pages elsewhere on the site that this section leans on:

- [The ANP fleet database](anp-fleet.md): the NPD curves, profiles and event
  wiring this page revises.
- [Airport Noise (ECAC Doc 29)](airport-noise.md): the single-event chain the
  revised curves feed.
- [Aircraft noise: Effective Perceived Noise Level](aircraft-noise.md): SAE ARP
  5534 on its own, as certification uses it.
- API reference:
  [`aircraft.npd_atmosphere`](https://jmrplens.github.io/phonometry/reference/api/aeroacoustics/npd-atmosphere/).

## References

- ECAC, *Report on standard method of computing noise contours around civil
  airports*, Volume 2: Technical guide, Doc 29 5th ed. (2026), Appendix D.
- ISO 3891:1978, *Acoustics — Procedure for describing aircraft noise heard on
  the ground*, Annex A (withdrawn).
- SAE ARP 5534, *Application of pure-tone atmospheric absorption losses to
  one-third octave-band data* (reaffirmed 2021).

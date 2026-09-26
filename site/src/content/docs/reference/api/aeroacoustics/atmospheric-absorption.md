---
title: "aircraft.atmospheric_absorption"
description: "One-third-octave-band atmospheric absorption for aircraft noise (SAE ARP 5534 and 866A)."
sidebar:
  label: "atmospheric_absorption"
---

One-third-octave-band atmospheric absorption for aircraft noise (SAE ARP 5534 and 866A).

Aircraft noise certification (14 CFR Part 36, ICAO Annex 16 Vol. I) works with
one-third-octave-band spectra, and correcting a measured flyover to reference
atmospheric conditions requires the band attenuation over the propagation path.
Two SAE practices give it.

* [`sae_band_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#sae_band_attenuation) -- SAE ARP 5534, the current practice. Its
  pure-tone coefficient (Eqs. 1-6) is the ISO 9613-1 one, Eqs. 1-3 repeating
  [`air_attenuation`](/phonometry/reference/api/environment/air-absorption/#air_attenuation)
  term for term, except for the saturation vapour pressure: Eqs. 5-6 write it
  in the longer form of ANSI S1.26, which gives a molar concentration of water
  vapour 4.5 parts in 100 000 below the ISO 9613-1 Annex B formula at
  10 °C. The **SAE Method** (§3.2.2) then turns the pure-tone mid-band
  path-length attenuation into the one-third-octave-band attenuation and stays
  consistent with the ISO/ANSI Exact Method well beyond the 50 dB limit of the
  older Approximate Method. The result is an [`AircraftBandAttenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#aircraftbandattenuation)
  with a `.plot()`.
* [`arp866a_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#arp866a_attenuation) -- SAE ARP 866A (1975), the legacy practice that
  ECAC Doc 29 Vol. 2 Appendix D still offers for recalculating NPD data, in the
  form ISO 3891:1978 Annex A gives it: an attenuation coefficient per band, in
  decibels per 100 m, independent of pressure and of path length, evaluated at
  the band centre up to 4 kHz and at the lower band edge above. The result is an
  [`Arp866aAttenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#arp866aattenuation) with a `.plot()`.

Sources (clean-room, implemented from the documents): SAE ARP 5534 (2021),
*Application of Pure-Tone Atmospheric Absorption Losses to One-Third-Octave-Band
Data*, Eqs. 1-10; ISO 3891:1978, *Acoustics -- Procedure for describing aircraft
noise heard on the ground*, Annex A (A.1, A.2, Tables 1 and 2), which transcribes
SAE ARP 866A. Both are checked against ECAC Doc 29 5th ed. Vol. 2 Appendix D,
Tables D-3b and D-3c, and ARP 866A against ISO 3891 Table 10 as well.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AircraftBandAttenuation

```python
AircraftBandAttenuation(
    frequencies: NDArray[np.float64],
    band_attenuation: NDArray[np.float64],
    midband_attenuation: NDArray[np.float64],
    coefficient: NDArray[np.float64],
    path_length: float,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float,
)
```

One-third-octave-band atmospheric attenuation over a path (SAE ARP 5534).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Nominal one-third-octave-band centre frequencies, in Hz. |
| `band_attenuation` | SAE-Method band attenuation `δ_B` per band, in dB. |
| `midband_attenuation` | Pure-tone mid-band path-length attenuation $\delta_\mathrm{t} = \alpha \cdot s$ per band, in dB (ARP 5534 Eqs. 1-6 coefficient). |
| `coefficient` | Pure-tone mid-band attenuation coefficient `α` per band, in dB/m. |
| `path_length` | Propagation path length `s`, in metres. |
| `temperature_c` | Air temperature, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity, in percent. |
| `atmospheric_pressure_kpa` | Ambient atmospheric pressure, in kPa. |

### AircraftBandAttenuation.plot()

```python
AircraftBandAttenuation.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the band and pure-tone mid-band attenuation versus frequency.

## arp866a_attenuation

```python
arp866a_attenuation(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    eta_interpolation: str = 'quadratic',
) -> Arp866aAttenuation
```

One-third-octave-band attenuation coefficient by SAE ARP 866A (ISO 3891 Annex A).

The formula of ISO 3891:1978 A.2, in decibels per 100 m:

$$
\alpha = 10^{2.05 \log_{10}(f_0/1000) + 1.1394 \times 10^{-3}\,\theta - 1.916984} + \eta(\delta) \times 10^{\log_{10} f_0 + 8.42994 \times 10^{-3}\,\theta - 2.755624}
$$

$$
\delta = \sqrt{\frac{1010}{f_0}} \times 10^{\log_{10} RH - 1.328924 + 3.179768 \times 10^{-2}\,\theta - 2.173716 \times 10^{-4}\,\theta^2 + 1.7496 \times 10^{-6}\,\theta^3}
$$

with `θ` in degrees Celsius, `RH` in percent and `f0` from Table 2.

`η(δ)` comes from Table 1, whose note says "A form of quadratic
interpolation shall be used where necessary" without saying which, and
the two documents that print this attenuation read it differently.
`"quadratic"` (the default) is the parabola through three neighbouring
entries of Table 1 that reproduces every cell of ISO 3891 Table 10
(80 %, -10 °C to 40 °C) to the printed digit, where linear interpolation
misses 11 of the 264. `"linear"` reproduces ECAC Doc 29 Vol. 2 Table
D-3b (10 °C, 80 %, over the ten NPD distances): 208 of its 240 cells to the
printed digit and all 240 within half a unit of that digit plus 7 parts per
million, where the quadratic leaves up to 1.2 dB at 25000 ft; it is the
form [`npd_atmosphere_increment`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#npd_atmosphere_increment)
uses. The two part only where `δ` falls in the curved part of Table 1,
below 6.50; from there on both hold `η` at 0.200. ISO 3891 Table 9
(70 %) is not reproduced as closely as Table 10: the quadratic misses 15
of its 264 cells by one printed unit, seven where it contradicts Table 10
(both humidities give the same value there; see the errata register) and
eight more, each within 0.014 dB/100 m of a rounding boundary.

A.2 states the range the formula was measured over: from 2 °C to 30 °C (on
the print the mark before the 2 is unclear and may be a minus sign) and
from 30 % to 90 %. Its Tables 3 to 12 print the formula from -10 °C to
40 °C and from 10 % to 100 %.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | One-third-octave bands, by nominal or exact centre frequency in Hz, from 50 Hz to 10 kHz. |
| `temperature_c` | Air temperature `θ`, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity `RH`, in percent (0 to 100). |
| `eta_interpolation` | `"quadratic"` (default, ISO 3891) or `"linear"` (ECAC Doc 29 Appendix D). |

**Returns:** An [`Arp866aAttenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#arp866aattenuation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a band outside Table 2, a temperature at or below absolute zero, a humidity outside 0 % to 100 %, or an unknown interpolation. |

## Arp866aAttenuation

```python
Arp866aAttenuation(
    frequencies_hz: NDArray[np.float64],
    evaluation_frequencies_hz: NDArray[np.float64],
    delta: NDArray[np.float64],
    eta: NDArray[np.float64],
    coefficient_db_per_100m: NDArray[np.float64],
    temperature_c: float,
    relative_humidity_percent: float,
    eta_interpolation: str,
)
```

Atmospheric attenuation coefficient per band by SAE ARP 866A (ISO 3891 Annex A).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal one-third-octave-band centre frequencies, in Hz, one per band. |
| `evaluation_frequencies_hz` | The frequency `f0` of ISO 3891 Table 2 at which each band is evaluated, in Hz: the centre up to 4 kHz, the rounded lower band edge above. |
| `delta` | The humidity-and-temperature argument `δ` of A.2 per band, dimensionless. |
| `eta` | `η(δ)` per band, interpolated in Table 1. |
| `coefficient_db_per_100m` | The attenuation coefficient `α` per band, in decibels per 100 m. |
| `temperature_c` | Air temperature `θ`, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity `RH`, in percent. |
| `eta_interpolation` | How `η` was read between the entries of Table 1, `"quadratic"` or `"linear"` (see [`arp866a_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#arp866a_attenuation)). |

### Arp866aAttenuation.path_attenuation_db()

```python
Arp866aAttenuation.path_attenuation_db(
    path_length_m: float | ArrayLike,
) -> NDArray[np.float64]
```

Attenuation over a path, $\alpha \cdot s / 100$, in dB.

ARP 866A gives a rate, so the attenuation is proportional to the path
length and does not depend on the pressure, unlike SAE ARP 5534.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path_length_m` | Path length `s`, in metres: one length, or a 1-D sequence of them. |

**Returns:** One value per band for a single length, or an array of shape `(bands, lengths)`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a length is negative or not finite. |

### Arp866aAttenuation.plot()

```python
Arp866aAttenuation.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the attenuation coefficient versus frequency.

## sae_band_attenuation

```python
sae_band_attenuation(
    frequencies: NDArray[np.float64] | list[float],
    path_length: float,
    *,
    temperature_c: float = 25.0,
    relative_humidity_percent: float = 70.0,
    atmospheric_pressure_kpa: float = 101.325,
) -> AircraftBandAttenuation
```

One-third-octave-band atmospheric attenuation (SAE ARP 5534, SAE Method).

Computes the pure-tone attenuation coefficient at each band's exact mid-band
frequency (Eqs. 1-6 and 10, $f_{\mathrm{m},i} = 10^{i/10}$), forms the
mid-band path-length attenuation $\delta_\mathrm{t} = \alpha \cdot s$
and maps it to the band attenuation `δ_B` with the SAE-Method regression
(Eqs. 7-8). The coefficient is ISO 9613-1's with the saturation vapour
pressure of Eqs. 5-6, which is what reproduces ECAC Doc 29 Vol. 2 Table
D-3c to the last printed digit in all 240 of its cells; the ISO 9613-1
Annex B form leaves 57 of them up to 0.036 dB off.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies` | Nominal one-third-octave-band centre frequencies, in Hz (standard range 50 Hz-10 kHz; the method extends to 25 Hz-20 kHz). |
| `path_length` | Propagation path length `s`, in metres (`>= 0`). |
| `temperature_c` | Air temperature, in degrees Celsius (SAE window ~6-32 °C; default 25 °C, the ARP 5534 reference point). |
| `relative_humidity_percent` | Relative humidity, in percent (SAE window ~20-95 %; default 70 %). |
| `atmospheric_pressure_kpa` | Ambient atmospheric pressure, in kPa (default 101.325). |

**Returns:** An [`AircraftBandAttenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#aircraftbandattenuation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs are invalid. |

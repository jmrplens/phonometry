---
title: "aircraft.npd_atmosphere"
description: "NPD data for a non-reference atmosphere (ECAC Doc 29 Vol. 2 Appendix D)."
sidebar:
  label: "npd_atmosphere"
---

NPD data for a non-reference atmosphere (ECAC Doc 29 Vol. 2 Appendix D).

The noise-power-distance (NPD) curves of the ANP database are normalised to
the **SAE AIR-1845 atmosphere**: the arithmetic mean of the attenuation rates
measured in European and US certification tests (Table D-1), a notional
atmosphere that no single temperature and humidity produce. Where the air of a
study differs, Appendix D recalculates the NPD data from the spectral class of
the NPD, the unweighted reference spectrum at 1 000 ft, in three steps:

1. the AIR-1845 attenuation over the reference distance
   $d_\mathrm{ref}$ = 1 000 ft is added back (Eq. D-1);
2. the corrected spectrum is taken to each NPD distance $d_i$ with
   spherical spreading and, in turn, the AIR-1845 attenuation (Eq. D-2) and
   the attenuation of the specified atmosphere (Eq. D-3), by SAE ARP 5534 or
   by SAE ARP 866A;
3. both spectra are A-weighted and summed, and the difference of the two
   levels is the increment $\Delta L(d_i)$ (Eq. D-4), added to the
   `Lmax` and `LE` NPD levels alike.

* [`SAE_AIR1845_ATTENUATION_DB_PER_100M`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#sae_air1845_attenuation_db_per_100m) -- Table D-1.
* [`npd_atmosphere_increment`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#npd_atmosphere_increment) -- the increment at each NPD distance, as an
  [`NpdAtmosphereIncrement`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#npdatmosphereincrement) with `.plot()` (the increment against
  distance) and `.plot_attenuation()` (the attenuation of the two
  atmospheres against frequency).
* [`revise_npd_curves`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#revise_npd_curves) -- an
  [`AnpNpdCurves`](/phonometry/reference/api/aeroacoustics/anp-fleet/#anpnpdcurves) revised by that
  increment, as a [`RevisedNpdCurves`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#revisednpdcurves) with `.plot()`; its `revised`
  curves feed [`event_level`](/phonometry/reference/api/aeroacoustics/airport-noise/#event_level) and
  [`noise_contour`](/phonometry/reference/api/aeroacoustics/airport-noise/#noise_contour) like any other NPD
  table.

The A-weighting of step 3 is the nominal one of IEC 61672-1, to 0.1 dB, in the
24 bands from 50 Hz to 10 kHz: Doc 29 names it $A_n$ without printing
it, and those are the values that reproduce Tables D-4 and D-5.

Source (clean-room, implemented from the document): ECAC.CEAC Doc 29, 5th ed.
(2026), Volume 2, Appendix D, Eqs. D-1 to D-4 and Table D-1, and G4.3 for the
spectral classes. Checked end to end against Tables D-2 to D-6c of the same
appendix.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## npd_atmosphere_increment

```python
npd_atmosphere_increment(
    spectrum: SpectralClass | ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float = 101.325,
    absorption: str = 'arp5534',
    distances_m: ArrayLike | None = None,
) -> NpdAtmosphereIncrement
```

NPD increment of a spectral class for a specified atmosphere (Doc 29 Appendix D).

$$
L_n(d_\mathrm{ref}) = L_{n,\mathrm{ref}}(d_\mathrm{ref}) + \alpha_{n,\mathrm{ref}} \, \frac{d_\mathrm{ref}}{100\,\mathrm{m}} \qquad \text{(D-1)}
$$

$$
L_{n,\mathrm{ref}}(d_i) = L_n(d_\mathrm{ref}) - 20 \lg(d_i/d_\mathrm{ref}) - \alpha_{n,\mathrm{ref}} \, \frac{d_i}{100\,\mathrm{m}} \qquad \text{(D-2)}
$$

$$
L_{n,\mathrm{atm}}(d_i) = L_n(d_\mathrm{ref}) - 20 \lg(d_i/d_\mathrm{ref}) - \delta_n(d_i) \, \frac{d_i}{100\,\mathrm{m}} \qquad \text{(D-3)}
$$

$$
\Delta L(d_i) = 10 \lg \sum_n 10^{(L_{n,\mathrm{atm}}(d_i) - A_n)/10} - 10 \lg \sum_n 10^{(L_{n,\mathrm{ref}}(d_i) - A_n)/10} \qquad \text{(D-4)}
$$

with the distances in metres, $d_\mathrm{ref}$ = 1 000 ft = 304.8 m,
$\alpha_{n,\mathrm{ref}}$ the Table D-1 rate in dB per 100 m of path,
the unit the table prints (Doc 29 writes the equations with the rates in
dB/m instead), and
$\delta_n(d_i) \, d_i / (100\,\mathrm{m})$ the band attenuation of
the specified atmosphere over $d_i$: the SAE Method of SAE ARP 5534
([`sae_band_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#sae_band_attenuation)),
which depends on the path and the pressure, or SAE ARP 866A
([`arp866a_attenuation`](/phonometry/reference/api/aeroacoustics/atmospheric-absorption/#arp866a_attenuation)),
which depends on neither, with `η(δ)` read linearly in Table 1 of ISO
3891, as Tables D-3b and D-5 are computed. Doc 29 recommends ARP 5534 and
keeps ARP 866A for transition. Nothing is rounded: Tables D-4 to D-6c are rounded for
presentation only, and the increment is carried at full precision.

The increment is a difference of two sums over the same spectrum, so it
does not depend on the overall level of the spectral class, only on its
shape; the spectral classes are normalised to 70 dB at 1 kHz (G4.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `spectrum` | The spectral class of the NPD, a [`SpectralClass`](/phonometry/reference/api/aeroacoustics/anp-fleet/#spectralclass) or its 24 one-third-octave-band levels from 50 Hz to 10 kHz at 1 000 ft, in dB. |
| `temperature_c` | Air temperature `T`, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity, in percent. |
| `atmospheric_pressure_kpa` | Air pressure `pa`, in kPa (default 101.325, sea level). Read by ARP 5534 only. |
| `absorption` | `"arp5534"` (default) or `"arp866a"`. |
| `distances_m` | The NPD slant distances, in metres. `None` takes the ten standard ones of footnote 40, 200 ft to 25 000 ft. |

**Returns:** An [`NpdAtmosphereIncrement`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#npdatmosphereincrement).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a spectrum that is not 24 finite levels, an unknown absorption route, a distance that is not positive, or an atmosphere the chosen route refuses. |

## NpdAtmosphereIncrement

```python
NpdAtmosphereIncrement(
    frequencies_hz: NDArray[np.float64],
    distances_m: NDArray[np.float64],
    spectrum_db: NDArray[np.float64],
    source_spectrum_db: NDArray[np.float64],
    reference_attenuation_db: NDArray[np.float64],
    specified_attenuation_db: NDArray[np.float64],
    reference_levels_dba: NDArray[np.float64],
    specified_levels_dba: NDArray[np.float64],
    increment_db: NDArray[np.float64],
    absorption: str,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float,
)
```

The NPD increment for a specified atmosphere (ECAC Doc 29 Vol. 2 Appendix D).

Every per-band array runs over the 24 bands of `frequencies_hz`, and
every per-distance array over `distances_m`; the two attenuation
tables are `(bands, distances)`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Nominal one-third-octave-band centre frequencies, in Hz (50 Hz to 10 kHz). |
| `distances_m` | The NPD slant distances $d_i$, in metres. |
| `spectrum_db` | The spectral class as given, $L_{n,\mathrm{ref}}(d_\mathrm{ref})$ at 1 000 ft in the AIR-1845 atmosphere, in dB. |
| `source_spectrum_db` | $L_n(d_\mathrm{ref})$, the same spectrum with the AIR-1845 attenuation added back (Eq. D-1), in dB. |
| `reference_attenuation_db` | $\alpha_{n,\mathrm{ref}} \, d_i / (100\,\mathrm{m})$, the AIR-1845 attenuation at each distance (Table D-3a), in dB. |
| `specified_attenuation_db` | $\delta_n(d_i) \, d_i / (100\,\mathrm{m})$, the attenuation of the specified atmosphere (Tables D-3b and D-3c), in dB. |
| `reference_levels_dba` | $L_{A,\mathrm{ref}}(d_i)$, in dB. |
| `specified_levels_dba` | $L_{A,\mathrm{atm}}(d_i)$, in dB. |
| `increment_db` | $\Delta L(d_i) = L_{A,\mathrm{atm}} - L_{A,\mathrm{ref}}$ (Eq. D-4), in dB, to add to the NPD levels at the same distances. |
| `absorption` | `"arp5534"` or `"arp866a"`, the route taken for the specified atmosphere. |
| `temperature_c` | Air temperature, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity, in percent. |
| `atmospheric_pressure_kpa` | Air pressure, in kPa. SAE ARP 866A does not use it. |

### NpdAtmosphereIncrement.distance_column()

```python
NpdAtmosphereIncrement.distance_column(distance_m: float) -> int
```

Column of the tables that holds one of `distances_m`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `distance_m` | One of the NPD distances, in metres. |

**Returns:** Its index along the distance axis.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the distance is not one of the table's. |

### NpdAtmosphereIncrement.plot()

```python
NpdAtmosphereIncrement.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the increment against slant distance.

### NpdAtmosphereIncrement.plot_attenuation()

```python
NpdAtmosphereIncrement.plot_attenuation(
    ax: Axes | None = None,
    *,
    distance_m: float = 304.8,
    reference: bool = True,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the attenuation of both atmospheres against frequency at one distance.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `distance_m` | One of `distances_m` (default 1 000 ft). |
| `reference` | Also draw the AIR-1845 attenuation. Pass `False` to add a second route to axes that already carry it. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the specified-atmosphere `plot` call. |

**Returns:** The axes.

## revise_npd_curves

```python
revise_npd_curves(
    curves: AnpNpdCurves,
    spectrum: SpectralClass | ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float = 101.325,
    absorption: str = 'arp5534',
) -> RevisedNpdCurves
```

NPD curves recalculated for a specified atmosphere (Doc 29 Vol. 2 Appendix D).

Adds [`npd_atmosphere_increment`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#npd_atmosphere_increment), taken at the curves' own distances,
to the level of every power setting. The same increment applies to the
`Lmax` and the `LE` curves of an operation, which assumes the
atmosphere changes the reference spectrum and not the shape of the level
time history (Appendix D, last paragraph of step 3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `curves` | The NPD curves, an [`AnpNpdCurves`](/phonometry/reference/api/aeroacoustics/anp-fleet/#anpnpdcurves). |
| `spectrum` | The spectral class of the same aircraft and operation (see [`spectral_class`](/phonometry/reference/api/aeroacoustics/anp-fleet/#anpaircraftspectral_class)). |
| `temperature_c` | Air temperature, in degrees Celsius. |
| `relative_humidity_percent` | Relative humidity, in percent. |
| `atmospheric_pressure_kpa` | Air pressure, in kPa (default 101.325). |
| `absorption` | `"arp5534"` (default) or `"arp866a"`. |

**Returns:** A [`RevisedNpdCurves`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#revisednpdcurves).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | as [`npd_atmosphere_increment`](/phonometry/reference/api/aeroacoustics/npd-atmosphere/#npd_atmosphere_increment) does. |

## RevisedNpdCurves

```python
RevisedNpdCurves(
    original: AnpNpdCurves,
    revised: AnpNpdCurves,
    increment: NpdAtmosphereIncrement,
)
```

NPD curves recalculated for a specified atmosphere (Doc 29 Vol. 2 Appendix D).

**Attributes**

| Name | Description |
| :--- | :--- |
| `original` | The curves as the ANP database gives them, in the AIR-1845 atmosphere. |
| `revised` | The same curves with `increment` added at every power setting, an [`AnpNpdCurves`](/phonometry/reference/api/aeroacoustics/anp-fleet/#anpnpdcurves) that [`level`](/phonometry/reference/api/aeroacoustics/anp-fleet/#anpnpdcurveslevel) and the Doc 29 event chain read like any other. |
| `increment` | The increment and everything it was computed from. |

### RevisedNpdCurves.plot()

```python
RevisedNpdCurves.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the revised curves over the original ones against slant distance.

## SAE_AIR1845_ATTENUATION_DB_PER_100M

*Constant* (`mapping`).

```python
SAE_AIR1845_ATTENUATION_DB_PER_100M = {50.0: 0.033, 63.0: 0.033, 80.0: 0.033, 100.0: 0.066, 125.0: 0.066, 160.0: 0.098, 200.0: 0.131, 250.0: 0.131, 315.0: 0.197, 400.0: 0.23, 500.0: 0.295, 630.0: 0.361, 800.0: 0.459, 1000.0: 0.59, 1250.0: 0.754, 1600.0: 0.983, 2000.0: 1.311, 2500.0: 1.705, 3150.0: 2.295, 4000.0: 3.115, 5000.0: 3.607, 6300.0: 5.246, 8000.0: 7.213, 10000.0: 9.836}
```

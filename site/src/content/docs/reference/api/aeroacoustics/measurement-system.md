---
title: "aircraft.measurement_system"
description: "Aircraft-noise measurement-system tolerances (IEC 61265:1995)."
sidebar:
  label: "measurement_system"
---

Aircraft-noise measurement-system tolerances (IEC 61265:1995).

The certification levels of [`phonometry.aircraft.certification`](/phonometry/reference/api/aeroacoustics/certification/) are only
worth what the chain that measured them is, and IEC 61265 is the standard that
says how good that chain has to be: microphone directional response, overall
frequency response, level linearity and the resolution of the reported level.
The one-third-octave filtering itself is covered by the IEC 61260 class 2
verification of [`phonometry.filters.verify_filter_class`](/phonometry/reference/api/filters/compliance/#verify_filter_class) (subclause 4.6)
and is not repeated here.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AircraftSystemComplianceResult

```python
AircraftSystemComplianceResult(
    passed: bool,
    checks: tuple[dict[str, Any], ...],
)
```

IEC 61265:1995 verdict on an aircraft-noise measurement chain.

What [`verify_aircraft_noise_system`](/phonometry/reference/api/aeroacoustics/measurement-system/#verify_aircraft_noise_system) returns: the verdict together
with the individual checks it is the conjunction of.

**Attributes**

| Name | Description |
| :--- | :--- |
| `passed` | Whether every supplied measurement met its limit. |
| `checks` | One entry per checked quantity, `{"quantity", "limit", "value", "ok", ...}`, as an immutable tuple. |

## verify_aircraft_noise_system

```python
verify_aircraft_noise_system(
    *,
    directional: dict[float, dict[float, float]] | None = None,
    frequency_response: dict[float, float] | None = None,
    linearity: dict[str, float] | None = None,
    resolution: float | None = None,
) -> AircraftSystemComplianceResult
```

Verify measured performance against IEC 61265:1995 tolerances.

Each supplied measurement is checked against the standard's limit; the
one-third-octave filtering itself is covered by the IEC 61260 class-2
verification (subclause 4.6) and is not repeated here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `directional` | Microphone directional response as `{frequency_hz: {angle_deg: \|Δsensitivity\| dB}}` (Table 1, §4.4.2). |
| `frequency_response` | System response deviations `{frequency_hz: deviation_db}` against the ±1.5 dB limit (§4.5.1). |
| `linearity` | Level non-linearity `{"reference": dB, "other": dB}` against the ±0.4/±0.5 dB limits (§4.5.2). |
| `resolution` | Readout resolution, in dB, against the 0.1 dB limit (§4.7). |

**Returns:** An [`AircraftSystemComplianceResult`](/phonometry/reference/api/aeroacoustics/measurement-system/#aircraftsystemcomplianceresult), whose `passed` is the conjunction of every check and `False` when no measurement was supplied.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a frequency or angle is out of the tabulated range. |

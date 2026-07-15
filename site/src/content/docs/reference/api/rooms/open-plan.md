---
title: "room.open_plan"
description: "Public API of phonometry.room.open_plan (auto-generated)."
sidebar:
  label: "open_plan"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Open-plan-office spatial metrics per ISO 3382-3:2012.

From a line of measurement positions across workstations (ISO 3382-3:2012,
5.2.2) this module derives the single-number quantities of Clause 4:

- the spatial decay rate of the A-weighted sound pressure level of speech
  `D2,S` and the nominal A-weighted speech level at 4 m `Lp,A,S,4m`
  (Clause 6.2), obtained by a least-squares fit of the A-weighted speech
  level against `lg(r/r0)` (logarithmic distance axis, `r0 = 1 m`)
  using only positions in the 2 m to 16 m range (Equation (5)); and
- the distraction distance `rD` (STI = 0,50) and privacy distance
  `rP` (STI = 0,20) (Clause 3.6, 3.7, 6.3), obtained from a linear
  regression of the speech transmission index against distance on a
  linear axis.

The A-weighted speech levels `Lp,A,S,n` (Clause 6.2, Equation (4)) and
the per-position STI (full IEC 60268-16 method, spatially averaged
background noise per Clause 6.3) are taken as inputs; this module performs
only the regressions and threshold read-offs of Clause 6.

The distraction and privacy distances are read from the fitted STI line,
extrapolating beyond the measured range when necessary (the regression-line
method of Clause 6.3, Figure 3 b). A distance is reported as `nan` when
the STI does not decrease with distance (non-negative fitted slope) or when
the crossing would fall at or before the source, realising the standard's
note that it "can prove impossible to determine the privacy distance if
STI > 0,20 in all positions" (Clause 6.3).

## open_plan_metrics

```python
open_plan_metrics(
    positions_m: List[float] | np.ndarray,
    spl_a_speech: List[float] | np.ndarray,
    sti_values: List[float] | np.ndarray,
) -> OpenPlanResult
```

Open-plan-office single-number quantities per ISO 3382-3:2012.

Computes the spatial decay rate `D2,S` and the nominal A-weighted
speech level at 4 m `Lp,A,S,4m` (Clause 6.2, Equation (5)) from a
least-squares fit of the A-weighted speech level against `lg(r/r0)`
(`r0 = 1 m`) restricted to positions in the 2 m to 16 m range, and
the distraction distance `rD` (STI = 0,50) and privacy distance
`rP` (STI = 0,20) from a linear regression of STI against distance
(Clause 3.6, 3.7, 6.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `positions_m` | Distances `r` from the source to each measurement position, in metres (ISO 3382-3:2012, 5.2.3 d). |
| `spl_a_speech` | A-weighted speech level `Lp,A,S,n` at each position, in dB (Clause 6.2, Equation (4)). |
| `sti_values` | Speech transmission index at each position (full IEC 60268-16 method with spatially averaged background noise, Clause 6.3). |

**Returns:** [`OpenPlanResult`](/phonometry/reference/api/rooms/open-plan/#openplanresult) with `d2s`, `lp_as_4m`, `rd` and `rp`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If fewer than four positions are given (Clause 5.2.2) or the three arrays differ in length. |

## OpenPlanResult

```python
OpenPlanResult(d2s: float, lp_as_4m: float, rd: float, rp: float)
```

Single-number open-plan-office quantities (ISO 3382-3:2012, Cl. 4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `d2s` | Spatial decay rate of the A-weighted SPL of speech in dB (per distance doubling), from the least-squares fit of Clause 6.2, Equation (5). `nan` when fewer than two positions lie in the 2 m to 16 m range. |
| `lp_as_4m` | Nominal A-weighted speech level at 4 m in dB, read off the same regression line (Clause 3.3, 6.2). `nan` under the same condition as `d2s`. |
| `rd` | Distraction distance in m, where the linear STI-vs-distance regression crosses 0,50 (Clause 3.6, 6.3). `nan` when the fitted STI does not decrease with distance or the crossing is non-positive. |
| `rp` | Privacy distance in m, where the same regression crosses 0,20 (Clause 3.7, 6.3), possibly extrapolated beyond the measured range. `nan` under the same condition as `rd`. |

Initialize self.  See help(type(self)) for accurate signature.

### OpenPlanResult.plot()

```python
OpenPlanResult.plot(ax: Axes | None = None, **kwargs: Any) -> Axes
```

Plot the spatial decay of speech with `rD`/`rP` marked.

Redraws the Clause 6.2 regression line from `d2s` and
`lp_as_4m` and marks the distraction and privacy distances.
Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

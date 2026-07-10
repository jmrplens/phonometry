---
title: "Occupational Noise Exposure (ISO 9612)"
description: "The ISO 9612 task-based, job-based and full-day measurement strategies for the daily noise exposure level LEX,8h, with the Annex C uncertainty budget and the one-sided 95 % upper limit."
---

A working day is rarely measured in one take: the daily exposure level a
regulation acts on has to be assembled from *samples* of a real shift, and
reported with an uncertainty a hygienist can defend. `lex_8h` (in
[Levels](/phonometry/guides/levels/)) turns *one* recording into a daily level. ISO 9612:2009 —
the engineering method (accuracy grade 2) — is the survey design *around* that
primitive: how to sample a real working day, how to combine the pieces, and how
to attach the normative uncertainty every occupational-hygiene report needs. The
`occupational_exposure` module adds the three **measurement strategies** and the
**Annex C** uncertainty budget on top of the energy-average machinery.

## 1. The three measurement strategies (Clauses 9-11)

The *task-based* strategy (Clause 9) splits the nominal day into tasks, takes
$I \ge 3$ samples per task, and energy-sums the task contributions

$$
L_{EX,8h,m} = L_{p,A,eqT,m} + 10 \log_{10}(T_m/T_0), \qquad T_0 = 8\ \text{h},
$$

so a loud but short task contributes little. The *job-based* (Clause 10) and
*full-day* (Clause 11) strategies instead take $N \ge 5$ (or three whole-day)
random samples over a homogeneous exposure group and normalise the effective-day
duration. The daily level is the same either way; the strategies differ in how
the **uncertainty** is built.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/exposure_uncertainty.png" alt="ISO 9612 Annex D task-based exposure: the three task LEX,8h contributions as bars, the energy-summed daily LEX,8h line and the one-sided 95 % upper limit LEX,8h + U band above it" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/exposure_uncertainty_dark.png" alt="ISO 9612 Annex D task-based exposure: the three task LEX,8h contributions as bars, the energy-summed daily LEX,8h line and the one-sided 95 % upper limit LEX,8h + U band above it" style="width:80%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# One line, with the Annex D `res` computed below: task contribution bars
# plus the LEX,8h and LEX,8h + U lines.
res.plot()
plt.show()
```

</details>


```python
from phonometry.occupational_exposure import (
    Task, task_based_exposure, job_based_exposure, full_day_exposure,
)

# ISO 9612 Annex D — a welder's day split into three tasks. Each task level is
# the energy average of its Lp,A,eqT samples; durations carry a measured range.
tasks = [
    Task(samples=(70.0,), duration_hours=1.5, label="planning/breaks"),
    Task(samples=(80.1, 82.2, 79.6), duration_hours=5.0,
         duration_range=(4.0, 6.0), label="welding"),
    Task(samples=(86.5, 92.4, 89.3, 93.2, 87.8, 86.2), duration_hours=1.5,
         duration_range=(1.0, 2.0), label="cutting/grinding"),
]
res = task_based_exposure(tasks, include_duration_uncertainty=False, warn=False)
print(f"LEX,8h = {res.lex_8h:.1f} dB   U = {res.expanded_uncertainty:.1f} dB")
# LEX,8h = 84.3 dB   U = 2.7 dB
print(f"one-sided 95 % upper limit LEX,8h + U = {res.upper_limit:.1f} dB")   # 87.0 dB
for t in res.tasks:
    print(f"  {t.label:<16} Lp,A,eqT = {t.lp_aeqt:5.1f}   contributes {t.lex_8h_contribution:5.1f} dB")
#   planning/breaks  Lp,A,eqT =  70.0   contributes  62.7 dB
#   welding          Lp,A,eqT =  80.8   contributes  78.7 dB
#   cutting/grinding Lp,A,eqT =  90.1   contributes  82.8 dB

# The same shift measured job-based (Annex E) and full-day (Annex F): both use
# the Eq C.9 / Table C.4 sampling budget with k = 1.65 (one-sided 95 %).
job = job_based_exposure([88.1, 86.1, 89.7, 86.5, 91.1, 86.7], effective_duration_hours=7.5)
full = full_day_exposure([88.0, 91.9, 87.6, 90.4, 89.0, 88.4], effective_duration_hours=9.25)
print(f"job      LEX,8h = {job.lex_8h:.1f} dB   U = {job.expanded_uncertainty:.1f} dB")
# job      LEX,8h = 88.2 dB   U = 3.8 dB
print(f"full-day LEX,8h = {full.lex_8h:.1f} dB   U = {full.expanded_uncertainty:.1f} dB")
# full-day LEX,8h = 90.1 dB   U = 3.4 dB
```

## 2. The Annex C uncertainty budget

Two subtleties are worth spelling out. First, the coverage factor is
$k = 1.65$ for a **one-sided** 95 % interval (Clause 14), because a hygienist
cares only about the *upper* bound: `res.upper_limit` = $L_{EX,8h} + U$ is the
value 95 % of measurements fall below, the number compared against an action
limit. Second, the task and job methods weight the *same* spread of samples
differently. The task sampling uncertainty $u_{1a}$ (Eq. C.6) divides the summed
squared deviations by $I(I-1)$ — the standard error of the mean, smaller by a
factor $\sqrt{I}$ — whereas the job/full-day sampling uncertainty $u_1$ (Eq. C.12)
is the plain sample standard deviation with denominator $N-1$, whose contribution
$c_1 u_1$ is then read from **Table C.4** as a function of $(N, u_1)$. The same
raw scatter therefore inflates the job estimate more, which is the standard's
built-in penalty for coarser, fewer samples. (The printed job $L_{EX,8h}$ is
$88.2$ dB where Annex E reports $88.1$: the standard rounds the effective-day
level to $88.4$ before the duration normalisation; the library keeps it
unrounded.)

When a task's samples span **3 dB or more** (Clause 9.3), or the job contribution
$c_1 u_1$ exceeds 3.5 dB (Clause 10.4), or too few workers are covered
(Table 1 cumulative-duration), the result sets `sampling_advisory=True` and, with
`warn=True`, emits an `OccupationalExposureWarning` recommending more measurements. Peak
levels $L_{p,Cpeak}$ are reported **without** an uncertainty — Annex C gives no
method for them (Table C.5, Note 1), so peak-uncertainty is out of scope. The
three Annex D/E/F worked examples above are reproduced to the standard's printed
precision (Annex E's final rounding is disclosed above), and the theory is
derived on the [Theory](/phonometry/reference/theory/) page.

### `task_based_exposure()` / `job_based_exposure()` / `full_day_exposure()` parameters

| Parameter | Applies to | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tasks` | task | list of `Task` | — | ≥ 1 | Each `Task` has `samples`, `duration_hours`, optional `duration_range`/`duration_samples`, `label`, `instrument` |
| `samples` | job / full-day | sequence | dB | ≥ 2 (≥ 5 / ≥ 3 advised) | Random `Lp,A,eqT` samples |
| `effective_duration_hours` | job / full-day | float | h | > 0 | Effective working-day duration $T_e$ |
| `instrument` | all | str | — | `'class1'`, `'class2'`, `'personal_exposimeter'` (default) | Selects $u_2$ (Table C.5) |
| `u3` | all | float | dB | default `1.0` | Microphone-position uncertainty (Clause C.6) |
| `include_duration_uncertainty` | task | bool | — | default `True` | `False` omits the $(c_{1b}u_{1b})^2$ term (Annex D case a) |
| `n_workers` / `sample_duration_hours` | job | int / float | — / h | default `None` | Table 1 cumulative-duration check |
| `warn` | all | bool | — | default `True` | Emit `OccupationalExposureWarning` for the sampling advisories |

All three return an `ExposureResult` with `lex_8h`, `combined_standard_uncertainty`
$u$, `expanded_uncertainty` $U = 1.65\ u$, `upper_limit` = $L_{EX,8h} + U$,
`sampling_advisory`, and (task-based) the per-task `tasks` breakdown; the
result's `.plot()` draws the per-task contribution bars with the $L_{EX,8h}$
and upper-limit lines (task-based results only, since the other strategies
carry no per-task breakdown).

## See also

- [Levels](/phonometry/guides/levels/) — the `lex_8h` / `sound_exposure` dose primitives
  (IEC 61252) and the LCpeak these strategies report alongside.
- [Measurement uncertainty](/phonometry/guides/gum-uncertainty/) — the GUM machinery behind
  combined and expanded uncertainties.
- [Theory](/phonometry/reference/theory/) — the derivation of the strategy formulas and the
  Annex C budget.

---

**Standards.** ISO 9612:2009, *Acoustics — Determination of occupational noise
exposure — Engineering method* — the task-based (Clause 9), job-based
(Clause 10) and full-day (Clause 11) strategies, the Annex C uncertainty budget
(Formulae C.6, C.9 and C.12, Tables C.4/C.5) and the one-sided coverage factor
k = 1.65 (Clause 14), validated against the worked examples of Annexes D, E
and F.

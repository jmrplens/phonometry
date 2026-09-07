← [Documentation index](../../README.md)

# What a seat does to the vibration (ISO 10326-1)

A driver does not sit on the floor of the machine. The seat is in between, and
whether it helps is not obvious: a suspension seat is a spring and a damper,
and a spring has a resonance. Feed it the wrong spectrum and it amplifies
exactly what it was bought to attenuate.

[Human vibration exposure](human-vibration.md)
measures what reaches the person. This page is the laboratory method that
measures what the seat did to it, and it answers with one number.

## 1. The SEAT factor

Mount the seat on a vibration simulator, drive the platform with the input
spectrum the application standard prescribes, sit a test person in it, and
measure the frequency-weighted r.m.s. acceleration in two places. The ratio is
the seat effective amplitude transmissibility, which everybody calls the SEAT
factor (10.2.2):

$$
\mathrm{SEAT} = \frac{a_\mathrm{wS}}{a_\mathrm{wP}}
$$

Below 1 the seat is doing its job. At 1 it is a rigid plank. Above 1 it is
making the ride worse than no seat at all, which is not a hypothetical: it is
what a suspension does when the machine's dominant frequency lands on its
resonance.

Both accelerations are the arithmetic mean of **three consecutive runs whose
values lie within ± 5 % of that mean** (10.2.1). The library treats that as a
condition rather than a footnote: `mean_of_test_runs` refuses a set that does
not meet the spread, because a mean of runs that disagree by more is not a
measurement this standard recognises.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seat_vibration_test_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/seat_vibration_test.svg" alt="Two panels. The left panel gives three test runs as paired bars, the platform near 1,00 and the seat near 0,71 metres per second squared, with the mean of each set drawn as a dashed line and a double arrow between the two means labelled SEAT = 0,71. The right panel gives four bars for the correction of clause 10.2.3: the input delivered at 1,00, the input intended at 1,10, the magnitude measured on the seat at 0,71 and the corrected magnitude at 0,78, over the formula a*wS = SEAT times a*wP." width="94%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
from phonometry import vibration

# Three runs at the platform and three at the seat, in m/s2.
test = vibration.seat_transmission(
    [0.72, 0.70, 0.71], [1.02, 1.00, 0.99]
)
print(round(test.seat_factor, 3), test.attenuates)     # 0.708 True
test.plot()
plt.show()

# Runs that do not agree within 5 % are not a measurement:
try:
    vibration.mean_of_test_runs([1.0, 1.2, 1.0])
except ValueError as error:
    print(error)
# The runs differ from their mean by 12.5 %, more than the 5 % this test allows.
```

</details>

*One test, and the ratio it exists to produce. The three runs agree to well
inside the tolerance, so their means are the two numbers the SEAT factor is
built from.*

## 2. Correcting to the input that was intended

A simulator does not reproduce its target spectrum exactly. Clause 10.2.3
scales the magnitude measured on the seat by the ratio between the input the
test intended and the input it actually delivered:

$$
a^{*}_\mathrm{wS} = \frac{a_\mathrm{wS}\, a^{*}_\mathrm{wP}}{a_\mathrm{wP}}
= \mathrm{SEAT} \cdot a^{*}_\mathrm{wP}
$$

```python
from phonometry import vibration

test = vibration.seat_transmission([0.72, 0.70, 0.71], [1.02, 1.00, 0.99])

# The platform delivered 1.003 m/s2 where 1.10 was intended.
print(round(test.corrected_acceleration(1.10), 3))     # 0.778

# The correction does nothing when the simulator hit its target:
print(round(test.corrected_acceleration(test.platform_acceleration), 3))
# 0.71
```

The standard prints that correction twice and only one printing is right.
Formula (4), the one shown above, is correct. Formula (3) beside it carries an
asterisk on all four of its symbols and so reduces to
$a^{*}_\mathrm{wS} = a^{*}_\mathrm{wS}$, which corrects nothing; the reading
the library implements is the one the clause's own prose asks for. It is
recorded in the [errata](../../ERRATA.md).

## 3. The damping test

The other test in Clause 10 does not involve a person. Load the seat with an
inert mass of 75 kg ± 1 %, drive the base at the resonance frequency
$f_\mathrm{r}$ of the suspension, and take the ratio there (10.3):

$$
T = \frac{a_\mathrm{S}(f_\mathrm{r})}{a_\mathrm{P}(f_\mathrm{r})}
$$

```python
from phonometry import vibration

# A suspension that doubles what it is given, at its own frequency.
print(vibration.resonance_transmissibility(2.4, 1.2))   # 2.0
print(vibration.DAMPING_TEST_MASS_KG)                   # 75.0
```

The arithmetic is the SEAT arithmetic and the meaning is not. The SEAT factor
is a verdict over a whole spectrum with a person in the seat; $T$ is what the
seat does at the one frequency where it does the most, with an inert mass in
it. Clause 9.5.1 notes that the test may not suit a suspension with active
damping, and that a reduced mass of 60 kg has been found appropriate.

## 4. What the numbers are not

Clause 11 is short and worth reading before quoting any figure from this page
as a pass or a fail. This standard fixes the method and states **no acceptance
value at all**: the application standard written for the machine states them,
either as a maximum SEAT factor or as a maximum corrected magnitude on the
seat, and separately as a maximum transmissibility at resonance. `attenuates`
is therefore a statement about the seat, not a verdict about the machine.

## What this guide covers

The **SEAT factor** of Formula (2), from the runs of one test, with the ± 5 %
agreement 10.2.1 requires of three consecutive runs enforced rather than
assumed.

The **correction to an intended input** of 10.2.3, as Formula (4) with the
SEAT factor substituted, which is what the clause's prose asks for and what
its printed Formula (3) fails to say.

The **transmissibility at resonance** of Formula (5), and the test masses of
10.3 and 9.5.1.

**No acceptance values**, because the standard states none: Clause 11 leaves
them to the application standard for the machine, and nothing here supplies a
default. The input spectral classes those standards prescribe, such as the
earth-moving machinery classes of ISO 7096, are not implemented either.

**Nothing weights a signal here.** The accelerations this page divides are
already frequency-weighted; the weightings themselves, and the r.m.s.
integration behind them, are in [human vibration
exposure](human-vibration.md).

**No laboratory.** The simulator tolerances of Clause 9, the transducer
mounting of 5.2, the semi-rigid disc, the test persons and posture of 8.2, the
run-in periods of 8.1.2 and the test report of Clause 12 are described in the
standard and none of them is implemented: this page is the arithmetic that
follows a test, not the test.

## See also

- [Human vibration exposure (ISO 2631, ISO 5349)](human-vibration.md):
  the weightings and the daily exposure the seat is measured in service of.
- [Vibration with repeated shocks (ISO 2631-5)](multiple-shock-vibration.md):
  what a seat that bottoms out delivers to the spine.
- [Transfer stiffness of resilient elements (ISO 10846)](../structural/transfer-stiffness.md):
  the same idea of a measured transmission ratio, applied to the isolator
  rather than to the seat.

## References

- International Organization for Standardization. (2016). *Mechanical
  vibration — Laboratory method for evaluating vehicle seat vibration — Part 1:
  Basic requirements* (ISO 10326-1:2016).
  Clause 10: the SEAT factor of Formula (2), the ± 5 % of 10.2.1, the
  correction of 10.2.3 and the damping test of 10.3 with its 75 kg inert mass.

## Standards

ISO 10326-1:2016, *Mechanical vibration — Laboratory method for evaluating
vehicle seat vibration — Part 1: Basic requirements*: the arithmetic of
Clause 10 and the tolerances it is run under. The SEAT factor of Formula (2),
the three consecutive runs within ± 5 % of their mean (10.2.1), the correction
to the intended input of 10.2.3 (Formula (4); the printed Formula (3) is an
identity and is registered in the errata), and the transmissibility at
resonance of Formula (5) with the 75 kg ± 1 % inert mass of 10.3 and the 60 kg
of 9.5.1. Clause 11 states no acceptance value and neither does this library;
the laboratory requirements of Clauses 5 to 9 and the test report of Clause 12
are not implemented.

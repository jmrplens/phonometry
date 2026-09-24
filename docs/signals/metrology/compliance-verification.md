← [Documentation index](../../README.md)

# Compliance and verification

Three kinds of evidence back a number computed with this library. The
**verifiers** are public functions that grade a filter or weighting you
configured against the acceptance limits of its governing standard. The
**conformance report** ([docs/CONFORMANCE.md](../../CONFORMANCE.md)) pins the
shipped implementation to the standards' own expected values and is
regenerated on every change. And the **scope notes** on each guide say where
the software's claim ends and a laboratory's begins. This page is the map of
the three.

## What a performance class asserts

IEC 61672-1:2013 (sound level meters) and IEC 61260-1:2014 (fractional-octave
filters) both specify two performance categories, **class 1 and class 2**,
and both define them the same way: the two classes share the *same design
goals* and differ mainly in the **acceptance limits** around those goals and
in the range of operational temperature; class 2 limits are greater than or
equal to class 1 limits everywhere (IEC 61672-1:2013 clause 1;
IEC 61260-1:2014 subclause 1.2).

A class is therefore not a quality grade but a **worst-case error bound
under stated conditions**, and the bound chains: a class 1 measurement needs
every stage at class 1, from the [calibrator](calibration.md) through the
weighting to the band filter. One class 2 stage bounds the chain at class 2.

Two vocabulary edges: **class 0** belongs to the withdrawn IEC 61260:1995 /
ANSI S1.11-2004 masks, not to the 2014 edition (see
[Filter class verification](../filters/filter-compliance.md)); and a class
belongs to a specification, so the honest claim is "class 1 per
IEC 61672-1:2013 Table 3" or "class 1 per IEC 61260-1:2014 Table 1", never
"class 1" alone.

## The verifiers: which function proves what

One verifier per instrument stage, all sharing the same verdict vocabulary:
`overall_class` (the strictest class met, or `None`), per-band margins in
decibels to the nearest limit, and a `range_limited` flag when part of the
standard's frequency range could not be demonstrated at your sample rate.

| Stage | Verifier | Acceptance limits |
| :--- | :--- | :--- |
| Frequency weighting (A, C, Z) | `verify_weighting_class` | IEC 61672-1:2013 Table 3 |
| Weightings B and AU | `verify_weighting_class` | ANSI S1.4-1983 Tables IV/V; IEC 61012:1990 Table 1 |
| Fractional-octave filter bank | `verify_filter_class` | IEC 61260-1:2014 Table 1 (1995 mask via `edition="1995"`) |
| Intensity instrument spectrum | `verify_intensity_class` | IEC 61043:1993 Table 2 |

The masks are public too: `weighting_class_limits(1)` returns the Table 3
corridor and `class_limits(fraction, filter_class, omega)` the Table 1 one,
so a report can draw the limits a verdict was judged against. Verifying a
whole chain, in the configuration the conformance suite itself pins
(48 kHz, order 6, one-third-octave, 100 Hz to 10 kHz):

```python
from phonometry import filters

wf = filters.WeightingFilter(48000, "A")
weighting = filters.verify_weighting_class(wf)
print(weighting.overall_class)       # 1
print(weighting.range_limited)       # False

bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6,
                                limits=[100, 10000])
bands = filters.verify_filter_class(bank)
print(bands.overall_class)           # 1
print(bands.range_limited)           # True for a decimated bank
```

Read the flags, not just the class: `range_limited` is `True` on the
decimated bank because a band cannot be evaluated beyond its own processing
Nyquist, so the far stopband rests on the anti-alias argument rather than on
the band filter itself. The details, including why a +0.400 dB margin is the
ceiling for a passing Butterworth bank, are in
[Filter class verification](../filters/filter-compliance.md); the weighting
side is section 6 of [Frequency weighting](../levels/weighting.md).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_class_mask_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_class_mask.svg" alt="A and C weighting deviations at 48 kHz threading within the IEC 61672-1 Table 3 class 1 acceptance corridor, with the wider class 2 limits dotted" width="80%"></picture>

When the verdict has to leave the console, the same call answers: what
`verify_filter_class` returns carries `.plot()` and `.report()`, the one-page
accredited fiche with an optional PASS/FAIL row against a required class, and
`verify_intensity_class` does the same for the IEC 61043 residual-index
verdict:

```python
from phonometry import ReportMetadata, filters

bank_11 = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
result = filters.verify_filter_class(bank_11)   # result.overall_class == 1
result.report(
    "iec61260.pdf",
    metadata=ReportMetadata(
        specimen="1/1-octave filter bank",
        measurement_standard="IEC 61260-1:2014",
        required_class=1,
    ),
)                                            # -> Class 1 - COMPLIES, PASS
```

**The verifiers that grade a measurement, not a design.** Six more functions
carry the same `verify_` prefix and answer a different question. The four
above are handed a filter this library built, and report whether that *design*
fits an acceptance mask; these are handed numbers somebody measured on a
bench, and report whether *that instrument, on the day it was measured*, meets
the standard it is sold against. There are no classes and no decibel margins
in them: the verdict is a pass or a fail, in the unit its own standard writes
its tolerances in. All six return a result object whose verdict says so and
whose other fields say where and by how much, down to `verify_running_rms_decay`,
which grades one printed row and keeps it.

| What is graded | Verifier | Acceptance limits |
| :--- | :--- | :--- |
| Aircraft-noise measurement system | `verify_aircraft_noise_system` | IEC 61265:1995 Table 1, and the scalar limits beside it |
| Human-vibration frequency weighting | `verify_weighting` | ISO 8041-1:2017 Tables 4 and 5 |
| Human-vibration phase response | `verify_phase_response` | ISO 8041-1:2017 Table 5 and Formula (6) |
| Saw-tooth burst indications | `verify_signal_burst_response` | ISO 8041-1:2017 Tables 7 to 9 (the signal is Table 6) |
| Running r.m.s. decay time | `verify_running_rms_decay` | ISO 8041-1:2017 Tables 10 and 11 |
| Sound calibrator | `verify_sound_calibrator` | IEC 60942:2017 Tables 2 to 7 and A.1 to A.5 |

One clause of ISO 8041-1 makes those four different in kind from everything
else on this page. The deviation a laboratory reports is extended by that
laboratory's own expanded uncertainty before it is compared with the limit
(clauses 13.1 and 14.1), so the same instrument passes on one bench and fails
on another, and `verify_weighting` takes that uncertainty as an argument
rather than assuming it away. The four are covered by [Verifying a
human-vibration meter](../../vibration/human/meter-verification.md), and the
aircraft one by [Aircraft noise](../../aircraft/aircraft-noise.md).

**The conformance rule of IEC TC 29.** The IEC instrument standards written
since 2013 answer the same question another way, in the same sentence:
IEC 61672-1:2013 5.1.21, IEC 60942:2017 5.1.15, IEC 61672-3:2013 4.1 and the
introductions of IEC 61260-2 and -3:2016. Conformance is demonstrated when the
measured deviation does not exceed the acceptance limits **and** the
laboratory's actual expanded uncertainty does not exceed the maximum-permitted
uncertainty the standard prints for the test, both limits inclusive. The
uncertainty is not added to the deviation: the tolerance the instrument has to
meet lies beyond the acceptance limit by that maximum (IEC 60942 Annex D,
IEC 61672-1 Annex A). `metrology.verify_conformance` is the rule on its own,
and its verdict names which of the four outcomes of IEC 60942 E.2.2 it is, in
the words of the tables' "Reasons" column; `verify_sound_calibrator` applies it
to every requirement of IEC 60942:2017 (see [Calibration and dBFS](calibration.md)).

```python
from phonometry import metrology

# IEC 61672-1:2013 Table C.1: acceptance limits +1.0 dB and -1.2 dB, and a
# maximum-permitted uncertainty of 0.5 dB.
on_the_limit = metrology.verify_conformance(          # example 7
    -1.2, uncertainty=0.3, acceptance_limits=(-1.2, 1.0), max_uncertainty=0.5)
print(on_the_limit.passes, on_the_limit.outcome)      # True 1
both_out = metrology.verify_conformance(              # example 10
    -2.0, uncertainty=0.7, acceptance_limits=(-1.2, 1.0), max_uncertainty=0.5)
print(both_out.passes, both_out.outcome)              # False 4
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/conformance_rule_examples_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/conformance_rule_examples.svg" alt="The eight examples of IEC 60942:2017 Table E.1 and the ten of IEC 61672-1:2013 Table C.1 drawn as the standards draw them, each marker the verdict verify_conformance returned, which is the verdict the table prints" width="100%"></picture>

All eighteen examples are rows of the [conformance report](../../CONFORMANCE.md),
verdict and printed reason each.

## Reading the conformance report

The verifiers grade *your* configuration; the
[conformance report](../../CONFORMANCE.md) is the complementary evidence for
the implementation as shipped: each row pins one implemented quantity to the
governing standard's own expected value (a worked example or a
tolerance-table entry, not a regression baseline), with the computed value,
the signed delta and a pass/fail verdict. It is regenerated on every pull
request and CI fails if it drifts from the code.

Use it in three ways: find the row for a metric before trusting it (the row
names the standard, edition and clause the implementation was held to); note
that the class rows walk one pinned configuration, so section 2's verifiers
are how the claim transfers to your own bank; and cite the report of the
exact library version you pinned. Defects the re-derivation exposed in the
published standards themselves are in the [errata registry](../../ERRATA.md).

## What only a laboratory can attest

Both instrument series continue past their Part 1 with two test regimes, and
neither is something a software library can run on itself.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_verification_regimes_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_verification_regimes.svg" alt="Three stacked bands, one for each part of the two instrument series, with sound level meters to IEC 61672 on the left and band filters to IEC 61260 on the right. A box at the top stands for the transfer function configured in phonometry, and two arrows, verify_weighting_class and verify_filter_class, reach down into the first band only. Part 1 holds the specifications: Table 3 of IEC 61672-1, the A, C and Z weightings at 34 frequencies from 10 Hz to 20 kHz with ±0.7 dB at 1 kHz for class 1, and Table 1 of IEC 61260-1, a relative attenuation corridor with ±0.4 dB at the mid-band, each with the largest uncertainty a laboratory may claim it with. A dashed line separates a design checked in software from a physical instrument in a laboratory. Part 2, pattern evaluation, shows at least three specimens submitted, at least two selected and at least one tested in full, with the environmental, electrostatic, radio-frequency, free-field, linearity and climate tests, and a report that states whether the pattern is approved. An arrow carries that approval down to Part 3, periodic tests on one working instrument at 20 °C to 26 °C with a limited set of checks, which support no general conclusion without it. A box at the foot gives the conformance criterion: the deviation within the acceptance limits and the uncertainty no larger than its maximum." width="100%"></picture>

*The two series side by side, their three parts stacked. The verifiers reach
only the Part 1 tables and only the first half of the conformance criterion;
Parts 2 and 3, under the dashed line, need a physical instrument, and a
periodic test says nothing general until the pattern approval it leans on is
public.*

**Pattern evaluation** (IEC 61672-2:2013 for meters, IEC 61260-2:2016 for
filters) is the type-approval regime a *model* passes once: the tests
necessary to verify conformance to **all mandatory specifications** of the
Part 1 (IEC 61672-2:2013 clause 1; IEC 61260-2:2016 subclause 1.1), on
physical specimens (IEC 61260-2 requires at least three of them
(subclause 4.1)). That includes everything a transfer function does not have:
static pressure, air temperature and humidity influence, electrostatic and
radio-frequency immunity, directional response, acoustical tests of the
weightings with the microphone in the sound field, level linearity of real
electronics, self-generated noise, tonebursts and overload behaviour
(IEC 61672-2:2013 clauses 7 to 9; IEC 61260-2:2016 clauses 7 to 9).

**Periodic tests** (IEC 61672-3:2013, IEC 61260-3:2016) are what a *working
instrument* receives in the laboratory, typically every year or two, on a
limited set of key tests "restricted to the minimum considered necessary",
valid for the environmental conditions of the day (IEC 61672-3:2013
clause 1; IEC 61260-3:2016 subclauses 1.2 and 1.3). Both Part 3 scopes end with the
same caveat: passing every periodic test supports **no general conclusion of
conformance** to the Part 1 unless the model's pattern approval is on record
(IEC 61672-3:2013 clause 1; IEC 61260-3:2016 subclause 1.5).

The same honesty applies to this library, in both directions. A verdict from
one of the four class verifiers is a statement about a *design*: the digital
transfer function you configured fits the Part 1 acceptance mask, with the
reported margins, over the checked range; every measurement made wholly in
software inherits it. A verdict from one of the six that grade a measurement
is narrower still: it belongs to the numbers somebody put in, on the day they
were measured, and nothing else inherits it. Neither is a pattern evaluation,
a periodic test, or a certificate for any physical device: nothing here has a microphone, a temperature or a serial
number, and a real front end brings its own paper: the meter's periodic
test per IEC 61672-3 and the calibrator's laboratory results per IEC 60942,
which `verify_sound_calibrator` grades but cannot produce, both discussed in
[Calibration and dBFS](calibration.md). A defensible report
names both verdicts: the library's design verdict with the version and its
conformance report, and the instrument's test record with its date.

## Standards

IEC 61672-1:2013, *Sound level meters — Part 1: Specifications*: the two
performance categories and the Table 3 acceptance limits checked by
`verify_weighting_class`.
IEC 61672-2:2013 (*Pattern evaluation tests*) and IEC 61672-3:2013
(*Periodic tests*): the instrument test regimes delimited above, not run.
IEC 61260-1:2014, *Octave-band and fractional-octave-band filters — Part 1:
Specifications*: the Table 1 acceptance limits checked by
`verify_filter_class`.
IEC 61260-2:2016 (*Pattern-evaluation tests*) and IEC 61260-3:2016
(*Periodic tests*): the filter-set test regimes delimited above, not run.
IEC 61043:1993, *Instruments for the measurement of sound intensity*: the
class limits behind `verify_intensity_class`.
IEC 60942:2017, *Sound calibrators*: the conformance rule of 5.1.15 and
Annex D, the eight examples of Table E.1 that `verify_conformance` reproduces,
and the requirements `verify_sound_calibrator` grades. IEC 61672-1:2013 5.1.21
and Table C.1 give the same rule and ten more examples.

**Not covered.** The verification mathematics of each stage belongs to that
stage's own page; and every test of the Parts 2 and 3 themselves is
delimited here but not performed: no environmental, immunity, acoustical or
linearity test is run, and no physical instrument is assigned a class.

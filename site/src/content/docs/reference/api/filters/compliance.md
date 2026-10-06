---
title: "filters.compliance"
description: "IEC 61260-1:2014 band-filter class verification."
sidebar:
  label: "compliance"
---

IEC 61260-1:2014 band-filter class verification.

Acceptance limits on relative attenuation transcribed from the
official text (BS EN 61260-1:2014, **Table 1**, standard pages 15-16):
octave-band breakpoint frequencies with class 1 and class 2 minimum/maximum
limits. Fractional-octave-band breakpoints are derived with Formulas (9) and
(10) (subclauses 5.10.3-5.10.4) and limits between breakpoints are interpolated
linearly in $\log_{10} \Omega$ per Formula (11) (subclause 5.10.6).
Relative attenuation is
$\Delta A(\Omega) = A(\Omega) - A_{\mathrm{ref}}$ (Formula 8) with
$A = L_{\mathrm{in}} - L_{\mathrm{out}}$
(Formula 7); here $A_{\mathrm{ref}}$ is the attenuation at the exact
mid-band frequency
(subclause 5.9: the pass-band reference attenuation).

IEC 61260-1:2014 defines only classes 1 and 2. **Class 0** (the tightest,
laboratory-grade class) lives only in the withdrawn **IEC 61260:1995 /
EN 61260:1995 Table 1** and its US twin **ANSI S1.11-2004 Table 1**, whose
class 1/2 masks differ numerically from the 2014 edition (e.g. the 2014
pass-band reference tolerance is ±0.4 dB for class 1 vs ±0.3 dB in 1995, and
the 2014 stop-band edge minimum is +1.2 dB vs +2.0 dB in 1995). The two editions
are therefore kept as separate mask tables selected by the `edition` argument
(`"2014"` default -> classes 1/2; `"1995"` -> classes 0/1/2). The 1995 /
ANSI-2004 octave-band table was transcribed digit-for-digit and cross-checked
between the two standards (they agree exactly).

One subject: the class of a band-filter design, graded against what IEC
61260-1:2014 requires of the transfer function of a set of filters, with the
effective bandwidth and the summation run the way IEC 61260-2:2016 (pattern
evaluation) tests them, or against what IEC 61260:1995 requires and run the
way its clause 5 tests it. The relative attenuation is graded further than
IEC 61260-2:2016 7.2.2.2 measures it, which is from 0.5 times the lowest to
1.5 times the highest mid-band frequency of the set: every band is read up to
$f_\mathrm{s}/2$, on the requirement of IEC 61260-1:2014 5.15 and
Table 1 themselves.

The transfer function graded is the one the bank has at its input rate. A
band the bank decimates by $M$ runs its input through a linear-phase
anti-aliasing filter, keeps one sample in $M$ and filters at
$f_\mathrm{s}/M$; a tone of frequency $f$ therefore comes out at
$f$ folded about the multiples of $f_\mathrm{s}/M$, scaled by the
anti-aliasing filter at $f$ and the band's sections at the folded
frequency. Every frequency below $f_\mathrm{s}/2$ is graded that way,
the images the decimation folds onto the band included. IEC 61260-1:2014
5.15 asks the anti-aliasing filters to keep the aliased components inside the
Table 1 limits, and Table 1 covers every frequency. IEC 61260:1995 4.8 asks
them to keep the relative attenuation from exceeding the greatest of the
applicable minimum limits of Table 1, and 5.7 tests it with a tone at the
decimated sampling frequency minus the mid-band frequency. The images are
graded against the Table 1 corridor at their input frequency in both
editions, which for the 1995 edition is the same floor: a decimated band
keeps $f_\mathrm{s}/(2M)$ at least sixteen times its upper band-edge
frequency, so every image lies past the last breakpoint of the mask, where
the minimum limit is the greatest one.

Besides the Table 1 mask there are two more requirements, both computed from
the same response:

* **Effective bandwidth deviation** (61260-1 5.11 and 5.12). The normalized
  effective bandwidth $B_\mathrm{e}$ is the integral of Formula (13),
  $\int (1/\Omega)\,10^{-0.1\,\Delta A(\Omega)}\,\mathrm{d}\Omega$,
  evaluated as IEC 61260-2 7.2.3.2 recommends: by the trapezoidal rule of its
  Formula (2) over the test frequencies of its Formula (1),
  $\Omega_i = G^{i/(bS)}$, with $S \ge 24$ frequencies per
  bandwidth (7.2.1.4). Its deviation from the reference
  $B_\mathrm{r} = (1/b)\ln G$ (Formula (15)) is
  $\Delta B = 10\lg(B_\mathrm{e}/B_\mathrm{r})$ (Formula (16)), within
  $\pm 0.4$ dB for class 1 and $\pm 0.6$ dB for class 2 (5.12.2).
  The 1995 edition calls the same quotient the **filter integrated
  response** (4.5) and builds it differently: its equation (14) integrates
  $10^{-0.1\,\Delta A}$ over $f/f_\mathrm{m}$ with no
  $1/\Omega$ weight, by the trapezoidal rule of equation (16) with
  $N \ge 5S$ (5.4.2), against
  $B_\mathrm{r} = G^{1/(2b)} - G^{-1/(2b)}$ (equation (9)), within
  $\pm 0.15$, $\pm 0.3$ and $\pm 0.5$ dB for classes 0, 1
  and 2 (4.5.3). Its $S$ is raised in steps of 12 until the integrated
  response of every band is independent of it to the nearest tenth of a
  decibel (5.3.3), and the summation runs at the same $S$.
* **Summation of output signals** (61260-1 5.16). At the test frequencies
  $\Omega_i$, $|i| \le \lfloor S/2 \rfloor$, inside a band, the
  outputs of that band and of its two neighbours are summed on an energy
  basis, IEC 61260-2 Formula (3):
  $\Delta P_j = 10\lg\left[10^{-0.1\,\Delta A_{j-1}} + 10^{-0.1\,\Delta A_j} + 10^{-0.1\,\Delta A_{j+1}}\right]$, for every band
  that has a neighbour on both sides (7.2.4.4). The limits are
  $+0.8$ dB and $-1.8$ dB for class 1 and $+1.8$ dB and
  $-3.8$ dB for class 2. They are applied to Formula (3) as printed,
  as 7.2.4.5 instructs; the words of 7.2.4.3 and of 5.16 name the difference
  the other way round, "input minus reference attenuation, and the summed
  output", which with limits this asymmetric is not the same test (see the
  errata registry). The 1995 edition prints the same sum as equation (19)
  (5.8.3), with the same conflict between its words and the formula, and
  runs it "from the lowest midband frequency to the highest midband
  frequency of the filter set" (5.8.4): its end bands are read on the half
  facing the set, where the neighbour the set lacks adds nothing. Its limits
  are $\pm 1.0$ dB for class 0, $+1.0$ dB and $-2.0$ dB for
  class 1 and $+2.0$ dB and $-4.0$ dB for class 2 (4.9).

The time-invariant operation of 5.14, tested with an exponential sweep
(IEC 61260-2 7.4), is [`phonometry.filters.verify_time_invariance`](/phonometry/reference/api/filters/time-invariance/#verify_time_invariance): it
runs the bank itself, decimation included, rather than reading its transfer
functions.

The acceptance limits of the A/B/C/AU/Z frequency weightings, which qualify a
network applied to the whole signal against a design-goal response, live in
[`phonometry.filters.weighting_compliance`](/phonometry/reference/api/filters/weighting-compliance/).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## class_limits

```python
class_limits(
    fraction: float,
    filter_class: int,
    omega: np.ndarray,
    *,
    edition: str = '2014',
) -> tuple[np.ndarray, np.ndarray]
```

Acceptance limits on relative attenuation at normalized frequencies.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fraction` | Bandwidth designator denominator b (1 for octave, 3 for one-third octave, ...). |
| `filter_class` | Performance class: 1 or 2 for `edition="2014"`; 0, 1 or 2 for `edition="1995"`. |
| `omega` | Normalized frequencies $f/f_\mathrm{m}$ (> 0). |
| `edition` | `"2014"` (IEC 61260-1:2014, classes 1/2) or `"1995"` (IEC 61260:1995 / ANSI S1.11-2004, classes 0/1/2). |

**Returns:** Tuple (minimum, maximum) relative attenuation in dB per point; the maximum is `+inf` outside the pass-band.

:::note
The exact band-edge point $\Omega = G^{1/2}$ is treated as
pass-band.
The 1995 edition's Table 1 prints a dedicated minimum (+2.3/+2.0/
+1.6 dB) *at* that single frequency, which this convention relaxes to
the pass-band minimum; the discrepancy has measure zero -- any
continuous response violating the edge row is caught at
$\text{edge} + \epsilon$
by the interpolated stop-band mask. The 2014 edition defines only
the $G^{1/2} - \epsilon$ and $G^{1/2} + \epsilon$
rows, which the masks match
exactly.
:::

## FilterComplianceResult

```python
FilterComplianceResult(
    overall_class: int | None,
    bands: tuple[dict[str, Any], ...],
    fraction: int,
    edition: str,
    sos: tuple[np.ndarray, ...],
    band_frequencies: np.ndarray,
    factors: tuple[int, ...],
    fs: float,
    num_points: int,
    *,
    range_limited: bool = False,
    points_per_bandwidth: int = 24,
)
```

IEC 61260-1 class-compliance verdict of an [`OctaveFilterBank`](/phonometry/reference/api/filters/core/#octavefilterbank).

What [`verify_filter_class`](/phonometry/reference/api/filters/compliance/#verify_filter_class) returns: the verdict together with the
minimal filter-bank data needed to redraw the measured relative-attenuation
curve, so the result exposes the standard `plot` / `report` pair without
holding a reference to the (possibly stateful) bank.

**Attributes**

| Name | Description |
| :--- | :--- |
| `overall_class` | The strictest class every band meets (0/1/2), or `None` when at least one band meets no class of the edition. |
| `bands` | The per-band verdicts (one `{"freq", "class", "margin_class<c>_db", ...}` per band), as an immutable tuple. |
| `fraction` | Bandwidth designator `b` (1 for octave, 3 for one-third-octave). |
| `edition` | `"2014"` (IEC 61260-1:2014, classes 1/2) or `"1995"` (IEC 61260:1995 / ANSI S1.11-2004, classes 0/1/2). |
| `sos` | Per-band second-order sections of the analysed bank (one array per band), kept so the relative attenuation can be recomputed exactly as the verifier does. |
| `band_frequencies` | The exact mid-band frequencies `f_m` in Hz. |
| `factors` | Per-band decimation factor; the band's processing sample rate is `fs / factor` (the multirate rate the SOS were designed at) and the factor fixes its anti-aliasing filter. Stored because the response is evaluated through both, which the verifier's public return does not otherwise expose. |
| `fs` | The bank's full sampling rate in Hz. |
| `num_points` | Frequency grid points per band used by the verification, retained so the redrawn curve matches the analysed grid. |
| `range_limited` | `True` when at least one band's outermost Table 1 breakpoint ($G^{4}$, carried to the bandwidth) lies beyond half the input sampling rate, so the verification could not exercise the full Table 1 mask there (no input of a digital bank has a frequency beyond it, but the limits are not demonstrated); the stated class then attests the verified frequency range and the `.report()` fiche prints a qualifying note. |
| `points_per_bandwidth` | `S`, the test frequencies per bandwidth of IEC 61260-2:2016 Formula (1) (IEC 61260:1995 equation (15)) the effective bandwidth and the summation were evaluated on; in the 1995 edition, the S that 5.3.3 raised the one asked for to. |

Every band entry carries, besides its Table 1 margins
`margin_class<c>_db`, the two requirements its edition tests on the
same measurements:

* `bandwidth_deviation_db`, the effective bandwidth deviation
  $\Delta B$ of 5.12 (the filter integrated response of 4.5 in the
  1995 edition), and `bandwidth_margin_class<c>_db`, its distance to
  each class's limit;
* `summation_min_db` and `summation_max_db`, the range of the
  summation $\Delta P_j$ of 5.16 (4.9 in the 1995 edition) across
  the band, and `summation_margin_class<c>_db`, the nearer of its
  distances to each class's two limits; all three are `None` on a band
  the summation does not apply to: in the 2014 edition the first and the
  last band, which have a neighbour on one side only (IEC 61260-2
  7.2.4.4), in the 1995 edition the one band of a single-band bank.

A band's `class` is then the strictest class it meets on all of them.

### FilterComplianceResult.available_classes()

```python
FilterComplianceResult.available_classes() -> list[int]
```

The performance classes carried by the per-band verdict dictionaries.

Reads the `margin_class<n>_db` keys of a band verdict, so it reflects
the edition (the 1995 edition adds class 0; the 2014 edition keeps only
classes 1 and 2). An empty result (a bank with no bands in range)
carries no verdicts, so this returns an empty list.

The first band answers for all of them: construction pins every band
to the same margin classes.

### FilterComplianceResult.binding_margin_db()

```python
FilterComplianceResult.binding_margin_db(
    requirement: str,
    filter_class: int,
) -> float
```

The smallest margin, in dB, of any band to one class on one requirement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `requirement` | One of `requirements`. |
| `filter_class` | One of `available_classes`. |

**Returns:** The binding margin; negative when a band misses the class.

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | for a requirement this verdict did not grade, or a class it carries no margins for. |

### FilterComplianceResult.plot()

```python
FilterComplianceResult.plot(
    ax: Axes | None = None,
    *,
    requirement: str = 'relative_attenuation',
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot one graded requirement.

`"relative_attenuation"` (the default) draws the measured relative
attenuation of the binding band over the acceptance corridor of the
achieved (or, when non-compliant, the loosest) class; see
`phonometry._plot.filters.plot_filter_class`.
`"effective_bandwidth"` draws $\Delta B$ of every band between
the limits of 5.12.2, and `"summation"` the Formula (3) curve of
every inner band between the limits of 5.16. Requires matplotlib
(`pip install phonometry[plot]`) and returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `requirement` | One of `requirements`. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the renderer's measured curve. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a requirement this verdict did not grade. |

### FilterComplianceResult.reference_class()

```python
FilterComplianceResult.reference_class() -> int
```

The class whose corridor the fiche/plot overlays.

The achieved overall class when the bank complies, else the loosest
class of the edition (the one it comes closest to meeting).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the result carries no bands, so there is no reference class to report. |

### FilterComplianceResult.report()

```python
FilterComplianceResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render an IEC 61260-1 filter-class-compliance fiche to a PDF.

Writes a one-page accredited report: the standard-basis line, an
optional metadata header block, a per-band classification table beside
the mask-overlay plot (the result's own `plot`), the boxed
class-compliance result, an optional verdict row against a supplied
`required_class` and a footer with the fixed disclaimer.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata); `None` produces a prediction fiche (body, result and disclaimer only). A supplied `required_class` drives the verdict row. |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | Accepted for a uniform signature; it has no effect on the single-layout filter-compliance fiche. |
| `language` | Fiche language: `"en"` (default, English) or `"es"` (Spanish, with a comma decimal separator). |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` is not `"reportlab"`. |
| ImportError | If reportlab is not installed (`pip install phonometry[report]`), or matplotlib is missing for the embedded figure (`pip install phonometry[plot]`). |

### FilterComplianceResult.requirement_class()

```python
FilterComplianceResult.requirement_class(requirement: str) -> int | None
```

The strictest class every band meets on one requirement alone.

**Parameters**

| Name | Description |
| :--- | :--- |
| `requirement` | One of `requirements`. |

**Returns:** The class, or `None` when a band meets none. The bands a requirement does not apply to (the end bands of the summation) do not constrain it.

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | for a requirement this verdict did not grade. |

### FilterComplianceResult.requirements

*property*

The requirements of its edition this verdict graded.

`"relative_attenuation"` (Table 1: 5.10 of IEC 61260-1:2014, 4.4 of
IEC 61260:1995) and `"effective_bandwidth"` (5.12; the filter
integrated response of 4.5 in 1995) always, and `"summation"`
(5.16; 4.9 in 1995) when the bank has a band it applies to: a band
with a neighbour on each side in the 2014 edition, which
IEC 61260-2:2016 7.2.4.4 grades on those bands only, and two bands or
more in the 1995 edition. Empty for a bank with no bands.

## verify_filter_class

```python
verify_filter_class(
    bank: OctaveFilterBank,
    *,
    num_points: int = 32768,
    edition: str = '2014',
    points_per_bandwidth: int = 24,
) -> FilterComplianceResult
```

Verify a filter bank against the IEC 61260 class limits.

Each band's relative attenuation (referenced to the attenuation at its
exact mid-band frequency) is checked against every acceptance-limit
class of the selected edition's Table 1, on the response the band has
at the bank's input rate: its anti-aliasing filter, the decimation and
its sections, so that every alias image the decimation folds onto the
band is graded where the input carries it. Table 1 covers every
frequency (its last rows read $\le G^{-4}$ and $\ge G^{+4}$),
and a sampled input holds every frequency below half its sampling rate,
so that is the range graded: `num_points` frequencies cover the
band's decimated half-band and the images above it are read at the same
spacing, up to half the input rate. The Table 1 breakpoint frequencies
in that range are always evaluated exactly, so the pass-band
constraints are checked even on a coarse grid. Above half the input
rate no input of the bank has a frequency, and the Table 1 limits there
are not demonstrated: the returned `range_limited` flag is set
whenever a band's outermost breakpoint ($G^{4}$, carried to the
bandwidth) lies beyond half the input rate, and the per-band
`checked_to_omega` records how far the check reached.

Two more requirements are graded on the same sections, the effective
bandwidth and the summation of the output signals, each in its edition's
own form (see the module docstring): for `edition="2014"` the
effective bandwidth deviation of IEC 61260-1:2014 5.12 of every band and
the summation of 5.16 of every band with a neighbour on each side, the
way IEC 61260-2:2016 tests them; for `edition="1995"` the filter
integrated response of IEC 61260:1995 4.5.3 of every band and the
summation of 4.9 from the lowest to the highest mid-band frequency, the
way its clauses 5.4 and 5.8 test them. A band's class, and so the
bank's, is the strictest class met on every requirement graded;
[`FilterComplianceResult.requirement_class`](/phonometry/reference/api/filters/compliance/#filtercomplianceresultrequirement_class) gives the class of each
requirement on its own.

**Parameters**

| Name | Description |
| :--- | :--- |
| `bank` | The filter bank to verify (its designed SOS are analyzed; works for stateful and stateless banks alike). |
| `num_points` | Number of frequency grid points per band on its decimated half-band (>= 16); the alias images are read at the same spacing. |
| `edition` | `"2014"` (IEC 61260-1:2014, classes 1/2) or `"1995"` (IEC 61260:1995, adds the stricter class 0). |
| `points_per_bandwidth` | `S`, the test frequencies per filter bandwidth of IEC 61260-2:2016 Formula (1) and IEC 61260:1995 equation (15), at least 24 (7.2.1.4 and 5.3.3). For `edition="1995"` it is where S starts: 5.3.3 raises it in steps of 12 until the filter integrated response of every band reads the same to the nearest tenth of a decibel at S and at S + 12, and the result's `points_per_bandwidth` says where it stopped. |

**Returns:** A [`FilterComplianceResult`](/phonometry/reference/api/filters/compliance/#filtercomplianceresult), which carries the verdict together with the sections, mid-band frequencies, decimation factors and sampling rate it was measured through, so it can redraw the relative attenuation and render an accredited `.report()` fiche without keeping a reference to the (possibly stateful) bank.

---
title: "Same bits on every machine"
description: "Determinism: why floating point drifts, how a designed filter stays byte-identical on any CPU, BLAS or thread count, what still differs, and the evidence."
---

A weighting filter designed by phonometry is the same filter, byte for byte,
whatever C library, thread count or hash seed it is designed under,
whichever compiler built numpy, and on any x86-64 processor, with or without
AVX-512 or fused multiply-adds, whichever OpenBLAS kernel set runs there.
The one reservation is two steps
of the realised cascade that go through a numerical library rather than the
C library, LAPACK's polynomial roots and the BLAS products SciPy forms,
which on 64-bit ARM, as measured, part some designs of the other curves and
none of the A weighting's; Scope below names them and says what was
measured. No routine of the C library is left in the weighting design's fit:
every transcendental it takes is spelled in arithmetic IEEE&nbsp;754 fixes
or computed correctly rounded in exact integer arithmetic, so glibc, Apple's
libm, musl and the Windows runtime, and the two builds glibc carries for
x86-64, have no say in its bits. This page records what was pinned and
measures what it does. The coefficients a laptop designs are the
coefficients a cluster designs, so a conformance verdict, a published figure
or a filter shipped inside a measurement chain is a reproducible artifact
rather than one machine's account of itself.

That sentence is not how scientific Python normally behaves, and this page
records what it cost, with the numbers.

## Why floating point drifts between hosts

IEEE 754 pins every *single* operation: given two doubles, their sum,
difference, product, quotient and square root are the same bit pattern on
every conforming machine. Everything beyond a single operation is where
reproducibility leaks, through three separate doors.

**Reductions are free to reassociate.** A sum of many terms has no defined
order, and a BLAS picks the order that suits the vector registers it finds at
run time. phonometry measured what that costs on its own weighting fit: two
OpenBLAS kernel sets agreed on every accept decision of the
Levenberg&ndash;Marquardt search for thirty-nine consecutive steps while the
costs they were comparing drifted from 3&nbsp;&times;&nbsp;10⁻¹³ to
1&nbsp;&times;&nbsp;10⁻⁴ apart, and the two runs then landed on **different
filters**: 5&nbsp;&times;&nbsp;10⁻⁵ apart in the leading coefficient,
0.002&nbsp;dB apart in response, a visible 0.0225&nbsp;pt apart in a plotted
curve. An optimiser in a shallow valley amplifies whatever the last bit does.

**Vectorised transcendentals are dispatched.** numpy chooses `log`, `exp`,
`tan`, `power`, `arctan` and `sin` kernels by what the CPU offers, and the
AVX-512 kernels do not agree to the last bit with the ones a machine without
AVX-512 runs. Measured under Intel SDE emulating Skylake-X against the same
host natively: every one of those six returns a different digest over the
same inputs. The leak reaches further than the obvious call sites:
`numpy.geomspace` is `10 ** linspace(...)`, so the frequency grid every
residual of the fit is evaluated on came out different under AVX-512, and
every step downstream inherited it.

**The platform's own libm is a platform choice.** `math.log` is whatever
`log` the C library ships. glibc's and Apple's are both accurate to about
half an ulp, which means that on a handful of inputs they legitimately round
to *opposite* neighbours, so a design loop built on `math.log` returned
different filters on macOS than on Linux with nothing anywhere to say so.
The same held for every other transcendental the C library ships, which is
why the A weighting at 48&nbsp;kHz once hashed to three values on the three
platforms the CI matrix runs.

## What phonometry pins

The deterministic design path answers each door in kind, in
`filters._weighting_design` and the pinned modules beside it,
`filters._pinned_log`, `filters._pinned_exp` and `filters._pinned_trig`:

- **Its own reductions.** Every sum the fit compares or solves with is folded
  pairwise in a shape fixed by the code, and the normal equations are solved
  by Gaussian elimination written out, the same algorithm LAPACK's `dgesv`
  runs with the order no longer a library's choice. Pairwise folding is also
  the *more accurate* order: O(&epsilon;&nbsp;log&nbsp;n) rounding against
  the O(&epsilon;&nbsp;n) of a running total, so nothing was traded away.
- **Real arithmetic where complex arithmetic dispatches or fuses.** Complex
  multiply and complex magnitude fuse operations differently per CPU, and
  numpy's complex product and quotient are C loops a compiler may fuse into
  multiply-adds: numpy built with clang, as on macOS and Windows, does, and
  numpy built with GCC, as on Linux, does not. So every place the path
  handed numpy or SciPy a complex expression is written out in real
  arithmetic, numpy's own steps in numpy's order, each rounded once: the
  printed curve the fit aims at, the read-back that sets the shipped gain,
  and the bilinear transform with its gain, which SciPy's `bilinear_zpk`
  forms as a product of complex numbers.
- **Pinned transcendentals.** Inside the iteration, the logarithm runs three
  quarters of a million times per design, the exponential once per factor
  per evaluation, and the power once per grid point in every Lawson round.
  Each is glibc's own routine spelled in numpy operations IEEE&nbsp;754 fixes
  exactly, plain arithmetic, integer bit work and table lookups: the
  table-driven `log` and the `log10` built on it, and the `exp` and `pow` of
  ARM's optimized-routines as glibc compiles them for a processor with a
  fused multiply-add, every multiply-add that build fuses reproduced by an
  exact emulation (rounding to odd, after Boldo and Melquiond). The sine,
  taken twice per design, the tangent, three times, the arctangent, once
  per design over the 257 points of the frequency grid, and the magnitude
  of a complex root are correctly rounded: the double nearest the exact
  value, found in exact integer arithmetic by Ziv's loop. Their bits are
  their own on every machine, which is stronger than calling anyone's libm,
  and no routine of the C library is left in the fit. For the arctangent
  that had a price on Linux: glibc's own rounds 19 of the 15&nbsp;866
  arctangents the checked designs evaluate to the other neighbour, so the
  correctly rounded value moved six of the 133 checked designs by their
  last bits. glibc's routine, which would have kept them where they were,
  is the IBM Accurate Mathematical Library, under LGPL-2.1-or-later, and is
  not transcribed into this MIT package.
- **The grid spelled out.** The geometric frequency grid is generated term
  for term with the endpoints pinned, so the fit evaluates the same
  frequencies everywhere.

## The evidence

Every claim above is measured, and most of them are re-measured by tests that
run in CI:

- **91,658,333 inputs, zero exceptions.** Every distinct value the whole
  design corpus feeds its logarithm was captured and compared bit for bit
  against glibc's `log`: identical on all of them, plus roughly a hundred
  million adversarial draws over the full exponent range, the near-one band,
  the subnormals and the branch edges. An adversarial search also found the
  honest limit: about one input in thirty million, in one narrow band, whose
  true logarithm sits within half an ulp of both neighbours and where the
  two implementations part by the last bit. None of those can reach a
  design, because on the design path the pinned routine *is* the definition.
- **The corpus moved where the arctangent did, and nowhere else.** The
  designs of seven curves at nineteen sampling rates, 133 in all, hash to
  the same single SHA-256 before and after the logarithm was vectorised, and
  again after the exponential, the power, the base-10 logarithm, the sine,
  the tangent and the complex magnitudes were pinned. The correctly rounded
  arctangent then moved six of them by their last bits: the A and C
  weightings at 44.1 and 88.2&nbsp;kHz, the D weighting at 88.2&nbsp;kHz and
  the G weighting at 1.5&nbsp;kHz. glibc's 19 misrounded arctangents reach
  32 of the 133 designs; in the other 26 the frequency that differs by one
  ulp gives the same target level to the last bit, so the fit never sees
  it. Put glibc's arctangent back and the corpus hashes to its old SHA-256
  again, and the six that moved stay inside the response bounds the tests
  hold.
- **The exponential and the power, bit for bit.** Every distinct value the
  corpus hands `exp` (677&nbsp;596 of them) and `pow` (580&nbsp;455) returns
  glibc's bits, and so does each of 120 million draws over each routine's
  domain, the edges of overflow and underflow and the subnormal results
  included. The fused multiply-add emulation returns the C library's `fma`
  on every one of 30 million draws, half of them nearly cancelling.
- **The arctangent, against the exact value.** The pinned arctangent
  returns the correctly rounded double, computed independently by an
  arbitrary-precision library at 200 bits, on every one of the
  15&nbsp;866 distinct values the checked designs hand it, on
  572&nbsp;386 edge values (every power of two from the smallest subnormal
  to the largest double with 64 neighbours on each side, the signed zeros,
  the infinities, NaN, and the two bands where the answer stops being the
  argument or the double nearest &pi;/2), on 60 million random bit
  patterns over the whole line of doubles, and on 150 million draws whose
  magnitude lies between 2⁻⁶² and 2⁶², where the routine does its real
  work. With its first pass cut to 56 bits, where
  a quarter to a third of the inputs need a second one and the error bound
  alone decides, 60 million more draws come back correctly rounded as well,
  and that bound, set against the exact value on a million evaluations at
  five working precisions, was never more than half used. In CI the answers
  are checked by exact rational bounds on the tangent, with no arctangent
  evaluated anywhere.
- **Correctly rounded, where glibc is and where it is not.** On the 70
  sines, 105 tangents and 67 complex magnitudes the corpus evaluates, glibc
  returns the correctly rounded value, so the correctly rounded routines
  return its bits there; on 19 of its arctangents it does not, as above.
  Away from the corpus the agreement rests on glibc's accuracy rather than
  on a proof: over every integer sampling rate from 100&nbsp;Hz to
  200&nbsp;kHz, 5&nbsp;864 of the 1&nbsp;399&nbsp;307 (rate, curve) designs
  meet a sine or a tangent glibc rounds the other way, and 45&nbsp;526 read
  a target level glibc's arctangent changes, and those designs can move on
  Linux with the pins, by what one ulp grows into through the fit. Of the
  common rates the checked set leaves out, 50&nbsp;kHz for A, B, C and D and
  100&nbsp;kHz for AU meet a sine or a tangent (AU moves from
  `7ee0fe06b2a91373` to `ec6c060d4b27d1b9`), and 176.4&nbsp;kHz for A, B and
  C the arctangent.
- **No C library left.** With every result the C library returns pushed
  one unit in the last place, by a shim between Python and the C library,
  the arctangent's included, twelve designs (the A weighting at 48, 44.1,
  88.2 and 192&nbsp;kHz, C at 44.1 and 88.2&nbsp;kHz, D at 48 and
  88.2&nbsp;kHz, G at 1 and 1.5&nbsp;kHz, and 468 and AU at 48&nbsp;kHz) do
  not move by a bit, where on the code before the pinned arctangent every
  one of them moved. musl, another C library, designs the whole corpus to
  glibc's SHA-256 with nothing replaced, and so does glibc's own build
  without FMA. On 64-bit ARM, the processor family of the macOS leg of the
  CI matrix, run in emulation under musl, 100 of the 133 designs are the
  same bytes, and the other 33 part at the two library steps Scope names,
  none of them in this package's own arithmetic.
- **Digest for digest across environments.** The designs are bit-identical
  between this host and the same host under AVX-512 emulation, under every
  selectable OpenBLAS kernel set, every thread count and every hash seed;
  the environment-versus-environment comparisons are pinned as tests.
- **One digest on three platforms.** With only the logarithm pinned, the A
  weighting at 48&nbsp;kHz hashed to `991833ff389afe91` on Linux (glibc,
  x86-64), `4efa1818bd80e23a` on macOS (arm64) and `79852a57e60961c8` on
  Windows (x86-64). With every transcendental pinned it still hashed to
  `5f5e34e5d3a8aa6e` on macOS and on Windows, one value for both: SciPy's
  bilinear transform took the gain as a product of complex numbers, through
  the numpy loop clang fuses and GCC does not. A test that fuses those
  products and quotients on any platform reproduces that digest on the code
  that called SciPy, and on the transform written out in real arithmetic
  designs `991833ff389afe91`, the plain bilinear designs of every curve at
  48&nbsp;kHz unchanged with it. A test in the CI matrix designs the A
  weighting as it ships, nothing replaced, and holds it to
  `991833ff389afe91` on all three platforms, and the A weighting at
  44.1&nbsp;kHz to `dbea4b7fc4ad972b`; a second test
  designs both again with an arctangent that owes nothing to the pinned
  routine, the C library's answer walked to the correctly rounded double by
  exact rational bounds, and lands on the same digests. On glibc x86-64
  without FMA the A weighting at 48&nbsp;kHz hashed to `43f786ffab5c4dd4`
  before the pins, and the arctangent's second build still parted nine of
  the 133 checked designs from the FMA build until it was pinned; the two
  builds now design the whole corpus to one SHA-256. The response tests
  that run on the same three platforms hold the A design within
  0.013&nbsp;dB of its analog prototype at 20&nbsp;001 frequencies across
  its fit band, at each of the six rates they check; two platforms whose
  bytes still differed could differ by up to twice that, 0.026&nbsp;dB, at
  one of those frequencies.

## See it yourself

Two designs are the same design, and the bytes have a name:

```python
import hashlib
from phonometry import filters

once = filters.WeightingFilter(48000, "A").sos
again = filters.WeightingFilter(48000, "A").sos
print(once.tobytes() == again.tobytes())                 # True
digest = hashlib.sha256(once.tobytes()).hexdigest()
print(digest[:16])                                       # 991833ff389afe91
```

The second line is the point: those sixteen hex digits, the head of the
SHA-256, are not "what my machine got", they are the digest of this
release's A weighting at 48&nbsp;kHz on any machine, the one the CI matrix
holds on Linux, macOS and Windows alike. If a future release moves a
coefficient deliberately, the digest moves with it and the change is a
documented event, never a property of your hardware.

## Scope

The guarantee covers the deterministic weighting design path end to end,
within the two library steps below: on every platform for the A weighting,
which the CI matrix holds on Linux, macOS and Windows, and for the other
curves wherever those two steps give the same bytes. Block processing
composes with it: a stateful cascade fed
block by block is bit-identical to one pass over the whole record, so
streaming does not spend the guarantee. General analysis functions built on numpy and SciPy in their
ordinary form remain reproducible on one machine but may differ in the last
bits across CPUs, which is the normal condition of scientific Python; the
deterministic treatment is applied where a filter's identity matters.

Two steps of the realised cascade go through a library rather than the C
library: the poles of the BS.468-4 prototype are numpy's polynomial roots,
which LAPACK computes, and the second-order sections are formed by SciPy,
whose polynomial products go through the BLAS. Both give the same bytes under
every OpenBLAS kernel set on x86-64, under glibc and under musl. On 64-bit
ARM they do not always: measured under musl in emulation, with the OpenBLAS
numpy ships there, 100 of the 133 checked designs are the x86-64 bytes, the
A weighting at all nineteen rates among them, and the other 33 part at
exactly these two steps. The 468 prototype's poles come out different in
their last bits, which reaches all nineteen 468 designs; for fourteen
designs of the B, C, D, G and AU weightings (D at 1.5, 32, 88.2 and
96&nbsp;kHz, G at 200&nbsp;Hz and 1, 88.2, 96 and 192&nbsp;kHz, AU at 32,
44.1 and 88.2&nbsp;kHz, B at 96&nbsp;kHz and C at 48&nbsp;kHz) the prototype
the fit returns and its bilinear transform are the same to the bit, and
only the sections SciPy forms from them differ. The Accelerate framework the
macOS build of numpy links is not measured here, so for those curves the
macOS bytes are not claimed; the A weighting, whose sections come out the
same on 64-bit ARM, is held by the CI test on macOS. SciPy's `zpk2sos` also takes complex
magnitudes, through numpy's own complex absolute, a loop numpy picks by
processor rather than the C library's `hypot`, but only to pair poles with
zeros and to test them against a tolerance: pushed one ulp, every one of
them, they move none of the A, D, 468 or AU weightings at 48&nbsp;kHz, the C
weighting at 44.1&nbsp;kHz or the G weighting at 1&nbsp;kHz.

The full engineering account lives with the code, in the module docstrings of
[`filters/_weighting_design.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_weighting_design.py),
[`filters/_pinned_log.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_log.py),
[`filters/_pinned_exp.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_exp.py)
and
[`filters/_pinned_trig.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_trig.py),
and the tests that hold it are in
[`tests/filters/test_weighting_design.py`](https://github.com/jmrplens/phonometry/blob/main/tests/filters/test_weighting_design.py)
and the three `tests/filters/test_pinned_*.py` beside it.

## See also

- [Conformance report](/phonometry/reference/conformance/): what the numbers are checked against; this page is why the checks read the same everywhere.
- [Errata in published sources](/phonometry/reference/errata/): the other half of the evidence story: where the printed expected value is the thing that is wrong.
- [Frequency weightings](/phonometry/signals/levels/weighting/): the guide to the curves the deterministic design realises.
- [Block processing](/phonometry/signals/filters/block-processing/): the streaming identity the scope section leans on.

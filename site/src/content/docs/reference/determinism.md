---
title: "Same bits on every machine"
description: "Determinism: why floating point drifts, how a designed filter stays byte-identical on any CPU, BLAS or thread count, what still differs, and the evidence."
---

A weighting filter designed by phonometry is the same filter, byte for byte,
whatever C library, BLAS, LAPACK, thread count or hash seed it is designed
under, whichever compiler built numpy, and on any processor: x86-64 with or
without AVX-512 or fused multiply-adds, and 64-bit ARM. No library step is
left on the design path. Every transcendental the fit takes is spelled in
arithmetic IEEE&nbsp;754 fixes or computed correctly rounded in exact
integer arithmetic, so glibc, Apple's libm, musl and the Windows runtime,
and glibc's x86-64 routines, built with fused multiply-adds or without, have
no say in its bits. The
two steps after the fit that used to go through a numerical library are the
package's own arithmetic too: the poles of the BS.468-4 prototype, which
LAPACK found, are the correctly rounded roots of the network's exact
polynomial, and the second-order sections, which SciPy formed through the
BLAS, are SciPy's own procedure with every product rounded once and every
magnitude correctly rounded. This page records what was pinned and measures
what it does. The coefficients a laptop designs are the
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
- **No library step after the fit.** The BS.468-4 prototype's six poles
  were numpy's polynomial roots: eigenvalues of the companion matrix, which
  LAPACK finds by an iteration whose sums the BLAS and the compiler are free
  to order and to fuse. The network's denominator is now built from its
  seven component values in exact rational arithmetic, and its roots are
  found in exact arithmetic too and rounded once, each part to the double
  nearest the exact root's, decided by a certificate: a disk around each
  approximation that provably holds one root and no other, and an extent in
  each coordinate that lies strictly between the midpoints around one
  double, or a coordinate shown in exact arithmetic to sit on one of those
  midpoints, which rounds to even. The second-order sections were SciPy's
  `zpk2sos`, which forms each section's polynomial with `numpy.convolve`,
  whose complex products go to the BLAS, and pairs poles with zeros by
  numpy's own complex magnitude, which is not correctly rounded. It is now
  spelled step for step and branch for branch, each product and sum
  rounded once and each magnitude correctly rounded; of two zeros at
  exactly the same distance from a pole it takes the first, as a stable
  sort does, where SciPy's choice goes through numpy's default sort, whose
  order of ties follows the processor.

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
- **The last two library steps moved 21 designs on Linux, and no others.**
  Spelling the poles and the sections moved all nineteen BS.468-4 designs,
  whose poles the correctly rounded roots place 2 to 36 units in the last
  place of each part away from LAPACK's. The fit starts from the poles, and
  from a start a few units away it settles on other coefficients inside its
  tolerance: 7 to 13 of each design's 18 move, by their last 9 to 12 bits
  at 250, 400 and 500&nbsp;Hz and at 22.05&nbsp;kHz by nearly half the value
  of one small coefficient, and the response differs by at most
  0.0072&nbsp;dB, at 125&nbsp;Hz (0.0033&nbsp;dB at 44.1&nbsp;kHz,
  0.000012&nbsp;dB at 48&nbsp;kHz). It moved the AU weighting by up to two
  units in the last place of eight coefficients at 100&nbsp;Hz and by one
  unit of six at 200&nbsp;Hz, where numpy's complex magnitude, one unit
  off the correctly rounded one, had paired two zeros one unit in the last
  place apart the other way round. The other 112 checked designs keep
  their bytes, the A weighting at all nineteen rates among them, and
  every design that moved stays inside the response bounds the tests hold.
- **The poles, against the exact value.** The six poles are the roots an
  arbitrary-precision library finds, rounded part by part, and the test
  suite holds them to those doubles. Against the same library at 3000 bits,
  the root finder as it ships returned the correctly rounded value of every
  part of every root of 10&nbsp;600 random polynomials, each in under half
  a second: 10&nbsp;200 copies of the 468 network with each component moved
  by up to 30&nbsp;%, 200 with integer coefficients of degree two to ten,
  four of them with a root at zero, and 200 whose roots spread over
  eighteen decades. numpy's own answer differs from them by 4 to 21 units in the last
  place of the root's magnitude, which is at most 3&nbsp;% of the error
  LAPACK's backward-stable eigensolver allows itself on that companion
  matrix, so the poles are what numpy finds, to numpy's own error, and the
  same bytes everywhere. In CI the root finder is held to roots written in
  closed form and rounded by exact integer square roots, a method it does
  not use.
- **The sections, against SciPy's.** Handed correctly rounded magnitudes,
  SciPy's `zpk2sos` returns the design's sections bit for bit on the plain
  and the fitted prototype of every one of the 133 checked designs, on the
  build of numpy that rounds its complex products step by step; with
  numpy's own magnitudes it parts from them only at AU at 100 and
  200&nbsp;Hz, as above, and the two realise the same response to
  10⁻⁹&nbsp;dB on every curve. With the BLAS's complex dot product fused
  by emulation, SciPy's sections for the D weighting at 48&nbsp;kHz move by
  up to 11 units in the last place and the design's do not move at all.
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
- **No C library left.** With every result of twenty routines of the C
  library pushed one unit in the last place, by a shim between Python and
  the C library (the exponentials, the logarithms, the power, the
  trigonometric and hyperbolic functions and their inverses, and `hypot`),
  the whole corpus, fitted and plain, hashes to the same two SHA-256 values
  as without it, where on the code before the pinned arctangent each of
  twelve designs measured that way (the A weighting at 48, 44.1, 88.2 and
  192&nbsp;kHz, C at 44.1 and 88.2&nbsp;kHz, D at 48 and 88.2&nbsp;kHz, G
  at 1 and 1.5&nbsp;kHz, and 468 and AU at 48&nbsp;kHz) moved. musl, another C library, designs the whole corpus to
  glibc's SHA-256 with nothing replaced, and so does glibc's own build
  without FMA. On 64-bit ARM, the processor family of the macOS leg of the
  CI matrix, run in emulation under glibc and under musl with the OpenBLAS
  numpy ships there, all 133 designs are the x86-64 bytes; until the last
  two library steps were spelled, 33 of them parted there, the nineteen
  BS.468-4 designs at the poles and fourteen others at the sections.
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
  44.1&nbsp;kHz to `dbea4b7fc4ad972b`, and every other curve at
  48&nbsp;kHz to a digest of its own; a second test
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
for every curve and every rate, on every platform: no step of it is a
library's, and the CI matrix holds every curve at 48&nbsp;kHz to one digest
on Linux, macOS and Windows. Block processing
composes with it: a stateful cascade fed
block by block is bit-identical to one pass over the whole record, so
streaming does not spend the guarantee. General analysis functions built on numpy and SciPy in their
ordinary form remain reproducible on one machine but may differ in the last
bits across CPUs, which is the normal condition of scientific Python; the
deterministic treatment is applied where a filter's identity matters.

Nothing after the fit is a library's either. The BS.468-4 prototype's
poles and the second-order sections were the last two steps that were, the
roots LAPACK found and the sections SciPy formed through the BLAS, and on
64-bit ARM under OpenBLAS they parted 33 of the 133 checked designs from the
x86-64 bytes; both are now this package's own arithmetic, measured to
design every one of the 133 to the same bytes on x86-64 under glibc, with
and without FMA, and under musl, and on 64-bit ARM under glibc and musl.
Apple's Accelerate, which the macOS build of numpy links, is no longer
reached by the design, so the macOS bytes are claimed for every curve and
held by the CI test.

The full engineering account lives with the code, in the module docstrings of
[`filters/_weighting_design.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_weighting_design.py),
[`filters/_pinned_log.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_log.py),
[`filters/_pinned_exp.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_exp.py),
[`filters/_pinned_trig.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_trig.py)
and
[`filters/_pinned_roots.py`](https://github.com/jmrplens/phonometry/blob/main/src/phonometry/filters/_pinned_roots.py),
and the tests that hold it are in
[`tests/filters/test_weighting_design.py`](https://github.com/jmrplens/phonometry/blob/main/tests/filters/test_weighting_design.py)
and the four `tests/filters/test_pinned_*.py` beside it.

## See also

- [Conformance report](/phonometry/reference/conformance/): what the numbers are checked against; this page is why the checks read the same everywhere.
- [Errata in published sources](/phonometry/reference/errata/): the other half of the evidence story: where the printed expected value is the thing that is wrong.
- [Frequency weightings](/phonometry/signals/levels/weighting/): the guide to the curves the deterministic design realises.
- [Block processing](/phonometry/signals/filters/block-processing/): the streaming identity the scope section leans on.

← [Documentation index](../README.md)

# Same bits on every machine

A weighting filter designed by phonometry is the same filter, byte for byte,
on every machine that runs the same C library routines: any BLAS kernel set,
any thread count, any hash seed, and any CPU, with or without AVX-512, save
for a choice the C library makes itself. glibc on x86-64 carries its
arctangent twice, built with fused multiply-adds and without, and picks one
by the processor; the two round a few inputs to opposite neighbours, so a
processor without FMA designs some filters differently, the A weighting at
44.1&nbsp;kHz among them, though not the A, D or 468 weightings at
48&nbsp;kHz. Across C libraries the bytes are not the same, yet, for the
same reason: the arctangent is the one transcendental the design still
takes from the platform's `math`. Every other transcendental is spelled in
arithmetic IEEE&nbsp;754 fixes, and the two steps that go through a
numerical library instead, LAPACK's polynomial roots and the BLAS products
SciPy forms, are named under Scope below. This page names what is left and
measures what it does. On one platform the coefficients a laptop designs are
the coefficients a cluster designs, so a conformance verdict, a published
figure or a filter shipped inside a measurement chain is a reproducible
artifact rather than one machine's account of itself.

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
- **Real arithmetic where complex arithmetic dispatches.** Complex multiply
  and complex magnitude fuse operations differently per CPU, so the two
  places the path handed numpy a complex expression are written out in real
  arithmetic.
- **Pinned transcendentals.** Inside the iteration, the logarithm runs three
  quarters of a million times per design, the exponential once per factor
  per evaluation, and the power once per grid point in every Lawson round.
  Each is glibc's own routine spelled in numpy operations IEEE&nbsp;754 fixes
  exactly, plain arithmetic, integer bit work and table lookups: the
  table-driven `log` and the `log10` built on it, and the `exp` and `pow` of
  ARM's optimized-routines as glibc compiles them for a processor with a
  fused multiply-add, every multiply-add that build fuses reproduced by an
  exact emulation (rounding to odd, after Boldo and Melquiond). The sine,
  taken twice per design, the tangent, three times, and the magnitude of a
  complex root are correctly rounded, in exact integer arithmetic. Their bits
  are their own on every machine, which is stronger than calling anyone's
  libm. One call is still the platform's: the arctangent, once per design
  over the 257 points of the frequency grid. Spelling it the same way is the
  remaining step to one digest everywhere, and the correctly rounded value
  will not do it alone: glibc's own arctangent rounds 19 of the
  15&nbsp;866 arctangents the corpus evaluates the other way, so only its
  own routine keeps the shipped Linux coefficients where they are, and its
  build with fused multiply-adds at that, the one `exp` and `pow` spell:
  glibc's arctangent, like its sine and tangent, rounds differently in its
  two builds.
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
- **The corpus is byte-identical.** The designs of seven curves at nineteen
  sampling rates, 133 in all, hash to the same single SHA-256 before and
  after the logarithm was vectorised, and again after the exponential, the
  power, the base-10 logarithm, the sine, the tangent and the complex
  magnitudes were pinned: no shipped coefficient, figure or conformance value
  moved.
- **The exponential and the power, bit for bit.** Every distinct value the
  corpus hands `exp` (677&nbsp;596 of them) and `pow` (580&nbsp;455) returns
  glibc's bits, and so does each of 120 million draws over each routine's
  domain, the edges of overflow and underflow and the subnormal results
  included. The fused multiply-add emulation returns the C library's `fma`
  on every one of 30 million draws, half of them nearly cancelling.
- **Correctly rounded where glibc is.** On the 70 sines, 105 tangents and 67
  complex magnitudes the corpus evaluates, glibc returns the correctly
  rounded value, so the correctly rounded routines return its bits there.
  Away from the corpus that rests on glibc's accuracy rather than on a
  proof: over every integer sampling rate from 100&nbsp;Hz to 200&nbsp;kHz,
  5&nbsp;864 of the 1&nbsp;399&nbsp;307 (rate, curve) designs meet a sine or
  a tangent glibc rounds the other way, and those designs can move with the
  pin, by what one ulp of a start grows into through the fit. None is at a
  rate the library is checked at; of the common rates, 50&nbsp;kHz for A, B,
  C and D and 100&nbsp;kHz for AU, which moves from `7ee0fe06b2a91373` to
  `ec6c060d4b27d1b9`.
- **No C library left but the arctangent's.** With every result the C
  library returns to a design pushed one unit in the last place, by a shim
  between Python and the C library, the designs do not move, except when the
  arctangent's is pushed, which moves them all. Under musl, another C
  library, the whole corpus hashes to glibc's SHA-256 once the arctangent
  agrees, and so do the A and D weightings at 48&nbsp;kHz under glibc and
  musl on 64-bit ARM, the processor family of the macOS leg of the CI
  matrix, run in emulation.
- **Digest for digest across environments.** The designs are bit-identical
  between this host and the same host under AVX-512 emulation, under every
  selectable OpenBLAS kernel set, every thread count and every hash seed;
  the environment-versus-environment comparisons are pinned as tests.
- **One digest on three platforms, the arctangent aside.** With only the
  logarithm pinned, the A weighting at 48&nbsp;kHz hashed to
  `991833ff389afe91` on Linux (glibc, x86-64), `4efa1818bd80e23a` on macOS
  (arm64) and `79852a57e60961c8` on Windows (x86-64). Now a test in the CI
  matrix designs it with a correctly rounded arctangent of its own, which is
  glibc's on all 257 points of that grid, and holds `991833ff389afe91` on all
  three platforms: no other routine of the C library reaches the design, and
  the BLAS and LAPACK steps are under Scope. The design a machine ships
  still takes its arctangent from the platform, so a second test designs it
  that way and holds the same digest wherever the platform's arctangent is
  correctly rounded on all 257 points, as glibc's is, and the platform's own
  measured digest where it is not. On glibc x86-64 without FMA the shipped
  design hashed to `43f786ffab5c4dd4` before the pin and hashes to
  `991833ff389afe91` now. The response tests that run on the same three
  platforms hold the A design within 0.013&nbsp;dB of its analog prototype
  everywhere in its fit band, which bounds what any difference left can
  amount to in response.

## See it yourself

Two designs are the same design, and the bytes have a name:

```python
import hashlib
from phonometry import filters

once = filters.WeightingFilter(48000, "A").sos
again = filters.WeightingFilter(48000, "A").sos
print(once.tobytes() == again.tobytes())                 # True
digest = hashlib.sha256(once.tobytes()).hexdigest()
print(digest[:16])                                       # 991833ff389afe91 on Linux
```

The second line is the point: those sixteen hex digits, the head of the
SHA-256, are not "what my machine got", they are the digest of this release's
A weighting at 48&nbsp;kHz on any glibc Linux machine, the leg the CI matrix
pins, and on any other platform whose arctangent agrees with glibc's on the
grid. If a future release moves a
coefficient deliberately, the digest moves with it and the change is a
documented event, never a property of your hardware.

## Scope

The guarantee covers the deterministic weighting design path end to end on
one platform, and block processing composes with it: a stateful cascade fed
block by block is bit-identical to one pass over the whole record, so
streaming does not spend the guarantee. General analysis functions built on numpy and SciPy in their
ordinary form remain reproducible on one machine but may differ in the last
bits across CPUs, which is the normal condition of scientific Python; the
deterministic treatment is applied where a filter's identity matters.

Two steps of the realised cascade go through a library rather than the C
library: the poles of the BS.468-4 prototype are numpy's polynomial roots,
which LAPACK computes, and the second-order sections are formed by SciPy,
whose polynomial products go through the BLAS. Both give the same bytes under
every OpenBLAS kernel set and on the 64-bit ARM and musl builds measured; a
BLAS that fused those products would move the D and G designs, measured by
fusing them on purpose, and the Accelerate framework the macOS build of numpy
links is not measured here. SciPy's `zpk2sos` also takes complex
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

- [Conformance report](../CONFORMANCE.md): what the numbers are checked against; this page is why the checks read the same everywhere.
- [Errata in published sources](../ERRATA.md): the other half of the evidence story: where the printed expected value is the thing that is wrong.
- [Frequency weightings](../signals/levels/weighting.md): the guide to the curves the deterministic design realises.
- [Block processing](../signals/filters/block-processing.md): the streaming identity the scope section leans on.

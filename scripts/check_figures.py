#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Tolerance-aware staleness check for the committed documentation figures.

The ``Documentation figures up to date`` CI job regenerates ``.github/images``
with ``make graphs`` and must confirm the result still matches what is
committed. A byte-exact ``git diff`` cannot do this reliably: GitHub's runner
fleet is hardware-heterogeneous, so the same pinned software stack computes a
handful of plotted path coordinates ~1 ULP apart depending on which CPU
microarchitecture the run lands on (a different SIMD kernel in the numpy/BLAS
stack). That sub-pixel drift is numerically and visually irrelevant, yet a
byte diff flags the figure as stale, which made the job intermittently fail.

This script compares the freshly regenerated working-tree figures against the
committed versions (``git HEAD``) within a tolerance instead:

* **SVG** -- the non-numeric structure (elements, text, colours, ordering)
  must be identical, and every numeric token must agree within an absolute or
  relative tolerance. A moved element, changed label or new path fails; a
  last-bit coordinate wobble passes.
* **Raster (WebP/PNG)** -- identical dimensions, at most
  :data:`RASTER_TOL`\ ``.max_sig_pixels`` meaningfully changed pixels and a
  bounded root-mean-square difference (see
  :class:`~generated_assets.RasterTolerance`).
* **Anything else** -- exact byte compare.

Added or removed files always fail: a new figure must be committed, and a
figure that is no longer generated must be removed from the tree.

The check is intentionally strict about *structure* and lenient only about the
*last digits of numbers*, so it still catches every real figure change while
being immune to cross-CPU floating-point non-determinism.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from generated_assets import (
    NumericTolerance,
    RasterTolerance,
    committed_bytes,
    numbers_within_tolerance,
    raster_problem,
    tracked_files,
)

IMG_DIR = ".github/images"

# Numeric tokens differing by less than this, in SVG user units, are treated
# as equal. The coordinates are written to generated_assets.SVG_DECIMALS
# places, so two machines that land either side of a rounding boundary differ
# by exactly one quantum, 0,01, whatever the magnitude, and the absolute term
# has to accept that. It is one and a half quanta rather than one because 0,01
# is not representable in binary: the difference of two such numbers comes
# out as 0,010000000000000002, and a tolerance of exactly one quantum rejected
# forty-five per cent of the consecutive pairs below a hundred when it was
# tried. Two quanta apart is rejected, which is what keeps a real edit
# visible.
#
# The relative term is zero on purpose. numbers_within_tolerance takes the
# larger of the two terms, and a relative term of 1e-4 let two quanta through
# at a coordinate of 200 and nine at 900, which is most of the canvas. Nothing
# legitimate needs it now: a rounded coordinate moves by one quantum or not at
# all, the glyph outlines are integers in font units, and the one number kept
# at full precision, the root element's size, wobbles by 1e-6 at most.
SVG_TOL = NumericTolerance(absolute=1.5e-2, relative=0.0)

# A pixel counts as "meaningfully changed" if any channel differs by more than
# ``level`` (0..255). Cross-CPU drift perturbs a coordinate by ~1e-6 units,
# i.e. a ~1e-5-pixel geometric shift, whose anti-aliasing effect rounds to at
# most a level or two on a few edge pixels -- far below this threshold. A real
# edit moves a plotted line or glyph, changing hundreds to thousands of edge
# pixels, and a restyled fill moves the whole image past the RMS bound.
RASTER_TOL = RasterTolerance(level=12, max_sig_pixels=100, rms=2.0)

# Integers and decimals, with optional sign and exponent. ``split``/``findall``
# with this pattern partition a file into fixed text and numeric values.
_TOKEN = re.compile(rb"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

# matplotlib derives clip-path / marker / collection ids by hashing the literal
# ``str()`` of the underlying float geometry (see backend_svg._make_id). A
# cross-CPU 1-ULP wobble in that geometry avalanches the whole SHA256, so the
# id *text* would change even though the figure is numerically identical -- the
# exact drift this check exists to tolerate. Canonicalising every id and its
# ``url(#...)`` / ``href="#..."`` references to placeholders numbered by first
# appearance removes the hash text from the structural comparison while still
# catching a genuine change (an id added, removed, reordered, or a reference
# repointed changes the placeholder sequence).
_IDREF = re.compile(rb'(\bid="|url\(#|xlink:href="#|\bhref="#)([A-Za-z_][\w.:\-]*)')


def _canonicalize_ids(data: bytes) -> bytes:
    """Rewrite hash-derived ids/references to first-appearance placeholders."""
    mapping: dict[bytes, bytes] = {}

    def repl(match: re.Match[bytes]) -> bytes:
        token = match.group(2)
        placeholder = mapping.setdefault(token, b"ID%d" % len(mapping))
        return match.group(1) + placeholder

    return _IDREF.sub(repl, data)


def _svg_within_tolerance(old: bytes, new: bytes) -> bool:
    """True if two SVGs match structurally and numerically within tolerance."""
    old = _canonicalize_ids(old)
    new = _canonicalize_ids(new)
    if _TOKEN.split(old) != _TOKEN.split(new):
        return False  # non-numeric structure (elements/text/colours) differs
    old_nums = _TOKEN.findall(old)
    new_nums = _TOKEN.findall(new)
    if len(old_nums) != len(new_nums):
        return False
    return all(
        numbers_within_tolerance(float(o_tok), float(n_tok), SVG_TOL)
        for o_tok, n_tok in zip(old_nums, new_nums, strict=True)
    )


def main() -> int:
    disk = {str(p) for p in Path(IMG_DIR).rglob("*") if p.is_file()}
    tracked = tracked_files(IMG_DIR)
    problems: list[str] = []

    problems.extend(
        f"new figure not committed: {path}" for path in sorted(disk - tracked)
    )
    problems.extend(
        f"committed figure no longer generated: {path}"
        for path in sorted(tracked - disk)
    )

    for path in sorted(disk & tracked):
        new = Path(path).read_bytes()
        old = committed_bytes(path)
        if old is None:
            problems.append(f"cannot read committed {path}")
            continue
        if old == new:
            continue  # byte-identical: fast path, no tolerance needed
        if path.endswith(".svg"):
            if not _svg_within_tolerance(old, new):
                problems.append(f"SVG changed beyond tolerance: {path}")
        elif path.endswith((".webp", ".png")):
            reason = raster_problem(old, new, RASTER_TOL)
            if reason is not None:
                problems.append(f"raster changed beyond tolerance ({reason}): {path}")
        else:
            problems.append(f"asset changed: {path}")

    if problems:
        print(
            "::error::.github/images is out of date - "
            "run 'make graphs' and commit the result."
        )
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"All {len(disk & tracked)} committed figures match within tolerance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Shared pieces of the tolerance-aware staleness checks.

Two committed directories are regenerated from the library and must not drift
from it: ``.github/images`` (:mod:`scripts.check_figures`) and
``.github/reports`` (:mod:`scripts.check_reports`). Both answer the same
question the same way -- regenerate into the working tree, then compare
against ``git HEAD`` -- and neither can do it with a byte diff, because
GitHub's runner fleet is hardware-heterogeneous and the same pinned stack
computes a few plotted coordinates ~1 ULP apart depending on which CPU
microarchitecture the run lands on.

``docs/conformance.json`` (:mod:`scripts.check_conformance_artifact`) is
regenerated and compared the same way and for the same reason, so the scalar
predicate the SVG comparison is built on lives here too rather than in one of
the three checkers.

What they share lives here: reading the committed bytes, listing what is
tracked, comparing two numbers within a tolerance, and comparing two rasters
within one. What differs stays in each checker, because the tolerances are not
the same: a documentation figure is a raster of a plot, a fiche preview is a
rasterized document page whose rendering runs through a pinned binary
rasterizer and is markedly quieter, and a conformance value is rounded to the
precision its own check declares.
"""

from __future__ import annotations

import io
import re
import subprocess
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class RasterTolerance:
    """How far two rasters of the same asset may drift and still match.

    The two criteria are complementary, and both must hold. ``max_sig_pixels``
    catches a *localised* change (a moved line, a relabelled axis) that a
    global root-mean-square would dilute across a large image; ``rms`` catches
    a *broad* change (a recoloured fill, a restyled background) that
    few-but-everywhere pixels would slip past the count. Cross-CPU sub-ULP
    coordinate drift moves neither meaningfully.

    :param level: Per-channel difference (0..255) above which a pixel counts
        as meaningfully changed rather than anti-aliasing noise.
    :param max_sig_pixels: How many such pixels are tolerated.
    :param rms: Largest tolerated per-channel root-mean-square difference.
    """

    level: float
    max_sig_pixels: int
    rms: float


@dataclass(frozen=True)
class NumericTolerance:
    """How far two computations of the same number may drift and still match.

    The absolute term carries the floor - for a raster coordinate it is a
    fraction of a pixel, for a conformance value it is one quantum of the
    precision the check reports at - and the relative term keeps the same
    judgement meaningful on a value of 10 000 as on a value of 0.001.

    :param absolute: Smallest difference always tolerated.
    :param relative: Difference tolerated as a fraction of the larger value.
    """

    absolute: float
    relative: float


def numbers_within_tolerance(old: float, new: float, tol: NumericTolerance) -> bool:
    """True if two computations of one number agree within ``tol``.

    :param old: The committed value.
    :param new: The freshly computed one.
    :param tol: The tolerance to judge them by.
    :return: Whether the difference is within the larger of the two terms.
    """
    limit = max(tol.absolute, tol.relative * max(abs(old), abs(new)))
    return abs(old - new) <= limit


#: Decimal places kept in the coordinates of a generated SVG. Matplotlib
#: writes six, which at the figure's scale of one user unit per point is a
#: hundredth of a micron; two is a hundredth of a point, three and a half
#: microns, below what any zoom of any display resolves. Measured over the
#: corpus the cut is a sixth of every file, and a rasterisation of the two at
#: three times display scale differs only in the antialiasing of glyph edges.
SVG_DECIMALS = 2

_SVG_NUMBER = re.compile(r"-?\d+\.\d+")
#: The attributes that carry coordinates or lengths in user units.
_SVG_COORDINATES = re.compile(
    r"\b(d|points|x|y|x1|y1|x2|y2|cx|cy|r|rx|ry|width|height|stroke-width|"
    r'stroke-dasharray|stroke-dashoffset|font-size)="([^"]*)"'
)
_SVG_TRANSFORM = re.compile(r'\btransform="([^"]*)"')
_SVG_TRANSLATE = re.compile(r"translate\(([^)]*)\)")


def _round_number(match: re.Match[str]) -> str:
    text = f"{float(match.group(0)):.{SVG_DECIMALS}f}".rstrip("0").rstrip(".")
    return "0" if text in ("", "-", "-0") else text


def _round_translate(match: re.Match[str]) -> str:
    return f"translate({_SVG_NUMBER.sub(_round_number, match.group(1))})"


def _round_transform(match: re.Match[str]) -> str:
    return f'transform="{_SVG_TRANSLATE.sub(_round_translate, match.group(1))}"'


def _round_coordinates(match: re.Match[str]) -> str:
    return f'{match.group(1)}="{_SVG_NUMBER.sub(_round_number, match.group(2))}"'


def compact_svg(text: str) -> str:
    """The same drawing with the digits nobody can see and the bytes nobody reads taken out.

    Coordinates and translations are rounded to :data:`SVG_DECIMALS`, and
    only those. A ``scale()`` keeps every digit, because the glyph outlines
    are drawn at ``scale(0.015625)`` and two decimals of that is a
    twenty-eight per cent error in every letter; so does the root ``<svg>``
    element, whose ``width`` and ``height`` fix the canvas and whose
    rounding moved it by a pixel. Both were found by rasterising before and
    after and counting the pixels that differed.

    The indentation between tags, the DOCTYPE and the metadata block go too.
    Nothing reads them: the figures are embedded as ``<img>``, and the
    metadata holds the matplotlib version, which is pinned elsewhere.

    ``check_figures.py`` compares the committed and the regenerated file of
    a figure number by number, and both pass through here, so its structure
    test sees the same text on both sides. Its numeric tolerance is set for
    the rounding: two runs that land either side of a rounding boundary are
    one quantum apart, and it accepts one quantum.
    """
    head, tag, body = text.partition("<svg ")
    if not tag:
        return text
    close = body.index(">")
    root, rest = body[: close + 1], body[close + 1 :]
    rest = _SVG_COORDINATES.sub(_round_coordinates, rest)
    rest = _SVG_TRANSFORM.sub(_round_transform, rest)
    text = head + tag + root + rest
    text = re.sub(r">\s+<", "><", text)
    text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", text, flags=re.DOTALL)
    return re.sub(r"<metadata>.*?</metadata>\s*", "", text, flags=re.DOTALL)


def committed_bytes(path: str) -> bytes | None:
    """Return the bytes of ``path`` as committed at HEAD, or ``None``."""
    result = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        capture_output=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def tracked_files(directory: str) -> set[str]:
    """Return the set of paths under ``directory`` tracked at HEAD."""
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD", directory],
        capture_output=True,
        text=True,
        check=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def raster_problem(old: bytes, new: bytes, tol: RasterTolerance) -> str | None:
    """Describe how two rasters differ beyond ``tol``, or ``None`` if within it."""
    a = np.asarray(Image.open(io.BytesIO(old)).convert("RGBA"), dtype=np.float64)
    b = np.asarray(Image.open(io.BytesIO(new)).convert("RGBA"), dtype=np.float64)
    if a.shape != b.shape:
        return f"dimensions changed {a.shape} != {b.shape}"
    diff = np.abs(a - b)
    sig_pixels = int(np.count_nonzero(diff.max(axis=-1) > tol.level))
    if sig_pixels > tol.max_sig_pixels:
        return f"{sig_pixels} pixels changed by >{tol.level:g} (> {tol.max_sig_pixels})"
    rms = float(np.sqrt(np.mean(diff**2)))
    if rms > tol.rms:
        return f"RMS {rms:.3f} > {tol.rms}"
    return None

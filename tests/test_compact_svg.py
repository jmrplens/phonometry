#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The pass every generated SVG goes through, and the tolerance it needs.

``generated_assets.compact_svg`` rounds the coordinates of a figure to two
decimals and drops the bytes nothing reads. Two of its rules were found by
rasterising a figure before and after and counting the pixels that differed,
and each has a test that breaks it:

* a ``scale()`` keeps every digit, because the glyph outlines are drawn at
  ``scale(0.015625)`` and two decimals of that is ``0.02``, a twenty-eight
  per cent error in every letter;
* the root ``<svg>`` element keeps its ``width``, ``height`` and ``viewBox``,
  because rounding them moved the canvas by a pixel.

The third thing is the comparison in ``check_figures.py``. Two machines that
land either side of a rounding boundary now differ by exactly one quantum, and
``0.01`` is not representable in binary, so the difference of two such numbers
comes out a hair above it. A tolerance of exactly one quantum rejected nearly
half of the consecutive pairs below a hundred. The sweep here holds the
tolerance to accepting every one-quantum step and rejecting every two-quantum
step, which is the whole band a real edit has to stay outside of.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_figures
import generated_assets as ga

_ROOT = (
    '<?xml version="1.0" encoding="utf-8" standalone="no"?>\n'
    '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
    '<svg xmlns="http://www.w3.org/2000/svg" width="892.996562pt" height="410.32pt" '
    'viewBox="0 0 892.996562 410.32" version="1.1">\n'
)


def _svg(body: str) -> str:
    return (
        _ROOT
        + " <metadata>\n  <dc:title>Matplotlib v3.11.1</dc:title>\n </metadata>\n"
        + body
        + "</svg>\n"
    )


def test_coordinates_are_cut_to_two_decimals() -> None:
    out = ga.compact_svg(
        _svg('<path d="M 123.456789 234.567891 L 0.004999 -0.005001"/>')
    )
    assert 'd="M 123.46 234.57 L 0 -0.01"' in out


def test_a_translate_is_rounded_and_a_scale_is_not() -> None:
    """The rule the pixels taught: 0.015625 is a glyph scale, not a coordinate."""
    body = (
        '<g transform="translate(393.232079 386.715312) scale(0.1 -0.1)">'
        '<path id="DejaVuSans-16" transform="scale(0.015625)" d="M 2597 2516"/>'
        '<use xlink:href="#DejaVuSans-44" transform="translate(96.728516 0.015625)"/>'
        "</g>"
    )
    out = ga.compact_svg(_svg(body))
    assert 'transform="translate(393.23 386.72) scale(0.1 -0.1)"' in out
    assert 'transform="scale(0.015625)"' in out
    assert 'transform="translate(96.73 0.02)"' in out


def test_the_root_element_keeps_its_canvas() -> None:
    """Rounding the root width moved the canvas by a pixel: it stays as drawn."""
    out = ga.compact_svg(_svg('<rect x="1.234567" width="2.345678"/>'))
    assert (
        'width="892.996562pt" height="410.32pt" viewBox="0 0 892.996562 410.32"' in out
    )
    assert '<rect x="1.23" width="2.35"/>' in out


def test_the_doctype_the_metadata_and_the_indentation_go() -> None:
    out = ga.compact_svg(_svg(' <g id="axes_1">\n  <path d="M 1.0 2.0"/>\n </g>\n'))
    assert "DOCTYPE" not in out
    assert "<metadata>" not in out
    assert "Matplotlib" not in out
    assert '<g id="axes_1"><path d="M 1 2"/></g></svg>' in out
    assert out.startswith('<?xml version="1.0"')


def test_colours_ids_and_the_xml_declaration_are_untouched() -> None:
    """Only geometry: a hex colour, an id with digits and the version stay."""
    body = (
        '<path id="line2d_10" style="fill:#1f77b4;stroke-opacity:0.6" d="M 5.5 6.5"/>'
    )
    out = ga.compact_svg(_svg(body))
    assert 'id="line2d_10"' in out
    assert "#1f77b4" in out
    assert 'version="1.1"' in out
    assert 'encoding="utf-8"' in out


def test_the_pass_is_idempotent() -> None:
    once = ga.compact_svg(
        _svg('<path d="M 1.005 2.995" transform="translate(3.005 4.005)"/>')
    )
    assert ga.compact_svg(once) == once


def test_text_without_an_svg_element_is_returned_unchanged() -> None:
    assert ga.compact_svg("not an svg") == "not an svg"


@pytest.mark.parametrize(
    ("start", "stop"),
    [(0, 100), (150, 250), (850, 950), (1_950, 2_050)],
    ids=["below a hundred", "around 200", "around 900", "around 2000"],
)
def test_the_tolerance_accepts_one_quantum_and_rejects_two(
    start: int, stop: int
) -> None:
    """Every consecutive pair of two-decimal values across the canvas.

    Below a hundred is where a tolerance of exactly 0,01 failed on the
    binary representation of the difference. The other three bands are
    where a relative term would have let two quanta through: at 200 a
    relative 1e-4 allowed 0,02 and at 900 it allowed 0,09, and review caught
    that the sweep had only ever looked below a hundred.
    """
    tol = check_figures.SVG_TOL
    values = [round(x / 100, 2) for x in range(start * 100, stop * 100)]
    one_apart_rejected = [
        a
        for a, b in zip(values, values[1:], strict=False)
        if not ga.numbers_within_tolerance(a, b, tol)
    ]
    two_apart_accepted = [
        a
        for a, b in zip(values, values[2:], strict=False)
        if ga.numbers_within_tolerance(a, b, tol)
    ]
    assert one_apart_rejected == []
    assert two_apart_accepted == []


def test_the_relative_term_is_zero_so_magnitude_buys_no_slack() -> None:
    """The one number kept at full precision still fits under the absolute term."""
    assert check_figures.SVG_TOL.relative == 0.0
    assert ga.numbers_within_tolerance(892.996562, 892.996563, check_figures.SVG_TOL)


@pytest.mark.parametrize("decimals", [ga.SVG_DECIMALS])
def test_the_tolerance_is_set_for_the_decimals_written(decimals: int) -> None:
    """Move one without the other and this says so."""
    quantum = 10.0**-decimals
    assert quantum < check_figures.SVG_TOL.absolute < 2 * quantum

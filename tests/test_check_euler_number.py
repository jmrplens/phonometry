#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The Euler-number gate, held against the shapes this corpus writes.

``scripts/check_euler_number.py`` fails on an italic ``e`` that is the
exponential's base, which ISO 80000-2 sets upright, and must leave alone every
other ``e``: the subscript of :math:`T_\mathrm{e}`, the e inside a word, the
constant already set upright, and an ``e`` with an exponent that is really a
variable because it also carries a subscript. These tests fix those readings
and the images the gate reads.
"""

from __future__ import annotations

import pathlib
import sys
from typing import TYPE_CHECKING

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_euler_number as cen

if TYPE_CHECKING:
    import pytest


def _write(tmp_path: pathlib.Path, name: str, text: str) -> pathlib.Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_an_italic_exponential_fails_with_its_line(tmp_path: pathlib.Path) -> None:
    """The defect the gate exists for, on the line that writes it."""
    path = _write(
        tmp_path,
        "weighting.md",
        "A running mean.\n\n$$\ny(t) = \\int x^2(\\xi)\\, e^{-(t-\\xi)/\\tau}\\, d\\xi\n$$\n",
    )
    read, failures = cen.check([path])
    assert read == 1
    assert len(failures) == 1
    assert "on line 4" in failures[0]


def test_the_upright_constant_passes(tmp_path: pathlib.Path) -> None:
    r"""``\mathrm{e}`` and ``\operatorname{e}`` are the constant, set right."""
    path = _write(
        tmp_path,
        "tube.md",
        "$p = \\mathrm{e}^{-jkx}$ and $\\operatorname{e}^{x}$ and $\\exp(-t)$\n",
    )
    _, failures = cen.check([path])
    assert failures == []


def test_an_e_that_is_not_the_exponential_is_left_alone(tmp_path: pathlib.Path) -> None:
    """A subscript, a word, a bare variable and a superscripted tensor."""
    path = _write(
        tmp_path,
        "notes.md",
        "$T_e^2$, $e_k$, $\\text{the}^2$, $R_{\\mathrm{e}}$, "
        "$x^{e}$ and the strain $2N e^s_{ij}$.\n",
    )
    assert cen.file_findings(path.read_text(encoding="utf-8"), ".md") == []
    _, failures = cen.check([path])
    assert failures == []


def test_a_braced_e_is_read_and_a_spaced_caret_too(tmp_path: pathlib.Path) -> None:
    """``{e}^{x}`` and ``e ^{x}`` are the same italic letter."""
    path = _write(tmp_path, "forms.md", "${e}^{x}$\n\n$e ^{-x}$\n")
    _, failures = cen.check([path])
    assert len(failures) == 1
    assert "on line 1, 3" in failures[0]


def test_docstring_mathematics_is_read(tmp_path: pathlib.Path) -> None:
    """The roles and blocks of a docstring are mathematics too."""
    path = _write(
        tmp_path,
        "module.py",
        'r"""Decay.\n\n:math:`e^{-t/\\tau}` falls.\n\n.. math::\n\n   a = e^{b}\n"""\n',
    )
    lines = cen.file_findings(path.read_text(encoding="utf-8"), ".py")
    assert lines == [3, 7]


def test_a_figure_label_is_read_from_its_comment(tmp_path: pathlib.Path) -> None:
    """matplotlib keeps the mathtext source of every text it draws."""
    images = tmp_path / "images"
    images.mkdir()
    (images / "decay.svg").write_text(
        '<?xml version="1.0"?>\n<svg><!-- $1 - e^{-t/\\tau}$ --></svg>',
        encoding="utf-8",
    )
    (images / "decay_es.svg").write_text(
        '<?xml version="1.0"?>\n<svg><!-- $1 - \\mathrm{e}^{-t/\\tau}$ --></svg>',
        encoding="utf-8",
    )
    read, failures = cen.check([], images)
    assert read == 2
    assert len(failures) == 1
    assert failures[0].startswith("  decay.svg")


def test_a_plate_label_writing_an_exponent_on_a_lone_e_fails(
    tmp_path: pathlib.Path,
) -> None:
    """The canvas sets a lone letter italic, so a plate writes ``exp(...)``."""
    from diagrams.canvas import LIGHT, SVG
    from generated_assets import compact_svg

    images = tmp_path / "images"
    images.mkdir()
    svg = SVG(900, 200, LIGHT)
    svg.text(450, 60, "$α = 1 − exp(−1/(f_s·τ))$", 16)
    svg.text(450, 120, "$y = e^{−t/τ}$", 16)
    (images / "diagram_decay.svg").write_text(
        compact_svg(svg.render("A plate")), encoding="utf-8"
    )
    _, failures = cen.check([], images)
    assert len(failures) == 1
    assert "e^{−t/τ}" in failures[0]


def test_a_declared_file_is_left_alone(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The escape hatch names the file and what its e is."""
    path = _write(tmp_path, "ellipse.md", "$e^2 = 1 - b^2/a^2$\n")
    _, failures = cen.check([path])
    assert len(failures) == 1
    monkeypatch.setitem(cen.DECLARED, "ellipse.md", "the eccentricity")
    _, failures = cen.check([path])
    assert failures == []


def test_the_tree_it_ships_with_passes() -> None:
    """The gate is green on this repository, which is what CI asserts."""
    root = pathlib.Path(__file__).resolve().parent.parent
    paths = cen.collect([str(root / r) for r in cen.DEFAULT_ROOTS])
    _, failures = cen.check(paths, root / cen.IMAGES)
    assert failures == []


def test_every_paragraph_of_a_math_block_is_read(tmp_path: pathlib.Path) -> None:
    """A block of two equations sets them in two paragraphs, and both count.

    The second equation of a ``.. math::`` block, after a blank line, used to
    fall outside the block, so its italic e reached the page unread.
    """
    path = _write(
        tmp_path,
        "tube.py",
        'r"""Faces.\n\n.. math::\n\n   p = \\mathrm{e}^{-jkd}\n\n'
        '   u = e^{-jkd}\n\nAfter the block.\n"""\n',
    )
    lines = cen.file_findings(path.read_text(encoding="utf-8"), ".py")
    assert lines == [7]


def test_an_exponential_inside_a_cases_block_is_read(tmp_path: pathlib.Path) -> None:
    r"""A row break ``\\`` is TeX, not the doubled backslash of a pattern.

    The time-weighting coefficient and the spreading function of the loudness
    model are written as ``cases`` blocks, and the gate passed over both
    because it took every region holding ``\\`` for a regex.
    """
    path = _write(
        tmp_path,
        "weighting.md",
        "$$\n\\alpha = \\begin{cases} 1 - e^{-1/(f_\\mathrm{s} \\tau)} & F \\\\\n"
        "  1 - \\mathrm{e}^{-1/(f_\\mathrm{s} \\tau)} & S\\end{cases}\n$$\n",
    )
    assert cen.file_findings(path.read_text(encoding="utf-8"), ".md") == [2]


def test_an_exponential_after_a_command_opening_with_d_is_read(
    tmp_path: pathlib.Path,
) -> None:
    r"""``(\delta`` and ``(\dfrac`` are TeX; only ``(\d`` alone is a pattern."""
    path = _write(
        tmp_path,
        "absorption.md",
        "$\\eta(\\delta)\\, e^{-x}$ and $\\left(\\dfrac{a}{b}\\right) e^{y}$\n",
    )
    assert cen.file_findings(path.read_text(encoding="utf-8"), ".md") == [1, 1]


def test_an_exponential_after_a_formula_that_wraps_is_read(
    tmp_path: pathlib.Path,
) -> None:
    """An inline formula may break across one line of a paragraph.

    Paired line by line, the closing dollar of the wrapped formula was taken
    for an opening one, the text after it was read as mathematics and the
    exponential that followed was read as text.
    """
    path = _write(
        tmp_path,
        "mobility.md",
        "The window $w(t) = \\mathrm{e}^{-at}$, with $a = \\pi\\,\n"
        "\\Delta f$ (Formula (A.1)) by $e^{-at}$ again.\n\n"
        "A new paragraph $x$\n\nis not joined to $y$.\n",
    )
    assert cen.file_findings(path.read_text(encoding="utf-8"), ".md") == [2]


def test_an_escaped_label_in_a_module_is_read(tmp_path: pathlib.Path) -> None:
    r"""A label in a plain string doubles every backslash, and is still TeX."""
    path = _write(
        tmp_path,
        "labels.py",
        'A = "$\\\\mathrm{e}^{-t}$"\nB = "$\\\\alpha\\\\, e^{-t}$"\n',
    )
    assert cen.file_findings(path.read_text(encoding="utf-8"), ".py") == [2]


def test_the_base_of_the_natural_logarithm_is_the_constant(
    tmp_path: pathlib.Path,
) -> None:
    r"""ISO 80000-2, item 2-13.5, prints :math:`\log_\mathrm{e} x` upright."""
    path = _write(
        tmp_path,
        "log.md",
        "$\\ln x = \\log_e x$, $\\log_{e} y$ and $\\log_\\mathrm{e} z$\n",
    )
    assert cen.file_findings(path.read_text(encoding="utf-8"), ".md") == [1, 1]

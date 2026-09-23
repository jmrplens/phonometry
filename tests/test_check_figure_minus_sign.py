#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate that reads every committed figure for a number signed with a hyphen.

The corpus signs its negative numbers with U+2212 and three things wrote the
hyphen-minus anyway: the polar ``ThetaFormatter``, which ignores
``axes.unicode_minus``; a reading assembled with an f-string; and the plates,
which set exactly the characters they are handed. ``_fmt_minus`` and the
library's ``fmt_minus`` are pinned by their own tests; these pin the gate that
reads the finished assets, so that it fires on a sign and on nothing else.

What is a sign is decided by the character before the hyphen, and the tests
walk through the hyphens that are not one: a designation, a compound, a range
and an exponent. Mathtext is the other half: matplotlib sets ``$-3$`` with the
minus sign itself, so between dollars a matplotlib figure is not read, while a
plate draws what it is given and is. The last tests put real matplotlib output
under the gate, because what the formatter writes is the fact the gate rests
on.
"""

from __future__ import annotations

import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_figure_minus_sign as gate
from diagrams.canvas import signed
from figures.i18n import _fmt_minus

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.projections.polar import PolarAxes

MINUS = "−"


@pytest.fixture
def images(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """An empty corpus with no allowances, so each test states its own."""
    monkeypatch.setattr(gate, "ALLOWED", {})
    return tmp_path


@pytest.fixture
def _default_rc() -> Iterator[None]:
    """Stock matplotlib, so the formatters are the ones matplotlib ships."""
    with mpl.rc_context(mpl.rcParamsDefault):
        yield
    plt.close("all")


def _drawing(
    images: pathlib.Path, name: str, *labels: str, matplotlib: bool = True
) -> None:
    """Write an SVG that records having drawn *labels*, as the generators do.

    A matplotlib figure opens with its root group, which is how the gate tells
    it from a plate.
    """
    drawn = "\n".join(f"   <!-- {label} -->\n   <g/>" for label in labels)
    root = '<g id="figure_1"/>\n' if matplotlib else ""
    images.mkdir(parents=True, exist_ok=True)
    (images / f"{name}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg">\n{root}{drawn}\n</svg>\n',
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "text",
    [
        "-3",
        "-0.6",
        "-.5",
        "-30°",
        "-20 dB",
        "axial, $c_3$ = -0.6",
        "range -10 to 35 °C",
        "(-2 dB)",
        "[-1, 1]",
    ],
)
def test_a_hyphen_before_a_number_is_a_sign(text: str) -> None:
    assert gate.signed_with_hyphen(text, mathtext=True)


@pytest.mark.parametrize(
    "text",
    [
        f"{MINUS}3",
        f"{MINUS}30°",
        # A designation, a compound, a range and an exponent: a hyphen after
        # a letter, a digit or a point joins what is on either side of it.
        "IEC 61672-1",
        "nmfs-2024",
        "10-90 % fractile band",
        "1e-05",
        "0.5-1",
        # A hyphen that no digit follows is not a sign of anything.
        "A-weighted",
        "one - two",
        "-",
    ],
)
def test_a_hyphen_that_joins_is_not_a_sign(text: str) -> None:
    assert not gate.signed_with_hyphen(text, mathtext=True)


@pytest.mark.parametrize(
    ("text", "on_a_plate"),
    [
        ("$-3$", True),
        (r"$\mathdefault{10^{-2}}$", True),
        ("$L_{p,C} - L_{p,A}$ = \u22121 dB", False),
        (r"$e^{-x}$", False),
    ],
)
def test_mathtext_is_read_only_where_it_does_not_set_the_minus(
    text: str, *, on_a_plate: bool
) -> None:
    """matplotlib sets every ``-`` between dollars as U+2212; a plate does not."""
    assert not gate.signed_with_hyphen(text, mathtext=True)
    assert gate.signed_with_hyphen(text, mathtext=False) is on_a_plate


def test_a_hyphen_outside_the_dollars_is_still_read() -> None:
    assert gate.signed_with_hyphen("$c_3$ = -0.6", mathtext=True)


def test_every_variant_is_read_and_reported_once(images: pathlib.Path) -> None:
    """Both languages and both themes ship, and the figure is named once."""
    for suffix in ("", "_dark", "_es", "_es_dark"):
        _drawing(images, f"half_disc{suffix}", "-90°", f"{MINUS}15")
    found, stale = gate.check(images)
    assert found == [("half_disc", "-90°")]
    assert stale == []


def test_a_figure_signed_with_the_minus_sign_passes(images: pathlib.Path) -> None:
    _drawing(images, "half_disc", f"{MINUS}90°", f"{MINUS}0,6", "ISO 9613-2", "$-3$")
    assert gate.check(images) == ([], [])


def test_a_plate_is_read_between_the_dollars(images: pathlib.Path) -> None:
    """The plate composer draws the character it is given, even in maths."""
    _drawing(images, "diagram_setup", "$q$ = -300 m", matplotlib=False)
    found, _ = gate.check(images)
    assert found == [("diagram_setup", "$q$ = -300 m")]


def test_an_allowed_string_passes_and_a_stale_allowance_fails(
    images: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A part number is not a sign, and the allowance cannot rot."""
    monkeypatch.setattr(
        gate, "ALLOWED", {"diagram_parts: ISO 389-1 / -2": "parts of one standard"}
    )
    _drawing(images, "diagram_parts", "ISO 389-1 / -2", matplotlib=False)
    assert gate.check(images) == ([], [])

    _drawing(images, "diagram_parts", "ISO 389-1 / -8", matplotlib=False)
    found, stale = gate.check(images)
    assert found == [("diagram_parts", "ISO 389-1 / -8")]
    assert stale == ["diagram_parts: ISO 389-1 / -2"]


def test_the_command_line_fails_on_a_sign_and_passes_without(
    images: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _drawing(images, "half_disc", "-60°")
    assert gate.main([str(images)]) == 1
    assert "half_disc" in capsys.readouterr().err

    _drawing(images, "half_disc", f"{MINUS}60°")
    assert gate.main([str(images)]) == 0


@pytest.mark.usefixtures("_default_rc")
def test_the_polar_angle_formatter_writes_a_hyphen(images: pathlib.Path) -> None:
    """The formatter this gate was written for, as matplotlib ships it.

    ``ThetaFormatter`` ignores ``axes.unicode_minus``, so a half disc from
    -90° to 90° labels its lower half with the hyphen. Restating the grid with
    explicit labels is the fix the generators use.
    """
    _fig, axes = plt.subplots(subplot_kw={"projection": "polar"})
    polar: PolarAxes = axes
    polar.set_thetamin(-90.0)
    polar.set_thetamax(90.0)
    plt.savefig(images / "half_disc.svg")
    found, _ = gate.check(images)
    assert ("half_disc", "-90°") in found

    polar.set_thetagrids(
        np.arange(-90, 91, 30), [f"{_fmt_minus(a, '.0f')}°" for a in range(-90, 91, 30)]
    )
    plt.savefig(images / "half_disc.svg")
    plt.close()
    assert gate.check(images) == ([], [])


@pytest.mark.usefixtures("_default_rc")
def test_mathtext_really_sets_the_minus_sign(images: pathlib.Path) -> None:
    """What makes it safe to leave mathtext unread in a matplotlib figure.

    The outlines of ``$-3$`` are the outlines of ``−3``, not of ``-3``: the
    glyph matplotlib places for the sign is the minus sign's.
    """

    def glyphs(label: str) -> list[str]:
        fig = plt.figure(figsize=(1, 1))
        fig.text(0.1, 0.5, label)
        path = images / "sign.svg"
        fig.savefig(path)
        plt.close(fig)
        source = path.read_text(encoding="utf-8")
        return sorted(part.split('"')[0] for part in source.split('id="DejaVu')[1:])

    assert glyphs("$-3$") == glyphs(f"{MINUS}3")
    assert glyphs("$-3$") != glyphs("-3")


@pytest.mark.parametrize(
    ("value", "spec", "expected"),
    [
        (-10, "", f"{MINUS}10"),
        (-70, "d", f"{MINUS}70"),
        (-1.0, "g", f"{MINUS}1"),
        (0, "", "0"),
        (4.0, "g", "4"),
        # The hyphen of an exponent belongs to the number.
        (1e-05, "g", "1e-05"),
        (-1e-05, "g", f"{MINUS}1e-05"),
    ],
)
def test_a_plate_signs_its_numbers_with_the_minus_sign(
    value: float, spec: str, expected: str
) -> None:
    """The plates' own helper, since they have no formatter in front of them."""
    assert signed(value, spec) == expected


def test_every_allowance_carries_a_reason() -> None:
    assert all(reason.strip() for reason in gate.ALLOWED.values())


def test_the_committed_figures_pass() -> None:
    """The corpus itself, which is what the gate protects."""
    found, stale = gate.check(gate.IMAGES)
    assert found == []
    assert stale == []

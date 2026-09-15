#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate that reads the committed Spanish figures for an English decimal.

Three separate machines write the decimal comma of a Spanish figure, and the
panels none of them reached shipped for months with every gate green: a log
distance axis, the ``z`` of a 3-D array, a zoom inset, a contour colorbar and
the frequency axis of a call that did not pass the language on. Asking each
machine whether it covered everything is how that happened; this asks the
finished asset instead, which is what a reader opens.

These tests pin the reading. The label has to be a number and nothing else, so
that prose and a clause number are left alone; the English figures are not read
at all; and the allowance table is held to the same two rules as every other in
the tree, a reason for each entry and a failure when an entry stops matching.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_figure_decimal_point as gate


@pytest.fixture
def images(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """An empty corpus with no allowances, so each test states its own."""
    monkeypatch.setattr(gate, "ALLOWED", {})
    return tmp_path


def _figure(images: pathlib.Path, name: str, *labels: str) -> None:
    """Write an SVG that records having drawn *labels*, as matplotlib does."""
    drawn = "\n".join(f"   <!-- {label} -->\n   <g/>" for label in labels)
    images.mkdir(parents=True, exist_ok=True)
    (images / f"{name}.svg").write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg">\n{drawn}\n</svg>\n',
        encoding="utf-8",
    )


def test_a_spanish_figure_with_an_english_decimal_fails(
    images: pathlib.Path,
) -> None:
    """The published defect: the axis says 31.5 and the legend says 52,4."""
    _figure(images, "band_levels_es", "31.5", "63", "125", "$L_p$ = 52,4 dB")
    found, stale = gate.check(images)
    assert found == [("band_levels", "31.5")]
    assert stale == []


def test_the_dark_twin_is_read_too(images: pathlib.Path) -> None:
    """Both Spanish variants ship, so both are read."""
    _figure(images, "band_levels_es_dark", "0.10")
    found, _ = gate.check(images)
    assert found == [("band_levels", "0.10")]


def test_a_spanish_figure_with_a_comma_passes(images: pathlib.Path) -> None:
    _figure(images, "band_levels_es", "31,5", "63", "−0,004", "2,5k")
    assert gate.check(images) == ([], [])


def test_an_english_figure_is_not_read(images: pathlib.Path) -> None:
    """The English figure is correct with the point, and is the byte reference."""
    _figure(images, "band_levels", "31.5")
    _figure(images, "band_levels_dark", "31.5")
    assert gate.check(images) == ([], [])


def test_a_decimal_inside_a_longer_label_is_left_to_the_other_check(
    images: pathlib.Path,
) -> None:
    """Prose is the business of ``scripts/check_decimal_comma.py``.

    Reading it here would report every clause reference and every standard
    designation a figure names, and a gate that cries wolf is switched off.
    """
    _figure(
        images,
        "barrier_es",
        "según el apartado 7.4",
        "ISO 9613-2",
        "$L_\\mathrm{eq}$ = 52.4 dB",
    )
    assert gate.check(images) == ([], [])


def test_an_allowed_label_passes_and_a_stale_allowance_fails(
    images: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A clause number is not a measurement, and the allowance cannot rot."""
    monkeypatch.setattr(gate, "ALLOWED", {"diagram_es_clauses: 9.1": "a clause"})
    _figure(images, "diagram_es_clauses_es", "9.1")
    assert gate.check(images) == ([], [])

    _figure(images, "diagram_es_clauses_es", "9.2")
    found, stale = gate.check(images)
    assert found == [("diagram_es_clauses", "9.2")]
    assert stale == ["diagram_es_clauses: 9.1"]


def test_every_allowance_carries_a_reason() -> None:
    assert all(reason.strip() for reason in gate.ALLOWED.values())


def test_the_committed_figures_pass() -> None:
    """The corpus itself, which is what the gate protects."""
    found, stale = gate.check(gate.IMAGES)
    assert found == []
    assert stale == []

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the form of ISO 10140-1:2021 Figure H.4 (``.report()`` -> PDF).

The sheet's numbers are pinned to a printed result: the improvement of
ISO 717-2:2020 Annex C, Table C.2, carried through the Annex H front end,
prints ΔLw = 15 dB as the standard does. The rest is structural, checked by
reading the text back out of the PDF: every field of the form, the frequency
range of the rating marked on the diagram, the two floor ratings H.5 i) asks
for, the C_I,r,50-2500 the reference floor cannot give, and one page with a
full header over 21 bands, in both languages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
import reference_data as ref

pytest.importorskip("reportlab")

from report_assertions import assert_one_page

from phonometry import ReportMetadata, building

if TYPE_CHECKING:
    from pathlib import Path

#: The 16 rating bands, 100 Hz to 3150 Hz.
_CORE = [float(f) for f in ref.ISO717_2_REFERENCE_FLOOR_FREQ]
#: The 21 bands of the form, 50 Hz to 5000 Hz.
_FORM_BANDS = [50.0, 63.0, 80.0, *_CORE, 4000.0, 5000.0]

#: A full header, every field of the form filled.
_FULL = ReportMetadata(
    manufacturer="Example floorings",
    product="Resilient vinyl, 3,2 mm",
    client="Example client",
    test_room="Floor transmission suite (example)",
    mounted_by="Example laboratory",
    test_date="2026-10-01",
    specimen="Vinyl sheet with foam backing, laid loose; four tapping-machine positions",
    mass_per_area=2.9,
    curing_time_h=0.0,
    source_temperature_c=21.2,
    source_relative_humidity_percent=48.0,
    receiving_volume=58.0,
    laboratory="Example laboratory",
    operator="Example operator",
    report_id="H-1",
    requirement=15.0,
)


def _text(path: Path) -> str:
    from pypdf import PdfReader

    return " ".join(
        " ".join(page.extract_text() for page in PdfReader(str(path)).pages).split()
    )


def _annex_c2() -> building.LabFloorCoveringImprovementResult:
    """ISO 717-2:2020 Table C.2 on the heavyweight floor, ΔLw = 15 dB printed."""
    bare = np.full(16, 75.0)
    return building.lab_floor_covering_improvement(
        bare, bare - np.asarray(ref.ISO717_2_ANNEX_C2_DELTA_L), _CORE
    )


def _form_bands() -> building.LabFloorCoveringImprovementResult:
    """A vinyl on the concrete floor over the 21 bands of the form."""
    ln0 = np.array(
        [62.4, 64.1, 65.8, 67.3, 68.0, 68.9, 69.6, 70.3, 71.0, 71.8, 72.5]
        + [73.1, 73.6, 74.0, 74.2, 74.1, 73.8, 73.2, 72.5, 71.4, 70.1]
    )
    delta = np.array(
        [0.3, 0.1, 0.6, 0.8, 1.2, 2.0, 3.4, 5.1, 7.2, 9.6, 12.3]
        + [15.0, 17.8, 20.4, 23.1, 25.6, 27.9, 30.1, 31.8, 33.2, 34.0]
    )
    return building.lab_floor_covering_improvement(ln0, ln0 - delta, _FORM_BANDS)


def test_form_prints_the_printed_annex_c_rating(tmp_path: Path) -> None:
    """The rating box reads ΔLw = 15 dB, as ISO 717-2:2020 Table C.2 prints."""
    out = tmp_path / "h4.pdf"
    _annex_c2().report(str(out))
    assert_one_page(out)
    text = _text(out)
    assert f"∆Lw = {ref.ISO717_2_ANNEX_C2_DELTA_LW} dB" in text
    assert f"CI,∆ = {ref.ISO717_2_ANNEX_C2_CI_DELTA} dB" in text


def test_full_form_over_21_bands_is_one_page(tmp_path: Path) -> None:
    out = tmp_path / "full.pdf"
    _form_bands().report(str(out), metadata=_FULL)
    assert_one_page(out)
    text = _text(out)
    for field in (
        "Manufacturer",
        "Product identification",
        "Test room identification",
        "Test specimen mounted by",
        "Type of reference floor",
        "Curing time [h]",
        "Air temp. in the source room",
        "Air humidity in the source room",
        "Receiving room volume",
        "artificial source",
    ):
        assert field in text
    assert "Heavyweight reference floor" in text
    assert "CI,r,50-2500: not formed" in text
    assert "Ln,0,w (CI,0)" in text
    assert "PASS" in text
    assert "34.0" in text  # the 5000 Hz improvement


def test_lightweight_floor_names_its_designation(tmp_path: Path) -> None:
    bare = np.full(16, 75.0)
    res = building.lab_floor_covering_improvement(
        bare, bare - np.linspace(1.0, 25.0, 16), _CORE, reference_floor="lightweight_3"
    )
    out = tmp_path / "light.pdf"
    res.report(str(out))
    text = _text(out)
    assert "∆Lt,3,w" in text
    assert "CI∆,t3" in text


def test_requirement_fails_below_it(tmp_path: Path) -> None:
    out = tmp_path / "fail.pdf"
    _annex_c2().report(str(out), metadata=ReportMetadata(requirement=20.0))
    assert "FAIL" in _text(out)


def test_requirement_met_exactly_passes(tmp_path: Path) -> None:
    """ΔLw = 15 dB against a requirement of 15 dB: "required ≥ 15 dB" holds."""
    out = tmp_path / "boundary.pdf"
    _annex_c2().report(str(out), metadata=ReportMetadata(requirement=15.0))
    assert "∆Lw = 15 dB, required ≥ 15 dB → PASS" in _text(out)


def test_header_prints_each_value_beside_its_label(tmp_path: Path) -> None:
    """Values no other field can carry, so each one is found only in its row."""
    out = tmp_path / "header.pdf"
    _annex_c2().report(
        str(out), metadata=ReportMetadata(curing_time_h=36.0, mass_per_area=2.9)
    )
    text = _text(out)
    assert "Curing time [h]: 36" in text
    assert "Mass of test specimen per unit area [kg/m2]: 2.9" in text


def test_spanish_verbose_form_is_one_page(tmp_path: Path) -> None:
    out = tmp_path / "es.pdf"
    _form_bands().report(str(out), metadata=_FULL, verbose=True, language="es")
    assert_one_page(out)
    text = _text(out)
    assert "Reducción del nivel de presión acústica de impactos" in text
    assert "Tiempo de curado" in text
    assert "34,0" in text


def test_form_needs_the_weighted_reduction(tmp_path: Path) -> None:
    res = building.lab_floor_covering_improvement(
        [70.0] * 3, [60.0] * 3, [500, 630, 800]
    )
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="weighted reduction"):
        res.report(out)


def test_form_refuses_an_unknown_engine(tmp_path: Path) -> None:
    res = _annex_c2()
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        res.report(out, engine="latex")


def test_curing_time_may_be_zero_but_not_negative() -> None:
    assert ReportMetadata(curing_time_h=0.0).curing_time_h == pytest.approx(0.0)
    with pytest.raises(ValueError, match="curing_time_h"):
        ReportMetadata(curing_time_h=-1.0)


def test_diagram_marks_the_frequency_range_of_the_rating() -> None:
    """Figure H.4 key 1: the rating range 100 Hz to 3150 Hz, dashed."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    res = _form_bands()
    ax = res.plot(rating_range=True)
    dashed = [line for line in ax.lines if line.get_linestyle() == "--"]
    positions = sorted(float(line.get_xdata()[0]) for line in dashed)
    assert positions == [3.0, 18.0]  # 100 Hz and 3150 Hz on the band axis
    plt.close("all")

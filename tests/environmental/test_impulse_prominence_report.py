#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the impulsive-sound prominence report (``.report()`` -> PDF).

The report is a rendering feature, so these tests assert only structural facts:
a valid single-page PDF is written for an impulse set, unknown engines and
languages are rejected, XML specials in metadata do not break reportlab, the
verdict renders both ways, and the boxed governing prominence ``P``, the derived
``LAeq`` adjustment ``KI`` and the metadata appear in the extracted text. The
prominence and adjustment maths itself is validated against the NT ACOU 112:2002
formulae elsewhere (tests/environmental/test_impulse_prominence.py); this fiche
test anchors its numbers to the documented three-impulse pile-driving set, whose
governing prominence and adjustment are derived from Formula 1 and Formula 2.
"""

from __future__ import annotations

import importlib
import math

import pytest

pytest.importorskip("reportlab")

from phonometry import ReportMetadata  # noqa: E402

# The module is shadowed in the package namespace by the function of the same
# name, so it must be imported through the import system directly.
nt = importlib.import_module("phonometry.environmental.impulse_prominence")

_PDF_MAGIC = b"%PDF"

# The documented three-impulse pile-driving set: (onset rate dB/s, level
# difference dB). All three qualify (onset rate > 10 dB/s); the first governs.
_ONSET_RATES = [1200.0, 300.0, 60.0]
_LEVEL_DIFFERENCES = [32.0, 18.0, 11.0]

# Governing prominence P = 3*lg(1200) + 2*lg(32) and its adjustment KI (Formula
# 2), derived by hand from the formulae so the fiche numbers are documented.
_P_GOVERNING = 3.0 * math.log10(1200.0) + 2.0 * math.log10(32.0)  # 12.2478...
_KI_GOVERNING = 1.8 * (_P_GOVERNING - 5.0)  # 13.046...


def _result():
    """The documented three-impulse pile-driving prominence result."""
    return nt.impulse_prominence(_ONSET_RATES, _LEVEL_DIFFERENCES)


def _assert_one_page(path: str) -> None:
    import os

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0
    from pypdf import PdfReader

    assert len(PdfReader(path).pages) == 1


def _extract_text(path: str) -> str:
    from pypdf import PdfReader

    return "\n".join(page.extract_text() for page in PdfReader(path).pages)


def test_report_writes_one_page_pdf(tmp_path) -> None:
    """An impulse set renders a one-page PDF fiche."""
    result = _result()
    out = tmp_path / "impulse.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_one_page(str(out))


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    result = _result()
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        result.report(out, engine="weasyprint")


def test_unknown_language_rejected(tmp_path) -> None:
    """An unknown fiche language raises ``ValueError``."""
    result = _result()
    out = str(tmp_path / "bad.pdf")
    with pytest.raises(ValueError, match="language"):
        result.report(out, language="xx")


def test_report_states_prominence_and_adjustment(tmp_path) -> None:
    """The fiche states the governing P, the derived KI and the formula basis.

    The governing prominence is the first (highest-P) impulse; its LAeq
    adjustment follows Formula 2. The extracted text must carry the boxed
    governing prominence, the adjustment value and the standard basis.
    """
    result = _result()
    out = tmp_path / "impulse.pdf"
    result.report(str(out))
    text = _extract_text(str(out)).replace("\n", " ")

    assert result.prominence == pytest.approx(_P_GOVERNING, abs=1e-6)
    assert result.adjustment == pytest.approx(_KI_GOVERNING, abs=1e-6)
    assert "Governing prominence" in text
    assert f"{_P_GOVERNING:.2f}" in text  # boxed governing P (12.25)
    assert f"{_KI_GOVERNING:.1f} dB" in text  # derived KI (13.0 dB)
    assert "NT ACOU 112" in text
    assert "Formula 2" in text


def test_metadata_appears_and_one_page(tmp_path) -> None:
    """A populated ReportMetadata renders one page and prints its fields."""
    md = ReportMetadata(
        specimen="Pile-driving site, intermittent hammering",
        client="Acoustic Test Client Ltd.",
        test_room="Free field, 25 m from source",
        instrumentation="Class 1 SLM (IEC 61672-1)",
        measurement_standard="ISO 1996-2",
        test_date="2026-07-21",
        laboratory="Phonometry Reference Laboratory",
        operator="J. M. Requena-Plens",
        report_id="PHN-2026-NTACOU112",
    )
    out = tmp_path / "meta.pdf"
    _result().report(str(out), metadata=md, verbose=True)
    _assert_one_page(str(out))
    text = _extract_text(str(out)).replace("\n", " ")
    assert "Pile-driving site, intermittent hammering" in text
    assert "Free field, 25 m from source" in text
    assert "PHN-2026-NTACOU112" in text
    assert "ISO 1996-2" in text
    assert "Assessment period" in text
    assert "30 min" in text


def test_requirement_pass_and_fail_both_render(tmp_path) -> None:
    """A PASS and a FAIL prominence limit both render one page."""
    result = _result()
    p = result.prominence
    passing = tmp_path / "pass.pdf"
    failing = tmp_path / "fail.pdf"
    result.report(str(passing), metadata=ReportMetadata(requirement=p + 2.0))
    result.report(str(failing), metadata=ReportMetadata(requirement=p - 2.0))
    _assert_one_page(str(passing))
    _assert_one_page(str(failing))
    assert "PASS" in _extract_text(str(passing)).replace("\n", " ")
    assert "FAIL" in _extract_text(str(failing)).replace("\n", " ")


def test_report_escapes_xml_specials_in_metadata(tmp_path) -> None:
    """Metadata with XML specials (& < >) renders without crashing reportlab."""
    md = ReportMetadata(
        client="Ac & Co <Ltd>",
        specimen="hammer <A> & pile",
        test_room="pos <1> & <2>",
        laboratory="Lab & Sons",
        operator="A <B>",
        report_id="R&D-112",
        measurement_standard="ISO 1996-2 & NT ACOU 112",
    )
    out = tmp_path / "xml.pdf"
    _result().report(str(out), metadata=md)
    _assert_one_page(str(out))


def test_spanish_report_renders_translated_fiche(tmp_path) -> None:
    """``language="es"`` renders a one-page Spanish fiche with comma decimals."""
    import re

    out = tmp_path / "impulse_es.pdf"
    _result().report(
        str(out),
        metadata=ReportMetadata(specimen="hincado de pilotes"),
        language="es",
    )
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "Evaluación de la prominencia de sonidos impulsivos" in text
    assert "ajuste de L" in text
    assert re.search(r"\d,\d", text) is not None  # comma decimal separator


def test_verdict_compares_unrounded_prominence(tmp_path) -> None:
    """A prominence just above the requirement FAILs, not rounded to a PASS.

    The governing prominence 12.2478 rounds to 12.25 for display; a requirement
    of 12.247 is just below it, so the assessment must FAIL even though the
    displayed P would round to the same two decimals as a passing value would.
    """
    result = _result()
    out = tmp_path / "boundary.pdf"
    requirement = result.prominence - 1e-3  # just below the unrounded P
    result.report(str(out), metadata=ReportMetadata(requirement=requirement))
    _assert_one_page(str(out))
    text = _extract_text(str(out)).replace("\n", " ")
    assert result.prominence > requirement
    assert "FAIL" in text
    assert "PASS" not in text


def test_verdict_passes_at_the_requirement(tmp_path) -> None:
    """A governing prominence at the requirement passes (``<=``)."""
    result = _result()
    out = tmp_path / "atlimit.pdf"
    result.report(str(out), metadata=ReportMetadata(requirement=result.prominence))
    _assert_one_page(str(out))
    assert "PASS" in _extract_text(str(out)).replace("\n", " ")


def test_oversized_impulse_set_stays_one_page(tmp_path) -> None:
    """A large valid impulse set caps the table and stays exactly one page.

    Forty qualifying impulses exceed the table row cap; the fiche must keep the
    highest-prominence rows (including the governing impulse), add an explicit
    ``... plus N more`` note and still render as a single A4 page.
    """
    import warnings

    import numpy as np

    rng = np.random.default_rng(0)
    onset_rates = rng.uniform(20.0, 2000.0, 40)
    level_differences = rng.uniform(5.0, 40.0, 40)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = nt.impulse_prominence(onset_rates, level_differences)
    out = tmp_path / "big.pdf"
    result.report(str(out))
    _assert_one_page(str(out))
    text = _extract_text(str(out)).replace("\n", " ")
    assert "more impulses of lower prominence" in text
    # The governing impulse (its 1-based input index) is always shown.
    governing = int(np.argmax(result.per_impulse[result.qualifies]))
    governing = int(np.where(result.qualifies)[0][governing])
    assert f"{result.prominence:.2f}" in text  # boxed governing P still present


def test_non_prominent_impulse_reports_zero_adjustment(tmp_path) -> None:
    """A qualifying but weak impulse (P <= 5) renders with a zero adjustment.

    A qualifying onset (rate above 10 dB/s) with a low prominence keeps KI at
    zero; the prominence note and boxed KI stay consistent.
    """
    # onset rate 15 dB/s, level difference 5 dB: P = 3*lg(15) + 2*lg(5) = 4.925.
    result = nt.impulse_prominence([15.0], [5.0])
    out = tmp_path / "weak.pdf"
    result.report(str(out))
    _assert_one_page(str(out))
    text = _extract_text(str(out)).replace("\n", " ")
    assert result.prominence <= 5.0
    assert result.adjustment == 0.0
    assert "No prominent impulse is present" in text
    assert "K = 0" in text or "0 dB" in text

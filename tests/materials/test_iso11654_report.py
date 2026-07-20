#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the ISO 11654 absorption-rating report (``.report()`` -> PDF).

The report is a rendering feature, so these tests assert only structural
facts: a valid single-page PDF is written for a weighted absorption rating,
the two normative Annex A worked examples are the ones the fiche renders,
unknown engines are rejected, XML specials in metadata do not break reportlab,
and the requirement verdict renders. Pixel or layout content is never inspected.
"""

from __future__ import annotations

import pytest

pytest.importorskip("reportlab")

from phonometry import ReportMetadata  # noqa: E402  (import after importorskip)
from phonometry.materials import weighted_absorption  # noqa: E402

from reference_data import (  # noqa: E402
    ISO11654_ANNEX_A1_ALPHA_P as _A1_ALPHA_P,
    ISO11654_ANNEX_A1_CLASS as _A1_CLASS,
    ISO11654_ANNEX_A1_INDICATOR as _A1_INDICATOR,
    ISO11654_ANNEX_A1_ALPHA_W as _A1_ALPHA_W,
    ISO11654_ANNEX_A2_ALPHA_P as _A2_ALPHA_P,
    ISO11654_ANNEX_A2_ALPHA_W as _A2_ALPHA_W,
    ISO11654_ANNEX_A2_INDICATOR as _A2_INDICATOR,
)

_PDF_MAGIC = b"%PDF"


def _assert_pdf(path: str) -> None:
    """A written report is a non-empty file beginning with ``%PDF``."""
    import os

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0


def _assert_one_page(path: str) -> None:
    """The fiche is a single-page PDF beginning with ``%PDF``."""
    _assert_pdf(path)
    from pypdf import PdfReader

    assert len(PdfReader(path).pages) == 1


def test_absorption_report_writes_pdf(tmp_path) -> None:
    """A weighted absorption rating renders a PDF fiche."""
    result = weighted_absorption(_A1_ALPHA_P)
    out = tmp_path / "absorption.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_pdf(str(out))


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    result = weighted_absorption(_A1_ALPHA_P)
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        result.report(out, engine="weasyprint")


def test_fiche_reproduces_iso11654_annex_a1(tmp_path) -> None:
    """The fiche renders the ISO 11654 Annex A.1 example: alpha_w = 0.60, class C."""
    result = weighted_absorption(_A1_ALPHA_P)
    assert result.alpha_w == pytest.approx(_A1_ALPHA_W)
    assert result.absorption_class == _A1_CLASS
    assert result.shape_indicator == _A1_INDICATOR
    _assert_one_page(str(result.report(str(tmp_path / "a1.pdf"))))


def test_fiche_reproduces_iso11654_annex_a2(tmp_path) -> None:
    """The fiche renders the Annex A.2 example: alpha_w = 0.60(M) shape indicator."""
    result = weighted_absorption(_A2_ALPHA_P)
    assert result.alpha_w == pytest.approx(_A2_ALPHA_W)
    assert result.shape_indicator == _A2_INDICATOR
    _assert_one_page(str(result.report(str(tmp_path / "a2.pdf"))))


def test_verbose_renders_evaluation_table(tmp_path) -> None:
    """``verbose=True`` renders the ISO 11654 evaluation-column one-pager."""
    result = weighted_absorption(_A2_ALPHA_P)
    out = tmp_path / "verbose.pdf"
    result.report(str(out), verbose=True)
    _assert_one_page(str(out))


def _full_metadata(**overrides) -> ReportMetadata:
    base = dict(
        specimen="50 mm porous absorber over a 100 mm air gap",
        client="Acoustic Test Client Ltd.",
        manufacturer="Acoustics Works Inc.",
        area=10.8,
        mounting="Type A (against a rigid wall)",
        test_room="Reverberation room R1",
        measurement_standard="ISO 354",
        test_date="2026-07-20",
        temperature=21.4,
        relative_humidity=54.0,
        pressure=101.0,
        laboratory="Phonometry Reference Laboratory",
        operator="J. M. Requena-Plens",
        report_id="PHN-2026-11654",
    )
    base.update(overrides)
    return ReportMetadata(**base)


def test_full_metadata_renders_one_page(tmp_path) -> None:
    """A full ReportMetadata renders a one-page accredited absorption fiche."""
    result = weighted_absorption(_A2_ALPHA_P)
    out = tmp_path / "meta.pdf"
    result.report(str(out), metadata=_full_metadata())
    _assert_one_page(str(out))


def test_requirement_pass_and_fail_both_render(tmp_path) -> None:
    """A PASS and a FAIL alpha_w requirement both render a one-page fiche."""
    result = weighted_absorption(_A1_ALPHA_P)  # alpha_w = 0.60
    passing = tmp_path / "pass.pdf"
    failing = tmp_path / "fail.pdf"
    result.report(str(passing), metadata=_full_metadata(requirement=0.55))
    result.report(str(failing), metadata=_full_metadata(requirement=0.80))
    _assert_one_page(str(passing))
    _assert_one_page(str(failing))


def test_report_escapes_xml_specials_in_metadata(tmp_path) -> None:
    """Metadata with XML specials (& < >) renders without crashing reportlab."""
    result = weighted_absorption(_A1_ALPHA_P)
    md = ReportMetadata(
        client="Ac & Co <Ltd>",
        specimen="absorber <A> & baffle",
        laboratory="Lab & Sons",
        operator="A <B>",
        report_id="R&D-011",
        measurement_standard="ISO 354 & Annex",
    )
    out = tmp_path / "xml.pdf"
    result.report(str(out), metadata=md)
    _assert_one_page(str(out))

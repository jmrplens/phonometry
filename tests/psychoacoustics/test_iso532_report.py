#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the ISO 532-1 Zwicker loudness report (``.report()`` -> PDF).

The report is a rendering feature, so these tests assert only structural facts:
a valid single-page PDF is written for a stationary loudness result, unknown
engines are rejected, XML specials in metadata do not break reportlab, and the
maximum-loudness verdict renders both ways. The loudness algorithm itself is
validated against the ISO 532-1 Annex B data elsewhere
(tests/psychoacoustics/test_loudness_zwicker.py); here a fixed synthetic
one-third-octave spectrum keeps the fiche test self-contained.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("reportlab")

from phonometry import ReportMetadata, loudness_zwicker_from_spectrum  # noqa: E402

# A shaped 28-band one-third-octave spectrum (25 Hz..12.5 kHz), descending.
_LEVELS = np.array(
    [55, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43,
     42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29],
    dtype=float,
)

_PDF_MAGIC = b"%PDF"


def _result():
    return loudness_zwicker_from_spectrum(_LEVELS, field="free")


def _assert_pdf(path: str) -> None:
    import os

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0


def _assert_one_page(path: str) -> None:
    _assert_pdf(path)
    from pypdf import PdfReader

    assert len(PdfReader(path).pages) == 1


def test_loudness_report_writes_pdf(tmp_path) -> None:
    """A stationary Zwicker loudness result renders a one-page PDF fiche."""
    result = _result()
    assert result.loudness > 0.0 and np.isfinite(result.loudness)
    assert result.n5 is None and result.n10 is None  # stationary
    out = tmp_path / "loudness.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_one_page(str(out))


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    result = _result()
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        result.report(out, engine="weasyprint")


def test_full_metadata_renders_one_page(tmp_path) -> None:
    """A populated ReportMetadata renders a one-page loudness fiche."""
    md = ReportMetadata(
        specimen="Household appliance, steady operating noise",
        client="Acoustic Test Client Ltd.",
        manufacturer="Appliance Works Inc.",
        test_room="Hemi-anechoic room H1",
        measurement_standard="ISO 532-1 method 1",
        test_date="2026-07-20",
        laboratory="Phonometry Reference Laboratory",
        operator="J. M. Requena-Plens",
        report_id="PHN-2026-0532",
    )
    out = tmp_path / "meta.pdf"
    _result().report(str(out), metadata=md)
    _assert_one_page(str(out))


def test_requirement_pass_and_fail_both_render(tmp_path) -> None:
    """A PASS and a FAIL maximum-loudness requirement both render one page."""
    result = _result()
    n = result.loudness
    passing = tmp_path / "pass.pdf"
    failing = tmp_path / "fail.pdf"
    result.report(str(passing), metadata=ReportMetadata(requirement=n + 5.0))
    result.report(str(failing), metadata=ReportMetadata(requirement=max(n - 2.0, 0.1)))
    _assert_one_page(str(passing))
    _assert_one_page(str(failing))


def test_report_escapes_xml_specials_in_metadata(tmp_path) -> None:
    """Metadata with XML specials (& < >) renders without crashing reportlab."""
    md = ReportMetadata(
        client="Ac & Co <Ltd>",
        specimen="fan <A> & motor",
        laboratory="Lab & Sons",
        operator="A <B>",
        report_id="R&D-532",
        measurement_standard="ISO 532-1 & method 1",
    )
    out = tmp_path / "xml.pdf"
    _result().report(str(out), metadata=md)
    _assert_one_page(str(out))


def _extract_text(path: str) -> str:
    """The concatenated text of every page (for language assertions)."""
    from pypdf import PdfReader

    return "\n".join(page.extract_text() for page in PdfReader(path).pages)


def test_spanish_report_renders_translated_fiche(tmp_path) -> None:
    """``language="es"`` renders a one-page Spanish fiche with comma decimals."""
    import re

    result = _result()
    out = tmp_path / "loudness_es.pdf"
    result.report(
        str(out),
        metadata=ReportMetadata(specimen="ruido de electrodoméstico"),
        language="es",
    )
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "Índice de sonoridad" in text
    assert "Sonoridad total" in text
    assert re.search(r"\d,\d", text) is not None  # comma decimal separator


def test_unknown_language_rejected(tmp_path) -> None:
    """An unknown fiche language raises ``ValueError``."""
    result = _result()
    with pytest.raises(ValueError, match="language"):
        result.report(str(tmp_path / "bad.pdf"), language="xx")

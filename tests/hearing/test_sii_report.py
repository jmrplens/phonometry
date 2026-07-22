#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for the ANSI S3.5-1997 speech-intelligibility-index ``.report()`` fiche.

The rendered index is checked against oracles independent of the renderer: the
standard normal-effort speech spectrum in quiet with normal hearing rates to
SII = 0.996 (ANSI S3.5-1997 clause 6), and the R CRAN "SII" package worked
Example C.2 (an independent implementation) rates to SII = 0.851. Both are pure
arithmetic (no filtering), so the boxed values are stable across platforms. The
Table 3 band-importance value, the verdict direction (a higher SII passes), the
EN/ES parity and the rendering contract complete the checks. Values are read
back from the PDF via pypdf text extraction.
"""

from __future__ import annotations

import os

import numpy as np
import pytest

from phonometry import ReportMetadata
from phonometry.hearing import speech_intelligibility_index

_PDF_MAGIC = b"%PDF"


def _assert_one_page(path: str) -> None:
    from pypdf import PdfReader

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0
    assert len(PdfReader(path).pages) == 1


def _extract_text(path: str) -> str:
    """Whitespace-normalized page text (PDF line wraps fold to single spaces)."""
    from pypdf import PdfReader

    raw = "\n".join(page.extract_text() for page in PdfReader(path).pages)
    return " ".join(raw.split())


def _example_c2():
    """R CRAN "SII" Example C.2: SII = 0.851 (independent oracle)."""
    return speech_intelligibility_index(
        np.full(18, 54.0),
        np.array([40.0, 30.0, 20.0] + [0.0] * 15),
        threshold=np.zeros(18),
    )


# --- exact oracle --------------------------------------------------------------


def test_example_c2_renders_index_and_band_importance(tmp_path) -> None:
    """The Example C.2 fiche prints SII = 0.851 and a Table 3 Ii value."""
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    res = _example_c2()
    assert res.sii == pytest.approx(0.851375, abs=1e-5)
    out = tmp_path / "sii.pdf"
    returned = res.report(str(out))
    assert returned == str(out)
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "SII = 0.851" in text
    # Band-importance function Ii at 2000 Hz (Table 3, four decimals).
    assert "0.0898" in text


def test_standard_speech_in_quiet_renders(tmp_path) -> None:
    """The standard normal spectrum in quiet rates to SII = 0.996."""
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    res = speech_intelligibility_index("normal")
    assert res.sii == pytest.approx(0.995825, abs=1e-5)
    out = tmp_path / "quiet.pdf"
    res.report(str(out))
    _assert_one_page(str(out))
    assert "SII = 0.996" in _extract_text(str(out))


# --- verbose adds the disturbance column --------------------------------------


def test_verbose_adds_disturbance_column(tmp_path) -> None:
    """verbose=True adds the equivalent disturbance spectrum level Di column."""
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    res = _example_c2()
    out = tmp_path / "verbose.pdf"
    res.report(str(out), verbose=True)
    _assert_one_page(str(out))
    flat = "".join(_extract_text(str(out)).split())
    assert "Di[dB]" in flat


# --- verdict direction (higher is better) -------------------------------------


def test_verdict_passes_at_or_above_requirement(tmp_path) -> None:
    """SII = 0.851 passes a 0.75 minimum and fails a 0.90 minimum."""
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    res = _example_c2()
    out_pass = tmp_path / "pass.pdf"
    res.report(str(out_pass), metadata=ReportMetadata(requirement=0.75))
    assert "PASS" in _extract_text(str(out_pass))
    out_fail = tmp_path / "fail.pdf"
    res.report(str(out_fail), metadata=ReportMetadata(requirement=0.90))
    assert "FAIL" in _extract_text(str(out_fail))


# --- metadata ------------------------------------------------------------------


def test_metadata_header_renders(tmp_path) -> None:
    """Supplied metadata renders the header grid; no requirement, no verdict."""
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    res = _example_c2()
    out = tmp_path / "meta.pdf"
    res.report(
        str(out),
        metadata=ReportMetadata(
            client="Example works",
            specimen="Speech in office noise",
            laboratory="Reference lab",
            report_id="SII-1",
        ),
    )
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "Example works" in text
    assert "Speech in office noise" in text
    assert "Result vs requirement" not in text


# --- Spanish fiche -------------------------------------------------------------


def test_spanish_report_renders_translated_fiche(tmp_path) -> None:
    """language="es" renders the SII vocabulary and comma decimals."""
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    res = _example_c2()
    out = tmp_path / "sii_es.pdf"
    res.report(str(out), metadata=ReportMetadata(requirement=0.75), language="es")
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "Índice de inteligibilidad del habla" in text
    assert "SII = 0,851" in text
    assert "CUMPLE" in text


# --- rendering contract --------------------------------------------------------


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ValueError."""
    res = _example_c2()
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        res.report(out, engine="weasyprint")


def test_unknown_language_rejected(tmp_path) -> None:
    """An unknown fiche language raises ValueError."""
    res = _example_c2()
    out = str(tmp_path / "bad.pdf")
    with pytest.raises(ValueError, match="language"):
        res.report(out, language="xx")

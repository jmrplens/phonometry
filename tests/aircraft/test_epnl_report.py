#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the ICAO Annex 16 EPNL report (``.report()`` -> PDF).

The report is a rendering feature, so these tests assert only structural facts:
a valid single-page PDF is written for a computed flyover, unknown engines are
rejected, a passing and a failing certification limit both render, and a
no-metadata prediction fiche renders. The EPNL algorithm itself is validated
against the ICAO Doc 9501 ETM worked examples elsewhere
(tests/aircraft/test_aircraft_noise.py); here a small self-contained synthetic
flyover keeps the fiche test independent.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

pytest.importorskip("reportlab")

from phonometry import ReportMetadata, effective_perceived_noise_level  # noqa: E402

_PDF_MAGIC = b"%PDF"


def _flyover():
    """A deterministic synthetic flyover EPNLResult (Gaussian temporal peak)."""
    k, dt = 24, 0.5
    idx = np.arange(k)
    from phonometry.aircraft import NOY_BANDS

    shape = 15.0 * np.exp(-((np.log10(NOY_BANDS) - np.log10(400.0)) ** 2) / 0.5)
    gain = 24.0 * np.exp(-((idx - 12.0) ** 2) / (2 * 3.5**2)) - 3.0
    spectra = (46.0 + shape)[None, :] + gain[:, None]
    spectra[:, 17] += 10.0 * np.exp(-((idx - 12.0) ** 2) / (2 * 4.0**2))
    return effective_perceived_noise_level(spectra, dt)


def _assert_one_page(path: str) -> None:
    import os

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0
    from pypdf import PdfReader

    assert len(PdfReader(path).pages) == 1


def test_report_writes_one_page_pdf(tmp_path) -> None:
    """A computed flyover renders a one-page certification fiche."""
    result = _flyover()
    assert np.isfinite(result.epnl)
    out = tmp_path / "epnl.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_one_page(str(out))


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    result = _flyover()  # constructed outside pytest.raises (Sonar S5778)
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        result.report(out, engine="weasyprint")


def test_passing_requirement_renders(tmp_path) -> None:
    """A certification limit at or above the EPNL renders a passing fiche."""
    result = _flyover()
    limit = float(result.epnl) + 3.0
    out = tmp_path / "pass.pdf"
    result.report(str(out), metadata=ReportMetadata(requirement=limit))
    _assert_one_page(str(out))


def test_failing_requirement_renders(tmp_path) -> None:
    """A certification limit below the EPNL renders a failing fiche."""
    result = _flyover()
    limit = float(result.epnl) - 3.0
    out = tmp_path / "fail.pdf"
    result.report(str(out), metadata=ReportMetadata(requirement=limit))
    _assert_one_page(str(out))


def test_full_metadata_renders_one_page(tmp_path) -> None:
    """A populated ReportMetadata renders a one-page fiche."""
    md = ReportMetadata(
        specimen="Example twin-turbofan transport",
        manufacturer="Example Aircraft Company",
        client="Example Aircraft Company",
        test_room="Flyover reference point",
        measurement_standard="ICAO Annex 16 Vol I Amendment 14 Chapter 4",
        test_date="2026-07-20",
        laboratory="Phonometry Reference Laboratory",
        operator="J. M. Requena-Plens",
        report_id="PHN-2026-EPNL",
        requirement=101.0,
    )
    out = tmp_path / "meta.pdf"
    _flyover().report(str(out), metadata=md)
    _assert_one_page(str(out))


def test_no_metadata_prediction_fiche(tmp_path) -> None:
    """With ``metadata=None`` a prediction fiche renders (no verdict row)."""
    out = tmp_path / "prediction.pdf"
    _flyover().report(str(out))
    _assert_one_page(str(out))

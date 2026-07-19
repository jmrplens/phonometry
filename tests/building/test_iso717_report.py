#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the ISO 717 Annex C rating report (``.report()`` -> PDF).

The report is a rendering feature, so these tests assert only structural
facts: a non-empty file that starts with the ``%PDF`` magic bytes is written
for both an airborne (ISO 717-1) and an impact (ISO 717-2) rating, unknown
engines and results lacking the per-band data are rejected, and the
convenience wrapper on the panel prediction result also renders. Pixel or
layout content is never inspected.
"""

from __future__ import annotations

import pytest

pytest.importorskip("reportlab")

from phonometry import (  # noqa: E402  (import after importorskip)
    WeightedRatingResult,
    single_panel_transmission_loss,
    weighted_impact_rating,
    weighted_rating,
)
import numpy as np  # noqa: E402

from reference_data import (  # noqa: E402
    ISO717_1_ANNEX_C_R as _AIRBORNE_R,
    ISO717_2_ANNEX_C1_EXPECTED as _IMPACT_EXPECTED,
    ISO717_2_ANNEX_C1_LN as _IMPACT_LN,
)

_PDF_MAGIC = b"%PDF"


def _assert_pdf(path: str) -> None:
    """A written report is a non-empty file beginning with ``%PDF``."""
    with open(path, "rb") as handle:
        head = handle.read(4)
    import os

    assert head == _PDF_MAGIC
    assert os.path.getsize(path) > 0


def test_airborne_report_writes_pdf(tmp_path) -> None:
    """An ISO 717-1 airborne rating renders a PDF fiche."""
    result = weighted_rating(_AIRBORNE_R)
    out = tmp_path / "airborne.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_pdf(str(out))


def test_impact_report_writes_pdf(tmp_path) -> None:
    """An ISO 717-2 impact rating renders a PDF fiche."""
    result = weighted_impact_rating(_IMPACT_LN)
    assert result.quantity == "impact"
    out = tmp_path / "impact.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_pdf(str(out))


def test_panel_result_report_convenience(tmp_path) -> None:
    """``SoundReductionResult.report()`` rates ``R(f)`` and writes its fiche."""
    freqs = [
        100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
        1000, 1250, 1600, 2000, 2500, 3150,
    ]
    res = single_panel_transmission_loss(
        freqs, 15.0, critical_frequency=2000.0, loss_factor=0.02
    )
    out = tmp_path / "panel.pdf"
    res.report(str(out))
    _assert_pdf(str(out))


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    result = weighted_rating(_AIRBORNE_R)
    with pytest.raises(ValueError, match="engine"):
        result.report(str(tmp_path / "x.pdf"), engine="weasyprint")


def test_missing_band_data_rejected(tmp_path) -> None:
    """A rating built without the per-band curves cannot be reported."""
    bare = WeightedRatingResult(rating=52, c=-1, ctr=-4, unfavourable_sum=30.0)
    assert bare.band_centers is None
    with pytest.raises(ValueError, match="per-band data"):
        bare.report(str(tmp_path / "bare.pdf"))


def test_airborne_fiche_reproduces_iso717_1_annex_c1(tmp_path) -> None:
    """The airborne fiche reproduces the ISO 717-1:2020 Annex C Table C.1 example.

    The values printed in the standard's worked example are exactly the ones the
    fiche shows: Rw(C;Ctr) = 30(-2;-3) dB, unfavourable-deviation sum 31,8 dB, the
    reference curve shifted by -22 dB, and the per-band unfavourable deviations.
    """
    result = weighted_rating(_AIRBORNE_R)
    assert (result.rating, result.c, result.ctr) == (30, -2, -3)
    assert result.unfavourable_sum == pytest.approx(31.8, abs=0.05)
    # Reference values shifted by -22 dB (Table C.1, column 3).
    shifted = np.array([11, 14, 17, 20, 23, 26, 29, 30,
                        31, 32, 33, 34, 34, 34, 34, 34], float)
    assert np.allclose(result.shifted_reference, shifted)
    # Unfavourable deviations (Table C.1, column 4; "-" printed as 0).
    deviations = np.maximum(result.shifted_reference - result.measured, 0.0)
    expected = np.array([0, 0, 0, 0, 0.6, 3.3, 4.2, 3.4,
                        3.0, 1.5, 1.2, 1.5, 0.6, 1.0, 3.0, 8.5], float)
    assert np.allclose(deviations, expected, atol=0.05)
    _assert_pdf(str(result.report(str(tmp_path / "airborne_c1.pdf"))))


def test_impact_fiche_reproduces_iso717_2_annex_c1(tmp_path) -> None:
    """The impact fiche reproduces the ISO 717-2 Annex C Table C.1 example.

    Ln,w = 79 dB, CI = -11 dB, unfavourable-deviation sum 28,0 dB (see the note
    on the 2020 reprint's CI in reference_data).
    """
    result = weighted_impact_rating(_IMPACT_LN)
    assert result.rating == _IMPACT_EXPECTED["ln_w"]
    assert result.ci == _IMPACT_EXPECTED["ci"]
    assert result.unfavourable_sum == pytest.approx(
        _IMPACT_EXPECTED["unfavourable_sum"], abs=0.05
    )
    _assert_pdf(str(result.report(str(tmp_path / "impact_c1.pdf"))))

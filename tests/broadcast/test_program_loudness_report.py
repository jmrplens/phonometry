#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the EBU R 128 programme-loudness report (``.report()`` -> PDF).

The report is a rendering feature, so these tests assert only structural facts:
a valid single-page PDF is written for a measured programme, unknown engines
are rejected, a compliant and a non-compliant programme both render, and the
informational rows (LRA, momentary/short-term maxima) never change the verdict.
The loudness algorithm itself is validated against the EBU Tech 3341/3342 test
signals elsewhere (tests/broadcast/test_program_loudness.py); here a small
self-contained synthetic signal keeps the fiche test independent.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

pytest.importorskip("reportlab")

from phonometry import ReportMetadata  # noqa: E402
from phonometry.broadcast import program_loudness  # noqa: E402
from phonometry._report.broadcast import _verdict  # noqa: E402

FS = 48000
_PDF_MAGIC = b"%PDF"


def _sine(level_dbfs: float, duration: float, freq: float = 1000.0) -> np.ndarray:
    """A 1 kHz sine with per-sample peak level ``level_dbfs`` (dB re full scale)."""
    t = np.arange(int(round(duration * FS))) / FS
    return 10.0 ** (level_dbfs / 20.0) * np.sin(2.0 * np.pi * freq * t)


def _stereo(x: np.ndarray) -> np.ndarray:
    """The signal applied in phase to both channels."""
    return np.vstack([x, x])


def _steps(segments: tuple[tuple[float, float], ...]) -> np.ndarray:
    """Concatenated stereo 1 kHz tone steps (level dBFS, duration s)."""
    return _stereo(np.concatenate([_sine(lvl, dur) for lvl, dur in segments]))


def _case1_result():
    """EBU Tech 3342 Case 1: -20/-30 dBFS steps -> I ~ -23 LUFS, LRA ~ 10 LU."""
    return program_loudness(_steps(((-20.0, 20.0), (-30.0, 20.0))), FS)


def _assert_pdf(path: str) -> None:
    import os

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0


def _assert_one_page(path: str) -> None:
    _assert_pdf(path)
    from pypdf import PdfReader

    assert len(PdfReader(path).pages) == 1


def test_report_writes_one_page_pdf(tmp_path) -> None:
    """A measured programme renders a one-page compliance fiche."""
    result = _case1_result()
    assert np.isfinite(result.integrated)
    out = tmp_path / "loudness.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_one_page(str(out))


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    result = _case1_result()
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        result.report(out, engine="weasyprint")


def test_full_metadata_renders_one_page(tmp_path) -> None:
    """A populated ReportMetadata renders a one-page fiche."""
    md = ReportMetadata(
        specimen="Reference tone sequence",
        client="Broadcast Client Ltd.",
        manufacturer="Post-production House",
        test_room="Reference monitoring room R1",
        measurement_standard="EBU R 128",
        test_date="2026-07-20",
        laboratory="Phonometry Reference Laboratory",
        operator="J. M. Requena-Plens",
        report_id="PHN-2026-R128",
        requirement=-23.0,
    )
    out = tmp_path / "meta.pdf"
    _case1_result().report(str(out), metadata=md)
    _assert_one_page(str(out))


def test_compliant_programme_passes(tmp_path) -> None:
    """The Case 1 signal is compliant (I within -23 +/-0.5 LU, TP <= -1 dBTP)."""
    result = _case1_result()
    _text, passed = _verdict(result, -23.0)
    assert passed is True
    out = tmp_path / "pass.pdf"
    result.report(str(out), metadata=ReportMetadata(requirement=-23.0))
    _assert_one_page(str(out))


def test_non_compliant_true_peak_fails(tmp_path) -> None:
    """A 0 dBFS tone exceeds the -1 dBTP true-peak ceiling and fails."""
    result = program_loudness(_stereo(_sine(0.0, 10.0)), FS)
    assert result.true_peak > -1.0
    _text, passed = _verdict(result, -23.0)
    assert passed is False
    out = tmp_path / "fail.pdf"
    result.report(str(out), metadata=ReportMetadata(requirement=-23.0))
    _assert_one_page(str(out))


def test_informational_rows_do_not_change_verdict(tmp_path) -> None:
    """LRA and the momentary/short-term maxima never affect the PASS verdict."""
    result = _case1_result()
    _text, passed = _verdict(result, -23.0)
    assert passed is True
    # Force extreme informational values; the verdict must stay PASS because it
    # is driven only by the integrated loudness and the maximum true peak.
    tampered = dataclasses.replace(
        result, loudness_range=999.0, max_momentary=0.0, max_short_term=0.0
    )
    _text2, passed2 = _verdict(tampered, -23.0)
    assert passed2 is True
    out = tmp_path / "info.pdf"
    tampered.report(str(out), metadata=ReportMetadata(requirement=-23.0))
    _assert_one_page(str(out))

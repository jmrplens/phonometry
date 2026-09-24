#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the IEC 62585 free-field-correction fiche (``.report()`` -> PDF).

The fiche is a rendering feature, so these tests assert structural facts: a
verdict renders a valid single-page fiche in both languages, with and without
metadata and a range, the Spanish fiche carries no English template, unknown
engines are refused, and a failing verdict says so. The verdict itself is
validated in tests/metrology/test_free_field_corrections.py.
"""

from __future__ import annotations

import matplotlib as mpl
import numpy as np
import pytest

mpl.use("Agg")

pytest.importorskip("reportlab")
pytest.importorskip("svglib")

from typing import TYPE_CHECKING

from report_assertions import assert_one_page

from phonometry import ReportMetadata, metrology

if TYPE_CHECKING:
    from pathlib import Path

#: The exact one-third-octave frequencies from 63 Hz to 16 kHz: the longest
#: table a calibrator's corrections are reported over.
_THIRDS = metrology.exact_frequencies(63.0, 16000.0, fraction=3)


def _verdict(
    *, exceed: bool = False, with_range: bool = True
) -> metrology.CorrectionUncertaintyVerification:
    """Corrections on a calibrator, reported at 25 exact one-third octaves."""
    x = _THIRDS / 1000.0
    expanded = 0.12 + 0.02 * x**0.8
    if exceed:
        expanded[-2] = 0.55
    return metrology.verify_correction_uncertainty(
        _THIRDS,
        expanded,
        clause=12,
        correction_db=-0.1 * x**1.5,
        coverage_factor=np.full(_THIRDS.size, 2.04),
        correction_range_db=0.02 * x**0.8 if with_range else None,
    )


def _metadata() -> ReportMetadata:
    return ReportMetadata(
        specimen="Class 1 sound level meter with its multi-frequency calibrator",
        client="Example client",
        manufacturer="Example instruments",
        test_room="Free-field room (example)",
        measurement_standard="IEC 62585:2012",
        test_date="2026-09-24",
        laboratory="Phonometry reference example",
        operator="phonometry",
        report_id="EXAMPLE-62585",
    )


def _extract_text(path: str) -> str:
    """Whitespace-normalized page text (PDF line wraps fold to single spaces)."""
    from pypdf import PdfReader

    raw = "\n".join(page.extract_text() for page in PdfReader(path).pages)
    return " ".join(raw.split())


@pytest.mark.parametrize("language", ["en", "es"])
def test_fiche_renders_one_page(tmp_path: Path, language: str) -> None:
    verdict = _verdict()
    path = verdict.report(
        str(tmp_path / f"iec62585_{language}.pdf"),
        metadata=_metadata(),
        language=language,
    )
    assert_one_page(path)


def test_bare_fiche_without_metadata_or_range(tmp_path: Path) -> None:
    verdict = _verdict(with_range=False)
    path = verdict.report(str(tmp_path / "bare.pdf"))
    assert_one_page(path)
    text = _extract_text(path)
    assert "Range over the microphones not judged" in text


def test_english_fiche_states_the_clause_and_the_verdict(tmp_path: Path) -> None:
    verdict = _verdict(exceed=True)
    path = verdict.report(str(tmp_path / "fail.pdf"), metadata=_metadata())
    text = _extract_text(path)
    for english in (
        "Free-field corrections of a sound level meter",
        "clause 12: corrections for a sound calibrator",
        "Exceeds the maximum permitted values of clause 12 at 1 of 25 frequencies",
        "FAIL",
    ):
        assert english in text, english


def test_spanish_fiche_translates_every_fixed_string(tmp_path: Path) -> None:
    verdict = _verdict()
    path = verdict.report(
        str(tmp_path / "es_text.pdf"), metadata=_metadata(), language="es"
    )
    text = _extract_text(path)
    for spanish in (
        "Correcciones de campo libre de un sonómetro",
        "apartado 12: correcciones para un calibrador acústico",
        "Incertidumbres expandidas para un nivel de confianza del 95 %",
        "Dentro de los valores máximos permitidos del apartado 12",
        "Factor de cobertura k de",
        "Dictamen",
    ):
        assert spanish in text, spanish
    for english in (
        "Free-field corrections",
        "Expanded uncertainties at a level",
        "Within the maximum permitted",
        "Coverage factor",
        "Verdict",
    ):
        assert english not in text, english


def test_unknown_engine_is_refused(tmp_path: Path) -> None:
    verdict = _verdict()
    target = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        verdict.report(target, engine="weasyprint")

#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the EN/ISO 12354-1/-2 predicted-insulation reports (``.report()``).

The prediction fiches are pinned to the standards' own worked examples, run
through the tested prediction code: EN 12354-1 Annex H.3 (airborne, a
separating wall with four flanking elements, predicted ``R'w`` = 52 dB) and EN
12354-2 Annex E.3 (impact, a concrete floor with a floating floor, predicted
``L'n,w`` = 45 dB). The rendering assertions are structural (a one-page
``%PDF``) plus pypdf text-extraction checks of the boxed single number, the
model-term labels, the mandatory "prediction / not a measurement" wording and a
couple of the model values, like the sibling report tests.
"""

from __future__ import annotations

import pytest

import reference_data as ref

pytest.importorskip("reportlab")

from phonometry import (  # noqa: E402  (import after importorskip)
    ReportMetadata,
    equivalent_impact_level,
    flanking_element,
    impact_flanking_correction,
    predicted_airborne_insulation,
    predicted_impact_insulation,
)
from phonometry.building.building_prediction import (  # noqa: E402
    AirbornePredictionResult,
    ImpactPredictionResult,
)

_PDF_MAGIC = b"%PDF"


def _annex_h3_airborne() -> AirbornePredictionResult:
    """The EN 12354-1 Annex H.3 airborne prediction (R'w = 52 dB)."""
    ss = ref.EN12354_1_ANNEX_H3_SEPARATING_AREA
    r_direct = ref.EN12354_1_ANNEX_H3_R_DIRECT
    paths = []
    for label, rw, kff, kfd, lf in ref.EN12354_1_ANNEX_H3_ELEMENTS:
        ff, df, fd = flanking_element(
            label=label, r_flanking=rw, r_separating=r_direct,
            k_ff=kff, k_fd=kfd, k_df=kfd, separating_area=ss, coupling_length=lf,
        )
        paths += [ff, df, fd]
    return predicted_airborne_insulation(r_direct=r_direct, flanking_paths=paths)


def _annex_e3_impact() -> ImpactPredictionResult:
    """The EN 12354-2 Annex E.3 impact prediction (L'n,w = 45 dB)."""
    ln_w_eq = equivalent_impact_level(ref.EN12354_2_ANNEX_E3_MASS)
    k = impact_flanking_correction(
        ref.EN12354_2_ANNEX_E3_MASS, ref.EN12354_2_ANNEX_E3_FLANKING_MEAN_MASS
    )
    return predicted_impact_insulation(
        ln_w_eq=ln_w_eq, delta_l_w=ref.EN12354_2_ANNEX_E3_DELTA_LW, k_correction=k
    )


def _assert_one_page(path: str) -> None:
    """A written report is a non-empty single-page PDF."""
    import os

    from pypdf import PdfReader

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0
    assert len(PdfReader(path).pages) == 1


def _extract_text(path: str) -> str:
    """The concatenated, whitespace-normalised text of every page."""
    from pypdf import PdfReader

    return " ".join(
        "\n".join(page.extract_text() for page in PdfReader(path).pages).split()
    )


def test_airborne_prediction_rating_pinned_to_annex_h3(tmp_path) -> None:
    """The airborne fiche boxes the Annex H.3 predicted R'w = 52 dB."""
    out = tmp_path / "air.pdf"
    _annex_h3_airborne().report(str(out))
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert f"{ref.EN12354_1_ANNEX_H3_RPRIME_W} dB" in text  # boxed R'w = 52 dB
    assert "EN/ISO 12354-1:2000" in text
    assert "ISO 717-1" in text
    # Explicitly a prediction, not a measurement.
    assert "prediction" in text
    assert "not a measurement" in text
    # The direct path and a couple of flanking-path indices from the table.
    assert "Dd" in text
    assert "65.5" in text  # floor-Ff Rij,w
    assert "73" in text  # intwall-Ff Rij,w


def test_impact_prediction_rating_pinned_to_annex_e3(tmp_path) -> None:
    """The impact fiche boxes the Annex E.3 predicted L'n,w = 45 dB."""
    out = tmp_path / "imp.pdf"
    _annex_e3_impact().report(str(out))
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert f"{ref.EN12354_2_ANNEX_E3_LPRIME_N_W} dB" in text  # boxed L'n,w = 45
    assert "EN/ISO 12354-2:2000" in text
    assert "ISO 717-2" in text
    assert "prediction" in text
    assert "not a measurement" in text
    # Formula (21) terms: the bare-floor level and the covering improvement.
    assert "76.2" in text  # Ln,w,eq = 164 - 35 lg(322)
    assert "33" in text  # covering improvement DLw
    assert "Formula (21)" in text


def test_airborne_verbose_adds_energy_share(tmp_path) -> None:
    """``verbose=True`` annexes each path's share of the transmitted energy."""
    plain = tmp_path / "plain.pdf"
    _annex_h3_airborne().report(str(plain))
    assert "%" not in _extract_text(str(plain))

    verbose = tmp_path / "verbose.pdf"
    _annex_h3_airborne().report(str(verbose), verbose=True)
    text = _extract_text(str(verbose))
    assert "%" in text  # per-path energy share column
    assert "energy share" in text  # the verbose caption


def test_airborne_requirement_verdict(tmp_path) -> None:
    """Airborne insulation passes at or above the requirement."""
    result = _annex_h3_airborne()  # R'w = 52 dB
    passing = tmp_path / "pass.pdf"
    result.report(str(passing), metadata=ReportMetadata(requirement=50.0))
    assert "PASS" in _extract_text(str(passing))

    failing = tmp_path / "fail.pdf"
    result.report(str(failing), metadata=ReportMetadata(requirement=55.0))
    assert "FAIL" in _extract_text(str(failing))


def test_impact_requirement_verdict_lower_is_better(tmp_path) -> None:
    """Impact level passes at or below the requirement (lower is better)."""
    result = _annex_e3_impact()  # L'n,w = 45 dB
    passing = tmp_path / "pass.pdf"
    result.report(str(passing), metadata=ReportMetadata(requirement=53.0))
    assert "PASS" in _extract_text(str(passing))

    failing = tmp_path / "fail.pdf"
    result.report(str(failing), metadata=ReportMetadata(requirement=40.0))
    assert "FAIL" in _extract_text(str(failing))


def test_metadata_header_renders(tmp_path) -> None:
    """A populated metadata header prints on the fiche."""
    metadata = ReportMetadata(
        specimen="Separating wall Rs,w = 57 dB",
        client="Acoustic Consultants Ltd.",
        area=11.5,
        source_volume=53.0,
        receiving_volume=50.0,
        laboratory="Phonometry Reference Laboratory",
        report_id="PHN-2026-0200",
        notes="Flanking: floor/ceiling/facade/internal wall.",
    )
    out = tmp_path / "meta.pdf"
    _annex_h3_airborne().report(str(out), metadata=metadata)
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "Separating wall Rs,w = 57 dB" in text
    assert "Phonometry Reference Laboratory" in text


def test_lightweight_fiche_without_metadata(tmp_path) -> None:
    """A fiche with no metadata is still a valid one-page prediction report."""
    out = tmp_path / "bare.pdf"
    _annex_e3_impact().report(str(out))
    _assert_one_page(str(out))
    assert "prediction" in _extract_text(str(out))


def test_spanish_fiche_renders_translated(tmp_path) -> None:
    """``language="es"`` renders the Spanish fiche with comma decimals."""
    import re

    out = tmp_path / "es.pdf"
    _annex_h3_airborne().report(
        str(out),
        metadata=ReportMetadata(requirement=50.0, laboratory="Ejemplo"),
        verbose=True,
        language="es",
    )
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "CUMPLE" in text  # R'w = 52 dB >= 50 dB
    assert "previsto" in text  # "predicted"
    assert "no una medici" in text  # "not a measurement"
    assert re.search(r"\d+,\d", text)  # comma decimal separator


def test_impact_spanish_fiche_renders_translated(tmp_path) -> None:
    """The impact fiche also renders in Spanish."""
    out = tmp_path / "es_imp.pdf"
    _annex_e3_impact().report(str(out), language="es")
    _assert_one_page(str(out))
    text = _extract_text(str(out))
    assert "previsto" in text
    assert "rmula (21)" in text  # "fórmula (21)"


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    out = str(tmp_path / "x.pdf")
    result = _annex_h3_airborne()
    with pytest.raises(ValueError, match="engine"):
        result.report(out, engine="weasyprint")


def test_unknown_language_rejected(tmp_path) -> None:
    """An unsupported language raises ``ValueError`` (shared validation path)."""
    out = str(tmp_path / "x.pdf")
    result = _annex_e3_impact()
    with pytest.raises(ValueError, match="language"):
        result.report(out, language="fr")

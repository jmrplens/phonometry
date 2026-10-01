#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the ISO 3743-1 and ISO 3743-2 ``.report()`` fiches.

The printed values are checked against closed forms taken from the two
standards, computed here without the library: ISO 3743-1:2010 Eq. (10) to
(14), the energy means of the source, the reference sound source and the
background, the background correction of Eq. (13) on the means (6 dB, 15 dB
and the fixed 1,3 dB below 6 dB) and
``LW = LW(RSS) - L'p(RSS) + L'p(ST) + K1(RSS) - K1``; ISO 3743-2:2018
Formula (9), ``LW = Lp - 10 lg(Tnom/T0) + 10 lg(V/V0) - 13 dB`` on the energy
mean of Formula (8); and the octave A-weighting corrections of Annex B /
Annex F (Table B.1, Table F.1). The values are read back from the PDF by pypdf
text extraction; the upper-bound marker, the statements the standards require
a report to make and the rendering contract (one page, rejected engines and
languages) complete the checks.
"""

from __future__ import annotations

import dataclasses
import warnings
from typing import TYPE_CHECKING

import numpy as np
import pytest
from report_assertions import assert_one_page

from phonometry import ReportMetadata
from phonometry.emission import (
    SoundPowerWarning,
    sound_energy_hard_walled,
    sound_power_hard_walled,
    sound_power_special_room,
    sound_power_special_room_comparison,
)

if TYPE_CHECKING:
    from pathlib import Path

    from phonometry.emission import (
        HardWalledSoundPowerResult,
        SpecialRoomSoundPowerResult,
    )

#: Table B.1 of ISO 3743-1:2010 (the same as Table F.1 of ISO 3743-2:2018).
_CK = np.array([-16.1, -8.6, -3.2, 0.0, 1.2, 1.0, -1.1])
_FREQS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
_ST = np.array(
    [
        [84.1, 86.0, 88.2, 90.1, 87.4, 83.2, 78.1],
        [82.6, 85.1, 87.5, 89.6, 88.0, 83.9, 77.5],
        [83.3, 86.8, 88.9, 90.8, 86.9, 82.8, 78.6],
        [85.0, 85.6, 87.8, 89.2, 87.7, 84.4, 77.9],
    ]
)
_RSS = np.array(
    [
        [87.8, 83.9, 86.8, 87.9, 87.1, 85.2, 81.8],
        [87.1, 83.1, 86.1, 87.3, 86.6, 84.7, 81.2],
        [88.5, 84.4, 87.2, 88.4, 87.6, 85.8, 82.4],
        [87.7, 83.6, 86.5, 87.8, 87.0, 85.1, 81.6],
    ]
)
_LW_RSS = np.array([94.0, 89.9, 92.8, 94.1, 93.2, 91.3, 87.9])
_BACKGROUND = np.array(
    [
        [78.5, 71.0, 64.0, 58.0, 52.0, 45.0, 40.0],
        [79.5, 71.5, 64.5, 58.5, 52.5, 45.5, 40.5],
        [78.0, 70.5, 63.5, 57.5, 51.5, 44.5, 39.5],
        [79.0, 71.0, 64.0, 58.0, 52.0, 45.0, 40.0],
    ]
)
_VOLUME = 72.0
_TNOM = 0.77


def _extract_text(path: str) -> str:
    """Whitespace-normalized page text (PDF line wraps fold to single spaces)."""
    from pypdf import PdfReader

    raw = "\n".join(page.extract_text() for page in PdfReader(path).pages)
    return " ".join(raw.split())


def _energy_mean(levels: np.ndarray) -> np.ndarray:
    """Eq. (10) to (12): the energy mean over the rows."""
    return 10.0 * np.log10(np.mean(10.0 ** (0.1 * levels), axis=0))


def _k1(margin: np.ndarray) -> np.ndarray:
    """Eq. (13) with the rules of 8.1.3: nothing above 15 dB, and below 6 dB
    the fixed 1,3 dB the clause prints as "the value for 6 dB".
    """
    safe = np.maximum(margin, 6.0)
    k1 = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * safe))
    return np.where(margin > 15.0, 0.0, np.where(margin < 6.0, 1.3, k1))


def _oracle_hard_walled() -> tuple[np.ndarray, float]:
    """``LW`` per band (Eq. 14) and ``LWA`` (Eq. B.1), by hand."""
    st, rss, bg = _energy_mean(_ST), _energy_mean(_RSS), _energy_mean(_BACKGROUND)
    lw = _LW_RSS - rss + st + _k1(rss - bg) - _k1(st - bg)
    return lw, float(10.0 * np.log10(np.sum(10.0 ** (0.1 * (lw + _CK)))))


def _hard_walled(
    *,
    background_levels: np.ndarray | None = _BACKGROUND,
    sigma_omc_db: float | None = None,
) -> HardWalledSoundPowerResult:
    """The guide's blender, its 125 Hz band an upper bound."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SoundPowerWarning)
        return sound_power_hard_walled(
            _ST,
            _RSS,
            _LW_RSS,
            _FREQS,
            background_levels=background_levels,
            sigma_omc_db=sigma_omc_db,
        )


def _special_direct() -> SpecialRoomSoundPowerResult:
    """A direct determination at six positions, background far below."""
    return sound_power_special_room(
        _ST - 20.0,
        _FREQS,
        volume_m3=_VOLUME,
        nominal_reverberation_time_s=_TNOM,
        background_levels=np.full(7, 30.0),
        a_weighted_levels=np.array([75.2, 75.6, 75.9, 75.4]),
        a_weighted_background_levels=40.0,
        sigma_omc_db=0.5,
    )


def _render(result: object, tmp_path: Path, name: str, **kwargs: object) -> str:
    """Render to ``tmp_path`` and return the extracted, one-page text."""
    pytest.importorskip("reportlab")
    pytest.importorskip("svglib")
    pytest.importorskip("matplotlib")
    out = tmp_path / name
    assert result.report(str(out), **kwargs) == str(out)  # type: ignore[attr-defined]
    assert_one_page(str(out))
    return _extract_text(str(out))


# --- clean-room oracle --------------------------------------------------------


def test_hand_oracle_matches_library() -> None:
    """The library's Eq. 14 and Eq. B.1 equal the closed forms above."""
    lw, lwa = _oracle_hard_walled()
    res = _hard_walled()
    np.testing.assert_allclose(res.sound_power_level, lw, atol=1e-9)
    assert res.sound_power_level_a == pytest.approx(lwa, abs=1e-9)


def test_hard_walled_fiche_prints_the_oracle_values(tmp_path: Path) -> None:
    """The fiche prints LWA, the band levels, the method and the grade."""
    lw, lwa = _oracle_hard_walled()
    text = _render(_hard_walled(sigma_omc_db=1.0), tmp_path, "iso3743_1.pdf")
    assert f"{lwa:.1f}" in text
    assert "re 1 pW" in text
    assert f"{lw[3]:.1f}" in text
    assert f"{lw[4]:.1f}" in text
    assert "ISO 3743-1:2010" in text
    assert "engineering method, accuracy grade 2" in text
    assert "hard-walled test room" in text
    assert "Eq. 14" in text
    assert "Annex B" in text
    # 10.5 h): the expanded uncertainty with its coverage factor and probability.
    assert "coverage factor k = 2" in text
    assert "coverage probability of 95 %" in text


def test_hard_walled_upper_bound_is_marked_and_stated(tmp_path: Path) -> None:
    """8.1.3: the 125 Hz band carries the marker and the sentence names it."""
    lw, _ = _oracle_hard_walled()
    text = _render(_hard_walled(), tmp_path, "upper.pdf")
    assert f"{lw[0]:.1f} *" in text
    assert f"{lw[1]:.1f} *" not in text
    assert "Upper bound" in text
    assert "(4.5, 8.1.3)" in text


def test_hard_walled_without_background_says_so(tmp_path: Path) -> None:
    """No background measured: every band marked, none an upper bound."""
    text = _render(_hard_walled(background_levels=None), tmp_path, "nobg.pdf")
    assert "No background noise was measured" in text
    assert "Upper bound" not in text
    assert text.count("\N{DAGGER}") >= 8  # seven bands and the note
    assert "No expanded uncertainty is stated" in text


def test_hard_walled_short_reference_margin_is_no_upper_bound(
    tmp_path: Path,
) -> None:
    """8.1.3 makes an upper bound of the source's margin alone: a short
    margin of the reference sound source is named as failing 4.5, with the
    reason it is no bound, under its own marker.
    """
    bg_ref = _BACKGROUND.copy()
    bg_ref[:, 6] = _energy_mean(_RSS)[6] - 4.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SoundPowerWarning)
        res = sound_power_hard_walled(
            _ST,
            _RSS,
            _LW_RSS,
            _FREQS,
            background_levels=_BACKGROUND,
            background_levels_ref=bg_ref,
        )
    text = _render(res, tmp_path, "rss.pdf")
    assert f"{res.sound_power_level[0]:.1f} *" in text
    assert f"{res.sound_power_level[6]:.1f} \N{DAGGER}" in text
    assert "margin of the reference sound source is below 6 dB" in text
    assert "no upper bound (8.1.4)" in text


def test_hard_walled_one_sided_coverage_is_named(tmp_path: Path) -> None:
    """9.1: k = 1,6 is the one-sided 95 % factor, and the basis says so."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SoundPowerWarning)
        res = sound_power_hard_walled(
            _ST,
            _RSS,
            _LW_RSS,
            _FREQS,
            background_levels=_BACKGROUND,
            sigma_omc_db=1.0,
            coverage_factor=1.6,
        )
    text = _render(res, tmp_path, "k16.pdf")
    assert "coverage factor k = 1.6" in text
    assert "k = 1.6 gives a coverage probability of 95 % for a one-sided" in text
    assert "k = 2 gives" not in text


def test_hard_walled_other_coverage_factor_is_stated_alone(tmp_path: Path) -> None:
    res = _hard_walled(sigma_omc_db=1.0)
    text = _render(dataclasses.replace(res, coverage_factor=3.0), tmp_path, "k3.pdf")
    assert "the coverage factor is k = 3." in text
    assert "95 %" not in text


def test_hard_walled_verbose_adds_the_corrections(tmp_path: Path) -> None:
    """``verbose`` adds the mean background level and both K1 columns."""
    st, bg = _energy_mean(_ST), _energy_mean(_BACKGROUND)
    text = _render(_hard_walled(), tmp_path, "verbose.pdf", verbose=True)
    assert f"{bg[0]:.1f}" in text
    assert f"{_k1(st - bg)[0]:.1f}" in text
    assert "1.3" in text  # K1 at 125 Hz, the fixed value of 8.1.3


def test_hard_walled_verdict(tmp_path: Path) -> None:
    """A declared limit above LWA passes, one below it fails."""
    res = _hard_walled()
    text = _render(
        res, tmp_path, "pass.pdf", metadata=ReportMetadata(requirement=101.0)
    )
    assert "PASS" in text
    text = _render(res, tmp_path, "fail.pdf", metadata=ReportMetadata(requirement=99.0))
    assert "FAIL" in text


def test_hard_walled_energy_fiche(tmp_path: Path) -> None:
    """Eq. 20: the energy sheet boxes LJA re 1 pJ under its own title."""
    events = np.stack([_ST + 12.0 + d for d in (-0.4, 0.1, 0.3, -0.2, 0.2)])
    res = sound_energy_hard_walled(
        events,
        _RSS,
        _LW_RSS,
        _FREQS,
        background_levels=np.full((4, 7), 30.0),
        integration_time_s=2.0,
        sigma_omc_db=2.0,
    )
    text = _render(
        res, tmp_path, "energy.pdf", metadata=ReportMetadata(requirement=120.0)
    )
    assert "Sound energy determination" in text
    assert f"{res.sound_energy_level_a:.1f}" in text
    assert "re 1 pJ" in text
    assert "Eq. 20" in text
    assert "PASS" in text
    # The 9.5 EXAMPLE: sigma_R0 = 1,5 dB and sigma_omc = 2,0 dB give U = 5 dB.
    assert "U = 5.0 dB" in text


def test_special_room_direct_fiche(tmp_path: Path) -> None:
    """Formula 9 by hand; the boxed level is the directly measured LWA."""
    res = _special_direct()
    lp = _energy_mean(_ST - 20.0)
    lw = lp - 10.0 * np.log10(_TNOM) + 10.0 * np.log10(_VOLUME) - 13.0
    lpa = float(_energy_mean(np.array([[75.2], [75.6], [75.9], [75.4]]))[0])
    lwa_direct = lpa - 10.0 * np.log10(_TNOM) + 10.0 * np.log10(_VOLUME) - 13.0
    np.testing.assert_allclose(res.sound_power_level, lw, atol=1e-9)
    assert res.sound_power_level_a_direct == pytest.approx(lwa_direct, abs=1e-9)
    text = _render(
        res,
        tmp_path,
        "direct.pdf",
        metadata=ReportMetadata(requirement=lwa_direct + 1.0),
    )
    assert f"{lwa_direct:.1f} dB(A)" in text
    assert "From the octave bands (Annex F)" in text
    assert f"{res.sound_power_level_a:.1f}" in text
    # 12.5 d): the corrected band levels to the nearest one-half decibel.
    assert f"{round(2.0 * lw[2]) / 2.0:.1f}" in text
    assert "nearest one-half decibel (12.5 d)" in text
    assert "ISO 3743-2:2018" in text
    assert "direct method" in text
    assert "Formula 9" in text
    assert "PASS" in text
    assert " *" not in text  # every margin is far above 4 dB


def test_special_room_comparison_fiche(tmp_path: Path) -> None:
    """Formula 10, with no background and no sigma_omc stated as such."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SoundPowerWarning)
        res = sound_power_special_room_comparison(
            _ST, np.vstack([_RSS, _RSS[:2]]), _LW_RSS, _FREQS
        )
    text = _render(res, tmp_path, "comparison.pdf")
    assert "comparison method using a reference sound source" in text
    assert "Formula 10" in text
    assert "not shown to be fulfilled" in text
    assert "No expanded uncertainty is stated" in text
    assert f"{round(2.0 * res.sound_power_level[0]) / 2.0:.1f} *" in text
    assert "Upper bound" not in text  # 9.8 never calls a band one


def test_spanish_fiche_uses_the_decimal_comma(tmp_path: Path) -> None:
    """``language="es"`` translates the sheet and switches the separator."""
    _, lwa = _oracle_hard_walled()
    text = _render(_hard_walled(sigma_omc_db=1.0), tmp_path, "es.pdf", language="es")
    assert "Determinación de la potencia acústica" in text
    assert f"{lwa:.1f}".replace(".", ",") in text
    assert "sala de ensayo de paredes rígidas" in text
    assert "Cota superior" in text
    text = _render(_special_direct(), tmp_path, "es2.pdf", language="es")
    assert "sala de ensayo reverberante especial" in text
    assert "fórmula 9" in text


@pytest.mark.parametrize("make", [_hard_walled, _special_direct])
def test_rejects_an_unknown_engine_and_language(make: object, tmp_path: Path) -> None:
    """Only reportlab renders, and only the two languages exist."""
    res = make()  # type: ignore[operator]
    with pytest.raises(ValueError, match="engine"):
        res.report(str(tmp_path / "x.pdf"), engine="weasyprint")
    with pytest.raises(ValueError, match="language"):
        res.report(str(tmp_path / "x.pdf"), language="fr")

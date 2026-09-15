#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The ISO 717 fiche hands its language to the extended adaptation terms.

The enlarged-range terms beside the boxed rating are whole decibels, so today
their text reads the same in both languages; they still go through the number
formatter with the fiche's language, so that a term printed with a decimal
could never keep an English point on a Spanish fiche.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

pytest.importorskip("reportlab")

from reference_data import ISO717_1_ANNEX_C_R

from phonometry import building
from phonometry._report import iso717

if TYPE_CHECKING:
    from pathlib import Path


def _airborne_with_terms() -> SimpleNamespace:
    """A stand-in carrying two of the enlarged-range terms the fiche looks for."""
    return SimpleNamespace(quantity="airborne", c_50_3150=-1.0, ctr_50_3150=-6.0)


def test_the_terms_hand_their_language_to_the_formatter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = iso717.format_number
    seen: list[str] = []

    def recording(value: float, language: str = "en", **kwargs: Any) -> str:
        seen.append(language)
        return real(value, language, **kwargs)

    monkeypatch.setattr(iso717, "format_number", recording)
    terms = iso717._extended_terms(_airborne_with_terms(), language="es")
    assert len(terms) == 2
    assert seen == ["es", "es"]


def test_the_whole_decibel_terms_read_the_same_in_both_languages() -> None:
    result = _airborne_with_terms()
    english = iso717._extended_terms(result)
    assert iso717._extended_terms(result, language="es") == english
    assert english[0].startswith("C<sub>50-3150</sub> = ")


def test_the_fiche_hands_its_language_to_the_terms(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    real = iso717._extended_terms
    seen: list[str] = []

    def recording(result: object, *, language: str = "en") -> list[str]:
        seen.append(language)
        return real(result, language=language)

    monkeypatch.setattr(iso717, "_extended_terms", recording)
    result = building.weighted_rating(ISO717_1_ANNEX_C_R)
    result.report(str(tmp_path / "airborne_es.pdf"), language="es")
    assert seen == ["es"]

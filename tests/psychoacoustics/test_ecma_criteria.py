#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The four ECMA-418-2:2025 decision criteria ``psychoacoustics`` publishes.

Each one is pinned to the number its clause prints, read on the page and
kept in ``tests/reference_data/psychoacoustics.py`` with the page it was read
on: the audibility criterion of Clause 5.1.9 and the prominence criteria of
Clauses 6.3, 7.2 and 9.2. No function applies them; a caller compares a
result with them, so the test holds the number, its type and its one
address.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry import psychoacoustics

#: ``(published name, printed value, where it is printed)``.
_CRITERIA: list[tuple[str, float, str]] = [
    (
        "AUDIBILITY_THRESHOLD_SONE_HMS",
        ref.ECMA418_2_AUDIBILITY_THRESHOLD_SONE,
        "Clause 5.1.9, PDF page 23, folio 13",
    ),
    (
        "PROMINENT_TONALITY_TU_HMS",
        ref.ECMA418_2_PROMINENT_TONALITY_TU,
        "Clause 6.3, PDF page 34, folio 24",
    ),
    (
        "PROMINENT_ROUGHNESS_ASPER",
        ref.ECMA418_2_PROMINENT_ROUGHNESS_ASPER,
        "Clause 7.2, PDF page 46, folio 36",
    ),
    (
        "PROMINENT_FLUCTUATION_STRENGTH_VACIL_HMS",
        ref.ECMA418_2_PROMINENT_FLUCTUATION_VACIL,
        "Clause 9.2, PDF page 61, folio 51",
    ),
]


@pytest.mark.parametrize(
    ("name", "printed", "where"), _CRITERIA, ids=[row[0] for row in _CRITERIA]
)
def test_each_criterion_is_the_value_its_clause_prints(
    name: str, printed: float, where: str
) -> None:
    assert name in psychoacoustics.__all__, where
    value = getattr(psychoacoustics, name)
    assert type(value) is float, where
    assert value == printed, where


@pytest.mark.parametrize("name", [row[0] for row in _CRITERIA])
def test_each_criterion_is_published_once_in_its_family(name: str) -> None:
    # The loudness criterion is published by the loudness family, the three
    # prominence criteria by the quality family; the domain re-exports both.
    family = (
        psychoacoustics.loudness
        if name.startswith("AUDIBILITY")
        else psychoacoustics.quality
    )
    other = (
        psychoacoustics.quality
        if family is psychoacoustics.loudness
        else psychoacoustics.loudness
    )
    assert name in family.__all__
    assert name not in other.__all__
    assert getattr(family, name) is getattr(psychoacoustics, name)

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Rossing's Table 6.5, the nonlinearity parameter of solids, read back."""

from __future__ import annotations

import reference_data as ref

from phonometry import solids
from phonometry.solids import (
    PUBLISHED_SOLID_NONLINEARITY,
    SolidNonlinearity,
    solid_nonlinearity_named,
)


def test_every_row_is_the_printed_one() -> None:
    rows = list(PUBLISHED_SOLID_NONLINEARITY.values())
    assert len(rows) == len(ref.ROSSING_6_5) == 8
    for row, (name, (bonding, beta)) in zip(rows, ref.ROSSING_6_5, strict=True):
        assert (row.name, row.bonding) == (name, bonding)
        assert row.nonlinearity_parameter == float(beta.replace("−", "-"))


def test_the_one_negative_value_keeps_its_sign_and_says_why() -> None:
    (silica,) = solid_nonlinearity_named("fused silica")
    assert silica.nonlinearity_parameter == -3.4
    assert "-(3 + K3/K2)" in silica.note


def test_the_misspelt_structure_is_kept_and_registered() -> None:
    (fluorite,) = solid_nonlinearity_named("flourite")
    assert "ERRATA" in fluorite.note


def test_the_lookup_finds_both_face_centred_rows() -> None:
    assert [row.name for row in solid_nonlinearity_named("FCC")] == [
        "FCC",
        "FCC (inert gas)",
    ]
    assert solid_nonlinearity_named("water") == ()


def test_every_row_cites_its_page_and_is_reachable() -> None:
    assert {row.source for row in PUBLISHED_SOLID_NONLINEARITY.values()} == {
        "Rossing (2014) Table 6.5, PDF page 261 (printed p. 244)"
    }
    assert solids.PUBLISHED_SOLID_NONLINEARITY is PUBLISHED_SOLID_NONLINEARITY
    assert isinstance(
        next(iter(PUBLISHED_SOLID_NONLINEARITY.values())), SolidNonlinearity
    )

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A floor covering's rating form chosen by a plain ``bool``, for mypy too.

``weighted_impact_improvement`` and ``impact_improvement_adaptation_term``
return an integer, or a value to one decimal place with ``one_decimal=True``
(ISO 717-2:2020 5.4). A literal ``True`` or ``False`` picks the narrow type;
a ``bool`` held in a variable, as when the form comes from a setting, is
accepted and gives either. The suite checks the values at run time; this
file holds the typing, and it only holds it because CI type checks every
file in this directory alongside ``src`` and ``scripts``. Overloads that
take only the two literals still run, and fail here.
"""

from __future__ import annotations

from typing import assert_type

import pytest

from phonometry import building

#: The ΔL of a resilient vinyl, 100 Hz to 3150 Hz, in dB.
_VINYL = (
    0.4,
    0.8,
    1.5,
    2.3,
    3.4,
    4.9,
    6.8,
    9.1,
    11.6,
    14.2,
    16.9,
    19.8,
    22.4,
    25.1,
    27.3,
    29.4,
)


def test_a_literal_form_gives_the_narrow_type() -> None:
    rating = building.weighted_impact_improvement(_VINYL)
    assert_type(rating, int)
    term = building.impact_improvement_adaptation_term(_VINYL)
    assert_type(term, int)
    rating_tenths = building.weighted_impact_improvement(_VINYL, one_decimal=True)
    assert_type(rating_tenths, float)
    term_tenths = building.impact_improvement_adaptation_term(_VINYL, one_decimal=True)
    assert_type(term_tenths, float)
    assert rating == 18
    assert term == -11
    assert rating_tenths == pytest.approx(17.9, abs=1e-9)
    assert term_tenths == pytest.approx(-10.4, abs=1e-9)


@pytest.mark.parametrize(
    ("one_decimal", "expected"), [(False, (8, -3)), (True, (8.4, -3.2))]
)
def test_a_bool_variable_is_accepted_and_gives_either_form(
    *, one_decimal: bool, expected: tuple[float, float]
) -> None:
    rating = building.weighted_impact_improvement(
        _VINYL, reference_floor="lightweight_3", one_decimal=one_decimal
    )
    assert_type(rating, int | float)
    term = building.impact_improvement_adaptation_term(
        _VINYL, reference_floor="lightweight_3", one_decimal=one_decimal
    )
    assert_type(term, int | float)
    form = float if one_decimal else int
    assert type(rating) is form
    assert type(term) is form
    got = (rating, term)
    assert got == pytest.approx(expected, abs=1e-9)

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A record's required fields refuse ``None``, not only a missing argument.

The fields below used to default to ``None`` so that a result built by hand
from a few of its numbers would still construct. They are required now, and
leaving one out of the call raises ``TypeError``. ``None`` can still be passed
for one explicitly, or put there with :func:`dataclasses.replace`, and the
shape and value guards skip ``None`` on purpose, so each record also refuses
it by name at construction instead of failing later in a report or a plot.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from result_factories import (
    _airborne_insulation,
    _airborne_rating,
    _extended_impact_rating,
    _extended_rating,
    _impact_insulation,
    _impact_rating,
    _intensity,
    _slit_aperture,
    _zwicker_stationary,
)

import phonometry as ph

if TYPE_CHECKING:
    from collections.abc import Callable


def _facade() -> ph.building.FacadePredictionResult:
    return ph.building.facade_sound_reduction(
        [ph.building.FacadeElement(name="wall", area=10.0, r=[40.0, 41.0, 42.0])],
        area=10.0,
        volume=50.0,
    )


def _barrier() -> ph.environment.BarrierInsertionLoss:
    return ph.environment.barrier_insertion_loss(
        np.array([125.0, 250.0, 500.0, 1000.0]), 1.5, 5.0, 3.0, 20.0, 1.5
    )


_REQUIRED: tuple[tuple[Callable[[], Any], str], ...] = (
    *((_airborne_insulation, f) for f in ("d", "dnt", "l1", "l2", "t2", "t0")),
    *((_impact_insulation, f) for f in ("l_n_t", "li", "t2", "t0")),
    *((_airborne_rating, f) for f in ("frequencies", "measured", "shifted_reference")),
    *((_impact_rating, f) for f in ("frequencies", "measured", "shifted_reference")),
    *((_extended_rating, f) for f in ("frequencies", "measured")),
    *((_extended_impact_rating, f) for f in ("frequencies", "measured")),
    (_slit_aperture, "depth"),
    (_facade, "elements"),
    (_intensity, "spacing_m"),
    *(
        (_barrier, f)
        for f in (
            "source_height_m",
            "barrier_distance",
            "barrier_height_m",
            "receiver_distance",
            "receiver_height_m",
        )
    ),
    (_zwicker_stationary, "field"),
)


@pytest.mark.parametrize(
    ("factory", "field"),
    _REQUIRED,
    ids=[f"{factory.__name__.lstrip('_')}-{field}" for factory, field in _REQUIRED],
)
def test_a_required_field_refuses_none(factory: Callable[[], Any], field: str) -> None:
    """``replace(result, field=None)`` raises TypeError naming the field."""
    result = factory()
    record = type(result).__name__
    with pytest.raises(TypeError, match=rf"{record}: '{field}' is required"):
        dataclasses.replace(result, **{field: None})


@pytest.mark.parametrize(
    ("factory", "field"),
    [(_airborne_insulation, "r_prime"), (_impact_insulation, "l_n")],
    ids=["airborne-r_prime", "impact-l_n"],
)
def test_an_optional_quantity_may_still_be_absent(
    factory: Callable[[], Any], field: str
) -> None:
    """``R'`` and ``L'n`` stay optional: a measurement may not produce them."""
    result = dataclasses.replace(factory(), **{field: None})
    assert getattr(result, field) is None

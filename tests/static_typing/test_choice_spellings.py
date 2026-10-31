#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A choice is written as its ``Literal`` spells it, for mypy and at run time.

A parameter typed with a ``Literal`` of its options promises one spelling of
each, and the runtime keeps the promise: it checks the text as the caller wrote
it, so ``"R_w"`` for ``"r_w"`` or ``"d"`` for ``"D"`` is refused by the type
checker and by the call alike. Each bad argument stands on a line of its own
with the error code mypy reports for it, so the ignore cannot drift onto
another line and becomes unused, and fails, the day the call accepts the value.
CI type checks every file in this directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

import pytest

from phonometry import aircraft, building


def test_a_case_variant_of_a_single_number_quantity_is_refused() -> None:
    with pytest.raises(ValueError, match=r"'quantity' must be one of .*got 'R_w'"):
        building.single_number_uncertainty(
            "R_w",  # type: ignore[arg-type]
            "A",
        )


def test_a_lower_case_operation_is_refused_by_the_flap_lookup() -> None:
    plane = aircraft.PerformanceAircraft(
        aircraft_id="JET",
        n_engines=2,
        max_static_thrust_lb=25000.0,
        max_landing_weight_lb=150000.0,
        aerodynamic_coefficients={
            ("D", "ZERO"): aircraft.AerodynamicCoefficients(drag_ratio=0.055)
        },
    )
    assert plane.flap("D", " zero ").drag_ratio == pytest.approx(0.055)
    with pytest.raises(ValueError, match=r"'operation' must be one of .*got 'd'"):
        plane.flap(
            "d",  # type: ignore[arg-type]
            "ZERO",
        )

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The components of an uncertainty budget are paired with its field, for mypy too.

``metrology.comparison_uncertainty_budget`` and
``metrology.reciprocity_uncertainty_budget`` take the components of the table
their ``field`` picks: IEC 61094-5 Table D.1 or IEC 61094-8 Table 2 for a
comparison, Table 1 of IEC 61094-2 or of IEC 61094-3 for a reciprocity
calibration. A component of the other table is refused with ``ValueError``
when the call runs, and a type checker refuses it first: a mapping typed by
one table's components goes with that table's field and no other. A field
held in a variable that may be either takes the components both tables list,
the only ones right for both. The suite checks the values at run time; this
file holds the typing, because CI type checks every file in this directory
alongside ``src`` and ``scripts``, in strict mode, so an ignore that a call no
longer needs fails too.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest

from phonometry import metrology

if TYPE_CHECKING:
    from phonometry.metrology.comparison_calibration import (
        PressureComparisonComponent,
    )
    from phonometry.metrology.reciprocity_calibration import (
        PressureReciprocityComponent,
    )

_FIELDS: tuple[Literal["pressure", "free"], ...] = ("pressure", "free")


def test_a_comparison_budget_takes_the_components_of_its_field() -> None:
    pressure: dict[PressureComparisonComponent, float] = {"impedance": 0.01}
    budget = metrology.comparison_uncertainty_budget(pressure, frequency_hz=1000.0)
    assert budget.names == ("impedance",)


def test_a_comparison_component_of_the_other_table_is_refused() -> None:
    pressure: dict[PressureComparisonComponent, float] = {"impedance": 0.01}
    with pytest.raises(ValueError, match="not components of IEC 61094-8"):
        metrology.comparison_uncertainty_budget(  # type: ignore[call-overload]
            pressure, frequency_hz=1000.0, field="free"
        )


def test_a_comparison_field_in_a_variable_takes_the_shared_components() -> None:
    for field in _FIELDS:
        budget = metrology.comparison_uncertainty_budget(
            {"reference": 0.03, "repeatability": 0.02},
            frequency_hz=1000.0,
            field=field,
        )
        assert budget.names == ("reference", "repeatability")


def test_a_comparison_field_in_a_variable_refuses_one_table_only() -> None:
    field = _FIELDS[1]
    with pytest.raises(ValueError, match="not components of IEC 61094-8"):
        metrology.comparison_uncertainty_budget(
            {"impedance": 0.01},
            frequency_hz=1000.0,
            field=field,  # type: ignore[arg-type]
        )


def test_a_reciprocity_component_of_the_other_table_is_refused() -> None:
    coupler: dict[PressureReciprocityComponent, float] = {"coupler_length": 0.01}
    budget = metrology.reciprocity_uncertainty_budget(coupler, frequencies=[1000.0])
    assert budget.names == ("coupler_length",)
    with pytest.raises(ValueError, match="not components of Table 1 of IEC 61094-3"):
        metrology.reciprocity_uncertainty_budget(  # type: ignore[call-overload]
            coupler, frequencies=[1000.0], field="free"
        )


def test_a_reciprocity_field_in_a_variable_takes_the_shared_components() -> None:
    for field in _FIELDS:
        budget = metrology.reciprocity_uncertainty_budget(
            {"voltage_ratio": 0.003, "repeatability": 0.01},
            frequencies=[1000.0],
            field=field,
        )
        assert budget.names == ("voltage_ratio", "repeatability")

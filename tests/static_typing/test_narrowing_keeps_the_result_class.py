#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A method that returns the record with fewer lines returns its own class, for mypy too.

``FaultFrequencyResult.within`` keeps the lines in a band and returns
``dataclasses.replace(self, ...)``: at run time a ``BladePassResult`` stays one,
with its ``lobe_patterns``. Annotated as the base class, a type checker read the
narrowed blade-pass result as a plain fault-frequency result and refused its
lobe patterns. This file only holds because CI type checks every file in this
directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_type

if TYPE_CHECKING:
    from phonometry import vibration

    fan = vibration.blade_pass_frequencies(60.0, 4, n_harmonics=2, n_vanes=2)
    narrowed = fan.within(0.0, 400.0)
    assert_type(narrowed, vibration.BladePassResult)
    patterns = narrowed.lobe_patterns
    faults = vibration.bearing_fault_frequencies(25.0, 9, 0.0079, 0.0390)
    assert_type(faults.within(0.0, 400.0), vibration.FaultFrequencyResult)

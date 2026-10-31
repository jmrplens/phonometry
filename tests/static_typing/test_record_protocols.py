#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A frozen record meets the protocol a function reads it through, for mypy too.

``enclosure_insertion_loss`` takes a panel prediction through
``PanelTransmissionResult``, a protocol that names the two fields it reads.
A protocol that declares them as plain attributes asks for members a caller
may write, and a frozen record refuses every write, so a type checker would
refuse the very results the function is documented to take. Declared as
read-only properties, they are met by the record's fields.
``tests/test_package_architecture.py`` holds every protocol of the package to
that; this file holds the one call a caller writes to mypy. CI type checks
every file in this directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

import numpy as np

from phonometry import building, noise_control, vibration

_BANDS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])


def test_a_frozen_panel_prediction_is_taken_whole() -> None:
    stiffness = vibration.plate_bending_stiffness(6.2e10, 0.006, 0.24)
    critical = vibration.coincidence_frequency(15.0, stiffness)
    panel = building.single_panel_transmission_loss(
        _BANDS, 15.0, critical_frequency=critical, loss_factor=0.024
    )
    result = noise_control.enclosure_insertion_loss(
        panel, 20.0, 18.0, np.full(_BANDS.size, 0.3)
    )
    assert result.frequencies is not None
    np.testing.assert_allclose(result.frequencies, _BANDS)

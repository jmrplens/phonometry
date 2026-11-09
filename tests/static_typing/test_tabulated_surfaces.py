#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``measurement_positions`` offers the one surface it has a table for.

ISO 3744 and ISO 3746 tabulate microphone positions on a hemisphere alone;
ISO 3744:2010 Annex C places them on a box by subdividing its faces, which no
table gives. The function's ``surface`` is typed ``Literal["hemisphere"]``, so
a type checker refuses the ``"box"`` that the call refuses when it runs, and
the error still says why. The bad argument stands on a line of its own with the
error code mypy reports for it, so the ignore becomes unused, and fails, the
day the annotation offers a box again. CI type checks every file in this
directory alongside ``src`` and ``scripts``.
"""

from __future__ import annotations

import pytest

from phonometry import emission


def test_a_box_is_refused_by_the_type_checker_and_the_call() -> None:
    with pytest.raises(ValueError, match=r"got 'box'.*ISO 3744:2010 Annex C"):
        emission.measurement_positions(
            "box",  # type: ignore[arg-type]
            radius=1.0,
        )


def test_a_hemisphere_is_taken() -> None:
    assert emission.measurement_positions("hemisphere", radius=1.0).shape == (10, 3)

#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The choices the vibration package reads in more than one module (private).

A building class is a row of DIN 4150-3:1999-02 Table 1 wherever it is asked
for: the guideline values of :mod:`~phonometry.vibration.structural`, and the
assessment weightings of DIN 45669-1 Annex E that invert those same rows in
:mod:`~phonometry.vibration.immission`. A working range is one of the two of
DIN 45669-1 5.2.3.1, read by the meter chain and by the train-passage
evaluation of DIN 45672-2 that reuses it. Each vocabulary is written here
once, so the two modules that read it cannot drift apart.
"""

from __future__ import annotations

from typing import Literal

__all__: list[str] = []

#: The three building classes of DIN 4150-3 Table 1, in the order the rows are
#: printed: commercial and industrial buildings (row 1), dwellings and
#: buildings of like construction or use (row 2), and buildings that suit
#: neither and are worth preserving, such as listed ones (row 3).
BuildingClass = Literal["commercial", "residential", "sensitive"]

#: The building classes, in the order of the rows of Table 1.
_BUILDING_CLASSES: tuple[BuildingClass, ...] = (
    "commercial",
    "residential",
    "sensitive",
)

#: The two working ranges of DIN 45669-1 5.2.3.1: ``"building"`` (1 Hz to
#: 80 Hz) and ``"railway"`` (4 Hz to 315 Hz, the range of DIN 45672-1).
WorkingRange = Literal["building", "railway"]

#: The working ranges, in the order 5.2.3.1 names them.
_WORKING_RANGES: tuple[WorkingRange, ...] = ("building", "railway")

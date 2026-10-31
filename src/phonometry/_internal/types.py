#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Shared typing aliases and array/scalar coercion helpers (private).

Seeded by the library audit: several modules re-declared the same
``Real`` alias and hand-copied the "0-d array becomes a float" return
idiom. New code should import from here; existing modules migrate as
they are touched.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes

#: Real-valued float64 array alias shared across the library.
Real = NDArray[np.float64]

#: The band set of a spectrum, as every public ``fraction`` writes it: 1 for
#: octaves, 3 for one-third octaves (the denominator ``b`` of the IEC 61260-1
#: bandwidth designator ``1/b``).
BandFraction = Literal[1, 3]

#: The band set of each :data:`BandFraction`, in the words a message uses.
BAND_SET_NAMES: Mapping[int, str] = MappingProxyType(
    {1: "octave", 3: "one-third-octave"}
)

#: A frequency weighting that is either the A-weighting of IEC 61672-1 or
#: none at all, written ``"Z"`` as everywhere a flat weighting is chosen.
AOrZWeighting = Literal["A", "Z"]

#: A free or a diffuse sound field, the two listening conditions a hearing
#: threshold is referred to.
FreeOrDiffuseField = Literal["free", "diffuse"]

#: The sound field a microphone is calibrated in: a pressure field (a closed
#: coupler) or a free field.
CalibrationField = Literal["pressure", "free"]

#: The engine a ``report`` entry point draws its fiche with. ``"reportlab"``
#: is the only one; the parameter is the seam a second engine would come in by.
ReportEngine = Literal["reportlab"]

#: The two panels of a two-panel figure, top first: what a multi-panel
#: ``.plot()`` returns when it is handed no axes. The API reference prints it
#: as its definition.
type TwoPanels = tuple[Axes, Axes]

#: The three panels of a three-panel figure, top first.
type ThreePanels = tuple[Axes, Axes, Axes]

#: The two weightings :data:`AOrZWeighting` accepts.
A_OR_Z_WEIGHTINGS: tuple[AOrZWeighting, ...] = ("A", "Z")

#: The two fields :data:`CalibrationField` accepts.
CALIBRATION_FIELDS: tuple[CalibrationField, ...] = ("pressure", "free")


def as_float_or_array(x: np.ndarray | float) -> np.ndarray | float:
    """Return a Python ``float`` for a 0-d array or scalar, the array otherwise.

    :param x: The array (or scalar) produced by a vectorised computation.
    :return: ``float(x)`` when *x* is zero-dimensional, else *x* unchanged.
    """
    return float(x) if np.ndim(x) == 0 else x

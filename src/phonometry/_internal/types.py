#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Shared typing aliases and array/scalar coercion helpers (private).

Seeded by the library audit: several modules re-declared the same
``Real`` alias and hand-copied the "0-d array becomes a float" return
idiom. New code should import from here; existing modules migrate as
they are touched.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

if TYPE_CHECKING:
    from matplotlib.axes import Axes

#: Real-valued float64 array alias shared across the library.
Real = NDArray[np.float64]

#: One real number, as a function that takes a number or an array of them is
#: handed it: a Python ``float`` or ``int``, or a numpy one (``np.float32``
#: and ``np.int64`` are not Python numbers to a type checker). Such a function
#: returns a Python ``float`` for it.
RealScalar = float | np.floating[Any] | np.integer[Any]

#: Several real numbers: a sequence of them, Python or numpy ones (a list of
#: ``np.float32`` is no ``Sequence[float]`` to a type checker), or a numpy
#: array of any shape, a zero-dimensional one included. A function that takes
#: a number or an array of them returns an array for it. A list that mixes
#: Python and numpy numbers is no ``ArrayLike`` to numpy's own stubs, so it
#: is left out here too and reads as the union.
RealValues = (
    Sequence[float]
    | Sequence[np.floating[Any]]
    | Sequence[np.integer[Any]]
    | NDArray[Any]
)

#: A fixed count of arrays a record holds as one field, a curve's ``(x, y)``
#: or the ``(x, y, z)`` axes of an elevation model: a sequence of them, each
#: any array-like (a tuple of an array and a list), or one array whose rows
#: they are (``np.vstack((x, y))``), which is no ``Sequence`` to a type
#: checker and so is named beside it.
ArrayRows = Sequence[ArrayLike] | NDArray[Any]

#: Values keyed by a band centre frequency in hertz (or by another number a
#: caller writes as an ``int`` as often as a ``float``, an angle in degrees),
#: ``{125: 40.0, ...}`` or ``{125.0: 40.0, ...}``. ``Mapping`` is invariant in
#: its key, so a mapping keyed by ``float`` alone refuses a ``dict[int,
#: float]``: both are named.
BandMapping = Mapping[int, float] | Mapping[float, float]

#: Values by band, as a :data:`BandMapping` of band centre to value or in
#: band order as any array-like.
BandValues = BandMapping | ArrayLike


def float_keyed[V](mapping: Mapping[int, V] | Mapping[float, V]) -> dict[float, V]:
    """The entries of a mapping keyed by a number, each key read as a ``float``.

    ``{125: 40.0}`` and ``{125.0: 40.0}`` name the same band; a reader that
    looks a band up by its centre as a ``float`` finds it in either once the
    keys are read this way.

    :param mapping: Values keyed by an ``int`` or a ``float``.
    :return: A new dictionary keyed by ``float``, in the mapping's order.
    """
    return {float(key): value for key, value in mapping.items()}


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

#: A ground impedance class of the Nordtest classification, by its letter:
#: ``"A"`` (very soft, snow or moss) to ``"H"`` (very hard, dense concrete),
#: as CNOSSOS-EU and ECAC Doc 32 Table 5 rate a ground and IEC TS
#: 61400-11-2:2024 Table C.1 describes it.
GroundClass = Literal["A", "B", "C", "D", "E", "F", "G", "H"]

#: The sex a population statistic is tabulated by, as ISO 7029, ISO 1999 and
#: ISO 2631-5 print their columns.
Sex = Literal["male", "female"]

#: A spectral-analysis taper, as :func:`scipy.signal.get_window` reads one: a
#: window name (``"hann"``), or a tuple of a name and its parameters
#: (``("kaiser", 8.6)``, ``("tukey", 0.5)``, ``("general_cosine", weights)``).
#: A bare number, which ``get_window`` reads as the beta of a Kaiser window,
#: is left out: the Welch estimators refuse it, and ``("kaiser", beta)``
#: names it everywhere.
WindowSpec = str | tuple[ArrayLike, ...]


def own_window(window: WindowSpec) -> WindowSpec:
    """The window specification with no parameter the caller can still edit.

    A name is kept as given. In a tuple, a list parameter, such as the
    weights of ``("general_cosine", weights)``, becomes a tuple, so editing
    the caller's weights afterwards does not rename the window a result
    was computed with. Every result that keeps its window stores it through
    this function first in its ``__post_init__``, so one a caller builds by
    hand, or :func:`dataclasses.replace` builds anew, holds it as the
    function that computes it would; an array parameter is the read-only
    copy :class:`~phonometry._internal.frozen.OwnsArrays` made of it before
    that hook ran.

    :param window: The specification a record was given.
    :return: The same specification, its list parameters as tuples.
    """
    if not isinstance(window, tuple):
        return window
    return tuple(tuple(item) if isinstance(item, list) else item for item in window)


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


#: How the arguments that decide a result's shape came in: all single numbers,
#: single numbers among which a zero-dimensional array, or with a sequence or an
#: array of values among them.
AnswerForm = Literal["number", "zero-dimensional", "array"]


def answer_form(like: tuple[ArrayLike | None, ...]) -> AnswerForm:
    """The form a result takes for the arguments that decide its shape.

    An array in, an array out: ``"array"`` when one of *like* holds more
    than one dimension's worth of values (a sequence, or an array of one
    dimension or more), ``"zero-dimensional"`` when all are single numbers
    and one of them is a numpy array, ``"number"`` otherwise. ``None`` (an
    optional argument left out) decides nothing.

    :param like: Every argument that decides the shape of the result, as the
        caller was handed it.
    :return: The form the result is given in.
    """
    given = [argument for argument in like if argument is not None]
    if any(np.ndim(argument) != 0 for argument in given):
        return "array"
    if any(isinstance(argument, np.ndarray) for argument in given):
        return "zero-dimensional"
    return "number"


def as_float_or_array(
    values: ArrayLike, *, like: tuple[ArrayLike | None, ...]
) -> float | NDArray[np.float64]:
    """Return *values* in the form the arguments that decide their shape came in.

    An array in, an array out: the result is a Python ``float`` only when
    none of *like* is a numpy array and every one of them is a single number;
    a sequence or an array among them, a zero-dimensional array included,
    gives an array (:func:`answer_form`). When every argument in *like* is a
    single number the result is one number too, so a validator that hands a
    scalar back as a one-element array is read through, and an argument left
    out of *like* that does shape the result fails loudly instead of being
    dropped.

    :param values: The result of a computation that broadcasts *like*.
    :param like: Every argument that decides the shape of the result, as the
        caller was handed it: ``like=(frequency,)``, ``like=(a, b)``. A tuple
        always, so an argument that is itself a tuple of numbers is not read
        as several arguments.
    :return: ``float`` for numbers in, a ``float64`` array otherwise.
    :raises ValueError: If every argument in *like* is a single number and
        *values* holds more than one.
    """
    result = np.asarray(values, dtype=np.float64)
    form = answer_form(like)
    if form == "array":
        return result
    return float(one_value(result)) if form == "number" else one_value(result)


def one_value[T: np.generic](values: NDArray[T]) -> NDArray[T]:
    """*values* as the zero-dimensional array of the one value they hold.

    :param values: A result computed from arguments that are all single
        numbers, which a validator may have made one-element and 1-D.
    :return: The same value, zero-dimensional.
    :raises ValueError: If *values* holds more than one value: an argument
        that shapes it is missing from the ``like`` it was read against.
    """
    if values.size != 1:
        msg = (
            f"a result of shape {values.shape} from arguments that are all "
            "single numbers: an argument that shapes it is missing from 'like'."
        )
        raise ValueError(msg)
    return values.reshape(())


def as_float_if_reduced(values: ArrayLike) -> float | NDArray[np.float64]:
    """Return a Python ``float`` for a result reduced to one number, else the array.

    For a function that reduces an axis (a level over the samples of a
    signal, an energy average over positions): the rank of what it was handed
    decides whether one number is left, not whether it was an array.

    :param values: The result of the reduction.
    :return: ``float`` when *values* is zero-dimensional, else a ``float64``
        array.
    """
    result = np.asarray(values, dtype=np.float64)
    return float(result) if result.ndim == 0 else result

#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Predicting the fundamental frequency of a building (ISO 4866 Annex D).

A vibration measurement on a building is read against the building's own
response, and that response starts with one number: the lowest natural
frequency of the fundamental translation mode. Measure it when you can, says
ISO 4866; Annex D is what to do when you cannot, because the excitation is too
weak, the damping too high or the subcomponents too loud to separate.

The annex offers four empirical predictors and is candid about all of them.
The simplest is the storey count, :math:`f = 10/n` hertz, the same rule
DIN 4150-3 prints in its 6.4 and this library already publishes as
:func:`~phonometry.vibration.structural.building_damage.storey_fundamental_frequency`.
The other three are the forms the period :math:`T` takes in national codes,
each with a coefficient the codes disagree about:

.. math::

   T = k_1 h \qquad
   T = \frac{k_2 h}{\sqrt{b}} \qquad
   T = \frac{k_3 h}{\sqrt{b}} \sqrt{\frac{h}{h + b}}

with :math:`h` the height and :math:`b` the width parallel to the force, both
in metres. The coefficients range over 0,014 to 0,03, over 0,087 to 0,109 and
over 0,06 to 0,08 respectively, so the choice of code moves the answer by more
than a factor of two in the first form alone.

Fitting one curve to measurements instead of to codes, D.3 quotes
:math:`f = 46/h` hertz (:math:`T = 0{,}022\,h` seconds) from a sample of 163
rectangular-plan buildings, and prints the fit with the data around it: errors
of **± 50 %** are not uncommon, and the annex says that is typical of what an
empirical formula can do. It also says something worth repeating, since it is
the opposite of what a reader expects: computer models correlate *worse* with
measured frequencies than :math:`46/h` does, because the model is only as good
as its idea of what the building is made of.

Damping (D.4) has no predictor at all. Measured values between **0,5 %** and
**2,1 %** of critical are what the annex reports for buildings where
soil-structure interaction was negligible, and the two orthogonal translation
modes of one building can differ widely. Damping is partly a function of how
the building was put together, so anticipate large errors.

Everything here is an estimate with a stated error, which is the only honest
way to use it: as the answer to "is the excitation anywhere near the
building's own frequency", not as a frequency to design against.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.types import as_float_or_array
from ..._internal.validation import require_choice, require_positive
from .building_damage import storey_fundamental_frequency

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

#: The four predictors of Annex D, by what they are computed from.
PeriodModel = Literal["storeys", "height", "height_width", "slenderness"]

PERIOD_MODELS: tuple[str, ...] = ("storeys", "height", "height_width", "slenderness")

#: D.2: the range each code coefficient is drawn from. ``height`` is
#: :math:`k_1` of Formula (D.1), ``height_width`` is :math:`k_2` of (D.2) and
#: ``slenderness`` is :math:`k_3` of (D.3). The midpoint of each range is what
#: this module uses when a caller states no coefficient.
PERIOD_COEFFICIENT_RANGES: dict[str, tuple[float, float]] = {
    "height": (0.014, 0.03),
    "height_width": (0.087, 0.109),
    "slenderness": (0.06, 0.08),
}

#: D.2: the storey rule as a period, ``T = 0,1 n`` seconds, which is the
#: reciprocal of the ``f = 10/n`` hertz DIN 4150-3 6.4 also prints.
STOREY_PERIOD_COEFFICIENT_S: float = 0.1

#: D.3: the fit to 163 rectangular-plan buildings, ``f = 46/h`` hertz.
HEIGHT_FREQUENCY_CONSTANT_HZ_M: float = 46.0

#: D.3: the same fit written as a period, ``T = 0,022 h`` seconds. It is the
#: reciprocal of :data:`HEIGHT_FREQUENCY_CONSTANT_HZ_M` to two figures, which
#: is the precision the annex prints it to.
HEIGHT_PERIOD_COEFFICIENT_S_PER_M: float = 0.022

#: D.3: "errors of ± 50 % are not uncommon, and this is typical of the
#: accuracy which can be expected using empirical formulae".
EMPIRICAL_FREQUENCY_TOLERANCE: float = 0.5

#: D.4: the damping ratios measured on buildings where soil-structure
#: interaction was negligible, as a fraction of critical rather than a
#: percentage. Nothing predicts a value inside this range.
DAMPING_RATIO_RANGE: tuple[float, float] = (0.005, 0.021)


def _coefficient(model: str, coefficient: float | None) -> float:
    """The code coefficient to use, or the midpoint of its printed range."""
    if coefficient is not None:
        return require_positive(coefficient, "coefficient")
    low, high = PERIOD_COEFFICIENT_RANGES[model]
    return 0.5 * (low + high)


def _refuse_unused(model: str, **given: object) -> None:
    """Refuse an argument the chosen predictor has no use for.

    Each of the four forms is written on a different set of dimensions, and a
    caller who hands over one the form ignores has misread which form they
    asked for. Taking it silently is worse than saying so: a height given to
    the storey model would be carried into the result and drawn on Figure D.1
    as though the prediction had used it.

    :param model: The predictor, one of :data:`PERIOD_MODELS`.
    :param given: The optional arguments as the caller passed them.
    :raises ValueError: On the first argument the model does not use.
    """
    used = {
        "storeys": {"storeys"},
        "height": {"height_m", "coefficient"},
        "height_width": {"height_m", "width_m", "coefficient"},
        "slenderness": {"height_m", "width_m", "coefficient"},
    }[model]
    for parameter, value in given.items():
        if value is not None and parameter not in used:
            msg = (
                f"The {model!r} model does not use {parameter!r}; it is not "
                "accepted, so a value given for it cannot be silently ignored."
            )
            raise ValueError(msg)


def fundamental_period(
    model: PeriodModel | str,
    *,
    storeys: int | None = None,
    height_m: float | None = None,
    width_m: float | None = None,
    coefficient: float | None = None,
) -> float:
    r"""The fundamental translation period of a building, in seconds (D.2).

    Four predictors, and which arguments are needed depends on which:

    * ``"storeys"`` needs *storeys*: :math:`T = 0{,}1\,n`.
    * ``"height"`` needs *height_m*: :math:`T = k_1 h`.
    * ``"height_width"`` needs both and *width_m*: :math:`T = k_2 h/\sqrt{b}`.
    * ``"slenderness"`` needs both:
      :math:`T = (k_3 h/\sqrt{b})\sqrt{h/(h+b)}`.

    The coefficient defaults to the midpoint of the range D.2 prints for that
    form, since the annex gives a range and no way to choose inside it; state
    *coefficient* to use the value of a particular code.

    :param model: One of :data:`PERIOD_MODELS`.
    :param storeys: Number of storeys ``n``, for the storey model.
    :param height_m: Height ``h`` above the base, in metres.
    :param width_m: Width ``b`` parallel to the force, in metres.
    :param coefficient: The code coefficient, or ``None`` for the midpoint of
        :data:`PERIOD_COEFFICIENT_RANGES`. Not accepted by the storey model,
        which has no coefficient to choose.
    :return: The fundamental period, in seconds.
    :raises ValueError: If the model is not one of the four, if an argument
        the model needs is missing or not positive, or if an argument the
        model does not use is given.
    """
    name = require_choice(str(model), "model", PERIOD_MODELS)
    _refuse_unused(
        name,
        storeys=storeys,
        height_m=height_m,
        width_m=width_m,
        coefficient=coefficient,
    )
    if name == "storeys":
        if storeys is None:
            msg = "The storey model needs 'storeys'."
            raise ValueError(msg)
        return 1.0 / storey_fundamental_frequency(storeys)
    if height_m is None:
        msg = f"The {name!r} model needs 'height_m'."
        raise ValueError(msg)
    height = require_positive(height_m, "height_m")
    k = _coefficient(name, coefficient)
    if name == "height":
        return k * height
    if width_m is None:
        msg = f"The {name!r} model needs 'width_m'."
        raise ValueError(msg)
    width = require_positive(width_m, "width_m")
    period = k * height / np.sqrt(width)
    if name == "slenderness":
        period *= np.sqrt(height / (height + width))
    return float(period)


def fundamental_frequency(
    model: PeriodModel | str,
    *,
    storeys: int | None = None,
    height_m: float | None = None,
    width_m: float | None = None,
    coefficient: float | None = None,
) -> float:
    """The reciprocal of :func:`fundamental_period`, in hertz.

    Arguments and errors are that function's; this exists because the annex
    states two of its four predictors as frequencies and two as periods, and a
    reader should not have to remember which.

    :param model: One of :data:`PERIOD_MODELS`.
    :param storeys: Number of storeys ``n``, for the storey model.
    :param height_m: Height ``h`` above the base, in metres.
    :param width_m: Width ``b`` parallel to the force, in metres.
    :param coefficient: The code coefficient, or ``None`` for the midpoint.
    :return: The fundamental frequency, in hertz.
    """
    return 1.0 / fundamental_period(
        model,
        storeys=storeys,
        height_m=height_m,
        width_m=width_m,
        coefficient=coefficient,
    )


def height_fundamental_frequency(height: ArrayLike) -> np.ndarray | float:
    """The ``f = 46/h`` fit of D.3, in hertz.

    Fitted to 163 rectangular-plan buildings rather than taken from a code,
    which is why it is here on its own: D.3 also reports that computed
    frequencies correlate with measurement *worse* than this line does.

    :param height: Height ``h`` above the base, in metres (scalar or array).
    :return: The predicted fundamental frequency, in hertz.
    :raises ValueError: If a height is not positive and finite.
    """
    h = np.asarray(height, dtype=np.float64)
    if np.any(h <= 0.0) or not np.all(np.isfinite(h)):
        msg = "'height' must be positive and finite."
        raise ValueError(msg)
    return as_float_or_array(HEIGHT_FREQUENCY_CONSTANT_HZ_M / h)


def empirical_frequency_bounds(frequency_hz: float) -> tuple[float, float]:
    """The ± 50 % band D.3 puts around an empirical prediction, in hertz.

    :param frequency_hz: A predicted fundamental frequency, in hertz.
    :return: ``(lower, upper)``, the band the annex says is not uncommon.
    :raises ValueError: If the frequency is not positive and finite.
    """
    f = require_positive(frequency_hz, "frequency_hz")
    return (
        f * (1.0 - EMPIRICAL_FREQUENCY_TOLERANCE),
        f * (1.0 + EMPIRICAL_FREQUENCY_TOLERANCE),
    )


@dataclass(frozen=True)
class BuildingFrequencyEstimate:
    """One predicted fundamental frequency, with the error it carries.

    :ivar frequency_hz: The predicted fundamental frequency.
    :ivar period_s: The same prediction as a period.
    :ivar model: Which of :data:`PERIOD_MODELS` produced it.
    :ivar coefficient: The code coefficient used, or ``None`` for the storey
        model, which has none.
    :ivar height_m: The height it was computed from, where the model uses one.
    """

    frequency_hz: float
    period_s: float
    model: str
    coefficient: float | None
    height_m: float | None

    @property
    def bounds_hz(self) -> tuple[float, float]:
        """The ± 50 % band of D.3 around :attr:`frequency_hz`."""
        return empirical_frequency_bounds(self.frequency_hz)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw Figure D.1 with this estimate on it.

        The ``f = 46/h`` line against height on logarithmic axes, the ± 50 %
        band around it, and this estimate as a point.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_building_frequency`.
        :raises ValueError: If the estimate came from the storey model, which
            has no height to place a point at.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_building_frequency

        if self.height_m is None:
            msg = (
                "Figure D.1 is drawn against height, and the storey model has "
                "no height; give 'height_m' to a model that uses one."
            )
            raise ValueError(msg)
        check_language(language)
        return plot_building_frequency(self, ax=ax, language=language, **kwargs)


def estimate_fundamental_frequency(
    model: PeriodModel | str,
    *,
    storeys: int | None = None,
    height_m: float | None = None,
    width_m: float | None = None,
    coefficient: float | None = None,
) -> BuildingFrequencyEstimate:
    """One prediction, bundled with the coefficient and the error band.

    :param model: One of :data:`PERIOD_MODELS`.
    :param storeys: Number of storeys ``n``, for the storey model.
    :param height_m: Height ``h`` above the base, in metres.
    :param width_m: Width ``b`` parallel to the force, in metres.
    :param coefficient: The code coefficient, or ``None`` for the midpoint.
    :return: The prediction, as a :class:`BuildingFrequencyEstimate`.
    :raises ValueError: For anything :func:`fundamental_period` refuses.
    """
    period = fundamental_period(
        model,
        storeys=storeys,
        height_m=height_m,
        width_m=width_m,
        coefficient=coefficient,
    )
    name = str(model)
    used = None if name == "storeys" else _coefficient(name, coefficient)
    return BuildingFrequencyEstimate(
        frequency_hz=1.0 / period,
        period_s=period,
        model=name,
        coefficient=used,
        height_m=None if height_m is None else float(height_m),
    )

#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""How often a blast is how loud: the distribution of its sound exposure level
(ISO 13474:2009, clauses 4 and 5).

A blast, a shot or a detonation a few kilometres away is heard at a level that
changes from one event to the next by ten decibels and more, because the
weather between source and receiver changes. ISO 13474 does not predict one
level; it describes the weather as a set of **replica atmospheres**, each one
a combination of an atmospheric-absorption class ``k`` and an
excess-attenuation class ``l`` with its probability of occurrence, computes
the frequency-weighted single-event sound exposure level ``L_E,w,k,l`` for
each, and turns that list into a statistical distribution. This module is that
statistical core. The propagation that produces each ``L_E,w,k,l`` (clause 6),
the classification of the weather (clause 7) and the probability of each class
from meteorological data (clause 8) are the caller's input.

The chain, in the order the standard writes it:

* the frequency-weighted level of each replica from its band levels,
  Equation (5), :func:`frequency_weighted_sel`;
* the joint probability of the two classes, Equation (14),
  :func:`replica_probabilities`;
* the long-term average of the single-event level, Equation (7), and the
  rating level that adds the adjustment ``K`` for highly impulsive sound,
  Equation (8), :func:`long_term_sel`;
* the levels placed in increasing order as ``M`` classes with contiguous
  boundaries half-way between consecutive levels and the density of each
  class, Equations (10) to (16);
* each class split into ``N_sub`` subclasses, Equations (17) to (20), and each
  subclass replaced by a normal distribution of standard deviation
  :math:`\sigma` (5 dB is the value the standard says is typically used) whose
  mean is shifted down by

  .. math::

     \Delta\mu = 10\lg\left[\frac{1}{\sigma\sqrt{2\pi}}
     \int_{-\infty}^{\infty} 10^{0{,}1x}\,
     \mathrm{e}^{-x^{2}/(2\sigma^{2})}\,\mathrm{d}x\right]
     = \frac{\sigma^{2}\ln 10}{20}~\text{dB}
     \tag{22}

  so that the energetic mean of the subclass stays where it was, Equations
  (21) to (23), :func:`turbulence_level_shift`;
* from the continuous density :math:`\rho^{*}(x)`, the probability that the
  level exceeds ``x``, Equation (24), and the ``n``-percent exceedance level,
  Equation (25), and the long-term level computed a second time from the
  distribution, Equation (A.4) of Annex A.

:func:`sel_distribution` does the last three steps and returns a
:class:`SelDistribution`, whose ``.plot()`` draws the class density, the
continuous density or the exceedance curve.

Two readings the text leaves to the implementer
-----------------------------------------------

**Equal levels.** Equation (11) puts a boundary half-way between consecutive
levels, so two equal levels share a boundary at that level and each keeps a
class of non-zero width on its own side; Annex A does exactly that with its
two classes at 30,8 dB and its two at 31,8 dB, and so does this module. The
standard says a class is undefined only when three consecutive levels are
equal, since the middle one then has no width, and that "classes with the same
level shall be combined". A run of two equal levels at either end of the list
leaves a class of no width in the same way, through Equation (12) or (13).
Every run of equal levels that would leave a class of no width is therefore
combined into one class carrying the sum of their probabilities; every other
run is left as the standard writes it.

**The integrals.** Equations (22), (24) and (A.4) are integrals of Gaussian
functions and are evaluated here in closed form, not by quadrature: the shift
is :math:`\sigma^{2}\ln 10/20`, the exceedance is a sum of Gaussian tail
probabilities, and :math:`\int\rho^{*}(x)\,10^{0{,}1x}\,\mathrm{d}x` is a sum of
lognormal means. There is no integration range to choose and no truncation to
account for.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.frozen import read_only
from ..._internal.validation import require_count, require_finite, require_positive

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "SelDistribution",
    "frequency_weighted_sel",
    "long_term_sel",
    "replica_probabilities",
    "sel_distribution",
    "turbulence_level_shift",
]

#: Clause 5: "a normal distribution having a standard deviation of 5 dB (the
#: value typically used)". The default of :func:`sel_distribution`, which a
#: caller with better knowledge of the local spread replaces; the clause itself
#: says other distributions may be more appropriate.
_TYPICAL_SIGMA_DB = 5.0

#: Annex A: "each class, m, in the example was divided into 10 equal,
#: contiguous subclasses". The standard fixes no number of subclasses; this is
#: the one its worked example uses.
_ANNEX_A_SUBCLASSES = 10

#: How far the probabilities of all the replica atmospheres may sum from one.
#: Clause 4.2 chooses the classes so that the probabilities over the whole
#: domain sum to one, and a table printed to four decimals does so only to its
#: rounding: Annex A Table A.3 prints a day column that sums to 1,000 1 and a
#: 07:00 to 19:00 column that sums to 1,000 4. One per cent admits every
#: rounded table and still refuses probabilities given in per cent, or a set
#: of classes with some left out.
_PROBABILITY_SUM_TOLERANCE = 0.01

#: The views :meth:`SelDistribution.plot` draws.
_VIEWS = ("classes", "density", "exceedance")

#: The fewest classes a distribution can have: the outer boundaries of
#: Equations (12) and (13) are each read off the inner boundary next to them,
#: and a single class has none.
_MIN_CLASSES = 2

#: The longest run of equal levels Equation (11) leaves with a width for every
#: class, as long as it is not at an end of the list: a pair shares one
#: boundary at their common level and each keeps the half on its own side.
_EQUAL_PAIR = 2


def _real_array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """A non-empty array of finite real numbers, any shape.

    :raises ValueError: for a complex, non-numeric, empty or non-finite input.
    """
    if np.iscomplexobj(values):
        msg = f"'{name}' must be real, not complex."
        raise ValueError(msg)
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc
    if array.size == 0:
        msg = f"'{name}' must not be empty."
        raise ValueError(msg)
    if not np.all(np.isfinite(array)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    return array


def _probability_array(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """A non-empty array of finite, non-negative probabilities."""
    array = _real_array(values, name)
    if np.any(array < 0.0):
        msg = f"'{name}' must not contain a negative probability."
        raise ValueError(msg)
    return array


def _levels_and_probabilities(
    levels_db: ArrayLike, probabilities: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The replica levels and their probabilities, flattened in the same order.

    Both are read in row-major order, so a ``(N_atm, N_exc)`` pair of arrays
    lists the replica ``(k, l)`` at flat index ``k * N_exc + l``.

    :raises ValueError: if the two shapes differ, a probability is negative or
        the probabilities do not sum to one within
        :data:`_PROBABILITY_SUM_TOLERANCE`.
    """
    levels = _real_array(levels_db, "levels_db")
    probs = _probability_array(probabilities, "probabilities")
    if levels.shape != probs.shape:
        msg = (
            "'levels_db' and 'probabilities' must have the same shape, one "
            f"probability per replica atmosphere; got {levels.shape} and "
            f"{probs.shape}."
        )
        raise ValueError(msg)
    total = float(probs.sum())
    if abs(total - 1.0) > _PROBABILITY_SUM_TOLERANCE:
        msg = (
            "'probabilities' must sum to one over the replica atmospheres "
            f"(clause 4.2); they sum to {total:.6g}."
        )
        raise ValueError(msg)
    return levels.ravel(), probs.ravel()


def frequency_weighted_sel(
    band_levels_db: ArrayLike, weighting_db: ArrayLike
) -> float | NDArray[np.float64]:
    r"""Frequency-weighted sound exposure level from band levels (Equation (5)).

    .. math::

       L_{E,\mathrm{w}} = 10\lg\sum_{j=N_\mathrm{min}}^{N_\mathrm{max}}
       10^{0{,}1\left[L_E(j) + \mathrm{w}(j)\right]}~\text{dB}

    The standard prefers one-third-octave bands and requires every band from
    1 Hz (index 0) to 10 kHz (index 40) whose weighted level is within 20 dB of
    the largest weighted band level. Which bands those are depends on the
    spectrum, so the function sums every band it is given: passing the whole
    range from 1 Hz to 10 kHz always meets the requirement.

    :param band_levels_db: Band sound exposure levels :math:`L_E(j)`, in dB,
        along the last axis. Leading axes are kept, so an array of shape
        ``(N_atm, N_exc, n_bands)`` of the replica atmospheres returns their
        ``(N_atm, N_exc)`` weighted levels at once.
    :param weighting_db: The frequency weighting :math:`\mathrm{w}(j)` of each
        band, in dB (A-weighting, C-weighting or any other), broadcast against
        ``band_levels_db``.
    :return: :math:`L_{E,\mathrm{w}}` in dB, a float for a single spectrum.
    :raises ValueError: for an empty or non-finite input, or shapes that do
        not broadcast.
    """
    levels = _real_array(band_levels_db, "band_levels_db")
    weighting = _real_array(weighting_db, "weighting_db")
    try:
        weighted = levels + weighting
    except ValueError as exc:
        msg = (
            "'weighting_db' must broadcast against 'band_levels_db' along the "
            f"band axis; got {weighting.shape} and {levels.shape}."
        )
        raise ValueError(msg) from exc
    weighted = np.atleast_1d(weighted)
    # Summed relative to the largest band so a spectrum far above or below
    # 0 dB cannot overflow or underflow the powers of ten.
    peak = np.max(weighted, axis=-1, keepdims=True)
    total = np.squeeze(peak, axis=-1) + 10.0 * np.log10(
        np.sum(10.0 ** (0.1 * (weighted - peak)), axis=-1)
    )
    if np.ndim(total) == 0:
        return float(total)
    return total


def replica_probabilities(
    absorption_probabilities: ArrayLike, excess_attenuation_probabilities: ArrayLike
) -> NDArray[np.float64]:
    r"""Probability of occurrence of each replica atmosphere (Equation (14)).

    .. math::

       \wp_m = \wp_{\mathrm{atm},k}\,\wp_{\mathrm{exc},l}

    The two classifications are taken as independent (clause 4.5, NOTE 1 to
    Equation (6)), so the probability of the replica ``(k, l)`` is the product
    of the probability of its atmospheric-absorption class and that of its
    excess-attenuation class.

    :param absorption_probabilities: :math:`\wp_{\mathrm{atm},k}`, one per
        atmospheric-absorption class. Annex A uses a single class of
        probability 1.
    :param excess_attenuation_probabilities: :math:`\wp_{\mathrm{exc},l}`, one
        per excess-attenuation class.
    :return: An array of shape ``(N_atm, N_exc)``, row ``k`` and column ``l``,
        the shape :func:`sel_distribution` and :func:`long_term_sel` read
        ``levels_db`` in.
    :raises ValueError: for an empty, multi-dimensional, non-finite or
        negative input.
    """
    atm = _probability_array(absorption_probabilities, "absorption_probabilities")
    exc = _probability_array(
        excess_attenuation_probabilities, "excess_attenuation_probabilities"
    )
    for name, array in (
        ("absorption_probabilities", atm),
        ("excess_attenuation_probabilities", exc),
    ):
        if array.ndim > 1:
            msg = f"'{name}' must be one-dimensional, one value per class."
            raise ValueError(msg)
    return np.outer(np.atleast_1d(atm), np.atleast_1d(exc))


def long_term_sel(
    levels_db: ArrayLike,
    probabilities: ArrayLike,
    *,
    rating_adjustment_db: float = 0.0,
) -> float:
    r"""Long-term average single-event sound exposure level (Equations (7), (8)).

    .. math::

       \langle L_{E,\mathrm{w}}\rangle_\mathrm{LT} = 10\lg\left[
       \sum_{k=1}^{N_\mathrm{atm}}\sum_{l=1}^{N_\mathrm{exc}}
       \wp_{\mathrm{atm},k}\,\wp_{\mathrm{exc},l}\,
       10^{0{,}1 L_{E,\mathrm{w},k,l}}\right]~\text{dB}
       \tag{7}

    With the rating level adjustment ``K`` for highly impulsive sound of
    ISO 1996-1 inside the sum, the same expression is the long-term average
    single-event sound exposure **rating** level
    :math:`\langle L_\mathrm{r}\rangle_\mathrm{LT}` of Equation (8), the
    quantity the standard offers to ISO 1996-1 as the frequency-weighted and
    adjusted single-event level. ``K`` is one constant for the source, so
    Equation (8) is Equation (7) plus ``K``.

    Annex A calls this value ``LT1`` and computes it with a single
    atmospheric-absorption class of probability 1.

    :param levels_db: :math:`L_{E,\mathrm{w},k,l}` of each replica atmosphere,
        in dB, any shape (``(N_atm, N_exc)`` or already flattened).
    :param probabilities: The probability of each replica, the same shape as
        ``levels_db`` (see :func:`replica_probabilities`).
    :param rating_adjustment_db: ``K``, in dB; 0 dB (the default) gives
        Equation (7).
    :return: The long-term average level, in dB.
    :raises ValueError: if the shapes differ, a probability is negative, the
        probabilities do not sum to one, every probability is zero, or a value
        is not finite.
    """
    levels, probs = _levels_and_probabilities(levels_db, probabilities)
    k_db = require_finite(rating_adjustment_db, "rating_adjustment_db")
    return _energy_mean_db(levels, probs) + k_db


def turbulence_level_shift(sigma_db: float) -> float:
    r"""Shift of the mean of each Gaussian subclass, :math:`\Delta\mu` (Equation (22)).

    The shift that keeps the energetically averaged level of a subclass at its
    centre once the subclass is spread by a normal distribution of standard
    deviation :math:`\sigma`. The integral of Equation (22) is the mean of a
    lognormal variable and has the closed form

    .. math::

       \Delta\mu = \frac{\sigma^{2}\ln 10}{20}~\text{dB},

    2,878 dB for the 5 dB the standard says is typically used.

    :param sigma_db: The standard deviation :math:`\sigma` of the turbulent
        spread, in dB.
    :return: :math:`\Delta\mu`, in dB.
    :raises ValueError: for a non-positive or non-finite ``sigma_db``.
    """
    sigma = require_positive(sigma_db, "sigma_db")
    return sigma * sigma * math.log(10.0) / 20.0


def _energy_mean_db(levels: NDArray[np.float64], weights: NDArray[np.float64]) -> float:
    """``10 lg sum(w 10^(0.1 L))``, summed relative to the largest level.

    :raises ValueError: when every weight is zero, which leaves no level to
        average.
    """
    if not np.any(weights > 0.0):
        msg = "'probabilities' must give at least one replica a non-zero probability."
        raise ValueError(msg)
    peak = float(np.max(levels[weights > 0.0]))
    return peak + 10.0 * math.log10(
        float(np.sum(weights * 10.0 ** (0.1 * (levels - peak))))
    )


def _merge_undefined_classes(
    levels: NDArray[np.float64],
    probs: NDArray[np.float64],
    members: list[tuple[int, ...]],
) -> tuple[NDArray[np.float64], NDArray[np.float64], list[tuple[int, ...]]]:
    """Combine each run of equal levels that would leave a class of no width.

    The input is sorted. A run of three or more equal levels leaves its inner
    classes with no width through Equation (11); a run of two at the first or
    last position leaves the end class with none through Equation (12) or (13).
    Either run is combined into one class carrying the sum of the
    probabilities, which is what clause 5 prescribes for the first case; a run
    of two anywhere else keeps its two classes, as Annex A keeps its pairs at
    30,8 dB and 31,8 dB.
    """
    distinct = np.diff(levels) > 0.0
    starts = np.concatenate(([0], np.flatnonzero(distinct) + 1))
    stops = np.concatenate((starts[1:], [levels.size]))
    out_levels: list[float] = []
    out_probs: list[float] = []
    out_members: list[tuple[int, ...]] = []
    last = levels.size
    for start, stop in zip(starts.tolist(), stops.tolist(), strict=True):
        run = stop - start
        at_end = start == 0 or stop == last
        if run > _EQUAL_PAIR or (run > 1 and at_end):
            out_levels.append(float(levels[start]))
            out_probs.append(float(np.sum(probs[start:stop])))
            out_members.append(tuple(i for group in members[start:stop] for i in group))
        else:
            for i in range(start, stop):
                out_levels.append(float(levels[i]))
                out_probs.append(float(probs[i]))
                out_members.append(members[i])
    return np.asarray(out_levels), np.asarray(out_probs), out_members


@dataclass(frozen=True)
class SelDistribution:
    r"""The statistical distribution of a single-event sound exposure level
    (ISO 13474:2009, clause 5).

    The replica atmospheres, sorted by level, are the ``M`` classes of
    Equations (10) to (16); each class is split into ``subclasses`` equal
    subclasses (Equations (17) to (20)) and each subclass is replaced by a
    normal distribution of standard deviation ``sigma_db`` centred
    ``level_shift_db`` below the subclass centre (Equations (21) to (23)).

    :ivar levels_db: :math:`L_{E,\mathrm{w},m}` of the ``M`` classes, in
        increasing order, in dB.
    :ivar probabilities: :math:`\wp_m` of each class (Equation (14)).
    :ivar lower_bounds_db: :math:`g_{\mathrm{L},m}`, in dB (Equations (11),
        (12)).
    :ivar upper_bounds_db: :math:`g_{\mathrm{U},m}`, in dB (Equations (11),
        (13)).
    :ivar class_densities_per_db: :math:`\rho_m`, the constant density of each
        class, in 1/dB (Equation (15)).
    :ivar subclass_centres_db: :math:`\mu_{m,j}`, shape ``(M, subclasses)``, in
        dB (Equation (18)).
    :ivar sigma_db: :math:`\sigma` of the turbulent spread, in dB.
    :ivar level_shift_db: :math:`\Delta\mu`, in dB (Equation (22)).
    :ivar subclasses: :math:`N_\mathrm{sub}`, the subclasses per class.
    :ivar long_term_level_db: :math:`\langle L_{E,\mathrm{w}}\rangle_\mathrm{LT}`
        from the classes, Equation (7); Annex A's ``LT1``.
    :ivar distribution_long_term_level_db: the same average taken over the
        continuous distribution, Equation (A.4); Annex A's ``LT2``. It differs
        from ``long_term_level_db`` only by the spreading of each class over its
        width, since :math:`\Delta\mu` preserves the energy of each subclass.
    :ivar replicas: For each class, the flat indices of the replica
        atmospheres it holds, in the row-major order the input was given in; a
        class holds more than one only where equal levels were combined.
    """

    levels_db: NDArray[np.float64]
    probabilities: NDArray[np.float64]
    lower_bounds_db: NDArray[np.float64]
    upper_bounds_db: NDArray[np.float64]
    class_densities_per_db: NDArray[np.float64]
    subclass_centres_db: NDArray[np.float64]
    sigma_db: float
    level_shift_db: float
    subclasses: int
    long_term_level_db: float
    distribution_long_term_level_db: float
    replicas: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        """Refuse a distribution whose columns disagree with each other.

        Every per-class column must hold the same ``M`` classes, at least two,
        the subclass centres one row of ``subclasses`` per class, and each
        class a positive width; the methods below read them together and a
        short column would shift every density by a class.

        :raises ValueError: if the columns disagree, a class has no width, or a
            value is not finite.
        """
        per_class = (
            "levels_db",
            "probabilities",
            "lower_bounds_db",
            "upper_bounds_db",
            "class_densities_per_db",
        )
        sizes = {name: np.shape(getattr(self, name)) for name in per_class}
        count = np.size(self.levels_db)
        if count < _MIN_CLASSES or any(shape != (count,) for shape in sizes.values()):
            msg = (
                "SelDistribution: the per-class columns must be 1-D arrays of "
                f"the same length, at least two classes; got {sizes}."
            )
            raise ValueError(msg)
        if np.shape(self.subclass_centres_db) != (count, self.subclasses):
            msg = (
                "SelDistribution: 'subclass_centres_db' must have one row of "
                f"'subclasses' ({self.subclasses}) centres per class; got "
                f"{np.shape(self.subclass_centres_db)}."
            )
            raise ValueError(msg)
        if len(self.replicas) != count:
            msg = "SelDistribution: 'replicas' must name the replicas of every class."
            raise ValueError(msg)
        for name in (*per_class, "subclass_centres_db"):
            if not np.all(np.isfinite(getattr(self, name))):
                msg = f"SelDistribution: '{name}' must contain only finite values."
                raise ValueError(msg)
        if not np.all(self.upper_bounds_db > self.lower_bounds_db):
            msg = "SelDistribution: every class must have a positive width."
            raise ValueError(msg)
        require_positive(self.sigma_db, "sigma_db")

    def class_density(self, x_db: ArrayLike) -> float | NDArray[np.float64]:
        r"""The class density :math:`\rho(x)` before the turbulent spread
        (Equations (15), (16)), in 1/dB.

        A step function, constant inside each class and zero outside the
        classes; at a boundary itself, where Equation (15) defines neither
        neighbour, it is zero.

        :param x_db: Level or levels ``x``, in dB.
        :return: :math:`\rho(x)`, a float for a scalar ``x``.
        """
        x = np.asarray(x_db, dtype=np.float64)
        inside = (x[..., None] > self.lower_bounds_db) & (
            x[..., None] < self.upper_bounds_db
        )
        value = np.sum(np.where(inside, self.class_densities_per_db, 0.0), axis=-1)
        return float(value) if value.ndim == 0 else value

    def _spread(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        r"""Means and weights of the ``M * subclasses`` Gaussian subclasses.

        The weight of subclass ``{m, j}`` is :math:`b_m\rho_m = \wp_m/N_\mathrm{sub}`
        (Equation (21)) and its mean :math:`\mu_{m,j} - \Delta\mu`.
        """
        means = (self.subclass_centres_db - self.level_shift_db).ravel()
        weights = np.repeat(self.probabilities / self.subclasses, self.subclasses)
        return means, weights

    def density(self, x_db: ArrayLike) -> float | NDArray[np.float64]:
        r"""The continuous density :math:`\rho^{*}(x)` (Equations (21), (23)), in 1/dB.

        :param x_db: Level or levels ``x``, in dB.
        :return: :math:`\rho^{*}(x)`, a float for a scalar ``x``.
        """
        means, weights = self._spread()
        x = np.asarray(x_db, dtype=np.float64)
        z = (x[..., None] - means) / self.sigma_db
        value = np.sum(weights * np.exp(-0.5 * z * z), axis=-1) / (
            self.sigma_db * math.sqrt(2.0 * math.pi)
        )
        return float(value) if value.ndim == 0 else value

    def exceedance(self, x_db: ArrayLike) -> float | NDArray[np.float64]:
        r"""Probability that the level exceeds ``x`` (Equation (24)).

        .. math::

           \mathrm{P_r}(L_{E,\mathrm{w}} > x) = \int_x^{\infty}
           \rho^{*}(x')\,\mathrm{d}x'

        evaluated exactly as a sum of Gaussian upper-tail probabilities. It
        tends to the sum of the probabilities of the classes, one, as ``x``
        falls.

        :param x_db: Level or levels ``x``, in dB.
        :return: The probability, a float for a scalar ``x``.
        """
        from scipy.special import ndtr

        means, weights = self._spread()
        x = np.asarray(x_db, dtype=np.float64)
        value = np.sum(weights * ndtr((means - x[..., None]) / self.sigma_db), axis=-1)
        return float(value) if value.ndim == 0 else value

    def exceedance_level(self, percent: ArrayLike) -> float | NDArray[np.float64]:
        r"""The ``n``-percent exceedance level :math:`L_{E,\mathrm{w},n}` (Equation (25)).

        The level exceeded with probability ``n / 100``: the root of
        :math:`\mathrm{P_r}(L_{E,\mathrm{w}} > x) = n/100`, found to 10⁻¹⁰ dB.
        ``exceedance_level(95)`` is the level exceeded by 95 % of the events,
        the lowest of the usual set; ``exceedance_level(1)`` the highest.

        :param percent: ``n``, in per cent, strictly between 0 and 100 times the
            total probability of the classes.
        :return: The level, in dB, a float for a scalar ``percent``.
        :raises ValueError: for a percentage outside that range.
        """
        from scipy.optimize import brentq

        n = np.asarray(percent, dtype=np.float64)
        total = float(np.sum(self.probabilities))
        target = n / 100.0
        if (
            not np.all(np.isfinite(target))
            or np.any(target <= 0.0)
            or np.any(target >= total)
        ):
            msg = (
                "'percent' must lie strictly between 0 and "
                f"{100.0 * total:.6g}, the total probability of the classes in "
                "per cent."
            )
            raise ValueError(msg)
        # The exceedance is strictly decreasing and every Gaussian lies within
        # 40 standard deviations of these two ends to far below 1e-300, so the
        # root is bracketed for any target the check above lets through.
        lo = float(np.min(self.lower_bounds_db)) - self.level_shift_db
        hi = float(np.max(self.upper_bounds_db))
        lo -= 40.0 * self.sigma_db
        hi += 40.0 * self.sigma_db

        def solve(p: float) -> float:
            return float(
                brentq(
                    lambda x: float(self.exceedance(x)) - p,
                    lo,
                    hi,
                    xtol=1e-10,
                    rtol=4.0 * np.finfo(float).eps,
                )
            )

        flat = np.array([solve(float(p)) for p in np.ravel(target)])
        if n.ndim == 0:
            return float(flat[0])
        return flat.reshape(n.shape)

    def plot(
        self,
        ax: Axes | None = None,
        *,
        view: str = "density",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot the distribution, as its class density, density or exceedance.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param view: ``"density"`` (default) draws the continuous density
            :math:`\rho^{*}(x)` with the long-term level of Equation (A.4)
            marked, the curve of Annex A Figure A.2; ``"classes"`` draws the
            step density :math:`\rho(x)` of the classes before the turbulent
            spread, Figure A.1; ``"exceedance"`` draws
            :math:`\mathrm{P_r}(L_{E,\mathrm{w}} > x)` with the 95, 50, 10, 5 and
            1 per cent exceedance levels marked, Figure A.3.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the primary artist.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        :raises ValueError: If ``view`` is not one of the three names above.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_sel_distribution

        if view not in _VIEWS:
            msg = f"Unknown view {view!r}; use one of {_VIEWS}."
            raise ValueError(msg)
        return plot_sel_distribution(
            self, ax=ax, view=view, language=check_language(language), **kwargs
        )


def sel_distribution(
    levels_db: ArrayLike,
    probabilities: ArrayLike,
    *,
    sigma_db: float = _TYPICAL_SIGMA_DB,
    subclasses: int = _ANNEX_A_SUBCLASSES,
) -> SelDistribution:
    r"""Statistical distribution of the single-event sound exposure level
    (ISO 13474:2009, clause 5).

    The levels of the replica atmospheres are placed in increasing order
    (Equation (10)); boundaries between consecutive classes lie half-way
    between their levels (Equation (11)) and the two outer boundaries mirror
    the nearest inner one about the end level (Equations (12), (13)); each
    class has the constant density :math:`\rho_m = \wp_m/(g_{\mathrm{U},m} -
    g_{\mathrm{L},m})` (Equation (15)). Each class is then divided into
    ``subclasses`` equal subclasses of width :math:`b_m` centred at
    :math:`\mu_{m,j} = g_{\mathrm{L},m} + (j - \tfrac12)b_m` (Equations (17),
    (18)), and each subclass is replaced by a normal distribution of standard
    deviation ``sigma_db`` and weight :math:`b_m\rho_m`, centred at
    :math:`\mu_{m,j} - \Delta\mu` (Equations (21) to (23)).

    Equal levels keep their own classes unless that leaves a class of no
    width, in which case the run is combined (see the module documentation).

    :param levels_db: :math:`L_{E,\mathrm{w},k,l}` of each replica atmosphere,
        in dB, any shape; a ``(N_atm, N_exc)`` array is read row by row.
    :param probabilities: The probability of occurrence of each replica, the
        same shape as ``levels_db``, summing to one (see
        :func:`replica_probabilities`).
    :param sigma_db: Standard deviation of the spread due to turbulence, in dB;
        5 dB by default, the value clause 5 says is typically used.
    :param subclasses: :math:`N_\mathrm{sub}`, the subclasses per class; 10 by
        default, the number Annex A uses. The standard fixes none.
    :return: The distribution.
    :raises ValueError: if the shapes differ, a value is not finite, a
        probability is negative, the probabilities do not sum to one, every
        probability is zero, fewer than two distinct levels remain once equal
        levels are combined, ``sigma_db`` is not positive, or ``subclasses``
        is not a whole number of at least one.
    """
    levels, probs = _levels_and_probabilities(levels_db, probabilities)
    sigma = require_positive(sigma_db, "sigma_db")
    n_sub = require_count(subclasses, "subclasses")
    lt1 = _energy_mean_db(levels, probs)

    order = np.argsort(levels, kind="stable")
    sorted_levels, sorted_probs, members = _merge_undefined_classes(
        levels[order], probs[order], [(int(i),) for i in order]
    )
    count = sorted_levels.size
    if count < _MIN_CLASSES:
        msg = (
            "'levels_db' must hold at least two distinct levels: with one, the "
            "outer boundaries of Equations (12) and (13) are not defined."
        )
        raise ValueError(msg)

    inner = 0.5 * (sorted_levels[:-1] + sorted_levels[1:])
    lower = np.concatenate(([2.0 * sorted_levels[0] - inner[0]], inner))
    upper = np.concatenate((inner, [2.0 * sorted_levels[-1] - inner[-1]]))
    width = upper - lower
    densities = sorted_probs / width
    step = width / n_sub
    centres = lower[:, None] + (np.arange(1, n_sub + 1) - 0.5)[None, :] * step[:, None]

    shift = turbulence_level_shift(sigma)
    # Equation (A.4) in closed form: each Gaussian of weight w and mean
    # mu - shift contributes w 10^(0.1 (mu - shift)) 10^(0.1 * Eq. (22)), and
    # the Eq. (22) factor is the shift itself, so the two cancel.
    weights = np.repeat(sorted_probs / n_sub, n_sub)
    lt2 = _energy_mean_db(centres.ravel(), weights)

    return SelDistribution(
        levels_db=read_only(sorted_levels),
        probabilities=read_only(sorted_probs),
        lower_bounds_db=read_only(lower),
        upper_bounds_db=read_only(upper),
        class_densities_per_db=read_only(densities),
        subclass_centres_db=read_only(centres),
        sigma_db=sigma,
        level_shift_db=shift,
        subclasses=n_sub,
        long_term_level_db=lt1,
        distribution_long_term_level_db=lt2,
        replicas=tuple(members),
    )

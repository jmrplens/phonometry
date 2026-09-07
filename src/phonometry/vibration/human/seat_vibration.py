#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a seat does to the vibration under it (ISO 10326-1:2016).

A driver does not sit on the floor of the machine. The seat is between them,
and whether it helps is not obvious: a suspension seat can amplify what it was
bought to attenuate, if the excitation happens to sit near its resonance. This
standard is the laboratory method that answers the question with one number.

**The SEAT factor** (10.2.2) is that number. Drive a vibration simulator with
the input spectrum the application standard prescribes, measure the
frequency-weighted r.m.s. acceleration at the seat and at the platform, and
divide:

.. math::

   \mathrm{SEAT} = \frac{a_\mathrm{wS}}{a_\mathrm{wP}} \tag{2}

Below 1 the seat is doing its job; at 1 it is a rigid plank; above 1 it is
making the ride worse. Both accelerations are the arithmetic mean of **three
consecutive runs agreeing within ± 5 %** (10.2.1), which is what
:func:`mean_of_test_runs` enforces, because a mean of runs that disagree by
more than that is not a measurement this standard recognises.

**Correcting to an intended input** (10.2.3). A simulator does not reproduce
its target spectrum exactly, so the magnitude measured on the seat is scaled
by the ratio between the input actually delivered and the input intended:

.. math::

   a^{*}_\mathrm{wS} = \frac{a_\mathrm{wS}\, a^{*}_\mathrm{wP}}{a_\mathrm{wP}}
   = \mathrm{SEAT} \cdot a^{*}_\mathrm{wP} \tag{3, 4}

The printed Formula (3) asterisks all four symbols and so reduces to
:math:`a^{*}_\mathrm{wS} = a^{*}_\mathrm{wS}`; the reading above is the one
its own prose, and Formula (4) beside it, require. See ``docs/ERRATA.md``.

**The damping test** (10.3) is the other half. Load the seat with an inert
mass of 75 kg ± 1 %, drive the base at the suspension's resonance frequency,
and take the ratio there:

.. math::

   T = \frac{a_\mathrm{S}(f_\mathrm{r})}{a_\mathrm{P}(f_\mathrm{r})} \tag{5}

The arithmetic is the SEAT arithmetic, and the meaning is not: SEAT is a
whole-spectrum verdict on a seat in service, and :math:`T` is what the seat
does at the one frequency where it does the most. Clause 11 makes them the two
acceptance values a specific application standard may set, and this standard
sets neither: it fixes the method and leaves the numbers to whoever writes for
the machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.validation import require_positive

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

#: Clause 10.2.1 and 10.3: the three consecutive runs of a test have to agree
#: within this fraction of their arithmetic mean, and that mean is the
#: measurement.
RUN_AGREEMENT_TOLERANCE: float = 0.05

#: Clause 10.2.1 and 10.3: how many consecutive runs a test is made of.
TEST_RUNS: int = 3

#: A spread needs two readings to exist at all, which is the floor below the
#: three runs the standard asks for.
_MINIMUM_RUNS = 2

#: The band is "within ± 5 %", so a reading placed exactly on it is inside it.
#: A run written as ``1.05`` against a mean of 1 lands 5,000000000000004 %
#: away once the two are floats, and refusing that would be refusing the
#: standard's own edge on a representation error rather than on a spread.
_EDGE_SLACK = 1e-12

#: Clause 10.3: the inert mass the seat carries for the damping test, in
#: kilograms, and the tolerance on it.
DAMPING_TEST_MASS_KG: float = 75.0
DAMPING_TEST_MASS_TOLERANCE: float = 0.01

#: Clause 9.5.1: for a suspension with active damping the damping test may not
#: suit, and a reduced mass has been found appropriate, in kilograms.
ACTIVE_DAMPING_TEST_MASS_KG: float = 60.0

#: The value of a SEAT factor or a transmissibility at which the seat passes
#: the vibration through unchanged. It is not an acceptance value: Clause 11
#: leaves those to the application standard.
UNITY_TRANSMISSION: float = 1.0


def mean_of_test_runs(
    values: ArrayLike, *, tolerance: float = RUN_AGREEMENT_TOLERANCE
) -> float:
    """The arithmetic mean of the runs of one test (10.2.1, 10.3).

    The standard asks for three consecutive runs whose values lie within
    ± 5 % of their arithmetic mean, and records that mean. A set that does not
    meet the spread is not a result to be averaged anyway, so it is refused
    here rather than quietly returned.

    :param values: The r.m.s. accelerations of the runs, in any consistent
        unit. Three of them, as the standard asks; a different count is
        accepted, since the run-in and warm-up notes in 10.2.1 leave room for
        discarding a reading.
    :param tolerance: The permitted spread as a fraction of the mean;
        :data:`RUN_AGREEMENT_TOLERANCE` by default.
    :return: The arithmetic mean, in the unit the values were given in.
    :raises ValueError: If fewer than two values are given, if any is not
        positive and finite, if the tolerance is not positive, or if any value
        lies outside the tolerance band around the mean.
    """
    tol = require_positive(tolerance, "tolerance")
    runs = np.atleast_1d(np.asarray(values, dtype=np.float64))
    if runs.size < _MINIMUM_RUNS:
        msg = "'values' needs at least two runs to have a spread."
        raise ValueError(msg)
    if np.any(runs <= 0.0) or not np.all(np.isfinite(runs)):
        msg = "'values' must be positive and finite."
        raise ValueError(msg)
    mean = float(runs.mean())
    spread = float(np.max(np.abs(runs - mean)) / mean)
    if spread > tol * (1.0 + _EDGE_SLACK):
        msg = (
            f"The runs differ from their mean by {100.0 * spread:.1f} %, more "
            f"than the {100.0 * tol:.0f} % this test allows."
        )
        raise ValueError(msg)
    return mean


def seat_factor(seat_acceleration: float, platform_acceleration: float) -> float:
    r"""The SEAT factor of Formula (2), dimensionless.

    :param seat_acceleration: The frequency-weighted r.m.s. acceleration
        measured at the seat, :math:`a_\mathrm{wS}`, in metres per second
        squared.
    :param platform_acceleration: The same quantity at the platform,
        :math:`a_\mathrm{wP}`.
    :return: :math:`a_\mathrm{wS}/a_\mathrm{wP}`; below 1 the seat attenuates.
    :raises ValueError: If either acceleration is not positive and finite.
    """
    seat = require_positive(seat_acceleration, "seat_acceleration")
    platform = require_positive(platform_acceleration, "platform_acceleration")
    return seat / platform


def corrected_seat_acceleration(
    seat_acceleration: float,
    platform_acceleration: float,
    intended_platform_acceleration: float,
) -> float:
    r"""The seat magnitude corrected to the intended input (10.2.3).

    :math:`a^{*}_\mathrm{wS} = a_\mathrm{wS}\,a^{*}_\mathrm{wP}/a_\mathrm{wP}`,
    which is Formula (4) with the SEAT factor substituted, and what the prose
    of 10.2.3 asks for. The printed Formula (3) carries an asterisk on every
    symbol and reduces to an identity; ``docs/ERRATA.md`` records it.

    :param seat_acceleration: The magnitude measured at the seat,
        :math:`a_\mathrm{wS}`.
    :param platform_acceleration: The input actually delivered,
        :math:`a_\mathrm{wP}`.
    :param intended_platform_acceleration: The input the test intended,
        :math:`a^{*}_\mathrm{wP}`.
    :return: The corrected magnitude on the seat, in the unit the
        accelerations were given in.
    :raises ValueError: If any acceleration is not positive and finite.
    """
    intended = require_positive(
        intended_platform_acceleration, "intended_platform_acceleration"
    )
    return seat_factor(seat_acceleration, platform_acceleration) * intended


def resonance_transmissibility(
    seat_acceleration: float, platform_acceleration: float
) -> float:
    r"""The transmissibility at resonance of Formula (5), dimensionless.

    The damping test drives the base at the suspension's resonance frequency
    :math:`f_\mathrm{r}` with the seat carrying an inert
    :data:`DAMPING_TEST_MASS_KG`, and this is the ratio there. The arithmetic
    matches :func:`seat_factor` and the meaning does not: this is the one
    frequency the seat treats worst, not a verdict over a spectrum, and
    Clause 11 makes it the acceptance value of a different test.

    :param seat_acceleration: :math:`a_\mathrm{S}(f_\mathrm{r})`, measured at
        the disc on the seat.
    :param platform_acceleration: :math:`a_\mathrm{P}(f_\mathrm{r})`, measured
        on the platform.
    :return: :math:`a_\mathrm{S}(f_\mathrm{r})/a_\mathrm{P}(f_\mathrm{r})`.
    :raises ValueError: If either acceleration is not positive and finite.
    """
    seat = require_positive(seat_acceleration, "seat_acceleration")
    platform = require_positive(platform_acceleration, "platform_acceleration")
    return seat / platform


@dataclass(frozen=True)
class SeatTransmissionResult:
    r"""One simulated input vibration test, as the standard records it.

    :ivar seat_acceleration: The mean of the seat runs,
        :math:`a_\mathrm{wS}`, in metres per second squared.
    :ivar platform_acceleration: The mean of the platform runs,
        :math:`a_\mathrm{wP}`.
    :ivar seat_runs: The individual seat readings the mean came from.
    :ivar platform_runs: The individual platform readings.
    """

    seat_acceleration: float
    platform_acceleration: float
    seat_runs: tuple[float, ...]
    platform_runs: tuple[float, ...]

    @property
    def seat_factor(self) -> float:
        """The SEAT factor of Formula (2)."""
        return seat_factor(self.seat_acceleration, self.platform_acceleration)

    @property
    def attenuates(self) -> bool:
        """Whether the seat passes less vibration than it receives.

        True is the whole of what it means: a SEAT factor below 1. It is not
        an acceptance, because Clause 11 leaves acceptance values to the
        application standard written for the machine.
        """
        return bool(self.seat_factor < UNITY_TRANSMISSION)

    def corrected_acceleration(self, intended_platform_acceleration: float) -> float:
        """The seat magnitude corrected to an intended input (10.2.3).

        :param intended_platform_acceleration: The input the test intended,
            in the unit the runs were given in.
        :return: The corrected magnitude on the seat.
        :raises ValueError: If the intended input is not positive and finite.
        """
        return corrected_seat_acceleration(
            self.seat_acceleration,
            self.platform_acceleration,
            intended_platform_acceleration,
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the runs, their means and the SEAT factor between them.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.vibration.plot_seat_transmission`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_seat_transmission

        check_language(language)
        return plot_seat_transmission(self, ax=ax, language=language, **kwargs)


def seat_transmission(
    seat_runs: ArrayLike,
    platform_runs: ArrayLike,
    *,
    tolerance: float = RUN_AGREEMENT_TOLERANCE,
) -> SeatTransmissionResult:
    """One simulated input vibration test, from its runs (10.2).

    Each set of runs is averaged through :func:`mean_of_test_runs`, so a test
    whose runs do not agree within ± 5 % is refused rather than averaged.

    :param seat_runs: The frequency-weighted r.m.s. accelerations measured at
        the seat, one per run, in metres per second squared.
    :param platform_runs: The same at the platform, one per run.
    :param tolerance: The permitted spread of each set, as a fraction of its
        mean.
    :return: The test, as a :class:`SeatTransmissionResult`.
    :raises ValueError: For anything :func:`mean_of_test_runs` refuses, or if
        the two sets do not hold the same number of runs.
    """
    seat = np.atleast_1d(np.asarray(seat_runs, dtype=np.float64))
    platform = np.atleast_1d(np.asarray(platform_runs, dtype=np.float64))
    if seat.size != platform.size:
        msg = (
            "The seat and the platform are measured in the same runs; got "
            f"{seat.size} and {platform.size}."
        )
        raise ValueError(msg)
    return SeatTransmissionResult(
        seat_acceleration=mean_of_test_runs(seat, tolerance=tolerance),
        platform_acceleration=mean_of_test_runs(platform, tolerance=tolerance),
        seat_runs=tuple(float(v) for v in seat),
        platform_runs=tuple(float(v) for v in platform),
    )

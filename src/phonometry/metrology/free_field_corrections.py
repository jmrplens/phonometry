#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Corrections that bring a sound level meter to its free-field response
(IEC 62585:2012).

A periodic test of a sound level meter by IEC 61672-3 drives its microphone
with a sound calibrator, a comparison coupler or an electrostatic actuator,
none of which is the plane progressive wave the meter is specified for. The
test needs, at each frequency, the correction that turns what the meter
indicates on that source into what it would indicate in a free field of the
same sound pressure level, and the manufacturer has to state it. IEC 62585
gives the methods for finding those corrections and the uncertainty they may
carry.

**The adjustment value, Annex A.** The manufacturer adjusts the meter's
sensitivity to minimise the averaged deviation of its free-field response from
the incident level over the whole frequency range, then applies the
recommended calibrator and reads :math:`L_4`. The adjustment value quoted in
the manual is :math:`\Delta L = L_1 - L_4`, :math:`L_1` being the level stated
for the calibrator. :func:`adjustment_value` makes the fit and returns an
:class:`AdjustmentValue`.

**The corrections, Annexes D, E and F.** Each compares the meter with a
laboratory standard microphone of type LS2P, in a free field and on the
source, and adds the free-field correction of that microphone, which comes
from IEC/TS 61094-7 and is an input here:

.. math::

   C_\mathrm{FF,SLM} = (L_\mathrm{ind1} - L_\mathrm{ind3})
   - (L_\mathrm{ind2} - L_\mathrm{ind4}) - (L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}})
   + (L_{p,\mathrm{P1}} - L_{p,\mathrm{P2}}) + C_\mathrm{FF,RM}
   \tag{D.7}

for a multi-frequency sound calibrator (:func:`sound_calibrator_correction`),
Formula (E.6) for a comparison coupler (:func:`comparison_coupler_correction`),
and Formula (F.13), normalised to the calibration check frequency, for an
electrostatic actuator (:func:`electrostatic_actuator_correction`). All three
return a :class:`FreeFieldCorrection`, which averages the determinations of
the combinations clause 7 asks for and keeps their range.

**The uncertainty, Annex I and clauses 9 to 14.**
:func:`correction_uncertainty_budget` builds the budget of Table I.1 on
:func:`~phonometry.metrology.combine_uncertainty`: its 15 components, each
divided by the divisor its distribution sets, and the effective degrees of
freedom by Welch-Satterthwaite, which choose the coverage factor for a level of
confidence of 95 %. :func:`verify_correction_uncertainty` judges the expanded
uncertainty at each frequency against the maximum permitted by the clause the
correction belongs to, :func:`maximum_expanded_uncertainty`, and for clauses
12 to 14 the range of the corrections over the microphones against the same
maximum.

**The exact frequencies, Annex H.** The corrections are reported at exact
base-ten frequencies, :func:`exact_frequencies`.

Three readings the text leaves to the implementer
-------------------------------------------------

**The fit of Annex A.** The text asks for the sensitivity that minimises "the
averaged deviation" of the free-field response, with the tolerance limits of
IEC 61672-1, which vary with frequency, "taken into account", and prints no
formula. :func:`adjustment_value` takes the least-squares reading: the
sensitivity adjustment :math:`s` minimises :math:`\sum_i w_i (d_i + s)^2`,
:math:`d_i` the deviation at frequency :math:`i` and :math:`w_i = 1/t_i^2`
for a tolerance :math:`t_i`, so a frequency with a tight tolerance pulls the
fit harder than one with a loose one, and a frequency without a tolerance
(:math:`t_i = \infty`) does not pull it at all. Without tolerances every
frequency weighs the same and :math:`s` is minus the mean deviation.

**The labels of Annex E.** Figure E.1, the list of symbols under (E.6) and the
descriptors a3 and a4 of Table I.1 all define :math:`L_\mathrm{ind3a}` as the
reading of the reference microphone in the coupler and :math:`L_\mathrm{ind3b}`
as that of the meter, with :math:`L_{p,\mathrm{P1}}` at the reference and
:math:`L_{p,\mathrm{P2}}` at the meter. Equations (E.4) to (E.6) are written
the other way round, as (D.5) to (D.7) are for a calibrator, and with the
figure's definitions they do not follow from (E.1) to (E.3B): they come out
:math:`2(\Delta L_\mathrm{P,SLM} - \Delta L_\mathrm{P,RM})` away from the
correction. :func:`comparison_coupler_correction` names its inputs by what
each reading is of, so neither labelling reaches it, and the defect is in
``docs/ERRATA.md``.

**The coverage factor of Table I.2.** The budget at 1 kHz reproduces the
printed combined standard uncertainty, 0,0590 dB, and effective degrees of
freedom, 29,98, but prints :math:`k = 2{,}11`, the Student factor for about 17
degrees of freedom. For 29,98 it is 2,04, and the expanded uncertainty
0,120 dB rather than the 0,124 dB the table prints to its guard digit. The
budget here gives 2,04, and the defect is in ``docs/ERRATA.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import (
    check_engine,
    require_count,
    require_finite,
    require_finite_array,
    require_positive,
    require_positive_array,
)
from .uncertainty import (
    Quantity,
    UncertaintyResult,
    combine_uncertainty,
    coverage_factor,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from .._report.metadata import ReportMetadata

__all__ = [
    "IEC62585_TABLE_I1",
    "AdjustmentValue",
    "CorrectionUncertaintyBudget",
    "CorrectionUncertaintyVerification",
    "FreeFieldCorrection",
    "UncertaintyComponentRow",
    "adjustment_value",
    "comparison_coupler_correction",
    "correction_uncertainty_budget",
    "electrostatic_actuator_correction",
    "exact_frequencies",
    "maximum_expanded_uncertainty",
    "sound_calibrator_correction",
    "verify_correction_uncertainty",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Formula (H.1): the reference frequency :math:`f_\mathrm{r}` of 1000 Hz.
_REFERENCE_FREQUENCY_HZ = 1000.0

#: The calibration check frequency IEC 61672-1 names for most meters, and the
#: normalisation frequency :math:`f_0` of Annex F by default.
_CHECK_FREQUENCY_HZ = 1000.0

#: How far a frequency may sit from a frequency the text names (the check
#: frequency, or a boundary such as "4 kHz") and still be read as it. An exact
#: base-ten frequency is within 1 % of its nominal value (15 849 Hz against
#: 16 kHz), and adjacent one-twelfth-octave frequencies are 6 % apart.
_NOMINAL_TOLERANCE = 0.02

#: How far an exact frequency of Formula (H.1) may sit outside the range asked
#: of :func:`exact_frequencies`, relative, and still be in it: the rounding of
#: the power of ten, not a nominal-to-exact allowance.
_RANGE_TOLERANCE = 1e-9

#: Clause 6: below this static pressure, in kPa, an additional component
#: enters the budget.
_LOW_STATIC_PRESSURE_KPA = 97.0

#: Clause 6: the range of static pressure measurements are made in, in kPa.
_STATIC_PRESSURE_RANGE_KPA = (80.0, 105.0)

#: Clause 6: the expanded uncertainty (k = 2) of that component when no
#: specific data are available, in dB: 0,15 dB up to and including 3 kHz and
#: 0,25 dB above, as ``(upper frequency in Hz, value)``.
_STATIC_PRESSURE_EXPANDED_DB = ((3000.0, 0.15), (math.inf, 0.25))

#: The coverage factor that clause 6 component is stated with.
_STATIC_PRESSURE_COVERAGE_FACTOR = 2.0

#: The descriptor the static-pressure component takes in a budget.
_STATIC_PRESSURE = "static pressure"

#: The sources Annexes D, E and F compare the meter on, with the formula and
#: the clause each belongs to.
_SOURCES: Mapping[str, tuple[str, int]] = MappingProxyType(
    {
        "sound_calibrator": ("D.7", 12),
        "comparison_coupler": ("E.6", 13),
        "electrostatic_actuator": ("F.13", 14),
    }
)

#: Readings of several determinations are a matrix: one row each, one column
#: per frequency.
_MATRIX_RANK = 2


@dataclass(frozen=True)
class UncertaintyComponentRow:
    r"""One row of IEC 62585:2012 Table I.1, the likely components of the
    uncertainty of a correction measured with a comparison coupler (Annex E).

    :ivar symbol: The symbol or name the table prints, such as
        ``"L_ind1"`` or ``"Gain of SLM"``.
    :ivar description: The description and source of the component.
    :ivar distribution: ``"rectangular"`` or ``"normal"``.
    :ivar divisor: What turns the value the budget states into a standard
        uncertainty: :math:`\sqrt{3}` for a rectangular half-width, 2 for a
        normal expanded uncertainty with :math:`k = 2`, 1 for a normal
        standard uncertainty from a statistical evaluation.
    """

    symbol: str
    description: str
    distribution: str
    divisor: float


_SQRT3 = math.sqrt(3.0)


def _row(
    symbol: str, description: str, divisor: float = _SQRT3
) -> UncertaintyComponentRow:
    distribution = "rectangular" if math.isclose(divisor, _SQRT3) else "normal"
    return UncertaintyComponentRow(
        symbol=symbol,
        description=description,
        distribution=distribution,
        divisor=divisor,
    )


#: IEC 62585:2012 Table I.1, "Description of likely uncertainty components",
#: keyed by the descriptor ``"a1"`` to ``"a15"`` the table prints, in its
#: order. Tables I.2 and I.3 fill in the values at 1 kHz and 8 kHz.
IEC62585_TABLE_I1: Mapping[str, UncertaintyComponentRow] = MappingProxyType(
    {
        "a1": _row("L_ind1", "Level measurement: sound level meter in free-field"),
        "a2": _row("L_ind2", "Level measurement: reference microphone in free-field"),
        "a3": _row(
            "L_ind3a",
            "Level measurement: reference microphone in comparison coupler",
        ),
        "a4": _row(
            "L_ind3b", "Level measurement: sound level meter in comparison coupler"
        ),
        "a5": _row(
            "L_p,F1 - L_p,F2",
            "(Uncorrected) drift in level of SPL in free-field between measurements "
            "with sound level meter and reference microphone",
        ),
        "a6": _row(
            "L_p,P1 - L_p,P2",
            "Difference in sound pressure level at sound level meter and reference "
            "microphone in comparison coupler",
        ),
        "a7": _row(
            "C_FF,RM",
            "Free-field correction of reference microphone from IEC/TS 61094-7",
            2.0,
        ),
        "a8": _row(
            "Gain of SLM",
            "Maximum drift in gain of sound level meter during measurements",
        ),
        "a9": _row(
            "Gain of RM channel",
            "Maximum drift in gain of reference microphone channel during measurements",
        ),
        "a10": _row(
            "Source to microphone distance",
            "Resetting distance from sound source to reference microphone or sound "
            "level meter",
        ),
        "a11": _row(
            "Free-progressive sound wave",
            "Due to reflections and non-uniform wave front",
        ),
        "a12": _row("SLM and RM mountings", "Due to reflection from mountings"),
        "a13": _row(
            "Microphone diameters",
            "Ratio of reference microphone and sound level meter microphone diameters",
        ),
        "a14": _row("Rounding", "Rounding of final result"),
        "a15": _row(
            "Repeatability", "Repeat measurements with combinations stated", 1.0
        ),
    }
)

#: The component whose standard uncertainty comes from a statistical
#: evaluation, and so carries finite degrees of freedom.
_REPEATABILITY = "a15"

#: The sign each component of Table I.1 carries in Formula (E.6), read with
#: the definitions of Figure E.1: the readings of the meter with a plus in the
#: free field and a minus in the coupler, those of the reference the other way
#: round, the two level differences as Table I.1 writes them with a minus, and
#: every other component as an additive correction. Only the magnitude, 1,
#: reaches the combined uncertainty of uncorrelated components.
_E6_SIGNS: Mapping[str, float] = MappingProxyType(
    {
        "a1": 1.0,
        "a2": -1.0,
        "a3": 1.0,
        "a4": -1.0,
        "a5": -1.0,
        "a6": -1.0,
        **{f"a{index}": 1.0 for index in range(7, 16)},
    }
)

# The maximum permitted expanded uncertainties of clauses 9 to 14, in dB, as
# ``(boundary in Hz, whether the boundary belongs to the band below, value)``,
# band after band upwards; the last band has no upper boundary. "Up to and
# including 4 kHz" keeps 4 kHz in the band below; "up to 10 kHz, and 0,50 dB at
# and above 10 kHz" puts 10 kHz in the band above.
_UP_TO_4K_INCLUSIVE = (4000.0, True)
_MAXIMUM_UNCERTAINTY_DB: Mapping[int, tuple[tuple[float, bool, float], ...]] = (
    MappingProxyType(
        {
            9: ((*_UP_TO_4K_INCLUSIVE, 0.25), (math.inf, True, 0.35)),
            10: (
                (*_UP_TO_4K_INCLUSIVE, 0.25),
                (8000.0, True, 0.35),
                (math.inf, True, 0.45),
            ),
            11: ((*_UP_TO_4K_INCLUSIVE, 0.20), (math.inf, True, 0.30)),
            **dict.fromkeys(
                (12, 13, 14),
                (
                    (*_UP_TO_4K_INCLUSIVE, 0.25),
                    (10000.0, False, 0.35),
                    (math.inf, True, 0.50),
                ),
            ),
        }
    )
)

#: The clause of the microphone's own response, which gives its maximum "from
#: 63 Hz", the lowest octave its measurements are made at.
_MICROPHONE_CLAUSE = 10
_CLAUSE10_LOWEST_HZ = 63.0

#: What each clause corrects for, in the words of its title.
_CLAUSE_SUBJECTS: Mapping[int, str] = MappingProxyType(
    {
        9: "reflections from the case and diffraction around the microphone",
        10: "deviation of the microphone from a uniform frequency response",
        11: "windscreens and similar accessories",
        12: "a sound calibrator",
        13: "a comparison coupler",
        14: "an electrostatic actuator",
    }
)

#: The clauses whose sources are judged on the range of their corrections over
#: the microphones as well: clauses 12, 13 and 14.
_RANGE_CLAUSES = (12, 13, 14)


# ---------------------------------------------------------------------------
# Shared validation
# ---------------------------------------------------------------------------


def _frequency_axis(frequencies_hz: ArrayLike) -> NDArray[np.float64]:
    """Positive, finite and strictly increasing frequencies.

    :raises ValueError: for anything else.
    """
    frequencies = require_positive_array(frequencies_hz, "frequencies_hz")
    if np.any(np.diff(frequencies) <= 0.0):
        msg = "'frequencies_hz' must be strictly increasing."
        raise ValueError(msg)
    return frequencies


def _band_column(values: ArrayLike, name: str, count: int) -> NDArray[np.float64]:
    """A finite column of one value per frequency, a scalar spread over all.

    :raises ValueError: if it is neither a scalar nor one value per frequency.
    """
    column = require_finite_array(values, name)
    if column.size == 1:
        return np.full(count, float(column[0]))
    if column.size != count:
        msg = (
            f"'{name}' must hold one value per frequency ({count}) or a single "
            f"value; got {column.size}."
        )
        raise ValueError(msg)
    return column


def _determinations(values: ArrayLike, name: str, count: int) -> NDArray[np.float64]:
    """Readings as a matrix of one row per determination, one column per band.

    A scalar is one value for every band, a 1-D array one determination, and a
    2-D array one row per determination.

    :raises ValueError: for a value that is not finite, a column count that is
        not the number of frequencies, or more than two dimensions.
    """
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc
    if array.ndim > _MATRIX_RANK or array.size == 0:
        msg = f"'{name}' must be a scalar, one value per frequency or a matrix."
        raise ValueError(msg)
    if not np.all(np.isfinite(array)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    if array.ndim == 0 or array.size == 1:
        return np.full((1, count), float(array.reshape(-1)[0]))
    matrix = np.atleast_2d(array)
    if matrix.shape[1] != count:
        msg = (
            f"'{name}' must hold one column per frequency ({count}); got shape "
            f"{array.shape}."
        )
        raise ValueError(msg)
    return matrix


def _common_rows(named: Mapping[str, NDArray[np.float64]]) -> int:
    """The number of determinations every matrix agrees on.

    A matrix of one row stands for every determination; any other count has to
    be the same across the inputs.

    :raises ValueError: for two inputs with different numbers of rows, both
        above one.
    """
    counts = {name: matrix.shape[0] for name, matrix in named.items()}
    rows = {count for count in counts.values() if count > 1}
    if len(rows) > 1:
        msg = (
            "The readings must hold the same number of determinations, one row "
            f"each, or a single row for all of them; got {counts}."
        )
        raise ValueError(msg)
    return rows.pop() if rows else 1


def _index_of(frequencies: NDArray[np.float64], target_hz: float, name: str) -> int:
    """The position of the frequency the text names among the given ones.

    :raises ValueError: if none of them is within 2 % of it.
    """
    target = require_positive(target_hz, name)
    nearest = int(np.argmin(np.abs(np.log(frequencies / target))))
    if not math.isclose(frequencies[nearest], target, rel_tol=_NOMINAL_TOLERANCE):
        msg = (
            f"'{name}' ({target:g} Hz) must be one of 'frequencies_hz', to within "
            "2 %, so that the readings there can be read."
        )
        raise ValueError(msg)
    return nearest


# ---------------------------------------------------------------------------
# Annex H: exact frequencies
# ---------------------------------------------------------------------------


def exact_frequencies(
    lowest_hz: float, highest_hz: float, *, fraction: int = 12
) -> NDArray[np.float64]:
    r"""The exact base-ten frequencies between two limits (IEC 62585:2012,
    Annex H, Formula (H.1)).

    .. math::

       f_x = f_\mathrm{r}\, 10^{3x/(10b)}

    for every integer :math:`x`, with :math:`f_\mathrm{r} = 1000` Hz and the
    step-width designator :math:`b`. Annex H gives it for :math:`b = 12`,
    one-twelfth-octave steps, whose decade from 1 kHz to 10 kHz Table H.1
    prints to seven significant digits; they are the band edges of
    one-twelfth-octave filters, so 1 kHz and every one-third-octave midband
    frequency are among them. Clauses 10 and 12 to 14 and Annexes B and C
    report the corrections at these exact frequencies rather than at the
    nominal ones. :math:`b = 1` gives the exact octave midband frequencies
    clause 10 measures a microphone at, and :math:`b = 3` the one-third-octave
    ones.

    :param lowest_hz: The lowest frequency wanted, in Hz.
    :param highest_hz: The highest frequency wanted, in Hz, not below
        ``lowest_hz``.
    :param fraction: The step-width designator :math:`b` (Default: 12).
    :return: Every exact frequency from ``lowest_hz`` to ``highest_hz``
        inclusive, in Hz, increasing and read-only. It may be empty when the
        range is narrower than a step.
    :raises ValueError: for a limit that is not positive and finite, limits in
        the wrong order, or a designator that is not a whole number of at
        least one.
    """
    lowest = require_positive(lowest_hz, "lowest_hz")
    highest = require_positive(highest_hz, "highest_hz")
    if highest < lowest:
        msg = (
            f"'highest_hz' ({highest:g} Hz) must not be below 'lowest_hz' "
            f"({lowest:g} Hz)."
        )
        raise ValueError(msg)
    b = require_count(fraction, "fraction")
    per_decade = 10.0 * b / 3.0
    first = math.ceil(per_decade * math.log10(lowest / _REFERENCE_FREQUENCY_HZ) - 1e-6)
    last = math.floor(per_decade * math.log10(highest / _REFERENCE_FREQUENCY_HZ) + 1e-6)
    x = np.arange(first, last + 1, dtype=np.float64)
    frequencies = _REFERENCE_FREQUENCY_HZ * 10.0 ** (3.0 * x / (10.0 * b))
    inside = (frequencies >= lowest * (1.0 - _RANGE_TOLERANCE)) & (
        frequencies <= highest * (1.0 + _RANGE_TOLERANCE)
    )
    return read_only(frequencies[inside])


# ---------------------------------------------------------------------------
# Annex A: the adjustment value at the calibration check frequency
# ---------------------------------------------------------------------------


def _tolerance_column(
    tolerance_db: ArrayLike | None, count: int
) -> NDArray[np.float64] | None:
    """One tolerance per frequency, positive, infinity allowed; or ``None``.

    :raises ValueError: for a tolerance that is not positive, of the wrong
        length, or infinite at every frequency.
    """
    if tolerance_db is None:
        return None
    try:
        tolerance = np.atleast_1d(np.asarray(tolerance_db, dtype=np.float64))
    except (TypeError, ValueError) as exc:
        msg = "'tolerance_db' must be numeric."
        raise ValueError(msg) from exc
    if tolerance.ndim != 1 or tolerance.size not in (1, count):
        msg = (
            f"'tolerance_db' must hold one value per frequency ({count}) or a "
            f"single value; got shape {tolerance.shape}."
        )
        raise ValueError(msg)
    if np.any(np.isnan(tolerance)) or np.any(tolerance <= 0.0):
        msg = "'tolerance_db' must be positive; infinity leaves a frequency out."
        raise ValueError(msg)
    if not np.any(np.isfinite(tolerance)):
        msg = "'tolerance_db' must be finite at one frequency at least."
        raise ValueError(msg)
    return np.array(np.broadcast_to(tolerance, (count,)))


@dataclass(frozen=True)
class AdjustmentValue:
    r"""The adjustment value at the calibration check frequency
    (IEC 62585:2012, Annex A).

    The free-field response of the meter before its sensitivity is adjusted,
    the tolerances the fit weighs it with, and what the meter indicates on its
    sound calibrator at that same sensitivity. The fit and everything that
    follows from it are derived from those, so a result cannot state an
    adjustment its own readings do not give. Figure A.1 names the levels at
    the calibration check frequency :math:`f_\mathrm{R}`: :math:`L_1` the
    level stated for the calibrator, :math:`L_2` the indication in a free
    field at that level, :math:`L_3` the indication in a pressure field at
    that level, :math:`L_4` the indication on the calibrator, all after the
    adjustment. The manual states :math:`\Delta L = L_1 - L_4` as a fixed
    number, without an uncertainty (clause 8).

    :ivar frequencies_hz: the frequencies of the free-field response, in Hz.
    :ivar free_field_deviation_db: :math:`d`, the indication in the free field
        less the incident level at each frequency, before the adjustment, in
        dB.
    :ivar calibrator_level_db: :math:`L_1`, the level stated for the sound
        calibrator, in dB.
    :ivar calibrator_reading_db: :math:`L_4'`, what the meter indicates on the
        calibrator before the adjustment, at the sensitivity the free-field
        readings were taken at, in dB.
    :ivar check_frequency_hz: :math:`f_\mathrm{R}`, the calibration check
        frequency, in Hz: one of :attr:`frequencies_hz`.
    :ivar tolerance_db: :math:`t` at each frequency, in dB, infinite where a
        frequency does not pull the fit; ``None`` for equal weights.
    :ivar pressure_deviation_db: the indication in a pressure field of level
        :math:`L_1` less :math:`L_1` at each frequency, before the adjustment,
        in dB; ``None`` when the pressure response was not given.
    """

    frequencies_hz: NDArray[np.float64]
    free_field_deviation_db: NDArray[np.float64]
    calibrator_level_db: float
    calibrator_reading_db: float
    check_frequency_hz: float = _CHECK_FREQUENCY_HZ
    tolerance_db: NDArray[np.float64] | None = None
    pressure_deviation_db: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Refuse columns that disagree, and publish them read-only.

        :raises ValueError: if a column does not hold one value per frequency,
            a value is not finite (a tolerance may be infinite), a tolerance
            is not positive, or the check frequency is not among the
            frequencies.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        columns = ["free_field_deviation_db"]
        if self.pressure_deviation_db is not None:
            columns.append("pressure_deviation_db")
        for name in columns:
            column = require_finite_array(getattr(self, name), name)
            if column.size != frequencies.size:
                msg = (
                    f"AdjustmentValue: '{name}' must hold one value per frequency "
                    f"({frequencies.size}); got {column.size}."
                )
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column.copy()))
        tolerance = _tolerance_column(self.tolerance_db, frequencies.size)
        if tolerance is not None:
            object.__setattr__(self, "tolerance_db", read_only(tolerance))
        for name in ("calibrator_level_db", "calibrator_reading_db"):
            require_finite(getattr(self, name), name)
        _index_of(frequencies, self.check_frequency_hz, "check_frequency_hz")

    @property
    def weights(self) -> NDArray[np.float64]:
        r"""The weight of each frequency in the fit, :math:`1/t_i^2`
        normalised to sum to one; equal without tolerances.
        """
        if self.tolerance_db is None:
            count = self.frequencies_hz.size
            return np.full(count, 1.0 / count)
        tolerance = self.tolerance_db
        raw = np.where(np.isfinite(tolerance), 1.0 / tolerance**2, 0.0)
        return raw / float(raw.sum())

    @property
    def sensitivity_adjustment_db(self) -> float:
        r""":math:`s = -\sum_i w_i d_i`, the change of sensitivity the fit
        makes, in dB: added to every indication.
        """
        return -float(np.sum(self.weights * self.free_field_deviation_db))

    @property
    def calibrator_indicated_level_db(self) -> float:
        r""":math:`L_4 = L_4' + s`, what the adjusted meter indicates on the
        calibrator, in dB.
        """
        return self.calibrator_reading_db + self.sensitivity_adjustment_db

    @property
    def adjusted_deviation_db(self) -> NDArray[np.float64]:
        r"""The deviation of the free-field response after the adjustment,
        :math:`d + s`, in dB: curve (2) less curve (1) of Figure A.1.
        """
        return self.free_field_deviation_db + self.sensitivity_adjustment_db

    @property
    def adjustment_db(self) -> float:
        r""":math:`\Delta L = L_1 - L_4`, in dB: the value the manual states,
        added to the indication on the calibrator to obtain its stated level.
        """
        return self.calibrator_level_db - self.calibrator_indicated_level_db

    def _check_index(self) -> int:
        return _index_of(
            self.frequencies_hz, self.check_frequency_hz, "check_frequency_hz"
        )

    @property
    def check_frequency_offset_db(self) -> float:
        r""":math:`L_2 - L_1`, in dB: the deliberate "offset" NOTE 1 of clause
        8 allows at the calibration check frequency, which the fit over the
        whole range leaves in the free-field response there.
        """
        return float(self.adjusted_deviation_db[self._check_index()])

    @property
    def free_field_indicated_level_db(self) -> float:
        r""":math:`L_2`, the indication in a free field at :math:`L_1` and the
        calibration check frequency, after the adjustment, in dB.
        """
        return self.calibrator_level_db + self.check_frequency_offset_db

    @property
    def pressure_indicated_level_db(self) -> float | None:
        r""":math:`L_3`, the indication in a pressure field at :math:`L_1` and
        the calibration check frequency, after the adjustment, in dB; ``None``
        without the pressure response. :math:`L_3 - L_4` is what the loading
        of the calibrator by the microphone makes of it (NOTE to Figure A.1).
        """
        if self.pressure_deviation_db is None:
            return None
        deviation = float(self.pressure_deviation_db[self._check_index()])
        return self.calibrator_level_db + deviation + self.sensitivity_adjustment_db

    @property
    def pressure_to_free_field_correction_db(self) -> NDArray[np.float64] | None:
        r"""The pressure-to-free-field correction of the meter at each
        frequency, in dB: the free-field level (1) less the indication in the
        pressure field (3), after the adjustment. ``None`` without the pressure
        response.
        """
        if self.pressure_deviation_db is None:
            return None
        return -(self.pressure_deviation_db + self.sensitivity_adjustment_db)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the free-field deviation before and after the adjustment,
        with the tolerances it was weighed against.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the adjusted-response curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_adjustment_value

        return plot_adjustment_value(
            self, ax=ax, language=check_language(language), **kwargs
        )


def adjustment_value(
    frequencies_hz: ArrayLike,
    free_field_indicated_level_db: ArrayLike,
    calibrator_reading_db: float,
    *,
    calibrator_level_db: float,
    incident_level_db: ArrayLike | None = None,
    tolerance_db: ArrayLike | None = None,
    pressure_indicated_level_db: ArrayLike | None = None,
    check_frequency_hz: float = _CHECK_FREQUENCY_HZ,
) -> AdjustmentValue:
    r"""The adjustment value at the calibration check frequency
    (IEC 62585:2012, Annex A).

    The free-field response of the meter is measured "with where possible a
    measured level equal to the stated level for the recommended sound
    calibrator", the sensitivity is adjusted "to minimise the averaged
    deviation" of the indication from the incident level over the frequency
    range, and the adjusted meter is then exposed to the calibrator:

    .. math::

       s = -\frac{\sum_i w_i d_i}{\sum_i w_i},
       \qquad
       \Delta L = L_1 - (L_4' + s)

    with :math:`d_i` the indication less the incident level at each
    frequency, :math:`w_i = 1/t_i^2` for a tolerance :math:`t_i` (or equal
    weights), and :math:`L_4'` the indication on the calibrator at the
    sensitivity the free-field readings were taken at. The least-squares
    weighting is this module's reading of a text that prints no formula (see
    the module notes). Where the achievable free-field level differs from
    :math:`L_1`, ``incident_level_db`` carries it, which is the allowance the
    text asks for.

    :param frequencies_hz: The frequencies of the free-field response, in Hz,
        increasing, the calibration check frequency among them.
    :param free_field_indicated_level_db: What the meter indicates in the free
        field at each frequency, in dB, before the adjustment.
    :param calibrator_reading_db: :math:`L_4'`, what the meter indicates on
        the recommended calibrator at the same sensitivity, in dB.
    :param calibrator_level_db: :math:`L_1`, the level stated for the
        calibrator at the calibration check frequency, in dB.
    :param incident_level_db: The incident free-field level at each frequency,
        in dB, one value or one per frequency (Default: None, the calibrator's
        :math:`L_1` at every frequency).
    :param tolerance_db: The tolerance the deviation is judged against at each
        frequency, in dB, such as the narrower side of the IEC 61672-1
        acceptance limits for the class; one value or one per frequency, and
        infinite where a frequency should not pull the fit (Default: None,
        equal weights).
    :param pressure_indicated_level_db: What the meter indicates in a
        pressure field of level :math:`L_1` at each frequency, in dB, before
        the adjustment, for the pressure-to-free-field correction and
        :math:`L_3` (Default: None).
    :param check_frequency_hz: :math:`f_\mathrm{R}`, in Hz (Default: 1000).
    :return: The :class:`AdjustmentValue`.
    :raises ValueError: for columns that do not hold one value per frequency,
        a value that is not finite, a tolerance that is not positive or finite
        nowhere, or a check frequency that is not among the frequencies.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    indicated = _band_column(
        free_field_indicated_level_db, "free_field_indicated_level_db", count
    )
    level = require_finite(calibrator_level_db, "calibrator_level_db")
    incident = (
        np.full(count, level)
        if incident_level_db is None
        else _band_column(incident_level_db, "incident_level_db", count)
    )
    pressure = (
        None
        if pressure_indicated_level_db is None
        else _band_column(
            pressure_indicated_level_db, "pressure_indicated_level_db", count
        )
        - level
    )
    return AdjustmentValue(
        frequencies_hz=frequencies,
        free_field_deviation_db=indicated - incident,
        calibrator_level_db=level,
        calibrator_reading_db=require_finite(
            calibrator_reading_db, "calibrator_reading_db"
        ),
        check_frequency_hz=float(check_frequency_hz),
        tolerance_db=_tolerance_column(tolerance_db, count),
        pressure_deviation_db=pressure,
    )


# ---------------------------------------------------------------------------
# Annexes D, E and F: the corrections over a range of frequencies
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FreeFieldCorrection:
    r"""The corrections that bring a meter on a source to its free-field
    response (IEC 62585:2012, Formulas (D.7), (E.6) and (F.13)).

    One row of :attr:`corrections_db` per determination, one combination of
    microphone and source, and one column per frequency. The correction the
    manual states is their mean at each frequency (D.2 step 6, E.2 step 5,
    F.2 step 5); clauses 12 to 14 judge the range over the microphones
    against the maximum permitted expanded uncertainty.

    :ivar frequencies_hz: the frequencies, in Hz.
    :ivar corrections_db: :math:`C_\mathrm{FF,SLM}`, or :math:`C_\mathrm{N,FF,SLM}`
        for an actuator, of each determination, in dB, shape
        ``(determinations, frequencies)``.
    :ivar reference_correction_db: what the reference microphone contributes
        at each frequency, in dB: :math:`C_\mathrm{FF,RM}` for a calibrator or
        a coupler, :math:`S_\mathrm{N,RM} + G_\mathrm{N,RC}` for an actuator.
    :ivar source: ``"sound_calibrator"`` (Annex D), ``"comparison_coupler"``
        (Annex E) or ``"electrostatic_actuator"`` (Annex F).
    :ivar check_frequency_hz: the normalisation frequency :math:`f_0` of an
        actuator's corrections, in Hz; ``None`` for the other two sources,
        whose corrections are absolute.
    """

    frequencies_hz: NDArray[np.float64]
    corrections_db: NDArray[np.float64]
    reference_correction_db: NDArray[np.float64]
    source: str
    check_frequency_hz: float | None = None

    def __post_init__(self) -> None:
        """Refuse an unknown source or columns that disagree, and publish them
        read-only.

        :raises ValueError: if the source is not one of the three, the
            corrections are not one column per frequency, a value is not
            finite, or the normalisation frequency is missing for an actuator,
            given for another source, or not among the frequencies.
        """
        if self.source not in _SOURCES:
            msg = (
                f"FreeFieldCorrection: 'source' must be one of {tuple(_SOURCES)}; "
                f"got {self.source!r}."
            )
            raise ValueError(msg)
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        corrections = np.array(self.corrections_db, dtype=np.float64, ndmin=2)
        if corrections.ndim != _MATRIX_RANK or corrections.shape[1] != frequencies.size:
            msg = (
                "FreeFieldCorrection: 'corrections_db' must hold one row per "
                f"determination and one column per frequency ({frequencies.size}); "
                f"got shape {corrections.shape}."
            )
            raise ValueError(msg)
        if not np.all(np.isfinite(corrections)):
            msg = (
                "FreeFieldCorrection: 'corrections_db' must contain only finite values."
            )
            raise ValueError(msg)
        object.__setattr__(self, "corrections_db", read_only(corrections))
        reference = require_finite_array(
            self.reference_correction_db, "reference_correction_db"
        )
        if reference.size != frequencies.size:
            msg = (
                "FreeFieldCorrection: 'reference_correction_db' must hold one "
                f"value per frequency ({frequencies.size}); got {reference.size}."
            )
            raise ValueError(msg)
        object.__setattr__(self, "reference_correction_db", read_only(reference.copy()))
        normalised = self.source == "electrostatic_actuator"
        if normalised != (self.check_frequency_hz is not None):
            msg = (
                "FreeFieldCorrection: 'check_frequency_hz' is the normalisation "
                "frequency of an electrostatic actuator's corrections, and only "
                "theirs."
            )
            raise ValueError(msg)
        if self.check_frequency_hz is not None:
            _index_of(frequencies, self.check_frequency_hz, "check_frequency_hz")

    @property
    def correction_db(self) -> NDArray[np.float64]:
        """The mean correction over the determinations at each frequency, in
        dB: the value the manual states.
        """
        return np.mean(self.corrections_db, axis=0)

    @property
    def range_db(self) -> NDArray[np.float64]:
        """The range of the determinations at each frequency, largest less
        smallest, in dB; zero for a single determination.
        """
        return np.ptp(self.corrections_db, axis=0)

    @property
    def determinations(self) -> int:
        """The number of determinations averaged."""
        return int(self.corrections_db.shape[0])

    @property
    def formula(self) -> str:
        """The formula applied: ``"D.7"``, ``"E.6"`` or ``"F.13"``."""
        return _SOURCES[self.source][0]

    @property
    def clause(self) -> int:
        """The clause whose maximum uncertainty the correction is judged
        against: 12, 13 or 14.
        """
        return _SOURCES[self.source][1]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the correction against frequency, with every determination
        and the range between them.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the mean-correction curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_free_field_correction

        return plot_free_field_correction(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _substitution(
    frequencies_hz: ArrayLike,
    readings: Mapping[str, ArrayLike],
    *,
    source: str,
    reference_correction_db: ArrayLike,
    source_level_difference_db: ArrayLike,
    source_difference_name: str,
    free_field_level_difference_db: ArrayLike,
) -> FreeFieldCorrection:
    """Formula (D.7) or (E.6): the two responses and the reference correction.

    ``readings`` holds, in this order, the meter in the free field, the
    reference in the free field, the meter on the source and the reference on
    the source.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    matrices = {
        name: _determinations(value, name, count) for name, value in readings.items()
    }
    free_field = _determinations(
        free_field_level_difference_db, "free_field_level_difference_db", count
    )
    on_source = _determinations(
        source_level_difference_db, source_difference_name, count
    )
    _common_rows(
        {
            **matrices,
            "free_field_level_difference_db": free_field,
            source_difference_name: on_source,
        }
    )
    slm_free, reference_free, slm_source, reference_source = matrices.values()
    reference = _band_column(
        reference_correction_db, "reference_free_field_correction_db", count
    )
    corrections = (
        (slm_free - slm_source)
        - (reference_free - reference_source)
        - free_field
        + on_source
        + reference
    )
    return FreeFieldCorrection(
        frequencies_hz=frequencies,
        corrections_db=corrections,
        reference_correction_db=reference,
        source=source,
    )


def sound_calibrator_correction(
    frequencies_hz: ArrayLike,
    slm_free_field_level_db: ArrayLike,
    reference_free_field_level_db: ArrayLike,
    slm_calibrator_level_db: ArrayLike,
    reference_calibrator_level_db: ArrayLike,
    *,
    reference_free_field_correction_db: ArrayLike,
    free_field_level_difference_db: ArrayLike = 0.0,
    calibrator_level_difference_db: ArrayLike = 0.0,
) -> FreeFieldCorrection:
    r"""Free-field corrections for use with a multi-frequency sound calibrator
    (IEC 62585:2012, Annex D, Formula (D.7)).

    .. math::

       C_\mathrm{FF,SLM} = (L_\mathrm{ind1} - L_\mathrm{ind3})
       - (L_\mathrm{ind2} - L_\mathrm{ind4})
       - (L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}})
       + (L_{p,\mathrm{P1}} - L_{p,\mathrm{P2}}) + C_\mathrm{FF,RM}

    Four measurements (Figure D.1): the meter in a free progressive field
    (1), a type LS2P reference microphone in its place in the same field (2),
    the calibrator on the meter (3) and the same calibrator on the reference
    (4). Neither the meter nor the calibrator has to be calibrated absolutely:
    the result is the meter's free-field response relative to its response on
    the calibrator, carried over from the reference microphone's known
    free-field correction.

    Each reading may be one value per frequency or a matrix of one row per
    determination; D.2 step 6 asks for at least nine, three microphones on
    three calibrators, and the correction is their mean.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param slm_free_field_level_db: :math:`L_\mathrm{ind1}`, the meter in the
        free field, in dB.
    :param reference_free_field_level_db: :math:`L_\mathrm{ind2}`, the
        reference microphone in the same field, in dB.
    :param slm_calibrator_level_db: :math:`L_\mathrm{ind3}`, the meter on the
        calibrator, in dB.
    :param reference_calibrator_level_db: :math:`L_\mathrm{ind4}`, the
        reference microphone on the calibrator, in dB.
    :param reference_free_field_correction_db: :math:`C_\mathrm{FF,RM}`, the
        free-field correction of the reference microphone from IEC/TS
        61094-7, in dB, one per frequency or one for all.
    :param free_field_level_difference_db: :math:`L_{p,\mathrm{F1}} -
        L_{p,\mathrm{F2}}`, the free-field level during measurement 1 less that
        during measurement 2, from a monitor microphone, in dB (Default: 0, a
        stable source; NOTE 2).
    :param calibrator_level_difference_db: :math:`L_{p,\mathrm{P1}} -
        L_{p,\mathrm{P2}}`, the calibrator's level on the meter less that on
        the reference, in dB (Default: 0, a stable calibrator; NOTE 3).
    :return: The :class:`FreeFieldCorrection`.
    :raises ValueError: for a reading that is not finite, a column count that
        is not the number of frequencies, or readings with different numbers
        of determinations.
    """
    return _substitution(
        frequencies_hz,
        {
            "slm_free_field_level_db": slm_free_field_level_db,
            "reference_free_field_level_db": reference_free_field_level_db,
            "slm_calibrator_level_db": slm_calibrator_level_db,
            "reference_calibrator_level_db": reference_calibrator_level_db,
        },
        source="sound_calibrator",
        reference_correction_db=reference_free_field_correction_db,
        source_level_difference_db=calibrator_level_difference_db,
        source_difference_name="calibrator_level_difference_db",
        free_field_level_difference_db=free_field_level_difference_db,
    )


def comparison_coupler_correction(
    frequencies_hz: ArrayLike,
    slm_free_field_level_db: ArrayLike,
    reference_free_field_level_db: ArrayLike,
    slm_coupler_level_db: ArrayLike,
    reference_coupler_level_db: ArrayLike,
    *,
    reference_free_field_correction_db: ArrayLike,
    free_field_level_difference_db: ArrayLike = 0.0,
    coupler_level_difference_db: ArrayLike = 0.0,
) -> FreeFieldCorrection:
    r"""Free-field corrections for use with a comparison coupler
    (IEC 62585:2012, Annex E, Formula (E.6)).

    .. math::

       C_\mathrm{FF,SLM} = (L_\mathrm{ind1} - L_\mathrm{ind3b})
       - (L_\mathrm{ind2} - L_\mathrm{ind3a})
       - (L_{p,\mathrm{F1}} - L_{p,\mathrm{F2}})
       + (L_{p,\mathrm{P2}} - L_{p,\mathrm{P1}}) + C_\mathrm{FF,RM}

    with the symbols of Figure E.1: the meter in a free progressive field
    (measurement 1), a type LS2P reference microphone in its place (2), and
    both face to face in the two openings of the coupler (3), the reference
    reading :math:`L_\mathrm{ind3a}` at :math:`L_{p,\mathrm{P1}}` and the meter
    :math:`L_\mathrm{ind3b}` at :math:`L_{p,\mathrm{P2}}`. Formula (E.6) as
    printed exchanges the two readings in the coupler (see the module notes);
    the inputs here are named by what each reading is of, so the result is
    the meter's free-field response relative to its response in the coupler
    either way.

    Each reading may be one value per frequency or a matrix of one row per
    determination; E.2 step 5 asks for three microphones at least, and the
    correction is their mean.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param slm_free_field_level_db: :math:`L_\mathrm{ind1}`, the meter in the
        free field, in dB.
    :param reference_free_field_level_db: :math:`L_\mathrm{ind2}`, the
        reference microphone in the same field, in dB.
    :param slm_coupler_level_db: the meter in the coupler, in dB
        (:math:`L_\mathrm{ind3b}` of Figure E.1).
    :param reference_coupler_level_db: the reference microphone in the
        coupler, in dB (:math:`L_\mathrm{ind3a}` of Figure E.1).
    :param reference_free_field_correction_db: :math:`C_\mathrm{FF,RM}` from
        IEC/TS 61094-7, in dB, one per frequency or one for all.
    :param free_field_level_difference_db: :math:`L_{p,\mathrm{F1}} -
        L_{p,\mathrm{F2}}`, the free-field level during measurement 1 less that
        during measurement 2, in dB (Default: 0; NOTE 2).
    :param coupler_level_difference_db: the sound pressure level at the meter
        less that at the reference in the coupler, in dB (Default: 0).
    :return: The :class:`FreeFieldCorrection`.
    :raises ValueError: as :func:`sound_calibrator_correction`.
    """
    return _substitution(
        frequencies_hz,
        {
            "slm_free_field_level_db": slm_free_field_level_db,
            "reference_free_field_level_db": reference_free_field_level_db,
            "slm_coupler_level_db": slm_coupler_level_db,
            "reference_coupler_level_db": reference_coupler_level_db,
        },
        source="comparison_coupler",
        reference_correction_db=reference_free_field_correction_db,
        source_level_difference_db=coupler_level_difference_db,
        source_difference_name="coupler_level_difference_db",
        free_field_level_difference_db=free_field_level_difference_db,
    )


def electrostatic_actuator_correction(
    frequencies_hz: ArrayLike,
    slm_free_field_level_db: ArrayLike,
    reference_free_field_level_db: ArrayLike,
    slm_actuator_level_db: ArrayLike,
    *,
    reference_sensitivity_level_db: ArrayLike,
    reference_channel_gain_db: ArrayLike = 0.0,
    actuator_level_db: ArrayLike = 0.0,
    free_field_level_difference_db: ArrayLike = 0.0,
    check_frequency_hz: float = _CHECK_FREQUENCY_HZ,
) -> FreeFieldCorrection:
    r"""Free-field corrections, normalised to the calibration check frequency,
    for use with an electrostatic actuator (IEC 62585:2012, Annex F,
    Formula (F.13)).

    .. math::

       C_\mathrm{N,FF,SLM} = R_\mathrm{N,ind1} - R_\mathrm{N,ind2}
       - (R_\mathrm{N,p,F1} - R_\mathrm{N,p,F2}) + S_\mathrm{N,RM}
       + G_\mathrm{N,RC} - (R_\mathrm{N,ind3} - R_\mathrm{N,EA})

    every term :math:`X_\mathrm{N} = X(f) - X(f_0)` normalised to the
    calibration check frequency :math:`f_0` (Formulas (F.5) to (F.12)). Three
    measurements (Figure F.1): the meter in a free progressive field (1), a
    type LS2P reference microphone of known free-field sensitivity in its
    place (2), and the actuator on the meter (3). An actuator is not an
    absolute source (NOTE 4 to 3.4), so the correction is relative to
    :math:`f_0`, where it is zero, and the absolute response there comes from
    a sound calibrator (NOTE 2 of F.2).

    Each reading may be one value per frequency or a matrix of one row per
    determination; F.2 step 5 averages the combinations of microphone and
    actuator clause 7 asks for.

    :param frequencies_hz: The frequencies, in Hz, increasing, :math:`f_0`
        among them.
    :param slm_free_field_level_db: :math:`L_\mathrm{ind1}(f)`, the meter in
        the free field, in dB.
    :param reference_free_field_level_db: :math:`L_\mathrm{ind2}(f)`, the
        reference channel in the same field, in dB.
    :param slm_actuator_level_db: :math:`L_\mathrm{ind3}(f)`, the meter on the
        actuator, in dB.
    :param reference_sensitivity_level_db: :math:`S_\mathrm{RM}(f)`, the
        free-field (open-circuit) sensitivity level of the reference
        microphone, in dB re 1 V/Pa, one per frequency.
    :param reference_channel_gain_db: :math:`G_\mathrm{RC}(f)`, the gain of
        the reference channel, in dB (Default: 0, a flat channel). Its
        frequency response has to be known; its absolute gain does not.
    :param actuator_level_db: :math:`L_\mathrm{EA}(f)`, the level the actuator
        simulates, in dB (Default: 0 at every frequency: the same at
        :math:`f` and :math:`f_0` for a drive voltage independent of
        frequency, NOTE 4).
    :param free_field_level_difference_db: :math:`L_{p,\mathrm{F1}} -
        L_{p,\mathrm{F2}}` at each frequency, in dB (Default: 0; NOTE 3).
    :param check_frequency_hz: :math:`f_0`, in Hz (Default: 1000).
    :return: The :class:`FreeFieldCorrection`, zero at :math:`f_0`.
    :raises ValueError: as :func:`sound_calibrator_correction`, or for an
        :math:`f_0` that is not among the frequencies.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    index = _index_of(frequencies, check_frequency_hz, "check_frequency_hz")
    named = {
        "slm_free_field_level_db": _determinations(
            slm_free_field_level_db, "slm_free_field_level_db", count
        ),
        "reference_free_field_level_db": _determinations(
            reference_free_field_level_db, "reference_free_field_level_db", count
        ),
        "slm_actuator_level_db": _determinations(
            slm_actuator_level_db, "slm_actuator_level_db", count
        ),
        "actuator_level_db": _determinations(
            actuator_level_db, "actuator_level_db", count
        ),
        "free_field_level_difference_db": _determinations(
            free_field_level_difference_db, "free_field_level_difference_db", count
        ),
    }
    _common_rows(named)
    normalised = {name: matrix - matrix[:, [index]] for name, matrix in named.items()}
    sensitivity = _band_column(
        reference_sensitivity_level_db, "reference_sensitivity_level_db", count
    )
    gain = _band_column(reference_channel_gain_db, "reference_channel_gain_db", count)
    reference = (sensitivity - sensitivity[index]) + (gain - gain[index])
    corrections = (
        normalised["slm_free_field_level_db"]
        - normalised["reference_free_field_level_db"]
        - normalised["free_field_level_difference_db"]
        + reference
        - (normalised["slm_actuator_level_db"] - normalised["actuator_level_db"])
    )
    return FreeFieldCorrection(
        frequencies_hz=frequencies,
        corrections_db=corrections,
        reference_correction_db=reference,
        source="electrostatic_actuator",
        check_frequency_hz=float(frequencies[index]),
    )


# ---------------------------------------------------------------------------
# Annex I: the uncertainty budget
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CorrectionUncertaintyBudget:
    r"""The uncertainty budget of a correction at one frequency
    (IEC 62585:2012, Annex I, Tables I.1 to I.3).

    One entry per component, in the order of Table I.1 and then any
    component the laboratory adds: the value the budget states, the divisor
    that turns it into a standard uncertainty :math:`u_i`, and its degrees of
    freedom. The combination is the law of propagation of the GUM, with every
    component entering Formula (E.6) with a sensitivity of :math:`\pm 1`, and
    the coverage factor the Student factor for the Welch-Satterthwaite
    effective degrees of freedom at the stated level of confidence.

    :ivar frequency_hz: the frequency, in Hz.
    :ivar descriptors: ``"a1"`` to ``"a15"``, then ``"static pressure"`` when
        clause 6 adds it, then the names of any further components.
    :ivar symbols: the symbol or name of each component.
    :ivar values_db: the value each component is stated as, in dB: a
        half-width, an expanded uncertainty or a standard uncertainty, as its
        divisor says.
    :ivar divisors: the divisor of each component.
    :ivar dofs: the degrees of freedom of each component (``inf`` for a
        Type B estimate).
    :ivar uncertainty: the :class:`~phonometry.metrology.UncertaintyResult`
        of the combination.
    :ivar coverage: the level of confidence, 0,95 by clause 5.
    """

    frequency_hz: float
    descriptors: tuple[str, ...]
    symbols: tuple[str, ...]
    values_db: NDArray[np.float64]
    divisors: NDArray[np.float64]
    dofs: NDArray[np.float64]
    uncertainty: UncertaintyResult
    coverage: float = 0.95

    def __post_init__(self) -> None:
        """Refuse columns that disagree, and publish them read-only.

        :raises ValueError: if the columns do not hold one entry per
            component, a value or divisor is not positive, or the coverage is
            not a probability.
        """
        require_positive(self.frequency_hz, "frequency_hz")
        count = len(self.descriptors)
        if len(self.symbols) != count:
            msg = "CorrectionUncertaintyBudget: 'symbols' must hold one per component."
            raise ValueError(msg)
        for name in ("values_db", "divisors", "dofs"):
            column = np.array(getattr(self, name), dtype=np.float64, ndmin=1)
            if column.shape != (count,):
                msg = (
                    f"CorrectionUncertaintyBudget: '{name}' must hold one value per "
                    f"component ({count}); got shape {column.shape}."
                )
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column))
        if np.any(np.isnan(self.values_db)) or np.any(self.values_db < 0.0):
            msg = "CorrectionUncertaintyBudget: 'values_db' must be non-negative."
            raise ValueError(msg)
        if not np.all(np.isfinite(self.divisors)) or np.any(self.divisors <= 0.0):
            msg = "CorrectionUncertaintyBudget: 'divisors' must be positive."
            raise ValueError(msg)
        if not 0.0 < self.coverage < 1.0:
            msg = f"CorrectionUncertaintyBudget: 'coverage' must be in (0, 1); got {self.coverage}."
            raise ValueError(msg)

    @property
    def standard_uncertainties_db(self) -> NDArray[np.float64]:
        r""":math:`u_i`, each value over its divisor, in dB."""
        return self.values_db / self.divisors

    @property
    def correction_db(self) -> float:
        """The correction the budget is for, in dB (0 when not given)."""
        return float(self.uncertainty.value)

    @property
    def combined_uncertainty_db(self) -> float:
        r""":math:`u(C_\mathrm{FF,SLM})`, the combined standard uncertainty,
        in dB.
        """
        return float(self.uncertainty.combined_uncertainty)

    @property
    def effective_dof(self) -> float:
        r"""The Welch-Satterthwaite effective degrees of freedom,
        :math:`u_\mathrm{c}^4 / \sum_i u_i^4/\nu_i`.
        """
        return float(self.uncertainty.effective_dof)

    @property
    def coverage_factor(self) -> float:
        """:math:`k`, the Student factor for the effective degrees of freedom
        at :attr:`coverage`.
        """
        return coverage_factor(self.coverage, self.effective_dof)

    @property
    def expanded_uncertainty_db(self) -> float:
        r""":math:`U = k\,u_\mathrm{c}`, in dB."""
        return self.coverage_factor * self.combined_uncertainty_db

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the standard uncertainty of each component, with
        :math:`u_\mathrm{c}`, :math:`k` and :math:`U`.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh`.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_correction_budget

        return plot_correction_budget(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _static_pressure_component(
    static_pressure_kpa: float, frequency_hz: float
) -> Quantity | None:
    """Clause 6: the component for measurements below 97 kPa, or ``None``.

    :raises ValueError: for a pressure outside the 80 kPa to 105 kPa clause 6
        allows measurements in.
    """
    pressure = require_finite(static_pressure_kpa, "static_pressure_kpa")
    low, high = _STATIC_PRESSURE_RANGE_KPA
    if not low <= pressure <= high:
        msg = (
            f"'static_pressure_kpa' ({pressure:g} kPa) must be within the "
            f"{low:g} kPa to {high:g} kPa IEC 62585 clause 6 allows measurements in."
        )
        raise ValueError(msg)
    if pressure >= _LOW_STATIC_PRESSURE_KPA:
        return None
    expanded = next(
        value
        for upper, value in _STATIC_PRESSURE_EXPANDED_DB
        if frequency_hz <= upper * (1.0 + _NOMINAL_TOLERANCE)
    )
    return Quantity(
        0.0,
        expanded / _STATIC_PRESSURE_COVERAGE_FACTOR,
        "gaussian",
        name=_STATIC_PRESSURE,
    )


def correction_uncertainty_budget(
    values_db: Mapping[str, float],
    *,
    repeatability_dof: float,
    frequency_hz: float,
    correction_db: float = 0.0,
    static_pressure_kpa: float | None = None,
    additional_components: Sequence[Quantity] = (),
    coverage: float = 0.95,
) -> CorrectionUncertaintyBudget:
    r"""The uncertainty budget of a correction with the 15 components of Table
    I.1 (IEC 62585:2012, Annex I).

    Each component is given as Table I.2 prints it in its "Value" column: the
    half-width of a rectangular distribution for most, the expanded
    uncertainty (:math:`k = 2`) from IEC/TS 61094-7 for the free-field
    correction of the reference microphone (a7), and the standard uncertainty
    from repeated measurements for the repeatability (a15). The divisors of
    Table I.1, :math:`\sqrt{3}`, 2 and 1, turn them into standard
    uncertainties; the combination is
    :func:`~phonometry.metrology.combine_uncertainty` on Formula (E.6), every
    component a correction with a sensitivity of :math:`\pm 1`; the effective
    degrees of freedom are Welch-Satterthwaite's, with only the repeatability
    finite; and the coverage factor is the Student factor for them at a level
    of confidence of 95 % (clause 5).

    Table I.2 at 1 kHz gives :math:`u_\mathrm{c} = 0{,}0590` dB and
    :math:`\nu_\mathrm{eff} = 29{,}98`, so :math:`k = 2{,}04` and
    :math:`U = 0{,}12` dB (the table prints :math:`k = 2{,}11`, an erratum;
    see the module notes); Table I.3 at 8 kHz gives :math:`u_\mathrm{c} =
    0{,}140` dB, :math:`k = 2{,}00` and :math:`U = 0{,}28` dB.

    Table I.1 is written for the comparison coupler of Annex E. The budget of
    a calibrator (Annex D) has the same 15 components with the readings on the
    calibrator in place of those in the coupler; one of an actuator (Annex F)
    adds its own, which ``additional_components`` carries.

    :param values_db: The value of each of the 15 components, in dB, keyed by
        the descriptor of Table I.1, ``"a1"`` to ``"a15"``. A component taken
        as negligible is given as 0, as Table I.2 gives a6 and a13.
    :param repeatability_dof: The degrees of freedom of the repeatability
        (a15), from the number of repeat measurements: 2 in Tables I.2 and
        I.3.
    :param frequency_hz: The frequency, in Hz, which sets the clause 6
        component and the maximum the budget is judged against.
    :param correction_db: The correction the budget is for, in dB (Default:
        0).
    :param static_pressure_kpa: The static pressure the measurements were
        made at, in kPa (Default: None). Below 97 kPa clause 6 adds a
        component of expanded uncertainty 0,15 dB up to 3 kHz and 0,25 dB
        above (:math:`k = 2`); outside 80 kPa to 105 kPa it refuses.
    :param additional_components: Further components the laboratory's own
        method needs, as :class:`~phonometry.metrology.Quantity` objects of
        estimate 0 and sensitivity 1, named (Default: none).
    :param coverage: The level of confidence (Default: 0,95, clause 5).
    :return: The :class:`CorrectionUncertaintyBudget`.
    :raises ValueError: for a set of components that is not the 15 of Table
        I.1, a value that is negative or not finite, degrees of freedom that
        are not positive, or a static pressure outside clause 6.
    """
    expected = tuple(IEC62585_TABLE_I1)
    given = tuple(values_db)
    missing = [key for key in expected if key not in values_db]
    extra = [key for key in given if key not in IEC62585_TABLE_I1]
    if missing or extra:
        msg = (
            "'values_db' must hold the 15 components of IEC 62585 Table I.1, keyed "
            f"'a1' to 'a15'; missing {missing}, unknown {extra}."
        )
        raise ValueError(msg)
    frequency = require_positive(frequency_hz, "frequency_hz")
    dof = float(repeatability_dof)
    if not dof > 0.0:
        msg = f"'repeatability_dof' must be positive; got {repeatability_dof!r}."
        raise ValueError(msg)
    quantities: list[Quantity] = []
    descriptors: list[str] = []
    symbols: list[str] = []
    values: list[float] = []
    divisors: list[float] = []
    signs: list[float] = []
    for key, row in IEC62585_TABLE_I1.items():
        value = float(values_db[key])
        if not (math.isfinite(value) and value >= 0.0):
            msg = (
                f"'values_db[{key!r}]' must be finite and non-negative; got {value!r}."
            )
            raise ValueError(msg)
        distribution = (
            "rectangular" if row.distribution == "rectangular" else "gaussian"
        )
        quantities.append(
            Quantity(
                0.0,
                value / row.divisor,
                distribution,
                dof if key == _REPEATABILITY else math.inf,
                name=key,
            )
        )
        descriptors.append(key)
        symbols.append(row.symbol)
        values.append(value)
        divisors.append(row.divisor)
        signs.append(_E6_SIGNS[key])
    extras: list[tuple[Quantity, float, float]] = []
    if static_pressure_kpa is not None:
        component = _static_pressure_component(static_pressure_kpa, frequency)
        if component is not None:
            # Stated as the expanded uncertainty (k = 2) clause 6 gives.
            extras.append(
                (
                    component,
                    component.uncertainty * _STATIC_PRESSURE_COVERAGE_FACTOR,
                    _STATIC_PRESSURE_COVERAGE_FACTOR,
                )
            )
    extras.extend(
        (component, component.uncertainty, 1.0) for component in additional_components
    )
    for index, (component, stated, divisor) in enumerate(extras):
        name = component.name or f"additional {index + 1}"
        quantities.append(
            Quantity(
                0.0,
                component.uncertainty,
                component.distribution,
                component.dof,
                name=name,
            )
        )
        descriptors.append(name)
        symbols.append(name)
        values.append(stated)
        divisors.append(divisor)
        signs.append(1.0)
    offset = require_finite(correction_db, "correction_db")
    weights = np.array(signs)

    def model(*components: float) -> float:
        return offset + float(np.dot(weights, np.asarray(components, dtype=np.float64)))

    result = combine_uncertainty(model, quantities)
    return CorrectionUncertaintyBudget(
        frequency_hz=frequency,
        descriptors=tuple(descriptors),
        symbols=tuple(symbols),
        values_db=np.array(values),
        divisors=np.array(divisors),
        dofs=np.array([quantity.dof for quantity in quantities]),
        uncertainty=result,
        coverage=float(coverage),
    )


# ---------------------------------------------------------------------------
# Clauses 9 to 14: the maximum permitted expanded uncertainty
# ---------------------------------------------------------------------------


def _clause(clause: object) -> int:
    """A clause of IEC 62585 that states a maximum uncertainty: 9 to 14.

    :raises ValueError: for any other.
    """
    msg = (
        "'clause' must be one of the IEC 62585 clauses that state a maximum "
        f"expanded uncertainty, {tuple(_MAXIMUM_UNCERTAINTY_DB)}; got {clause!r}."
    )
    if isinstance(clause, bool) or not isinstance(clause, (int, np.integer)):
        raise ValueError(msg)
    number = int(clause)
    if number not in _MAXIMUM_UNCERTAINTY_DB:
        raise ValueError(msg)
    return number


def _maximum_at(frequency: float, clause: int) -> float:
    """The maximum of one clause at one frequency, in dB.

    A frequency within 2 % of a boundary the text names is read as that
    boundary, so an exact base-ten frequency falls in the band its nominal one
    does: 3 981 Hz, the exact 4 kHz, is "up to and including 4 kHz", and
    10 000 Hz is "at and above 10 kHz".
    """
    for boundary, inclusive, value in _MAXIMUM_UNCERTAINTY_DB[clause]:
        if inclusive and frequency <= boundary * (1.0 + _NOMINAL_TOLERANCE):
            return value
        if not inclusive and frequency < boundary / (1.0 + _NOMINAL_TOLERANCE):
            return value
    return _MAXIMUM_UNCERTAINTY_DB[clause][-1][2]


def maximum_expanded_uncertainty(
    frequencies_hz: ArrayLike, *, clause: int
) -> NDArray[np.float64]:
    r"""The maximum permitted expanded uncertainty of a correction
    (IEC 62585:2012, clauses 9 to 14).

    ====== ========================================== =========================
    Clause Correction for                             Maximum, dB
    ====== ========================================== =========================
    9      reflections from the case, diffraction     0,25 to 4 kHz; 0,35 above
    10     the microphone's non-uniform response      0,25 from 63 Hz to 4 kHz;
                                                      0,35 to 8 kHz; 0,45 above
    11     windscreens and similar accessories        0,20 to 4 kHz; 0,30 above
    12-14  a calibrator, a coupler, an actuator       0,25 to 4 kHz; 0,35 below
                                                      10 kHz; 0,50 from 10 kHz
    ====== ========================================== =========================

    "To 4 kHz" includes 4 kHz; 10 kHz is in the band "at and above 10 kHz".
    Clauses 10 and 11 exclude the reproducibility component of the samples of
    microphone or accessory. A frequency within 2 % of a boundary is read as
    it, so the exact base-ten frequencies of Annex H fall where their nominal
    ones do.

    :param frequencies_hz: The frequencies, in Hz.
    :param clause: The clause, 9 to 14.
    :return: The maximum at each frequency, in dB, read-only.
    :raises ValueError: for another clause, a frequency that is not positive
        and finite, or, for clause 10, a frequency below 63 Hz.
    """
    number = _clause(clause)
    frequencies = require_positive_array(frequencies_hz, "frequencies_hz")
    if number == _MICROPHONE_CLAUSE and np.any(
        frequencies < _CLAUSE10_LOWEST_HZ / (1.0 + _NOMINAL_TOLERANCE)
    ):
        msg = "IEC 62585 clause 10 states its maximum from 63 Hz; 'frequencies_hz' goes below."
        raise ValueError(msg)
    return read_only(np.array([_maximum_at(float(f), number) for f in frequencies]))


@dataclass(frozen=True)
class CorrectionUncertaintyVerification:
    r"""The expanded uncertainties of a set of corrections against the maxima
    of their clause (IEC 62585:2012, clauses 5 and 9 to 14).

    Clause 5: "If the actual expanded uncertainty of measurement exceeds any
    of the maximum permitted values, the measurement shall not be used to
    evaluate the corrections provided in the instruction manual." Clauses 12
    to 14 add a second requirement on the microphone: when the range of the
    corrections measured with three microphones exceeds the maximum permitted
    expanded uncertainty at a frequency, the microphone is unsuitable for the
    source unless more samples show otherwise. Both are "shall not exceed", so
    a value equal to its maximum passes.

    :ivar clause: the clause, 9 to 14.
    :ivar frequencies_hz: the frequencies, in Hz.
    :ivar expanded_uncertainty_db: the actual expanded uncertainty at each
        frequency, in dB.
    :ivar maximum_uncertainty_db: the maximum permitted at each frequency, in
        dB.
    :ivar correction_db: the corrections, in dB, which the documentation of
        clause 15 states with their uncertainty; ``None`` if not given.
    :ivar coverage_factor: the coverage factor of each expanded uncertainty,
        which clause 15 asks to be stated; ``None`` if not given.
    :ivar correction_range_db: the range of the corrections over the
        microphones at each frequency, in dB (clauses 12 to 14); ``None`` if
        not given.
    """

    clause: int
    frequencies_hz: NDArray[np.float64]
    expanded_uncertainty_db: NDArray[np.float64]
    maximum_uncertainty_db: NDArray[np.float64]
    correction_db: NDArray[np.float64] | None = None
    coverage_factor: NDArray[np.float64] | None = None
    correction_range_db: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Refuse columns that disagree, and publish them read-only.

        :raises ValueError: for an unknown clause, a column that does not hold
            one value per frequency, a value that is not finite, a negative
            uncertainty or range, or a range for a clause other than 12 to 14.
        """
        _clause(self.clause)
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        if self.correction_range_db is not None and self.clause not in _RANGE_CLAUSES:
            msg = (
                "CorrectionUncertaintyVerification: the range of the corrections is "
                "judged by clauses 12 to 14 only."
            )
            raise ValueError(msg)
        for name in (
            "expanded_uncertainty_db",
            "maximum_uncertainty_db",
            "correction_db",
            "coverage_factor",
            "correction_range_db",
        ):
            value = getattr(self, name)
            if value is None:
                continue
            column = require_finite_array(value, name)
            if column.size != frequencies.size:
                msg = (
                    f"CorrectionUncertaintyVerification: '{name}' must hold one value "
                    f"per frequency ({frequencies.size}); got {column.size}."
                )
                raise ValueError(msg)
            if name != "correction_db" and np.any(column < 0.0):
                msg = (
                    f"CorrectionUncertaintyVerification: '{name}' must be non-negative."
                )
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column.copy()))

    @property
    def uncertainty_passes(self) -> NDArray[np.bool_]:
        """Whether the expanded uncertainty is within the maximum, frequency
        by frequency.
        """
        return self.expanded_uncertainty_db <= self.maximum_uncertainty_db

    @property
    def range_passes(self) -> NDArray[np.bool_] | None:
        """Whether the range of the corrections is within the maximum,
        frequency by frequency; ``None`` when no range was given.
        """
        if self.correction_range_db is None:
            return None
        return self.correction_range_db <= self.maximum_uncertainty_db

    @property
    def margin_db(self) -> NDArray[np.float64]:
        """The maximum less the expanded uncertainty at each frequency, in dB:
        negative where it fails.
        """
        return self.maximum_uncertainty_db - self.expanded_uncertainty_db

    @property
    def failing_frequencies_hz(self) -> NDArray[np.float64]:
        """The frequencies where either requirement fails, in Hz."""
        failing = ~self.uncertainty_passes
        ranges = self.range_passes
        if ranges is not None:
            failing = failing | ~ranges
        return self.frequencies_hz[failing]

    @property
    def subject(self) -> str:
        """What the clause corrects for, in the words of its title."""
        return _CLAUSE_SUBJECTS[self.clause]

    @property
    def passes(self) -> bool:
        """Whether every expanded uncertainty, and every range when given, is
        within the maximum of the clause.

        True says the measurement may be used for the corrections in the
        manual and, for clauses 12 to 14 with a range, that the microphone is
        suitable for the source. It says nothing of whether the corrections
        conform to IEC 61672-1, which clause 15 p) asks separately.
        """
        return self.failing_frequencies_hz.size == 0

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        An object is always true, so ``if verify_correction_uncertainty(...):``
        would pass every measurement. The verdict is :attr:`passes`.

        :raises TypeError: Always.
        """
        msg = (
            "a CorrectionUncertaintyVerification has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the expanded uncertainty and the range against the maximum of
        the clause.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the expanded-uncertainty curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_correction_uncertainty_verification

        return plot_correction_uncertainty_verification(
            self, ax=ax, language=check_language(language), **kwargs
        )

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        """Render the documentation of clause 15 n) and o) to a PDF.

        One page: the standard-basis line, an optional metadata header, the
        table of the corrections with their expanded uncertainty, coverage
        factor, maximum and verdict at each frequency beside the plot, and
        the boxed statement of whether the uncertainties are within the
        maximum permitted values.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata`;
            ``None`` produces a bare fiche.
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: Accepted for a uniform signature; it has no effect.
        :param language: Fiche language: ``"en"`` (default) or ``"es"``.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"``.
        :raises ImportError: If reportlab is not installed
            (``pip install phonometry[report]``), or matplotlib is missing
            for the embedded figure (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language

        check_language(language)
        check_engine(engine)
        from .._report.iec62585 import render_iec62585_report

        return render_iec62585_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def _optional_column(
    values: ArrayLike | None, name: str, count: int
) -> NDArray[np.float64] | None:
    return None if values is None else _band_column(values, name, count)


def verify_correction_uncertainty(
    frequencies_hz: ArrayLike,
    expanded_uncertainty_db: ArrayLike,
    *,
    clause: int,
    correction_db: ArrayLike | None = None,
    coverage_factor: ArrayLike | None = None,
    correction_range_db: ArrayLike | None = None,
) -> CorrectionUncertaintyVerification:
    r"""Verify the expanded uncertainties of a set of corrections against the
    maxima of their clause (IEC 62585:2012, clauses 5 and 9 to 14).

    The actual expanded uncertainty at each frequency, at a level of
    confidence of 95 % with the coverage factor stated (clause 5), has not to
    exceed :func:`maximum_expanded_uncertainty` of the clause; for a
    calibrator, a coupler or an actuator (clauses 12 to 14) the range of the
    corrections over three microphones has not to exceed it either. A
    :class:`FreeFieldCorrection` knows its clause, :attr:`~FreeFieldCorrection.clause`,
    and its range, :attr:`~FreeFieldCorrection.range_db`; a
    :class:`CorrectionUncertaintyBudget` per frequency gives the expanded
    uncertainty and the coverage factor.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param expanded_uncertainty_db: The actual expanded uncertainty at each
        frequency, in dB, one value or one per frequency.
    :param clause: The clause the corrections belong to: 9 (case and
        diffraction), 10 (microphone response), 11 (windscreens and
        accessories), 12 (sound calibrator), 13 (comparison coupler) or 14
        (electrostatic actuator).
    :param correction_db: The corrections, in dB, for the documentation of
        clause 15 (Default: None).
    :param coverage_factor: The coverage factor of each expanded uncertainty,
        for the same documentation (Default: None).
    :param correction_range_db: The range of the corrections over the
        microphones at each frequency, in dB, clauses 12 to 14 only (Default:
        None, not judged).
    :return: The :class:`CorrectionUncertaintyVerification`.
    :raises ValueError: for an unknown clause, columns that do not hold one
        value per frequency, a negative uncertainty or range, a range for
        clauses 9 to 11, or a frequency below 63 Hz for clause 10.
    """
    number = _clause(clause)
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    return CorrectionUncertaintyVerification(
        clause=number,
        frequencies_hz=frequencies,
        expanded_uncertainty_db=_band_column(
            expanded_uncertainty_db, "expanded_uncertainty_db", count
        ),
        maximum_uncertainty_db=maximum_expanded_uncertainty(frequencies, clause=number),
        correction_db=_optional_column(correction_db, "correction_db", count),
        coverage_factor=_optional_column(coverage_factor, "coverage_factor", count),
        correction_range_db=_optional_column(
            correction_range_db, "correction_range_db", count
        ),
    )

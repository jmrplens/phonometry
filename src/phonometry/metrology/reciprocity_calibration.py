#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Primary calibration of laboratory standard microphones by reciprocity: the
sensitivities that come out of three pair measurements, and the uncertainty
budget that goes with them (IEC 61094-2:2009 clause 5.7 and clause 7, IEC
61094-3:2016 clause 5.7 and clause 7).

A reciprocity calibration needs no reference microphone. Two microphones are
coupled acoustically, one drives and the other receives, and the electrical
transfer impedance :math:`Z_\mathrm{e,12} = U_2/i_1` that is measured is the
product of their two sensitivities times the acoustic transfer impedance of
whatever couples them, which is computed:

.. math::

   M_1 M_2 = \frac{Z_\mathrm{e,12}}{Z_\mathrm{a,12}}

In a coupler (IEC 61094-2) :math:`Z_\mathrm{a,12}` is the acoustic impedance
of the enclosed gas, worked out in
:mod:`~phonometry.metrology.reciprocity_coupler`; in a free field (IEC
61094-3) it is that of a spherical wave between the two acoustic centres,
worked out in :mod:`~phonometry.metrology.reciprocity_free_field`. Either way
three pairs taken from three microphones give three products, and each
sensitivity follows from them alone:

.. math::

   M_1 = \left(\frac{P_{12}\,P_{31}}{P_{23}}\right)^{1/2}, \qquad
   M_2 = \frac{P_{12}}{M_1}, \qquad M_3 = \frac{P_{31}}{M_1}

which is Formula (7) of IEC 61094-2 and Formula (8) of IEC 61094-3. With two
microphones and an auxiliary sound source, the ratio :math:`r_{12} =
M_1/M_2` measured against the source replaces the third pair (Formula (8) of
the first part, Formula (9) of the second): :math:`M_1 = (r_{12}\,P_{12})^{1/2}`.

**The sign of a square root.** Reciprocity fixes the products, and a product
does not change when every sensitivity changes sign together, so no
measurement of this kind can tell :math:`M` from :math:`-M`. Both parts ask
for the phase to be referred to the full four-quadrant range, 0 to
:math:`2\pi` (5.7.1 of each: a NOTE in IEC 61094-2, the running text in IEC
61094-3); the library takes the square root on
the branch that is continuous in frequency and has a non-negative real part at
the lowest frequency, then fixes the other two microphones by the products, so
that the three are consistent with every product at every frequency. The
modulus does not depend on the choice.

**Uncertainty.** Both parts list the components of a calibration in their
Table 1 (:data:`IEC61094_2_TABLE_1`, :data:`IEC61094_3_TABLE_1`) and ask for
each as a standard uncertainty as a function of frequency, in linear or
logarithmic form (7.5 of the first part, 7.8 of the second).
:func:`reciprocity_uncertainty_budget` combines them in quadrature at each
frequency and multiplies by the coverage factor: :math:`k = 2` in IEC 61094-2
7.5, and the factor for a 95 % coverage probability in IEC 61094-3 7.8, which
is 2 for a combination dominated by many comparable components. The
components the acoustic transfer impedance contributes are found, as both
parts describe, by "repeating a calculation while the various components are
changed one at a time by their associated uncertainty":
:func:`~phonometry.metrology.coupler_parameter_uncertainty` and
:func:`~phonometry.metrology.free_field_parameter_uncertainty` do that.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.display import RichDisplay
from .._internal.frozen import OwnsArrays, read_only
from .._internal.validation import require_choice, require_positive
from .free_field_corrections import _band_column, _frequency_axis

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "IEC61094_2_TABLE_1",
    "IEC61094_3_TABLE_1",
    "ReciprocityCalibration",
    "ReciprocityUncertaintyBudget",
    "ReciprocityUncertaintyRow",
    "reciprocity_uncertainty_budget",
]

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

#: The two sound fields, one part each: a coupler (IEC 61094-2) and a free
#: field (IEC 61094-3).
_FIELDS = ("pressure", "free_field")

#: The designation each field is calibrated by. IEC 61094-3 is read with its
#: corrigendum, which makes Formula (9) the complex sensitivity.
_STANDARDS: Mapping[str, str] = MappingProxyType(
    {"pressure": "IEC 61094-2:2009", "free_field": "IEC 61094-3:2016+COR1:2016"}
)

#: The two methods of 5.1 in both parts: three microphones, or two and an
#: auxiliary sound source.
_METHODS = ("three_microphones", "auxiliary_source")

#: The pairs of the three-microphone method, in the order of Formula (7) of
#: IEC 61094-2: 1 with 2, 2 with 3, 3 with 1.
_TRIAD_PAIRS = ("12", "23", "31")

#: IEC 61094-2:2009 7.5: "the uncertainty ... shall be stated as the expanded
#: uncertainty of measurement using a coverage factor of k = 2".
_COVERAGE_FACTOR = 2.0

#: Number of microphones in each method.
_TRIAD = 3
_PAIR = 2


def _complex_column(values: ArrayLike, name: str, count: int) -> NDArray[np.complex128]:
    """A finite complex column of one value per frequency, a scalar spread.

    :raises ValueError: for a value that is not numeric or not finite, or a
        size that is neither one nor the number of frequencies.
    """
    try:
        column = np.asarray(values, dtype=np.complex128).reshape(-1)
    except (TypeError, ValueError) as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc
    if column.size == 1:
        column = np.full(count, column[0], dtype=np.complex128)
    if column.size != count:
        msg = (
            f"'{name}' must hold one value per frequency ({count}) or a single "
            f"value; got {column.size}."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(column)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    if not np.all(np.abs(column) > 0.0):
        msg = f"'{name}' must not be zero: a sensitivity is divided by it."
        raise ValueError(msg)
    return column


def _continuous_root(square: NDArray[np.complex128]) -> NDArray[np.complex128]:
    r"""The square root of a frequency response on its continuous branch.

    The modulus is :math:`|z|^{1/2}`; the phase is half the unwrapped phase of
    :math:`z`, shifted by :math:`\pi` as a whole when that leaves the real part
    negative at the first frequency. A common change of sign is all the
    choice a reciprocity calibration leaves open (the module docstring).
    """
    phase = 0.5 * np.unwrap(np.angle(square))
    if math.cos(float(phase[0])) < 0.0:
        phase = phase + math.pi
    return np.sqrt(np.abs(square)) * np.exp(1j * phase)


def _triad(
    products: Sequence[NDArray[np.complex128]],
) -> NDArray[np.complex128]:
    """The three sensitivities from the products of pairs 12, 23 and 31."""
    p12, p23, p31 = products
    first = _continuous_root(p12 * p31 / p23)
    return np.vstack([first, p12 / first, p31 / first])


def _pair(
    product: NDArray[np.complex128], ratio: NDArray[np.complex128]
) -> NDArray[np.complex128]:
    """The two sensitivities from a product and the ratio :math:`M_1/M_2`."""
    first = _continuous_root(ratio * product)
    return np.vstack([first, first / ratio])


# ---------------------------------------------------------------------------
# The calibration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReciprocityCalibration(OwnsArrays):
    r"""The complex sensitivities of microphones calibrated by reciprocity
    (IEC 61094-2:2009 5.7 in a coupler, IEC 61094-3:2016 5.7 in a free field).

    Built by :func:`~phonometry.metrology.pressure_reciprocity`,
    :func:`~phonometry.metrology.pressure_reciprocity_pair`,
    :func:`~phonometry.metrology.free_field_reciprocity` and
    :func:`~phonometry.metrology.free_field_reciprocity_pair`.

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar sensitivity_v_per_pa: The complex sensitivity of each microphone,
        one row per microphone, in V/Pa: the pressure sensitivity
        :math:`M_\mathrm{p}` in a coupler, the free-field sensitivity
        :math:`M_\mathrm{f}` in a free field.
    :ivar products_v2_per_pa2: The product of the two sensitivities of each
        pair, one row per pair (12, 23, 31 in the three-microphone method,
        12 alone with an auxiliary source), in V²/Pa².
    :ivar field: ``"pressure"`` (IEC 61094-2) or ``"free_field"`` (IEC 61094-3).
    :ivar method: ``"three_microphones"`` or ``"auxiliary_source"``.
    :ivar corrections_db: Corrections added to every microphone's sensitivity
        level, by name, in dB at each frequency: the wave-motion correction of
        IEC 61094-2 Table C.3 for a large-volume coupler, say.
    :ivar expanded_uncertainty_db: The expanded uncertainty of the
        sensitivity level at each frequency, in dB, or ``None``.
    """

    frequencies_hz: NDArray[np.float64]
    sensitivity_v_per_pa: NDArray[np.complex128]
    products_v2_per_pa2: NDArray[np.complex128]
    field: str
    method: str
    corrections_db: Mapping[str, NDArray[np.float64]]
    expanded_uncertainty_db: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Refuse arrays that disagree, and publish everything read-only.

        :raises ValueError: for an unknown field or method, frequencies that
            are not positive and increasing, a sensitivity or product array
            whose shape does not match the method and the frequencies, a
            correction that is not one finite value per frequency, or a
            negative uncertainty.
        """
        require_choice(self.field, "field", _FIELDS)
        require_choice(self.method, "method", _METHODS)
        frequencies = _frequency_axis(self.frequencies_hz)
        count = frequencies.size
        object.__setattr__(self, "frequencies_hz", read_only(frequencies))
        microphones = _TRIAD if self.method == "three_microphones" else _PAIR
        pairs = _TRIAD if self.method == "three_microphones" else 1
        for name, rows in (
            ("sensitivity_v_per_pa", microphones),
            ("products_v2_per_pa2", pairs),
        ):
            array = np.array(
                getattr(self, name), dtype=np.complex128, ndmin=2, copy=None
            )
            if array.shape != (rows, count):
                msg = (
                    f"ReciprocityCalibration: '{name}' must have shape "
                    f"({rows}, {count}); got {array.shape}."
                )
                raise ValueError(msg)
            if not np.all(np.isfinite(array)):
                msg = f"ReciprocityCalibration: '{name}' must be finite."
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(array))
        corrections = {
            str(key): read_only(_band_column(value, f"corrections_db[{key!r}]", count))
            for key, value in self.corrections_db.items()
        }
        object.__setattr__(self, "corrections_db", MappingProxyType(corrections))
        if self.expanded_uncertainty_db is not None:
            uncertainty = _band_column(
                self.expanded_uncertainty_db, "expanded_uncertainty_db", count
            )
            if np.any(uncertainty < 0.0):
                msg = (
                    "ReciprocityCalibration: 'expanded_uncertainty_db' must be "
                    "non-negative."
                )
                raise ValueError(msg)
            object.__setattr__(self, "expanded_uncertainty_db", read_only(uncertainty))

    @property
    def standard(self) -> str:
        """The designation the calibration follows."""
        return _STANDARDS[self.field]

    @property
    def microphones(self) -> int:
        """The number of microphones calibrated: 3, or 2 with a source."""
        return int(self.sensitivity_v_per_pa.shape[0])

    @property
    def correction_db(self) -> NDArray[np.float64]:
        r""":math:`\sum_j C_j`, the corrections added to every level, in dB."""
        total = np.zeros(self.frequencies_hz.size)
        for value in self.corrections_db.values():
            total = total + value
        return total

    @property
    def sensitivity_level_db(self) -> NDArray[np.float64]:
        r""":math:`20\lg(|M|/1\,\mathrm{V/Pa}) + \sum_j C_j`, one row per
        microphone, in dB re 1 V/Pa.
        """
        level = 20.0 * np.log10(np.abs(self.sensitivity_v_per_pa))
        return level + self.correction_db

    @property
    def sensitivity_mv_per_pa(self) -> NDArray[np.float64]:
        """The modulus of each sensitivity with the corrections, in mV/Pa."""
        return 1000.0 * 10.0 ** (self.sensitivity_level_db / 20.0)

    @property
    def phase_deg(self) -> NDArray[np.float64]:
        """The phase of each sensitivity, in degrees from 0 to 360 (5.7.1 of
        both parts: a NOTE in IEC 61094-2, the running text in IEC 61094-3).
        """
        return np.mod(np.degrees(np.angle(self.sensitivity_v_per_pa)), 360.0)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the sensitivity level of each microphone against frequency,
        with the expanded uncertainty as a band when it is known.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve of the first microphone.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_reciprocity_calibration

        return plot_reciprocity_calibration(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _calibration(
    frequencies: NDArray[np.float64],
    sensitivities: NDArray[np.complex128],
    products: NDArray[np.complex128],
    *,
    field: str,
    method: str,
    corrections_db: Mapping[str, ArrayLike] | None,
    expanded_uncertainty_db: ArrayLike | None,
) -> ReciprocityCalibration:
    """Build the result; shared by the pressure and the free-field routes."""
    return ReciprocityCalibration(
        frequencies_hz=frequencies,
        sensitivity_v_per_pa=sensitivities,
        products_v2_per_pa2=products,
        field=field,
        method=method,
        corrections_db=dict(corrections_db or {}),  # type: ignore[arg-type]
        expanded_uncertainty_db=(
            None
            if expanded_uncertainty_db is None
            else np.asarray(expanded_uncertainty_db, dtype=np.float64)
        ),
    )


def _solved(
    frequencies: NDArray[np.float64],
    products: Sequence[NDArray[np.complex128]],
    sensitivity_ratio: ArrayLike | None,
    *,
    field: str,
    corrections_db: Mapping[str, ArrayLike] | None,
    expanded_uncertainty_db: ArrayLike | None,
) -> ReciprocityCalibration:
    """Solve the products for the sensitivities, by the triad or by a pair."""
    if sensitivity_ratio is None:
        sensitivities = _triad(products)
        method = "three_microphones"
    else:
        ratio = _complex_column(
            sensitivity_ratio, "sensitivity_ratio", frequencies.size
        )
        sensitivities = _pair(products[0], ratio)
        method = "auxiliary_source"
    return _calibration(
        frequencies,
        sensitivities,
        np.vstack(products),
        field=field,
        method=method,
        corrections_db=corrections_db,
        expanded_uncertainty_db=expanded_uncertainty_db,
    )


# ---------------------------------------------------------------------------
# The uncertainty components (Table 1 of both parts)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReciprocityUncertaintyRow(RichDisplay):
    """One row of Table 1 of IEC 61094-2:2009 or IEC 61094-3:2016,
    "Uncertainty components".

    :ivar component: The measured quantity as the table prints it.
    :ivar group: The heading the table lists it under.
    :ivar subclauses: The subclauses or annexes the table refers it to; empty
        where the table prints none.
    """

    component: str
    group: str
    subclauses: tuple[str, ...] = ()


def _rows(
    group: str, *rows: tuple[str, str, tuple[str, ...]]
) -> dict[str, ReciprocityUncertaintyRow]:
    return {
        key: ReciprocityUncertaintyRow(component, group, subclauses)
        for key, component, subclauses in rows
    }


_ELECTRICAL = "Electrical transfer impedance"
_PROCESSING = "Processing of results"
_THEORY = "Imperfection of theory"
_MICROPHONE = "Microphone parameters"

#: IEC 61094-2:2009 7.3.2, "Coupler properties", and 7.3.3, "Microphone
#: parameters", whose numbered subclauses Table 1 refers most of its components
#: to; each is named by its heading and numbered from its parent.
_COUPLER_PROPERTIES = "7.3.2"
_MICROPHONE_PARAMETERS = "7.3.3"
#: 7.3.2.1 "Coupler dimensions".
_COUPLER_DIMENSIONS = f"{_COUPLER_PROPERTIES}.1"
#: 7.3.2.2 "Heat conduction and viscous losses".
_HEAT_CONDUCTION_LOSSES = f"{_COUPLER_PROPERTIES}.2"
#: 7.3.2.3 "Capillary tube".
_CAPILLARY_TUBE = f"{_COUPLER_PROPERTIES}.3"
#: 7.3.2.4 "Physical quantities".
_PHYSICAL_QUANTITIES = f"{_COUPLER_PROPERTIES}.4"
#: 7.3.3.1 "Front cavity".
_FRONT_CAVITY = f"{_MICROPHONE_PARAMETERS}.1"
#: 7.3.3.2 "Acoustic impedance".
_ACOUSTIC_IMPEDANCE = f"{_MICROPHONE_PARAMETERS}.2"
#: 7.3.3.3 "Polarizing voltage".
_POLARIZING_VOLTAGE = f"{_MICROPHONE_PARAMETERS}.3"

#: IEC 61094-2:2009 Table 1, "Uncertainty components", printed folio 19 (PDF
#: page 21), keyed by the name :func:`reciprocity_uncertainty_budget` and
#: :func:`~phonometry.metrology.coupler_parameter_uncertainty` take each
#: component by, in the table's order. "Unintentional coupler/microphone
#: leakage" and the rounding error and repeatability print no subclause.
IEC61094_2_TABLE_1: Mapping[str, ReciprocityUncertaintyRow] = MappingProxyType(
    {
        **_rows(
            _ELECTRICAL,
            ("series_impedance", "Series impedance", ("7.2",)),
            ("voltage_ratio", "Voltage ratio", ("7.2",)),
            ("cross_talk", "Cross-talk", ("7.2",)),
            ("noise", "Inherent and ambient noise", ("7.2",)),
            ("distortion", "Distortion", ("7.2",)),
            ("frequency", "Frequency", ("7.2",)),
            ("receiver_ground_shield", "Receiver ground shield", ("6.3",)),
            ("transmitter_ground_shield", "Transmitter ground shield", ("6.3", "7.2")),
        ),
        **_rows(
            "Coupler properties",
            ("coupler_length", "Coupler length", (_COUPLER_DIMENSIONS,)),
            ("coupler_diameter", "Coupler diameter", (_COUPLER_DIMENSIONS,)),
            (
                "coupler_volume",
                "Coupler volume",
                (_COUPLER_DIMENSIONS, _HEAT_CONDUCTION_LOSSES),
            ),
            (
                "coupler_surface_area",
                "Coupler surface area",
                (_COUPLER_DIMENSIONS, _HEAT_CONDUCTION_LOSSES),
            ),
            ("leakage", "Unintentional coupler/microphone leakage", ()),
            (
                "capillary_tube_dimensions",
                "Capillary tube dimensions",
                (_CAPILLARY_TUBE,),
            ),
            ("static_pressure", "Static pressure", (_PHYSICAL_QUANTITIES,)),
            ("temperature", "Temperature", (_PHYSICAL_QUANTITIES,)),
            ("relative_humidity", "Relative humidity", (_PHYSICAL_QUANTITIES,)),
        ),
        **_rows(
            _MICROPHONE,
            ("front_cavity_depth", "Front cavity depth", (_FRONT_CAVITY,)),
            ("front_cavity_volume", "Front cavity volume", (_FRONT_CAVITY,)),
            ("equivalent_volume", "Equivalent volume", (_ACOUSTIC_IMPEDANCE,)),
            ("resonance_frequency", "Resonance frequency", (_ACOUSTIC_IMPEDANCE,)),
            ("loss_factor", "Loss factor", (_ACOUSTIC_IMPEDANCE,)),
            ("diaphragm_compliance", "Diaphragm compliance", (_ACOUSTIC_IMPEDANCE,)),
            ("diaphragm_mass", "Diaphragm mass", (_ACOUSTIC_IMPEDANCE,)),
            ("diaphragm_resistance", "Diaphragm resistance", (_ACOUSTIC_IMPEDANCE,)),
            (
                "front_cavity_thread",
                "Additional heat conduction caused by front cavity thread",
                (_FRONT_CAVITY,),
            ),
            (
                "polarizing_voltage",
                "Polarizing voltage",
                ("6.5.3", _POLARIZING_VOLTAGE),
            ),
        ),
        **_rows(
            _THEORY,
            ("heat_conduction_theory", "Heat conduction theory", ("Annex A",)),
            ("excess_volume", "Adding of excess volume", (_FRONT_CAVITY, "7.4")),
            ("viscosity_losses", "Viscosity losses", ("7.4",)),
            (
                "radial_wave_motion",
                "Radial wave-motion",
                ("6.4", _COUPLER_DIMENSIONS, "7.4"),
            ),
        ),
        **_rows(
            _PROCESSING,
            ("rounding", "Rounding error", ()),
            ("repeatability", "Repeatability of measurements", ()),
            (
                "static_pressure_corrections",
                "Static pressure corrections",
                ("6.5", "Annex D"),
            ),
            ("temperature_corrections", "Temperature corrections", ("6.5", "Annex D")),
        ),
    }
)

#: IEC 61094-3:2016 Table 1, "Uncertainty components", printed folios 17 and
#: 18 (PDF pages 19 and 20), keyed like :data:`IEC61094_2_TABLE_1` and in the
#: table's order. "Mathematical manipulations", the rounding error and the
#: repeatability print no subclause.
IEC61094_3_TABLE_1: Mapping[str, ReciprocityUncertaintyRow] = MappingProxyType(
    {
        **_rows(
            _ELECTRICAL,
            ("series_impedance", "Series impedance", ("7.2",)),
            ("voltage_ratio", "Voltage ratio", ("7.2",)),
            ("cross_talk", "Cross-talk", ("7.2",)),
            ("noise", "Inherent and ambient noise", ("7.2",)),
            ("distortion", "Distortion", ("7.2",)),
            ("reflections", "Reflections from surroundings", ("7.2", "7.3")),
            ("frequency", "Frequency", ("7.2",)),
            ("receiver_shield", "Receiver shield", ("6.3",)),
            ("transmitter_shield", "Transmitter shield", ("6.3", "7.2")),
        ),
        **_rows(
            "Acoustic transfer impedance",
            ("distance", "Distance", ("6.4", "6.5")),
            ("static_pressure", "Static pressure", ("6.6.2", "7.6")),
            ("temperature", "Temperature", ("6.6.3", "7.6")),
            ("relative_humidity", "Relative humidity", ("6.6.4", "7.6")),
            ("standing_waves", "Standing waves between microphones", ("7.3",)),
            ("air_attenuation", "Air attenuation", ("7.4", "Annex B")),
        ),
        **_rows(
            _MICROPHONE,
            ("acoustic_centres", "Acoustic centres", ("6.5",)),
            ("polarizing_voltage", "Polarizing voltage", ("6.2", "7.5")),
        ),
        **_rows(
            _THEORY,
            ("plane_wave_deviation", "Deviation from plane-waves", ("6.4", "7.3")),
        ),
        **_rows(
            _PROCESSING,
            ("mathematical_manipulations", "Mathematical manipulations", ()),
            ("rounding", "Rounding error", ()),
            ("repeatability", "Repeatability of measurements", ()),
            (
                "static_pressure_corrections",
                "Static pressure corrections",
                ("6.6", "Annex C"),
            ),
            ("temperature_corrections", "Temperature corrections", ("6.6", "Annex C")),
        ),
    }
)

#: The table each field's budget draws its components from.
_BUDGET_TABLES: Mapping[str, Mapping[str, ReciprocityUncertaintyRow]] = (
    MappingProxyType({"pressure": IEC61094_2_TABLE_1, "free_field": IEC61094_3_TABLE_1})
)


@dataclass(frozen=True)
class ReciprocityUncertaintyBudget(OwnsArrays):
    r"""The uncertainty budget of a reciprocity calibration as a function of
    frequency (IEC 61094-2:2009 7.5 and Table 1, IEC 61094-3:2016 7.8 and
    Table 1).

    Every component is a standard uncertainty of the sensitivity level in dB at
    each frequency; they are combined in quadrature and multiplied by the
    coverage factor.

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar field: ``"pressure"`` (IEC 61094-2) or ``"free_field"`` (IEC 61094-3).
    :ivar names: The key of each component, those of the field's Table 1 in its
        order, then any additional ones.
    :ivar components: The component as the table prints it, or the name of an
        additional one.
    :ivar standard_uncertainties_db: :math:`u_i(f)`, one row per component, in
        dB.
    :ivar coverage_factor: :math:`k`.
    """

    frequencies_hz: NDArray[np.float64]
    field: str
    names: tuple[str, ...]
    components: tuple[str, ...]
    standard_uncertainties_db: NDArray[np.float64]
    coverage_factor: float = _COVERAGE_FACTOR

    def __post_init__(self) -> None:
        """Refuse columns that disagree, and publish them read-only.

        :raises ValueError: for an unknown field, frequencies that are not
            positive and increasing, names and components of different
            lengths, no component, a matrix that is not one row per component
            and one column per frequency, an uncertainty that is negative or
            not finite, or a coverage factor that is not positive.
        """
        require_choice(self.field, "field", _FIELDS)
        require_positive(self.coverage_factor, "coverage_factor")
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies))
        count = len(self.names)
        if count == 0 or len(self.components) != count:
            msg = (
                "ReciprocityUncertaintyBudget: 'names' and 'components' must hold "
                "the same, non-zero, number of entries."
            )
            raise ValueError(msg)
        matrix = np.array(
            self.standard_uncertainties_db, dtype=np.float64, ndmin=2, copy=None
        )
        if matrix.shape != (count, frequencies.size):
            msg = (
                "ReciprocityUncertaintyBudget: 'standard_uncertainties_db' must "
                f"have shape ({count}, {frequencies.size}); got {matrix.shape}."
            )
            raise ValueError(msg)
        if not np.all(np.isfinite(matrix)) or np.any(matrix < 0.0):
            msg = (
                "ReciprocityUncertaintyBudget: 'standard_uncertainties_db' must be "
                "finite and non-negative."
            )
            raise ValueError(msg)
        object.__setattr__(self, "standard_uncertainties_db", read_only(matrix))

    @property
    def standard(self) -> str:
        """The designation whose Table 1 the budget follows."""
        return _STANDARDS[self.field]

    @property
    def combined_uncertainty_db(self) -> NDArray[np.float64]:
        r""":math:`u_\mathrm{c}(f) = (\sum_i u_i^2)^{1/2}`, in dB."""
        return np.sqrt(np.sum(self.standard_uncertainties_db**2, axis=0))

    @property
    def expanded_uncertainty_db(self) -> NDArray[np.float64]:
        r""":math:`U(f) = k\,u_\mathrm{c}(f)`, in dB."""
        return self.coverage_factor * self.combined_uncertainty_db

    @property
    def linear_combined_uncertainty_db(self) -> NDArray[np.float64]:
        r""":math:`u_\mathrm{c}` combined in linear form, in dB.

        Each component converted to a relative uncertainty
        :math:`r_i = 10^{u_i/20} - 1`, combined in quadrature and converted
        back by :math:`20\lg(1 + r_\mathrm{c})`: the linear form 7.5 of the first
        part and 7.8 of the second prefer, while accepting the logarithmic one
        "as the values are very small".
        """
        relative = 10.0 ** (self.standard_uncertainties_db / 20.0) - 1.0
        return 20.0 * np.log10(1.0 + np.sqrt(np.sum(relative**2, axis=0)))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each standard uncertainty and the expanded uncertainty against
        frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the expanded-uncertainty curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_reciprocity_budget

        return plot_reciprocity_budget(
            self, ax=ax, language=check_language(language), **kwargs
        )


def reciprocity_uncertainty_budget(
    frequencies_hz: ArrayLike,
    standard_uncertainties_db: Mapping[str, ArrayLike],
    *,
    field: str = "pressure",
    additional_components_db: Mapping[str, ArrayLike] | None = None,
    coverage_factor: float = _COVERAGE_FACTOR,
) -> ReciprocityUncertaintyBudget:
    r"""The uncertainty budget of a reciprocity calibration (IEC 61094-2:2009
    7.5, IEC 61094-3:2016 7.8).

    Each component is the standard uncertainty of the sensitivity level it
    causes, in dB, one value or one per frequency, keyed by the names of the
    field's Table 1 (:data:`IEC61094_2_TABLE_1`, :data:`IEC61094_3_TABLE_1`).
    Neither table is exhaustive ("Not all of the components may be relevant in
    a given calibration setup"), so a component may be left out and
    ``additional_components_db`` adds others. The components that come from
    the acoustic transfer impedance are what
    :func:`~phonometry.metrology.coupler_parameter_uncertainty` and
    :func:`~phonometry.metrology.free_field_parameter_uncertainty` return,
    keyed the same way.

    The combination is the root-sum-square at each frequency; the expanded
    uncertainty is :math:`k` times it, with :math:`k = 2` as IEC 61094-2 7.5
    states. IEC 61094-3 7.8 asks for the factor of a 95 % coverage
    probability, which is 2 for a budget of many comparable components; a
    caller whose budget is dominated by one component with few degrees of
    freedom passes its own.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param standard_uncertainties_db: The components, keyed by name, each a
        standard uncertainty in dB, one value or one per frequency.
    :param field: ``"pressure"`` (default) or ``"free_field"``.
    :param additional_components_db: Further components, by name, in the same
        form (Default: none).
    :param coverage_factor: :math:`k` (Default: 2).
    :return: The :class:`ReciprocityUncertaintyBudget`.
    :raises ValueError: for a key that is not in the field's Table 1, an
        additional component with the name of another, no component at all,
        or a value that is negative or not finite.
    """
    field = require_choice(field, "field", _FIELDS)
    frequencies = _frequency_axis(frequencies_hz)
    table = _BUDGET_TABLES[field]
    unknown = [key for key in standard_uncertainties_db if key not in table]
    if unknown:
        msg = (
            f"{unknown} are not components of Table 1 of {_STANDARDS[field]}; the "
            f"keys are {tuple(table)}. Pass other components through "
            "'additional_components_db'."
        )
        raise ValueError(msg)
    names: list[str] = []
    components: list[str] = []
    rows: list[NDArray[np.float64]] = []
    for key, row in table.items():
        if key in standard_uncertainties_db:
            names.append(key)
            components.append(row.component)
            rows.append(
                _band_column(standard_uncertainties_db[key], key, frequencies.size)
            )
    for key, value in (additional_components_db or {}).items():
        if key in names or key in table:
            msg = (
                f"The additional component {key!r} has the name of a component "
                "of Table 1; pass it under that name instead."
            )
            raise ValueError(msg)
        names.append(str(key))
        components.append(str(key))
        rows.append(_band_column(value, str(key), frequencies.size))
    if not rows:
        msg = "The budget needs at least one component."
        raise ValueError(msg)
    return ReciprocityUncertaintyBudget(
        frequencies_hz=frequencies,
        field=field,
        names=tuple(names),
        components=tuple(components),
        standard_uncertainties_db=np.vstack(rows),
        coverage_factor=require_positive(coverage_factor, "coverage_factor"),
    )

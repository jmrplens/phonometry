#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Free-field calibration of laboratory standard microphones by reciprocity
(IEC 61094-3:2016 with its corrigendum IEC 61094-3:2016/COR1:2016).

Two microphones face each other in a free field with their principal axes in
line. A current :math:`i_1` through the transmitter makes it, seen from far
enough, a simple source of strength :math:`M_{\mathrm{f},1} i_1` placed at its
acoustic centre, and the spherical wave it radiates reaches the acoustic centre
of the receiver at the distance :math:`d_{12}` as (Formula (6))

.. math::

   p_0 = \mathrm{j}\frac{\rho f}{2 d_{12}} M_{\mathrm{f},1}\,i_1\,
   \mathrm{e}^{-\mathrm{j}k d_{12}}\,\mathrm{e}^{-\alpha d_{\mathrm{m}12}}

attenuated by the air over :math:`d_{\mathrm{m}12}`, the distance the wave
actually travels between the diaphragms. The receiver turns it into
:math:`U_2 = M_{\mathrm{f},2}\,p_0`, so the product of the two free-field
sensitivities is (Formula (7))

.. math::

   M_{\mathrm{f},1} M_{\mathrm{f},2} = -\mathrm{j}\,\frac{2 d_{12}}{\rho f}\,
   \frac{U_2}{i_1}\,\mathrm{e}^{\mathrm{j}k d_{12}}\,\mathrm{e}^{\alpha d_{\mathrm{m}12}}

and three pairs give each sensitivity (Formula (8)), or one pair and the ratio
of the two sensitivities measured against an auxiliary source give both
(Formula (9), the complex sensitivity since COR1).

**The factor** :math:`-\mathrm{j}`. Formula (7) carries it and Formulas (8)
and (9) do not, although (8) is the quotient of three products of the form
(7) and (9) the product of one of them with :math:`r_{12}`. The modulus does
not see the difference, and before the corrigendum (9) gave the modulus only;
the phase does, by 45°. The library takes the factor through from Formula (7)
and Formula (D.1), which agree with each other; the defect is recorded in
``docs/ERRATA.md``.

**The attenuation of sound in air** (7.4 and Annex B). :math:`\alpha` is the
real part of the propagation coefficient, computed by the five steps of B.2
(:func:`reciprocity_air_attenuation`): ISO 9613-1 adjusted to the
quantities of IEC 61094-2, with the speed of sound at the conditions of the
calibration in the vibrational terms. Step 1 prints the last coefficient of
the saturation vapour pressure as :math:`6{,}3343\,184\,5\cdot10^3`, where
IEC 61094-2 Table F.2, which the step refers to, prints
:math:`6{,}343\,164\,5\times10^3`; the library uses the latter (an erratum).
Table B.1 tabulates the attenuation by ISO 9613-1 itself, as its text says,
and :func:`~phonometry.environment.propagation.air_absorption.air_attenuation`
reproduces every one of its 162 entries.

**The wave number** :math:`k = \omega/c` takes the speed of sound of IEC
61094-2 Annex F (:func:`~phonometry.fluids.air`), by default with the
dispersion of its NOTE to F.3: :math:`c = c_0[1 + \sum_n c\,\alpha_{\mathrm{v}n}/
(2\pi f_{\mathrm{v}n})]`, a few parts in :math:`10^5` that reach a few tenths of
a degree of phase at 20 kHz over 0,2 m. Annex B.1 points to it ("including
dispersion effects").

**Acoustic centres** (6.5 and Annex A). The distance :math:`d_{12}` is between
the acoustic centres, each given as its position on the principal axis
relative to the diaphragm, positive in front of it, a value or one per
frequency; Annex A shows them only as a figure. :func:`acoustic_centre` finds
one from the inverse-distance law, as 6.5 describes.

**The arrangement** (6.4, 7.3). :func:`check_free_field_arrangement` holds the
distance between the microphones to the ten nominal diameters 7.3 recommends
and their supporting cylinders to the twenty 6.4 recommends, and the
conditions to the domain in which Annex B states the accuracy of the
attenuation: its verdict is whether the arrangement is the recommended one.
"""

from __future__ import annotations

import math
from dataclasses import KW_ONLY, dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import require_non_negative, require_positive
from .free_field_corrections import _band_column, _frequency_axis
from .reciprocity_calibration import (
    _TRIAD_PAIRS,
    ReciprocityCalibration,
    _complex_column,
    _solved,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "AcousticCentre",
    "FreeFieldArrangementCheck",
    "FreeFieldInputUncertainties",
    "FreeFieldParameterUncertainty",
    "ReciprocityAirAttenuation",
    "acoustic_centre",
    "check_free_field_arrangement",
    "free_field_parameter_uncertainty",
    "free_field_reciprocity",
    "free_field_reciprocity_pair",
    "free_field_transfer_impedance",
    "reciprocity_air_attenuation",
]

# ---------------------------------------------------------------------------
# Annex B: the attenuation of sound in air
# ---------------------------------------------------------------------------

#: B.2: ":math:`T_{20}` = 293,15 K (20 °C)".
_T20_K = 293.15
#: B.2: "T = 273,15 + t".
_KELVIN = 273.15
#: IEC 61094-3:2016 B.2: ":math:`p_\mathrm{s,r}` = 101 325 Pa".
_REFERENCE_PRESSURE_PA = 101325.0
#: Step 1, read from IEC 61094-2:2009 Table F.2, which the step refers to; the
#: step itself prints the last coefficient as 6,3343 184 5e3, a misprint
#: (docs/ERRATA.md).
_PSV = (1.2378847e-5, -1.9121316e-2, 33.93711047, -6.3431645e3)
#: Step 2: "(1,000 62 + 3,14·10^-8·p_s + 5,6·10^-7·t^2)".
_ENHANCEMENT = (1.00062, 3.14e-8, 5.6e-7)
#: Step 3, the oxygen relaxation frequency: 24, 4,04e6, 0,2, 1e3, 3,91.
_FRO = (24.0, 4.04e6, 0.2, 1.0e3, 3.91)
#: Step 3, the nitrogen relaxation frequency: 9, 28e3, -4,170.
_FRN = (9.0, 28.0e3, -4.170)
#: Step 4, classical and rotational absorption: 18,42e-12.
_CLASSICAL = 18.42e-12
#: Step 4, vibrational absorption of oxygen: 4,3778 and 2 239,1 K.
_VIB_O = (4.3778, 2239.1)
#: Step 4, vibrational absorption of nitrogen: 36,6624 and 3 352,0 K.
_VIB_N = (36.6624, 3352.0)
#: B.2: "The tabulated values are expressed in decibels per metre as 8,686
#: alpha"; 20 lg e, which 8,686 rounds.
_NP_TO_DB = 20.0 / math.log(10.0)

#: B.2: the accuracy of ±10 % holds within "Air temperature: -20 °C to 50 °C",
#: "Static pressure: less than 200 kPa", "Molar fraction of water vapour:
#: 0,5 × 10^-3 to 50 × 10^-3" and "Frequency-to-pressure ratio: 0,4 Hz/kPa to
#: 10^4 Hz/kPa".
_ACCURACY_TEMPERATURE_C = (-20.0, 50.0)
_ACCURACY_PRESSURE_PA = 200_000.0
_ACCURACY_WATER_FRACTION = (0.5e-3, 50e-3)
_ACCURACY_FREQUENCY_PER_KPA = (0.4, 1.0e4)


@dataclass(frozen=True)
class ReciprocityAirAttenuation:
    r"""The attenuation of sound in air of a free-field reciprocity calibration
    (IEC 61094-3:2016 7.4 and Annex B), and the speed of sound with dispersion
    (IEC 61094-2:2009 F.3, NOTE).

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar temperature_c: :math:`t`, in °C.
    :ivar static_pressure_pa: :math:`p_\mathrm{s}`, in Pa.
    :ivar relative_humidity_percent: :math:`H`, in %.
    :ivar water_vapour_mole_fraction: :math:`x_\mathrm{w}` (Step 2).
    :ivar oxygen_relaxation_hz: :math:`f_\mathrm{rO}`, in Hz (Step 3).
    :ivar nitrogen_relaxation_hz: :math:`f_\mathrm{rN}`, in Hz (Step 3).
    :ivar speed_of_sound: :math:`c`, the zero-frequency speed of sound of
        IEC 61094-2 Formula (F.2) at the conditions, in m/s; the one Step 4
        divides by.
    :ivar classical_np_per_m: :math:`\alpha_\mathrm{cl} + \alpha_\mathrm{rot}`,
        in Np/m.
    :ivar oxygen_np_per_m: :math:`\alpha_\mathrm{vib,O}`, in Np/m.
    :ivar nitrogen_np_per_m: :math:`\alpha_\mathrm{vib,N}`, in Np/m.
    """

    frequencies_hz: NDArray[np.float64]
    temperature_c: float
    static_pressure_pa: float
    relative_humidity_percent: float
    water_vapour_mole_fraction: float
    oxygen_relaxation_hz: float
    nitrogen_relaxation_hz: float
    speed_of_sound: float
    classical_np_per_m: NDArray[np.float64]
    oxygen_np_per_m: NDArray[np.float64]
    nitrogen_np_per_m: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, or columns of another length.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in ("classical_np_per_m", "oxygen_np_per_m", "nitrogen_np_per_m"):
            column = _band_column(getattr(self, name), name, frequencies.size)
            object.__setattr__(self, name, read_only(column.copy()))

    @property
    def attenuation_np_per_m(self) -> NDArray[np.float64]:
        r""":math:`\alpha = \alpha_\mathrm{cl} + \alpha_\mathrm{rot}
        + \alpha_\mathrm{vib,O} + \alpha_\mathrm{vib,N}` (Step 5), in Np/m.
        """
        return self.classical_np_per_m + self.oxygen_np_per_m + self.nitrogen_np_per_m

    @property
    def attenuation_db_per_m(self) -> NDArray[np.float64]:
        r""":math:`20\lg(\mathrm{e})\,\alpha`, in dB/m, the quantity of Table B.1."""
        return _NP_TO_DB * self.attenuation_np_per_m

    @property
    def dispersive_speed_of_sound(self) -> NDArray[np.float64]:
        r"""The speed of sound at each frequency, in m/s (IEC 61094-2:2009 F.3,
        NOTE):

        .. math::

           c = c_0\left[1 + \sum_n \frac{c\,\alpha_{\mathrm{v}n}}{2\pi f_{\mathrm{v}n}}\right]

        over oxygen and nitrogen, where :math:`c\,\alpha_{\mathrm{v}n}` does not
        depend on :math:`c` because Step 4 divides by it.
        """
        c0 = self.speed_of_sound
        relative = c0 * (
            self.oxygen_np_per_m / (2.0 * math.pi * self.oxygen_relaxation_hz)
            + self.nitrogen_np_per_m / (2.0 * math.pi * self.nitrogen_relaxation_hz)
        )
        return c0 * (1.0 + relative)

    @property
    def within_stated_accuracy(self) -> NDArray[np.bool_]:
        """Whether each frequency is inside the domain in which B.2 states the
        ±10 % accuracy of the attenuation.
        """
        conditions = (
            _ACCURACY_TEMPERATURE_C[0]
            <= self.temperature_c
            <= _ACCURACY_TEMPERATURE_C[1]
            and self.static_pressure_pa < _ACCURACY_PRESSURE_PA
            and _ACCURACY_WATER_FRACTION[0]
            <= self.water_vapour_mole_fraction
            <= _ACCURACY_WATER_FRACTION[1]
        )
        per_kpa = self.frequencies_hz / (self.static_pressure_pa / 1000.0)
        return np.asarray(
            conditions
            & (per_kpa >= _ACCURACY_FREQUENCY_PER_KPA[0])
            & (per_kpa <= _ACCURACY_FREQUENCY_PER_KPA[1]),
            dtype=np.bool_,
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the attenuation in dB/m and its three parts against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the total-attenuation curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_air_attenuation

        return plot_air_attenuation(
            self, ax=ax, language=check_language(language), **kwargs
        )


def reciprocity_air_attenuation(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
) -> ReciprocityAirAttenuation:
    r"""The air attenuation coefficient of a free-field reciprocity calibration
    (IEC 61094-3:2016 B.2, Steps 1 to 5).

    .. math::

       \alpha = f^2\left[18{,}42\times10^{-12}\left(\frac{p_\mathrm{s}}{p_\mathrm{s,r}}\right)^{-1}
       \left(\frac{T}{T_{20}}\right)^{1/2}
       + \left(\frac{T}{T_{20}}\right)^{-2}\left(
       \frac{4{,}3778}{c}\frac{\mathrm{e}^{-2239{,}1/T}}{f_\mathrm{rO} + f^2/f_\mathrm{rO}}
       + \frac{36{,}6624}{c}\frac{\mathrm{e}^{-3352{,}0/T}}{f_\mathrm{rN} + f^2/f_\mathrm{rN}}
       \right)\right]

    in Np/m, with the relaxation frequencies of Step 3 from the water vapour
    mole fraction of Steps 1 and 2, and :math:`c` the speed of sound of IEC
    61094-2 Formula (F.2) at the conditions. B.2 estimates the accuracy at
    ±10 % within -20 °C to 50 °C, below 200 kPa, for
    :math:`0{,}5\times10^{-3} \le x_\mathrm{w} \le 50\times10^{-3}` and a
    frequency-to-pressure ratio of 0,4 Hz/kPa to :math:`10^4` Hz/kPa
    (:attr:`ReciprocityAirAttenuation.within_stated_accuracy`).

    Step 1 is computed with the coefficient of IEC 61094-2 Table F.2, which it
    refers to, not with the one it prints (``docs/ERRATA.md``).

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param temperature_c: :math:`t`, in °C.
    :param static_pressure_pa: :math:`p_\mathrm{s}`, in Pa.
    :param relative_humidity_percent: :math:`H`, in %.
    :return: The :class:`ReciprocityAirAttenuation`.
    :raises ValueError: for frequencies that are not positive and increasing,
        a pressure that is not positive, a humidity outside 0 % to 100 %, or a
        temperature at or below absolute zero.
    """
    from ..fluids import air

    frequencies = _frequency_axis(frequencies_hz)
    pressure = require_positive(static_pressure_pa, "static_pressure_pa")
    gas = air(
        temperature_c=temperature_c,
        static_pressure_pa=pressure,
        relative_humidity_percent=relative_humidity_percent,
    )
    t = float(temperature_c)
    kelvin = _KELVIN + t
    a = _PSV
    saturation = math.exp(a[0] * kelvin**2 + a[1] * kelvin + a[2] + a[3] / kelvin)
    e = _ENHANCEMENT
    water = (
        relative_humidity_percent
        / 100.0
        * (saturation / pressure)
        * (e[0] + e[1] * pressure + e[2] * t**2)
    )
    ratio = pressure / _REFERENCE_PRESSURE_PA
    theta = kelvin / _T20_K
    o = _FRO
    oxygen_relaxation = ratio * (
        o[0] + o[1] * water * (o[2] + o[3] * water) / (o[4] + o[3] * water)
    )
    n = _FRN
    nitrogen_relaxation = (
        ratio
        * theta**-0.5
        * (n[0] + n[1] * water * math.exp(n[2] * (theta ** (-1.0 / 3.0) - 1.0)))
    )
    c = gas.speed_of_sound
    f2 = frequencies**2
    classical = _CLASSICAL * f2 / ratio * theta**0.5
    oxygen = (
        _VIB_O[0]
        * f2
        / c
        / (oxygen_relaxation + f2 / oxygen_relaxation)
        * theta**-2.0
        * math.exp(-_VIB_O[1] / kelvin)
    )
    nitrogen = (
        _VIB_N[0]
        * f2
        / c
        / (nitrogen_relaxation + f2 / nitrogen_relaxation)
        * theta**-2.0
        * math.exp(-_VIB_N[1] / kelvin)
    )
    return ReciprocityAirAttenuation(
        frequencies_hz=frequencies,
        temperature_c=t,
        static_pressure_pa=pressure,
        relative_humidity_percent=float(relative_humidity_percent),
        water_vapour_mole_fraction=water,
        oxygen_relaxation_hz=oxygen_relaxation,
        nitrogen_relaxation_hz=nitrogen_relaxation,
        speed_of_sound=c,
        classical_np_per_m=classical,
        oxygen_np_per_m=oxygen,
        nitrogen_np_per_m=nitrogen,
    )


# ---------------------------------------------------------------------------
# Clause 5: the products and the sensitivities
# ---------------------------------------------------------------------------


def _medium(
    frequencies: NDArray[np.float64],
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    *,
    dispersion: bool,
) -> tuple[float, NDArray[np.float64], NDArray[np.float64]]:
    r""":math:`\rho`, the wave number :math:`k` and :math:`\alpha` at each
    frequency.
    """
    from ..fluids import air

    density = air(
        temperature_c=temperature_c,
        static_pressure_pa=static_pressure_pa,
        relative_humidity_percent=relative_humidity_percent,
    ).density
    attenuation = reciprocity_air_attenuation(
        frequencies,
        temperature_c=temperature_c,
        static_pressure_pa=static_pressure_pa,
        relative_humidity_percent=relative_humidity_percent,
    )
    speed = (
        attenuation.dispersive_speed_of_sound
        if dispersion
        else np.full(frequencies.size, attenuation.speed_of_sound)
    )
    return (
        density,
        2.0 * math.pi * frequencies / speed,
        attenuation.attenuation_np_per_m,
    )


def _positions(
    acoustic_centres_m: Sequence[ArrayLike], count: int, microphones: int
) -> list[NDArray[np.float64]]:
    """The acoustic centre of each microphone at each frequency."""
    if len(acoustic_centres_m) != microphones:
        msg = (
            f"'acoustic_centres_m' must hold one entry per microphone ({microphones})."
        )
        raise ValueError(msg)
    return [
        _band_column(value, f"acoustic_centres_m[{index}]", count)
        for index, value in enumerate(acoustic_centres_m)
    ]


def _product(
    frequencies: NDArray[np.float64],
    electrical: NDArray[np.complex128],
    centres: NDArray[np.float64],
    diaphragms: float,
    medium: tuple[float, NDArray[np.float64], NDArray[np.float64]],
) -> NDArray[np.complex128]:
    r"""Formula (7): :math:`-\mathrm{j}\,(2d/\rho f)\,Z_\mathrm{e}\,
    \mathrm{e}^{\mathrm{j}kd}\,\mathrm{e}^{\alpha d_\mathrm{m}}`.
    """
    density, wavenumber, attenuation = medium
    if np.any(centres <= 0.0):
        msg = (
            "The acoustic centres leave no distance between them: the distance "
            "between the diaphragms has to exceed the sum of the two positions."
        )
        raise ValueError(msg)
    return (
        -1.0j
        * 2.0
        * centres
        / (density * frequencies)
        * electrical
        * np.exp(1.0j * wavenumber * centres)
        * np.exp(attenuation * diaphragms)
    )


def _distances(diaphragm_distances_m: Sequence[float], count: int) -> list[float]:
    """The distances between the diaphragms, one per pair."""
    if len(diaphragm_distances_m) != count:
        msg = f"'diaphragm_distances_m' must hold one distance per pair ({count})."
        raise ValueError(msg)
    return [
        require_positive(value, f"diaphragm_distances_m[{index}]")
        for index, value in enumerate(diaphragm_distances_m)
    ]


def free_field_reciprocity(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedances_ohm: Sequence[ArrayLike],
    *,
    diaphragm_distances_m: Sequence[float],
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0, 0.0),
    dispersion: bool = True,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration:
    r"""The free-field sensitivities of three microphones calibrated in pairs
    (IEC 61094-3:2016 5.7.1, Formula (8)).

    Each pair gives the product of Formula (7), with :math:`d_{ij}` the
    distance between the acoustic centres and :math:`d_{\mathrm{m}ij}` that
    between the diaphragms; facing each other, :math:`d_{ij} =
    d_{\mathrm{m}ij} - x_i - x_j` with :math:`x` the position of each acoustic
    centre in front of its diaphragm. The three are solved as Formula (8) asks:

    .. math::

       M_{\mathrm{f},1} = \left(-\mathrm{j}\,\frac{2}{\rho f}\,
       \frac{d_{12}d_{31}}{d_{23}}\,\frac{Z_{\mathrm{e},12}Z_{\mathrm{e},31}}
       {Z_{\mathrm{e},23}}\,\mathrm{e}^{\mathrm{j}k(d_{12}+d_{31}-d_{23})}\,
       \mathrm{e}^{\alpha(d_{\mathrm{m}12}+d_{\mathrm{m}31}-d_{\mathrm{m}23})}\right)^{1/2}

    with the factor :math:`-\mathrm{j}` that Formula (7) carries and the
    printed Formula (8) drops (module docstring).

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param electrical_transfer_impedances_ohm: :math:`Z_{\mathrm{e},12}`,
        :math:`Z_{\mathrm{e},23}` and :math:`Z_{\mathrm{e},31}`, complex, in Ω.
    :param diaphragm_distances_m: :math:`d_{\mathrm{m}12}`,
        :math:`d_{\mathrm{m}23}` and :math:`d_{\mathrm{m}31}`, in m.
    :param temperature_c: The temperature of the air, in °C.
    :param static_pressure_pa: The static pressure, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param acoustic_centres_m: The acoustic centre of microphones 1, 2 and 3,
        each relative to its diaphragm on the principal axis, positive in
        front, in m, one value or one per frequency (Default: the centres of
        the diaphragms, which Annex A allows at sufficiently remote points).
    :param dispersion: Whether :math:`k` takes the speed of sound with the
        dispersion of IEC 61094-2 F.3 (Default: ``True``).
    :param corrections_db: Corrections added to every level (Default: none).
    :param expanded_uncertainty_db: The expanded uncertainty, in dB (Default:
        ``None``).
    :return: The :class:`~phonometry.metrology.ReciprocityCalibration`.
    :raises ValueError: for other than three pairs, distances that are not
        positive or that the acoustic centres use up, or values that are zero
        or not finite.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    if len(electrical_transfer_impedances_ohm) != len(_TRIAD_PAIRS):
        msg = "Three pairs are needed, in the order 12, 23, 31 (Formula (8))."
        raise ValueError(msg)
    distances = _distances(diaphragm_distances_m, len(_TRIAD_PAIRS))
    x1, x2, x3 = _positions(acoustic_centres_m, count, 3)
    medium = _medium(
        frequencies,
        temperature_c,
        static_pressure_pa,
        relative_humidity_percent,
        dispersion=dispersion,
    )
    centres = (distances[0] - x1 - x2, distances[1] - x2 - x3, distances[2] - x3 - x1)
    products = [
        _product(
            frequencies,
            _complex_column(
                value, f"electrical_transfer_impedances_ohm[{pair}]", count
            ),
            centre,
            distance,
            medium,
        )
        for pair, value, centre, distance in zip(
            _TRIAD_PAIRS,
            electrical_transfer_impedances_ohm,
            centres,
            distances,
            strict=True,
        )
    ]
    return _solved(
        frequencies,
        products,
        None,
        field="free_field",
        corrections_db=corrections_db,
        expanded_uncertainty_db=expanded_uncertainty_db,
    )


def free_field_reciprocity_pair(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedance_ohm: ArrayLike,
    sensitivity_ratio: ArrayLike,
    *,
    diaphragm_distance_m: float,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0),
    dispersion: bool = True,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration:
    r"""The complex free-field sensitivities of two microphones and an
    auxiliary sound source (IEC 61094-3:2016 5.1.3 and 5.7.2, Formula (9) as
    corrected by COR1).

    .. math::

       M_{\mathrm{f},1} = \left(-\mathrm{j}\,r_{12}\,\frac{2 d_{12}}{\rho f}\,
       Z_{\mathrm{e},12}\,\mathrm{e}^{\mathrm{j}k d_{12}}\,
       \mathrm{e}^{\alpha d_{\mathrm{m}12}}\right)^{1/2}

    COR1 replaces "modulus of the" by "complex" in 5.7.2, so the formula gives
    the complex sensitivity; the factor :math:`-\mathrm{j}` is that of
    Formula (7), which the printed Formula (9) drops (module docstring).

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param electrical_transfer_impedance_ohm: :math:`Z_{\mathrm{e},12}`,
        complex, in Ω.
    :param sensitivity_ratio: :math:`r_{12} = M_{\mathrm{f},1}/M_{\mathrm{f},2}`,
        complex, measured against the auxiliary source.
    :param diaphragm_distance_m: :math:`d_{\mathrm{m}12}`, in m.
    :param temperature_c: The temperature of the air, in °C.
    :param static_pressure_pa: The static pressure, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param acoustic_centres_m: The acoustic centres of the two microphones,
        positive in front of the diaphragm, in m (Default: the diaphragms).
    :param dispersion: Whether :math:`k` includes dispersion (Default:
        ``True``).
    :param corrections_db: Corrections added to both levels (Default: none).
    :param expanded_uncertainty_db: The expanded uncertainty, in dB (Default:
        ``None``).
    :return: The :class:`~phonometry.metrology.ReciprocityCalibration`, of two
        microphones.
    :raises ValueError: for a distance that is not positive or that the
        acoustic centres use up, or values that are zero or not finite.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    distance = require_positive(diaphragm_distance_m, "diaphragm_distance_m")
    x1, x2 = _positions(acoustic_centres_m, count, 2)
    medium = _medium(
        frequencies,
        temperature_c,
        static_pressure_pa,
        relative_humidity_percent,
        dispersion=dispersion,
    )
    product = _product(
        frequencies,
        _complex_column(
            electrical_transfer_impedance_ohm,
            "electrical_transfer_impedance_ohm",
            count,
        ),
        distance - x1 - x2,
        distance,
        medium,
    )
    return _solved(
        frequencies,
        [product],
        sensitivity_ratio,
        field="free_field",
        corrections_db=corrections_db,
        expanded_uncertainty_db=expanded_uncertainty_db,
    )


def free_field_transfer_impedance(
    frequencies_hz: ArrayLike,
    sensitivity_1_v_per_pa: ArrayLike,
    sensitivity_2_v_per_pa: ArrayLike,
    *,
    diaphragm_distance_m: float,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0),
    dispersion: bool = True,
) -> NDArray[np.complex128]:
    r"""The electrical transfer impedance two microphones of known free-field
    sensitivity give (IEC 61094-3:2016 D.4.2, Formula (D.1)).

    .. math::

       \frac{U_2}{i_1} = \mathrm{j}\,\frac{\rho f}{2 d_{12}}\,M_{\mathrm{f},1}
       M_{\mathrm{f},2}\,\mathrm{e}^{-\mathrm{j}k d_{12}}\,\mathrm{e}^{-\alpha d_{\mathrm{m}12}}

    Formula (7) turned round. D.4.2 uses it to fill the frequency range below
    the lowest measured frequency before a transformation to the time domain,
    with the free-field sensitivities taken there from the pressure
    sensitivity and the scattering factor (Formula (4)).

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param sensitivity_1_v_per_pa: :math:`M_{\mathrm{f},1}`, complex, in V/Pa.
    :param sensitivity_2_v_per_pa: :math:`M_{\mathrm{f},2}`, complex, in V/Pa.
    :param diaphragm_distance_m: :math:`d_{\mathrm{m}12}`, in m.
    :param temperature_c: The temperature of the air, in °C.
    :param static_pressure_pa: The static pressure, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param acoustic_centres_m: The two acoustic centres, in m (Default: the
        diaphragms).
    :param dispersion: Whether :math:`k` includes dispersion (Default:
        ``True``).
    :return: :math:`U_2/i_1`, complex, in Ω, at each frequency.
    :raises ValueError: for a distance that is not positive or that the
        acoustic centres use up, or values that are zero or not finite.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    distance = require_positive(diaphragm_distance_m, "diaphragm_distance_m")
    x1, x2 = _positions(acoustic_centres_m, count, 2)
    medium = _medium(
        frequencies,
        temperature_c,
        static_pressure_pa,
        relative_humidity_percent,
        dispersion=dispersion,
    )
    first = _complex_column(sensitivity_1_v_per_pa, "sensitivity_1_v_per_pa", count)
    second = _complex_column(sensitivity_2_v_per_pa, "sensitivity_2_v_per_pa", count)
    unit = _product(
        frequencies,
        np.ones(count, dtype=np.complex128),
        distance - x1 - x2,
        distance,
        medium,
    )
    return first * second / unit


# ---------------------------------------------------------------------------
# Clause 6.5: the acoustic centre
# ---------------------------------------------------------------------------

#: The fewest distances a straight line can be fitted through with a residual.
_FEWEST_DISTANCES = 3


@dataclass(frozen=True)
class AcousticCentre:
    r"""The position of the acoustic centre of a microphone from the
    inverse-distance law (IEC 61094-3:2016 6.5).

    :ivar distances_m: The distances from the reference point of the
        microphone to the observation points, in m.
    :ivar inverse_readings: :math:`1/|p|`, corrected for the attenuation of
        sound, at each distance, in the reciprocal of the unit the pressures
        were given in.
    :ivar slope: The slope of the straight line fitted by least squares.
    :ivar intercept: Its intercept at zero distance.
    """

    distances_m: NDArray[np.float64]
    inverse_readings: NDArray[np.float64]
    slope: float
    intercept: float

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for columns of different lengths.
        """
        distances = np.array(self.distances_m, dtype=np.float64).reshape(-1)
        inverse = np.array(self.inverse_readings, dtype=np.float64).reshape(-1)
        if distances.size != inverse.size:
            msg = "AcousticCentre: one inverse pressure per distance."
            raise ValueError(msg)
        object.__setattr__(self, "distances_m", read_only(distances))
        object.__setattr__(self, "inverse_readings", read_only(inverse))

    @property
    def position_m(self) -> float:
        r"""The acoustic centre relative to the reference point, in m: where the
        fitted line crosses the axis, :math:`-b/a`; positive towards the
        observation points, which for a reference point on the diaphragm is in
        front of it (Annex A).
        """
        return -self.intercept / self.slope

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the inverse pressures, the fitted line and where it crosses the
        axis.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the fitted line.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_acoustic_centre

        return plot_acoustic_centre(
            self, ax=ax, language=check_language(language), **kwargs
        )


def acoustic_centre(
    distances_m: ArrayLike,
    sound_pressures_pa: ArrayLike,
    *,
    attenuation_np_per_m: float = 0.0,
) -> AcousticCentre:
    r"""The position of the acoustic centre of a microphone used as a source
    (IEC 61094-3:2016 6.5).

    "In a limited region of the far field, the sound pressure, corrected for
    the effect of sound attenuation, will follow the 1/r-law, r being referred
    now to the acoustic centre of the microphone. Thus, when plotting the
    inverse value of the measured sound pressure as a function of the distance
    from an arbitrarily chosen reference point of the microphone (most
    conveniently the centre of the diaphragm), a straight line can be fitted
    (e.g. by the methods of least squares) through the plotted values. The
    intersection of this straight line and the abscissa axis determines the
    position of the acoustic centre relative to the reference point."

    The pressures may be in any unit proportional to the sound pressure, such
    as the receiver's output voltage at one frequency; each is multiplied by
    :math:`\mathrm{e}^{\alpha r}` before it is inverted.

    :param distances_m: The distances from the reference point, in m, at least
        three, positive.
    :param sound_pressures_pa: The modulus of the sound pressure at each, in Pa
        or any proportional unit, positive.
    :param attenuation_np_per_m: :math:`\alpha` at the frequency, in Np/m
        (Default: 0), from :func:`reciprocity_air_attenuation`.
    :return: The :class:`AcousticCentre`.
    :raises ValueError: for fewer than three distances, columns of different
        lengths, values that are not positive and finite, or distances that
        are all the same.
    """
    distances = np.asarray(distances_m, dtype=np.float64).reshape(-1)
    pressures = np.abs(np.asarray(sound_pressures_pa, dtype=np.float64)).reshape(-1)
    if distances.size < _FEWEST_DISTANCES or distances.size != pressures.size:
        msg = "One pressure per distance is needed, at three distances or more."
        raise ValueError(msg)
    for name, value in (("distances_m", distances), ("sound_pressures_pa", pressures)):
        if not np.all(np.isfinite(value)) or np.any(value <= 0.0):
            msg = f"'{name}' must be positive and finite."
            raise ValueError(msg)
    if np.ptp(distances) <= 0.0:
        msg = "'distances_m' must not all be the same."
        raise ValueError(msg)
    alpha = require_non_negative(attenuation_np_per_m, "attenuation_np_per_m")
    inverse = 1.0 / (pressures * np.exp(alpha * distances))
    slope, intercept = np.polyfit(distances, inverse, 1)
    return AcousticCentre(
        distances_m=distances,
        inverse_readings=inverse,
        slope=float(slope),
        intercept=float(intercept),
    )


# ---------------------------------------------------------------------------
# Clauses 6.4 and 7.3: the arrangement
# ---------------------------------------------------------------------------

#: 7.3: "the distance between the two microphones during the calibration
#: should be greater than ten times the nominal diameter of the microphones".
_DISTANCE_DIAMETERS = 10.0
#: 6.4: "A minimum length of twenty times the diameter of the microphone ...
#: is recommended" for the cylinder the microphone is attached to.
_SUPPORT_DIAMETERS = 20.0
#: Annex A: "For distances in the range 150 mm to 500 mm, normally used when
#: carrying out reciprocity calibrations, the values given in the bibliography
#: and shown in Figure A.1 may be applied."
_ANNEX_A_RANGE_M = (0.150, 0.500)


@dataclass(frozen=True)
class FreeFieldArrangementCheck:
    """Whether a free-field reciprocity arrangement is the one IEC 61094-3:2016
    recommends.

    6.4 asks for a distance "great enough" and supporting cylinders "long
    compared to the diameter", and puts numbers on both only as
    recommendations: ten nominal diameters between the microphones (7.3) and
    twenty along the cylinder (6.4). The verdict holds the arrangement to those
    numbers, and the conditions to the domain in which B.2 states the accuracy
    of the attenuation; an arrangement that fails it is not forbidden, but
    falls outside what the standard recommends and what its uncertainty
    figures assume.

    Built by :func:`check_free_field_arrangement`.

    :ivar diaphragm_distances_m: The distances between the microphones, in m.
    :ivar microphone_diameter_m: The nominal diameter of the microphones, in m.
    :ivar distances_ok: Every distance is greater than ten nominal diameters,
        as 7.3 recommends.
    :ivar support_length_m: The length of the cylinder each microphone is
        attached to, in m, or ``None``.
    :ivar support_ok: It is at least twenty diameters, as 6.4 recommends, or
        ``None``.
    :ivar annex_a_range: Every distance is within 150 mm to 500 mm, where Annex
        A allows the published acoustic centres. Advisory: it does not enter
        :attr:`passes`.
    :ivar attenuation_accuracy: The conditions and every frequency are within
        the domain in which B.2 states the accuracy of the attenuation.
    """

    diaphragm_distances_m: tuple[float, ...]
    microphone_diameter_m: float
    distances_ok: bool
    support_length_m: float | None
    support_ok: bool | None
    annex_a_range: bool
    attenuation_accuracy: bool

    @property
    def passes(self) -> bool:
        """The verdict: the distances and the supports are as 7.3 and 6.4
        recommend, and the conditions are where B.2 states the accuracy of
        the attenuation.
        """
        return (
            self.distances_ok
            and self.support_ok is not False
            and self.attenuation_accuracy
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a FreeFieldArrangementCheck has no truth value; read '.passes'"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each distance against ten diameters and the range of Annex A.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh`.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_free_field_arrangement

        return plot_free_field_arrangement(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_free_field_arrangement(
    frequencies_hz: ArrayLike,
    *,
    diaphragm_distances_m: Sequence[float],
    microphone_diameter_m: float,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    support_length_m: float | None = None,
) -> FreeFieldArrangementCheck:
    """Is this the free-field arrangement IEC 61094-3:2016 recommends?

    7.3 recommends a distance between the microphones greater than ten times
    their nominal diameter, "to ensure an approximately plane wave in a
    suitable region around the receiving microphone"; 6.4 recommends
    attaching each microphone to a cylinder of its diameter at least twenty
    diameters long; and B.2 states the accuracy of the attenuation within a
    domain of temperature, static pressure, water vapour and
    frequency-to-pressure ratio. Annex A allows the published acoustic centres
    between 150 mm and 500 mm, which is reported without entering the verdict.

    :param frequencies_hz: The frequencies of the calibration, in Hz.
    :param diaphragm_distances_m: The distance of each pair, in m.
    :param microphone_diameter_m: The nominal diameter of the microphones, in m
        (23,77 mm for LS1, 13,2 mm for LS2a: dimension A of Table C.1 of IEC
        61094-2).
    :param temperature_c: The temperature, in °C.
    :param static_pressure_pa: The static pressure, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param support_length_m: The length of the supporting cylinder, in m, or
        ``None`` if not known.
    :return: The :class:`FreeFieldArrangementCheck`.
    :raises ValueError: for no distance, or a distance, diameter or length that
        is not positive.
    """
    distances = tuple(
        require_positive(value, f"diaphragm_distances_m[{index}]")
        for index, value in enumerate(diaphragm_distances_m)
    )
    if not distances:
        msg = "'diaphragm_distances_m' must hold at least one distance."
        raise ValueError(msg)
    diameter = require_positive(microphone_diameter_m, "microphone_diameter_m")
    support_ok = None
    if support_length_m is not None:
        support_ok = (
            require_positive(support_length_m, "support_length_m")
            >= _SUPPORT_DIAMETERS * diameter
        )
    attenuation = reciprocity_air_attenuation(
        frequencies_hz,
        temperature_c=temperature_c,
        static_pressure_pa=static_pressure_pa,
        relative_humidity_percent=relative_humidity_percent,
    )
    return FreeFieldArrangementCheck(
        diaphragm_distances_m=distances,
        microphone_diameter_m=diameter,
        distances_ok=all(d > _DISTANCE_DIAMETERS * diameter for d in distances),
        support_length_m=None if support_length_m is None else float(support_length_m),
        support_ok=support_ok,
        annex_a_range=all(
            _ANNEX_A_RANGE_M[0] <= d <= _ANNEX_A_RANGE_M[1] for d in distances
        ),
        attenuation_accuracy=bool(np.all(attenuation.within_stated_accuracy)),
    )


# ---------------------------------------------------------------------------
# Clause 7.8: one component at a time
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FreeFieldParameterUncertainty:
    """The standard uncertainty of a free-field sensitivity level that each
    parameter of the acoustic transfer impedance contributes (IEC
    61094-3:2016 7.8).

    Built by :func:`free_field_parameter_uncertainty`; ready to pass to
    :func:`~phonometry.metrology.reciprocity_uncertainty_budget` with
    ``field="free_field"``.

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar components_db: The component of each parameter, keyed by its name in
        :data:`~phonometry.metrology.IEC61094_3_TABLE_1`, in dB at each
        frequency.
    :ivar microphone: The microphone whose level they are for, 1, 2 or 3.
    """

    frequencies_hz: NDArray[np.float64]
    components_db: Mapping[str, NDArray[np.float64]]
    microphone: int

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, or a component that is not one finite non-negative
            value per frequency.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        components = {}
        for name, value in self.components_db.items():
            column = np.array(value, dtype=np.float64).reshape(-1)
            if (
                column.size != frequencies.size
                or not np.all(np.isfinite(column))
                or np.any(column < 0.0)
            ):
                msg = (
                    f"FreeFieldParameterUncertainty: 'components_db[{name!r}]' must "
                    "be one finite, non-negative value per frequency."
                )
                raise ValueError(msg)
            components[str(name)] = read_only(column)
        object.__setattr__(self, "components_db", MappingProxyType(components))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each component against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the first component's curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_parameter_uncertainty

        return plot_parameter_uncertainty(
            self, ax=ax, language=check_language(language), field="free_field", **kwargs
        )


#: For each microphone, the pairs that multiply in Formula (8) and the one that
#: divides: :math:`M_1^2 = P_{12} P_{31}/P_{23}`.
_SIGNS: Mapping[int, Mapping[str, float]] = MappingProxyType(
    {
        1: MappingProxyType({"12": 1.0, "23": -1.0, "31": 1.0}),
        2: MappingProxyType({"12": 1.0, "23": 1.0, "31": -1.0}),
        3: MappingProxyType({"12": -1.0, "23": 1.0, "31": 1.0}),
    }
)


def _pair_levels(
    frequencies: NDArray[np.float64],
    distances: Sequence[float],
    centres: Sequence[NDArray[np.float64]],
    conditions: tuple[float, float, float],
    *,
    attenuation_scale: float,
    dispersion: bool,
) -> dict[str, NDArray[np.float64]]:
    r""":math:`20\lg|P_{ij}/Z_{\mathrm{e},ij}|` of each pair, the part of the
    product the measurement does not fix.
    """
    density, wavenumber, attenuation = _medium(
        frequencies, *conditions, dispersion=dispersion
    )
    medium = (density, wavenumber, attenuation * attenuation_scale)
    pairs = {"12": (0, 1), "23": (1, 2), "31": (2, 0)}
    unit = np.ones(frequencies.size, dtype=np.complex128)
    return {
        key: 20.0
        * np.log10(
            np.abs(
                _product(
                    frequencies,
                    unit,
                    distances[index] - centres[i] - centres[j],
                    distances[index],
                    medium,
                )
            )
        )
        for index, (key, (i, j)) in enumerate(pairs.items())
    }


@dataclass(frozen=True)
class FreeFieldInputUncertainties:
    r"""The standard uncertainty of each input quantity of the free-field
    acoustic transfer impedance that :func:`free_field_parameter_uncertainty`
    can move: the distance, the three conditions and the air attenuation, rows
    Table 1 of IEC 61094-3:2016 lists under "Acoustic transfer impedance", and
    the acoustic centres of its "Microphone parameters".

    Each one left at zero contributes no component.

    :param u_distance_m: Of each distance between the diaphragms, in m.
    :param u_acoustic_centre_m: Of each acoustic centre, in m, one value or one
        per frequency (Annex A puts it under 2 mm below the resonance
        frequency, as a bound). It is held as a read-only float64 copy.
    :param u_static_pressure_pa: Of the static pressure, in Pa.
    :param u_temperature_k: Of the temperature, in K.
    :param u_relative_humidity_percent: Of the relative humidity, in
        percentage points.
    :param u_air_attenuation_ratio: Of the attenuation coefficient, as a
        fraction of it. B.2 estimates its accuracy at ±10 %, a standard
        uncertainty of :math:`0{,}1/\sqrt{3}` for a rectangular distribution.
    :raises ValueError: for an uncertainty that is negative or not finite, or
        acoustic-centre uncertainties that are not one value or one column.
    """

    _: KW_ONLY
    u_distance_m: float = 0.0
    u_acoustic_centre_m: ArrayLike = 0.0
    u_static_pressure_pa: float = 0.0
    u_temperature_k: float = 0.0
    u_relative_humidity_percent: float = 0.0
    u_air_attenuation_ratio: float = 0.0

    def __post_init__(self) -> None:
        """Refuse an uncertainty that is negative or not finite.

        :raises ValueError: for any, or acoustic-centre uncertainties of more
            than one dimension.
        """
        for name in (
            "u_distance_m",
            "u_static_pressure_pa",
            "u_temperature_k",
            "u_relative_humidity_percent",
            "u_air_attenuation_ratio",
        ):
            object.__setattr__(
                self, name, require_non_negative(getattr(self, name), name)
            )
        centre = np.array(self.u_acoustic_centre_m, dtype=np.float64)
        if centre.ndim > 1 or not np.all(np.isfinite(centre)) or np.any(centre < 0.0):
            msg = (
                "'u_acoustic_centre_m' must be one finite, non-negative value or "
                "one per frequency."
            )
            raise ValueError(msg)
        object.__setattr__(self, "u_acoustic_centre_m", read_only(centre))


def free_field_parameter_uncertainty(
    frequencies_hz: ArrayLike,
    uncertainties: FreeFieldInputUncertainties,
    *,
    diaphragm_distances_m: Sequence[float],
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    acoustic_centres_m: Sequence[ArrayLike] = (0.0, 0.0, 0.0),
    microphone: int = 1,
    dispersion: bool = True,
) -> FreeFieldParameterUncertainty:
    r"""The uncertainty components of the free-field acoustic transfer
    impedance, one parameter at a time (IEC 61094-3:2016 7.8).

    As in IEC 61094-2 7.5, each parameter with a non-zero standard uncertainty
    is moved by it, the three products of Formula (7) recomputed with the
    electrical transfer impedances held, and the change of the level of
    ``microphone`` by Formula (8) is its component. The distance of each pair
    and the acoustic centre of each microphone are moved one at a time, as
    independent quantities, and their changes combined in quadrature into the
    single rows "Distance" and "Acoustic centres" of Table 1. The attenuation
    is moved by a fraction of itself,
    :attr:`FreeFieldInputUncertainties.u_air_attenuation_ratio`.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param uncertainties: The standard uncertainty of each input quantity, a
        :class:`FreeFieldInputUncertainties`.
    :param diaphragm_distances_m: :math:`d_{\mathrm{m}12}`,
        :math:`d_{\mathrm{m}23}`, :math:`d_{\mathrm{m}31}`, in m.
    :param temperature_c: The temperature, in °C.
    :param static_pressure_pa: The static pressure, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param acoustic_centres_m: The three acoustic centres, in m.
    :param microphone: The microphone whose level is analysed, 1, 2 or 3.
    :param dispersion: Whether :math:`k` includes dispersion (Default:
        ``True``).
    :return: The :class:`FreeFieldParameterUncertainty`.
    :raises ValueError: for other than three distances or centres, a
        microphone that is not 1, 2 or 3, or acoustic-centre uncertainties
        that are not one value or one per frequency.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    if microphone not in _SIGNS:
        msg = "'microphone' must be 1, 2 or 3."
        raise ValueError(msg)
    distances = _distances(diaphragm_distances_m, len(_TRIAD_PAIRS))
    centres = _positions(acoustic_centres_m, count, 3)
    conditions = (
        float(temperature_c),
        float(static_pressure_pa),
        float(relative_humidity_percent),
    )
    signs = _SIGNS[microphone]

    def level(
        new_distances: Sequence[float] = distances,
        new_centres: Sequence[NDArray[np.float64]] = centres,
        new_conditions: tuple[float, float, float] = conditions,
        scale: float = 1.0,
    ) -> NDArray[np.float64]:
        pairs = _pair_levels(
            frequencies,
            new_distances,
            new_centres,
            new_conditions,
            attenuation_scale=scale,
            dispersion=dispersion,
        )
        total = np.zeros(count)
        for key, value in pairs.items():
            total = total + signs[key] * value
        return 0.5 * total

    nominal = level()
    u = uncertainties
    components: dict[str, NDArray[np.float64]] = {}
    if u.u_distance_m > 0.0:
        changes = []
        for index in range(3):
            moved = list(distances)
            moved[index] += u.u_distance_m
            changes.append(level(new_distances=moved) - nominal)
        components["distance"] = np.sqrt(sum(c**2 for c in changes))
    centre_u = _band_column(u.u_acoustic_centre_m, "u_acoustic_centre_m", count)
    if np.any(centre_u > 0.0):
        changes = []
        for index in range(3):
            moved_centres = list(centres)
            moved_centres[index] = centres[index] + centre_u
            changes.append(level(new_centres=moved_centres) - nominal)
        components["acoustic_centres"] = np.sqrt(sum(c**2 for c in changes))
    for key, index, step in (
        ("static_pressure", 1, u.u_static_pressure_pa),
        ("temperature", 0, u.u_temperature_k),
        ("relative_humidity", 2, u.u_relative_humidity_percent),
    ):
        if step > 0.0:
            shifted = list(conditions)
            shifted[index] += step
            components[key] = np.abs(level(new_conditions=tuple(shifted)) - nominal)  # type: ignore[arg-type]
    if u.u_air_attenuation_ratio > 0.0:
        components["air_attenuation"] = np.abs(
            level(scale=1.0 + u.u_air_attenuation_ratio) - nominal
        )
    return FreeFieldParameterUncertainty(
        frequencies_hz=frequencies, components_db=components, microphone=microphone
    )

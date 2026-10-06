#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Pressure calibration of laboratory standard microphones by reciprocity in a
closed coupler (IEC 61094-2:2009).

Two microphones close the two ends of a small cavity. A current :math:`i_1`
through the transmitter makes its diaphragm a source of short-circuit volume
velocity :math:`M_{\mathrm{p},1} i_1`, the gas in the cavity turns that into
the pressure :math:`p_2 = Z_{\mathrm{a},12}\,M_{\mathrm{p},1} i_1` on the
receiver, and the receiver turns the pressure into its open-circuit voltage,
so (Formula (2))

.. math::

   M_{\mathrm{p},1} M_{\mathrm{p},2} = \frac{1}{Z_{\mathrm{a},12}}\,
   \frac{U_2}{i_1}

The electrical transfer impedance :math:`U_2/i_1` is measured; this module
computes the acoustic transfer impedance :math:`Z_{\mathrm{a},12}` it is
divided by, with every correction the standard gives, and solves the three
products for the sensitivities with
:mod:`~phonometry.metrology.reciprocity_calibration`.

**Two couplers** (5.4 and Annex C). A *large-volume* coupler, small against
the wavelength, holds a pure compliance, and Formula (3) adds the admittances
of the gas and of the two microphones,

.. math::

   \frac{1}{Z'_{\mathrm{a},12}} = \mathrm{j}\omega\left(\frac{V}{\kappa p_\mathrm{s}}
   + \frac{V_{\mathrm{e},1}}{\kappa_\mathrm{r} p_\mathrm{s,r}}
   + \frac{V_{\mathrm{e},2}}{\kappa_\mathrm{r} p_\mathrm{s,r}}\right)

with :math:`V` the coupler volume plus the two front cavities (7.3.3.1), and
the bores that Figure C.2 draws between each microphone face and the cavity
(dimension F of Table C.2), and :math:`V_\mathrm{e}` the complex equivalent
volume of each microphone. A
*plane-wave* coupler, of the diameter of the diaphragms, is a transmission line
of length :math:`l_0` between them (Formula (4)):

.. math::

   \frac{1}{Z'_{\mathrm{a},12}} = \frac{1}{Z_{\mathrm{a},0}}\left[
   \left(\frac{Z_{\mathrm{a},0}}{Z_{\mathrm{a},1}}
   + \frac{Z_{\mathrm{a},0}}{Z_{\mathrm{a},2}}\right)\cosh\gamma l_0
   + \left(1 + \frac{Z_{\mathrm{a},0}^2}{Z_{\mathrm{a},1} Z_{\mathrm{a},2}}\right)
   \sinh\gamma l_0\right]

**Heat conduction** (5.5 and Annex A). In the large-volume coupler the walls
draw heat from the compressed gas and the volume looks larger, by the complex
factor of Formula (A.1),

.. math::

   \Delta_\mathrm{H} = \frac{\kappa}{1 + (\kappa - 1)\,E_V}

where :math:`E_V` is Gerber's temperature transfer function of a finite
cylinder: :func:`temperature_transfer_function` computes it either by the
approximation (A.2) or by the full solution of the reference [A.1], which
A.2 requires below 20 Hz unless the uncertainty component is increased
instead, and which reproduces every entry of Table A.1 to its
stated 0,000 01. In the plane-wave coupler the propagation coefficient and the
wave impedance of Formulas (A.3) and (A.4) carry the losses at the cylindrical
wall, and the admittance of Formula (A.5) those at the two diaphragms.

**Capillary tubes** (5.6 and Annex B). Tubes that equalise the static pressure
shunt the cavity, and Formula (6) divides the transfer impedance by

.. math::

   \Delta_\mathrm{C} = 1 + n\,\frac{Z''_{\mathrm{a},12}}{Z_{\mathrm{a,C}}}

with :math:`Z_{\mathrm{a,C}}` the input impedance of an open tube of Formulas
(B.1) to (B.3), which :func:`capillary_tube_impedance` computes and Tables B.1
and B.2 test.

**The microphone** (7.3.3 and Annex E). Its acoustic impedance is a lumped
compliance, mass and resistance, written as an equivalent volume, a resonance
frequency and a loss factor (:class:`ReciprocityMicrophone`); its front cavity
adds volume, length and, through the excess of its measured volume over the
cylinder of its depth, a further terminating admittance (7.3.3.1).

The wave-motion corrections of Table C.3 for the air-filled large-volume
coupler of LS1P microphones are :func:`large_volume_wave_motion_correction`,
the coupler dimensions of Tables C.1 and C.2 are :data:`IEC61094_2_TABLE_C1`
and :data:`IEC61094_2_TABLE_C2`, and :func:`coupler_parameter_uncertainty`
finds the uncertainty each coupler and microphone parameter contributes, by the
one-at-a-time recalculation 7.5 describes.

The properties of the gas, :math:`\rho`, :math:`c`, :math:`\kappa`,
:math:`\eta` and :math:`\alpha_t`, are those of humid air by Annex F
(:func:`~phonometry.fluids.air`) at the conditions of the calibration, or of
any :class:`~phonometry.fluids.Fluid` passed as ``gas``: 7.3.2.1 allows the
coupler to be filled with hydrogen or helium.
"""

from __future__ import annotations

import dataclasses
import functools
import math
from dataclasses import KW_ONLY, dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy.special import jn_zeros, jv

from .._internal.boundary import settled
from .._internal.frozen import read_only
from .._internal.validation import (
    require_choice,
    require_count,
    require_non_negative,
    require_positive,
)
from .free_field_corrections import _frequency_axis
from .reciprocity_calibration import (
    _TRIAD_PAIRS,
    ReciprocityCalibration,
    _complex_column,
    _solved,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ..fluids import Fluid

__all__ = [
    "IEC61094_2_TABLE_C1",
    "IEC61094_2_TABLE_C2",
    "IEC61094_2_TABLE_C3",
    "CapillaryTube",
    "CapillaryTubeImpedance",
    "CouplerCheck",
    "CouplerDimensions",
    "CouplerInputUncertainties",
    "CouplerParameterUncertainty",
    "CouplerTransferImpedance",
    "HeatConductionCorrection",
    "LargeVolumeCoupler",
    "PlaneWaveCoupler",
    "ReciprocityMicrophone",
    "WaveMotionCorrection",
    "capillary_tube_impedance",
    "check_coupler",
    "coupler_parameter_uncertainty",
    "coupler_transfer_impedance",
    "heat_conduction_correction",
    "large_volume_wave_motion_correction",
    "microphone_acoustic_impedance",
    "pressure_reciprocity",
    "pressure_reciprocity_pair",
    "temperature_transfer_function",
]

# ---------------------------------------------------------------------------
# Reference conditions and the gas
# ---------------------------------------------------------------------------

#: IEC 61094-2:2009 clause 4: "temperature 23,0 °C".
_REFERENCE_TEMPERATURE_C = 23.0
#: IEC 61094-2:2009 clause 4: "static pressure 101,325 kPa", which is
#: :math:`p_\mathrm{s,r}`.
_REFERENCE_STATIC_PRESSURE_PA = 101325.0
#: Clause 4: "relative humidity 50 %".
_REFERENCE_RELATIVE_HUMIDITY_PERCENT = 50.0


@functools.cache
def _reference_kappa() -> float:
    r""":math:`\kappa_\mathrm{r}`, the ratio of specific heats of humid air at
    the reference conditions of clause 4, by Annex F (1,400 757 3 in Table F.1).
    """
    from ..fluids import air

    return air(
        temperature_c=_REFERENCE_TEMPERATURE_C,
        static_pressure_pa=_REFERENCE_STATIC_PRESSURE_PA,
        relative_humidity_percent=_REFERENCE_RELATIVE_HUMIDITY_PERCENT,
    ).heat_capacity_ratio


def _reference_stiffness() -> float:
    r""":math:`\kappa_\mathrm{r} p_\mathrm{s,r}`, in Pa: what turns an
    equivalent volume into a compliance (Formula (3), Annex E).
    """
    return _reference_kappa() * _REFERENCE_STATIC_PRESSURE_PA


#: Relative agreement asked of a given gas's static pressure and the
#: calibration's: the rounding of a value that went through arithmetic.
_SAME_PRESSURE_REL_TOL = 1e-9


def _gas(
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    gas: Fluid | None,
) -> Fluid:
    r"""The gas in the coupler: humid air by Annex F at the conditions, or the
    fluid given (7.3.2.1 allows hydrogen or helium).

    A given fluid's density, speed of sound and viscosity hold at its own
    static pressure, while the stiffness of the gas is taken as
    :math:`\kappa p_\mathrm{s}` at ``static_pressure_pa``: the two have to be
    the same pressure, or the result mixes two states of the gas.
    """
    if gas is not None:
        if not math.isclose(
            gas.static_pressure_pa, static_pressure_pa, rel_tol=_SAME_PRESSURE_REL_TOL
        ):
            msg = (
                f"'gas' holds at {gas.static_pressure_pa:g} Pa but "
                f"'static_pressure_pa' is {static_pressure_pa:g} Pa: give the "
                "fluid at the pressure of the calibration."
            )
            raise ValueError(msg)
        return gas
    from ..fluids import air

    return air(
        temperature_c=temperature_c,
        static_pressure_pa=static_pressure_pa,
        relative_humidity_percent=relative_humidity_percent,
    )


#: Relative agreement asked of the frequencies an impedance was computed at
#: and those of the calibration: the rounding of a value that went through
#: arithmetic, nothing more.
_SAME_FREQUENCY_REL_TOL = 1e-9

#: A coupler is closed by two microphones, a transmitter and a receiver.
_PAIR_SIZE = 2


# ---------------------------------------------------------------------------
# Annex A.2: heat conduction in a closed cavity at low frequencies
# ---------------------------------------------------------------------------

_HEAT_CONDUCTION_METHODS = ("exact", "approximation")

#: The zeros of :math:`J_0` computed by scipy before the McMahon expansion
#: takes over; past the fortieth it agrees with them to 3e-14.
_EXACT_ZEROS = 50

#: The truncation of the radial series of the full solution: at least this
#: many terms, and enough that the last zero squared exceeds a hundred times
#: :math:`|s|`, past which the tail is summed in closed form.
_MIN_TERMS = 200
_TAIL_RATIO = 10.0


@functools.cache
def _bessel_zeros(count: int) -> NDArray[np.float64]:
    r"""The first ``count`` positive zeros of :math:`J_0`, read-only.

    The first fifty from scipy, the rest from McMahon's expansion
    :math:`j_m \approx \beta + 1/(8\beta) - 31/(384\beta^3)
    + 3779/(15360\beta^5)` with :math:`\beta = (m - 1/4)\pi`.
    """
    first = jn_zeros(0, min(count, _EXACT_ZEROS))
    if count <= _EXACT_ZEROS:
        return read_only(np.asarray(first, dtype=np.float64))
    beta = (np.arange(_EXACT_ZEROS + 1, count + 1) - 0.25) * math.pi
    rest = (
        beta
        + 1.0 / (8.0 * beta)
        - 31.0 / (384.0 * beta**3)
        + 3779.0 / (15360.0 * beta**5)
    )
    return read_only(np.concatenate([first, rest]))


def _gerber_exact(ratio: float, x: float) -> complex:
    r"""Gerber's :math:`E_V` of a cylinder of length-to-diameter ratio
    ``ratio``, at the parameter :math:`X`, by its eigenfunction series.

    The temperature in the cylinder (radius 1, length :math:`2R`) solves the
    diffusion equation with a uniform source and walls held at constant
    temperature. Expanding in the radial modes :math:`J_0(j_m r)` and solving
    each axial problem in closed form,

    .. math::

       E_V = \sum_m \frac{4}{j_m^2}\,\frac{s}{q_m^2}
       \left(1 - \frac{\tanh(q_m R)}{q_m R}\right),\qquad
       q_m^2 = j_m^2 + s,\quad s = \frac{2\pi\mathrm{j}X}{l^2}

    with :math:`l = R/(1 + 2R)` the volume to surface ratio. The tail past
    the last term kept is summed by the midpoint rule over the asymptotic
    spacing :math:`\pi` of the zeros.
    """
    length_ratio = ratio / (1.0 + 2.0 * ratio)
    s = 2.0j * math.pi * x / length_ratio**2
    count = max(_MIN_TERMS, math.ceil(_TAIL_RATIO * math.sqrt(abs(s)) / math.pi) + 1)
    zeros = _bessel_zeros(count)
    q = np.sqrt(zeros**2 + s)
    z = q * ratio
    terms = 4.0 / zeros**2 * (s / q**2) * (1.0 - np.tanh(z) / z)
    edge = float(zeros[-1]) + 0.5 * math.pi
    root = np.sqrt(s)
    first = 4.0 * (1.0 / edge - np.arctan(root / edge) / root)
    second = s / (ratio * edge**4)
    return complex(np.sum(terms) + (first - second) / math.pi)


def _gerber_approximation(
    ratio: float, x: NDArray[np.float64]
) -> NDArray[np.complex128]:
    r"""Formula (A.2): :math:`E_V = 1 - S + D_1 S^2 + (3/4)\sqrt{\pi} D_2 S^3`."""
    s = (1.0 - 1.0j) / (2.0 * np.sqrt(math.pi * x))
    d1 = (math.pi * ratio**2 + 8.0 * ratio) / (math.pi * (2.0 * ratio + 1.0) ** 2)
    d2 = (ratio**3 - 6.0 * ratio**2) / (
        3.0 * math.sqrt(math.pi) * (2.0 * ratio + 1.0) ** 3
    )
    value = 1.0 - s + d1 * s**2 + 0.75 * math.sqrt(math.pi) * d2 * s**3
    return np.asarray(value, dtype=np.complex128)


def temperature_transfer_function(
    length_to_diameter_ratio: float,
    x: ArrayLike,
    *,
    method: str = "exact",
) -> NDArray[np.complex128]:
    r"""Gerber's complex temperature transfer function :math:`E_V` of a
    cylindrical cavity (IEC 61094-2:2009 A.2, Formula (A.2) and Table A.1).

    :math:`E_V` is "the ratio of the space average of the sinusoidal
    temperature variation associated with the sound pressure to the sinusoidal
    temperature variation that would be generated if the walls of the coupler
    were perfectly non-conducting", a function of the length-to-diameter ratio
    :math:`R` of the cylinder and of

    .. math::

       X = \frac{f\,l^2}{\kappa\,\alpha_t}

    with :math:`l` its volume to surface ratio and :math:`\alpha_t` the thermal
    diffusivity of the gas.

    ``method="exact"`` (default) sums the full solution of the annex's
    reference [A.1], which A.2 requires below 20 Hz unless the uncertainty
    component is increased instead, and which reproduces all 96
    entries of Table A.1 to the 0,000 01 the annex states for them.
    ``method="approximation"`` is Formula (A.2), whose modulus the annex
    states accurate to 0,01 % for :math:`0{,}125 < R < 8` and :math:`X > 5`;
    its first two terms are the approximation the annex allows for a coupler
    that is not a right circular cylinder.

    :param length_to_diameter_ratio: :math:`R`, positive.
    :param x: :math:`X`, one value or several, positive.
    :param method: ``"exact"`` or ``"approximation"``.
    :return: :math:`E_V`, complex, with the shape of ``x``.
    :raises ValueError: for a ratio or an :math:`X` that is not positive and
        finite, or an unknown method.
    """
    method = require_choice(method, "method", _HEAT_CONDUCTION_METHODS)
    ratio = require_positive(length_to_diameter_ratio, "length_to_diameter_ratio")
    values = np.asarray(x, dtype=np.float64)
    if values.size == 0 or not np.all(np.isfinite(values)) or np.any(values <= 0.0):
        msg = "'x' must be positive and finite."
        raise ValueError(msg)
    if method == "approximation":
        return np.asarray(_gerber_approximation(ratio, values), dtype=np.complex128)
    flat = [_gerber_exact(ratio, float(value)) for value in values.reshape(-1)]
    return np.asarray(flat, dtype=np.complex128).reshape(values.shape)


@dataclass(frozen=True)
class HeatConductionCorrection:
    r"""The heat-conduction correction of a closed cavity at low frequencies
    (IEC 61094-2:2009 5.5 and A.2, Formula (A.1)).

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar length_to_diameter_ratio: :math:`R`.
    :ivar volume_to_surface_m: :math:`l`, the volume to surface ratio, in m.
    :ivar x: :math:`X = f l^2/(\kappa\alpha_t)` at each frequency.
    :ivar transfer_function: :math:`E_V` at each frequency.
    :ivar heat_capacity_ratio: :math:`\kappa` of the gas.
    :ivar method: ``"exact"`` or ``"approximation"``.
    """

    frequencies_hz: NDArray[np.float64]
    length_to_diameter_ratio: float
    volume_to_surface_m: float
    x: NDArray[np.float64]
    transfer_function: NDArray[np.complex128]
    heat_capacity_ratio: float
    method: str

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, or columns of another length.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name, dtype in (("x", np.float64), ("transfer_function", np.complex128)):
            column = np.array(getattr(self, name), dtype=dtype).reshape(-1)
            if column.size != frequencies.size:
                msg = f"HeatConductionCorrection: '{name}' must hold one value per frequency."
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column))

    @property
    def volume_factor(self) -> NDArray[np.complex128]:
        r""":math:`\Delta_\mathrm{H} = \kappa/(1 + (\kappa - 1)E_V)`, the complex
        factor on the geometrical volume (Formula (A.1)).
        """
        kappa = self.heat_capacity_ratio
        return kappa / (1.0 + (kappa - 1.0) * self.transfer_function)

    @property
    def correction_db(self) -> NDArray[np.float64]:
        r""":math:`20\lg|\Delta_\mathrm{H}|`, the apparent increase of the
        volume, in dB.
        """
        return 20.0 * np.log10(np.abs(self.volume_factor))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot :math:`|\Delta_\mathrm{H}|` in dB and its phase against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the modulus curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_heat_conduction_correction

        return plot_heat_conduction_correction(
            self, ax=ax, language=check_language(language), **kwargs
        )


def heat_conduction_correction(
    frequencies_hz: ArrayLike,
    *,
    volume_m3: float,
    surface_area_m2: float,
    length_to_diameter_ratio: float,
    gas: Fluid,
    method: str = "exact",
) -> HeatConductionCorrection:
    r"""The heat-conduction correction :math:`\Delta_\mathrm{H}` of a closed
    cavity (IEC 61094-2:2009 5.5, A.2).

    :math:`\Delta_\mathrm{H}` multiplies the geometrical volume :math:`V` in
    Formula (3). For a coupler closed by microphones, :math:`V` and the surface
    are those of the coupler together with the front cavities (7.3.2.2), which
    :func:`coupler_transfer_impedance` assembles; :math:`R` is that of the
    coupler.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param volume_m3: The total volume, in m³.
    :param surface_area_m2: The total surface, in m².
    :param length_to_diameter_ratio: :math:`R`.
    :param gas: The gas: its thermal diffusivity and ratio of specific heats.
    :param method: ``"exact"`` (default) or ``"approximation"``
        (:func:`temperature_transfer_function`).
    :return: The :class:`HeatConductionCorrection`.
    :raises ValueError: for a volume, surface or ratio that is not positive,
        or frequencies that are not positive and increasing.
    """
    frequencies = _frequency_axis(frequencies_hz)
    volume = require_positive(volume_m3, "volume_m3")
    surface = require_positive(surface_area_m2, "surface_area_m2")
    length = volume / surface
    kappa = gas.heat_capacity_ratio
    x = frequencies * length**2 / (kappa * gas.thermal_diffusivity)
    transfer = temperature_transfer_function(length_to_diameter_ratio, x, method=method)
    return HeatConductionCorrection(
        frequencies_hz=frequencies,
        length_to_diameter_ratio=float(length_to_diameter_ratio),
        volume_to_surface_m=length,
        x=x,
        transfer_function=transfer,
        heat_capacity_ratio=kappa,
        method=method,
    )


# ---------------------------------------------------------------------------
# Annex A.3: wave propagation in a plane-wave coupler
# ---------------------------------------------------------------------------

#: The square root of two of Formulas (A.3) to (A.5).
_SQRT2 = math.sqrt(2.0)

#: A.3: "Equations (A.3) - (A.4) are valid for the frequency range given by
#: omega rho a**2 > 100 eta."
_BROADBAND_VALIDITY = 100.0


def _plane_wave_line(
    omega: NDArray[np.float64], radius: float, gas: Fluid
) -> tuple[NDArray[np.complex128], NDArray[np.complex128]]:
    r""":math:`\gamma` and :math:`Z_{\mathrm{a},0}` of Formulas (A.3) and (A.4)."""
    rho, c, kappa = gas.density, gas.speed_of_sound, gas.heat_capacity_ratio
    viscous = np.sqrt(gas.viscosity / (omega * rho))
    thermal = (kappa - 1.0) * np.sqrt(gas.thermal_diffusivity / omega)
    loss = (1.0 - 1.0j) / _SQRT2 / radius
    area = math.pi * radius**2
    gamma = 1.0j * omega / c * (1.0 + loss * (viscous + thermal))
    impedance = rho * c / area * (1.0 + loss * (viscous - thermal))
    return (
        np.asarray(gamma, dtype=np.complex128),
        np.asarray(impedance, dtype=np.complex128),
    )


def _end_admittance(
    omega: NDArray[np.float64], area: float, gas: Fluid
) -> NDArray[np.complex128]:
    r""":math:`1/Z_{\mathrm{a,h}}` of Formula (A.5) for an end surface of ``area``."""
    rho, c, kappa = gas.density, gas.speed_of_sound, gas.heat_capacity_ratio
    return (
        area
        / (rho * c)
        * (1.0 + 1.0j)
        / _SQRT2
        * (kappa - 1.0)
        / c
        * np.sqrt(gas.thermal_diffusivity * omega)
    )


# ---------------------------------------------------------------------------
# Annex B: the capillary tube
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CapillaryTube:
    r"""Identical open capillary tubes that equalise the static pressure of a
    coupler (IEC 61094-2:2009 5.6 and Annex B).

    :ivar length_m: :math:`l_\mathrm{C}`, the length of each tube, in m.
    :ivar radius_m: :math:`a_\mathrm{t}`, its radius, in m. B.1 notes the
        impedance goes as the fourth power of it, and that a flow calibration
        may be needed to know the effective radius of a tube that is not
        circular.
    :ivar count: :math:`n`, the number of identical tubes.
    """

    length_m: float
    radius_m: float
    count: int = 1

    def __post_init__(self) -> None:
        """Refuse a length or radius that is not positive, or no tube.

        :raises ValueError: for either.
        """
        require_positive(self.length_m, "length_m")
        require_positive(self.radius_m, "radius_m")
        require_count(self.count, "count")


@dataclass(frozen=True)
class CapillaryTubeImpedance:
    r"""The acoustic input impedance of an open capillary tube (IEC
    61094-2:2009 Formulas (B.1) to (B.3)).

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar length_m: :math:`l_\mathrm{C}`, in m.
    :ivar radius_m: :math:`a_\mathrm{t}`, in m.
    :ivar propagation_coefficient_per_m: :math:`\gamma`, complex, in 1/m.
    :ivar wave_impedance_pa_s_m3: :math:`Z_{\mathrm{a,t}}`, the wave impedance
        of an infinite tube, complex, in Pa·s/m³.
    """

    frequencies_hz: NDArray[np.float64]
    length_m: float
    radius_m: float
    propagation_coefficient_per_m: NDArray[np.complex128]
    wave_impedance_pa_s_m3: NDArray[np.complex128]

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, or columns of another length.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in ("propagation_coefficient_per_m", "wave_impedance_pa_s_m3"):
            column = np.array(getattr(self, name), dtype=np.complex128).reshape(-1)
            if column.size != frequencies.size:
                msg = f"CapillaryTubeImpedance: '{name}' must hold one value per frequency."
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column))

    @property
    def impedance_pa_s_m3(self) -> NDArray[np.complex128]:
        r""":math:`Z_{\mathrm{a,C}} = Z_{\mathrm{a,t}}\tanh\gamma l_\mathrm{C}`
        (Formula (B.1)), in Pa·s/m³.
        """
        return self.wave_impedance_pa_s_m3 * np.tanh(
            self.propagation_coefficient_per_m * self.length_m
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the real and imaginary parts of :math:`Z_{\mathrm{a,C}}` in
        GPa·s/m³, the unit of Tables B.1 and B.2.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the real-part curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_capillary_tube_impedance

        return plot_capillary_tube_impedance(
            self, ax=ax, language=check_language(language), **kwargs
        )


def capillary_tube_impedance(
    frequencies_hz: ArrayLike,
    *,
    length_m: float,
    radius_m: float,
    gas: Fluid,
) -> CapillaryTubeImpedance:
    r"""The acoustic input impedance of an open capillary tube (IEC
    61094-2:2009 B.1).

    Formulas (B.2) and (B.3) give the product and the quotient of the
    propagation coefficient and the wave impedance of an infinite tube of
    radius :math:`a_\mathrm{t}`,

    .. math::

       \gamma Z_{\mathrm{a,t}} = \mathrm{j}\frac{\omega\rho}{\pi a_\mathrm{t}^2}
       \left[1 - \frac{2 J_1(k a_\mathrm{t})}{k a_\mathrm{t} J_0(k a_\mathrm{t})}\right]^{-1},
       \qquad
       \frac{\gamma}{Z_{\mathrm{a,t}}} = \mathrm{j}\omega\frac{\pi a_\mathrm{t}^2}{\rho c^2}
       \left[1 + \frac{2(\kappa - 1)}{B k a_\mathrm{t}}
       \frac{J_1(B k a_\mathrm{t})}{J_0(B k a_\mathrm{t})}\right]

    with :math:`k = (-\mathrm{j}\omega\rho/\eta)^{1/2}` and
    :math:`B = (\eta/\rho\alpha_t)^{1/2}`; each follows from their product and
    quotient on the branch with a positive real part, and Formula (B.1) gives
    :math:`Z_{\mathrm{a,C}} = Z_{\mathrm{a,t}}\tanh\gamma l_\mathrm{C}`. A
    tube blocked along its length by a wire has :math:`\Delta_\mathrm{C} = 1`
    instead (B.1), which a coupler without a ``capillary`` stands for.

    Tables B.1 and B.2 tabulate :math:`Z_{\mathrm{a,C}}` at the reference
    conditions for tubes 50 mm and 100 mm long and 0,1667 mm, 0,20 mm and
    0,25 mm in radius; the first radius is 1/6 mm, which is what the printed
    values were computed with.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param length_m: :math:`l_\mathrm{C}`, in m.
    :param radius_m: :math:`a_\mathrm{t}`, in m.
    :param gas: The gas in the tube.
    :return: The :class:`CapillaryTubeImpedance`.
    :raises ValueError: for a length or radius that is not positive, or
        frequencies that are not positive and increasing.
    """
    frequencies = _frequency_axis(frequencies_hz)
    length = require_positive(length_m, "length_m")
    radius = require_positive(radius_m, "radius_m")
    rho, c, kappa = gas.density, gas.speed_of_sound, gas.heat_capacity_ratio
    eta = gas.viscosity
    omega = 2.0 * math.pi * frequencies
    k = np.sqrt(-1.0j * omega * rho / eta)
    b = math.sqrt(eta / (rho * gas.thermal_diffusivity))
    ka = k * radius
    area = math.pi * radius**2
    product = 1.0j * omega * rho / area / (1.0 - 2.0 * jv(1, ka) / (ka * jv(0, ka)))
    quotient = (
        1.0j
        * omega
        * area
        / (rho * c**2)
        * (1.0 + 2.0 * (kappa - 1.0) / (b * ka) * jv(1, b * ka) / jv(0, b * ka))
    )
    gamma = np.sqrt(product * quotient)
    gamma = np.where(gamma.real < 0.0, -gamma, gamma)
    return CapillaryTubeImpedance(
        frequencies_hz=frequencies,
        length_m=length,
        radius_m=radius,
        propagation_coefficient_per_m=gamma,
        wave_impedance_pa_s_m3=product / gamma,
    )


# ---------------------------------------------------------------------------
# The microphone and the couplers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReciprocityMicrophone:
    r"""The parameters of a laboratory standard microphone that enter the
    acoustic transfer impedance (IEC 61094-2:2009 7.3.3 and Annex E).

    The acoustic impedance is the lumped series compliance, mass and
    resistance of E.4, written as the equivalent volume at low frequencies,
    the resonance frequency and the loss factor:

    .. math::

       (2\pi f_0)^2 = (m_\mathrm{a} c_\mathrm{a})^{-1},\qquad
       V_\mathrm{eq} = c_\mathrm{a}\kappa_\mathrm{r} p_\mathrm{s,r},\qquad
       d = r_\mathrm{a}\,2\pi f_0\,c_\mathrm{a}

    E.4 states this representation is generally sufficient up to about 1,3
    times the resonance frequency.

    :ivar equivalent_volume_m3: :math:`V_\mathrm{eq}`, the low-frequency real
        part of the equivalent volume, in m³.
    :ivar resonance_frequency_hz: :math:`f_0`, where the imaginary part of
        :math:`Z_\mathrm{a}` vanishes, in Hz.
    :ivar loss_factor: :math:`d`.
    :ivar front_cavity_volume_m3: The measured volume of the front cavity, in
        m³ (7.3.3.1, E.3).
    :ivar front_cavity_depth_m: Its depth, in m (E.2).
    :ivar front_cavity_diameter_m: Its diameter, in m (dimension B of Tables
        C.1 and C.2).
    :ivar thread_area_m2: The surface an inner thread of the front cavity adds
        to the cavity wall, in m²; added to :math:`S_0` in Formula (A.5)
        (A.3, [A.4]) and to the surface of a large-volume coupler (7.3.2.2).
    """

    equivalent_volume_m3: float
    resonance_frequency_hz: float
    loss_factor: float
    front_cavity_volume_m3: float
    front_cavity_depth_m: float
    front_cavity_diameter_m: float
    thread_area_m2: float = 0.0

    def __post_init__(self) -> None:
        """Refuse parameters that are not physical.

        :raises ValueError: for a volume, frequency, depth or diameter that is
            not positive, or a loss factor or thread area that is negative.
        """
        for name in (
            "equivalent_volume_m3",
            "resonance_frequency_hz",
            "front_cavity_volume_m3",
            "front_cavity_depth_m",
            "front_cavity_diameter_m",
        ):
            require_positive(getattr(self, name), name)
        require_non_negative(self.loss_factor, "loss_factor")
        require_non_negative(self.thread_area_m2, "thread_area_m2")

    @property
    def compliance_m3_per_pa(self) -> float:
        r""":math:`c_\mathrm{a} = V_\mathrm{eq}/(\kappa_\mathrm{r} p_\mathrm{s,r})`,
        in m³/Pa.
        """
        return self.equivalent_volume_m3 / _reference_stiffness()

    @property
    def mass_kg_m4(self) -> float:
        r""":math:`m_\mathrm{a} = 1/((2\pi f_0)^2 c_\mathrm{a})`, in kg/m⁴."""
        omega = 2.0 * math.pi * self.resonance_frequency_hz
        return 1.0 / (omega**2 * self.compliance_m3_per_pa)

    @property
    def resistance_pa_s_m3(self) -> float:
        r""":math:`r_\mathrm{a} = d/(2\pi f_0 c_\mathrm{a})`, in Pa·s/m³."""
        omega = 2.0 * math.pi * self.resonance_frequency_hz
        return self.loss_factor / (omega * self.compliance_m3_per_pa)

    def complex_equivalent_volume_m3(
        self, frequencies_hz: ArrayLike
    ) -> NDArray[np.complex128]:
        r"""The complex equivalent volume :math:`V_\mathrm{e}` of Formula (3),
        in m³, which tends to :attr:`equivalent_volume_m3` at low frequencies:

        .. math::

           V_\mathrm{e} = \frac{\kappa_\mathrm{r} p_\mathrm{s,r}}{\mathrm{j}\omega Z_\mathrm{a}}
           = \frac{V_\mathrm{eq}}{1 - (f/f_0)^2 + \mathrm{j}\,d\,f/f_0}

        :param frequencies_hz: The frequencies, in Hz.
        :return: :math:`V_\mathrm{e}` at each frequency, in m³.
        """
        ratio = (
            np.asarray(frequencies_hz, dtype=np.float64) / self.resonance_frequency_hz
        )
        volume = self.equivalent_volume_m3 / (
            1.0 - ratio**2 + 1.0j * self.loss_factor * ratio
        )
        return np.asarray(volume, dtype=np.complex128)

    def acoustic_impedance_pa_s_m3(
        self, frequencies_hz: ArrayLike
    ) -> NDArray[np.complex128]:
        r""":math:`Z_\mathrm{a} = r_\mathrm{a} + \mathrm{j}\omega m_\mathrm{a}
        + 1/(\mathrm{j}\omega c_\mathrm{a})`, in Pa·s/m³.

        :param frequencies_hz: The frequencies, in Hz, positive.
        :return: :math:`Z_\mathrm{a}` at each frequency, in Pa·s/m³.
        """
        omega = 2.0 * math.pi * np.asarray(frequencies_hz, dtype=np.float64)
        return _reference_stiffness() / (
            1.0j * omega * self.complex_equivalent_volume_m3(frequencies_hz)
        )


def microphone_acoustic_impedance(
    electrical_admittance_s: ArrayLike,
    blocked_impedance_ohm: ArrayLike,
    pressure_sensitivity_v_per_pa: ArrayLike,
) -> NDArray[np.complex128]:
    r"""The acoustic impedance of a microphone from its electrical admittance
    (IEC 61094-2:2009 E.4, Formula (E.1)).

    .. math::

       Z_\mathrm{a} = \frac{Z_\mathrm{e,0} - Y^{-1}}{M_\mathrm{p}^2}

    with the admittance :math:`Y` measured while the diaphragm is terminated by
    a closed quarter-wavelength tube (:math:`p = 0`), and the blocked
    impedance :math:`Z_\mathrm{e,0}` at 100 kHz to 200 kHz, where the
    diaphragm cannot move. E.4 calculates it "by iteration", because the
    pressure sensitivity is itself the result of a calibration that used
    :math:`Z_\mathrm{a}`: alternate this with
    :func:`pressure_reciprocity` until both stop changing.

    :param electrical_admittance_s: :math:`Y`, complex, in S.
    :param blocked_impedance_ohm: :math:`Z_\mathrm{e,0}`, complex, in Ω.
    :param pressure_sensitivity_v_per_pa: :math:`M_\mathrm{p}`, complex, in V/Pa.
    :return: :math:`Z_\mathrm{a}`, complex, in Pa·s/m³.
    :raises ValueError: for an admittance or a sensitivity of zero, or a value
        that is not finite.
    """
    admittance = np.asarray(electrical_admittance_s, dtype=np.complex128)
    blocked = np.asarray(blocked_impedance_ohm, dtype=np.complex128)
    sensitivity = np.asarray(pressure_sensitivity_v_per_pa, dtype=np.complex128)
    for name, value in (
        ("electrical_admittance_s", admittance),
        ("blocked_impedance_ohm", blocked),
        ("pressure_sensitivity_v_per_pa", sensitivity),
    ):
        if not np.all(np.isfinite(value)):
            msg = f"'{name}' must be finite."
            raise ValueError(msg)
    if not (np.all(np.abs(admittance) > 0.0) and np.all(np.abs(sensitivity) > 0.0)):
        msg = "The admittance and the sensitivity must not be zero."
        raise ValueError(msg)
    return (blocked - 1.0 / admittance) / sensitivity**2


@dataclass(frozen=True)
class PlaneWaveCoupler:
    r"""A plane-wave coupler: a cylinder of the diameter of the front cavities
    (IEC 61094-2:2009 C.2, Table C.1 and Figure C.1).

    :ivar length_m: The length of the coupler, between its two faces, in m
        (dimension E); the distance :math:`l_0` between the diaphragms adds
        the depths of the two front cavities (7.3.3.1).
    :ivar diameter_m: Its diameter, in m (dimension C).
    :ivar capillary: The capillary tubes, or ``None`` for none or tubes
        blocked by a wire (:math:`\Delta_\mathrm{C} = 1`).
    """

    length_m: float
    diameter_m: float
    capillary: CapillaryTube | None = None

    def __post_init__(self) -> None:
        """Refuse a length or diameter that is not positive.

        :raises ValueError: for either.
        """
        require_positive(self.length_m, "length_m")
        require_positive(self.diameter_m, "diameter_m")


@dataclass(frozen=True)
class LargeVolumeCoupler:
    r"""A large-volume coupler: a cylinder much larger than the front cavities
    and the equivalent volumes (IEC 61094-2:2009 C.3, Table C.2 and Figure C.2).

    Figure C.2 draws each microphone with its face :attr:`port_length_m` back
    from the cavity: the front cavity, of diameter B, continues through the
    wall of the coupler as a bore of length F to the cavity. Each bore adds
    :math:`\pi B^2 F/4` to the volume of Formula (3) and :math:`\pi B F` to the
    surface the heat conduction sees, with B the front-cavity diameter of the
    microphone in it (:func:`coupler_transfer_impedance`). For the coupler of
    Table C.2 the two bores of LS1P microphones are 2,4 % of the cavity, about
    0,1 dB on each sensitivity.

    :ivar length_m: The length of the cavity, in m (dimension E).
    :ivar diameter_m: Its diameter, in m (dimension C).
    :ivar port_length_m: The length of the bore between each microphone face
        and the cavity, in m (dimension F of Table C.2: 0,80 mm for LS1P, 0,40
        mm for LS2P); zero for microphones whose faces close the cavity.
    :ivar capillary: The capillary tubes, or ``None``.
    :ivar volume_m3: The measured volume of the cavity of length E, without
        the bores and the front cavities, in m³, or ``None`` for the cylinder
        of :attr:`length_m` and :attr:`diameter_m`. A volume measured between
        the two microphone faces includes the bores: pass it with
        ``port_length_m=0``.
    :ivar surface_area_m2: Its measured surface, in m², or ``None`` for that of
        the closed cylinder; measured between the faces, with
        ``port_length_m=0`` as well.
    """

    length_m: float
    diameter_m: float
    port_length_m: float
    capillary: CapillaryTube | None = None
    volume_m3: float | None = None
    surface_area_m2: float | None = None

    def __post_init__(self) -> None:
        """Refuse dimensions that are not positive, or a negative port length.

        :raises ValueError: for any.
        """
        require_positive(self.length_m, "length_m")
        require_positive(self.diameter_m, "diameter_m")
        require_non_negative(self.port_length_m, "port_length_m")
        for name in ("volume_m3", "surface_area_m2"):
            value = getattr(self, name)
            if value is not None:
                require_positive(value, name)

    @property
    def cavity_volume_m3(self) -> float:
        """The volume of the cavity of length E, in m³: the measured one, or
        the cylinder's.
        """
        if self.volume_m3 is not None:
            return self.volume_m3
        return math.pi * self.diameter_m**2 / 4.0 * self.length_m

    @property
    def cavity_surface_m2(self) -> float:
        """The surface of the cavity of length E, in m²: the measured one, or
        the closed cylinder's.
        """
        if self.surface_area_m2 is not None:
            return self.surface_area_m2
        return math.pi * self.diameter_m * (self.length_m + self.diameter_m / 2.0)

    def closed_volume_m3(self, microphones: Sequence[ReciprocityMicrophone]) -> float:
        """The volume :math:`V` of Formula (3) with the coupler closed by two
        microphones, in m³: the cavity, the two bores and the two front
        cavities (7.3.3.1, Figure C.2).

        :param microphones: The two microphones that close it.
        :return: :math:`V`, in m³.
        :raises ValueError: for other than two microphones.
        """
        return _closed_cavity(self, microphones)[0]

    def closed_surface_m2(self, microphones: Sequence[ReciprocityMicrophone]) -> float:
        """The surface the heat conduction sees with the coupler closed by two
        microphones, in m²: the closed cylinder, the wall of each bore and of
        each front cavity, and any thread in it (7.3.2.2); each diaphragm takes
        the place of the port it closes.

        :param microphones: The two microphones that close it.
        :return: The surface, in m².
        :raises ValueError: for other than two microphones.
        """
        return _closed_cavity(self, microphones)[1]


def _closed_cavity(
    coupler: LargeVolumeCoupler, microphones: Sequence[ReciprocityMicrophone]
) -> tuple[float, float]:
    """The volume and the surface of a large-volume coupler closed by two
    microphones.

    :raises ValueError: for other than two microphones.
    """
    if len(microphones) != _PAIR_SIZE:
        msg = "A coupler is closed by two microphones."
        raise ValueError(msg)
    volume = coupler.cavity_volume_m3
    surface = coupler.cavity_surface_m2
    for m in microphones:
        bore = m.front_cavity_diameter_m
        volume += (
            m.front_cavity_volume_m3 + math.pi * bore**2 / 4.0 * coupler.port_length_m
        )
        surface += (
            math.pi * bore * (m.front_cavity_depth_m + coupler.port_length_m)
            + m.thread_area_m2
        )
    return volume, surface


@dataclass(frozen=True)
class CouplerDimensions:
    """One column of IEC 61094-2:2009 Table C.1 or Table C.2, the nominal
    dimensions of a coupler for one type of laboratory standard microphone,
    in millimetres as printed.

    :ivar microphone_diameter_mm: ø A, the outer diameter of the microphone.
    :ivar front_cavity_diameter_mm: ø B.
    :ivar coupler_diameter_mm: ø C.
    :ivar front_cavity_depth_mm: D.
    :ivar coupler_length_mm: E, the nominal length (Table C.2), or ``None``.
    :ivar coupler_length_range_mm: E as a range (Table C.1), or ``None``.
    :ivar port_length_mm: F (Table C.2 only), the length of the bore Figure
        C.2 draws between each microphone face and the cavity, or ``None``.
    :ivar tolerance_mm: The ± tolerance Table C.2 prints on C, E and F, or
        ``None``.
    """

    microphone_diameter_mm: float
    front_cavity_diameter_mm: float
    coupler_diameter_mm: float
    front_cavity_depth_mm: float
    coupler_length_mm: float | None = None
    coupler_length_range_mm: tuple[float, float] | None = None
    port_length_mm: float | None = None
    tolerance_mm: float | None = None


#: IEC 61094-2:2009 Table C.1, "Nominal dimensions for plane-wave couplers",
#: printed folio 28 (PDF page 30), keyed by microphone type. E is printed as a
#: range of lengths.
IEC61094_2_TABLE_C1: Mapping[str, CouplerDimensions] = MappingProxyType(
    {
        "LS1P": CouplerDimensions(
            23.77, 18.6, 18.6, 1.95, coupler_length_range_mm=(3.5, 9.5)
        ),
        "LS2aP": CouplerDimensions(
            13.2, 9.3, 9.3, 0.5, coupler_length_range_mm=(3.0, 7.0)
        ),
        "LS2bP": CouplerDimensions(
            12.15, 9.8, 9.8, 0.7, coupler_length_range_mm=(3.5, 6.0)
        ),
    }
)

#: IEC 61094-2:2009 Table C.2, "Nominal dimensions and tolerances for
#: large-volume couplers", printed folio 29 (PDF page 31), keyed by microphone
#: type; the tolerance is ± 0,03 mm on C, E and F.
IEC61094_2_TABLE_C2: Mapping[str, CouplerDimensions] = MappingProxyType(
    {
        "LS1P": CouplerDimensions(
            23.77, 18.6, 42.88, 1.95, coupler_length_mm=12.55,
            port_length_mm=0.80, tolerance_mm=0.03,
        ),
        "LS2aP": CouplerDimensions(
            13.2, 9.3, 18.30, 0.5, coupler_length_mm=3.50,
            port_length_mm=0.40, tolerance_mm=0.03,
        ),
        "LS2bP": CouplerDimensions(
            12.15, 9.8, 18.30, 0.7, coupler_length_mm=3.50,
            port_length_mm=0.40, tolerance_mm=0.03,
        ),
    }
)  # fmt: skip

#: IEC 61094-2:2009 Table C.3, "Experimentally determined wave-motion
#: corrections for the air-filled large-volume coupler used with type LS1P
#: microphones", printed folio 30 (PDF page 32), keyed by frequency in Hz, in
#: dB. The first row is printed as "≤ 800": the correction is nil up to 800 Hz.
IEC61094_2_TABLE_C3: Mapping[float, float] = MappingProxyType(
    {
        800.0: 0.0,
        1000.0: -0.002,
        1250.0: -0.013,
        1600.0: -0.034,
        2000.0: -0.060,
        2500.0: -0.087,
    }
)


# ---------------------------------------------------------------------------
# The acoustic transfer impedance
# ---------------------------------------------------------------------------

_COUPLER_KINDS = ("plane_wave", "large_volume")


@dataclass(frozen=True)
class CouplerTransferImpedance:
    r"""The acoustic transfer impedance of a coupler closed by two microphones,
    with its corrections (IEC 61094-2:2009 5.4 to 5.6).

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar coupler: ``"plane_wave"`` or ``"large_volume"``.
    :ivar adiabatic_impedance_pa_s_m3: :math:`Z'_{\mathrm{a},12}`, adiabatic
        and without losses (Formula (3) or (4)), in Pa·s/m³.
    :ivar heat_conducting_impedance_pa_s_m3: :math:`Z''_{\mathrm{a},12}`,
        corrected for heat conduction (5.5): with :math:`\Delta_\mathrm{H}` in
        a large-volume coupler, with Formulas (A.3) to (A.5) in a plane-wave
        one, in Pa·s/m³.
    :ivar capillary_correction: :math:`\Delta_\mathrm{C}` of Formula (6), 1
        without capillary tubes.
    :ivar heat_conduction: The :class:`HeatConductionCorrection` of a
        large-volume coupler, ``None`` for a plane-wave one.
    """

    frequencies_hz: NDArray[np.float64]
    coupler: str
    adiabatic_impedance_pa_s_m3: NDArray[np.complex128]
    heat_conducting_impedance_pa_s_m3: NDArray[np.complex128]
    capillary_correction: NDArray[np.complex128]
    heat_conduction: HeatConductionCorrection | None = None

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for an unknown coupler, frequencies that are not
            positive and increasing, or columns of another length.
        """
        require_choice(self.coupler, "coupler", _COUPLER_KINDS)
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in (
            "adiabatic_impedance_pa_s_m3",
            "heat_conducting_impedance_pa_s_m3",
            "capillary_correction",
        ):
            column = _complex_column(getattr(self, name), name, frequencies.size)
            object.__setattr__(self, name, read_only(column.copy()))

    @property
    def transfer_impedance_pa_s_m3(self) -> NDArray[np.complex128]:
        r""":math:`Z_{\mathrm{a},12} = Z''_{\mathrm{a},12}/\Delta_\mathrm{C}`,
        the impedance the electrical transfer impedance is divided by, in
        Pa·s/m³.
        """
        return self.heat_conducting_impedance_pa_s_m3 / self.capillary_correction

    @property
    def heat_conduction_correction_db(self) -> NDArray[np.float64]:
        r""":math:`20\lg|Z''_{\mathrm{a},12}/Z'_{\mathrm{a},12}|`, in dB."""
        return 20.0 * np.log10(
            np.abs(
                self.heat_conducting_impedance_pa_s_m3
                / self.adiabatic_impedance_pa_s_m3
            )
        )

    @property
    def capillary_correction_db(self) -> NDArray[np.float64]:
        r""":math:`-20\lg|\Delta_\mathrm{C}|`, the change of
        :math:`|Z_{\mathrm{a},12}|` the tubes cause, in dB.
        """
        return -20.0 * np.log10(np.abs(self.capillary_correction))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the heat-conduction and capillary corrections of the transfer
        impedance, in dB, against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the heat-conduction curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_coupler_transfer_impedance

        return plot_coupler_transfer_impedance(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _capillary_correction(
    frequencies: NDArray[np.float64],
    impedance: NDArray[np.complex128],
    capillary: CapillaryTube | None,
    gas: Fluid,
) -> NDArray[np.complex128]:
    r""":math:`\Delta_\mathrm{C} = 1 + n Z''_{\mathrm{a},12}/Z_{\mathrm{a,C}}`."""
    if capillary is None:
        return np.ones(frequencies.size, dtype=np.complex128)
    tube = capillary_tube_impedance(
        frequencies, length_m=capillary.length_m, radius_m=capillary.radius_m, gas=gas
    )
    return 1.0 + capillary.count * impedance / tube.impedance_pa_s_m3


def _large_volume(
    frequencies: NDArray[np.float64],
    coupler: LargeVolumeCoupler,
    microphones: tuple[ReciprocityMicrophone, ReciprocityMicrophone],
    gas: Fluid,
    static_pressure_pa: float,
    method: str,
) -> CouplerTransferImpedance:
    r"""Formula (3) with :math:`\Delta_\mathrm{H}` (A.1) and :math:`\Delta_\mathrm{C}`."""
    omega = 2.0 * math.pi * frequencies
    volume, surface = _closed_cavity(coupler, microphones)
    heat = heat_conduction_correction(
        frequencies,
        volume_m3=volume,
        surface_area_m2=surface,
        length_to_diameter_ratio=coupler.length_m / coupler.diameter_m,
        gas=gas,
        method=method,
    )
    gas_stiffness = gas.heat_capacity_ratio * static_pressure_pa
    microphone_volumes = sum(
        m.complex_equivalent_volume_m3(frequencies) for m in microphones
    )
    microphone_term = microphone_volumes / _reference_stiffness()
    adiabatic = np.asarray(
        1.0 / (1.0j * omega * (volume / gas_stiffness + microphone_term)),
        dtype=np.complex128,
    )
    corrected = 1.0 / (
        1.0j * omega * (heat.volume_factor * volume / gas_stiffness + microphone_term)
    )
    return CouplerTransferImpedance(
        frequencies_hz=frequencies,
        coupler="large_volume",
        adiabatic_impedance_pa_s_m3=adiabatic,
        heat_conducting_impedance_pa_s_m3=corrected,
        capillary_correction=_capillary_correction(
            frequencies, corrected, coupler.capillary, gas
        ),
        heat_conduction=heat,
    )


def _line_impedance(
    gamma: NDArray[np.complex128],
    wave: NDArray[np.complex128],
    length: float,
    admittances: tuple[NDArray[np.complex128], NDArray[np.complex128]],
) -> NDArray[np.complex128]:
    """Formula (4) with the terminations given as admittances."""
    first, second = admittances
    inverse = (
        (wave * first + wave * second) * np.cosh(gamma * length)
        + (1.0 + wave**2 * first * second) * np.sinh(gamma * length)
    ) / wave
    return 1.0 / inverse


def _plane_wave(
    frequencies: NDArray[np.float64],
    coupler: PlaneWaveCoupler,
    microphones: tuple[ReciprocityMicrophone, ReciprocityMicrophone],
    gas: Fluid,
    static_pressure_pa: float,
) -> CouplerTransferImpedance:
    r"""Formula (4), lossless and with (A.3) to (A.5), and :math:`\Delta_\mathrm{C}`."""
    omega = 2.0 * math.pi * frequencies
    radius = coupler.diameter_m / 2.0
    area = math.pi * radius**2
    length = coupler.length_m + sum(m.front_cavity_depth_m for m in microphones)
    gas_stiffness = gas.heat_capacity_ratio * static_pressure_pa
    # Each diaphragm in parallel with the excess of its front cavity over the
    # cylinder of its depth (7.3.3.1), which may be negative (NOTE 1).
    admittances = [
        1.0 / m.acoustic_impedance_pa_s_m3(frequencies)
        + 1.0j
        * omega
        * (m.front_cavity_volume_m3 - area * m.front_cavity_depth_m)
        / gas_stiffness
        for m in microphones
    ]
    terminations = (admittances[0], admittances[1])
    lossless_gamma = np.asarray(1.0j * omega / gas.speed_of_sound, dtype=np.complex128)
    lossless_wave = np.full(
        frequencies.size, gas.density * gas.speed_of_sound / area, dtype=np.complex128
    )
    adiabatic = _line_impedance(lossless_gamma, lossless_wave, length, terminations)
    gamma, wave = _plane_wave_line(omega, radius, gas)
    # The heat conduction at each diaphragm, Formula (A.5), with the surface a
    # thread adds to the end surface (A.3).
    lossy_terminations = (
        terminations[0]
        + _end_admittance(omega, area + microphones[0].thread_area_m2, gas),
        terminations[1]
        + _end_admittance(omega, area + microphones[1].thread_area_m2, gas),
    )
    corrected = _line_impedance(gamma, wave, length, lossy_terminations)
    return CouplerTransferImpedance(
        frequencies_hz=frequencies,
        coupler="plane_wave",
        adiabatic_impedance_pa_s_m3=adiabatic,
        heat_conducting_impedance_pa_s_m3=corrected,
        capillary_correction=_capillary_correction(
            frequencies, corrected, coupler.capillary, gas
        ),
    )


def coupler_transfer_impedance(
    frequencies_hz: ArrayLike,
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    transmitter: ReciprocityMicrophone,
    receiver: ReciprocityMicrophone,
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    gas: Fluid | None = None,
    heat_conduction_method: str = "exact",
) -> CouplerTransferImpedance:
    r"""The acoustic transfer impedance :math:`Z_{\mathrm{a},12}` of a coupler
    closed by two microphones (IEC 61094-2:2009 5.4 to 5.6).

    A :class:`LargeVolumeCoupler` takes Formula (3): the gas of the coupler,
    the two bores of Figure C.2 and the two front cavities (7.3.3.1) as one
    compliance, its volume multiplied by :math:`\Delta_\mathrm{H}` of Formula
    (A.1) for the heat conduction, in parallel with the equivalent volumes of
    the two microphones. The surface the heat conduction sees is that of the
    coupler plus the wall of each bore and front cavity and any thread in it
    (7.3.2.2): the diaphragm takes the place of the port it closes
    (:meth:`LargeVolumeCoupler.closed_volume_m3`,
    :meth:`LargeVolumeCoupler.closed_surface_m2`).

    A :class:`PlaneWaveCoupler` takes Formula (4): a line of length
    :math:`l_0`, the coupler plus the two front-cavity depths, terminated at
    each end by the microphone's acoustic impedance in parallel with the excess
    volume of its front cavity (7.3.3.1); the losses of Formulas (A.3) to (A.5)
    give :math:`Z''_{\mathrm{a},12}`, and the same line without them
    :math:`Z'_{\mathrm{a},12}`.

    Both are then divided by :math:`\Delta_\mathrm{C}` of Formula (6) for the
    capillary tubes. The pair is reciprocal, so which microphone transmits does
    not change the result.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param coupler: The coupler.
    :param transmitter: Microphone (1).
    :param receiver: Microphone (2).
    :param temperature_c: The temperature of the gas, in °C.
    :param static_pressure_pa: The static pressure :math:`p_\mathrm{s}`, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param gas: A :class:`~phonometry.fluids.Fluid` for a coupler filled with a
        gas other than air; ``None`` (default) takes humid air by Annex F at
        the three conditions.
    :param heat_conduction_method: ``"exact"`` (default) or ``"approximation"`` for
        :math:`E_V` in a large-volume coupler
        (:func:`temperature_transfer_function`).
    :return: The :class:`CouplerTransferImpedance`.
    :raises ValueError: for frequencies that are not positive and increasing,
        a static pressure that is not positive, or an unknown method.
    """
    frequencies = _frequency_axis(frequencies_hz)
    pressure = require_positive(static_pressure_pa, "static_pressure_pa")
    medium = _gas(temperature_c, pressure, relative_humidity_percent, gas)
    pair = (transmitter, receiver)
    if isinstance(coupler, LargeVolumeCoupler):
        method = require_choice(
            heat_conduction_method, "heat_conduction_method", _HEAT_CONDUCTION_METHODS
        )
        return _large_volume(frequencies, coupler, pair, medium, pressure, method)
    if isinstance(coupler, PlaneWaveCoupler):
        return _plane_wave(frequencies, coupler, pair, medium, pressure)
    msg = "'coupler' must be a PlaneWaveCoupler or a LargeVolumeCoupler."
    raise TypeError(msg)


# ---------------------------------------------------------------------------
# Clause 5.7: the pressure sensitivities
# ---------------------------------------------------------------------------


def _acoustic(
    value: ArrayLike | CouplerTransferImpedance,
    name: str,
    frequencies: NDArray[np.float64],
) -> NDArray[np.complex128]:
    """The transfer impedance of a pair, from a result or from numbers.

    A result carries the frequencies it was computed at, and they have to be
    the calibration's: an impedance of other frequencies with as many points
    would divide each electrical transfer impedance by the wrong one.
    """
    count = frequencies.size
    if isinstance(value, CouplerTransferImpedance):
        computed = value.frequencies_hz
        if computed.size != count or not np.allclose(
            computed, frequencies, rtol=_SAME_FREQUENCY_REL_TOL, atol=0.0
        ):
            msg = (
                f"'{name}' was computed at other frequencies than the "
                f"calibration's ({computed.size} from {computed[0]:g} Hz against "
                f"{count} from {frequencies[0]:g} Hz)."
            )
            raise ValueError(msg)
        return value.transfer_impedance_pa_s_m3
    return _complex_column(value, name, count)


def pressure_reciprocity(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedances_ohm: Sequence[ArrayLike],
    acoustic_transfer_impedances: Sequence[ArrayLike | CouplerTransferImpedance],
    *,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration:
    r"""The pressure sensitivities of three microphones calibrated in pairs in
    a coupler (IEC 61094-2:2009 5.7.1, Formula (7)).

    Each pair gives the product
    :math:`M_{\mathrm{p},i} M_{\mathrm{p},j} = Z_{\mathrm{e},ij}/Z_{\mathrm{a},ij}`
    (Formula (2)), and Formula (7) solves the three:

    .. math::

       |M_{\mathrm{p},1}| = \left\{\left|\frac{Z_{\mathrm{e},12}Z_{\mathrm{e},31}}
       {Z_{\mathrm{e},23}}\right|\left|\frac{Z''_{\mathrm{a},23}}
       {Z''_{\mathrm{a},12}Z''_{\mathrm{a},31}}\right|\left|\frac{\Delta_\mathrm{C,12}
       \Delta_\mathrm{C,31}}{\Delta_\mathrm{C,23}}\right|\right\}^{1/2}

    with similar expressions for the other two, and the phase "by a similar
    procedure from the phase angle of each term". The library solves the
    complex products together, on the branch described in
    :mod:`~phonometry.metrology.reciprocity_calibration`.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param electrical_transfer_impedances_ohm: :math:`Z_{\mathrm{e},12}`,
        :math:`Z_{\mathrm{e},23}` and :math:`Z_{\mathrm{e},31}`, complex, in Ω,
        each one value or one per frequency.
    :param acoustic_transfer_impedances: :math:`Z_{\mathrm{a},12}`,
        :math:`Z_{\mathrm{a},23}` and :math:`Z_{\mathrm{a},31}`, each a
        :class:`CouplerTransferImpedance` or complex values in Pa·s/m³ already
        corrected.
    :param corrections_db: Corrections added to every sensitivity level, by
        name, in dB: :func:`large_volume_wave_motion_correction` for the
        large-volume coupler of LS1P microphones (Default: none).
    :param expanded_uncertainty_db: The expanded uncertainty of the levels, in
        dB, one value or one per frequency, from
        :func:`~phonometry.metrology.reciprocity_uncertainty_budget` (Default:
        ``None``).
    :return: The :class:`~phonometry.metrology.ReciprocityCalibration`.
    :raises ValueError: for other than three pairs, values that are zero or not
        finite, or a column of the wrong length.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    if len(electrical_transfer_impedances_ohm) != len(_TRIAD_PAIRS) or len(
        acoustic_transfer_impedances
    ) != len(_TRIAD_PAIRS):
        msg = "Three pairs are needed, in the order 12, 23, 31 (Formula (7))."
        raise ValueError(msg)
    products = [
        _complex_column(
            electrical, f"electrical_transfer_impedances_ohm[{pair}]", count
        )
        / _acoustic(acoustic, f"acoustic_transfer_impedances[{pair}]", frequencies)
        for pair, electrical, acoustic in zip(
            _TRIAD_PAIRS,
            electrical_transfer_impedances_ohm,
            acoustic_transfer_impedances,
            strict=True,
        )
    ]
    return _solved(
        frequencies,
        products,
        None,
        field="pressure",
        corrections_db=corrections_db,
        expanded_uncertainty_db=expanded_uncertainty_db,
    )


def pressure_reciprocity_pair(
    frequencies_hz: ArrayLike,
    electrical_transfer_impedance_ohm: ArrayLike,
    acoustic_transfer_impedance: ArrayLike | CouplerTransferImpedance,
    sensitivity_ratio: ArrayLike,
    *,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ReciprocityCalibration:
    r"""The pressure sensitivities of two microphones and an auxiliary sound
    source (IEC 61094-2:2009 5.1.3 and 5.7.2, Formula (8)).

    .. math::

       |M_{\mathrm{p},1}| = \left|\frac{M_{\mathrm{p},1}}{M_{\mathrm{p},2}}\,
       \frac{Z_{\mathrm{e},12}}{Z''_{\mathrm{a},12}}\,\Delta_\mathrm{C}\right|^{1/2}

    with the ratio of the two sensitivities measured by exposing both to the
    same pressure of the auxiliary source; only microphone (1) needs to be
    reciprocal (5.1.1).

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param electrical_transfer_impedance_ohm: :math:`Z_{\mathrm{e},12}`,
        complex, in Ω.
    :param acoustic_transfer_impedance: :math:`Z_{\mathrm{a},12}`, a
        :class:`CouplerTransferImpedance` or complex values in Pa·s/m³.
    :param sensitivity_ratio: :math:`M_{\mathrm{p},1}/M_{\mathrm{p},2}`,
        complex, one value or one per frequency.
    :param corrections_db: Corrections added to both levels (Default: none).
    :param expanded_uncertainty_db: The expanded uncertainty, in dB (Default:
        ``None``).
    :return: The :class:`~phonometry.metrology.ReciprocityCalibration`, of two
        microphones.
    :raises ValueError: for values that are zero or not finite, or a column
        of the wrong length.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    product = _complex_column(
        electrical_transfer_impedance_ohm, "electrical_transfer_impedance_ohm", count
    ) / _acoustic(
        acoustic_transfer_impedance, "acoustic_transfer_impedance", frequencies
    )
    return _solved(
        frequencies,
        [product],
        sensitivity_ratio,
        field="pressure",
        corrections_db=corrections_db,
        expanded_uncertainty_db=expanded_uncertainty_db,
    )


# ---------------------------------------------------------------------------
# Table C.3: wave motion in the large-volume coupler of LS1P microphones
# ---------------------------------------------------------------------------

#: How far a frequency may sit from one Table C.3 prints and still be read as
#: it: an exact base-ten one-third-octave frequency is within 1 % of its
#: nominal value, and adjacent rows are 25 % apart.
_NOMINAL_TOLERANCE = 0.02


@dataclass(frozen=True)
class WaveMotionCorrection:
    """The wave-motion correction of the large-volume coupler for LS1P
    microphones (IEC 61094-2:2009 C.3, Table C.3).

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar correction_db: The correction added to the pressure sensitivity
        level, in dB.
    :ivar speed_of_sound_ratio: The ratio of the speed of sound in the gas of
        the coupler to that in air, 1 for air.
    :ivar interpolated: Whether each value was interpolated between rows of the
        table rather than read from one.
    """

    frequencies_hz: NDArray[np.float64]
    correction_db: NDArray[np.float64]
    speed_of_sound_ratio: float
    interpolated: NDArray[np.bool_]

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, or columns of another length.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name, dtype in (("correction_db", np.float64), ("interpolated", np.bool_)):
            column = np.array(getattr(self, name), dtype=dtype).reshape(-1)
            if column.size != frequencies.size:
                msg = (
                    f"WaveMotionCorrection: '{name}' must hold one value per frequency."
                )
                raise ValueError(msg)
            object.__setattr__(self, name, read_only(column))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the correction against frequency, with the rows of Table C.3.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the correction curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_wave_motion_correction

        return plot_wave_motion_correction(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _table_c3(frequency: float) -> tuple[float, bool]:
    """The correction of Table C.3 at an air frequency, and whether it was
    interpolated in lg f between two rows.

    :raises ValueError: above the last row, 2 500 Hz.
    """
    printed = np.array(sorted(IEC61094_2_TABLE_C3), dtype=np.float64)
    values = np.array([IEC61094_2_TABLE_C3[f] for f in printed])
    nearest = int(np.argmin(np.abs(np.log(printed / frequency))))
    if abs(frequency / printed[nearest] - 1.0) <= _NOMINAL_TOLERANCE:
        return float(values[nearest]), False
    if frequency < printed[0]:
        return 0.0, False
    if frequency > printed[-1]:
        msg = (
            f"Table C.3 prints no correction above 2500 Hz, the upper limit C.3 "
            f"gives this coupler for LS1P microphones in air; got {frequency:g} Hz "
            "in air."
        )
        raise ValueError(msg)
    return float(np.interp(math.log(frequency), np.log(printed), values)), True


def large_volume_wave_motion_correction(
    frequencies_hz: ArrayLike, *, speed_of_sound_ratio: float = 1.0
) -> WaveMotionCorrection:
    """The wave-motion correction of the large-volume coupler used with LS1P
    microphones (IEC 61094-2:2009 C.3, Table C.3).

    The correction is to be added to the pressure sensitivity level determined
    in the air-filled coupler of Table C.2, when it is not practical to
    determine it for the individual coupler and microphones. It is nil up to
    800 Hz and printed at five frequencies from 1 kHz to 2,5 kHz, where C.3
    sets the upper limit of the coupler for LS1P microphones. A frequency
    within 2 % of a printed one takes its value; one between two rows is
    interpolated linearly in lg f, and flagged.

    For a coupler filled with hydrogen, C.3 allows the same corrections "provided
    the frequency scale is multiplied by a factor equal to the ratio of the
    speed of sound": ``speed_of_sound_ratio`` is that factor, and each
    frequency is read at its value divided by it.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param speed_of_sound_ratio: The speed of sound in the gas re that in air
        (Default: 1, air).
    :return: The :class:`WaveMotionCorrection`.
    :raises ValueError: for a frequency whose air equivalent is above 2 500 Hz,
        or a ratio that is not positive.
    """
    frequencies = _frequency_axis(frequencies_hz)
    ratio = require_positive(speed_of_sound_ratio, "speed_of_sound_ratio")
    read = [_table_c3(float(f) / ratio) for f in frequencies]
    return WaveMotionCorrection(
        frequencies_hz=frequencies,
        correction_db=np.array([value for value, _ in read]),
        speed_of_sound_ratio=ratio,
        interpolated=np.array([flag for _, flag in read]),
    )


# ---------------------------------------------------------------------------
# What the coupler formulas require
# ---------------------------------------------------------------------------

#: C.2: "Coupler cavities having length to diameter ratios within the range
#: of 0,5 to 0,75 are recommended."
_PLANE_WAVE_RATIO = (0.5, 0.75)
#: A.2: Formula (A.2) is accurate "within the range 0,125 < R < 8 and for X > 5".
_APPROXIMATION_RATIO = (0.125, 8.0)
_APPROXIMATION_X = 5.0
#: A.2: "When calibrations are performed at frequencies below 20 Hz ... the full
#: frequency domain solution given in [A.1] shall be used, or the corresponding
#: uncertainty component shall be increased accordingly".
_APPROXIMATION_LOWEST_HZ = 20.0
#: Annex F, printed folio 38: "15 °C - 27 °C", "60 kPa - 110 kPa", "10 % - 90 %".
_ANNEX_F_TEMPERATURE_C = (15.0, 27.0)
_ANNEX_F_PRESSURE_PA = (60_000.0, 110_000.0)
_ANNEX_F_HUMIDITY_PERCENT = (10.0, 90.0)


@dataclass(frozen=True)
class CouplerCheck:
    r"""Whether the formulas of IEC 61094-2:2009 apply to a coupler at the
    frequencies and conditions of a calibration.

    Built by :func:`check_coupler`.

    :ivar coupler: ``"plane_wave"`` or ``"large_volume"``.
    :ivar length_to_diameter_ratio: :math:`R`: for a plane-wave coupler the
        distance between the diaphragms, :math:`l_0`, over the diameter (C.2,
        5.4), for a large-volume one the length of the cavity over its
        diameter (A.2).
    :ivar ratio_recommended: For a plane-wave coupler, whether :math:`R` is
        within the 0,5 to 0,75 C.2 recommends; ``None`` for a large-volume one.
        Advisory: it does not enter :attr:`passes`.
    :ivar broadband_margin: For a plane-wave coupler,
        :math:`\omega\rho a^2/(100\eta)` at the lowest frequency, which A.3
        requires above 1 for Formulas (A.3) and (A.4); ``None`` otherwise.
    :ivar lowest_x: For a large-volume coupler, :math:`X` at the lowest
        frequency; ``None`` otherwise. It binds only the approximation.
    :ivar approximation_valid: For a large-volume coupler computed with
        Formula (A.2), whether :math:`0{,}125 < R < 8` and :math:`X > 5`, where
        A.2 states its accuracy; ``None`` with the full solution or for a
        plane-wave coupler.
    :ivar full_solution_advised: For a large-volume coupler computed with
        Formula (A.2), whether a frequency is below 20 Hz, where A.2 asks for
        the full solution "or the corresponding uncertainty component shall be
        increased accordingly"; ``None`` with the full solution or for a
        plane-wave coupler. Advisory: it does not enter :attr:`passes`,
        because the larger uncertainty is the caller's to state.
    :ivar conditions_valid: For air, whether the conditions are within the
        domain Annex F states for its equations; ``None`` for another gas.
    :ivar lowest_frequency_hz: The lowest frequency of the calibration, in Hz.
    """

    coupler: str
    length_to_diameter_ratio: float
    ratio_recommended: bool | None
    broadband_margin: float | None
    lowest_x: float | None
    approximation_valid: bool | None
    full_solution_advised: bool | None
    conditions_valid: bool | None
    lowest_frequency_hz: float

    @property
    def broadband_valid(self) -> bool | None:
        """Whether Formulas (A.3) and (A.4) hold at every frequency."""
        if self.broadband_margin is None:
            return None
        return self.broadband_margin > 1.0

    @property
    def passes(self) -> bool:
        """The verdict: the formulas the calibration uses hold where it uses them."""
        return all(
            flag is not False
            for flag in (
                self.broadband_valid,
                self.approximation_valid,
                self.conditions_valid,
            )
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a CouplerCheck has no truth value; read '.passes'"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each condition as its margin to the limit it is held to.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh`.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.reciprocity import plot_coupler_check

        return plot_coupler_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _within(value: float, bounds: tuple[float, float]) -> bool:
    """Whether a value is in a printed range, ends included, read in decimal.

    The length-to-diameter ratio of a coupler is a sum of decimal lengths over
    a decimal diameter, and one that is 0,5 in decimal comes out
    0,499 999 999 999 999 9 in binary; settled, it is on the range.
    """
    return bool(bounds[0] <= float(settled(value)) <= bounds[1])


def check_coupler(
    frequencies_hz: ArrayLike,
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    microphones: Sequence[ReciprocityMicrophone],
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    gas: Fluid | None = None,
    heat_conduction_method: str = "exact",
) -> CouplerCheck:
    r"""Do the coupler formulas of IEC 61094-2:2009 hold for this calibration?

    For a plane-wave coupler, Formulas (A.3) and (A.4) "are valid for the
    frequency range given by :math:`\omega\rho a^2 > 100\eta`" (A.3), which is
    required at the lowest frequency; C.2 recommends a ratio of the distance
    between the diaphragms to the diameter of 0,5 to 0,75, reported but not
    required. For a large-volume coupler with the approximation (A.2), A.2
    states its accuracy for :math:`0{,}125 < R < 8` and :math:`X > 5`, which
    is required; below 20 Hz A.2 asks for the full solution or a larger
    uncertainty component, which is reported but not required. In air, the
    conditions are checked against the domain Annex F states for its
    equations (15 °C to 27 °C, 60 kPa to 110 kPa, 10 % to 90 %).

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param coupler: The coupler.
    :param microphones: The microphones that close it, two or a triad of one
        type; the first two give the front cavities that add to the volume,
        surface and length.
    :param temperature_c: The temperature, in °C.
    :param static_pressure_pa: The static pressure, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param gas: Another gas than air, or ``None``.
    :param heat_conduction_method: The method the calibration uses for
        :math:`E_V`.
    :return: The :class:`CouplerCheck`.
    :raises ValueError: for frequencies that are not positive and increasing,
        fewer than two microphones, or an unknown method.
    """
    frequencies = _frequency_axis(frequencies_hz)
    method = require_choice(
        heat_conduction_method, "heat_conduction_method", _HEAT_CONDUCTION_METHODS
    )
    if len(microphones) < _PAIR_SIZE:
        msg = "A coupler is closed by two microphones."
        raise ValueError(msg)
    pair = tuple(microphones[:_PAIR_SIZE])
    lowest = float(frequencies[0])
    medium = _gas(temperature_c, static_pressure_pa, relative_humidity_percent, gas)
    if isinstance(coupler, PlaneWaveCoupler):
        # C.2 and 5.4: "the length of the coupler, i.e. the distance between
        # the two diaphragms".
        length = coupler.length_m + sum(m.front_cavity_depth_m for m in pair)
    else:
        length = coupler.length_m
    ratio = length / coupler.diameter_m
    conditions = None
    if gas is None:
        conditions = (
            _within(temperature_c, _ANNEX_F_TEMPERATURE_C)
            and _within(static_pressure_pa, _ANNEX_F_PRESSURE_PA)
            and _within(relative_humidity_percent, _ANNEX_F_HUMIDITY_PERCENT)
        )
    if isinstance(coupler, PlaneWaveCoupler):
        radius = coupler.diameter_m / 2.0
        omega = 2.0 * math.pi * lowest
        margin = (
            omega
            * medium.density
            * radius**2
            / (_BROADBAND_VALIDITY * medium.viscosity)
        )
        return CouplerCheck(
            coupler="plane_wave",
            length_to_diameter_ratio=ratio,
            ratio_recommended=_within(ratio, _PLANE_WAVE_RATIO),
            broadband_margin=margin,
            lowest_x=None,
            approximation_valid=None,
            full_solution_advised=None,
            conditions_valid=conditions,
            lowest_frequency_hz=lowest,
        )
    volume, surface = _closed_cavity(coupler, pair)
    lowest_x = (
        lowest
        * (volume / surface) ** 2
        / (medium.heat_capacity_ratio * medium.thermal_diffusivity)
    )
    approximation = advised = None
    if method == "approximation":
        approximation = (
            _APPROXIMATION_RATIO[0] < ratio < _APPROXIMATION_RATIO[1]
            and lowest_x > _APPROXIMATION_X
        )
        advised = lowest < _APPROXIMATION_LOWEST_HZ
    return CouplerCheck(
        coupler="large_volume",
        length_to_diameter_ratio=ratio,
        ratio_recommended=None,
        broadband_margin=None,
        lowest_x=lowest_x,
        approximation_valid=approximation,
        full_solution_advised=advised,
        conditions_valid=conditions,
        lowest_frequency_hz=lowest,
    )


# ---------------------------------------------------------------------------
# Clause 7.5: one component at a time
# ---------------------------------------------------------------------------

#: For each microphone (1, 2, 3), the pair that is divided by in Formula (7)
#: and the two that divide: :math:`|M_1|^2 = |P_{12} P_{31}/P_{23}|`, and
#: :math:`P = Z_\mathrm{e}/Z_\mathrm{a}` with :math:`Z_\mathrm{e}` measured.
_OPPOSITE_PAIR = MappingProxyType({1: "23", 2: "31", 3: "12"})


@dataclass(frozen=True)
class CouplerParameterUncertainty:
    """The standard uncertainty of a sensitivity level that each parameter of
    the acoustic transfer impedance contributes (IEC 61094-2:2009 7.5).

    Built by :func:`coupler_parameter_uncertainty`; ready to pass to
    :func:`~phonometry.metrology.reciprocity_uncertainty_budget`.

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar components_db: The component of each parameter, keyed by its name in
        :data:`~phonometry.metrology.IEC61094_2_TABLE_1`, in dB at each
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
                    f"CouplerParameterUncertainty: 'components_db[{name!r}]' must be "
                    "one finite, non-negative value per frequency."
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
            self, ax=ax, language=check_language(language), field="pressure", **kwargs
        )


def _pair_impedances(
    frequencies: NDArray[np.float64],
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    microphones: Sequence[ReciprocityMicrophone],
    conditions: tuple[float, float, float],
    method: str,
    gas: Fluid | None,
) -> dict[str, NDArray[np.complex128]]:
    """The corrected transfer impedance of the three pairs."""
    temperature, pressure, humidity = conditions
    first, second, third = microphones
    pairs = {"12": (first, second), "23": (second, third), "31": (third, first)}
    return {
        key: coupler_transfer_impedance(
            frequencies,
            coupler,
            *pair,
            temperature_c=temperature,
            static_pressure_pa=pressure,
            relative_humidity_percent=humidity,
            gas=gas,
            heat_conduction_method=method,
        ).transfer_impedance_pa_s_m3
        for key, pair in pairs.items()
    }


def _level_change(
    nominal: Mapping[str, NDArray[np.complex128]],
    changed: Mapping[str, NDArray[np.complex128]],
    microphone: int,
) -> NDArray[np.float64]:
    r"""The change of :math:`20\lg|M|` of one microphone, Formula (7) with the
    electrical transfer impedances held.
    """
    opposite = _OPPOSITE_PAIR[microphone]
    change = np.zeros(next(iter(nominal.values())).size)
    for pair, value in nominal.items():
        ratio = 10.0 * np.log10(np.abs(changed[pair] / value))
        change = change + (ratio if pair == opposite else -ratio)
    return change


@dataclass(frozen=True)
class CouplerInputUncertainties:
    """The standard uncertainty of each input quantity of the acoustic transfer
    impedance in a coupler: those Table 1 of IEC 61094-2:2009 lists under
    "Coupler properties" (7.3.2) and "Microphone parameters" (7.3.3) that
    :func:`coupler_parameter_uncertainty` can move.

    Each one left at zero contributes no component. A microphone parameter is
    the uncertainty of that parameter on each of the three microphones.

    :param u_coupler_length_m: Of the coupler length, in m.
    :param u_coupler_diameter_m: Of its diameter, in m.
    :param u_coupler_volume_m3: Of the volume of a large-volume coupler, in m³.
    :param u_coupler_surface_area_m2: Of its surface, in m².
    :param u_capillary_length_m: Of the length of the capillary tubes, in m.
    :param u_capillary_radius_m: Of their radius, in m.
    :param u_static_pressure_pa: Of the static pressure, in Pa.
    :param u_temperature_k: Of the temperature, in K.
    :param u_relative_humidity_percent: Of the relative humidity, in
        percentage points.
    :param u_front_cavity_depth_m: Of each front cavity depth, in m.
    :param u_front_cavity_volume_m3: Of each front cavity volume, in m³.
    :param u_equivalent_volume_m3: Of each equivalent volume, in m³.
    :param u_resonance_frequency_hz: Of each resonance frequency, in Hz.
    :param u_loss_factor: Of each loss factor.
    :raises ValueError: for an uncertainty that is negative or not finite.
    """

    _: KW_ONLY
    u_coupler_length_m: float = 0.0
    u_coupler_diameter_m: float = 0.0
    u_coupler_volume_m3: float = 0.0
    u_coupler_surface_area_m2: float = 0.0
    u_capillary_length_m: float = 0.0
    u_capillary_radius_m: float = 0.0
    u_static_pressure_pa: float = 0.0
    u_temperature_k: float = 0.0
    u_relative_humidity_percent: float = 0.0
    u_front_cavity_depth_m: float = 0.0
    u_front_cavity_volume_m3: float = 0.0
    u_equivalent_volume_m3: float = 0.0
    u_resonance_frequency_hz: float = 0.0
    u_loss_factor: float = 0.0

    def __post_init__(self) -> None:
        """Refuse an uncertainty that is negative or not finite.

        :raises ValueError: for any.
        """
        for item in dataclasses.fields(self):
            object.__setattr__(
                self,
                item.name,
                require_non_negative(getattr(self, item.name), item.name),
            )


def coupler_parameter_uncertainty(
    frequencies_hz: ArrayLike,
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    microphones: Sequence[ReciprocityMicrophone],
    uncertainties: CouplerInputUncertainties,
    *,
    temperature_c: float,
    static_pressure_pa: float,
    relative_humidity_percent: float,
    microphone: int = 1,
    gas: Fluid | None = None,
    heat_conduction_method: str = "exact",
) -> CouplerParameterUncertainty:
    r"""The uncertainty components of the acoustic transfer impedance, one
    parameter at a time (IEC 61094-2:2009 7.5).

    "Due to the complexity of the final expression for the pressure
    sensitivity in Equation (7) the uncertainty analysis of the acoustic
    transfer impedance is usually performed by repeating a calculation while
    the various components are changed one at a time by their associated
    uncertainty. The difference to the result derived by the unchanged
    components is then used to determine the standard uncertainty related to
    the various components." This is that: each parameter with a non-zero
    standard uncertainty is moved by it, the three transfer impedances of the
    triad recomputed, and the change of the sensitivity level of
    ``microphone`` by Formula (7), with the measured electrical transfer
    impedances held, is its component. A microphone parameter is moved for
    each of the three microphones in turn, as three independent quantities,
    and their changes combined in quadrature into the one row of Table 1; so
    are the length and the radius of the capillary tubes.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param coupler: The coupler, the same for the three pairs.
    :param microphones: The three microphones.
    :param uncertainties: The standard uncertainty of each input quantity, a
        :class:`CouplerInputUncertainties`.
    :param temperature_c: The temperature, in °C.
    :param static_pressure_pa: The static pressure, in Pa.
    :param relative_humidity_percent: The relative humidity, in %.
    :param microphone: The microphone whose level is analysed, 1, 2 or 3
        (Default: 1).
    :param gas: A :class:`~phonometry.fluids.Fluid` for a coupler filled with a
        gas other than air (7.3.2.1), as in :func:`coupler_transfer_impedance`;
        ``None`` (default) takes humid air by Annex F at the conditions. A
        given gas keeps its properties whatever the conditions, so a step in
        the static pressure, the temperature or the humidity could not move
        them with it, and an uncertainty on any of the three is refused.
    :param heat_conduction_method: The method for :math:`E_V` (Default:
        ``"exact"``).
    :return: The :class:`CouplerParameterUncertainty`, with a component for
        each parameter given a non-zero uncertainty.
    :raises ValueError: for other than three microphones, a microphone index
        that is not 1, 2 or 3, an uncertainty on the volume or surface of a
        plane-wave coupler (they follow from its length and diameter), one
        on capillary tubes the coupler does not have, or one on the static
        pressure, the temperature or the humidity of a coupler filled with a
        given gas.
    """
    frequencies = _frequency_axis(frequencies_hz)
    if len(microphones) != len(_TRIAD_PAIRS):
        msg = "The triad needs three microphones."
        raise ValueError(msg)
    if microphone not in _OPPOSITE_PAIR:
        msg = "'microphone' must be 1, 2 or 3."
        raise ValueError(msg)
    method = require_choice(
        heat_conduction_method, "heat_conduction_method", _HEAT_CONDUCTION_METHODS
    )
    if gas is not None and (
        uncertainties.u_static_pressure_pa > 0.0
        or uncertainties.u_temperature_k > 0.0
        or uncertainties.u_relative_humidity_percent > 0.0
    ):
        msg = (
            "coupler_parameter_uncertainty: a coupler filled with a given 'gas' "
            "keeps the gas's properties, so 'u_static_pressure_pa', "
            "'u_temperature_k' and 'u_relative_humidity_percent' cannot move them."
        )
        raise ValueError(msg)
    mics = tuple(microphones)
    conditions = (
        float(temperature_c),
        float(static_pressure_pa),
        float(relative_humidity_percent),
    )
    nominal = _pair_impedances(frequencies, coupler, mics, conditions, method, gas)

    def moved(
        new_coupler: PlaneWaveCoupler | LargeVolumeCoupler = coupler,
        new_mics: tuple[ReciprocityMicrophone, ...] = mics,
        new_conditions: tuple[float, float, float] = conditions,
    ) -> NDArray[np.float64]:
        changed = _pair_impedances(
            frequencies, new_coupler, new_mics, new_conditions, method, gas
        )
        return np.abs(_level_change(nominal, changed, microphone))

    u = uncertainties
    components: dict[str, NDArray[np.float64]] = {}
    coupler_steps = _coupler_steps(
        coupler,
        (
            ("coupler_length", "length_m", u.u_coupler_length_m),
            ("coupler_diameter", "diameter_m", u.u_coupler_diameter_m),
            ("coupler_volume", "volume_m3", u.u_coupler_volume_m3),
            ("coupler_surface_area", "surface_area_m2", u.u_coupler_surface_area_m2),
        ),
    )
    for key, moved_coupler in coupler_steps.items():
        components[key] = moved(new_coupler=moved_coupler)
    capillary = _capillary_steps(
        coupler, u.u_capillary_length_m, u.u_capillary_radius_m
    )
    if capillary:
        components["capillary_tube_dimensions"] = np.sqrt(
            sum(moved(new_coupler=tubes) ** 2 for tubes in capillary)
        )
    for key, index, step in (
        ("static_pressure", 1, u.u_static_pressure_pa),
        ("temperature", 0, u.u_temperature_k),
        ("relative_humidity", 2, u.u_relative_humidity_percent),
    ):
        if step > 0.0:
            shifted = list(conditions)
            shifted[index] += step
            components[key] = moved(new_conditions=tuple(shifted))  # type: ignore[arg-type]
    for key, field, step in (
        ("front_cavity_depth", "front_cavity_depth_m", u.u_front_cavity_depth_m),
        ("front_cavity_volume", "front_cavity_volume_m3", u.u_front_cavity_volume_m3),
        ("equivalent_volume", "equivalent_volume_m3", u.u_equivalent_volume_m3),
        ("resonance_frequency", "resonance_frequency_hz", u.u_resonance_frequency_hz),
        ("loss_factor", "loss_factor", u.u_loss_factor),
    ):
        if step > 0.0:
            components[key] = np.sqrt(
                sum(
                    moved(new_mics=_moved_microphone(mics, i, field, step)) ** 2
                    for i in range(3)
                )
            )
    return CouplerParameterUncertainty(
        frequencies_hz=frequencies, components_db=components, microphone=microphone
    )


def _moved_microphone(
    microphones: tuple[ReciprocityMicrophone, ...], index: int, field: str, step: float
) -> tuple[ReciprocityMicrophone, ...]:
    """The triad with one parameter of one microphone moved by ``step``."""
    changed = dataclasses.replace(
        microphones[index], **{field: getattr(microphones[index], field) + step}
    )
    return microphones[:index] + (changed,) + microphones[index + 1 :]


def _coupler_steps(
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    moves: Sequence[tuple[str, str, float]],
) -> dict[str, PlaneWaveCoupler | LargeVolumeCoupler]:
    """The coupler with each of its dimensions moved, keyed by Table 1.

    :param moves: ``(key, field, standard uncertainty)`` for each dimension,
        the uncertainty already checked to be finite and non-negative.
    """
    steps: dict[str, PlaneWaveCoupler | LargeVolumeCoupler] = {}
    for key, field, u in moves:
        if u <= 0.0:
            continue
        if isinstance(coupler, PlaneWaveCoupler):
            if field in ("volume_m3", "surface_area_m2"):
                msg = (
                    f"A plane-wave coupler has no {key.replace('_', ' ')} of its "
                    "own: it follows from the length and the diameter."
                )
                raise ValueError(msg)
            base = float(getattr(coupler, field))
        elif field == "volume_m3":
            base = coupler.cavity_volume_m3
        elif field == "surface_area_m2":
            base = coupler.cavity_surface_m2
        else:
            base = float(getattr(coupler, field))
        steps[key] = dataclasses.replace(coupler, **{field: base + u})  # type: ignore[arg-type]
    return steps


def _capillary_steps(
    coupler: PlaneWaveCoupler | LargeVolumeCoupler,
    u_length: float,
    u_radius: float,
) -> list[PlaneWaveCoupler | LargeVolumeCoupler]:
    """The coupler with the length, then the radius, of its tubes moved, by
    uncertainties already checked to be finite and non-negative.
    """
    if u_length <= 0.0 and u_radius <= 0.0:
        return []
    tube = coupler.capillary
    if tube is None:
        msg = "The coupler has no capillary tubes to be uncertain about."
        raise ValueError(msg)
    moves: list[Callable[[CapillaryTube], CapillaryTube]] = []
    if u_length > 0.0:
        moves.append(lambda t: dataclasses.replace(t, length_m=t.length_m + u_length))
    if u_radius > 0.0:
        moves.append(lambda t: dataclasses.replace(t, radius_m=t.radius_m + u_radius))
    return [dataclasses.replace(coupler, capillary=move(tube)) for move in moves]

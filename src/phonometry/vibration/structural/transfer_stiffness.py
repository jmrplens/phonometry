#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Dynamic transfer stiffness of resilient elements (ISO 10846, Parts 1 to 5).

The vibro-acoustic transfer property of a resilient element (a vibration
isolator, mount, bellows or hose) is its **dynamic transfer stiffness**: the
frequency-dependent ratio of the *blocking force* phasor ``F2,b`` on the output
(receiver) side to the displacement phasor ``u1`` on the input (source) side,
with the output blocked (ISO 10846-1, 3.7), in N/m:

.. math::

   k_{2,1} = \frac{F_{2,\mathrm{b}}}{u_1}

For an isolator between two structures of large driving-point stiffness, the
force delivered to the receiver approximates this blocking force (ISO 10846-1,
Equation 7), so :math:`k_{2,1}` characterises the isolator's transmission.
Results are reported as a **level**, in dB, re the reference stiffness
:math:`k_0 = 1` N/m (ISO 10846-2 and -3, 3.17):

.. math::

   L_k = 10 \log_{10}\!\left( \frac{|k_{2,1}|^2}{k_0^2} \right)
   = 20 \log_{10}\!\left( \frac{|k_{2,1}|}{k_0} \right)

and, in the low-frequency range where inertial forces in the element are
negligible, the **loss factor** is the tangent of the phase angle of
:math:`k_{2,1}` (ISO 10846-1, 3.8):
:math:`\eta = \operatorname{Im}(k_{2,1}) / \operatorname{Re}(k_{2,1})`.

Three laboratory methods determine :math:`k_{2,1}`, in four parts:

* **Direct method** (ISO 10846-2 for resilient supports, ISO 10846-4 for
  other elements): measure the blocked output force ``F2,b`` and the input
  displacement ``u1`` directly: :math:`k_{2,1} = F_{2,\mathrm{b}} / u_1`. The
  mass between the element and the output force transducers biases the
  measured force; ISO 10846-4 Inequality (3) (ISO 10846-2 Inequality (2))
  bounds it, see :func:`check_output_mass`.
* **Indirect method** (ISO 10846-3, and ISO 10846-4 for other elements): load
  the output with a compact blocking mass ``m2`` and measure the vibration
  transmissibility :math:`T = u_2/u_1`; the blocking force is the mass's
  inertia force (ISO 10846-3, Equation 1):
  :math:`k_{2,1} = -(2\pi f)^2 (m_2 + m_\mathrm{f}) T` for :math:`T \ll 1`,
  where ``mf`` is the mass of the output flange of the test element. The
  approximation is valid only where :math:`|T| \le 0.1` (Inequality (2):
  :math:`\Delta L_{1,2} \ge 20` dB) and while the blocking mass still
  behaves rigidly,
  :math:`|10 \log_{10}(m_{2,\mathrm{eff}}^2/m_2^2)| \le 1` dB (ISO 10846-3
  Inequality (3), ISO 10846-4 Inequality (5)); see
  :func:`transfer_stiffness_indirect` and :func:`effective_blocking_mass`.
* **Driving-point method** (ISO 10846-5): measure the input force and the
  input acceleration with the output blocked, which gives the driving-point
  stiffness :math:`k_{1,1}` (Formula (3)). Below the upper limiting frequency
  :math:`f_\mathrm{UL}` of clause 6.2 its band averages stand for those of
  :math:`k_{2,1}` within 2 dB (Formula (7)); see
  :func:`driving_point_stiffness`.

Every part reports the result as one-third-octave-band averages of the squared
magnitude over at least five narrow-band frequencies (ISO 10846-2 Formula (6),
-3 Formula (7), -4 Formula (11), -5 Formula (6)): :func:`band_averaged_stiffness`.
The adequacy conditions the parts share, the output blocked by 20 dB and the
unwanted input directions 15 dB down, are :func:`check_blocked_output` and
:func:`check_unwanted_input`, and the Annex B uncertainty budget of
ISO 10846-5 is :func:`driving_point_uncertainty`.

The dynamic transfer stiffness is a member of the frequency-response-function
family (ISO 10846-1, Annex A / Table A.2):
:math:`k = j\omega Z = -\omega^2 m_{\mathrm{eff}}`, so it converts to
mechanical impedance and effective mass through
:func:`phonometry.vibration.convert_frf` (``"dynamic_stiffness"`` <->
``"impedance"`` <-> ``"apparent_mass"``). This module feeds the structure-borne
source and building prediction standards (ISO 9611, EN 15657, EN 12354-5).
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ..._report.metadata import ReportMetadata


from ..._internal.validation import (
    check_engine,
    require_finite,
    require_finite_fields,
    require_non_negative,
    require_positive,
    require_ranks,
    require_same_length,
)
from ..._internal.warnings import PhonometryWarning
from ...filters.frequencies import _nominal_freq_for_band
from ...metrology.reference_values import ISO1683_REFERENCE_VALUES
from ...metrology.uncertainty import Quantity, UncertaintyResult, combine_uncertainty
from .mechanical_mobility import convert_frf

#: Reference dynamic stiffness for the level ``L_k`` (ISO 10846-2/-3, 3.17), N/m.
REFERENCE_STIFFNESS: float = 1.0

#: Validity limit on the vibration transmissibility magnitude for the indirect
#: method (ISO 10846-3:2002, 6.1, Inequality (2)): measurements are valid only
#: where ``DeltaL1,2 = La1 - La2 >= 20 dB``, i.e. ``|T| <= 0.1``, which keeps
#: the ``T << 1`` approximation of Formula (1) accurate within 1 dB (12 %).
TRANSMISSIBILITY_LIMIT: float = 0.1

#: Fewest narrow-band frequencies a one-third-octave band average is taken
#: over. The band average of every part says "the summation is performed over
#: a minimum of n = 5 frequencies" (ISO 10846-2:2008 Formula (6), -3:2002
#: Formula (7), -4:2003 Formula (11), -5:2008 Formula (6)), and the analyser
#: clause of every part asks for "at least five distinct frequencies per
#: one-third-octave band" (-2 6.8 a), -3 6.8 a), -4 6.9 a), -5 6.6 a)), so a
#: band holding fewer has no band value determined for it.
MIN_FREQUENCIES_PER_BAND: int = 5

#: Minimum level difference between the input and output accelerations,
#: :math:`\Delta L_{1,2} = L_{a1} - L_{a2}`, for the output to count as
#: blocked, in dB (ISO 10846-2:2008 Inequality (1), -3:2002 Inequality (2),
#: -4:2003 Inequality (2), -5:2008 Inequality (1)).
_BLOCKED_OUTPUT_LIMIT_DB = 20.0

#: Minimum level difference between the input acceleration in the excitation
#: direction and in each direction perpendicular to it, in dB (ISO 10846-2:2008
#: Inequality (3), -3:2002 Inequality (5), -4:2003 Inequality (7), -5:2008
#: Inequality (2)).
_UNWANTED_INPUT_LIMIT_DB = 15.0

#: The factor of ISO 10846-4:2003 Inequality (3) and ISO 10846-2:2008
#: Inequality (2): the mass between the element and the output force
#: transducers may carry at most 6 % of the measured force as its own inertia,
#: ``m0 |a2| <= 0,06 |F2|``, which NOTE 1 of each states as a force-level bias
#: of 0,5 dB.
_OUTPUT_MASS_FACTOR = 0.06

#: ISO 10846-3:2002 Inequality (3) and ISO 10846-4:2003 Inequality (5): the
#: effective mass of the blocking mass stays within 1 dB (12 %) of ``m2``.
_EFFECTIVE_MASS_TOLERANCE_DB = 1.0

#: Below 40 Hz a deviation of the effective mass is the mass-spring behaviour
#: of the block on its soft supports, not a loss of rigidity, and is ignored
#: in finding ``f3`` (ISO 10846-3:2002 6.2.3, ISO 10846-4:2003 6.3.3.2).
_EFFECTIVE_MASS_IGNORED_BELOW_HZ = 40.0

#: ISO 10846-5:2008 6.2: ``f_UL`` is the lowest frequency at which the
#: driving-point stiffness level is 2 dB below its low-frequency value, and
#: below it Formula (7) holds within 2 dB.
_DRIVING_POINT_TOLERANCE_DB = 2.0

#: ISO 10846-5:2008 6.2: the low-frequency value is "the average for 1 Hz to
#: 20 Hz", and the method covers "the frequency range from f1 = 1 Hz" (clause 1).
_LOW_FREQUENCY_RANGE_HZ = (1.0, 20.0)

#: The coverage factor of ISO 10846-5:2008 Formula (B.3), ``U = 2u``.
_ANNEX_B_COVERAGE_FACTOR = 2.0

#: Standard uncertainties of ISO 10846-5:2008 Annex B, in dB, as B.3 writes
#: them. B.3.1 and B.3.2 print the numbers; B.3.4 to B.3.6 print the
#: expressions, which are kept exact here rather than taken as the one decimal
#: Table B.1 rounds them up to (0,3, 1,2 and 0,5 dB): a rectangular
#: distribution over a range of 1 dB for the test rig, over +/-2 dB for the
#: driving-point discrepancy and over a range of 1,5 dB for linearity.
_U_SIGNAL_DB = 0.3
_U_INSTRUMENTATION_DB = 0.5
_U_TEST_RIG_DB = 1.0 / (2.0 * math.sqrt(3.0))
_U_DISCREPANCY_DB = 2.0 / math.sqrt(3.0)
_U_LINEARITY_DB = 1.5 / (2.0 * math.sqrt(3.0))

#: One-third-octave bands on the base-ten grid of IEC 61260-1 that ISO 266
#: names: band ``x`` has its exact midband at ``1000 * 10**(x/10)`` Hz and its
#: edges a factor ``10**(1/20)`` either side, so ten bands span a decade.
_BANDS_PER_DECADE = 10.0
_REFERENCE_MIDBAND_HZ = 1000.0
_THIRD_OCTAVE = 3

#: The references ISO 10846-4:2003 3.15 and 3.16 give the force and
#: acceleration levels of Inequality (3): 1 µN and 1 µm/s², which are those of
#: ISO 1683:2015 Table 3.
_FORCE_REFERENCE_N = ISO1683_REFERENCE_VALUES["solid"]["force"].value
_ACCELERATION_REFERENCE_M_S2 = ISO1683_REFERENCE_VALUES["solid"]["acceleration"].value


class TransferStiffnessWarning(PhonometryWarning):
    """Advisory when an ISO 10846 adequacy condition or a band count fails."""


def _omega(frequency: ArrayLike) -> NDArray[np.float64]:
    r"""Angular frequency :math:`\omega = 2\pi f` (rad/s); rejects f <= 0."""
    f = np.asarray(frequency, dtype=np.float64)
    if np.any(f <= 0.0):
        msg = "'frequency' must be positive."
        raise ValueError(msg)
    return 2.0 * np.pi * f


def transfer_stiffness_level(
    stiffness: ArrayLike, *, reference: float = REFERENCE_STIFFNESS
) -> np.ndarray:
    r"""Level of the dynamic transfer stiffness (ISO 10846-2/-3, 3.17).

    :math:`L_k = 20 \log_{10}(|k_{2,1}| / k_0)` dB, with ``k0`` the reference
    stiffness.

    :param stiffness: Dynamic transfer stiffness :math:`k_{2,1}` (complex or
        real, scalar or array, non-zero), in N/m.
    :param reference: Reference stiffness ``k0`` (Default: 1 N/m), in N/m.
    :return: The level ``L_k``, in dB re ``k0``.
    :raises ValueError: for a non-positive reference, a non-finite stiffness,
        or a zero stiffness magnitude (a dead channel has no level).
    """
    reference = require_positive(reference, "reference")
    magnitude = np.abs(np.asarray(stiffness, dtype=np.complex128))
    # Two refusals, because they are two mistakes and the diagnosis has to be
    # true: a NaN compares False against the bound below, so folded into it it
    # was reported as a dead channel, which is a measurement that happened and
    # read zero rather than one that did not read at all.
    if not np.all(np.isfinite(magnitude)):
        msg = (
            "'stiffness' contains non-finite magnitudes; a level can only be "
            "taken of a stiffness that was measured."
        )
        raise ValueError(msg)
    if np.any(magnitude <= 0.0):
        msg = (
            "'stiffness' contains zero magnitudes; a zero (dead-channel) "
            "stiffness has no level."
        )
        raise ValueError(msg)
    return np.asarray(20.0 * np.log10(magnitude / reference), dtype=np.float64)


def loss_factor(stiffness: ArrayLike) -> np.ndarray:
    r"""Loss factor
    :math:`\eta = \operatorname{Im}(k_{2,1}) / \operatorname{Re}(k_{2,1})`
    (ISO 10846-1, 3.8).

    Valid in the low-frequency range where inertial forces in the element are
    negligible; it is the tangent of the phase angle of the transfer stiffness.

    :param stiffness: Dynamic transfer stiffness :math:`k_{2,1}` (complex,
        scalar or array, with a non-zero real part), in N/m.
    :return: The loss factor ``eta`` (dimensionless).
    :raises ValueError: for a purely imaginary stiffness
        (:math:`\operatorname{Re}(k_{2,1}) = 0`), for which the loss factor
        is undefined.
    """
    k = np.asarray(stiffness, dtype=np.complex128)
    if not np.all(np.abs(k.real) > 0.0):
        msg = (
            "'stiffness' contains purely imaginary values (Re = 0); the loss "
            "factor eta = Im/Re is undefined there."
        )
        raise ValueError(msg)
    return np.asarray(k.imag / k.real, dtype=np.float64)


def transfer_stiffness_direct(
    blocking_force: ArrayLike, input_displacement: ArrayLike
) -> np.ndarray:
    r"""Dynamic transfer stiffness by the direct method (ISO 10846-2).

    :math:`k_{2,1} = F_{2,\mathrm{b}} / u_1`, the blocked output force phasor over
    the input displacement phasor.

    :param blocking_force: Blocked output force phasor ``F2,b`` (complex), in N.
    :param input_displacement: Input displacement phasor ``u1`` (complex,
        non-zero), in m.
    :return: The dynamic transfer stiffness :math:`k_{2,1}`, in N/m.
    :raises ValueError: for a zero input displacement (dead input channel).
    """
    f2b = np.asarray(blocking_force, dtype=np.complex128)
    u1 = np.asarray(input_displacement, dtype=np.complex128)
    if not np.all(np.abs(u1) > 0.0):
        msg = (
            "'input_displacement' contains zeros (dead input channel); the "
            "ratio k2,1 = F2,b/u1 is undefined there."
        )
        raise ValueError(msg)
    return np.asarray(f2b / u1, dtype=np.complex128)


def transfer_stiffness_indirect(
    frequency: ArrayLike,
    transmissibility: ArrayLike,
    blocking_mass: float,
    *,
    flange_mass: float = 0.0,
) -> np.ndarray:
    r"""Dynamic transfer stiffness by the indirect method (ISO 10846-3, Eq. 1).

    :math:`k_{2,1} = -(2\pi f)^2 (m_2 + m_\mathrm{f}) T`: the blocking force is the
    inertia force of a compact blocking mass ``m2`` (plus the output flange
    mass ``mf``), derived from the measured vibration transmissibility
    :math:`T = u_2/u_1`. Valid for :math:`T \ll 1` (i.e. well above the
    mass/spring resonance).

    **Validity (ISO 10846-3, clause 6).** The :math:`T \ll 1` approximation
    of Formula (1) is required accurate within 1 dB, i.e. within 12 % of the
    calculated stiffness magnitude. This holds only where Inequality (2) is
    met: :math:`\Delta L_{1,2} = L_{a1} - L_{a2} \ge 20` dB, i.e.
    :math:`|T| \le 0.1` (:data:`TRANSMISSIBILITY_LIMIT`). Lines with
    ``|T|`` above that limit
    (routine near or below the mass/spring resonance) trigger a
    :class:`TransferStiffnessWarning`; the result marks each of them as not
    valid, and its band average leaves them out. The upper frequency limit
    ``f3`` additionally requires the blocking mass to vibrate as a rigid
    body: results are valid only while its effective mass ``m2,eff``,
    measured per Formula (4) as
    :math:`m_{2,\mathrm{eff}} = 2 F_2 / (a'_1 + a''_1)` (two accelerometers
    spaced :math:`D = \sqrt{S}` across the contact area), stays within 1 dB
    of the rigid mass,
    :math:`|10 \log_{10}(m_{2,\mathrm{eff}}^2 / m_2^2)| \le 1` dB
    (Inequality (3), 6.2.3); :func:`effective_blocking_mass` finds ``f3``.

    :param frequency: Frequency ``f``, in hertz (scalar or array).
    :param transmissibility: Vibration transmissibility
        :math:`T = u_2/u_1` (complex,
        scalar or array; velocity and acceleration ratios have the same value).
    :param blocking_mass: Blocking mass ``m2``, in kg (> 0).
    :param flange_mass: Output-flange mass ``mf``, in kg (Default: 0.0).
    :return: The dynamic transfer stiffness :math:`k_{2,1}`, in N/m.
    :raises ValueError: for a non-positive frequency or blocking mass.
    :warns TransferStiffnessWarning: where any :math:`\lvert T\rvert > 0.1`
        (Inequality (2) violated).
    """
    blocking_mass = require_positive(blocking_mass, "blocking_mass")
    flange_mass = require_non_negative(flange_mass, "flange_mass")
    omega = _omega(frequency)
    t = np.asarray(transmissibility, dtype=np.complex128)
    magnitude = np.abs(t)
    if np.any(magnitude > TRANSMISSIBILITY_LIMIT):
        worst = float(np.max(magnitude))
        warnings.warn(
            f"|T| up to {worst:.3g} exceeds {TRANSMISSIBILITY_LIMIT:g} "
            "(DeltaL1,2 < 20 dB): ISO 10846-3 Inequality (2) is violated and "
            "the T << 1 approximation of Formula (1) is no longer accurate "
            "within 1 dB (12 %); those bands lie outside the valid frequency "
            "range of the indirect method.",
            TransferStiffnessWarning,
            stacklevel=2,
        )
    return np.asarray(
        -(omega**2) * (blocking_mass + flange_mass) * t, dtype=np.complex128
    )


def blocking_force_ratio(
    driving_point_stiffness: ArrayLike, termination_stiffness: ArrayLike
) -> np.ndarray:
    r"""Ratio of the delivered force to the blocking force (ISO 10846-1, Eq. 6).

    For an isolator driving a receiving structure, the output force for a
    given source displacement ``u1`` is
    :math:`F_2 = k_{2,1} u_1 / (1 + k_{2,2}/k_\mathrm{t})`
    (Equation (6)), where ``k2,2`` is the isolator's output driving-point
    stiffness (output blocked at the input) and ``kt`` the dynamic
    driving-point stiffness of the termination. This function returns

    .. math::

       \frac{F_2}{F_{2,\mathrm{b}}} = \frac{1}{1 + k_{2,2}/k_\mathrm{t}}

    the factor by which the delivered force deviates from the blocking force
    :math:`F_{2,\mathrm{b}} = k_{2,1} u_1` of Equation (7). For
    :math:`|k_{2,2}| < 0.1 |k_\mathrm{t}|` the ratio is within 10 % of unity
    (:math:`1/1.1 = 0.909` at the limit), which is the
    stiffness mismatch that justifies characterising an isolator by its
    blocked transfer stiffness alone.

    :param driving_point_stiffness: Output driving-point stiffness ``k2,2`` of
        the isolator (complex, scalar or array), in N/m.
    :param termination_stiffness: Driving-point stiffness ``kt`` of the
        receiving structure (complex, scalar or array, non-zero), in N/m.
    :return: The complex ratio ``F2/F2,b``.
    :raises ValueError: for a zero termination stiffness.
    """
    k22 = np.asarray(driving_point_stiffness, dtype=np.complex128)
    kt = np.asarray(termination_stiffness, dtype=np.complex128)
    if not np.all(np.abs(kt) > 0.0):
        msg = "'termination_stiffness' must be non-zero."
        raise ValueError(msg)
    return np.asarray(1.0 / (1.0 + k22 / kt), dtype=np.complex128)


def base_transmissibility(
    frequency: ArrayLike, mass: float, stiffness: float, damping: float = 0.0
) -> np.ndarray:
    r"""Transmissibility of a mass on an ideal resilient element (model).

    The output mass ``m`` on a massless Kelvin-Voigt element (spring ``k`` in
    parallel with a viscous damper ``c``) driven at the input has the
    base-excitation transmissibility

    .. math::

       T = \frac{u_2}{u_1}
       = \frac{k + j\omega c}{k - \omega^2 m + j\omega c}

    This ideal-element model is the counterpart of the indirect-method test
    arrangement (ISO 10846-3): feeding ``T`` into
    :func:`transfer_stiffness_indirect` with the same mass recovers the
    element's transfer stiffness :math:`k + j\omega c` in the high-frequency
    limit :math:`T \ll 1`.

    :param frequency: Frequency ``f``, in hertz (scalar or array).
    :param mass: Output mass ``m``, in kg.
    :param stiffness: Element stiffness ``k``, in N/m.
    :param damping: Viscous damping ``c``, in N.s/m (Default: 0.0).
    :return: The complex transmissibility ``T``.
    """
    mass = require_positive(mass, "mass")
    stiffness = require_positive(stiffness, "stiffness")
    damping = require_non_negative(damping, "damping")
    omega = _omega(frequency)
    numerator = stiffness + 1j * omega * damping
    denominator = stiffness - omega**2 * mass + 1j * omega * damping
    return np.asarray(numerator / denominator, dtype=np.complex128)


@dataclass(frozen=True)
class TransferStiffnessResult:
    r"""A dynamic transfer stiffness over frequency (ISO 10846).

    :ivar frequencies: Frequencies, in hertz.
    :ivar transfer_stiffness: Complex :math:`k_{2,1}` per frequency, in N/m.
    :ivar blocking_mass: Blocking mass ``m2`` used (indirect method), in kg, or
        ``None`` for the direct method.
    :ivar valid: Per frequency, whether the line meets the adequacy conditions
        of its part and so enters the band average (results that fail them
        "shall be excluded from the evaluation of the dynamic stiffness
        function", ISO 10846-2, -4 and -5 7.6.1, ISO 10846-3 7.5.1), or
        ``None`` when every line does. The indirect method sets it from
        Inequality (2), :math:`|T| \le 0.1`.
    """

    frequencies: np.ndarray
    transfer_stiffness: np.ndarray
    blocking_mass: float | None = None
    valid: np.ndarray | None = None

    def __post_init__(self) -> None:
        r"""Reject a spectrum whose stiffnesses do not run over its own frequencies.

        A plain length difference is loud, in both directions, and the fiche is
        not where it shows. :meth:`report` characterises the element by its
        low-frequency plateau, read at the lowest entry of ``frequencies``,
        which for an ascending sweep is the first one: an index no missing or
        extra value at the end can move, so the :math:`|k_{2,1}|`, ``L_k`` and
        ``eta`` it would print are the correct ones to the last digit. What
        stops the sheet is the ``L_k(f)`` spectrum beside them, where
        matplotlib complains that x and y must have the same first dimension, a
        stiffness one short and one long alike; :meth:`plot` fails there
        directly, and :meth:`to` at numpy's refusal to broadcast the stiffness
        against a function of the frequency. None of the three names a field,
        and the shapes they quote belong to whatever the plotter or the
        arithmetic was handed, not to the two attributes that disagree.

        The length that does pass in silence is the one numpy is willing to
        stretch. A single stiffness against a swept ``frequencies`` is
        broadcast by :meth:`to`, which hands back an impedance or an effective
        mass at every frequency, every one of them computed from that one
        value: a smooth roll-off with the shape of a measured curve and the
        content of a single point. Counting the entries refuses it, because one
        stiffness disagrees with three frequencies exactly as two do.

        Both fields must also be finite. Neither determination can emit a
        non-finite stiffness from valid data - the direct method refuses a
        dead input channel and the indirect method multiplies finite
        inertia terms by the measured transmissibility - so an ``inf`` here
        is always an overflowed or clipped channel, not an undeterminable
        band. Admitting it printed ``Lk = inf dB re 1 N/m`` boxed as the
        fiche headline, with a loss factor of ``nan`` beside it and nothing
        on the page qualifying either.

        The validity flags, when given, are one boolean per frequency: a count
        that disagrees would drop lines from the band average, or keep lines
        the adequacy conditions refused, without any figure showing which.

        :raises ValueError: if ``transfer_stiffness`` or ``valid`` does not
            carry one value per frequency, a field carries an extra axis,
            ``valid`` is not boolean, or either numeric field carries a
            non-finite value.
        """
        require_ranks(self, frequencies=1, transfer_stiffness=1, valid=1)
        require_same_length(
            self, "frequencies", "transfer_stiffness", "valid", axis="frequency"
        )
        require_finite_fields(self, "frequencies", "transfer_stiffness")
        if self.valid is not None and np.asarray(self.valid).dtype != np.bool_:
            msg = "TransferStiffnessResult: 'valid' must be boolean, one flag per frequency."
            raise ValueError(msg)

    @property
    def magnitude(self) -> np.ndarray:
        r"""Transfer-stiffness magnitude :math:`|k_{2,1}|`, in N/m."""
        return np.asarray(np.abs(self.transfer_stiffness), dtype=np.float64)

    @property
    def levels(self) -> np.ndarray:
        """Transfer-stiffness level ``L_k`` re 1 N/m, in dB (3.17)."""
        return transfer_stiffness_level(self.transfer_stiffness)

    @property
    def loss_factor(self) -> np.ndarray:
        r"""Loss factor :math:`\eta = \operatorname{Im}/\operatorname{Re}`
        per frequency (3.8).
        """
        return loss_factor(self.transfer_stiffness)

    def to(self, target: str) -> np.ndarray:
        r"""Convert :math:`k_{2,1}` to an FRF (ISO 10846-1 Annex A / Table A.2).

        ``target`` is ``"impedance"`` (:math:`Z = k/(j\omega)`) or
        ``"apparent_mass"`` (:math:`m_{\mathrm{eff}} = -k/\omega^2`); see
        :func:`phonometry.vibration.convert_frf`.
        """
        return convert_frf(
            self.transfer_stiffness, self.frequencies, "dynamic_stiffness", target
        )

    def band_average(self) -> BandAveragedStiffness:
        r"""One-third-octave-band averages of :math:`k_{2,1}` (every part's band average).

        ISO 10846-2:2008 Formula (6), ISO 10846-3:2002 Formula (7) and
        ISO 10846-4:2003 Formula (11) average the squared magnitude over the
        narrow-band lines of each band; see :func:`band_averaged_stiffness`.
        Lines :attr:`valid` marks as failing their adequacy conditions are
        left out, as the parts require.

        :return: The :class:`BandAveragedStiffness`.
        :warns TransferStiffnessWarning: when a band holds fewer than
            :data:`MIN_FREQUENCIES_PER_BAND` valid lines.
        """
        return _band_average(
            self.frequencies,
            self.transfer_stiffness,
            self.valid,
            owner="TransferStiffnessResult.band_average",
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the transfer-stiffness level ``L_k(f)``.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_transfer_stiffness

        return plot_transfer_stiffness(
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
        r"""Render a dynamic-transfer-stiffness fiche to a PDF (ISO 10846).

        Writes a one-page transfer-stiffness characterisation report for a
        resilient element: the standard-basis line naming the determination
        method (direct, ISO 10846-2:2008, or indirect blocking-mass,
        ISO 10846-3:2002; definition per ISO 10846-1:2008), an optional metadata
        header, a two-panel body with a compact table of the FRF's
        characteristic points (the method, the blocking mass for the indirect
        method, the frequency range, and the low-frequency stiffness plateau
        :math:`|k_{2,1}|`, its level ``L_k`` and the loss factor ``eta``
        there) beside
        the transfer-stiffness level spectrum ``L_k(f)``, the one-third-octave
        band levels of :meth:`band_average` that the test report of
        ISO 10846-2 (9 m)) and ISO 10846-3 (10 j)) presents, a boxed
        low-frequency ``L_k`` with the stiffness magnitude and method
        alongside, and a footer identity/disclaimer block.

        The characteristic points are read at the lowest line :attr:`valid`
        keeps, since the part excludes the others from the evaluation, and the
        spectrum draws the excluded lines apart. A band holding fewer than
        five valid lines prints its line count instead of a level. A
        transfer-stiffness determination is a characterisation, so there is
        no pass/fail verdict.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata` supplying
            the header identity (``specimen`` is the tested resilient element)
            and the footer identity; the ``requirement`` field is ignored.
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: Accepted for a uniform ``.report()`` signature; the
            transfer-stiffness fiche has a single body layout, so it has no
            effect.
        :param language: Fiche language: ``"en"`` (default, English) or
            ``"es"`` (Spanish, with a comma decimal separator).
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"`` or ``language``
            is unknown, or :attr:`valid` marks every line as failing its
            adequacy conditions (there is then no value to report).
        :raises ImportError: If reportlab or matplotlib is not installed. The
            fiche always embeds the ``L_k(f)`` spectrum, so both are required
            (``pip install "phonometry[report,plot]"``).
        """
        from ..._i18n import check_language

        check_language(language)
        check_engine(engine)
        from ..._report.iso10846 import render_transfer_stiffness_report

        return render_transfer_stiffness_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def indirect_transfer_stiffness_result(
    frequency: ArrayLike,
    transmissibility: ArrayLike,
    blocking_mass: float,
    *,
    flange_mass: float = 0.0,
) -> TransferStiffnessResult:
    r"""Indirect-method transfer stiffness bundled as a :class:`TransferStiffnessResult`.

    See :func:`transfer_stiffness_indirect` for the ISO 10846-3 validity
    conditions (Inequalities (2) and (3)); bands with :math:`|T| > 0.1`
    trigger a :class:`TransferStiffnessWarning`, and the result marks them
    not :attr:`~TransferStiffnessResult.valid`, so that
    :meth:`~TransferStiffnessResult.band_average` leaves them out.

    :param frequency: Frequencies ``f``, in hertz (array).
    :param transmissibility: Vibration transmissibility
        :math:`T = u_2/u_1` (complex).
    :param blocking_mass: Blocking mass ``m2``, in kg (> 0).
    :param flange_mass: Output-flange mass ``mf``, in kg (Default: 0.0).
    :return: The :class:`TransferStiffnessResult` (indirect method).
    :warns TransferStiffnessWarning: where any :math:`\lvert T\rvert > 0.1`
        (Inequality (2) violated).
    """
    freq = np.asarray(frequency, dtype=np.float64)
    k = transfer_stiffness_indirect(
        freq, transmissibility, blocking_mass, flange_mass=flange_mass
    )
    magnitude = np.abs(np.asarray(transmissibility, dtype=np.complex128))
    valid = np.broadcast_to(magnitude <= TRANSMISSIBILITY_LIMIT, k.shape).copy()
    return TransferStiffnessResult(
        frequencies=freq,
        transfer_stiffness=k,
        blocking_mass=float(blocking_mass),
        valid=valid,
    )


# ---------------------------------------------------------------------------
# One-third-octave band average: ISO 10846-2 Formula (6), -3 Formula (7),
# -4 Formula (11), -5 Formula (6).
# ---------------------------------------------------------------------------


def _frequency_axis(frequencies: ArrayLike, owner: str) -> NDArray[np.float64]:
    """One-dimensional, finite, positive frequencies, in hertz."""
    freq = np.asarray(frequencies, dtype=np.float64)
    if freq.ndim != 1 or freq.size == 0:
        msg = f"{owner}: 'frequencies' must be a non-empty one-dimensional array."
        raise ValueError(msg)
    if not np.all(np.isfinite(freq)) or np.any(freq <= 0.0):
        msg = f"{owner}: 'frequencies' must be finite and positive."
        raise ValueError(msg)
    return freq


def _require_increasing(frequencies: NDArray[np.float64], owner: str) -> None:
    """Refuse a frequency axis that does not rise strictly, line after line.

    A limit frequency is the *lowest* line at which a condition fails, and
    everything above it is cut off, so the lines have to be read in order and
    none may repeat: a repeated line would count twice towards the five of a
    band, and an unsorted sweep would put the cut in the middle of the data.
    """
    if np.any(np.diff(frequencies) <= 0.0):
        msg = (
            f"{owner}: 'frequencies' must increase strictly, one line per "
            "frequency, because the limit frequency is the lowest line at which "
            "the condition fails."
        )
        raise ValueError(msg)


def _band_index(frequencies: NDArray[np.float64]) -> NDArray[np.int64]:
    """Base-ten one-third-octave band of each line (band 0 is the 1 kHz band)."""
    x = _BANDS_PER_DECADE * np.log10(frequencies / _REFERENCE_MIDBAND_HZ)
    return np.asarray(np.floor(x + 0.5), dtype=np.int64)


def _as_flags(
    value: ArrayLike, shape: tuple[int, ...], owner: str, name: str
) -> NDArray[np.bool_]:
    """A boolean mask with one flag per frequency."""
    flags = np.asarray(value)
    if flags.dtype != np.bool_ or flags.shape != shape:
        msg = f"{owner}: '{name}' must be boolean, one flag per frequency."
        raise ValueError(msg)
    return flags


@dataclass(frozen=True)
class BandAveragedStiffness:
    r"""One-third-octave-band averages of a narrow-band dynamic stiffness (ISO 10846).

    Every part of the series reduces the narrow-band stiffness to one value
    per one-third-octave band by averaging the squared magnitude over the
    ``n`` lines of the band (ISO 10846-2:2008 Formula (6), -3:2002 Formula (7),
    -4:2003 Formula (11), -5:2008 Formula (6)):

    .. math::

       k_\mathrm{av} = \left\{ \frac{1}{n} \sum_{i=1}^{n}
       \lvert k(f_i) \rvert^2 \right\}^{1/2}, \qquad n \ge 5

    and reports it as the level
    :math:`L_{k,\mathrm{av}} = 10 \lg(k_\mathrm{av}^2/k_0^2)` re
    :math:`k_0 = 1` N/m (ISO 10846-2, -3 and -4 3.18, ISO 10846-5 3.17). A band
    holding fewer than :data:`MIN_FREQUENCIES_PER_BAND` lines has no value:
    its stiffness is NaN and :attr:`determined` is ``False``.

    :ivar nominal_frequencies: Preferred centre frequency of each band
        (ISO 266), in hertz.
    :ivar center_frequencies: Exact base-ten midband frequency
        :math:`1000 \cdot 10^{x/10}` of each band, in hertz; a line belongs to
        the band whose edges, a factor :math:`10^{1/20}` either side, enclose
        it.
    :ivar stiffness: Band average :math:`k_\mathrm{av}`, in N/m, NaN where the
        band holds fewer than five lines.
    :ivar line_counts: Number of narrow-band lines averaged in each band.
    """

    nominal_frequencies: np.ndarray
    center_frequencies: np.ndarray
    stiffness: np.ndarray
    line_counts: np.ndarray

    def __post_init__(self) -> None:
        """Reject bands whose value and count disagree.

        A band value exists exactly where five or more lines were averaged:
        a number beside a count of three would be printed as a determined band
        the standard does not allow, and a NaN beside a count of eight would
        hide a band that was measured. Both are refused, as are fields of
        different lengths and counts that are not whole numbers.

        :raises ValueError: if the fields disagree in length or rank, the
            frequencies are not finite and positive, a count is negative or
            not an integer, or the stiffness is not a positive finite number
            exactly where the count reaches five.
        """
        owner = type(self).__name__
        require_ranks(
            self,
            nominal_frequencies=1,
            center_frequencies=1,
            stiffness=1,
            line_counts=1,
        )
        require_same_length(
            self,
            "nominal_frequencies",
            "center_frequencies",
            "stiffness",
            "line_counts",
        )
        require_finite_fields(self, "nominal_frequencies", "center_frequencies")
        for name in ("nominal_frequencies", "center_frequencies"):
            if np.any(np.asarray(getattr(self, name), dtype=np.float64) <= 0.0):
                msg = f"{owner}: '{name}' must be positive."
                raise ValueError(msg)
        counts = np.asarray(self.line_counts)
        if counts.dtype.kind not in "iu" or np.any(counts < 0):
            msg = f"{owner}: 'line_counts' must be non-negative integers."
            raise ValueError(msg)
        k = np.asarray(self.stiffness, dtype=np.float64)
        determined = counts >= MIN_FREQUENCIES_PER_BAND
        value_ok = np.isfinite(k) & (k > 0.0)
        if np.any(value_ok != determined):
            msg = (
                f"{owner}: 'stiffness' must be a positive finite value exactly "
                f"where a band holds at least {MIN_FREQUENCIES_PER_BAND} lines, "
                "and NaN elsewhere."
            )
            raise ValueError(msg)

    @property
    def determined(self) -> np.ndarray:
        """Per band, whether it holds enough lines to have a value.

        :return: One boolean per band.
        """
        return np.asarray(self.line_counts) >= MIN_FREQUENCIES_PER_BAND

    @property
    def levels(self) -> np.ndarray:
        r"""Band level :math:`L_{k,\mathrm{av}}` re 1 N/m, in dB, NaN where undetermined.

        :return: One level per band.
        """
        k = np.asarray(self.stiffness, dtype=np.float64)
        out = np.full(k.shape, np.nan)
        determined = self.determined
        out[determined] = 20.0 * np.log10(k[determined] / REFERENCE_STIFFNESS)
        return out

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the band levels, with the undetermined bands marked.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the band-level bars.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_band_averaged_stiffness

        return plot_band_averaged_stiffness(
            self, ax=ax, language=check_language(language), **kwargs
        )


def band_averaged_stiffness(
    frequencies: ArrayLike,
    stiffness: ArrayLike,
    *,
    valid: ArrayLike | None = None,
) -> BandAveragedStiffness:
    r"""One-third-octave-band averages of a narrow-band stiffness (ISO 10846).

    The band average of every part of the series, ISO 10846-2:2008
    Formula (6), -3:2002 Formula (7), -4:2003 Formula (11) and -5:2008
    Formula (6):

    .. math::

       k_\mathrm{av} = \left\{ \frac{1}{n} \sum_{i=1}^{n}
       \lvert k(f_i) \rvert^2 \right\}^{1/2}

    "where the summation is performed over a minimum of n = 5 frequencies".
    Averaging the squared magnitude "is chosen to emphasize the maxima in the
    stiffness values" (NOTE 1), and the phase is lost (NOTE 3). Each line is
    assigned to the base-ten one-third-octave band that encloses it, the bands
    named by the ISO 266 centre frequencies the parts ask for.

    **Fewer than five lines.** The parts leave no band value to a band that
    holds fewer: the analyser shall resolve "at least five distinct
    frequencies per one-third-octave band", and a stepped or swept sine shall
    put at least five frequencies in "each one-third-octave band for which
    stiffness data are determined". Such a band is returned undetermined (NaN)
    and a :class:`TransferStiffnessWarning` names it. Lines ``valid`` marks
    ``False`` are left out first, as the parts exclude results that fail their
    adequacy conditions; bands beyond the outermost valid line are not listed,
    and a band inside the range with no valid line at all is undetermined
    without a warning, since its lines were excluded rather than missing.

    :param frequencies: Narrow-band frequencies :math:`f_i`, in hertz
        (one-dimensional, distinct).
    :param stiffness: Dynamic stiffness :math:`k(f_i)` at each frequency
        (complex or real, finite), in N/m: a transfer stiffness
        :math:`k_{2,1}` or a driving-point stiffness :math:`k_{1,1}`.
    :param valid: Per frequency, whether the line enters the average
        (Default: ``None``, every line).
    :return: The :class:`BandAveragedStiffness`.
    :raises ValueError: for frequencies that are not one-dimensional, finite,
        positive and distinct, a stiffness of another length or not finite, a
        mask that is not boolean or has another length, or no valid line.
    :warns TransferStiffnessWarning: when a band holds between one and four
        valid lines.
    """
    return _band_average(frequencies, stiffness, valid, owner="band_averaged_stiffness")


def _band_average(
    frequencies: ArrayLike,
    stiffness: ArrayLike,
    valid: ArrayLike | None,
    *,
    owner: str,
    quiet_up_to_hz: float | None = None,
) -> BandAveragedStiffness:
    """The body of :func:`band_averaged_stiffness`.

    The public function and the two ``band_average`` methods reach it at the
    same depth, so the warning below points at the caller's own line from all
    three. ``quiet_up_to_hz`` spares the bands centred at or below it the
    warning: ISO 10846-5 7.5 asks for five lines per band only above 20 Hz,
    its 0,2 Hz spacing below leaves the lowest bands short of five, and the
    NOTE to clause 9 m) accepts narrow-band data there instead.
    """
    freq = _frequency_axis(frequencies, owner)
    if np.unique(freq).size != freq.size:
        msg = f"{owner}: 'frequencies' must be distinct, one line per frequency."
        raise ValueError(msg)
    k = np.asarray(stiffness, dtype=np.complex128)
    if k.shape != freq.shape:
        msg = (
            f"{owner}: 'stiffness' must carry one value per frequency; got "
            f"{k.shape} against {freq.shape}."
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(k)):
        msg = f"{owner}: 'stiffness' must be finite."
        raise ValueError(msg)
    mask = (
        np.ones(freq.shape, dtype=bool)
        if valid is None
        else _as_flags(valid, freq.shape, owner, "valid")
    )
    if not np.any(mask):
        msg = f"{owner}: no valid line is left to average."
        raise ValueError(msg)
    index = _band_index(freq)[mask]
    first = int(index.min())
    bands = np.arange(first, int(index.max()) + 1)
    offset = index - first
    counts = np.bincount(offset, minlength=bands.size)
    power = np.bincount(offset, weights=np.abs(k[mask]) ** 2, minlength=bands.size)
    determined = counts >= MIN_FREQUENCIES_PER_BAND
    k_av = np.full(bands.size, np.nan)
    k_av[determined] = np.sqrt(power[determined] / counts[determined])
    exact = _REFERENCE_MIDBAND_HZ * 10.0 ** (bands / _BANDS_PER_DECADE)
    nominal = np.array(
        [_nominal_freq_for_band(float(f), _THIRD_OCTAVE) for f in exact],
        dtype=np.float64,
    )
    short = (counts > 0) & ~determined
    if quiet_up_to_hz is not None:
        short &= exact > quiet_up_to_hz
    if np.any(short):
        listed = ", ".join(
            f"{f:g} Hz ({n})"
            for f, n in zip(nominal[short], counts[short], strict=True)
        )
        warnings.warn(
            f"ISO 10846 takes a band average over at least "
            f"{MIN_FREQUENCIES_PER_BAND} frequencies; these bands hold fewer "
            f"valid lines and are left undetermined: {listed}.",
            TransferStiffnessWarning,
            stacklevel=3,
        )
    return BandAveragedStiffness(
        nominal_frequencies=nominal,
        center_frequencies=exact,
        stiffness=k_av,
        line_counts=counts,
    )


# ---------------------------------------------------------------------------
# Adequacy of the test arrangement: the output blocked, the input
# unidirectional, and the mass in front of the output force transducers.
# ---------------------------------------------------------------------------

#: The two level-difference conditions the parts share, by name.
_CONDITIONS: tuple[str, ...] = ("blocked_output", "unwanted_input")


@dataclass(frozen=True)
class LevelDifferenceCheck:
    r"""An ISO 10846 level-difference condition judged frequency by frequency.

    Two conditions of the series take this form. The output is blocked where
    the input acceleration level exceeds the output one by at least 20 dB,
    :math:`\Delta L_{1,2} = L_{a1} - L_{a2} \ge 20` dB (``"blocked_output"``;
    ISO 10846-2:2008 Inequality (1), -3:2002 Inequality (2), -4:2003
    Inequality (2), -5:2008 Inequality (1)). The input is unidirectional where
    the acceleration in the excitation direction exceeds that in every
    direction perpendicular to it by at least 15 dB,
    :math:`L_{a(\mathrm{excitation})} - L_{a(\mathrm{unwanted})} \ge 15` dB
    (``"unwanted_input"``; ISO 10846-2:2008 Inequality (3), -3:2002
    Inequality (5), -4:2003 Inequality (7), -5:2008 Inequality (2)). The
    measurements are valid only at the frequencies where the condition holds.

    :ivar frequencies: Frequencies judged, in hertz.
    :ivar difference_db: The level difference at each frequency, in dB
        (``+inf`` where the second level is that of a zero signal).
    :ivar limit_db: The least difference the condition accepts, in dB.
    :ivar condition: ``"blocked_output"`` or ``"unwanted_input"``.
    """

    frequencies: np.ndarray
    difference_db: np.ndarray
    limit_db: float
    condition: Literal["blocked_output", "unwanted_input"]

    def __post_init__(self) -> None:
        """Reject a check whose fields disagree or that names no condition.

        :raises ValueError: if the arrays differ in length or rank, a
            frequency is not finite, a difference is NaN or ``-inf``, the
            limit is not finite, or the condition is unknown.
        """
        owner = type(self).__name__
        require_ranks(self, frequencies=1, difference_db=1)
        require_same_length(self, "frequencies", "difference_db", axis="frequency")
        require_finite_fields(self, "frequencies")
        require_finite(self.limit_db, "limit_db")
        difference = np.asarray(self.difference_db, dtype=np.float64)
        if np.any(np.isnan(difference)) or np.any(np.isneginf(difference)):
            msg = f"{owner}: 'difference_db' must not hold NaN or -inf."
            raise ValueError(msg)
        if self.condition not in _CONDITIONS:
            msg = (
                f"{owner}: 'condition' must be one of {_CONDITIONS}; "
                f"got {self.condition!r}."
            )
            raise ValueError(msg)

    @property
    def holds(self) -> np.ndarray:
        """Per frequency, whether the difference reaches the limit.

        :return: One boolean per frequency.
        """
        return np.asarray(self.difference_db, dtype=np.float64) >= self.limit_db

    @property
    def passes(self) -> bool:
        """Whether the condition holds at every frequency judged.

        :return: ``True`` when no frequency falls short of the limit.
        """
        return bool(np.all(self.holds))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a LevelDifferenceCheck has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the level difference against its limit, failures marked.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the level-difference curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_level_difference_check

        return plot_level_difference_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _level_spectrum(
    value: ArrayLike, shape: tuple[int, ...], owner: str, name: str
) -> NDArray[np.float64]:
    """A level spectrum, one level per frequency (or one row per direction)."""
    level = np.asarray(value, dtype=np.float64)
    if level.ndim not in (1, 2) or level.shape[-1:] != shape:
        msg = f"{owner}: '{name}' must carry one level per frequency."
        raise ValueError(msg)
    if np.any(np.isnan(level)) or np.any(np.isposinf(level)):
        msg = f"{owner}: '{name}' must not hold NaN or +inf."
        raise ValueError(msg)
    return level


def _warn_level_difference(
    check: LevelDifferenceCheck, clauses: str, meaning: str
) -> None:
    """Warn, naming the worst frequency, when a level-difference check fails."""
    if check.passes:
        return
    holds = check.holds
    difference = np.asarray(check.difference_db, dtype=np.float64)
    worst = int(np.argmin(difference))
    warnings.warn(
        f"{np.count_nonzero(~holds)} of {holds.size} frequencies fall short of "
        f"the {check.limit_db:g} dB of {clauses}, down to "
        f"{difference[worst]:.1f} dB at {float(check.frequencies[worst]):g} Hz: "
        f"{meaning} The measurements are valid only where it holds, and the "
        "parts exclude the rest from the evaluation.",
        TransferStiffnessWarning,
        stacklevel=3,
    )


def check_blocked_output(
    frequencies: ArrayLike,
    input_acceleration_level_db: ArrayLike,
    output_acceleration_level_db: ArrayLike,
) -> LevelDifferenceCheck:
    r"""Is the output side blocked well enough for the stiffness to mean anything?

    Every part of ISO 10846 is valid "only for those frequencies where"

    .. math::

       \Delta L_{1,2} = L_{a1} - L_{a2} \ge 20\ \text{dB}

    (ISO 10846-2:2008 Inequality (1), -3:2002 Inequality (2) with ``a2`` the
    acceleration of the blocking mass, -4:2003 Inequality (2), -5:2008
    Inequality (1)): a smaller difference means too little stiffness
    mismatch between the element and the foundation, or flanking transmission.
    For the indirect method the same 20 dB is the :math:`|T| \le 0.1` of
    :data:`TRANSMISSIBILITY_LIMIT`.

    :param frequencies: Frequencies, in hertz (narrow-band lines or band
        centres).
    :param input_acceleration_level_db: Input acceleration level
        :math:`L_{a1}`, in dB, one per frequency.
    :param output_acceleration_level_db: Output acceleration level
        :math:`L_{a2}`, in dB re the same reference, one per frequency;
        ``-inf`` for an output that does not move.
    :return: The :class:`LevelDifferenceCheck` (``condition="blocked_output"``).
    :raises ValueError: for frequencies that are not finite and positive, or
        level spectra that do not carry one level per frequency.
    :warns TransferStiffnessWarning: where :math:`\Delta L_{1,2} < 20` dB.
    """
    owner = "check_blocked_output"
    freq = _frequency_axis(frequencies, owner)
    first = _level_spectrum(
        input_acceleration_level_db, freq.shape, owner, "input_acceleration_level_db"
    )
    second = _level_spectrum(
        output_acceleration_level_db, freq.shape, owner, "output_acceleration_level_db"
    )
    if first.ndim != 1 or second.ndim != 1 or np.any(np.isneginf(first)):
        msg = (
            f"{owner}: both level spectra must be one-dimensional, and the "
            "input one finite."
        )
        raise ValueError(msg)
    check = LevelDifferenceCheck(
        frequencies=freq,
        difference_db=first - second,
        limit_db=_BLOCKED_OUTPUT_LIMIT_DB,
        condition="blocked_output",
    )
    _warn_level_difference(
        check,
        "Inequality (1) of ISO 10846-2 and -5 (Inequality (2) of -3 and -4)",
        "the output is not blocked there.",
    )
    return check


def check_unwanted_input(
    frequencies: ArrayLike,
    excitation_level_db: ArrayLike,
    unwanted_level_db: ArrayLike,
) -> LevelDifferenceCheck:
    r"""Does the input move in the excitation direction alone, by 15 dB?

    Every part of ISO 10846 is valid only where the input acceleration in the
    excitation direction exceeds that in the directions perpendicular to it
    by at least 15 dB:

    .. math::

       L_{a(\mathrm{excitation})} - L_{a(\mathrm{unwanted})} \ge 15\ \text{dB}

    (ISO 10846-2:2008 Inequality (3), -3:2002 Inequality (5), -4:2003
    Inequality (7), -5:2008 Inequality (2)), the unwanted accelerations read
    at the edge of the excitation mass or force distribution plate in the
    plane of the input flange. With several unwanted directions, the loudest
    one at each frequency decides. (ISO 10846-2:2008 7.6.1, which excludes
    the lines that fail this pre-run, prints the reference as "6.1,
    Inequality (1)", the blocked-output condition; the condition meant is
    6.4, Inequality (3), as the same sentence in Parts 3 to 5 shows. See the
    errata register.)

    :param frequencies: Frequencies, in hertz.
    :param excitation_level_db: Acceleration level in the excitation
        direction, in dB, one per frequency.
    :param unwanted_level_db: Acceleration level in a perpendicular
        direction, in dB re the same reference, one per frequency; or one row
        per direction, shape ``(directions, frequencies)``.
    :return: The :class:`LevelDifferenceCheck` (``condition="unwanted_input"``).
    :raises ValueError: for frequencies that are not finite and positive, or
        level spectra that do not carry one level per frequency.
    :warns TransferStiffnessWarning: where the difference is below 15 dB.
    """
    owner = "check_unwanted_input"
    freq = _frequency_axis(frequencies, owner)
    excitation = _level_spectrum(
        excitation_level_db, freq.shape, owner, "excitation_level_db"
    )
    unwanted = _level_spectrum(
        unwanted_level_db, freq.shape, owner, "unwanted_level_db"
    )
    if excitation.ndim != 1 or np.any(np.isneginf(excitation)):
        msg = f"{owner}: 'excitation_level_db' must be one finite level per frequency."
        raise ValueError(msg)
    loudest = unwanted if unwanted.ndim == 1 else np.max(unwanted, axis=0)
    check = LevelDifferenceCheck(
        frequencies=freq,
        difference_db=excitation - loudest,
        limit_db=_UNWANTED_INPUT_LIMIT_DB,
        condition="unwanted_input",
    )
    _warn_level_difference(
        check,
        "Inequality (2) of ISO 10846-5 (Inequality (3) of -2, (5) of -3, (7) of -4)",
        "the input moves in the unwanted directions too.",
    )
    return check


@dataclass(frozen=True)
class OutputMassCheck:
    r"""The mass in front of the output force transducers, against its limit.

    In the direct method the mass ``m0`` between the element and the output
    force transducers (the output flange, the force distribution plate and
    half the transducers) biases the measured force by its own inertia force
    :math:`m_0 a_2`. ISO 10846-4:2003 Inequality (3) bounds it, and so does
    ISO 10846-2:2008 Inequality (2) for resilient supports, where the mass is
    called ``m2`` and counts the force distribution plate and half the
    transducers only:

    .. math::

       m_0 \le 0{,}06 \times \frac{10^{L_{F2}/20}}{10^{L_{a2}/20}}\ \text{kg}

    with the levels re 1 µN and 1 µm/s² (ISO 10846-4 3.15 and 3.16), so the
    bound is :math:`0{,}06\,|F_2|/|a_2|`. Since
    :math:`F_\mathrm{b} = F_2 + m_0 a_2`, the force levels differ by at most
    :math:`-20 \lg(1 - r)` dB with :math:`r = m_0 |a_2| / |F_2|`, which at
    the bound (:math:`r = 0{,}06`) is 0,54 dB against the 0,51 dB of an
    inertia force in phase with the measured one: the "0,5 dB" of NOTE 1.

    :ivar frequencies: Frequencies judged, in hertz.
    :ivar output_mass_kg: The mass ``m0``, in kg.
    :ivar mass_limit_kg: The right-hand side of the inequality at each
        frequency, in kg.
    """

    frequencies: np.ndarray
    output_mass_kg: float
    mass_limit_kg: np.ndarray

    def __post_init__(self) -> None:
        """Reject a check whose fields disagree or hold impossible values.

        :raises ValueError: if the arrays differ in length or rank, a value
            is not finite, the mass is negative or a limit is not positive.
        """
        require_ranks(self, frequencies=1, mass_limit_kg=1)
        require_same_length(self, "frequencies", "mass_limit_kg", axis="frequency")
        require_finite_fields(self, "frequencies", "mass_limit_kg")
        require_finite(
            require_non_negative(self.output_mass_kg, "output_mass_kg"),
            "output_mass_kg",
        )
        if np.any(np.asarray(self.mass_limit_kg, dtype=np.float64) <= 0.0):
            msg = "OutputMassCheck: 'mass_limit_kg' must be positive."
            raise ValueError(msg)

    @property
    def holds(self) -> np.ndarray:
        """Per frequency, whether ``m0`` is within its limit.

        :return: One boolean per frequency.
        """
        return self.output_mass_kg <= np.asarray(self.mass_limit_kg, dtype=np.float64)

    @property
    def inertia_ratio(self) -> np.ndarray:
        r"""The inertia force over the measured force, :math:`r = m_0 |a_2| / |F_2|`.

        :return: One ratio per frequency; 0,06 where ``m0`` sits on its limit.
        """
        limit = np.asarray(self.mass_limit_kg, dtype=np.float64)
        return np.asarray(_OUTPUT_MASS_FACTOR * self.output_mass_kg / limit)

    @property
    def bias_bound_db(self) -> np.ndarray:
        r"""Largest :math:`|L_{F\mathrm{b}} - L_{F2}|` the mass can cause, in dB.

        :math:`-20 \lg(1 - r)`, reached when the inertia force opposes the
        measured force; ``inf`` where :math:`r \ge 1`, when the mass can
        cancel the force altogether.

        :return: One bound per frequency, in dB.
        """
        r = self.inertia_ratio
        out = np.full(r.shape, np.inf)
        below = r < 1.0
        out[below] = -20.0 * np.log10(1.0 - r[below])
        return out

    @property
    def passes(self) -> bool:
        """Whether ``m0`` is within its limit at every frequency judged.

        :return: ``True`` when the inequality holds throughout.
        """
        return bool(np.all(self.holds))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "an OutputMassCheck has no truth value; read its '.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the mass limit over frequency against the mass in place.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the mass-limit curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_output_mass_check

        return plot_output_mass_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_output_mass(
    frequencies: ArrayLike,
    output_mass_kg: float,
    output_force_level_db: ArrayLike,
    output_acceleration_level_db: ArrayLike,
) -> OutputMassCheck:
    r"""Is the mass in front of the output force transducers light enough?

    ISO 10846-4:2003 Inequality (3), and ISO 10846-2:2008 Inequality (2) for
    resilient supports:

    .. math::

       m_0 \le 0{,}06 \times \frac{10^{L_{F2}/20}}{10^{L_{a2}/20}}\ \text{kg}

    with :math:`L_{F2}` the force level re 1 µN and :math:`L_{a2}` the
    acceleration level re 1 µm/s² of the output side (ISO 10846-4 3.15 and
    3.16, the references of ISO 1683). If it fails, NOTE 2 says what to do: a
    lighter ``m0``, or stiffer (more, or larger) force transducers. See
    :class:`OutputMassCheck` for the bias it bounds.

    :param frequencies: Frequencies, in hertz.
    :param output_mass_kg: The mass ``m0`` between the element and the output
        force transducers: the output flange, the force distribution plate and
        half the mass of the transducers (ISO 10846-4), or the plate and half
        the transducers for a resilient support (ISO 10846-2), in kg.
    :param output_force_level_db: Measured output force level
        :math:`L_{F2}`, in dB re 1 µN, one per frequency.
    :param output_acceleration_level_db: Output acceleration level
        :math:`L_{a2}`, in dB re 1 µm/s², one per frequency.
    :return: The :class:`OutputMassCheck`.
    :raises ValueError: for frequencies that are not finite and positive, a
        negative mass, or level spectra that do not carry one finite level per
        frequency.
    :warns TransferStiffnessWarning: where ``m0`` exceeds its limit.
    """
    owner = "check_output_mass"
    output_mass_kg = require_finite(
        require_non_negative(output_mass_kg, "output_mass_kg"), "output_mass_kg"
    )
    freq = _frequency_axis(frequencies, owner)
    levels = []
    for name, value in (
        ("output_force_level_db", output_force_level_db),
        ("output_acceleration_level_db", output_acceleration_level_db),
    ):
        level = np.asarray(value, dtype=np.float64)
        if level.shape != freq.shape or not np.all(np.isfinite(level)):
            msg = f"{owner}: '{name}' must carry one finite level per frequency."
            raise ValueError(msg)
        levels.append(level)
    force_db, acceleration_db = levels
    limit = (
        _OUTPUT_MASS_FACTOR
        * (_FORCE_REFERENCE_N / _ACCELERATION_REFERENCE_M_S2)
        * 10.0 ** ((force_db - acceleration_db) / 20.0)
    )
    check = OutputMassCheck(
        frequencies=freq, output_mass_kg=output_mass_kg, mass_limit_kg=limit
    )
    if not check.passes:
        worst = int(np.argmin(limit))
        warnings.warn(
            f"m0 = {output_mass_kg:g} kg exceeds the limit of ISO 10846-4 "
            f"Inequality (3) (ISO 10846-2 Inequality (2)) at "
            f"{np.count_nonzero(~check.holds)} of {freq.size} frequencies, "
            f"down to {limit[worst]:.3g} kg at {freq[worst]:g} Hz: the measured "
            "force may miss the blocking force by more than 0.5 dB there; use a "
            "lighter m0 or stiffer force transducers (NOTE 2).",
            TransferStiffnessWarning,
            stacklevel=2,
        )
    return check


# ---------------------------------------------------------------------------
# Effective blocking mass: ISO 10846-4 Formula (6) = ISO 10846-3 Formula (4).
# ---------------------------------------------------------------------------


def _limit_crossing(
    frequencies: NDArray[np.float64],
    margin: NDArray[np.float64],
    failing: NDArray[np.bool_],
    judged: NDArray[np.bool_],
) -> tuple[int | None, float | None]:
    """The first judged line that fails, and where the margin crossed zero.

    ``margin`` is the distance to the limit, positive inside it; the crossing
    is interpolated linearly in the margin against the logarithm of frequency
    between the last judged line before the failure and the failing line
    itself. With no judged line before it, the failing line is the limit.

    :return: ``(index, frequency)`` of the first failure, or ``(None, None)``
        when no judged line fails.
    """
    candidates = np.flatnonzero(judged & failing)
    if candidates.size == 0:
        return None, None
    first = int(candidates[0])
    before = np.flatnonzero(judged[:first])
    if before.size == 0:
        return first, float(frequencies[first])
    last = int(before[-1])
    fraction = margin[last] / (margin[last] - margin[first])
    if fraction >= 1.0:
        # A margin of exactly zero on the failing line puts the limit on that
        # line; returning the line itself, not a power that rounds a unit in
        # the last place either side of it, lets a caller keep the line at
        # the limit by comparing frequencies.
        return first, float(frequencies[first])
    ratio = frequencies[first] / frequencies[last]
    return first, float(frequencies[last] * ratio**fraction)


@dataclass(frozen=True)
class EffectiveBlockingMass:
    r"""Effective mass of a blocking mass over frequency, and its limit ``f3``.

    The indirect method treats the blocking mass as rigid; above some
    frequency it no longer is, and the force it measures departs from
    :math:`m_2 a_2`. Driven alone on soft supports through its centre of mass,
    with two accelerometers a spacing :math:`\sqrt{S}` apart inside the contact
    area ``S``, its effective mass is (ISO 10846-4:2003 Formula (6); the same
    quantity is ISO 10846-3:2002 Formula (4))

    .. math::

       m_{2,\mathrm{eff}} = \left| \frac{2 F_2}{a'_1 + a''_1} \right|

    and the results of the indirect method are presented only up to ``f3``,
    "the lowest frequency at which the effective mass deviates more than 12 %
    (i.e. 1 dB in level) from the mass m2", where
    :math:`|\Delta L| = |20 \lg(m_{2,\mathrm{eff}}/m_2)| \le 1` dB
    (ISO 10846-4 Inequality (5), ISO 10846-3 Inequality (3)). A deviation
    below 40 Hz is the mass-spring behaviour of the block on its supports and
    is ignored in finding ``f3``.

    :ivar frequencies: Frequencies, in hertz, strictly increasing.
    :ivar effective_mass_kg: :math:`m_{2,\mathrm{eff}}` at each frequency,
        in kg.
    :ivar blocking_mass_kg: The mass ``m2`` of the block, in kg.
    """

    frequencies: np.ndarray
    effective_mass_kg: np.ndarray
    blocking_mass_kg: float

    def __post_init__(self) -> None:
        """Reject fields that disagree, masses that are not positive, or an unsorted sweep.

        :raises ValueError: if the arrays differ in length or rank, a value is
            not finite, a mass is not positive, or the frequencies do not rise
            strictly.
        """
        owner = type(self).__name__
        require_ranks(self, frequencies=1, effective_mass_kg=1)
        require_same_length(self, "frequencies", "effective_mass_kg", axis="frequency")
        require_finite_fields(self, "frequencies", "effective_mass_kg")
        require_finite(
            require_positive(self.blocking_mass_kg, "blocking_mass_kg"),
            "blocking_mass_kg",
        )
        if np.any(np.asarray(self.effective_mass_kg, dtype=np.float64) <= 0.0):
            msg = f"{owner}: 'effective_mass_kg' must be positive."
            raise ValueError(msg)
        freq = _frequency_axis(self.frequencies, owner)
        _require_increasing(freq, owner)

    @property
    def deviation_db(self) -> np.ndarray:
        r""":math:`\Delta L = 20 \lg(m_{2,\mathrm{eff}}/m_2)`, in dB.

        :return: One deviation per frequency.
        """
        m_eff = np.asarray(self.effective_mass_kg, dtype=np.float64)
        return np.asarray(20.0 * np.log10(m_eff / self.blocking_mass_kg))

    @property
    def ignored_below_hz(self) -> float:
        """The 40 Hz below which a deviation is not read as a loss of rigidity, in hertz.

        :return: 40.0 (ISO 10846-3 6.2.3, ISO 10846-4 6.3.3.2).
        """
        return _EFFECTIVE_MASS_IGNORED_BELOW_HZ

    def _first_failure(self) -> tuple[int | None, float | None]:
        """The first line from 40 Hz up outside 1 dB, and the interpolated ``f3``."""
        freq = np.asarray(self.frequencies, dtype=np.float64)
        margin = _EFFECTIVE_MASS_TOLERANCE_DB - np.abs(self.deviation_db)
        judged = freq >= _EFFECTIVE_MASS_IGNORED_BELOW_HZ
        return _limit_crossing(freq, margin, margin < 0.0, judged)

    @property
    def upper_frequency_limit_hz(self) -> float | None:
        """``f3``, in hertz, or ``None`` when the mass stays rigid over the sweep.

        The deviation crosses 1 dB between the last line inside it and the
        first line (from 40 Hz up) outside it; the crossing is interpolated in
        the logarithm of frequency.

        :return: ``f3``, or ``None``.
        """
        return self._first_failure()[1]

    @property
    def valid(self) -> np.ndarray:
        """Per frequency, whether it lies below the first line outside 1 dB.

        :return: One boolean per frequency.
        """
        freq = np.asarray(self.frequencies, dtype=np.float64)
        first, _ = self._first_failure()
        if first is None:
            return np.ones(freq.shape, dtype=bool)
        return np.asarray(freq < freq[first])

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the deviation from ``m2`` with the 1 dB tolerance and ``f3``.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the deviation curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_effective_blocking_mass

        return plot_effective_blocking_mass(
            self, ax=ax, language=check_language(language), **kwargs
        )


def effective_blocking_mass(
    frequencies: ArrayLike,
    force_n: ArrayLike,
    first_acceleration_m_s2: ArrayLike,
    second_acceleration_m_s2: ArrayLike,
    *,
    blocking_mass_kg: float,
) -> EffectiveBlockingMass:
    r"""Effective mass of a blocking mass from one force and two accelerations.

    ISO 10846-4:2003 Formula (6) (ISO 10846-3:2002 Formula (4)):
    :math:`m_{2,\mathrm{eff}} = |2 F_2 / (a'_1 + a''_1)|`, with the block
    supported on soft springs (a mass-spring resonance below 10 Hz), the
    force ``F2`` applied along the axis through its centre of mass, and the
    two accelerometers placed symmetrically inside the contact area ``S`` a
    distance :math:`\sqrt{S}` apart; the force and acceleration measurements
    follow ISO 7626-1 and ISO 7626-2. See :class:`EffectiveBlockingMass` for
    ``f3``.

    :param frequencies: Frequencies, in hertz, strictly increasing.
    :param force_n: Excitation force phasor ``F2``, in N, one per frequency.
    :param first_acceleration_m_s2: Acceleration phasor :math:`a'_1`, in
        m/s², one per frequency.
    :param second_acceleration_m_s2: Acceleration phasor :math:`a''_1`, in
        m/s², one per frequency.
    :param blocking_mass_kg: The mass ``m2`` of the block, in kg.
    :return: The :class:`EffectiveBlockingMass`.
    :raises ValueError: for frequencies that are not finite, positive and
        strictly increasing, phasors of another length, a zero or non-finite
        effective mass, or a non-positive ``m2``.
    """
    owner = "effective_blocking_mass"
    blocking_mass_kg = require_positive(blocking_mass_kg, "blocking_mass_kg")
    freq = _frequency_axis(frequencies, owner)
    _require_increasing(freq, owner)
    force = np.asarray(force_n, dtype=np.complex128)
    first = np.asarray(first_acceleration_m_s2, dtype=np.complex128)
    second = np.asarray(second_acceleration_m_s2, dtype=np.complex128)
    if (
        force.shape != freq.shape
        or first.shape != freq.shape
        or second.shape != freq.shape
    ):
        msg = (
            f"{owner}: the force and both accelerations must carry one phasor "
            "per frequency."
        )
        raise ValueError(msg)
    summed = first + second
    if not np.all(np.abs(summed) > 0.0):
        msg = (
            f"{owner}: the two accelerations sum to zero at some frequency; "
            "m2,eff is undefined there."
        )
        raise ValueError(msg)
    m_eff = np.abs(2.0 * force / summed)
    if not np.all(np.isfinite(m_eff)) or not np.all(m_eff > 0.0):
        msg = f"{owner}: the effective mass must be finite and positive at every frequency."
        raise ValueError(msg)
    return EffectiveBlockingMass(
        frequencies=freq,
        effective_mass_kg=np.asarray(m_eff, dtype=np.float64),
        blocking_mass_kg=blocking_mass_kg,
    )


# ---------------------------------------------------------------------------
# Driving-point method: ISO 10846-5.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DrivingPointStiffnessResult:
    r"""A dynamic driving-point stiffness and the transfer stiffness it stands for (ISO 10846-5).

    With the output of the element blocked, the input force and acceleration
    give the driving-point stiffness (ISO 10846-5:2008 Formula (3))

    .. math::

       k_{1,1}(f) = \frac{F_1}{u_1} = -(2\pi f)^2 \frac{F_1}{a_1}

    which equals the transfer stiffness :math:`k_{2,1}` at low frequencies
    only. Clause 6.2 finds where that ends: the upper limiting frequency
    :math:`f_\mathrm{UL}` is "the lowest frequency, at which the driving point
    stiffness level becomes 2 dB smaller than the low-frequency stiffness",
    the low-frequency value being "the average for 1 Hz to 20 Hz". Below it
    the band averages of :math:`k_{1,1}` stand for those of :math:`k_{2,1}`,
    :math:`k_\mathrm{av} = k_{\mathrm{av}(2,1)} \approx k_{\mathrm{av}(1,1)}`,
    within 2 dB (Formula (7)).

    The low-frequency value is taken as the Formula (6) average of the lines
    from 1 Hz to 20 Hz, the one average the part defines for a stiffness; for
    the flat stiffness the clause presumes, it and the mean of the levels
    agree. The crossing of the 2 dB threshold is interpolated in the logarithm
    of frequency between the last line above it and the first line on or
    below it, and every line above :math:`f_\mathrm{UL}` is excluded; a line
    exactly on the threshold is :math:`f_\mathrm{UL}` itself and stays in,
    since 8.3 states the 2 dB for :math:`f \le f_\mathrm{UL}`. Lines that
    fail Inequality (1) or (2) (:attr:`adequate`) are excluded from the
    evaluation altogether, as 7.6.1 requires, and so are lines below the
    1 Hz at which the method starts.

    :ivar frequencies: Frequencies, in hertz, strictly increasing.
    :ivar driving_point_stiffness: Complex :math:`k_{1,1}` at each frequency,
        in N/m.
    :ivar adequate: Per frequency, whether Inequalities (1) and (2) hold, or
        ``None`` when they were not checked.
    """

    frequencies: np.ndarray
    driving_point_stiffness: np.ndarray
    adequate: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Reject a sweep that cannot give a low-frequency value or an ordered limit.

        :raises ValueError: if the fields disagree in length or rank, a value
            is not finite, a stiffness is zero, the frequencies do not rise
            strictly, ``adequate`` is not boolean, or no adequate line lies
            between 1 Hz and 20 Hz.
        """
        owner = type(self).__name__
        require_ranks(self, frequencies=1, driving_point_stiffness=1, adequate=1)
        require_same_length(
            self,
            "frequencies",
            "driving_point_stiffness",
            "adequate",
            axis="frequency",
        )
        require_finite_fields(self, "frequencies", "driving_point_stiffness")
        freq = _frequency_axis(self.frequencies, owner)
        _require_increasing(freq, owner)
        if not np.all(np.abs(np.asarray(self.driving_point_stiffness)) > 0.0):
            msg = f"{owner}: 'driving_point_stiffness' must be non-zero."
            raise ValueError(msg)
        if self.adequate is not None:
            _as_flags(self.adequate, freq.shape, owner, "adequate")
        if not np.any(self._low_frequency_lines()):
            low, high = _LOW_FREQUENCY_RANGE_HZ
            msg = (
                f"{owner}: no adequate line lies between {low:g} Hz and "
                f"{high:g} Hz, so ISO 10846-5 6.2 has no low-frequency value "
                "to find f_UL from."
            )
            raise ValueError(msg)

    def _adequate(self) -> NDArray[np.bool_]:
        """The adequacy flags, every line adequate when none were given."""
        freq = np.asarray(self.frequencies, dtype=np.float64)
        if self.adequate is None:
            return np.ones(freq.shape, dtype=bool)
        return np.asarray(self.adequate, dtype=bool)

    def _low_frequency_lines(self) -> NDArray[np.bool_]:
        """The adequate lines from 1 Hz to 20 Hz, both included."""
        freq = np.asarray(self.frequencies, dtype=np.float64)
        low, high = _LOW_FREQUENCY_RANGE_HZ
        return np.asarray(self._adequate() & (freq >= low) & (freq <= high))

    @property
    def magnitude(self) -> np.ndarray:
        r"""Driving-point stiffness magnitude :math:`|k_{1,1}|`, in N/m."""
        return np.asarray(np.abs(self.driving_point_stiffness), dtype=np.float64)

    @property
    def levels(self) -> np.ndarray:
        """Driving-point stiffness level re 1 N/m at each frequency, in dB."""
        return transfer_stiffness_level(self.driving_point_stiffness)

    @property
    def loss_factor(self) -> np.ndarray:
        r"""Loss factor :math:`\eta = \operatorname{Im}(k_{1,1})/\operatorname{Re}(k_{1,1})` (Formula (4))."""
        return loss_factor(self.driving_point_stiffness)

    @property
    def low_frequency_level_db(self) -> float:
        r"""The low-frequency stiffness level of 6.2, in dB re 1 N/m.

        :return: :math:`10 \lg` of the mean squared magnitude over the
            adequate lines from 1 Hz to 20 Hz, re :math:`k_0^2`.
        """
        lines = self._low_frequency_lines()
        power = float(np.mean(self.magnitude[lines] ** 2))
        return 10.0 * math.log10(power / REFERENCE_STIFFNESS**2)

    @property
    def threshold_level_db(self) -> float:
        r"""The level 2 dB below the low-frequency value, whose crossing is :math:`f_\mathrm{UL}`.

        :return: The threshold, in dB re 1 N/m.
        """
        return self.low_frequency_level_db - _DRIVING_POINT_TOLERANCE_DB

    def _first_failure(self) -> tuple[int | None, float | None]:
        """The first adequate line 2 dB down, and the interpolated ``f_UL``."""
        freq = np.asarray(self.frequencies, dtype=np.float64)
        margin = self.levels - self.threshold_level_db
        judged = self._adequate() & (freq >= _LOW_FREQUENCY_RANGE_HZ[0])
        return _limit_crossing(freq, margin, margin <= 0.0, judged)

    @property
    def upper_limiting_frequency_hz(self) -> float | None:
        r""":math:`f_\mathrm{UL}` of 6.2, in hertz, or ``None`` when the sweep never reaches it.

        :return: :math:`f_\mathrm{UL}`, or ``None``.
        """
        return self._first_failure()[1]

    @property
    def valid(self) -> np.ndarray:
        r"""Per frequency, whether the line is evaluated.

        A line is evaluated when it is adequate, lies at or above 1 Hz and
        lies at or below :math:`f_\mathrm{UL}`: 8.3 states the accuracy of
        Formula (7) "if :math:`f \le f_\mathrm{UL}`", so a line that sits
        exactly on the 2 dB threshold, and is :math:`f_\mathrm{UL}` itself,
        is kept.

        :return: One boolean per frequency.
        """
        freq = np.asarray(self.frequencies, dtype=np.float64)
        keep = self._adequate() & (freq >= _LOW_FREQUENCY_RANGE_HZ[0])
        f_ul = self._first_failure()[1]
        if f_ul is not None:
            keep &= freq <= f_ul
        return np.asarray(keep)

    def band_average(self) -> BandAveragedStiffness:
        r"""One-third-octave-band averages of :math:`k_{1,1}` over the valid lines (Formulas (6), (7)).

        Only the lines at or below :math:`f_\mathrm{UL}` are averaged. For
        those bands 8.3 states that the band averages of :math:`k_{1,1}`
        stand for those of :math:`k_{2,1}` within 2 dB, and Annex B (B.3.5)
        assumes the same :math:`\pm 2` dB for its uncertainty budget; the
        criterion of 6.2 itself only watches :math:`k_{1,1}` fall below its
        own low-frequency value, so the 2 dB is the standard's statement,
        not something the average can prove line by line.

        Up to 20 Hz the 0,2 Hz line spacing of 7.5 leaves the lowest bands
        with fewer than five lines; the NOTE to clause 9 m) accepts
        narrow-band data there, so those bands are left undetermined without
        a warning.

        :return: The :class:`BandAveragedStiffness`.
        :warns TransferStiffnessWarning: when a band above 20 Hz holds fewer
            than :data:`MIN_FREQUENCIES_PER_BAND` valid lines.
        """
        return _band_average(
            self.frequencies,
            self.driving_point_stiffness,
            self.valid,
            owner="DrivingPointStiffnessResult.band_average",
            quiet_up_to_hz=_LOW_FREQUENCY_RANGE_HZ[1],
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the driving-point stiffness level with the 6.2 threshold and :math:`f_\mathrm{UL}`.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the level curve.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_driving_point_stiffness

        return plot_driving_point_stiffness(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _acceleration_level(
    value: ArrayLike, shape: tuple[int, ...], owner: str, name: str
) -> NDArray[np.float64]:
    """Level re 1 µm/s² of acceleration phasors, ``-inf`` where they are zero."""
    acceleration = np.abs(np.asarray(value, dtype=np.complex128))
    if (
        acceleration.ndim not in (1, 2)
        or acceleration.shape[-1:] != shape
        or not np.all(np.isfinite(acceleration))
    ):
        msg = f"{owner}: '{name}' must carry one finite phasor per frequency."
        raise ValueError(msg)
    with np.errstate(divide="ignore"):
        return np.asarray(20.0 * np.log10(acceleration / _ACCELERATION_REFERENCE_M_S2))


def driving_point_stiffness(
    frequencies: ArrayLike,
    input_force_n: ArrayLike,
    input_acceleration_m_s2: ArrayLike,
    *,
    output_acceleration_m_s2: ArrayLike | None = None,
    unwanted_acceleration_m_s2: ArrayLike | None = None,
) -> DrivingPointStiffnessResult:
    r"""Dynamic driving-point stiffness of a resilient support (ISO 10846-5 Formula (3)).

    :math:`k_{1,1}(f) = -(2\pi f)^2 F_1 / a_1`, from the input force and the
    input acceleration measured with the output side of the element blocked.
    With the output acceleration given, Inequality (1),
    :math:`\Delta L_{1,2} \ge 20` dB, is checked line by line
    (:func:`check_blocked_output`); with the unwanted accelerations given,
    Inequality (2), 15 dB (:func:`check_unwanted_input`). A line that fails
    either raises a :class:`TransferStiffnessWarning` and is excluded from the
    evaluation. The result finds :math:`f_\mathrm{UL}` (6.2) and averages the
    valid lines into bands (Formulas (6), (7)).

    :param frequencies: Frequencies, in hertz, strictly increasing; the sweep
        needs lines between 1 Hz and 20 Hz for the low-frequency value, and
        7.5 asks for a 0,2 Hz spacing there.
    :param input_force_n: Input force phasor ``F1``, in N.
    :param input_acceleration_m_s2: Input acceleration phasor ``a1``, in m/s²,
        non-zero.
    :param output_acceleration_m_s2: Output-flange acceleration phasor ``a2``,
        in m/s² (Default: ``None``, Inequality (1) not checked).
    :param unwanted_acceleration_m_s2: Input acceleration phasor in a
        direction perpendicular to the excitation, in m/s², or one row per
        direction (Default: ``None``, Inequality (2) not checked).
    :return: The :class:`DrivingPointStiffnessResult`.
    :raises ValueError: for frequencies that are not finite, positive and
        strictly increasing, phasors that do not carry one value per
        frequency, a zero input acceleration, or no adequate line from 1 Hz to
        20 Hz.
    :warns TransferStiffnessWarning: where Inequality (1) or (2) fails.
    """
    owner = "driving_point_stiffness"
    freq = _frequency_axis(frequencies, owner)
    _require_increasing(freq, owner)
    force = np.asarray(input_force_n, dtype=np.complex128)
    a1 = np.asarray(input_acceleration_m_s2, dtype=np.complex128)
    if force.shape != freq.shape or a1.shape != freq.shape:
        msg = (
            f"{owner}: the input force and acceleration must carry one phasor "
            "per frequency."
        )
        raise ValueError(msg)
    if not np.all(np.abs(a1) > 0.0):
        msg = (
            f"{owner}: 'input_acceleration_m_s2' contains zeros; "
            "k1,1 = -(2 pi f)^2 F1/a1 is undefined there."
        )
        raise ValueError(msg)
    k11 = -((2.0 * np.pi * freq) ** 2) * force / a1
    adequate: NDArray[np.bool_] | None = None
    input_level = _acceleration_level(a1, freq.shape, owner, "input_acceleration_m_s2")
    if output_acceleration_m_s2 is not None:
        output_level = _acceleration_level(
            output_acceleration_m_s2, freq.shape, owner, "output_acceleration_m_s2"
        )
        if output_level.ndim != 1:
            msg = (
                f"{owner}: 'output_acceleration_m_s2' must be one phasor per frequency."
            )
            raise ValueError(msg)
        adequate = np.asarray(
            check_blocked_output(freq, input_level, output_level).holds, dtype=bool
        )
    if unwanted_acceleration_m_s2 is not None:
        unwanted_level = _acceleration_level(
            unwanted_acceleration_m_s2, freq.shape, owner, "unwanted_acceleration_m_s2"
        )
        holds = np.asarray(
            check_unwanted_input(freq, input_level, unwanted_level).holds, dtype=bool
        )
        adequate = holds if adequate is None else adequate & holds
    return DrivingPointStiffnessResult(
        frequencies=freq,
        driving_point_stiffness=np.asarray(k11, dtype=np.complex128),
        adequate=adequate,
    )


# ---------------------------------------------------------------------------
# Measurement uncertainty: ISO 10846-5 Annex B.
# ---------------------------------------------------------------------------

#: The input quantities of ISO 10846-5 Formula (B.1), as the budget labels them.
_ANNEX_B_NAMES = (
    r"$\hat{L}_{k,\mathrm{av}}$",
    r"$\delta_\mathrm{ins}$",
    r"$\delta_\mathrm{rep}$",
    r"$\delta_\mathrm{rig}$",
    r"$\delta_\mathrm{dps}$",
    r"$\delta_\mathrm{lin}$",
)


@dataclass(frozen=True)
class DrivingPointUncertainty:
    r"""Uncertainty budget of a band level measured by the driving-point method (ISO 10846-5 Annex B).

    The band level is modelled as the measured one plus five corrections of
    zero estimate (Formula (B.1)),

    .. math::

       L_{k,\mathrm{av}} = \hat{L}_{k,\mathrm{av}} + \delta_\mathrm{ins}
       + \delta_\mathrm{rep} + \delta_\mathrm{rig} + \delta_\mathrm{dps}
       + \delta_\mathrm{lin}

    every sensitivity coefficient is 1, the combined standard uncertainty is
    the root sum of squares of the six contributions (Formula (B.2)) and the
    expanded uncertainty for 95 % coverage is :math:`U = 2u` (Formula (B.3)),
    the six inputs being "assumed to result in a normal distribution".

    :ivar budget: The GUM budget, one row per input quantity of Table B.1.
    """

    budget: UncertaintyResult

    def __post_init__(self) -> None:
        """Reject a budget that is not the six rows of Table B.1.

        :raises ValueError: if the budget does not hold six input quantities.
        """
        if np.asarray(self.budget.contributions).size != len(_ANNEX_B_NAMES):
            msg = (
                "DrivingPointUncertainty: 'budget' must hold the six input "
                "quantities of ISO 10846-5 Table B.1."
            )
            raise ValueError(msg)

    @property
    def band_level_db(self) -> float:
        r"""The band level :math:`L_{k,\mathrm{av}}`, in dB re 1 N/m."""
        return float(self.budget.value)

    @property
    def combined_uncertainty_db(self) -> float:
        r"""Combined standard uncertainty :math:`u(L_{k,\mathrm{av}})`, in dB (Formula (B.2))."""
        return float(self.budget.combined_uncertainty)

    @property
    def coverage_factor(self) -> float:
        """The coverage factor 2 of Formula (B.3)."""
        return _ANNEX_B_COVERAGE_FACTOR

    @property
    def expanded_uncertainty_db(self) -> float:
        """Expanded uncertainty :math:`U = 2u`, in dB (Formula (B.3))."""
        return self.coverage_factor * self.combined_uncertainty_db

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the contribution of each input quantity, with ``u`` and ``U``.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the contribution bars.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.vibration import plot_driving_point_uncertainty

        return plot_driving_point_uncertainty(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _sum_of_inputs(*inputs: float) -> float:
    """Formula (B.1): the band level is the sum of its six input quantities."""
    return float(sum(inputs))


def driving_point_uncertainty(
    band_level_db: float,
    *,
    repeatability_range_db: float,
    signal_uncertainty_db: float = _U_SIGNAL_DB,
    instrumentation_uncertainty_db: float = _U_INSTRUMENTATION_DB,
    test_rig_uncertainty_db: float = _U_TEST_RIG_DB,
    discrepancy_uncertainty_db: float = _U_DISCREPANCY_DB,
    linearity_uncertainty_db: float = _U_LINEARITY_DB,
) -> DrivingPointUncertainty:
    r"""Uncertainty of a band level measured by the driving-point method (ISO 10846-5 Annex B).

    Table B.1, built on :func:`phonometry.metrology.combine_uncertainty`:

    - :math:`\hat{L}_{k,\mathrm{av}}`, signal processing and background
      noise, normal, 0,3 dB (B.3.1);
    - :math:`\delta_\mathrm{ins}`, instrumentation, normal, 0,5 dB when only
      the minimum requirements are met, 0,3 dB "with good choices and
      precautions" (B.3.2);
    - :math:`\delta_\mathrm{rep}`, installation repeatability, rectangular,
      :math:`p/\sqrt{3}` for a spread of :math:`2p` between the highest and
      lowest level of repeated installations (B.3.3);
    - :math:`\delta_\mathrm{rig}`, the test rig, rectangular,
      :math:`1/(2\sqrt{3})` dB (B.3.4);
    - :math:`\delta_\mathrm{dps}`, the driving-point stiffness standing for
      the transfer stiffness, rectangular over :math:`\pm 2` dB,
      :math:`2/\sqrt{3}` dB (B.3.5);
    - :math:`\delta_\mathrm{lin}`, linearity, rectangular,
      :math:`1{,}5/(2\sqrt{3})` dB (B.3.6).

    The last three are the expressions B.3.4 to B.3.6 print, 0,289, 1,155
    and 0,433 dB. Table B.1 carries them rounded up to one decimal, 0,3, 1,2
    and 0,5 dB, the conservative rounding an uncertainty may take
    (ISO/IEC Guide 98-3:2008, 7.2.6); the defaults keep the expressions.
    With the defaults and no repeatability spread, :math:`u = 1{,}394` dB and
    :math:`U = 2{,}789` dB, against 1,456 dB and 2,91 dB with the rounded
    table. Every default can be replaced by a reasoned estimate, as the annex
    encourages, and the note to (B.3) allows doing so band by band.

    :param band_level_db: The measured band level
        :math:`\hat{L}_{k,\mathrm{av}}`, in dB re 1 N/m.
    :param repeatability_range_db: The difference :math:`2p` between the
        highest and lowest band level of repeated installations, in dB
        (0 for none observed).
    :param signal_uncertainty_db: Standard uncertainty of
        :math:`\hat{L}_{k,\mathrm{av}}`, in dB (Default: 0,3).
    :param instrumentation_uncertainty_db: Standard uncertainty
        :math:`u_\mathrm{ins}`, in dB (Default: 0,5).
    :param test_rig_uncertainty_db: Standard uncertainty
        :math:`u_\mathrm{rig}`, in dB (Default: :math:`1/(2\sqrt{3})`).
    :param discrepancy_uncertainty_db: Standard uncertainty
        :math:`u_\mathrm{dps}`, in dB (Default: :math:`2/\sqrt{3}`).
    :param linearity_uncertainty_db: Standard uncertainty
        :math:`u_\mathrm{lin}`, in dB (Default: :math:`1{,}5/(2\sqrt{3})`).
    :return: The :class:`DrivingPointUncertainty`.
    :raises ValueError: for a non-finite band level, or a negative or
        non-finite spread or standard uncertainty.
    """
    band_level_db = require_finite(band_level_db, "band_level_db")
    spread = require_finite(
        require_non_negative(repeatability_range_db, "repeatability_range_db"),
        "repeatability_range_db",
    )
    standard = {
        "signal_uncertainty_db": signal_uncertainty_db,
        "instrumentation_uncertainty_db": instrumentation_uncertainty_db,
        "test_rig_uncertainty_db": test_rig_uncertainty_db,
        "discrepancy_uncertainty_db": discrepancy_uncertainty_db,
        "linearity_uncertainty_db": linearity_uncertainty_db,
    }
    u = {
        name: require_finite(require_non_negative(value, name), name)
        for name, value in standard.items()
    }
    quantities = (
        Quantity(
            band_level_db,
            u["signal_uncertainty_db"],
            "gaussian",
            name=_ANNEX_B_NAMES[0],
        ),
        Quantity(
            0.0, u["instrumentation_uncertainty_db"], "gaussian", name=_ANNEX_B_NAMES[1]
        ),
        Quantity(
            0.0, 0.5 * spread / math.sqrt(3.0), "rectangular", name=_ANNEX_B_NAMES[2]
        ),
        Quantity(
            0.0, u["test_rig_uncertainty_db"], "rectangular", name=_ANNEX_B_NAMES[3]
        ),
        Quantity(
            0.0, u["discrepancy_uncertainty_db"], "rectangular", name=_ANNEX_B_NAMES[4]
        ),
        Quantity(
            0.0, u["linearity_uncertainty_db"], "rectangular", name=_ANNEX_B_NAMES[5]
        ),
    )
    budget = combine_uncertainty(_sum_of_inputs, quantities)
    return DrivingPointUncertainty(budget=budget)

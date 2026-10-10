#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Components of an audio-frequency induction-loop system: the loop, its amplifier, the neck loop.

IEC 62489-1:2010, with its Amendment 1:2014 (read in the consolidated BS EN
62489-1:2010+A1:2015), says how the manufacturer of an induction-loop
amplifier, of a loop and of a neck loop measures and states what the
component does. IEC 60118-4:2014 then judges the installed system built from
them (:mod:`phonometry.electroacoustics.induction_loop`). This module holds
the parts of IEC 62489-1 that are arithmetic, and the loop formulas both
standards lean on.

The loop and its field
----------------------

A current :math:`I` in a loop of :math:`N` turns produces a magnetic field
strength :math:`H`, in amperes per metre, that is proportional to
:math:`N I` everywhere and falls with distance from the conductor. IEC
60118-4:2014 E.1 gives the one closed form it uses, the field at the centre
of a single-turn square loop of side :math:`d`, in its own plane,

.. math::

   H = \frac{2\sqrt{2}\,I}{\pi d},

and extends it to a rectangle of sides :math:`d_1` and :math:`d_2`:
"Provided that the sides d1, d2 of a rectangular loop are not extremely
different", :math:`d` is taken as :math:`\sqrt{d_1 d_2}`
(:func:`loop_centre_field`). Everything else about the field is a figure in
that standard. Here it is computed: :func:`rectangular_loop_field` sums the
Biot-Savart field of the four straight sides exactly, at any point, which is
how the E.1 formula is checked (it is exact for the square and off by 0,35 dB
for a rectangle of aspect ratio 1,5). Two of the figures are reproduced: the
curves of Figure E.2 b), both components within about half a decibel, taken
across the 10-unit width of its 15 by 10 loop, as E.1 describes them (the
figure's panel a) puts the vertical-field line along the length, see
``docs/ERRATA.md``), and the currents of Figure H.1 through
:func:`loop_current`. Figures E.3 to E.5 and A.1 draw the same kind of
pattern and are not checked point by point.

IEC 62489-1:2010 5.4.10.2 fixes where an amplifier's field is measured: 1,4 m
above the centre of a horizontal square loop whose resistance and inductance
equal the rated load. :func:`loop_current` gives the current that loop needs
for a field strength, and :func:`loop_dimensions` answers 5.4.11 the other way
round, the largest square loop, or loop of aspect ratio 3:1, whose centre
reaches 400 mA/m at that height with the amplifier's current.

The loop as a load
------------------

The loop is a resistance in series with an inductance (IEC 62489-1 B.2).
The resistance is :math:`R = \rho l / a` for a conductor of length :math:`l`
and area :math:`a` (:func:`loop_resistance`), with the resistivity of standard
annealed copper, 1/58 ohm square millimetre per metre at 20 degrees Celsius
and a temperature coefficient of 0,00393 per degree (IEC 60028:1925, clause I).
The inductance of a rectangle of round wire is Grover's Formula (58)
(:func:`rectangular_loop_inductance`); for :math:`N` turns it is multiplied by
:math:`N^2`, the perfect coupling Table B.1 assumes. The impedance
:math:`|Z| = \sqrt{R^2 + (2\pi f L)^2}` rises above the frequency where the
reactance equals the resistance, where it is :math:`\sqrt{2}` times the
resistance (IEC 60118-4 E.3), and the voltage the amplifier has to deliver is
:math:`U = I |Z|` (:class:`LoopImpedance`).

Table B.1 of IEC 62489-1 is the oracle. Its six resistances are reproduced by
the 20 degree resistivity with the perimeter of each loop, which for the
0,35 m by 0,45 m counter loop is 1,6 m and not the printed 1,5 m (see
``docs/ERRATA.md``). Grover's formula reproduces four of its six inductances
to the printed microhenry once the term for the flux inside the wire is left
out: 189, 22, 47 and 109 microhenries. Table B.1 does not say which formula it
used, and the two it does not reproduce, the neck loop (79 against 85) and the
15 m by 40 m loop (206 against 218), are not reached by any reading of the
wire size either, so they are not claimed. The internal term is kept by
default here, because at audio frequencies the skin depth in copper (2 mm at
1 kHz) is larger than the radius of every conductor Table B.1 lists.

The amplifier
-------------

IEC 62489-1 clause 5 lists what an amplifier's specification states, and
which of it is measured. The measured characteristics that are computations
are:

* the maximum (distortion-limited) output current, 5.4.7: the 1 kHz load
  current is raised until the total harmonic distortion across the resistive
  part of the load reaches the rated value, and the current is the total
  voltage across that resistance over its value
  (:func:`maximum_output_current`);
* the compliance voltage, 5.4.8: the maximum positive-going and negative-going
  peak voltages across the rated load, over at least 60 s of the specified
  pink noise, averaged and divided by :math:`\sqrt{2}`
  (:func:`compliance_voltage`);
* the noise, 5.4.9: the equivalent input noise voltage
  :math:`U_\mathrm{n} = U I_\mathrm{n} / I` and the signal-to-noise ratio
  :math:`S = 10\lg(I_\mathrm{r}^2 / I_\mathrm{n}^2)` dB
  (:func:`equivalent_input_noise_voltage`,
  :func:`amplifier_signal_to_noise_ratio`);
* the frequency response, 5.4.12: the load current at one-third-octave
  centres from at least 50 Hz to 8 kHz, with the response at 1 kHz taken as
  0 dB (:func:`amplifier_frequency_response`);
* the automatic gain control, 5.4.13: the steady-state output current against
  the source e.m.f., and the recommendation Amendment 1 added as 5.4.13.4, an
  input range of at least 32 dB for an output change of at most 3 dB
  (:func:`agc_characteristic`);
* the phase error of the quadrature network of a phased loop array, 5.4.14:
  the maximum deviation from 90 degrees between the loop currents over 100 Hz
  to 5 kHz (:func:`quadrature_phase_error`).

The rated conditions (5.4.1 to 5.4.6) are what the manufacturer states and are
not measured; the standard measuring conditions of 5.2.2 put the output
current 10 dB below the rated one. The test signal of 5.4.8.2 b) is the pink
noise of IEC 60118-4 6.4, generated by
:func:`~phonometry.electroacoustics.induction_loop.loop_test_noise`.

The neck loop
-------------

Clause 9, added by Amendment 1, specifies a neck loop by the input voltage
that produces 400 mA/m at the telecoil position of the test jig of Annex E,
the smallest magnitude of its input impedance over 100 Hz to 5 kHz rounded to
the nearest ohm, and its frequency response, stated in text as the
frequencies where it differs from the response at 1 kHz by 3 dB
(:func:`neck_loop_characteristics`). The draft Amendment 2 (prEN
62489-1:2010/prA2:2017, read in E DIN EN 62489-1/A2:2017-10) replaces Annex D
with two example specifications: type 1, for audio sources powered by two
primary 1,5 V cells and higher voltage supplies, by a DC resistance of 32 ohm
plus or minus 5 %, and type 2, a neck loop with a transformer or an amplifier,
by an input DC resistance of at least 32 ohm, both reaching 400 mA/m on the
jig with at most 1,06 V at the input (:data:`NECK_LOOP_TYPES`,
:func:`verify_neck_loop`). It is a draft, and
this module cites it as one. Its Table D.1 (the field a type 1 loop reaches
from a 3 V and a 9 V battery) rests on a source model the draft does not give
and is not reproduced.

What is not here
----------------

The loop listener and the assistive listening device of Annex F, and the
monitoring devices of clause 10, are specified by values to be met (a
sensitivity of 150 mV into 32 ohm for 400 mA/m, a volume range of 40 dB plus
or minus 5 dB, a THD of 3 %) that are single comparisons with nothing to
compute. The target frequency response of Annex F is stated by two corner
frequencies and two final slopes, with its shape only in Figure F.1. The
electromagnetic exposure of IEC 62489-2 is outside this library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy import optimize

from .._internal.display import RichDisplay
from .._internal.frozen import OwnsArrays, read_only
from .._internal.validation import (
    _as_float64,
    require_choice,
    require_count,
    require_finite,
    require_finite_array,
    require_positive,
    require_positive_array,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "NECK_LOOP_TYPES",
    "AgcCharacteristic",
    "AmplifierFrequencyResponse",
    "LoopField",
    "LoopImpedance",
    "MaximumOutputCurrent",
    "NeckLoopCharacteristics",
    "NeckLoopType",
    "NeckLoopVerification",
    "QuadraturePhaseError",
    "agc_characteristic",
    "amplifier_frequency_response",
    "amplifier_signal_to_noise_ratio",
    "compliance_voltage",
    "equivalent_input_noise_voltage",
    "loop_centre_field",
    "loop_current",
    "loop_dimensions",
    "loop_impedance",
    "loop_resistance",
    "maximum_output_current",
    "neck_loop_characteristics",
    "quadrature_phase_error",
    "rectangular_loop_field",
    "rectangular_loop_inductance",
    "verify_neck_loop",
]

#: The reference magnetic field strength of IEC 60118-4:2014 3.1, in A/m. The
#: public constant lives in :mod:`phonometry.electroacoustics.induction_loop`,
#: which imports this module; the number is repeated here rather than imported
#: back so the two modules do not import each other.
_REFERENCE_FIELD_STRENGTH_A_PER_M = 0.4

#: Height above the centre of the loop plane at which IEC 62489-1:2010
#: 5.4.10.2 measures an amplifier's magnetic field strength, in metres.
_MEASUREMENT_HEIGHT_M = 1.4

#: Resistivity of standard annealed copper at 20 degrees Celsius, in ohm
#: metres: 1/58 ohm square millimetre per metre (IEC 60028:1925, clause I (1)).
_COPPER_RESISTIVITY_OHM_M = 1.0e-6 / 58.0

#: Temperature coefficient of the resistance of standard annealed copper at
#: 20 degrees Celsius, per degree (IEC 60028:1925, clause I (4)).
_COPPER_TEMPERATURE_COEFFICIENT = 0.00393

#: The temperature the two copper constants above are stated at, in degrees
#: Celsius.
_COPPER_REFERENCE_TEMPERATURE_C = 20.0

#: Magnetic constant, in henries per metre. The exact pre-2019 value: Grover's
#: formulas carry it as the factor 0,004 microhenry per centimetre.
_MU_0 = 4.0e-7 * math.pi

#: The reference frequency every response of both standards is normalized to,
#: in hertz (IEC 62489-1:2010 5.4.12.3, IEC 60118-4:2014 8.3.7).
_REFERENCE_FREQUENCY_HZ = 1000.0

#: Relative tolerance within which a given frequency is taken as the 1 kHz
#: reference: a 1000 Hz typed as 999.9999999 is still the reference.
_FREQUENCY_MATCH_RTOL = 1.0e-6

#: The one-third-octave centres of IEC 62489-1:2010 5.4.12.2, "at least 50 Hz
#: to 8 kHz", widened to 10 kHz for the impedance of a loop: nominal values.
_THIRD_OCTAVE_CENTRES_HZ = (
    50.0,
    63.0,
    80.0,
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
)

#: Output level change within which IEC 62489-1:2010+A1:2014 5.4.13.4
#: recommends the automatic gain control range, in dB.
_AGC_OUTPUT_CHANGE_DB = 3.0

#: Input level range 5.4.13.4 recommends over that output change, in dB.
_AGC_RECOMMENDED_RANGE_DB = 32.0

#: Two output levels 3 dB apart to within this are taken as exactly 3 dB
#: apart, in dB: a characteristic stated to the tenth of a decibel, whose
#: 3,0 dB difference can come out of floating point as 3,0000000000000004,
#: does not lose its window to the rounding.
_AGC_LEVEL_MATCH_DB = 1.0e-9

#: The fewest steps an output/input characteristic can be read from.
_MIN_CHARACTERISTIC_POINTS = 2

#: The frequency range over which 5.4.14.2 states the phase error of a
#: quadrature network and 9.2.1 the input impedance of a neck loop, in hertz.
_SPEECH_BAND_HZ = (100.0, 5000.0)

#: The response difference 9.3.3 states a neck loop's frequencies at, in dB.
_NECK_LOOP_RESPONSE_STEP_DB = 3.0

#: The phase angle a quadrature network aims at, in degrees.
_QUADRATURE_DEG = 90.0

#: A point closer to a conductor than this fraction of the loop's smaller side
#: sits on the wire, where the field of a filament is infinite.
_ON_CONDUCTOR = 1.0e-9


# ---------------------------------------------------------------------------
# The field of a rectangular loop
# ---------------------------------------------------------------------------


def _segment_field(
    start: np.ndarray, end: np.ndarray, points: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    r"""Field of a unit current along one straight filament, and its singularity.

    For a filament from :math:`\mathbf{r}_1` to :math:`\mathbf{r}_2` carrying a
    unit current, the field at a point :math:`\mathbf{p}` follows from the law
    of Biot and Savart integrated along the segment,

    .. math::

       \mathbf{H} = \frac{1}{4\pi}
       \frac{(\mathbf{a}\times\mathbf{b})(|\mathbf{a}| + |\mathbf{b}|)}
       {|\mathbf{a}||\mathbf{b}|\,(|\mathbf{a}||\mathbf{b}| + \mathbf{a}\cdot\mathbf{b})},
       \qquad \mathbf{a} = \mathbf{r}_1 - \mathbf{p},\;
       \mathbf{b} = \mathbf{r}_2 - \mathbf{p}.

    The denominator vanishes only on the segment itself, where
    :math:`\mathbf{a}` and :math:`\mathbf{b}` point opposite ways; on its
    extension the cross product is zero and so is the field.

    :param start: Start point of the filament, shape ``(3,)``.
    :param end: End point, shape ``(3,)``.
    :param points: Evaluation points, shape ``(..., 3)``.
    :return: The field, shape ``(..., 3)``, and a boolean mask of the points
        that lie on the filament.
    """
    a = start - points
    b = end - points
    na = np.linalg.norm(a, axis=-1)
    nb = np.linalg.norm(b, axis=-1)
    cross = np.cross(a, b)
    denominator = na * nb * (na * nb + np.sum(a * b, axis=-1))
    scale = np.linalg.norm(end - start)
    on_wire = denominator <= (_ON_CONDUCTOR * scale) ** 2 * (na * nb)
    safe = np.where(on_wire, 1.0, denominator)
    factor = (na + nb) / (4.0 * math.pi * safe)
    field = cross * factor[..., np.newaxis]
    return np.where(on_wire[..., np.newaxis], 0.0, field), on_wire


def _loop_corners(length_m: float, width_m: float) -> np.ndarray:
    """The four corners of the loop, counterclockwise seen from +z."""
    x = length_m / 2.0
    y = width_m / 2.0
    return np.array(
        [[-x, -y, 0.0], [x, -y, 0.0], [x, y, 0.0], [-x, y, 0.0]], dtype=np.float64
    )


def _axis_field_per_ampere(length_m: float, width_m: float, height_m: float) -> float:
    r"""Vertical field of one ampere in one turn, on the loop's axis.

    The Biot-Savart integral on the axis of a rectangle of half-sides
    :math:`a` and :math:`b`, at a height :math:`z`, closes to

    .. math::

       H_z = \frac{a b}{\pi\sqrt{a^2 + b^2 + z^2}}
       \left(\frac{1}{a^2 + z^2} + \frac{1}{b^2 + z^2}\right),

    which at :math:`z = 0` and :math:`a = b = d/2` is the
    :math:`2\sqrt{2}/(\pi d)` of IEC 60118-4:2014 E.1.
    """
    a = length_m / 2.0
    b = width_m / 2.0
    z2 = height_m * height_m
    return (
        a
        * b
        / (math.pi * math.sqrt(a * a + b * b + z2))
        * (1.0 / (a * a + z2) + 1.0 / (b * b + z2))
    )


@dataclass(frozen=True)
class LoopField(OwnsArrays):
    """The magnetic field of a rectangular induction loop at a set of points.

    The loop lies in the plane :math:`z = 0`, centred on the origin, with its
    sides of length :attr:`length_m` along :math:`x` and :attr:`width_m` along
    :math:`y`, and the current runs counterclockwise seen from :math:`+z`, so
    the field inside the loop points to :math:`+z`. For a horizontal loop on
    the floor :math:`z` is the height and :attr:`h_z_a_per_m` the vertical component a
    standing listener's telecoil picks up; for a vertical loop on a counter the
    same arrays describe it turned on its side.

    :ivar current_a: The RMS current in each turn, in amperes.
    :ivar length_m: Length of the loop along :math:`x`, in metres.
    :ivar width_m: Width along :math:`y`, in metres.
    :ivar turns: Number of turns.
    :ivar x_m: The points' :math:`x` coordinates, in metres.
    :ivar y_m: The points' :math:`y` coordinates, in metres.
    :ivar z_m: The points' :math:`z` coordinates, in metres.
    :ivar h_x_a_per_m: The :math:`x` component of the RMS field strength, in A/m.
    :ivar h_y_a_per_m: The :math:`y` component, in A/m.
    :ivar h_z_a_per_m: The :math:`z` component, in A/m.
    """

    current_a: float
    length_m: float
    width_m: float
    turns: int
    x_m: np.ndarray
    y_m: np.ndarray
    z_m: np.ndarray
    h_x_a_per_m: np.ndarray
    h_y_a_per_m: np.ndarray
    h_z_a_per_m: np.ndarray

    @property
    def magnitude_a_per_m(self) -> np.ndarray:
        """The magnitude of the field strength vector, in A/m."""
        return np.asarray(
            np.sqrt(self.h_x_a_per_m**2 + self.h_y_a_per_m**2 + self.h_z_a_per_m**2)
        )

    def level_db(self, component: str = "z") -> np.ndarray:
        r"""The field strength level of one component, dB re 400 mA/m.

        :param component: ``"x"``, ``"y"``, ``"z"`` or ``"magnitude"``.
        :return: :math:`20\lg(|H|/0{,}4\ \mathrm{A/m})`; minus infinity where
            the component vanishes, which is the null line outside a loop.
        """
        name = require_choice(component, "component", ("x", "y", "z", "magnitude"))
        values = (
            self.magnitude_a_per_m
            if name == "magnitude"
            else getattr(self, f"h_{name}_a_per_m")
        )
        with np.errstate(divide="ignore"):
            return 20.0 * np.log10(np.abs(values) / _REFERENCE_FIELD_STRENGTH_A_PER_M)

    def plot(
        self,
        ax: Axes | None = None,
        *,
        component: str = "z",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the field strength level along the points, as Figures E.2 and E.3.

        The abscissa is the coordinate that varies most among the points, and
        the ordinate the level of one component in dB re 400 mA/m, with the
        0 dB reference and the plus or minus 3 dB band of IEC 60118-4:2014
        8.4.3 around it.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param component: ``"x"``, ``"y"``, ``"z"`` or ``"magnitude"``.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the level curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_loop_field

        check_language(language)
        return plot_loop_field(
            self, ax, component=component, language=language, **kwargs
        )


def rectangular_loop_field(
    current_a: float,
    length_m: float,
    width_m: float,
    x_m: ArrayLike,
    y_m: ArrayLike,
    z_m: ArrayLike,
    *,
    turns: int = 1,
) -> LoopField:
    r"""The magnetic field of a rectangular loop, by Biot and Savart.

    Each of the four sides is a straight filament whose field closes exactly
    (see the module docstring), so the result carries no discretisation. It
    reproduces the curves of Figure E.2 b) of IEC 60118-4:2014 across the
    width of that figure's loop, it is the kind of pattern Figures E.3 to E.5
    draw, and at the centre of a square it is the
    :math:`2\sqrt{2}I/(\pi d)` of E.1. The conductor is a filament, so the
    field is that of a thin wire everywhere except within a few wire radii of
    it. Metal in the building, which Annex F describes, is not modelled.

    :param current_a: RMS current in each turn, in amperes.
    :param length_m: Length of the loop along :math:`x`, in metres.
    :param width_m: Width along :math:`y`, in metres.
    :param x_m: :math:`x` coordinates of the points, in metres, with the loop
        centred on the origin.
    :param y_m: :math:`y` coordinates, broadcast against ``x_m``.
    :param z_m: :math:`z` coordinates (height above the loop plane),
        broadcast against both.
    :param turns: Number of turns, all carrying the same current.
    :return: A :class:`LoopField`.
    :raises ValueError: for a non-positive dimension, a non-finite coordinate
        or a point on the conductor, where a filament's field is infinite.
    """
    current = require_finite(current_a, "current_a")
    length = require_positive(length_m, "length_m")
    width = require_positive(width_m, "width_m")
    n = require_count(turns, "turns")
    coordinates = (
        _as_float64(x_m, "x_m"),
        _as_float64(y_m, "y_m"),
        _as_float64(z_m, "z_m"),
    )
    try:
        xs, ys, zs = np.broadcast_arrays(*coordinates)
    except ValueError as exc:
        msg = "'x_m', 'y_m' and 'z_m' must broadcast to one shape."
        raise ValueError(msg) from exc
    if not (
        np.all(np.isfinite(xs)) and np.all(np.isfinite(ys)) and np.all(np.isfinite(zs))
    ):
        msg = "'x_m', 'y_m' and 'z_m' must be finite."
        raise ValueError(msg)
    points = np.stack([xs, ys, zs], axis=-1)
    corners = _loop_corners(length, width)
    total = np.zeros(points.shape, dtype=np.float64)
    on_conductor = np.zeros(xs.shape, dtype=bool)
    for k in range(4):
        field, on_wire = _segment_field(corners[k], corners[(k + 1) % 4], points)
        total += field
        on_conductor |= on_wire
    if np.any(on_conductor):
        msg = (
            "a point lies on the loop conductor, where the field of a filament "
            "is infinite; move it off the wire."
        )
        raise ValueError(msg)
    total *= current * n
    return LoopField(
        current_a=current,
        length_m=length,
        width_m=width,
        turns=n,
        x_m=xs,
        y_m=ys,
        z_m=zs,
        h_x_a_per_m=total[..., 0],
        h_y_a_per_m=total[..., 1],
        h_z_a_per_m=total[..., 2],
    )


def loop_centre_field(
    current_a: float, length_m: float, *, width_m: float | None = None, turns: int = 1
) -> float:
    r"""The field at the centre of a loop, in its plane (IEC 60118-4:2014 E.1).

    .. math::

       H = \frac{2\sqrt{2}\,N I}{\pi d},

    with :math:`d` the side of a square loop, or :math:`\sqrt{d_1 d_2}` for a
    rectangle, which E.1 allows "Provided that the sides d1, d2 of a
    rectangular loop are not extremely different". For the square it is
    exact; for a rectangle
    it is the approximation E.1 prints, and :func:`rectangular_loop_field`
    gives the exact value, which is larger by
    :math:`\sqrt{(d_1^2 + d_2^2)/(2 d_1 d_2)}`: 0,35 dB at an aspect ratio
    of 1,5 and 3,3 dB at 4.

    :param current_a: RMS current in each turn, in amperes.
    :param length_m: Side of the square, or one side of the rectangle, in
        metres.
    :param width_m: The other side of a rectangle, in metres; ``None`` for a
        square.
    :param turns: Number of turns.
    :return: The field strength at the centre, in A/m.
    """
    current = require_finite(current_a, "current_a")
    side = require_positive(length_m, "length_m")
    if width_m is not None:
        side = math.sqrt(side * require_positive(width_m, "width_m"))
    n = require_count(turns, "turns")
    return 2.0 * math.sqrt(2.0) * n * current / (math.pi * side)


def loop_current(
    length_m: float,
    width_m: float,
    *,
    height_m: float = _MEASUREMENT_HEIGHT_M,
    field_strength_a_per_m: float = _REFERENCE_FIELD_STRENGTH_A_PER_M,
    turns: int = 1,
) -> float:
    """The current a loop needs for a field strength above its centre.

    The exact on-axis field of the rectangle (see the module docstring),
    inverted for the current. The defaults are the conditions of IEC
    62489-1:2010 5.4.10.2, 400 mA/m at 1,4 m above the centre of the loop
    plane, which is also where IEC 60118-4:2014 Figure H.1 plots the current
    required against the loop's size and aspect ratio, and the curves of that
    figure are reproduced: 4,88 A for a 10 m square and 6,41 A for 10 m by
    30 m, read as about 4,89 A and 6,41 A.

    :param length_m: Length of the loop, in metres.
    :param width_m: Width of the loop, in metres.
    :param height_m: Height above the centre of the loop plane, in metres.
    :param field_strength_a_per_m: The field strength to reach, in A/m.
    :param turns: Number of turns.
    :return: The RMS current in each turn, in amperes.
    """
    length = require_positive(length_m, "length_m")
    width = require_positive(width_m, "width_m")
    height = require_finite(height_m, "height_m")
    target = require_positive(field_strength_a_per_m, "field_strength_a_per_m")
    n = require_count(turns, "turns")
    return target / (n * _axis_field_per_ampere(length, width, height))


def loop_dimensions(
    current_a: float,
    *,
    aspect_ratio: float = 1.0,
    height_m: float = _MEASUREMENT_HEIGHT_M,
    field_strength_a_per_m: float = _REFERENCE_FIELD_STRENGTH_A_PER_M,
    turns: int = 1,
) -> tuple[float, float]:
    """The largest loop an amplifier's current drives to a field strength (5.4.11).

    IEC 62489-1:2010 5.4.11.1 states "the linear dimensions of a square loop,
    and a loop of aspect ratio 3:1, for which the magnetic field strength,
    measured as specified in 5.4.10.1, is 400 mA/m". Above the centre, the
    field of a given current first grows with the loop and then falls, so two
    sizes reach any field below the peak. The characteristic is the larger
    one: the biggest loop the amplifier can serve, which is the size a
    specification is read for.

    :param current_a: The amplifier's RMS output current into the loop, in
        amperes.
    :param aspect_ratio: Long side over short side, at least 1 (1 for the
        square of 5.4.11.1, 3 for its second loop).
    :param height_m: Height above the centre of the loop plane, in metres
        (1,4 m, 5.4.10.2).
    :param field_strength_a_per_m: The field strength to reach, in A/m
        (400 mA/m).
    :param turns: Number of turns.
    :return: ``(short_side_m, long_side_m)``, in metres.
    :raises ValueError: when the current cannot reach the field strength at
        that height with a loop of any size.
    """
    current = require_positive(current_a, "current_a")
    ratio = require_finite(aspect_ratio, "aspect_ratio")
    if ratio < 1.0:
        msg = f"'aspect_ratio' is long side over short side and must be at least 1; got {ratio}."
        raise ValueError(msg)
    height = require_positive(height_m, "height_m")
    target = require_positive(field_strength_a_per_m, "field_strength_a_per_m")
    n = require_count(turns, "turns")

    def field(short: float) -> float:
        return n * current * _axis_field_per_ampere(ratio * short, short, height)

    # The on-axis field of a loop of fixed shape peaks at a short side of the
    # order of the height; bracket the peak before splitting the branches.
    peak = optimize.minimize_scalar(
        lambda s: -field(s),
        bounds=(1e-3 * height, 100.0 * height),
        method="bounded",
        options={"xatol": 1e-12 * height},
    )
    best = float(peak.x)
    if field(best) < target:
        msg = (
            f"{current:g} A in {n} turn(s) cannot reach {target:g} A/m at "
            f"{height:g} m with a loop of any size: the most it gives there is "
            f"{field(best):.4g} A/m."
        )
        raise ValueError(msg)
    upper = best
    while field(upper) >= target:
        upper *= 2.0
    short = float(
        optimize.brentq(
            lambda s: field(s) - target, best, upper, xtol=1e-12, rtol=1e-14
        )
    )
    return short, ratio * short


# ---------------------------------------------------------------------------
# The loop as a load
# ---------------------------------------------------------------------------


def loop_resistance(
    perimeter_m: float,
    conductor_area_mm2: float,
    *,
    turns: int = 1,
    conductor_temperature_c: float = _COPPER_REFERENCE_TEMPERATURE_C,
) -> float:
    r"""The resistance of a copper loop (IEC 62489-1:2010 B.2).

    :math:`R = \rho N l / a`, with the resistivity of standard annealed copper,
    1/58 ohm square millimetre per metre at 20 degrees Celsius, carried to the
    conductor's temperature by the coefficient 0,00393 per degree (IEC
    60028:1925, clause I). B.2 quotes "approximately 0,017 ohm/m" for 1 mm² at
    25 degrees Celsius; Table B.1 is computed at 20 degrees, where its six
    rounded resistances hold the resistivity between 1,716 and 1,738 times
    :math:`10^{-8}` ohm metres, and 1/58 is inside that range.

    :param perimeter_m: Length of one turn, in metres.
    :param conductor_area_mm2: Cross-sectional area of the conductor, in
        square millimetres.
    :param turns: Number of turns.
    :param conductor_temperature_c: Temperature of the conductor, in degrees
        Celsius.
    :return: The DC resistance of the loop, in ohms.
    """
    perimeter = require_positive(perimeter_m, "perimeter_m")
    area = require_positive(conductor_area_mm2, "conductor_area_mm2")
    n = require_count(turns, "turns")
    temperature = require_finite(conductor_temperature_c, "conductor_temperature_c")
    resistivity = _COPPER_RESISTIVITY_OHM_M * (
        1.0
        + _COPPER_TEMPERATURE_COEFFICIENT
        * (temperature - _COPPER_REFERENCE_TEMPERATURE_C)
    )
    if resistivity <= 0.0:
        msg = f"'conductor_temperature_c' of {temperature} degC is outside the linear law."
        raise ValueError(msg)
    return resistivity * n * perimeter / (area * 1.0e-6)


def rectangular_loop_inductance(
    length_m: float,
    width_m: float,
    conductor_area_mm2: float,
    *,
    turns: int = 1,
    internal_inductance: bool = True,
) -> float:
    r"""The inductance of a rectangular loop of round wire (Grover, Formula (58)).

    .. math::

       L = \frac{\mu_0}{\pi}\left[a\ln\frac{2a}{\rho} + b\ln\frac{2b}{\rho}
       + 2\sqrt{a^2 + b^2} - a\sinh^{-1}\frac{a}{b} - b\sinh^{-1}\frac{b}{a}
       - 2(a + b) + \frac{\mu}{4}(a + b)\right]

    for sides :math:`a` and :math:`b` and a wire of radius :math:`\rho`
    (Grover, *Inductance Calculations*, 1946, p. 60; the factor 0,004
    microhenry per centimetre there is :math:`\mu_0/\pi`). The last term is the
    flux inside the wire, :math:`\mu = 1` for copper. For :math:`N` turns the
    single-turn value is multiplied by :math:`N^2`, the perfect coupling IEC
    62489-1:2010 Table B.1 assumes.

    Table B.1 is reproduced without the internal term
    (``internal_inductance=False``): the counter loop, the home loop, the small
    room and the typical place of worship come out at 189, 22, 47 and 109
    microhenries, as printed. With the term they are about 3 % higher, from
    2,7 % for the place of worship to 4,2 % for the counter loop. At audio
    frequencies the current fills the wire (the skin depth in copper is 2 mm
    at 1 kHz), which is why the term is included by default.

    :param length_m: One side of the rectangle, in metres.
    :param width_m: The other side, in metres.
    :param conductor_area_mm2: Cross-sectional area of the round conductor,
        in square millimetres; the radius is :math:`\sqrt{a/\pi}`.
    :param turns: Number of turns.
    :param internal_inductance: Include the flux inside the wire (the
        :math:`\mu/4` term).
    :return: The inductance, in henries.
    :raises ValueError: when the wire is not thin against the sides, where the
        formula does not hold.
    """
    a = require_positive(length_m, "length_m")
    b = require_positive(width_m, "width_m")
    area = require_positive(conductor_area_mm2, "conductor_area_mm2")
    n = require_count(turns, "turns")
    radius = math.sqrt(area * 1.0e-6 / math.pi)
    if radius * 10.0 > min(a, b):
        msg = (
            f"a wire of radius {radius * 1e3:.3g} mm is not thin against sides of "
            f"{a:g} m and {b:g} m; Formula (58) holds for a filament-like conductor."
        )
        raise ValueError(msg)
    diagonal = math.hypot(a, b)
    bracket = (
        a * math.log(2.0 * a / radius)
        + b * math.log(2.0 * b / radius)
        + 2.0 * diagonal
        - a * math.asinh(a / b)
        - b * math.asinh(b / a)
        - 2.0 * (a + b)
    )
    if internal_inductance:
        bracket += (a + b) / 4.0
    return n * n * _MU_0 / math.pi * bracket


def _frequencies_to_read(frequency_hz: ArrayLike) -> np.ndarray:
    """Frequencies of any shape to read a tabulated quantity at: positive, finite."""
    f = _as_float64(frequency_hz, "frequency_hz")
    if not np.all(np.isfinite(f)) or np.any(f <= 0.0):
        msg = "'frequency_hz' must be positive and finite."
        raise ValueError(msg)
    return f


@dataclass(frozen=True)
class LoopImpedance(OwnsArrays):
    r"""The impedance of a loop, a resistance in series with an inductance.

    IEC 62489-1:2010 5.4.3.2 states the rated load "as a series combination of
    resistance and inductance", and B.2 represents the loop the same way. The
    magnitude :math:`|Z| = \sqrt{R^2 + (2\pi f L)^2}` is
    :math:`\sqrt{2}` times the resistance at the corner frequency
    :math:`f_\mathrm{c} = R/(2\pi L)`, "1,4 times" in IEC 60118-4:2014 E.3,
    and the voltage an amplifier has to deliver for a current :math:`I` is
    :math:`U = I|Z|`, the :math:`U_\mathrm{h}` of E.3.

    :ivar resistance_ohm: The series resistance, in ohms.
    :ivar inductance_h: The series inductance, in henries.
    :ivar frequencies_hz: The frequencies the magnitude is tabulated at, in
        hertz.
    :ivar impedance_ohm: The magnitude of the impedance there, in ohms.
    """

    resistance_ohm: float
    inductance_h: float
    frequencies_hz: np.ndarray
    impedance_ohm: np.ndarray

    @property
    def corner_frequency_hz(self) -> float:
        """The frequency where the reactance equals the resistance, in hertz."""
        return self.resistance_ohm / (2.0 * math.pi * self.inductance_h)

    def at(self, frequency_hz: ArrayLike) -> np.ndarray:
        """The magnitude of the impedance at any frequency, in ohms.

        :param frequency_hz: Frequencies, in hertz, positive and finite.
        :return: :math:`|Z|` there, in ohms.
        """
        f = _frequencies_to_read(frequency_hz)
        return np.hypot(self.resistance_ohm, 2.0 * math.pi * f * self.inductance_h)

    def drive_voltage(self, current_a: float, frequency_hz: ArrayLike) -> np.ndarray:
        """The RMS voltage that drives a current through the loop (IEC 60118-4 E.3).

        :param current_a: RMS loop current, in amperes.
        :param frequency_hz: Frequencies, in hertz, positive and finite.
        :return: :math:`U = I|Z|`, in volts.
        """
        current = require_finite(current_a, "current_a")
        return current * self.at(frequency_hz)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Draw the magnitude of the impedance against frequency.

        The resistance is drawn as a floor and the corner frequency marked,
        where the magnitude has risen to :math:`\sqrt{2}` times the resistance.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the impedance curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_loop_impedance

        check_language(language)
        return plot_loop_impedance(self, ax, language=language, **kwargs)


def loop_impedance(
    resistance_ohm: float,
    inductance_h: float,
    *,
    frequencies_hz: ArrayLike | None = None,
) -> LoopImpedance:
    """The impedance of a loop from its resistance and inductance.

    :param resistance_ohm: Series resistance, in ohms (:func:`loop_resistance`,
        plus that of the feed cable).
    :param inductance_h: Series inductance, in henries
        (:func:`rectangular_loop_inductance`, plus that of the feed cable).
    :param frequencies_hz: Frequencies to tabulate the magnitude at, in hertz;
        by default the one-third-octave centres from 50 Hz to 10 kHz.
    :return: A :class:`LoopImpedance`.
    """
    resistance = require_positive(resistance_ohm, "resistance_ohm")
    inductance = require_positive(inductance_h, "inductance_h")
    f = (
        np.array(_THIRD_OCTAVE_CENTRES_HZ, dtype=np.float64)
        if frequencies_hz is None
        else require_positive_array(frequencies_hz, "frequencies_hz")
    )
    magnitude = np.hypot(resistance, 2.0 * math.pi * f * inductance)
    return LoopImpedance(
        resistance_ohm=resistance,
        inductance_h=inductance,
        frequencies_hz=f,
        impedance_ohm=read_only(magnitude),
    )


# ---------------------------------------------------------------------------
# The amplifier
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MaximumOutputCurrent(OwnsArrays):
    """The maximum (distortion-limited) output current of an amplifier (5.4.7).

    :ivar resistor_voltage_v: The total RMS voltage across the resistive part
        of the rated load at each step of the level, in volts.
    :ivar load_current_a: The load current at each step, that voltage over
        the resistance, in amperes.
    :ivar thd_percent: The total harmonic distortion across the resistive
        part at each step, in percent.
    :ivar load_resistance_ohm: The resistance of the resistive part of the
        rated load, in ohms.
    :ivar rated_thd_percent: The rated total harmonic distortion of 5.4.6, in
        percent.
    :ivar maximum_current_a: The load current at which the distortion first
        reaches the rated value, interpolated linearly between the two steps
        either side, in amperes: the characteristic of 5.4.7, stated in
        amperes (5.4.7.3).
    """

    resistor_voltage_v: np.ndarray
    load_current_a: np.ndarray
    thd_percent: np.ndarray
    load_resistance_ohm: float
    rated_thd_percent: float
    maximum_current_a: float

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the distortion against the load current, with the rated THD.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the distortion curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_maximum_output_current

        check_language(language)
        return plot_maximum_output_current(self, ax, language=language, **kwargs)


def maximum_output_current(
    resistor_voltage_v: ArrayLike,
    thd_percent: ArrayLike,
    *,
    load_resistance_ohm: float,
    rated_thd_percent: float,
) -> MaximumOutputCurrent:
    """The maximum (distortion-limited) output current of an amplifier (5.4.7).

    IEC 62489-1:2010 5.4.7.1 defines it as "The maximum current, produced by a
    sinusoidal input signal at 1 kHz, deliverable for at least 10 s into the
    rated load without exceeding the rated total harmonic distortion (THD)".
    5.4.7.2 measures it from standard measuring conditions: the load current
    is increased until the total harmonic distortion across the resistive
    part of the load equals the rated value, and "The current is then
    calculated from the total voltage across the resistive part of the load
    and the resistance value". The 10 s the current has to be held for is a
    condition on the measurement, not a computation.

    The steps of the level are given as the total RMS voltage across the
    resistance and the distortion read there, in ascending order of voltage;
    the current where the distortion first reaches the rated value is
    interpolated linearly between the two steps either side of it.

    :param resistor_voltage_v: The total RMS voltage across the resistive part
        of the load at each step, in volts, strictly ascending.
    :param thd_percent: The total harmonic distortion measured across it at
        each step, in percent, none of it negative.
    :param load_resistance_ohm: The resistance of the resistive part of the
        rated load, in ohms.
    :param rated_thd_percent: The rated total harmonic distortion (5.4.6), in
        percent.
    :return: A :class:`MaximumOutputCurrent`.
    :raises ValueError: for a negative distortion, which no measurement gives,
        or when the distortion never reaches the rated value, or already
        exceeds it at the first step, so the current lies outside the steps
        measured.
    """
    voltage = require_positive_array(resistor_voltage_v, "resistor_voltage_v")
    thd = require_finite_array(thd_percent, "thd_percent")
    if np.any(thd < 0.0):
        msg = (
            f"'thd_percent' must be non-negative, got {float(np.min(thd)):g} %: "
            "a distortion is a ratio of RMS values."
        )
        raise ValueError(msg)
    if voltage.size != thd.size or voltage.size < _MIN_CHARACTERISTIC_POINTS:
        msg = "'resistor_voltage_v' and 'thd_percent' need the same length, at least 2."
        raise ValueError(msg)
    _ascending(voltage, "resistor_voltage_v")
    resistance = require_positive(load_resistance_ohm, "load_resistance_ohm")
    rated = require_positive(rated_thd_percent, "rated_thd_percent")
    current = voltage / resistance
    if thd[0] > rated:
        msg = (
            f"the distortion is already {float(thd[0]):g} % at the first step, above "
            f"the rated {rated:g} %: start the steps lower."
        )
        raise ValueError(msg)
    reached = np.flatnonzero(thd >= rated)
    if reached.size == 0:
        msg = (
            f"the distortion never reaches the rated {rated:g} % (it peaks at "
            f"{float(np.max(thd)):g} %): raise the level further."
        )
        raise ValueError(msg)
    k = int(reached[0])
    if k == 0:
        maximum = float(current[0])
    else:
        t = (rated - float(thd[k - 1])) / (float(thd[k]) - float(thd[k - 1]))
        maximum = float(current[k - 1] + t * (current[k] - current[k - 1]))
    return MaximumOutputCurrent(
        resistor_voltage_v=voltage,
        load_current_a=read_only(current),
        thd_percent=thd,
        load_resistance_ohm=resistance,
        rated_thd_percent=rated,
        maximum_current_a=maximum,
    )


def compliance_voltage(voltage_v: ArrayLike) -> float:
    r"""The compliance voltage of an amplifier (IEC 62489-1:2010 5.4.8).

    The voltage across the rated load is recorded "over a period of at least
    60 s" of the specified pink noise with the automatic gain control fully in
    operation, or with the RMS output current 6 dB below the maximum output
    current (5.4.8.2 c). The magnitudes of its most positive and most negative
    peaks are averaged and divided by :math:`\sqrt{2}` (5.4.8.2 d), which gives
    the RMS voltage of the sine with the same peaks.

    :param voltage_v: The recorded load voltage, in volts, sampled at more
        than 50 000 samples per second or through more than 25 kHz of
        bandwidth (5.4.8.2 c).
    :return: The compliance voltage, in volts.
    :raises ValueError: for a record that does not swing both ways.
    """
    v = require_finite_array(voltage_v, "voltage_v")
    positive = float(np.max(v))
    negative = float(np.min(v))
    if positive <= 0.0 or negative >= 0.0:
        msg = (
            "'voltage_v' must swing both ways: the compliance voltage averages "
            "the positive-going and the negative-going peak."
        )
        raise ValueError(msg)
    return (positive - negative) / 2.0 / math.sqrt(2.0)


def equivalent_input_noise_voltage(
    source_emf_v: float, output_current_a: float, noise_current_a: float
) -> float:
    r"""The equivalent input noise voltage of an amplifier (IEC 62489-1:2010 5.4.9).

    With the amplifier below the action of its automatic gain control, a 1 kHz
    source e.m.f. :math:`U` gives an output current :math:`I`; with the e.m.f.
    reduced to zero the A-weighted output current is :math:`I_\mathrm{n}`. The
    1 kHz input that would give the same current as the noise is

    .. math::

       U_\mathrm{n} = \frac{U I_\mathrm{n}}{I}.

    :param source_emf_v: The 1 kHz source e.m.f., in volts.
    :param output_current_a: The output current it produces, in amperes.
    :param noise_current_a: The A-weighted output current with no input, in
        amperes.
    :return: The equivalent input noise voltage, in volts.
    """
    u = require_positive(source_emf_v, "source_emf_v")
    i = require_positive(output_current_a, "output_current_a")
    i_n = require_positive(noise_current_a, "noise_current_a")
    return u * i_n / i


def amplifier_signal_to_noise_ratio(
    rated_current_a: float, noise_current_a: float
) -> float:
    r"""The signal-to-noise ratio of an amplifier (IEC 62489-1:2010 5.4.9.2).

    .. math::

       S = 10\lg\frac{I_\mathrm{r}^2}{I_\mathrm{n}^2}\ \mathrm{dB},

    the rated output current against the A-weighted output current with the
    source e.m.f. reduced to zero.

    :param rated_current_a: The rated output current :math:`I_\mathrm{r}`, in
        amperes.
    :param noise_current_a: The noise output current :math:`I_\mathrm{n}`, in
        amperes.
    :return: The signal-to-noise ratio, in dB.
    """
    i_r = require_positive(rated_current_a, "rated_current_a")
    i_n = require_positive(noise_current_a, "noise_current_a")
    return 10.0 * math.log10(i_r * i_r / (i_n * i_n))


def _reference_index(frequencies: np.ndarray, name: str) -> int:
    """The index of the 1 kHz entry, which every normalized response needs."""
    matches = np.flatnonzero(
        np.isclose(
            frequencies, _REFERENCE_FREQUENCY_HZ, rtol=_FREQUENCY_MATCH_RTOL, atol=0.0
        )
    )
    if matches.size != 1:
        msg = (
            f"'{name}' must contain 1000 Hz exactly once: the response is "
            "normalized to the one at 1 kHz."
        )
        raise ValueError(msg)
    return int(matches[0])


def _ascending(frequencies: np.ndarray, name: str) -> None:
    """Require strictly ascending frequencies."""
    if frequencies.size > 1 and not np.all(np.diff(frequencies) > 0.0):
        msg = f"'{name}' must be strictly ascending."
        raise ValueError(msg)


@dataclass(frozen=True)
class AmplifierFrequencyResponse(OwnsArrays):
    """The frequency response of an amplifier into its load (IEC 62489-1:2010 5.4.12).

    :ivar frequencies_hz: The measurement frequencies, in hertz, ascending.
    :ivar output_current_a: The load current measured at each, in amperes.
    :ivar response_db: The current level relative to the one at 1 kHz, in dB,
        so 0 dB at 1 kHz (5.4.12.3).
    """

    frequencies_hz: np.ndarray
    output_current_a: np.ndarray
    response_db: np.ndarray

    def at(self, frequency_hz: ArrayLike) -> np.ndarray:
        """The response at any frequency inside the measured range, in dB.

        Interpolated linearly against the logarithm of frequency, the way a
        response measured at one-third-octave centres is read between them.

        :param frequency_hz: Frequencies, in hertz.
        :return: The response there, dB re 1 kHz.
        :raises ValueError: for a frequency that is not finite and positive,
            or lies outside the measured range.
        """
        f = _frequencies_to_read(frequency_hz)
        lo, hi = float(self.frequencies_hz[0]), float(self.frequencies_hz[-1])
        if np.any(f < lo * (1.0 - _FREQUENCY_MATCH_RTOL)) or np.any(
            f > hi * (1.0 + _FREQUENCY_MATCH_RTOL)
        ):
            msg = f"frequency outside the measured range {lo:g} Hz to {hi:g} Hz."
            raise ValueError(msg)
        return np.asarray(
            np.interp(np.log(f), np.log(self.frequencies_hz), self.response_db)
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the response against frequency, 0 dB at 1 kHz (5.4.12.3).

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the response curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_amplifier_frequency_response

        check_language(language)
        return plot_amplifier_frequency_response(self, ax, language=language, **kwargs)


def amplifier_frequency_response(
    frequencies_hz: ArrayLike, output_current_a: ArrayLike
) -> AmplifierFrequencyResponse:
    """The frequency response of an amplifier into its rated load (5.4.12).

    Under standard measuring conditions, with the automatic gain control and
    compression disabled or with the input the manufacturer states, the
    signal frequency is stepped through the one-third-octave centres "over the
    range of at least 50 Hz to 8 kHz" and the load current measured at each
    (5.4.12.2). The result is presented with the response at 1 kHz taken as
    0 dB (5.4.12.3).

    :param frequencies_hz: The measurement frequencies, in hertz, ascending
        and including 1000 Hz.
    :param output_current_a: The RMS load current at each, in amperes.
    :return: An :class:`AmplifierFrequencyResponse`.
    """
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    current = require_positive_array(output_current_a, "output_current_a")
    if f.size != current.size:
        msg = "'frequencies_hz' and 'output_current_a' must have the same length."
        raise ValueError(msg)
    _ascending(f, "frequencies_hz")
    ref = _reference_index(f, "frequencies_hz")
    response = 20.0 * np.log10(current / current[ref])
    return AmplifierFrequencyResponse(
        frequencies_hz=f,
        output_current_a=current,
        response_db=read_only(response),
    )


def _range_tables(y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sparse tables of the running minimum and maximum of ``y``.

    Row ``r`` holds the extreme of the ``2**r`` values from each index on,
    padded past the end, so the extreme of any stretch is the extreme of two
    overlapping rows' entries.
    """
    lowest = [y]
    highest = [y]
    span = 1
    while 2 * span <= y.size:
        lowest.append(np.minimum(lowest[-1][:-span], lowest[-1][span:]))
        highest.append(np.maximum(highest[-1][:-span], highest[-1][span:]))
        span *= 2
    table_min = np.full((len(lowest), y.size), np.inf)
    table_max = np.full((len(highest), y.size), -np.inf)
    for row, (low, high) in enumerate(zip(lowest, highest, strict=True)):
        table_min[row, : low.size] = low
        table_max[row, : high.size] = high
    return table_min, table_max


def _widest_window(x: np.ndarray, y: np.ndarray, spread: float) -> tuple[float, float]:
    r"""The widest span of ``x`` over which the broken line through ``y`` varies by at most ``spread``.

    Exact on the line drawn straight between the steps. In a widest window
    the lowest and the highest value each lie at a step inside it or at one
    of its ends. When neither lies at a step, the window slides without
    changing its spread until an end reaches a step or a step becomes an
    extreme: were the spread to shrink one way, the window could widen. So
    one widest window holds a step ``k`` at its lowest or its highest value,
    and lies wholly inside the band ``[y_k, y_k + spread]`` or
    ``[y_k - spread, y_k]``. The line stays inside that band over a run of
    steps around ``k``, bounded by the nearest steps outside it, and on into
    the segments either side up to where it crosses an edge; that run is a
    window, and the widest window is the widest run, the leftmost of two
    that tie.

    The run's steps are found by a binary search over sparse tables of the
    running extremes, for every step and both bands at once, so the work
    grows as :math:`n \log n` in the number of steps and not with the span
    of ``x``. A step within :data:`_AGC_LEVEL_MATCH_DB` of an edge counts as
    inside, so a difference of 3 dB that floating point leaves a hair over
    3 dB does not cut a run short; the crossings are taken at the edges.
    """
    n = y.size
    anchor = np.concatenate([np.arange(n), np.arange(n)])
    lows = np.concatenate([y, y - spread])
    highs = np.concatenate([y + spread, y])
    table_min, table_max = _range_tables(y)

    def fits(first: np.ndarray, last: np.ndarray) -> np.ndarray:
        row = np.frexp(last - first + 1)[1] - 1
        other = last - (1 << row) + 1
        low = np.minimum(table_min[row, first], table_min[row, other])
        high = np.maximum(table_max[row, first], table_max[row, other])
        return np.asarray(
            (low >= lows - _AGC_LEVEL_MATCH_DB) & (high <= highs + _AGC_LEVEL_MATCH_DB)
        )

    below, above = np.zeros_like(anchor), anchor.copy()
    while np.any(below < above):
        middle = (below + above) // 2
        inside = fits(middle, anchor)
        above = np.where(inside, middle, above)
        below = np.where(inside, below, middle + 1)
    first = below
    below, above = anchor.copy(), np.full_like(anchor, n - 1)
    while np.any(below < above):
        middle = (below + above + 1) // 2
        inside = fits(anchor, middle)
        below = np.where(inside, middle, below)
        above = np.where(inside, above, middle - 1)
    last = below

    def crossing(
        inner: np.ndarray, outer: np.ndarray, beyond: np.ndarray
    ) -> np.ndarray:
        """Where the segment from a step inside to the next one outside leaves the band."""
        y_out = y[outer]
        edge = np.where(y_out < lows, lows, highs)
        # The step beyond is outside the band and the inner one inside, so
        # their levels differ wherever the fraction is used.
        rise = np.where(beyond, y_out - y[inner], 1.0)
        fraction = np.clip((edge - y[inner]) / rise, 0.0, 1.0)
        return np.asarray(
            np.where(beyond, x[inner] + fraction * (x[outer] - x[inner]), x[inner])
        )

    start = crossing(first, np.maximum(first - 1, 0), first > 0)
    end = crossing(last, np.minimum(last + 1, n - 1), last < n - 1)
    best = int(np.lexsort((start, -(end - start)))[0])
    return float(start[best]), float(end[best])


@dataclass(frozen=True)
class AgcCharacteristic(OwnsArrays):
    """The steady-state output/input characteristic of an amplifier (5.4.13).

    :ivar source_emf_db: The source e.m.f. levels, in dB, ascending.
    :ivar output_level_db: The output current level at each, in dB referred to
        the rated maximum output current (5.4.13.3).
    :ivar agc_range_db: The widest span of input level over which the output
        level changes by no more than 3 dB, in dB: the quantity IEC
        62489-1:2010+A1:2014 5.4.13.4 recommends to be at least 32 dB.
    :ivar agc_range_start_db: The input level where that span starts, in dB.
    :ivar agc_range_end_db: The input level where it ends, in dB.
    """

    source_emf_db: np.ndarray
    output_level_db: np.ndarray
    agc_range_db: float
    agc_range_start_db: float
    agc_range_end_db: float

    @property
    def recommended_range_db(self) -> float:
        """The range 5.4.13.4 recommends, 32 dB, for comparison with :attr:`agc_range_db`."""
        return _AGC_RECOMMENDED_RANGE_DB

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw output level against input level, as Figure A.1.

        The span of :attr:`agc_range_db` is shaded, with the 3 dB output band
        it is taken over.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the characteristic's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_agc_characteristic

        check_language(language)
        return plot_agc_characteristic(self, ax, language=language, **kwargs)


def agc_characteristic(
    source_emf_db: ArrayLike, output_level_db: ArrayLike
) -> AgcCharacteristic:
    """The output/input characteristic of an amplifier and its AGC range (5.4.13).

    From standard measuring conditions the source e.m.f. is reduced to zero
    and raised in steps, the output current being read at each once it has
    settled (5.4.13.2), and the result is plotted with the e.m.f. on a
    logarithmic abscissa and the output current level in dB referred to the
    rated maximum output current (5.4.13.3). Amendment 1 adds the
    recommendation of 5.4.13.4: "an input level range of at least 32 dB for a
    maximum output level change of 3 dB".

    That range is read here as the widest span of input level over which the
    output varies by at most 3 dB, on the characteristic interpolated
    linearly between the measured steps, and found exactly: its ends are
    steps, or the inputs where the line crosses a step's output level or that
    level 3 dB up or down. For a characteristic that rises and then holds,
    which is what an automatic gain control is (Annex A), it runs from the
    input where the output is 3 dB below its top to the highest input
    measured.

    :param source_emf_db: Source e.m.f. levels, in dB re any fixed voltage,
        strictly ascending.
    :param output_level_db: Output current level at each, in dB re the rated
        maximum output current.
    :return: An :class:`AgcCharacteristic`.
    """
    x = require_finite_array(source_emf_db, "source_emf_db")
    y = require_finite_array(output_level_db, "output_level_db")
    if x.size != y.size or x.size < _MIN_CHARACTERISTIC_POINTS:
        msg = "'source_emf_db' and 'output_level_db' need the same length, at least 2."
        raise ValueError(msg)
    _ascending(x, "source_emf_db")
    start, end = _widest_window(x, y, _AGC_OUTPUT_CHANGE_DB)
    return AgcCharacteristic(
        source_emf_db=x,
        output_level_db=y,
        agc_range_db=end - start,
        agc_range_start_db=start,
        agc_range_end_db=end,
    )


@dataclass(frozen=True)
class QuadraturePhaseError(OwnsArrays):
    r"""The phase error of a quadrature network for a phased loop array (5.4.14).

    Two adjacent loops fed with currents about 90 degrees apart make a field
    whose direction rotates, instead of one that cancels at the nulls. A
    deviation :math:`\delta` from 90 degrees leaves an in-phase component
    :math:`\cos(90^\circ - \delta) = \sin\delta` of one field against the
    other, which raises the level where the two add and lowers it where they
    subtract, by :math:`20\lg(1 \pm \sin\delta)` dB (5.4.14.1: at 85 degrees
    the in-phase part is :math:`\cos 85^\circ = 0{,}087`).

    :ivar frequencies_hz: The measurement frequencies, in hertz.
    :ivar phase_difference_deg: The phase angle between the loop currents at
        each, in degrees.
    :ivar deviation_deg: Its absolute deviation from 90 degrees, in degrees.
    :ivar max_deviation_deg: The largest deviation over 100 Hz to 5 kHz, the
        characteristic of 5.4.14.2, in degrees.
    :ivar max_deviation_frequency_hz: Where it occurs, in hertz, stated with
        it (5.4.14.4).
    """

    frequencies_hz: np.ndarray
    phase_difference_deg: np.ndarray
    deviation_deg: np.ndarray
    max_deviation_deg: float
    max_deviation_frequency_hz: float

    @property
    def level_increase_db(self) -> float:
        """Where the in-phase parts add, the level rises by this, in dB."""
        return 20.0 * math.log10(1.0 + math.sin(math.radians(self.max_deviation_deg)))

    @property
    def level_decrease_db(self) -> float:
        r"""Where they subtract, the level falls by this, in dB (a negative number).

        :math:`20\lg(1 - \sin\delta)`, computed as
        :math:`20\lg\left(2\sin^2(45^\circ - \delta/2)\right)`, which is the
        same number without the cancellation near 90 degrees. At a deviation
        of 90 degrees, currents in phase or in antiphase, the two fields
        cancel where they subtract and the fall is minus infinity.
        """
        half = math.radians((_QUADRATURE_DEG - self.max_deviation_deg) / 2.0)
        with np.errstate(divide="ignore"):
            return float(20.0 * np.log10(2.0 * math.sin(half) ** 2))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the deviation from 90 degrees against frequency.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the deviation curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_quadrature_phase_error

        check_language(language)
        return plot_quadrature_phase_error(self, ax, language=language, **kwargs)


def quadrature_phase_error(
    frequencies_hz: ArrayLike, phase_difference_deg: ArrayLike
) -> QuadraturePhaseError:
    """The maximum deviation from 90 degrees between two loop currents (5.4.14).

    The phase angle between the currents of the two loops, measured across a
    low-value series resistor in each (5.4.14.3), is judged over 100 Hz to
    5 kHz (5.4.14.2). Either loop may lead: an angle is folded into 0 to 180
    degrees before its distance from 90 degrees is taken, so -90 and 270
    degrees are as much in quadrature as 90.

    :param frequencies_hz: The measurement frequencies, in hertz, ascending,
        at least one of them inside 100 Hz to 5 kHz.
    :param phase_difference_deg: The phase angle between the loop currents at
        each, in degrees.
    :return: A :class:`QuadraturePhaseError`.
    """
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    phase = require_finite_array(phase_difference_deg, "phase_difference_deg")
    if f.size != phase.size:
        msg = "'frequencies_hz' and 'phase_difference_deg' must have the same length."
        raise ValueError(msg)
    _ascending(f, "frequencies_hz")
    wrapped = np.abs((phase + 180.0) % 360.0 - 180.0)
    deviation = np.abs(wrapped - _QUADRATURE_DEG)
    inside = (f >= _SPEECH_BAND_HZ[0]) & (f <= _SPEECH_BAND_HZ[1])
    if not np.any(inside):
        msg = "no measurement frequency lies in 100 Hz to 5 kHz, where 5.4.14.2 states the error."
        raise ValueError(msg)
    indices = np.flatnonzero(inside)
    worst = int(indices[np.argmax(deviation[inside])])
    return QuadraturePhaseError(
        frequencies_hz=f,
        phase_difference_deg=phase,
        deviation_deg=read_only(deviation),
        max_deviation_deg=float(deviation[worst]),
        max_deviation_frequency_hz=float(f[worst]),
    )


# ---------------------------------------------------------------------------
# The neck loop
# ---------------------------------------------------------------------------


def _crossings(f: np.ndarray, response: np.ndarray, level: float) -> tuple[float, ...]:
    """Where a response crosses a level, interpolated against log frequency."""
    found: list[float] = []
    shifted = response - level
    for k in range(f.size - 1):
        y0, y1 = float(shifted[k]), float(shifted[k + 1])
        if (y0 < 0.0) != (y1 < 0.0):
            t = y0 / (y0 - y1)
            found.append(
                float(math.exp(math.log(f[k]) + t * math.log(f[k + 1] / f[k])))
            )
    return tuple(found)


@dataclass(frozen=True)
class NeckLoopCharacteristics(OwnsArrays):
    """What IEC 62489-1:2010+A1:2014 clause 9 states for a neck loop.

    :ivar frequencies_hz: The measurement frequencies, in hertz.
    :ivar field_strength_level_db: The field strength level on the test jig at
        each, in dB re 400 mA/m, with :attr:`input_voltage_v` applied.
    :ivar impedance_ohm: The magnitude of the input impedance at each, in ohms.
    :ivar input_voltage_v: The input voltage the field was measured with, in
        volts.
    :ivar reference_input_voltage_v: The input voltage that produces 400 mA/m
        at 1 kHz at the telecoil position of the jig, the characteristic of
        9.1, in volts.
    :ivar minimum_impedance_ohm: The smallest magnitude of the input
        impedance over 100 Hz to 5 kHz, rounded to the nearest ohm (9.2.1).
    :ivar response_db: The field strength level relative to the one at
        1 kHz, in dB.
    :ivar frequencies_3db_hz: The frequencies where the response differs from
        the one at 1 kHz by 3 dB, which 9.3.3 states when the response is
        given as text.
    """

    frequencies_hz: np.ndarray
    field_strength_level_db: np.ndarray
    impedance_ohm: np.ndarray
    input_voltage_v: float
    reference_input_voltage_v: float
    minimum_impedance_ohm: float
    response_db: np.ndarray
    frequencies_3db_hz: tuple[float, ...]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the frequency response on the jig, 0 dB at 1 kHz.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the response curve's ``Axes.plot``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_neck_loop_characteristics

        check_language(language)
        return plot_neck_loop_characteristics(self, ax, language=language, **kwargs)


def neck_loop_characteristics(
    frequencies_hz: ArrayLike,
    field_strength_level_db: ArrayLike,
    impedance_ohm: ArrayLike,
    *,
    input_voltage_v: float,
) -> NeckLoopCharacteristics:
    r"""The input voltage, input impedance and frequency response of a neck loop.

    The loop is arranged on the non-metallic jig of Annex E and the field
    measured at the telecoil position with a small inductor, about 3 mm by
    10 mm, the size of a behind-the-ear telecoil (9.1.2). The rated input
    voltage is applied from a source of less than 0,4 ohm (9.3.2).

    A passive loop is linear, so the input voltage for 400 mA/m at 1 kHz
    (9.1) follows from the level measured at any voltage:
    :math:`U_{400} = U\,10^{-L/20}`, with :math:`L` the level at 1 kHz in dB
    re 400 mA/m. For an active loop that is not linear, measure at the voltage
    that gives 0 dB, where the scaling does nothing.

    :param frequencies_hz: The measurement frequencies, in hertz, ascending
        and including 1000 Hz.
    :param field_strength_level_db: The field strength level on the jig at
        each, in dB re 400 mA/m.
    :param impedance_ohm: The input impedance at each, in ohms; complex
        values are reduced to their magnitude, and real ones must be
        positive.
    :param input_voltage_v: The input voltage the field was measured with, in
        volts.
    :return: A :class:`NeckLoopCharacteristics`.
    """
    f = require_positive_array(frequencies_hz, "frequencies_hz")
    level = require_finite_array(field_strength_level_db, "field_strength_level_db")
    try:
        complex_input = np.iscomplexobj(impedance_ohm)
    except (TypeError, ValueError) as exc:
        msg = "'impedance_ohm' must be numeric."
        raise ValueError(msg) from exc
    z = require_positive_array(
        np.abs(np.asarray(impedance_ohm)) if complex_input else impedance_ohm,
        "impedance_ohm",
    )
    if not f.size == level.size == z.size:
        msg = (
            "'frequencies_hz', 'field_strength_level_db' and 'impedance_ohm' "
            "must have the same length."
        )
        raise ValueError(msg)
    _ascending(f, "frequencies_hz")
    voltage = require_positive(input_voltage_v, "input_voltage_v")
    ref = _reference_index(f, "frequencies_hz")
    inside = (f >= _SPEECH_BAND_HZ[0]) & (f <= _SPEECH_BAND_HZ[1])
    minimum = float(np.min(z[inside]))
    response = level - level[ref]
    crossings = _crossings(f, response, -_NECK_LOOP_RESPONSE_STEP_DB) + _crossings(
        f, response, _NECK_LOOP_RESPONSE_STEP_DB
    )
    return NeckLoopCharacteristics(
        frequencies_hz=f,
        field_strength_level_db=level,
        impedance_ohm=z,
        input_voltage_v=voltage,
        reference_input_voltage_v=voltage * 10.0 ** (-float(level[ref]) / 20.0),
        minimum_impedance_ohm=float(math.floor(minimum + 0.5)),
        response_db=read_only(response),
        frequencies_3db_hz=tuple(sorted(crossings)),
    )


@dataclass(frozen=True)
class NeckLoopType(RichDisplay):
    """One neck-loop type of the draft Annex D (prEN 62489-1:2010/prA2:2017).

    :ivar description: What the type is, as the draft describes it.
    :ivar min_dc_resistance_ohm: The smallest DC input resistance, in ohms.
    :ivar max_dc_resistance_ohm: The largest, in ohms; infinite when the draft
        sets only a floor.
    :ivar max_input_voltage_v: The input voltage within which the loop reaches
        400 mA/m on the jig of Annex E, in volts.
    """

    description: str
    min_dc_resistance_ohm: float
    max_dc_resistance_ohm: float
    max_input_voltage_v: float


#: The two neck-loop types of the draft Amendment 2, D.1.2 and D.1.3
#: (prEN 62489-1:2010/prA2:2017, a draft; read in E DIN EN 62489-1/A2:2017-10):
#: type 1, for sources of two primary 1,5 V cells and higher voltage supplies,
#: of 32 ohm plus or minus 5 % DC resistance, and type 2, a neck loop with a
#: transformer or an amplifier, of at least 32 ohm. Both reach 400 mA/m on the
#: jig with at most 1,06 V at the input.
NECK_LOOP_TYPES: Mapping[int, NeckLoopType] = MappingProxyType(
    {
        1: NeckLoopType(
            description=(
                "for audio sources powered by two primary 1.5 V cells and "
                "higher voltage supplies"
            ),
            min_dc_resistance_ohm=32.0 * 0.95,
            max_dc_resistance_ohm=32.0 * 1.05,
            max_input_voltage_v=1.06,
        ),
        2: NeckLoopType(
            description="neck loop with a transformer or an amplifier",
            min_dc_resistance_ohm=32.0,
            max_dc_resistance_ohm=math.inf,
            max_input_voltage_v=1.06,
        ),
    }
)


@dataclass(frozen=True)
class NeckLoopVerification(RichDisplay):
    """A neck loop judged against one type of the draft Annex D (prA2:2017).

    :ivar neck_loop_type: The type it was judged as, 1 or 2.
    :ivar dc_resistance_ohm: The measured DC input resistance, in ohms.
    :ivar input_voltage_v: The input voltage that produces 400 mA/m on the
        jig, in volts.

    The limits of the type (:attr:`limits`) are read from
    :data:`NECK_LOOP_TYPES`, so a verification cannot be built against other
    limits.
    """

    neck_loop_type: int
    dc_resistance_ohm: float
    input_voltage_v: float

    def __post_init__(self) -> None:
        """Reject a type the draft Annex D does not define.

        :raises ValueError: if ``neck_loop_type`` is not 1 or 2.
        """
        if self.neck_loop_type not in NECK_LOOP_TYPES:
            msg = (
                f"'neck_loop_type' must be one of {tuple(NECK_LOOP_TYPES)}; "
                f"got {self.neck_loop_type!r}."
            )
            raise ValueError(msg)

    @property
    def limits(self) -> NeckLoopType:
        """The :class:`NeckLoopType` judged against."""
        return NECK_LOOP_TYPES[self.neck_loop_type]

    @property
    def resistance_passes(self) -> bool:
        """Whether the DC resistance is inside the type's range."""
        return (
            self.limits.min_dc_resistance_ohm
            <= self.dc_resistance_ohm
            <= self.limits.max_dc_resistance_ohm
        )

    @property
    def voltage_passes(self) -> bool:
        """Whether 400 mA/m is reached within the type's input voltage."""
        return self.input_voltage_v <= self.limits.max_input_voltage_v

    @property
    def passes(self) -> bool:
        """Whether the loop meets both limits of its type."""
        return self.resistance_passes and self.voltage_passes

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a NeckLoopVerification has no truth value; read its '.passes' for the verdict"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each measured value as a share of its limit.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars' ``Axes.bar``.
        """
        from .._i18n import check_language
        from .._plot.induction_loop import plot_neck_loop_verification

        check_language(language)
        return plot_neck_loop_verification(self, ax, language=language, **kwargs)


def verify_neck_loop(
    dc_resistance_ohm: float, input_voltage_v: float, *, neck_loop_type: int = 1
) -> NeckLoopVerification:
    """Does a neck loop meet one type of the draft Annex D (prA2:2017)?

    The draft Amendment 2 to IEC 62489-1 (prEN 62489-1:2010/prA2:2017, read in
    E DIN EN 62489-1/A2:2017-10) specifies a type 1 neck loop, for audio
    sources powered by two primary 1,5 V cells and higher voltage supplies, by
    a DC resistance of 32 ohm plus or minus 5 % and a type 2 neck loop with a
    transformer or an amplifier by an input DC resistance of at least 32 ohm,
    both reaching 400 mA/m on the jig of Annex E with at most 1,06 V at the
    input (:data:`NECK_LOOP_TYPES`). It is a draft, cited as one.

    :param dc_resistance_ohm: The measured DC input resistance, in ohms.
    :param input_voltage_v: The input voltage that produces 400 mA/m on the
        jig, in volts (:attr:`NeckLoopCharacteristics.reference_input_voltage_v`).
    :param neck_loop_type: 1 or 2.
    :return: A :class:`NeckLoopVerification`.
    """
    resistance = require_positive(dc_resistance_ohm, "dc_resistance_ohm")
    voltage = require_positive(input_voltage_v, "input_voltage_v")
    msg = f"'neck_loop_type' must be one of {tuple(NECK_LOOP_TYPES)}; got {neck_loop_type!r}."
    try:
        kind = require_count(neck_loop_type, "neck_loop_type")
    except ValueError:
        raise ValueError(msg) from None
    if kind not in NECK_LOOP_TYPES:
        raise ValueError(msg)
    return NeckLoopVerification(
        neck_loop_type=kind,
        dc_resistance_ohm=resistance,
        input_voltage_v=voltage,
    )

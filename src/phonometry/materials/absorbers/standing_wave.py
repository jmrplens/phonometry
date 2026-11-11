#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Standing-wave-ratio method for normal-incidence absorption and impedance.

**BS EN ISO 10534-1:2001**, the probe-traverse method of the impedance tube: a
loudspeaker drives one pure tone at a time, a probe microphone traverses the
tube and reads the maximum and minimum sound pressure levels of the standing
wave the specimen sets up, and the position of the first pressure minimum
fixes the phase. The reflection magnitude, phase, absorption coefficient and
normalised impedance follow from those two readings alone (Clause 5,
Eqs. (12)-(26)).

That is the whole method, and it is why it is one module: it consumes a
standing-wave ratio and a distance, and needs neither a measured transfer
function nor the complex wavenumber and air properties every broadband
reduction in the tube goes through. The quantities are the same
normal-incidence quantities the two-microphone method reports
(:math:`\alpha = 1 - \lvert r\rvert^2` is Eq. (9) here and Eq. (18) there),
measured one frequency at a time; see
:mod:`~phonometry.materials.absorbers.impedance_tube`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

import numpy as np
from numpy.typing import NDArray

from ..._internal.types import as_complex_or_array, as_float_or_array
from ..._internal.validation import real_array

if TYPE_CHECKING:
    from ..._internal.types import NumericArrayLike, RealScalar, RealValues

Complex = NDArray[np.complex128]

__all__ = [
    "standing_wave_absorption",
    "standing_wave_normalized_impedance",
    "standing_wave_ratio_from_level",
    "standing_wave_reflection",
    "standing_wave_reflection_magnitude",
]


@overload
def standing_wave_ratio_from_level[S: RealScalar](level_difference: S) -> float: ...


@overload
def standing_wave_ratio_from_level[V: RealValues](
    level_difference: V,
) -> NDArray[np.float64]: ...


@overload
def standing_wave_ratio_from_level[A: NumericArrayLike](
    level_difference: A,
) -> float | NDArray[np.float64]: ...


def standing_wave_ratio_from_level(
    level_difference: NumericArrayLike,
) -> float | NDArray[np.float64]:
    r"""Standing-wave ratio from a level difference (ISO 10534-1, Eq. (15)).

    :math:`s = 10^{\Delta L / 20}` with
    :math:`\Delta L = L_{\max} - L_{\min}` in decibels.

    :param level_difference: Level difference
        :math:`\Delta L = L_{\max} - L_{\min}`, in dB.
    :return: Standing-wave ratio ``s`` (>= 1). A ``float`` for a number, an array for a
        sequence or an array, a zero-dimensional one included.
    :raises TypeError: if ``level_difference`` holds a text or a value that is not a
        real number.
    """
    dl = real_array(level_difference, "level_difference")
    if np.any(dl < 0.0):
        msg = "'level_difference' must be non-negative."
        raise ValueError(msg)
    return as_float_or_array(10.0 ** (dl / 20.0), like=(level_difference,))


def _check_swr(swr: NDArray[np.float64]) -> None:
    if np.any(swr < 1.0):
        msg = "Standing-wave ratio 's' must be >= 1."
        raise ValueError(msg)


@overload
def standing_wave_reflection_magnitude[S: RealScalar](swr: S) -> float: ...


@overload
def standing_wave_reflection_magnitude[V: RealValues](
    swr: V,
) -> NDArray[np.float64]: ...


@overload
def standing_wave_reflection_magnitude[A: NumericArrayLike](
    swr: A,
) -> float | NDArray[np.float64]: ...


def standing_wave_reflection_magnitude(
    swr: NumericArrayLike,
) -> float | NDArray[np.float64]:
    r"""Reflection magnitude from the standing-wave ratio (ISO 10534-1, Eq. (14)).

    :math:`|r| = (s - 1) / (s + 1)`.

    :param swr: Standing-wave ratio ``s`` (>= 1).
    :return: Reflection magnitude ``|r|`` in ``[0, 1]``. A ``float`` for a number, an
        array for a sequence or an array, a zero-dimensional one included.
    :raises TypeError: if ``swr`` holds a text or a value that is not a real number.
    """
    s = real_array(swr, "swr")
    _check_swr(s)
    return as_float_or_array((s - 1.0) / (s + 1.0), like=(swr,))


@overload
def standing_wave_absorption[S: RealScalar](swr: S) -> float: ...


@overload
def standing_wave_absorption[V: RealValues](swr: V) -> NDArray[np.float64]: ...


@overload
def standing_wave_absorption[A: NumericArrayLike](
    swr: A,
) -> float | NDArray[np.float64]: ...


def standing_wave_absorption(swr: NumericArrayLike) -> float | NDArray[np.float64]:
    r"""Absorption coefficient from the standing-wave ratio (ISO 10534-1).

    Combining :math:`\alpha = 1 - |r|^2` (Eq. (9)) with
    :math:`|r| = (s - 1)/(s + 1)` (Eq. (14)) gives
    :math:`\alpha = 4s/(s + 1)^2`.

    :param swr: Standing-wave ratio ``s`` (>= 1).
    :return: Absorption coefficient ``alpha`` in ``[0, 1]``. A ``float`` for a number,
        an array for a sequence or an array, a zero-dimensional one included.
    :raises TypeError: if ``swr`` holds a text or a value that is not a real number.
    """
    s = real_array(swr, "swr")
    _check_swr(s)
    return as_float_or_array(4.0 * s / (s + 1.0) ** 2, like=(swr,))


def _standing_wave_phase(
    first_min_distance: NDArray[np.float64], wavelength: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Reflection phase from the first minimum (ISO 10534-1, Eq. (20))."""
    if np.any(wavelength <= 0.0):
        msg = "'wavelength' must be positive."
        raise ValueError(msg)
    if np.any(first_min_distance < 0.0):
        msg = "'first_min_distance' must be non-negative."
        raise ValueError(msg)
    return np.asarray(
        np.pi * (4.0 * first_min_distance / wavelength - 1.0), dtype=np.float64
    )


@overload
def standing_wave_reflection[S1: RealScalar, S2: RealScalar, S3: RealScalar](
    swr: S1,
    first_min_distance: S2,
    *,
    wavelength: S3,
) -> complex: ...


@overload
def standing_wave_reflection[V: RealValues, A2: NumericArrayLike, A3: NumericArrayLike](
    swr: V,
    first_min_distance: A2,
    *,
    wavelength: A3,
) -> NDArray[np.complex128]: ...


@overload
def standing_wave_reflection[S1: RealScalar, V: RealValues, A3: NumericArrayLike](
    swr: S1,
    first_min_distance: V,
    *,
    wavelength: A3,
) -> NDArray[np.complex128]: ...


@overload
def standing_wave_reflection[S1: RealScalar, S2: RealScalar, V: RealValues](
    swr: S1,
    first_min_distance: S2,
    *,
    wavelength: V,
) -> NDArray[np.complex128]: ...


@overload
def standing_wave_reflection[
    A1: NumericArrayLike,
    A2: NumericArrayLike,
    A3: NumericArrayLike,
](
    swr: A1,
    first_min_distance: A2,
    *,
    wavelength: A3,
) -> complex | NDArray[np.complex128]: ...


def standing_wave_reflection(
    swr: NumericArrayLike,
    first_min_distance: NumericArrayLike,
    *,
    wavelength: NumericArrayLike,
) -> complex | NDArray[np.complex128]:
    r"""Complex reflection factor from the standing wave (ISO 10534-1, Eqs. (17)-(23)).

    :math:`r = |r| \mathrm{e}^{j\phi}` with :math:`|r| = (s - 1)/(s + 1)` (Eq. (14))
    and the phase at the first pressure minimum
    :math:`\phi = \pi (4 x_{\text{min},1} / \lambda_0 - 1)` (Eq. (20)).

    :param swr: Standing-wave ratio ``s`` (>= 1).
    :param first_min_distance: Distance ``x_min1`` from the reference plane to
        the first pressure minimum (toward the source), in metres.
    :param wavelength: Wavelength ``lambda0``, in metres (Eq. (27)).
    :return: Complex reflection factor ``r``. A ``complex`` when ``swr``,
        ``first_min_distance`` and ``wavelength`` are all numbers, an array when one of
        them is a sequence or an array, a zero-dimensional one included.
    :raises TypeError: if ``first_min_distance`` or ``wavelength`` holds a text or a
        value that is not a real number.
    """
    magnitude = standing_wave_reflection_magnitude(swr)
    phase = _standing_wave_phase(
        real_array(first_min_distance, "first_min_distance"),
        real_array(wavelength, "wavelength"),
    )
    return as_complex_or_array(
        magnitude * np.exp(1j * phase), like=(swr, first_min_distance, wavelength)
    )


@overload
def standing_wave_normalized_impedance[S1: RealScalar, S2: RealScalar, S3: RealScalar](
    swr: S1,
    first_min_distance: S2,
    *,
    wavelength: S3,
) -> complex: ...


@overload
def standing_wave_normalized_impedance[
    V: RealValues,
    A2: NumericArrayLike,
    A3: NumericArrayLike,
](
    swr: V,
    first_min_distance: A2,
    *,
    wavelength: A3,
) -> NDArray[np.complex128]: ...


@overload
def standing_wave_normalized_impedance[
    S1: RealScalar,
    V: RealValues,
    A3: NumericArrayLike,
](
    swr: S1,
    first_min_distance: V,
    *,
    wavelength: A3,
) -> NDArray[np.complex128]: ...


@overload
def standing_wave_normalized_impedance[S1: RealScalar, S2: RealScalar, V: RealValues](
    swr: S1,
    first_min_distance: S2,
    *,
    wavelength: V,
) -> NDArray[np.complex128]: ...


@overload
def standing_wave_normalized_impedance[
    A1: NumericArrayLike,
    A2: NumericArrayLike,
    A3: NumericArrayLike,
](
    swr: A1,
    first_min_distance: A2,
    *,
    wavelength: A3,
) -> complex | NDArray[np.complex128]: ...


def standing_wave_normalized_impedance(
    swr: NumericArrayLike,
    first_min_distance: NumericArrayLike,
    *,
    wavelength: NumericArrayLike,
) -> complex | NDArray[np.complex128]:
    r"""Normalised impedance from the standing wave (ISO 10534-1, Eqs. (24)-(26)).

    :math:`z = Z/Z_0 = (1 + r)/(1 - r)`, split into real and imaginary parts
    by Eqs. (25)/(26). With :math:`|r| = (s - 1)/(s + 1)` (Eq. (14)) and the
    phase of Eq. (20) put in for :math:`r' = |r| \cos\phi` and
    :math:`r'' = |r| \sin\phi` (Eqs. (22), (23)), the two parts read

    .. math::

        z' = \frac{s}{D}, \qquad
        z'' = \frac{(s^2 - 1)\sin(\phi/2)\cos(\phi/2)}{D}, \qquad
        D = 1 + (s^2 - 1)\sin^2(\phi/2),

    which is how they are computed: the same numbers, with no
    :math:`1 - r'` to cancel. That difference keeps only the digits
    :math:`1 - |r| = 2/(s + 1)` leaves it, and none once :math:`|r|` rounds
    to 1, past :math:`s \approx 10^{16}`; a first minimum a quarter
    wavelength from the face (:math:`\phi = 0`) then gives :math:`z = s`
    exactly.

    :param swr: Standing-wave ratio ``s`` (>= 1).
    :param first_min_distance: Distance ``x_min1`` to the first minimum, in metres.
    :param wavelength: Wavelength ``lambda0``, in metres.
    :return: Normalised surface impedance ``z`` (complex). A ``complex`` when ``swr``,
        ``first_min_distance`` and ``wavelength`` are all numbers, an array when one of
        them is a sequence or an array, a zero-dimensional one included.
    """
    s = real_array(swr, "swr")
    _check_swr(s)
    phase = _standing_wave_phase(
        real_array(first_min_distance, "first_min_distance"),
        real_array(wavelength, "wavelength"),
    )
    half_sin = np.sin(phase / 2.0)
    half_cos = np.cos(phase / 2.0)
    # Every term over w**2, w = 1 + (s + 1)|sin(phi/2)|, so that no product
    # overflows for a ratio whose square does: (s - 1) sin(phi/2) / w and
    # (s + 1) sin(phi/2) / w stay within 1, and (1 / w)**2 keeps D positive.
    w = 1.0 + (s + 1.0) * np.abs(half_sin)
    lower = (s - 1.0) * half_sin / w
    upper = (s + 1.0) * half_sin / w
    d = (1.0 / w) * (1.0 / w) + lower * upper
    resistance = s / w / w / d
    reactance = lower * ((s + 1.0) / w) * half_cos / d
    return as_complex_or_array(
        resistance + 1j * reactance, like=(swr, first_min_distance, wavelength)
    )

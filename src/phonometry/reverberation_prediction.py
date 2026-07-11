#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Reverberation-time prediction from room geometry and absorption.

Predicts the reverberation time ``T`` of an enclosed space from its volume,
boundary areas and the sound-absorption coefficients of its surfaces, through
the classical statistical-acoustics formulae. Given a diffuse field and an
exponential energy decay, ``T`` is the time for the level to fall by 60 dB.

Five models are provided, in order of increasing account of a non-uniform
absorption distribution:

* **Sabine** -- the original diffuse-field estimate, ``T = k V / (A + 4 m V)``
  with the total equivalent absorption area ``A = sum_i S_i alpha_i`` and the
  air term ``4 m V``. Exact only for low, uniform absorption.
* **Eyring** (Norris-Eyring) -- replaces ``A`` by ``-S ln(1 - alpha_bar)`` with
  the mean absorption ``alpha_bar = A / S`` over the total surface ``S``;
  correct in the strong-absorption limit where Sabine overestimates ``T``.
* **Millington-Sette** -- ``-sum_i S_i ln(1 - alpha_i)`` sums the Eyring term
  per surface, so a single perfectly absorbing surface drives ``T`` to zero.
* **Fitzroy** -- an *area-weighted arithmetic* mean of three axial Eyring
  reverberation times, one per pair of opposing walls; captures rooms with the
  absorption concentrated on one axis (e.g. a carpeted, otherwise hard room).
* **Arau-Puchades** -- an *area-weighted geometric* mean of the same three axial
  Eyring times (Arau-Puchades, *Acustica* 65 (1988) 163): ``T = prod_i T_i **
  (S_i / S)``. Recommended by its author over Fitzroy for anisotropic rooms.

The Sabine constant is ``k = 24 ln 10 / c0`` (``= 55.26 / c0``); with the
default ``c0 = 343 m/s`` it takes the familiar textbook value ``0.161``. (The
:mod:`~phonometry.enclosed_space_absorption` EN 12354-6 model instead rounds
``k`` to ``55.3`` and uses ``c0 = 345.6`` to pin the factor at exactly ``0.16``.)

Air absorption enters every model through the ``air_attenuation`` power
coefficient ``m`` (in neper per metre) as the additive term ``4 m V``; obtain a
physical ``m`` from temperature and humidity with
:func:`phonometry.air_absorption.air_attenuation_m`.

The Fitzroy and Arau-Puchades models require a rectangular (shoebox) room and
take the room ``dimensions`` together with the mean absorption of each of the
three wall pairs. All five reduce to Eyring for a uniform absorption
distribution, and Eyring reduces to Sabine as the absorption tends to zero --
the identities the conformance suite anchors on, absent a machine-readable
worked example in the source texts.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import log
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike, NDArray

from ._types import as_float_or_array
from ._validation import require_non_negative, require_positive

# ---------------------------------------------------------------------------
# Constants.
# ---------------------------------------------------------------------------

#: Sabine numerator ``24 ln 10 = 55.26...`` (the ``0.161`` constant with
#: ``c0 = 343 m/s``). ``T = 24 ln 10 / c0 * V / A``.
_SABINE_NUMERATOR = 24.0 * log(10.0)

#: Default speed of sound ``c0`` (20 degC dry air), in m/s, giving ``k = 0.161``.
DEFAULT_SPEED_OF_SOUND = 343.0

#: Absorption-coefficient ceiling for the Eyring-family logarithm ``ln(1 -
#: alpha)``; a mean absorption at or above this triggers a clear error rather
#: than a silent ``-inf``/``nan``. A fully absorbing surface (``alpha = 1``) has
#: no finite Eyring reverberation time.
_MAX_MEAN_ABSORPTION = 1.0


Surface = tuple[float, ArrayLike]


# ---------------------------------------------------------------------------
# Surface bookkeeping.
# ---------------------------------------------------------------------------


def _broadcast_or_raise(
    shapes: Sequence[tuple[int, ...]], name: str
) -> tuple[int, ...]:
    """Common broadcast shape of *shapes*, or a clear error naming the mismatch.

    Turns NumPy's terse "operands could not be broadcast" into the library's
    usual descriptive :class:`ValueError` for a per-band count mismatch.
    """
    try:
        return np.broadcast_shapes(*shapes)
    except ValueError:
        raise ValueError(
            f"the per-band {name} have incompatible shapes "
            f"{[tuple(s) for s in shapes]}; each must be a scalar or share a "
            "common band count."
        ) from None


def _accumulate_surfaces(
    surfaces: Sequence[Surface],
) -> tuple[float, NDArray[np.float64], NDArray[np.float64]]:
    """Total area ``S``, total absorption area ``A`` and Millington sum.

    Returns ``(S, A, M)`` where ``A = sum_i S_i alpha_i`` and
    ``M = -sum_i S_i ln(1 - alpha_i)``; ``A`` and ``M`` are per-band arrays
    (0-d for scalar coefficients).

    :raises ValueError: for an empty surface list, a negative area, a
        coefficient outside ``[0, 1)`` (``1`` gives a divergent Millington sum),
        or per-band coefficients whose band counts do not broadcast together.
    """
    if not surfaces:
        raise ValueError("at least one surface is required.")
    areas: list[float] = []
    alphas: list[NDArray[np.float64]] = []
    for area, alpha in surfaces:
        areas.append(require_non_negative(area, "surface area"))
        alpha_arr = np.asarray(alpha, dtype=np.float64)
        if np.any(alpha_arr < 0.0) or np.any(alpha_arr >= 1.0):
            raise ValueError("absorption coefficients must be in the range [0, 1).")
        alphas.append(alpha_arr)
    shape = _broadcast_or_raise(
        [a.shape for a in alphas], "surface absorption coefficients"
    )
    total_area = float(sum(areas))
    if total_area <= 0.0:
        raise ValueError("the total surface area must be positive.")
    absorption_area = np.zeros(shape, dtype=np.float64)
    millington = np.zeros(shape, dtype=np.float64)
    for area, alpha_arr in zip(areas, alphas):
        absorption_area = absorption_area + area * alpha_arr
        millington = millington - area * np.log1p(-alpha_arr)
    return total_area, absorption_area, millington


def _air_term(air_attenuation: ArrayLike, volume: float) -> NDArray[np.float64]:
    """Air absorption area ``4 m V`` (m2), validated non-negative."""
    m = np.asarray(air_attenuation, dtype=np.float64)
    if np.any(m < 0.0):
        raise ValueError("'air_attenuation' must be non-negative.")
    return np.asarray(4.0 * m * volume, dtype=np.float64)


def _add_air(
    absorption_term: NDArray[np.float64], air_attenuation: ArrayLike, volume: float
) -> NDArray[np.float64]:
    """Add the air term ``4 m V`` to an absorption term, band counts checked."""
    air = _air_term(air_attenuation, volume)
    _broadcast_or_raise(
        [absorption_term.shape, air.shape], "absorption and air attenuation"
    )
    return np.asarray(absorption_term + air, dtype=np.float64)


def _eyring_absorption(total_area: float, mean_absorption: NDArray[np.float64]) -> NDArray[np.float64]:
    """Eyring equivalent absorption ``-S ln(1 - alpha_bar)`` (per band)."""
    if np.any(mean_absorption >= _MAX_MEAN_ABSORPTION):
        raise ValueError(
            "the mean absorption coefficient must be below 1; a fully absorbing "
            "room has no finite Eyring reverberation time."
        )
    return np.asarray(-total_area * np.log1p(-mean_absorption), dtype=np.float64)


def _reverberation_time(
    volume: float, absorption: NDArray[np.float64], speed_of_sound: float
) -> np.ndarray | float:
    """``T = 24 ln 10 / c0 * V / absorption``, with a positive-absorption guard."""
    if np.any(absorption <= 0.0):
        raise ValueError(
            "the total absorption is non-positive; a perfectly reflecting room "
            "has no finite reverberation time."
        )
    t = _SABINE_NUMERATOR / speed_of_sound * volume / absorption
    return as_float_or_array(t)


def mean_absorption(surfaces: Sequence[Surface]) -> np.ndarray | float:
    """Area-weighted mean absorption coefficient ``alpha_bar = A / S``.

    :param surfaces: Sequence of ``(area, absorption_coefficient)`` pairs; each
        coefficient a scalar or a per-band array.
    :return: The mean absorption ``sum_i S_i alpha_i / sum_i S_i``; a float for
        scalar coefficients, otherwise a per-band array.
    """
    total_area, absorption_area, _ = _accumulate_surfaces(surfaces)
    return as_float_or_array(absorption_area / total_area)


# ---------------------------------------------------------------------------
# Statistical models over an arbitrary surface list.
# ---------------------------------------------------------------------------


def sabine_reverberation_time(
    volume: float,
    surfaces: Sequence[Surface],
    *,
    air_attenuation: ArrayLike = 0.0,
    speed_of_sound: float = DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray | float:
    """Sabine reverberation time ``T = k V / (A + 4 m V)``.

    :param volume: Room volume ``V``, m3.
    :param surfaces: Sequence of ``(area, absorption_coefficient)`` pairs; each
        coefficient a scalar or a per-band array.
    :param air_attenuation: Air power-attenuation coefficient ``m``, in neper
        per metre (scalar or per-band); see
        :func:`phonometry.air_absorption.air_attenuation_m`. Default ``0``
        (air absorption neglected).
    :param speed_of_sound: Speed of sound ``c0``, m/s (default
        :data:`DEFAULT_SPEED_OF_SOUND`, giving the factor ``0.161``).
    :return: The reverberation time ``T``, s; a float for scalar inputs,
        otherwise a per-band array.
    """
    volume = require_positive(volume, "volume")
    speed_of_sound = require_positive(speed_of_sound, "speed_of_sound")
    _, absorption_area, _ = _accumulate_surfaces(surfaces)
    absorption = _add_air(absorption_area, air_attenuation, volume)
    return _reverberation_time(volume, absorption, speed_of_sound)


def eyring_reverberation_time(
    volume: float,
    surfaces: Sequence[Surface],
    *,
    air_attenuation: ArrayLike = 0.0,
    speed_of_sound: float = DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray | float:
    """Eyring (Norris-Eyring) reverberation time.

    ``T = k V / (-S ln(1 - alpha_bar) + 4 m V)`` with the total surface ``S``
    and its area-weighted mean absorption ``alpha_bar``.

    :param volume: Room volume ``V``, m3.
    :param surfaces: Sequence of ``(area, absorption_coefficient)`` pairs.
    :param air_attenuation: Air power-attenuation coefficient ``m`` (1/m).
    :param speed_of_sound: Speed of sound ``c0``, m/s.
    :return: The reverberation time ``T``, s.
    """
    volume = require_positive(volume, "volume")
    speed_of_sound = require_positive(speed_of_sound, "speed_of_sound")
    total_area, absorption_area, _ = _accumulate_surfaces(surfaces)
    mean = absorption_area / total_area
    absorption = _add_air(_eyring_absorption(total_area, mean), air_attenuation, volume)
    return _reverberation_time(volume, absorption, speed_of_sound)


def millington_sette_reverberation_time(
    volume: float,
    surfaces: Sequence[Surface],
    *,
    air_attenuation: ArrayLike = 0.0,
    speed_of_sound: float = DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray | float:
    """Millington-Sette reverberation time.

    ``T = k V / (-sum_i S_i ln(1 - alpha_i) + 4 m V)``: the Eyring absorption
    term summed surface by surface rather than through a single mean. A surface
    approaching total absorption (``alpha_i -> 1``) drives ``T`` to zero.

    :param volume: Room volume ``V``, m3.
    :param surfaces: Sequence of ``(area, absorption_coefficient)`` pairs.
    :param air_attenuation: Air power-attenuation coefficient ``m`` (1/m).
    :param speed_of_sound: Speed of sound ``c0``, m/s.
    :return: The reverberation time ``T``, s.
    """
    volume = require_positive(volume, "volume")
    speed_of_sound = require_positive(speed_of_sound, "speed_of_sound")
    _, _, millington = _accumulate_surfaces(surfaces)
    absorption = _add_air(millington, air_attenuation, volume)
    return _reverberation_time(volume, absorption, speed_of_sound)


# ---------------------------------------------------------------------------
# Axial models for a rectangular room (Fitzroy, Arau-Puchades).
# ---------------------------------------------------------------------------


def _axial_geometry(dimensions: Sequence[float]) -> tuple[float, float, NDArray[np.float64]]:
    """Volume ``V``, total surface ``S`` and the three wall-pair areas ``S_i``.

    ``S_i`` is the combined area of the two walls perpendicular to axis ``i``:
    ``S_x = 2 L_y L_z``, ``S_y = 2 L_x L_z``, ``S_z = 2 L_x L_y``.
    """
    if len(dimensions) != 3:
        raise ValueError("'dimensions' must be the three room lengths (Lx, Ly, Lz).")
    lx, ly, lz = (require_positive(float(d), "dimension") for d in dimensions)
    volume = lx * ly * lz
    pair_areas = np.array([2.0 * ly * lz, 2.0 * lx * lz, 2.0 * lx * ly], dtype=np.float64)
    total_area = float(pair_areas.sum())
    return volume, total_area, pair_areas


def _axial_eyring_times(
    dimensions: Sequence[float],
    absorptions: Sequence[ArrayLike],
    air_attenuation: ArrayLike,
    speed_of_sound: float,
) -> tuple[NDArray[np.float64], list[np.ndarray | float]]:
    """Per-axis Eyring reverberation times and their area weights ``S_i / S``.

    Each axial time uses the *whole* room surface ``S`` and the mean absorption
    ``alpha_bar_i`` of the wall pair perpendicular to that axis (Arau-Puchades'
    construction), plus the shared air term ``4 m V``.
    """
    if len(absorptions) != 3:
        raise ValueError(
            "'absorptions' must give the mean absorption of the three wall pairs "
            "(perpendicular to x, y and z)."
        )
    volume, total_area, pair_areas = _axial_geometry(dimensions)
    speed_of_sound = require_positive(speed_of_sound, "speed_of_sound")
    air = _air_term(air_attenuation, volume)
    means: list[NDArray[np.float64]] = []
    for alpha in absorptions:
        mean = np.asarray(alpha, dtype=np.float64)
        if np.any(mean < 0.0) or np.any(mean >= 1.0):
            raise ValueError("absorption coefficients must be in the range [0, 1).")
        means.append(mean)
    # The three axial times are combined (arithmetic/geometric mean), so their
    # band counts -- and the shared air term -- must broadcast together.
    _broadcast_or_raise(
        [m.shape for m in means] + [air.shape], "axis absorptions and air attenuation"
    )
    times: list[np.ndarray | float] = []
    for mean in means:
        absorption = _eyring_absorption(total_area, mean) + air
        times.append(_reverberation_time(volume, absorption, speed_of_sound))
    weights = pair_areas / total_area
    return weights, times


def fitzroy_reverberation_time(
    dimensions: Sequence[float],
    absorptions: Sequence[ArrayLike],
    *,
    air_attenuation: ArrayLike = 0.0,
    speed_of_sound: float = DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray | float:
    """Fitzroy reverberation time -- area-weighted arithmetic mean of axial times.

    ``T = sum_i (S_i / S) T_i`` with ``T_i`` the Eyring time of the wall pair
    perpendicular to axis ``i`` (Fitzroy, *J. Acoust. Soc. Am.* 31 (1959) 893).
    Equivalent to ``T = k V / S**2 * sum_i S_i / (-ln(1 - alpha_i))`` without
    air. Reduces to Eyring for a uniform absorption distribution.

    :param dimensions: Room lengths ``(Lx, Ly, Lz)``, m.
    :param absorptions: Mean absorption ``(alpha_x, alpha_y, alpha_z)`` of the
        three wall pairs (perpendicular to x, y, z); each a scalar or per-band
        array.
    :param air_attenuation: Air power-attenuation coefficient ``m`` (1/m).
    :param speed_of_sound: Speed of sound ``c0``, m/s.
    :return: The reverberation time ``T``, s.
    """
    weights, times = _axial_eyring_times(
        dimensions, absorptions, air_attenuation, speed_of_sound
    )
    total = sum(w * np.asarray(t, dtype=np.float64) for w, t in zip(weights, times))
    return as_float_or_array(total)


def arau_puchades_reverberation_time(
    dimensions: Sequence[float],
    absorptions: Sequence[ArrayLike],
    *,
    air_attenuation: ArrayLike = 0.0,
    speed_of_sound: float = DEFAULT_SPEED_OF_SOUND,
) -> np.ndarray | float:
    """Arau-Puchades reverberation time -- area-weighted geometric mean of axial times.

    ``T = prod_i T_i ** (S_i / S)`` with ``T_i`` the Eyring time of the wall
    pair perpendicular to axis ``i`` (Arau-Puchades, *Acustica* 65 (1988) 163,
    Formula 18). Preferred by its author over Fitzroy for rooms with an
    anisotropic absorption distribution. Reduces to Eyring for a uniform
    distribution.

    :param dimensions: Room lengths ``(Lx, Ly, Lz)``, m.
    :param absorptions: Mean absorption ``(alpha_x, alpha_y, alpha_z)`` of the
        three wall pairs (perpendicular to x, y, z); each a scalar or per-band
        array.
    :param air_attenuation: Air power-attenuation coefficient ``m`` (1/m).
    :param speed_of_sound: Speed of sound ``c0``, m/s.
    :return: The reverberation time ``T``, s.
    """
    weights, times = _axial_eyring_times(
        dimensions, absorptions, air_attenuation, speed_of_sound
    )
    log_t = sum(w * np.log(np.asarray(t, dtype=np.float64)) for w, t in zip(weights, times))
    return as_float_or_array(np.exp(log_t))


# ---------------------------------------------------------------------------
# Bundled model comparison for a rectangular room.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReverberationModelResult:
    """Predicted reverberation time of a rectangular room by five models.

    :ivar frequencies: Band centre frequencies, in hertz.
    :ivar sabine: Sabine reverberation time per band, s.
    :ivar eyring: Eyring (Norris-Eyring) reverberation time per band, s.
    :ivar millington_sette: Millington-Sette reverberation time per band, s.
    :ivar fitzroy: Fitzroy reverberation time per band, s.
    :ivar arau_puchades: Arau-Puchades reverberation time per band, s.
    :ivar volume: Room volume ``V``, m3.
    :ivar surface_area: Total boundary area ``S``, m2.
    """

    frequencies: np.ndarray
    sabine: np.ndarray
    eyring: np.ndarray
    millington_sette: np.ndarray
    fitzroy: np.ndarray
    arau_puchades: np.ndarray
    volume: float
    surface_area: float

    @property
    def models(self) -> dict[str, np.ndarray]:
        """The five reverberation-time curves keyed by model name."""
        return {
            "Sabine": self.sabine,
            "Eyring": self.eyring,
            "Millington-Sette": self.millington_sette,
            "Fitzroy": self.fitzroy,
            "Arau-Puchades": self.arau_puchades,
        }

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the reverberation-time curves of the five models.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_reverberation_models

        return plot_reverberation_models(self, ax=ax, **kwargs)


def reverberation_time_models(
    dimensions: Sequence[float],
    absorptions: Sequence[ArrayLike],
    *,
    air_attenuation: ArrayLike = 0.0,
    frequencies: ArrayLike | None = None,
    speed_of_sound: float = DEFAULT_SPEED_OF_SOUND,
) -> ReverberationModelResult:
    """Predict the reverberation time of a rectangular room by all five models.

    A convenience front-end that builds the six boundary surfaces of the room
    from ``dimensions`` and the three wall-pair mean absorptions, then evaluates
    :func:`sabine_reverberation_time`, :func:`eyring_reverberation_time`,
    :func:`millington_sette_reverberation_time`, :func:`fitzroy_reverberation_time`
    and :func:`arau_puchades_reverberation_time` on a common footing.

    :param dimensions: Room lengths ``(Lx, Ly, Lz)``, m.
    :param absorptions: Mean absorption ``(alpha_x, alpha_y, alpha_z)`` of the
        three wall pairs (perpendicular to x, y, z); each a scalar or a per-band
        array aligned with ``frequencies``.
    :param air_attenuation: Air power-attenuation coefficient ``m`` (1/m),
        scalar or per-band.
    :param frequencies: Band centre frequencies, in hertz, used only to label
        the result and its plot; defaults to an integer index over the bands.
    :param speed_of_sound: Speed of sound ``c0``, m/s.
    :return: The :class:`ReverberationModelResult`.
    """
    volume, total_area, pair_areas = _axial_geometry(dimensions)
    if len(absorptions) != 3:
        raise ValueError(
            "'absorptions' must give the mean absorption of the three wall pairs."
        )
    # Two equal-area opposing walls per axis share the axis mean absorption.
    surfaces: list[Surface] = []
    for area, alpha in zip(pair_areas, absorptions):
        surfaces.append((float(area) / 2.0, alpha))
        surfaces.append((float(area) / 2.0, alpha))

    sabine = np.atleast_1d(sabine_reverberation_time(
        volume, surfaces, air_attenuation=air_attenuation, speed_of_sound=speed_of_sound))
    eyring = np.atleast_1d(eyring_reverberation_time(
        volume, surfaces, air_attenuation=air_attenuation, speed_of_sound=speed_of_sound))
    millington = np.atleast_1d(millington_sette_reverberation_time(
        volume, surfaces, air_attenuation=air_attenuation, speed_of_sound=speed_of_sound))
    fitzroy = np.atleast_1d(fitzroy_reverberation_time(
        dimensions, absorptions, air_attenuation=air_attenuation,
        speed_of_sound=speed_of_sound))
    arau = np.atleast_1d(arau_puchades_reverberation_time(
        dimensions, absorptions, air_attenuation=air_attenuation,
        speed_of_sound=speed_of_sound))

    curve_bands = max(arr.size for arr in (sabine, eyring, millington, fitzroy, arau))
    if frequencies is None:
        n_bands = curve_bands
        freq = np.arange(1.0, n_bands + 1.0, dtype=np.float64)
    else:
        freq = np.asarray(frequencies, dtype=np.float64)
        if curve_bands not in (1, freq.size):
            raise ValueError(
                f"'frequencies' has {freq.size} bands but the per-band "
                f"absorption has {curve_bands}; they must match."
            )
        n_bands = freq.size

    def _fit(arr: np.ndarray) -> np.ndarray:
        return np.broadcast_to(arr, (n_bands,)).astype(np.float64)

    return ReverberationModelResult(
        frequencies=freq,
        sabine=_fit(sabine),
        eyring=_fit(eyring),
        millington_sette=_fit(millington),
        fitzroy=_fit(fitzroy),
        arau_puchades=_fit(arau),
        volume=volume,
        surface_area=total_area,
    )

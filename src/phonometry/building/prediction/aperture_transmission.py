#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound transmission through slits, holes and apertures (Hopkins 2007, Sound
Insulation, Section 4.3.10; Gomperts 1964; Wilson & Soroka 1965).

Air paths are the real limit on the sound insulation of an otherwise heavy
construction: a small slit or hole caps the achievable sound reduction index no
matter how massive the wall. This module predicts the transmission coefficient
``tau`` of the two canonical apertures and combines them with the surrounding
wall into a composite sound reduction index, the practical answer to "why do I
never reach the catalogue ``Rw``".

**Straight-edged slit (Hopkins Eq. 4.99, Gomperts).** With the acoustic
wavenumber :math:`k = 2\pi f / c_0`, :math:`K = k w` (``w`` slit width),
:math:`X = d / w` (``d`` slit depth) and the end correction
:math:`e = (1/\pi)(\ln(8/K) - 0.57722)`:

.. math::

   \tau = \frac{m K \cos^2(Ke)}
   {2 n^2 \left[ \frac{\sin^2(KX + 2Ke)}{\cos^2(Ke)}
   + \frac{K^2}{2 n^2} \left( 1 + \cos(KX) \cos(KX + 2Ke) \right) \right]}

where :math:`m = 8` (diffuse field) or ``4`` (normal incidence), and
:math:`n = 1` (slit in the middle of a plate) or ``0.5`` (slit along an
edge). The model assumes an inviscid air path; maxima in ``tau`` (dips in
``R``) occur at the resonances :math:`d + 2e = z\lambda/2` (Eq. 4.101,
:math:`z = 1, 2, 3, \ldots`).

**Circular aperture (Hopkins Eq. 4.102, Wilson & Soroka).** With the piston
radiation resistance :math:`R_0(2ka) = 1 - 2 J_1(2ka)/(2ka)` and reactance
:math:`X_0(2ka) = 2 H_1(2ka)/(2ka)` (:math:`J_1` Bessel, :math:`H_1` Struve;
radius ``a``, depth ``d``):

.. math::

   \tau = \frac{4 R_0}
   {4 R_0^2 \left[ \cos(kd) - X_0 \sin(kd) \right]^2
   + \left[ \left( R_0^2 - X_0^2 + 1 \right) \sin(kd)
   + 2 X_0 \cos(kd) \right]^2}

**Composite (Hopkins Eq. 4.92).** For elements of area :math:`S_n` and sound
reduction index :math:`R_n` the resultant is the area-weighted energy sum

.. math::

   R = -10 \log_{10}\!\left[ \frac{1}{\sum S_n} \sum S_n \, 10^{-R_n/10} \right]

so a bare opening (:math:`R = 0`, :math:`\tau = 1`) of relative area
:math:`S_\mathrm{a}/S` caps the composite at :math:`10 \log_{10}(S / S_\mathrm{a})`. This is the same
energetic combination used by the EN 12354-3/-4 facade model of
:mod:`phonometry.building.prediction.facade`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from scipy.special import j1, struve

from ..._internal.frozen import OwnsArrays
from ..._internal.validation import (
    require_choice,
    require_equal_counts,
    require_positive,
    require_present,
    require_ranks,
    require_same_length,
    require_scalar,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from ..._i18n import Language

#: Default speed of sound in air ``c0``, m/s (20 degC).
_SPEED_OF_SOUND: float = 343.0
#: Euler-Mascheroni constant in the slit end correction (Hopkins Eq. 4.100).
_EULER_GAMMA: float = 0.57722
#: Incident-field constant ``m`` of Hopkins (2007) Eq. 4.99, printed with the
#: equation's symbols on PDF page 522 (printed p. 495).
_FIELD_M: dict[Literal["diffuse", "normal"], float] = {"diffuse": 8.0, "normal": 4.0}
#: Slit-position constant ``n`` of Hopkins (2007) Eq. 4.99, printed with the
#: equation's symbols on PDF page 522 (printed p. 495).
_POSITION_N: dict[Literal["mid", "edge"], float] = {"mid": 1.0, "edge": 0.5}

__all__ = [
    "ApertureTransmissionResult",
    "circular_aperture_transmission_coefficient",
    "composite_transmission_loss",
    "slit_resonance_frequencies",
    "slit_transmission_coefficient",
    "transmission_loss_from_coefficient",
]


def transmission_loss_from_coefficient(tau: ArrayLike) -> np.ndarray:
    r"""Sound reduction index :math:`R = -10 \log_{10}(\tau)` from a transmission
    coefficient.

    :param tau: Transmission coefficient(s) ``tau`` (> 0). Values above 1 (a
        resonating aperture that transmits more than the incident intensity)
        give a negative ``R``.
    :return: The sound reduction index ``R``, in dB.
    :raises ValueError: for a non-positive coefficient.
    """
    t = np.asarray(tau, dtype=np.float64)
    if np.any(t <= 0.0):
        msg = "'tau' must be positive."
        raise ValueError(msg)
    return np.asarray(-10.0 * np.log10(t), dtype=np.float64)


@dataclass(frozen=True, kw_only=True)
class ApertureTransmissionResult(OwnsArrays):
    """Transmission through a slit or circular aperture (Hopkins 4.3.10).

    :ivar frequencies: Band centre frequencies, in hertz.
    :ivar transmission_coefficient: Transmission coefficient ``tau`` per band.
    :ivar kind: ``"slit"`` or ``"circular"``.
    :ivar depth: Wall thickness, in metres.
    :ivar width_m: Slit width, in metres, kept (with ``depth``) so
        :meth:`plot_geometry` can draw the section; given for a slit and
        ``None`` for a circular aperture.
    :ivar radius: Circular-aperture radius, in metres; given for a circular
        aperture and ``None`` for a slit.
    """

    frequencies: np.ndarray
    transmission_coefficient: np.ndarray
    kind: Literal["slit", "circular"]
    depth: float
    width_m: float | None = None
    radius: float | None = None

    def __post_init__(self) -> None:
        """Reject an aperture whose coefficient and band axis disagree.

        The aperture is rarely the end of the calculation: its ``R(f)`` goes
        on to :func:`composite_transmission_loss` beside the wall it pierces,
        or into an enclosure leak, where it is combined band by band with
        spectra that came from elsewhere. Numpy pairs a one-element
        coefficient with any band axis at all rather than refuse, so a
        coefficient that lost its band axis returns a composite ``R`` that is
        the right length, finite, and about a slit that was evaluated at one
        frequency only.

        The retained geometry is pinned to one shape as well: a slit keeps its
        ``width_m`` and a circular aperture its ``radius``, always one and
        never both, and :meth:`plot_geometry` draws whichever is present,
        testing ``width_m`` first. A result carrying both would silently
        render the slit section for what claims to be a circular aperture.

        The kept shape has to be the shape ``kind`` names, too. The section is
        drawn from whichever of the two is present and nothing in it says which
        kind it belongs to, so a ``"circular"`` result that kept a ``width_m``
        draws the slit section of that width -- pixel for pixel the figure of a
        slit, under a curve the same result labels a circular aperture -- and a
        ``"slit"`` that kept a ``radius`` draws the hole section of the doubled
        opening.

        :raises ValueError: if the two per-band arrays disagree, ``kind`` is
            neither ``"slit"`` nor ``"circular"``, the result carries both a
            slit width and a circular radius, the shape it carries is not the
            one ``kind`` names, or it carries no shape at all.
        :raises TypeError: if ``depth`` is ``None``, or ``kind`` is not a text.
        """
        require_present(self, "depth")
        require_ranks(self, frequencies=1, transmission_coefficient=1)
        require_same_length(self, "frequencies", "transmission_coefficient")
        require_choice(self.kind, "kind", ("slit", "circular"))
        if self.width_m is not None and self.radius is not None:
            msg = (
                "Give at most one of 'width_m' (a slit) and 'radius' (a "
                "circular aperture); this result carries both."
            )
            raise ValueError(msg)
        if self.width_m is not None and self.kind != "slit":
            msg = (
                f"'width_m' is the slit width, but 'kind' is {self.kind!r}; give "
                "'radius' for a circular aperture."
            )
            raise ValueError(msg)
        if self.radius is not None and self.kind != "circular":
            msg = (
                f"'radius' is the circular-aperture radius, but 'kind' is "
                f"{self.kind!r}; give 'width_m' for a slit."
            )
            raise ValueError(msg)
        if (self.width_m if self.kind == "slit" else self.radius) is None:
            shape = "'width_m'" if self.kind == "slit" else "'radius'"
            msg = f"A {self.kind!r} aperture keeps its {shape}; this result has none."
            raise ValueError(msg)

    @property
    def transmission_loss(self) -> np.ndarray:
        r"""Aperture sound reduction index :math:`R = -10 \log_{10}(\tau)` per
        band, dB.
        """
        return transmission_loss_from_coefficient(self.transmission_coefficient)

    def plot(
        self, ax: Axes | None = None, *, language: Language = "en", **kwargs: Any
    ) -> Axes:
        """Plot the aperture sound reduction index ``R(f)``.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_aperture_transmission

        check_language(language)
        return plot_aperture_transmission(self, ax=ax, language=language, **kwargs)

    def plot_geometry(
        self, ax: Axes | None = None, *, language: Language = "en", **kwargs: Any
    ) -> Axes:
        """Draw the wall-aperture cross-section to scale.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.geometry import plot_aperture_result_geometry

        check_language(language)
        return plot_aperture_result_geometry(self, ax=ax, language=language, **kwargs)


def _slit_end_correction(k_big: np.ndarray) -> np.ndarray:
    r"""End correction :math:`e = (1/\pi)(\ln(8/K) - \gamma)` (Hopkins
    Eq. 4.100).
    """
    return np.asarray((np.log(8.0 / k_big) - _EULER_GAMMA) / np.pi, dtype=np.float64)


def slit_transmission_coefficient(
    frequency: ArrayLike,
    width_m: float,
    depth: float,
    *,
    field: Literal["diffuse", "normal"] = "diffuse",
    position: Literal["mid", "edge"] = "mid",
    speed_of_sound: float = _SPEED_OF_SOUND,
) -> ApertureTransmissionResult:
    r"""Transmission coefficient of a straight-edged slit (Hopkins Eq. 4.99).

    :param frequency: Band centre frequency ``f``, in hertz (scalar or array, > 0).
    :param width_m: Slit width ``w``, in m (> 0).
    :param depth: Slit depth ``d`` (wall thickness across the slit), in m (> 0).
    :param field: ``"diffuse"`` (:math:`m = 8`) or ``"normal"``
        (:math:`m = 4`).
    :param position: ``"mid"`` (:math:`n = 1`) or ``"edge"``
        (:math:`n = 0.5`).
    :param speed_of_sound: Speed of sound in air ``c0`` (Default: 343 m/s).
    :return: An :class:`ApertureTransmissionResult` (kind ``"slit"``).
    :raises ValueError: for a non-positive input or unknown field/position.
    :raises TypeError: if ``field`` or ``position`` is not a text, or ``depth``,
        ``speed_of_sound`` or ``width_m`` is not a single number.
    """
    w = require_positive(width_m, "width_m")
    d = require_positive(depth, "depth")
    c0 = require_positive(speed_of_sound, "speed_of_sound")
    field = require_choice(field, "field", tuple(_FIELD_M))
    position = require_choice(position, "position", tuple(_POSITION_N))
    f = np.atleast_1d(np.asarray(frequency, dtype=np.float64))
    if f.ndim != 1 or f.size == 0:
        msg = "'frequency' must be a non-empty 1-D array."
        raise ValueError(msg)
    if np.any(f <= 0.0):
        msg = "'frequency' must be positive."
        raise ValueError(msg)

    m = _FIELD_M[field]
    n = _POSITION_N[position]
    k = 2.0 * np.pi * f / c0
    k_big = k * w
    x = d / w
    e = _slit_end_correction(k_big)
    cos_ke = np.cos(k_big * e)
    kx = k_big * x
    kx_2ke = kx + 2.0 * k_big * e
    # Numerator and denominator are both multiplied by cos^2(Ke) relative to
    # the printed Eq. 4.99, an identity that removes the division by cos(Ke)
    # (which vanishes at Ke = pi/2 + n*pi) and keeps tau finite there.
    numerator = m * k_big * cos_ke**4
    denominator = (
        2.0
        * n**2
        * (
            np.sin(kx_2ke) ** 2
            + (k_big**2 / (2.0 * n**2))
            * cos_ke**2
            * (1.0 + np.cos(kx) * np.cos(kx_2ke))
        )
    )
    tau = numerator / denominator
    return ApertureTransmissionResult(
        frequencies=f,
        transmission_coefficient=np.asarray(tau, dtype=np.float64),
        kind="slit",
        width_m=float(width_m),
        depth=float(depth),
    )


def slit_resonance_frequencies(
    depth: float,
    width_m: float,
    *,
    n_orders: int = 3,
    speed_of_sound: float = _SPEED_OF_SOUND,
) -> np.ndarray:
    r"""Slit resonance frequencies :math:`d + 2e = z\lambda/2` (Hopkins
    Eq. 4.101).

    Maxima in the transmission coefficient (dips in ``R``) occur where the
    effective slit depth is a half-wavelength multiple. Solved iteratively
    because the end correction ``e`` depends weakly on frequency.

    :param depth: Slit depth ``d``, in m (> 0).
    :param width_m: Slit width ``w``, in m (> 0).
    :param n_orders: Number of resonance orders ``z = 1..n_orders`` (>= 1).
    :param speed_of_sound: Speed of sound in air ``c0`` (Default: 343 m/s).
    :return: The resonance frequencies (Hz), one per order.
    :raises ValueError: for a non-positive input, ``n_orders < 1``, or a slit so
        wide relative to its depth that the effective depth :math:`d + 2e` is
        non-positive (no resonance exists; ``width_m`` must be much less than the
        wavelength).
    :raises TypeError: if ``depth``, ``n_orders``, ``speed_of_sound`` or ``width_m`` is
        not a single number.
    """
    require_scalar(n_orders, "n_orders")
    d = require_positive(depth, "depth")
    w = require_positive(width_m, "width_m")
    c0 = require_positive(speed_of_sound, "speed_of_sound")
    if n_orders < 1:
        msg = "'n_orders' must be at least 1."
        raise ValueError(msg)
    out = np.empty(n_orders, dtype=np.float64)
    for i in range(n_orders):
        z = i + 1
        # Fixed-point iteration on f: f = z c0 / (2 (d + 2 e(f))).
        f = z * c0 / (2.0 * d)
        for _ in range(50):
            k_big = (2.0 * np.pi * f / c0) * w
            e = (np.log(8.0 / k_big) - _EULER_GAMMA) / np.pi
            effective_depth = d + 2.0 * e * w
            if effective_depth <= 0.0:
                msg = (
                    "slit too wide relative to its depth: the effective depth "
                    "d + 2e is non-positive, so no resonance exists (the "
                    "Gomperts slit model requires 'width_m' << wavelength)."
                )
                raise ValueError(msg)
            f_new = z * c0 / (2.0 * effective_depth)
            if abs(f_new - f) < 1e-9 * f:
                f = f_new
                break
            f = f_new
        out[i] = f
    return out


def circular_aperture_transmission_coefficient(
    frequency: ArrayLike,
    radius: float,
    depth: float,
    *,
    speed_of_sound: float = _SPEED_OF_SOUND,
) -> ApertureTransmissionResult:
    """Transmission coefficient of a circular aperture (Hopkins Eq. 4.102).

    :param frequency: Band centre frequency ``f``, in hertz (scalar or array, > 0).
    :param radius: Aperture radius ``a``, in m (> 0).
    :param depth: Aperture depth ``d`` (wall thickness), in m (> 0).
    :param speed_of_sound: Speed of sound in air ``c0`` (Default: 343 m/s).
    :return: An :class:`ApertureTransmissionResult` (kind ``"circular"``).
    :raises ValueError: for a non-positive input.
    :raises TypeError: if ``depth``, ``radius`` or ``speed_of_sound`` is not a single
        number.
    """
    a = require_positive(radius, "radius")
    d = require_positive(depth, "depth")
    c0 = require_positive(speed_of_sound, "speed_of_sound")
    f = np.atleast_1d(np.asarray(frequency, dtype=np.float64))
    if f.ndim != 1 or f.size == 0:
        msg = "'frequency' must be a non-empty 1-D array."
        raise ValueError(msg)
    if np.any(f <= 0.0):
        msg = "'frequency' must be positive."
        raise ValueError(msg)

    k = 2.0 * np.pi * f / c0
    x = 2.0 * k * a
    r0 = 1.0 - 2.0 * j1(x) / x
    x0 = 2.0 * struve(1, x) / x
    kd = k * d
    term_a = 4.0 * r0**2 * (np.cos(kd) - x0 * np.sin(kd)) ** 2
    term_b = ((r0**2 - x0**2 + 1.0) * np.sin(kd) + 2.0 * x0 * np.cos(kd)) ** 2
    tau = 4.0 * r0 / (term_a + term_b)
    return ApertureTransmissionResult(
        frequencies=f,
        transmission_coefficient=np.asarray(tau, dtype=np.float64),
        kind="circular",
        radius=float(radius),
        depth=float(depth),
    )


def composite_transmission_loss(
    areas: ArrayLike, reduction_indices: ArrayLike
) -> np.ndarray:
    r"""Composite sound reduction index of parallel elements (Hopkins
    Eq. 4.92).

    The area-weighted energy combination of ``N`` elements (wall, window,
    slit, open aperture ...) sharing a partition:

    .. math::

       R = -10 \log_{10}\!\left[ \frac{1}{\sum S_n} \sum S_n \, 10^{-R_n/10}
       \right]

    A bare opening enters with :math:`R = 0` (:math:`\tau = 1`).

    :param areas: Element areas ``S_n``, in m^2 (1-D, length ``N``, all > 0).
    :param reduction_indices: Element sound reduction indices ``R_n``, in dB.
        Either a 1-D array of length ``N`` (one value per element) or a 2-D
        array of shape ``(N, M)`` (``N`` elements over ``M`` bands).
    :return: The composite ``R``: a scalar array for 1-D input, or one value
        per band (length ``M``) for 2-D input.
    :raises ValueError: for a non-positive area, mismatched shapes, or an
        empty element set.
    """
    s = np.atleast_1d(np.asarray(areas, dtype=np.float64))
    if s.ndim != 1 or s.size == 0:
        msg = "'areas' must be a non-empty 1-D array."
        raise ValueError(msg)
    if np.any(s <= 0.0) or not np.all(np.isfinite(s)):
        msg = "'areas' must be positive and finite."
        raise ValueError(msg)
    r = np.asarray(reduction_indices, dtype=np.float64)
    if r.ndim not in (1, 2):
        msg = "'reduction_indices' must be 1-D or 2-D."
        raise ValueError(msg)
    require_equal_counts(
        "composite_transmission_loss",
        {"areas": s.shape[0], "reduction_indices": r.shape[0]},
        "element",
    )
    tau = 10.0 ** (-r / 10.0)
    if r.ndim == 1:
        total_1d = float(np.sum(s * tau) / np.sum(s))
        return np.asarray(-10.0 * np.log10(total_1d), dtype=np.float64)
    total_2d = np.sum(s[:, None] * tau, axis=0) / np.sum(s)
    return np.asarray(-10.0 * np.log10(total_2d), dtype=np.float64)

#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Insertion loss of a close or free-standing machine enclosure.

Wrapping a machine in a sealed enclosure reduces the radiated noise by the
transmission loss of its panels, *minus* a penalty for the reverberant build-up
inside the small, hard cavity. Bies, Hansen & Howard, *Engineering Noise
Control* 5th ed., §7.4.2 (Eqs. (7.103), (7.111)) write the net reduction as

    IL = R - C,        C = 10 log10[ 0.3 + S_E (1 - alpha_i) / (S_i alpha_i) ],

where ``R`` is the field-incidence transmission loss of the enclosure panels,
``S_E`` the external surface area, ``S_i`` the internal surface area (including
the machine) and ``alpha_i`` the mean absorption of the enclosure interior. The
reverberant term is exactly ``S_E`` over the interior **room constant**
``R_i = S_i alpha_i / (1 - alpha_i)`` (:func:`phonometry.room.room_constant`), so

    C = 10 log10( 0.3 + S_E / R_i ).

A hard interior (``alpha_i`` small) makes ``C`` large and wastes much of the
panel ``R``; lining the enclosure drives ``C`` toward its floor
``10 log10 0.3 = -5.2 dB`` (a fully absorbing interior, where ``IL = R + 5.2``).
Bies terms this net reduction the enclosure *noise reduction*; it is the
insertion loss of the enclosure.

**The panel transmission loss ``R`` is supplied by the caller** -- measured, or
predicted by a panel model -- as a per-band array, a callable of frequency, or
a panel prediction result (a :class:`phonometry.building.SoundReductionResult`
or :class:`phonometry.building.ApertureTransmissionResult`, matched structurally
so no dependency on ``building`` is introduced). This module never predicts
``R`` itself; it combines a given ``R`` with the interior absorption. The
interior room constant reuses :func:`phonometry.room.room_constant`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .._internal.validation import require_positive
from ..room.steady_field import room_constant

if TYPE_CHECKING:
    from matplotlib.axes import Axes


@dataclass(frozen=True)
class EnclosureResult:
    """Insertion loss of a machine enclosure over frequency (Bies §7.4.2).

    :ivar frequencies: Frequencies ``f``, Hz, or ``None`` if the panel ``R``
        was given as a bare per-band array with no frequency labels.
    :ivar panel_transmission_loss: The supplied panel transmission loss ``R``
        per band, dB.
    :ivar correction: The interior-build-up correction ``C`` per band, dB.
    :ivar insertion_loss: The net enclosure insertion loss ``IL = R - C``, dB.
    :ivar external_area: External enclosure surface area ``S_E``, m2.
    :ivar internal_area: Internal surface area ``S_i``, m2.
    :ivar room_constant: Interior room constant ``R_i`` per band, m2.
    """

    frequencies: np.ndarray | None
    panel_transmission_loss: np.ndarray
    correction: np.ndarray
    insertion_loss: np.ndarray
    external_area: float
    internal_area: float
    room_constant: np.ndarray

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the panel ``R``, correction ``C`` and net insertion loss.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from .._plot.noise_control import plot_enclosure

        return plot_enclosure(self, ax=ax, **kwargs)


class PanelTransmissionResult(Protocol):
    """A panel prediction result exposing a per-band transmission loss.

    A frozen result such as :class:`phonometry.building.SoundReductionResult`
    or :class:`phonometry.building.ApertureTransmissionResult` carries the
    predicted transmission loss in ``transmission_loss`` and its band centres
    in ``frequencies``. Matching structurally (a :class:`typing.Protocol`)
    lets :func:`enclosure_insertion_loss` accept such a result directly without
    importing the ``building`` package, so ``noise_control`` keeps no
    dependency on it.
    """

    transmission_loss: NDArray[np.float64]
    frequencies: NDArray[np.float64]


def _resolve_frequencies(
    frequencies: ArrayLike | None,
) -> NDArray[np.float64] | None:
    """Validate an optional 1-D positive frequency grid (Hz)."""
    if frequencies is None:
        return None
    freqs = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    if freqs.ndim != 1 or freqs.size == 0:
        raise ValueError("'frequencies' must be a non-empty 1-D array.")
    if np.any(freqs <= 0.0) or not np.all(np.isfinite(freqs)):
        raise ValueError("'frequencies' must be positive and finite.")
    return freqs


def _resolve_panel_r(
    panel_transmission_loss: ArrayLike | Callable[[NDArray[np.float64]], ArrayLike],
    freqs: NDArray[np.float64] | None,
) -> NDArray[np.float64]:
    """Resolve the panel transmission loss ``R`` into a validated 1-D array."""
    if callable(panel_transmission_loss):
        if freqs is None:
            raise ValueError(
                "'frequencies' is required when 'panel_transmission_loss' "
                "is a callable."
            )
        r = np.atleast_1d(np.asarray(panel_transmission_loss(freqs), dtype=np.float64))
    else:
        r = np.atleast_1d(np.asarray(panel_transmission_loss, dtype=np.float64))
    if r.ndim != 1 or r.size == 0:
        raise ValueError("'panel_transmission_loss' must be a non-empty 1-D array.")
    if not np.all(np.isfinite(r)):
        raise ValueError("'panel_transmission_loss' must be finite.")
    return r


def enclosure_insertion_loss(
    panel_transmission_loss: (
        ArrayLike
        | Callable[[NDArray[np.float64]], ArrayLike]
        | PanelTransmissionResult
    ),
    external_area: float,
    internal_area: float,
    internal_absorption: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> EnclosureResult:
    """Net insertion loss of a machine enclosure (Bies Eqs. (7.103), (7.111)).

    ``IL = R - C`` with ``C = 10 log10(0.3 + S_E / R_i)`` and the interior room
    constant ``R_i = S_i alpha_i / (1 - alpha_i)``.

    :param panel_transmission_loss: Panel transmission loss ``R`` per band, dB.
        One of: a per-band array (measured); a callable mapping a frequency
        array to per-band ``R`` (then ``frequencies`` is required); or a panel
        prediction result carrying ``transmission_loss`` and ``frequencies``,
        such as the :class:`~phonometry.building.SoundReductionResult` of
        :func:`phonometry.single_panel_transmission_loss` /
        :func:`phonometry.double_wall_transmission_loss` or the
        :class:`~phonometry.building.ApertureTransmissionResult` of
        :func:`phonometry.composite_transmission_loss` (its ``frequencies`` are
        then used unless *frequencies* is given). This function does not
        predict ``R`` itself.
    :param external_area: External enclosure surface area ``S_E``, m2.
    :param internal_area: Internal surface area ``S_i`` (including the machine),
        m2.
    :param internal_absorption: Mean interior absorption ``alpha_i`` in
        ``(0, 1)`` (scalar or per-band).
    :param frequencies: Band centre frequencies, Hz; required when
        ``panel_transmission_loss`` is a callable, optional otherwise (used to
        label the result and the plot).
    :return: An :class:`EnclosureResult`.
    """
    s_e = require_positive(external_area, "external_area")
    s_i = require_positive(internal_area, "internal_area")

    if (
        not callable(panel_transmission_loss)
        and not isinstance(panel_transmission_loss, (np.ndarray, list, tuple))
        and hasattr(panel_transmission_loss, "transmission_loss")
        and hasattr(panel_transmission_loss, "frequencies")
    ):
        result = cast("PanelTransmissionResult", panel_transmission_loss)
        if frequencies is None:
            frequencies = result.frequencies
        panel_transmission_loss = np.asarray(
            result.transmission_loss, dtype=np.float64
        )

    freqs = _resolve_frequencies(frequencies)
    r = _resolve_panel_r(panel_transmission_loss, freqs)

    alpha = np.asarray(internal_absorption, dtype=np.float64)
    if alpha.ndim > 1:
        raise ValueError("'internal_absorption' must be a scalar or a 1-D array.")
    if np.any(alpha <= 0.0) or np.any(alpha >= 1.0) or not np.all(np.isfinite(alpha)):
        raise ValueError("'internal_absorption' must lie strictly in (0, 1).")

    r_i = np.atleast_1d(np.asarray(room_constant(s_i, alpha), dtype=np.float64))
    r_i_b, r_b = np.broadcast_arrays(r_i, r)
    if freqs is not None and freqs.shape != r_b.shape:
        raise ValueError(
            "'frequencies' must match the number of panel-R / absorption bands."
        )
    correction = 10.0 * np.log10(0.3 + s_e / r_i_b)
    il = r_b - correction
    return EnclosureResult(
        frequencies=freqs,
        panel_transmission_loss=np.array(r_b, dtype=np.float64),
        correction=np.array(correction, dtype=np.float64),
        insertion_loss=np.array(il, dtype=np.float64),
        external_area=s_e,
        internal_area=s_i,
        room_constant=np.array(r_i_b, dtype=np.float64),
    )

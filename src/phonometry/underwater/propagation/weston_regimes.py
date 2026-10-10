#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Weston's shallow-water propagation regimes (flux theory).

A source in a shallow-water waveguide loses energy in four successive range
regimes, each with its own power law. The boundaries between them follow from
the seabed reflectivity alone, which makes the set an inexpensive analytic
reference for any numerical propagation model:

* **spherical spreading** -- :math:`F = 1/r^2` (:math:`20 \log_{10} r`), while the
  sound has not yet felt the boundaries;
* **cylindrical spreading** -- :math:`F = 2\psi_\mathrm{c}/(r H)` (:math:`10 \log_{10} r`),
  once the energy is confined to a cylinder of height ``H`` and only rays
  within the critical angle :math:`\psi_\mathrm{c}` survive;
* **mode stripping** -- :math:`F = (\pi/(\eta H))^{1/2} \, r^{-3/2}`
  (:math:`15 \log_{10} r`), once the accumulated reflection loss has eroded the
  steep paths;
* **single mode** -- an exponential decay dominated by the lowest-order mode.

Everything here is implemented clean-room from Ainslie, *Principles of Sonar
Performance Modelling* (Springer 2010), §9.1.1.2 (printed pp. 452-458):
Equations (9.42) to (9.61) and the seabed properties of Table 9.1
(:data:`WESTON_SEABEDS`). The quantity computed is Ainslie's **propagation
factor** ``F`` (units m⁻²), reported as the propagation loss
:math:`\mathrm{PL} = -10 \log_{10} F` dB re 1 m², which reduces to spherical
spreading for a point source in free water.

The regime formulae are energy-flux (incoherent) results: they describe the
range-averaged field, not its modal interference. That is exactly what makes
them a usable cross-check for :mod:`phonometry.underwater.propagation.numerical`
-- the range average of a normal-mode or parabolic-equation field over many
interference cycles converges on the cylindrical-spreading law, with
:math:`\psi_\mathrm{c} = \pi/2` for a totally reflecting (pressure-release) bottom.

.. note::
    Ainslie's Equation (9.57) for the mode-stripping/single-mode transition is
    printed as :math:`r_{\mathrm{MS}} \approx k^2 H_\mathrm{e}^3/(9\eta)`. Carrying out
    the derivation the accompanying text prescribes -- "equating
    :math:`\theta_n` and :math:`\theta_{\mathrm{eff}}` with :math:`n = 3/2`"
    -- with the two equations exactly as they are printed, namely
    :math:`\theta_{\mathrm{eff}} = (\pi H/(4 \eta r))^{1/2}` (Equation 9.47,
    with the **true** water depth ``H``) and :math:`\theta_n = n\pi/(k H_\mathrm{e})`
    (Equation 9.56, with the **effective** depth ``He``), gives
    :math:`r_{\mathrm{MS}} = k^2 H_\mathrm{e}^2 H/(9\pi\eta)` instead. The printed
    form is larger by :math:`\pi H_\mathrm{e}/H`. This module implements the
    derivation-consistent value, which also keeps
    :math:`\theta_{\mathrm{eff}}` defined with ``H`` everywhere it is used
    (the composite loss below evaluates Equation 9.47 the same way), and
    records the discrepancy in ``docs/ERRATA.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy.special import erf

from ..._internal.frozen import OwnsArrays
from ..._internal.validation import (
    require_positive,
    require_ranks,
    require_same_length,
    require_scalar,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import NDArray

#: Regime labels, in order of increasing range.
WESTON_REGIMES = ("spherical", "cylindrical", "mode-stripping", "single-mode")

#: How far, in dB, the composite loss of a result built by hand may be from
#: the law of the regime in force: rounding, not a tolerance of the method.
_FIELD_SLACK_DB = 1e-9

# Normal incidence, the largest grazing angle a ray can have: the upper edge
# of the (0, 90] degree validity range for a 'critical_angle_deg' override.
_NORMAL_INCIDENCE_DEG = 90.0


@dataclass(frozen=True)
class WestonSeabed:
    r"""Characteristic seabed properties (Ainslie Table 9.1, printed p. 454).

    :ivar name: Sediment name.
    :ivar grain_size: Grain size ``Mz`` (phi units).
    :ivar sound_speed_ratio: :math:`c_{\mathrm{sed}}/c_\mathrm{w}`.
    :ivar density_ratio: :math:`\rho_{\mathrm{sed}}/\rho_\mathrm{w}`.
    :ivar attenuation_db_per_wavelength: :math:`\beta_{\mathrm{sed}}`, in dB
        per wavelength.
    :ivar loss_parameter:
        :math:`\varepsilon = \beta_{\mathrm{sed}}/(40 \pi \log_{10} e)`
        (Equation 9.23).
    :ivar sound_speed_gradient_per_s: ``c'``, the sediment sound-speed gradient, in
        s⁻¹ (0 for sand, 1 for mud).
    """

    name: str
    grain_size: float
    sound_speed_ratio: float
    density_ratio: float
    attenuation_db_per_wavelength: float
    loss_parameter: float
    sound_speed_gradient_per_s: float


#: The two characteristic seabeds tabulated in Ainslie Table 9.1, PDF page 484
#: (printed p. 454): medium sand
#: (``Mz = 1.5``, a reflecting bottom with a critical angle) and mud
#: (``Mz = 8``, refracting, no critical angle).
WESTON_SEABEDS: Mapping[str, WestonSeabed] = MappingProxyType(
    {
        "sand": WestonSeabed(
            name="sand",
            grain_size=1.5,
            sound_speed_ratio=1.20,
            density_ratio=2.1,
            attenuation_db_per_wavelength=0.88,
            loss_parameter=0.0161,
            sound_speed_gradient_per_s=0.0,
        ),
        "mud": WestonSeabed(
            name="mud",
            grain_size=8.0,
            sound_speed_ratio=1.00,
            density_ratio=1.4,
            attenuation_db_per_wavelength=0.09,
            loss_parameter=0.00165,
            sound_speed_gradient_per_s=1.0,
        ),
    }
)


def _seabed(seabed: str | WestonSeabed) -> WestonSeabed:
    if isinstance(seabed, WestonSeabed):
        return seabed
    key = str(seabed).strip().lower()
    if key not in WESTON_SEABEDS:
        msg = f"'seabed' must be one of {tuple(WESTON_SEABEDS)} or a WestonSeabed, got {seabed!r}."
        raise ValueError(msg)
    return WESTON_SEABEDS[key]


def critical_grazing_angle(sound_speed_ratio: float) -> float:
    r"""Critical grazing angle
    :math:`\psi_\mathrm{c} = \arccos(c_\mathrm{w}/c_{\mathrm{sed}})`, in radians.

    A seabed slower than the water (:math:`c_{\mathrm{sed}} \le c_\mathrm{w}`, e.g.
    mud) has **no** critical angle; the function then returns ``0``, which
    correctly switches the reflection-loss gradient to the
    refracting-sediment branch of :func:`reflection_loss_gradient`.

    :param sound_speed_ratio: :math:`c_{\mathrm{sed}}/c_\mathrm{w}`, dimensionless and
        positive.
    :return: The critical grazing angle, in radians (``0`` if none exists).
    :raises ValueError: If the ratio is not positive and finite.
    """
    ratio = require_positive(sound_speed_ratio, "sound_speed_ratio")
    if ratio <= 1.0:
        return 0.0
    return float(np.arccos(1.0 / ratio))


def loss_parameter(attenuation_db_per_wavelength: float) -> float:
    r"""Sediment loss parameter
    :math:`\varepsilon = \beta_{\mathrm{sed}}/(40 \pi \log_{10} e)`
    (Ainslie Eq. 9.23).

    :param attenuation_db_per_wavelength: :math:`\beta_{\mathrm{sed}}`, in dB
        per wavelength.
    :return: The dimensionless loss parameter :math:`\varepsilon`.
    :raises ValueError: If the attenuation is negative or non-finite.
    """
    require_scalar(attenuation_db_per_wavelength, "attenuation_db_per_wavelength")
    beta = float(attenuation_db_per_wavelength)
    if not np.isfinite(beta) or beta < 0.0:
        msg = "'attenuation_db_per_wavelength' must be non-negative and finite."
        raise ValueError(msg)
    return float(beta / (40.0 * np.pi * np.log10(np.e)))


def reflection_loss_gradient(
    seabed: str | WestonSeabed = "sand", *, frequency_hz: float | None = None
) -> float:
    r"""Reflection loss gradient :math:`\eta`, in nepers per radian.

    The rate at which the seabed reflection loss grows with grazing angle,
    :math:`\lvert R(\theta) \rvert \approx \exp(-\eta \theta)` (Ainslie
    Eq. 9.45). Two branches:

    * a **reflecting** seabed with a critical angle (sand, coarse silt),
      :math:`\eta = 2 \varepsilon (\rho_{\mathrm{sed}}/\rho_\mathrm{w})
      \cos^2 \psi_\mathrm{c} / \sin^3 \psi_\mathrm{c}` (Eq. 9.51), frequency-independent;
    * a **refracting** seabed with none (mud, clay, fine silt),
      :math:`\eta = 2 \omega \varepsilon / c'` (Eq. 9.53), proportional to
      frequency.

    :param seabed: ``"sand"``, ``"mud"`` or an explicit :class:`WestonSeabed`.
    :param frequency_hz: Acoustic frequency, in Hz; required only for the
        refracting branch (:math:`c' > 0`).
    :return: The reflection loss gradient :math:`\eta`, in Np/rad.
    :raises ValueError: If the frequency is missing or invalid for a refracting
        seabed.
    """
    bed = _seabed(seabed)
    psi_c = critical_grazing_angle(bed.sound_speed_ratio)
    if psi_c > 0.0:
        return float(
            2.0
            * bed.loss_parameter
            * bed.density_ratio
            * np.cos(psi_c) ** 2
            / np.sin(psi_c) ** 3
        )
    if bed.sound_speed_gradient_per_s <= 0.0:
        msg = (
            "a seabed without a critical angle needs a positive 'sound_speed_gradient_per_s'"
            " to use the refracting branch of Equation (9.53)."
        )
        raise ValueError(msg)
    if frequency_hz is None:
        msg = "'frequency_hz' is required for a refracting seabed (Equation 9.53)."
        raise ValueError(msg)
    f = require_positive(frequency_hz, "frequency_hz")
    return float(
        2.0 * (2.0 * np.pi * f) * bed.loss_parameter / bed.sound_speed_gradient_per_s
    )


def effective_depth(
    water_depth: float,
    frequency_hz: float,
    *,
    seabed: str | WestonSeabed = "sand",
    speed_of_sound: float = 1500.0,
) -> float:
    r"""Weston effective water depth ``He`` (Ainslie Eq. 9.55), in metres.

    :math:`H_\mathrm{e} = H + (\rho_{\mathrm{sed}}/\rho_\mathrm{w}) /
    ((\omega/c_\mathrm{w}) \sin \psi_\mathrm{c})`: the depth at which a
    pressure-release boundary appears to lie, a short distance below the true
    seabed. Only meaningful for a seabed with a critical angle.

    :param water_depth: Water-column depth ``H``, in metres.
    :param frequency_hz: Acoustic frequency, in Hz.
    :param seabed: ``"sand"``, ``"mud"`` or a :class:`WestonSeabed`.
    :param speed_of_sound: Water sound speed ``c_w``, in m/s.
    :return: The effective depth ``He``, in metres.
    :raises ValueError: If the seabed has no critical angle or an input is
        invalid.
    """
    h = require_positive(water_depth, "water_depth")
    f = require_positive(frequency_hz, "frequency_hz")
    c = require_positive(speed_of_sound, "speed_of_sound")
    bed = _seabed(seabed)
    psi_c = critical_grazing_angle(bed.sound_speed_ratio)
    if psi_c <= 0.0:
        msg = (
            "'effective_depth' needs a seabed with a critical angle (c_sed > c_w);"
            f" {bed.name!r} has none."
        )
        raise ValueError(msg)
    k = 2.0 * np.pi * f / c
    return float(h + bed.density_ratio / (k * np.sin(psi_c)))


def waveguide_cutoff_frequency(
    water_depth: float,
    *,
    seabed: str | WestonSeabed = "sand",
    speed_of_sound: float = 1500.0,
) -> float:
    r"""Shallow-water waveguide cut-off frequency ``fc`` (Ainslie Eq. 9.60),
    in Hz.

    :math:`f_\mathrm{c} = (\pi - \rho_{\mathrm{sed}}/\rho_\mathrm{w}) /
    (2 \pi \sin \psi_\mathrm{c}) \cdot c_\mathrm{w}/H` -- below it no mode is cut on
    and ducted propagation does not occur.

    :param water_depth: Water-column depth ``H``, in metres.
    :param seabed: ``"sand"``, ``"mud"`` or a :class:`WestonSeabed`.
    :param speed_of_sound: Water sound speed ``c_w``, in m/s.
    :return: The cut-off frequency, in Hz.
    :raises ValueError: If the seabed has no critical angle or an input is
        invalid.
    """
    h = require_positive(water_depth, "water_depth")
    c = require_positive(speed_of_sound, "speed_of_sound")
    bed = _seabed(seabed)
    psi_c = critical_grazing_angle(bed.sound_speed_ratio)
    if psi_c <= 0.0:
        msg = (
            "'waveguide_cutoff_frequency' needs a seabed with a critical angle"
            f" (c_sed > c_w); {bed.name!r} has none."
        )
        raise ValueError(msg)
    return float((np.pi - bed.density_ratio) / (2.0 * np.pi * np.sin(psi_c)) * c / h)


@dataclass(frozen=True)
class WestonRegimeBoundaries:
    r"""Range boundaries between Weston's four propagation regimes.

    :ivar spherical_to_cylindrical: Range at which :math:`1/r^2` and
        :math:`2\psi_\mathrm{c}/(r H)` are equal, :math:`H/(2\psi_\mathrm{c})`, in metres.
    :ivar cylindrical_to_mode_stripping: Ainslie Eq. (9.50)
        :math:`r_{\mathrm{CS}} = \pi H/(4 \eta \psi_\mathrm{c}^2)`, in metres
        (``inf`` for a lossless bottom).
    :ivar mode_stripping_to_single_mode:
        :math:`r_{\mathrm{MS}} = k^2 H_\mathrm{e}^2 H/(9 \pi \eta)`, in metres
        (``inf`` for a lossless bottom). See the module note on Eq. (9.57).
    :ivar critical_angle_rad: Critical grazing angle :math:`\psi_\mathrm{c}`, in radians.
    :ivar reflection_loss_gradient_np_per_rad: :math:`\eta`, in Np/rad.
    :ivar effective_depth: Weston effective depth ``He``, in metres.
    :ivar cutoff_frequency: Waveguide cut-off frequency, in Hz (``nan`` when
        the seabed has no critical angle).
    :ivar mode_count: Number of cut-on modes,
        :math:`(\omega/c_\mathrm{w}) H_\mathrm{e} \sin \psi_\mathrm{c} / \pi` (Eq. 9.58), as a real
        number.
    """

    spherical_to_cylindrical: float
    cylindrical_to_mode_stripping: float
    mode_stripping_to_single_mode: float
    critical_angle_rad: float
    reflection_loss_gradient_np_per_rad: float
    effective_depth: float
    cutoff_frequency: float
    mode_count: float


def weston_regime_boundaries(
    frequency_hz: float,
    water_depth: float,
    *,
    seabed: str | WestonSeabed = "sand",
    speed_of_sound: float = 1500.0,
    critical_angle_deg: float | None = None,
    reflection_loss_gradient_value_np_per_rad: float | None = None,
) -> WestonRegimeBoundaries:
    r"""Regime boundaries of a shallow-water waveguide (Ainslie §9.1.1.2).

    :param frequency_hz: Acoustic frequency, in Hz.
    :param water_depth: Water-column depth ``H``, in metres.
    :param seabed: ``"sand"``, ``"mud"`` or a :class:`WestonSeabed`.
    :param speed_of_sound: Water sound speed ``c_w``, in m/s.
    :param critical_angle_deg: Override the seabed critical angle :math:`\psi_\mathrm{c}`,
        in degrees. Use ``90`` for the ideal totally reflecting waveguide.
    :param reflection_loss_gradient_value_np_per_rad: Override :math:`\eta`, in Np/rad.
        Use ``0`` for a lossless bottom (no mode stripping, no single-mode
        regime).
    :return: A :class:`WestonRegimeBoundaries`.
    :raises ValueError: If an input is invalid.

    .. note::
        The two overrides are independent: overriding ``critical_angle_deg``
        alone leaves :math:`\eta` computed from the seabed's *own* critical
        angle through Equation (9.51), which mixes two different bottoms.
        Pass both together (as the ideal-waveguide case
        ``critical_angle_deg=90`` with
        ``reflection_loss_gradient_value=0`` does) whenever the intent is a
        hypothetical seabed rather than a tweak of the tabulated one.
    """
    f = require_positive(frequency_hz, "frequency_hz")
    h = require_positive(water_depth, "water_depth")
    c = require_positive(speed_of_sound, "speed_of_sound")
    bed = _seabed(seabed)
    psi_c, eta = _angle_and_gradient(
        bed, f, critical_angle_deg, reflection_loss_gradient_value_np_per_rad
    )
    k = 2.0 * np.pi * f / c
    if psi_c < np.pi / 2.0 and bed.sound_speed_ratio > 1.0:
        h_eff = h + bed.density_ratio / (k * np.sin(psi_c))
        f_cut = (np.pi - bed.density_ratio) / (2.0 * np.pi * np.sin(psi_c)) * c / h
    else:
        # An ideal (totally reflecting) bottom puts the pressure-release
        # boundary at the seabed itself and cuts on the first mode at c/(2H).
        h_eff = h
        f_cut = c / (2.0 * h) if psi_c >= np.pi / 2.0 else float("nan")
    r_ss_cs = h / (2.0 * psi_c)
    if eta > 0.0:
        r_cs = np.pi * h / (4.0 * eta * psi_c**2)
        # Equation (9.57) re-derived from Equations (9.47) and (9.56) exactly
        # as printed -- H in the effective angle, He in the mode angle -- which
        # restores a factor pi and keeps the true depth where Eq. (9.47) puts
        # it (see the module note and docs/ERRATA.md).
        r_ms = k**2 * h_eff**2 * h / (9.0 * np.pi * eta)
    else:
        r_cs = float("inf")
        r_ms = float("inf")
    return WestonRegimeBoundaries(
        spherical_to_cylindrical=float(r_ss_cs),
        cylindrical_to_mode_stripping=float(r_cs),
        mode_stripping_to_single_mode=float(r_ms),
        critical_angle_rad=float(psi_c),
        reflection_loss_gradient_np_per_rad=float(eta),
        effective_depth=float(h_eff),
        cutoff_frequency=float(f_cut),
        mode_count=float(k * h_eff * np.sin(psi_c) / np.pi),
    )


def _angle_and_gradient(
    bed: WestonSeabed,
    frequency_hz: float,
    critical_angle_deg: float | None,
    gradient: float | None,
) -> tuple[float, float]:
    r"""Resolve :math:`(\psi_\mathrm{c}, \eta)` from the seabed and the optional
    overrides.
    """
    if critical_angle_deg is None:
        psi_c = critical_grazing_angle(bed.sound_speed_ratio)
        if psi_c <= 0.0:
            msg = (
                f"seabed {bed.name!r} has no critical angle; pass 'critical_angle_deg'"
                " explicitly (in degrees) to fix the trapped-ray cone."
            )
            raise ValueError(msg)
    else:
        require_scalar(critical_angle_deg, "critical_angle_deg")
        deg = float(critical_angle_deg)
        if not np.isfinite(deg) or not (0.0 < deg <= _NORMAL_INCIDENCE_DEG):
            msg = "'critical_angle_deg' must lie in (0, 90] degrees."
            raise ValueError(msg)
        psi_c = np.radians(deg)
    if gradient is None:
        eta = reflection_loss_gradient(bed, frequency_hz=frequency_hz)
    else:
        require_scalar(gradient, "reflection_loss_gradient_value_np_per_rad")
        eta = float(gradient)
        if not np.isfinite(eta) or eta < 0.0:
            msg = "'reflection_loss_gradient_value_np_per_rad' must be non-negative and finite."
            raise ValueError(msg)
    return float(psi_c), float(eta)


@dataclass(frozen=True)
class WestonPropagationResult(OwnsArrays):
    r"""Weston regime propagation loss versus range.

    :ivar range_m: Ranges from the source, in metres.
    :ivar propagation_loss: Composite propagation loss
        :math:`\mathrm{PL} = -10 \log_{10} F` per range, in dB re 1 m².
    :ivar propagation_factor: The composite propagation factor ``F``, in m⁻².
    :ivar spherical: Spherical-spreading loss :math:`20 \log_{10} r` at every
        range, in dB.
    :ivar cylindrical: Cylindrical-spreading loss (Eq. 9.42) at every range, dB.
    :ivar mode_stripping: Mode-stripping loss (Eq. 9.49) at every range, dB
        (``nan`` when the bottom is lossless: without reflection loss there is
        nothing to strip).
    :ivar single_mode: Single-mode loss (Eq. 9.54) at every range, in dB.
    :ivar multipath: Loss from the continuous multipath integral (Eq. 9.46),
        which joins the cylindrical and mode-stripping regimes smoothly, in dB.
    :ivar boundaries: The :class:`WestonRegimeBoundaries` in force.
    :ivar frequency: Acoustic frequency, in Hz.
    :ivar water_depth: Water-column depth ``H``, in metres.
    :ivar source_depth: Source depth ``z0``, in metres.
    :ivar receiver_depth: Receiver depth ``z``, in metres.
    :ivar seabed: Name of the seabed used.

    The regime in force at each range (:attr:`regime`) is read from the
    ranges and the boundaries, so it is not a field.
    """

    range_m: NDArray[np.float64]
    propagation_loss: NDArray[np.float64]
    propagation_factor: NDArray[np.float64]
    spherical: NDArray[np.float64]
    cylindrical: NDArray[np.float64]
    mode_stripping: NDArray[np.float64]
    single_mode: NDArray[np.float64]
    multipath: NDArray[np.float64]
    boundaries: WestonRegimeBoundaries
    frequency: float
    water_depth: float
    source_depth: float
    receiver_depth: float
    seabed: str

    def __post_init__(self) -> None:
        r"""Reject a column that does not run over the result's own ranges.

        The eight arrays are one table indexed by ``range_m``: the composite
        loss, the factor it was taken from, and the four regime laws evaluated
        at every range whether or not they are in force there. A column of
        another length answers for ranges the row beside it did not come
        from. The label of the regime in force is read from ``range_m`` and
        the boundaries, so it always runs over the result's own ranges.

        Six of the eight reach :meth:`plot`, and there the mistake stops the
        figure without saying whose it is -- matplotlib refuses with ``x and y
        must have same first dimension, but have shapes (40,) and (39,)``,
        which carries two shapes and neither the field nor the result they
        belong to, so the six are indistinguishable from it.

        The figure never draws the factor, so nothing complains about it: a
        one-element ``propagation_factor`` broadcasts rather than raising,
        :math:`-10 \log_{10} F` checked against ``propagation_loss`` comes
        back 49 dB adrift instead of nought, and the figure is drawn in full
        either way.

        The ranks are pinned with the lengths because a range grid handed in
        two-dimensional stays two-dimensional through every column and agrees
        with itself on every count; it survives construction and dies in
        :meth:`plot` on numpy's ambiguous truth value, raised while testing
        whether a regime boundary falls inside the axis.

        The composite loss is the law of the regime in force at each range,
        so it is held to that column, and to the factor it was taken from.

        :raises ValueError: if a column has the wrong number of axes, or a
            length other than ``range_m``'s, or the composite loss is not the
            law of the regime in force or not :math:`-10 \log_{10} F`.
        """
        require_ranks(
            self,
            range_m=1,
            propagation_loss=1,
            propagation_factor=1,
            spherical=1,
            cylindrical=1,
            mode_stripping=1,
            single_mode=1,
            multipath=1,
        )
        require_same_length(
            self,
            "range_m",
            "propagation_loss",
            "propagation_factor",
            "spherical",
            "cylindrical",
            "mode_stripping",
            "single_mode",
            "multipath",
            axis="range",
        )
        laws = dict(
            zip(
                WESTON_REGIMES,
                (
                    self.spherical,
                    self.cylindrical,
                    self.mode_stripping,
                    self.single_mode,
                ),
                strict=True,
            )
        )
        in_force = _composite(self.regime, laws)
        loss = np.asarray(self.propagation_loss, dtype=np.float64)
        for name, expected in (
            ("the law of the regime in force", in_force),
            ("-10 lg F of 'propagation_factor'", _to_db(self.propagation_factor)),
        ):
            if not np.allclose(
                loss, expected, rtol=0.0, atol=_FIELD_SLACK_DB, equal_nan=True
            ):
                msg = (
                    "WestonPropagationResult: 'propagation_loss' must be "
                    f"{name} at each range."
                )
                raise ValueError(msg)

    @property
    def regime(self) -> NDArray[np.str_]:
        """The regime in force at each range, one of :data:`WESTON_REGIMES`.

        Read from :attr:`range_m` and :attr:`boundaries`: each regime holds
        from its own boundary onwards, the boundary itself included.

        :return: One label per range.
        """
        return _regime_labels(self.range_m, self.boundaries)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the composite loss with each regime's law and the boundaries."""
        from ..._i18n import check_language
        from ..._plot.underwater import plot_weston_regimes

        return plot_weston_regimes(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _regime_labels(
    r: NDArray[np.float64], bounds: WestonRegimeBoundaries
) -> NDArray[np.str_]:
    """The label of the regime in force at each range ``r``."""
    labels = np.full(np.shape(r), WESTON_REGIMES[0], dtype="<U14")
    labels[r >= bounds.spherical_to_cylindrical] = WESTON_REGIMES[1]
    labels[r >= bounds.cylindrical_to_mode_stripping] = WESTON_REGIMES[2]
    labels[r >= bounds.mode_stripping_to_single_mode] = WESTON_REGIMES[3]
    return labels


def _composite(
    labels: NDArray[np.str_], laws: dict[str, NDArray[np.float64]]
) -> NDArray[np.float64]:
    """At each range, the value of the law of the regime its label names."""
    out = np.array(laws[WESTON_REGIMES[0]], dtype=np.float64, copy=True)
    for name in WESTON_REGIMES[1:]:
        in_force = labels == name
        out[in_force] = np.asarray(laws[name], dtype=np.float64)[in_force]
    return out


def _to_db(factor: NDArray[np.float64]) -> NDArray[np.float64]:
    r"""Propagation loss :math:`-10 \log_{10} F`; a non-positive factor maps
    to ``nan``.
    """
    with np.errstate(divide="ignore"):
        return np.asarray(
            -10.0 * np.log10(np.where(factor > 0.0, factor, np.nan)), dtype=np.float64
        )


def weston_propagation_loss(
    range_m: NDArray[np.float64] | list[float] | float,
    frequency_hz: float,
    water_depth: float,
    *,
    seabed: str | WestonSeabed = "sand",
    speed_of_sound: float = 1500.0,
    source_depth: float | None = None,
    receiver_depth: float | None = None,
    critical_angle_deg: float | None = None,
    reflection_loss_gradient_value_np_per_rad: float | None = None,
) -> WestonPropagationResult:
    r"""Propagation loss across Weston's four shallow-water regimes.

    Assembles the piecewise loss from Ainslie's Equations (9.42), (9.49) and
    (9.54), switching regime at the boundaries of
    :func:`weston_regime_boundaries`, and returns each regime's own law over the
    whole range grid so the transitions can be drawn.

    :param range_m: Range(s) from the source, in metres (scalar or array,
        strictly positive).
    :param frequency_hz: Acoustic frequency, in Hz.
    :param water_depth: Water-column depth ``H``, in metres.
    :param seabed: ``"sand"``, ``"mud"`` or a :class:`WestonSeabed`.
    :param speed_of_sound: Water sound speed ``c_w``, in m/s.
    :param source_depth: Source depth ``z0``, in metres; defaults to ``H/2``
        (used only by the single-mode formula).
    :param receiver_depth: Receiver depth ``z``, in metres; defaults to ``H/2``.
    :param critical_angle_deg: Override :math:`\psi_\mathrm{c}`, in degrees (``90`` for an
        ideal totally reflecting waveguide).
    :param reflection_loss_gradient_value_np_per_rad: Override :math:`\eta`, in Np/rad
        (``0`` for a lossless bottom: no mode stripping, no single-mode
        regime).
    :return: A :class:`WestonPropagationResult`.
    :raises ValueError: If an input is invalid.
    """
    f = require_positive(frequency_hz, "frequency_hz")
    h = require_positive(water_depth, "water_depth")
    c = require_positive(speed_of_sound, "speed_of_sound")
    r = np.atleast_1d(np.asarray(range_m, dtype=np.float64))
    if r.size == 0 or not np.all(np.isfinite(r)):
        msg = "'range_m' must be finite and non-empty."
        raise ValueError(msg)
    if np.any(r <= 0.0):
        msg = "'range_m' must be strictly positive."
        raise ValueError(msg)
    z0 = h / 2.0 if source_depth is None else float(source_depth)
    zr = h / 2.0 if receiver_depth is None else float(receiver_depth)
    for name, value in (("source_depth", z0), ("receiver_depth", zr)):
        if not np.isfinite(value) or not (0.0 <= value <= h):
            msg = f"'{name}' must lie within the water column [0, H]."
            raise ValueError(msg)

    bed = _seabed(seabed)
    bounds = weston_regime_boundaries(
        f,
        h,
        seabed=bed,
        speed_of_sound=c,
        critical_angle_deg=critical_angle_deg,
        reflection_loss_gradient_value_np_per_rad=reflection_loss_gradient_value_np_per_rad,
    )
    psi_c = bounds.critical_angle_rad
    eta = bounds.reflection_loss_gradient_np_per_rad
    h_eff = bounds.effective_depth
    lam = c / f

    f_ss = 1.0 / r**2  # Eq. (9.43)/(9.44)
    f_cs = 2.0 * psi_c / (r * h)  # Eq. (9.42)
    if eta > 0.0:
        theta_eff = np.sqrt(np.pi * h / (4.0 * eta * r))  # Eq. (9.47)
        f_mp = (2.0 * theta_eff / (r * h)) * erf(
            np.sqrt(np.pi) * psi_c / (2.0 * theta_eff)
        )  # Eq. (9.46)
        f_ms = np.sqrt(np.pi / (eta * h)) * r ** (-1.5)  # Eq. (9.49)
    else:
        f_mp = f_cs
        f_ms = np.zeros_like(r)
    f_sm = (  # Eq. (9.54)
        4.0
        * lam
        / (h_eff**2 * r)
        * np.sin(np.pi * z0 / h_eff) ** 2
        * np.sin(np.pi * zr / h_eff) ** 2
        * np.exp(-eta * lam**2 * r / (4.0 * h_eff**3))
    )

    factor = _composite(
        _regime_labels(r, bounds),
        dict(zip(WESTON_REGIMES, (f_ss, f_cs, f_ms, f_sm), strict=True)),
    )

    return WestonPropagationResult(
        range_m=r,
        propagation_loss=_to_db(factor),
        propagation_factor=factor,
        spherical=_to_db(f_ss),
        cylindrical=_to_db(f_cs),
        mode_stripping=_to_db(f_ms),
        single_mode=_to_db(f_sm),
        multipath=_to_db(f_mp),
        boundaries=bounds,
        frequency=f,
        water_depth=h,
        source_depth=z0,
        receiver_depth=zr,
        seabed=bed.name,
    )

#  Copyright (c) 2026. Jose M. Requena-Plens
"""Plot renderers for the materials domain (lazy imports from result .plot())."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .common import (
    _ABSORPTION_QUANTITY_LABELS,
    _C_MUTED,
    _C_PRIMARY,
    _C_PRIMARY_LIGHT,
    _C_REFERENCE,
    _band_axis,
    _freq_axis,
    _import_pyplot,
    _new_axes,
    _plot_rating,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from ..materials.absorption_rating import AbsorptionRatingResult
    from ..materials.absorption_uncertainty import AbsorptionUncertaintyResult
    from ..materials.airflow_resistance import StaticAirflowResult
    from ..materials.dynamic_stiffness import DynamicStiffnessResult
    from ..materials.impedance_tube import ImpedanceTubeResult
    from ..materials.porous_absorber import (
        LayeredAbsorberResult,
        PorousMediumResult,
        DiffuseFieldAbsorptionResult,
    )
    from ..materials.road_absorption import InsituAbsorptionResult
    from ..materials.scattering_diffusion import DiffusionResult, ScatteringResult

_FREQ_LABEL = "Frequency [Hz]"

def plot_weighted_absorption(
    result: "AbsorptionRatingResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Practical absorption curve vs the shifted reference (ISO 11654:1997).

    Draws the practical coefficients ``alpha_p`` against the shifted reference
    curve and shades the unfavourable deviations (measured below the shifted
    reference, Clause 4.2) through the shared rating renderer.

    :param result: An
        :class:`~phonometry.absorption_rating.AbsorptionRatingResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the measured-curve ``plot`` call.
    :return: The axes.
    """
    return _plot_rating(
        np.asarray(result.band_centers, dtype=np.float64),
        np.asarray(result.measured, dtype=np.float64),
        np.asarray(result.shifted_reference, dtype=np.float64),
        impact=False,
        title=(
            f"ISO 11654 alpha_w = {result.rating_label}  "
            f"(class {result.absorption_class}, "
            f"Sigma unfav. = {result.unfavourable_sum:.2f})"
        ),
        ylabel="Sound absorption coefficient",
        measured_label="Practical alpha_p",
        ylim=(0.0, 1.05),
        ax=ax,
        **kwargs,
    )

def plot_scattering_coefficient(
    result: "ScatteringResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Random-incidence scattering coefficient ``s`` versus frequency.

    :param result: A :class:`~phonometry.scattering_diffusion.ScatteringResult`
        exposing ``frequencies`` and ``scattering``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the coefficient curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    s = np.asarray(result.scattering, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(freqs, s, **kwargs)
    _freq_axis(ax, freqs)
    ax.set_ylabel("Scattering coefficient s")
    # s is normally in [0, 1], but edge effects (Clause 6.3.2) can push it above
    # 1 and those values are kept, not clipped; grow the top so they stay visible.
    top = max(1.05, float(np.nanmax(s)) * 1.05) if s.size else 1.05
    ax.set_ylim(0.0, top)
    ax.set_title("Random-incidence scattering coefficient (ISO 17497-1)")
    ax.grid(True, alpha=0.3)
    return ax

def plot_diffusion_polar(
    result: "DiffusionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Polar reflected-level response with the diffusion coefficient annotated.

    :param result: A :class:`~phonometry.scattering_diffusion.DiffusionResult`
        exposing ``angles`` (degrees), ``levels`` (dB) and ``coefficient``.
    :param ax: Existing (ideally polar) axes, or ``None`` to create a polar one.
    :param kwargs: Forwarded to the reflected-level curve ``plot`` call.
    :return: The polar axes.
    """
    if ax is None:
        plt = _import_pyplot()
        _fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
    angles = np.radians(np.asarray(result.angles, dtype=np.float64))
    levels = np.asarray(result.levels, dtype=np.float64)
    kwargs.setdefault("marker", "o")
    kwargs.setdefault("color", _C_PRIMARY)
    ax.plot(angles, levels, **kwargs)
    ax.fill(angles, levels, alpha=0.15, color=kwargs["color"])
    ax.set_title(
        f"Diffusion coefficient d = {float(result.coefficient):.2f} "
        "(ISO 17497-2)"
    )
    return cast("Axes", ax)

def plot_insitu_absorption(
    result: "InsituAbsorptionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """In-situ one-third-octave absorption spectrum ``alpha(f)``.

    :param result: An
        :class:`~phonometry.road_absorption.InsituAbsorptionResult` exposing
        ``frequencies`` and ``absorption``.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the absorption :meth:`~matplotlib.axes.Axes.bar`.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequencies, dtype=np.float64)
    alpha = np.asarray(result.absorption, dtype=np.float64)
    positions = _band_axis(ax, freqs)
    kwargs.setdefault("color", _C_PRIMARY)
    ax.bar(positions, np.nan_to_num(alpha), **kwargs)
    ax.set_ylabel("Absorption coefficient")
    ax.set_ylim(0.0, 1.0)
    ax.set_title("In-situ road-surface absorption (ISO 13472-1)")
    ax.grid(True, axis="y", alpha=0.3)
    return ax

def plot_dynamic_stiffness(
    result: "DynamicStiffnessResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Floating-floor natural frequency ``f0(s')`` with the design point marked.

    :param result: A
        :class:`~phonometry.dynamic_stiffness.DynamicStiffnessResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the design-point ``scatter``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    m = result.floor_mass_per_area
    s_mn = result.dynamic_stiffness / 1e6
    grid = np.logspace(np.log10(max(s_mn * 0.2, 1e-2)), np.log10(s_mn * 5.0), 240)
    f0 = np.sqrt(grid * 1e6 / m) / (2.0 * np.pi)
    ax.plot(grid, f0, color=_C_PRIMARY,
            label=rf"$f_0 = \frac{{1}}{{2\pi}}\sqrt{{s'/m'}}$,  $m'$ = {m:g} kg/m²")
    ax.axhline(result.natural_frequency, color=_C_MUTED, ls=":", lw=0.8)
    ax.plot([s_mn, s_mn], [0.0, result.natural_frequency], color=_C_MUTED, ls=":", lw=0.8)

    kwargs.setdefault("color", _C_REFERENCE)
    kwargs.setdefault("zorder", 5)
    kwargs.setdefault("s", 80)
    ax.scatter([s_mn], [result.natural_frequency],
               label=f"$s'$ = {s_mn:.2f} MN/m³,  $f_0$ = {result.natural_frequency:.1f} Hz",
               **kwargs)
    ax.set_xscale("log")
    ax.set_xlabel("Dynamic stiffness per unit area $s'$ [MN/m³]")
    ax.set_ylabel("Natural frequency $f_0$ [Hz]")
    ax.set_title("EN 29052-1 floating-floor resonance")
    ax.set_ylim(bottom=0.0)
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax

def plot_impedance_tube(
    result: "ImpedanceTubeResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Normal-incidence absorption spectrum with |r| overlaid (ISO 10534-2).

    Draws the absorption coefficient ``alpha(f)`` as the primary curve and
    the magnitude of the reflection factor ``|r|(f)`` as a muted companion
    (both are dimensionless and share the 0..1 axis).

    :param result: An :class:`~phonometry.impedance_tube.ImpedanceTubeResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the absorption-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequency, dtype=np.float64)
    alpha = np.asarray(result.absorption, dtype=np.float64)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", r"Absorption $\alpha$")
    ax.plot(freqs, alpha, **kwargs)
    ax.plot(freqs, np.abs(np.asarray(result.reflection, dtype=np.complex128)),
            ls="--", color=_C_MUTED, label="Reflection factor $|r|$")
    ax.set_xlabel(_FREQ_LABEL)
    ax.set_ylabel("Coefficient")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("ISO 10534-2 normal-incidence absorption")
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax

def plot_static_airflow(
    result: "StaticAirflowResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Fitted pressure-drop curve with the evaluation point (ISO 9053-1).

    Draws the clause 7.5 through-origin fit ``dp = a u + b u**2`` over twice
    the evaluation range and marks the reference evaluation point.

    :param result: A
        :class:`~phonometry.airflow_resistance.StaticAirflowResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the fitted-curve ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    u_eval = float(result.evaluation_velocity)
    u = np.linspace(0.0, 2.0 * u_eval, 200)
    dp = result.linear_coefficient * u + result.quadratic_coefficient * u**2

    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", r"Fit $\Delta p = a\,u + b\,u^2$")
    # Millimetres per second keep the clause 7.5 reference (0.5 mm/s) legible.
    ax.plot(u * 1e3, dp, **kwargs)
    ax.plot([u_eval * 1e3], [result.pressure_drop], "D", color=_C_REFERENCE,
            ms=7, label=f"Evaluation point (u = {u_eval * 1e3:g} mm/s)")
    ax.set_xlabel("Linear airflow velocity u [mm/s]")
    ax.set_ylabel(r"Pressure difference $\Delta p$ [Pa]")
    ax.set_title(
        "ISO 9053-1 static airflow resistance — "
        f"$R_s$ = {result.specific_resistance:.3g} Pa s/m"
    )
    ax.legend(loc="upper left", fontsize="small")
    ax.grid(True, alpha=0.3)
    return ax

def plot_absorption_uncertainty(
    result: "AbsorptionUncertaintyResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Absorption quantity with its expanded-uncertainty ribbon (ISO 12999-2).

    Draws the per-band quantity (``alpha_s``, ``A_T`` or ``alpha_p``) as a curve
    with a shaded ``±U`` band using the exact expanded uncertainty ``U = k·u``.

    :param result: An
        :class:`~phonometry.absorption_uncertainty.AbsorptionUncertaintyResult`
        for a band quantity (single-number results have no spectrum to plot).
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the value-curve ``plot`` call.
    :return: The axes.
    :raises ValueError: The result is a single-number quantity (no bands).
    """
    if result.frequencies.size == 0:
        raise ValueError(
            "plot() needs a per-band result; single-number quantities "
            "(alpha_w, DLalpha) have no spectrum to plot."
        )
    ax = ax if ax is not None else _new_axes()
    freqs = result.frequencies
    value = result.values
    u_expanded = result.expanded_uncertainty
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("marker", "o")
    ax.fill_between(
        freqs,
        value - u_expanded,
        value + u_expanded,
        color=_C_PRIMARY_LIGHT,
        alpha=0.5,
        label=f"+/-U (k = {result.coverage_factor:g})",
    )
    ax.plot(freqs, value, **kwargs)
    _freq_axis(ax, freqs)
    ylabel = _ABSORPTION_QUANTITY_LABELS.get(result.quantity, "Value")
    ax.set_ylabel(ylabel)
    if result.quantity != "equivalent_area":
        ax.set_ylim(0.0, 1.05)
    sigma = "sigma_R" if result.condition == "reproducibility" else "sigma_r"
    ax.set_title(
        f"ISO 12999-2 absorption uncertainty ({sigma}) — {result.condition}"
    )
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    return ax


def _absorption_spectrum_axes(
    ax: "Axes | None",
    freqs: np.ndarray,
    alpha: np.ndarray,
    *,
    title: str,
    label: str,
    **kwargs: Any,
) -> Axes:
    """Shared alpha(f) spectrum renderer for the absorber predictions."""
    ax = ax if ax is not None else _new_axes()
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", label)
    ax.semilogx(freqs, alpha, **kwargs)
    ax.set_xlabel(_FREQ_LABEL)
    ax.set_ylabel(r"Absorption coefficient $\alpha$")
    ax.set_ylim(0.0, 1.05)
    ax.set_title(title)
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_porous_medium(
    result: "PorousMediumResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Normalised characteristic values of a porous medium vs frequency.

    Draws the real part and negative imaginary part of the normalised
    characteristic impedance ``Zc / (rho c)`` and wavenumber ``k / k0`` on a
    log-log grid, the classical presentation of the empirical porous models
    (Mechel 2e Sect. G.11; Cox & D'Antonio 3e Figs. 6.19-6.20).

    :param result: A :class:`~phonometry.materials.porous_absorber.PorousMediumResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the ``Re(Zc)`` ``plot`` call.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    freqs = np.asarray(result.frequency, dtype=np.float64)
    zn = np.asarray(result.normalized_impedance, dtype=np.complex128)
    kn = np.asarray(result.normalized_wavenumber, dtype=np.complex128)
    kwargs.setdefault("color", _C_PRIMARY)
    kwargs.setdefault("label", r"Re$(Z_c)/\rho c$")
    ax.loglog(freqs, zn.real, **kwargs)
    ax.loglog(freqs, -zn.imag, ls="--", color=_C_PRIMARY_LIGHT,
              label=r"$-$Im$(Z_c)/\rho c$")
    ax.loglog(freqs, kn.real, color=_C_REFERENCE, label=r"Re$(k)/k_0$")
    ax.loglog(freqs, -kn.imag, ls="--", color=_C_MUTED, label=r"$-$Im$(k)/k_0$")
    ax.set_xlabel(_FREQ_LABEL)
    ax.set_ylabel("Normalised characteristic value")
    ax.set_title(
        f"Porous medium ({result.model}), "
        f"$\\sigma$ = {result.flow_resistivity:g} Pa s/m$^2$"
    )
    ax.legend(loc="best", fontsize="small")
    ax.grid(True, which="both", alpha=0.3)
    return ax


def plot_layered_absorber(
    result: "LayeredAbsorberResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Oblique-incidence absorption spectrum with |R| overlaid.

    Draws the predicted ``alpha(f)`` of the layer stack as the primary curve
    and the reflection-factor magnitude ``|R|(f)`` as a muted companion.

    :param result: A :class:`~phonometry.materials.porous_absorber.LayeredAbsorberResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the absorption-curve ``plot`` call.
    :return: The axes.
    """
    angle_deg = np.degrees(result.angle)
    ax = _absorption_spectrum_axes(
        ax,
        np.asarray(result.frequency, dtype=np.float64),
        np.asarray(result.absorption, dtype=np.float64),
        title=(
            "Layered absorber prediction "
            f"($\\theta$ = {angle_deg:.0f}°)"
        ),
        label=r"Absorption $\alpha(\theta)$",
        **kwargs,
    )
    ax.semilogx(
        np.asarray(result.frequency, dtype=np.float64),
        np.abs(np.asarray(result.reflection, dtype=np.complex128)),
        ls="--", color=_C_MUTED, label="Reflection factor $|R|$",
    )
    ax.legend(loc="best", fontsize="small")
    return ax


def plot_diffuse_field_absorption(
    result: "DiffuseFieldAbsorptionResult", ax: Axes | None = None, **kwargs: Any
) -> Axes:
    """Random-incidence (Paris-integral) absorption spectrum.

    :param result: A :class:`~phonometry.materials.porous_absorber.DiffuseFieldAbsorptionResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param kwargs: Forwarded to the absorption-curve ``plot`` call.
    :return: The axes.
    """
    limit_deg = np.degrees(result.angle_limit)
    ax = _absorption_spectrum_axes(
        ax,
        np.asarray(result.frequency, dtype=np.float64),
        np.asarray(result.absorption, dtype=np.float64),
        title=(
            "Random-incidence absorption "
            f"(Paris integral to {limit_deg:.0f}°)"
        ),
        label=r"Absorption $\alpha_{dif}$",
        **kwargs,
    )
    ax.legend(loc="best", fontsize="small")
    return ax

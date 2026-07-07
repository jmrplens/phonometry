#  Copyright (c) 2026. Jose M. Requena-Plens

"""One-line ``.plot()`` methods on result objects (plan 16 T2).

The library exposes matplotlib as a *soft* dependency: importing
phonometry and computing must work without it, and only ``.plot()``
requires it. These tests run on the non-interactive Agg backend and check
both the smoke path (a figure is produced and the axes returned) and the
content (line/bar data echo the result fields, shading falls only on
unfavourable deviations, invalid/negative bands are marked) plus the
missing-matplotlib ImportError path.
"""

from __future__ import annotations

import ast
import builtins
import inspect

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import phonometry as ph  # noqa: E402
from phonometry import _plotting  # noqa: E402

FS = 48000
RNG = np.random.default_rng(20260707)


# --------------------------------------------------------------------------
# Fixtures: minimal real result objects via the public API
# --------------------------------------------------------------------------
def _exp_ir(seconds: float = 0.8, t60: float = 0.5) -> np.ndarray:
    t = np.arange(int(seconds * FS)) / FS
    decay = np.exp(-3.0 * np.log(10.0) / t60 * t)
    return decay * RNG.standard_normal(t.size)


def _zwicker_stationary() -> ph.ZwickerLoudness:
    return ph.loudness_zwicker_from_spectrum(np.full(28, 40.0))


def _sti() -> ph.STIResult:
    sig = ph.stipa_signal(fs=FS, seconds=16.0, seed=3)
    return ph.stipa(sig, FS)


def _airborne_rating() -> ph.WeightedRatingResult:
    measured = np.array(
        [30, 34, 38, 41, 45, 49, 50, 53, 54, 55, 56, 57, 58, 58, 58, 58],
        dtype=float,
    )
    return ph.weighted_rating(measured)


def _impact_rating() -> ph.ImpactRatingResult:
    measured = np.array(
        [60, 61, 62, 63, 64, 65, 63, 61, 60, 58, 56, 53, 50, 47, 44, 41],
        dtype=float,
    )
    return ph.weighted_impact_rating(measured)


def _room(limits: list[float] | None) -> ph.RoomAcousticsResult:
    return ph.room_parameters(_exp_ir(), FS, limits=limits)


def _sound_power() -> ph.SoundPowerResult:
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    r = 2.0
    s = 2.0 * np.pi * r**2
    lw_bands = np.array([90.0, 92.0, 95.0, 93.0])
    levels = np.tile(lw_bands - 10.0 * np.log10(s), (10, 1))
    return ph.sound_power_pressure(levels, "hemisphere", radius=r, frequencies=freqs)


def _reverb_power() -> ph.ReverberationSoundPowerResult:
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    t60 = np.array([1.6, 1.5, 1.4, 1.1])
    lp = np.tile(np.array([80.0, 82.0, 84.0, 81.0]), (6, 1))
    return ph.sound_power_reverberation(lp, t60, 200.0, 220.0, freqs)


def _intensity_power_negative() -> ph.SoundPowerIntensityResult:
    areas = np.array([0.5, 0.5, 0.5, 0.5])
    # band 0 positive net, band 1 all-negative net (external source).
    intensity = np.column_stack([np.full(4, 5.0e-4), np.full(4, -5.0e-5)])
    freqs = np.array([500.0, 1000.0])
    with pytest.warns(ph.SoundPowerWarning):
        return ph.sound_power_intensity(intensity, areas, frequencies=freqs)


def _intensity() -> ph.IntensityResult:
    p1 = RNG.standard_normal(FS)
    p2 = np.roll(p1, 1)
    return ph.sound_intensity(p1, p2, FS, spacing=0.012, fraction=3, limits=[125, 4000])


# --------------------------------------------------------------------------
# Soft-dependency contract: lazy import + ImportError guidance
# --------------------------------------------------------------------------
def test_plotting_module_has_no_toplevel_matplotlib_import() -> None:
    """matplotlib must be imported inside functions, never at module scope."""
    tree = ast.parse(inspect.getsource(_plotting))
    # Imports inside a function body are lazy; imports under an
    # ``if TYPE_CHECKING:`` guard never run at import time. Both are allowed;
    # a plain module-scope runtime import of matplotlib is not.
    allowed: set[ast.AST] = set()
    for node in ast.walk(tree):
        is_func = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        is_typecheck = (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        )
        if is_func or is_typecheck:
            for sub in ast.walk(node):
                allowed.add(sub)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            names = [module, *[a.name for a in node.names]]
            if any("matplotlib" in n for n in names):
                assert node in allowed, "matplotlib imported at runtime module scope"


def test_plot_raises_helpful_error_without_matplotlib(monkeypatch) -> None:
    """Without matplotlib, .plot() fails with an actionable message."""
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        if name.startswith("matplotlib"):
            raise ImportError("No module named 'matplotlib'")
        return real_import(name, *args, **kwargs)

    res = _zwicker_stationary()
    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ImportError, match=r"pip install phonometry\[plot\]"):
        res.plot()


# --------------------------------------------------------------------------
# Zwicker loudness
# --------------------------------------------------------------------------
def test_zwicker_stationary_returns_single_axes_with_specific_curve() -> None:
    res = _zwicker_stationary()
    ax = res.plot()
    assert not isinstance(ax, np.ndarray)
    ydata = ax.lines[0].get_ydata()
    np.testing.assert_allclose(ydata, res.specific)
    xdata = ax.lines[0].get_xdata()
    assert xdata[0] == pytest.approx(0.1) and xdata[-1] == pytest.approx(24.0)
    assert "Bark" in ax.get_xlabel()
    assert "sone/Bark" in ax.get_ylabel()
    plt.close("all")


def test_zwicker_time_varying_returns_two_panels() -> None:
    sig = RNG.standard_normal(FS) * 0.02  # 1 s of noise
    res = ph.loudness_zwicker(sig, FS, stationary=False)
    assert res.loudness_vs_time is not None
    axes = res.plot()
    assert isinstance(axes, np.ndarray) and axes.size == 2
    np.testing.assert_allclose(axes[0].lines[0].get_ydata(), res.specific)
    np.testing.assert_allclose(axes[1].lines[0].get_ydata(), res.loudness_vs_time)
    plt.close("all")


# --------------------------------------------------------------------------
# STI
# --------------------------------------------------------------------------
def test_sti_bars_match_mti_and_annotate_rating() -> None:
    res = _sti()
    ax = res.plot()
    heights = [patch.get_height() for patch in ax.patches]
    np.testing.assert_allclose(heights, res.mti)
    assert res.rating in ax.get_title()
    assert ax.get_ylim() == (0.0, 1.0)
    plt.close("all")


# --------------------------------------------------------------------------
# Weighted ratings (airborne / impact)
# --------------------------------------------------------------------------
def test_airborne_rating_carries_curve_fields() -> None:
    res = _airborne_rating()
    assert res.band_centers is not None and res.band_centers.size == 16
    assert res.measured is not None and res.shifted_reference is not None
    # shifted reference read at 500 Hz (index 7) equals the rating.
    assert int(round(res.shifted_reference[7])) == res.rating


def test_airborne_rating_shades_only_unfavourable_bands() -> None:
    res = _airborne_rating()
    ax = res.plot()
    # measured curve and shifted reference are drawn as lines.
    np.testing.assert_allclose(ax.lines[0].get_ydata(), res.measured)
    np.testing.assert_allclose(ax.lines[1].get_ydata(), res.shifted_reference)
    # a shaded region (fill_between -> collection) is present.
    assert len(ax.collections) >= 1
    mask = _plotting._unfavourable_mask(
        res.measured, res.shifted_reference, impact=False
    )
    # airborne: unfavourable where measured < reference.
    np.testing.assert_array_equal(mask, res.measured < res.shifted_reference)
    assert mask.any()
    plt.close("all")


def test_impact_rating_uses_opposite_sign_mask() -> None:
    res = _impact_rating()
    ax = res.plot()
    mask = _plotting._unfavourable_mask(
        res.measured, res.shifted_reference, impact=True
    )
    np.testing.assert_array_equal(mask, res.measured > res.shifted_reference)
    assert str(res.rating) in ax.get_title()
    plt.close("all")


def test_rating_without_curve_data_raises() -> None:
    bare = ph.WeightedRatingResult(rating=52, c=-1, ctr=-3, unfavourable_sum=10.0)
    with pytest.raises(ValueError, match="no band curve"):
        bare.plot()


# --------------------------------------------------------------------------
# Room acoustics
# --------------------------------------------------------------------------
def test_room_acoustics_two_panels_and_bar_heights() -> None:
    res = _room(limits=[250, 2000])
    axes = res.plot()
    assert isinstance(axes, np.ndarray) and axes.size == 2
    ax_times = axes[0]
    n = res.t30.size
    # 3 grouped bars (EDT/T20/T30) per band.
    assert len(ax_times.patches) == 3 * n
    assert "time" in ax_times.get_ylabel().lower()
    plt.close("all")


def test_room_acoustics_invalid_bands_are_hatched() -> None:
    # A near-silent IR yields invalid decay-time bands (fails ISO criterion).
    ir = RNG.standard_normal(int(0.3 * FS)) * 1e-6
    ir[0] = 1.0
    res = ph.room_parameters(ir, FS, limits=[250, 2000])
    if bool(np.all(res.t30_valid)):
        pytest.skip("all bands happened to be valid")
    axes = res.plot()
    hatched = [p for p in axes[0].patches if p.get_hatch()]
    assert hatched, "expected at least one hatched (invalid) bar"
    plt.close("all")


def test_room_acoustics_single_axes_composition() -> None:
    res = _room(limits=[250, 2000])
    fig, ax = plt.subplots()
    out = res.plot(ax=ax)
    assert out is ax
    plt.close("all")


# --------------------------------------------------------------------------
# Sound power (pressure / reverberation / intensity)
# --------------------------------------------------------------------------
def test_sound_power_bars_match_lw_and_annotate_lwa() -> None:
    res = _sound_power()
    ax = res.plot()
    heights = [p.get_height() for p in ax.patches]
    np.testing.assert_allclose(heights, res.sound_power_level)
    assert f"{res.sound_power_level_a:.1f}" in ax.get_title()
    plt.close("all")


def test_reverberation_power_plot_smoke() -> None:
    res = _reverb_power()
    ax = res.plot()
    heights = [p.get_height() for p in ax.patches]
    np.testing.assert_allclose(heights, np.nan_to_num(res.sound_power_level))
    plt.close("all")


def test_intensity_power_marks_negative_band() -> None:
    res = _intensity_power_negative()
    assert bool(res.negative_band[1])
    ax = res.plot()
    hatched = [p for p in ax.patches if p.get_hatch()]
    assert len(hatched) == int(np.count_nonzero(res.negative_band))
    plt.close("all")


# --------------------------------------------------------------------------
# Sound intensity (Lp vs LI)
# --------------------------------------------------------------------------
def test_intensity_plots_lp_and_li_with_index_twin() -> None:
    res = _intensity()
    ax = res.plot()
    np.testing.assert_allclose(ax.lines[0].get_ydata(), res.pressure_level)
    np.testing.assert_allclose(ax.lines[1].get_ydata(), res.intensity_level)
    # twin axis carries the pressure-intensity index bars.
    twins = [a for a in ax.figure.axes if a is not ax]
    assert twins, "expected a twin axis for the pressure-intensity index"
    plt.close("all")


def test_intensity_without_band_data_raises() -> None:
    p1 = RNG.standard_normal(FS)
    res = ph.sound_intensity(p1, np.roll(p1, 1), FS, spacing=0.012)
    assert res.frequency is None
    with pytest.raises(ValueError, match="per-band"):
        res.plot()


# --------------------------------------------------------------------------
# Schroeder decay curve (backward compat + plot)
# --------------------------------------------------------------------------
def test_decay_curve_is_dataclass_and_unpacks_like_tuple() -> None:
    ir = _exp_ir()
    dc = ph.decay_curve(ir, FS)
    assert isinstance(dc, ph.DecayCurve)
    time, level = ph.decay_curve(ir, FS)  # backward-compatible unpacking
    np.testing.assert_array_equal(time, dc.time)
    np.testing.assert_array_equal(level, dc.level)
    assert dc.band is None


def test_decay_curve_records_band() -> None:
    dc = ph.decay_curve(_exp_ir(), FS, band=500.0)
    assert dc.band == 500.0


def test_decay_curve_plot_has_curve_and_fit_overlays() -> None:
    dc = ph.decay_curve(_exp_ir(seconds=1.0, t60=0.6), FS)
    ax = dc.plot()
    np.testing.assert_allclose(ax.lines[0].get_ydata(), dc.level)
    labels = [ln.get_label() for ln in ax.lines]
    assert any("fit" in str(lbl) for lbl in labels)
    assert "s]" in ax.get_xlabel()
    plt.close("all")


def test_decay_curve_plot_without_fits() -> None:
    dc = ph.decay_curve(_exp_ir(), FS)
    ax = dc.plot(fits=False)
    labels = [str(ln.get_label()) for ln in ax.lines]
    assert not any("fit" in lbl for lbl in labels)
    plt.close("all")


# --------------------------------------------------------------------------
# Common contract: ax=None creates a figure; passing ax composes
# --------------------------------------------------------------------------
def test_single_axes_plots_accept_external_ax() -> None:
    for res in (_zwicker_stationary(), _sti(), _airborne_rating(), _sound_power()):
        fig, ax = plt.subplots()
        out = res.plot(ax=ax)
        assert out is ax
        plt.close(fig)

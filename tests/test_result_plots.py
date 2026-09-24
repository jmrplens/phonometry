#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The contract every one-line ``.plot()`` method on a result object has to keep.

Four promises, none of them about any single standard, which is why they are
tested together and away from the domains:

* matplotlib is a *soft* dependency. Importing phonometry and computing must
  work without it, so ``phonometry._plot.common`` may not import matplotlib at
  module scope; the AST check below allows only imports inside a function body
  or under ``if TYPE_CHECKING:``.
* When it really is missing, ``.plot()`` fails with the install command, not
  with a bare ``ModuleNotFoundError``.
* Styling kwargs reach the primary artist. Every renderer draws a fixed default
  colour and width, and a user-supplied ``linewidth=`` or ``color=`` must
  override it rather than collide with it: ``color`` in particular used to raise
  ``TypeError: got multiple values for keyword``. The table below walks every
  public renderer, line-drawn and bar-drawn alike.
* ``ax=None`` creates a figure and passing ``ax=`` composes into it, returning
  the same axes object, so a result can be drawn into a caller's subplot.

The result objects are built by ``tests/result_factories.py``; what each figure
*says* about its own standard is asserted in that domain's own test file. These
tests run on the non-interactive Agg backend.
"""

from __future__ import annotations

import ast
import builtins
import inspect
from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from result_factories import (
    FS,
    _airborne_insulation,
    _airborne_prediction,
    _airborne_rating,
    _assessment_velocity,
    _band_averaged_stiffness,
    _band_uncertainty,
    _binaural_indicators,
    _cnossos_road,
    _conformance_verification,
    _diffuse_absorption,
    _diffuse_field,
    _directivity_factor,
    _double_wall,
    _driving_point_stiffness,
    _effective_blocking_mass,
    _exp_ir,
    _exposure,
    _extended_impact_rating,
    _extended_rating,
    _field_indicators,
    _high_frequency_power,
    _impact_insulation,
    _impact_prediction,
    _impact_rating,
    _impedance_tube,
    _in_situ_power,
    _intensity,
    _intensity_power_negative,
    _layered_absorber,
    _low_frequency_procedure,
    _method_a_summary,
    _method_b_summary,
    _modulation,
    _monte_carlo,
    _open_plan,
    _outdoor,
    _people_assessment,
    _pleasantness_eventfulness,
    _porous_medium,
    _radiation_efficiency,
    _random_incidence,
    _reverb_energy,
    _reverb_power,
    _room,
    _sel_distribution,
    _single_panel,
    _slit_aperture,
    _sound_calibrator,
    _sound_energy,
    _sound_power,
    _soundscape_correlation,
    _source_ranking,
    _static_airflow,
    _statistical_pass_by,
    _sti,
    _train_passage,
    _vibration_meter_reading,
    _vibration_meter_verification,
    _zwicker_stationary,
)

import phonometry as ph
from phonometry._plot import common as _plotting

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch


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


def test_plot_raises_helpful_error_without_matplotlib(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without matplotlib, .plot() fails with an actionable message."""
    real_import = builtins.__import__

    def blocked(name: str, *args: object, **kwargs: object) -> ModuleType:
        if name.startswith("matplotlib"):
            msg = "No module named 'matplotlib'"
            raise ImportError(msg)
        return real_import(name, *args, **kwargs)

    res = _zwicker_stationary()
    monkeypatch.setattr(builtins, "__import__", blocked)
    with pytest.raises(ImportError, match=r"pip install phonometry\[plot\]"):
        res.plot()


# --------------------------------------------------------------------------
# Every public .plot() must accept and forward a benign styling kwarg
# --------------------------------------------------------------------------
#: ISO 4869-2 Annex A: 16 subjects over the eight octaves from 63 Hz, which
#: every hearing-protector result is built from.
_PROTECTOR_ATTENUATION = [
    [4, 8, 13, 18, 20, 30, 35, 30],
    [6, 12, 16, 21, 29, 35, 47, 35],
    [10, 16, 17, 23, 25, 32, 48, 37],
    [3, 7, 12, 18, 20, 25, 33, 30],
    [8, 10, 16, 16, 25, 27, 43, 32],
    [4, 7, 10, 15, 19, 32, 35, 31],
    [5, 5, 9, 16, 20, 25, 30, 28],
    [15, 15, 21, 26, 25, 38, 46, 38],
    [5, 6, 10, 13, 19, 22, 29, 28],
    [9, 9, 10, 19, 20, 27, 37, 31],
    [9, 16, 18, 24, 25, 35, 44, 39],
    [5, 6, 11, 12, 17, 20, 28, 28],
    [7, 10, 17, 22, 25, 35, 41, 44],
    [6, 8, 16, 18, 19, 19, 30, 33],
    [10, 12, 17, 25, 28, 33, 45, 40],
    [12, 13, 17, 27, 29, 38, 49, 41],
]

_KWARG_PLOT_CASES = [
    ("zwicker", _zwicker_stationary, "line"),
    ("sti", _sti, "bar"),
    ("airborne", _airborne_rating, "line"),
    ("impact", _impact_rating, "line"),
    ("room", lambda: _room([250, 2000]), "bar"),
    ("sound_power", _sound_power, "bar"),
    ("reverb_power", _reverb_power, "bar"),
    ("in_situ_power", _in_situ_power, "bar"),
    ("high_frequency_power", _high_frequency_power, "bar"),
    ("sound_energy", _sound_energy, "bar"),
    ("reverb_energy", _reverb_energy, "bar"),
    ("intensity_power", _intensity_power_negative, "bar"),
    ("intensity", _intensity, "line"),
    (
        "decay_curve",
        lambda: ph.room.decay_curve(_exp_ir(seconds=1.0, t60=0.6), FS),
        "line",
    ),
    (
        "facade",
        lambda: ph.building.facade_insulation(
            [70.0, 72.0, 74.0], [40.0, 41.0, 42.0], [0.5, 0.5, 0.5]
        ),
        "line",
    ),
    ("open_plan", _open_plan, "line"),
    ("outdoor", _outdoor, "line"),
    ("cnossos_road", _cnossos_road, "bar"),
    ("statistical_pass_by", _statistical_pass_by, "line"),
    (
        "pass_by_regression",
        lambda: _statistical_pass_by().regressions["1"],
        "line",
    ),
    ("impedance_tube", _impedance_tube, "line"),
    ("porous_medium", _porous_medium, "line"),
    ("layered_absorber", _layered_absorber, "line"),
    ("diffuse_absorption", _diffuse_absorption, "line"),
    ("monte_carlo", _monte_carlo, "bar"),
    ("exposure", _exposure, "bar"),
    ("sel_distribution", _sel_distribution, "line"),
    ("pleasantness_eventfulness", _pleasantness_eventfulness, "line"),
    ("method_a_summary", _method_a_summary, "line"),
    ("soundscape_correlation", _soundscape_correlation, "line"),
    ("method_b_summary", _method_b_summary, "line"),
    ("source_ranking", _source_ranking, "bar"),
    ("binaural_indicators", _binaural_indicators, "bar"),
    ("directivity_factor", _directivity_factor, "line"),
    ("random_incidence", _random_incidence, "line"),
    ("diffuse_field", _diffuse_field, "line"),
    ("vibration_meter_reading", _vibration_meter_reading, "line"),
    ("vibration_meter_verification", _vibration_meter_verification, "line"),
    (
        "running_rms_decay_verification",
        lambda: ph.vibration.verify_running_rms_decay(
            0.98, integration_time_s=1.0, method="linear"
        ),
        "line",
    ),
    ("conformance_verification", _conformance_verification, "line"),
    (
        "sound_calibrator_requirement",
        lambda: _sound_calibrator().requirement("environmental_level"),
        "line",
    ),
    ("sound_calibrator_verification", _sound_calibrator, "bar"),
    ("assessment_velocity", _assessment_velocity, "line"),
    ("train_passage", _train_passage, "line"),
    ("people_assessment", _people_assessment, "bar"),
    (
        "assumed_protection",
        lambda: ph.hearing.assumed_protection_value(_PROTECTOR_ATTENUATION),
        "line",
    ),
    (
        "hml_rating",
        lambda: ph.hearing.hml_rating(_PROTECTOR_ATTENUATION),
        "line",
    ),
    ("snr_rating", lambda: ph.hearing.snr_rating(_PROTECTOR_ATTENUATION), "bar"),
    (
        "protected_level",
        lambda: ph.hearing.octave_band_protected_level(
            [75.0, 84.0, 86.0, 88.0, 97.0, 99.0, 97.0, 96.0],
            ph.hearing.assumed_protection_value(_PROTECTOR_ATTENUATION),
        ),
        "bar",
    ),
    (
        "real_ear_attenuation",
        lambda: ph.hearing.real_ear_attenuation(_PROTECTOR_ATTENUATION),
        "line",
    ),
    (
        "attenuation_difference",
        lambda: ph.hearing.assess_attenuation_difference(
            ph.hearing.real_ear_attenuation(_PROTECTOR_ATTENUATION),
            [6.0, 9.0, 14.0, 19.0, 22.0, 29.0, 30.0, 33.0],
            second_expanded_uncertainty_db=2.0,
        ),
        "bar",
    ),
    (
        "reat_sound_field",
        lambda: ph.hearing.check_reat_sound_field(
            dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.5] * 7),
            [0.0] * 7,
        ),
        "line",
    ),
    (
        "active_insertion_loss",
        lambda: ph.hearing.active_insertion_loss(
            [[20.0, 24.0, -3.0], [22.0, 23.0, -1.0], [21.0, 25.0, -2.0]],
            frequencies=[100.0, 125.0, 1000.0],
        ),
        "line",
    ),
    (
        "anr_total_attenuation",
        lambda: ph.hearing.anr_total_attenuation(
            _PROTECTOR_ATTENUATION, [[20.0] * 24] * len(_PROTECTOR_ATTENUATION)
        ),
        "line",
    ),
    (
        "anr_linearity",
        lambda: ph.hearing.assess_anr_linearity(
            [90.0, 95.0, 100.0], [[60.0, 65.0, 70.0], [60.0, 65.0, 69.0]]
        ),
        "line",
    ),
    ("static_airflow", _static_airflow, "line"),
    ("airborne_prediction", _airborne_prediction, "bar"),
    ("impact_prediction", _impact_prediction, "bar"),
    ("airborne_insulation", _airborne_insulation, "line"),
    ("impact_insulation", _impact_insulation, "line"),
    ("low_frequency_procedure", _low_frequency_procedure, "line"),
    (
        "low_frequency_element",
        lambda: ph.building.low_frequency_element_normalized_difference(
            [84.0, 86.0, 88.0],
            [70.0, 73.0, 76.0],
            measurement_area=2.0,
            elements=4,
            l_p=[78.0, 80.0, 82.0],
            frequencies=[50.0, 63.0, 80.0],
        ),
        "bar",
    ),
    (
        "low_frequency_intensity",
        lambda: ph.building.low_frequency_intensity_reduction(
            [84.0, 86.0, 88.0],
            [70.0, 73.0, 76.0],
            measurement_area=12.0,
            area=10.0,
            frequencies=[50.0, 63.0, 80.0],
        ),
        "bar",
    ),
    ("band_uncertainty", _band_uncertainty, "line"),
    ("band_averaged_stiffness", _band_averaged_stiffness, "line"),
    (
        "blocked_output_check",
        lambda: ph.vibration.check_blocked_output(
            [50.0, 100.0, 200.0], [100.0, 100.0, 100.0], [70.0, 75.0, 60.0]
        ),
        "line",
    ),
    (
        "output_mass_check",
        lambda: ph.vibration.check_output_mass(
            [50.0, 100.0, 200.0], 0.1, [120.0, 120.0, 120.0], [100.0, 105.0, 110.0]
        ),
        "line",
    ),
    ("effective_blocking_mass", _effective_blocking_mass, "line"),
    ("driving_point_stiffness", _driving_point_stiffness, "line"),
    (
        "driving_point_uncertainty",
        lambda: ph.vibration.driving_point_uncertainty(
            120.0, repeatability_range_db=0.6
        ),
        "bar",
    ),
    ("radiation_efficiency", _radiation_efficiency, "line"),
    ("single_panel", _single_panel, "line"),
    ("double_wall", _double_wall, "line"),
    ("slit_aperture", _slit_aperture, "line"),
    ("modulation_distortion", _modulation, "line"),
    ("field_indicators", _field_indicators, "line"),
    (
        "flight_profile",
        lambda: ph.aircraft.load_anp_database().flight_profile(
            "A320-211",
            "departure",
            aerodrome=ph.aircraft.Aerodrome(elevation_ft=0.0),
        ),
        "line",
    ),
]


@pytest.mark.parametrize(
    ("name", "factory", "kind"),
    _KWARG_PLOT_CASES,
    ids=[c[0] for c in _KWARG_PLOT_CASES],
)
def test_every_plot_forwards_kwargs_to_primary_artist(
    name: str, factory: Callable[[], object], kind: str
) -> None:
    res = factory()
    out = res.plot(linewidth=2)
    ax = out[0] if isinstance(out, np.ndarray) else out
    artists = ax.lines if kind == "line" else ax.patches
    assert artists, f"{name}: no primary {kind} artist drawn"
    assert any(a.get_linewidth() == 2.0 for a in artists), (
        f"{name}: linewidth kwarg not forwarded to the primary artist"
    )
    plt.close("all")

    # A user-supplied color must win over the renderer's fixed default rather
    # than raising ``TypeError: got multiple values for keyword 'color'``.
    out = res.plot(color="red")
    ax = out[0] if isinstance(out, np.ndarray) else out
    artists = ax.lines if kind == "line" else ax.patches
    red = plt.matplotlib.colors.to_rgba("red")

    def _is_red(artist: Line2D | Patch) -> bool:
        if kind == "line":
            return plt.matplotlib.colors.to_rgba(artist.get_color()) == red
        return tuple(artist.get_facecolor()) == red

    assert any(_is_red(a) for a in artists), (
        f"{name}: color kwarg did not override the fixed default artist color"
    )
    plt.close("all")

    # And the same for `label`, which is where this went wrong for longest.
    # `color` was passed by name next to `**kwargs` once and fixed; `label`
    # was passed that way in fifty-five renderers, so a caller naming a curve
    # got `TypeError: got multiple values for keyword argument 'label'`
    # instead of a labelled curve.
    out = res.plot(label="mine")
    ax = out[0] if isinstance(out, np.ndarray) else out
    # Through the legend, not through the artist: `ax.bar` puts the label on
    # the container it returns rather than on each rectangle, so reading
    # `ax.patches` would miss it on every bar renderer. The legend is what the
    # caller is naming the curve for anyway.
    assert "mine" in ax.get_legend_handles_labels()[1], (
        f"{name}: label kwarg did not reach the legend"
    )
    plt.close("all")

    # Matplotlib gives seven properties two names, and since 3.3 a call that
    # receives both is `TypeError: Got both 'color' and 'c', which are aliases
    # of one another`. A renderer that defaults its own colour under one
    # spelling therefore refuses every caller who wrote the other, which is
    # what 195 `setdefault` calls across 24 modules did until `style_default`
    # replaced them. The long spelling is checked above; this is the short one,
    # and it has to reach the artist rather than raise.
    # `c` is the short spelling of `color` on a Line2D only: a Rectangle has no
    # such alias, so the bar renderers are held to `lw`, which every artist
    # aliases, and the colour half of the check stays with the line renderers.
    out = res.plot(c="red", lw=2) if kind == "line" else res.plot(lw=2)
    ax = out[0] if isinstance(out, np.ndarray) else out
    artists = ax.lines if kind == "line" else ax.patches
    assert any(a.get_linewidth() == 2.0 for a in artists), (
        f"{name}: the short spelling of linewidth did not reach the artist"
    )
    if kind == "line":
        assert any(_is_red(a) for a in artists), (
            f"{name}: the short spelling of color did not reach the artist"
        )
    plt.close("all")


# --------------------------------------------------------------------------
# One signature for every .plot(): ax first, everything else by name
# --------------------------------------------------------------------------
def _public_plot_methods() -> dict[str, Callable[..., object]]:
    """Every ``plot`` a caller can reach on a class the package publishes.

    Walks the imported package rather than the source, so a class published
    from a private module (``io._signal.Signal``) counts under the public name
    that reaches it, and a ``plot`` inherited from a phonometry base class is
    held to the rule on every subclass that exposes it.
    """
    import importlib
    import pkgutil

    found: dict[str, Callable[..., object]] = {}
    for info in pkgutil.walk_packages(ph.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if name.startswith("_") or not inspect.isclass(obj):
                continue
            if not obj.__module__.startswith("phonometry"):
                continue
            try:
                method = inspect.getattr_static(obj, "plot")
            except AttributeError:
                continue
            if isinstance(method, staticmethod | classmethod):
                method = method.__func__
            if inspect.isfunction(method):
                found.setdefault(f"{obj.__module__}.{obj.__qualname__}", method)
    return found


#: The parameter kinds a call can fill by position.
_BY_POSITION = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
    inspect.Parameter.VAR_POSITIONAL,
)


def test_every_plot_takes_ax_first_and_the_rest_by_name() -> None:
    """``result.plot(ax)`` draws into ``ax``, on every result in the library.

    Two shapes broke it. Three results put a choice before the axes
    (``plot(quantity, ax)``, ``plot(frequency, characteristic_impedance,
    ax)``), so the call every other result accepts raised or, worse, bound the
    axes to a frequency vector. Six took ``language`` by position, so
    ``plot(ax, "es")`` worked on those six and nowhere else. The rule is the
    one every other result keeps: the axes first, and every other
    argument, ``language`` included, keyword-only.
    """
    methods = _public_plot_methods()
    assert len(methods) > 200, "the walk found too few plot methods to mean anything"
    offenders: list[str] = []
    for owner, method in sorted(methods.items()):
        parameters = list(inspect.signature(method).parameters.values())[1:]
        if not parameters or parameters[0].name != "ax":
            first = parameters[0].name if parameters else None
            offenders.append(f"{owner}.plot: first parameter is {first!r}, not 'ax'")
            continue
        offenders.extend(
            f"{owner}.plot: {parameter.name!r} can be passed by position"
            for parameter in parameters[1:]
            if parameter.kind in _BY_POSITION and parameter.name != "language"
        )
        language = next((p for p in parameters if p.name == "language"), None)
        if language is not None and language.kind is not inspect.Parameter.KEYWORD_ONLY:
            offenders.append(f"{owner}.plot: 'language' is not keyword-only")
    assert not offenders, "\n".join(offenders)


# --------------------------------------------------------------------------
# Common contract: ax=None creates a figure; passing ax composes
# --------------------------------------------------------------------------
def test_single_axes_plots_accept_external_ax() -> None:
    for res in (
        _zwicker_stationary(),
        _sti(),
        _airborne_rating(),
        _extended_rating(),
        _extended_impact_rating(),
        _sound_power(),
        _sound_energy(),
        _reverb_energy(),
        _open_plan(),
        _outdoor(),
        _cnossos_road(),
        _statistical_pass_by(),
        _statistical_pass_by().regressions["2a"],
        _impedance_tube(),
        _porous_medium(),
        _layered_absorber(),
        _diffuse_absorption(),
        _monte_carlo(),
        _exposure(),
        _sel_distribution(),
        _pleasantness_eventfulness(),
        _method_a_summary(),
        _soundscape_correlation(),
        _method_b_summary(),
        _source_ranking(),
        _binaural_indicators(),
        _random_incidence(),
        _diffuse_field(),
        _static_airflow(),
        _airborne_prediction(),
        _impact_prediction(),
        _airborne_insulation(),
        _impact_insulation(),
        _low_frequency_procedure(),
        _band_uncertainty(),
        ph.vibration.verify_running_rms_decay(
            4.7, integration_time_s=1.0, method="exponential"
        ),
        _conformance_verification(),
        _sound_calibrator(),
        _sound_calibrator().requirement("level"),
        ph.aircraft.load_anp_database().flight_profile(
            "A320-211", "departure", aerodrome=ph.aircraft.Aerodrome(elevation_ft=0.0)
        ),
    ):
        fig, ax = plt.subplots()
        out = res.plot(ax=ax)
        assert out is ax
        plt.close(fig)


def test_no_renderer_defaults_a_label_on_the_shared_kwargs_inside_a_loop() -> None:
    """One `setdefault` in a loop names every curve after the first one.

    `dict.setdefault` mutates, so a renderer that draws several named curves
    has to take a copy per curve. Doing it once on `kwargs` sets the first
    label and then finds it already there on every later pass, which is not a
    crash and not a test failure anywhere else: the figure simply comes out
    with one legend entry repeated, and the only thing that noticed was a
    committed report preview drifting by 693 pixels.

    This is a structural check because the behavioural one cannot be written
    once: what "several named curves" means differs per renderer, while the
    shape that produces the bug is the same everywhere.
    """
    import ast
    import pathlib

    root = (
        pathlib.Path(__file__).resolve().parent.parent / "src" / "phonometry" / "_plot"
    )
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.For | ast.While | ast.AsyncFor):
                continue
            offenders.extend(
                f"{path.name}:{child.lineno}"
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "setdefault"
                and isinstance(child.func.value, ast.Name)
                and child.func.value.id == "kwargs"
                and child.args
                and isinstance(child.args[0], ast.Constant)
                and child.args[0].value == "label"
            )
    assert not offenders, (
        "a label default on the shared kwargs inside a loop names every curve "
        f"after the first one: {offenders}. Take a copy per iteration."
    )
